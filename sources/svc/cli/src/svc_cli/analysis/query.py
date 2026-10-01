"""Typed structural navigation over validated Agent-thread evidence."""

from __future__ import annotations

import json
from typing import Annotated, Any, Iterable, Literal, Mapping, TypeAlias

from pydantic import (
    Discriminator,
    Field,
    Tag,
    TypeAdapter,
    ValidationError,
    field_validator,
    model_validator,
)

from ..telemetry.evidence import NativeIndexEntry, ValidatedEvidence
from ..telemetry.trajectory import (
    RECORD_TYPES,
    canonical_json_bytes,
    projection_summary,
)
from .protocol import (
    ANALYSIS_CONTRACT_VERSION,
    AnalysisModel,
    AnalysisProtocolError,
    EvidenceRef,
    adapt_validation_error,
    decode_cursor,
    encode_cursor,
    evidence_ref,
)


QUERY_FORMAT = "svc.analysis.query/v2"
DEFAULT_MAX_ITEMS = 50
MAX_ITEMS = 100
MAX_TERMS = 8
MAX_TERM_CODE_POINTS = 256
RESPONSE_PAGE_CAP = 65_536
_STRUCTURAL_KEYS = {
    "record_types",
    "roles",
    "tool_names",
    "relationship",
}
_RELATIONSHIP_FIELDS = {
    "turn_ref",
    "actor_ref",
    "parent_actor_ref",
    "lane_ref",
    "concurrency_group",
}

RecordType: TypeAlias = Literal[
    "message",
    "reasoning",
    "tool_call",
    "tool_result",
    "context",
    "event",
]
Role: TypeAlias = Literal["user", "assistant"]
RelationshipField: TypeAlias = Literal[
    "turn_ref",
    "actor_ref",
    "parent_actor_ref",
    "lane_ref",
    "concurrency_group",
]


def _unique(values: list[str]) -> list[str]:
    if len(values) != len(set(values)):
        raise ValueError("values must be unique")
    return values


class RelationshipPredicate(AnalysisModel):
    field: RelationshipField
    value: str = Field(min_length=1)


class NativeRangePredicate(AnalysisModel):
    start: EvidenceRef | None = None
    end: EvidenceRef | None = None

    @model_validator(mode="after")
    def require_endpoint(self) -> "NativeRangePredicate":
        if self.start is None and self.end is None:
            raise ValueError("native_range requires an endpoint")
        return self


class TextPredicate(AnalysisModel):
    terms: list[str] = Field(min_length=1, max_length=MAX_TERMS)
    mode: Literal["any", "all"]
    case_sensitive: bool = False

    @field_validator("terms")
    @classmethod
    def validate_terms(cls, values: list[str]) -> list[str]:
        if any(not value or len(value) > MAX_TERM_CODE_POINTS for value in values):
            raise ValueError("text terms are outside their bounds")
        return _unique(values)


class MatchPredicates(AnalysisModel):
    record_types: list[RecordType] | None = Field(
        default=None, min_length=1, max_length=MAX_TERMS
    )
    roles: list[Role] | None = Field(default=None, min_length=1, max_length=MAX_TERMS)
    tool_names: list[str] | None = Field(
        default=None, min_length=1, max_length=MAX_TERMS
    )
    relationship: RelationshipPredicate | None = None
    native_range: NativeRangePredicate | None = None
    text: TextPredicate | None = None

    @field_validator("record_types", "roles", "tool_names")
    @classmethod
    def validate_lists(cls, values: list[str] | None) -> list[str] | None:
        if values is None:
            return None
        if any(not value or len(value) > MAX_TERM_CODE_POINTS for value in values):
            raise ValueError("predicate values are outside their bounds")
        return _unique(values)

    @model_validator(mode="after")
    def require_predicate(self) -> "MatchPredicates":
        if not any(
            value is not None
            for value in (
                self.record_types,
                self.roles,
                self.tool_names,
                self.relationship,
                self.native_range,
                self.text,
            )
        ):
            raise ValueError("match predicates cannot be empty")
        return self


class OverviewRequest(AnalysisModel):
    intent: Literal["overview"]


class InitialMatchRequest(AnalysisModel):
    intent: Literal["match"]
    predicates: MatchPredicates
    max_items: int = Field(default=DEFAULT_MAX_ITEMS, ge=1, le=MAX_ITEMS)


class ContinueMatchRequest(AnalysisModel):
    intent: Literal["match"]
    cursor: str = Field(min_length=1, max_length=8192)
    max_items: int = Field(default=DEFAULT_MAX_ITEMS, ge=1, le=MAX_ITEMS)


def _request_kind(value: Any) -> str:
    if isinstance(value, Mapping):
        if value.get("intent") == "overview":
            return "overview"
        if value.get("intent") == "match" and "cursor" in value:
            return "match-continuation"
        if value.get("intent") == "match":
            return "match-initial"
    if isinstance(value, OverviewRequest):
        return "overview"
    if isinstance(value, ContinueMatchRequest):
        return "match-continuation"
    if isinstance(value, InitialMatchRequest):
        return "match-initial"
    return "invalid"


QueryRequest: TypeAlias = Annotated[
    Annotated[OverviewRequest, Tag("overview")]
    | Annotated[InitialMatchRequest, Tag("match-initial")]
    | Annotated[ContinueMatchRequest, Tag("match-continuation")],
    Discriminator(_request_kind),
]
MatchRequest: TypeAlias = InitialMatchRequest | ContinueMatchRequest
_QUERY_REQUEST_ADAPTER: TypeAdapter[QueryRequest] = TypeAdapter(QueryRequest)


class MatchCursor(AnalysisModel):
    version: Literal[2]
    tool: Literal["query-match"]
    evidence_id: str
    scope: MatchPredicates
    next_ordinal: int = Field(ge=0)


def _validate_predicate_refs(
    predicates: MatchPredicates,
    evidence: ValidatedEvidence,
) -> None:
    if predicates.native_range is None:
        return
    for reference in (predicates.native_range.start, predicates.native_range.end):
        if reference is not None:
            reference.require_scope(evidence.evidence_id, expected_kind="native")


def parse_query_request(value: Any, evidence: ValidatedEvidence) -> QueryRequest:
    try:
        request = _QUERY_REQUEST_ADAPTER.validate_python(value)
    except ValidationError as error:
        adapt_validation_error(
            error,
            code="invalid-query-request",
            message="Query request does not match a supported strict request shape.",
        )
    if isinstance(request, InitialMatchRequest):
        _validate_predicate_refs(request.predicates, evidence)
    return request


def parse_match_request(value: Any, evidence: ValidatedEvidence) -> MatchRequest:
    request = parse_query_request(value, evidence)
    if isinstance(request, OverviewRequest):
        raise AnalysisProtocolError(
            "invalid-query-request",
            "match request must declare intent=match.",
        )
    return request


def _decode_match_cursor(value: str, evidence: ValidatedEvidence) -> MatchCursor:
    payload = decode_cursor(value)
    if (
        payload.get("version") != ANALYSIS_CONTRACT_VERSION
        or payload.get("tool") != "query-match"
    ):
        raise AnalysisProtocolError(
            "cursor-scope-mismatch",
            "Cursor belongs to a different analysis contract or tool.",
        )
    try:
        cursor = MatchCursor.model_validate(payload)
    except ValidationError as error:
        adapt_validation_error(
            error,
            code="invalid-cursor",
            message="Match cursor payload has an invalid shape.",
        )
    if cursor.evidence_id != evidence.evidence_id:
        raise AnalysisProtocolError(
            "cursor-scope-mismatch",
            "Match cursor belongs to different evidence.",
        )
    _validate_predicate_refs(cursor.scope, evidence)
    return cursor


def _records_by_native(
    evidence: ValidatedEvidence,
) -> dict[str, list[Mapping[str, Any]]]:
    assert evidence.trajectory is not None
    result: dict[str, list[Mapping[str, Any]]] = {}
    for item in evidence.trajectory.records:
        record = item.model_dump(mode="python", exclude_none=True)
        if record.get("type") == "meta":
            continue
        source_ref = record.get("source_ref")
        if isinstance(source_ref, Mapping):
            native_id = source_ref.get("native_record_id")
            if isinstance(native_id, str):
                result.setdefault(native_id, []).append(record)
    return result


def _native_bounds(
    evidence: ValidatedEvidence,
    predicates: MatchPredicates,
) -> tuple[int, int]:
    if predicates.native_range is None:
        return 0, len(evidence.native_index) - 1
    by_id = {item.native_record_id: item.native_index for item in evidence.native_index}
    start = 0
    end = len(evidence.native_index) - 1
    if predicates.native_range.start is not None:
        record_id = predicates.native_range.start.record_id
        if record_id not in by_id:
            raise AnalysisProtocolError(
                "reference-not-found",
                "native_range start does not resolve.",
            )
        start = by_id[record_id]
    if predicates.native_range.end is not None:
        record_id = predicates.native_range.end.record_id
        if record_id not in by_id:
            raise AnalysisProtocolError(
                "reference-not-found",
                "native_range end does not resolve.",
            )
        end = by_id[record_id]
    if start > end:
        raise AnalysisProtocolError(
            "invalid-query-request",
            "native_range start follows its end.",
        )
    return start, end


def _structural_matches(
    records: Iterable[Mapping[str, Any]],
    predicates: MatchPredicates,
) -> list[Mapping[str, Any]]:
    matches: list[Mapping[str, Any]] = []
    for record in records:
        if (
            predicates.record_types is not None
            and record.get("type") not in predicates.record_types
        ):
            continue
        if predicates.roles is not None and record.get("role") not in predicates.roles:
            continue
        if (
            predicates.tool_names is not None
            and record.get("name") not in predicates.tool_names
        ):
            continue
        relationship = predicates.relationship
        if relationship is not None:
            relationships = record.get("relationships")
            if (
                not isinstance(relationships, Mapping)
                or relationships.get(relationship.field) != relationship.value
            ):
                continue
        matches.append(record)
    return matches


def _native_strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, Mapping):
        for child in value.values():
            yield from _native_strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from _native_strings(child)


def _text_match(
    raw: bytes,
    predicate: TextPredicate,
) -> tuple[bool, list[str], bool]:
    try:
        value = json.loads(raw.decode("utf-8").rstrip("\r\n"))
        strings = list(_native_strings(value))
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError, RecursionError):
        return False, [], False
    haystacks = (
        strings if predicate.case_sensitive else [item.casefold() for item in strings]
    )
    matched = [
        term
        for term in predicate.terms
        if any(
            (term if predicate.case_sensitive else term.casefold()) in haystack
            for haystack in haystacks
        )
    ]
    passes = (
        bool(matched)
        if predicate.mode == "any"
        else len(matched) == len(predicate.terms)
    )
    return passes, matched, True


def _descriptor(
    evidence: ValidatedEvidence,
    entry: NativeIndexEntry,
    records: list[Mapping[str, Any]],
    matched_terms: list[str],
) -> tuple[dict[str, Any], bool]:
    retained = records[:8]
    record_types = sorted({str(item["type"]) for item in records})
    roles = sorted({str(item["role"]) for item in records if "role" in item})
    tool_names = sorted({str(item["name"]) for item in records if "name" in item})
    return (
        {
            "ref": evidence_ref(evidence.evidence_id, "native", entry.native_record_id),
            "native_index": entry.native_index,
            "frame_status": entry.frame_status,
            "source_coordinate": entry.source_coordinate.model_dump(mode="json"),
            "record_types": record_types,
            "roles": roles,
            "tool_names": tool_names,
            "trajectory_refs": [
                evidence_ref(evidence.evidence_id, "trajectory", str(item["record_id"]))
                for item in retained
            ],
            "matched_terms": matched_terms,
        },
        len(records) > len(retained),
    )


def _capture(evidence: ValidatedEvidence) -> tuple[str, bool, dict[str, Any]]:
    capture = evidence.manifest.capture
    return capture.status, capture.unknown_remainder, capture.model_dump(mode="json")


def _overview(evidence: ValidatedEvidence) -> dict[str, Any]:
    capture_status, _, capture = _capture(evidence)
    native_first = (
        evidence_ref(
            evidence.evidence_id, "native", evidence.native_index[0].native_record_id
        )
        if evidence.native_index
        else None
    )
    native_last = (
        evidence_ref(
            evidence.evidence_id, "native", evidence.native_index[-1].native_record_id
        )
        if evidence.native_index
        else None
    )
    if evidence.trajectory is None:
        return {
            "format": QUERY_FORMAT,
            "schema_version": ANALYSIS_CONTRACT_VERSION,
            "intent": "overview",
            "status": "unavailable",
            "evidence_id": evidence.evidence_id,
            "source": evidence.manifest.source.model_dump(mode="json"),
            "capture": capture,
            "projection": {
                "result_status": "projection-unavailable",
                "capabilities": {},
                "lossiness": {},
            },
            "ordering": "native-forward",
            "native_range": {
                "records": len(evidence.native_index),
                "first_ref": native_first,
                "last_ref": native_last,
            },
            "structural_ranges": [],
            "available_match_fields": [],
            "next_cursor": None,
        }

    projection = projection_summary(evidence.trajectory)
    by_type: dict[str, list[dict[str, Any]]] = {}
    for item in evidence.trajectory.records:
        record = item.model_dump(mode="python", exclude_none=True)
        by_type.setdefault(str(record["type"]), []).append(record)
    ranges = []
    for record_type in RECORD_TYPES:
        records = by_type.get(record_type, [])
        if not records:
            continue
        ranges.append(
            {
                "record_type": record_type,
                "count": len(records),
                "first_ref": evidence_ref(
                    evidence.evidence_id,
                    "trajectory",
                    str(records[0]["record_id"]),
                ),
                "last_ref": evidence_ref(
                    evidence.evidence_id,
                    "trajectory",
                    str(records[-1]["record_id"]),
                ),
            }
        )
    if not evidence.native_index:
        status = "unavailable"
    elif capture_status == "partial" or projection["result_status"] == "partial":
        status = "partial"
    else:
        status = "complete"
    return {
        "format": QUERY_FORMAT,
        "schema_version": ANALYSIS_CONTRACT_VERSION,
        "intent": "overview",
        "status": status,
        "evidence_id": evidence.evidence_id,
        "source": evidence.manifest.source.model_dump(mode="json"),
        "capture": capture,
        "projection": {
            "result_status": projection["result_status"],
            "capabilities": projection["capabilities"],
            "lossiness": projection["lossiness"],
        },
        "ordering": "native-forward",
        "native_range": {
            "records": len(evidence.native_index),
            "first_ref": native_first,
            "last_ref": native_last,
        },
        "structural_ranges": ranges,
        "available_match_fields": [
            "record_types",
            "roles",
            "tool_names",
            "native_range",
            "relationship",
            "text",
        ],
        "next_cursor": None,
    }


def overview(evidence: ValidatedEvidence) -> dict[str, Any]:
    return _overview(evidence)


def _match_position(
    evidence: ValidatedEvidence,
    request: MatchRequest,
) -> tuple[MatchPredicates, int]:
    if isinstance(request, ContinueMatchRequest):
        cursor = _decode_match_cursor(request.cursor, evidence)
        return cursor.scope, cursor.next_ordinal
    return request.predicates, _native_bounds(evidence, request.predicates)[0]


def _projection_unavailable_match(
    evidence: ValidatedEvidence,
    predicates: MatchPredicates,
) -> dict[str, Any]:
    capture_status, _, _ = _capture(evidence)
    return {
        "format": QUERY_FORMAT,
        "schema_version": ANALYSIS_CONTRACT_VERSION,
        "intent": "match",
        "status": "unavailable",
        "evidence_id": evidence.evidence_id,
        "ordering": "native-forward",
        "items": [],
        "next_cursor": None,
        "coverage": {
            "capture_status": capture_status,
            "projection_status": "projection-unavailable",
            "text_native_values": (
                "unavailable" if predicates.text is not None else "not-requested"
            ),
            "descriptor_truncated": False,
            "returned_items": 0,
            "descriptor_bytes": 0,
        },
    }


def _match(evidence: ValidatedEvidence, request: MatchRequest) -> dict[str, Any]:
    predicates, next_ordinal = _match_position(evidence, request)
    start, end = _native_bounds(evidence, predicates)
    if not start <= next_ordinal <= end + 1:
        raise AnalysisProtocolError(
            "invalid-cursor",
            "Match cursor position is outside its range.",
        )
    if evidence.trajectory is None:
        return _projection_unavailable_match(evidence, predicates)

    by_native = _records_by_native(evidence)
    structural = any(getattr(predicates, key) is not None for key in _STRUCTURAL_KEYS)
    text_predicate = predicates.text
    items: list[dict[str, Any]] = []
    output_bytes = 0
    coverage_partial = False
    descriptor_truncated = False
    ordinal = next_ordinal
    while ordinal <= end:
        entry = evidence.native_index[ordinal]
        records = by_native.get(entry.native_record_id, [])
        structural_records = (
            _structural_matches(records, predicates) if structural else records
        )
        passes = bool(structural_records) if structural else True
        matched_terms: list[str] = []
        if text_predicate is not None:
            raw = evidence.native[entry.byte_start : entry.byte_end]
            text_passes, matched_terms, covered = _text_match(raw, text_predicate)
            coverage_partial |= not covered or entry.frame_status != "complete"
            passes = passes and text_passes and entry.frame_status == "complete"
        if passes:
            descriptor, truncated = _descriptor(
                evidence,
                entry,
                structural_records,
                matched_terms,
            )
            encoded_size = len(canonical_json_bytes(descriptor))
            if items and (
                len(items) >= request.max_items
                or output_bytes + encoded_size > RESPONSE_PAGE_CAP
            ):
                break
            if encoded_size > RESPONSE_PAGE_CAP:
                raise AnalysisProtocolError(
                    "query-response-item-too-large",
                    "One bounded match descriptor exceeds the response page cap.",
                )
            items.append(descriptor)
            output_bytes += encoded_size
            descriptor_truncated |= truncated
            if len(items) >= request.max_items:
                ordinal += 1
                break
        ordinal += 1

    more = ordinal <= end
    next_cursor = None
    if more:
        cursor = MatchCursor(
            version=2,
            tool="query-match",
            evidence_id=evidence.evidence_id,
            scope=predicates,
            next_ordinal=ordinal,
        )
        next_cursor = encode_cursor(cursor.model_dump(mode="json", exclude_none=True))
    projection = projection_summary(evidence.trajectory)
    capture_status, _, _ = _capture(evidence)
    projection_partial = structural and projection["result_status"] == "partial"
    capture_partial = capture_status == "partial"
    coverage_partial |= projection_partial or capture_partial or descriptor_truncated
    unavailable = False
    capabilities = projection["capabilities"]
    if isinstance(capabilities, Mapping):
        requested_types = predicates.record_types
        if requested_types == ["reasoning"] and capabilities.get("reasoning") in {
            "absent",
            "opaque",
        }:
            unavailable = True
    status = (
        "unavailable" if unavailable else "partial" if coverage_partial else "complete"
    )
    return {
        "format": QUERY_FORMAT,
        "schema_version": ANALYSIS_CONTRACT_VERSION,
        "intent": "match",
        "status": status,
        "evidence_id": evidence.evidence_id,
        "ordering": "native-forward",
        "items": items,
        "next_cursor": next_cursor,
        "coverage": {
            "capture_status": capture_status,
            "projection_status": projection["result_status"],
            "text_native_values": (
                "partial"
                if text_predicate is not None and coverage_partial
                else "complete"
                if text_predicate is not None
                else "not-requested"
            ),
            "descriptor_truncated": descriptor_truncated,
            "returned_items": len(items),
            "descriptor_bytes": output_bytes,
        },
    }


def match(
    evidence: ValidatedEvidence,
    request_value: Any,
) -> dict[str, Any]:
    return _match(evidence, parse_match_request(request_value, evidence))


def query_evidence(
    evidence: ValidatedEvidence,
    request_value: Any,
) -> dict[str, Any]:
    request = parse_query_request(request_value, evidence)
    if isinstance(request, OverviewRequest):
        return _overview(evidence)
    return _match(evidence, request)


def query_schema() -> dict[str, Any]:
    native_ref_shape = {
        "required": ["evidence_id", "record_kind", "record_id"],
        "record_kind": "native",
        "record_id_pattern": "n[0-9]{6,}",
        "additional_properties": False,
    }
    return {
        "format": "svc.analysis.query.schema/v2",
        "schema_version": ANALYSIS_CONTRACT_VERSION,
        "guidance": {"command": ["svc", "analysis", "--help"]},
        "composition": [
            "overview",
            "match to obtain native refs",
            "read contiguous native context before concluding",
        ],
        "intents": {
            "overview": {
                "request": {"intent": "overview"},
                "additional_properties": False,
            },
            "match": {
                "initial": {
                    "required": ["intent", "predicates"],
                    "optional": ["max_items"],
                    "additional_properties": False,
                },
                "continuation": {
                    "required": ["intent", "cursor"],
                    "optional": ["max_items"],
                    "note": "Reuse next_cursor; predicates are already bound and must be omitted.",
                    "additional_properties": False,
                },
                "predicates": {
                    "combination": "intersection across supplied predicates",
                    "record_types": {
                        "type": "non-empty unique string array",
                        "values": list(RECORD_TYPES[1:]),
                    },
                    "roles": {
                        "type": "non-empty unique string array",
                        "values": ["user", "assistant"],
                    },
                    "tool_names": {
                        "type": "non-empty unique string array",
                        "matching": "exact",
                    },
                    "relationship": {
                        "shape": {
                            "field": "<relationship field>",
                            "value": "<exact ref>",
                        },
                        "fields": sorted(_RELATIONSHIP_FIELDS),
                    },
                    "native_range": {
                        "shape": {"start": "<native ref>", "end": "<native ref>"},
                        "minimum_fields": 1,
                        "semantics": "inclusive native-order endpoints",
                        "reference": native_ref_shape,
                    },
                    "text": {
                        "shape": {
                            "terms": ["<literal>"],
                            "mode": "any | all",
                            "case_sensitive": False,
                        },
                        "bounds": {
                            "terms": [1, MAX_TERMS],
                            "term_code_points": [1, MAX_TERM_CODE_POINTS],
                        },
                        "matching": "literal substrings in provider-native JSON string values",
                    },
                },
                "bounds": {
                    "max_items": [1, MAX_ITEMS],
                },
            },
        },
        "status": {
            "complete": "The exact requested evidence range is answerable; an empty result is a trustworthy negative.",
            "partial": "Useful results exist but capture or projection loss limits the conclusion.",
            "unavailable": "The evidence lacks the requested capability; this is not a negative finding.",
        },
        "response_format": QUERY_FORMAT,
    }


__all__ = [
    "QUERY_FORMAT",
    "ContinueMatchRequest",
    "InitialMatchRequest",
    "MatchCursor",
    "MatchPredicates",
    "MatchRequest",
    "OverviewRequest",
    "match",
    "overview",
    "parse_match_request",
    "parse_query_request",
    "query_evidence",
    "query_schema",
]
