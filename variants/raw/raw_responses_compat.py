"""Keep Codex's Responses request aligned with the raw model API contract."""

from responses_compat import CustomLogger, sanitize_responses_input


class RawResponsesCompat(CustomLogger):
    async def async_pre_call_hook(self, user_api_key_dict, cache, data, call_type):
        if call_type not in {"responses", "aresponses"}:
            return data
        result = sanitize_responses_input(data)
        # Codex's own effort setting must not override the model API's thinking field.
        if isinstance(result, dict):
            result.pop("reasoning", None)
        return result


proxy_handler_instance = RawResponsesCompat()
