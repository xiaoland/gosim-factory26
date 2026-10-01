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
    subprocess.run([str(cache/'node_modules/.bin/playwright'),'install','chromium','--no-shell'],
                   env=dict(os.environ,PLAYWRIGHT_BROWSERS_PATH=str(cache/'.playwright')),check=True)
    return cache


def linux(output, backend, lock_dir, docker_context=None, braid_source=None):
    """Export an independent Linux runtime directory; Docker owns build caching."""
    output = Path(output).resolve()
    if output.exists():
        raise FileExistsError(output)
    lock_dir = Path(lock_dir).resolve()
    docker = ['docker']+(['--context',docker_context] if docker_context else [])
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
                                            'context7-pi-0.1.2.patch', 'pi-fff-0.11.0.patch')}
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
                '--build-arg',f'BACKEND={backend}','-t',name,str(context)],check=True)
            subprocess.run(docker+['create','--name',name,name],check=True);created=True
            output.parent.mkdir(parents=True,exist_ok=True)
            subprocess.run(docker+['cp',name+':/runtime',str(output)],check=True)
        finally:
            if created: subprocess.run(docker+['rm',name],check=True)
            subprocess.run(docker+['image','rm','--no-prune',name],check=False)
    (output/'runtime-source.json').write_text(json.dumps({'backend':backend,'platform':'linux-x86_64',
        'sources':records,'npm_sha256':npm_sha256,
        'native_patch_sha256':native_patch_sha256},indent=2)+'\n')
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
            'status': subprocess.check_output(['git', '-C', str(source), 'status', '--short'], text=True),
            'version': subprocess.check_output([str(ROOT/'.venv/bin/svc'), '--version'], text=True).strip()}
    target = ROOT/'.bootstrap/dev-svc.json'
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps(info, ensure_ascii=False, indent=2)+'\n')
    return target


def host_lab(output, base_python):
    """Build one immutable host Python environment for lab controllers and jobs."""
    output = output.expanduser().absolute()
    base_python = base_python.expanduser().absolute()
    if output.exists():
        raise FileExistsError(output)
    if not base_python.is_file() or not os.access(base_python, os.X_OK):
        raise ValueError(f'host lab base Python is not executable: {base_python}')
    requirements = ROOT/'lab/requirements.txt'
    output.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(['uv', 'venv', '--python', str(base_python), str(output)], check=True)
    launcher = output/('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    subprocess.run(['uv', 'pip', 'install', '--python', str(launcher), '-r', str(requirements)], check=True)
    packages = sorted(subprocess.check_output(
        ['uv', 'pip', 'freeze', '--python', str(launcher)], text=True).splitlines())
    version = subprocess.check_output(
        [str(launcher), '-c', 'import platform; print(platform.python_version())'], text=True).strip()
    receipt = {'schema_version': 1, 'record_type': 'factory26.host-runtime',
               'root': str(output), 'launcher': str(launcher), 'base_python': str(base_python),
               'python_version': version, 'host_platform': platform.platform(),
               'requirements': str(requirements),
               'requirements_sha256': hashlib.sha256(requirements.read_bytes()).hexdigest(),
               'packages': packages, 'identity': asset_inventory(output)}
    (output/'asset.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2)+'\n')
    return output/'asset.json'


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=['path','prepare','linux','dev-svc','host-lab'])
    p.add_argument('--lock-dir',type=Path,default=ROOT/'harness/npm')
    p.add_argument('--output',type=Path)
    p.add_argument('--backend',choices=['pi','codex'],default='pi')
    p.add_argument('--docker-context')
    p.add_argument('--braid-source',type=Path,help='Optional team dependency; raw runtimes do not require Braid')
    p.add_argument('--svc-source',type=Path,help='完整开发 SVC checkout；不是参赛 Corpus')
    p.add_argument('--python',type=Path,help='host-lab 使用的明确基础 Python')
    a=p.parse_args()
    if a.command=='path': result=cache_path(a.lock_dir)
    elif a.command=='prepare': result=prepare(a.lock_dir)
    elif a.command=='dev-svc':
        if a.svc_source is None: p.error('dev-svc requires --svc-source')
        result=dev_svc(a.svc_source)
    elif a.command=='host-lab':
        if a.output is None or a.python is None: p.error('host-lab requires --output and --python')
        result=host_lab(a.output,a.python)
    else:
        if a.output is None: p.error('linux requires --output')
        result=linux(a.output,a.backend,a.lock_dir,a.docker_context,a.braid_source)
    print(result)


if __name__=='__main__': main()
