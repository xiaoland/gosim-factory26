"""Prepare native tools without loading a Harness, Corpus or benchmark."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from lab.assets import asset_inventory
from lab.docker_endpoint import freeze as freeze_docker, environment as docker_environment, confirm as confirm_docker


def workssd_path(path):
    """Reject a system-disk alias before a producer creates any project files."""
    path = Path(path).expanduser().resolve()
    volume = Path('/Volumes/WorkSSD').resolve(strict=True)
    parent = path
    while not parent.exists():
        parent = parent.parent
    if not path.is_relative_to(volume) or parent.stat().st_dev != volume.stat().st_dev:
        raise ValueError(f'project output must physically reside on WorkSSD: {path}')
    return path

def production_environment(cache):
    cache = workssd_path(cache)
    locations = {'TMPDIR': 'tmp', 'XDG_CACHE_HOME': 'xdg', 'UV_CACHE_DIR': 'uv',
                 'PIP_CACHE_DIR': 'pip', 'npm_config_cache': 'npm',
                 'CARGO_HOME': 'cargo', 'CARGO_TARGET_DIR': 'target',
                 'ZIG_LOCAL_CACHE_DIR': 'zig/local', 'ZIG_GLOBAL_CACHE_DIR': 'zig/global'}
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', COPYFILE_DISABLE='1')
    for key, name in locations.items():
        directory = cache/name
        directory.mkdir(parents=True, exist_ok=True)
        env[key] = str(directory)
    return env

def cache_path(lock_dir):
    lock = Path(lock_dir)/'package-lock.json'
    return Path.home()/'.cache/factory26'/('runtime-'+hashlib.sha256(lock.read_bytes()).hexdigest()[:16])


def prepare(lock_dir):
    lock_dir = Path(lock_dir).resolve()
    cache = cache_path(lock_dir)
    lock = lock_dir/'package-lock.json'
    expected = cache/'package-lock.json'
    patches = (
        ('pi-background-bash', 'pi-background-bash-1.0.5.patch', ('extensions/background-bash.ts', 'bin/pbb.js')),
        ('pi-subagents', 'pi-subagents-0.56.0-completion-boundary.patch',
         ('src/extension/index.ts', 'src/runs/background/notify.ts', 'src/runs/background/result-watcher.ts', 'src/shared/utils.ts')),
        ('pi-subagents', 'pi-subagents-0.56.0-model-exclusion-boundary.patch',
         ('src/runs/shared/model-exclusions.ts', 'src/runs/shared/model-fallback.ts', 'src/runs/background/subagent-runner.ts')),
        ('pi-subagents', 'pi-subagents-0.56.0-open-tools.patch',
         ('src/runs/shared/pi-args.ts', 'src/runs/shared/subagent-prompt-runtime.ts')),
        ('pi-subagents', 'pi-subagents-0.56.0-acceptance-off.patch',
         ('README.md',
          'docs/agents.md',
          'docs/tool-reference.md',
          'docs/workflows.md',
          'skills/pi-subagents/SKILL.md',
          'skills/pi-subagents/references/constraints-and-recipes.md',
          'skills/pi-subagents/references/execution-controls.md',
          'skills/pi-subagents/references/multi-lane-orchestration.md',
          'skills/pi-subagents/references/prompting-and-roles.md',
          'src/extension/schemas.ts',
          'src/extension/tool-description.ts',
          'src/runs/background/async-execution.ts',
          'src/runs/background/async-resume.ts',
          'src/runs/background/async-status.ts',
          'src/runs/background/run-status.ts',
          'src/runs/background/subagent-runner.ts',
          'src/runs/background/wait-tool.ts',
          'src/runs/foreground/execution.ts',
          'src/runs/foreground/subagent-executor.ts',
          'src/runs/shared/acceptance.ts',
          'src/runs/shared/single-output.ts',
          'src/runs/shared/structured-output.ts')),
        ('@earendil-works/pi-coding-agent', 'pi-coding-agent-0.85.1-braid-boundary.patch', ('dist/core/agent-session.js', 'dist/core/tools/edit.js', 'dist/core/tools/grep.js', 'dist/core/tools/find.js', 'dist/core/resource-loader.js', 'dist/bundle/cli.js', 'dist/bundle/rpc-entry.js')),
        ('@upstash/context7-pi', 'context7-pi-0.1.2.patch', ('lib/prompts.ts', 'lib/api.ts', 'skills/context7-docs/SKILL.md')),
        ('@ff-labs/pi-fff', 'pi-fff-0.11.0.patch', ('src/index.ts',)),
        ('@earendil-works/pi-coding-agent', 'pi-coding-agent-0.85.1-i13-2-managed.patch',
         ('dist/modes/rpc/rpc-mode.js', 'dist/core/tools/bash.js')),
        ('pi-background-bash', 'pi-background-bash-1.0.5-i13-2-managed.patch',
         ('extensions/background-bash.ts',)),
        ('pi-subagents', 'pi-subagents-0.56.0-i13-2-managed.patch',
         ('src/runs/foreground/execution.ts', 'src/runs/background/async-execution.ts',
          'src/runs/background/subagent-runner.ts', 'src/runs/background/result-watcher.ts',
          'src/extension/index.ts')),
    )
    def patch_matches(package, patch_name, target_names):
        patch_file = lock_dir/'patches'/patch_name
        targets = [cache/'node_modules'/package/name for name in target_names]
        stamp = cache/(patch_name+'.sha256')
        return (stamp.is_file() and all(target.is_file() for target in targets) and
                stamp.read_text().splitlines() ==
                [hashlib.sha256(patch_file.read_bytes()).hexdigest(),
                 *(hashlib.sha256(target.read_bytes()).hexdigest() for target in targets)])
    if not expected.is_file() or expected.read_bytes()!=lock.read_bytes() or any(
            not (cache/'node_modules/.bin'/name).is_file() for name in ('pi','codex','agent-browser','playwright','pnpm','portless')) or \
            not all(patch_matches(*item) for item in patches):
        cache.mkdir(parents=True, exist_ok=True)
        for name in ('package.json','package-lock.json'):
            shutil.copy2(lock_dir/name, cache/name)
        subprocess.run(['npm','ci','--legacy-peer-deps','--prefix',str(cache)],check=True)
        for package, patch_name, target_names in patches:
            patch_file = lock_dir/'patches'/patch_name
            targets = [cache/'node_modules'/package/name for name in target_names]
            subprocess.run(['patch','--batch','--fuzz=0','-p1','-d',str(cache/'node_modules'/package),
                            '-i',str(patch_file)],check=True)
        # Later patches may touch an earlier patch's targets; record the final assembly.
        for package, patch_name, target_names in patches:
            patch_file = lock_dir/'patches'/patch_name
            targets = [cache/'node_modules'/package/name for name in target_names]
            (cache/(patch_name+'.sha256')).write_text(
                hashlib.sha256(patch_file.read_bytes()).hexdigest()+'\n'+
                ''.join(hashlib.sha256(target.read_bytes()).hexdigest()+'\n' for target in targets))
    shutil.copy2(lock_dir/'native-managed.mjs', cache/'native-managed.mjs')
    subprocess.run([str(cache/'node_modules/.bin/playwright'),'install','chromium','--no-shell'],
                   env=dict(os.environ,PLAYWRIGHT_BROWSERS_PATH=str(cache/'.playwright')),check=True)
    return cache


def linux(output, backend, lock_dir, docker_context=None, braid_source=None):
    """Export an independent Linux runtime directory; Docker owns build caching."""
    output = Path(output).resolve()
    if output.exists():
        raise FileExistsError(output)
    lock_dir = Path(lock_dir).resolve()
    endpoint = freeze_docker(docker_context)
    docker = endpoint['argv']
    docker_env = docker_environment(endpoint)
    name = 'factory26-runtime-'+uuid.uuid4().hex
    records = {}
    with tempfile.TemporaryDirectory(prefix=name) as tmp:
        context=Path(tmp)
        for file in ('Dockerfile','build.py'):
            shutil.copy2(ROOT/'submission'/file,context/file)
        shutil.copytree(lock_dir,context/'harness/npm',ignore=shutil.ignore_patterns('node_modules'))
        npm_sha256 = hashlib.sha256((context/'harness/npm/package-lock.json').read_bytes()).hexdigest()
        native_patch_sha256 = {name:hashlib.sha256((context/'harness/npm/patches'/name).read_bytes()).hexdigest()
                               for name in ('pi-background-bash-1.0.5.patch',
                                            'pi-subagents-0.56.0-completion-boundary.patch',
                                            'pi-subagents-0.56.0-model-exclusion-boundary.patch',
                                            'pi-subagents-0.56.0-open-tools.patch',
                                            'pi-subagents-0.56.0-acceptance-off.patch',
                                            'pi-coding-agent-0.85.1-braid-boundary.patch',
                                            'context7-pi-0.1.2.patch', 'pi-fff-0.11.0.patch',
                                            'pi-coding-agent-0.85.1-i13-2-managed.patch',
                                            'pi-background-bash-1.0.5-i13-2-managed.patch',
                                            'pi-subagents-0.56.0-i13-2-managed.patch')}
        if braid_source:
            source=Path(braid_source).resolve(strict=True)
            for part in ('Cargo.toml','Cargo.lock','src','migrations','config.example.toml'):
                origin=source/part;target=context/'sources/braid'/part
                target.parent.mkdir(parents=True,exist_ok=True)
                if origin.is_dir(): shutil.copytree(origin,target)
                elif origin.exists(): shutil.copy2(origin,target)
            braid_files = {str(path.relative_to(context/'sources/braid')):hashlib.sha256(path.read_bytes()).hexdigest()
                           for path in (context/'sources/braid').rglob('*') if path.is_file()}
            records['braid']={'revision':subprocess.check_output(['git','rev-parse','HEAD'],cwd=source,text=True).strip(),
                              'source_sha256':hashlib.sha256(json.dumps(braid_files,sort_keys=True).encode()).hexdigest()}
        created=False
        try:
            subprocess.run(docker+['build','--platform','linux/amd64','--target','team' if braid_source else 'runtime',
                '--build-arg',f'BACKEND={backend}','-t',name,str(context)],check=True,env=docker_env)
            confirm_docker(endpoint)
            subprocess.run(docker+['create','--name',name,name],check=True,env=docker_env);created=True
            output.parent.mkdir(parents=True,exist_ok=True)
            subprocess.run(docker+['cp',name+':/runtime',str(output)],check=True,env=docker_env)
        finally:
            confirm_docker(endpoint)
            if created: subprocess.run(docker+['rm',name],check=True,env=docker_env)
            subprocess.run(docker+['image','rm','--no-prune',name],check=False,env=docker_env)
    (output/'runtime-source.json').write_text(json.dumps({'backend':backend,'platform':'linux-x86_64',
        'sources':records,'npm_sha256':npm_sha256,'docker_endpoint':endpoint,
        'native_patch_sha256':native_patch_sha256,
        'native_modules_sha256': {'native-managed.mjs': hashlib.sha256(
            (lock_dir/'native-managed.mjs').read_bytes()).hexdigest()}},indent=2)+'\n')
    return output


def dev_svc(source):
    """Install the complete development CLI from an explicitly chosen checkout."""
    source = source.expanduser().resolve(strict=True)
    package = source/'cli'
    if not (package/'pyproject.toml').is_file():
        raise ValueError('开发 SVC 源码必须包含 cli/pyproject.toml；参赛 Corpus 树不能代替')
    python = ROOT/'.venv/bin/python'
    if not python.exists():
        subprocess.run(['uv', 'venv', '--python', '3.13', str(ROOT/'.venv')], check=True)
    subprocess.run(['uv', 'pip', 'install', '--python', str(python),
                    '--reinstall-package', 'sustainable-vibe-coding', str(package)], check=True)
    info = {'source': str(source),
            'revision': subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip(),
            'status': subprocess.check_output(['git', '-C', str(source), 'status', '--short', '--', '.'], text=True),
            'version': subprocess.check_output([str(ROOT/'.venv/bin/svc'), '--version'], text=True).strip()}
    target = ROOT/'.bootstrap/dev-svc.json'
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps(info, ensure_ascii=False, indent=2)+'\n')
    return target


def host_lab(output, base_python, purpose):
    """Build one explicitly identified controller or runner Python runtime."""
    output = output.expanduser().absolute()
    base_python = base_python.expanduser().absolute()
    if output.exists():
        raise FileExistsError(output)
    if not base_python.is_file() or not os.access(base_python, os.X_OK):
        raise ValueError(f'host lab base Python is not executable: {base_python}')
    requirements = ROOT/'lab/requirements.txt'
    output.parent.mkdir(parents=True, exist_ok=True)
    environment=production_environment(output.parent/'.producer-cache')
    subprocess.run(['uv', 'venv', '--python', str(base_python), str(output)], check=True,env=environment)
    launcher = output/('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    subprocess.run(['uv', 'pip', 'install', '--python', str(launcher), '-r', str(requirements)], check=True,env=environment)
    packages = sorted(subprocess.check_output(
        ['uv', 'pip', 'freeze', '--python', str(launcher)], text=True).splitlines())
    version = subprocess.check_output(
        [str(launcher), '-c', 'import platform; print(platform.python_version())'], text=True).strip()
    receipt = {'schema_version': 1, 'kind': 'factory26.exp.runtime', 'purpose': purpose,
               'root': str(output), 'launcher': str(launcher), 'base_python': str(base_python),
               'python_version': version, 'host_platform': platform.platform(),
               'interpreter_sha256': hashlib.sha256(launcher.resolve(strict=True).read_bytes()).hexdigest(),
               'requirements': str(requirements),
               'requirements_sha256': hashlib.sha256(requirements.read_bytes()).hexdigest(),
               'packages': packages, 'identity': asset_inventory(output)}
    (output/'asset.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2)+'\n')
    return output/'asset.json'



def plan_host_runtime(base_python):
    """Pure dependency planning; do not execute an interpreter during compile."""
    base_python = Path(base_python).expanduser().resolve(strict=True)
    if not base_python.is_file():
        raise ValueError('runtime producer 需要明确解释器文件')
    dependencies = {'interpreter': hashlib.sha256(base_python.read_bytes()).hexdigest(),
                    'requirements': hashlib.sha256((ROOT/'lab/requirements.txt').read_bytes()).hexdigest(),
                    'producer': hashlib.sha256(''.join(__import__('inspect').getsource(function) for function in (host_lab,production_environment,workssd_path)).encode()).hexdigest(),
                    'platform': platform.system(), 'architecture': platform.machine()}
    return {'kind': 'factory26.exp.runtime-plan', 'schema_version': 1, 'dependencies': dependencies,
            'key': hashlib.sha256(json.dumps(dependencies, sort_keys=True).encode()).hexdigest()}


def ensure_host_runtime(cache_root, base_python, purpose, expected_dependencies=None, *, verification_window=None):
    """Controller and runner bind separate receipts to one verified physical venv."""
    import fcntl
    if purpose not in {'controller', 'runner'}:
        raise ValueError('runtime purpose 必须明确 controller 或 runner')
    plan = plan_host_runtime(base_python)
    if expected_dependencies is not None and expected_dependencies != plan['dependencies']:
        raise ValueError('runtime dependencies 与冻结选择不一致')
    cache = Path(cache_root).expanduser().resolve()
    cache.mkdir(parents=True, exist_ok=True)
    with (cache/'.runtime.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        root = cache/plan['key']/'environment'
        reused = root.exists()
        if not reused:
            receipt = host_lab(root, Path(base_python), purpose)
        else:
            receipt = root/'asset.json'
        value = json.loads(receipt.read_text())
        readback=(str(root.resolve()),json.dumps(value['identity'],sort_keys=True))
        if verification_window is None or readback not in verification_window:
            if value['identity'] != asset_inventory(root):
                raise ValueError('共享 runtime 已被修改；不覆盖原环境')
            if verification_window is not None: verification_window.add(readback)
        if plan_host_runtime(base_python)['dependencies'] != plan['dependencies']:
            raise ValueError('runtime 构建期间依赖发生变化')
        value.update(purpose=purpose, dependencies=plan['dependencies'])
        selected = root.parent/(purpose + '.json')
        if not selected.exists(): selected.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')
        elif json.loads(selected.read_text()) != value: raise ValueError('runtime binding receipt 不一致')
        return {**value, 'receipt': str(selected), 'reused': reused}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=['path','prepare','linux','dev-svc','host-exp'])
    p.add_argument('--lock-dir',type=Path,default=ROOT/'harness/npm')
    p.add_argument('--output',type=Path)
    p.add_argument('--backend',choices=['pi','codex'],default='pi')
    p.add_argument('--docker-context')
    p.add_argument('--braid-source',type=Path,help='Optional team dependency; raw runtimes do not require Braid')
    p.add_argument('--svc-source',type=Path,help='完整开发 SVC checkout；不是参赛 Corpus')
    p.add_argument('--python',type=Path,help='host-exp 使用的明确基础 Python')
    p.add_argument('--purpose',choices=['controller','runner'],help='明确 runtime 制品职责')
    a=p.parse_args()
    if a.command=='path': result=cache_path(a.lock_dir)
    elif a.command=='prepare': result=prepare(a.lock_dir)
    elif a.command=='dev-svc':
        if a.svc_source is None: p.error('dev-svc requires --svc-source')
        result=dev_svc(a.svc_source)
    elif a.command=='host-exp':
        if a.output is None or a.python is None or a.purpose is None: p.error('host-exp requires --output/--python/--purpose')
        result=host_lab(a.output,a.python,a.purpose)
    else:
        if a.output is None: p.error('linux requires --output')
        result=linux(a.output,a.backend,a.lock_dir,a.docker_context,a.braid_source)
    print(result)


if __name__=='__main__': main()
