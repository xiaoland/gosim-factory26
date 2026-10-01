"""Small public-boundary evidence corpus shared by analysis contract tests."""

from __future__ import annotations

import copy
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Mapping, Sequence

from svc_cli.telemetry.evidence import (
    build_evidence_manifest,
    build_native_index,
    write_evidence_stream,
)
from svc_cli.telemetry.trajectory import (
    attach_projection_summary,
    canonical_json_bytes,
)


THREAD_REF = "thread_" + "a" * 64


@dataclass(frozen=True, slots=True)
class EvidenceBundle:
    path: Path
    evidence_id: str
    native: bytes


def message_record(
    native_index: int,
    role: str,
    content: str,
) -> dict[str, object]:
    del content  # Text predicates read native authority, not projection content.
    return {
        "type": "message",
        "record_id": f"r{native_index:06d}",
        "record_index": native_index,
        "timestamp": f"2026-01-01T00:00:0{native_index}Z",
        "source_ref": {"event_index": native_index},
        "relationships": {},
        "role": role,
        "task_refs": [],
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
        "thread_ref": THREAD_REF,
        "workspace": {
            "status": "missing",
            "flavor": None,
            "label": None,
            "ref": None,
        },
    }


def write_evidence_bundle(
    directory: Path,
    name: str,
    frames: Sequence[bytes],
    *,
    records: Sequence[Mapping[str, object]] = (),
    projection_status: Literal["ready", "partial"] = "ready",
    incomplete_last: bool = False,
) -> EvidenceBundle:
    native = b"".join(frames)
    offsets: list[int] = []
    ranges: list[tuple[int, int, dict[str, int], str]] = []
    offset = 0
    for index, frame in enumerate(frames):
        offsets.append(offset)
        ranges.append(
            (
                offset,
                offset + len(frame),
                {"event_index": index, "line": index, "byte_offset": offset},
                (
                    "incomplete"
                    if incomplete_last and index == len(frames) - 1
                    else "complete"
                ),
            )
        )
        offset += len(frame)
    native_index = build_native_index(native, ranges)

    trajectory_records = [_meta()]
    for source in records:
        record = copy.deepcopy(dict(source))
        raw_source_ref = record["source_ref"]
        assert isinstance(raw_source_ref, Mapping)
        source_ref = dict(raw_source_ref)
        event_index = source_ref["event_index"]
        assert isinstance(event_index, int)
        source_ref.update(
            {
                "line": event_index,
                "byte_offset": offsets[event_index],
                "native_record_id": f"n{event_index:06d}",
            }
        )
        record["source_ref"] = source_ref
        trajectory_records.append(record)
    raw_trajectory = b"".join(
        canonical_json_bytes(record, newline=True) for record in trajectory_records
    )
    trajectory = attach_projection_summary(
        raw_trajectory,
        result_status=projection_status,
        capabilities={
            "reasoning": "absent",
            "tool_linkage": "absent",
            "context": "absent",
            "task_references": "available",
            "explicit_concurrency": "unavailable",
            "timestamps": "full" if records else "absent",
            "terminal_events": "unavailable",
        },
        lossiness={},
    )
    partial = incomplete_last and bool(frames)
    manifest = build_evidence_manifest(
        native=native,
        native_index=native_index,
        source={
            "provider_id": "codex",
            "adapter_id": "codex-rollout-v1",
            "source_format": "rollout-v1",
            "thread_id": "thread",
            "source_status": "stable",
        },
        capture={
            "status": "partial" if partial else "complete",
            "unknown_remainder": partial,
            "read_interrupted": False,
        },
    )
    target = directory / f"{name}.zip"
    with target.open("x+b") as stream:
        validated = write_evidence_stream(
            stream,
            manifest,
            native,
            native_index,
            trajectory,
        )
    return EvidenceBundle(target, validated.evidence_id, native)
