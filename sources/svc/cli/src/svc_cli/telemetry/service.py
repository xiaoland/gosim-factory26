"""Public service functions for local Agent-thread evidence acquisition."""

from __future__ import annotations

from pathlib import Path

from ..errors import SvcError
from .agent_threads import (
    ArchiveFilter,
    ArchiveState,
    ProviderContext,
    ThreadInventoryQuery,
    ThreadSelection,
)
from .providers import provider as local_provider
from .evidence_v4 import write_evidence_v4_stream
from .providers.codex_v4 import collect_codex_v4
from .providers.pi_v4 import collect_pi_v4, list_pi_sessions


TELEMETRY_SCHEMA_VERSION = 3


def _context(codex_home: Path | None) -> ProviderContext:
    return ProviderContext(
        home=(Path(codex_home).expanduser() if codex_home is not None else None)
    )


def list_agent_threads(
    codex_home: Path | None,
    limit: int,
    archive_state: ArchiveFilter | str = ArchiveFilter.ALL,
) -> dict[str, object]:
    """Return one bounded thread inventory for explicit selection."""

    try:
        query = ThreadInventoryQuery(
            archive_state=archive_state,
            limit=limit,
        )
    except ValueError as error:
        raise SvcError("invalid-inventory-query", str(error)) from error
    provider = local_provider()
    listing = provider.list_inventory(_context(codex_home), query)
    threads = [
        {
            "provider_id": row.provider_id,
            "thread_id": row.thread_id,
            "archive_state": ArchiveState(row.archive_state).value,
            "workspace": row.workspace,
            "title": row.title,
            "first_user_message": row.first_user_message,
            "workspace_truncated": row.workspace_truncated,
            "title_truncated": row.title_truncated,
            "first_user_message_truncated": row.first_user_message_truncated,
            "created_at": row.created_at,
            "updated_at": row.updated_at,
            "recency_at_ms": row.recency_at_ms,
        }
        for row in listing.items
    ]
    return {
        "schema_version": TELEMETRY_SCHEMA_VERSION,
        "command": "telemetry agent-thread list",
        "status": "listed",
        "provider": provider.provider_id,
        "threads": threads,
        "inventory_truncated": listing.inventory_truncated,
    }


def list_pi_agent_threads(home: Path | None, limit: int) -> dict[str, object]:
    threads, truncated = list_pi_sessions(home, limit)
    return {
        "schema_version": 4,
        "command": "telemetry agent-thread list",
        "status": "listed",
        "provider": "pi",
        "threads": threads,
        "inventory_truncated": truncated,
    }


def export_agent_thread_v4(
    *,
    provider_id: str,
    home: Path | None,
    thread_id: str | None,
    source: Path | None,
    output: Path,
) -> dict[str, object]:
    """Export one selected Codex or standard Pi trajectory as evidence v4."""

    try:
        selection = ThreadSelection(thread_id=thread_id, source=source)
    except ValueError as error:
        raise SvcError("invalid-thread-selector", str(error)) from error
    context = _context(home)
    if provider_id == "codex":
        manifest, trajectory, materials = collect_codex_v4(context, selection)
    elif provider_id == "pi":
        manifest, trajectory, materials = collect_pi_v4(context, selection)
    else:
        raise SvcError(
            "unsupported-provider", f"Unsupported telemetry provider: {provider_id}"
        )
    target = Path(output).expanduser()
    if target.suffix != ".zip" or not target.parent.is_dir():
        raise SvcError(
            "invalid-export-request",
            "Evidence output must be an absent .zip in an existing directory.",
        )
    created = False
    try:
        with target.open("x+b") as stream:
            created = True
            evidence = write_evidence_v4_stream(stream, manifest, trajectory, materials)
    except FileExistsError as error:
        raise SvcError(
            "output-exists",
            "Evidence output already exists and was not replaced.",
            {"path": str(target)},
        ) from error
    except Exception:
        if created:
            target.unlink(missing_ok=True)
        raise
    return {
        "schema_version": 4,
        "command": "telemetry agent-thread export",
        "status": "exported",
        "provider": provider_id,
        "evidence": {
            "path": str(target),
            "evidence_id": evidence.evidence_id,
            "schema_version": 4,
            "trajectory_events": len(evidence.trajectory.events),
            "executions": len(evidence.trajectory.executions),
            "materials": len(evidence.materials),
        },
        "coverage": [
            item.model_dump(mode="json") for item in evidence.trajectory.header.coverage
        ],
        "issues": [
            item.model_dump(mode="json") for item in evidence.trajectory.header.issues
        ],
    }


__all__ = ["export_agent_thread_v4", "list_agent_threads", "list_pi_agent_threads"]
