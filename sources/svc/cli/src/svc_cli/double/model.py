"""Runtime-neutral value models for BSL compilation and double runs."""

from __future__ import annotations

import math
from typing import Annotated, Any, Literal, Self, TypeAlias

from pydantic import Field, JsonValue, model_validator

from ..model import ValueModel


PathPart: TypeAlias = str | int


class SourceLocation(ValueModel):
    line: int
    column: int
    path: tuple[PathPart, ...]


class Snapshot(ValueModel):
    logical_path: str
    sha256: str
    bytes: int
    content_base64: str


class Provenance(ValueModel):
    kind: Literal[
        "consumer-requirement",
        "provider-contract",
        "provider-documentation",
        "provider-capture",
        "synthetic",
    ]
    source: str
    sanitized: bool | None = None
    snapshot_sha256: str | None = None


class _MatcherBase(ValueModel):
    kind: Literal["exact", "enum", "range", "regex", "semantic"]
    value: JsonValue | None = None
    values: tuple[JsonValue, ...] | None = None
    minimum: int | float | None = None
    maximum: int | float | None = None
    pattern: str | None = None
    semantic: str | None = None
    using: str | None = None


class ExactMatcher(_MatcherBase):
    kind: Literal["exact"] = "exact"
    value: JsonValue
    values: None = None
    minimum: None = None
    maximum: None = None
    pattern: None = None
    semantic: None = None
    using: None = None


class EnumMatcher(_MatcherBase):
    kind: Literal["enum"] = "enum"
    value: None = None
    values: tuple[JsonValue, ...]
    minimum: None = None
    maximum: None = None
    pattern: None = None
    semantic: None = None
    using: None = None


class RangeMatcher(_MatcherBase):
    kind: Literal["range"] = "range"
    value: None = None
    values: None = None
    pattern: None = None
    semantic: None = None
    using: None = None

    @model_validator(mode="after")
    def require_ordered_bound(self) -> Self:
        if self.minimum is None and self.maximum is None:
            raise ValueError("range requires minimum or maximum")
        if "minimum" in self.model_fields_set and self.minimum is None:
            raise ValueError("range minimum cannot be null")
        if "maximum" in self.model_fields_set and self.maximum is None:
            raise ValueError("range maximum cannot be null")
        if (
            self.minimum is not None
            and self.maximum is not None
            and self.minimum > self.maximum
        ):
            raise ValueError("range minimum cannot exceed maximum")
        return self


class RegexMatcher(_MatcherBase):
    kind: Literal["regex"] = "regex"
    value: None = None
    values: None = None
    minimum: None = None
    maximum: None = None
    pattern: str
    semantic: None = None
    using: None = None


class SemanticMatcher(_MatcherBase):
    kind: Literal["semantic"] = "semantic"
    value: None = None
    values: None = None
    minimum: None = None
    maximum: None = None
    pattern: None = None
    semantic: str
    using: str


Matcher: TypeAlias = Annotated[
    ExactMatcher | EnumMatcher | RangeMatcher | RegexMatcher | SemanticMatcher,
    Field(discriminator="kind"),
]


class _ValueNodeBase(ValueModel):
    path: tuple[PathPart, ...]
    kind: Literal[
        "literal", "match", "capture", "example", "derived", "generated", "managed"
    ]
    value: JsonValue | None = None
    matcher: Matcher | None = None
    name: str | None = None
    expression: str | None = None
    semantic: str | None = None
    using: str | None = None
    options: dict[str, JsonValue] | None = None
    bind: str | None = None
    validator: Matcher | None = None
    managed_snapshot: Snapshot | None = None
    media_type: str | None = None
    location: SourceLocation | None = None


class LiteralValueNode(_ValueNodeBase):
    kind: Literal["literal"] = "literal"
    value: JsonValue
    matcher: None = None
    name: None = None
    expression: None = None
    semantic: None = None
    using: None = None
    options: None = None
    validator: None = None
    managed_snapshot: None = None
    media_type: None = None


class MatchValueNode(_ValueNodeBase):
    kind: Literal["match"] = "match"
    matcher: Matcher
    name: None = None
    expression: None = None
    semantic: None = None
    using: None = None
    options: None = None
    bind: None = None
    validator: None = None
    managed_snapshot: None = None
    media_type: None = None


class CaptureValueNode(_ValueNodeBase):
    kind: Literal["capture"] = "capture"
    matcher: Matcher
    name: str
    expression: None = None
    semantic: None = None
    using: None = None
    options: None = None
    bind: None = None
    validator: None = None
    managed_snapshot: None = None
    media_type: None = None


class ExampleValueNode(_ValueNodeBase):
    kind: Literal["example"] = "example"
    value: JsonValue
    matcher: None = None
    name: None = None
    expression: None = None
    semantic: None = None
    using: None = None
    options: None = None
    managed_snapshot: None = None
    media_type: None = None


class DerivedValueNode(_ValueNodeBase):
    kind: Literal["derived"] = "derived"
    value: None = None
    matcher: None = None
    name: None = None
    expression: str
    semantic: None = None
    using: None = None
    options: None = None
    validator: Matcher
    managed_snapshot: None = None
    media_type: None = None


class GeneratedValueNode(_ValueNodeBase):
    kind: Literal["generated"] = "generated"
    value: None = None
    matcher: None = None
    name: None = None
    expression: None = None
    semantic: str
    using: str
    options: dict[str, JsonValue]
    validator: Matcher
    managed_snapshot: None = None
    media_type: None = None


class ManagedValueNode(_ValueNodeBase):
    kind: Literal["managed"] = "managed"
    matcher: None = None
    name: None = None
    expression: None = None
    semantic: None = None
    using: None = None
    options: None = None
    managed_snapshot: Snapshot
    media_type: str


ValueNode: TypeAlias = Annotated[
    LiteralValueNode
    | MatchValueNode
    | CaptureValueNode
    | ExampleValueNode
    | DerivedValueNode
    | GeneratedValueNode
    | ManagedValueNode,
    Field(discriminator="kind"),
]


class _BodyBase(ValueModel):
    kind: Literal["structured", "form-urlencoded", "raw"]
    template: JsonValue | None = None
    nodes: tuple[ValueNode, ...] = ()
    raw: Snapshot | None = None
    media_type: str | None = None


class StructuredBody(_BodyBase):
    kind: Literal["structured"] = "structured"
    template: JsonValue
    raw: None = None
    media_type: None = None


class FormUrlencodedBody(_BodyBase):
    kind: Literal["form-urlencoded"] = "form-urlencoded"
    template: dict[str, JsonValue]
    raw: None = None
    media_type: None = None


class RawBody(_BodyBase):
    kind: Literal["raw"] = "raw"
    template: None = None
    nodes: tuple[()] = ()
    raw: Snapshot
    media_type: str


Body: TypeAlias = Annotated[
    StructuredBody | FormUrlencodedBody | RawBody,
    Field(discriminator="kind"),
]


class Materializer(ValueModel):
    argv: tuple[str, ...]
    cwd: str
    env: dict[str, str]
    timeout_ms: int
    max_output_bytes: int


class Request(ValueModel):
    method: str
    path: str
    query: dict[str, JsonValue]
    query_nodes: tuple[ValueNode, ...] = ()
    headers: dict[str, JsonValue]
    header_nodes: tuple[ValueNode, ...] = ()
    body: Body | None = None
    materializer: Materializer | None = None


class Response(ValueModel):
    status: int
    headers: dict[str, JsonValue]
    header_nodes: tuple[ValueNode, ...] = ()
    body: Body | None = None
    materializer: Materializer | None = None


class Interaction(ValueModel):
    name: str
    provenance: Provenance
    request: Request
    response: Response


class Event(ValueModel):
    name: str
    target: str
    provenance: Provenance
    request: Request


class SchemaResource(ValueModel):
    uri: str
    document: JsonValue
    snapshot_sha256: str


class Contract(ValueModel):
    source: Snapshot
    method: str
    path: str
    request_schema: JsonValue | None = None
    response_schemas: dict[str, JsonValue]
    schema_resources: tuple[SchemaResource, ...]


class Scenario(ValueModel):
    language: Literal["svc.double/v0"] = "svc.double/v0"
    module_path: str
    workspace_root: str
    name: str
    claim: str
    boundary_name: str
    event_target_policy: Literal["loopback-only", "explicit-remote"]
    interactions: tuple[Interaction, ...]
    events: tuple[Event, ...]
    contract: Contract | None
    snapshots: tuple[Snapshot, ...]
    fidelity: tuple[str, ...]
    nonclaims: tuple[str, ...]
    scenario_digest: str
    uses_materializer: bool


class Replay(ValueModel):
    seed: int
    clock: str
    generators: tuple[str, ...]
    validators: tuple[str, ...]
    runtime: str


class TargetBinding(ValueModel):
    name: str
    origin: str
    remote: bool


class JournalEntry(ValueModel):
    sequence: int
    at: str
    kind: Literal["request", "event", "runtime"]
    status: str
    facts: dict[str, JsonValue]


class Journal(ValueModel):
    total: int
    retained: int
    omitted: int
    entries: tuple[JournalEntry, ...]


class RunObservation(ValueModel):
    run_id: str
    scenario_name: str
    status: Literal["bootstrapping", "ready", "stopping", "stopped", "failed"]
    sealed: bool
    responder_url: str | None
    scenario_digest: str
    run_context_digest: str
    replay: Replay
    targets: tuple[TargetBinding, ...]
    bindings: dict[str, JsonValue]
    journal: Journal
    nonclaims: tuple[str, ...]
    failure: str | None = None


class RunRecord(ValueModel):
    schema_version: Literal[1] = 1
    run_id: str
    workspace_root: str
    workspace_instance: str
    run_directory: str
    manifest_path: str
    scenario_digest: str
    run_context_digest: str
    replay: Replay
    targets: tuple[TargetBinding, ...]
    control_url: str
    control_capability: str
    observation_path: str
    created_at: str


class Diagnostic(ValueModel):
    code: str
    message: str
    path: str | None = None
    line: int | None = None
    column: int | None = None


class ValidateResult(ValueModel):
    command: Literal["double validate"] = "double validate"
    module: str
    scenario_name: str | None = None
    claim: str | None = None
    valid: bool
    scenario_digest: str | None = None
    fidelity: tuple[str, ...]
    nonclaims: tuple[str, ...]
    snapshots: tuple[Snapshot, ...]
    diagnostic: Diagnostic | None = None


class StartResult(ValueModel):
    command: Literal["double start"] = "double start"
    run_id: str
    module: str
    scenario_name: str
    responder_url: str
    scenario_digest: str
    run_context_digest: str
    replay: Replay
    targets: tuple[TargetBinding, ...]
    nonclaims: tuple[str, ...]


class EmitResult(ValueModel):
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
    http_status: int | None = None
    reason: str | None = None


class ObserveResult(ValueModel):
    command: Literal["double observe"] = "double observe"
    observation: RunObservation
    authority: Literal["active-carrier", "sealed-snapshot", "unsealed-projection"]
    control_status: Literal["available", "not-required", "control-unavailable"]


class StopResult(ValueModel):
    command: Literal["double stop"] = "double stop"
    run_id: str
    status: Literal["stopped", "control-unavailable"]
    sealed: bool
    idempotent: bool
    observation: RunObservation | None = None


def strict_json_value(value: Any) -> JsonValue:
    """Narrow an already validated Python JSON value for model construction."""

    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise TypeError("JSON numbers must be finite")
        return value
    if isinstance(value, list):
        return [strict_json_value(item) for item in value]
    if isinstance(value, dict):
        if not all(isinstance(key, str) for key in value):
            raise TypeError("JSON object keys must be strings")
        return {key: strict_json_value(item) for key, item in value.items()}
    raise TypeError(f"value is not JSON-compatible: {type(value).__name__}")
