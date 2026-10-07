"""Compatibility adapter for frozen runs without a program observer.

Format readers remain in the explicit native helper modules.  This adapter
only selects the historical Pi/Braid identity from the preserved run tree;
it does not become another parser.
"""

from __future__ import annotations

from pathlib import Path

try:
    from .native_observation import observe as observe_native
except ImportError:  # direct packaged execution beside the helper
    from native_observation import observe as observe_native


def observe(run: str | Path) -> dict:
    run = Path(run).resolve()
    manifest = run / "manifest.json"
    state = {}
    if manifest.is_file():
        import json
        state = json.loads(manifest.read_text(encoding="utf-8"))
    scope = state.get("native_scope_id")
    scope_root = run / "data" / "harness" / str(scope) if scope else None
    braid = bool(scope_root and list(scope_root.rglob("braid-state/status.json")))
    return observe_native(run, provider="pi-braid" if braid else "pi", braid=braid)
