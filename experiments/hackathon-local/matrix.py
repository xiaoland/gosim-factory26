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
    parser.add_argument("--gateway-state", type=Path)
    parser.add_argument("--client-env", type=Path)
    parser.add_argument("--gateway-include-var", action="append", default=[])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--task", choices=("github", "sheet"), action="append")
    parser.add_argument("--scenario", action="append")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--experiment-key")
    parser.add_argument("--case", help="experiment configuration row, not the source variant")
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
        job_inputs = {"adapter": str(adapter), "runner": str(args.runner.resolve()),
                      "agent": str(args.replay.resolve()), "requirements": str(inputs),
                      "tests": str(tests_root), "selection": str(selection_path)}
        command = [sys.executable, "{adapter}/arc_bench_adapter.py", "--runner", "{runner}",
                   "--agent", "{agent}", "--requirements", "{requirements}",
                   "--tests", "{tests}", "--selection", "{selection}",
                   "--workspace", "{workspace}",
                   "--competition", "hackathon", "--task", item["task"],
                   "--image", args.image, "--expected-tests", "1"]
        if args.gateway_state:
            job_inputs["gateway"] = str(ROOT / "scripts/hackathon_gateway.py")
            job_inputs["gateway_service"] = str(args.gateway_state.resolve(strict=True) / "service.json")
            job_inputs["gateway_callback"] = str(args.gateway_state.resolve(strict=True) /
                                                 "code/hackathon_gateway_compat.py")
            wrapper = [sys.executable, "{gateway}", "wrap", "--service-state",
                       str(args.gateway_state.resolve(strict=True)), "--url-env", "OPENAI_BASE_URL",
                       "--key-env", "OPENAI_API_KEY", "--env-file-var", "ARC_MODEL_ENV_FILE"]
            if args.client_env:
                wrapper += ["--client-env", str(args.client_env.resolve(strict=True))]
            for variable in args.gateway_include_var:
                wrapper += ["--include-var", variable]
            command = wrapper + ["--"] + command
        handlers = {action: [[sys.executable, "{adapter}/arc_bench_adapter.py",
                              "resource", action, "--workspace", "{workspace}"]]
                    for action in ("inspect", "cleanup")}
        if args.gateway_state:
            for action in handlers:
                handlers[action].append([sys.executable, "{gateway}", "resource", action,
                                         "--service-state", str(args.gateway_state.resolve(strict=True)),
                                         "--run-dir", "{run_dir}", "--run-id", "{run_id}"])
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
            "adapter_kind": "arc-bench", "result_path": "workspace/experiment-result.json",
            "resource_handlers": handlers,
        })
    manifest = {"schema_version": 2, "max_parallel": args.workers,
                "suite": coverage["suite"], "coverage": str(BENCH / "coverage.json"),
                "jobs": jobs}
    # lab.run resolves every input relative to the manifest, so keep portable relative paths.
    for job in jobs:
        job["inputs"] = {name: relative(path, output.parent) for name, path in job["inputs"].items()}
    output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"manifest": str(output), "jobs": len(jobs), "workers": args.workers}))


if __name__ == "__main__":
    main()
