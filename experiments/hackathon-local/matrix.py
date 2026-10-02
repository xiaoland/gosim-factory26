"""Materialize one isolated official-Runner job per local Hackathon scenario."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[2]
BENCH = ROOT / "benchmarks/hackathon"
sys.path.insert(0, str(ROOT))
from lab.arc_bench.arc_artifacts import replay_source
from lab.exp.core import record


def suite_hash(directory):
    digest = hashlib.sha256()
    sources = [path for path in directory.glob("*.ts") if not path.name.startswith(".")]
    for path in sorted([directory / "coverage.json", *sources]):
        digest.update(path.name.encode() + b"\0" + path.read_bytes())
    return digest.hexdigest()


def relative(path, base):
    return os.path.relpath(Path(path).resolve(), base.resolve())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replay", type=Path, required=True)
    parser.add_argument("--inputs-root", type=Path, required=True)
    parser.add_argument("--runner", type=Path, required=True)
    parser.add_argument("--image", required=True)
    parser.add_argument("--controller-runtime", type=Path, required=True)
    parser.add_argument("--runner-runtime", type=Path, required=True)
    parser.add_argument("--storage", type=Path, required=True)
    parser.add_argument("--budget", type=Path, required=True)
    parser.add_argument("--docker-endpoint", type=Path, required=True)
    parser.add_argument("--admission-volume", required=True)
    parser.add_argument("--docker-slots", type=int, required=True)
    parser.add_argument("--memory-bytes", type=int, required=True)
    parser.add_argument("--cpus", type=float, required=True)
    parser.add_argument("--pids", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--task", choices=("github", "sheet"), action="append")
    parser.add_argument("--scenario", action="append")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--authorization", required=True)
    parser.add_argument("--experiment-key")
    parser.add_argument("--case", help="experiment configuration row, not the source variant")
    parser.add_argument('--authority-handoff', type=Path, required=True)
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
    with ZipFile(args.replay) as archive:
        replay = json.loads(archive.read("replay-manifest.json"))
    if replay.get("mode") != "artifact-replay":
        raise ValueError("--replay must be an artifact-replay package")
    cases = replay["cases"]
    identities = {}
    for task in {item["task"] for item in selected}:
        matches = [case for case in cases
                   if case["requirements_sha256"] == coverage["requirements_sha256"][task]]
        if len(matches) != 1 or matches[0]["task"] != task:
            raise ValueError(f"no unique replay case for {task}")
        identities[task] = matches[0]
    source_suite = suite_hash(BENCH)
    output.parent.mkdir(parents=True, exist_ok=True)
    tests_root = output.parent / "tests"
    tests_root.mkdir()
    for source in BENCH.glob("*.ts"):
        if not source.name.startswith("."):
            shutil.copy2(source, tests_root / source.name)
    shutil.copy2(BENCH / "coverage.json", tests_root / "coverage.json")
    selection_root = tests_root / "selections"
    selection_root.mkdir()
    storage = json.loads(args.storage.read_text())
    budget = json.loads(args.budget.read_text())
    endpoint = json.loads(args.docker_endpoint.read_text())
    jobs = []
    for item in selected:
        selection_path = selection_root / f'{item["scenario_id"]}.json'
        selection = {"schema_version": 1, "scenario_id": item["scenario_id"],
                     "task": item["task"], "atomic_id": item["atomic_id"],
                     "requirements_sha256": coverage["requirements_sha256"][item["task"]],
                     "suite_sha256": source_suite}
        selection_path.write_text(json.dumps(selection, indent=2) + "\n")
        inputs = args.inputs_root.resolve() / "hackathon" / item["task"] / "requirements"
        actual = hashlib.sha256((inputs / "requirements.yaml").read_bytes()).hexdigest()
        if actual != selection["requirements_sha256"]:
            raise ValueError(f"requirements identity mismatch for {item['task']}: {actual}")
        adapter = ROOT / "lab/arc_bench"
        job_inputs = {"runner": str(args.runner.resolve()),
                      "agent": str(args.replay.resolve()), "requirements": str(inputs),
                      "tests": str(tests_root), "selection": str(selection_path)}
        command = [sys.executable, "-m", "lab.arc_bench.arc_bench_adapter", "--runner", "{runner}",
                   "--agent", "{agent}", "--requirements", "{requirements}",
                   "--tests", "{tests}", "--selection", "{selection}",
                   "--workspace", "{workspace}",
                   "--competition", "hackathon", "--task", item["task"],
                   "--image", args.image, "--expected-tests", "1",
                   "--admission-volume", args.admission_volume, "--shared-docker-slots", str(args.docker_slots)]
        jobs.append({
            "id": item["scenario_id"],
            **({"variant": identities[item["task"]]["variant"]} if identities[item["task"]].get("variant") else {}),
            "source_application": replay_source(identities[item["task"]]),
            "labels": {"operation": "replay", "scenario": item["scenario_id"], "benchmark_task": item["task"],
                       **({"experiment_key": args.experiment_key} if args.experiment_key else {}),
                       **({"case": args.case} if args.case else {})},
            "competition": "hackathon-local",
            "task": item["scenario_id"],
            "venue": "public-requirements-proxy",
            "inputs": job_inputs,
            "command": command,
            "artifact_paths": ["workspace/official/template/.arc",
                               "workspace/official/tests/test-results",
                               "workspace/official/execution.debug.log",
                               "workspace/official/local-result.json",
                               "workspace/container-cleanup.jsonl",
                               "workspace/official/.lab-artifacts/receipt.json"],
            "purpose": "evaluate",
            "outputs": [{"name": "workspace", "type": "terminal-archive", "path": "."},
                        {"name": "score", "type": "evaluation-result", "path": "experiment-result.json"}],
            "backend": {"kind": "local", "capabilities_required": ["arc-sdk-host-docker"],
                        "external_docker": {"endpoint": endpoint, "image_id": args.image,
                                            "slots": args.docker_slots, "admission_volume": args.admission_volume,
                                            "authority_handoff": json.loads(args.authority_handoff.read_text())}},
            "limits": {"wall_seconds": budget["wall_seconds_per_attempt"],
                       "storage_bytes": storage["workspace_bytes_per_run"],
                       "telemetry_bytes": storage["telemetry_bytes_per_run"],
                       "memory_bytes": args.memory_bytes, "cpus": args.cpus, "pids": args.pids},
        })
    manifest = record('experiment', experiment_id=args.experiment_key or 'hackathon-local',
                      max_parallel=args.workers, suite=coverage['suite'], jobs=jobs,
                      storage=storage, budget=budget, authorization=args.authorization,
                      controller_runtime=str(args.controller_runtime.resolve()),
                      runner_runtime=str(args.runner_runtime.resolve()))
    for job in jobs:
        job.pop('artifact_paths', None)
        job['inputs'] = {name: {'source': str(Path(path).resolve())} for name, path in job['inputs'].items()}
    output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"manifest": str(output), "jobs": len(jobs), "workers": args.workers}))


if __name__ == "__main__":
    main()
