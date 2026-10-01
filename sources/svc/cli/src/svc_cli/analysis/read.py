"""Forward-only, exactly reassemblable reading of native evidence frames."""

from __future__ import annotations

import base64
import hashlib
from typing import Annotated, Any, Literal, Mapping, TypeAlias

from pydantic import (
    Discriminator,
    Field,
    Tag,
    TypeAdapter,
    ValidationError,
    model_validator,
)

from ..telemetry.evidence import NativeIndexEntry, ValidatedEvidence
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


READ_FORMAT = "svc.analysis.read/v2"
DEFAULT_MAX_ITEMS = 20
DEFAULT_MAX_BYTES = 65_536
MAX_ITEMS = 100
MAX_BYTES = 1_048_576
MIN_BYTES = 256
MAX_PRECEDING = 20


class InitialReadRequest(AnalysisModel):
    start: EvidenceRef | None = None
    preceding: int = Field(default=0, ge=0, le=MAX_PRECEDING)
    max_items: int = Field(default=DEFAULT_MAX_ITEMS, ge=1, le=MAX_ITEMS)
    max_bytes: int = Field(default=DEFAULT_MAX_BYTES, ge=MIN_BYTES, le=MAX_BYTES)

    @model_validator(mode="after")
    def require_start_for_preceding(self) -> "InitialReadRequest":
        if self.start is None and self.preceding:
            raise ValueError("preceding requires start")
        return self


class ContinueReadRequest(AnalysisModel):
    cursor: str = Field(min_length=1, max_length=8192)
    max_items: int = Field(default=DEFAULT_MAX_ITEMS, ge=1, le=MAX_ITEMS)
    max_bytes: int = Field(default=DEFAULT_MAX_BYTES, ge=MIN_BYTES, le=MAX_BYTES)


def _request_kind(value: Any) -> str:
    if isinstance(value, Mapping):
        return "continuation" if "cursor" in value else "initial"
    if isinstance(value, ContinueReadRequest):
        return "continuation"
    if isinstance(value, InitialReadRequest):
        return "initial"
    return "invalid"


ReadRequest: TypeAlias = Annotated[
    Annotated[InitialReadRequest, Tag("initial")]
    | Annotated[ContinueReadRequest, Tag("continuation")],
    Discriminator(_request_kind),
]
_READ_REQUEST_ADAPTER: TypeAdapter[ReadRequest] = TypeAdapter(ReadRequest)


class ReadScope(AnalysisModel):
    anchor: EvidenceRef | None
    preceding: int = Field(ge=0, le=MAX_PRECEDING)
    ordering: Literal["native-forward"]

    @model_validator(mode="after")
    def require_anchor_for_preceding(self) -> "ReadScope":
        if self.anchor is None and self.preceding:
            raise ValueError("preceding requires anchor")
        return self


class ReadCursor(AnalysisModel):
    version: Literal[2]
    tool: Literal["read"]
    evidence_id: str
    scope: ReadScope
    next_ordinal: int = Field(ge=0)
    next_offset: int = Field(ge=0)


def parse_read_request(
    value: object,
    evidence: ValidatedEvidence,
) -> ReadRequest:
    try:
        request = _READ_REQUEST_ADAPTER.validate_python(value)
    except ValidationError as error:
        adapt_validation_error(
            error,
            code="invalid-read-request",
            message="Read request does not match a supported strict request shape.",
        )
    if isinstance(request, InitialReadRequest) and request.start is not None:
        request.start.require_scope(evidence.evidence_id, expected_kind="native")
    return request


def _decode_read_cursor(value: str, evidence: ValidatedEvidence) -> ReadCursor:
    payload = decode_cursor(value)
    if (
        payload.get("version") != ANALYSIS_CONTRACT_VERSION
        or payload.get("tool") != "read"
    ):
        raise AnalysisProtocolError(
            "cursor-scope-mismatch",
            "Cursor belongs to a different analysis contract or tool.",
        )
    try:
        cursor = ReadCursor.model_validate(payload)
    except ValidationError as error:
        adapt_validation_error(
            error,
            code="invalid-cursor",
            message="Read cursor payload has an invalid shape.",
        )
    if cursor.evidence_id != evidence.evidence_id:
        raise AnalysisProtocolError(
            "cursor-scope-mismatch",
            "Read cursor belongs to different evidence.",
        )
    if cursor.scope.anchor is not None:
        cursor.scope.anchor.require_scope(evidence.evidence_id, expected_kind="native")
    return cursor


def _initial_position(
    evidence: ValidatedEvidence,
    request: ReadRequest,
) -> tuple[int, int, ReadScope]:
    if isinstance(request, ContinueReadRequest):
        cursor = _decode_read_cursor(request.cursor, evidence)
        return cursor.next_ordinal, cursor.next_offset, cursor.scope

    scope = ReadScope(
        anchor=request.start,
        preceding=request.preceding,
        ordering="native-forward",
    )
    if request.start is None:
        ordinal = 0
    else:
        by_id = {
            entry.native_record_id: entry.native_index
            for entry in evidence.native_index
        }
        if request.start.record_id not in by_id:
            raise AnalysisProtocolError(
                "reference-not-found",
                "Native start reference does not resolve in this evidence.",
            )
        ordinal = max(
            0,
            by_id[request.start.record_id] - request.preceding,
        )
    return ordinal, 0, scope


def _fragment_item(
    evidence: ValidatedEvidence,
    entry: NativeIndexEntry,
    start: int,
    end: int,
) -> dict[str, object]:
    frame_size = entry.byte_end - entry.byte_start
    frame = evidence.native[entry.byte_start : entry.byte_end]
    fragment = frame[start:end]
    payload: dict[str, object] = {
        "fragment_start": start,
        "fragment_end": end,
        "fragment_sha256": hashlib.sha256(fragment).hexdigest(),
        "fragment_starts_record": start == 0,
        "fragment_ends_record": end == frame_size,
        "whole_record": start == 0 and end == frame_size,
    }
    try:
        payload.update(
            {
                "encoding": "utf-8",
                "text": fragment.decode("utf-8"),
            }
        )
    except UnicodeDecodeError:
        payload.update(
            {
                "encoding": "base64",
                "data": base64.b64encode(fragment).decode("ascii"),
            }
        )
    return {
        "ref": evidence_ref(
            evidence.evidence_id,
            "native",
            entry.native_record_id,
        ),
        "native_index": entry.native_index,
        "byte_start": entry.byte_start,
        "byte_end": entry.byte_end,
        "frame_status": entry.frame_status,
        "source_coordinate": entry.source_coordinate.model_dump(mode="json"),
        "frame_sha256": hashlib.sha256(frame).hexdigest(),
        "payload": payload,
    }


def read_evidence(
    evidence: ValidatedEvidence,
    request_value: object,
) -> dict[str, object]:
    """Read one bounded page in canonical native order."""

    request = parse_read_request(request_value, evidence)
    ordinal, offset, scope = _initial_position(evidence, request)
    if ordinal > len(evidence.native_index):
        raise AnalysisProtocolError(
            "invalid-cursor",
            "Read cursor ordinal is outside the evidence index.",
        )
    if ordinal < len(evidence.native_index):
        size = (
            evidence.native_index[ordinal].byte_end
            - evidence.native_index[ordinal].byte_start
        )
        if offset >= size:
            raise AnalysisProtocolError(
                "invalid-cursor",
                "Read cursor fragment offset is outside its native frame.",
            )
    elif offset:
        raise AnalysisProtocolError(
            "invalid-cursor",
            "Read cursor cannot carry an offset at end of evidence.",
        )

    items: list[dict[str, object]] = []
    remaining_bytes = request.max_bytes
    page_bytes = 0
    current_ordinal = ordinal
    current_offset = offset
    while (
        current_ordinal < len(evidence.native_index)
        and len(items) < request.max_items
        and remaining_bytes > 0
    ):
        entry = evidence.native_index[current_ordinal]
        frame_size = entry.byte_end - entry.byte_start
        end = min(frame_size, current_offset + remaining_bytes)
        items.append(
            _fragment_item(
                evidence,
                entry,
                current_offset,
                end,
            )
        )
        consumed = end - current_offset
        page_bytes += consumed
        remaining_bytes -= consumed
        if end == frame_size:
            current_ordinal += 1
            current_offset = 0
        else:
            current_offset = end

    more = current_ordinal < len(evidence.native_index)
    next_cursor = None
    if more:
        next_cursor = encode_cursor(
            ReadCursor(
                version=2,
                tool="read",
                evidence_id=evidence.evidence_id,
                scope=scope,
                next_ordinal=current_ordinal,
                next_offset=current_offset,
            )
        )
    capture = evidence.manifest.capture
    if not evidence.native_index:
        status = "unavailable"
    else:
        status = "partial" if capture.status == "partial" else "complete"
    return {
        "format": READ_FORMAT,
        "schema_version": ANALYSIS_CONTRACT_VERSION,
        "status": status,
        "evidence_id": evidence.evidence_id,
        "ordering": "native-forward",
        "items": items,
        "next_cursor": next_cursor,
        "coverage": {
            "capture_status": capture.status,
            "unknown_remainder": capture.unknown_remainder,
            "page_start_ordinal": ordinal,
            "page_start_offset": offset,
            "returned_items": len(items),
            "returned_bytes": page_bytes,
        },
    }


def read_schema() -> dict[str, object]:
    """Return compact discovery data; execution remains stricter than JSON Schema."""

    native_ref_shape = {
        "required": ["evidence_id", "record_kind", "record_id"],
        "record_kind": "native",
        "record_id_pattern": "n[0-9]{6,}",
        "additional_properties": False,
    }
    return {
        "format": "svc.analysis.read.schema/v2",
        "schema_version": ANALYSIS_CONTRACT_VERSION,
        "guidance": {"command": ["svc", "analysis", "--help"]},
        "purpose": "Read contiguous provider-native evidence in forward order; never use an isolated match as a conclusion.",
        "request": {
            "initial": {
                "optional": ["start", "preceding", "max_items", "max_bytes"],
                "start": native_ref_shape,
                "note": "Omit start to begin at the first native record; preceding requires start.",
                "additional_properties": False,
            },
            "continuation": {
                "required": ["cursor"],
                "optional": ["max_items", "max_bytes"],
                "note": "Reuse next_cursor; the anchor, preceding count, and ordering are already bound and must be omitted.",
                "additional_properties": False,
            },
            "bounds": {
                "preceding": [0, MAX_PRECEDING],
                "max_items": [1, MAX_ITEMS],
                "max_bytes": [MIN_BYTES, MAX_BYTES],
            },
        },
        "response": {
            "ordering": "native-forward",
            "payload_encoding": {
                "utf-8": "preferred exact text when the fragment decodes losslessly",
                "base64": "exact fallback for arbitrary bytes",
            },
            "fragment_offsets": "relative to the native frame; concatenate fragments by cursor order",
            "fragment_flags": {
                "fragment_starts_record": "this fragment begins at byte zero",
                "fragment_ends_record": "this fragment reaches the frame end",
                "whole_record": "this one fragment contains the entire frame",
            },
            "integrity": ["frame_sha256", "fragment_sha256"],
            "pagination": "next_cursor means more output, not partial evidence",
        },
        "status": {
            "complete": "The captured native range is complete.",
            "partial": "Captured bytes are readable but the source has a declared gap or incomplete final frame.",
            "unavailable": "No native records were captured.",
        },
        "response_format": READ_FORMAT,
    }


__all__ = [
    "READ_FORMAT",
    "ContinueReadRequest",
    "InitialReadRequest",
    "ReadCursor",
    "ReadRequest",
    "ReadScope",
    "parse_read_request",
    "read_evidence",
    "read_schema",
]
