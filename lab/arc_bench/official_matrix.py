"""Run frozen variant ZIPs through the historical hosted Competition."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import fcntl
import hashlib
import json
from pathlib import Path
import sys
import time

from . import competition
from .playground import api_key, save


def execute(manifest, directory, secret=None):
    manifest, directory = Path(manifest).resolve(), Path(directory).resolve()
    spec = json.loads(manifest.read_text())
    variants = spec['variants']
    if not variants or len({v['id'] for v in variants}) != len(variants):
        raise ValueError('variants must be nonempty and unique')
    legacy = 'competitions' not in spec
    competitions = ([{'id':spec['competition'], 'tasks':spec['tasks']}]
                    if legacy else spec['competitions'])
    if not competitions or len({c['id'] for c in competitions}) != len(competitions):
        raise ValueError('competitions must be nonempty and unique')
    tasks = [task for contest in competitions for task in contest['tasks']]
    if any(not c['tasks'] for c in competitions) or len({t['id'] for t in tasks}) != len(tasks):
        raise ValueError('tasks must be nonempty and unique')
    for contest in competitions:
        competition.identifier(contest['id'])
        for task in contest['tasks']:
            if not task['id'].startswith(contest['id']+'--'):
                raise ValueError('task does not belong to competition: '+task['id'])
    for row in variants:
        if Path(row['id']).name != row['id'] or row['id'] in ('.', '..'):
            raise ValueError('variant id must be a directory name')
        package = (manifest.parent/row['package']).resolve()
        actual = hashlib.sha256(package.read_bytes()).hexdigest()
        if actual != row['package_sha256']:
            raise ValueError('matrix package hash mismatch: '+row['id'])
        row['package'] = str(package)
    if spec.get('local'):
        raise ValueError('the hosted matrix no longer runs local jobs; use python3 -m lab.run')
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

        def scored(summary, contest):
            return (isinstance(summary, dict) and summary.get('status') == 'completed'
                and summary.get('score_status') == 'complete'
                and set(summary.get('tasks', {})) == {task['id'] for task in contest['tasks']}
                and all('expected_tests' not in task or
                    summary['tasks'][task['id']].get('platform_result', {}).get('total_tests') == task['expected_tests']
                    for task in contest['tasks']))

        def hosted():
            results = {}
            def run_one(row, contest):
                target = directory/'hosted'/row['id']
                if not legacy:
                    target = target/contest['id']
                competition.prepare(target, row['package'], competition_id=contest['id'],
                    variant=row['id'], tasks=[t['id'] for t in contest['tasks']],
                    model_config=row['model_config'])
                with competition.Controller(target, secret=secret) as controller:
                    controller.run_all(interval=180)
                    return controller.summary()
            for row in variants:
                with ThreadPoolExecutor(max_workers=len(competitions)) as pool:
                    futures = {contest['id']:pool.submit(run_one, row, contest) for contest in competitions}
                    sides = {}
                    for contest in competitions:
                        try:
                            sides[contest['id']] = futures[contest['id']].result()
                        except Exception as exc:
                            sides[contest['id']] = {'error':str(exc)}
                results[row['id']] = sides[competitions[0]['id']] if legacy else sides
                # Each competition permits a new snapshot only after its latest
                # snapshot has terminal tasks. Keep variants aligned across both.
                if not all(scored(sides[contest['id']], contest) for contest in competitions):
                    break
            return results

        try:
            state['hosted'] = hosted()
        except Exception as exc:
            state['hosted'] = {'error':str(exc)}
            state['status'] = 'blocked'
        save(state_file, state)
        hosted_done = len(state['hosted']) == len(variants) and all(
            isinstance(value, dict) and all(scored((value if legacy else value.get(contest['id'], {})), contest)
                for contest in competitions)
            for value in state['hosted'].values())
        state['status'] = 'completed' if hosted_done else 'blocked'
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
