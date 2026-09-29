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

from .control import Control, exclusive, process_start
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


def _allocate(experiment, manifest, controller, retry_of=None, operation_id=None, run_labels=None):
    runs = _run_root(experiment, manifest)
    requested = []
    source = read_status(retry_of) if retry_of else None
    if source and source.get("experiment_id") != manifest["experiment_id"]:
        raise ValueError("retry run belongs to a different experiment")
    if source and source.get("pid") and source.get("process_start") == process_start(source["pid"]):
        raise ValueError("source attempt process is still alive; inspect or stop it before retry")
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
    return env


def _worker(run, server, events, stop_requested):
    process = None
    try:
        if stop_requested.is_set():
            events.put(("cancelled", run, None))
            return
        state = read_status(run)
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


def controller(experiment, *, retry_of=None, listen_host="127.0.0.1", stop_grace=30, run_labels=None):
    experiment = Path(experiment).resolve(strict=True)
    manifest = read_json(experiment / "manifest.json")
    if manifest.get("record_type") != "lab.experiment":
        raise ValueError("controller needs a frozen experiment")
    run_labels = execution_labels(manifest, run_labels)
    with exclusive(experiment), receiver(listen_host) as server:
        control = Control(experiment)
        _signal_stop(control.commands)
        pending = deque()
        active = {}
        slots = manifest["max_parallel"]
        stopping = False
        deadline = None
        try:
            operation_id = secrets.token_hex(12)
            operation_dir = control.root / "operations"
            write_json(operation_dir / f"{operation_id}.request.json", {
                "id": operation_id, "action": "retry" if retry_of else "run",
                "retry_of": str(retry_of) if retry_of else None, "created_at": time.time(),
                "run_labels": run_labels})
            pending = deque(_allocate(experiment, manifest, control, retry_of, operation_id, run_labels))
            write_json(operation_dir / f"{operation_id}.result.json", {
                "id": operation_id, "action": "retry" if retry_of else "run",
                "allocated": [run.name for run, _ in pending]})
            control.emit("operation", operation_id=operation_id,
                         action="retry" if retry_of else "run", allocated=len(pending))
            while pending or active:
                while pending and not stopping and len(active) < slots:
                    run, state = pending.popleft()
                    requested = Event()
                    thread = Thread(target=_worker, args=(run, server, control.commands, requested), daemon=True)
                    active[run.name] = {"run": run, "thread": thread, "stop": requested, "process": None}
                    thread.start()
                timeout = max(0, deadline - time.monotonic()) if deadline is not None else None
                try:
                    item = control.commands.get(timeout=timeout)
                except Empty:
                    item = ("stop-deadline",)
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
                        slots = saved["slots"]
                        response = {"id": identifier, "action": action, "slots": slots}
                    elif action == "stop":
                        stopping = True
                        deadline = time.monotonic() + stop_grace
                        for item_active in active.values():
                            item_active["stop"].set()
                            process = item_active["process"]
                            if process is not None and process.poll() is None:
                                try:
                                    os.killpg(process.pid, signal.SIGTERM)
                                except ProcessLookupError:
                                    pass
                        response = {"id": identifier, "action": action, "status": "requested"}
                    else:
                        response = {"id": identifier, "error": f"unknown action: {action}"}
                    write_json(outcome, response)
                    control.emit("operation", operation_id=identifier, action=action)
                    reply.put(response)
                elif item[0] == "signal":
                    stopping = True
                    deadline = time.monotonic() + stop_grace
                    for current in active.values():
                        current["stop"].set()
                        process = current["process"]
                        if process is not None and process.poll() is None:
                            try:
                                os.killpg(process.pid, signal.SIGTERM)
                            except ProcessLookupError:
                                pass
                elif item[0] == "started":
                    _, run, process = item
                    current = active[run.name]
                    current["process"] = process
                    state = read_status(run)
                    state.update(phase="running", started_at=time.time(), pid=process.pid,
                                 process_start=process_start(process.pid), pgid=process.pid)
                    write_json(run / "run.json", {k: v for k, v in state.items() if k != "path"})
                    control.emit("attempt-started", run_id=run.name, pid=process.pid)
                elif item[0] in ("exited", "launch-error", "cancelled"):
                    kind, run, value = item
                    current = active.pop(run.name)
                    current["thread"].join()
                    state = read_status(run)
                    state.update(phase="cancelled" if stopping or kind == "cancelled" else "finished",
                                 finished_at=time.time())
                    if kind == "exited":
                        state["runner_exit_code"] = value
                    else:
                        state["error"] = value
                    _collect(run, {k: v for k, v in state.items() if k != "path"})
                    control.emit("attempt-exited", run_id=run.name, phase=state["phase"],
                                 exit_code=state.get("runner_exit_code"))
                elif item[0] == "stop-deadline":
                    for current in active.values():
                        process = current["process"]
                        if process is not None and process.poll() is None:
                            try:
                                os.killpg(process.pid, signal.SIGKILL)
                            except ProcessLookupError:
                                pass
                    deadline = None
                if stopping:
                    while pending:
                        run, state = pending.popleft()
                        state.update(phase="cancelled", finished_at=time.time(), cancellation="before-start")
                        write_json(run / "run.json", state)
                        control.emit("attempt-cancelled", run_id=run.name)
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
    env = dict(os.environ)
    env["PYTHONPATH"] = str(source) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    command = [sys.executable, "-m", "lab", "_controller", str(experiment), "--listen-host", listen_host]
    if retry_of:
        command += ["--retry-of", str(Path(retry_of).resolve(strict=True))]
    if run_labels is not None:
        execution_labels(read_json(experiment / "manifest.json"), run_labels)
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
