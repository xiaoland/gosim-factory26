import hashlib, json, pathlib, re, sys

ROOT=pathlib.Path('/Volumes/WorkSSD/Development/factory26/tasks/iteration11/run-audit/github')
OWN=[4,5,11,0,8,6,9,1,2,7]
INDEX=json.loads((ROOT/'increment-index.json').read_text())['changed']
seen={};out=[]

def red(s):
 s=s.replace('Valid-password-123!','[redacted test password]')
 s=re.sub(r'(?i)(api[_ -]?key\s*[:=]\s*)[^\s,;]+',r'\1[redacted]',s)
 s=re.sub(r'(?i)("(?:sessionKey|accessToken|refreshToken|apiKey|secret|password)"\s*:\s*")[^"]+',r'\1[redacted]',s)
 s=re.sub(r'(?i)(session[_-]?key|access[_-]?token|refresh[_-]?token|api[_-]?key|secret|password)(\s*=\s*)(["\x27])[^"\x27\s<>]+\3',r'\1\2\3[redacted]\3',s)
 s=re.sub(r'(?i)(session[_-]?key|access[_-]?token|refresh[_-]?token|api[_-]?key|secret|password)(\s*[:=]\s*)([^\s,;<>]+)',r'\1\2[redacted]',s)
 return s

def emit(i,n,label,s):
 key=(label.split('-part-')[0],hashlib.sha256(s.encode()).hexdigest());prev=seen.get(key)
 if prev:out.append(f'\n## I{i} R{n} {label} EXACT DUPLICATE I{prev[0]} R{prev[1]}\n')
 else:
  seen[key]=(i,n);out.append(f'\n## I{i} R{n} {label} CHARS {len(s)}\n'+red(s)+'\n')

for i in OWN:
 x=INDEX[i];p=ROOT/'snapshot-02'/x['path'];q=ROOT/'snapshot-01'/x['path'];prior=sum(1 for _ in q.open()) if q.exists() else 0
 for n,line in enumerate(p.open(),1):
  if n<=prior:continue
  d=json.loads(line);m=d.get('message')
  if isinstance(m,dict):
   for pi,part in enumerate(m.get('content',[]),1):
    if isinstance(part,dict) and part.get('type')=='thinking':emit(i,n,f'thinking-part-{pi}',part.get('thinking',''))
   if m.get('details'):emit(i,n,'message.details',json.dumps(m['details'],ensure_ascii=False,indent=2))
  if d.get('type')!='message':
   typ=d.get('recordType') or d.get('type')
   if typ=='message':obj={k:v for k,v in d.items() if k not in ('id','parentId','timestamp','ts','runId','cwd','version','message','text')};emit(i,n,'transcript-metadata',json.dumps(obj,ensure_ascii=False,indent=2))
   else:obj={k:v for k,v in d.items() if k not in ('id','parentId','timestamp','ts','runId','cwd','version')};emit(i,n,'nonmessage-'+str(typ),json.dumps(obj,ensure_ascii=False,indent=2))

stream=''.join(out)
if len(sys.argv)==1 or sys.argv[1]=='status':
 print('chars',len(stream),'chunks35k',(len(stream)+34999)//35000,'parts',len(out),'unique',len(seen));sys.exit()
size=35000;chunk=int(sys.argv[1]);a=chunk*size;b=min(len(stream),(chunk+1)*size)
print(f'CHUNK {chunk} RANGE {a}:{b} OF {len(stream)}');print(stream[a:b])
