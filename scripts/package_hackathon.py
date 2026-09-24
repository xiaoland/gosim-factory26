"""Freeze a native Pi/Codex Hackathon ZIP from a Linux runtime directory."""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
from zipfile import ZipFile, ZIP_DEFLATED


ROOT = Path(__file__).resolve().parents[1]


def package(runtime, backend, svc, output):
    runtime = runtime.resolve(strict=True)
    source = json.loads((runtime / "runtime-source.json").read_text())
    if backend not in ("pi", "codex") or source["backend"] != backend:
        raise ValueError("runtime backend does not match")
    if not (runtime / "node_modules/playwright-core/package.json").is_file():
        raise ValueError("runtime lacks Playwright")
    files = {"runtime/" + str(path.relative_to(runtime)): path for path in runtime.rglob("*")
             if path.is_file() and "node_modules/.bin" not in str(path.relative_to(runtime))}
    executable = [name for name, path in files.items() if path.stat().st_mode & 0o111]
    if f"runtime/bin/{backend}" not in executable or "runtime/bin/agent-browser" not in executable:
        raise ValueError("runtime lacks native commands")
    skill = ROOT / "harness/skills/agent-browser"
    files.update({"skills/agent-browser/" + str(path.relative_to(skill)): path
                  for path in skill.rglob("*") if path.is_file()})
    if svc:
        skill = ROOT / "sources/svc"
        for part in ("SKILL.md", "references", "assets"):
            origin = skill / part
            paths = [origin] if origin.is_file() else origin.rglob("*")
            files.update({"skills/svc/" + str(path.relative_to(skill)): path
                          for path in paths if path.is_file()})
    files.update({name: ROOT / path for name, path in {
        "main.py": "submission/hackathon_main.py",
        "hackathon_models.json": "submission/hackathon_models.json",
        "raw_main.py": "submission/raw_main.py",
        "raw_otlp.py": "submission/raw_otlp.py",
        "native_browser.py": "submission/native_browser.py",
    }.items()})
    digest = hashlib.sha256(json.dumps({name: hashlib.sha256(path.read_bytes()).hexdigest()
                                      for name, path in files.items()}, sort_keys=True).encode()).hexdigest()
    config = {"backend": backend, "svc": svc, "model": "glm-5.3-flash",
              "runtime_source_sha256": hashlib.sha256((runtime / "runtime-source.json").read_bytes()).hexdigest()}
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("xb") as stream:
        try:
            with ZipFile(stream, "w", compression=ZIP_DEFLATED, compresslevel=6) as archive:
                for name, path in files.items():
                    with path.open("rb") as source_file, archive.open(name, "w", force_zip64=True) as target:
                        shutil.copyfileobj(source_file, target, 1024 * 1024)
                archive.writestr("raw-config.json", json.dumps(config, indent=2) + "\n")
                archive.writestr("runtime-executables.json", json.dumps(executable) + "\n")
                archive.writestr("requirements.txt", "")
                archive.writestr("package-manifest.json", json.dumps({**config, "files_sha256": digest}, indent=2) + "\n")
        except BaseException:
            output.unlink(missing_ok=True)
            raise
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--backend", choices=("pi", "codex"), required=True)
    parser.add_argument("--svc", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(package(args.runtime, args.backend, args.svc, args.output))


if __name__ == "__main__":
    main()
