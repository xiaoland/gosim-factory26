"""Run the authorized four-task submission through its isolated frozen executor."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT/'runs/pi-minimal-vv/20261003'


def save(path, value):
    temporary = path.with_suffix('.new')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')
    temporary.replace(path)


def cli(arguments, name):
    environment = dict(os.environ, PYTHONPATH=str(OUT/'executor-source'),
                       PYTHONDONTWRITEBYTECODE='1', TMPDIR=str(OUT/'tmp'))
    with (OUT/(name+'.stdout')).open('w') as output, (OUT/(name+'.stderr')).open('w') as errors:
        result = subprocess.run([sys.executable, '-B', '-m', 'lab', *arguments],
                                cwd=OUT/'executor-source', env=environment, stdout=output, stderr=errors)
    if result.returncode:
        raise RuntimeError(f'{name} exited {result.returncode}; see saved stderr')


def attempts(experiment):
    return sorted(path.parent for path in (experiment/'attempts').glob('*/attempt.json'))


def guard_available():
    if (OUT/'budget-stop.json').exists():
        return False
    state = json.loads((OUT/'budget-state.json').read_text())
    os.kill(state['pid'], 0)
    return time.time()-state['checked_at'] < 180 and state['cost_status']=='known'


def main():
    registry = json.loads((OUT/'registry.json').read_text())
    save(OUT/'queue-process.json', {'pid':os.getpid(), 'started_at':time.time()})
    ready = OUT/'guard-ready.json'
    guard_pid = None
    if ready.exists():
        candidate = json.loads(ready.read_text())['pid']
        try:
            os.kill(candidate, 0)
            guard_pid = candidate
        except ProcessLookupError:
            pass
    if guard_pid is None:
        with (OUT/'budget-guard.log').open('a') as log:
            guard = subprocess.Popen([sys.executable, '-B', str(Path(__file__).with_name('budget_guard.py')), str(OUT)],
                                     cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, start_new_session=True,
                                     env=dict(os.environ, TMPDIR=str(OUT/'tmp'), PYTHONDONTWRITEBYTECODE='1'))
        guard_pid = guard.pid
        save(OUT/'budget-guard-process.json', {'pid':guard_pid, 'started_at':time.time()})
    deadline = time.monotonic()+30
    while not ready.exists():
        os.kill(guard_pid, 0)
        if time.monotonic()>deadline:
            raise RuntimeError('independent budget guard did not become ready')
        time.sleep(.5)
    previous = None
    for item in registry['tasks']:
        if not guard_available():
            save(OUT/'queue-complete.json', {'status':'budget-blocked','at':time.time()})
            return
        task = item['task'].removeprefix('hackathon--')
        recipe = Path(registry['definition'])/(task+'.json')
        if previous:
            prior = json.loads((previous/'execution.json').read_text())
            reference = {'source_attempt':str(previous), 'submission_id':prior['submission_id'],
                         'source_attempt_sha256':hashlib.sha256((previous/'attempt.json').read_bytes()).hexdigest()}
            reference_path = OUT/(task+'-submission-reference.json')
            save(reference_path,reference)
            specification = json.loads(recipe.read_text())
            next(iter(specification['cases'].values()))['inputs']['submission_reference']={'source':str(reference_path)}
            save(recipe,specification)
        experiment = Path(item['experiment'])
        bundle = Path(registry['definition'])/(task+'-compiled')
        cli(['compile',str(recipe),'--environment',str(Path(registry['definition'])/'environment.json'),
             '--directory',str(bundle)],task+'-compile')
        cli(['build',str(bundle/'recipe.json'),'--directory',str(experiment),'--job',item['job']],task+'-build')
        if not guard_available():
            save(OUT/'queue-complete.json', {'status':'budget-blocked','at':time.time()})
            return
        save(OUT/'queue-state.json', {'phase':'starting','task':item['task'],'at':time.time()})
        cli(['start',str(experiment),'--job',item['job'],'--request-id',item['request_id'],
             '--deployment',registry['deployment']],task+'-start')
        owned = attempts(experiment)
        if len(owned)!=1:
            raise RuntimeError('explicit request did not produce one unique attempt')
        previous = owned[0]
        save(OUT/'queue-state.json', {'phase':'running','task':item['task'],'attempt':str(previous),'at':time.time()})
        print(json.dumps({'task':item['task'],'attempt':previous.name}),flush=True)
        while True:
            state = json.loads((previous/'execution.json').read_text())
            if state.get('remote_status') in {'PASSED','FAILED','CANCELLED'}:
                save(OUT/(task+'-terminal.json'),state.get('platform_result'))
                break
            try:
                os.kill(guard_pid, 0)
            except ProcessLookupError:
                cli(['control',str(experiment),previous.name,'stop',
                     '--request-id','pivv-guard-lost-'+previous.name],task+'-guard-lost-stop')
                raise RuntimeError('budget guard exited; own current task stop requested')
            time.sleep(15)
    save(OUT/'queue-complete.json', {'status':'four-tasks-terminal','at':time.time()})
    print('Four registered tasks reached terminal status.',flush=True)


if __name__=='__main__':
    try:
        main()
    except Exception as error:
        save(OUT/'queue-error.json', {'at':time.time(),'error':str(error),'type':type(error).__name__,
                                    'policy':'no automatic repeat of unknown platform writes; independent guard retained'})
        raise
