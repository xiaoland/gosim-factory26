from pathlib import Path
import json,collections,re
out=Path('tasks/iteration10/run-audit/github/evidence');D=json.loads((out/'raw.json').read_text()); db=list(D['dbs'].values())[-1]
(out/'db-final.json').write_text(json.dumps(db,ensure_ascii=False,indent=2))
# All snapshots mapped by native path basename. Never assume headers exist.
mapid={}
for f in D['files'].values():
 if f['path'].endswith('/sessions.json'):
  for s in json.loads(f['text']):
   if s.get('native_session_path'):mapid[s['native_session_path'].split('/')[-1]]=s
sessions={};sources=collections.defaultdict(list); variants=[]
for f in D['files'].values():
 if not ('/native-homes/' in f['path'] and f['path'].endswith('.jsonl')):continue
 lines=f['text'].splitlines(); header=next((json.loads(l) for l in lines if json.loads(l).get('type')=='session'),None)
 name=f['path'].split('/')[-1];sid=header['id'] if header else mapid.get(name,{}).get('native_session_id',name)
 s=sessions.setdefault(sid,{});sources[sid].append(f['path'])
 for n,line in enumerate(lines,1):
  v=json.loads(line);k=(sid,v.get('id'),v.get('timestamp'))
  if k in s and s[k]['raw']!=v:variants.append({'sid':sid,'line':n,'path':f['path'],'other':s[k]['source']})
  else:s.setdefault(k,{'raw':v,'source':f['path'],'line':n})
ss=[]
for sid,m in sessions.items():
 rows=sorted(m.values(),key=lambda x:(x['raw'].get('timestamp',''),x['line']));ss.append({'id':sid,'mapping':next((v for v in mapid.values() if v.get('native_session_id')==sid),{}),'sources':sources[sid],'rows':rows})
ss.sort(key=lambda s:s['rows'][0]['raw'].get('timestamp',''))
(out/'sessions.json').write_text(json.dumps(ss,ensure_ascii=False))
for i,s in enumerate(ss,1):
 lines=[]
 for n,x in enumerate(s['rows'],1):
  r=x['raw'];lines.append(f"\n[{n} raw:L{x['line']} {r.get('timestamp')} {r.get('type')} id={r.get('id')}]\n")
  msg=r.get('message',r);lines.append(json.dumps(msg,ensure_ascii=False))
 (out/f'session-{i:02}.txt').write_text(''.join(lines))
print('SESSIONS',len(ss),'rows',sum(len(s['rows']) for s in ss),'variants',len(variants))
for i,s in enumerate(ss,1):
 ctr=collections.Counter(x['raw'].get('type') for x in s['rows']);print(i,s['id'],s['mapping'].get('work_item_kind'),s['mapping'].get('work_item_id'),len(s['rows']),sum(len(json.dumps(x['raw'])) for x in s['rows']),dict(ctr))
(out/'manifest.json').write_text(json.dumps({'roots':D['roots'],'files':D['manifest'],'variants':variants},ensure_ascii=False,indent=2))
# Human-readable work item corpus includes hidden comments and activity.
for x in db['local_items']:
 wi=x['node_id'];lines=[json.dumps(x,ensure_ascii=False,indent=2)]
 for c in db['local_comments']:
  if c['work_item_node_id']==wi:lines.append('COMMENT '+json.dumps(c,ensure_ascii=False))
 for a in db['local_activity']:
  if a['work_item_node_id']==wi:lines.append('ACTIVITY '+json.dumps(a,ensure_ascii=False))
 (out/(wi.replace(':','-')+'.txt')).write_text('\n\n'.join(lines))
for f in D['files'].values():
 if f['path'].endswith('/requirements.yaml'):(out/'requirements.yaml').write_text(f['text'])
