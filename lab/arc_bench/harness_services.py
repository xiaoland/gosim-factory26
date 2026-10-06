"""Submission-side snapshot transport and OTLP setup for the DX variants."""
from contextlib import contextmanager
import json
import hashlib
import os
from pathlib import Path
import select
import shutil
import stat
import subprocess
import sys
import tarfile
import threading
import time
from urllib.request import ProxyHandler, build_opener


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


def _model_bindings(catalog, routes, endpoint):
    """Build the native descriptor consumed by agent_support.model_bindings().

    The descriptor is keyed by the native provider/model identity and contains
    only the loopback transport plus the selected model's wire identity.  The
    public catalog remains the source for contextWindow/maxTokens/compat; those
    fields are not guessed or copied into this transport descriptor.
    """
    grouped = {}
    for entry in catalog.get('model_list', []):
        grouped.setdefault(entry['model_name'], []).append(entry)
    entries = {alias: rows[0] for alias, rows in grouped.items()}
    aliases = set(routes)
    if aliases != set(entries):
        raise ValueError('gateway routes and selected catalog aliases differ')
    def model_info(canonical):
        rows = sorted(grouped[canonical], key=lambda row: row['litellm_params']['order'])
        primary = dict(rows[0].get('model_info') or {})
        for field in ('contextWindow', 'maxTokens'):
            values = [row['model_info'][field] for row in rows
                      if isinstance(row.get('model_info', {}).get(field), int)
                      and not isinstance(row['model_info'][field], bool)]
            if values:
                primary[field] = min(values)
        return primary

    def descriptor(canonical):
        return {
            'provider': 'factory26', 'base_url': endpoint,
            'credential_env': 'FACTORY26_GATEWAY_TOKEN', 'model_id': canonical,
            'model_info': model_info(canonical),
        }
    bindings = {}
    for alias in routes:
        descriptor_value = descriptor(alias)
        descriptor_value['model_id'] = alias
        bindings['factory26/' + alias] = descriptor_value
        # The visual provider is a separate native identity but uses the same
        # selected route when the recipe exposes a visual-capable alias.
        if alias.endswith('glm-5.3-flash'):
            bindings['factory26-visual/' + alias] = dict(descriptor_value)
    # I14 keeps the historical selector while the self-funded recipe freezes
    # the explicit 0731 wire alias.  This is an alias adaptation, not a route
    # choice or a provider fallback.
    if 'deepseek-v4-flash-0731' in entries:
        bindings['factory26/deepseek-v4-flash'] = descriptor('deepseek-v4-flash-0731')
        bindings['factory26/deepseek-v4-flash']['model_id'] = 'deepseek-v4-flash-0731'
    return bindings


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
    env.update(FACTORY26_BASE_URL=endpoint, FACTORY26_GATEWAY_TOKEN=frozen['token'],
               FACTORY26_MODEL_BINDINGS=json.dumps(
                   _model_bindings(catalog, routes, endpoint), separators=(',', ':')))
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
        if child.poll() is None:
            child.terminate()
        child.wait(timeout=10)
        capture.join(timeout=2)
        raise


def _repair_native_state_ownership(output, contract):
    """Return only Pi's two root-created state files to the mounted output owner."""
    if os.geteuid() != 0:
        return
    try:
        owner = Path(output).stat()
    except OSError:
        return
    scope = Path(output)/'.factory26/data/harness'/contract['native_scope_id']
    agents = [scope/'home/.pi/agent', scope/'work/home/.pi/agent']
    homes = scope/'work/native-homes'
    files = [agent/name for agent in agents for name in ('auth.json', 'models-store.json')]
    if homes.is_dir():
        files += [path for name in ('auth.json', 'models-store.json') for path in homes.rglob(name)]
    errors = []
    for path in files:
        try:
            info = path.lstat()
            if not stat.S_ISREG(info.st_mode) or path.is_symlink():
                continue
            if (info.st_uid, info.st_gid) != (owner.st_uid, owner.st_gid):
                os.chown(path, owner.st_uid, owner.st_gid, follow_symlinks=False)
        except FileNotFoundError:
            continue
        except OSError as error:
            errors.append({'path': str(path.relative_to(scope)), 'error': str(error)})
    if errors:
        evidence = scope/'producers'/contract['run_id']
        (evidence/'state-ownership-errors.json').write_text(json.dumps(errors)+'\n')


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
    previous = {}
    error_log = None
    try:
        for name, value in contract.get('model_environment', {}).items():
            if name not in os.environ:
                previous[name] = None
                os.environ[name] = value
        gateway, gateway_env = _start_model_proxy(package, evidence, contract)
        if gateway is not None:
            # Native clients receive only the loopback token. Provider secrets
            # stay in the proxy's private input, not in the Agent/tool env.
            provider_names = set(contract.get('provider_env_names', [])) | {
                'OPENAI_API_KEY', 'FACTORY26_API_KEY', 'FACTORY26_VISUAL_API_KEY', 'VISUAL_API_KEY'}
            for name in provider_names:
                if name in os.environ:
                    previous[name] = os.environ.pop(name)
        for name, value in gateway_env.items():
            if name in {'FACTORY26_BASE_URL', 'FACTORY26_GATEWAY_TOKEN', 'FACTORY26_MODEL_BINDINGS'}:
                previous[name] = os.environ.get(name)
                os.environ[name] = value
        if contract.get('target_kind') == 'hosted':
            error_log = (evidence / 'collector.stderr.log').open('a')
            process = subprocess.Popen(
                [sys.executable, str(package / 'lab_otlp.py'), '--serve-run', str(evidence)],
                stdout=subprocess.PIPE, stderr=error_log, text=True)
            try:
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
                (evidence/'collector-start.json').write_text(json.dumps({
                    'status': 'failed', 'error': f'{type(error).__name__}: {error}'})+'\n')
        yield contract
    finally:
        if process is not None:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        if gateway is not None:
            child = gateway['process']
            if child.poll() is None:
                child.terminate()
            try:
                child.wait(timeout=10)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()
            gateway['log_thread'].join(timeout=2)
        _repair_native_state_ownership(output, contract)
        if error_log is not None:
            error_log.close()
        for name, value in previous.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value
