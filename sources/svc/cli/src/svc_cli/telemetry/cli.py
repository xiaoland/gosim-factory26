"""Argument grammar, execution, and presentation for telemetry commands."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from ..cli_output.model import dump_machine_output, unscoped_machine_object
from ..errors import SvcError
from .agent_threads import ArchiveFilter
from .service import export_agent_thread_v4, list_agent_threads, list_pi_agent_threads


def register(subparsers: argparse._SubParsersAction[Any]) -> None:
    telemetry = subparsers.add_parser(
        "telemetry",
        help="Collect explicit local observability evidence",
        description=(
            "Inventory one supported local provider or capture one explicitly selected "
            "Agent thread as immutable evidence. Telemetry does not interpret task "
            "performance, upload content, mutate the provider source, or imply that a "
            "listed source will remain readable."
        ),
    )
    resources = telemetry.add_subparsers(dest="telemetry_resource", required=True)
    agent_thread = resources.add_parser(
        "agent-thread",
        help="List or capture provider-obtainable Agent-thread evidence",
        description=(
            "List bounded provider metadata or export one exact local Agent thread. "
            "The caller owns source selection, destination privacy, retention, and "
            "subsequent interpretation."
        ),
    )
    commands = agent_thread.add_subparsers(dest="agent_thread_command", required=True)
    listing = commands.add_parser("list", help="List bounded thread selection context")
    listing.add_argument("--provider", choices=("codex", "pi"))
    listing.add_argument("--home", type=Path)
    listing.add_argument("--codex-home", type=Path)
    listing.add_argument(
        "--archive-state",
        choices=tuple(state.value for state in ArchiveFilter),
        default=ArchiveFilter.ALL.value,
        help="Filter by provider-reported lifecycle (default: all)",
    )
    listing.add_argument(
        "--limit", type=_limit, default=20, help="Maximum threads to list (1-100)"
    )
    listing.add_argument("--json", action="store_true", dest="json_output")

    export = commands.add_parser(
        "export", help="Capture one exact local thread into an evidence ZIP"
    )
    export.add_argument("--provider", choices=("codex", "pi"))
    selector = export.add_mutually_exclusive_group(required=True)
    selector.add_argument("--id", "--thread-id", dest="thread_id")
    selector.add_argument("--source", type=Path, help="Exact provider source")
    export.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Absent .zip destination distinct from the source",
    )
    export.add_argument("--codex-home", type=Path)
    export.add_argument("--home", type=Path)
    export.add_argument("--json", action="store_true", dest="json_output")


def run(args: argparse.Namespace, json_output: bool) -> int:
    if args.home is not None and args.codex_home is not None:
        raise SvcError("invalid-cli-usage", "Use only one of --home and --codex-home.")
    if args.agent_thread_command == "list":
        payload = (
            list_pi_agent_threads(args.home, args.limit)
            if args.provider == "pi"
            else list_agent_threads(
                args.home or args.codex_home, args.limit, args.archive_state
            )
        )
        _emit_list(payload, json_output)
        return 0
    payload = export_agent_thread_v4(
        provider_id=args.provider or "codex",
        home=args.home or args.codex_home,
        thread_id=args.thread_id,
        source=args.source,
        output=args.output,
    )
    _emit_export(payload, json_output)
    return 0


def _limit(value: str) -> int:
    try:
        limit = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("--limit must be an integer") from error
    if not 1 <= limit <= 100:
        raise argparse.ArgumentTypeError("--limit must be between 1 and 100")
    return limit


def _emit_list(payload: dict[str, Any], json_output: bool) -> None:
    if json_output:
        _emit_json(payload)
        return
    threads = payload["threads"]
    assert isinstance(threads, list)
    print(f"SVC telemetry agent-thread list: {len(threads)} thread(s)")
    for descriptor in threads:
        if isinstance(descriptor, dict):
            updated = descriptor.get("updated_at") or "unknown-time"
            print(
                f"  {descriptor.get('thread_id')}  {descriptor.get('archive_state')}  {updated}"
            )


def _emit_export(payload: dict[str, Any], json_output: bool) -> None:
    if json_output:
        _emit_json(payload)
        return
    evidence = payload["evidence"]
    path = evidence.get("path") if isinstance(evidence, dict) else None
    print(f"SVC telemetry agent-thread export: exported{f' {path}' if path else ''}")


def _emit_json(payload: dict[str, Any]) -> None:
    dump_machine_output(unscoped_machine_object(payload), sys.stdout)


__all__ = ["register", "run"]
