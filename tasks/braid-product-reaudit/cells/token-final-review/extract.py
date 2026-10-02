import json, sqlite3, sys
from pathlib import Path
from datetime import datetime, timezone

start = '2026-09-28T09:20:00.180875Z'
base = Path('/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/generation/runs')
out = {'since': start, 'captured': datetime.now(timezone.utc).isoformat(), 'runs': {}}
for root in base.glob('*/workspace/official-generation/template/.factory26/*'):
    label = 'sheet' if 'sheet-' in str(root) else 'github'
    data = {'root': str(root), 'sessions': json.loads((root/'braid-state/sessions.json').read_text()), 'messages': [], 'timing': [], 'schema': {}, 'tables': {}}
    seen = set()
    identities = {Path(s['native_session_path']).name: s['native_session_id'] for s in data['sessions'] if s.get('native_session_path')}
    data['headerless_files'] = []
    data['all_model_usage'] = {}
    for path in sorted((root/'work/native-homes').rglob('*.jsonl')):
        session = identities.get(path.name)
        header_seen = False
        for number, line in enumerate(path.open(), 1):
            try: row = json.loads(line)
            except ValueError: continue
            if row.get('type') == 'session':
                session = row.get('id'); header_seen = True
            if row.get('type') != 'message' or not session: continue
            key = (session, row.get('id'), row.get('timestamp'))
            if key in seen: continue
            seen.add(key)
            usage = row.get('message', {}).get('usage', {})
            if 'input' in usage:
                model = row['message'].get('model', 'unknown')
                total = data['all_model_usage'].setdefault(model, dict(responses=0, input=0, output=0, cacheRead=0, cacheWrite=0, reasoning=0))
                total['responses'] += 1
                for field in ('input', 'output', 'cacheRead', 'cacheWrite', 'reasoning'): total[field] += usage.get(field, 0)
            if row.get('timestamp', '') < start: continue
            data['messages'].append({'session': session, 'path': str(path.relative_to(root)), 'line': number, **row})
        if not header_seen: data['headerless_files'].append({'path': str(path.relative_to(root)), 'mapped_session': session})
    for line in (root/'pi-timing.jsonl').open():
        try: row = json.loads(line)
        except ValueError: continue
        if row.get('at_ms', 0) >= datetime.fromisoformat(start.replace('Z', '+00:00')).timestamp()*1000: data['timing'].append(row)
    conn = sqlite3.connect(f'file:{root}/braid-state/braid.sqlite3?mode=ro', uri=True)
    conn.row_factory = sqlite3.Row
    names = [r[0] for r in conn.execute("select name from sqlite_master where type='table'")]
    for name in names:
        data['schema'][name] = [dict(r) for r in conn.execute(f'pragma table_info("{name}")')]
        if name in ('work_items','comments','assignments','physical_sessions','threads','pull_requests','issues','events','local_items','local_comments','context_resets','provider_sessions','turns','agent_instances','wake_batches'):
            data['tables'][name] = [dict(r) for r in conn.execute(f'select * from "{name}"')]
    out['runs'][label] = data
out['capture_finished'] = datetime.now(timezone.utc).isoformat()
json.dump(out, sys.stdout, ensure_ascii=False)
