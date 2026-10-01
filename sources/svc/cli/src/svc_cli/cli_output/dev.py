"""Public dev output and projections from dev capability services."""

from __future__ import annotations

from typing import Literal, TypeAlias

from .._execution import ExecutionState
from ..dev.identity import CapabilityIdentity
from ..dev.readiness import ProbeObservation
from ..dev.runtime import (
    DevAttempt as ServiceDevAttempt,
    DevEnsureResult,
    DevEnsureStatus,
    DevIdentityResult,
    DevStatusResult,
    DevStopResult,
    DevTargetFailure as ServiceDevTargetFailure,
    DevTargetObservation as ServiceDevTargetObservation,
    DevTargetStatus as ServiceDevTargetStatus,
    ExecProvisionSummary as ServiceExecProvisionSummary,
    ManualProvisionSummary as ServiceManualProvisionSummary,
)
from ..workspace import WorkspaceIdentity
from .model import MachineErrorBody, MachineModel, project_failure


class DevLogReference(MachineModel):
    path: str
    bytes: int


class DevMergedLogs(MachineModel):
    merged: DevLogReference


class DevAttempt(MachineModel):
    machine_exclude_none = True

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


class ManualProvisionOutput(MachineModel):
    kind: Literal["manual"] = "manual"


class ExecProvisionOutput(MachineModel):
    kind: Literal["exec"] = "exec"
    mode: Literal["run", "activate"]


DevProvisionOutput: TypeAlias = ManualProvisionOutput | ExecProvisionOutput


class DevStopDeclaration(MachineModel):
    kind: Literal["absent", "manual", "exec"]


class DevIdentityOutput(MachineModel):
    schema_version: Literal[2] = 2
    command: Literal["dev identity"] = "dev identity"
    workspace: WorkspaceIdentity


class DevTargetObservation(MachineModel):
    machine_exclude_none = True

    target: str
    effective_target_digest: str
    capability: CapabilityIdentity
    probe: ProbeObservation
    access: tuple[str, ...]
    provision: DevProvisionOutput
    continuation: (
        Literal["blocked-unhealthy-responder", "manual-action-required", "ensure"]
        | None
    ) = None
    probe_argv: tuple[str, ...] | None = None


class DevTargetError(MachineModel):
    target: str
    effective_target_digest: str
    error: MachineErrorBody


DevTargetStatus: TypeAlias = DevTargetObservation | DevTargetError


class DevStatusOutput(MachineModel):
    machine_exclude_none = True

    schema_version: Literal[2] = 2
    command: Literal["dev status"] = "dev status"
    healthy: bool
    status: Literal[
        "healthy", "action-required", "invalid-configuration", "not-configured"
    ]
    workspace: WorkspaceIdentity
    reason: str | None = None
    targets: tuple[DevTargetStatus, ...] | None = None


class DevEnsureOutput(MachineModel):
    machine_exclude_none = True

    schema_version: Literal[2] = 2
    command: Literal["dev ensure"] = "dev ensure"
    target: str
    ready: bool | None
    status: DevEnsureStatus
    effective_target_digest: str
    workspace: WorkspaceIdentity
    capability: CapabilityIdentity
    access: tuple[str, ...]
    provision: DevProvisionOutput
    probe: ProbeObservation | None = None
    probe_argv: tuple[str, ...] | None = None
    attempt: DevAttempt | None = None
    caller_status: Literal["detached"] | None = None
    cleanup: Literal["completed", "unknown"] | None = None
    execution_id: str | None = None


class DevStopOutput(MachineModel):
    machine_exclude_none = True

    schema_version: Literal[2] = 2
    command: Literal["dev stop"] = "dev stop"
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
    probe_error: MachineErrorBody | None = None
    caller_status: Literal["detached", "interrupted"] | None = None
    attempt: DevAttempt | None = None


def project_dev_identity(result: DevIdentityResult) -> DevIdentityOutput:
    return DevIdentityOutput(workspace=result.workspace)


def project_dev_status(result: DevStatusResult) -> DevStatusOutput:
    return DevStatusOutput(
        healthy=result.healthy,
        status=result.status,
        workspace=result.workspace,
        reason=result.reason,
        targets=(
            None
            if result.targets is None
            else tuple(_target(value) for value in result.targets)
        ),
    )


def project_dev_ensure(result: DevEnsureResult) -> DevEnsureOutput:
    return DevEnsureOutput(
        target=result.target,
        ready=result.ready,
        status=result.status,
        effective_target_digest=result.effective_target_digest,
        workspace=result.workspace,
        capability=result.capability,
        access=result.access,
        provision=_provision(result.provision),
        probe=result.probe,
        probe_argv=result.probe_argv,
        attempt=None if result.attempt is None else _attempt(result.attempt),
        caller_status=result.caller_status,
        cleanup=result.cleanup,
        execution_id=result.execution_id,
    )


def project_dev_stop(result: DevStopResult) -> DevStopOutput:
    return DevStopOutput(
        target=result.target,
        effective_target_digest=result.effective_target_digest,
        workspace=result.workspace,
        capability=result.capability,
        stop=DevStopDeclaration(kind=result.stop.kind),
        status=result.status,
        ready=result.ready,
        probe=result.probe,
        probe_error=(
            None if result.probe_error is None else project_failure(result.probe_error)
        ),
        caller_status=result.caller_status,
        attempt=None if result.attempt is None else _attempt(result.attempt),
    )


def _target(value: ServiceDevTargetStatus) -> DevTargetStatus:
    if isinstance(value, ServiceDevTargetFailure):
        return DevTargetError(
            target=value.target,
            effective_target_digest=value.effective_target_digest,
            error=project_failure(value.error),
        )
    assert isinstance(value, ServiceDevTargetObservation)
    return DevTargetObservation(
        target=value.target,
        effective_target_digest=value.effective_target_digest,
        capability=value.capability,
        probe=value.probe,
        access=value.access,
        provision=_provision(value.provision),
        continuation=value.continuation,
        probe_argv=value.probe_argv,
    )


def _provision(
    value: ServiceManualProvisionSummary | ServiceExecProvisionSummary,
) -> DevProvisionOutput:
    if isinstance(value, ServiceExecProvisionSummary):
        return ExecProvisionOutput(mode=value.mode)
    return ManualProvisionOutput()


def _attempt(value: ServiceDevAttempt) -> DevAttempt:
    return DevAttempt(
        caller_role=value.caller_role,
        execution_id=value.execution_id,
        state=value.state,
        argv=value.argv,
        cwd=value.cwd,
        logs=DevMergedLogs(
            merged=DevLogReference(
                path=value.logs.merged.path,
                bytes=value.logs.merged.bytes,
            )
        ),
        duration_ms=value.duration_ms,
        exit_code=value.exit_code,
        requested_signal=value.requested_signal,
        termination_signal=value.termination_signal,
        failure_reason=value.failure_reason,
        timed_out=value.timed_out,
    )
