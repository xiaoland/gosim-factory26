"""Submission-side snapshot transport and OTLP setup for the DX variants."""
from contextlib import contextmanager
import json
import hashlib
import os
from pathlib import Path
import select
import shutil
import subprocess
import sys
import tarfile
import threading
import time
from urllib.request import ProxyHandler, build_opener


def _diagnostic(evidence, phase, error):
    value = {'phase': phase, 'status': 'failed',
             'error': f'{type(error).__name__}: {error}'}
    try:
        with (Path(evidence) / 'services-errors.jsonl').open('a') as stream:
            stream.write(json.dumps(value)+'\n')
    except OSError as write_error:
        print(f'Harness service diagnostic: {value}; write failed: {write_error}', file=sys.stderr)


def _stop_service(process):
    if process.poll() is None:
        process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=3)


class ResourceSupervisor:
    """Own the Rust observer connection; gateway and receiver ownership stays with this caller."""
    def __init__(self, evidence):
        self.evidence = Path(evidence)
        self.children = []
        self.monitor = None
        self.package = None

    def attach_sampler(self, package):
        self.package = Path(package)

    def start(self):
        support = next(candidate for candidate in (self.package/'support', self.package)
                       if (candidate/'resource_monitor.py').is_file())
        sys.path.insert(0, str(support))
        from resource_monitor import ResourceMonitor
        self.monitor = ResourceMonitor(self.evidence, root_pid=os.getpid(), package=self.package)

    def register_entry(self, process):
        if self.monitor is not None:
            try:
                self.monitor.register_entry(process)
            except Exception as error:
                _diagnostic(self.evidence, 'resource-entry-registration', error)

    def close(self):
        if self.monitor is not None:
            self.monitor.close()


def install_inputs(package, output):
    package, output = Path(package), Path(output)
    output.mkdir(parents=True, exist_ok=True)
    inputs = package / 'inputs'
    seed = inputs / 'seed-data'
    archive = inputs / 'seed-data.tar'
    if archive.is_file() and not seed.exists():
        seed.mkdir()
        with tarfile.open(archive) as source:
            # The builder creates this trusted archive from our own frozen data.
            # Native absolute symlinks retain stable /workspace/template targets.
            source.extractall(seed, filter='fully_trusted')
    workspace = seed / 'workspace'
    if workspace.is_dir():
        for item in workspace.iterdir():
            # ARC owns the current allowed input and private evaluation context.
            # Previous versions remain in the original snapshot archive.
            if item.name in {'requirements', '.arc'}:
                continue
            target = output / item.name
            if item.is_symlink():
                if target.is_symlink() or target.exists():
                    target.unlink()
                target.symlink_to(os.readlink(item))
            elif item.is_dir():
                shutil.copytree(item, target, dirs_exist_ok=True, symlinks=True)
            else:
                shutil.copy2(item, target)
    harness = seed / 'harness'
    if harness.is_dir():
        shutil.copytree(harness, output / '.factory26/data/harness',
                        dirs_exist_ok=True, symlinks=True)
    contract = output / '.factory26/lab-run.json'
    contract.parent.mkdir(parents=True, exist_ok=True)
    if (inputs / 'lab-run.json').is_file():
        shutil.copy2(inputs / 'lab-run.json', contract)
    return json.loads(contract.read_text())


def _digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _selected_gateway_inputs(package):
    """Return the public frozen selection and optional private credentials."""
    package = Path(package)
    catalog = package / 'inputs/model-gateway.json'
    routes = package / 'inputs/gateway-routes.json'
    if not catalog.is_file() or not routes.is_file():
        return None
    provider_env = package / '.private/provider-env.json'
    if not provider_env.is_file():
        provider_env = None
    return catalog, routes, provider_env


def _read_provider_values(package, provider_env):
    if provider_env is not None:
        value = json.loads(Path(provider_env).read_text())
        if not isinstance(value, dict):
            raise ValueError('private provider-env.json must be an object')
        return value
    catalog = json.loads((Path(package) / 'inputs/model-gateway.json').read_text())
    names = {
        entry['litellm_params'][field].removeprefix('os.environ/')
        for entry in catalog.get('model_list', [])
        for field in ('api_base', 'api_key')
    }
    values = {name: os.environ[name] for name in names if os.environ.get(name)}
    if set(values) != names:
        raise ValueError(f'selected provider environment is incomplete: {sorted(names-set(values))}')
    return values


def _capture_gateway_log(child, log, cap_bytes=8 * 1024 * 1024):
    """Drain proxy output while retaining only a bounded diagnostic prefix."""
    def capture():
        retained = dropped = 0
        try:
            with Path(log).open('wb') as stream:
                while True:
                    chunk = child.stdout.read1(65536)
                    if not chunk:
                        break
                    keep = chunk[:max(0, cap_bytes - retained)]
                    if keep:
                        stream.write(keep)
                        stream.flush()
                        retained += len(keep)
                    dropped += len(chunk) - len(keep)
            if dropped:
                Path(log).with_suffix('.capped.json').write_text(json.dumps({
                    'cap_bytes': cap_bytes, 'retained_bytes': retained,
                    'later_output': 'drained-without-retention'}) + '\n')
        except OSError:
            # The process lifecycle still owns termination; diagnostics are best effort.
            pass
    thread = threading.Thread(target=capture, name='model-proxy-log', daemon=True)
    thread.start()
    return thread


def _start_model_proxy(package, evidence, contract):
    if contract.get('competition'):
        return None, {}
    selected_inputs = _selected_gateway_inputs(package)
    if selected_inputs is None:
        return None, {}
    catalog_path, routes_path, provider_env = selected_inputs
    binary = Path(package) / 'model-proxy/factory26-model-proxy'
    adapter = Path(package) / 'model_proxy_prepare.py'
    if not binary.is_file() or not os.access(binary, os.X_OK):
        raise FileNotFoundError(f'package model proxy is missing or not executable: {binary}')
    if not adapter.is_file():
        raise FileNotFoundError(f'package model proxy adapter is missing: {adapter}')
    catalog = json.loads(catalog_path.read_text())
    routes = json.loads(routes_path.read_text())
    values = _read_provider_values(package, provider_env)
    state = Path(package) / '.private/model-proxy' / contract['run_id']
    if state.exists():
        raise FileExistsError(f'model proxy state already exists for run: {state}')
    import importlib.util
    spec = importlib.util.spec_from_file_location('model_proxy_prepare', adapter)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    listen = '127.0.0.1:4021'
    frozen = module.freeze_proxy(catalog, routes, values, state, contract['run_id'], listen,
                                 catalog_sha256=_digest(catalog_path), routes_sha256=_digest(routes_path))
    endpoint = 'http://' + listen + '/v1'
    env = dict(os.environ)
    env.update(OPENAI_BASE_URL=endpoint, OPENAI_API_KEY=frozen['token'])
    log = evidence / 'gateway.log'
    child = subprocess.Popen(
        [str(binary), '--config', str(state / 'config.json'), '--credentials',
         str(state / '.private/provider-env.json')],
        cwd=package, env={key: value for key, value in env.items()
                          if key not in values}, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, start_new_session=True)
    capture = _capture_gateway_log(child, log)
    opener = build_opener(ProxyHandler({}))
    try:
        deadline = time.monotonic() + 30
        while child.poll() is None and time.monotonic() < deadline:
            try:
                with opener.open('http://' + listen + '/health/liveliness', timeout=1) as response:
                    if response.status == 200:
                        return {'process': child, 'log_thread': capture, 'state': str(state),
                                'endpoint': endpoint, 'token': frozen['token'],
                                'config_sha256': frozen['config_sha256'], 'binary': str(binary)}, env
            except OSError:
                pass
            time.sleep(.1)
        raise RuntimeError(f'model proxy failed readiness: exit={child.poll()}; log={log}')
    except BaseException:
        try:
            _stop_service(child)
        except Exception as error:
            _diagnostic(evidence, 'gateway-start-cleanup', error)
        try:
            capture.join(timeout=2)
        except Exception as error:
            _diagnostic(evidence, 'gateway-start-log-close', error)
        raise


@contextmanager
def services(package, output):
    """Use injected local OTLP, or a lightweight raw receiver on Hosted."""
    package, output = Path(package), Path(output)
    contract = install_inputs(package, output)
    evidence = (output / '.factory26/data/harness' / contract['native_scope_id'] /
                'producers' / contract['run_id'])
    evidence.mkdir(parents=True, exist_ok=True)
    process = None
    gateway = None
    supervisor = ResourceSupervisor(evidence)
    supervisor.attach_sampler(package)
    previous = {}
    error_log = None
    try:
        try:
            supervisor.start()
        except Exception as error:
            _diagnostic(evidence, 'resource-monitor-start', error)
        for name, value in contract.get('model_environment', {}).items():
            if name not in os.environ:
                previous[name] = None
                os.environ[name] = value
        gateway, gateway_env = _start_model_proxy(package, evidence, contract)
        if gateway is not None:
            supervisor.children.append(gateway['process'])
            # Native clients receive only the loopback token. Provider secrets
            # stay in the proxy's private input, not in the Agent/tool env.
            provider_names = set(contract.get('provider_env_names', [])) | {
                'OPENAI_API_KEY', 'FACTORY26_API_KEY', 'FACTORY26_VISUAL_API_KEY', 'VISUAL_API_KEY'}
            for name in provider_names:
                if name in os.environ:
                    previous[name] = os.environ.pop(name)
        for name, value in gateway_env.items():
            if name in {'OPENAI_BASE_URL', 'OPENAI_API_KEY'}:
                previous.setdefault(name, os.environ.get(name))
                os.environ[name] = value
        if contract.get('target_kind') == 'hosted':
            try:
                error_log = (evidence / 'collector.stderr.log').open('a')
                process = subprocess.Popen(
                    [sys.executable, str(package / 'lab_otlp.py'), '--serve-run', str(evidence),
                     '--no-resource-sampling'],
                    stdout=subprocess.PIPE, stderr=error_log, text=True)
                supervisor.children.append(process)
                if not select.select([process.stdout], [], [], 15)[0]:
                    raise RuntimeError('Hosted OTLP receiver did not provide its startup handshake')
                line = process.stdout.readline()
                if not line:
                    raise RuntimeError(f'Hosted OTLP receiver exited before startup: {process.poll()}')
                binding = json.loads(line)
                values = {
                    'OTEL_EXPORTER_OTLP_ENDPOINT': binding['endpoint'],
                    'OTEL_EXPORTER_OTLP_PROTOCOL': 'http/protobuf',
                    'OTEL_EXPORTER_OTLP_HEADERS': 'x-experiment-token=' + binding['token'],
                    'OTEL_SDK_DISABLED': 'false',
                }
                for name, value in values.items():
                    previous[name] = os.environ.get(name)
                    os.environ[name] = value
            except Exception as error:
                # Evidence failure is visible, but does not gate generation.
                _diagnostic(evidence, 'collector-start', error)
        # The public wrapper registers its actual Popen after creating the
        # variant child.  This is a local-only handle; callers must not
        # serialize it as part of the run contract.
        contract['_resource_supervisor'] = supervisor
        yield contract
    finally:
        # Stop each owned evidence/gateway service independently. A cleanup
        # failure must neither mask a variant failure nor gate evaluation.
        for phase, child in [('collector-close', process),
                             ('gateway-close', gateway['process'] if gateway else None)]:
            if child is not None:
                try:
                    _stop_service(child)
                except Exception as error:
                    _diagnostic(evidence, phase, error)
        if gateway is not None:
            try:
                gateway['log_thread'].join(timeout=2)
            except Exception as error:
                _diagnostic(evidence, 'gateway-log-close', error)
        if error_log is not None:
            try:
                error_log.close()
            except Exception as error:
                _diagnostic(evidence, 'collector-log-close', error)
        try:
            supervisor.close()
        except Exception as error:
            _diagnostic(evidence, 'resource-monitor-close', error)
        for name, value in previous.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value
