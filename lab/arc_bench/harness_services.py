"""Submission-side snapshot transport and OTLP setup for the DX variants."""
from contextlib import contextmanager
import json
import hashlib
import os
from pathlib import Path
import select
import signal
import shutil
import subprocess
import sys
import tarfile
import threading
import time
from urllib.request import ProxyHandler, build_opener


def _current_cgroup():
    """Resolve this process' cgroup v2 directory without host-path guessing."""
    try:
        membership = next(line[3:] for line in Path('/proc/self/cgroup').read_text().splitlines()
                          if line.startswith('0::'))
        for line in Path('/proc/self/mountinfo').read_text().splitlines():
            before, separator, after = line.partition(' - ')
            if not separator or not after.startswith('cgroup2 '):
                continue
            fields = before.split()
            root, mount = Path(fields[3]), Path(fields[4])
            if membership == '/':
                return mount
            if Path(membership).is_relative_to(root):
                candidate = mount / Path(membership).relative_to(root)
                return candidate if '..' not in candidate.parts else None
    except (OSError, StopIteration, IndexError, ValueError):
        return None
    return None


class ResourceSupervisor:
    """Observe and close only services owned by this context.

    The supervisor is a thread, not a recovery process: it can still run when
    the pids limit is exhausted. It never gates startup or kills unowned
    Agent, browser, or workspace processes.
    """
    def __init__(self, evidence):
        self.evidence = Path(evidence)
        self.cgroup = _current_cgroup()
        self.stop = threading.Event()
        self.failed = None
        self.children = []
        self.entry = None
        self.thread = None
        self.baseline_events = {}
        self.sampler = None
        self.sample_condition = threading.Condition()
        self.sample_pending = None
        self.sample_closing = False
        self.sample_thread = None
        self.sample_coalesced = 0

    def attach_sampler(self, package):
        """Sample the execution namespace; an external OTLP receiver cannot see it."""
        try:
            package = Path(package)
            support = next(candidate for candidate in (package / 'support', package)
                           if (candidate / 'agent_support.py').is_file())
            sys.path.insert(0, str(support))
            from agent_support import ResourceEvidence
            self.sampler = ResourceEvidence(self.evidence, root_pid=os.getpid())
        except Exception as error:
            self._save({'phase': 'startup', 'error': {
                'type': type(error).__name__, 'message': str(error)}}, 'resource-sampler-error.json')

    def _collect_sample(self, kind='sample', request=None):
        if self.sampler is None:
            return
        try:
            self.sampler.sample(kind, request=request)
        except Exception as error:
            try:
                self._save({'phase': kind, 'error': {
                    'type': type(error).__name__, 'message': str(error)}}, 'resource-sampler-error.json')
            except OSError as save_error:
                print(f'resource sample failed: {type(error).__name__}: {error}; evidence write failed: {save_error}',
                      file=sys.stderr, flush=True)

    def _sample(self, kind='sample'):
        if self.sampler is None:
            return
        with self.sample_condition:
            if self.sample_closing:
                return
            request = {'kind': kind, 'kinds': [kind], 'requested_monotonic_ns': time.monotonic_ns()}
            if self.sample_pending is not None:
                self.sample_coalesced += 1
                request['kinds'] = list(dict.fromkeys([*self.sample_pending['kinds'], kind]))
                request['requested_monotonic_ns'] = self.sample_pending['requested_monotonic_ns']
                priorities = {'sample': 0, 'baseline': 1, 'resource_limit': 2, 'final': 3}
                if priorities.get(kind, 0) <= priorities.get(self.sample_pending['kind'], 0):
                    self.sample_pending['kinds'] = request['kinds']
                    return
            self.sample_pending = request
            self.sample_condition.notify()

    def _sampling_worker(self):
        while True:
            with self.sample_condition:
                self.sample_condition.wait_for(lambda: self.sample_pending is not None or self.sample_closing)
                if self.sample_pending is None:
                    return
                request, self.sample_pending = self.sample_pending, None
                coalesced = self.sample_coalesced
            started = time.monotonic_ns()
            request['coalesced_requests'] = coalesced
            self._collect_sample(request['kind'], request)
            try:
                self._save({'kind': request['kind'], 'requested_monotonic_ns': request['requested_monotonic_ns'],
                            'started_monotonic_ns': started, 'finished_monotonic_ns': time.monotonic_ns(),
                            'queue_delay_ns': started-request['requested_monotonic_ns'],
                            'coalesced_requests': coalesced}, 'resource-sampling-worker.json')
            except OSError as error:
                print(f'resource sampler status failed: {error}', file=sys.stderr, flush=True)

    def _read(self):
        row = {'observed_at_ns': time.time_ns(), 'cgroup_path': str(self.cgroup) if self.cgroup else None,
               'values': {}, 'errors': {}}
        if self.cgroup is None:
            row['errors']['cgroup'] = 'cgroup v2 is not visible'
            return row
        for name in ('memory.current', 'memory.max', 'memory.events', 'pids.current', 'pids.max', 'pids.events'):
            try:
                row['values'][name] = (self.cgroup / name).read_text().strip()
            except OSError as error:
                row['errors'][name] = {'type': type(error).__name__, 'errno': error.errno, 'message': str(error)}
        return row

    def _save(self, row, name='resource-observation.json'):
        self.evidence.mkdir(parents=True, exist_ok=True)
        target = self.evidence / name
        temporary = target.with_name('.' + target.name + '.tmp')
        # The entry may be terminated immediately after this record.  Flush it
        # before signalling so resource_exhausted.json is useful even when the
        # entry's finally block is never reached.
        with temporary.open('w') as stream:
            stream.write(json.dumps(row, ensure_ascii=False, indent=2) + '\n')
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(target)

    def _event_values(self, row):
        values = row['values']
        events = {}
        for source in ('memory.events', 'pids.events'):
            prefix = source.split('.', 1)[0]
            events.update({f'{prefix}.{key}': int(value)
                           for key, value in (line.split() for line in values.get(source, '').splitlines()
                                              if len(line.split()) == 2)
                           if value.isdigit()})
        return events

    def _limit_state(self, row, event_baseline=None):
        values = row['values']
        def number(name):
            value = values.get(name)
            return None if value in (None, '', 'max') else int(value)
        memory, memory_max = number('memory.current'), number('memory.max')
        pids, pids_max = number('pids.current'), number('pids.max')
        current_limit = ((memory is not None and memory_max is not None and memory >= memory_max) or
                (pids is not None and pids_max is not None and pids >= pids_max) or
                (event_baseline is not None and any(value > event_baseline.get(key, value)
                    for key, value in self._event_values(row).items()
                    if key in {'memory.oom', 'memory.oom_kill', 'pids.max'})))
        return current_limit, self._event_values(row)

    def _at_limit(self, row):
        return self._limit_state(row, self.baseline_events)[0]

    def _reap_finished(self, reason):
        actions = []
        for child in tuple(self.children):
            code = child.poll()
            if code is None:
                continue
            action = {'pid': child.pid, 'reason': reason, 'result': 'already_exited',
                      'exit_code': code, 'reaped': False}
            try:
                child.wait(timeout=0)
                action['reaped'] = True
            except BaseException as error:
                action['error'] = {'type': type(error).__name__, 'message': str(error)}
            actions.append(action)
        return actions

    def _fail_fast(self):
        """Stop an explicitly owned entry group after durable evidence.

        The public entry gives us its actual child Popen. Killing the
        supervisor itself would bypass the caller's service cleanup.
        """
        entry = self.entry
        if entry is None:
            return {'status': 'entry_owner_missing'}
        pid = entry.pid
        if entry.poll() is not None:
            return {'status': 'entry_already_exited', 'pid': pid, 'exit_code': entry.returncode}
        try:
            pgid = os.getpgid(pid)
            if pgid == pid:
                os.killpg(pgid, signal.SIGTERM)
                target = lambda: entry.poll() is None
            else:
                entry.terminate()
                target = lambda: entry.poll() is None
            deadline = time.monotonic() + 3
            while time.monotonic() < deadline and target():
                time.sleep(.05)
            if target():
                if pgid == pid:
                    os.killpg(pgid, signal.SIGKILL)
                else:
                    entry.kill()
                return {'status': 'entry_killed', 'pid': pid, 'pgid': pgid, 'term': 'sent', 'kill': 'sent'}
            return {'status': 'entry_stopped', 'pid': pid, 'pgid': pgid, 'term': 'sent'}
        except (OSError, ValueError) as error:
            return {'status': 'entry_signal_failed', 'pid': pid,
                    'error': {'type': type(error).__name__, 'errno': getattr(error, 'errno', None),
                              'message': str(error)}}

    def register_entry(self, process):
        """Give the supervisor the exact Popen owned by the public entry."""
        self.entry = process
        if self.failed:
            self.failed['entry_shutdown'] = self._fail_fast()
            self._save(self.failed, 'resource-exhausted.json')
            raise RuntimeError(json.dumps(self.failed, ensure_ascii=False))

    def start(self):
        if self.sampler is not None:
            self.sample_thread = threading.Thread(target=self._sampling_worker, name='resource-sampler', daemon=True)
            self.sample_thread.start()
        self.thread = threading.Thread(target=self._run, name='resource-supervisor', daemon=True)
        self.thread.start()

    def _run(self):
        self._sample('baseline')
        initial = self._read()
        initial_events = {}
        initial_events.update(self._event_values(initial))
        self.baseline_events = initial_events
        previous_check = time.monotonic_ns()
        while not self.stop.wait(2):
            check = time.monotonic_ns()
            row = self._read()
            row.update(check_monotonic_ns=check, actual_interval_ns=check-previous_check,
                       scheduling_delay_ns=max(0, check-previous_check-2_000_000_000))
            previous_check = check
            self._sample('resource_limit' if self._at_limit(row) else 'sample')
            self._save(row)
            if not self._at_limit(row):
                continue
            # Required gateway/collector children are not reclaim candidates.
            # Only reap children that had already exited before this event.
            action = {'trigger': row, 'actions': self._reap_finished('resource_limit'),
                      'active_owned_services': [child.pid for child in self.children if child.poll() is None],
                      'remediation_deadline_ns': time.time_ns() + 4_000_000_000}
            trigger_events = self._event_values(row)
            if self.cgroup is not None and (self.cgroup / 'memory.reclaim').exists():
                try:
                    (self.cgroup / 'memory.reclaim').write_text(str(256 * 1024 * 1024))
                    action['memory_reclaim'] = 'requested'
                except OSError as error:
                    action['memory_reclaim'] = {'status': 'failed', 'error': str(error)}
            time.sleep(1)
            after = self._read()
            action['after'] = after
            after_events = self._event_values(after)
            event_during_remediation = {key: value for key, value in after_events.items()
                                        if value > trigger_events.get(key, value)
                                        and key in {'memory.oom', 'memory.oom_kill', 'pids.max'}}
            # A trigger caused by an OOM/pids failure is already an execution
            # failure; lowering current usage cannot rewrite that fact.  For a
            # pure current/max ceiling, recovery is possible if no new event
            # occurred during the bounded remediation window.
            trigger_failure = any(trigger_events.get(key, 0) > self.baseline_events.get(key, 0)
                                  for key in {'memory.oom', 'memory.oom_kill', 'pids.max'})
            still_limited = (self._limit_state(after, None)[0] or trigger_failure or
                             bool(event_during_remediation))
            action['events_during_remediation'] = event_during_remediation
            self._save({'status': 'resource_exhausted' if still_limited else 'recovered', **action},
                       'resource-remediation.json')
            if still_limited:
                self.failed = {'status': 'resource_exhausted', 'reason': 'memory_or_pids_limit_persisted',
                               'remediation': action}
                self._save(self.failed, 'resource-exhausted.json')
                action['entry_shutdown'] = self._fail_fast()
                self.failed['remediation']['entry_shutdown'] = action['entry_shutdown']
                self._save(self.failed, 'resource-exhausted.json')
                return

    def close(self):
        self.stop.set()
        if self.thread is not None:
            self.thread.join(timeout=3)
        self._sample('final')
        with self.sample_condition:
            self.sample_closing = True
            self.sample_condition.notify()
        if self.sample_thread is not None:
            self.sample_thread.join(timeout=3)
            if self.sample_thread.is_alive():
                self._save({'phase': 'close', 'status': 'incomplete',
                            'reason': 'sampler_did_not_finish_within_shutdown_window'}, 'resource-sampler-error.json')
        if self.failed:
            raise RuntimeError(json.dumps(self.failed, ensure_ascii=False))


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
        if child.poll() is None:
            child.terminate()
        child.wait(timeout=10)
        capture.join(timeout=2)
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
        supervisor.start()
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
            error_log = (evidence / 'collector.stderr.log').open('a')
            process = subprocess.Popen(
                [sys.executable, str(package / 'lab_otlp.py'), '--serve-run', str(evidence),
                 '--no-resource-sampling'],
                stdout=subprocess.PIPE, stderr=error_log, text=True)
            supervisor.children.append(process)
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
        # The public wrapper registers its actual Popen after creating the
        # variant child.  This is a local-only handle; callers must not
        # serialize it as part of the run contract.
        contract['_resource_supervisor'] = supervisor
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
        if error_log is not None:
            error_log.close()
        supervisor_error = None
        try:
            supervisor.close()
        except BaseException as error:
            supervisor_error = error
        for name, value in previous.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value
        if supervisor_error is not None:
            raise supervisor_error
