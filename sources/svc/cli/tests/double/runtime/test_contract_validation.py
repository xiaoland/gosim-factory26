from __future__ import annotations
import json
from svc_cli.double.compiler import compile_scenario
from svc_cli.double.materialization import (
    MaterializationContext,
    compact_json,
)
from svc_cli.double.model import (
    CaptureValueNode,
    EnumMatcher,
    Replay,
    StructuredBody,
)
from svc_cli.double.runtime import BoundaryEngine

from ..support.scenarios import (
    LANGUAGE_FIXTURES,
    CLOCK,
)


def test_recursive_local_openapi_registry_is_runtime_authority() -> None:
    scenario = compile_scenario(LANGUAGE_FIXTURES / "recursive.double.yaml")
    valid = {"value": "root", "next": {"value": "child", "next": None}}
    invalid = {"value": "root", "next": {"value": 1, "next": None}}
    interaction = scenario.interactions[0]
    request = interaction.request.model_copy(
        update={
            "body": StructuredBody(
                template=None,
                nodes=(
                    CaptureValueNode(
                        path=(),
                        name="payload",
                        matcher=EnumMatcher(values=(valid, invalid)),
                    ),
                ),
            )
        }
    )
    scenario = scenario.model_copy(
        update={"interactions": (interaction.model_copy(update={"request": request}),)}
    )

    def execute(body: dict[str, object]) -> tuple[int, bytes]:
        context = MaterializationContext(
            replay=Replay(
                seed=1,
                clock=CLOCK,
                generators=(),
                validators=(),
                runtime="svc.double.native/v0",
            ),
            scenario_name=scenario.name,
            scenario_digest=scenario.scenario_digest,
            run_context_digest="recursive",
        )
        engine = BoundaryEngine(scenario, context, ())
        engine.ready("http://127.0.0.1:1")
        status, _headers, raw = engine.handle_request(
            method="POST",
            target="/v1/nodes",
            headers={},
            raw_body=compact_json(body),
        )
        return status, raw

    assert execute(valid)[0] == 204
    rejected_status, rejected_body = execute(invalid)
    assert rejected_status == 422
    assert (
        json.loads(rejected_body)["error"]["code"] == "double-request-contract-failed"
    )
