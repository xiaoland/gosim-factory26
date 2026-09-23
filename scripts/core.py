"""Native agent transports; provider homes are supplied by the isolated run."""
import json
import hashlib
import re
import shutil
import subprocess
from pathlib import Path


_ARCHIVE_INHERITED_KEYS = (
    'profile_id', 'effective_profile_digest', 'work_item_kind', 'work_item_id',
    'assignment_generation', 'native_home',
)


def _archive_path(value, work, base=None):
    if not value:
        raise ValueError('原生会话路径缺失')
    path = Path(value)
    if not path.is_absolute():
        path = (base or work) / path
    path = path.resolve(strict=True)
    if not path.is_relative_to(work.resolve()):
        raise ValueError('原生会话路径不属于本次运行目录')
    return path


def _read_native_header(source):
    with source.open() as stream:
        raw = stream.readline()
    if not raw.strip():
        raise ValueError('原生会话缺少 header')
    header = json.loads(raw)
    if not isinstance(header, dict):
        raise ValueError('原生会话 header 不是对象')
    return header


def _native_id(provider, header):
    if provider == 'codex':
        payload = header.get('payload') or {}
        return payload.get('id') or payload.get('session_id') or header.get('id')
    if header.get('type') != 'session':
        raise ValueError('Pi 原生文件首行不是 session header；不能将 message ID 当作会话身份')
    return header.get('sessionId') or header.get('session_id') or header.get('id')


def _codex_spawn(header):
    payload = header.get('payload') or {}
    source = payload.get('source') or {}
    if not isinstance(source, dict):
        return None
    subagent = source.get('subagent') or source.get('subAgent') or {}
    if not isinstance(subagent, dict):
        return None
    spawn = subagent.get('thread_spawn')
    if not isinstance(spawn, dict) or not spawn.get('parent_thread_id'):
        return None
    return spawn


def _inherited(root, extra=None):
    row = {key: root[key] for key in _ARCHIVE_INHERITED_KEYS if key in root}
    if extra:
        row.update(extra)
    return row


def _child_inherited(root, extra=None):
    row = _inherited(root, extra)
    row.pop('assignment_generation', None)
    return row


def archive_sessions(output, home, work, entries):
    """Archive native sessions and passively observed parent relations."""
    output = Path(output).resolve()
    native = output/'native'
    native.mkdir(parents=True, exist_ok=True)
    work = Path(work).resolve()
    home = Path(home).resolve()
    archived = []
    seen = {}
    target_index = 0

    def error_row(row, message):
        nonlocal target_index
        failed = dict(row, native=None, sha256=None)
        failed['archive_error'] = message
        if row.get('native_session_path'):
            try:
                source = _archive_path(row['native_session_path'], work)
                if source.is_file():
                    target = native/f'{target_index:03}-unparsed-{source.name}'
                    target_index += 1
                    shutil.copy2(source, target)
                    failed['unparsed_native'] = str(target.relative_to(output))
            except (OSError, ValueError):
                pass
        archived.append(failed)
        return failed

    def copy_one(row, provider, source, actual_id):
        nonlocal target_index
        if not actual_id:
            raise ValueError('原生会话 header 缺少 native UUID')
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        key = (provider, str(actual_id))
        previous = seen.get(key)
        if previous:
            if previous['source_path'] != str(source) or previous['sha256'] != digest:
                error_row(row, f'原生身份冲突: {provider}/{actual_id} 对应不同内容或路径')
                return None
            return previous
        target = native/f'{target_index:03}-{source.name}'
        target_index += 1
        shutil.copy2(source, target)
        archived_row = dict(row, source_path=str(source), native=str(target.relative_to(output)),
                            sha256=hashlib.sha256(target.read_bytes()).hexdigest(), native_id=str(actual_id))
        archived.append(archived_row)
        seen[key] = archived_row
        return archived_row

    def root_source(row, provider):
        source = row.get('native_session_path')
        session_id = row.get('session_id')
        native_home = None
        if provider == 'pi' and row.get('native_home'):
            native_home = _archive_path(row['native_home'], work)
            tree_path = native_home/'.factory'/'session-tree.json'
            if tree_path.exists():
                try:
                    tree = json.loads(tree_path.read_text())
                    root_ids = {str(session_id), str(row.get('native_session_id'))}
                    root_ids.discard('None')
                    if str(tree.get('parent_native_session_id')) in root_ids:
                        source = tree.get('parent_session_file') or source
                except (OSError, ValueError, TypeError, json.JSONDecodeError):
                    pass
        if not source and provider == 'codex' and isinstance(session_id, str) and re.fullmatch(r'[a-fA-F0-9-]+', session_id):
            native_home = _archive_path(row['native_home'], work) if row.get('native_home') else home
            matches = list(native_home.glob(f'sessions/**/rollout-*-{session_id}.jsonl'))
            if len(matches) != 1:
                raise ValueError('Codex thread 没有唯一的原生 rollout')
            source = matches[0]
        if provider == 'pi' and native_home and source and not Path(source).is_file():
            native_id = row.get('native_session_id')
            matches = list(native_home.glob(f'sessions/**/*_{native_id}.jsonl')) if native_id else []
            if len(matches) != 1:
                raise ValueError('Pi 根会话没有唯一的规范 session 文件')
            source = matches[0]
        return _archive_path(source, work)

    def archive_pi_children(root, root_archived, provider):
        nonlocal target_index
        native_home = root.get('native_home')
        if not native_home:
            return
        child_home = _archive_path(native_home, work)
        factory_dir = child_home/'.factory'
        tree_path = factory_dir/'session-tree.json'
        if not tree_path.exists():
            root_archived['observer_diagnostic_status'] = 'unknown'
            return
        tree_source = _archive_path(tree_path, work)
        tree = json.loads(tree_source.read_text())
        if not isinstance(tree, dict) or not isinstance(tree.get('children'), list):
            raise ValueError('Pi session-tree manifest 格式无效')
        tree_target = native/f'{target_index:03}-{tree_source.name}'
        target_index += 1
        shutil.copy2(tree_source, tree_target)
        root_archived['session_tree_manifest'] = str(tree_target.relative_to(output))
        root_archived['observer_diagnostic_status'] = tree.get('diagnostic_status', 'unknown')
        parent_id = tree.get('parent_native_session_id')
        root_ids = {str(root_archived.get('native_id')), str(root.get('session_id')),
                    str(root.get('native_session_id')),
                    str(root.get('native_session_path')), str(root_archived.get('source_path'))}
        root_ids.discard('None')
        if not parent_id or str(parent_id) not in root_ids:
            raise ValueError('Pi session-tree parent identity 与 Braid 根会话不一致')
        pending = list(tree['children'])
        connected = set(root_ids)
        while pending:
            progress = False
            for child in pending[:]:
                if not isinstance(child, dict):
                    pending.remove(child)
                    error_row(_inherited(root, {'provider': provider, 'parent_native_session_id': parent_id}), 'Pi child evidence 不是对象')
                    continue
                child_parent = child.get('parent_session_id') or child.get('parent_native_session_id')
                if not child_parent or str(child_parent) not in connected:
                    continue
                pending.remove(child)
                progress = True
                child_id = child.get('child_session_id')
                source_value = child.get('session_file')
                row = _child_inherited(root, {
                    'provider': provider, 'session_id': child_id,
                    'parent_native_session_id': str(child_parent),
                    'native_role': child.get('native_role') or child.get('role'),
                    'evidence_source': child.get('evidence_source'),
                    'mode': child.get('mode'), 'run_id': child.get('run_id'),
                    'child_id': child.get('child_id'),
                })
                if child.get('artifact_paths') is not None:
                    row['artifact_paths'] = child['artifact_paths']
                row['association_status'] = child.get('association_status', 'unknown')
                row = {key: value for key, value in row.items() if value is not None}
                try:
                    if not child_id or not source_value or not child.get('evidence_source'):
                        raise ValueError('Pi child evidence 缺少 child_session_id、session_file 或 evidence_source')
                    source = _archive_path(source_value, work, child_home)
                    row['native_session_path'] = str(source)
                    header = _read_native_header(source)
                    actual_id = _native_id(provider, header)
                    if str(actual_id) != str(child_id):
                        raise ValueError('Pi child header 身份与 child_session_id 不一致')
                    archived_child = copy_one(row, provider, source, actual_id)
                    if archived_child:
                        connected.add(str(child_id))
                        archived_child.setdefault('native_parent', str(child_parent))
                except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
                    row['association_status'] = 'partial'
                    error_row(row, str(exc))
            if not progress:
                for child in pending:
                    error_row(_child_inherited(root, {'provider':provider, 'session_id':child.get('child_session_id'),
                              'association_status':'partial'}), 'Pi child 没有连通到声明父会话的身份链')
                break

    def archive_codex_children(root, root_archived, provider):
        native_home = root.get('native_home')
        if not native_home:
            return
        codex_home = _archive_path(native_home, work)
        root_id = str(root_archived.get('native_id'))
        known = {root_id}
        candidates = []
        for source in sorted(codex_home.rglob('rollout-*.jsonl')):
            try:
                header = _read_native_header(source)
                actual_id = _native_id(provider, header)
                spawn = _codex_spawn(header)
            except (OSError, ValueError, TypeError, json.JSONDecodeError):
                continue
            if actual_id and spawn:
                candidates.append((source, header, str(actual_id), spawn))
        while candidates:
            progress = False
            for source, header, child_id, spawn in candidates[:]:
                parent_id = str(spawn.get('parent_thread_id'))
                if parent_id not in known:
                    continue
                candidates.remove((source, header, child_id, spawn))
                progress = True
                row = _child_inherited(root, {
                    'provider': provider, 'session_id': child_id,
                    'parent_native_session_id': parent_id,
                    'native_role': spawn.get('agent_role') or spawn.get('agentRole'),
                    'evidence_source': 'codex:rollout-header.payload.source.subagent.thread_spawn',
                })
                try:
                    source = _archive_path(source, work)
                    row['native_session_path'] = str(source)
                    archived_child = copy_one(row, provider, source, child_id)
                    if archived_child:
                        known.add(child_id)
                        archived_child.setdefault('native_parent', parent_id)
                except (OSError, ValueError, TypeError) as exc:
                    error_row(row, str(exc))
                    known.add(child_id)
            if not progress:
                break

    for entry in entries:
        row = dict(entry, native=None, sha256=None)
        try:
            provider = row['provider']
            source = root_source(row, provider)
            header = _read_native_header(source)
            actual_id = _native_id(provider, header)
            session_id = row['session_id']
            if provider == 'codex' and str(actual_id) != str(session_id):
                raise ValueError('原生会话身份与 Braid 清单不同')
            if provider == 'pi' and str(actual_id) not in (str(session_id), str(row.get('native_session_id'))) \
                    and str(session_id) != str(source):
                raise ValueError('Pi 原生会话身份与清单不同')
            root_key = (provider, str(actual_id))
            root_is_new = root_key not in seen
            root_archived = copy_one(row, provider, source, actual_id)
            if root_is_new and root_archived and row.get('native_home'):
                try:
                    if provider == 'pi':
                        archive_pi_children(row, root_archived, provider)
                    elif provider == 'codex':
                        archive_codex_children(row, root_archived, provider)
                except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
                    root_archived['observer_diagnostic_status'] = 'partial'
                    root_archived['observer_diagnostic_error'] = str(exc)
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
            error_row(row, str(exc))
    valid = [row for row in archived if row.get('native') and not row.get('archive_error')]
    incomplete_observation = any(row.get('observer_diagnostic_status') in ('partial', 'unknown')
                                 or row.get('association_status') in ('partial', 'unknown') for row in archived)
    diagnostic_status = ('unknown' if not valid else 'partial'
                         if len(valid) != len(archived) or incomplete_observation else 'complete')
    manifest = {'schema_version': 1, 'diagnostic_status': diagnostic_status, 'sessions': archived}
    (native/'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n')
    return archived


def codex_turn(command, app, env, prompt, output, model, thinking):
    """Drive app-server v2; only turn/completed establishes completion."""
    with (output / 'codex-events.jsonl').open('w') as events, (output / 'codex.stderr.log').open('w') as err:
        proc = subprocess.Popen(command + ['app-server', '--stdio'], cwd=app, env=env,
                                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=err,
                                text=True, start_new_session=True)
        next_id = 0
        deferred = []
        def send(method, params, request=True):
            nonlocal next_id
            frame = {'method': method, 'params': params}
            if request:
                next_id += 1
                frame['id'] = next_id
            proc.stdin.write(json.dumps(frame) + '\n'); proc.stdin.flush()
            return next_id
        def receive():
            line = proc.stdout.readline()
            if not line:
                raise RuntimeError('Codex app-server disconnected before terminal')
            events.write(line); events.flush()
            frame = json.loads(line)
            if 'method' in frame and 'id' in frame:
                # No operator exists. Reject unsupported interactive requests explicitly.
                proc.stdin.write(json.dumps({'id':frame['id'], 'error':{'code':-32601,'message':'Unattended harness has no interactive handler'}})+'\n')
                proc.stdin.flush()
            return frame
        def request(method, params):
            request_id = send(method, params)
            while True:
                frame = receive()
                if frame.get('id') == request_id and 'method' not in frame:
                    if 'error' in frame: raise RuntimeError(str(frame['error']))
                    return frame['result']
                deferred.append(frame)
        try:
            request('initialize', {'clientInfo': {'name':'factory26','version':'1'}, 'capabilities':{'experimentalApi':True}})
            send('initialized', {}, False)
            result = request('thread/start', {'cwd':str(app), 'model':model,
                             'approvalPolicy':'never', 'sandbox':'danger-full-access', 'ephemeral':False})
            thread = result['thread']['id']
            started = request('turn/start', {'threadId':thread, 'input':[{'type':'text','text':prompt}], 'effort':thinking})
            usage = None
            while True:
                frame = deferred.pop(0) if deferred else receive()
                if frame.get('params',{}).get('threadId') != thread: continue
                if frame.get('method') == 'thread/tokenUsage/updated': usage = frame['params'].get('tokenUsage')
                if frame.get('method') == 'turn/completed':
                    turn = frame['params']['turn']
                    if turn['id'] != started['turn']['id']: continue
                    if turn['status'] != 'completed': raise RuntimeError(str(turn))
                    return {'thread_id':thread, 'native_usage':usage, 'estimated_cost':None}
        finally:
            # Imported lazily so this transport can also be used in standalone probes.
            import os, signal
            try: os.killpg(proc.pid, signal.SIGTERM)
            except ProcessLookupError: pass
            try: proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL); proc.wait()
            proc.stdin.close()
            proc.stdout.close()


def codex_config(home, base_url, model, context_window=None):
    context = f'model_context_window = {int(context_window)}\n' if context_window is not None else ''
    (home / 'config.toml').write_text(context + f'''model_supports_reasoning_summaries = true
model_reasoning_summary = "none"
model = {json.dumps(model)}
model_provider = "factory26"
approval_policy = "never"
sandbox_mode = "danger-full-access"
web_search = "disabled"
[model_providers.factory26]
name = "Factory26 competition"
base_url = {json.dumps(base_url)}
env_key = "FACTORY26_API_KEY"
wire_api = "responses"
''')
