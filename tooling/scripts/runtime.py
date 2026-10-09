"""Prepare native tools without loading a Harness, Corpus or benchmark."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import shlex
import subprocess
import sys
import tempfile
import uuid
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lab.assets import asset_inventory
from lab.docker_endpoint import freeze as freeze_docker, environment as docker_environment, confirm as confirm_docker
from tooling.linux.browser_runtime import browser_scripts


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
    return ROOT/'runs/runtime-cache'/('runtime-'+hashlib.sha256(lock.read_bytes()).hexdigest()[:16])


PI_RETRY_MEMBER = 'node_modules/@earendil-works/pi-coding-agent/node_modules/@earendil-works/pi-ai/dist/utils/retry.js'
# Pinned npm lock + connection-reset patch output; reject historical inputs rather
# than silently changing the SDK bytes and their frozen runtime identity.
PI_RETRY_SHA256 = 'd92542c68b9026030708ff07c2b0f6ad2f8aa097e7e03f64ea809223da32cfbf'


def require_pi_retry_source(runtime):
    target = Path(runtime)/PI_RETRY_MEMBER
    actual = hashlib.sha256(target.read_bytes()).hexdigest() if target.is_file() else None
    if actual != PI_RETRY_SHA256:
        raise ValueError(f'Pi retry SDK missing or mismatched pi-ai-0.85.1-connection-reset.patch: {target}; sha256={actual}; expected={PI_RETRY_SHA256}; rebuild or explicitly derive a patched runtime')


def native_patch_specs():
    """Ordered patch inputs and target files shared by native runtime producers."""
    return (
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
        ('@earendil-works/pi-coding-agent', 'pi-coding-agent-0.85.1-braid-boundary.patch', ('dist/core/agent-session.js', 'dist/core/extensions/types.d.ts', 'dist/core/tools/edit.js', 'dist/core/tools/grep.js', 'dist/core/tools/find.js', 'dist/core/resource-loader.js', 'dist/bundle/cli.js', 'dist/bundle/rpc-entry.js')),
        ('@earendil-works/pi-coding-agent', 'pi-ai-0.85.1-connection-reset.patch',
         ('node_modules/@earendil-works/pi-ai/dist/utils/retry.js',)),
        ('@earendil-works/pi-coding-agent', 'pi-coding-agent-0.85.1-compaction-threshold.patch',
         ('dist/core/compaction/compaction.js', 'dist/core/compaction/compaction.d.ts',
          'dist/core/settings-manager.js', 'dist/core/settings-manager.d.ts')),
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
        ('pi-subagents', 'pi-subagents-0.56.0-catalog-hook.patch', ('src/extension/index.ts',)),
        ('pi-background-bash', 'pi-background-bash-1.0.5-native-result.patch', ('extensions/background-bash.ts', 'skills/pbb/SKILL.md')),
        ('pi-subagents', 'pi-subagents-0.56.0-wait-handle.patch', ('src/runs/background/subagent-wait.ts',)),
        ('@earendil-works/pi-coding-agent', 'pi-coding-agent-0.85.1-capacity-handoff.patch', ('dist/modes/rpc/rpc-mode.js',)),
        ('pi-background-bash', 'pi-background-bash-1.0.5-capacity-handoff.patch', ('extensions/background-bash.ts',)),
        ('mcporter', 'mcporter-0.14.0-managed-service.patch', ('dist/daemon/launch.js',)),
        ('pi-background-bash', 'pi-background-bash-1.0.5-visible-handle.patch', ('extensions/background-bash.ts', 'skills/pbb/SKILL.md')),
        ('pi-subagents', 'pi-subagents-0.56.0-owner-lifecycle.patch', ('src/runs/shared/session-lease.ts', 'src/shared/types.ts', 'src/runs/foreground/subagent-executor.ts', 'src/runs/background/subagent-runner.ts', 'src/runs/background/stale-run-reconciler.ts', 'src/runs/background/subagent-wait.ts')),
    )


def apply_native_patches(runtime, lock_dir, env=None):
    """Apply the maintained ordered patches to freshly installed npm packages."""
    runtime, lock_dir = Path(runtime), Path(lock_dir)
    for package, name, _ in native_patch_specs():
        subprocess.run(['patch', '--batch', '--fuzz=0', '-p1', '-d',
                        str(runtime/'node_modules'/package), '-i', str(lock_dir/'patches'/name)],
                       check=True, env=env)
    for name in ('native-managed.mjs', 'v8-observation.mjs'):
        shutil.copy2(lock_dir/name, runtime/name)
    return native_baseline_manifest(runtime, lock_dir)


def native_baseline_manifest(runtime, lock_dir):
    """Record final shared patch targets after every ordered patch is applied."""
    runtime, lock_dir = Path(runtime), Path(lock_dir)
    def sha(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()
    specs = native_patch_specs()
    targets = sorted({f'node_modules/{package}/{relative}'
                      for package, _, relatives in specs for relative in relatives})
    return {'npm_sha256': sha(lock_dir/'package-lock.json'),
            'native_patch_order': [name for _, name, _ in specs],
            'native_patch_sha256': {name: sha(lock_dir/'patches'/name) for _, name, _ in specs},
            'native_target_sha256': {name: sha(runtime/name) for name in targets},
            'native_modules_sha256': {name: sha(runtime/name) for name in ('native-managed.mjs', 'v8-observation.mjs')}}


def require_native_baseline(runtime, lock_dir=None):
    """Require current shared inputs and the producer's final bytes, not a variant overlay."""
    runtime = Path(runtime)
    lock_dir = Path(lock_dir) if lock_dir else ROOT/'materials/npm'
    source = json.loads((runtime/'runtime-source.json').read_text())
    actual = native_baseline_manifest(runtime, lock_dir)
    expected_module = hashlib.sha256((lock_dir/'native-managed.mjs').read_bytes()).hexdigest()
    if actual['native_modules_sha256']['native-managed.mjs'] != expected_module:
        raise ValueError('Pi baseline managed module differs from current shared source')
    for field, value in actual.items():
        if source.get(field) != value:
            raise ValueError(f'Pi native baseline {field} missing or mismatched: {runtime}; rebuild with the current shared producer; do not patch a variant copy')
    require_pi_retry_source(runtime)
    return actual


def native_patch_script():
    """Docker consumes the same ordered patch inventory as the native producer."""
    lines = ['#!/bin/sh', 'set -eu']
    for package, name, _ in native_patch_specs():
        lines.append('patch --batch --fuzz=0 -p1 -d '+shlex.quote('/runtime/node_modules/'+package)+
                     ' -i '+shlex.quote('/build/patches/'+name))
    return '\n'.join(lines)+'\n'


def derive_linux(output, package, braid_source, cache_root):
    """Derive a current Linux runtime from an immutable package, without Docker."""
    from tooling.scripts.package_agent import copy_file
    output, cache = workssd_path(output), workssd_path(cache_root)
    package, source = Path(package).resolve(strict=True), Path(braid_source).resolve(strict=True)
    env = production_environment(cache)
    def digest(path):
        with Path(path).open('rb') as stream:
            return hashlib.file_digest(stream, 'sha256').hexdigest()
    package_hash = digest(package)
    progress = output/'.derivation-in-progress.json'
    if output.exists() and (not progress.is_file() or json.loads(progress.read_text()).get('package_sha256') != package_hash):
        raise FileExistsError(output)
    output.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(package) as archive:
        records = json.loads(archive.read('runtime/runtime-source.json'))
        lock = ROOT/'materials/npm'
        if records['npm_sha256'] != digest(lock/'package-lock.json'):
            raise ValueError('retained Linux npm lock differs from current input')
        current_patches = {name: digest(lock/'patches'/name) for _, name, _ in native_patch_specs()}
        if records['native_patch_sha256'] != current_patches:
            raise ValueError('retained Linux native patch inventory differs from current input; rebuild or explicitly derive a patched package')
        target_names = {f'node_modules/{package}/{relative}' for package, _, relatives in native_patch_specs() for relative in relatives}
        target_records = records.get('native_target_sha256', {})
        if (records.get('native_patch_order') != [name for _, name, _ in native_patch_specs()] or
                set(target_records) != target_names):
            raise ValueError('retained Linux native baseline final-target manifest missing or mismatched; rebuild the shared producer')
        for member, expected in target_records.items():
            if hashlib.sha256(archive.read('runtime/'+member)).hexdigest() != expected:
                raise ValueError(f'retained Linux native baseline target differs: {member}')
        if records.get('backend') == 'pi' and hashlib.sha256(archive.read('runtime/'+PI_RETRY_MEMBER)).hexdigest() != PI_RETRY_SHA256:
            raise ValueError('retained Linux Pi retry SDK bytes are not the current patched source')
        for name, expected in records['native_modules_sha256'].items():
            if digest(lock/name) != expected:
                raise ValueError(f'retained Linux managed module differs: {name}')
        if not progress.is_file():
            for info in archive.infolist():
                if not info.filename.startswith('runtime/') or info.is_dir():
                    continue
                member = Path(info.filename).relative_to('runtime')
                destination = (output/member).resolve()
                if not destination.is_relative_to(output):
                    raise ValueError(f'unsafe source member: {info.filename}')
                destination.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(info) as incoming, destination.open('xb') as outgoing:
                    shutil.copyfileobj(incoming, outgoing)
                mode = (info.external_attr >> 16) & 0o777
                destination.chmod(mode or 0o644)
            progress.write_text(json.dumps({'package_sha256': package_hash, 'phase': 'base-extracted'})+'\n')
    # Cargo may update its registry/index. Clone the read-only installed cache
    # rather than symlinking it and letting compilation write into the user home.
    existing = Path.home()/'.cargo'
    for name in ('registry',):
        if (existing/name).is_dir() and not (cache/'cargo'/name).exists():
            shutil.copytree(existing/name, cache/'cargo'/name, copy_function=copy_file)
    def source_files():
        return {str(path.relative_to(source)): digest(path) for part in
                ('Cargo.toml', 'Cargo.lock', 'src', 'migrations', 'config.example.toml')
                for path in ([source/part] if (source/part).is_file() else (source/part).rglob('*'))
                if path.is_file()}
    before = source_files()
    command = ['cargo', 'zigbuild', '--locked', '--release', '--target',
               'x86_64-unknown-linux-gnu.2.36', '--manifest-path', str(source/'Cargo.toml')]
    logs = cache/'logs'
    logs.mkdir(exist_ok=True)
    with (logs/'braid-build.log').open('w') as log:
        subprocess.run(command, check=True, env=env, stdout=log, stderr=subprocess.STDOUT)
    if before != source_files():
        raise ValueError('Braid sources changed during compilation; preserve build and derive again')
    binary = cache/'target/x86_64-unknown-linux-gnu/release/braid'
    shutil.copy2(binary, output/'bin/braid')
    (output/'bin/braid').chmod(0o755)
    monitor_source = ROOT/'sources/resource-monitor'
    subprocess.run(['cargo', 'zigbuild', '--locked', '--release', '--target',
                    'x86_64-unknown-linux-gnu.2.36', '--manifest-path', str(monitor_source/'Cargo.toml')],
                   check=True, env=env)
    shutil.copy2(cache/'target/x86_64-unknown-linux-gnu/release/factory26-resource-monitor',
                 output/'bin/factory26-resource-monitor')
    (output/'bin/factory26-resource-monitor').chmod(0o755)
    records.setdefault('sources', {})['resource_monitor'] = {
        'binary_sha256': digest(output/'bin/factory26-resource-monitor'),
        'files': {str(path.relative_to(monitor_source)): digest(path)
                  for part in ('Cargo.toml', 'Cargo.lock', 'src')
                  for path in ([monitor_source/part] if (monitor_source/part).is_file() else (monitor_source/part).rglob('*'))
                  if path.is_file()}}
    versions = {}
    if records.get('backend') == 'codex':
        python = output/'python'
        if python.exists():
            shutil.rmtree(python)
        command = [sys.executable, '-m', 'pip', 'install', '--ignore-installed', '--no-compile', '--only-binary=:all:',
                   '--platform', 'manylinux2014_x86_64', '--platform', 'manylinux_2_28_x86_64',
                   '--python-version', '3.12', '--implementation', 'cp', '--abi', 'cp312',
                   '--target', str(python), 'litellm[proxy]==1.102.0']
        with (logs/'router-dependencies.log').open('w') as log:
            subprocess.run(command, check=True, env=env, stdout=log, stderr=subprocess.STDOUT)
        # pip --target generates host-interpreter scripts. The portable runtime
        # exports only its explicit bin/litellm launcher, never those Mac shebangs.
        shutil.rmtree(python/'bin', ignore_errors=True)
        for metadata in python.glob('*.dist-info/METADATA'):
            headers = dict(line.split(': ', 1) for line in metadata.read_text().splitlines()
                           if line.startswith(('Name: ', 'Version: ')))
            versions[headers['Name']] = headers['Version']
        (output/'python-requirements.lock').write_text(
            ''.join(f'{name}=={version}\n' for name, version in sorted(versions.items())))
        (output/'bin/litellm').write_text('#!/usr/bin/env python3\nimport sys\nfrom pathlib import Path\n'
            "sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'python'))\n"
            'from litellm import run_server\nsys.exit(run_server())\n')
        (output/'bin/litellm').chmod(0o755)
    else:
        # Pi/Braid targets do not start the LiteLLM proxy; leave the base
        # runtime untouched and record that no router layer was installed.
        (output/'python-requirements.lock').write_text('')
    records.pop('docker_endpoint', None)
    records['derivation'] = {'package': str(package), 'package_sha256': package_hash,
                             'producer': 'runtime.py derive-linux', 'cache_root': str(cache),
                             'python_target': 'cp312-manylinux-x86_64' if versions else None,
                             'router': versions}
    records['sources']['braid'] = {'revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=source, text=True).strip(),
        'working_tree_status': subprocess.check_output(
            ['git', 'status', '--short', '--untracked-files=all', '--', '.'], cwd=source, text=True),
        'source_sha256': hashlib.sha256(json.dumps(before, sort_keys=True).encode()).hexdigest(),
        'binary_sha256': digest(output/'bin/braid'), 'target': 'x86_64-unknown-linux-gnu.2.36',
        'files': before, 'command': ['cargo', 'zigbuild', '--locked', '--release', '--target', 'x86_64-unknown-linux-gnu.2.36']}
    records.update(native_baseline_manifest(output, lock))
    (output/'runtime-source.json').write_text(json.dumps(records, indent=2)+'\n')
    progress.unlink()
    return output


def slim_linux(output, source, profile='arc-core'):
    """Copy a frozen runtime while omitting browser payloads from the base mount.

    The Node browser clients remain available for an explicit on-demand install;
    startup no longer requires a preinstalled Chromium tree. The slim profile
    is additive and never mutates the source runtime.
    """
    if profile != 'arc-core':
        raise ValueError('unsupported runtime profile')
    source = workssd_path(source).resolve(strict=True)
    output = workssd_path(output)
    if output.exists():
        raise FileExistsError(output)
    omitted = {'.playwright', 'share/fonts', 'share/glib-2.0', 'etc/fonts', 'bin/chromium',
               # tooling/linux/build.py freezes one Linux ast-grep binary in
               # libexec/; the two npm native copies are byte-identical and
               # are not imported by either DX entry.
               'node_modules/@ast-grep/cli', 'node_modules/@ast-grep/cli-linux-x64-gnu',
               'e2e/browsers', 'e2e/.cache', 'e2e/.npm'}
    def ignore(directory, names):
        relative = Path(directory).relative_to(source)
        return [name for name in names if str(relative / name) in omitted]
    shutil.copytree(source, output, ignore=ignore, symlinks=True)
    # Canonical wrappers are shared with direct Docker builds.
    for name, script in browser_scripts().items():
        path = output / 'bin' / name
        path.write_text(script)
        path.chmod(0o755)
    source_record = output / 'runtime-source.json'
    if source_record.is_file():
        value = json.loads(source_record.read_text())
        value['profile'] = profile
        value['omitted_members'] = sorted(omitted)
        value['base_runtime'] = str(source)
        value['slim_wrapper_sha256'] = {
            name: hashlib.sha256((output / 'bin' / name).read_bytes()).hexdigest()
            for name in ('browser-install', 'browser-exec', 'agent-browser')
        }
        source_record.write_text(json.dumps(value, indent=2) + '\n')
    return output


def prepare(lock_dir):
    lock_dir = Path(lock_dir).resolve()
    cache = cache_path(lock_dir)
    env = production_environment(ROOT/'runs/build-cache'/cache.name)
    lock = lock_dir/'package-lock.json'
    expected = cache/'package-lock.json'
    patches = native_patch_specs()
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
        subprocess.run(['npm','ci','--legacy-peer-deps','--prefix',str(cache)],check=True,env=env)
        apply_native_patches(cache, lock_dir, env)
        # Later patches may touch an earlier patch's targets; record the final assembly.
        for package, patch_name, target_names in patches:
            patch_file = lock_dir/'patches'/patch_name
            targets = [cache/'node_modules'/package/name for name in target_names]
            (cache/(patch_name+'.sha256')).write_text(
                hashlib.sha256(patch_file.read_bytes()).hexdigest()+'\n'+
                ''.join(hashlib.sha256(target.read_bytes()).hexdigest()+'\n' for target in targets))
    for name in ('native-managed.mjs', 'v8-observation.mjs'):
        shutil.copy2(lock_dir/name, cache/name)
    subprocess.run([str(cache/'node_modules/.bin/playwright'),'install','chromium','--no-shell'],
                   env=dict(env,PLAYWRIGHT_BROWSERS_PATH=str(cache/'.playwright')),check=True)
    return cache


def linux(output, backend, lock_dir, docker_context=None, braid_source=None, profile='full'):
    """Export an independent Linux runtime directory; Docker owns build caching."""
    output = workssd_path(output)
    if output.exists():
        raise FileExistsError(output)
    lock_dir = Path(lock_dir).resolve()
    endpoint = freeze_docker(docker_context)
    docker = endpoint['argv']
    docker_env = docker_environment(endpoint)
    name = 'factory26-runtime-'+uuid.uuid4().hex
    records = {}
    staging = workssd_path(output.parent/'.runtime-staging')
    staging.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=name, dir=staging) as tmp:
        context=Path(tmp)
        for file in ('Dockerfile','build.py','browser_runtime.py'):
            shutil.copy2(ROOT/'tooling/linux'/file,context/file)
        shutil.copytree(lock_dir,context/'harness/npm',ignore=shutil.ignore_patterns('node_modules'))
        shutil.copytree(ROOT/'sources/resource-monitor', context/'sources/resource-monitor',
                        ignore=shutil.ignore_patterns('target'))
        (context/'apply-native-patches.sh').write_text(native_patch_script())
        npm_sha256 = hashlib.sha256((context/'harness/npm/package-lock.json').read_bytes()).hexdigest()
        records['resource_monitor'] = {'files': {str(path.relative_to(context/'sources/resource-monitor')):
            hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (context/'sources/resource-monitor').rglob('*') if path.is_file()}}
        native_patch_sha256 = {name: hashlib.sha256((context/'harness/npm/patches'/name).read_bytes()).hexdigest()
                               for _, name, _ in native_patch_specs()}
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
                              'working_tree_status':subprocess.check_output(
                                  ['git','status','--short','--untracked-files=all','--','.'],cwd=source,text=True),
                              'source_sha256':hashlib.sha256(json.dumps(braid_files,sort_keys=True).encode()).hexdigest()}
        created=False
        exported=False
        cleanup_errors=[]
        def write_source_metadata():
            (output/'runtime-source.json').write_text(json.dumps({'backend':backend,'platform':'linux-x86_64',
                'profile': profile,
                'sources':records,'npm_sha256':npm_sha256,'docker_endpoint':endpoint,
                'native_patch_sha256':native_patch_sha256,
                **native_baseline_manifest(output, context/'harness/npm')},indent=2)+'\n')
        try:
            subprocess.run(docker+['build','--platform','linux/amd64','--target','team' if braid_source else 'runtime',
                '--build-arg',f'BACKEND={backend}','--build-arg',f'RUNTIME_PROFILE={profile}',
                '-t',name,str(context)],check=True,env=docker_env)
            confirm_docker(endpoint)
            subprocess.run(docker+['create','--name',name,name],check=True,env=docker_env);created=True
            output.parent.mkdir(parents=True,exist_ok=True)
            subprocess.run(docker+['cp',name+':/runtime',str(output)],check=True,env=docker_env)
            if backend == 'pi':
                require_pi_retry_source(output)
            write_source_metadata()
            exported=True
        finally:
            for action in (
                ('confirm-after-export', lambda: confirm_docker(endpoint)),
                ('remove-container', lambda: subprocess.run(docker+['rm',name],check=True,env=docker_env)) if created else None,
                ('remove-image', lambda: subprocess.run(docker+['image','rm','--no-prune',name],check=False,env=docker_env)),
            ):
                if action is None:
                    continue
                try:
                    action[1]()
                except Exception as error:
                    cleanup_errors.append({'action': action[0], 'error': f'{type(error).__name__}: {error}'})
        if exported and cleanup_errors:
            value=json.loads((output/'runtime-source.json').read_text())
            value['cleanup_errors']=cleanup_errors
            (output/'runtime-source.json').write_text(json.dumps(value,indent=2)+'\n')
    return output


def dev_svc(source):
    """Install the complete development CLI from an explicitly chosen checkout."""
    source = source.expanduser().resolve(strict=True)
    package = source/'cli'
    if not (package/'pyproject.toml').is_file():
        raise ValueError('开发 SVC 源码必须包含 cli/pyproject.toml；参赛 Corpus 树不能代替')
    python = ROOT/'.venv/bin/python'
    env = production_environment(ROOT/'runs/build-cache/dev-svc')
    if not python.exists():
        subprocess.run(['uv', 'venv', '--python', '3.13', str(ROOT/'.venv')], check=True, env=env)
    subprocess.run(['uv', 'pip', 'install', '--python', str(python),
                    '--reinstall-package', 'sustainable-vibe-coding', str(package)], check=True, env=env)
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
    output = workssd_path(output)
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
        ['uv', 'pip', 'freeze', '--python', str(launcher)], text=True, env=environment).splitlines())
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
    cache = workssd_path(cache_root)
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
    p.add_argument('command',choices=['path','prepare','linux','derive-linux','slim-linux','dev-svc','host-exp'])
    p.add_argument('--lock-dir',type=Path,default=ROOT/'materials/npm')
    p.add_argument('--output',type=Path)
    p.add_argument('--backend',choices=['pi','codex'],default='pi')
    p.add_argument('--docker-context')
    p.add_argument('--braid-source',type=Path,help='Optional team dependency; raw runtimes do not require Braid')
    p.add_argument('--base-package',type=Path,help='Retained immutable Linux package used by derive-linux')
    p.add_argument('--source',type=Path,help='Frozen runtime directory used by slim-linux')
    p.add_argument('--profile',default='arc-core',help='slim-linux profile')
    p.add_argument('--cache-root',type=Path,help='Explicit WorkSSD production cache')
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
    elif a.command=='derive-linux':
        if a.output is None or a.base_package is None or a.braid_source is None or a.cache_root is None:
            p.error('derive-linux requires --output/--base-package/--braid-source/--cache-root')
        result=derive_linux(a.output,a.base_package,a.braid_source,a.cache_root)
    elif a.command=='slim-linux':
        if a.output is None or a.source is None: p.error('slim-linux requires --output/--source')
        result=slim_linux(a.output,a.source,a.profile)
    else:
        if a.output is None: p.error('linux requires --output')
        result=linux(a.output,a.backend,a.lock_dir,a.docker_context,a.braid_source,a.profile)
    print(result)


if __name__=='__main__': main()
