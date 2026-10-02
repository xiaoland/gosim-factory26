import difflib, hashlib, json, pathlib, re, sys
ROOT=pathlib.Path('/Volumes/WorkSSD/Development/factory26/tasks/iteration11/run-audit/github')
ASSIGN=json.loads((ROOT/'cells/m3/assignment.json').read_text())
EXCLUDE='2026-09-29T05-26-59-511Z_01a0eba1-6ab7-7751-8a0a-e84a52a71f95'
ASSIGN=[x for x in ASSIGN if x['id'] != EXCLUDE]

def records(v):
 body=(ROOT/v).read_text()
 for block in re.split(r'(?=^## Record \d+\n)',body,flags=re.M):
  if block.startswith('## Record '):
   n=int(re.match(r'## Record (\d+)',block).group(1))
   yield n,json.loads(block[block.index('{'):])

def parts(item):
 if isinstance(item,str):return [item]
 if isinstance(item,list):
  a=[]
  for x in item:a.extend(parts(x))
  return a
 if isinstance(item,dict):
  t=item.get('type')
  if t=='text':return [item.get('text','')]
  if t=='thinking':return []
  if t=='toolCall':return ['CALL '+str(item.get('name'))+' '+json.dumps(item.get('arguments'),ensure_ascii=False)]
  if t=='image':return ['[image]']
  return [json.dumps(item,ensure_ascii=False)]
 return [str(item)]

def content(o):
 m=o.get('message',{})
 p=parts(m.get('content',o.get('text','')))
 if not p and o.get('type')!='message':
  p=[json.dumps({k:v for k,v in o.items() if k not in ('id','parentId','message')},ensure_ascii=False)]
 return '\n'.join(p).replace('\\n','\n')

def role(o):
 m=o.get('message',{})
 return m.get('role') or o.get('role') or o.get('recordType') or o.get('type') or 'other'

def redact(s):
 s=s.replace('Valid-password-123!','[redacted test password]')
 s=re.sub(r'(?i)(api[_ -]?key\s*[:=]\s*)[^\s,;]+',r'\1[redacted]',s)
 return s

rows=[];seen={}
for ix,x in enumerate(ASSIGN):
 arr=[]
 for n,o in records(x['view']):
  c=content(o);r=role(o);key=(r,hashlib.sha256(c.encode()).hexdigest()) if c else None
  d=seen.get(key) if key else None
  arr.append((n,o,c,d))
  if key and not d:seen[key]=(ix,n)
 rows.append(arr)

if len(sys.argv)>1 and sys.argv[1]=='diff':
 ix,n,bix,bn=map(int,sys.argv[2:6]); a=rows[bix][bn-1][2].splitlines(keepends=True); b=rows[ix][n-1][2].splitlines(keepends=True)
 print('UNIT',ix,'RECORD',n,'COMPARE',bix,bn,'TARGET_CHARS',sum(map(len,b)),'BASE_CHARS',sum(map(len,a)))
 for tag,i,j,k,l in difflib.SequenceMatcher(None,a,b,autojunk=False).get_opcodes():
  if tag=='equal':print('EQUAL lines',k+1,'-',l,'references BASE lines',i+1,'-',j)
  else:
   print('DELTA',tag,'target lines',k+1,'-',l,'base lines',i+1,'-',j)
   print(redact(''.join(b[k:l])))
 sys.exit()

if len(sys.argv)==1:
 for ix,arr in enumerate(rows):
  print(ix,ASSIGN[ix]['owner'],ASSIGN[ix]['kind'],len(arr),'unique_chars',sum(len(c) for n,o,c,d in arr if not d),'dups',sum(bool(d) for n,o,c,d in arr))
  print('big',[(n,len(c)) for n,o,c,d in arr if len(c)>10000 and not d])
 sys.exit()
ix=int(sys.argv[1]);lo=int(sys.argv[2]);hi=int(sys.argv[3]);off=int(sys.argv[4]) if len(sys.argv)>4 else None;end=int(sys.argv[5]) if len(sys.argv)>5 else None
for n,o,c,d in rows[ix]:
 if not lo<=n<=hi:continue
 print('\n### UNIT',ix,'RECORD',n,role(o),o.get('timestamp',''),'LENGTH',len(c))
 if d:
  print('EXACT DUPLICATE',d)
 elif off is not None:
  print('SLICE',off,end,'OF',len(c));print(redact(c[off:end]))
 else:print(redact(c))
