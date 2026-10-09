"""Guard only the four explicitly registered competition attempts."""
import argparse
import json
import math
import os
from pathlib import Path
import subprocess
import time

TERMINAL = {'PASSED', 'FAILED', 'CANCELLED'}


def save(path, value):
    temporary = path.with_suffix('.new')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    temporary.replace(path)


def executor(experiment):
    manifest = json.loads((experiment/'experiment.json').read_text())
    source = experiment/'artifacts'/manifest['code']['artifact_id']/'payload'
    environment = dict(os.environ, PYTHONPATH=str(source), PYTHONDONTWRITEBYTECODE='1')
    return manifest['controller_runtime']['launcher'], source, environment


def observe(experiment, attempt):
    python, source, environment = executor(experiment)
    code = ('import json,sys;from lab.exp.hosted import observe_identity;'
            'd=observe_identity(sys.argv[1],live=True);'
            'print(json.dumps({k:d.get(k) for k in '
            "['run_id','submission_id','remote_status','platform_result','observation_error','pending']}))")
    result = subprocess.run([python, '-B', '-c', code, str(attempt)],
                            cwd=source, env=environment, capture_output=True, text=True, timeout=55)
    if result.returncode:
        raise RuntimeError(result.stderr[-4000:])
    return json.loads(result.stdout)


def check(root, previous):
    registry = json.loads((root/'registry.json').read_text())
    rows, gaps = [], []
    history = dict(previous.get('runs', {}))
    for item in registry['tasks']:
        experiment = Path(item['experiment'])
        if not (experiment/'experiment.json').exists():
            continue
        for attempt in (experiment/'attempts').glob('*/attempt.json'):
            attempt = attempt.parent
            old = history.get(attempt.name, {})
            try:
                state = observe(experiment, attempt)
                value = state.get('platform_result') or {}
                if not state.get('run_id'):
                    continue
                if value.get('requirement_id') != item['task'] or value.get('submission_id') != state['submission_id']:
                    raise ValueError('run/task/submission identity mismatch')
                raw, currency = value.get('token_cost_usd'), value.get('token_cost_currency')
                row = dict(old, attempt_id=attempt.name, experiment=str(experiment), task=item['task'],
                           run_id=state['run_id'], submission_id=state['submission_id'],
                           status=value.get('status'), observed_at=time.time(), pending=state.get('pending'))
                if raw is not None and currency == 'CNY':
                    cost = float(raw)
                    if not math.isfinite(cost) or cost < 0:
                        raise ValueError('non-finite or negative platform cost')
                    row.update(cost_cny=max(cost, old.get('cost_cny', 0)), cost_observed_at=time.time(), cost_status='known')
                    row.pop('unknown_since', None)
                elif value.get('started_at'):
                    row.update(cost_status='unknown', cost_gap=f'cost={raw!r}, currency={currency!r}')
                    row.setdefault('unknown_since', time.time())
                    gaps.append(row['cost_gap'])
                else:
                    row.update(cost_status='not-started')
                history[attempt.name] = row
                rows.append(row)
            except Exception as error:
                gaps.append(str(error))
                if old:
                    row = dict(old, cost_status='unknown', error=str(error))
                    row.setdefault('unknown_since', time.time())
                    history[attempt.name] = row
                    rows.append(row)
    total = sum(row.get('cost_cny', 0) for row in history.values())
    reason = 'total_cost_above_limit' if total > registry['limit_cny'] else None
    if not reason and any(row.get('status') not in TERMINAL and row.get('cost_status') == 'unknown'
                          and time.time()-row.get('unknown_since', time.time()) > 180 for row in rows):
        reason = 'active_cost_observation_unavailable'
    state = {'checked_at': time.time(), 'limit_cny': registry['limit_cny'], 'currency': 'CNY',
             'total_known_cost_cny': total, 'cost_status': 'unknown' if gaps else 'known',
             'gaps': gaps, 'runs': history, 'stopped': bool(reason or previous.get('stopped')),
             'stop_reason': reason or previous.get('stop_reason'), 'pid': os.getpid()}
    save(root/'budget-state.json', state)
    if state['stopped']:
        save(root/'budget-stop.json', state)
        for row in history.values():
            if row.get('status') in TERMINAL or row.get('stop_requested'):
                continue
            experiment = Path(row['experiment'])
            python, source, environment = executor(experiment)
            request = 'pivv-budget-stop-' + row['attempt_id']
            with (root/(request+'.log')).open('a') as log:
                result = subprocess.run([python, '-B', '-m', 'lab', 'control', str(experiment),
                                         row['attempt_id'], 'stop', '--request-id', request],
                                        cwd=source, env=environment, stdout=log, stderr=subprocess.STDOUT)
            row.update(stop_requested=True, stop_request_id=request, stop_command_exit=result.returncode)
        save(root/'budget-state.json', state)
    return state


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    args = parser.parse_args()
    root = args.directory.resolve(strict=True)
    if not root.is_relative_to(Path('/Volumes/WorkSSD').resolve()):
        raise ValueError('Mac budget records must reside on WorkSSD')
    previous = {}
    while True:
        previous = check(root, previous)
        if not (root/'guard-ready.json').exists():
            save(root/'guard-ready.json', {'pid': os.getpid(), 'at': time.time(), 'limit_cny': 100,
                                          'scope': 'only four registered task attempts'})
        if (root/'queue-complete.json').exists() and all(row.get('status') in TERMINAL for row in previous['runs'].values()):
            return
        time.sleep(60)


if __name__ == '__main__':
    main()
