"""Capture and publish the small schema-v3 Agent-thread evidence core."""

from __future__ import annotations

from pathlib import Path
import tempfile
from typing import Any, BinaryIO, Callable, Literal, cast

from ..errors import SvcError
from .agent_threads import (
    EvidenceThreadProvider,
    MAX_NATIVE_FRAME_BYTES,
    MAX_SOURCE_BYTES,
    NativeCaptureResult,
    NormalizationStatus,
    ProviderContext,
    ResolvedThread,
    SourceStatus,
    ThreadSelection,
)
from .evidence import (
    EvidenceError,
    EvidenceManifest,
    ValidatedEvidence,
    build_evidence_manifest,
    encode_native_index,
    validate_evidence,
    validate_evidence_members,
    write_evidence_stream,
)
from .trajectory import (
    TrajectoryCollector,
    TrajectoryError,
    attach_projection_summary,
)


def _evidence_output(output: Path) -> Path:
    """Validate the stable request shape; exclusive creation owns absence."""

    requested = Path(output).expanduser()
    if requested.suffix != ".zip":
        raise ValueError("Evidence output must have an explicit .zip suffix")
    if not requested.parent.is_dir():
        raise ValueError("Evidence output parent must be an existing directory")
    return requested


def _publish_output(
    output: Path,
    writer: Callable[[BinaryIO], object],
) -> ValidatedEvidence:
    """Exclusively create one target and retain it only after validation."""

    created = False
    try:
        with output.open("x+b") as archive_stream:
            created = True
            writer(archive_stream)
        return validate_evidence(output)
    except Exception:
        if created:
            try:
                output.unlink()
            except OSError:
                pass
        raise


def _capture_bounds() -> dict[str, int]:
    """Return the two provider limits that protect native acquisition."""

    return {
        "source_bytes": MAX_SOURCE_BYTES,
        "native_line_bytes": MAX_NATIVE_FRAME_BYTES,
    }


def _derive_trajectory(
    provider: EvidenceThreadProvider,
    resolved: ResolvedThread,
    capture: NativeCaptureResult,
    native: BinaryIO,
) -> bytes:
    """Build one disposable structural cache from captured authority."""

    collector = TrajectoryCollector()
    native.seek(0)
    result = provider.stream_normalize_captured(
        resolved,
        native,
        capture,
        collector.emit,
        _capture_bounds(),
    )
    trajectory = collector.finish()
    if trajectory is None:
        raise ValueError("An owned trajectory collector must return bytes")
    return attach_projection_summary(
        trajectory,
        result_status=cast(
            Literal["ready", "partial"],
            NormalizationStatus(result.result_status).value,
        ),
        capabilities=result.capabilities,
        lossiness=result.lossiness,
    )


def _capture_members(
    provider: EvidenceThreadProvider,
    resolved: ResolvedThread,
    native: BinaryIO,
) -> tuple[EvidenceManifest, bytes, bytes, bytes | None]:
    native.seek(0)
    native.truncate(0)
    capture = provider.capture_native(resolved, native, _capture_bounds())
    if (
        capture.provider_id != resolved.provider_id
        or capture.adapter_id != resolved.adapter_id
        or capture.source_format != resolved.source_format
    ):
        raise ValueError("Captured source identity does not match selection")

    native.seek(0)
    native_bytes = native.read()
    if not isinstance(native_bytes, bytes):
        raise ValueError("Evidence staging stream must return bytes")
    native_index = encode_native_index(capture.frames)
    manifest = build_evidence_manifest(
        native=native_bytes,
        native_index=native_index,
        source={
            "provider_id": capture.provider_id,
            "adapter_id": capture.adapter_id,
            "source_format": capture.source_format,
            "thread_id": resolved.thread_id,
            "source_status": SourceStatus(capture.source_status).value,
        },
        capture={
            "status": "partial" if capture.is_partial else "complete",
            "unknown_remainder": capture.unknown_remainder,
            "read_interrupted": capture.read_interrupted,
        },
    )

    trajectory: bytes | None = None
    try:
        trajectory = _derive_trajectory(provider, resolved, capture, native)
        validated = validate_evidence_members(
            manifest,
            native_bytes,
            native_index,
            trajectory,
        )
        if validated.trajectory is None:
            trajectory = None
    except (EvidenceError, SvcError, TrajectoryError, OSError, TypeError, ValueError):
        # Projection is a disposable cache. Its failure cannot invalidate
        # successfully captured native authority.
        trajectory = None
    return manifest, native_bytes, native_index, trajectory


def write_agent_thread_evidence(
    provider: EvidenceThreadProvider,
    context: ProviderContext,
    selection: ThreadSelection,
    output: Path,
) -> ValidatedEvidence:
    """Capture and exclusively create one validated schema-v3 archive."""

    resolved = provider.resolve(context, selection)
    target = _evidence_output(output)
    native = tempfile.SpooledTemporaryFile(max_size=1024 * 1024, mode="w+b")
    try:
        manifest, native_bytes, native_index, trajectory = _capture_members(
            provider,
            resolved,
            cast(BinaryIO, native),
        )

        def write(stream: BinaryIO) -> Any:
            return write_evidence_stream(
                stream,
                manifest,
                native_bytes,
                native_index,
                trajectory,
            )

        return _publish_output(target, write)
    except (TrajectoryError, EvidenceError) as error:
        raise SvcError(error.code, error.message) from error
    finally:
        native.close()


def rebuild_evidence_trajectory(
    evidence: ValidatedEvidence,
    provider: EvidenceThreadProvider,
) -> ValidatedEvidence:
    """Return an in-memory cache view without mutating the evidence ZIP."""

    if evidence.trajectory is not None:
        return evidence
    source = evidence.manifest.source
    if source.provider_id != provider.provider_id:
        return evidence
    resolved = ResolvedThread(
        provider_id=source.provider_id,
        adapter_id=source.adapter_id,
        source_format=source.source_format,
        thread_id=source.thread_id,
        source_path=Path(evidence.path or "."),
    )
    capture_facts = evidence.manifest.capture
    capture = NativeCaptureResult(
        provider_id=source.provider_id,
        adapter_id=source.adapter_id,
        source_format=source.source_format,
        source_status=source.source_status,
        frames=tuple(entry.as_dict() for entry in evidence.native_index),
        native_bytes=len(evidence.native),
        unknown_remainder=capture_facts.unknown_remainder,
        read_interrupted=capture_facts.read_interrupted,
    )
    try:
        with tempfile.SpooledTemporaryFile(
            max_size=1024 * 1024,
            mode="w+b",
        ) as native:
            native.write(evidence.native)
            trajectory = _derive_trajectory(
                provider,
                resolved,
                capture,
                cast(BinaryIO, native),
            )
        rebuilt = validate_evidence_members(
            evidence.manifest,
            evidence.native,
            evidence.native_index_bytes,
            trajectory,
        )
    except (EvidenceError, SvcError, TrajectoryError, OSError, TypeError, ValueError):
        return evidence
    if rebuilt.trajectory is None:
        return evidence
    return ValidatedEvidence(
        manifest=rebuilt.manifest,
        native=rebuilt.native,
        native_index=rebuilt.native_index,
        trajectory=rebuilt.trajectory,
        evidence_id=rebuilt.evidence_id,
        path=evidence.path,
        _native_index_bytes=rebuilt.native_index_bytes,
    )


__all__ = [
    "rebuild_evidence_trajectory",
    "write_agent_thread_evidence",
]
