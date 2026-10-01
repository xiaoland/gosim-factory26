"""Payload-bearing provider-neutral trajectory v2 wire contract."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Annotated, Any, Literal, Mapping, TypeAlias

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    JsonValue,
    TypeAdapter,
    ValidationError,
    model_validator,
)

from .trajectory import TrajectoryError, canonical_json_bytes


TRAJECTORY_SCHEMA_V2 = "svc.trajectory/v2"
_NAMESPACED = re.compile(r"^[a-z][a-z0-9_.-]*/v[1-9][0-9]*$")


class TrajectoryV2Model(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)


class SourceRef(TrajectoryV2Model):
    material: str = Field(min_length=1)
    record_id: str | None = Field(default=None, min_length=1)
    line: int | None = Field(default=None, ge=0)
    byte_start: int | None = Field(default=None, ge=0)
    byte_end: int | None = Field(default=None, ge=0)
    component: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def validate_range(self) -> "SourceRef":
        if (self.byte_start is None) != (self.byte_end is None):
            raise ValueError("byte_start and byte_end must be supplied together")
        if self.byte_start is not None and self.byte_end <= self.byte_start:
            raise ValueError("byte range must be non-empty")
        return self


class CoverageIssue(TrajectoryV2Model):
    issue_id: str = Field(min_length=1)
    code: str = Field(min_length=1)
    message: str = Field(min_length=1)
    object_refs: tuple[str, ...] = ()


CoverageDomain: TypeAlias = Literal[
    "content",
    "tool_linkage",
    "relation_mapping",
    "descendant_closure",
    "history_branch",
    "usage",
    "timestamps",
    "terminal_state",
]


class Coverage(TrajectoryV2Model):
    domain: CoverageDomain
    status: Literal["complete", "partial", "unavailable"]
    issue_ids: tuple[str, ...] = ()

    @model_validator(mode="after")
    def issues_match_status(self) -> "Coverage":
        if self.status == "complete" and self.issue_ids:
            raise ValueError("complete coverage cannot cite issues")
        if self.status != "complete" and not self.issue_ids:
            raise ValueError("partial or unavailable coverage must cite an issue")
        return self


class HeaderRecord(TrajectoryV2Model):
    type: Literal["header"]
    trajectory_schema: Literal["svc.trajectory/v2"]
    provider_id: str = Field(min_length=1)
    source_format: str = Field(min_length=1)
    normalizer: str = Field(min_length=1)
    roots: tuple[str, ...]
    coverage: tuple[Coverage, ...]
    issues: tuple[CoverageIssue, ...] = ()
    extensions: dict[str, JsonValue] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_header(self) -> "HeaderRecord":
        if len(self.roots) != len(set(self.roots)):
            raise ValueError("roots must be unique")
        domains = [item.domain for item in self.coverage]
        if len(domains) != len(set(domains)):
            raise ValueError("coverage domains must be unique")
        issue_ids = [item.issue_id for item in self.issues]
        if len(issue_ids) != len(set(issue_ids)):
            raise ValueError("coverage issue IDs must be unique")
        known = set(issue_ids)
        if any(
            issue not in known for item in self.coverage for issue in item.issue_ids
        ):
            raise ValueError("coverage cites an unknown issue")
        _validate_extensions(self.extensions)
        return self


class ExecutionRecord(TrajectoryV2Model):
    type: Literal["execution"]
    execution_id: str = Field(pattern=r"^exec_[A-Za-z0-9_.-]+$")
    role: Literal["root", "subagent", "unknown"]
    source_refs: tuple[SourceRef, ...] = Field(min_length=1)
    display_name: str | None = None
    model: str | None = None
    native_id: str | None = None
    extensions: dict[str, JsonValue] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_extensions(self) -> "ExecutionRecord":
        _validate_extensions(self.extensions)
        return self


class TextContent(TrajectoryV2Model):
    type: Literal["text"]
    text: str


class BlobContent(TrajectoryV2Model):
    type: Literal["blob"]
    ref: str = Field(min_length=1)
    media_type: str | None = None


class OpaqueContent(TrajectoryV2Model):
    type: Literal["opaque"]
    reason: str = Field(min_length=1)


Content: TypeAlias = Annotated[
    TextContent | BlobContent | OpaqueContent, Field(discriminator="type")
]


class MessagePayload(TrajectoryV2Model):
    role: Literal["system", "developer", "user", "assistant", "tool", "unknown"]
    content: tuple[Content, ...]


class ReasoningPayload(TrajectoryV2Model):
    visibility: Literal["full", "summary", "opaque"]
    content: tuple[Content, ...] = Field(min_length=1)


class ToolCallPayload(TrajectoryV2Model):
    call_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    arguments_state: Literal["available", "unknown"]
    arguments: JsonValue | None = None

    @model_validator(mode="after")
    def validate_arguments(self) -> "ToolCallPayload":
        if self.arguments_state == "unknown" and self.arguments is not None:
            raise ValueError("unknown arguments cannot carry a value")
        return self


class ToolResultPayload(TrajectoryV2Model):
    call_id: str | None = None
    linkage: Literal["linked", "unresolved"]
    outcome: Literal["success", "error", "unknown"]
    content: tuple[Content, ...]

    @model_validator(mode="after")
    def validate_linkage(self) -> "ToolResultPayload":
        if self.linkage == "linked" and self.call_id is None:
            raise ValueError("linked tool results require call_id")
        return self


class LifecyclePayload(TrajectoryV2Model):
    subject: Literal["agent", "turn", "model_attempt"]
    transition: Literal["start", "complete", "error", "cancel"]
    outcome: str | None = None
    error: str | None = None


class ContextChangePayload(TrajectoryV2Model):
    operation: Literal["append", "replace", "compact", "reset"]
    subject: Literal["model", "configuration", "prompt", "history", "unknown"]
    content: tuple[Content, ...] = ()
    affected_event_ids: tuple[str, ...] = ()


class RelationEndpoint(TrajectoryV2Model):
    type: Literal["execution", "event"]
    id: str = Field(min_length=1)


class RelationPayload(TrajectoryV2Model):
    relation: Literal["delegation", "history_inheritance"]
    source: RelationEndpoint
    target: RelationEndpoint
    trigger_event_id: str | None = None


class UsageOwner(TrajectoryV2Model):
    type: Literal["execution", "event", "operation", "unknown"]
    id: str | None = None

    @model_validator(mode="after")
    def validate_owner(self) -> "UsageOwner":
        if self.type == "unknown" and self.id is not None:
            raise ValueError("unknown owner cannot carry an ID")
        if self.type != "unknown" and self.id is None:
            raise ValueError("known owner requires an ID")
        return self


class UsageMeasurement(TrajectoryV2Model):
    metric: str = Field(min_length=1)
    value: int | float = Field(ge=0)
    unit: Literal["tokens", "milliseconds", "seconds", "calls", "currency"]
    inclusion: Literal["standalone", "included_in", "additional_to", "unknown"]
    related_metric: str | None = None
    currency: str | None = Field(default=None, pattern=r"^[A-Z]{3}$")

    @model_validator(mode="after")
    def validate_semantics(self) -> "UsageMeasurement":
        common = {
            "input",
            "output",
            "cache_read",
            "cache_write",
            "reasoning",
            "total",
            "duration",
            "cost",
        }
        if self.metric not in common and "/" not in self.metric:
            raise ValueError("provider-specific metrics must be namespaced")
        if (
            self.inclusion in {"included_in", "additional_to"}
            and self.related_metric is None
        ):
            raise ValueError("measurement inclusion requires related_metric")
        if (
            self.inclusion in {"standalone", "unknown"}
            and self.related_metric is not None
        ):
            raise ValueError(
                "standalone or unknown inclusion cannot name related_metric"
            )
        if (self.unit == "currency") != (self.currency is not None):
            raise ValueError(
                "currency unit and currency code must be supplied together"
            )
        return self


class UsagePayload(TrajectoryV2Model):
    owner: UsageOwner
    model: str | None = None
    scope: Literal["self", "subtree", "unknown"]
    temporality: Literal["delta", "cumulative", "gauge", "unknown"]
    measurements: tuple[UsageMeasurement, ...] = Field(min_length=1)
    sample_id: str | None = None
    counter_id: str | None = None
    zero_baseline: bool = False
    reset: bool = False
    source: Literal["provider_reported", "client_estimated"]

    @model_validator(mode="after")
    def validate_counter(self) -> "UsagePayload":
        if self.temporality == "cumulative" and self.counter_id is None:
            raise ValueError("cumulative usage requires counter_id")
        if self.temporality != "cumulative" and (self.zero_baseline or self.reset):
            raise ValueError("baseline and reset apply only to cumulative usage")
        return self


class ProviderEventPayload(TrajectoryV2Model):
    namespace: str
    event_type: str = Field(min_length=1)
    value: JsonValue

    @model_validator(mode="after")
    def validate_namespace(self) -> "ProviderEventPayload":
        if not _NAMESPACED.fullmatch(self.namespace):
            raise ValueError("provider event namespace must be versioned")
        return self


class EventBase(TrajectoryV2Model):
    type: Literal["event"]
    event_id: str = Field(pattern=r"^evt_[A-Za-z0-9_.-]+$")
    seq: int = Field(ge=0)
    execution_id: str | None
    source_refs: tuple[SourceRef, ...] = Field(min_length=1)
    timestamp: str | None = None
    turn_id: str | None = None
    predecessor_ids: tuple[str, ...] = ()
    mapping: Literal["explicit", "derived", "tentative"]
    extensions: dict[str, JsonValue] = Field(default_factory=dict)


class MessageEvent(EventBase):
    kind: Literal["message"]
    payload: MessagePayload


class ReasoningEvent(EventBase):
    kind: Literal["reasoning"]
    payload: ReasoningPayload


class ToolCallEvent(EventBase):
    kind: Literal["tool_call"]
    payload: ToolCallPayload


class ToolResultEvent(EventBase):
    kind: Literal["tool_result"]
    payload: ToolResultPayload


class LifecycleEvent(EventBase):
    kind: Literal["lifecycle"]
    payload: LifecyclePayload


class ContextChangeEvent(EventBase):
    kind: Literal["context_change"]
    payload: ContextChangePayload


class RelationEvent(EventBase):
    kind: Literal["relation"]
    payload: RelationPayload


class UsageEvent(EventBase):
    kind: Literal["usage"]
    payload: UsagePayload


class ProviderEvent(EventBase):
    kind: Literal["provider_event"]
    payload: ProviderEventPayload


SemanticEvent: TypeAlias = Annotated[
    MessageEvent
    | ReasoningEvent
    | ToolCallEvent
    | ToolResultEvent
    | LifecycleEvent
    | ContextChangeEvent
    | RelationEvent
    | UsageEvent
    | ProviderEvent,
    Field(discriminator="kind"),
]
TrajectoryRecordV2: TypeAlias = Annotated[
    HeaderRecord | ExecutionRecord | SemanticEvent, Field(discriminator="type")
]
_RECORD = TypeAdapter(TrajectoryRecordV2)


def _validate_extensions(value: Mapping[str, JsonValue]) -> None:
    if any(not _NAMESPACED.fullmatch(key) for key in value):
        raise ValueError("extension keys must be versioned namespaces")


@dataclass(frozen=True, slots=True)
class ValidatedTrajectoryV2:
    header: HeaderRecord
    executions: tuple[ExecutionRecord, ...]
    events: tuple[SemanticEvent, ...]
    trajectory_bytes: bytes


def validate_trajectory_v2(data: bytes) -> ValidatedTrajectoryV2:
    """Validate one complete v2 JSONL trajectory and its cross-record references."""

    if not isinstance(data, bytes) or not data.strip():
        raise TrajectoryError(
            "invalid-trajectory", "Trajectory v2 must be non-empty bytes."
        )
    records: list[TrajectoryRecordV2] = []
    try:
        for line in data.splitlines():
            if not line:
                raise ValueError("blank line")
            records.append(_RECORD.validate_json(line))
    except (ValidationError, ValueError) as error:
        details = (
            {"errors": error.errors(include_url=False)}
            if isinstance(error, ValidationError)
            else None
        )
        raise TrajectoryError(
            "invalid-trajectory", "Trajectory v2 record is invalid.", details
        ) from error
    if not isinstance(records[0], HeaderRecord) or any(
        isinstance(item, HeaderRecord) for item in records[1:]
    ):
        raise TrajectoryError(
            "invalid-trajectory", "Trajectory v2 requires one leading header."
        )
    executions = tuple(item for item in records if isinstance(item, ExecutionRecord))
    events = tuple(item for item in records if isinstance(item, EventBase))
    execution_ids = [item.execution_id for item in executions]
    event_ids = [item.event_id for item in events]
    if len(execution_ids) != len(set(execution_ids)) or len(event_ids) != len(
        set(event_ids)
    ):
        raise TrajectoryError("invalid-trajectory", "Trajectory v2 IDs must be unique.")
    header = records[0]
    assert isinstance(header, HeaderRecord)
    known_executions = set(execution_ids)
    if any(root not in known_executions for root in header.roots):
        raise TrajectoryError("invalid-trajectory", "Trajectory root does not resolve.")
    if any(
        item.execution_id is not None and item.execution_id not in known_executions
        for item in events
    ):
        raise TrajectoryError("invalid-trajectory", "Event execution does not resolve.")
    if [item.seq for item in events] != list(range(len(events))):
        raise TrajectoryError(
            "invalid-trajectory", "Event seq values must be contiguous."
        )
    return ValidatedTrajectoryV2(header, executions, events, data)


def encode_trajectory_v2(records: tuple[TrajectoryRecordV2, ...]) -> bytes:
    data = b"".join(canonical_json_bytes(item, newline=True) for item in records)
    validate_trajectory_v2(data)
    return data


def trajectory_v2_schema() -> dict[str, Any]:
    schema = _RECORD.json_schema(mode="serialization")
    return {"$schema": "https://json-schema.org/draft/2020-12/schema", **schema}


__all__ = [
    "Coverage",
    "CoverageIssue",
    "ExecutionRecord",
    "HeaderRecord",
    "SemanticEvent",
    "SourceRef",
    "TRAJECTORY_SCHEMA_V2",
    "TrajectoryRecordV2",
    "UsageEvent",
    "UsageMeasurement",
    "UsageOwner",
    "UsagePayload",
    "ValidatedTrajectoryV2",
    "encode_trajectory_v2",
    "trajectory_v2_schema",
    "validate_trajectory_v2",
]
