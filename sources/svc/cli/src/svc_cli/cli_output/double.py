"""Public machine results for the optional double runtime."""

from __future__ import annotations

from typing import Annotated, Literal, TypeAlias

from pydantic import ConfigDict, Field, model_validator

from .model import MachineModel


DoubleCommand: TypeAlias = Literal[
    "double validate",
    "double start",
    "double emit",
    "double observe",
    "double stop",
]


class DoubleRuntimeUnavailableOutput(MachineModel):
    """Base-install continuation shared by every double operation."""

    schema_version: Literal[1] = 1
    command: DoubleCommand
    status: Literal["double-runtime-unavailable"] = "double-runtime-unavailable"
    continuation: Literal["pip install 'sustainable-vibe-coding[double]'"] = (
        "pip install 'sustainable-vibe-coding[double]'"
    )


class DoubleValidateRuntimeUnavailableOutput(DoubleRuntimeUnavailableOutput):
    command: Literal["double validate"] = "double validate"


class DoubleStartRuntimeUnavailableOutput(DoubleRuntimeUnavailableOutput):
    command: Literal["double start"] = "double start"


class DoubleEmitRuntimeUnavailableOutput(DoubleRuntimeUnavailableOutput):
    command: Literal["double emit"] = "double emit"


class DoubleObserveRuntimeUnavailableOutput(DoubleRuntimeUnavailableOutput):
    command: Literal["double observe"] = "double observe"


class DoubleStopRuntimeUnavailableOutput(DoubleRuntimeUnavailableOutput):
    command: Literal["double stop"] = "double stop"


class DoubleDiagnosticOutput(MachineModel):
    machine_exclude_none = True

    code: str
    message: str
    path: str | None = None
    line: Annotated[int, Field(ge=1)] | None = None
    column: Annotated[int, Field(ge=1)] | None = None


class DoubleSnapshotOutput(MachineModel):
    """Identity-only projection; snapshot content is deliberately private."""

    logical_path: str
    sha256: str
    bytes: Annotated[int, Field(ge=0)]


class DoubleReplayOutput(MachineModel):
    seed: Annotated[int, Field(ge=0, le=18_446_744_073_709_551_615)]
    clock: str
    generators: tuple[str, ...]
    validators: tuple[str, ...]
    runtime: str


class DoubleTargetOutput(MachineModel):
    name: str
    origin: str
    remote: bool


class DoubleJournalFactsOutput(MachineModel):
    """Bounded public journal facts; captures and raw envelopes are absent."""

    machine_exclude_none = True

    interaction: str | None = None
    event: str | None = None
    method: str | None = None
    path: str | None = None
    target: str | None = None
    http_status: Annotated[int, Field(ge=100, le=599)] | None = None
    request_sha256: str | None = None
    response_sha256: str | None = None
    body_excerpt: str | None = None
    body_truncated: bool | None = None
    diagnostics: tuple[str, ...] = ()


class DoubleJournalEntryOutput(MachineModel):
    """One already-redacted boundary fact from the carrier journal."""

    sequence: Annotated[int, Field(ge=1)]
    at: str
    kind: Literal["request", "event", "runtime"]
    status: str
    facts: DoubleJournalFactsOutput


class DoubleJournalOutput(MachineModel):
    total: Annotated[int, Field(ge=0)]
    retained: Annotated[int, Field(ge=0)]
    omitted: Annotated[int, Field(ge=0)]
    entries: tuple[DoubleJournalEntryOutput, ...]

    @model_validator(mode="after")
    def _counts_describe_entries(self) -> "DoubleJournalOutput":
        if self.retained != len(self.entries):
            raise ValueError("retained journal count must equal the entry count")
        if self.total != self.retained + self.omitted:
            raise ValueError("journal total must equal retained plus omitted")
        sequences = tuple(entry.sequence for entry in self.entries)
        if sequences != tuple(sorted(set(sequences))):
            raise ValueError("retained journal sequences must be unique and ordered")
        if sequences and sequences[-1] > self.total:
            raise ValueError("journal sequence cannot exceed the total count")
        return self


class DoubleRunObservationOutput(MachineModel):
    machine_exclude_none = True

    run_id: str
    scenario_name: str
    status: Literal["bootstrapping", "ready", "stopping", "stopped", "failed"]
    sealed: bool
    responder_url: str | None
    scenario_digest: str
    run_context_digest: str
    replay: DoubleReplayOutput
    targets: tuple[DoubleTargetOutput, ...]
    bindings: tuple[str, ...]
    journal: DoubleJournalOutput
    nonclaims: tuple[str, ...]
    failure: str | None = None


class DoubleValidateOutput(MachineModel):
    machine_exclude_none = True

    schema_version: Literal[1] = 1
    command: Literal["double validate"] = "double validate"
    module: str
    scenario_name: str | None = None
    claim: str | None = None
    valid: bool
    scenario_digest: str | None = None
    fidelity: tuple[str, ...]
    nonclaims: tuple[str, ...]
    snapshots: tuple[DoubleSnapshotOutput, ...]
    diagnostic: DoubleDiagnosticOutput | None = None

    @model_validator(mode="after")
    def _validation_facts_are_complete(self) -> "DoubleValidateOutput":
        compiled = (self.scenario_name, self.claim, self.scenario_digest)
        if self.valid and (any(value is None for value in compiled) or self.diagnostic):
            raise ValueError("a valid module requires compiled facts and no diagnostic")
        if not self.valid and self.diagnostic is None:
            raise ValueError("an invalid module requires a diagnostic")
        return self


class DoubleStartOutput(MachineModel):
    schema_version: Literal[1] = 1
    command: Literal["double start"] = "double start"
    run_id: str
    module: str
    scenario_name: str
    responder_url: str
    scenario_digest: str
    run_context_digest: str
    replay: DoubleReplayOutput
    targets: tuple[DoubleTargetOutput, ...]
    nonclaims: tuple[str, ...]


class DoubleEmitOutput(MachineModel):
    machine_exclude_none = True

    schema_version: Literal[1] = 1
    command: Literal["double emit"] = "double emit"
    run_id: str
    event: str
    status: Literal[
        "acknowledged",
        "not-acknowledged",
        "transport-failed",
        "control-unavailable",
    ]
    target: str | None = None
    http_status: Annotated[int, Field(ge=100, le=599)] | None = None
    reason: str | None = None

    @model_validator(mode="after")
    def _acknowledgement_matches_delivery(self) -> "DoubleEmitOutput":
        if self.status == "acknowledged":
            if self.target is None or self.http_status is None:
                raise ValueError(
                    "an acknowledged event requires target and HTTP status"
                )
            if not 200 <= self.http_status < 300:
                raise ValueError("only a 2xx event response is acknowledged")
            return self
        if self.http_status is not None and 200 <= self.http_status < 300:
            raise ValueError("a 2xx event response must be acknowledged")
        if (
            self.status in {"transport-failed", "control-unavailable"}
            and self.http_status is not None
        ):
            raise ValueError(f"{self.status} cannot report an HTTP response")
        return self


class DoubleObserveOutput(MachineModel):
    model_config = ConfigDict(
        json_schema_extra={
            "allOf": [
                {
                    "if": {
                        "properties": {"authority": {"const": "active-carrier"}},
                        "required": ["authority"],
                    },
                    "then": {
                        "properties": {
                            "control_status": {"const": "available"},
                            "observation": {"properties": {"sealed": {"const": False}}},
                        }
                    },
                },
                {
                    "if": {
                        "properties": {"authority": {"const": "sealed-snapshot"}},
                        "required": ["authority"],
                    },
                    "then": {
                        "properties": {
                            "control_status": {"const": "not-required"},
                            "observation": {
                                "properties": {
                                    "sealed": {"const": True},
                                    "status": {"const": "stopped"},
                                }
                            },
                        }
                    },
                },
                {
                    "if": {
                        "properties": {"authority": {"const": "unsealed-projection"}},
                        "required": ["authority"],
                    },
                    "then": {
                        "properties": {
                            "control_status": {"const": "control-unavailable"},
                            "observation": {"properties": {"sealed": {"const": False}}},
                        }
                    },
                },
            ]
        }
    )

    schema_version: Literal[1] = 1
    command: Literal["double observe"] = "double observe"
    observation: DoubleRunObservationOutput
    authority: Literal["active-carrier", "sealed-snapshot", "unsealed-projection"]
    control_status: Literal["available", "not-required", "control-unavailable"]

    @model_validator(mode="after")
    def _authority_matches_observation(self) -> "DoubleObserveOutput":
        expected = {
            "active-carrier": (False, "available"),
            "sealed-snapshot": (True, "not-required"),
            "unsealed-projection": (False, "control-unavailable"),
        }
        sealed, control_status = expected[self.authority]
        if self.observation.sealed is not sealed:
            raise ValueError("observation seal does not match its authority")
        if self.control_status != control_status:
            raise ValueError("control status does not match observation authority")
        if self.authority == "sealed-snapshot" and self.observation.status != "stopped":
            raise ValueError("a sealed observation must have stopped status")
        return self


class DoubleStopOutput(MachineModel):
    model_config = ConfigDict(
        json_schema_extra={
            "allOf": [
                {
                    "if": {
                        "properties": {"status": {"const": "stopped"}},
                        "required": ["status"],
                    },
                    "then": {
                        "properties": {
                            "sealed": {"const": True},
                            "observation": {
                                "properties": {
                                    "sealed": {"const": True},
                                    "status": {"const": "stopped"},
                                }
                            },
                        }
                    },
                },
                {
                    "if": {
                        "properties": {"status": {"const": "control-unavailable"}},
                        "required": ["status"],
                    },
                    "then": {
                        "properties": {
                            "sealed": {"const": False},
                            "idempotent": {"const": False},
                            "observation": {"properties": {"sealed": {"const": False}}},
                        }
                    },
                },
            ]
        }
    )

    schema_version: Literal[1] = 1
    command: Literal["double stop"] = "double stop"
    run_id: str
    status: Literal["stopped", "control-unavailable"]
    sealed: bool
    idempotent: bool
    observation: DoubleRunObservationOutput

    @model_validator(mode="after")
    def _stop_state_is_authoritative(self) -> "DoubleStopOutput":
        if self.status == "stopped":
            if not self.sealed or not self.observation.sealed:
                raise ValueError("a stopped result requires the sealed observation")
            if self.observation.status != "stopped":
                raise ValueError("a stopped result requires a stopped observation")
            return self
        if self.sealed or self.observation.sealed:
            raise ValueError(
                "control-unavailable may expose only an unsealed observation"
            )
        if self.idempotent:
            raise ValueError("control-unavailable is not an idempotent stop")
        return self
