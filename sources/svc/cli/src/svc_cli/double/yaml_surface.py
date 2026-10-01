"""Strict YAML 1.2 authoring surface and source-coordinate adapter."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap
from ruamel.yaml.error import YAMLError
from ruamel.yaml.events import (
    AliasEvent,
    DocumentStartEvent,
    MappingEndEvent,
    MappingStartEvent,
    ScalarEvent,
    SequenceEndEvent,
    SequenceStartEvent,
)

from ..errors import SvcError


MAX_YAML_NODES = 50_000
MAX_YAML_DEPTH = 64


def load_yaml(
    raw: bytes,
    source: Path,
    module: Path,
    *,
    is_module: bool,
) -> object:
    """Load one admitted YAML document while preserving ruamel locations."""

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise SvcError(
            "invalid-double-yaml",
            "YAML source must be UTF-8.",
            {"module": str(module), "source": str(source)},
        ) from error
    if text.startswith("\ufeff"):
        raise SvcError(
            "invalid-double-yaml",
            "YAML source must not contain a UTF-8 BOM.",
            {
                "module": str(module),
                "source": str(source),
                "line": 1,
                "column": 1,
            },
        )

    parser = _new_parser()
    try:
        _inspect_events(parser, text, source, module)
        result = parser.load(text)
    except SvcError:
        raise
    except YAMLError as error:
        mark = getattr(error, "problem_mark", None) or getattr(
            error, "context_mark", None
        )
        details: dict[str, Any] = {
            "module": str(module),
            "source": str(source),
        }
        if mark is not None:
            details.update({"line": mark.line + 1, "column": mark.column + 1})
        raise SvcError(
            "invalid-double-yaml",
            "YAML source is not a valid strict BSL document."
            if is_module
            else "Local contract is not valid strict YAML/JSON.",
            {**details, "diagnostic": _bounded_diagnostic(error)},
        ) from error
    if result is None:
        raise SvcError(
            "invalid-double-yaml",
            "YAML source must contain one non-empty document.",
            {"module": str(module), "source": str(source)},
        )
    return result


def source_location(owner: object, key: str | None = None) -> tuple[int, int]:
    """Return one-based authored coordinates, falling back deterministically."""

    try:
        if key is not None and isinstance(owner, CommentedMap):
            position = owner.lc.key(key)
            if position is not None:
                return position[0] + 1, position[1] + 1
        line = owner.lc.line  # type: ignore[attr-defined]
        column = owner.lc.col  # type: ignore[attr-defined]
        return line + 1, column + 1
    except (AttributeError, KeyError, TypeError):
        return 1, 1


def _new_parser() -> YAML:
    parser = YAML(typ="rt", pure=True)
    parser.version = (1, 2)
    parser.allow_duplicate_keys = False
    parser.constructor.add_constructor(
        "tag:yaml.org,2002:timestamp",
        lambda loader, node: loader.construct_scalar(node),
    )
    return parser


def _inspect_events(parser: YAML, text: str, source: Path, module: Path) -> None:
    documents = 0
    nodes = 0
    stack: list[tuple[str, bool]] = []

    def complete_node() -> None:
        if stack and stack[-1][0] == "mapping":
            kind, expecting_key = stack[-1]
            stack[-1] = (kind, not expecting_key)

    for event in parser.parse(text):
        if isinstance(event, DocumentStartEvent):
            documents += 1
            if documents > 1:
                raise SvcError(
                    "multiple-double-yaml-documents",
                    "BSL v0 admits exactly one YAML document.",
                    _event_details(module, source, event),
                )
        if isinstance(event, AliasEvent) or getattr(event, "anchor", None) is not None:
            raise SvcError(
                "unsupported-double-yaml-feature",
                "YAML anchors and aliases are not admitted in BSL v0.",
                {
                    **_event_details(module, source, event),
                    "feature": "anchor-or-alias",
                },
            )
        if getattr(event, "tag", None) is not None:
            raise SvcError(
                "unsupported-double-yaml-feature",
                "Explicit YAML tags are not admitted in BSL v0.",
                {**_event_details(module, source, event), "feature": "tag"},
            )
        if isinstance(event, ScalarEvent):
            is_mapping_key = bool(stack and stack[-1] == ("mapping", True))
            if is_mapping_key and event.value == "<<":
                raise SvcError(
                    "unsupported-double-yaml-feature",
                    "YAML merge keys are not admitted in BSL v0.",
                    {
                        **_event_details(module, source, event),
                        "feature": "merge-key",
                    },
                )
            nodes += 1
            complete_node()
        elif isinstance(event, (MappingStartEvent, SequenceStartEvent)):
            nodes += 1
            depth = len(stack) + 1
            if depth > MAX_YAML_DEPTH:
                raise SvcError(
                    "double-yaml-too-deep",
                    "YAML source exceeds the BSL v0 nesting bound.",
                    {
                        **_event_details(module, source, event),
                        "max_depth": MAX_YAML_DEPTH,
                    },
                )
            stack.append(
                ("mapping", True)
                if isinstance(event, MappingStartEvent)
                else ("sequence", False)
            )
        elif isinstance(event, (MappingEndEvent, SequenceEndEvent)):
            if stack:
                stack.pop()
            complete_node()
        if nodes > MAX_YAML_NODES:
            raise SvcError(
                "double-yaml-too-many-nodes",
                "YAML source exceeds the BSL v0 node bound.",
                {
                    **_event_details(module, source, event),
                    "max_nodes": MAX_YAML_NODES,
                },
            )
    if documents != 1:
        raise SvcError(
            "invalid-double-yaml",
            "BSL v0 admits exactly one YAML document.",
            {"module": str(module), "source": str(source)},
        )


def _event_details(module: Path, source: Path, event: object) -> dict[str, object]:
    mark = event.start_mark  # type: ignore[attr-defined]
    return {
        "module": str(module),
        "source": str(source),
        "line": mark.line + 1,
        "column": mark.column + 1,
    }


def _bounded_diagnostic(error: BaseException, maximum: int = 1_000) -> str:
    text = " ".join(str(error).split())
    if len(text) <= maximum:
        return text
    return text[: maximum - 3] + "..."
