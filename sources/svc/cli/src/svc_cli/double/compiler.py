"""Strict BSL v0 compiler producing runtime-neutral normalized scenarios."""

from __future__ import annotations

import base64
import hashlib
import json
import math
import os
import re
import shutil
import uuid
from collections.abc import Iterable, Mapping, MutableSet, Sequence
from datetime import datetime
from pathlib import Path
from typing import Any, Literal, NoReturn, TypeAlias, cast
from urllib.parse import urlsplit

from pydantic import JsonValue
from ruamel.yaml.comments import CommentedMap, CommentedSeq

from ..errors import SvcError
from .cel_profile import (
    MAX_CEL_EXPRESSION_BYTES,
    CelExpressionTooLarge,
    CelProfileError,
    inspect_expression,
    regex_matches,
    validate_expression,
    validate_regex,
)
from .model import (
    Body,
    CaptureValueNode,
    Contract,
    DerivedValueNode,
    EnumMatcher,
    Event,
    ExactMatcher,
    ExampleValueNode,
    FormUrlencodedBody,
    GeneratedValueNode,
    Interaction,
    LiteralValueNode,
    ManagedValueNode,
    MatchValueNode,
    Matcher,
    Materializer,
    PathPart,
    Provenance,
    RangeMatcher,
    RawBody,
    RegexMatcher,
    Request,
    Response,
    Scenario,
    SemanticMatcher,
    Snapshot,
    SourceLocation,
    StructuredBody,
    ValueNode,
)
from .openapi_profile import OpenApiProfileError, compile_openapi_profile
from .sources import LocalSources
from .yaml_surface import (
    MAX_YAML_DEPTH as MAX_YAML_DEPTH,
    MAX_YAML_NODES as MAX_YAML_NODES,
    load_yaml,
    source_location,
)


MAX_MODULE_BYTES = 1_048_576
MAX_MATERIALIZER_ARGUMENTS = 64
MAX_MATERIALIZER_TIMEOUT_MS = 30_000
MAX_MATERIALIZER_OUTPUT_BYTES = 8_388_608

_NAME_RE = re.compile(r"^[a-z][a-z0-9.-]*$")
_BINDING_RE = re.compile(r"^[a-z][a-z0-9_]*$")
_METHOD_RE = re.compile(r"^[A-Z][A-Z0-9!#$%&'*+.^_`|~-]*$")
_HEADER_RE = re.compile(r"^[!#$%&'*+.^_`|~0-9A-Za-z-]+$")
_REQUEST_NODE_KINDS = frozenset({"literal", "match", "capture", "managed"})
_OUTPUT_NODE_KINDS = frozenset(
    {"literal", "example", "derived", "generated", "managed"}
)
_PROVENANCE_KINDS = frozenset(
    {
        "consumer-requirement",
        "provider-contract",
        "provider-documentation",
        "provider-capture",
        "synthetic",
    }
)
_SEMANTIC_VALIDATORS = {
    ("rfc.uuid", "svc.rfc-uuid/v1"),
    ("rfc3339", "svc.rfc3339/v1"),
}
_OPAQUE_TOKEN_ALPHABETS = frozenset({"lower-alphanumeric", "alphanumeric", "hex-lower"})

_Phase: TypeAlias = Literal["request", "response", "event"]


class _Compiler:
    def __init__(self, module: Path) -> None:
        self.sources = LocalSources(module)
        self.module = self.sources.module
        self.workspace = self.sources.workspace
        self.snapshots = self.sources.snapshots

    def compile(self) -> Scenario:
        raw = self.sources.read_bounded(
            self.module, MAX_MODULE_BYTES, "module-too-large"
        )
        document = load_yaml(raw, self.module, self.module, is_module=True)
        root = self._mapping(document, (), "Module must be a mapping.")
        self._keys(root, (), required={"language", "scenario"})

        language = self._string(root["language"], ("language",))
        if language != "svc.double/v0":
            self._fail(
                "unsupported-double-language",
                "The module language must be exactly 'svc.double/v0'.",
                root,
                ("language",),
                key="language",
                details={"language": language},
            )

        authored = self._mapping(
            root["scenario"], ("scenario",), "Scenario must be a mapping."
        )
        self._keys(
            authored,
            ("scenario",),
            required={"name", "claim", "boundary", "interactions"},
            optional={"policy", "events"},
        )
        name = self._name(authored["name"], ("scenario", "name"), "scenario")
        claim = self._nonempty_string(authored["claim"], ("scenario", "claim"))
        boundary_name, contract_spec = self._compile_boundary(
            authored["boundary"], ("scenario", "boundary")
        )
        event_target_policy = self._compile_policy(
            authored.get("policy"), ("scenario", "policy")
        )

        declared_bindings: set[str] = set()
        available_bindings: set[str] = set()
        interactions = self._compile_interactions(
            authored["interactions"], declared_bindings, available_bindings
        )
        events = self._compile_events(
            authored.get("events", CommentedSeq()),
            declared_bindings,
            available_bindings,
        )
        contract = (
            self._compile_contract(contract_spec) if contract_spec is not None else None
        )
        if contract is not None:
            self._check_contract_coverage(contract, interactions)

        snapshots = tuple(self.snapshots[key] for key in sorted(self.snapshots))
        uses_materializer = any(
            item.response.materializer is not None for item in interactions
        ) or any(item.request.materializer is not None for item in events)
        fidelity = ["http-exact-boundary", "provenance-declared"]
        if any(
            item.request.body is not None
            and item.request.body.kind == "structured"
            or item.response.body is not None
            and item.response.body.kind == "structured"
            for item in interactions
        ) or any(
            item.request.body is not None and item.request.body.kind == "structured"
            for item in events
        ):
            fidelity.append("json.compact-utf8/v1")
        if any(
            item.request.body is not None
            and item.request.body.kind == "form-urlencoded"
            for item in interactions
        ):
            fidelity.append("form-urlencoded.field-matching/v1")
        if contract is not None:
            fidelity.append("selected-operation-schema")
        if snapshots:
            fidelity.append("local-snapshots")

        nonclaims = [
            "provider-behavior: not-claimed",
            "provider-currentness: not-claimed",
            "consumer-egress: not-enforced",
        ]
        if uses_materializer:
            nonclaims.extend(
                (
                    "materializer-code-identity: not-enforced",
                    "materializer-determinism: not-enforced",
                    "materializer-egress: not-enforced",
                    "materializer-fidelity: not-enforced",
                )
            )

        scenario = Scenario(
            module_path=str(self.module),
            workspace_root=str(self.workspace),
            name=name,
            claim=claim,
            boundary_name=boundary_name,
            event_target_policy=event_target_policy,
            interactions=interactions,
            events=events,
            contract=contract,
            snapshots=snapshots,
            fidelity=tuple(fidelity),
            nonclaims=tuple(nonclaims),
            scenario_digest="",
            uses_materializer=uses_materializer,
        )
        digest = _scenario_digest(scenario)
        return scenario.model_copy(update={"scenario_digest": digest})

    def _compile_boundary(
        self, value: object, path: tuple[PathPart, ...]
    ) -> tuple[str, CommentedMap | None]:
        boundary = self._mapping(value, path, "Boundary must be a mapping.")
        self._keys(boundary, path, required={"name", "protocol"}, optional={"contract"})
        name = self._name(boundary["name"], (*path, "name"), "boundary")
        protocol = self._string(boundary["protocol"], (*path, "protocol"))
        if protocol != "http":
            self._fail(
                "unsupported-double-protocol",
                "BSL v0 supports only the HTTP boundary protocol.",
                boundary,
                (*path, "protocol"),
                key="protocol",
                details={"protocol": protocol},
            )
        contract = boundary.get("contract")
        if contract is None:
            return name, None
        return name, self._mapping(
            contract, (*path, "contract"), "Contract must be a mapping."
        )

    def _compile_policy(
        self, value: object | None, path: tuple[PathPart, ...]
    ) -> Literal["loopback-only", "explicit-remote"]:
        if value is None:
            return "loopback-only"
        policy = self._mapping(value, path, "Policy must be a mapping.")
        self._keys(policy, path, optional={"event-targets"})
        selected = policy.get("event-targets", "loopback-only")
        selected_text = self._string(selected, (*path, "event-targets"))
        if selected_text not in {"loopback-only", "explicit-remote"}:
            self._fail(
                "invalid-double-policy",
                "event-targets must be 'loopback-only' or 'explicit-remote'.",
                policy,
                (*path, "event-targets"),
                key="event-targets",
            )
        return cast(Literal["loopback-only", "explicit-remote"], selected_text)

    def _compile_interactions(
        self,
        value: object,
        declared: MutableSet[str],
        available: MutableSet[str],
    ) -> tuple[Interaction, ...]:
        path: tuple[PathPart, ...] = ("scenario", "interactions")
        items = self._sequence(
            value, path, "interactions must be a non-empty sequence."
        )
        if not items:
            self._fail(
                "invalid-double-module", "interactions must not be empty.", items, path
            )
        result: list[Interaction] = []
        names: set[str] = set()
        for index, item in enumerate(items):
            interaction_bindings: set[str] = set()
            item_path = (*path, index)
            interaction = self._mapping(
                item, item_path, "Interaction must be a mapping."
            )
            self._keys(
                interaction,
                item_path,
                required={"name", "provenance", "request", "response"},
            )
            name = self._name(interaction["name"], (*item_path, "name"), "interaction")
            self._unique_name(
                name, names, interaction, (*item_path, "name"), "interaction"
            )
            provenance = self._compile_provenance(
                interaction["provenance"], (*item_path, "provenance")
            )
            request = self._compile_request(
                interaction["request"],
                (*item_path, "request"),
                "request",
                declared,
                interaction_bindings,
            )
            response = self._compile_response(
                interaction["response"],
                (*item_path, "response"),
                declared,
                interaction_bindings,
            )
            result.append(
                Interaction(
                    name=name,
                    provenance=provenance,
                    request=request,
                    response=response,
                )
            )
            for binding in interaction_bindings:
                available.add(binding)
        return tuple(result)

    def _compile_events(
        self,
        value: object,
        declared: MutableSet[str],
        available: MutableSet[str],
    ) -> tuple[Event, ...]:
        path: tuple[PathPart, ...] = ("scenario", "events")
        items = self._sequence(value, path, "events must be a sequence.")
        result: list[Event] = []
        names: set[str] = set()
        for index, item in enumerate(items):
            event_bindings = set(available)
            item_path = (*path, index)
            event = self._mapping(item, item_path, "Event must be a mapping.")
            self._keys(
                event, item_path, required={"name", "target", "provenance", "request"}
            )
            name = self._name(event["name"], (*item_path, "name"), "event")
            self._unique_name(name, names, event, (*item_path, "name"), "event")
            target = self._name(event["target"], (*item_path, "target"), "event target")
            provenance = self._compile_provenance(
                event["provenance"], (*item_path, "provenance")
            )
            request = self._compile_request(
                event["request"],
                (*item_path, "request"),
                "event",
                declared,
                event_bindings,
            )
            result.append(
                Event(name=name, target=target, provenance=provenance, request=request)
            )
        return tuple(result)

    def _compile_request(
        self,
        value: object,
        path: tuple[PathPart, ...],
        phase: Literal["request", "event"],
        declared: MutableSet[str],
        available: MutableSet[str],
    ) -> Request:
        request = self._mapping(value, path, "Request must be a mapping.")
        self._keys(
            request,
            path,
            required={"method", "path"},
            optional={"query", "headers", "body", "materializer"},
        )
        method = self._method(request["method"], request, (*path, "method"))
        request_path = self._http_path(request["path"], request, (*path, "path"))
        query, query_nodes = self._compile_query(
            request.get("query", CommentedMap()),
            (*path, "query"),
            phase,
            declared,
            available,
        )
        headers, header_nodes = self._compile_headers(
            request.get("headers", CommentedMap()),
            (*path, "headers"),
            phase,
            declared,
            available,
        )
        body = (
            self._compile_body(
                request["body"], (*path, "body"), phase, declared, available
            )
            if "body" in request
            else None
        )
        materializer = (
            self._compile_materializer(request["materializer"], (*path, "materializer"))
            if "materializer" in request
            else None
        )
        if materializer is not None and any(
            field in request for field in ("query", "headers", "body")
        ):
            self._fail(
                "invalid-double-materializer",
                "A materialized request cannot also declare query, headers, or body.",
                request,
                path,
            )
        if phase == "request" and materializer is not None:
            self._fail(
                "invalid-double-materializer",
                "An interaction request cannot use a materializer.",
                request,
                (*path, "materializer"),
                key="materializer",
            )
        return Request(
            method=method,
            path=request_path,
            query=query,
            query_nodes=query_nodes,
            headers=headers,
            header_nodes=header_nodes,
            body=body,
            materializer=materializer,
        )

    def _compile_response(
        self,
        value: object,
        path: tuple[PathPart, ...],
        declared: MutableSet[str],
        available: MutableSet[str],
    ) -> Response:
        response = self._mapping(value, path, "Response must be a mapping.")
        self._keys(
            response,
            path,
            required={"status"},
            optional={"headers", "body", "materializer"},
        )
        status = response["status"]
        if (
            isinstance(status, bool)
            or not isinstance(status, int)
            or not 100 <= status <= 599
        ):
            self._fail(
                "invalid-double-http-status",
                "Response status must be an integer from 100 through 599.",
                response,
                (*path, "status"),
                key="status",
            )
        headers, header_nodes = self._compile_headers(
            response.get("headers", CommentedMap()),
            (*path, "headers"),
            "response",
            declared,
            available,
        )
        body = (
            self._compile_body(
                response["body"], (*path, "body"), "response", declared, available
            )
            if "body" in response
            else None
        )
        materializer = (
            self._compile_materializer(
                response["materializer"], (*path, "materializer")
            )
            if "materializer" in response
            else None
        )
        if materializer is not None and ("headers" in response or "body" in response):
            self._fail(
                "invalid-double-materializer",
                "A materialized response cannot also declare headers or body.",
                response,
                path,
            )
        return Response(
            status=status,
            headers=headers,
            header_nodes=header_nodes,
            body=body,
            materializer=materializer,
        )

    def _compile_query(
        self,
        value: object,
        path: tuple[PathPart, ...],
        phase: _Phase,
        declared: MutableSet[str],
        available: MutableSet[str],
    ) -> tuple[dict[str, JsonValue], tuple[ValueNode, ...]]:
        query = self._mapping(value, path, "query must be a mapping.")
        result: dict[str, JsonValue] = {}
        nodes: list[ValueNode] = []
        for key, authored in query.items():
            if not isinstance(key, str) or not key:
                self._fail(
                    "invalid-double-query",
                    "Query names must be non-empty strings.",
                    query,
                    path,
                )
            compiled, item_nodes = self._compile_value(
                authored,
                phase,
                (key,),
                (*path, key),
                declared,
                available,
            )
            if not _query_shape(authored) or not _string_surface_plan(
                {key: compiled}, item_nodes
            ):
                self._fail(
                    "invalid-double-query",
                    "Query values must be strings, typed string values, or arrays of those values.",
                    query,
                    (*path, key),
                    key=key,
                )
            result[key] = compiled
            nodes.extend(item_nodes)
        return result, tuple(nodes)

    def _compile_headers(
        self,
        value: object,
        path: tuple[PathPart, ...],
        phase: _Phase,
        declared: MutableSet[str],
        available: MutableSet[str],
    ) -> tuple[dict[str, JsonValue], tuple[ValueNode, ...]]:
        headers = self._mapping(value, path, "headers must be a mapping.")
        result: dict[str, JsonValue] = {}
        nodes: list[ValueNode] = []
        for key, authored in headers.items():
            if not isinstance(key, str) or not _HEADER_RE.fullmatch(key):
                self._fail(
                    "invalid-double-header",
                    "Header names must be HTTP field names.",
                    headers,
                    path,
                )
            normalized = key.lower()
            if normalized in result:
                self._fail(
                    "duplicate-double-header",
                    "Header names are case-insensitive and must be unique.",
                    headers,
                    (*path, key),
                    key=key,
                    details={"header": normalized},
                )
            if not isinstance(authored, str) and not _is_typed_value(authored):
                self._fail(
                    "invalid-double-header",
                    "Header values must be strings or typed values.",
                    headers,
                    (*path, key),
                    key=key,
                )
            compiled, item_nodes = self._compile_value(
                authored,
                phase,
                (normalized,),
                (*path, key),
                declared,
                available,
            )
            if not _string_surface_plan({normalized: compiled}, item_nodes):
                self._fail(
                    "invalid-double-header",
                    "Typed header values must match or materialize strings.",
                    headers,
                    (*path, key),
                    key=key,
                )
            result[normalized] = compiled
            nodes.extend(item_nodes)
        return result, tuple(nodes)

    def _compile_body(
        self,
        value: object,
        path: tuple[PathPart, ...],
        phase: _Phase,
        declared: MutableSet[str],
        available: MutableSet[str],
    ) -> Body:
        body = self._mapping(value, path, "Body must be a mapping.")
        self._keys(
            body,
            path,
            required=set(),
            optional={"structured", "form-urlencoded", "raw"},
        )
        if len(body) != 1:
            self._fail(
                "invalid-double-body",
                "Body must contain exactly one of structured, form-urlencoded, or raw.",
                body,
                path,
            )
        if "structured" in body:
            template, nodes = self._compile_value(
                body["structured"],
                phase,
                (),
                (*path, "structured"),
                declared,
                available,
            )
            return StructuredBody(template=template, nodes=nodes)

        if "form-urlencoded" in body:
            if phase != "request":
                self._fail(
                    "invalid-double-body",
                    "form-urlencoded is admitted only for interaction requests.",
                    body,
                    (*path, "form-urlencoded"),
                    key="form-urlencoded",
                )
            fields = self._mapping(
                body["form-urlencoded"],
                (*path, "form-urlencoded"),
                "form-urlencoded must be a mapping.",
            )
            form_template: dict[str, JsonValue] = {}
            form_nodes: list[ValueNode] = []
            for key, authored in fields.items():
                if not isinstance(key, str) or not key:
                    self._fail(
                        "invalid-double-form",
                        "Form field names must be non-empty strings.",
                        fields,
                        (*path, "form-urlencoded"),
                    )
                compiled, field_nodes = self._compile_value(
                    authored,
                    phase,
                    (key,),
                    (*path, "form-urlencoded", key),
                    declared,
                    available,
                )
                if not _query_shape(authored) or not _string_surface_plan(
                    {key: compiled}, field_nodes
                ):
                    self._fail(
                        "invalid-double-form",
                        "Form values must be strings, typed string values, or arrays of those values.",
                        fields,
                        (*path, "form-urlencoded", key),
                        key=key,
                    )
                form_template[key] = compiled
                form_nodes.extend(field_nodes)
            return FormUrlencodedBody(
                template=form_template,
                nodes=tuple(form_nodes),
            )

        raw = self._mapping(
            body["raw"], (*path, "raw"), "Raw body must be a typed managed value."
        )
        if set(raw) != {"$bsl"}:
            self._fail(
                "invalid-double-body",
                "Raw body must contain exactly one managed $bsl node.",
                raw,
                (*path, "raw"),
            )
        spec = self._mapping(
            raw["$bsl"], (*path, "raw", "$bsl"), "$bsl must be a mapping."
        )
        node = self._compile_typed_node(
            spec,
            phase,
            (),
            (*path, "raw"),
            raw,
            declared,
            available,
            raw=True,
        )
        if node.kind != "managed" or node.managed_snapshot is None:
            self._fail(
                "invalid-double-body",
                "Raw body supports only a managed typed value.",
                raw,
                (*path, "raw"),
            )
        return RawBody(
            raw=node.managed_snapshot,
            media_type=node.media_type,
        )

    def _compile_value(
        self,
        value: object,
        phase: _Phase,
        ir_path: tuple[PathPart, ...],
        source_path: tuple[PathPart, ...],
        declared: MutableSet[str],
        available: MutableSet[str],
    ) -> tuple[JsonValue, tuple[ValueNode, ...]]:
        if _is_typed_value(value):
            typed = cast(Mapping[str, object], value)
            spec = self._mapping(
                typed["$bsl"], (*source_path, "$bsl"), "$bsl must be a mapping."
            )
            node = self._compile_typed_node(
                spec,
                phase,
                ir_path,
                source_path,
                cast(CommentedMap, value),
                declared,
                available,
                raw=False,
            )
            return cast(JsonValue, node.value), (node,)
        if isinstance(value, Mapping):
            result: dict[str, JsonValue] = {}
            nodes: list[ValueNode] = []
            for key, item in value.items():
                if not isinstance(key, str):
                    self._fail(
                        "invalid-double-json-value",
                        "Structured JSON object keys must be strings.",
                        value,
                        source_path,
                    )
                compiled, item_nodes = self._compile_value(
                    item,
                    phase,
                    (*ir_path, key),
                    (*source_path, key),
                    declared,
                    available,
                )
                result[key] = compiled
                nodes.extend(item_nodes)
            return result, tuple(nodes)
        if isinstance(value, Sequence) and not isinstance(
            value, (str, bytes, bytearray)
        ):
            result_list: list[JsonValue] = []
            nodes = []
            for index, item in enumerate(value):
                compiled, item_nodes = self._compile_value(
                    item,
                    phase,
                    (*ir_path, index),
                    (*source_path, index),
                    declared,
                    available,
                )
                result_list.append(compiled)
                nodes.extend(item_nodes)
            return result_list, tuple(nodes)
        return _json_value(value, self, source_path), ()

    def _compile_typed_node(
        self,
        spec: CommentedMap,
        phase: _Phase,
        ir_path: tuple[PathPart, ...],
        source_path: tuple[PathPart, ...],
        authored_node: CommentedMap,
        declared: MutableSet[str],
        available: MutableSet[str],
        *,
        raw: bool,
    ) -> ValueNode:
        if "kind" not in spec:
            self._fail(
                "invalid-double-value-node",
                "A $bsl node requires kind.",
                spec,
                (*source_path, "$bsl"),
            )
        kind = self._string(spec["kind"], (*source_path, "$bsl", "kind"))
        allowed = _REQUEST_NODE_KINDS if phase == "request" else _OUTPUT_NODE_KINDS
        if kind not in allowed:
            self._fail(
                "illegal-double-value-phase",
                f"Typed value kind '{kind}' is not legal in {phase} phase.",
                spec,
                (*source_path, "$bsl", "kind"),
                key="kind",
                details={"kind": kind, "phase": phase},
            )
        location = self._location(authored_node, source_path, key="$bsl")
        if kind == "literal":
            self._keys(
                spec,
                (*source_path, "$bsl"),
                required={"kind", "value"},
                optional={"bind"} if phase != "request" else set(),
            )
            value = _json_value(spec["value"], self, (*source_path, "$bsl", "value"))
            bind = (
                self._optional_output_binding(spec, source_path, declared, available)
                if phase != "request"
                else None
            )
            return LiteralValueNode(
                path=ir_path, value=value, bind=bind, location=location
            )
        if kind in {"match", "capture"}:
            required = {"kind", "match"}
            optional = {"example"}
            if kind == "capture":
                required.add("name")
            self._keys(
                spec, (*source_path, "$bsl"), required=required, optional=optional
            )
            matcher = self._compile_matcher(
                spec["match"], (*source_path, "$bsl", "match")
            )
            example = (
                _json_value(spec["example"], self, (*source_path, "$bsl", "example"))
                if "example" in spec
                else None
            )
            if "example" in spec:
                self._check_example(
                    matcher, example, spec, (*source_path, "$bsl", "example")
                )
            if kind == "capture":
                name = self._binding_name(spec["name"], (*source_path, "$bsl", "name"))
                self._declare_binding(
                    name, declared, available, spec, (*source_path, "$bsl", "name")
                )
                return CaptureValueNode(
                    path=ir_path,
                    value=example,
                    matcher=matcher,
                    name=name,
                    location=location,
                )
            return MatchValueNode(
                path=ir_path,
                value=example,
                matcher=matcher,
                location=location,
            )
        if kind == "example":
            self._keys(
                spec,
                (*source_path, "$bsl"),
                required={"kind", "value"},
                optional={"validate", "bind"},
            )
            value = _json_value(spec["value"], self, (*source_path, "$bsl", "value"))
            validator = (
                self._compile_matcher(
                    spec["validate"], (*source_path, "$bsl", "validate")
                )
                if "validate" in spec
                else None
            )
            if validator is not None:
                self._check_example(
                    validator, value, spec, (*source_path, "$bsl", "value")
                )
            bind = self._optional_output_binding(spec, source_path, declared, available)
            return ExampleValueNode(
                path=ir_path,
                value=value,
                bind=bind,
                validator=validator,
                location=location,
            )
        if kind == "derived":
            self._keys(
                spec,
                (*source_path, "$bsl"),
                required={"kind", "expression", "validate"},
                optional={"bind"},
            )
            expression = self._nonempty_string(
                spec["expression"], (*source_path, "$bsl", "expression")
            )
            self._compile_cel(
                expression,
                phase,
                available,
                spec,
                (*source_path, "$bsl", "expression"),
            )
            validator = self._compile_matcher(
                spec["validate"], (*source_path, "$bsl", "validate")
            )
            bind = self._optional_output_binding(spec, source_path, declared, available)
            return DerivedValueNode(
                path=ir_path,
                expression=expression,
                bind=bind,
                validator=validator,
                location=location,
            )
        if kind == "generated":
            self._keys(
                spec,
                (*source_path, "$bsl"),
                required={"kind", "semantic", "using", "validate"},
                optional={"options", "bind"},
            )
            semantic = self._nonempty_string(
                spec["semantic"], (*source_path, "$bsl", "semantic")
            )
            using = self._nonempty_string(
                spec["using"], (*source_path, "$bsl", "using")
            )
            options = self._compile_generator(
                semantic, using, spec.get("options"), spec, source_path
            )
            validator = self._compile_matcher(
                spec["validate"], (*source_path, "$bsl", "validate")
            )
            self._check_generator_validator(
                semantic, using, options, validator, spec, source_path
            )
            bind = self._optional_output_binding(spec, source_path, declared, available)
            return GeneratedValueNode(
                path=ir_path,
                semantic=semantic,
                using=using,
                options=options,
                bind=bind,
                validator=validator,
                location=location,
            )
        if kind == "managed":
            self._keys(
                spec,
                (*source_path, "$bsl"),
                required={"kind", "source", "media-type"},
                optional=set() if raw or phase == "request" else {"validate", "bind"},
            )
            source = self._nonempty_string(
                spec["source"], (*source_path, "$bsl", "source")
            )
            media_type = self._nonempty_string(
                spec["media-type"], (*source_path, "$bsl", "media-type")
            )
            snapshot = self.sources.snapshot_local(
                source, (*source_path, "$bsl", "source")
            )
            managed_value: JsonValue | None = None
            validator = None
            if not raw:
                if media_type != "application/json":
                    self._fail(
                        "invalid-double-managed-value",
                        "A structured managed value must use media-type application/json.",
                        spec,
                        (*source_path, "$bsl", "media-type"),
                        key="media-type",
                    )
                managed_value = self._load_managed_json(
                    snapshot, (*source_path, "$bsl", "source")
                )
                if "validate" in spec:
                    validator = self._compile_matcher(
                        spec["validate"], (*source_path, "$bsl", "validate")
                    )
                    self._check_example(
                        validator,
                        managed_value,
                        spec,
                        (*source_path, "$bsl", "source"),
                    )
            bind = (
                self._optional_output_binding(spec, source_path, declared, available)
                if not raw and phase != "request"
                else None
            )
            return ManagedValueNode(
                path=ir_path,
                value=managed_value,
                bind=bind,
                validator=validator,
                managed_snapshot=snapshot,
                media_type=media_type,
                location=location,
            )
        raise AssertionError(f"unhandled BSL value kind: {kind}")

    def _optional_output_binding(
        self,
        spec: CommentedMap,
        source_path: tuple[PathPart, ...],
        declared: MutableSet[str],
        available: MutableSet[str],
    ) -> str | None:
        if "bind" not in spec:
            return None
        name = self._binding_name(spec["bind"], (*source_path, "$bsl", "bind"))
        self._declare_binding(
            name, declared, available, spec, (*source_path, "$bsl", "bind")
        )
        return name

    def _compile_matcher(self, value: object, path: tuple[PathPart, ...]) -> Matcher:
        matcher = self._mapping(value, path, "Matcher or validator must be a mapping.")
        if "kind" not in matcher:
            self._fail(
                "invalid-double-matcher", "Matcher requires kind.", matcher, path
            )
        kind = self._string(matcher["kind"], (*path, "kind"))
        if kind == "exact":
            self._keys(matcher, path, required={"kind", "value"})
            return ExactMatcher(
                value=_json_value(matcher["value"], self, (*path, "value")),
            )
        if kind == "enum":
            self._keys(matcher, path, required={"kind", "values"})
            values = self._sequence(
                matcher["values"], (*path, "values"), "enum values must be a sequence."
            )
            if not values:
                self._fail(
                    "invalid-double-matcher",
                    "enum values must not be empty.",
                    values,
                    (*path, "values"),
                )
            normalized = tuple(
                _json_value(item, self, (*path, "values", index))
                for index, item in enumerate(values)
            )
            first_type = _json_type(normalized[0])
            if any(_json_type(item) != first_type for item in normalized[1:]):
                self._fail(
                    "invalid-double-matcher",
                    "enum values must all have the same JSON type.",
                    matcher,
                    path,
                )
            return EnumMatcher(values=normalized)
        if kind == "range":
            self._keys(
                matcher, path, required={"kind"}, optional={"minimum", "maximum"}
            )
            if "minimum" not in matcher and "maximum" not in matcher:
                self._fail(
                    "invalid-double-matcher",
                    "range requires minimum or maximum.",
                    matcher,
                    path,
                )
            if ("minimum" in matcher and matcher["minimum"] is None) or (
                "maximum" in matcher and matcher["maximum"] is None
            ):
                self._fail(
                    "invalid-double-matcher",
                    "Authored range bounds cannot be null.",
                    matcher,
                    path,
                )
            minimum = _number_or_none(matcher.get("minimum"), self, (*path, "minimum"))
            maximum = _number_or_none(matcher.get("maximum"), self, (*path, "maximum"))
            if minimum is not None and maximum is not None and minimum > maximum:
                self._fail(
                    "invalid-double-matcher",
                    "range minimum cannot exceed maximum.",
                    matcher,
                    path,
                )
            if minimum is None:
                assert maximum is not None
                return RangeMatcher(maximum=maximum)
            if maximum is None:
                return RangeMatcher(minimum=minimum)
            return RangeMatcher(minimum=minimum, maximum=maximum)
        if kind == "regex":
            self._keys(matcher, path, required={"kind", "pattern"})
            pattern = self._nonempty_string(matcher["pattern"], (*path, "pattern"))
            self._compile_regex(pattern, matcher, (*path, "pattern"))
            return RegexMatcher(pattern=pattern)
        if kind == "semantic":
            self._keys(matcher, path, required={"kind", "semantic", "using"})
            semantic = self._nonempty_string(matcher["semantic"], (*path, "semantic"))
            using = self._nonempty_string(matcher["using"], (*path, "using"))
            if (semantic, using) not in _SEMANTIC_VALIDATORS:
                self._fail(
                    "unsupported-double-validator",
                    "The semantic validator is not in the BSL v0 registry.",
                    matcher,
                    path,
                    details={"semantic": semantic, "using": using},
                )
            return SemanticMatcher(semantic=semantic, using=using)
        self._fail(
            "unsupported-double-matcher",
            "Matcher kind is not in the BSL v0 algebra.",
            matcher,
            (*path, "kind"),
            key="kind",
            details={"kind": kind},
        )

    def _compile_generator(
        self,
        semantic: str,
        using: str,
        value: object | None,
        owner: CommentedMap,
        source_path: tuple[PathPart, ...],
    ) -> dict[str, JsonValue]:
        path = (*source_path, "$bsl", "options")
        options = (
            self._mapping(value, path, "Generator options must be a mapping.")
            if value is not None
            else CommentedMap()
        )
        if using == "svc.uuid-v4/v1":
            expected_semantic = "rfc.uuid"
            self._keys(options, path)
        elif using == "svc.opaque-token/v1":
            expected_semantic = "opaque-token"
            self._keys(options, path, required={"alphabet", "length"})
            alphabet = self._string(options["alphabet"], (*path, "alphabet"))
            if alphabet not in _OPAQUE_TOKEN_ALPHABETS:
                self._fail(
                    "invalid-double-generator-options",
                    "opaque-token alphabet is not in the BSL v0 registry.",
                    options,
                    (*path, "alphabet"),
                    key="alphabet",
                )
            length = options["length"]
            if (
                isinstance(length, bool)
                or not isinstance(length, int)
                or not 1 <= length <= 1024
            ):
                self._fail(
                    "invalid-double-generator-options",
                    "opaque-token length must be an integer from 1 through 1024.",
                    options,
                    (*path, "length"),
                    key="length",
                )
        elif using == "svc.bounded-integer/v1":
            expected_semantic = "bounded-integer"
            self._keys(options, path, required={"minimum", "maximum"})
            minimum = _number_or_none(
                options["minimum"], self, (*path, "minimum"), integer=True
            )
            maximum = _number_or_none(
                options["maximum"], self, (*path, "maximum"), integer=True
            )
            if minimum is None or maximum is None or minimum > maximum:
                self._fail(
                    "invalid-double-generator-options",
                    "bounded-integer requires integer minimum <= maximum.",
                    options,
                    path,
                )
        elif using == "svc.enum-choice/v1":
            expected_semantic = "enum-choice"
            self._keys(options, path, required={"values"})
            values = self._sequence(
                options["values"],
                (*path, "values"),
                "enum-choice values must be a sequence.",
            )
            if not values:
                self._fail(
                    "invalid-double-generator-options",
                    "enum-choice values must not be empty.",
                    options,
                    path,
                )
            normalized = [
                _json_value(item, self, (*path, "values", index))
                for index, item in enumerate(values)
            ]
            if any(
                _json_type(item) != _json_type(normalized[0]) for item in normalized[1:]
            ):
                self._fail(
                    "invalid-double-generator-options",
                    "enum-choice values must have one JSON type.",
                    options,
                    path,
                )
        elif using == "svc.fixed-clock-rfc3339/v1":
            expected_semantic = "rfc3339"
            self._keys(options, path)
        else:
            self._fail(
                "unsupported-double-generator",
                "The generator is not in the closed BSL v0 registry.",
                owner,
                (*source_path, "$bsl", "using"),
                key="using",
                details={"using": using},
            )
        if semantic != expected_semantic:
            self._fail(
                "invalid-double-generator-semantic",
                "Generator semantic does not match its registered identity.",
                owner,
                (*source_path, "$bsl", "semantic"),
                key="semantic",
                details={
                    "semantic": semantic,
                    "using": using,
                    "expected": expected_semantic,
                },
            )
        return {
            str(key): _json_value(item, self, (*path, str(key)))
            for key, item in options.items()
        }

    def _check_generator_validator(
        self,
        semantic: str,
        using: str,
        options: Mapping[str, JsonValue],
        validator: Matcher,
        owner: CommentedMap,
        source_path: tuple[PathPart, ...],
    ) -> None:
        expected_type = "number" if using == "svc.bounded-integer/v1" else "string"
        if using == "svc.enum-choice/v1":
            values = cast(list[JsonValue], options["values"])
            expected_type = _json_type(values[0])
        if validator.kind == "range" and expected_type != "number":
            self._generator_validator_failure(
                owner, source_path, semantic, validator.kind
            )
        if validator.kind in {"regex", "semantic"} and expected_type != "string":
            self._generator_validator_failure(
                owner, source_path, semantic, validator.kind
            )
        if validator.kind == "semantic" and (
            validator.semantic != semantic
            or (using == "svc.uuid-v4/v1" and validator.using != "svc.rfc-uuid/v1")
            or (
                using == "svc.fixed-clock-rfc3339/v1"
                and validator.using != "svc.rfc3339/v1"
            )
        ):
            self._generator_validator_failure(
                owner, source_path, semantic, validator.kind
            )
        if validator.kind == "exact" and _json_type(validator.value) != expected_type:
            self._generator_validator_failure(
                owner, source_path, semantic, validator.kind
            )
        if (
            validator.kind == "enum"
            and validator.values
            and _json_type(validator.values[0]) != expected_type
        ):
            self._generator_validator_failure(
                owner, source_path, semantic, validator.kind
            )

    def _generator_validator_failure(
        self,
        owner: CommentedMap,
        source_path: tuple[PathPart, ...],
        semantic: str,
        validator_kind: str,
    ) -> None:
        self._fail(
            "invalid-double-generator-validator",
            "Generator output and validator are semantically incompatible.",
            owner,
            (*source_path, "$bsl", "validate"),
            key="validate",
            details={"semantic": semantic, "validator_kind": validator_kind},
        )

    def _compile_cel(
        self,
        expression: str,
        phase: _Phase,
        available: MutableSet[str],
        owner: CommentedMap,
        path: tuple[PathPart, ...],
    ) -> None:
        try:
            inspection = inspect_expression(expression)
        except CelExpressionTooLarge:
            self._fail(
                "double-cel-expression-too-large",
                "CEL expression exceeds the BSL v0 byte bound.",
                owner,
                path,
                key="expression",
                details={"max_bytes": MAX_CEL_EXPRESSION_BYTES},
            )
        if inspection.dynamic_binding_access:
            self._fail(
                "dynamic-double-binding-reference",
                "CEL bindings must use a statically named binding.",
                owner,
                path,
                key="expression",
            )
        missing = sorted(inspection.bindings - set(available))
        if missing:
            self._fail(
                "unavailable-double-binding",
                "CEL expression reads a binding that is not yet available.",
                owner,
                path,
                key="expression",
                details={"bindings": missing},
            )
        if phase == "event" and inspection.uses_request:
            self._fail(
                "unavailable-double-request-context",
                "Event derivation has no matched request context.",
                owner,
                path,
                key="expression",
            )
        try:
            validate_expression(expression)
        except CelProfileError as error:
            self._fail(
                "invalid-double-cel",
                "CEL expression is outside the restricted BSL v0 profile.",
                owner,
                path,
                key="expression",
                details={"diagnostic": _bounded_diagnostic(error)},
            )

    def _compile_regex(
        self,
        pattern: str,
        owner: CommentedMap,
        path: tuple[PathPart, ...],
    ) -> None:
        try:
            validate_regex(pattern)
        except CelExpressionTooLarge:
            self._fail(
                "double-regex-too-large",
                "Regex pattern exceeds the BSL v0 byte bound.",
                owner,
                path,
                key="pattern",
                details={"max_bytes": MAX_CEL_EXPRESSION_BYTES},
            )
        except CelProfileError as error:
            self._fail(
                "invalid-double-regex",
                "Regex pattern is not valid in the CEL/RE2 profile.",
                owner,
                path,
                key="pattern",
                details={"diagnostic": _bounded_diagnostic(error)},
            )

    def _check_example(
        self,
        matcher: Matcher,
        value: JsonValue,
        owner: CommentedMap,
        path: tuple[PathPart, ...],
    ) -> None:
        valid = True
        if matcher.kind == "exact":
            valid = _json_equal(value, matcher.value)
        elif matcher.kind == "enum":
            valid = any(_json_equal(value, item) for item in matcher.values or ())
        elif matcher.kind == "range":
            valid = (
                not isinstance(value, bool)
                and isinstance(value, (int, float))
                and (matcher.minimum is None or value >= matcher.minimum)
                and (matcher.maximum is None or value <= matcher.maximum)
            )
        elif matcher.kind == "regex":
            valid = isinstance(value, str) and regex_matches(
                value, matcher.pattern or ""
            )
        elif matcher.kind == "semantic":
            valid = isinstance(value, str) and _semantic_valid(
                matcher.semantic or "", matcher.using or "", value
            )
        if not valid:
            self._fail(
                "invalid-double-example",
                "The authored example does not satisfy its matcher or validator.",
                owner,
                path,
                details={"matcher_kind": matcher.kind},
            )

    def _compile_provenance(
        self, value: object, path: tuple[PathPart, ...]
    ) -> Provenance:
        provenance = self._mapping(value, path, "Provenance must be a mapping.")
        self._keys(
            provenance, path, required={"kind", "source"}, optional={"sanitized"}
        )
        kind = self._string(provenance["kind"], (*path, "kind"))
        if kind not in _PROVENANCE_KINDS:
            self._fail(
                "invalid-double-provenance",
                "Provenance kind is not in the BSL v0 vocabulary.",
                provenance,
                (*path, "kind"),
                key="kind",
                details={"kind": kind},
            )
        source = self._nonempty_string(provenance["source"], (*path, "source"))
        sanitized: bool | None = None
        if kind == "provider-capture":
            if provenance.get("sanitized") is not True:
                self._fail(
                    "unsanitized-double-capture",
                    "provider-capture provenance requires sanitized: true.",
                    provenance,
                    (*path, "sanitized"),
                    key="sanitized" if "sanitized" in provenance else None,
                )
            sanitized = True
        elif "sanitized" in provenance:
            self._fail(
                "invalid-double-provenance",
                "sanitized is valid only for provider-capture provenance.",
                provenance,
                (*path, "sanitized"),
                key="sanitized",
            )
        snapshot_sha256 = None
        if _is_local_reference(source):
            local_source = source.split("#", 1)[0]
            snapshot = self.sources.snapshot_local(local_source, (*path, "source"))
            snapshot_sha256 = snapshot.sha256
        return Provenance(
            kind=cast(Any, kind),
            source=source,
            sanitized=sanitized,
            snapshot_sha256=snapshot_sha256,
        )

    def _compile_materializer(
        self, value: object, path: tuple[PathPart, ...]
    ) -> Materializer:
        materializer = self._mapping(value, path, "Materializer must be a mapping.")
        self._keys(
            materializer,
            path,
            required={"argv", "cwd", "env", "timeout-ms", "max-output-bytes"},
        )
        argv_value = self._sequence(
            materializer["argv"], (*path, "argv"), "argv must be a non-empty sequence."
        )
        if not argv_value or len(argv_value) > MAX_MATERIALIZER_ARGUMENTS:
            self._fail(
                "invalid-double-materializer",
                "argv must be non-empty and within the argument-count bound.",
                materializer,
                (*path, "argv"),
                key="argv",
                details={"max_arguments": MAX_MATERIALIZER_ARGUMENTS},
            )
        argv = [
            self._nonempty_string(item, (*path, "argv", index))
            for index, item in enumerate(argv_value)
        ]
        cwd_text = self._nonempty_string(materializer["cwd"], (*path, "cwd"))
        cwd = self.sources.resolve(
            cwd_text, (*path, "cwd"), kind="directory", allow_absolute=True
        )
        executable = _resolve_executable(argv[0], cwd)
        if executable is None:
            self._fail(
                "double-materializer-executable-not-found",
                "Materializer argv[0] could not be resolved to an executable.",
                materializer,
                (*path, "argv", 0),
                details={"executable": argv[0]},
            )
        argv[0] = str(executable)
        env_value = self._mapping(
            materializer["env"], (*path, "env"), "env must be a string map."
        )
        env: dict[str, str] = {}
        for key, item in env_value.items():
            if not isinstance(key, str) or not key or "\0" in key or "=" in key:
                self._fail(
                    "invalid-double-materializer",
                    "Materializer environment names are invalid.",
                    env_value,
                    (*path, "env"),
                )
            env[key] = self._string(item, (*path, "env", key))
            if "\0" in env[key]:
                self._fail(
                    "invalid-double-materializer",
                    "Materializer environment values cannot contain NUL.",
                    env_value,
                    (*path, "env", key),
                    key=key,
                )
        timeout = materializer["timeout-ms"]
        if (
            isinstance(timeout, bool)
            or not isinstance(timeout, int)
            or not 1 <= timeout <= MAX_MATERIALIZER_TIMEOUT_MS
        ):
            self._fail(
                "invalid-double-materializer",
                "timeout-ms is outside the admitted bound.",
                materializer,
                (*path, "timeout-ms"),
                key="timeout-ms",
                details={"maximum": MAX_MATERIALIZER_TIMEOUT_MS},
            )
        output_bound = materializer["max-output-bytes"]
        if (
            isinstance(output_bound, bool)
            or not isinstance(output_bound, int)
            or not 1 <= output_bound <= MAX_MATERIALIZER_OUTPUT_BYTES
        ):
            self._fail(
                "invalid-double-materializer",
                "max-output-bytes is outside the admitted bound.",
                materializer,
                (*path, "max-output-bytes"),
                key="max-output-bytes",
                details={"maximum": MAX_MATERIALIZER_OUTPUT_BYTES},
            )
        return Materializer(
            argv=tuple(argv),
            cwd=str(cwd),
            env=env,
            timeout_ms=timeout,
            max_output_bytes=output_bound,
        )

    def _compile_contract(self, value: CommentedMap) -> Contract:
        path: tuple[PathPart, ...] = ("scenario", "boundary", "contract")
        self._keys(value, path, required={"kind", "source", "method", "path"})
        kind = self._string(value["kind"], (*path, "kind"))
        if kind != "openapi-3.1-operation":
            self._fail(
                "unsupported-double-contract",
                "Contract kind must be openapi-3.1-operation.",
                value,
                (*path, "kind"),
                key="kind",
                details={"kind": kind},
            )
        source_text = self._nonempty_string(value["source"], (*path, "source"))
        if not _is_local_reference(source_text) or "#" in source_text:
            self._fail(
                "invalid-double-contract-source",
                "OpenAPI contract source must be one local file path without a fragment.",
                value,
                (*path, "source"),
                key="source",
            )
        source = self.sources.snapshot_local(source_text, (*path, "source"))
        source_path = self.workspace / source.logical_path
        document = load_yaml(
            base64.b64decode(source.content_base64),
            source_path,
            self.module,
            is_module=False,
        )
        source_path = source_path.resolve()
        method = self._method(value["method"], value, (*path, "method"))
        operation_path = self._http_path(value["path"], value, (*path, "path"))
        if "{" in operation_path or "}" in operation_path:
            self._fail(
                "unsupported-double-contract-path",
                "OpenAPI operation path must be static; templates are not admitted.",
                value,
                (*path, "path"),
                key="path",
            )
        loaded_documents: dict[Path, object] = {source_path: document}

        def load_document(relative: str, base: Path) -> tuple[Path, object]:
            target = self.sources.resolve_from(
                relative,
                base,
                ("$ref",),
                kind="file",
                error_code="invalid-double-contract-ref",
            )
            if target not in loaded_documents:
                snapshot = self.sources.snapshot_path(target)
                loaded_documents[target] = load_yaml(
                    base64.b64decode(snapshot.content_base64),
                    target,
                    self.module,
                    is_module=False,
                )
            return target, loaded_documents[target]

        try:
            return compile_openapi_profile(
                source=source,
                source_name=source_text,
                source_path=source_path,
                document=document,
                method=method,
                operation_path=operation_path,
                load_document=load_document,
                snapshot_for_path=self.sources.snapshot_path,
            )
        except OpenApiProfileError as error:
            payload: dict[str, Any] = {
                "module": str(self.module),
                "source": error.source,
                **error.details,
            }
            if error.code == "invalid-double-json-value":
                payload.update({"path": ["contract", "schema"], "line": 1, "column": 1})
            raise SvcError(error.code, error.message, payload) from error

    def _check_contract_coverage(
        self, contract: Contract, interactions: tuple[Interaction, ...]
    ) -> None:
        for interaction in interactions:
            if (
                interaction.request.method != contract.method
                or interaction.request.path != contract.path
            ):
                raise SvcError(
                    "double-contract-operation-mismatch",
                    "Every interaction must use the selected contract operation.",
                    {
                        "module": str(self.module),
                        "interaction": interaction.name,
                        "expected_method": contract.method,
                        "expected_path": contract.path,
                        "actual_method": interaction.request.method,
                        "actual_path": interaction.request.path,
                    },
                )
            if (
                interaction.request.body is not None
                and interaction.request.body.kind == "structured"
                and contract.request_schema is None
            ):
                raise SvcError(
                    "double-contract-schema-missing",
                    "Selected operation has no application/json request schema.",
                    {
                        "module": str(self.module),
                        "interaction": interaction.name,
                        "phase": "request",
                    },
                )
            response_key = str(interaction.response.status)
            if (
                interaction.response.body is not None
                and interaction.response.body.kind == "structured"
                and response_key not in contract.response_schemas
                and "default" not in contract.response_schemas
            ):
                raise SvcError(
                    "double-contract-schema-missing",
                    "Selected operation has no application/json schema for the response status.",
                    {
                        "module": str(self.module),
                        "interaction": interaction.name,
                        "phase": "response",
                        "status": interaction.response.status,
                    },
                )

    def _load_managed_json(
        self, snapshot: Snapshot, path: tuple[PathPart, ...]
    ) -> JsonValue:
        raw = base64.b64decode(snapshot.content_base64)
        try:
            value = json.loads(
                raw.decode("utf-8"),
                object_pairs_hook=_reject_json_duplicates,
                parse_constant=_reject_json_constant,
            )
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
            raise SvcError(
                "invalid-double-managed-json",
                "Managed structured value must be strict UTF-8 JSON.",
                {
                    "module": str(self.module),
                    "path": list(path),
                    "source": snapshot.logical_path,
                    "diagnostic": _bounded_diagnostic(error),
                },
            ) from error
        return _json_value(value, self, path)

    def _keys(
        self,
        value: Mapping[object, object],
        path: tuple[PathPart, ...],
        *,
        required: set[str] | None = None,
        optional: set[str] | None = None,
    ) -> None:
        required = required or set()
        optional = optional or set()
        actual = set(value)
        non_string = [key for key in actual if not isinstance(key, str)]
        if non_string:
            self._fail(
                "invalid-double-key",
                "Mapping keys must be strings.",
                value,
                path,
                details={"keys": [str(key) for key in non_string]},
            )
        unknown = sorted(cast(set[str], actual) - required - optional)
        if unknown:
            key = unknown[0]
            self._fail(
                "unknown-double-key",
                "The BSL object contains an unknown key.",
                value,
                (*path, key),
                key=key,
                details={"key": key},
            )
        missing = sorted(required - cast(set[str], actual))
        if missing:
            self._fail(
                "missing-double-key",
                "The BSL object is missing a required key.",
                value,
                path,
                details={"keys": missing},
            )

    def _mapping(
        self, value: object, path: tuple[PathPart, ...], message: str
    ) -> CommentedMap:
        if not isinstance(value, CommentedMap):
            self._fail("invalid-double-type", message, value, path)
        return cast(CommentedMap, value)

    def _sequence(
        self, value: object, path: tuple[PathPart, ...], message: str
    ) -> CommentedSeq:
        if not isinstance(value, CommentedSeq):
            self._fail("invalid-double-type", message, value, path)
        return cast(CommentedSeq, value)

    def _string(self, value: object, path: tuple[PathPart, ...]) -> str:
        if not isinstance(value, str):
            self._fail(
                "invalid-double-type",
                "Value must be a string.",
                value,
                path,
                details={"expected": "string", "actual": type(value).__name__},
            )
        return value

    def _nonempty_string(self, value: object, path: tuple[PathPart, ...]) -> str:
        result = self._string(value, path)
        if not result.strip() or "\0" in result:
            self._fail(
                "invalid-double-string",
                "Value must be a non-empty string without NUL.",
                value,
                path,
            )
        return result

    def _name(self, value: object, path: tuple[PathPart, ...], role: str) -> str:
        result = self._string(value, path)
        if not _NAME_RE.fullmatch(result):
            self._fail(
                "invalid-double-name",
                f"{role.capitalize()} name must match [a-z][a-z0-9.-]*.",
                value,
                path,
                details={"name": result, "role": role},
            )
        return result

    def _binding_name(self, value: object, path: tuple[PathPart, ...]) -> str:
        result = self._string(value, path)
        if not _BINDING_RE.fullmatch(result):
            self._fail(
                "invalid-double-binding",
                "Binding name must match [a-z][a-z0-9_]*.",
                value,
                path,
                details={"binding": result},
            )
        return result

    def _declare_binding(
        self,
        name: str,
        declared: MutableSet[str],
        available: MutableSet[str],
        owner: object,
        path: tuple[PathPart, ...],
    ) -> None:
        if name in declared:
            self._fail(
                "duplicate-double-binding",
                "Each immutable binding must have one declaration.",
                owner,
                path,
                details={"binding": name},
            )
        declared.add(name)
        available.add(name)

    def _method(
        self, value: object, owner: Mapping[object, object], path: tuple[PathPart, ...]
    ) -> str:
        result = self._string(value, path)
        if not _METHOD_RE.fullmatch(result):
            self._fail(
                "invalid-double-http-method",
                "HTTP method must be an uppercase method token.",
                owner,
                path,
                key="method",
                details={"method": result},
            )
        return result

    def _http_path(
        self, value: object, owner: Mapping[object, object], path: tuple[PathPart, ...]
    ) -> str:
        result = self._string(value, path)
        if (
            not result.startswith("/")
            or "?" in result
            or "#" in result
            or "\0" in result
        ):
            self._fail(
                "invalid-double-http-path",
                "HTTP path must be an exact absolute path without query or fragment.",
                owner,
                path,
                key="path",
                details={"path_value": result},
            )
        return result

    def _unique_name(
        self,
        name: str,
        names: set[str],
        owner: Mapping[object, object],
        path: tuple[PathPart, ...],
        role: str,
    ) -> None:
        if name in names:
            self._fail(
                "duplicate-double-name",
                f"Each {role} name must be unique.",
                owner,
                path,
                key="name",
                details={"name": name, "role": role},
            )
        names.add(name)

    def _location(
        self,
        owner: object,
        path: tuple[PathPart, ...],
        *,
        key: str | None = None,
    ) -> SourceLocation:
        line, column = source_location(owner, key)
        return SourceLocation(line=line, column=column, path=path)

    def _fail(
        self,
        code: str,
        message: str,
        owner: object,
        path: tuple[PathPart, ...],
        *,
        key: str | None = None,
        details: Mapping[str, Any] | None = None,
    ) -> NoReturn:
        line, column = source_location(owner, key)
        payload: dict[str, Any] = {
            "module": str(self.module),
            "path": list(path),
            "line": line,
            "column": column,
        }
        if details:
            payload.update(details)
        raise SvcError(code, message, payload)

    def _contract_fail(
        self, message: str, source: str, *, details: Mapping[str, Any] | None = None
    ) -> NoReturn:
        payload: dict[str, Any] = {"module": str(self.module), "source": source}
        if details:
            payload.update(details)
        raise SvcError("invalid-double-contract", message, payload)


def compile_scenario(module: Path) -> Scenario:
    """Compile one strict BSL v0 module without executing Consumer code."""

    return _Compiler(module).compile()


def _json_value(
    value: object, compiler: _Compiler, path: tuple[PathPart, ...]
) -> JsonValue:
    if value is None or isinstance(value, (str, bool)):
        return value
    if isinstance(value, int):
        return int(value)
    if isinstance(value, float):
        if not math.isfinite(value):
            compiler._fail(
                "invalid-double-json-value",
                "JSON values cannot contain non-finite numbers.",
                value,
                path,
            )
        return float(value)
    if isinstance(value, Mapping):
        result: dict[str, JsonValue] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                compiler._fail(
                    "invalid-double-json-value",
                    "JSON object keys must be strings.",
                    value,
                    path,
                )
            result[key] = _json_value(item, compiler, (*path, key))
        return result
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [
            _json_value(item, compiler, (*path, index))
            for index, item in enumerate(value)
        ]
    compiler._fail(
        "invalid-double-json-value",
        "Value is not JSON-compatible under the BSL YAML 1.2 profile.",
        value,
        path,
        details={"actual": type(value).__name__},
    )


def _number_or_none(
    value: object | None,
    compiler: _Compiler,
    path: tuple[PathPart, ...],
    *,
    integer: bool = False,
) -> int | float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(
        value, int if integer else (int, float)
    ):
        compiler._fail(
            "invalid-double-matcher",
            "Numeric bounds must be finite numbers."
            if not integer
            else "Numeric bounds must be integers.",
            value,
            path,
        )
    if isinstance(value, float) and not math.isfinite(value):
        compiler._fail(
            "invalid-double-matcher", "Numeric bounds must be finite.", value, path
        )
    return value


def _json_type(value: JsonValue | None) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    return "object"


def _json_equal(left: JsonValue, right: JsonValue | None) -> bool:
    if isinstance(left, bool) or isinstance(right, bool):
        return type(left) is type(right) and left == right
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return left == right
    if type(left) is not type(right):
        return False
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(
            _json_equal(a, b) for a, b in zip(left, right, strict=True)
        )
    if isinstance(left, dict) and isinstance(right, dict):
        return set(left) == set(right) and all(
            _json_equal(left[key], right[key]) for key in left
        )
    return left == right


def _is_typed_value(value: object) -> bool:
    return isinstance(value, Mapping) and set(value) == {"$bsl"}


def _query_shape(value: object) -> bool:
    if _is_typed_value(value):
        return True
    if isinstance(value, str):
        return True
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return all(_is_typed_value(item) or isinstance(item, str) for item in value)
    return False


def _string_surface_plan(template: JsonValue, nodes: tuple[ValueNode, ...]) -> bool:
    by_path = {node.path: node for node in nodes}

    def visit(value: JsonValue, path: tuple[PathPart, ...]) -> bool:
        node = by_path.get(path)
        if node is not None:
            if node.kind in {"literal", "example", "managed"}:
                return isinstance(node.value, str)
            if node.kind in {"match", "capture"}:
                return node.matcher is not None and _matcher_is_string_typed(
                    node.matcher
                )
            if node.kind == "derived":
                return node.validator is not None and _matcher_is_string_typed(
                    node.validator
                )
            if node.kind == "generated":
                if node.using == "svc.enum-choice/v1":
                    values = (node.options or {}).get("values")
                    return isinstance(values, list) and all(
                        isinstance(item, str) for item in values
                    )
                return node.using in {
                    "svc.uuid-v4/v1",
                    "svc.opaque-token/v1",
                    "svc.fixed-clock-rfc3339/v1",
                }
            return False
        if isinstance(value, dict):
            return all(visit(item, (*path, key)) for key, item in value.items())
        if isinstance(value, list):
            return all(visit(item, (*path, index)) for index, item in enumerate(value))
        return isinstance(value, str)

    return visit(template, ())


def _matcher_is_string_typed(matcher: Matcher) -> bool:
    if matcher.kind in {"regex", "semantic"}:
        return True
    if matcher.kind == "exact":
        return isinstance(matcher.value, str)
    if matcher.kind == "enum":
        values = matcher.values
        return (
            values is not None
            and bool(values)
            and all(isinstance(item, str) for item in values)
        )
    return False


def _is_local_reference(source: str) -> bool:
    parsed = urlsplit(source)
    return not parsed.scheme and not parsed.netloc and bool(source.split("#", 1)[0])


def _resolve_executable(argv0: str, cwd: Path) -> Path | None:
    candidate = Path(argv0)
    try:
        if candidate.is_absolute():
            resolved = candidate.resolve()
        elif "/" in argv0 or "\\" in argv0:
            resolved = (cwd / candidate).resolve()
        else:
            found = shutil.which(argv0)
            if found is None:
                return None
            resolved = Path(found).resolve()
    except (OSError, RuntimeError):
        return None
    if not resolved.is_file() or not os.access(resolved, os.X_OK):
        return None
    return resolved


def _semantic_valid(semantic: str, using: str, value: str) -> bool:
    if (semantic, using) == ("rfc.uuid", "svc.rfc-uuid/v1"):
        try:
            parsed = uuid.UUID(value)
        except ValueError:
            return False
        return str(parsed) == value.lower()
    if (semantic, using) == ("rfc3339", "svc.rfc3339/v1"):
        if not re.fullmatch(
            r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})",
            value,
        ):
            return False
        try:
            parsed_datetime = datetime.fromisoformat(
                value.removesuffix("Z") + "+00:00" if value.endswith("Z") else value
            )
        except ValueError:
            return False
        return parsed_datetime.tzinfo is not None
    return False


def _scenario_digest(scenario: Scenario) -> str:
    payload = scenario.model_dump(mode="json")
    payload.pop("scenario_digest", None)
    payload.pop("module_path", None)
    payload.pop("workspace_root", None)
    _remove_diagnostic_locations(payload)
    _normalize_materializer_cwds(payload, Path(scenario.workspace_root))
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _remove_diagnostic_locations(value: object) -> None:
    if isinstance(value, dict):
        value.pop("location", None)
        for item in value.values():
            _remove_diagnostic_locations(item)
    elif isinstance(value, list):
        for item in value:
            _remove_diagnostic_locations(item)


def _normalize_materializer_cwds(value: object, workspace: Path) -> None:
    if isinstance(value, dict):
        if {"argv", "cwd", "env", "timeout_ms", "max_output_bytes"} <= set(value):
            cwd = value.get("cwd")
            if isinstance(cwd, str):
                try:
                    value["cwd"] = Path(cwd).relative_to(workspace).as_posix() or "."
                except ValueError:
                    value["cwd"] = cwd
        for item in value.values():
            _normalize_materializer_cwds(item, workspace)
    elif isinstance(value, list):
        for item in value:
            _normalize_materializer_cwds(item, workspace)


def _reject_json_duplicates(pairs: Iterable[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON number: {value}")


def _bounded_diagnostic(error: BaseException, maximum: int = 1_000) -> str:
    text = str(error).strip().replace(str(Path.home()), "<home>")
    return text[:maximum]
