"""Required files for the locked Linux E2E addon; browser payloads stay external."""
import hashlib
import json
from pathlib import Path
import shutil

# These are the entry points consumed by the shipped wrapper/config, including
# esbuild's Linux binary used to load TypeScript configs and application checks.
ENTRIES = ("e2e/dist/cli/bin.js", "@e2e-dev/web/dist/engine.js",
           "@ai-sdk/openai-compatible/dist/index.js", "playwright/cli.js",
           "@esbuild/linux-x64/bin/esbuild")
VERSIONS = {"e2e": "0.15.1", "@e2e-dev/web": "0.11.1",
            "@ai-sdk/openai-compatible": "3.0.53", "playwright": "1.63.0"}


def require_e2e_addon(addon):
    addon = Path(addon)
    for member in ("package.json", "package-lock.json", "addon-source.json",
                   *("node_modules/" + name for name in ENTRIES)):
        if not (addon / member).is_file():
            raise ValueError(f"E2E addon missing required file: {addon / member}; build-e2e.py --profile arc-core and pass --e2e-runtime")
    if json.loads((addon / "addon-source.json").read_text()).get("platform") != "linux-x86_64":
        raise ValueError(f"E2E addon requires frozen linux-x86_64 identity: {addon}")
    for name, version in VERSIONS.items():
        metadata = json.loads((addon / "node_modules" / name / "package.json").read_text())
        if metadata.get("version") != version:
            raise ValueError(f"E2E addon version mismatch: {name}; expected {version}, got {metadata.get('version')}")
    executable = addon / "node_modules/@esbuild/linux-x64/bin/esbuild"
    if not executable.stat().st_mode & 0o111:
        raise ValueError(f"E2E addon esbuild is not executable: {executable}")
    with executable.open("rb") as binary:
        magic = binary.read(4)
    if magic != b"\x7fELF":
        raise ValueError(f"E2E addon esbuild is not Linux ELF: {addon}")
    for name in ("libnss3.so", "libfontconfig.so.1"):
        if not (addon / "lib" / name).is_file():
            raise ValueError(f"E2E browser runtime library missing: {addon / 'lib' / name}")
    return {member: hashlib.sha256((addon / "node_modules" / member).read_bytes()).hexdigest()
            for member in ENTRIES}


def copy_e2e_addon(source, destination):
    source, destination = Path(source).resolve(strict=True), Path(destination)
    require_e2e_addon(source)
    if destination.exists():
        shutil.rmtree(destination)
    # npm runtime dependencies are needed; browser downloads and rebuildable
    # caches stay out of the package. The locked Linux browser
    # library closure remains part of the addon.
    destination.mkdir(parents=True)
    for name in ("package.json", "package-lock.json", "node_modules", "lib"):
        origin = source / name
        if origin.is_dir():
            shutil.copytree(origin, destination / name, symlinks=True,
                            ignore=shutil.ignore_patterns("__pycache__", ".cache", ".npm"))
        else:
            shutil.copy2(origin, destination / name)
    record = {"platform": "linux-x86_64", "profile": "arc-core",
              "producer": "copy_e2e_addon", "source": str(source),
              "source_identity_sha256": hashlib.sha256((source / "addon-source.json").read_bytes()).hexdigest(),
              "omitted": ["browsers", ".cache", ".npm"],
              "browser_provisioning": "locked @e2e-dev/web first-run Playwright install in owned cache"}
    (destination / "addon-source.json").write_text(json.dumps(record, indent=2) + "\n")
    record["entry_sha256"] = require_e2e_addon(destination)
    return record


def copy_e2e_install_material(source, destination):
    """Copy only what the container needs to install the locked addon."""
    source, destination = Path(source).resolve(strict=True), Path(destination)
    require_e2e_addon(source)
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)
    for name in ("package.json", "package-lock.json", "addon-source.json", "lib"):
        origin = source / name
        if origin.is_dir():
            shutil.copytree(origin, destination / name, symlinks=False)
        else:
            shutil.copy2(origin, destination / name)
    return {"platform": "linux-x86_64", "profile": "arc-core",
            "producer": "copy_e2e_install_material",
            "omitted": ["node_modules", "browsers", ".cache", ".npm"]}
