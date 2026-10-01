"""Native loopback responder and explicit event engine for one double run."""

from __future__ import annotations

import base64
import hashlib
import re
import threading
import urllib.parse
from collections import deque
from collections.abc import Mapping
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Literal, cast

import urllib3
from pydantic import JsonValue

from ..errors import SvcError
from .materialization import (
    MaterializationContext,
    commit_bindings,
    compact_json,
    json_equal,
    match_body,
    match_mapping,
    materialize_body,
    materialize_mapping,
    run_materializer,
)
from .model import (
    EmitResult,
    Event,
    Interaction,
    Journal,
    JournalEntry,
    RunObservation,
    Scenario,
    TargetBinding,
)
from .schema_registry import (
    SchemaRegistry,
    build_schema_registry,
    schema_validation_errors,
)


_MAX_BODY_BYTES = 1_048_576
_MAX_JOURNAL_ENTRIES = 200
_HTTP_TIMEOUT_SECONDS = 5.0
_SENSITIVE_HEADERS = frozenset({"authorization", "cookie", "proxy-authorization"})
_HTTP_FIELD_NAME = re.compile(r"[!#$%&'*+.^_`|~0-9A-Za-z-]+", re.ASCII)
_RUNTIME_OWNED_HEADERS = frozenset(
    {"connection", "content-length", "host", "transfer-encoding"}
)


class BoundaryEngine:
    """Single carrier-owned authority for matching, bindings, events, and journal."""

    def __init__(
        self,
        scenario: Scenario,
        context: MaterializationContext,
        targets: tuple[TargetBinding, ...],
    ) -> None:
        self.scenario = scenario
        self.context = context
        self.targets = {binding.name: binding for binding in targets}
        resources = (
            () if scenario.contract is None else scenario.contract.schema_resources
        )
        self._schema_registry = build_schema_registry(resources)
        self._lock = threading.RLock()
        self._entries: deque[JournalEntry] = deque(maxlen=_MAX_JOURNAL_ENTRIES)
        self._journal_total = 0
        self._status: Literal[
            "bootstrapping", "ready", "stopping", "stopped", "failed"
        ] = "bootstrapping"
        self._failure: str | None = None
        self.responder_url: str | None = None

    def ready(self, responder_url: str) -> None:
        with self._lock:
            self.responder_url = responder_url
            self._status = "ready"

    def begin_stop(self) -> None:
        with self._lock:
            self._status = "stopping"

    def stopped(self) -> None:
        with self._lock:
            self._status = "stopped"

    def fail(self, reason: str) -> None:
        with self._lock:
            self._failure = reason
            self._status = "failed"
            self._journal("runtime", "failed", {"reason": reason})

    def handle_request(
        self,
        *,
        method: str,
        target: str,
        headers: dict[str, str],
        raw_body: bytes,
    ) -> tuple[int, dict[str, str], bytes]:
        with self._lock:
            if self._status != "ready":
                return self._failure_response(
                    503, "double-not-ready", "Responder is not accepting traffic."
                )
            try:
                path, query = _parse_target(target)
            except SvcError as error:
                self._journal(
                    "request", error.code, {"method": method, "target": target}
                )
                return self._failure_response(400, error.code, error.message)
            candidates: list[
                tuple[
                    Interaction,
                    dict[str, JsonValue],
                    JsonValue | None,
                    Literal["empty", "structured", "raw"],
                ]
            ] = []
            mismatch: list[dict[str, JsonValue]] = []
            capture_conflict: SvcError | None = None
            for interaction in self.scenario.interactions:
                try:
                    matched, reasons, proposed, structured, body_kind = (
                        self._match_interaction(
                            interaction,
                            method=method,
                            path=path,
                            query=query,
                            headers=headers,
                            raw_body=raw_body,
                        )
                    )
                except SvcError as error:
                    if error.code == "double-capture-conflict":
                        capture_conflict = error
                        continue
                    self._journal(
                        "request",
                        error.code,
                        {"method": method, "path": path, "reason": error.message},
                    )
                    return self._failure_response(400, error.code, error.message)
                if matched:
                    candidates.append((interaction, proposed, structured, body_kind))
                else:
                    mismatch.append(
                        {
                            "interaction": interaction.name,
                            "reasons": list(reasons[:12]),
                        }
                    )
            request_facts: dict[str, JsonValue] = {
                "method": method,
                "path": path,
                "body_sha256": hashlib.sha256(raw_body).hexdigest(),
                "body_bytes": len(raw_body),
            }
            if not candidates:
                if capture_conflict is not None:
                    self._journal("request", "capture-conflict", request_facts)
                    return self._failure_response(
                        409, capture_conflict.code, capture_conflict.message
                    )
                request_facts["mismatch"] = cast(JsonValue, mismatch)
                self._journal("request", "no-match", request_facts)
                return self._failure_response(
                    404, "double-no-match", "No interaction matched the request."
                )
            if len(candidates) != 1:
                request_facts["interactions"] = [item[0].name for item in candidates]
                self._journal("request", "ambiguous-match", request_facts)
                return self._failure_response(
                    409, "double-ambiguous-match", "More than one interaction matched."
                )
            interaction, proposed, structured_request, request_body_kind = candidates[0]
            try:
                self._validate_contract_request(structured_request, request_body_kind)
                commit_bindings(self.context, proposed)
                normalized_request = self._normalized_request(
                    interaction,
                    method=method,
                    path=path,
                    query=query,
                    headers=headers,
                    raw_body=raw_body,
                    structured=structured_request,
                    body_kind=request_body_kind,
                )
                status, response_headers, response_body = self._response(
                    interaction, normalized_request
                )
            except SvcError as error:
                request_facts["interaction"] = interaction.name
                self._journal("request", error.code, request_facts)
                http_status = (
                    422 if error.code == "double-request-contract-failed" else 500
                )
                return self._failure_response(http_status, error.code, error.message)
            request_facts.update(
                {
                    "interaction": interaction.name,
                    "response_status": status,
                    "response_sha256": hashlib.sha256(response_body).hexdigest(),
                }
            )
            self._journal("request", "matched", request_facts)
            return status, response_headers, response_body

    def emit(self, event_name: str) -> EmitResult:
        with self._lock:
            if self._status != "ready":
                return EmitResult(
                    run_id="",
                    event=event_name,
                    status="control-unavailable",
                    reason="run is not ready",
                )
            event = next(
                (item for item in self.scenario.events if item.name == event_name), None
            )
            if event is None:
                raise SvcError(
                    "double-event-unknown",
                    "The run does not declare that event.",
                    {"event": event_name},
                )
            binding = self.targets.get(event.target)
            if binding is None:
                raise SvcError(
                    "double-target-missing",
                    "The event target was not bound at start.",
                    {"target": event.target},
                )
            try:
                url, headers, body = self._event_request(event, binding)
            except SvcError as error:
                self._journal(
                    "event",
                    error.code,
                    {"event": event.name, "target": binding.origin},
                )
                return EmitResult(
                    run_id="",
                    event=event.name,
                    status="not-acknowledged",
                    target=binding.origin,
                    reason=error.code,
                )
        # The Consumer may synchronously call the responder while handling an event
        # (for example, a status callback that refreshes provider detail). Keep the
        # binding snapshot/materialization atomic, but never hold the engine lock
        # across external I/O or that legitimate re-entry deadlocks.
        manager = urllib3.PoolManager(retries=False)
        try:
            response = manager.request(
                event.request.method,
                url,
                body=body,
                headers=headers,
                redirect=False,
                retries=False,
                timeout=urllib3.Timeout(total=_HTTP_TIMEOUT_SECONDS),
                preload_content=False,
            )
        except urllib3.exceptions.HTTPError as error:
            with self._lock:
                self._journal(
                    "event",
                    "transport-failed",
                    {
                        "event": event.name,
                        "target": binding.origin,
                        "body_sha256": hashlib.sha256(body).hexdigest(),
                        "reason": type(error).__name__,
                    },
                )
                return EmitResult(
                    run_id="",
                    event=event.name,
                    status="transport-failed",
                    target=binding.origin,
                    reason=str(error),
                )
        status = response.status
        response.close()
        acknowledged = 200 <= status < 300
        with self._lock:
            self._journal(
                "event",
                "acknowledged" if acknowledged else "not-acknowledged",
                {
                    "event": event.name,
                    "target": binding.origin,
                    "http_status": status,
                    "body_sha256": hashlib.sha256(body).hexdigest(),
                },
            )
        return EmitResult(
            run_id="",
            event=event.name,
            status="acknowledged" if acknowledged else "not-acknowledged",
            target=binding.origin,
            http_status=status,
            reason=None if acknowledged else "event acknowledgement was not 2xx",
        )

    def observation(self, *, run_id: str, sealed: bool) -> RunObservation:
        with self._lock:
            retained = tuple(self._entries)
            journal = Journal(
                total=self._journal_total,
                retained=len(retained),
                omitted=self._journal_total - len(retained),
                entries=retained,
            )
            return RunObservation(
                run_id=run_id,
                scenario_name=self.scenario.name,
                status=self._status,
                sealed=sealed,
                responder_url=self.responder_url,
                scenario_digest=self.context.scenario_digest,
                run_context_digest=self.context.run_context_digest,
                replay=self.context.replay,
                targets=tuple(self.targets.values()),
                bindings=dict(self.context.bindings),
                journal=journal,
                nonclaims=self.scenario.nonclaims,
                failure=self._failure,
            )

    def _match_interaction(
        self,
        interaction: Interaction,
        *,
        method: str,
        path: str,
        query: dict[str, JsonValue],
        headers: dict[str, str],
        raw_body: bytes,
    ) -> tuple[
        bool,
        tuple[str, ...],
        dict[str, JsonValue],
        JsonValue | None,
        Literal["empty", "structured", "raw"],
    ]:
        reasons: list[str] = []
        request = interaction.request
        if method != request.method:
            reasons.append("method differs")
        if path != request.path:
            reasons.append("path differs")
        body_kind: Literal["empty", "structured", "raw"] = (
            "empty"
            if request.body is None
            else "raw"
            if request.body.kind == "form-urlencoded"
            else request.body.kind
        )
        # Method and path are the route discriminator. An unrelated structured
        # interaction must not attempt to parse this route's empty/raw body and
        # turn a valid request into a global syntax failure.
        if reasons:
            return False, tuple(reasons), {}, None, body_kind
        proposed: dict[str, JsonValue] = {}
        query_ok, query_reasons, query_captures = match_mapping(
            request.query,
            request.query_nodes,
            query,
            self.context,
            namespace=f"interaction:{interaction.name}:request:query",
        )
        if not query_ok:
            reasons.extend(f"query {reason}" for reason in query_reasons)
        proposed.update(query_captures)
        declared_headers = set(request.headers)
        missing_headers = declared_headers - set(headers)
        if missing_headers:
            reasons.append("required header is absent")
            header_ok = False
            header_captures: dict[str, JsonValue] = {}
        else:
            selected_headers: dict[str, JsonValue] = {
                name: headers[name] for name in declared_headers
            }
            header_ok, header_reasons, header_captures = match_mapping(
                request.headers,
                request.header_nodes,
                selected_headers,
                self.context,
                namespace=f"interaction:{interaction.name}:request:headers",
            )
            if not header_ok:
                reasons.extend(f"header {reason}" for reason in header_reasons)
        proposed.update(header_captures)
        body_ok, body_reasons, body_captures, structured = match_body(
            request.body,
            raw_body,
            self.context,
            namespace=f"interaction:{interaction.name}:request:body",
        )
        if not body_ok:
            reasons.extend(body_reasons)
        for name, value in body_captures.items():
            if name in proposed and not json_equal(proposed[name], value):
                raise SvcError(
                    "double-capture-conflict",
                    "One request proposed conflicting values for the same binding.",
                    {"binding": name},
                )
            proposed[name] = value
        return not reasons, tuple(reasons), proposed, structured, body_kind

    def _response(
        self, interaction: Interaction, request: JsonValue
    ) -> tuple[int, dict[str, str], bytes]:
        response = interaction.response
        if response.materializer is not None:
            envelope = run_materializer(
                response.materializer,
                phase="response",
                context=self.context,
                request=request,
                expected_status=response.status,
            )
            self._validate_contract_response(
                response.status, envelope.structured, envelope.body_kind
            )
            return response.status, _string_headers(envelope.headers), envelope.body
        header_values = materialize_mapping(
            response.headers,
            response.header_nodes,
            self.context,
            namespace=f"interaction:{interaction.name}:response:headers",
            request=request,
        )
        headers = _string_headers(header_values)
        body, kind, structured = materialize_body(
            response.body,
            self.context,
            namespace=f"interaction:{interaction.name}:response:body",
            request=request,
        )
        self._validate_contract_response(response.status, structured, kind)
        return response.status, headers, body

    def _normalized_request(
        self,
        interaction: Interaction,
        *,
        method: str,
        path: str,
        query: dict[str, JsonValue],
        headers: dict[str, str],
        raw_body: bytes,
        structured: JsonValue | None,
        body_kind: Literal["empty", "structured", "raw"],
    ) -> JsonValue:
        selected_headers: dict[str, JsonValue] = {
            name: headers[name] for name in interaction.request.headers
        }
        if body_kind == "empty":
            body: JsonValue = {"kind": "empty"}
        elif body_kind == "raw":
            body = {
                "kind": "raw",
                "base64": base64.b64encode(raw_body).decode("ascii"),
            }
        else:
            body = {"kind": "structured", "value": structured}
        return {
            "method": method,
            "path": path,
            "query": query,
            "headers": selected_headers,
            "body": body,
        }

    def _event_request(
        self, event: Event, binding: TargetBinding
    ) -> tuple[str, dict[str, str], bytes]:
        request = event.request
        if request.materializer is not None:
            envelope = run_materializer(
                request.materializer,
                phase="event",
                context=self.context,
                request=None,
                expected_method=request.method,
                expected_path=request.path,
            )
            query = envelope.query
            headers = _string_headers(envelope.headers)
            body = envelope.body
        else:
            query = materialize_mapping(
                request.query,
                request.query_nodes,
                self.context,
                namespace=f"event:{event.name}:query",
                request=None,
            )
            header_values = materialize_mapping(
                request.headers,
                request.header_nodes,
                self.context,
                namespace=f"event:{event.name}:headers",
                request=None,
            )
            headers = _string_headers(header_values)
            body, _kind, _structured = materialize_body(
                request.body,
                self.context,
                namespace=f"event:{event.name}:body",
                request=None,
            )
        url = binding.origin.rstrip("/") + request.path + _encode_query(query)
        return url, headers, body

    def _validate_contract_request(
        self,
        structured: JsonValue | None,
        body_kind: Literal["empty", "structured", "raw"],
    ) -> None:
        contract = self.scenario.contract
        if (
            contract is None
            or contract.request_schema is None
            or body_kind != "structured"
        ):
            return
        _validate_schema(
            contract.request_schema,
            structured,
            "double-request-contract-failed",
            self._schema_registry,
        )

    def _validate_contract_response(
        self,
        status: int,
        structured: JsonValue | None,
        body_kind: Literal["empty", "structured", "raw"],
    ) -> None:
        contract = self.scenario.contract
        if contract is None or body_kind != "structured":
            return
        if str(status) in contract.response_schemas:
            schema = contract.response_schemas[str(status)]
        elif "default" in contract.response_schemas:
            schema = contract.response_schemas["default"]
        else:
            raise SvcError(
                "double-response-contract-failed",
                "Response status is absent from the selected operation contract.",
                {"status": status},
            )
        _validate_schema(
            schema,
            structured,
            "double-response-contract-failed",
            self._schema_registry,
        )

    def _journal(
        self,
        kind: Literal["request", "event", "runtime"],
        status: str,
        facts: dict[str, JsonValue],
    ) -> None:
        self._journal_total += 1
        self._entries.append(
            JournalEntry(
                sequence=self._journal_total,
                at=_now(),
                kind=kind,
                status=status,
                facts=_redact_facts(facts),
            )
        )

    @staticmethod
    def _failure_response(
        status: int, code: str, message: str
    ) -> tuple[int, dict[str, str], bytes]:
        body = compact_json({"error": {"code": code, "message": message}})
        return status, {"content-type": "application/json"}, body


class ResponderServer:
    def __init__(self, engine: BoundaryEngine) -> None:
        self.engine = engine
        handler = _handler(engine)
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.server.daemon_threads = True
        self.thread = threading.Thread(
            target=self.server.serve_forever,
            name="svc-double-responder",
            daemon=True,
        )

    @property
    def url(self) -> str:
        host, port = self.server.server_address[:2]
        if isinstance(host, bytes):
            host = host.decode("ascii")
        return f"http://{host}:{port}"

    def start(self) -> None:
        self.thread.start()
        self.engine.ready(self.url)

    def stop(self) -> None:
        self.engine.begin_stop()
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        self.engine.stopped()


def _handler(engine: BoundaryEngine) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def do_GET(self) -> None:
            self._handle()

        def do_POST(self) -> None:
            self._handle()

        def do_PUT(self) -> None:
            self._handle()

        def do_PATCH(self) -> None:
            self._handle()

        def do_DELETE(self) -> None:
            self._handle()

        def do_HEAD(self) -> None:
            self._handle()

        def do_OPTIONS(self) -> None:
            self._handle()

        def _handle(self) -> None:
            self.close_connection = True
            transfer = self.headers.get("Transfer-Encoding")
            lengths = self.headers.get_all("Content-Length", failobj=[])
            if transfer is not None:
                self._write(
                    *BoundaryEngine._failure_response(
                        400,
                        "double-transfer-encoding-unsupported",
                        "Transfer-Encoding is unsupported.",
                    )
                )
                return
            if len(lengths) > 1:
                self._write(
                    *BoundaryEngine._failure_response(
                        400,
                        "double-content-length-invalid",
                        "Content-Length is ambiguous.",
                    )
                )
                return
            if lengths:
                try:
                    length = int(lengths[0])
                except ValueError:
                    self._write(
                        *BoundaryEngine._failure_response(
                            400,
                            "double-content-length-invalid",
                            "Content-Length is invalid.",
                        )
                    )
                    return
            else:
                length = 0
            if length < 0 or length > _MAX_BODY_BYTES:
                self._write(
                    *BoundaryEngine._failure_response(
                        413,
                        "double-request-too-large",
                        "Request body exceeds its byte bound.",
                    )
                )
                return
            body = self.rfile.read(length)
            if len(body) != length:
                self._write(
                    *BoundaryEngine._failure_response(
                        400, "double-request-truncated", "Request body ended early."
                    )
                )
                return
            normalized_headers: dict[str, str] = {}
            for name in self.headers:
                lowered = name.lower()
                values = self.headers.get_all(name, failobj=[])
                if len(values) != 1:
                    self._write(
                        *BoundaryEngine._failure_response(
                            400,
                            "double-header-duplicate",
                            "Duplicate request headers are unsupported.",
                        )
                    )
                    return
                normalized_headers[lowered] = values[0]
            result = engine.handle_request(
                method=self.command,
                target=self.path,
                headers=normalized_headers,
                raw_body=body,
            )
            self._write(*result)

        def _write(self, status: int, headers: dict[str, str], body: bytes) -> None:
            self.send_response_only(status)
            for name, value in headers.items():
                if name.lower() in {"content-length", "connection"}:
                    continue
                self.send_header(name, value)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Connection", "close")
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(body)

        def log_message(self, format: str, *args: Any) -> None:
            return

    return Handler


def _parse_target(target: str) -> tuple[str, dict[str, JsonValue]]:
    if not target.startswith("/") or "#" in target:
        raise SvcError(
            "double-request-target-invalid", "HTTP request target is invalid."
        )
    split = urllib.parse.urlsplit(target)
    if split.scheme or split.netloc:
        raise SvcError(
            "double-request-target-invalid", "Absolute-form targets are unsupported."
        )
    values: dict[str, list[str]] = {}
    if split.query:
        for pair in split.query.split("&"):
            name, separator, value = pair.partition("=")
            if not separator:
                raise SvcError(
                    "double-query-invalid", "Query fields require name=value form."
                )
            decoded_name = _strict_unquote(name)
            decoded_value = _strict_unquote(value)
            values.setdefault(decoded_name, []).append(decoded_value)
    query: dict[str, JsonValue] = {
        name: cast(JsonValue, items[0] if len(items) == 1 else items)
        for name, items in values.items()
    }
    return split.path, query


def _strict_unquote(value: str) -> str:
    index = 0
    while index < len(value):
        if value[index] == "%":
            if index + 2 >= len(value) or any(
                char not in "0123456789abcdefABCDEF"
                for char in value[index + 1 : index + 3]
            ):
                raise SvcError(
                    "double-query-invalid", "Query percent encoding is invalid."
                )
            index += 3
        else:
            index += 1
    try:
        return urllib.parse.unquote_to_bytes(value.replace("+", " ")).decode("utf-8")
    except UnicodeDecodeError as error:
        raise SvcError("double-query-invalid", "Query is not valid UTF-8.") from error


def _encode_query(query: dict[str, JsonValue]) -> str:
    pairs: list[tuple[str, str]] = []
    for name, value in query.items():
        items = value if isinstance(value, list) else [value]
        for item in items:
            if not isinstance(item, str):
                raise SvcError(
                    "double-event-query-invalid",
                    "Event query values must be strings or arrays of strings.",
                )
            pairs.append((name, item))
    return "" if not pairs else "?" + urllib.parse.urlencode(pairs)


def _string_headers(values: Mapping[str, object]) -> dict[str, str]:
    headers: dict[str, str] = {}
    for name, value in values.items():
        lowered = name.lower()
        if not _HTTP_FIELD_NAME.fullmatch(name) or lowered in _RUNTIME_OWNED_HEADERS:
            raise SvcError(
                "double-header-name-invalid",
                "Materialized HTTP header name is invalid or runtime-owned.",
                {"header": name},
            )
        if not isinstance(value, str):
            raise SvcError(
                "double-header-value-invalid",
                "Materialized HTTP header values must be strings.",
                {"header": name},
            )
        if any(
            character != "\t"
            and not 0x20 <= ord(character) <= 0x7E
            and not 0x80 <= ord(character) <= 0xFF
            for character in value
        ):
            raise SvcError(
                "double-header-value-invalid",
                "Materialized HTTP header value contains unsupported characters.",
                {"header": name},
            )
        headers[lowered] = value
    return headers


def _validate_schema(
    schema: JsonValue,
    value: JsonValue,
    code: str,
    registry: SchemaRegistry,
) -> None:
    try:
        errors = schema_validation_errors(schema, value, registry)
    except Exception as error:
        raise SvcError(
            code,
            "Selected contract schema could not be evaluated.",
            {"reason": str(error)},
        ) from error
    if errors:
        first = errors[0]
        raise SvcError(
            code,
            "Value does not satisfy the selected operation schema.",
            {"path": list(first.path), "reason": first.message},
        )


def _redact_facts(facts: dict[str, JsonValue]) -> dict[str, JsonValue]:
    result: dict[str, JsonValue] = {}
    for key, value in facts.items():
        if key.lower() in _SENSITIVE_HEADERS:
            result[key] = "<redacted>"
        else:
            result[key] = value
    return result


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
