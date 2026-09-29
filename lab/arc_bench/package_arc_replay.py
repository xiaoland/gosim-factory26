"""Package published ARC applications independently of later Runner scoring."""

import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

from .arc_artifacts import application_source, manifest as application_manifest, verify as verify_application


def package(runs, output):
    cases, files = [], {}
    for run in runs:
        state = json.loads((run / "run.json").read_text())
        published = next((path for path in (run / "workspace/official-generation/.lab-artifacts/application",
                                            run / "workspace/official/.lab-artifacts/application")
                          if path.is_dir() and (path.parent / "receipt.json").is_file()), None)
        application = (published or next((path for path in (run / "workspace/official-generation/template",
                                                             run / "workspace/official/template") if path.is_dir()),
                                         run / "workspace/official-generation/template")).resolve(strict=True)
        for part in ("frontend", "backend"):
            if not (application / part / "package.json").is_file():
                raise ValueError(f"Missing {part}/package.json: {application}")
        requirement = run / "inputs/requirements/requirements.yaml"
        requirement_hash = hashlib.sha256(requirement.read_bytes()).hexdigest()
        if any(case["requirements_sha256"] == requirement_hash for case in cases):
            raise ValueError("A replay package must contain only one application per requirement")
        receipt = published.parent / "receipt.json" if published else None
        app_manifest = verify_application(application, receipt) if receipt and receipt.is_file() else application_manifest(application)
        hashes = {}
        for item in app_manifest["entries"]:
            if item["type"] != "file":
                raise ValueError(f"replay ZIP cannot transport application symlink: {item['path']}")
            path = application / item["path"]
            hashes[item["path"]] = item["sha256"]
            files[f"applications/{state['run_id']}/{item['path']}"] = path
        provenance = "published" if published and application == published.resolve() else "imported-at-packaging"
        cases.append({"run_id": state["run_id"], "variant": state.get("variant"),
                      "competition": state["competition"], "task": state["task"],
                      "requirements_sha256": requirement_hash, "files": hashes,
                      "application_sha256": hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest(),
                      "application_manifest": app_manifest,
                      "source_application": application_source(state, run, app_manifest, provenance),
                      "provenance": provenance})
    manifest = {"mode": "artifact-replay", "delay_seconds": 3, "cases": cases}
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("xb") as stream:
        try:
            with ZipFile(stream, "w", compression=ZIP_DEFLATED) as archive:
                archive.write(Path(__file__).with_name("arc_replay.py"), "main.py")
                archive.write(Path(__file__).with_name("arc_artifacts.py"), "arc_artifacts.py")
                archive.writestr("requirements.txt", "")
                archive.writestr("replay-manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
                for name, path in files.items():
                    archive.write(path, name)
        except BaseException:
            output.unlink(missing_ok=True)
            raise
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest = package(args.run, args.output)
    print(json.dumps({"package": str(args.output), "runs": [case["run_id"] for case in manifest["cases"]]}))


if __name__ == "__main__":
    main()
