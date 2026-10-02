import sys
from read_view import records, content_parts

view, record_s, offset_s, length_s = sys.argv[1:5]
record = int(record_s)
offset = int(offset_s)
length = int(length_s)
for number, source, data in records(view):
    if number != record:
        continue
    content = '\n'.join(content_parts(data.get('message', {}).get('content', data.get('text', ''))))
    print(f'{view} record {number}, source {source}, role {data.get("message", {}).get("role")}, len {len(content)}, chars [{offset},{min(offset + length, len(content))})')
    print(content[offset:offset + length])
    break
