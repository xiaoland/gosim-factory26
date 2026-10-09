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


from lab.arc_bench.score_evidence import final_score


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
    if job.get('arc_contract'):
        if not model.get('bindings'):
            raise ValueError('ARC generation needs explicit native model bindings')
        job.setdefault('environment', {}).update(MODEL=config['model'], VISUAL_MODEL=config['visual_model'],
            OPENAI_BASE_URL=config['base_url'], FACTORY26_MODEL_PROVIDER=config['provider'])
    if job['backend']['kind'] == 'hosted':
        job['backend']['model_config'] = deepcopy(config)
    if 'bindings' in model:
        for binding in model['bindings'].values():
            _fields(binding, ('provider', 'base_url', 'credential_env', 'model', 'model_id'),
                    ('provider', 'base_url', 'credential_env'))
            if any(key in binding and (not isinstance(binding[key], str) or not binding[key].strip())
                   for key in ('model', 'model_id')):
                raise ValueError('native model binding requires non-empty model identifiers')
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
        if set(binding) == {'from_production'}:
            continue
        if 'source' in binding:
            source = (base / binding['source']).resolve()
            binding['source'] = str(source)
        if binding.get('store'):
            binding['store'] = str((base / binding['store']).resolve(strict=True))
    for name in ('checkpoint', 'prepared', 'stop_evidence'):
        if name in job:
            if set(job[name]) == {'from_production'}:
                continue
            source = (base / job[name]['source']).resolve()
            job[name]['source'] = str(source)
    for backend in (job['backend'], *([job['backend']['external_docker']] if job['backend'].get('external_docker') else [])):
        if backend.get('authority_handoff'):
            handoff = backend['authority_handoff']
            if isinstance(handoff, dict) and set(handoff) == {'source'}:
                source = (base / handoff['source']).resolve(strict=True)
                backend['authority_handoff'] = require(read(source), 'authority-handoff')
                files[str(source)] = digest(source)
            else:
                require(handoff, 'authority-handoff')


def compile_intent(intent_path, directory, *, environment=None):
    """Publish one immutable compile bundle; changed inputs require a new bundle."""
    intent_path, directory = Path(intent_path).resolve(strict=True), Path(directory).resolve()
    if intent_path.is_relative_to(directory):
        raise ValueError('frozen compilation bundle must be separate from its editable intent')
    intent_bytes = intent_path.read_bytes()
    intent_sha256 = hashlib.sha256(intent_bytes).hexdigest()
    intent = require(json.loads(intent_bytes), 'intent')
    if environment is not None:
        from .environment import resolve
        intent = resolve(intent, environment, base=intent_path.parent)
    _fields(intent, ('kind', 'schema_version', 'experiment_id', 'authorization', 'execution',
                     'cases', 'variants', 'models', 'targets', 'selection_policy', 'evaluation_policy', 'labels',
                     'productions', 'environment_selection', 'environment_resolution', 'resolved_productions', 'derivation'),
            ('experiment_id', 'authorization', 'execution', 'cases', 'variants', 'models', 'targets', 'selection_policy', 'evaluation_policy'))
    base = intent_path.parent
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    with locked(directory / '.compile.lock'):
        try:
            decision = select(intent['selection_policy'], intent['models'], base)
            execution = _fields(intent['execution'], ('controller_runtime', 'runner_runtime', 'max_parallel', 'budget', 'storage'),
                                ('max_parallel', 'budget', 'storage'))
            if not execution.get('controller_runtime') and not intent.get('environment_selection'):
                raise ValueError('execution needs a maintained environment or an explicit controller runtime')
            recipe = record('experiment', experiment_id=identifier(intent['experiment_id']),
                            authorization=intent['authorization'], execution_contract='explicit-request-v1', **deepcopy(execution), jobs=[], labels=intent.get('labels', {}))
            for field in ('productions', 'environment_selection', 'environment_resolution', 'resolved_productions', 'derivation'):
                if field in intent:
                    recipe[field] = deepcopy(intent[field])
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
                    recipe[field] = str((base / recipe[field]).resolve())
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
                operation = job.pop('operation', None)
                if operation is not None:
                    if operation != 'arc-local-generate' or job['purpose'] != 'generate':
                        raise ValueError('unsupported generation operation')
                    _fields(job, ('id', 'target', 'purpose', 'inputs', 'limits', 'labels', 'delivery_mode'), ('inputs', 'limits'))
                    delivery_mode = job.pop('delivery_mode', None)
                    if delivery_mode not in (None, 'copied-tree'):
                        raise ValueError('unsupported ARC delivery mode')
                    if not intent.get('environment_selection', {}).get('selection', {}).get('arc'):
                        raise ValueError('arc-local-generate requires environment.arc physical selections')
                    if not {'agent', 'requirements'} <= set(job['inputs']) or set(job['inputs']) - {'agent', 'requirements', 'template'} or set(case_backend) != {'competition_id', 'task'}:
                        raise ValueError('ARC generation needs agent/requirements and case competition_id/task')
                    from lab.arc_bench.local_job import job as local_job, sdk_role
                    arc = intent['environment_selection']['selection']['arc']
                    job['inputs']['runner'] = {'source': arc['sdk_source']}
                    job = local_job(job['id'], job['inputs'], job['limits'], arc['target'],
                                    case_backend['competition_id'], case_backend['task'],
                                    labels=job.get('labels'), arc_contract={'schema_version': 1,
                                    'operation': operation, 'sdk_source': arc['sdk_source'],
                                    'sdk': sdk_role(arc['sdk_source']),
                                    **({'delivery_mode': delivery_mode} if delivery_mode else {})})
                    job['target'] = {'case': target['case'], 'variant': target['variant']}
                else:
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
            recipe['compilation'] = {'intent_sha256': intent_sha256, 'compiler_sha256': digest(Path(__file__)), 'binding_phase': 'unresolved-plan', 'evidence_adapter_sha256': digest(Path(__import__('lab.arc_bench.score_evidence',fromlist=['x']).__file__)),
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
