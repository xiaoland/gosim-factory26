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

from .playground import API, ApiError, Client, redact, run_path, TERMINAL
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
    detail = getattr(exc, "detail", None)
    if isinstance(detail, dict) and detail.get("response_path"):
        response_path = Path(detail["response_path"])
        try:
            raw = response_path.read_bytes()
            clipped = raw[:16 * 1024]
            try:
                body = redact(json.loads(clipped))
            except (ValueError, UnicodeDecodeError):
                body = clipped.decode(errors="replace")
            detail = {**detail, "response_bytes": len(raw),
                      "response_truncated": len(raw) > len(clipped),
                      "response_body": body}
        except OSError as read_error:
            detail = {**detail, "response_read_error": f"{type(read_error).__name__}: {read_error}"}
    return {"type": type(exc).__name__, "message": str(exc),
            "http_status": getattr(exc, "status", None), "detail": redact(detail)}


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
    package = Path(value["agent_package"]).resolve(strict=True)
    mode = value.get("billing_mode") or ("official_evaluation" if value.get("competition") else "self_funded")
    if mode == "competition":
        mode = "official_evaluation"
    if mode not in {"self_funded", "official_evaluation"}:
        raise ValueError(f"unsupported Hosted billing mode: {mode}")
    # Keep the observed upload form shape; competition model intent comes
    # from the variant, never from a self-funded supplier deployment.
    model = ({**target['submission_models'], 'base_url': 'https://api.arc-bench.com/v1'}
             if mode == 'official_evaluation' else target['model_config'])
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


_LIVE_WORKSPACE_NAMES = {
    "lab-run.json", "run.json", "delivery.json", "audit-status.json",
    "audit-report.json", "model-gateway.json", "resource-latest.json",
    "resource-status.json", "resource-observation.json", "resources-baseline.jsonl", "request-metadata.jsonl",
    "gateway.log", "status.json", "recovery-attempt.json",
}


def _workspace_member_name(name):
    """Return a safe, repository-relative member name or None."""
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts or "\\" in name:
        return None
    parts = path.parts
    if parts and parts[0] == "template":
        parts = parts[1:]
    if ".factory26" not in parts:
        return None
    return "/".join(parts)


def _live_member(path):
    """Select bounded run facts, never application/runtime files."""
    name = path.name
    if name in _LIVE_WORKSPACE_NAMES:
        return True
    # Native session files are copied only into a temporary selected-facts tree;
    # the complete platform environment is never extracted or retained here.
    return name in {"session.jsonl", "pi-timing.jsonl"}


def _fact_path(relative):
    """Normalize modern and frozen legacy native members for existing readers."""
    parts = PurePosixPath(relative).parts
    factory = parts.index(".factory26")
    rest = parts[factory + 1:]
    if len(rest) >= 2 and rest[:2] == ("data", "harness"):
        return PurePosixPath(*rest)
    if not rest:
        raise ValueError("native member has no scope")
    return PurePosixPath("data", "harness", rest[0], *rest[1:])


def _read_existing_facts(live_root, jsonl_members, *, created_at=None):
    """Run the existing native/provider readers on selected files only."""
    from scripts.native_observation import observe as observe_native
    from .provider_usage import collect as collect_provider

    scopes = set()
    gateway = []
    for member in jsonl_members:
        path = Path(member)
        parts = path.parts
        try:
            index = parts.index("data")
            if parts[index + 1] != "harness":
                continue
            scope = parts[index + 2]
            scopes.add(scope)
            if path.name == "gateway.log":
                producer_index = parts.index("producers")
                gateway.append((scope, parts[producer_index + 1]))
        except (ValueError, IndexError):
            continue

    native = []
    for scope in sorted(scopes):
        try:
            write_json(live_root / "manifest.json", {"native_scope_id": scope,
                       "created_at": created_at or 0})
            value = observe_native(live_root, provider="pi-braid", braid=True)
            native.append(value)
        except Exception as exc:
            native.append({"scope": scope, "error": {"type": type(exc).__name__, "message": str(exc)}})

    attempts = []
    errors = []
    for scope, producer_run_id in gateway:
        try:
            value = collect_provider(live_root, {"native_scope_id": scope, "run_id": producer_run_id})
            if value:
                attempts.extend(value.get("attempts", []))
                errors.extend(value.get("reader_errors", []))
        except Exception as exc:
            errors.append({"source": f"{scope}/producers/{producer_run_id}/gateway.log",
                           "error": f"{type(exc).__name__}: {exc}"})
    merged = {"sessions": [], "session_messages": [], "provider_turns": [], "reader_errors": [],
              "usage": None, "braid": {"states": [], "sources": [], "gaps": []}}
    for value in native:
        if "error" in value:
            merged["reader_errors"].append(value["error"])
            continue
        for key in ("sessions", "session_messages", "provider_turns", "reader_errors"):
            merged[key].extend(value.get(key, []))
        if value.get("usage") is not None:
            merged["usage"] = value["usage"]
        braid = value.get("braid") or {}
        merged["braid"]["states"].extend(braid.get("states", []))
        merged["braid"]["sources"].extend(braid.get("sources", []))
        merged["braid"]["gaps"].extend(braid.get("gaps", []))
    return {"native": merged, "provider_usage": {
        "scope": "current-run-provider-attempts", "status": "partial" if attempts else "unknown",
        "attempts": attempts, "reader_errors": errors,
        "aggregation": "replace-by-source-not-sum-observations",
        "note": "Existing provider reader output; usage is not a bill."}}


def _append_observation(path, value):
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n")
        stream.flush()


def _workspace_resources(workspace):
    """Map selected resource snapshots without mixing modern and legacy sources."""
    modern = []
    legacy = []
    for entry in workspace.get("members", []):
        member = entry.get("member", "")
        value = entry.get("json")
        if not isinstance(value, dict) or not member.endswith(("resource-observation.json",
                                                                "resource-latest.json",
                                                                "resource-status.json")):
            continue
        parts = PurePosixPath(member).parts
        is_modern = "data" in parts and "harness" in parts and "producers" in parts
        observed_at = value.get("observed_at") or value.get("observed_at_ns")
        item = {**value, "source": member, "observed_at": observed_at}
        (modern if is_modern else legacy).append(item)
    return {"supervisor": modern[-1] if modern else None,
            "platform": legacy[-1] if legacy else None}


def _collect_workspace_observation(directory, client, run_id, *, created_at=None,
                                   native_scope_id=None, producer_run_id=None):
    """Read the live platform bundle without extracting or retaining its environment."""
    endpoint = run_path(run_id) + "/workspace/template-bundle"
    stamp = time.time()
    temporary = directory / f".workspace-observation-{time.time_ns()}.zip"
    live_root = directory / f".workspace-facts-{time.time_ns()}"
    receipt = {"kind": "hosted-workspace-observation", "endpoint": endpoint,
               "source": f"{API}{endpoint}",
               "requested_at": stamp, "status": "unknown"}
    try:
        client.download(endpoint, temporary)
        selected, jsonl_members, braid_statuses, parse_errors = [], [], [], []
        with ZipFile(temporary) as archive:
            for item in archive.infolist():
                relative = _workspace_member_name(item.filename)
                if relative is None or item.is_dir():
                    continue
                member = PurePosixPath(relative)
                if not _live_member(member):
                    continue
                if member.name == "resource-observation.json":
                    parts = member.parts
                    try:
                        data_index = parts.index("data")
                        observed_scope = parts[data_index + 2]
                        observed_run = parts[parts.index("producers") + 1]
                    except (ValueError, IndexError):
                        continue
                    if ((native_scope_id and observed_scope != native_scope_id) or
                            (producer_run_id and observed_run != producer_run_id)):
                        continue
                entry = {"member": relative, "bytes": item.file_size, "crc": item.CRC}
                if member.name in {"session.jsonl", "pi-timing.jsonl"}:
                    fact_path = _fact_path(relative)
                    target = live_root / fact_path
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with archive.open(item) as source, target.open("wb") as output:
                        shutil.copyfileobj(source, output)
                    entry["fact_path"] = str(fact_path)
                    jsonl_members.append(str(fact_path))
                elif member.name == "gateway.log":
                    fact_path = _fact_path(relative)
                    target = live_root / fact_path
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with archive.open(item) as source, target.open("wb") as output:
                        shutil.copyfileobj(source, output)
                    entry["fact_path"] = str(fact_path)
                    jsonl_members.append(str(fact_path))
                elif member.suffix == ".json":
                    with archive.open(item) as stream:
                        data = stream.read(2 * 1024 * 1024 + 1)
                    if len(data) <= 2 * 1024 * 1024:
                        try:
                            decoded = redact(json.loads(data))
                            entry["json"] = decoded
                            if member.name == "status.json" and "braid-state" in member.parts:
                                braid_statuses.append({"source": relative, "status": decoded})
                        except (ValueError, UnicodeDecodeError) as exc:
                            parse_errors.append({"member": relative, "error": f"{type(exc).__name__}: {exc}"})
                    else:
                        entry["json"] = {"status": "omitted", "reason": "member exceeds 2MiB"}
                selected.append(entry)
        reader_facts = _read_existing_facts(live_root, jsonl_members, created_at=created_at)
        signature = [(row["member"], row["bytes"], row["crc"]) for row in selected]
        receipt.update({"status": "observed", "observed_at": time.time(),
                        "archive_bytes": temporary.stat().st_size, "members": selected,
                        "native": {**reader_facts["native"], "raw_braid_status": braid_statuses},
                        "provider_usage": reader_facts["provider_usage"],
                        "parse_errors": parse_errors,
                        "aggregation": "replace-latest-facts; observation history is metadata only"})
        latest_path = directory / "workspace-latest.json"
        previous = None
        if latest_path.exists():
            try:
                previous = [(row["member"], row["bytes"], row["crc"])
                            for row in json.loads(latest_path.read_text()).get("members", [])]
            except (OSError, ValueError, KeyError, TypeError):
                previous = None
        changed = signature != previous
        receipt["changed"] = changed
        write_json(directory / "workspace-latest.json", receipt)
        if changed:
            _append_observation(directory / "workspace-observations.jsonl",
                                {"observed_at": receipt["observed_at"], "endpoint": endpoint,
                                 "archive_bytes": receipt["archive_bytes"], "members": selected,
                                 "native": receipt["native"], "provider_usage": receipt["provider_usage"],
                                 "parse_errors": parse_errors,
                                 "aggregation": receipt["aggregation"]})
        return receipt
    except Exception as exc:
        receipt.update({"status": "error", "observed_at": time.time(), "error": _error(exc)})
        write_json(directory / "workspace-latest.json", receipt)
        _append_observation(directory / "workspace-observations.jsonl", receipt)
        return receipt
    finally:
        temporary.unlink(missing_ok=True)
        for partial in directory.glob(temporary.name + ".*.partial"):
            partial.unlink(missing_ok=True)
        shutil.rmtree(live_root, ignore_errors=True)


def _snapshot_state(run):
    with _state(run) as (directory, state):
        return directory, json.loads(json.dumps(state))


def _clear_pending(run, request_id):
    with _state(run) as (directory, state):
        pending = state.get("pending") or {}
        if pending.get("request_id") == request_id:
            state["pending"] = None


def observe(run):
    """Observe outside the execution lock; only identity updates take the lock."""
    run, value, target, client = _context(run)
    directory, snapshot = _snapshot_state(run)
    pending = snapshot.get("pending")
    if pending and pending["action"] in {"upload", "create"}:
        history = _get(directory, client, "/competitions/" + target["competition_id"] + "/submissions", "history.json")
        found = {}
        if pending["action"] == "upload":
            matches = [row for row in history if row.get("display_name") == snapshot.get("display_name")]
            if len(matches) == 1:
                found["submission_id"] = matches[0]["id"]
        else:
            matches = {score["run_id"] for row in history if row.get("id") == snapshot.get("submission_id")
                       for score in row.get("task_scores", [])
                       if score.get("task_id") == snapshot.get("task") and score.get("run_id")}
            if len(matches) == 1:
                found["run_id"] = matches.pop()
        if found:
            with _state(run) as (directory, state):
                current = state.get("pending") or {}
                if current.get("request_id") == pending.get("request_id"):
                    state.update(found)
            directory, snapshot = _snapshot_state(run)
    if not snapshot.get("run_id"):
        return {"lifecycle": "failed" if snapshot.get("rejected") else "unknown", "activity": "unknown",
                "as_of": time.time(), "platform": snapshot}

    platform_run_id = snapshot["run_id"]
    remote = _get(directory, client, run_path(platform_run_id), "status.json")
    status_observed_at = time.time()
    if (remote.get("id") != platform_run_id or remote.get("submission_id") != snapshot.get("submission_id")
            or remote.get("requirement_id") != snapshot.get("task")):
        raise ValueError("Hosted status identity differs from this run's saved submission/task")
    phase = remote.get("status")
    if pending and pending["action"] in {"start", "stop"}:
        confirmed = phase in TERMINAL if pending["action"] == "stop" else bool(remote.get("started_at"))
        if confirmed:
            _clear_pending(run, pending.get("request_id"))
    steps = {step.get("key"): step.get("status") for step in remote.get("steps", [])}
    lifecycle = "stopped" if phase == "CANCELLED" else "completed" if phase == "PASSED" else (
        "completed" if phase == "FAILED" and steps.get("start_agent") == "completed" else
        "failed" if phase == "FAILED" else "running" if phase in {"RUNNING", "STARTING", "QUEUED"} else "unknown")
    cursor_file = directory / "log-cursor.json"
    cursor = json.loads(cursor_file.read_text()) if cursor_file.exists() else {"log_offset": 0}
    log_error = None
    try:
        chunk = _get(directory, client, run_path(platform_run_id) + "/logs?" + urlencode(cursor),
                     f"logs-{cursor.get('log_offset', 0)}.json")
        write_json(cursor_file, {"log_offset": chunk.get("log_offset", cursor.get("log_offset", 0)),
                               **({"after_event_id": chunk["last_event_id"]} if chunk.get("last_event_id") else {})})
    except Exception as exc:
        log_error = _error(exc)
        write_json(directory / "logs-error.json", {"as_of": time.time(), **log_error})
    if phase in TERMINAL:
        latest_path = directory / "workspace-latest.json"
        workspace = json.loads(latest_path.read_text()) if latest_path.exists() else {
            "status": "not-collected", "reason": "terminal observation uses save() for the complete export"}
    else:
        latest_path = directory / "workspace-latest.json"
        latest = None
        if latest_path.exists():
            try:
                latest = json.loads(latest_path.read_text())
                requested_at = float(latest.get("requested_at", 0))
            except (OSError, ValueError, TypeError):
                latest = None
                requested_at = 0
        else:
            requested_at = 0
        if latest and latest.get("status") == "observed" and time.time() - requested_at < 300:
            workspace = {**latest, "observation_reused": True}
        else:
            workspace = _collect_workspace_observation(directory, client, platform_run_id,
                                                       created_at=value.get("created_at"),
                                                       native_scope_id=value.get("native_scope_id"),
                                                       producer_run_id=value.get("run_id"))
    platform_usage = {key: redact(remote.get(key)) for key in
                      ("token_count", "token_usage", "usage", "model_usage", "models")
                      if remote.get(key) is not None}
    if platform_usage:
        write_json(directory / "platform-usage.json", {"source": run_path(platform_run_id),
                   "as_of": status_observed_at, "scope": "platform-run", "status": "partial",
                   "usage": platform_usage,
                   "note": "Platform usage dimensions are retained; they are not a bill."})
    amount = remote.get("token_cost_usd")
    currency = remote.get("token_cost_currency")
    if amount is not None:
        cost = {"amount": amount, "currency": currency, "source": run_path(platform_run_id),
                "as_of": status_observed_at, "scope": "platform-run"}
        if phase in TERMINAL:
            cost.update(kind="actual", status="terminal-platform-bill")
            write_json(run / "records/cost.json", cost)
        else:
            cost.update(kind="unknown", status="unverified-platform-running-field", platform_field=amount,
                        note="Running Hosted field semantics are unverified; not used as spend.")
            write_json(directory / "platform-meter.json", cost)
    workspace_error = workspace.get("error") if workspace.get("status") == "error" else None
    native = workspace.get("native") or {}
    provider_usage = workspace.get("provider_usage") or {"status": "unknown", "attempts": []}
    resources = _workspace_resources(workspace)
    return {"lifecycle": lifecycle, "activity": "unknown", "as_of": status_observed_at,
            "platform_run_id": platform_run_id, "platform_status": phase,
            "logs_error": log_error, "workspace_observation": workspace,
            "workspace_error": workspace_error, "native": native,
            "resources": resources,
            "brief": remote.get("failure_reason") or phase, "spend": {
                "kind": "actual" if amount is not None and phase in TERMINAL else "unknown",
                "status": "terminal-platform-bill" if amount is not None and phase in TERMINAL else
                          "unverified-platform-running-field" if amount is not None else "not-returned",
                "amount": amount if phase in TERMINAL else None,
                "platform_field": amount if phase not in TERMINAL else None,
                "currency": currency, "usage": native.get("usage"),
                "provider_usage": provider_usage, "source": run_path(platform_run_id),
                "as_of": status_observed_at}}


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
            response = redact((state.get("pending") or {}).get("response"))
            request_id = (state.get("pending") or {}).get("request_id")
            state["pending"] = None
        else:
            response = None
            request_id = (state.get("pending") or {}).get("request_id")
    return {"lifecycle": "unknown", "activity": "unknown", "control_action": "stop",
            "platform_status": "cancel_requested", "platform_run_id": state["run_id"],
            "request_id": request_id, "response": response,
            "brief": "cancel request accepted; observe() must confirm terminal status",
            "as_of": time.time()}


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
