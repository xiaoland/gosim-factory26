"""基于已冻结的完整自费基线包，生成本 variant 的窄 overlay。"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tarfile
import zipfile
import io

HERE = Path(__file__).resolve().parent
BASE_SHA256 = 'e9f7b7d2a7ad88728dcf5c589db552dd1dde1731055d10563d161baf7b8733f5'

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-zip', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    base = args.base_zip.resolve(strict=True)
    output = args.output.resolve()
    if __import__('sys').platform == 'darwin':
        ssd = Path('/Volumes/WorkSSD').resolve(strict=True)
        if not output.is_relative_to(ssd):
            raise ValueError('Mac 产物必须位于 WorkSSD')
        output.mkdir(parents=True, exist_ok=True)
        if output.stat().st_dev != ssd.stat().st_dev:
            raise ValueError('输出实际文件系统不是 WorkSSD')
    else:
        output.mkdir(parents=True, exist_ok=True)
    hasher = hashlib.sha256()
    with base.open('rb') as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            hasher.update(chunk)
    if hasher.hexdigest() != BASE_SHA256:
        raise ValueError('底包不是冻结的完整 standalone 自费 baseline；不得使用 official 包或 stage 目录')
    with zipfile.ZipFile(base) as archive:
        manifest = json.loads(archive.read('package-manifest.json'))
        required = ['.private/provider-env.json', 'support/standalone_model_gateway.py',
                    'runtime/bin/factory26-model-proxy', 'runtime/native-managed.mjs',
                    'runtime/e2e/node_modules/e2e/dist/cli/bin.js', 'skills/e2e/SKILL.md']
        for name in required:
            if name not in manifest['files']:
                raise ValueError(f'完整基线缺少必需成员：{name}')
        members = {}
        for name in ('main.py', 'run.py', 'README.md', 'requirements.txt', 'materials.json'):
            members[name] = (HERE/name).read_bytes()
        for folder in ('agents', 'extensions', 'tools'):
            for path in sorted((HERE/folder).rglob('*')):
                if path.is_file():
                    members[path.relative_to(HERE).as_posix()] = path.read_bytes()
        records = {}
        changed = {}
        for name, data in members.items():
            record = {'sha256': hashlib.sha256(data).hexdigest(),
                      'executable': bool((HERE/name).stat().st_mode & 0o111)}
            records[name] = record
            if manifest['files'].get(name) != record:
                changed[name] = data
            manifest['files'][name] = record
        material = hashlib.sha256(json.dumps(records, sort_keys=True).encode()).hexdigest()
        capabilities = manifest['capabilities']
        capabilities['variant'] = HERE.name
        capabilities['material_id'] = 'manual-i14-reviewer-cleaner-e2e-' + material
        capabilities['manual_fresh'] = True
        capabilities['variants'] = [HERE.name]
        capabilities['mechanisms'] = {'reviewer': True, 'cleaner': True, 'e2e': True}
        changed['package-manifest.json'] = (json.dumps(manifest, ensure_ascii=False, indent=2)+'\n').encode()
        overlay = output/'overlay.tar'
        with tarfile.open(overlay, 'w') as delivery:
            for name, data in sorted(changed.items()):
                info = tarfile.TarInfo(name)
                info.size = len(data)
                info.mode = 0o755 if records.get(name, {}).get('executable') else 0o644
                delivery.addfile(info, io.BytesIO(data))
        runtime = json.loads(archive.read('runtime/runtime-source.json'))
        receipt = {
            'variant': HERE.name, 'credential_mode': 'self_funded',
            'base_zip': str(base), 'base_zip_sha256': BASE_SHA256, 'base_zip_bytes': base.stat().st_size,
            'overlay': str(overlay), 'overlay_bytes': overlay.stat().st_size,
            'overlay_sha256': hashlib.sha256(overlay.read_bytes()).hexdigest(),
            'material_id': capabilities['material_id'], 'fresh': True,
            'application_seed': False, 'prepared_state': False,
            'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=HERE, text=True).strip(),
            'variant_files': records, 'overlay_members': sorted(changed), 'removed_members': [],
            'model_routes': json.loads(archive.read('support/gateway-routes.json')),
            'runtime_source': runtime,
            'retained_members': {name: manifest['files'][name] for name in required + [
                'runtime/bin/braid', 'runtime/node_modules/pi-subagents/src/runs/background/async-execution.ts',
                'support/model_budget.mjs', 'runtime/e2e/addon-source.json']},
            'braid_session_budget': capabilities['braid_session_budget'],
        }
        (output/'package-identity.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2)+'\n')
        print(json.dumps({key:receipt[key] for key in ['variant','overlay','overlay_bytes','overlay_sha256','material_id']},ensure_ascii=False))

if __name__ == '__main__':
    main()
