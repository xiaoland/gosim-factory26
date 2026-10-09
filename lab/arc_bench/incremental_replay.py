"""Apply a frozen application delta to an injected ARC baseline."""

import argparse
import hashlib
import json
from pathlib import Path
import shutil


def file_hash(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def target(root, relative):
    path = root / relative
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError(f'replay path escapes output: {relative}')
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('requirements', type=Path)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    package = Path(__file__).resolve().parent
    manifest = json.loads((package / 'incremental-replay.json').read_text())
    if file_hash(args.requirements / 'requirements.yaml') != manifest['requirements_sha256']:
        raise ValueError('requirements do not match frozen application')
    output = args.output_dir.resolve(strict=True)
    for relative, expected in manifest['baseline'].items():
        path = target(output, relative)
        if not path.is_file() or file_hash(path) != expected['sha256']:
            raise ValueError(f'injected baseline differs: {relative}')
    for relative in manifest['added']:
        if target(output, relative).exists():
            raise ValueError(f'new application path already exists: {relative}')
    for relative, expected in manifest['changed'].items():
        if file_hash(target(package / 'delta', relative)) != expected['sha256']:
            raise ValueError(f'packaged delta differs: {relative}')
    for relative in manifest['deleted']:
        target(output, relative).unlink()
    for relative, expected in manifest['changed'].items():
        path = target(output, relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(target(package / 'delta', relative), path)
        path.chmod(expected['mode'])
    for relative, expected in manifest['final'].items():
        if file_hash(target(output, relative)) != expected['sha256']:
            raise ValueError(f'delivered application differs: {relative}')
    receipt = output / '.arc' / 'incremental-replay.json'
    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text(json.dumps({key: manifest[key] for key in (
        'source', 'requirements_sha256', 'baseline_sha256', 'final_sha256',
        'added', 'deleted')}, ensure_ascii=False, indent=2) + '\n')
    print(f"Delivered incremental replay {manifest['final_sha256']}; no model calls", flush=True)


if __name__ == '__main__':
    main()
