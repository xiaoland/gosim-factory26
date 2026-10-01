from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import json
from pathlib import Path

from svc_cli.cli import main
from svc_cli.telemetry.agent_threads import (
    ArchiveState,
    ThreadInventoryListing,
    ThreadInventoryRow,
)
from svc_cli.telemetry.evidence_v4 import validate_evidence_v4


def _invoke(arguments: list[str]) -> tuple[int, str, str]:
    stdout = StringIO()
    stderr = StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        code = main(arguments)
    return code, stdout.getvalue(), stderr.getvalue()


def _rollout(path: Path) -> None:
    records = (
        {
            "timestamp": "2026-01-01T00:00:00Z",
            "type": "session_meta",
            "payload": {"id": "thread-cli", "cwd": "/work/svc"},
        },
        {
            "timestamp": "2026-01-01T00:00:01Z",
            "type": "response_item",
            "payload": {
                "type": "message",
                "role": "assistant",
                "content": "finished",
            },
        },
    )
    path.write_text(
        "\n".join(json.dumps(item, separators=(",", ":")) for item in records) + "\n",
        encoding="utf-8",
    )


def _request(
    tmp_path: Path,
    bundle: Path,
    tool: str,
    payload: dict[str, object],
) -> dict[str, object]:
    request = tmp_path / f"{tool}.json"
    request.write_text(json.dumps(payload), encoding="utf-8")
    code, stdout, stderr = _invoke(
        [
            "analysis",
            tool,
            "--input",
            str(bundle),
            "--request",
            str(request),
        ]
    )
    assert (code, stderr) == (0, "")
    return json.loads(stdout)


def test_cli_export_query_and_read_contract(tmp_path: Path) -> None:
    source = tmp_path / "rollout.jsonl"
    bundle = tmp_path / "evidence.zip"
    _rollout(source)

    code, stdout, stderr = _invoke(
        [
            "telemetry",
            "agent-thread",
            "export",
            "--source",
            str(source),
            "--output",
            str(bundle),
            "--json",
        ]
    )
    assert (code, stderr) == (0, "")
    exported = json.loads(stdout)
    assert exported["schema_version"] == exported["evidence"]["schema_version"] == 4
    assert exported["provider"] == "codex"
    assert validate_evidence_v4(bundle).manifest.schema_version == 4

    code, stdout, stderr = _invoke(["analysis", "query", "--schema"])
    assert (code, stderr) == (0, "")
    schema = json.loads(stdout)
    assert schema["version"] == 3

    overview = _request(tmp_path, bundle, "query", {"version": 3, "intent": "overview"})
    assert (overview["intent"], overview["status"]) == ("overview", "complete")


def test_analysis_errors_and_removed_grammar_are_json(tmp_path: Path) -> None:
    code, stdout, stderr = _invoke(["analysis", "query", "--unknown"])
    assert (code, stdout, json.loads(stderr)["code"]) == (
        2,
        "",
        "invalid-cli-usage",
    )

    request = tmp_path / "bad.json"
    request.write_text('{"intent":"overview","intent":"match"}', encoding="utf-8")
    code, stdout, stderr = _invoke(
        [
            "analysis",
            "query",
            "--input",
            str(tmp_path / "missing.zip"),
            "--request",
            str(request),
        ]
    )
    assert (code, stdout, json.loads(stderr)["code"]) == (
        2,
        "",
        "invalid-analysis-request-json",
    )

    assert _invoke(["telemetry", "agent-thread", "analyze"])[0] == 2
    source = tmp_path / "source.jsonl"
    _rollout(source)
    assert (
        _invoke(
            [
                "telemetry",
                "agent-thread",
                "export",
                "--source",
                str(source),
                "--output",
                str(tmp_path / "x.zip"),
                "--legacy-listing",
            ]
        )[0]
        == 2
    )


def test_list_projects_only_public_inventory_fields(monkeypatch) -> None:
    class Provider:
        provider_id = "codex"

        def list_inventory(self, context, query):
            return ThreadInventoryListing(
                (
                    ThreadInventoryRow(
                        provider_id="codex",
                        thread_id="thread-1",
                        archive_state=ArchiveState.ACTIVE,
                        workspace="/work/svc",
                        title="Implement analysis",
                        first_user_message="Start",
                    ),
                )
            )

    monkeypatch.setattr("svc_cli.telemetry.service.local_provider", lambda: Provider())
    code, stdout, stderr = _invoke(["telemetry", "agent-thread", "list", "--json"])

    assert (code, stderr) == (0, "")
    payload = json.loads(stdout)
    row = payload["threads"][0]
    assert {
        "provider_id": row["provider_id"],
        "thread_id": row["thread_id"],
        "archive_state": row["archive_state"],
        "workspace": row["workspace"],
        "title": row["title"],
    } == {
        "provider_id": "codex",
        "thread_id": "thread-1",
        "archive_state": "active",
        "workspace": "/work/svc",
        "title": "Implement analysis",
    }
    assert not {
        "source_availability",
        "source_warning_code",
        "omitted_sources",
    } & (set(row) | set(payload))
