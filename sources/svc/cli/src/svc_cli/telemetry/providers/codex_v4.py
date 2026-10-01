"""Codex rollout collection and payload-bearing trajectory v2 normalization."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sqlite3
from typing import Any, Iterable, Mapping

from ...errors import SvcError
from ..agent_threads import MAX_SOURCE_BYTES, ProviderContext, ThreadSelection
from ..evidence_v4 import CollectionGap, EvidenceV4Manifest, build_evidence_v4_manifest
from ..trajectory_v2 import (
    BlobContent,
    ContextChangeEvent,
    ContextChangePayload,
    Coverage,
    CoverageIssue,
    ExecutionRecord,
    HeaderRecord,
    LifecycleEvent,
    LifecyclePayload,
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
from .codex_rollout import CodexRolloutProvider


def _stable_id(prefix: str, *parts: object) -> str:
    digest = hashlib.sha256(
        "\x00".join(str(part) for part in parts).encode()
    ).hexdigest()
    return f"{prefix}_{digest}"


def _session_meta(path: Path) -> dict[str, Any] | None:
    try:
        with path.open("rb") as stream:
            for raw in stream:
                try:
                    value = json.loads(raw)
                except (UnicodeDecodeError, json.JSONDecodeError):
                    continue
                if value.get("type") == "session_meta" and isinstance(
                    value.get("payload"), dict
                ):
                    return value["payload"]
    except OSError:
        return None
    return None


def _state_sources(home: Path) -> tuple[dict[str, Path], dict[str, str]]:
    database = home / "state_5.sqlite"
    if not database.is_file():
        return {}, {}
    sources: dict[str, Path] = {}
    parents: dict[str, str] = {}
    try:
        connection = sqlite3.connect(f"file:{database}?mode=ro", uri=True)
        connection.row_factory = sqlite3.Row
        columns = {row[1] for row in connection.execute("PRAGMA table_info(threads)")}
        id_name = next(
            (
                name
                for name in ("id", "thread_id", "threadId", "uuid")
                if name in columns
            ),
            None,
        )
        path_name = next(
            (
                name
                for name in ("rollout_path", "rolloutPath", "source_path", "path")
                if name in columns
            ),
            None,
        )
        parent_name = next(
            (
                name
                for name in ("parent_thread_id", "parentThreadId", "parent_id")
                if name in columns
            ),
            None,
        )
        if id_name is None or path_name is None:
            return {}, {}
        selected = [id_name, path_name, *([parent_name] if parent_name else [])]
        quoted = ", ".join(f'"{name}"' for name in selected)
        for row in connection.execute(f"SELECT {quoted} FROM threads"):
            thread_id, source_value = row[id_name], row[path_name]
            if not isinstance(thread_id, str) or not isinstance(source_value, str):
                continue
            source = Path(source_value).expanduser()
            if not source.is_absolute():
                source = home / source
            sources[thread_id] = source
            if parent_name and isinstance(row[parent_name], str):
                parents[thread_id] = row[parent_name]
    except sqlite3.DatabaseError as error:
        raise SvcError(
            "thread-source-incompatible", "Codex state database cannot be read."
        ) from error
    finally:
        if "connection" in locals():
            connection.close()
    return sources, parents


def _collect_sources(
    context: ProviderContext,
    selection: ThreadSelection,
) -> tuple[
    str, list[tuple[str, Path, str | None]], tuple[CollectionGap, ...], dict[str, str]
]:
    provider = CodexRolloutProvider()
    root = provider.resolve(context, selection)
    home = (
        Path(context.home).expanduser()
        if context.home is not None
        else Path.home() / ".codex"
    )
    sources, database_parents = _state_sources(home)
    sources[root.thread_id] = root.source_path
    candidates = {root.source_path.parent}
    candidates.update(
        path
        for path in (home / "sessions", home / "archived_sessions")
        if path.is_dir()
    )
    for directory in candidates:
        for path in directory.glob("**/*.jsonl"):
            meta = _session_meta(path)
            native_id = meta.get("id") if meta else None
            if isinstance(native_id, str):
                sources.setdefault(native_id, path)
    metadata: dict[str, dict[str, Any]] = {}
    parents = dict(database_parents)
    for thread_id, path in sources.items():
        meta = _session_meta(path)
        if meta is None:
            continue
        metadata[thread_id] = meta
        parent = meta.get("parent_thread_id")
        if isinstance(parent, str):
            parents[thread_id] = parent
    gap_parents: dict[str, str] = {}
    for parent_id, path in tuple(sources.items()):
        if not path.is_file():
            continue
        calls: dict[str, None] = {}
        targets: dict[str, str] = {}
        try:
            records = _native_lines(path.read_bytes())
            for _, _, _, value in records:
                payload = value.get("payload") if value else None
                if (
                    not isinstance(payload, Mapping)
                    or value.get("type") != "response_item"
                ):
                    continue
                if (
                    payload.get("type") == "function_call"
                    and payload.get("name") == "spawn_agent"
                ):
                    calls[str(payload.get("call_id") or len(calls))] = None
                elif payload.get("type") == "function_call_output":
                    call_id = str(payload.get("call_id") or "")
                    output = payload.get("output")
                    if isinstance(output, str):
                        try:
                            output = json.loads(output)
                        except json.JSONDecodeError:
                            output = None
                    if isinstance(output, Mapping):
                        child = output.get("agent_id") or output.get("thread_id")
                        if isinstance(child, str):
                            targets[call_id] = child
        except OSError:
            continue
        for call_id in calls:
            child_id = targets.get(call_id)
            if child_id is not None:
                parents.setdefault(child_id, parent_id)
                if child_id not in sources:
                    gap_parents[child_id] = parent_id
            else:
                gap_parents[f"unresolved-spawn:{parent_id}:{call_id}"] = parent_id
    selected: list[tuple[str, Path, str | None]] = []
    frontier = [root.thread_id]
    seen: set[str] = set()
    while frontier:
        current = frontier.pop(0)
        if current in seen:
            continue
        seen.add(current)
        path = sources.get(current)
        if path is not None and path.is_file():
            selected.append((current, path, parents.get(current)))
        for child, parent in sorted(parents.items()):
            if parent == current and child not in seen:
                frontier.append(child)
    gap_parents = {
        child: parent for child, parent in gap_parents.items() if parent in seen
    }
    missing = {
        thread_id: parents.get(thread_id)
        for thread_id in seen
        if thread_id in sources and not sources[thread_id].is_file()
    }
    gap_parents.update(
        {child: parent for child, parent in missing.items() if parent is not None}
    )
    gaps = tuple(
        CollectionGap(
            code="missing-execution-material",
            object_id=thread_id,
            affected_domains=("descendant_closure", "usage"),
        )
        for thread_id in sorted(gap_parents)
    )
    return root.thread_id, selected, gaps, gap_parents


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
    result: list[TextContent | BlobContent | OpaqueContent] = []
    for block in value:
        if not isinstance(block, Mapping):
            result.append(OpaqueContent(type="opaque", reason="unsupported-content"))
            continue
        text = block.get("text")
        if isinstance(text, str) and block.get("type") in {
            "text",
            "input_text",
            "output_text",
        }:
            result.append(_text_content(text, materials))
        else:
            result.append(
                OpaqueContent(
                    type="opaque", reason=f"unsupported-{block.get('type', 'content')}"
                )
            )
    return tuple(result)


def _measurements(value: Mapping[str, Any]) -> tuple[UsageMeasurement, ...]:
    names = {
        "input_tokens": ("input", "standalone", None),
        "cached_input_tokens": ("cache_read", "included_in", "input"),
        "cache_write_input_tokens": ("cache_write", "unknown", None),
        "output_tokens": ("output", "standalone", None),
        "reasoning_output_tokens": ("reasoning", "included_in", "output"),
        "total_tokens": ("total", "unknown", None),
    }
    result: list[UsageMeasurement] = []
    for native, (metric, inclusion, related) in names.items():
        amount = value.get(native)
        if type(amount) not in {int, float} or amount < 0:
            continue
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


def _native_lines(
    value: bytes,
) -> Iterable[tuple[int, int, int, dict[str, Any] | None]]:
    offset = 0
    for line, raw in enumerate(value.splitlines(keepends=True)):
        end = offset + len(raw)
        try:
            parsed = json.loads(raw)
        except (UnicodeDecodeError, json.JSONDecodeError):
            parsed = None
        yield line, offset, end, parsed if isinstance(parsed, dict) else None
        offset = end


def collect_codex_v4(
    context: ProviderContext,
    selection: ThreadSelection,
) -> tuple[EvidenceV4Manifest, bytes, dict[str, bytes]]:
    root_id, sources, gaps, gap_parents = _collect_sources(context, selection)
    if not sources:
        raise SvcError(
            "thread-source-not-found", "No Codex rollout material was collected."
        )
    executions: list[ExecutionRecord] = []
    events: list[Any] = []
    materials: dict[str, bytes] = {}
    execution_by_thread = {
        thread_id: _stable_id("exec", thread_id) for thread_id, _, _ in sources
    }
    execution_by_thread.update(
        {gap.object_id: _stable_id("exec", gap.object_id) for gap in gaps}
    )
    issues: list[CoverageIssue] = [
        CoverageIssue(
            issue_id=f"gap-{index}",
            code=gap.code,
            message=f"Material is missing for execution {gap.object_id}.",
            object_refs=(gap.object_id,),
        )
        for index, gap in enumerate(gaps)
    ]
    seq = 0
    for thread_id, path, parent in sources:
        value = path.read_bytes()
        if len(value) > MAX_SOURCE_BYTES:
            raise SvcError(
                "source-limit-reached", "Codex rollout exceeds the source bound."
            )
        material = f"native/{hashlib.sha256(thread_id.encode()).hexdigest()}.jsonl"
        materials[material] = value
        execution_id = execution_by_thread[thread_id]
        meta = _session_meta(path) or {}
        model = meta.get("model") or meta.get("model_provider")
        executions.append(
            ExecutionRecord(
                type="execution",
                execution_id=execution_id,
                role="root" if thread_id == root_id else "subagent",
                source_refs=(SourceRef(material=material, line=0),),
                model=model if isinstance(model, str) else None,
                native_id=thread_id,
            )
        )
        if parent in execution_by_thread:
            events.append(
                RelationEvent(
                    type="event",
                    kind="relation",
                    event_id=_stable_id("evt", material, 0, "delegation"),
                    seq=seq,
                    execution_id=execution_by_thread[parent],
                    source_refs=(SourceRef(material=material, line=0),),
                    mapping="explicit",
                    payload=RelationPayload(
                        relation="delegation",
                        source=RelationEndpoint(
                            type="execution", id=execution_by_thread[parent]
                        ),
                        target=RelationEndpoint(type="execution", id=execution_id),
                    ),
                )
            )
            seq += 1
        for line, start, end, envelope in _native_lines(value):
            if envelope is None:
                issues.append(
                    CoverageIssue(
                        issue_id=f"invalid-{len(issues)}",
                        code="invalid-native-record",
                        message="A Codex rollout line is not valid JSON.",
                    )
                )
                continue
            native_type = envelope.get("type")
            payload = envelope.get("payload")
            if not isinstance(payload, Mapping) or native_type == "session_meta":
                continue
            timestamp = (
                envelope.get("timestamp")
                if isinstance(envelope.get("timestamp"), str)
                else None
            )
            source = (
                SourceRef(material=material, line=line, byte_start=start, byte_end=end),
            )
            base = {
                "type": "event",
                "event_id": _stable_id(
                    "evt", material, line, native_type, payload.get("type")
                ),
                "seq": seq,
                "execution_id": execution_id,
                "source_refs": source,
                "timestamp": timestamp,
                "turn_id": (
                    payload.get("turn_id")
                    if isinstance(payload.get("turn_id"), str)
                    else (
                        payload.get(
                            "internal_chat_message_metadata_passthrough", {}
                        ).get("turn_id")
                        if isinstance(
                            payload.get("internal_chat_message_metadata_passthrough"),
                            Mapping,
                        )
                        else None
                    )
                ),
                "mapping": "explicit",
            }
            record_type = payload.get("type")
            event: Any | None = None
            if native_type == "response_item" and record_type == "message":
                role = payload.get("role")
                event = MessageEvent(
                    kind="message",
                    payload=MessagePayload(
                        role=role
                        if role in {"system", "developer", "user", "assistant", "tool"}
                        else "unknown",
                        content=_content(payload.get("content"), materials),
                    ),
                    **base,
                )
            elif native_type == "response_item" and record_type == "reasoning":
                summary = payload.get("summary")
                content = _content(
                    summary if summary else payload.get("content"), materials
                )
                visibility = (
                    "summary"
                    if summary
                    else ("full" if payload.get("content") else "opaque")
                )
                event = ReasoningEvent(
                    kind="reasoning",
                    payload=ReasoningPayload(visibility=visibility, content=content),
                    **base,
                )
            elif native_type == "response_item" and record_type == "function_call":
                arguments = payload.get("arguments")
                if isinstance(arguments, str):
                    try:
                        arguments = json.loads(arguments)
                    except json.JSONDecodeError:
                        pass
                event = ToolCallEvent(
                    kind="tool_call",
                    payload=ToolCallPayload(
                        call_id=str(
                            payload.get("call_id") or _stable_id("call", material, line)
                        ),
                        name=str(payload.get("name") or "unknown"),
                        arguments_state="available"
                        if "arguments" in payload
                        else "unknown",
                        arguments=arguments if "arguments" in payload else None,
                    ),
                    **base,
                )
            elif (
                native_type == "response_item" and record_type == "function_call_output"
            ):
                event = ToolResultEvent(
                    kind="tool_result",
                    payload=ToolResultPayload(
                        call_id=str(payload["call_id"])
                        if payload.get("call_id") is not None
                        else None,
                        linkage="linked"
                        if payload.get("call_id") is not None
                        else "unresolved",
                        outcome="error"
                        if payload.get("status") == "error"
                        else "success",
                        content=_content(payload.get("output"), materials),
                    ),
                    **base,
                )
            elif native_type == "event_msg" and record_type in {
                "task_started",
                "task_complete",
                "task_aborted",
            }:
                transition = {
                    "task_started": "start",
                    "task_complete": "complete",
                    "task_aborted": "cancel",
                }[record_type]
                event = LifecycleEvent(
                    kind="lifecycle",
                    payload=LifecyclePayload(subject="turn", transition=transition),
                    **base,
                )
            elif native_type == "event_msg" and record_type == "context_compacted":
                event = ContextChangeEvent(
                    kind="context_change",
                    payload=ContextChangePayload(
                        operation="compact", subject="history"
                    ),
                    **base,
                )
            elif native_type == "event_msg" and record_type == "token_count":
                info = payload.get("info")
                if isinstance(info, Mapping):
                    total = info.get("total_token_usage")
                    last = info.get("last_token_usage")
                    for label, usage, temporality in (
                        ("total", total, "cumulative"),
                        ("last", last, "delta"),
                    ):
                        if not isinstance(usage, Mapping) or not _measurements(usage):
                            continue
                        usage_base = dict(base)
                        usage_base["event_id"] = _stable_id(
                            "evt", material, line, "usage", label
                        )
                        usage_base["seq"] = seq
                        event = UsageEvent(
                            kind="usage",
                            payload=UsagePayload(
                                owner=UsageOwner(type="execution", id=execution_id),
                                model=model if isinstance(model, str) else None,
                                scope="self",
                                temporality=temporality,
                                measurements=_measurements(usage),
                                sample_id=(
                                    _stable_id("sample", material, line, label)
                                    if label == "total"
                                    else None
                                ),
                                counter_id=(
                                    f"codex-total:{execution_id}"
                                    if label == "total"
                                    else None
                                ),
                                zero_baseline=(label == "total" and line == 0),
                                source="provider_reported",
                            ),
                            **usage_base,
                        )
                        events.append(event)
                        seq += 1
                    event = None
            elif native_type in {"event_msg", "response_item"}:
                event = ProviderEvent(
                    kind="provider_event",
                    payload=ProviderEventPayload(
                        namespace="codex.rollout/v1",
                        event_type=str(record_type or native_type),
                        value=dict(payload),
                    ),
                    **base,
                )
            if event is not None:
                events.append(event)
                seq += 1
    for gap in gaps:
        execution_id = execution_by_thread[gap.object_id]
        if execution_id in {item.execution_id for item in executions}:
            continue
        parent_execution = execution_by_thread[gap_parents[gap.object_id]]
        parent_material = next(
            item.source_refs[0].material
            for item in executions
            if item.execution_id == parent_execution
        )
        executions.append(
            ExecutionRecord(
                type="execution",
                execution_id=execution_id,
                role="subagent",
                source_refs=(SourceRef(material=parent_material, line=0),),
                native_id=gap.object_id,
            )
        )
        events.append(
            RelationEvent(
                type="event",
                kind="relation",
                event_id=_stable_id("evt", gap.object_id, "delegation"),
                seq=seq,
                execution_id=parent_execution,
                source_refs=(SourceRef(material=parent_material, line=0),),
                mapping="derived",
                payload=RelationPayload(
                    relation="delegation",
                    source=RelationEndpoint(type="execution", id=parent_execution),
                    target=RelationEndpoint(type="execution", id=execution_id),
                ),
            )
        )
        seq += 1
    issue_ids = tuple(item.issue_id for item in issues)
    coverage = tuple(
        Coverage(
            domain=domain,
            status=(
                "partial"
                if issue_ids and domain in {"content", "descendant_closure", "usage"}
                else "complete"
            ),
            issue_ids=(
                issue_ids
                if issue_ids and domain in {"content", "descendant_closure", "usage"}
                else ()
            ),
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
    header = HeaderRecord(
        type="header",
        trajectory_schema="svc.trajectory/v2",
        provider_id="codex",
        source_format="rollout-v1",
        normalizer="codex.rollout/v2",
        roots=(execution_by_thread[root_id],),
        coverage=coverage,
        issues=tuple(issues),
    )
    trajectory = encode_trajectory_v2((header, *executions, *events))
    manifest = build_evidence_v4_manifest(
        provider_id="codex",
        source_format="rollout-v1",
        selected_roots=(root_id,),
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
        gaps=gaps,
    )
    return manifest, trajectory, materials


__all__ = ["collect_codex_v4"]
