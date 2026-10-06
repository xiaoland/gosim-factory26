"""Build a self-contained I14 ARC payload without the legacy delivery gate."""
import argparse
import json
import shutil
import subprocess
import tarfile
import tempfile
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from agent_support import copy_skill
from package_agent import write_zip

SKILLS = ('svc-sub-agents', 'svc-task-packet', 'svc-documentation', 'svc-verification',
          'hyperformula', 'handsontable', 'better-auth-best-practices',
          'organization-best-practices', 'fixing-accessibility', 'ponytail',
          'impeccable', 'agent-browser', 'context7-docs', 'braid-collaboration', 'arc-bench')
SUPPORT = ('agent_support.py', 'braid_runtime.py', 'core.py', 'state_writer.py',
           'model_budget.mjs', 'runtime_resources.py')
CONFIGURED_OTLP_DEPS = ROOT / 'runs/deadline-20261003/local-five/overlays/common/support/otlp-deps'


def _otlp_source(runtime: Path) -> Path:
    """Use only the executor-provided sibling bundle or the configured local bundle."""
    sibling = runtime.parent / 'otlp-deps'
    if sibling.is_dir():
        return sibling
    if CONFIGURED_OTLP_DEPS.is_dir():
        return CONFIGURED_OTLP_DEPS
    raise FileNotFoundError(
        f'OTLP dependency bundle missing beside runtime and at configured path: {sibling}; {CONFIGURED_OTLP_DEPS}')


def _seed_archive(source: Path, destination: Path) -> None:
    source = source.resolve(strict=True)
    roots = [('workspace', source / 'workspace'), ('harness', source / 'harness')]
    if (source / 'data').is_dir():
        roots = [('workspace', source / 'data/workspace'), ('harness', source / 'data/harness')]
    with tarfile.open(destination, 'w') as archive:
        for name, path in roots:
            if not path.exists():
                continue
            archive.add(path, arcname=name, recursive=True,
                        filter=lambda info: None if info.name.rstrip('/').endswith(
                            'workspace/.factory26/data/harness') else info)


def _shared_materials(stage: Path, runtime: Path) -> None:
    shutil.copy2(ROOT / 'lab/arc_bench/harness_services.py', stage / 'harness_services.py')
    shutil.copy2(ROOT / 'lab/otlp.py', stage / 'lab_otlp.py')
    shutil.copytree(_otlp_source(runtime), stage / 'otlp-deps', symlinks=True)
    subprocess.run([sys.executable, '-B', '-m', 'lab.arc_bench', 'runtime', 'export',
                    '--output', str(stage / 'arc-runtime.pyz')], cwd=ROOT, check=True)


def build(runtime: Path, output: Path, skills: Path, route: Path | None = None,
          run_config: Path | None = None, seed_data: Path | None = None) -> None:
    runtime = runtime.resolve(strict=True)
    skills = skills.resolve(strict=True)
    output = output.resolve()
    with tempfile.TemporaryDirectory(prefix='I14-dx-test-', dir=ROOT / 'runs') as temporary:
        stage = Path(temporary)
        for item in HERE.iterdir():
            if item.name in {'__pycache__', 'build.py', 'materials.json'}:
                continue
            destination = stage / item.name
            shutil.copytree(item, destination, symlinks=True) if item.is_dir() else shutil.copy2(item, destination)
        for name in SUPPORT:
            shutil.copy2(ROOT / 'scripts' / name, stage / name)
        shutil.copy2(ROOT / 'variants/raw/raw_otlp.py', stage / 'raw_otlp.py')
        _shared_materials(stage, runtime)
        for name in SKILLS:
            source = (HERE / 'vendor/ponytail/skills/ponytail'
                      if name == 'ponytail' and (HERE / 'vendor/ponytail/skills/ponytail').is_dir()
                      else skills / name)
            copy_skill(source, stage / 'skills' / name)
        shutil.copytree(runtime, stage / 'runtime', symlinks=True)
        if route:
            shutil.copy2(route.resolve(strict=True), stage / 'gateway-routes.json')
        if run_config:
            (stage / 'inputs').mkdir()
            shutil.copy2(run_config.resolve(strict=True), stage / 'inputs/lab-run.json')
        if seed_data:
            (stage / 'inputs').mkdir(exist_ok=True)
            _seed_archive(seed_data, stage / 'inputs/seed-data.tar')
        executable_files = [str(path.relative_to(stage)) for path in stage.joinpath('runtime').rglob('*')
                            if path.is_file() and path.stat().st_mode & 0o111
                            and 'node_modules/.bin' not in str(path.relative_to(stage))]
        (stage / 'runtime-executables.json').write_text(json.dumps(executable_files) + '\n')
        source = json.loads((runtime / 'runtime-source.json').read_text())
        write_zip(stage, output, 'pi', source, {'variant': 'I14-dx-test', 'base_variant': 'pi-braid-i14'})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--skills', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--route', type=Path)
    parser.add_argument('--run-config', type=Path)
    parser.add_argument('--seed-data', type=Path)
    args = parser.parse_args()
    build(args.runtime, args.output, args.skills, args.route, args.run_config, args.seed_data)
