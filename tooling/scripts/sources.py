"""交接独立 Git 源码仓库，包括本地提交、未提交修改与未跟踪文件。"""
import argparse
import json
from pathlib import Path
import subprocess
import tarfile


def git(source, *args):
    return subprocess.check_output(['git', '-C', str(source), *args])


def export(source, output):
    source = source.resolve(strict=True)
    if Path(git(source, 'rev-parse', '--show-toplevel').decode().strip()).resolve() != source:
        raise ValueError('只接受独立仓库根目录；本仓库中的源码目录请通过父仓库交接')
    output = output.resolve()
    if output.is_relative_to(source):
        raise ValueError('交接目录必须位于源码仓库之外')
    output.mkdir(parents=True, exist_ok=False)
    revision = git(source, 'rev-parse', 'HEAD').decode().strip()
    branch = git(source, 'branch', '--show-current').decode().strip()
    # The bundle keeps unpublished commits; the patch flattens staged/unstaged edits.
    subprocess.run(['git', '-C', str(source), 'bundle', 'create', str(output/'repository.bundle'),
                    '--all', 'HEAD'], check=True)
    shallow = Path(git(source, 'rev-parse', '--git-path', 'shallow').decode().strip())
    if not shallow.is_absolute():
        shallow = source/shallow
    if shallow.is_file():
        (output/'shallow').write_bytes(shallow.read_bytes())
    (output/'worktree.patch').write_bytes(git(source, 'diff', '--binary', 'HEAD'))
    untracked = git(source, 'ls-files', '--others', '--exclude-standard', '-z').decode().split('\0')
    with tarfile.open(output/'untracked.tar.gz', 'w:gz') as archive:
        for name in untracked:
            if name:
                archive.add(source/name, arcname=name, recursive=False)
    remotes = git(source, 'remote').decode().splitlines()
    origin = git(source, 'remote', 'get-url', 'origin').decode().strip() if 'origin' in remotes else None
    (output/'source.json').write_text(json.dumps({'source': str(source), 'revision': revision,
        'branch': branch, 'origin': origin,
        'status': git(source, 'status', '--short').decode()}, ensure_ascii=False, indent=2)+'\n')
    return output


def restore(archive, destination):
    archive = archive.resolve(strict=True)
    destination = destination.resolve()
    if destination.exists():
        raise FileExistsError(f'恢复只接受新目录: {destination}')
    record = json.loads((archive/'source.json').read_text())
    destination.mkdir(parents=True)
    git(destination, 'init')
    # Git bundle stores objects but omits the boundary of a shallow checkout.
    if (archive/'shallow').exists():
        (destination/'.git/shallow').write_bytes((archive/'shallow').read_bytes())
    refs = git(destination, 'bundle', 'unbundle', str(archive/'repository.bundle')).decode().splitlines()
    for row in refs:
        revision, ref = row.split(' ', 1)
        if ref != 'HEAD':
            git(destination, 'update-ref', ref, revision)
    if record['branch']:
        git(destination, 'checkout', '-B', record['branch'], record['revision'])
    else:
        git(destination, 'checkout', '--detach', record['revision'])
    patch = archive/'worktree.patch'
    if patch.stat().st_size:
        git(destination, 'apply', '--binary', str(patch))
    with tarfile.open(archive/'untracked.tar.gz') as bundle:
        bundle.extractall(destination, filter='data')
    if record['origin']:
        git(destination, 'remote', 'add', 'origin', record['origin'])
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['export', 'restore'])
    parser.add_argument('source', type=Path, help='源码仓库，或先前 export 的交接目录')
    parser.add_argument('destination', type=Path, help='必须是尚不存在的新目录')
    args = parser.parse_args()
    print(export(args.source, args.destination) if args.command == 'export'
          else restore(args.source, args.destination))


if __name__ == '__main__':
    main()
