"""Read current-producer gateway facts without inventing prices or billing units."""
import json


def collect(run, state):
    scope = state.get('native_scope_id')
    if not scope:
        return None
    path = run / 'data/harness' / scope / 'producers' / state['run_id'] / 'gateway.log'
    if not path.is_file():
        return None
    attempts, current, errors = {}, {}, []
    try:
        with path.open(encoding='utf-8') as stream:
            for number, line in enumerate(stream, 1):
                try:
                    event = json.loads(line)
                    if event.get('run_id') != state['run_id']:
                        continue
                    request = event.get('request_id')
                    details = event.get('details') or {}
                    kind = event.get('event')
                    attempt = details.get('attempt') or (details.get('channel') or {}).get('attempt')
                    if kind == 'attempt':
                        current[request] = attempt
                        attempts[(request, attempt)] = {
                            'request_id': request, 'attempt': attempt,
                            'deployment_id': event.get('deployment_id'),
                            'provider': details.get('provider'), 'plan': details.get('plan'),
                            'wire_model': details.get('wire_model'),
                            'usage_status': 'not_returned', 'usage': None,
                            'monetary_status': 'unknown',
                        }
                    row = attempts.get((request, attempt or current.get(request)))
                    if row is None:
                        continue
                    row['as_of'] = event.get('timestamp_ms')
                    if kind == 'upstream_headers':
                        row['http_status'] = details.get('http_status')
                    elif kind == 'usage':
                        capture = details.get('capture') or {}
                        returned = capture.get('returned') or {}
                        row.update(usage_status=capture.get('status'), usage=returned.get('usage'),
                                   response_id=returned.get('response_id'),
                                   response_complete=capture.get('response_complete'),
                                   capture_truncated=capture.get('capture_truncated'))
                    elif kind in {'terminal', 'fallback', 'transport_error', 'upstream_error'}:
                        row['outcome'] = details.get('reason') or kind
                except (ValueError, TypeError, AttributeError) as exc:
                    errors.append({'line': number, 'error': f'{type(exc).__name__}: {exc}'})
    except (OSError, UnicodeError) as exc:
        errors.append({'error': f'{type(exc).__name__}: {exc}'})
    return {'scope': 'current-run-provider-attempts', 'source': str(path.relative_to(run)),
            'status': 'partial', 'attempts': list(attempts.values()), 'reader_errors': errors,
            'note': 'Returned usage is not a bill, purchase cost, or inferred plan credits.'}
