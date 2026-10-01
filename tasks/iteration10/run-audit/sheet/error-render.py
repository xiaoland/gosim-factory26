import json,pathlib,collections,difflib,hashlib
B=pathlib.Path(__file__).parent;M=json.loads((B/'manifest.json').read_text());IX=json.loads((B/'record-sources.json').read_text());rr=collections.defaultdict(list);cache={}
for x in IX:
 p,n=x['sources'][0]
 if p not in cache:cache[p]=[json.loads(z) for z in (B/'evidence'/p).read_text().splitlines()]
 rr[x['key'][0]].append((x,cache[p][n-1]))
known=[]
for fn in ['local_items.json','local_comments.json']:
 for z in json.loads((B/'evidence'/fn).read_text()):
  txt=z.get('body') or ''; label=z.get('node_id', 'comment:'+str(z.get('comment_id')))
  if len(txt)>80:known.append((txt,label))
known.sort(key=lambda z:-len(z[0]))
def omitknown(t):
 for txt,label in known:
  t=t.replace(txt,'[EXACT ALREADY SEMANTICALLY READ items.md '+label+'; '+str(len(txt))+' chars]')
 return t
indices=[v[0] for v in json.loads((B/'error-only-groups.json').read_text()).values()];seen={};out=[]
for i in indices:
 m=M[i];out.append(f'\n# {i} {m["sid"]} {m["start"]}..{m["end"]}')
 for x,r in sorted(rr[m['sid']],key=lambda z:str(z[0]['key'][2])):
  msg=r.get('message');loc=str(x['sources'][0]);
  if not msg:out.append(f'{loc} {r["type"]}: '+json.dumps({k:v for k,v in r.items() if k not in ["timestamp","id","parentId"]},ensure_ascii=False));continue
  if msg['role']=='user':
   txt=omitknown('\n'.join(c.get('text','') for c in msg['content']));key=next((l for l in txt.splitlines() if l.startswith('# Local ')),'other');out.append(loc+' USER')
   if key not in seen:out.append(txt)
   else:
    prev,ploc=seen[key];out.append('EXACT LINE DIFF against '+ploc+' (unchanged lines exact omitted)');out.extend(difflib.unified_diff(prev.splitlines(),txt.splitlines(),n=2))
   seen[key]=(txt,loc)
  else:out.append(loc+' '+str(r.get('timestamp'))+' '+msg['role']+' '+msg.get('stopReason','')+' '+msg.get('errorMessage',''))
(B/'error-sessions-delta.md').write_text('\n'.join(out));print(len('\n'.join(out)),len('\n'.join(out).splitlines()))
