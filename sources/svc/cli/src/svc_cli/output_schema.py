"""Packaged JSON Schema discovery for typed core CLI machine output."""

from __future__ import annotations

import json
from dataclasses import dataclass
from importlib import resources
from typing import Any, TypeAlias

from pydantic import JsonValue, TypeAdapter

from .cli_output.dev import (
    DevEnsureOutput,
    DevIdentityOutput,
    DevStatusOutput,
    DevStopOutput,
)
from .cli_output.double import (
    DoubleEmitRuntimeUnavailableOutput,
    DoubleEmitOutput,
    DoubleObserveRuntimeUnavailableOutput,
    DoubleObserveOutput,
    DoubleStartRuntimeUnavailableOutput,
    DoubleStartOutput,
    DoubleStopRuntimeUnavailableOutput,
    DoubleStopOutput,
    DoubleValidateRuntimeUnavailableOutput,
    DoubleValidateOutput,
)
from .cli_output.lookup import LookupOutput
from .cli_output.project import InitApplyOutput, InitPlanOutput, RootStatusOutput
from .cli_output.model import CliUsageOutput, MachineError
from .cli_output.run import RunReceipt
from .cli_output.upgrade import UpgradeApplyOutput, UpgradePlanOutput


LookupMachineOutput: TypeAlias = LookupOutput | MachineError | CliUsageOutput
InitMachineOutput: TypeAlias = (
    InitPlanOutput | InitApplyOutput | MachineError | CliUsageOutput
)
StatusMachineOutput: TypeAlias = RootStatusOutput | MachineError | CliUsageOutput
UpgradeMachineOutput: TypeAlias = (
    UpgradePlanOutput | UpgradeApplyOutput | MachineError | CliUsageOutput
)
DevIdentityMachineOutput: TypeAlias = DevIdentityOutput | MachineError | CliUsageOutput
DevStatusMachineOutput: TypeAlias = DevStatusOutput | MachineError | CliUsageOutput
DevEnsureMachineOutput: TypeAlias = DevEnsureOutput | MachineError | CliUsageOutput
DevStopMachineOutput: TypeAlias = DevStopOutput | MachineError | CliUsageOutput
RunMachineOutput: TypeAlias = RunReceipt | MachineError | CliUsageOutput
DoubleValidateMachineOutput: TypeAlias = (
    DoubleValidateOutput
    | DoubleValidateRuntimeUnavailableOutput
    | MachineError
    | CliUsageOutput
)
DoubleStartMachineOutput: TypeAlias = (
    DoubleStartOutput
    | DoubleStartRuntimeUnavailableOutput
    | MachineError
    | CliUsageOutput
)
DoubleEmitMachineOutput: TypeAlias = (
    DoubleEmitOutput
    | DoubleEmitRuntimeUnavailableOutput
    | MachineError
    | CliUsageOutput
)
DoubleObserveMachineOutput: TypeAlias = (
    DoubleObserveOutput
    | DoubleObserveRuntimeUnavailableOutput
    | MachineError
    | CliUsageOutput
)
DoubleStopMachineOutput: TypeAlias = (
    DoubleStopOutput
    | DoubleStopRuntimeUnavailableOutput
    | MachineError
    | CliUsageOutput
)

RegisteredMachineOutput: TypeAlias = (
    LookupOutput
    | InitPlanOutput
    | InitApplyOutput
    | RootStatusOutput
    | UpgradePlanOutput
    | UpgradeApplyOutput
    | DevIdentityOutput
    | DevStatusOutput
    | DevEnsureOutput
    | DevStopOutput
    | RunReceipt
    | DoubleValidateOutput
    | DoubleStartOutput
    | DoubleEmitOutput
    | DoubleObserveOutput
    | DoubleStopOutput
    | DoubleValidateRuntimeUnavailableOutput
    | DoubleStartRuntimeUnavailableOutput
    | DoubleEmitRuntimeUnavailableOutput
    | DoubleObserveRuntimeUnavailableOutput
    | DoubleStopRuntimeUnavailableOutput
    | MachineError
    | CliUsageOutput
)


@dataclass(frozen=True)
class OutputSchemaSpec:
    result_schema_version: int
    adapter: TypeAdapter[Any]


OUTPUT_SCHEMA_SPECS = {
    "lookup": OutputSchemaSpec(2, TypeAdapter(LookupMachineOutput)),
    "init": OutputSchemaSpec(3, TypeAdapter(InitMachineOutput)),
    "status": OutputSchemaSpec(2, TypeAdapter(StatusMachineOutput)),
    "upgrade": OutputSchemaSpec(2, TypeAdapter(UpgradeMachineOutput)),
    "dev-identity": OutputSchemaSpec(2, TypeAdapter(DevIdentityMachineOutput)),
    "dev-status": OutputSchemaSpec(2, TypeAdapter(DevStatusMachineOutput)),
    "dev-ensure": OutputSchemaSpec(2, TypeAdapter(DevEnsureMachineOutput)),
    "dev-stop": OutputSchemaSpec(2, TypeAdapter(DevStopMachineOutput)),
    "run": OutputSchemaSpec(2, TypeAdapter(RunMachineOutput)),
    "double-validate": OutputSchemaSpec(1, TypeAdapter(DoubleValidateMachineOutput)),
    "double-start": OutputSchemaSpec(1, TypeAdapter(DoubleStartMachineOutput)),
    "double-emit": OutputSchemaSpec(1, TypeAdapter(DoubleEmitMachineOutput)),
    "double-observe": OutputSchemaSpec(1, TypeAdapter(DoubleObserveMachineOutput)),
    "double-stop": OutputSchemaSpec(1, TypeAdapter(DoubleStopMachineOutput)),
}
OUTPUT_SCHEMA_KEYS = tuple(OUTPUT_SCHEMA_SPECS)


def generate_output_schema(key: str) -> dict[str, JsonValue]:
    """Generate one deterministic schema from the registered serialization model."""

    try:
        spec = OUTPUT_SCHEMA_SPECS[key]
    except KeyError as error:
        raise ValueError(f"Unknown output schema key: {key}") from error
    generated = spec.adapter.json_schema(mode="serialization")
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"urn:svc:cli-output:{key}:v{spec.result_schema_version}",
        "title": f"SVC {key} machine output",
        "x-svc-result-schema-version": spec.result_schema_version,
        **generated,
    }


def read_output_schema(key: str) -> dict[str, JsonValue]:
    """Read the packaged projection returned to consumers by --json-schema."""

    if key not in OUTPUT_SCHEMA_SPECS:
        raise ValueError(f"Unknown output schema key: {key}")
    resource = resources.files("svc_cli").joinpath(
        "data", "output-schemas", f"{key}.json"
    )
    value = json.loads(resource.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Packaged output schema {key} is not a JSON object")
    return value
