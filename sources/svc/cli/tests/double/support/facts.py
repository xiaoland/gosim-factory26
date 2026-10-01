from __future__ import annotations

from typing import Literal

from svc_cli.cli_output.double import (
    DoubleJournalEntryOutput,
    DoubleJournalFactsOutput,
    DoubleJournalOutput,
    DoubleReplayOutput,
    DoubleRunObservationOutput,
    DoubleTargetOutput,
)
from svc_cli.double.model import (
    Journal,
    JournalEntry,
    Replay,
    RunObservation,
    TargetBinding,
)

from .scenarios import RUN_ID


def output_replay() -> DoubleReplayOutput:
    return DoubleReplayOutput(
        seed=123,
        clock="2026-08-10T02:00:00Z",
        generators=("svc.opaque-token/v1",),
        validators=("svc.rfc-uuid/v1",),
        runtime="svc.double/v0",
    )


def output_target() -> DoubleTargetOutput:
    return DoubleTargetOutput(
        name="consumer.payment-events",
        origin="http://127.0.0.1:9010",
        remote=False,
    )


def output_observation(
    *, sealed: bool, status: str = "ready"
) -> DoubleRunObservationOutput:
    return DoubleRunObservationOutput(
        run_id=RUN_ID,
        scenario_name="payment-confirmed",
        status=status,
        sealed=sealed,
        responder_url="http://127.0.0.1:43811",
        scenario_digest="a" * 64,
        run_context_digest="b" * 64,
        replay=output_replay(),
        targets=(output_target(),),
        bindings=("external_id", "payment_id"),
        journal=DoubleJournalOutput(
            total=2,
            retained=1,
            omitted=1,
            entries=(
                DoubleJournalEntryOutput(
                    sequence=2,
                    at="2026-08-10T02:00:01Z",
                    kind="event",
                    status="acknowledged",
                    facts=DoubleJournalFactsOutput(
                        event="payment.succeeded", request_sha256="c" * 64
                    ),
                ),
            ),
        ),
        nonclaims=("consumer-egress:not-enforced",),
    )


def service_observation(
    *, sealed: bool, status: Literal["ready", "stopped"]
) -> RunObservation:
    return RunObservation(
        run_id=RUN_ID,
        scenario_name="payment-confirmed",
        status=status,
        sealed=sealed,
        responder_url="http://127.0.0.1:43811",
        scenario_digest="a" * 64,
        run_context_digest="b" * 64,
        replay=Replay(
            seed=123,
            clock="2026-08-10T02:00:00Z",
            generators=("svc.opaque-token/v1",),
            validators=("svc.rfc-uuid/v1",),
            runtime="svc.double.native/v0",
        ),
        targets=(
            TargetBinding(
                name="consumer.payment-events",
                origin="http://127.0.0.1:9010",
                remote=False,
            ),
        ),
        bindings={"external_id": "private-capture"},
        journal=Journal(
            total=1,
            retained=1,
            omitted=0,
            entries=(
                JournalEntry(
                    sequence=1,
                    at="2026-08-10T02:00:01Z",
                    kind="request",
                    status="matched",
                    facts={
                        "interaction": "create-payment",
                        "body_sha256": "c" * 64,
                        "authorization": "private-header",
                    },
                ),
            ),
        ),
        nonclaims=("consumer-egress: not-enforced",),
    )
