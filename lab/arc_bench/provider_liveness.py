"""Read provider activity and report bounded liveness suspicion, without models or control."""
import datetime
import hashlib
import json
import re
import shutil
from pathlib import Path
import sqlite3
import time


def epoch(value):
    if isinstance(value, (int, float)):
        return value / 1e9 if value > 1e17 else value / 1e3 if value > 1e11 else value
    if isinstance(value, str):
        try:
            return datetime.datetime.fromisoformat(value.replace('Z', '+00:00')).timestamp()
        except ValueError:
            return None
    return None


def native_activity(path, expected_id=None, *, exported=False, evidence_dir=None, archive_member=None):
    result = {'path': str(path), 'available': False}
    try:
        info = path.stat()
        with path.open('rb') as stream:
            header_bytes = stream.readline()
            header = json.loads(header_bytes)
            if expected_id and header.get('id') != expected_id:
                raise ValueError('native header identity differs from physical session')
            start = max(0, info.st_size - 1024 * 1024)
            stream.seek(start)
            data = stream.read()
        if evidence_dir is not None:
            evidence_dir = Path(evidence_dir)
            evidence_dir.mkdir(parents=True, exist_ok=True)
            (evidence_dir / 'header.jsonl').write_bytes(header_bytes)
            (evidence_dir / 'tail.raw').write_bytes(data)
            metadata = {'coverage': 'native-header-and-tail-window', 'complete_native': False,
                        'source': archive_member or str(path), 'source_bytes': info.st_size,
                        'offset': start, 'captured_bytes': len(data), 'header_bytes': len(header_bytes),
                        'partial_first_line': bool(start),
                        'partial_last_line': bool(data and not data.endswith(b'\n'))}
            (evidence_dir / 'source.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + '\n')
            result.update(path=str(evidence_dir / 'source.json'), retained_evidence=metadata,
                          required_reads=[str(evidence_dir / name) for name in ('source.json', 'header.jsonl', 'tail.raw')])
        if start:
            data = data.partition(b'\n')[2]
        lines = data.split(b'\n')[:-1]
        stamps, pending, errors = [], {}, []
        for line in lines:
            if not line:
                continue
            try:
                entry = json.loads(line)
                stamp = epoch(entry.get('timestamp'))
                if stamp is not None:
                    stamps.append(stamp)
                message = entry.get('message') or {}
                if message.get('role') == 'toolResult':
                    pending.pop(message.get('toolCallId'), None)
                for part in message.get('content', []) if isinstance(message.get('content'), list) else []:
                    if part.get('type') == 'toolCall':
                        pending[part.get('id')] = part.get('name')
            except (ValueError, TypeError, AttributeError) as error:
                errors.append(str(error))
        result.update(available=True, native_id=header.get('id'), bytes=info.st_size,
                      mtime=None if exported else info.st_mtime,
                      last_event_at=max(stamps, default=None),
                      pending_tools=list(pending.values()), tail_truncated=bool(start),
                      partial_last_line=bool(data and not data.endswith(b'\n')),
                      parse_errors=errors[:3])
    except (OSError, ValueError) as error:
        result['error'] = f'{type(error).__name__}: {error}'
        if isinstance(error, FileNotFoundError):
            result['source_absent'] = True
            result['expected_source'] = archive_member or str(path)
    return result


def collect_provider_evidence(state_root, observed_at, boundary=None, *, exported=False, evidence_root=None, source_root=None):
    """A SQLite backup includes the matching WAL in one read snapshot; originals stay intact."""
    state_root = Path(state_root)
    evidence_root = Path(evidence_root) if evidence_root is not None else None
    required_reads = []
    if evidence_root is not None:
        evidence_root.mkdir(parents=True, exist_ok=True)
        result_source = evidence_root
    else:
        result_source = state_root
    result = {'observed_at': observed_at, 'boundary': boundary, 'source': str(result_source),
              'sessions': [], 'errors': [], 'exported': exported}
    status_path = state_root / 'status.json'
    physical, health = [], {}
    try:
        status = json.loads(status_path.read_text())
        if evidence_root is not None:
            shutil.copy2(status_path, evidence_root / 'status.json')
            required_reads.append(str(evidence_root / 'status.json'))
        physical = status.get('physical_sessions', [])
        health = status.get('provider_health', {})
        result['provider_health'] = health
        result['status_source_mtime'] = None if exported else status_path.stat().st_mtime
    except (OSError, ValueError) as error:
        result['errors'].append(f'{status_path}: {type(error).__name__}: {error}')
    attempt = state_root.parent / 'recovery-attempt.json'
    if attempt.is_file():
        try:
            record = json.loads(attempt.read_text())
            if evidence_root is not None:
                shutil.copy2(attempt, evidence_root.parent / 'recovery-attempt.json')
                required_reads.append(str(evidence_root.parent / 'recovery-attempt.json'))
            result['recovery_attempt'] = record
            stamps = [epoch(record.get(key)) for key in ('started_at', 'created_at', 'started_at_ns', 'created_at_ns')]
            result['boundary'] = max([v for v in [boundary, *stamps] if v is not None], default=None)
        except (OSError, ValueError) as error:
            result['errors'].append(f'{attempt}: {type(error).__name__}: {error}')
    database = state_root / 'braid.sqlite3'
    try:
        source = sqlite3.connect(database.resolve().as_uri() + '?mode=ro', uri=True, timeout=5)
        snapshot = sqlite3.connect(':memory:')
        try:
            deadline = time.monotonic() + 15
            def bounded_backup(_status, _remaining, _total):
                if time.monotonic() > deadline:
                    raise TimeoutError('provider SQLite read snapshot exceeded 15 seconds')
            source.backup(snapshot, pages=256, progress=bounded_backup, sleep=0.05)
            snapshot.row_factory = sqlite3.Row
            providers = [dict(row) for row in snapshot.execute('SELECT * FROM provider_sessions ORDER BY started_at,session_id')]
            turns = [dict(row) for row in snapshot.execute('SELECT * FROM turns ORDER BY started_at,turn_id')]
        finally:
            source.close()
            snapshot.close()
        result['database_consistency'] = 'SQLite read snapshot includes matching DB/WAL; export file-set atomicity is unknown' if exported else 'SQLite read snapshot includes live DB/WAL'
        latest = {}
        for row in providers:
            latest[row['agent_id']] = row
        selected_turns = []
        for row in latest.values():
            if row['lifecycle'] in ('replaced', 'retired'):
                continue
            matches = [p for p in physical if p.get('session_id') == row['provider_session_id']]
            item = {**row, 'physical': matches[-1] if matches else None,
                    'turn': next((t for t in reversed(turns) if t['session_id'] == row['session_id']), None)}
            if item['turn'] is not None:
                selected_turns.append(item['turn'])
            raw = row.get('provider_session_id')
            native = Path(raw or '')
            # Exports retain original absolute identities; only this source's namespace is eligible.
            if exported and raw and '.factory26' in native.parts:
                relative = native.parts[native.parts.index('.factory26') + 1:]
                if relative and relative[0] == state_root.parent.name:
                    native = state_root.parent.joinpath(*relative[1:])
            expected = (item['physical'] or {}).get('native_session_id')
            window = evidence_root.parent / 'native-windows' / hashlib.sha256(str(native).encode()).hexdigest()[:24] if evidence_root is not None else None
            member = str(native.relative_to(source_root)) if source_root is not None and native.is_relative_to(source_root) else str(native)
            item['native'] = native_activity(native, expected, exported=exported, evidence_dir=window, archive_member=member) if raw else {'available': False, 'error': 'native identity absent'}
            required_reads.extend(item['native'].get('required_reads', []))
            result['sessions'].append(item)
        if evidence_root is not None:
            retained = evidence_root / 'provider-rows.json'
            # Keep raw SQLite values selected by the existing latest-provider/last-turn queries.
            def sqlite_value(value):
                if isinstance(value, bytes):
                    import base64
                    return {'sqlite_blob_base64': base64.b64encode(value).decode()}
                raise TypeError('unsupported SQLite row value: ' + type(value).__name__)
            retained.write_text(json.dumps({'source': str(database.relative_to(source_root)) if source_root is not None else str(database),
                'database_consistency': result['database_consistency'], 'provider_selection': 'last row per agent ORDER BY started_at,session_id',
                'turn_selection': 'last matching session ORDER BY started_at,turn_id',
                'providers': list(latest.values()), 'turns': selected_turns}, ensure_ascii=False, indent=2, default=sqlite_value) + '\n')
            required_reads.append(str(retained))
    except (OSError, sqlite3.Error, TimeoutError) as error:
        result['errors'].append(f'{database}: {type(error).__name__}: {error}')
    if evidence_root is not None:
        result['required_reads'] = required_reads
    return result


def assess(observation, previous=None, *, stale_after=1800, min_samples=2):
    now = observation['observed_at']
    previous = previous or {}
    report = {'observed_at': now, 'stale_after_seconds': stale_after, 'minimum_samples': min_samples,
              'semantic_progress': 'unknown', 'sessions': [], 'errors': list(observation.get('errors', [])),
              'phase': observation.get('phase'), 'run_error': observation.get('run_error'),
              'provider_health': observation.get('provider_health', {})}
    if observation.get('observation_error'):
        report['errors'].append(observation['observation_error'])
    phase = str(observation.get('phase', '')).lower()
    terminal = phase in ('passed', 'completed', 'finished', 'failed', 'cancelled', 'canceled', 'interrupted', 'lost')
    if terminal:
        report['classification'] = 'terminal'
    elif phase in ('evaluating', 'finalizing'):
        report['classification'] = 'finalizing'
    elif observation.get('physical_running') is False:
        report['classification'] = 'stopped_finalizing'
    elif observation.get('observation_error'):
        report['classification'] = 'observation_missing'
    elif not observation.get('sessions'):
        report['classification'] = 'observation_missing'
    prior = {row['session_id']: row for row in previous.get('sessions', [])}
    for item in observation.get('sessions', []):
        native = item.get('native') or {}
        turn = item.get('turn') or {}
        lifecycle = item.get('lifecycle', 'unknown')
        activity = max([v for v in [epoch(item.get('started_at')), epoch(item.get('last_resumed_at')),
                                   native.get('last_event_at')] if v is not None], default=None)
        boundary = observation.get('boundary')
        attempt_activity = max([v for v in [activity, epoch(item.get('last_resume_failed_at')),
                                           epoch(turn.get('last_deferred_at'))] if v is not None], default=None)
        current = boundary is not None and attempt_activity is not None and attempt_activity >= boundary
        signature = {key: item.get(key) for key in ('session_id', 'provider_session_id', 'lifecycle', 'resume_count', 'last_resumed_at', 'last_resume_error')}
        signature['boundary'] = boundary
        signature.update(native={key: native.get(key) for key in ('native_id', 'bytes', 'last_event_at', 'mtime')},
                         turn={key: turn.get(key) for key in ('turn_id', 'lifecycle', 'ended_at', 'error', 'deferred_reason')})
        fingerprint = hashlib.sha256(json.dumps(signature, sort_keys=True).encode()).hexdigest()
        old = prior.get(item['session_id'], {})
        consecutive = old.get('fingerprint') == fingerprint and old.get('current_attempt') and current
        since = old.get('unchanged_since', now) if consecutive else now
        samples = old.get('unchanged_samples', 0) + 1 if consecutive else 1
        reason = item.get('last_resume_error') or turn.get('deferred_reason') or turn.get('error')
        state = 'active'
        if not current:
            state = 'historical_or_unknown'
        elif reason and reason.startswith((
                'session waiting for resources:', 'provider waiting for resources:',
                'session deferred input: resource pressure:', 'resource pressure:')):
            state = 'resource_wait'
        elif lifecycle in ('failed', 'unavailable', 'blocked'):
            state = 'provider_failed' if lifecycle == 'failed' else 'provider_unavailable'
        elif lifecycle in ('sleeping', 'idle') and turn.get('lifecycle') not in ('starting', 'running'):
            state = lifecycle
        elif lifecycle in ('running', 'starting', 'stopping', 'reset_pending', 'unknown') or turn.get('lifecycle') in ('starting', 'running'):
            if now - since >= stale_after and samples >= min_samples:
                state = 'suspected_stale' if native.get('available') else 'observation_missing'
                if state == 'observation_missing':
                    reason = native.get('error') or 'current provider native evidence unavailable'
            elif lifecycle in ('idle', 'sleeping', 'unknown') or not native.get('available'):
                state = 'activity_unknown'
        else:
            state = 'activity_unknown'
        # An unmatched historical tool call does not prove a tool is still executing.
        report['sessions'].append({'session_id': item['session_id'], 'agent_id': item.get('agent_id'),
            'provider_session_id': item.get('provider_session_id'), 'lifecycle': lifecycle,
            'classification': state, 'current_attempt': current, 'boundary': boundary,
            'last_activity_at': activity, 'fingerprint': fingerprint, 'unchanged_since': since,
            'unchanged_samples': samples, 'unchanged_seconds': max(0, now - since),
            'native': native, 'turn': turn, 'reason': reason,
            'tool_liveness': 'unknown' if native.get('pending_tools') else 'not_observed'})
    if 'classification' not in report:
        priority = ('provider_failed', 'provider_unavailable', 'observation_missing', 'suspected_stale', 'activity_unknown', 'resource_wait', 'active', 'sleeping', 'idle', 'historical_or_unknown')
        states = {item['classification'] for item in report['sessions']}
        report['classification'] = next((state for state in priority if state in states), 'observation_missing')
    waiting_groups = [key for key, health in report['provider_health'].items()
                      if isinstance(health, dict) and health.get('waiting_for_resources') is True]
    report['resource_wait_groups'] = waiting_groups
    report['group_errors'] = {key: health['error'] for key, health in report['provider_health'].items()
                              if isinstance(health, dict) and health.get('error') and not health.get('waiting_for_resources')}
    if report['group_errors'] and report['classification'] not in ('terminal', 'finalizing', 'stopped_finalizing') and not observation.get('observation_error') and not report['errors']:
        report['classification'] = 'provider_unavailable'
    if waiting_groups and report['classification'] in ('observation_missing', 'historical_or_unknown', 'idle', 'sleeping') and not observation.get('observation_error') and not report['errors'] and not any(row['classification'] == 'observation_missing' for row in report['sessions']):
        report['classification'] = 'resource_wait'
    return report


def transition(run_id, report, saved):
    """Return one notification on a fault/terminal change or recovery, never per poll."""
    faults = ('observation_missing', 'provider_failed', 'provider_unavailable', 'suspected_stale', 'stopped_finalizing')
    signature = {'classification': report['classification'], 'errors': report['errors'], 'run_error': report['run_error'],
                 'group_errors': report.get('group_errors'),
                 'faults': [(r['session_id'], r['classification'], r['reason'], r['native'].get('error')) for r in report['sessions'] if r['classification'] in faults]}
    # Batch export prefixes vary while the underlying relative evidence error stays the same.
    encoded = re.sub(r'[^\s\"\']*/monitor/\d{8}T\d{6}(?:\.\d+)?Z/', '<batch>/',
                     json.dumps(signature, sort_keys=True))
    key = hashlib.sha256(encoded.encode()).hexdigest()
    old = saved.get(run_id, {})
    saved[run_id] = {'key': key, 'classification': report['classification']}
    if old.get('key') == key:
        return None
    if report['classification'] in (*faults, 'terminal') or old.get('classification') in faults:
        return {'run_id': run_id, 'previous': old.get('classification'), 'classification': report['classification'],
                'evidence': report, 'semantic_progress': 'unknown'}
    return None
