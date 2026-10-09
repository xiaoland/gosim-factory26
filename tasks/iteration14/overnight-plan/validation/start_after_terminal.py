"""Wait for the existing Hosted task slot, then dispatch the two frozen jobs once."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

PROJECT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(PROJECT))
from lab.arc_bench.playground import Client, run_path
from lab.exp.core import atomic, locked, process_identity, read
from lab.exp.hosted import TERMINAL

ROOT = PROJECT / 'runs/iteration14/overnight-20261003'
QUEUE = ROOT / 'queued-generations'
SOURCE = ROOT / 'stage-a2/experiment/attempts/attempt-07031e32569a13d9886ca629/execution.json'


def main():
    if ROOT.resolve().stat().st_dev != Path('/Volumes/WorkSSD').stat().st_dev:
        raise RuntimeError('queue output must remain on WorkSSD')
    with locked(QUEUE / 'dispatch-owner.lock', blocking=False):
        owner = process_identity(os.getpid())
        if (QUEUE / 'start-intent.json').exists():
            raise RuntimeError('dispatch was already requested; inspect its receipt before re-entry')
        started = time.time()
        try:
            while True:
                source = read(SOURCE)
                if source.get('run_id') != '8a282da5502e' or source.get('submission_id') != '3c086cc0c8f1':
                    raise RuntimeError('upstream execution identity changed')
                atomic(QUEUE / 'dispatch-status.json', {'status': 'waiting-for-e2e', 'owner': owner,
                    'checked_at': time.time(), 'source_run_id': source['run_id'],
                    'source_status': source.get('remote_status'), 'source_observed_at': source.get('observed_at')})
                if source.get('remote_status') in TERMINAL and not source.get('pending'):
                    break
                if time.time() - started > 36 * 3600:
                    raise RuntimeError('task slot was not released within 36 hours')
                time.sleep(30)
            deployment = read(ROOT / 'stage-a/.private/deployment.json')
            value = Client(deployment['cookie_file']).request(run_path(source['run_id']))
            atomic(QUEUE / 'source-terminal-independent-get.json', {
                'observed_at': time.time(), 'run': value})
            if (value.get('id') != source['run_id'] or value.get('submission_id') != source['submission_id'] or
                    value.get('requirement_id') != 'hackathon--github' or value.get('billing_mode') != 'self_funded' or
                    value.get('status') not in TERMINAL or not value.get('finished_at')):
                raise RuntimeError('source terminal identity or task-slot release is unconfirmed')
            manifest = read(QUEUE / 'experiment/experiment.json')
            argv = [manifest['controller_runtime']['launcher'], '-B', '-m', 'lab',
                'start', str(QUEUE / 'experiment'), '--deployment', str(ROOT / 'stage-a/.private/deployment.json')]
            atomic(QUEUE / 'start-intent.json', {'argv': argv, 'requested_at': time.time(),
                'source_run_id': source['run_id'], 'owner': owner})
            with (QUEUE / 'start.stdout.json').open('w') as out, (QUEUE / 'start.stderr.log').open('w') as err:
                result = subprocess.run(argv, cwd=PROJECT, stdout=out, stderr=err)
            atomic(QUEUE / 'start-receipt.json', {'argv': argv, 'finished_at': time.time(),
                'returncode': result.returncode})
            if result.returncode:
                raise RuntimeError('queue start failed; inspect saved stderr without repeating dispatch')
            controller = read(QUEUE / 'experiment/controller.json')
            with locked(ROOT / 'monitor-contract.lock'):
                contract = read(ROOT / 'monitor-contract.json')
                for row in contract['experiments']:
                    if row.get('candidate_key') in ('reviewer-generation', 'cleaner-generation'):
                        row.update(controller=controller, phase='controller-dispatched')
                contract['queue_dispatcher'].update(status='completed', effect='controller-dispatched')
                contract['updated_at'] = time.time()
                atomic(ROOT / 'monitor-contract.json', contract)
            atomic(QUEUE / 'dispatch-status.json', {'status': 'completed', 'owner': owner,
                'controller': controller, 'finished_at': time.time(), 'effect': 'controller-dispatched'})
        except BaseException as exc:
            atomic(QUEUE / 'dispatch-status.json', {'status': 'failed', 'owner': owner,
                'finished_at': time.time(), 'error': {'type': type(exc).__name__, 'message': str(exc)}})
            raise


if __name__ == '__main__':
    main()
