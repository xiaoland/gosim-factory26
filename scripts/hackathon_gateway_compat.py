"""Record model parameter routing without prompts or credentials."""

import json
import os
from pathlib import Path
import time

from responses_compat import CustomLogger, sanitize_responses_input


PARAMETERS = ("model", "reasoning", "thinking", "max_tokens", "max_output_tokens", "max_completion_tokens",
              "temperature", "top_p", "tool_choice")
MODEL_LIMITS = json.loads((Path(__file__).resolve().parents[1] / "submission/hackathon_models.json").read_text())
OUTPUT_FIELDS = ("max_tokens", "max_output_tokens", "max_completion_tokens")


class GatewayCompat(CustomLogger):
    async def async_pre_call_hook(self, user_api_key_dict, cache, data, call_type):
        if call_type in {"responses", "aresponses"}:
            data = sanitize_responses_input(data)
        requested = {name: data[name] for name in OUTPUT_FIELDS if name in data} if isinstance(data, dict) else {}
        if isinstance(data, dict) and data.get("model") in MODEL_LIMITS:
            budgets = [value for value in requested.values() if value is not None]
            if any(type(value) is not int or value <= 0 for value in budgets):
                raise ValueError("output token limits must be positive integers")
            # Preserve a client's smaller budget, including Pi's remaining-context clamp.
            budget = min([MODEL_LIMITS[data["model"]]["maxTokens"], *budgets])
            for name in ("reasoning", "reasoning_effort", "thinking", "max_tokens",
                         "max_output_tokens", "max_completion_tokens", "temperature", "top_p"):
                data.pop(name, None)
            field = "max_output_tokens" if call_type in {"responses", "aresponses"} else "max_tokens"
            data[field] = budget
        if isinstance(data, dict) and (path := os.environ.get("GATEWAY_REQUEST_LOG")):
            record = {"time_ns": time.time_ns(), "api": call_type,
                      "requested_output_limits": requested,
                      **{name: data[name] for name in PARAMETERS if name in data}}
            with Path(path).open("a") as output:
                output.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
        return data


proxy_handler_instance = GatewayCompat()
