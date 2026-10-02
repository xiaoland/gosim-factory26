from pathlib import Path
import json,re,hashlib
root=Path(__file__).resolve().parents[2];dest=Path(__file__).parent;sel=json.loads((dest/'assignment.json').read_text());seen={};pieces=[];refs=[]
def text(s,path):
 out=[]
 for i,p in enumerate(s.split('\n\n')):
  at=path+' paragraph '+str(i)
  if len(p)>100:
   h=hashlib.sha256(p.encode()).hexdigest()
   if h in seen:
    refs.append({'at':at,'prior':seen[h],'sha256':h,'chars':len(p)});out.append('[EXACT PARAGRAPH DUPLICATE '+seen[h]+']');continue
   seen[h]=at
  out.append(p)
 return '\n\n'.join(out)
def render(x,path):
 if isinstance(x,dict):return '\n'.join(k+': '+render(v,path+'.'+k) for k,v in x.items())
 if isinstance(x,list):return '\n'.join('['+str(i)+'] '+render(v,path+'.'+str(i)) for i,v in enumerate(x))
 if isinstance(x,str):return text(x,path)
 return json.dumps(x)
for u in sel:
 for b in re.split(r'(?=^## Record \d+\n)',(root/u['view']).read_text(),flags=re.M):
  if not b.startswith('## Record '):continue
  n=int(re.match(r'## Record (\d+)',b)[1]);loc=u['id']+' r'+str(n)
  if 'EXACT_DUPLICATE →' in b and '{' not in b:pieces.append('\n'+loc+'\n'+b);continue
  row=json.loads(b[b.index('{'):]);pieces.append('\n'+loc+'\n'+render(row,loc))
s='\n'.join(pieces);(dest/'visible.txt').write_text(s);(dest/'duplicate-refs.json').write_text(json.dumps(refs,ensure_ascii=False,indent=2));print('characters',len(s),'duplicate chars',sum(r['chars'] for r in refs))
