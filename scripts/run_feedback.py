#!/usr/bin/env python3
"""Small, local-only feedback collector for an experiment run."""
from contextlib import contextmanager
import argparse
import hashlib
import json
from pathlib import Path
import threading
import time


MIN_INTERVAL = 180
MAX_ERRORS = 8
MAX_TEXT = 320
TERMINAL = {"completed", "failed", "interrupted"}


def _read(path):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError, TypeError):
        return None


def _short(value):
    text = str(value or "").replace("\x00", " ").strip()
    return text[:MAX_TEXT] + ("…" if len(text) > MAX_TEXT else "")


def _brief_error(value):
    if isinstance(value, dict):
        return {key: _short(value.get(key)) for key in ("type", "code", "message")
                if value.get(key) is not None}
    return _short(value)


def _relative(path, run):
    try:
        return str(path.resolve().relative_to(run.resolve()))
    except (OSError, ValueError):
        return str(path)


def _event_id(run_id, value):
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256((run_id + ":" + encoded).encode()).hexdigest()[:24]


def _outcome(run, metadata):
    outcome_path = run / "outcome.json"
    outcome = _read(outcome_path)
    interruption = _read(run / "interruption.json")
    if outcome_path.exists() and not (isinstance(outcome, dict) and outcome.get("status") in ("running", *TERMINAL)):
        return {"status": "unknown", "stage": "generation", "scope": "full", "error": None,
                "analysis": None, "evaluation_id": None, "failed_stage": None,
                "variant": None, "task": None, "source": "outcome.json"}
    if isinstance(outcome, dict) and outcome.get("status") in ("running", *TERMINAL):
        return {"status": outcome["status"], "stage": outcome.get("stage") or "generation",
                "scope": "full", "error": outcome.get("error"),
                "analysis": outcome.get("analysis"), "evaluation_id": outcome.get("evaluation_id"),
                "failed_stage": outcome.get("failed_stage"), "variant": outcome.get("variant"),
                "task": outcome.get("task"), "source": "outcome.json"}
    if isinstance(interruption, dict) and interruption.get("stopped") is True:
        return {"status": "interrupted", "stage": "generation", "scope": "generation",
                "error": None, "analysis": None, "evaluation_id": None,
                "failed_stage": None, "source": "interruption.json"}
    status = metadata.get("status")
    if status == "interrupted":
        return {"status": "interrupted", "stage": metadata.get("failed_phase") or "generation",
                "scope": "generation", "error": metadata.get("error"), "analysis": None,
                "evaluation_id": None, "failed_stage": metadata.get("failed_phase"), "source": "run.json"}
    if status == "generating":
        return {"status": "running", "stage": "generation", "scope": "generation",
                "error": None, "analysis": None, "evaluation_id": None, "failed_stage": None, "source": "run.json"}
    if status == "generated":
        return {"status": "completed", "stage": "generation", "scope": "generation",
                "error": None, "analysis": None, "evaluation_id": None, "failed_stage": None, "source": "run.json"}
    if status in ("generation_failed", "failed"):
        return {"status": "failed", "stage": metadata.get("failed_phase") or "generation",
                "scope": "generation", "error": metadata.get("error"),
                "analysis": None, "evaluation_id": None, "failed_stage": metadata.get("failed_phase"), "source": "run.json"}
    return {"status": "unknown", "stage": metadata.get("phase") or "generation",
            "scope": "generation", "error": None, "analysis": None, "evaluation_id": None,
            "failed_stage": None, "source": "run.json"}


def _declared_native(run, metadata):
    """Return only manifest/runtime-declared session files; never pick latest by mtime."""
    result = []
    issues = []
    manifest_path = run / "native/manifest.json"
    manifest = _read(manifest_path)
    if manifest_path.exists() and not (isinstance(manifest, dict) and isinstance(manifest.get("sessions"), list)):
        return result, [f"native/manifest.json 无效: {_relative(manifest_path, run)}"]
    if isinstance(manifest, dict) and isinstance(manifest.get("sessions"), list):
        for entry in manifest["sessions"]:
            if not isinstance(entry, dict) or not isinstance(entry.get("native"), str):
                issues.append("native/manifest.json 会话缺少 native 路径")
                continue
            raw = Path(entry["native"])
            path = (run / raw).resolve()
            if raw.is_absolute() or not path.is_relative_to((run / "native").resolve()):
                issues.append(f"native/manifest.json 路径越界: {entry['native']}")
                continue
            if not path.is_file():
                issues.append(f"native/manifest.json 文件缺失: {entry['native']}")
                continue
            expected = entry.get("sha256")
            if not isinstance(expected, str):
                issues.append(f"native/manifest.json 缺少哈希: {entry['native']}")
                continue
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if digest != expected:
                issues.append(f"native/manifest.json 哈希不匹配: {entry['native']}")
                continue
            if entry.get("provider") not in ("pi", "codex"):
                issues.append(f"native/manifest.json provider 未知: {entry['native']}")
                continue
            result.append((path, entry.get("provider")))
        return result, issues
    runtime = metadata.get("runtime")
    if metadata.get("workflow") != "braid":
        runtime = None
    if not isinstance(runtime, dict):
        if (run / "native").is_dir() and any((run / "native").glob("*.jsonl")):
            return result, ["native/manifest.json 缺失: native/manifest.json"]
        return result, issues
    work, state = runtime.get("work"), runtime.get("braid_state")
    if not isinstance(work, str) or not isinstance(state, str):
        return result, ["run.json runtime 缺少 work/braid_state"]
    work, state = Path(work).resolve(), Path(state).resolve()
    if not state.is_relative_to(work):
        return result, ["run.json runtime.braid_state 越界"]
    sessions = state / "sessions.json"
    values = _read(sessions)
    if not isinstance(values, (list, dict)):
        return result, [f"sessions.json 缺失或无效: {_relative(sessions, run)}"]
    values = values if isinstance(values, list) else values.get("sessions", [])
    if not isinstance(values, list):
        return result, [f"sessions.json sessions 无效: {_relative(sessions, run)}"]
    for entry in values:
        if not isinstance(entry, dict):
            continue
        raw = next((entry.get(key) for key in ("native_session_path", "session_path", "native")
                    if isinstance(entry.get(key), str)), None)
        if raw is None:
            issues.append(f"sessions.json native_session_path 缺失: {_relative(sessions, run)}")
            continue
        path = Path(raw)
        path = path if path.is_absolute() else (work / path)
        path = path.resolve()
        if path.is_file() and path.is_relative_to(work):
            provider = entry.get("provider")
            if provider not in ("pi", "codex"):
                issues.append(f"sessions.json provider 未知: {raw}")
            else:
                result.append((path, provider))
        else:
            issues.append(f"sessions.json native 路径越界或缺失: {raw}")
    return result, issues


def _sources(run, metadata):
    paths = []
    issues = []
    root_providers = set()
    for name, provider in (("pi-events.jsonl", "pi"), ("codex-events.jsonl", "codex")):
        path = run / name
        if path.is_file():
            paths.append((path, provider))
            root_providers.add(provider)
    native, native_issues = _declared_native(run, metadata)
    issues.extend(native_issues)
    for path, provider in native:
        if provider in root_providers:
            continue
        if all(path != existing for existing, _ in paths):
            paths.append((path, provider or "unknown"))
    return paths, issues


def _category(provider, message, detail=""):
    text = (str(message) + " " + str(detail)).lower()
    if "stream" in text and ("disconnect" in text or "closed" in text):
        return provider + ":response_stream_disconnected"
    if "json" in text or "unterminated" in text or "property name" in text:
        return provider + ":json_parse"
    if "cancel" in text or "abort" in text:
        return provider + ":cancelled"
    return provider + ":error"


def _scan(path, provider, run):
    errors = {}
    retries = []
    parse_errors = 0
    terminal_errors = []
    try:
        # ponytail: rescan on each sparse observation; add offsets only if measured I/O warrants it.
        lines = path.read_text().splitlines()
    except OSError as exc:
        return errors, retries, 0, [{"path": _relative(path, run), "error": type(exc).__name__}]
    for number, line in enumerate(lines, 1):
        try:
            event = json.loads(line)
        except (ValueError, TypeError):
            parse_errors += 1
            continue
        if not isinstance(event, dict):
            parse_errors += 1
            continue
        payload = event.get("payload") or {}
        if provider == "codex" and not isinstance(payload, dict):
            parse_errors += 1
            continue
        evidence = f"{_relative(path, run)}:{number}"
        if provider == "pi":
            kind = event.get("type")
            message = event.get("message") or {}
            if kind == "auto_retry_start":
                message = event.get("errorMessage") or "retry requested"
                retries.append({"provider": "pi", "attempt": event.get("attempt"),
                                "max_attempts": event.get("maxAttempts"),
                                "delay_ms": event.get("delayMs"), "message": _short(message),
                                "evidence": evidence})
                category = _category("pi", message)
                group = errors.setdefault(category, {"category": category, "count": 0,
                                                     "messages": [], "evidence": [], "details": []})
                group["count"] += 1
                if _short(message) not in group["messages"]:
                    group["messages"].append(_short(message))
                group["evidence"].append(evidence)
                group["details"].append(retries[-1])
            elif kind in ("message", "message_end"):
                if not isinstance(message, dict):
                    parse_errors += 1
                    continue
                if message.get("role") == "assistant" and message.get("stopReason") in ("error", "aborted"):
                    error = message.get("errorMessage") or f"stopReason={message.get('stopReason')}"
                    terminal_errors.append((error, evidence))
        elif provider == "codex" and (event.get("method") == "error"
                                      or event.get("type") == "event_msg"
                                      and payload.get("type") == "error"):
            if event.get("method") == "error":
                params = event.get("params") or {}
            else:
                params = payload
            if not isinstance(params, dict):
                parse_errors += 1
                continue
            detail = params.get("error") or params
            if not isinstance(detail, dict):
                detail = {"message": detail}
            message = detail.get("message") or "Codex error"
            additional = detail.get("additionalDetails")
            info = detail.get("codexErrorInfo") or {}
            if not isinstance(info, dict):
                info = {"value": info}
            stream = info.get("responseStreamDisconnected") or {}
            if not isinstance(stream, dict):
                stream = {"value": stream}
            record = {"provider": "codex", "message": _short(message),
                      "will_retry": params.get("willRetry", params.get("will_retry")),
                      "thread_id": params.get("threadId", params.get("thread_id")),
                      "turn_id": params.get("turnId", params.get("turn_id")),
                      "http_status_code": stream.get("httpStatusCode"),
                      "details": _short(additional), "evidence": evidence}
            if record["will_retry"]:
                retries.append(record)
            category = _category("codex", message, additional)
            group = errors.setdefault(category, {"category": category, "count": 0,
                                                 "messages": [], "evidence": [], "details": []})
            group["count"] += 1
            if _short(message) not in group["messages"]:
                group["messages"].append(_short(message))
            group["evidence"].append(evidence)
            group["details"].append(record)
    if provider == "pi" and not retries:
        for error, evidence in terminal_errors[-1:]:
            category = _category("pi", error)
            group = errors.setdefault(category, {"category": category, "count": 0,
                                                 "messages": [], "evidence": [], "details": []})
            group["count"] += 1
            group["messages"].append(_short(error))
            group["evidence"].append(evidence)
    return errors, retries, parse_errors, []


def _analysis(run):
    root = run / "analysis"
    if not root.exists():
        return {"status": "unknown"}
    folders = [path for path in root.iterdir() if path.is_dir() and not path.name.startswith(".")]
    if not folders and not (root / "overview.json").exists():
        return {"status": "unknown"}
    statuses = []
    for folder in folders or [root]:
        overview = _read(folder / "overview.json") or {}
        statuses.append(overview.get("status") or "unknown")
    if any(status in ("failed", "error") for status in statuses):
        return {"status": "error"}
    return {"status": "completed" if all(status == "completed" for status in statuses) else "available"}


def collect(run: Path) -> dict:
    run = Path(run).resolve()
    metadata_path = run / "run.json"
    metadata = _read(metadata_path)
    metadata_issues = []
    if not isinstance(metadata, dict):
        metadata = {}
        metadata_issues.append(f"run.json 缺失或无效: {_relative(metadata_path, run)}")
    lifecycle = _outcome(run, metadata)
    groups, retries, parse_errors, source_errors, parse_evidence = {}, [], 0, [], []
    sources, source_issues = _sources(run, metadata)
    for path, provider in sources:
        found, found_retries, malformed, failures = _scan(path, provider, run)
        parse_errors += malformed
        if malformed:
            parse_evidence.append(_relative(path, run))
        retries.extend(found_retries)
        source_errors.extend(failures)
        for category, group in found.items():
            target = groups.setdefault(category, {"category": category, "count": 0,
                                                  "messages": [], "evidence": [], "details": []})
            target["count"] += group.get("count", 0)
            target["messages"] = list(dict.fromkeys(target["messages"] + group.get("messages", [])))[:3]
            target["evidence"] = list(dict.fromkeys(target["evidence"] + group.get("evidence", [])))[:4]
            target["details"] = (target.get("details", []) + group.get("details", []))[:4]
    errors = []
    for category in sorted(groups):
        group = groups[category]
        group["details"] = group.get("details", [])[:4]
        errors.append(group)
    errors = errors[:MAX_ERRORS]
    # Log entries do not prove that a fault is still active, even while a run is running.
    error_scope = "historical"
    for group in errors:
        group["scope"] = error_scope
    for retry in retries:
        retry["scope"] = error_scope
    analysis = lifecycle.get("analysis") or _analysis(run)
    outcome_path = run / "outcome.json"
    if outcome_path.exists() and lifecycle['status'] == 'unknown':
        metadata_issues.append(f"outcome.json 无效: {_relative(outcome_path, run)}")
    unknowns = list(metadata_issues)
    unknowns.extend(source_issues)
    unknowns.extend(f"事件源读取失败: {item['path']}" for item in source_errors)
    if parse_errors:
        unknowns.append("存在无法解析的事件行")
    if not errors:
        unknowns.append("未发现结构化错误；这不等于健康")
    primary_error = _brief_error(lifecycle.get("error")) or None
    if isinstance(analysis, dict) and analysis.get("error") is not None:
        analysis = dict(analysis, error=_brief_error(analysis.get("error")))
    brief = {
        "schema_version": 1,
        "run_id": run.name,
        "variant": lifecycle.get("variant") or metadata.get("variant"),
        "task": lifecycle.get("task") or metadata.get("task"),
        "status": lifecycle["status"],
        "stage": lifecycle["stage"],
        "scope": lifecycle["scope"],
        "terminal": lifecycle["status"] in TERMINAL,
        "error": primary_error,
        "failed_stage": lifecycle.get("failed_stage"),
        "analysis": analysis,
        "evaluation_id": lifecycle.get("evaluation_id") or metadata.get("evaluation_id"),
        "retries": retries[:MAX_ERRORS],
        "retry_count": len(retries),
        "error_scope": error_scope,
        "errors": errors,
        "error_count": sum(group["count"] for group in errors),
        "parse_error_count": parse_errors,
        "unknowns": [_short(value) for value in unknowns[:MAX_ERRORS]],
        "unknown_count": len(unknowns),
        "observed_at": time.time(),
        "evidence_paths": sorted({evidence for item in errors for evidence in item["evidence"]})[:MAX_ERRORS],
    }
    brief["unknown_evidence"] = sorted(set(source_issues + metadata_issues + parse_evidence
                                            + [item["path"] for item in source_errors]))[:MAX_ERRORS]
    terminal_identity = {key: brief.get(key) for key in
                         ("run_id", "status", "scope", "stage", "failed_stage", "error", "analysis", "evaluation_id", "errors")}
    brief["event_id"] = _event_id(run.name, terminal_identity if brief["terminal"] else {"run_id": run.name, "errors": [e["category"] for e in errors]})
    return brief


def _event_key(brief):
    return (brief.get("status"), tuple(error.get("category") for error in brief.get("errors", [])),
            brief.get("analysis", {}).get("status"))


class _Monitor:
    def __init__(self, run, interval):
        if interval < MIN_INTERVAL:
            raise ValueError(f"interval 必须至少为 {MIN_INTERVAL} 秒")
        self.run = Path(run)
        self.interval = interval
        self.stop_event = threading.Event()
        self.thread = None
        self.previous = None
        self.emitted = set()
        self.observer_error = None

    def _emit(self, brief):
        key = _event_key(brief)
        terminal = brief.get("terminal")
        if (not terminal and not brief.get("errors")
                and brief.get("analysis", {}).get("status") not in ("error", "failed")):
            return
        event_id = brief.get("event_id") if terminal else _event_id(self.run.name, {"key": key})
        if event_id in self.emitted or (self.previous is not None and key == self.previous and not terminal):
            return
        self.emitted.add(event_id)
        self.previous = key
        event = {"event_id": event_id, "run_id": brief.get("run_id"),
                 "status": brief.get("status"), "stage": brief.get("stage"),
                 "scope": brief.get("scope"), "evaluation_id": brief.get("evaluation_id"),
                 "failed_stage": brief.get("failed_stage"), "terminal": terminal,
                 "error": brief.get("error"), "errors": brief.get("errors", []),
                 "analysis": brief.get("analysis"), "evidence_paths": brief.get("evidence_paths", [])}
        print(json.dumps(event, ensure_ascii=False), flush=True)

    def sample(self):
        try:
            brief = collect(self.run)
            temporary = self.run / "feedback.json.tmp"
            temporary.write_text(json.dumps(brief, ensure_ascii=False, indent=2) + "\n")
            temporary.replace(self.run / "feedback.json")
            self._emit(brief)
            return brief
        except Exception as exc:  # observer failure must not become experiment failure
            self.observer_error = {"type": type(exc).__name__, "message": _short(exc)}
            event_id = _event_id(self.run.name, {"observer_error": self.observer_error})
            if event_id not in self.emitted:
                self.emitted.add(event_id)
                print(json.dumps({"event_id": event_id, "run_id": self.run.name,
                                  "status": "observer_error", "error": self.observer_error}, ensure_ascii=False), flush=True)
            return None

    def loop(self):
        self.sample()
        while not self.stop_event.wait(self.interval):
            self.sample()

    def start(self):
        self.thread = threading.Thread(target=self.loop, name="run-feedback", daemon=True)
        self.thread.start()

    def close(self):
        self.stop_event.set()
        if self.thread:
            self.thread.join()
        self.sample()


def monitor(run: Path, interval=MIN_INTERVAL):
    if interval < MIN_INTERVAL:
        raise ValueError(f"interval 必须至少为 {MIN_INTERVAL} 秒")

    @contextmanager
    def lifecycle():
        watcher = _Monitor(run, interval)
        watcher.start()
        try:
            yield watcher
        finally:
            watcher.close()

    return lifecycle()


def watch(run: Path, interval=MIN_INTERVAL, after_event=None):
    if interval < MIN_INTERVAL:
        raise ValueError(f"interval 必须至少为 {MIN_INTERVAL} 秒")
    waiter = threading.Event()
    while True:
        brief = collect(run)
        if brief.get("terminal"):
            if after_event and brief.get("event_id") == after_event:
                return {"seen": True, "event_id": after_event, "run_id": brief.get("run_id")}
            return brief
        waiter.wait(interval)


def main():
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    brief = commands.add_parser("brief"); brief.add_argument("run")
    watching = commands.add_parser("watch"); watching.add_argument("run"); watching.add_argument("--interval", type=int, default=MIN_INTERVAL); watching.add_argument("--after-event")
    args = parser.parse_args()
    if args.command == "brief":
        print(json.dumps(collect(Path(args.run)), ensure_ascii=False, indent=2))
    else:
        result = watch(Path(args.run), args.interval, args.after_event)
        if not result.get("seen"):
            print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
