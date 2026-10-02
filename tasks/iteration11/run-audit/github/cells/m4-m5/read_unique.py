import hashlib
import json
import pathlib
import re
import sys

from read_view import content_parts, records

HERE = pathlib.Path(__file__).resolve().parent
receipt = json.loads((HERE / 'read-receipts.json').read_text())
unit_index = int(sys.argv[1])
start_record = int(sys.argv[2])
max_chars = int(sys.argv[3]) if len(sys.argv) > 3 else 40000
units = receipt['units']
seen = {}
for previous in units[:unit_index]:
    if previous.get('unread') is not None:
        continue
    for number, source, data in records(previous['view']):
        role = data.get('message', {}).get('role') or data.get('type') or 'other'
        content = '\n'.join(content_parts(data.get('message', {}).get('content', data.get('text', ''))))
        if content:
            seen[(role, hashlib.sha256(content.encode()).hexdigest())] = (previous['id'], number)

used = 0
next_record = None
for number, source, data in records(units[unit_index]['view']):
    if number < start_record:
        continue
    role = data.get('message', {}).get('role') or data.get('type') or 'other'
    content = '\n'.join(content_parts(data.get('message', {}).get('content', data.get('text', ''))))
    stamp = data.get('timestamp', '')
    prior = seen.get((role, hashlib.sha256(content.encode()).hexdigest())) if content else None
    body = f'\n### Record {number} {stamp} {role}\nSOURCE {pathlib.Path(source).name}\n'
    if prior:
        body += f'EXACT DUPLICATE of {prior[0]} record {prior[1]}\n'
    else:
        content = content.replace('Valid-password-123!', '[redacted test password]')
        content = re.sub(r'(?i)(api[_ -]?key\s*[:=]\s*)[^\s,;]+', r'\1[redacted]', content)
        body += content + '\n'
    if used and used + len(body) > max_chars:
        next_record = number
        break
    print(body)
    used += len(body)
print(f'\nCHUNK chars={used} NEXT_RECORD={next_record or "DONE"}')
