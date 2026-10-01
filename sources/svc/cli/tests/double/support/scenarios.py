from __future__ import annotations

import urllib.parse
from pathlib import Path

from svc_cli.double.compiler import compile_scenario
from svc_cli.double.materialization import MaterializationContext
from svc_cli.double.model import Replay, TargetBinding
from svc_cli.double.runtime import BoundaryEngine


DOUBLE_FIXTURES = Path(__file__).parents[1] / "fixtures"
LANGUAGE_FIXTURES = DOUBLE_FIXTURES / "language"
CONSUMER_FIXTURES = DOUBLE_FIXTURES / "consumer"
PAYMENT_MODULE = LANGUAGE_FIXTURES / "payment.double.yaml"
RUN_ID = "ad300eca-a210-4b09-873c-95bbffdc16b8"
CLOCK = "2026-08-10T02:00:00Z"
TARGET_NAME = "consumer.payment-events"
FIRST_EXTERNAL_ID = "00000000-0000-4000-8000-000000000001"
SECOND_EXTERNAL_ID = "00000000-0000-4000-8000-000000000003"
FIRST_REQUEST_ID = "00000000-0000-4000-8000-000000000002"
SECOND_REQUEST_ID = "00000000-0000-4000-8000-000000000004"


def write_module(root: Path, scenario: str) -> Path:
    module = root / "scenario.double.yaml"
    module.write_text(
        "language: svc.double/v0\nscenario:\n" + scenario,
        encoding="utf-8",
    )
    return module


def one_interaction(
    *, request: str = "", response: str = "        status: 200\n"
) -> str:
    return (
        "  name: example\n"
        "  claim: one boundary claim\n"
        "  boundary: {name: provider, protocol: http}\n"
        "  interactions:\n"
        "    - name: call\n"
        "      provenance: {kind: synthetic, source: https://example.invalid/call}\n"
        "      request:\n"
        "        method: POST\n"
        "        path: /call\n"
        f"{request}"
        "      response:\n"
        f"{response}"
    )


def build_engine(
    seed: int, *, ambiguous: bool = False, target_origin: str | None = None
) -> BoundaryEngine:
    scenario = compile_scenario(PAYMENT_MODULE)
    if ambiguous:
        duplicate = scenario.interactions[0].model_copy(update={"name": "duplicate"})
        scenario = scenario.model_copy(
            update={"interactions": (*scenario.interactions, duplicate)}
        )
    context = MaterializationContext(
        replay=Replay(
            seed=seed,
            clock=CLOCK,
            generators=("svc.opaque-token/v1",),
            validators=("svc.rfc-uuid/v1",),
            runtime="svc.double.native/v0",
        ),
        scenario_name=scenario.name,
        scenario_digest=scenario.scenario_digest,
        run_context_digest=f"run-context-{seed}",
    )
    targets = (
        ()
        if target_origin is None
        else (TargetBinding(name=TARGET_NAME, origin=target_origin, remote=False),)
    )
    boundary = BoundaryEngine(scenario, context, targets)
    boundary.ready("http://127.0.0.1:1")
    return boundary


def payment_target(path: str = "/v1/payments") -> str:
    query = urllib.parse.urlencode({"observed-at": CLOCK, "trace": "trace-001"})
    return f"{path}?{query}"
