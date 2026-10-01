from __future__ import annotations
from pathlib import Path
import pytest
from svc_cli.double.cel_profile import (
    evaluate_expression,
    inspect_expression,
    regex_matches,
    validate_expression,
)
from svc_cli.double.compiler import (
    compile_scenario,
)
from svc_cli.errors import SvcError

from ..support.scenarios import LANGUAGE_FIXTURES, one_interaction, write_module


def test_cel_profile_inspection_freezes_the_dynamic_map_limitation() -> None:
    inspection = inspect_expression(
        "// bindings.in_comment\n"
        "bindings.direct + bindings['indexed'] + 'bindings.in_string'"
    )

    assert inspection.bindings == frozenset({"direct", "indexed"})
    assert inspection.dynamic_binding_access is False
    assert inspection.uses_request is False

    dynamic = inspect_expression("bindings['prefix_' + 'name'] + request.body.value")
    assert dynamic.bindings == frozenset()
    assert dynamic.dynamic_binding_access is True
    assert dynamic.uses_request is True


def test_cel_profile_compilation_evaluation_and_regex_share_one_environment() -> None:
    source = "request.body.value + '-' + bindings.suffix"
    validate_expression(source)

    value = evaluate_expression(
        source,
        {
            "request": {"body": {"value": "provider"}},
            "bindings": {"suffix": "accepted"},
            "run": {"seed": 7, "clock": "2026-08-10T02:00:00Z"},
            "scenario": {"name": "payment"},
        },
    )

    assert value == "provider-accepted"
    assert regex_matches(value, r"^[a-z]+-[a-z]+$") is True


@pytest.mark.parametrize(
    ("name", "code"),
    [
        ("cel-macro.double.yaml", "invalid-double-cel"),
        ("unavailable-binding.double.yaml", "unavailable-double-binding"),
    ],
)
def test_invalid_fixture_corpus_has_stable_diagnostics(name: str, code: str) -> None:
    with pytest.raises(SvcError) as caught:
        compile_scenario(LANGUAGE_FIXTURES / "invalid" / name)

    assert caught.value.code == code
    assert Path(caught.value.details["module"]).name == name
    assert caught.value.details["line"] >= 1
    assert caught.value.details["column"] >= 1


def test_cel_binding_text_inside_a_string_is_not_a_reference(tmp_path: Path) -> None:
    module = write_module(
        tmp_path,
        one_interaction(
            response=(
                "        status: 200\n"
                "        body:\n"
                "          structured:\n"
                "            text:\n"
                "              $bsl:\n"
                "                kind: derived\n"
                "                expression: \"'bindings.not_a_reference'\"\n"
                "                validate: {kind: exact, value: bindings.not_a_reference}\n"
            )
        ),
    )

    scenario = compile_scenario(module)

    body = scenario.interactions[0].response.body
    assert body is not None
    assert body.nodes[0].expression == "'bindings.not_a_reference'"


@pytest.mark.parametrize(
    ("expression", "validator"),
    [
        ("[1, 2]", "{kind: exact, value: [1, 2]}"),
        ("{'key': 1}", "{kind: exact, value: {key: 1}}"),
    ],
)
def test_cel_json_collection_return_types_are_admitted(
    tmp_path: Path, expression: str, validator: str
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
                "                kind: derived\n"
                f'                expression: "{expression}"\n'
                f"                validate: {validator}\n"
            )
        ),
    )

    scenario = compile_scenario(module)

    body = scenario.interactions[0].response.body
    assert body is not None and body.nodes[0].kind == "derived"


def test_cel_non_json_return_type_is_rejected(tmp_path: Path) -> None:
    module = write_module(
        tmp_path,
        one_interaction(
            response=(
                "        status: 200\n"
                "        body:\n"
                "          structured:\n"
                "            value:\n"
                "              $bsl:\n"
                "                kind: derived\n"
                "                expression: 'b\"not-json\"'\n"
                "                validate: {kind: exact, value: not-json}\n"
            )
        ),
    )

    with pytest.raises(SvcError) as caught:
        compile_scenario(module)

    assert caught.value.code == "invalid-double-cel"


def test_cel_static_scan_ignores_comments_and_event_string_literals(
    tmp_path: Path,
) -> None:
    scenario = one_interaction(
        response=(
            "        status: 200\n"
            "        body:\n"
            "          structured:\n"
            "            value:\n"
            "              $bsl:\n"
            "                kind: derived\n"
            "                expression: |\n"
            "                  // bindings.not_a_reference\n"
            "                  'ok'\n"
            "                validate: {kind: exact, value: ok}\n"
        )
    )
    scenario += (
        "  events:\n"
        "    - name: explicit\n"
        "      target: consumer.events\n"
        "      provenance: {kind: synthetic, source: https://example.invalid/event}\n"
        "      request:\n"
        "        method: POST\n"
        "        path: /event\n"
        "        body:\n"
        "          structured:\n"
        "            text:\n"
        "              $bsl:\n"
        "                kind: derived\n"
        "                expression: \"'request'\"\n"
        "                validate: {kind: exact, value: request}\n"
    )

    compiled = compile_scenario(write_module(tmp_path, scenario))

    assert compiled.events[0].name == "explicit"


def test_invalid_re2_pattern_is_a_stable_compile_error(tmp_path: Path) -> None:
    module = write_module(
        tmp_path,
        one_interaction(
            request=(
                "        body:\n"
                "          structured:\n"
                "            value:\n"
                "              $bsl:\n"
                "                kind: match\n"
                "                match: {kind: regex, pattern: '['}\n"
            )
        ),
    )

    with pytest.raises(SvcError) as caught:
        compile_scenario(module)

    assert caught.value.code == "invalid-double-regex"
    assert "diagnostic" in caught.value.details
