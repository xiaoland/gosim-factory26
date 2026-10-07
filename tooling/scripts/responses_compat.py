"""Small LiteLLM Responses input compatibility hook.

Some Codex Responses turns contain an assistant ``output_text`` block whose
text is exactly the empty string between function calls and their outputs.
Strict Chat gateways reject that block.  This hook removes only that proven
empty Responses input block and an enclosing message left with no content.
"""

from copy import deepcopy

try:
    from litellm.integrations.custom_logger import CustomLogger
except ImportError:  # Keep the pure sanitizer importable by repository tests.
    class CustomLogger:  # type: ignore[no-redef]
        pass


_TEXT_TYPES = {"text", "input_text", "output_text"}


def sanitize_responses_input(data):
    """Return a copy with exact-empty text blocks removed from ``input`` only."""
    result = deepcopy(data)
    if not isinstance(result, dict) or not isinstance(result.get("input"), list):
        return result

    cleaned = []
    for item in result["input"]:
        if not (
            isinstance(item, dict)
            and item.get("type") == "message"
            and isinstance(item.get("content"), list)
        ):
            cleaned.append(item)
            continue

        content = [
            block
            for block in item["content"]
            if not (
                isinstance(block, dict)
                and block.get("type") in _TEXT_TYPES
                and block.get("text") == ""
            )
        ]
        if content:
            item["content"] = content
            cleaned.append(item)
    result["input"] = cleaned
    return result


class ResponsesCompat(CustomLogger):
    async def async_pre_call_hook(self, user_api_key_dict, cache, data, call_type):
        if call_type not in {"responses", "aresponses"}:
            return data
        return sanitize_responses_input(data)


proxy_handler_instance = ResponsesCompat()
