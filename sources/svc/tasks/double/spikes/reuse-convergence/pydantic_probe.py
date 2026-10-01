"""Prove that discriminated IR variants make invalid BSL states unrepresentable."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    JsonValue,
    TypeAdapter,
    ValidationError,
)
from pydantic.functional_validators import model_validator
from ruamel.yaml import YAML


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class ExactMatcher(StrictModel):
    kind: Literal["exact"]
    value: JsonValue


class EnumMatcher(StrictModel):
    kind: Literal["enum"]
    values: tuple[JsonValue, ...]


class RangeMatcher(StrictModel):
    kind: Literal["range"]
    minimum: int | float | None = None
    maximum: int | float | None = None

    @model_validator(mode="after")
    def require_bound(self) -> RangeMatcher:
        if self.minimum is None and self.maximum is None:
            raise ValueError("range requires at least one bound")
        return self


class RegexMatcher(StrictModel):
    kind: Literal["regex"]
    pattern: str


class SemanticMatcher(StrictModel):
    kind: Literal["semantic"]
    semantic: str
    using: str


Matcher = Annotated[
    ExactMatcher | EnumMatcher | RangeMatcher | RegexMatcher | SemanticMatcher,
    Field(discriminator="kind"),
]
MATCHER = TypeAdapter(Matcher)


class LiteralNode(StrictModel):
    kind: Literal["literal"]
    path: tuple[str | int, ...]
    value: JsonValue
    bind: str | None = None


class MatchNode(StrictModel):
    kind: Literal["match"]
    path: tuple[str | int, ...]
    matcher: Matcher
    value: JsonValue | None = None


class CaptureNode(StrictModel):
    kind: Literal["capture"]
    path: tuple[str | int, ...]
    name: str
    matcher: Matcher
    value: JsonValue | None = None


class ExampleNode(StrictModel):
    kind: Literal["example"]
    path: tuple[str | int, ...]
    value: JsonValue
    validator: Matcher | None = None
    bind: str | None = None


class DerivedNode(StrictModel):
    kind: Literal["derived"]
    path: tuple[str | int, ...]
    expression: str
    validator: Matcher | None = None
    bind: str | None = None


class GeneratedNode(StrictModel):
    kind: Literal["generated"]
    path: tuple[str | int, ...]
    semantic: str
    using: str
    options: dict[str, JsonValue]
    validator: Matcher
    bind: str | None = None


class ManagedNode(StrictModel):
    kind: Literal["managed"]
    path: tuple[str | int, ...]
    snapshot_sha256: str
    media_type: str | None = None
    bind: str | None = None


ValueNode = Annotated[
    LiteralNode
    | MatchNode
    | CaptureNode
    | ExampleNode
    | DerivedNode
    | GeneratedNode
    | ManagedNode,
    Field(discriminator="kind"),
]
VALUE_NODE = TypeAdapter(ValueNode)


def rejected(adapter: TypeAdapter, value: object) -> list[str]:
    try:
        adapter.validate_python(value)
    except ValidationError as error:
        return [item["type"] for item in error.errors()]
    raise AssertionError(f"invalid value was accepted: {value!r}")


def main() -> None:
    exact = MATCHER.validate_python({"kind": "exact", "value": 1})
    derived = VALUE_NODE.validate_python(
        {"kind": "derived", "path": (), "expression": "bindings.external_id"}
    )

    evidence = {
        "valid_variants": [type(exact).__name__, type(derived).__name__],
        "invalid_exact_fields": rejected(MATCHER, {"kind": "exact", "values": (1,)}),
        "invalid_empty_range": rejected(MATCHER, {"kind": "range"}),
        "invalid_derived_without_expression": rejected(
            VALUE_NODE, {"kind": "derived", "path": ()}
        ),
        "invalid_capture_with_expression": rejected(
            VALUE_NODE,
            {"kind": "capture", "path": (), "expression": "request.body"},
        ),
    }
    authored = YAML(typ="rt").load("kind: exact\nvalues: [1]\n")
    try:
        MATCHER.validate_python(authored)
    except ValidationError as error:
        extra = next(
            item for item in error.errors() if item["type"] == "extra_forbidden"
        )
        authored_location = authored.lc.key(str(extra["loc"][-1]))
    else:
        raise AssertionError("invalid ruamel-authored matcher was accepted")
    evidence["ruamel_error_path"] = list(extra["loc"])
    evidence["ruamel_error_line_column_zero_based"] = list(authored_location)

    assert all(evidence[key] for key in evidence if key.startswith("invalid_"))
    for key, value in evidence.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
