"""Private process-attempt authority shared by SVC execution domains."""

from __future__ import annotations

import json
import os
import re
import signal
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import BinaryIO, Callable, Iterator, Literal, Mapping, cast

from filelock import FileLock, Timeout
from platformdirs import user_runtime_dir

from .errors import SvcError


ExecutionDomain = Literal["run", "dev", "double"]
ExecutionState = Literal[
    "starting",
    "running",
    "exited",
    "interrupted",
    "start-failed",
    "capture-failed",
    "owner-lost",
    "released",
]
CapturePolicy = Literal["split", "merged"]

ACTIVE_STATES = frozenset({"starting", "running"})
TERMINAL_STATES = frozenset(
    {
        "exited",
        "interrupted",
        "start-failed",
        "capture-failed",
        "owner-lost",
        "released",
    }
)
_SAFE_COORDINATION_KEY = re.compile(r"^[a-f0-9]{16,64}$")
_SPLIT_STREAMS: tuple[Literal["stdout", "stderr"], ...] = ("stdout", "stderr")


@dataclass(frozen=True)
class LaunchSpec:
    argv: tuple[str, ...]
    cwd: Path
    env: Mapping[str, str]


@dataclass(frozen=True)
class ExecutionRecord:
    execution_id: str
    domain: ExecutionDomain
    operation: str
    subject: str
    workspace_instance: str
    intent_digest: str
    coordination_key: str
    state: ExecutionState
    argv: tuple[str, ...]
    cwd: str
    env_files: tuple[str, ...]
    capture: CapturePolicy
    owner_pid: int
    started_at: str
    started_monotonic_ns: int
    process_id: int | None = None
    finished_at: str | None = None
    duration_ms: int | None = None
    exit_code: int | None = None
    requested_signal: str | None = None
    termination_signal: str | None = None
    failure_reason: str | None = None

    def as_dict(self) -> dict[str, object]:
        result: dict[str, object] = {
            "schema_version": 2,
            "execution_id": self.execution_id,
            "domain": self.domain,
            "operation": self.operation,
            "subject": self.subject,
            "workspace_instance": self.workspace_instance,
            "intent_digest": self.intent_digest,
            "coordination_key": self.coordination_key,
            "state": self.state,
            "argv": list(self.argv),
            "cwd": self.cwd,
            "env_files": list(self.env_files),
            "capture": self.capture,
            "owner_pid": self.owner_pid,
            "started_at": self.started_at,
            "started_monotonic_ns": self.started_monotonic_ns,
        }
        for key in (
            "process_id",
            "finished_at",
            "duration_ms",
            "exit_code",
            "requested_signal",
            "termination_signal",
            "failure_reason",
        ):
            value = getattr(self, key)
            if value is not None:
                result[key] = value
        return result


@dataclass
class PublishedExecution:
    record: ExecutionRecord
    merged_stream: BinaryIO | None = None


@dataclass
class OwnedExecution:
    record: ExecutionRecord
    process: subprocess.Popen[bytes]
    isolated_group: bool


@dataclass(frozen=True)
class ExecutionLogReference:
    stream: str
    path: str
    bytes: int

    def as_dict(self) -> dict[str, object]:
        return {"path": self.path, "bytes": self.bytes}


class ExecutionStore:
    """Strict local record, log, coordination-pointer, and lock storage."""

    def __init__(self, root: Path | None = None) -> None:
        self.root = (
            root or Path(user_runtime_dir("svc", ensure_exists=True)) / "execution"
        )
        _ensure_private_dir(self.root)
        _ensure_private_dir(self.root / "coordination")

    def coordination_lock(
        self, domain: ExecutionDomain, coordination_key: str
    ) -> FileLock:
        _require_coordination_key(coordination_key)
        path = self.root / "coordination" / f"{domain}-{coordination_key}.lock"
        return FileLock(str(path), mode=0o600)

    def read_coordination(
        self, domain: ExecutionDomain, coordination_key: str
    ) -> str | None:
        _require_coordination_key(coordination_key)
        path = self.root / "coordination" / f"{domain}-{coordination_key}.json"
        if not path.exists():
            return None
        value = _read_json(path)
        if (
            set(value) != {"schema_version", "execution_id"}
            or value.get("schema_version") != 2
        ):
            raise _state_error(
                "execution-coordination-invalid",
                "Execution coordination pointer is malformed.",
                path,
            )
        execution_id = require_execution_id(value.get("execution_id"))
        record = self.read(execution_id)
        if record.domain != domain or record.coordination_key != coordination_key:
            raise _state_error(
                "execution-coordination-mismatch",
                "Execution coordination pointer does not match its record.",
                path,
            )
        return execution_id

    def write_coordination(
        self, domain: ExecutionDomain, coordination_key: str, execution_id: str
    ) -> None:
        _require_coordination_key(coordination_key)
        parsed = require_execution_id(execution_id)
        path = self.root / "coordination" / f"{domain}-{coordination_key}.json"
        _atomic_json(path, {"schema_version": 2, "execution_id": parsed})

    def publish(
        self,
        *,
        domain: ExecutionDomain,
        operation: str,
        subject: str,
        workspace_instance: str,
        intent_digest: str,
        coordination_key: str,
        argv: tuple[str, ...],
        cwd: Path,
        env_files: tuple[str, ...] = (),
        capture: CapturePolicy,
    ) -> PublishedExecution:
        _require_coordination_key(coordination_key)
        self._reject_active_legacy_execution()
        execution_id = str(uuid.uuid4())
        directory = self.execution_dir(execution_id)
        try:
            try:
                directory.mkdir(mode=0o700)
            except OSError as error:
                raise _state_error(
                    "execution-storage-failed",
                    "Execution runtime directory could not be created.",
                    directory,
                ) from error
            if capture == "split":
                _create_private_file(directory / "stdout.log").close()
                _create_private_file(directory / "stderr.log").close()
                merged_stream = None
            else:
                merged_stream = _create_private_file(directory / "output.log")
            record = ExecutionRecord(
                execution_id=execution_id,
                domain=domain,
                operation=operation,
                subject=subject,
                workspace_instance=workspace_instance,
                intent_digest=intent_digest,
                coordination_key=coordination_key,
                state="starting",
                argv=argv,
                cwd=str(cwd),
                env_files=env_files,
                capture=capture,
                owner_pid=os.getpid(),
                started_at=_utc_now(),
                started_monotonic_ns=time.monotonic_ns(),
            )
            self.write(record)
            return PublishedExecution(record, merged_stream)
        except BaseException:
            try:
                if "merged_stream" in locals() and merged_stream is not None:
                    merged_stream.close()
            finally:
                pass
            raise

    def read(self, execution_id: object) -> ExecutionRecord:
        parsed = require_execution_id(execution_id)
        path = self.execution_dir(parsed) / "execution.json"
        value = _read_json(path)
        if value.get("schema_version") == 1:
            raise _state_error(
                "execution-record-schema-unsupported",
                "Execution record schema 1 is no longer supported.",
                path,
            )
        try:
            return _record_from_dict(value, expected_id=parsed)
        except (KeyError, TypeError, ValueError) as error:
            raise _state_error(
                "execution-record-invalid", "Execution record is malformed.", path
            ) from error

    def write(self, record: ExecutionRecord) -> None:
        path = self.execution_dir(record.execution_id) / "execution.json"
        _atomic_json(path, record.as_dict())

    def execution_dir(self, execution_id: object) -> Path:
        return self.root / require_execution_id(execution_id)

    def log_path(
        self, record: ExecutionRecord, stream: Literal["stdout", "stderr", "merged"]
    ) -> Path:
        if record.capture == "merged":
            if stream != "merged":
                raise ValueError("merged execution has no attributed stream log")
            name = "output.log"
        else:
            if stream == "merged":
                raise ValueError("split execution has no merged log")
            name = f"{stream}.log"
        return self.execution_dir(record.execution_id) / name

    def log_reference(
        self,
        record: ExecutionRecord,
        stream: Literal["stdout", "stderr", "merged"],
    ) -> ExecutionLogReference:
        path = self.log_path(record, stream)
        try:
            size = path.stat().st_size
        except OSError as error:
            raise _state_error(
                "execution-log-unreadable", "Execution output cannot be read.", path
            ) from error
        return ExecutionLogReference(stream, str(path), size)

    def _reject_active_legacy_execution(self) -> None:
        """Reject only a schema-v1 active attempt whose lifetime lock is held."""

        for path in sorted(self.root.glob("*/execution.json")):
            try:
                value = _read_json(path)
            except SvcError:
                continue
            if (
                value.get("schema_version") != 1
                or value.get("state") not in ACTIVE_STATES
            ):
                continue
            domain = value.get("domain")
            slot_key = value.get("slot_key")
            if domain not in {"run", "dev"} or not isinstance(slot_key, str):
                continue
            try:
                _require_coordination_key(slot_key)
            except SvcError:
                continue
            legacy_lock = FileLock(
                str(self.root / "slots" / f"{domain}-{slot_key}.lock"), mode=0o600
            )
            if not Path(legacy_lock.lock_file).parent.is_dir():
                continue
            try:
                legacy_lock.acquire(timeout=0)
            except Timeout as error:
                raise SvcError(
                    "legacy-execution-active",
                    "A schema-v1 execution is still active; let it settle before starting a new operation.",
                    {"path": str(path)},
                ) from error
            else:
                legacy_lock.release()


def require_execution_id(value: object) -> str:
    if not isinstance(value, str):
        raise SvcError(
            "invalid-execution-id", "Execution ID must be a canonical UUIDv4 string."
        )
    try:
        parsed = uuid.UUID(value)
    except (ValueError, AttributeError) as error:
        raise SvcError(
            "invalid-execution-id", "Execution ID must be a canonical UUIDv4 string."
        ) from error
    if parsed.version != 4 or str(parsed) != value:
        raise SvcError(
            "invalid-execution-id",
            "Execution ID must use canonical lowercase UUIDv4 spelling.",
        )
    return value


def start_isolated(
    store: ExecutionStore,
    published: PublishedExecution,
    spec: LaunchSpec,
) -> OwnedExecution | ExecutionRecord:
    """Start an isolated/null-stdin process using a pre-opened merged log."""

    stream = published.merged_stream
    if stream is None or published.record.capture != "merged":
        raise ValueError("isolated execution requires a pre-opened merged log")
    creationflags, start_new_session = _isolated_carrier()
    try:
        process = subprocess.Popen(
            spec.argv,
            cwd=spec.cwd,
            env=dict(spec.env),
            stdin=subprocess.DEVNULL,
            stdout=stream,
            stderr=subprocess.STDOUT,
            shell=False,
            close_fds=True,
            creationflags=creationflags,
            start_new_session=start_new_session,
        )
    except OSError as error:
        stream.close()
        record = _settle(
            store,
            published.record,
            "start-failed",
            failure_reason=str(error),
        )
        return record
    stream.close()
    record = replace(published.record, state="running", process_id=process.pid)
    try:
        store.write(record)
    except BaseException:
        owned = OwnedExecution(record, process, True)
        _signal_owned_group(owned, signal.SIGTERM)
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            _signal_owned_group(owned, signal.SIGTERM, force=True)
            process.wait()
        raise
    return OwnedExecution(record, process, True)


def run_foreground(
    store: ExecutionStore,
    published: PublishedExecution,
    spec: LaunchSpec,
    *,
    stdout_sink: BinaryIO | None,
    stderr_sink: BinaryIO | None,
) -> ExecutionRecord:
    """Own one foreground process through child settlement and capture EOF."""

    if published.record.capture != "split" or published.merged_stream is not None:
        raise ValueError("foreground execution requires split capture")
    requested: list[int] = []
    capture_failure: list[str] = []
    sink_states = {"stdout": stdout_sink, "stderr": stderr_sink}
    record = published.record
    return_code = 0

    def drain(name: Literal["stdout", "stderr"], source: BinaryIO) -> None:
        log_path = store.log_path(record, name)
        try:
            with log_path.open("ab", buffering=0) as log:
                while chunk := source.read(65_536):
                    log.write(chunk)
                    sink = sink_states[name]
                    if sink is not None:
                        try:
                            sink.write(chunk)
                            sink.flush()
                        except (BrokenPipeError, OSError, ValueError):
                            sink_states[name] = None
        except (OSError, ValueError) as error:
            capture_failure.append(f"{name}: {error}")
            _best_effort_signal(process, signal.SIGTERM)
        finally:
            source.close()

    with _owned_signal_handlers(requested) as bind_process:
        try:
            process = subprocess.Popen(
                spec.argv,
                cwd=spec.cwd,
                env=dict(spec.env),
                stdin=None,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=False,
                close_fds=True,
            )
        except OSError as error:
            if requested:
                return settle_unstarted_interruption(
                    store, published.record, requested[-1]
                )
            return _settle(
                store, published.record, "start-failed", failure_reason=str(error)
            )
        bind_process(process)
        record = replace(published.record, state="running", process_id=process.pid)
        try:
            store.write(record)
        except BaseException:
            _best_effort_signal(process, signal.SIGTERM)
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                _best_effort_kill(process)
                process.wait()
            raise
        assert process.stdout is not None and process.stderr is not None
        readers = (
            threading.Thread(
                target=drain, args=("stdout", process.stdout), daemon=True
            ),
            threading.Thread(
                target=drain, args=("stderr", process.stderr), daemon=True
            ),
        )
        for reader in readers:
            reader.start()
        return_code = process.wait()
        for reader in readers:
            reader.join()

    if capture_failure:
        return _settle(
            store,
            record,
            "capture-failed",
            failure_reason="; ".join(capture_failure),
        )
    posix_signal = os.name != "nt" and return_code < 0
    termination = _signal_name(-return_code) if posix_signal else None
    if requested or posix_signal:
        requested_name = _signal_name(requested[-1]) if requested else None
        return _settle(
            store,
            record,
            "interrupted",
            requested_signal=requested_name,
            termination_signal=termination,
        )
    return _settle(store, record, "exited", exit_code=_normalize_exit_code(return_code))


def wait_owned(
    store: ExecutionStore,
    owned: OwnedExecution,
    *,
    timeout: float | None = None,
) -> ExecutionRecord | None:
    """Settle an isolated bounded command, returning None on caller-owned timeout."""

    try:
        return_code = owned.process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        return None
    posix_signal = os.name != "nt" and return_code < 0
    termination = _signal_name(-return_code) if posix_signal else None
    if posix_signal:
        return _settle(
            store,
            owned.record,
            "interrupted",
            termination_signal=termination,
        )
    return _settle(
        store,
        owned.record,
        "exited",
        exit_code=_normalize_exit_code(return_code),
    )


def terminate_owned(
    store: ExecutionStore,
    owned: OwnedExecution,
    *,
    requested_signal: int = signal.SIGTERM,
) -> ExecutionRecord:
    """Terminate only a process still owned by this attempt."""

    if owned.process.poll() is None:
        _signal_owned_group(owned, requested_signal)
        try:
            owned.process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            _signal_owned_group(owned, signal.SIGTERM, force=True)
            try:
                owned.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                pass
    termination = (
        _signal_name(-owned.process.returncode)
        if owned.process.returncode is not None and owned.process.returncode < 0
        else None
    )
    return _settle(
        store,
        owned.record,
        "interrupted",
        requested_signal=_signal_name(requested_signal),
        termination_signal=termination,
    )


def release_owned(store: ExecutionStore, owned: OwnedExecution) -> ExecutionRecord:
    """Persist release before relinquishing the live child handle."""

    if owned.process.poll() is not None:
        return wait_owned(store, owned) or store.read(owned.record.execution_id)
    return _settle(store, owned.record, "released")


def mark_owner_lost(store: ExecutionStore, record: ExecutionRecord) -> ExecutionRecord:
    """Record an already-proved abandoned active attempt without PID takeover."""

    if record.state not in ACTIVE_STATES:
        return record
    lost = replace(
        record,
        state="owner-lost",
        finished_at=_utc_now(),
        duration_ms=_monotonic_duration_ms(record),
        failure_reason="execution owner released its lifetime lock before settlement",
    )
    store.write(lost)
    return lost


def settle_unstarted_interruption(
    store: ExecutionStore,
    record: ExecutionRecord,
    requested_signal: int = signal.SIGINT,
) -> ExecutionRecord:
    """Settle a published starting attempt interrupted before process creation."""

    if record.state != "starting" or record.process_id is not None:
        return record
    interrupted = replace(
        record,
        state="interrupted",
        finished_at=_utc_now(),
        duration_ms=_monotonic_duration_ms(record),
        requested_signal=_signal_name(requested_signal),
    )
    store.write(interrupted)
    return interrupted


def reconcile_owner_loss(
    store: ExecutionStore, record: ExecutionRecord
) -> ExecutionRecord:
    """Use the abandoned domain lifetime lock as the sole owner-loss proof."""

    if record.state not in ACTIVE_STATES:
        return record
    lock = store.coordination_lock(record.domain, record.coordination_key)
    try:
        lock.acquire(timeout=0)
    except Timeout:
        return store.read(record.execution_id)
    try:
        current = store.read(record.execution_id)
        return (
            mark_owner_lost(store, current)
            if current.state in ACTIVE_STATES
            else current
        )
    finally:
        lock.release()


def follow_execution(
    store: ExecutionStore,
    execution_id: str,
    *,
    stdout_sink: BinaryIO | None,
    stderr_sink: BinaryIO | None,
    poll_interval: float = 0.05,
) -> ExecutionRecord:
    """Replay attributed bytes and follow until the authoritative record settles."""

    record = store.read(execution_id)
    if record.capture != "split":
        raise SvcError(
            "execution-not-followable",
            "This execution has no public attributed output streams.",
        )
    offsets = {"stdout": 0, "stderr": 0}
    sinks = {"stdout": stdout_sink, "stderr": stderr_sink}
    while True:
        for name in ("stdout", "stderr"):
            path = store.log_path(record, name)
            try:
                with path.open("rb") as stream:
                    stream.seek(offsets[name])
                    while chunk := stream.read(65_536):
                        offsets[name] += len(chunk)
                        sink = sinks[name]
                        if sink is not None:
                            try:
                                sink.write(chunk)
                                sink.flush()
                            except (BrokenPipeError, OSError, ValueError):
                                sinks[name] = None
            except OSError as error:
                raise _state_error(
                    "execution-log-unreadable", "Execution output cannot be read.", path
                ) from error
        record = reconcile_owner_loss(store, store.read(execution_id))
        if record.state in TERMINAL_STATES:
            # The owner writes terminal state only after EOF; one final pass
            # covers bytes published between this loop's read and state read.
            drained = True
            for stream_name in _SPLIT_STREAMS:
                path = store.log_path(record, stream_name)
                try:
                    size = path.stat().st_size
                except OSError as error:
                    raise _state_error(
                        "execution-log-unreadable",
                        "Execution output cannot be read.",
                        path,
                    ) from error
                if size != offsets[stream_name]:
                    drained = False
            if drained:
                return record
            continue
        time.sleep(poll_interval)


def wait_execution(
    store: ExecutionStore, execution_id: str, *, poll_interval: float = 0.05
) -> ExecutionRecord:
    while True:
        record = reconcile_owner_loss(store, store.read(execution_id))
        if record.state in TERMINAL_STATES:
            return record
        time.sleep(poll_interval)


def _settle(
    store: ExecutionStore,
    record: ExecutionRecord,
    state: ExecutionState,
    *,
    exit_code: int | None = None,
    requested_signal: str | None = None,
    termination_signal: str | None = None,
    failure_reason: str | None = None,
) -> ExecutionRecord:
    settled = replace(
        record,
        state=state,
        finished_at=_utc_now(),
        duration_ms=_monotonic_duration_ms(record),
        exit_code=exit_code,
        requested_signal=requested_signal,
        termination_signal=termination_signal,
        failure_reason=failure_reason,
    )
    store.write(settled)
    return settled


def _normalize_exit_code(return_code: int, *, platform_name: str = os.name) -> int:
    """Expose a Windows DWORD exit status as its signed 32-bit value."""

    if platform_name == "nt" and return_code >= 1 << 31:
        return return_code - (1 << 32)
    return return_code


@contextmanager
def _owned_signal_handlers(
    requested: list[int],
) -> Iterator[Callable[[subprocess.Popen[bytes]], None]]:
    if threading.current_thread() is not threading.main_thread():
        yield lambda _process: None
        return
    handled = tuple(
        number for number in (signal.SIGINT, signal.SIGTERM) if number is not None
    )
    previous = {number: signal.getsignal(number) for number in handled}
    terminal_group_delivery = _terminal_group_delivery()
    process_holder: list[subprocess.Popen[bytes]] = []
    deferred: list[int] = []

    def forward(
        process: subprocess.Popen[bytes], number: int, *, force: bool = False
    ) -> None:
        if force or number != signal.SIGINT or not terminal_group_delivery:
            _best_effort_signal(process, number)

    def on_signal(number: int, _frame: object) -> None:
        requested.append(number)
        if process_holder:
            forward(process_holder[0], number)
        else:
            deferred.append(number)

    def bind_process(process: subprocess.Popen[bytes]) -> None:
        process_holder.append(process)
        for number in deferred:
            forward(process, number, force=True)
        deferred.clear()

    try:
        for number in handled:
            signal.signal(number, on_signal)
        yield bind_process
    finally:
        for number, handler in previous.items():
            signal.signal(number, handler)


def _terminal_group_delivery() -> bool:
    if os.name == "nt" or not sys.stdin.isatty() or not hasattr(os, "tcgetpgrp"):
        return False
    try:
        return os.tcgetpgrp(sys.stdin.fileno()) == os.getpgrp()
    except OSError:
        return False


def _best_effort_signal(process: subprocess.Popen[bytes], number: int) -> None:
    try:
        if process.poll() is None:
            process.send_signal(number)
    except OSError:
        pass


def _best_effort_kill(process: subprocess.Popen[bytes]) -> None:
    try:
        if process.poll() is None:
            process.kill()
    except OSError:
        pass


def _signal_owned_group(
    owned: OwnedExecution, number: int, *, force: bool = False
) -> None:
    try:
        if os.name == "nt" and owned.isolated_group:
            subprocess.run(
                (
                    "taskkill",
                    "/PID",
                    str(owned.process.pid),
                    "/T",
                    "/F",
                ),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
        elif owned.isolated_group:
            os.killpg(
                owned.process.pid,
                getattr(signal, "SIGKILL", signal.SIGTERM) if force else number,
            )
        elif force:
            owned.process.kill()
        else:
            owned.process.send_signal(number)
    except OSError:
        pass


def _isolated_carrier() -> tuple[int, bool]:
    """Return the smallest platform launch boundary for a detached attempt."""

    if os.name == "nt":
        return (
            getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
            | getattr(subprocess, "DETACHED_PROCESS", 0)
            | getattr(subprocess, "CREATE_BREAKAWAY_FROM_JOB", 0),
            False,
        )
    return 0, True


def _signal_name(number: int) -> str:
    try:
        return signal.Signals(number).name
    except ValueError:
        return f"SIGNAL_{number}"


def _record_from_dict(value: dict[str, object], *, expected_id: str) -> ExecutionRecord:
    required = {
        "schema_version",
        "execution_id",
        "domain",
        "operation",
        "subject",
        "workspace_instance",
        "intent_digest",
        "coordination_key",
        "state",
        "argv",
        "cwd",
        "env_files",
        "capture",
        "owner_pid",
        "started_at",
        "started_monotonic_ns",
    }
    optional = {
        "process_id",
        "finished_at",
        "duration_ms",
        "exit_code",
        "requested_signal",
        "termination_signal",
        "failure_reason",
    }
    if (
        set(value) - required - optional
        or required - set(value)
        or type(value["schema_version"]) is not int
        or value["schema_version"] != 2
    ):
        raise ValueError("record fields do not match schema")
    execution_id = require_execution_id(value["execution_id"])
    if execution_id != expected_id:
        raise ValueError("record ID does not match path")
    domain = value["domain"]
    state = value["state"]
    capture = value["capture"]
    if (
        domain not in {"run", "dev", "double"}
        or state not in ACTIVE_STATES | TERMINAL_STATES
        or capture not in {"split", "merged"}
    ):
        raise ValueError("record enum is invalid")
    strings = (
        "operation",
        "subject",
        "workspace_instance",
        "intent_digest",
        "coordination_key",
        "cwd",
        "started_at",
    )
    if any(not isinstance(value[key], str) or not value[key] for key in strings):
        raise TypeError("record string is invalid")
    _require_coordination_key(str(value["coordination_key"]))
    argv = value["argv"]
    env_files = value["env_files"]
    if (
        not isinstance(argv, list)
        or not argv
        or not all(isinstance(item, str) for item in argv)
    ):
        raise TypeError("record argv is invalid")
    if not argv[0]:
        raise ValueError("record executable is empty")
    if not isinstance(env_files, list) or not all(
        isinstance(item, str) for item in env_files
    ):
        raise TypeError("record env_files is invalid")
    owner_pid = value["owner_pid"]
    if type(owner_pid) is not int or owner_pid <= 0:
        raise TypeError("record owner PID is invalid")
    started_monotonic_ns = value["started_monotonic_ns"]
    if type(started_monotonic_ns) is not int or started_monotonic_ns < 0:
        raise TypeError("record monotonic start is invalid")
    integer_fields = ("process_id", "duration_ms", "exit_code")
    for key in integer_fields:
        if key in value and type(value[key]) is not int:
            raise TypeError(f"record {key} is invalid")
    for key in (
        "finished_at",
        "requested_signal",
        "termination_signal",
        "failure_reason",
    ):
        if key in value and not isinstance(value[key], str):
            raise TypeError(f"record {key} is invalid")
    _validate_record_lifecycle(value, str(domain), str(state), str(capture))
    return ExecutionRecord(
        execution_id=execution_id,
        domain=cast(ExecutionDomain, domain),
        operation=str(value["operation"]),
        subject=str(value["subject"]),
        workspace_instance=str(value["workspace_instance"]),
        intent_digest=str(value["intent_digest"]),
        coordination_key=str(value["coordination_key"]),
        state=cast(ExecutionState, state),
        argv=tuple(argv),
        cwd=str(value["cwd"]),
        env_files=tuple(env_files),
        capture=cast(CapturePolicy, capture),
        owner_pid=owner_pid,
        started_at=str(value["started_at"]),
        started_monotonic_ns=started_monotonic_ns,
        process_id=cast(int | None, value.get("process_id")),
        finished_at=cast(str | None, value.get("finished_at")),
        duration_ms=cast(int | None, value.get("duration_ms")),
        exit_code=(
            _normalize_exit_code(cast(int, value["exit_code"]), platform_name="nt")
            if "exit_code" in value
            else None
        ),
        requested_signal=cast(str | None, value.get("requested_signal")),
        termination_signal=cast(str | None, value.get("termination_signal")),
        failure_reason=cast(str | None, value.get("failure_reason")),
    )


def _validate_record_lifecycle(
    value: dict[str, object],
    domain: str,
    state: str,
    capture: str,
) -> None:
    if (domain == "run" and capture != "split") or (
        domain in {"dev", "double"} and capture != "merged"
    ):
        raise ValueError("record capture policy does not match domain")
    if domain == "run" and state == "released":
        raise ValueError("run execution cannot be released")
    _parse_timestamp(str(value["started_at"]))
    terminal = state in TERMINAL_STATES
    has_finished = "finished_at" in value and "duration_ms" in value
    if terminal != has_finished:
        raise ValueError("record settlement fields do not match state")
    if "finished_at" in value:
        _parse_timestamp(str(value["finished_at"]))
    duration = value.get("duration_ms")
    if isinstance(duration, int) and duration < 0:
        raise ValueError("record duration is negative")
    process_id = value.get("process_id")
    if process_id is not None and (type(process_id) is not int or process_id <= 0):
        raise ValueError("record process ID is invalid")
    if state == "starting" and process_id is not None:
        raise ValueError("starting record cannot have a process ID")
    if (
        state in {"running", "exited", "capture-failed", "released"}
        and process_id is None
    ):
        raise ValueError("started record requires a process ID")
    if (
        state == "interrupted"
        and process_id is None
        and "requested_signal" not in value
    ):
        raise ValueError("unstarted interruption requires the requested signal")
    if state == "exited":
        exit_code = value.get("exit_code")
        if type(exit_code) is not int or exit_code < -(1 << 31) or exit_code >= 1 << 32:
            raise ValueError("exited record requires a 32-bit exit code")
    elif "exit_code" in value:
        raise ValueError("non-exit record cannot have an exit code")


def _parse_timestamp(value: str) -> datetime:
    if not value.endswith("Z"):
        raise ValueError("record timestamp is not UTC RFC 3339")
    parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    if parsed.tzinfo != timezone.utc:
        raise ValueError("record timestamp is not UTC")
    return parsed


def _read_json(path: Path) -> dict[str, object]:
    try:
        raw = path.read_bytes()
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_constant,
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        raise _state_error(
            "execution-state-unreadable", "Execution state cannot be read safely.", path
        ) from error
    if not isinstance(value, dict) or _contains_null(value):
        raise _state_error(
            "execution-state-invalid",
            "Execution state must be a strict JSON object.",
            path,
        )
    return value


def _atomic_json(path: Path, value: Mapping[str, object]) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    payload = (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")
    descriptor = -1
    temporary = ""
    try:
        descriptor, temporary = tempfile.mkstemp(
            prefix=f".{path.name}.", dir=path.parent
        )
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "wb") as stream:
            descriptor = -1
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except OSError as error:
        if descriptor >= 0:
            os.close(descriptor)
        if temporary:
            try:
                os.unlink(temporary)
            except OSError:
                pass
        raise _state_error(
            "execution-storage-failed", "Execution state could not be persisted.", path
        ) from error


def _create_private_file(path: Path) -> BinaryIO:
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        return os.fdopen(descriptor, "wb", buffering=0)
    except OSError as error:
        raise _state_error(
            "execution-storage-failed",
            "Execution output storage could not be created.",
            path,
        ) from error


def _ensure_private_dir(path: Path) -> None:
    try:
        path.mkdir(mode=0o700, parents=True, exist_ok=True)
    except OSError as error:
        raise _state_error(
            "execution-storage-failed",
            "Execution runtime directory is unavailable.",
            path,
        ) from error


def _require_coordination_key(value: str) -> None:
    if not _SAFE_COORDINATION_KEY.fullmatch(value):
        raise SvcError(
            "invalid-execution-coordination",
            "Execution coordination key is invalid.",
        )


def _state_error(code: str, message: str, path: Path) -> SvcError:
    return SvcError(code, message, {"path": str(path)})


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate key {key!r}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-finite value {value!r}")


def _contains_null(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, dict):
        return any(_contains_null(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_null(item) for item in value)
    return False


def _utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


def _monotonic_duration_ms(record: ExecutionRecord) -> int:
    return max(0, (time.monotonic_ns() - record.started_monotonic_ns) // 1_000_000)
