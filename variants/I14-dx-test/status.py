"""I14 activity interpreter; lifecycle belongs to the supervisor."""
import json
import sys
import time


def main():
    facts = json.load(sys.stdin)
    turns = facts.get("native", {}).get("provider_turns", [])
    latest = max((item.get("at") for item in turns if item.get("at") is not None), default=None)
    now = facts.get("observed_at", time.time())
    age = None if latest is None else max(0.0, now - latest)
    stale = age is not None and age > 600
    return {
        "activity": "unknown" if latest is None else ("stale" if stale else "active"),
        "brief": "provider turn unavailable" if latest is None else ("provider turn older than 10 minutes" if stale else "recent provider turn"),
        "last_activity_at": latest,
        "evidence": {"source": "native.provider_turns", "observed_at": now, "age_seconds": age,
                      "threshold_seconds": 600, "fresh": latest is not None and age <= 600},
    }


if __name__ == "__main__":
    json.dump(main(), sys.stdout, ensure_ascii=False)
