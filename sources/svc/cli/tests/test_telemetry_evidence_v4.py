from __future__ import annotations

from io import BytesIO
import json
from pathlib import Path
import zipfile

import pytest

from svc_cli.telemetry.evidence import EvidenceError
from svc_cli.telemetry.evidence_v4 import (
    build_evidence_v4_manifest,
    validate_evidence_v4,
    write_evidence_v4_stream,
)
from svc_cli.telemetry.trajectory_v2 import (
    Coverage,
    ExecutionRecord,
    HeaderRecord,
    MessageEvent,
    MessagePayload,
    SourceRef,
    TextContent,
    encode_trajectory_v2,
)


def _bundle(
    material: bytes = b'{"message":"hello"}\n',
) -> tuple[object, bytes, dict[str, bytes]]:
    material_name = "native/root.jsonl"
    source = SourceRef(
        material=material_name, line=0, byte_start=0, byte_end=len(material)
    )
    trajectory = encode_trajectory_v2(
        (
            HeaderRecord(
                type="header",
                trajectory_schema="svc.trajectory/v2",
                provider_id="test",
                source_format="jsonl-v1",
                normalizer="test/v1",
                roots=("exec_root",),
                coverage=(Coverage(domain="content", status="complete"),),
            ),
            ExecutionRecord(
                type="execution",
                execution_id="exec_root",
                role="root",
                source_refs=(source,),
            ),
            MessageEvent(
                type="event",
                kind="message",
                event_id="evt_message",
                seq=0,
                execution_id="exec_root",
                source_refs=(source,),
                mapping="explicit",
                payload=MessagePayload(
                    role="user",
                    content=(TextContent(type="text", text="hello"),),
                ),
            ),
        )
    )
    materials = {material_name: material}
    manifest = build_evidence_v4_manifest(
        provider_id="test",
        source_format="jsonl-v1",
        selected_roots=("root",),
        trajectory=trajectory,
        materials=materials,
        material_media_types={material_name: "application/x-ndjson"},
    )
    return manifest, trajectory, materials


def test_v4_round_trip_requires_and_binds_trajectory_and_materials(
    tmp_path: Path,
) -> None:
    manifest, trajectory, materials = _bundle()
    output = tmp_path / "evidence.zip"
    with output.open("w+b") as stream:
        written = write_evidence_v4_stream(stream, manifest, trajectory, materials)  # type: ignore[arg-type]

    loaded = validate_evidence_v4(output)
    assert loaded.evidence_id == written.evidence_id
    assert loaded.trajectory.events[0].payload.content[0].text == "hello"  # type: ignore[union-attr]
    assert loaded.materials["native/root.jsonl"] == materials["native/root.jsonl"]


def test_v4_rejects_trajectory_or_material_tampering(tmp_path: Path) -> None:
    manifest, trajectory, materials = _bundle()
    original = BytesIO()
    write_evidence_v4_stream(original, manifest, trajectory, materials)  # type: ignore[arg-type]

    for member in ("trajectory.jsonl", "native/root.jsonl"):
        target = tmp_path / f"tampered-{member.replace('/', '-')}.zip"
        with (
            zipfile.ZipFile(BytesIO(original.getvalue())) as source,
            zipfile.ZipFile(target, "w") as output,
        ):
            for info in source.infolist():
                value = source.read(info.filename)
                output.writestr(
                    info.filename, value + b"x" if info.filename == member else value
                )
        with pytest.raises(EvidenceError, match="integrity|invalid"):
            validate_evidence_v4(target)


def test_v4_rejects_undeclared_members(tmp_path: Path) -> None:
    manifest, trajectory, materials = _bundle()
    output = tmp_path / "extra.zip"
    with zipfile.ZipFile(output, "w") as archive:
        archive.writestr("manifest.json", json.dumps(manifest.model_dump(mode="json")))  # type: ignore[union-attr]
        archive.writestr("trajectory.jsonl", trajectory)
        archive.writestr("native/root.jsonl", materials["native/root.jsonl"])
        archive.writestr("surprise.txt", "no")
    with pytest.raises(EvidenceError, match="undeclared"):
        validate_evidence_v4(output)
