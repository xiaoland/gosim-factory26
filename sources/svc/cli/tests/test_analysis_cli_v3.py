from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import json
from pathlib import Path
import shutil

import pytest

from svc_cli.cli import main
from svc_cli.analysis.models_v3 import AnalysisErrorV3


FIXTURES = Path(__file__).parent / "fixtures" / "analysis"


def _invoke(arguments: list[str]) -> tuple[int, str, str]:
    stdout, stderr = StringIO(), StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        code = main(arguments)
    return code, stdout.getvalue(), stderr.getvalue()


def test_v3_cli_discovers_exports_and_analyzes_standard_pi(tmp_path: Path) -> None:
    home = tmp_path / "pi"
    sessions = home / "sessions" / "demo"
    sessions.mkdir(parents=True)
    source = sessions / "session.jsonl"
    shutil.copyfile(FIXTURES / "pi" / "session.jsonl", source)

    code, stdout, stderr = _invoke(
        [
            "telemetry",
            "agent-thread",
            "list",
            "--provider",
            "pi",
            "--home",
            str(home),
            "--json",
        ]
    )
    assert (code, stderr) == (0, "")
    assert json.loads(stdout)["threads"][0]["thread_id"] == "pi-root"

    bundle = tmp_path / "pi.zip"
    code, stdout, stderr = _invoke(
        [
            "telemetry",
            "agent-thread",
            "export",
            "--provider",
            "pi",
            "--source",
            str(source),
            "--output",
            str(bundle),
            "--json",
        ]
    )
    assert (code, stderr) == (0, "")
    assert json.loads(stdout)["schema_version"] == 4

    request = tmp_path / "overview.json"
    request.write_text('{"version":3,"intent":"overview"}')
    code, stdout, stderr = _invoke(
        ["analysis", "query", "--input", str(bundle), "--request", str(request)]
    )
    assert (code, stderr) == (0, "")
    overview = json.loads(stdout)
    assert overview["version"] == 3
    assert overview["counts"]["usage"] == 5

    code, stdout, stderr = _invoke(["analysis", "--schema"])
    assert (code, stderr) == (0, "")
    assert json.loads(stdout)["ref_consumers"]["native"] == ["read"]

    bad = tmp_path / "bad.json"
    bad.write_text('{"version":3,"intent":"trace"}')
    code, stdout, stderr = _invoke(
        ["analysis", "query", "--input", str(bundle), "--request", str(bad)]
    )
    assert (code, stdout) == (2, "")
    AnalysisErrorV3.model_validate_json(stderr)


def test_analysis_help_routes_normalized_trace_before_native_audit() -> None:
    stdout = StringIO()
    with redirect_stdout(stdout), pytest.raises(SystemExit) as exit_info:
        main(["analysis", "--help"])
    assert exit_info.value.code == 0
    help_text = " ".join(stdout.getvalue().split())
    assert "trace for linked normalized context" in help_text
    assert "read for exact content recovery or native audit" in help_text
    assert "read contiguous opening" not in help_text
