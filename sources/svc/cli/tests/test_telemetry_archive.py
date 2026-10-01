from __future__ import annotations

import json
from pathlib import Path
import pytest

from svc_cli.telemetry.agent_threads import ProviderContext, ThreadSelection
from svc_cli.telemetry.archive import write_agent_thread_evidence
from svc_cli.telemetry.evidence import ValidatedEvidence, validate_evidence
from svc_cli.telemetry.providers.codex_rollout import CodexRolloutProvider


def _rollout(path: Path) -> bytes:
    records = (
        {
            "timestamp": "2026-01-01T00:00:00Z",
            "type": "session_meta",
            "payload": {"id": "thread-v3"},
        },
        {
            "timestamp": "2026-01-01T00:00:01Z",
            "type": "response_item",
            "payload": {
                "type": "message",
                "role": "assistant",
                "content": "done",
            },
        },
    )
    content = (
        "\n".join(json.dumps(item, separators=(",", ":")) for item in records) + "\n"
    ).encode()
    path.write_bytes(content)
    return content


def _export(source: Path, output: Path) -> ValidatedEvidence:
    return write_agent_thread_evidence(
        CodexRolloutProvider(),
        ProviderContext(home=source.parent),
        ThreadSelection(source=source),
        output,
    )


def test_export_never_overwrites_a_valid_bundle(tmp_path: Path) -> None:
    source = tmp_path / "rollout.jsonl"
    native = _rollout(source)
    output = tmp_path / "evidence.zip"
    _export(source, output)

    with pytest.raises(FileExistsError):
        _export(source, output)

    assert validate_evidence(output).native == native
