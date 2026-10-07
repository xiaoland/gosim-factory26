"""Materialise only the Pi variant portion of a public ARC package."""
import argparse
import json
import shutil
import tempfile
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'tooling/scripts'))
from agent_support import copy_skill

SKILLS = ('svc-verification', 'agent-browser', 'hyperformula', 'handsontable',
          'better-auth-best-practices', 'organization-best-practices',
          'fixing-accessibility', 'ponytail')
SUPPORT = ('agent_support.py', 'runtime_resources.py', 'pi_state.py',
           'native_observation.py', 'braid_provider_evidence.py', 'pi_transport.py')


def build(runtime: Path, output: Path | None, skills: Path | None = None,
          route: Path | None = None, run_config: Path | None = None,
          seed_data: Path | None = None, directory: Path | None = None,
          otlp_deps: Path | None = None, catalog: Path | None = None,
          provider_env: Path | None = None, model_proxy: Path | None = None,
          variant_only: bool = False) -> None:
    if not variant_only:
        raise RuntimeError('DX builders only produce variant material; use Lab public assembly')
    runtime.resolve(strict=True)
    skills = (skills or ROOT / 'materials/skills').resolve(strict=True)
    if directory is None or output is not None:
        raise ValueError('variant material requires --directory and no --output')
    with tempfile.TemporaryDirectory(prefix='pi-minimal-vv-dx-test-', dir=ROOT / 'runs') as temporary:
        stage = Path(temporary)
        for item in HERE.iterdir():
            if item.name in {'__pycache__', 'build.py', 'materials.json'}:
                continue
            destination = stage / item.name
            shutil.copytree(item, destination, symlinks=True) if item.is_dir() else shutil.copy2(item, destination)
        for name in SUPPORT:
            shutil.copy2(ROOT / 'tooling/scripts' / name, stage / name)
        shutil.copy2(ROOT / 'variants/raw/raw_otlp.py', stage / 'raw_otlp.py')
        for name in SKILLS:
            source = (HERE / 'vendor/ponytail/skills/ponytail'
                      if name == 'ponytail' else skills / name)
            copy_skill(source.resolve(strict=True), stage / 'skills' / name)
        descriptions = {
            'better-auth-best-practices': 'Use when designing account registration, login, password recovery, or persistent sessions; evaluate existing authentication support before choosing a library or implementing it yourself.',
            'organization-best-practices': 'Use when designing organizations, teams, invitations, membership, or permissions; compare product requirements with existing support before implementing your own.',
        }
        for name, description in descriptions.items():
            guide = stage / 'skills' / name / 'SKILL.md'
            lines = guide.read_text().splitlines()
            index = next(i for i, line in enumerate(lines) if line.startswith('description:'))
            lines[index] = 'description: ' + description
            guide.write_text('\n'.join(lines) + '\n')
        models = json.loads((HERE / 'models.json').read_text())
        model = models['providers']['factory26']['models'][0]['id']
        (stage / 'submission-models.json').write_text(json.dumps(
            {'model': model, 'visual_model': model}) + '\n')
        shutil.copytree(stage, directory, symlinks=True, dirs_exist_ok=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--skills', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--directory', type=Path)
    parser.add_argument('--route', type=Path)
    parser.add_argument('--run-config', type=Path)
    parser.add_argument('--seed-data', type=Path)
    parser.add_argument('--otlp-deps', type=Path)
    parser.add_argument('--catalog', type=Path)
    parser.add_argument('--provider-env', type=Path)
    parser.add_argument('--model-proxy', type=Path)
    parser.add_argument('--variant-only', action='store_true')
    args = parser.parse_args()
    build(args.runtime, args.output, args.skills, args.route, args.run_config, args.seed_data,
          args.directory, args.otlp_deps, args.catalog, args.provider_env, args.model_proxy, args.variant_only)
