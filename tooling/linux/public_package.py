"""Common public-package assembly for local and Hosted ARC runs."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile

from tooling.scripts.runtime import native_patch_specs

PATCHES = tuple((package, name) for package, name, _ in native_patch_specs())


def add_runtime_materials(stage: Path, runtime: Path, repository: Path, *, include_e2e: bool = True) -> None:
    native = stage / "native" / "bin"
    native.mkdir(parents=True, exist_ok=True)
    for name in ("pi", "braid", "factory26-resource-monitor"):
        source = runtime / "bin" / name
        if source.is_file():
            shutil.copy2(source, native / name)
    tini = repository / "tooling/linux/assets/tini-static-amd64"
    shutil.copy2(tini.resolve(strict=True), native / "tini")
    (native / "tini").chmod(0o755)
    shutil.copy2(repository / "tooling/linux/assets/LICENSE.tini", native / "LICENSE.tini")
    for name in ("native-managed.mjs", "v8-observation.mjs"):
        shutil.copy2(runtime / name, stage / "native" / name)
    source_metadata = runtime / "runtime-source.json"
    if source_metadata.is_file():
        # Hosted packages install the runtime inside the execution container;
        # carry the selected source identity beside the native payload so the
        # entrypoint can report what was actually installed.
        shutil.copy2(source_metadata, stage / "native" / source_metadata.name)
    npm = stage / "inputs" / "npm"
    npm.mkdir(parents=True, exist_ok=True)
    for name in ("package.json", "package-lock.json"):
        shutil.copy2(repository / "materials/npm/public-package" / name, npm / name)
    for name in ("native-managed.mjs", "v8-observation.mjs"):
        shutil.copy2(repository / "materials/npm" / name, npm / name)
    shutil.copytree(repository / "materials/npm/patches", npm / "patches", symlinks=True)
    (npm / "native-patches.json").write_text(json.dumps(
        [{"package": package, "file": filename} for package, filename in PATCHES], indent=2) + "\n")
    # E2E is a variant-owned definition, but its locked Linux addon must cross
    # the same Local/Hosted installation boundary as the native runtime.  The
    # addon producer intentionally omits browser downloads and caches; those
    # remain run-owned and are provisioned by the normal browser helper.
    try:
        definition_roles = json.loads((stage / "materials.json").read_text()).get("definition_roles", [])
    except (OSError, ValueError, TypeError):
        definition_roles = []
    if include_e2e and "e2e-runtime" in definition_roles:
        source = runtime / "e2e"
        from tooling.scripts.e2e_runtime import copy_e2e_install_material
        # The container installs the locked npm tree.  The submitted package
        # carries only the lock, provenance, and the small Linux library
        # closure; browser downloads and generated node_modules stay out.
        copy_e2e_install_material(source, stage / "inputs" / "e2e")
    shutil.copy2(repository / "tooling/linux/runtime_install.py", stage / "runtime_install.py")
    shutil.copy2(repository / "tooling/linux/browser_runtime.py", stage / "browser_runtime.py")


def add_shared_materials(stage: Path, runtime: Path, repository: Path,
                         otlp_deps: Path | None = None,
                         model_proxy: Path | None = None) -> None:
    """Add gateway/OTLP material shared by both transport forms."""
    shutil.copy2(repository / "lab/arc_bench/harness_services.py", stage / "harness_services.py")
    shutil.copy2(repository / "lab/otlp.py", stage / "lab_otlp.py")
    configured = repository / "runs/deadline-20261003/local-five/overlays/common/support/otlp-deps"
    source = (otlp_deps or runtime.parent / "otlp-deps")
    if not source.is_dir():
        source = configured
    shutil.copytree(source.resolve(strict=True), stage / "otlp-deps", symlinks=True)
    if model_proxy is not None:
        proxy = model_proxy.resolve(strict=True)
        if not proxy.stat().st_mode & 0o111:
            raise PermissionError(f"model proxy is not executable: {proxy}")
        (stage / "model-proxy").mkdir()
        shutil.copy2(proxy, stage / "model-proxy/factory26-model-proxy")
        (stage / "model-proxy/factory26-model-proxy").chmod(0o755)
        shutil.copy2(repository / "sources/model-proxy/prepare.py", stage / "model_proxy_prepare.py")
    (stage / "arc-runtime.pyz").unlink(missing_ok=True)
    subprocess.run([sys.executable, "-B", "-m", "lab.arc_bench", "runtime", "export",
                    "--output", str(stage / "arc-runtime.pyz")], cwd=repository, check=True)


def add_seed_data(stage: Path, source: Path) -> None:
    source = source.resolve(strict=True)
    roots = [("workspace", source / "workspace"), ("harness", source / "harness")]
    if (source / "data").is_dir():
        roots = [("workspace", source / "data/workspace"), ("harness", source / "data/harness")]
    destination = stage / "inputs" / "seed-data.tar"
    destination.parent.mkdir(exist_ok=True)
    with tarfile.open(destination, "w") as archive:
        for name, path in roots:
            if path.exists():
                archive.add(path, arcname=name, recursive=True,
                            filter=lambda info: None if info.name.rstrip("/").endswith(
                                "workspace/.factory26/data/harness") else info)


def assemble(variant_dir: Path, runtime: Path, repository: Path,
             output: Path | None = None, directory: Path | None = None,
             route: Path | None = None, run_config: Path | None = None,
             seed_data: Path | None = None, otlp_deps: Path | None = None,
             catalog: Path | None = None, provider_env: Path | None = None,
             model_proxy: Path | None = None, identity: dict | None = None,
             prebuilt_runtime: bool = False) -> None:
    """Turn variant-only material into the one Local/Hosted package form."""
    if (output is None) == (directory is None):
        raise ValueError("exactly one of output or directory is required")
    import tempfile
    from tooling.scripts.package_agent import write_zip
    if catalog is not None and model_proxy is None:
        candidate = repository / "runs/provider-model-config-20261007/delivery/model-proxy-linux-x86_64-provider-usage-20261007/factory26-model-proxy-linux-x86_64"
        model_proxy = candidate.resolve(strict=True)
    with tempfile.TemporaryDirectory(prefix="factory26-public-", dir=repository / "runs") as temporary:
        stage = Path(temporary)
        shutil.copytree(variant_dir, stage, symlinks=True, dirs_exist_ok=True)
        # Runtime is a facility-owned output, never a variant payload.  A
        # stale material directory from the old prebuilt workflow must not
        # silently turn a new installer run back into a full package.
        if not prebuilt_runtime and (stage / "runtime").exists():
            shutil.rmtree(stage / "runtime")
        add_shared_materials(stage, runtime, repository, otlp_deps, model_proxy)
        add_runtime_materials(stage, runtime, repository,
                              include_e2e=not (output is not None and prebuilt_runtime))
        if output is not None and prebuilt_runtime:
            # Hosted cannot mount the selected offline runtime as Local does.
            # Preserve its native patches and separately built E2E addon.
            shutil.copytree(runtime, stage / "runtime", symlinks=True)
        wrap_entry(stage)
        if route:
            shutil.copy2(route.resolve(strict=True), stage / "gateway-routes.json")
            (stage / "inputs").mkdir(exist_ok=True)
            shutil.copy2(route.resolve(strict=True), stage / "inputs/gateway-routes.json")
        if catalog:
            (stage / "inputs").mkdir(exist_ok=True)
            shutil.copy2(catalog.resolve(strict=True), stage / "inputs/model-gateway.json")
        if provider_env:
            private = stage / ".private"
            private.mkdir(mode=0o700, exist_ok=True)
            private.chmod(0o700)
            target = private / "provider-env.json"
            shutil.copy2(provider_env.resolve(strict=True), target)
            target.chmod(0o600)
        if run_config:
            (stage / "inputs").mkdir(exist_ok=True)
            shutil.copy2(run_config.resolve(strict=True), stage / "inputs/lab-run.json")
        if seed_data:
            add_seed_data(stage, seed_data)
        executable_members = (["runtime/" + path.relative_to(runtime).as_posix()
                               for path in runtime.rglob("*")
                               if path.is_file() and path.stat().st_mode & 0o111
                               and "node_modules/.bin" not in path.relative_to(runtime).as_posix()]
                              if output is not None and prebuilt_runtime else
                              ["runtime/bin/node", "runtime/bin/pi", "runtime/bin/braid", "runtime/bin/tini"])
        if (stage / "inputs" / "e2e").is_dir() and not (output is not None and prebuilt_runtime):
            executable_members.extend(
                "runtime/e2e/" + path.relative_to(stage / "inputs" / "e2e").as_posix()
                for path in (stage / "inputs" / "e2e").rglob("*")
                if path.is_file() and path.stat().st_mode & 0o111
                and "node_modules/.bin" not in path.relative_to(stage / "inputs" / "e2e").as_posix()
            )
        (stage / "runtime-executables.json").write_text(json.dumps(executable_members) + "\n")
        if directory is not None:
            shutil.copytree(stage, directory, symlinks=True, dirs_exist_ok=True)
        else:
            source = json.loads((runtime / "runtime-source.json").read_text())
            write_zip(stage, output, "pi", source, identity or {})


def wrap_entry(stage: Path) -> None:
    entry = stage / "main.py"
    if not entry.is_file():
        raise FileNotFoundError(entry)
    entry.rename(stage / "variant_main.py")
    entry.write_text(r"""from pathlib import Path
import json
import os
import signal
import subprocess
import sys
import traceback

ROOT = Path(__file__).resolve().parent
output = None
child = None
receipt = {'status': 'generation_failed', 'entry_exit_code': 0}

def interrupted(signum, frame):
    receipt.update(status='externally_terminated', entry_exit_code=128 + signum, signal=signum)
    raise SystemExit(128 + signum)

signal.signal(signal.SIGTERM, interrupted)
signal.signal(signal.SIGINT, interrupted)
try:
    output = Path(sys.argv[sys.argv.index('--output-dir') + 1]).resolve()
    if os.environ.get('FACTORY26_TINI_ACTIVE') != '1':
        env = dict(os.environ, FACTORY26_TINI_ACTIVE='1')
        tini = ROOT / 'native/bin/tini'
        tini.chmod(0o755)
        os.execve(str(tini), [str(tini), '-s', '--', sys.executable, str(__file__), *sys.argv[1:]], env)
    from runtime_install import ensure, write_consumption_receipt
    runtime = ensure(ROOT)
    try:
        write_consumption_receipt(ROOT, output, runtime)
    except Exception as error:
        print(f'factory26 material-consumption receipt unavailable: {error}', file=sys.stderr)
    from harness_services import services
    with services(ROOT, output) as contract:
        child = subprocess.Popen([sys.executable, str(ROOT / 'variant_main.py'), *sys.argv[1:]],
                                 cwd=ROOT, start_new_session=True)
        try:
            contract['_resource_supervisor'].register_entry(child)
            code = child.wait()
            receipt['generation_exit_code'] = code
            if code < 0 or code in (130, 143):
                receipt.update(status='externally_terminated', entry_exit_code=128-code if code < 0 else code)
            else:
                # Internal generation failures remain evidence, not an evaluation gate.
                receipt['status'] = 'returned' if code == 0 else 'generation_failed'
        finally:
            if child.poll() is None:
                os.killpg(child.pid, signal.SIGTERM)
                try:
                    child.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    os.killpg(child.pid, signal.SIGKILL)
                    child.wait(timeout=5)
except Exception as error:
    receipt['error'] = f'{type(error).__name__}: {error}'
    traceback.print_exc()
finally:
    if output is not None:
        try:
            evidence = output / '.factory26/generation-entry.json'
            evidence.parent.mkdir(parents=True, exist_ok=True)
            evidence.write_text(json.dumps(receipt, ensure_ascii=False) + '\n')
        except Exception as error:
            print(f'factory26 entry receipt unavailable: {type(error).__name__}: {error}', file=sys.stderr)
raise SystemExit(receipt['entry_exit_code'])
""")
