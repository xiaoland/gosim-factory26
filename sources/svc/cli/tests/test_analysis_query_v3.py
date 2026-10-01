from __future__ import annotations

import json
from pathlib import Path
import shutil
import sqlite3

from svc_cli.analysis.models_v3 import QUERY_RESPONSE_V3
from svc_cli.analysis.query_v3 import query_evidence_v3
from svc_cli.telemetry.agent_threads import ProviderContext, ThreadSelection
from svc_cli.telemetry.evidence_v4 import validate_evidence_v4_members
from svc_cli.telemetry.providers.codex_v4 import collect_codex_v4
from svc_cli.telemetry.providers.pi_v4 import collect_pi_v4


FIXTURES = Path(__file__).parent / "fixtures" / "analysis"


def _codex(tmp_path: Path):
    home = tmp_path / "codex"
    home.mkdir()
    for name in ("root", "child"):
        shutil.copyfile(FIXTURES / "codex" / f"{name}.jsonl", home / f"{name}.jsonl")
    with sqlite3.connect(home / "state_5.sqlite") as database:
        database.execute(
            "CREATE TABLE threads (id TEXT, rollout_path TEXT, parent_thread_id TEXT)"
        )
        database.executemany(
            "INSERT INTO threads VALUES (?, ?, ?)",
            (("root", "root.jsonl", None), ("child", "child.jsonl", "root")),
        )
    manifest, trajectory, materials = collect_codex_v4(
        ProviderContext(home=home), ThreadSelection(thread_id="root")
    )
    return validate_evidence_v4_members(manifest, trajectory, materials)


def _pi(tmp_path: Path):
    home = tmp_path / "pi"
    home.mkdir()
    shutil.copyfile(FIXTURES / "pi" / "session.jsonl", home / "session.jsonl")
    manifest, trajectory, materials = collect_pi_v4(
        ProviderContext(home=home), ThreadSelection(source=home / "session.jsonl")
    )
    return validate_evidence_v4_members(manifest, trajectory, materials)


def _metrics(value: dict[str, object]) -> dict[str, int | float]:
    return {item["metric"]: item["value"] for item in value["known"]}  # type: ignore[index,union-attr]


def test_overview_answers_codex_subagent_usage_without_native_replay(
    tmp_path: Path,
) -> None:
    evidence = _codex(tmp_path)
    overview = query_evidence_v3(evidence, {"version": 3, "intent": "overview"})
    oracle = json.loads((FIXTURES / "oracle.json").read_text())["codex"]

    assert len(overview["executions"]) == 2
    assert overview["relations"][0]["relation"] == "delegation"
    by_role = {item["role"]: item for item in overview["executions"]}
    child = _metrics(by_role["subagent"]["self_usage"])
    assert child["input"] == oracle["usage"]["child"]["input"]
    assert child["output"] == oracle["usage"]["child"]["output"]
    assert by_role["subagent"]["self_usage"]["unknown_observations"] == 0

    profile = query_evidence_v3(
        evidence,
        {
            "version": 3,
            "intent": "profile",
            "select": {"execution": by_role["subagent"]["ref"]},
            "breakdown": "execution",
        },
    )
    QUERY_RESPONSE_V3.validate_json(json.dumps(profile))
    assert _metrics(profile["total"])["total"] == 95


def test_pi_path_profile_excludes_abandoned_branch_and_match_cursor_is_stable(
    tmp_path: Path,
) -> None:
    evidence = _pi(tmp_path)
    trajectory = evidence.trajectory
    leaf = next(
        event
        for event in trajectory.events
        if event.source_refs[0].record_id == "a2" and event.kind == "message"
    )
    profile = query_evidence_v3(
        evidence,
        {
            "version": 3,
            "intent": "profile",
            "breakdown": "execution",
            "scope": {
                "history": "path",
                "leaf": {
                    "evidence_id": evidence.evidence_id,
                    "kind": "event",
                    "id": leaf.event_id,
                },
            },
        },
    )
    oracle = json.loads((FIXTURES / "oracle.json").read_text())["pi"]
    assert _metrics(profile["total"])["input"] == oracle["active_path_usage"]["input"]

    request = {
        "version": 3,
        "intent": "match",
        "predicates": {"kinds": ["message"]},
        "max_items": 1,
    }
    first = query_evidence_v3(evidence, request)
    second = query_evidence_v3(
        evidence,
        {
            "version": 3,
            "intent": "match",
            "cursor": first["next_cursor"],
            "max_items": 1,
        },
    )
    assert first["refs"] != second["refs"]


def test_large_payload_is_recoverable_by_public_blob_ref(tmp_path: Path) -> None:
    home = tmp_path / "large-pi"
    home.mkdir()
    source = home / "session.jsonl"
    lines = (FIXTURES / "pi" / "session.jsonl").read_text().splitlines()
    last = json.loads(lines[-1])
    last["message"]["content"][0]["text"] = "x" * 20_000
    lines[-1] = json.dumps(last)
    source.write_text("\n".join(lines) + "\n")
    manifest, trajectory, materials = collect_pi_v4(
        ProviderContext(home=home), ThreadSelection(source=source)
    )
    evidence = validate_evidence_v4_members(manifest, trajectory, materials)
    execution = evidence.trajectory.executions[0]
    trace = query_evidence_v3(
        evidence,
        {
            "version": 3,
            "intent": "trace",
            "execution": {
                "evidence_id": evidence.evidence_id,
                "kind": "execution",
                "id": execution.execution_id,
            },
        },
    )
    assert trace["content_refs"][0]["kind"] == "blob"


def test_event_trace_associates_tool_call_and_result(tmp_path: Path) -> None:
    evidence = _pi(tmp_path)
    call = next(
        event for event in evidence.trajectory.events if event.kind == "tool_call"
    )
    trace = query_evidence_v3(
        evidence,
        {
            "version": 3,
            "intent": "trace",
            "event": {
                "evidence_id": evidence.evidence_id,
                "kind": "event",
                "id": call.event_id,
            },
        },
    )
    assert {event["kind"] for event in trace["events"]} >= {"tool_call", "tool_result"}


def test_profile_breakdowns_are_paginated_with_bounded_cursor(tmp_path: Path) -> None:
    evidence = _codex(tmp_path)
    first = query_evidence_v3(
        evidence,
        {"version": 3, "intent": "profile", "breakdown": "execution", "max_items": 1},
    )
    assert first["next_cursor"] is not None
    assert len(first["next_cursor"]) < 8192
    second = query_evidence_v3(
        evidence,
        {
            "version": 3,
            "intent": "profile",
            "cursor": first["next_cursor"],
            "max_items": 1,
        },
    )
    assert second["total"] == first["total"]


def test_trace_cursor_keeps_selector_across_all_pages(tmp_path: Path) -> None:
    evidence = _pi(tmp_path)
    execution = evidence.trajectory.executions[0]
    request = {
        "version": 3,
        "intent": "trace",
        "execution": {
            "evidence_id": evidence.evidence_id,
            "kind": "execution",
            "id": execution.execution_id,
        },
        "max_items": 1,
    }
    seen = []
    while True:
        page = query_evidence_v3(evidence, request)
        seen.extend(page["events"])
        if page["next_cursor"] is None:
            break
        request = {
            "version": 3,
            "intent": "trace",
            "cursor": page["next_cursor"],
            "max_items": 1,
        }
    assert len(seen) == len(
        [
            event
            for event in evidence.trajectory.events
            if event.execution_id == execution.execution_id
        ]
    )


def test_empty_trace_and_match_are_normal_results(tmp_path: Path) -> None:
    evidence = _pi(tmp_path)
    trace = query_evidence_v3(
        evidence, {"version": 3, "intent": "trace", "turn_id": "absent"}
    )
    match = query_evidence_v3(
        evidence,
        {
            "version": 3,
            "intent": "match",
            "predicates": {"text_terms": ["never-present"]},
        },
    )
    assert trace["events"] == []
    assert match["refs"] == []
