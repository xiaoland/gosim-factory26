"""Concrete process boundary for current Lab runs.

One worker process owns one run. Historical ``lab.exp`` execution remains
outside this module; current runs consume only their manifest and data tree.
"""

from __future__ import annotations

import hashlib
from collections import deque
from datetime import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any, Mapping
import shutil
import secrets
import shlex

from .run_layout import manifest, paths, write_json


def _repo() -> Path:
    return Path(__file__).resolve().parents[2]


def _target(state: Mapping[str, Any]) -> dict[str, Any]:
    target = state.get("target_config")
    if isinstance(target, Mapping):
        return dict(target)
    name = state.get("target")
    config_path = Path(os.environ.get("LAB_CONFIG", Path(__file__).with_name("targets.json")))
    config = json.loads(config_path.read_text(encoding="utf-8"))
    value = config.get("targets", {}).get(str(name))
    if not isinstance(value, dict):
        raise ValueError(f"unknown ARC target {name!r} in {config_path}")
    variant = config.get("variants", {}).get(str(state.get("variant")), {})
    defaults = config.get('defaults', {})
    result = {"name": name, **defaults, **value, **variant}
    result['environment'] = {**defaults.get('environment', {}), **value.get('environment', {}),
                             **variant.get('environment', {})}
    return result


def _task_config(state: Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(state.get("task_config"), Mapping):
        return dict(state["task_config"])
    task = str(state.get("task", ""))
    source = Path(task).expanduser()
    if source.is_dir():
        config = source / "task.json"
        return {"path": str(source.resolve()), **(json.loads(config.read_text()) if config.is_file() else {})}
    registry = Path(os.environ.get("LAB_CONFIG", Path(__file__).with_name("targets.json")))
    config = json.loads(registry.read_text())
    value = config.get("tasks", {}).get(task)
    if not isinstance(value, dict):
        raise FileNotFoundError(f"task {task!r} is neither a directory nor registered in {registry}")
    return dict(value)


def _runtime_profile(target: Mapping[str, Any], program: Path) -> tuple[Path, Path]:
    """Resolve the native runtime and skills from the target contract.

    A run may use a preinstalled target runtime, but the path must be explicit;
    silently falling back to a developer's PATH was the source of old drift.
    """
    runtime = target.get("runtime") or target.get("runtime_path") or os.environ.get("FACTORY26_RUNTIME")
    skills = target.get("skills") or target.get("skills_path")
    runtime_path = Path(runtime).expanduser().resolve() if runtime else program / "runtime"
    skills_path = Path(skills).expanduser().resolve() if skills else program / "skills"
    if not runtime_path.is_dir() or not skills_path.is_dir():
        raise RuntimeError("local ARC target requires explicit runtime and skills directories")
    return runtime_path, skills_path


def _tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        digest.update(str(path.relative_to(root)).encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def freeze_model_channel(run_path: Path, state: Mapping[str, Any], target: Mapping[str, Any]):
    """Freeze the selected model route and private provider bindings.

    This is shared by generation assembly and independent evaluations.  It
    performs no model request and never chooses a catalog default: a recipe or
    explicit route must cover every alias declared by the selected variant.
    The returned state/target contain only references to the run-local private
    provider file; secret values never enter the manifest.
    """
    run_path = Path(run_path).expanduser().resolve()
    layout = paths(run_path)
    updated = dict(state)
    frozen_target = dict(target)
    recipe = frozen_target.get("model_recipe")
    route_input = state.get("route") or frozen_target.get("route")
    if recipe:
        route_input = route_input or _repo() / "harness/model-recipes" / f"{recipe}.json"
    if not route_input:
        if frozen_target.get("kind") == "hosted" and not frozen_target.get("model_config"):
            raise ValueError("Hosted evaluation needs an explicit frozen model channel")
        return updated, frozen_target, None
    from scripts.hackathon_gateway import prepare_catalog, read_assignments
    route = Path(route_input).expanduser().resolve(strict=True)
    routes = json.loads(route.read_text())
    aliases = frozen_target.get("model_aliases") or []
    missing = set(aliases) - set(routes)
    if missing:
        raise ValueError(f"model recipe lacks required aliases: {sorted(missing)}")
    routes = {alias: routes[alias] for alias in aliases} if aliases else routes
    destination = layout["inputs"] / "gateway-routes.json"
    write_json(destination, routes)
    catalog, selected = prepare_catalog(_repo() / "harness/model-gateway.json", routes, aliases=aliases)
    write_json(layout["inputs"] / "model-gateway.json", catalog)
    references = {entry["litellm_params"][field].removeprefix("os.environ/")
                  for entry in catalog["model_list"] for field in ("api_base", "api_key")}
    environment_file = frozen_target.get("environment_file")
    if not environment_file:
        raise ValueError("selected model recipe has no private environment file")
    environment = read_assignments(environment_file)
    missing = references - environment.keys()
    if missing:
        raise ValueError(f"selected model recipe needs provider variables: {sorted(missing)}")
    private = run_path / ".private"
    private.mkdir(mode=0o700, exist_ok=True)
    provider_env = private / "provider-env.json"
    write_json(provider_env, {name: environment[name] for name in references})
    provider_env.chmod(0o600)
    updated["route"] = str(destination)
    updated["model_recipe"] = recipe or "explicit"
    updated["model_routes"] = selected
    updated["provider_env_file"] = str(provider_env)
    if frozen_target.get("kind") == "hosted":
        primary = frozen_target.get("environment", {}).get("MODEL", "glm-5.3-flash")
        try:
            entry = next(row for row in catalog["model_list"]
                         if row["model_name"] == primary and row["litellm_params"]["order"] == 0)
        except StopIteration as exc:
            raise ValueError(f"selected model recipe has no primary model {primary!r}") from exc
        params = entry["litellm_params"]
        base_name = params["api_base"].removeprefix("os.environ/")
        frozen_target["credential_file"] = str(provider_env)
        frozen_target["credential_env"] = params["api_key"].removeprefix("os.environ/")
        frozen_target["model_config"] = {
            "model": params["model"].removeprefix("openai/"),
            "visual_model": "glm-5.3-flash",
            "base_url": environment[base_name],
        }
    return updated, frozen_target, route_input


def assemble(run: str | os.PathLike[str]) -> dict[str, Any]:
    """Materialize the selected variant and explicit target contract."""
    run_path = Path(run).expanduser().resolve()
    state = manifest(run_path)
    target = _target(state)
    variant = str(state.get("variant", ""))
    source = _repo() / "variants" / variant
    if not source.is_dir():
        raise FileNotFoundError(f"variant is not installed: {variant}")
    layout = paths(run_path)
    write_json(layout['records']/'status.json', {'lifecycle': 'starting', 'activity': 'unknown',
               'brief': 'assembling program and frozen inputs', 'phase': 'assembly', 'as_of': time.time()})
    if any(layout["program"].iterdir()):
        raise FileExistsError(f"program already assembled: {layout['program']}")
    shutil.copytree(source, layout["program"], dirs_exist_ok=True, symlinks=True,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    task_config = _task_config(state)
    task = Path(task_config.get("requirements") or task_config["path"]).expanduser().resolve(strict=True)
    if not (task / "requirements.yaml").is_file():
        raise FileNotFoundError(f"requirements.yaml is missing: {task}")
    if not (layout["inputs"] / "requirements").exists():
        shutil.copytree(task, layout["inputs"] / "requirements", symlinks=True)
    for field, member in (("support", "support"),):
        value = target.get(field)
        if value:
            source_path = Path(value).expanduser().resolve(strict=True)
            destination = layout["program"] / member
            if destination.exists():
                raise FileExistsError(f"target material overlaps variant program: {destination}")
            shutil.copytree(source_path, destination, symlinks=True)
    runtime, skills = _runtime_profile(target, layout["program"])
    entry = state.get("program_entry") or "main.py"
    updated = dict(state)
    requirements_version = _tree_digest(layout["inputs"] / "requirements")
    updated.update({"target_config": target, "target_kind": target["kind"],
                    "task_config": task_config, "requirements_version": requirements_version,
                    "native_scope_id": state.get("native_scope_id") or run_path.name,
                    "native_resume": bool(state.get("native_resume")),
                    "program_version": _tree_digest(layout["program"]),
                    "program_entry": entry, "assembled_at": time.time()})
    if updated["native_resume"] and state.get("requirements_version") != requirements_version:
        raise ValueError("native resume requirements differ from the retained session")
    updated, target, route_input = freeze_model_channel(run_path, updated, target)
    updated["target_config"] = target
    contract = {
        "run_id": run_path.name, "native_scope_id": updated["native_scope_id"],
        "native_resume": updated["native_resume"], "requirements_version": requirements_version,
        "target_kind": updated["target_kind"],
        'model_recipe': updated.get('model_recipe'),
        'model_alias_map': target.get('model_alias_map', {}),
        'provider_env_names': sorted({entry['litellm_params'][field].removeprefix('os.environ/')
            for entry in json.loads((_repo()/'harness/model-gateway.json').read_text())['model_list']
            for field in ('api_base', 'api_key')}) if route_input else [],
        'model_environment': {name: value for name, value in target.get('environment', {}).items()
            if name in {'OPENAI_BASE_URL', 'FACTORY26_BASE_URL', 'MODEL', 'VISUAL_MODEL',
                        'FACTORY26_MODEL_PROVIDER', 'FACTORY26_VISUAL_PROVIDER'}},
    }
    write_json(layout["inputs"] / "lab-run.json", contract)
    write_json(layout["workspace"] / ".factory26/lab-run.json", contract)
    observability = target.get("observability") or state.get("observability")
    if isinstance(observability, Mapping):
        updated["observability"] = {key: observability[key] for key in
                                     ("service_url", "registration_token_file", "collector_token_file", 'collector_url',
                                      'import_host', 'import_root')
                                     if observability.get(key)}
    builder = source / "build.py"
    if not builder.is_file():
        raise FileNotFoundError(f"variant package builder is missing: {builder}")
    package_path = layout["inputs"] / "agent-package.zip"
    command = [sys.executable, str(builder), "--runtime", str(runtime),
               "--skills", str(skills),
               "--run-config", str(layout["inputs"] / "lab-run.json")]
    if target.get('otlp_deps'):
        command += ['--otlp-deps', str(target['otlp_deps'])]
    if target['kind'] == 'local':
        command += ['--directory', str(layout['program'])]
    else:
        command += ['--output', str(package_path)]
    if updated.get("route"):
        command += ["--route", updated["route"]]
        command += ['--catalog', str(layout['inputs']/'model-gateway.json')]
        if target['kind'] == 'hosted':
            command += ['--provider-env', updated['provider_env_file']]
    if target["kind"] == "hosted" and state.get("source_run"):
        command += ["--seed-data", str(layout["workspace"].parent)]
    write_json(layout["records"] / "package-build.json", {"argv": command, "started_at": time.time()})
    with (layout["records"] / "package-build.stdout.log").open("ab") as output, \
            (layout["records"] / "package-build.stderr.log").open("ab") as errors:
        result = subprocess.run(command, cwd=_repo(), stdout=output, stderr=errors)
    if result.returncode:
        raise RuntimeError(f"variant package build exited {result.returncode}; see {layout['records']}/package-build.*.log")
    write_json(layout['records']/'program-assembly.json', {
        'started_at': updated['assembled_at'], 'finished_at': time.time(),
        'transport': 'directory' if target['kind'] == 'local' else 'zip',
        'program': str(layout['program'])})
    if target['kind'] == 'hosted':
        updated["agent_package"] = str(package_path)
        updated["agent_package_sha256"] = hashlib.sha256(package_path.read_bytes()).hexdigest()
    else:
        updated['program_version'] = _tree_digest(layout['program'])
        updated['runtime_source'] = json.loads((runtime/'runtime-source.json').read_text())
    write_json(layout["manifest"], updated)
    return updated






def _save_handle(run: Path, **updates: Any) -> dict[str, Any]:
    current = manifest(run)
    current.update(updates)
    write_json(paths(run)["manifest"], current)
    return current










def _configure_observability(run: Path):
    """Register once and keep producer credentials outside migratable data."""
    state = manifest(run)
    config = dict(state.get('observability') or {})
    if not config.get('service_url'):
        return
    private = run/'.private'
    private.mkdir(mode=0o700, exist_ok=True)
    collector_file = private/'collector.token'
    if not collector_file.exists():
        with os.fdopen(os.open(collector_file, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'w') as stream:
            stream.write(secrets.token_urlsafe(24))
    config['collector_token_file'] = str(collector_file)
    state['observability'] = config
    target = dict(state['target_config'])
    if target['kind'] == 'local':
        environment = Path(target['environment_file']).read_text()
        endpoint = config.get('collector_url') or config['service_url']
        additions = {
            'OTEL_EXPORTER_OTLP_ENDPOINT': endpoint,
            'OTEL_EXPORTER_OTLP_PROTOCOL': 'http/protobuf',
            'OTEL_EXPORTER_OTLP_HEADERS': 'x-experiment-token='+collector_file.read_text().strip(),
            'OTEL_EXPORTER_OTLP_COMPRESSION': 'none',
            'OTEL_SDK_DISABLED': 'false',
        }
        # Restart may use the previous run's private env. Replace only our own
        # OTLP variables so a new run never continues sending to its source.
        lines = [line for line in environment.splitlines() if line.split('=', 1)[0] not in additions]
        lines.extend(name+'='+value for name, value in additions.items())
        env_file = private/'runner.env'
        with os.fdopen(os.open(env_file, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600), 'w') as stream:
            stream.write('\n'.join(lines)+'\n')
        target['environment_file'] = str(env_file)
        state['target_config'] = target
    write_json(paths(run)['manifest'], state)
    from lab.backend import register_run
    try:
        registered = register_run(config['service_url'], state,
            registration_token=Path(config['registration_token_file']).read_text().strip(),
            collector_token=collector_file.read_text().strip())
        write_json(paths(run)['records']/'collector-registration.json', {
            'registered': True, 'run_id': registered['run_id'], 'as_of': time.time()})
    except Exception as error:
        write_json(paths(run)['records']/'collector-registration.json', {
            'registered': False, 'error': f'{type(error).__name__}: {error}', 'as_of': time.time()})


def start(run: str | os.PathLike[str]) -> dict[str, Any]:
    run_path = Path(run).expanduser().resolve()
    write_json(paths(run_path)['records']/'status.json', {'lifecycle': 'starting', 'activity': 'unknown',
               'brief': 'dispatching to execution host', 'phase': 'dispatch', 'as_of': time.time()})
    _configure_observability(run_path)
    state = manifest(run_path)
    target = _target(state)
    if target.get("kind") == "hosted":
        from . import hosted_run
        try:
            result = hosted_run.start(run_path)
        except Exception as exc:
            # The Hosted adapter writes the raw request/response before an
            # uncertain error. Do not retry a potentially billable POST.
            _save_handle(run_path, lifecycle="unknown", start_error={"type": type(exc).__name__, "message": str(exc)})
            return _save_handle(run_path, lifecycle="unknown", adapter_error=str(exc))
        lifecycle = result.get("lifecycle", "unknown") if isinstance(result, dict) else "unknown"
        return _save_handle(run_path, lifecycle=lifecycle, platform=result,
                            started_at=time.time(), target_config=target)
    from . import local_run
    result = local_run.start(run_path)
    return _save_handle(run_path, **result, target_config=target)








def _native_facts(run: Path):
    run = run.resolve()
    harness = paths(run)["harness"]
    messages, turns, errors = deque(maxlen=500), deque(maxlen=500), deque(maxlen=20)
    sessions = {}
    candidates = set(harness.rglob("session.jsonl")) | set(harness.rglob("pi-timing.jsonl"))
    for path in sorted(candidates):
        session_id = None
        source = str(path.relative_to(run))
        try:
            with path.open() as stream:
                for number, line in enumerate(stream, 1):
                    try:
                        value = json.loads(line)
                        if not isinstance(value, dict):
                            raise ValueError("native record is not an object")
                        kind = value.get("kind") or value.get("type")
                        if kind == "session":
                            session_id = value.get("id")
                            continue
                        identity = value.get("native_session_id") or value.get("session_id") or session_id
                        if not identity:
                            continue
                        stamp = value.get("at_ms") if value.get("at_ms") is not None else value.get("timestamp")
                        if isinstance(stamp, str):
                            stamp = datetime.fromisoformat(stamp.replace("Z", "+00:00")).timestamp()
                        elif isinstance(stamp, (int, float)):
                            stamp = stamp / 1000 if stamp > 10_000_000_000 else stamp
                        else:
                            continue
                        row = {"at": stamp, "source": source, "session_id": identity,
                               "turn_id": value.get("turn_id"), "request_id": value.get("request_id"),
                               "response_id": value.get("response_id"), "event": kind}
                        message = value.get('message') or {}
                        if isinstance(message, dict) and message.get('stopReason'):
                            row['stop_reason'] = message['stopReason']
                            if message.get('errorMessage'):
                                row['error'] = str(message['errorMessage'])[:16384]
                        if kind in {"message", "message_end"}:
                            messages.append(row)
                        if kind in {"response_headers", "message_end", "provider_turn", "turn_complete"}:
                            turns.append(row)
                        prior = sessions.get(identity)
                        if prior is None or stamp >= prior["last_activity_at"]:
                            state = {"request_start": "active", "first_update": "active",
                                     "activity_sample": "active", "tool_start": "waiting_tool",
                                     "tool_end": "active", "message_end": "observed"}.get(kind, "observed")
                            sessions[identity] = {"session_id": identity, "state": state,
                                "last_activity_at": stamp, "observed_at": time.time(),
                                "source": source, "reader_status": "ok",
                                "request_id": value.get("request_id"), "turn_id": value.get("turn_id")}
                    except (ValueError, TypeError, OverflowError) as exc:
                        # A writer may still be appending its final line. Keep
                        # prior evidence and its concrete parse error, not a
                        # fabricated session/turn identity or file-mtime pulse.
                        errors.append({"source": source, "line": number,
                                       "error": f"{type(exc).__name__}: {exc}"})
        except (OSError, UnicodeError) as exc:
            errors.append({"source": source, "error": f"{type(exc).__name__}: {exc}"})
    facts = {"sessions": list(sessions.values()), "session_messages": list(messages),
             "provider_turns": list(turns), "reader_errors": list(errors)}
    facts["braid"] = _braid_facts(run, harness)
    return facts


def _braid_facts(run: Path, harness: Path) -> dict[str, Any]:
    """Read the Braid lifecycle projection already produced in this run.

    This is observation only.  The supervisor still owns control; missing or
    stale Braid material remains unknown instead of being inferred from text
    timestamps.
    """
    observed_at = time.time()
    roots = sorted({path.parent for path in harness.rglob("braid-state/status.json")})
    result: dict[str, Any] = {"observed_at": observed_at, "sources": [],
                              "states": [], "gaps": []}
    if not roots:
        result["gaps"].append({"source": str(harness.relative_to(run)),
                                "reason": "braid-state/status.json unavailable"})
        return result
    from .provider_liveness import collect_provider_evidence
    for state_root in roots:
        status_path = state_root / "status.json"
        source = str(status_path.relative_to(run))
        row: dict[str, Any] = {"source": source, "observed_at": observed_at}
        try:
            status = json.loads(status_path.read_text(encoding="utf-8"))
            if not isinstance(status, dict):
                raise ValueError("Braid status must be an object")
            row["status"] = {key: status.get(key) for key in (
                "active_turns", "pending_batches", "pending_events",
                "pending_continuations", "pending_resets",
                "materializing_groups", "blocked_groups", "provider_health")}
            row["physical_sessions"] = status.get("physical_sessions", [])
        except (OSError, UnicodeError, ValueError) as exc:
            row["error"] = f"{type(exc).__name__}: {exc}"
            result["gaps"].append({"source": source, "reason": row["error"]})
        try:
            evidence = collect_provider_evidence(state_root, observed_at)
            row["provider_evidence"] = evidence
            if evidence.get("errors"):
                result["gaps"].extend({"source": source, "reason": error}
                                     for error in evidence["errors"])
        except (OSError, UnicodeError, ValueError) as exc:
            row["provider_evidence_error"] = f"{type(exc).__name__}: {exc}"
            result["gaps"].append({"source": source, "reason": row["provider_evidence_error"]})
        result["sources"].append(source)
        result["states"].append(row)
    result["available"] = bool(result["states"]) and not all(
        "error" in row and "provider_evidence" not in row for row in result["states"])
    return result


def _activity(run: Path, facts):
    state = manifest(run)
    if state.get("run_kind") == "evaluation":
        return {"activity": "unknown", "brief": "evaluation run",
                "last_activity_at": None,
                "evidence": {"source": "evaluation.lifecycle"}}
    script = paths(run)["program"] / "status.py"
    if not script.is_file():
        return {"activity": "unknown", "brief": "variant status script unavailable",
                "last_activity_at": None, "error": "missing program/status.py"}
    try:
        result = subprocess.run([sys.executable, str(script)], input=json.dumps(facts), text=True,
                                capture_output=True, check=True, cwd=run, timeout=10)
        value = json.loads(result.stdout)
        if not isinstance(value, dict):
            raise ValueError("status script output must be an object")
        return value
    except (OSError, subprocess.SubprocessError, ValueError) as exc:
        return {"activity": "unknown", "brief": "variant status script failed",
                "last_activity_at": None, "error": f"{type(exc).__name__}: {exc}",
                "stdout": getattr(exc, "stdout", None), "stderr": getattr(exc, "stderr", None)}


def _status_facts(run: Path, lifecycle):
    facts = {"lifecycle": lifecycle, "observed_at": time.time(), "native": _native_facts(run),
             "spend": {"value": None, "currency": None, "kind": "unknown", "source": None,
                       "as_of": time.time()}, "resource": {}, "resources": {}}
    records = paths(run)["records"]
    for name, key in (("cost.json", "spend"), ("resources.json", "resource"), ("resource-latest.json", "resource")):
        candidate = records / name
        if candidate.is_file():
            try:
                facts[key] = json.loads(candidate.read_text())
            except (OSError, ValueError) as exc:
                facts.setdefault("record_errors", []).append({"source": str(candidate.relative_to(run)),
                                    "error": f"{type(exc).__name__}: {exc}"})
    facts["resources"] = facts.get("resource", {})
    return facts


def control(run: str | os.PathLike[str], action: str) -> dict[str, Any]:
    run_path = Path(run).expanduser().resolve()
    state = manifest(run_path)
    if state.get("target_config", {}).get("kind") == "hosted":
        from . import hosted_run
        value = hosted_run.control(run_path, action)
        return _save_handle(run_path, **(value if isinstance(value, dict) else {"platform": value}))
    from . import local_run
    result = local_run.control(run_path, action)
    _save_handle(run_path, control_action=action, control_at=time.time())
    return result


def observe(run: str | os.PathLike[str]) -> dict[str, Any]:
    run_path = Path(run).expanduser().resolve()
    state = manifest(run_path)
    if state.get("target_config", {}).get("kind") == "hosted":
        from . import hosted_run
        value = hosted_run.observe(run_path)
        if isinstance(value, dict):
            lifecycle = value.get("lifecycle", "unknown")
            facts = _status_facts(run_path, lifecycle)
            activity = _activity(run_path, facts)
            spend = value.get("spend")
            if isinstance(spend, Mapping) and "value" not in spend:
                spend = {**spend, "value": spend.get("amount")}
            value = {**value, **facts, **activity,
                     "spend": spend or facts["spend"],
                     "lifecycle": lifecycle, "as_of": value.get("as_of", time.time())}
            write_json(paths(run_path)["records"] / "status.json", value)
            if state.get('lifecycle') != lifecycle:
                _save_handle(run_path, lifecycle=lifecycle)
            return value
    from . import local_run
    observed = local_run.observe(run_path)
    lifecycle = observed.get("lifecycle", "unknown")
    facts = _status_facts(run_path, lifecycle)
    facts.update(observed)
    value = {**facts, **_activity(run_path, facts), "lifecycle": lifecycle,
             "as_of": observed.get("as_of", observed.get("observed_at"))}
    write_json(paths(run_path)["records"] / "status.json", value)
    if state.get("lifecycle") != lifecycle:
        _save_handle(run_path, lifecycle=lifecycle)
    return value


def save(run: str | os.PathLike[str]) -> dict[str, Any]:
    """Save the complete data domain and report scope/gaps explicitly."""
    run_path = Path(run).expanduser().resolve()
    if manifest(run_path).get("target_config", {}).get("kind") == "hosted":
        from . import hosted_run
        value = hosted_run.save(run_path)
        value = dict(value) if isinstance(value, dict) else {"saved": False, "error": value}
        if value.get("kind") == "pre-execution-rejection":
            write_json(paths(run_path)["records"] / "save.json", value)
            return value
        # The actual template-bundle ZIP has a `template/` archive root.
        # Preserve that entire application workspace, and split the native
        # subtree back into the same data domain used by Local containers.
        exported = Path(value.get("workspace", "")) if value.get("workspace") else None
        mapped = []
        gaps = list(value.get("gaps", [])) if isinstance(value.get("gaps"), list) else []
        if exported and exported.is_dir():
            template = exported / "template"
            if not template.is_dir():
                raise FileNotFoundError(f"Hosted template-bundle has no template directory: {exported}")
            native = template / ".factory26/data/harness"
            if native.is_dir():
                shutil.copytree(native, paths(run_path)["harness"], symlinks=True, dirs_exist_ok=True)
                mapped.append("data/harness")
            else:
                gaps.append("template export has no native data subtree")
            def skip_native(directory, names):
                return ["harness"] if Path(directory) == native.parent else []
            shutil.copytree(template, paths(run_path)["workspace"], symlinks=True,
                            dirs_exist_ok=True, ignore=skip_native)
            mapped.append("data/workspace")
            # Full native history is migrated, but this run's receiver writes
            # to a distinct producer directory rather than re-importing the
            # source run's batches as newly incurred activity or expense.
            scope = manifest(run_path)["native_scope_id"]
            telemetry = paths(run_path)["harness"] / scope / "producers" / run_path.name / "telemetry.sqlite"
            if telemetry.is_file():
                import sqlite3
                from lab.otlp import connect
                with connect(telemetry, readonly=True) as source, \
                        sqlite3.connect(paths(run_path)["records"] / "telemetry.sqlite") as destination:
                    source.backup(destination)
                mapped.append("records/telemetry.sqlite")
                _import_raw(run_path, paths(run_path)['records']/'telemetry.sqlite')
            else:
                gaps.append("current run raw collector database is unavailable")
        else:
            raise FileNotFoundError("Hosted saved workspace is unavailable")
        value["scope"] = ["records", *mapped]
        value["gaps"] = gaps
        write_json(paths(run_path)["records"] / "save.json", value)
        return value
    from . import local_run
    return local_run.save(run_path)


def _import_raw(run: Path, database: Path):
    """Transfer saved Hosted raw evidence, independently of generation success."""
    from urllib.request import Request, urlopen
    from urllib.error import HTTPError
    config = manifest(run).get('observability') or {}
    if not config.get('import_host') or not config.get('import_root'):
        return
    remote = Path(config['import_root'])/run.name
    receipt = {'as_of': time.time(), 'source': str(database), 'complete': False}
    try:
        mkdir = subprocess.run(['ssh', config['import_host'],
                                shlex.join(['mkdir', '-p', str(remote)])], capture_output=True, text=True)
        if mkdir.returncode:
            raise RuntimeError(f'raw import mkdir exit={mkdir.returncode}: {mkdir.stderr}')
        copied = subprocess.run(['rsync', '-a', str(database),
                                 config['import_host']+':'+str(remote/'telemetry.sqlite')],
                                capture_output=True, text=True)
        if copied.returncode:
            raise RuntimeError(f'raw import rsync exit={copied.returncode}: {copied.stderr}')
        request = Request(config['service_url'].rstrip('/')+'/api/import',
                          data=json.dumps({'run_id': run.name, 'source': run.name}).encode(),
                          headers={'Content-Type': 'application/json'}, method='POST')
        with urlopen(request, timeout=60) as response:
            result = json.loads(response.read())
        receipt.update(result)
    except HTTPError as error:
        receipt.update(http_status=error.code, response=error.read(65536).decode(errors='replace'),
                       error=f'{type(error).__name__}: {error}')
    except Exception as error:
        receipt['error'] = f'{type(error).__name__}: {error}'
    write_json(paths(run)['records']/'raw-import.json', receipt)
