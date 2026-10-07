"""Run-scoped Playground execution with durable, never-retried POSTs.

Assembly supplies agent_package, task_config.platform_task and target_config
(cookie_file, competition_id, model_config, credential_file). Platform identity
and responses stay in records/platform; no legacy attempt or admission object
enters this path.
"""
from contextlib import contextmanager
import fcntl
import json
from pathlib import Path, PurePosixPath
import shutil
import stat
import time
from urllib.parse import urlencode
from zipfile import ZipFile

from .playground import ApiError, Client, redact, run_path, TERMINAL
from .run_layout import manifest, write_json


@contextmanager
def _state(run):
    directory = Path(run) / "records/platform"
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / "write.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        path = directory / "execution.json"
        value = json.loads(path.read_text()) if path.exists() else {"pending": None}
        try:
            yield directory, value
        finally:
            write_json(path, value)


def _context(run):
    run = Path(run)
    value = manifest(run)
    target = value["target_config"]
    return run, value, target, Client(target["cookie_file"])


def _error(exc):
    return {"type": type(exc).__name__, "message": str(exc),
            "http_status": getattr(exc, "status", None), "detail": redact(getattr(exc, "detail", None))}


def _post(directory, state, client, action, endpoint, **kwargs):
    """Persist intent before network I/O, then response before interpreting it."""
    if state.get("pending"):
        raise RuntimeError("platform write outcome unknown; query saved identity, do not resend")
    state.pop("rejected", None)
    request_id = f"{action}-{time.time_ns()}"
    state["pending"] = {"action": action, "endpoint": endpoint, "requested_at": time.time(),
                        "request_id": request_id}
    if kwargs.get("fields"):
        state["pending"]["fields"] = redact(kwargs["fields"])
    write_json(directory / "execution.json", state)
    try:
        response = client.request(endpoint, "POST", **kwargs)
    except Exception as exc:
        failure = _error(exc)
        if kwargs.get("secret"):
            failure = json.loads(json.dumps(failure).replace(kwargs["secret"], "[redacted]"))
        state["pending"]["error"] = failure
        # A rejected HTTP request differs from loss of its response. Neither
        # condition permits this adapter to repeat the POST.
        if isinstance(exc, ApiError) and 400 <= exc.status < 500 and exc.status != 408:
            state["rejected"] = state["pending"]
            state["pending"] = None
        write_json(directory / f"{request_id}.json", state)
        write_json(directory / "execution.json", state)
        return None
    write_json(directory / f"{request_id}.json", {"request": state["pending"], "response": redact(response)})
    state["pending"]["response"] = redact(response)
    write_json(directory / "execution.json", state)
    return response


def start(run):
    run, value, target, client = _context(run)
    task = value["task_config"]["platform_task"]
    model = target["model_config"]
    package = Path(value["agent_package"]).resolve(strict=True)
    mode = value.get("billing_mode") or ("official_evaluation" if value.get("competition") else "self_funded")
    if mode == "competition":
        mode = "official_evaluation"
    if mode not in {"self_funded", "official_evaluation"}:
        raise ValueError(f"unsupported Hosted billing mode: {mode}")
    secret = None
    if mode == "self_funded":
        from scripts.hackathon_gateway import read_assignments
        environment = read_assignments(target["credential_file"])
        secret = (environment.get(target['credential_env']) if target.get('credential_env') else
                  environment.get("FACTORY26_API_KEY") or environment.get("OPENAI_API_KEY"))
        if not secret:
            raise ValueError("credential_file lacks the selected model key")
    with _state(run) as (directory, state):
        if state.get("pending") or state.get("rejected"):
            return {"lifecycle": "unknown" if state.get("pending") else "failed",
                    "error": (state.get("pending") or state.get("rejected")).get("error")}
        state.update(display_name=f"lab-{run.name}", task=task, billing_mode=mode)
        if not state.get("submission_id"):
            fields = {"competition_id": target["competition_id"], "runtime": "python",
                      "catalog": "competition", "agent_source": "upload", "credential_mode": mode,
                      "display_name": state["display_name"],
                      **{key: model[key] for key in ("model", "visual_model", "base_url")}}
            response = _post(directory, state, client, "upload", "/submissions", fields=fields,
                             package=package, secret=secret)
            identity = response.get("submission", {}).get("id") if isinstance(response, dict) else None
            if identity:
                state["submission_id"] = identity
                state["pending"] = None
        if state.get("submission_id") and not state.get("pending") and not state.get("rejected") and not state.get("run_id"):
            response = _post(directory, state, client, "create", "/runs",
                             fields={"submission_id": state["submission_id"], "requirement_id": task})
            identity = response.get("run", {}).get("id") if isinstance(response, dict) else None
            if identity:
                state["run_id"] = identity
                state["pending"] = None
        if state.get("run_id") and not state.get("pending") and not state.get("rejected") and not state.get("started"):
            # The platform can report self_funded on start after creating an
            # official_evaluation run. Preserve the receipt; do not use that
            # known label defect to reject start or overwrite the selected mode.
            response = _post(directory, state, client, "start", run_path(state["run_id"]) + "/start")
            if not state.get("pending") and not state.get("rejected"):
                state["started"] = True
            elif "response" in (state.get("pending") or {}):
                state["started"] = True
                state["pending"] = None
        return {"lifecycle": "failed" if state.get("rejected") else "unknown" if state.get("pending") else "starting",
                "platform_run_id": state.get("run_id"), "submission_id": state.get("submission_id"),
                "error": (state.get("rejected") or state.get("pending") or {}).get("error")}


def _get(directory, client, endpoint, name):
    value = client.request(endpoint)
    write_json(directory / name, {"endpoint": endpoint, "as_of": time.time(), "response": redact(value)})
    return value


def observe(run):
    run, value, target, client = _context(run)
    with _state(run) as (directory, state):
        pending = state.get("pending")
        if pending and pending["action"] in {"upload", "create"}:
            history = _get(directory, client, "/competitions/" + target["competition_id"] + "/submissions", "history.json")
            if pending["action"] == "upload":
                matches = [row for row in history if row.get("display_name") == state["display_name"]]
                if len(matches) == 1:
                    state["submission_id"] = matches[0]["id"]
            else:
                matches = {score["run_id"] for row in history if row.get("id") == state.get("submission_id")
                           for score in row.get("task_scores", [])
                           if score.get("task_id") == state["task"] and score.get("run_id")}
                if len(matches) == 1:
                    state["run_id"] = matches.pop()
            # Query confirmation never authorizes a new downstream POST.
        if not state.get("run_id"):
            return {"lifecycle": "failed" if state.get("rejected") else "unknown", "activity": "unknown",
                    "as_of": time.time(), "platform": state}
        remote = _get(directory, client, run_path(state["run_id"]), "status.json")
        if remote.get("id") != state["run_id"] or remote.get("submission_id") != state["submission_id"] or remote.get("requirement_id") != state["task"]:
            raise ValueError("Hosted status identity differs from this run's saved submission/task")
        phase = remote.get("status")
        if pending and pending["action"] in {"start", "stop"}:
            confirmed = phase in TERMINAL if pending["action"] == "stop" else bool(remote.get("started_at"))
            if confirmed:
                state["pending"] = None
        steps = {step.get("key"): step.get("status") for step in remote.get("steps", [])}
        lifecycle = "stopped" if phase == "CANCELLED" else "completed" if phase == "PASSED" else (
            "completed" if phase == "FAILED" and steps.get("start_agent") == "completed" else
            "failed" if phase == "FAILED" else "running" if phase in {"RUNNING", "STARTING", "QUEUED"} else "unknown")
        cursor_file = directory / "log-cursor.json"
        cursor = json.loads(cursor_file.read_text()) if cursor_file.exists() else {"log_offset": 0}
        log_error = None
        try:
            chunk = _get(directory, client, run_path(state["run_id"]) + "/logs?" + urlencode(cursor), f"logs-{cursor.get('log_offset', 0)}.json")
            write_json(cursor_file, {"log_offset": chunk.get("log_offset", cursor.get("log_offset", 0)),
                                   **({"after_event_id": chunk["last_event_id"]} if chunk.get("last_event_id") else {})})
        except Exception as exc:
            log_error = _error(exc)
            write_json(directory / "logs-error.json", {"as_of": time.time(), **log_error})
        if remote.get("token_cost_usd") is not None:
            write_json(run / "records/cost.json", {"kind": "actual", "amount": remote["token_cost_usd"],
                       "currency": remote.get("token_cost_currency"), "source": run_path(state["run_id"]),
                       "as_of": time.time(), "scope": "platform-run"})
        return {"lifecycle": lifecycle, "activity": "unknown", "as_of": time.time(),
                "platform_run_id": state["run_id"], "platform_status": phase,
                "logs_error": log_error,
                "brief": remote.get("failure_reason") or phase, "spend": {"kind": "actual" if remote.get("token_cost_usd") is not None else "unknown",
                "amount": remote.get("token_cost_usd"), "currency": remote.get("token_cost_currency"),
                "source": run_path(state["run_id"]), "as_of": time.time()}}


def control(run, action):
    if action != "stop":
        raise ValueError("Hosted does not support pause/resume")
    run, value, target, client = _context(run)
    with _state(run) as (directory, state):
        if not state.get("run_id"):
            raise RuntimeError("Hosted run identity unknown; cannot target cancel")
        if state.get("pending"):
            raise RuntimeError("Hosted write outcome unknown; observe before another control")
        _post(directory, state, client, "stop", run_path(state["run_id"]) + "/cancel")
        if state.get("rejected"):
            failure = state["rejected"]["error"]
            raise ApiError(failure["http_status"], failure["detail"])
        if (state.get("pending") or {}).get("response") is not None:
            state["pending"] = None
    return observe(run)


def _extract(archive, destination):
    """Preserve links, but never write an archive member through one."""
    with ZipFile(archive) as stream:
        entries = {str(PurePosixPath(item.filename)): item for item in stream.infolist()}
        if len(entries) != len(stream.infolist()):
            raise ValueError("duplicate workspace ZIP members")
        for name, item in entries.items():
            relative = PurePosixPath(item.filename)
            if name == "." or relative.is_absolute() or ".." in relative.parts or "\\" in item.filename:
                raise ValueError(f"unsafe workspace ZIP path: {name}")
            for parent in relative.parents:
                ancestor = entries.get(str(parent))
                if ancestor and stat.S_ISLNK(ancestor.external_attr >> 16):
                    raise ValueError(f"workspace ZIP writes through link: {name}")
        for links in (False, True):
            for name, item in entries.items():
                mode = item.external_attr >> 16
                if stat.S_ISLNK(mode) != links:
                    continue
                path = destination / name
                if item.is_dir():
                    path.mkdir(parents=True, exist_ok=True)
                    continue
                path.parent.mkdir(parents=True, exist_ok=True)
                if links:
                    path.symlink_to(stream.read(item).decode())
                else:
                    with stream.open(item) as source, path.open("wb") as output:
                        shutil.copyfileobj(source, output)
                    if mode & 0o111:
                        path.chmod(path.stat().st_mode | 0o111)


def save(run):
    run, value, target, client = _context(run)
    directory = run / "records/platform"
    state = json.loads((directory / "execution.json").read_text())
    if not state.get("run_id"):
        if state.get("rejected") and not state.get("pending"):
            # A definitive pre-execution rejection has no remote workspace.
            # Its frozen inputs and original platform response are the result.
            result = {"saved": True, "as_of": time.time(),
                      "kind": "pre-execution-rejection",
                      "scope": ["program", "inputs", "records"],
                      "platform_run_id": None,
                      "gaps": ["No platform run was created; no remote workspace exists"]}
            write_json(directory / "saved-inputs.json", result)
            return result
        raise RuntimeError("Hosted identity unknown; no downloadable result yet")
    remote = _get(directory, client, run_path(state["run_id"]), "save-status.json")
    if remote.get("id") != state["run_id"] or remote.get("status") not in TERMINAL:
        raise RuntimeError("Hosted result save requires this execution's confirmed terminal status")
    receipt = directory / "saved-workspace.json"
    if receipt.exists():
        return json.loads(receipt.read_text())
    stamp = str(time.time_ns())
    snapshot = run / "snapshots" / ("platform-" + stamp)
    snapshot.mkdir()
    archive = client.download(run_path(state["run_id"]) + "/workspace/template-bundle", snapshot / "workspace.zip")
    _extract(archive, snapshot / "workspace")
    # Keep the complete platform export, not only an application manifest.
    # Assembly places data/harness inside the exported workspace; the caller
    # maps that exact data root, rather than guessing from historical layouts.
    result = {"saved": True, "as_of": time.time(), "scope": "platform-template-bundle",
              "snapshot": str(snapshot), "workspace": str(snapshot / "workspace"),
              "platform_run_id": state["run_id"], "gaps": ["platform export may omit runner-private files"]}
    write_json(receipt, result)
    return result
