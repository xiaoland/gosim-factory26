"""Public run API shared by CLI and ordinary Python automation.

Execution adapters own the real platform handles. Queries read saved records;
neither a query nor the Console creates another observation loop.
"""
from pathlib import Path
import json
import os
import subprocess
import sys
import time

from .arc_bench import run_layout
from .records import write_json
from .control import process_identity, process_state

ROOT = Path(__file__).resolve().parents[1]
TERMINAL = {"completed", "failed", "stopped"}


def run_root():
    path = Path(os.environ.get("LAB_RUN_ROOT", ROOT / "runs/lab")).expanduser().resolve()
    run_layout.storage_path(path)
    return path


def resolve(run):
    candidate = Path(run).expanduser()
    if not (candidate / "manifest.json").is_file():
        if candidate.name != str(run) or str(run) in {".", ".."}:
            raise FileNotFoundError(f"run manifest not found: {candidate / 'manifest.json'}")
        candidate = run_root() / "runs" / str(run)
    candidate = candidate.resolve(strict=True)
    run_layout.storage_path(candidate)
    manifest = run_layout.manifest(candidate)
    if manifest.get("record_type") != "arc.run":
        raise ValueError(f"not a current ARC run: {candidate}; historical records use lab.exp/history")
    return candidate


def successors(run):
    """Return direct, explicitly recorded restart children of one run.

    This is a read-only registry lookup.  It never chooses between branches;
    callers must surface more than one child as ambiguous.
    """
    source = resolve(run)
    rows = []
    registry = source.parent
    for candidate in registry.iterdir():
        manifest_path = candidate / "manifest.json"
        if not candidate.is_dir() or not manifest_path.is_file() or candidate == source:
            continue
        try:
            value = run_layout.manifest(candidate)
        except (OSError, ValueError, TypeError):
            continue
        # ``source_run`` is also used by independent application evaluations.
        # Only the explicit restart provenance denotes a continuation that a
        # read-only watcher may follow.
        source_meta = value.get("source")
        if not isinstance(source_meta, dict) or source_meta.get("kind") != "restart":
            continue
        recorded = value.get("source_run")
        if recorded != source.name and Path(str(recorded)).name != source.name:
            continue
        saved = candidate / "records/status.json"
        facts = {}
        if saved.is_file():
            try:
                facts = json.loads(saved.read_text())
            except (OSError, ValueError, TypeError):
                facts = {}
        rows.append({"run_id": candidate.name, "path": str(candidate),
                     "created_at": value.get("created_at"),
                     "lifecycle": facts.get("lifecycle", value.get("lifecycle", "unknown")),
                     "variant": value.get("variant"), "task": value.get("task")})
    return sorted(rows, key=lambda row: (row.get("created_at") or 0, row["run_id"]))


def _continuation(path, manifest, children=None):
    source = manifest.get("source_run")
    children = successors(path) if children is None else children
    if len(children) == 1:
        child = children[0]
        return {"state": "single", "source_run": path.name, "successor": child,
                "label": f"{path.name}→{child['run_id']}"}
    if len(children) > 1:
        return {"state": "ambiguous", "source_run": path.name, "successors": children,
                "label": f"{path.name}→({len(children)} successors; explicit run required)"}
    if source:
        return {"state": "origin", "source_run": str(source), "successor": path.name,
                "label": f"{Path(str(source)).name}→{path.name}"}
    return {"state": "none", "source_run": None, "successors": [], "label": None}


def _restart_summary(path, manifest, facts):
    """Summarize restart provenance and current-run observations only.

    The native session may be retained across a restart, so it is deliberately
    not used as the request count.  Provider attempts are already sliced by
    the current producer run; the complete native session remains a separately
    named fact in ``native_session_scope``.
    """
    source_meta = manifest.get("source") or {}
    restart_record = path / "records/restart.json"
    restart = {}
    if restart_record.is_file():
        try:
            value = json.loads(restart_record.read_text())
            if isinstance(value, dict):
                restart = value
        except (OSError, ValueError, TypeError):
            restart = {}
    dispatch = restart.get("started") if isinstance(restart.get("started"), dict) else {}
    dispatch_record = path / "records/dispatch.json"
    docker_observe_record = path / "records/docker-observe.json"
    dispatch_facts = {}
    docker_observe = {}
    for record_path, target in ((dispatch_record, dispatch_facts),
                                (docker_observe_record, docker_observe)):
        if record_path.is_file():
            try:
                value = json.loads(record_path.read_text())
                if isinstance(value, dict):
                    target.update(value)
            except (OSError, ValueError, TypeError):
                pass
    consumption_path = path / "records/material-consumption.json"
    consumption = {}
    if consumption_path.is_file():
        try:
            value = json.loads(consumption_path.read_text())
            if isinstance(value, dict):
                consumption = value
        except (OSError, ValueError, TypeError):
            pass
    is_restart = source_meta.get("kind") == "restart" or bool(restart)
    spend = facts.get("spend") if isinstance(facts.get("spend"), dict) else {}
    provider = spend.get("provider_usage") if isinstance(spend.get("provider_usage"), dict) else {}
    attempts = provider.get("attempts") if isinstance(provider.get("attempts"), list) else []
    timestamps = [item.get("as_of") for item in attempts
                  if isinstance(item, dict) and isinstance(item.get("as_of"), (int, float))]
    response_attempts = [item for item in attempts if isinstance(item, dict) and
                         (item.get("http_status") is not None or
                          item.get("usage_status") in {"recorded", "partial", "returned"} or
                          item.get("response_id"))]
    successful_responses = [item for item in response_attempts if
                            (isinstance(item.get("http_status"), int) and
                             200 <= item["http_status"] < 300) or
                            (item.get("http_status") is None and
                             item.get("usage_status") == "recorded")]
    activity = facts.get("activity")
    last_activity = facts.get("last_activity_at")
    started_at = manifest.get("started_at") or manifest.get("created_at")
    effective_action = facts.get("effective_action")
    if not isinstance(effective_action, dict):
        native_facts = facts.get("native")
        candidate = native_facts.get("effective_action") if isinstance(native_facts, dict) else None
        effective_action = candidate if isinstance(candidate, dict) else None
    effective_at = effective_action.get("at") if isinstance(effective_action, dict) else None
    effective_identity = (isinstance(effective_action, dict) and
                          (effective_action.get("run_id") == path.name or
                           effective_action.get("producer_run_id") == path.name))
    effective_current = bool(effective_identity and isinstance(effective_at, (int, float)) and
                             (not isinstance(started_at, (int, float)) or effective_at >= started_at) and
                             effective_action.get("source"))
    valid_action = effective_current
    observation = {
        "activity": activity,
        "brief": facts.get("brief"),
        "last_activity_at": last_activity,
        "evidence": facts.get("evidence"),
        "effective_action": effective_action if isinstance(effective_action, dict) else None,
        "as_of": facts.get("as_of"),
        "valid": valid_action,
        "evidence_current_run": effective_current,
        "action_source": effective_action.get("source") if effective_current else None,
        "action_at": effective_at if effective_current else None,
        "source": "saved variant status and current-run provider observations",
    }
    if not valid_action:
        observation["reason"] = ("running-but-no-valid-action-observed"
                                   if facts.get("lifecycle") == "running"
                                   else "no-current-run-variant-action-evidence")
    consumed_run = consumption.get("run") if isinstance(consumption.get("run"), dict) else {}
    consumed_program = consumption.get("program") if isinstance(consumption.get("program"), dict) else {}
    consumed_runtime = consumption.get("runtime") if isinstance(consumption.get("runtime"), dict) else {}
    consumed_native = consumption.get("native") if isinstance(consumption.get("native"), dict) else {}
    consumed_identity = consumed_run.get("run_id") == path.name
    scope_matches = (not manifest.get("native_scope_id") or
                     consumed_native.get("scope_id") == manifest.get("native_scope_id"))
    consumed_adopted = (True if consumed_identity and scope_matches and
                        consumption.get("consumed_at") and consumed_program.get("entry_sha256") and
                        consumed_runtime.get("source_sha256") and consumed_runtime.get("native_files_sha256")
                        else None)
    return {
        "is_restart": is_restart,
        "source_run": manifest.get("source_run") if is_restart else None,
        "material": {
            "saved": restart.get("saved"),
            "restart_snapshot": manifest.get("restart_snapshot"),
            "native_resume": manifest.get("native_resume"),
            "requirements_version": manifest.get("requirements_version"),
            "source_as_of": (restart.get("saved") or {}).get("as_of")
                if isinstance(restart.get("saved"), dict) else None,
            "frozen": {
                "program_version": manifest.get("program_version"),
                "runtime_source_present": bool(manifest.get("runtime_source")),
                "native_scope_id": manifest.get("native_scope_id"),
                "source": "destination manifest/assembly",
            },
            "dispatch": {
                "program_version": dispatch.get("program_version"),
                "runtime_source_present": bool(dispatch.get("runtime_source")),
                "remote_run": dispatch.get("remote_run") or dispatch_facts.get("remote_run"),
                "as_of": dispatch.get("started_at") or dispatch.get("created_at")
                    or dispatch_facts.get("as_of"),
                "source": "dispatch/start receipt; not proof of execution-side consumption",
            },
            "consumed": {
                "adopted": consumed_adopted,
                "program": consumed_program,
                "runtime": consumed_runtime,
                "native": consumed_native,
                "execution_observed": bool(docker_observe.get("container_id")),
                "source": ("records/material-consumption.json" if consumption else
                            "records/docker-observe.json" if docker_observe else None),
                "reason": (None if consumed_adopted else
                           "execution-side material/version receipt unavailable"),
            },
        },
        "actual_requests": {
            "count": len(attempts),
            "responses": len(response_attempts),
            "successful_responses": len(successful_responses),
            "last_as_of": max(timestamps) if timestamps else None,
            "scope": provider.get("scope") or "current-run-provider-attempts",
            "source": provider.get("source"),
            "time_source": "gateway.log event timestamp_ms" if attempts else None,
        },
        "variant_observation": observation,
    }


def status(run=None, *, include_all=False):
    """Read saved execution facts and the variant's saved activity judgment."""
    if run is None:
        directory = run_root() / "runs"
        rows = [status(path) for path in directory.iterdir()
                if path.is_dir() and (path / "manifest.json").is_file()] if directory.is_dir() else []
        return sorted((row for row in rows if include_all or
                       (not row.get("archived") and row.get("lifecycle") != "completed")),
                      key=lambda row: row.get("created_at") or 0, reverse=True)
    path = resolve(run)
    manifest = run_layout.manifest(path)
    saved = path / "records/status.json"
    if saved.is_file():
        try:
            facts = json.loads(saved.read_text())
            if not isinstance(facts, dict):
                raise ValueError("saved status must be an object")
        except (OSError, ValueError) as exc:
            facts = {"lifecycle": "unknown", "activity": "unknown", "as_of": None,
                     "error": f"{saved}: {type(exc).__name__}: {exc}"}
    else:
        facts = {"lifecycle": "starting", "activity": "unknown", "brief": "尚无执行观察",
                 "as_of": manifest.get("created_at")}
    archive_path = path / "records/archive.json"
    archived = json.loads(archive_path.read_text()).get("archived", False) if archive_path.is_file() else False
    direct_successors = successors(path)
    continuation = _continuation(path, manifest, direct_successors)
    spend = facts.get("spend") if isinstance(facts.get("spend"), dict) else {}
    usage = spend.get("usage") if isinstance(spend.get("usage"), dict) else {}
    return {**manifest, **facts, "path": str(path), "archived": archived,
            "successors": direct_successors,
            "continuation": continuation,
            "usage_scope": usage.get("scope"),
            "native_session_scope": ("full-retained-native-session"
                                     if manifest.get("native_scope_id") and isinstance(facts.get("native"), dict)
                                     else None),
            "restart_summary": _restart_summary(path, manifest, facts)}


def _background(run, module, args, name):
    target = run_layout.manifest(run).get('target_config') or {}
    if name != 'relay' and target.get('kind') == 'local' and target.get('executor') != 'local':
        from .arc_bench.local_run import spawn
        receipt = spawn(run, module, args, name=name)
        write_json(run / 'records' / f'{name}.json', receipt)
        if name == 'supervisor':
            _background(run, 'lab.automation', ['relay', run], 'relay')
        return receipt.get('pid')
    records = run / "records"
    with (records / f"{name}.log").open("ab") as output:
        env = dict(os.environ, LAB_RUN=str(run), LAB_RUN_ROOT=str(run_root()))
        process = subprocess.Popen([sys.executable, "-m", module, *map(str, args)],
                                   cwd=ROOT, env=env, stdout=output, stderr=subprocess.STDOUT,
                                   start_new_session=True)
    write_json(records / f"{name}.json", {**process_identity(process.pid),
                                          "module": module, "arguments": list(map(str, args)),
                                          "started_at": time.time()})
    return process.pid


def publish(path):
    """Publish saved facts; Console failure never changes execution status."""
    from .backend import publish_run, saved_record_summaries
    path = resolve(path)
    manifest = run_layout.manifest(path)
    config = manifest.get("observability") or {}
    if not config.get("service_url"):
        return
    try:
        token_file = config.get("registration_token_file")
        collector_file = config.get("collector_token_file")
        credentials = []
        for filename in (token_file, collector_file):
            if filename:
                source = Path(filename)
                if not source.is_absolute():
                    source = path / source
                credentials.append(source.read_text().strip())
            else:
                credentials.append(None)
        token, collector = credentials
        row = status(path)
        facts = {key: row[key] for key in (
            "lifecycle", "activity", "brief", "as_of", "last_activity_at", "evidence",
            "native", "spend", "resources", "error", "observation_failed_at"
        ) if key in row}
        records = saved_record_summaries(path)
        published = publish_run(config["service_url"], {**manifest, "archived": row["archived"]},
                                status=facts, records=records, token=token, collector_token=collector)
        write_json(path / "records/console-publish.json", {"as_of": time.time(), "published": True,
                   "run_id": published.get("run_id", path.name)})
    except Exception as exc:
        write_json(path / "records/console-publish.json", {"as_of": time.time(), "published": False,
                   "error": f"{type(exc).__name__}: {exc}"})


def start(variant, target, task, *, route=None, competition=False, script=None):
    """Assemble inputs, directly dispatch, then detach observation and automation."""
    from .arc_bench import execution
    if script:
        import shutil
        source = Path(script).resolve(strict=True)
    path = run_layout.create_run(run_root(), variant, target, str(task), route=route,
                                 competition=competition)
    try:
        if script:
            destination = path / "records/automation.py"
            shutil.copy2(source, destination)
        execution.assemble(path)
        execution.start(path)
    except Exception as exc:
        # The adapter may already have recorded an uncertain platform write.
        # An exception is not evidence that a dispatched execution failed.
        saved = path / "records/status.json"
        if not saved.is_file():
            write_json(saved, {"lifecycle": "failed", "activity": "unknown",
                       "as_of": time.time(), "error": f"{type(exc).__name__}: {exc}"})
        raise
    _background(path, "lab.automation", ["observe", path], "supervisor")
    # A user policy supplements observation; it must not disable task evaluations.
    _background(path, "lab.automation", ["default", path], "evaluations" if script else "automation")
    if script:
        target_config = run_layout.manifest(path).get('target_config') or {}
        if target_config.get('kind') == 'local' and target_config.get('executor') != 'local':
            from .arc_bench.local_run import spawn
            receipt = spawn(path, '', [], script=destination, name='automation')
            write_json(path / 'records/automation.json', receipt)
        else:
            with (path / "records/automation.log").open("ab") as output:
                process = subprocess.Popen([sys.executable, str(destination)], cwd=ROOT,
                             env=dict(os.environ, LAB_RUN=str(path), LAB_RUN_ROOT=str(run_root())),
                             stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
            write_json(path / "records/automation.json", {**process_identity(process.pid),
                        "source": str(destination), "started_at": time.time()})
    return status(path)


def _control(run, action):
    from .arc_bench import execution
    path = resolve(run)
    return execution.control(path, action)


def stop(run):
    """Stop only this run; its supervisor continues saving available results."""
    return _control(run, "stop")


def pause(run):
    return _control(run, "pause")


def resume(run):
    return _control(run, "resume")


def save(run, *, output=None):
    """Create a portable snapshot without changing this run's lifecycle."""
    from .portable_save import create
    return create(resolve(run), output=output)


def restart(run, *, target=None, task=None, route=None, snapshot=None):
    from .arc_bench.restart import restart as restart_run
    result = restart_run(resolve(run), target=target, task=task, route=route, snapshot=snapshot)
    path = resolve(result["path"] if isinstance(result, dict) else result)
    _background(path, "lab.automation", ["observe", path], "supervisor")
    _background(path, "lab.automation", ["default", path], "automation")
    return status(path)


def wait(run):
    """Wait for this run's saved terminal record, without platform polling."""
    path = resolve(run)
    while True:
        row = status(path)
        if row.get("lifecycle") in TERMINAL:
            return row
        supervisor = path / "records/supervisor.json"
        if supervisor.is_file() and process_state(json.loads(supervisor.read_text())) == "lost":
            raise RuntimeError(f"observer exited before a confirmed terminal record: {supervisor}; "
                               "actual execution may still be running; see saved logs")
        time.sleep(2)


def archive(run, *, undo=False):
    path = resolve(run)
    write_json(path / "records/archive.json", {"archived": not undo, "as_of": time.time()})
    publish(path)
    return status(path)


def logs(run, *, follow=False):
    path = resolve(run)
    cursors = {}
    while True:
        for log in sorted((path / "records").glob("*.log")):
            with log.open("rb") as stream:
                stream.seek(cursors.get(log, 0))
                first_chunk = True
                while chunk := stream.read(65536):
                    if first_chunk:
                        metadata = log.with_name(log.name + ".meta.json")
                        boundary = json.loads(metadata.read_text()) if metadata.is_file() else {}
                        suffix = "; 包含迁移历史，当前 run 边界未知" if boundary.get("retained_history") else ""
                        sys.stdout.write(f"\n--- {log.name}{suffix} ---\n")
                        first_chunk = False
                    sys.stdout.write(chunk.decode(errors="replace"))
                cursors[log] = stream.tell()
        sys.stdout.flush()
        if not follow or status(path).get("lifecycle") in TERMINAL:
            return
        time.sleep(1)


def evaluate(run, *, kind, snapshot=None, configuration=None):
    from .arc_bench.evaluate import evaluate_run
    return evaluate_run(resolve(run), kind=kind, snapshot=snapshot, configuration=configuration)
