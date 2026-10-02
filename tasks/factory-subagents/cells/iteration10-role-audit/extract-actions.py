import json,sys,zipfile
from pathlib import Path
SIDS={'01a0e299-90fd-7652-8f9c-ac54e0f5e402','01a0e29d-9511-719a-9662-a40b1351d755','01a0e2ba-6e7a-7719-929d-7923f8e4cca7','01a0e5f3-916b-7222-9cc8-a17bf775891c'}
out=[];seen=set()
def take(name,raw):
 sid=next((s for s in SIDS if s in Path(name).name),None)
 if not sid or not name.endswith('.jsonl'):return
 for ln,line in enumerate(raw.decode().splitlines(),1):
  r=json.loads(line);m=r.get('message',{});key=(sid,r.get('id'),r.get('timestamp'))
  if r.get('type')!='message' or key in seen:continue
  seen.add(key); blocks=m.get('content',[]);blocks=blocks if isinstance(blocks,list) else []
  keep=[b for b in blocks if b.get('type')=='toolCall' or b.get('type')=='text']
  # Keep observable tools and user-facing messages, never private thinking.
  if keep:out.append({'session':sid,'path':name,'line':ln,'time':r.get('timestamp'),'role':m.get('role'),'tool':m.get('toolName'),'content':keep})
if sys.argv[1]=='hosted':
 with zipfile.ZipFile('runs/e20260928-completed-replay/github/source-workspace.zip') as z:
  for name in sorted(z.namelist()):
   if '/work/native-homes/' in name and any(s in name for s in SIDS):take(name,z.read(name))
else:
 base=Path('/home/yyh/Development/factory26/runs/e20260928-01-flash-team/attempt-02/generation/runs')
 for p in base.glob('*/workspace/official-generation/template/.factory26/*/work/native-homes/**/*.jsonl'):
  if any(s in str(p) for s in SIDS):take(str(p),p.read_bytes())
json.dump(out,sys.stdout,ensure_ascii=False)
