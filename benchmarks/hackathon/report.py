"""Summarize local Hackathon proxy results without changing Runner evidence."""

import argparse
import base64
import hashlib
import json
from pathlib import Path


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
            "run_phase": state.get("phase"), "finished_at": state.get("finished_at")}
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
    attachments = [attachment for result in test.get("results", []) for attachment in result.get("attachments", [])]
    phase = phase_record(attachments)
    if phase is None:
        return {**base, "outcome": "incomplete", "title": spec.get("title"),
                "statuses": statuses, "error": errors or "missing valid phase attachment",
                "attachments": attachments}
    return {**base, "outcome": phase["outcome"], "title": spec.get("title"),
            "statuses": statuses, "step": phase.get("step"),
            "error": errors or phase.get("error"), "attachments": attachments}


def suite_hash():
    digest = hashlib.sha256()
    for path in sorted(ROOT.glob("*")):
        if path.is_file() and path.name not in {"report.py"}:
            digest.update(path.name.encode() + b"\0" + path.read_bytes())
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    coverage = json.loads((ROOT / "coverage.json").read_text())
    latest = {}
    for run in args.runs_root.glob("*"):
        selection = run / "inputs/tests/selection.json"
        if not selection.is_file() or not (run / "run.json").is_file():
            continue
        scenario_id = json.loads(selection.read_text()).get("scenario_id")
        state = json.loads((run / "run.json").read_text())
        if scenario_id and (scenario_id not in latest or
                            state.get("finished_at", 0) > latest[scenario_id][0]):
            latest[scenario_id] = (state.get("finished_at", 0), run)
    requirements = []
    for item in coverage["requirements"]:
        run = latest.get(item["scenario_id"])
        result = outcome(run[1], item["scenario_id"]) if run else {"outcome": "unexecuted"}
        requirements.append({**item, "result": result})
    summaries = {}
    for task in ("github", "sheet"):
        items = [item for item in requirements if item["task"] == task]
        counts = {name: sum(item["result"]["outcome"] == name for item in items)
                  for name in ("passed", "failed", "blocked", "incomplete", "unexecuted")}
        summaries[task] = {"requirements": len(items), **counts}
    report = {"schema_version": 1, "suite": coverage["suite"], "suite_sha256": suite_hash(),
              "requirements_sha256": coverage["requirements_sha256"],
              "summary": summaries, "requirements": requirements,
              "claim": coverage["interpretation"]}
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "result.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    lines = ["# Hackathon 本地公开需求代理评测", "", coverage["interpretation"], "",
             "| 任务 | 通过/总数 | 失败 | 前置阻断 | 设施不完整 | 未执行 |",
             "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for task in ("github", "sheet"):
        summary = summaries[task]
        lines.append(f"| {task} | {summary['passed']}/{summary['requirements']} | {summary['failed']} | "
                     f"{summary['blocked']} | {summary['incomplete']} | {summary['unexecuted']} |")
    lines += ["", "## 场景", "",
              "| 任务 | 原子需求 | 场景 | 结果 | Run |", "| --- | --- | --- | --- | --- |"]
    for item in requirements:
        result = item["result"]
        run = result.get("run_path", "")
        lines.append(f"| {item['task']} | {item['atomic_id']} {item['name']} | {item['scenario_id']} | "
                     f"{result['outcome']} | {run} |")
    (args.output / "report.md").write_text("\n".join(lines) + "\n")
    print(json.dumps({"output": str(args.output), "summary": summaries}, ensure_ascii=False))


if __name__ == "__main__":
    main()
