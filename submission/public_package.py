"""Common public-package assembly for local and Hosted ARC runs."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile

PATCHES = (
    ("pi-background-bash", "pi-background-bash-1.0.5.patch"),
    ("pi-subagents", "pi-subagents-0.56.0-completion-boundary.patch"),
    ("pi-subagents", "pi-subagents-0.56.0-model-exclusion-boundary.patch"),
    ("pi-subagents", "pi-subagents-0.56.0-open-tools.patch"),
    ("pi-subagents", "pi-subagents-0.56.0-acceptance-off.patch"),
    ("@earendil-works/pi-coding-agent", "pi-coding-agent-0.85.1-braid-boundary.patch"),
    ("@earendil-works/pi-coding-agent", "pi-ai-0.85.1-connection-reset.patch"),
    ("@upstash/context7-pi", "context7-pi-0.1.2.patch"),
    ("@ff-labs/pi-fff", "pi-fff-0.11.0.patch"),
    ("@earendil-works/pi-coding-agent", "pi-coding-agent-0.85.1-i13-2-managed.patch"),
    ("pi-background-bash", "pi-background-bash-1.0.5-i13-2-managed.patch"),
    ("pi-subagents", "pi-subagents-0.56.0-i13-2-managed.patch"),
)


def add_runtime_materials(stage: Path, runtime: Path, repository: Path) -> None:
    native = stage / "native" / "bin"
    native.mkdir(parents=True, exist_ok=True)
    for name in ("pi", "braid"):
        source = runtime / "bin" / name
        if source.is_file():
            shutil.copy2(source, native / name)
    tini = repository / "submission/assets/tini-static-amd64"
    shutil.copy2(tini.resolve(strict=True), native / "tini")
    (native / "tini").chmod(0o755)
    shutil.copy2(repository / "submission/assets/LICENSE.tini", native / "LICENSE.tini")
    managed = runtime / "native-managed.mjs"
    if managed.is_file():
        shutil.copy2(managed, stage / "native" / managed.name)
    npm = stage / "inputs" / "npm"
    npm.mkdir(parents=True, exist_ok=True)
    for name in ("package.json", "package-lock.json"):
        shutil.copy2(repository / "harness/npm/public-package" / name, npm / name)
    shutil.copy2(repository / "harness/npm/native-managed.mjs", npm / "native-managed.mjs")
    shutil.copytree(repository / "harness/npm/patches", npm / "patches", symlinks=True)
    (npm / "native-patches.json").write_text(json.dumps(
        [{"package": package, "file": filename} for package, filename in PATCHES], indent=2) + "\n")
    shutil.copy2(repository / "submission/runtime_install.py", stage / "runtime_install.py")
    shutil.copy2(repository / "submission/browser_runtime.py", stage / "browser_runtime.py")


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
             model_proxy: Path | None = None, identity: dict | None = None) -> None:
    """Turn variant-only material into the one Local/Hosted package form."""
    if (output is None) == (directory is None):
        raise ValueError("exactly one of output or directory is required")
    import tempfile
    from scripts.package_agent import write_zip
    if catalog is not None and model_proxy is None:
        candidate = repository / "runs/provider-model-config-20261007/delivery/model-proxy-linux-x86_64-tcp-deadline-20261007/factory26-model-proxy-linux-x86_64"
        model_proxy = candidate.resolve(strict=True)
    with tempfile.TemporaryDirectory(prefix="factory26-public-", dir=repository / "runs") as temporary:
        stage = Path(temporary)
        shutil.copytree(variant_dir, stage, symlinks=True, dirs_exist_ok=True)
        add_shared_materials(stage, runtime, repository, otlp_deps, model_proxy)
        add_runtime_materials(stage, runtime, repository)
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
        (stage / "runtime-executables.json").write_text(
            json.dumps(["runtime/bin/node", "runtime/bin/pi", "runtime/bin/braid", "runtime/bin/tini"]) + "\n")
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
    entry.write_text(
        "from pathlib import Path\n"
        "import os\n"
        "import subprocess\n"
        "import sys\n"
        "from runtime_install import ensure\n\n"
        "ROOT = Path(__file__).resolve().parent\n"
        "if os.environ.get('FACTORY26_TINI_ACTIVE') != '1':\n"
        "    env = dict(os.environ, FACTORY26_TINI_ACTIVE='1')\n"
        "    tini = ROOT / 'native/bin/tini'\n"
        "    tini.chmod(0o755)\n"
        "    os.execve(str(tini), [str(tini), '-s', '--', sys.executable, str(__file__), *sys.argv[1:]], env)\n"
        "ensure(ROOT)\n"
        "from harness_services import services\n"
        "output = Path(sys.argv[sys.argv.index('--output-dir') + 1]).resolve()\n"
        "with services(ROOT, output) as contract:\n"
        "    child = subprocess.Popen([sys.executable, str(ROOT / 'variant_main.py'), *sys.argv[1:]], cwd=ROOT, start_new_session=True)\n"
        "    contract['_resource_supervisor'].register_entry(child)\n"
        "    try:\n"
        "        code = child.wait()\n"
        "    finally:\n"
        "        if child.poll() is None:\n"
        "            child.terminate()\n"
        "            child.wait(timeout=10)\n"
        "    raise SystemExit(code)\n")
