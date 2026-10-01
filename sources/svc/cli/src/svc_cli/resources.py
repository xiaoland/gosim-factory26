"""Read-only access to the wheel corpus, with a source-tree development fallback."""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path, PurePosixPath
from typing import Literal, Protocol

from .catalog import build_catalog_bytes, normalized_document_path


class Resource(Protocol):
    def is_file(self) -> bool: ...

    def joinpath(self, *descendants: str): ...

    def read_bytes(self) -> bytes: ...


def source_root() -> Path:
    member_root = Path(__file__).resolve().parents[2]
    candidates = (
        member_root.parent / "corpus",
        member_root / "_build_inputs" / "corpus",
    )
    for candidate in candidates:
        if candidate.is_dir() and (candidate / "version.json").is_file():
            return candidate
    raise FileNotFoundError("SVC source fallback is unavailable")


def _packaged_data_root() -> Resource | None:
    packaged = files("svc_cli").joinpath("data")
    if packaged.joinpath("catalog.json").is_file():
        return packaged
    return None


def resource_mode() -> Literal["wheel", "source"]:
    return "wheel" if _packaged_data_root() is not None else "source"


def read_catalog_bytes() -> bytes:
    packaged = _packaged_data_root()
    if packaged is not None:
        return packaged.joinpath("catalog.json").read_bytes()

    return build_catalog_bytes(source_root())


def read_document(path: str) -> bytes:
    normalized = normalized_document_path(path)
    packaged = _packaged_data_root()
    if packaged is not None:
        resource = packaged.joinpath("corpus", *PurePosixPath(normalized).parts)
        if not resource.is_file():
            raise FileNotFoundError(
                f"Packaged SVC document does not exist: {normalized}"
            )
        return resource.read_bytes()

    source = source_root() / PurePosixPath(normalized)
    if not source.is_file():
        raise FileNotFoundError(f"SVC source document does not exist: {normalized}")
    return source.read_bytes()
