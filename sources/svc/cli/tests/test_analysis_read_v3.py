from __future__ import annotations

import base64
import json
from pathlib import Path

import pytest

from svc_cli.analysis.protocol import AnalysisProtocolError
from svc_cli.analysis.models_v3 import ReadResponseV3
from svc_cli.analysis.read_v3 import read_evidence_v3
from svc_cli.telemetry.evidence_v4 import (
    build_evidence_v4_manifest,
    validate_evidence_v4,
    write_evidence_v4_stream,
)
from svc_cli.telemetry.trajectory import canonical_json_bytes
from svc_cli.telemetry.trajectory_v2 import (
    Coverage,
    ExecutionRecord,
    HeaderRecord,
    SourceRef,
    encode_trajectory_v2,
)


def _evidence(tmp_path: Path, material: bytes):
    name = "native/root.jsonl"
    source = SourceRef(material=name, line=0)
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
        )
    )
    materials = {name: material}
    manifest = build_evidence_v4_manifest(
        provider_id="test",
        source_format="jsonl-v1",
        selected_roots=("root",),
        trajectory=trajectory,
        materials=materials,
    )
    path = tmp_path / "evidence.zip"
    with path.open("w+b") as output:
        write_evidence_v4_stream(output, manifest, trajectory, materials)
    return validate_evidence_v4(path), name


def _payload(item: dict[str, object]) -> bytes:
    payload = item["payload"]
    assert isinstance(payload, dict)
    if payload["encoding"] == "utf-8":
        return payload["text"].encode()  # type: ignore[union-attr]
    return base64.b64decode(payload["data"])  # type: ignore[arg-type]


def test_read_v3_pages_exact_binary_material_with_whole_response_budget(
    tmp_path: Path,
) -> None:
    original = ("你好" * 300).encode() + b"\xff\x00" + b"x" * 1200
    evidence, name = _evidence(tmp_path, original)
    request: dict[str, object] = {
        "version": 3,
        "ref": {"evidence_id": evidence.evidence_id, "kind": "native", "id": name},
        "max_bytes": 900,
    }
    recovered = bytearray()
    while True:
        response = read_evidence_v3(evidence, request)
        ReadResponseV3.model_validate_json(json.dumps(response))
        assert len(canonical_json_bytes(response)) <= 900
        recovered.extend(_payload(response["items"][0]))  # type: ignore[index]
        cursor = response["next_cursor"]
        if cursor is None:
            break
        request = {"version": 3, "cursor": cursor, "max_bytes": 900}
    assert bytes(recovered) == original


def test_read_v3_rejects_cross_evidence_ref(tmp_path: Path) -> None:
    evidence, name = _evidence(tmp_path, b"data")
    with pytest.raises(AnalysisProtocolError) as raised:
        read_evidence_v3(
            evidence,
            {
                "version": 3,
                "ref": {"evidence_id": "0" * 64, "kind": "native", "id": name},
            },
        )
    assert raised.value.code == "reference-scope-mismatch"
