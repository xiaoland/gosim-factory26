"""Freeze the independent native Pi variant; no Braid or SVC materials."""
import argparse
import json
from pathlib import Path
import shutil
import sys
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from package_agent import write_zip
from agent_support import copy_skill

SKILLS = ('agent-browser', 'hyperformula', 'handsontable', 'better-auth-best-practices',
          'organization-best-practices', 'fixing-accessibility', 'ponytail')


def build(runtime, output):
    if (runtime/'bin/braid').exists():
        raise ValueError('pi-minimal requires a native Pi runtime without Braid')
    with tempfile.TemporaryDirectory(prefix='pi-minimal-', dir=ROOT/'runs') as temporary:
        stage = Path(temporary)
        for name in ('main.py', 'models.json', 'instructions.md', 'mcporter.json', 'requirements.txt'):
            shutil.copy2(HERE/name, stage/name)
        for folder in ('agents', 'extensions', 'vendor'):
            shutil.copytree(HERE/folder, stage/folder)
        shutil.copy2(ROOT/'scripts/agent_support.py', stage/'agent_support.py')
        shutil.copy2(ROOT/'variants/raw/raw_otlp.py', stage/'raw_otlp.py')
        for name in SKILLS:
            source = (HERE/'vendor/ponytail/skills/ponytail' if name == 'ponytail'
                      else ROOT/'harness/skills'/name)
            copy_skill(source, stage/'skills'/name)
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
        browser_guide = stage/'skills/agent-browser/SKILL.md'
        browser_guide.write_text(browser_guide.read_text().replace(
            'Use svc-verification’s result interpretation to judge coverage and applicability to another candidate; ',
            ''))
        shutil.copytree(runtime, stage/'runtime', symlinks=True)
        executables = [str(path.relative_to(stage)) for path in (stage/'runtime').rglob('*')
                       if path.is_file() and path.stat().st_mode & 0o111
                       and 'node_modules/.bin' not in str(path.relative_to(stage))]
        (stage/'runtime-executables.json').write_text(json.dumps(executables)+'\n')
        source = json.loads((runtime/'runtime-source.json').read_text())
        write_zip(stage, output, 'pi', source, {'variant': 'pi-minimal'})


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--runtime', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    build(a.runtime.resolve(strict=True), a.output.resolve())
