"""Evidence bundle v4 with a required trajectory and source-faithful materials."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
from typing import Annotated, Any, BinaryIO, Literal, Mapping
import zipfile

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from .agent_threads import MAX_SOURCE_BYTES
from .evidence import EvidenceError
from .trajectory import canonical_json_bytes
from .trajectory_v2 import ValidatedTrajectoryV2, validate_trajectory_v2


EVIDENCE_SCHEMA_VERSION_V4 = 4
EVIDENCE_FORMAT_V4 = "svc-agent-thread-evidence"
TRAJECTORY_MEMBER = "trajectory.jsonl"
_IDENTITY_DOMAIN = b"svc-agent-thread-evidence-id\x00v4\x00"
_NonNegativeInt = Annotated[int, Field(ge=0)]


class EvidenceV4Model(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)


class MaterialDescriptor(EvidenceV4Model):
    name: str
    kind: Literal["native", "blob"]
    media_type: str = Field(min_length=1)
    bytes: _NonNegativeInt
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        path = PurePosixPath(value)
        if (
            path.is_absolute()
            or ".." in path.parts
            or not value.startswith(("native/", "blob/"))
        ):
            raise ValueError("material name must be a safe native/ or blob/ path")
        return value


class TrajectoryDescriptor(EvidenceV4Model):
    name: Literal["trajectory.jsonl"]
    bytes: _NonNegativeInt
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class CollectionGap(EvidenceV4Model):
    code: str = Field(min_length=1)
    object_id: str = Field(min_length=1)
    affected_domains: tuple[str, ...] = Field(min_length=1)


class EvidenceV4Manifest(EvidenceV4Model):
    format: Literal["svc-agent-thread-evidence"]
    schema_version: Literal[4]
    evidence_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    provider_id: str = Field(min_length=1)
    source_format: str = Field(min_length=1)
    selected_roots: tuple[str, ...] = Field(min_length=1)
    trajectory: TrajectoryDescriptor
    materials: tuple[MaterialDescriptor, ...] = Field(min_length=1)
    gaps: tuple[CollectionGap, ...] = ()


@dataclass(frozen=True, slots=True)
class ValidatedEvidenceV4:
    manifest: EvidenceV4Manifest
    trajectory: ValidatedTrajectoryV2
    materials: Mapping[str, bytes]
    evidence_id: str
    path: Path | None = None


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _frame(name: str, value: bytes) -> bytes:
    encoded = name.encode("utf-8")
    return (
        len(encoded).to_bytes(4, "big")
        + encoded
        + len(value).to_bytes(8, "big")
        + value
    )


def build_evidence_v4_id(
    *,
    provider_id: str,
    source_format: str,
    selected_roots: tuple[str, ...],
    trajectory: bytes,
    materials: Mapping[str, bytes],
) -> str:
    digest = hashlib.sha256(_IDENTITY_DOMAIN)
    identity_header = canonical_json_bytes(
        {
            "provider_id": provider_id,
            "selected_roots": selected_roots,
            "source_format": source_format,
        }
    )
    digest.update(_frame("identity.json", identity_header))
    digest.update(_frame(TRAJECTORY_MEMBER, trajectory))
    for name in sorted(materials):
        digest.update(_frame(name, materials[name]))
    return digest.hexdigest()


def build_evidence_v4_manifest(
    *,
    provider_id: str,
    source_format: str,
    selected_roots: tuple[str, ...],
    trajectory: bytes,
    materials: Mapping[str, bytes],
    material_kinds: Mapping[str, Literal["native", "blob"]] | None = None,
    material_media_types: Mapping[str, str] | None = None,
    gaps: tuple[CollectionGap, ...] = (),
) -> EvidenceV4Manifest:
    validate_trajectory_v2(trajectory)
    if not materials:
        raise EvidenceError(
            "invalid-evidence-manifest", "Evidence v4 requires native material."
        )
    kinds = material_kinds or {}
    media_types = material_media_types or {}
    descriptors = tuple(
        MaterialDescriptor(
            name=name,
            kind=kinds.get(name, "native"),
            media_type=media_types.get(name, "application/octet-stream"),
            bytes=len(value),
            sha256=_sha256(value),
        )
        for name, value in sorted(materials.items())
    )
    return EvidenceV4Manifest(
        format=EVIDENCE_FORMAT_V4,
        schema_version=EVIDENCE_SCHEMA_VERSION_V4,
        evidence_id=build_evidence_v4_id(
            provider_id=provider_id,
            source_format=source_format,
            selected_roots=selected_roots,
            trajectory=trajectory,
            materials=materials,
        ),
        provider_id=provider_id,
        source_format=source_format,
        selected_roots=selected_roots,
        trajectory=TrajectoryDescriptor(
            name=TRAJECTORY_MEMBER,
            bytes=len(trajectory),
            sha256=_sha256(trajectory),
        ),
        materials=descriptors,
        gaps=gaps,
    )


def validate_evidence_v4_members(
    manifest: EvidenceV4Manifest | Mapping[str, Any],
    trajectory: bytes,
    materials: Mapping[str, bytes],
) -> ValidatedEvidenceV4:
    try:
        typed = (
            manifest
            if isinstance(manifest, EvidenceV4Manifest)
            else EvidenceV4Manifest.model_validate(manifest)
        )
    except ValidationError as error:
        raise EvidenceError(
            "invalid-evidence-manifest",
            "Evidence v4 manifest is invalid.",
            {"errors": error.errors(include_url=False)},
        ) from error
    trajectory_model = validate_trajectory_v2(trajectory)
    expected_names = [item.name for item in typed.materials]
    if len(expected_names) != len(set(expected_names)) or set(expected_names) != set(
        materials
    ):
        raise EvidenceError(
            "bundle-invalid", "Evidence v4 material set disagrees with its manifest."
        )
    if typed.trajectory.bytes != len(trajectory) or typed.trajectory.sha256 != _sha256(
        trajectory
    ):
        raise EvidenceError(
            "integrity-failed", "Evidence v4 trajectory integrity check failed."
        )
    descriptors = {item.name: item for item in typed.materials}
    for name, value in materials.items():
        descriptor = descriptors[name]
        if descriptor.bytes != len(value) or descriptor.sha256 != _sha256(value):
            raise EvidenceError(
                "integrity-failed",
                "Evidence v4 material integrity check failed.",
                {"material": name},
            )
    calculated = build_evidence_v4_id(
        provider_id=typed.provider_id,
        source_format=typed.source_format,
        selected_roots=typed.selected_roots,
        trajectory=trajectory,
        materials=materials,
    )
    if calculated != typed.evidence_id:
        raise EvidenceError("integrity-failed", "Evidence v4 identity check failed.")
    known_materials = set(materials)
    for execution in trajectory_model.executions:
        for source_ref in execution.source_refs:
            if source_ref.material not in known_materials:
                raise EvidenceError(
                    "native-reference-unresolved",
                    "Execution source ref does not resolve.",
                )
    for event in trajectory_model.events:
        for source_ref in event.source_refs:
            if source_ref.material not in known_materials:
                raise EvidenceError(
                    "native-reference-unresolved", "Event source ref does not resolve."
                )
    return ValidatedEvidenceV4(
        typed, trajectory_model, dict(materials), typed.evidence_id
    )


def _zip_info(name: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.create_system = 3
    info.external_attr = (0o644 & 0xFFFF) << 16
    return info


def write_evidence_v4_stream(
    output: BinaryIO,
    manifest: EvidenceV4Manifest | Mapping[str, Any],
    trajectory: bytes,
    materials: Mapping[str, bytes],
) -> ValidatedEvidenceV4:
    validated = validate_evidence_v4_members(manifest, trajectory, materials)
    output.seek(0)
    output.truncate(0)
    with zipfile.ZipFile(
        output, "w", compression=zipfile.ZIP_DEFLATED, allowZip64=True
    ) as archive:
        archive.writestr(
            _zip_info("manifest.json"),
            canonical_json_bytes(validated.manifest, newline=True),
        )
        archive.writestr(_zip_info(TRAJECTORY_MEMBER), trajectory)
        for name in sorted(materials):
            archive.writestr(_zip_info(name), materials[name])
    output.flush()
    return validated


def evidence_v4_bytes(
    manifest: EvidenceV4Manifest,
    trajectory: bytes,
    materials: Mapping[str, bytes],
) -> bytes:
    stream = io.BytesIO()
    write_evidence_v4_stream(stream, manifest, trajectory, materials)
    return stream.getvalue()


def validate_evidence_v4(path: Path) -> ValidatedEvidenceV4:
    try:
        with zipfile.ZipFile(path, "r") as archive:
            infos = archive.infolist()
            names = [item.filename for item in infos]
            if (
                len(names) != len(set(names))
                or "manifest.json" not in names
                or TRAJECTORY_MEMBER not in names
            ):
                raise EvidenceError(
                    "bundle-invalid", "Evidence v4 ZIP members are invalid."
                )
            by_name = {item.filename: item for item in infos}
            if any(item.file_size > MAX_SOURCE_BYTES for item in infos):
                raise EvidenceError(
                    "member-limit-reached", "Evidence v4 member is too large."
                )
            manifest = EvidenceV4Manifest.model_validate_json(
                archive.read("manifest.json")
            )
            allowed = {
                "manifest.json",
                TRAJECTORY_MEMBER,
                *(item.name for item in manifest.materials),
            }
            if set(names) != allowed:
                raise EvidenceError(
                    "bundle-invalid", "Evidence v4 ZIP contains undeclared members."
                )
            trajectory = archive.read(TRAJECTORY_MEMBER)
            materials = {
                item.name: archive.read(by_name[item.name])
                for item in manifest.materials
            }
        validated = validate_evidence_v4_members(manifest, trajectory, materials)
        return ValidatedEvidenceV4(
            validated.manifest,
            validated.trajectory,
            validated.materials,
            validated.evidence_id,
            Path(path),
        )
    except EvidenceError:
        raise
    except (
        OSError,
        ValueError,
        ValidationError,
        zipfile.BadZipFile,
        json.JSONDecodeError,
    ) as error:
        raise EvidenceError("bundle-invalid", "Evidence v4 ZIP is invalid.") from error


__all__ = [
    "CollectionGap",
    "EVIDENCE_SCHEMA_VERSION_V4",
    "EvidenceV4Manifest",
    "MaterialDescriptor",
    "ValidatedEvidenceV4",
    "build_evidence_v4_manifest",
    "evidence_v4_bytes",
    "validate_evidence_v4",
    "validate_evidence_v4_members",
    "write_evidence_v4_stream",
]
