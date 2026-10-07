"""Repackage a frozen native runtime as a raw Pi/Codex ARC-Bench entry."""

import argparse
from contextlib import ExitStack
import hashlib
import json
from pathlib import Path
import shutil
import sys
from zipfile import ZipFile, ZIP_DEFLATED


ROOT = Path(__file__).resolve().parents[2]


def package(source, backend, model, output):
    source = Path(source).resolve(strict=True)
    output = Path(output).resolve()
    models = json.loads((ROOT / "variants/raw/raw_models.json").read_text())
    if backend not in ("pi", "codex") or model not in models:
        raise ValueError("unsupported native backend or model")
    with ExitStack() as stack:
        if source.is_dir():
            source_manifest = json.loads((source/'runtime-source.json').read_text())
            paths = {"runtime/"+str(p.relative_to(source)):p for p in source.rglob('*')
                     if p.is_file() and 'node_modules/.bin' not in str(p.relative_to(source))}
            files = {name:{'executable':bool(p.stat().st_mode & 0o111),
                           'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for name,p in paths.items()}
            source_manifest['files'] = files
            source_digest = hashlib.sha256(json.dumps(files,sort_keys=True).encode()).hexdigest()
            def read_runtime(name): return paths[name].open('rb')
        else:
            archive = stack.enter_context(ZipFile(source))
            source_manifest = json.loads(archive.read("package-manifest.json"))
            source_digest = hashlib.sha256(source.read_bytes()).hexdigest()
            def read_runtime(name): return archive.open(name)
        if source_manifest["backend"] != backend:
            raise ValueError("runtime source backend does not match")
        files = source_manifest["files"]
        runtime = [name for name in files if name.startswith("runtime/")]
        executable = [name for name in runtime if files[name]["executable"]]
        if not runtime or f"runtime/bin/{backend}" not in executable:
            raise ValueError("runtime source lacks the requested native executable")
        descriptor = models[model]["descriptor"]
        config = {"schema_version": 2, "backend": backend, "model": model,
                  "descriptor": descriptor,
                  "chat_parameters": {**models[model]["chat_parameters"],
                                      "max_tokens": descriptor["maxTokens"]},
                  "runtime_source_sha256": source_digest}
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("xb") as stream:
            try:
                with ZipFile(stream, "w", compression=ZIP_DEFLATED, compresslevel=6) as target:
                    for name in runtime:
                        with read_runtime(name) as source_file, target.open(name, "w", force_zip64=True) as target_file:
                            shutil.copyfileobj(source_file, target_file, 1024 * 1024)
                    target.writestr("main.py", (ROOT / "variants/raw/raw_main.py").read_bytes())
                    target.writestr("raw_otlp.py", (ROOT / "variants/raw/raw_otlp.py").read_bytes())
                    if backend == "codex":
                        target.writestr("responses_compat.py", (ROOT / "tooling/scripts/responses_compat.py").read_bytes())
                        target.writestr("raw_responses_compat.py", (ROOT / "variants/raw/raw_responses_compat.py").read_bytes())
                    target.writestr("requirements.txt", "")
                    target.writestr("raw-config.json", json.dumps(config, ensure_ascii=False, indent=2) + "\n")
                    target.writestr("runtime-executables.json", json.dumps(executable) + "\n")
            except BaseException:
                output.unlink(missing_ok=True)
                raise
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--runtime", dest="source", type=Path, help="runtime.py linux 导出的独立目录")
    source.add_argument("--source", type=Path, help="历史 ZIP 的运行依赖；新构建优先使用 --runtime")
    parser.add_argument("--backend", choices=("pi", "codex"), required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(package(args.source, args.backend, args.model, args.output))


if __name__ == "__main__":
    sys.exit(main())
