import json,sys,hashlib,re
from pathlib import Path
P=Path('tasks/iteration10/run-audit/github/evidence');ss=json.loads((P/'sessions.json').read_text());si,lo,hi=map(int,sys.argv[1:4]);s=ss[si-1]
db=json.loads((P/'db-final.json').read_text())
known=[re.sub(r'\s+',' ',(P/'requirements.yaml').read_text()).strip()]
for table in ['local_items','local_comments']:
 for item in db[table]:
  for key in ['body','description']:
   if isinstance(item.get(key),str):known.append(re.sub(r'\s+',' ',item[key]).strip())
def reuse(t):
 parts=re.split(r'(\n\s*\n)',t);out=[]
 for part in parts:
  norm=re.sub(r'\s+',' ',part).strip()
  if len(norm)>80 and any(norm in k for k in known):out.append('[EXACT KNOWN REQUIREMENT/ITEM PARAGRAPH REUSED '+str(len(part))+' chars SHA '+hashlib.sha256(part.encode()).hexdigest()[:12]+']')
  else:out.append(part)
 return re.sub(r'(?m)^\[EXACT KNOWN REQUIREMENT/ITEM PARAGRAPH REUSED.*?\]\n?', '', ''.join(out)) + ('\n[KNOWN PARAGRAPHS REUSED; full bodies/source hashes preserved in session/raw files]' if any(x.startswith('[EXACT KNOWN') for x in out) else '')
for n,x in enumerate(s['rows'][lo-1:hi],lo):
 r=x['raw'];m=r.get('message',r);print(f'\n[{si}:{n} rawL{x["line"]} {r.get("timestamp")} {r.get("type")} {m.get("role", "")}]')
 if 'content' not in m: print(json.dumps(m,ensure_ascii=False));continue
 for b in m['content'] if isinstance(m['content'],list) else [{'type':'text','text':m['content']}]:
  if b.get('type')=='toolCall':
   a=b.get('arguments',{}).copy()
   if b.get('name')=='write' and len(a.get('content',''))>1000 and str(a.get('path','')).endswith(('.js','.mjs','.ts','.tsx','.css','.html','.json','.py')):
    t=a['content'];a['content']=f'[MECHANICAL CODE OMITTED {len(t)} chars SHA256 {hashlib.sha256(t.encode()).hexdigest()}; original retained]'
   if b.get('name')=='edit' and len(json.dumps(a))>2500:
    original=json.dumps(a,ensure_ascii=False);a={'path':a.get('path'),'omitted_edits':len(a.get('edits',[])),'chars':len(original),'sha':hashlib.sha256(original.encode()).hexdigest()}
   if b.get('name')=='bash' and len(a.get('command',''))>3000 and 'braid ' not in a['command'] and any(z in a['command'] for z in ['cat >', 'python3 -', 'node -']):
    t=a['command'];a['command']=t[:350]+'\n[MECHANICAL SCRIPT MIDDLE OMITTED '+str(len(t))+' chars SHA '+hashlib.sha256(t.encode()).hexdigest()+']\n'+t[-350:]
   print('TOOL',b.get('name'),json.dumps(a,ensure_ascii=False))
  elif b.get('type') in ('text','thinking'):
   t=b.get('text',b.get('thinking',''))
   if m.get('role')=='toolResult' and len(t)>5000 and (t.lstrip().startswith(('import ','export ','function ')) or (t.lstrip().startswith('=====') and 'import ' in t[:1000])):
    print(t[:350]+'\n[MECHANICAL SOURCE RESULT MIDDLE OMITTED '+str(len(t))+' chars SHA '+hashlib.sha256(t.encode()).hexdigest()+']\n'+t[-350:])
   else:print(reuse(t) if m.get('role')!='assistant' else t)
  elif b.get('type')=='image':print('[BINARY IMAGE OMITTED mime='+str(b.get('mimeType'))+' chars='+str(len(json.dumps(b)))+']')
  else:print(json.dumps(b,ensure_ascii=False))
 if m.get('isError'):print('IS_ERROR',m['isError'])
 if m.get('errorMessage'):print('NATIVE_ERROR',m.get('stopReason'),m['errorMessage'])
