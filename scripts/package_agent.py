"""Package one independent Harness; runtime and skill inputs are explicit."""
import argparse
import ast
import fcntl
import uuid
import platform
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import stat
import subprocess
import sys
import tempfile
import zipfile

if __package__:
    from .agent_support import copy_skill
else:
    from agent_support import copy_skill

ROOT=Path(__file__).resolve().parents[1]

TOOL_KEY_NAMES = ('CONTEXT7_API_KEY', 'EXA_API_KEY')
I14_VARIANTS = {'pi-braid-i14', 'pi-braid-i14-cleaner', 'pi-braid-i14-reviewer', 'pi-braid-i14-e2e'}


def require_private_artifact(path):
    path = Path(path).resolve()
    if path.is_relative_to(ROOT) and subprocess.run(
            ['git', 'check-ignore', '-q', '--', str(path)], cwd=ROOT).returncode != 0:
        raise ValueError('含工具凭据的私有制品须放在 Git 忽略目录（如 runs/）或仓库外')


def write_tool_credentials(env_file, destination):
    """Read an explicit two-key dotenv input as data, never as shell commands."""
    values = {}
    for number, line in enumerate(Path(env_file).read_text().splitlines(), 1):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        name, separator, value = line.removeprefix('export ').partition('=')
        name = name.strip()
        if not separator or name not in TOOL_KEY_NAMES or name in values:
            raise ValueError(f'工具凭据输入第 {number} 行不是唯一的已知变量赋值')
        try:
            tokens = shlex.split(value, comments=True, posix=True)
        except ValueError:
            raise ValueError(f'工具凭据输入第 {number} 行引号不完整') from None
        if len(tokens) != 1 or not tokens[0]:
            raise ValueError(f'工具凭据输入第 {number} 行需要一个非空值')
        values[name] = tokens[0]
    if set(values) != set(TOOL_KEY_NAMES):
        raise ValueError('工具凭据输入需要 CONTEXT7_API_KEY 与 EXA_API_KEY')
    target = Path(destination)/'.private/tool-env.json'
    require_private_artifact(target)
    target.parent.mkdir(mode=0o700)
    with os.fdopen(os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'w') as stream:
        json.dump(values, stream)
        stream.write('\n')

def is_metadata_path(path):
    """Exclude transport-created macOS metadata from runnable package payloads."""
    return any(part.startswith('._') or part in {'.DS_Store', '__MACOSX', '__pycache__'} or part.endswith('.pyc')
               for part in Path(path).parts)


def prune_metadata(root):
    for path in sorted(root.rglob('*'), key=lambda item: len(item.parts), reverse=True):
        if is_metadata_path(path.name) and (path.exists() or path.is_symlink()):
            if path.is_dir() and not path.is_symlink():
                shutil.rmtree(path)
            else:
                path.unlink()

def bundle_files(root):
    """Materialize internal symlinks; reject escape, cycles, and special files."""
    root = root.resolve()

    def walk(directory, ancestors):
        resolved = directory.resolve()
        if not resolved.is_relative_to(root):
            raise ValueError(f'参赛包链接越出根目录：{directory}')
        if resolved in ancestors:
            raise ValueError(f'参赛包链接形成循环：{directory}')
        for path in sorted(directory.iterdir()):
            if is_metadata_path(path.name):
                continue
            target = path.resolve()
            if not target.is_relative_to(root):
                raise ValueError(f'参赛包链接越出根目录：{path}')
            if path.is_dir():
                yield from walk(path, ancestors | {resolved})
            elif path.is_file():
                yield path
            else:
                raise ValueError(f'不支持的参赛包条目：{path}')

    yield from walk(root, set())

def write_zip(bundle, output, backend, records, capabilities=None, *, persist_manifest=True):
    bundle = bundle.resolve()
    if (bundle/'.private').is_dir():
        require_private_artifact(output)
    files = [path for path in bundle_files(bundle)
             if path != bundle / 'package-manifest.json'
             and 'node_modules/.bin' not in path.relative_to(bundle).as_posix()]
    manifest = {'schema_version': 1, 'backend': backend, 'platform': 'linux-x86_64',
                'python': '3.12', 'sources': records, 'files': {}}
    if capabilities is not None:
        manifest['capabilities'] = capabilities
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('xb') as stream:
        if (bundle/'.private').is_dir():
            output.chmod(0o600)
        try:
            with zipfile.ZipFile(stream, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
                for path in files:
                    info = zipfile.ZipInfo(path.relative_to(bundle).as_posix())
                    info.create_system = 3
                    mode = 0o600 if path.relative_to(bundle).parts[0] == '.private' else (0o755 if path.stat().st_mode & 0o111 else 0o644)
                    info.external_attr = (stat.S_IFREG | mode) << 16
                    # Hash exactly the bytes written without increasing the uploaded payload.
                    info.compress_type = zipfile.ZIP_DEFLATED
                    info.file_size = path.stat().st_size
                    content_hash = hashlib.sha256()
                    with path.open('rb') as incoming, archive.open(info, 'w') as outgoing:
                        for chunk in iter(lambda: incoming.read(1024 * 1024), b''):
                            content_hash.update(chunk)
                            outgoing.write(chunk)
                    manifest['files'][path.relative_to(bundle).as_posix()] = {
                        'sha256': content_hash.hexdigest(), 'executable': bool(path.stat().st_mode & 0o111)}
                encoded = (json.dumps(manifest, indent=2) + '\n').encode()
                info = zipfile.ZipInfo('package-manifest.json')
                info.create_system = 3
                info.external_attr = (stat.S_IFREG | 0o644) << 16
                info.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(info, encoded)
            if persist_manifest:
                (bundle / 'package-manifest.json').write_bytes(encoded)
        except BaseException:
            output.unlink()
            raise



def copy_file(source, destination):
    """APFS COW copies isolate writers; unsupported filesystems use ordinary copying."""
    if sys.platform == 'darwin':
        import ctypes
        import errno
        library = ctypes.CDLL(None,use_errno=True)
        if library.clonefile(os.fsencode(source),os.fsencode(destination),0) == 0:
            return str(destination)
        code = ctypes.get_errno()
        if code not in {errno.EXDEV,errno.ENOTSUP,errno.EINVAL}:
            raise OSError(code,os.strerror(code),str(source))
    return shutil.copy2(source,destination)

def assemble(source, destination, runtime, skill_source, skills):
    """Copy selected files. This boundary does not parse profiles or choose behavior."""
    destination=Path(destination);destination.mkdir(parents=True)
    source=Path(source)
    for item in source.iterdir():
        if item.name in {'__pycache__','variant.json','build.py'}: continue
        if item.is_dir(): shutil.copytree(item,destination/item.name)
        else: shutil.copy2(item,destination/item.name)
    shutil.copy2(ROOT/'submission/exp_checkpoint.py',destination/'exp_checkpoint.py')
    support=destination/'support';support.mkdir()
    for name in ('agent_support.py','braid_runtime.py','core.py','model_budget.mjs','runtime_resources.py'):
        shutil.copy2(ROOT/'scripts'/name,support/name)
    if source.name in I14_VARIANTS | {'pi-braid', 'pi-braid-i12', 'pi-braid-i13', 'pi-braid-i13-glm-root', 'pi-braid-flash-team', 'pi-braid-kimi-root'}:
        shutil.copy2(ROOT/'lab/otlp.py',support/'otlp.py')
        dependency = os.environ.get('FACTORY26_BUILD_OTLP_DEPENDENCIES')
        if not dependency:
            raise ValueError('材料生产必须绑定已准备 OTLP dependencies；请使用 package_agent.produce')
        shutil.copytree(dependency, support/'otlp-deps',copy_function=copy_file)
    for name in skills:
        copy_skill(Path(skill_source)/name,destination/'skills'/name)
    shutil.copytree(runtime,destination/'runtime',symlinks=True,copy_function=copy_file)
    return destination


def _tree_identity(root):
    """Freeze actual bytes/modes and literal links without reading through links."""
    root = Path(root).resolve(strict=True)
    rows = {}
    if root.is_file():
        return {'sha256': hashlib.sha256(root.read_bytes()).hexdigest(), 'mode': root.stat().st_mode & 0o777}
    for directory, folders, files in os.walk(root, followlinks=False):
        for name in sorted(folders + files):
            path = Path(directory)/name
            if name == '__pycache__' or is_metadata_path(name):
                if name in folders: folders.remove(name)
                continue
            member = path.relative_to(root).as_posix()
            if path.is_symlink(): rows[member] = {'link': os.readlink(path)}
            elif path.is_file():
                with path.open('rb') as incoming:
                    value = hashlib.file_digest(incoming, 'sha256').hexdigest()
                rows[member] = {'sha256': value, 'mode': path.stat().st_mode & 0o777}
    return rows


def _key(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def material_capabilities():
    return {'braid_session_budget': {'version': 2, 'native_children_share_owner': True,
                                    'missing_identity': 'reject'},
            'resource_evidence': {'required': True, 'owner': 'runner', 'binding': 'FACTORY26_EXP_SERVICES'},
            'checkpoint': {'schema_version': 2, 'producer': 'exp_checkpoint.py'},
            'application': {'schema_version': 2, 'producer': 'exp_checkpoint.py'},
            'variants': sorted(I14_VARIANTS)}


def _otlp_dependencies(cache, selected=None):
    if selected is not None:
        selected = Path(selected).resolve(strict=True)
        if not (selected/'opentelemetry/proto').is_dir():
            raise ValueError('OTLP dependencies 缺少 opentelemetry/proto')
        return selected
    dependencies = {'requirements': _tree_identity(ROOT/'lab/requirements.txt'),
                    'python': platform.python_version(), 'platform': 'pure-python'}
    target = cache/'otlp'/ _key(dependencies)
    if not (target/'dependency.json').exists():
        stage = target.with_name(target.name + '-' + uuid.uuid4().hex)
        stage.mkdir(parents=True)
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--quiet', '--no-compile',
                        '--target', str(stage/'payload'), '-r', str(ROOT/'lab/requirements.txt')], check=True)
        for binary in (stage/'payload').rglob('*.so'): binary.unlink()
        (stage/'dependency.json').write_text(json.dumps(dependencies, sort_keys=True))
        stage.rename(target)
    return target/'payload'


def selection(variant, runtime, skill_source=None, tool_env=None, e2e_runtime=None, otlp_dependencies=None):
    """Describe the same literal material selection consumed by variant build.py."""
    source = ROOT/'variants'/variant
    if variant not in I14_VARIANTS:
        raise ValueError('新材料生产首版只支持四个 I14 variant')
    skills = None
    for call in ast.walk(ast.parse((source/'build.py').read_text())):
        if isinstance(call, ast.Call) and isinstance(call.func, ast.Name) and call.func.id == 'assemble':
            skills = next(ast.literal_eval(value.value) for value in call.keywords if value.arg == 'skills')
    if not skills:
        raise ValueError('variant build 必须声明字面量 skills 选择')
    runtime = Path(runtime).resolve(strict=True)
    if not (runtime/'bin/braid').is_file():
        raise ValueError('材料生产需要明确含 Braid 的 runtime')
    child_sources = runtime/'node_modules/pi-subagents/src/runs'
    foreground = (child_sources/'foreground/execution.ts').read_text()
    background = (child_sources/'background/subagent-runner.ts').read_text()
    spawning = (child_sources/'shared/pi-spawn.ts').read_text()
    if ('...process.env' not in foreground or '...process.env' not in background or
            'getPiSpawnCommand(args' not in foreground or 'getPiSpawnCommand(args' not in background or
            'PI_SUBAGENT_PI_BINARY' not in spawning):
        raise ValueError('冻结child接线未声明继承父环境及预算包装器；不复用此runtime')
    skill_source = Path(skill_source or ROOT/'harness/skills').resolve(strict=True)
    # assemble copies every source member except variant.json and build.py;
    # build.py still participates because it executes the material selection.
    variant_source = {name: identity for name, identity in _tree_identity(source).items()
                      if name != 'variant.json'}
    dependencies = {'variant': variant, 'variant_source': variant_source,
                    'builder': _tree_identity(Path(__file__)), 'runtime': _tree_identity(runtime),
                    'skills': {name: _tree_identity(skill_source/name) for name in skills},
                    'support': {name: _tree_identity(ROOT/'scripts'/name) for name in
                                ('agent_support.py','braid_runtime.py','core.py','model_budget.mjs','runtime_resources.py')},
                    'checkpoint': _tree_identity(ROOT/'submission/exp_checkpoint.py'),
                    'collector': _tree_identity(ROOT/'lab/otlp.py'),
                    'otlp_requirements': _tree_identity(ROOT/'lab/requirements.txt'),
                    'sdk_wrapper': _tree_identity(ROOT/'lab/arc_bench/agent_runtime'),
                    'sdk_exporter': _tree_identity(ROOT/'lab/arc_bench/__main__.py')}
    if tool_env is not None: dependencies['private_tool_credentials'] = _tree_identity(Path(tool_env))
    if variant == 'pi-braid-i14-e2e':
        e2e_runtime = Path(e2e_runtime or runtime/'e2e').resolve(strict=True)
        dependencies['e2e_runtime'] = _tree_identity(e2e_runtime)
    if otlp_dependencies is not None:
        dependencies['otlp_dependencies'] = _tree_identity(Path(otlp_dependencies))
    else:
        dependencies['otlp_build'] = {'python': platform.python_version(), 'pure_python': True}
    return dependencies


def plan_material(variant, runtime, skill_source=None, tool_env=None, e2e_runtime=None, otlp_dependencies=None):
    return selection(variant, runtime, skill_source, tool_env, e2e_runtime, otlp_dependencies)


def produce(variant, output_store, runtime, skill_source=None, tool_env=None,
            e2e_runtime=None, otlp_dependencies=None, expected_dependencies=None):
    """Reuse verified material production across runs; callers publish it once."""
    cache = Path(output_store).resolve()
    cache.mkdir(parents=True, exist_ok=True)
    with (cache/'.producer.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        dependencies = plan_material(variant, runtime, skill_source, tool_env, e2e_runtime, otlp_dependencies)
        if expected_dependencies is not None and dependencies != expected_dependencies:
            raise ValueError('producer dependencies 与冻结选择不一致；必须重新编译')
        otlp = _otlp_dependencies(cache, otlp_dependencies)
        identity = _key(dependencies)
        target = cache/'materials'/identity
        receipt = target/'material.json'
        if receipt.exists():
            value = json.loads(receipt.read_text())
            if value['dependencies'] != dependencies or _tree_identity(target/'payload') != value['contents']:
                raise ValueError('已发布材料或依赖身份发生变化；保留现场，不覆盖')
            return {**value, 'manifest_sha256': hashlib.sha256(receipt.read_bytes()).hexdigest(), 'reused': True}
        stage = cache/'.staging'/('material-' + uuid.uuid4().hex)
        stage.mkdir(parents=True)
        command = [sys.executable, str(ROOT/'variants'/variant/'build.py'), '--stage', str(stage/'payload'),
                   '--runtime', str(Path(runtime).resolve(strict=True)), '--skills', str(Path(skill_source or ROOT/'harness/skills').resolve(strict=True))]
        for flag, value in (('--tool-env', tool_env), ('--e2e-runtime', e2e_runtime)):
            if value is not None: command += [flag, str(Path(value).resolve(strict=True))]
        (stage/'production.json').write_text(json.dumps({'phase': 'staging', 'argv': command, 'dependencies': dependencies}, ensure_ascii=False))
        try:
            subprocess.run(command, check=True, env={**os.environ, 'FACTORY26_BUILD_OTLP_DEPENDENCIES': str(otlp)})
            prune_metadata(stage/'payload')
            if plan_material(variant, runtime, skill_source, tool_env, e2e_runtime, otlp_dependencies) != dependencies:
                raise ValueError('生产期间材料来源发生变化')
            value = {'kind': 'factory26.harness.material', 'schema_version': 2,
                     'material_id': 'material-' + identity, 'root': str(target/'payload'),
                     'dependencies': dependencies, 'capabilities': material_capabilities(),
                     'contents': _tree_identity(stage/'payload')}
            (stage/'material.json').write_text(json.dumps(value, ensure_ascii=False, sort_keys=True)+'\n')
            target.parent.mkdir(parents=True, exist_ok=True)
            stage.rename(target)
            return {**value, 'manifest_sha256': hashlib.sha256(receipt.read_bytes()).hexdigest(), 'reused': False}
        except BaseException as error:
            (stage/'failure.json').write_text(json.dumps({'type': type(error).__name__, 'message': str(error)}, ensure_ascii=False))
            raise


def package(variant, output, docker_context=None, runtime=None, stage=None,
            skill_source=None, tool_env=None, e2e_runtime=None, cache_root=None, otlp_dependencies=None):
    if runtime is None:
        raise ValueError('新生产必须明确已冻结 runtime；缺失构建由 runtime producer 负责')
    if output is not None and Path(output).exists(): raise FileExistsError(output)
    cache = Path(cache_root or ROOT/'runs/material-cache')
    material = produce(variant, cache, runtime, skill_source, tool_env, e2e_runtime, otlp_dependencies)
    bundle = Path(material['root'])
    if stage is not None:
        shutil.copytree(bundle, Path(stage), symlinks=True)
    if output is not None:
        records = json.loads((Path(runtime)/'runtime-source.json').read_text()).get('sources', {}) if (Path(runtime)/'runtime-source.json').exists() else {}
        write_zip(bundle, Path(output).resolve(), 'pi', records,
                  {'variant': variant, **material['capabilities'], 'material_id': material['material_id']}, persist_manifest=False)
    if output is None and stage is None: raise ValueError('需要 output 或 stage')
    return Path(output or stage).resolve()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--variant',required=True)
    p.add_argument('--output',type=Path)
    p.add_argument('--stage',type=Path,help='准备可直接执行的目录，不压 ZIP')
    p.add_argument('--runtime',type=Path,help='复用 runtime.py linux 导出的目录')
    p.add_argument('--docker-context')
    p.add_argument('--cache-root',type=Path)
    p.add_argument('--otlp-dependencies',type=Path)
    p.add_argument('--skills',type=Path)
    p.add_argument('--tool-env',type=Path,help='工具凭据的显式 dotenv 输入；仅写入非 Git 制品私有配置')
    p.add_argument('--e2e-runtime',type=Path,help='I14 e2e 独立 Linux 工具与浏览器目录')
    a=p.parse_args()
    if a.output is None and a.stage is None:p.error('需要 --output 或 --stage')
    print(package(a.variant,a.output,a.docker_context,a.runtime,a.stage,a.skills,a.tool_env,a.e2e_runtime,a.cache_root,a.otlp_dependencies))


if __name__=='__main__':main()
