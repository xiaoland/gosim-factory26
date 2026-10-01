"""Public run receipt projection and CLI exit policy."""

from __future__ import annotations

import os
from typing import Literal

from .._execution import ExecutionState
from .model import MachineModel
from ..run.runtime import CallerRole, RunOutcome


class RunLogReference(MachineModel):
    path: str
    bytes: int


class RunLogs(MachineModel):
    stdout: RunLogReference
    stderr: RunLogReference


class RunReceipt(MachineModel):
    """Public receipt for execute, follow, and inspect callers."""

    machine_exclude_none = True

    schema_version: Literal[2] = 2
    command: Literal["run", "run follow", "run inspect"]
    caller_role: CallerRole
    entry: str
    caller_status: Literal["detached"] | None = None
    execution_id: str | None = None
    workspace_instance: str | None = None
    effective_entry_digest: str | None = None
    state: ExecutionState | None = None
    argv: tuple[str, ...] | None = None
    cwd: str | None = None
    env_files: tuple[str, ...] | None = None
    started_at: str | None = None
    finished_at: str | None = None
    duration_ms: int | None = None
    exit_code: int | None = None
    requested_signal: str | None = None
    termination_signal: str | None = None
    logs: RunLogs | None = None


def project_run_receipt(
    outcome: RunOutcome, command: Literal["run", "run follow", "run inspect"]
) -> RunReceipt:
    """Project neutral execution facts onto the public run receipt."""

    if outcome.detached:
        record = outcome.record
        return RunReceipt(
            command=command,
            caller_role=outcome.caller_role,
            entry=outcome.entry,
            caller_status="detached",
            execution_id=None if record is None else record.execution_id,
            workspace_instance=None if record is None else record.workspace_instance,
            effective_entry_digest=None if record is None else record.intent_digest,
            state=None if record is None else record.state,
            argv=None if record is None else record.argv,
            cwd=None if record is None else record.cwd,
            env_files=None if record is None else record.env_files,
            started_at=None if record is None else record.started_at,
            logs=_run_logs(outcome),
        )
    if outcome.record is None:
        raise ValueError("settled run outcome has no execution record")
    record = outcome.record
    return RunReceipt(
        command=command,
        caller_role=outcome.caller_role,
        execution_id=record.execution_id,
        entry=record.subject,
        workspace_instance=record.workspace_instance,
        effective_entry_digest=record.intent_digest,
        state=record.state,
        argv=record.argv,
        cwd=record.cwd,
        env_files=record.env_files,
        started_at=record.started_at,
        finished_at=record.finished_at,
        duration_ms=record.duration_ms,
        exit_code=record.exit_code,
        requested_signal=record.requested_signal,
        termination_signal=record.termination_signal,
        logs=_run_logs(outcome),
    )


def run_exit_code(outcome: RunOutcome, *, inspect: bool = False) -> int:
    """Map a neutral run outcome onto the CLI process contract."""

    if inspect:
        return 0
    if outcome.detached:
        return 130
    if outcome.record is None:
        return 4
    record = outcome.record
    if record.state == "exited":
        return int(record.exit_code or 0)
    if record.state == "interrupted":
        signal_name = record.requested_signal or record.termination_signal
        if signal_name == "SIGINT":
            return 130
        if signal_name == "SIGTERM":
            return 143 if os.name != "nt" else 4
    return 4


def _run_logs(outcome: RunOutcome) -> RunLogs | None:
    record = outcome.record
    if outcome.store is None or record is None:
        return None
    stdout = outcome.store.log_reference(record, "stdout")
    stderr = outcome.store.log_reference(record, "stderr")
    return RunLogs(
        stdout=RunLogReference(path=stdout.path, bytes=stdout.bytes),
        stderr=RunLogReference(path=stderr.path, bytes=stderr.bytes),
    )
