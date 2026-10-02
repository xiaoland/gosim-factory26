#!/usr/bin/env python3
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from lab.arc_bench.playground import ApiError, Client, redact, run_path, save


RUNS = ("caf2d2f23e13", "17bffdd4a8b0", "7207a7fe0845")
TERMINAL = {"PASSED", "FAILED", "CANCELLED"}
OUTPUT = Path("runs/issue-decomposition/20260925-hackathon/monitoring")


def request(client, run_id, endpoint=""):
    try:
        return {"ok": True, "value": redact(client.request(run_path(run_id) + endpoint))}
    except ApiError as error:
        return {"ok": False, "error": type(error).__name__, "status": error.status,
                "detail": redact(error.detail)}
    except Exception as error:
        return {"ok": False, "error": type(error).__name__, "message": str(error)}


def poll(client, sequence):
    observed_at = datetime.now(timezone.utc).isoformat()
    result = {"observed_at": observed_at, "runs": {}}
    for run_id in RUNS:
        response = request(client, run_id)
        result["runs"][run_id] = response
        folder = OUTPUT / run_id
        folder.mkdir(parents=True, exist_ok=True)
        save(folder / f"status-{sequence:04d}.json", {"observed_at": observed_at, **response})
    save(OUTPUT / "latest.json", result)
    return result


def collect(client, result):
    for run_id, response in result["runs"].items():
        value = response.get("value", {})
        if value.get("status") not in TERMINAL:
            continue
        folder = OUTPUT / run_id / "terminal"
        folder.mkdir(parents=True, exist_ok=True)
        for name, endpoint in (("logs", "/logs?log_offset=0"),
                               ("traceability", "/traceability?node_id=__all__"),
                               ("commit-history", "/commit-history")):
            save(folder / f"{name}.json", request(client, run_id, endpoint))


def summary(result):
    return {run_id: ({"monitor_error": response.get("error"), "http_status": response.get("status")}
                     if not response.get("ok") else
                     {key: response["value"].get(key) for key in
                      ("status", "score", "passed_count", "failed_count", "total_tests",
                       "run_duration_seconds", "started_at", "finished_at", "failure_reason")})
            for run_id, response in result["runs"].items()}


def main():
    client = Client()
    sequence = 0
    while True:
        result = poll(client, sequence)
        failed = any(not response.get("ok") for response in result["runs"].values())
        terminal = not failed and all(response["value"].get("status") in TERMINAL
                                      for response in result["runs"].values())
        if sequence == 0 or failed or terminal:
            print(json.dumps({"event": "monitor_error" if failed else
                              "terminal" if terminal else "initial",
                              "evidence": str(OUTPUT), "runs": summary(result)},
                             ensure_ascii=False), flush=True)
        if failed:
            return 2
        if terminal:
            collect(client, result)
            return 0
        sequence += 1
        time.sleep(900)


if __name__ == "__main__":
    sys.exit(main())
