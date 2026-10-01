from __future__ import annotations

from io import BytesIO
import json

import pytest

from svc_cli.telemetry.trajectory import (
    MessageRecord,
    MetaRecord,
    TrajectoryCollector,
    TrajectoryError,
    attach_projection_summary,
    projection_summary,
    validate_trajectory_bytes,
)


def _ref(kind: str) -> str:
    return f"{kind}_{'a' * 64}"


def _capabilities() -> dict[str, str]:
    return {
        "reasoning": "absent",
        "tool_linkage": "absent",
        "context": "absent",
        "task_references": "available",
        "explicit_concurrency": "unavailable",
        "timestamps": "full",
        "terminal_events": "unavailable",
    }


def _lossiness() -> dict[str, int]:
    return {
        "dropped_records": 0,
        "unavailable_records": 0,
        "synthesized_records": 0,
        "partial_frames": 0,
    }


def _meta() -> dict[str, object]:
    return {
        "type": "meta",
        "record_id": "r000000",
        "record_index": 0,
        "timestamp": None,
        "source_ref": {"event_index": None, "component": "meta"},
        "relationships": {},
        "trajectory_schema": "svc.trajectory/v1",
        "provider_id": "codex",
        "adapter_id": "codex-rollout-v1",
        "source_format": "rollout-v1",
        "thread_ref": _ref("thread"),
        "workspace": {
            "status": "missing",
            "flavor": None,
            "label": None,
            "ref": None,
        },
    }


def _message(index: int = 1) -> dict[str, object]:
    return {
        "type": "message",
        "record_id": f"r{index:06d}",
        "record_index": index,
        "timestamp": "2026-01-01T00:00:01Z",
        "source_ref": {
            "event_index": index,
            "line": index,
            "native_record_id": f"n{index:06d}",
        },
        "relationships": {"turn_ref": _ref("turn")},
        "role": "user",
        "task_refs": ["tasks/example/packet.md"],
    }


def _pending_trajectory() -> bytes:
    collector = TrajectoryCollector()
    assert collector.emit(_meta())
    assert collector.emit(_message())
    value = collector.finish()
    assert isinstance(value, bytes)
    return value


def _trajectory() -> bytes:
    return attach_projection_summary(
        _pending_trajectory(),
        result_status="ready",
        capabilities=_capabilities(),
        lossiness=_lossiness(),
    )


def test_collector_writes_only_typed_sequence_invariants() -> None:
    output = BytesIO()
    collector = TrajectoryCollector(output)
    assert collector.emit(_meta())
    assert collector.emit(_message())
    assert collector.finish() is None

    assert output.getvalue() == _pending_trajectory()
    with pytest.raises(TrajectoryError, match="already finished"):
        collector.emit(_message(2))


def test_summary_is_attached_to_meta_and_projects_json_ready_source() -> None:
    pending = _pending_trajectory()
    with pytest.raises(TrajectoryError, match="missing its projection summary"):
        validate_trajectory_bytes(pending)

    final = attach_projection_summary(
        pending,
        result_status="ready",
        capabilities=_capabilities(),
        lossiness=_lossiness(),
    )
    validated = validate_trajectory_bytes(final)

    assert isinstance(validated.records[0], MetaRecord)
    assert isinstance(validated.records[1], MessageRecord)
    assert validated.records[1].task_refs == ("tasks/example/packet.md",)
    assert projection_summary(validated) == {
        "source": {
            "provider_id": "codex",
            "adapter_id": "codex-rollout-v1",
            "source_format": "rollout-v1",
            "thread_ref": _ref("thread"),
            "workspace": {
                "status": "missing",
                "flavor": None,
                "label": None,
                "ref": None,
            },
        },
        "result_status": "ready",
        "capabilities": _capabilities(),
        "lossiness": _lossiness(),
    }


def test_validator_accepts_equivalent_noncanonical_json() -> None:
    canonical = _trajectory()
    values = [json.loads(line) for line in canonical.splitlines()]
    noncanonical = b"".join(
        (
            json.dumps(
                dict(reversed(list(value.items()))),
                ensure_ascii=False,
            ).encode("utf-8")
            + b"\n"
        )
        for value in values
    )

    validated = validate_trajectory_bytes(noncanonical)

    assert validated.trajectory_bytes == noncanonical
    assert [record.type for record in validated.records] == ["meta", "message"]
    assert noncanonical != canonical


def test_sequence_rejects_nonleading_meta_and_noncontiguous_ids() -> None:
    with pytest.raises(TrajectoryError):
        TrajectoryCollector().emit(_message(0))

    collector = TrajectoryCollector()
    assert collector.emit(_meta())
    with pytest.raises(TrajectoryError):
        collector.emit(_message(2))

    with pytest.raises(TrajectoryError):
        TrajectoryCollector().emit({**_meta(), "record_id": "r000001"})
