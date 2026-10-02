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
HOOK = 'pi-braid-logical-layout-v2'
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


def semantic_readback(payload, logical_root, materials=None):
    """Harness-owned readback: preserve Git, Braid DB/WAL and native history."""
    gaps, git, native = [], [], []
    mounts = [(str(logical_root), payload)]
    mounts += [(str(row['logical_root']), path_at(payload.parent, row['member'])) for row in materials or []]
    # Link checks need current types and targets; byte integrity is checked by validate().
    for logical, physical in mounts:
        for name, item in inventory(physical, hash_files=False).items():
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
    for logical, physical in mounts:
        for member, row in inventory(physical, hash_files=False).items():
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
    return {'schema_version': 2, 'stopped_checkpoint': True, 'active_checkpoint': False,
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


def _refresh_native(run, logical_root, material):
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
    shutil.copytree(material/'skills',skills,symlinks=True)
    write(request_path,request)
    state_request = run/'braid-state/request.json'
    if state_request.is_file():
        retained = json.loads(state_request.read_text())
        retained['profiles'] = request['profiles']
        write(state_request,retained)

def apply_repairs(output, manifest, repair):
    """Bounded material changes; original Git, native history and application stay intact."""
    if set(repair) - {'materials', 'provider_bindings', 'aliases', 'transient_links', 'nodegyp_tools', 'runtime'}:
        raise ValueError('未支持的恢复修复类别')
    content, run = output/'content', output/'content/run'
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

def validate(root):
    root = Path(root).resolve(strict=True)
    manifest = json.loads((root / 'harness-manifest.json').read_text())
    if manifest.get('kind') not in {KIND, PREPARED} or manifest.get('schema_version') not in {1, 2}:
        raise ValueError('不是当前 Harness checkpoint/prepared 合同')
    actual = inventory(root / 'content')
    if actual != manifest['files']:
        raise ValueError('检查点内容清单与读回不一致')
    identity = manifest['source_identity']
    source_identity_fields(identity, legacy_read=manifest['schema_version'] == 1)
    if manifest['kind'] == KIND:
        stop = manifest['stop_provenance']
        original = path_at(root, stop['member'])
        if digest(original) != stop['sha256']:
            raise ValueError('停止来源原件发生变化')
        observed = json.loads(original.read_text())
        validate_stop_identity(identity, observed, legacy_read=manifest['schema_version'] == 1)
    if manifest['schema_version'] == 2 and manifest.get('validator',{}).get('hook') != HOOK:
        raise ValueError('Harness validator hook不支持此证明覆盖')
    readback = semantic_readback(root / 'content/run', manifest['layout']['run_root'], manifest['materials'])
    consistency = manifest.get('acquisition', {}).get('status', 'unknown')
    expected_status = 'partial' if readback['gaps'] or (manifest['schema_version'] == 2 and consistency != 'writer-closed') else 'complete'
    if manifest['schema_version'] == 2 and manifest['status'] != expected_status:
        raise ValueError('检查点完整性声明与实际缺口不一致')
    if manifest['schema_version'] == 2 and readback['gaps'] != manifest['readback']['gaps']:
        raise ValueError('检查点语义缺口与独立读回不一致')
    return {'kind': 'factory26.harness.validation', 'schema_version': 2, 'validator':validator_identity(),
            'coverage': {'content': 'verified', 'structure': 'partial' if readback['gaps'] else 'complete',
                         'acquisition': consistency, 'runtime_execution': 'not-observed'},
            'manifest_sha256': digest(root / 'harness-manifest.json'),
            'status': manifest['status'] if manifest['schema_version'] == 2 else 'partial', 'readback': readback,
            'capabilities': manifest['capabilities']}


def checkpoint(source, output, identity, stop, materials, acquisition=None):
    source = source.resolve(strict=True)
    identity_value = json.loads(identity.read_text())
    stop_value = json.loads(stop.read_text())
    validate_stop_identity(identity_value, stop_value)
    acquisition_value = _acquisition(acquisition, identity_value)
    output = output.absolute()
    if output.exists() or output.is_relative_to(source):
        raise ValueError('检查点输出必须是来源以外的新目录')
    output.mkdir(parents=True)
    write(output / 'production.json', {'phase': 'staging', 'argv': sys.argv,
                                      'producer': HOOK, 'source': str(source)})
    (output / 'content').mkdir()
    shutil.copytree(source, output / 'content/run', symlinks=True,copy_function=copy_file)
    copied = []
    for number, material in enumerate(materials):
        original = material.resolve(strict=True)
        if output.is_relative_to(original):
            raise ValueError('检查点输出不能位于材料来源内部')
        member = f'content/materials/{number}'
        shutil.copytree(original, output / member, symlinks=True,copy_function=copy_file)
        copied.append({'logical_root': str(original), 'member': member.removeprefix('content/')})
    (output / 'provenance').mkdir()
    shutil.copy2(identity, output / 'provenance/source-identity.json')
    shutil.copy2(stop, output / 'provenance/stop-observation.json')
    readback = semantic_readback(output / 'content/run', source, copied)
    manifest = {'kind': KIND, 'schema_version': 2, 'checkpoint_id': 'hcp-' + uuid.uuid4().hex,
                'producer': {'name': 'pi-braid-checkpoint', 'hook': HOOK, 'sha256': PRODUCER_SOURCE_SHA256},
                'created_at': datetime.now(timezone.utc).isoformat(),
                'source_identity': identity_value, 'acquisition': acquisition_value,
                'validator': validator_identity(), 'coverage': capabilities(),
                'stop_provenance': {'sha256': digest(stop), 'member': 'provenance/stop-observation.json',
                                    'role': 'historical_acquisition_basis'},
                'layout': {'run_root': str(source), 'os': platform.system(), 'architecture': platform.machine()},
                'materials': copied, 'files': inventory(output / 'content'),
                'status': 'partial' if readback['gaps'] or acquisition_value['status'] != 'writer-closed' else 'complete', 'readback': readback,
                'capabilities': capabilities()}
    write(output / 'harness-manifest.json', manifest)
    write(output / 'validation.json', validate(output))
    write(output / 'production.json', {'phase': 'published', 'argv': sys.argv, 'producer': HOOK})
    return manifest


def prepare(source, output, target, repair=None):
    validation = validate(source)
    if validation['coverage']['structure'] != 'complete' and not repair:
        raise ValueError('结构缺损 checkpoint 需要明确支持的修复；不重建历史')
    manifest = json.loads((source / 'harness-manifest.json').read_text())
    if manifest['kind'] not in {KIND,PREPARED}:
        raise ValueError('prepare 输入必须是 checkpoint 或已有派生prepared')
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
    shutil.copytree(source / 'content', output / 'content', symlinks=True,copy_function=copy_file)
    before = inventory(output/'content')
    changes = apply_repairs(output, {**manifest, 'target_layout':target}, repair or {})
    readback = semantic_readback(output/'content/run', manifest['layout']['run_root'], manifest['materials'])
    after = inventory(output/'content')
    actual_changes = [{'member': name, 'before': before.get(name), 'after': after.get(name)}
                      for name in sorted(set(before) | set(after)) if before.get(name) != after.get(name)]
    prepared = {key: value for key, value in manifest.items() if key not in {'stop_provenance'}}
    prepared.update(kind=PREPARED, schema_version=2, validator=validator_identity(), capabilities=capabilities(),
                    acquisition=manifest.get('acquisition', {'status':'unknown','limitation':'legacy source has no acquisition-window proof'}),
                    readback=readback, files=after,
                    status='complete' if not readback['gaps'] and manifest.get('acquisition',{}).get('status') == 'writer-closed' else 'partial',
                    losses=[*manifest.get('losses', []),*[gap for gap in readback['gaps'] if gap['kind']=='lost-original-git-history']], changes=actual_changes, repair_effects=changes,
                    prepared_id='hprep-' + uuid.uuid4().hex,
                    source_input={'kind':manifest['kind'],'manifest_sha256':digest(source/'harness-manifest.json')},
                    source_checkpoint={'checkpoint_id': manifest['checkpoint_id'],
                                       'manifest_sha256': digest(source / 'harness-manifest.json')},
                    allowed_changes=repair or {}, target_layout=target,
                    preparation={'argv': sys.argv, 'network': False, 'model_credentials': False, 'hook': HOOK})
    write(output / 'harness-manifest.json', prepared)
    write(output / 'validation.json', validate(output))
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
        sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
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
    parser.add_argument('--materials-root', action='append', default=[], type=Path)
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
        result = validate(args.source)
    elif args.command == 'checkpoint':
        if not args.output or not args.source_identity or not args.stop_evidence:
            parser.error('checkpoint 需要 output/source-identity/stop-evidence')
        result = checkpoint(args.source, args.output, args.source_identity, args.stop_evidence, args.materials_root,args.acquisition)
    else:
        if not args.output or not args.target_layout:
            parser.error('prepare 需要 output/target-layout')
        result = prepare(args.source, args.output, json.loads(args.target_layout.read_text()),json.loads(args.repair.read_text()) if args.repair else None)
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
