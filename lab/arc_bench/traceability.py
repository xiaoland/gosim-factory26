"""Collect and inspect ARC traceability evidence without interpreting a Harness."""

import argparse
from io import BytesIO
import hashlib
import json
from pathlib import Path
import time
from zipfile import BadZipFile, ZipFile


def collect_hosted(client, endpoint, folder, name, *, save, redact, latest_wrapped=True):
    """Keep every API observation; a failed refresh must not replace the last success."""
    folder = Path(folder)
    history = folder / "observations" / name
    history.mkdir(parents=True, exist_ok=True)
    observed_at = time.time()
    try:
        value = redact(client.request(endpoint))
    except Exception as exc:
        error = {"type": type(exc).__name__, "message": str(exc)}
        for field in ("status", "detail"):
            if hasattr(exc, field):
                error[field] = redact(getattr(exc, field))
        record = {"observed_at": observed_at, "source": endpoint,
                  "status": "failed", "error": redact(error)}
    else:
        record = {"observed_at": observed_at, "source": endpoint,
                  "status": "completed", "value": value}
    save(history / f"{time.time_ns()}.json", record)
    # A terminal workspace_unavailable response is observed, but must not erase live history.
    unavailable_history = (name == "commit-history" and record["status"] == "completed" and
                           isinstance(record["value"], dict) and
                           record["value"].get("availability") == "workspace_unavailable")
    if record["status"] == "completed" and not unavailable_history:
        save(folder / (name + ".json"),
             {"observed_at": observed_at, "source": endpoint, "value": value}
             if latest_wrapped else value)
    return record


def _read(path):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError) as exc:
        return {"read_error": f"{type(exc).__name__}: {exc}", "path": str(path)}


def _support(package):
    if not package or not package.exists():
        return {"status": "unknown"}
    try:
        if package.is_dir():
            payloads = [(str(path), path.read_bytes()) for path in sorted(package.rglob("*.pyz"))
                        if path.is_file() and path.stat().st_size <= 1024 * 1024]
        else:
            with ZipFile(package) as archive:
                payloads = [(entry.filename, archive.read(entry)) for entry in archive.infolist()
                            if Path(entry.filename).suffix == ".pyz" and entry.file_size <= 1024 * 1024]
        for name, payload in payloads:
            try:
                with ZipFile(BytesIO(payload)) as runtime:
                    source = json.loads(runtime.read("SOURCE.json"))
            except (BadZipFile, KeyError, ValueError):
                continue
            if source.get("name") == "arcbench-agent-runtime":
                return {"status": "present", "package": str(package), "path": name,
                        "sha256": hashlib.sha256(payload).hexdigest(),
                        "sdk_version": source.get("version")}
    except (OSError, BadZipFile, ValueError) as exc:
        return {"status": "unreadable", "package": str(package),
                "error": f"{type(exc).__name__}: {exc}"}
    return {"status": "unknown", "package": str(package)}


def _related(row, node, key=None):
    if node is None:
        return False
    if key == node:
        return True
    if not isinstance(row, dict):
        return False
    if node in (row.get("req_id"), row.get("node_id"), row.get("source_req_id"),
                row.get("target_req_id")):
        return True
    return node in (row.get("req_ids") or [])


def _trace_dir(folder):
    default = folder / "template/.arc/traceability"
    spec = folder / "runner-spec.json"
    if not spec.is_file():
        return default, None
    record = _read(spec)
    if not isinstance(record, dict):
        return default, f"{spec}: Runner spec must be a JSON object"
    if "read_error" in record:
        return default, f"{spec}: {record['read_error']}"
    configured = record.get("traceability_dir")
    if not isinstance(configured, str) or not configured.strip():
        return default, None
    path = Path(configured)
    if path.is_absolute():
        try:
            path = folder / path.relative_to("/workspace")
        except ValueError:
            return default, f"{spec}: traceability_dir is outside the saved Runner workspace: {configured}"
    else:
        path = folder / "template" / path
    if not path.resolve().is_relative_to(folder.resolve()):
        return default, f"{spec}: traceability_dir escapes the saved Runner workspace: {configured}"
    return path, None


def _local(run, node):
    state = _read(run / "run.json")
    agent = state.get("inputs", {}).get("agent", {}).get("path") if isinstance(state, dict) else None
    evidence = []
    for name in ("official-generation", "official-evaluation", "official"):
        root = run / "workspace" / name / "template" / ".arc"
        if not root.is_dir():
            continue
        tables = {}
        matches = {}
        trace_dir, trace_error = _trace_dir(run / "workspace" / name)
        for path in sorted(trace_dir.glob("*.json")):
            data = _read(path)
            tables[path.stem] = {"path": str(path), "rows": len(data) if isinstance(data, dict)
                                 and "read_error" not in data else None,
                                 "error": data.get("read_error") if isinstance(data, dict) else "not a JSON object"}
            if node and isinstance(data, dict) and "read_error" not in data:
                selected = [value for key, value in data.items() if _related(value, node, key)]
                if selected:
                    matches[path.stem] = selected
        events = root / "runner-events.jsonl"
        operations = root / "runtime-reporting" / "operations.jsonl"
        calls = []
        operation_error = None
        if operations.is_file():
            try:
                for number, line in enumerate(operations.read_text().splitlines(), 1):
                    try:
                        calls.append(json.loads(line))
                    except ValueError as exc:
                        calls.append({"line": number, "read_error": str(exc)})
            except (OSError, UnicodeError) as exc:
                operation_error = f"{type(exc).__name__}: {exc}"
        linked = [tables.get(table, {}).get("rows") for table in ("interfaces", "tests")]
        evidence.append({"phase": name, "traceability_dir": str(trace_dir),
                         "traceability_path_error": trace_error,
                         "tables": tables, "node_matches": matches,
                         "relationships": "available" if any(count for count in linked if count is not None)
                         else "empty" if all(count is not None for count in linked) else "unknown",
                         "runner_events": str(events) if events.is_file() else None,
                         "operation_log": str(operations) if operations.is_file() else None,
                         "operations": {"status": "unreadable" if operation_error else "observed" if calls else "unknown",
                                        "completed": sum(row.get("status") == "completed" for row in calls),
                                        "failed": sum(row.get("status") == "failed" for row in calls),
                                        "read_error": operation_error,
                                        "last_error": next((row.get("error") or row.get("read_error")
                                                            for row in reversed(calls) if row.get("error")
                                                            or row.get("read_error")), None)}})
    return {"kind": "local", "run": str(run), "support": _support(run / agent if agent else None),
            "source_application": state.get("source_application") if isinstance(state, dict) else None,
            "evidence": evidence}


def _hosted_history(folder):
    history_archive = folder / "commit-history.json"
    history_observations = sorted((folder / "observations" / "commit-history").glob("*.json"))
    history_attempt = _read(history_observations[-1]) if history_observations else (
        _read(history_archive) if history_archive.is_file() else None)
    history_available = None
    history_path = None
    for candidate in reversed(([history_archive] if history_archive.is_file() else []) +
                              history_observations):
        record = _read(candidate)
        candidate_value = record.get("value", record) if isinstance(record, dict) else None
        if (isinstance(candidate_value, dict) and
                candidate_value.get("availability") != "workspace_unavailable" and
                isinstance(candidate_value.get("commits"), list)):
            history_available, history_path = record, candidate
            break
    attempt_value = history_attempt.get("value", history_attempt) if isinstance(history_attempt, dict) else None
    available_value = history_available.get("value", history_available) if history_available else None
    attempt_details = None
    if isinstance(history_attempt, dict):
        attempt_details = {key: history_attempt[key] for key in
                           ("observed_at", "source", "status", "error", "read_error")
                           if key in history_attempt}
        if isinstance(attempt_value, dict):
            attempt_details["availability"] = attempt_value.get("availability")
    return {"status": "available" if history_available else
                      "unavailable" if history_attempt else "unknown",
            "last_attempt": attempt_details,
            "last_available": {"observed_at": history_available.get("observed_at"),
                               "source": history_available.get("source"),
                               "path": str(history_path),
                               "commits": len(available_value["commits"])}
                              if history_available else None}


def _hosted(folder, node):
    archive = folder / "traceability.json"
    latest = _read(archive) if archive.is_file() else None
    observations = sorted((folder / "observations" / "traceability").glob("*.json"))
    attempt = _read(observations[-1]) if observations else latest
    success = None
    success_path = archive
    for path in reversed(observations):
        record = _read(path)
        if isinstance(record, dict) and record.get("status") == "completed":
            success, success_path = record, path
            break
    if success is None and isinstance(latest, dict) and "read_error" not in latest:
        if "value" in latest and "observed_at" in latest:
            success = latest
        else:
            observation = _read(folder / "observation.json") if (folder / "observation.json").is_file() else {}
            success = {"value": latest, **observation.get("traceability", {})}
    if not observations and success is not None:
        attempt = {"status": "completed", **success}
    value = success.get("value") if isinstance(success, dict) else None
    tables = {name: len(rows) for name, rows in value.items() if isinstance(rows, list)} if isinstance(value, dict) else {}
    matches = {}
    if node and isinstance(value, dict):
        matches = {name: selected for name, rows in value.items() if isinstance(rows, list)
                   if (selected := [row for row in rows if _related(row, node)])}
    package = folder.parent.parent / "agent.zip" if (folder.parent.parent / "inputs.json").is_file() else None
    known = (isinstance(value, dict) and isinstance(value.get("interfaces"), list)
             and isinstance(value.get("tests"), list))
    return {"kind": "hosted", "task": str(folder), "support": _support(package),
            "tool_usage": {"status": "unknown", "reason": "hosted tool operation file was not downloaded"},
            "traceability": {"status": ("available" if tables.get("interfaces", 0) + tables.get("tests", 0) > 0 else "empty")
                             if known else "unavailable",
                             "tables": tables, "node_matches": matches,
                             "last_attempt": {key: attempt.get(key) for key in
                                              ("observed_at", "source", "status", "error", "read_error") if key in attempt}
                             if isinstance(attempt, dict) else None,
                             "last_success": {"observed_at": success.get("observed_at"),
                                              "source": success.get("source"), "path": str(success_path)}
                             if isinstance(success, dict) else None},
            "commit_history": _hosted_history(folder)}


def inspect(path, node=None):
    path = Path(path).expanduser().resolve(strict=True)
    if (path / "run.json").is_file():
        return _local(path, node)
    if ((path / "traceability.json").is_file() or (path / "observations" / "traceability").is_dir()
            or (path / "commit-history.json").is_file()
            or (path / "observations" / "commit-history").is_dir()):
        return _hosted(path, node)
    raise ValueError(f"no ARC run or hosted task evidence at {path}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="lab run directory or hosted task evidence directory")
    parser.add_argument("--node", help="show saved records associated with this official requirement ID")
    parser.add_argument("--json", action="store_true", help="compact machine-readable output")
    args = parser.parse_args(argv)
    result = inspect(args.path, args.node)
    print(json.dumps(result, ensure_ascii=False, indent=None if args.json else 2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
