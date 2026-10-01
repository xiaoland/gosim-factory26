from __future__ import annotations

import json
from pathlib import Path

import pytest

from svc_cli.upgrade import plan_upgrade
from svc_cli.release import catalog


def write_project(root: Path, baseline: str = "15.0.0") -> None:
    (root / "svc.json").write_text(
        json.dumps({"schema_version": 3, "corpus_version": baseline}),
        encoding="utf-8",
    )


def test_current_corpus_baseline_requires_no_upgrade(tmp_path: Path) -> None:
    available = catalog().corpus_version
    write_project(tmp_path, available)

    plan = plan_upgrade(tmp_path)

    assert plan.status == "noop"
    assert plan.corpus.project_version == available
    assert plan.corpus.available_version == available


@pytest.mark.parametrize("schema", [1, 2, 4])
def test_historical_configuration_schemas_are_hard_cut_off(
    tmp_path: Path, schema: int
) -> None:
    (tmp_path / "svc.json").write_text(
        json.dumps({"schema_version": schema, "corpus_version": "15.0.0"}),
        encoding="utf-8",
    )

    plan = plan_upgrade(tmp_path)

    assert plan.status == "blocked"
    assert plan.blockers[0].code == "invalid-project-configuration"
    assert f"Unsupported svc.json schema: {schema}" in plan.blockers[0].message


@pytest.mark.parametrize("baseline", ["9.0.0", "14.0.0", "14.1.0", "15.0.1"])
def test_pre_v15_corpus_baselines_are_hard_cut_off(
    tmp_path: Path, baseline: str
) -> None:
    write_project(tmp_path, baseline)

    plan = plan_upgrade(tmp_path)

    assert plan.status == "blocked"
    assert plan.blockers[0].code == "unsupported-corpus-baseline"
    assert plan.mutations == ()
