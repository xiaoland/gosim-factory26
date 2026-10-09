"""Build and export this variant's frozen Linux e2e addon."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from lab.docker_endpoint import freeze, environment, confirm
from tooling.scripts.runtime import production_environment, workssd_path


def derive(base, output, cache_root, profile):
    """Install locked Linux files and bind the inherited browser ABI closure."""
    base = Path(base).resolve(strict=True)
    output = workssd_path(output)
    env = production_environment(cache_root)
    output.mkdir(parents=True, exist_ok=True)
    for name in ('package.json', 'package-lock.json'):
        shutil.copy2(source/name, output/name)
    logs = Path(cache_root)/'logs'
    logs.mkdir(exist_ok=True)
    with (logs/'e2e-install.log').open('w') as log:
        subprocess.run(['npm', 'ci', '--ignore-scripts', '--os=linux', '--cpu=x64'], cwd=output,
                       env=env, check=True, stdout=log, stderr=subprocess.STDOUT)
        env.update(PLAYWRIGHT_BROWSERS_PATH=str(output/'browsers'),
                   PLAYWRIGHT_HOST_PLATFORM_OVERRIDE='debian12-x64')
        subprocess.run(['node', 'node_modules/playwright/cli.js', 'install', 'chromium'],
                       cwd=output, env=env, check=True, stdout=log, stderr=subprocess.STDOUT)
    # ELF parsing is a build-only dependency. Its output is the actual runtime
    # dependency closure, not a synthetic browser run on the Mac controller.
    tools = Path(cache_root)/'elf-tools'
    if not (tools/'elftools').is_dir():
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--no-compile', '--quiet',
                        '--target', str(tools), 'pyelftools==0.32'], check=True, env=env)
    sys.path.insert(0, str(tools))
    from elftools.elf.elffile import ELFFile
    from elftools.elf.gnuversions import GNUVerNeedSection, GNUVerDefSection
    library = output/'lib'
    shutil.copytree(base/'lib/chromium', library, dirs_exist_ok=True)
    executables = [*output.glob('browsers/chromium-*/*/chrome'),
                   *output.glob('browsers/chromium_headless_shell-*/*/chrome-headless-shell'),
                   *output.glob('browsers/chromium_headless_shell-*/*/headless_shell'),
                   *output.glob('node_modules/@esbuild/linux-x64/bin/esbuild')]
    if not any(file.name == 'chrome' for file in executables) or not any('shell' in file.name for file in executables):
        raise ValueError('locked Chrome and Headless Shell are both required')
    if not (output/'node_modules/@esbuild/linux-x64/bin/esbuild').is_file():
        raise ValueError('npm target installation omitted Linux esbuild')
    for file in (output/'browsers').rglob('*'):
        if file.is_file() and file not in executables:
            with file.open('rb') as stream:
                if stream.read(4) == b'\x7fELF':
                    executables.append(file)
    for file in executables:
        with file.open('rb') as stream:
            if stream.read(4) != b'\x7fELF':
                raise ValueError(f'non-Linux executable in addon: {file}')
    platform = re.compile(r'^(?:libc|libm|libpthread|librt|libdl|libresolv)\.so(?:\.|$)|^ld-linux')
    facts = {}
    for file in [*executables, *library.iterdir()]:
        with file.open('rb') as stream:
            elf = ELFFile(stream)
            if elf.get_machine_arch() != 'x64':
                raise ValueError(f'addon ELF target mismatch: {file}')
            dynamic = elf.get_section_by_name('.dynamic')
            needed = [tag.needed for tag in dynamic.iter_tags() if tag.entry.d_tag == 'DT_NEEDED'] if dynamic else []
            requirements, definitions = {}, set()
            for section in elf.iter_sections():
                if isinstance(section, GNUVerNeedSection):
                    for version, auxiliaries in section.iter_versions():
                        requirements[version.name] = [item.name for item in auxiliaries]
                elif isinstance(section, GNUVerDefSection):
                    for version, auxiliaries in section.iter_versions():
                        definitions.update(item.name for item in auxiliaries)
            stream.seek(0)
            content_hash = hashlib.file_digest(stream, 'sha256').hexdigest()
            facts[file.name] = {'path': str(file.relative_to(output)), 'needed': needed,
                                'requires': requirements, 'defines': sorted(definitions),
                                'sha256': content_hash}
    for name, fact in facts.items():
        for dependency in fact['needed']:
            if not platform.match(dependency) and dependency not in facts:
                raise ValueError(f'Linux browser closure missing {dependency}, required by {name}')
        for dependency, versions in fact['requires'].items():
            if platform.match(dependency):
                for version in versions:
                    if version.startswith('GLIBC_') and tuple(map(int, version.removeprefix('GLIBC_').split('.'))) > (2, 36):
                        raise ValueError(f'Linux browser requires {version} beyond Debian bookworm: {name}')
            else:
                missing = set(versions) - set(facts.get(dependency, {}).get('defines', []))
                if missing:
                    raise ValueError(f'Linux browser ABI missing {dependency} {sorted(missing)}, required by {name}')
    if profile == 'arc-core':
        shutil.rmtree(output/'browsers')
    (output/'addon-source.json').write_text(json.dumps({'platform': 'linux-x86_64', 'profile': profile,
        'inputs': inputs, 'producer': 'build-e2e.py --base-runtime',
        'base_runtime': str(base), 'base_source_sha256': hashlib.sha256((base/'runtime-source.json').read_bytes()).hexdigest(),
        'elf_dependency_closure': facts, 'native_execution': 'deferred-to-authorized-hosted-run'}, indent=2)+'\n')
    return output

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--docker-context')
parser.add_argument('--profile', choices=('full', 'arc-core'), default='full',
                    help='arc-core exports locked E2E dependencies without browser payloads')
parser.add_argument('--base-runtime', type=Path, help='Derive from retained Linux browser libraries without Docker')
parser.add_argument('--cache-root', type=Path, help='Explicit WorkSSD caches and temp for file derivation')
args = parser.parse_args()
output = workssd_path(args.output)
if output.exists() and (args.base_runtime is None or (output/'addon-source.json').exists()):
    raise FileExistsError(output)
source = Path(__file__).resolve().parent/'e2e'
inputs = {file.name: hashlib.sha256(file.read_bytes()).hexdigest()
          for file in source.iterdir() if file.is_file()}
if args.base_runtime is not None:
    if args.cache_root is None:
        parser.error('--base-runtime requires --cache-root')
    if output.exists() and (not (output/'package-lock.json').is_file() or
                            (output/'package-lock.json').read_bytes() != (source/'package-lock.json').read_bytes()):
        raise ValueError('partial addon does not match the selected frozen lock')
    print(derive(args.base_runtime, output, args.cache_root, args.profile))
    sys.exit(0)
endpoint = freeze(args.docker_context)
docker = endpoint['argv']
docker_env = environment(endpoint)
name = 'factory26-i14-e2e-'+uuid.uuid4().hex
created = False
try:
    subprocess.run(docker+['build', '--platform', 'linux/amd64', '--build-arg', 'E2E_PROFILE='+args.profile, '-t', name, str(source)], check=True, env=docker_env)
    confirm(endpoint)
    subprocess.run(docker+['create', '--name', name, name], check=True, env=docker_env)
    created = True
    output.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(docker+['cp', name+':/e2e', str(output)], check=True, env=docker_env)
finally:
    confirm(endpoint)
    if created:
        subprocess.run(docker+['rm', name], check=True, env=docker_env)
    subprocess.run(docker+['image', 'rm', '--no-prune', name], check=False, env=docker_env)
(output/'addon-source.json').write_text(json.dumps({
    'platform': 'linux-x86_64',
    'profile': args.profile,
    'docker_endpoint': endpoint,
    'inputs': inputs,
}, indent=2)+'\n')
from tooling.scripts.e2e_runtime import require_e2e_addon
require_e2e_addon(output)
print(output)
