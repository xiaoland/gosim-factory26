"""Read-only Braid provider evidence for a variant-owned observer.

This module deliberately owns the Braid status/SQLite format knowledge.  The
public execution layer receives its bounded JSON result and does not inspect
the Braid directory or database itself.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
import time
from typing import Any

_repo_root = Path(__file__).resolve().parents[1]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

try:
    # Source-tree execution uses the existing verified reader.  Packagers
    # must include that same file beside this helper; no second SQL reader is
    # maintained here.
    from provider_liveness import collect_provider_evidence
except ImportError:  # pragma: no cover - selected only by packaged layouts
    from lab.arc_bench.provider_liveness import collect_provider_evidence


def collect(state_root: str | Path, observed_at: float | None = None, *,
            run: str | Path | None = None, scope_id: str | None = None) -> dict[str, Any]:
    root = Path(state_root)
    now = observed_at if observed_at is not None else time.time()
    result: dict[str, Any] = {"source": str(root / "status.json"), "observed_at": now}
    scope_root = root.parent

    def resolve_native(path: Path) -> Path | None:
        if path.is_file():
            return path
        parts = path.parts
        if scope_id and scope_id in parts:
            suffix = Path(*parts[parts.index(scope_id) + 1:])
        elif ".factory26" in parts:
            suffix = Path(*parts[parts.index(".factory26") + 1:])
            prefix = ("data", "harness", scope_id or "")
            if suffix.parts[:len(prefix)] == prefix:
                suffix = Path(*suffix.parts[len(prefix):])
        else:
            return None
        direct = scope_root / suffix
        if direct.is_file():
            return direct
        for candidate in scope_root.rglob(suffix.name):
            if candidate.is_file() and candidate.parts[-len(suffix.parts):] == suffix.parts:
                return candidate
        return None

    evidence = collect_provider_evidence(root, now, native_resolver=resolve_native)
    # Preserve the existing reader's complete diagnostic contract, adding the
    # status projection expected by the variant activity interpreter.
    try:
        status = json.loads((root / "status.json").read_text(encoding="utf-8"))
        evidence["status"] = {key: status.get(key) for key in (
            "active_turns", "pending_batches", "pending_events", "pending_continuations",
            "pending_resets", "materializing_groups", "blocked_groups", "provider_health")}
    except (OSError, UnicodeError, ValueError) as exc:
        evidence.setdefault("errors", []).append(f"status projection: {type(exc).__name__}: {exc}")
    return evidence
