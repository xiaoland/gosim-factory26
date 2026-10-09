"""基于已冻结的完整自费基线包，生成本 variant 的窄 overlay。"""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import tarfile
import zipfile
import io
import sys
import tempfile
import shutil

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tooling/scripts"))
from runtime import native_patch_specs, require_native_baseline
from agent_support import copy_skill
from pi_extensions import extension_sources, extension_identity

HERE = Path(__file__).resolve().parent
VARIANT = 'pi-braid-i15-reviewer-cleaner-e2e'
BASE_SHA256 = 'e9f7b7d2a7ad88728dcf5c589db552dd1dde1731055d10563d161baf7b8733f5'

def shared_skill_files(skills_root, destination):
    """Materialize the current shared library using its published resource boundary."""
    for source in sorted(skills_root.iterdir()):
        if source.is_dir() and (source/'SKILL.md').is_file():
            copy_skill(source, destination/source.name)
    return {'skills/'+path.relative_to(destination).as_posix(): path
            for path in sorted(destination.rglob('*')) if path.is_file()}

def public_material(runtime, skills, directory):
    """Consume public producer components without the historical base package."""
    from tooling.scripts.package_agent import produce, gateway_sources
    repository = HERE.parents[1]
    material = produce(HERE.name, repository/'runs/material-cache', runtime,
                       skill_source=skills)
    directory.mkdir(parents=True, exist_ok=False)
    shutil.copytree(material['components']['agent']['root'], directory, dirs_exist_ok=True)
    shutil.copytree(material['components']['support']['root'], directory/'support')
    shutil.copy2(HERE/'submission-models.json', directory/'submission-models.json')
    for name, source in gateway_sources().items():
        shutil.copy2(source, directory/'support'/name)
    shared_skill_files(skills, directory/'skills')
    if (HERE/'skills').is_dir():
        shutil.copytree(HERE/'skills', directory/'skills', dirs_exist_ok=True)
    (directory/'package-manifest.json').write_text(json.dumps({
        'schema_version': 1, 'backend': 'pi', 'platform': 'linux-x86_64',
        'sources': {'material': material['dependencies']},
        'capabilities': {'material_id': material['material_id']}
    }, ensure_ascii=False, indent=2)+'\n')


def main():
    if '--variant-only' in sys.argv:
        parser = argparse.ArgumentParser(description='当前公共组件的I15材料')
        parser.add_argument('--runtime', type=Path, required=True)
        parser.add_argument('--skills', type=Path, required=True)
        parser.add_argument('--directory', type=Path, required=True)
        parser.add_argument('--variant-only', action='store_true', required=True)
        args = parser.parse_args()
        public_material(args.runtime.resolve(strict=True), args.skills.resolve(strict=True),
                        args.directory.resolve())
        return
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-zip', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--braid-binary', type=Path, required=True)
    parser.add_argument('--braid-build-receipt', type=Path, required=True)
    parser.add_argument('--protocol-runtime', type=Path, required=True)
    parser.add_argument('--resource-helper', type=Path, default=HERE.parents[1]/'tooling/scripts/runtime_resources.py')
    parser.add_argument('--skills-root', type=Path, default=HERE.parents[1]/'materials/skills')
    parser.add_argument('--agent-support-source', type=Path, default=HERE.parents[1]/'tooling/scripts/agent_support.py')
    args = parser.parse_args()
    base = args.base_zip.resolve(strict=True)
    braid_binary = args.braid_binary.resolve(strict=True)
    braid = braid_binary.read_bytes()
    # This package executes on Linux x86_64; a Mac build cannot supply its runtime.
    if braid[:6] != b'\x7fELF\x02\x01' or int.from_bytes(braid[18:20], 'little') != 62:
        raise ValueError('Braid必须是Linux x86_64 ELF64二进制')
    braid_sha = hashlib.sha256(braid).hexdigest()
    build_receipt_path = args.braid_build_receipt.resolve(strict=True)
    build_receipt = json.loads(build_receipt_path.read_text())
    if (build_receipt.get('braid_binary_sha256') != braid_sha
            or not build_receipt.get('source_identity')
            or 'linux' not in build_receipt.get('target', '')
            or 'x86_64' not in build_receipt.get('target', '')):
        raise ValueError('编译receipt须绑定实际binary SHA、Linux target与source identity')
    protocol = args.protocol_runtime.resolve(strict=True)
    protocol_baseline = require_native_baseline(protocol)
    helper = args.resource_helper.resolve(strict=True)
    support_source = args.agent_support_source.resolve(strict=True)
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
    with zipfile.ZipFile(base) as archive, tempfile.TemporaryDirectory(prefix='i15-skills-', dir=output) as staged:
        manifest = json.loads(archive.read('package-manifest.json'))
        base_runtime_source = json.loads(archive.read('runtime/runtime-source.json'))
        if base_runtime_source.get('npm_sha256') != protocol_baseline['npm_sha256']:
            raise ValueError('Pi baseline npm lock differs from retained dependency tree; rebuild the complete runtime before overlaying shared targets')
        required = ['.private/provider-env.json', 'support/standalone_model_gateway.py',
                    'runtime/bin/factory26-model-proxy', 'runtime/native-managed.mjs',
                    'runtime/e2e/node_modules/e2e/dist/cli/bin.js', 'skills/e2e/SKILL.md']
        for name in required:
            if name not in manifest['files']:
                raise ValueError(f'完整基线缺少必需成员：{name}')
        old_braid = manifest['files']['runtime/bin/braid']
        if old_braid['sha256'] == braid_sha:
            raise ValueError('必须替换底包旧Braid，不能仅叠加I15提示词')
        members = {}
        for name in ('main.py', 'run.py', 'README.md', 'requirements.txt', 'materials.json'):
            members[name] = (HERE/name).read_bytes()
        for folder in ('agents', 'tools'):
            for path in sorted((HERE/folder).rglob('*')):
                if path.is_file():
                    members[path.relative_to(HERE).as_posix()] = path.read_bytes()
        extension_record = extension_identity(VARIANT)
        for name, path in extension_sources(VARIANT).items():
            members['extensions/'+name] = path.read_bytes()
        if extension_identity(VARIANT) != extension_record:
            raise ValueError('Pi extension source changed during overlay selection')
        skills_root = args.skills_root.resolve(strict=True)
        skill_members = shared_skill_files(skills_root, Path(staged))
        variant_skill_members = {path.relative_to(HERE).as_posix(): path
                                 for path in sorted((HERE/'skills').rglob('*')) if path.is_file()}
        # Shared source is the default; only explicit variant files override it.
        skill_members.update(variant_skill_members)
        for skill in json.loads(members['materials.json'])['skills']:
            if f'skills/{skill}/SKILL.md' not in skill_members:
                raise FileNotFoundError(f'已声明技能缺少当前共享源或variant覆盖：{skill}')
        for name, path in skill_members.items():
            members[name] = path.read_bytes()
        members['runtime/bin/braid'] = braid
        protocol_members = {
            'runtime/bin/pi': protocol/'bin/pi',
            'runtime/native-managed.mjs': protocol/'native-managed.mjs',
            'runtime/node_modules/pi-background-bash/bin/pbb.js': protocol/'node_modules/pi-background-bash/bin/pbb.js',
            'support/runtime_resources.py': helper,
            'runtime/runtime_resources.py': helper,
        }
        # Reuse the producer's complete patch target set; a hand-picked list can
        # silently leave retry, tools, subagents or PBB behavior in the frozen base.
        for package, _, relatives in native_patch_specs():
            for relative in relatives:
                path = protocol/'node_modules'/package/relative
                if not path.is_file():
                    raise FileNotFoundError(path)
                protocol_members['runtime/'+path.relative_to(protocol).as_posix()] = path
        for name, path in protocol_members.items():
            members[name] = path.read_bytes()
        assembled_source = dict(base_runtime_source)
        assembled_source.update(protocol_baseline)
        assembled_source['pi_execution_mode'] = 'managed'
        assembled_source['native_baseline_source'] = str(protocol/'runtime-source.json')
        members['runtime/runtime-source.json'] = (json.dumps(assembled_source, indent=2)+'\n').encode()
        # Replace only the ownership setup function; keep frozen gateway/telemetry behavior.
        current_support = support_source.read_text()
        node = next(n for n in ast.parse(current_support).body
                    if isinstance(n, ast.FunctionDef) and n.name == 'runtime_resource_environment')
        function = '\n'.join(current_support.splitlines()[node.lineno-1:node.end_lineno])
        frozen_support = archive.read('support/agent_support.py').decode()
        old_node = next(n for n in ast.parse(frozen_support).body
                       if isinstance(n, ast.FunctionDef) and n.name == node.name)
        lines = frozen_support.splitlines(keepends=True)
        patched_support = ''.join(lines[:old_node.lineno-1])+function+'\n'+''.join(lines[old_node.end_lineno:])
        ast.parse(patched_support)
        members['support/agent_support.py'] = patched_support.encode()
        records = {}
        changed = {}
        for name, data in members.items():
            if name in {'runtime/bin/braid', 'runtime/bin/pi'}:
                executable = True
            elif name == 'runtime/runtime-source.json':
                executable = False
            elif name == 'support/agent_support.py':
                executable = manifest['files'][name]['executable']
            else:
                executable = bool((skill_members.get(name) or protocol_members.get(name) or HERE/name).stat().st_mode & 0o111)
            record = {'sha256': hashlib.sha256(data).hexdigest(), 'executable': executable}
            records[name] = record
            if manifest['files'].get(name) != record:
                changed[name] = data
            manifest['files'][name] = record
        material = hashlib.sha256(json.dumps(records, sort_keys=True).encode()).hexdigest()
        capabilities = manifest['capabilities']
        capabilities['variant'] = HERE.name
        capabilities['material_id'] = 'manual-i15-reviewer-cleaner-e2e-' + material
        capabilities['manual_fresh'] = True
        capabilities['variants'] = [HERE.name]
        capabilities['mechanisms'] = {'reviewer': True, 'cleaner': True, 'e2e': True, 'single_reviewer_per_pr': True}
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
            'pi_extensions': {'files': extension_record,
                'selector_sha256': hashlib.sha256((HERE.parents[1]/'tooling/scripts/pi_extensions.py').read_bytes()).hexdigest()},
            'variant_files': records, 'overlay_members': sorted(changed), 'removed_members': [],
            'model_routes': json.loads(archive.read('support/gateway-routes.json')),
            'base_runtime_source': runtime,
            'pi_execution_mode': 'managed',
            'native_baseline': protocol_baseline,
            'braid_replacement': {'previous': old_braid, 'binary': str(braid_binary),
                'sha256': braid_sha, 'build_receipt': build_receipt,
                'build_receipt_path': str(build_receipt_path),
                'build_receipt_sha256': hashlib.sha256(build_receipt_path.read_bytes()).hexdigest()},
            'skills_overlay': {'source_root': str(skills_root),
                'variant_overrides': sorted(variant_skill_members),
                'files': {name: records[name] for name in skill_members}},
            'protocol_overlay': {'runtime': str(protocol),
                'runtime_source': protocol_source,
                'resource_helper': str(helper), 'agent_support_source': str(support_source),
                'agent_support_function_sha256': hashlib.sha256(function.encode()).hexdigest(),
                'files': {name: records[name] for name in [*protocol_members, 'support/agent_support.py']}},
            'retained_members': {name: manifest['files'][name] for name in [n for n in required if n not in protocol_members and n not in members] + [
                'runtime/node_modules/pi-subagents/src/runs/background/async-execution.ts',
                'support/model_budget.mjs', 'runtime/e2e/addon-source.json']},
            'braid_session_budget': capabilities['braid_session_budget'],
        }
        (output/'package-identity.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2)+'\n')
        print(json.dumps({key:receipt[key] for key in ['variant','overlay','overlay_bytes','overlay_sha256','material_id']},ensure_ascii=False))

if __name__ == '__main__':
    main()
