"""Run frozen variant ZIPs through the historical hosted Competition."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import fcntl
import hashlib
import json
from pathlib import Path
import sys
import time

import competition
from factory import api_key, save


def execute(manifest, directory, secret=None):
    manifest, directory = Path(manifest).resolve(), Path(directory).resolve()
    spec = json.loads(manifest.read_text())
    variants = spec['variants']
    if not variants or len({v['id'] for v in variants}) != len(variants):
        raise ValueError('variants must be nonempty and unique')
    if not spec['tasks'] or len({t['id'] for t in spec['tasks']}) != len(spec['tasks']):
        raise ValueError('tasks must be nonempty and unique')
    for row in variants:
        if Path(row['id']).name != row['id'] or row['id'] in ('.', '..'):
            raise ValueError('variant id must be a directory name')
        package = (manifest.parent/row['package']).resolve()
        actual = hashlib.sha256(package.read_bytes()).hexdigest()
        if actual != row['package_sha256']:
            raise ValueError('matrix package hash mismatch: '+row['id'])
        row['package'] = str(package)
    local = spec.get('local')
    if local and not 1 <= local['workers'] <= 4:
        raise ValueError('local workers must be in 1..4')
    directory.mkdir(parents=True, exist_ok=True)
    with (directory/'controller.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        inputs = directory/'inputs.json'
        if inputs.exists() and json.loads(inputs.read_text()) != spec:
            raise ValueError('matrix inputs changed; refusing mixed revisions')
        if not inputs.exists():
            save(inputs, spec)
        state = {'started_at':time.time(), 'status':'running', 'hosted':{}, 'local':{}}
        state_file = directory/'matrix.json'
        if state_file.exists():
            state = json.loads(state_file.read_text())
            if state['status'] == 'completed':
                return state
        state['status'] = 'running'
        state.pop('finished_at', None)
        save(state_file, state)

        def scored(summary):
            return summary.get('status') == 'completed' and summary.get('score_status') == 'complete' and all(
                'expected_tests' not in task or summary.get('tasks', {}).get(task['id'], {}).get('platform_result', {}).get('total_tests') == task['expected_tests']
                for task in spec['tasks'])

        def hosted():
            results = {}
            for row in variants:
                target = directory/'hosted'/row['id']
                competition.prepare(target, row['package'], competition_id=spec['competition'],
                    variant=row['id'], tasks=[t['id'] for t in spec['tasks']],
                    model_config=row['model_config'])
                with competition.Controller(target, secret=secret) as controller:
                    controller.run_all(interval=180)
                    results[row['id']] = controller.summary()
                # The current platform only accepts fresh tasks on its latest
                # snapshot. Finish both tasks before uploading the next ZIP.
                if not scored(results[row['id']]):
                    break
            return results

        def local_jobs():
            if not local:
                return {}
            selected = set(local.get('variants', [v['id'] for v in variants]))
            jobs = [(v,t) for v in variants if v['id'] in selected for t in spec['tasks']]
            results, futures = {}, {}
            with ThreadPoolExecutor(max_workers=local['workers']) as pool:
                pending = iter(jobs)
                def submit_next():
                    pair = next(pending, None)
                    if pair is None:
                        return
                    row, task = pair
                    key = row['id']+'--'+task['id']
                    future = pool.submit(local_runner.execute, local['runner'], row['package'],
                        task['requirements'], task['tests'], directory/'local'/key, task['slug'],
                        image=local['image'], env_file=local.get('env_file'), shared_key=True, expected_tests=task.get('expected_tests'))
                    futures[future] = key
                for _ in range(local['workers']):
                    submit_next()
                paused = False
                while futures:
                    done, _ = wait(futures, return_when=FIRST_COMPLETED)
                    for future in done:
                        key = futures.pop(future)
                        try:
                            result = future.result()
                        except Exception as exc:
                            result = {'phase':'unknown', 'error':str(exc)}
                        results[key] = result
                        paused |= result.get('phase') != 'collected'
                    if not paused:
                        for _ in done:
                            submit_next()
            return results

        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = {pool.submit(hosted): 'hosted', pool.submit(local_jobs): 'local'}
            while futures:
                done, _ = wait(futures, return_when=FIRST_COMPLETED)
                for future in done:
                    venue = futures.pop(future)
                    try:
                        state[venue] = future.result()
                    except Exception as exc:
                        state[venue] = {'error':str(exc)}
                        state['status'] = 'blocked'
                    save(state_file, state)
        hosted_done = len(state['hosted']) == len(variants) and all(
            isinstance(v, dict) and scored(v) for v in state['hosted'].values())
        local_expected = sum(1 for v in variants if not local or v['id'] in local.get('variants', [x['id'] for x in variants])) * len(spec['tasks']) if local else 0
        local_done = len(state['local']) == local_expected and all(
            isinstance(v, dict) and v.get('phase') == 'collected' for v in state['local'].values())
        state['status'] = 'completed' if hosted_done and local_done else 'blocked'
        state['finished_at'] = time.time()
        save(state_file, state)
        return state


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--directory', type=Path)
    args = parser.parse_args()
    if args.directory is None:
        parser.error('--directory is required for execution')
    state = execute(args.manifest, args.directory, secret=api_key())
    def compact(row):
        if 'status' in row or 'error' in row:
            return {key:row.get(key) for key in ('status','score_status','error') if key in row}
        return {contest:compact(summary) for contest,summary in row.items()}
    print(json.dumps({'status':state['status'], 'evidence':str(args.directory.resolve()),
        'errors':{venue: state[venue]['error'] for venue in ('hosted',) if 'error' in state[venue]},
        'hosted':{name:compact(row) for name,row in state['hosted'].items() if isinstance(row,dict)}}, ensure_ascii=False))
    return 0 if state['status'] == 'completed' else 1


if __name__ == '__main__':
    sys.exit(main())
