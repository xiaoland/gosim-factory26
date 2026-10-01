from __future__ import annotations
import json
import subprocess
import sys
from jsonschema import Draft202012Validator
from svc_cli.output_schema import (
    OUTPUT_SCHEMA_KEYS,
    generate_output_schema,
    read_output_schema,
)

from ..support.facts import output_observation


def test_double_schemas_are_registered_packaged_and_verdict_free() -> None:
    keys = (
        "double-validate",
        "double-start",
        "double-emit",
        "double-observe",
        "double-stop",
    )
    assert OUTPUT_SCHEMA_KEYS[-5:] == keys

    for key in keys:
        generated = generate_output_schema(key)
        encoded = json.dumps(generated, sort_keys=True)
        assert read_output_schema(key) == generated
        assert generated["x-svc-result-schema-version"] == 1
        assert "double-runtime-unavailable" in encoded
        assert "product_verdict" not in encoded
        assert "control_capability" not in encoded
        assert "carrier_pid" not in encoded
        assert "content_base64" not in encoded


def test_each_double_schema_rejects_an_unavailable_result_for_another_command() -> None:
    operations = ("validate", "start", "emit", "observe", "stop")

    for index, operation in enumerate(operations):
        validator = Draft202012Validator(generate_output_schema(f"double-{operation}"))
        unavailable = {
            "schema_version": 1,
            "command": f"double {operation}",
            "status": "double-runtime-unavailable",
            "continuation": "pip install 'sustainable-vibe-coding[double]'",
        }
        assert validator.is_valid(unavailable)

        unavailable["command"] = f"double {operations[(index + 1) % len(operations)]}"
        assert not validator.is_valid(unavailable)


def test_observe_and_stop_schemas_reject_contradictory_authority() -> None:
    unsealed = output_observation(sealed=False).as_dict()
    sealed = output_observation(sealed=True, status="stopped").as_dict()
    valid_observe = {
        "schema_version": 1,
        "command": "double observe",
        "observation": sealed,
        "authority": "sealed-snapshot",
        "control_status": "not-required",
    }
    valid_stop = {
        "schema_version": 1,
        "command": "double stop",
        "run_id": sealed["run_id"],
        "status": "stopped",
        "sealed": True,
        "idempotent": True,
        "observation": sealed,
    }
    contradictory_observe = {
        "schema_version": 1,
        "command": "double observe",
        "observation": unsealed,
        "authority": "sealed-snapshot",
        "control_status": "not-required",
    }
    contradictory_stop = {
        "schema_version": 1,
        "command": "double stop",
        "run_id": unsealed["run_id"],
        "status": "control-unavailable",
        "sealed": True,
        "idempotent": True,
        "observation": unsealed,
    }

    observe_validator = Draft202012Validator(generate_output_schema("double-observe"))
    stop_validator = Draft202012Validator(generate_output_schema("double-stop"))

    assert observe_validator.is_valid(valid_observe)
    assert stop_validator.is_valid(valid_stop)
    assert not observe_validator.is_valid(contradictory_observe)
    assert not stop_validator.is_valid(contradictory_stop)


def test_double_output_schema_imports_without_optional_runtime() -> None:
    script = r"""
import builtins

original_import = builtins.__import__
blocked = ("svc_cli.double", "ruamel", "jsonschema", "cel_expr_python")

def guarded_import(name, *args, **kwargs):
    if name in blocked or any(name.startswith(prefix + ".") for prefix in blocked):
        raise AssertionError(f"optional import attempted: {name}")
    return original_import(name, *args, **kwargs)

builtins.__import__ = guarded_import
import svc_cli.cli_output.double
import svc_cli.output_schema
"""
    completed = subprocess.run(
        (sys.executable, "-c", script),
        check=False,
        capture_output=True,
        text=True,
        timeout=5,
    )

    assert completed.returncode == 0, completed.stderr
