"""Typed ownership and deterministic serialization for CLI machine output."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import IO, Any, ClassVar, Literal, TypeAlias

from pydantic import BaseModel, ConfigDict, JsonValue, RootModel

from ..errors import Failure, SvcError


class MachineModel(BaseModel):
    """Strict immutable base for a public SVC machine-protocol value."""

    model_config = ConfigDict(
        extra="forbid", frozen=True, strict=True, populate_by_name=True
    )
    machine_exclude_none: ClassVar[bool] = False

    def as_dict(self) -> dict[str, JsonValue]:
        """Return the same typed projection used by the CLI serializer."""

        value = self.model_dump(
            mode="json",
            by_alias=True,
            exclude_none=self.machine_exclude_none,
        )
        assert isinstance(value, dict)
        return value


class MachineErrorBody(MachineModel):
    code: str
    message: str
    details: dict[str, JsonValue]


class MachineError(MachineModel):
    schema_version: Literal[1] = 1
    error: MachineErrorBody


class CliUsageOutput(MachineModel):
    code: Literal["invalid-cli-usage"] = "invalid-cli-usage"
    message: str


class UnscopedMachineObject(RootModel[dict[str, JsonValue]]):
    """Temporary boundary for telemetry/analysis protocols outside this unit."""

    model_config = ConfigDict(frozen=True, strict=True)


MachineOutput: TypeAlias = MachineModel | UnscopedMachineObject


def project_error(error: SvcError) -> MachineError:
    return MachineError(error=project_failure(error.snapshot()))


def project_failure(failure: Failure) -> MachineErrorBody:
    details = json_compatible(failure.details)
    assert isinstance(details, dict)
    return MachineErrorBody(
        code=failure.code,
        message=failure.message,
        details=details,
    )


def json_compatible(value: Any) -> JsonValue:
    """Project diagnostic values onto JSON without inventing repr protocols."""

    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, Mapping):
        return {str(key): json_compatible(item) for key, item in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [json_compatible(item) for item in value]
    raise TypeError(f"Machine output contains a non-JSON value: {type(value).__name__}")


def unscoped_machine_object(value: Mapping[str, Any]) -> UnscopedMachineObject:
    projected = json_compatible(value)
    if not isinstance(projected, dict):
        raise TypeError("Machine output root must be an object")
    return UnscopedMachineObject(projected)


def dump_machine_output(value: MachineOutput, stream: IO[str]) -> None:
    """Write one sorted, compact UTF-8 JSON object and a trailing newline."""

    payload = value.model_dump(
        mode="json",
        by_alias=True,
        exclude_none=getattr(value, "machine_exclude_none", False),
    )
    json.dump(
        payload,
        stream,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    stream.write("\n")
