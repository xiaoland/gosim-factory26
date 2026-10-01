import collections, hashlib, json, re, sys, zipfile
from pathlib import Path

def scan(names, read):
    names = sorted(names)
    session_maps = []
    for name in names:
        if name.endswith('/braid-state/sessions.json'):
            session_maps.extend(json.loads(read(name)))
    mapped = {Path(s['native_session_path']).name:s['native_session_id'] for s in session_maps if s.get('native_session_path')}
    members = {s['native_session_id']:s for s in session_maps if s.get('native_session_id')}
    seen=set(); summaries={}; calls=[]; results={}; mentions=[]; errors=[]; headerless=[]; tools=collections.Counter(); files=0
    for name in names:
        if not name.endswith('.jsonl') or not ('/work/native-homes/' in name or '/native/' in name): continue
        files+=1; sid=mapped.get(Path(name).name); header=False
        for line_no,line in enumerate(read(name).decode().splitlines(),1):
            try: row=json.loads(line)
            except ValueError as e: errors.append([name,line_no,str(e)]);continue
            if row.get('type')=='session': sid=row.get('id');header=True
            if row.get('type')!='message' or not sid:continue
            key=(sid,row.get('id'),row.get('timestamp'))
            if key in seen:continue
            seen.add(key)
            m=row.get('message',{});loc={'session':sid,'path':name,'line':line_no,'timestamp':row.get('timestamp')}
            summary=summaries.setdefault(sid,{'paths':set(),'models':set(),'usage_messages':0,'member':{k:members.get(sid,{}).get(k) for k in ('work_item_kind','work_item_id','profile_id')},'first':row.get('timestamp'),'last':row.get('timestamp')})
            summary['paths'].add(name);summary['last']=max(summary['last'] or '',row.get('timestamp') or '')
            if m.get('model'):summary['models'].add(m['model'])
            if 'input' in m.get('usage',{}):summary['usage_messages']+=1
            content=m.get('content',[]); blocks=content if isinstance(content,list) else []
            if m.get('role')=='toolResult' and m.get('toolName','').startswith('subagent'):
                body=content if isinstance(content,str) else '\n'.join(b.get('text','') for b in blocks)
                results[m.get('toolCallId')]={**loc,'name':m.get('toolName'),'text':body,'details':m.get('details')}
            for b in blocks:
                if b.get('type')!='toolCall':continue
                tools[b.get('name')]+=1
                if b.get('name','').startswith('subagent'):
                    calls.append({**loc,'id':b.get('id'),'name':b['name'],'arguments':b.get('arguments',{})})
            if m.get('role')=='assistant':
                body='\n'.join(b.get('text','') or b.get('thinking','') for b in blocks)
                hits=[match.start() for match in re.finditer(r'advisor|顾问|咨询',body,re.I)]
                if hits:mentions.append({**loc,'snippets':[body[max(0,i-350):i+650] for i in hits[:4]]})
        if not header:headerless.append({'path':name,'mapped_session':sid})
    configs=[]
    for name in names:
        if name.endswith('/advisor.md') or (('/native-config/' in name or '/agents/' in name) and name.endswith('/instructions.md')):
            raw=read(name);configs.append({'path':name,'sha256':hashlib.sha256(raw).hexdigest(),'text':raw.decode()})
    artifacts=[]
    for name in names:
        if '/subagent-artifacts/' in name and name.endswith('_meta.json'):
            artifacts.append({'path':name,'data':json.loads(read(name))})
    for s in summaries.values():s['paths']=sorted(s['paths']);s['models']=sorted(s['models'])
    return {'files_scanned':files,'member_manifest_count':len(members),'missing_member_sessions':sorted(set(members)-set(summaries)),'sessions':summaries,'tool_counts':tools,'calls':[{**c,'result':results.get(c['id'])} for c in calls],'advisor_mentions_not_calls':mentions,'parse_errors':errors,'headerless':headerless,'configs':configs,'artifact_meta':artifacts}

out={}
if sys.argv[1]=='hosted':
    for task in ('github','sheet'):
        path=f'runs/e20260928-completed-replay/{task}/source-workspace.zip'
        with zipfile.ZipFile(path) as z:out[task]=scan(z.namelist(),z.read)
else:
    root=Path('/home/yyh/Development/factory26/runs')
    for experiment,attempt in [('e20260928-01-flash-team','attempt-02'),('e20260928-02-deepseek-direct','attempt-09')]:
        for run in (root/experiment/attempt/'generation/runs').iterdir():
            bases=list((run/'workspace').glob('official-generation/template/.factory26/*'))
            if not bases: bases=list((run/'workspace').glob('observed-agent/template/.factory26/*'))
            if not bases: bases=list((run/'workspace').glob('**/.factory26/*'))
            for base in bases:
                if not base.is_dir():continue
                names=[str(p) for p in base.rglob('*') if p.is_file() and (p.suffix in ('.jsonl','.md') or p.name=='sessions.json' or p.name.endswith('_meta.json'))]
                out[experiment+'/'+run.name]=scan(names,lambda n:Path(n).read_bytes())
json.dump(out,sys.stdout,ensure_ascii=False)
