from __future__ import annotations

from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from pydantic import ValidationError

from svc_cli.analysis.models_v3 import QUERY_REQUEST_V3, query_request_schema_v3
from svc_cli.analysis.protocol import AnalysisProtocolError
from svc_cli.analysis.versions import validate_analysis_versions
from svc_cli.telemetry.evidence_v4 import (
    build_evidence_v4_manifest,
    write_evidence_v4_stream,
)
from svc_cli.telemetry.trajectory_v2 import (
    Coverage,
    ExecutionRecord,
    HeaderRecord,
    SourceRef,
    encode_trajectory_v2,
)


EVIDENCE_ID = "a" * 64


def test_v3_requests_are_constructible_from_generated_schema_contract() -> None:
    overview = QUERY_REQUEST_V3.validate_python({"version": 3, "intent": "overview"})
    trace = QUERY_REQUEST_V3.validate_python(
        {
            "version": 3,
            "intent": "trace",
            "execution": {
                "evidence_id": EVIDENCE_ID,
                "kind": "execution",
                "id": "exec_root",
            },
            "scope": {
                "history": "path",
                "leaf": {"evidence_id": EVIDENCE_ID, "kind": "event", "id": "evt_leaf"},
            },
        }
    )
    assert overview.intent == "overview"
    assert trace.scope.history == "path"  # type: ignore[union-attr]
    assert query_request_schema_v3()["$schema"].endswith("2020-12/schema")
    validator = Draft202012Validator(query_request_schema_v3())
    assert not list(validator.iter_errors(trace.model_dump(mode="json")))
    assert list(validator.iter_errors({"version": 3, "intent": "trace"}))
    wrong_kind = trace.model_dump(mode="json")
    wrong_kind["execution"]["kind"] = "event"
    assert list(validator.iter_errors(wrong_kind))


def test_v3_requests_reject_implicit_active_path_and_open_ended_profile_dsl() -> None:
    with pytest.raises(ValidationError):
        QUERY_REQUEST_V3.validate_python(
            {
                "version": 3,
                "intent": "trace",
                "turn_id": "turn-1",
                "scope": {"history": "active"},
            }
        )
    with pytest.raises(ValidationError):
        QUERY_REQUEST_V3.validate_python(
            {"version": 3, "intent": "profile", "breakdown": "anything"}
        )


def _write_v4(path: Path) -> None:
    native = b"{}\n"
    source = SourceRef(material="native/root.jsonl", line=0)
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
    materials = {"native/root.jsonl": native}
    manifest = build_evidence_v4_manifest(
        provider_id="test",
        source_format="jsonl-v1",
        selected_roots=("root",),
        trajectory=trajectory,
        materials=materials,
    )
    with path.open("w+b") as stream:
        write_evidence_v4_stream(stream, manifest, trajectory, materials)


def test_current_router_accepts_v3_and_rejects_v2_early(tmp_path: Path) -> None:
    bundle = tmp_path / "v4.zip"
    _write_v4(bundle)
    validate_analysis_versions({"version": 3, "intent": "overview"}, bundle)
    validate_analysis_versions({"intent": "overview"}, bundle)
    with pytest.raises(AnalysisProtocolError) as raised:
        validate_analysis_versions({"version": 2, "intent": "overview"}, bundle)
    assert raised.value.code == "unsupported-analysis-version"
