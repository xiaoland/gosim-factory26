"""Package one independent Harness; runtime and skill inputs are explicit."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import zipfile

from agent_support import copy_skill

ROOT=Path(__file__).resolve().parents[1]

def is_metadata_path(path):
    """Exclude transport-created macOS metadata from runnable package payloads."""
    return any(part.startswith('._') or part in {'.DS_Store', '__MACOSX'}
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

def write_zip(bundle, output, backend, records, capabilities=None):
    bundle = bundle.resolve()
    files = [path for path in bundle_files(bundle)
             if path != bundle / 'package-manifest.json'
             and 'node_modules/.bin' not in path.relative_to(bundle).as_posix()]
    manifest = {'schema_version': 1, 'backend': backend, 'platform': 'linux-x86_64',
                'python': '3.12', 'sources': records, 'files': {}}
    if capabilities is not None:
        manifest['capabilities'] = capabilities
    for path in files:
        relative = path.relative_to(bundle).as_posix()
        manifest['files'][relative] = {'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                                       'executable': bool(path.stat().st_mode & 0o111)}
    (bundle / 'package-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    files.append(bundle / 'package-manifest.json')
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('xb') as stream:
        try:
            with zipfile.ZipFile(stream, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
                for path in files:
                    info = zipfile.ZipInfo(path.relative_to(bundle).as_posix())
                    info.create_system = 3
                    mode = 0o755 if path.stat().st_mode & 0o111 else 0o644
                    info.external_attr = (stat.S_IFREG | mode) << 16
                    info.compress_type = zipfile.ZIP_DEFLATED
                    archive.writestr(info, path.read_bytes())
        except BaseException:
            output.unlink()
            raise


def assemble(source, destination, runtime, skill_source, skills):
    """Copy selected files. This boundary does not parse profiles or choose behavior."""
    destination=Path(destination);destination.mkdir(parents=True)
    source=Path(source)
    for item in source.iterdir():
        if item.name in {'__pycache__','variant.json','build.py'}: continue
        if item.is_dir(): shutil.copytree(item,destination/item.name)
        else: shutil.copy2(item,destination/item.name)
    support=destination/'support';support.mkdir()
    for name in ('agent_support.py','braid_runtime.py','core.py','model_budget.mjs'):
        shutil.copy2(ROOT/'scripts'/name,support/name)
    if source.name in {'pi-braid', 'pi-braid-flash-team', 'pi-braid-kimi-root'}:
        shutil.copy2(ROOT/'lab/otlp.py',support/'otlp.py')
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--quiet', '--no-compile',
                        '--target', str(support/'otlp-deps'), '-r', str(ROOT/'lab/requirements.txt')],
                       check=True)
        for binary in (support/'otlp-deps').rglob('*.so'):
            binary.unlink()  # protobuf's pure Python implementation works across build/target hosts.
    for name in skills:
        copy_skill(Path(skill_source)/name,destination/'skills'/name)
    shutil.copytree(runtime,destination/'runtime',symlinks=True)
    return destination


def package(variant, output, docker_context=None, runtime=None, stage=None,
            skill_source=None):
    source=ROOT/'variants'/variant
    if source.parent!=ROOT/'variants' or not (source/'build.py').is_file():
        raise ValueError('请选择含 build.py 的独立 variant')
    if output is not None and Path(output).exists(): raise FileExistsError(output)
    skill_source=Path(skill_source or ROOT/'harness/skills').resolve()
    from runtime import linux
    (ROOT/'runs').mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='package-',dir=ROOT/'runs') as temporary:
        tmp=Path(temporary)
        if runtime is None:
            runtime=linux(tmp/'runtime','pi',ROOT/'harness/npm',docker_context,ROOT/'sources/braid')
        runtime=Path(runtime).resolve(strict=True)
        if not (runtime/'bin/braid').is_file():
            raise ValueError('团队制品需要包含 Braid 的 Linux runtime；参阅 runtime.py linux --braid-source')
        bundle=Path(stage).resolve() if stage else tmp/'bundle'
        subprocess.run([sys.executable,str(source/'build.py'),'--stage',str(bundle),
                        '--runtime',str(runtime),'--skills',str(skill_source)],check=True)
        prune_metadata(bundle)
        records=json.loads((runtime/'runtime-source.json').read_text()).get('sources',{}) if (runtime/'runtime-source.json').is_file() else {}
        if output is not None:
            write_zip(bundle,Path(output).resolve(),'pi',records,{'variant':variant})
        elif stage is None:
            raise ValueError('需要 --output 或 --stage')
    return Path(output or stage).resolve()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--variant',required=True)
    p.add_argument('--output',type=Path)
    p.add_argument('--stage',type=Path,help='准备可直接执行的目录，不压 ZIP')
    p.add_argument('--runtime',type=Path,help='复用 runtime.py linux 导出的目录')
    p.add_argument('--docker-context')
    p.add_argument('--skills',type=Path)
    a=p.parse_args()
    if a.output is None and a.stage is None:p.error('需要 --output 或 --stage')
    print(package(a.variant,a.output,a.docker_context,a.runtime,a.stage,a.skills))


if __name__=='__main__':main()
