from __future__ import annotations
import io
import json
from contextlib import redirect_stderr, redirect_stdout
import pytest
from svc_cli.cli import EXIT_CONFLICT, EXIT_FAILURE, EXIT_OK, main
from svc_cli.double import service
from svc_cli.double.model import (
    EmitResult,
    ObserveResult,
    StopResult,
)
from svc_cli.errors import SvcError

from ..support.facts import service_observation
from ..support.scenarios import LANGUAGE_FIXTURES, PAYMENT_MODULE, RUN_ID


def _invoke(arguments: list[str]) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        try:
            code = main(arguments)
        except SystemExit as error:
            code = int(error.code or 0)
    return code, stdout.getvalue(), stderr.getvalue()


def _json(raw: str) -> dict[str, object]:
    assert raw.endswith("\n")
    assert raw.count("\n") == 1
    value = json.loads(raw)
    assert isinstance(value, dict)
    return value


def test_double_validate_json_human_and_exit_contract() -> None:
    code, stdout, stderr = _invoke(
        ["double", "validate", str(PAYMENT_MODULE), "--json"]
    )
    payload = _json(stdout)

    assert (code, stderr) == (EXIT_OK, "")
    assert payload["command"] == "double validate"
    assert payload["valid"] is True
    assert payload["scenario_name"] == "payment-confirmed"
    assert len(str(payload["scenario_digest"])) == 64
    assert "content_base64" not in stdout
    assert "product_verdict" not in stdout

    invalid = LANGUAGE_FIXTURES / "invalid" / "unknown-key.double.yaml"
    code, stdout, stderr = _invoke(["double", "validate", str(invalid), "--json"])
    rejected = _json(stdout)
    assert (code, stderr) == (EXIT_CONFLICT, "")
    assert rejected["valid"] is False
    assert rejected["diagnostic"]["code"] == "unknown-double-key"
    assert rejected["diagnostic"]["path"] == "/scenario/assertion"
    assert rejected["diagnostic"]["line"] == 5
    assert rejected["diagnostic"]["column"] == 3

    code, stdout, stderr = _invoke(["double", "validate", str(PAYMENT_MODULE)])
    assert (code, stderr) == (EXIT_OK, "")
    assert "Valid double scenario: payment-confirmed" in stdout
    assert "Claim: consumer exposes a paid order" in stdout
    assert "Non-claims:" in stdout
    assert "product verdict" not in stdout.lower()


def test_double_start_rejects_non_rfc3339_fixed_clock_on_stderr() -> None:
    code, stdout, stderr = _invoke(
        [
            "double",
            "start",
            str(PAYMENT_MODULE),
            "--clock",
            "2026-08-10 02:00:00Z",
            "--json",
        ]
    )

    assert (code, stdout) == (EXIT_CONFLICT, "")
    assert _json(stderr)["error"]["code"] == "double-clock-invalid"


def test_double_cli_preserves_typed_failures_and_safely_classifies_bugs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def typed_failure(run_id: str) -> ObserveResult:
        raise SvcError(
            "double-control-protocol-invalid",
            "Carrier observation response is malformed.",
        )

    monkeypatch.setattr(service, "observe_run", typed_failure)
    code, stdout, stderr = _invoke(["double", "observe", RUN_ID, "--json"])

    assert (code, stdout) == (EXIT_FAILURE, "")
    assert _json(stderr)["error"]["code"] == "double-control-protocol-invalid"

    def unexpected_failure(run_id: str) -> ObserveResult:
        raise RuntimeError("private implementation detail")

    monkeypatch.setattr(service, "observe_run", unexpected_failure)
    code, stdout, stderr = _invoke(["double", "observe", RUN_ID, "--json"])
    failure = _json(stderr)

    assert (code, stdout) == (EXIT_FAILURE, "")
    assert failure["error"]["code"] == "double-internal-error"
    assert failure["error"]["details"] == {"exception": "RuntimeError"}
    assert "private implementation detail" not in stderr


def test_double_help_and_schemas_are_self_contained() -> None:
    code, stdout, stderr = _invoke(["double", "--help"])
    assert (code, stderr) == (EXIT_OK, "")
    family_help = " ".join(stdout.split())
    assert "EXPERIMENTAL" in family_help
    assert "*.double.yaml BSL module" in family_help
    assert "Consumer test remains the product oracle" in family_help
    assert "does not prove provider behavior or currentness" in family_help
    assert "Do not use double merely to make a test pass" in family_help
    assert "could reduce test credibility or validity" in family_help
    assert "report the concern and obtain user confirmation" in family_help
    assert "external materializer is unsandboxed Consumer-owned code" in family_help
    assert "svc double validate checkout.double.yaml" in family_help
    assert "svc double emit RUN_ID payment.succeeded" in family_help
    assert "pip install 'sustainable-vibe-coding[double]'" in family_help

    operation_facts = {
        "validate": ("starts no responder", "Exact *.double.yaml BSL module"),
        "start": ("canonical UUIDv4 RUN_ID", "Every event target declared"),
        "emit": ("cannot invent a payload", "Exact event name declared"),
        "observe": ("never a Consumer test verdict", "sealed snapshot is authority"),
        "stop": (
            "never treats a recorded PID as authority",
            "does not invent terminal state",
        ),
    }

    for operation, facts in operation_facts.items():
        code, stdout, stderr = _invoke(["double", operation, "--help"])
        assert (code, stderr) == (EXIT_OK, "")
        assert f"usage: svc double {operation}" in stdout
        operation_help = " ".join(stdout.split())
        assert "EXPERIMENTAL" in operation_help
        assert "Consumer test remains the product oracle" in operation_help
        assert "Do not use double merely to make a test pass" in operation_help
        assert "could reduce test credibility or validity" in operation_help
        assert "obtain user confirmation before proceeding" in operation_help
        assert "pip install 'sustainable-vibe-coding[double]'" in operation_help
        assert all(fact in operation_help for fact in facts)

        code, stdout, stderr = _invoke(["double", operation, "--json-schema"])
        schema = _json(stdout)
        assert (code, stderr) == (EXIT_OK, "")
        assert schema["$id"] == f"urn:svc:cli-output:double-{operation}:v1"
        assert schema["x-svc-result-schema-version"] == 1
        assert "double-runtime-unavailable" in stdout
        assert "pip install 'sustainable-vibe-coding[double]'" in stdout


def test_double_emit_observe_and_stop_project_stable_machine_facts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    active = service_observation(sealed=False, status="ready")
    sealed = service_observation(sealed=True, status="stopped")

    monkeypatch.setattr(
        service,
        "emit_event",
        lambda run_id, event: EmitResult(
            run_id=run_id,
            event=event,
            status="acknowledged",
            target="http://127.0.0.1:9010",
            http_status=204,
        ),
    )
    monkeypatch.setattr(
        service,
        "observe_run",
        lambda run_id: ObserveResult(
            observation=active,
            authority="active-carrier",
            control_status="available",
        ),
    )
    monkeypatch.setattr(
        service,
        "stop_run",
        lambda run_id: StopResult(
            run_id=run_id,
            status="stopped",
            sealed=True,
            idempotent=True,
            observation=sealed,
        ),
    )

    code, stdout, stderr = _invoke(
        ["double", "emit", RUN_ID, "payment.succeeded", "--json"]
    )
    emitted = _json(stdout)
    assert (code, stderr) == (EXIT_OK, "")
    assert emitted["status"] == "acknowledged"
    assert emitted["http_status"] == 204

    code, stdout, stderr = _invoke(["double", "observe", RUN_ID, "--json"])
    observed = _json(stdout)
    assert (code, stderr) == (EXIT_OK, "")
    assert observed["authority"] == "active-carrier"
    assert observed["observation"]["bindings"] == ["external_id"]
    assert observed["observation"]["journal"] == {
        "total": 1,
        "retained": 1,
        "omitted": 0,
        "entries": observed["observation"]["journal"]["entries"],
    }
    assert "private-capture" not in stdout
    assert "private-header" not in stdout

    code, stdout, stderr = _invoke(["double", "stop", RUN_ID, "--json"])
    stopped = _json(stdout)
    assert (code, stderr) == (EXIT_OK, "")
    assert stopped["status"] == "stopped"
    assert stopped["sealed"] is True
    assert stopped["idempotent"] is True
