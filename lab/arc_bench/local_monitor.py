"""Read-only local provider monitor; 3+8 sampling, script judgments, no model or run control."""
import argparse
import base64
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

from .hosted_monitor import alert
from .provider_liveness import assess, transition

TERMINAL={'completed','finished','failed','interrupted','cancelled','lost'}

REMOTE="\nfrom pathlib import Path\nimport base64,json,sys\nrows=[]\nfor value in json.loads(sys.argv[1]):\n run=Path(value['record']).parent; state=value['state']; files={}; notes={}\n def keep(p,key,tail=False):\n  if not p.is_file():return\n  size=p.stat().st_size\n  with p.open('rb') as f:\n   start=max(0,size-2*1024*1024) if tail else 0\n   f.seek(start); data=f.read()\n  if start:\n   pos=data.find(b'\\n'); data=data[pos+1:] if pos>=0 else b''\n  files[key]=base64.b64encode(data).decode(); notes[key]={'source':str(p),'source_mtime':p.stat().st_mtime,'source_bytes':size,'captured_bytes':len(data),'tail':bool(start)}\n keep(run/'run.json','run.json')\n resource=Path('/factory26-no-mac-resource')\n keep(resource,'generation.resource.json')\n stage=Path('/workspace')\n factory=stage/'template/.factory26'\n required=[]; sessions=[]; provider_sources=[]\n result_path=run/state.get('result_path','workspace/experiment-result.json')\n result=state.get('result')\n for braid in sorted(factory.glob('*')) if factory.is_dir() else []:\n  if not (braid/'braid-state/request.json').is_file():continue\n  for name in ['braid-state/status.json','braid-state/result.json','recovery-provenance.json','recovery-attempt.json','process-evidence/resource-latest.json','process-evidence/resource-status.json','recovery-native-materials.json','recovery-source-result.json','recovery-diagnostics.json','recovery-git.json']:\n   keep(braid/name,'evidence/'+braid.name+'/'+name)\n  status=braid/'braid-state/status.json'\n  if not status.is_file():continue\n  required.append('evidence/'+braid.name+'/braid-state/status.json')\n  current=json.loads(status.read_text()).get('physical_sessions',[])\n  for session in current:\n   raw=session.get('native_session_path')\n   parts=Path(raw).parts if raw else ()\n   if '.factory26' not in parts:continue\n   rel=Path(*parts[parts.index('.factory26')+1:])\n   key='evidence/'+str(rel)\n   keep(factory/rel,key,True)\n   sessions.append({**{k:session.get(k) for k in ['work_item_kind','work_item_id','profile_id','status','native_session_id']},'path':key if key in files else None,'source':raw})\n   if key in files and session.get('status')=='running':required.append(key)\n  provider_sources.append(collect_provider_evidence(braid/'braid-state',time.time(),state.get('started_at')))\n  for name in ['braid.log','recovery-braid.log','pi-timing.jsonl']:\n   keep(braid/name,'evidence/'+braid.name+'/'+name,True)\n   if name=='recovery-braid.log' and 'evidence/'+braid.name+'/'+name in files:required.append('evidence/'+braid.name+'/'+name)\n for name in ['stdout.log','stderr.log','workspace/generation.stdout.log','workspace/generation.stderr.log','workspace/official-generation/template/.arc/stdout.log']:\n  keep(Path('/workspace/template/.arc/stdout.log') if name.endswith('/.arc/stdout.log') else run/name,name,True)\n  if name in files and name.endswith('/.arc/stdout.log') and state['phase'] in ('finished','failed','lost','interrupted','cancelled'):required.append(name)\n rows.append({'run_id':state['run_id'],'phase':state['phase'],'result':result,'runner_exit_code':state.get('runner_exit_code'),'labels':state.get('labels'), 'started_at':state.get('started_at'),'finished_at':state.get('finished_at'),'error':state.get('error'),'files':files,'notes':notes,'required_reads':required,'session_evidence':sessions,'provider_sources':provider_sources,'record':str(run/'run.json')})\nprint(json.dumps(rows))\n"


def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    temporary.replace(path)


def collect(run,batch,module_source):
    now=time.time();record=json.loads((run/'run.json').read_text())
    item={'run_id':run.name,'observed_at':now,'phase':record['phase'],'source_phase':record['phase'],
          'started_at':record.get('started_at'),'finished_at':record.get('finished_at'),
          'runner_exit_code':record.get('runner_exit_code'),'error':record.get('error'),
          'labels':record.get('labels'),'files':{},'notes':{},'required_reads':[],
          'session_evidence':[],'provider_sources':[],'record':str(run/'run.json')}
    result=run/record.get('result_path','workspace/experiment-result.json')
    if result.is_file():item['result']=json.loads(result.read_text())
    if record['phase'] in TERMINAL:return item
    try:
        resource_path=run/'workspace/generation.resource.json'
        resource=json.loads(resource_path.read_text())
        if resource.get('state')=='sending':
            item['status']='preparing'
            item['preparation']={'resource_state':'sending','source':str(resource_path)}
            return item
        argv=record['docker_endpoint']['argv']
        cid_path=resource_path.with_suffix('.cid')
        bound_id=resource.get('container_id') or (cid_path.read_text().strip() if cid_path.is_file() else None)
        container=bound_id or resource.get('container_name')
        if not container:raise ValueError('generation container identity not yet available')
        inspect=subprocess.run([*argv,'inspect',container],capture_output=True,text=True,timeout=20)
        if inspect.returncode:
            if not bound_id and ('No such object:' in inspect.stderr or 'No such container:' in inspect.stderr):
                item['status']='preparing'
                item['preparation']={'resource_state':resource.get('state'),'source':str(resource_path),'inspect_error':inspect.stderr}
                return item
            raise RuntimeError(f'Docker inspect exit {inspect.returncode}: {inspect.stderr}')
        physical=json.loads(inspect.stdout)[0]
        if physical['Image']!=resource['image_id'] or physical['Config']['Labels'].get('io.factory26.run')!=run.name:
            raise ValueError('generation image/run identity mismatch')
        item['physical']={'id':physical['Id'],'state':physical['State'],'image':physical['Image']}
        item['physical_running']=physical['State']['Running']
        if not physical['State']['Running']:
            item['status']='stopped_finalizing'
            return item
        if physical['State']['Paused']:
            item['status']='paused'
            return item
        code='exec('+repr(module_source)+')\n'+REMOTE
        response=subprocess.run([*argv,'exec','-i',physical['Id'],'python3','-',
            json.dumps([{'record':str(run/'run.json'),'state':record}])],input=code,text=True,capture_output=True,timeout=75)
        save(batch/(run.name+'-exec-receipt.json'),{'exit_code':response.returncode,'stderr':response.stderr})
        if response.returncode:raise RuntimeError(f'Docker exec exit {response.returncode}: {response.stderr}')
        captured=json.loads(response.stdout)[0]
        item.update(captured,physical=item['physical'],physical_running=True,observed_at=now)
        if not item['provider_sources']:
            item['status']='preparing'
            item['preparation']={'resource_state':resource.get('state'),'reason':'current top-level Braid status not created yet'}
    except Exception as error:
        item['observation_error']=f'{type(error).__name__}: {error}'
    return item


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--matrix',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--stale-after-seconds',type=int,default=1800)
    parser.add_argument('--minimum-samples',type=int,default=2)
    parser.add_argument('--once',action='store_true')
    args=parser.parse_args()
    if args.stale_after_seconds<=0 or args.minimum_samples<2:parser.error('positive threshold and at least two samples required')
    os.umask(0o077)
    output=args.output.resolve();monitor=output/'monitor';monitor.mkdir(parents=True,exist_ok=True)
    lock=(monitor/'lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    module_source=Path(__file__).with_name('provider_liveness.py').read_text()
    schedule=monitor/'scheduler.json'
    state=json.loads(schedule.read_text()) if schedule.exists() else {'done':[],'liveness':{},'notifications':{}}
    state.update(pid=os.getpid(),matrix=str(args.matrix.resolve()),module_sha256=hashlib.sha256(module_source.encode()).hexdigest(),model_invoked=False)
    save(schedule,state)
    while True:
        config=json.loads(args.matrix.read_text());runs=[Path(p) for p in config['runs']]
        pending=[run for run in runs if run.name not in state['done']]
        if not pending:break
        delay=state.get('next_at',0)-time.time()
        if delay>0:
            if args.once:break
            time.sleep(delay)
        batch=monitor/datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ');batch.mkdir()
        rows=[];verdicts=[]
        for run in pending:
            try:item=collect(run,batch,module_source)
            except Exception as error:item={'run_id':run.name,'observed_at':time.time(),'phase':'unknown','observation_error':f'{type(error).__name__}: {error}','files':{},'provider_sources':[]}
            dest=batch/run.name;dest.mkdir()
            for key,value in item.pop('files').items():
                path=Path(key)
                if path.is_absolute() or '..' in path.parts:raise ValueError('invalid evidence path')
                target=dest/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(base64.b64decode(value))
            sources=item.get('provider_sources',[])
            observation={'observed_at':item['observed_at'],'phase':item['phase'],'run_error':item.get('error'),
                'physical_running':item.get('physical_running'),'observation_error':item.get('observation_error'),
                'boundary':max([s['boundary'] for s in sources if s.get('boundary') is not None],default=item.get('started_at')),
                'sessions':[session for source in sources for session in source['sessions']],
                'errors':[error for source in sources for error in source['errors']],
                'provider_health':{group:health for source in sources for group,health in source.get('provider_health',{}).items()}}
            verdict=assess(observation,state['liveness'].get(run.name),stale_after=args.stale_after_seconds,min_samples=args.minimum_samples)
            if item.get('status') in ('paused','preparing'):
                verdict['classification']=item['status']
            state['liveness'][run.name]=verdict
            notice=transition(run.name,verdict,state['notifications'])
            if notice:alert(output,'provider_liveness',notice)
            item['evidence']=str(dest);item['model_invoked']=False
            save(dest/'collection.json',item);save(dest/'provider-observation.json',observation);save(dest/'liveness.json',verdict)
            rows.append(item);verdicts.append({'run_id':run.name,**verdict})
            if item['phase'] in TERMINAL:state['done'].append(run.name)
        save(batch/'outcome.json',{'runs':rows,'liveness':verdicts,'done':state['done'],'model_invoked':False})
        starts=[json.loads((run/'run.json').read_text()).get('started_at') for run in runs]
        earliest=min([stamp for stamp in starts if isinstance(stamp,(int,float))],default=time.time())
        state.update(last_batch=str(batch),last_completed_at=time.time(),next_at=time.time()+(180 if time.time()-earliest<600 else 480))
        save(schedule,state)
        print(json.dumps({'batch':str(batch),'states':{v['run_id']:v['classification'] for v in verdicts}},ensure_ascii=False),flush=True)
        if args.once:break
    if all(Path(p).name in state['done'] for p in json.loads(args.matrix.read_text())['runs']):
        save(monitor/'completion.json',{'finished_at':time.time(),'done':state['done'],'model_invoked':False})

if __name__=='__main__':main()
