from __future__ import annotations

import json
from pathlib import Path


FIXTURES = Path(__file__).parent / "fixtures" / "analysis"


def _jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text().splitlines()]


def test_analysis_fixture_corpus_preserves_native_shapes_and_manual_oracle() -> None:
    root = _jsonl(FIXTURES / "codex" / "root.jsonl")
    child = _jsonl(FIXTURES / "codex" / "child.jsonl")
    pi = _jsonl(FIXTURES / "pi" / "session.jsonl")
    fork = _jsonl(FIXTURES / "pi" / "fork.jsonl")
    oracle = json.loads((FIXTURES / "oracle.json").read_text())

    assert root[0]["payload"]["id"] == "root"  # type: ignore[index]
    assert child[0]["payload"]["parent_thread_id"] == "root"  # type: ignore[index]
    assert (
        sum(
            item["message"]["usage"]["input"]
            for item in pi
            if item["type"] == "message" and item["message"]["role"] == "assistant"
        )
        == 100
    )  # type: ignore[index]
    assert fork[0]["parentSession"] == "session.jsonl"
    assert oracle["codex"]["usage"]["root"]["total"] == 180
    assert oracle["pi"]["all_work_usage"]["input"] == 114
    assert oracle["pi"]["active_path_usage"]["input"] == 94
