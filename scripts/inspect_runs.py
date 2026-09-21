"""只读实验摘要与证据入口；失败时提取已核实原生终止信息，不推断工具调用因果。"""
import hashlib
import json
import os
from pathlib import Path
import re
import time


ERROR_LIMIT = 4000
ANSI = re.compile(r"\x1b(?:\[[0-?]*[ -/]*[@-~]|\][^\x07]*(?:\x07|\x1b\\))")


def _read(path, warnings):
    try:
        value = json.loads(path.read_text())
        if not isinstance(value, dict):
            raise ValueError("顶层必须是 JSON 对象")
        return value
    except (OSError, ValueError) as exc:
        warnings.append(f"{path}: {exc}")
        return {}


def _error(value):
    clean = ANSI.sub("", str(value or ""))
    clean = re.sub(r"[\x00-\x08\x0b-\x1f\x7f]", "", clean)
    return {"text": clean[:ERROR_LIMIT], "truncated": len(clean) > ERROR_LIMIT}


def _existing(path):
    return str(path) if path.exists() else None


def _digest(path, warnings):
    try:
        with path.open("rb") as source:
            return hashlib.file_digest(source, "sha256").hexdigest()
    except OSError as exc:
        warnings.append(f"{path}: {exc}")
        return None


def _variant(metadata, config):
    if isinstance(metadata.get("variant"), str) and metadata["variant"]:
        return metadata["variant"], False
    backend = config.get("backend") or metadata.get("backend")
    workflow = config.get("workflow", "single")
    svc = config.get("svc", False)
    if backend not in ("pi", "codex") or workflow not in ("single", "braid") or not isinstance(svc, bool):
        return None, True
    name = backend + ("-svc" if svc else "-baseline")
    return name + ("-braid" if workflow == "braid" else ""), True


def _evaluation(folder, warnings, benchmark_revision=None):
    result = {"id": None, "path": None, "status": "unknown", "phase": None,
              "phase_started_at": None, "updated_at": None, "phase_log": None, "failed_phase": None,
              "score": None, "error": None}
    if folder is None:
        return result
    summary = _read(folder / "summary.json", warnings)
    identities = [("evaluation_id", folder.name), ("run_id", folder.parent.parent.name)]
    if benchmark_revision is not None:
        identities.append(("benchmark_revision", benchmark_revision))
    if summary.get("application_sha256"):
        warning_count = len(warnings)
        hashes = _read(folder.parent.parent / "application-hashes.json", warnings)
        identities.append(("application_sha256", hashlib.sha256(json.dumps(hashes, sort_keys=True, separators=(",", ":")).encode()).hexdigest() if len(warnings) == warning_count else None))
    for key, expected in identities:
        if summary.get(key) is not None and summary[key] != expected:
            warnings.append(f"{folder / 'summary.json'}: {key} 与目录身份不符，拒绝关联")
            result.update(id=folder.name, path=str(folder), status="identity_mismatch")
            return result
    result.update(id=folder.name, path=str(folder), status=summary.get("status") or "unknown",
                  **{key: summary.get(key) for key in ("phase", "phase_started_at", "updated_at", "phase_log", "failed_phase")})
    result.update({key: summary.get(key) for key in ("evaluation_id", "run_id", "application_sha256", "benchmark_revision")})
    if summary.get("error"):
        result["error"] = _error(summary["error"])
    # 中断产生的局部计数不是完整分数；也不能回退到上一次成功评测。
    if result["status"] == "completed":
        counts = {key: summary.get(key) for key in ("passed", "failed", "flaky", "skipped", "total")}
        valid = all(type(value) is int and value >= 0 for value in counts.values())
        if valid and counts["total"] > 0 and sum(counts[key] for key in ("passed", "failed", "flaky", "skipped")) == counts["total"] and not summary.get("errors"):
            result["score"] = dict(counts, pass_rate=counts["passed"] / counts["total"])
        else:
            warnings.append(f"{folder / 'summary.json'}: completed 缺少有效完整计数，分数未知")
    return result


def _analysis(run, warnings):
    root = run / "analysis"
    folders = sorted(path for path in root.glob("*") if path.is_dir() and not path.name.startswith("."))
    if any((root / name).exists() for name in ("overview.json", "evidence-v4.zip", "evidence.zip")):
        folders.insert(0, root)
    result = []
    for folder in folders:
        overview = _read(folder / "overview.json", warnings)
        result.append({"id": folder.name if folder != root else "legacy", "path": str(folder),
                       "status": overview.get("status") or "unknown",
                       "coverage": overview.get("coverage"), "issues": overview.get("issues"),
                       "evidence": _existing(folder / "evidence-v4.zip") or _existing(folder / "evidence.zip"),
                       "overview": _existing(folder / "overview.json"), "profile": _existing(folder / "profile.json")})
    return result


def _summary(run, evaluation=None):
    warnings = []
    metadata = _read(run / "run.json", warnings)
    config = _read(run / "config.json", warnings)
    variant, inferred = _variant(metadata, config)
    folders = sorted(path for path in (run / "evaluation").glob("*") if path.is_dir())
    selected = folders[-1] if folders else None
    if evaluation is not None:
        selected = Path(evaluation)
        selected = run / "evaluation" / selected if len(selected.parts) == 1 else selected.resolve()
        if selected not in folders:
            raise ValueError(f"评测目录不属于此 run 或不存在: {evaluation}")
    generation = {key: metadata.get(key) for key in
                  ("phase", "phase_started_at", "updated_at", "phase_log", "failed_phase", "started_at", "generation_finished_at", "generation_seconds", "recovery")}
    generation.update(status=metadata.get("status") or "unknown",
                      exit_code=metadata.get("process_exit_code", metadata.get("agent_exit_code")),
                      error=_error(metadata["error"]) if metadata.get("error") else None)
    remote = None
    remote_path = run / "remote-evaluation.json"
    if selected and (run / "remote-evaluations" / f"{selected.name}.json").exists():
        remote_path = run / "remote-evaluations" / f"{selected.name}.json"
    if remote_path.exists():
        data = _read(remote_path, warnings)
        if remote_path.parent.name == "remote-evaluations" and data.get("attempt") != selected.name:
            warnings.append(f"{remote_path}: 远程评测身份不符，拒绝关联")
            data = {}
        elif evaluation is not None and data.get("attempt") != selected.name:
            data = {}
    else:
        data = {}
    if data:
        remote = {key: data.get(key) for key in ("phase", "host", "remote_run", "updated_at", "phase_log", "attempt", "summary", "observed_at", "observation_error", "failed_phase")}
        remote["error"] = _error(data["error"]) if data.get("error") else None
        remote["path"] = str(remote_path)
    detail = {"id": run.name, "path": str(run), "variant": variant, "variant_inferred": inferred,
              "backend": metadata.get("backend") or config.get("backend"),
              "workflow_implementation": metadata.get("workflow_implementation"),
              "task": metadata.get("task") or config.get("task"), "model": config.get("model"),
              "generation": generation, "evaluation": _evaluation(selected, warnings, config.get("benchmark_revision")),
              "analysis": _analysis(run, warnings), "remote": remote, "warnings": warnings}
    return detail, metadata, folders


def list_runs(root, variant=None, task=None, backend=None) -> list[dict]:
    """按目录名逆序列出有 run.json 的实验；缺失指标使用 null/unknown。"""
    result = []
    for path in sorted((Path(root).resolve() / "runs").glob("*/run.json"), reverse=True):
        row, _, _ = _summary(path.parent)
        if ((variant is None or row["variant"] == variant) and (task is None or row["task"] == task)
                and (backend is None or row["backend"] == backend)):
            result.append(row)
    return result


def _session_evidence(entry, run, warnings):
    """将清单里的可移植证据路径变成可打开的归档入口；不读取输入正文。"""
    entry = dict(entry)

    def relocate(record, field):
        source = record.get(field)
        if source is None:
            return
        path = (run / source).resolve() if isinstance(source, str) else None
        if not source or path is None or Path(source).is_absolute() or not path.is_relative_to(run) or not path.is_file():
            warnings.append(f"会话 {entry.get('session_id', '未知')}: {field} 归档缺失或路径不属于本次 run: {source}")
            record[field] = None
        else:
            record[field] = str(path)

    for field in ("context_path", "instructions_path"):
        relocate(entry, field)
    if isinstance(entry.get("turns"), list):
        entry["turns"] = [dict(turn) if isinstance(turn, dict) else turn for turn in entry["turns"]]
        for turn in entry["turns"]:
            if isinstance(turn, dict):
                relocate(turn, "input_path")
    return entry


def _live_braid(metadata, warnings):
    runtime = metadata.get("runtime")
    if metadata.get("status") != "generating" or metadata.get("workflow") != "braid" or not isinstance(runtime, dict) or not runtime:
        return None
    counts = ("active_turns", "pending_batches", "pending_resets", "blocked_groups")
    result = {"status": "unknown", "source": None, "observed_at": time.time(),
              "written_at": None, "items": None, "counts": dict.fromkeys(counts), "model_progress": "unknown"}
    try:
        if not all(isinstance(runtime.get(key), str) and Path(runtime[key]).is_absolute() for key in ("work", "braid_state")):
            raise ValueError("runtime.work/braid_state 缺少有效绝对路径")
        work = Path(runtime["work"]).resolve()
        path = (Path(runtime["braid_state"]) / "status.json").resolve()
        if not path.is_relative_to(work):
            raise ValueError("Braid 状态路径不属于当前 runtime.work，拒绝读取")
        result["source"] = str(path)
        # 同一打开文件取得快照和 mtime；写入时间只描述状态采样，不是模型进展。
        with path.open() as source:
            value = json.load(source)
            result["written_at"] = os.fstat(source.fileno()).st_mtime
        if not isinstance(value, dict):
            raise ValueError("Braid 状态顶层必须是 JSON 对象")
        items = value.get("items")
        if isinstance(items, list) and all(isinstance(item, dict) and isinstance(item.get("kind"), str)
                                           and type(item.get("id")) in (str, int) and isinstance(item.get("state"), str) for item in items):
            result["items"] = [{key: item[key] for key in ("kind", "id", "state")} for item in items]
        result["counts"] = {key: value[key] if type(value.get(key)) is int and value[key] >= 0 else None for key in counts}
        if result["items"] is None or any(value is None for value in result["counts"].values()):
            raise ValueError("Braid 状态缺少有效工作项或调度计数，缺失字段为 unknown")
        result["status"] = "available"
    except (OSError, ValueError, RuntimeError) as exc:
        warnings.append(f"Braid 实时状态 {result['source'] or '未知来源'}: {exc}")
    return result


def _sessions(run, analysis, warnings):
    native = sorted((run / "native").glob("*.jsonl"))
    if not native and (run / "pi-session.jsonl").exists():
        native = [run / "pi-session.jsonl"]
    manifest_path = run / "native/manifest.json"
    manifest = None
    archived = {}
    rejected = []
    if manifest_path.exists():
        manifest = _read(manifest_path, warnings)
        if manifest.get("schema_version") != 1 or not isinstance(manifest.get("sessions"), list):
            warnings.append(f"{manifest_path}: 未知会话清单格式，拒绝推导关联")
            return {"native": [], "stages": [], "manifest": str(manifest_path), "integrity": "unknown"}
        native = []
        for entry in manifest["sessions"]:
            if not isinstance(entry, dict):
                warnings.append(f"{manifest_path}: 会话记录必须是对象")
                continue
            entry = _session_evidence(entry, run, warnings)
            if not isinstance(entry.get("native"), str) or not entry["native"]:
                warnings.append(f"{manifest_path}: 会话缺少 native 路径")
                rejected.append(dict(entry, native=None, integrity="unavailable", analysis=None, analysis_candidates=[], stages=[]))
                continue
            path = (run / entry["native"]).resolve()
            if Path(entry["native"]).is_absolute() or not path.is_relative_to(run / "native") or path in native:
                warnings.append(f"{manifest_path}: native 路径越界或重复，拒绝关联: {entry['native']}")
                rejected.append(dict(entry, rejected_native=entry["native"], native=None, integrity="mismatch", analysis=None, analysis_candidates=[], stages=[]))
                continue
            native.append(path)
            archived[path] = entry
    sources = {path: re.sub(r"^\d{3,}-", "", path.name, count=1) for path in native}
    analysis_sources = {}
    for entry in analysis:
        provenance = Path(entry["path"]) / "provenance.json"
        if provenance.exists():
            analysis_sources[entry["id"]] = _read(provenance, warnings)
    stages = []
    for folder in ([] if manifest is not None else sorted(path for path in (run / "braid-state").glob("*") if path.is_dir())):
        session = _read(folder / "session.json", warnings)
        terminal = _read(folder / "terminal.json", warnings)
        session_id = session.get("id")
        # 归档只增加序号；Pi 保存源路径，Codex 保存完整 thread ID。
        matches = [path for path, source in sources.items() if isinstance(session_id, str) and session_id and
                   (source == Path(session_id).name or
                    re.fullmatch(r"rollout-\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}-" + re.escape(session_id) + r"\.jsonl", source))]
        stages.append({"id": folder.name, "stage": session.get("stage"), "workitem": session.get("workitem"), "session_id": session_id,
                       "status": terminal.get("status") or "unknown", "native": str(matches[0]) if len(matches) == 1 else None,
                       "session": str(folder / "session.json"), "terminal": str(folder / "terminal.json"),
                       "action": _existing(folder / "action.json"), "context": _existing(folder / "context.md"),
                       "packet": _existing(folder / "packet.md"), "design": _existing(folder / "design.md"),
                       "implementation": _existing(folder / "implementation.md"),
                       "instructions": _existing(folder / "instructions.md")})
    sessions = rejected
    for index, path in enumerate(native):
        entry = archived.get(path, {})
        digest = _digest(path, warnings)
        integrity = ("verified" if digest and digest == entry.get("sha256") else "mismatch") if manifest is not None else "unverified"
        candidates = [entry for entry in analysis if
                      (analysis_sources[entry["id"]].get("source_session") == path.name if entry["id"] in analysis_sources else
                       entry["id"].split("-", 1)[0] == f"{index:03}" or (len(native) == 1 and entry["id"] == "legacy"))]
        links = []
        for candidate in candidates:
            provenance = analysis_sources.get(candidate["id"], {})
            expected = provenance.get("source_sha256")
            status = "verified" if digest and expected == digest else "mismatch" if expected else "unverified"
            if integrity == "mismatch" or (entry.get("provider") and provenance.get("provider") not in (None, entry["provider"])):
                status = "mismatch"
            links.append({"id": candidate["id"], "status": status, "evidence": candidate["evidence"]})
        verified = [link["id"] for link in links if link["status"] == "verified"]
        sessions.append(dict(entry, native=str(path), integrity=integrity, source_sha256=digest,
                             analysis=verified[0] if len(verified) == 1 else None, analysis_candidates=links,
                             stages=[stage["id"] for stage in stages if stage["native"] == str(path)]))
    linked = {link["id"] for session in sessions for link in session["analysis_candidates"]}
    return {"native": sessions, "stages": stages, "manifest": str(manifest_path) if manifest is not None else None,
            "unmatched_analysis": [entry["id"] for entry in analysis if entry["id"] not in linked]}


def _pi_terminal(session):
    result = {"status": "unknown", "path": session.get("native"), "line": None, "record_id": None,
              "stop_reason": None, "error": None, "reason": "原生归档未通过哈希核实"}
    if session["integrity"] != "verified":
        return result
    last = None
    line_number = None
    try:
        # 逐行保留最后 assistant 的少量字段，长响应也不能造成静默漏报。
        with Path(session["native"]).open() as source:
            for line_number, line in enumerate(source, 1):
                if not line.strip():
                    continue
                entry = json.loads(line)
                if not isinstance(entry, dict):
                    raise ValueError("原生记录必须是 JSON 对象")
                message = entry.get("message")
                if entry.get("type") == "message" and not isinstance(message, dict):
                    raise ValueError("message 记录缺少有效内容")
                if entry.get("type") == "message" and message.get("role") == "assistant":
                    last = {"line": line_number, "record_id": entry.get("id"), "timestamp": entry.get("timestamp"),
                            "stop_reason": message.get("stopReason"), "error": _error(message.get("errorMessage"))}
    except (OSError, ValueError) as exc:
        result.update(line=line_number, reason="原生记录无法完整解析: " + _error(exc)["text"])
        return result
    if last is None:
        result["reason"] = "没有 assistant 终止记录"
        return result
    result.update(last)
    if last["stop_reason"] == "stop":
        result.update(status="stopped", error=None, reason=None)
    elif last["stop_reason"] in ("error", "aborted"):
        result.update(status=last["stop_reason"], reason=None)
        if not result["error"]["text"]:
            result["error"] = _error(f"stopReason={last['stop_reason']}，未提供错误消息")
    else:
        result.update(error=None, reason=f"最后 assistant 的 stopReason={last['stop_reason'] or 'unknown'}，终止信息未知")
    return result


def _attachment(attachment, folder):
    source = attachment.get("path")
    if not isinstance(source, str):
        return None
    path = Path(source)
    # 报告记录远程绝对路径；只重定位明确属于这一次 evaluation 的附件。
    marker = ("evaluation", folder.name)
    for index in range(len(path.parts) - 1):
        if path.parts[index:index + 2] == marker:
            path = folder.joinpath(*path.parts[index + 2:])
            break
    else:
        if not path.is_absolute():
            path = folder / path
    return {"name": attachment.get("name"), "path": str(path), "exists": path.is_file(), "source_path": source}


def _page_evidence(attachment, folder, error, warnings):
    """只定位 Playwright 页面快照中的可访问节点；名称相似不构成故障归因。"""
    path = Path(attachment["path"]).resolve()
    result = {"path": str(path), "status": "unavailable", "lines": []}
    if not path.is_relative_to(folder.resolve()):
        warnings.append(f"{path}: error-context 不属于所选评测，未读取")
        return result
    try:
        with path.open() as source:
            text = source.read(256_000)
    except (OSError, UnicodeError) as exc:
        warnings.append(f"{path}: {exc}")
        return result
    snapshot = re.search(r"(?m)^# Page snapshot\s*\n+```(?:yaml)?\n([\s\S]*?)\n```", text)
    if not snapshot:
        return result
    first_line = text[:snapshot.start(1)].count("\n") + 1
    rows = snapshot.group(1).splitlines()
    nodes = []
    for index, line in enumerate(rows):
        node = re.match(r'^([ ]*)- ([\w-]+)(?: "([^"\n]*)")?', line)
        if node:
            nodes.append((index, len(node[1]), node[2], node[3]))
    # 只识别字面名称或 /^字面名称$/，不解释任意 JS/正则定位器。
    locator_error = error.split("Call log:", 1)[-1].split("\n\n", 1)[0]
    locators = re.findall(r'''getByRole\(['"]([\w-]+)['"]\s*,\s*\{\s*name:\s*(?:['"]([^'"]+)['"]|/\^([^/$]+)\$/[a-z]*)''', locator_error)
    matches = []
    for role, literal, anchored in reversed(locators):
        name = literal or anchored
        matches = [node for node in nodes if node[2] == role and node[3] and node[3].casefold() == name.casefold()]
        if matches:
            break
    result["selection"] = "role_and_name"
    if not matches:
        roles = re.findall(r'''getByRole\(['"]([\w-]+)['"]''', locator_error)
        matches = [node for node in nodes if node[2] in roles]
        result["selection"] = "role_only"
    if not matches:
        result["status"] = "no_matching_role"
        return result
    selected = set()
    for target in matches[:3]:
        stack = []
        for node in nodes:
            if node[0] > target[0]:
                break
            while stack and stack[-1][1] >= node[1]:
                stack.pop()
            stack.append(node)
        selected.update(node[0] for node in stack if node[2] in ("dialog", "alertdialog", "form", "region", "main"))
        selected.add(target[0])
    # 片段按原文件行号呈现，不将不连续节点伪装成连续 DOM。
    result.update(status="found", lines=[{"number": first_line + index, "text": rows[index][:500]} for index in sorted(selected)[:12]],
                  truncated=len(matches) > 3 or len(selected) > 12 or any(len(rows[index]) > 500 for index in selected))
    return result


def _case(folder, case, warnings):
    result = {"id": case, "status": "unavailable", "matches": [], "error_limit": ERROR_LIMIT}
    if folder is None:
        return result
    report = _read(folder / "results.json", warnings)
    if not report:
        return result
    if not isinstance(report.get("suites"), list):
        warnings.append(f"{folder / 'results.json'}: 缺少 suites，用例结果未知")
        return result
    pattern = re.compile(r"(?<![\w.-])" + re.escape(case) + r"(?![\w-]|\.\d)")

    def visit(suite):
        for spec in suite.get("specs", []):
            if not pattern.search(str(spec.get("title", ""))) and Path(str(spec.get("file", ""))).name != case + ".spec.ts":
                continue
            for test in spec.get("tests", []):
                errors, attachments, attempts, page_evidence = [], [], [], []
                for attempt in test.get("results", []):
                    attempts.append(attempt.get("status") or "unknown")
                    attempt_errors = []
                    for error in attempt.get("errors", []) or [attempt.get("error")]:
                        if error:
                            text = (error.get("message") or error.get("stack") or str(error)) if isinstance(error, dict) else str(error)
                            attempt_errors.append(text)
                            if text not in errors:
                                errors.append(text)
                    for raw in attempt.get("attachments", []):
                        item = _attachment(raw, folder)
                        if item:
                            attachments.append(item)
                            if item["name"] == "error-context" and item["exists"]:
                                evidence = _page_evidence(item, folder, "\n".join(attempt_errors), warnings)
                                evidence["attempt"] = len(attempts)
                                page_evidence.append(evidence)
                result["matches"].append({"title": spec.get("title"), "file": spec.get("file"),
                                          "status": test.get("status") or "unknown", "project": test.get("projectName"),
                                          "attempts": attempts, "error": _error("\n\n".join(errors)), "attachments": attachments,
                                          "page_evidence": page_evidence})
        for child in suite.get("suites", []):
            visit(child)

    visit(report)
    result["status"] = "found" if result["matches"] else "not_found"
    return result


def show_run(run, evaluation=None, case=None, profile=None, session=None) -> dict:
    """返回摘要和证据路径；指定 case 时只展开该用例的有界错误与附件。"""
    run = Path(run).resolve()
    detail, metadata, folders = _summary(run, evaluation)
    detail["evaluations"] = [{"id": folder.name, "path": str(folder)} for folder in folders]
    detail["runtime"] = metadata.get("runtime")
    detail["live_braid"] = _live_braid(metadata, detail["warnings"])
    detail["evidence"] = {name: _existing(run / name) for name in
                          ("run.json", "config.json", "input", "input/requirements.md", "input/requirements.yaml",
                           "input/reference", "application", "application-hashes.json", "prompt.txt", "recovery.json",
                           "braid-state", "analysis", "native", "sources", "remote-evaluation.json", "remote-evaluations")}
    detail["evidence"]["logs"] = sorted({str(path) for pattern in ("*.log", "*stderr*") for path in run.glob(pattern) if path.is_file()})
    detail["sessions"] = _sessions(run, detail["analysis"], detail["warnings"])
    if detail["generation"]["status"] == "generation_failed":
        for session in detail["sessions"]["native"]:
            if session.get("provider") == "pi":
                session["terminal"] = _pi_terminal(session)
    if profile is not None or session is not None:
        manifest = _read(run/'native/manifest.json', detail['warnings'])
        detail['selected_sessions'] = [entry for entry in manifest.get('sessions', [])
            if (profile is None or entry.get('profile_id')==profile)
            and (session is None or session in (entry.get('native_id'),entry.get('session_id')))]
    selected = Path(detail["evaluation"]["path"]) if detail["evaluation"]["path"] else None
    detail["evaluation"]["evidence"] = {name: _existing(selected / name) if selected else None for name in
                                           ("summary.json", "results.json", "html/index.html", "test.log", "install.log", "build.log", "application.log", "test-results")}
    detail["case"] = _case(selected if detail["evaluation"]["status"] != "identity_mismatch" else None, case, detail["warnings"]) if case is not None else None
    return detail


def _score_text(evaluation):
    score = evaluation["score"]
    return f"{score['passed']}/{score['total']} ({score['pass_rate']:.3%})" if score else "未知"


def render_list(rows) -> str:
    if not rows:
        return "没有匹配的实验。"
    lines = ["运行 | 组合 | Backend | 任务 | 生成状态/阶段 | 最新评测 | 分数"]
    for row in rows:
        variant = (row["variant"] or "未知") + ("（推导）" if row["variant_inferred"] else "")
        generation, evaluation = row["generation"], row["evaluation"]
        lines.append(f"{row['id']} | {variant} | {row['backend'] or '未知'} | {row['task'] or '未知'} | {generation['status']}/{generation['phase'] or '未知'} | {evaluation['id'] or '无本地评测'}:{evaluation['status']} | {_score_text(evaluation)}")
        if row["remote"]:
            lines.append(f"  远程: {row['remote']['host']} / {row['remote']['phase'] or '未知'}；评测 {row['remote']['attempt'] or '未知'}")
        lines.extend("  警告: " + warning for warning in row["warnings"])
    return "\n".join(lines)


def render_show(detail) -> str:
    def path_text(value):
        path = Path(value)
        return str(path.relative_to(detail["path"])) if path.is_relative_to(detail["path"]) else str(path)

    def error_text(error):
        preview = "\n".join(error["text"].splitlines()[:8])[:1000]
        if error["truncated"] or preview != error["text"]:
            preview += "\n[错误已截断；--json 查看更多]"
        return preview

    generation, evaluation = detail["generation"], detail["evaluation"]
    lines = [render_list([detail]).replace("最新评测", "所选评测", 1), f"目录: {detail['path']}"]
    context = [f"根配置模型: {detail['model']}"] if detail["model"] else []
    if generation["exit_code"] is not None:
        context.append(f"生成退出码: {generation['exit_code']}")
    if generation["updated_at"] is not None:
        context.append(f"阶段更新: {generation['updated_at']}")
    if context:
        lines.append("；".join(context))
    if 'selected_sessions' in detail:
        for entry in detail['selected_sessions']:
            lines.append(f"会话 {entry.get('native_id') or entry.get('session_id')}: profile={entry.get('profile_id')}，role={entry.get('native_role')}，evidence={entry.get('native') or entry.get('archive_error')}")
    live = detail.get("live_braid")
    if live:
        items = live["items"]
        work_items = "未知" if items is None else "，".join(f"{item['kind']} #{item['id']} {item['state']}" for item in items[:3]) or "无"
        if items and len(items) > 3:
            work_items += f"（另 {len(items) - 3} 个见 --json）"
        counts = "，".join(f"{label}={live['counts'][key] if live['counts'][key] is not None else '未知'}" for key, label in
                          (("active_turns", "active turn"), ("pending_batches", "pending batch"), ("pending_resets", "reset"), ("blocked_groups", "blocked")))
        lines.append(f"Braid 实时: {work_items}；{counts}；模型进展: 未知")
    for label, data in (("生成", generation), ("评测", evaluation), ("远程", detail["remote"] or {})):
        if data.get("failed_phase"):
            lines.append(f"{label}失败阶段: {data['failed_phase']}")
        elif label == "评测" and data.get("phase") and data.get("status") != "completed":
            lines.append(f"评测阶段: {data['phase']}")
        if data.get("phase_log") and (data.get("failed_phase") or data.get("error") or data.get("status") not in ("generated", "completed")):
            log = Path(data["phase_log"])
            if label != "远程" and not log.is_absolute():
                log = Path(evaluation["path"] if label == "评测" else detail["path"]) / log
            lines.append(f"{label}阶段日志: {path_text(log)}")
        if data.get("error"):
            lines.append(f"{label}错误: {error_text(data['error'])}")
    current = [session for session in detail["sessions"]["native"]
               if session.get("terminal") and session.get("status") not in ("replaced", "retired")]
    problems = [session for session in current if session["terminal"]["status"] != "stopped"]
    if problems:
        # 多份未退役物理会话不能靠文件顺序决定哪份代表当前 group。
        ambiguous = {session["group_id"] for session in current if session.get("group_id") and
                     sum(other.get("group_id") == session["group_id"] for other in current) > 1}
        candidates = [session for session in problems if session.get("group_id") not in ambiguous]
        candidates.sort(key=lambda session: session["terminal"]["status"] == "unknown")
        if candidates:
            terminal = candidates[0]["terminal"]
            message = terminal["error"]["text"] if terminal["error"] else "未知：" + terminal["reason"]
            preview = " ".join(message.splitlines())[:500]
            if len(message) > 500 or (terminal["error"] and terminal["error"]["truncated"]):
                preview += "…"
            evidence = path_text(terminal["path"]) if terminal["path"] else "归档缺失"
            if terminal["line"] is not None:
                evidence += f":{terminal['line']}"
            record = f"；record {terminal['record_id']}" if terminal["record_id"] else ""
            lines.append(f"Pi 原生末条 assistant: {preview}（{evidence}{record}）" + (f"；另 {len(problems) - 1} 份异常/未知见 --json" if len(problems) > 1 else ""))
        else:
            lines.append(f"Pi 原生终止信息: 当前 group 的物理会话关联不唯一；{len(problems)} 份异常/未知见 --json")
    remote = detail.get("remote") or {}
    if remote.get("summary"):
        lines.append(f"远端阶段: {remote['summary'].get('phase', '未知')}；观测时间: {remote.get('observed_at')}；尝试: {remote.get('attempt')}")
    if remote.get("observation_error"):
        lines.append(f"远端观测失败: {remote['observation_error']}（上次状态可能已过时）")
    if detail["case"]:
        lines.append(f"用例 {detail['case']['id']}: {detail['case']['status']}")
        for match in detail["case"]["matches"]:
            lines.append(f"{match['title']} [{match['project'] or '未知'}]: {match['status']} / {', '.join(match['attempts'])}")
            if match["error"]["text"]:
                lines.append(error_text(match["error"]))
            for page in match["page_evidence"]:
                if page["lines"]:
                    lines.append(f"页面片段（第 {page['attempt']} 次执行，按定位器检索）: {path_text(page['path'])}")
                    lines.extend(f"  {line['number']}: {line['text'].strip()}" for line in page["lines"])
                else:
                    lines.append(f"页面片段: {page['status']}；{path_text(page['path'])}")
            for attachment in match["attachments"]:
                lines.append(f"{attachment['name']}: {path_text(attachment['path'])}" + ("（本地缺失）" if not attachment["exists"] else ""))
    report = evaluation["evidence"].get("html/index.html") or evaluation["evidence"].get("results.json") or evaluation["evidence"].get("summary.json")
    if report:
        lines.append(f"评测报告: {path_text(report)}")
    stages = detail["sessions"]["stages"]
    if detail["sessions"].get("manifest"):
        verified = sum(entry["integrity"] == "verified" for entry in detail["sessions"]["native"])
        lines.append(f"原生证据: {verified}/{len(detail['sessions']['native'])} 份哈希核实；{path_text(detail['sessions']['manifest'])}")
    if stages:
        lines.append("会话阶段: " + "；".join(f"{entry['id']}={entry['status']}" for entry in stages))
        for entry in stages:
            if entry["status"] != "completed":
                lines.append(f"阶段证据 {entry['id']}: {path_text(entry['terminal'])}")
        unmapped = sum(entry["native"] is None for entry in stages)
        if unmapped:
            lines.append(f"会话映射: {unmapped} 个阶段未匹配到原生会话；--json 查看详情")
    if detail["analysis"]:
        statuses = {}
        for entry in detail["analysis"]:
            statuses[entry["status"]] = statuses.get(entry["status"], 0) + 1
        lines.append("SVC: " + "，".join(f"{status} {count}" for status, count in statuses.items()) + "；analysis/（partial 不等于生成失败）")
        links = [link for session in detail["sessions"]["native"] for link in session["analysis_candidates"]]
        verified = sum(link["status"] == "verified" for link in links)
        lines.append(f"SVC 会话关联: {verified} 份哈希核实，{sum(link['status'] == 'unverified' for link in links)} 份缺来源哈希，{sum(link['status'] == 'mismatch' for link in links)} 份不符；多份结果通过 --json 选择")
        if detail["sessions"].get("unmatched_analysis"):
            lines.append(f"SVC 未找到源会话: {len(detail['sessions']['unmatched_analysis'])} 份；--json 查看详情")
    entries = [f"{label}: {path_text(detail['evidence'][name])}" for label, name in
               (("应用", "application"), ("工作记忆", "braid-state")) if detail["evidence"].get(name)]
    if entries:
        lines.append("；".join(entries))
    lines.append("更多证据: --json（元数据、日志、会话实际输入与 SVC 映射）" + ("；--case <REQ-ID>（用例错误与附件）" if not detail["case"] else ""))
    return "\n".join(lines)
