"""Render saved Braid SQLite evidence as a standalone, read-only collaboration browser."""
from pathlib import Path
import hashlib
import json
import sqlite3
import zipfile
from markdown_it import MarkdownIt

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'runs/official-collaboration-review'
md = MarkdownIt('commonmark', {'html': False}).enable('table')
all_data = {}
for task, run in [('github', '435b79927a47'), ('sheet', 'bd7ac1b232ba')]:
    archive = ROOT / f'runs/e20260928-completed-replay/{task}/source-workspace.zip'
    with zipfile.ZipFile(archive) as z:
        entry = next(n for n in z.namelist() if n.endswith('/braid-state/braid.sqlite3'))
        database = OUT / f'{task}.sqlite3'
        database.write_bytes(z.read(entry))
    c = sqlite3.connect(f'file:{database}?mode=ro', uri=True)
    c.row_factory = sqlite3.Row
    def rows(sql): return [dict(r) for r in c.execute(sql)]
    authors = {r['agent_id']: r['member_login'] for r in rows('SELECT ai.agent_id,a.member_login FROM agent_instances ai JOIN assignments a USING(assignment_id)')}
    items = rows('SELECT w.node_id,w.kind,w.number,w.state,w.observed_at,l.* FROM work_items w JOIN local_items l USING(node_id) ORDER BY w.kind,w.number')
    comments = rows('SELECT * FROM local_comments ORDER BY created_at,comment_id')
    for item in items:
        item['html'] = md.render(item['body'] or '')
    for comment in comments:
        comment['author'] = comment['system_author'] or authors.get(comment['writer_group']) or '未知作者'
        comment['html'] = md.render(comment['body'] or '')
    all_data[task] = dict(run=run, archive=str(archive.relative_to(ROOT)), sha256=hashlib.sha256(archive.read_bytes()).hexdigest(), entry=entry,
        items=items, comments=comments, activity=rows('SELECT * FROM local_activity ORDER BY occurred_at,ordinal'),
        links=rows('SELECT * FROM associations'), merges=rows('SELECT * FROM local_merges'),
        reactions=rows('SELECT * FROM local_comment_reactions'), delivery=rows('SELECT * FROM local_comment_delivery'),
        assignments=rows('SELECT a.*,ai.profile_id FROM assignments a JOIN agent_instances ai USING(assignment_id) ORDER BY assigned_at'))
    c.close()
(OUT/'data.json').write_text(json.dumps(all_data, ensure_ascii=False, indent=2))
template = Path(__file__).with_name('template.html').read_text()
(OUT/'index.html').write_text(template.replace('__DATA__', json.dumps(all_data,ensure_ascii=False).replace('<','\\u003c')))
print(OUT/'index.html')
