"""Application service for validate/start/emit/observe/stop double commands."""

from __future__ import annotations

import hashlib
import ipaddress
import json
import os
import re
import secrets
import sys
import tempfile
import time
import urllib.parse
from contextlib import suppress
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, cast

import urllib3
from platformdirs import user_runtime_dir
from pydantic import ValidationError

from .._execution import (
    ExecutionRecord,
    ExecutionStore,
    LaunchSpec,
    OwnedExecution,
    release_owned,
    require_execution_id,
    start_isolated,
    terminate_owned,
    wait_owned,
)
from ..errors import SvcError
from ..workspace import resolve_workspace_identity
from .compiler import compile_scenario
from .materialization import compact_json, strict_json_loads
from .model import (
    Diagnostic,
    EmitResult,
    ObserveResult,
    Replay,
    RunObservation,
    RunRecord,
    Scenario,
    StartResult,
    StopResult,
    TargetBinding,
    ValidateResult,
    ValueNode,
)


_RUNTIME_ID = "svc.double.native/v0"
_CONTROL_TIMEOUT_SECONDS = 5.0
_MAX_CONTROL_RESPONSE_BYTES = 2_097_152
_START_TIMEOUT_SECONDS = 10.0
_INSTALL_CONTINUATION = "pip install 'sustainable-vibe-coding[double]'"
_UTC_CLOCK = re.compile(
    r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z",
    re.ASCII,
)


class DoubleRunStore:
    def __init__(self, root: Path | None = None) -> None:
        base = (
            root
            or Path(user_runtime_dir("svc", ensure_exists=True)) / "double" / "runs"
        )
        self.root = base.resolve()
        _private_directory(self.root)

    def create(self, run_id: str) -> Path:
        parsed = require_execution_id(run_id)
        directory = self.root / parsed
        try:
            directory.mkdir(mode=0o700)
        except FileExistsError as error:
            raise SvcError(
                "double-run-collision", "Generated run ID already exists."
            ) from error
        except OSError as error:
            raise SvcError(
                "double-storage-failed",
                "Double run directory could not be created.",
                {"reason": str(error)},
            ) from error
        return directory

    def read_record(self, run_id: object) -> RunRecord:
        parsed = require_execution_id(run_id)
        directory = self.root / parsed
        path = directory / "record.json"
        value = _read_json(path, code="double-run-record-unreadable")
        try:
            record = RunRecord.model_validate_json(_json_bytes(value))
        except ValidationError as error:
            raise SvcError(
                "double-run-record-invalid",
                "Double run record is malformed.",
                {"path": str(path)},
            ) from error
        if (
            record.run_id != parsed
            or Path(record.run_directory) != directory
            or Path(record.manifest_path) != directory / "manifest.json"
            or Path(record.observation_path) != directory / "observation.json"
        ):
            raise SvcError(
                "double-run-record-mismatch",
                "Double run record does not match its storage identity.",
                {"run_id": parsed},
            )
        return record

    def write_record(self, record: RunRecord) -> None:
        _atomic_json(
            Path(record.run_directory) / "record.json",
            record.model_dump(mode="json"),
        )

    def read_observation(self, record: RunRecord) -> RunObservation:
        value = _read_json(
            Path(record.observation_path), code="double-observation-unreadable"
        )
        try:
            observation = RunObservation.model_validate_json(_json_bytes(value))
        except ValidationError as error:
            raise SvcError(
                "double-observation-invalid",
                "Double observation projection is malformed.",
            ) from error
        if (
            observation.run_id != record.run_id
            or observation.scenario_digest != record.scenario_digest
            or observation.run_context_digest != record.run_context_digest
        ):
            raise SvcError(
                "double-observation-mismatch",
                "Double observation does not match its run record.",
            )
        return observation


def validate_module(module: Path) -> ValidateResult:
    resolved = str(module.expanduser().resolve())
    try:
        scenario = compile_scenario(module)
    except SvcError as error:
        details = error.details
        return ValidateResult(
            module=resolved,
            valid=False,
            fidelity=(),
            nonclaims=(),
            snapshots=(),
            diagnostic=Diagnostic(
                code=error.code,
                message=error.message,
                path=_diagnostic_path(details.get("path")),
                line=_optional_int(details.get("line")),
                column=_optional_int(details.get("column")),
            ),
        )
    return ValidateResult(
        module=scenario.module_path,
        scenario_name=scenario.name,
        claim=scenario.claim,
        valid=True,
        scenario_digest=scenario.scenario_digest,
        fidelity=scenario.fidelity,
        nonclaims=scenario.nonclaims,
        snapshots=scenario.snapshots,
    )


def start_run(
    module: Path,
    *,
    seed: int | None,
    clock: str | None,
    target_values: tuple[str, ...],
    allow_remote_names: tuple[str, ...],
    run_root: Path | None = None,
    execution_root: Path | None = None,
) -> StartResult:
    scenario = compile_scenario(module)
    replay = _replay(scenario, seed=seed, clock=clock)
    targets = _targets(scenario, target_values, allow_remote_names)
    run_context_digest = _digest(
        {
            "scenario_digest": scenario.scenario_digest,
            "targets": [item.model_dump(mode="json") for item in targets],
            "replay": replay.model_dump(mode="json"),
            "snapshot_hashes": [item.sha256 for item in scenario.snapshots],
        }
    )
    import uuid

    run_id = str(uuid.uuid4())
    store = DoubleRunStore(run_root)
    run_directory = store.create(run_id)
    capability = secrets.token_urlsafe(48)
    manifest = {
        "schema_version": 1,
        "run_id": run_id,
        "scenario": scenario.model_dump(mode="json"),
        "replay": replay.model_dump(mode="json"),
        "run_context_digest": run_context_digest,
        "targets": [item.model_dump(mode="json") for item in targets],
        "control_capability": capability,
    }
    _atomic_json(run_directory / "manifest.json", manifest)

    workspace = resolve_workspace_identity(Path(scenario.workspace_root))
    execution_store = ExecutionStore(execution_root)
    coordination_key = hashlib.sha256(f"double\0{run_id}".encode()).hexdigest()
    argv = (
        sys.executable,
        "-m",
        "svc_cli.double.carrier",
        "--run-directory",
        str(run_directory),
    )
    published = execution_store.publish(
        domain="double",
        operation="carrier",
        subject=run_id,
        workspace_instance=workspace.instance,
        intent_digest=run_context_digest,
        coordination_key=coordination_key,
        argv=argv,
        cwd=Path(scenario.workspace_root),
        capture="merged",
    )
    started = start_isolated(
        execution_store,
        published,
        LaunchSpec(argv=argv, cwd=Path(scenario.workspace_root), env=dict(os.environ)),
    )
    if isinstance(started, ExecutionRecord):
        raise SvcError(
            "double-carrier-launch-failed",
            "Double carrier could not be launched.",
            {"reason": started.failure_reason or "unknown"},
        )
    launch_released = False
    try:
        bootstrap = _wait_for_bootstrap(run_directory, started, execution_store)
        control_url = _required_url(bootstrap.get("control_url"), "control")
        responder_url = _required_url(bootstrap.get("responder_url"), "responder")
        if (
            bootstrap.get("run_id") != run_id
            or bootstrap.get("scenario_digest") != scenario.scenario_digest
            or bootstrap.get("run_context_digest") != run_context_digest
        ):
            raise SvcError(
                "double-carrier-readiness-invalid",
                "Double carrier bootstrap does not match the run.",
            )
        ready = _control_request(
            control_url,
            capability,
            "/v1/ready",
            payload=None,
            unavailable_is_result=False,
        )
        assert ready is not None
        if (
            ready.get("run_id") != run_id
            or ready.get("scenario_digest") != scenario.scenario_digest
            or ready.get("run_context_digest") != run_context_digest
            or ready.get("responder_url") != responder_url
        ):
            raise SvcError(
                "double-carrier-readiness-invalid",
                "Authenticated carrier readiness does not match the run.",
            )
        released = release_owned(execution_store, started)
        if released.state != "released":
            raise SvcError(
                "double-carrier-exited",
                "Double carrier exited before launch authority was released.",
            )
        launch_released = True
        record = RunRecord(
            run_id=run_id,
            workspace_root=scenario.workspace_root,
            workspace_instance=workspace.instance,
            run_directory=str(run_directory),
            manifest_path=str(run_directory / "manifest.json"),
            scenario_digest=scenario.scenario_digest,
            run_context_digest=run_context_digest,
            replay=replay,
            targets=targets,
            control_url=control_url,
            control_capability=capability,
            observation_path=str(run_directory / "observation.json"),
            created_at=_now(),
        )
        try:
            store.write_record(record)
        except BaseException:
            _control_request(
                control_url,
                capability,
                "/v1/stop",
                payload=None,
                unavailable_is_result=True,
            )
            raise
    except BaseException:
        if not launch_released and started.process.poll() is None:
            terminate_owned(execution_store, started)
        raise
    return StartResult(
        run_id=run_id,
        module=scenario.module_path,
        scenario_name=scenario.name,
        responder_url=responder_url,
        scenario_digest=scenario.scenario_digest,
        run_context_digest=run_context_digest,
        replay=replay,
        targets=targets,
        nonclaims=scenario.nonclaims,
    )


def emit_event(
    run_id: str,
    event: str,
    *,
    run_root: Path | None = None,
) -> EmitResult:
    store = DoubleRunStore(run_root)
    record = store.read_record(run_id)
    projection = store.read_observation(record)
    if projection.sealed:
        return EmitResult(
            run_id=record.run_id,
            event=event,
            status="not-acknowledged",
            reason="run is stopped",
        )
    response = _control_request(
        record.control_url,
        record.control_capability,
        "/v1/emit",
        payload={"event": event},
        unavailable_is_result=True,
    )
    if response is None:
        latest = store.read_observation(record)
        if latest.sealed:
            return EmitResult(
                run_id=record.run_id,
                event=event,
                status="not-acknowledged",
                reason="run is stopped",
            )
        return EmitResult(
            run_id=record.run_id,
            event=event,
            status="control-unavailable",
            reason="active run control is unavailable",
        )
    if "error" in response:
        error = response["error"]
        reason = (
            error.get("code") if isinstance(error, dict) else "control-operation-failed"
        )
        return EmitResult(
            run_id=record.run_id,
            event=event,
            status="not-acknowledged",
            reason=str(reason),
        )
    try:
        result = EmitResult.model_validate_json(_json_bytes(response["result"]))
    except (KeyError, ValidationError) as error:
        raise SvcError(
            "double-control-protocol-invalid",
            "Carrier emit response is malformed.",
        ) from error
    return result.model_copy(update={"run_id": record.run_id})


def observe_run(run_id: str, *, run_root: Path | None = None) -> ObserveResult:
    store = DoubleRunStore(run_root)
    record = store.read_record(run_id)
    projection = store.read_observation(record)
    if projection.sealed:
        return ObserveResult(
            observation=projection,
            authority="sealed-snapshot",
            control_status="not-required",
        )
    response = _control_request(
        record.control_url,
        record.control_capability,
        "/v1/observe",
        payload=None,
        unavailable_is_result=True,
    )
    if response is None:
        latest = store.read_observation(record)
        if latest.sealed:
            return ObserveResult(
                observation=latest,
                authority="sealed-snapshot",
                control_status="not-required",
            )
        return ObserveResult(
            observation=latest,
            authority="unsealed-projection",
            control_status="control-unavailable",
        )
    observation = _control_observation(response, record)
    if observation.sealed:
        return ObserveResult(
            observation=observation,
            authority="sealed-snapshot",
            control_status="not-required",
        )
    return ObserveResult(
        observation=observation,
        authority="active-carrier",
        control_status="available",
    )


def stop_run(run_id: str, *, run_root: Path | None = None) -> StopResult:
    store = DoubleRunStore(run_root)
    record = store.read_record(run_id)
    projection = store.read_observation(record)
    if projection.sealed:
        return StopResult(
            run_id=record.run_id,
            status="stopped",
            sealed=True,
            idempotent=True,
            observation=projection,
        )
    response = _control_request(
        record.control_url,
        record.control_capability,
        "/v1/stop",
        payload=None,
        unavailable_is_result=True,
    )
    if response is None:
        latest = store.read_observation(record)
        if latest.sealed:
            return StopResult(
                run_id=record.run_id,
                status="stopped",
                sealed=True,
                idempotent=True,
                observation=latest,
            )
        return StopResult(
            run_id=record.run_id,
            status="control-unavailable",
            sealed=False,
            idempotent=False,
            observation=latest,
        )
    observation = _control_observation(response, record)
    if not observation.sealed or observation.status != "stopped":
        raise SvcError(
            "double-control-protocol-invalid",
            "Carrier stop did not return a sealed stopped observation.",
        )
    return StopResult(
        run_id=record.run_id,
        status="stopped",
        sealed=True,
        idempotent=False,
        observation=observation,
    )


def install_continuation() -> str:
    return _INSTALL_CONTINUATION


def _replay(scenario: Scenario, *, seed: int | None, clock: str | None) -> Replay:
    selected_seed = secrets.randbits(64) if seed is None else seed
    if type(selected_seed) is not int or not 0 <= selected_seed <= (2**64 - 1):
        raise SvcError(
            "double-seed-invalid", "Seed must be an unsigned 64-bit integer."
        )
    selected_clock = _now() if clock is None else clock
    if not _utc_clock(selected_clock):
        raise SvcError(
            "double-clock-invalid",
            "Clock must be an RFC3339 UTC value ending in Z.",
        )
    generators = sorted(
        {
            node.using
            for node in _all_nodes(scenario)
            if node.kind == "generated" and node.using is not None
        }
    )
    validators = sorted(
        {
            node.validator.using
            for node in _all_nodes(scenario)
            if node.validator is not None and node.validator.using is not None
        }
        | {
            node.matcher.using
            for node in _all_nodes(scenario)
            if node.matcher is not None and node.matcher.using is not None
        }
    )
    return Replay(
        seed=selected_seed,
        clock=selected_clock,
        generators=tuple(cast(list[str], generators)),
        validators=tuple(cast(list[str], validators)),
        runtime=_RUNTIME_ID,
    )


def _all_nodes(scenario: Scenario) -> tuple[ValueNode, ...]:
    nodes: list[ValueNode] = []
    for interaction in scenario.interactions:
        request = interaction.request
        nodes.extend(request.query_nodes)
        nodes.extend(request.header_nodes)
        if request.body is not None:
            nodes.extend(request.body.nodes)
        nodes.extend(interaction.response.header_nodes)
        if interaction.response.body is not None:
            nodes.extend(interaction.response.body.nodes)
    for event in scenario.events:
        nodes.extend(event.request.query_nodes)
        nodes.extend(event.request.header_nodes)
        if event.request.body is not None:
            nodes.extend(event.request.body.nodes)
    return tuple(nodes)


def _targets(
    scenario: Scenario,
    values: tuple[str, ...],
    allowed_remote: tuple[str, ...],
) -> tuple[TargetBinding, ...]:
    parsed: dict[str, TargetBinding] = {}
    for value in values:
        name, separator, origin = value.partition("=")
        if not separator or not name or name in parsed:
            raise SvcError(
                "double-target-invalid",
                "Each target must be one unique NAME=ORIGIN binding.",
                {"target": value},
            )
        normalized, remote = _origin(origin)
        parsed[name] = TargetBinding(name=name, origin=normalized, remote=remote)
    declared = {event.target for event in scenario.events}
    supplied = set(parsed)
    if supplied != declared:
        raise SvcError(
            "double-target-set-invalid",
            "Start target names must exactly match declared event targets.",
            {
                "missing": sorted(declared - supplied),
                "unused": sorted(supplied - declared),
            },
        )
    allowed = set(allowed_remote)
    if len(allowed) != len(allowed_remote) or not allowed <= supplied:
        raise SvcError(
            "double-remote-target-opt-in-invalid",
            "Remote target opt-ins must name unique supplied targets.",
            {"unused": sorted(allowed - supplied)},
        )
    remote_names = {name for name, binding in parsed.items() if binding.remote}
    if remote_names:
        if scenario.event_target_policy != "explicit-remote" or remote_names != allowed:
            raise SvcError(
                "double-remote-target-not-authorized",
                "Remote delivery requires module policy and matching command opt-in.",
                {"remote": sorted(remote_names), "allowed": sorted(allowed)},
            )
    elif allowed:
        raise SvcError(
            "double-remote-target-opt-in-unused",
            "Remote target opt-in was supplied for a loopback target.",
        )
    return tuple(parsed[name] for name in sorted(parsed))


def _origin(value: str) -> tuple[str, bool]:
    try:
        parsed = urllib.parse.urlsplit(value)
        port = parsed.port
    except ValueError as error:
        raise SvcError(
            "double-target-origin-invalid", "Target origin is invalid."
        ) from error
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or parsed.path not in {"", "/"}
    ):
        raise SvcError(
            "double-target-origin-invalid",
            "Target binding must be an HTTP(S) origin without userinfo, path, query, or fragment.",
        )
    try:
        address = ipaddress.ip_address(parsed.hostname)
    except ValueError:
        remote = True
    else:
        remote = not address.is_loopback
    host = parsed.hostname
    assert host is not None
    if ":" in host:
        host = f"[{host}]"
    default = (parsed.scheme == "http" and port in {None, 80}) or (
        parsed.scheme == "https" and port in {None, 443}
    )
    normalized = f"{parsed.scheme}://{host}" + ("" if default else f":{port}")
    return normalized, remote


def _wait_for_bootstrap(
    run_directory: Path,
    owned: OwnedExecution,
    execution_store: ExecutionStore,
) -> dict[str, Any]:
    deadline = time.monotonic() + _START_TIMEOUT_SECONDS
    path = run_directory / "bootstrap.json"
    while time.monotonic() < deadline:
        if path.exists():
            value = _read_json(path, code="double-carrier-readiness-invalid")
            if not isinstance(value, dict):
                raise SvcError(
                    "double-carrier-readiness-invalid",
                    "Carrier bootstrap is malformed.",
                )
            return cast(dict[str, Any], value)
        if owned.process.poll() is not None:
            settled = wait_owned(execution_store, owned)
            raise SvcError(
                "double-carrier-exited",
                "Double carrier exited before readiness.",
                {"exit_code": None if settled is None else settled.exit_code},
            )
        time.sleep(0.05)
    terminate_owned(execution_store, owned)
    raise SvcError(
        "double-carrier-readiness-timeout", "Double carrier did not become ready."
    )


def _control_request(
    origin: str,
    capability: str,
    path: str,
    *,
    payload: dict[str, Any] | None,
    unavailable_is_result: bool,
) -> dict[str, Any] | None:
    manager = urllib3.PoolManager(retries=False)
    raw = None if payload is None else compact_json(cast(Any, payload))
    try:
        response = manager.request(
            "POST",
            origin + path,
            body=raw,
            headers={
                "Authorization": f"Bearer {capability}",
                **({} if raw is None else {"Content-Type": "application/json"}),
            },
            redirect=False,
            retries=False,
            timeout=urllib3.Timeout(total=_CONTROL_TIMEOUT_SECONDS),
            preload_content=False,
        )
    except urllib3.exceptions.HTTPError as error:
        if unavailable_is_result:
            return None
        raise SvcError(
            "double-control-unavailable",
            "Double carrier control is unavailable during startup.",
            {"reason": str(error)},
        ) from error
    status = response.status
    try:
        data = response.read(_MAX_CONTROL_RESPONSE_BYTES + 1)
    except urllib3.exceptions.HTTPError as error:
        if unavailable_is_result:
            return None
        raise SvcError(
            "double-control-unavailable",
            "Double carrier control response could not be read during startup.",
            {"reason": str(error)},
        ) from error
    finally:
        response.close()
    if len(data) > _MAX_CONTROL_RESPONSE_BYTES:
        raise SvcError(
            "double-control-protocol-invalid",
            "Double carrier control response exceeds its byte bound.",
        )
    if status not in {200, 409}:
        if unavailable_is_result and status in {401, 403, 404, 410, 503}:
            return None
        raise SvcError(
            "double-control-protocol-invalid",
            "Double carrier returned an unexpected control status.",
            {"status": status},
        )
    value = strict_json_loads(data, code="double-control-protocol-invalid")
    if not isinstance(value, dict):
        raise SvcError(
            "double-control-protocol-invalid", "Control response is not an object."
        )
    return cast(dict[str, Any], value)


def _control_observation(value: dict[str, Any], record: RunRecord) -> RunObservation:
    try:
        observation = RunObservation.model_validate_json(
            _json_bytes(value["observation"])
        )
    except (KeyError, ValidationError) as error:
        raise SvcError(
            "double-control-protocol-invalid",
            "Carrier observation response is malformed.",
        ) from error
    if (
        observation.run_id != record.run_id
        or observation.scenario_digest != record.scenario_digest
        or observation.run_context_digest != record.run_context_digest
    ):
        raise SvcError(
            "double-control-protocol-invalid",
            "Carrier observation response does not match the run.",
        )
    return observation


def _read_json(path: Path, *, code: str) -> Any:
    try:
        raw = path.read_bytes()
    except FileNotFoundError as error:
        raise SvcError(
            code, "Required double runtime state is absent.", {"path": str(path)}
        ) from error
    except OSError as error:
        raise SvcError(
            code, "Double runtime state could not be read.", {"path": str(path)}
        ) from error
    return strict_json_loads(raw, code=code)


def _atomic_json(path: Path, value: Any) -> None:
    _private_directory(path.parent)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            descriptor = -1
            json.dump(
                value,
                stream,
                ensure_ascii=False,
                allow_nan=False,
                separators=(",", ":"),
                sort_keys=True,
            )
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except OSError as error:
        raise SvcError(
            "double-storage-failed",
            "Double runtime state could not be written.",
            {"path": str(path), "reason": str(error)},
        ) from error
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        with suppress(FileNotFoundError):
            os.unlink(temporary)


def _private_directory(path: Path) -> None:
    try:
        path.mkdir(mode=0o700, parents=True, exist_ok=True)
        if os.name != "nt":
            path.chmod(0o700)
    except OSError as error:
        raise SvcError(
            "double-storage-failed",
            "Double runtime directory is unavailable.",
            {"path": str(path), "reason": str(error)},
        ) from error


def _digest(value: Any) -> str:
    return hashlib.sha256(compact_json(cast(Any, value))).hexdigest()


def _json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _required_url(value: Any, kind: str) -> str:
    if not isinstance(value, str) or not value.startswith("http://127.0.0.1:"):
        raise SvcError(
            "double-carrier-readiness-invalid",
            f"Carrier {kind} URL is not numeric loopback HTTP.",
        )
    return value


def _utc_clock(value: str) -> bool:
    if not _UTC_CLOCK.fullmatch(value):
        return False
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        return False
    return parsed.tzinfo == timezone.utc


def _now() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


def _optional_string(value: Any) -> str | None:
    return value if isinstance(value, str) else None


def _diagnostic_path(value: Any) -> str | None:
    if isinstance(value, str):
        return value
    if not isinstance(value, list) or not all(
        isinstance(part, (str, int)) and not isinstance(part, bool) for part in value
    ):
        return None
    escaped = (str(part).replace("~", "~0").replace("/", "~1") for part in value)
    return "/" + "/".join(escaped)


def _optional_int(value: Any) -> int | None:
    return value if type(value) is int else None
