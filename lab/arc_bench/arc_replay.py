"""Deliver a frozen local application for hosted scoring without regenerating it."""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("requirements", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    manifest = json.loads((root / "replay-manifest.json").read_text())
    digest = hashlib.sha256((args.requirements / "requirements.yaml").read_bytes()).hexdigest()
    matches = [case for case in manifest["cases"] if case["requirements_sha256"] == digest]
    if len(matches) != 1:
        raise ValueError(f"No unique frozen application for requirements SHA256 {digest}")
    case = matches[0]
    if Path(case["run_id"]).name != case["run_id"] or case["run_id"] in (".", ".."):
        raise ValueError("invalid replay run ID")
    print(f"Replaying frozen application from {case['run_id']}; no model generation", flush=True)
    time.sleep(3)
    shutil.copytree(root / "applications" / case["run_id"], args.output_dir, dirs_exist_ok=True)
    consumed = None
    if case.get("application_manifest"):
        from arc_artifacts import restore_modes, verify
        restore_modes(args.output_dir, case["application_manifest"])
        consumed = verify(args.output_dir, case["application_manifest"])
    else:
        hashes = {}
        for path in case["files"]:
            source = (args.output_dir / path).resolve(strict=True)
            if not source.is_relative_to(args.output_dir.resolve()) or not source.is_file():
                raise ValueError(f"legacy replay path escapes delivered application: {path}")
            hashes[path] = hashlib.sha256(source.read_bytes()).hexdigest()
        if hashes != case["files"]:
            raise ValueError("legacy replay application files changed after loading")
    evidence = args.output_dir / ".arc/replay.json"
    evidence.parent.mkdir(parents=True, exist_ok=True)
    evidence.write_text(json.dumps({**case, "consumed_application": consumed}, ensure_ascii=False, indent=2) + "\n")
    print(f"Delivered {case['application_sha256']}", flush=True)


if __name__ == "__main__":
    main()
