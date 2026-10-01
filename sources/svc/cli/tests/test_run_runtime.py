from __future__ import annotations

import json
import sys
import threading
import time
from pathlib import Path

import pytest

from svc_cli._execution import ExecutionStore
from svc_cli.cli_output.run import project_run_receipt
from svc_cli.errors import SvcError
from svc_cli.run.runtime import (
    execute_entry,
    follow_run,
    inspect_run,
    resolve_run,
)
from svc_cli_test_support.project_contract import (
    write_local_run_overlay,
    write_project_config,
)


def write_config(
    root: Path, entry: dict[str, object], local: dict[str, object] | None = None
) -> None:
    write_project_config(root, run_entries={"check": entry})
    if local is not None:
        write_local_run_overlay(root, {"check": local})


def test_run_resolution_applies_overlay_env_precedence_and_private_digest(
    tmp_path: Path,
) -> None:
    (tmp_path / ".env.shared").write_text(
        "FROM_FILE=first\nINLINE=file\nLITERAL=${HOME}\n",
        encoding="utf-8",
    )
    (tmp_path / ".env.local").write_text(
        "FROM_FILE=second\nLOCAL=yes\n", encoding="utf-8"
    )
    (tmp_path / "work").mkdir()
    write_config(
        tmp_path,
        {"argv": ["base"], "env_files": [".env.shared"], "env": {"INLINE": "base"}},
        {
            "argv": [sys.executable, "-c", "pass"],
            "cwd": "work",
            "env_files": [".env.shared", ".env.local"],
            "env": {"INLINE": "inline"},
        },
    )
    run = resolve_run(
        tmp_path,
        "check",
        namespace="fixture",
        ambient={"FROM_FILE": "ambient", "HOME": "/must-not-interpolate"},
    )
    assert run.argv[0] == sys.executable
    assert run.cwd == (tmp_path / "work").resolve()
    assert run.environment["FROM_FILE"] == "second"
    assert run.environment["LOCAL"] == "yes"
    assert run.environment["INLINE"] == "inline"
    assert run.environment["LITERAL"] == "${HOME}"
    assert "inline" not in json.dumps({"digest": run.effective_entry_digest})

    with pytest.raises(SvcError) as unknown:
        resolve_run(tmp_path, "missing", namespace="fixture")
    assert unknown.value.code == "unknown-run-entry"
    assert unknown.value.details["available_entries"] == ["check"]


def test_execution_record_and_receipt_never_store_environment_values(
    tmp_path: Path,
) -> None:
    secret = "not-for-records"
    write_config(
        tmp_path,
        {"argv": [sys.executable, "-c", "pass"], "env": {"PRIVATE_VALUE": secret}},
    )
    store = ExecutionStore(tmp_path / "runtime")
    outcome = execute_entry(
        tmp_path,
        "check",
        stdout_sink=None,
        stderr_sink=None,
        namespace="fixture",
        store=store,
    )
    assert outcome.record is not None
    assert secret not in json.dumps(outcome.record.as_dict())
    assert secret not in json.dumps(project_run_receipt(outcome, "run").as_dict())


def test_interrupt_after_publication_returns_the_known_execution_receipt(
    tmp_path: Path,
) -> None:
    write_config(tmp_path, {"argv": [sys.executable, "-c", "pass"]})
    store = ExecutionStore(tmp_path / "runtime")

    def interrupt_after_selection(_record: object, _role: object) -> None:
        raise KeyboardInterrupt

    outcome = execute_entry(
        tmp_path,
        "check",
        stdout_sink=None,
        stderr_sink=None,
        on_selected=interrupt_after_selection,
        namespace="fixture",
        store=store,
    )
    assert outcome.record is not None
    assert outcome.record.state == "interrupted"
    assert outcome.record.process_id is None
    assert (
        project_run_receipt(outcome, "run").execution_id == outcome.record.execution_id
    )


@pytest.mark.parametrize("content", ["VALUE\n", "BAD='unterminated\n"])
def test_run_resolution_rejects_malformed_or_valueless_env_without_publication(
    tmp_path: Path, content: str
) -> None:
    (tmp_path / ".env").write_text(content, encoding="utf-8")
    write_config(
        tmp_path, {"argv": [sys.executable, "-c", "pass"], "env_files": [".env"]}
    )
    store = ExecutionStore(tmp_path / "runtime")
    with pytest.raises(SvcError):
        resolve_run(tmp_path, "check", namespace="fixture")
    assert not [path for path in store.root.iterdir() if path.name != "coordination"]


def test_concurrent_entry_callers_share_one_execution_and_later_call_reruns(
    tmp_path: Path,
) -> None:
    counter = tmp_path / "counter.txt"
    script = (
        "from pathlib import Path; import time; "
        f"p=Path({str(counter)!r}); p.open('a').write('1\\n'); "
        "print('started', flush=True); time.sleep(.25)"
    )
    write_config(tmp_path, {"argv": [sys.executable, "-c", script]})
    store = ExecutionStore(tmp_path / "runtime")
    outcomes = []

    def invoke() -> None:
        outcomes.append(
            execute_entry(
                tmp_path,
                "check",
                stdout_sink=None,
                stderr_sink=None,
                namespace="fixture",
                store=store,
            )
        )

    first = threading.Thread(target=invoke)
    second = threading.Thread(target=invoke)
    first.start()
    time.sleep(0.05)
    second.start()
    first.join()
    second.join()
    assert counter.read_text(encoding="utf-8") == "1\n"
    assert {outcome.caller_role for outcome in outcomes} == {"owner", "follower"}
    assert len({outcome.record.execution_id for outcome in outcomes}) == 1

    later = execute_entry(
        tmp_path,
        "check",
        stdout_sink=None,
        stderr_sink=None,
        namespace="fixture",
        store=store,
    )
    assert later.caller_role == "owner"
    assert later.record.execution_id != outcomes[0].record.execution_id
    assert counter.read_text(encoding="utf-8") == "1\n1\n"


def test_changed_entry_intent_serializes_then_runs_as_a_distinct_execution(
    tmp_path: Path,
) -> None:
    events = tmp_path / "events"
    first_started = tmp_path / "first-started"
    first_script = (
        "from pathlib import Path; import time; "
        f"Path({str(first_started)!r}).write_text('yes'); "
        f"p=Path({str(events)!r}); p.write_text('first-start\\n'); "
        "time.sleep(.25); "
        "p.write_text(p.read_text()+'first-end\\n')"
    )
    second_script = (
        "from pathlib import Path; "
        f"p=Path({str(events)!r}); p.write_text(p.read_text()+'second\\n')"
    )
    write_config(tmp_path, {"argv": [sys.executable, "-c", first_script]})
    store = ExecutionStore(tmp_path / "runtime")
    outcomes = []
    first = threading.Thread(
        target=lambda: outcomes.append(
            execute_entry(
                tmp_path,
                "check",
                stdout_sink=None,
                stderr_sink=None,
                namespace="fixture",
                store=store,
            )
        )
    )
    first.start()
    deadline = time.monotonic() + 2
    while not first_started.exists() and time.monotonic() < deadline:
        time.sleep(0.01)
    assert first_started.exists()
    write_config(
        tmp_path,
        {"argv": [sys.executable, "-c", first_script]},
        {"argv": [sys.executable, "-c", second_script]},
    )

    second = execute_entry(
        tmp_path,
        "check",
        stdout_sink=None,
        stderr_sink=None,
        namespace="fixture",
        store=store,
    )
    first.join()

    assert events.read_text(encoding="utf-8") == "first-start\nfirst-end\nsecond\n"
    assert second.caller_role == "owner"
    assert outcomes[0].caller_role == "owner"
    assert second.record.execution_id != outcomes[0].record.execution_id
    assert second.record.intent_digest != outcomes[0].record.intent_digest


def test_follow_and_inspect_use_record_authority_after_config_changes(
    tmp_path: Path,
) -> None:
    write_config(tmp_path, {"argv": [sys.executable, "-c", "print('evidence')"]})
    store = ExecutionStore(tmp_path / "runtime")
    owner = execute_entry(
        tmp_path,
        "check",
        stdout_sink=None,
        stderr_sink=None,
        namespace="fixture",
        store=store,
    )
    (tmp_path / "svc.json").write_text("{}", encoding="utf-8")
    replay = bytearray()

    class Sink:
        def write(self, data: bytes) -> int:
            replay.extend(data)
            return len(data)

        def flush(self) -> None:
            pass

    followed = follow_run(
        tmp_path,
        owner.record.execution_id,
        stdout_sink=Sink(),  # type: ignore[arg-type]
        stderr_sink=None,
        namespace="fixture",
        store=store,
    )
    inspected = inspect_run(
        tmp_path,
        owner.record.execution_id,
        namespace="fixture",
        store=store,
    )
    assert replay == b"evidence\n"
    assert followed.record == inspected.record == owner.record
    assert project_run_receipt(inspected, "run inspect").state == "exited"


def test_run_follow_rejects_dev_domain_and_other_workspace(tmp_path: Path) -> None:
    store = ExecutionStore(tmp_path / "runtime")
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()
    write_config(first, {"argv": [sys.executable, "-c", "pass"]})
    dev = store.publish(
        domain="dev",
        operation="ensure",
        subject="server",
        workspace_instance="unrelated",
        intent_digest="digest",
        coordination_key="a" * 48,
        argv=(sys.executable,),
        cwd=first,
        capture="merged",
    )
    dev.merged_stream.close()
    with pytest.raises(SvcError, match="does not belong"):
        follow_run(
            first,
            dev.record.execution_id,
            stdout_sink=None,
            stderr_sink=None,
            namespace="fixture",
            store=store,
        )

    owner = execute_entry(
        first,
        "check",
        stdout_sink=None,
        stderr_sink=None,
        namespace="fixture",
        store=store,
    )
    with pytest.raises(SvcError, match="different workspace"):
        inspect_run(second, owner.record.execution_id, namespace="fixture", store=store)
