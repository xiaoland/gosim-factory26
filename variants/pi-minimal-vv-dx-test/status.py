"""Pure activity interpreter for the Pi-only dx variant."""
import json
import sys
import time


def main():
    facts = json.load(sys.stdin)
    messages = facts.get("native", {}).get("session_messages", [])
    # Timing and session readers can report the same message timestamp; the
    # session record carries the actual outcome rather than just message_end.
    latest_message = max(messages, key=lambda item: (
        item.get('at') or 0, bool(item.get('stop_reason'))), default={})
    latest = max((item.get("at") for item in messages if item.get("at") is not None), default=None)
    now = facts.get("observed_at", time.time())
    age = None if latest is None else max(0.0, now - latest)
    fresh = latest is not None and age <= 600
    lifecycle = facts.get('lifecycle')
    if lifecycle in {'completed', 'failed', 'stopped', 'paused'}:
        return {'activity': 'inactive', 'brief': latest_message.get('error') or lifecycle,
                'last_activity_at': latest, 'evidence': latest_message}
    if latest_message.get('stop_reason') == 'error':
        return {'activity': 'error', 'brief': latest_message.get('error') or 'Pi model request failed',
                'last_activity_at': latest, 'evidence': latest_message}
    return {
        "activity": "active" if fresh else ("stale" if latest is not None else "unknown"),
        "brief": "latest Pi session message" if fresh else ("latest Pi session message is stale" if latest is not None else "session message unavailable"),
        "last_activity_at": latest,
        "evidence": {"source": "native.session_messages", "observed_at": now, "age_seconds": age,
                      "threshold_seconds": 600, "fresh": fresh},
    }


if __name__ == "__main__":
    json.dump(main(), sys.stdout, ensure_ascii=False)
