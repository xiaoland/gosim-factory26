"""Summarize archived Pi usage and callback timings without inferring missing time."""
import argparse
from datetime import datetime
import json
from pathlib import Path
import sys

TOKENS = ('input', 'output', 'cacheRead', 'cacheWrite', 'reasoning')


def _live_native(run, path):
    """Map a container path from this run's own Braid record into the archive."""
    prefix = f'/workspace/template/.factory26/{run.name}/'
    if not isinstance(path, str) or not path.startswith(prefix):
        raise ValueError(f'native path is outside this generation run: {path}')
    source = (run / path[len(prefix):]).resolve()
    if not source.is_relative_to(run):
        raise ValueError(f'native path escapes run: {path}')
    return str(source.relative_to(run))


def _live_sessions(run, events, gaps):
    path = run / 'braid-state/sessions.json'
    if not path.is_file():
        gaps.append('live Braid session list absent: braid-state/sessions.json')
        sessions = []
    else:
        sessions = json.loads(path.read_text())
        if not isinstance(sessions, list):
            raise ValueError('live Braid session list is not an array')
    result = {}
    for session in sessions:
        if session.get('provider') != 'pi' or not session.get('native_session_path'):
            continue
        native_id = session.get('native_session_id')
        if not native_id:
            gaps.append('live Braid session without native_session_id')
            continue
        result[native_id] = {**session,
            'native': _live_native(run, session['native_session_path']),
            'native_id': native_id, 'session_kind': 'braid_member'}
    # Pi sub-agents write callback events too, but do not appear in Braid sessions.json.
    for event in events:
        native_id = event.get('session_id')
        if not native_id or native_id in result or not event.get('session_file'):
            continue
        result[native_id] = {'provider': 'pi', 'native_id': native_id,
            'native': _live_native(run, event['session_file']),
            'session_kind': 'pi_subagent'}
    return list(result.values())


def union_ms(intervals):
    merged = []
    for start, end in sorted(intervals):
        if end < start:
            continue
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return sum(end - start for start, end in merged)


def usage_total(rows):
    result = {'messages': sum(row['messages'] for row in rows),
              'tokens': {}, 'known_messages': {}}
    for field in TOKENS:
        known = sum(row['known_messages'][field] for row in rows)
        result['known_messages'][field] = known
        result['tokens'][field] = (sum(row['tokens'][field] or 0 for row in rows)
                                   if known else None)
    return result


def timing_total(requests, tools):
    completed_requests = [row for row in requests if row['duration_ms'] is not None]
    completed_tools = [row for row in tools if row['duration_ms'] is not None]
    intervals = [(row['start_ms'], row['end_ms']) for row in (*completed_requests, *completed_tools)]
    return {'requests': len(requests), 'completed_requests': len(completed_requests),
            'request_sum_ms': sum(row['duration_ms'] for row in completed_requests) if completed_requests else None,
            'tools': len(tools), 'completed_tools': len(completed_tools),
            'tool_sum_ms': sum(row['duration_ms'] for row in completed_tools) if completed_tools else None,
            'observed_active_union_ms': union_ms(intervals) if intervals else None}


def timestamp_ms(value):
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value.replace('Z', '+00:00')).timestamp() * 1000
    raise ValueError(f'invalid message timestamp: {value!r}')


def profile(run, since_ms=None):
    run = Path(run).resolve(strict=True)
    gaps = []
    events = []
    timing_file = run/'pi-timing.jsonl'
    if timing_file.is_file():
        for number, line in enumerate(timing_file.read_text().splitlines(), 1):
            try:
                events.append(json.loads(line))
            except ValueError as exc:
                gaps.append(f'pi-timing.jsonl:{number}: {exc}')
    manifest_file = run/'native/manifest.json'
    manifest = json.loads(manifest_file.read_text()) if manifest_file.is_file() else {
        'diagnostic_status': 'live-unarchived', 'sessions': []}
    live_ids = set()
    if manifest.get('diagnostic_status') != 'complete':
        indexed = {entry.get('native_id'): entry for entry in manifest.get('sessions', [])}
        for entry in _live_sessions(run, events, gaps):
            if (run/entry['native']).is_file():
                indexed[entry['native_id']] = entry
                live_ids.add(entry['native_id'])
            else:
                gaps.append(f"missing live native session: {entry['native']}")
        manifest['sessions'] = list(indexed.values())
        manifest['diagnostic_status'] = 'live-unarchived'
    groups = {}
    seen = set()
    identities = {}
    for session in manifest.get('sessions', []):
        relative = session.get('native')
        if session.get('provider') != 'pi' or not relative:
            continue
        source = (run/relative).resolve()
        if not source.is_relative_to(run):
            raise ValueError(f'native path escapes run: {relative}')
        native_id = session.get('native_id') or relative
        identities[native_id] = {key: session.get(key) for key in
            ('profile_id', 'work_item_id', 'work_item_kind', 'native_role',
             'native_parent', 'parent_native_session_id', 'group_id', 'association_status',
             'session_kind', 'assignment_generation')}
        identities[native_id]['session_kind'] = (session.get('session_kind') or
            ('pi_subagent' if session.get('parent_native_session_id') else 'braid_member'))
        if not source.is_file():
            gaps.append(f'missing native session: {relative}')
            continue
        sources = [source]
        if native_id in live_ids:
            home = next((parent for parent in source.parents
                         if parent.parent.name == 'native-homes'), source.parent)
            sources = sorted({source, *home.rglob(f'*_{native_id}.jsonl')})
        for native_source in sources:
            for number, line in enumerate(native_source.read_text().splitlines(), 1):
                try:
                    entry = json.loads(line)
                except ValueError as exc:
                    gaps.append(f'{native_source.relative_to(run)}:{number}: {exc}')
                    continue
                message = entry.get('message') if entry.get('type') == 'message' else None
                if not isinstance(message, dict) or message.get('role') != 'assistant':
                    continue
                if since_ms is not None:
                    try:
                        at = timestamp_ms(message.get('timestamp') or entry.get('timestamp'))
                    except ValueError as exc:
                        gaps.append(f'{native_source.relative_to(run)}:{number}: {exc}')
                        continue
                    if at < since_ms:
                        continue
                key = (native_id, entry.get('id') or entry.get('timestamp'))
                if key in seen:
                    continue
                seen.add(key)
                model = message.get('model') or 'unknown'
                provider = message.get('provider') or 'unknown'
                outcome = 'error' if message.get('stopReason') == 'error' or message.get('errorMessage') else 'success'
                usage = message.get('usage') if isinstance(message.get('usage'), dict) else {}
                group_key = (native_id, model, provider, outcome)
                row = groups.setdefault(group_key, {'session_id': native_id, 'model': model,
                    'provider': provider, 'outcome': outcome,
                    'profile_id': session.get('profile_id'), 'work_item_id': session.get('work_item_id'),
                    'messages': 0, 'known_messages': {field: 0 for field in TOKENS},
                    'tokens': {field: None for field in TOKENS}})
                row['messages'] += 1
                for field in TOKENS:
                    amount = usage.get(field)
                    if isinstance(amount, (int, float)) and not isinstance(amount, bool):
                        row['known_messages'][field] += 1
                        row['tokens'][field] = (row['tokens'][field] or 0) + amount

    requests, tools = {}, {}
    for event in events:
        kind = event.get('kind')
        key = event.get('request_id')
        at = event.get('at_ms')
        if not isinstance(at, (int, float)) or isinstance(at, bool):
            gaps.append(f'event without numeric time: {kind}')
            continue
        if key and kind == 'request_start':
            requests[key] = {'request_id': key, 'session_id': event.get('session_id'),
                'model': event.get('model'), 'provider': event.get('provider') or 'unknown',
                'start_ms': at, 'headers_ms': None,
                'first_update_ms': None, 'end_ms': None, 'usage': None}
        elif key in requests:
            row = requests[key]
            if kind == 'response_headers': row['headers_ms'] = at
            elif kind == 'first_update' and row['first_update_ms'] is None: row['first_update_ms'] = at
            elif kind == 'message_end':
                row.update(end_ms=at, usage=event.get('usage'), model=event.get('model') or row['model'])
        tool_key = (event.get('instance_id'), event.get('session_id'), event.get('tool_call_id'))
        if kind == 'tool_start' and tool_key[2]:
            tools[tool_key] = {'session_id': event.get('session_id'), 'tool_name': event.get('tool_name'),
                'tool_call_id': tool_key[2], 'start_ms': at, 'end_ms': None, 'is_error': None}
        elif kind == 'tool_end' and tool_key in tools:
            tools[tool_key].update(end_ms=at, is_error=event.get('is_error'))
    for row in requests.values():
        row['duration_ms'] = (row['end_ms'] - row['start_ms']
            if row['end_ms'] is not None and row['end_ms'] >= row['start_ms'] else None)
        row['time_to_first_update_ms'] = (row['first_update_ms'] - row['start_ms']
            if row['first_update_ms'] is not None and row['first_update_ms'] >= row['start_ms'] else None)
        if row['end_ms'] is not None and row['duration_ms'] is None:
            gaps.append(f'non-monotonic request clock: {row["request_id"]}')
    for row in tools.values():
        row['duration_ms'] = (row['end_ms'] - row['start_ms']
            if row['end_ms'] is not None and row['end_ms'] >= row['start_ms'] else None)
        if row['end_ms'] is not None and row['duration_ms'] is None:
            gaps.append(f'non-monotonic tool clock: {row["tool_call_id"]}')
    crossing_requests = crossing_tools = 0
    if since_ms is not None:
        # Usage is counted by response time; timing covers operations started in the window.
        crossing_requests = sum(row['start_ms'] < since_ms and
            (row['end_ms'] is None or row['end_ms'] >= since_ms) for row in requests.values())
        crossing_tools = sum(row['start_ms'] < since_ms and
            (row['end_ms'] is None or row['end_ms'] >= since_ms) for row in tools.values())
        requests = {key: row for key, row in requests.items() if row['start_ms'] >= since_ms}
        tools = {key: row for key, row in tools.items() if row['start_ms'] >= since_ms}
    usage_rows = list(groups.values())
    request_rows = list(requests.values())
    tool_rows = list(tools.values())
    models = []
    model_keys = {(row['model'], row['provider']) for row in usage_rows}
    model_keys.update((row['model'], row['provider']) for row in request_rows if row['model'])
    for model, provider in sorted(model_keys):
        model_requests = [row for row in request_rows if (row['model'], row['provider']) == (model, provider)]
        model_usage = [row for row in usage_rows if (row['model'], row['provider']) == (model, provider)]
        native_ids = {row['session_id'] for row in (*model_usage, *model_requests)}
        member_ids = {native_id for native_id in native_ids
                      if identities.get(native_id, {}).get('session_kind') == 'braid_member'}
        member_keys = {(identities[native_id]['group_id'], identities[native_id]['assignment_generation'])
                       for native_id in member_ids if identities[native_id].get('group_id') is not None
                       and identities[native_id].get('assignment_generation') is not None}
        unknown_members = sum(identities[native_id].get('group_id') is None or
                              identities[native_id].get('assignment_generation') is None for native_id in member_ids)
        models.append({'model': model, 'provider': provider,
                       'braid_members': len(member_keys) if not unknown_members else None,
                       'unknown_member_identities': unknown_members,
                       'successful_messages': sum(row['messages'] for row in model_usage if row['outcome'] == 'success'),
                       'error_messages': sum(row['messages'] for row in model_usage if row['outcome'] == 'error'),
                       'braid_sessions': len(member_ids),
                       'pi_subagent_sessions': sum(identities.get(native_id, {}).get('session_kind') == 'pi_subagent' for native_id in native_ids),
                       **usage_total(model_usage),
                       **timing_total(model_requests, [])})
    sessions = []
    for native_id in sorted(set(identities) | {row['session_id'] for row in (*request_rows, *tool_rows) if row['session_id']}):
        sessions.append({'session_id': native_id, **identities.get(native_id, {}),
                         **usage_total([row for row in usage_rows if row['session_id'] == native_id]),
                         **timing_total([row for row in request_rows if row['session_id'] == native_id],
                                        [row for row in tool_rows if row['session_id'] == native_id])})
    metadata_file = run/'run.json'
    metadata = json.loads(metadata_file.read_text()) if metadata_file.is_file() else {}
    wall_seconds = metadata.get('generation_seconds')
    wall_ms = wall_seconds * 1000 if since_ms is None and isinstance(wall_seconds, (int, float)) else None
    return {'run': str(run), 'source': 'Pi JSONL + Pi callback events',
            'window': {'since_ms': since_ms, 'usage_basis': 'assistant response timestamp',
                       'timing_basis': 'operation start timestamp',
                       'excluded_crossing_requests': crossing_requests, 'excluded_crossing_tools': crossing_tools},
            'coverage': {'native_manifest': manifest.get('diagnostic_status', 'unknown'),
                         'timing_events': 'present' if timing_file.is_file() else 'absent',
                         'gaps': gaps,
                         'open_requests': sum(row['end_ms'] is None for row in requests.values()),
                         'open_tools': sum(row['end_ms'] is None for row in tools.values())},
            'summary': {'run_wall_ms': wall_ms, 'cost': None,
                        **usage_total(usage_rows), **timing_total(request_rows, tool_rows)},
            'models': models, 'sessions': sessions,
            'usage': sorted(usage_rows, key=lambda row: (row['model'], row['provider'], row['session_id'], row['outcome'])),
            'requests': sorted(request_rows, key=lambda row: row['start_ms']),
            'tools': sorted(tool_rows, key=lambda row: row['start_ms'])}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('generation_run', type=Path, help='the .factory26/<run> directory')
    parser.add_argument('--output', type=Path, help='write machine-readable JSON to a new file')
    parser.add_argument('--since', help='ISO-8601 timestamp with timezone; restrict to recovery/new activity')
    args = parser.parse_args()
    try:
        since = datetime.fromisoformat(args.since.replace('Z', '+00:00')) if args.since else None
        if since is not None and since.tzinfo is None:
            raise ValueError('--since requires an explicit timezone')
        result = json.dumps(profile(args.generation_run, since.timestamp() * 1000 if since else None), ensure_ascii=False, indent=2) + '\n'
        if args.output:
            with args.output.open('x') as stream:
                stream.write(result)
        else:
            print(result, end='')
    except (OSError, ValueError, KeyError) as exc:
        print(f'Pi profile failed: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
