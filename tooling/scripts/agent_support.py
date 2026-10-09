"""File, process and delivery operations; no Harness selection or orchestration."""
import hashlib,json,os,platform,selectors,shutil,signal,subprocess,sys,time,uuid
import shlex
import re
import fcntl
import errno
import traceback
from pathlib import Path

RESERVED={".arc", ".git", "requirements", ".factory26"}


def require_subagent_catalog(runtime, patch):
    """Reject stale runtime inputs before opting in to the shared catalog hook."""
    member = Path('node_modules/pi-subagents/src/extension/index.ts')
    target, patch = Path(runtime)/member, Path(patch)
    patch_text = patch.read_text()
    # The maintained patch adds an import and one contiguous event hook. Require
    # its exact additions, rather than trusting a filename or an env-token match.
    additions, current = [], []
    for line in patch_text.splitlines():
        if line.startswith('+') and not line.startswith('+++'):
            current.append(line[1:])
        elif current:
            additions.append('\n'.join(current))
            current = []
    if current:
        additions.append('\n'.join(current))
    text = target.read_text() if target.is_file() else ''
    if len(additions) != 2 or any(text.count(block) != 1 for block in additions):
        raise ValueError(f'Pi subagent catalog hook missing or mismatched: {target}; rebuild with {patch.name}; launcher opt-in cannot upgrade an old runtime')
    return {'member': str(member), 'sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
            'patch': patch.name, 'patch_sha256': hashlib.sha256(patch.read_bytes()).hexdigest()}

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
    path = run
    try:
        folder = Path(run)/'process-evidence'
        path = folder/name
        marker = path.with_suffix(path.suffix+'.capped.json')
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
    except Exception as error:
        try:
            print(f'process evidence failed: {path}: {json.dumps(evidence_error(error))}', file=sys.stderr, flush=True)
        except OSError:
            pass
        return False

try:
    from .resource_monitor import ResourceEvidence
except ImportError:
    from resource_monitor import ResourceEvidence

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
    """Configure process ownership; resource evidence never gates execution."""
    helper = Path(__file__).resolve().with_name('runtime_resources.py')
    native_module = Path(runtime)/'native-managed.mjs'
    for source in (helper, native_module):
        if not source.is_file():
            raise FileNotFoundError(source)
    directory = Path(run)/'process-control'
    subprocess.run([sys.executable, str(helper), 'configure', '--directory', str(directory)],
                   check=True, stdout=subprocess.DEVNULL)
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
    with log.open('w') as stream:
        child = subprocess.Popen(command, cwd=run, env=environment,start_new_session=True,
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


def start_model_gateway(*args, **kwargs):
    """Use the shared gateway owner for both source and installed support."""
    if __package__:
        from .model_gateway_service import start_model_gateway as start
    else:
        from model_gateway_service import start_model_gateway as start
    return start(*args, **kwargs)


def stop_model_gateway(handle, run):
    """Close the service through the same owner that launched it."""
    if __package__:
        from .model_gateway_service import stop_model_gateway as stop
    else:
        from model_gateway_service import stop_model_gateway as stop
    return stop(handle, run)


def browser_executable(runtime):
    """Use the portable wrapper or the browser paired with this runtime's Playwright."""
    packaged = runtime/'bin/chromium'
    if packaged.is_file() and any((runtime/'.playwright').glob('chromium-*/chrome-linux/chrome')):
        return packaged
    cache = os.environ.get('FACTORY26_BROWSER_CACHE_DIR')
    browser_roots = [Path(cache)] if cache else []
    browser_roots.append(runtime/'.playwright')
    for root in browser_roots:
        if root and root.is_dir():
            matches = sorted(root.glob('chromium-*/chrome-linux*/chrome'))
            if matches:
                return matches[0]
    for name in ('google-chrome', 'chromium', 'chromium-browser'):
        candidate = shutil.which(name)
        if candidate:
            return Path(candidate)
    try:
        browsers_path = browser_roots[0] if browser_roots else runtime/'.playwright'
        binary = Path(subprocess.check_output(
            ['node', '-e', "process.stdout.write(require('playwright').chromium.executablePath())"],
            cwd=runtime, env=dict(os.environ, PLAYWRIGHT_BROWSERS_PATH=str(browsers_path)),
            text=True))
    except (OSError, subprocess.CalledProcessError):
        binary = None
    return binary if binary is not None and binary.is_file() else None

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

def cleanup_workspace(work, *, evidence=None):
    """Best-effort cleanup; callers receive observed PIDs, not a stop guarantee.

    The receipt preserves inspection/signal failures and remaining identities.
    Delivery must not depend on cleanup succeeding; reclamation still requires
    the receipt's explicit stopped status.
    """
    work = Path(work).resolve()
    evidence = work if evidence is None else Path(evidence)
    errors, observed = [], set()
    def inspect():
        try:
            pids = workspace_processes(work)
            observed.update(pids)
            return pids
        except Exception as exc:
            errors.append({'operation':'inspect', 'type':type(exc).__name__, 'error':str(exc)})
            return None
    def signal_pids(pids, sig):
        for pid in pids or []:
            try:
                _signal_process(pid, sig, evidence, 'workspace-cleanup')
            except ProcessLookupError:
                pass
            except Exception as exc:
                errors.append({'operation':'signal', 'signal':int(sig), 'pid':pid,
                               'type':type(exc).__name__, 'error':str(exc)})
    pids = inspect()
    signal_pids(pids, signal.SIGTERM)
    if pids:
        time.sleep(.2)
    signal_pids(inspect(), signal.SIGKILL)
    deadline = time.monotonic() + 5
    remaining = inspect()
    while remaining and time.monotonic() < deadline:
        time.sleep(.05)
        remaining = inspect()
    identities = []
    for pid in remaining or []:
        try:
            identities.append(process_identity(pid))
        except Exception as exc:
            identities.append({'pid':pid, 'error':str(exc)})
    receipt = {'workspace':str(work), 'status':'stopped' if remaining == [] else 'unconfirmed',
               'observed_pids':sorted(observed), 'remaining_pids':remaining,
               'remaining_identities':identities, 'errors':errors, 'recorded_at':time.time()}
    try:
        save(evidence/'workspace-cleanup.json', receipt)
    except Exception as exc:
        print(f'workspace cleanup receipt unavailable: {type(exc).__name__}: {exc}; {receipt}', file=sys.stderr)
    return sorted(observed)

def workspace_cleanup_stopped(evidence):
    """A missing/unreadable receipt is not proof that workspace use ended."""
    try:
        return json.loads((Path(evidence)/'workspace-cleanup.json').read_text()).get('status') == 'stopped'
    except (OSError, ValueError, AttributeError):
        return False


def logged(command, cwd, env, log, cleanup_errors=None):
    with log.open("w") as output:
        proc = subprocess.Popen(command, cwd=cwd, env=env, stdout=output,
                                stderr=subprocess.STDOUT, start_new_session=True)
        primary_failure = False
        # Nothing after successful Popen may bypass the owned cleanup finally.
        try:
            try:
                process_evidence(log.parent, 'operations.jsonl', {
                    'kind': 'process_started', 'role': 'logged-command',
                    'process': process_identity(proc.pid), 'log': str(log)})
            except Exception:
                traceback.print_exc()
            return _wait_process(proc, log.parent, 'logged-command')
        except BaseException:
            primary_failure = True
            raise
        finally:
            try:
                stop(proc, log.parent)
            except BaseException as exc:
                traceback.print_exc()
                record = {'pid': proc.pid, 'exit_code': proc.returncode,
                          'error_type': type(exc).__name__, 'error': str(exc)}
                if cleanup_errors is not None:
                    cleanup_errors.append(record)
                # Preserve the wait/command exception if cleanup also fails.
                # Otherwise keep the established strict cleanup contract;
                # callers may defer a reaped PermissionError to workspace cleanup.
                if not primary_failure and not (
                        isinstance(exc, PermissionError) and cleanup_errors is not None
                        and proc.returncode is not None):
                    raise


def validate_application(app, *, allow_platform_paths=False):
    for directory, script in (('frontend', 'build'), ('backend', 'start')):
        path = app/directory/'package.json'
        package = json.loads(path.read_text())
        if not isinstance(package.get('scripts', {}).get(script), str) or not package['scripts'][script].strip():
            raise ValueError(f'参赛应用缺少 {directory} 的 {script} script')
    forbidden = RESERVED.intersection(p.name for p in app.iterdir())
    if (forbidden and not allow_platform_paths) or (app/'deploy.sh').exists():
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
    cache_advice = {'requested_files':0, 'errors':[]}
    if not files or 'package-manifest.json' in files:
        raise ValueError('参赛载荷清单无效')
    installed_runtime = (root/'runtime_install.py').is_file()
    thin_runtime = installed_runtime and not any(name.startswith('runtime/') for name in files)
    if any(p.is_symlink() and not (thin_runtime and p.relative_to(root).parts[0] == 'runtime')
           for p in root.rglob('*')):
        raise ValueError('参赛载荷不得包含符号链接')
    # Public packages install the runtime after delivery.  Those generated
    # files are execution state, not an unregistered submitted payload; the
    # manifest still covers every submitted member and runtime_install owns
    # the executable/material checks at the actual install boundary.
    actual = {str(p.relative_to(root)) for p in root.rglob('*')
              if p.is_file() and '__pycache__' not in p.parts and p != root/'package-manifest.json'
              and not (thin_runtime and p.relative_to(root).parts[0] in {'runtime', '.cache'})}
    if actual != set(files):
        raise ValueError('参赛包包含缺失或未登记载荷')
    for name, record in files.items():
        path = root/name
        if Path(name).is_absolute() or '..' in Path(name).parts or path.is_symlink() or not path.resolve().is_relative_to(root):
            raise ValueError('参赛载荷路径越界')
        with path.open('rb') as stream:
            actual_sha = hashlib.file_digest(stream, 'sha256').hexdigest()
            # Verifying unused runtime payloads must not retain their file cache
            # throughout a 2 GiB generation. This advises only files we read.
            if hasattr(os, 'posix_fadvise'):
                try:
                    os.posix_fadvise(stream.fileno(), 0, 0, os.POSIX_FADV_DONTNEED)
                    cache_advice['requested_files'] += 1
                except OSError as error:
                    if len(cache_advice['errors']) < 4:
                        cache_advice['errors'].append({'path':name, 'errno':error.errno, 'message':str(error)})
        if actual_sha != record['sha256']:
            raise ValueError(f'参赛载荷哈希不匹配：{name}')
        # Python ZIP extraction does not preserve executable permission bits.
        if record['executable']:
            mode = path.stat().st_mode
            if mode & 0o111 != 0o111:
                path.chmod(mode | 0o111)
    return {**manifest, 'verification_cache_advice':cache_advice}


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
        if set(route) - {'provider', 'base_url', 'credential_env', 'model', 'model_id', 'model_info'}:
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


def _apply_native_model_info(model, route):
    """Apply confirmed native fields without changing an existing request budget.

    Provider capabilities are metadata, not Pi compatibility configuration.
    Missing fields retain the variant's native behavior.
    """
    import copy
    info = route.get('model_info') or {}
    if 'contextWindow' in info:
        model['contextWindow'] = info['contextWindow']
    if 'maxTokens' in info and 'maxTokens' in model:
        model['maxTokens'] = min(model['maxTokens'], info['maxTokens'])
    if 'compat' in info:
        model['compat'] = copy.deepcopy(info['compat'])


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
            _apply_native_model_info(model, route)
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
            _apply_native_model_info(definition, route)
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
