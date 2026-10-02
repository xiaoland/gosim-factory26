import pathlib,json,subprocess,shlex
B=pathlib.Path(__file__).parent
r=json.loads((B.parent/'source-manifest.json').read_text())
roots=list(dict.fromkeys(str(pathlib.Path(x).parent.parent) for e in r['execution_records'] if e['task']=='sheet' for x in e['braid_databases']))
known=[x['key'] for x in json.loads((B/'record-sources.json').read_text())]
script='''import pathlib,json,re,hashlib,collections
ROOTS=ROOTS_LITERAL
KNOWN=set(tuple(x) for x in KNOWN_LITERAL)
stats=[];fresh={}
for root in ROOTS:
 b=pathlib.Path(root);sj=b/'braid-state/sessions.json'
 ss=json.loads(sj.read_text()) if sj.exists() else []
 mapping={pathlib.Path(s.get('native_session_path','')).name:s.get('native_session_id') for s in ss}
 dirs=[b/'native',b/'work/native-homes']+list(b.glob('*native*'))
 files=sorted(set(p for d in dirs if d.is_dir() for p in d.glob('**/*.jsonl')))
 keys=set();unknown=0
 for p in files:
  rows=[]
  for n,l in enumerate(p.read_text(errors='replace').splitlines(),1):
   try:rows.append((n,json.loads(l)))
   except:pass
  h=next((v for _,v in rows if v.get('type')=='session'),{})
  sid=h.get('id') or mapping.get(p.name)
  if not sid:
   m=re.search(r'_([0-9a-f-]{36})\\.jsonl$',p.name);sid=m.group(1) if m else None
  if not sid:unknown+=1;continue
  for n,v in rows:
   k=(sid,v.get('id') or hashlib.sha256(json.dumps(v,sort_keys=True).encode()).hexdigest(),v.get('timestamp'));keys.add(k)
   if k not in KNOWN:fresh.setdefault(k,{'key':k,'record':v,'sources':[]})['sources'].append([str(p),n])
 stats.append({'root':root,'files':len(files),'unique_records':len(keys),'unique_not_main':len(keys-KNOWN),'unmapped_files':unknown})
print(json.dumps({'roots':stats,'fresh':list(fresh.values())},ensure_ascii=False))
'''.replace('ROOTS_LITERAL',repr(roots)).replace('KNOWN_LITERAL',repr(known))
out=subprocess.run(['ssh','wsl.win-ws.localhost','python3 -'],input=script,text=True,capture_output=True,check=True)
data=json.loads(out.stdout);(B/'early-reconciliation.json').write_text(json.dumps(data,ensure_ascii=False,indent=2));print(json.dumps({'roots':data['roots'],'fresh_records':len(data['fresh'])},indent=2))
