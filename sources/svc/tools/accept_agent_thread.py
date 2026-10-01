"""Black-box acceptance for one built SVC wheel."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import sqlite3
import subprocess
import tempfile
import venv
from pathlib import Path
from typing import Sequence


TIMEOUT = 60


class Failure(Exception):
    def __init__(
        self, case: str, result: subprocess.CompletedProcess[str] | None = None
    ):
        self.case = case
        self.result = result


def command(
    arguments: Sequence[str | os.PathLike[str]], cwd: Path
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        [os.fspath(value) for value in arguments],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=TIMEOUT,
        check=False,
    )
    if result.returncode:
        raise Failure("command", result)
    return result


def cli(
    python: Path, cwd: Path, *arguments: str | os.PathLike[str]
) -> dict[str, object]:
    result = command((python, "-m", "svc_cli.cli", *arguments), cwd)
    try:
        value = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise Failure("json", result) from error
    if not isinstance(value, dict):
        raise Failure("json", result)
    return value


def source_fixture(path: Path) -> None:
    records = (
        {
            "timestamp": "2026-01-01T00:00:00Z",
            "type": "session_meta",
            "payload": {"id": "accept"},
        },
        {
            "timestamp": "2026-01-01T00:00:01Z",
            "type": "response_item",
            "payload": {"type": "message", "role": "assistant", "content": "done"},
        },
    )
    path.write_text(
        "".join(json.dumps(item, separators=(",", ":")) + "\n" for item in records)
    )


def run_case(name: str, python: Path, root: Path) -> None:
    if name == "inventory":
        home = root / "codex-home"
        home.mkdir()
        with sqlite3.connect(home / "state_5.sqlite") as database:
            database.execute(
                "CREATE TABLE threads (id TEXT, rollout_path TEXT, archived INTEGER, "
                "created_at INTEGER, updated_at INTEGER, recency_at_ms INTEGER, cwd TEXT, "
                "title TEXT, first_user_message TEXT)"
            )
        payload = cli(
            python,
            root,
            "telemetry",
            "agent-thread",
            "list",
            "--codex-home",
            home,
            "--json",
        )
        if payload.get("status") != "listed":
            raise Failure(name)
        return

    source = root / f"{name}.jsonl"
    bundle = root / f"{name}.zip"
    source_fixture(source)
    exported = cli(
        python,
        root,
        "telemetry",
        "agent-thread",
        "export",
        "--provider",
        "codex",
        "--source",
        source,
        "--output",
        bundle,
        "--json",
    )
    evidence = exported.get("evidence")
    if exported.get("schema_version") != 4 or not isinstance(evidence, dict):
        raise Failure("evidence")
    if evidence.get("schema_version") != 4:
        raise Failure("evidence")
    if name == "evidence":
        return

    schema = cli(python, root, "analysis", name, "--schema")
    if schema.get("version") != 3:
        raise Failure(name)
    if name == "query":
        request = root / "query.json"
        request.write_text('{"version":3,"intent":"overview"}')
        response = cli(
            python,
            root,
            "analysis",
            "query",
            "--input",
            bundle,
            "--request",
            request,
        )
        if response.get("version") != 3 or response.get("status") not in {
            "complete",
            "partial",
        }:
            raise Failure(name)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--slice",
        choices=("inventory", "evidence", "query", "read", "all"),
        required=True,
    )
    parser.add_argument("--wheel", type=Path, required=True)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--wheelhouse", type=Path, required=True)
    options = parser.parse_args(argv)
    report: dict[str, object] = {
        "status": "failed",
        "slice": options.slice,
        "python": platform.python_version(),
        "cases": {},
    }
    root = Path(tempfile.mkdtemp(prefix="svc-accept-"))
    try:
        wheel = options.wheel.resolve(strict=True)
        wheelhouse = options.wheelhouse.resolve(strict=True)
        digest = hashlib.sha256(wheel.read_bytes()).hexdigest()
        if digest != options.expected_sha256:
            raise Failure("wheel-digest")
        environment = root / "venv"
        venv.EnvBuilder(with_pip=True).create(environment)
        python = environment / (
            "Scripts/python.exe" if os.name == "nt" else "bin/python"
        )
        command(
            (
                python,
                "-m",
                "pip",
                "install",
                "--no-index",
                "--find-links",
                wheelhouse,
                wheel,
            ),
            root,
        )
        selected = (
            ("inventory", "evidence", "query", "read")
            if options.slice == "all"
            else (options.slice,)
        )
        cases = report["cases"]
        assert isinstance(cases, dict)
        for case in selected:
            run_case(case, python, root)
            cases[case] = "passed"
        report["status"] = "passed"
        report["workdir"] = None
        shutil.rmtree(root)
        print(json.dumps(report, sort_keys=True))
        return 0
    except (Failure, OSError, subprocess.SubprocessError) as error:
        report["error"] = type(error).__name__
        report["workdir"] = str(root)
        if isinstance(error, Failure):
            report["case"] = error.case
            if error.result is not None:
                report["command"] = error.result.args
                report["returncode"] = error.result.returncode
                report["stdout"] = error.result.stdout[-8000:]
                report["stderr"] = error.result.stderr[-8000:]
        print(json.dumps(report, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
