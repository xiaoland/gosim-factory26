"""Public, offline Pi/Braid checkpoint, validation and preparation producer.

The controller supplies physical stop evidence. This producer preserves that
observation as checkpoint provenance; prepared content never grants launch.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import uuid

KIND = 'factory26.harness.checkpoint'
PREPARED = 'factory26.harness.prepared'
HOOK = 'pi-braid-logical-layout-v1'


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def inventory(root):
    rows = {}
    for directory, folders, files in os.walk(root, followlinks=False):
        for name in sorted(folders + files):
            path = Path(directory) / name
            member = path.relative_to(root).as_posix()
            if path.is_symlink():
                rows[member] = {'type': 'symlink', 'target': os.readlink(path)}
            elif path.is_file():
                rows[member] = {'type': 'file', 'sha256': digest(path),
                                'size': path.stat().st_size, 'mode': path.stat().st_mode & 0o777}
            elif path.is_dir():
                rows[member] = {'type': 'directory'}
            else:
                raise ValueError(f'不支持的检查点对象：{member}')
    return rows


def path_at(root, member):
    relative = PurePosixPath(member)
    if relative.is_absolute() or '..' in relative.parts or '\\' in member:
        raise ValueError(f'检查点 member 无效：{member}')
    path = root.joinpath(*relative.parts)
    if path.is_symlink():
        raise ValueError(f'检查点 member 不能是链接：{member}')
    for parent in path.parents:
        if parent == root:
            break
        if parent.is_symlink():
            raise ValueError(f'检查点目录不能经过链接：{member}')
    return path


def semantic_readback(payload, logical_root, materials=None):
    """Harness-owned readback: preserve Git, Braid DB/WAL and native history."""
    gaps, git, native = [], [], []
    mounts = [(str(logical_root), payload)]
    mounts += [(str(row['logical_root']), path_at(payload.parent, row['member'])) for row in materials or []]
    for logical, physical in mounts:
        for name, item in inventory(physical).items():
            if item['type'] == 'symlink':
                link = physical / name
                if not link.resolve().is_relative_to(payload.parent):
                    gaps.append({'kind': 'external_link', 'path': str(Path(logical) / name), 'target': item['target'],
                                 'impact': '链接字面值保留；当前 hook 不装配外部链接目标'})
    if gaps:
        # Git and SQLite can follow indirect files inside their own formats.
        # Keep the snapshot, but do not read through unresolved external links.
        return {'gaps': gaps, 'git': git, 'native': native}

    def resolve(value):
        path = Path(value)
        for logical, physical in sorted(mounts, key=lambda row: len(row[0]), reverse=True):
            if path.is_relative_to(logical):
                candidate = physical / path.relative_to(logical)
                if not candidate.resolve().is_relative_to(payload.parent):
                    gaps.append({'kind': 'external_link', 'path': value, 'impact': '不沿链接读取快照之外的现场'})
                    return None
                return candidate
        gaps.append({'kind': 'external_path', 'path': value, 'impact': '目标必须显式装配此外部材料'})
        return None

    state = payload / 'braid-state'
    request_file = payload / 'braid-request.json'
    database = state / 'braid.sqlite3'
    if not request_file.is_file() or not database.is_file():
        gaps.append({'kind': 'braid_state', 'impact': '缺少 Braid request 或 SQLite 原件'})
        return {'gaps': gaps, 'git': git, 'native': native}
    request = json.loads(request_file.read_text())
    # SQLite may write shared-memory state even for a read-only WAL connection.
    # Read a disposable copy so validation never changes published evidence.
    with tempfile.TemporaryDirectory(prefix='harness-readback-') as temporary:
        copied = Path(temporary) / database.name
        for suffix in ('', '-wal', '-shm'):
            original = Path(str(database) + suffix)
            if original.is_file() and not original.is_symlink():
                shutil.copy2(original, Path(str(copied) + suffix))
        db = sqlite3.connect(copied.as_uri() + '?mode=ro', uri=True)
        try:
            result = db.execute('PRAGMA integrity_check').fetchall()
            if result != [('ok',)]:
                gaps.append({'kind': 'braid_database', 'errors': result})
            worktrees = db.execute('SELECT path FROM worktrees').fetchall()
        except sqlite3.Error as error:
            gaps.append({'kind': 'braid_database', 'error': f'{type(error).__name__}: {error}'})
            worktrees = []
        finally:
            db.close()
    repositories = [payload / 'work/application', state / 'origin.git']
    repositories += [p for (value,) in worktrees if (p := resolve(value)) is not None]
    for repository in dict.fromkeys(repositories):
        marker = repository if repository.name.endswith('.git') else repository / '.git'
        if not marker.exists():
            gaps.append({'kind': 'git_history', 'path': str(repository.relative_to(payload.parent)),
                         'impact': '原始 .git 缺失；不重建 index、reflog 或历史'})
            continue
        git_directory = marker
        if marker.is_file():
            pointer = marker.read_text().strip()
            if not pointer.startswith('gitdir: '):
                gaps.append({'kind': 'gitdir', 'path': str(marker), 'impact': 'gitdir 文件无效'})
                continue
            location = Path(pointer[8:])
            if location.is_absolute():
                git_directory = resolve(str(location))
            else:
                git_directory = Path(os.path.normpath(marker.parent / location))
                if not git_directory.is_relative_to(payload.parent):
                    git_directory = None
            if git_directory is None or not git_directory.is_dir():
                gaps.append({'kind': 'gitdir', 'path': str(location), 'impact': 'gitdir 原件缺失'})
                continue
        alternates = git_directory / 'objects/info/alternates'
        if alternates.is_file() and alternates.read_text().strip():
            gaps.append({'kind': 'git_alternates', 'path': str(alternates),
                         'impact': '外置 Git object store 未装配，不读取外部历史'})
            continue
        command = ['git', '--git-dir', str(git_directory)]
        environment = {**os.environ, 'GIT_OPTIONAL_LOCKS': '0'}
        for name in ('GIT_DIR', 'GIT_WORK_TREE', 'GIT_OBJECT_DIRECTORY', 'GIT_ALTERNATE_OBJECT_DIRECTORIES'):
            environment.pop(name, None)
        head = subprocess.run(command + ['rev-parse', '--verify', 'HEAD'],
                              capture_output=True, text=True, env=environment)
        objects = subprocess.run(command + ['fsck', '--full'],
                                 capture_output=True, text=True, env=environment)
        member = os.path.relpath(repository, payload)
        git.append({'member': member, 'head': head.stdout.strip(),
                    'exit_code': head.returncode, 'error': head.stderr.strip(),
                    'objects_exit_code': objects.returncode, 'objects_error': objects.stderr.strip()})
        if head.returncode or objects.returncode:
            gaps.append({'kind': 'git_history', 'member': member,
                         'error': head.stderr.strip() + objects.stderr.strip()})
    for logical, physical in mounts:
        for member, row in inventory(physical).items():
            if row['type'] != 'symlink':
                continue
            destination = Path(row['target'])
            if not destination.is_absolute():
                destination = Path(logical) / Path(member).parent / destination
            destination = Path(os.path.normpath(destination))
            if resolve(str(destination)) is None:
                gaps.append({'kind': 'external_link', 'member': member, 'logical_root': logical,
                             'target': row['target'], 'impact': '没有显式材料绑定，不沿外链读取'})
    for profile, binding in request.get('bindings', {}).items():
        for name in ('executable', 'native_template'):
            value = binding.get(name)
            if value:
                target = resolve(value)
                if target is not None and not target.exists():
                    gaps.append({'kind': 'native_material', 'profile': profile, 'field': name, 'path': value})
        value = binding.get('native_home', {}).get('root')
        if value:
            home = resolve(value)
            histories = sorted(home.glob(profile + '-*/sessions/**/*.jsonl')) if home and home.exists() else []
            native.append({'profile': profile, 'history_members': [os.path.relpath(p, payload) for p in histories]})
            for history in histories:
                try:
                    with history.open() as lines:
                        for number, line in enumerate(lines, 1):
                            if line.strip() and not isinstance(json.loads(line), dict):
                                raise ValueError(f'第 {number} 行不是 native JSON 对象')
                except (OSError, ValueError) as error:
                    gaps.append({'kind': 'native_history', 'member': os.path.relpath(history, payload),
                                 'error': f'{type(error).__name__}: {error}'})
            if home is None or not home.is_dir():
                gaps.append({'kind': 'native_history', 'profile': profile, 'impact': 'native root 原件缺失'})
    return {'gaps': gaps, 'git': git, 'native': native}


def validate(root):
    root = Path(root).resolve(strict=True)
    manifest = json.loads((root / 'harness-manifest.json').read_text())
    if manifest.get('kind') not in {KIND, PREPARED} or manifest.get('schema_version') != 1:
        raise ValueError('不是当前 Harness checkpoint/prepared 合同')
    actual = inventory(root / 'content')
    if actual != manifest['files']:
        raise ValueError('检查点内容清单与读回不一致')
    identity = manifest['source_identity']
    if not all(identity.get(name) for name in ('attempt_id', 'execution_instance', 'backend_identity')):
        raise ValueError('检查点缺少来源执行身份')
    if manifest['kind'] == KIND:
        stop = manifest['stop_provenance']
        original = path_at(root, stop['member'])
        if digest(original) != stop['sha256']:
            raise ValueError('停止来源原件发生变化')
        observed = json.loads(original.read_text())
        if any(observed.get(name) != identity[name] for name in ('attempt_id', 'execution_instance', 'backend_identity')):
            raise ValueError('停止来源 instance 不一致')
    readback = semantic_readback(root / 'content/run', manifest['layout']['run_root'], manifest['materials'])
    expected_status = 'partial' if readback['gaps'] else 'complete'
    if manifest['status'] != expected_status:
        raise ValueError('检查点完整性声明与实际缺口不一致')
    if readback['gaps'] != manifest['readback']['gaps']:
        raise ValueError('检查点语义缺口与独立读回不一致')
    return {'kind': 'factory26.harness.validation', 'schema_version': 1,
            'manifest_sha256': digest(root / 'harness-manifest.json'),
            'status': manifest['status'], 'readback': readback,
            'capabilities': manifest['capabilities']}


def checkpoint(source, output, identity, stop, materials):
    source = source.resolve(strict=True)
    identity_value = json.loads(identity.read_text())
    stop_value = json.loads(stop.read_text())
    for field in ('attempt_id', 'execution_instance', 'backend_identity'):
        if not identity_value.get(field) or stop_value.get(field) != identity_value[field]:
            raise ValueError(f'停止原件与来源执行身份不一致：{field}')
    if stop_value.get('effect') != 'stopped' or not stop_value.get('observation'):
        raise ValueError('检查点必须有真实停止观察，受理不等于已停止')
    output = output.absolute()
    if output.exists() or output.is_relative_to(source):
        raise ValueError('检查点输出必须是来源以外的新目录')
    output.mkdir(parents=True)
    write(output / 'production.json', {'phase': 'staging', 'argv': sys.argv,
                                      'producer': HOOK, 'source': str(source)})
    (output / 'content').mkdir()
    shutil.copytree(source, output / 'content/run', symlinks=True)
    copied = []
    for number, material in enumerate(materials):
        original = material.resolve(strict=True)
        if output.is_relative_to(original):
            raise ValueError('检查点输出不能位于材料来源内部')
        member = f'content/materials/{number}'
        shutil.copytree(original, output / member, symlinks=True)
        copied.append({'logical_root': str(original), 'member': member.removeprefix('content/')})
    (output / 'provenance').mkdir()
    shutil.copy2(identity, output / 'provenance/source-identity.json')
    shutil.copy2(stop, output / 'provenance/stop-observation.json')
    readback = semantic_readback(output / 'content/run', source, copied)
    manifest = {'kind': KIND, 'schema_version': 1, 'checkpoint_id': 'hcp-' + uuid.uuid4().hex,
                'producer': {'name': 'pi-braid-checkpoint', 'hook': HOOK, 'sha256': digest(Path(__file__))},
                'created_at': datetime.now(timezone.utc).isoformat(),
                'source_identity': identity_value,
                'stop_provenance': {'sha256': digest(stop), 'member': 'provenance/stop-observation.json',
                                    'role': 'historical_acquisition_basis'},
                'layout': {'run_root': str(source), 'os': platform.system(), 'architecture': platform.machine()},
                'materials': copied, 'files': inventory(output / 'content'),
                'status': 'partial' if readback['gaps'] else 'complete', 'readback': readback,
                'capabilities': {'stopped_checkpoint': True, 'active_checkpoint': False,
                                 'same_logical_root_cross_daemon': True, 'native_path_migration': False,
                                 'cross_os': False, 'prepare_hook': HOOK}}
    write(output / 'harness-manifest.json', manifest)
    write(output / 'validation.json', validate(output))
    write(output / 'production.json', {'phase': 'published', 'argv': sys.argv, 'producer': HOOK})
    return manifest


def prepare(source, output, target):
    validation = validate(source)
    if validation['status'] != 'complete':
        raise ValueError('partial checkpoint 不能 prepare；保留缺口，不重建历史')
    manifest = json.loads((source / 'harness-manifest.json').read_text())
    if manifest['kind'] != KIND:
        raise ValueError('prepare 输入必须是 checkpoint')
    if target.get('run_root') != manifest['layout']['run_root'] or target.get('os') != manifest['layout']['os']:
        raise ValueError('当前 native hook 只支持同 OS、同 logical root；跨根迁移不受支持')
    if target.get('architecture') != manifest['layout']['architecture']:
        raise ValueError('当前冻结 binary 只支持同 architecture')
    if not target.get('runtime_identity'):
        raise ValueError('prepare 必须显式冻结目标 runtime_identity')
    output = output.absolute()
    source = source.resolve(strict=True)
    if output.exists() or output.is_relative_to(source):
        raise ValueError('prepared 输出必须为来源外部的新目录')
    output.mkdir(parents=True)
    write(output / 'production.json', {'phase': 'staging', 'argv': sys.argv, 'producer': HOOK})
    shutil.copytree(source / 'content', output / 'content', symlinks=True)
    prepared = {key: value for key, value in manifest.items() if key not in {'stop_provenance'}}
    prepared.update(kind=PREPARED, prepared_id='hprep-' + uuid.uuid4().hex,
                    source_checkpoint={'checkpoint_id': manifest['checkpoint_id'],
                                       'manifest_sha256': digest(source / 'harness-manifest.json')},
                    allowed_changes=[], target_layout=target,
                    preparation={'argv': sys.argv, 'network': False, 'model_credentials': False, 'hook': HOOK})
    write(output / 'harness-manifest.json', prepared)
    write(output / 'validation.json', validate(output))
    write(output / 'production.json', {'phase': 'published', 'argv': sys.argv, 'producer': HOOK})
    return prepared


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['checkpoint', 'validate', 'prepare'])
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--source-identity', type=Path)
    parser.add_argument('--stop-evidence', type=Path)
    parser.add_argument('--materials-root', action='append', default=[], type=Path)
    parser.add_argument('--target-layout', type=Path)
    args = parser.parse_args()
    if args.command == 'validate':
        result = validate(args.source)
    elif args.command == 'checkpoint':
        if not args.output or not args.source_identity or not args.stop_evidence:
            parser.error('checkpoint 需要 output/source-identity/stop-evidence')
        result = checkpoint(args.source, args.output, args.source_identity, args.stop_evidence, args.materials_root)
    else:
        if not args.output or not args.target_layout:
            parser.error('prepare 需要 output/target-layout')
        result = prepare(args.source, args.output, json.loads(args.target_layout.read_text()))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        if '--output' in sys.argv:
            output = Path(sys.argv[sys.argv.index('--output') + 1])
            if output.is_dir() and (output / 'production.json').is_file():
                write(output / 'production-failure.json', {'type': type(error).__name__,
                                                         'message': str(error), 'argv': sys.argv})
        raise
