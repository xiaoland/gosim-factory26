"""Factory's local Braid boundary: isolated repository, delivery and evidence."""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile


def initialize_repository(app):
    subprocess.run(['git', 'init', '-q', '-b', 'factory-source', str(app)], check=True)
    for key, value in [('user.name', 'Factory26'), ('user.email', 'factory26@localhost'),
                       ('commit.gpgsign', 'false'), ('core.hooksPath', '/dev/null')]:
        subprocess.run(['git', '-C', str(app), 'config', key, value], check=True)
    (app/'.git/info/exclude').write_text('.braid/\nnode_modules/\n__pycache__/\n')
    subprocess.run(['git', '-C', str(app), 'commit', '--allow-empty', '-qm',
                    '初始化本次生成的应用仓库'], check=True)


def load_delivery(state, app, work, request):
    result = json.loads((state/'result.json').read_text())
    if result.get('schema_version') != 1 or result.get('status') != 'completed':
        raise RuntimeError(f'Braid 尚未完成交付: {result.get("status")} / {result.get("reason")}')
    if any(result.get(key) != request[key] for key in ('run_id','delivery_ref')):
        raise RuntimeError('Braid 交付身份与启动请求不一致')
    if result.get('root_issue') != {'kind':'issue','id':'1'}:
        raise RuntimeError('Braid 交付没有对应本次根 Issue')
    repository = Path(result['repository']).resolve(strict=True)
    if repository != app.resolve() or not repository.is_relative_to(work.resolve()):
        raise RuntimeError('Braid 返回的交付仓库不属于本次运行')
    commit = result.get('delivery_commit', '')
    if not re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', commit):
        raise RuntimeError('Braid 没有返回不可变交付 commit')
    object_type = subprocess.check_output(['git', '-C', str(repository), 'cat-file', '-t', commit], text=True).strip()
    if object_type != 'commit':
        raise RuntimeError('交付 Git 对象不是 commit')
    delivery_ref = result.get('delivery_ref', '')
    if not delivery_ref.startswith('refs/heads/'):
        raise RuntimeError('交付分支没有完整本地 ref')
    head = subprocess.check_output(['git', '-C', str(repository), 'rev-parse', '--verify',
                                    '--end-of-options', delivery_ref], text=True).strip()
    if head != commit:
        raise RuntimeError('交付分支与返回 commit 不一致')
    for key in ('objects_database', 'sessions_manifest'):
        path = Path(result[key]).resolve(strict=True)
        if not path.is_relative_to(state.resolve()):
            raise RuntimeError(f'Braid {key} 不属于本次状态目录')
    return result


def export_delivery(app, commit, output):
    """Export precisely the accepted commit, independently of worktree contents."""
    output.mkdir()
    proc = subprocess.Popen(['git', '-C', str(app), 'archive', '--format=tar', commit], stdout=subprocess.PIPE)
    try:
        with tarfile.open(fileobj=proc.stdout, mode='r|') as archive:
            archive.extractall(output, filter='data')
    finally:
        proc.stdout.close()
        code = proc.wait()
    if code:
        raise RuntimeError('无法导出 Braid 交付 commit')


def archive_state(state, output):
    """Preserve the original state and return portable evidence references."""
    if state.resolve() != (output/'braid-state').resolve():
        shutil.copytree(state, output/'braid-state')
    manifest=state/'sessions.json'
    entries=json.loads(manifest.read_text()) if manifest.exists() else []
    for entry in entries:
        try:
            for owner, keys in [(entry, ('context_path','instructions_path'))] + [
                    (turn, ('input_path',)) for turn in entry.get('turns',[])]:
                for key in keys:
                    if not owner.get(key): continue
                    path=Path(owner[key]).resolve(strict=True)
                    relative=path.relative_to(state.resolve())
                    owner['source_'+key]=owner[key]
                    owner[key]=str(Path('braid-state')/relative)
        except (OSError,ValueError) as exc:
            entry['evidence_error']=str(exc)
    return entries


def export_telemetry(output, work, archived_manifest):
    """补采已归档的原生证据；遥测失败不改变归档或应用终态。"""
    state = output/'braid-state'
    if not state.is_dir() or not any(os.environ.get(key) for key in (
            'OTEL_EXPORTER_OTLP_ENDPOINT', 'OTEL_EXPORTER_OTLP_TRACES_ENDPOINT',
            'OTEL_EXPORTER_OTLP_LOGS_ENDPOINT', 'OTEL_EXPORTER_OTLP_METRICS_ENDPOINT')):
        return
    log_path = output/'telemetry-export.log'
    result = {'log': log_path.name}
    try:
        gaps = []
        identities = []
        for name in ('request.json', 'result.json'):
            path = state/name
            if path.exists():
                run_id = json.loads(path.read_text()).get('run_id')
                if isinstance(run_id, str) and run_id:
                    identities.append(run_id)
        if not identities:
            raise ValueError('Braid request/result 缺少 run_id，不能用外层实验身份替代')
        if len(set(identities)) != 1:
            gaps.append('Braid request/result 的 run_id 不一致')
        status = archived_manifest.get('diagnostic_status', 'unknown')
        if status != 'complete':
            gaps.append(f'Factory native diagnostic_status={status}')
        rows = archived_manifest['sessions']
        native_ids = {(row.get('provider'), str(row[key])): row['native_id']
                      for row in rows if row.get('native_id')
                      for key in ('native_id', 'session_id', 'source_path', 'native_session_path')
                      if row.get(key)}
        sessions = []
        for index, row in enumerate(rows):
            label = f'Factory native session[{index}]'
            for key in ('archive_error', 'evidence_error', 'observer_diagnostic_error'):
                if row.get(key):
                    gaps.append(f'{label} {key}: {row[key]}')
            for key in ('observer_diagnostic_status', 'association_status'):
                if row.get(key) and row[key] != 'complete':
                    gaps.append(f'{label} {key}={row[key]}')
            path = row.get('native') or row.get('unparsed_native')
            if not path:
                gaps.append(f'{label} 没有已归档原生文件')
                continue
            session = {key: row[key] for key in (
                'group_id', 'profile_id', 'effective_profile_digest', 'assignment_generation',
                'work_item_kind', 'work_item_id', 'native_role', 'evidence_source', 'sha256',
                'association_status', 'observer_diagnostic_status',
            ) if row.get(key) is not None}
            session.update(provider=row['provider'], native_session_id=row.get('native_id'), path=path)
            # Pi session_id 可以是原生路径，不能把它当作 Braid 数据库 session UUID。
            if row.get('session_id'):
                session['provider_session_id'] = row['session_id']
            if not row.get('native_id'):
                gaps.append(f'{label} 未核实 native_session_id；保留未解析原文')
            parent = row.get('parent_native_session_id') or row.get('native_parent')
            if parent:
                native_parent = native_ids.get((row['provider'], str(parent)))
                if native_parent:
                    session['parent_native_session_id'] = native_parent
                else:
                    session['source_parent_session_id'] = parent
                    gaps.append(f'{label} 未关联到已归档父会话: {parent}')
            sessions.append(session)
        manifest = output/'telemetry-native.json'
        manifest.write_text(json.dumps(dict(schema_version=1, run_id=identities[0],
                                            sessions=sessions, gaps=gaps), ensure_ascii=False, indent=2)+'\n')
        with log_path.open('a') as log:
            proc = subprocess.run([str(work/'bin/braid'), 'telemetry', 'export', '--state', str(state),
                                   '--native-manifest', str(manifest)], stdout=subprocess.PIPE,
                                  stderr=log, timeout=120, text=True)
            log.write(proc.stdout)
        result.update(status='exited', exit_code=proc.returncode)
        if proc.stdout.strip():
            result['report'] = json.loads(proc.stdout)
    except Exception as exc:
        message = f'Braid telemetry export: {type(exc).__name__}: {exc}\n'
        result.update(status='error', error=message.strip())
        try:
            with log_path.open('a') as log:
                if isinstance(exc, subprocess.TimeoutExpired) and exc.stdout:
                    log.write(exc.stdout.decode(errors='replace') if isinstance(exc.stdout, bytes) else exc.stdout)
                log.write(message)
        except OSError:
            print(message, file=sys.stderr, end='')
    try:
        (output/'telemetry-export-status.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    except OSError as exc:
        print(f'无法保存 Braid telemetry export 状态: {exc}', file=sys.stderr)
