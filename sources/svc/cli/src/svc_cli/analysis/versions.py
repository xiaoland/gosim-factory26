"""Explicit analysis API and evidence compatibility routing."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping
import zipfile

from .protocol import AnalysisProtocolError


def requested_analysis_version(request: object) -> int:
    if not isinstance(request, Mapping):
        raise AnalysisProtocolError(
            "invalid-query-request", "Analysis request must be an object."
        )
    version = request.get("version", 3)
    if version != 3:
        raise AnalysisProtocolError(
            "unsupported-analysis-version", "Analysis version must be 3."
        )
    return version


def evidence_schema_version(path: Path) -> int:
    try:
        with zipfile.ZipFile(path, "r") as archive:
            raw = archive.read("manifest.json")
        value = json.loads(raw)
        version = value.get("schema_version") if isinstance(value, dict) else None
    except (
        OSError,
        KeyError,
        ValueError,
        zipfile.BadZipFile,
        json.JSONDecodeError,
    ) as error:
        raise AnalysisProtocolError(
            "bundle-invalid", "Evidence manifest cannot be read."
        ) from error
    if type(version) is not int:
        raise AnalysisProtocolError(
            "invalid-evidence-manifest", "Evidence schema version is missing."
        )
    return version


def validate_analysis_versions(request: object, path: Path) -> None:
    requested_analysis_version(request)
    evidence = evidence_schema_version(path)
    if evidence != 4:
        raise AnalysisProtocolError(
            "unsupported-agent-thread-bundle-schema",
            "Evidence schema must be 4; recollect older evidence.",
        )


__all__ = [
    "evidence_schema_version",
    "requested_analysis_version",
    "validate_analysis_versions",
]
