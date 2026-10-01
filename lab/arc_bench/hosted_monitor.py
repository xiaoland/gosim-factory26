"""Read hosted run/provider evidence at 3+8 intervals; notify script liveness changes and exit at terminal."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import datetime
import fcntl
import json
import os
from pathlib import Path
import subprocess
import time
import zipfile
from .playground import COOKIE, TERMINAL, save, polling_interval
from .provider_liveness import assess, collect_provider_evidence, epoch, transition

COMPETITIONS=('arc-bench-lite','hackathon')

def alert(base,kind,data):
    record={'time':time.time(),'kind':kind,**data}
    message=f'Factory26: {kind}，查看 {base}/monitor/alerts.jsonl'
    # A successful OS call confirms submission, not human receipt.
    try:
        result=subprocess.run(['osascript','-e','display notification '+json.dumps(message,ensure_ascii=False)+' with title "Factory26"'],capture_output=True,text=True,timeout=10)
        record['desktop_notification']={'exit_code':result.returncode,'error':result.stderr.strip(),'human_seen':'unknown'}
    except (OSError, subprocess.TimeoutExpired) as error:
        record['desktop_notification']={'error':str(error),'human_seen':'unknown'}
    with (base/'monitor/alerts.jsonl').open('a') as f:f.write(json.dumps(record,ensure_ascii=False)+'\n')

def download(path,target):
    r=subprocess.run(['curl','-q','-sS','--retry','1','--connect-timeout','30','--max-time','600','--cookie',str(COOKIE),
                      '--output',str(target),'--write-out','%{http_code}','https://arc-bench.com/api'+path],capture_output=True,text=True,timeout=1250)
    if r.returncode or r.stdout!='200':raise RuntimeError(f'HTTP {r.stdout}; curl {r.returncode}; {r.stderr[:500]}')

def session_evidence(braid_status,native_sessions):
    """Bind native files to the work items in Braid's current physical sessions."""
    rows=[]
    for source in braid_status:
        for session in json.loads(source.read_text()).get('physical_sessions',[]):
            parts=Path(session.get('native_session_path') or '').parts
            key=parts[parts.index('.factory26'):] if '.factory26' in parts else None
            target=native_sessions.get(key)
            rows.append({**{name:session.get(name) for name in
                ('work_item_kind','work_item_id','profile_id','status','native_session_id')},
                'source':str(source),'path':str(target) if target else None})
    return rows

def collect(base,comp,task,rid,batch,with_workspace=True):
    dest=batch/rid;dest.mkdir()
    row={'run_id':rid,'competition':comp,'task':task,'evidence':str(dest),'started_at':time.time()}
    try:
        download('/runs/'+rid,dest/'status.json')
        status=json.loads((dest/'status.json').read_text());status=status.get('run',status)
        row['status']=status.get('status');row['failure_reason']=status.get('failure_reason')
        row['boundary']=epoch(status.get('started_at') or status.get('created_at'))
        row['evaluation_started_at']=status.get('evaluation_started_at')
        row['poll_interval']=polling_interval(status)
        row['score']={key:status.get(key) for key in ('score','passed_count','failed_count',
            'feature_implemented_count','feature_total_count','token_cost_usd')}
        row['stages']={step['key']:step.get('status') for step in status.get('steps',[]) if 'key' in step}
        if row['status']=='QUEUED' or (row['status'] not in TERMINAL
                and row['stages'].get('start_agent')=='pending'
                and row['stages'].get('deploy_agent') in ('pending','running','completed')):
            row['preparing']=True
            row['finished_at']=time.time();save(dest/'collection.json',row)
            return row
        if not with_workspace and row['status'] not in TERMINAL:
            row['finished_at']=time.time();save(dest/'collection.json',row)
            return row
        try:
            download('/runs/'+rid+'/workspace/template-bundle',dest/'workspace.zip')
            index=[]
            braid_status=[]
            native_sessions={}
            with zipfile.ZipFile(dest/'workspace.zip') as z:
                for item in z.infolist():
                    path=Path(item.filename)
                    if item.is_dir():continue
                    index.append({'path':item.filename,'bytes':item.file_size})
                    if not path.is_absolute() and '..' not in path.parts and '.factory26' in path.parts and not any(x in path.parts for x in ['node_modules','runtime','.cache']):
                        if path.suffix in {'.jsonl','.json','.md','.log','.sqlite3'} or path.name.endswith(('.sqlite3-wal','.sqlite3-shm')):
                            target=dest/'evidence'/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(item))
                            if (len(path.parts)==5 and path.parts[:2]==('template','.factory26')
                                    and path.parts[3:]==('braid-state','status.json')):
                                braid_status.append(target)
                            if 'native-homes' in path.parts and path.suffix=='.jsonl':
                                native_sessions[path.parts[path.parts.index('.factory26'):]]=target
            save(dest/'archive-index.json',index)
            row['session_evidence']=session_evidence(braid_status,native_sessions)
            observed=time.time()
            sources=[collect_provider_evidence(path.parent,observed,row['boundary'],exported=True) for path in braid_status]
            provider_phase=row['status']
            if row['status'] not in TERMINAL and row.get('evaluation_started_at'):
                provider_phase='finalizing'
            row['provider_observation']={'observed_at':observed,'phase':provider_phase,
                'run_error':row.get('failure_reason'),'boundary':max([v for v in [row['boundary'],*[s.get('boundary') for s in sources]] if v is not None],default=None),
                'sessions':[item for source in sources for item in source['sessions']],
                'errors':[error for source in sources for error in source['errors']],
                'provider_health':{group:health for source in sources for group,health in source.get('provider_health',{}).items()}, 'sources':sources}
            save(dest/'provider-observation.json',row['provider_observation'])
            if not sources and row['status'] not in TERMINAL:
                row['preparing']=True
            row['required_reads']=list(dict.fromkeys([str(path) for path in braid_status]
                + [session['path'] for session in row['session_evidence'] if session['path']]))
        except Exception as e:row['workspace_error']=str(e)
    except Exception as e:row['observation_error']=str(e)
    row['finished_at']=time.time();save(dest/'collection.json',row)
    return row

def run_batch(base,journals,state,*,stale_after=1800,min_samples=2):
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    batch=base/'monitor'/stamp;batch.mkdir(parents=True)
    jobs=[]
    for path in journals:
        journal=json.loads((path/'state.json').read_text())
        comp=journal['competition_id']
        jobs += [(comp,task,item['run_id']) for task,item in journal['tasks'].items() if item.get('run_id') and item['run_id'] not in state['done']]
    with ThreadPoolExecutor(max_workers=4) as pool:
        rows=list(pool.map(lambda x:collect(base,*x,batch,with_workspace=True),jobs))
    assessments=[]
    for row in rows:
        rid=row['run_id']
        observation=row.get('provider_observation') or {'observed_at':row['finished_at'],
            'phase':row.get('status'),'run_error':row.get('failure_reason'),'sessions':[],
            'errors':[], 'observation_error':row.get('observation_error') or row.get('workspace_error')}
        verdict=assess(observation,state.setdefault('liveness',{}).get(rid),stale_after=stale_after,min_samples=min_samples)
        if row.get('preparing') and not state['liveness'].get(rid,{}).get('sessions'):
            verdict['classification']='preparing'
        state['liveness'][rid]=verdict
        save(Path(row['evidence'])/'liveness.json',verdict)
        assessments.append({'run_id':rid,**verdict})
        notice=transition(rid,verdict,state.setdefault('notifications',{}))
        if notice:alert(base,'provider_liveness',notice)
        if row.get('status') in TERMINAL:
            state['done'].append(rid)
            if row.get('workspace_error'):
                state.setdefault('evidence_errors',{})[rid]=row['workspace_error']
    save(batch/'outcome.json',{'runs':rows,'liveness':assessments,'done':state['done'],'model_invoked':False})
    for path in journals:
        journal=json.loads((path/'state.json').read_text())
        ids={item.get('run_id') for item in journal['tasks'].values()}
        intervals=[r.get('poll_interval',180) for r in rows if r['run_id'] in ids and r['run_id'] not in state['done']]
        state['next'][str(path)]=time.time()+min(intervals,default=480)
    return batch

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('directory',type=Path)
    p.add_argument('--journal',type=Path,action='append',help='Existing competition journal; repeat for independent runs')
    p.add_argument('--once',action='store_true')
    p.add_argument('--review',action='store_true',help='Compatibility: provider evidence and script liveness only; never invokes a model')
    p.add_argument('--observe-only',action='store_true',help='Compatibility: observations are now the default')
    p.add_argument('--cancel-on-lite-failure',action='store_true',help='Removed: monitoring never cancels runs')
    p.add_argument('--stale-after-seconds',type=int,default=1800)
    p.add_argument('--minimum-samples',type=int,default=2)
    p.add_argument('--competition',action='append',choices=list(COMPETITIONS))
    a=p.parse_args()
    if a.cancel_on_lite_failure:
        p.error('--cancel-on-lite-failure is removed; monitoring is read-only')
    if a.stale_after_seconds<=0 or a.minimum_samples<2:
        p.error('stale threshold must be positive and minimum samples must be at least 2')
    os.umask(0o077)
    base=a.directory.resolve();(base/'monitor').mkdir(parents=True,exist_ok=True)
    lock=(base/'monitor/lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    journals=[path.resolve() for path in a.journal] if a.journal else [base/c for c in (a.competition or COMPETITIONS) if (base/c/'state.json').exists()]
    if not journals:p.error('no existing run journals found')
    path=base/'monitor/scheduler-v2.json'
    state=json.loads(path.read_text()) if path.exists() else {'done':[],'reviews':[],'next':{}}
    state.update(pid=os.getpid(),journals=[str(j) for j in journals],semantic_review=False,model_invoked=False,
                 stale_after_seconds=a.stale_after_seconds,minimum_samples=a.minimum_samples)
    save(path,state)
    while True:
        active=[]
        for journal in journals:
            items=json.loads((journal/'state.json').read_text())['tasks'].values()
            if any(i.get('run_id') and i['run_id'] not in state['done'] for i in items):active.append(journal)
        if not active:break
        due=[j for j in active if state['next'].get(str(j),0)<=time.time()]
        if due:
            run_batch(base,due,state,stale_after=a.stale_after_seconds,min_samples=a.minimum_samples)
            save(path,state)
            if a.once:break
        elif a.once:break
        else:time.sleep(max(1,min(state['next'][str(j)] for j in active)-time.time()))
    state['finished_at']=time.time();save(path,state)
    print(json.dumps({'done':state['done'],'state':str(path)},ensure_ascii=False),flush=True)

if __name__=='__main__':main()
