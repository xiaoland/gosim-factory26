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

from .inspect_runs import _case, list_runs, show_run


ROOT = Path(__file__).resolve().parents[2]
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
.process-session{margin:12px 0}.process-list{max-height:680px;overflow:auto;border:1px solid #e1e7e2;border-radius:10px}.process-row{display:grid;grid-template-columns:135px minmax(120px,1fr) 100px;gap:12px;align-items:start;padding:10px 13px;border-bottom:1px solid #eef1ee;font-size:13px}.process-row[hidden]{display:none}.process-row:last-child{border-bottom:0}.process-row:hover{background:#f8faf8}.process-row .when{color:#687975;font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:11px;overflow-wrap:anywhere}.process-row .action{overflow-wrap:anywhere}.process-row .source{font-size:11px;text-align:right}.process-meta{font-size:12px;color:#687975;overflow-wrap:anywhere}.process-filter{width:100%;border:1px solid #cbd7cf;border-radius:10px;padding:10px 12px;font:inherit;margin:0 0 10px}
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
    if not (path.is_relative_to(runs.resolve()) or
            path.is_relative_to((runs.parent / "analysis").resolve())) or not path.exists():
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


def excerpt(value, limit=180):
    """Keep local snapshots useful without copying common credential shapes."""
    value = re.sub(r"(?i)\bBearer\s+\S+", "Bearer [隐藏]", str(value or ""))
    value = re.sub(r"\bsk-[A-Za-z0-9_-]{8,}", "[隐藏]", value)
    value = re.sub(r"(?i)\b([A-Za-z0-9_]*(?:api[_-]?key|token|password|secret))(\s*[:=]\s*|\s+)([^\s,;]+)",
                   r"\1\2[隐藏]", value)
    return short(value, limit)


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


def tool_summary(name, arguments):
    if isinstance(arguments, str):
        try:
            arguments = json.loads(arguments)
        except ValueError:
            arguments = {}
    arguments = arguments if isinstance(arguments, dict) else {}
    target = arguments.get("path") or arguments.get("file_path")
    if isinstance(target, str):
        return f"{name} · {excerpt(target, 130)}"
    command = arguments.get("command") or arguments.get("cmd")
    if isinstance(command, str):
        return f"{name} · {excerpt(command.replace(chr(10), ' ↵ '), 130)}"
    return str(name or "未知工具")


def result_status(result, codex=False):
    if codex:
        output = result.get("output")
        match = re.search(r"Process exited with code (\d+)", output[:500] if isinstance(output, str) else "")
        return f"退出码 {match.group(1)}" if match else "已返回"
    return "工具报错" if result.get("isError") else "已返回"


def native_process(run, sessions):
    result = {"kind": "native", "sessions": [], "warnings": []}
    for index, session in enumerate(sessions):
        source = session.get("native")
        item = {"number": index + 1, "source": source, "integrity": session.get("integrity"),
                "work_item": f'{session.get("work_item_kind")} #{session.get("work_item_id")}'
                if session.get("integrity") == "verified" and session.get("work_item_kind") else None,
                "status": session.get("status"), "turns": session.get("turns") or [], "events": [],
                "tool_count": 0, "unmatched": 0, "invalid": 0, "first": None, "last": None}
        result["sessions"].append(item)
        if not source or session.get("integrity") == "mismatch":
            result["warnings"].append(f"第 {index + 1} 段原生会话缺失或哈希不符，过程不可用")
            continue
        path = Path(source).resolve()
        if not path.is_file() or not path.is_relative_to(run.resolve()):
            result["warnings"].append(f"第 {index + 1} 段原生会话路径不可用")
            continue
        calls = {}
        recognized = 0
        try:
            with path.open() as stream:
                for line_number, line in enumerate(stream, 1):
                    try:
                        record = json.loads(line)
                    except ValueError:
                        item["invalid"] += 1
                        continue
                    if not isinstance(record, dict):
                        item["invalid"] += 1
                        continue
                    timestamp = record.get("timestamp")
                    if timestamp:
                        item["first"] = item["first"] or timestamp
                        item["last"] = timestamp
                    kind = record.get("type")
                    if kind == "message":
                        message = record.get("message") or {}
                        if not isinstance(message, dict):
                            item["invalid"] += 1
                            continue
                        recognized += 1
                        if message.get("role") == "assistant":
                            blocks = message.get("content") or []
                            if not isinstance(blocks, list):
                                continue
                            note = " ".join(block.get("text", "") for block in blocks
                                            if isinstance(block, dict) and block.get("type") == "text" and isinstance(block.get("text"), str))
                            if note.strip():
                                item["events"].append({"kind": "note", "time": timestamp, "line": line_number,
                                                       "action": excerpt(note, 260)})
                            for block in blocks:
                                if not isinstance(block, dict) or block.get("type") != "toolCall":
                                    continue
                                event = {"kind": "tool", "time": timestamp, "line": line_number,
                                         "action": tool_summary(block.get("name"), block.get("arguments")),
                                         "result_line": None, "result": "无归档结果"}
                                item["events"].append(event)
                                item["tool_count"] += 1
                                call_id = block.get("id")
                                if isinstance(call_id, str) and call_id:
                                    calls[call_id] = event
                        elif message.get("role") == "toolResult":
                            call_id = message.get("toolCallId")
                            event = calls.get(call_id) if isinstance(call_id, str) else None
                            if event and event["result_line"] is None:
                                event["result_line"] = line_number
                                event["result"] = result_status(message)
                            else:
                                item["unmatched"] += 1
                    elif kind == "response_item":
                        payload = record.get("payload") or {}
                        if not isinstance(payload, dict):
                            item["invalid"] += 1
                            continue
                        recognized += 1
                        if payload.get("type") == "function_call":
                            event = {"kind": "tool", "time": timestamp, "line": line_number,
                                     "action": tool_summary(payload.get("name"), payload.get("arguments")),
                                     "result_line": None, "result": "无归档结果"}
                            item["events"].append(event)
                            item["tool_count"] += 1
                            call_id = payload.get("call_id")
                            if isinstance(call_id, str) and call_id:
                                calls[call_id] = event
                        elif payload.get("type") == "function_call_output":
                            call_id = payload.get("call_id")
                            event = calls.get(call_id) if isinstance(call_id, str) else None
                            if event and event["result_line"] is None:
                                event["result_line"] = line_number
                                event["result"] = result_status(payload, codex=True)
                            else:
                                item["unmatched"] += 1
                        elif payload.get("type") == "message" and payload.get("role") == "assistant":
                            blocks = payload.get("content") or []
                            if not isinstance(blocks, list):
                                continue
                            note = " ".join(block.get("text", "") for block in blocks
                                            if isinstance(block, dict) and block.get("type") == "output_text" and isinstance(block.get("text"), str))
                            if note.strip():
                                item["events"].append({"kind": "note", "time": timestamp, "line": line_number,
                                                       "action": excerpt(note, 260)})
        except OSError as exc:
            result["warnings"].append(f"第 {index + 1} 段原生会话读取失败：{exc}")
        if not recognized:
            result["warnings"].append(f"第 {index + 1} 段原生会话格式暂不支持，仅保留原始证据")
        missing = sum(event["result_line"] is None for event in item["events"] if event["kind"] == "tool")
        item["unmatched"] += missing
    if not result["sessions"]:
        result["warnings"].append("没有归档的原生会话，无法还原 Agent 内部过程")
    return result


def platform_process(folder, runs):
    result = {"kind": "platform", "events": [], "raw": 0, "heartbeats": 0,
              "missing_id": 0, "warnings": []}
    chunks = []
    for path in (folder / "logs").glob("*.json"):
        if not path.resolve().is_relative_to(runs.resolve()):
            result["warnings"].append(f"日志路径越界：{path.name}")
            continue
        try:
            wrapper = read_json(path)
        except (OSError, ValueError) as exc:
            result["warnings"].append(f"{path.name}: {exc}")
            continue
        value = wrapper.get("value", wrapper)
        if not isinstance(value, dict) or not isinstance(value.get("runner_events"), list):
            result["warnings"].append(f"{path.name}: 无可读的 runner_events")
            continue
        events = value["runner_events"]
        first_time = next((str(e.get("timestamp")) for e in events if isinstance(e, dict) and e.get("timestamp")), "")
        chunks.append((wrapper.get("observed_at") or 0, first_time, path.name, path, events))
    chunks.sort(key=lambda part: (time_value(part[0]).timestamp() if time_value(part[0]) else 0, part[1], part[2]))
    unique = {}
    order = 0
    for _, _, _, path, events in chunks:
        for event in events:
            order += 1
            result["raw"] += 1
            if not isinstance(event, dict):
                result["missing_id"] += 1
                continue
            event_id = event.get("event_id")
            if not isinstance(event_id, str) or not event_id:
                result["missing_id"] += 1
                continue
            unique[event_id] = {"id": event_id, "order": order, "time": str(event.get("timestamp") or "未知"),
                                "stage": str(event.get("stage") or "未知阶段"),
                                "status": str(event.get("status") or "未知"),
                                "summary": excerpt(event.get("summary"), 240),
                                "heartbeat": event.get("heartbeat") is True, "source": path}
    ordered = sorted(unique.values(), key=lambda e: (e["time"], e["order"]))
    result["heartbeats"] = sum(event["heartbeat"] for event in ordered)
    result["unique"] = len(ordered)
    result["events"] = [event for event in ordered if not event["heartbeat"]]
    if not chunks:
        result["warnings"].append("没有归档平台事件；仅能查看阶段状态")
    if result["missing_id"]:
        result["warnings"].append(f'{result["missing_id"]} 条平台事件缺少 ID 或格式错误，未并入时间线')
    return result


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
                if detail.get('producer') == 'local_experiment':
                    item['error'] = '\n\n'.join(str(error.get('message') or error)
                        for result in test.get('results', []) for error in result.get('errors', []))
                    item['evidence'] = [('Playwright 原始报告', report)]
                elif status == "failed" and match:
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


def naming_fields(labels):
    return [(title, labels[key], None) for key, title in
            (("experiment_key", "实验编号"), ("case", "配置行"), ("operation", "执行类型"), ("run_name", "运行名"))
            if labels.get(key)]


def experiment_run(path, detail):
    cases, warnings = local_cases(detail)
    generation, deployment, evaluation = (detail[k] for k in ('generation', 'deployment', 'evaluation'))
    evidence = list(detail['evidence'].items()) + [("分析", item['path']) for item in detail.get('analysis', [])]
    return {'kind': 'Local experiment', 'id': detail['id'],
            'key': 'experiment-'+hashlib.sha256(str(path).encode()).hexdigest()[:16],
            'title': detail.get('labels', {}).get('run_name') or detail['id'],
            'subtitle': f"{detail['variant']} · {detail['competition']} · {detail['task']}",
            'status': detail['status'], 'stage': detail['stage'], 'evaluation_status': evaluation['status'],
            'score': evaluation['score'], 'platform_score': None, 'observed': detail['observed_at'],
            'fields': [('实验状态', detail['status'], None), ('生成', generation['status'], None),
                       ('部署', deployment['status'], None), ('评分', evaluation['status'], None),
                       ('外层进程退出码', detail['runner_exit_code'], '退出码不是得分'),
                       ('Run ID', detail['id'], None)] + naming_fields(detail.get('labels', {})),
            'errors': [('执行', detail['error']), ('生成', (generation.get('error') or {}).get('text')),
                       ('部署', deployment.get('error')), ('评分', (evaluation.get('error') or {}).get('text'))],
            'steps': [], 'cases': cases, 'evidence': evidence,
            'process': {'kind': 'evidence', 'paths': [('Factory 生成目录', p) for p in detail['factory_runs']]
                        + [('原生会话', p) for p in detail['native']] + [('应用', p) for p in detail['applications']]},
            'warnings': detail['warnings']+warnings, 'path': str(path)}


def local_run(path):
    detail = show_run(path)
    if detail.get('producer') == 'local_experiment':
        return experiment_run(path, detail)
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
            "cases": cases, "evidence": evidence, "process": native_process(path, detail["sessions"]["native"]),
            "warnings": detail["warnings"] + warnings,
            "path": str(path)}


def hosted_runs(runs):
    rows = []
    warnings = []
    journals = []
    # A journal's saved type identifies it; experiment directory names are only navigation.
    for folder, directories, files in os.walk(runs):
        directories[:] = [name for name in directories if name not in
                          {'node_modules', '.git', 'inputs', 'workspace', 'work', 'artifacts',
                           'runtime', 'viewer', 'sources', 'source', 'source-snapshots', 'application', 'native', 'submission'}]
        if 'inputs.json' in files and 'state.json' in files:
            journals.append(Path(folder) / 'inputs.json')
            directories.clear()
        elif 'run.json' in files:
            directories.clear()
    for inputs_path in sorted(journals):
        folder = inputs_path.parent
        if not all(path.resolve().is_relative_to(runs.resolve()) for path in (inputs_path, folder / "state.json")):
            warnings.append(f"{folder}: 归档路径越界")
            continue
        try:
            inputs, state = read_json(inputs_path), read_json(folder / "state.json")
            if inputs.get('venue') != 'hosted':
                continue
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
            rows.append(platform_run("Competition", item["run_id"], task,
                item.get('labels', {}).get('variant') or inputs.get("variant") or "未知实现",
                platform["status"], item.get("phase"), score, observed, value if status_matches else {},
                [("控制状态", folder / "state.json"), ("平台状态", status_path),
                 ("追踪", path / "traceability.json"), ("提交历史", path / "commit-history.json"),
                 ("应用现场", path / "analysis" / "official-stdout.log")]
                + [("日志 · " + p.stem, p) for p in sorted((path / "logs").glob("*.json"))],
                local_warnings, path, runs, labels=item.get('labels', {})))
    return rows, warnings


def platform_run(kind, run_id, task, variant, status, stage, score, observed, value, evidence, warnings, path, runs, *, labels=None):
    labels = labels or {}
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
            "title": labels.get('run_name') or run_id, "subtitle": f"{variant} · {task}", "status": status or "unknown", "stage": stage,
            "evaluation_status": status, "score": None, "platform_score": score, "observed": observed,
            "fields": [("平台状态", status, stage), ("组合", variant, None), ("任务", task, None),
                       ("平台分数", score["score"] if score else None, "终态且计数完整" if score else "未取得完整评分"),
                       ("开始时间", value.get("started_at"), None), ("结束时间", value.get("finished_at"), None),
                       ("Run ID", run_id, None)] + naming_fields(labels),
            "errors": errors, "steps": visible_steps, "cases": cases, "evidence": evidence, "warnings": warnings,
            "process": platform_process(path, runs),
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
        submission = read_json(folder / 'submission.json') if (folder / 'submission.json').is_file() else {}
        rows.append(platform_run("Playground", value["id"], value.get("requirement_id") or "未知任务",
            submission.get('labels', {}).get('variant') or value.get("display_name") or "未知实现", value.get("status"), None,
            score_from_platform(value), observed, value,
            [("平台状态", path), ("观测记录", observation), ("追踪", folder / "traceability.json"),
             ("提交历史", folder / "commit-history.json")]
            + [("日志 · " + p.stem, p) for p in sorted((folder / "logs").glob("*.json"))], [], folder, runs,
            labels=submission.get('labels', {})))
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
            '<p class="muted">从状态进入执行过程、失败用例和归档现场。页面只反映生成时已有的证据。</p>'
            f'<div class="small">生成时间：{txt(generated)} · 刷新：重新运行 <code>python3 -m lab.analysis.run_viewer</code></div></div>' + summary)
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


def render_process(process, output, runs):
    body = '<section class="panel" id="process"><h2>执行过程</h2>'
    if process['kind'] == 'evidence':
        return body + links(process['paths'], output, runs) + '</section>'
    if process["kind"] == "native":
        sessions = process["sessions"]
        body += ('<p class="section-note">按物理会话和工作项查看 Agent 的可见消息与工具动作。'
                 'Issue 和 PR 可能并发，下面的顺序不是单一因果链；推理、原始提示词及完整工具输出未嵌入页面。</p>')
        body += f'<p class="process-meta">{len(sessions)} 段会话 · {sum(s["tool_count"] for s in sessions)} 次工具调用</p>'
        body += '<input class="process-filter" type="search" placeholder="筛选动作、文件或结果" aria-label="筛选执行过程">'
        for session in sessions:
            label = session["work_item"] or f'会话 {session["number"]} · 工作项归属未核实'
            integrity = {"verified": "哈希已核实", "unverified": "无清单校验", "mismatch": "哈希不符"}.get(
                session["integrity"], "未知")
            failures = sum(event["result"] == "工具报错" or
                           (event["result"].startswith("退出码 ") and event["result"] != "退出码 0")
                           for event in session["events"] if event["kind"] == "tool")
            error_badge = f'<span class="pill bad">{failures} 次工具异常</span>' if failures else ""
            body += (f'<details class="case process-session" {"open" if session["number"] == 1 else ""}>'
                     f'<summary><span class="title">{txt(label)} · 第 {session["number"]} 段</span>'
                     f'<span class="pill">{txt(integrity)}</span>'
                     f'{error_badge}'
                     f'<span class="pill">{session["tool_count"]} 次工具</span></summary><div class="body">')
            if session["source"]:
                body += '<p class="process-meta">原生归档：' + file_link(
                    session["source"], Path(session["source"]).name, output, runs) + '</p>'
            body += (f'<p class="process-meta">会话状态：{txt(session["status"])} · '
                     f'时间：{txt(session["first"])} → {txt(session["last"])} · '
                     f'未配对结果：{session["unmatched"]} · 无效行：{session["invalid"]}</p>')
            for turn in session["turns"]:
                if isinstance(turn, dict):
                    body += (f'<p class="process-meta">Braid turn {txt(turn.get("braid_turn_id"))} · '
                             f'Provider turn {txt(turn.get("provider_turn_id"))} · '
                             f'触发：{txt(turn.get("trigger_kind"))}</p>')
            body += '<div class="process-list">'
            for event in session["events"]:
                source_label = f'行 {event["line"]}'
                if event["kind"] == "tool" and event["result_line"]:
                    source_label += f' / {event["result_line"]}'
                link = file_link(session["source"], source_label, output, runs)
                label = "工具" if event["kind"] == "tool" else "Agent 说明"
                if event["kind"] == "tool":
                    status = event["result"]
                    kind = "bad" if status == "工具报错" or (status.startswith("退出码 ") and status != "退出码 0") else "warn" if status == "无归档结果" else ""
                    result = f' <span class="pill {kind}">{txt(status)}</span>'
                else:
                    result = ""
                body += (f'<div class="process-row"><span class="when">{txt(event["time"])}</span>'
                         f'<span class="action"><strong>{label}</strong> · {txt(event["action"])}'
                         f'{result}</span><span class="source">{link}</span></div>')
            if not session["events"]:
                body += '<div class="empty">没有可解析的过程记录</div>'
            body += '</div></div></details>'
    else:
        events = process["events"]
        unique = process["unique"]
        dropped = process["raw"] - process["missing_id"] - unique
        body += ('<p class="section-note">这里是平台归档的阶段事件，时间保留平台原值。'
                 '平台未归档 Agent 的内部工具调用，只有心跳的区段不能据此判断实现进展。</p>')
        body += (f'<p class="process-meta">原始事件 {process["raw"]} · 去重后 {unique} · '
                 f'合并重复 {dropped} · 可见 {len(events)} · 心跳 {process["heartbeats"]} · '
                 f'缺失 ID {process["missing_id"]}</p>')
        body += '<input class="process-filter" type="search" placeholder="筛选阶段、事件或状态" aria-label="筛选执行过程">'
        body += '<div class="process-list">'
        for event in events:
            link = file_link(event["source"], Path(event["source"]).stem, output, runs)
            body += (f'<div class="process-row"><span class="when">{txt(event["time"])}</span>'
                     f'<span class="action"><strong>{txt(event["stage"])}</strong> · '
                     f'{txt(event["summary"])} · {status_pill(event["status"])}'
                     f'<span class="meta">事件 ID：{txt(event["id"])}</span></span>'
                     f'<span class="source">{link}</span></div>')
        if not events:
            body += '<div class="empty">没有非心跳的平台事件；Agent 内部过程未归档</div>'
        body += '</div>'
    for warning in process["warnings"]:
        body += f'<div class="warning">{txt(warning)}</div>'
    body += ('<script>const p=document.querySelector("#process"),q=p.querySelector(".process-filter");'
             'q.addEventListener("input",()=>{const value=q.value.toLocaleLowerCase();'
             'for(const row of p.querySelectorAll(".process-row"))row.hidden=!row.textContent.toLocaleLowerCase().includes(value);'
             'if(value)for(const group of p.querySelectorAll(".process-session"))'
             'group.open=[...group.querySelectorAll(".process-row")].some(row=>!row.hidden)});</script></section>')
    return body


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
        body += '<section class="panel"><h2>错误与阻塞</h2>' + ''.join(f'<h3>{txt(label)}</h3><pre>{txt(value)}</pre>' for label, value in errors) + '</section>'
    if run.get("steps"):
        body += '<section class="panel"><h2>执行阶段</h2>'
        for title, status, logs in run["steps"]:
            body += f'<details class="case"><summary><span class="title">{txt(title)}</span>{status_pill(status)}</summary><div class="body">'
            body += '<pre>' + txt("\n".join(str(line) for line in logs if line) or "无阶段日志摘要") + '</pre></div></details>'
        body += '</section>'
    body += render_process(run["process"], output, runs)
    cases = sorted(run["cases"], key=lambda item: (item["status"] in ("passed", "expected"), item["id"]))
    body += f'<section class="panel"><h2>用例 <span class="muted small">{len(cases)} 项</span></h2>'
    body += '<p class="section-note">失败项排在前面。页面片段与错误是现场事实，不自动判定根因。</p>'
    body += ''.join(case_html(case, output, runs) for case in cases) if cases else '<div class="empty">尚无逐用例结果</div>'
    body += '</section><section class="panel"><h2>原始证据</h2>' + links(run["evidence"], output, runs) + '</section>'
    if run["warnings"]:
        body += '<section class="panel"><h2>证据警告</h2>' + ''.join(f'<div class="warning">{txt(warning)}</div>' for warning in run["warnings"]) + '</section>'
    (output / f'{run["key"]}.html').write_text(render_shell(run["title"] + " · Factory26", body))


def build(root=ROOT, output=None):
    root = Path(root).resolve()
    runs = root / "runs"
    output = Path(output).resolve() if output else runs / "viewer"
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
        if page.name not in current and page.name.startswith(("factory-", "competition-", "playground-", "experiment-")):
            page.unlink()
    return output / "index.html", len(rows), warnings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="Factory26 仓库根目录")
    parser.add_argument("--output", type=Path, help="网站输出目录；默认 ROOT/runs/viewer")
    args = parser.parse_args()
    path, count, warnings = build(args.root, args.output)
    print(f"{path} · {count} 个 run · {len(warnings)} 条发现警告")


if __name__ == "__main__":
    main()
