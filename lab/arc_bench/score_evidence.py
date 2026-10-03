"""Normalize saved ARC and legacy score evidence; no platform requests."""
import hashlib
import json
import math
from lab.exp.core import Blocked, error

def _fields(value, allowed, required=()):
    if not isinstance(value,dict) or set(value)-set(allowed) or set(required)-set(value):
        raise ValueError("invalid ARC score evidence binding")
    return value

def final_score(binding, base):
    """Bind a saved GET or a named legacy task, including its real run identity."""
    _fields(binding, ('source', 'run_id', 'task'), ('source', 'run_id'))
    path = (base / binding['source']).resolve()
    result = {'status': 'unavailable', 'source': str(path), 'run_id': binding['run_id']}
    try:
        source = path.read_bytes()
        raw = json.loads(source)
        result['source_sha256'] = hashlib.sha256(source).hexdigest()
        value = raw.get('value', raw)
        if 'tasks' in value:
            task = value['tasks'][binding['task']]
            run_id = task.get('run_id')
            value = {**task.get('platform_result', {}), 'status': task.get('remote_status'), 'id': run_id}
            if raw.get('pending'):
                raise Blocked('legacy source has an unresolved platform write')
        if value.get('id') != binding['run_id']:
            raise ValueError('score evidence does not bind the declared run')
        score, passed, failed = (value.get(key) for key in ('score', 'passed_count', 'failed_count'))
        total = value.get('total_tests')
        if total is None and type(passed) is int and type(failed) is int:
            total = passed + failed
        if (value.get('status') not in {'PASSED', 'FAILED'} or type(score) not in (int, float) or
                not math.isfinite(score) or not 0 <= score <= 100 or
                any(type(count) is not int or count < 0 for count in (passed, failed, total)) or
                total == 0 or passed + failed != total):
            raise Blocked('score source lacks a complete terminal percentage and test counts')
        result.update(status='complete', score_percent=score)
    except (OSError, KeyError, TypeError, Blocked) as exc:
        result['error'] = error(exc)
        result['error'].pop('observed_at', None)  # Read time is not part of a frozen selection decision.
    return result
