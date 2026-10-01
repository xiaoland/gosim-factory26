from __future__ import annotations
import json
import pytest
from pydantic import ValidationError
from svc_cli.cli_output.double import (
    DoubleDiagnosticOutput,
    DoubleEmitOutput,
    DoubleJournalFactsOutput,
    DoubleJournalOutput,
    DoubleObserveOutput,
    DoubleRuntimeUnavailableOutput,
    DoubleSnapshotOutput,
    DoubleStartOutput,
    DoubleStopOutput,
    DoubleValidateOutput,
)

from ..support.facts import output_observation, output_replay, output_target


def test_validate_and_start_expose_identity_without_snapshot_content() -> None:
    validated = DoubleValidateOutput(
        module="/workspace/payment.double.yaml",
        scenario_name="payment-confirmed",
        claim="consumer exposes a paid order",
        valid=True,
        scenario_digest="a" * 64,
        fidelity=("selected-operation-schema",),
        nonclaims=("provider-behavior:not-claimed",),
        snapshots=(
            DoubleSnapshotOutput(
                logical_path="contracts/payment.openapi.yaml",
                sha256="b" * 64,
                bytes=417,
            ),
        ),
    )
    started = DoubleStartOutput(
        run_id="ad300eca-a210-4b09-873c-95bbffdc16b8",
        module=validated.module,
        scenario_name="payment-confirmed",
        responder_url="http://127.0.0.1:43811",
        scenario_digest="a" * 64,
        run_context_digest="c" * 64,
        replay=output_replay(),
        targets=(output_target(),),
        nonclaims=(
            "consumer-egress:not-enforced",
            "materializer-egress:not-enforced",
        ),
    )
    invalid = DoubleValidateOutput(
        module="/workspace/unsupported.double.yaml",
        valid=False,
        fidelity=(),
        nonclaims=(),
        snapshots=(),
        diagnostic=DoubleDiagnosticOutput(
            code="unsupported-language",
            message="language must be svc.double/v0",
            path="language",
            line=1,
            column=11,
        ),
    )

    assert "content_base64" not in json.dumps(validated.as_dict())
    assert invalid.valid is False
    assert started.as_dict()["replay"]["seed"] == 123
    assert started.as_dict()["run_context_digest"] == "c" * 64
    with pytest.raises(ValidationError):
        DoubleSnapshotOutput.model_validate(
            {
                "logical_path": "secret.bin",
                "sha256": "d" * 64,
                "bytes": 6,
                "content_base64": "c2VjcmV0",
            }
        )
    with pytest.raises(ValidationError):
        DoubleJournalFactsOutput.model_validate(
            {"event": "payment.succeeded", "control_capability": "secret"}
        )


def test_runtime_unavailable_and_event_acknowledgement_are_typed_results() -> None:
    unavailable = DoubleRuntimeUnavailableOutput(command="double validate")
    acknowledged = DoubleEmitOutput(
        run_id="ad300eca-a210-4b09-873c-95bbffdc16b8",
        event="payment.succeeded",
        status="acknowledged",
        target="http://127.0.0.1:9010/webhooks/payment",
        http_status=204,
    )
    transport_failure = DoubleEmitOutput(
        run_id=acknowledged.run_id,
        event=acknowledged.event,
        status="transport-failed",
        target="http://127.0.0.1:9010/webhooks/payment",
        reason="connection-refused",
    )

    assert unavailable.continuation == "pip install 'sustainable-vibe-coding[double]'"
    assert acknowledged.status == "acknowledged"
    assert transport_failure.http_status is None
    with pytest.raises(ValidationError, match="only a 2xx"):
        DoubleEmitOutput(
            run_id=acknowledged.run_id,
            event=acknowledged.event,
            status="acknowledged",
            target=acknowledged.target,
            http_status=302,
        )


def test_observe_distinguishes_active_sealed_and_last_unsealed_projection() -> None:
    active = DoubleObserveOutput(
        observation=output_observation(sealed=False),
        authority="active-carrier",
        control_status="available",
    )
    sealed = DoubleObserveOutput(
        observation=output_observation(sealed=True, status="stopped"),
        authority="sealed-snapshot",
        control_status="not-required",
    )
    unavailable = DoubleObserveOutput(
        observation=output_observation(sealed=False),
        authority="unsealed-projection",
        control_status="control-unavailable",
    )

    assert active.observation.journal.model_dump(exclude={"entries"}) == {
        "total": 2,
        "retained": 1,
        "omitted": 1,
    }
    assert sealed.observation.sealed is True
    assert unavailable.authority == "unsealed-projection"
    with pytest.raises(ValidationError, match="seal does not match"):
        DoubleObserveOutput(
            observation=output_observation(sealed=False),
            authority="sealed-snapshot",
            control_status="not-required",
        )
    with pytest.raises(ValidationError, match="retained journal count"):
        DoubleJournalOutput(total=1, retained=1, omitted=0, entries=())


def test_stop_is_idempotent_only_from_the_sealed_authority() -> None:
    repeated = DoubleStopOutput(
        run_id="ad300eca-a210-4b09-873c-95bbffdc16b8",
        status="stopped",
        sealed=True,
        idempotent=True,
        observation=output_observation(sealed=True, status="stopped"),
    )
    unavailable = DoubleStopOutput(
        run_id=repeated.run_id,
        status="control-unavailable",
        sealed=False,
        idempotent=False,
        observation=output_observation(sealed=False),
    )

    assert repeated.idempotent is True
    assert unavailable.observation.sealed is False
    with pytest.raises(ValidationError, match="not an idempotent stop"):
        DoubleStopOutput(
            run_id=repeated.run_id,
            status="control-unavailable",
            sealed=False,
            idempotent=True,
            observation=output_observation(sealed=False),
        )
