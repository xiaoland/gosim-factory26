"""Schema-v3 native evidence authority and optional trajectory cache.

The required bundle members are deliberately small: a manifest identifies the
capture, ``native.bin`` is the captured authority, and ``native-index.jsonl``
frames those exact bytes.  ``trajectory.jsonl`` is an optional derived cache;
its absence or invalidity never weakens the native evidence core.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
import re
from types import MappingProxyType
from typing import Annotated, Any, BinaryIO, Iterable, Literal, Mapping, Never
import zipfile

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from .agent_threads import MAX_SOURCE_BYTES
from .trajectory import (
    TrajectoryError,
    ValidatedTrajectory,
    canonical_json_bytes,
    validate_trajectory_bytes,
)


EVIDENCE_FORMAT = "svc-agent-thread-evidence"
EVIDENCE_SCHEMA_VERSION = 3
EVIDENCE_MEMBERS = (
    "manifest.json",
    "native.bin",
    "native-index.jsonl",
)
EVIDENCE_OPTIONAL_MEMBERS = ("trajectory.jsonl",)

_EVIDENCE_ID_DOMAIN = b"svc-agent-thread-evidence-id\x00v3\x00"
_SOURCE_ID_PATTERN = r"^[a-z][a-z0-9_-]{0,63}$"
_FORBIDDEN_THREAD_CONTROL = re.compile(r"[\x00-\x1f\x7f]")


class EvidenceError(ValueError):
    """Stable schema-v3 evidence failure."""

    def __init__(
        self,
        code: str,
        message: str,
        details: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = MappingProxyType(dict(details or {}))

    def as_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"code": self.code, "message": self.message}
        if self.details:
            result["details"] = dict(self.details)
        return result


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)


class EvidenceSource(_StrictModel):
    """Provider-native identity retained independently of derived caches."""

    provider_id: str = Field(pattern=_SOURCE_ID_PATTERN)
    adapter_id: str = Field(pattern=_SOURCE_ID_PATTERN)
    source_format: str = Field(pattern=_SOURCE_ID_PATTERN)
    thread_id: str = Field(min_length=1, max_length=512)
    source_status: Literal["stable", "grew", "changed"]

    @field_validator("thread_id")
    @classmethod
    def validate_thread_id(cls, value: str) -> str:
        if not value.strip() or _FORBIDDEN_THREAD_CONTROL.search(value):
            raise ValueError("thread_id must be non-blank, control-free text")
        try:
            value.encode("utf-8")
        except UnicodeEncodeError as error:
            raise ValueError("thread_id must be UTF-8 text") from error
        return value


class EvidenceCapture(_StrictModel):
    """Bounded facts about the retained native capture."""

    status: Literal["complete", "partial"]
    unknown_remainder: bool
    read_interrupted: bool


class EvidenceManifest(_StrictModel):
    """The complete schema-v3 manifest authority."""

    format: Literal["svc-agent-thread-evidence"]
    schema_version: Literal[3]
    evidence_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    source: EvidenceSource
    capture: EvidenceCapture


_NonNegativeInt = Annotated[int, Field(ge=0)]


class SourceCoordinate(_StrictModel):
    """Provider coordinate for the start of one native frame."""

    event_index: _NonNegativeInt
    line: _NonNegativeInt
    byte_offset: _NonNegativeInt


class NativeIndexEntry(_StrictModel):
    """One contiguous frame in ``native.bin``.

    ``native_index`` is an in-memory convenience derived from the validated
    record ID.  It is intentionally absent from the wire representation.
    """

    native_record_id: str = Field(pattern=r"^n[0-9]{6,}$")
    byte_start: _NonNegativeInt
    byte_end: _NonNegativeInt
    frame_status: Literal["complete", "incomplete"]
    source_coordinate: SourceCoordinate

    @property
    def native_index(self) -> int:
        return int(self.native_record_id[1:])

    def as_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


@dataclass(frozen=True, slots=True)
class ValidatedEvidence:
    """Validated native authority plus an optional reusable cache."""

    manifest: EvidenceManifest
    native: bytes
    native_index: tuple[NativeIndexEntry, ...]
    trajectory: ValidatedTrajectory | None
    evidence_id: str
    path: Any = None
    _native_index_bytes: bytes = field(default=b"", repr=False)

    @property
    def native_bytes(self) -> bytes:
        return self.native

    @property
    def native_index_bytes(self) -> bytes:
        if self._native_index_bytes:
            return self._native_index_bytes
        return encode_native_index(self.native_index)


def _fail(code: str, message: str, **details: Any) -> Never:
    raise EvidenceError(code, message, details)


def _json_loads(value: bytes) -> Any:
    try:
        return json.loads(value.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise EvidenceError(
            "invalid-evidence-json",
            "Evidence member is not UTF-8 JSON.",
        ) from error


def _coerce_bytes(
    value: bytes | bytearray | memoryview,
    *,
    name: str,
) -> bytes:
    if not isinstance(value, (bytes, bytearray, memoryview)):
        _fail("invalid-evidence-member", f"{name} must be bytes.")
    return bytes(value)


def _manifest_error(error: ValidationError) -> EvidenceError:
    return EvidenceError(
        "invalid-evidence-manifest",
        "Evidence manifest has an invalid shape or value.",
        {"errors": error.error_count()},
    )


def _index_error(error: ValidationError) -> EvidenceError:
    return EvidenceError(
        "invalid-native-index",
        "Native index entry has an invalid shape or value.",
        {"errors": error.error_count()},
    )


def _source(value: EvidenceSource | Mapping[str, Any]) -> EvidenceSource:
    try:
        return EvidenceSource.model_validate(value)
    except ValidationError as error:
        raise _manifest_error(error) from error


def _capture(value: EvidenceCapture | Mapping[str, Any]) -> EvidenceCapture:
    try:
        return EvidenceCapture.model_validate(value)
    except ValidationError as error:
        raise _manifest_error(error) from error


def _entry_from_mapping(value: Any) -> NativeIndexEntry:
    try:
        return NativeIndexEntry.model_validate(value)
    except ValidationError as error:
        raise _index_error(error) from error


def _validate_index_sequence(
    entries: tuple[NativeIndexEntry, ...],
    *,
    native_size: int,
) -> None:
    expected_start = 0
    for ordinal, entry in enumerate(entries):
        if entry.native_record_id != f"n{ordinal:06d}":
            _fail(
                "invalid-native-index",
                "Native record IDs must be contiguous and ordinal.",
            )
        if (
            entry.byte_start != expected_start
            or entry.byte_end <= entry.byte_start
            or entry.byte_end > native_size
        ):
            _fail(
                "invalid-native-index",
                "Native byte ranges must exactly and contiguously cover native content.",
            )
        if entry.frame_status == "incomplete" and ordinal != len(entries) - 1:
            _fail(
                "invalid-native-index",
                "Only the final native frame may be incomplete.",
            )
        expected_start = entry.byte_end
    if expected_start != native_size:
        _fail(
            "invalid-native-index",
            "Native index does not cover every retained native byte.",
        )


def encode_native_index(
    entries: Iterable[NativeIndexEntry | Mapping[str, Any]],
) -> bytes:
    """Encode an exact-shape native index as canonical JSONL."""

    materialized = tuple(
        entry if isinstance(entry, NativeIndexEntry) else _entry_from_mapping(entry)
        for entry in entries
    )
    native_size = materialized[-1].byte_end if materialized else 0
    _validate_index_sequence(materialized, native_size=native_size)
    data = b"".join(
        canonical_json_bytes(entry.as_dict(), newline=True) for entry in materialized
    )
    return data


def build_native_index(
    native: bytes,
    frames: Iterable[Mapping[str, Any] | tuple[int, int, Mapping[str, int], str]],
) -> bytes:
    """Build a native index while deriving contiguous record IDs."""

    native_bytes = _coerce_bytes(native, name="native")
    if len(native_bytes) > MAX_SOURCE_BYTES:
        _fail("source-limit-reached", "Native source byte bound exceeded.")
    entries: list[NativeIndexEntry] = []
    for ordinal, frame in enumerate(frames):
        if isinstance(frame, Mapping):
            allowed = {
                "native_record_id",
                "byte_start",
                "byte_end",
                "frame_status",
                "source_coordinate",
            }
            if not set(frame) <= allowed:
                _fail(
                    "invalid-native-index",
                    "Native frame contains unsupported fields.",
                )
            value = {
                "native_record_id": frame.get(
                    "native_record_id",
                    f"n{ordinal:06d}",
                ),
                "byte_start": frame.get("byte_start"),
                "byte_end": frame.get("byte_end"),
                "frame_status": frame.get("frame_status", "complete"),
                "source_coordinate": frame.get("source_coordinate"),
            }
        else:
            if len(frame) != 4:
                _fail(
                    "invalid-native-index",
                    "Frame tuple must contain start, end, coordinate, and status.",
                )
            start, end, coordinate, status = frame
            value = {
                "native_record_id": f"n{ordinal:06d}",
                "byte_start": start,
                "byte_end": end,
                "frame_status": status,
                "source_coordinate": coordinate,
            }
        entries.append(_entry_from_mapping(value))
    materialized = tuple(entries)
    _validate_index_sequence(materialized, native_size=len(native_bytes))
    return encode_native_index(materialized)


def _parse_native_index(data: bytes) -> tuple[NativeIndexEntry, ...]:
    if not data:
        return ()
    lines = data.split(b"\n")
    if lines[-1] == b"":
        lines.pop()
    entries: list[NativeIndexEntry] = []
    for line in lines:
        if line.endswith(b"\r"):
            line = line[:-1]
        if not line:
            _fail("invalid-native-index", "Native index cannot contain blank lines.")
        entries.append(_entry_from_mapping(_json_loads(line)))
    return tuple(entries)


def _validate_native_index(
    native: bytes,
    entries: tuple[NativeIndexEntry, ...],
) -> None:
    _validate_index_sequence(entries, native_size=len(native))


def _validate_capture_against_core(
    manifest: EvidenceManifest,
    entries: tuple[NativeIndexEntry, ...],
) -> None:
    capture = manifest.capture
    incomplete = bool(entries and entries[-1].frame_status == "incomplete")
    if (incomplete or capture.read_interrupted) and not capture.unknown_remainder:
        _fail(
            "invalid-evidence-manifest",
            "Incomplete or interrupted capture requires an unknown remainder.",
        )
    is_partial = (
        manifest.source.source_status != "stable"
        or capture.unknown_remainder
        or capture.read_interrupted
        or incomplete
    )
    expected_status = "partial" if is_partial else "complete"
    if capture.status != expected_status:
        _fail(
            "invalid-evidence-manifest",
            "Capture status disagrees with retained core evidence.",
        )


def _validate_trajectory_native_refs(
    trajectory: ValidatedTrajectory,
    entries: tuple[NativeIndexEntry, ...],
) -> None:
    by_id = {entry.native_record_id: entry for entry in entries}
    for record in trajectory.records:
        value = record.model_dump(mode="json", exclude_unset=True)
        source_ref = value.get("source_ref")
        if value.get("type") == "meta":
            if isinstance(source_ref, Mapping) and "native_record_id" in source_ref:
                _fail(
                    "native-reference-invalid",
                    "The synthetic meta record cannot reference a native frame.",
                )
            continue
        if not isinstance(source_ref, Mapping):
            _fail(
                "native-reference-missing",
                "A derived trajectory record is missing its native reference.",
            )
        native_record_id = source_ref.get("native_record_id")
        if not isinstance(native_record_id, str):
            _fail(
                "native-reference-missing",
                "A derived trajectory record is missing its native reference.",
            )
        entry = by_id.get(native_record_id)
        if entry is None:
            _fail(
                "native-reference-unresolved",
                "A derived trajectory native reference does not resolve.",
            )
        if entry.frame_status != "complete":
            _fail(
                "native-reference-incomplete",
                "Derived trajectory records may reference only complete frames.",
            )


def _trajectory_cache(
    trajectory: bytes | None,
    entries: tuple[NativeIndexEntry, ...],
) -> ValidatedTrajectory | None:
    if trajectory is None:
        return None
    try:
        validated = validate_trajectory_bytes(trajectory)
        _validate_trajectory_native_refs(validated, entries)
    except (TrajectoryError, EvidenceError):
        return None
    return validated


def _identity_frame(name: bytes, data: bytes) -> bytes:
    return len(name).to_bytes(4, "big") + name + len(data).to_bytes(8, "big") + data


def build_evidence_id(native: bytes, native_index: bytes) -> str:
    """Bind identity only to the exact native and native-index wire bytes."""

    native_bytes = _coerce_bytes(native, name="native")
    index_bytes = _coerce_bytes(native_index, name="native-index")
    digest = hashlib.sha256()
    digest.update(_EVIDENCE_ID_DOMAIN)
    digest.update(_identity_frame(b"native.bin", native_bytes))
    digest.update(_identity_frame(b"native-index.jsonl", index_bytes))
    return digest.hexdigest()


def build_evidence_manifest(
    *,
    native: bytes,
    native_index: bytes | Iterable[NativeIndexEntry | Mapping[str, Any]],
    source: EvidenceSource | Mapping[str, Any],
    capture: EvidenceCapture | Mapping[str, Any],
) -> EvidenceManifest:
    """Build the small immutable manifest around the native authority."""

    native_bytes = _coerce_bytes(native, name="native")
    if len(native_bytes) > MAX_SOURCE_BYTES:
        _fail("source-limit-reached", "Native source byte bound exceeded.")
    index_bytes = (
        _coerce_bytes(native_index, name="native-index")
        if isinstance(native_index, (bytes, bytearray, memoryview))
        else encode_native_index(native_index)
    )
    entries = _parse_native_index(index_bytes)
    _validate_native_index(native_bytes, entries)
    manifest = EvidenceManifest(
        format="svc-agent-thread-evidence",
        schema_version=3,
        evidence_id=build_evidence_id(native_bytes, index_bytes),
        source=_source(source),
        capture=_capture(capture),
    )
    _validate_capture_against_core(manifest, entries)
    return manifest


def validate_evidence_manifest(
    manifest: EvidenceManifest | Mapping[str, Any],
    *,
    native: bytes | None = None,
    native_index: bytes | None = None,
) -> EvidenceManifest:
    """Validate the manifest and, when supplied, bind it to core bytes."""

    if isinstance(manifest, Mapping):
        legacy_schema = manifest.get("schema_version")
        if type(legacy_schema) is int and legacy_schema in {1, 2}:
            _fail(
                "unsupported-agent-thread-bundle-schema",
                "Schema-v1/v2 bundles require recollection into schema v3.",
            )
    try:
        validated = EvidenceManifest.model_validate(manifest)
    except ValidationError as error:
        raise _manifest_error(error) from error
    if (native is None) != (native_index is None):
        _fail(
            "invalid-evidence-member",
            "Native and native-index bytes must be validated together.",
        )
    if native is None or native_index is None:
        return validated
    native_bytes = _coerce_bytes(native, name="native")
    index_bytes = _coerce_bytes(native_index, name="native-index")
    if len(native_bytes) > MAX_SOURCE_BYTES:
        _fail("source-limit-reached", "Native source byte bound exceeded.")
    entries = _parse_native_index(index_bytes)
    _validate_native_index(native_bytes, entries)
    _validate_capture_against_core(validated, entries)
    if build_evidence_id(native_bytes, index_bytes) != validated.evidence_id:
        _fail(
            "evidence-id-mismatch",
            "Evidence ID does not match the native authority bytes.",
        )
    return validated


def validate_evidence_members(
    manifest: EvidenceManifest | Mapping[str, Any],
    native: bytes,
    native_index: bytes,
    trajectory: bytes | None = None,
) -> ValidatedEvidence:
    """Validate in-memory core members and optionally retain a valid cache."""

    native_bytes = _coerce_bytes(native, name="native")
    index_bytes = _coerce_bytes(native_index, name="native-index")
    trajectory_bytes = (
        None if trajectory is None else _coerce_bytes(trajectory, name="trajectory")
    )
    validated_manifest = validate_evidence_manifest(
        manifest,
        native=native_bytes,
        native_index=index_bytes,
    )
    entries = _parse_native_index(index_bytes)
    validated_trajectory = _trajectory_cache(trajectory_bytes, entries)
    return ValidatedEvidence(
        manifest=validated_manifest,
        native=native_bytes,
        native_index=entries,
        trajectory=validated_trajectory,
        evidence_id=validated_manifest.evidence_id,
        _native_index_bytes=index_bytes,
    )


def _zip_info(name: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.create_system = 3
    info.external_attr = (0o644 & 0xFFFF) << 16
    return info


def _write_member(archive: zipfile.ZipFile, name: str, data: bytes) -> None:
    archive.writestr(_zip_info(name), data)


def write_evidence_stream(
    binary_file: BinaryIO,
    manifest: EvidenceManifest | Mapping[str, Any],
    native: bytes,
    native_index: bytes,
    trajectory: bytes | None = None,
) -> ValidatedEvidence:
    """Write the three core members and, when supplied, one cache member."""

    validated = validate_evidence_members(
        manifest,
        native,
        native_index,
        trajectory,
    )
    manifest_bytes = canonical_json_bytes(
        validated.manifest.model_dump(mode="json"),
        newline=True,
    )
    cache_bytes = (
        validated.trajectory.trajectory_bytes
        if validated.trajectory is not None
        else None
    )
    if (
        len(manifest_bytes) > MAX_SOURCE_BYTES
        or len(validated.native_index_bytes) > MAX_SOURCE_BYTES
        or (cache_bytes is not None and len(cache_bytes) > MAX_SOURCE_BYTES)
    ):
        _fail("member-limit-reached", "Evidence transport bound exceeded.")
    try:
        binary_file.seek(0)
        binary_file.truncate(0)
        with zipfile.ZipFile(
            binary_file,
            mode="w",
            compression=zipfile.ZIP_DEFLATED,
            allowZip64=True,
        ) as archive:
            _write_member(archive, "manifest.json", manifest_bytes)
            _write_member(archive, "native.bin", validated.native)
            _write_member(
                archive,
                "native-index.jsonl",
                validated.native_index_bytes,
            )
            if cache_bytes is not None:
                _write_member(archive, "trajectory.jsonl", cache_bytes)
        binary_file.flush()
    except (OSError, ValueError, zipfile.BadZipFile) as error:
        raise EvidenceError(
            "evidence-write-failed",
            "Evidence ZIP could not be written.",
        ) from error
    return validated


def _read_member(
    archive: zipfile.ZipFile,
    info: zipfile.ZipInfo,
    limit: int,
) -> bytes:
    if info.file_size > limit:
        _fail("member-limit-reached", "Evidence member byte bound exceeded.")
    with archive.open(info, mode="r") as stream:
        data = stream.read(limit + 1)
    if not isinstance(data, bytes) or len(data) > limit:
        _fail("member-limit-reached", "Evidence member byte bound exceeded.")
    return data


def validate_evidence(path: Any) -> ValidatedEvidence:
    """Load a bounded schema-v3 ZIP without requiring canonical encoding."""

    input_path = Path(path)
    try:
        with zipfile.ZipFile(input_path, mode="r") as archive:
            infos = archive.infolist()
            names = [info.filename for info in infos]
            if len(names) != len(set(names)):
                _fail("bundle-invalid", "Evidence ZIP contains duplicate members.")
            by_name = {info.filename: info for info in infos}
            manifest_info = by_name.get("manifest.json")
            if manifest_info is None:
                _fail("bundle-invalid", "Evidence ZIP is missing manifest.json.")
            manifest_bytes = _read_member(
                archive,
                manifest_info,
                MAX_SOURCE_BYTES,
            )
            manifest_value = _json_loads(manifest_bytes)
            if not isinstance(manifest_value, Mapping):
                _fail(
                    "invalid-evidence-manifest",
                    "Evidence manifest must be an object.",
                )
            legacy_schema = manifest_value.get("schema_version")
            if type(legacy_schema) is int and legacy_schema in {1, 2}:
                _fail(
                    "unsupported-agent-thread-bundle-schema",
                    "Schema-v1/v2 bundles require recollection into schema v3.",
                )
            required = set(EVIDENCE_MEMBERS)
            allowed = required | set(EVIDENCE_OPTIONAL_MEMBERS)
            if not required <= set(names) or not set(names) <= allowed:
                _fail(
                    "bundle-invalid",
                    "Evidence ZIP must contain the three core members and only an optional trajectory cache.",
                )
            native = _read_member(
                archive,
                by_name["native.bin"],
                MAX_SOURCE_BYTES,
            )
            native_index = _read_member(
                archive,
                by_name["native-index.jsonl"],
                MAX_SOURCE_BYTES,
            )
            trajectory_info = by_name.get("trajectory.jsonl")
            trajectory = (
                None
                if trajectory_info is None
                or trajectory_info.file_size > MAX_SOURCE_BYTES
                else _read_member(
                    archive,
                    trajectory_info,
                    MAX_SOURCE_BYTES,
                )
            )
            validated = validate_evidence_members(
                manifest_value,
                native,
                native_index,
                trajectory,
            )
            return ValidatedEvidence(
                manifest=validated.manifest,
                native=validated.native,
                native_index=validated.native_index,
                trajectory=validated.trajectory,
                evidence_id=validated.evidence_id,
                path=input_path,
                _native_index_bytes=validated.native_index_bytes,
            )
    except EvidenceError:
        raise
    except (
        EOFError,
        KeyError,
        NotImplementedError,
        OSError,
        RuntimeError,
        ValueError,
        zipfile.BadZipFile,
    ) as error:
        raise EvidenceError(
            "bundle-invalid",
            "Evidence ZIP is not a valid schema-v3 artifact.",
        ) from error


__all__ = [
    "EVIDENCE_FORMAT",
    "EVIDENCE_MEMBERS",
    "EVIDENCE_OPTIONAL_MEMBERS",
    "EVIDENCE_SCHEMA_VERSION",
    "EvidenceCapture",
    "EvidenceError",
    "EvidenceManifest",
    "EvidenceSource",
    "NativeIndexEntry",
    "SourceCoordinate",
    "ValidatedEvidence",
    "build_evidence_id",
    "build_evidence_manifest",
    "build_native_index",
    "encode_native_index",
    "validate_evidence",
    "validate_evidence_manifest",
    "validate_evidence_members",
    "write_evidence_stream",
]
