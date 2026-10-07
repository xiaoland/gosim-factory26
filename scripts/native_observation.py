"""Variant-owned read-only native observation helpers.

The caller selects the native identities it owns (Pi and/or Braid).  Results
are bounded facts for status interpretation; complete native files remain in
the run's preserved harness data and are never rewritten here.
"""

from __future__ import annotations

from collections import deque
from datetime import datetime
import json
from pathlib import Path
import time
from typing import Any

try:
    from .braid_provider_evidence import collect as collect_braid
except ImportError:  # direct packaged execution beside the helper
    from braid_provider_evidence import collect as collect_braid


def _stamp(value: Any) -> float | None:
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
        except ValueError:
            return None
    if isinstance(value, (int, float)):
        return value / 1000 if value > 10_000_000_000 else float(value)
    return None


def _pi(run: Path, scope: str, observed_at: float, since: float | None) -> dict[str, Any]:
    harness = run / "data" / "harness" / scope
    messages, turns, errors = deque(maxlen=500), deque(maxlen=500), deque(maxlen=20)
    sessions: dict[str, dict[str, Any]] = {}
    usage_groups, seen_usage = {}, set()
    candidates = set(harness.rglob("session.jsonl")) | set(harness.rglob("pi-timing.jsonl"))
    for path in sorted(candidates):
        session_id = None
        source = str(path.relative_to(run))
        try:
            with path.open(encoding="utf-8") as stream:
                for number, line in enumerate(stream, 1):
                    try:
                        value = json.loads(line)
                        if not isinstance(value, dict):
                            raise ValueError("native record is not an object")
                        kind = value.get("kind") or value.get("type")
                        if kind == "session":
                            session_id = value.get("id")
                            continue
                        identity = value.get("native_session_id") or value.get("session_id") or session_id
                        if not identity:
                            continue
                        stamp = _stamp(value.get("at_ms", value.get("timestamp")))
                        if stamp is None:
                            continue
                        row = {"at": stamp, "source": source, "session_id": identity,
                               "turn_id": value.get("turn_id"), "request_id": value.get("request_id"),
                               "response_id": value.get("response_id"), "event": kind}
                        message = value.get("message") or {}
                        usage = message.get('usage') if isinstance(message, dict) else None
                        if (kind == 'message' and isinstance(message, dict) and message.get('role') == 'assistant'
                                and isinstance(usage, dict) and since is not None and stamp >= since):
                            # Count producer messages, not timing copies or migrated
                            # history. Native cost=0 is not a provider bill.
                            key = (str(identity), value.get('id') or value.get('timestamp'))
                            if key not in seen_usage:
                                seen_usage.add(key)
                                group = (str(identity), message.get('provider'), message.get('model'))
                                summary = usage_groups.setdefault(group, {'session_id': str(identity),
                                    'provider': message.get('provider'), 'model': message.get('model'),
                                    'messages': 0, 'tokens': {}, 'source': source})
                                summary['messages'] += 1
                                for field in ('input', 'output', 'cacheRead', 'cacheWrite', 'reasoning', 'totalTokens'):
                                    amount = usage.get(field)
                                    if isinstance(amount, (int, float)) and not isinstance(amount, bool):
                                        summary['tokens'][field] = summary['tokens'].get(field, 0) + amount
                        if isinstance(message, dict) and message.get("stopReason"):
                            row["stop_reason"] = message["stopReason"]
                            if message.get("errorMessage"):
                                row["error"] = str(message["errorMessage"])[:16384]
                        if kind in {"message", "message_end"}:
                            messages.append(row)
                        if kind in {"response_headers", "message_end", "provider_turn", "turn_complete"}:
                            turns.append(row)
                        prior = sessions.get(str(identity))
                        if prior is None or stamp >= prior["last_activity_at"]:
                            state = {"request_start": "active", "first_update": "active",
                                     "activity_sample": "active", "tool_start": "waiting_tool",
                                     "tool_end": "active", "message_end": "observed"}.get(kind, "observed")
                            sessions[str(identity)] = {"session_id": identity, "state": state,
                                "last_activity_at": stamp, "observed_at": observed_at,
                                "source": source, "reader_status": "ok",
                                "request_id": value.get("request_id"), "turn_id": value.get("turn_id")}
                    except (ValueError, TypeError, OverflowError) as exc:
                        errors.append({"source": source, "line": number,
                                       "error": f"{type(exc).__name__}: {exc}"})
        except (OSError, UnicodeError) as exc:
            errors.append({"source": source, "error": f"{type(exc).__name__}: {exc}"})
    return {"sessions": list(sessions.values()), "session_messages": list(messages),
            "provider_turns": list(turns), "reader_errors": list(errors),
            "usage": {'scope': 'current-run-native-messages', 'since': since, 'as_of': observed_at,
                      'status': 'partial' if since is not None else 'unknown',
                      'items': list(usage_groups.values()),
                      'note': 'Only recorded native messages; unrecorded/in-flight usage and provider bills are unknown.'}}


def observe(run: str | Path, *, provider: str, braid: bool = False) -> dict[str, Any]:
    run = Path(run).resolve()
    now = time.time()
    manifest_path = run / "manifest.json"
    state = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.is_file() else {}
    scope = state.get("native_scope_id")
    result: dict[str, Any] = {"observed_at": now, "provider": provider,
                              "sessions": [], "session_messages": [], "provider_turns": [],
                              "reader_errors": [], "braid": {"observed_at": now, "states": [], "gaps": []}}
    if provider in {"pi", "pi-braid"} and isinstance(scope, str) and scope:
        result.update(_pi(run, scope, now, _stamp(state.get('created_at'))))
    elif provider not in {"pi", "pi-braid"}:
        result["reader_errors"].append({"source": "observer", "error": f"unsupported provider {provider}"})
    if braid and isinstance(scope, str) and scope:
        root = run / "data" / "harness" / scope
        states = []
        for status in sorted(root.rglob("braid-state/status.json")) if root.is_dir() else []:
            # The helper delegates to the repository's verified
            # provider_liveness reader (or its byte-identical packaged copy),
            # including native path resolution, activity windows, resume
            # attempts and concrete SQLite/native errors.
            evidence = collect_braid(status.parent, now, run=run, scope_id=scope)
            states.append({"source": str(status.relative_to(run)),
                           "status": evidence.get("status", {}),
                           "provider_evidence": evidence,
                           "observed_at": now})
        result["braid"] = {"observed_at": now, "states": states,
                            "sources": [item["source"] for item in states],
                            "gaps": [] if states else [{"source": str(root.relative_to(run)),
                                                           "reason": "Braid status unavailable"}],
                            "available": bool(states)}
    return result
