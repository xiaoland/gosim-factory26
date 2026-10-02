from pathlib import Path
import json,sqlite3,hashlib,os
r=Path('/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct')
files={}; manifests=[]; dbs={}
def add(p):
 if not p.is_file(): return
 b=p.read_bytes(); h=hashlib.sha256(b).hexdigest(); key=str(p.relative_to(r)); manifests.append({'path':key,'bytes':len(b),'sha256':h})
 if h not in files:
  try: files[h]={'path':key,'text':b.decode()}
  except UnicodeDecodeError: pass
roots=[]
for g in [r/'generation']+sorted(r.glob('attempt-*/generation'))+sorted(r.glob('attempt-*/continuation-*/generation')):
 for run in g.glob('runs/pi-braid--hackathon--github-*'):
  add(run/'run.json')
  for p in run.glob('workspace/official-generation/template/.factory26/*'):
   roots.append(str(p.relative_to(r)))
   for pat in ['*.json','*.jsonl','*.txt','braid-state/sessions.json','braid-state/physical/*/context.md','braid-state/physical/*/instructions.md','braid-state/turns/*.md','work/native-homes/*/*.jsonl','work/native-homes/*/sessions/**/*.jsonl','native/**/*.jsonl','recovery-source-native-*/*.jsonl','continuation02-root-native/*.jsonl','input/*']:
    for f in p.glob(pat):add(f)
   # Session trees only, explicitly excluding dependency trees.
   for base in (p/'work/native-homes').glob('*'):
    for root,ds,fs in os.walk(base):
     ds[:]=[d for d in ds if d not in ['node_modules','.cache']]
     for f in fs:
      if f.endswith('.jsonl'):add(Path(root)/f)
   dp=p/'braid-state/braid.sqlite3'
   if dp.exists():
    c=sqlite3.connect(f'file:{dp}?mode=ro',uri=True); c.row_factory=sqlite3.Row
    ts=[row[0] for row in c.execute("select name from sqlite_master where type='table'")]
    dbs[str(dp.relative_to(r))]={t:[{k:(v.decode(errors='replace') if isinstance(v,bytes) else v) for k,v in dict(row).items()} for row in c.execute('select * from '+t)] for t in ts}
for p in r.glob('attempt-*/github-workspace-provenance.json'):add(p)
print(json.dumps({'roots':roots,'manifest':manifests,'files':files,'dbs':dbs},ensure_ascii=False))
