"""Version facts exposed by the packaged runtime."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version as distribution_version

from . import DISTRIBUTION_NAME
from .catalog import Catalog, parse_catalog
from .resources import read_catalog_bytes


def catalog() -> Catalog:
    return parse_catalog(read_catalog_bytes())


def installed_distribution_version() -> str | None:
    try:
        return distribution_version(DISTRIBUTION_NAME)
    except PackageNotFoundError:
        return None


def runtime_version() -> str:
    """Report only the CLI distribution identity, never the Corpus version."""

    return installed_distribution_version() or "source-tree"
