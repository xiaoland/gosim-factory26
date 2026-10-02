"""Compile explicit experiment intent; never install, observe or execute a job."""
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import os
import time

from . import artifacts
from .core import Blocked, atomic, digest, error, identifier, locked, public, read, record, require


def _fields(value, allowed, required=()):
    if not isinstance(value, dict) or set(value) - set(allowed) or set(required) - set(value):
        raise ValueError(f'intent fields required={list(required)}, allowed={list(allowed)}')
    return value


def _merge(left, right, context):
    overlap = set(left) & set(right)
    if any(left[key] != right[key] for key in overlap):
        raise ValueError(f'conflicting {context}: {sorted(overlap)}')
    return {**left, **right}


def final_score(binding, base):
    """Bind a saved GET or a named legacy task, including its real run identity."""
    _fields(binding, ('source', 'run_id', 'task'), ('source', 'run_id'))
    path = (base / binding['source']).resolve()
    result = {'status': 'unavailable', 'source': str(path), 'run_id': binding['run_id']}
    try:
        source = path.read_bytes()
        raw = json.loads(source)
        result['source_sha256'] = hashlib.sha256(source).hexdigest()
        value = raw.get('value', raw)
        if 'tasks' in value:
            task = value['tasks'][binding['task']]
            run_id = task.get('run_id')
            value = {**task.get('platform_result', {}), 'status': task.get('remote_status'), 'id': run_id}
            if raw.get('pending'):
                raise Blocked('legacy source has an unresolved platform write')
        if value.get('id') != binding['run_id']:
            raise ValueError('score evidence does not bind the declared run')
        score, passed, failed = (value.get(key) for key in ('score', 'passed_count', 'failed_count'))
        total = value.get('total_tests')
        if total is None and type(passed) is int and type(failed) is int:
            total = passed + failed
        if (value.get('status') not in {'PASSED', 'FAILED'} or type(score) not in (int, float) or
                not math.isfinite(score) or not 0 <= score <= 100 or
                any(type(count) is not int or count < 0 for count in (passed, failed, total)) or
                total == 0 or passed + failed != total):
            raise Blocked('score source lacks a complete terminal percentage and test counts')
        result.update(status='complete', score_percent=score)
    except (OSError, KeyError, TypeError, Blocked) as exc:
        result['error'] = error(exc)
        result['error'].pop('observed_at', None)  # Read time is not part of a frozen selection decision.
    return result


def select(policy, models, base):
    kind = policy.get('kind')
    if kind == 'explicit':
        _fields(policy, ('kind',), ('kind',))
        return {'kind': kind, 'selected_model': None, 'evidence': []}
    if kind != 'final-score-margin':
        raise ValueError('selection_policy must be explicit or final-score-margin')
    _fields(policy, ('kind', 'baseline', 'candidate', 'minimum_margin', 'scores', 'on_incomplete'),
            ('kind', 'baseline', 'candidate', 'minimum_margin', 'scores', 'on_incomplete'))
    baseline, candidate = policy['baseline'], policy['candidate']
    if baseline == candidate or baseline not in models or candidate not in models:
        raise ValueError('selection must name two distinct declared models')
    margin = policy['minimum_margin']
    if type(margin) not in (int, float) or not math.isfinite(margin) or margin < 0:
        raise ValueError('minimum_margin must be an explicit nonnegative percentage-point threshold')
    if policy['on_incomplete'] not in ('block', 'baseline'):
        raise ValueError('on_incomplete must explicitly be block or baseline')
    scores = policy['scores']
    if set(scores) != {baseline, candidate} or not scores[baseline] or set(scores[baseline]) != set(scores[candidate]):
        raise ValueError('score comparison needs identical nonempty case sets for both models')
    evidence = {model: {case: final_score(binding, base) for case, binding in cases.items()}
                for model, cases in scores.items()}
    complete = all(row['status'] == 'complete' for cases in evidence.values() for row in cases.values())
    decision = {'kind': kind, 'evidence': evidence, 'coverage': 'complete' if complete else 'incomplete',
                'minimum_margin': margin, 'on_incomplete': policy['on_incomplete']}
    if not complete and policy['on_incomplete'] == 'block':
        blocked = Blocked('selection lacks declared terminal score evidence')
        blocked.detail = decision
        raise blocked
    means = {model: sum(row['score_percent'] for row in cases.values()) / len(cases)
             for model, cases in evidence.items()} if complete else {}
    difference = means[candidate] - means[baseline] if complete else None
    decision.update(means=means, difference=difference,
                    selected_model=candidate if complete and difference >= margin else baseline)
    return decision


def _model(job, name, models):
    model = models[name]
    _fields(model, ('config', 'bindings'), ('config',))
    config = _fields(model['config'], ('model', 'visual_model', 'provider', 'base_url'),
                     ('model', 'visual_model', 'provider', 'base_url'))
    if any(not isinstance(value, str) or not value.strip() for value in config.values()) or public(config) != config:
        raise ValueError('model config needs public, explicit model/provider/endpoint strings')
    if 'model_config' in job or 'model_config' in job['backend']:
        raise ValueError('intent model_config belongs in models, not execution templates')
    job['model_config'] = deepcopy(config)
    if job['backend']['kind'] == 'hosted':
        job['backend']['model_config'] = deepcopy(config)
    if 'bindings' in model:
        for binding in model['bindings'].values():
            _fields(binding, ('provider', 'base_url', 'credential_env', 'model_id'),
                    ('provider', 'base_url', 'credential_env'))
            if any(not isinstance(value, str) or not value.strip() for value in binding.values()) or public(binding) != binding:
                raise ValueError('model bindings use explicit public strings and credential variable names')
        environment = job.setdefault('environment', {})
        serialized = json.dumps(model['bindings'], sort_keys=True, separators=(',', ':'))
        if 'FACTORY26_MODEL_BINDINGS' in environment and json.loads(environment['FACTORY26_MODEL_BINDINGS']) != model['bindings']:
            raise ValueError('template model bindings conflict with selected model')
        environment['FACTORY26_MODEL_BINDINGS'] = serialized


def _paths(job, base, files):
    for name, binding in list(job.get('inputs', {}).items()):
        if isinstance(binding, str):
            binding = {'source': binding}
            job['inputs'][name] = binding
        if 'source' in binding:
            source = (base / binding['source']).resolve(strict=True)
            binding['source'] = str(source)
            binding['source_identity'] = artifacts.contents(source)
        if binding.get('store'):
            binding['store'] = str((base / binding['store']).resolve(strict=True))
    for name in ('checkpoint', 'prepared', 'stop_evidence'):
        if name in job:
            source = (base / job[name]['source']).resolve(strict=True)
            job[name]['source'] = str(source)
            job[name]['source_identity'] = artifacts.contents(source)
    for backend in (job['backend'], *([job['backend']['external_docker']] if job['backend'].get('external_docker') else [])):
        if backend.get('authority_handoff'):
            handoff = backend['authority_handoff']
            if isinstance(handoff, dict) and set(handoff) == {'source'}:
                source = (base / handoff['source']).resolve(strict=True)
                backend['authority_handoff'] = require(read(source), 'authority-handoff')
                files[str(source)] = digest(source)
            else:
                require(handoff, 'authority-handoff')


def compile_intent(intent_path, directory):
    """Publish one immutable compile bundle; changed inputs require a new bundle."""
    intent_path, directory = Path(intent_path).resolve(strict=True), Path(directory).resolve()
    intent_bytes = intent_path.read_bytes()
    intent_sha256 = hashlib.sha256(intent_bytes).hexdigest()
    intent = require(json.loads(intent_bytes), 'intent')
    _fields(intent, ('kind', 'schema_version', 'experiment_id', 'authorization', 'execution',
                     'cases', 'variants', 'models', 'targets', 'selection_policy', 'evaluation_policy', 'labels'),
            ('experiment_id', 'authorization', 'execution', 'cases', 'variants', 'models', 'targets', 'selection_policy', 'evaluation_policy'))
    base = intent_path.parent
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    with locked(directory / '.compile.lock'):
        try:
            decision = select(intent['selection_policy'], intent['models'], base)
            execution = _fields(intent['execution'], ('controller_runtime', 'runner_runtime', 'max_parallel', 'budget', 'storage'),
                                ('controller_runtime', 'max_parallel', 'budget', 'storage'))
            recipe = record('experiment', experiment_id=identifier(intent['experiment_id']),
                            authorization=intent['authorization'], **deepcopy(execution), jobs=[], labels=intent.get('labels', {}))
            files = {}
            for cases in decision['evidence'].values() if isinstance(decision['evidence'], dict) else ():
                for row in cases.values():
                    if 'source_sha256' not in row:
                        continue
                    source = Path(row['source']).read_bytes()
                    if hashlib.sha256(source).hexdigest() != row['source_sha256']:
                        raise ValueError('selection source changed during compilation: ' + row['source'])
                    snapshot = directory / 'score-evidence' / (row['source_sha256'] + '.json')
                    snapshot.parent.mkdir(exist_ok=True, mode=0o700)
                    if not snapshot.exists():
                        with snapshot.open('xb') as stream:
                            os.chmod(snapshot, 0o600)
                            stream.write(source)
                            stream.flush()
                            os.fsync(stream.fileno())
                    if digest(snapshot) != row['source_sha256']:
                        raise ValueError('frozen score snapshot changed: ' + str(snapshot))
                    row['snapshot'] = str(snapshot)
                    files[str(snapshot)] = row['source_sha256']
            for field in ('controller_runtime', 'runner_runtime'):
                if field in recipe:
                    source = (base / recipe[field]).resolve(strict=True)
                    recipe[field] = str(source)
                    files[str(source)] = digest(source)
            ids = set()
            for target in intent['targets']:
                _fields(target, ('id', 'case', 'variant', 'model'), ('id', 'case', 'variant', 'model'))
                case, variant = intent['cases'][target['case']], intent['variants'][target['variant']]
                _fields(case, ('inputs', 'backend'))
                _fields(variant, ('generate',), ('generate',))
                job = deepcopy(variant['generate'])
                if any(key in job for key in ('id', 'target')) or job.get('purpose') not in ('generate', 'prepare'):
                    raise ValueError('variant generate template declares generate/prepare purpose; IDs and targets come from targets')
                job['id'] = identifier(target['id'])
                if job['id'] in ids:
                    raise ValueError('duplicate explicit target ID')
                ids.add(job['id'])
                job['target'] = {'case': target['case'], 'variant': target['variant']}
                job['inputs'] = _merge(job.get('inputs', {}), case.get('inputs', {}), 'case inputs')
                case_backend = _fields(case.get('backend', {}), ('competition_id', 'task'))
                job['backend'] = _merge(job['backend'], case_backend, 'case backend')
                selected = target['model']
                if isinstance(selected, dict):
                    if selected != {'selection': True} or decision['selected_model'] is None:
                        raise ValueError('selected target model needs a declared conditional selection policy')
                    selected = decision['selected_model']
                _model(job, selected, intent['models'])
                _paths(job, base, files)
                recipe['jobs'].append(job)
                evaluation = intent['evaluation_policy']
                if evaluation.get('kind') == 'none':
                    _fields(evaluation, ('kind',), ('kind',))
                    continue
                _fields(evaluation, ('kind', 'job', 'from_generation', 'model'), ('kind', 'job', 'from_generation'))
                if evaluation['kind'] != 'per-application' or job['purpose'] != 'generate' or not evaluation['from_generation']:
                    raise ValueError('evaluation must explicitly be per-application and bind generation outputs')
                evaluated = deepcopy(evaluation['job'])
                if any(key in evaluated for key in ('id', 'target')) or evaluated.get('purpose') != 'evaluate':
                    raise ValueError('evaluation job declares evaluate purpose; IDs and targets come from compiler')
                evaluated.update(id=identifier(job['id'] + '.evaluate'), target=dict(job['target']))
                evaluated['backend'] = _merge(evaluated['backend'], case_backend, 'evaluation case backend')
                evaluated['inputs'] = _merge(evaluated.get('inputs', {}), case.get('inputs', {}), 'evaluation case inputs')
                for name, output in evaluation['from_generation'].items():
                    if name in evaluated['inputs'] or output not in {row['name'] for row in job.get('outputs', [])}:
                        raise ValueError('evaluation binding duplicates an input or names an undeclared generation output')
                    evaluated['inputs'][name] = {'from_job': job['id'], 'output': output}
                if 'model' in evaluation:
                    _model(evaluated, evaluation['model'], intent['models'])
                elif evaluated['backend']['kind'] == 'hosted':
                    raise ValueError('hosted evaluation needs an explicit independent model binding')
                _paths(evaluated, base, files)
                recipe['jobs'].append(evaluated)
            recipe['compilation'] = {'intent_sha256': intent_sha256, 'compiler_sha256': digest(Path(__file__)),
                                     'selection': decision, 'files': files}
            from .controller import validate_recipe
            validate_recipe(recipe)
            receipt_path = directory / 'compilation.json'
            if receipt_path.exists():
                previous = require(read(receipt_path), 'compilation')
                if (read(directory / 'recipe.json') != recipe or digest(directory / 'recipe.json') != previous['recipe_sha256'] or
                        read(directory / 'intent.json') != intent or digest(directory / 'intent.json') != previous['intent_snapshot_sha256'] or
                        previous['intent_sha256'] != intent_sha256 or previous['compiler_sha256'] != recipe['compilation']['compiler_sha256'] or
                        previous['selection'] != decision):
                    raise ValueError('compiled input, policy, compiler or bundle changed; choose a new bundle')
                return public(previous)
            for name, value in (('intent.json', intent), ('recipe.json', recipe)):
                path = directory / name
                if path.exists() and read(path) != value:
                    raise ValueError('incomplete bundle belongs to different compilation input')
                atomic(path, value)
            receipt = record('compilation', intent_sha256=recipe['compilation']['intent_sha256'],
                             intent_snapshot_sha256=digest(directory / 'intent.json'),
                             compiler_sha256=recipe['compilation']['compiler_sha256'],
                             recipe=str(directory / 'recipe.json'), recipe_sha256=digest(directory / 'recipe.json'),
                             selection=decision, target_count=len(intent['targets']), job_count=len(recipe['jobs']),
                             created_at=time.time(), execution_permission=False)
            atomic(receipt_path, receipt)
            return public(receipt)
        except Exception as exc:
            atomic(directory / ('compile-error-' + str(time.time_ns()) + '.json'), error(exc))
            raise
