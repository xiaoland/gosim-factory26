import json
import pathlib
import re
import sys

base = pathlib.Path(__file__).parents[2]
outdir = pathlib.Path(__file__).parent
manifest = json.loads((base / 'manifest.json').read_text())
sources = json.loads((base / 'record-sources.json').read_text())
read_indices = json.loads((base / 'semantic-coverage-index.json').read_text())['decision_read_session_indices']
read_sids = {manifest[i]['sid'] for i in read_indices}
cache = {}
known = {}
known_bodies = []


def record(path, line):
    if path not in cache:
        cache[path] = [json.loads(s) for s in (base / 'evidence' / path).read_text().splitlines()]
    return cache[path][line - 1]


def remember(value, loc):
    for para in re.split(r'\n\s*\n', value):
        if len(para) > 150:
            known.setdefault(para, loc)


for entry in sources:
    if entry['key'][0] not in read_sids:
        continue
    path, line = entry['sources'][0]
    obj = record(path, line)
    for part in obj.get('message', {}).get('content', []):
        if part.get('type') in ('text', 'thinking'):
            remember(part.get(part['type'], ''), f'{path}:L{line}')

for name in ('local_items.json', 'local_comments.json'):
    for item in json.loads((base / 'evidence' / name).read_text()):
        body = item.get('body') or ''
        loc = f'{name}:{item.get("node_id", item.get("comment_id"))}'
        remember(body, loc)
        if len(body) > 80:
            known_bodies.append((body, loc))
known_bodies.sort(key=lambda item: -len(item[0]))


def known_text(value):
    for body, loc in known_bodies:
        value = value.replace(body, f'[EXACT PREVIOUSLY READ BODY: {loc}; {len(body)} chars]')
    fragments = re.split(r'(\n\s*\n)', value)
    return ''.join(
        f'[EXACT PREVIOUSLY READ: {known[p]}; {len(p)} chars]' if p in known else p
        for p in fragments
    )


for index in range(231, 263):
    if index == 256 or manifest[index].get('read', '').startswith('语义已读全部'):
        continue
    sid = manifest[index]['sid']
    lines = []
    omissions = []
    entries = [x for x in sources if x['key'][0] == sid]
    entries.sort(key=lambda x: x['key'][2])
    for entry in entries:
        path, n = entry['sources'][0]
        obj = record(path, n)
        loc = f'{path}:L{n}'
        lines.append(f'\n## {obj.get("timestamp")} {obj.get("type")} {loc}')
        msg = obj.get('message')
        if not msg:
            lines.append(known_text(json.dumps(obj, ensure_ascii=False)))
            continue
        lines.append(f'ROLE {msg.get("role")} TOOL {msg.get("toolName", "")}')
        for j, part in enumerate(msg.get('content', [])):
            typ = part.get('type')
            if typ in ('text', 'thinking'):
                value = part.get(typ, '')
                if msg.get('role') == 'user' and value.startswith('Braid refreshed your local working memory.') and '\n\n请处理' in value:
                    at = value.rfind('\n\n请处理')
                    omissions.append(dict(source=loc, part=j, kind='items_projection_already_read', chars=at, note='Issue/PR/comment body previously fully read in items.md; trailing new update retained'))
                    value = value[:350] + f'\n[EXISTING ITEMS PROJECTION OMITTED: {at - 350} chars; items.md previously read]\n' + value[at:]
                lines.append(f'{typ}: {known_text(value)}')
            elif typ == 'image':
                omissions.append(dict(source=loc, part=j, kind='image', chars=len(part.get('data', ''))))
                lines.append(f'IMAGE BINARY OMITTED; {len(part.get("data", ""))} chars')
            elif typ == 'toolCall':
                args = part.get('arguments', {}).copy()
                target = str(args.get('path', ''))
                if part.get('name') in ('write', 'edit') and target.endswith(('.ts', '.tsx', '.js', '.mjs', '.css', '.json', '.html', '.md')):
                    for key in ('content', 'oldText', 'newText'):
                        if key in args and len(str(args[key])) > 1000:
                            omissions.append(dict(source=loc, part=j, kind='mechanical_write', path=target, field=key, chars=len(str(args[key]))))
                            args[key] = f'[MECHANICAL WRITE OMITTED; {len(str(args[key]))} chars]'
                lines.append(f'toolCall {part.get("name")} {known_text(json.dumps(args, ensure_ascii=False))}')
            else:
                lines.append(known_text(json.dumps(part, ensure_ascii=False)))
        for key in ('stopReason', 'isError', 'errorMessage'):
            if key in msg:
                lines.append(f'{key}: {msg[key]}')
    (outdir / f'session-{index:03}.md').write_text('\n'.join(lines))
    (outdir / f'session-{index:03}-omissions.json').write_text(json.dumps(omissions, ensure_ascii=False, indent=2))
    print(index, sid, len(entries), len('\n'.join(lines)), len(omissions))
