#!/usr/bin/env python3
"""Guard the pi-minimal official journal against an exhausted competition budget.

The guard is intentionally independent of Competition's controller lock.  It
only reads the competition registration and target journal, and it cancels a run after verifying
that the run belongs to the target submission.
"""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lab.arc_bench.playground import Client, TERMINAL, run_path


TARGET = (ROOT / "runs/pi-minimal/20260929/official").resolve()
STOP_NAME = "budget-stop.json"
EVENTS_NAME = "budget-events.jsonl"
COMPETITION = "hackathon"
COMPETITION_REGISTRATION = "/competitions/hackathon/registration"
THRESHOLD = 100.0
INTERVAL = 600


class GuardError(RuntimeError):
    """A balance observation or journal identity could not be trusted."""


def target_journal(value):
    path = Path(value).expanduser().resolve()
    if path != TARGET:
        raise GuardError(f"只允许 pi-minimal 官方 journal：{TARGET}")
    path.mkdir(parents=True, exist_ok=True)
    return path


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def append_event(journal, value):
    event_path = journal / EVENTS_NAME
    with event_path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(value, ensure_ascii=False) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def observe_balance(client):
    """Read the official competition budget, not a self-funded Meter key."""
    try:
        value = client.request(COMPETITION_REGISTRATION)
    except Exception as exc:
        raise GuardError(f"官网比赛额度查询失败：{type(exc).__name__}") from None
    if not isinstance(value, dict) or value.get("competition_id") != COMPETITION:
        raise GuardError("官网比赛额度响应身份不符")
    if value.get("competition_type") != "official" or value.get("registered") is not True:
        raise GuardError("官网正式参赛资格未确认")
    raw = value.get("remaining_budget_cny")
    try:
        balance = float(raw)
    except (TypeError, ValueError):
        raise GuardError("官网额度缺少可解析的 remaining_budget_cny") from None
    if balance != balance or balance in (float("inf"), float("-inf")):
        raise GuardError("官网额度不是有限数字")
    return {
        "balance": balance,
        "currency": value.get("currency"),
        "initial_budget_cny": value.get("initial_budget_cny"),
        "registered": value.get("registered"),
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "budget_endpoint": COMPETITION_REGISTRATION,
    }


def stop(journal, observation, reason):
    marker = {
        "schema_version": 1,
        "reason": reason,
        "threshold": THRESHOLD,
        **observation,
    }
    atomic_json(journal / STOP_NAME, marker)
    append_event(journal, {"event": "budget_stop", **marker})
    return marker


def cancel_target_runs(journal):
    state_path = journal / "state.json"
    if not state_path.is_file():
        return [{"action": "skip", "reason": "journal_state_missing"}]
    state = json.loads(state_path.read_text(encoding="utf-8"))
    submission_id = state.get("submission_id")
    if not submission_id:
        return [{"action": "skip", "reason": "submission_id_missing"}]
    client = Client()
    results = []
    for task, item in (state.get("tasks") or {}).items():
        run_id = item.get("run_id") if isinstance(item, dict) else None
        if not run_id:
            results.append({"task": task, "action": "skip", "reason": "run_id_missing"})
            continue
        record = {"task": task, "run_id": run_id}
        try:
            before = client.request(run_path(run_id))
            before = before.get("run", before)
            record["before"] = before.get("status")
            if before.get("submission_id") != submission_id:
                record["action"] = "skip"
                record["reason"] = "submission_mismatch"
            elif before.get("status") in TERMINAL:
                record["action"] = "skip"
                record["reason"] = "already_terminal"
            else:
                client.request(run_path(run_id) + "/cancel", method="POST")
                after = client.request(run_path(run_id))
                after = after.get("run", after)
                record["after"] = after.get("status")
                record["action"] = "cancel"
                record["confirmed"] = after.get("status") == "CANCELLED"
        except Exception as exc:  # preserve the stop marker even if one cancel is uncertain
            record["action"] = "error"
            record["error"] = type(exc).__name__
        results.append(record)
        append_event(journal, {"event": "cancel", **record})
    return results


def check_once(journal, client, cancel=True):
    try:
        observation = observe_balance(client)
    except GuardError as exc:
        observation = {
            "observed_at": datetime.now(timezone.utc).isoformat(),
            "budget_endpoint": COMPETITION_REGISTRATION,
            "error": str(exc),
        }
        marker = stop(journal, observation, "budget_unavailable")
        return {"status": "stopped", "marker": marker, "cancellations": []}
    append_event(journal, {"event": "balance", **observation})
    if observation["balance"] <= THRESHOLD:
        marker = stop(journal, observation, "balance_below_threshold")
        cancellations = cancel_target_runs(journal) if cancel else []
        return {"status": "stopped", "marker": marker, "cancellations": cancellations}
    return {"status": "clear", "observation": observation}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("journal", type=Path)
    parser.add_argument("--once", action="store_true", help="只查询一次；默认每 600 秒继续查询")
    parser.add_argument("--check", action="store_true", help="查询一次且不取消已启动目标 run")
    args = parser.parse_args()
    journal = target_journal(args.journal)
    client = Client()
    while True:
        result = check_once(journal, client, cancel=not args.check)
        print(json.dumps(result, ensure_ascii=False), flush=True)
        if args.once or args.check:
            return 2 if result["status"] == "stopped" else 0
        state_path = journal / "state.json"
        if state_path.is_file() and json.loads(state_path.read_text()).get("phase") == "collected":
            return 0
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
