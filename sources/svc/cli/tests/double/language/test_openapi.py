from __future__ import annotations
from pathlib import Path
import pytest
from jsonschema import Draft202012Validator  # type: ignore[import-untyped]
from referencing.exceptions import Unresolvable
from svc_cli.double.compiler import (
    compile_scenario,
)
from svc_cli.double.schema_registry import build_schema_registry
from svc_cli.errors import SvcError

from ..support.scenarios import LANGUAGE_FIXTURES, one_interaction, write_module


def test_remote_openapi_reference_is_rejected_without_retrieval(tmp_path: Path) -> None:
    (tmp_path / "openapi.yaml").write_text(
        """\
openapi: 3.1.0
info: {title: fixture, version: 1.0.0}
paths:
  /call:
    post:
      requestBody:
        content:
          application/json:
            schema: {$ref: 'https://provider.invalid/schema.json'}
      responses:
        '200': {description: ok}
""",
        encoding="utf-8",
    )
    scenario = one_interaction().replace(
        "boundary: {name: provider, protocol: http}",
        (
            "boundary:\n"
            "    name: provider\n"
            "    protocol: http\n"
            "    contract: {kind: openapi-3.1-operation, source: openapi.yaml, method: POST, path: /call}"
        ),
    )
    module = write_module(tmp_path, scenario)

    with pytest.raises(SvcError) as caught:
        compile_scenario(module)

    assert caught.value.code == "invalid-double-contract"
    assert caught.value.details["ref"] == "https://provider.invalid/schema.json"


def test_local_openapi_path_item_ref_and_canonical_dialect_are_admitted(
    tmp_path: Path,
) -> None:
    (tmp_path / "openapi.yaml").write_text(
        """\
openapi: 3.1.0
jsonSchemaDialect: https://spec.openapis.org/oas/3.1/dialect/base
info: {title: fixture, version: 1.0.0}
paths:
  /call:
    $ref: '#/components/pathItems/Call'
components:
  pathItems:
    Call:
      post:
        responses:
          '200': {description: ok}
""",
        encoding="utf-8",
    )
    scenario = one_interaction().replace(
        "boundary: {name: provider, protocol: http}",
        (
            "boundary:\n"
            "    name: provider\n"
            "    protocol: http\n"
            "    contract: {kind: openapi-3.1-operation, source: openapi.yaml, method: POST, path: /call}"
        ),
    )

    compiled = compile_scenario(write_module(tmp_path, scenario))

    assert compiled.contract is not None
    assert compiled.contract.method == "POST"


def test_missing_local_openapi_pointer_is_rejected_by_registry(
    tmp_path: Path,
) -> None:
    (tmp_path / "openapi.yaml").write_text(
        """\
openapi: 3.1.0
info: {title: fixture, version: 1.0.0}
paths:
  /call:
    post:
      requestBody:
        content:
          application/json:
            schema: {$ref: '#/$defs/Missing'}
      responses:
        '200': {description: ok}
""",
        encoding="utf-8",
    )
    scenario = one_interaction().replace(
        "boundary: {name: provider, protocol: http}",
        (
            "boundary:\n"
            "    name: provider\n"
            "    protocol: http\n"
            "    contract: {kind: openapi-3.1-operation, source: openapi.yaml, method: POST, path: /call}"
        ),
    )

    with pytest.raises(SvcError) as caught:
        compile_scenario(write_module(tmp_path, scenario))

    assert caught.value.code == "invalid-double-contract"
    assert caught.value.details["ref"] == "#/$defs/Missing"


def test_unselected_remote_openapi_reference_is_not_scenario_authority(
    tmp_path: Path,
) -> None:
    (tmp_path / "openapi.yaml").write_text(
        """\
openapi: 3.1.0
info: {title: fixture, version: 1.0.0}
paths:
  /call:
    post:
      responses:
        '200': {description: ok}
  /unselected:
    post:
      requestBody:
        content:
          application/json:
            schema: {$ref: 'https://provider.invalid/unselected.json'}
      responses:
        '200': {description: ok}
""",
        encoding="utf-8",
    )
    scenario = one_interaction().replace(
        "boundary: {name: provider, protocol: http}",
        (
            "boundary:\n"
            "    name: provider\n"
            "    protocol: http\n"
            "    contract: {kind: openapi-3.1-operation, source: openapi.yaml, method: POST, path: /call}"
        ),
    )

    compiled = compile_scenario(write_module(tmp_path, scenario))

    assert compiled.contract is not None
    assert len(compiled.contract.schema_resources) == 1


def test_cross_file_recursive_openapi_schema_uses_immutable_registry() -> None:
    scenario = compile_scenario(LANGUAGE_FIXTURES / "recursive.double.yaml")

    contract = scenario.contract
    assert contract is not None and contract.request_schema is not None
    assert len(contract.schema_resources) == 2
    assert all(
        resource.uri.startswith("urn:svc:double:schema-resource:")
        for resource in contract.schema_resources
    )
    assert all(
        resource.snapshot_sha256 in {snapshot.sha256 for snapshot in scenario.snapshots}
        for resource in contract.schema_resources
    )
    assert "urn:svc:double:schema-resource:" in str(contract.request_schema)

    registry = build_schema_registry(contract.schema_resources)
    validator = Draft202012Validator(contract.request_schema, registry=registry)

    assert validator.is_valid(
        {"value": "root", "next": {"value": "child", "next": None}}
    )
    assert not validator.is_valid({"value": "root", "next": {"value": 1}})
    with pytest.raises(Unresolvable):
        registry.resolver().lookup("https://provider.invalid/absent-schema")


@pytest.mark.parametrize(
    ("version", "contract_path", "dialect", "code"),
    [
        ("3.0.3", "/call", "", "invalid-double-contract"),
        ("3.1.0", "/calls/{id}", "", "unsupported-double-contract-path"),
        (
            "3.1.0",
            "/call",
            "jsonSchemaDialect: https://example.invalid/custom\n",
            "invalid-double-contract",
        ),
    ],
)
def test_openapi_profile_rejects_unsupported_versions_templates_and_dialects(
    tmp_path: Path, version: str, contract_path: str, dialect: str, code: str
) -> None:
    (tmp_path / "openapi.yaml").write_text(
        (
            f"openapi: {version}\n"
            f"{dialect}"
            "info: {title: fixture, version: 1.0.0}\n"
            "paths:\n"
            f"  {contract_path}:\n"
            "    post:\n"
            "      responses:\n"
            "        '200': {description: ok}\n"
        ),
        encoding="utf-8",
    )
    scenario = one_interaction().replace(
        "boundary: {name: provider, protocol: http}",
        (
            "boundary:\n"
            "    name: provider\n"
            "    protocol: http\n"
            "    contract: "
            f"{{kind: openapi-3.1-operation, source: openapi.yaml, method: POST, path: '{contract_path}'}}"
        ),
    )
    module = write_module(tmp_path, scenario)

    with pytest.raises(SvcError) as caught:
        compile_scenario(module)

    assert caught.value.code == code
