from __future__ import annotations

import hashlib
import json

import pytest
from pydantic import TypeAdapter, ValidationError

from svc_cli.double.compiler import compile_scenario
from svc_cli.double.model import (
    ExactMatcher,
    LiteralValueNode,
    Matcher,
    Scenario,
    ValueNode,
)

from ..support.scenarios import PAYMENT_MODULE


MATCHER_ADAPTER = TypeAdapter(Matcher)
VALUE_NODE_ADAPTER = TypeAdapter(ValueNode)


def test_tagged_ir_rejects_cross_variant_and_missing_fields() -> None:
    invalid_values = (
        (MATCHER_ADAPTER, {"kind": "exact", "value": 1, "values": (1,)}),
        (MATCHER_ADAPTER, {"kind": "range"}),
        (
            VALUE_NODE_ADAPTER,
            {
                "kind": "derived",
                "path": (),
                "validator": {"kind": "exact", "value": None},
            },
        ),
        (
            VALUE_NODE_ADAPTER,
            {
                "kind": "capture",
                "path": (),
                "name": "captured",
                "matcher": {"kind": "exact", "value": 1},
                "expression": "request.body",
            },
        ),
    )

    for adapter, value in invalid_values:
        with pytest.raises(ValidationError):
            adapter.validate_python(value)

    assert ExactMatcher(value=None).value is None
    assert LiteralValueNode(path=(), value=None).value is None


def test_tagged_ir_round_trip_preserves_the_serialized_contract() -> None:
    scenario = compile_scenario(PAYMENT_MODULE)
    payload = scenario.model_dump(mode="json")
    portable_payload = dict(payload)
    portable_payload["module_path"] = "<module>"
    portable_payload["workspace_root"] = "<workspace>"
    encoded = json.dumps(
        portable_payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()

    assert scenario.scenario_digest == (
        "4e41468d6aa47d73d2b6272143a6fce773fd258b67ec5402ed2e8cb7e09b6070"
    )
    assert hashlib.sha256(encoded).hexdigest() == (
        "d96fb594f3002120ec092941ef1a3e2c933a6b3b59a3e37df34104dfa14c0230"
    )
    assert Scenario.model_validate_json(json.dumps(payload)) == scenario
