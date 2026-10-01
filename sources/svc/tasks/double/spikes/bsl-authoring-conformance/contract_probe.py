#!/usr/bin/env python3
"""Disposable OpenAPI 3.1/JSON Schema probe; not product code."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from referencing import Registry
from referencing.jsonschema import DRAFT202012
from ruamel.yaml import YAML


def load_yaml(path: Path) -> dict[str, Any]:
    yaml = YAML(typ="rt", pure=True)
    yaml.version = (1, 2)
    yaml.allow_duplicate_keys = False
    yaml.constructor.add_constructor(
        "tag:yaml.org,2002:timestamp",
        lambda loader, node: loader.construct_scalar(node),
    )
    value = yaml.load(path.read_text())
    if not isinstance(value, dict):
        raise ValueError("OpenAPI source must be a mapping")
    return value


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    args = parser.parse_args()
    document = load_yaml(args.source)
    if document.get("openapi") != "3.1.0":
        raise ValueError("spike supports exactly OpenAPI 3.1.0")
    operation = document["paths"]["/v1/rides"]["post"]
    if operation.get("operationId") != "createRide":
        raise ValueError("selected operation is absent")

    base = "urn:svc:spike:mobility-openapi"
    registry = Registry().with_resource(base, DRAFT202012.create_resource(document))
    request_schema = operation["requestBody"]["content"]["application/json"]["schema"]
    response_schema = operation["responses"]["201"]["content"]["application/json"]["schema"]
    request_validator = Draft202012Validator(
        {"$ref": base + request_schema["$ref"]}, registry=registry
    )
    response_validator = Draft202012Validator(
        {"$ref": base + response_schema["$ref"]}, registry=registry
    )

    valid_request = {"externalId": "123e4567-e89b-42d3-a456-426614174000"}
    invalid_uuid = {"externalId": "not-a-uuid"}
    valid_response = {
        "rideId": "ride_nqybmozaqwlbsexa",
        "vehicleRegistration": "BJ16 JDB",
    }
    invalid_response = {
        "rideId": "ride_nqybmozaqwlbsexa",
        "vehicleRegistration": "random",
    }
    report = {
        "operation_selected": True,
        "valid_request_schema_errors": [
            error.message for error in request_validator.iter_errors(valid_request)
        ],
        "invalid_uuid_passes_without_explicit_format_assertion": request_validator.is_valid(
            invalid_uuid
        ),
        "valid_response_schema_errors": [
            error.message for error in response_validator.iter_errors(valid_response)
        ],
        "invalid_response_schema_errors": [
            error.message for error in response_validator.iter_errors(invalid_response)
        ],
        "fidelity_claim": "selected-operation-schema",
        "behavioral_fidelity_claimed": False,
        "full_openapi_document_conformance_claimed": False,
        "remote_reference_retrieval": False,
    }
    assert report["valid_request_schema_errors"] == []
    assert report["valid_response_schema_errors"] == []
    assert report["invalid_uuid_passes_without_explicit_format_assertion"] is True
    assert report["invalid_response_schema_errors"]
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
