"""Freeze a hosted Braid workspace for self-funded recovery; generation requires explicit opt-in."""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
from zipfile import ZipFile, ZIP_DEFLATED, ZIP_STORED

from package_agent import is_metadata_path


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-run-id", required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--base-package", type=Path, required=True)
    parser.add_argument("--braid", type=Path, required=True)
    parser.add_argument("--braid-source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--continue-generation", action="store_true",
                        help="Resume open work items with models; source execution must already be stopped")
    parser.add_argument("--refresh-native-materials", action="store_true",
                        help="Use current variant instructions and collector with refreshed native materials")
    args = parser.parse_args()
    if args.refresh_native_materials and not args.continue_generation:
        parser.error("--refresh-native-materials requires --continue-generation")
    workspace = args.workspace.resolve(strict=True)
    base = args.base_package.resolve(strict=True)
    braid = args.braid.resolve(strict=True)
    braid_source = args.braid_source.resolve(strict=True)
    output = args.output.resolve()
    if output.exists():
        raise FileExistsError(output)
    with ZipFile(workspace) as archive:
        candidates = [p for p in archive.namelist() if p.startswith("template/.factory26/")
                      and p.endswith("/braid-state/request.json")]
        if len(candidates) != 1:
            raise ValueError(f"expected one retained Braid run, found {len(candidates)}")
        braid_run = candidates[0].split("/")[2]
        request = json.loads(archive.read(candidates[0]))
        if request.get("run_id") != braid_run:
            raise ValueError("retained Braid run identity differs from its path")
        requirements_sha256 = hashlib.sha256(archive.read("template/requirements/requirements.yaml")).hexdigest()
    source = {"source_run_id": args.source_run_id, "braid_run_id": braid_run,
              "workspace_sha256": digest(workspace), "base_package_sha256": digest(base),
              "braid_sha256": digest(braid), "braid_source_sha256": digest(braid_source),
              "requirements_sha256": requirements_sha256,
              "mode": "workspace-resume" if args.continue_generation else "completed-workspace-recovery",
              "refresh_native_materials": args.refresh_native_materials}
    root = Path(__file__).resolve().parents[1]
    main_file = root / "submission/recover_completed.py"
    replacements = {"main.py": main_file, "runtime/bin/braid": braid,
                    "recovery-braid-source.tar.gz": braid_source,
                    "recovery-workspace.zip": workspace}
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        with ZipFile(base) as original, ZipFile(output, "w", allowZip64=True) as target:
            manifest = json.loads(original.read("package-manifest.json"))
            manifest["files"] = {name: record for name, record in manifest["files"].items()
                                 if not is_metadata_path(name)}
            if args.refresh_native_materials:
                variant = manifest.get("capabilities", {}).get("variant")
                if variant not in {"pi-braid", "pi-braid-flash-team"}:
                    raise ValueError(f"unsupported Braid variant for native refresh: {variant}")
                instructions = sorted(name for name in manifest["files"]
                                      if len(Path(name).parts) == 3 and Path(name).parts[0] == "agents"
                                      and Path(name).name == "instructions.md")
                observer = "extensions/factory-subagent-observer.ts"
                if ("support/otlp.py" not in manifest["files"] or observer not in manifest["files"]
                        or not instructions):
                    raise ValueError("base package is missing collector, observer, or variant instructions")
                refreshed = ["support/otlp.py", observer, *instructions]
                replacements["support/otlp.py"] = (root / "lab/otlp.py").resolve(strict=True)
                replacements[observer] = (root / "variants" / variant / observer).resolve(strict=True)
                replacements.update({name: (root / "variants" / variant / name).resolve(strict=True)
                                     for name in instructions})
            skipped = set(replacements) | {"recovery-source.json", "package-manifest.json"}
            for item in original.infolist():
                if item.filename in skipped or is_metadata_path(item.filename):
                    continue
                with original.open(item) as incoming, target.open(item, "w") as outgoing:
                    shutil.copyfileobj(incoming, outgoing)
            for name, path in replacements.items():
                target.write(path, name, compress_type=ZIP_STORED if name.endswith(".zip") else ZIP_DEFLATED)
                manifest["files"][name] = {"sha256": digest(path),
                                           "executable": name == "runtime/bin/braid"}
            if args.refresh_native_materials:
                source["refreshed_files_sha256"] = {name: manifest["files"][name]["sha256"]
                                                    for name in refreshed}
            encoded = (json.dumps(source, ensure_ascii=False, indent=2) + "\n").encode()
            target.writestr("recovery-source.json", encoded, compress_type=ZIP_DEFLATED)
            manifest["files"]["recovery-source.json"] = {"sha256": hashlib.sha256(encoded).hexdigest(),
                                                          "executable": False}
            manifest["sources"]["braid"]["binary_sha256"] = source["braid_sha256"]
            manifest["sources"]["braid"]["source_snapshot_sha256"] = source["braid_source_sha256"]
            target.writestr("package-manifest.json", json.dumps(manifest, ensure_ascii=False),
                            compress_type=ZIP_DEFLATED)
    except BaseException:
        output.unlink(missing_ok=True)
        raise
    print(json.dumps({"package": str(output), "sha256": digest(output), **source}, ensure_ascii=False))


if __name__ == "__main__":
    main()
