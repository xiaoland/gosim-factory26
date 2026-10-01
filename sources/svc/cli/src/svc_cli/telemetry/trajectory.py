"""Typed derived trajectory records and deterministic JSONL writing.

The trajectory is a rebuildable projection over captured native evidence.  It
therefore owns only the structural record shape and a deterministic writer;
identity, manifests, retention policy, and source limits belong elsewhere.
"""

from __future__ import annotations

from dataclasses import dataclass
import io
import json
from types import MappingProxyType
from typing import Annotated, Any, BinaryIO, Iterable, Literal, Mapping, TypeAlias

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    TypeAdapter,
    ValidationError,
    model_validator,
)


TRAJECTORY_SCHEMA = "svc.trajectory/v1"
RECORD_TYPES = (
    "meta",
    "message",
    "reasoning",
    "tool_call",
    "tool_result",
    "context",
    "event",
)

_RECORD_ID_PATTERN = r"^r[0-9]{6,}$"
_NATIVE_RECORD_ID_PATTERN = r"^n[0-9]{6,}$"
_CALL_REFERENCE_PATTERN = r"^call_[0-9a-f]{64}(?:_d[0-9]{6,})?$"
_TIMESTAMP_PATTERN = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,9})?Z$"
_TASK_REFERENCE_PATTERN = r"^tasks/(?:[A-Za-z0-9_-][^/]*/)+packet\.md$"

RecordId = Annotated[str, Field(pattern=_RECORD_ID_PATTERN)]
NativeRecordId = Annotated[str, Field(pattern=_NATIVE_RECORD_ID_PATTERN)]
CallReference = Annotated[str, Field(pattern=_CALL_REFERENCE_PATTERN)]
ThreadReference = Annotated[str, Field(pattern=r"^thread_[0-9a-f]{64}$")]
TurnReference = Annotated[str, Field(pattern=r"^turn_[0-9a-f]{64}$")]
ActorReference = Annotated[str, Field(pattern=r"^actor_[0-9a-f]{64}$")]
LaneReference = Annotated[str, Field(pattern=r"^lane_[0-9a-f]{64}$")]
ConcurrencyReference = Annotated[
    str,
    Field(pattern=r"^concurrency_[0-9a-f]{64}$"),
]
WorkspaceReference = Annotated[
    str,
    Field(pattern=r"^workspace_[0-9a-f]{64}$"),
]
Timestamp = Annotated[str, Field(pattern=_TIMESTAMP_PATTERN)]
TaskReference = Annotated[str, Field(pattern=_TASK_REFERENCE_PATTERN)]
NonNegativeInt = Annotated[int, Field(ge=0)]


class TrajectoryError(ValueError):
    """Stable trajectory failure with a machine-readable code."""

    def __init__(
        self,
        code: str,
        message: str,
        details: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = MappingProxyType(dict(details or {}))

    def as_dict(self) -> dict[str, Any]:
        value: dict[str, Any] = {"code": self.code, "message": self.message}
        if self.details:
            value["details"] = dict(self.details)
        return value


class _StrictFrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)


class SourceRef(_StrictFrozenModel):
    """Coordinate of a derived claim in the provider/native frame stream."""

    event_index: NonNegativeInt
    line: NonNegativeInt | None = None
    byte_offset: NonNegativeInt | None = None
    component_index: NonNegativeInt | None = None
    component: str | None = None
    native_record_id: NativeRecordId | None = None


class MetaSourceRef(_StrictFrozenModel):
    event_index: None
    component: Literal["meta"]


class Relationships(_StrictFrozenModel):
    """Structural chain edges retained for query and future derivations."""

    turn_ref: TurnReference | None = None
    actor_ref: ActorReference | None = None
    parent_actor_ref: ActorReference | None = None
    lane_ref: LaneReference | None = None
    concurrency_group: ConcurrencyReference | None = None


class Workspace(_StrictFrozenModel):
    status: Literal["present", "missing"]
    flavor: Literal["posix", "windows", "unc"] | None
    label: str | None
    ref: WorkspaceReference | None


class ProjectionCapabilities(_StrictFrozenModel):
    reasoning: Literal["full", "summary", "opaque", "absent"]
    tool_linkage: Literal["explicit", "mixed", "synthesized", "absent"]
    context: Literal["full", "partial", "absent"]
    task_references: Literal["available", "unavailable"]
    explicit_concurrency: Literal["available", "unavailable"]
    timestamps: Literal["full", "partial", "absent"]
    terminal_events: Literal["available", "unavailable"]


class ProjectionLossiness(_StrictFrozenModel):
    """Only structural loss that changes interpretation of the projection."""

    dropped_records: NonNegativeInt = 0
    unavailable_records: NonNegativeInt = 0
    synthesized_records: NonNegativeInt = 0
    partial_frames: NonNegativeInt = 0


class ContextAttributes(_StrictFrozenModel):
    model: str | None = None
    reasoning_effort: str | None = None
    approval_mode: str | None = None
    sandbox_mode: str | None = None
    collaboration_mode: str | None = None
    tool_names: tuple[str, ...] | None = None


class TrajectoryRecordBase(_StrictFrozenModel):
    """Fields available on every typed trajectory record."""

    type: str
    record_id: RecordId
    record_index: NonNegativeInt
    timestamp: Timestamp | None
    source_ref: SourceRef | MetaSourceRef
    relationships: Relationships

    @model_validator(mode="after")
    def _record_id_matches_index(self) -> "TrajectoryRecordBase":
        if self.record_id != f"r{self.record_index:06d}":
            raise ValueError("record_id does not match record_index")
        return self


class MetaRecord(TrajectoryRecordBase):
    type: Literal["meta"]
    timestamp: None
    source_ref: MetaSourceRef
    trajectory_schema: Literal["svc.trajectory/v1"]
    provider_id: str
    adapter_id: str
    source_format: str
    thread_ref: ThreadReference
    workspace: Workspace
    result_status: Literal["ready", "partial"] | None = None
    capabilities: ProjectionCapabilities | None = None
    lossiness: ProjectionLossiness | None = None


class MessageRecord(TrajectoryRecordBase):
    type: Literal["message"]
    source_ref: SourceRef
    role: Literal["user", "assistant"]
    task_refs: tuple[TaskReference, ...]


class ReasoningRecord(TrajectoryRecordBase):
    type: Literal["reasoning"]
    source_ref: SourceRef
    reasoning_kind: Literal["full", "summary", "opaque"]


class ToolCallRecord(TrajectoryRecordBase):
    type: Literal["tool_call"]
    source_ref: SourceRef
    tool_call_id: CallReference
    name: str
    arguments_kind: Literal["json", "text", "absent"]


class ToolResultRecord(TrajectoryRecordBase):
    type: Literal["tool_result"]
    source_ref: SourceRef
    tool_call_id: CallReference
    status: Literal["success", "error", "unknown"]
    link_status: Literal["linked", "unresolved"]


class ContextRecord(TrajectoryRecordBase):
    type: Literal["context"]
    source_ref: SourceRef
    context_kind: Literal["system", "developer", "tool_config", "turn"]
    attributes: ContextAttributes


class EventRecord(TrajectoryRecordBase):
    type: Literal["event"]
    source_ref: SourceRef
    event_kind: Literal[
        "turn_start",
        "turn_complete",
        "turn_abort",
        "agent_start",
        "agent_complete",
        "compaction",
        "approval",
        "error",
    ]
    outcome: (
        Literal[
            "requested",
            "granted",
            "denied",
            "cancelled",
            "completed",
            "error",
            "aborted",
            "unknown",
        ]
        | None
    )


TrajectoryRecord: TypeAlias = Annotated[
    MetaRecord
    | MessageRecord
    | ReasoningRecord
    | ToolCallRecord
    | ToolResultRecord
    | ContextRecord
    | EventRecord,
    Field(discriminator="type"),
]
_RECORD_ADAPTER: TypeAdapter[TrajectoryRecord] = TypeAdapter(TrajectoryRecord)


def canonical_json_bytes(value: Any, *, newline: bool = False) -> bytes:
    """Encode one JSON-ready value deterministically for durable writing."""

    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json", exclude_unset=True)
    try:
        encoded = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8", errors="strict")
    except (TypeError, ValueError, UnicodeEncodeError) as error:
        raise TrajectoryError(
            "invalid-json",
            "Value cannot be encoded as deterministic JSON.",
        ) from error
    return encoded + (b"\n" if newline else b"")


def _record_from_mapping(record: Mapping[str, Any]) -> TrajectoryRecord:
    try:
        return _RECORD_ADAPTER.validate_json(canonical_json_bytes(record))
    except ValidationError as error:
        raise TrajectoryError(
            "invalid-trajectory",
            "Trajectory record does not match its typed schema.",
            {"errors": error.errors(include_url=False)},
        ) from error


def _coerce_record(record: Mapping[str, Any] | TrajectoryRecord) -> TrajectoryRecord:
    if isinstance(record, TrajectoryRecordBase):
        return record
    if not isinstance(record, Mapping):
        raise TrajectoryError(
            "invalid-trajectory",
            "Trajectory records must be objects.",
        )
    return _record_from_mapping(record)


def _check_position(record: TrajectoryRecord, expected_index: int) -> None:
    if record.record_index != expected_index:
        raise TrajectoryError(
            "invalid-trajectory",
            "Trajectory record indexes must be contiguous.",
            {"expected_index": expected_index, "record_index": record.record_index},
        )
    if expected_index == 0 and not isinstance(record, MetaRecord):
        raise TrajectoryError(
            "invalid-trajectory",
            "Trajectory must begin with a meta record.",
        )
    if expected_index > 0 and isinstance(record, MetaRecord):
        raise TrajectoryError(
            "invalid-trajectory",
            "Trajectory may contain only one leading meta record.",
        )


class TrajectoryCollector:
    """Write typed records incrementally with only sequence invariants."""

    def __init__(self, output: BinaryIO | None = None) -> None:
        self._owned = output is None
        self._output = output or io.BytesIO()
        self._next_index = 0
        self._finished = False

    def emit(self, record: Mapping[str, Any] | TrajectoryRecord) -> bool:
        if self._finished:
            raise TrajectoryError(
                "collector-finished",
                "Trajectory collector is already finished.",
            )
        typed = _coerce_record(record)
        _check_position(typed, self._next_index)
        line = canonical_json_bytes(typed, newline=True)
        try:
            self._output.write(line)
        except (OSError, ValueError) as error:
            raise TrajectoryError(
                "trajectory-write-failed",
                "Trajectory sink could not be written.",
            ) from error
        self._next_index += 1
        return True

    def finish(self) -> bytes | None:
        if self._finished:
            raise TrajectoryError(
                "collector-finished",
                "Trajectory collector is already finished.",
            )
        self._finished = True
        if self._next_index == 0:
            raise TrajectoryError(
                "invalid-trajectory",
                "Trajectory must contain a leading meta record.",
            )
        if self._owned and isinstance(self._output, io.BytesIO):
            return self._output.getvalue()
        return None


@dataclass(frozen=True, slots=True)
class ValidatedTrajectory:
    records: tuple[TrajectoryRecord, ...]
    trajectory_bytes: bytes


def _parse_trajectory_bytes(
    data: bytes,
    *,
    require_summary: bool,
) -> ValidatedTrajectory:
    if not isinstance(data, bytes):
        raise TrajectoryError(
            "invalid-trajectory",
            "Trajectory input must be bytes.",
        )
    if not data.strip():
        raise TrajectoryError(
            "invalid-trajectory",
            "Trajectory must contain a leading meta record.",
        )

    records: list[TrajectoryRecord] = []
    for raw_line in data.splitlines():
        if not raw_line.strip():
            raise TrajectoryError(
                "invalid-trajectory",
                "Trajectory contains an empty line.",
            )
        try:
            record = _RECORD_ADAPTER.validate_json(raw_line)
        except ValidationError as error:
            raise TrajectoryError(
                "invalid-trajectory",
                "Trajectory record does not match its typed schema.",
                {"errors": error.errors(include_url=False)},
            ) from error
        _check_position(record, len(records))
        records.append(record)

    meta = records[0]
    assert isinstance(meta, MetaRecord)
    if require_summary and (
        meta.result_status is None
        or meta.capabilities is None
        or meta.lossiness is None
    ):
        raise TrajectoryError(
            "invalid-trajectory",
            "Final trajectory meta is missing its projection summary.",
        )
    return ValidatedTrajectory(tuple(records), data)


def validate_trajectory_bytes(data: bytes) -> ValidatedTrajectory:
    """Validate equivalent JSONL through the typed record boundary.

    Input key order and insignificant JSON whitespace are deliberately not an
    authority.  Deterministic bytes are produced only by the writer.
    """

    return _parse_trajectory_bytes(data, require_summary=True)


def attach_projection_summary(
    trajectory_bytes: bytes,
    *,
    result_status: Literal["ready", "partial"],
    capabilities: Mapping[str, Any] | ProjectionCapabilities,
    lossiness: Mapping[str, Any] | ProjectionLossiness,
) -> bytes:
    """Attach the derived summary to the leading meta and rewrite JSONL."""

    parsed = _parse_trajectory_bytes(trajectory_bytes, require_summary=False)
    meta = parsed.records[0]
    assert isinstance(meta, MetaRecord)
    meta_value = meta.model_dump(mode="json", exclude_unset=True)
    meta_value.update(
        {
            "result_status": result_status,
            "capabilities": (
                capabilities.model_dump(mode="json")
                if isinstance(capabilities, ProjectionCapabilities)
                else dict(capabilities)
            ),
            "lossiness": (
                lossiness.model_dump(mode="json")
                if isinstance(lossiness, ProjectionLossiness)
                else dict(lossiness)
            ),
        }
    )
    final_meta = _record_from_mapping(meta_value)
    records = (final_meta, *parsed.records[1:])
    encoded = b"".join(canonical_json_bytes(record, newline=True) for record in records)
    validate_trajectory_bytes(encoded)
    return encoded


def projection_summary(
    trajectory: ValidatedTrajectory | Iterable[TrajectoryRecord],
) -> dict[str, Any]:
    """Return the JSON-ready summary carried by the leading meta record."""

    records = (
        trajectory.records
        if isinstance(trajectory, ValidatedTrajectory)
        else tuple(trajectory)
    )
    if not records or not isinstance(records[0], MetaRecord):
        raise TrajectoryError(
            "invalid-trajectory",
            "Trajectory must contain a leading meta record.",
        )
    meta = records[0]
    if (
        meta.result_status is None
        or meta.capabilities is None
        or meta.lossiness is None
    ):
        raise TrajectoryError(
            "invalid-trajectory",
            "Final trajectory meta is missing its projection summary.",
        )
    return {
        "source": {
            "provider_id": meta.provider_id,
            "adapter_id": meta.adapter_id,
            "source_format": meta.source_format,
            "thread_ref": meta.thread_ref,
            "workspace": meta.workspace.model_dump(mode="json"),
        },
        "result_status": meta.result_status,
        "capabilities": meta.capabilities.model_dump(mode="json"),
        "lossiness": meta.lossiness.model_dump(mode="json"),
    }


__all__ = [
    "ContextAttributes",
    "ContextRecord",
    "EventRecord",
    "MessageRecord",
    "MetaRecord",
    "ProjectionCapabilities",
    "ProjectionLossiness",
    "RECORD_TYPES",
    "ReasoningRecord",
    "Relationships",
    "SourceRef",
    "TRAJECTORY_SCHEMA",
    "ToolCallRecord",
    "ToolResultRecord",
    "TrajectoryCollector",
    "TrajectoryError",
    "TrajectoryRecord",
    "TrajectoryRecordBase",
    "ValidatedTrajectory",
    "Workspace",
    "attach_projection_summary",
    "canonical_json_bytes",
    "projection_summary",
    "validate_trajectory_bytes",
]
