"""Deterministic BSL matching, value materialization, and code escape boundary."""

from __future__ import annotations

import base64
import copy
import hashlib
import json
import math
import random
import re
import subprocess
import threading
import urllib.parse
import uuid
from contextlib import suppress
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal, cast

from pydantic import JsonValue

from ..errors import SvcError
from .cel_profile import (
    CelExpressionTooLarge,
    CelProfileError,
    evaluate_expression,
    regex_matches,
)
from .model import Body, Matcher, Materializer, Replay, ValueNode, strict_json_value


_MAX_CEL_CONTEXT_BYTES = 262_144
_MATERIALIZER_STDERR_BYTES = 65_536
_RFC3339 = re.compile(
    r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})",
    re.ASCII,
)


@dataclass
class MaterializationContext:
    replay: Replay
    scenario_name: str
    scenario_digest: str
    run_context_digest: str
    bindings: dict[str, JsonValue] = field(default_factory=dict)
    generated: dict[str, JsonValue] = field(default_factory=dict)


@dataclass(frozen=True)
class MaterializedEnvelope:
    method: str | None
    path: str | None
    query: dict[str, JsonValue]
    status: int | None
    headers: dict[str, str]
    body: bytes
    body_kind: Literal["empty", "structured", "raw"]
    structured: JsonValue | None


def compact_json(value: JsonValue) -> bytes:
    """Serialize the BSL structured-body profile deterministically."""

    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")


def strict_json_loads(raw: bytes, *, code: str) -> JsonValue:
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in items:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    try:
        text = raw.decode("utf-8")
        value = json.loads(
            text,
            object_pairs_hook=pairs,
            parse_constant=lambda token: (_ for _ in ()).throw(
                ValueError(f"non-finite number: {token}")
            ),
        )
        return strict_json_value(value)
    except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError) as error:
        raise SvcError(
            code, "Value is not strict UTF-8 JSON.", {"reason": str(error)}
        ) from error


def match_mapping(
    template: dict[str, JsonValue],
    nodes: tuple[ValueNode, ...],
    actual: dict[str, JsonValue],
    context: MaterializationContext,
    *,
    namespace: str,
) -> tuple[bool, tuple[str, ...], dict[str, JsonValue]]:
    return _match_value(template, nodes, actual, context, namespace=namespace)


def match_body(
    plan: Body | None,
    raw: bytes,
    context: MaterializationContext,
    *,
    namespace: str,
) -> tuple[bool, tuple[str, ...], dict[str, JsonValue], JsonValue | None]:
    if plan is None:
        return (raw == b"", (() if raw == b"" else ("unexpected body",)), {}, None)
    if plan.kind == "raw":
        assert plan.raw is not None
        expected = base64.b64decode(plan.raw.content_base64, validate=True)
        matched = raw == expected
        return matched, (() if matched else ("raw body differs",)), {}, None
    if plan.kind == "form-urlencoded":
        form_actual = _strict_form_urlencoded(raw)
        matched, reasons, captures = _match_value(
            plan.template,
            plan.nodes,
            form_actual,
            context,
            namespace=namespace,
        )
        return matched, reasons, captures, form_actual
    actual = strict_json_loads(raw, code="double-request-json-invalid")
    matched, reasons, captures = _match_value(
        plan.template,
        plan.nodes,
        actual,
        context,
        namespace=namespace,
    )
    return matched, reasons, captures, actual


def _strict_form_urlencoded(raw: bytes) -> dict[str, JsonValue]:
    if not raw:
        return {}

    values: dict[str, list[str]] = {}
    for pair in raw.split(b"&"):
        name, separator, value = pair.partition(b"=")
        if not separator or not name:
            raise SvcError(
                "double-request-form-invalid",
                "Form fields require non-empty name=value pairs.",
            )
        decoded_name = _strict_form_component(name)
        decoded_value = _strict_form_component(value)
        values.setdefault(decoded_name, []).append(decoded_value)
    return {
        name: cast(JsonValue, items[0] if len(items) == 1 else items)
        for name, items in values.items()
    }


def _strict_form_component(raw: bytes) -> str:
    index = 0
    while index < len(raw):
        if raw[index] == ord("%"):
            if index + 2 >= len(raw) or any(
                value not in b"0123456789abcdefABCDEF"
                for value in raw[index + 1 : index + 3]
            ):
                raise SvcError(
                    "double-request-form-invalid",
                    "Form percent encoding is invalid.",
                )
            index += 3
        else:
            index += 1
    try:
        return urllib.parse.unquote_to_bytes(raw.replace(b"+", b" ")).decode("utf-8")
    except UnicodeDecodeError as error:
        raise SvcError(
            "double-request-form-invalid",
            "Form field is not valid UTF-8.",
        ) from error


def commit_bindings(
    context: MaterializationContext, proposed: dict[str, JsonValue]
) -> None:
    for name, value in proposed.items():
        if name in context.bindings and not json_equal(context.bindings[name], value):
            raise SvcError(
                "double-capture-conflict",
                "A capture conflicts with its immutable run binding.",
                {"binding": name},
            )
    context.bindings.update(proposed)


def materialize_mapping(
    template: dict[str, JsonValue],
    nodes: tuple[ValueNode, ...],
    context: MaterializationContext,
    *,
    namespace: str,
    request: JsonValue | None,
) -> dict[str, JsonValue]:
    value = _materialize_value(
        template,
        nodes,
        context,
        namespace=namespace,
        request=request,
    )
    if not isinstance(value, dict):
        raise SvcError("double-materialization-invalid", "Expected an object value.")
    return value


def materialize_body(
    plan: Body | None,
    context: MaterializationContext,
    *,
    namespace: str,
    request: JsonValue | None,
) -> tuple[bytes, Literal["empty", "structured", "raw"], JsonValue | None]:
    if plan is None:
        return b"", "empty", None
    if plan.kind == "raw":
        assert plan.raw is not None
        try:
            return base64.b64decode(plan.raw.content_base64, validate=True), "raw", None
        except ValueError as error:
            raise SvcError(
                "double-managed-asset-invalid", "Managed raw snapshot is malformed."
            ) from error
    value = _materialize_value(
        plan.template,
        plan.nodes,
        context,
        namespace=namespace,
        request=request,
    )
    return compact_json(value), "structured", value


def run_materializer(
    declaration: Materializer,
    *,
    phase: Literal["response", "event"],
    context: MaterializationContext,
    request: JsonValue | None,
    expected_status: int | None = None,
    expected_method: str | None = None,
    expected_path: str | None = None,
) -> MaterializedEnvelope:
    stdin_value: dict[str, JsonValue] = {
        "schema_version": 1,
        "phase": phase,
        "run": {
            "seed": context.replay.seed,
            "clock": context.replay.clock,
            "scenario_digest": context.scenario_digest,
            "run_context_digest": context.run_context_digest,
            "runtime": context.replay.runtime,
            "generators": list(context.replay.generators),
            "validators": list(context.replay.validators),
        },
        "scenario": {"name": context.scenario_name},
        "bindings": dict(context.bindings),
        "request": request,
    }
    stdin = compact_json(stdin_value)
    if len(stdin) > _MAX_CEL_CONTEXT_BYTES:
        raise SvcError(
            "double-materializer-context-too-large",
            "Materializer context exceeds its byte bound.",
        )
    returncode, stdout, stderr_bytes = _run_bounded_materializer(
        declaration,
        stdin,
    )
    stderr = stderr_bytes.decode("utf-8", errors="replace")
    if returncode != 0:
        raise SvcError(
            "double-materializer-failed",
            "External materializer returned a non-zero exit status.",
            {"exit_code": returncode, "stderr": stderr},
        )
    value = strict_json_loads(stdout, code="double-materializer-output-invalid")
    if not isinstance(value, dict):
        raise SvcError(
            "double-materializer-envelope-invalid",
            "External materializer output must be one JSON object.",
        )
    return _materializer_envelope(
        value,
        phase=phase,
        expected_status=expected_status,
        expected_method=expected_method,
        expected_path=expected_path,
    )


def _run_bounded_materializer(
    declaration: Materializer,
    stdin: bytes,
) -> tuple[int, bytes, bytes]:
    try:
        process = subprocess.Popen(
            declaration.argv,
            cwd=declaration.cwd,
            env=declaration.env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except OSError as error:
        raise SvcError(
            "double-materializer-launch-failed",
            "External materializer could not be launched.",
            {"reason": str(error)},
        ) from error

    stdout = bytearray()
    stderr = bytearray()
    output_too_large = threading.Event()

    def write_input() -> None:
        assert process.stdin is not None
        try:
            process.stdin.write(stdin)
            process.stdin.flush()
        except (BrokenPipeError, OSError):
            pass
        finally:
            with suppress(OSError):
                process.stdin.close()

    def drain(
        stream: Any,
        destination: bytearray,
        limit: int,
        *,
        terminate_on_overflow: bool,
    ) -> None:
        try:
            while chunk := stream.read(65_536):
                remaining = limit + 1 - len(destination)
                if remaining > 0:
                    destination.extend(chunk[:remaining])
                if terminate_on_overflow and len(destination) > limit:
                    output_too_large.set()
                    with suppress(OSError):
                        process.kill()
        except (OSError, ValueError):
            pass

    assert process.stdout is not None
    assert process.stderr is not None
    threads = (
        threading.Thread(target=write_input, daemon=True),
        threading.Thread(
            target=drain,
            args=(process.stdout, stdout, declaration.max_output_bytes),
            kwargs={"terminate_on_overflow": True},
            daemon=True,
        ),
        threading.Thread(
            target=drain,
            args=(process.stderr, stderr, _MATERIALIZER_STDERR_BYTES),
            kwargs={"terminate_on_overflow": False},
            daemon=True,
        ),
    )
    for thread in threads:
        thread.start()
    try:
        process.wait(timeout=declaration.timeout_ms / 1000)
    except subprocess.TimeoutExpired as error:
        with suppress(OSError):
            process.kill()
        process.wait()
        raise SvcError(
            "double-materializer-timeout",
            "External materializer exceeded its timeout.",
            {"timeout_ms": declaration.timeout_ms},
        ) from error
    except BaseException:
        with suppress(OSError):
            process.kill()
        process.wait()
        raise
    finally:
        for thread in threads:
            thread.join(timeout=1)
        for stream in (process.stdin, process.stdout, process.stderr):
            if stream is not None:
                with suppress(OSError):
                    stream.close()

    if output_too_large.is_set():
        raise SvcError(
            "double-materializer-output-too-large",
            "External materializer output exceeds its byte bound.",
            {"max_output_bytes": declaration.max_output_bytes},
        )
    return process.returncode, bytes(stdout), bytes(stderr[:_MATERIALIZER_STDERR_BYTES])


def _match_value(
    template: JsonValue,
    nodes: tuple[ValueNode, ...],
    actual: JsonValue,
    context: MaterializationContext,
    *,
    namespace: str,
) -> tuple[bool, tuple[str, ...], dict[str, JsonValue]]:
    by_path = {node.path: node for node in nodes}
    reasons: list[str] = []
    captures: dict[str, JsonValue] = {}

    def visit(
        expected: JsonValue, observed: JsonValue, path: tuple[str | int, ...]
    ) -> None:
        node = by_path.get(path)
        if node is not None:
            matcher = node.matcher
            if node.kind in {"literal", "managed"}:
                required = node.value
                if not json_equal(required, observed):
                    reasons.append(f"{_pointer(path)}: exact value differs")
                return
            if matcher is None:
                reasons.append(f"{_pointer(path)}: matcher is absent")
                return
            if not matcher_accepts(matcher, observed):
                reasons.append(
                    f"{_pointer(path)}: {matcher.kind} matcher rejected value"
                )
                return
            if node.kind == "capture":
                assert node.name is not None
                if node.name in context.bindings:
                    existing = context.bindings[node.name]
                    exists = True
                elif node.name in captures:
                    existing = captures[node.name]
                    exists = True
                else:
                    existing = None
                    exists = False
                if exists and not json_equal(existing, observed):
                    raise SvcError(
                        "double-capture-conflict",
                        "A capture conflicts with its immutable run binding.",
                        {"binding": node.name, "path": _pointer(path)},
                    )
                captures[node.name] = observed
            return
        if (
            not isinstance(expected, bool)
            and not isinstance(observed, bool)
            and isinstance(expected, (int, float))
            and isinstance(observed, (int, float))
        ):
            if not json_equal(expected, observed):
                reasons.append(f"{_pointer(path)}: exact value differs")
            return
        if type(expected) is not type(observed):
            reasons.append(f"{_pointer(path)}: JSON type differs")
            return
        if isinstance(expected, dict) and isinstance(observed, dict):
            if set(expected) != set(observed):
                reasons.append(f"{_pointer(path)}: object keys differ")
                return
            for key in expected:
                visit(expected[key], observed[key], (*path, key))
            return
        if isinstance(expected, list) and isinstance(observed, list):
            if len(expected) != len(observed):
                reasons.append(f"{_pointer(path)}: array length differs")
                return
            for index, (left, right) in enumerate(zip(expected, observed, strict=True)):
                visit(left, right, (*path, index))
            return
        if expected != observed:
            reasons.append(f"{_pointer(path)}: exact value differs")

    visit(template, actual, ())
    return not reasons, tuple(reasons), captures


def matcher_accepts(matcher: Matcher, value: JsonValue) -> bool:
    if matcher.kind == "exact":
        return json_equal(value, matcher.value)
    if matcher.kind == "enum":
        return matcher.values is not None and any(
            json_equal(value, candidate) for candidate in matcher.values
        )
    if matcher.kind == "range":
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return False
        return (matcher.minimum is None or value >= matcher.minimum) and (
            matcher.maximum is None or value <= matcher.maximum
        )
    if matcher.kind == "regex":
        if not isinstance(value, str) or matcher.pattern is None:
            return False
        return _cel_regex_match(value, matcher.pattern)
    if matcher.kind == "semantic":
        if matcher.using == "svc.rfc-uuid/v1":
            if not isinstance(value, str):
                return False
            try:
                parsed = uuid.UUID(value)
            except ValueError:
                return False
            return str(parsed) == value.lower()
        if matcher.using == "svc.rfc3339/v1":
            return isinstance(value, str) and _rfc3339(value)
    return False


def _materialize_value(
    template: JsonValue,
    nodes: tuple[ValueNode, ...],
    context: MaterializationContext,
    *,
    namespace: str,
    request: JsonValue | None,
) -> JsonValue:
    value = cast(JsonValue, copy.deepcopy(template))
    # The compiler preserves author order so a later derived node may consume a
    # binding produced by an earlier node in the same output phase.
    for node in nodes:
        produced = _materialize_node(
            node,
            context,
            namespace=namespace,
            request=request,
        )
        value = _replace(value, node.path, produced)
    return value


def _materialize_node(
    node: ValueNode,
    context: MaterializationContext,
    *,
    namespace: str,
    request: JsonValue | None,
) -> JsonValue:
    if node.kind in {"literal", "example", "managed"}:
        value = node.value
    elif node.kind == "derived":
        assert node.expression is not None
        value = _evaluate_cel(node.expression, context, request)
    elif node.kind == "generated":
        key = f"{namespace}:{_pointer(node.path)}:{node.using}"
        if key not in context.generated:
            context.generated[key] = _generate(
                node, context.replay.seed, context.replay.clock, key
            )
        value = context.generated[key]
    else:
        raise SvcError(
            "double-materialization-phase-invalid",
            "Request-only node reached output materialization.",
            {"kind": node.kind, "path": _pointer(node.path)},
        )
    projected = strict_json_value(value)
    if node.validator is not None and not matcher_accepts(node.validator, projected):
        raise SvcError(
            "double-output-validation-failed",
            "Materialized output failed its declared validator.",
            {"path": _pointer(node.path), "validator": node.validator.kind},
        )
    if node.bind is not None:
        commit_bindings(context, {node.bind: projected})
    return projected


def _generate(node: ValueNode, seed: int, clock: str, key: str) -> JsonValue:
    assert node.using is not None
    digest = hashlib.sha256(f"{seed}\0{key}".encode("utf-8")).digest()
    rng = random.Random(int.from_bytes(digest, "big"))
    options = node.options or {}
    if node.using == "svc.uuid-v4/v1":
        raw = bytearray(rng.randbytes(16))
        raw[6] = (raw[6] & 0x0F) | 0x40
        raw[8] = (raw[8] & 0x3F) | 0x80
        return str(uuid.UUID(bytes=bytes(raw)))
    if node.using == "svc.opaque-token/v1":
        alphabet_name = options.get("alphabet")
        length = options.get("length")
        alphabets = {
            "lower-alphanumeric": "abcdefghijklmnopqrstuvwxyz0123456789",
            "alphanumeric": "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789",
            "hex-lower": "0123456789abcdef",
        }
        if not isinstance(alphabet_name, str) or alphabet_name not in alphabets:
            raise SvcError(
                "double-generator-options-invalid", "Opaque token alphabet is invalid."
            )
        if type(length) is not int or not 1 <= length <= 1024:
            raise SvcError(
                "double-generator-options-invalid", "Opaque token length is invalid."
            )
        alphabet = alphabets[alphabet_name]
        return "".join(rng.choice(alphabet) for _ in range(length))
    if node.using == "svc.bounded-integer/v1":
        minimum = options.get("minimum")
        maximum = options.get("maximum")
        if type(minimum) is not int or type(maximum) is not int or minimum > maximum:
            raise SvcError(
                "double-generator-options-invalid", "Integer bounds are invalid."
            )
        return rng.randint(minimum, maximum)
    if node.using == "svc.enum-choice/v1":
        values = options.get("values")
        if not isinstance(values, list) or not values:
            raise SvcError(
                "double-generator-options-invalid", "Enum choices are invalid."
            )
        return strict_json_value(values[rng.randrange(len(values))])
    if node.using == "svc.fixed-clock-rfc3339/v1":
        return clock
    raise SvcError(
        "double-generator-unsupported",
        "Generator is outside the closed SVC registry.",
        {"using": node.using},
    )


def _evaluate_cel(
    source: str, context: MaterializationContext, request: JsonValue | None
) -> JsonValue:
    data: dict[str, JsonValue] = {
        "request": request,
        "bindings": dict(context.bindings),
        "run": {"seed": context.replay.seed, "clock": context.replay.clock},
        "scenario": {"name": context.scenario_name},
    }
    if len(compact_json(strict_json_value(data))) > _MAX_CEL_CONTEXT_BYTES:
        raise SvcError(
            "double-cel-context-too-large", "CEL context exceeds its byte bound."
        )
    try:
        return evaluate_expression(source, data)
    except CelExpressionTooLarge as error:
        raise SvcError(
            "double-cel-too-large", "CEL expression exceeds its byte bound."
        ) from error
    except CelProfileError as error:
        raise SvcError(
            "double-cel-evaluation-failed",
            "Restricted CEL expression could not be evaluated.",
            {"reason": str(error)},
        ) from error


def _cel_regex_match(value: str, pattern: str) -> bool:
    try:
        return regex_matches(value, pattern)
    except CelProfileError as error:
        raise SvcError(
            "double-regex-evaluation-failed",
            "CEL/RE2 matcher could not be evaluated.",
            {"reason": str(error)},
        ) from error


def _materializer_envelope(
    value: dict[str, JsonValue],
    *,
    phase: Literal["response", "event"],
    expected_status: int | None,
    expected_method: str | None,
    expected_path: str | None,
) -> MaterializedEnvelope:
    required = (
        {"status", "headers", "body"}
        if phase == "response"
        else {"method", "path", "query", "headers", "body"}
    )
    if set(value) != required:
        raise SvcError(
            "double-materializer-envelope-invalid",
            "External materializer envelope fields do not match its phase.",
        )
    headers = value["headers"]
    if not isinstance(headers, dict) or not all(
        isinstance(key, str) and isinstance(item, str) for key, item in headers.items()
    ):
        raise SvcError(
            "double-materializer-envelope-invalid", "Envelope headers are invalid."
        )
    status = cast(int | None, value.get("status"))
    method = cast(str | None, value.get("method"))
    path = cast(str | None, value.get("path"))
    query_value = cast(JsonValue, value.get("query", {}))
    if phase == "response":
        if type(status) is not int or status != expected_status:
            raise SvcError(
                "double-materializer-envelope-invalid", "Envelope status changed."
            )
    elif method != expected_method or path != expected_path:
        raise SvcError(
            "double-materializer-envelope-invalid", "Envelope route changed."
        )
    if not isinstance(query_value, dict):
        raise SvcError(
            "double-materializer-envelope-invalid", "Envelope query is invalid."
        )
    if not all(
        isinstance(key, str)
        and (
            isinstance(item, str)
            or (
                isinstance(item, list)
                and all(isinstance(element, str) for element in item)
            )
        )
        for key, item in query_value.items()
    ):
        raise SvcError(
            "double-materializer-envelope-invalid",
            "Envelope query values must be strings or arrays of strings.",
        )
    body = value["body"]
    if not isinstance(body, dict) or not isinstance(body.get("kind"), str):
        raise SvcError(
            "double-materializer-envelope-invalid", "Envelope body is invalid."
        )
    kind = body["kind"]
    structured: JsonValue | None = None
    if kind == "empty" and set(body) == {"kind"}:
        raw = b""
    elif kind == "structured" and set(body) == {"kind", "value"}:
        structured = strict_json_value(body["value"])
        raw = compact_json(structured)
    elif (
        kind == "raw"
        and set(body) == {"kind", "base64"}
        and isinstance(body["base64"], str)
    ):
        try:
            raw = base64.b64decode(body["base64"], validate=True)
        except ValueError as error:
            raise SvcError(
                "double-materializer-envelope-invalid", "Envelope base64 is invalid."
            ) from error
    else:
        raise SvcError(
            "double-materializer-envelope-invalid", "Envelope body variant is invalid."
        )
    return MaterializedEnvelope(
        method=method,
        path=path,
        query={str(key): item for key, item in query_value.items()},
        status=status,
        headers=cast(dict[str, str], headers),
        body=raw,
        body_kind=cast(Literal["empty", "structured", "raw"], kind),
        structured=structured,
    )


def _replace(
    root: JsonValue, path: tuple[str | int, ...], value: JsonValue
) -> JsonValue:
    if not path:
        return value
    current: Any = root
    for part in path[:-1]:
        current = current[part]
    current[path[-1]] = value
    return root


def _pointer(path: tuple[str | int, ...]) -> str:
    if not path:
        return "/"
    return "/" + "/".join(
        str(item).replace("~", "~0").replace("/", "~1") for item in path
    )


def _rfc3339(value: str) -> bool:
    if not _RFC3339.fullmatch(value):
        return False
    try:
        parsed = datetime.fromisoformat(
            value[:-1] + "+00:00" if value.endswith("Z") else value
        )
    except ValueError:
        return False
    return parsed.tzinfo is not None and math.isfinite(parsed.timestamp())


def json_equal(left: JsonValue, right: JsonValue) -> bool:
    if isinstance(left, bool) or isinstance(right, bool):
        return type(left) is type(right) and left == right
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return left == right
    if type(left) is not type(right):
        return False
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(
            json_equal(a, b) for a, b in zip(left, right, strict=True)
        )
    if isinstance(left, dict) and isinstance(right, dict):
        return set(left) == set(right) and all(
            json_equal(left[key], right[key]) for key in left
        )
    return left == right
