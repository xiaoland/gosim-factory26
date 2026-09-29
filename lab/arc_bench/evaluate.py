"""Evaluate an existing ARC application without running its generating Agent."""

import argparse
import json
from pathlib import Path
import shutil
import sys

from .arc_artifacts import application_source as application_origin, copy_snapshot, verify as verify_application
from lab.plan import create
from lab.records import read_json
from lab.run import start
from lab.status import read_status


def source_application(run):
    for relative in ("workspace/official-generation/.lab-artifacts/application",
                     "workspace/official/.lab-artifacts/application",
                     "workspace/official-generation/template", "workspace/official/template"):
        app = run / relative
        if all((app / part / "package.json").is_file() for part in ("frontend", "backend")):
            if ".lab-artifacts" in relative:
                receipt = app.parent / "receipt.json"
                if not receipt.is_file():
                    continue
                verify_application(app, receipt)
            return app
    raise ValueError(f"no delivered application found in {run}")


def source_input(run, state, name):
    frozen = state.get("inputs", {}).get(name)
    if frozen is None:
        return None
    if state.get("schema_version") == 2:
        path = run / frozen["path"]
    else:
        path = run / "inputs" / name
        if frozen.get("kind") == "file":
            path /= Path(frozen["source"]).name
    return path if path.exists() else None


def _argument(command, flag):
    return command[command.index(flag) + 1] if flag in command else None


def prepare(run, output, *, tests=None, selection=None, image=None, runner=None, experiment_key=None, case=None):
    run = Path(run).expanduser().resolve(strict=True)
    output = Path(output).expanduser().resolve()
    state = read_status(run)
    app = source_application(run)
    tests = Path(tests).expanduser().resolve(strict=True) if tests else source_input(run, state, "tests")
    selection = Path(selection).expanduser().resolve(strict=True) if selection else (
        source_input(run, state, "selection") or (tests / "selection.json" if tests else None))
    requirement = source_input(run, state, "requirements")
    runner = Path(runner).expanduser().resolve(strict=True) if runner else source_input(run, state, "runner")
    image = image or (state.get("result") or {}).get("image_id")
    missing = [name for name, value in (("requirements", requirement), ("tests", tests),
                                         ("runner", runner), ("image", image)) if value is None]
    if missing:
        raise ValueError("frozen evaluation conditions are missing: " + ", ".join(missing))
    if selection is not None and not selection.is_file():
        raise ValueError(f"selection snapshot does not exist: {selection}")
    command = state.get("command") or []
    competition = _argument(command, "--competition") or state.get("competition")
    task = _argument(command, "--task") or state.get("task")
    if not competition or not task:
        raise ValueError("source run does not identify its ARC competition and task")
    staging = output.with_name(output.name + ".preparation")
    staging.mkdir(parents=True, exist_ok=False)
    try:
        receipt = copy_snapshot(app, staging / "source")
        source = staging / "source"
        adapter = Path(__file__).resolve().parent
        frozen_inputs = {"adapter": str(adapter), "noop": str(adapter / "arc_bench_noop.py"),
                         "application": str(source / "application"),
                         "application_receipt": str(source / "receipt.json"),
                         "requirements": str(requirement), "tests": str(tests), "runner": str(runner)}
        argv = [sys.executable, "{adapter}/arc_bench_adapter.py", "--runner", "{runner}",
                "--application", "{application}", "--application-receipt", "{application_receipt}",
                "--noop-script", "{noop}", "--requirements", "{requirements}",
                "--tests", "{tests}", "--workspace", "{workspace}",
                "--competition", competition, "--task", task, "--image", image,
                "--source-run-id", state["run_id"]]
        if selection is not None:
            frozen_inputs["selection"] = str(selection)
            argv += ["--selection", "{selection}"]
            case = read_json(selection).get("scenario_id")
            if case:
                argv += ["--expected-scenario", case, "--expected-tests", "1"]
        job = {"id": "evaluation", "adapter_kind": "arc-bench", "result_path": "workspace/experiment-result.json",
               "competition": competition,
               **({"variant": state["variant"]} if state.get("variant") else {}),
               "task": state.get("task") or task, "venue": "frozen-application-evaluation",
               "labels": {"operation": "replay", **({"experiment_key": experiment_key} if experiment_key else {}),
                          **({"case": case} if case else {})},
               "source_application": application_origin(state, run, receipt,
                   "published" if ".lab-artifacts" in app.parts else "imported-now"),
               "inputs": frozen_inputs, "command": argv,
               "resource_handlers": {action: [sys.executable, "{adapter}/arc_bench_adapter.py",
                                             "resource", action, "--workspace", "{workspace}"]
                                     for action in ("inspect", "cleanup")},
               "artifact_paths": ["workspace/official/local-result.json",
                                  "workspace/official/template/.arc/playwright-report.json",
                                  "workspace/evaluation.stdout.log", "workspace/evaluation.stderr.log"]}
        recipe = staging / "recipe.json"
        recipe.write_text(json.dumps({"schema_version": 2, "max_parallel": 1, "jobs": [job]}, indent=2) + "\n")
        return create(recipe, experiment_root=output)
    finally:
        shutil.rmtree(staging)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path, help="run that contains the application")
    parser.add_argument("--output", type=Path, required=True, help="new experiment root")
    parser.add_argument("--tests", type=Path, help="explicit frozen test directory if source run has none")
    parser.add_argument("--selection", type=Path)
    parser.add_argument("--runner", type=Path)
    parser.add_argument("--image", help="image ID; changing it creates a different evaluation condition")
    parser.add_argument("--plan-only", action="store_true")
    parser.add_argument("--experiment-key")
    parser.add_argument("--case", help="experiment configuration row, independent of source variant")
    parser.add_argument("--run-labels", type=Path, help="execution labels for job evaluation")
    args = parser.parse_args(argv)
    experiment = prepare(args.run, args.output, tests=args.tests, selection=args.selection,
                         runner=args.runner, image=args.image, experiment_key=args.experiment_key, case=args.case)
    print(json.dumps({"experiment": str(experiment), "source_run": str(args.run)}, ensure_ascii=False), flush=True)
    return 0 if args.plan_only else start(experiment, run_labels=read_json(args.run_labels) if args.run_labels else None)


if __name__ == "__main__":
    sys.exit(main())
