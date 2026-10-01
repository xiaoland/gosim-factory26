"""Filesystem boundary for the two Agent analysis tools."""

from __future__ import annotations

from pathlib import Path

from ..telemetry.evidence import EvidenceError
from ..telemetry.evidence_v4 import validate_evidence_v4
from .protocol import AnalysisProtocolError
from .query_v3 import query_evidence_v3
from .read_v3 import read_evidence_v3
from .versions import validate_analysis_versions


def execute_query(input_path: Path, request: object) -> dict[str, object]:
    validate_analysis_versions(request, input_path)
    try:
        return query_evidence_v3(validate_evidence_v4(input_path), request)
    except EvidenceError as error:
        raise AnalysisProtocolError(error.code, error.message, error.details) from error


def execute_read(input_path: Path, request: object) -> dict[str, object]:
    validate_analysis_versions(request, input_path)
    try:
        return read_evidence_v3(validate_evidence_v4(input_path), request)
    except EvidenceError as error:
        raise AnalysisProtocolError(error.code, error.message, error.details) from error


__all__ = ["execute_query", "execute_read"]
