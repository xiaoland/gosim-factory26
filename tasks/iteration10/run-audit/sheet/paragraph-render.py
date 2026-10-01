"""Pure read-only rendering; exact paragraphs only; no semantic coverage claims."""
import json,pathlib,hashlib,re,collections
B=pathlib.Path(__file__).parent;E=B/'evidence';O=B/'paragraphs';O.mkdir(exist_ok=True)
sources=json.loads((B/'record-sources.json').read_text());manifest=json.loads((B/'manifest.json').read_text());cache={}; grouped=collections.defaultdict(list)
for x in sources:
 sid=x['key'][0];p,n=x['sources'][0]
 if p not in cache:cache[p]=[json.loads(z) for z in (E/p).read_text().splitlines()]
 grouped[sid].append((str(x['key'][2]),p,n,cache[p][n-1]))
seen={};stat=[]
def render(s,loc):
 if not isinstance(s,str):return json.dumps(s,ensure_ascii=False)
 out=[]
 for i,para in enumerate(re.split(r'(\n\s*\n)',s)):
  if len(para)<160:out.append(para);continue
  h=hashlib.sha256(para.encode()).hexdigest()
  if h in seen:out.append('[EXACT PARAGRAPH REPEAT '+seen[h]+']')
  else:seen[h]=loc+' paragraph '+str(i//2+1);out.append(para)
 return ''.join(out)
for idx,m in enumerate(manifest):
 sid=m['sid'];out=[]
 for t,p,n,r in sorted(grouped[sid]):
  loc=f'{p}:L{n}';out.append(f'\n### {t} {r.get("id")} {r.get("type")} SOURCE {loc}')
  if r.get('type')!='message':out.append(render(json.dumps(r,ensure_ascii=False),loc));continue
  msg=r['message'];out.append('ROLE '+msg.get('role','')+' '+msg.get('toolName',''))
  content=msg.get('content',[])
  if isinstance(content,str):content=[{'type':'text','text':content}]
  for j,c in enumerate(content):
   typ=c.get('type');bl=f'{loc} block{j}'
   if typ in ['text','thinking']:out.append(typ+': '+render(c.get(typ,''),bl))
   elif typ=='image':out.append('IMAGE BINARY OMITTED '+str(len(c.get('data',''))))
   else:out.append(typ+': '+render(json.dumps(c,ensure_ascii=False),bl))
  for k in ['isError','stopReason','errorMessage']: 
   if k in msg:out.append(k+': '+str(msg[k]))
 txt='\n'.join(out);(O/f'{idx:03}-{sid}.md').write_text(txt);stat.append({'index':idx,'sid':sid,'chars':len(txt),'lines':len(txt.splitlines())})
(B/'paragraph-stats.json').write_text(json.dumps(stat,indent=2));print('chars',sum(x['chars'] for x in stat),'paragraphs',len(seen));print(stat[64])
