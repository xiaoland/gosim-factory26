"""Single admitted CEL profile for double compilation and execution."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from cel_expr_python import cel  # type: ignore[import-untyped]
from pydantic import JsonValue

from .model import strict_json_value


MAX_CEL_EXPRESSION_BYTES = 4_096

_PROFILE = """\
stdlib:
  exclude_macros:
    - all
    - exists
    - exists_one
    - map
    - filter
"""
_VARIABLES = {
    "request": cel.Type.Map(cel.Type.STRING, cel.Type.DYN),
    "bindings": cel.Type.Map(cel.Type.STRING, cel.Type.DYN),
    "run": cel.Type.Map(cel.Type.STRING, cel.Type.DYN),
    "scenario": cel.Type.Map(cel.Type.STRING, cel.Type.DYN),
}
_BINDING_DOT_RE = re.compile(r"\bbindings\.([a-z][a-z0-9_]*)\b")
_BINDING_INDEX_RE = re.compile(r"\bbindings\[['\"]([a-z][a-z0-9_]*)['\"]\]")
_BINDINGS_TOKEN_RE = re.compile(r"\bbindings\b")
_REQUEST_TOKEN_RE = re.compile(r"\brequest\b")


class CelProfileError(ValueError):
    """A CEL library failure projected through the admitted profile."""


class CelExpressionTooLarge(CelProfileError):
    """The authored expression exceeds the stable v0 byte bound."""


@dataclass(frozen=True)
class CelInspection:
    """Mechanically inspectable names in the v0 dynamic-map surface."""

    bindings: frozenset[str]
    dynamic_binding_access: bool
    uses_request: bool


def inspect_expression(source: str) -> CelInspection:
    """Inspect the frozen v0 binding surface without reading string contents."""

    _check_expression_size(source)
    code_only = _without_string_literals(source)
    bindings = frozenset(
        (*_BINDING_DOT_RE.findall(code_only), *_BINDING_INDEX_RE.findall(code_only))
    )
    stripped = _BINDING_DOT_RE.sub("", code_only)
    stripped = _BINDING_INDEX_RE.sub("", stripped)
    return CelInspection(
        bindings=bindings,
        dynamic_binding_access=_BINDINGS_TOKEN_RE.search(stripped) is not None,
        uses_request=_REQUEST_TOKEN_RE.search(code_only) is not None,
    )


def validate_expression(source: str) -> None:
    """Compile an expression under the admitted environment and JSON type policy."""

    _compile(source)


def evaluate_expression(source: str, data: Mapping[str, JsonValue]) -> JsonValue:
    """Evaluate a compiled-scenario expression under the same admitted profile."""

    try:
        result = _compile(source).eval(data=dict(data)).plain_value()
        return strict_json_value(result)
    except CelProfileError:
        raise
    except Exception as error:
        raise CelProfileError(str(error)) from error


def validate_regex(pattern: str) -> None:
    """Compile and execute a pattern once so invalid RE2 fails at authoring time."""

    _check_expression_size(pattern)
    regex_matches("", pattern)


def regex_matches(value: str, pattern: str) -> bool:
    """Evaluate one matcher with CEL's admitted RE2 implementation."""

    try:
        config = cel.NewEnvConfigFromYaml(_PROFILE)
        environment = cel.NewEnv(
            config=config,
            variables={"value": cel.Type.STRING, "pattern": cel.Type.STRING},
        )
        result = environment.compile("value.matches(pattern)").eval(
            data={"value": value, "pattern": pattern}
        )
        if result.type() == cel.Type.ERROR:
            raise RuntimeError(str(result.value()))
        return bool(result.plain_value())
    except Exception as error:
        raise CelProfileError(str(error)) from error


def _compile(source: str) -> Any:
    _check_expression_size(source)
    try:
        config = cel.NewEnvConfigFromYaml(_PROFILE)
        program = cel.NewEnv(config=config, variables=_VARIABLES).compile(source)
        if not _type_is_json(program.return_type().name()):
            raise TypeError(
                f"CEL return type is outside JSON values: {program.return_type()}"
            )
        return program
    except CelProfileError:
        raise
    except Exception as error:
        raise CelProfileError(str(error)) from error


def _check_expression_size(source: str) -> None:
    if len(source.encode("utf-8")) > MAX_CEL_EXPRESSION_BYTES:
        raise CelExpressionTooLarge(
            f"CEL expression exceeds {MAX_CEL_EXPRESSION_BYTES} bytes"
        )


def _without_string_literals(source: str) -> str:
    """Blank CEL string/comment contents so inspection does not read literals."""

    result = list(source)
    index = 0
    while index < len(source):
        if source.startswith("//", index):
            while index < len(source) and source[index] not in "\r\n":
                result[index] = " "
                index += 1
            continue
        quote = source[index]
        if quote not in {"'", '"'}:
            index += 1
            continue
        static_binding = re.search(r"\bbindings\[$", source[:index])
        if static_binding is not None:
            key = re.match(
                rf"{re.escape(quote)}[a-z][a-z0-9_]*{re.escape(quote)}\]",
                source[index:],
            )
            if key is not None:
                index += len(key.group(0)) - 1
                continue
        width = 3 if source.startswith(quote * 3, index) else 1
        cursor = index
        for offset in range(width):
            result[index + offset] = " "
        index += width
        while index < len(source):
            if source.startswith(quote * width, index):
                for offset in range(width):
                    result[index + offset] = " "
                index += width
                break
            result[index] = " "
            if source[index] == "\\" and index + 1 < len(source):
                index += 1
                result[index] = " "
            index += 1
        if index == cursor:
            index += 1
    return "".join(result)


def _type_is_json(type_name: str) -> bool:
    compact = type_name.replace(" ", "")
    if compact in {"DYN", "NULL", "BOOL", "INT", "UINT", "DOUBLE", "STRING"}:
        return True
    if compact.startswith("LIST<") and compact.endswith(">"):
        return _type_is_json(compact[5:-1])
    if compact.startswith("MAP<STRING,") and compact.endswith(">"):
        return _type_is_json(compact[len("MAP<STRING,") : -1])
    return False
