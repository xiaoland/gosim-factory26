"""Freeze the I14 policy once, then dispatch solely through the exp controller."""
import argparse
import math
import json
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from lab.exp.core import atomic, digest as file_hash, read as read_json, require

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


def work(directory, *, build_only=False):
    directory = Path(directory).resolve(strict=True)
    config = read_json(directory / 'config.json')
    recipe = require(read_json(directory / 'recipe.json'), 'experiment')
    targets = config['targets']
    target_ids = {target['job_id'] for target in targets}
    if not targets or len(target_ids) != len(targets):
        raise ValueError('I14 requires a nonempty unique explicitly declared target set')
    primary = [job for job in recipe['jobs'] if job['purpose'] in {'generate', 'prepare'}]
    if {job['id'] for job in primary} != target_ids:
        raise ValueError('recipe primary jobs differ from the declared targets')
    selected = {job['id']: job.get('model_config', job['backend'].get('model_config')) for job in primary}
    for job_id, model in selected.items():
        if not model or any(not model.get(key) for key in ('model', 'visual_model', 'provider', 'base_url')):
            raise ValueError('target must explicitly freeze model/provider/endpoint: ' + job_id)
    selection = {'models': selected, 'targets': targets, 'config_sha256': file_hash(directory / 'config.json'),
                 'recipe_sha256': file_hash(directory / 'recipe.json'), 'policy': 'explicit-recipe'}
    if config.get('root_selection') == 'i13-final-two-task-margin':
        decision = choose_root(config)
        if any(model['model'] != decision['root_model'] for model in selected.values()):
            raise ValueError('explicit recipe differs from the requested research selection policy')
        selection['research_decision'] = decision
    selection_path = directory / 'selection.json'
    if selection_path.exists():
        if read_json(selection_path) != selection:
            raise ValueError('frozen selection differs; choose a new experiment directory')
    else:
        atomic(selection_path, selection)
    deployment = directory / 'deployment.json'
    if not deployment.exists() or not read_json(deployment).get('credential_file'):
        raise ValueError('I14 requires an explicit private deployment credential binding')
    from lab.exp.controller import build, start
    build(directory / 'recipe.json', directory / 'experiment')
    root = directory / 'experiment'
    atomic(directory / 'launch-receipt.json', {'selection': selection, 'experiment': str(root), 'build_only': build_only})
    if not build_only:
        print(json.dumps(start(root, deployment=deployment), ensure_ascii=False))
    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--build-only', action='store_true')
    args = parser.parse_args()
    raise SystemExit(work(args.directory, build_only=args.build_only))
