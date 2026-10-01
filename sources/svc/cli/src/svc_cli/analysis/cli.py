"""Argument grammar and execution for the analysis command family."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from ..cli_output.model import dump_machine_output, unscoped_machine_object
from .models_v3 import (
    error_schema_v3,
    query_request_schema_v3,
    query_response_schema_v3,
    read_request_schema_v3,
    read_response_schema_v3,
)
from .protocol import AnalysisProtocolError
from .service import execute_query, execute_read


def register(subparsers: argparse._SubParsersAction[Any]) -> None:
    analysis = subparsers.add_parser(
        "analysis",
        help="Navigate immutable Agent-thread evidence without interpreting it",
        description=(
            "Query structural projections or read exact native records from one immutable "
            "Agent-thread evidence bundle. The CLI owns bounded navigation, references, "
            "coverage status, and byte fidelity; the calling Agent owns task intent, "
            "semantic interpretation, conclusions, and acceptance."
        ),
        epilog=(
            "Analysis method: establish the task objective and authority; use overview "
            "and match to locate evidence, then trace for linked normalized context or "
            "profile for supported measurements. Use read for exact content recovery "
            "or native audit, not as a mandatory step after trace. Distinguish observations, "
            "within-case inference, candidate mechanisms, and recurring patterns; search "
            "for competing explanations and counterexamples; report the supported claim, "
            "evidence horizon, material unknowns, and task-visible cost. A match, completion "
            "marker, Agent statement, command result, or missing record is not by itself a "
            "task-performance conclusion. Use query/read --schema for machine contracts."
        ),
    )
    analysis.add_argument("--schema", action="store_true", dest="analysis_schema")
    tools = analysis.add_subparsers(dest="analysis_tool")
    for name, help_text in (
        ("query", "Inspect boundaries or match deterministic navigation predicates"),
        ("read", "Read ordered native evidence from start, exact ref, or cursor"),
    ):
        tool = tools.add_parser(name, help=help_text)
        tool.add_argument(
            "--schema",
            action="store_true",
            help="Return the machine contract; use svc analysis --help for interpretation guidance",
        )
        tool.add_argument("--input", type=Path, help="Exact schema-v4 evidence ZIP")
        tool.add_argument("--request", help="JSON request file or - for stdin")


def run(args: argparse.Namespace) -> int:
    if args.analysis_schema:
        if args.analysis_tool is not None:
            raise AnalysisProtocolError(
                "invalid-cli-usage",
                "Top-level --schema cannot be combined with a tool.",
            )
        _emit(
            {
                "format": "svc.analysis.schema/v3",
                "versions": {"analysis": [3], "evidence": [4]},
                "tools": {
                    "query": {
                        "request": query_request_schema_v3(),
                        "response": query_response_schema_v3(),
                    },
                    "read": {
                        "request": read_request_schema_v3(),
                        "response": read_response_schema_v3(),
                    },
                },
                "error": error_schema_v3(),
                "ref_consumers": {
                    "execution": ["query.trace", "query.profile", "query.match"],
                    "turn": ["query.trace"],
                    "event": ["query.trace"],
                    "content": ["read"],
                    "blob": ["read"],
                    "native": ["read"],
                },
            }
        )
        return 0
    if args.analysis_tool is None:
        raise AnalysisProtocolError(
            "invalid-cli-usage", "Analysis requires --schema, query, or read."
        )
    if args.schema:
        if args.input is not None or args.request is not None:
            raise AnalysisProtocolError(
                "invalid-cli-usage",
                "--schema cannot be combined with --input or --request.",
            )
        query = args.analysis_tool == "query"
        _emit(
            {
                "format": f"svc.analysis.{args.analysis_tool}.schema/v3",
                "version": 3,
                "request": query_request_schema_v3()
                if query
                else read_request_schema_v3(),
                "response": query_response_schema_v3()
                if query
                else read_response_schema_v3(),
                "error": error_schema_v3(),
            }
        )
        return 0
    if args.input is None or args.request is None:
        raise AnalysisProtocolError(
            "invalid-cli-usage",
            "Analysis execution requires --input and --request.",
        )
    request = _request(args.request)
    payload = (
        execute_query(args.input, request)
        if args.analysis_tool == "query"
        else execute_read(args.input, request)
    )
    _emit(payload)
    return 0


def _request(source: str) -> object:
    if source == "-":
        text = sys.stdin.read(1_048_577)
    else:
        try:
            with Path(source).open("r", encoding="utf-8") as stream:
                text = stream.read(1_048_577)
        except (OSError, UnicodeDecodeError) as error:
            raise AnalysisProtocolError(
                "analysis-request-unreadable",
                "Analysis request could not be read as UTF-8 JSON.",
                {"path": source, "reason": str(error)},
            ) from error
    if len(text.encode("utf-8")) > 1_048_576:
        raise AnalysisProtocolError(
            "analysis-request-too-large", "Analysis request exceeds its byte bound."
        )

    def pairs(items: list[tuple[str, object]]) -> dict[str, object]:
        value: dict[str, object] = {}
        for key, item in items:
            if key in value:
                raise ValueError(f"duplicate JSON key: {key}")
            value[key] = item
        return value

    try:
        return json.loads(
            text,
            object_pairs_hook=pairs,
            parse_constant=lambda token: (_ for _ in ()).throw(
                ValueError(f"non-finite number: {token}")
            ),
        )
    except (json.JSONDecodeError, ValueError) as error:
        raise AnalysisProtocolError(
            "invalid-analysis-request-json",
            "Analysis request is not strict JSON.",
            {"reason": str(error)},
        ) from error


def _emit(payload: dict[str, Any]) -> None:
    dump_machine_output(unscoped_machine_object(payload), sys.stdout)


__all__ = ["register", "run"]
