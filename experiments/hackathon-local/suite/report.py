"""Summarize local Hackathon proxy results without changing Runner evidence."""

import argparse
import base64
import hashlib
import json
from pathlib import Path
import time
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from lab.arc_bench.arc_artifacts import package_metadata, replay_source


ROOT = Path(__file__).resolve().parent


def tests_in(report):
    found = []

    def walk(suite):
        for spec in suite.get("specs", []):
            for test in spec.get("tests", []):
                found.append((spec, test))
        for child in suite.get("suites", []):
            walk(child)

    for suite in report.get("suites", []):
        walk(suite)
    return found


def error_text(test):
    values = []
    for result in test.get("results", []):
        for error in result.get("errors", []):
            values.append(str(error.get("message") or error.get("stack") or error))
        if result.get("error"):
            error = result["error"]
            values.append(str(error.get("message") or error.get("stack") or error))
    return "\n".join(values)


def phase_record(attachments):
    matches = [item for item in attachments if item.get("name") == "hackathon-outcome"]
    if len(matches) != 1 or not matches[0].get("body"):
        return None
    try:
        value = json.loads(base64.b64decode(matches[0]["body"]).decode())
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    return value if value.get("outcome") in {"passed", "failed", "blocked"} else None


def outcome(run, expected):
    state = json.loads((run / "run.json").read_text())
    base = {"run_id": state.get("run_id", run.name), "run_path": str(run),
            "run_phase": state.get("phase"), "finished_at": state.get("finished_at"),
            "labels": state.get("labels", {}), "retry_of": state.get("retry_of"),
            "source_application": state.get("source_application")}
    report_path = run / "workspace/official/template/.arc/playwright-report.json"
    if not report_path.is_file():
        return {**base, "outcome": "incomplete", "reason": state.get("error") or "missing Playwright report"}
    report = json.loads(report_path.read_text())
    tests = tests_in(report)
    matches = [(spec, test) for spec, test in tests
               if str(spec.get("title", "")).startswith(expected + " ::")]
    if len(tests) != 1 or len(matches) != 1:
        return {**base, "outcome": "incomplete",
                "reason": f"expected exactly {expected}; report has {len(tests)} tests and {len(matches)} matches"}
    spec, test = matches[0]
    statuses = [result.get("status") for result in test.get("results", [])]
    errors = error_text(test)
    final = test.get("results", [])[-1] if test.get("results") else {}
    attachments = final.get("attachments", [])
    phase = phase_record(attachments)
    if phase is None:
        return {**base, "outcome": "incomplete", "title": spec.get("title"),
                "statuses": statuses, "error": errors or "missing valid phase attachment",
                "attachments": attachments}
    adapter = state.get("result") or {}
    if (phase["outcome"] == "passed" and final.get("status") != "passed") or (
            phase["outcome"] == "failed" and final.get("status") == "passed"):
        return {**base, "outcome": "incomplete", "title": spec.get("title"),
                "statuses": statuses, "error": "phase attachment conflicts with final Playwright status",
                "attachments": attachments}
    if adapter.get("status") == "failed" or state.get("phase") in ("cancelled", "lost"):
        return {**base, "outcome": "incomplete", "title": spec.get("title"),
                "statuses": statuses, "error": "Runner result or execution phase is incomplete",
                "attachments": attachments}
    return {**base, "outcome": phase["outcome"], "title": spec.get("title"),
            "statuses": statuses, "step": phase.get("step"),
            "error": errors or phase.get("error"), "attachments": attachments}


def source_hash(directory, include_coverage):
    digest = hashlib.sha256()
    sources = [path for path in directory.glob("*.ts") if not path.name.startswith(".")]
    if include_coverage:
        sources.append(directory / "coverage.json")
    if not sources or any(not path.is_file() for path in sources):
        raise ValueError(f"missing frozen suite source in {directory}")
    for path in sorted(sources):
        digest.update(path.name.encode() + b"\0" + path.read_bytes())
    return digest.hexdigest()


def selection_path(run, state=None):
    state = state or json.loads((run / "run.json").read_text())
    item = state.get("inputs", {}).get("selection")
    if item:
        return run / item["path"]
    return run / "inputs/tests/selection.json"


def application_identity(run, state, requirement_hash):
    source = state.get("source_application") or {}
    if source.get("sha256") and source.get("algorithm"):
        return {key: source[key] for key in ("algorithm", "sha256")}
    for relative in ("workspace/official/template/.arc/replay.json",
                     "workspace/official-generation/template/.arc/replay.json"):
        path = run / relative
        if path.is_file():
            case = json.loads(path.read_text())
            if case.get("requirements_sha256") != requirement_hash:
                raise ValueError(f"replay source requirement mismatch: {path}")
            source = replay_source(case)
            return {key: source[key] for key in ("algorithm", "sha256")}
    agent = state.get("inputs", {}).get("agent", {})
    path = run / agent["path"] if agent.get("path") else None
    if path and path.is_file():
        matches = [item for item in package_metadata(path)["source_applications"]
                   if item["requirements_sha256"] == requirement_hash]
        if len(matches) == 1:
            return {key: matches[0][key] for key in ("algorithm", "sha256")}
    return None


def run_identity(run, item, coverage):
    state = json.loads((run / "run.json").read_text())
    selection = json.loads(selection_path(run, state).read_text())
    expected = {"scenario_id": item["scenario_id"], "task": item["task"],
                "atomic_id": item["atomic_id"],
                "requirements_sha256": coverage["requirements_sha256"][item["task"]]}
    if any(selection.get(key) != value for key, value in expected.items()):
        raise ValueError(f"selection does not match coverage: {run}")
    requirements = run / "inputs/requirements/requirements.yaml"
    if hashlib.sha256(requirements.read_bytes()).hexdigest() != expected["requirements_sha256"]:
        raise ValueError(f"frozen requirements do not match coverage: {run}")
    agent = (state.get("inputs", {}).get("agent", {}).get("sha256") or
             state.get("source_application", {}).get("sha256"))
    if not agent:
        raise ValueError(f"missing frozen replay identity: {run}")
    source = run / "inputs/tests"
    complete = (source / "coverage.json").is_file()
    digest = source_hash(source, complete)
    if complete:
        if selection.get("suite_sha256") != digest:
            raise ValueError(f"frozen suite hash does not match selection: {run}")
    return {"test_source_sha256": digest, "coverage_snapshot": complete, "agent_input_sha256": agent,
            "image_id": (state.get("result") or {}).get("image_id"),
            "application": application_identity(run, state, expected["requirements_sha256"])}


def selected_runs(args):
    paths, batches = [], []
    if args.experiment:
        for reference in args.experiment:
            manifest_path = reference if reference.is_file() else reference / "manifest.json"
            value = json.loads(manifest_path.read_text())
            if value.get("record_type") != "lab.experiment":
                raise ValueError(f"expected frozen lab manifest: {manifest_path}")
            root = manifest_path.parent / value["runs_root"]
            job_ids = {job["id"] for job in value["jobs"]}
            for path in sorted(root.glob("*/run.json")):
                state = json.loads(path.read_text())
                if state.get("experiment_id") == value["experiment_id"] and state.get("job_id") in job_ids:
                    paths.append(path.parent.resolve())
            batches.append({"experiment_id": value["experiment_id"], "manifest": str(manifest_path.resolve()),
                            "job_ids": sorted(job_ids)})
    elif args.run:
        paths = [path.resolve(strict=True) for path in args.run]
        batches.append({"explicit_runs": [str(path) for path in paths]})
    else:
        paths = [path.parent.resolve() for path in sorted(args.runs_root.glob("*/run.json"))]
        identities = {json.loads((path / "run.json").read_text()).get("experiment_id") for path in paths}
        if None in identities or len(identities) != 1:
            raise ValueError("runs root has mixed or unknown batches; choose --experiment or explicit --run paths: "
                             + json.dumps(sorted(str(value) for value in identities)))
        batches.append({"experiment_id": next(iter(identities)), "runs_root": str(args.runs_root.resolve())})
    if len(set(paths)) != len(paths):
        raise ValueError("the same run was selected more than once")
    return paths, batches


def retry_leaves(rows):
    # Only an explicit edge within the same frozen job replaces an earlier observation.
    indexed = {(row["state"].get("experiment_id"), row["state"].get("job_id"), row["state"]["run_id"]): row
               for row in rows}
    replaced = {}
    for row in rows:
        state = row["state"]
        if not state.get("experiment_id") or not state.get("job_id"):
            continue
        seen = {state["run_id"]}
        parent = state.get("retry_of")
        while parent:
            if parent in seen:
                raise ValueError(f"cyclic retry relationship: {row['run']}")
            seen.add(parent)
            previous = indexed.get((state["experiment_id"], state["job_id"], parent))
            if previous is None:
                break
            replaced[str(previous["run"])] = {"run": str(previous["run"]), "reason": "explicit retry descendant selected",
                                               "replaced_by": str(row["run"])}
            parent = previous["state"].get("retry_of")
    return [row for row in rows if str(row["run"]) not in replaced], list(replaced.values())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--runs-root", type=Path, help="one known lab experiment only")
    selection.add_argument("--experiment", type=Path, action="append", help="frozen experiment or manifest; repeatable")
    selection.add_argument("--run", type=Path, action="append", help="explicit batch members; repeatable")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--coverage", type=Path, help="explicit frozen coverage for legacy runs lacking a snapshot")
    args = parser.parse_args()
    paths, batches = selected_runs(args)
    groups, skipped = {}, []
    for run in paths:
        state = json.loads((run / "run.json").read_text())
        source = run / "inputs/tests/coverage.json"
        if not source.is_file():
            source = args.coverage
        if source is None or not source.is_file():
            raise ValueError(f"missing frozen coverage for {run}; pass --coverage")
        coverage = json.loads(source.read_text())
        coverage_sha = hashlib.sha256(source.read_bytes()).hexdigest()
        selection_file = selection_path(run, state)
        scenario = (json.loads(selection_file.read_text()).get("scenario_id") if selection_file.is_file() else
                    (state.get("labels") or {}).get("scenario") or state.get("task"))
        item = next((item for item in coverage["requirements"] if item["scenario_id"] == scenario), None)
        if item is None:
            skipped.append({"run": str(run), "reason": f"no scenario in selected coverage: {scenario}"})
            continue
        error = None
        try:
            identity = run_identity(run, item, coverage)
        except (OSError, ValueError, KeyError) as exc:
            identity = {}
            error = f"{type(exc).__name__}: {exc}"
        labels = state.get("labels") or {}
        condition = {"experiment_id": state.get("experiment_id"), "experiment_key": labels.get("experiment_key"),
                     "case": labels.get("case"), "variant": labels.get("variant") or state.get("variant"),
                     "task": item["task"], "application": identity.get("application"),
                     "suite_sha256": identity.get("test_source_sha256"), "coverage_sha256": coverage_sha,
                     "image_id": identity.get("image_id"), "venue": labels.get("venue") or state.get("venue"),
                     "execution_inputs": {name: {key: value.get(key) for key in ("algorithm", "sha256")}
                                          for name, value in state.get("inputs", {}).items()
                                          if name not in ("tests", "selection")}}
        # Unknown application identity is not evidence that two runs consumed the same application.
        if not condition["application"] or error:
            condition["unresolved_run"] = state["run_id"]
        key = json.dumps(condition, sort_keys=True)
        groups.setdefault(key, []).append({"run": run, "state": state, "scenario": scenario, "coverage": coverage,
                                          "coverage_source": str(source.resolve()), "identity": identity,
                                          "condition": condition, "error": error})
    all_leaves, replaced = retry_leaves([row for rows in groups.values() for row in rows])
    leaf_paths = {str(row["run"]) for row in all_leaves}
    cohorts = {}
    for rows in groups.values():
        leaves = [row for row in rows if str(row["run"]) in leaf_paths]
        if not leaves:
            continue
        scenarios = [row["scenario"] for row in leaves]
        # Independent repeats cannot be aligned across scenarios by time or display name.
        partitions = [[row] for row in leaves] if len(set(scenarios)) != len(scenarios) else [leaves]
        for partition in partitions:
            first = partition[0]
            condition = first["condition"]
            coverage = first["coverage"]
            by_scenario = {row["scenario"]: row for row in partition}
            requirements, selected = [], {}
            for item in coverage["requirements"]:
                if item["task"] != condition["task"]:
                    continue
                row = by_scenario.get(item["scenario_id"])
                result = {"outcome": "unexecuted"}
                if row:
                    selected[item["scenario_id"]] = str(row["run"])
                    if row["error"]:
                        result = {"outcome": "incomplete", "run_id": row["state"]["run_id"],
                                  "run_path": str(row["run"]), "reason": row["error"]}
                    else:
                        result = {**outcome(row["run"], item["scenario_id"]), **row["identity"]}
                requirements.append({**item, "result": result})
            summary = {"full_suite_requirements": len(requirements), "selected_requirements": len(selected),
                       **{name: sum(item["result"]["outcome"] == name for item in requirements)
                          for name in ("passed", "failed", "blocked", "incomplete", "unexecuted")}}
            key = f"cohort-{len(cohorts) + 1:03d}"
            partition_paths = {str(row["run"]) for row in partition}
            excluded = [item for item in replaced if item["replaced_by"] in partition_paths]
            cohorts[key] = {**condition, "summary": {condition["task"]: summary}, "requirements": requirements,
                            "selection": selected, "excluded": excluded,
                            "coverage_sources": sorted({row["coverage_source"] for row in partition}),
                            "claim": coverage["interpretation"], "suite": coverage["suite"],
                            "requirements_sha256": coverage["requirements_sha256"],
                            "agent_input_versions": sorted({row["identity"]["agent_input_sha256"] for row in partition
                                                            if row["identity"].get("agent_input_sha256")}),
                            "independent_repeat": len(partitions) > 1,
                            "conditions_complete": bool(condition["application"] and condition["suite_sha256"]
                                and condition["image_id"] and all(row["identity"].get("coverage_snapshot") for row in partition)
                                and {'runner', 'adapter', 'requirements'} <= condition['execution_inputs'].keys()
                                and all(value['algorithm'] and value['sha256'] for value in condition['execution_inputs'].values()))}
    report = {"schema_version": 3, "batches": batches, "cohorts": cohorts, "excluded": skipped + replaced,
              "report_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    report["comparison"] = {"variant_is_grouping_axis": False,
        "same_frozen_suite": bool(cohorts) and len({cohort["suite_sha256"] for cohort in cohorts.values()}) == 1
                             and all(cohort["suite_sha256"] for cohort in cohorts.values())}
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "result.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    (args.output / "analysis.json").write_text(json.dumps({
        "schema_version": 1, "title": "Hackathon public-requirements proxy",
        "created_at": time.time(), "tool": "experiments/hackathon-local/suite/report.py",
        "tool_sha256": report["report_source_sha256"], "batches": batches,
        "run_ids": [json.loads((path / "run.json").read_text())["run_id"] for path in paths],
        "result": "result.json", "report": "report.md"
    }, ensure_ascii=False, indent=2) + "\n")
    lines = ["# Hackathon 本地公开需求代理评测", "", "按明确选择的批次、配置、赛题、应用与评测条件分组；不是官网分数。", ""]
    for key, cohort in cohorts.items():
        lines += [f"## {cohort['case'] or cohort['variant'] or '未知配置'} / {cohort['task']} / {key}", "",
                  f"批次：{cohort['experiment_id'] or '显式 run 集（历史批次身份未知）'}。", "", cohort["claim"], ""]
        if not cohort["conditions_complete"]:
            lines += ["该组应用、镜像或测试来源不完整；具体缺失见 result.json，不声明同条件总分。", ""]
        if cohort["independent_repeat"]:
            lines += ["存在没有替代关系的独立重复，分别呈现；用显式 run 集选择一轮，不能按时间拼接。", ""]
        lines += ["| 任务 | 通过/本次选择/全套 | 失败 | 前置阻断 | 不完整 | 未执行 |",
                  "| --- | ---: | ---: | ---: | ---: | ---: |"]
        for task, summary in cohort["summary"].items():
            lines.append(f"| {task} | {summary['passed']}/{summary['selected_requirements']}/{summary['full_suite_requirements']} | "
                         f"{summary['failed']} | {summary['blocked']} | {summary['incomplete']} | {summary['unexecuted']} |")
        lines += ["", "| 场景 | 结果 | 运行名 | Run |", "| --- | --- | --- | --- |"]
        for item in cohort["requirements"]:
            result = item["result"]
            lines.append(f"| {item['scenario_id']} | {result['outcome']} | "
                         f"{result.get('labels', {}).get('run_name', '')} | {result.get('run_path', '')} |")
        lines.append("")
    if skipped:
        lines += ["## 未纳入场景统计", ""] + [f"- {item['run']}：{item['reason']}" for item in skipped]
    (args.output / "report.md").write_text("\n".join(lines) + "\n")
    print(json.dumps({"output": str(args.output), "cohorts": {name: item["summary"] for name, item in cohorts.items()}},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
