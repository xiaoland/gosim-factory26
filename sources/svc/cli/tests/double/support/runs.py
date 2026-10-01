from __future__ import annotations

import json
import os
import signal
from contextlib import suppress
from pathlib import Path

from svc_cli.double.model import StartResult
from svc_cli.double.service import DoubleRunStore, start_run, stop_run

from .http import wait_until_closed
from .scenarios import CLOCK, PAYMENT_MODULE, TARGET_NAME


def start_double_run(
    tmp_path: Path,
    callback_origin: str,
    *,
    seed: int,
) -> tuple[StartResult, Path, Path]:
    run_root = tmp_path / "runs"
    execution_root = tmp_path / "execution"
    result = start_run(
        PAYMENT_MODULE,
        seed=seed,
        clock=CLOCK,
        target_values=(f"{TARGET_NAME}={callback_origin}",),
        allow_remote_names=(),
        run_root=run_root,
        execution_root=execution_root,
    )
    return result, run_root, execution_root


def carrier_pid(run_id: str, execution_root: Path) -> int:
    records = []
    for path in execution_root.glob("*/execution.json"):
        value = json.loads(path.read_bytes())
        if value.get("domain") == "double" and value.get("subject") == run_id:
            records.append(value)
    assert len(records) == 1
    process_id = records[0].get("process_id")
    assert type(process_id) is int
    return process_id


def terminate_test_carrier(run_id: str, run_root: Path, execution_root: Path) -> None:
    record = DoubleRunStore(run_root).read_record(run_id)
    with suppress(ProcessLookupError):
        os.kill(carrier_pid(run_id, execution_root), signal.SIGTERM)
    wait_until_closed(record.control_url)


def cleanup_run(run_id: str, run_root: Path, execution_root: Path) -> None:
    try:
        stopped = stop_run(run_id, run_root=run_root)
    except Exception:
        terminate_test_carrier(run_id, run_root, execution_root)
        return
    if stopped.status != "stopped":
        terminate_test_carrier(run_id, run_root, execution_root)


def file_bytes(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }
