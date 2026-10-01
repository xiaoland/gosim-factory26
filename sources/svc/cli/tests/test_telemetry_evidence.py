from __future__ import annotations

import json
from pathlib import Path
import zipfile

import pytest

from svc_cli.telemetry.evidence import (
    EVIDENCE_MEMBERS,
    EVIDENCE_OPTIONAL_MEMBERS,
    EvidenceError,
    build_evidence_id,
    build_evidence_manifest,
    build_native_index,
    validate_evidence,
    validate_evidence_members,
    write_evidence_stream,
)
from svc_cli.telemetry.trajectory import canonical_json_bytes


def _source(thread_id: str = "thread-native") -> dict[str, object]:
    return {
        "provider_id": "codex",
        "adapter_id": "codex-rollout-v1",
        "source_format": "rollout-v1",
        "thread_id": thread_id,
        "source_status": "stable",
    }


def _capture() -> dict[str, object]:
    return {
        "status": "complete",
        "unknown_remainder": False,
        "read_interrupted": False,
    }


def _trajectory() -> bytes:
    records = (
        {
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
            "thread_ref": "thread_" + "a" * 64,
            "workspace": {
                "status": "missing",
                "flavor": None,
                "label": None,
                "ref": None,
            },
            "result_status": "ready",
            "capabilities": {
                "reasoning": "absent",
                "tool_linkage": "absent",
                "context": "absent",
                "task_references": "available",
                "explicit_concurrency": "unavailable",
                "timestamps": "full",
                "terminal_events": "unavailable",
            },
            "lossiness": {},
        },
        {
            "type": "message",
            "record_id": "r000001",
            "record_index": 1,
            "timestamp": "2026-01-01T00:00:01Z",
            "source_ref": {
                "event_index": 1,
                "line": 1,
                "byte_offset": 5,
                "native_record_id": "n000001",
            },
            "relationships": {},
            "role": "user",
            "task_refs": [],
        },
    )
    return b"".join(canonical_json_bytes(record, newline=True) for record in records)


def _fixture():
    native = b"meta\nmessage\n"
    index = build_native_index(
        native,
        [
            (0, 5, {"event_index": 0, "line": 0, "byte_offset": 0}, "complete"),
            (
                5,
                len(native),
                {"event_index": 1, "line": 1, "byte_offset": 5},
                "complete",
            ),
        ],
    )
    manifest = build_evidence_manifest(
        native=native,
        native_index=index,
        source=_source(),
        capture=_capture(),
    )
    return manifest, native, index, _trajectory()


def test_three_member_core_round_trips_with_one_raw_identity(tmp_path: Path) -> None:
    manifest, native, index, _ = _fixture()
    target = tmp_path / "core.zip"
    with target.open("x+b") as stream:
        written = write_evidence_stream(stream, manifest, native, index)
    loaded = validate_evidence(target)

    assert written.evidence_id == loaded.evidence_id == build_evidence_id(native, index)
    assert loaded.native == native
    assert loaded.native_index_bytes == index
    assert [entry.native_index for entry in loaded.native_index] == [0, 1]
    assert set(manifest.model_dump()) == {
        "format",
        "schema_version",
        "evidence_id",
        "source",
        "capture",
    }
    assert (
        build_evidence_manifest(
            native=native,
            native_index=index,
            source=_source("other-thread"),
            capture=_capture(),
        ).evidence_id
        == manifest.evidence_id
    )
    assert build_evidence_id(native + b"x", index) != manifest.evidence_id
    with zipfile.ZipFile(target) as archive:
        assert tuple(archive.namelist()) == EVIDENCE_MEMBERS


def test_cache_is_optional_and_bundle_json_is_semantic(tmp_path: Path) -> None:
    manifest, native, index, trajectory = _fixture()
    valid = validate_evidence_members(manifest, native, index, trajectory)
    invalid = validate_evidence_members(manifest, native, index, b"bad\n")
    assert valid.trajectory is not None
    assert invalid.trajectory is None
    assert valid.evidence_id == invalid.evidence_id

    entries = [json.loads(line) for line in index.splitlines()]
    ordinary_index = b"\r\n".join(
        json.dumps(entry, ensure_ascii=False).encode() for entry in entries
    )
    ordinary_manifest = build_evidence_manifest(
        native=native,
        native_index=ordinary_index,
        source=_source(),
        capture=_capture(),
    )
    manifest_json = json.dumps(ordinary_manifest.model_dump(mode="json"), indent=2)
    duplicate_json = ('{"schema_version":NaN,' + manifest_json[1:]).encode()
    target = tmp_path / "semantic.zip"
    with zipfile.ZipFile(target, "w") as archive:
        archive.writestr("native-index.jsonl", ordinary_index)
        archive.writestr("manifest.json", duplicate_json)
        archive.writestr("native.bin", native)
        archive.writestr("trajectory.jsonl", b"invalid cache\n")

    loaded = validate_evidence(target)
    assert loaded.evidence_id == build_evidence_id(native, ordinary_index)
    assert loaded.trajectory is None
    with zipfile.ZipFile(target) as archive:
        assert set(archive.namelist()) == set(
            EVIDENCE_MEMBERS + EVIDENCE_OPTIONAL_MEMBERS
        )


def test_index_rejects_gaps_and_nonfinal_incomplete_frames() -> None:
    native = b"one\ntwo\n"
    cases = (
        (
            (0, 4, {"event_index": 0, "line": 0, "byte_offset": 0}, "complete"),
            (5, 8, {"event_index": 1, "line": 1, "byte_offset": 5}, "complete"),
        ),
        (
            (0, 4, {"event_index": 0, "line": 0, "byte_offset": 0}, "incomplete"),
            (4, 8, {"event_index": 1, "line": 1, "byte_offset": 4}, "complete"),
        ),
    )
    for frames in cases:
        with pytest.raises(EvidenceError) as raised:
            build_native_index(native, frames)
        assert raised.value.code == "invalid-native-index"


@pytest.mark.filterwarnings("ignore:Duplicate name:UserWarning")
def test_bundle_rejects_wrong_members_and_historical_schemas(tmp_path: Path) -> None:
    manifest, native, index, _ = _fixture()
    values = {
        "manifest.json": canonical_json_bytes(manifest.model_dump(mode="json")),
        "native.bin": native,
        "native-index.jsonl": index,
        "notes.txt": b"extra",
    }
    for name, members, code in (
        ("missing", ("manifest.json", "native.bin"), "bundle-invalid"),
        ("duplicate", (*EVIDENCE_MEMBERS, "native.bin"), "bundle-invalid"),
        ("extra", (*EVIDENCE_MEMBERS, "notes.txt"), "bundle-invalid"),
        ("v2", ("manifest.json",), "unsupported-agent-thread-bundle-schema"),
    ):
        target = tmp_path / f"{name}.zip"
        with zipfile.ZipFile(target, "w") as archive:
            for member in members:
                value = values[member]
                if name == "v2":
                    value = b'{"schema_version":2}'
                archive.writestr(member, value)
        with pytest.raises(EvidenceError) as raised:
            validate_evidence(target)
        assert raised.value.code == code
