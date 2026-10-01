"""Standard Pi session v3 collection and trajectory normalization."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from ...errors import SvcError
from ..agent_threads import MAX_SOURCE_BYTES, ProviderContext, ThreadSelection
from ..evidence_v4 import EvidenceV4Manifest, build_evidence_v4_manifest
from ..trajectory_v2 import (
    BlobContent,
    ContextChangeEvent,
    ContextChangePayload,
    Coverage,
    CoverageIssue,
    ExecutionRecord,
    HeaderRecord,
    MessageEvent,
    MessagePayload,
    OpaqueContent,
    ProviderEvent,
    ProviderEventPayload,
    ReasoningEvent,
    ReasoningPayload,
    RelationEndpoint,
    RelationEvent,
    RelationPayload,
    SourceRef,
    TextContent,
    ToolCallEvent,
    ToolCallPayload,
    ToolResultEvent,
    ToolResultPayload,
    UsageEvent,
    UsageMeasurement,
    UsageOwner,
    UsagePayload,
    encode_trajectory_v2,
)


def _stable_id(prefix: str, *parts: object) -> str:
    return f"{prefix}_{hashlib.sha256(chr(0).join(str(part) for part in parts).encode()).hexdigest()}"


def _header(path: Path) -> dict[str, Any] | None:
    try:
        with path.open("rb") as stream:
            for raw in stream:
                if not raw.strip():
                    continue
                value = json.loads(raw)
                return (
                    value
                    if isinstance(value, dict) and value.get("type") == "session"
                    else None
                )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    return None


def _resolve(context: ProviderContext, selection: ThreadSelection) -> Path:
    if selection.source is not None:
        path = Path(selection.source).expanduser()
        if _header(path) is None:
            raise SvcError(
                "thread-source-incompatible", "Source is not a Pi session JSONL file."
            )
        return path
    assert selection.thread_id is not None
    home = (
        Path(context.home).expanduser()
        if context.home is not None
        else Path.home() / ".pi" / "agent"
    )
    matches = [
        path
        for path in home.glob("sessions/**/*.jsonl")
        if (_header(path) or {}).get("id") == selection.thread_id
    ]
    if len(matches) != 1:
        raise SvcError("thread-not-found", "Pi session ID did not resolve uniquely.")
    return matches[0]


def _line_records(value: bytes):
    offset = 0
    for line, raw in enumerate(value.splitlines(keepends=True)):
        end = offset + len(raw)
        try:
            parsed = json.loads(raw)
        except (UnicodeDecodeError, json.JSONDecodeError):
            parsed = None
        yield line, offset, end, parsed if isinstance(parsed, dict) else None
        offset = end


def _text_content(value: str, materials: dict[str, bytes]) -> TextContent | BlobContent:
    encoded = value.encode("utf-8")
    if len(encoded) <= 16_384:
        return TextContent(type="text", text=value)
    name = f"blob/{hashlib.sha256(encoded).hexdigest()}.txt"
    materials[name] = encoded
    return BlobContent(type="blob", ref=name, media_type="text/plain; charset=utf-8")


def _content(
    value: object, materials: dict[str, bytes]
) -> tuple[TextContent | BlobContent | OpaqueContent, ...]:
    if isinstance(value, str):
        return (_text_content(value, materials),)
    if not isinstance(value, list):
        return (OpaqueContent(type="opaque", reason="content-unavailable"),)
    result: list[TextContent | OpaqueContent] = []
    for block in value:
        if (
            isinstance(block, Mapping)
            and block.get("type") == "text"
            and isinstance(block.get("text"), str)
        ):
            result.append(_text_content(block["text"], materials))
        elif isinstance(block, Mapping) and block.get("type") in {
            "thinking",
            "toolCall",
        }:
            continue
        else:
            result.append(OpaqueContent(type="opaque", reason="unsupported-content"))
    return tuple(result)


def _usage_measurements(value: Mapping[str, Any]) -> tuple[UsageMeasurement, ...]:
    names = {
        "input": ("input", "standalone", None),
        "output": ("output", "standalone", None),
        "cacheRead": ("cache_read", "unknown", None),
        "cacheWrite": ("cache_write", "unknown", None),
        "reasoning": ("reasoning", "included_in", "output"),
    }
    result: list[UsageMeasurement] = []
    for native, (metric, inclusion, related) in names.items():
        amount = value.get(native)
        if type(amount) in {int, float} and amount >= 0:
            result.append(
                UsageMeasurement(
                    metric=metric,
                    value=amount,
                    unit="tokens",
                    inclusion=inclusion,
                    related_metric=related,
                )
            )
    return tuple(result)


def _cost_measurement(value: Mapping[str, Any]) -> tuple[UsageMeasurement, ...]:
    cost = value.get("cost")
    if (
        not isinstance(cost, Mapping)
        or type(cost.get("total")) not in {int, float}
        or cost["total"] < 0
    ):
        return ()
    return (
        UsageMeasurement(
            metric="cost",
            value=cost["total"],
            unit="currency",
            currency="USD",
            inclusion="unknown",
        ),
    )


def _parent_path(path: Path, parent: str) -> Path:
    candidate = Path(parent).expanduser()
    return candidate if candidate.is_absolute() else path.parent / candidate


def _collect_lineage(selected: Path) -> list[Path]:
    lineage: list[Path] = []
    current = selected
    seen: set[Path] = set()
    while current not in seen:
        seen.add(current)
        header = _header(current)
        if header is None:
            break
        lineage.append(current)
        parent = header.get("parentSession")
        if not isinstance(parent, str):
            break
        current = _parent_path(current, parent)
        if not current.is_file():
            break
    lineage.reverse()
    return lineage


def collect_pi_v4(
    context: ProviderContext,
    selection: ThreadSelection,
) -> tuple[EvidenceV4Manifest, bytes, dict[str, bytes]]:
    selected = _resolve(context, selection)
    paths = _collect_lineage(selected)
    headers = [_header(path) for path in paths]
    if not paths or any(header is None for header in headers):
        raise SvcError("thread-source-incompatible", "Pi session lineage is invalid.")
    typed_headers = [header for header in headers if header is not None]
    execution_ids = {
        header["id"]: _stable_id("exec", header["id"]) for header in typed_headers
    }
    materials: dict[str, bytes] = {}
    executions: list[ExecutionRecord] = []
    events: list[Any] = []
    issues: list[CoverageIssue] = []
    seq = 0
    previous_session: str | None = None
    inherited_events: dict[str, str] = {}
    for path, header in zip(paths, typed_headers, strict=True):
        session_id = header["id"]
        value = path.read_bytes()
        if len(value) > MAX_SOURCE_BYTES:
            raise SvcError(
                "source-limit-reached", "Pi session exceeds the source bound."
            )
        material = f"native/{hashlib.sha256(session_id.encode()).hexdigest()}.jsonl"
        materials[material] = value
        model: str | None = None
        for _, _, _, entry in _line_records(value):
            if (
                entry
                and entry.get("type") == "message"
                and isinstance(entry.get("message"), Mapping)
            ):
                candidate = entry["message"].get("model")
                if isinstance(candidate, str):
                    model = candidate
        executions.append(
            ExecutionRecord(
                type="execution",
                execution_id=execution_ids[session_id],
                role="root" if path == selected else "unknown",
                source_refs=(SourceRef(material=material, line=0),),
                model=model,
                native_id=session_id,
            )
        )
        if previous_session is not None:
            events.append(
                RelationEvent(
                    type="event",
                    kind="relation",
                    event_id=_stable_id("evt", material, "history-inheritance"),
                    seq=seq,
                    execution_id=execution_ids[session_id],
                    source_refs=(SourceRef(material=material, line=0),),
                    mapping="explicit",
                    payload=RelationPayload(
                        relation="history_inheritance",
                        source=RelationEndpoint(
                            type="execution", id=execution_ids[previous_session]
                        ),
                        target=RelationEndpoint(
                            type="execution", id=execution_ids[session_id]
                        ),
                    ),
                )
            )
            seq += 1
        previous_session = session_id
        entry_event_ids: dict[str, str] = {}
        for line, start, end, entry in _line_records(value):
            if line == 0:
                continue
            if entry is None:
                issue_id = f"invalid-{len(issues)}"
                issues.append(
                    CoverageIssue(
                        issue_id=issue_id,
                        code="invalid-native-record",
                        message="A Pi session line is not valid JSON.",
                    )
                )
                continue
            entry_id = entry.get("id")
            if not isinstance(entry_id, str):
                continue
            if entry_id in inherited_events:
                entry_event_ids[entry_id] = inherited_events[entry_id]
                continue
            primary_id = _stable_id("evt", material, entry_id, "primary")
            parent_id = entry.get("parentId")
            predecessor_ids = (
                (entry_event_ids[parent_id],)
                if isinstance(parent_id, str) and parent_id in entry_event_ids
                else ()
            )
            source = (
                SourceRef(
                    material=material,
                    record_id=entry_id,
                    line=line,
                    byte_start=start,
                    byte_end=end,
                ),
            )
            timestamp = (
                entry.get("timestamp")
                if isinstance(entry.get("timestamp"), str)
                else None
            )
            generated: list[Any] = []
            entry_type = entry.get("type")
            message = entry.get("message")
            common = {
                "type": "event",
                "seq": seq,
                "execution_id": execution_ids[session_id],
                "source_refs": source,
                "timestamp": timestamp,
                "predecessor_ids": predecessor_ids,
                "mapping": "explicit",
            }
            if entry_type == "message" and isinstance(message, Mapping):
                role = message.get("role")
                if role in {"system", "user", "assistant"}:
                    generated.append(
                        MessageEvent(
                            event_id=primary_id,
                            kind="message",
                            payload=MessagePayload(
                                role=role,
                                content=_content(message.get("content"), materials),
                            ),
                            **common,
                        )
                    )
                elif role == "toolResult":
                    generated.append(
                        ToolResultEvent(
                            event_id=primary_id,
                            kind="tool_result",
                            payload=ToolResultPayload(
                                call_id=str(message["toolCallId"])
                                if message.get("toolCallId") is not None
                                else None,
                                linkage="linked"
                                if message.get("toolCallId") is not None
                                else "unresolved",
                                outcome="error"
                                if message.get("isError")
                                else "success",
                                content=_content(message.get("content"), materials),
                            ),
                            **common,
                        )
                    )
                if role == "assistant" and isinstance(message.get("content"), list):
                    for index, block in enumerate(message["content"]):
                        if not isinstance(block, Mapping):
                            continue
                        extra = {
                            **common,
                            "seq": seq + len(generated),
                            "predecessor_ids": (),
                        }
                        if block.get("type") == "thinking" and isinstance(
                            block.get("thinking"), str
                        ):
                            generated.append(
                                ReasoningEvent(
                                    event_id=_stable_id(
                                        "evt", material, entry_id, "thinking", index
                                    ),
                                    kind="reasoning",
                                    payload=ReasoningPayload(
                                        visibility="full",
                                        content=(
                                            TextContent(
                                                type="text", text=block["thinking"]
                                            ),
                                        ),
                                    ),
                                    **extra,
                                )
                            )
                        elif block.get("type") == "toolCall":
                            generated.append(
                                ToolCallEvent(
                                    event_id=_stable_id(
                                        "evt", material, entry_id, "tool", index
                                    ),
                                    kind="tool_call",
                                    payload=ToolCallPayload(
                                        call_id=str(
                                            block.get("id")
                                            or _stable_id(
                                                "call", material, entry_id, index
                                            )
                                        ),
                                        name=str(block.get("name") or "unknown"),
                                        arguments_state="available"
                                        if "arguments" in block
                                        else "unknown",
                                        arguments=block.get("arguments")
                                        if "arguments" in block
                                        else None,
                                    ),
                                    **extra,
                                )
                            )
                usage = message.get("usage") if isinstance(message, Mapping) else None
                if isinstance(usage, Mapping) and _usage_measurements(usage):
                    generated.append(
                        UsageEvent(
                            event_id=_stable_id("evt", material, entry_id, "usage"),
                            kind="usage",
                            payload=UsagePayload(
                                owner=UsageOwner(type="event", id=primary_id),
                                model=message.get("model")
                                if isinstance(message.get("model"), str)
                                else None,
                                scope="self",
                                temporality="delta",
                                measurements=_usage_measurements(usage),
                                sample_id=str(message.get("responseId") or entry_id),
                                source="provider_reported",
                            ),
                            **{
                                **common,
                                "seq": seq + len(generated),
                                "predecessor_ids": (),
                            },
                        )
                    )
                if isinstance(usage, Mapping) and _cost_measurement(usage):
                    generated.append(
                        UsageEvent(
                            event_id=_stable_id("evt", material, entry_id, "cost"),
                            kind="usage",
                            payload=UsagePayload(
                                owner=UsageOwner(type="event", id=primary_id),
                                model=message.get("model")
                                if isinstance(message.get("model"), str)
                                else None,
                                scope="self",
                                temporality="delta",
                                measurements=_cost_measurement(usage),
                                sample_id=f"cost:{message.get('responseId') or entry_id}",
                                source="client_estimated",
                            ),
                            **{
                                **common,
                                "seq": seq + len(generated),
                                "predecessor_ids": (),
                            },
                        )
                    )
            elif entry_type in {
                "model_change",
                "thinking_level_change",
                "compaction",
                "branch_summary",
            }:
                operation = (
                    "compact"
                    if entry_type == "compaction"
                    else (
                        "replace"
                        if entry_type in {"model_change", "thinking_level_change"}
                        else "append"
                    )
                )
                subject = (
                    "history"
                    if entry_type in {"compaction", "branch_summary"}
                    else ("model" if entry_type == "model_change" else "configuration")
                )
                text = entry.get("summary")
                generated.append(
                    ContextChangeEvent(
                        event_id=primary_id,
                        kind="context_change",
                        payload=ContextChangePayload(
                            operation=operation,
                            subject=subject,
                            content=(
                                (TextContent(type="text", text=text),)
                                if isinstance(text, str)
                                else ()
                            ),
                            affected_event_ids=(
                                (entry_event_ids[entry["fromId"]],)
                                if entry_type == "branch_summary"
                                and entry.get("fromId") in entry_event_ids
                                else ()
                            ),
                        ),
                        **common,
                    )
                )
                usage = entry.get("usage")
                if isinstance(usage, Mapping) and _usage_measurements(usage):
                    generated.append(
                        UsageEvent(
                            event_id=_stable_id("evt", material, entry_id, "usage"),
                            kind="usage",
                            payload=UsagePayload(
                                owner=UsageOwner(type="event", id=primary_id),
                                scope="self",
                                temporality="delta",
                                measurements=_usage_measurements(usage),
                                sample_id=entry_id,
                                source="provider_reported",
                            ),
                            **{**common, "seq": seq + 1, "predecessor_ids": ()},
                        )
                    )
                if isinstance(usage, Mapping) and _cost_measurement(usage):
                    generated.append(
                        UsageEvent(
                            event_id=_stable_id("evt", material, entry_id, "cost"),
                            kind="usage",
                            payload=UsagePayload(
                                owner=UsageOwner(type="event", id=primary_id),
                                scope="self",
                                temporality="delta",
                                measurements=_cost_measurement(usage),
                                sample_id=f"cost:{entry_id}",
                                source="client_estimated",
                            ),
                            **{
                                **common,
                                "seq": seq + len(generated),
                                "predecessor_ids": (),
                            },
                        )
                    )
            else:
                generated.append(
                    ProviderEvent(
                        event_id=primary_id,
                        kind="provider_event",
                        payload=ProviderEventPayload(
                            namespace="pi.session/v3",
                            event_type=str(entry_type),
                            value=entry,
                        ),
                        **common,
                    )
                )
            if generated:
                entry_event_ids[entry_id] = generated[0].event_id
                events.extend(generated)
                seq += len(generated)
            if generated:
                inherited_events[entry_id] = generated[0].event_id
    issues.append(
        CoverageIssue(
            issue_id="terminal-state-unavailable",
            code="terminal-state-unavailable",
            message="Standard Pi session persistence does not declare an execution terminal state.",
        )
    )
    issue_ids = tuple(
        item.issue_id
        for item in issues
        if item.issue_id != "terminal-state-unavailable"
    )
    coverage = tuple(
        (
            Coverage(
                domain=domain,
                status="unavailable",
                issue_ids=("terminal-state-unavailable",),
            )
            if domain == "terminal_state"
            else Coverage(
                domain=domain,
                status=(
                    "partial"
                    if issue_ids and domain in {"content", "history_branch", "usage"}
                    else "complete"
                ),
                issue_ids=(
                    issue_ids
                    if issue_ids and domain in {"content", "history_branch", "usage"}
                    else ()
                ),
            )
        )
        for domain in (
            "content",
            "tool_linkage",
            "relation_mapping",
            "descendant_closure",
            "history_branch",
            "usage",
            "timestamps",
            "terminal_state",
        )
    )
    selected_header = typed_headers[-1]
    header = HeaderRecord(
        type="header",
        trajectory_schema="svc.trajectory/v2",
        provider_id="pi",
        source_format=f"session-v{selected_header.get('version', 1)}",
        normalizer="pi.session/v1",
        roots=(execution_ids[selected_header["id"]],),
        coverage=coverage,
        issues=tuple(issues),
    )
    trajectory = encode_trajectory_v2((header, *executions, *events))
    manifest = build_evidence_v4_manifest(
        provider_id="pi",
        source_format=f"session-v{selected_header.get('version', 1)}",
        selected_roots=(selected_header["id"],),
        trajectory=trajectory,
        materials=materials,
        material_kinds={
            name: ("blob" if name.startswith("blob/") else "native")
            for name in materials
        },
        material_media_types={
            name: (
                "text/plain; charset=utf-8"
                if name.startswith("blob/")
                else "application/x-ndjson"
            )
            for name in materials
        },
    )
    return manifest, trajectory, materials


def list_pi_sessions(
    home: Path | None, limit: int
) -> tuple[list[dict[str, object]], bool]:
    root = (
        Path(home).expanduser() if home is not None else Path.home() / ".pi" / "agent"
    )
    rows: list[dict[str, object]] = []
    for path in root.glob("sessions/**/*.jsonl"):
        header = _header(path)
        if header is None or not isinstance(header.get("id"), str):
            continue
        rows.append(
            {
                "provider_id": "pi",
                "thread_id": header["id"],
                "archive_state": "unknown",
                "workspace": header.get("cwd")
                if isinstance(header.get("cwd"), str)
                else None,
                "title": None,
                "first_user_message": None,
                "workspace_truncated": False,
                "title_truncated": False,
                "first_user_message_truncated": False,
                "created_at": header.get("timestamp")
                if isinstance(header.get("timestamp"), str)
                else None,
                "updated_at": None,
                "recency_at_ms": int(path.stat().st_mtime_ns / 1_000_000),
            }
        )
    rows.sort(key=lambda item: (-int(item["recency_at_ms"]), str(item["thread_id"])))
    return rows[:limit], len(rows) > limit


__all__ = ["collect_pi_v4", "list_pi_sessions"]
