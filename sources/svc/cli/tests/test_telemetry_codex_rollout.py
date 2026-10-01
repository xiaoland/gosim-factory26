from __future__ import annotations

from io import BytesIO
import json
from pathlib import Path
import sqlite3
from typing import Mapping

import pytest

from svc_cli.errors import SvcError
from svc_cli.telemetry.agent_threads import ProviderContext, ThreadSelection
from svc_cli.telemetry.archive import write_agent_thread_evidence
from svc_cli.telemetry.providers import CodexRolloutProvider


def _envelope(record_type: str, payload: object) -> dict[str, object]:
    return {
        "timestamp": "2026-01-01T00:00:00Z",
        "type": record_type,
        "payload": payload,
    }


def _source(path: Path, thread_id: str = "thread-rollout") -> bytes:
    records = (
        _envelope("session_meta", {"id": thread_id}),
        _envelope(
            "response_item",
            {"type": "message", "role": "user", "content": "raw"},
        ),
    )
    native = (
        "\n".join(json.dumps(item, separators=(",", ":")) for item in records) + "\n"
    ).encode()
    path.write_bytes(native)
    return native


def _resolved(provider: CodexRolloutProvider, source: Path):
    return provider.resolve(
        ProviderContext(home=source.parent),
        ThreadSelection(source=source),
    )


def test_capture_and_projection_share_one_native_frame_identity(
    tmp_path: Path,
) -> None:
    provider = CodexRolloutProvider()
    source = tmp_path / "rollout.jsonl"
    native_bytes = _source(source)
    resolved = _resolved(provider, source)
    native = BytesIO()
    capture = provider.capture_native(resolved, native, {})

    records: list[dict[str, object]] = []
    result = provider.stream_normalize_captured(
        resolved,
        native,
        capture,
        lambda record: records.append(dict(record)) or True,
        {},
    )
    evidence = write_agent_thread_evidence(
        provider,
        ProviderContext(home=tmp_path),
        ThreadSelection(source=source),
        tmp_path / "evidence.zip",
    )

    assert native.getvalue() == evidence.native == native_bytes
    assert [frame["native_record_id"] for frame in capture.frames] == [
        "n000000",
        "n000001",
    ]
    assert [record["type"] for record in records] == ["meta", "message"]
    source_ref = records[1]["source_ref"]
    assert isinstance(source_ref, Mapping)
    assert source_ref["native_record_id"] == "n000001"
    assert result.result_status.value == "ready"
    assert evidence.trajectory is not None
    assert [record.type for record in evidence.trajectory.records] == [
        "meta",
        "message",
    ]


def test_source_bound_retains_an_explicit_partial_core(tmp_path: Path) -> None:
    provider = CodexRolloutProvider()
    source = tmp_path / "rollout.jsonl"
    source_bytes = _source(source)
    resolved = _resolved(provider, source)
    limit = source_bytes.find(b"\n") + 13
    native = BytesIO()
    capture = provider.capture_native(
        resolved,
        native,
        {"source_bytes": limit},
    )
    records: list[dict[str, object]] = []
    result = provider.stream_normalize_captured(
        resolved,
        native,
        capture,
        lambda record: records.append(dict(record)) or True,
        {"source_bytes": limit},
    )

    assert native.getvalue() == source_bytes[:limit]
    assert capture.is_partial and capture.unknown_remainder
    assert capture.frames[-1]["frame_status"] == "incomplete"
    assert [record["type"] for record in records] == ["meta"]
    assert result.result_status.value == "partial"
    assert result.lossiness == {
        "dropped_records": 0,
        "unavailable_records": 1,
        "synthesized_records": 0,
        "partial_frames": 1,
    }


def test_resolution_rejects_conflicting_or_missing_selection(tmp_path: Path) -> None:
    provider = CodexRolloutProvider()
    conflict = tmp_path / "conflict.jsonl"
    conflict.write_text(
        json.dumps(_envelope("session_meta", {"id": "one"}))
        + "\n"
        + json.dumps(_envelope("session_meta", {"id": "two"}))
        + "\n",
        encoding="utf-8",
    )
    resolved = _resolved(provider, conflict)
    native = BytesIO()
    capture = provider.capture_native(resolved, native, {})
    with pytest.raises(SvcError) as raised:
        provider.stream_normalize_captured(
            resolved,
            native,
            capture,
            lambda _record: True,
            {},
        )
    assert raised.value.code == "thread-source-incompatible"

    selected = tmp_path / "selected.jsonl"
    _source(selected, "actual-thread")
    with sqlite3.connect(tmp_path / "state_5.sqlite") as database:
        database.execute("CREATE TABLE threads (id TEXT, rollout_path TEXT)")
        database.execute(
            "INSERT INTO threads VALUES (?, ?)",
            ("selected-thread", selected.name),
        )
    with pytest.raises(SvcError) as raised:
        provider.resolve(
            ProviderContext(home=tmp_path),
            ThreadSelection(thread_id="selected-thread"),
        )
    assert raised.value.code == "thread-source-incompatible"

    with pytest.raises(SvcError) as raised:
        _resolved(provider, tmp_path / "missing.jsonl")
    assert raised.value.code == "thread-source-not-found"
