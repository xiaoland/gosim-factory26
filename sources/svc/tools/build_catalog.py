"""Repository access to the runtime-owned Corpus/catalog projection primitive."""

from __future__ import annotations

from svc_cli.catalog import (
    build_catalog_bytes,
    build_projection,
    canonical_documents,
    read_version_index,
)


__all__ = [
    "build_catalog_bytes",
    "build_projection",
    "canonical_documents",
    "read_version_index",
]
