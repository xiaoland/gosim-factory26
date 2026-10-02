import json
import pathlib
import re
import sys
from read_view import records, ROOT

assignment = json.loads((ROOT / 'cells/m4-m5/assignment.json').read_text())
owner = sys.argv[1]
for entry in assignment:
    if entry['owner'] != owner:
        continue
    print('\nFILE', entry['id'], entry['kind'], entry['records'])
    for n, source, data in records(entry['view']):
        msg = data.get('message', {})
        role = msg.get('role') or data.get('role') or data.get('recordType') or data.get('type')
        parts = []
        for p in msg.get('content', []):
            if not isinstance(p, dict):
                continue
            if p.get('type') == 'text':
                parts.append(p.get('text', ''))
            elif p.get('type') == 'toolCall':
                parts.append('CALL ' + p.get('name', '') + ' ' + json.dumps(p.get('arguments', {}), ensure_ascii=False))
        if data.get('recordType') == 'message' and not parts and data.get('sourceEventType') in ('message_end','initial_prompt'):
            parts = [data.get('text', '')]
        joined = ' | '.join(parts).replace('\n', ' ⏎ ')
        if len(joined) > 600:
            joined = joined[:330] + f' …[len={len(joined)}]… ' + joined[-210:]
        print(n, data.get('timestamp', ''), role, joined, sep='\t')
