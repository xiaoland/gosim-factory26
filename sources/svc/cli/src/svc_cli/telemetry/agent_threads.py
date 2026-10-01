"""Provider-neutral contracts for local agent-thread inventory and collection.

The trajectory side deliberately exposes a sink-oriented normalisation seam.
Providers translate one bounded native source into canonical records while the
bundle core owns canonical JSONL, manifests, and publication.  No provider
record is accumulated in this module.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any, BinaryIO, Callable, Iterable, Mapping, Protocol
import unicodedata


MAX_INVENTORY_ROWS = 100
MAX_WORKSPACE_CHARS = 4_096
MAX_TITLE_CHARS = 160
MAX_FIRST_MESSAGE_CHARS = 512
MAX_THREAD_ID_CHARS = 512
MAX_SOURCE_BYTES = 256 * 1024 * 1024
MAX_NATIVE_FRAME_BYTES = 4 * 1024 * 1024
_SIGNED_64_MAX = 9_223_372_036_854_775_807
_CONTROL_CATEGORIES = frozenset({"Cc", "Cf", "Cs", "Zl", "Zp"})


class ArchiveState(StrEnum):
    """Provider-reported lifecycle for one thread."""

    ACTIVE = "active"
    ARCHIVED = "archived"
    UNKNOWN = "unknown"


class ArchiveFilter(StrEnum):
    """Inventory lifecycle filter; ``all`` is not a lifecycle state."""

    ACTIVE = "active"
    ARCHIVED = "archived"
    ALL = "all"


class SourceStatus(StrEnum):
    """Descriptor-bound source status reported by a normalizer."""

    STABLE = "stable"
    GREW = "grew"
    CHANGED = "changed"


class NormalizationStatus(StrEnum):
    """Whether a structurally valid normalized trajectory is complete."""

    READY = "ready"
    PARTIAL = "partial"


class NativeFrameStatus(StrEnum):
    """Whether one captured native frame contains its full provider record."""

    COMPLETE = "complete"
    INCOMPLETE = "incomplete"


@dataclass(frozen=True)
class ProviderContext:
    """Explicit, provider-owned local source location; never an implicit scan root."""

    home: Path | None = None


@dataclass(frozen=True)
class ThreadSelection:
    """One exact user-selected thread or native source artifact."""

    thread_id: str | None = None
    source: Path | None = None

    def __post_init__(self) -> None:
        if (self.thread_id is None) == (self.source is None):
            raise ValueError("Exactly one of thread_id or source is required")
        if self.thread_id is not None and not self.thread_id.strip():
            raise ValueError("thread_id must not be blank")


def _has_forbidden_control(value: str) -> bool:
    return any(
        unicodedata.category(character) in _CONTROL_CATEGORIES for character in value
    )


def _validate_utf8(value: str, *, field_name: str) -> None:
    try:
        value.encode("utf-8")
    except UnicodeEncodeError as error:
        raise ValueError(f"{field_name} must be representable UTF-8 text") from error


@dataclass(frozen=True, slots=True)
class ThreadRef:
    """Stable provider/thread identity for in-process selection."""

    provider_id: str
    thread_id: str

    def __post_init__(self) -> None:
        if (
            not isinstance(self.provider_id, str)
            or not self.provider_id.strip()
            or _has_forbidden_control(self.provider_id)
        ):
            raise ValueError("provider_id must be non-blank, control-free text")
        _validate_utf8(self.provider_id, field_name="provider_id")
        if (
            not isinstance(self.thread_id, str)
            or not 1 <= len(self.thread_id) <= MAX_THREAD_ID_CHARS
        ):
            raise ValueError("thread_id must be bounded non-empty text")
        _validate_utf8(self.thread_id, field_name="thread_id")


@dataclass(frozen=True, slots=True)
class ThreadInventoryRow:
    """One provider-bounded row for explicit thread selection."""

    provider_id: str
    thread_id: str
    archive_state: ArchiveState | str
    workspace: str | None = field(default=None, repr=False)
    title: str | None = field(default=None, repr=False)
    first_user_message: str | None = field(default=None, repr=False)
    workspace_truncated: bool = False
    title_truncated: bool = False
    first_user_message_truncated: bool = False
    created_at: str | None = field(default=None, repr=False)
    updated_at: str | None = field(default=None, repr=False)
    recency_at_ms: int | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        reference = ThreadRef(self.provider_id, self.thread_id)
        object.__setattr__(self, "provider_id", reference.provider_id)
        object.__setattr__(self, "thread_id", reference.thread_id)
        try:
            archive_state = ArchiveState(self.archive_state)
        except (TypeError, ValueError) as error:
            raise ValueError(
                "archive_state must be active, archived, or unknown"
            ) from error
        object.__setattr__(self, "archive_state", archive_state)

        workspace = self.workspace
        if workspace is not None:
            if not isinstance(workspace, str):
                raise ValueError("workspace must be text or null")
            _validate_utf8(workspace, field_name="workspace")
            if len(workspace) > MAX_WORKSPACE_CHARS:
                raise ValueError("workspace exceeds its provider-enforced bound")
            if _has_forbidden_control(workspace):
                workspace = None
        if self.workspace_truncated:
            if workspace is not None:
                raise ValueError("workspace_truncated requires a null workspace value")
        object.__setattr__(self, "workspace", workspace or None)

        for field_name, maximum in (
            ("title", MAX_TITLE_CHARS),
            ("first_user_message", MAX_FIRST_MESSAGE_CHARS),
        ):
            value = getattr(self, field_name)
            if value is None:
                continue
            if not isinstance(value, str):
                raise ValueError(f"{field_name} must be text or null")
            _validate_utf8(value, field_name=field_name)
            if len(value) > maximum:
                raise ValueError(f"{field_name} exceeds its provider-enforced bound")

        if self.recency_at_ms is not None and (
            isinstance(self.recency_at_ms, bool)
            or not isinstance(self.recency_at_ms, int)
            or self.recency_at_ms < 0
            or self.recency_at_ms > _SIGNED_64_MAX
        ):
            object.__setattr__(self, "recency_at_ms", None)

    @property
    def selection(self) -> ThreadRef:
        return ThreadRef(self.provider_id, self.thread_id)

    def __repr__(self) -> str:
        return (
            "ThreadInventoryRow("
            f"provider_id={self.provider_id!r}, "
            f"thread_id={self.thread_id!r}, "
            f"archive_state={str(self.archive_state)!r}, "
            f"workspace_truncated={self.workspace_truncated}, "
            f"title_truncated={self.title_truncated}, "
            "first_user_message_truncated="
            f"{self.first_user_message_truncated})"
        )


@dataclass(frozen=True, slots=True)
class ThreadInventoryQuery:
    """Bounded interactive query; active is the deliberate default."""

    archive_state: ArchiveFilter | str = ArchiveFilter.ACTIVE
    limit: int = MAX_INVENTORY_ROWS

    def __post_init__(self) -> None:
        try:
            archive_state = ArchiveFilter(self.archive_state)
        except (TypeError, ValueError) as error:
            raise ValueError(
                "archive_state must be active, archived, or all"
            ) from error
        object.__setattr__(self, "archive_state", archive_state)
        if (
            isinstance(self.limit, bool)
            or not isinstance(self.limit, int)
            or not 1 <= self.limit <= MAX_INVENTORY_ROWS
        ):
            raise ValueError(
                f"limit must be an integer between 1 and {MAX_INVENTORY_ROWS}"
            )

    @property
    def archive_filter(self) -> ArchiveFilter:
        return ArchiveFilter(self.archive_state)


def _inventory_row_order(
    row: ThreadInventoryRow,
) -> tuple[bool, int, bytes, bytes]:
    recency_at_ms = row.recency_at_ms
    missing = recency_at_ms is None
    recency = 0 if recency_at_ms is None else -recency_at_ms
    return (
        missing,
        recency,
        row.thread_id.encode("utf-8"),
        row.provider_id.encode("utf-8"),
    )


@dataclass(frozen=True, slots=True)
class ThreadInventoryListing:
    """A bounded listing plus an honest non-counting truncation signal."""

    items: tuple[ThreadInventoryRow, ...]
    inventory_truncated: bool = False

    def __post_init__(self) -> None:
        items = tuple(self.items)
        if len(items) > MAX_INVENTORY_ROWS:
            raise ValueError(
                f"listing cannot retain more than {MAX_INVENTORY_ROWS} rows"
            )
        object.__setattr__(self, "items", items)

    @classmethod
    def from_rows(
        cls,
        rows: Iterable[ThreadInventoryRow],
        *,
        archive_state: ArchiveFilter | str = ArchiveFilter.ACTIVE,
        limit: int = MAX_INVENTORY_ROWS,
    ) -> "ThreadInventoryListing":
        query = ThreadInventoryQuery(
            archive_state=archive_state,
            limit=limit,
        )
        retained: list[ThreadInventoryRow] = []
        truncated = False
        for row in rows:
            if not isinstance(row, ThreadInventoryRow):
                raise TypeError("rows must contain ThreadInventoryRow values")
            if (
                query.archive_filter is not ArchiveFilter.ALL
                and ArchiveState(row.archive_state).value != query.archive_filter.value
            ):
                continue
            if len(retained) >= query.limit:
                truncated = True
                continue
            retained.append(row)
        retained.sort(key=_inventory_row_order)
        return cls(
            tuple(retained),
            inventory_truncated=truncated,
        )


@dataclass(frozen=True)
class ResolvedThread:
    """A descriptor-bound local source selected for normalisation.

    ``source_path`` is process-local authority only.  It is never copied into
    a bundle or exposed through a service payload.  ``thread_id`` remains the
    provider's native selection identity; the normalizer derives the opaque
    trajectory ``thread_ref``.
    """

    provider_id: str
    adapter_id: str
    source_format: str
    thread_id: str
    source_path: Path = field(repr=False)

    def __post_init__(self) -> None:
        if not isinstance(self.source_path, Path):
            object.__setattr__(self, "source_path", Path(self.source_path))
        if not self.thread_id.strip():
            raise ValueError("thread_id must not be blank")


NormalizedRecordSink = Callable[[Mapping[str, Any]], bool]


@dataclass(frozen=True, slots=True)
class NativeCaptureResult:
    """Descriptor-bound facts for one immutable native capture.

    Providers own native record framing and source-change observation.  The
    evidence core owns typed index encoding, validation, snapshot identity,
    and publication. ``frames`` contains only JSON-ready byte boundaries and
    source coordinates; digests are computed from the captured authority when
    a reader needs them.
    """

    provider_id: str
    adapter_id: str
    source_format: str
    source_status: SourceStatus | str
    frames: tuple[Mapping[str, Any], ...]
    native_bytes: int
    unknown_remainder: bool = False
    read_interrupted: bool = False

    def __post_init__(self) -> None:
        try:
            object.__setattr__(self, "source_status", SourceStatus(self.source_status))
        except (TypeError, ValueError) as error:
            raise ValueError("invalid native capture source status") from error
        frames = tuple(self.frames)
        object.__setattr__(self, "frames", frames)
        if (
            isinstance(self.native_bytes, bool)
            or not isinstance(self.native_bytes, int)
            or self.native_bytes < 0
        ):
            raise ValueError("native_bytes must be a non-negative integer")

    @property
    def is_partial(self) -> bool:
        return (
            self.source_status is not SourceStatus.STABLE
            or self.unknown_remainder
            or self.read_interrupted
            or any(
                frame.get("frame_status") == NativeFrameStatus.INCOMPLETE.value
                for frame in self.frames
            )
        )


@dataclass(frozen=True)
class NormalizationResult:
    """Small derived-view summary returned after streaming records.

    Source identity and capture state already belong to ``ResolvedThread`` and
    ``NativeCaptureResult``. Record counts are computed from the emitted
    trajectory, so providers return only facts that cannot be recovered by
    counting its records.
    """

    result_status: NormalizationStatus | str
    capabilities: Mapping[str, str]
    lossiness: Mapping[str, Any]

    def __post_init__(self) -> None:
        try:
            object.__setattr__(
                self, "result_status", NormalizationStatus(self.result_status)
            )
        except (TypeError, ValueError) as error:
            raise ValueError("invalid normalization status") from error


class EvidenceThreadProvider(Protocol):
    """Provider capable of immutable native capture and captured projection."""

    provider_id: str

    def list_inventory(
        self,
        context: ProviderContext,
        query: ThreadInventoryQuery,
    ) -> ThreadInventoryListing: ...

    def resolve(
        self,
        context: ProviderContext,
        selection: ThreadSelection,
    ) -> ResolvedThread: ...

    def capture_native(
        self,
        resolved: ResolvedThread,
        output: BinaryIO,
        bounds: Mapping[str, int],
    ) -> NativeCaptureResult: ...

    def stream_normalize_captured(
        self,
        resolved: ResolvedThread,
        native: BinaryIO,
        capture: NativeCaptureResult,
        sink: NormalizedRecordSink,
        bounds: Mapping[str, int],
    ) -> NormalizationResult: ...
