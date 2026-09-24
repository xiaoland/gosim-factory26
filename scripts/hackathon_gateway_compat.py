"""Record model parameter routing without prompts or credentials."""

import json
import os
from pathlib import Path
import time

from responses_compat import CustomLogger, sanitize_responses_input


PARAMETERS = ("model", "reasoning", "reasoning_effort", "thinking", "max_tokens", "max_output_tokens", "max_completion_tokens",
              "temperature", "top_p", "tool_choice")
OUTPUT_FIELDS = ("max_tokens", "max_output_tokens", "max_completion_tokens")


def record_parameters(data, **metadata):
    if path := os.environ.get("GATEWAY_REQUEST_LOG"):
        record = {"time_ns": time.time_ns(), **metadata,
                  **{name: data[name] for name in PARAMETERS if name in data}}
        with Path(path).open("a") as output:
            output.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")


class GatewayCompat(CustomLogger):
    def log_pre_api_call(self, model, messages, kwargs):
        payload = kwargs.get("additional_args", {}).get("complete_input_dict")
        if isinstance(payload, dict):
            record_parameters(payload, stage="upstream", model=model)

    async def async_pre_call_hook(self, user_api_key_dict, cache, data, call_type):
        if call_type in {"responses", "aresponses"}:
            data = sanitize_responses_input(data)
        requested = {name: data[name] for name in OUTPUT_FIELDS if name in data} if isinstance(data, dict) else {}
        if isinstance(data, dict):
            # This experiment uses provider defaults, including the output limit.
            # Pi inserts a default cap even when its model descriptor omits it.
            for name in ("reasoning", "reasoning_effort", "thinking", "max_tokens",
                         "max_output_tokens", "max_completion_tokens", "temperature", "top_p"):
                data.pop(name, None)
            record_parameters(data, stage="normalized", api=call_type, requested_output_limits=requested)
        return data


proxy_handler_instance = GatewayCompat()
