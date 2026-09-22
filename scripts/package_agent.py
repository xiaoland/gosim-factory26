"""从当前源码快照构建 Linux x86_64 离线参赛 Agent ZIP。"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import stat
import subprocess
import tempfile
import uuid
import zipfile

import sources
import profiles

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ('factory.py', 'core.py', 'braid_runtime.py', 'sources.py', 'profiles.py',
           'native_profiles.py', 'submission.py', 'linux_sandbox.py', 'responses_compat.py')


def source_input(name, relative):
    parts = Path(relative).parts
    if name == 'braid':
        return parts[0] in ('Cargo.toml', 'Cargo.lock', 'src', 'migrations', 'config.example.toml')
    return parts[0] == 'corpus' or (len(parts) > 1 and parts[0] == 'cli' and
            parts[1] in ('pyproject.toml', 'pdm_build.py', 'README.md', 'src'))


def prepare_context(context, records):
    for name, record in records.items():
        source = sources.checkout(name).resolve()
        for relative, digest in record['files'].items():
            if digest is None or not source_input(name, relative):
                continue
            path = source / relative
            if not path.resolve().is_relative_to(source):
                raise ValueError(f'源码链接越出仓库：{path}')
            data = path.read_bytes()
            if hashlib.sha256(data).hexdigest() != digest:
                raise RuntimeError(f'复制期间 {name} 源码发生变化：{relative}')
            target = context / 'sources' / name / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
    for name in ('Dockerfile', 'build.py'):
        shutil.copyfile(ROOT / 'submission' / name, context / name)
    shutil.copytree(ROOT / 'harness/npm', context / 'harness/npm')


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


def capability_manifest(effective, records):
    if effective['svc']['source_revision'] != records['svc']['revision']:
        raise RuntimeError('variant SVC revision differs from packaged source snapshot')
    return {'variant': effective['variant'], 'effective_digest': effective['effective_digest'],
            'materials': effective['materials']}


def package(variant, output, docker_context):
    output = output.resolve()
    if output.exists():
        raise FileExistsError(f'输出文件已存在：{output}')
    config = profiles.configuration(variant, root=ROOT)
    backend = config['backend']
    records = {name: sources.snapshot(name) for name in ('svc', 'braid')}
    capabilities = capability_manifest(config['effective'], records)
    identifier = 'factory26-package-' + uuid.uuid4().hex
    docker = ['docker'] + (['--context', docker_context] if docker_context else [])
    image = identifier + ':build'
    container_created = False
    with tempfile.TemporaryDirectory(prefix=identifier) as temporary:
        temp = Path(temporary)
        context = temp / 'context'; context.mkdir()
        bundle = temp / 'bundle'; bundle.mkdir()
        prepare_context(context, records)
        try:
            subprocess.run(docker + ['build', '--platform', 'linux/amd64', '--label',
                           f'factory26.package={identifier}', '--build-arg', f'BACKEND={backend}',
                           '-t', image, str(context)], check=True)
            subprocess.run(docker + ['create', '--name', identifier, '--label',
                           f'factory26.package={identifier}', image], check=True)
            container_created = True
            subprocess.run(docker + ['cp', f'{identifier}:/runtime', str(bundle / 'runtime')], check=True)
            for name in records:
                if sources.snapshot(name) != records[name]:
                    raise RuntimeError(f'打包期间 {name} 源码发生变化，请重试')
            shutil.copyfile(ROOT / 'submission/main.py', bundle / 'main.py')
            (bundle / 'requirements.txt').write_text('')
            (bundle / 'scripts').mkdir()
            for name in SCRIPTS:
                shutil.copyfile(ROOT / 'scripts' / name, bundle / 'scripts' / name)
            shutil.copytree(ROOT / 'harness', bundle / 'harness')
            shutil.copytree(ROOT / 'variants' / variant, bundle / 'variants' / variant)
            config.update(deployment='arcbench')
            (bundle / 'variants/factory').mkdir(parents=True)
            (bundle / 'variants/factory/config.json').write_text(json.dumps(config, indent=2) + '\n')
            write_zip(bundle, output, backend, records, capabilities)
        finally:
            if container_created:
                subprocess.run(docker + ['rm', identifier], check=False)
            subprocess.run(docker + ['image', 'rm', '--no-prune', image], check=False)
    print(output)


def main():
    parser = argparse.ArgumentParser(description=__doc__, add_help=False)
    parser.add_argument('-h', '--help', action='help', help='显示帮助并退出')
    parser.add_argument('--variant', required=True, help='选择要冻结的 capability variant')
    parser.add_argument('--output', required=True, type=Path, help='输出 ZIP 路径；拒绝覆盖现有文件')
    parser.add_argument('--docker-context', help='构建使用的 Docker context 名称')
    args = parser.parse_args()
    package(args.variant, args.output, args.docker_context)


if __name__ == '__main__':
    main()
