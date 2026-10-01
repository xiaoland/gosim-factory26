import hashlib, json, pathlib, re, sys
from read_view import content_parts, records as view_records
ROOT=pathlib.Path('/Volumes/WorkSSD/Development/factory26/tasks/iteration11/run-audit/github')
OWN=[4,5,11,0,8,6,9,1,2,7]
INDEX=json.loads((ROOT/'increment-index.json').read_text())['changed']
READ=json.loads((ROOT/'cells/m4-m5/read-receipts.json').read_text())['units']

def content(o):
 m=o.get('message',{})
 return '\n'.join(content_parts(m.get('content',o.get('text',''))))

def role(o):
 m=o.get('message',{})
 return m.get('role') or o.get('type') or 'other'

def red(s):
 s=s.replace('Valid-password-123!','[redacted test password]')
 s=re.sub(r'(?i)(api[_ -]?key\s*[:=]\s*)[^\s,;]+',r'\1[redacted]',s)
 return s

seen={}
for u in READ:
 for n,source,o in view_records(u['view']):
  c=content(o)
  if c:seen[(role(o),hashlib.sha256(c.encode()).hexdigest())]=(u['id'],n)
rows={}
for i in OWN:
 x=INDEX[i]; p=ROOT/'snapshot-02'/x['path'];q=ROOT/'snapshot-01'/x['path'];prior=sum(1 for _ in q.open()) if q.exists() else 0
 arr=[]
 for n,line in enumerate(p.open(),1):
  if n<=prior: continue
  o=json.loads(line);c=content(o);r=role(o);h=hashlib.sha256(c.encode()).hexdigest() if c else None
  dup=seen.get((r,h)) if h else None
  arr.append((n,o,c,dup))
  if c and not dup: seen[(r,h)]=(f'increment-index:{i}',n)
 rows[i]=arr
if len(sys.argv)==1:
 for i in OWN:
  a=rows[i];print(f'FILE {i}: {len(a)} records {a[0][0]}-{a[-1][0]} unique_chars={sum(len(c) for n,o,c,d in a if not d)} dup={sum(bool(d) for n,o,c,d in a)}')
  for n,o,c,d in a:
   if len(c)>12000: print(f' BIG {n} {role(o)} {len(c)} duplicate={d}')
 sys.exit()
i=int(sys.argv[1]);start=int(sys.argv[2]);end=int(sys.argv[3]);a=rows[i]
for n,o,c,d in a:
 if not start<=n<=end:continue
 m=o.get('message',{});print(f'\n### FILE {i} RECORD {n} {o.get("timestamp","")} {role(o)} {m.get("toolName","")} LENGTH {len(c)}')
 if d:print('EXACT DUPLICATE',d);continue
 if len(sys.argv)>4:
  lo=int(sys.argv[4]);hi=int(sys.argv[5]);print('SLICE',lo,hi,'OF',len(c));print(red(c[lo:hi]))
 else:print(red(c))
