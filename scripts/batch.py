"""Fixed experiment matrix with separate generation/evaluation capacity."""
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
import fcntl
import json
from pathlib import Path
import time

import factory
import profiles
import sources
from run_feedback import collect, monitor


def complete(run, outcome, error=None):
    outcome['stage'] = 'analysis'
    factory.save(run/'outcome.json', outcome)
    if (run/'native/manifest.json').is_file():
        try:
            factory.analyze(run)
            outcome['analysis'] = {'status':'completed'}
        except Exception as exc:
            outcome['analysis'] = {'status':'failed', 'error':{'type':type(exc).__name__, 'message':str(exc)}}
    else:
        outcome['analysis'] = {'status':'unavailable', 'reason':'No native manifest'}
    outcome.update(status='failed' if error else 'completed', finished_at=time.time())
    factory.save(run/'outcome.json', outcome)
    return collect(run)


def generate(job, directory):
    run = directory/job['run_id']
    run.mkdir()
    config = job['config']
    outcome = dict(schema_version=1, run_id=run.name, variant=job['variant'], task=job['task'],
                   backend=config['backend'], status='running', stage='generation', started_at=time.time(),
                   finished_at=None, error=None, analysis={'status':'pending'}, evaluation_id=None)
    factory.save(run/'outcome.json', outcome)
    with monitor(run):
        try:
            factory.generate(config, run)
            outcome['stage'] = 'evaluation-queued'
            factory.save(run/'outcome.json', outcome)
            return {'status':'generated'}
        except Exception as exc:
            outcome.update(failed_stage='generation', error={'type':type(exc).__name__, 'message':str(exc)})
            return dict(complete(run, outcome, exc), pause_queue=True)


def evaluate(job, directory):
    run = directory/job['run_id']
    outcome = json.loads((run/'outcome.json').read_text())
    outcome.update(stage='evaluation', evaluation_id=factory.evaluation_id())
    factory.save(run/'outcome.json', outcome)
    error = None
    with monitor(run):
        try:
            factory.evaluate(run, outcome['evaluation_id'])
        except Exception as exc:
            error = exc
            outcome.update(failed_stage='evaluation', error={'type':type(exc).__name__, 'message':str(exc)})
        result = complete(run, outcome, error)
    summary_file = run/'evaluation'/outcome['evaluation_id']/'summary.json'
    summary = json.loads(summary_file.read_text()) if summary_file.is_file() else {}
    result['evaluation'] = summary
    # A broken application is an experimental result. Missing evaluation identity
    # or setup/protocol evidence is a facility failure, so do not spread it.
    result['pause_queue'] = bool(error and summary.get('failed_phase') not in ('install','build','start','health','test'))
    return result


def execute(manifest, directory):
    """Resume only queued work or already-frozen generation; never rerun a terminal."""
    manifest = Path(manifest).resolve()
    directory = Path(directory).resolve()
    directory.mkdir(parents=True, exist_ok=True)
    with (directory/'controller.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        spec = json.loads(manifest.read_text())
        jobs = []
        for variant in spec['variants']:
            for task in spec['tasks']:
                config = profiles.configuration(variant, task)
                if config['benchmark_revision'] != spec['benchmark_revision']:
                    raise ValueError('batch runner revision differs from resolved configuration')
                jobs.append(dict(run_id=f'{variant}-{task}', variant=variant, task=task, config=config))
        if len(spec['variants']) != 4 or len(spec['tasks']) != 2 or len(jobs) != 8:
            raise ValueError('batch 必须是固定的 4 个 variant × 2 个 task')
        if not 1 <= spec['generation_workers'] <= 2:
            raise ValueError('generation_workers 必须在 1..2 内')
        if not 1 <= spec['evaluation_workers'] <= 4:
            raise ValueError('evaluation_workers 必须在 1..4 内')
        inputs = {'manifest':spec, 'jobs':jobs, 'source_inputs':{name:sources.require_build(name) for name in ('svc','braid')},
                  'runner':factory.hashes(factory.ROOT/'scripts'), 'requirements':{
            task:factory.hashes(factory.BENCH/'arc-bench/webapp'/task/'requirements') for task in spec['tasks']}}
        frozen = directory/'inputs.json'
        if frozen.exists():
            if json.loads(frozen.read_text()) != inputs:
                raise ValueError('batch inputs changed; refusing to resume with another configuration')
        else:
            factory.save(frozen, inputs)
        state_file = directory/'batch.json'
        state = json.loads(state_file.read_text()) if state_file.exists() else {
            'schema_version':1, 'input_digest':factory.digest(inputs), 'status':'running',
            'jobs':{j['run_id']:{'status':'queued'} for j in jobs}}
        if state.get('input_digest') != factory.digest(inputs):
            raise ValueError('batch state inputs changed; refusing to resume')
        for job in jobs:
            row = state['jobs'][job['run_id']]
            if row['status'] in ('generating','evaluating'):
                # The exclusive lock proves no previous controller exists, but
                # does not prove detached model/tool processes have stopped.
                row.update(status='unknown', reason='controller interrupted; inspect the existing run before recovery')
        if any(r['status']=='unknown' for r in state['jobs'].values()):
            state['status']='blocked'
            factory.save(state_file, state)
            return state
        state['status']='running'
        pending = [j for j in jobs if state['jobs'][j['run_id']]['status']=='queued']
        generated = [j for j in jobs if state['jobs'][j['run_id']]['status']=='generated']
        futures = {}
        paused = False
        with ThreadPoolExecutor(max_workers=spec['generation_workers']) as generators, \
             ThreadPoolExecutor(max_workers=spec['evaluation_workers']) as evaluators:
            def submit(job, stage):
                row = state['jobs'][job['run_id']]
                row['status'] = 'generating' if stage=='generate' else 'evaluating'
                factory.save(state_file, state)
                executor = generators if stage=='generate' else evaluators
                futures[executor.submit(generate if stage=='generate' else evaluate, job, directory)] = (job,stage)
            for job in generated:
                submit(job,'evaluate')
            while pending or futures:
                active = sum(stage=='generate' for _,stage in futures.values())
                # Drain an already-completed future before filling a slot. This
                # prevents a failure that completed beside another future from
                # allowing one more queued writer to start first.
                while pending and not paused and active < spec['generation_workers'] \
                        and not any(future.done() for future in futures):
                    submit(pending.pop(0),'generate'); active += 1
                if not futures:
                    break
                done, _ = wait(futures, return_when=FIRST_COMPLETED)
                for future in done:
                    job, stage = futures.pop(future)
                    row = state['jobs'][job['run_id']]
                    try:
                        result = future.result()
                    except Exception as exc:
                        result = {'status':'unknown', 'pause_queue':True, 'error':str(exc)}
                    row.update(status=result['status'], result=result)
                    paused = paused or result.get('pause_queue',False)
                    factory.save(state_file, state)
                    if stage=='generate' and result['status']=='generated':
                        submit(job,'evaluate')
                    else:
                        print(json.dumps({'job':job['run_id'], 'status':row['status'],
                                          'evidence':str(directory/job['run_id'])},ensure_ascii=False),flush=True)
        state.update(status='paused' if pending or paused else 'completed', updated_at=time.time())
        factory.save(state_file,state)
        return state
