"""File, process and delivery operations; no Harness selection or orchestration."""
import hashlib,json,os,platform,selectors,shutil,signal,subprocess,sys,time,uuid
import shlex
import secrets
import re
import fcntl
import errno
from pathlib import Path

RESERVED={".arc", ".git", "requirements", ".factory26"}

def evidence_time():
    return {'realtime_ns': time.time_ns(), 'monotonic_ns': time.monotonic_ns()}

def evidence_error(error):
    return {'type': type(error).__name__, 'message': str(error),
            'errno': getattr(error, 'errno', None), 'filename': getattr(error, 'filename', None)}

def process_identity(pid):
    """Container-visible identity and resources; do not read argv or credentials."""
    root = Path('/proc')/str(pid)
    row = {'pid': pid, 'errors': {}}
    try:
        fields = (root/'stat').read_text().rsplit(')', 1)[1].split()
        row.update(ppid=int(fields[1]), pgid=int(fields[2]), starttime=int(fields[19]),
                   state=fields[0], rss_pages=int(fields[21]))
    except (OSError, ValueError, IndexError) as error:
        row['errors']['stat'] = evidence_error(error)
    for name in ('comm', 'cgroup', 'status'):
        try:
            value = (root/name).read_text()
            if name == 'status':
                row['status'] = {key: value.strip() for line in value.splitlines() if ':' in line
                                 for key, value in [line.split(':', 1)]
                                 if key in {'Tgid', 'Pid', 'PPid', 'NSpid', 'Threads', 'VmRSS', 'VmHWM', 'VmSize',
                                            'RssAnon', 'RssFile', 'RssShmem', 'VmSwap', 'CapEff'}}
            else:
                row[name] = value.strip()
        except OSError as error:
            row['errors'][name] = evidence_error(error)
    for name in ('exe', 'cwd', 'ns/pid', 'ns/cgroup'):
        try:
            row[name] = os.readlink(root/name)
        except OSError as error:
            row['errors'][name] = evidence_error(error)
    return row

def process_memory_evidence(pid, starttime):
    """Read memory ownership without argv, environment or file contents."""
    root = Path('/proc')/str(pid)
    row = {'pid': pid, 'starttime': starttime, 'errors': {}}
    for name in ('smaps_rollup', 'io'):
        try:
            row[name] = (root/name).read_text()
        except OSError as error:
            row['errors'][name] = evidence_error(error)
    try:
        descriptors = {'file': 0, 'socket': 0, 'pipe': 0, 'anon_inode': 0, 'other': 0}
        for descriptor in (root/'fd').iterdir():
            try:
                target = os.readlink(descriptor)
            except OSError as error:
                row['errors']['fd_entry'] = evidence_error(error)
                continue
            kind = next((kind for kind in ('socket', 'pipe', 'anon_inode')
                         if target.startswith(kind+':')), 'file' if target.startswith('/') else 'other')
            descriptors[kind] += 1
        row['file_descriptors'] = descriptors
    except OSError as error:
        row['errors']['fd'] = evidence_error(error)
    current = process_identity(pid)
    row['identity_matches'] = current.get('starttime') == starttime
    if not row['identity_matches']:
        row['errors']['identity'] = {'message': 'process disappeared or PID was reused during memory read',
                                     'current_starttime': current.get('starttime')}
    return row

def process_evidence(run, name, row, *, cap_bytes=8*1024*1024):
    """Append bounded evidence; failure must never change the operation being observed."""
    folder = Path(run)/'process-evidence'
    path = folder/name
    marker = path.with_suffix(path.suffix+'.capped.json')
    try:
        folder.mkdir(exist_ok=True)
        with path.open('ab', buffering=0) as stream:
            fcntl.flock(stream, fcntl.LOCK_EX)
            if marker.exists():
                return False
            value = {'schema_version': 1, **evidence_time(), **row}
            encoded = (json.dumps(value, ensure_ascii=False)+'\n').encode()
            size = os.fstat(stream.fileno()).st_size
            if size+len(encoded) > cap_bytes-4096:
                value = {'kind': 'log_capped', 'cap_bytes': cap_bytes, 'bytes_before': size,
                         'dropped_kind': row.get('kind'), **evidence_time()}
                save(marker, value)
                encoded = (json.dumps(value)+'\n').encode()
                if stream.write(encoded) != len(encoded):
                    raise OSError(errno.EIO, 'incomplete process evidence append', str(path))
                os.fsync(stream.fileno())
                return False
            if stream.write(encoded) != len(encoded):
                raise OSError(errno.EIO, 'incomplete process evidence append', str(path))
            os.fsync(stream.fileno())
        return True
    except (OSError, TypeError, ValueError) as error:
        try:
            print(f'process evidence failed: {path}: {json.dumps(evidence_error(error))}', file=sys.stderr, flush=True)
        except OSError:
            pass
        return False

class ResourceEvidence:
    """Read the namespace's visible cgroup and processes from the existing collector."""
    memory_files = ('memory.events', 'memory.events.local', 'memory.current', 'memory.peak',
                    'memory.stat', 'memory.pressure',
                    'memory.max', 'memory.oom.group', 'memory.swap.current', 'memory.swap.peak',
                    'memory.swap.max', 'pids.current', 'pids.max', 'pids.events')

    def __init__(self, run, *, root_pid=None):
        self.run = Path(run)
        self.cgroup = None
        self.errors = {}
        self.cap_bytes = 64*1024*1024
        self.segment_bytes = 31*1024*1024
        self.samples = 0
        self.capped = False
        self.rotations = 0
        self.segment_started = None
        self.previous_started = None
        self.root_pid = os.getppid() if root_pid is None else root_pid
        self.last_memory_detail_ns = 0
        root_process = process_identity(self.root_pid)
        self.root_starttime = root_process.get('starttime')
        self.membership = None
        capabilities = {'kind': 'capabilities', 'collector': process_identity(os.getpid()),
                        'interval_seconds': 2, 'max_processes_per_sample': 256,
                        'cap_bytes': self.cap_bytes, 'host_signal_sender': 'unavailable', 'raw': {},
                        'segment_bytes': self.segment_bytes, 'baseline_cap_bytes': 2*1024*1024,
                        'root_pid': self.root_pid, 'clock_ticks': os.sysconf('SC_CLK_TCK'),
                        'root_process': root_process,
                        'page_size': os.sysconf('SC_PAGE_SIZE'),
                        'selection_order': ['run-tree-by-depth', 'run-cwd', 'current-cgroup', 'other-visible'],
                        'live_processes_first': True, 'memory_detail_interval_seconds': 10,
                        'max_memory_detail_processes': 12,
                        'errors': self.errors}
        for name in ('/proc/self/cgroup', '/proc/self/mountinfo', '/proc/sys/kernel/random/boot_id'):
            try:
                capabilities['raw'][name] = Path(name).read_text()
            except OSError as error:
                self.errors[name] = evidence_error(error)
        membership = next((line[3:] for line in capabilities['raw'].get('/proc/self/cgroup', '').splitlines()
                           if line.startswith('0::')), None)
        self.membership = capabilities['raw'].get('/proc/self/cgroup', '').strip()
        for line in capabilities['raw'].get('/proc/self/mountinfo', '').splitlines():
            before, separator, after = line.partition(' - ')
            if not separator or after.split()[0] != 'cgroup2' or membership is None:
                continue
            fields = before.split()
            mount_root, mount = (Path(re.sub(r'\\([0-7]{3})', lambda match: chr(int(match[1], 8)), fields[i]))
                                for i in (3, 4))
            if membership == '/':
                candidate = mount
            elif Path(membership).is_relative_to(mount_root):
                candidate = mount/Path(membership).relative_to(mount_root)
            else:
                continue
            if '..' in candidate.parts:
                continue
            self.cgroup = candidate
            break
        capabilities['cgroup_path'] = str(self.cgroup) if self.cgroup else None
        capabilities['cgroup_mapping'] = 'visible-cgroup-v2' if self.cgroup else 'unavailable'
        process_evidence(self.run, 'resources-baseline.jsonl', capabilities, cap_bytes=2*1024*1024)
        self.sample('baseline')

    def sample(self, kind='sample'):
        row = {'kind': kind, 'cgroup_path': str(self.cgroup) if self.cgroup else None,
               'values': {}, 'errors': {}, 'processes': [], 'process_limit': 256,
               'processes_omitted': 0, 'visible_processes': 0, 'sample_started': evidence_time(),
               'scope_counts': {}, 'scope_omitted': {}, 'classification_errors': [],
               'classification_errors_omitted': 0}
        row['memory_detail'] = []
        if self.cgroup:
            try:
                info = self.cgroup.stat()
                row['cgroup_identity'] = {'device': info.st_dev, 'inode': info.st_ino}
            except OSError as error:
                row['errors']['cgroup_identity'] = evidence_error(error)
            for name in self.memory_files:
                try:
                    row['values'][name] = (self.cgroup/name).read_text().strip()
                except OSError as error:
                    row['errors'][name] = evidence_error(error)
        try:
            entries = sorted((entry for entry in Path('/proc').iterdir() if entry.name.isdigit()),
                             key=lambda entry: int(entry.name))
            row['visible_processes'] = len(entries)
            inventory = {}
            for entry in entries:
                item = {'pid': int(entry.name), 'ppid': None, 'starttime': None, 'cgroup': None, 'cwd': None,
                        'state': None, 'rss_pages': 0}
                for name in ('stat', 'cgroup', 'cwd'):
                    try:
                        if name == 'stat':
                            fields = (entry/name).read_text().rsplit(')', 1)[1].split()
                            item['ppid'], item['starttime'] = int(fields[1]), int(fields[19])
                            item['state'], item['rss_pages'] = fields[0], int(fields[21])
                        elif name == 'cgroup':
                            item['cgroup'] = (entry/name).read_text().strip()
                        else:
                            item['cwd'] = Path(os.readlink(entry/name))
                    except (OSError, ValueError, IndexError) as error:
                        if len(row['classification_errors']) < 32:
                            row['classification_errors'].append({'pid': item['pid'], 'field': name,
                                                                 **evidence_error(error)})
                        else:
                            row['classification_errors_omitted'] += 1
                inventory[item['pid']] = item
            ranked = []
            row['process_totals'] = {}
            root_matches = (self.root_starttime is not None and
                            inventory.get(self.root_pid, {}).get('starttime') == self.root_starttime)
            for pid, item in inventory.items():
                parent, depth, seen = pid, 0, set()
                while parent in inventory and parent != self.root_pid and parent not in seen:
                    seen.add(parent)
                    parent = inventory[parent]['ppid']
                    depth += 1
                if root_matches and parent == self.root_pid:
                    priority, scope = 0, 'run-tree'
                elif item['cwd'] is not None and item['cwd'].is_relative_to(self.run):
                    priority, scope = 1, 'run-cwd'
                elif self.membership and item['cgroup'] == self.membership:
                    priority, scope = 2, 'current-cgroup'
                else:
                    priority, scope = 3, 'other-visible'
                item['scope_priority'], item['sampling_scope'] = priority, scope
                row['scope_counts'][scope] = row['scope_counts'].get(scope, 0)+1
                totals = row['process_totals'].setdefault(scope, {'live': 0, 'zombie_or_dead': 0, 'rss_pages': 0})
                dead = item['state'] in {'Z', 'X'}
                totals['zombie_or_dead' if dead else 'live'] += 1
                totals['rss_pages'] += item['rss_pages']
                ranked.append((int(dead), priority, depth if priority == 0 else 0,
                               -item['rss_pages'], pid, scope))
            ranked.sort()
            for _dead, _priority, depth, _rss, pid, scope in ranked[:256]:
                row['processes'].append({**process_identity(pid), 'sampling_scope': scope,
                                         'tree_depth': depth if scope == 'run-tree' else None})
            for _dead, _priority, _depth, _rss, _pid, scope in ranked[256:]:
                row['scope_omitted'][scope] = row['scope_omitted'].get(scope, 0)+1
            row['processes_omitted'] = max(0, len(entries)-256)
            now_ns = row['sample_started']['monotonic_ns']
            if kind == 'baseline' or now_ns-self.last_memory_detail_ns >= 10_000_000_000:
                # RSS sums are a ranking aid, not cgroup use: shared pages may
                # appear in several processes. PSS/anonymous/file detail below
                # supplies the discriminating evidence for the largest users.
                largest = sorted((item for item in inventory.values()
                                  if item['state'] not in {None, 'Z', 'X'}),
                                 key=lambda item: (item['scope_priority'], -item['rss_pages'], item['pid']))[:12]
                row['memory_detail'] = [{**process_memory_evidence(item['pid'], item['starttime']),
                                         'sampling_scope': item['sampling_scope']}
                                        for item in largest]
                self.last_memory_detail_ns = now_ns
        except OSError as error:
            row['errors']['process_scan'] = evidence_error(error)
        if kind == 'baseline':
            written = process_evidence(self.run, 'resources-baseline.jsonl', row, cap_bytes=2*1024*1024)
        else:
            path = self.run/'process-evidence/resources.jsonl'
            previous = path.with_name('resources.previous.jsonl')
            marker = path.with_suffix(path.suffix+'.capped.json')
            try:
                size = path.stat().st_size if path.exists() else 0
                encoded_bytes = len(json.dumps(row, ensure_ascii=False).encode())+256
                if path.exists() and (size+encoded_bytes > self.segment_bytes-4096 or marker.exists()):
                    discarded = previous.stat().st_size if previous.exists() else 0
                    path.replace(previous)
                    marker.unlink(missing_ok=True)
                    self.rotations += 1
                    self.previous_started = self.segment_started
                    self.segment_started = None
                    process_evidence(self.run, 'resources.jsonl', {
                        'kind': 'resource_rotation', 'rotation': self.rotations,
                        'previous_bytes': size, 'discarded_previous_bytes': discarded,
                        'previous_started_monotonic_ns': self.previous_started,
                    }, cap_bytes=self.segment_bytes)
                if self.segment_started is None:
                    self.segment_started = row['sample_started']['monotonic_ns']
                written = process_evidence(self.run, 'resources.jsonl', row, cap_bytes=self.segment_bytes)
            except OSError as error:
                row['errors']['rotation'] = evidence_error(error)
                written = False
        latest = self.run/'process-evidence/resource-latest.json'
        temporary = latest.with_name(f'.{latest.name}.{uuid.uuid4().hex}.tmp')
        try:
            # Keep the admission input small; the rotating journal owns process detail.
            with temporary.open('x') as stream:
                json.dump({key: row[key] for key in
                           ('sample_started', 'cgroup_path', 'values', 'errors')}
                          | {'cgroup_identity': row.get('cgroup_identity')}, stream)
            temporary.replace(latest)
        except OSError as error:
            print(f'resource latest failed: {json.dumps(evidence_error(error))}', file=sys.stderr, flush=True)
        finally:
            temporary.unlink(missing_ok=True)
        self.samples += 1
        self.capped = (self.run/'process-evidence/resources.jsonl.capped.json').exists()
        status = {'kind': 'resource_status', 'samples': self.samples, 'last_sample_kind': kind,
                  'capped': self.capped, 'write_succeeded': written,
                  'cgroup_mapping': 'visible-cgroup-v2' if self.cgroup else 'unavailable',
                  'processes_omitted': row['processes_omitted'], 'errors': row['errors'],
                  'scope_counts': row['scope_counts'], 'scope_omitted': row['scope_omitted'],
                  'rotations': self.rotations, 'segment_bytes': self.segment_bytes,
                  'current_started_monotonic_ns': self.segment_started,
                  'previous_started_monotonic_ns': self.previous_started,
                  'capability_errors': self.errors, **evidence_time()}
        try:
            save(self.run/'process-evidence/resource-status.json', status)
        except OSError as error:
            print(f'resource status failed: {json.dumps(evidence_error(error))}', file=sys.stderr, flush=True)

def _signal_process(target, sig, run, reason, *, group=False):
    pid = target if isinstance(target, int) else target.pid
    method = 'killpg' if group else 'kill' if isinstance(target, int) else 'Popen.send_signal'
    identifier = uuid.uuid4().hex
    row = {'kind': 'signal', 'request_id': identifier, 'phase': 'request',
           'sender': process_identity(os.getpid()), 'target': process_identity(pid),
           'target_kind': 'pgid' if group else 'pid', 'target_id': pid,
           'signal': int(sig), 'reason': reason, 'method': method}
    if run is not None:
        process_evidence(run, 'operations.jsonl', row)
    try:
        if group:
            os.killpg(pid, sig)
        elif isinstance(target, int):
            os.kill(pid, sig)
        else:
            target.send_signal(sig)
    except BaseException as error:
        if run is not None:
            process_evidence(run, 'operations.jsonl', {**row, 'phase': 'result',
                                                       'result': 'error', 'error': evidence_error(error)})
        raise
    if run is not None:
        process_evidence(run, 'operations.jsonl', {**row, 'phase': 'result', 'result': 'returned'})

def _wait_process(proc, run, reason, *, timeout=None):
    row = {'kind': 'wait', 'request_id': uuid.uuid4().hex, 'phase': 'request',
           'pid': proc.pid, 'reason': reason, 'timeout_seconds': timeout}
    if run is not None:
        process_evidence(run, 'operations.jsonl', row)
    try:
        code = proc.wait(timeout=timeout)
    except BaseException as error:
        if run is not None:
            process_evidence(run, 'operations.jsonl', {**row, 'phase': 'result',
                                                       'result': 'error', 'error': evidence_error(error)})
        raise
    if run is not None:
        process_evidence(run, 'operations.jsonl', {**row, 'phase': 'result', 'result': 'reaped',
                                                   'exit_code': code, 'signal': -code if code < 0 else None})
    return code

def start_local_telemetry(run):
    """Consume the receiver declared by the ready execution context."""
    attempt_id = os.environ.get('FACTORY26_EXP_ATTEMPT_ID')
    if attempt_id:
        service = json.loads(os.environ.get('FACTORY26_EXP_SERVICES', '{}')).get('telemetry', {})
        if service.get('owner') not in {'runner', 'runner-payload'} or service.get('status') not in {'ready', 'disabled'}:
            raise ValueError('Harness 入口需要 runner 明确声明 telemetry 已就绪或关闭')
        if service['status'] == 'disabled':
            return None, {'status': 'disabled'}
    external = os.environ.get('FACTORY26_EXP_TELEMETRY_BINDING')
    if external:
        binding = json.loads(external)
        for name in ('endpoint', 'token', 'attempt_id', 'stream_id', 'collector_epoch'):
            if not binding.get(name):
                raise ValueError(f'runner telemetry binding 缺少 {name}')
        expected = os.environ.get('FACTORY26_EXP_ATTEMPT_ID')
        if not expected or binding['attempt_id'] != expected:
            raise ValueError('runner telemetry binding 与当前 attempt 不一致')
        for field in ('stream_id', 'collector_epoch'):
            expected = os.environ.get('FACTORY26_EXP_' + field.upper())
            if expected and binding[field] != expected:
                raise ValueError(f'runner telemetry binding 与当前 {field} 不一致')
        return None, binding
    if attempt_id:
        raise ValueError('runner telemetry 已就绪但未提供当前 attempt 的 receiver binding')
    raise ValueError('telemetry creation belongs to the facility bootstrap; Harness needs an explicit ready/disabled service')


def telemetry_environment(binding):
    if binding.get('status') == 'disabled':
        return {'OTEL_SDK_DISABLED': 'true'}
    endpoint = binding['endpoint']
    headers = 'x-experiment-token=' + binding['token']
    values = dict(OTEL_EXPORTER_OTLP_ENDPOINT=endpoint,
                  OTEL_EXPORTER_OTLP_PROTOCOL='http/protobuf',
                  OTEL_EXPORTER_OTLP_HEADERS=headers,
                  OTEL_EXPORTER_OTLP_COMPRESSION='none')
    for name in ('TRACES', 'LOGS', 'METRICS'):
        prefix = 'OTEL_EXPORTER_OTLP_' + name
        values[prefix + '_ENDPOINT'] = endpoint + '/v1/' + name.lower()
        values[prefix + '_PROTOCOL'] = 'http/protobuf'
        values[prefix + '_HEADERS'] = headers
        values[prefix + '_COMPRESSION'] = 'none'
    return values

def stop_local_telemetry(process):
    run = getattr(process, '_factory26_evidence_run', None)
    _signal_process(process, signal.SIGTERM, run, 'collector-stop')
    try:
        code = _wait_process(process, run, 'collector-stop', timeout=30)
    except subprocess.TimeoutExpired:
        _signal_process(process, signal.SIGKILL, run, 'collector-stop-timeout')
        _wait_process(process, run, 'collector-stop-timeout')
        raise TimeoutError('OTLP receiver did not stop within 30 seconds')
    if code:
        raise RuntimeError(f'OTLP receiver exited {code}')

def budgeted_pi(runtime, run):
    """Both Braid and pi-subagents launch Pi through the same per-run spending guard."""
    pi = runtime/'bin/pi' if (runtime/'bin/pi').is_file() else runtime/'node_modules/.bin/pi'
    guard = Path(__file__).resolve().with_name('model_budget.mjs')
    if not guard.is_file():
        raise FileNotFoundError(guard)
    launcher = run/'budgeted-pi'
    launcher.write_text('#!/bin/sh\n'
        +'export FACTORY26_MODEL_BUDGET_PATH='+shlex.quote(str(run/'expensive-model-session'))+'\n'
        +'export PI_SUBAGENT_PI_BINARY='+shlex.quote(str(launcher))+'\n'
        +'if [ -n "${FACTORY_NATIVE_RUNTIME_MODULE:-}" ]; then\n'
        +'  set -- --extension "$FACTORY_NATIVE_RUNTIME_MODULE" "$@"\n'
        +'fi\n'
        +'if [ -n "${FACTORY26_PI_TIMING_EXTENSION:-}" ]; then\n'
        +'  set -- --extension "$FACTORY26_PI_TIMING_EXTENSION" "$@"\n'
        +'fi\n'
        +'exec '+shlex.join([str(pi), '--extension', str(guard)])+' "$@"\n')
    launcher.chmod(0o755)
    return launcher


def runtime_resource_environment(runtime, run):
    """Configure one generation's shared resource admission and native ownership."""
    helper = Path(__file__).resolve().with_name('runtime_resources.py')
    native_module = Path(runtime)/'native-managed.mjs'
    for source in (helper, native_module):
        if not source.is_file():
            raise FileNotFoundError(source)
    directory = Path(run)/'process-control'
    services = json.loads(os.environ.get('FACTORY26_EXP_SERVICES', '{}'))
    resource = services.get('resource_evidence')
    if os.environ.get('FACTORY26_EXP_ATTEMPT_ID'):
        if not resource or resource.get('owner') not in {'runner', 'runner-payload'} or resource.get('status') != 'ready' or not resource.get('sample_path'):
            raise ValueError('Harness 入口需要 runner 已就绪的 ResourceEvidence 与明确样本路径')
        sample_path = Path(resource['sample_path'])
    else:
        sample_path = Path(os.environ.get('FACTORY26_EXP_RESOURCE_SAMPLE', str(Path(run)/'process-evidence/resource-latest.json')))
    subprocess.run([sys.executable, str(helper), 'configure', '--directory', str(directory),
                    '--sample-path', str(sample_path)], check=True, stdout=subprocess.DEVNULL)
    return {'FACTORY_RESOURCE_HELPER': str(helper), 'FACTORY_RESOURCE_PYTHON': sys.executable,
            'FACTORY_RESOURCE_DIR': str(directory),
            'FACTORY_NATIVE_RUNTIME_MODULE': str(native_module)}


def start_shared_proxy(runtime, run, env):
    """Own the run's shared proxy outside any member's finite tool execution."""
    import http.client
    port = int(env['PORTLESS_PORT'])
    if not 0 < port < 65536 or env.get('PORTLESS_HTTPS') != '0':
        raise ValueError('shared proxy requires the declared unprivileged HTTP run endpoint')

    def ready():
        connection = http.client.HTTPConnection('127.0.0.1', port, timeout=.5)
        try:
            connection.request('HEAD', '/')
            response = connection.getresponse()
            return response.getheader('X-Portless') == '1'
        except (OSError, http.client.HTTPException):
            return False
        finally:
            connection.close()

    if ready():
        raise RuntimeError(f'portless proxy already listens on {port}; this run has no owner handle')
    environment = {key: value for key, value in env.items() if key not in {
        'FACTORY_NATIVE_EXECUTION_ID', 'FACTORY_NATIVE_EXECUTION_DIR', 'FACTORY_NATIVE_START_ID'}}
    command = [str(runtime/'bin/node'), str(runtime/'node_modules/portless/dist/cli.js'),
               'proxy', 'start', '--foreground', '--skip-trust', '--no-tls', '-p', str(port)]
    log = run/'shared-proxy.log'
    try:
        from .state_writer import gate, spawn
    except ImportError:
        from state_writer import gate, spawn
    gate(environment)
    with log.open('w') as stream:
        child = spawn(command, cwd=run, environment=environment,role='service',start_new_session=True,
                                 stdout=stream, stderr=subprocess.STDOUT)
    identity = process_identity(child.pid)
    process_evidence(run, 'operations.jsonl', {'kind': 'process_started', 'role': 'shared-proxy',
                                              'process': identity, 'log': str(log)})
    try:
        deadline = time.monotonic() + 30
        while child.poll() is None:
            if ready():
                save(run/'shared-proxy.json', {'owner': 'run', 'process': identity, 'port': port,
                                               'ready_header': 'X-Portless: 1', 'log': str(log)})
                return child
            if time.monotonic() >= deadline:
                raise TimeoutError(f'portless proxy readiness timed out; raw output: {log}')
            time.sleep(.1)
        raise RuntimeError(f'portless proxy exited {child.returncode} before readiness; raw output: {log}')
    except BaseException:
        stop_shared_proxy(child, run)
        raise


def stop_shared_proxy(child, run):
    """Wait the foreground owner; never infer ownership from a stale proxy PID file."""
    _signal_process(child, signal.SIGTERM, run, 'shared-proxy-stop')
    try:
        result = _wait_process(child, run, 'shared-proxy-stop', timeout=5)
    except subprocess.TimeoutExpired:
        _signal_process(child, signal.SIGKILL, run, 'shared-proxy-stop-timeout')
        result = _wait_process(child, run, 'shared-proxy-stop-timeout')

    try:
        from .state_writer import closed
    except ImportError:
        from state_writer import closed
    closed(getattr(child,'_state_writer',None))
    return result

def read_provider_environment(path, allowed=None):
    """Read one private provider-env JSON for the run-owned gateway only."""
    path = Path(path).resolve(strict=True)
    if path.stat().st_mode & 0o077:
        # The official Docker runner extracts ZIP entries with its default
        # umask. Tighten the private file at the container boundary before
        # reading it; never relax the contract or copy the value elsewhere.
        path.chmod(0o600)
    value = json.loads(path.read_text())
    if isinstance(value, dict) and set(value) == {'environment'}:
        value = value['environment']
    if not isinstance(value, dict) or not value:
        raise ValueError('provider-env must be a non-empty object')
    if allowed is not None and set(value) - set(allowed):
        raise ValueError('provider-env contains an undeclared credential')
    if any(not isinstance(name, str) or not name.isidentifier() or
           not isinstance(secret, str) or not secret for name, secret in value.items()):
        raise ValueError('provider-env contains an invalid name or empty credential')
    return value


def start_model_gateway(runtime, run, env, config, *, bindings=None, gateway_routes=None,
                        port=4011, host='127.0.0.1', provider_env=None,
                        preserve_parameters=None):
    """Start one run-owned frozen LiteLLM gateway and return its local contract.

    ``bindings`` is the already-frozen native route map.  The returned
    ``pi_environment`` contains only the local gateway token plus the rewritten
    bindings; upstream provider secrets stay in the gateway child.
    """
    if preserve_parameters is None:
        raise ValueError('gateway preserve_parameters must be frozen explicitly')
    runtime = Path(runtime).resolve(strict=True)
    run = Path(run).resolve(strict=True)
    config = Path(config).resolve(strict=True)
    launcher = runtime/'bin/litellm'
    if not launcher.is_file() or not os.access(launcher, os.X_OK):
        raise FileNotFoundError(f'冻结 runtime 缺少 LiteLLM launcher: {launcher}')
    if not config.is_file() or not config.resolve().is_relative_to(run):
        raise ValueError('gateway config must be a run-local frozen file')
    if not 0 < int(port) < 65536 or host not in {'127.0.0.1', '::1'}:
        raise ValueError('run-owned gateway must use a loopback unprivileged port')
    environment = dict(env)
    values = read_provider_environment(provider_env) if provider_env is not None else {}
    if gateway_routes is not None:
        if isinstance(gateway_routes, (str, Path)):
            route_path = Path(gateway_routes).resolve(strict=True)
            gateway_routes = json.loads(route_path.read_text())
        if not isinstance(gateway_routes, dict):
            raise ValueError('gateway-routes must be an object keyed by stable alias')
        if any(not isinstance(alias, str) or not isinstance(chain, list) or
               not chain or any(not isinstance(item, str) or not item for item in chain)
               for alias, chain in gateway_routes.items()):
            raise ValueError('gateway-routes values must be non-empty deployment ID lists')
    environment.update(values)
    state = run/'model-gateway'
    state.mkdir(mode=0o700, exist_ok=True)
    log = state/'gateway.log'
    (state/'bindings').mkdir(mode=0o700, exist_ok=True)
    code = state/'code'
    code.mkdir(mode=0o700, exist_ok=True)
    support_root = Path(__file__).resolve().parent
    for name in ('hackathon_gateway_compat.py', 'responses_compat.py'):
        shutil.copy2(support_root/name, code/name)
    route_record = state/'gateway-routes.json'
    if gateway_routes is not None:
        route_record.write_text(json.dumps(gateway_routes, ensure_ascii=False, indent=2) + '\n')
        route_record.chmod(0o600)
    local_token = secrets.token_urlsafe(32)
    master_key = secrets.token_urlsafe(32)
    binding_id = hashlib.sha256(local_token.encode()).hexdigest()
    binding_path = state/'bindings'/f'{binding_id}.json'
    binding = {'binding_id': binding_id,
               'run_id': environment.get('FACTORY26_EXP_RUN_ID', run.name),
               'attempt_id': environment.get('FACTORY26_EXP_ATTEMPT_ID'),
               'experiment_id': environment.get('FACTORY26_EXP_EXPERIMENT_ID'),
               'incarnation': environment.get('FACTORY26_EXP_INCARNATION_ID'),
               'config_sha256': None}
    # Materialize the run-owned config so direct callers cannot accidentally
    # omit auth/callbacks or leave upstream base URLs unresolved.
    config_value = json.loads(config.read_text())
    config_value.setdefault('general_settings', {}).update(
        master_key='os.environ/LITELLM_MASTER_KEY',
        custom_auth='hackathon_gateway_compat.user_api_key_auth')
    config_value.setdefault('litellm_settings', {}).update(
        telemetry=False, callbacks=['hackathon_gateway_compat.proxy_handler_instance'])
    selected_env = set()
    for entry in config_value.get('model_list', []):
        params = entry.setdefault('litellm_params', {})
        params.setdefault('use_chat_completions_api', True)
        base = params.get('api_base')
        if isinstance(base, str) and base.startswith('os.environ/'):
            name = base.removeprefix('os.environ/')
            selected_env.add(name)
            if not environment.get(name):
                raise ValueError(f'gateway config references missing provider endpoint: {name}')
            params['api_base'] = environment[name]
        key_ref = params.get('api_key')
        if isinstance(key_ref, str) and key_ref.startswith('os.environ/'):
            selected_env.add(key_ref.removeprefix('os.environ/'))
    if set(values) - selected_env:
        raise ValueError('provider-env contains credentials outside the selected gateway catalog')
    config.write_text(json.dumps(config_value, ensure_ascii=False, indent=2) + '\n')
    config.chmod(0o600)
    binding['config_sha256'] = hashlib.sha256(config.read_bytes()).hexdigest()
    binding_path.write_text(json.dumps(binding, ensure_ascii=False) + '\n')
    binding_path.chmod(0o600)
    environment.update(LITELLM_MASTER_KEY=master_key,
                       GATEWAY_REQUEST_LOG=str(state/'request-metadata.jsonl'),
                       GATEWAY_BINDINGS_DIR=str(state/'bindings'),
                       GATEWAY_PRESERVE_PARAMETERS='1' if preserve_parameters else '0',
                       PYTHONPATH=os.pathsep.join((str(code), str(runtime/'python'),
                                                   environment.get('PYTHONPATH', ''))).strip(os.pathsep))
    command = [str(launcher), '--config', str(config), '--host', host, '--port', str(port)]
    with log.open('a') as stream:
        child = subprocess.Popen(command, cwd=run, env=environment, stdout=stream,
                                 stderr=subprocess.STDOUT, start_new_session=True)
    identity = process_identity(child.pid)
    process_evidence(run, 'operations.jsonl', {'kind': 'process_started', 'role': 'model-gateway',
                                               'process': identity, 'log': str(log)})
    try:
        from urllib.request import urlopen
        deadline = time.monotonic() + 30
        while child.poll() is None and time.monotonic() < deadline:
            try:
                with urlopen(f'http://{host}:{port}/health/liveliness', timeout=1) as response:
                    if response.status == 200:
                        endpoint = f'http://{host}:{port}/v1'
                        local_bindings = None
                        if bindings is not None:
                            local_bindings = {}
                            for name, route in bindings.items():
                                route = dict(route)
                                route['base_url'] = endpoint
                                route['credential_env'] = 'FACTORY26_GATEWAY_TOKEN'
                                local_bindings[name] = route
                        # Remove only the credentials explicitly assembled for this
                        # gateway.  Tool credentials (for example Context7/Exa) have
                        # a separate contract and must remain available to Pi.
                        pi_environment = {key: value for key, value in env.items()
                                          if key not in values}
                        pi_environment['FACTORY26_GATEWAY_TOKEN'] = local_token
                        if local_bindings is not None:
                            pi_environment['FACTORY26_MODEL_BINDINGS'] = json.dumps(local_bindings, separators=(',', ':'))
                        handle = {'owner': 'run', 'process': child, 'identity': identity,
                                  'pid': child.pid, 'endpoint': endpoint, 'port': port,
                                  'config': str(config), 'log': str(log),
                                  'routes': str(route_record) if gateway_routes is not None else None,
                                  'pi_environment': pi_environment}
                        save(run/'model-gateway.json', {key: value for key, value in handle.items()
                                                       if key not in {'process', 'pi_environment'}})
                        return handle
            except OSError:
                pass
            time.sleep(.2)
        raise RuntimeError(f'model gateway readiness timed out; raw output: {log}')
    except BaseException:
        _signal_process(child, signal.SIGTERM, run, 'model-gateway-start-failed')
        raise

def stop_model_gateway(handle, run):
    """Stop only the process owned by start_model_gateway."""
    child = handle['process'] if isinstance(handle, dict) else handle
    return _wait_process(child, run, 'model-gateway-stop', timeout=5) if child.poll() is not None else (
        _signal_process(child, signal.SIGTERM, run, 'model-gateway-stop') or
        _wait_process(child, run, 'model-gateway-stop', timeout=5))


def browser_executable(runtime):
    """Use the portable wrapper or the browser paired with this runtime's Playwright."""
    packaged = runtime/'bin/chromium'
    if packaged.is_file():
        return packaged
    binary = Path(subprocess.check_output(
        ['node', '-e', "process.stdout.write(require('playwright').chromium.executablePath())"],
        cwd=runtime, env=dict(os.environ, PLAYWRIGHT_BROWSERS_PATH=str(runtime/'.playwright')),
        text=True))
    if not binary.is_file():
        raise FileNotFoundError(f'{binary}; run runtime.py prepare')
    return binary

def copy_skill(source, destination):
    """Copy the published skill resources, excluding repository maintenance files.

    Factory's skills use SKILL.md and the standard resource directories.
    Materialize source links so the installed skill remains self-contained.
    """
    source, destination = Path(source), Path(destination)
    destination.mkdir(parents=True)
    shutil.copy2(source/'SKILL.md', destination/'SKILL.md')
    for name in ('references', 'assets', 'scripts'):
        if (source/name).is_dir():
            shutil.copytree(source/name, destination/name)
    for pattern in ('LICENSE*', 'NOTICE*'):
        for path in source.glob(pattern):
            if path.is_file():
                shutil.copy2(path, destination/path.name)


def capture(*args):
    return subprocess.check_output(args,text=True).strip()

def save(path, value):
    temporary = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)

def phase(path, metadata, name, log=None, **fields):
    now = time.time()
    metadata.update(phase=name, phase_started_at=now, updated_at=now, phase_log=log, **fields)
    save(path, metadata)

def hashes(folder):
    return {str(p.relative_to(folder)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(folder.rglob("*")) if p.is_file()
            and not {"node_modules", ".git", "__pycache__"}.intersection(p.relative_to(folder).parts)}

def copy_application(source, output):
    root=source.resolve()
    omitted={'node_modules','.git','__pycache__','.braid'}
    def ignore(folder, names):
        for name in set(names)-omitted:
            path=Path(folder)/name
            if path.is_symlink() and not path.resolve().is_relative_to(root):
                raise RuntimeError(f'应用链接指向工作区外: {path.relative_to(source)}')
        return omitted.intersection(names)
    shutil.copytree(source,output,ignore=ignore)

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

def signal_group(proc, sig, run=None, reason='process-group-cleanup'):
    try:
        _signal_process(proc, sig, run, reason, group=True)
    except ProcessLookupError:
        pass
    except PermissionError:
        # macOS can retain only inaccessible zombie group members after exit.
        states=capture('ps','-ax','-o','pgid=,stat=').splitlines()
        if any(line.split()[0]==str(proc.pid) and not line.split()[1].startswith('Z')
               for line in states if len(line.split())==2):
            raise

def stop(proc, run=None):
    signal_group(proc,signal.SIGTERM,run)
    try: _wait_process(proc,run,'process-group-cleanup',timeout=5)
    except subprocess.TimeoutExpired: pass
    signal_group(proc,signal.SIGKILL,run)
    _wait_process(proc,run,'process-group-cleanup')

def workspace_processes(work):
    """Include app-server tool jobs that start their own process sessions."""
    found=[]
    if platform.system()=='Linux':
        for entry in Path('/proc').iterdir():
            if not entry.name.isdigit(): continue
            try:
                cwd=(entry/'cwd').resolve(strict=True)
                if cwd.is_relative_to(work): found.append(int(entry.name))
            except (OSError,RuntimeError): pass
    else:
        result=subprocess.run(['lsof','-a','-u',str(os.getuid()),'-d','cwd','-F','pn'],capture_output=True,text=True)
        if result.returncode not in (0,1): raise RuntimeError('cannot inspect workspace processes')
        pid=None
        for line in result.stdout.splitlines():
            if line.startswith('p'): pid=int(line[1:])
            elif line.startswith('n') and pid and Path(line[1:]).is_relative_to(work): found.append(pid)
    return [pid for pid in found if pid!=os.getpid()]

def cleanup_workspace(work):
    pids=workspace_processes(work)
    for pid in pids:
        try: _signal_process(pid,signal.SIGTERM,work,'workspace-cleanup')
        except ProcessLookupError: pass
    if pids: time.sleep(.2)
    for pid in workspace_processes(work):
        try: _signal_process(pid,signal.SIGKILL,work,'workspace-cleanup')
        except ProcessLookupError: pass
    remaining=workspace_processes(work)
    if remaining: raise RuntimeError(f'workspace processes remain after cleanup: {remaining}')
    return pids

def logged(command, cwd, env, log, cleanup_errors=None):
    try:
        from .state_writer import gate, spawn, closed
    except ImportError:
        from state_writer import gate, spawn, closed
    gate(env)
    with log.open("w") as output:
        proc = spawn(command, cwd=cwd, environment=env,role='native',stdout=output,
                                stderr=subprocess.STDOUT, start_new_session=True)
        state_receipt=proc._state_writer
        process_evidence(log.parent, 'operations.jsonl', {'kind': 'process_started', 'role': 'logged-command',
                                                         'process': process_identity(proc.pid), 'log': str(log)})
        try:
            return _wait_process(proc,log.parent,'logged-command')
        finally:
            try: stop(proc,log.parent)
            except PermissionError as exc:
                # Generation has an outer, verified workspace cleanup before freezing.
                if cleanup_errors is None or proc.returncode is None: raise
                cleanup_errors.append({'pid':proc.pid,'exit_code':proc.returncode,'error':str(exc)})
            if proc.returncode is not None: closed(state_receipt)

def validate_application(app):
    for directory, script in (('frontend', 'build'), ('backend', 'start')):
        path = app/directory/'package.json'
        package = json.loads(path.read_text())
        if not isinstance(package.get('scripts', {}).get(script), str) or not package['scripts'][script].strip():
            raise ValueError(f'参赛应用缺少 {directory} 的 {script} script')
    forbidden = RESERVED.intersection(p.name for p in app.iterdir())
    if forbidden or (app/'deploy.sh').exists():
        raise ValueError('参赛应用包含平台保留路径或本地专用 deploy.sh')

def deliver(app, output):
    validate_application(app)
    entries = list(app.iterdir())
    if any((output/entry.name).exists() or (output/entry.name).is_symlink() for entry in entries):
        raise ValueError('输出目录已有同名应用文件，拒绝覆盖')
    # Validate every link before writing any platform output.
    for path in app.rglob('*'):
        if path.is_symlink() and not path.resolve().is_relative_to(app.resolve()):
            raise ValueError('应用链接指向冻结目录之外')
    for entry in entries:
        target = output/entry.name
        if entry.is_dir():
            shutil.copytree(entry, target, ignore=shutil.ignore_patterns('node_modules', '__pycache__', '.git'))
        else:
            shutil.copy2(entry, target)


import sys

def verify_package(root):
    root = root.resolve()
    manifest = json.loads((root/'package-manifest.json').read_text())
    if (manifest.get('schema_version'), manifest.get('platform'), manifest.get('python')) != (1, 'linux-x86_64', '3.12'):
        raise ValueError('不支持的参赛制品格式')
    if platform.system() != 'Linux' or platform.machine() != 'x86_64' or sys.version_info[:2] != (3, 12):
        raise RuntimeError('参赛包需要 Linux x86_64、CPython 3.12')
    files = manifest['files']
    if not files or 'package-manifest.json' in files:
        raise ValueError('参赛载荷清单无效')
    if any(p.is_symlink() for p in root.rglob('*')):
        raise ValueError('参赛载荷不得包含符号链接')
    actual = {str(p.relative_to(root)) for p in root.rglob('*')
              if p.is_file() and '__pycache__' not in p.parts and p != root/'package-manifest.json'}
    if actual != set(files):
        raise ValueError('参赛包包含缺失或未登记载荷')
    for name, record in files.items():
        path = root/name
        if Path(name).is_absolute() or '..' in Path(name).parts or path.is_symlink() or not path.resolve().is_relative_to(root):
            raise ValueError('参赛载荷路径越界')
        if hashlib.sha256(path.read_bytes()).hexdigest() != record['sha256']:
            raise ValueError(f'参赛载荷哈希不匹配：{name}')
        # Python ZIP extraction does not preserve executable permission bits.
        if record['executable']:
            mode = path.stat().st_mode
            if mode & 0o111 != 0o111:
                path.chmod(mode | 0o111)
    return manifest


def model_bindings(base_url=None, visual_url=None, *, require_key=True):
    """Consume recipe-owned native provider routes without choosing a supplier."""
    raw = os.environ.get('FACTORY26_MODEL_BINDINGS')
    if raw:
        bindings = json.loads(raw)
    else:
        endpoint = base_url or os.environ.get('OPENAI_BASE_URL') or os.environ.get('FACTORY26_BASE_URL')
        if not endpoint:
            raise ValueError('模型配方必须提供 FACTORY26_MODEL_BINDINGS 或明确 base URL')
        bindings = {
            'factory26': {'provider': os.environ.get('FACTORY26_MODEL_PROVIDER'),
                          'base_url': endpoint, 'credential_env': 'FACTORY26_API_KEY'},
            'factory26-visual': {'provider': os.environ.get('FACTORY26_VISUAL_PROVIDER'),
                                 'base_url': visual_url or endpoint,
                                 'credential_env': 'FACTORY26_VISUAL_API_KEY' if visual_url else 'FACTORY26_API_KEY'},
        }
    if not isinstance(bindings, dict) or not bindings:
        raise ValueError('模型绑定需要非空 provider 映射')
    environment = dict(os.environ)
    if not raw:
        if os.environ.get('OPENAI_API_KEY'):
            environment['FACTORY26_API_KEY'] = os.environ['OPENAI_API_KEY']
        if visual_url and os.environ.get('VISUAL_API_KEY'):
            environment['FACTORY26_VISUAL_API_KEY'] = os.environ['VISUAL_API_KEY']
    for name, route in bindings.items():
        if not isinstance(route, dict) or not route.get('provider') or not route.get('base_url'):
            raise ValueError(f'模型绑定缺少显式 provider/base_url：{name}')
        if set(route) - {'provider', 'base_url', 'credential_env', 'model', 'model_id'}:
            raise ValueError(f'模型绑定包含未知字段：{name}')
        if 'model_id' in route and (not isinstance(route['model_id'], str) or not route['model_id'].strip()):
            raise ValueError(f'模型绑定 model_id 必须为非空字符串：{name}')
        from urllib.parse import urlsplit
        endpoint = urlsplit(route['base_url'])
        if endpoint.scheme not in {'http', 'https'} or not endpoint.hostname or endpoint.username or endpoint.password or endpoint.query or endpoint.fragment:
            raise ValueError(f'模型绑定 base_url 必须为不含凭据的 HTTP endpoint：{name}')
        variable = route.get('credential_env', '')
        if not variable or not variable.isidentifier():
            raise ValueError(f'模型绑定 credential_env 无效：{name}')
        if require_key and not environment.get(variable):
            raise ValueError(f'模型绑定缺少凭据环境变量：{name}/{variable}')
    return bindings, environment


def native_model_route(provider, model, bindings):
    """Resolve an explicit provider/model override to one native transport identity."""
    selector = provider + '/' + model
    if selector in bindings:
        alias = provider + '-route-' + hashlib.sha256(selector.encode()).hexdigest()[:12]
        route = bindings[selector]
        return alias, route.get('model_id', model), route
    for key, route in bindings.items():
        if '/' in key:
            original_provider, original_model = key.split('/', 1)
            alias = original_provider + '-route-' + hashlib.sha256(key.encode()).hexdigest()[:12]
            if provider == alias:
                return alias, route.get('model_id', original_model), route
    if provider not in bindings:
        raise ValueError(f'原生模型未绑定：{selector}')
    return provider, model, bindings[provider]


def bind_native_models(value, bindings):
    """Split model-specific transports so each provider owns exactly one credential."""
    import copy
    providers = {}
    for name, provider in value['providers'].items():
        for definition in provider['models']:
            alias, model_id, route = native_model_route(name, definition['id'], bindings)
            if alias not in providers:
                providers[alias] = {k: copy.deepcopy(v) for k, v in provider.items() if k != 'models'}
                providers[alias].update(baseUrl=route['base_url'], apiKey='$' + route['credential_env'], models=[])
            model = copy.deepcopy(definition)
            model['id'] = model_id
            if 'baseUrl' in model:
                model['baseUrl'] = route['base_url']
            if any(row['id'] == model_id for row in providers[alias]['models']):
                raise ValueError(f'模型绑定产生重复原生ID：{alias}/{model_id}')
            providers[alias]['models'].append(model)
    value['providers'] = providers
    return value


def bind_native_model_scope(settings, bindings):
    """Keep each allow rule on the same models after provider transport aliases change."""
    import re
    scope = settings.get('subagents', {}).get('modelScope')
    if not scope:
        return settings
    for rule in [scope, *scope.get('agents', {}).values()]:
        allowed = rule.get('allow')
        if not allowed:
            continue
        patterns = [re.compile('^' + re.escape(pattern).replace(r'\*', '.*') + '$', re.I)
                    for pattern in allowed]
        additions = []
        for selector in bindings:
            if '/' not in selector or not any(pattern.fullmatch(selector) for pattern in patterns):
                continue
            provider, model = selector.split('/', 1)
            alias, model_id, _ = native_model_route(provider, model, bindings)
            resolved = alias + '/' + model_id
            if resolved not in allowed and resolved not in additions:
                additions.append(resolved)
        rule['allow'] = [*allowed, *additions]
    return settings


def bind_retained_native_models(value, bindings):
    """Route retained models through Pi's per-model headers, preserving identities."""
    for name, provider in value['providers'].items():
        for definition in provider['models']:
            _, model_id, route = native_model_route(name, definition['id'], bindings)
            api = definition.get('api', provider.get('api'))
            if api not in {'openai-completions', 'openai-responses'}:
                raise ValueError(f'恢复逐模型传输不支持原生API：{name}/{definition["id"]}/{api}')
            definition['baseUrl'] = route['base_url']
            # Pi keeps the native model ID in history and budgets; OpenAI APIs
            # apply these request fields last, including a declared supplier ID.
            definition['samplingParams'] = dict(definition.get('samplingParams', {}), model=model_id)
            # Pi expands this template and merges model headers after provider auth.
            # No credential value is persisted in models.json or recovery receipts.
            definition['headers'] = {key: value for key, value in definition.get('headers', {}).items()
                                     if key.lower() != 'authorization'}
            definition['headers']['Authorization'] = 'Bearer ${' + route['credential_env'] + '}'
        first = native_model_route(name, provider['models'][0]['id'], bindings)[2]
        provider.update(baseUrl=first['base_url'], apiKey='$' + first['credential_env'])
        provider['headers'] = {key: value for key, value in provider.get('headers', {}).items()
                               if key.lower() != 'authorization'}
    return value


def bind_native_role(text, bindings):
    """Rewrite only native role model frontmatter, preserving role instructions."""
    import re
    def replace(match):
        provider, model, _ = native_model_route(match[2], match[3], bindings)
        return match[1] + '"' + provider + '/' + model + '"'
    return re.sub(r'(?m)^(model:\s*)["\']?([^/\s"\']+)/([^\s"\']+)["\']?$', replace, text)
