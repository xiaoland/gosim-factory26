from __future__ import annotations

import os
import signal
import socket
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

from svc_cli._execution import ExecutionStore
from svc_cli.config import ExecProbe, HttpProbe, TargetConfig
from svc_cli.dev.runtime import (
    DevEnsureResult,
    DevStopResult,
    DevTargetObservation,
    ensure_target,
    inspect_dev_status,
    stop_target,
)
from svc_cli.dev.readiness import probe_exec, probe_http, probe_target
from svc_cli.errors import SvcError
from svc_cli.workspace import resolve_workspace_identity
from svc_cli_test_support.project_contract import write_project_config


class _Response:
    def __init__(self, status: int) -> None:
        self.status = status

    def close(self) -> None:
        pass


def test_http_probe_enforces_loopback_and_treats_redirect_as_an_observation() -> None:
    probe = HttpProbe(
        kind="http", url="http://app.localhost/health", success_status=[200, 299]
    )
    observed = probe_http(
        probe,
        probe.url,
        timeout=1,
        resolver=lambda host, port: ("127.0.0.1",),
        opener=lambda method, path, headers, timeout: _Response(302),
    )
    assert not observed.healthy
    assert observed.responded
    assert observed.status_code == 302
    with pytest.raises(SvcError, match="outside loopback"):
        probe_http(
            probe,
            probe.url,
            timeout=1,
            resolver=lambda host, port: ("198.51.100.10",),
            opener=lambda method, path, headers, timeout: _Response(200),
        )


def test_http_probe_pins_the_validated_address_instead_of_resolving_again() -> None:
    requests: list[tuple[str, str]] = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802 - stdlib handler contract
            requests.append((self.path, self.headers["Host"]))
            self.send_response(302)
            self.send_header("Location", "/followed")
            self.end_headers()

        def log_message(self, format: str, *args: object) -> None:
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        probe = HttpProbe(
            kind="http",
            url=f"http://unresolvable.example:{server.server_port}/",
            success_status=[200, 299],
        )
        observed = probe_http(
            probe, probe.url, timeout=1, resolver=lambda host, port: ("127.0.0.1",)
        )
        assert not observed.healthy
        assert observed.status_code == 302
        assert requests == [("/", f"unresolvable.example:{server.server_port}")]
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def test_exec_probe_enforces_its_declared_output_limit() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        probe = ExecProbe(
            kind="exec",
            argv=[sys.executable, "-c", "print('x' * 100)"],
            output_limit=10,
        )
        result = probe_exec(probe, tuple(probe.argv), Path(tmp), timeout=1)
        assert not result.healthy
        assert result.reason == "output-limit"
        assert result.output_truncated
        assert result.output_bytes == 10


def test_worktree_scope_refuses_static_probe_and_manual_never_provisions() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        workspace = resolve_workspace_identity(root, namespace="fixture")
        static = TargetConfig(
            probe={"kind": "http", "url": "http://127.0.0.1:1/health"},
            provision={"kind": "manual"},
        )
        with pytest.raises(SvcError, match="provenance"):
            probe_target(static, workspace, target_name="app")

        write_target(
            root,
            "manual",
            {
                "scope": "repository",
                "probe": {
                    "kind": "exec",
                    "argv": [
                        sys.executable,
                        "-c",
                        "print('bounded diagnostic'); raise SystemExit(1)",
                    ],
                },
                "provision": {"kind": "manual"},
                "access": ["offline-receipt"],
            },
        )
        status = inspect_dev_status(root, namespace="fixture")
        assert status.targets is not None and len(status.targets) == 1
        observed = status.targets[0]
        assert isinstance(observed, DevTargetObservation)
        assert observed.probe.output == "bounded diagnostic\n"
        assert observed.continuation == "manual-action-required"
        assert observed.access == ("offline-receipt",)

        result = ensure_target(root, "manual", namespace="fixture")
        assert result.status == "manual-action-required"
        assert result.probe is not None
        assert result.probe.output == "bounded diagnostic\n"
        assert result.access == ("offline-receipt",)


def test_owned_early_exit_reports_only_attempt_cleanup() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        store = ExecutionStore(root / "runtime")
        write_target(
            root,
            "fails",
            {
                "scope": "repository",
                "readiness_timeout": 1,
                "poll_interval": 0.01,
                "probe": {
                    "kind": "exec",
                    "argv": [
                        sys.executable,
                        "-c",
                        "import sys; sys.exit(1)",
                    ],
                },
                "provision": {
                    "kind": "exec",
                    "mode": "run",
                    "argv": [
                        sys.executable,
                        "-c",
                        "import sys; sys.exit(0)",
                    ],
                },
            },
        )
        result = ensure_target(root, "fails", namespace="fixture", store=store)
        assert result.status == "child-exit"
        assert result.cleanup == "completed"
        assert result.attempt is not None
        assert result.attempt.logs.merged.path.endswith("output.log")


def test_concurrent_ensure_starts_once_then_reuses_the_declared_server() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        store = ExecutionStore(root / "runtime")
        port = free_port()
        counter = root / "starts.txt"
        server = (
            "from pathlib import Path; import http.server; "
            f"Path({str(counter)!r}).open('a').write('1\\n'); "
            f"http.server.HTTPServer(('127.0.0.1', {port}), http.server.SimpleHTTPRequestHandler).serve_forever()"
        )
        write_target(
            root,
            "server",
            {
                "scope": "repository",
                "readiness_timeout": 5,
                "poll_interval": 0.02,
                "probe": {
                    "kind": "http",
                    "url": f"http://127.0.0.1:{port}/",
                    "success_status": [200, 299],
                },
                "provision": {
                    "kind": "exec",
                    "mode": "run",
                    "argv": [sys.executable, "-c", server],
                },
            },
        )
        results: list[DevEnsureResult] = []
        failures: list[BaseException] = []

        def ensure() -> None:
            try:
                results.append(
                    ensure_target(root, "server", namespace="fixture", store=store)
                )
            except BaseException as error:  # test records concurrent failures
                failures.append(error)

        first = threading.Thread(target=ensure)
        second = threading.Thread(target=ensure)
        first.start()
        second.start()
        first.join()
        second.join()
        try:
            assert failures == []
            assert sorted(result.status for result in results) == [
                "joined",
                "started",
            ]
            assert counter.read_text(encoding="utf-8") == "1\n"
            started_result = next(
                result for result in results if result.status == "started"
            )
            capability_id = started_result.capability.capability_id
            execution_id = store.read_coordination("dev", capability_id)
            assert execution_id is not None
            record = store.read(execution_id)
            assert record.state == "released"
            assert started_result.attempt is not None
            assert started_result.attempt.logs.merged.path.endswith("output.log")
            assert started_result.ready is True
            assert started_result.attempt.caller_role == "owner"
            joined = next(result for result in results if result.status == "joined")
            assert joined.attempt is not None
            assert joined.attempt.caller_role == "follower"
        finally:
            started = next(
                (result for result in results if result.status == "started"),
                None,
            )
            if started is not None and started.attempt is not None:
                execution_id = started.attempt.execution_id
                process_id = store.read(execution_id).process_id
                assert process_id is not None
                stop_owned_process(process_id)


def test_activation_timeout_is_structured_and_cleans_its_owned_group(
    tmp_path: Path,
) -> None:
    write_project_config(
        tmp_path,
        dev_targets={
            "activation": {
                "scope": "repository",
                "readiness_timeout": 0.01,
                "poll_interval": 0.005,
                "probe": {
                    "kind": "exec",
                    "argv": [sys.executable, "-c", "raise SystemExit(1)"],
                },
                "provision": {
                    "kind": "exec",
                    "mode": "activate",
                    "argv": [
                        sys.executable,
                        "-c",
                        "import time; time.sleep(30)",
                    ],
                },
            }
        },
    )

    result = ensure_target(
        tmp_path,
        "activation",
        namespace="fixture",
        store=ExecutionStore(tmp_path / "runtime"),
    )

    assert result.status == "activation-timeout"
    assert result.cleanup == "completed"


def test_declared_stop_runs_once_and_is_qualified_by_final_readiness() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        marker = root / "ready"
        counter = root / "stops"
        marker.write_text("ready", encoding="utf-8")
        write_target(
            root,
            "server",
            {
                "scope": "repository",
                "probe": {
                    "kind": "exec",
                    "argv": [
                        sys.executable,
                        "-c",
                        "from pathlib import Path; import sys; "
                        f"sys.exit(0 if Path({str(marker)!r}).exists() else 1)",
                    ],
                },
                "provision": {"kind": "manual"},
                "stop": {
                    "kind": "exec",
                    "argv": [
                        sys.executable,
                        "-c",
                        "from pathlib import Path; import time; "
                        f"p=Path({str(counter)!r}); p.write_text((p.read_text() if p.exists() else '')+'1\\n'); "
                        "time.sleep(.15); "
                        f"Path({str(marker)!r}).unlink(missing_ok=True)",
                    ],
                    "timeout": 2,
                },
            },
        )
        store = ExecutionStore(root / "runtime")
        results: list[DevStopResult] = []
        failures: list[BaseException] = []

        def stop() -> None:
            try:
                results.append(
                    stop_target(root, "server", namespace="fixture", store=store)
                )
            except BaseException as error:
                failures.append(error)

        callers = (threading.Thread(target=stop), threading.Thread(target=stop))
        for caller in callers:
            caller.start()
        for caller in callers:
            caller.join()

        assert failures == []
        assert [result.status for result in results] == ["stopped", "stopped"]
        attempts = [result.attempt for result in results]
        assert all(attempt is not None for attempt in attempts)
        concrete_attempts = [attempt for attempt in attempts if attempt is not None]
        assert {attempt.caller_role for attempt in concrete_attempts} == {
            "owner",
            "follower",
        }
        assert len({attempt.execution_id for attempt in concrete_attempts}) == 1
        assert counter.read_text(encoding="utf-8") == "1\n"
        assert all(result.ready is False for result in results)
        assert all(
            attempt.logs.merged.path.endswith("output.log")
            for attempt in concrete_attempts
        )


@pytest.mark.parametrize("stop", [None, {"kind": "manual"}])
def test_absent_or_manual_stop_never_infers_a_pid_cleanup(stop: object) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        target: dict[str, object] = {
            "scope": "repository",
            "probe": {
                "kind": "exec",
                "argv": [sys.executable, "-c", "raise SystemExit(0)"],
            },
            "provision": {"kind": "manual"},
        }
        if stop is not None:
            target["stop"] = stop
        write_target(root, "server", target)

        result = stop_target(root, "server", namespace="fixture")

        assert result.status == "manual-action-required"
        assert result.ready is True
        assert result.attempt is None
        assert result.stop.kind == ("manual" if stop is not None else "absent")


def test_stop_failure_preserves_action_and_final_probe_evidence() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_target(
            root,
            "server",
            {
                "scope": "repository",
                "probe": {
                    "kind": "exec",
                    "argv": [sys.executable, "-c", "raise SystemExit(0)"],
                },
                "provision": {"kind": "manual"},
                "stop": {
                    "kind": "exec",
                    "argv": [sys.executable, "-c", "raise SystemExit(7)"],
                },
            },
        )

        result = stop_target(root, "server", namespace="fixture")

        assert result.status == "stop-failed"
        assert result.ready is True
        assert result.attempt is not None
        assert result.attempt.exit_code == 7


def test_settled_ensure_attempt_does_not_prevent_a_later_explicit_restart() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        marker = root / "ready"
        counter = root / "starts"
        write_target(
            root,
            "server",
            {
                "scope": "repository",
                "poll_interval": 0.01,
                "probe": {
                    "kind": "exec",
                    "argv": [
                        sys.executable,
                        "-c",
                        "from pathlib import Path; import sys; "
                        f"sys.exit(0 if Path({str(marker)!r}).exists() else 1)",
                    ],
                },
                "provision": {
                    "kind": "exec",
                    "mode": "activate",
                    "argv": [
                        sys.executable,
                        "-c",
                        "from pathlib import Path; "
                        f"p=Path({str(counter)!r}); p.write_text((p.read_text() if p.exists() else '')+'1\\n'); "
                        f"Path({str(marker)!r}).write_text('ready')",
                    ],
                },
            },
        )
        store = ExecutionStore(root / "runtime")

        first = ensure_target(root, "server", namespace="fixture", store=store)
        marker.unlink()
        second = ensure_target(root, "server", namespace="fixture", store=store)

        assert (first.status, second.status) == ("started", "started")
        assert counter.read_text(encoding="utf-8") == "1\n1\n"
        assert first.attempt is not None and second.attempt is not None
        assert first.attempt.execution_id != second.attempt.execution_id


def test_stop_and_ensure_serialize_on_the_same_capability_boundary() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        marker = root / "ready"
        stopping = root / "stopping"
        starts = root / "starts"
        marker.write_text("ready", encoding="utf-8")
        write_target(
            root,
            "server",
            {
                "scope": "repository",
                "poll_interval": 0.01,
                "probe": {
                    "kind": "exec",
                    "argv": [
                        sys.executable,
                        "-c",
                        "from pathlib import Path; import sys; "
                        f"sys.exit(0 if Path({str(marker)!r}).exists() else 1)",
                    ],
                },
                "provision": {
                    "kind": "exec",
                    "mode": "activate",
                    "argv": [
                        sys.executable,
                        "-c",
                        "from pathlib import Path; "
                        f"Path({str(starts)!r}).write_text('1'); "
                        f"Path({str(marker)!r}).write_text('ready')",
                    ],
                },
                "stop": {
                    "kind": "exec",
                    "argv": [
                        sys.executable,
                        "-c",
                        "from pathlib import Path; import time; "
                        f"Path({str(stopping)!r}).write_text('1'); "
                        "time.sleep(.2); "
                        f"Path({str(marker)!r}).unlink()",
                    ],
                },
            },
        )
        store = ExecutionStore(root / "runtime")
        stopped: list[DevStopResult] = []
        stopper = threading.Thread(
            target=lambda: stopped.append(
                stop_target(root, "server", namespace="fixture", store=store)
            )
        )
        stopper.start()
        deadline = time.monotonic() + 2
        while not stopping.exists() and time.monotonic() < deadline:
            time.sleep(0.01)

        ensured = ensure_target(root, "server", namespace="fixture", store=store)
        stopper.join()

        assert stopped[0].status == "stopped"
        assert stopped[0].ready is False
        assert ensured.status == "started"
        assert ensured.ready is True
        assert marker.exists() and starts.read_text(encoding="utf-8") == "1"


def write_target(root: Path, name: str, target: object) -> None:
    write_project_config(root, dev_targets={name: target})


def free_port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


def stop_owned_process(pid: int) -> None:
    if os.name == "nt":
        os.kill(pid, signal.SIGTERM)
    else:
        os.killpg(pid, signal.SIGTERM)
