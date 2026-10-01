"""Shared public projections for service-owned file transaction facts."""

from __future__ import annotations

from pydantic import Field

from .model import MachineModel
from ..plans import (
    Blocker,
    FileState,
    FileStateKind,
    PlanAction,
    PlannedFileMutation,
    RollbackReport,
    RollbackStatus,
)


class BlockerOutput(MachineModel):
    code: str
    path: str
    message: str


class FileStateOutput(MachineModel):
    state: FileStateKind
    sha256: str | None = Field(default=None, exclude_if=lambda value: value is None)
    posix_mode: int | None = Field(default=None, exclude_if=lambda value: value is None)


class FileMutationOutput(MachineModel):
    path: str
    action: PlanAction
    reason: str
    before: FileStateOutput
    after: FileStateOutput


class RollbackOutput(MachineModel):
    status: RollbackStatus
    restored_paths: tuple[str, ...]
    preserved_external_paths: tuple[str, ...]
    unrestored_paths: tuple[str, ...]


def project_blocker(value: Blocker) -> BlockerOutput:
    return BlockerOutput(code=value.code, path=value.path, message=value.message)


def project_file_state(value: FileState) -> FileStateOutput:
    return FileStateOutput(
        state=value.state,
        sha256=value.sha256,
        posix_mode=value.posix_mode,
    )


def project_file_mutation(value: PlannedFileMutation) -> FileMutationOutput:
    return FileMutationOutput(
        path=value.path,
        action=value.action,
        reason=value.reason,
        before=project_file_state(value.before),
        after=project_file_state(value.after),
    )


def project_rollback(value: RollbackReport) -> RollbackOutput:
    return RollbackOutput(
        status=value.status,
        restored_paths=value.restored_paths,
        preserved_external_paths=value.preserved_external_paths,
        unrestored_paths=value.unrestored_paths,
    )
