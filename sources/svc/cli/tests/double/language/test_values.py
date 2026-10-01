from __future__ import annotations
from pathlib import Path
import pytest
from svc_cli.double.compiler import (
    compile_scenario,
)
from svc_cli.double.materialization import (
    MaterializationContext,
    match_body,
)
from svc_cli.double.model import Replay
from svc_cli.errors import SvcError

from ..support.scenarios import LANGUAGE_FIXTURES, one_interaction, write_module


@pytest.mark.parametrize(
    ("name", "code"),
    [
        ("illegal-phase.double.yaml", "illegal-double-value-phase"),
    ],
)
def test_invalid_fixture_corpus_has_stable_diagnostics(name: str, code: str) -> None:
    with pytest.raises(SvcError) as caught:
        compile_scenario(LANGUAGE_FIXTURES / "invalid" / name)

    assert caught.value.code == code
    assert Path(caught.value.details["module"]).name == name
    assert caught.value.details["line"] >= 1
    assert caught.value.details["column"] >= 1


def test_query_and_header_typed_values_must_be_string_typed(tmp_path: Path) -> None:
    numeric_query = write_module(
        tmp_path,
        one_interaction(request="        query: {page: 1}\n"),
    )
    with pytest.raises(SvcError) as caught:
        compile_scenario(numeric_query)
    assert caught.value.code == "invalid-double-query"

    range_header = write_module(
        tmp_path,
        one_interaction(
            request=(
                "        headers:\n"
                "          x-page:\n"
                "            $bsl:\n"
                "              kind: match\n"
                "              match: {kind: range, minimum: 1, maximum: 9}\n"
            )
        ),
    )
    with pytest.raises(SvcError) as caught:
        compile_scenario(range_header)
    assert caught.value.code == "invalid-double-header"


def test_form_urlencoded_request_fields_match_capture_and_preserve_repeats(
    tmp_path: Path,
) -> None:
    module = write_module(
        tmp_path,
        one_interaction(
            request=(
                "        headers: {content-type: application/x-www-form-urlencoded}\n"
                "        body:\n"
                "          form-urlencoded:\n"
                "            ext_order_id:\n"
                "              $bsl:\n"
                "                kind: capture\n"
                "                name: external_order_id\n"
                "                match: {kind: regex, pattern: '^[0-9a-f-]{36}$'}\n"
                "            tag: [first, second]\n"
                "            note: Hangzhou East\n"
            )
        ),
    )
    scenario = compile_scenario(module)
    body = scenario.interactions[0].request.body
    assert body is not None
    assert body.kind == "form-urlencoded"
    assert "form-urlencoded.field-matching/v1" in scenario.fidelity
    context = MaterializationContext(
        replay=Replay(
            seed=1,
            clock="2026-08-10T02:00:00Z",
            generators=(),
            validators=(),
            runtime="test",
        ),
        scenario_name=scenario.name,
        scenario_digest=scenario.scenario_digest,
        run_context_digest="form-run",
    )

    matched, reasons, captures, parsed = match_body(
        body,
        (
            b"note=Hangzhou+East&tag=first&"
            b"ext_order_id=00000000-0000-4000-8000-000000000001&tag=second"
        ),
        context,
        namespace="form-request",
    )

    assert matched, reasons
    assert captures == {"external_order_id": "00000000-0000-4000-8000-000000000001"}
    assert parsed == {
        "ext_order_id": "00000000-0000-4000-8000-000000000001",
        "note": "Hangzhou East",
        "tag": ["first", "second"],
    }
    with pytest.raises(SvcError) as caught:
        match_body(
            body,
            b"ext_order_id=%GG&tag=first&tag=second&note=Hangzhou+East",
            context,
            namespace="invalid-form-request",
        )
    assert caught.value.code == "double-request-form-invalid"


def test_form_urlencoded_is_request_only_and_string_typed(tmp_path: Path) -> None:
    numeric = write_module(
        tmp_path,
        one_interaction(
            request=("        body:\n          form-urlencoded:\n            page: 1\n")
        ),
    )
    with pytest.raises(SvcError) as caught:
        compile_scenario(numeric)
    assert caught.value.code == "invalid-double-form"

    response_form = write_module(
        tmp_path,
        one_interaction(
            response=(
                "        status: 200\n"
                "        body:\n"
                "          form-urlencoded: {ok: yes}\n"
            )
        ),
    )
    with pytest.raises(SvcError) as caught:
        compile_scenario(response_form)
    assert caught.value.code == "invalid-double-body"


def test_output_binding_is_available_to_later_derived_value(tmp_path: Path) -> None:
    module = write_module(
        tmp_path,
        one_interaction(
            response=(
                "        status: 200\n"
                "        body:\n"
                "          structured:\n"
                "            first:\n"
                "              $bsl: {kind: example, value: stable, bind: stable_value}\n"
                "            second:\n"
                "              $bsl:\n"
                "                kind: derived\n"
                "                expression: bindings.stable_value\n"
                "                validate: {kind: exact, value: stable}\n"
            )
        ),
    )

    scenario = compile_scenario(module)

    body = scenario.interactions[0].response.body
    assert body is not None
    nodes = body.nodes
    assert nodes[0].bind == "stable_value"
    assert nodes[1].expression == "bindings.stable_value"


def test_cross_interaction_binding_is_not_statically_available(tmp_path: Path) -> None:
    scenario = one_interaction(
        request=(
            "        body:\n"
            "          structured:\n"
            "            id:\n"
            "              $bsl:\n"
            "                kind: capture\n"
            "                name: first_id\n"
            "                match: {kind: regex, pattern: '^x$'}\n"
        )
    )
    scenario += (
        "    - name: independent\n"
        "      provenance: {kind: synthetic, source: https://example.invalid/independent}\n"
        "      request: {method: POST, path: /independent}\n"
        "      response:\n"
        "        status: 200\n"
        "        body:\n"
        "          structured:\n"
        "            leaked:\n"
        "              $bsl:\n"
        "                kind: derived\n"
        "                expression: bindings.first_id\n"
        "                validate: {kind: regex, pattern: '^x$'}\n"
    )
    module = write_module(tmp_path, scenario)

    with pytest.raises(SvcError) as caught:
        compile_scenario(module)

    assert caught.value.code == "unavailable-double-binding"


def test_literal_node_escapes_reserved_bsl_object(tmp_path: Path) -> None:
    module = write_module(
        tmp_path,
        one_interaction(
            request=(
                "        body:\n"
                "          structured:\n"
                "            providerValue:\n"
                "              $bsl:\n"
                "                kind: literal\n"
                "                value: {$bsl: provider-owned}\n"
            )
        ),
    )

    scenario = compile_scenario(module)

    body = scenario.interactions[0].request.body
    assert body is not None
    node = body.nodes[0]
    assert node.kind == "literal"
    assert node.value == {"$bsl": "provider-owned"}


def test_header_names_reject_case_insensitive_duplicates(tmp_path: Path) -> None:
    module = write_module(
        tmp_path,
        one_interaction(
            request=(
                "        headers:\n"
                "          Content-Type: application/json\n"
                "          content-type: text/plain\n"
            )
        ),
    )

    with pytest.raises(SvcError) as caught:
        compile_scenario(module)

    assert caught.value.code == "duplicate-double-header"
    assert caught.value.details["header"] == "content-type"


@pytest.mark.parametrize(
    "using",
    ["faker.string/v1", "provider.payment-id/v1", "project.custom/v1"],
)
def test_project_and_provider_generators_are_outside_closed_registry(
    tmp_path: Path, using: str
) -> None:
    module = write_module(
        tmp_path,
        one_interaction(
            response=(
                "        status: 200\n"
                "        body:\n"
                "          structured:\n"
                "            value:\n"
                "              $bsl:\n"
                "                kind: generated\n"
                "                semantic: provider-value\n"
                f"                using: {using}\n"
                "                validate: {kind: regex, pattern: '^x$'}\n"
            )
        ),
    )

    with pytest.raises(SvcError) as caught:
        compile_scenario(module)

    assert caught.value.code == "unsupported-double-generator"
    assert caught.value.details["using"] == using


def test_range_null_bound_and_generator_null_validator_are_rejected(
    tmp_path: Path,
) -> None:
    null_bound = write_module(
        tmp_path,
        one_interaction(
            request=(
                "        body:\n"
                "          structured:\n"
                "            value:\n"
                "              $bsl:\n"
                "                kind: match\n"
                "                match: {kind: range, minimum: null, maximum: 3}\n"
            )
        ),
    )
    with pytest.raises(SvcError) as caught:
        compile_scenario(null_bound)
    assert caught.value.code == "invalid-double-matcher"

    module = write_module(
        tmp_path,
        one_interaction(
            response=(
                "        status: 200\n"
                "        body:\n"
                "          structured:\n"
                "            value:\n"
                "              $bsl:\n"
                "                kind: generated\n"
                "                semantic: rfc.uuid\n"
                "                using: svc.uuid-v4/v1\n"
                "                validate: {kind: exact, value: null}\n"
            )
        ),
    )
    with pytest.raises(SvcError) as caught:
        compile_scenario(module)
    assert caught.value.code == "invalid-double-generator-validator"
