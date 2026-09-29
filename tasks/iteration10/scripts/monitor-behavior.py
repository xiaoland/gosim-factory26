#!/usr/bin/env python3
"""Incremental, read-only evidence index for live Braid/Pi workflows."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import subprocess
import time


TASKS = {"github", "sheet"}
TERMINAL = {"completed", "finished", "failed", "cancelled", "interrupted", "error"}
CLI = re.compile(r"\bbraid\s+(issue|pr)\s+([\w-]+)")
PATH = re.compile(r"[^\s'\";|]+(?:SKILL\.md|[\w.-]+\.md)")
DOC = re.compile(r"(?:^|/)(?:docs|tasks|plans?|specs?|acceptance|README)(?:/|\.|$)", re.I)
MAX_EVENTS = 160
MAX_BYTES = 2_000_000


def read_json(path, default=None):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return default


def short(value, length=180):
    value = " ".join(str(value or "").split())
    # Tool arguments may contain credentials; preserve the source reference,
    # while masking common literal forms in the bounded human preview.
    value = re.sub(r"(?i)(api[_-]?key|token|password|secret)\s*[:=]\s*\S+", r"\1=[redacted]", value)
    return value[:length]


def input_path(template, raw):
    if not isinstance(raw, str) or not raw.startswith("/workspace/template/"):
        return None
    path = (template / raw.removeprefix("/workspace/template/")).resolve()
    return path if path.is_relative_to(template.resolve()) and path.is_file() else None


def consume(path, cursors, visit, limit=MAX_BYTES):
    """Advance only through complete JSONL lines; leave overflow for next sample."""
    key = str(path)
    state = cursors.setdefault(key, {"offset": 0, "line": 0})
    size = path.stat().st_size
    if size < state["offset"]:
        state.update(offset=0, line=0)
    used = 0
    with path.open("rb") as source:
        source.seek(state["offset"])
        while used < limit:
            start = source.tell()
            raw = source.readline()
            if not raw or not raw.endswith(b"\n") or (used and used + len(raw) > limit):
                break
            line = state["line"] + 1
            try:
                record = json.loads(raw)
            except ValueError:
                record = None
            if visit(record, path, line, start) is False:
                break
            used += len(raw)
            state.update(offset=source.tell(), line=line)
    return {"path": key, "offset": state["offset"], "line": state["line"],
            "remaining_bytes": max(0, size - state["offset"])}


def run_records(root):
    for path in sorted((root / "runs").glob("*/run.json")):
        record = read_json(path)
        if isinstance(record, dict) and (record.get("labels") or {}).get("task") in TASKS:
            yield record, path.parent


def git_origin(state):
    origin = state / "origin.git"
    if not origin.is_dir():
        return {"path": str(origin), "error": "origin.git unavailable"}

    def git(*args):
        result = subprocess.run(["git", "--git-dir", str(origin), *args],
                                capture_output=True, text=True, timeout=5, check=False)
        return result.stdout.strip() if result.returncode == 0 else None

    commit = git("rev-parse", "--verify", "refs/heads/develop")
    refs = git("for-each-ref", "--format=%(refname:short) %(objectname)", "refs/heads/braid/pr-")
    return {"path": str(origin), "develop_commit": commit,
            "develop_tree": git("rev-parse", f"{commit}^{{tree}}") if commit else None,
            "pr_refs": (refs or "").splitlines()[:20]}


def braid_objects(database):
    if not database.is_file():
        return {"database": str(database), "error": "database unavailable"}
    with sqlite3.connect(f"file:{database}?mode=ro", uri=True, timeout=5) as db:
        rows = db.execute(
            "SELECT w.kind,w.number,w.state,a.member_login,a.lifecycle "
            "FROM work_items w LEFT JOIN assignments a ON a.work_item_node_id=w.node_id "
            "ORDER BY w.kind,w.number,a.assignment_revision DESC LIMIT 80"
        ).fetchall()
    return {"database": str(database), "items": [dict(zip(
        ("kind", "number", "state", "assignee", "assignment_lifecycle"), row)) for row in rows]}


def sample_run(record, run_path, state):
    labels = record.get("labels") or {}
    generation = Path(labels.get("retained_generation") or run_path / "workspace/official-generation")
    template = generation / "template"
    homes = list(template.glob(".factory26/*/braid-state/sessions.json"))
    result = {"task": labels["task"], "run_id": record.get("run_id"),
              "run_path": str(run_path), "generation": str(generation), "events": [], "gaps": [],
              "sample_kind": "incremental" if record.get("run_id") in state["sampled_runs"] else "backfill",
              "attempt_started_at": record.get("started_at")}
    if not homes:
        result["gaps"].append("sessions.json unavailable")
        return result
    index = max(homes, key=lambda p: p.stat().st_mtime)
    home = index.parent.parent
    sessions = read_json(index, [])
    if not isinstance(sessions, list):
        result["gaps"].append(f"invalid sessions index: {index}")
        return result
    files = {}
    parents = {}
    for entry in sessions:
        path = input_path(template, entry.get("native_session_path"))
        if path:
            identity = entry.get("native_session_id") or str(path)
            files[str(path)] = {"path": path, "session": identity,
                                "work_item": f"{entry.get('work_item_kind')}:{entry.get('work_item_id')}",
                                "kind": "braid_member", "status": entry.get("status")}
            parents[str(path.with_suffix(""))] = files[str(path)]

    timing = home / "pi-timing.jsonl"
    if timing.is_file():
        def visit_timing(item, path, line, offset):
            if not isinstance(item, dict):
                return True
            native = input_path(template, item.get("session_file"))
            if native and str(native) not in files:
                parent = next((entry for stem, entry in parents.items()
                               if str(native).startswith(stem + "/")), None)
                files[str(native)] = {"path": native, "session": item.get("session_id") or str(native),
                                      "work_item": parent["work_item"] if parent else None,
                                      "kind": "pi_subagent" if parent else "unindexed_native",
                                      "parent_session": parent["session"] if parent else None}
            return True
        result["timing_cursor"] = consume(timing, state["cursors"], visit_timing)

    pending = state["pending"]
    observed_models = state["models"]
    started = record.get("started_at")
    cutoff = datetime.fromtimestamp(started, timezone.utc).isoformat().replace("+00:00", "Z") if started else None
    def emit(event):
        at = event.get("at")
        event["period"] = ("historical" if cutoff and isinstance(at, str) and at < cutoff
                           else "current_attempt" if cutoff and isinstance(at, str) else "unknown")
        result["events"].append(event)
        return True

    for info in sorted(files.values(), key=lambda item: str(item["path"])):
        path = info["path"]
        def visit(item, source, line, offset):
            if len(result["events"]) >= MAX_EVENTS:
                return False
            if not isinstance(item, dict) or item.get("type") != "message":
                return True
            message = item.get("message") or {}
            if not isinstance(message, dict):
                return True
            base = {"at": item.get("timestamp") or message.get("timestamp"),
                    "path": str(source), "line": line, "offset": offset,
                    "session": info["session"], "work_item": info.get("work_item"),
                    "session_kind": info["kind"]}
            if info.get("parent_session"):
                base["parent_session"] = info["parent_session"]
            if message.get("role") == "toolResult":
                call_id = message.get("toolCallId")
                call = pending.get(call_id)
                if call and call["session"] == info["session"]:
                    event = {**base, "kind": "tool_result", "call_id": call_id,
                             "call_path": call["path"], "call_line": call["line"],
                             "call_kind": call["kind"], "is_error": message.get("isError") is True}
                    if not emit(event):
                        return False
                    pending.pop(call_id, None)
            if message.get("role") != "assistant":
                return True
            if info["kind"] == "pi_subagent" and info["session"] not in observed_models:
                model = message.get("model")
                if model:
                    if not emit({**base, "kind": "subagent_native", "model": model}):
                        return False
                    observed_models[info["session"]] = model
            for block in message.get("content") or []:
                if not isinstance(block, dict) or block.get("type") != "toolCall":
                    continue
                name = block.get("name")
                args = block.get("arguments") or {}
                if not isinstance(args, dict):
                    args = {}
                event = None
                if name in ("subagent", "subagent_wait"):
                    agent = args.get("agent") if isinstance(args.get("agent"), dict) else {}
                    agent_name = args.get("agent") if isinstance(args.get("agent"), str) else None
                    script = args.get("workflowScript") if isinstance(args.get("workflowScript"), str) else ""
                    scripted_task = re.search(r"(?:const|let)\s+task\s*=\s*`([^`]*)`", script, re.S)
                    scripted_role = re.search(r"runs\.run\(\s*['\"]([^'\"]+)['\"]", script)
                    scripted_model = re.search(r"\bmodel\s*:\s*['\"]([^'\"]+)['\"]", script)
                    task = args.get("task") or args.get("prompt") or agent.get("task") or (scripted_task[1] if scripted_task else None)
                    event = {**base, "kind": "subagent_call", "tool": name,
                             "action": args.get("action") or ("wait" if name == "subagent_wait" else "spawn" if script or task else None),
                             "agent_id": args.get("id"), "role": args.get("role") or agent.get("role") or agent_name,
                             "model": args.get("model") or agent.get("model") or (scripted_model[1] if scripted_model else None),
                             "task_preview": short(task),
                             "task_sha256": hashlib.sha256(str(task).encode()).hexdigest() if task else None}
                    if scripted_role and not event["role"]:
                        event["role"] = scripted_role[1]
                    if script:
                        event["workflow_script_sha256"] = hashlib.sha256(script.encode()).hexdigest()
                elif name and ("workflowScript" in name or "skill" in name.lower()):
                    event = {**base, "kind": "workflow_tool", "tool": name,
                             "action": short(args.get("action") or args.get("name"))}
                elif name in ("read", "write", "edit"):
                    target = args.get("path")
                    if isinstance(target, str) and (target.endswith("SKILL.md") or DOC.search(target)):
                        event = {**base, "kind": "skill_file" if target.endswith("SKILL.md") else "document",
                                 "tool": name, "target": target}
                elif name == "bash":
                    command = args.get("command") or ""
                    if isinstance(command, str):
                        cli = CLI.search(command)
                        paths = [p for p in PATH.findall(command) if p.endswith("SKILL.md") or DOC.search(p)]
                        if cli or paths or "workflowScript" in command:
                            event = {**base, "kind": "shell_workflow", "tool": name,
                                     "braid_command": f"{cli[1]} {cli[2]}" if cli else None,
                                     "paths": paths[:8], "workflow_script": "workflowScript" in command}
                if event:
                    call_id = block.get("id")
                    event["call_id"] = call_id
                    if not emit(event):
                        return False
                    if isinstance(call_id, str):
                        pending[call_id] = {"session": info["session"], "path": str(source),
                                            "line": line, "kind": event["kind"]}
            return True
        result.setdefault("native_cursors", []).append(consume(path, state["cursors"], visit))
        if len(result["events"]) >= MAX_EVENTS:
            break
    # Pending results can outlive a sample; keep a bounded set in the cursor.
    if len(pending) > 1000:
        for key in list(pending)[:len(pending) - 1000]:
            pending.pop(key)
    result["indexed_sessions"] = len(sessions)
    result["native_files"] = len(files)
    result["origin"] = git_origin(index.parent)
    result["objects"] = braid_objects(index.parent / "braid.sqlite3")
    result["backlog"] = any(info["path"].stat().st_size > state["cursors"].get(str(info["path"]), {}).get("offset", 0)
                            for info in files.values())
    result["backlog"] |= bool(result.get("timing_cursor", {}).get("remaining_bytes"))
    state["sampled_runs"][record.get("run_id")] = True
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    out = args.out.resolve()
    cursor_path = out.with_suffix(out.suffix + ".cursor.json")
    state = read_json(cursor_path, {}) or {}
    for key in ("cursors", "pending", "models", "sampled_runs"):
        state.setdefault(key, {})
    while True:
        rows = [sample_run(record, path, state) for record, path in run_records(root)]
        entry = {"at": time.time(), "root": str(root), "runs": rows}
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("a") as stream:
            stream.write(json.dumps(entry, ensure_ascii=False) + "\n")
        temporary = cursor_path.with_suffix(cursor_path.suffix + ".tmp")
        temporary.write_text(json.dumps(state, ensure_ascii=False))
        os.replace(temporary, cursor_path)
        print(json.dumps({"at": entry["at"], "out": str(out),
                          "events": {row["task"]: len(row["events"]) for row in rows}},
                         ensure_ascii=False), flush=True)
        if args.once:
            return 0
        records = list(run_records(root))
        if len({row["task"] for row in rows}) == len(TASKS) and all(
            (record.get("phase") in TERMINAL or (record.get("result") or {}).get("status") in TERMINAL)
            for record, _ in records
        ) and not any(row.get("backlog") for row in rows):
            return 0
        if any(row.get("backlog") for row in rows):
            continue
        age = min((time.time() - (record.get("started_at") or time.time())
                   for record, _ in records), default=0)
        time.sleep(180 if age < 600 else 480)


if __name__ == "__main__":
    raise SystemExit(main())
