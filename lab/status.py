"""Read lab records and show execution facts without interpreting Agent sessions."""

from pathlib import Path

from .control import owner_state
from .records import experiment_paths, read_json


def read_status(run):
    run = Path(run).resolve()
    state = read_json(run / "run.json")
    if not isinstance(state, dict) or state.get("schema_version") not in (1, 2):
        raise ValueError(f"invalid lab run record: {run / 'run.json'}")
    return {**state, "path": str(run)}


def is_lab_run(state):
    return state.get("record_type") == "lab.run" or (
        state.get("schema_version") == 1 and "result_path" in state and "run_id" in state)


def run_rows(root):
    root = Path(root).expanduser().resolve()
    if (root / "run.json").is_file():
        return [read_status(root)]
    if (root / "manifest.json").is_file():
        manifest = read_json(root / "manifest.json")
        root = experiment_paths(root)[1] if manifest.get("record_type") == "lab.experiment" else root / "runs"
    elif (root / "runs").is_dir():
        root = root / "runs"
    rows = []
    for child in root.iterdir():
        if child.is_dir() and (child / "run.json").is_file():
            state = read_status(child)
            if is_lab_run(state):
                rows.append(state)
    return rows


def _latest(rows):
    explicit = [row for row in rows if isinstance(row.get("attempt"), int)]
    if explicit and len(explicit) == len(rows):
        return max(rows, key=lambda row: row["attempt"])
    newest = max((row.get("created_at") for row in rows if isinstance(row.get("created_at"), (int, float))),
                 default=None)
    matches = [row for row in rows if row.get("created_at") == newest] if newest is not None else []
    return matches[0] if len(matches) == 1 else None


def _state(row):
    if row.get("schema_version") == 2:
        phase = row.get("phase", "unknown")
        if phase in ("running", "queued"):
            run = Path(row["path"])
            experiment = run.parent.parent
            if not (experiment / "manifest.json").is_file():
                experiment = run.parent / ".experiments" / row.get("experiment_id", "")
            active_path = experiment / "active.json"
            active = read_json(active_path) if active_path.is_file() else None
            if not active or active.get("phase") != "running" or active.get("controller_id") != row.get(
                    "controller") or owner_state(active) != "alive":
                return "unconfirmed"
        return phase
    phase = row.get("phase", "unknown")
    return "unconfirmed" if phase in ("running", "queued") else phase


def _legacy_key(row):
    return " / ".join(str(row.get(name) or "?") for name in ("competition", "variant", "task"))


def _job_key(row):
    return f"{row['experiment_id']}/{row['job_id']}" if row.get("experiment_id") and row.get("job_id") else _legacy_key(row)


def experiment_summary(root):
    root = Path(root).expanduser().resolve()
    manifest = None
    if (root / "manifest.json").is_file():
        manifest = read_json(root / "manifest.json")
    rows = run_rows(root)
    if manifest and manifest.get("record_type") == "lab.experiment":
        rows = [row for row in rows if row.get("experiment_id") == manifest["experiment_id"]]
    jobs = {}
    if manifest and manifest.get("record_type") == "lab.experiment":
        jobs = {f"{manifest['experiment_id']}/{job['id']}": {"key": f"{manifest['experiment_id']}/{job['id']}",
                                 "job_id": job["id"], "labels": job.get("labels", {}),
                                 "preparation": job.get("preparation"), "attempts": []}
                for job in manifest["jobs"]}
    for row in rows:
        key = _job_key(row)
        job = jobs.setdefault(key, {"key": key, "job_id": row.get("job_id") or key, "labels": {
            name: row.get(name) for name in ("competition", "variant", "task")}, "attempts": []})
        job["attempts"].append({"run_id": row["run_id"], "path": row["path"],
                                "labels": row.get("labels", {}), "retry_of": row.get("retry_of"),
                                "phase": _state(row), "started_at": row.get("started_at"),
                                "finished_at": row.get("finished_at"), "error": row.get("error"),
                                "attempt": row.get("attempt"), "created_at": row.get("created_at")})
    for job in jobs.values():
        job["attempts"].sort(key=lambda item: (item.get("attempt") or 0,
                                               item.get("created_at") or 0, item["run_id"]))
        matches = [row for row in rows if _job_key(row) == job.get("key", job["job_id"])]
        if matches:
            latest = _latest(matches)
            valid = [row for row in matches if (row.get("phase") in ("completed", "finished") and
                      isinstance(row.get("result"), dict) and row["result"].get("status") == "completed")]
            job["latest"] = latest["run_id"] if latest else None
            job["latest_labels"] = latest.get("labels", {}) if latest else {}
            job["latest_phase"] = _state(latest) if latest else "order-unknown"
            job["latest_result_status"] = (latest.get("result") or {}).get("status") if latest and isinstance(
                latest.get("result"), dict) else None
            job["latest_exit_code"] = latest.get("runner_exit_code") if latest else None
            job["latest_result_contract"] = latest.get("result_contract") if latest else None
            valid_latest = _latest(valid) if valid else None
            job["latest_valid_result"] = valid_latest["run_id"] if valid_latest else None
        else:
            job["latest"] = None
            job["latest_labels"] = {}
            job["latest_phase"] = job.get("preparation", {}).get("status", "unstarted")
            job["latest_result_status"] = None
            job["latest_exit_code"] = None
            job["latest_result_contract"] = None
            job["latest_valid_result"] = None
    attempt_phases = {}
    for row in rows:
        phase = _state(row)
        attempt_phases[phase] = attempt_phases.get(phase, 0) + 1
    return {"kind": "experiment", "path": str(root),
            "experiment_id": manifest.get("experiment_id") if manifest else None,
            "comparison": manifest.get("comparison") if manifest else None,
            "planned_jobs": len(jobs), "attempts": len(rows),
            "started_attempts": sum(row.get("started_at") is not None for row in rows),
            "attempt_phases": attempt_phases,
            "jobs": list(jobs.values())}


def show_run(run):
    row = read_status(run)
    if not is_lab_run(row):
        raise ValueError(f"not a lab experiment run: {run}")
    result = row.get("result")
    result_path = row.get("result_path")
    if result_path:
        path = Path(run) / result_path
        if path.is_file() and path.resolve().is_relative_to(Path(run).resolve()):
            try:
                result = read_json(path)
                if not isinstance(result, dict):
                    raise ValueError("result must be a JSON object")
            except (OSError, ValueError) as exc:
                result = {"error": f"{type(exc).__name__}: {exc}", "path": str(path)}
    replay = None
    replay_path = None
    for relative in ("workspace/official/template/.arc/replay.json",
                     "workspace/official-generation/template/.arc/replay.json"):
        path = Path(run) / relative
        if path.is_file():
            try:
                replay = read_json(path)
                replay_path = path
            except (OSError, ValueError):
                pass
            break
    evidence = {name: str(Path(run) / name) for name in ("stdout.log", "stderr.log", "telemetry.sqlite")
                if (Path(run) / name).is_file()}
    for path in sorted((Path(run) / "events").glob("*.jsonl")):
        evidence[f"events/{path.name}"] = str(path)
    for path in sorted((Path(run) / "workspace").glob("*.resource.json")):
        evidence[f"workspace/{path.name}"] = str(path)
    for relative in ("artifacts/index.json", "artifacts/gateway-export-result.json"):
        path = Path(run) / relative
        if path.is_file():
            evidence[relative] = str(path)
    origin = row.get("source_application") or {}
    if origin.get("run_id"):
        candidates = [Path(origin["run_path"])] if origin.get("run_path") else [Path(run).parent / origin["run_id"]]
        for candidate in candidates:
            if (candidate / "run.json").is_file() and read_json(candidate / "run.json").get("run_id") == origin["run_id"]:
                evidence["source_run"] = str(candidate)
                break
    if replay is not None:
        evidence["application_source"] = {"run_id": replay.get("run_id"),
                                           "application_sha256": replay.get("application_sha256"),
                                           "evidence": str(replay_path), "verification": "producer-declared"}
    for relative in ("workspace/official/execution.debug.log",
                     "workspace/official-generation/execution.debug.log",
                     "workspace/official-evaluation/execution.debug.log"):
        if (Path(run) / relative).is_file():
            evidence[relative] = str(Path(run) / relative)
    analyses = []
    root = Path(run).parent.parent
    if not (root / "manifest.json").is_file() and row.get("experiment_id"):
        root = Path(run).parent / ".experiments" / row["experiment_id"]
    for path in (root / "analysis").glob("*/analysis.json"):
        try:
            record = read_json(path)
            if row["run_id"] in record.get("run_ids", []) or record.get("run_id") == row["run_id"]:
                analyses.append({"path": str(path), "record": record})
        except (OSError, ValueError):
            continue
    return {"kind": "run", "run_id": row["run_id"], "path": row["path"],
            "phase": _state(row), "observed_phase": row.get("phase"),
            "controller": row.get("controller"), "job_id": row.get("job_id"),
            "experiment_id": row.get("experiment_id"), "attempt": row.get("attempt"),
            "labels": row.get("labels", {}), "retry_of": row.get("retry_of"),
            "source_application": row.get("source_application"),
            "process_exit_code": row.get("runner_exit_code"), "result": result,
            "result_contract": row.get("result_contract"), "result_error": row.get("result_error"),
            "error": row.get("error") or row.get("controller_error"),
            "cancellation": row.get("cancellation"), "evidence": evidence,
            "telemetry": row.get("telemetry"), "artifacts": row.get("artifacts"),
            "telemetry_error": row.get("telemetry_error"), "artifact_error": row.get("artifact_error"),
            "analysis": analyses}


def show(reference):
    path = Path(reference).expanduser().resolve()
    return show_run(path) if (path / "run.json").is_file() else experiment_summary(path)
