"""Run-entry resolution, convergence, and execution outcomes."""

from __future__ import annotations

import hashlib
import io
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Callable, Literal, Mapping

from dotenv.parser import parse_stream
from filelock import BaseFileLock, Timeout

from .._execution import (
    ACTIVE_STATES,
    ExecutionRecord,
    ExecutionStore,
    LaunchSpec,
    follow_execution,
    mark_owner_lost,
    reconcile_owner_loss,
    require_execution_id,
    run_foreground,
    settle_unstarted_interruption,
)
from ..config import ConfigError, RunEntry, load_config
from ..errors import SvcError
from ..workspace import WorkspaceIdentity, resolve_workspace_identity


CallerRole = Literal["owner", "follower", "inspector"]
SelectedCallback = Callable[[ExecutionRecord, CallerRole], None]


@dataclass(frozen=True)
class ResolvedRun:
    entry: str
    workspace: WorkspaceIdentity
    argv: tuple[str, ...]
    cwd: Path
    env_files: tuple[Path, ...]
    environment: Mapping[str, str]
    effective_entry_digest: str
    coordination_key: str


@dataclass(frozen=True)
class RunOutcome:
    caller_role: CallerRole
    entry: str
    record: ExecutionRecord | None
    detached: bool = False
    store: ExecutionStore | None = None


def resolve_run(
    repo: Path,
    entry_name: str,
    *,
    namespace: str | None = None,
    ambient: Mapping[str, str] | None = None,
) -> ResolvedRun:
    try:
        resolved = load_config(repo)
    except ConfigError as error:
        raise SvcError(
            "invalid-project-configuration",
            "Cannot load declared run configuration.",
            {"reason": str(error)},
        ) from error
    if entry_name not in resolved.base.run:
        raise SvcError(
            "unknown-run-entry",
            "The project has no committed run entry with this name.",
            {
                "entry": entry_name,
                "available_entries": sorted(resolved.base.run)[:50],
            },
        )
    entry = resolved.effective.run[entry_name]
    workspace = resolve_workspace_identity(repo, namespace=namespace)
    cwd = _resolve_directory(workspace.root, entry.cwd)
    env_files, file_layers = _load_env_files(workspace.root, entry.env_files)
    environment = _resolve_environment(
        os.environ if ambient is None else ambient, file_layers, entry.env
    )
    _validate_launch(entry.argv, cwd, env_files, environment)
    effective_digest = _effective_digest(entry, cwd, env_files, file_layers)
    coordination_key = _digest(
        "run-coordination",
        workspace.namespace_id,
        workspace.worktree_id,
        entry_name,
    )
    return ResolvedRun(
        entry=entry_name,
        workspace=workspace,
        argv=tuple(entry.argv),
        cwd=cwd,
        env_files=env_files,
        environment=environment,
        effective_entry_digest=effective_digest,
        coordination_key=coordination_key,
    )


def execute_entry(
    repo: Path,
    entry_name: str,
    *,
    stdout_sink: BinaryIO | None,
    stderr_sink: BinaryIO | None,
    on_selected: SelectedCallback | None = None,
    namespace: str | None = None,
    store: ExecutionStore | None = None,
) -> RunOutcome:
    selected = resolve_run(repo, entry_name, namespace=namespace)
    authority = store or ExecutionStore()
    lock = authority.coordination_lock("run", selected.coordination_key)
    pointer_before = authority.read_coordination("run", selected.coordination_key)
    pointer_before_active = (
        pointer_before is not None
        and _same_intent(authority.read(pointer_before), selected)
        and authority.read(pointer_before).state in ACTIVE_STATES
    )
    try:
        lock.acquire(timeout=0)
    except Timeout:
        return _join_or_claim_after_publication(
            authority,
            lock,
            selected,
            pointer_before,
            pointer_before_active,
            stdout_sink,
            stderr_sink,
            on_selected,
        )

    try:
        current_id = authority.read_coordination("run", selected.coordination_key)
        if current_id is not None:
            current = authority.read(current_id)
            if current.state in ACTIVE_STATES:
                lost = mark_owner_lost(authority, current)
                if _same_intent(lost, selected):
                    _notify(on_selected, lost, "follower")
                    return RunOutcome("follower", entry_name, lost, store=authority)
        return _own_run(authority, selected, stdout_sink, stderr_sink, on_selected)
    except KeyboardInterrupt:
        return RunOutcome("owner", entry_name, None, detached=True, store=authority)
    finally:
        lock.release()


def follow_run(
    repo: Path,
    execution_id: str,
    *,
    stdout_sink: BinaryIO | None,
    stderr_sink: BinaryIO | None,
    on_selected: SelectedCallback | None = None,
    namespace: str | None = None,
    store: ExecutionStore | None = None,
) -> RunOutcome:
    workspace = resolve_workspace_identity(repo, namespace=namespace)
    authority = store or ExecutionStore()
    record = _select_run_record(authority, execution_id, workspace)
    record = _reconcile(authority, record)
    _notify(on_selected, record, "follower")
    try:
        final = follow_execution(
            authority,
            record.execution_id,
            stdout_sink=stdout_sink,
            stderr_sink=stderr_sink,
        )
        return RunOutcome("follower", record.subject, final, store=authority)
    except KeyboardInterrupt:
        return RunOutcome(
            "follower",
            record.subject,
            authority.read(record.execution_id),
            detached=True,
            store=authority,
        )


def inspect_run(
    repo: Path,
    execution_id: str,
    *,
    namespace: str | None = None,
    store: ExecutionStore | None = None,
) -> RunOutcome:
    workspace = resolve_workspace_identity(repo, namespace=namespace)
    authority = store or ExecutionStore()
    record = _select_run_record(authority, execution_id, workspace)
    return RunOutcome(
        "inspector", record.subject, _reconcile(authority, record), store=authority
    )


def _own_run(
    store: ExecutionStore,
    selected: ResolvedRun,
    stdout_sink: BinaryIO | None,
    stderr_sink: BinaryIO | None,
    on_selected: SelectedCallback | None,
) -> RunOutcome:
    published = store.publish(
        domain="run",
        operation="execute",
        subject=selected.entry,
        workspace_instance=selected.workspace.instance,
        intent_digest=selected.effective_entry_digest,
        coordination_key=selected.coordination_key,
        argv=selected.argv,
        cwd=selected.cwd,
        env_files=tuple(str(path) for path in selected.env_files),
        capture="split",
    )
    try:
        store.write_coordination(
            "run", selected.coordination_key, published.record.execution_id
        )
        _notify(on_selected, published.record, "owner")
        final = run_foreground(
            store,
            published,
            LaunchSpec(selected.argv, selected.cwd, selected.environment),
            stdout_sink=stdout_sink,
            stderr_sink=stderr_sink,
        )
    except KeyboardInterrupt:
        current = store.read(published.record.execution_id)
        final = settle_unstarted_interruption(store, current)
    return RunOutcome("owner", selected.entry, final, store=store)


def _join_or_claim_after_publication(
    store: ExecutionStore,
    lock: BaseFileLock,
    selected: ResolvedRun,
    pointer_before: str | None,
    pointer_before_active: bool,
    stdout_sink: BinaryIO | None,
    stderr_sink: BinaryIO | None,
    on_selected: SelectedCallback | None,
) -> RunOutcome:
    while True:
        current_id = store.read_coordination("run", selected.coordination_key)
        if current_id is not None:
            current = store.read(current_id)
            # If the pointer already named an active attempt before lock
            # contention, this caller belongs to it even if it settles before
            # the first follow read. A changed pointer is the winner's
            # publication even when that command also settles quickly.
            same_intent = _same_intent(current, selected)
            if same_intent and (
                current.state in ACTIVE_STATES
                or current_id != pointer_before
                or pointer_before_active
            ):
                _notify(on_selected, current, "follower")
                try:
                    final = follow_execution(
                        store,
                        current_id,
                        stdout_sink=stdout_sink,
                        stderr_sink=stderr_sink,
                    )
                    return RunOutcome("follower", selected.entry, final, store=store)
                except KeyboardInterrupt:
                    return RunOutcome(
                        "follower",
                        selected.entry,
                        store.read(current_id),
                        detached=True,
                        store=store,
                    )
        try:
            lock.acquire(timeout=0)
        except Timeout:
            time.sleep(0.02)
            continue
        try:
            after = store.read_coordination("run", selected.coordination_key)
            if after is not None and after != pointer_before:
                record = store.read(after)
                if record.state in ACTIVE_STATES and _same_intent(record, selected):
                    record = mark_owner_lost(store, record)
                    _notify(on_selected, record, "follower")
                    return RunOutcome("follower", selected.entry, record, store=store)
            if pointer_before is not None:
                previous = store.read(pointer_before)
                if previous.state in ACTIVE_STATES and _same_intent(previous, selected):
                    lost = mark_owner_lost(store, previous)
                    _notify(on_selected, lost, "follower")
                    return RunOutcome("follower", selected.entry, lost, store=store)
                if pointer_before_active and _same_intent(previous, selected):
                    _notify(on_selected, previous, "follower")
                    return RunOutcome("follower", selected.entry, previous, store=store)
            return _own_run(store, selected, stdout_sink, stderr_sink, on_selected)
        except KeyboardInterrupt:
            return RunOutcome("owner", selected.entry, None, detached=True, store=store)
        finally:
            lock.release()


def _select_run_record(
    store: ExecutionStore, execution_id: str, workspace: WorkspaceIdentity
) -> ExecutionRecord:
    record = store.read(require_execution_id(execution_id))
    if record.domain != "run":
        raise SvcError(
            "execution-domain-mismatch", "The execution ID does not belong to svc run."
        )
    if record.workspace_instance != workspace.instance:
        raise SvcError(
            "execution-workspace-mismatch",
            "The execution ID belongs to a different workspace.",
        )
    if record.operation != "execute":
        raise SvcError(
            "execution-operation-mismatch",
            "The execution ID does not belong to a run execution operation.",
        )
    return record


def _same_intent(record: ExecutionRecord, selected: ResolvedRun) -> bool:
    return (
        record.domain == "run"
        and record.operation == "execute"
        and record.subject == selected.entry
        and record.intent_digest == selected.effective_entry_digest
    )


def _reconcile(store: ExecutionStore, record: ExecutionRecord) -> ExecutionRecord:
    return reconcile_owner_loss(store, record)


def _notify(
    callback: SelectedCallback | None, record: ExecutionRecord, role: CallerRole
) -> None:
    if callback is not None:
        callback(record, role)


def _resolve_directory(root: Path, configured: str) -> Path:
    path = Path(configured)
    candidate = path.resolve() if path.is_absolute() else (root / path).resolve()
    if not candidate.is_dir():
        raise SvcError(
            "run-cwd-not-directory",
            "Run working directory does not exist.",
            {"cwd": str(candidate)},
        )
    return candidate


def _load_env_files(
    root: Path, configured: list[str]
) -> tuple[tuple[Path, ...], tuple[dict[str, str], ...]]:
    paths: list[Path] = []
    layers: list[dict[str, str]] = []
    for value in configured:
        source = Path(value)
        path = source.resolve() if source.is_absolute() else (root / source).resolve()
        try:
            snapshot = path.read_bytes()
        except OSError as error:
            raise SvcError(
                "run-env-file-unreadable",
                "Declared run environment file cannot be read.",
                {"path": str(path)},
            ) from error
        try:
            text = snapshot.decode("utf-8")
        except UnicodeDecodeError as error:
            raise SvcError(
                "run-env-file-invalid",
                "Declared run environment file must be UTF-8.",
                {"path": str(path)},
            ) from error
        layer: dict[str, str] = {}
        for binding in parse_stream(io.StringIO(text)):
            if binding.error:
                raise SvcError(
                    "run-env-file-invalid",
                    "Declared run environment file contains malformed dotenv syntax.",
                    {"path": str(path)},
                )
            if binding.key is None:
                continue
            if binding.value is None:
                raise SvcError(
                    "run-env-file-invalid",
                    "Declared run environment variable has no value.",
                    {"path": str(path), "key": binding.key},
                )
            _validate_env_pair(binding.key, binding.value)
            _set_environment(layer, binding.key, binding.value)
        paths.append(path)
        layers.append(layer)
    return tuple(paths), tuple(layers)


def _resolve_environment(
    ambient: Mapping[str, str],
    file_layers: tuple[dict[str, str], ...],
    inline: Mapping[str, str],
) -> dict[str, str]:
    result: dict[str, str] = {}
    for layer in (ambient, *file_layers, inline):
        for key, value in layer.items():
            _validate_env_pair(key, value)
            _set_environment(result, key, value)
    return result


def _set_environment(target: dict[str, str], key: str, value: str) -> None:
    if os.name == "nt":
        normalized = key.casefold()
        for existing in tuple(target):
            if existing.casefold() == normalized and existing != key:
                del target[existing]
    target[key] = value


def _validate_env_pair(key: str, value: str) -> None:
    if not key or "=" in key or "\0" in key or "\0" in value:
        raise SvcError(
            "invalid-run-environment",
            "Run environment contains an invalid key or value.",
        )


def _validate_launch(
    argv: list[str],
    cwd: Path,
    env_files: tuple[Path, ...],
    environment: Mapping[str, str],
) -> None:
    values = [*argv, str(cwd), *(str(path) for path in env_files)]
    try:
        for value in values:
            os.fsencode(value)
        for key, value in environment.items():
            os.fsencode(key)
            os.fsencode(value)
    except (UnicodeEncodeError, ValueError) as error:
        raise SvcError(
            "invalid-run-launch-encoding",
            "Run launch values cannot be encoded by this platform.",
        ) from error


def _effective_digest(
    entry: RunEntry,
    cwd: Path,
    env_files: tuple[Path, ...],
    file_layers: tuple[dict[str, str], ...],
) -> str:
    def normalized(layer: Mapping[str, str]) -> list[list[str]]:
        values: dict[str, str] = {}
        for key, value in layer.items():
            values[key.casefold() if os.name == "nt" else key] = value
        return [[key, value] for key, value in sorted(values.items())]

    material = {
        "argv": entry.argv,
        "cwd": str(cwd),
        "env_files": [
            {"path": str(path), "values": normalized(layer)}
            for path, layer in zip(env_files, file_layers, strict=True)
        ],
        "env": normalized(entry.env),
    }
    encoded = json.dumps(
        material,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _digest(*parts: str) -> str:
    return hashlib.sha256("\0".join(parts).encode("utf-8")).hexdigest()[:48]
