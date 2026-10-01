"""Analysis v3 overview, trace, profile, and match intents."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from pydantic import ValidationError

from ..telemetry.evidence_v4 import ValidatedEvidenceV4
from ..telemetry.trajectory_v2 import SemanticEvent, UsageEvent
from ..telemetry.trajectory import canonical_json_bytes
from .engine_v3 import (
    UsageAggregate,
    aggregate_usage,
    descendants,
    execution_lifecycle,
    path_event_ids,
    usage_for_execution,
)
from .models_v3 import (
    MatchRequestV3,
    MatchPredicatesV3,
    OverviewRequestV3,
    ProfileRequestV3,
    QUERY_REQUEST_V3,
    TraceRequestV3,
)
from .protocol import AnalysisProtocolError, decode_cursor, encode_cursor


def _ref(evidence_id: str, kind: str, record_id: str) -> dict[str, str]:
    return {"evidence_id": evidence_id, "kind": kind, "id": record_id}


def _usage(value: UsageAggregate) -> dict[str, Any]:
    return {
        "known": [
            {
                "metric": item.metric,
                "value": item.value,
                "unit": item.unit,
                "inclusion": item.inclusion,
                "related_metric": item.related_metric,
                "currency": item.currency,
                "scope": item.scope,
                "source": item.source,
            }
            for item in value.known
        ],
        "ambiguous_observations": value.ambiguous_observations,
        "unknown_observations": value.unknown_observations,
    }


def _status(evidence: ValidatedEvidenceV4) -> str:
    statuses = {item.status for item in evidence.trajectory.header.coverage}
    if statuses == {"unavailable"}:
        return "unavailable"
    return "partial" if statuses != {"complete"} else "complete"


def _base(evidence: ValidatedEvidenceV4, intent: str) -> dict[str, Any]:
    header = evidence.trajectory.header
    return {
        "format": "svc.analysis.query/v3",
        "version": 3,
        "intent": intent,
        "evidence_id": evidence.evidence_id,
        "status": _status(evidence),
        "coverage": [item.model_dump(mode="json") for item in header.coverage],
        "issues": [item.issue_id for item in header.issues],
    }


def _page(
    evidence: ValidatedEvidenceV4,
    intent: str,
    cursor: str | None,
    max_items: int,
    items: tuple[Any, ...],
) -> tuple[tuple[Any, ...], str | None]:
    start = 0
    if cursor is not None:
        payload = decode_cursor(cursor)
        if payload.get("version") != 3 or payload.get("intent") != intent:
            raise AnalysisProtocolError(
                "cursor-version-mismatch", "Cursor requires a fresh original request."
            )
        if payload.get("evidence_id") != evidence.evidence_id:
            raise AnalysisProtocolError(
                "cursor-scope-mismatch", "Cursor belongs to different evidence."
            )
        start = payload.get("next")
        if type(start) is not int or start < 0 or start > len(items):
            raise AnalysisProtocolError("invalid-cursor", "Cursor position is invalid.")
    end = min(len(items), start + max_items)
    next_cursor = None
    if end < len(items):
        next_cursor = encode_cursor(
            {
                "version": 3,
                "intent": intent,
                "evidence_id": evidence.evidence_id,
                "next": end,
            }
        )
    return items[start:end], next_cursor


def _validate_ref(evidence: ValidatedEvidenceV4, reference: Any, kind: str) -> str:
    if reference.evidence_id != evidence.evidence_id:
        raise AnalysisProtocolError(
            "reference-scope-mismatch", "Reference belongs to different evidence."
        )
    if reference.kind != kind:
        raise AnalysisProtocolError(
            "reference-kind-mismatch", f"Reference must identify {kind}."
        )
    return reference.id


def _overview(
    evidence: ValidatedEvidenceV4, request: OverviewRequestV3
) -> dict[str, Any]:
    trajectory = evidence.trajectory
    all_executions = tuple(trajectory.executions)
    page, cursor = _page(
        evidence, "overview", request.cursor, request.max_items, all_executions
    )
    executions = [
        {
            "ref": _ref(evidence.evidence_id, "execution", item.execution_id),
            "role": item.role,
            "lifecycle": execution_lifecycle(trajectory, item.execution_id),
            "model": item.model,
            "self_usage": _usage(usage_for_execution(trajectory, item.execution_id)),
            "inclusive_usage": _usage(
                usage_for_execution(trajectory, item.execution_id, inclusive=True)
            ),
        }
        for item in page
    ]
    page_ids = {item.execution_id for item in page}
    relations = [
        {
            "relation": event.payload.relation,
            "source": _ref(
                evidence.evidence_id, event.payload.source.type, event.payload.source.id
            ),
            "target": _ref(
                evidence.evidence_id, event.payload.target.type, event.payload.target.id
            ),
            "mapping": event.mapping,
        }
        for event in trajectory.events
        if event.kind == "relation"
        and (event.payload.source.id in page_ids or event.payload.target.id in page_ids)
    ]
    counts = Counter(event.kind for event in trajectory.events)
    while executions:
        end = (
            0 if request.cursor is None else int(decode_cursor(request.cursor)["next"])
        ) + len(executions)
        cursor = (
            None
            if end >= len(all_executions)
            else encode_cursor(
                {
                    "version": 3,
                    "intent": "overview",
                    "evidence_id": evidence.evidence_id,
                    "next": end,
                }
            )
        )
        kept_ids = {item["ref"]["id"] for item in executions}
        response = {
            **_base(evidence, "overview"),
            "roots": [
                _ref(evidence.evidence_id, "execution", item)
                for item in trajectory.header.roots
            ],
            "executions": executions,
            "relations": [
                item
                for item in relations
                if item["source"]["id"] in kept_ids or item["target"]["id"] in kept_ids
            ],
            "counts": dict(sorted(counts.items())),
            "next_cursor": cursor,
        }
        if len(canonical_json_bytes(response)) <= request.max_bytes:
            return response
        executions.pop()
    raise AnalysisProtocolError(
        "query-page-budget-too-small", "Overview response envelope exceeds max_bytes."
    )


def _trace_events(
    evidence: ValidatedEvidenceV4, request: TraceRequestV3
) -> tuple[SemanticEvent, ...]:
    trajectory = evidence.trajectory
    if request.cursor is not None:
        payload = decode_cursor(request.cursor)
        selector = payload.get("selector")
        if not isinstance(selector, dict):
            raise AnalysisProtocolError(
                "invalid-cursor", "Trace cursor has an invalid shape."
            )
        try:
            initial = TraceRequestV3.model_validate(
                {"version": 3, "intent": "trace", **selector}
            )
        except ValidationError as error:
            raise AnalysisProtocolError(
                "invalid-cursor", "Trace cursor selector is invalid."
            ) from error
        return _trace_events(evidence, initial)
    event_ids: set[str] | None = None
    if request.scope.history == "path":
        leaf = _validate_ref(evidence, request.scope.leaf, "event")
        event_ids = path_event_ids(trajectory, leaf)
        if not event_ids:
            raise AnalysisProtocolError(
                "reference-not-found", "Path leaf event does not resolve."
            )
    if request.execution is not None:
        execution_id = _validate_ref(evidence, request.execution, "execution")
        if execution_id not in {item.execution_id for item in trajectory.executions}:
            raise AnalysisProtocolError(
                "reference-not-found", "Execution does not resolve."
            )
        events = tuple(
            event for event in trajectory.events if event.execution_id == execution_id
        )
    elif request.event is not None:
        event_id = _validate_ref(evidence, request.event, "event")
        selected = next(
            (event for event in trajectory.events if event.event_id == event_id), None
        )
        if selected is None:
            raise AnalysisProtocolError(
                "reference-not-found", "Event does not resolve."
            )
        associated = {event_id, *selected.predecessor_ids}
        associated.update(
            event.event_id
            for event in trajectory.events
            if event_id in event.predecessor_ids
        )
        call_id = getattr(selected.payload, "call_id", None)
        if call_id is not None:
            associated.update(
                event.event_id
                for event in trajectory.events
                if getattr(event.payload, "call_id", None) == call_id
            )
        events = tuple(
            event for event in trajectory.events if event.event_id in associated
        )
    else:
        events = tuple(
            event for event in trajectory.events if event.turn_id == request.turn_id
        )
    if event_ids is not None:
        events = tuple(event for event in events if event.event_id in event_ids)
    return events


def _trace(evidence: ValidatedEvidenceV4, request: TraceRequestV3) -> dict[str, Any]:
    events = _trace_events(evidence, request)
    page, cursor = _page(evidence, "trace", request.cursor, request.max_items, events)
    cursor_payload = None if request.cursor is None else decode_cursor(request.cursor)
    start = 0 if cursor_payload is None else int(cursor_payload["next"])
    selector = (
        {
            key: value
            for key, value in request.model_dump(mode="json", exclude_none=True).items()
            if key not in {"version", "intent", "cursor", "max_items", "max_bytes"}
        }
        if cursor_payload is None
        else cursor_payload["selector"]
    )
    while True:
        blob_ids: set[str] = set()
        native_ids: set[str] = set()
        for event in page:
            native_ids.update(ref.material for ref in event.source_refs)
            value = event.model_dump(mode="json", exclude_none=True)
            payload = value.get("payload")
            if isinstance(payload, dict):
                for content in payload.get("content", []):
                    if (
                        isinstance(content, dict)
                        and content.get("type") == "blob"
                        and isinstance(content.get("ref"), str)
                    ):
                        blob_ids.add(content["ref"])
        end = start + len(page)
        if end < len(events):
            cursor = encode_cursor(
                {
                    "version": 3,
                    "intent": "trace",
                    "evidence_id": evidence.evidence_id,
                    "selector": selector,
                    "next": end,
                }
            )
        response = {
            **_base(evidence, "trace"),
            "events": [
                event.model_dump(mode="json", exclude_none=True) for event in page
            ],
            "content_refs": [
                _ref(evidence.evidence_id, "blob", item) for item in sorted(blob_ids)
            ],
            "native_refs": [
                _ref(evidence.evidence_id, "native", item)
                for item in sorted(native_ids)
            ],
            "next_cursor": cursor,
        }
        if len(canonical_json_bytes(response)) <= request.max_bytes:
            return response
        if not page:
            break
        page = page[:-1]
    raise AnalysisProtocolError(
        "query-page-budget-too-small", "Trace response envelope exceeds max_bytes."
    )


def _profile(
    evidence: ValidatedEvidenceV4, request: ProfileRequestV3
) -> dict[str, Any]:
    start = 0
    max_items = request.max_items
    max_bytes = request.max_bytes
    selector: dict[str, Any]
    if request.cursor is not None:
        payload = decode_cursor(request.cursor)
        if payload.get("version") != 3 or payload.get("intent") != "profile":
            raise AnalysisProtocolError(
                "cursor-version-mismatch", "Cursor requires a fresh original request."
            )
        if payload.get("evidence_id") != evidence.evidence_id:
            raise AnalysisProtocolError(
                "cursor-scope-mismatch", "Cursor belongs to different evidence."
            )
        selector_value, start_value = payload.get("selector"), payload.get("next")
        if not isinstance(selector_value, dict) or type(start_value) is not int:
            raise AnalysisProtocolError(
                "invalid-cursor", "Profile cursor has an invalid shape."
            )
        try:
            initial = ProfileRequestV3.model_validate(
                {"version": 3, "intent": "profile", **selector_value}
            )
        except ValidationError as error:
            raise AnalysisProtocolError(
                "invalid-cursor", "Profile cursor selector is invalid."
            ) from error
        selector, start, request = selector_value, start_value, initial
    else:
        selector = {
            key: value
            for key, value in request.model_dump(mode="json", exclude_none=True).items()
            if key not in {"version", "intent", "cursor", "max_items", "max_bytes"}
        }
    trajectory = evidence.trajectory
    event_ids: set[str] | None = None
    if request.scope.history == "path":
        leaf = _validate_ref(evidence, request.scope.leaf, "event")
        event_ids = path_event_ids(trajectory, leaf)
        if not event_ids:
            raise AnalysisProtocolError(
                "reference-not-found", "Path leaf event does not resolve."
            )
    selected_executions = {item.execution_id for item in trajectory.executions}
    if request.select.execution is not None:
        execution_id = _validate_ref(evidence, request.select.execution, "execution")
        if execution_id not in selected_executions:
            raise AnalysisProtocolError(
                "reference-not-found", "Execution does not resolve."
            )
        selected_executions = {execution_id}
        if request.select.descendants:
            selected_executions |= descendants(trajectory, execution_id)
    usage_events = tuple(
        event
        for event in trajectory.events
        if isinstance(event, UsageEvent)
        and (
            event_ids is None
            or event.event_id in event_ids
            or (
                event.payload.owner.type == "event"
                and event.payload.owner.id in event_ids
            )
        )
        and event.execution_id in selected_executions
    )
    by_execution: dict[str, list[UsageEvent]] = defaultdict(list)
    by_model: dict[str, list[UsageEvent]] = defaultdict(list)
    for event in usage_events:
        key = event.execution_id or "unknown"
        by_execution[key].append(event)
        by_model[event.payload.model or "unknown"].append(event)
    tools: dict[str, list[UsageEvent]] = defaultdict(list)
    tool_counts: dict[str, Counter[str]] = defaultdict(Counter)
    call_names = {
        event.payload.call_id: event.payload.name
        for event in trajectory.events
        if event.kind == "tool_call"
    }
    for event in trajectory.events:
        if event_ids is not None and event.event_id not in event_ids:
            continue
        if event.execution_id not in selected_executions:
            continue
        if event.kind == "tool_call":
            tool_counts[event.payload.name]["calls"] += 1
        elif event.kind == "tool_result":
            name = call_names.get(event.payload.call_id or "", "unknown")
            tool_counts[name]["results"] += 1
            if event.payload.outcome == "error":
                tool_counts[name]["errors"] += 1
    for event in usage_events:
        if event.payload.owner.type == "event":
            owner = next(
                (
                    item
                    for item in trajectory.events
                    if item.event_id == event.payload.owner.id
                ),
                None,
            )
            if owner and owner.kind in {"tool_call", "tool_result"}:
                tools[call_names.get(owner.payload.call_id, "unknown")].append(event)

    def breakdown(values: dict[str, list[UsageEvent]]) -> list[dict[str, Any]]:
        return [
            {"key": key, "usage": _usage(aggregate_usage(items))}
            for key, items in sorted(values.items())
        ]

    tool_breakdown = [
        {
            "key": key,
            "usage": _usage(aggregate_usage(tools.get(key, ()))),
            "calls": counts["calls"],
            "results": counts["results"],
            "errors": counts["errors"],
        }
        for key, counts in sorted(tool_counts.items())
    ]
    assert request.breakdown is not None
    entries = {
        "execution": breakdown(by_execution),
        "model": breakdown(by_model),
        "tool": tool_breakdown,
    }[request.breakdown]
    if not 0 <= start <= len(entries):
        raise AnalysisProtocolError(
            "cursor-scope-mismatch", "Profile cursor position no longer resolves."
        )
    end = min(len(entries), start + max_items)
    page = entries[start:end]
    cursor = None
    if end < len(entries):
        cursor = encode_cursor(
            {
                "version": 3,
                "intent": "profile",
                "evidence_id": evidence.evidence_id,
                "selector": selector,
                "next": end,
            }
        )
    while True:
        response = {
            **_base(evidence, "profile"),
            "breakdown": request.breakdown,
            "total": _usage(aggregate_usage(usage_events)),
            "rows": page,
            "next_cursor": cursor,
        }
        if len(canonical_json_bytes(response)) <= max_bytes:
            return response
        if not page:
            break
        page = page[:-1]
        end -= 1
        cursor = encode_cursor(
            {
                "version": 3,
                "intent": "profile",
                "evidence_id": evidence.evidence_id,
                "selector": selector,
                "next": end,
            }
        )
    raise AnalysisProtocolError(
        "query-page-budget-too-small", "Profile response envelope exceeds max_bytes."
    )


def _event_text(event: SemanticEvent) -> str:
    return event.model_dump_json(exclude_none=True)


def _match(evidence: ValidatedEvidenceV4, request: MatchRequestV3) -> dict[str, Any]:
    if request.cursor is not None:
        payload = decode_cursor(request.cursor)
        if payload.get("version") != 3 or payload.get("intent") != "match":
            raise AnalysisProtocolError(
                "cursor-version-mismatch", "Cursor requires a fresh original request."
            )
        if payload.get("evidence_id") != evidence.evidence_id:
            raise AnalysisProtocolError(
                "cursor-scope-mismatch", "Cursor belongs to different evidence."
            )
        predicates_value = payload.get("predicates")
        start = payload.get("next")
        if not isinstance(predicates_value, dict) or type(start) is not int:
            raise AnalysisProtocolError(
                "invalid-cursor", "Match cursor has an invalid shape."
            )
        try:
            predicates = MatchPredicatesV3.model_validate(predicates_value)
        except ValidationError as error:
            raise AnalysisProtocolError(
                "invalid-cursor", "Match cursor predicates are invalid."
            ) from error
    else:
        assert request.predicates is not None
        predicates = request.predicates
        start = 0
    events_list: list[SemanticEvent] = []
    for event in evidence.trajectory.events:
        if predicates.kinds is not None and event.kind not in predicates.kinds:
            continue
        if predicates.execution is not None:
            execution_id = _validate_ref(evidence, predicates.execution, "execution")
            if event.execution_id != execution_id:
                continue
        if predicates.tool_names is not None:
            name = event.payload.name if event.kind == "tool_call" else None
            if name not in predicates.tool_names:
                continue
        if predicates.text_terms is not None and not all(
            term in _event_text(event) for term in predicates.text_terms
        ):
            continue
        events_list.append(event)
    events = tuple(events_list)
    if not 0 <= start <= len(events):
        raise AnalysisProtocolError(
            "cursor-scope-mismatch", "Match cursor position no longer resolves."
        )
    end = min(len(events), start + request.max_items)
    page = events[start:end]
    cursor = None
    if end < len(events):
        cursor = encode_cursor(
            {
                "version": 3,
                "intent": "match",
                "evidence_id": evidence.evidence_id,
                "predicates": predicates.model_dump(mode="json", exclude_none=True),
                "next": end,
            }
        )
    refs = [_ref(evidence.evidence_id, "event", event.event_id) for event in page]
    while True:
        next_index = start + len(refs)
        cursor = (
            None
            if next_index >= len(events)
            else encode_cursor(
                {
                    "version": 3,
                    "intent": "match",
                    "evidence_id": evidence.evidence_id,
                    "predicates": predicates.model_dump(mode="json", exclude_none=True),
                    "next": next_index,
                }
            )
        )
        response = {**_base(evidence, "match"), "refs": refs, "next_cursor": cursor}
        if len(canonical_json_bytes(response)) <= request.max_bytes:
            return response
        if not refs:
            break
        refs.pop()
    raise AnalysisProtocolError(
        "query-page-budget-too-small", "Match response envelope exceeds max_bytes."
    )


def query_evidence_v3(
    evidence: ValidatedEvidenceV4, request_value: object
) -> dict[str, Any]:
    try:
        request = QUERY_REQUEST_V3.validate_python(request_value)
    except ValidationError as error:
        details = [
            {
                "pointer": "/" + "/".join(str(part) for part in item["loc"]),
                "message": item["msg"],
            }
            for item in error.errors(include_url=False)[:16]
        ]
        raise AnalysisProtocolError(
            "invalid-query-request", "Query v3 request is invalid.", {"errors": details}
        ) from error
    if isinstance(request, OverviewRequestV3):
        return _overview(evidence, request)
    if isinstance(request, TraceRequestV3):
        return _trace(evidence, request)
    if isinstance(request, ProfileRequestV3):
        return _profile(evidence, request)
    return _match(evidence, request)


__all__ = ["query_evidence_v3"]
