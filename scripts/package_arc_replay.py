"""Package completed ARC local applications for non-leaderboard hosted scoring."""

import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

from arc_bench_adapter import EXCLUDED_SOURCE


ROOT = Path(__file__).resolve().parents[1]


def package(runs, output):
    cases, files = [], {}
    for run in runs:
        state = json.loads((run / "run.json").read_text())
        if state["phase"] != "completed":
            raise ValueError(f"Run is not completed: {run}")
        application = (run / "workspace/official-generation/template").resolve(strict=True)
        for part in ("frontend", "backend"):
            if not (application / part / "package.json").is_file():
                raise ValueError(f"Missing {part}/package.json: {application}")
        requirement = run / "inputs/requirements/requirements.yaml"
        requirement_hash = hashlib.sha256(requirement.read_bytes()).hexdigest()
        if any(case["requirements_sha256"] == requirement_hash for case in cases):
            raise ValueError("A replay package must contain only one application per requirement")
        hashes = {}
        for path in sorted(application.rglob("*")):
            relative = path.relative_to(application)
            if set(relative.parts) & EXCLUDED_SOURCE or relative.name in {".env", ".env.local", ".env.production"}:
                continue
            if not path.is_file() or path.suffix in {".pyc", ".pyo"}:
                continue
            if not path.resolve().is_relative_to(application):
                raise ValueError(f"Application file points outside its root: {relative}")
            hashes[relative.as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
            files[f"applications/{state['run_id']}/{relative.as_posix()}"] = path
        cases.append({"run_id": state["run_id"], "variant": state["variant"],
                      "competition": state["competition"], "task": state["task"],
                      "requirements_sha256": requirement_hash, "files": hashes,
                      "application_sha256": hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()})
    manifest = {"mode": "artifact-replay", "delay_seconds": 3, "cases": cases}
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("xb") as stream:
        try:
            with ZipFile(stream, "w", compression=ZIP_DEFLATED) as archive:
                archive.write(ROOT / "submission/arc_replay.py", "main.py")
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
