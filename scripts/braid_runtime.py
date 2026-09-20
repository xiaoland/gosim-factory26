"""Factory's local Braid boundary: isolated repository, delivery and evidence."""
import json
from pathlib import Path
import re
import shutil
import subprocess
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
