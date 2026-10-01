from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Protocol, cast


class _BuildContext(Protocol):
    root: str | Path
    build_dir: str | Path
    target: str


class _CatalogProjection(Protocol):
    def canonical_documents(self, source_root: Path) -> list[tuple[str, Path]]: ...

    def build_projection(
        self, source_root: Path, output_dir: Path
    ) -> dict[str, Path]: ...


def _catalog_module(root: Path) -> _CatalogProjection:
    source_root = root / "src"
    expected = (source_root / "svc_cli" / "catalog.py").resolve()
    sys.path.insert(0, str(source_root))
    module = importlib.import_module("svc_cli.catalog")
    actual = Path(module.__file__ or "").resolve()
    if actual != expected:
        raise RuntimeError(
            f"SVC build imported catalog projection from {actual}, expected {expected}"
        )
    return cast(_CatalogProjection, module)


def _corpus_root(member_root: Path) -> Path:
    candidates = (
        member_root / "_build_inputs" / "corpus",
        member_root.parent / "corpus",
    )
    for candidate in candidates:
        if candidate.is_dir() and (candidate / "version.json").is_file():
            return candidate
    raise FileNotFoundError("Canonical SVC Corpus build input is unavailable")


def pdm_build_update_files(
    context: _BuildContext, files: dict[str, Path]
) -> None:
    """Carry canonical Corpus inputs through sdist and project them into wheels."""

    if context.target not in {"sdist", "wheel"}:
        return
    member_root = Path(context.root)
    catalog_module = _catalog_module(member_root)
    source_root = _corpus_root(member_root)
    if context.target == "sdist":
        files["_build_inputs/corpus/version.json"] = source_root / "version.json"
        for relative, source in catalog_module.canonical_documents(source_root):
            files[f"_build_inputs/corpus/{relative}"] = source
        return
    output_dir = Path(context.build_dir) / "svc_cli" / "data"
    files.update(catalog_module.build_projection(source_root, output_dir))
