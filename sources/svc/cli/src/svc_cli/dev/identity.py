"""Workspace-safe identities and constrained dev configuration interpolation."""

from __future__ import annotations

import hashlib
import re
from typing import Literal, Sequence, cast

from ..errors import SvcError
from ..model import ValueModel
from ..workspace import WorkspaceIdentity


_TOKEN = re.compile(r"\$\{([^}]+)\}")
_TOKEN_NAMES = frozenset(
    {
        "dev.instance",
        "dev.worktree.id",
        "dev.target",
    }
)
_SCOPES = frozenset({"worktree", "repository", "host"})
DevScope = Literal["worktree", "repository", "host"]


def _digest(*parts: str, length: int = 20) -> str:
    payload = "\0".join(parts).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:length]


class CapabilityIdentity(ValueModel):
    scope: DevScope
    target: str
    endpoint_id: str
    scope_id: str
    capability_id: str


def resolve_capability_identity(
    workspace: WorkspaceIdentity,
    *,
    scope: str,
    target: str,
    endpoint_identity: str,
    host_key: str | None = None,
) -> CapabilityIdentity:
    """Identify one declared capability independently of an operation intent."""

    if scope not in _SCOPES:
        raise SvcError(
            "invalid-dev-scope", "Dev target scope is invalid.", {"scope": scope}
        )
    if not target or not endpoint_identity:
        raise SvcError("invalid-dev-identity", "Dev identity fields must be non-empty.")
    if scope == "worktree":
        scope_id = workspace.worktree_id
    elif scope == "repository":
        scope_id = workspace.repository_id
    else:
        if not host_key:
            raise SvcError(
                "missing-host-key", "Host-scoped targets require an explicit host_key."
            )
        scope_id = _digest("host-scope", workspace.namespace_id, host_key)

    endpoint_id = _digest("endpoint", endpoint_identity)
    material = (workspace.namespace_id, scope, scope_id, target)
    return CapabilityIdentity(
        scope=cast(DevScope, scope),
        target=target,
        endpoint_id=endpoint_id,
        scope_id=scope_id,
        capability_id=_digest("capability", *material, length=48),
    )


def interpolate_dev_value(
    value: str, workspace: WorkspaceIdentity, *, target: str
) -> str:
    """Substitute the three non-secret tokens without invoking a shell."""

    values = {
        "dev.instance": workspace.instance,
        "dev.worktree.id": workspace.worktree_id,
        "dev.target": target,
    }

    def replace(match: re.Match[str]) -> str:
        token = match.group(1)
        if token not in _TOKEN_NAMES:
            raise SvcError(
                "unknown-dev-interpolation",
                "Only documented ${dev.*} interpolation tokens are allowed.",
                {"token": token},
            )
        return values[token]

    return _TOKEN.sub(replace, value)


def interpolate_dev_argv(
    argv: Sequence[str], workspace: WorkspaceIdentity, *, target: str
) -> tuple[str, ...]:
    if not argv or any(not isinstance(item, str) or not item for item in argv):
        raise SvcError(
            "invalid-dev-argv", "Dev command argv must be a non-empty string array."
        )
    return tuple(interpolate_dev_value(item, workspace, target=target) for item in argv)


def require_worktree_provenance(
    scope: str, endpoint_identity: str, workspace: WorkspaceIdentity
) -> None:
    """Reject static healthy endpoints for application targets in linked worktrees."""

    if scope == "worktree" and workspace.instance not in endpoint_identity:
        raise SvcError(
            "worktree-provenance-unverified",
            "A worktree-scoped target probe must expose this worktree's resolved instance.",
            {"instance": workspace.instance},
        )
