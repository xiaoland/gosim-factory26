"""定向读取子角色工具反馈与冻结的原生配置，避免读取全量轨迹正文。"""
import subprocess,json,pathlib,hashlib
out=pathlib.Path(__file__).resolve().parent
remote=r'''
import pathlib,json,hashlib
root=pathlib.Path('/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/generation/runs')
result={}
for label,slug,stamp in [('github','github-88884da4b94a0f','20260928-030347-78b10c07'),('sheet','sheet-984a08e3155e3e','20260928-025746-66feadac')]:
 b=root/('pi-braid--hackathon--'+slug)/'workspace/official-generation/template/.factory26'/stamp
 feedback=[];roles={};launch={}
 for p in (b/'work/native-homes').glob('*/agents/*.md'):
  raw=p.read_bytes();roles[str(p.relative_to(b))]={'sha256':hashlib.sha256(raw).hexdigest(),'text':raw.decode()}
 for p in (b/'work/native-homes').rglob('*.jsonl'):
  for n,line in enumerate(p.open(),1):
   try:o=json.loads(line)
   except:continue
   m=o.get('message',{})
   if m.get('role')=='toolResult' and m.get('toolName') in ['subagent','subagent_wait']:
    feedback.append({'path':str(p.relative_to(b)),'line':n,'content':m.get('content'),'details':m.get('details')})
 for p in (b/'work/tmp').glob('pi-subagents-*/async-subagent-runs/*/config.json'):
  o=json.loads(p.read_text());launch[str(p.relative_to(b))]=o
 result[label]={'feedback':feedback,'roles':roles,'launch':launch}
print(json.dumps(result,ensure_ascii=False))
'''
data=json.loads(subprocess.check_output(['ssh','wsl.win-ws.localhost','python3 -'],input=remote.encode()))
(out/'feedback.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
for label,d in data.items():print(label,len(d['roles']),len(d['feedback']),len(d['launch']))
