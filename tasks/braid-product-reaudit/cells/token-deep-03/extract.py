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
    for path in sorted((root/'work/native-homes').rglob('*.jsonl')):
        session = None
        for number, line in enumerate(path.open(), 1):
            try: row = json.loads(line)
            except ValueError: continue
            if row.get('type') == 'session': session = row.get('id')
            if row.get('type') != 'message' or not session: continue
            if row.get('timestamp', '') < start: continue
            key = (session, row.get('id'), row.get('timestamp'))
            if key in seen: continue
            seen.add(key)
            data['messages'].append({'session': session, 'path': str(path.relative_to(root)), 'line': number, **row})
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
json.dump(out, sys.stdout, ensure_ascii=False)
