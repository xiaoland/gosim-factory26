"""Record model parameter routing without prompts or credentials."""

import json
import os
from pathlib import Path
import time

from responses_compat import CustomLogger, sanitize_responses_input


PARAMETERS = ("model", "reasoning", "thinking", "max_tokens", "max_output_tokens",
              "temperature", "top_p", "tool_choice")
MODELS = {"glm-5.3-flash", "kimi-k3", "deepseek-v4-flash-vision-exp"}


class GatewayCompat(CustomLogger):
    async def async_pre_call_hook(self, user_api_key_dict, cache, data, call_type):
        if call_type in {"responses", "aresponses"}:
            data = sanitize_responses_input(data)
        if isinstance(data, dict) and data.get("model") in MODELS:
            for name in ("reasoning", "reasoning_effort", "thinking", "max_tokens",
                         "max_output_tokens", "temperature", "top_p"):
                data.pop(name, None)
            field = "max_output_tokens" if call_type in {"responses", "aresponses"} else "max_tokens"
            data[field] = 16384
        if isinstance(data, dict) and (path := os.environ.get("GATEWAY_REQUEST_LOG")):
            record = {"time_ns": time.time_ns(), "api": call_type,
                      **{name: data[name] for name in PARAMETERS if name in data}}
            with Path(path).open("a") as output:
                output.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
        return data


proxy_handler_instance = GatewayCompat()
