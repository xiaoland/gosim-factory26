"""Prove one immutable, no-retrieval registry can own recursive local schemas."""

from __future__ import annotations

from pathlib import Path

from jsonschema import Draft202012Validator  # type: ignore[import-untyped]
from referencing import Registry
from referencing.jsonschema import DRAFT202012
from ruamel.yaml import YAML


ROOT_URI = "https://svc.invalid/workspace/root.yaml"
CHILD_URI = "https://svc.invalid/workspace/child.yaml"

ROOT = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": ROOT_URI,
    "$ref": "child.yaml#/$defs/node",
}
CHILD = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": CHILD_URI,
    "$defs": {
        "node": {
            "anyOf": [
                {"type": "null"},
                {
                    "type": "object",
                    "required": ["value", "next"],
                    "properties": {
                        "value": {"type": "string"},
                        "next": {"$ref": "#/$defs/node"},
                    },
                    "additionalProperties": False,
                },
            ]
        }
    },
}


def actual_openapi_contract_evidence() -> dict[str, list[int]]:
    repository = Path(__file__).resolve().parents[4]
    contracts = repository / "svc_cli/tests/double/fixtures/language/contracts"
    yaml = YAML(typ="safe", pure=True)
    base = "https://svc.invalid/contracts/"
    cases = (
        (
            "payment",
            "payment.openapi.yaml",
            "schemas.yaml",
            "/paths/~1v1~1payments/post/requestBody/content/application~1json/schema",
            {"externalId": "00000000-0000-4000-8000-000000000001"},
            {"externalId": 1},
        ),
        (
            "recursive",
            "recursive.openapi.yaml",
            "recursive.schemas.yaml",
            "/paths/~1v1~1nodes/post/requestBody/content/application~1json/schema",
            {"value": "a", "next": {"value": "b", "next": None}},
            {"value": 1, "next": None},
        ),
    )
    evidence: dict[str, list[int]] = {}
    for name, openapi_name, schema_name, pointer, valid, invalid in cases:
        documents = {
            openapi_name: yaml.load(
                (contracts / openapi_name).read_text(encoding="utf-8")
            ),
            schema_name: yaml.load(
                (contracts / schema_name).read_text(encoding="utf-8")
            ),
        }
        registry = Registry().with_resources(
            (base + filename, DRAFT202012.create_resource(document))
            for filename, document in documents.items()
        )
        selected = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$ref": base + openapi_name + "#" + pointer,
        }
        validator = Draft202012Validator(selected, registry=registry)
        counts = [
            len(list(validator.iter_errors(valid))),
            len(list(validator.iter_errors(invalid))),
        ]
        assert counts[0] == 0 and counts[1] > 0
        evidence[name] = counts
    return evidence


def main() -> None:
    registry = Registry().with_resources(
        (
            (ROOT_URI, DRAFT202012.create_resource(ROOT)),
            (CHILD_URI, DRAFT202012.create_resource(CHILD)),
        )
    )
    validator = Draft202012Validator(ROOT, registry=registry)
    valid = {"value": "a", "next": {"value": "b", "next": None}}
    invalid = {"value": 1, "next": None}

    assert list(validator.iter_errors(valid)) == []
    invalid_errors = [error.message for error in validator.iter_errors(invalid)]
    assert invalid_errors

    remote = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$ref": "https://provider.example/remote-schema",
    }
    try:
        list(Draft202012Validator(remote, registry=registry).iter_errors({}))
    except Exception as error:
        remote_error = f"{type(error).__name__}: {error}"
    else:
        raise AssertionError("an absent remote resource was unexpectedly resolved")
    assert "Unresolvable" in remote_error
    openapi_evidence = actual_openapi_contract_evidence()

    print(f"registry-resources: {len(registry)}")
    print("recursive-valid-errors: 0")
    print(f"recursive-invalid-errors: {len(invalid_errors)}")
    print(f"remote-reference: {remote_error}")
    print(f"actual-openapi-valid-invalid-error-counts: {openapi_evidence}")
    print(
        "finding: referencing can own relative pointers, recursion, and fail-closed "
        "absence; SVC still owns URI assignment, contained loading, and snapshots"
    )


if __name__ == "__main__":
    main()
