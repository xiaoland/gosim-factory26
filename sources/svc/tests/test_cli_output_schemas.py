from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

import tools.build_cli_output_schemas as schemas


def _git(root: Path, *args: str) -> None:
    subprocess.run(("git", *args), cwd=root, check=True, capture_output=True)


def test_schema_comparison_reads_the_pre_rename_layout(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    old = tmp_path / "svc_cli/src/svc_cli/data/output-schemas"
    old.mkdir(parents=True)
    (old / "example.json").write_text(
        json.dumps({"x-svc-result-schema-version": 1, "type": "string"}),
        encoding="utf-8",
    )
    (tmp_path / "svc_cli/pyproject.toml").write_text(
        '[project]\nversion = "15.0.0"\n', encoding="utf-8"
    )
    current = tmp_path / "cli"
    current.mkdir()
    (current / "pyproject.toml").write_text(
        '[project]\nversion = "15.0.0"\n', encoding="utf-8"
    )
    _git(tmp_path, "init")
    _git(tmp_path, "add", "svc_cli")
    _git(
        tmp_path,
        "-c",
        "user.name=SVC Test",
        "-c",
        "user.email=svc@example.invalid",
        "commit",
        "-m",
        "baseline",
    )
    monkeypatch.setattr(schemas, "ROOT", tmp_path)
    monkeypatch.setattr(schemas, "OUTPUT_SCHEMA_KEYS", ("example",))
    monkeypatch.setattr(
        schemas,
        "generate_output_schema",
        lambda key: {"x-svc-result-schema-version": 1, "type": "integer"},
    )

    assert schemas.compare_ref("HEAD") == [
        "example output changed without advancing x-svc-result-schema-version"
    ]
