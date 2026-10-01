import pathlib,json,sqlite3,collections,hashlib,re
base=pathlib.Path(__file__).parent; src=base/'snapshot-01'; out=base/'views';out.mkdir(exist_ok=True)
d=sqlite3.connect(src/'braid.sqlite3');d.row_factory=sqlite3.Row
sessions=[dict(r) for r in d.execute('select p.*,a.work_item_node_id from provider_sessions p join agent_instances i using(agent_id) join assignments a using(assignment_id)')]
byhome={pathlib.Path(r['provider_session_id']).parent.name:r for r in sessions}
units={}; files=[]
for f in sorted((src/'work/native-homes').rglob('*.jsonl')):
 rel=f.relative_to(src); home=rel.parts[2]; owner=byhome.get(home,{}).get('work_item_node_id','unknown'); rows=[]
 for n,l in enumerate(f.read_text().splitlines(),1):
  try: r=json.loads(l)
  except: continue
  rows.append((n,r))
 if f.name=='run-history.jsonl': kind='history'; uid=home+'-history'
 elif 'subagent-artifacts' in str(f): kind='transcript'; uid=f.stem
 elif f.name=='session.jsonl': kind='subagent'; uid=next((r['id'] for n,r in rows if r.get('type')=='session'),str(rel.parent).replace('/','_'))
 else: kind='native';uid=f.stem
 u=units.setdefault(uid,dict(id=uid,owner=owner,kind=kind,sources=[],records={}))
 u['sources'].append(str(rel))
 for n,r in rows:
  key=r.get('id') or hashlib.sha256(json.dumps(r,sort_keys=True).encode()).hexdigest()
  if key in u['records'] and u['records'][key]['row'] != r:
   key=key+'-variant-'+hashlib.sha256(json.dumps(r,sort_keys=True).encode()).hexdigest()[:12]
  if key not in u['records']: u['records'][key]=dict(row=r,locations=[])
  u['records'][key]['locations'].append(f'{rel}:{n}')
 files.append(dict(path=str(rel),unit=uid,lines=len(rows),status='indexed'))
# readable JSON preserves all text; suppress only binary image payloads
seen={}; usage=collections.Counter(); responses=set(); modelusage=collections.defaultdict(collections.Counter)
def clean(x):
 if isinstance(x,list): return [clean(a) for a in x]
 if isinstance(x,dict): return {k:('[binary omitted sha256='+hashlib.sha256(str(v).encode()).hexdigest()+']' if k in ['data','image_url'] and len(str(v))>2000 else clean(v)) for k,v in x.items()}
 return x
ledger=[]
for uid,u in units.items():
 rows=sorted(u.pop('records').values(),key=lambda a:a['row'].get('timestamp',''))
 text=[]
 for ix,a in enumerate(rows,1):
  r=a['row']; m=r.get('message',{}); key=r.get('id'); content=clean(r)
  if m.get('role')=='assistant' and 'usage' in m:
   identity=(uid,key) if u['kind']=='native' else ('sub',key, r.get('timestamp'))
   # transcript copies don't count; canonical subagent session used instead
   if u['kind']!='transcript' and identity not in responses:
    responses.add(identity)
    for k,v in m['usage'].items():
     if isinstance(v,(int,float)): usage[k]+=v;modelusage[m.get('model','?')][k]+=v
  rendered=json.dumps(content,ensure_ascii=False,indent=2); h=hashlib.sha256(rendered.encode()).hexdigest()
  if h in seen: rendered='EXACT_DUPLICATE → '+seen[h]
  else: seen[h]=f'{uid} record {ix}'
  text.append(f'## Record {ix}\nSource: '+a['locations'][0]+'\n'+rendered+'\n')
 body='\n'.join(text); (out/(uid+'.txt')).write_text(body)
 ledger.append(dict(**u,records=len(rows),characters=len(body),view='views/'+uid+'.txt',status='indexed',read_ranges=[],truncation_followup=[]))
(base/'coverage.json').write_text(json.dumps(dict(cutoff='snapshot-01/manifest.json',units=ledger,files=files),ensure_ascii=False,indent=2))
for owner in sorted(set(u['owner'] for u in ledger)):
 group=[u for u in ledger if u['owner']==owner];print(owner,len(group),sum(u['characters'] for u in group))
(base/'usage-provisional.json').write_text(json.dumps(dict(total=dict(usage),models={k:dict(v) for k,v in modelusage.items()},responses=len(responses)),indent=2))
# Full work item, comment, action views with stable database ids
for w in d.execute('select w.*,l.title,l.body from work_items w join local_items l using(node_id)'):
 name=w['node_id']; parts=[json.dumps(dict(w),ensure_ascii=False,indent=2)]
 for table,key in [('local_comments','comment_id'),('local_activity','ordinal')]:
  for r in d.execute('select * from '+table+' where work_item_node_id=? order by '+key,(name,)):parts.append(table+' '+json.dumps(dict(r),ensure_ascii=False,indent=2))
 (out/(name.replace(':','-')+'-board.txt')).write_text('\n\n'.join(parts))
print('total units',len(ledger),'responses provisional',len(responses),'usage',dict(usage))
