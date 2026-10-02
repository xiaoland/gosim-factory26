import pathlib,re,json,hashlib
base=pathlib.Path('tasks/iteration10/run-audit/github')
out=base/'cells/late-workers'
for n in (28,31,35,37,38):
 s=(base/f'evidence/session-{n}.txt').read_text()
 chunks=re.split(r'(?=\n\[\d+ raw:L\d+ )',s)
 lines=[]
 def view(t,limit=4000):
  if len(t)<=limit:return t
  return t[:1200]+f'\n[省略机械/重复长块 chars={len(t)} sha256={hashlib.sha256(t.encode()).hexdigest()}]\n'+t[-700:]
 for ch in chunks:
  m=re.match(r'\s*\[(\d+) raw:L(\d+) ([^ ]+) ([^]]+)\]\n(.*)',ch,re.S)
  if not m:continue
  k,raw,ts,desc,payload=m.groups()
  lines.append(f'\n### {k} L{raw} {ts} {desc}')
  try:o=json.loads(payload.strip())
  except Exception as e:lines.append(f'PARSE ERROR {e}');continue
  typ=o.get('type')
  if typ=='message' or 'role' in o:
   for c in o.get('message',{}).get('content',[]) if 'message' in o else o.get('content',[]):
    ct=c.get('type')
    if ct=='thinking':lines.append('THINK '+view(c.get('thinking',''),120000))
    elif ct=='text':
     t=c.get('text','')
     lines.append('TEXT '+view(t,5500 if o.get('role')=='toolResult' else 9000))
    elif ct=='toolCall':lines.append('CALL '+c.get('name','')+' '+view(json.dumps(c.get('arguments',{}),ensure_ascii=False),2000))
   if 'usage' in o:lines.append('USAGE '+json.dumps(o['usage'],ensure_ascii=False))
  elif typ=='custom_message':lines.append('CUSTOM '+view(json.dumps(o,ensure_ascii=False),3000))
  else:lines.append(view(json.dumps(o,ensure_ascii=False),3000))
 (out/f'chain{n}.txt').write_text('\n'.join(lines))
 print(n,len(chunks)-1,len('\n'.join(lines)))
