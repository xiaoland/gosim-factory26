from __future__ import annotations
import shutil
from pathlib import Path
from svc_cli.double.compiler import (
    compile_scenario,
)
from svc_cli.double.materialization import (
    MaterializationContext,
    commit_bindings,
    match_body,
    match_mapping,
    materialize_body,
    materialize_mapping,
)
from svc_cli.double.model import Replay

from ..support.scenarios import LANGUAGE_FIXTURES


def test_compile_representative_module_to_normalized_ir() -> None:
    module = LANGUAGE_FIXTURES / "payment.double.yaml"

    scenario = compile_scenario(module)

    assert scenario.name == "payment-confirmed"
    assert scenario.language == "svc.double/v0"
    assert scenario.event_target_policy == "loopback-only"
    assert len(scenario.scenario_digest) == 64
    assert scenario.scenario_digest == compile_scenario(module).scenario_digest
    assert scenario.fidelity == (
        "http-exact-boundary",
        "provenance-declared",
        "json.compact-utf8/v1",
        "selected-operation-schema",
        "local-snapshots",
    )
    assert "consumer-egress: not-enforced" in scenario.nonclaims

    interaction = scenario.interactions[0]
    assert interaction.request.query["observed-at"] == "2026-08-10T02:00:00Z"
    assert isinstance(interaction.request.query["observed-at"], str)
    assert interaction.request.query_nodes[0].path == ("trace",)
    assert interaction.request.header_nodes[0].path == ("x-request-id",)
    assert interaction.response.header_nodes[0].path == ("x-payment-id",)
    assert scenario.events[0].request.header_nodes[0].path == ("x-request-id",)
    assert interaction.request.header_nodes[0].location is not None
    assert interaction.request.header_nodes[0].location.line == 37

    assert scenario.contract is not None
    assert scenario.contract.method == "POST"
    assert scenario.contract.path == "/v1/payments"
    assert "urn:svc:double:schema-resource:" in str(scenario.contract.request_schema)
    assert "urn:svc:double:schema-resource:" in str(scenario.contract.response_schemas)
    assert len(scenario.contract.schema_resources) == 2
    assert [item.logical_path for item in scenario.snapshots] == [
        "cli/tests/double/fixtures/language/contracts/payment.openapi.yaml",
        "cli/tests/double/fixtures/language/contracts/schemas.yaml",
    ]
    assert interaction.provenance.snapshot_sha256 == scenario.contract.source.sha256


def test_compiled_ir_drives_matching_captures_and_output_materialization() -> None:
    scenario = compile_scenario(LANGUAGE_FIXTURES / "payment.double.yaml")
    interaction = scenario.interactions[0]
    context = MaterializationContext(
        replay=Replay(
            seed=7,
            clock="2026-08-10T02:00:00Z",
            generators=("svc.opaque-token/v1",),
            validators=("svc.rfc-uuid/v1",),
            runtime="test",
        ),
        scenario_name=scenario.name,
        scenario_digest=scenario.scenario_digest,
        run_context_digest="test-run",
    )

    query_match, _, query_captures = match_mapping(
        interaction.request.query,
        interaction.request.query_nodes,
        {"observed-at": "2026-08-10T02:00:00Z", "trace": "trace-001"},
        context,
        namespace="request-query",
    )
    header_match, _, header_captures = match_mapping(
        interaction.request.headers,
        interaction.request.header_nodes,
        {
            "content-type": "application/json",
            "x-request-id": "00000000-0000-4000-8000-000000000002",
        },
        context,
        namespace="request-headers",
    )
    body_match, _, body_captures, structured_request = match_body(
        interaction.request.body,
        b'{"externalId":"00000000-0000-4000-8000-000000000001"}',
        context,
        namespace="request-body",
    )
    assert query_match and header_match and body_match
    commit_bindings(context, {**query_captures, **header_captures, **body_captures})

    response_headers = materialize_mapping(
        interaction.response.headers,
        interaction.response.header_nodes,
        context,
        namespace="response-headers",
        request=structured_request,
    )
    raw, kind, structured = materialize_body(
        interaction.response.body,
        context,
        namespace="response-body",
        request=structured_request,
    )

    assert kind == "structured"
    assert structured == {"paymentId": response_headers["x-payment-id"]}
    assert raw == (
        b'{"paymentId":"' + str(response_headers["x-payment-id"]).encode() + b'"}'
    )


def test_scenario_digest_ignores_physical_location_and_yaml_comments(
    tmp_path: Path,
) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    shutil.copytree(LANGUAGE_FIXTURES, first)
    shutil.copytree(LANGUAGE_FIXTURES, second)
    module = second / "payment.double.yaml"
    module.write_text(
        "# shifted source locations\n" + module.read_text(encoding="utf-8")
    )

    left = compile_scenario(first / "payment.double.yaml")
    right = compile_scenario(module)

    assert left.scenario_digest == right.scenario_digest
    assert left.module_path != right.module_path
    assert (
        left.interactions[0].request.header_nodes[0].location
        != right.interactions[0].request.header_nodes[0].location
    )
