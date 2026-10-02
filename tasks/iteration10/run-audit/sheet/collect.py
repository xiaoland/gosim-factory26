import json,pathlib,hashlib,re,collections
B=pathlib.Path(__file__).parent; E=B/'evidence'; O=B/'readable';O.mkdir(exist_ok=True)
sessions=json.loads((E/'braid-state/sessions.json').read_text()); bypath={s.get('native_session_path',''):s for s in sessions}
records={}; sources=collections.defaultdict(list); parse=[]; excluded=[]
for p in sorted(E.glob('**/*.jsonl')):
 if p.name=='pi-timing.jsonl' or p.name=='run-history.jsonl':continue
 rows=[]
 for n,line in enumerate(p.read_text(errors='replace').splitlines(),1):
  try: rows.append((n,json.loads(line)))
  except Exception:parse.append([str(p),n])
 header=next((r for _,r in rows if r.get('type')=='session'),{})
 sid=header.get('id'); orig='/workspace/template/.factory26/20260928-025746-66feadac/'+str(p.relative_to(E))
 mapped=bypath.get(orig,{})
 if not sid:sid=mapped.get('native_session_id')
 if not sid:
  m=re.search(r'_([0-9a-f-]{36})\.jsonl$',p.name);sid=m.group(1) if m else None
 if not sid:
  # transcript artifacts are response event streams, retain but do not count as native session
  excluded.append({'path':str(p.relative_to(E)),'rows':len(rows),'types':dict(collections.Counter(r.get('type') for _,r in rows))});continue
 for n,r in rows:
  key=(sid,r.get('id'),r.get('timestamp'))
  if not r.get('id'):key=(sid,hashlib.sha256(json.dumps(r,sort_keys=True).encode()).hexdigest(),r.get('timestamp'))
  sources[key].append([str(p.relative_to(E)),n]);records[key]=r
manifest=[];blocks={};noise=[]
def scrub(x,loc):
 if isinstance(x,dict):
  return {k:('[BINARY OMITTED '+str(len(str(v)))+' chars]' if k in ('data','thinkingSignature') and isinstance(v,str) and len(v)>200 else scrub(v,loc)) for k,v in x.items()}
 if isinstance(x,list):return [scrub(v,loc) for v in x]
 if isinstance(x,str) and len(x)>600:
  h=hashlib.sha256(x.encode()).hexdigest()
  if h in blocks:return '[EXACT REPEAT '+blocks[h]+']'
  blocks[h]=loc
 return x
for sid in sorted(set(k[0] for k in records),key=lambda s:min(str(k[2]) for k in records if k[0]==s)):
 rr=sorted([(k,r) for k,r in records.items() if k[0]==sid],key=lambda x:str(x[0][2]))
 m={'sid':sid,'records':len(rr),'sources':sorted(set(a[0] for k,r in rr for a in sources[k])),'start':rr[0][0][2],'end':rr[-1][0][2],'types':dict(collections.Counter(r.get('type') for k,r in rr)),'read':'未读'}
 text=[];usage=collections.Counter()
 for k,r in rr:
  src=sources[k][0]; loc=f'{sid}:{src[0]}:L{src[1]}'
  text.append(f'\n### {r.get("timestamp")} {r.get("id")} {r.get("type")} SOURCE {src[0]}:{src[1]}')
  if r.get('type')=='message':
   msg=r['message'];usage.update({a:b for a,b in msg.get('usage',{}).items() if isinstance(b,(int,float))});txt=scrub(msg,loc)
  else:txt=scrub(r,loc)
  text.append(json.dumps(txt,ensure_ascii=False,indent=1))
 m['usage']=dict(usage); data='\n'.join(text); m['chars']=len(data);(O/(sid+'.md')).write_text(data);manifest.append(m)
(B/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2));(B/'record-sources.json').write_text(json.dumps([{'key':k,'sources':v} for k,v in sources.items()],ensure_ascii=False));(B/'excluded-streams.json').write_text(json.dumps(excluded,indent=2));print('sessions',len(manifest),'records',len(records),'chars',sum(m['chars'] for m in manifest),'parse errors',parse,'excluded',len(excluded));print('\n'.join(f'{i:03} {m["sid"]} {m["start"]} {m["records"]} {m["chars"]}' for i,m in enumerate(manifest)))
