"""Monitor hosted journals every 3 minutes initially, then every 8 minutes; collect terminal evidence and exit."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
import zipfile
from .playground import Client, COOKIE, TERMINAL, save, polling_interval

ROOT=Path(__file__).resolve().parents[2]
PROMPT=ROOT/'agents/run-monitor.md'
COMPETITIONS=('arc-bench-lite','hackathon')
SCHEMA={'type':'object','properties':{'reviews':{'type':'array','items':{'type':'object','properties':{
    'run_id':{'type':'string'},'classification':{'type':'string','enum':['progress','waiting','needs_review','confirmed_stall','harness_failure','completed']},
    'observations':{'type':'array','items':{'type':'object','properties':{'source':{'type':'string'},'quote':{'type':'string'},'significance':{'type':'string'}},'required':['source','quote','significance'],'additionalProperties':False}},'inspected_paths':{'type':'array','items':{'type':'string'}},'summary':{'type':'string'},'evidence':{'type':'array','items':{'type':'string'}},
    'recommended_action':{'type':'string','enum':['continue','cancel_hackathon','review']},'needs_decision':{'type':'boolean'}},
    'required':['run_id','classification','observations','inspected_paths','summary','evidence','recommended_action','needs_decision'],'additionalProperties':False}}},'required':['reviews'],'additionalProperties':False}

def alert(base,kind,data):
    record={'time':time.time(),'kind':kind,**data}
    message=f'Factory26: {kind}，查看 {base}/monitor/alerts.jsonl'
    # A successful OS call confirms submission, not human receipt.
    result=subprocess.run(['osascript','-e','display notification '+json.dumps(message,ensure_ascii=False)+' with title "Factory26"'],capture_output=True,text=True)
    record['desktop_notification']={'exit_code':result.returncode,'error':result.stderr.strip(),'human_seen':'unknown'}
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
        row['evaluation_started_at']=status.get('evaluation_started_at')
        row['poll_interval']=polling_interval(status)
        row['score']={key:status.get(key) for key in ('score','passed_count','failed_count',
            'feature_implemented_count','feature_total_count','token_cost_usd')}
        row['stages']={step['key']:step.get('status') for step in status.get('steps',[]) if 'key' in step}
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
                            if item.filename.endswith('/braid-state/status.json'):
                                braid_status.append(target)
                            if 'native-homes' in path.parts and path.suffix=='.jsonl':
                                native_sessions[path.parts[path.parts.index('.factory26'):]]=target
            save(dest/'archive-index.json',index)
            row['session_evidence']=session_evidence(braid_status,native_sessions)
            row['required_reads']=list(dict.fromkeys([str(path) for path in braid_status]
                + [session['path'] for session in row['session_evidence'] if session['path']]))
        except Exception as e:row['workspace_error']=str(e)
    except Exception as e:row['observation_error']=str(e)
    row['finished_at']=time.time();save(dest/'collection.json',row)
    return row

def review(base,batch,rows,previous):
    prompt=PROMPT.read_text();(batch/'instructions.md').write_text(prompt)
    settings=dict(line.split(': ',1) for line in prompt.split('---',2)[1].splitlines() if ': ' in line)
    model=settings['model'];effort=settings['reasoning_effort']
    save(batch/'schema.json',SCHEMA)
    save(batch/'batch.json',{'runs':rows,'previous_reviews':previous,'package':str(base/'package.json')})
    command=['codex','exec','--ephemeral','--skip-git-repo-check','-C',str(ROOT),'-m',model,'-c',f'model_reasoning_effort="{effort}"',
             '--dangerously-bypass-approvals-and-sandbox','--json','--output-schema',str(batch/'schema.json'),'--output-last-message',str(batch/'review.json'),'-']
    message=f'读取并遵循固定审查指令 {batch}/instructions.md（源 {PROMPT}）。本次只审查 {batch}/batch.json 指定的新证据；完成即退出。不要开展本项目其他工作。'
    receipt={'model':model,'reasoning':effort,'instructions_sha256':hashlib.sha256(prompt.encode()).hexdigest(),'started_at':time.time(),'state':'starting'}
    save(batch/'review-execution.json',receipt)
    with (batch/'review-events.jsonl').open('w') as out,(batch/'review-stderr.log').open('w') as err:
        process=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=out,stderr=err,text=True)
        receipt.update(pid=process.pid,state='running');save(batch/'review-execution.json',receipt)
        process.communicate(message)
    receipt.update(exit_code=process.returncode,finished_at=time.time(),state='completed' if process.returncode==0 else 'failed')
    save(batch/'review-execution.json',receipt)
    if process.returncode:raise RuntimeError(f'reviewer exited {process.returncode}; {batch}/review-stderr.log')
    result=json.loads((batch/'review.json').read_text())
    expected={r['run_id'] for r in rows}
    if {r['run_id'] for r in result['reviews']}!=expected:raise RuntimeError('review does not cover exactly the collected run IDs')
    required={r['run_id']:set(r.get('required_reads',[])) for r in rows}
    for verdict in result['reviews']:
        missing=required[verdict['run_id']]-set(verdict['inspected_paths'])
        if missing:raise RuntimeError(f'review omitted required evidence: {sorted(missing)}')
        # Quotations of parsed JSON need not match its escaped bytes. Preserve the
        # observations and tool transcript for content review, rather than reject
        # a useful alert on formatting and thereby hide the reported failure.
        if not verdict['observations']:
            raise RuntimeError('review lacks content observations')
    return result['reviews']

def cancel_hackathon(base,trigger):
    journal=base/'hackathon/state.json'
    if not journal.exists():return
    client=Client();state=json.loads(journal.read_text())
    for task,item in state['tasks'].items():
        rid=item.get('run_id')
        if not rid:continue
        result={'run_id':rid,'task':task,'trigger':trigger,'time':time.time()}
        try:
            before=client.request('/runs/'+rid);before=before.get('run',before)
            if before.get('submission_id')!=state['submission_id']:raise RuntimeError('run submission differs from this journal')
            result['before']=before.get('status')
            if before.get('status') not in TERMINAL:
                result['response']=client.request('/runs/'+rid+'/cancel',method='POST')
                after=client.request('/runs/'+rid);after=after.get('run',after);result['after']=after.get('status')
                result['confirmed']=after.get('status')=='CANCELLED'
            else:result['already_terminal']=True
        except Exception as e:result['error']=str(e)
        save(base/'monitor'/('cancel-'+rid+'.json'),result)
        alert(base,'hackathon_cancel_result',result)

def run_batch(base,journals,state,*,semantic_review=False,cancel_on_lite_failure=False):
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    batch=base/'monitor'/stamp;batch.mkdir(parents=True)
    jobs=[]
    for path in journals:
        journal=json.loads((path/'state.json').read_text())
        comp=journal['competition_id']
        jobs += [(comp,task,item['run_id']) for task,item in journal['tasks'].items() if item.get('run_id') and item['run_id'] not in state['done']]
    with ThreadPoolExecutor(max_workers=4) as pool:
        rows=list(pool.map(lambda x:collect(base,*x,batch,with_workspace=semantic_review),jobs))
    # FAILED also means a scored application failed scenarios, not a harness failure.
    failures=[r for r in rows if r['competition']=='arc-bench-lite' and r.get('status')=='FAILED'
              and any(r.get('stages',{}).get(stage)=='failed' for stage in ('deploy_agent','start_agent'))]
    if failures and cancel_on_lite_failure:cancel_hackathon(base,{'type':'lite_failed','runs':failures})
    if rows and semantic_review:
        try:
            reviews=review(base,batch,rows,state.get('reviews',[]))
            state.setdefault('reviews',[]).append(str(batch/'review.json'))
            lite={r['run_id'] for r in rows if r['competition']=='arc-bench-lite'}
            triggers=[r for r in reviews if r['run_id'] in lite and r['recommended_action']=='cancel_hackathon' and r['classification'] in {'confirmed_stall','harness_failure'} and r['evidence']]
            if triggers and not failures and cancel_on_lite_failure:cancel_hackathon(base,{'type':'semantic_review','reviews':triggers,'source':str(batch/'review.json')})
            alerts=[r for r in reviews if r['classification'] not in {'progress','waiting'}]
            if alerts:alert(base,'review_result',{'reviews':alerts,'path':str(batch/'review.json')})
        except Exception as e:alert(base,'review_failed',{'error':str(e),'batch':str(batch)})
    for row in rows:
        if row.get('status') in TERMINAL:
            state['done'].append(row['run_id'])
            if row.get('workspace_error'):
                state.setdefault('evidence_errors',{})[row['run_id']]=row['workspace_error']
            alert(base,'terminal',row)
        elif row.get('observation_error'):
            alert(base,'observation_failed',row)
    save(batch/'outcome.json',{'runs':rows,'done':state['done']})
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
    p.add_argument('--review',action='store_true',help='Download live workspaces and request one-shot semantic review')
    p.add_argument('--observe-only',action='store_true',help='Compatibility: observations are now the default')
    p.add_argument('--cancel-on-lite-failure',action='store_true',help='Explicitly authorized cancellation of sibling Hackathon runs')
    p.add_argument('--competition',action='append',choices=list(COMPETITIONS))
    a=p.parse_args()
    if a.observe_only and a.cancel_on_lite_failure:
        p.error('--observe-only conflicts with --cancel-on-lite-failure')
    if a.journal and a.cancel_on_lite_failure:
        p.error('sibling cancellation requires the legacy directory/hackathon journal layout')
    base=a.directory.resolve();(base/'monitor').mkdir(parents=True,exist_ok=True)
    lock=(base/'monitor/lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    journals=[path.resolve() for path in a.journal] if a.journal else [base/c for c in (a.competition or COMPETITIONS) if (base/c/'state.json').exists()]
    if not journals:p.error('no existing run journals found')
    path=base/'monitor/scheduler-v2.json'
    state=json.loads(path.read_text()) if path.exists() else {'done':[],'reviews':[],'next':{}}
    state.update(pid=os.getpid(),journals=[str(j) for j in journals],semantic_review=a.review)
    save(path,state)
    while True:
        active=[]
        for journal in journals:
            items=json.loads((journal/'state.json').read_text())['tasks'].values()
            if any(i.get('run_id') and i['run_id'] not in state['done'] for i in items):active.append(journal)
        if not active:break
        due=[j for j in active if state['next'].get(str(j),0)<=time.time()]
        if due:
            run_batch(base,due,state,semantic_review=a.review,cancel_on_lite_failure=a.cancel_on_lite_failure)
            save(path,state)
            if a.once:break
        elif a.once:break
        else:time.sleep(max(1,min(state['next'][str(j)] for j in active)-time.time()))
    state['finished_at']=time.time();save(path,state)
    print(json.dumps({'done':state['done'],'state':str(path)},ensure_ascii=False),flush=True)

if __name__=='__main__':main()
