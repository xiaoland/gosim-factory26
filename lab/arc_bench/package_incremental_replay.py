"""Package only changed files from a frozen application and its official baseline."""

import argparse
import hashlib
import json
from pathlib import Path
import stat
from zipfile import ZipFile, ZIP_DEFLATED


# Generated application API tests isolate temporary SQLite databases here.
# Retain the delivery database; do not replay test databases or their journals.
EXCLUDED = {'.git', '.arc', '.factory26', 'node_modules', '.cache', 'dist', '.arc-test-db'}


def inventory(root):
    result = {}
    for path in sorted(root.rglob('*')):
        relative = path.relative_to(root)
        if relative.parts[0] not in {'frontend', 'backend'} and relative.as_posix() != 'README.md':
            continue
        if set(relative.parts) & EXCLUDED or path.name in {'.env', '.env.local', '.env.production'}:
            continue
        if path.suffix in {'.pyc', '.pyo', '.tsbuildinfo', '.log'}:
            continue
        if path.is_symlink():
            raise ValueError(f'application symlink not supported: {relative}')
        if path.is_file():
            with path.open('rb') as stream:
                sha = hashlib.file_digest(stream, 'sha256').hexdigest()
            result[relative.as_posix()] = {'sha256': sha, 'mode': stat.S_IMODE(path.stat().st_mode)}
    for part in ('frontend', 'backend'):
        if f'{part}/package.json' not in result:
            raise ValueError(f'incomplete application: {part}/package.json')
    return result


def identity(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def package(baseline, application, requirements, output, source):
    before, after = inventory(baseline), inventory(application)
    changed = {name: value for name, value in after.items() if before.get(name) != value}
    with requirements.open('rb') as stream:
        requirement_sha = hashlib.file_digest(stream, 'sha256').hexdigest()
    manifest = {'schema_version': 1, 'source': source, 'requirements_sha256': requirement_sha,
                'baseline_sha256': identity(before), 'final_sha256': identity(after),
                'baseline': before, 'final': after, 'changed': changed,
                'added': sorted(set(after) - set(before)), 'deleted': sorted(set(before) - set(after))}
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('xb') as stream, ZipFile(stream, 'w', compression=ZIP_DEFLATED) as archive:
        archive.write(Path(__file__).with_name('incremental_replay.py'), 'main.py')
        archive.writestr('requirements.txt', '')
        archive.writestr('incremental-replay.json', json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
        for name in changed:
            archive.write(application / name, 'delta/' + name)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--application', type=Path, required=True)
    parser.add_argument('--requirements', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--source', type=Path, required=True, help='Frozen application provenance JSON')
    args = parser.parse_args()
    manifest = package(args.baseline.resolve(strict=True), args.application.resolve(strict=True),
                       args.requirements.resolve(strict=True), args.output.resolve(),
                       json.loads(args.source.read_text()))
    print(json.dumps({'package': str(args.output), 'changed': len(manifest['changed']),
                      'added': len(manifest['added']), 'deleted': len(manifest['deleted']),
                      'final_sha256': manifest['final_sha256']}))


if __name__ == '__main__':
    main()
