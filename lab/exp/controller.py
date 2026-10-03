"""One experiment owner; execution effects belong to independent executors."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import zipapp

from . import artifacts, projection
from .core import (Blocked, atomic, canonical, digest, error, identifier, locked, new_id,
                   process_identity, process_state, public, read, record, request, require)

ROOT = Path(__file__).resolve().parents[1]
FINISHED = {'exited', 'stopped', 'failed'}


def _source_files():
    files = [ROOT / 'exp' / '__init__.py', ROOT / '__init__.py', ROOT / '__main__.py', ROOT / 'control.py',
             ROOT / 'records.py', ROOT / 'assets.py', ROOT / 'otlp.py', ROOT / 'docker_endpoint.py']
    files += list((ROOT / 'exp').glob('*.py'))
    # ARC SDK child resources use the same execution identity and daemon authority.
    files += [ROOT / 'arc_bench' / name for name in (
        '__init__.py', 'playground.py', 'arc_bench_adapter.py', 'arc_bench_noop.py',
        'workspace_archive.py', 'local_job.py', 'docker_workspace.py', 'docker_admission.py', 'arc_artifacts.py', 'traceability.py')]
    files += [ROOT.parent / 'scripts' / name for name in ('__init__.py', 'agent_support.py', 'harness_layout.py', 'execution_context.py', 'execution_bootstrap.py', 'state_writer.py', 'runtime_resources.py')]
    files += [ROOT.parent / 'submission/exp_checkpoint.py']
    return list(dict.fromkeys(files))


def _source(destination):
    """Freeze explicit modules, not a mutable directory-wide controller snapshot."""
    destination.mkdir(parents=True)
    files = _source_files()
    for source in dict.fromkeys(files):
        target = destination / source.relative_to(ROOT.parent)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    submission = destination / 'submission'
    submission.mkdir(exist_ok=True)
    (submission / '__init__.py').write_text('')
    shutil.copy2(ROOT.parent / 'submission/exp_checkpoint.py', submission / 'exp_checkpoint.py')
    return files


def _executor(directory, store, runtime, selection):
    """Reuse one frozen source/dependency assembly and runner archive across runs."""
    files = {str(path.relative_to(ROOT.parent)): digest(path) for path in _source_files()}
    dependency = {'files': files, 'runtime': canonical(runtime['identity']),
                  'packages': runtime.get('packages'), 'python': runtime.get('python_version')}
    key = canonical(dependency)
    cache = Path(selection['selection']['cache_root']) / 'executors' / key
    index = cache / 'production.json'
    with locked(cache.parent / (key + '.lock')):
        if index.exists():
            value = read(index)
            if value['dependencies'] != dependency:
                raise ValueError('executor production selection changed')
            artifacts.verify(store, value['code'])
            if digest(cache / 'runner.pyz') != value['runner_sha256']:
                raise ValueError('cached runner archive changed')
        else:
            cache.mkdir(parents=True, exist_ok=True)
            source = cache / 'source'
            if source.exists():
                source.rename(cache / new_id('incomplete-source'))
            _source(source)
            _dependency_tree(source, runtime)
            if {str(path.relative_to(ROOT.parent)): digest(path) for path in _source_files()} != files:
                raise ValueError('execution sources changed during production')
            code = artifacts.publish(store, source, 'executor-code',
                provenance={'producer': 'exp.executor', 'production_key': key, 'dependencies': dependency},
                consumer='executor-' + key, purpose='frozen-code', request_id='executor-' + key)
            zipapp.create_archive(source, cache / 'runner.pyz', main='lab.exp.runner:main',
                                  interpreter='/usr/bin/env python3', compressed=True)
            value = {'dependencies': dependency, 'code': code, 'runner_sha256': digest(cache / 'runner.pyz')}
            atomic(index, value)
        consumer = 'run-' + canonical(str(directory))
        artifacts.retain(store, value['code'], consumer=consumer, purpose='executor',
                         request_id='retain-' + canonical([consumer, value['code']]))
        payload = artifacts.resolve(store, value['code'])
        for name, target in (('source', payload), ('runner.pyz', cache / 'runner.pyz')):
            path = directory / name
            if path.is_symlink() and path.resolve() == target.resolve():
                continue
            if path.exists() or path.is_symlink():
                raise ValueError('run frozen code path already occupied: ' + name)
            path.symlink_to(target.resolve(), target_is_directory=name == 'source')
    return value['code']


def _runtime(path, purpose='controller'):
    value = require(path if isinstance(path, dict) else read(path), 'runtime')
    if value.get('purpose') != purpose:
        raise ValueError(f'runtime must declare {purpose} purpose')
    from lab.assets import asset_inventory
    root = Path(value['root']).resolve(strict=True)
    if asset_inventory(root) != value['identity'] or not os.access(value['launcher'], os.X_OK):
        raise ValueError('frozen controller runtime identity changed')
    if digest(Path(value['launcher']).resolve(strict=True)) != value['interpreter_sha256']:
        raise ValueError('runtime interpreter changed outside its managed package root')
    return value


def _dependency_tree(source, runtime):
    result = subprocess.run([runtime['launcher'], '-B', '-c',
        'import json,google.protobuf,google.rpc,opentelemetry.proto; '
        'print(json.dumps([str(next(iter(m.__path__))) '
        'for m in (google.protobuf,google.rpc,opentelemetry.proto)]))'],
        capture_output=True, text=True, check=True)
    paths = json.loads(result.stdout)
    for origin, relative in zip(paths, ('google/protobuf', 'google/rpc', 'opentelemetry/proto')):
        shutil.copytree(origin, source / relative,
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '*.so', '*.pyd'))
    for namespace in ('google', 'google/rpc', 'opentelemetry', 'opentelemetry/proto'):
        (source / namespace / '__init__.py').touch(exist_ok=True)


def validate_recipe(spec):
    """Validate execution shape without installing assets or publishing inputs."""
    require(spec, 'experiment')
    if not isinstance(spec.get('authorization'), str) or not spec['authorization'].strip():
        raise ValueError('experiment needs explicit authorized scope; the string grants no execution permission')
    if not spec.get('jobs') or not isinstance(spec['jobs'], list):
        raise ValueError('experiment needs a nonempty jobs list')
    if type(spec.get('max_parallel')) is not int or spec['max_parallel'] < 1:
        raise ValueError('max_parallel must be an explicit positive integer')
    budget = spec.get('budget', {})
    if type(budget.get('max_attempts')) is not int or budget['max_attempts'] < len(spec['jobs']):
        raise ValueError('budget.max_attempts must cover declared jobs')
    storage = spec.get('storage', {})
    if type(storage.get('host_reserve_bytes')) is not int or storage['host_reserve_bytes'] < 1:
        raise ValueError('storage.host_reserve_bytes must be explicit and positive')
    ids = set()
    for raw in spec['jobs']:
        job = dict(raw)
        job_id = identifier(job['id'])
        if job_id in ids:
            raise ValueError('duplicate job identifier')
        ids.add(job_id)
        if job.get('purpose') not in {'build', 'prepare', 'generate', 'evaluate'}:
            raise ValueError('job purpose must be build/prepare/generate/evaluate')
        if 'target' in job:
            projection.validate_target(job['target'])
        kind = job.get('backend', {}).get('kind')
        if kind not in {'local', 'docker', 'hosted'}:
            raise ValueError('backend must be explicitly local/docker/hosted')
        if kind == 'docker' and 'network' in job['backend'] and job['backend']['network'] != 'none':
            raise ValueError('explicit Docker network currently supports only none; omit to retain default networking')
        if kind == 'hosted':
            from urllib.parse import urlsplit
            backend = job['backend']
            for field in ('competition_id', 'variant', 'task'):
                identifier(backend[field])
            if backend.get('credential_mode') not in {'self_funded', 'official_evaluation'}:
                raise ValueError('hosted backend requires explicit credential_mode')
            if backend['credential_mode'] == 'official_evaluation' and backend.get('allow_competition_credit') is not True:
                raise ValueError('official evaluation requires frozen competition-credit authorization')
            config = backend.get('model_config', {})
            if any(not isinstance(config.get(field), str) or not config[field].strip()
                   for field in ('model', 'visual_model', 'base_url', 'provider')):
                raise ValueError('hosted model_config must freeze model, visual_model, base_url and provider')
            url = urlsplit(config['base_url'])
            if url.scheme != 'https' or not url.hostname or url.username or url.password or url.query or url.fragment:
                raise ValueError('hosted model endpoint must be HTTPS without credentials')
        command = job.get('command')
        if kind != 'hosted' and (not isinstance(command, list) or not command or
                                any(not isinstance(arg, str) for arg in command)):
            raise ValueError('local/Docker job must supply argv')
        limits = job.get('limits', {})
        for field in ('storage_bytes', 'telemetry_bytes', 'wall_seconds'):
            if type(limits.get(field)) is not int or limits[field] < 1:
                raise ValueError(f'job {job_id} needs positive limit {field}')
        if not isinstance(job.get('environment', {}), dict) or any(
                not isinstance(k, str) or not isinstance(v, str) or
                re.search(r'api.?key|token|cookie|password|secret', k, re.I)
                for k, v in job.get('environment', {}).items()):
            raise ValueError('public environment must contain strings without credential values')
        for name, binding in job.get('inputs', {}).items():
            identifier(name)
            if isinstance(binding, str):
                continue
            if not isinstance(binding, dict) or not (
                    isinstance(binding.get('source'), str) or 'artifact_id' in binding and 'manifest_sha256' in binding or
                    set(binding) == {'from_job', 'output'} or set(binding) == {'from_production'}):
                raise ValueError('input must explicitly reference a source or artifact')
            if 'from_production' in binding and binding['from_production'] not in spec.get('productions', {}):
                raise ValueError('input names an undeclared material production')
            if 'from_job' in binding and job['purpose'] != 'evaluate':
                raise ValueError('published job outputs are only consumed by independent evaluation')
        for output in job.get('outputs', []):
            from .core import member
            identifier(output['name']); identifier(output['type']); member(output['path'])
    by_id = {job['id']: job for job in spec['jobs']}
    for job in spec['jobs']:
        for binding in job.get('inputs', {}).values():
            if isinstance(binding, dict) and 'from_job' in binding:
                source = by_id.get(binding['from_job'])
                if not source or source['purpose'] != 'generate' or not any(
                        output['name'] == binding['output'] for output in source.get('outputs', [])):
                    raise ValueError('evaluation input must name a declared generation output')
    return spec


def build(spec_path, directory, *, environment=None):
    spec_path, directory = Path(spec_path).resolve(strict=True), Path(directory).resolve()
    raw = read(spec_path)
    if raw.get('kind') == 'factory26.exp.intent':
        from .compiler import compile_intent
        bundle = directory.parent / (directory.name + '.definition')
        compiled = compile_intent(spec_path, bundle, environment=environment)
        spec_path = Path(compiled['recipe'])
    elif environment is not None:
        from .environment import resolve
        raw = resolve(raw, environment)
    definition_bytes = spec_path.read_bytes()
    recipe_sha256 = hashlib.sha256(definition_bytes).hexdigest()
    spec = require(json.loads(definition_bytes), 'experiment')
    for field in ('environment_resolution', 'resolved_productions'):
        if field in raw:
            spec[field] = raw[field]
    validate_recipe(spec)
    if (directory / 'experiment.json').exists():
        manifest = require(read(directory / 'experiment.json'), 'experiment')
        if manifest['recipe_sha256'] != recipe_sha256:
            raise ValueError('experiment specification changed; build a new experiment')
        verify(directory)
        return manifest
    if spec_path.is_relative_to(directory):
        raise ValueError('run data directory cannot contain its source definition')
    if spec.get('compilation') and (directory.is_relative_to(spec_path.parent) or spec_path.parent.is_relative_to(directory)):
        raise ValueError('run data and frozen compilation bundle must use separate directories')
    for source, expected in spec.get('compilation', {}).get('files', {}).items():
        if digest(source) != expected:
            raise ValueError('compiled input descriptor changed: ' + source)
    directory.mkdir(parents=True, mode=0o700, exist_ok=True)
    os.chmod(directory, 0o700)
    if (directory / 'build-intent.json').exists() and read(directory / 'build-intent.json')['recipe_sha256'] != recipe_sha256:
        raise ValueError('incomplete build belongs to a different recipe')
    if (directory / 'build-error.json').exists():
        (directory / 'build-error.json').rename(directory / ('build-error-' + new_id('receipt') + '.json'))
    atomic(directory / 'build-intent.json', record('build', recipe_sha256=recipe_sha256,
                                                  started_at=time.time(), phase='building'))
    store = directory / 'artifacts'
    if spec.get('environment_selection'):
        binding = spec.get('environment_resolution', spec['environment_selection'])
        shared = Path(binding['selection']['cache_root']) / 'artifacts'
        shared.mkdir(parents=True, exist_ok=True)
        if store.is_symlink():
            if store.resolve() != shared.resolve():
                raise ValueError('run artifact store differs from frozen environment')
        elif store.exists():
            raise ValueError('new environment run cannot replace an existing private artifact store')
        else:
            store.symlink_to(shared.resolve(), target_is_directory=True)
    bindings_path = directory / 'build-bindings.json'
    bindings = read(bindings_path) if bindings_path.exists() else {}
    def publish_input(key, origin, kind, provenance, expected=None):
        if key in bindings:
            ref = bindings[key]
            if artifacts.contents(origin) != artifacts.verify(store, ref)['contents']:
                raise ValueError('build source changed after publication: ' + key)
            return ref
        ref = artifacts.publish(store, origin, kind, provenance=provenance)
        if expected is not None and artifacts.verify(store, ref)['contents'] != expected:
            raise ValueError('source changed during compiled input publication: ' + key)
        bindings[key] = ref
        atomic(bindings_path, bindings)
        return ref
    try:
        definition_snapshot = publish_input('definition', spec_path, 'experiment-definition',
            {'source': str(spec_path), 'recipe_sha256': recipe_sha256},
            {'kind': 'file', 'sha256': recipe_sha256, 'executable': bool(spec_path.stat().st_mode & 0o111)})
        compilation_evidence = {}
        for source, expected_sha256 in spec.get('compilation', {}).get('files', {}).items():
            origin = Path(source)
            compilation_evidence[source] = publish_input('compile-input/' + canonical(source), origin, 'compiler-input',
                {'component': 'exp.compiler', 'source': source, 'source_sha256': expected_sha256},
                {'kind': 'file', 'sha256': expected_sha256, 'executable': bool(origin.stat().st_mode & 0o111)})
        runtime_paths = {}
        if spec.get('environment_selection'):
            from .environment import produce_runtimes
            runtime_paths = produce_runtimes(spec['environment_selection'],
                ('controller', 'runner') if any(job['backend']['kind'] != 'hosted' for job in spec['jobs']) else ('controller',),
                resolution=spec.get('environment_resolution'))
        runtime_path = (spec_path.parent / spec.get('controller_runtime', runtime_paths.get('controller', ''))).resolve(strict=True)
        runtime = _runtime(runtime_path)
        runner_runtime = None
        if any(job.get('backend', {}).get('kind') != 'hosted' for job in spec['jobs']):
            runner_runtime = _runtime((spec_path.parent / spec.get('runner_runtime', runtime_paths.get('runner', ''))).resolve(strict=True), 'runner')
        from .environment import produce_materials
        productions = produce_materials(spec, directory, store) if spec.get('productions') else {}
        jobs = []
        for raw in spec['jobs']:
            job = dict(raw)
            job_id = identifier(job['id'])
            kind = job['backend']['kind']
            inputs = {}
            for name, value in job.get('inputs', {}).items():
                identifier(name)
                if isinstance(value, str) or isinstance(value, dict) and 'source' in value:
                    origin = value if isinstance(value, str) else value['source']
                    origin = (spec_path.parent / origin).resolve(strict=True)
                    if isinstance(value, dict) and 'source_identity' in value and artifacts.contents(origin) != value['source_identity']:
                        raise ValueError('compiled source input changed: ' + job_id + '/' + name)
                    inputs[name] = publish_input(job_id + '/input/' + name, origin, 'input',
                        {'recipe_sha256': recipe_sha256, 'job_id': job_id, 'name': name},
                        value.get('source_identity') if isinstance(value, dict) else None)
                elif isinstance(value, dict) and 'artifact_id' in value:
                    ref = {key: value[key] for key in ('artifact_id', 'manifest_sha256')}
                    if value.get('store'):
                        artifacts.transfer((spec_path.parent / value['store']).resolve(strict=True), store, ref)
                    else:
                        artifacts.verify(store, ref)
                    inputs[name] = ref
                elif isinstance(value, dict) and set(value) == {'from_production'}:
                    produced = productions[value['from_production']]
                    inputs[name] = (produced['package'] if kind == 'hosted' else produced.get('delivery', produced['artifact'])) if name == 'agent' else produced['artifact']
                    if name == 'agent' and produced.get('definition'):
                        inputs['definition'] = produced['definition']
                        job['definition'] = produced['definition']
                        if produced.get('private_inputs',{}).get('tool_env'):
                            inputs['tool_credentials']=produced['private_inputs']['tool_env']
                        for asset in produced['definition_value']['assets']:
                            inputs['definition-' + asset['name']] = asset['reference']
                elif isinstance(value, dict) and set(value) == {'from_job', 'output'}:
                    identifier(value['from_job']); identifier(value['output'])
                    if job['purpose'] != 'evaluate':
                        raise ValueError('published job outputs are only consumed by independent evaluation')
                    inputs[name] = value
                else:
                    raise ValueError('input must explicitly reference a source or artifact')
            if job.get('arc_contract'):
                from lab.arc_bench.local_job import generation_inputs
                bound = {name: store / ref['artifact_id'] / 'payload' for name, ref in inputs.items()}
                job['arc_input_readback'] = generation_inputs(bound, bound['runner'], expected_sdk=job['arc_contract']['sdk'],
                    agent_provenance=artifacts._manifest(store, inputs['agent']).get('provenance'))
            for output in job.get('outputs', []):
                from .core import member
                identifier(output['name']); identifier(output['type']); member(output['path'])
            for field in ('checkpoint', 'prepared', 'stop_evidence'):
                if field in job:
                    binding = job[field]
                    if isinstance(binding, dict) and set(binding) == {'from_production'}:
                        ref = productions[binding['from_production']]['artifact']
                        inputs[field] = ref
                        job[field] = ref
                        continue
                    if not isinstance(binding, dict) or 'source' not in binding:
                        raise ValueError(f'{field} must reference explicit producer evidence source')
                    if 'source_identity' in binding and artifacts.contents((spec_path.parent / binding['source']).resolve(strict=True)) != binding['source_identity']:
                        raise ValueError('compiled producer input changed: ' + job_id + '/' + field)
                    inputs[field] = publish_input(job_id + '/' + field, (spec_path.parent / binding['source']).resolve(strict=True),
                                                     field.replace('_', '-'), binding.get('provenance', {}), binding.get('source_identity'))
                    job[field] = inputs[field]
            if 'prepared' in job:
                prepared_root = artifacts.resolve(store, job['prepared'])
                descriptor = read(prepared_root / 'harness-manifest.json')
                if descriptor.get('schema_version') not in (3, 4):
                    raise ValueError('new execution requires separated prepared content; old records keep their frozen executor')
                locations = read(prepared_root / 'provenance/asset-bindings.json')
                transferred = set()
                for asset in descriptor['definition_assets']:
                    reference = asset['artifact']
                    location = locations[asset['name']]
                    input_name = 'definition-' + asset['name']
                    inputs[input_name] = reference
                    job.setdefault('input_members', {})[input_name] = asset.get('member', '.')
                    if location.get('domain_identity', {}).get('kind') == 'docker':
                        target = job['backend']
                        if target.get('kind') != 'docker' or location['domain_identity']['daemon_id'] != target['endpoint']['daemon_id']:
                            raise Blocked('prepared definition is still daemon-local; select explicit cross-domain preparation')
                        job.setdefault('input_locations', {})[input_name] = {**location, 'reference': reference}
                        continue
                    key = (location['store'], canonical(reference))
                    if key not in transferred and not (store / reference['artifact_id'] / 'manifest.json').exists():
                        artifacts.transfer(location['store'], store, reference,
                                           consumer='prepared-' + descriptor['prepared_id'])
                        transferred.add(key)
                    artifacts.retain(store, reference, 'run-' + canonical(str(directory.resolve())),
                                     'prepared-definition/' + asset['name'],
                                     'retain-definition-' + canonical([str(directory.resolve()), asset])[:40])
                job['prepared_descriptor'] = descriptor
            job['inputs'] = inputs
            jobs.append(job)
        by_id = {job['id']: job for job in jobs}
        for job in jobs:
            for binding in job['inputs'].values():
                if 'from_job' in binding:
                    source_job = by_id.get(binding['from_job'])
                    if not source_job or source_job['purpose'] != 'generate' or not any(
                            row['name'] == binding['output'] for row in source_job.get('outputs', [])):
                        raise ValueError('evaluation input must name a declared generation output')
        source = directory / 'source'
        if spec.get('environment_selection'):
            code = _executor(directory, store, runtime, spec.get('environment_resolution', spec['environment_selection']))
        elif 'executor-code' in bindings:
            artifacts.materialize(store, bindings['executor-code'], source)
            code = bindings['executor-code']
        else:
            if source.exists():
                source.rename(directory / new_id('incomplete-source'))
            _source(source)
            _dependency_tree(source, runtime)
            code = publish_input('executor-code', source, 'executor-code', {'source': 'explicit exp module set'})
        if not spec.get('environment_selection'):
            zipapp.create_archive(source, directory / 'runner.pyz', main='lab.exp.runner:main',
                                  interpreter='/usr/bin/env python3', compressed=True)
        experiment_id = identifier(spec.get('experiment_id') or new_id('experiment'))
        value = record('experiment', experiment_id=experiment_id, authorization=spec['authorization'],
                       jobs=jobs, budget=spec['budget'], storage=spec['storage'], max_parallel=spec['max_parallel'],
                       recipe_sha256=recipe_sha256,
                       definition={'source': str(spec_path), 'sha256': recipe_sha256, 'artifact': definition_snapshot},
                       controller_runtime=runtime,
                       runner_runtime=runner_runtime,
                       code=code, runner_sha256=digest(directory / 'runner.pyz'), created_at=time.time(),
                       labels=spec.get('labels', {}))
        if 'compilation' in spec:
            value['compilation'] = spec['compilation']
            value['compilation_evidence'] = compilation_evidence
        for field in ('environment_selection', 'environment_resolution', 'derivation'):
            if field in spec:
                value[field] = spec[field]
        value['productions'] = productions
        atomic(directory / 'experiment.json', value)
        atomic(directory / 'build-intent.json', record('build', phase='published',
              experiment_id=experiment_id, recipe_sha256=recipe_sha256, finished_at=time.time()))
        return public(value)
    except BaseException as exc:
        atomic(directory / 'build-error.json', error(exc))
        raise


def verify(directory):
    directory = Path(directory).resolve(strict=True)
    value = require(read(directory / 'experiment.json'), 'experiment')
    _runtime_identity = value['controller_runtime']
    from lab.assets import asset_inventory
    if asset_inventory(Path(_runtime_identity['root'])) != _runtime_identity['identity']:
        raise ValueError('controller runtime was modified')
    if digest(Path(_runtime_identity['launcher']).resolve(strict=True)) != _runtime_identity['interpreter_sha256']:
        raise ValueError('controller interpreter changed')
    if value.get('runner_runtime'):
        runner_runtime = value['runner_runtime']
        if asset_inventory(Path(runner_runtime['root'])) != runner_runtime['identity']:
            raise ValueError('runner runtime was modified')
        if digest(Path(runner_runtime['launcher']).resolve(strict=True)) != runner_runtime['interpreter_sha256']:
            raise ValueError('runner interpreter changed')
    store = directory / 'artifacts'
    if value.get('definition'):
        definition = value['definition']
        snapshot = artifacts.verify(store, definition['artifact'])
        if snapshot['contents']['kind'] != 'file' or snapshot['contents']['sha256'] != definition['sha256'] or definition['sha256'] != value['recipe_sha256']:
            raise ValueError('consumed definition snapshot differs from the recorded recipe identity')
    code_manifest = artifacts.verify(store, value['code'])
    if ((directory / 'source').resolve() != (store / value['code']['artifact_id'] / 'payload').resolve() and
            artifacts.contents(directory / 'source') != code_manifest['contents']):
        raise ValueError('installed executor code differs from frozen artifact')
    if digest(directory / 'runner.pyz') != value['runner_sha256']:
        raise ValueError('frozen runner code changed')
    for job in value['jobs']:
        for ref in job.get('inputs', {}).values():
            if 'from_job' not in ref:
                artifacts.verify(store, ref)
    return value


def recover(source, intent_path, directory, *, environment):
    """Derive a new run; same-domain repair holds capture and never dispatches models."""
    source = Path(source).resolve(strict=True)
    intent_path = Path(intent_path).resolve(strict=True)
    directory = Path(directory).resolve()
    intent = require(read(intent_path), 'intent')
    recovery = intent.pop('recovery', None)
    if not isinstance(recovery, dict) or not {'production', 'target', 'repair'} <= set(recovery) or set(recovery) - {'production', 'target', 'repair', 'mode', 'request_id'}:
        raise ValueError('recover intent needs recovery {production, target, repair}')
    name = identifier(recovery['production'])
    productions = intent.setdefault('productions', {})
    if name in productions:
        raise ValueError('recovery production is already declared')
    checkpoint = read(source / 'harness-manifest.json')
    if checkpoint.get('kind') != 'factory26.harness.checkpoint':
        raise ValueError('recover SOURCE must be an explicit Harness checkpoint')
    mode = recovery.get('mode', 'snapshot-copy')
    if mode not in ('snapshot-copy', 'domain-state'):
        raise ValueError('recovery mode必须是snapshot-copy或domain-state')
    if mode == 'domain-state':
        from . import state, backends
        managed = require(read(source / 'managed-source.json'), 'managed-checkpoint-source')
        binding = managed['holder']
        operation_path = directory.parent / (directory.name + '.recovery-operation.json')
        operation_parameters = {'source': str(source), 'manifest_sha256': digest(source / 'harness-manifest.json'),
                                'target': recovery['target'], 'repair': recovery['repair'], 'intent_sha256': digest(intent_path)}
        with locked(operation_path.with_suffix('.lock')):
            if operation_path.exists():
                operation = require(read(operation_path), 'recovery-operation')
                if operation['parameters'] != operation_parameters or (recovery.get('request_id') and recovery['request_id'] != operation['request_id']):
                    raise ValueError('recovery operation belongs to changed inputs; retain original partial')
                request_id = operation['request_id']
            else:
                request_id = identifier(recovery.get('request_id') or new_id('recover'))
                atomic(operation_path, record('recovery-operation', request_id=request_id, parameters=operation_parameters))
        holder = state.query(binding)['holder']
        if holder['phase'] == 'closed':
            token = 'capture-' + canonical([binding['holder_id'], holder['generation'], request_id])[:32]
            holder = state.action(binding, 'capture-reopen', request_id + '--capture', {
                'expected_generation': holder['generation'], 'snapshot': holder['snapshot'],
                'capture_owner': 'capture-' + request_id, 'capture_token': token,
                'owner': {'kind': 'recovery', 'request_id': request_id}})['holder']
        if holder['phase'] not in ('snapshot-sealed', 'repairing', 'repaired') or holder['snapshot']['reference'] != managed['workspace_snapshot']['reference']:
            raise Blocked('domain-state recovery requires the unchanged original retained capture')
        capture = holder['capture']
        if holder['phase'] == 'snapshot-sealed':
            holder = state.action(binding, 'repair-begin', request_id + '--repair', {
                'expected_generation': holder['generation'], 'snapshot': holder['snapshot'],
                'capture_owner': capture['owner'], 'capture_token': capture['token'],
                'changes': list(recovery['repair'])})['holder']
        elif holder['repair']['request_id'] != request_id + '--repair':
            raise Blocked('state is held by another repair request')
        prepared_output = directory.parent / (directory.name + '.domain-prepared')
        if (prepared_output / 'harness-manifest.json').exists():
            prepared = read(prepared_output / 'harness-manifest.json')
            if prepared.get('allowed_changes') != recovery['repair'] or prepared.get('source_checkpoint', {}).get('checkpoint_id') != checkpoint['checkpoint_id']:
                raise Blocked('existing prepared metadata belongs to another repair source')
        else:
            prepared = backends.prepare_in_domain({'source': str(source), 'target': recovery['target'],
                'repair': recovery['repair'], 'state_binding': binding}, prepared_output)
        for category in recovery['repair']:
            if holder['phase'] == 'repaired' or category in holder['repair']['completed']:
                continue
            state.action(binding, 'repair-item', request_id + '--item--' + category, {
                'expected_generation': holder['generation'], 'capture_owner': capture['owner'],
                'capture_token': capture['token'], 'repair_request': request_id + '--repair',
                'item': category, 'readback': {'effects': prepared['repair_effects'],
                                             'manifest_sha256': digest(prepared_output / 'harness-manifest.json')}})
        if holder['phase'] != 'repaired':
            state.action(binding, 'repair-complete', request_id + '--repair-complete', {
                'expected_generation': holder['generation'], 'capture_owner': capture['owner'],
                'capture_token': capture['token'], 'repair_request': request_id + '--repair',
                'readback': {'compatible': prepared['status'] == 'complete', 'readback': prepared['readback']}})
        def replace_production(value):
            if isinstance(value, dict):
                if value == {'from_production': name}:
                    return {'source': str(prepared_output)}
                return {key: replace_production(item) for key, item in value.items()}
            if isinstance(value, list):
                return [replace_production(item) for item in value]
            return value
        intent = replace_production(intent)
    else:
        productions[name] = {'producer': 'prepare', 'source': str(source),
                             'target': recovery['target'], 'repair': recovery['repair']}
    intent['derivation'] = {'kind': 'recovery', 'source': str(source),
        'source_identity': checkpoint['source_identity'], 'checkpoint_id': checkpoint['checkpoint_id'],
        'manifest_sha256': digest(source / 'harness-manifest.json'),
        'intent_sha256': digest(intent_path), 'execution_permission': False}
    # Resolve original relative paths before moving the immutable definition outside run data.
    from .environment import resolve
    intent = resolve(intent, environment, base=intent_path.parent)
    def paths(job):
        for name, binding in list(job.get('inputs', {}).items()):
            if isinstance(binding, str):
                job['inputs'][name] = str((intent_path.parent / binding).resolve(strict=True))
            elif isinstance(binding, dict):
                for field in ('source', 'store'):
                    if field in binding:
                        binding[field] = str((intent_path.parent / binding[field]).resolve(strict=True))
        for field in ('checkpoint', 'prepared', 'stop_evidence'):
            if field in job and 'source' in job[field]:
                job[field]['source'] = str((intent_path.parent / job[field]['source']).resolve(strict=True))
        backend = job.get('backend', {})
        for target in (backend, backend.get('external_docker', {})):
            handoff = target.get('authority_handoff', {})
            if set(handoff) == {'source'}:
                handoff['source'] = str((intent_path.parent / handoff['source']).resolve(strict=True))
    for case in intent['cases'].values():
        paths(case)
    for variant in intent['variants'].values():
        paths(variant['generate'])
    if 'job' in intent['evaluation_policy']:
        paths(intent['evaluation_policy']['job'])
    for field in ('controller_runtime', 'runner_runtime'):
        if field in intent['execution']:
            intent['execution'][field] = str((intent_path.parent / intent['execution'][field]).resolve(strict=True))
    for cases in intent['selection_policy'].get('scores', {}).values():
        for binding in cases.values():
            binding['source'] = str((intent_path.parent / binding['source']).resolve(strict=True))
    definition = directory.parent / (directory.name + '.recovery-intent.json')
    with locked(definition.with_suffix('.lock')):
        if definition.exists() and read(definition) != intent:
            raise ValueError('recovery definition belongs to different inputs; choose a new run')
        atomic(definition, intent)
    return build(definition, directory, environment=environment)


def _backend(attempt):
    if attempt['job']['backend']['kind'] == 'hosted':
        from . import hosted
        return hosted
    from . import runner
    return runner


def source_stop_binding(prepared, stop):
    """Check the saved binding; a matching record is not a current stop proof."""
    if prepared.get('kind') != 'factory26.harness.prepared' or prepared.get('schema_version') != 3:
        raise Blocked('prepared artifact needs the public Harness prepared contract')
    if prepared.get('status') != 'complete' or prepared.get('acquisition', {}).get('status') != 'writer-closed':
        raise Blocked('prepared input lacks complete semantics or continuous writer-closed acquisition')
    if not stop:
        raise Blocked('prepared input valid; source stop evidence missing')
    if stop.get('kind') != 'factory26.exp.stop-evidence' or stop.get('schema_version') != 1:
        raise Blocked('new execution needs explicit source stop producer evidence')
    source = prepared['source_identity']
    if not isinstance(source, dict) or not source.get('execution_instance') or not isinstance(source.get('backend_identity'), dict):
        raise Blocked('prepared source execution identity is incomplete')
    if stop.get('source_identity') != source or stop.get('effect') != 'stopped':
        raise Blocked('stop evidence does not bind the prepared source execution instance')
    return source


def _launch_gate(attempt_dir, attempt):
    job, store = attempt['job'], attempt['artifact_store']
    descriptor = job.get('prepared_descriptor', {})
    if descriptor.get('state_binding'):
        from . import state
        binding = descriptor['state_binding']
        holder = state.query(binding)['holder']
        if holder['generation'] != binding['generation'] or holder['phase'] != 'repaired' or not holder.get('capture'):
            raise Blocked('domain-state entry requires the unchanged repaired holder capture')
        if descriptor.get('status') != 'complete' or descriptor.get('acquisition', {}).get('status') != 'writer-closed':
            raise Blocked('domain-state semantic readback is incomplete')
        atomic(attempt_dir / 'launch-gate.json', record('launch-gate', prepared=job['prepared'],
            holder=binding, snapshot=holder['snapshot'], execution_permission=False, verified_at=time.time()))
        deployment = read(attempt_dir / 'deployment.json')
        deployment['state_binding'] = binding
        atomic(attempt_dir / 'deployment.json', deployment)
        return
    if 'prepared' not in job:
        return
    prepared_path = artifacts.resolve(store, job['prepared'])
    manifest_path = prepared_path / 'harness-manifest.json' if prepared_path.is_dir() else prepared_path
    prepared = read(manifest_path)
    if prepared.get('kind') != 'factory26.harness.prepared' or prepared.get('schema_version') != 3:
        raise Blocked('prepared artifact needs the public Harness prepared contract')
    from submission.exp_checkpoint import validate
    validate(prepared_path, store)
    stop_ref = job.get('stop_evidence')
    if not stop_ref:
        raise Blocked('prepared input valid; source stop evidence missing')
    stop_path = artifacts.resolve(store, stop_ref)
    stop = read(stop_path / 'manifest.json' if stop_path.is_dir() else stop_path)
    source = source_stop_binding(prepared, stop)
    # Historical stopped bytes are insufficient to rule out a restarted resource.
    from .backends import observe_source
    observation = observe_source(source, read(attempt_dir / 'deployment.json'))
    if observation.get('effect') != 'stopped' or observation.get('source_identity') != source:
        raise Blocked('source execution current ownership/stopping unconfirmed')
    atomic(attempt_dir / 'launch-gate.json', record('launch-gate', prepared=job['prepared'],
           stop_evidence=stop_ref, source_observation=observation, verified_at=time.time()))


def _allocate(directory, manifest, job, *, retry_of=None, deployment=None, retry_request_id=None):
    attempt_id = new_id('attempt')
    path = directory / 'attempts' / attempt_id
    path.mkdir(parents=True, mode=0o700)
    value = record('attempt', attempt_id=attempt_id, experiment_id=manifest['experiment_id'],
                   job_id=job['id'], job=job, artifact_store=str(directory / 'artifacts'),
                   retry_of=retry_of, retry_request_id=retry_request_id, created_at=time.time())
    dispatch = request(attempt_id, 'dispatch', {'job_sha256': canonical(job)})
    value['dispatch_request_id'] = dispatch['request_id']
    atomic(path / 'attempt.json', value)
    atomic(path / 'request.json', dispatch)
    execution_runtime = manifest.get('runner_runtime') or manifest['controller_runtime']
    atomic(path / 'deployment.json', {'runtime': {'python': execution_runtime['launcher'],
           'source': str(directory / 'source'), 'identity': execution_runtime['identity'], 'asset': execution_runtime}, 'runner_path': str(directory / 'runner.pyz'),
           'executor_code': manifest['code'],
           **(deployment or {})})
    try:
        if job['backend']['kind'] != 'docker':
            for name, ref in job['inputs'].items():
                artifacts.materialize(directory / 'artifacts', ref, path / 'inputs' / name,
                                      path=job.get('input_members', {}).get(name, '.'))
        _launch_gate(path, value)
        return path, value
    except BaseException as exc:
        atomic(path / 'allocation-error.json', error(exc))
        raise


def _load_deployment(path):
    if path is None:
        return {}
    value = read(path)
    if not isinstance(value, dict) or set(value) - {'credential_file', 'cookie_file'}:
        raise ValueError('deployment only accepts explicit private credential_file/cookie_file references')
    return {name: str(Path(location).expanduser().resolve(strict=True)) for name, location in value.items()}


def start(directory, *, deployment=None):
    directory = Path(directory).resolve(strict=True)
    manifest = verify(directory)
    with locked(directory / '.dispatch.lock'):
        owner_path = directory / 'controller.json'
        if owner_path.exists():
            previous = read(owner_path)
            if previous.get('phase') == 'running':
                state = process_state(previous)
                if state == 'alive':
                    return record('acceptance', controller=public(previous), effect='already-running')
                if state == 'unknown':
                    raise Blocked('controller birth identity unknown; do not duplicate dispatch')
            atomic(directory / 'controllers' / (previous['controller_id'] + '.json'), previous)
        private = _load_deployment(deployment)
        if private:
            atomic(directory / 'deployment.json', private)
        source = directory / 'source'
        env = dict(os.environ, PYTHONPATH=str(source), PYTHONDONTWRITEBYTECODE='1')
        command = [manifest['controller_runtime']['launcher'], '-B', '-m', 'lab.exp.controller',
                   'internal_work', str(directory)]
        atomic(directory / 'controller-dispatch.json', record('request', action='controller',
              created_at=time.time(), effect='requested', request_id=new_id('request')))
        with (directory / 'controller.stdout.log').open('ab') as out, (directory / 'controller.stderr.log').open('ab') as err:
            child = subprocess.Popen(command, env=env, cwd=source, stdout=out, stderr=err, start_new_session=True)
        owner = record('controller', **process_identity(child.pid), phase='running',
                       controller_id=new_id('controller'), accepted_at=time.time())
        atomic(owner_path, owner)
        atomic(directory / 'controllers' / (owner['controller_id'] + '.json'), owner)
        return record('acceptance', controller=public(owner), effect='accepted')


def work(directory):
    directory = Path(directory).resolve(strict=True)
    with locked(directory / '.dispatch.lock'):
        owner = require(read(directory / 'controller.json'), 'controller')
        if owner['pid'] != os.getpid():
            raise Blocked('controller dispatch identity differs')
    with locked(directory / '.controller.lock', blocking=False):
        manifest = verify(directory)
        owner.update(started_at=time.time())
        atomic(directory / 'controller.json', owner)
        try:
            while True:
                attempts = []
                for path in sorted((directory / 'attempts').glob('*')):
                    if not (path / 'attempt.json').exists():
                        continue
                    attempt = require(read(path / 'attempt.json'), 'attempt')
                    executor = _backend(attempt)
                    try:
                        observation = executor.observe(path, live=True)
                        if observation.get('phase') in FINISHED:
                            if attempt['job']['backend']['kind'] == 'hosted' and observation.get('archive', {}).get('status') == 'not-exported':
                                observation = executor.export(path)
                            elif attempt['job']['backend']['kind'] != 'hosted' and observation.get('archive') == 'preserved':
                                _ingest_telemetry(path)
                        if observation.get('phase') in {'unaccepted', 'not-dispatched', 'accepted', 'snapshot-saved', 'run-created'} or observation.get('execution') == 'unaccepted':
                            if (path / 'allocation-error.json').exists():
                                if attempt['job']['backend']['kind'] != 'docker':
                                    for name, ref in attempt['job']['inputs'].items():
                                        artifacts.materialize(directory / 'artifacts', ref, path / 'inputs' / name,
                                              path=attempt['job'].get('input_members', {}).get(name, '.'))
                                _launch_gate(path, attempt)
                                (path / 'allocation-error.json').rename(path / (new_id('allocation-error') + '.json'))
                            observation = executor.dispatch(path)
                    except Exception as exc:
                        observation = {'phase': 'unknown', 'error': error(exc)}
                    atomic(path / 'observation.json', observation)
                    attempts.append((path, attempt, observation))
                attempts.sort(key=lambda row: row[1]['created_at'])
                for retry_path in sorted((directory / 'retries').glob('*.json')):
                    retry_request = require(read(retry_path), 'retry')
                    if any(row[1].get('retry_request_id') == retry_request['request_id'] for row in attempts):
                        continue
                    source_rows = [row for row in attempts if row[1]['attempt_id'] == retry_request['source_attempt']]
                    if len(source_rows) != 1 or source_rows[0][2].get('phase') not in FINISHED:
                        raise Blocked('retry requires known terminal source; unknown effects never authorize a second entry')
                    source_path, source_attempt, source_observation = source_rows[0]
                    if source_observation.get('archive') == 'pending':
                        continue
                    if sum(row[2].get('phase') not in FINISHED or row[2].get('archive') == 'pending' for row in attempts) >= manifest['max_parallel']:
                        continue
                    if source_attempt['job']['backend']['kind'] != 'hosted':
                        stop_evidence(directory, source_attempt['attempt_id'],
                                      source_path / (new_id('retry-stop-evidence') + '.json'))
                    if len(attempts) >= manifest['budget']['max_attempts']:
                        raise Blocked('retry exceeds frozen attempt budget')
                    private = read(directory / 'deployment.json') if (directory / 'deployment.json').exists() else {}
                    path, attempt = _allocate(directory, manifest, source_attempt['job'], retry_of=source_attempt['attempt_id'],
                                              retry_request_id=retry_request['request_id'], deployment=private)
                    observation = _backend(attempt).dispatch(path)
                    atomic(path / 'dispatch-observation.json', observation)
                    attempts.append((path, attempt, observation))
                assigned = {row[1]['job_id'] for row in attempts}
                active = [row for row in attempts if row[2].get('phase') not in FINISHED]
                if any(row[2].get('phase') == 'unknown' or row[2].get('pending') or
                       (row[0] / 'allocation-error.json').exists() for row in attempts):
                    raise Blocked('an attempt has unknown effects or preparation failure; retain its identity and inspect')
                for job in manifest['jobs']:
                    if job['id'] in assigned or len(active) >= manifest['max_parallel']:
                        continue
                    resolved = dict(job, inputs=dict(job['inputs']), input_locations=dict(job.get('input_locations', {})),
                                    input_members=dict(job.get('input_members', {})))
                    unavailable = False
                    for name, binding in job['inputs'].items():
                        if 'from_job' not in binding:
                            continue
                        producers = [row for row in attempts if row[1]['job_id'] == binding['from_job']]
                        if not producers or producers[-1][2].get('phase') not in FINISHED:
                            unavailable = True
                            break
                        production = producers[-1][2]
                        ref = production.get('artifacts', {}).get(binding['output'])
                        if production.get('exit_code') != 0:
                            raise Blocked('generation has no successful frozen output for evaluation: ' + binding['from_job'])
                        if not ref:
                            if production.get('outputs') == 'sealed':
                                raise Blocked('producer sealed without required named output: ' + binding['from_job'] + '/' + binding['output'])
                            unavailable = True
                            break
                        location = production.get('output_locations', {}).get(binding['output'])
                        if location:
                            target = job['backend']
                            if target['kind'] == 'docker' and location['domain_identity'].get('daemon_id') == target['endpoint']['daemon_id']:
                                resolved['input_locations'][name] = location
                            else:
                                from .backends import export_named
                                export_named(producers[-1][0], ref, location, directory / 'artifacts')
                                artifacts.verify(directory / 'artifacts', ref)
                        else:
                            artifacts.verify(directory / 'artifacts', ref)
                        resolved['inputs'][name] = ref
                        selected_member = production.get('output_members', {}).get(binding['output'], '.')
                        from .core import member
                        resolved['input_members'][name] = member(selected_member)
                    if unavailable:
                        continue
                    if job['backend']['kind'] == 'hosted' and any(
                        row[1]['job']['backend'].get('competition_id') == job['backend'].get('competition_id')
                        and row[1]['job']['backend']['kind'] == 'hosted' for row in active):
                        continue
                    if len(attempts) >= manifest['budget']['max_attempts']:
                        raise Blocked('experiment attempt budget exhausted')
                    if shutil.disk_usage(directory).free <= manifest['storage']['host_reserve_bytes']:
                        raise Blocked('experiment storage reserve unavailable')
                    private = read(directory / 'deployment.json') if (directory / 'deployment.json').exists() else {}
                    path, attempt = _allocate(directory, manifest, resolved, deployment=private)
                    result = _backend(attempt).dispatch(path)
                    atomic(path / 'dispatch-observation.json', result)
                    active.append((path, attempt, result)); attempts.append((path, attempt, result))
                    assigned.add(job['id'])
                if len(assigned) == len(manifest['jobs']) and not active:
                    if any(row[2].get('archive') == 'pending' for row in attempts):
                        time.sleep(2)
                        continue
                    if any(row[2].get('archive') == 'failed' for row in attempts):
                        raise Blocked('executions finished; terminal archive needs its legal continuation')
                    owner.update(phase='completed', finished_at=time.time(),
                                 outcome='failed' if any(row[2].get('exit_code') not in (None, 0) or
                                                        row[2].get('phase') == 'failed' for row in attempts) else 'finished',
                                 completion_scope='declared executions and evidence; platform verdict remains separate')
                    break
                time.sleep(2)
        except BaseException as exc:
            owner.update(phase='blocked' if isinstance(exc, Blocked) else 'failed', error=error(exc), finished_at=time.time())
            raise
        finally:
            atomic(directory / 'controller.json', owner)
            atomic(directory / 'controllers' / (owner['controller_id'] + '.json'), owner)
    return public(owner)


def status(directory):
    directory = Path(directory).resolve(strict=True)
    if directory.is_file():
        index = require(read(directory), 'index')
        rows = []
        for location in index['experiments']:
            try:
                rows.append(status((directory.parent / location).resolve()))
            except (OSError, ValueError) as exc:
                rows.append({'source': location, 'error': error(exc)})
        return record('status-index', experiments=rows, read_at=time.time())
    result = projection.facts(directory, time.time())
    if not result['frozen']:
        return public(result)
    if 'controller' in result:
        result['controller']['physical_state'] = process_state(result['controller'])
    return projection.stages(result, available_actions)


def available_actions(job, attempt, stage, value):
    """Describe controller operations, never grant permission from saved state.

    Export preserves the same entry. Retry is a separate authorized attempt.
    Every invoked operation retains its existing frozen executor/physical gates.
    """
    prefix = ['python', '-m', 'lab']
    directory = value['directory']
    owner = value.get('controller', {})
    alive = owner.get('phase') == 'running' and owner.get('physical_state') == 'alive'
    owner_unknown = owner.get('phase') == 'unknown' or (owner.get('phase') == 'running' and
                                                       owner.get('physical_state') == 'unknown')
    def action(name, label, argv=None, requires=()):
        return {'operation': name, 'label': label, 'argv': argv,
                'requires': list(requires), 'basis': 'saved facts; operation revalidates current gates'}
    if any(row.get('error') for row in value['attempts']) or owner_unknown or any(
            issue.get('component') == 'retry' for issue in value['blockers']):
        return [action('inspect', '核对不可读记录或 controller 出生身份；不能据此重派发')]
    if not attempt:
        if job.get('prepared'):
            prepared = stage['inputs'].get('prepared', {}).get('harness', {})
            stop = stage['inputs'].get('stop_evidence', {}).get('stop', {})
            try:
                source_stop_binding(prepared, stop)
                if prepared.get('status') != 'complete':
                    raise Blocked('prepared producer has not declared complete content')
            except (Blocked, KeyError) as exc:
                stage['blockers'].append({'component': 'source-gate', 'reason': str(exc),
                                           'evidence': stage['inputs'].get('prepared', {}).get('evidence')})
            else:
                stage['facts']['source_stop'] = {'status': 'saved-binding-matched',
                    'evidence': stage['inputs']['stop_evidence']['evidence'], 'current_observation': 'required-on-launch'}
        if len(value['attempts']) + len(value.get('pending_retries', [])) >= value['budget']['max_attempts']:
            stage['blockers'].append({'component': 'budget', 'reason': '冻结 attempt 预算已使用或预约，不能新增执行'})
        active = [row for row in value['attempts'] if row['execution'].get('phase', row['execution'].get('execution')) not in FINISHED]
        if any(row['execution'].get('phase', row['execution'].get('execution')) == 'unknown' or row['execution'].get('pending') for row in active):
            stage['blockers'].append({'component': 'execution', 'reason': '其它 attempt 的副作用尚未确认，controller 不继续派发'})
        if len(active) >= value['max_parallel']:
            stage['blockers'].append({'component': 'capacity', 'reason': '等待本实验冻结的并行额度'})
        if stage['blockers']:
            if alive and all(issue['component'] == 'capacity' for issue in stage['blockers']):
                return [action('wait', '等待当前 controller 的派发额度', prefix + ['wait', directory, '--timeout', '60'])]
            return [action('inspect', '先解决列出的前置阻塞；不能单独派发此阶段')]
        if alive:
            return [action('wait', '等待现有 controller 派发', prefix + ['wait', directory, '--timeout', '60'])]
        return [action('start', '启动或接续 controller', prefix + ['start', directory],
                       ('沿用本实验明确授权；私有 deployment 未保存时显式提供 --deployment',
                        '重新核对冻结 runtime、输入、预算、准入及物理来源；不保证当前可派发'))]
    observed = attempt['execution']
    phase = observed.get('phase', observed.get('execution'))
    if any(issue.get('component') == 'identity' for issue in attempt['errors']):
        return [action('inspect', '保存记录身份不一致，先核对原件；不发出控制')]
    if phase == 'unknown' or observed.get('pending') or attempt.get('allocation-error.json') or attempt.get('launch-error.json'):
        return [action('inspect', '保留当前 attempt，先核对原始错误和缺失证明；不重跑入口')]
    if phase == 'readiness_failed' and observed.get('entry_status') == 'not_requested':
        services = observed.get('services', {})
        repairs = [action('repair-ready', '修复失败服务 ' + name + '；保留同一入口与已就绪服务',
                          prefix + ['control', directory, attempt['attempt_id'], 'repair-ready', '--service', name],
                          ('先解决原始服务错误；调用时核对原 supervisor 出生身份、未请求入口及剩余 wall 预算',))
                   for name, service in services.items()
                   if name in ('collector', 'resource_evidence') and service.get('status') == 'failed']
        return repairs or [action('inspect', 'ready 服务失败但缺少公开服务身份，先核对原件')]
    if phase not in FINISHED:
        if alive:
            return [action('wait', '等待当前 attempt；不新增入口', prefix + ['wait', directory, '--timeout', '60'])]
        if stage['blockers']:
            return [action('inspect', '先核对观察故障及当前资源身份')]
        return [action('start', '重连接续原 attempt 的 controller', prefix + ['start', directory],
                       ('原 runner/平台身份保持；启动操作重新核对并按原请求接续',))]
    archive = observed.get('archive')
    sealed = (observed.get('exit_code') == 0 and job.get('outputs') and
              all(stage['outputs'].get(output['name'], {}).get('status') == 'published'
                  for output in job['outputs']))
    consumption = ([action('consume', '封口产物可按其位置消费；完整归档由原 owner 继续保全',
                          requires=('消费端重新核对位置、保留、字节及语义；归档状态不是消费证明',))]
                   if sealed else [])
    local_partial = [row for row in attempt.get('state_observations', [])
                     if row.get('domain_identity', {}).get('kind') == 'local'
                     and not row.get('snapshot', {}).get('reference')
                     and row.get('coverage', {}).get('descendant_writer_contract') != 'registered-or-no-detach-v1']
    if attempt['backend'] == 'local' and local_partial:
        return consumption + [action('inspect', 'Local原生工具派生writer关闭合同缺失；保留证据原件，核对coverage或选择支持完整捕获的Docker域，不能反复export')]
    needs_export = (archive == 'failed' or attempt['backend'] == 'docker' and
                    attempt.get('export.json', {}).get('status') != 'preserved' or
                    isinstance(archive, dict) and archive.get('status') == 'not-exported')
    if needs_export:
        if alive:
            return consumption + [action('wait', '等待当前 controller 收尾；不重跑入口', prefix + ['wait', directory, '--timeout', '60'])]
        if not observed.get('incarnation_id'):
            return [action('inspect', '执行 incarnation 缺失，不能发出 export 控制')]
        return consumption + [action('export', '接续保全或输运同一 attempt，保留原入口结果',
                       prefix + ['control', directory, attempt['attempt_id'], 'export'],
                       ('执行时核对同一 incarnation 和物理终态；不会重新运行 main',
                        '修复已报告的存储/输运条件；导出成功不代表 Harness prepared 完整'))]
    if archive == 'pending':
        return consumption + [action('wait' if alive else 'inspect', '等待或核对 runner 收尾；不能按入口退出推断保全完成')]
    if stage['status'] == 'failed':
        return [action('inspect', '先诊断入口失败；若确需新 attempt，另行明确 retry 授权和剩余预算')]
    if stage['blockers']:
        return [action('inspect', '核对剩余错误及产物覆盖，不把归档当作完整交付')]
    missing = [output['name'] for output in job.get('outputs', [])
               if stage['outputs'].get(output['name'], {}).get('status') != 'published']
    if missing:
        return [action('inspect', '核对尚未发布的声明输出：' + ', '.join(missing))]
    return [action('consume', '读取已发布产物；消费端重新核验字节、语义及来源门控')]


def _ingest_telemetry(path):
    """Consume saved source transports; this creates no receiver or polling loop."""
    from . import telemetry
    receipts = []
    source_index = path / 'telemetry-transports/sources.json'
    if not source_index.exists():
        atomic(path / 'telemetry-ingestion.json', record('telemetry-ingestion', coverage='unknown',
               reason='source transport index unavailable'))
        return
    sources = require(read(source_index), 'telemetry_sources')
    for source in sources['sources']:
        if not source.get('transport'):
            receipts.append(source)
            continue
        from .core import member
        location = path / member(source['transport'])
        if location.is_symlink() or not location.resolve().is_relative_to(path):
            raise ValueError('telemetry source transport escapes attempt')
        receipt = telemetry.ingest(path / 'telemetry-ingestion', location)
        receipts.append({'source': source, 'receipt': receipt})
    atomic(path / 'telemetry-ingestion.json', record('telemetry-ingestion', sources=receipts, captured_at=time.time()))


def _control_manifest(directory):
    """Authenticate the code/interpreter actually used for control, not job payloads."""
    directory = Path(directory).resolve(strict=True)
    value = read(directory / 'experiment.json')
    if value.get('kind') != 'factory26.exp.experiment' or value.get('schema_version') not in (1, 2):
        raise ValueError('unsupported frozen execution producer')
    identifier(value['experiment_id'])
    runtime = value['controller_runtime']
    if runtime.get('purpose') != 'controller' or not os.access(runtime['launcher'], os.X_OK):
        raise ValueError('frozen control interpreter is unavailable')
    if digest(Path(runtime['launcher']).resolve(strict=True)) != runtime['interpreter_sha256']:
        raise ValueError('frozen control interpreter identity changed')
    store = directory / 'artifacts'
    if value.get('definition'):
        definition = value['definition']
        manifest = artifacts._manifest(store, definition['artifact'])
        if manifest['contents']['kind'] != 'file' or manifest['contents']['sha256'] != definition['sha256'] or definition['sha256'] != value['recipe_sha256']:
            raise ValueError('frozen recipe identity changed')
    manifest = artifacts._manifest(store, value['code'])
    if artifacts.contents(directory / 'source') != manifest['contents']:
        raise ValueError('actual frozen controller code closure changed')
    return value


def _control_attempt(directory, manifest, attempt_id):
    path = Path(directory) / 'attempts' / identifier(attempt_id)
    attempt = require(read(path / 'attempt.json'), 'attempt')
    if attempt['attempt_id'] != attempt_id or attempt['experiment_id'] != manifest['experiment_id']:
        raise Blocked('control attempt belongs to another experiment')
    job = next((row for row in manifest['jobs'] if row['id'] == attempt['job_id']), None)
    actual_job = attempt['job']
    excluded = {'inputs', 'input_locations', 'input_members'}
    if not job or {key: item for key, item in actual_job.items() if key not in excluded} != {key: item for key, item in job.items() if key not in excluded}:
        raise Blocked('control attempt differs from its frozen recipe job')
    if set(actual_job['inputs']) != set(job['inputs']):
        raise Blocked('control input names differ from frozen job')
    for name, binding in job['inputs'].items():
        if 'from_job' not in binding:
            if actual_job['inputs'][name] != binding:
                raise Blocked('control static input differs from frozen job')
            continue
        matched = False
        for source_path in (Path(directory) / 'attempts').glob('*/attempt.json'):
            source = read(source_path)
            receipt_path = source_path.parent / 'execution.json'
            if source['job_id'] != binding['from_job'] or source['experiment_id'] != manifest['experiment_id'] or not receipt_path.exists():
                continue
            receipt = read(receipt_path)
            if receipt.get('exit_code') == 0 and receipt.get('artifacts', {}).get(binding['output']) == actual_job['inputs'][name] and receipt.get('output_members', {}).get(binding['output'], '.') == actual_job.get('input_members', {}).get(name, '.'):
                matched = True
                break
        if not matched:
            raise Blocked('control derived input has no frozen successful producer receipt')
    return path, attempt


def control(directory, attempt_id, action, *, request_id=None, parameters=None):
    directory = Path(directory).resolve(strict=True)
    manifest = _control_manifest(directory)
    frozen_module = directory / 'source/lab/exp/controller.py'
    if Path(__file__).resolve() != frozen_module.resolve():
        env = dict(os.environ, PYTHONPATH=str(directory / 'source'), PYTHONDONTWRITEBYTECODE='1')
        result = subprocess.run([manifest['controller_runtime']['launcher'], '-B', '-m', 'lab.exp.controller',
            'internal_control', str(directory), attempt_id, action,
            json.dumps({'request_id': request_id, 'parameters': parameters})],
            cwd=directory / 'source', env=env, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    path, attempt = _control_attempt(directory, manifest, attempt_id)
    executor = _backend(attempt)
    observed = executor.observe(path, live=True)
    incarnation = observed.get('incarnation_id') or observed.get('incarnation')
    if not incarnation:
        raise Blocked('executor incarnation unknown; cannot issue physical control')
    if (parameters or {}).get('expected_incarnation') not in (None, incarnation):
        raise Blocked('consumer expected a different execution incarnation')
    value = request(attempt_id, action, parameters or {}, request_id=request_id, incarnation=incarnation)
    target = path / 'requests' / (value['request_id'] + '.json')
    with locked(path / '.request.lock'):
        if target.exists():
            old = require(read(target), 'request')
            if any(old.get(k) != value.get(k) for k in ('action', 'parameters_sha256', 'expected_incarnation')):
                raise ValueError('request identity is bound to different control parameters')
            value = old
        else:
            atomic(target, value)
        result = executor.control(path, value)
        atomic(path / 'request-results' / (value['request_id'] + '.json'), result)
        return public(result)


def stop_evidence(directory, attempt_id, output):
    """Publish a separate current stopped observation, never infer it from a request."""
    directory = Path(directory).resolve(strict=True)
    manifest = _control_manifest(directory)
    frozen_module = directory / 'source/lab/exp/controller.py'
    if Path(__file__).resolve() != frozen_module.resolve():
        result = subprocess.run([manifest['controller_runtime']['launcher'], '-B', '-m', 'lab.exp.controller',
            'internal_stop_evidence', str(directory), attempt_id, str(Path(output).resolve())],
            cwd=directory / 'source', env=dict(os.environ, PYTHONPATH=str(directory / 'source'), PYTHONDONTWRITEBYTECODE='1'),
            capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    path = directory / 'attempts' / identifier(attempt_id)
    attempt = require(read(path / 'attempt.json'), 'attempt')
    observation = _backend(attempt).observe(path, live=True)
    if not observation.get('backend_identity') or not observation.get('incarnation_id'):
        raise Blocked('source has no exact self-owned execution identity')
    source = {'attempt_id': attempt_id, 'execution_instance': observation['incarnation_id'],
              'backend_identity': observation['backend_identity']}
    from .runner import observe_source
    current = observe_source(source)
    if current['effect'] != 'stopped':
        raise Blocked('source physical stop is not confirmed')
    if Path(output).exists():
        raise FileExistsError('stop evidence is immutable; choose a new output')
    value = record('stop-evidence', source_identity=source, **source, effect='stopped', observation=current,
                   captured_at=time.time())
    atomic(output, value)
    return public(value)


def _sdk_checkpoint(path, attempt, output, request_id, source_resource=None):
    """Select only registered, terminal-verified child sources; preserve inner birth."""
    from . import state, backends
    external_path = path / 'external-resources.json'
    if not external_path.exists():
        raise Blocked('SDK checkpoint lacks registered child resources')
    external = require(read(external_path), 'external_resources')
    candidates = []
    for entry in external['resources']:
        if entry.get('role') != 'execution':
            continue
        if source_resource and entry['authority_resource_id'] != source_resource:
            continue
        resource = read(Path(entry['resource_file']))
        if resource.get('state_binding') and resource.get('capture_source'):
            candidates.append((entry, resource))
    if len(candidates) != 1:
        raise Blocked('SDK checkpoint needs one explicit registered child source; use --source-resource; candidates=' +
                      ','.join(item[0]['authority_resource_id'] for item in candidates))
    entry, resource = candidates[0]
    source = read(Path(resource['capture_source']))
    binding = resource['state_binding']
    namespace = source['namespace']
    outer = read(path / 'binding.json')
    if (source.get('status') != 'writer-terminal-and-reception-verified'
            or resource.get('state') != 'exited' or not source.get('state_member')
            or not binding.get('selected_state') or not binding.get('snapshot')):
        raise Blocked('SDK child needs terminal verified reception and actual selected-state mapping')
    if (source['outer']['attempt_id'] != attempt['attempt_id']
            or source['outer']['incarnation'] != outer['incarnation_id']
            or source['attempt_id'] != entry['attempt_id']
            or source['incarnation'] != entry['incarnation']
            or any(namespace[key] != entry[key] for key in ('container_id', 'created', 'started_at', 'labels'))):
        raise Blocked('SDK source inner birth or outer relation differs from its registered execution')
    target = binding['authority']['target']
    physical = backends.exact_resource(target, entry)
    if physical['state'].get('Status') not in ('exited', 'dead'):
        raise Blocked('SDK child is not physically terminal')
    holder = state.query(binding)['holder']
    snapshot = binding['snapshot']
    if holder['generation'] != binding['generation'] or holder['snapshot']['reference'] != snapshot['reference']:
        raise Blocked('SDK source holder generation/snapshot changed')
    prefix = Path(source['workspace']['subpath'])
    selected = Path(source['state_member']).relative_to(prefix).as_posix()
    if binding['selected_state']['subpath'] != source['state_member']:
        raise Blocked('SDK selected state differs from its verified bootstrap mapping')
    source_identity = {'attempt_id': entry['attempt_id'], 'execution_instance': entry['incarnation'],
        'backend_identity': {'kind':'docker', 'endpoint':target['endpoint'],
            **{key:entry[key] for key in ('container_id','created','started_at','labels')},
            'image_id':namespace['image_id']}, 'outer_relation': source['outer']}
    stop = record('stop-evidence', source_identity=source_identity, **source_identity,
        effect='stopped', observation={'physical':physical, 'observed_at':time.time()}, captured_at=time.time())
    original_capture = holder['source_closure']
    stage = path / 'checkpoint-requests' / request_id
    stage.mkdir(parents=True, exist_ok=True)
    intent = record('checkpoint-request', attempt_id=attempt['attempt_id'], source_resource=entry['authority_resource_id'],
        request_id=request_id, output=str(Path(output).absolute()), source=source, snapshot=snapshot)
    if (stage/'request.json').exists() and read(stage/'request.json') != intent:
        raise Blocked('SDK checkpoint request parameters changed')
    atomic(stage/'request.json', intent)
    if (stage/'result.json').exists():
        return read(stage/'result.json')
    if (stage/'metadata-result.json').exists():
        prepared = read(stage/'metadata-result.json')
        result = prepared['result']
        if digest(Path(result['directory'])/'harness-manifest.json') != result['metadata_sha256']:
            raise Blocked('SDK checkpoint partial metadata changed after publication')
        backends.close_capture_helper(target, prepared['helper'], request_id+'--sdk-metadata-close')
        atomic(stage/'result.json', result)
        return result
    helper_resource_id = request_id + '--sdk-metadata--capture-helper'
    helper_row = backends.admission.query(target, helper_resource_id).get('resource')
    if helper_row and helper_row['phase'] == 'released':
        raise Blocked('SDK metadata helper already released; retained metadata/partial require a new request, never restart its physical resource')
    helper = backends.capture_helper(path, binding, request_id + '--sdk-metadata', assets_only=True)
    script = r"""import json,sys
from pathlib import Path
from lab.exp import artifacts
from lab.exp.core import read,atomic,record,member
from submission.exp_checkpoint import checkpoint
v=json.loads(sys.argv[1]); snapshot=v['snapshot']; source_binding=v['source']
root=artifacts.allocate_scratch('/assets','sdk-checkpoints/'+v['resource_id']+'/'+v['request_id'])
stage=Path(root); output=stage/'metadata'
if not (output/'harness-manifest.json').exists():
 source=artifacts.resolve('/assets',snapshot['reference'],v['selected'],consumer=snapshot['retention']['consumer'],retention=snapshot['retention'])
 whole=Path('/assets')/snapshot['reference']['artifact_id']/'payload'
 prefix=Path(source_binding['workspace']['subpath'])
 assembly=read(whole/Path(source_binding['records']['assembly']).relative_to(prefix))
 context=read(whole/Path(source_binding['records']['context']).relative_to(prefix))
 original=read(whole/Path(source_binding['records']['source_binding']).relative_to(prefix))
 if (original['attempt_id']!=v['identity']['attempt_id'] or original['incarnation']!=v['identity']['execution_instance']
     or original['state_member']!=source_binding['state_member'] or assembly['state']['root']!=v['logical_state']):
  raise ValueError('sealed SDK bootstrap identity/state mapping differs from public source descriptor')
 manifest=artifacts._manifest('/assets',snapshot['reference'])
 provenance=manifest['provenance']
 if provenance['source_namespace']['container_id']!=v['identity']['backend_identity']['container_id'] or provenance['closure']!=v['closure']:
  raise ValueError('SDK snapshot producer closure differs from the admitted source')
 token=provenance.get('capture_token')
 if not token:raise ValueError('SDK snapshot lacks its original managed capture token')
 proof=provenance['acquisition']
 closure=record('writer-closure',**proof['closure'],source_identity=v['identity'],closure_id=proof['capture_request_id'],capture_token=proof['capture_token'])
 atomic(stage/'identity.json',v['identity']);atomic(stage/'stop.json',v['stop'])
 layout=read(source/'harness-layout.json')
 bindings={row['name']:{**row['artifact'],'store':'/assets'} for row in layout['definitions']}
 checkpoint(source,output,stage/'identity.json',stage/'stop.json',acquisition=closure,
  definition_bindings=bindings,snapshot={**snapshot,'store':'/assets','member':v['selected']})
bindings=read(output/'provenance/asset-bindings.json')
for row in bindings.values():row.update({key:snapshot['location'][key] for key in ('domain_identity','volume_id','store_root') if key in snapshot['location']})
atomic(output/'provenance/asset-bindings.json',bindings)
print(json.dumps({'metadata_root':str(output),'files':{p.relative_to(output).as_posix():p.read_text() for p in output.rglob('*') if p.is_file()}}))
"""
    try:
        facts = json.loads(backends._owner_exec(target, helper, [target.get('python','python3'),'-B','-c',script,
            json.dumps({'snapshot':snapshot,'source':source,'identity':source_identity,'stop':stop,'closure':original_capture,
                'selected':selected,'logical_state':binding['selected_state']['logical_root'],
                'resource_id':entry['authority_resource_id'],'request_id':request_id})]).stdout)
        output = Path(output).absolute()
        if output.exists():
            raise Blocked('SDK checkpoint output already exists; preserve partial metadata')
        output.mkdir(parents=True)
        from .core import member
        for relative, content in facts['files'].items():
            destination = output/member(relative)
            destination.parent.mkdir(parents=True,exist_ok=True)
            destination.write_text(content)
        location = snapshot['location']
        atomic(output/'managed-source.json',record('managed-checkpoint-source',holder=binding,
            workspace_snapshot=snapshot,child_source=source,outer_relation=source['outer'],sdk_resume=False))
        atomic(output/'domain-resolver.json',record('checkpoint-domain-resolver',authority=binding['authority'],
            location=location,metadata_root=facts['metadata_root']))
        produced = read(output/'harness-manifest.json')
        result = record('checkpoint-result',checkpoint_id=produced['checkpoint_id'],directory=str(output),
            holder=binding,generation=binding['generation'],state_snapshot=produced['state_snapshot'],
            workspace_snapshot=snapshot,domain_location=location,status=produced['status'],
            source_resource=entry['authority_resource_id'],source_identity=source_identity,sdk_resume=False,
            metadata_sha256=digest(output/'harness-manifest.json'))
        atomic(stage/'metadata-result.json',record('checkpoint-metadata-result',result=result,helper=helper))
        backends.close_capture_helper(target,helper,request_id+'--sdk-metadata-close')
        atomic(stage/'result.json',result)
        return result
    except Exception as exc:
        atomic(stage/'error.json',record('error',**error(exc)))
        raise


def checkpoint(directory, attempt_id, output, *, request_id=None, source_resource=None):
    """Managed stopped capture; callers provide an attempt, never a closure claim."""
    directory = Path(directory).resolve(strict=True)
    manifest = _control_manifest(directory)
    frozen_module = directory / 'source/lab/exp/controller.py'
    request_id = identifier(request_id or new_id('checkpoint'))
    if Path(__file__).resolve() != frozen_module.resolve():
        result = subprocess.run([manifest['controller_runtime']['launcher'], '-B', '-m', 'lab.exp.controller',
            'internal_checkpoint', str(directory), identifier(attempt_id), str(Path(output).absolute()), request_id, json.dumps(source_resource)],
            cwd=directory / 'source', env=dict(os.environ, PYTHONPATH=str(directory / 'source'), PYTHONDONTWRITEBYTECODE='1'),
            capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    from . import state, backends, terminal
    path = directory / 'attempts' / identifier(attempt_id)
    attempt = require(read(path / 'attempt.json'), 'attempt')
    deployment = read(path / 'deployment.json')
    assembly = read(path / 'assembly.json') if (path / 'assembly.json').exists() else {}
    if source_resource or attempt['job']['backend'].get('external_docker'):
        return _sdk_checkpoint(path, attempt, output, request_id, source_resource)
    binding = deployment.get('state_binding') or assembly.get('state', {}).get('holder')
    if not binding:
        raise Blocked('source has no maintained managed state/writer contract; historical stop is not closure')
    stage = path / 'checkpoint-requests' / request_id
    stage.mkdir(parents=True, exist_ok=True)
    intent = record('checkpoint-request', attempt_id=attempt_id, request_id=request_id,
                    output=str(Path(output).absolute()), holder=binding)
    if (stage / 'request.json').exists() and read(stage / 'request.json') != intent:
        raise ValueError('checkpoint request belongs to different parameters')
    atomic(stage / 'request.json', intent)
    if (stage / 'result.json').exists():
        return read(stage / 'result.json')
    current_holder = state.query(binding)['holder']
    if current_holder['generation'] != binding['generation'] or (current_holder.get('writer') and current_holder['writer']['attempt_id'] != attempt_id):
        raise Blocked('old attempt no longer owns this mutable generation; consume its immutable saved checkpoint/snapshot')
    try:
        holder = state.begin_capture(path, binding, request_id,
            grace=attempt['job']['limits'].get('stop_grace_seconds', 10))
        receipt = read(path / 'execution.json')
        if binding['authority']['kind'] == 'docker':
            helper = backends.capture_helper(path, binding, request_id + '--reader')
            acquisition = state.capture_acquisition(binding, holder)
            snapshot = holder.get('snapshot')
            if snapshot:
                published = snapshot.get('acquisition')
                if (not published or published.get('kind') != 'managed-writer-capture'
                        or published['holder_id'] != binding['holder_id'] or published['generation'] != holder['generation']
                        or published['closure'] != holder['source_closure']):
                    raise Blocked('authority snapshot is not the same generation original managed capture')
            identity = {'attempt_id': attempt_id, 'execution_instance': receipt['incarnation_id'],
                        'backend_identity': receipt['backend_identity']}
            from .runner import observe_source
            observation = observe_source(identity)
            if observation['effect'] != 'stopped':
                raise Blocked('daemon source exact terminal birth is unconfirmed')
            stop = record('stop-evidence', source_identity=identity, **identity, effect='stopped',
                          observation=observation, captured_at=time.time())
            closure = record('writer-closure', **holder['source_closure'], source_identity=identity,
                closure_id=holder['capture']['request_id'], capture_token=holder['capture']['token'])
            script = r'''import json,sys
from pathlib import Path
from lab.exp.core import atomic,read
from lab.exp import artifacts
from submission.exp_checkpoint import checkpoint
request=json.loads(sys.argv[1])
root=artifacts.allocate_scratch('/assets','captures/'+request['attempt_id']+'/checkpoint-requests/'+request['request_id'])
metadata=Path(request['payload'])
assembly=read(metadata/'assembly.json')
atomic(root/'attempt.json',read(metadata/'attempt.json'));atomic(root/'assembly.json',assembly)
attempt=read(root/'attempt.json')
attempt['artifact_store']='/assets'
receipt=request['receipt']
snapshot=request['snapshot']
if snapshot is None:
 from lab.exp.terminal import seal_workspace
 snapshot=seal_workspace(root,attempt,receipt,physical_root=request['workspace'],acquisition=request['acquisition'],request_scope=request['request_id'])
selected=Path(assembly['state']['root']).relative_to(assembly['workspace']).as_posix()
proof=snapshot['acquisition']
closure={**request['closure'],**proof['closure'],'closure_id':proof['capture_request_id'],'capture_token':proof['capture_token']}
source=artifacts.resolve(snapshot['store'],snapshot['reference'],selected,consumer=request['attempt_id'],retention=snapshot['retention'])
atomic(root/'source-identity.json',request['identity'])
atomic(root/'stop-evidence.json',request['stop'])
output=root/'metadata'
if not (output/'harness-manifest.json').exists():
 checkpoint(source,output,root/'source-identity.json',root/'stop-evidence.json',acquisition=closure,snapshot={**snapshot,'member':selected})
print(json.dumps({'snapshot':snapshot,'metadata_root':str(output),'files':{p.relative_to(output).as_posix():p.read_text() for p in output.rglob('*') if p.is_file()}}))
'''
            target = binding['authority']['target']
            remote = json.loads(backends._owner_exec(target, helper,
                [target.get('python', 'python3'), '-B', '-c', script,
                 json.dumps({'attempt_id': attempt_id, 'request_id': request_id, 'snapshot': snapshot,
                             'identity': identity, 'stop': stop, 'closure': closure, 'acquisition':acquisition,
                             'receipt':receipt,'workspace':helper['capture_paths']['workspace'],'payload':helper['capture_paths']['metadata']})]).stdout)
            output = Path(output).absolute()
            if output.exists():
                raise FileExistsError('checkpoint metadata output already exists; original remains retained')
            output.mkdir(parents=True)
            from .core import member
            snapshot = remote['snapshot']
            if holder['snapshot'] is None:
                holder = state.bind_snapshot(binding,snapshot,request_id+'--snapshot')
            for relative, content in remote['files'].items():
                destination = output / member(relative)
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text(content)
            atomic(output / 'managed-source.json', record('managed-checkpoint-source', holder={**binding, 'source_attempt_directory': str(path)}, workspace_snapshot=snapshot))
            result = read(output / 'harness-manifest.json')
            location = {'domain_identity': {'kind': 'docker', 'daemon_id': binding['domain_identity']['daemon_id'], 'volume_id': read(path / 'resource.json')['artifact_volume']},
                        'volume_id': read(path / 'resource.json')['artifact_volume'], 'store_root': '/assets'}
            atomic(output / 'domain-resolver.json', record('checkpoint-domain-resolver',
                authority=binding['authority'], location=location, metadata_root=remote['metadata_root']))
            state.consumer_bindings(path, snapshot, holder['consumers'], binding=binding)
            backends.close_capture_helper(target, helper, request_id + '--reader-close')
            result_binding = record('checkpoint-result', checkpoint_id=result['checkpoint_id'],
                directory=str(output), holder=binding, generation=holder['generation'],
                state_snapshot=result['state_snapshot'], workspace_snapshot=snapshot,
                domain_location=location, status=result['status'])
            atomic(stage / 'result.json', result_binding)
            return result_binding
        acquisition = state.capture_acquisition(binding, holder)
        snapshot = holder.get('snapshot')
        if snapshot:
            published = snapshot.get('acquisition')
            if (not published or published.get('kind') != 'managed-writer-capture'
                    or published['holder_id'] != binding['holder_id'] or published['generation'] != holder['generation']
                    or published['closure'] != holder['source_closure']):
                raise Blocked('authority snapshot is not the same generation original managed capture')
        else:
            snapshot = terminal.seal_workspace(path,attempt,receipt,acquisition=acquisition,request_scope=request_id)
            holder = state.bind_snapshot(binding,snapshot,request_id+'--snapshot')
        snapshot.update(holder=binding['holder_id'], generation=holder['generation'], snapshot_request=request_id)
        state.consumer_bindings(path, snapshot, holder['consumers'], binding=binding)
        identity = {'attempt_id': attempt_id, 'execution_instance': receipt['incarnation_id'],
                    'backend_identity': receipt['backend_identity']}
        from .runner import observe_source
        current = observe_source(identity)
        if current['effect'] != 'stopped':
            raise Blocked('source physical stop is not confirmed after managed closure')
        stop = record('stop-evidence', source_identity=identity, **identity, effect='stopped',
                      observation=current, captured_at=time.time())
        atomic(stage / 'source-identity.json', identity)
        atomic(stage / 'stop-evidence.json', stop)
        proof = snapshot['acquisition']
        closure = record('writer-closure', **proof['closure'], source_identity=identity,
                         closure_id=proof['capture_request_id'], capture_token=proof['capture_token'])
        atomic(stage / 'writer-closure.json', closure)
        selected = Path(holder['locator']['path']).resolve(strict=True)
        workspace = Path(snapshot['source_root']).resolve(strict=True)
        relative = selected.relative_to(workspace).as_posix()
        source = terminal.resolve_workspace(snapshot, attempt)
        if relative != '.':
            source = source / relative
        from submission.exp_checkpoint import checkpoint as produce_checkpoint
        result = produce_checkpoint(source, output, stage / 'source-identity.json', stage / 'stop-evidence.json',
            acquisition=closure, snapshot={**snapshot, 'member': relative})
        atomic(Path(output) / 'managed-source.json', record('managed-checkpoint-source', holder={**binding, 'source_attempt_directory': str(path)}, workspace_snapshot=snapshot))
        result_binding = record('checkpoint-result', checkpoint_id=result['checkpoint_id'],
            directory=str(Path(output).absolute()), holder=binding, generation=holder['generation'],
            state_snapshot=result['state_snapshot'], workspace_snapshot=snapshot, status=result['status'])
        atomic(stage / 'result.json', result_binding)
        return result_binding
    except Exception as exc:
        atomic(stage / 'error.json', record('error', **error(exc)))
        raise


def access_control(directory, attempt_id, action, *, access_resource_id, container_id, request_id):
    """Console access participates in the same workspace writer/capture ordering."""
    directory = Path(directory).resolve(strict=True)
    manifest = _control_manifest(directory)
    path, attempt = _control_attempt(directory, manifest, attempt_id)
    target = attempt['job']['backend']
    if target['kind'] != 'docker':
        target = target.get('external_docker')
    if not target:
        raise Blocked('attempt has no managed Docker accessor domain')
    from . import admission, backends
    saved = admission.query(target, identifier(access_resource_id))
    resource = saved.get('resource')
    if not resource or resource['role'] != 'accessor' or resource.get('workspace') != (read(path / 'deployment.json').get('state_binding') or {}).get('holder_id', attempt_id):
        raise Blocked('accessor is outside the attempt workspace authority')
    from . import state
    state_binding = read(path / 'deployment.json').get('state_binding')
    if state_binding:
        holder = state.query(state_binding)['holder']
        old_generation = holder['generation'] != state_binding['generation'] or (holder.get('writer') and holder['writer']['attempt_id'] != attempt_id)
        if old_generation:
            if action == 'query' and (path / 'terminal-snapshot.json').exists():
                return {**saved, 'state_access': 'snapshot', 'snapshot': read(path / 'terminal-snapshot.json')}
            raise Blocked('accessor belongs to a previous state incarnation; live reuse is forbidden')
        if holder['phase'] != 'writable':
            if action == 'query' and holder.get('snapshot'):
                return {**saved, 'state_access': 'snapshot', 'snapshot': holder['snapshot']}
            if action == 'start':
                raise Blocked('old live accessor cannot enter a transferred state generation')
        elif action in ('start', 'query'):
            state.action(state_binding, 'consumer-register', 'consumer-' + access_resource_id, {
                'expected_generation': holder['generation'], 'consumer': {
                    'id': access_resource_id, 'resource_id': access_resource_id, 'kind': 'console',
                    'writer': True, 'locator': holder['locator']}})
    identity = resource.get('identity') or {}
    if identity.get('container_id') != container_id:
        raise Blocked('Console accessor differs from domain-owned physical birth')
    binding = {**identity, 'authority_resource_id': access_resource_id}
    if action == 'start':
        backends.managed(target, binding, 'writer-open', request_id + '--writer-open')
        return backends.managed(target, binding, 'start', request_id + '--start')
    if action == 'stop':
        physical = backends.managed(target, binding, 'stop', request_id + '--stop')
        backends.managed(target, binding, 'writer-close', request_id + '--writer-close')
        return physical
    if action == 'query':
        if access_resource_id not in (saved.get('workspace') or {}).get('writers', []):
            raise Blocked('running accessor has no domain workspace writer coverage')
        return {**saved, 'state_access': 'live', 'snapshot': None, 'managed_state': bool(state_binding)}
    raise ValueError('unsupported accessor action')


def retry(directory, attempt_id, authorization, *, request_id=None):
    directory = Path(directory).resolve(strict=True)
    manifest = verify(directory)
    if not isinstance(authorization, str) or not authorization.strip():
        raise ValueError('retry requires explicit scope; the string is a record, not permission')
    attempt_id = identifier(attempt_id)
    attempt = require(read(directory / 'attempts' / attempt_id / 'attempt.json'), 'attempt')
    request_id = identifier(request_id or new_id('retry'))
    target = directory / 'retries' / (request_id + '.json')
    value = record('retry', request_id=request_id, source_attempt=attempt_id, authorization=authorization)
    with locked(directory / '.retry.lock'):
        if target.exists():
            if read(target) != value:
                raise ValueError('retry request identity belongs to different parameters')
            return value
        attempts = list((directory / 'attempts').glob('*/attempt.json'))
        pending = list((directory / 'retries').glob('*.json'))
        consumed = {read(path).get('retry_request_id') for path in attempts}
        reserved = sum(read(path)['request_id'] not in consumed for path in pending)
        if len(attempts) + reserved >= manifest['budget']['max_attempts']:
            raise Blocked('frozen attempt budget has no retry capacity')
        atomic(target, value)
    return public(value)


def render(value):
    return projection.render(value)


if __name__ == '__main__':
    if sys.argv[1:2] == ['internal_work'] and len(sys.argv) == 3:
        work(sys.argv[2])
    elif sys.argv[1:2] == ['internal_control'] and len(sys.argv) == 6:
        print(json.dumps(control(sys.argv[2], sys.argv[3], sys.argv[4], **json.loads(sys.argv[5]))))
    elif sys.argv[1:2] == ['internal_stop_evidence'] and len(sys.argv) == 5:
        print(json.dumps(stop_evidence(sys.argv[2], sys.argv[3], sys.argv[4])))
    elif sys.argv[1:2] == ['internal_checkpoint'] and len(sys.argv) in (6, 7):
        print(json.dumps(public(checkpoint(sys.argv[2], sys.argv[3], sys.argv[4], request_id=sys.argv[5], source_resource=json.loads(sys.argv[6]) if len(sys.argv)==7 else None))))
    elif sys.argv[1:2] == ['internal_observe'] and len(sys.argv) == 4:
        directory = Path(sys.argv[2]).resolve(strict=True)
        manifest = _control_manifest(directory)
        attempt_path, attempt = _control_attempt(directory, manifest, sys.argv[3])
        print(json.dumps(public(_backend(attempt).observe(attempt_path, live=True))))
    elif sys.argv[1:2] == ['internal_access'] and len(sys.argv) == 6:
        print(json.dumps(public(access_control(sys.argv[2], sys.argv[3], sys.argv[4], **json.loads(sys.argv[5])))))
    else:
        raise SystemExit('internal controller invocation required')
