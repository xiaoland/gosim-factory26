"""Freeze the independent native Pi variant with explicitly selected skills."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
VARIANT = 'pi-minimal-vv'
sys.path.insert(0, str(ROOT/'tooling/scripts'))
from package_agent import write_zip, write_tool_credentials, require_private_artifact
from agent_support import copy_skill
from runtime import require_native_baseline
from e2e_runtime import copy_e2e_addon
from task_context import bind_packaged_task_context
from pi_extensions import copy_extensions, extension_identity

SKILLS = ('svc-task-packet', 'svc-specs', 'svc-verification', 'e2e', 'agent-browser', 'hyperformula', 'handsontable', 'better-auth-best-practices',
          'organization-best-practices', 'fixing-accessibility')


def bind_evaluation_entry(stage):
    # Wrap after task-context binding, including early module/parser failures.
    (stage/'main.py').rename(stage/'harness-entry.py')
    shutil.copy2(HERE/'evaluation-entry.py', stage/'main.py')
    return {'exit_code': 0,
            'source_sha256': hashlib.sha256((HERE/'evaluation-entry.py').read_bytes()).hexdigest(),
            'generation_status': 'native result and entry-outcome.json; process exit is not generation success'}


def build(runtime, output, task_context_config=None, task=None, e2e_runtime=None, tool_env=None):
    if (runtime/'bin/braid').exists():
        raise ValueError('pi-minimal requires a native Pi runtime without Braid')
    if not (runtime/'bin/fd').is_file() or not (runtime/'bin/fd').stat().st_mode & 0o111:
        raise ValueError('pi-minimal-vv offline native find requires runtime/bin/fd')
    baseline = require_native_baseline(runtime)
    for member, version in (('@ff-labs/pi-fff', '0.11.0'), ('@upstash/context7-pi', '0.1.2')):
        package = runtime/'node_modules'/member/'package.json'
        if json.loads(package.read_text()).get('version') != version:
            raise ValueError(f'Native plugin differs from the shared lock: {member}')
    if tool_env is not None:
        require_private_artifact(output)
    with tempfile.TemporaryDirectory(prefix='pi-minimal-', dir=ROOT/'runs') as temporary:
        stage = Path(temporary)
        for name in ('main.py', 'models.json', 'instructions.md', 'mcporter.json', 'requirements.txt'):
            shutil.copy2(HERE/name, stage/name)
        for folder in ('agents', 'tools'):
            shutil.copytree(HERE/folder, stage/folder)
        extension_record = copy_extensions(VARIANT, stage/'extensions')
        shutil.copy2(ROOT/'materials/e2e/owned-client.mjs', stage/'tools/owned-e2e.mjs')
        shutil.copy2(ROOT/'tooling/scripts/agent_support.py', stage/'agent_support.py')
        shutil.copy2(ROOT/'tooling/scripts/resource_monitor.py', stage/'resource_monitor.py')
        shutil.copy2(ROOT/'tooling/scripts/e2e_runtime.py', stage/'e2e_runtime.py')
        shutil.copy2(ROOT/'variants/raw/raw_otlp.py', stage/'raw_otlp.py')
        for name in SKILLS:
            source = ROOT/'materials/skills'/name
            copy_skill(source, stage/'skills'/name)
        copy_skill(runtime/'node_modules/@upstash/context7-pi/skills/context7-docs',
                   stage/'skills/context7-docs')
        if tool_env is not None:
            write_tool_credentials(tool_env, stage)
        # Package the independent E2E project setup guide.
        shutil.copy2(ROOT/'variants/pi-minimal-vv/skills/e2e/references/runtime-setup.md',
                     stage/'skills/e2e/references/runtime-setup.md')
        descriptions = {
            'better-auth-best-practices': 'Use when designing account registration, login, password recovery, or persistent sessions; evaluate existing authentication support before choosing a library or implementing it yourself.',
            'organization-best-practices': 'Use when designing organizations, teams, invitations, membership, or permissions; compare the product requirements with existing support before implementing your own.',
        }
        for name, description in descriptions.items():
            guide = stage/'skills'/name/'SKILL.md'
            lines = guide.read_text().splitlines()
            index = next(i for i, line in enumerate(lines) if line.startswith('description:'))
            lines[index] = 'description: ' + description
            guide.write_text('\n'.join(lines) + '\n')
        addon = e2e_runtime or runtime/'e2e'
        # Validate before copying the base; missing E2E is a packaging failure, not an Agent task.
        from e2e_runtime import require_e2e_addon
        require_e2e_addon(addon)
        shutil.copytree(runtime, stage/'runtime', symlinks=True)
        e2e_record = copy_e2e_addon(addon, stage/'runtime/e2e')
        metadata = stage/'runtime/runtime-source.json'
        source = json.loads(metadata.read_text())
        source.update(baseline)
        source['pi_execution_mode'] = 'standalone'
        source['pi_extensions'] = {'files': extension_record,
            'selector_sha256': hashlib.sha256((ROOT/'tooling/scripts/pi_extensions.py').read_bytes()).hexdigest()}
        if extension_identity(VARIANT) != extension_record:
            raise ValueError('Pi extension source changed during package construction')
        source['e2e_addon'] = e2e_record
        source.pop('pi_minimal_vv_error_exit', None)
        metadata.write_text(json.dumps(source, indent=2)+'\n')
        executables = [str(path.relative_to(stage)) for path in (stage/'runtime').rglob('*')
                       if path.is_file() and path.stat().st_mode & 0o111
                       and 'node_modules/.bin' not in str(path.relative_to(stage))]
        (stage/'runtime-executables.json').write_text(json.dumps(executables)+'\n')
        if task_context_config is not None:
            source['task_context'] = bind_packaged_task_context(stage, task_context_config, task)
        source['evaluation_entry'] = bind_evaluation_entry(stage)
        write_zip(stage, output, 'pi', source, {'variant': 'pi-minimal-vv', 'e2e': True})


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--runtime', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--e2e-runtime', type=Path, help='Locked Linux E2E addon; required unless runtime/e2e is complete')
    p.add_argument('--tool-env', type=Path, help='Explicit private two-key dotenv input; never a Git artifact')
    p.add_argument('--task-context-config', type=Path)
    p.add_argument('--task')
    a = p.parse_args()
    build(a.runtime.resolve(strict=True), a.output.resolve(), a.task_context_config, a.task, a.e2e_runtime, a.tool_env)
