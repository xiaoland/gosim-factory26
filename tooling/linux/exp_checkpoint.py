"""Public, offline Pi/Braid checkpoint, validation and preparation producer.

The controller supplies physical stop evidence. This producer preserves that
observation as checkpoint provenance; prepared content never grants launch.
"""
import argparse
import ast
import re
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
LEGACY_HOOK = 'pi-braid-logical-layout-v2'
HOOK = 'pi-braid-separated-layout-v3'
PRODUCER_SOURCE_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()



def copy_file(source,destination):
    """Independent APFS snapshots when available; never share writable hardlinks."""
    if sys.platform == 'darwin':
        import ctypes, errno
        library = ctypes.CDLL(None,use_errno=True)
        if library.clonefile(os.fsencode(source),os.fsencode(destination),0) == 0: return str(destination)
        code = ctypes.get_errno()
        if code not in {errno.EXDEV,errno.ENOTSUP,errno.EINVAL}: raise OSError(code,os.strerror(code),str(source))
    return shutil.copy2(source,destination)

def inventory(root, *, hash_files=True):
    rows = {}
    for directory, folders, files in os.walk(root, followlinks=False):
        for name in sorted(folders + files):
            path = Path(directory) / name
            member = path.relative_to(root).as_posix()
            if path.is_symlink():
                rows[member] = {'type': 'symlink', 'target': os.readlink(path)}
            elif path.is_file():
                rows[member] = {'type': 'file', **({'sha256': digest(path)} if hash_files else {}),
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


def semantic_readback(payload, logical_root, materials=None, definition_mounts=None):
    """Harness-owned readback: preserve Git, Braid DB/WAL and native history."""
    gaps, git, native = [], [], []
    mounts = [(str(logical_root), payload)]
    mounts += [(str(row['logical_root']), path_at(payload.parent, row['member'])) for row in materials or []]
    mounts += definition_mounts or []
    allowed = [payload.parent.resolve(), *(physical.resolve() for _, physical in definition_mounts or [])]
    def resolve(value, visited=None):
        path = Path(os.path.normpath(value))
        visited = set() if visited is None else visited
        if str(path) in visited:
            gaps.append({'kind': 'external_link', 'path': value, 'impact': '声明路径包含循环链接'})
            return None
        for logical, physical in sorted(mounts, key=lambda row: len(row[0]), reverse=True):
            if path.is_relative_to(logical):
                relative = path.relative_to(logical)
                candidate = physical
                for index, part in enumerate(relative.parts):
                    candidate = candidate / part
                    if candidate.is_symlink():
                        target = Path(os.readlink(candidate))
                        if not target.is_absolute():
                            target = Path(logical).joinpath(*relative.parts[:index]) / target
                        target = target.joinpath(*relative.parts[index+1:])
                        return resolve(str(target), visited | {str(path)})
                if not any(candidate.resolve().is_relative_to(root) or candidate.resolve() == root for root in allowed):
                    gaps.append({'kind': 'external_link', 'path': value, 'impact': '不沿链接读取声明状态和定义之外的现场'})
                    return None
                return candidate
        gaps.append({'kind': 'external_path', 'path': value, 'impact': '目标必须显式装配此外部材料'})
        return None

    scan_mounts = []
    for logical, physical in sorted(mounts, key=lambda row: len(row[1].parts)):
        if not any(physical.is_relative_to(parent) for _, parent in scan_mounts):
            scan_mounts.append((logical, physical))
    # Resolve literals through declared logical roots, never through the live source tree.
    for logical, physical in scan_mounts:
        for name, item in inventory(physical, hash_files=False).items() if physical.is_dir() else []:
            if item['type'] == 'symlink' and resolve(str(Path(logical) / name)) is None:
                gaps.append({'kind': 'external_link', 'path': str(Path(logical) / name), 'target': item['target'],
                             'impact': '链接字面值保留；目标缺少声明绑定'})
    if gaps:
        return {'gaps': gaps, 'git': git, 'native': native}

    state = payload / 'braid-state'
    request_file = payload / 'braid-request.json'
    database = state / 'braid.sqlite3'
    if not request_file.is_file() or not database.is_file():
        gaps.append({'kind': 'braid_state', 'impact': '缺少 Braid request 或 SQLite 原件'})
        return {'gaps': gaps, 'git': git, 'native': native}
    request = json.loads(request_file.read_text())
    # SQLite may write shared-memory state even for a read-only WAL connection.
    # Read a disposable copy so validation never changes published evidence.
    with tempfile.TemporaryDirectory(prefix='harness-readback-', dir=payload.parent.parent.parent) as temporary:
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
    reconstruction = payload/'recovery-git.json'
    if reconstruction.is_file():
        restored = json.loads(reconstruction.read_text())
        if restored.get('repaired'):
            gaps.append({'kind':'lost-original-git-history','impact':restored.get('limitation','Original clone history was reconstructed'),
                         'members':[row.get('path') for row in restored['repaired']]})
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
    for logical, physical in scan_mounts:
        for member, row in inventory(physical, hash_files=False).items() if physical.is_dir() else []:
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


def source_identity_fields(identity, *, legacy_read=False):
    if not isinstance(identity, dict):
        raise ValueError('检查点来源执行身份必须为对象')
    if identity.get('kind') == 'factory26.exp.legacy-source':
        if identity.get('schema_version') != 1 or 'attempt_id' in identity:
            raise ValueError('旧来源必须保持 schema 1 source_id，不得补造 attempt_id')
        fields = ('source_id', 'execution_instance', 'backend_identity')
    elif identity.get('kind') is None:
        if legacy_read and identity.get('source_id') and not identity.get('attempt_id'):
            fields = ('source_id', 'execution_instance', 'backend_identity')
        else:
            fields = ('attempt_id', 'execution_instance', 'backend_identity')
    else:
        raise ValueError('不支持的检查点来源执行身份合同')
    if not all(identity.get(name) for name in fields):
        raise ValueError('检查点缺少来源执行身份')
    return fields


def validate_stop_identity(identity, observed, *, legacy_read=False):
    fields = source_identity_fields(identity, legacy_read=legacy_read)
    if any(observed.get(name) != identity[name] for name in fields):
        raise ValueError('停止来源 instance 不一致')
    if ('source_identity' in observed or identity.get('kind') == 'factory26.exp.legacy-source') and observed.get('source_identity') != identity:
        raise ValueError('停止来源嵌套执行身份不一致')
    if observed.get('effect') != 'stopped' or not observed.get('observation'):
        raise ValueError('检查点必须有真实停止观察，受理不等于已停止')


def validator_identity():
    return {'hook': HOOK, 'source_sha256': PRODUCER_SOURCE_SHA256,
            'python': platform.python_version(), 'sqlite': sqlite3.sqlite_version,
            'git': subprocess.check_output(['git', '--version'], text=True).strip()}


def capabilities():
    return {'schema_version': 3, 'stopped_checkpoint': True, 'active_checkpoint': False,
            'same_logical_root_cross_daemon': True, 'native_path_migration': False,
            'cross_os': False, 'cross_architecture': False, 'prepare_hook': HOOK,
            'repair_hooks': ['materials-refresh', 'provider-transport', 'internal-alias',
                             'transient-pulse-link', 'frozen-nodegyp-tool', 'compatible-runtime'],
            'coverage': ['content', 'sqlite-structure', 'git-objects-and-refs', 'native-json-structure',
                         'declared-logical-paths'], 'execution_compatibility': 'exact-frozen-runtime'}


def _acquisition(source, identity):
    if source is None:
        return {'status': 'unknown', 'limitation': '历史 stopped 原件不能证明捕获窗口持续关闭全部 writer'}
    value = json.loads(Path(source).read_text()) if isinstance(source, (str, Path)) else source
    if value.get('kind') != 'factory26.exp.writer-closure' or value.get('source_identity') != identity:
        raise ValueError('checkpoint acquisition 必须是同源的执行域 writer-closure 合同')
    if value.get('status') != 'closed' or not value.get('closure_id') or not value.get('writers') or not value.get('capture_token'):
        raise ValueError('writer-closure 缺少连续捕获保护或 writer 覆盖')
    return {'status': 'writer-closed', 'closure': value,
            'limitation': 'producer消费执行域覆盖；实际writer关闭由执行域负责'}



def _repair_link(root, member):
    relative = PurePosixPath(member)
    if relative.is_absolute() or '..' in relative.parts or not relative.parts or '\\' in member:
        raise ValueError('修复member必须为受限相对路径')
    path = root.joinpath(*relative.parts)
    for parent in path.parents:
        if parent == root: break
        if parent.is_symlink(): raise ValueError('修复不能经过链接目录')
    return path


def _refresh_native(run, logical_root, material, logical_material_root=None):
    request_path = run/'braid-request.json'
    request = json.loads(request_path.read_text())
    condition = next((ast.literal_eval(node.value) for node in ast.parse((material/'run.py').read_text()).body
                      if isinstance(node, ast.Assign) and any(isinstance(name, ast.Name) and name.id == 'RUN_CONDITIONS' for name in node.targets)), '')
    source_agents = material/'agents'
    for profile in request['profiles']:
        source = source_agents/profile['id']
        if not source.is_dir(): raise ValueError('材料刷新缺少已有profile，不改变成员身份')
        profile['user_instructions'] = (source/'instructions.md').read_text().rstrip() + '\n\n' + condition + '\n'
        binding = request['bindings'][profile['id']]
        logical_template = Path(binding['native_template'])
        if not logical_template.is_relative_to(logical_root): raise ValueError('native template不属于checkpoint')
        template = path_at(run, logical_template.relative_to(logical_root).as_posix())
        homes = list((run/'work/native-homes').glob(profile['id']+'-*'))
        for destination in [template, *homes]:
            for role in (source/'agents').glob('*.md'):
                target = destination/'agents'/role.name
                if not target.is_file(): raise ValueError('native role不存在，不静默增加角色')
                old = target.read_text(); fresh = role.read_text()
                old_parts, fresh_parts = old.split('---',2), fresh.split('---',2)
                if len(old_parts) != 3 or len(fresh_parts) != 3: raise ValueError('native role缺少frontmatter')
                # Connection/tool paths belong to the frozen launcher recipe.
                target.write_text('---'+old_parts[1]+'---'+fresh_parts[2])
    skills = run/'work/skills'
    if skills.exists(): shutil.rmtree(skills)
    if logical_material_root is None:
        shutil.copytree(material/'skills',skills,symlinks=True)
    else:
        skills.mkdir()
        for source in (material/'skills').iterdir():
            (skills/source.name).symlink_to(Path(logical_material_root)/'skills'/source.name, target_is_directory=True)
    write(request_path,request)
    state_request = run/'braid-state/request.json'
    if state_request.is_file():
        retained = json.loads(state_request.read_text())
        retained['profiles'] = request['profiles']
        write(state_request,retained)

def apply_repairs(output, manifest, repair, *, state_root=None):
    """Bounded material changes; original Git, native history and application stay intact."""
    if set(repair) - {'materials', 'provider_bindings', 'aliases', 'transient_links', 'nodegyp_tools', 'runtime'}:
        raise ValueError('未支持的恢复修复类别')
    content, run = output/'content', Path(state_root) if state_root is not None else output/'content/run'
    effects = []
    for row in repair.get('runtime', []):
        target = path_at(content,row['member'])
        if not row['member'].startswith('materials/') or target.name != 'runtime' or not target.is_dir():
            raise ValueError('runtime替换只支持明确材料root的runtime成员')
        replacement = Path(row['source']).resolve(strict=True)
        protected = ('bin/braid','native-managed.mjs','node_modules/@earendil-works/pi-coding-agent/package.json')
        for member in protected:
            if not (target/member).is_file() or not (replacement/member).is_file() or digest(target/member) != digest(replacement/member):
                raise ValueError('首版runtime兼容要求相同Braid/native hook/Pi版本；不迁移会话协议')
        if row.get('runtime_identity') != manifest['target_layout']['runtime_identity']:
            raise ValueError('runtime替换需要与冻结目标identity一致')
        shutil.rmtree(target); shutil.copytree(replacement,target,symlinks=True,copy_function=copy_file)
        effects.append({'hook':'compatible-runtime','member':row['member'],
                        'preserved_contract':list(protected),'runtime_identity':row['runtime_identity']})
    for row in repair.get('materials', []):
        target = path_at(content, row['member'])
        if not row['member'].startswith('materials/') or not target.is_dir():
            raise ValueError('materials-refresh 只允许明确的包材料root')
        material = Path(row['source']).resolve(strict=True)
        receipt = json.loads((material.parent/'material.json').read_text())
        if receipt.get('kind') != 'factory26.harness.material' or receipt.get('schema_version') != 2:
            raise ValueError('材料刷新需要新版公开material生产合同')
        actual = inventory(material)
        normalized = {name:({'link':row['target']} if row['type']=='symlink' else
                             {'sha256':row['sha256'],'mode':row['mode']})
                      for name,row in actual.items() if row['type']!='directory' and '__pycache__' not in PurePosixPath(name).parts}
        if normalized != receipt['contents']:
            raise ValueError('刷新材料内容与已发布producer receipt不一致')
        for section in ('agents', 'skills', 'extensions', 'tools', 'support'):
            origin = material/section
            if origin.is_dir():
                if (target/section).exists(): shutil.rmtree(target/section)
                shutil.copytree(origin, target/section, symlinks=True)
        for name in ('run.py', 'exp_checkpoint.py'):
            if (material/name).is_file(): shutil.copy2(material/name, target/name)
        _refresh_native(run, manifest['layout']['run_root'], material)
        effects.append({'hook': 'materials-refresh', 'member':row['member'], 'material_id':receipt['material_id'],
                        'preserved':['runtime','application','Git','native sessions'],
                        'scope':'owned instructions/skills/role bodies; retained transport and launcher bindings remain fixed'})
    routes = repair.get('provider_bindings')
    if routes:
        for row in routes.values():
            if set(row) != {'base_url', 'credential_env', 'provider'} or not row['credential_env'].isidentifier():
                raise ValueError('provider binding 必须显式非secret transport/provider/credential_env')
            from urllib.parse import urlsplit
            url = urlsplit(row['base_url'])
            if url.scheme not in {'http','https'} or not url.hostname or url.username or url.password or url.query:
                raise ValueError('provider URL 不能包含凭据')
        for path in [*(run/'work/capabilities').glob('*/native-template/models.json'),
                     *(run/'work/native-homes').glob('*/models.json')]:
            value = json.loads(path.read_text())
            for name, route in routes.items():
                if name in value['providers']:
                    value['providers'][name].update(baseUrl=route['base_url'],apiKey='$'+route['credential_env'])
            write(path, value)
            auth = path.with_name('auth.json')
            if auth.is_file():
                original = json.loads(auth.read_text())
                write(auth, {name:key for name,key in original.items() if name not in routes})
        effects.append({'hook':'provider-transport','bindings':routes,'preserved':['model IDs','session history']})
    for row in repair.get('aliases', []):
        member = row['member']
        relative = PurePosixPath(member)
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('alias member 无效')
        alias = _repair_link(content, member)
        if alias.name not in {'runtime','support','extensions','tools','agents','skills'} or not alias.is_symlink() or os.readlink(alias) != row['original_target']:
            raise ValueError('只允许匹配原literal的材料别名修复')
        target = path_at(content,row['target_member'])
        if not target.is_dir(): raise ValueError('alias目标必须是冻结内部材料')
        alias.unlink(); alias.symlink_to(os.path.relpath(target,alias.parent),target_is_directory=True)
        effects.append({'hook':'internal-alias','member':member,'original':row['original_target']})
    for row in repair.get('transient_links', []):
        link = _repair_link(run, row['member'])
        if not link.is_symlink() or os.readlink(link) != row['original_target'] or 'pulse' not in link.name or not row['original_target'].startswith('/tmp/'):
            raise ValueError('只支持明确原literal的已停pulse临时链接清理')
        if not row.get('retired_evidence'):
            raise ValueError('pulse清理需要保留退役依据')
        link.unlink(); effects.append({'hook':'transient-pulse-link',**row})
    for row in repair.get('nodegyp_tools', []):
        link = _repair_link(run, row['member'])
        if not str(link).endswith('/node_gyp_bins/python3') or not link.is_symlink() or os.readlink(link) != row['original_target']:
            raise ValueError('只支持精确 node-gyp python3链接物化')
        tool = Path(row['source']).resolve(strict=True)
        if not row.get('runtime_identity') or row['runtime_identity'] != manifest['target_layout']['runtime_identity']:
            raise ValueError('node-gyp工具必须来自明确目标runtime')
        link.unlink(); shutil.copy2(tool, link)
        effects.append({'hook':'frozen-nodegyp-tool','member':row['member'], 'original_target':row['original_target'],
                        'sha256':digest(tool),'runtime_identity':row['runtime_identity']})
    return effects

def definition_assets(rows, state_root):
    """Validate declared dependency relations; do not infer exclusions from an old tree."""
    from lab.exp.core import identifier, member
    names, assets = set(), []
    state_root = Path(state_root)
    for row in rows:
        name = identifier(row['name'])
        if name in names:
            raise ValueError('definition asset name重复：' + name)
        names.add(name)
        logical = Path(row['logical_root'])
        if not logical.is_absolute() or logical == Path('/') or '..' in logical.parts:
            raise ValueError('definition logical_root必须为有界绝对路径')
        if logical.is_relative_to(state_root) or state_root.is_relative_to(logical):
            raise ValueError('definition与运行state混装；不能猜测排除旧目录')
        reference = row['artifact']
        if set(reference) != {'artifact_id', 'manifest_sha256'}:
            raise ValueError('definition asset需要明确artifact reference')
        identifier(reference['artifact_id'])
        asset = {'name': name, 'logical_root': str(logical), 'artifact': reference, 'member': member(row.get('member', '.'))}
        if row.get('identity') is not None:
            asset['identity'] = row['identity']
        for previous in assets:
            parent, child = (previous, asset) if logical.is_relative_to(previous['logical_root']) else (asset, previous)
            if Path(child['logical_root']).is_relative_to(parent['logical_root']):
                relative = Path(child['logical_root']).relative_to(parent['logical_root'])
                expected = (Path(parent['member']) / relative).as_posix()
                if child['artifact'] != parent['artifact'] or child['member'] != expected:
                    raise ValueError('重叠definition必须引用同一artifact及一致member关系')
        assets.append(asset)
    if not assets:
        raise ValueError('separated checkpoint需要非空definition资产关系')
    return assets


def definition_mount_roots(rows, state_root):
    """Fold matching semantic sub-assets into one physical definition placement."""
    assets = sorted(definition_assets(rows, state_root), key=lambda row: len(Path(row['logical_root']).parts))
    result = []
    for row in assets:
        if not any(Path(row['logical_root']).is_relative_to(parent['logical_root']) for parent in result):
            result.append(row)
    return result


def resolve_definition_assets(root, manifest, artifact_store=None, verified=None):
    """Verify each immutable payload once per resolution, then retain semantic members."""
    from lab.exp import artifacts
    from lab.exp.core import canonical, member
    bindings_path = root / 'provenance/asset-bindings.json'
    saved = json.loads(bindings_path.read_text()) if bindings_path.exists() else {}
    consumer = manifest.get('prepared_id', manifest['checkpoint_id'])
    mounts, bindings = [], {}
    verified = {} if verified is None else verified
    for row in definition_assets(manifest['definition_assets'], manifest['layout']['run_root']):
        location = saved.get(row['name'], {})
        if not artifact_store and not location.get('store'):
            raise ValueError('definition缺少已解析artifact store：' + row['name'])
        store = Path(artifact_store or location['store']).resolve(strict=True)
        request_id = 'definition-' + canonical([consumer, row['name'], row['artifact']])[:40]
        if (location.get('reference') == row['artifact'] and location.get('retention')
                and str(store) == location.get('store') and location.get('consumer')):
            hold = location['retention']
            retained_consumer = location['consumer']
        else:
            hold = artifacts.retain(store, row['artifact'], consumer, 'harness-definition/' + row['name'], request_id)
            retained_consumer = consumer
        relative = member(row['member'])
        full_key = (str(store), canonical(row['artifact']))
        key = (*full_key, relative)
        if key not in verified:
            if full_key in verified:
                payload = verified[full_key]
                path = payload if relative == '.' else payload / relative
                current = payload
                for part in Path(relative).parts:
                    if part != '.':
                        current = current / part
                        if current.is_symlink():
                            raise ValueError('definition member不能经过未绑定alias：' + relative)
                if not path.exists() or not path.resolve().is_relative_to(payload.resolve()):
                    raise ValueError('definition member不存在或逃离artifact：' + relative)
                verified[key] = path
            else:
                verified[key] = artifacts.resolve(store, row['artifact'], path=relative,
                    consumer=retained_consumer, retention=hold)
        path = verified[key]
        mounts.append((row['logical_root'], path))
        bindings[row['name']] = {'store': str(store), 'root': str(path), 'reference': row['artifact'],
                                 'member': row['member'], 'consumer': retained_consumer, 'retention': hold}
    return mounts, bindings


def validation_receipt(root, manifest, readback):
    """Record one completed producer readback; public validate obtains a new one."""
    consistency = manifest.get('acquisition', {}).get('status', 'unknown')
    return {'kind': 'factory26.harness.validation', 'schema_version': 2, 'validator':validator_identity(),
            'coverage': {'content': 'verified', 'structure': 'partial' if readback['gaps'] else 'complete',
                         'acquisition': consistency, 'runtime_execution': 'not-observed'},
            'manifest_sha256': digest(Path(root) / 'harness-manifest.json'),
            'status': manifest['status'] if manifest['schema_version'] >= 2 else 'partial', 'readback': readback,
            'capabilities': manifest['capabilities']}


def referenced_state(manifest, state_readback=None):
    """Resolve the retained state member; metadata never substitutes active state."""
    from lab.exp import artifacts
    if manifest.get('kind') == PREPARED and manifest.get('state_binding'):
        from lab.exp import state
        binding = manifest['state_binding']
        holder = state_readback or state.query(binding)['holder']
        if holder['generation'] != binding['generation'] or holder['phase'] not in ('repaired', 'writable'):
            raise ValueError('prepared domain state不再属于该repaired generation')
        locator = holder['locator']
        if locator.get('kind') == 'local':
            if Path(locator['path']).resolve(strict=True) != Path(manifest['state_root']).resolve(strict=True):
                raise ValueError('domain state resolver不是实际state路径')
        elif not state_readback or binding['authority']['kind'] != 'docker':
            raise ValueError('Docker mutable state validation必须在持capture的实际domain中执行')
        return Path(manifest['state_root']).resolve(strict=True)
    binding = manifest['state_snapshot']
    return artifacts.resolve(binding['store'], binding['reference'], binding['member'],
                             consumer=manifest['checkpoint_id'], retention=binding['retention'])


def validate(root, artifact_store=None, *, _verified_assets=None, _state_readback=None, _in_domain=False):
    root = Path(root).resolve(strict=True)
    manifest = json.loads((root / 'harness-manifest.json').read_text())
    if not _in_domain and (root / 'domain-resolver.json').exists():
        from lab.exp.backends import validate_in_domain
        return validate_in_domain(root)
    if manifest.get('kind') not in {KIND, PREPARED} or manifest.get('schema_version') not in {1, 2, 3, 4}:
        raise ValueError('不是当前 Harness checkpoint/prepared 合同')
    state_root = referenced_state(manifest, _state_readback) if manifest['schema_version'] == 4 else root / 'content/run'
    actual = {'run/' + name: value for name, value in inventory(state_root).items()} if manifest['schema_version'] == 4 else inventory(root / 'content')
    if actual != manifest['files']:
        raise ValueError('检查点内容清单与读回不一致')
    identity = manifest['source_identity']
    if manifest.get('state_provenance'):
        proof = manifest['state_provenance']
        original = path_at(root, proof['member'])
        if digest(original) != proof['sha256']:
            raise ValueError('state export来源原件发生变化')
        exported = json.loads(original.read_text())['state_binding']
        if any(exported['source_identity'].get(key) != identity[key] for key in source_identity_fields(identity)) or not Path(manifest['layout']['run_root']).is_relative_to(exported['logical_root']):
            raise ValueError('state export来源执行/逻辑namespace不同')
    source_identity_fields(identity, legacy_read=manifest['schema_version'] == 1)
    if manifest['kind'] == KIND:
        stop = manifest['stop_provenance']
        original = path_at(root, stop['member'])
        if digest(original) != stop['sha256']:
            raise ValueError('停止来源原件发生变化')
        observed = json.loads(original.read_text())
        validate_stop_identity(identity, observed, legacy_read=manifest['schema_version'] == 1)
    if manifest['schema_version'] >= 2 and manifest.get('validator',{}).get('hook') != (HOOK if manifest['schema_version'] >= 3 else LEGACY_HOOK):
        raise ValueError('Harness validator hook不支持此证明覆盖')
    if manifest['schema_version'] >= 3:
        mounts, _ = resolve_definition_assets(root, manifest, artifact_store, _verified_assets)
        readback = semantic_readback(state_root, manifest['layout']['run_root'], definition_mounts=mounts)
    else:
        readback = semantic_readback(root / 'content/run', manifest['layout']['run_root'], manifest['materials'])
    consistency = manifest.get('acquisition', {}).get('status', 'unknown')
    expected_status = 'partial' if readback['gaps'] or (manifest['schema_version'] >= 2 and consistency != 'writer-closed') else 'complete'
    if manifest['schema_version'] >= 2 and manifest['status'] != expected_status:
        raise ValueError('检查点完整性声明与实际缺口不一致')
    if manifest['schema_version'] >= 2 and readback['gaps'] != manifest['readback']['gaps']:
        raise ValueError('检查点语义缺口与独立读回不一致')
    return validation_receipt(root, manifest, readback)


def checkpoint(source, output, identity, stop, materials=(), acquisition=None, definition_bindings=None, state_binding=None, snapshot=None):
    source = Path(source).resolve(strict=True)
    layout_path = source / 'harness-layout.json'
    if not layout_path.is_file() or materials:
        raise ValueError('新checkpoint需要显式separated harness-layout；旧v2来源保留原冻结producer，不猜排除材料')
    layout = json.loads(layout_path.read_text())
    if layout.get('kind') != 'factory26.harness.layout' or layout.get('schema_version') != 1:
        raise ValueError('harness-layout不绑定当前state root')
    logical_root = Path(layout['state_root'])
    export = json.loads(Path(state_binding).read_text()) if state_binding else None
    export_binding = export.get('state_binding') if export else None
    if logical_root != source and not export_binding and not snapshot:
        raise ValueError('导出state需要显式state-binding真实export回执；不猜原logical路径')
    source_layout = {'run_root': str(logical_root), 'os': platform.system(), 'architecture': platform.machine(), 'definition_layout': layout.get('definition_layout')}
    if export_binding:
        from lab.exp import artifacts
        try:
            relative = logical_root.relative_to(export_binding['logical_root'])
        except ValueError:
            raise ValueError('state logical root不在该export namespace内')
        installed = Path(export_binding['installed_root'])
        current = installed
        for part in relative.parts:
            current = current / part
            if current.is_symlink():
                raise ValueError('export state路径不能经过alias')
        expected = artifacts.contents_member(export_binding['contents'], relative.as_posix())
        if (export.get('status') != 'preserved' or current.resolve() != source
                or export_binding['installed_member'] != 'workspace'
                or export['installed']['workspace'] != export_binding['contents']
                or artifacts.contents(source) != expected):
            raise ValueError('state-binding与真实导出state/装配不一致')
        if export_binding['source_identity']['backend_identity'].get('container_id') != export['source'].get('container_id'):
            raise ValueError('state-binding不是export来源container')
        source_layout = {'run_root': str(logical_root), **export_binding['platform']}
    declared = []
    physical = {}
    overrides = definition_bindings or {}
    if set(overrides) - {row['name'] for row in layout['definitions']}:
        raise ValueError('definition binding包含未声明name')
    for row in layout['definitions']:
        asset_binding = overrides.get(row['name'], row.get('artifact'))
        if not asset_binding or not asset_binding.get('store'):
            raise ValueError('checkpoint definition缺少真实artifact binding：' + row['name'])
        original = row.get('artifact')
        if original and (original['reference'] != asset_binding['reference'] or original.get('member', '.') != asset_binding.get('member', '.')):
            raise ValueError('definition override只能选择同ref/member解析位置；换版必须显式prepare repair：' + row['name'])
        declared.append({'name': row['name'], 'logical_root': row['logical_root'], 'identity': row['identity'],
                         'artifact': asset_binding['reference'], 'member': asset_binding.get('member', '.')})
        physical[row['name']] = {'store': str(Path(asset_binding['store']).resolve(strict=True))}
    assets = definition_assets(declared, logical_root)
    identity_value, stop_value = json.loads(identity.read_text()), json.loads(stop.read_text())
    validate_stop_identity(identity_value, stop_value)
    if export_binding and any(export_binding['source_identity'].get(key) != identity_value[key] for key in source_identity_fields(identity_value)):
        raise ValueError('state-binding不是当前停止来源执行身份')
    acquisition_value = _acquisition(acquisition, identity_value)
    output = Path(output).absolute()
    if output.exists() or output.is_relative_to(source):
        raise ValueError('检查点输出必须是来源以外的新目录')
    output.mkdir(parents=True)
    write(output / 'production.json', {'phase': 'staging', 'argv': sys.argv, 'producer': HOOK, 'source': str(source)})
    (output / 'provenance').mkdir()
    write(output / 'provenance/asset-bindings.json', physical)
    manifest = {'kind': KIND, 'schema_version': 4 if snapshot else 3, 'checkpoint_id': 'hcp-' + uuid.uuid4().hex,
                'producer': {'name': 'pi-braid-checkpoint', 'hook': HOOK, 'sha256': PRODUCER_SOURCE_SHA256},
                'created_at': datetime.now(timezone.utc).isoformat(), 'source_identity': identity_value,
                'acquisition': acquisition_value, 'validator': validator_identity(), 'coverage': capabilities(),
                'layout': source_layout,
                'definition_assets': assets, 'derived_inputs': layout['derived_inputs'], 'capabilities': capabilities()}
    verified_assets = {}
    mounts, bindings = resolve_definition_assets(output, manifest, verified=verified_assets)
    from lab.exp import artifacts
    physical_roots = dict(mounts)
    for row in definition_mount_roots(assets, logical_root):
        logical, actual = row['logical_root'], physical_roots[row['logical_root']]
        if export_binding:
            placement = next((value for value in export_binding['definitions'] if value['logical_root'] == logical
                              and value['artifact'] == row['artifact'] and value['member'] == row['member']), None)
            if not placement or placement.get('access') != 'read-only':
                placement = next((value for value in export_binding.get('readonly_inputs', [])
                                  if value['artifact'] == row['artifact']
                                  and str(Path(value['root']) / row['member']) == logical), None)
                if not placement:
                    raise ValueError('导出definition缺少原执行真实RO input装配关系：' + logical)
        elif not snapshot and Path(logical).resolve() != actual.resolve() and artifacts.contents(Path(logical)) != artifacts.member_contents(bindings[row['name']]['store'], row['artifact'], row['member']):
            raise ValueError('声明definition与冻结artifact内容不同：' + logical)
    write(output / 'provenance/asset-bindings.json', bindings)
    if export:
        shutil.copy2(state_binding, output / 'provenance/state-export.json')
        manifest['state_provenance'] = {'member': 'provenance/state-export.json', 'sha256': digest(Path(state_binding))}
    if snapshot:
        binding = dict(snapshot)
        publication = artifacts._manifest(binding['store'],binding['reference'])
        proof = publication.get('provenance',{}).get('acquisition')
        actual_closure = acquisition_value.get('closure',{})
        if (not proof or proof.get('kind') != 'managed-writer-capture'
                or proof != binding.get('acquisition')
                or proof.get('capture_token') != actual_closure.get('capture_token')
                or proof.get('capture_request_id') != actual_closure.get('closure_id')
                or any(actual_closure.get(key) != value for key,value in proof['closure'].items())):
            raise ValueError('schema4 checkpoint requires the snapshot publication original managed capture; ordinary terminal content cannot be upgraded')
        binding['retention'] = artifacts.retain(binding['store'], binding['reference'],
            manifest['checkpoint_id'], 'checkpoint-state', manifest['checkpoint_id'] + '--state-retain')
        manifest['state_snapshot'] = binding
        sealed_source = referenced_state(manifest)
        if not source.samefile(sealed_source) and artifacts.contents(source) != artifacts.contents(sealed_source):
            raise ValueError('checkpoint source不是该snapshot实际state member')
        state_root = sealed_source
    else:
        (output / 'content').mkdir()
        shutil.copytree(source, output / 'content/run', symlinks=True, copy_function=copy_file)
        state_root = output / 'content/run'
    shutil.copy2(identity, output / 'provenance/source-identity.json')
    shutil.copy2(stop, output / 'provenance/stop-observation.json')
    readback = semantic_readback(state_root, logical_root, definition_mounts=mounts)
    manifest.update(stop_provenance={'sha256': digest(stop), 'member': 'provenance/stop-observation.json',
                                    'role': 'historical_acquisition_basis'}, files=({'run/' + name: value for name, value in inventory(state_root).items()} if snapshot else inventory(output / 'content')),
                    status='partial' if readback['gaps'] or acquisition_value['status'] != 'writer-closed' else 'complete', readback=readback)
    write(output / 'harness-manifest.json', manifest)
    write(output / 'validation.json', validation_receipt(output, manifest, readback))
    write(output / 'production.json', {'phase': 'published', 'argv': sys.argv, 'producer': HOOK})
    return manifest


def prepare(source, output, target, repair=None, artifact_store=None, *, state_binding=None, state_readback=None):
    source = Path(source).resolve(strict=True)
    manifest = json.loads((source / 'harness-manifest.json').read_text())
    if manifest.get('schema_version') not in (3, 4):
        raise ValueError('新prepare只消费separated v3 checkpoint；旧v2保留原冻结producer及完整现场')
    verified_assets = {}
    validation = validate(source, _verified_assets=verified_assets)
    repair = repair or {}
    if set(repair) - {'definition_assets', 'provider_bindings', 'transient_links', 'nodegyp_tools'}:
        raise ValueError('v3修复仅支持显式definition关系替换与既有状态派生输入修复，不修改原共享材料')
    if validation['coverage']['structure'] != 'complete' and not repair:
        raise ValueError('结构缺损checkpoint需要明确支持的修复；不重建历史')
    if target.get('run_root') != manifest['layout']['run_root'] or target.get('os') != manifest['layout']['os']:
        raise ValueError('当前native hook只支持同OS、同run logical root')
    if target.get('architecture') != manifest['layout']['architecture'] or not target.get('runtime_identity'):
        raise ValueError('prepare需要同architecture及明确目标runtime identity')
    output = Path(output).absolute()
    if output.exists() or output.is_relative_to(source):
        raise ValueError('prepared输出必须为来源外部的新目录')
    if state_binding:
        from lab.exp import state
        holder = state_readback or state.query(state_binding)['holder']
        if holder['phase'] != 'repairing' or holder['snapshot']['reference'] != manifest['state_snapshot']['reference']:
            raise ValueError('domain-state prepare需要原snapshot对应的独立capture repair许可')
        if holder['locator'].get('kind') == 'local':
            run = Path(holder['locator']['path']).resolve(strict=True)
        elif state_readback and state_binding['authority']['kind'] == 'docker':
            run = Path(target['run_root']).resolve(strict=True)
        else:
            raise ValueError('Docker domain-state repair必须经实际domain capture helper执行')
        if run != Path(manifest['layout']['run_root']).resolve(strict=True):
            raise ValueError('domain-state locator不是checkpoint实际Harness state root')
    else:
        run = output / 'content/run'
    output.mkdir(parents=True)
    write(output / 'production.json', {'phase': 'staging', 'argv': sys.argv, 'producer': HOOK})
    shutil.copytree(source / 'provenance', output / 'provenance', symlinks=True, copy_function=copy_file)
    if state_binding:
        pass
    elif manifest['schema_version'] == 4:
        (output / 'content').mkdir()
        shutil.copytree(referenced_state(manifest), output / 'content/run', symlinks=True, copy_function=copy_file)
    else:
        shutil.copytree(source / 'content', output / 'content', symlinks=True, copy_function=copy_file)
    before = manifest['files']
    old_mounts, old_bindings = resolve_definition_assets(source, manifest, verified=verified_assets)
    assets = {row['name']: dict(row) for row in manifest['definition_assets']}
    locations = {name: dict(value) for name, value in old_bindings.items()}
    changes, seen = [], set()
    for row in repair.get('definition_assets', []):
        name = row['name']
        if name in seen or name not in assets or set(row) - {'name', 'artifact', 'member', 'store'}:
            raise ValueError('definition修复需要唯一已声明name、明确reference/member及可选store')
        seen.add(name)
        original = assets[name]
        fresh = {**original, 'artifact': row['artifact'], 'member': row.get('member', original['member'])}
        fresh['identity'] = {'kind': 'artifact-member', 'reference': fresh['artifact'], 'member': fresh['member']}
        assets[name] = fresh
        if row.get('store'):
            locations[name] = {'store': str(Path(row['store']).resolve(strict=True))}
        changes.append({'hook': 'definition-reference', 'name': name, 'before': original, 'after': fresh})
    prepared = {key: value for key, value in manifest.items() if key not in ('stop_provenance', 'state_snapshot')}
    prepared.update(kind=PREPARED, schema_version=4 if state_binding else 3, prepared_id='hprep-' + uuid.uuid4().hex,
                    definition_assets=definition_assets(list(assets.values()), manifest['layout']['run_root']),
                    target_layout=target, validator=validator_identity(), capabilities=capabilities())
    if state_binding:
        prepared.update(state_binding={**state_binding, 'generation': holder['generation'] + 1},
                        state_root=str(run), state_snapshot=manifest['state_snapshot'])
    write(output / 'provenance/asset-bindings.json', locations)
    # Explicitly acquire every dependency at the selected worker store; source references remain retained.
    if artifact_store:
        from lab.exp import artifacts
        from lab.exp.core import canonical
        transferred = set()
        for row in prepared['definition_assets']:
            source_store = locations[row['name']]['store']
            key = (str(Path(source_store).resolve()), canonical(row['artifact']), row['member'])
            if key not in transferred:
                if Path(source_store).resolve() != Path(artifact_store).resolve():
                    artifacts.transfer(source_store, artifact_store, row['artifact'], selected_member=row['member'], consumer=prepared['prepared_id'])
                    verified_assets[(str(Path(artifact_store).resolve()), canonical(row['artifact']), row['member'])] = artifacts.member_payload(artifact_store, row['artifact'], row['member'])
                transferred.add(key)
    mounts, bindings = resolve_definition_assets(output, prepared, artifact_store, verified_assets)
    write(output / 'provenance/asset-bindings.json', bindings)
    old_by_root, new_by_root = dict(old_mounts), dict(mounts)
    if state_binding and manifest['layout'].get('definition_layout') and not target['runtime_identity'].get('image_id'):
        from lab.exp.assembly import install_aliases
        placement = manifest['layout']['definition_layout']
        base = Path(placement['base'])
        roles = []
        expected = {}
        for asset in definition_mount_roots(prepared['definition_assets'], target['run_root']):
            logical = Path(asset['logical_root'])
            if logical != base / asset['name']:
                raise ValueError('definition repair alias不是原holder placements声明的role')
            roles.append({'role': asset['name'], 'reference': asset['artifact'], 'member': asset['member'],
                          'local_root': str(logical), 'physical_root': str(new_by_root[asset['logical_root']])})
        for asset in definition_mount_roots(manifest['definition_assets'], manifest['layout']['run_root']):
            expected[asset['name']] = {'reference': asset['artifact'], 'member': asset['member']}
        _, new_placement = install_aliases(roles, base, state_binding=state_binding, expected=expected)
        prepared['layout'] = {**manifest['layout'], 'definition_layout': new_placement}
    if not target['runtime_identity'].get('image_id'):
        from lab.exp import artifacts
        for asset in definition_mount_roots(prepared['definition_assets'], target['run_root']):
            logical = Path(asset['logical_root'])
            physical = new_by_root[asset['logical_root']]
            if (logical.exists() or logical.is_symlink()) and logical.resolve() != physical.resolve():
                expected = artifacts.member_contents(bindings[asset['name']]['store'], asset['artifact'], asset['member'])
                if artifacts.contents(logical.resolve()) != expected:
                    raise ValueError('Local definition logical root occupied by original content; cannot replace immutable source: ' + str(logical))
    runtime_asset = next((row for row in prepared['definition_assets'] if row['name'] == 'runtime'), None)
    if runtime_asset and runtime_asset['name'] in seen:
        old, new = old_by_root[runtime_asset['logical_root']], new_by_root[runtime_asset['logical_root']]
        for member in ('bin/braid', 'native-managed.mjs', 'node_modules/@earendil-works/pi-coding-agent/package.json'):
            if not (old/member).is_file() or not (new/member).is_file() or digest(old/member) != digest(new/member):
                raise ValueError('definition替换必须保留原Braid/native hook/Pi协议；不能迁移会话')
    if 'agent' in seen:
        agent = assets['agent']
        _refresh_native(run, Path(manifest['layout']['run_root']),
                        new_by_root[agent['logical_root']], agent['logical_root'])
    state_repairs = {key: value for key, value in repair.items() if key != 'definition_assets'}
    effects = apply_repairs(output, prepared, state_repairs, state_root=run)
    run_layout = run / 'harness-layout.json'
    layout = json.loads(run_layout.read_text())
    for row in layout['definitions']:
        asset = assets[row['name']]
        row['identity'] = asset.get('identity', row['identity'])
        row['artifact'] = {'reference': asset['artifact'], 'store': bindings[row['name']]['store'], 'member': asset['member']}
    layout['definition_layout'] = prepared['layout'].get('definition_layout')
    write(run_layout, layout)
    after = {'run/' + name: value for name, value in inventory(run).items()} if state_binding else inventory(output / 'content')
    readback = semantic_readback(run, manifest['layout']['run_root'], definition_mounts=mounts)
    file_changes = [{'member': name, 'before': before.get(name), 'after': after.get(name)}
                    for name in sorted(set(before) | set(after)) if before.get(name) != after.get(name)]
    prepared.update(files=after, readback=readback, changes=file_changes, repair_effects=[*changes, *effects],
                    status='complete' if not readback['gaps'] and manifest.get('acquisition',{}).get('status') == 'writer-closed' else 'partial',
                    source_input={'kind': manifest['kind'], 'manifest_sha256': digest(source/'harness-manifest.json')},
                    source_checkpoint={'checkpoint_id': manifest['checkpoint_id'], 'manifest_sha256': digest(source/'harness-manifest.json')},
                    allowed_changes=repair, preparation={'argv': sys.argv, 'network': False, 'model_credentials': False, 'hook': HOOK})
    write(output / 'harness-manifest.json', prepared)
    write(output / 'validation.json', validation_receipt(output, prepared, readback))
    write(output / 'production.json', {'phase': 'published', 'argv': sys.argv, 'producer': HOOK})
    return prepared



def application(source, output, requirements, source_identity, delivery_kind, commit=None):
    """Freeze an application independently of checkpoint and archive completeness."""
    if delivery_kind not in {'final','stage'}:
        raise ValueError('应用交付身份必须为 final 或 stage')
    source, output = Path(source).resolve(strict=True), Path(output).absolute()
    requirements = Path(requirements).resolve(strict=True)
    identity = json.loads(Path(source_identity).read_text()) if isinstance(source_identity,(str,Path)) else source_identity
    if not (identity.get('attempt_id') or identity.get('source_id')):
        raise ValueError('应用必须绑定明确来源attempt或历史source_id')
    if output.exists() or output.is_relative_to(source): raise ValueError('应用输出必须为新的独立目录')
    output.mkdir(parents=True)
    if commit:
        sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tooling/scripts'))
        from braid_runtime import export_delivery
        resolved = subprocess.check_output(['git','-C',str(source),'rev-parse','--verify',commit+'^{commit}'],text=True).strip()
        if resolved != commit: raise ValueError('应用冻结必须使用完整commit身份')
        export_delivery(source,commit,output/'application')
        policy = 'selected-commit-only; uncommitted files excluded'
    else:
        if delivery_kind == 'stage': raise ValueError('阶段应用必须有明确Git commit')
        shutil.copytree(source,output/'application',symlinks=True)
        policy = 'delivered-snapshot; no reconstructed Git attribution'
    files = inventory(output/'application')
    for name,item in files.items():
        if item['type'] == 'symlink' and not (output/'application'/name).resolve().is_relative_to(output/'application'):
            raise ValueError('应用交付包含未冻结外部链接')
    manifest = {'kind':'factory26.harness.application','schema_version':2,
                'application_id':'happ-'+uuid.uuid4().hex,'source_identity':identity,
                'delivery_kind':delivery_kind,'commit':commit,'worktree_policy':policy,
                'requirements':inventory(requirements),'files':files,
                'producer':validator_identity(), 'status':'published',
                'coverage':{'content':'frozen','checkpoint':'not-required','evaluation':'not-observed'}}
    write(output/'application-manifest.json',manifest)
    return manifest

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['checkpoint', 'validate', 'prepare', 'application', 'capabilities'])
    parser.add_argument('--source', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--source-identity', type=Path)
    parser.add_argument('--stop-evidence', type=Path)
    parser.add_argument('--materials-root', action='append', default=[], type=Path, help='旧混装捕获已退役；不推断排除目录')
    parser.add_argument('--definition-bindings', type=Path, help='按layout definition name提供真实reference/store/member')
    parser.add_argument('--state-binding', type=Path, help='已分离Docker状态导出的真实export.json；保留原logical root和执行平台')
    parser.add_argument('--artifact-store', type=Path, help='明确解析/装配definition资产的当前位置')
    parser.add_argument('--target-layout', type=Path)
    parser.add_argument('--acquisition', type=Path)
    parser.add_argument('--repair', type=Path)
    parser.add_argument('--requirements', type=Path)
    parser.add_argument('--delivery-kind',choices=['final','stage'])
    parser.add_argument('--commit')
    args = parser.parse_args()
    if args.command == 'capabilities':
        print(json.dumps(capabilities(),ensure_ascii=False,indent=2)); return
    if not args.source: parser.error('需要 source')
    if args.command == 'application':
        if not args.output or not args.requirements or not args.source_identity or not args.delivery_kind:
            parser.error('application 需要 output/requirements/source-identity/delivery-kind')
        result = application(args.source,args.output,args.requirements,args.source_identity,args.delivery_kind,args.commit)
    elif args.command == 'validate':
        result = validate(args.source, args.artifact_store)
    elif args.command == 'checkpoint':
        if not args.output or not args.source_identity or not args.stop_evidence:
            parser.error('checkpoint 需要 output/source-identity/stop-evidence')
        result = checkpoint(args.source, args.output, args.source_identity, args.stop_evidence, args.materials_root,args.acquisition, json.loads(args.definition_bindings.read_text()) if args.definition_bindings else None, args.state_binding)
    else:
        if not args.output or not args.target_layout:
            parser.error('prepare 需要 output/target-layout')
        result = prepare(args.source, args.output, json.loads(args.target_layout.read_text()),json.loads(args.repair.read_text()) if args.repair else None, args.artifact_store)
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
