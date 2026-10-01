import json
import pathlib
import re

SRC = pathlib.Path(__file__).resolve().parents[2]
OUT = pathlib.Path(__file__).resolve().parent
manifest = json.loads((SRC / 'manifest.json').read_text())
index = json.loads((SRC / 'record-sources.json').read_text())
done = json.loads((SRC / 'semantic-coverage-index.json').read_text())['decision_read_session_indices']
known_sids = {manifest[i]['sid'] for i in done}
cache = {}
seen = {}


def source(entry):
    path, line = entry['sources'][0]
    if path not in cache:
        cache[path] = [json.loads(x) for x in (SRC / 'evidence' / path).read_text().splitlines()]
    return cache[path][line - 1], f'evidence/{path}:L{line}'


def remember(text, location):
    for para in re.split(r'\n\s*\n', text):
        if len(para) > 150:
            seen.setdefault(para, location)


for entry in index:
    if entry['key'][0] not in known_sids:
        continue
    record, location = source(entry)
    for part in record.get('message', {}).get('content', []):
        if part.get('type') in ('text', 'thinking'):
            remember(part.get(part['type'], ''), location)
    if record.get('type') == 'custom_message':
        remember(str(record.get('content', '')), location)
for name in ('local_items.json', 'local_comments.json'):
    for item in json.loads((SRC / 'evidence' / name).read_text()):
        remember(item.get('body') or '', f'items.md {item.get("node_id", item.get("comment_id"))}')


def render_text(text, location):
    chunks = []
    for para in re.split(r'(\n\s*\n)', text):
        if para in seen:
            chunks.append(f'[EXACT REPEAT {len(para)} chars, first {seen[para]}]')
        else:
            chunks.append(para)
            remember(para, location)
    return ''.join(chunks)


for idx in range(113, 170):
    sid = manifest[idx]['sid']
    entries = sorted((e for e in index if e['key'][0] == sid), key=lambda e: str(e['key'][2]))
    rendered = []
    omissions = []
    for entry in entries:
        record, location = source(entry)
        rendered.append(f'\n## {record.get("timestamp")} {record.get("type")} {location}')
        if record.get('type') != 'message':
            rendered.append(render_text(json.dumps(record, ensure_ascii=False), location))
            continue
        message = record['message']
        rendered.append(f'ROLE {message.get("role", "")} {message.get("toolName", "")}')
        for part_no, part in enumerate(message.get('content', [])):
            kind = part.get('type')
            if kind in ('text', 'thinking'):
                value = part.get(kind, '')
                if (kind == 'text' and message.get('role') == 'user'
                        and '# Local Issue:' in value and '## Comments' in value
                        and '\n\n请处理 Issue' in value):
                    head, tail = value.rsplit('\n\n请处理 Issue', 1)
                    omissions.append([location, part_no, 'Issue/PR snapshot already read in items.md', len(head)])
                    value = f'[WORK ITEM SNAPSHOT REFERENCED: items.md; {len(head)} chars; {location}]\n\n请处理 Issue' + tail
                rendered.append(f'{kind}: {render_text(value, location)}')
            elif kind == 'image':
                omissions.append([location, part_no, 'image data', len(part.get('data', ''))])
                rendered.append(f'IMAGE BINARY OMITTED {len(part.get("data", ""))} chars')
            elif kind == 'toolCall':
                args = part.get('arguments', {}).copy()
                path = args.get('path', '')
                if part.get('name') in ('write', 'edit') and path.endswith(('.ts', '.tsx', '.js', '.mjs')):
                    for field in ('content', 'oldText', 'newText'):
                        if field in args:
                            omissions.append([location, part_no, path, field, len(args[field])])
                            args[field] = '[MECHANICAL CODE OMITTED]'
                rendered.append('toolCall ' + part.get('name', '') + ' ' + render_text(json.dumps(args, ensure_ascii=False), location))
            else:
                rendered.append(render_text(json.dumps(part, ensure_ascii=False), location))
        for field in ('stopReason', 'isError', 'errorMessage'):
            if field in message:
                rendered.append(f'{field}: {message[field]}')
    (OUT / f'session-{idx:03}.md').write_text('\n'.join(rendered))
    (OUT / f'session-{idx:03}-omissions.json').write_text(json.dumps(omissions, ensure_ascii=False, indent=2))
    print(idx, len(entries), len(rendered), len('\n'.join(rendered)), len(omissions))
