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
sys.path.insert(0, str(ROOT/'tooling/scripts'))
from package_agent import write_zip
from agent_support import copy_skill

SKILLS = ('svc-task-packet', 'svc-specs', 'svc-verification', 'e2e', 'agent-browser', 'hyperformula', 'handsontable', 'better-auth-best-practices',
          'organization-best-practices', 'fixing-accessibility', 'ponytail')


def build(runtime, output):
    if (runtime/'bin/braid').exists():
        raise ValueError('pi-minimal requires a native Pi runtime without Braid')
    if not (runtime/'bin/fd').is_file() or not (runtime/'bin/fd').stat().st_mode & 0o111:
        raise ValueError('pi-minimal-vv-tailwindcss offline native find requires runtime/bin/fd')
    with tempfile.TemporaryDirectory(prefix='pi-minimal-', dir=ROOT/'runs') as temporary:
        stage = Path(temporary)
        for name in ('main.py', 'models.json', 'instructions.md', 'mcporter.json', 'requirements.txt'):
            shutil.copy2(HERE/name, stage/name)
        for folder in ('agents', 'extensions', 'vendor', 'tools'):
            shutil.copytree(HERE/folder, stage/folder)
        shutil.copy2(ROOT/'tooling/scripts/agent_support.py', stage/'agent_support.py')
        shutil.copy2(ROOT/'variants/raw/raw_otlp.py', stage/'raw_otlp.py')
        for name in SKILLS:
            source = (HERE/'vendor/ponytail/skills/ponytail' if name == 'ponytail'
                      else ROOT/'materials/skills'/name)
            copy_skill(source, stage/'skills'/name)
        # Both native variants prepare the same independent e2e project.
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
        shutil.copytree(runtime, stage/'runtime', symlinks=True)
        # Error termination must reach native shutdown even with finite jobs pending.
        background = stage/'runtime/node_modules/pi-background-bash/extensions/background-bash.ts'
        text = background.read_text()
        guard = ('\t\tconst lastAssistant = [..._event.messages].reverse().find((message) => message.role === "assistant");\n'
                 '\t\tif (ctx.mode !== "tui" && lastAssistant?.role === "assistant" &&\n'
                 '\t\t\t(lastAssistant.stopReason === "error" || lastAssistant.stopReason === "aborted")) return;\n')
        shared_guard = ('\tpi.on("agent_end", async (event, ctx) => {\n'
                        '\t\tif (event.willRetry) return;\n'
                        '\t\tconst lastAssistant = [...event.messages].reverse().find((message) => message.role === "assistant");\n'
                        '\t\tif (lastAssistant?.stopReason === "error" || lastAssistant?.stopReason === "aborted") {\n')
        if shared_guard in text:
            boundary = 'shared terminal-result persistence; native shutdown retains abort+settle'
        else:
            boundary = 'legacy nonTUI error/aborted bypass; native shutdown retains abort+settle'
            if guard not in text:
                anchor = '\tpi.on("agent_end", async (_event, ctx) => {\n'
                if text.count(anchor) != 1:
                    raise ValueError('native background Bash error-exit boundary changed')
                background.write_text(text.replace(anchor, anchor + guard))
        metadata = stage/'runtime/runtime-source.json'
        source = json.loads(metadata.read_text())
        source['pi_minimal_vv_error_exit'] = {
            'member': str(background.relative_to(stage/'runtime')),
            'sha256': hashlib.sha256(background.read_bytes()).hexdigest(),
            'reason': boundary,
        }
        metadata.write_text(json.dumps(source, indent=2)+'\n')
        executables = [str(path.relative_to(stage)) for path in (stage/'runtime').rglob('*')
                       if path.is_file() and path.stat().st_mode & 0o111
                       and 'node_modules/.bin' not in str(path.relative_to(stage))]
        (stage/'runtime-executables.json').write_text(json.dumps(executables)+'\n')
        write_zip(stage, output, 'pi', source, {'variant': 'pi-minimal-vv-tailwindcss'})


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--runtime', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    build(a.runtime.resolve(strict=True), a.output.resolve())
