import hashlib, json, pathlib, re, sys
from read_view import records

HERE=pathlib.Path(__file__).resolve().parent
receipt=json.loads((HERE/'read-receipts.json').read_text())
seen={}; out=[]

def red(s):
 s=s.replace('Valid-password-123!','[redacted test password]')
 s=re.sub(r'(?i)(api[_ -]?key\s*[:=]\s*)[^\s,;]+',r'\1[redacted]',s)
 s=re.sub(r'(?i)("(?:sessionKey|accessToken|refreshToken|apiKey|secret|password)"\s*:\s*")[^"]+',r'\1[redacted]',s)
 s=re.sub(r'(?i)(session[_-]?key|access[_-]?token|refresh[_-]?token|api[_-]?key|secret|password)(\s*=\s*)(["\x27])[^"\x27\s<>]+\3',r'\1\2\3[redacted]\3',s)
 s=re.sub(r'(?i)(session[_-]?key|access[_-]?token|refresh[_-]?token|api[_-]?key|secret|password)(\s*[:=]\s*)([^\s,;<>]+)',r'\1\2[redacted]',s)
 return s

def emit(ix,n,label,s):
 key=(label.split('-part-')[0],hashlib.sha256(s.encode()).hexdigest())
 prev=seen.get(key)
 if prev: out.append(f'\n## U{ix} R{n} {label} EXACT DUPLICATE U{prev[0]} R{prev[1]}\n')
 else:
  seen[key]=(ix,n)
  out.append(f'\n## U{ix} R{n} {label} CHARS {len(s)}\n'+red(s)+'\n')

for ix,u in enumerate(receipt['units']):
 for n,source,d in records(u['view']):
  m=d.get('message')
  if isinstance(m,dict):
   for pi,p in enumerate(m.get('content',[]),1):
    if isinstance(p,dict) and p.get('type')=='thinking':
     emit(ix,n,f'thinking-part-{pi}',p.get('thinking',''))
   if m.get('details'):
    emit(ix,n,'message.details',json.dumps(m['details'],ensure_ascii=False,indent=2))
  if d.get('type')!='message':
   # Transcript message content was already displayed by read_view/read_unique.
   # Its top-level text repeats that content. Supplement only fields those readers skipped.
   typ=d.get('recordType') or d.get('type')
   if typ=='message':
    obj={k:v for k,v in d.items() if k not in ('id','parentId','timestamp','ts','runId','cwd','version','message','text')}
    emit(ix,n,'transcript-metadata',json.dumps(obj,ensure_ascii=False,indent=2))
   else:
    obj={k:v for k,v in d.items() if k not in ('id','parentId','timestamp','ts','runId','cwd','version')}
    emit(ix,n,'nonmessage-'+str(typ),json.dumps(obj,ensure_ascii=False,indent=2))

stream=''.join(out)
if len(sys.argv)==1 or sys.argv[1]=='status':
 print('chars',len(stream),'chunks35k',(len(stream)+34999)//35000,'parts',len(out),'unique',len(seen))
 sys.exit()
size=int(sys.argv[2]) if len(sys.argv)>2 else 35000
chunk=int(sys.argv[1]);a=chunk*size;b=min(len(stream),(chunk+1)*size)
print(f'CHUNK {chunk} RANGE {a}:{b} OF {len(stream)}')
print(stream[a:b])
