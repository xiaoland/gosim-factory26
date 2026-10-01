"""Dev capability coordination over neutral private process attempts."""

from __future__ import annotations

import hashlib
import json
import os
import signal
import threading
import time
from contextlib import contextmanager, suppress
from pathlib import Path
from typing import Callable, Iterator, Literal, TypeAlias

from filelock import BaseFileLock, Timeout

from .._execution import (
    ACTIVE_STATES,
    ExecutionRecord,
    ExecutionState,
    ExecutionStore,
    LaunchSpec,
    OwnedExecution,
    mark_owner_lost,
    reconcile_owner_loss,
    release_owned,
    start_isolated,
    terminate_owned,
    wait_execution,
    wait_owned,
)
from ..config import (
    ConfigError,
    ExecProvision,
    ExecStop,
    ManualProvision,
    ManualStop,
    TargetConfig,
    load_config,
)
from ..errors import Failure, SvcError
from ..model import ValueModel
from ..workspace import WorkspaceIdentity, resolve_workspace_identity
from .identity import (
    CapabilityIdentity,
    interpolate_dev_argv,
    interpolate_dev_value,
    resolve_capability_identity,
)
from .readiness import (
    ProbeObservation,
    probe_target,
    resolve_dev_cwd,
    resolve_probe,
)


DevSelectedCallback = Callable[[ExecutionRecord, str, str], None]
DevEnsureStatus: TypeAlias = (
    ExecutionState
    | Literal[
        "reused",
        "manual-action-required",
        "lock-timeout",
        "activation-timeout",
        "activation-failed",
        "started",
        "readiness-timeout",
        "child-exit",
        "joined",
        "conflict",
        "waiting",
    ]
)


class DevLogReference(ValueModel):
    path: str
    bytes: int


class DevMergedLogs(ValueModel):
    merged: DevLogReference


class DevAttempt(ValueModel):
    caller_role: Literal["owner", "follower"]
    execution_id: str
    state: ExecutionState
    argv: tuple[str, ...]
    cwd: str
    logs: DevMergedLogs
    duration_ms: int | None = None
    exit_code: int | None = None
    requested_signal: str | None = None
    termination_signal: str | None = None
    failure_reason: str | None = None
    timed_out: bool | None = None


class ManualProvisionSummary(ValueModel):
    kind: Literal["manual"] = "manual"


class ExecProvisionSummary(ValueModel):
    kind: Literal["exec"] = "exec"
    mode: Literal["run", "activate"]


DevProvisionSummary: TypeAlias = ManualProvisionSummary | ExecProvisionSummary


class DevStopDeclaration(ValueModel):
    kind: Literal["absent", "manual", "exec"]


class DevIdentityResult(ValueModel):
    workspace: WorkspaceIdentity


class DevTargetObservation(ValueModel):
    target: str
    effective_target_digest: str
    capability: CapabilityIdentity
    probe: ProbeObservation
    access: tuple[str, ...]
    provision: DevProvisionSummary
    continuation: (
        Literal["blocked-unhealthy-responder", "manual-action-required", "ensure"]
        | None
    ) = None
    probe_argv: tuple[str, ...] | None = None


class DevTargetFailure(ValueModel):
    target: str
    effective_target_digest: str
    error: Failure


DevTargetStatus: TypeAlias = DevTargetObservation | DevTargetFailure


class DevStatusResult(ValueModel):
    healthy: bool
    status: Literal[
        "healthy", "action-required", "invalid-configuration", "not-configured"
    ]
    workspace: WorkspaceIdentity
    reason: str | None = None
    targets: tuple[DevTargetStatus, ...] | None = None


class DevEnsureContext(ValueModel):
    target: str
    ready: bool
    effective_target_digest: str
    workspace: WorkspaceIdentity
    capability: CapabilityIdentity
    access: tuple[str, ...]
    provision: DevProvisionSummary
    probe: ProbeObservation
    probe_argv: tuple[str, ...] | None = None

    def result(
        self,
        status: DevEnsureStatus,
        *,
        ready: bool | None = None,
        probe: ProbeObservation | None = None,
        attempt: DevAttempt | None = None,
        caller_status: Literal["detached"] | None = None,
        cleanup: Literal["completed", "unknown"] | None = None,
        execution_id: str | None = None,
    ) -> "DevEnsureResult":
        return DevEnsureResult(
            target=self.target,
            ready=self.ready if ready is None else ready,
            status=status,
            effective_target_digest=self.effective_target_digest,
            workspace=self.workspace,
            capability=self.capability,
            access=self.access,
            provision=self.provision,
            probe=self.probe if probe is None else probe,
            probe_argv=self.probe_argv,
            attempt=attempt,
            caller_status=caller_status,
            cleanup=cleanup,
            execution_id=execution_id,
        )


class DevEnsureResult(ValueModel):
    target: str
    ready: bool | None
    status: DevEnsureStatus
    effective_target_digest: str
    workspace: WorkspaceIdentity
    capability: CapabilityIdentity
    access: tuple[str, ...]
    provision: DevProvisionSummary
    probe: ProbeObservation | None = None
    probe_argv: tuple[str, ...] | None = None
    attempt: DevAttempt | None = None
    caller_status: Literal["detached"] | None = None
    cleanup: Literal["completed", "unknown"] | None = None
    execution_id: str | None = None


class DevStopResult(ValueModel):
    target: str
    effective_target_digest: str
    workspace: WorkspaceIdentity
    capability: CapabilityIdentity
    stop: DevStopDeclaration
    status: Literal[
        "manual-action-required",
        "waiting",
        "stop-failed",
        "stop-unverified",
        "still-ready",
        "stopped",
    ]
    ready: bool | None
    probe: ProbeObservation | None = None
    probe_error: Failure | None = None
    caller_status: Literal["detached", "interrupted"] | None = None
    attempt: DevAttempt | None = None

    def with_attempt(self, attempt: DevAttempt) -> "DevStopResult":
        return DevStopResult(
            target=self.target,
            effective_target_digest=self.effective_target_digest,
            workspace=self.workspace,
            capability=self.capability,
            stop=self.stop,
            status=self.status,
            ready=self.ready,
            probe=self.probe,
            probe_error=self.probe_error,
            caller_status=self.caller_status,
            attempt=attempt,
        )

    def with_caller_status(
        self, caller_status: Literal["detached", "interrupted"]
    ) -> "DevStopResult":
        return DevStopResult(
            target=self.target,
            effective_target_digest=self.effective_target_digest,
            workspace=self.workspace,
            capability=self.capability,
            stop=self.stop,
            status=self.status,
            ready=self.ready,
            probe=self.probe,
            probe_error=self.probe_error,
            caller_status=caller_status,
            attempt=self.attempt,
        )


class _SettledEnsure(Exception):
    """Private unwind signal for an expected ensure result."""

    def __init__(self, result: DevEnsureResult) -> None:
        super().__init__(result.status)
        self.result = result


def ensure_target(
    repo: Path,
    target_name: str,
    *,
    namespace: str | None = None,
    store: ExecutionStore | None = None,
    on_selected: DevSelectedCallback | None = None,
) -> DevEnsureResult:
    """Ensure one capability without taking over an unowned process."""

    try:
        resolved = load_config(repo)
    except ConfigError as error:
        raise SvcError(
            "invalid-project-configuration",
            "Cannot load declared dev configuration.",
            {"reason": str(error)},
        ) from error
    if resolved.effective.dev is None:
        raise SvcError(
            "dev-not-configured", "This project has no declared dev configuration."
        )
    targets = resolved.effective.dev.targets
    if target_name not in targets:
        raise SvcError(
            "unknown-dev-target",
            "The dev configuration has no such target.",
            {"target": target_name, "available_targets": sorted(targets)},
        )
    target = targets[target_name]
    workspace = resolve_workspace_identity(repo, namespace=namespace)
    resolved_probe = resolve_probe(target, workspace, target_name=target_name)
    identity = resolve_capability_identity(
        workspace,
        scope=target.scope,
        target=target_name,
        endpoint_identity=resolved_probe.endpoint_identity,
        host_key=target.host_key,
    )
    target_digest = _effective_target_digest(target)
    intent_digest = _ensure_intent_digest(target, identity)
    deadline = time.monotonic() + target.readiness_timeout
    authority = store or ExecutionStore()
    lock = authority.coordination_lock("dev", identity.capability_id)
    pointer_before = authority.read_coordination("dev", identity.capability_id)
    pointer_before_active = (
        pointer_before is not None
        and _same_dev_intent(
            authority.read(pointer_before), "ensure", target_name, intent_digest
        )
        and authority.read(pointer_before).state in ACTIVE_STATES
    )
    try:
        try:
            lock.acquire(timeout=0)
        except Timeout:
            return _join_dev_attempt(
                authority,
                lock,
                pointer_before,
                pointer_before_active,
                target,
                workspace,
                target_name,
                identity,
                target_digest,
                intent_digest,
                deadline,
                on_selected,
            )
        try:
            return _ensure_under_lock(
                authority,
                target,
                workspace,
                target_name,
                identity,
                target_digest,
                intent_digest,
                deadline,
                on_selected,
            )
        finally:
            lock.release()
    except _SettledEnsure as settled:
        return settled.result


def stop_target(
    repo: Path,
    target_name: str,
    *,
    namespace: str | None = None,
    store: ExecutionStore | None = None,
    on_selected: DevSelectedCallback | None = None,
) -> DevStopResult:
    """Run only the target's declared bounded stop action."""

    try:
        resolved = load_config(repo)
    except ConfigError as error:
        raise SvcError(
            "invalid-project-configuration",
            "Cannot load declared dev configuration.",
            {"reason": str(error)},
        ) from error
    if resolved.effective.dev is None:
        raise SvcError(
            "dev-not-configured", "This project has no declared dev configuration."
        )
    targets = resolved.effective.dev.targets
    if target_name not in targets:
        raise SvcError(
            "unknown-dev-target",
            "The dev configuration has no such target.",
            {"target": target_name, "available_targets": sorted(targets)},
        )
    target = targets[target_name]
    workspace = resolve_workspace_identity(repo, namespace=namespace)
    resolved_probe = resolve_probe(target, workspace, target_name=target_name)
    identity = resolve_capability_identity(
        workspace,
        scope=target.scope,
        target=target_name,
        endpoint_identity=resolved_probe.endpoint_identity,
        host_key=target.host_key,
    )
    target_digest = _effective_target_digest(target)
    intent_digest = _stop_intent_digest(target, identity)
    authority = store or ExecutionStore()
    lock = authority.coordination_lock("dev", identity.capability_id)
    pointer_before = authority.read_coordination("dev", identity.capability_id)
    pointer_before_active = (
        pointer_before is not None
        and _same_dev_intent(
            authority.read(pointer_before), "stop", target_name, intent_digest
        )
        and authority.read(pointer_before).state in ACTIVE_STATES
    )
    try:
        lock.acquire(timeout=0)
    except Timeout:
        return _join_or_claim_stop(
            authority,
            lock,
            pointer_before,
            pointer_before_active,
            target,
            workspace,
            target_name,
            identity,
            target_digest,
            intent_digest,
            on_selected,
        )
    try:
        current_id = authority.read_coordination("dev", identity.capability_id)
        if current_id is not None:
            current = authority.read(current_id)
            if current.state in ACTIVE_STATES:
                current = mark_owner_lost(authority, current)
            if _same_dev_intent(current, "stop", target_name, intent_digest):
                return _stop_result(
                    target,
                    workspace,
                    target_name,
                    identity,
                    target_digest,
                    current,
                    authority,
                    caller_role="follower",
                )
        return _own_stop(
            authority,
            target,
            workspace,
            target_name,
            identity,
            target_digest,
            intent_digest,
            on_selected,
        )
    finally:
        lock.release()


def inspect_dev_identity(
    repo: Path, *, namespace: str | None = None
) -> DevIdentityResult:
    workspace = resolve_workspace_identity(repo, namespace=namespace)
    return DevIdentityResult(workspace=workspace)


def inspect_dev_status(
    repo: Path,
    target_name: str | None = None,
    *,
    namespace: str | None = None,
) -> DevStatusResult:
    workspace = resolve_workspace_identity(repo, namespace=namespace)
    try:
        resolved = load_config(repo)
    except ConfigError as error:
        return DevStatusResult(
            healthy=False,
            status="invalid-configuration",
            reason=str(error),
            workspace=workspace,
        )
    if resolved.effective.dev is None:
        return DevStatusResult(
            healthy=False,
            status="not-configured",
            workspace=workspace,
        )
    targets = resolved.effective.dev.targets
    names = (target_name,) if target_name is not None else tuple(sorted(targets))
    entries: list[DevTargetStatus] = []
    for name in names:
        target = targets.get(name)
        if target is None:
            raise SvcError(
                "unknown-dev-target",
                "The dev configuration has no such target.",
                {"target": name},
            )
        try:
            resolved_probe = resolve_probe(target, workspace, target_name=name)
            observed = probe_target(target, workspace, target_name=name)
            identity = resolve_capability_identity(
                workspace,
                scope=target.scope,
                target=name,
                endpoint_identity=resolved_probe.endpoint_identity,
                host_key=target.host_key,
            )
            entry = DevTargetObservation(
                target=name,
                effective_target_digest=_effective_target_digest(target),
                capability=identity,
                probe=observed,
                access=tuple(
                    interpolate_dev_value(value, workspace, target=name)
                    for value in target.access
                ),
                provision=_provision_projection(target),
                continuation=_dev_continuation(target, observed),
                probe_argv=resolved_probe.argv,
            )
            entries.append(entry)
        except SvcError as error:
            entries.append(
                DevTargetFailure(
                    target=name,
                    effective_target_digest=_effective_target_digest(target),
                    error=error.snapshot(),
                )
            )
    healthy = bool(entries) and all(_entry_is_healthy(entry) for entry in entries)
    return DevStatusResult(
        status="healthy" if healthy else "action-required",
        healthy=healthy,
        workspace=workspace,
        targets=tuple(entries),
    )


def _join_or_claim_stop(
    store: ExecutionStore,
    lock: BaseFileLock,
    pointer_before: str | None,
    pointer_before_active: bool,
    target: TargetConfig,
    workspace: WorkspaceIdentity,
    target_name: str,
    identity: CapabilityIdentity,
    target_digest: str,
    intent_digest: str,
    on_selected: DevSelectedCallback | None,
) -> DevStopResult:
    while True:
        current_id = store.read_coordination("dev", identity.capability_id)
        if current_id is not None:
            current = store.read(current_id)
            if _same_dev_intent(current, "stop", target_name, intent_digest) and (
                current.state in ACTIVE_STATES
                or current_id != pointer_before
                or pointer_before_active
            ):
                _notify_dev_selected(store, current, "follower", on_selected)
                try:
                    settled = wait_execution(store, current.execution_id)
                except KeyboardInterrupt:
                    return _detached_stop_result(
                        target,
                        workspace,
                        target_name,
                        identity,
                        target_digest,
                        current,
                        store,
                    )
                return _stop_result(
                    target,
                    workspace,
                    target_name,
                    identity,
                    target_digest,
                    settled,
                    store,
                    caller_role="follower",
                )
        try:
            lock.acquire(timeout=0)
        except Timeout:
            time.sleep(0.02)
            continue
        try:
            after = store.read_coordination("dev", identity.capability_id)
            if after is not None and after != pointer_before:
                record = store.read(after)
                if _same_dev_intent(record, "stop", target_name, intent_digest):
                    if record.state in ACTIVE_STATES:
                        record = mark_owner_lost(store, record)
                    return _stop_result(
                        target,
                        workspace,
                        target_name,
                        identity,
                        target_digest,
                        record,
                        store,
                        caller_role="follower",
                    )
            if pointer_before is not None and pointer_before_active:
                record = store.read(pointer_before)
                if _same_dev_intent(record, "stop", target_name, intent_digest):
                    if record.state in ACTIVE_STATES:
                        record = mark_owner_lost(store, record)
                    return _stop_result(
                        target,
                        workspace,
                        target_name,
                        identity,
                        target_digest,
                        record,
                        store,
                        caller_role="follower",
                    )
            return _own_stop(
                store,
                target,
                workspace,
                target_name,
                identity,
                target_digest,
                intent_digest,
                on_selected,
            )
        finally:
            lock.release()


def _own_stop(
    store: ExecutionStore,
    target: TargetConfig,
    workspace: WorkspaceIdentity,
    target_name: str,
    identity: CapabilityIdentity,
    target_digest: str,
    intent_digest: str,
    on_selected: DevSelectedCallback | None,
) -> DevStopResult:
    action = target.stop
    if action is None or isinstance(action, ManualStop):
        observed, probe_error = _final_probe(target, workspace, target_name)
        return _stop_payload(
            target_name,
            workspace,
            identity,
            target_digest,
            status="manual-action-required",
            ready=observed.healthy if observed is not None else None,
            stop_kind="manual" if isinstance(action, ManualStop) else "absent",
            probe=observed,
            probe_error=probe_error,
        )
    assert isinstance(action, ExecStop)
    argv = interpolate_dev_argv(action.argv, workspace, target=target_name)
    cwd = resolve_dev_cwd(workspace.root, action.cwd, workspace, target_name)
    environment = _dev_environment(action.env, workspace, target_name)
    published = store.publish(
        domain="dev",
        operation="stop",
        subject=target_name,
        workspace_instance=workspace.instance,
        intent_digest=intent_digest,
        coordination_key=identity.capability_id,
        argv=argv,
        cwd=cwd,
        capture="merged",
    )
    store.write_coordination(
        "dev", identity.capability_id, published.record.execution_id
    )
    _notify_dev_selected(store, published.record, "owner", on_selected)
    started = start_isolated(store, published, LaunchSpec(argv, cwd, environment))
    if isinstance(started, ExecutionRecord):
        raise SvcError(
            "execution-launch-failed",
            "SVC could not launch the declared stop action.",
            {
                "execution_id": started.execution_id,
                "reason": started.failure_reason or "unknown",
                "logs": {"merged": store.log_reference(started, "merged").as_dict()},
            },
        )
    try:
        settled = wait_owned(store, started, timeout=action.timeout)
    except KeyboardInterrupt:
        settled = terminate_owned(store, started, requested_signal=signal.SIGINT)
        result = _stop_result(
            target,
            workspace,
            target_name,
            identity,
            target_digest,
            settled,
            store,
            caller_role="owner",
        )
        return result.with_caller_status("interrupted")
    if settled is None:
        settled = terminate_owned(store, started)
        return _stop_result(
            target,
            workspace,
            target_name,
            identity,
            target_digest,
            settled,
            store,
            caller_role="owner",
            timed_out=True,
        )
    return _stop_result(
        target,
        workspace,
        target_name,
        identity,
        target_digest,
        settled,
        store,
        caller_role="owner",
    )


def _stop_result(
    target: TargetConfig,
    workspace: WorkspaceIdentity,
    target_name: str,
    identity: CapabilityIdentity,
    target_digest: str,
    record: ExecutionRecord,
    store: ExecutionStore,
    *,
    caller_role: Literal["owner", "follower"],
    timed_out: bool = False,
) -> DevStopResult:
    observed, probe_error = _final_probe(target, workspace, target_name)
    ready = observed.healthy if observed is not None else None
    action_succeeded = record.state == "exited" and record.exit_code == 0
    status: Literal["stop-failed", "stop-unverified", "still-ready", "stopped"]
    if not action_succeeded or timed_out:
        status = "stop-failed"
    elif ready is None:
        status = "stop-unverified"
    elif ready:
        status = "still-ready"
    else:
        status = "stopped"
    result = _stop_payload(
        target_name,
        workspace,
        identity,
        target_digest,
        status=status,
        ready=ready,
        stop_kind="exec",
        probe=observed,
        probe_error=probe_error,
    )
    return result.with_attempt(
        _attempt_projection(record, store, caller_role=caller_role, timed_out=timed_out)
    )


def _detached_stop_result(
    target: TargetConfig,
    workspace: WorkspaceIdentity,
    target_name: str,
    identity: CapabilityIdentity,
    target_digest: str,
    record: ExecutionRecord,
    store: ExecutionStore,
) -> DevStopResult:
    result = _stop_payload(
        target_name,
        workspace,
        identity,
        target_digest,
        status="waiting",
        ready=None,
        stop_kind="exec",
        probe=None,
        probe_error=None,
    )
    return result.with_attempt(
        _attempt_projection(record, store, caller_role="follower")
    ).with_caller_status("detached")


def _stop_payload(
    target_name: str,
    workspace: WorkspaceIdentity,
    identity: CapabilityIdentity,
    target_digest: str,
    *,
    status: Literal[
        "manual-action-required",
        "waiting",
        "stop-failed",
        "stop-unverified",
        "still-ready",
        "stopped",
    ],
    ready: bool | None,
    stop_kind: Literal["absent", "manual", "exec"],
    probe: ProbeObservation | None,
    probe_error: Failure | None,
) -> DevStopResult:
    return DevStopResult(
        target=target_name,
        effective_target_digest=target_digest,
        workspace=workspace,
        capability=identity,
        stop=DevStopDeclaration(kind=stop_kind),
        status=status,
        ready=ready,
        probe=probe,
        probe_error=probe_error,
    )


def _attempt_projection(
    record: ExecutionRecord,
    store: ExecutionStore,
    *,
    caller_role: Literal["owner", "follower"],
    timed_out: bool = False,
) -> DevAttempt:
    log = store.log_reference(record, "merged")
    return DevAttempt(
        caller_role=caller_role,
        execution_id=record.execution_id,
        state=record.state,
        argv=record.argv,
        cwd=record.cwd,
        logs=DevMergedLogs(merged=DevLogReference(path=log.path, bytes=log.bytes)),
        duration_ms=record.duration_ms,
        exit_code=record.exit_code,
        requested_signal=record.requested_signal,
        termination_signal=record.termination_signal,
        failure_reason=record.failure_reason,
        timed_out=True if timed_out else None,
    )


def _final_probe(
    target: TargetConfig, workspace: WorkspaceIdentity, target_name: str
) -> tuple[ProbeObservation | None, Failure | None]:
    try:
        return probe_target(target, workspace, target_name=target_name), None
    except SvcError as error:
        return None, error.snapshot()


def _ensure_under_lock(
    store: ExecutionStore,
    target: TargetConfig,
    workspace: WorkspaceIdentity,
    target_name: str,
    identity: CapabilityIdentity,
    target_digest: str,
    intent_digest: str,
    deadline: float,
    on_selected: DevSelectedCallback | None,
) -> DevEnsureResult:
    current_id = store.read_coordination("dev", identity.capability_id)
    if current_id is not None:
        current = store.read(current_id)
        if current.state in ACTIVE_STATES:
            mark_owner_lost(store, current)

    observed = probe_target(
        target,
        workspace,
        target_name=target_name,
        timeout=_remaining(deadline),
    )
    base = _result_base(target, target_digest, workspace, identity, observed)
    if observed.healthy:
        return base.result("reused")
    if observed.responded:
        raise _occupied_error(base)

    provision = target.provision
    if isinstance(provision, ManualProvision):
        raise _SettledEnsure(base.result("manual-action-required"))
    launched = _provision(
        store,
        provision,
        workspace,
        target_name,
        identity,
        intent_digest,
        base,
        on_selected,
        timeout=_remaining(deadline),
    )
    if isinstance(launched, ExecutionRecord):
        return _wait_for_external_readiness(
            target, workspace, target_name, deadline, base, launched, store
        )
    with _cleanup_on_interrupt(store, launched, base):
        return _wait_for_owned_readiness(
            store,
            target,
            workspace,
            target_name,
            deadline,
            base,
            launched,
        )


def _join_dev_attempt(
    store: ExecutionStore,
    lock: BaseFileLock,
    pointer_before: str | None,
    pointer_before_active: bool,
    target: TargetConfig,
    workspace: WorkspaceIdentity,
    target_name: str,
    identity: CapabilityIdentity,
    target_digest: str,
    intent_digest: str,
    deadline: float,
    on_selected: DevSelectedCallback | None,
) -> DevEnsureResult:
    while _remaining(deadline) > 0:
        current_id = store.read_coordination("dev", identity.capability_id)
        if current_id is not None:
            current = store.read(current_id)
            if _same_dev_intent(current, "ensure", target_name, intent_digest) and (
                current.state in ACTIVE_STATES
                or current_id != pointer_before
                or pointer_before_active
            ):
                return _join_ensure_attempt(
                    store,
                    target,
                    workspace,
                    target_name,
                    identity,
                    target_digest,
                    deadline,
                    current,
                    on_selected,
                )
        try:
            lock.acquire(timeout=0)
        except Timeout:
            time.sleep(min(0.02, _remaining(deadline)))
            continue
        try:
            after = store.read_coordination("dev", identity.capability_id)
            if after is not None and after != pointer_before:
                record = store.read(after)
                if _same_dev_intent(record, "ensure", target_name, intent_digest):
                    if record.state in ACTIVE_STATES:
                        record = mark_owner_lost(store, record)
                    return _join_ensure_attempt(
                        store,
                        target,
                        workspace,
                        target_name,
                        identity,
                        target_digest,
                        deadline,
                        record,
                        on_selected,
                    )
            if pointer_before is not None and pointer_before_active:
                previous = store.read(pointer_before)
                if _same_dev_intent(previous, "ensure", target_name, intent_digest):
                    if previous.state in ACTIVE_STATES:
                        previous = mark_owner_lost(store, previous)
                    return _join_ensure_attempt(
                        store,
                        target,
                        workspace,
                        target_name,
                        identity,
                        target_digest,
                        deadline,
                        previous,
                        on_selected,
                    )
            return _ensure_under_lock(
                store,
                target,
                workspace,
                target_name,
                identity,
                target_digest,
                intent_digest,
                deadline,
                on_selected,
            )
        finally:
            lock.release()
    base = _result_base(
        target,
        target_digest,
        workspace,
        identity,
        probe_target(target, workspace, target_name=target_name, timeout=0),
    )
    raise _SettledEnsure(base.result("lock-timeout"))


def _provision(
    store: ExecutionStore,
    provision: ExecProvision,
    workspace: WorkspaceIdentity,
    target_name: str,
    identity: CapabilityIdentity,
    intent_digest: str,
    base: DevEnsureContext,
    on_selected: DevSelectedCallback | None,
    *,
    timeout: float,
) -> OwnedExecution | ExecutionRecord:
    argv = interpolate_dev_argv(provision.argv, workspace, target=target_name)
    cwd = resolve_dev_cwd(workspace.root, provision.cwd, workspace, target_name)
    environment = _dev_environment(provision.env, workspace, target_name)
    published = store.publish(
        domain="dev",
        operation="ensure",
        subject=target_name,
        workspace_instance=workspace.instance,
        intent_digest=intent_digest,
        coordination_key=identity.capability_id,
        argv=argv,
        cwd=cwd,
        capture="merged",
    )
    store.write_coordination(
        "dev", identity.capability_id, published.record.execution_id
    )
    _notify_dev_selected(store, published.record, "owner", on_selected)
    started = start_isolated(store, published, LaunchSpec(argv, cwd, environment))
    if isinstance(started, ExecutionRecord):
        raise SvcError(
            "execution-launch-failed",
            "SVC could not launch the declared provision action.",
            {
                "execution_id": started.execution_id,
                "reason": started.failure_reason or "unknown",
                "logs": {"merged": store.log_reference(started, "merged").as_dict()},
            },
        )
    if provision.mode == "run":
        return started
    settled = wait_owned(store, started, timeout=max(0.01, timeout))
    if settled is None:
        terminated = terminate_owned(store, started)
        raise _SettledEnsure(
            base.result(
                "activation-timeout",
                attempt=_attempt_projection(
                    terminated, store, caller_role="owner", timed_out=True
                ),
                cleanup=(
                    "completed" if terminated.state == "interrupted" else "unknown"
                ),
            )
        )
    if settled.state != "exited" or settled.exit_code != 0:
        raise _SettledEnsure(
            base.result(
                "activation-failed",
                attempt=_attempt_projection(settled, store, caller_role="owner"),
            )
        )
    return settled


def _wait_for_external_readiness(
    target: TargetConfig,
    workspace: WorkspaceIdentity,
    target_name: str,
    deadline: float,
    base: DevEnsureContext,
    attempt: ExecutionRecord,
    store: ExecutionStore,
) -> DevEnsureResult:
    while _remaining(deadline) > 0:
        observed = probe_target(
            target,
            workspace,
            target_name=target_name,
            timeout=_remaining(deadline),
        )
        if observed.healthy:
            return base.result(
                "started",
                ready=True,
                probe=observed,
                attempt=_attempt_projection(attempt, store, caller_role="owner"),
            )
        time.sleep(min(target.poll_interval, _remaining(deadline)))
    raise _SettledEnsure(base.result("readiness-timeout"))


def _wait_for_owned_readiness(
    store: ExecutionStore,
    target: TargetConfig,
    workspace: WorkspaceIdentity,
    target_name: str,
    deadline: float,
    base: DevEnsureContext,
    owned: OwnedExecution,
) -> DevEnsureResult:
    while _remaining(deadline) > 0:
        if owned.process.poll() is not None:
            settled = wait_owned(store, owned)
            raise _SettledEnsure(
                base.result(
                    "child-exit",
                    attempt=_attempt_projection(
                        settled if settled is not None else owned.record,
                        store,
                        caller_role="owner",
                    ),
                    cleanup="completed",
                )
            )
        observed = probe_target(
            target,
            workspace,
            target_name=target_name,
            timeout=_remaining(deadline),
        )
        if observed.healthy:
            try:
                released = release_owned(store, owned)
            except SvcError:
                with suppress(SvcError):
                    terminate_owned(store, owned)
                raise
            return base.result(
                "started",
                ready=True,
                probe=observed,
                attempt=_attempt_projection(released, store, caller_role="owner"),
            )
        time.sleep(min(target.poll_interval, _remaining(deadline)))
    terminated = terminate_owned(store, owned)
    raise _SettledEnsure(
        base.result(
            "readiness-timeout",
            attempt=_attempt_projection(terminated, store, caller_role="owner"),
            cleanup=("completed" if terminated.state == "interrupted" else "unknown"),
        )
    )


def _await_capability_after_attempt(
    target: TargetConfig,
    workspace: WorkspaceIdentity,
    target_name: str,
    identity: CapabilityIdentity,
    target_digest: str,
    deadline: float,
    record: ExecutionRecord,
    *,
    store: ExecutionStore | None = None,
) -> DevEnsureResult:
    authority = store
    while record.state in ACTIVE_STATES and _remaining(deadline) > 0:
        time.sleep(min(0.02, _remaining(deadline)))
        if authority is None:
            break
        record = reconcile_owner_loss(authority, authority.read(record.execution_id))
    while _remaining(deadline) > 0:
        observed = probe_target(
            target,
            workspace,
            target_name=target_name,
            timeout=_remaining(deadline),
        )
        base = _result_base(target, target_digest, workspace, identity, observed)
        if observed.healthy:
            attempt = (
                _attempt_projection(record, authority, caller_role="follower")
                if authority is not None
                else None
            )
            return base.result("joined", attempt=attempt)
        if observed.responded:
            raise _occupied_error(base)
        if record.state not in {"released", "owner-lost", "exited"}:
            raise _attempt_error(record, base, authority)
        time.sleep(min(target.poll_interval, _remaining(deadline)))
    observed = probe_target(target, workspace, target_name=target_name, timeout=0)
    base = _result_base(target, target_digest, workspace, identity, observed)
    if record.state == "owner-lost":
        raise _SettledEnsure(
            base.result("owner-lost", execution_id=record.execution_id)
        )
    raise _SettledEnsure(
        base.result("readiness-timeout", execution_id=record.execution_id)
    )


def _join_ensure_attempt(
    store: ExecutionStore,
    target: TargetConfig,
    workspace: WorkspaceIdentity,
    target_name: str,
    identity: CapabilityIdentity,
    target_digest: str,
    deadline: float,
    record: ExecutionRecord,
    on_selected: DevSelectedCallback | None,
) -> DevEnsureResult:
    _notify_dev_selected(store, record, "follower", on_selected)
    try:
        return _await_capability_after_attempt(
            target,
            workspace,
            target_name,
            identity,
            target_digest,
            deadline,
            record,
            store=store,
        )
    except KeyboardInterrupt:
        return DevEnsureResult(
            target=target_name,
            ready=None,
            status="waiting",
            caller_status="detached",
            effective_target_digest=target_digest,
            workspace=workspace,
            capability=identity,
            access=tuple(
                interpolate_dev_value(value, workspace, target=target_name)
                for value in target.access
            ),
            provision=_provision_projection(target),
            attempt=_attempt_projection(
                store.read(record.execution_id), store, caller_role="follower"
            ),
        )


def _attempt_error(
    record: ExecutionRecord,
    base: DevEnsureContext,
    store: ExecutionStore | None,
) -> _SettledEnsure:
    attempt = (
        _attempt_projection(record, store, caller_role="follower")
        if store is not None
        else None
    )
    return _SettledEnsure(
        base.result(
            record.state,
            attempt=attempt,
            execution_id=record.execution_id,
        )
    )


@contextmanager
def _cleanup_on_interrupt(
    store: ExecutionStore,
    owned: OwnedExecution,
    base: DevEnsureContext,
) -> Iterator[None]:
    if threading.current_thread() is not threading.main_thread():
        yield
        return
    previous = {
        number: signal.getsignal(number) for number in (signal.SIGINT, signal.SIGTERM)
    }

    def interrupt(_number: int, _frame: object) -> None:
        raise KeyboardInterrupt

    try:
        for number in previous:
            signal.signal(number, interrupt)
        try:
            yield
        except KeyboardInterrupt as error:
            terminated = terminate_owned(store, owned)
            raise _SettledEnsure(
                base.result(
                    "interrupted",
                    attempt=_attempt_projection(terminated, store, caller_role="owner"),
                    cleanup=(
                        "completed" if terminated.state == "interrupted" else "unknown"
                    ),
                )
            ) from error
    finally:
        for number, handler in previous.items():
            signal.signal(number, handler)


def _occupied_error(base: DevEnsureContext) -> _SettledEnsure:
    return _SettledEnsure(base.result("conflict"))


def _entry_is_healthy(entry: DevTargetStatus) -> bool:
    return isinstance(entry, DevTargetObservation) and entry.probe.healthy


def _provision_projection(target: TargetConfig) -> DevProvisionSummary:
    provision = target.provision
    if isinstance(provision, ExecProvision):
        return ExecProvisionSummary(mode=provision.mode)
    return ManualProvisionSummary()


def _dev_continuation(
    target: TargetConfig, observed: ProbeObservation
) -> Literal["blocked-unhealthy-responder", "manual-action-required", "ensure"] | None:
    if observed.healthy:
        return None
    if observed.responded:
        return "blocked-unhealthy-responder"
    if isinstance(target.provision, ManualProvision):
        return "manual-action-required"
    return "ensure"


def _result_base(
    target: TargetConfig,
    target_digest: str,
    workspace: WorkspaceIdentity,
    identity: CapabilityIdentity,
    observed: ProbeObservation,
) -> DevEnsureContext:
    resolved_probe = resolve_probe(target, workspace, target_name=identity.target)
    return DevEnsureContext(
        target=identity.target,
        ready=observed.healthy,
        effective_target_digest=target_digest,
        workspace=workspace,
        capability=identity,
        access=tuple(
            interpolate_dev_value(value, workspace, target=identity.target)
            for value in target.access
        ),
        provision=_provision_projection(target),
        probe=observed,
        probe_argv=resolved_probe.argv,
    )


def _effective_target_digest(target: TargetConfig) -> str:
    return _json_digest(target.model_dump(mode="json", exclude_none=True))


def _ensure_intent_digest(target: TargetConfig, identity: CapabilityIdentity) -> str:
    value = target.model_dump(mode="json", exclude={"stop"}, exclude_none=True)
    return _json_digest(
        {"operation": "ensure", "endpoint_id": identity.endpoint_id, "target": value}
    )


def _stop_intent_digest(target: TargetConfig, identity: CapabilityIdentity) -> str:
    return _json_digest(
        {
            "operation": "stop",
            "endpoint_id": identity.endpoint_id,
            "probe": target.probe.model_dump(mode="json", exclude_none=True),
            "stop": (
                target.stop.model_dump(mode="json", exclude_none=True)
                if target.stop is not None
                else None
            ),
        }
    )


def _dev_environment(
    declared: dict[str, str], workspace: WorkspaceIdentity, target_name: str
) -> dict[str, str]:
    environment = os.environ.copy()
    environment.update(
        {
            "SVC_DEV_INSTANCE": workspace.instance,
            "SVC_DEV_WORKTREE_ID": workspace.worktree_id,
            "SVC_DEV_TARGET": target_name,
        }
    )
    environment.update(
        {
            key: interpolate_dev_value(value, workspace, target=target_name)
            for key, value in declared.items()
        }
    )
    return environment


def _json_digest(value: object) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _same_dev_intent(
    record: ExecutionRecord,
    operation: str,
    target_name: str,
    intent_digest: str,
) -> bool:
    return (
        record.domain == "dev"
        and record.operation == operation
        and record.subject == target_name
        and record.intent_digest == intent_digest
    )


def _notify_dev_selected(
    store: ExecutionStore,
    record: ExecutionRecord,
    caller_role: str,
    callback: DevSelectedCallback | None,
) -> None:
    if callback is not None:
        callback(record, caller_role, str(store.log_path(record, "merged")))


def _remaining(deadline: float) -> float:
    return max(0.0, deadline - time.monotonic())
