"""Exact, plan-first local file-state transactions."""

from __future__ import annotations

import os
import tempfile
from contextlib import suppress
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any, Literal, TypeAlias

from .catalog import canonical_json, sha256_bytes
from .errors import SvcError


PLAN_SCHEMA_VERSION = 2
CREATED_TEXT_MODE = 0o644
FileStateKind: TypeAlias = Literal["absent", "file"]
PlanAction: TypeAlias = Literal["create", "append", "refresh", "rewrite", "delete"]
RollbackStatus: TypeAlias = Literal["succeeded", "conflicted", "failed"]
LocalApplyStatus: TypeAlias = Literal["noop", "applied"]


@dataclass(frozen=True)
class LocalApplyResult:
    status: LocalApplyStatus
    changed: int
    verification: Literal["passed"]
    plan_digest: str


def normalized_target_path(value: str) -> str:
    path = PurePosixPath(value)
    if (
        not value
        or path.is_absolute()
        or "." in path.parts
        or ".." in path.parts
        or path.as_posix() != value
    ):
        raise ValueError(f"Plan target must be a normalized relative path: {value!r}")
    return value


def _supports_posix_mode() -> bool:
    return os.name != "nt"


@dataclass(frozen=True)
class Blocker:
    code: str
    path: str
    message: str

    def as_dict(self) -> dict[str, object]:
        return {"code": self.code, "path": self.path, "message": self.message}


@dataclass(frozen=True)
class FileState:
    """Exact observable state for one absent or regular-file path."""

    state: FileStateKind
    sha256: str | None = None
    posix_mode: int | None = None

    def __post_init__(self) -> None:
        if self.state == "absent":
            if self.sha256 is not None or self.posix_mode is not None:
                raise ValueError("An absent file state has no digest or mode")
            return
        if self.state != "file":
            raise ValueError(f"Unsupported file state: {self.state!r}")
        if self.sha256 is None:
            raise ValueError("A file state needs a digest")
        if self.posix_mode is not None and not 0 <= self.posix_mode <= 0o777:
            raise ValueError("A POSIX file mode must contain only permission bits")

    def as_dict(self) -> dict[str, object]:
        result: dict[str, object] = {"state": self.state}
        if self.sha256 is not None:
            result["sha256"] = self.sha256
        if self.posix_mode is not None:
            result["posix_mode"] = self.posix_mode
        return result


ABSENT_FILE = FileState("absent")


@dataclass(frozen=True)
class PlannedFileMutation:
    path: str
    action: PlanAction
    reason: str
    before: FileState
    after: FileState
    parent_preconditions: tuple[tuple[str, str], ...]
    before_content: bytes | None = field(repr=False, compare=False)
    after_content: bytes | None = field(repr=False, compare=False)

    def __post_init__(self) -> None:
        normalized_target_path(self.path)
        if (self.before.state == "file") != (self.before_content is not None):
            raise ValueError("Before content must agree with before file state")
        if (self.after.state == "file") != (self.after_content is not None):
            raise ValueError("After content must agree with after file state")
        if self.before == self.after:
            raise ValueError("A planned file mutation must change state")

    def signature(self) -> dict[str, object]:
        return {
            "path": self.path,
            "action": self.action,
            "before": self.before.as_dict(),
            "after": self.after.as_dict(),
            "parent_preconditions": [
                list(state) for state in self.parent_preconditions
            ],
        }

    def as_dict(self) -> dict[str, object]:
        return {
            "path": self.path,
            "action": self.action,
            "reason": self.reason,
            "before": self.before.as_dict(),
            "after": self.after.as_dict(),
        }


@dataclass(frozen=True)
class RollbackReport:
    status: RollbackStatus
    restored_paths: tuple[str, ...] = ()
    preserved_external_paths: tuple[str, ...] = ()
    unrestored_paths: tuple[str, ...] = ()

    @property
    def repository_effect(self) -> str:
        if self.status == "failed":
            return "uncertain"
        if self.status == "conflicted":
            return "external-changes-preserved"
        return "restored"

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "restored_paths": list(self.restored_paths),
            "preserved_external_paths": list(self.preserved_external_paths),
            "unrestored_paths": list(self.unrestored_paths),
        }


@dataclass(frozen=True)
class LocalPlan:
    command: str
    repo: Path
    target_version: str
    mutations: tuple[PlannedFileMutation, ...]
    blockers: tuple[Blocker, ...] = ()

    def __post_init__(self) -> None:
        paths = tuple(mutation.path for mutation in self.mutations)
        if len(paths) != len(set(paths)):
            raise ValueError("A local plan may mutate each path only once")

    @property
    def status(self) -> Literal["blocked", "ready", "noop"]:
        if self.blockers:
            return "blocked"
        return "ready" if self.mutations else "noop"

    @property
    def digest(self) -> str:
        return sha256_bytes(canonical_json(self.signature()))

    def signature(self) -> dict[str, object]:
        return {
            "schema_version": PLAN_SCHEMA_VERSION,
            "command": self.command,
            "repo": str(self.repo.resolve()),
            "target_version": self.target_version,
            "operations": [mutation.signature() for mutation in self.mutations],
            "blockers": [
                {"code": blocker.code, "path": blocker.path}
                for blocker in self.blockers
            ],
        }


def make_write(
    repo: Path,
    path: str,
    action: PlanAction,
    reason: str,
    content: bytes,
) -> PlannedFileMutation:
    target = _absolute_target(repo, path)
    before_content, before = _read_file(target)
    after_mode = before.posix_mode
    if before.state == "absent" and _supports_posix_mode():
        after_mode = CREATED_TEXT_MODE
    after = FileState("file", sha256_bytes(content), after_mode)
    return PlannedFileMutation(
        path=path,
        action=action,
        reason=reason,
        before=before,
        after=after,
        parent_preconditions=_parent_states(repo.resolve(), target),
        before_content=before_content,
        after_content=content,
    )


def make_delete(
    repo: Path,
    path: str,
    action: PlanAction,
    reason: str,
) -> PlannedFileMutation:
    target = _absolute_target(repo, path)
    before_content, before = _read_file(target)
    if before.state == "absent":
        raise ValueError(f"Cannot plan deletion of an absent file: {path}")
    return PlannedFileMutation(
        path=path,
        action=action,
        reason=reason,
        before=before,
        after=ABSENT_FILE,
        parent_preconditions=_parent_states(repo.resolve(), target),
        before_content=before_content,
        after_content=None,
    )


def apply_local_plan(plan: LocalPlan, approved_digest: str) -> LocalApplyResult:
    """Apply exactly one approved file-state transaction."""

    if approved_digest != plan.digest:
        raise SvcError(
            "plan-digest-mismatch",
            "The supplied plan digest does not match the current plan.",
            {"expected": plan.digest, "received": approved_digest},
        )
    if plan.blockers:
        raise SvcError(
            "plan-blocked",
            "The plan has unresolved blockers.",
            {"blockers": [blocker.as_dict() for blocker in plan.blockers]},
        )
    if not plan.repo.is_dir():
        raise SvcError(
            "repo-not-directory",
            "Project root is not a directory.",
            {"repo": str(plan.repo)},
        )

    _assert_preconditions(plan)
    if not plan.mutations:
        return LocalApplyResult(
            status="noop",
            changed=0,
            verification="passed",
            plan_digest=plan.digest,
        )

    attempted: list[PlannedFileMutation] = []
    created_directories: list[Path] = []
    try:
        with tempfile.TemporaryDirectory(prefix="svc-plan-") as staging_directory:
            staged = _stage_after_content(plan, Path(staging_directory))
            _assert_preconditions(plan)
            try:
                for mutation in plan.mutations:
                    target = _absolute_target(plan.repo, mutation.path)
                    _assert_mutation_precondition(plan.repo.resolve(), target, mutation)
                    if mutation.after.state == "file":
                        _ensure_parent_directories(
                            plan.repo.resolve(), target, created_directories
                        )
                    # Register before the atomic effect. If SIGINT lands after
                    # os.replace/unlink but before this call returns, rollback
                    # reconciles the observed path against before and after.
                    attempted.append(mutation)
                    _commit_mutation(target, mutation, staged.get(mutation.path))
                _verify_postconditions(plan)
            except SvcError as error:
                report = _rollback(plan, attempted, created_directories)
                error.details = {
                    **error.details,
                    "rollback": report.as_dict(),
                    "repository_effect": report.repository_effect,
                }
                raise
            except OSError as error:
                report = _rollback(plan, attempted, created_directories)
                raise SvcError(
                    "apply-failed",
                    f"Project integration apply failed: {error}",
                    {
                        "rollback": report.as_dict(),
                        "repository_effect": report.repository_effect,
                    },
                ) from error
    except KeyboardInterrupt as error:
        if attempted or created_directories:
            report = _rollback(plan, attempted, created_directories)
            details: dict[str, Any] = {
                "rollback": report.as_dict(),
                "repository_effect": report.repository_effect,
            }
        else:
            details = {"repository_effect": "none"}
        raise SvcError(
            "apply-interrupted",
            "Project integration apply was interrupted.",
            details,
        ) from error
    except OSError as error:
        # Staging occurs before any repository mutation.
        raise SvcError(
            "staging-failed",
            f"Project integration staging failed: {error}",
            {"repository_effect": "none"},
        ) from error

    return LocalApplyResult(
        status="applied",
        changed=len(plan.mutations),
        verification="passed",
        plan_digest=plan.digest,
    )


def _stage_after_content(plan: LocalPlan, staging: Path) -> dict[str, bytes]:
    staged: dict[str, bytes] = {}
    for index, mutation in enumerate(plan.mutations):
        if mutation.after_content is None:
            continue
        staged_path = staging / str(index)
        staged_path.write_bytes(mutation.after_content)
        content = staged_path.read_bytes()
        if sha256_bytes(content) != mutation.after.sha256:
            raise SvcError(
                "staging-failed",
                "Staged output did not match the plan.",
                {"path": mutation.path, "repository_effect": "none"},
            )
        staged[mutation.path] = content
    return staged


def _absolute_target(repo: Path, relative: str) -> Path:
    normalized = normalized_target_path(relative)
    root = repo.resolve()
    target = root.joinpath(*PurePosixPath(normalized).parts)
    try:
        target.resolve(strict=False).relative_to(root)
    except ValueError as error:
        raise SvcError(
            "unsafe-target",
            "Plan target escapes the project root.",
            {"path": relative},
        ) from error
    return target


def _read_file(path: Path) -> tuple[bytes | None, FileState]:
    if not path.exists() and not path.is_symlink():
        return None, ABSENT_FILE
    if path.is_symlink() or not path.is_file():
        raise SvcError(
            "path-not-file",
            "Integration target must be a regular file.",
            {"path": str(path)},
        )
    content = path.read_bytes()
    mode = path.stat().st_mode & 0o777 if _supports_posix_mode() else None
    return content, FileState("file", sha256_bytes(content), mode)


def _parent_states(root: Path, target: Path) -> tuple[tuple[str, str], ...]:
    parents: list[Path] = []
    cursor = target.parent
    while cursor != root:
        parents.append(cursor)
        cursor = cursor.parent
    return tuple(
        (parent.relative_to(root).as_posix(), _path_state(parent))
        for parent in reversed(parents)
    )


def _path_state(path: Path) -> str:
    if not path.exists() and not path.is_symlink():
        return "missing"
    if path.is_symlink():
        return "symlink"
    if path.is_dir():
        return "directory"
    return "other"


def _assert_preconditions(plan: LocalPlan) -> None:
    root = plan.repo.resolve()
    for mutation in plan.mutations:
        _assert_mutation_precondition(
            root, _absolute_target(plan.repo, mutation.path), mutation
        )


def _assert_mutation_precondition(
    root: Path, path: Path, mutation: PlannedFileMutation
) -> None:
    _, actual = _read_file(path)
    if actual != mutation.before:
        raise SvcError(
            "stale-plan",
            "Project file state changed after planning.",
            {
                "path": mutation.path,
                "expected": mutation.before.as_dict(),
                "actual": actual.as_dict(),
            },
        )
    for relative, expected_state in mutation.parent_preconditions:
        actual_state = _path_state(root.joinpath(*PurePosixPath(relative).parts))
        if actual_state != expected_state:
            raise SvcError(
                "stale-plan",
                "Project parent path changed after planning.",
                {
                    "path": mutation.path,
                    "parent": relative,
                    "expected_state": expected_state,
                    "actual_state": actual_state,
                },
            )


def _ensure_parent_directories(root: Path, target: Path, created: list[Path]) -> None:
    pending: list[Path] = []
    cursor = target.parent
    while cursor != root and not cursor.exists():
        pending.append(cursor)
        cursor = cursor.parent
    if cursor.exists() and not cursor.is_dir():
        raise SvcError(
            "parent-not-directory",
            "Integration target parent is not a directory.",
            {"path": str(cursor)},
        )
    for directory in reversed(pending):
        directory.mkdir()
        created.append(directory)


def _write_atomic(path: Path, content: bytes, mode: int | None) -> None:
    descriptor, temporary = tempfile.mkstemp(prefix=".svc-write-", dir=path.parent)
    temporary_path = Path(temporary)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        if mode is not None:
            os.chmod(temporary_path, mode)
        os.replace(temporary_path, path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def _commit_mutation(
    path: Path, mutation: PlannedFileMutation, staged_content: bytes | None
) -> None:
    if mutation.after.state == "absent":
        path.unlink()
        return
    if staged_content is None:
        raise SvcError(
            "staging-failed",
            "Planned file content was not staged.",
            {"path": mutation.path},
        )
    _write_atomic(path, staged_content, mutation.after.posix_mode)


def _verify_postconditions(plan: LocalPlan) -> None:
    for mutation in plan.mutations:
        _, actual = _read_file(_absolute_target(plan.repo, mutation.path))
        if actual != mutation.after:
            raise SvcError(
                "postcondition-failed",
                "Applied file state differs from the approved plan.",
                {
                    "path": mutation.path,
                    "expected": mutation.after.as_dict(),
                    "actual": actual.as_dict(),
                },
            )


def _restore_before(path: Path, mutation: PlannedFileMutation) -> None:
    if mutation.before.state == "absent":
        if path.exists() or path.is_symlink():
            path.unlink()
        return
    if mutation.before_content is None:
        raise OSError(f"Missing rollback bytes for {mutation.path}")
    _write_atomic(path, mutation.before_content, mutation.before.posix_mode)


def _rollback(
    plan: LocalPlan,
    attempted: list[PlannedFileMutation],
    created_directories: list[Path],
) -> RollbackReport:
    restored: list[str] = []
    preserved: list[str] = []
    unrestored: list[str] = []
    for mutation in reversed(attempted):
        path = _absolute_target(plan.repo, mutation.path)
        try:
            _, current = _read_file(path)
            if current == mutation.before:
                continue
            if current != mutation.after:
                preserved.append(mutation.path)
                continue
            _restore_before(path, mutation)
            _, restored_state = _read_file(path)
            if restored_state == mutation.before:
                restored.append(mutation.path)
            else:
                unrestored.append(mutation.path)
        except (OSError, SvcError):
            unrestored.append(mutation.path)
    for directory in reversed(created_directories):
        with suppress(OSError):
            directory.rmdir()
    status: RollbackStatus = (
        "failed" if unrestored else "conflicted" if preserved else "succeeded"
    )
    return RollbackReport(
        status,
        tuple(reversed(restored)),
        tuple(reversed(preserved)),
        tuple(reversed(unrestored)),
    )
