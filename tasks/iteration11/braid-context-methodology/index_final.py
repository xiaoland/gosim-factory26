import json,hashlib,pathlib,collections,sqlite3,re
B=pathlib.Path(__file__).parent
E=pathlib.Path('runs/analysis/braid-context-methodology/github-final-20260930/extracted/evidence')
A=pathlib.Path('tasks/iteration11/run-audit/github')
def sig(d):
 content=d.get('message',d.get('data',d))
 return str(d.get('id',''))+'|'+str(d.get('timestamp',''))+'|'+str(d.get('type',''))+'|'+hashlib.sha256(json.dumps(content,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
old=set()
for root in [A/'snapshot-01/work/native-homes',A/'snapshot-02/work/native-homes']:
 for f in root.rglob('*.jsonl'):
  for l in f.open():
   try:old.add(sig(json.loads(l)))
   except json.JSONDecodeError: pass
units={};files=[]
for root in [E/'work/native-homes',E/'native']:
 for f in sorted(root.rglob('*.jsonl')):
  info={'path':str(f),'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'records':0,'unique_added':0,'previously_audited_rows':0}
  for n,l in enumerate(f.open(),1):
   try:d=json.loads(l)
   except json.JSONDecodeError:continue
   s=sig(d);info['records']+=1
   if s in old:info['previously_audited_rows']+=1
   src={'path':str(f),'line':n}
   if s in units:units[s]['sources'].append(src);continue
   units[s]={'id':d.get('id'),'timestamp':d.get('timestamp'),'type':d.get('type'),'content_hash':s.rsplit('|',1)[1],'sources':[src],'prior_read':s in old};info['unique_added']+=1
  files.append(info)
segments={'early':[],'0826-1445':[],'1445-1709':[],'after1709-final':[],'untimed':[]}
for k,r in units.items():
 t=r.get('timestamp') or ''
 if not t:seg='untimed'
 elif t<'2026-09-29T08:26:13':seg='early'
 elif t<'2026-09-29T14:45:00':seg='0826-1445'
 elif t<'2026-09-29T17:10:00':seg='1445-1709'
 else:seg='after1709-final'
 r['segment']=seg;segments[seg].append(r)
summary={k:{'unique_records':len(v),'prior_audit_records':sum(r['prior_read'] for r in v),'new_records':sum(not r['prior_read'] for r in v),'files':len(set(s['path'] for r in v for s in r['sources']))} for k,v in segments.items()}
(B/'final-message-index.json').write_text(json.dumps({'source':str(E),'dedup_key':'message/custom id + timestamp + type + canonical content hash; paths retained, basename not identity','prior_source':'snapshot01+02 native-homes all rows; reused full substantive audit exceptions per coverage.json','summary':summary,'files':files,'messages':list(units.values())},ensure_ascii=False,indent=2)+'\n')
print(json.dumps(summary,ensure_ascii=False,indent=2))
# compact chronology of new middle records; skip only implementation payload, never thinking/control/feedback.
rows=sorted(segments['0826-1445'],key=lambda r:(r['timestamp'] or '',r['id'] or ''))
output=[];ledger=[]
for r in rows:
 if r['prior_read']:continue
 s=r['sources'][0];d=json.loads(pathlib.Path(s['path']).read_text().splitlines()[s['line']-1])
 # save source references for a bounded section per record, all thought/text retained.
 m=d.get('message',{});parts=[]
 for x in m.get('content',[]) if isinstance(m.get('content',[]),list) else []:
  typ=x.get('type')
  if typ in ['thinking','text']:
   t=x.get('thinking',x.get('text',''));parts.append((typ,t))
  elif typ=='toolCall':parts.append(('toolCall',json.dumps({'name':x.get('name'),'arguments':x.get('arguments')},ensure_ascii=False)))
 if not parts and d.get('type') not in ('message','session','model_change','thinking_level_change'):parts=[('custom',json.dumps(d,ensure_ascii=False))]
 header=f"\n### {r['timestamp']} {r['id']} {r['type']} {m.get('role','')}\n{s['path']}:{s['line']}\n"
 output.append(header)
 for typ,t in parts:
  # projection boundaries are explicit; raw record always linked.
  if len(t)>12000 and (m.get('role')=='toolResult' or typ=='toolCall'):
   output.append(f'[{typ} large {len(t)} chars; ORIGINAL LINKED; requires classify/read separately]\n'+t[:900]+'\n[... index omission ...]\n'+t[-300:]+'\n')
   ledger.append({'id':r['id'],'source':s,'type':typ,'chars':len(t),'status':'large block requires semantic classification'})
  else:output.append(f'[{typ}]\n{t}\n')
text=''.join(output);(B/'middle-chronology.txt').write_text(text)
(B/'middle-large-blocks.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
print('middle projection',len(rows),'records',len(text),'chars',len(ledger),'large blocks')
