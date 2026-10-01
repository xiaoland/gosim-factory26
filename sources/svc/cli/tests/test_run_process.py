from __future__ import annotations

import json
import os
import re
import selectors
import signal
import subprocess
import sys
import time
from contextlib import suppress
from pathlib import Path

import pytest

from svc_cli_test_support.project_contract import write_project_config


EXECUTION_ID = re.compile(rb"owner ([0-9a-f-]{36})\n")


def svc_command(root: Path, *arguments: str, ready: Path | None = None) -> list[str]:
    runtime_root = root / "svc-test-runtime"
    bootstrap = (
        "import svc_cli._execution as execution; "
        f"execution.user_runtime_dir=lambda *_args, **_kwargs: {str(runtime_root)!r}; "
        + (
            "from pathlib import Path; import svc_cli.run.runtime as run_runtime; "
            "original_follow=run_runtime.follow_execution; "
            f"run_runtime.follow_execution=lambda *args, **kwargs: (Path({str(ready)!r}).write_text('yes'), original_follow(*args, **kwargs))[1]; "
            if ready
            else ""
        )
        + "from svc_cli.cli import main; "
        + "raise SystemExit(main())"
    )
    return [sys.executable, "-c", bootstrap, *arguments]


def write_run(root: Path, script: str) -> None:
    write_project_config(
        root,
        run_entries={"check": {"argv": [sys.executable, "-c", script]}},
    )


def start_owner(root: Path) -> tuple[subprocess.Popen[bytes], str]:
    process = subprocess.Popen(
        svc_command(root, "run", "check", "--repo", str(root)),
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert process.stderr is not None
    selector = selectors.DefaultSelector()
    selector.register(process.stderr, selectors.EVENT_READ)
    if not selector.select(timeout=5):
        process.kill()
        stdout, stderr = process.communicate(timeout=5)
        pytest.fail(f"owner startup timed out\nstdout={stdout!r}\nstderr={stderr!r}")
    header = process.stderr.readline()
    match = EXECUTION_ID.search(header)
    assert match, header
    return process, match.group(1).decode("ascii")


@pytest.mark.skipif(os.name == "nt", reason="POSIX signal projection")
def test_owner_sigint_settles_shared_execution_and_preserves_foreground_group(
    tmp_path: Path,
) -> None:
    child_pgrp = tmp_path / "child-pgrp"
    script = (
        "from pathlib import Path; import os,time; "
        f"Path({str(child_pgrp)!r}).write_text(str(os.getpgrp())); "
        "time.sleep(30)"
    )
    write_run(tmp_path, script)
    owner, execution_id = start_owner(tmp_path)
    try:
        deadline = time.monotonic() + 5
        while not child_pgrp.exists() and time.monotonic() < deadline:
            time.sleep(0.02)
        assert child_pgrp.exists()
        assert int(child_pgrp.read_text()) == os.getpgid(owner.pid)
        os.kill(owner.pid, signal.SIGINT)
        stdout, stderr = owner.communicate(timeout=5)
        assert owner.returncode == 130
        assert stdout == b""
        assert b"interrupted" in stderr

        inspected = subprocess.run(
            svc_command(
                tmp_path,
                "run",
                "--inspect",
                execution_id,
                "--repo",
                str(tmp_path),
                "--json",
            ),
            cwd=tmp_path,
            capture_output=True,
            check=False,
            timeout=5,
        )
        assert inspected.returncode == 0
        assert json.loads(inspected.stdout)["state"] == "interrupted"
    finally:
        if owner.poll() is None:
            owner.kill()
            owner.wait(timeout=5)


@pytest.mark.skipif(os.name == "nt", reason="POSIX signal projection")
def test_follower_sigint_detaches_without_interrupting_owner(tmp_path: Path) -> None:
    started = tmp_path / "started"
    write_run(
        tmp_path,
        f"from pathlib import Path; import time; Path({str(started)!r}).write_text('yes'); time.sleep(2)",
    )
    owner, execution_id = start_owner(tmp_path)
    follower_ready = tmp_path / "follower-ready"
    follower = subprocess.Popen(
        svc_command(
            tmp_path,
            "run",
            "--follow",
            execution_id,
            "--repo",
            str(tmp_path),
            "--json",
            ready=follower_ready,
        ),
        cwd=tmp_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        deadline = time.monotonic() + 5
        while not follower_ready.exists() and time.monotonic() < deadline:
            time.sleep(0.02)
        assert follower_ready.exists()
        os.kill(follower.pid, signal.SIGINT)
        follower_stdout, follower_stderr = follower.communicate(timeout=5)
        assert follower.returncode == 130
        assert follower_stderr == b""
        detached = json.loads(follower_stdout)
        assert detached["caller_status"] == "detached"
        assert detached["execution_id"] == execution_id
        owner.communicate(timeout=5)
        assert owner.returncode == 0
    finally:
        for process in (follower, owner):
            if process.poll() is None:
                process.kill()
                process.wait(timeout=5)


@pytest.mark.skipif(os.name == "nt", reason="POSIX uncatchable owner loss")
def test_owner_loss_is_reconciled_without_same_invocation_replacement(
    tmp_path: Path,
) -> None:
    counter = tmp_path / "counter"
    orphan_pid = tmp_path / "orphan-pid"
    script = (
        "from pathlib import Path; import os,time; "
        f"counter=Path({str(counter)!r}); n=int(counter.read_text())+1 if counter.exists() else 1; counter.write_text(str(n)); "
        f"Path({str(orphan_pid)!r}).write_text(str(os.getpid())) if n == 1 else None; "
        "time.sleep(30) if n == 1 else None"
    )
    write_run(tmp_path, script)
    owner, execution_id = start_owner(tmp_path)
    orphan = None
    follower: subprocess.Popen[bytes] | None = None
    try:
        deadline = time.monotonic() + 5
        while not orphan_pid.exists() and time.monotonic() < deadline:
            time.sleep(0.02)
        orphan = int(orphan_pid.read_text())
        follower = subprocess.Popen(
            svc_command(
                tmp_path,
                "run",
                "--follow",
                execution_id,
                "--repo",
                str(tmp_path),
                "--json",
            ),
            cwd=tmp_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        time.sleep(0.1)
        os.kill(owner.pid, signal.SIGKILL)
        owner.wait(timeout=5)
        follower_stdout, follower_stderr = follower.communicate(timeout=5)
        assert follower.returncode == 4
        assert follower_stderr == b""
        assert json.loads(follower_stdout)["state"] == "owner-lost"

        inspected = subprocess.run(
            svc_command(
                tmp_path,
                "run",
                "--inspect",
                execution_id,
                "--repo",
                str(tmp_path),
                "--json",
            ),
            cwd=tmp_path,
            capture_output=True,
            check=False,
            timeout=5,
        )
        assert inspected.returncode == 0
        assert json.loads(inspected.stdout)["state"] == "owner-lost"
        assert counter.read_text() == "1"

        later = subprocess.run(
            svc_command(tmp_path, "run", "check", "--repo", str(tmp_path), "--json"),
            cwd=tmp_path,
            capture_output=True,
            check=False,
            timeout=5,
        )
        assert later.returncode == 0
        assert json.loads(later.stdout)["execution_id"] != execution_id
        assert counter.read_text() == "2"
    finally:
        if owner.poll() is None:
            owner.kill()
            owner.wait(timeout=5)
        if follower is not None and follower.poll() is None:
            follower.kill()
            follower.wait(timeout=5)
        if orphan is not None:
            with suppress(ProcessLookupError):
                os.kill(orphan, signal.SIGTERM)
