"""Workspace identity shared by local SVC execution domains."""

from __future__ import annotations

import hashlib
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Literal

from .errors import SvcError
from .model import ValueModel


def _digest(*parts: str, length: int = 20) -> str:
    payload = "\0".join(parts).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:length]


class WorkspaceIdentity(ValueModel):
    """Stable identity facts for one executable workspace."""

    root: Path
    namespace_id: str
    repository_kind: Literal["git", "non-git"]
    repository_id: str
    worktree_id: str
    instance: str


def resolve_workspace_identity(
    root: Path, *, namespace: str | None = None
) -> WorkspaceIdentity:
    """Resolve Git common/private worktree facts, with a deterministic fallback."""

    workspace = _workspace_root(root)
    namespace_id = _namespace_id(namespace)
    git = _git_paths(workspace)
    if git is None:
        workspace_id = _digest("non-git-workspace", str(workspace))
        return WorkspaceIdentity(
            root=workspace,
            namespace_id=namespace_id,
            repository_kind="non-git",
            repository_id=workspace_id,
            worktree_id=workspace_id,
            instance=_digest("instance", namespace_id, workspace_id, length=16),
        )

    common_dir, git_dir = git
    common_id = _digest("git-common", str(common_dir))
    private_marker = (
        "main"
        if git_dir == common_dir
        else _relative_private_marker(common_dir, git_dir)
    )
    worktree_id = _digest("git-worktree", common_id, private_marker)
    return WorkspaceIdentity(
        root=workspace,
        namespace_id=namespace_id,
        repository_kind="git",
        repository_id=common_id,
        worktree_id=worktree_id,
        instance=_digest("instance", namespace_id, worktree_id, length=16),
    )


def _workspace_root(root: Path) -> Path:
    try:
        resolved = root.resolve(strict=True)
    except OSError as error:
        raise SvcError(
            "workspace-not-directory", "Workspace does not exist.", {"root": str(root)}
        ) from error
    if not resolved.is_dir():
        raise SvcError(
            "workspace-not-directory",
            "Workspace is not a directory.",
            {"root": str(root)},
        )
    return resolved


def _namespace_id(namespace: str | None) -> str:
    if namespace is not None:
        if not namespace or "\0" in namespace:
            raise SvcError(
                "invalid-execution-namespace",
                "Execution namespace must be a non-empty string.",
            )
        material = namespace
    else:
        uid = str(os.getuid()) if hasattr(os, "getuid") else "unknown-user"
        material = "|".join((sys.platform, platform.node(), uid))
    return _digest("namespace", material)


def _git_paths(workspace: Path) -> tuple[Path, Path] | None:
    completed = subprocess.run(
        (
            "git",
            "-C",
            str(workspace),
            "rev-parse",
            "--is-bare-repository",
            "--path-format=absolute",
            "--git-common-dir",
            "--git-dir",
        ),
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        return None
    lines = completed.stdout.splitlines()
    if len(lines) != 3 or lines[0] != "false":
        if lines and lines[0] == "true":
            raise SvcError(
                "bare-repository",
                "A bare Git repository is not an executable workspace.",
            )
        return None
    common_dir = Path(lines[1]).resolve()
    git_dir = Path(lines[2]).resolve()
    if not common_dir.is_dir() or not git_dir.is_dir():
        raise SvcError(
            "invalid-git-worktree",
            "Git did not report usable worktree administration directories.",
        )
    return common_dir, git_dir


def _relative_private_marker(common_dir: Path, git_dir: Path) -> str:
    try:
        return git_dir.relative_to(common_dir).as_posix()
    except ValueError:
        return f"external:{git_dir}"
