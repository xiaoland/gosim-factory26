from __future__ import annotations

import json
from pathlib import Path
import shutil

from svc_cli.telemetry.agent_threads import ProviderContext, ThreadSelection
from svc_cli.telemetry.providers.pi_v4 import collect_pi_v4
from svc_cli.telemetry.trajectory_v2 import validate_trajectory_v2
from svc_cli.analysis.engine_v3 import usage_for_execution


FIXTURES = Path(__file__).parent / "fixtures" / "analysis"


def test_pi_v4_preserves_tree_branch_compaction_usage_and_fork_history(
    tmp_path: Path,
) -> None:
    home = tmp_path / "pi"
    home.mkdir()
    session = home / "session.jsonl"
    fork = home / "fork.jsonl"
    shutil.copyfile(FIXTURES / "pi" / "session.jsonl", session)
    shutil.copyfile(FIXTURES / "pi" / "fork.jsonl", fork)

    manifest, trajectory_bytes, materials = collect_pi_v4(
        ProviderContext(home=home),
        ThreadSelection(source=fork),
    )
    trajectory = validate_trajectory_v2(trajectory_bytes)
    oracle = json.loads((FIXTURES / "oracle.json").read_text())["pi"]

    assert manifest.provider_id == "pi"
    assert len(materials) == 2
    assert {item.native_id for item in trajectory.executions} == {"pi-root", "pi-fork"}
    assert any(
        item.kind == "relation" and item.payload.relation == oracle["fork_relation"]
        for item in trajectory.events
    )
    by_native_id = {}
    for item in trajectory.events:
        native_id = item.source_refs[0].record_id
        if native_id is not None:
            by_native_id.setdefault(native_id, item)
    assert by_native_id["a2"].predecessor_ids
    assert by_native_id["a-old"].event_id not in by_native_id["b1"].predecessor_ids
    assert any(
        item.kind == "context_change" and item.payload.operation == "compact"
        for item in trajectory.events
    )
    assert len([item for item in trajectory.events if item.kind == "usage"]) == 6


def test_pi_v4_does_not_charge_copied_fork_history_twice(tmp_path: Path) -> None:
    home = tmp_path / "pi"
    home.mkdir()
    session = home / "session.jsonl"
    fork = home / "fork.jsonl"
    shutil.copyfile(FIXTURES / "pi" / "session.jsonl", session)
    fork_lines = (FIXTURES / "pi" / "fork.jsonl").read_text().splitlines()
    copied = next(
        line
        for line in (FIXTURES / "pi" / "session.jsonl").read_text().splitlines()
        if json.loads(line).get("id") == "a2"
    )
    fork_user = json.loads(fork_lines[1])
    fork_user["parentId"] = "a2"
    fork.write_text(
        "\n".join([fork_lines[0], copied, json.dumps(fork_user), *fork_lines[2:]])
        + "\n"
    )

    _, trajectory_bytes, _ = collect_pi_v4(
        ProviderContext(home=home), ThreadSelection(source=fork)
    )
    trajectory = validate_trajectory_v2(trajectory_bytes)
    fork_execution = next(
        item for item in trajectory.executions if item.native_id == "pi-fork"
    )
    usage = usage_for_execution(trajectory, fork_execution.execution_id)
    assert next(item.value for item in usage.known if item.metric == "input") == 12
    fork_user_event = next(
        item for item in trajectory.events if item.source_refs[0].record_id == "fu1"
    )
    copied_event = next(
        item
        for item in trajectory.events
        if item.source_refs[0].record_id == "a2" and item.kind == "message"
    )
    assert fork_user_event.predecessor_ids == (copied_event.event_id,)
