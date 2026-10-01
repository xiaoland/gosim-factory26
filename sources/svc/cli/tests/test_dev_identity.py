from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from svc_cli.dev.identity import (
    interpolate_dev_argv,
    interpolate_dev_value,
    require_worktree_provenance,
    resolve_capability_identity,
)
from svc_cli.errors import SvcError
from svc_cli.workspace import resolve_workspace_identity


def test_non_git_fallback_and_scope_specific_lock_identity() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        workspace = resolve_workspace_identity(Path(tmp), namespace="fixture")
        assert workspace.repository_kind == "non-git"
        worktree = resolve_capability_identity(
            workspace,
            scope="worktree",
            target="app",
            endpoint_identity=f"http://app-{workspace.instance}.localhost/health",
        )
        repository = resolve_capability_identity(
            workspace,
            scope="repository",
            target="app",
            endpoint_identity="tcp://127.0.0.1:5432",
        )
        assert worktree.capability_id != repository.capability_id
        with pytest.raises(SvcError, match="host_key"):
            resolve_capability_identity(
                workspace,
                scope="host",
                target="app",
                endpoint_identity="tcp://127.0.0.1:5432",
            )


def test_interpolation_is_constrained_to_declared_dev_tokens() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        workspace = resolve_workspace_identity(Path(tmp), namespace="fixture")
        value = interpolate_dev_value(
            "http://${dev.target}-${dev.instance}.localhost",
            workspace,
            target="frontend",
        )
        assert value == f"http://frontend-{workspace.instance}.localhost"
        assert interpolate_dev_argv(
            ("tool", "--id=${dev.worktree.id}"), workspace, target="frontend"
        ) == (
            "tool",
            f"--id={workspace.worktree_id}",
        )
        with pytest.raises(SvcError, match="interpolation"):
            interpolate_dev_value("${HOME}", workspace, target="frontend")


def test_worktree_provenance_requires_the_resolved_instance() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        workspace = resolve_workspace_identity(Path(tmp), namespace="fixture")
        resolved = f"http://frontend-{workspace.instance}.localhost/health"

        require_worktree_provenance("worktree", resolved, workspace)
        with pytest.raises(SvcError, match="provenance"):
            require_worktree_provenance(
                "worktree", "http://static.localhost/health", workspace
            )
