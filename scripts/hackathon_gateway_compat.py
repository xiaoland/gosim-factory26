"""Record model parameter routing without prompts or credentials."""

import json
import os
from pathlib import Path
import hashlib
import secrets
import sys
from threading import Lock
import time

from responses_compat import CustomLogger, sanitize_responses_input


PARAMETERS = ("model", "reasoning", "reasoning_effort", "thinking", "max_tokens", "max_output_tokens", "max_completion_tokens",
              "temperature", "top_p", "tool_choice")
OUTPUT_FIELDS = ("max_tokens", "max_output_tokens", "max_completion_tokens")
WRITE_LOCK = Lock()


async def user_api_key_auth(request, api_key):
    """Bind one ordinary client API key to its lab run before model routing."""
    from fastapi import HTTPException
    from litellm.proxy._types import UserAPIKeyAuth

    master = os.environ.get("LITELLM_MASTER_KEY", "")
    if master and secrets.compare_digest(api_key, master):
        return UserAPIKeyAuth(api_key=api_key, metadata={"binding": "legacy-shared"})
    directory = Path(os.environ["GATEWAY_BINDINGS_DIR"])
    binding_id = hashlib.sha256(api_key.encode()).hexdigest()
    path = directory / f"{binding_id}.json"
    try:
        binding = json.loads(path.read_text())
    except FileNotFoundError as exc:
        raise HTTPException(status_code=401, detail="unknown or revoked local gateway credential") from exc
    except (OSError, ValueError) as exc:
        raise HTTPException(status_code=503, detail=f"local gateway binding unavailable: {exc}") from exc
    return UserAPIKeyAuth(api_key=api_key, metadata={
        "binding_id": binding_id, "run_id": binding["run_id"],
        "legacy_run_id": binding.get("legacy_run_id"),
        "attempt_id": binding.get("attempt_id"),
        "experiment_id": binding.get("experiment_id"),
        "incarnation": binding.get("incarnation"),
        "config_sha256": binding.get("config_sha256"),
        "request_id": secrets.token_hex(16)})


def _context(user_api_key_dict):
    value = getattr(user_api_key_dict, "metadata", None)
    return {key: value[key] for key in ("binding_id", "run_id", "legacy_run_id", "attempt_id", "experiment_id", "incarnation", "config_sha256", "request_id")
            if isinstance(value, dict) and key in value}


def _record(value):
    if path := os.environ.get("GATEWAY_REQUEST_LOG"):
        try:
            with WRITE_LOCK, Path(path).open("a") as output:
                output.write(json.dumps({"time_ns": time.time_ns(), **value},
                                        ensure_ascii=False, default=str) + "\n")
        except OSError as exc:
            print(f"gateway diagnostic write failed: {exc}", file=sys.stderr)


def record_parameters(data, **metadata):
    _record({**metadata, **{name: data[name] for name in PARAMETERS if name in data}})


class GatewayCompat(CustomLogger):
    def log_pre_api_call(self, model, messages, kwargs):
        payload = kwargs.get("additional_args", {}).get("complete_input_dict")
        if isinstance(payload, dict):
            metadata = payload.get("metadata") or payload.get("litellm_metadata") or {}
            identity = (metadata.get("factory26_gateway") or metadata.get("user_api_key_metadata")) if isinstance(
                metadata, dict) else None
            record_parameters(payload, stage="upstream", model=model,
                              **{key: identity[key] for key in ("binding_id", "run_id", "request_id")
                                 if isinstance(identity, dict) and key in identity})

    async def async_pre_call_hook(self, user_api_key_dict, cache, data, call_type):
        if call_type in {"responses", "aresponses"}:
            data = sanitize_responses_input(data)
        context = _context(user_api_key_dict)
        if isinstance(data, dict):
            metadata = data.get("metadata")
            if context and isinstance(metadata, dict):
                metadata["factory26_gateway"] = context
            elif context and metadata is None:
                data["metadata"] = {"factory26_gateway": context}
            record_parameters(data, stage="requested", api=call_type, **context)
        requested = {name: data[name] for name in OUTPUT_FIELDS if name in data} if isinstance(data, dict) else {}
        if isinstance(data, dict):
            # Historical raw runs use provider defaults; recipe comparisons retain
            # the client's explicit parameters instead.
            # Pi inserts a default cap even when its model descriptor omits it.
            if os.environ.get("GATEWAY_PRESERVE_PARAMETERS") != "1":
                for name in ("reasoning", "reasoning_effort", "thinking", "max_tokens",
                             "max_output_tokens", "max_completion_tokens", "temperature", "top_p"):
                    data.pop(name, None)
            elif "thinking" in data:
                # This is a vendor Chat field, not an OpenAI SDK parameter.
                data.setdefault("extra_body", {})["thinking"] = data.pop("thinking")
            record_parameters({**data, **data.get("extra_body", {})}, stage="normalized",
                              api=call_type, requested_output_limits=requested, **context)
        return data

    async def async_post_call_success_hook(self, data, user_api_key_dict, response):
        usage = getattr(response, "usage", None)
        if hasattr(usage, "model_dump"):
            usage = usage.model_dump()
        elif not isinstance(usage, dict):
            usage = None
        _record({"stage": "response", "status": "stream-opened" if isinstance(data, dict) and
                 data.get("stream") else "completed", "usage": usage,
                 **_context(user_api_key_dict)})
        return None

    async def async_post_call_failure_hook(self, request_data, original_exception, user_api_key_dict,
                                           traceback_str=None):
        _record({"stage": "failure", "error_type": type(original_exception).__name__,
                 "error": str(original_exception), **_context(user_api_key_dict)})
        return None

    async def async_post_call_streaming_iterator_hook(self, user_api_key_dict, response, request_data):
        context = _context(user_api_key_dict)
        terminal = None
        chunks = 0
        try:
            async for chunk in response:
                chunks += 1
                item = chunk if isinstance(chunk, dict) else {}
                event = item.get("type") if item else getattr(chunk, "type", None)
                if event in ("response.completed", "response.failed", "response.incomplete"):
                    terminal = event
                choices = item.get("choices") if item else getattr(chunk, "choices", None)
                if choices and any((choice.get("finish_reason") if isinstance(choice, dict) else
                                    getattr(choice, "finish_reason", None)) for choice in choices):
                    terminal = "chat.finish_reason"
                yield chunk
        except BaseException as exc:
            _record({"stage": "stream", "status": "interrupted", "error_type": type(exc).__name__,
                     "error": str(exc), "chunks": chunks, **context})
            raise
        else:
            _record({"stage": "stream", "status": terminal or "eof-without-terminal",
                     "chunks": chunks, **context})


proxy_handler_instance = GatewayCompat()
