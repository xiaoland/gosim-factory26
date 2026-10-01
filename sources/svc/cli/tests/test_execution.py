from __future__ import annotations

import io
import json
import os
import signal
import subprocess
import sys
import uuid
from pathlib import Path

import pytest
from filelock import FileLock, Timeout

from svc_cli._execution import (
    ExecutionStore,
    LaunchSpec,
    follow_execution,
    release_owned,
    run_foreground,
    start_isolated,
    terminate_owned,
    wait_owned,
)
from svc_cli.errors import SvcError


COORDINATION = "a" * 48


def publish(store: ExecutionStore, *, domain: str = "run", capture: str = "split"):
    operations = {"run": "execute", "dev": "ensure", "double": "carrier"}
    return store.publish(
        domain=domain,  # type: ignore[arg-type]
        operation=operations[domain],
        subject="check",
        workspace_instance="workspace",
        intent_digest="digest",
        coordination_key=COORDINATION,
        argv=(sys.executable, "-c", "pass"),
        cwd=store.root,
        capture=capture,  # type: ignore[arg-type]
    )


def test_record_coordination_round_trip(tmp_path: Path) -> None:
    store = ExecutionStore(tmp_path / "runtime")
    published = publish(store)
    store.write_coordination("run", COORDINATION, published.record.execution_id)
    assert store.read_coordination("run", COORDINATION) == published.record.execution_id
    assert store.read(published.record.execution_id) == published.record


def test_publish_classifies_execution_directory_creation_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = ExecutionStore(tmp_path / "runtime")
    original_mkdir = Path.mkdir

    def fail_execution_directory(path: Path, *args: object, **kwargs: object) -> None:
        if path.parent == store.root:
            raise PermissionError("read-only runtime")
        original_mkdir(path, *args, **kwargs)

    monkeypatch.setattr(Path, "mkdir", fail_execution_directory)

    with pytest.raises(SvcError) as caught:
        publish(store)

    assert caught.value.code == "execution-storage-failed"


def test_foreground_capture_preserves_binary_streams_and_sink_failure(
    tmp_path: Path,
) -> None:
    store = ExecutionStore(tmp_path / "runtime")
    published = store.publish(
        domain="run",
        operation="execute",
        subject="binary",
        workspace_instance="workspace",
        intent_digest="digest",
        coordination_key=COORDINATION,
        argv=(sys.executable,),
        cwd=tmp_path,
        capture="split",
    )

    class ClosedSink(io.BytesIO):
        def write(self, data: bytes) -> int:
            raise BrokenPipeError

    spec = LaunchSpec(
        (
            sys.executable,
            "-c",
            "import os; os.write(1, b'out\\xff'); os.write(2, b'err\\xfe')",
        ),
        tmp_path,
        os.environ.copy(),
    )
    stderr = io.BytesIO()
    record = run_foreground(
        store, published, spec, stdout_sink=ClosedSink(), stderr_sink=stderr
    )
    assert record.state == "exited"
    assert record.exit_code == 0
    assert store.log_path(record, "stdout").read_bytes() == b"out\xff"
    assert store.log_path(record, "stderr").read_bytes() == b"err\xfe"
    assert stderr.getvalue() == b"err\xfe"

    replay_out = io.BytesIO()
    replay_err = io.BytesIO()
    followed = follow_execution(
        store, record.execution_id, stdout_sink=replay_out, stderr_sink=replay_err
    )
    assert followed == record
    assert replay_out.getvalue() == b"out\xff"
    assert replay_err.getvalue() == b"err\xfe"


def test_reader_normalizes_a_persisted_windows_dword_exit_status(
    tmp_path: Path,
) -> None:
    store = ExecutionStore(tmp_path / "runtime")
    published = publish(store)
    record = run_foreground(
        store,
        published,
        LaunchSpec(
            (sys.executable, "-c", "raise SystemExit(7)"), tmp_path, os.environ.copy()
        ),
        stdout_sink=None,
        stderr_sink=None,
    )
    record_path = store.execution_dir(record.execution_id) / "execution.json"
    value = json.loads(record_path.read_text(encoding="utf-8"))
    value["exit_code"] = 4_294_963_238
    record_path.write_text(json.dumps(value), encoding="utf-8")

    assert store.read(record.execution_id).exit_code == -4_058


def test_foreground_log_open_failure_is_a_capture_failure(tmp_path: Path) -> None:
    store = ExecutionStore(tmp_path / "runtime")
    published = publish(store)
    stdout_log = store.log_path(published.record, "stdout")
    stdout_log.unlink()
    stdout_log.mkdir()

    record = run_foreground(
        store,
        published,
        LaunchSpec(
            (sys.executable, "-c", "print('output')"), tmp_path, os.environ.copy()
        ),
        stdout_sink=None,
        stderr_sink=None,
    )

    assert record.state == "capture-failed"
    assert record.failure_reason is not None and "stdout" in record.failure_reason


def test_start_failure_is_a_published_execution_outcome(tmp_path: Path) -> None:
    store = ExecutionStore(tmp_path / "runtime")
    published = publish(store)
    result = run_foreground(
        store,
        published,
        LaunchSpec((str(tmp_path / "missing-command"),), tmp_path, os.environ.copy()),
        stdout_sink=None,
        stderr_sink=None,
    )
    assert result.state == "start-failed"
    assert result.failure_reason
    assert store.read(result.execution_id) == result


def test_isolated_execution_can_settle_release_or_be_terminated(tmp_path: Path) -> None:
    store = ExecutionStore(tmp_path / "runtime")
    bounded = publish(store, domain="dev", capture="merged")
    started = start_isolated(
        store,
        bounded,
        LaunchSpec(
            (sys.executable, "-c", "print('activated')"), tmp_path, os.environ.copy()
        ),
    )
    assert not hasattr(started, "state")
    settled = wait_owned(store, started)  # type: ignore[arg-type]
    assert settled is not None and settled.state == "exited"
    assert store.log_path(settled, "merged").read_bytes() == b"activated\n"

    long_lived = publish(store, domain="dev", capture="merged")
    owned = start_isolated(
        store,
        long_lived,
        LaunchSpec(
            (sys.executable, "-c", "import time; time.sleep(30)"),
            tmp_path,
            os.environ.copy(),
        ),
    )
    assert not hasattr(owned, "state")
    released = release_owned(store, owned)  # type: ignore[arg-type]
    assert released.state == "released"
    os.kill(int(released.process_id), signal.SIGTERM)

    terminated_launch = publish(store, domain="dev", capture="merged")
    terminate_candidate = start_isolated(
        store,
        terminated_launch,
        LaunchSpec(
            (sys.executable, "-c", "import time; time.sleep(30)"),
            tmp_path,
            os.environ.copy(),
        ),
    )
    terminated = terminate_owned(store, terminate_candidate)  # type: ignore[arg-type]
    assert terminated.state == "interrupted"
    assert terminated.requested_signal == "SIGTERM"


def test_double_execution_requires_merged_capture_and_can_be_released(
    tmp_path: Path,
) -> None:
    store = ExecutionStore(tmp_path / "runtime")
    split = publish(store, domain="double", capture="split")

    with pytest.raises(SvcError) as rejected:
        store.read(split.record.execution_id)
    assert rejected.value.code == "execution-record-invalid"

    merged = publish(store, domain="double", capture="merged")
    started = start_isolated(
        store,
        merged,
        LaunchSpec(
            (sys.executable, "-c", "import time; time.sleep(30)"),
            tmp_path,
            os.environ.copy(),
        ),
    )
    assert not hasattr(started, "state")
    try:
        released = release_owned(store, started)  # type: ignore[arg-type]
        assert released.domain == "double"
        assert released.capture == "merged"
        assert released.state == "released"
        assert store.read(released.execution_id) == released
    finally:
        started.process.terminate()  # type: ignore[union-attr]
        started.process.wait(timeout=3)  # type: ignore[union-attr]


def test_lifetime_coordination_lock_is_cross_process_authority(tmp_path: Path) -> None:
    store = ExecutionStore(tmp_path / "runtime")
    lock = store.coordination_lock("run", COORDINATION)
    with lock.acquire(timeout=0):
        completed = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "from filelock import FileLock, Timeout; import sys; "
                    f"lock=FileLock({str(lock.lock_file)!r}); "
                    "\ntry: lock.acquire(timeout=0)\nexcept Timeout: sys.exit(0)\nsys.exit(1)"
                ),
            ],
            check=False,
            timeout=5,
        )
        assert completed.returncode == 0
    try:
        with lock.acquire(timeout=0):
            pass
    except Timeout:
        pytest.fail("coordination lock remained held after owner release")


def test_active_schema_one_attempt_blocks_new_publication_without_translation(
    tmp_path: Path,
) -> None:
    store = ExecutionStore(tmp_path / "runtime")
    legacy_id = str(uuid.uuid4())
    legacy_dir = store.root / legacy_id
    legacy_dir.mkdir()
    (legacy_dir / "execution.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "domain": "run",
                "state": "running",
                "slot_key": COORDINATION,
            }
        ),
        encoding="utf-8",
    )
    slots = store.root / "slots"
    slots.mkdir()
    legacy_lock = slots / f"run-{COORDINATION}.lock"

    with (
        FileLock(str(legacy_lock)).acquire(timeout=0),
        pytest.raises(SvcError) as raised,
    ):
        publish(store)

    assert raised.value.code == "legacy-execution-active"
    with pytest.raises(SvcError) as unsupported:
        store.read(legacy_id)
    assert unsupported.value.code == "execution-record-schema-unsupported"

    published = publish(store)
    assert published.record.operation == "execute"
    assert published.record.coordination_key == COORDINATION
