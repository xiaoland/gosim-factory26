"""Small builders for project configuration used across behavior tests."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path


CORPUS_VERSION = "14.0.0"


def write_project_config(
    root: Path,
    *,
    dev_targets: Mapping[str, object] | None = None,
    run_entries: Mapping[str, object] | None = None,
    corpus_version: str = CORPUS_VERSION,
) -> Path:
    document: dict[str, object] = {
        "schema_version": 3,
        "corpus_version": corpus_version,
    }
    if dev_targets is not None:
        document["dev"] = {"targets": dict(dev_targets)}
    if run_entries is not None:
        document["run"] = dict(run_entries)
    path = root / "svc.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    return path


def write_local_run_overlay(root: Path, entries: Mapping[str, object]) -> Path:
    path = root / "svc.local.json"
    path.write_text(
        json.dumps({"schema_version": 3, "run": dict(entries)}),
        encoding="utf-8",
    )
    return path
