"""Materialize one isolated official-Runner job per local Hackathon scenario."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys


ROOT = Path(__file__).resolve().parents[2]
BENCH = ROOT / "benchmarks/hackathon"


def relative(path, base):
    return os.path.relpath(Path(path).resolve(), base.resolve())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replay", type=Path, required=True)
    parser.add_argument("--inputs-root", type=Path, required=True)
    parser.add_argument("--runner", type=Path, required=True)
    parser.add_argument("--image", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--task", choices=("github", "sheet"), action="append")
    parser.add_argument("--scenario", action="append")
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists() or output.parent.joinpath("tests").exists():
        raise ValueError("output manifest and adjacent tests directory must be new")
    coverage = json.loads((BENCH / "coverage.json").read_text())
    selected = [item for item in coverage["requirements"]
                if (not args.task or item["task"] in args.task)
                and (not args.scenario or item["scenario_id"] in args.scenario)]
    if args.scenario and {item["scenario_id"] for item in selected} != set(args.scenario):
        raise ValueError("unknown or task-mismatched scenario ID")
    if not selected:
        raise ValueError("selection contains no scenarios")
    output.parent.mkdir(parents=True, exist_ok=True)
    tests_root = output.parent / "tests"
    tests_root.mkdir()
    jobs = []
    for item in selected:
        bundle = tests_root / item["scenario_id"]
        bundle.mkdir()
        for source in BENCH.glob("*.ts"):
            if source.name.startswith("."):
                continue
            shutil.copy2(source, bundle / source.name)
        selection = {"schema_version": 1, "scenario_id": item["scenario_id"],
                     "task": item["task"], "atomic_id": item["atomic_id"],
                     "requirements_sha256": coverage["requirements_sha256"][item["task"]]}
        (bundle / "selection.json").write_text(json.dumps(selection, indent=2) + "\n")
        inputs = args.inputs_root.resolve() / "hackathon" / item["task"] / "requirements"
        actual = hashlib.sha256((inputs / "requirements.yaml").read_bytes()).hexdigest()
        if actual != selection["requirements_sha256"]:
            raise ValueError(f"requirements identity mismatch for {item['task']}: {actual}")
        adapter = ROOT / "lab/arc_bench/arc_bench_adapter.py"
        job_inputs = {"adapter": str(adapter), "runner": str(args.runner.resolve()),
                      "agent": str(args.replay.resolve()), "requirements": str(inputs),
                      "tests": str(bundle)}
        jobs.append({
            "variant": "codex-base-artifact-replay",
            "competition": "hackathon-local",
            "task": item["scenario_id"],
            "venue": "public-requirements-proxy",
            "inputs": job_inputs,
            "command": [sys.executable, "{adapter}", "--runner", "{runner}",
                        "--agent", "{agent}", "--requirements", "{requirements}",
                        "--tests", "{tests}", "--workspace", "{workspace}",
                        "--competition", "hackathon", "--task", item["task"],
                        "--image", args.image, "--expected-tests", "1"],
            "artifact_paths": ["workspace/official/template/.arc",
                               "workspace/official/tests/test-results",
                               "workspace/official/execution.debug.log",
                               "workspace/official/local-result.json",
                               "workspace/container-cleanup.jsonl"],
        })
    manifest = {"schema_version": 1, "max_parallel": args.workers,
                "suite": coverage["suite"], "coverage": str(BENCH / "coverage.json"),
                "jobs": jobs}
    # lab.run resolves every input relative to the manifest, so keep portable relative paths.
    for job in jobs:
        job["inputs"] = {name: relative(path, output.parent) for name, path in job["inputs"].items()}
    output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"manifest": str(output), "jobs": len(jobs), "workers": args.workers}))


if __name__ == "__main__":
    main()
