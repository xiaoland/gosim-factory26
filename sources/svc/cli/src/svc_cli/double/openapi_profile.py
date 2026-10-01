"""Admitted OpenAPI 3.1 selected-operation profile for double contracts."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any, NoReturn, cast
from urllib.parse import unquote, urlsplit

from jsonschema.exceptions import SchemaError  # type: ignore[import-untyped]
from pydantic import JsonValue
from referencing.exceptions import Unresolvable

from .model import Contract, SchemaResource, Snapshot, strict_json_value
from .schema_registry import (
    build_schema_registry,
    check_schema_graph,
    resolve_document_reference,
)


_OPENAPI_VERSION_RE = re.compile(r"^3\.1\.\d+$")
_ADMITTED_SCHEMA_DIALECTS = frozenset(
    {
        "https://json-schema.org/draft/2020-12/schema",
        "https://spec.openapis.org/oas/3.1/dialect/base",
    }
)

DocumentLoader = Callable[[str, Path], tuple[Path, object]]
SnapshotForPath = Callable[[Path], Snapshot]


class OpenApiProfileError(ValueError):
    """A stable profile failure for compiler-owned diagnostic projection."""

    def __init__(
        self,
        message: str,
        source: str,
        *,
        code: str = "invalid-double-contract",
        details: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.source = source
        self.details = dict(details or {})


def compile_openapi_profile(
    *,
    source: Snapshot,
    source_name: str,
    source_path: Path,
    document: object,
    method: str,
    operation_path: str,
    load_document: DocumentLoader,
    snapshot_for_path: SnapshotForPath,
) -> Contract:
    """Compile one static selected operation from contained immutable artifacts."""

    profile = _Profile(
        source=source,
        source_name=source_name,
        source_path=source_path.resolve(),
        document=document,
        method=method,
        operation_path=operation_path,
        load_document=load_document,
        snapshot_for_path=snapshot_for_path,
    )
    return profile.compile()


class _Profile:
    def __init__(
        self,
        *,
        source: Snapshot,
        source_name: str,
        source_path: Path,
        document: object,
        method: str,
        operation_path: str,
        load_document: DocumentLoader,
        snapshot_for_path: SnapshotForPath,
    ) -> None:
        self.source = source
        self.source_name = source_name
        self.source_path = source_path
        self.document = document
        self.method = method
        self.operation_path = operation_path
        self.load_document = load_document
        self.snapshot_for_path = snapshot_for_path
        self.documents: dict[Path, object] = {source_path: document}

    def compile(self) -> Contract:
        openapi = self.document
        if not isinstance(openapi, Mapping):
            self._fail("OpenAPI source must be a mapping.", self.source_name)
        version = openapi.get("openapi")
        if not isinstance(version, str) or not _OPENAPI_VERSION_RE.fullmatch(version):
            self._fail(
                "OpenAPI source must declare a 3.1.x version.",
                self.source_name,
                details={"openapi": version},
            )
        dialect = openapi.get("jsonSchemaDialect")
        if dialect is not None and dialect not in _ADMITTED_SCHEMA_DIALECTS:
            self._fail(
                "Custom OpenAPI JSON Schema dialects are not admitted in v0.",
                self.source_name,
                details={"jsonSchemaDialect": dialect},
            )
        paths = openapi.get("paths")
        if not isinstance(paths, Mapping) or self.operation_path not in paths:
            self._fail(
                "The selected OpenAPI path does not exist.",
                self.source_name,
                details={"path": self.operation_path},
            )
        path_item = self._resolve_openapi_object(
            paths[self.operation_path], self.source_path, self.document
        )
        if not isinstance(path_item, Mapping) or self.method.lower() not in path_item:
            self._fail(
                "The selected OpenAPI method does not exist at the static path.",
                self.source_name,
                details={"method": self.method, "path": self.operation_path},
            )
        operation = self._resolve_openapi_object(
            path_item[self.method.lower()], self.source_path, self.document
        )
        if not isinstance(operation, Mapping):
            self._fail(
                "The selected OpenAPI operation is not an object.",
                self.source_name,
            )

        self._walk_local_refs(operation, self.source_path, self.document, set())
        resource_uris = self._schema_resource_uris()
        request_schema = self._extract_request_schema(
            operation, self.source_path, self.document, resource_uris
        )
        response_schemas = self._extract_response_schemas(
            operation, self.source_path, self.document, resource_uris
        )
        schema_resources = self._compile_schema_resources(resource_uris)
        registry = build_schema_registry(schema_resources)
        for schema_name, schema in [
            ("request", request_schema),
            *(
                (f"response:{status}", item)
                for status, item in response_schemas.items()
            ),
        ]:
            if schema is None:
                continue
            try:
                checked_schemas = check_schema_graph(schema, registry)
                for checked_schema in checked_schemas:
                    self._reject_custom_schema_dialects(
                        checked_schema, self.source_name
                    )
            except (SchemaError, Unresolvable) as error:
                self._fail(
                    "Selected OpenAPI Schema Object is invalid for JSON Schema 2020-12.",
                    self.source_name,
                    details={
                        "schema": schema_name,
                        "diagnostic": _bounded_diagnostic(error),
                    },
                )
        return Contract(
            source=self.source,
            method=self.method,
            path=self.operation_path,
            request_schema=request_schema,
            response_schemas={
                key: cast(JsonValue, item) for key, item in response_schemas.items()
            },
            schema_resources=schema_resources,
        )

    def _walk_local_refs(
        self,
        value: object,
        document_path: Path,
        document: object,
        visiting: set[tuple[Path, str]],
    ) -> None:
        if isinstance(value, Mapping):
            reference = value.get("$ref")
            if reference is not None:
                if not isinstance(reference, str) or not reference:
                    self._fail(
                        "OpenAPI $ref must be a non-empty string.", str(document_path)
                    )
                target_path, fragment, target_document = self._resolve_ref(
                    reference, document_path, document
                )
                identity = (target_path, fragment)
                if identity not in visiting:
                    visiting.add(identity)
                    try:
                        target = resolve_document_reference(
                            self.documents, document_path, reference
                        )
                    except Unresolvable:
                        self._fail(
                            "OpenAPI $ref fragment does not resolve.",
                            str(document_path),
                            details={"ref": reference},
                        )
                    self._walk_local_refs(
                        target, target_path, target_document, visiting
                    )
                    visiting.remove(identity)
            for key, item in value.items():
                if key != "$ref":
                    self._walk_local_refs(item, document_path, document, visiting)
        elif isinstance(value, Sequence) and not isinstance(
            value, (str, bytes, bytearray)
        ):
            for item in value:
                self._walk_local_refs(item, document_path, document, visiting)

    def _resolve_ref(
        self,
        reference: str,
        document_path: Path,
        document: object,
    ) -> tuple[Path, str, object]:
        parsed = urlsplit(reference)
        if parsed.scheme or parsed.netloc or parsed.query:
            self._fail(
                "Only local OpenAPI references are admitted.",
                str(document_path),
                details={"ref": reference},
            )
        fragment = unquote(parsed.fragment)
        if fragment and not fragment.startswith("/"):
            self._fail(
                "OpenAPI references must use JSON Pointer fragments.",
                str(document_path),
                details={"ref": reference},
            )
        if not parsed.path:
            return document_path, fragment, document
        relative = unquote(parsed.path)
        target_path, target_document = self.load_document(
            relative, document_path.parent
        )
        self.documents.setdefault(target_path, target_document)
        return target_path, fragment, self.documents[target_path]

    def _extract_request_schema(
        self,
        operation: Mapping[object, object],
        document_path: Path,
        document: object,
        resource_uris: Mapping[Path, str],
    ) -> dict[str, JsonValue] | None:
        request_body = operation.get("requestBody")
        if request_body is None:
            return None
        resolved = self._resolve_openapi_object(request_body, document_path, document)
        content = resolved.get("content") if isinstance(resolved, Mapping) else None
        media = (
            content.get("application/json") if isinstance(content, Mapping) else None
        )
        schema = media.get("schema") if isinstance(media, Mapping) else None
        if schema is None:
            return None
        normalized = self._rewrite_schema_refs(
            schema, document_path, document, resource_uris, strict=True
        )
        if not isinstance(normalized, dict):
            self._fail("OpenAPI request schema must be an object.", str(document_path))
        return cast(dict[str, JsonValue], normalized)

    def _extract_response_schemas(
        self,
        operation: Mapping[object, object],
        document_path: Path,
        document: object,
        resource_uris: Mapping[Path, str],
    ) -> dict[str, dict[str, JsonValue]]:
        responses_value = operation.get("responses")
        if not isinstance(responses_value, Mapping) or not responses_value:
            self._fail(
                "Selected OpenAPI operation requires responses.", str(document_path)
            )
        result: dict[str, dict[str, JsonValue]] = {}
        for status, authored in responses_value.items():
            status_text = str(status)
            if status_text != "default" and not re.fullmatch(
                r"[1-5][0-9]{2}", status_text
            ):
                self._fail(
                    "OpenAPI response keys must be exact status codes or default in v0.",
                    str(document_path),
                    details={"status": status_text},
                )
            resolved = self._resolve_openapi_object(authored, document_path, document)
            content = resolved.get("content") if isinstance(resolved, Mapping) else None
            media = (
                content.get("application/json")
                if isinstance(content, Mapping)
                else None
            )
            schema = media.get("schema") if isinstance(media, Mapping) else None
            if schema is None:
                continue
            normalized = self._rewrite_schema_refs(
                schema, document_path, document, resource_uris, strict=True
            )
            if not isinstance(normalized, dict):
                self._fail(
                    "OpenAPI response schema must be an object.", str(document_path)
                )
            result[status_text] = cast(dict[str, JsonValue], normalized)
        return result

    def _rewrite_schema_refs(
        self,
        value: object,
        document_path: Path,
        document: object,
        resource_uris: Mapping[Path, str],
        *,
        strict: bool,
    ) -> JsonValue:
        if isinstance(value, Mapping):
            result: dict[str, JsonValue] = {}
            for key, item in value.items():
                if not isinstance(key, str):
                    self._fail(
                        "JSON Schema object keys must be strings.", str(document_path)
                    )
                if key == "$ref":
                    if not isinstance(item, str):
                        self._fail("OpenAPI $ref must be a string.", str(document_path))
                    result[key] = self._registry_reference(
                        item,
                        document_path,
                        document,
                        resource_uris,
                        strict=strict,
                    )
                else:
                    result[key] = self._rewrite_schema_refs(
                        item,
                        document_path,
                        document,
                        resource_uris,
                        strict=strict,
                    )
            return result
        if isinstance(value, Sequence) and not isinstance(
            value, (str, bytes, bytearray)
        ):
            return [
                self._rewrite_schema_refs(
                    item,
                    document_path,
                    document,
                    resource_uris,
                    strict=strict,
                )
                for item in value
            ]
        try:
            return strict_json_value(value)
        except TypeError:
            self._fail(
                "Value is not JSON-compatible under the BSL YAML 1.2 profile.",
                str(document_path),
                code="invalid-double-json-value",
                details={"actual": type(value).__name__},
            )

    def _schema_resource_uris(self) -> dict[Path, str]:
        result: dict[Path, str] = {}
        for path in sorted(self.documents, key=lambda item: item.as_posix()):
            snapshot = self.snapshot_for_path(path)
            identity = hashlib.sha256(
                f"{snapshot.logical_path}\0{snapshot.sha256}".encode("utf-8")
            ).hexdigest()
            result[path] = f"urn:svc:double:schema-resource:{identity}"
        return result

    def _compile_schema_resources(
        self, resource_uris: Mapping[Path, str]
    ) -> tuple[SchemaResource, ...]:
        resources: list[SchemaResource] = []
        for path in sorted(self.documents, key=lambda item: resource_uris[item]):
            snapshot = self.snapshot_for_path(path)
            document = self.documents[path]
            normalized = self._rewrite_schema_refs(
                document, path, document, resource_uris, strict=False
            )
            resources.append(
                SchemaResource(
                    uri=resource_uris[path],
                    document=normalized,
                    snapshot_sha256=snapshot.sha256,
                )
            )
        return tuple(resources)

    def _registry_reference(
        self,
        reference: str,
        document_path: Path,
        document: object,
        resource_uris: Mapping[Path, str],
        *,
        strict: bool,
    ) -> str:
        parsed = urlsplit(reference)
        if parsed.scheme or parsed.netloc or parsed.query:
            if not strict:
                return reference
            self._fail(
                "Only local OpenAPI references are admitted.",
                str(document_path),
                details={"ref": reference},
            )
        if strict:
            target_path, _, _ = self._resolve_ref(reference, document_path, document)
        elif not parsed.path:
            target_path = document_path
        else:
            try:
                target_path = (document_path.parent / unquote(parsed.path)).resolve(
                    strict=True
                )
            except (OSError, RuntimeError):
                return reference
            if target_path not in resource_uris:
                return reference
        uri = resource_uris.get(target_path)
        if uri is None:
            self._fail(
                "Local OpenAPI reference is absent from the immutable schema registry.",
                str(document_path),
                details={"ref": reference},
            )
        return uri + (f"#{parsed.fragment}" if parsed.fragment else "")

    def _resolve_openapi_object(
        self, value: object, document_path: Path, document: object
    ) -> object:
        if not isinstance(value, Mapping) or "$ref" not in value:
            return value
        reference = value["$ref"]
        if not isinstance(reference, str):
            self._fail("OpenAPI $ref must be a string.", str(document_path))
        self._resolve_ref(reference, document_path, document)
        try:
            return resolve_document_reference(self.documents, document_path, reference)
        except Unresolvable:
            self._fail(
                "OpenAPI $ref fragment does not resolve.",
                str(document_path),
                details={"ref": reference},
            )

    def _reject_custom_schema_dialects(self, value: object, source: str) -> None:
        if isinstance(value, Mapping):
            dialect = value.get("$schema")
            if dialect is not None and dialect not in _ADMITTED_SCHEMA_DIALECTS:
                self._fail(
                    "Custom JSON Schema dialects are not admitted in v0.",
                    source,
                    details={"$schema": dialect},
                )
            for item in value.values():
                self._reject_custom_schema_dialects(item, source)
        elif isinstance(value, Sequence) and not isinstance(
            value, (str, bytes, bytearray)
        ):
            for item in value:
                self._reject_custom_schema_dialects(item, source)

    def _fail(
        self,
        message: str,
        source: str,
        *,
        code: str = "invalid-double-contract",
        details: Mapping[str, Any] | None = None,
    ) -> NoReturn:
        raise OpenApiProfileError(message, source, code=code, details=details)


def _bounded_diagnostic(error: BaseException, maximum: int = 1_000) -> str:
    text = " ".join(str(error).split())
    if len(text) <= maximum:
        return text
    return text[: maximum - 3] + "..."
