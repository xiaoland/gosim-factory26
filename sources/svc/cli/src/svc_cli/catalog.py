"""Validated Corpus release facts and the packaged document catalog."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

from semantic_version import Version  # type: ignore[import-untyped]


CATALOG_SCHEMA_VERSION = 2
CORPUS_VERSION_SCHEMA_VERSION = 2
AUTHORING_ONLY_DOCUMENT = "AGENTS.md"
TITLE_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def canonical_json(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def require_semver(value: object, label: str) -> str:
    """Return one exact stable SemVer string without coercion."""

    if not isinstance(value, str):
        raise ValueError(f"{label} must be stable x.y.z SemVer: {value!r}")
    try:
        parsed = Version(value)
    except ValueError as error:
        raise ValueError(f"{label} must be stable x.y.z SemVer: {value!r}") from error
    if parsed.prerelease or parsed.build or str(parsed) != value:
        raise ValueError(f"{label} must be stable x.y.z SemVer: {value!r}")
    return value


def normalized_document_path(value: object, label: str = "document path") -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a non-empty normalized relative path")
    path = PurePosixPath(value)
    if (
        path.is_absolute()
        or "." in path.parts
        or ".." in path.parts
        or any(part.startswith(".") for part in path.parts)
        or path.suffix != ".md"
    ):
        raise ValueError(
            f"{label} must be a visible normalized Markdown path: {value!r}"
        )
    normalized = path.as_posix()
    if normalized != value:
        raise ValueError(f"{label} must use normalized POSIX separators: {value!r}")
    return normalized


def normalized_migration_path(value: object) -> str:
    path = normalized_document_path(value, "Corpus migration guide path")
    if not path.startswith("migrations/"):
        raise ValueError(
            f"Corpus migration guide path must be under migrations/: {value!r}"
        )
    return path


def title_from_markdown(content: bytes, fallback_path: str) -> str:
    text = content.decode("utf-8")
    match = TITLE_RE.search(text)
    if match:
        return match.group(1).rstrip("#").strip()
    return PurePosixPath(fallback_path).stem.replace("-", " ")


@dataclass(frozen=True)
class CorpusMigration:
    """Closed migration disposition for one Corpus release."""

    status: str
    paths: tuple[str, ...] = ()

    @classmethod
    def from_mapping(cls, raw: object) -> "CorpusMigration":
        if not isinstance(raw, dict):
            raise ValueError("Corpus release migration must be an object")
        status = raw.get("status")
        if status == "not-required":
            if set(raw) != {"status"}:
                raise ValueError("not-required Corpus migration has unsupported fields")
            return cls(status)
        if status != "guide":
            raise ValueError("Corpus migration status must be guide or not-required")
        if set(raw) != {"status", "paths"}:
            raise ValueError("guide Corpus migration has unsupported fields")
        paths_raw = raw.get("paths")
        if not isinstance(paths_raw, list) or not paths_raw:
            raise ValueError("guide Corpus migration must name at least one path")
        paths = tuple(normalized_migration_path(path) for path in paths_raw)
        if len(paths) != len(set(paths)):
            raise ValueError("Corpus migration guide paths must be unique")
        return cls(status, paths)

    def as_dict(self) -> dict[str, object]:
        if self.status == "not-required":
            return {"status": self.status}
        return {"status": self.status, "paths": list(self.paths)}


@dataclass(frozen=True)
class CorpusRelease:
    """One stable hop in the retained Corpus release chain."""

    version: str
    previous_version: str
    migration: CorpusMigration

    @classmethod
    def from_mapping(cls, raw: object) -> "CorpusRelease":
        if not isinstance(raw, dict):
            raise ValueError("Every Corpus release must be an object")
        if set(raw) != {"version", "previous_version", "migration"}:
            raise ValueError("Corpus release has unsupported fields")
        return cls(
            require_semver(raw.get("version"), "Corpus release version"),
            require_semver(raw.get("previous_version"), "Corpus previous version"),
            CorpusMigration.from_mapping(raw.get("migration")),
        )

    def as_dict(self) -> dict[str, object]:
        return {
            "version": self.version,
            "previous_version": self.previous_version,
            "migration": self.migration.as_dict(),
        }


@dataclass(frozen=True)
class CorpusVersionIndex:
    """Canonical source-owned Corpus release chain."""

    schema_version: int
    corpus_version: str
    releases: tuple[CorpusRelease, ...]

    @property
    def supported_anchor(self) -> str:
        return (
            self.releases[0].previous_version if self.releases else self.corpus_version
        )

    @classmethod
    def from_mapping(cls, raw: object) -> "CorpusVersionIndex":
        if not isinstance(raw, dict):
            raise ValueError("Corpus version index must be a JSON object")
        if raw.get("schema_version") != CORPUS_VERSION_SCHEMA_VERSION:
            raise ValueError(
                "Unsupported Corpus version index schema: "
                f"{raw.get('schema_version')!r}"
            )
        if set(raw) != {"schema_version", "corpus_version", "releases"}:
            raise ValueError("Corpus version index has unsupported fields")
        corpus_version = require_semver(raw.get("corpus_version"), "Corpus version")
        releases_raw = raw.get("releases")
        if not isinstance(releases_raw, list):
            raise ValueError("Corpus version index releases must be a list")
        releases = tuple(CorpusRelease.from_mapping(item) for item in releases_raw)
        previous = releases[0].previous_version if releases else corpus_version
        seen = {previous}
        for release in releases:
            if release.previous_version != previous:
                raise ValueError(
                    "Corpus release chain is not contiguous at "
                    f"{release.version}: expected previous_version {previous}"
                )
            if Version(release.version) <= Version(release.previous_version):
                raise ValueError(
                    f"Corpus release {release.version} must advance "
                    f"{release.previous_version}"
                )
            if release.version in seen:
                raise ValueError(
                    f"Corpus release chain repeats version {release.version}"
                )
            seen.add(release.version)
            previous = release.version
        if previous != corpus_version:
            raise ValueError("Corpus version must match the last release")
        return cls(CORPUS_VERSION_SCHEMA_VERSION, corpus_version, releases)

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "corpus_version": self.corpus_version,
            "releases": [release.as_dict() for release in self.releases],
        }


def parse_version_index(content: bytes) -> CorpusVersionIndex:
    try:
        raw = json.loads(content)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("Corpus version index must be valid UTF-8 JSON") from error
    return CorpusVersionIndex.from_mapping(raw)


@dataclass(frozen=True)
class CatalogEntry:
    """One canonical Markdown document, addressed by its source-relative path."""

    path: str
    title: str
    sha256: str

    @classmethod
    def from_mapping(cls, raw: object) -> "CatalogEntry":
        if not isinstance(raw, dict):
            raise ValueError("Every catalog entry must be an object")
        path = normalized_document_path(raw.get("path"))
        title = raw.get("title")
        digest = raw.get("sha256")
        if not isinstance(title, str) or not title.strip():
            raise ValueError(f"Catalog entry {path} needs a title")
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError(f"Catalog entry {path} has an invalid sha256")
        if set(raw) != {"path", "title", "sha256"}:
            raise ValueError(f"Catalog entry {path} has unsupported fields")
        return cls(path=path, title=title, sha256=digest)

    def as_dict(self) -> dict[str, str]:
        return {"path": self.path, "title": self.title, "sha256": self.sha256}


@dataclass(frozen=True)
class Catalog:
    """Packaged Corpus release facts plus integrity-checked document addresses."""

    schema_version: int
    corpus_version: str
    releases: tuple[CorpusRelease, ...]
    entries: tuple[CatalogEntry, ...]

    @property
    def version_index(self) -> CorpusVersionIndex:
        return CorpusVersionIndex(
            CORPUS_VERSION_SCHEMA_VERSION, self.corpus_version, self.releases
        )

    @classmethod
    def from_mapping(cls, raw: object) -> "Catalog":
        if not isinstance(raw, dict):
            raise ValueError("Catalog must be a JSON object")
        if raw.get("schema_version") != CATALOG_SCHEMA_VERSION:
            raise ValueError(
                f"Unsupported catalog schema: {raw.get('schema_version')!r}"
            )
        if set(raw) != {
            "schema_version",
            "corpus_version",
            "releases",
            "entries",
        }:
            raise ValueError("Catalog has unsupported fields")
        version = require_semver(raw.get("corpus_version"), "catalog corpus_version")
        index = CorpusVersionIndex.from_mapping(
            {
                "schema_version": CORPUS_VERSION_SCHEMA_VERSION,
                "corpus_version": version,
                "releases": raw.get("releases"),
            }
        )
        entries_raw = raw.get("entries")
        if not isinstance(entries_raw, list) or not entries_raw:
            raise ValueError("Catalog must contain at least one entry")
        entries = tuple(CatalogEntry.from_mapping(item) for item in entries_raw)
        paths = tuple(entry.path for entry in entries)
        if len(paths) != len(set(paths)):
            raise ValueError("Catalog document paths must be unique")
        if paths != tuple(sorted(paths)):
            raise ValueError("Catalog entries must be path-sorted")
        _require_guide_entries(index, set(paths))
        return cls(CATALOG_SCHEMA_VERSION, version, index.releases, entries)

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "corpus_version": self.corpus_version,
            "releases": [release.as_dict() for release in self.releases],
            "entries": [entry.as_dict() for entry in self.entries],
        }


def _require_guide_entries(index: CorpusVersionIndex, documents: set[str]) -> None:
    for release in index.releases:
        for path in release.migration.paths:
            if path not in documents:
                raise ValueError(
                    f"Corpus release {release.version} references missing guide {path}"
                )


def catalog_bytes(
    version_index: CorpusVersionIndex,
    documents: Iterable[tuple[str, bytes]],
) -> bytes:
    """Build canonical catalog bytes without copying Markdown bodies into it."""

    entries = []
    for path, content in documents:
        normalized = normalized_document_path(path)
        entries.append(
            CatalogEntry(
                path=normalized,
                title=title_from_markdown(content, normalized),
                sha256=sha256_bytes(content),
            )
        )
    paths = [entry.path for entry in entries]
    if len(paths) != len(set(paths)):
        raise ValueError("Catalog document paths must be unique")
    _require_guide_entries(version_index, set(paths))
    catalog = Catalog(
        CATALOG_SCHEMA_VERSION,
        version_index.corpus_version,
        version_index.releases,
        tuple(sorted(entries, key=lambda item: item.path)),
    )
    return canonical_json(catalog.as_dict())


def parse_catalog(content: bytes) -> Catalog:
    try:
        raw = json.loads(content)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("Catalog must be valid UTF-8 JSON") from error
    return Catalog.from_mapping(raw)


def canonical_documents(source_root: Path) -> list[tuple[str, Path]]:
    """Return canonical Markdown, excluding only root authoring instructions."""

    root = source_root.resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"Canonical SVC source does not exist: {source_root}")

    authoring_document = root / AUTHORING_ONLY_DOCUMENT
    if authoring_document.is_symlink():
        raise ValueError(
            "Canonical source authoring instructions may not be a symlink: "
            f"{authoring_document}"
        )
    if authoring_document.exists() and not authoring_document.is_file():
        raise ValueError(
            "Canonical source authoring instructions must be a regular file: "
            f"{authoring_document}"
        )

    documents: list[tuple[str, Path]] = []
    for path in sorted(root.rglob("*.md")):
        if path.is_symlink():
            raise ValueError(
                f"Canonical source may not contain a symlinked Markdown document: {path}"
            )
        if not path.is_file():
            continue
        resolved = path.resolve()
        try:
            relative = resolved.relative_to(root).as_posix()
        except ValueError as error:
            raise ValueError(
                f"Canonical source escapes Corpus root/: {path}"
            ) from error
        if relative == AUTHORING_ONLY_DOCUMENT:
            continue
        documents.append((normalized_document_path(relative), resolved))
    if not documents:
        raise ValueError("Canonical SVC source contains no Markdown documents")
    return documents


def read_version_index(source_root: Path) -> CorpusVersionIndex:
    version_path = source_root / "version.json"
    if not version_path.is_file():
        raise FileNotFoundError(f"Corpus version index does not exist: {version_path}")
    return parse_version_index(version_path.read_bytes())


def build_catalog_bytes(source_root: Path) -> bytes:
    documents = canonical_documents(source_root)
    return catalog_bytes(
        read_version_index(source_root),
        ((relative, path.read_bytes()) for relative, path in documents),
    )


def build_projection(source_root: Path, output_dir: Path) -> dict[str, Path]:
    """Build the exact derived Corpus/catalog mapping for an installed wheel."""

    documents = canonical_documents(source_root)
    catalog = catalog_bytes(
        read_version_index(source_root),
        ((relative, path.read_bytes()) for relative, path in documents),
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    catalog_path = output_dir / "catalog.json"
    catalog_path.write_bytes(catalog)

    files: dict[str, Path] = {"svc_cli/data/catalog.json": catalog_path}
    for relative, source in documents:
        files[f"svc_cli/data/corpus/{relative}"] = source
    return files
