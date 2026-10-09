"""Consume this wave's frozen applications through one finite Hosted queue."""
import argparse
import copy
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time

PROJECT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(PROJECT))
from lab.exp.core import atomic, digest, locked, process_identity, process_state, read
from lab.exp.hosted import TERMINAL
from lab.arc_bench.playground import Client, run_path


def command(argv, directory, name):
    atomic(directory / (name + '-intent.json'), {'argv': argv, 'requested_at': time.time()})
    with (directory / (name + '.stdout.json')).open('w') as out, (directory / (name + '.stderr.log')).open('w') as err:
        result = subprocess.run(argv, cwd=PROJECT, stdout=out, stderr=err)
    atomic(directory / (name + '-receipt.json'), {'returncode': result.returncode, 'finished_at': time.time()})
    if result.returncode:
        raise RuntimeError(name + ' failed; inspect the saved original without repeating dispatch')


def generation(candidate):
    directory = Path(candidate['experiment'])
    manifest = read(directory / 'experiment.json')
    if manifest['recipe_sha256'] != candidate['recipe_sha256']:
        raise RuntimeError('generation definition changed: ' + candidate['key'])
    attempt = directory / 'attempts' / candidate['attempt_id']
    definition = read(attempt / 'attempt.json')
    if definition['job_id'] != candidate['job_id']:
        raise RuntimeError('generation job identity changed: ' + candidate['key'])
    execution = read(attempt / 'execution.json')
    outputs = execution.get('artifacts', {})
    if not all(name in outputs for name in ('application', 'application_receipt')):
        controller = read(directory / 'controller.json')
        if controller.get('phase') in {'blocked', 'failed'}:
            raise RuntimeError('generation controller needs root intervention: ' + candidate['key'])
        if controller.get('phase') == 'completed':
            return {'state': 'unscored-no-published-application', 'execution': execution.get('execution'),
                    'evidence': str(attempt / 'execution.json')}
        return {'state': 'waiting-for-application'}
    store = Path(definition['artifact_store'])
    inputs = {}
    references = {name: outputs[name] for name in ('application', 'application_receipt')}
    references['requirements'] = definition['job']['inputs']['requirements']
    for name, reference in references.items():
        artifact = store / reference['artifact_id']
        if digest(artifact / 'manifest.json') != reference['manifest_sha256']:
            raise RuntimeError('source artifact identity differs: ' + name)
        published = read(artifact / 'manifest.json')
        inputs[name] = {'source': str(artifact / 'payload'), 'source_identity': published['contents']}
    return {'state': 'published', 'inputs': inputs, 'source_references': references,
            'source_attempt': candidate['attempt_id'], 'manifest': manifest}


def evaluation(contract, candidate, source, directory):
    original = read(Path(contract['upstream_experiment']) / 'experiment.json')
    baseline = next(job for job in original['jobs'] if job['backend']['kind'] == 'hosted')
    backend = copy.deepcopy(baseline['backend'])
    backend.update(variant=candidate['variant'], credential_mode='self_funded')
    job = {'id': candidate['key'] + '-replay', 'purpose': 'evaluate', 'backend': backend,
           'target': {'case': 'github', 'variant': candidate['key']}, 'inputs': source['inputs'],
           'outputs': [], 'limits': copy.deepcopy(baseline['limits']),
           'model_config': copy.deepcopy(baseline['model_config']),
           'source_job': {'experiment': candidate['experiment'], 'attempt_id': candidate['attempt_id'],
                          'job_id': candidate['job_id'], 'artifacts': source['source_references']}}
    recipe = {'kind': 'factory26.exp.experiment', 'schema_version': 2,
              'experiment_id': 'i14-' + candidate['key'] + '-github-replay-20261003',
              'authorization': contract['authorization'], 'max_parallel': 1, 'budget': {'max_attempts': 1},
              'storage': copy.deepcopy(original['storage']), 'jobs': [job],
              'controller_runtime': str(Path(original['controller_runtime']['root']) / 'asset.json'),
              'labels': {'iteration': 'I14', 'candidate': candidate['key'], 'execution': 'application-replay',
                         'input_boundary': 'frozen-application-only; no new generation'}}
    directory.mkdir(parents=True, exist_ok=True)
    atomic(directory / 'recipe.json', recipe)
    launcher = original['controller_runtime']['launcher']
    experiment = directory / 'experiment'
    command([launcher, '-B', '-m', 'lab', 'build', str(directory / 'recipe.json'),
             '--directory', str(experiment)], directory, 'build')
    # A durable start intent always precedes the single start call. Unknown effects
    # are left for root; the queue never recreates or retries this evaluation.
    command([launcher, '-B', '-m', 'lab', 'start', str(experiment),
             '--deployment', contract['deployment']], directory, 'start')
    return str(experiment)


def terminal_get(contract, execution, destination):
    deployment = read(contract['deployment'])
    actual = Client(deployment['cookie_file']).request(run_path(execution['run_id']))
    atomic(destination, {'observed_at': time.time(), 'run': actual})
    if (actual.get('id') != execution['run_id'] or
            actual.get('submission_id') != execution['submission_id'] or
            actual.get('requirement_id') != 'hackathon--github' or
            actual.get('billing_mode') != 'self_funded' or actual.get('status') not in TERMINAL or
            not actual.get('finished_at') or execution.get('pending')):
        raise RuntimeError('exact upstream terminal/task-slot release is unconfirmed')
    return actual


def evaluation_result(actual):
    passed, failed = actual.get('passed_count'), actual.get('failed_count')
    count = lambda value: type(value) is int and value >= 0
    total = actual.get('total_tests')
    if total is None and count(passed) and count(failed):
        total = passed + failed
    stages = [step for step in actual.get('steps', []) if step.get('key') == 'run_tests']
    evaluated = (stages[0].get('status') == 'completed' if len(stages) == 1 else
                 actual.get('evaluation_status') == 'completed')
    complete = (actual.get('status') in {'PASSED', 'FAILED'} and evaluated and
                count(passed) and count(failed) and count(total) and total > 0 and total == passed + failed)
    score = actual.get('score')
    score_available = type(score) in (int, float) and math.isfinite(score) and score >= 0
    return {'functional_complete': complete, 'passed_count': passed, 'failed_count': failed,
            'total_tests': total, 'functional_pass_rate_percent': 100 * passed / total if complete else None,
            'platform_score': score, 'platform_score_available': score_available,
            'platform_score_semantics': 'unconfirmed; preserve original API result',
            'test_pass_rate_raw': actual.get('test_pass_rate'), 'failure_reason': actual.get('failure_reason')}


def main(contract_path):
    contract_path = Path(contract_path).resolve(strict=True)
    contract = read(contract_path)
    directory = Path(contract['output']).resolve()
    existing = directory
    while not existing.exists():
        existing = existing.parent
    if existing.stat().st_dev != Path('/Volumes/WorkSSD').stat().st_dev:
        raise RuntimeError('Mac evaluation records must physically reside on WorkSSD')
    directory.mkdir(parents=True, exist_ok=True)
    with locked(directory / 'owner.lock', blocking=False):
        if (directory / 'queue-started.json').exists():
            raise RuntimeError('queue already entered; inspect its exact receipts before any recovery')
        owner = process_identity(os.getpid())
        atomic(directory / 'queue-started.json', {'owner': owner, 'contract_sha256': digest(contract_path),
                                                'started_at': time.time()})
        state = {'owner': owner, 'phase': 'waiting-for-upstream', 'candidates': {}, 'checked_at': time.time()}
        started = time.time()
        released = False
        active = None
        try:
            while True:
                if time.time() - started > 36 * 3600:
                    raise RuntimeError('finite evaluation queue exceeded 36 hours')
                if not released:
                    upstream = read(Path(contract['upstream_attempt']) / 'execution.json')
                    if (upstream.get('run_id') != contract['upstream_run_id'] or
                            upstream.get('submission_id') != contract['upstream_submission_id']):
                        raise RuntimeError('upstream identity changed')
                    if upstream.get('remote_status') in TERMINAL and not upstream.get('pending'):
                        terminal_get(contract, upstream, directory / 'upstream-terminal-get.json')
                        released = True
                    else:
                        controller = read(Path(contract['upstream_experiment']) / 'controller.json')
                        if controller.get('phase') in {'blocked', 'failed'} or (
                                controller.get('phase') == 'running' and process_state(controller) != 'alive'):
                            raise RuntimeError('upstream controller requires root intervention; do not release Hosted slot')
                if active:
                    key, experiment = active
                    controller = read(Path(experiment) / 'controller.json')
                    if controller.get('phase') in {'blocked', 'failed'} or (
                            controller.get('phase') == 'running' and process_state(controller) != 'alive'):
                        raise RuntimeError('evaluation controller requires root intervention: ' + key)
                    if controller.get('phase') == 'completed':
                        attempts = list((Path(experiment) / 'attempts').glob('*/attempt.json'))
                        if len(attempts) != 1:
                            raise RuntimeError('evaluation must retain exactly one attempt: ' + key)
                        definition = read(attempts[0])
                        if definition['job_id'] != key + '-replay':
                            raise RuntimeError('evaluation job identity differs: ' + key)
                        execution = read(attempts[0].parent / 'execution.json')
                        actual = terminal_get(contract, execution, directory / key / 'terminal-get.json')
                        result_summary = evaluation_result(actual)
                        from lab.exp.controller import status
                        result = status(experiment)
                        atomic(directory / key / 'terminal.json', result)
                        state['candidates'][key].update(phase='functional-evaluation-complete' if result_summary['functional_complete'] else 'platform-terminal-evaluation-incomplete',
                                                       result=result_summary, run_id=actual['id'],
                                                       submission_id=actual['submission_id'],
                                                       terminal_evidence=str(directory / key / 'terminal.json'))
                        active = None
                for candidate in contract['candidates']:
                    key = candidate['key']
                    if key in state['candidates']:
                        continue
                    source = generation(candidate)
                    if source['state'] == 'unscored-no-published-application':
                        state['candidates'][key] = {'phase': source['state'], 'source': source}
                    elif source['state'] == 'published' and released and not active:
                        experiment = evaluation(contract, candidate, source, directory / key)
                        state['candidates'][key] = {'phase': 'evaluation-dispatched', 'experiment': experiment,
                                                   'source_attempt': candidate['attempt_id']}
                        active = (key, experiment)
                        atomic(directory / 'status.json', dict(state, phase='evaluating', checked_at=time.time()))
                complete = len(state['candidates']) == len(contract['candidates']) and not active
                state.update(phase='completed' if complete else 'evaluating' if active else
                             'waiting-for-application' if released else 'waiting-for-upstream', checked_at=time.time())
                if complete:
                    state['all_functional_evaluations_complete'] = all(row.get('result', {}).get('functional_complete') for row in state['candidates'].values())
                    state['all_platform_scores_available'] = all(row.get('result', {}).get('platform_score_available') for row in state['candidates'].values())
                atomic(directory / 'status.json', state)
                if complete:
                    return
                time.sleep(30)
        except Exception as exc:
            state.update(phase='failed', checked_at=time.time(), error={'type': type(exc).__name__, 'message': str(exc)})
            atomic(directory / 'status.json', state)
            raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('contract', type=Path)
    main(parser.parse_args().contract)
