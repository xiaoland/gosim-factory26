"""Archive native sessions and their work-item identities from completed runs."""
import json
import hashlib
import os
import re
import shutil
import stat
import time
from pathlib import Path
from urllib.parse import quote

from agent_support import save
from braid_runtime import export_telemetry


_ARCHIVE_INHERITED_KEYS = (
    'profile_id', 'effective_profile_digest', 'work_item_kind', 'work_item_id',
    'assignment_generation', 'member_login', 'native_home',
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


def _read_json(path, default=None):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return default


def _file_identity(path):
    with path.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    return {'algorithm': 'file-bytes-sha256-v1', 'sha256': digest,
            'bytes': path.stat().st_size, 'kind': 'file'}


def _tree_identity(root):
    """Hash paths, file bytes and symlink targets without following links."""
    entries = []
    total = 0
    def failed(error):
        raise error
    for directory, names, files in os.walk(root, followlinks=False, onerror=failed):
        names.sort(); files.sort()
        folder = Path(directory)
        for name in names[:]:
            path = folder/name
            relative = path.relative_to(root).as_posix()
            mode = path.lstat().st_mode
            if stat.S_ISLNK(mode):
                entries.append({'path': relative, 'type': 'link', 'target': os.readlink(path)})
                names.remove(name)
            else:
                entries.append({'path': relative, 'type': 'directory'})
        for name in files:
            path = folder/name
            relative = path.relative_to(root).as_posix()
            mode = path.lstat().st_mode
            if stat.S_ISLNK(mode):
                entries.append({'path': relative, 'type': 'link', 'target': os.readlink(path)})
            elif stat.S_ISREG(mode):
                identity = _file_identity(path)
                total += identity['bytes']
                entries.append({'path': relative, 'type': 'file',
                                'sha256': identity['sha256'],
                                'executable': bool(mode & 0o111)})
            else:
                raise ValueError(f'归档含不支持的文件类型: {path}')
    encoded = json.dumps(entries, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()
    return {'algorithm': 'tree-sha256-v1', 'sha256': hashlib.sha256(encoded).hexdigest(),
            'bytes': total, 'entries': len(entries), 'kind': 'directory'}


def _native_preservation_gaps(output, manifest):
    sessions = manifest.get('sessions')
    if not isinstance(sessions, list):
        return ['native manifest 缺少 sessions 清单']
    gaps = []
    for index, row in enumerate(sessions):
        if not isinstance(row, dict):
            gaps.append(f'native session {index} 不是对象')
            continue
        if row.get('observer_preservation_error'):
            gaps.append(f"native session {index}: {row['observer_preservation_error']}")
        original = row.get('native') or row.get('unparsed_native')
        if not original:
            gaps.append(f'native session {index} 未保存声明的原文')
            continue
        for field in ('native', 'unparsed_native', 'session_tree_manifest'):
            relative = row.get(field)
            if not relative:
                continue
            try:
                path = (output / relative).resolve(strict=True)
                if not path.is_relative_to(output / 'native') or not path.is_file():
                    raise ValueError('原文不在持久 native 目录内')
                identity = _file_identity(path)
                expected = row.get('sha256' if field == 'native' else 'unparsed_sha256')
                if field != 'session_tree_manifest' and expected and identity['sha256'] != expected:
                    raise ValueError('原文 sha256 与 manifest 不一致')
            except (OSError, TypeError, ValueError) as exc:
                gaps.append(f'native session {index} {field}: {type(exc).__name__}: {exc}')
    return gaps


def finalize_archive(output, *, reclaim_workspace):
    """Write one decision-archive receipt and decide whether work may be reclaimed."""
    output = Path(output).resolve()
    if not output.is_dir():
        raise FileNotFoundError(output)
    objects = []
    roots = ('application', 'braid-state', 'native', 'native-config')
    files = ('run.json', 'config.json', 'input-hashes.json', 'implementation-hashes.json',
             'materials.json', 'application-hashes.json', 'delivery.json',
             'history-publication.json', 'telemetry-export-status.json',
             'telemetry-collector.log', 'telemetry-export.log', 'pi-timing.jsonl',
             'recovery-workspace.json')
    selected = [output/name for name in roots + files]
    selected.extend(sorted(output.glob('telemetry.sqlite*')))
    seen = set()
    for path in selected:
        if path in seen or not (path.exists() or path.is_symlink()):
            continue
        seen.add(path)
        if path.is_symlink():
            raise ValueError(f'归档根不能是符号链接: {path}')
        identity = _tree_identity(path) if path.is_dir() else _file_identity(path)
        objects.append({'path': path.relative_to(output).as_posix(), **identity})

    run = _read_json(output/'run.json', {})
    delivery = _read_json(output/'delivery.json', {})
    native = _read_json(output/'native/manifest.json', {})
    request = _read_json(output/'braid-state/request.json', {})
    result = _read_json(output/'braid-state/result.json', {})
    telemetry = _read_json(output/'telemetry-export-status.json', {'status': 'unknown'})
    gaps = []
    run_ids = {value for value in (request.get('run_id'), result.get('run_id'))
               if isinstance(value, str) and value}
    if len(run_ids) != 1:
        gaps.append('Braid request/result 缺少唯一 run_id')
    if native.get('diagnostic_status') != 'complete':
        gaps.append(f"native diagnostic_status={native.get('diagnostic_status', 'unknown')}")
    if telemetry.get('status') not in {'exited', 'not_configured'} or telemetry.get('exit_code', 0) != 0:
        gaps.append(f"telemetry export status={telemetry.get('status', 'unknown')}")
    preservation_gaps = _native_preservation_gaps(output, native)
    if run.get('diagnostic_error'):
        preservation_gaps.append(f"归档保存失败: {run['diagnostic_error']}")

    recovery = _read_json(output/'recovery-workspace.json')
    materials = _read_json(output/'materials.json', {})
    purpose = 'recovery' if recovery else 'provenance'
    dependencies = [{'purpose': purpose, 'kind': kind, 'location': location}
                    for kind, location in (('runtime', materials.get('runtime')),
                                           ('braid_binary', materials.get('braid')))
                    if isinstance(location, str) and location]
    required = {'braid-state', 'native', 'native-config', 'run.json'}
    if delivery.get('status') == 'delivered':
        required.add('application')
    present = {item['path'] for item in objects}
    missing = sorted(required - present)
    reasons = []
    if not reclaim_workspace:
        reasons.append('运行仍有恢复承诺或未满足既有成功条件')
    if missing:
        reasons.append('归档缺少关键对象: ' + ', '.join(missing))
    reasons.extend(preservation_gaps)
    reclaim = 'blocked' if reasons else 'eligible'
    receipt = {
        'schema_version': 1, 'record_type': 'factory26.archive', 'archive_level': 'decision',
        'run_id': output.name, 'braid_run_id': next(iter(run_ids)) if len(run_ids) == 1 else None,
        'created_at': time.time(), 'objects': objects, 'dependencies': dependencies,
        'execution_result': {'status': run.get('status', 'unknown'), 'phase': run.get('phase'),
                             'error': run.get('error')},
        'delivery_result': delivery,
        'evaluation_result': {'status': 'not_applicable', 'reason': 'generation archive'},
        'diagnostic_coverage': {'status': native.get('diagnostic_status', 'unknown'),
                                'telemetry': telemetry, 'gaps': gaps,
                                'preservation': {'status': 'partial' if preservation_gaps else 'complete',
                                                 'gaps': preservation_gaps}},
        'recovery_capability': {'status': 'declared' if recovery else 'none',
                                'workspace': recovery.get('path') if recovery else None},
        'reclaim_state': {'status': reclaim, 'target': 'work', 'reasons': reasons},
    }
    receipt['archive_id'] = hashlib.sha256(json.dumps(
        receipt, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()
    save(output/'archive.json', receipt)
    return receipt


def _pi_session_tree(native_home, work, parent_ids):
    """Select evidence for this parent, not whichever parent last used its home."""
    factory = native_home / '.factory'
    candidates = [factory / 'session-tree.json']
    candidates.extend(factory / 'session-trees' / f'{quote(parent, safe="")}.json'
                      for parent in sorted(parent_ids) if "/" not in parent and "\\" not in parent)
    found = False
    for candidate in candidates:
        if not candidate.exists():
            continue
        found = True
        source = _archive_path(candidate, work)
        tree = json.loads(source.read_text())
        if not isinstance(tree, dict) or not isinstance(tree.get('children'), list):
            raise ValueError(f'Pi session-tree manifest 格式无效: {source}')
        if str(tree.get('parent_native_session_id')) in parent_ids:
            return source, tree
    if found:
        raise ValueError('Pi 当前及历史 session-tree 均不匹配所归档父会话')
    return None


def archive_sessions(output, home, work, entries, telemetry_env=None):
    """归档原生会话及被动观察的父子关系，返回每份材料的归档记录。

    manifest 的 complete/partial/unknown 描述诊断覆盖，不是应用交付状态。
    身份无法核实时尽量保留 unparsed_native，并记录错误，不伪造会话关联。
    """
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
                    failed['unparsed_sha256'] = _file_identity(target)['sha256']
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
            try:
                root_ids = {str(value) for value in (session_id, row.get('native_session_id'))
                            if value is not None}
                selected = _pi_session_tree(native_home, work, root_ids)
                if selected:
                    source = selected[1].get('parent_session_file') or source
            except (OSError, ValueError, TypeError, json.JSONDecodeError):
                pass  # Preserve the native file; archive_pi_children records index errors separately.
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
        root_ids = {str(root_archived.get('native_id')), str(root.get('session_id')),
                    str(root.get('native_session_id')),
                    str(root.get('native_session_path')), str(root_archived.get('source_path'))}
        root_ids.discard('None')
        selected = _pi_session_tree(child_home, work, root_ids)
        if selected is None:
            root_archived['observer_diagnostic_status'] = 'unknown'
            return
        tree_source, tree = selected
        tree_target = native/f'{target_index:03}-{tree_source.name}'
        target_index += 1
        shutil.copy2(tree_source, tree_target)
        root_archived['session_tree_manifest'] = str(tree_target.relative_to(output))
        root_archived['observer_diagnostic_status'] = tree.get('diagnostic_status', 'unknown')
        parent_id = tree['parent_native_session_id']
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
                    if isinstance(exc, OSError):
                        root_archived['observer_preservation_error'] = f'{type(exc).__name__}: {exc}'
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
            error_row(row, str(exc))
    valid = [row for row in archived if row.get('native') and not row.get('archive_error')]
    incomplete_observation = any(row.get('observer_diagnostic_status') in ('partial', 'unknown')
                                 or row.get('association_status') in ('partial', 'unknown') for row in archived)
    diagnostic_status = ('unknown' if not valid else 'partial'
                         if len(valid) != len(archived) or incomplete_observation else 'complete')
    manifest = {'schema_version': 1, 'diagnostic_status': diagnostic_status, 'sessions': archived}
    (native/'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n')
    export_telemetry(output, work, manifest, env=telemetry_env)
    return archived
