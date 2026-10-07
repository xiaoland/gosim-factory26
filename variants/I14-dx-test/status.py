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
    lifecycle = facts.get('lifecycle')
    if lifecycle == 'failed':
        errors = []
        for state in facts.get('native', {}).get('braid', {}).get('states', []):
            for session in state.get('provider_evidence', {}).get('sessions', []):
                error = (session.get('turn') or {}).get('error')
                if error:
                    errors.append({'source': state.get('source'), 'agent_id': session.get('agent_id'),
                                   'error': error})
        if errors:
            brief = '; '.join(dict.fromkeys(item['error'] for item in errors))
            return {'activity': 'inactive', 'brief': 'provider error: ' + brief[:1600],
                    'last_activity_at': latest, 'evidence': {'provider_errors': errors, 'observed_at': now}}
    if lifecycle in {'completed', 'failed', 'stopped', 'paused'}:
        return {'activity': 'inactive', 'brief': lifecycle, 'last_activity_at': latest,
                'evidence': {'source': 'lifecycle', 'observed_at': now}}
    return {
        "activity": "unknown" if latest is None else ("stale" if stale else "active"),
        "brief": "provider turn unavailable" if latest is None else ("provider turn older than 10 minutes" if stale else "recent provider turn"),
        "last_activity_at": latest,
        "evidence": {"source": "native.provider_turns", "observed_at": now, "age_seconds": age,
                      "threshold_seconds": 600, "fresh": latest is not None and age <= 600},
    }


if __name__ == "__main__":
    json.dump(main(), sys.stdout, ensure_ascii=False)
