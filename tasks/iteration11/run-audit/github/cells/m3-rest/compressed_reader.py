import difflib, hashlib, json, pathlib, re, sys

ROOT=pathlib.Path('/Volumes/WorkSSD/Development/factory26/tasks/iteration11/run-audit/github')
ASSIGN=json.loads((ROOT/'cells/m3/assignment.json').read_text())
EXCLUDE='2026-09-29T05-26-59-511Z_01a0eba1-6ab7-7751-8a0a-e84a52a71f95'
ASSIGN=[x for x in ASSIGN if x['id']!=EXCLUDE]
seen={}; raw={}; out=[]

def redact(s):
 s=s.replace('Valid-password-123!','[redacted test password]')
 s=re.sub(r'(?i)(api[_ -]?key\s*[:=]\s*)[^\s,;]+',r'\1[redacted]',s)
 s=re.sub(r'(?i)("(?:sessionKey|accessToken|refreshToken|apiKey|secret|password)"\s*:\s*")[^"]+',r'\1[redacted]',s)
 s=re.sub(r'(?i)(session[_-]?key|access[_-]?token|refresh[_-]?token|api[_-]?key|secret|password)(\s*=\s*)(["\x27])[^"\x27\s<>]+\3',r'\1\2\3[redacted]\3',s)
 s=re.sub(r'(?i)(session[_-]?key|access[_-]?token|refresh[_-]?token|api[_-]?key|secret|password)(\s*[:=]\s*)([^\s,;<>]+)',r'\1\2[redacted]',s)
 return s

def emit(ix,n,label,s):
 if not isinstance(s,str):s=json.dumps(s,ensure_ascii=False,indent=2)
 family=label.split('-part-')[0]
 key=(family,hashlib.sha256(s.encode()).hexdigest())
 prev=seen.get(key)
 if prev:out.append(f'\n## U{ix} R{n} {label} EXACT DUPLICATE U{prev[0]} R{prev[1]} {prev[2]}\n')
 else:
  seen[key]=(ix,n,label)
  # A bounded read may reappear as the exact prefix of a later bounded read.
  # Cite only byte-for-byte equal prefixes already emitted; show the new tail.
  ref=None;prefix=0
  if len(s)>5000:
   for p,loc in raw.get(family,[]):
    if p[:128]!=s[:128]:continue
    lim=min(len(p),len(s));i=0
    while i<lim and p[i]==s[i]:i+=1
    if i>prefix:prefix=i;ref=loc
   if prefix<max(5000,int(len(s)*0.8)):prefix=0;ref=None
  if prefix:
   out.append(f'\n## U{ix} R{n} {label} CHARS {len(s)} EXACT PREFIX 0:{prefix} U{ref[0]} R{ref[1]} {ref[2]}; NEW TAIL {prefix}:{len(s)}\n'+redact(s[prefix:])+'\n')
  elif len(s)>10000 and raw.get(family):
   # Long board snapshots and command results often repeat sections verbatim
   # while appending a few comments. Cite exact matching line spans from an
   # earlier emitted part and show every changed span in full.
   lines=s.splitlines(keepends=True)
   candidates=raw[family][-12:]
   best=None;best_len=0
   for old,loc in candidates:
    if len(old)<5000:continue
    oldlines=old.splitlines(keepends=True)
    matcher=difflib.SequenceMatcher(None,oldlines,lines,autojunk=False)
    blocks=matcher.get_matching_blocks()
    matched=sum(sum(map(len,lines[b:b+k])) for _,b,k in blocks if k)
    if matched>best_len:best=(oldlines,loc,blocks);best_len=matched
   if best and best_len>len(s)*0.5:
    oldlines,loc,blocks=best
    out.append(f'\n## U{ix} R{n} {label} CHARS {len(s)} EXACT MATCHED {best_len} CHARS TO U{loc[0]} R{loc[1]} {loc[2]}\n')
    pos=0
    for ai,bi,k in blocks:
     if bi>pos:
      frag=''.join(lines[pos:bi]);out.append(f'NEW LINES {pos+1}:{bi} CHARS {len(frag)}\n'+redact(frag)+'\n')
     if k:out.append(f'EXACT REUSE U{loc[0]} R{loc[1]} lines {ai+1}:{ai+k} -> current {bi+1}:{bi+k}\n')
     pos=bi+k
   else:out.append(f'\n## U{ix} R{n} {label} CHARS {len(s)}\n'+redact(s)+'\n')
  else:out.append(f'\n## U{ix} R{n} {label} CHARS {len(s)}\n'+redact(s)+'\n')
  if len(s)>5000:raw.setdefault(family,[]).append((s,(ix,n,label)))

for ix,u in enumerate(ASSIGN):
 body=(ROOT/u['view']).read_text()
 for block in re.split(r'(?=^## Record \d+\n)',body,flags=re.M):
  if not block.startswith('## Record '):continue
  n=int(re.match(r'## Record (\d+)',block).group(1))
  d=json.loads(block[block.index('{'):])
  m=d.get('message')
  if isinstance(m,dict):
   for pi,p in enumerate(m.get('content',[]),1):
    if isinstance(p,dict):
     typ=p.get('type','unknown')
     if typ=='text':s=p.get('text','')
     elif typ=='thinking':s=p.get('thinking','')
     elif typ=='toolCall':s=json.dumps({'name':p.get('name'),'arguments':p.get('arguments')},ensure_ascii=False,indent=2)
     elif typ=='image':s='[image: bytes unavailable in view]'
     else:s=json.dumps(p,ensure_ascii=False,indent=2)
     # These exact message.content parts in units 0–4 were read through the
     # earlier bounded content-only pass; this stream fills their missing fields.
     if ix>=5 or typ not in ('text','toolCall','image'):
      emit(ix,n,f'message.{typ}-part-{pi}',s)
    else:emit(ix,n,f'message.other-part-{pi}',p)
   if m.get('details'):emit(ix,n,'message.details',m['details'])
   # Provider/model/usage/stop packaging is operational metadata. The audit
   # consumes substantive content, thinking, tool calls/results and details.
  if d.get('type')!='message':
   typ=d.get('recordType') or d.get('type') or 'other'
   # Transcript message text is the same material as message.content in its
   # corresponding subagent session; inspect its delivery metadata separately.
   skip=('id','parentId','timestamp','ts','runId','cwd','version','message')
   if typ=='message':skip+=('text',)
   obj={k:v for k,v in d.items() if k not in skip}
   if obj and typ not in ('session','model_change','thinking_level_change'):
    emit(ix,n,'nonmessage-'+str(typ),obj)

stream=''.join(out)
if len(sys.argv)>1 and sys.argv[1]=='locate':
 needle='\n## '+sys.argv[2]+' '
 print(stream.find(needle))
 sys.exit()
if len(sys.argv)>1 and sys.argv[1]=='slice':
 a=int(sys.argv[2]);b=min(len(stream),int(sys.argv[3]))
 print(f'SLICE RANGE {a}:{b} OF {len(stream)}')
 print(stream[a:b]);sys.exit()
if len(sys.argv)==1 or sys.argv[1]=='status':
 print('chars',len(stream),'chunks35k',(len(stream)+34999)//35000,'parts',len(out),'unique',len(seen))
 sys.exit()
size=int(sys.argv[2]) if len(sys.argv)>2 else 35000
chunk=int(sys.argv[1]);a=chunk*size;b=min(len(stream),(chunk+1)*size)
print(f'CHUNK {chunk} RANGE {a}:{b} OF {len(stream)}')
print(stream[a:b])
