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
SUPPORT = ('agent_support.py', 'braid_runtime.py', 'core.py',
           'model_budget.mjs', 'runtime_resources.py')
CONFIGURED_OTLP_DEPS = ROOT / 'runs/deadline-20261003/local-five/overlays/common/support/otlp-deps'
MODEL_PROXY_BUILD = ROOT / 'runs/provider-model-config-20261007/delivery/model-proxy-linux-x86_64'


def _otlp_source(runtime: Path, explicit: Path | None = None) -> Path:
    """Use only the executor-provided sibling bundle or the configured local bundle."""
    if explicit is not None:
        return explicit.resolve(strict=True)
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


def _shared_materials(stage: Path, runtime: Path, otlp_deps: Path | None = None,
                      model_proxy: Path | None = None) -> None:
    shutil.copy2(ROOT / 'lab/arc_bench/harness_services.py', stage / 'harness_services.py')
    shutil.copy2(ROOT / 'lab/otlp.py', stage / 'lab_otlp.py')
    shutil.copytree(_otlp_source(runtime, otlp_deps), stage / 'otlp-deps', symlinks=True)
    if model_proxy is not None:
        proxy = model_proxy.resolve(strict=True)
        if not proxy.stat().st_mode & 0o111:
            raise PermissionError(f'model proxy is not executable: {proxy}')
        (stage / 'model-proxy').mkdir()
        shutil.copy2(proxy, stage / 'model-proxy/factory26-model-proxy')
        (stage / 'model-proxy/factory26-model-proxy').chmod(0o755)
        shutil.copy2(ROOT / 'sources/model-proxy/prepare.py', stage / 'model_proxy_prepare.py')
    subprocess.run([sys.executable, '-B', '-m', 'lab.arc_bench', 'runtime', 'export',
                    '--output', str(stage / 'arc-runtime.pyz')], cwd=ROOT, check=True)


def build(runtime: Path, output: Path | None, skills: Path, route: Path | None = None,
          run_config: Path | None = None, seed_data: Path | None = None,
          directory: Path | None = None, otlp_deps: Path | None = None,
          catalog: Path | None = None, provider_env: Path | None = None,
          model_proxy: Path | None = None) -> None:
    runtime = runtime.resolve(strict=True)
    skills = skills.resolve(strict=True)
    if output is None and directory is None:
        raise ValueError('one of output or directory is required')
    if output is not None and directory is not None:
        raise ValueError('output and directory are mutually exclusive')
    output = output.resolve() if output is not None else None
    directory = directory.resolve() if directory is not None else None
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
        selected_proxy = ((model_proxy or MODEL_PROXY_BUILD).resolve(strict=True)
                          if catalog is not None else None)
        _shared_materials(stage, runtime, otlp_deps, selected_proxy)
        for name in SKILLS:
            source = (HERE / 'vendor/ponytail/skills/ponytail'
                      if name == 'ponytail' and (HERE / 'vendor/ponytail/skills/ponytail').is_dir()
                      else skills / name)
            copy_skill(source, stage / 'skills' / name)
        if directory is None:
            shutil.copytree(runtime, stage / 'runtime', symlinks=True)
        if route:
            shutil.copy2(route.resolve(strict=True), stage / 'gateway-routes.json')
            (stage / 'inputs').mkdir(exist_ok=True)
            shutil.copy2(route.resolve(strict=True), stage / 'inputs/gateway-routes.json')
        if catalog:
            (stage / 'inputs').mkdir(exist_ok=True)
            shutil.copy2(catalog.resolve(strict=True), stage / 'inputs/model-gateway.json')
        if provider_env:
            private = stage / '.private'
            private.mkdir(mode=0o700, exist_ok=True)
            private.chmod(0o700)
            target = private / 'provider-env.json'
            shutil.copy2(provider_env.resolve(strict=True), target)
            target.chmod(0o600)
        if run_config:
            (stage / 'inputs').mkdir(exist_ok=True)
            shutil.copy2(run_config.resolve(strict=True), stage / 'inputs/lab-run.json')
        if seed_data:
            (stage / 'inputs').mkdir(exist_ok=True)
            _seed_archive(seed_data, stage / 'inputs/seed-data.tar')
        executable_files = [
            'runtime/' + str(path.relative_to(runtime))
            for path in runtime.rglob('*')
            if path.is_file() and path.stat().st_mode & 0o111
            and 'node_modules/.bin' not in str(path.relative_to(runtime))]
        (stage / 'runtime-executables.json').write_text(json.dumps(executable_files) + '\n')
        source = json.loads((runtime / 'runtime-source.json').read_text())
        if directory is not None:
            shutil.copytree(stage, directory, symlinks=True, dirs_exist_ok=True)
        else:
            write_zip(stage, output, 'pi', source, {'variant': 'I14-dx-test', 'base_variant': 'pi-braid-i14'})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--skills', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--directory', type=Path)
    parser.add_argument('--route', type=Path)
    parser.add_argument('--run-config', type=Path)
    parser.add_argument('--seed-data', type=Path)
    parser.add_argument('--otlp-deps', type=Path)
    parser.add_argument('--catalog', type=Path)
    parser.add_argument('--provider-env', type=Path)
    parser.add_argument('--model-proxy', type=Path)
    args = parser.parse_args()
    build(args.runtime, args.output, args.skills, args.route, args.run_config, args.seed_data,
          args.directory, args.otlp_deps, args.catalog, args.provider_env, args.model_proxy)
