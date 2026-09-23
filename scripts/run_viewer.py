#!/usr/bin/env python3
"""Generate a local, read-only HTML snapshot of archived runs."""

import argparse
from datetime import datetime
from html import escape
import hashlib
import json
import math
import os
from pathlib import Path
import re
from urllib.parse import quote

from inspect_runs import _case, list_runs, show_run


ROOT = Path(__file__).resolve().parents[1]
TERMINAL = {"PASSED", "FAILED", "CANCELLED"}
CASE_ID = re.compile(r"REQ-\d+(?:\.\d+)*")


STYLE = """
:root{font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:#182229;background:#f5f6f3;font-size:15px}
*{box-sizing:border-box}body{margin:0}a{color:#1659a5;text-decoration:none}a:hover{text-decoration:underline}main{max-width:1180px;margin:auto;padding:42px 24px 100px}
.top{display:flex;justify-content:space-between;align-items:flex-start;gap:20px;margin-bottom:30px}.eyebrow{font-size:12px;letter-spacing:.16em;text-transform:uppercase;font-weight:800;color:#56706a}h1{font-size:clamp(32px,5vw,54px);letter-spacing:-.05em;line-height:1.08;margin:8px 0 12px}h2{font-size:22px;letter-spacing:-.025em;margin:0 0 18px}p{line-height:1.55}.muted{color:#64736f}.small{font-size:13px}.panel{background:#fff;border:1px solid #dae3dc;border-radius:18px;padding:24px;margin:20px 0;box-shadow:0 8px 28px #213d2d0a}
.hero{background:#17352f;color:white;border-radius:22px;padding:32px;margin-bottom:24px}.hero .eyebrow,.hero .muted{color:#afcec5}.hero a{color:#cae6dd}.hero h1{margin-bottom:6px}
.stats{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin:20px 0}.stat{background:#fff;border:1px solid #dae3dc;border-radius:14px;padding:17px}.stat strong{font-size:27px;display:block;letter-spacing:-.04em}.stat span{font-size:12px;color:#64736f;text-transform:uppercase;letter-spacing:.08em;font-weight:700}
.toolbar{display:flex;gap:12px;align-items:center;margin:26px 0 14px}.toolbar input{width:100%;border:1px solid #cbd7cf;border-radius:12px;padding:13px 15px;font:inherit;background:#fff;outline-color:#356e60}.toolbar span{white-space:nowrap;color:#64736f}
table{width:100%;border-collapse:collapse}th{text-align:left;color:#687975;font-size:11px;letter-spacing:.09em;text-transform:uppercase;padding:12px 10px;border-bottom:1px solid #dce5de}td{padding:15px 10px;border-bottom:1px solid #edf0ed;vertical-align:top}tr:last-child td{border-bottom:0}tr:hover td{background:#f8faf8}.runname{font-weight:750;word-break:break-word}.meta{font-size:12px;color:#697973;margin-top:4px}.nowrap{white-space:nowrap}
.pill{display:inline-block;border-radius:999px;padding:4px 10px;font-size:12px;font-weight:750;background:#e9eeeb;color:#52655e}.pill.ok{background:#daf0df;color:#246441}.pill.bad{background:#f9e5df;color:#9f4431}.pill.live{background:#e5edfc;color:#305da3}.pill.warn{background:#fff0c9;color:#805d12}
.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}.field{border:1px solid #e1e7e2;border-radius:12px;padding:16px;background:#fbfcfb;min-width:0}.field span{display:block;color:#687975;font-size:12px;margin-bottom:8px}.field strong{display:block;font-size:17px;overflow-wrap:anywhere}.field small{display:block;color:#687975;margin-top:5px}
.bar{height:9px;background:#e5ece7;border-radius:20px;margin:16px 0 0;overflow:hidden}.bar i{display:block;height:100%;background:#3c8e6f;border-radius:20px}.bar.bad i{background:#d77552}
.case{border:1px solid #e1e7e2;border-radius:12px;margin:9px 0;background:#fff;overflow:hidden}.case summary{cursor:pointer;display:flex;align-items:center;gap:12px;padding:14px 16px;list-style:none}.case summary::-webkit-details-marker{display:none}.case summary:after{content:"+";margin-left:auto;color:#74877d;font-size:18px}.case[open] summary:after{content:"−"}.case .body{border-top:1px solid #e9eee9;padding:15px 16px}.case .title{font-weight:650;flex:1}.case .id{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12px;color:#4c645b;min-width:78px}pre{background:#f4f6f4;color:#24322b;white-space:pre-wrap;overflow-wrap:anywhere;border-radius:9px;padding:12px;max-height:300px;overflow:auto;font-size:12px;line-height:1.5}.links{display:flex;flex-wrap:wrap;gap:8px}.links a{background:#eef4f0;border:1px solid #d8e5dc;border-radius:8px;padding:7px 10px;font-size:12px}.warning{border-left:3px solid #c48a25;background:#fff8e9;padding:10px 13px;margin:8px 0;border-radius:0 8px 8px 0;overflow-wrap:anywhere}.empty{padding:35px;text-align:center;color:#687975}.back{display:inline-block;margin-bottom:14px;font-weight:650}.section-note{font-size:13px;color:#687975;margin-top:-8px;margin-bottom:18px}
@media(max-width:760px){main{padding:20px 14px 60px}.top{display:block}.stats{grid-template-columns:repeat(2,1fr)}.grid{grid-template-columns:1fr}.table-wrap{overflow:auto}table{min-width:700px}.hero{padding:24px}}
"""


def txt(value):
    return escape("未知" if value is None or value == "" else str(value), quote=True)


def read_json(path):
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ValueError(f"{path} 顶层不是对象")
    return value


def file_link(path, label, output, runs):
    if not path:
        return ""
    path = Path(path).resolve()
    if not path.is_relative_to(runs.resolve()) or not path.is_file():
        return ""
    relative = os.path.relpath(path, output)
    return f'<a href="{escape(quote(relative, safe="/"), quote=True)}">{txt(label)}</a>'


def links(paths, output, runs):
    rendered = [file_link(path, label, output, runs) for label, path in paths]
    rendered = [link for link in rendered if link]
    return '<div class="links">' + "".join(rendered) + "</div>" if rendered else '<p class="muted small">无已归档文件</p>'


def score_from_platform(value):
    """A terminal status alone does not make partial counters a score."""
    if value.get("status") not in TERMINAL:
        return None
    passed, failed = value.get("passed_count"), value.get("failed_count")
    total = value.get("total_tests")
    if total is None and isinstance(value.get("tests"), list):
        total = len(value["tests"])
    score = value.get("score")
    if (any(type(number) is not int or number < 0 for number in (passed, failed, total))
            or total == 0 or passed + failed != total
            or type(score) not in (int, float) or not math.isfinite(score)):
        return None
    return {"passed": passed, "failed": failed, "total": total, "score": score}


def status_pill(value):
    status = str(value or "unknown")
    kind = ("ok" if status.lower() in {"passed", "generated", "completed"} else
            "bad" if status.lower() in {"failed", "generation_failed", "interrupted", "cancelled"} else
            "live" if status.lower() in {"running", "generating"} else "warn")
    return f'<span class="pill {kind}">{txt(status)}</span>'


def field(label, value, note=None):
    return f'<div class="field"><span>{txt(label)}</span><strong>{txt(value)}</strong>' + (f'<small>{txt(note)}</small>' if note else "") + "</div>"


def short(value, limit=3000):
    clean = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", str(value or ""))
    return clean[:limit] + ("…" if len(clean) > limit else "")


def time_value(value):
    try:
        return datetime.fromtimestamp(float(value)).astimezone()
    except (TypeError, ValueError, OverflowError):
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone()
        except (TypeError, ValueError):
            return None


def time_text(value):
    parsed = time_value(value)
    return parsed.strftime("%Y-%m-%d %H:%M") if parsed else "未知"


def case_html(case, output, runs):
    status = case.get("status") or "unknown"
    kind = "ok" if status in ("passed", "expected") else "warn" if status in ("skipped", "flaky") else "bad"
    body = ""
    if case.get("error"):
        body += f'<pre>{txt(short(case["error"]))}</pre>'
    if case.get("page"):
        body += '<p class="small muted">页面现场（保留原文件行号）</p><pre>' + txt(case["page"]) + "</pre>"
    if case.get("evidence"):
        body += links(case["evidence"], output, runs)
    if not body:
        body = '<p class="muted small">没有附加错误或附件。</p>'
    return (f'<details class="case"><summary><span class="id">{txt(case.get("id"))}</span>'
            f'<span class="title">{txt(case.get("title"))}</span><span class="pill {kind}">{txt(status)}</span></summary>'
            f'<div class="body">{body}</div></details>')


def local_cases(detail):
    report = detail["evaluation"].get("evidence", {}).get("results.json")
    if not report:
        return [], []
    warnings = []
    try:
        suites = read_json(Path(report)).get("suites", [])
        if not isinstance(suites, list):
            raise ValueError("results.json 缺少 suites")
    except (OSError, ValueError) as exc:
        return [], [str(exc)]
    cases = []

    def visit(suite):
        if not isinstance(suite, dict):
            return
        for spec in suite.get("specs") or []:
            if not isinstance(spec, dict):
                continue
            match = CASE_ID.search(str(spec.get("title") or spec.get("file") or ""))
            identity = match.group() if match else str(spec.get("title") or "未知")
            for test in spec.get("tests") or []:
                if not isinstance(test, dict):
                    continue
                raw = test.get("status") or "unknown"
                status = {"expected": "passed", "unexpected": "failed"}.get(raw, raw)
                item = {"id": identity, "title": spec.get("title"), "status": status}
                if status == "failed" and match:
                    evidence = _case(Path(detail["evaluation"]["path"]), identity, warnings)
                    matched = evidence.get("matches", [])
                    item["error"] = "\n\n".join(m.get("error", {}).get("text", "") for m in matched if m.get("error"))
                    item["page"] = "\n".join(f'{line["number"]}: {line["text"]}' for m in matched
                        for page in m.get("page_evidence", []) for line in page.get("lines", []))
                    item["evidence"] = [(a.get("name") or "附件", a.get("path")) for m in matched
                        for a in m.get("attachments", []) if a.get("exists")]
                cases.append(item)
        for child in suite.get("suites") or []:
            visit(child)

    for suite in suites:
        visit(suite)
    return cases, warnings


def local_run(path):
    detail = show_run(path)
    cases, warnings = local_cases(detail)
    evaluation = detail["evaluation"]
    score = evaluation.get("score")
    evidence = [(key, value) for key, value in detail["evidence"].items() if isinstance(value, str)]
    evidence += [("日志 · " + Path(value).name, value) for value in detail["evidence"].get("logs", [])]
    evidence += [("评测 · " + key, value) for key, value in evaluation.get("evidence", {}).items() if value]
    evidence += [("会话 · " + str(index + 1), item.get("native")) for index, item in enumerate(detail["sessions"]["native"])]
    evidence += [("反馈", path / "feedback.json")]
    generation = detail["generation"]
    if generation.get("phase_log"):
        evidence.append(("生成阶段日志", path / generation["phase_log"]))
    if evaluation.get("phase_log") and evaluation.get("path"):
        evidence.append(("评测阶段日志", Path(evaluation["path"]) / evaluation["phase_log"]))
    native_errors = []
    for session in detail["sessions"]["native"]:
        terminal = session.get("terminal") or {}
        if terminal.get("status") == "error" and terminal.get("error"):
            native_errors.append((f'原生会话错误（第 {terminal.get("line") or "?"} 行）', terminal["error"]["text"]))
    return {"kind": "Factory", "id": detail["id"], "key": f'factory-{detail["id"]}',
            "title": detail["id"], "subtitle": f'{detail["variant"] or "未知组合"} · {detail["task"] or "未知任务"}',
            "status": generation["status"], "stage": generation.get("phase"),
            "evaluation_status": evaluation.get("status"), "score": score,
            "platform_score": None, "observed": generation.get("updated_at"),
            "fields": [("生成状态", generation["status"], generation.get("phase")),
                       ("评测状态", evaluation.get("status"), evaluation.get("phase")),
                       ("组合", detail.get("variant"), "由旧配置推导" if detail.get("variant_inferred") else None),
                       ("任务", detail.get("task"), None),
                       ("生成退出码", generation.get("exit_code"), None),
                       ("评测 ID", evaluation.get("id"), None)],
            "errors": [("生成错误", generation.get("error", {}).get("text")) if generation.get("error") else None,
                       ("评测错误", evaluation.get("error", {}).get("text")) if evaluation.get("error") else None]
                      + native_errors,
            "steps": [("生成", generation.get("status"), [generation.get("failed_phase") or generation.get("phase")]),
                      ("评测", evaluation.get("status"), [evaluation.get("failed_phase") or evaluation.get("phase")])],
            "cases": cases, "evidence": evidence,
            "warnings": detail["warnings"] + warnings,
            "path": str(path)}


def hosted_runs(runs):
    rows = []
    warnings = []
    for inputs_path in sorted((runs / "competition").glob("**/hosted/*/inputs.json")):
        folder = inputs_path.parent
        if not all(path.resolve().is_relative_to(runs.resolve()) for path in (inputs_path, folder / "state.json")):
            warnings.append(f"{folder}: 归档路径越界")
            continue
        try:
            inputs, state = read_json(inputs_path), read_json(folder / "state.json")
            if any(inputs.get(key) != state.get(key) for key in ("competition_id", "package_sha256")):
                raise ValueError("inputs.json 与 state.json 身份不符")
            tasks = state.get("tasks")
            if not isinstance(tasks, dict):
                raise ValueError("state.json 缺少 tasks")
        except (OSError, ValueError) as exc:
            warnings.append(f"{folder}: {exc}")
            continue
        for task, item in sorted(tasks.items()):
            if not isinstance(item, dict) or not item.get("run_id"):
                continue
            if not isinstance(item["run_id"], str) or not re.fullmatch(r"[A-Za-z0-9_-]+", item["run_id"]):
                warnings.append(f"{folder}: 非法平台 run ID {item['run_id']!r}")
                continue
            if (not isinstance(task, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", task)):
                warnings.append(f"{folder}: 非法任务目录名 {task!r}")
                continue
            path = folder / "tasks" / task
            status_path = path / "status.json"
            local_warnings = []
            value = {}
            observed = item.get("observed_at")
            if status_path.exists() and not status_path.resolve().is_relative_to(runs.resolve()):
                local_warnings.append("归档 status 路径越界")
            elif status_path.exists():
                try:
                    wrapper = read_json(status_path)
                    candidate = wrapper.get("value")
                    if not isinstance(candidate, dict) or candidate.get("id") != item["run_id"]:
                        raise ValueError("归档 status 的平台 run ID 不符")
                    if candidate.get("requirement_id") not in (None, task):
                        raise ValueError("归档 status 的任务身份不符")
                    value = candidate
                    observed = observed or wrapper.get("observed_at")
                except (OSError, ValueError) as exc:
                    local_warnings.append(str(exc))
            else:
                local_warnings.append("尚无归档 status.json")
            platform = dict(item["platform_result"]) if isinstance(item.get("platform_result"), dict) else {}
            status_matches = value.get("status") in (None, item.get("remote_status"))
            if not status_matches:
                local_warnings.append("平台状态快照与控制状态不一致；不展示旧逐用例结果")
            platform["tests"] = value.get("tests") if status_matches else None
            for key in ("score", "passed_count", "failed_count"):
                if platform.get(key) is None:
                    platform[key] = value.get(key)
            platform["status"] = item.get("remote_status") or value.get("status")
            score = score_from_platform(platform)
            rows.append(platform_run("Competition", item["run_id"], task, inputs.get("variant") or folder.name,
                platform["status"], item.get("phase"), score, observed, value if status_matches else {},
                [("控制状态", folder / "state.json"), ("平台状态", status_path),
                 ("追踪", path / "traceability.json"), ("提交历史", path / "commit-history.json"),
                 ("应用现场", path / "analysis" / "official-stdout.log")]
                + [("日志 · " + p.stem, p) for p in sorted((path / "logs").glob("*.json"))],
                local_warnings, path))
    return rows, warnings


def platform_run(kind, run_id, task, variant, status, stage, score, observed, value, evidence, warnings, path):
    cases = []
    for test in value.get("tests", []) if isinstance(value.get("tests"), list) else []:
        if not isinstance(test, dict):
            continue
        match = CASE_ID.search(str(test.get("name") or test.get("file") or ""))
        cases.append({"id": match.group() if match else test.get("file") or "—",
                      "title": test.get("name") or test.get("file"),
                      "status": test.get("status") or "unknown", "error": test.get("error")})
    steps = value.get("steps") or []
    for step in steps if isinstance(steps, list) else []:
        if isinstance(step, dict) and step.get("status") not in ("completed", "pending"):
            stage = step.get("title") or step.get("key") or stage
            break
    errors = [("平台失败原因", value.get("failure_reason"))]
    visible_steps = []
    for step in steps if isinstance(steps, list) else []:
        if not isinstance(step, dict):
            continue
        raw_logs = step.get("logs")
        logs = [line for line in raw_logs if isinstance(line, str) and not line.startswith("Still working:")] if isinstance(raw_logs, list) else []
        visible_steps.append((step.get("title") or step.get("key"), step.get("status"), logs[-12:]))
    slug = re.sub(r"[^A-Za-z0-9_-]", "-", str(run_id))
    fingerprint = hashlib.sha1(str(path).encode()).hexdigest()[:10]
    return {"kind": kind, "id": run_id, "key": f"{kind.lower()}-{slug}-{fingerprint}",
            "title": run_id, "subtitle": f"{variant} · {task}", "status": status or "unknown", "stage": stage,
            "evaluation_status": status, "score": None, "platform_score": score, "observed": observed,
            "fields": [("平台状态", status, stage), ("组合", variant, None), ("任务", task, None),
                       ("平台分数", score["score"] if score else None, "终态且计数完整" if score else "未取得完整评分"),
                       ("开始时间", value.get("started_at"), None), ("结束时间", value.get("finished_at"), None)],
            "errors": errors, "steps": visible_steps, "cases": cases, "evidence": evidence, "warnings": warnings,
            "path": str(path)}


def playground_runs(runs):
    rows = []
    warnings = []
    for path in sorted((runs / "playground").glob("*/status.json")):
        if not path.resolve().is_relative_to(runs.resolve()):
            warnings.append(f"{path}: 归档路径越界")
            continue
        try:
            value = read_json(path)
            if value.get("id") != path.parent.name:
                raise ValueError("平台 run ID 与目录不符")
        except (OSError, ValueError) as exc:
            warnings.append(f"{path}: {exc}")
            continue
        folder = path.parent
        observation = folder / "observation.json"
        observed = None
        if observation.exists():
            try:
                observed = read_json(observation).get("status", {}).get("observed_at")
            except (OSError, ValueError, AttributeError) as exc:
                warnings.append(f"{observation}: {exc}")
        rows.append(platform_run("Playground", value["id"], value.get("requirement_id") or "未知任务",
            value.get("display_name") or "Playground", value.get("status"), None,
            score_from_platform(value), observed, value,
            [("平台状态", path), ("观测记录", observation), ("追踪", folder / "traceability.json"),
             ("提交历史", folder / "commit-history.json")]
            + [("日志 · " + p.stem, p) for p in sorted((folder / "logs").glob("*.json"))], [], folder))
    return rows, warnings


def score_text(run):
    score = run.get("score") or run.get("platform_score")
    if not score:
        return "未知"
    return f'{score["passed"]}/{score["total"]}'


def render_shell(title, content):
    return ('<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<meta name="color-scheme" content="light"><title>' + txt(title) + '</title><style>' + STYLE + '</style></head><body><main>' + content + '</main></body></html>')


def render_index(rows, warnings, output, generated):
    counts = {kind: sum(row["kind"] == kind for row in rows) for kind in ("Factory", "Competition", "Playground")}
    summary = '<div class="stats">' + ''.join(f'<div class="stat"><strong>{number}</strong><span>{txt(label)}</span></div>'
        for label, number in (("run 总数", len(rows)), *counts.items())) + '</div>'
    body = ('<div class="hero"><span class="eyebrow">Factory26 · Run Viewer</span><h1>运行诊断</h1>'
            '<p class="muted">从状态进入失败用例，再打开归档现场。页面只反映生成时已有的证据。</p>'
            f'<div class="small">生成时间：{txt(generated)} · 刷新：重新运行 <code>python3 scripts/run_viewer.py</code></div></div>' + summary)
    body += '<div class="toolbar"><input id="filter" type="search" placeholder="搜索 run ID、组合、任务或状态" aria-label="搜索 run"><span id="visible"></span></div>'
    body += '<div class="panel table-wrap" style="padding:4px 15px"><table><thead><tr><th>Run</th><th>来源 / 任务</th><th>状态</th><th>完整评分</th><th>观测时间</th></tr></thead><tbody>'
    for row in rows:
        score = row.get("score") or row.get("platform_score")
        failures = f'<div class="meta">{score["failed"]} 项失败</div>' if score and score.get("failed") else ""
        body += (f'<tr class="run-row"><td><a class="runname" href="{txt(row["key"])}.html">{txt(row["title"])}</a>'
                 f'<div class="meta">{txt(row["subtitle"])}</div></td><td>{txt(row["kind"])}</td>'
                 f'<td>{status_pill(row["status"])}<div class="meta">{txt(row.get("stage"))}</div>'
                 + (f'<div class="meta">评测 {txt(row["evaluation_status"])}</div>' if row["kind"] == "Factory" else "")
                 + f'</td><td class="nowrap">{txt(score_text(row))}{failures}</td><td class="small">{txt(time_text(row.get("observed")))}</td></tr>')
    body += '</tbody></table></div>'
    body += ''.join(f'<div class="warning">{txt(warning)}</div>' for warning in warnings)
    body += '<script>const q=document.querySelector("#filter"),rows=[...document.querySelectorAll(".run-row")],n=document.querySelector("#visible");function filter(){let value=q.value.toLocaleLowerCase(),count=0;for(const row of rows){row.hidden=!row.textContent.toLocaleLowerCase().includes(value);if(!row.hidden)count++}n.textContent=`${count} 条`}q.addEventListener("input",filter);filter()</script>'
    (output / "index.html").write_text(render_shell("Factory26 · 运行诊断", body))


def render_detail(run, output, runs, generated):
    score = run.get("score") or run.get("platform_score")
    percent = score["passed"] / score["total"] * 100 if score else None
    body = (f'<a class="back" href="index.html">← 返回全部 run</a><div class="hero"><span class="eyebrow">{txt(run["kind"])} · {txt(run["subtitle"])}</span>'
            f'<h1>{txt(run["title"])}</h1><div>{status_pill(run["status"])} &nbsp; 阶段：{txt(run.get("stage"))}</div>'
            f'<p class="muted small">来源：{txt(Path(run["path"]).relative_to(runs))} · 观测时间：{txt(time_text(run.get("observed")))} · 页面生成：{txt(generated)}</p></div>')
    body += '<section class="panel"><h2>状态与评分</h2><div class="grid">' + ''.join(field(*item) for item in run["fields"]) + '</div>'
    if score:
        body += f'<div class="bar {"bad" if percent < 50 else ""}" role="img" aria-label="通过 {score["passed"]} / {score["total"]}"><i style="width:{percent:.1f}%"></i></div>'
        body += f'<p class="small muted">完整测试：{score["passed"]} 通过 / {score["total"]} 总计'
        if run.get("platform_score"):
            body += f' · 平台分数 {txt(score["score"])}'
        body += '</p>'
    else:
        body += '<p class="warning">没有完整评分；运行中、生成失败或评测中断均不推断为零分。</p>'
    body += '</section>'
    errors = [item for item in run["errors"] if item and item[1]]
    if errors:
        body += '<section class="panel"><h2>错误与阻塞</h2>' + ''.join(f'<h3>{txt(label)}</h3><pre>{txt(short(value))}</pre>' for label, value in errors) + '</section>'
    if run.get("steps"):
        body += '<section class="panel"><h2>执行阶段</h2>'
        for title, status, logs in run["steps"]:
            body += f'<details class="case"><summary><span class="title">{txt(title)}</span>{status_pill(status)}</summary><div class="body">'
            body += '<pre>' + txt("\n".join(str(line) for line in logs if line) or "无阶段日志摘要") + '</pre></div></details>'
        body += '</section>'
    cases = sorted(run["cases"], key=lambda item: (item["status"] in ("passed", "expected"), item["id"]))
    body += f'<section class="panel"><h2>用例 <span class="muted small">{len(cases)} 项</span></h2>'
    body += '<p class="section-note">失败项排在前面。页面片段与错误是现场事实，不自动判定根因。</p>'
    body += ''.join(case_html(case, output, runs) for case in cases) if cases else '<div class="empty">尚无逐用例结果</div>'
    body += '</section><section class="panel"><h2>原始证据</h2>' + links(run["evidence"], output, runs) + '</section>'
    if run["warnings"]:
        body += '<section class="panel"><h2>证据警告</h2>' + ''.join(f'<div class="warning">{txt(warning)}</div>' for warning in run["warnings"]) + '</section>'
    (output / f'{run["key"]}.html').write_text(render_shell(run["title"] + " · Factory26", body))


def build(root=ROOT):
    root = Path(root).resolve()
    runs = root / "runs"
    output = runs / "viewer"
    output.mkdir(parents=True, exist_ok=True)
    warnings = []
    rows = []
    for brief in list_runs(root):
        try:
            path = Path(brief["path"]).resolve()
            if not path.is_relative_to(runs):
                raise ValueError("run 目录越界")
            rows.append(local_run(path))
        except (OSError, ValueError, TypeError, KeyError) as exc:
            warnings.append(f'{brief["id"]}: {exc}')
    hosted, hosted_warnings = hosted_runs(runs)
    playground, playground_warnings = playground_runs(runs)
    rows.extend(hosted + playground)
    warnings.extend(hosted_warnings + playground_warnings)
    rows.sort(key=lambda row: ((time_value(row.get("observed")) or datetime.fromtimestamp(0).astimezone()).timestamp(), row["id"]), reverse=True)
    generated = datetime.now().astimezone().isoformat(timespec="seconds")
    for row in rows:
        render_detail(row, output, runs, generated)
    render_index(rows, warnings, output, generated)
    current = {f'{row["key"]}.html' for row in rows} | {"index.html"}
    for page in output.glob("*.html"):
        if page.name not in current and page.name.startswith(("factory-", "competition-", "playground-")):
            page.unlink()
    return output / "index.html", len(rows), warnings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="Factory26 仓库根目录")
    args = parser.parse_args()
    path, count, warnings = build(args.root)
    print(f"{path} · {count} 个 run · {len(warnings)} 条发现警告")


if __name__ == "__main__":
    main()
