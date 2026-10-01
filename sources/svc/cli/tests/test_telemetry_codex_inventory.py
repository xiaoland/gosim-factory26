from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

from svc_cli.errors import SvcError
from svc_cli.telemetry.agent_threads import (
    ArchiveFilter,
    ArchiveState,
    ProviderContext,
    ThreadInventoryQuery,
    ThreadSelection,
)
from svc_cli.telemetry.providers import CodexRolloutProvider


@dataclass(frozen=True)
class InventoryCase:
    root: Path
    provider: CodexRolloutProvider

    def list(
        self,
        *,
        limit: int = 20,
        archive_state: ArchiveFilter = ArchiveFilter.ALL,
    ):
        return self.provider.list_inventory(
            ProviderContext(home=self.root),
            ThreadInventoryQuery(archive_state=archive_state, limit=limit),
        )

    def rollout(self, name: str, thread_id: str) -> Path:
        path = self.root / name
        path.write_text(
            json.dumps(
                {
                    "timestamp": "2026-01-01T00:00:00Z",
                    "type": "session_meta",
                    "payload": {"id": thread_id},
                }
            )
            + "\n",
            encoding="utf-8",
        )
        return path


@pytest.fixture
def inventory_case(tmp_path: Path) -> InventoryCase:
    return InventoryCase(tmp_path, CodexRolloutProvider())


@contextmanager
def state_database(root: Path) -> Iterator[sqlite3.Connection]:
    connection = sqlite3.connect(root / "state_5.sqlite")
    try:
        with connection:
            yield connection
    finally:
        connection.close()


def insert_rows(
    connection: sqlite3.Connection,
    schema: str,
    rows: Iterable[tuple[Any, ...]],
) -> None:
    connection.execute(f"CREATE TABLE threads ({schema})")
    placeholders = ", ".join("?" for _ in schema.split(","))
    connection.executemany(
        f"INSERT INTO threads VALUES ({placeholders})",
        rows,
    )


class TestCodexInventory:
    def test_inventory_is_metadata_only_and_resolution_returns_public_descriptor(
        self,
        inventory_case: InventoryCase,
    ) -> None:
        valid = inventory_case.rollout("valid.jsonl", "thread-valid")
        invalid = inventory_case.root / "not-a-rollout.jsonl"
        invalid.write_text("private non-rollout body", encoding="utf-8")
        with state_database(inventory_case.root) as connection:
            insert_rows(
                connection,
                "id TEXT, rollout_path TEXT, archived, recency_at_ms INTEGER",
                [
                    ("thread-invalid", invalid.name, None, 20),
                    ("thread-valid", valid.name, 0, 10),
                    ("metadata-without-source", None, 1, 5),
                ],
            )

        listing = inventory_case.list()

        assert [item.thread_id for item in listing.items] == [
            "thread-invalid",
            "thread-valid",
            "metadata-without-source",
        ]
        assert listing.items[0].archive_state is ArchiveState.UNKNOWN
        assert listing.items[2].archive_state is ArchiveState.ARCHIVED

        resolved = inventory_case.provider.resolve(
            ProviderContext(home=inventory_case.root),
            ThreadSelection(thread_id="thread-valid"),
        )
        assert (
            resolved.provider_id,
            resolved.adapter_id,
            resolved.source_format,
            resolved.thread_id,
            resolved.source_path,
        ) == (
            "codex",
            "codex-rollout-v1",
            "rollout-v1",
            "thread-valid",
            valid,
        )

        with pytest.raises(SvcError) as raised:
            inventory_case.provider.resolve(
                ProviderContext(home=inventory_case.root),
                ThreadSelection(thread_id="thread-invalid"),
            )
        assert raised.value.code == "thread-source-incompatible"

    def test_lifecycle_filter_precedes_limit_and_ties_have_stable_order(
        self,
        inventory_case: InventoryCase,
    ) -> None:
        with state_database(inventory_case.root) as connection:
            insert_rows(
                connection,
                "id TEXT, rollout_path TEXT, archived, recency_at_ms INTEGER",
                [
                    ("archived-new", "a.jsonl", 1, 900),
                    ("unknown-new", "u.jsonl", "1", 850),
                    ("active-new", "n.jsonl", 0, 800),
                    ("zulu", "z.jsonl", 0, 700),
                    ("alpha", "alpha.jsonl", 0, 700),
                    ("archived-old", "old.jsonl", 1, 600),
                ],
            )

        active = inventory_case.list(
            limit=2,
            archive_state=ArchiveFilter.ACTIVE,
        )
        archived = inventory_case.list(
            limit=2,
            archive_state=ArchiveFilter.ARCHIVED,
        )
        all_rows = inventory_case.list(limit=20)

        assert [item.thread_id for item in active.items] == [
            "active-new",
            "alpha",
        ]
        assert active.inventory_truncated
        assert [item.thread_id for item in archived.items] == [
            "archived-new",
            "archived-old",
        ]
        assert not archived.inventory_truncated
        assert [item.thread_id for item in all_rows.items] == [
            "archived-new",
            "unknown-new",
            "active-new",
            "alpha",
            "zulu",
            "archived-old",
        ]

    def test_inventory_descriptor_text_and_limit_bounds_are_observable(
        self,
        inventory_case: InventoryCase,
    ) -> None:
        with state_database(inventory_case.root) as connection:
            insert_rows(
                connection,
                """
                    id, rollout_path TEXT, archived, created_at, updated_at,
                    recency_at_ms, cwd TEXT, title TEXT,
                    first_user_message TEXT
                """,
                [
                    (
                        "bounded",
                        "bounded.jsonl",
                        0,
                        3,
                        4,
                        8_000,
                        "w" * 4_097,
                        "t" * 161,
                        "m" * 513,
                    ),
                ],
            )

        listing = inventory_case.list(limit=1)

        assert [item.thread_id for item in listing.items] == ["bounded"]
        bounded = listing.items[0]
        assert bounded.workspace is None
        assert bounded.workspace_truncated
        assert bounded.title == "t" * 160
        assert bounded.title_truncated
        assert bounded.first_user_message == "m" * 512
        assert bounded.first_user_message_truncated
        assert (bounded.created_at, bounded.updated_at, bounded.recency_at_ms) == (
            "3",
            "4",
            8_000,
        )
