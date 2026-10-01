"""One immutable JSON reference authority for compiled double contracts."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, TypeAlias

from jsonschema import Draft202012Validator  # type: ignore[import-untyped]
from jsonschema.exceptions import ValidationError  # type: ignore[import-untyped]
from pydantic import JsonValue
from referencing import Registry
from referencing.jsonschema import DRAFT202012

from .model import SchemaResource


SchemaRegistry: TypeAlias = Registry[Any]


def build_schema_registry(
    resources: Sequence[SchemaResource],
) -> SchemaRegistry:
    """Build a frozen registry without a retrieval callback."""

    registry: SchemaRegistry = Registry()
    for resource in resources:
        registry = registry.with_resource(
            resource.uri,
            DRAFT202012.create_resource(resource.document),
        )
    return registry


def resolve_document_reference(
    documents: Mapping[Path, object],
    document_path: Path,
    reference: str,
) -> object:
    """Resolve one already-loaded local document reference and JSON Pointer."""

    registry: SchemaRegistry = Registry()
    for path, document in documents.items():
        registry = registry.with_resource(
            path.resolve().as_uri(),
            DRAFT202012.create_resource(document),
        )
    return (
        registry.resolver(document_path.resolve().as_uri()).lookup(reference).contents
    )


def check_schema_graph(
    schema: JsonValue, registry: SchemaRegistry
) -> tuple[object, ...]:
    """Check a selected schema and every reachable referenced schema."""

    checked: set[str] = set()
    checked_schemas: list[object] = []

    def check(candidate: object, resolver: Any) -> None:
        Draft202012Validator.check_schema(candidate)
        checked_schemas.append(candidate)
        scan(candidate, resolver)

    def scan(candidate: object, resolver: Any) -> None:
        if isinstance(candidate, Mapping):
            reference = candidate.get("$ref")
            if isinstance(reference, str) and reference not in checked:
                checked.add(reference)
                resolved = resolver.lookup(reference)
                check(resolved.contents, resolved.resolver)
            for key, item in candidate.items():
                if key != "$ref":
                    scan(item, resolver)
        elif isinstance(candidate, Sequence) and not isinstance(
            candidate, (str, bytes, bytearray)
        ):
            for item in candidate:
                scan(item, resolver)

    check(schema, registry.resolver())
    return tuple(checked_schemas)


def schema_validation_errors(
    schema: JsonValue,
    value: JsonValue,
    registry: SchemaRegistry,
) -> list[ValidationError]:
    """Return stable path-order instance validation failures."""

    return sorted(
        Draft202012Validator(schema, registry=registry).iter_errors(value),
        key=lambda item: list(item.path),
    )
