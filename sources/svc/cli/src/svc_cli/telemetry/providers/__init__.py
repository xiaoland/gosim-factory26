"""Static local telemetry provider adapters."""

from .codex_rollout import CodexRolloutProvider


_FACTORIES = {"codex": CodexRolloutProvider}


def provider(provider_id: str = "codex") -> CodexRolloutProvider:
    """Return a reviewed in-process provider; no dynamic plugin loading exists."""

    try:
        return _FACTORIES[provider_id]()
    except KeyError as error:
        raise ValueError(f"Unknown local telemetry provider: {provider_id}") from error


__all__ = ["CodexRolloutProvider", "provider"]
