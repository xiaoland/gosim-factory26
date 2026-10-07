"""Braid-owned read-only projection reader.

Factory mounts this module; it does not interpret Braid objects itself.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path


def read_projection(path: Path, *, cursor=0, limit=50):
    path = Path(path).resolve(strict=True)
    value = json.loads(path.read_text())
    value.setdefault("as_of", value.get("generated_at"))
    value.setdefault("coverage", "unknown")
    for key in ("sessions", "turns", "objects", "events", "gaps"):
        if isinstance(value.get(key), list):
            value[key] = value[key][max(0, int(cursor)):max(0, int(cursor)) + min(max(int(limit), 1), 200)]
    return value


def artifact_page(path: Path, *, offset=0, bytes_=65536):
    path = Path(path).resolve(strict=True)
    size = min(max(int(bytes_), 1), 1024 * 1024)
    with path.open("rb") as stream:
        stream.seek(max(0, int(offset)))
        data = stream.read(size)
    return {"path": str(path), "offset": max(0, int(offset)), "bytes": len(data), "eof": len(data) < size,
            "data": data.decode("utf-8", errors="replace")}


def _rows(value, *names):
    """Accept the object JSON shapes emitted by the native reconstruct command."""
    if not isinstance(value, dict):
        return []
    tables = value.get("tables") if isinstance(value.get("tables"), dict) else value
    for name in names:
        table = tables.get(name)
        if isinstance(table, dict) and isinstance(table.get("rows"), list):
            return table["rows"]
        if isinstance(table, list):
            return table
    return []


def _session_summary(path, artifact):
    summary = {key: artifact.get(key) for key in ("file", "record_id", "metadata", "bytes", "sha256")}
    latest = {}
    try:
        with Path(path).open("r", encoding="utf-8", errors="replace") as stream:
            for number, line in enumerate(stream):
                if number >= 2048:
                    break
                try:
                    row = json.loads(line)
                except ValueError:
                    continue
                if isinstance(row, dict):
                    latest = row
    except (OSError, UnicodeError):
        return summary
    metadata = latest.get("metadata") if isinstance(latest.get("metadata"), dict) else {}
    for out, keys in (("session_id", ("session_id", "session", "id")),
                      ("state", ("state", "status", "lifecycle")),
                      ("last_activity_at", ("last_activity_at", "timestamp", "observed_at", "at"))):
        for key in keys:
            if latest.get(key) is not None:
                summary[out] = latest[key]
                break
            if metadata.get(key) is not None:
                summary[out] = metadata[key]
                break
    return summary


def _evidence_records(decoded_batches, run_id):
    for item in decoded_batches:
        batch = item.get("batch", {})
        if batch.get("signal") != "logs":
            continue
        for resource in batch.get("data", {}).get("resourceLogs", []):
            for scope in resource.get("scopeLogs", []):
                for row in scope.get("logRecords", []):
                    body = row.get("body", {}).get("stringValue")
                    if not isinstance(body, str):
                        continue
                    try:
                        record = json.loads(body)
                    except ValueError:
                        continue
                    if (isinstance(record, dict) and
                            str(record.get("event_kind", "")).startswith("evidence_") and
                            (run_id is None or record.get("run_id") == run_id)):
                        yield record


def materialize(database: Path, output: Path, *, braid="braid", run_id=None,
                experiment_run_id=None, cache=None):
    """Decode new batches and atomically publish one cumulative Braid projection.

    This is deliberately a worker operation, never called from an HTTP handler.
    ``cache`` and ``output`` must live below the producer-owned records directory.
    The decoded JSON is cumulative, while reconstruction uses a fresh staging
    directory so a failed rebuild cannot replace the last good projection.
    """
    from lab import otlp

    output = Path(output).resolve()
    cache = Path(cache or output.parent / "braid-cache").resolve()
    cache.mkdir(parents=True, exist_ok=True)
    state_path = cache / "decoded.json"
    state = {"schema_version": 1, "batches": [], "errors": []}
    if state_path.is_file():
        state = json.loads(state_path.read_text())
    decoded_batches = state.setdefault("decoded_batches", [])
    if not decoded_batches and state.get("batches"):
        # Invalidate the pre-cumulative cache format; its decoded entries had
        # no collector batch identity and cannot safely advance a cursor.
        state.pop("last_batch_id", None)
    after_id = int(state.get("last_batch_id") or 0)
    batches = otlp.list_batches(Path(database), after_id=after_id, limit=500)
    fresh = batches
    if not fresh and output.is_file() and not state.get("reconstruct_failed"):
        return {"changed": False, "as_of": state.get("as_of"), "projection": str(output)}
    for batch in fresh:
        with tempfile.TemporaryDirectory(prefix="batch-", dir=cache) as temp:
            temp_path = Path(temp)
            pb = temp_path / f'{int(batch["id"]):020d}-{batch["signal"]}.pb'
            pb.write_bytes(otlp.read_batch(Path(database), int(batch["id"]))[1])
            command = [str(braid), "telemetry", "decode", "--input", str(temp_path)]
            result = subprocess.run(command, check=False, capture_output=True, text=True)
            if result.returncode:
                state.setdefault("errors", []).append({"batch": batch["id"], "error": result.stderr[-2000:]})
                state["decode_failed_batch"] = int(batch["id"])
                break
            decoded = json.loads(result.stdout)
            decoded_items = decoded.get("batches", [])
            for item in decoded_items:
                decoded_batches.append({"id": int(batch["id"]), "batch": item})
            state.setdefault("errors", []).extend(decoded.get("errors", []))
        state["last_batch_id"] = int(batch["id"])
    if state.get("decode_failed_batch"):
        # Do not advance past a failed batch: a later invocation must retry it.
        fresh = [batch for batch in fresh if int(batch["id"]) < int(state["decode_failed_batch"])]
    cutoff = fresh[-1] if fresh else None
    state["cutoff_batch_id"] = int(cutoff["id"]) if cutoff else state.get("cutoff_batch_id")
    state["cutoff_received_at"] = cutoff.get("received_at") if cutoff else state.get("cutoff_received_at")
    state["as_of"] = state.get("cutoff_received_at")
    state["updated_at"] = time.time()
    state_tmp = state_path.with_suffix(".tmp")
    state_tmp.write_text(json.dumps(state, ensure_ascii=False))
    os.replace(state_tmp, state_path)
    records = list(_evidence_records(decoded_batches, run_id))
    portable = any(record.get("event_kind") == "evidence_snapshot" for record in records)
    if not portable:
        summaries = [record for record in records if record.get("event_kind") == "evidence_summary"]
        summary = max(summaries, key=lambda row: int(row.get("captured_at_unix_nanos", 0)), default={})
        current = summary.get("current", {})
        errors = list(summary.get("gaps", []))
        if not current:
            errors.append("No collaboration snapshot received; legacy Summary only contains inventory.")
        projection = {"schema_version": 1, "run_id": summary.get("run_id", run_id),
                      "experiment_run_id": experiment_run_id, "as_of": state.get("as_of"),
                      "cutoff_batch_id": state.get("cutoff_batch_id"),
                      "cutoff_received_at": state.get("cutoff_received_at"),
                      "coverage": "partial", "status": "current-state" if current else "unavailable",
                      "artifacts": [], "batches": len(decoded_batches), "errors": errors,
                      **{name: current.get(name, []) for name in ("objects", "sessions", "turns", "events")}}
        published = output.with_suffix(".tmp")
        published.write_text(json.dumps(projection, ensure_ascii=False))
        os.replace(published, output)
        state.pop("reconstruct_failed", None)
        return {"changed": True, "as_of": projection["as_of"], "projection": str(output)}
    stage = Path(tempfile.mkdtemp(prefix="projection-", dir=cache))
    try:
        evidence = stage / "evidence"
        decoded_path = stage / "decoded.json"
        decoded_path.write_text(json.dumps({"schema_version": 1,
                                             "batches": [item["batch"] for item in decoded_batches],
                                             "errors": state.get("errors", [])}, ensure_ascii=False))
        command = [str(braid), "telemetry", "reconstruct", "--input", str(cache), "--decoded", str(decoded_path), "--output", str(evidence)]
        if run_id:
            command.extend(["--run-id", run_id])
        result = subprocess.run(command, check=False, capture_output=True, text=True)
        if result.returncode:
            state.setdefault("errors", []).append({"reconstruct": result.stderr[-2000:]})
            state["reconstruct_failed"] = True
            state_tmp.write_text(json.dumps(state, ensure_ascii=False))
            os.replace(state_tmp, state_path)
            return {"changed": False, "as_of": state.get("as_of"), "error": result.stderr[-2000:]}
        summary = json.loads(result.stdout)
        state.pop("reconstruct_failed", None)
        durable = cache / f"evidence-{state.get('as_of') or 'empty'}"
        if durable.exists():
            shutil.rmtree(durable)
        shutil.move(str(evidence), str(durable))
        errors = list(state.get("errors", [])) + list(summary.get("gaps", []))
        artifacts = [{**item, "path": str(durable / item["file"])} for item in summary.get("artifacts", [])]
        sessions = [_session_summary(item["path"], item)
                    for item in artifacts if item.get("logical_type") == "native_session"]
        objects, turns, events = [], [], []
        object_artifact = next((item for item in artifacts if item.get("logical_type") == "objects"), None)
        if object_artifact and Path(object_artifact["path"]).is_file():
            object_value = json.loads(Path(object_artifact["path"]).read_text())
            objects = list(_rows(object_value, "objects", "work_items", "object"))[:5000]
            turns = list(_rows(object_value, "turns", "turn", "messages"))[:5000]
            events = list(_rows(object_value, "events", "event"))[:5000]
        coverage = "unknown" if not decoded_batches else ("complete" if not errors and not state.get("errors") else "partial")
        projection = {"schema_version": 1, "run_id": run_id, "experiment_run_id": experiment_run_id,
                      "as_of": state.get("as_of"), "cutoff_batch_id": state.get("cutoff_batch_id"),
                      "cutoff_received_at": state.get("cutoff_received_at"), "coverage": coverage,
                      "status": summary.get("status"), "summary": summary,
                      "artifacts": artifacts, "sessions": sessions, "objects": objects,
                      "turns": turns, "events": events, "batches": len(decoded_batches), "errors": errors}
        published = output.with_suffix(".tmp")
        published.write_text(json.dumps(projection, ensure_ascii=False))
        os.replace(published, output)
        return {"changed": True, "as_of": projection["as_of"], "projection": str(output)}
    finally:
        shutil.rmtree(stage, ignore_errors=True)
