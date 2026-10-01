"""Test whether strict IR TypeAdapters can replace authored YAML shape checks."""

from __future__ import annotations

from pydantic import TypeAdapter, ValidationError
from ruamel.yaml import YAML

from svc_cli.double.model import Matcher, ValueNode


MATCHER = TypeAdapter(Matcher)
VALUE_NODE = TypeAdapter(ValueNode)


def errors(adapter: TypeAdapter, value: object) -> list[dict[str, object]]:
    try:
        adapter.validate_python(value)
    except ValidationError as error:
        return error.errors(include_url=False, include_context=False)
    raise AssertionError(f"invalid value was accepted: {value!r}")


def main() -> None:
    parser = YAML(typ="rt", pure=True)

    authored_enum = parser.load("kind: enum\nvalues: [one, two]\n")
    enum_errors = errors(MATCHER, authored_enum)
    assert [item["type"] for item in enum_errors] == ["tuple_type"]
    assert enum_errors[0]["loc"] == ("enum", "values")

    cross_variant = parser.load("kind: exact\nvalues: [one]\n")
    cross_variant_errors = errors(MATCHER, cross_variant)
    assert [item["type"] for item in cross_variant_errors] == [
        "missing",
        "none_required",
    ]
    assert cross_variant.lc.key("values") == (1, 0)

    authored_range_null = parser.load("kind: range\nminimum: null\n")
    range_errors = errors(MATCHER, authored_range_null)
    assert range_errors[0]["type"] == "value_error"
    assert "requires minimum or maximum" in str(range_errors[0]["msg"])
    assert "cannot be null" not in str(range_errors[0]["msg"])

    non_finite = MATCHER.validate_python({"kind": "exact", "value": float("nan")})
    assert non_finite.value != non_finite.value

    authored_derived = parser.load(
        "kind: derived\n"
        "expression: bindings.value\n"
        "validate: {kind: exact, value: one}\n"
    )
    value_errors = errors(VALUE_NODE, authored_derived)
    value_error_types = [item["type"] for item in value_errors]
    assert "missing" in value_error_types
    assert "extra_forbidden" in value_error_types

    evidence = {
        "yaml_list_to_ir_tuple": [item["type"] for item in enum_errors],
        "cross_variant_projection": [
            item["type"] for item in cross_variant_errors
        ],
        "range_null_message": range_errors[0]["msg"],
        "json_nan_admitted_by_ir_adapter": True,
        "authored_value_node_impedance": value_error_types,
        "ruamel_source_location_available": list(cross_variant.lc.key("values")),
    }
    for key, value in evidence.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
