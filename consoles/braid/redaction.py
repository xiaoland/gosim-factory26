"""The Console's existing credential redaction, shared by fixed readers."""

import os
import re


secrets = [v for k, v in os.environ.items() if len(v) >= 8 and re.search(r"(?i)(api.?key|token|secret|password)", k)]


def redact(value):
    if isinstance(value, dict):
        return {k: "[已隐藏凭据]" if re.fullmatch(r"(?i)(api[_-]?key|access[_-]?token|refresh[_-]?token|token|authorization|password|secret|credential)", k) else redact(v) for k, v in value.items()}
    if isinstance(value, list):
        return [redact(v) for v in value]
    if isinstance(value, str):
        for secret in secrets:
            value = value.replace(secret, "[已隐藏凭据]")
        value = re.sub(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+", "Bearer [已隐藏凭据]", value)
        value = re.sub(r"\b(?:sk|ghp|gho|github_pat)-?[A-Za-z0-9_-]{20,}\b", "[已隐藏凭据]", value)
        value = re.sub(r"(?i)((?:[a-z0-9_]*(?:api[_-]?key|access[_-]?token|refresh[_-]?token|password|secret))[\"']?\s*[=:]\s*[\"']?)([^\s\"',;]+)", r"\1[已隐藏凭据]", value)
    return value
