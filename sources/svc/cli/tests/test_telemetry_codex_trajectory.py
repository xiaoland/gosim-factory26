from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path
from typing import Any, Mapping

from svc_cli.telemetry.agent_threads import NormalizationStatus, ResolvedThread
from svc_cli.telemetry.providers.codex_trajectory import CodexTrajectoryNormalizer


def envelope(
    kind: str,
    payload: object,
    timestamp: str = "2026-01-01T00:00:00Z",
) -> dict[str, object]:
    return {"timestamp": timestamp, "type": kind, "payload": payload}


def session(thread_id: str, **payload: object) -> dict[str, object]:
    return envelope("session_meta", {"id": thread_id, **payload})


def response(kind: str, **payload: object) -> dict[str, object]:
    return envelope("response_item", {"type": kind, **payload})


def event(kind: str, **payload: object) -> dict[str, object]:
    return envelope("event_msg", {"type": kind, **payload})


def project(
    *events: dict[str, object] | str,
    bounds: Mapping[str, int] | None = None,
) -> tuple[object, list[dict[str, Any]]]:
    lines = [
        item if isinstance(item, str) else json.dumps(item, ensure_ascii=False)
        for item in events
    ]
    stream = BytesIO(("\n".join(lines) + "\n").encode("utf-8"))
    resolved = ResolvedThread(
        provider_id="codex",
        adapter_id="codex-rollout-v1",
        source_format="rollout-v1",
        thread_id="thread-test",
        source_path=Path("unused-rollout.jsonl"),
    )
    records: list[dict[str, Any]] = []
    result = CodexTrajectoryNormalizer().normalize(
        stream,
        resolved,
        lambda record: records.append(dict(record)) or True,
        bounds,
    )
    return result, records


def test_normalizer_emits_only_structural_chain_fields() -> None:
    relation = {
        "turn_id": "turn-native",
        "author": "agent-native",
        "recipient": "lane-native",
    }
    result, records = project(
        session("thread-test", cwd="/work/project"),
        response(
            "message",
            role="developer",
            content="developer context is deliberately not cached",
            internal_chat_message_metadata_passthrough=relation,
        ),
        response(
            "message",
            role="user",
            content="inspect tasks/flow/packet.md",
            internal_chat_message_metadata_passthrough=relation,
        ),
        response("message", role="assistant", content="working"),
        response(
            "function_call",
            name="svc",
            call_id="call-native",
            arguments={"cmd": "status"},
            parent_actor_id="parent-native",
            internal_chat_message_metadata_passthrough=relation,
        ),
        event(
            "exec_command_end",
            call_id="call-native",
            status="completed",
            internal_chat_message_metadata_passthrough=relation,
        ),
        response("function_call_output", call_id="call-native", output="done"),
        event("task_started"),
        event("task_complete", status="completed"),
        event("context_compacted"),
        event("user_message", text="UI duplicate"),
        event("token_count", count=4),
    )

    assert [record["type"] for record in records] == [
        "meta",
        "context",
        "message",
        "message",
        "tool_call",
        "tool_result",
        "event",
        "event",
        "event",
    ]
    assert [record["record_index"] for record in records] == list(range(9))
    assert records[0]["workspace"]["label"] == "project"
    assert records[2]["task_refs"] == ["tasks/flow/packet.md"]
    assert records[4]["arguments_kind"] == "json"
    assert records[5]["status"] == "success"
    assert records[5]["link_status"] == "linked"
    assert records[2]["relationships"] == {
        key: records[4]["relationships"][key] for key in records[2]["relationships"]
    }
    assert set(records[4]["relationships"]) >= {
        "turn_ref",
        "actor_ref",
        "parent_actor_ref",
        "lane_ref",
    }
    assert not any(
        removed in record
        for record in records
        for removed in (
            "content",
            "content_meta",
            "arguments",
            "arguments_meta",
            "arguments_fingerprint",
            "name_meta",
            "name_fingerprint",
            "fingerprint",
            "attributes_meta",
        )
    )
    assert result.result_status is NormalizationStatus.READY
    assert result.lossiness == {
        "dropped_records": 0,
        "unavailable_records": 0,
        "synthesized_records": 0,
        "partial_frames": 0,
    }
    assert result.capabilities["context"] == "partial"
    assert result.capabilities["terminal_events"] == "available"


def test_normalizer_reports_structural_loss_without_diagnostics() -> None:
    result, records = project(
        session("thread-test"),
        response("reasoning", summary="summary", encrypted_content="opaque"),
        response("reasoning", encrypted_content="opaque"),
        "{not-json}",
        response("function_call", name="synthetic"),
        response("function_call", name="explicit", call_id="explicit-1"),
        response(
            "function_call_output",
            call_id="explicit-1",
            status="success",
        ),
        response(
            "function_call_output",
            call_id="explicit-1",
            status="error",
        ),
    )

    reasoning = [record for record in records if record["type"] == "reasoning"]
    assert reasoning == [
        {
            key: reasoning[0][key]
            for key in (
                "type",
                "record_id",
                "record_index",
                "timestamp",
                "source_ref",
                "relationships",
                "reasoning_kind",
            )
        }
    ]
    assert reasoning[0]["reasoning_kind"] == "summary"
    assert result.result_status is NormalizationStatus.PARTIAL
    assert result.capabilities["reasoning"] == "summary"
    assert result.capabilities["tool_linkage"] == "mixed"
    assert result.lossiness == {
        "dropped_records": 2,
        "unavailable_records": 2,
        "synthesized_records": 1,
        "partial_frames": 0,
    }


def test_task_refs_use_full_message_without_content_or_task_caps() -> None:
    first = "tasks/first/packet.md"
    second = "tasks/second/packet.md"
    content = " ".join(
        [
            "x" * 20_000,
            first,
            second,
            "/private/tasks/absolute/packet.md",
            r"tasks\backslash\packet.md",
            "tasks/../invalid/packet.md",
        ]
    )
    result, records = project(
        session("thread-test"),
        response("message", role="user", content=content),
        bounds={"task_reference_occurrences": 1, "message_context_code_points": 1},
    )

    message = next(record for record in records if record["type"] == "message")
    assert message["task_refs"] == [first, second]
    assert "content" not in message
    assert result.lossiness["dropped_records"] == 0


def test_frame_bound_is_reported_only_as_partial_frame_loss() -> None:
    result, records = project(
        session("thread-test", cwd="/workspace/" + "x" * 200),
        bounds={"native_line_bytes": 32},
    )

    assert [record["type"] for record in records] == ["meta"]
    assert records[0]["workspace"]["status"] == "missing"
    assert result.result_status is NormalizationStatus.PARTIAL
    assert result.lossiness == {
        "dropped_records": 0,
        "unavailable_records": 0,
        "synthesized_records": 0,
        "partial_frames": 1,
    }
