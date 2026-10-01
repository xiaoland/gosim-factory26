"""Generated-schema models for the analysis v3 public contract."""

from __future__ import annotations

from typing import Annotated, Any, Literal, TypeAlias

from pydantic import Field, TypeAdapter, field_validator, model_validator

from ..telemetry.trajectory_v2 import Coverage, SemanticEvent, UsageMeasurement
from .protocol import AnalysisModel


ANALYSIS_VERSION_V3 = 3
QUERY_FORMAT_V3 = "svc.analysis.query/v3"
READ_FORMAT_V3 = "svc.analysis.read/v3"


class AnalysisRefV3(AnalysisModel):
    evidence_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    kind: Literal["execution", "turn", "event", "content", "blob", "native"]
    id: str = Field(min_length=1)


class AllWorkScope(AnalysisModel):
    history: Literal["all_work"]


class PathScope(AnalysisModel):
    history: Literal["path"]
    leaf: AnalysisRefV3

    @model_validator(mode="after")
    def leaf_is_event(self) -> "PathScope":
        if self.leaf.kind != "event":
            raise ValueError("path leaf must be an event ref")
        return self


HistoryScope: TypeAlias = Annotated[
    AllWorkScope | PathScope, Field(discriminator="history")
]


class OverviewRequestV3(AnalysisModel):
    version: Literal[3]
    intent: Literal["overview"]
    cursor: str | None = Field(default=None, min_length=1, max_length=8192)
    max_items: int = Field(default=50, ge=1, le=100)
    max_bytes: int = Field(default=65_536, ge=256, le=1_048_576)


class TraceRequestV3(AnalysisModel):
    version: Literal[3]
    intent: Literal["trace"]
    execution: AnalysisRefV3 | None = None
    event: AnalysisRefV3 | None = None
    turn_id: str | None = Field(default=None, min_length=1)
    scope: HistoryScope = Field(
        default_factory=lambda: AllWorkScope(history="all_work")
    )
    cursor: str | None = Field(default=None, min_length=1, max_length=8192)
    max_items: int = Field(default=50, ge=1, le=100)
    max_bytes: int = Field(default=65_536, ge=256, le=1_048_576)

    @model_validator(mode="after")
    def one_selector(self) -> "TraceRequestV3":
        selected = sum(
            value is not None for value in (self.execution, self.event, self.turn_id)
        )
        if (self.cursor is None and selected != 1) or (
            self.cursor is not None and selected != 0
        ):
            raise ValueError(
                "initial trace requires one selector; continuation requires only cursor"
            )
        if self.execution is not None and self.execution.kind != "execution":
            raise ValueError("execution selector requires an execution ref")
        if self.event is not None and self.event.kind != "event":
            raise ValueError("event selector requires an event ref")
        return self


class ProfileSelectV3(AnalysisModel):
    execution: AnalysisRefV3 | None = None
    descendants: bool = False

    @model_validator(mode="after")
    def execution_kind(self) -> "ProfileSelectV3":
        if self.execution is not None and self.execution.kind != "execution":
            raise ValueError("profile execution requires an execution ref")
        if self.descendants and self.execution is None:
            raise ValueError("descendants requires an execution selector")
        return self


class ProfileRequestV3(AnalysisModel):
    version: Literal[3]
    intent: Literal["profile"]
    select: ProfileSelectV3 = Field(default_factory=ProfileSelectV3)
    scope: HistoryScope = Field(
        default_factory=lambda: AllWorkScope(history="all_work")
    )
    breakdown: Literal["execution", "model", "tool"] | None = None
    cursor: str | None = Field(default=None, min_length=1, max_length=8192)
    max_items: int = Field(default=50, ge=1, le=100)
    max_bytes: int = Field(default=65_536, ge=256, le=1_048_576)

    @model_validator(mode="after")
    def initial_or_continuation(self) -> "ProfileRequestV3":
        if self.cursor is None and self.breakdown is None:
            raise ValueError("initial profile requires breakdown")
        if self.cursor is not None and self.breakdown is not None:
            raise ValueError("profile continuation requires only cursor")
        if self.cursor is not None and self.select != ProfileSelectV3():
            raise ValueError("profile continuation requires only cursor")
        return self


class MatchPredicatesV3(AnalysisModel):
    kinds: (
        list[
            Literal[
                "message",
                "reasoning",
                "tool_call",
                "tool_result",
                "lifecycle",
                "context_change",
                "relation",
                "usage",
                "provider_event",
            ],
            ...,
        ]
        | None
    ) = Field(default=None, min_length=1)
    execution: AnalysisRefV3 | None = None
    tool_names: list[str] | None = Field(default=None, min_length=1)
    text_terms: list[str] | None = Field(default=None, min_length=1)

    @field_validator("tool_names", "text_terms")
    @classmethod
    def unique_bounded_terms(cls, value: list[str] | None) -> list[str] | None:
        if value is not None and (
            len(value) > 8
            or len(set(value)) != len(value)
            or any(not item or len(item) > 256 for item in value)
        ):
            raise ValueError("match terms must be unique bounded text")
        return value

    @model_validator(mode="after")
    def non_empty(self) -> "MatchPredicatesV3":
        if all(
            value is None
            for value in (self.kinds, self.execution, self.tool_names, self.text_terms)
        ):
            raise ValueError("match predicates cannot be empty")
        if self.execution is not None and self.execution.kind != "execution":
            raise ValueError("match execution requires an execution ref")
        return self


class MatchRequestV3(AnalysisModel):
    version: Literal[3]
    intent: Literal["match"]
    predicates: MatchPredicatesV3 | None = None
    cursor: str | None = Field(default=None, min_length=1, max_length=8192)
    max_items: int = Field(default=50, ge=1, le=100)
    max_bytes: int = Field(default=65_536, ge=256, le=1_048_576)

    @model_validator(mode="after")
    def initial_or_continuation(self) -> "MatchRequestV3":
        if (self.predicates is None) == (self.cursor is None):
            raise ValueError("match requires predicates or cursor, but not both")
        return self


QueryRequestV3: TypeAlias = Annotated[
    OverviewRequestV3 | TraceRequestV3 | ProfileRequestV3 | MatchRequestV3,
    Field(discriminator="intent"),
]
QUERY_REQUEST_V3 = TypeAdapter(QueryRequestV3)


class ExactReadRequestV3(AnalysisModel):
    version: Literal[3]
    ref: AnalysisRefV3
    max_bytes: int = Field(default=65_536, ge=256, le=1_048_576)

    @model_validator(mode="after")
    def readable_ref(self) -> "ExactReadRequestV3":
        if self.ref.kind not in {"content", "blob", "native"}:
            raise ValueError("read requires a content, blob, or native ref")
        return self


class ForwardReadRequestV3(AnalysisModel):
    version: Literal[3]
    start: AnalysisRefV3
    max_items: int = Field(default=20, ge=1, le=100)
    max_bytes: int = Field(default=65_536, ge=256, le=1_048_576)

    @model_validator(mode="after")
    def native_start(self) -> "ForwardReadRequestV3":
        if self.start.kind != "native":
            raise ValueError("forward read requires a native start ref")
        return self


class ContinueReadRequestV3(AnalysisModel):
    version: Literal[3]
    cursor: str = Field(min_length=1, max_length=8192)
    max_items: int = Field(default=20, ge=1, le=100)
    max_bytes: int = Field(default=65_536, ge=256, le=1_048_576)


ReadRequestV3: TypeAlias = (
    ExactReadRequestV3 | ForwardReadRequestV3 | ContinueReadRequestV3
)
READ_REQUEST_V3 = TypeAdapter(ReadRequestV3)


class AggregatedUsageMeasurementV3(UsageMeasurement):
    scope: Literal["self", "subtree", "unknown"]
    source: Literal["provider_reported", "client_estimated"]


class UsageSummaryV3(AnalysisModel):
    known: tuple[AggregatedUsageMeasurementV3, ...] = ()
    ambiguous_observations: int = Field(default=0, ge=0)
    unknown_observations: int = Field(default=0, ge=0)


class ExecutionSummaryV3(AnalysisModel):
    ref: AnalysisRefV3
    role: Literal["root", "subagent", "unknown"]
    lifecycle: Literal["running", "complete", "error", "cancelled", "unknown"]
    model: str | None = None
    self_usage: UsageSummaryV3
    inclusive_usage: UsageSummaryV3


class RelationSummaryV3(AnalysisModel):
    relation: Literal["delegation", "history_inheritance"]
    source: AnalysisRefV3
    target: AnalysisRefV3
    mapping: Literal["explicit", "derived", "tentative"]


class QueryResponseBaseV3(AnalysisModel):
    format: Literal["svc.analysis.query/v3"]
    version: Literal[3]
    evidence_id: str
    intent: str
    status: Literal["complete", "partial", "unavailable"]
    coverage: tuple[Coverage, ...]
    issues: tuple[str, ...] = ()
    next_cursor: str | None = None


class OverviewResponseV3(QueryResponseBaseV3):
    intent: Literal["overview"]
    roots: tuple[AnalysisRefV3, ...]
    executions: tuple[ExecutionSummaryV3, ...]
    relations: tuple[RelationSummaryV3, ...]
    counts: dict[str, int]


class TraceResponseV3(QueryResponseBaseV3):
    intent: Literal["trace"]
    events: tuple[SemanticEvent, ...]
    content_refs: tuple[AnalysisRefV3, ...] = ()
    native_refs: tuple[AnalysisRefV3, ...] = ()


class ProfileBreakdownV3(AnalysisModel):
    key: str
    usage: UsageSummaryV3
    calls: int = Field(default=0, ge=0)
    results: int = Field(default=0, ge=0)
    errors: int = Field(default=0, ge=0)


class ProfileResponseV3(QueryResponseBaseV3):
    intent: Literal["profile"]
    breakdown: Literal["execution", "model", "tool"]
    total: UsageSummaryV3
    rows: tuple[ProfileBreakdownV3, ...]


class MatchResponseV3(QueryResponseBaseV3):
    intent: Literal["match"]
    refs: tuple[AnalysisRefV3, ...]


QueryResponseV3: TypeAlias = Annotated[
    OverviewResponseV3 | TraceResponseV3 | ProfileResponseV3 | MatchResponseV3,
    Field(discriminator="intent"),
]
QUERY_RESPONSE_V3 = TypeAdapter(QueryResponseV3)


class AnalysisErrorV3(AnalysisModel):
    format: Literal["svc.analysis.error/v3"]
    version: Literal[3]
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
    restart: str | None = None


class ReadItemV3(AnalysisModel):
    ref: AnalysisRefV3
    fragment_start: int = Field(ge=0)
    fragment_end: int = Field(ge=0)
    fragment_sha256: str
    material_sha256: str | None = None
    starts_material: bool
    ends_material: bool
    payload: dict[str, Any]


class ReadResponseV3(AnalysisModel):
    format: Literal["svc.analysis.read/v3"]
    version: Literal[3]
    evidence_id: str
    status: Literal["complete", "partial", "unavailable"]
    ordering: Literal["exact", "native-forward"]
    items: tuple[ReadItemV3, ...]
    next_cursor: str | None


def _schema(adapter: TypeAdapter[Any]) -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        **adapter.json_schema(mode="serialization"),
    }


def query_request_schema_v3() -> dict[str, Any]:
    schema = _schema(QUERY_REQUEST_V3)

    def typed_ref(kind: str) -> dict[str, Any]:
        return {
            "allOf": [
                {"$ref": "#/$defs/AnalysisRefV3"},
                {"properties": {"kind": {"const": kind}}, "required": ["kind"]},
            ]
        }

    trace = schema.get("$defs", {}).get("TraceRequestV3")
    if isinstance(trace, dict):
        trace["oneOf"] = [
            {
                "oneOf": [
                    {
                        "required": ["execution"],
                        "properties": {"execution": typed_ref("execution")},
                    },
                    {
                        "required": ["event"],
                        "properties": {"event": typed_ref("event")},
                    },
                    {
                        "required": ["turn_id"],
                        "properties": {"turn_id": {"type": "string", "minLength": 1}},
                    },
                ],
                "properties": {"cursor": {"type": "null"}},
            },
            {
                "required": ["cursor"],
                "properties": {
                    "cursor": {"type": "string", "minLength": 1},
                    "execution": {"type": "null"},
                    "event": {"type": "null"},
                    "turn_id": {"type": "null"},
                },
            },
        ]
    match = schema.get("$defs", {}).get("MatchRequestV3")
    if isinstance(match, dict):
        match["oneOf"] = [
            {
                "required": ["predicates"],
                "properties": {
                    "predicates": {"$ref": "#/$defs/MatchPredicatesV3"},
                    "cursor": {"type": "null"},
                },
            },
            {
                "required": ["cursor"],
                "properties": {
                    "cursor": {"type": "string", "minLength": 1},
                    "predicates": {"type": "null"},
                },
            },
        ]
    profile = schema.get("$defs", {}).get("ProfileRequestV3")
    if isinstance(profile, dict):
        profile["allOf"] = [
            {
                "if": {
                    "required": ["cursor"],
                    "properties": {"cursor": {"type": "string"}},
                },
                "then": {
                    "properties": {
                        "select": {
                            "properties": {
                                "execution": {"type": "null"},
                                "descendants": {"const": False},
                            }
                        }
                    }
                },
            }
        ]
        profile["oneOf"] = [
            {
                "required": ["breakdown"],
                "properties": {
                    "breakdown": {"enum": ["execution", "model", "tool"]},
                    "cursor": {"type": "null"},
                },
            },
            {
                "required": ["cursor"],
                "properties": {
                    "cursor": {"type": "string", "minLength": 1},
                    "breakdown": {"type": "null"},
                },
            },
        ]
    profile_select = schema.get("$defs", {}).get("ProfileSelectV3")
    if isinstance(profile_select, dict):
        profile_select["properties"]["execution"] = {
            "anyOf": [typed_ref("execution"), {"type": "null"}],
            "default": None,
        }
    predicates = schema.get("$defs", {}).get("MatchPredicatesV3")
    if isinstance(predicates, dict):
        predicates["properties"]["execution"] = {
            "anyOf": [typed_ref("execution"), {"type": "null"}],
            "default": None,
        }
    path = schema.get("$defs", {}).get("PathScope")
    if isinstance(path, dict):
        path["properties"]["leaf"] = typed_ref("event")
    return schema


def query_response_schema_v3() -> dict[str, Any]:
    return _schema(QUERY_RESPONSE_V3)


def read_request_schema_v3() -> dict[str, Any]:
    return _schema(READ_REQUEST_V3)


def read_response_schema_v3() -> dict[str, Any]:
    return _schema(TypeAdapter(ReadResponseV3))


def error_schema_v3() -> dict[str, Any]:
    return _schema(TypeAdapter(AnalysisErrorV3))


__all__ = [
    "ANALYSIS_VERSION_V3",
    "AnalysisErrorV3",
    "AnalysisRefV3",
    "ContinueReadRequestV3",
    "ExactReadRequestV3",
    "ForwardReadRequestV3",
    "READ_REQUEST_V3",
    "QUERY_REQUEST_V3",
    "QUERY_RESPONSE_V3",
    "QueryRequestV3",
    "QueryResponseV3",
    "query_request_schema_v3",
    "query_response_schema_v3",
    "read_request_schema_v3",
    "read_response_schema_v3",
    "error_schema_v3",
]
