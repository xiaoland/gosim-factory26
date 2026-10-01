"""Codex rollout to structural ``svc.trajectory/v1`` projection.

This provider adapter interprets Codex fields and streams rebuildable records.
It retains no content payloads, policy metadata, diagnostics, or projection
identity.  Source/frame byte limits remain provider-side safety boundaries.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import PurePosixPath
import re
from typing import Any, BinaryIO, Mapping

from ...errors import SvcError
from ..agent_threads import (
    MAX_NATIVE_FRAME_BYTES,
    MAX_SOURCE_BYTES,
    NormalizationResult,
    NormalizedRecordSink,
    NormalizationStatus,
    ResolvedThread,
)
from ..trajectory import TRAJECTORY_SCHEMA


DEFAULT_BOUNDS: dict[str, int] = {
    "source_bytes": MAX_SOURCE_BYTES,
    "native_line_bytes": MAX_NATIVE_FRAME_BYTES,
}

_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_TOKEN = re.compile(r"(?<![A-Za-z0-9_./-])tasks/[^\s\x00<>\"'`\[\]{}()\\]+")
_TRAILING = ".,;:!?。！？；：、"
_RELATION_KEYS = {
    "turn": ("turn_ref", "turn_id", "turnId", "turn"),
    "actor": ("actor_ref", "actor_id", "actorId", "actor"),
    "parent": (
        "parent_actor_ref",
        "parent_actor_id",
        "parentActorId",
        "parent_actor",
    ),
    "lane": ("lane_ref", "lane_id", "laneId", "lane"),
    "concurrency": (
        "concurrency_group",
        "concurrency_group_id",
        "concurrencyGroup",
    ),
}
_BASE_CAPABILITIES = {
    "reasoning": "absent",
    "tool_linkage": "absent",
    "context": "absent",
    "task_references": "available",
    "explicit_concurrency": "unavailable",
    "timestamps": "absent",
    "terminal_events": "unavailable",
}


def _empty_lossiness() -> dict[str, int]:
    return {
        "dropped_records": 0,
        "unavailable_records": 0,
        "synthesized_records": 0,
        "partial_frames": 0,
    }


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _json_loads(value: bytes | str) -> Any:
    if isinstance(value, bytes):
        value = value.decode("utf-8")
    return json.loads(value)


def _sha(domain: bytes, value: bytes) -> str:
    return hashlib.sha256(domain + value).hexdigest()


def native_ref(kind: str, provider_id: str, value: str) -> str:
    domain = provider_id.encode() + b"\0" + kind.encode() + b"\0native\0"
    return f"{kind}_{_sha(domain, value.encode())}"


def synthetic_ref(
    kind: str,
    provider_id: str,
    event_index: int,
    component_index: int,
) -> str:
    marker = b"synthetic" if kind == "call" else b"orphan-result"
    domain = (
        provider_id.encode()
        + b"\0call\0"
        + marker
        + b"\0"
        + str(event_index).encode()
        + b"\0"
        + str(component_index).encode()
    )
    return f"call_{_sha(domain, b'')}"


def _timestamp(value: Any) -> tuple[str | None, bool]:
    if value is None:
        return None, False
    try:
        if isinstance(value, bool):
            raise ValueError
        original_fraction: str | None = None
        if isinstance(value, (int, float)):
            if not math.isfinite(float(value)):
                raise ValueError
            number = float(value)
            if abs(number) > 1_000_000_000_000:
                number /= 1000
            parsed = datetime.fromtimestamp(number, timezone.utc)
        elif isinstance(value, str):
            text = value.strip()
            fraction_match = re.search(
                r"\.([0-9]+)(?:Z|[+-][0-9]{2}:[0-9]{2})$",
                text,
            )
            if fraction_match:
                original_fraction = fraction_match.group(1)
            if text.endswith("Z"):
                text = text[:-1] + "+00:00"
            parsed = datetime.fromisoformat(text)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            parsed = parsed.astimezone(timezone.utc)
        else:
            raise ValueError
        rendered = (
            parsed.replace(microsecond=0)
            .isoformat(timespec="seconds")
            .replace("+00:00", "Z")
        )
        if original_fraction is None:
            original_fraction = (
                f"{parsed.microsecond:06d}" if parsed.microsecond else ""
            )
        fraction = original_fraction[:9].rstrip("0")
        if fraction:
            rendered = rendered[:-1] + f".{fraction}Z"
        return rendered, True
    except (TypeError, ValueError, OverflowError, OSError):
        return None, False


def _find(payload: Mapping[str, Any], keys: tuple[str, ...]) -> Any | None:
    for key in keys:
        if key in payload:
            return payload[key]
    return None


def _payload_map(payload: Any) -> Mapping[str, Any]:
    return payload if isinstance(payload, Mapping) else {}


def _relation(
    payload: Mapping[str, Any],
    kind: str,
    provider_id: str,
) -> str | None:
    passthrough = payload.get("internal_chat_message_metadata_passthrough")
    passthrough_map = passthrough if isinstance(passthrough, Mapping) else {}
    nested_keys = {
        "turn": ("turn_id", "turnId", "turn_ref"),
        "actor": ("author", "actor", "actor_id", "actorId"),
        "lane": ("recipient", "lane", "lane_id", "laneId"),
        "parent": (
            "parent_actor",
            "parent_actor_id",
            "parentActorId",
        ),
        "concurrency": (
            "concurrency_group",
            "concurrency_group_id",
            "concurrencyGroup",
        ),
    }
    value = _find(passthrough_map, nested_keys[kind])
    if value is None:
        value = _find(payload, _RELATION_KEYS[kind])
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        if kind not in {"actor", "lane"}:
            return None
        text = _canonical(value).decode("utf-8")
    else:
        text = str(value)
    if not text:
        return None
    ref_kind = "actor" if kind == "parent" else kind
    if text.startswith(f"{ref_kind}_") and _HEX64.fullmatch(text[len(ref_kind) + 1 :]):
        return text
    return native_ref(ref_kind, provider_id, text)


def _relations(payload: Mapping[str, Any], provider_id: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for key in ("turn", "actor", "parent", "lane", "concurrency"):
        value = _relation(payload, key, provider_id)
        if value is None:
            continue
        target = {
            "parent": "parent_actor_ref",
            "concurrency": "concurrency_group",
        }.get(key, f"{key}_ref")
        result[target] = value
    return result


def _known_ui_record(marker: str, payload: Mapping[str, Any]) -> bool:
    """Recognize provider/UI bookkeeping that is not a trajectory record."""

    raw = str(
        payload.get("type") or payload.get("event") or payload.get("kind") or ""
    ).lower()
    text = f"{marker}:{raw}"
    if any(
        token in text
        for token in ("token_count", "rate_limit", "rate-limit", "world_state")
    ):
        return True
    if raw in {
        "task_started",
        "task_start",
        "task_complete",
        "task_completed",
        "turn_aborted",
        "context_compacted",
    }:
        return False
    return (
        marker.startswith("event_msg:")
        and any(
            token in text
            for token in ("user_message", "agent_message", "agent_reasoning")
        )
    ) or any(
        token in text
        for token in (
            "thread_ui",
            "thread_activity",
            "thread_event",
            "thread_started",
            "thread_ended",
            "thread_name_updated",
            "thread_renamed",
            "thread_rolled_back",
            "inter-agent",
            "inter_agent",
            "sub-agent",
            "sub_agent",
            "subagent",
            "agent_activity",
            "bookkeeping",
        )
    )


def _completion_kind(marker: str, payload: Mapping[str, Any]) -> bool:
    raw = str(
        payload.get("type") or payload.get("event") or payload.get("kind") or ""
    ).lower()
    text = f"{marker}:{raw}"
    return any(
        token in text
        for token in (
            "exec_command_end",
            "exec_command_completed",
            "patch_apply_end",
            "patch_apply_completed",
            "mcp_tool_call_end",
            "mcp_tool_call_completed",
            "collab_call_end",
            "collab_tool_call_end",
            "collab_completion",
            "sub_agent_end",
            "sub_agent_completed",
            "web_search_end",
            "collab_agent_spawn_end",
            "collab_waiting_end",
            "collab_agent_interaction_end",
        )
    )


def _completion_status(payload: Mapping[str, Any]) -> str:
    success = payload.get("success")
    if isinstance(success, bool):
        return "success" if success else "error"
    exit_code = payload.get("exit_code")
    if isinstance(exit_code, int) and not isinstance(exit_code, bool):
        return "success" if exit_code == 0 else "error"
    raw_value = _find(payload, ("status", "outcome", "result"))
    if isinstance(raw_value, Mapping):
        keys = {str(key).lower() for key in raw_value}
        if keys & {"err", "error", "failed", "failure", "aborted", "cancelled"}:
            return "error"
        if keys & {"ok", "success", "completed", "complete", "done"}:
            return "success"
        return "unknown"
    raw = str(raw_value or "").lower()
    if raw in {"success", "completed", "complete", "done", "ok"}:
        return "success"
    if raw in {"error", "failed", "failure", "aborted", "cancelled"}:
        return "error"
    return "unknown"


def _source_ref(
    event_index: int,
    line: int,
    component: str,
    component_index: int = 0,
) -> dict[str, Any]:
    return {
        "event_index": event_index,
        "line": line,
        "component_index": component_index,
        "component": component,
    }


def _task_refs(text: str) -> list[str]:
    absolute = re.compile(
        r"(?<![\w])(?:/|[A-Za-z]:[\\/]|\\\\|//)"
        r"[^\s<>\"'`\[\]{}()]*tasks[\\/][^\s<>\"'`\[\]{}()]*packet\.md"
    )
    uri = re.compile(
        r"(?<![\w])[A-Za-z][A-Za-z0-9+.-]*://"
        r"[^\s<>\"'`\[\]{}()]*tasks/[^\s<>\"'`\[\]{}()]*packet\.md"
    )
    backslash = re.compile(r"(?<![\w])tasks\\[^\s<>\"'`\[\]{}()]*packet\.md")
    consumed = uri.sub(" ", text)
    consumed = absolute.sub(" ", consumed)
    consumed = backslash.sub(" ", consumed)
    found: list[str] = []
    seen: set[str] = set()
    for match in _TOKEN.finditer(consumed):
        candidate = match.group(0).rstrip(_TRAILING)
        path = PurePosixPath(candidate)
        if (
            path.is_absolute()
            or path.as_posix() != candidate
            or len(path.parts) < 3
            or path.parts[0] != "tasks"
            or path.parts[-1] != "packet.md"
            or any(part in {"", ".", ".."} for part in path.parts)
            or candidate in seen
        ):
            continue
        found.append(candidate)
        seen.add(candidate)
    return found


def _workspace(provider_id: str, payload: Mapping[str, Any]) -> dict[str, Any]:
    value = _find(
        payload,
        ("cwd", "workspace", "working_directory", "workingDirectory"),
    )
    if not isinstance(value, str) or not value:
        return {
            "status": "missing",
            "flavor": None,
            "label": None,
            "ref": None,
        }
    if value.startswith("\\\\") or value.startswith("//"):
        flavor = "unc"
    elif re.match(r"^[A-Za-z]:[\\/]", value):
        flavor = "windows"
    else:
        flavor = "posix"
    normalized = value.replace("\\", "/")
    label = normalized.rstrip("/").rsplit("/", 1)[-1] or normalized
    digest = _sha(
        provider_id.encode() + b"\0workspace\0" + flavor.encode() + b"\0",
        value.encode(),
    )
    return {
        "status": "present",
        "flavor": flavor,
        "label": label,
        "ref": f"workspace_{digest}",
    }


class CodexTrajectoryNormalizer:
    """Stream structural records from one descriptor-bound Codex rollout."""

    provider_id = "codex"
    adapter_id = "codex-rollout-v1"
    source_format = "rollout-v1"

    def normalize(
        self,
        stream: BinaryIO,
        resolved: ResolvedThread,
        sink: NormalizedRecordSink,
        bounds: Mapping[str, int] | None = None,
    ) -> NormalizationResult:
        effective = dict(DEFAULT_BOUNDS)
        if bounds:
            effective.update(
                {
                    key: int(value)
                    for key, value in bounds.items()
                    if key in DEFAULT_BOUNDS
                    and isinstance(value, int)
                    and not isinstance(value, bool)
                    and value > 0
                }
            )
        loss = _empty_lossiness()
        capabilities = dict(_BASE_CAPABILITIES)
        emitted = 0
        stopped = False
        call_occurrences: dict[str, int] = {}
        result_occurrences: dict[str, int] = {}
        completion_cache: dict[str, dict[str, Any]] = {}
        explicit_tool_call_count = 0
        synthesized_tool_call_count = 0
        unresolved_tool_result_count = 0
        context_kinds: set[str] = set()
        reasoning_kinds: set[str] = set()
        saw_tool = False
        saw_valid_timestamp = False
        saw_invalid_timestamp = False
        saw_terminal = False
        saw_concurrency = False
        workspace = _workspace(self.provider_id, {})
        remaining = effective["source_bytes"]

        def emit(record: dict[str, Any]) -> bool:
            nonlocal emitted, stopped
            if not sink(record):
                loss["partial_frames"] += 1
                stopped = True
                return False
            emitted += 1
            return True

        def read_frame() -> tuple[bytes, bool]:
            """Read one source frame and report a clipped/oversize frame."""

            nonlocal remaining
            if remaining <= 0:
                return b"", False
            request = min(effective["native_line_bytes"] + 1, remaining)
            raw = stream.readline(request)
            remaining -= len(raw)
            clipped = bool(
                raw
                and (
                    len(raw) > effective["native_line_bytes"]
                    or not raw.endswith((b"\n", b"\r"))
                )
            )
            tail = raw
            if clipped and len(raw) > effective["native_line_bytes"]:
                while remaining > 0 and not tail.endswith((b"\n", b"\r")):
                    chunk = stream.readline(min(64 * 1024, remaining))
                    remaining -= len(chunk)
                    if not chunk:
                        break
                    tail = chunk
            return raw, clipped

        pending: tuple[bytes, bool, int] | None = None
        try:
            first, first_partial = read_frame()
        except OSError as error:
            raise SvcError(
                "thread-source-unreadable",
                "Codex rollout source cannot be read.",
            ) from error
        if first:
            pending = (first, first_partial, 0)
            if not first_partial:
                try:
                    first_value = _json_loads(first.rstrip(b"\r\n"))
                    if (
                        isinstance(first_value, Mapping)
                        and first_value.get("type") == "session_meta"
                    ):
                        workspace = _workspace(
                            self.provider_id,
                            _payload_map(first_value.get("payload")),
                        )
                except (
                    UnicodeDecodeError,
                    json.JSONDecodeError,
                    ValueError,
                    TypeError,
                ):
                    pass

        thread_ref = native_ref("thread", self.provider_id, resolved.thread_id)
        if not emit(
            {
                "type": "meta",
                "record_id": "r000000",
                "record_index": 0,
                "timestamp": None,
                "source_ref": {"event_index": None, "component": "meta"},
                "relationships": {},
                "trajectory_schema": TRAJECTORY_SCHEMA,
                "provider_id": self.provider_id,
                "adapter_id": self.adapter_id,
                "source_format": self.source_format,
                "thread_ref": thread_ref,
                "workspace": workspace,
            }
        ):
            return self._result(capabilities, loss)

        def common(
            kind: str,
            timestamp: str | None,
            source: dict[str, Any],
            payload: Mapping[str, Any],
        ) -> dict[str, Any]:
            return {
                "type": kind,
                "record_id": f"r{emitted:06d}",
                "record_index": emitted,
                "timestamp": timestamp,
                "source_ref": source,
                "relationships": _relations(payload, self.provider_id),
            }

        def parse_component(
            value: Any,
            source: dict[str, Any],
        ) -> None:
            nonlocal workspace
            nonlocal explicit_tool_call_count, synthesized_tool_call_count
            nonlocal unresolved_tool_result_count
            nonlocal saw_tool, saw_valid_timestamp, saw_invalid_timestamp
            nonlocal saw_terminal, saw_concurrency
            if stopped:
                return
            if not isinstance(value, Mapping):
                loss["dropped_records"] += 1
                return
            native_type = str(value.get("type", ""))
            payload = _payload_map(value.get("payload"))
            top_passthrough = value.get("internal_chat_message_metadata_passthrough")
            if (
                isinstance(top_passthrough, Mapping)
                and "internal_chat_message_metadata_passthrough" not in payload
            ):
                payload = dict(payload)
                payload["internal_chat_message_metadata_passthrough"] = top_passthrough
            inner_type = str(payload.get("type", ""))
            marker = f"{native_type}:{inner_type}".lower()
            if native_type == "session_meta":
                candidate = _find(
                    payload,
                    ("id", "thread_id", "threadId", "session_id", "sessionId"),
                )
                if candidate is not None and str(candidate) != resolved.thread_id:
                    raise SvcError(
                        "thread-source-incompatible",
                        "Rollout source identity changed during normalization.",
                    )
                workspace = _workspace(self.provider_id, payload)
                return

            timestamp, valid_timestamp = _timestamp(value.get("timestamp"))
            relationships = _relations(payload, self.provider_id)
            if any(
                key in relationships
                for key in (
                    "lane_ref",
                    "parent_actor_ref",
                    "concurrency_group",
                )
            ):
                saw_concurrency = True

            if _completion_kind(marker, payload):
                raw_id = _find(
                    payload,
                    (
                        "tool_call_id",
                        "call_id",
                        "callId",
                        "id",
                        "command_id",
                        "commandId",
                    ),
                )
                if raw_id is not None and str(raw_id):
                    completion_cache[str(raw_id)] = {
                        "status": _completion_status(payload),
                        "relationships": relationships,
                    }
                return
            if _known_ui_record(marker, payload):
                return

            semantic_role = str(payload.get("role") or "").lower()
            is_message = "message" in marker or inner_type in {
                "agent_message",
                "user_message",
                "assistant_message",
            }
            if is_message and semantic_role not in {"developer", "system"}:
                role = semantic_role
                if role not in {"user", "assistant"}:
                    role = (
                        "assistant"
                        if "assistant" in marker or "agent" in marker
                        else "user"
                    )
                content_value = _find(payload, ("content", "text", "message"))
                content = (
                    content_value
                    if isinstance(content_value, str)
                    else _canonical(content_value).decode("utf-8")
                    if content_value is not None
                    else ""
                )
                record = common("message", timestamp, source, payload)
                record.update({"role": role, "task_refs": _task_refs(content)})
                emit(record)
                saw_valid_timestamp |= valid_timestamp
                saw_invalid_timestamp |= (
                    value.get("timestamp") is not None and not valid_timestamp
                )
                return

            if "reason" in marker:
                opaque = any(
                    key in payload
                    for key in (
                        "encrypted",
                        "encrypted_content",
                        "encrypted_reasoning",
                        "ciphertext",
                        "opaque",
                    )
                )
                raw = _find(payload, ("content", "summary", "text", "reasoning"))
                if raw is None:
                    loss["unavailable_records"] += 1
                    reasoning_kinds.add("opaque")
                    return
                reasoning_kind = "summary" if opaque or "summary" in payload else "full"
                if opaque:
                    loss["unavailable_records"] += 1
                reasoning_kinds.add(reasoning_kind)
                record = common("reasoning", timestamp, source, payload)
                record["reasoning_kind"] = reasoning_kind
                emit(record)
                saw_valid_timestamp |= valid_timestamp
                saw_invalid_timestamp |= (
                    value.get("timestamp") is not None and not valid_timestamp
                )
                return

            is_web_terminal = inner_type == "web_search_call" and str(
                payload.get("status") or ""
            ).lower() in {
                "completed",
                "complete",
                "failed",
                "error",
                "cancelled",
            }
            is_custom_call = (
                inner_type
                in {"custom_tool_call", "tool_search_call", "web_search_call"}
                and not any(token in marker for token in ("output", "result", "end"))
                and not is_web_terminal
            )
            is_tool_call = (
                any(
                    token in marker
                    for token in (
                        "function_call",
                        "functioncall",
                        "custom_tool_call",
                        "tool_call",
                    )
                )
                and not any(token in marker for token in ("output", "result"))
            ) or is_custom_call
            if is_tool_call:
                saw_tool = True
                raw_id = _find(
                    payload,
                    ("tool_call_id", "call_id", "callId", "id"),
                )
                if raw_id is None or not str(raw_id):
                    synthesized_tool_call_count += 1
                    loss["synthesized_records"] += 1
                    call_id = synthetic_ref(
                        "call", self.provider_id, source["event_index"], 0
                    )
                else:
                    explicit_tool_call_count += 1
                    base_id = native_ref("call", self.provider_id, str(raw_id))
                    occurrence = call_occurrences.get(base_id, 0) + 1
                    call_occurrences[base_id] = occurrence
                    call_id = (
                        base_id if occurrence == 1 else f"{base_id}_d{occurrence:06d}"
                    )
                    if occurrence > 1:
                        loss["synthesized_records"] += 1
                name_value = _find(payload, ("name", "tool_name", "toolName"))
                if name_value is None and isinstance(payload.get("function"), Mapping):
                    name_value = payload["function"].get("name")
                if name_value is None:
                    name_value = {
                        "custom_tool_call": "custom_tool",
                        "tool_search_call": "tool_search",
                        "web_search_call": "web_search",
                    }.get(inner_type, "unknown")
                arguments = _find(
                    payload,
                    ("arguments", "input", "parameters", "args"),
                )
                if arguments is None:
                    arguments_kind = "absent"
                elif isinstance(arguments, str):
                    try:
                        _json_loads(arguments)
                        arguments_kind = "json"
                    except (TypeError, ValueError, UnicodeDecodeError):
                        arguments_kind = "text"
                else:
                    arguments_kind = "json"
                record = common("tool_call", timestamp, source, payload)
                record.update(
                    {
                        "tool_call_id": call_id,
                        "name": str(name_value),
                        "arguments_kind": arguments_kind,
                    }
                )
                emit(record)
                saw_valid_timestamp |= valid_timestamp
                saw_invalid_timestamp |= (
                    value.get("timestamp") is not None and not valid_timestamp
                )
                return

            is_custom_output = inner_type in {
                "custom_tool_call_output",
                "tool_search_call_output",
                "tool_search_output",
            }
            is_web_output = inner_type == "web_search_call" and (
                str(payload.get("status") or "").lower()
                in {
                    "completed",
                    "complete",
                    "failed",
                    "error",
                    "cancelled",
                }
                or str(payload.get("action") or "").lower() in {"end", "completed"}
            )
            is_tool_result = (
                any(
                    token in marker
                    for token in (
                        "function_output",
                        "function_call_output",
                        "tool_result",
                        "tool_output",
                    )
                )
                or is_custom_output
                or is_web_output
            )
            if is_tool_result:
                saw_tool = True
                raw_id = _find(
                    payload,
                    ("tool_call_id", "call_id", "callId", "id"),
                )
                explicit_occurrence: int | None = None
                result_base_id: str | None
                if raw_id is None or not str(raw_id):
                    call_id = synthetic_ref(
                        "result", self.provider_id, source["event_index"], 0
                    )
                    result_base_id = None
                    loss["synthesized_records"] += 1
                else:
                    result_base_id = native_ref("call", self.provider_id, str(raw_id))
                    occurrence_value = _find(
                        payload,
                        ("call_occurrence", "callOccurrence", "occurrence"),
                    )
                    if (
                        isinstance(occurrence_value, int)
                        and not isinstance(occurrence_value, bool)
                        and occurrence_value >= 1
                    ):
                        explicit_occurrence = occurrence_value
                    call_id = (
                        result_base_id
                        if explicit_occurrence in (None, 1)
                        else f"{result_base_id}_d{explicit_occurrence:06d}"
                    )
                result_occurrence = result_occurrences.get(call_id, 0) + 1
                result_occurrences[call_id] = result_occurrence
                if result_occurrence > 1:
                    loss["dropped_records"] += 1
                    return
                cached = (
                    completion_cache.get(str(raw_id)) if raw_id is not None else None
                )
                status = str(_find(payload, ("status", "outcome")) or "").lower()
                if cached is not None and cached["status"] in {"success", "error"}:
                    status = str(cached["status"])
                if status in {"completed", "complete", "done", "ok"}:
                    status = "success"
                elif status in {"failed", "failure", "aborted", "cancelled"}:
                    status = "error"
                if status not in {"success", "error", "unknown"}:
                    status = (
                        "error"
                        if any(
                            key in payload
                            for key in ("error", "error_message", "exception")
                        )
                        else "unknown"
                    )
                realized = (
                    call_occurrences.get(result_base_id, 0) if result_base_id else 0
                )
                target = explicit_occurrence or 1
                link_status = "linked" if realized >= target else "unresolved"
                if link_status == "unresolved":
                    unresolved_tool_result_count += 1
                    loss["unavailable_records"] += 1
                record = common("tool_result", timestamp, source, payload)
                if cached is not None and isinstance(
                    cached.get("relationships"), Mapping
                ):
                    record["relationships"] = {
                        **record["relationships"],
                        **cached["relationships"],
                    }
                record.update(
                    {
                        "tool_call_id": call_id,
                        "status": status,
                        "link_status": link_status,
                    }
                )
                emit(record)
                saw_valid_timestamp |= valid_timestamp
                saw_invalid_timestamp |= (
                    value.get("timestamp") is not None and not valid_timestamp
                )
                return

            context_kind = str(
                _find(payload, ("context_kind", "context_type"))
                or inner_type
                or native_type
            ).lower()
            if semantic_role in {"developer", "system"}:
                context_kind = semantic_role
            elif context_kind in {
                "turn_context",
                "turn-context",
                "thread_settings_applied",
            }:
                context_kind = "turn"
            if (
                context_kind in {"system", "developer", "tool_config", "turn"}
                or native_type == "context"
            ):
                if context_kind not in {
                    "system",
                    "developer",
                    "tool_config",
                    "turn",
                }:
                    context_kind = "turn"
                context_kinds.add(context_kind)
                if isinstance(payload.get("context"), Mapping):
                    context_source = payload["context"]
                elif inner_type == "thread_settings_applied" and isinstance(
                    payload.get("thread_settings"), Mapping
                ):
                    context_source = payload["thread_settings"]
                else:
                    context_source = payload
                attributes: dict[str, Any] = {}
                aliases = {
                    "model": (("model", None),),
                    "reasoning_effort": (
                        ("reasoning_effort", None),
                        ("effort", None),
                    ),
                    "approval_mode": (
                        ("approval_mode", None),
                        ("approval_policy", None),
                    ),
                    "sandbox_mode": (
                        ("sandbox_mode", None),
                        ("sandbox_policy", "type"),
                        ("permission_profile", "type"),
                        ("active_permission_profile", "id"),
                    ),
                    "collaboration_mode": (("collaboration_mode", "mode"),),
                }
                for key, candidates in aliases.items():
                    for provider_key, nested_key in candidates:
                        candidate = context_source.get(provider_key)
                        if nested_key is not None and isinstance(candidate, Mapping):
                            candidate = candidate.get(nested_key)
                        if candidate is not None and not isinstance(
                            candidate, (Mapping, list)
                        ):
                            attributes[key] = str(candidate)
                            break
                names = context_source.get("tool_names")
                if isinstance(names, list):
                    attributes["tool_names"] = sorted({str(item) for item in names})
                record = common("context", timestamp, source, payload)
                record.update({"context_kind": context_kind, "attributes": attributes})
                emit(record)
                saw_valid_timestamp |= valid_timestamp
                saw_invalid_timestamp |= (
                    value.get("timestamp") is not None and not valid_timestamp
                )
                return

            event_kind = _event_kind(marker, payload)
            if event_kind is not None:
                saw_terminal |= event_kind in {
                    "turn_start",
                    "turn_complete",
                    "turn_abort",
                    "agent_start",
                    "agent_complete",
                    "error",
                }
                record = common("event", timestamp, source, payload)
                record.update(
                    {
                        "event_kind": event_kind,
                        "outcome": _event_outcome(event_kind, payload),
                    }
                )
                emit(record)
                saw_valid_timestamp |= valid_timestamp
                saw_invalid_timestamp |= (
                    value.get("timestamp") is not None and not valid_timestamp
                )
                return
            loss["dropped_records"] += 1

        event_index = 0
        source_bound_partial = False
        while not stopped:
            if pending is not None:
                raw, partial, event_index = pending
                pending = None
            else:
                try:
                    raw, partial = read_frame()
                except OSError:
                    loss["partial_frames"] += 1
                    break
                if not raw:
                    break
                event_index += 1
            if partial:
                loss["partial_frames"] += 1
                source_bound_partial |= remaining == 0
                continue
            source = _source_ref(event_index, event_index, "envelope")
            try:
                value = _json_loads(raw.rstrip(b"\r\n"))
                parse_component(value, source)
            except (UnicodeDecodeError, json.JSONDecodeError, ValueError, TypeError):
                loss["dropped_records"] += 1

        if remaining == 0 and not source_bound_partial:
            try:
                if stream.read(1):
                    loss["partial_frames"] += 1
            except OSError:
                loss["partial_frames"] += 1

        if reasoning_kinds:
            if "summary" in reasoning_kinds or "opaque" in reasoning_kinds:
                capabilities["reasoning"] = (
                    "summary" if "summary" in reasoning_kinds else "opaque"
                )
            else:
                capabilities["reasoning"] = "full"
        if saw_tool:
            if unresolved_tool_result_count or (
                explicit_tool_call_count and synthesized_tool_call_count
            ):
                capabilities["tool_linkage"] = "mixed"
            elif synthesized_tool_call_count:
                capabilities["tool_linkage"] = "synthesized"
            else:
                capabilities["tool_linkage"] = "explicit"
        if context_kinds:
            capabilities["context"] = (
                "full"
                if context_kinds == {"system", "developer", "tool_config", "turn"}
                else "partial"
            )
        if saw_valid_timestamp and saw_invalid_timestamp:
            capabilities["timestamps"] = "partial"
        elif saw_valid_timestamp:
            capabilities["timestamps"] = "full"
        elif saw_invalid_timestamp:
            capabilities["timestamps"] = "partial"
        if saw_terminal:
            capabilities["terminal_events"] = "available"
        if saw_concurrency:
            capabilities["explicit_concurrency"] = "available"
        return self._result(capabilities, loss)

    @staticmethod
    def _result(
        capabilities: Mapping[str, str],
        lossiness: Mapping[str, int],
    ) -> NormalizationResult:
        result_status = (
            NormalizationStatus.PARTIAL
            if lossiness["dropped_records"] or lossiness["partial_frames"]
            else NormalizationStatus.READY
        )
        return NormalizationResult(
            result_status=result_status,
            capabilities=capabilities,
            lossiness=lossiness,
        )


def _event_kind(marker: str, payload: Mapping[str, Any]) -> str | None:
    raw = str(
        payload.get("event_kind")
        or payload.get("event")
        or payload.get("kind")
        or payload.get("type")
        or ""
    ).lower()
    aliases = {
        "task_started": "turn_start",
        "task_start": "turn_start",
        "task_complete": "turn_complete",
        "task_completed": "turn_complete",
        "turn_aborted": "turn_abort",
        "context_compacted": "compaction",
    }
    if raw in aliases:
        return aliases[raw]
    for candidate in (
        "turn_start",
        "turn_complete",
        "turn_abort",
        "agent_start",
        "agent_complete",
        "compaction",
        "approval",
        "error",
    ):
        if candidate in marker or raw == candidate:
            return candidate
    return None


def _event_outcome(
    event_kind: str,
    payload: Mapping[str, Any],
) -> str | None:
    raw = str(payload.get("outcome") or payload.get("status") or "").lower()
    if event_kind == "approval":
        return (
            raw
            if raw in {"requested", "granted", "denied", "cancelled", "unknown"}
            else "unknown"
        )
    if event_kind in {"turn_complete", "agent_complete"}:
        return raw if raw in {"completed", "error", "aborted", "unknown"} else "unknown"
    if event_kind == "turn_abort":
        return "aborted"
    if event_kind == "error":
        return "error"
    return None


__all__ = ["CodexTrajectoryNormalizer", "DEFAULT_BOUNDS", "native_ref"]
