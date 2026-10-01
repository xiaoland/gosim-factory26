from __future__ import annotations

import subprocess
from pathlib import Path

from svc_cli.workspace import resolve_workspace_identity


def _git(root: Path, *arguments: str) -> None:
    subprocess.run(
        ("git", "-C", str(root), *arguments),
        check=True,
        capture_output=True,
        text=True,
        timeout=5,
    )


def test_workspace_owner_distinguishes_linked_worktrees(tmp_path: Path) -> None:
    root = tmp_path / "main"
    linked = tmp_path / "linked"
    root.mkdir()
    _git(root, "init")
    _git(root, "config", "user.email", "test@example.com")
    _git(root, "config", "user.name", "Test")
    (root / "README.md").write_text("fixture\n", encoding="utf-8")
    _git(root, "add", "README.md")
    _git(root, "commit", "-m", "fixture")
    _git(root, "worktree", "add", "-b", "linked", str(linked))

    main = resolve_workspace_identity(root, namespace="fixture")
    other = resolve_workspace_identity(linked, namespace="fixture")
    assert main.repository_id == other.repository_id
    assert main.worktree_id != other.worktree_id
