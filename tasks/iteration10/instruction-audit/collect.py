"""只读收集定向输入材料；不运行 Harness 或模型，不采集凭据。"""
import hashlib,json,pathlib,subprocess
OUT=pathlib.Path(__file__).resolve().parent
REMOTE=r'''
import pathlib,json,hashlib
root=pathlib.Path('/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/generation/runs')
result={}
for label,slug,stamp in [('github','github-88884da4b94a0f','20260928-030347-78b10c07'),('sheet','sheet-984a08e3155e3e','20260928-025746-66feadac')]:
 b=root/('pi-braid--hackathon--'+slug)/'workspace/official-generation/template/.factory26'/stamp
 paths=[b/'prompt.txt',b/'materials.json',b/'implementation-hashes.json',b/'braid-state/sessions.json']
 paths+=list((b/'work/capabilities').glob('*/native-template/agents/*.md'))
 paths+=list((b/'work/capabilities').glob('*/pi'))
 paths+=list((b/'braid-state/physical').glob('*/instructions.md'))
 paths+=list((b/'braid-state/physical').glob('*/context.md'))
 paths+=list((b/'work/skills').rglob('*.md'))
 paths+=list((b/'work/native-homes').rglob('*meta.json'))
 paths+=list((b/'work/tmp').rglob('prompt*.md'))
 req=json.loads((b/'braid-request.json').read_text())
 result[label]={'root':str(b),'request':{k:req[k] for k in ['profiles','root_profile_id','bindings']},'files':{}}
 for p in paths:
  if p.is_file():
   raw=p.read_bytes();result[label]['files'][str(p.relative_to(b))]={'sha256':hashlib.sha256(raw).hexdigest(),'text':raw.decode(errors='replace')}
 # Exact entry prompts and subagent requests, not the complete behavior transcript.
 entries=[]
 for p in (b/'work/native-homes').rglob('*.jsonl'):
  first=True
  for ln,line in enumerate(p.open(),1):
   try:o=json.loads(line)
   except ValueError:continue
   m=o.get('message',{}); content=m.get('content',[])
   if m.get('role')=='user' and first:
    entries.append({'path':str(p.relative_to(b)),'line':ln,'kind':'first-user','content':content});first=False
   if isinstance(content,list):
    for c in content:
     if c.get('type')=='toolCall' and c.get('name') in ['subagent','subagent_wait']:
      entries.append({'path':str(p.relative_to(b)),'line':ln,'kind':'toolCall','content':c})
 result[label]['entries']=entries
print(json.dumps(result,ensure_ascii=False))
'''
data=json.loads(subprocess.check_output(['ssh','wsl.win-ws.localhost','python3 -'],input=REMOTE.encode()))
(OUT/'evidence.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
manifest={label:{'root':d['root'],'files':{p:{'sha256':f['sha256'],'chars':len(f['text'])} for p,f in d['files'].items()},'entries':len(d['entries'])} for label,d in data.items()}
(OUT/'sources.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
for label,d in data.items():
 print(label,len(d['files']),len(d['entries']))
 for k,v in d['files'].items():
  if k=='materials.json':print(json.loads(v['text'])['runtime'])
