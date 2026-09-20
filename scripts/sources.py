"""Build the two editable upstream repositories; archive the actual inputs per run."""
import hashlib
import json
from pathlib import Path
import subprocess
import tarfile


ROOT = Path(__file__).resolve().parents[1]


def checkout(name):
    if name not in ('svc', 'braid'):
        raise ValueError('unknown source repository')
    return ROOT / 'sources' / name


def snapshot(name):
    source = checkout(name)
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=source, text=True).strip()
    names = subprocess.check_output(
        ['git', 'ls-files', '-z', '--cached', '--others', '--exclude-standard'], cwd=source
    ).decode().split('\0')
    files = {name: hashlib.sha256((source / name).read_bytes()).hexdigest()
             if (source / name).is_file() else None for name in sorted(set(names)) if name}
    return {'revision': revision, 'files': files}


def binary():
    return checkout('braid') / 'target/debug/braid'


def artifact_hashes(name):
    if name == 'braid':
        return {'braid': hashlib.sha256(binary().read_bytes()).hexdigest()}
    package = next((ROOT / '.venv/lib').glob('python*/site-packages/svc_cli'))
    return {str(path.relative_to(package)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(package.rglob('*')) if path.is_file() and '__pycache__' not in path.parts}


def build(name):
    source = checkout(name)
    if not source.exists():
        source.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(['git', 'clone', '--branch', 'main',
                        f'https://github.com/xiaoland/{name}.git', str(source)], check=True)
    before = snapshot(name)
    stamp = ROOT / '.bootstrap' / f'{name}-build.json'
    stamp.parent.mkdir(exist_ok=True)
    artifact = binary() if name == 'braid' else ROOT / '.venv/bin/svc'
    if stamp.exists() and artifact.exists():
        recorded = json.loads(stamp.read_text())
        if recorded['source'] == before and recorded['artifacts'] == artifact_hashes(name):
            print(f'[缓存] {name} source build', flush=True)
            return
    if name == 'braid':
        subprocess.run(['cargo', 'build', '--locked'], cwd=source, check=True)
    else:
        if not (ROOT / '.venv/bin/python').exists():
            subprocess.run(['uv', 'venv', str(ROOT / '.venv')], check=True)
        subprocess.run(['uv', 'pip', 'install', '--python', str(ROOT / '.venv/bin/python'),
                        '--reinstall-package', 'sustainable-vibe-coding', str(source / 'cli')], check=True)
    if snapshot(name) != before:
        raise RuntimeError(f'{name} source changed during build; rebuild before running')
    record = {'source': before, 'artifacts': artifact_hashes(name)}
    stamp.write_text(json.dumps(record, indent=2) + '\n')


def require_build(name):
    stamp = ROOT / '.bootstrap' / f'{name}-build.json'
    if not stamp.exists():
        raise RuntimeError(f'{name} has no recorded build; run bootstrap')
    record = json.loads(stamp.read_text())
    if record['source'] != snapshot(name):
        raise RuntimeError(f'{name} source changed; run bootstrap before generation')
    if record['artifacts'] != artifact_hashes(name):
        raise RuntimeError(f'{name} installation differs from recorded build; run bootstrap')
    return record


def archive(name, output):
    record = require_build(name)
    output.mkdir(exist_ok=True)
    (output / f'{name}.json').write_text(json.dumps(record, indent=2) + '\n')
    # A complete source snapshot also preserves uncommitted and untracked edits.
    with tarfile.open(output / f'{name}.tar.gz', 'w:gz') as bundle:
        for path, digest in record['source']['files'].items():
            if digest is not None:
                bundle.add(checkout(name) / path, arcname=path, recursive=False)
    if snapshot(name) != record['source']:
        raise RuntimeError(f'{name} changed while archiving')
    return record
