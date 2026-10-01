"""Read-only adapter for Codex ``rollout-v1`` JSONL snapshots.

The adapter intentionally treats the source JSONL as the authority.  It does
not launch Codex, inspect editor caches, or attempt to interpret provider
payloads beyond the small amount of metadata needed for indexing.
"""

from __future__ import annotations

import json
import os
import sqlite3
import stat
import tempfile
from pathlib import Path
from typing import Any, BinaryIO, Iterable, Mapping, cast
from ...errors import SvcError
from ..agent_threads import (
    ArchiveFilter,
    ArchiveState,
    MAX_FIRST_MESSAGE_CHARS,
    MAX_TITLE_CHARS,
    MAX_WORKSPACE_CHARS,
    NativeCaptureResult,
    NormalizationResult,
    NormalizedRecordSink,
    NormalizationStatus,
    ProviderContext,
    ResolvedThread,
    SourceStatus,
    ThreadInventoryListing,
    ThreadInventoryQuery,
    ThreadInventoryRow,
    ThreadSelection,
)
from .codex_trajectory import CodexTrajectoryNormalizer, DEFAULT_BOUNDS


MAX_INDEX_RECORD_BYTES = 4 * 1024 * 1024
MAX_THREAD_ID_CHARS = 512
_MAX_SQLITE_INTEGER = 9_223_372_036_854_775_807
_MAX_RECENCY_SECONDS = _MAX_SQLITE_INTEGER // 1000
_SOURCE_FORMAT = "rollout-v1"
_ADAPTER_ID = "codex-rollout-v1"


def _error(code: str, message: str, **details: Any) -> SvcError:
    return SvcError(code, message, details)


def _home(context: ProviderContext) -> Path:
    if context.home is not None:
        return Path(context.home).expanduser()
    configured = os.environ.get("CODEX_HOME")
    return Path(configured).expanduser() if configured else Path.home() / ".codex"


def _open_source(path: Path) -> tuple[BinaryIO, os.stat_result]:
    """Open one ordinary local file read-only and bind facts to its descriptor."""

    try:
        stream = path.open("rb")
    except FileNotFoundError as exc:
        raise _error(
            "thread-source-not-found",
            "Codex rollout source does not exist.",
            path=str(path),
        ) from exc
    except (OSError, ValueError) as exc:
        raise _error(
            "thread-source-unreadable",
            "Codex rollout source cannot be opened.",
            path=str(path),
            reason=str(exc),
        ) from exc
    try:
        opened = os.fstat(stream.fileno())
        if not stat.S_ISREG(opened.st_mode):
            raise _error(
                "thread-source-unreadable",
                "Codex rollout source must be a regular file.",
                path=str(path),
            )
        return stream, opened
    except Exception:
        stream.close()
        raise


def _readline(stream: BinaryIO, limit: int, path: Path) -> bytes:
    """Translate a native-source read fault into a provider diagnostic."""
    try:
        return stream.readline(limit)
    except OSError as exc:
        raise _error(
            "thread-source-unreadable",
            "Codex rollout source cannot be read.",
            path=str(path),
            reason=str(exc),
        ) from exc


def _resolve_path(home: Path, value: Any) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise _error(
            "thread-source-incompatible", "State database has no usable rollout path."
        )
    try:
        candidate = Path(value).expanduser()
        if not candidate.is_absolute():
            candidate = home / candidate
        candidate = Path(os.path.abspath(candidate))
    except (OSError, RuntimeError, ValueError) as exc:
        raise _error(
            "thread-source-incompatible",
            "State database rollout path cannot be resolved.",
            reason=str(exc),
        ) from exc
    return candidate


def _columns(connection: Any) -> list[str]:
    try:
        rows = connection.execute("PRAGMA table_info(threads)").fetchall()
    except sqlite3.DatabaseError as exc:
        raise _error(
            "thread-source-incompatible",
            "Codex state database has an unreadable threads table.",
            reason=str(exc),
        ) from exc
    return [str(row[1]) for row in rows]


def _pick(columns: Iterable[str], choices: tuple[str, ...]) -> str | None:
    by_lower = {column.lower(): column for column in columns}
    for choice in choices:
        if choice.lower() in by_lower:
            return by_lower[choice.lower()]
    return None


def _state_connection(path: Path) -> sqlite3.Connection:
    """Open one direct read-only SQLite transaction."""

    connection: sqlite3.Connection | None = None
    handed_off = False
    try:
        database_uri = Path(os.path.abspath(path.expanduser())).as_uri()
        connection = sqlite3.connect(
            f"{database_uri}?mode=ro",
            uri=True,
            isolation_level=None,
        )
        connection.execute("BEGIN")
        handed_off = True
        return connection
    except (OSError, ValueError, sqlite3.DatabaseError) as exc:
        raise _error(
            "thread-source-incompatible",
            "Codex state database is not a readable SQLite database.",
            path=str(path),
            reason=str(exc),
        ) from exc
    finally:
        if connection is not None and not handed_off:
            connection.close()


def _archive_state(value: Any) -> ArchiveState:
    """Map only the exact Codex lifecycle authority."""
    if isinstance(value, int) and not isinstance(value, bool):
        if value == 0:
            return ArchiveState.ACTIVE
        if value == 1:
            return ArchiveState.ARCHIVED
    return ArchiveState.UNKNOWN


def _bounded_sqlite_text(value: Any, *, sqlite_type: Any, max_chars: int) -> str | None:
    """Decode one SQL-bounded text prefix without replacement or normalization."""
    if sqlite_type != "text":
        return None
    if isinstance(value, bytes):
        try:
            decoded = value.decode("utf-8", errors="strict")
        except UnicodeDecodeError:
            return None
    elif isinstance(value, str):
        decoded = value
    else:
        return None
    if len(decoded) > max_chars:
        return None
    try:
        decoded.encode("utf-8", errors="strict")
    except UnicodeEncodeError:
        return None
    return decoded


def _thread_id(sqlite_type: Any, prefix: Any) -> str | None:
    thread_id = _bounded_sqlite_text(
        prefix, sqlite_type=sqlite_type, max_chars=MAX_THREAD_ID_CHARS
    )
    return thread_id or None


def _inventory_text_projection(
    columns: Iterable[str],
    column: str,
    maximum_code_points: int,
) -> tuple[str, str, str]:
    """Return type, bounded UTF-8 bytes, and overflow SQL expressions."""

    if column not in columns:
        return "'null'", "NULL", "0"
    prefix_limit = maximum_code_points + 1
    quoted = column.replace('"', '""')
    sqlite_type = f'typeof("{quoted}")'
    usable = f"{sqlite_type} = 'text' AND instr(\"{quoted}\", char(0)) = 0"
    prefix = f"""CASE WHEN {usable}
            THEN CAST(
                substr("{quoted}", 1, {prefix_limit})
                AS BLOB
            )
            ELSE NULL END"""
    overflow = f"""CASE WHEN {usable}
            THEN length("{quoted}") > {prefix_limit}
            ELSE 0 END"""
    return sqlite_type, prefix, overflow


def _decode_inventory_prefix(
    sqlite_type: Any,
    prefix: Any,
    byte_overflow: Any,
    *,
    maximum_code_points: int,
    discard_when_truncated: bool,
) -> tuple[str | None, bool]:
    """Decode one SQL-bounded optional value without replacement decoding."""

    if sqlite_type != "text":
        return None, False
    if not isinstance(prefix, (bytes, bytearray, memoryview)):
        return None, False
    try:
        decoded = bytes(prefix).decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return None, False
    overflow = byte_overflow == 1
    truncated = overflow or len(decoded) > maximum_code_points
    if truncated:
        if discard_when_truncated:
            return None, True
        return decoded[:maximum_code_points], True
    return decoded, False


def _inventory_rows(
    home: Path,
    query: ThreadInventoryQuery,
) -> ThreadInventoryListing:
    """Materialize the bounded inventory view."""

    database = home / "state_5.sqlite"
    connection = _state_connection(database)
    try:
        columns = _columns(connection)
        if "id" not in columns:
            raise _error(
                "thread-source-incompatible",
                "Codex threads table does not expose its stable ID column.",
                columns=columns,
            )

        archive_value = (
            """CASE
                WHEN typeof("archived") = 'integer'
                    AND "archived" IN (0, 1)
                THEN "archived"
                ELSE NULL
            END"""
            if "archived" in columns
            else "NULL"
        )
        archive_state = (
            """CASE
                WHEN typeof("archived") = 'integer'
                    AND "archived" = 0 THEN 'active'
                WHEN typeof("archived") = 'integer'
                    AND "archived" = 1 THEN 'archived'
                ELSE 'unknown'
            END"""
            if "archived" in columns
            else "'unknown'"
        )

        def non_negative_integer(column: str) -> str:
            if column not in columns:
                return "NULL"
            return f"""CASE
                WHEN typeof("{column}") = 'integer' AND "{column}" >= 0
                THEN "{column}"
                ELSE NULL
            END"""

        recency_candidates: list[str] = []
        for column in ("recency_at_ms", "updated_at_ms"):
            if column in columns:
                recency_candidates.append(
                    f"""WHEN typeof("{column}") = 'integer'
                        AND "{column}" BETWEEN 0 AND {_MAX_SQLITE_INTEGER}
                    THEN "{column}" """
                )
        if "updated_at" in columns:
            recency_candidates.append(
                f"""WHEN typeof("updated_at") = 'integer'
                    AND "updated_at" BETWEEN 0
                        AND {_MAX_RECENCY_SECONDS}
                    THEN "updated_at" * 1000 """
            )
        recency = (
            "CASE " + " ".join(recency_candidates) + " ELSE NULL END"
            if recency_candidates
            else "NULL"
        )

        cwd_type, cwd_prefix, cwd_overflow = _inventory_text_projection(
            columns,
            "cwd",
            MAX_WORKSPACE_CHARS,
        )
        title_type, title_prefix, title_overflow = _inventory_text_projection(
            columns,
            "title",
            MAX_TITLE_CHARS,
        )
        message_type, message_prefix, message_overflow = _inventory_text_projection(
            columns,
            "first_user_message",
            MAX_FIRST_MESSAGE_CHARS,
        )

        sql = f"""
            WITH bounded AS (
                SELECT
                    typeof("id") AS id_type,
                    CASE WHEN typeof("id") = 'text'
                        AND instr("id", char(0)) = 0
                        THEN CAST(
                            substr("id", 1, {MAX_THREAD_ID_CHARS + 1})
                            AS BLOB
                        )
                        ELSE NULL
                    END AS id_prefix,
                    {archive_value} AS archive_value,
                    {archive_state} AS archive_state,
                    {non_negative_integer("created_at")} AS created_at,
                    {non_negative_integer("updated_at")} AS updated_at,
                    {recency} AS recency,
                    {cwd_type} AS cwd_type,
                    {cwd_prefix} AS cwd_prefix,
                    {cwd_overflow} AS cwd_overflow,
                    {title_type} AS title_type,
                    {title_prefix} AS title_prefix,
                    {title_overflow} AS title_overflow,
                    {message_type} AS message_type,
                    {message_prefix} AS message_prefix,
                    {message_overflow} AS message_overflow
                FROM threads
            ),
            inventory AS (
                SELECT
                    bounded.*,
                    COUNT(*) OVER (
                        PARTITION BY id_type, id_prefix
                    ) AS duplicate_count
                FROM bounded
            )
            SELECT
                id_type, id_prefix,
                archive_value, created_at, updated_at, recency,
                cwd_type, cwd_prefix, cwd_overflow,
                title_type, title_prefix, title_overflow,
                message_type, message_prefix, message_overflow,
                duplicate_count
            FROM inventory
            WHERE ? = 'all' OR archive_state = ?
            ORDER BY
                recency IS NULL ASC,
                recency DESC,
                id_prefix ASC
        """
        archive_filter = ArchiveFilter(query.archive_state).value
        rows = connection.execute(
            sql,
            (archive_filter, archive_filter),
        )
        result: list[ThreadInventoryRow] = []
        inventory_truncated = False
        for row in rows:
            (
                id_type,
                id_prefix,
                raw_archive_value,
                created_at,
                updated_at,
                recency_at_ms,
                cwd_type_value,
                cwd_prefix_value,
                cwd_overflow_value,
                title_type_value,
                title_prefix_value,
                title_overflow_value,
                message_type_value,
                message_prefix_value,
                message_overflow_value,
                duplicate_count,
            ) = row
            thread_id = _thread_id(id_type, id_prefix)
            if thread_id is None or duplicate_count != 1:
                continue

            if len(result) >= query.limit:
                inventory_truncated = True
                break

            workspace, workspace_truncated = _decode_inventory_prefix(
                cwd_type_value,
                cwd_prefix_value,
                cwd_overflow_value,
                maximum_code_points=MAX_WORKSPACE_CHARS,
                discard_when_truncated=True,
            )
            title, title_truncated = _decode_inventory_prefix(
                title_type_value,
                title_prefix_value,
                title_overflow_value,
                maximum_code_points=MAX_TITLE_CHARS,
                discard_when_truncated=False,
            )
            first_message, first_message_truncated = _decode_inventory_prefix(
                message_type_value,
                message_prefix_value,
                message_overflow_value,
                maximum_code_points=MAX_FIRST_MESSAGE_CHARS,
                discard_when_truncated=False,
            )
            result.append(
                ThreadInventoryRow(
                    provider_id="codex",
                    thread_id=thread_id,
                    archive_state=_archive_state(raw_archive_value),
                    workspace=workspace,
                    title=title,
                    first_user_message=first_message,
                    workspace_truncated=workspace_truncated,
                    title_truncated=title_truncated,
                    first_user_message_truncated=(first_message_truncated),
                    created_at=(None if created_at is None else str(created_at)),
                    updated_at=(None if updated_at is None else str(updated_at)),
                    recency_at_ms=recency_at_ms,
                )
            )
        return ThreadInventoryListing(
            tuple(result),
            inventory_truncated=inventory_truncated,
        )
    except SvcError:
        raise
    except sqlite3.DatabaseError as exc:
        raise _error(
            "thread-source-incompatible",
            "Codex state database inventory metadata cannot be read.",
            path=str(database),
            reason=str(exc),
        ) from exc
    finally:
        connection.close()


def _extract_thread_id(payload: Any) -> str | None:
    if not isinstance(payload, dict):
        return None
    for key in ("thread_id", "threadId", "session_id", "sessionId", "id"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return None


def _is_envelope(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and isinstance(value.get("type"), str)
        and "payload" in value
        and "timestamp" in value
    )


def _signature(path: Path) -> str:
    stream, _ = _open_source(path)
    try:
        while True:
            line = _readline(stream, MAX_INDEX_RECORD_BYTES + 1, path)
            if not line:
                break
            if len(line) > MAX_INDEX_RECORD_BYTES:
                while not line.endswith(b"\n"):
                    line = _readline(stream, MAX_INDEX_RECORD_BYTES + 1, path)
                    if not line:
                        break
                continue
            try:
                value = json.loads(line)
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
            if not _is_envelope(value):
                continue
            if value.get("type") == "session_meta":
                candidate = _extract_thread_id(value.get("payload"))
                if candidate:
                    return candidate
    finally:
        stream.close()
    raise _error(
        "thread-source-incompatible",
        "Source is not a compatible rollout-v1 JSONL snapshot.",
        path=str(path),
    )


class CodexRolloutProvider:
    """Static ``codex-rollout-v1`` provider implementation."""

    provider_id = "codex"

    def list_inventory(
        self,
        context: ProviderContext,
        query: ThreadInventoryQuery,
    ) -> ThreadInventoryListing:
        if not isinstance(query, ThreadInventoryQuery):
            raise _error(
                "invalid-inventory-query", "Thread inventory query is invalid."
            )
        home = _home(context)
        return _inventory_rows(home, query)

    def resolve(
        self, context: ProviderContext, selection: ThreadSelection
    ) -> ResolvedThread:
        home = _home(context)
        if selection.source is not None:
            source = Path(selection.source).expanduser()
            thread_id = _signature(source)
        else:
            assert selection.thread_id is not None
            connection = _state_connection(home / "state_5.sqlite")
            try:
                columns = _columns(connection)
                id_column = _pick(columns, ("thread_id", "threadId", "id", "uuid"))
                source_column = _pick(
                    columns,
                    (
                        "rollout_path",
                        "rolloutPath",
                        "source_path",
                        "sourcePath",
                        "rollout",
                        "path",
                    ),
                )
                if id_column is None or source_column is None:
                    raise _error(
                        "thread-source-incompatible",
                        "Codex threads table does not expose exact ID and rollout path columns.",
                        columns=columns,
                    )
                query = f'SELECT "{id_column.replace(chr(34), chr(34) * 2)}", "{source_column.replace(chr(34), chr(34) * 2)}" FROM threads WHERE "{id_column.replace(chr(34), chr(34) * 2)}" = ? LIMIT 1'
                row = connection.execute(query, (selection.thread_id,)).fetchone()
                if row is None:
                    raise _error(
                        "thread-not-found",
                        "No exact Codex thread ID is present in the state database.",
                        thread_id=selection.thread_id,
                    )
                source = _resolve_path(home, row[1])
            except SvcError:
                raise
            except sqlite3.DatabaseError as exc:
                raise _error(
                    "thread-source-incompatible",
                    "Codex state database cannot resolve the selected thread.",
                    thread_id=selection.thread_id,
                    reason=str(exc),
                ) from exc
            finally:
                connection.close()
            discovered_id = _signature(source)
            if discovered_id != selection.thread_id:
                raise _error(
                    "thread-source-incompatible",
                    "Rollout source identity does not match the selected thread ID.",
                    thread_id=selection.thread_id,
                )
            thread_id = selection.thread_id
        return ResolvedThread(
            provider_id=self.provider_id,
            adapter_id=_ADAPTER_ID,
            source_format=_SOURCE_FORMAT,
            thread_id=thread_id,
            source_path=source,
        )

    def capture_native(
        self,
        resolved: ResolvedThread,
        output: BinaryIO,
        bounds: Mapping[str, int],
    ) -> NativeCaptureResult:
        """Copy and frame the descriptor-bound initial rollout extent once."""

        if (
            resolved.provider_id != self.provider_id
            or resolved.adapter_id != _ADAPTER_ID
            or resolved.source_format != _SOURCE_FORMAT
        ):
            raise _error(
                "thread-source-incompatible",
                "Resolved source does not belong to codex-rollout-v1.",
            )
        source_limit = int(bounds.get("source_bytes", DEFAULT_BOUNDS["source_bytes"]))
        if source_limit <= 0:
            raise ValueError("source_bytes must be a positive integer")
        source = Path(resolved.source_path)
        stream, initial_info = _open_source(source)
        extent = min(initial_info.st_size, source_limit)
        remaining = extent
        captured = 0
        frame_start = 0
        frames: list[dict[str, Any]] = []
        read_interrupted = False
        final_info: os.stat_result | None = None

        def finish_frame(end: int, status: str) -> None:
            ordinal = len(frames)
            frames.append(
                {
                    "native_record_id": f"n{ordinal:06d}",
                    "byte_start": frame_start,
                    "byte_end": end,
                    "frame_status": status,
                    "source_coordinate": {
                        "event_index": ordinal,
                        "line": ordinal,
                        "byte_offset": frame_start,
                    },
                }
            )

        try:
            while remaining:
                try:
                    chunk = stream.read(min(1024 * 1024, remaining))
                except OSError:
                    read_interrupted = True
                    break
                if not chunk:
                    read_interrupted = True
                    break
                output.write(chunk)
                cursor = 0
                while True:
                    newline = chunk.find(b"\n", cursor)
                    if newline < 0:
                        break
                    captured += newline + 1 - cursor
                    finish_frame(captured, "complete")
                    frame_start = captured
                    cursor = newline + 1
                captured += len(chunk) - cursor
                remaining -= len(chunk)
            final_info = os.fstat(stream.fileno())
        except OSError as error:
            raise _error(
                "thread-source-unreadable",
                "Codex rollout source cannot be captured.",
                path=str(source),
            ) from error
        finally:
            stream.close()

        unknown_remainder = initial_info.st_size > captured or read_interrupted
        if frame_start < captured:
            finish_frame(
                captured,
                "incomplete" if unknown_remainder else "complete",
            )

        status = SourceStatus.STABLE
        assert final_info is not None
        if final_info.st_size < initial_info.st_size or (
            final_info.st_size == initial_info.st_size
            and final_info.st_mtime_ns != initial_info.st_mtime_ns
        ):
            status = SourceStatus.CHANGED
        elif final_info.st_size > initial_info.st_size:
            status = SourceStatus.GREW

        output.seek(0)
        return NativeCaptureResult(
            provider_id=self.provider_id,
            adapter_id=_ADAPTER_ID,
            source_format=_SOURCE_FORMAT,
            source_status=status,
            frames=tuple(frames),
            native_bytes=captured,
            unknown_remainder=unknown_remainder,
            read_interrupted=read_interrupted,
        )

    def stream_normalize_captured(
        self,
        resolved: ResolvedThread,
        native: BinaryIO,
        capture: NativeCaptureResult,
        sink: NormalizedRecordSink,
        bounds: Mapping[str, int],
    ) -> NormalizationResult:
        """Derive the trajectory only from the immutable captured bytes."""

        if (
            resolved.provider_id != self.provider_id
            or resolved.adapter_id != _ADAPTER_ID
            or resolved.source_format != _SOURCE_FORMAT
            or capture.provider_id != self.provider_id
            or capture.adapter_id != _ADAPTER_ID
            or capture.source_format != _SOURCE_FORMAT
        ):
            raise _error(
                "thread-source-incompatible",
                "Captured source does not belong to codex-rollout-v1.",
            )
        effective = dict(DEFAULT_BOUNDS)
        effective.update(
            {
                key: int(value)
                for key, value in bounds.items()
                if isinstance(value, int) and not isinstance(value, bool) and value > 0
            }
        )
        projection = tempfile.SpooledTemporaryFile(
            max_size=1024 * 1024,
            mode="w+b",
        )
        omitted_frames: list[Mapping[str, Any]] = []
        try:
            for frame in capture.frames:
                start = int(frame["byte_start"])
                end = int(frame["byte_end"])
                size = end - start
                if (
                    frame["frame_status"] != "complete"
                    or size > effective["native_line_bytes"]
                ):
                    omitted_frames.append(frame)
                    projection.write(
                        json.dumps(
                            {
                                "type": "session_meta",
                                "payload": {"id": resolved.thread_id},
                            },
                            separators=(",", ":"),
                        ).encode("utf-8")
                        + b"\n"
                    )
                    continue
                native.seek(start)
                data = native.read(size)
                if not isinstance(data, bytes) or len(data) != size:
                    raise _error(
                        "thread-source-unreadable",
                        "Captured Codex rollout frame cannot be read.",
                    )
                projection.write(data)
            projection.seek(0)

            def mapped_sink(record: Mapping[str, Any]) -> bool:
                if record.get("type") == "meta":
                    return sink(record)
                source_ref = record.get("source_ref")
                if not isinstance(source_ref, Mapping):
                    raise _error(
                        "thread-source-incompatible",
                        "Normalized record omitted its source coordinate.",
                    )
                ordinal = source_ref.get("event_index")
                if (
                    not isinstance(ordinal, int)
                    or isinstance(ordinal, bool)
                    or not 0 <= ordinal < len(capture.frames)
                ):
                    raise _error(
                        "thread-source-incompatible",
                        "Normalized record source coordinate is outside the capture.",
                    )
                mapped = dict(record)
                mapped_source = dict(source_ref)
                mapped_source["native_record_id"] = capture.frames[ordinal][
                    "native_record_id"
                ]
                mapped["source_ref"] = mapped_source
                return sink(mapped)

            result = CodexTrajectoryNormalizer().normalize(
                cast(BinaryIO, projection),
                resolved,
                mapped_sink,
                DEFAULT_BOUNDS,
            )
        finally:
            projection.close()

        lossiness = dict(result.lossiness)
        result_status = result.result_status
        oversized = [
            frame
            for frame in omitted_frames
            if frame["frame_status"] == "complete"
            and int(frame["byte_end"]) - int(frame["byte_start"])
            > effective["native_line_bytes"]
        ]
        incomplete = [
            frame for frame in omitted_frames if frame["frame_status"] != "complete"
        ]
        lossiness["dropped_records"] += len(oversized)
        lossiness["unavailable_records"] += len(incomplete)
        lossiness["partial_frames"] += len(incomplete)
        if oversized or capture.is_partial:
            result_status = NormalizationStatus.PARTIAL
        return NormalizationResult(
            result_status=result_status,
            capabilities=result.capabilities,
            lossiness=lossiness,
        )


__all__ = ["CodexRolloutProvider"]
