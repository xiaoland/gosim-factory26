from __future__ import annotations

from pathlib import Path
import json
import shutil
import sqlite3

from svc_cli.telemetry.agent_threads import ProviderContext, ThreadSelection
from svc_cli.telemetry.providers.codex_v4 import collect_codex_v4


FIXTURES = Path(__file__).parent / "fixtures" / "analysis" / "codex"


def _home(tmp_path: Path) -> Path:
    home = tmp_path / "codex"
    home.mkdir()
    for name in ("root", "child"):
        shutil.copyfile(FIXTURES / f"{name}.jsonl", home / f"{name}.jsonl")
    with sqlite3.connect(home / "state_5.sqlite") as database:
        database.execute(
            "CREATE TABLE threads (id TEXT, rollout_path TEXT, parent_thread_id TEXT)"
        )
        database.executemany(
            "INSERT INTO threads VALUES (?, ?, ?)",
            (("root", "root.jsonl", None), ("child", "child.jsonl", "root")),
        )
    return home


def test_codex_v4_collects_descendants_payloads_relations_and_usage(
    tmp_path: Path,
) -> None:
    home = _home(tmp_path)
    manifest, trajectory_bytes, materials = collect_codex_v4(
        ProviderContext(home=home),
        ThreadSelection(thread_id="root"),
    )

    assert manifest.schema_version == 4
    assert len(materials) == 2
    assert len(trajectory_bytes) > 0
    # Inspect the typed result retained by the required trajectory contract.
    from svc_cli.telemetry.trajectory_v2 import validate_trajectory_v2

    trajectory = validate_trajectory_v2(trajectory_bytes)
    assert len(trajectory.executions) == 2
    assert {item.native_id for item in trajectory.executions} == {"root", "child"}
    assert any(
        item.kind == "relation" and item.payload.relation == "delegation"
        for item in trajectory.events
    )
    assert any(
        item.kind == "message"
        and item.payload.role == "user"
        and item.payload.content[0].text == "Inspect the failing tests"
        for item in trajectory.events
    )
    usage = [item for item in trajectory.events if item.kind == "usage"]
    assert len(usage) == 6
    assert {item.payload.temporality for item in usage} == {"cumulative", "delta"}
    assert all(item.source_refs[0].material in materials for item in trajectory.events)


def test_codex_v4_keeps_missing_child_in_topology_and_coverage(tmp_path: Path) -> None:
    home = _home(tmp_path)
    (home / "child.jsonl").unlink()

    manifest, trajectory_bytes, _ = collect_codex_v4(
        ProviderContext(home=home), ThreadSelection(thread_id="root")
    )
    from svc_cli.telemetry.trajectory_v2 import validate_trajectory_v2

    trajectory = validate_trajectory_v2(trajectory_bytes)
    assert len(trajectory.executions) == 2
    assert any(item.kind == "relation" for item in trajectory.events)
    assert {gap.object_id for gap in manifest.gaps} == {"child"}
    assert (
        next(
            item for item in trajectory.header.coverage if item.domain == "usage"
        ).status
        == "partial"
    )


def test_codex_v4_attaches_missing_grandchild_to_observed_parent(
    tmp_path: Path,
) -> None:
    home = _home(tmp_path)
    child = home / "child.jsonl"
    child.write_text(
        child.read_text()
        + '{"type":"response_item","payload":{"type":"function_call","name":"spawn_agent","call_id":"spawn-grand","arguments":"{}"}}\n'
        + '{"type":"response_item","payload":{"type":"function_call_output","call_id":"spawn-grand","output":"{\\"agent_id\\":\\"grand\\"}"}}\n'
    )

    _, trajectory_bytes, _ = collect_codex_v4(
        ProviderContext(home=home), ThreadSelection(thread_id="root")
    )
    from svc_cli.telemetry.trajectory_v2 import validate_trajectory_v2

    trajectory = validate_trajectory_v2(trajectory_bytes)
    by_native = {item.native_id: item.execution_id for item in trajectory.executions}
    relation = next(
        item
        for item in trajectory.events
        if item.kind == "relation" and item.payload.target.id == by_native["grand"]
    )
    assert relation.payload.source.id == by_native["child"]


def test_codex_v4_marks_replayed_legacy_usage_ambiguous_without_double_counting(
    tmp_path: Path,
) -> None:
    home = _home(tmp_path)
    root = home / "root.jsonl"
    records = root.read_text().splitlines()
    repeated = next(
        item
        for item in reversed(records)
        if (json.loads(item).get("payload") or {}).get("type") == "token_count"
    )
    root.write_text("\n".join([*records, repeated]) + "\n")

    _, trajectory_bytes, _ = collect_codex_v4(
        ProviderContext(home=home), ThreadSelection(thread_id="root")
    )
    from svc_cli.analysis.engine_v3 import usage_for_execution
    from svc_cli.telemetry.trajectory_v2 import validate_trajectory_v2

    trajectory = validate_trajectory_v2(trajectory_bytes)
    root_execution = next(
        item for item in trajectory.executions if item.native_id == "root"
    )
    usage = usage_for_execution(trajectory, root_execution.execution_id)
    assert next(item.value for item in usage.known if item.metric == "input") == 160
    assert usage.ambiguous_observations >= 1


def test_codex_v4_ignores_gaps_outside_selected_closure(tmp_path: Path) -> None:
    home = _home(tmp_path)
    root = home / "root.jsonl"
    root.write_text(
        root.read_text()
        + '{"type":"response_item","payload":{"type":"function_call","name":"spawn_agent","call_id":"unresolved","arguments":"{}"}}\n'
    )

    manifest, trajectory_bytes, _ = collect_codex_v4(
        ProviderContext(home=home), ThreadSelection(thread_id="child")
    )
    from svc_cli.telemetry.trajectory_v2 import validate_trajectory_v2

    trajectory = validate_trajectory_v2(trajectory_bytes)
    assert [item.native_id for item in trajectory.executions] == ["child"]
    assert manifest.gaps == ()
