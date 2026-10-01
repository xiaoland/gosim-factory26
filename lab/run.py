"""Dispatch frozen external commands and preserve independent outcome facts."""

from collections import deque
import json
import os
from pathlib import Path
from queue import Empty
import re
import secrets
import signal
import sqlite3
import subprocess
import sys
from threading import Event, Thread
import time

from .assets import frozen_host_runtime
from .control import Control, exclusive, process_identity, process_state
from .docker_endpoint import freeze as freeze_docker, environment as docker_environment
from .otlp import SIGNALS, database_for_run, initialize, list_batches, new_session, receiver
from .plan import create
from .records import merge_labels, read_json, write_json
from .status import read_status


NAME = re.compile(r"[a-z][a-z0-9_]*\Z")
PLACEHOLDER = re.compile(r"\{([a-z][a-z0-9_]*)\}")


def safe_relative(value):
    path = Path(value)
    if path.is_absolute() or not path.parts or any(part in (".", "..") for part in path.parts):
        raise ValueError(f"path must stay within this run: {value}")
    return path


def _run_root(experiment, manifest):
    root = (Path(experiment) / manifest["runs_root"]).resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def _job_inputs(experiment, run, job):
    mapping = {"run_id": run.name, "run_dir": str(run), "workspace": str(run / "workspace"),
               "artifacts": str(run / "artifacts")}
    frozen = {}
    for name, item in job["inputs"].items():
        if not NAME.fullmatch(name) or name in mapping:
            raise ValueError(f"invalid input name: {name}")
        source = Path(experiment) / "inputs" / item["id"] / item["content"]
        target = run / "inputs" / name
        target.symlink_to(os.path.relpath(source.parent if source.is_file() else source, target.parent),
                          target_is_directory=True)
        actual = target / source.name if source.is_file() else target
        mapping[name] = str(actual)
        frozen[name] = {"path": str(actual.relative_to(run)), "sha256": item["sha256"],
                        "algorithm": item["algorithm"], "source": str(source)}
    return mapping, frozen


def _expand(argv, mapping):
    def expand(argument):
        def substitute(match):
            if match[1] not in mapping:
                raise ValueError(f"unknown command placeholder: {match[1]}")
            return mapping[match[1]]
        return PLACEHOLDER.sub(substitute, argument)
    return [expand(argument) for argument in argv]


def _previous(runs, experiment_id, job_id):
    found = []
    for path in runs.iterdir():
        if not path.is_dir() or not (path / "run.json").is_file():
            continue
        row = read_json(path / "run.json")
        if row.get("experiment_id") == experiment_id and row.get("job_id") == job_id:
            found.append(row)
    return found


def execution_labels(manifest, requested):
    """Validate all per-job execution labels before allocating any attempt."""
    if requested is None:
        return {}
    jobs = {job["id"]: job for job in manifest["jobs"]}
    if not isinstance(requested, dict) or any(key not in jobs for key in requested):
        raise ValueError("run labels must map known job IDs to label objects")
    for key, labels in requested.items():
        merge_labels(jobs[key].get("labels", {}), labels)
    return requested


def _storage_preflight(experiment, manifest, slots, *, retry=False):
    root = _run_root(experiment, manifest)
    policy = manifest.get("storage")
    observed_at = time.time()
    identifier = f"{time.time_ns()}-{secrets.token_hex(4)}"
    if policy is None:
        receipt = {"schema_version": 1, "id": identifier, "status": "legacy-unbudgeted",
                   "observed_at": observed_at, "filesystem": str(root)}
    else:
        stats = os.statvfs(root)
        available = stats.f_bavail * stats.f_frsize
        free_inodes = stats.f_favail
        inode_reserve = stats.f_files * policy["inode_reserve_percent"] // 100
        concurrent = 1 if retry else slots
        per_run = (policy["workspace_bytes_per_run"] + policy["telemetry_bytes_per_run"] +
                   policy["finalization_scratch_bytes_per_run"])
        required = (policy["host_reserve_bytes"] + concurrent * per_run +
                    (0 if retry else policy["build_bytes"]))
        ready = available >= required and free_inodes >= inode_reserve
        receipt = {"schema_version": 1, "id": identifier,
                   "status": "ready" if ready else "blocked", "observed_at": observed_at,
                   "filesystem": str(root), "slots": concurrent, "retry": retry,
                   "policy": policy, "available_bytes": available,
                   "required_bytes": required, "free_inodes": free_inodes,
                   "required_free_inodes": inode_reserve}
    destination = Path(experiment) / "storage-preflights" / f"{identifier}.json"
    write_json(destination, receipt)
    write_json(Path(experiment) / "storage-preflight.json", receipt)
    if receipt["status"] == "blocked":
        raise ValueError(
            f"storage preflight blocked: available={receipt['available_bytes']} "
            f"required={receipt['required_bytes']} free_inodes={receipt['free_inodes']} "
            f"required_free_inodes={receipt['required_free_inodes']}; receipt={destination}"
        )
    return receipt


def _allocate(experiment, manifest, controller, retry_of=None, operation_id=None, run_labels=None):
    runs = _run_root(experiment, manifest)
    requested = []
    source = read_status(retry_of) if retry_of else None
    if source and source.get("experiment_id") != manifest["experiment_id"]:
        raise ValueError("retry run belongs to a different experiment")
    if source and (source.get("pid") or source.get("started_at")):
        state = process_state(source)
        if state != "lost":
            raise ValueError(f"source attempt process is {state}; confirm it has exited before retry")
    for job in manifest["jobs"]:
        if job["preparation"]["status"] != "ready":
            continue
        if source and job["id"] != source.get("job_id"):
            continue
        previous = _previous(runs, manifest["experiment_id"], job["id"])
        if previous and not source:
            continue
        attempt = max((row.get("attempt", 0) for row in previous), default=0) + 1
        run_id = f"{job['id']}-{secrets.token_hex(7)}"
        run = runs / run_id
        run.mkdir()
        for name in ("inputs", "workspace", "artifacts", "events"):
            (run / name).mkdir()
        try:
            mapping, frozen = _job_inputs(experiment, run, job)
            preparation_error = None
        except (OSError, ValueError) as exc:
            mapping, frozen = {}, {}
            preparation_error = f"{type(exc).__name__}: {exc}"
        try:
            if preparation_error:
                raise ValueError(preparation_error)
            command = _expand(job["command"], mapping)
            result_path = str(safe_relative(job["result_path"])) if "result_path" in job else None
            artifact_paths = [str(safe_relative(path)) for path in job.get("artifact_paths", [])]
            resource_handlers = {name: [_expand(command, mapping) for command in
                                        ([argv] if isinstance(argv[0], str) else argv)]
                                 for name, argv in job.get("resource_handlers", {}).items()}
            preflight_error = None
        except ValueError as exc:
            command, result_path, artifact_paths, resource_handlers = [], None, [], {}
            preflight_error = str(exc)
        labels = merge_labels(job["labels"], (run_labels or {}).get(job["id"], {}))
        state = {"schema_version": 2, "record_type": "lab.run", "run_id": run_id,
                 "experiment_id": manifest["experiment_id"], "job_id": job["id"], "attempt": attempt,
                 "retry_of": source["run_id"] if source else None,
                 "trigger_operation": operation_id,
                 "controller": controller.id, "phase": "queued" if preflight_error is None else "finished",
                 "created_at": time.time(), "labels": labels,
                 **{key: labels.get(key) for key in ("competition", "variant", "task", "venue")},
                 "inputs": frozen, "command": command, "result_path": result_path,
                 "artifact_paths": artifact_paths, "adapter_kind": job.get("adapter_kind"),
                 "resource_handlers": resource_handlers}
        if job.get("docker"):
            state["docker"] = True
        if manifest.get("controller_runtime"):
            state["controller_runtime"] = manifest["controller_runtime"]
        if job.get("dependencies"):
            state["dependencies"] = job["dependencies"]
        if manifest.get("storage"):
            state["storage"] = manifest["storage"]
        if job.get("source_application"):
            state["source_application"] = job["source_application"]
        if preflight_error:
            state.update(error=preflight_error, result_contract="preflight-failed", finished_at=time.time())
        write_json(run / "run.json", state)
        if preflight_error is None:
            initialize(run / "telemetry.sqlite")
            requested.append((run, state))
        controller.emit("attempt-allocated", run_id=run_id, job_id=job["id"], phase=state["phase"])
    if source and not requested:
        raise ValueError("retry source job is not ready or no new attempt was allocated")
    return requested


def _environment(run, server, token):
    endpoint = f"http://127.0.0.1:{server.server_port}"
    headers = f"x-experiment-token={token}"
    env = dict(os.environ)
    env.update(OTEL_EXPORTER_OTLP_ENDPOINT=endpoint,
               OTEL_EXPORTER_OTLP_PROTOCOL="http/protobuf",
               OTEL_EXPORTER_OTLP_HEADERS=headers,
               OTEL_EXPORTER_OTLP_COMPRESSION="none",
               EXPERIMENT_RUN_ID=run.name, EXPERIMENT_RUN_DIR=str(run),
               EXPERIMENT_ARTIFACT_DIR=str(run / "artifacts"),
               EXPERIMENT_EVENT_DIR=str(run / "events"))
    for suffix, path in SIGNALS.items():
        prefix = f"OTEL_EXPORTER_OTLP_{path.upper()}"
        env[f"{prefix}_ENDPOINT"] = endpoint + suffix
        env[f"{prefix}_PROTOCOL"] = "http/protobuf"
        env[f"{prefix}_HEADERS"] = headers
        env[f"{prefix}_COMPRESSION"] = "none"
    state = read_status(run)
    env.update(EXPERIMENT_ID=state["experiment_id"], EXPERIMENT_ATTEMPT=str(state["attempt"]))
    if state.get("docker_endpoint"):
        for name in ("DOCKER_CONTEXT", "DOCKER_HOST", "DOCKER_TLS", "DOCKER_TLS_VERIFY", "DOCKER_CERT_PATH"):
            env.pop(name, None)
        env.update({key: value for key, value in docker_environment(state["docker_endpoint"]).items()
                    if key.startswith("DOCKER_")})
        env["EXPERIMENT_DOCKER_ENDPOINT"] = json.dumps(state["docker_endpoint"])
    return env


def _worker(run, server, events, stop_requested):
    process = None
    try:
        if stop_requested.is_set():
            events.put(("cancelled", run, None))
            return
        state = read_status(run)
        if state.get("docker"):
            state["docker_endpoint"] = freeze_docker()
            write_json(run / "run.json", {key: value for key, value in state.items() if key != "path"})
        token = secrets.token_urlsafe(24)
        session = new_session(run / "telemetry.sqlite")
        server.register(token, run / "telemetry.sqlite", session)
        env = _environment(run, server, token)
        with (run / "stdout.log").open("wb") as stdout, (run / "stderr.log").open("wb") as stderr:
            process = subprocess.Popen(state["command"], cwd=run / "workspace", env=env,
                                       stdout=stdout, stderr=stderr, start_new_session=True)
            events.put(("started", run, process))
            if stop_requested.is_set() and process.poll() is None:
                os.killpg(process.pid, signal.SIGTERM)
            exit_code = process.wait()
            events.put(("exited", run, exit_code))
    except BaseException as exc:
        events.put(("launch-error", run, f"{type(exc).__name__}: {exc}"))


def _artifact_index(run, paths):
    records = []
    root = run.resolve()
    for relative in paths:
        path = run / relative
        item = {"path": relative}
        try:
            resolved = path.resolve(strict=True)
            if not resolved.is_relative_to(root):
                raise ValueError("artifact is outside this run")
            item.update(status="available", location=str(path.relative_to(run)),
                        kind="directory" if path.is_dir() else "file")
        except FileNotFoundError:
            item["status"] = "missing"
        except (OSError, ValueError) as exc:
            item.update(status="error", error=f"{type(exc).__name__}: {exc}")
        records.append(item)
    for stage in ("official-generation", "official"):
        receipt = run / "workspace" / stage / ".lab-artifacts/receipt.json"
        if receipt.is_file():
            records.append({"path": str(receipt.relative_to(run)), "status": "published",
                            "kind": "application", "receipt": str(receipt.relative_to(run))})
    write_json(run / "artifacts/index.json", {"schema_version": 1, "artifacts": records})
    return records


def _collect(run, state):
    transport = run / "workspace/docker-workspace.json"
    if transport.is_file():
        try:
            state["workspace_transport"] = read_json(transport)
            state["resource_state"] = ("cleaned" if state["workspace_transport"].get("state") == "removed"
                                       else "unconfirmed")
        except (OSError, ValueError) as error:
            state.update(resource_state="unconfirmed", workspace_transport_error=f"{type(error).__name__}: {error}")
    path = run / state["result_path"] if state.get("result_path") else None
    if path is not None:
        try:
            if not path.is_file():
                raise FileNotFoundError(path)
            if not path.resolve().is_relative_to(run.resolve()):
                raise ValueError("result file points outside this run")
            result = read_json(path)
            if not isinstance(result, dict) or result.get("schema_version") != 1:
                raise ValueError("runner result must be a schema_version=1 object")
            state["result"] = result
            state["result_contract"] = "present"
        except (OSError, ValueError) as exc:
            state["result_contract"] = "invalid"
            state["result_error"] = f"{type(exc).__name__}: {exc}"
    try:
        state["artifacts"] = _artifact_index(run, state.get("artifact_paths", []))
    except (OSError, ValueError) as exc:
        state["artifact_error"] = f"{type(exc).__name__}: {exc}"
    try:
        database = database_for_run(run)
        batches = list_batches(database)
        state["telemetry"] = {"status": "received" if batches else "absent",
                              "database": str(database.relative_to(run.resolve())),
                              "batches": len(batches), "until_batch_id": batches[-1]["id"] if batches else None,
                              "signals": {name: sum(item["signal"] == name for item in batches)
                                          for name in SIGNALS.values()}}
    except (OSError, ValueError, sqlite3.Error) as exc:
        state["telemetry_error"] = f"{type(exc).__name__}: {exc}"
    write_json(run / "run.json", state)


def _signal_stop(event_queue):
    def handle(number, _frame):
        event_queue.put(("signal", number))
    signal.signal(signal.SIGINT, handle)
    signal.signal(signal.SIGTERM, handle)


def _run_storage_usage(root):
    by_inode = {}
    errors = []
    telemetry_paths = {root / name for name in
                       ("telemetry.sqlite", "telemetry.sqlite-wal", "telemetry.sqlite-shm")}
    for database in (root / "workspace").glob("*/template/.factory26/*/telemetry.sqlite"):
        telemetry_paths.update((database, database.with_name("telemetry.sqlite-wal"),
                                database.with_name("telemetry.sqlite-shm")))
    for directory, names, files in os.walk(root, followlinks=False, onerror=errors.append):
        names.sort(); files.sort()
        folder = Path(directory)
        paths = [folder/name for name in names + files]
        if folder == Path(root):
            paths.insert(0, folder)
        for path in paths:
            try:
                info = path.lstat()
            except FileNotFoundError:
                continue
            except OSError as exc:
                errors.append(exc)
                continue
            key = (info.st_dev, info.st_ino)
            prior = by_inode.get(key, {"bytes": 0, "telemetry": False})
            by_inode[key] = {"bytes": max(prior["bytes"], info.st_blocks * 512),
                             "telemetry": prior["telemetry"] or path in telemetry_paths}
    allocated = sum(item["bytes"] for item in by_inode.values())
    telemetry = sum(item["bytes"] for item in by_inode.values() if item["telemetry"])
    return {"allocated_bytes": allocated, "workspace_bytes": max(0, allocated - telemetry),
            "telemetry_bytes": telemetry, "inodes": len(by_inode),
            "scan_errors": [f"{type(error).__name__}: {error}" for error in errors]}


def _storage_observation(experiment, manifest, active):
    root = _run_root(experiment, manifest)
    policy = manifest["storage"]
    runs = {name: _run_storage_usage(path) for name, path in sorted(active.items())}
    stats = os.statvfs(root)
    reasons = []
    hard_runs = set()
    status = "ready"
    for run_id, usage in runs.items():
        for field, cap in (("workspace_bytes", policy["workspace_bytes_per_run"]),
                           ("telemetry_bytes", policy["telemetry_bytes_per_run"])):
            if usage[field] >= cap:
                status = "hard"
                hard_runs.add(run_id)
                reasons.append(f"{run_id} {field}={usage[field]} reached cap={cap}")
            elif usage[field] >= cap * 4 // 5 and status != "hard":
                status = "soft"
                reasons.append(f"{run_id} {field}={usage[field]} reached 80% of cap={cap}")
    scan_errors = [{"run_id": run_id, "errors": usage["scan_errors"]}
                   for run_id, usage in runs.items() if usage["scan_errors"]]
    if scan_errors and status == "ready":
        status = "unknown"
        reasons.append("one or more run directory scans were incomplete")
    available = stats.f_bavail * stats.f_frsize
    free_inodes = stats.f_favail
    inode_reserve = stats.f_files * policy["inode_reserve_percent"] // 100
    host_hard = available < policy["host_reserve_bytes"] or free_inodes < inode_reserve
    if host_hard:
        status = "hard"
        reasons.append(
            f"host reserve crossed: available={available}/{policy['host_reserve_bytes']} "
            f"free_inodes={free_inodes}/{inode_reserve}"
        )
    soft_floor = (policy["host_reserve_bytes"] +
                  max(1, len(active)) * policy["finalization_scratch_bytes_per_run"])
    if status in {"ready", "unknown"} and available < soft_floor:
        status = "soft"
        reasons.append(f"available={available} below finalization floor={soft_floor}")
    return {"schema_version": 1, "observed_at": time.time(), "status": status,
            "filesystem": str(root), "available_bytes": available,
            "free_inodes": free_inodes, "required_free_inodes": inode_reserve,
            "runs": runs, "hard_runs": sorted(hard_runs), "host_hard": host_hard,
            "scan_errors": scan_errors, "reasons": reasons}


def _measure_storage(experiment, manifest, active, events):
    try:
        observation = _storage_observation(experiment, manifest, active)
    except Exception as exc:
        observation = {"schema_version": 1, "observed_at": time.time(), "status": "unknown",
                       "filesystem": str(Path(experiment) / manifest["runs_root"]), "host_hard": False,
                       "hard_runs": [], "runs": {},
                       "scan_errors": [{"error": f"{type(exc).__name__}: {exc}"}],
                       "reasons": ["storage observation failed"]}
    events.put(("storage-observed", observation))


def _append_storage_observation(experiment, observation):
    path = Path(experiment) / "storage-observations.jsonl"
    with path.open("a") as stream:
        stream.write(json.dumps(observation, ensure_ascii=False) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def _storage_stop_record(observation):
    return {**observation, "writer_scope": "controller_process_group",
            "resource_state": "unconfirmed"}


def _diagnostic(message):
    try:
        os.write(2, (message + "\n").encode(errors="replace"))
    except OSError:
        pass


def _stop_active(active, sig=signal.SIGTERM, names=None):
    selected = active.values() if names is None else (
        active[name] for name in names if name in active)
    for current in selected:
        current["stop"].set()
        process = current["process"]
        if process is not None and process.poll() is None:
            try:
                os.killpg(process.pid, sig)
            except ProcessLookupError:
                pass


def _request_stop(active, targets, kill_targets, kill_escalated, deadline, stop_grace):
    targets = set(targets)
    kill_targets.update(targets)
    if kill_escalated:
        _stop_active(active, signal.SIGKILL, names=targets)
    else:
        _stop_active(active, names=targets)
        if targets and deadline is None:
            deadline = time.monotonic() + stop_grace
    return deadline


def controller(experiment, *, retry_of=None, listen_host="127.0.0.1", stop_grace=30, run_labels=None):
    experiment = Path(experiment).resolve(strict=True)
    manifest = read_json(experiment / "manifest.json")
    if manifest.get("record_type") != "lab.experiment":
        raise ValueError("controller needs a frozen experiment")
    run_labels = execution_labels(manifest, run_labels)
    with exclusive(experiment), receiver(listen_host) as server:
        preflight = _storage_preflight(experiment, manifest, manifest["max_parallel"],
                                       retry=retry_of is not None)
        control = Control(experiment)
        _signal_stop(control.commands)
        pending = deque()
        active = {}
        slots = manifest["max_parallel"]
        stopping = False
        stopping_reason = None
        dispatch_paused = False
        storage_stop = None
        budget_stops = {}
        kill_targets = set()
        kill_escalated = False
        controller_started = time.monotonic()
        next_storage_check = controller_started + 180 if manifest.get("storage") else None
        storage_scan_running = False
        deadline = None
        try:
            operation_id = secrets.token_hex(12)
            operation_dir = control.root / "operations"
            write_json(operation_dir / f"{operation_id}.request.json", {
                "id": operation_id, "action": "retry" if retry_of else "run",
                "retry_of": str(retry_of) if retry_of else None, "created_at": time.time(),
                "run_labels": run_labels, "storage_preflight": preflight["id"]})
            pending = deque(_allocate(experiment, manifest, control, retry_of, operation_id, run_labels))
            write_json(operation_dir / f"{operation_id}.result.json", {
                "id": operation_id, "action": "retry" if retry_of else "run",
                "allocated": [run.name for run, _ in pending]})
            control.emit("operation", operation_id=operation_id,
                         action="retry" if retry_of else "run", allocated=len(pending))
            while pending or active:
                now = time.monotonic()
                item = ("stop-deadline",) if deadline is not None and now >= deadline else None
                if (item is None and next_storage_check is not None and
                        now >= next_storage_check and not storage_scan_running):
                    snapshot = {name: current["run"] for name, current in active.items()}
                    Thread(target=_measure_storage,
                           args=(experiment, manifest, snapshot, control.commands), daemon=True).start()
                    storage_scan_running = True
                    next_storage_check = None
                if item is None:
                    while (pending and not stopping and not dispatch_paused and
                           not storage_scan_running and len(active) < slots):
                        run, state = pending.popleft()
                        requested = Event()
                        thread = Thread(target=_worker, args=(run, server, control.commands, requested), daemon=True)
                        active[run.name] = {"run": run, "thread": thread, "stop": requested,
                                            "process": None}
                        thread.start()
                    now = time.monotonic()
                    timeouts = ([max(0, deadline - now)] if deadline is not None else [])
                    if next_storage_check is not None:
                        timeouts.append(max(0, next_storage_check - now))
                    timeout = min(timeouts) if timeouts else None
                    try:
                        item = control.commands.get(timeout=timeout)
                    except Empty:
                        continue
                if len(item) == 2 and isinstance(item[0], dict):
                    request, reply = item
                    identifier = request.get("id")
                    operation_dir = control.root / "operations"
                    outcome = operation_dir / f"{identifier}.result.json"
                    if not identifier or not re.fullmatch(r"[0-9a-f]{24}", identifier):
                        reply.put({"error": "invalid operation ID"})
                        continue
                    if outcome.is_file():
                        reply.put(read_json(outcome))
                        continue
                    saved = read_json(operation_dir / f"{identifier}.request.json")
                    action = saved.get("action")
                    if action == "parallel" and type(saved.get("slots")) is int and saved["slots"] > 0:
                        try:
                            checked = _storage_preflight(experiment, manifest, saved["slots"])
                            slots = saved["slots"]
                            response = {"id": identifier, "action": action, "slots": slots,
                                        "storage_preflight": checked["id"]}
                        except (OSError, ValueError) as exc:
                            response = {"id": identifier, "action": action,
                                        "error": f"{type(exc).__name__}: {exc}"}
                    elif action == "stop":
                        stopping = True
                        stopping_reason = "requested"
                        deadline = _request_stop(active, active, kill_targets, kill_escalated,
                                                 deadline, stop_grace)
                        response = {"id": identifier, "action": action, "status": "requested"}
                    else:
                        response = {"id": identifier, "error": f"unknown action: {action}"}
                    try:
                        write_json(outcome, response)
                        control.emit("operation", operation_id=identifier, action=action)
                    except OSError as exc:
                        detail = f"{type(exc).__name__}: {exc}"
                        response = {**response,
                                    "error": f"operation enacted but receipt persistence failed: {detail}"}
                        _diagnostic(f"operation receipt persistence failed: {detail}")
                    reply.put(response)
                elif item[0] == "signal":
                    stopping = True
                    stopping_reason = f"signal:{item[1]}"
                    deadline = _request_stop(active, active, kill_targets, kill_escalated,
                                             deadline, stop_grace)
                elif item[0] == "started":
                    _, run, process = item
                    current = active[run.name]
                    current["process"] = process
                    if run.name in kill_targets:
                        _stop_active(active, signal.SIGKILL if kill_escalated else signal.SIGTERM,
                                     names={run.name})
                    state = read_status(run)
                    state.update(phase="running", started_at=time.time(),
                                 **process_identity(process.pid), pgid=process.pid)
                    try:
                        write_json(run / "run.json", {k: v for k, v in state.items() if k != "path"})
                        control.emit("attempt-started", run_id=run.name, pid=process.pid)
                    except OSError as exc:
                        _diagnostic(f"attempt start persistence failed: {type(exc).__name__}: {exc}")
                elif item[0] in ("exited", "launch-error", "cancelled"):
                    kind, run, value = item
                    current = active.pop(run.name)
                    current["thread"].join()
                    state = read_status(run)
                    budget_stop = budget_stops.pop(run.name, None)
                    state.update(phase="cancelled" if stopping or kind == "cancelled" or budget_stop
                                 else "finished",
                                 finished_at=time.time())
                    if budget_stop is not None:
                        state["cancellation"] = "storage_budget_exceeded"
                        state["storage_budget"] = _storage_stop_record(budget_stop)
                    elif stopping:
                        state["cancellation"] = stopping_reason or "controller-stop"
                    if storage_stop is not None and budget_stop is None:
                        state["storage_budget"] = _storage_stop_record(storage_stop)
                    if kind == "exited":
                        state["runner_exit_code"] = value
                    else:
                        state["error"] = value
                    try:
                        _collect(run, {k: v for k, v in state.items() if k != "path"})
                        control.emit("attempt-exited", run_id=run.name, phase=state["phase"],
                                     exit_code=state.get("runner_exit_code"))
                    except OSError as exc:
                        _diagnostic(f"attempt exit persistence failed: {type(exc).__name__}: {exc}")
                    if dispatch_paused and next_storage_check is not None:
                        next_storage_check = min(next_storage_check, time.monotonic())
                    kill_targets.discard(run.name)
                    if not kill_targets and not stopping:
                        deadline = None
                        kill_escalated = False
                elif item[0] == "storage-observed":
                    observation = item[1]
                    storage_scan_running = False
                    stale_runs = set(observation["runs"]) - set(active)
                    previous = dispatch_paused
                    dispatch_paused = observation["status"] in {"soft", "hard", "unknown"}
                    if observation["status"] == "hard":
                        if observation["host_hard"]:
                            storage_stop = observation
                            stopping = True
                            stopping_reason = "storage_budget_exceeded"
                            deadline = _request_stop(active, active, kill_targets, kill_escalated,
                                                     deadline, stop_grace)
                        else:
                            targets = set(observation["hard_runs"]) & set(active)
                            budget_stops.update((name, observation) for name in targets)
                            deadline = _request_stop(active, targets, kill_targets, kill_escalated,
                                                     deadline, stop_grace)
                    interval = 180 if time.monotonic() - controller_started < 600 else 480
                    next_storage_check = time.monotonic() + (0 if stale_runs else interval)
                    try:
                        _append_storage_observation(experiment, observation)
                    except OSError as exc:
                        _diagnostic(f"storage observation persistence failed: "
                                    f"{type(exc).__name__}: {exc}")
                    try:
                        if observation["status"] == "hard":
                            control.emit("storage-budget-hard", reasons=observation["reasons"])
                        elif dispatch_paused != previous:
                            control.emit("storage-dispatch-paused" if dispatch_paused else
                                         "storage-dispatch-resumed", reasons=observation["reasons"])
                    except OSError as exc:
                        _diagnostic(f"storage notification persistence failed: "
                                    f"{type(exc).__name__}: {exc}")
                elif item[0] == "stop-deadline":
                    _stop_active(active, signal.SIGKILL, kill_targets)
                    kill_escalated = True
                    deadline = None
                if stopping:
                    while pending:
                        run, state = pending.popleft()
                        state.update(phase="cancelled", finished_at=time.time(),
                                     cancellation=stopping_reason or "before-start")
                        if storage_stop is not None:
                            state["storage_budget"] = _storage_stop_record(storage_stop)
                        try:
                            write_json(run / "run.json", state)
                            control.emit("attempt-cancelled", run_id=run.name)
                        except OSError as exc:
                            _diagnostic(f"attempt cancellation persistence failed: "
                                        f"{type(exc).__name__}: {exc}")
        finally:
            for current in active.values():
                current["stop"].set()
                process = current["process"]
                if process is not None and process.poll() is None:
                    try:
                        os.killpg(process.pid, signal.SIGTERM)
                    except ProcessLookupError:
                        pass
                run = current["run"]
                try:
                    state = read_status(run)
                    state.update(phase="lost", ownership_observed_at=time.time(),
                                 controller_error="controller ended before the attempt exit was recorded")
                    if run.name in budget_stops:
                        state["cancellation"] = "storage_budget_exceeded"
                        state["storage_budget"] = _storage_stop_record(budget_stops[run.name])
                    elif storage_stop is not None:
                        state["cancellation"] = "storage_budget_exceeded"
                        state["storage_budget"] = _storage_stop_record(storage_stop)
                    write_json(run / "run.json", {k: v for k, v in state.items() if k != "path"})
                except OSError:
                    pass
            for run, state in pending:
                state.update(phase="cancelled", finished_at=time.time(),
                             cancellation="controller-ended-before-start")
                try:
                    write_json(run / "run.json", state)
                except OSError:
                    pass
            control.finish()
    return [read_status(path) for path in _run_root(experiment, manifest).iterdir()
            if path.is_dir() and (path / "run.json").is_file()]


def _frozen_command(experiment, *, retry_of=None, listen_host="127.0.0.1", run_labels=None):
    experiment = Path(experiment).resolve(strict=True)
    source = experiment / "controller-source"
    manifest = read_json(experiment / "manifest.json")
    runtime = manifest.get("controller_runtime", {})
    python = frozen_host_runtime(runtime)["launcher"] if manifest.get("schema_version") == 3 else sys.executable
    env = dict(os.environ)
    env["PYTHONPATH"] = str(source) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    command = [python, "-m", "lab", "_controller", str(experiment), "--listen-host", listen_host]
    if retry_of:
        command += ["--retry-of", str(Path(retry_of).resolve(strict=True))]
    if run_labels is not None:
        execution_labels(manifest, run_labels)
        # Pass the consumed contents, not a mutable file read later by a background controller.
        command += ["--run-labels-json", json.dumps(run_labels, ensure_ascii=False)]
    return command, env


def start(experiment, *, retry_of=None, listen_host="127.0.0.1", background=False, run_labels=None):
    command, env = _frozen_command(experiment, retry_of=retry_of, listen_host=listen_host, run_labels=run_labels)
    if background:
        experiment = Path(experiment)
        with (experiment / "controller.stdout.log").open("ab") as out, (
                experiment / "controller.stderr.log").open("ab") as err:
            process = subprocess.Popen(command, cwd=experiment, env=env, stdout=out, stderr=err,
                                       start_new_session=True)
        return {"experiment": str(experiment), "controller_pid": process.pid}
    return subprocess.call(command, cwd=experiment, env=env)


def run_manifest(manifest_path, runs_root, max_parallel=None, listen_host="127.0.0.1"):
    manifest_path = Path(manifest_path).resolve(strict=True)
    experiment = create(manifest_path, runs_root=runs_root, max_parallel=max_parallel)
    exit_code = start(experiment, listen_host=listen_host)
    result = [read_status(path) for path in _run_root(experiment, read_json(experiment / "manifest.json")).iterdir()
              if path.is_dir() and (path / "run.json").is_file()]
    if exit_code != 0:
        raise RuntimeError(f"controller exited with status {exit_code}; experiment: {experiment}")
    return result


def main():
    from .__main__ import main as lab_main
    return lab_main()


if __name__ == "__main__":
    sys.exit(main())
