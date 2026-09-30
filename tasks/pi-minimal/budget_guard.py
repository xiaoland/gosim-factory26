#!/usr/bin/env python3
"""Observe pi-minimal usage and guard the legacy official journal.

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
from usage_budget import active_cost


TARGET = (ROOT / "runs/pi-minimal/20260929/official").resolve()
SELF_FUNDED_TARGET = (ROOT / "runs/pi-minimal/20260930/self-funded").resolve()
STOP_NAME = "budget-stop.json"
EVENTS_NAME = "budget-events.jsonl"
COMPETITION = "hackathon"
COMPETITION_REGISTRATION = "/competitions/hackathon/registration"
THRESHOLD = 100.0
INTERVAL = 600


class GuardError(RuntimeError):
    """A balance observation or journal identity could not be trusted."""


def target_journal(value, self_funded=False):
    path = Path(value).expanduser().resolve()
    expected = SELF_FUNDED_TARGET if self_funded else TARGET
    if path != expected:
        kind = "self_funded" if self_funded else "官方"
        raise GuardError(f"只允许 pi-minimal {kind} journal：{expected}")
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
        usage = active_cost(journal, client)
    except Exception as exc:
        usage = {'cost_cny': 0, 'incomplete': True, 'error': str(exc), 'runs': []}
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
    observation.update(usage=usage, estimated_balance=observation['balance'] - usage['cost_cny'])
    append_event(journal, {"event": "estimated_balance", **observation})
    if observation["estimated_balance"] <= THRESHOLD:
        marker = stop(journal, observation, "balance_below_threshold")
        cancellations = cancel_target_runs(journal) if cancel else []
        return {"status": "stopped", "marker": marker, "cancellations": cancellations}
    return {"status": "usage_unknown" if usage.get('incomplete') else "clear", "observation": observation}


def observe_self_funded(journal, client):
    """Record known direct-provider usage without inventing a stop threshold."""
    try:
        usage = active_cost(journal, client, tariff_name='provider-prices.json',
                            include_terminal=True)
    except Exception as exc:
        usage = {
            'cost_cny': 0,
            'cost_status': 'unknown',
            'incomplete': True,
            'error': type(exc).__name__,
            'runs': [],
        }
    observation = {
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "billing_mode": "self_funded",
        "journal": str(journal),
        "stop_policy": "none",
        "usage": usage,
    }
    append_event(journal, {"event": "self_funded_usage", **observation})
    return {
        "status": "observed" if not usage.get("incomplete") else "usage_unknown",
        "observation": observation,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("journal", type=Path)
    parser.add_argument("--self-funded-observe", action="store_true",
                        help="观察自费 provider usage；不查询比赛余额、不取消 run")
    parser.add_argument("--once", action="store_true", help="只查询一次；默认每 600 秒继续查询")
    parser.add_argument("--check", action="store_true", help="查询一次且不取消已启动目标 run")
    args = parser.parse_args()
    journal = target_journal(args.journal, self_funded=args.self_funded_observe)
    client = Client()
    while True:
        started = time.monotonic()
        result = (observe_self_funded(journal, client) if args.self_funded_observe
                  else check_once(journal, client, cancel=not args.check))
        print(json.dumps(result, ensure_ascii=False), flush=True)
        if args.once or args.check:
            return 2 if result["status"] == "stopped" else 0
        state_path = journal / "state.json"
        if state_path.is_file() and json.loads(state_path.read_text()).get("phase") == "collected":
            return 0
        time.sleep(max(0, INTERVAL - (time.monotonic() - started)))


if __name__ == "__main__":
    main()
