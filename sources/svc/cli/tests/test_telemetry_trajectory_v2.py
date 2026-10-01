from __future__ import annotations

import pytest

from svc_cli.telemetry.trajectory import TrajectoryError, canonical_json_bytes
from svc_cli.telemetry.trajectory_v2 import (
    Coverage,
    CoverageIssue,
    ExecutionRecord,
    HeaderRecord,
    SourceRef,
    UsageEvent,
    UsageMeasurement,
    UsageOwner,
    UsagePayload,
    encode_trajectory_v2,
    trajectory_v2_schema,
    validate_trajectory_v2,
)


def _records() -> tuple[object, ...]:
    source = SourceRef(material="native/root.jsonl", line=0)
    return (
        HeaderRecord(
            type="header",
            trajectory_schema="svc.trajectory/v2",
            provider_id="codex",
            source_format="rollout-v1",
            normalizer="codex.rollout/v2",
            roots=("exec_root",),
            coverage=(
                Coverage(domain="relation_mapping", status="complete"),
                Coverage(
                    domain="descendant_closure",
                    status="partial",
                    issue_ids=("missing-child",),
                ),
            ),
            issues=(
                CoverageIssue(
                    issue_id="missing-child",
                    code="missing-execution-material",
                    message="One delegated child was not captured.",
                ),
            ),
        ),
        ExecutionRecord(
            type="execution",
            execution_id="exec_root",
            role="root",
            source_refs=(source,),
        ),
        UsageEvent(
            type="event",
            kind="usage",
            event_id="evt_usage",
            seq=0,
            execution_id="exec_root",
            source_refs=(source,),
            mapping="explicit",
            payload=UsagePayload(
                owner=UsageOwner(type="execution", id="exec_root"),
                scope="self",
                temporality="cumulative",
                counter_id="turn-root",
                zero_baseline=True,
                source="provider_reported",
                measurements=(
                    UsageMeasurement(
                        metric="input",
                        value=100,
                        unit="tokens",
                        inclusion="standalone",
                    ),
                    UsageMeasurement(
                        metric="cache_read",
                        value=20,
                        unit="tokens",
                        inclusion="included_in",
                        related_metric="input",
                    ),
                ),
            ),
        ),
    )


def test_v2_round_trip_keeps_payload_usage_and_scope_aware_coverage() -> None:
    data = encode_trajectory_v2(_records())  # type: ignore[arg-type]
    trajectory = validate_trajectory_v2(data)

    assert trajectory.header.trajectory_schema == "svc.trajectory/v2"
    assert trajectory.header.coverage[0].domain == "relation_mapping"
    assert trajectory.header.coverage[1].domain == "descendant_closure"
    assert trajectory.events[0].payload.measurements[1].related_metric == "input"  # type: ignore[union-attr]
    assert trajectory_v2_schema()["$schema"].endswith("2020-12/schema")


def test_v2_rejects_unresolved_execution_and_invalid_usage_semantics() -> None:
    records = list(_records())
    value = records[-1].model_dump(mode="json")  # type: ignore[union-attr]
    value["execution_id"] = "exec_missing"
    data = b"".join(
        canonical_json_bytes(item if index < 2 else value, newline=True)
        for index, item in enumerate(records)
    )
    with pytest.raises(TrajectoryError, match="does not resolve"):
        validate_trajectory_v2(data)

    with pytest.raises(ValueError, match="requires counter_id"):
        UsagePayload(
            owner=UsageOwner(type="unknown"),
            scope="unknown",
            temporality="cumulative",
            source="provider_reported",
            measurements=(
                UsageMeasurement(
                    metric="input",
                    value=1,
                    unit="tokens",
                    inclusion="unknown",
                ),
            ),
        )
