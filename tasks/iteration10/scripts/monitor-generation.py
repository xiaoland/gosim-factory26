#!/usr/bin/env python3
"""Read-only sampling of the two local Hackathon generation runs."""

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import time

TASKS = ("github", "sheet")
TERMINAL = {"completed", "finished", "failed", "cancelled", "interrupted", "error"}
FAILURE = {"failed", "cancelled", "interrupted", "error"}


def read(path):
    return json.loads(path.read_text()) if path.is_file() else None


def events_since(root, cursor):
    """The saved controller notification format used by lab events --after."""
    rows = []
    skipping = bool(cursor)
    owners = sorted((root / "controllers").glob("*/controller.json"),
                    key=lambda path: (read(path) or {}).get("started_at", 0))
    for owner in owners:
        log = owner.parent / "notifications.jsonl"
        if not log.is_file():
            continue
        with log.open() as source:
            for line in source:
                try:
                    item = json.loads(line)
                    item["cursor"] = f"{item['controller_id']}:{item['seq']}"
                except (ValueError, KeyError):
                    continue
                if skipping:
                    if item["cursor"] == cursor:
                        skipping = False
                    continue
                rows.append(item)
    return {"error": f"unknown event cursor: {cursor}"} if skipping else rows


def incremental(path, offsets, limit=65536):
    if not path.is_file():
        return None
    key = str(path)
    size = path.stat().st_size
    start = min(offsets.get(key, 0), size)
    with path.open("rb") as source:
        source.seek(start)
        raw = source.read(limit)
        end = source.tell()
    offsets[key] = end
    return {"path": key, "offset": start, "next_offset": end,
            "truncated": end < size, "text": raw.decode("utf-8", "replace")}


def native(template, state, cutoff, until=None):
    index = read(state / "sessions.json") or []
    files = {}
    for entry in index if isinstance(index, list) else []:
        raw = entry.get("native_session_path")
        if not raw or not raw.startswith("/workspace/template/"):
            continue
        path = (template / raw.removeprefix("/workspace/template/")).resolve()
        if path.is_relative_to(template.resolve()) and path.is_file():
            files[str(path)] = (path, entry)
    latest_success = latest_error = None
    streaks = []
    last_by_path = {}
    for path, entry in files.values():
        consecutive = 0
        first_error = None
        # Indexed JSONL paths avoid scanning application dependencies or native-home trees.
        with path.open(errors="replace") as source:
            for line_number, line in enumerate(source, 1):
                try:
                    event = json.loads(line)
                except ValueError:  # A concurrently written final line is incomplete.
                    continue
                message = event.get("message") or {}
                stamp = event.get("timestamp")
                if (message.get("role") != "assistant" or not isinstance(stamp, str) or stamp < cutoff
                        or (until and stamp > until)):
                    continue
                item = {"at": stamp, "path": str(path), "line": line_number, "model": message.get("model"),
                        "stop_reason": message.get("stopReason")}
                last_by_path[str(path)] = item
                if message.get("stopReason") == "error":
                    item["error"] = message.get("errorMessage")
                    if not consecutive:
                        first_error = stamp
                    consecutive += 1
                    if latest_error is None or stamp > latest_error["at"]:
                        latest_error = item
                else:
                    consecutive = 0
                    first_error = None
                    if latest_success is None or stamp > latest_success["at"]:
                        latest_success = item
        if consecutive:
            streaks.append({"path": str(path), "first_error_at": first_error,
                            "last_error_at": last_by_path[str(path)]["at"],
                            "last_error": last_by_path[str(path)].get("error"),
                            "session_status": entry.get("status"),
                            "work_item": f"{entry.get('work_item_kind')}:{entry.get('work_item_id')}",
                            "consecutive_errors": consecutive})
    return {"indexed_sessions": len(index), "readable_sessions": len(files),
            "latest_success": latest_success, "latest_error": latest_error,
            "error_recovered": bool(latest_error and last_by_path.get(latest_error["path"], {}).get("at", "") >
                                    latest_error["at"] and last_by_path[latest_error["path"]]["stop_reason"] != "error"),
            "error_streaks": sorted(streaks, key=lambda item: -item["consecutive_errors"])}


def braid(generation, run_path, labels, started, finished):
    template = generation / "template"
    databases = list(template.glob(".factory26/*/braid-state/braid.sqlite3"))
    if not databases:
        return {"source": "unavailable", "reason": "Braid SQLite not yet present"}
    path = max(databases, key=lambda item: item.stat().st_mtime)
    state = path.parent
    home = state.parent
    inner = read(home / "run.json") or {}
    inner_started = inner.get("started_at")
    retained = bool(labels.get("retained_generation"))
    own_workspace = generation.resolve() == (run_path / "workspace/official-generation").resolve()
    current_log = None
    origin = "inherited_snapshot"
    if own_workspace and not retained and isinstance(inner_started, (int, float)) and inner_started >= started:
        origin = "fresh_generation"
        current_log = home / "braid.log"
    else:
        # Current attempt stdout is unique; retained generation debug belongs to an older attempt.
        witness = run_path / "stdout.log" if retained else generation / "execution.debug.log"
        witness_time = witness.stat().st_mtime if witness.is_file() else 0
        if witness.is_file() and witness_time >= started and (not finished or witness_time <= finished + 60):
            for line in witness.read_text(errors="replace").splitlines():
                if "resuming" not in line or "log=/workspace/template/" not in line:
                    continue
                if not retained:
                    try:
                        reported = datetime.strptime(line[1:20], "%Y-%m-%d %H:%M:%S").replace(
                            tzinfo=timezone.utc).timestamp()
                    except ValueError:
                        continue
                    if reported < started or (finished and reported > finished):
                        continue
                raw = line.split("log=/workspace/template/", 1)[1].split()[0]
                candidate = (template / raw).resolve()
                if candidate.parent == home.resolve() and candidate.is_file():
                    if candidate.name.startswith("continuation-"):
                        try:
                            log_started = int(candidate.name.split("-", 2)[1]) / 1e9
                        except ValueError:
                            continue
                        if log_started < started or (finished and log_started > finished):
                            continue
                    elif candidate.name != "recovery-braid.log" or candidate.stat().st_mtime < started:
                        continue
                    current_log = candidate
                    origin = "current_recovery"
    cutoff = datetime.fromtimestamp(started, timezone.utc).isoformat().replace("+00:00", "Z")
    until = (datetime.fromtimestamp(finished, timezone.utc).isoformat().replace("+00:00", "Z")
             if finished else None)
    db = sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=5)
    try:
        run = db.execute("SELECT run_id,lifecycle,delivery_commit FROM local_run").fetchone()
        root = db.execute("SELECT w.state,i.state_reason FROM work_items w LEFT JOIN local_items i "
                          "ON i.node_id=w.node_id WHERE w.node_id='issue:1'").fetchone()
        prs = Counter(row[0] for row in db.execute("SELECT state FROM work_items WHERE kind='pr'"))
        merged = db.execute("SELECT count(*) FROM local_merges WHERE lifecycle='applied'").fetchone()[0]
        latest_state_write = max(p.stat().st_mtime for p in
                                 (path, Path(str(path) + "-wal"), state / "sessions.json") if p.is_file())
        result = {"source": origin, "inner_started_at": inner_started,
                  "database": str(path), "phase_log": str(current_log) if current_log and current_log.is_file() else None,
                  "phase_log_origin": ("later_shared_state" if current_log and current_log.is_file() and finished and
                                       current_log.stat().st_mtime > finished else origin),
                  "statistics_origin": "later_shared_state" if finished and latest_state_write > finished else origin,
                  "run": {"id": run[0], "lifecycle": run[1], "delivery_commit": run[2]} if run else None,
                  "root": {"state": root[0], "reason": root[1]} if root else None,
                  "prs": dict(prs), "applied_merges": merged,
                  "items": db.execute("SELECT count(*) FROM local_items").fetchone()[0],
                  "active_turns": db.execute("SELECT count(*) FROM turns WHERE lifecycle IN ('starting','running')").fetchone()[0],
                  "pending_events": db.execute("SELECT count(*) FROM events WHERE lifecycle='pending'").fetchone()[0],
                  "failed_turns_since_start": db.execute(
                      "SELECT count(*) FROM turns WHERE lifecycle='failed' AND started_at>=? AND (? IS NULL OR started_at<=?)",
                      (cutoff, until, until)).fetchone()[0] if origin != "inherited_snapshot" else None}
        # A delivery rejection has no provider start timestamp. Keep it distinct
        # from failed execution, and bound it by its actual recorded end time.
        result["unstarted_failures_since_start"] = db.execute(
            "SELECT count(*) FROM turns WHERE lifecycle='failed' AND started_at IS NULL "
            "AND ended_at>=? AND (? IS NULL OR ended_at<=?)",
            (cutoff, until, until)).fetchone()[0] if origin != "inherited_snapshot" else None
        turn_columns = {row[1] for row in db.execute("PRAGMA table_info(turns)")}
        result["deferred_deliveries"] = []
        if "deferred_count" in turn_columns:
            fields = ("turn_id", "session_id", "trigger_kind", "lifecycle", "deferred_reason",
                      "first_deferred_at", "last_deferred_at", "deferred_count")
            result["deferred_deliveries"] = [dict(zip(fields, row)) for row in db.execute(
                "SELECT " + ",".join(fields) + " FROM turns WHERE lifecycle='deferred' "
                "AND last_deferred_at>=? AND (? IS NULL OR last_deferred_at<=?)",
                (cutoff, until, until))]
        resets = db.execute(
            "SELECT reset_id,lifecycle,error,created_at,updated_at,old_session_id "
            "FROM context_resets WHERE lifecycle NOT IN ('applied','failed') ORDER BY created_at"
        ).fetchall()
        result["pending_resets"] = [dict(zip(
            ("reset_id", "lifecycle", "error", "created_at", "updated_at", "old_session_id"), row))
            for row in resets]
    finally:
        db.close()
    if origin != "inherited_snapshot":
        result["native"] = native(template, state, cutoff, until)
    return result


def gateway(path, runs, state):
    if not path or not path.is_file():
        return {run["run_id"]: {"source": str(path) if path else None, "status": "unavailable"} for run in runs}
    offset = min(state.get("offset", 0), path.stat().st_size)
    with path.open("rb") as source:
        source.seek(offset)
        while True:
            line_start = source.tell()
            line = source.readline()
            if not line:
                break
            if not line.endswith(b"\n"):
                break
            offset = source.tell()
            try:
                item = json.loads(line)
            except ValueError:
                continue
            item["byte_offset"] = line_start
            run_id = item.get("run_id")
            if run_id not in {run["run_id"] for run in runs}:
                continue
            if item.get("time_ns", 0) < (next(run["started_at"] for run in runs if run["run_id"] == run_id) or 0) * 1e9:
                continue
            current = state.setdefault(run_id, {})
            if item.get("stage") in ("requested", "normalized", "upstream"):
                current["latest_request"] = item
            if item.get("stage") == "failure" or item.get("status") in ("interrupted", "response.failed"):
                current["latest_error"] = item
            if item.get("stage") in ("response", "stream") and not item.get("error"):
                current["latest_success"] = item
    state["offset"] = offset
    return {run["run_id"]: {"source": str(path), **state.get(run["run_id"], {}),
                            "error_recovered": bool(state.get(run["run_id"], {}).get("latest_error") and
                                                    state.get(run["run_id"], {}).get("latest_success") and
                                                    state[run["run_id"]]["latest_success"]["time_ns"] >
                                                    state[run["run_id"]]["latest_error"]["time_ns"])} for run in runs}


def sample(root, gateway_path, offsets, gateway_state, event_state):
    runs = []
    for path in sorted((root / "runs").glob("*/run.json")) if (root / "runs").is_dir() else []:
        try:
            record = read(path)
            if not isinstance(record, dict) or record.get("schema_version") not in (1, 2):
                raise ValueError("invalid lab run record")
        except (OSError, ValueError) as exc:
            runs.append({"path": str(path.parent), "status_error": f"{type(exc).__name__}: {exc}"})
            continue
        if (record.get("labels") or {}).get("task") not in TASKS:
            continue
        runs.append({**record, "path": str(path.parent)})
    gateway_rows = gateway(gateway_path, [item for item in runs if item.get("run_id")], gateway_state)
    rows = []
    for record in runs:
        if "status_error" in record:
            rows.append(record)
            continue
        run = Path(record["path"])
        started = record.get("started_at") or 0
        generation = Path((record.get("labels") or {}).get("retained_generation") or
                          run / "workspace/official-generation")
        result = record.get("result") or {}
        agent_path = generation / "template/.arc/adapter-agent-result.json"
        agent = read(agent_path) or {}
        agent_origin = ("unavailable" if not agent_path.is_file() else
                        "later_shared_state" if record.get("finished_at") and agent_path.stat().st_mtime > record["finished_at"] else
                        "inherited_snapshot" if agent_path.stat().st_mtime < started else "current_attempt")
        receipt = generation / ".lab-artifacts/receipt.json"
        local = read(generation / "local-result.json") or {}
        debug = generation / "execution.debug.log"
        braid_state = braid(generation, run, record["labels"], started, record.get("finished_at")) if started else {"source": "not_started"}
        evidence = {}
        for path in (run / "stdout.log", run / "stderr.log", debug):
            chunk = incremental(path, offsets)
            if chunk and chunk["text"]:
                evidence[path.name] = chunk
        if braid_state.get("phase_log") and braid_state.get("phase_log_origin") != "later_shared_state":
            chunk = incremental(Path(braid_state["phase_log"]), offsets)
            if chunk and chunk["text"]:
                evidence["braid-phase.log"] = chunk
        recovery = []
        if debug.is_file():
            with debug.open(errors="replace") as source:
                recovery = [line.strip() for line in source if "Recovery:" in line]
        rows.append({"task": record["labels"]["task"], "run_id": record["run_id"],
                     "path": str(run), "phase": record.get("phase"),
                     "started_at": started, "recovery_boundary": started,
                     "source_run_id": record["labels"].get("source_run_id"),
                     "retained_generation": str(generation), "result_status": result.get("status"),
                     "runner_exit": record.get("runner_exit_code"), "error": record.get("error") or record.get("controller_error"),
                     "agent_status": agent.get("status"), "agent_error": agent.get("error"),
                     "agent_origin": agent_origin,
                     "local_exit": local.get("container_exit_code"), "receipt": str(receipt) if receipt.is_file() else None,
                     "restore_report": recovery[-1] if recovery else None,
                     "braid": braid_state,
                     "gateway": gateway_rows.get(record["run_id"]), "evidence_increment": evidence})
    events = events_since(root, event_state.get("cursor")) if (root / "manifest.json").is_file() else []
    if isinstance(events, list) and events:
        event_state["cursor"] = events[-1]["cursor"]
    return {"at": time.time(), "runs": rows, "events_increment": events,
            "expected_tasks": list(TASKS), "observed_tasks": sorted({row.get("task") for row in rows if row.get("task")})}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("/home/yyh/Development/factory26/runs/e20260928-03-check-receipts/generation"))
    parser.add_argument("--out", type=Path)
    parser.add_argument("--gateway-log", type=Path)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    out = args.out or root.parent / "generation-monitor.jsonl"
    gateway_path = args.gateway_log or root.parent / "gateway/request-metadata.jsonl"
    offsets, gateway_state, event_state = {}, {}, {}
    while True:
        entry = sample(root, gateway_path, offsets, gateway_state, event_state)
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("a") as stream:
            stream.write(json.dumps(entry, ensure_ascii=False) + "\n")
        rows = entry["runs"]
        failures = [row for row in rows if row.get("phase") in FAILURE or row.get("status_error") or
                    row.get("result_status") in FAILURE or (row.get("phase") in {"completed", "finished"}
                    and row.get("result_status") != "completed") or
                    (row.get("agent_status") == "failed" and row.get("agent_origin") == "current_attempt")]
        attention = [(row, streak) for row in rows if row.get("phase") not in TERMINAL
                     for streak in (((row.get("braid") or {}).get("native") or {}).get("error_streaks") or [])
                     if streak["consecutive_errors"] >= 2 and
                     streak["session_status"] in {"running", "idle", "sleeping", "blocked"}]
        delivery_attention = [row for row in rows if row.get("phase") not in TERMINAL
                              and (row.get("braid") or {}).get("pending_resets")
                              and ((row.get("braid") or {}).get("unstarted_failures_since_start") or 0) >= 2]
        complete = len({row.get("task") for row in rows}) == len(TASKS) and all(
            row.get("phase") in TERMINAL for row in rows)
        summary = {"at": entry["at"], "output": str(out), "tasks": {row.get("task", row.get("path")): {
            "phase": row.get("phase"), "result": row.get("result_status"),
            "braid": (row.get("braid") or {}).get("run", {}).get("lifecycle") if isinstance((row.get("braid") or {}).get("run"), dict) else None,
            "native_error": (((row.get("braid") or {}).get("native") or {}).get("latest_error") or {}).get("error"),
            "native_error_recovered": ((row.get("braid") or {}).get("native") or {}).get("error_recovered"),
            "gateway_error": ((row.get("gateway") or {}).get("latest_error") or {}).get("error"),
            "gateway_error_recovered": (row.get("gateway") or {}).get("error_recovered"),
            "unstarted_failures_since_start": (row.get("braid") or {}).get("unstarted_failures_since_start"),
            "pending_resets": (row.get("braid") or {}).get("pending_resets"),
            "deferred_deliveries": (row.get("braid") or {}).get("deferred_deliveries"),
            "active_native_streaks": [streak for item, streak in attention if item is row][:3],
            "error": row.get("error") or row.get("status_error")}
            for row in rows}}
        if failures or complete or attention or delivery_attention or args.once:
            summary["state"] = "failure" if failures else "terminal" if complete else "attention" if attention or delivery_attention else "observing"
            print(json.dumps(summary, ensure_ascii=False), flush=True)
            return 1 if failures else 2 if attention or delivery_attention else 0
        print(json.dumps({"at": entry["at"], "state": "observing", "output": str(out),
                          "observed_tasks": entry["observed_tasks"]}, ensure_ascii=False), flush=True)
        age = min((time.time() - row["started_at"] for row in rows if row.get("started_at")), default=0)
        time.sleep(180 if age < 600 else 480)


if __name__ == "__main__":
    raise SystemExit(main())
