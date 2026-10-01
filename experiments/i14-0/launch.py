"""Dispatch the eight authorized I14-0 targets through immutable ARC operations."""
import argparse
import math
import os
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from lab.arc_bench.arc_matrix import build
from lab.arc_bench.competition import atomic_json
from lab.arc_bench.docker_admission import snapshot
from lab.arc_bench.operations import prepare, run, selected_runs, lock, error_record, worker_owner, TERMINAL
from lab.control import process_identity, process_state
from lab.docker_endpoint import environment, SELECTION_ENV, confirm
from lab.records import read_json, file_hash


def final_score(binding):
    """Consume saved platform observations, never collect or query the platform."""
    journal = Path(binding['journal'])
    if not (journal / 'state.json').is_file():
        return {'status': 'unavailable', 'journal': str(journal)}
    state = read_json(journal / 'state.json')
    task = state['tasks'][binding['task']]
    rid = task.get('run_id')
    if binding.get('run_id') and rid != binding['run_id']:
        raise ValueError('I13 score binding changed')
    if state.get('pending') or not rid:
        return {'status': 'unavailable', 'journal': str(journal)}
    observations = list(Path(binding['monitor']).glob('*/' + rid + '/status.json'))
    path = max(observations, key=lambda p: p.parent.parent.name) if observations else journal / 'state.json'
    observed = read_json(path)
    value = observed.get('value', observed)
    if path.name == 'state.json':
        value = {**task.get('platform_result', {}), 'status': task.get('remote_status')}
    score, passed, failed = (value.get(k) for k in ('score', 'passed_count', 'failed_count'))
    total = value.get('total_tests')
    if total is None and type(passed) is int and type(failed) is int:
        total = passed + failed
    valid = (value.get('status') in {'PASSED', 'FAILED'} and
             type(score) in (int, float) and math.isfinite(score) and 0 <= score <= 100 and
             all(type(n) is int and n >= 0 for n in (passed, failed, total)) and
             total > 0 and passed + failed == total)
    return {'status': 'complete' if valid else 'unavailable', 'score_percent': score if valid else None,
            'run_id': rid, 'journal': str(journal), 'evidence': str(path), 'evidence_sha256': file_hash(path)}


def choose_root(config):
    evidence = {group: {case: final_score(row) for case, row in cases.items()}
                for group, cases in config['i13_scores'].items()}
    complete = all(row['status'] == 'complete' for cases in evidence.values() for row in cases.values())
    means = {group: sum(row['score_percent'] for row in cases.values()) / 2
             for group, cases in evidence.items()} if complete else {}
    difference = means['glm'] - means['flash'] if complete else None
    return {'root_model': 'glm-5.3' if complete and difference >= 10 else 'glm-5.3-flash',
            'mean_scores_percent': means, 'difference_percentage_points': difference,
            'criterion': 'two final tasks in both groups; GLM minus Flash >= 10pp',
            'evidence': evidence, 'decided_at': time.time()}


def bindings(directory, targets):
    result = []
    for target in targets:
        op = directory / 'operations' / target['id']
        if not (op / 'inputs.json').is_file():
            continue
        inputs = read_json(op / 'inputs.json')
        runs = selected_runs(inputs)
        result.append({'target': target['id'], 'operation': str(op), 'experiment': inputs['experiment'],
                       'monitor': inputs['monitor_output'], 'runs': [str(p) for p in runs]})
    return result


def write_index(directory, config, state):
    rows = bindings(directory, config['targets'])
    atomic_json(directory / 'active-matrix.json', {
        'schema_version': 1, 'kind': 'operation-index', 'experiment_key': config['experiment_key'],
        'operations': rows, 'runs': [p for row in rows for p in row['runs']],
        'queued': [t['id'] for t in config['targets'] if t['id'] not in state['dispatched']],
        'model_channel': 'arc-self-funded', 'docker_context': config['endpoint']['context'],
        'selection_receipts': {name: str(directory / 'operations' / name / 'selection.json')
                               for name in state['dispatched']}, 'observed_at': time.time()})
    return rows


def dispatch(directory, config, target):
    op = directory / 'operations' / target['id']
    op.mkdir(parents=True, exist_ok=True)
    selection_path = op / 'selection.json'
    if selection_path.exists():
        selection = read_json(selection_path)
    else:
        selection = {**choose_root(config), 'target': target,
                     'config_sha256': file_hash(directory / 'config.json')}
        atomic_json(selection_path, selection)
    if selection['target'] != target or selection['config_sha256'] != file_hash(directory / 'config.json'):
        raise ValueError('pending operation belongs to a different selection')
    if file_hash(target['package']) != target['package_sha256']:
        raise ValueError('frozen package changed')
    model = selection['root_model']
    private_env = op / 'model.env'
    if not private_env.exists():
        lines = [line for line in Path(config['arc_env']).read_text().splitlines()
                 if not line.partition('=')[0].strip().removeprefix('export ').strip() in {'MODEL', 'VISUAL_MODEL'}]
        temporary = private_env.with_suffix('.env.pending')
        with temporary.open('w') as stream:
            stream.write('\n'.join([*lines, 'MODEL=' + model, 'VISUAL_MODEL=glm-5.3-flash']) + '\n')
            stream.flush()
            os.fsync(stream.fileno())
        temporary.chmod(0o600)
        temporary.replace(private_env)
    values = {}
    for line in private_env.read_text().splitlines():
        name, separator, value = line.strip().partition('=')
        if separator and name in {'MODEL', 'VISUAL_MODEL', 'OPENAI_API_KEY', 'OPENAI_BASE_URL'}:
            if name in values:
                raise ValueError('duplicate model connection variable: ' + name)
            values[name] = value.strip().strip('\"\'')
    if (values.get('MODEL') != model or values.get('VISUAL_MODEL') != 'glm-5.3-flash' or
            not values.get('OPENAI_API_KEY') or not values.get('OPENAI_BASE_URL') or private_env.stat().st_mode & 0o077):
        raise ValueError('private model connection does not match the selected root')
    recipe_path = op / 'matrix.json'
    if not recipe_path.exists():
        recipe = build([target['variant'] + '=' + target['package']], [target['case']],
                       config['inputs_root'], config['runner'], image=config['image'],
                       env_file=str(private_env), workers=1, separate_evaluation=True, requirements_only=True,
                       experiment_key=config['experiment_key'], storage=config['storage'],
                       host_runtime_receipt=config['host_runtime'], shared_docker_slots=5, memory='2g', cpus=2)
        recipe['jobs'][0]['inputs']['model_env'] = str(private_env)
        recipe['jobs'][0]['command'] = ['{model_env}' if part == str(private_env) else part
                                       for part in recipe['jobs'][0]['command']]
        recipe['jobs'][0]['labels'].update(batch='i14-0', root_model=model, model_channel='arc-self-funded',
                                          execution_kind='clean-generation', target=target['id'])
        atomic_json(recipe_path, recipe)
    job_id = read_json(recipe_path)['jobs'][0]['id']
    spec_path = op / 'operation-spec.json'
    if not spec_path.exists():
        task = target['case'].split('/')[1]
        atomic_json(spec_path, {'authorization': config['authorization'], 'venue': 'local',
            'recipe': str(recipe_path), 'monitor_output': str(op / 'observation'),
            'credential_file': config['arc_env'],
            'replay': {'jobs': {job_id: {
                'competition_id': 'hackathon', 'variant': target['variant'], 'tasks': ['hackathon--' + task],
                'model_config': {'base_url': 'https://api.arc-bench.com/v1', 'model': model,
                                 'visual_model': 'glm-5.3-flash'},
                'credential_mode': 'self_funded', 'allow_competition_credit': False,
                'experiment_key': config['experiment_key'], 'case': target['variant'],
                'name': config['experiment_key'] + '--' + target['id'] + '--artifact-replay',
                'run_names': {'hackathon--' + task: config['experiment_key'] + '--' + target['id'] + '--r01'}}}}})
    prepare(spec_path, op)
    receipt = run(op)
    atomic_json(op / 'dispatch-receipt.json', receipt)


def work(directory):
    os.umask(0o077)
    config = read_json(directory / 'config.json')
    for name in (*SELECTION_ENV, 'DOCKER_API_VERSION'):
        os.environ.pop(name, None)
    os.environ.update(environment(config['endpoint']))
    confirm(config['endpoint'])
    expected = {(v, 'hackathon/' + c) for v in ('pi-braid-i14', 'pi-braid-i14-cleaner',
                'pi-braid-i14-reviewer', 'pi-braid-i14-e2e') for c in ('github', 'sheet')}
    if (len(config['targets']) != 8 or len({t['id'] for t in config['targets']}) != 8 or
            {(t['variant'], t['case']) for t in config['targets']} != expected or
            set(config['i13_scores']) != {'glm', 'flash'} or
            any(set(cases) != {'github', 'sheet'} for cases in config['i13_scores'].values())):
        raise ValueError('I14-0 requires eight distinct authorized targets')
    with lock(directory / 'dispatcher.lock'):
        state_path = directory / 'dispatcher.json'
        previous = read_json(state_path) if state_path.exists() else {}
        if previous and previous['config_sha256'] != file_hash(directory / 'config.json'):
            raise ValueError('queue configuration changed')
        state = {**process_identity(), 'phase': 'running', 'config_sha256': file_hash(directory / 'config.json'),
                 'dispatched': previous.get('dispatched', []), 'started_at': time.time()}
        atomic_json(state_path, state)
        try:
            while True:
                # A crash after dispatch but before queue acknowledgment resumes that same immutable operation.
                pending = [t for t in config['targets'] if t['id'] not in state['dispatched']]
                if pending and (directory / 'operations' / pending[0]['id'] / 'selection.json').exists():
                    dispatch(directory, config, pending[0])
                    state['dispatched'].append(pending[0]['id'])
                    atomic_json(state_path, state)
                rows = write_index(directory, config, state)
                capacity = snapshot(config['endpoint'], 5)
                state['capacity'] = capacity
                represented = {p['labels']['io.factory26.run'] for p in capacity['physical']}
                represented.update(r['labels']['io.factory26.run'] for r in capacity['reservations'])
                # A snapshot does not reserve capacity. Wait for each actual admission before dispatching another.
                admitting = False
                for row in rows:
                    op = Path(row['operation'])
                    worker = worker_owner(op)
                    if worker.get('phase') in {'failed', 'interrupted'} or process_state(worker) == 'lost' and worker.get('phase') != 'completed':
                        raise RuntimeError('operation needs recovery: ' + str(op))
                    admitting |= not row['runs'] or any(read_json(Path(p) / 'run.json')['phase'] not in TERMINAL
                                                       and Path(p).name not in represented for p in row['runs'])
                pending = [t for t in config['targets'] if t['id'] not in state['dispatched']]
                if not pending and not admitting:
                    state.update(phase='dispatched', finished_at=time.time())
                    atomic_json(state_path, state)
                    return
                if pending and not admitting and capacity['available']:
                    target = pending[0]
                    dispatch(directory, config, target)
                    state['dispatched'].append(target['id'])
                    state['last_dispatch_at'] = time.time()
                atomic_json(state_path, state)
                time.sleep(10)
        except BaseException as error:
            state.update(phase='failed', error=error_record(error), finished_at=time.time())
            atomic_json(state_path, state)
            raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    work(parser.parse_args().directory.resolve(strict=True))
