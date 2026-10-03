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


def _source_files(role='runner'):
    """Freeze each executable role's actual imports, never a directory glob."""
    exp=('__init__.py','core.py','runner.py','backends.py','admission.py','state.py',
         'artifacts.py','telemetry.py','terminal.py','assembly.py','definitions.py')
    if role=='controller':
        exp += ('controller.py','compiler.py','environment.py','projection.py','delivery.py','readiness.py','hosted.py','history.py','analyze.py','__main__.py')
    elif role!='runner':
        raise ValueError('unknown executable code role')
    files=[ROOT/name for name in ('__init__.py','control.py','records.py','assets.py','otlp.py','docker_endpoint.py')]
    files += [ROOT/'exp'/name for name in exp]
    files += [ROOT/'arc_bench'/name for name in ('__init__.py','playground.py','arc_bench_adapter.py',
        'arc_bench_noop.py','workspace_archive.py','local_job.py','docker_workspace.py','docker_admission.py',
        'arc_artifacts.py','traceability.py')]
    scripts=('__init__.py','agent_support.py','harness_layout.py','execution_context.py','execution_bootstrap.py',
             'experiment_entry.py','state_writer.py','runtime_resources.py')
    if role=='controller':
        scripts += ('runtime.py','package_agent.py','braid_runtime.py','core.py','model_budget.mjs',
                    'hackathon_gateway.py','hackathon_gateway_compat.py','responses_compat.py','model_gateway_service.py')
        files += [ROOT/'__main__.py',ROOT/'arc_bench/score_evidence.py',ROOT/'arc_bench/hosted_monitor.py',ROOT/'arc_bench/provider_liveness.py',ROOT/'requirements.txt',ROOT.parent/'harness/model-gateway.json']
    files += [ROOT.parent/'scripts'/name for name in scripts]
    files += [ROOT.parent/'submission'/name for name in ('exp_checkpoint.py','recover_completed.py')]
    return list(dict.fromkeys(files))


def _source(destination, role='runner'):
    """Freeze explicit modules, not a mutable directory-wide controller snapshot."""
    destination.mkdir(parents=True)
    files = _source_files(role)
    for source in dict.fromkeys(files):
        target = destination / source.relative_to(ROOT.parent)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    submission = destination / 'submission'
    submission.mkdir(exist_ok=True)
    (submission / '__init__.py').write_text('')
    shutil.copy2(ROOT.parent / 'submission/exp_checkpoint.py', submission / 'exp_checkpoint.py')
    return files


def _executor(directory, store, runtime, selection, *, role='runner'):
    """Reuse one frozen source/dependency assembly and runner archive across runs."""
    files = {str(path.relative_to(ROOT.parent)): digest(path) for path in _source_files(role)}
    dependency = {'role':role,'files': files, 'runtime': canonical(runtime['identity']),
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
            if role=='runner' and digest(cache / 'runner.pyz') != value['runner_sha256']:
                raise ValueError('cached runner archive changed')
        else:
            cache.mkdir(parents=True, exist_ok=True)
            source = cache / 'source'
            if source.exists():
                source.rename(cache / new_id('incomplete-source'))
            _source(source,role)
            _dependency_tree(source, runtime)
            if {str(path.relative_to(ROOT.parent)): digest(path) for path in _source_files(role)} != files:
                raise ValueError('execution sources changed during production')
            code = artifacts.publish(store, source, 'executor-code',
                provenance={'producer': 'exp.executor', 'production_key': key, 'dependencies': dependency},
                consumer='executor-' + key, purpose='frozen-code', request_id='executor-' + key)
            value = {'dependencies':dependency,'code':code}
            if role=='runner':
                zipapp.create_archive(source,cache/'runner.pyz',main='lab.exp.runner:main',interpreter='/usr/bin/env python3',compressed=True)
                value['runner_sha256']=digest(cache/'runner.pyz')
            atomic(index, value)
        consumer = 'run-' + canonical(str(directory))
        artifacts.retain(store, value['code'], consumer=consumer, purpose='executor',
                         request_id='retain-' + canonical([consumer, value['code']]))
        payload = artifacts.resolve(store, value['code'])
        placements=[('source' if role=='runner' else 'controller-source',payload)]
        if role=='runner': placements.append(('runner.pyz',cache/'runner.pyz'))
        for name,target in placements:
            path = directory / name
            if path.is_symlink() and path.resolve() == target.resolve():
                continue
            if path.exists() or path.is_symlink():
                raise ValueError('run frozen code path already occupied: ' + name)
            path.symlink_to(target.resolve(), target_is_directory=name == 'source')
    return value['code']


def _runtime(path, purpose='controller', *, verification_window=None):
    value = require(path if isinstance(path, dict) else read(path), 'runtime')
    if value.get('purpose') != purpose:
        raise ValueError(f'runtime must declare {purpose} purpose')
    from lab.assets import asset_inventory
    root = Path(value['root']).resolve(strict=True)
    readback=(str(root),json.dumps(value['identity'],sort_keys=True))
    if verification_window is None or readback not in verification_window:
        if asset_inventory(root) != value['identity']:
            raise ValueError('frozen runtime identity changed')
        if verification_window is not None: verification_window.add(readback)
    if not os.access(value['launcher'], os.X_OK):
        raise ValueError('frozen runtime launcher is not executable')
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
    if type(budget.get('max_attempts')) is not int or budget['max_attempts'] < 1:
        raise ValueError('budget.max_attempts must be an explicit positive execution limit')
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


def build(spec_path, directory, *, environment=None, job_id):
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
    selected = [job for job in spec['jobs'] if job['id'] == job_id]
    if len(selected) != 1:
        raise ValueError('build requires one explicitly declared job: ' + str(job_id))
    declared_jobs = {job['id']: job for job in spec['jobs']}
    spec = {**spec, 'jobs': selected}
    if (directory / 'experiment.json').exists():
        manifest = require(read(directory / 'experiment.json'), 'experiment')
        if manifest['recipe_sha256'] != recipe_sha256 or manifest.get('selected_job') != job_id:
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
    if (directory / 'build-intent.json').exists() and (read(directory / 'build-intent.json')['recipe_sha256'] != recipe_sha256 or read(directory / 'build-intent.json').get('selected_job') != job_id):
        raise ValueError('incomplete build belongs to a different recipe')
    if (directory / 'build-error.json').exists():
        (directory / 'build-error.json').rename(directory / ('build-error-' + new_id('receipt') + '.json'))
    atomic(directory / 'build-intent.json', record('build', recipe_sha256=recipe_sha256, selected_job=job_id,
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
        runtime_readback=set()
        if spec.get('environment_selection'):
            from .environment import produce_runtimes
            runtime_paths = produce_runtimes(spec['environment_selection'],
                ('controller', 'runner') if any(job['backend']['kind'] != 'hosted' for job in spec['jobs']) else ('controller',),
                resolution=spec.get('environment_resolution'), verification_window=runtime_readback)
        runtime_path = (spec_path.parent / spec.get('controller_runtime', runtime_paths.get('controller', ''))).resolve(strict=True)
        runtime = _runtime(runtime_path, verification_window=runtime_readback)
        runner_runtime = None
        if any(job.get('backend', {}).get('kind') != 'hosted' for job in spec['jobs']):
            runner_runtime = _runtime((spec_path.parent / spec.get('runner_runtime', runtime_paths.get('runner', ''))).resolve(strict=True), 'runner', verification_window=runtime_readback)
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
                        for private_name,reference in produced.get('private_inputs',{}).items():
                            inputs[{'tool_env':'tool_credentials','provider_env':'provider_credentials'}[private_name]]=reference
                        for input_name,reference in produced.get('inputs',{}).items():
                            inputs[input_name]=reference
                        for asset in produced['definition_value']['assets']:
                            inputs['definition-' + asset['name']] = asset['reference']
                            job.setdefault('input_members',{})['definition-'+asset['name']]=asset.get('member','.')
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
            if job.get('arc_contract'):
                from lab.arc_bench.local_job import sdk_role
                sdk_root=Path(next(value['source'] for name,value in raw.get('inputs',{}).items() if name=='runner'))
                job['arc_contract']['sdk']=sdk_role(sdk_root)
            job['inputs'] = inputs
            jobs.append(job)
        by_id = declared_jobs
        for job in jobs:
            for binding in job['inputs'].values():
                if 'from_job' in binding:
                    source_job = by_id.get(binding['from_job'])
                    if not source_job or source_job['purpose'] != 'generate' or not any(
                            row['name'] == binding['output'] for row in source_job.get('outputs', [])):
                        raise ValueError('evaluation input must name a declared generation output')
        if not spec.get('environment_selection'):
            raise ValueError('new build requires a declared environment for role code production')
        selection=spec.get('environment_resolution',spec['environment_selection'])
        runner_code=_executor(directory,store,runner_runtime or runtime,selection,role='runner')
        code=_executor(directory,store,runtime,selection,role='controller')
        experiment_id = identifier(spec.get('experiment_id') or new_id('experiment'))
        value = record('experiment', experiment_id=experiment_id, authorization=spec['authorization'],
                       execution_contract='explicit-request-v1', selected_job=job_id,
                       jobs=jobs, budget=spec['budget'], storage=spec['storage'], max_parallel=spec['max_parallel'],
                       recipe_sha256=recipe_sha256,
                       definition={'source': str(spec_path), 'sha256': recipe_sha256, 'artifact': definition_snapshot},
                       controller_runtime=runtime,
                       runner_runtime=runner_runtime,
                       code=code, runner_code=runner_code, code_roles={'controller':code,'runner':runner_code}, runner_sha256=digest(directory / 'runner.pyz'), created_at=time.time(),
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
    for role,reference in value['code_roles'].items():
        source=directory/('source' if role=='runner' else 'controller-source')
        code_manifest=artifacts.verify(store,reference)
        if source.resolve() != (store/reference['artifact_id']/'payload').resolve() and artifacts.contents(source)!=code_manifest['contents']:
            raise ValueError('installed '+role+' code differs from frozen role artifact')
    if digest(directory / 'runner.pyz') != value['runner_sha256']:
        raise ValueError('frozen runner code changed')
    for job in value['jobs']:
        for ref in job.get('inputs', {}).values():
            if 'from_job' not in ref:
                artifacts.verify(store, ref)
    return value


def recover(source, intent_path, directory, *, environment, job_id, request_id,
            action='continue', execute=False, input_bindings=None, deployment=None):
    """Continue one explicit recovery transaction; prepare-only never requests entry."""
    directory = Path(directory).resolve()
    if action == 'query':
        return _recover_request(source, intent_path, directory, environment=environment, job_id=job_id,
            request_id=request_id, action=action, execute=execute, input_bindings=input_bindings, deployment=deployment)
    operation_lock = directory.parent / (directory.name + '.recovery-owner.lock')
    with locked(operation_lock, blocking=False):
        try:
            return _recover_request(source, intent_path, directory, environment=environment, job_id=job_id,
                request_id=request_id, action=action, execute=execute, input_bindings=input_bindings, deployment=deployment)
        except Exception as exc:
            atomic(directory.parent / (directory.name + '.recovery-error.json'), record('error',
                request_id=request_id, action=action, **error(exc)))
            raise


def _recover_request(source, intent_path, directory, *, environment, job_id, request_id, action="continue", execute=False, input_bindings=None, deployment=None):
    """Derive a new run; same-domain repair holds capture and never dispatches models."""
    directory = Path(directory).resolve()
    request_id = identifier(request_id)
    job_id = identifier(job_id)
    operation_path = directory.parent / (directory.name + '.recovery-operation.json')
    if action not in ('query', 'continue', 'abort'):
        raise ValueError('recovery action must be query, continue or abort')
    if action == 'query':
        operation = require(read(operation_path), 'recovery-operation')
        if operation['request_id'] != request_id:
            raise ValueError('recovery query must name the original request')
        return operation
    if action == 'abort':
        operation = require(read(operation_path), 'recovery-operation')
        if operation['request_id'] != request_id:
            raise ValueError('recovery abort must name the original request')
        if operation.get('execution'):
            raise Blocked('execution already accepted; stop its exact attempt, not the preparation operation')
        if operation.get('holder'):
            from . import state, backends
            backends.abort_recovery_assets(operation['holder'], request_id + '--assets')
            backends.finish_recovery_preparation(operation['holder'], request_id)
            state.abort_recovery(operation['holder'], request_id)
        operation.update(phase='aborted', aborted_at=time.time(), state_preserved=True)
        atomic(operation_path, operation)
        return operation
    source = Path(source).resolve(strict=True)
    intent_path = Path(intent_path).resolve(strict=True)
    directory = Path(directory).resolve()
    intent = require(read(intent_path), 'intent')
    recovery = intent.pop('recovery', None)
    if not isinstance(recovery, dict) or not {'production', 'target', 'repair'} <= set(recovery) or set(recovery) - {'production', 'target', 'repair', 'mode', 'request_id'}:
        raise ValueError('recover intent needs recovery {production, target, repair}')
    if recovery.get('request_id') not in (None, request_id):
        raise ValueError('recovery intent request_id differs from the explicit operation request')
    name = identifier(recovery['production'])
    productions = intent.setdefault('productions', {})
    if name in productions:
        raise ValueError('recovery production is already declared')
    try:
        checkpoint = read(source / 'harness-manifest.json')
    except FileNotFoundError as exc:
        exc.add_note('recover SOURCE 必须是包含 harness-manifest.json 的显式 Harness checkpoint 目录；'
                     '平台 workspace ZIP 或 partial 导出不能直接恢复，不从 run 目录或应用 ZIP 猜测 checkpoint。')
        raise
    if checkpoint.get('kind') != 'factory26.harness.checkpoint':
        raise ValueError('recover SOURCE must be an explicit Harness checkpoint')
    operation_parameters = {'source': str(source), 'manifest_sha256': digest(source / 'harness-manifest.json'),
        'target': recovery['target'], 'repair': recovery['repair'], 'intent_sha256': digest(intent_path),
        'environment_sha256': digest(Path(environment)), 'job_id': job_id, 'input_bindings': input_bindings or {}, 'deployment': str(Path(deployment).resolve()) if deployment else None}
    with locked(operation_path.with_suffix('.lock')):
        if operation_path.exists():
            operation = require(read(operation_path), 'recovery-operation')
            if operation['request_id'] != request_id or operation['parameters'] != operation_parameters:
                raise ValueError('recovery request belongs to changed inputs; retain its original partial')
            if operation.get('phase') == 'aborted':
                raise Blocked('recovery was explicitly aborted; use a new request and destination')
        else:
            operation = record('recovery-operation', request_id=request_id, parameters=operation_parameters,
                phase='accepted', accepted_at=time.time())
            atomic(operation_path, operation)
    mode = recovery.get('mode', 'snapshot-copy')
    if mode not in ('snapshot-copy', 'domain-state'):
        raise ValueError('recovery mode必须是snapshot-copy或domain-state')
    if mode == 'domain-state':
        from . import state, backends
        managed = require(read(source / 'managed-source.json'), 'managed-checkpoint-source')
        binding = managed['holder']
        operation['holder'] = binding
        atomic(operation_path, operation)
        if 'asset_dependencies' not in operation:
            rows = recovery['repair'].get('definition_assets', [])
            dependencies = []
            for row in rows:
                if not row.get('store'):
                    raise ValueError('replacement definition requires an explicit source store before capture')
                manifest = artifacts.verify(row['store'], row['artifact'], path=row.get('member', '.'))
                hold = artifacts.retain(row['store'], row['artifact'], request_id, 'recovery-definition',
                                        request_id + '--definition--' + canonical(row)[:20])
                dependencies.append({'selection': row, 'manifest_sha256': row['artifact']['manifest_sha256'], 'retention': hold})
            # Domain installation is immutable transport, before entering repair/capture.
            installed = backends.install_recovery_assets(binding, rows, request_id + '--assets')
            operation.update(asset_dependencies=dependencies, installed_definitions=installed, phase='assets-ready')
            atomic(operation_path, operation)
        effective_repair = {**recovery['repair'], 'definition_assets': operation.get('installed_definitions', [])}
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
            if prepared.get('allowed_changes') != effective_repair or prepared.get('source_checkpoint', {}).get('checkpoint_id') != checkpoint['checkpoint_id']:
                raise Blocked('existing prepared metadata belongs to another repair source')
        else:
            prepared = backends.prepare_in_domain({'source': str(source), 'target': recovery['target'],
                'repair': effective_repair, 'state_binding': binding}, prepared_output)
        backends.finish_recovery_preparation(binding, request_id)
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
    prepared_run = build(definition, directory, environment=environment, job_id=job_id)
    operation.update(phase='prepared', experiment=str(directory), prepared_at=time.time(), execution_permission=False)
    atomic(operation_path, operation)
    if execute:
        accepted = start(directory, job_id=job_id, request_id=request_id + '--execute', input_bindings=input_bindings, deployment=deployment)
        operation.update(phase='execution-accepted', execution=accepted, execution_permission=True)
        atomic(operation_path, operation)
    return operation


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


def _allocate(directory, manifest, job, *, attempt_id, request_id, retry_of=None,
              deployment=None, input_bindings=None):
    """Persist one request's attempt before materialization or execution effects."""
    path = directory / 'attempts' / identifier(attempt_id)
    value = record('attempt', attempt_id=attempt_id, experiment_id=manifest['experiment_id'],
                   job_id=job['id'], job=job, artifact_store=str(directory / 'artifacts'),
                   retry_of=retry_of, input_bindings=input_bindings or {},
                   dispatch_request_id=request_id, created_at=time.time())
    if (path / 'attempt.json').exists():
        saved = require(read(path / 'attempt.json'), 'attempt')
        if any(saved.get(key) != value.get(key) for key in value if key != 'created_at'):
            raise ValueError('request already binds a different attempt definition')
        value = saved
    else:
        atomic(path / 'attempt.json', value)
    if not (path / 'request.json').exists():
        atomic(path / 'request.json', request(attempt_id, 'dispatch',
               {'job_sha256': canonical(job)}, request_id=request_id))
    execution_runtime = manifest.get('runner_runtime') or manifest['controller_runtime']
    private = {'runtime': {'python': execution_runtime['launcher'],
               'source': str(directory / 'source'), 'identity': execution_runtime['identity'],
               'asset': execution_runtime}, 'runner_path': str(directory / 'runner.pyz'),
               'executor_code': manifest.get('runner_code', manifest['code']), **(deployment or {})}
    if (path / 'deployment.json').exists():
        if read(path / 'deployment.json') != private:
            raise ValueError('same attempt cannot change its deployment')
    else:
        atomic(path / 'deployment.json', private)
    # An accepted executor owns reentry. Materialization cannot overwrite its input.
    if (path / 'execution.json').exists():
        return path, value
    try:
        if job['backend']['kind'] != 'docker':
            for name, ref in job['inputs'].items():
                artifacts.materialize(directory / 'artifacts', ref, path / 'inputs' / name,
                                      path=job.get('input_members', {}).get(name, '.'))
        _launch_gate(path, value)
        if (path / 'allocation-error.json').exists():
            (path / 'allocation-error.json').rename(path / (new_id('allocation-error') + '.json'))
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


def _explicit_inputs(directory, job, bindings):
    """Resolve only named, user-selected sources; never select a latest attempt."""
    from .core import member
    if not isinstance(bindings, dict) or set(bindings) - set(job['inputs']):
        raise ValueError('explicit input bindings must name declared job inputs')
    resolved = dict(job, inputs=dict(job['inputs']),
                    input_locations=dict(job.get('input_locations', {})),
                    input_members=dict(job.get('input_members', {})))
    relations = {}
    for name, declared in job['inputs'].items():
        if 'from_job' not in declared:
            if name in bindings:
                raise ValueError('cannot replace an already frozen input: ' + name)
            continue
        choice = bindings.get(name)
        if not isinstance(choice, dict):
            raise Blocked('input requires an explicit source attempt/output or artifact: ' + name)
        if set(choice) == {'experiment', 'attempt_id', 'output'}:
            source_directory = Path(choice['experiment']).resolve(strict=True)
            source_path = source_directory / 'attempts' / identifier(choice['attempt_id'])
            source = require(read(source_path / 'attempt.json'), 'attempt')
            if source['attempt_id'] != choice['attempt_id'] or source['job_id'] != declared['from_job'] or choice['output'] != declared['output']:
                raise ValueError('chosen producer differs from the declared input relation')
            execution = require(read(source_path / 'execution.json'), 'execution')
            reference = execution.get('artifacts', {}).get(choice['output'])
            if not reference or execution.get('outputs') != 'sealed':
                raise Blocked('chosen source has no sealed named output: ' + name)
            selected = member(execution.get('output_members', {}).get(choice['output'], '.'))
            location = execution.get('output_locations', {}).get(choice['output'])
            source_store = source['artifact_store']
            relations[name] = {'experiment': str(source_directory), 'attempt_id': source['attempt_id'],
                               'output': choice['output'], 'receipt_sha256': digest(source_path / 'execution.json'),
                               'reference': reference, 'member': selected}
        else:
            if set(choice) - {'reference', 'store', 'member', 'location'} or not {'reference', 'store'} <= set(choice):
                raise ValueError('artifact input needs reference/store and optional member/location')
            reference = choice['reference']
            selected = member(choice.get('member', '.'))
            location = choice.get('location')
            source_store = str(Path(choice['store']).resolve(strict=location is None))
            source_path = None
            relations[name] = {'reference': reference, 'member': selected, 'store': source_store}
        target = job['backend']
        same_domain = location and target['kind'] == 'docker' and location['domain_identity'].get('daemon_id') == target['endpoint']['daemon_id']
        if same_domain:
            resolved['input_locations'][name] = location
        elif location:
            if source_path is None:
                raise Blocked('cross-domain remote input needs its exact source attempt for transport')
            from .backends import export_named
            export_named(source_path, reference, location, directory / 'artifacts', selected_member=selected)
        elif Path(source_store).resolve() != (directory / 'artifacts').resolve():
            artifacts.transfer(source_store, directory / 'artifacts', reference,
                               consumer='input-' + canonical([str(directory), name, reference, selected]),
                               request_id='input-' + canonical([str(directory), name, reference, selected]), selected_member=selected)
        resolved['inputs'][name] = reference
        resolved['input_members'][name] = selected
    return resolved, relations


def _request_capacity(directory, manifest, current_attempt=None):
    attempts = list((directory / 'attempts').glob('*/attempt.json'))
    if current_attempt is None and len(attempts) >= manifest['budget']['max_attempts']:
        raise Blocked('explicit attempt budget exhausted; no request was queued')
    active = 0
    for path in attempts:
        if path.parent.name == current_attempt:
            continue
        attempt = require(read(path), 'attempt')
        if not (path.parent / 'execution.json').exists():
            continue  # Allocation itself does not create an execution resource.
        observed = _backend(attempt).observe(path.parent, live=False)
        capacity_path = path.parent / 'execution-capacity.json'
        released = False
        if capacity_path.exists() and (path.parent / 'resource.json').exists():
            capacity = require(read(capacity_path), 'execution-capacity')
            resource = read(path.parent / 'resource.json')
            released = (capacity.get('attempt_id') == attempt['attempt_id'] and
                        capacity.get('resource') == resource and
                        capacity.get('capacity_released') is True and capacity.get('status') == 'released')
        if not released and observed.get('phase', observed.get('execution')) not in FINISHED:
            active += 1
    if active >= manifest['max_parallel']:
        raise Blocked('execution capacity unavailable; no request was queued')
    if shutil.disk_usage(directory).free <= manifest['storage']['host_reserve_bytes']:
        raise Blocked('experiment storage reserve unavailable; no request was queued')


def _control_source(directory, manifest):
    return Path(directory) / ('controller-source' if manifest.get('schema_version') == 3 else 'source')


def _retry_terminal(path, attempt, observed):
    if observed.get('pending') or observed.get('observation_error'):
        return False
    terminal = observed.get('phase', observed.get('execution')) in FINISHED
    docker = attempt['job']['backend']['kind'] == 'docker'
    if not docker and not terminal:
        return False
    resource_path, capacity_path = path / 'resource.json', path / 'execution-capacity.json'
    if docker:
        if not resource_path.exists() or not capacity_path.exists():
            return False
        resource = read(resource_path)
        capacity = require(read(capacity_path), 'execution-capacity')
        if (capacity.get('attempt_id') != attempt['attempt_id'] or capacity.get('resource') != resource or
                capacity.get('capacity_released') is not True or capacity.get('status') != 'released'):
            return False
    elif observed.get('entry_identity_state') == 'alive':
        return False
    def stopped(physical):
        state = physical.get('state', {})
        return (state.get('Status') in ('exited', 'dead') and state.get('Pid') == 0 and
                all(state.get(key) is False for key in ('Running', 'Paused', 'Restarting')))
    if docker and not stopped(observed.get('physical') or {}):
        return False
    # Outcome gaps do not make a closed executor active. Pending controls still own effects.
    for effect_path in (path / 'requests').glob('*.effect.json'):
        effect = read(effect_path)
        if effect.get('action') in ('dispatch', 'stop', 'pause', 'resume', 'repair-ready'):
            unresolved = ('pending', 'queued') if effect['action'] == 'dispatch' else ('pending', 'queued', 'unknown', 'accepted')
            if effect.get('status') in unresolved:
                return False
    external_path = path / 'external-resources.json'
    if external_path.exists():
        from .backends import exact_resource
        external = require(read(external_path), 'external_resources')
        for child in external['resources']:
            if child.get('role') == 'execution' and not stopped(exact_resource(child['backend'], child)):
                return False
    return True


def start(directory, *, job_id, request_id, deployment=None, input_bindings=None, retry_of=None):
    """Accept one explicitly selected job; a request ID binds at most one attempt."""
    directory = Path(directory).resolve(strict=True)
    job_id, request_id = identifier(job_id), identifier(request_id)
    if input_bindings is not None:
        if not isinstance(input_bindings, dict):
            raise ValueError('input bindings must be an object')
        input_bindings = {name: {key: str(Path(item).expanduser().resolve()) if key in ('experiment', 'store') else item
                                 for key, item in choice.items()} if isinstance(choice, dict) else choice
                          for name, choice in input_bindings.items()}
    saved_manifest = read(directory / 'experiment.json')
    require(saved_manifest, 'experiment')
    source = _control_source(directory, saved_manifest)
    frozen_module = source / 'lab/exp/controller.py'
    arguments = {'job_id': job_id, 'request_id': request_id,
                 'deployment': str(Path(deployment).resolve()) if deployment is not None else None,
                 'input_bindings': input_bindings or {}, 'retry_of': retry_of}
    if Path(__file__).resolve() != frozen_module.resolve():
        manifest = _control_manifest(directory)
        outcome = subprocess.run([manifest['controller_runtime']['launcher'], '-B', '-m',
                  'lab.exp.controller', 'internal_start', str(directory), json.dumps(arguments)],
                  env=dict(os.environ, PYTHONPATH=str(source), PYTHONDONTWRITEBYTECODE='1'),
                  cwd=source, capture_output=True, text=True, check=True)
        return json.loads(outcome.stdout)
    manifest = verify(directory)
    jobs = [job for job in manifest['jobs'] if job['id'] == job_id]
    if len(jobs) != 1:
        raise ValueError('explicit start requires exactly one built job: ' + job_id)
    private = _load_deployment(deployment)
    parameters = {'job_id': job_id, 'job_sha256': canonical(jobs[0]),
                  'deployment_file': str(Path(deployment).resolve()) if deployment is not None else None,
                  'deployment': private, 'input_bindings': input_bindings or {}, 'retry_of': retry_of}
    operation_path = directory / 'execution-requests' / (request_id + '.json')
    with locked(directory / '.dispatch.lock'):
        if operation_path.exists():
            operation = require(read(operation_path), 'execution-request')
            if operation['parameters_sha256'] != canonical(parameters):
                raise ValueError('request ID already binds different execution parameters')
        else:
            operation = record('execution-request', request_id=request_id, parameters=parameters,
                parameters_sha256=canonical(parameters), effect='requested', created_at=time.time())
            atomic(operation_path, operation)
        try:
            if not operation.get('attempt_id'):
                _request_capacity(directory, manifest)
                resolved, relations = _explicit_inputs(directory, jobs[0], input_bindings or {})
                if retry_of:
                    original_path = directory / 'attempts' / identifier(retry_of)
                    original = require(read(original_path / 'attempt.json'), 'attempt')
                    if original['job_id'] != job_id:
                        raise ValueError('retry source belongs to another job')
                    owner = _backend(original)
                    terminal = (owner.observe_identity if hasattr(owner, 'observe_identity') else owner.observe)(original_path, live=True)
                    if not _retry_terminal(original_path, original, terminal):
                        raise Blocked('retry source execution is not confirmed terminal')
                operation.update(attempt_id='attempt-' + canonical([manifest['experiment_id'], job_id, request_id])[:24],
                                 job=resolved, input_bindings=relations)
                atomic(operation_path, operation)
            current_path = directory / 'attempts' / operation['attempt_id']
            if not (current_path / 'execution.json').exists():
                _request_capacity(directory, manifest, current_attempt=operation['attempt_id'])
            path, attempt = _allocate(directory, manifest, operation['job'],
                attempt_id=operation['attempt_id'], request_id=request_id, retry_of=retry_of,
                deployment=private, input_bindings=operation['input_bindings'])
            observation = _backend(attempt).dispatch(path)
            atomic(path / 'dispatch-observation.json', observation)
            operation.update(effect='accepted', accepted_at=operation.get('accepted_at', time.time()),
                             execution=observation)
            operation.pop('error', None)
        except Exception as exc:
            attempt_path = directory / 'attempts' / operation['attempt_id'] if operation.get('attempt_id') else None
            execution_path = attempt_path / 'execution.json' if attempt_path else None
            # A failed caller cannot negate an executor's accepted or pending effect.
            execution = read(execution_path) if execution_path and execution_path.exists() else None
            operation.update(effect='unknown' if execution is not None else
                             ('blocked' if isinstance(exc, Blocked) else 'failed'), error=error(exc))
            if execution is not None:
                operation['execution'] = execution
            atomic(operation_path, operation)
            raise
        atomic(operation_path, operation)
        return public(record('acceptance', request_id=request_id, job_id=job_id,
            attempt_id=attempt['attempt_id'], effect=operation['effect'], execution=observation,
            receipt=str(operation_path)))


def status(directory):
    if isinstance(directory, (list, tuple)):
        if len(directory) == 1:
            return status(directory[0])
        rows = []
        for location in directory:
            try:
                rows.append(status(location))
            except (OSError, ValueError) as exc:
                rows.append({'source': str(location), 'error': error(exc)})
        return record('status-index', experiments=rows, read_at=time.time())
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
    """Suggest explicit operations over saved facts; execution rechecks its gates."""
    prefix = ['python3', '-m', 'lab']
    directory = value['directory']
    def action(name, label, argv=None, requires=()):
        return {'operation': name, 'label': label, 'argv': argv,
                'requires': list(requires), 'basis': 'saved facts; operation revalidates its own gates'}
    if not attempt:
        if value.get('execution_contract') != 'explicit-request-v1':
            return [action('inspect', '旧冻结定义仅查询或控制已有attempt；新执行需重新compile/build')]
        unbound = stage['blockers'] and all(issue.get('operation') == 'start' for issue in stage['blockers'])
        if stage['blockers'] and not unbound:
            return [action('inspect', '先满足选定job的输入；没有后台排队或派发')]
        argv = prefix + ['start', directory, '--job', job['id'], '--request-id', 'REQUEST']
        if unbound:
            argv += ['--inputs', 'INPUT_BINDINGS.json']
        return [action('start', '显式选择输入并运行此job；同请求ID只绑定一个attempt', argv,
            ('指定本次deployment及确切输入；不足容量直接返回，不留待启动队列',))]
    observed = attempt['execution']
    phase = observed.get('phase', observed.get('execution', 'unknown'))
    if any(issue.get('component') == 'identity' for issue in attempt['errors']):
        return [action('inspect', '核对身份原件；不据错误新增执行')]
    actions = []
    if phase == 'readiness_failed' and observed.get('entry_status') == 'not_requested':
        for name, service in observed.get('services', {}).items():
            if name in ('collector', 'resource_evidence') and service.get('status') == 'failed':
                actions.append(action('repair-ready', '修复本attempt的失败服务 ' + name,
                    prefix + ['control', directory, attempt['attempt_id'], 'repair-ready',
                              '--service', name, '--request-id', 'REQUEST'],
                    ('同一live supervisor、入口未请求及原剩余预算',)))
    if phase not in FINISHED and attempt.get('capacity', {}).get('status') == 'released':
        return [action('inspect', '执行容量已确认释放；入口结果仍未知，核对原件'),
                action('retry', '明确请求新attempt；重新核对原执行物理终态',
                    prefix + ['retry', directory, attempt['attempt_id'], '--request-id', 'REQUEST'],
                    ('准确出生身份的实时终态、无pending、已释放容量、预算与明确输入',))]
    if phase not in FINISHED:
        actions.append(action('wait', '等待选定attempt的终态；不创建执行',
            prefix + ['wait', directory, attempt['attempt_id'], '--timeout', '60']))
        if observed.get('incarnation_id'):
            actions.append(action('stop', '停止明确的原执行；不等待完整诊断采集',
                prefix + ['control', directory, attempt['attempt_id'], 'stop', '--request-id', 'REQUEST']))
        if observed.get('pending') or phase == 'unknown':
            actions.insert(0, action('inspect', '核对原请求的未知效果；不能换ID重开入口'))
        return actions
    published = [name for name, output in stage['outputs'].items() if output.get('status') == 'published']
    if published:
        actions.append(action('consume', '按明确产物及成员消费：' + ', '.join(published),
            requires=('消费端核对引用、所需成员、实际位置与保留；不自动发起评测',)))
    if observed.get('outputs') == 'failed' or observed.get('archive') == 'failed':
        operation = 'seal' if value.get('execution_contract') == 'explicit-request-v1' else 'export'
        actions.append(action(operation, '接续同attempt的封口或证据保全；不重跑入口',
            prefix + ['control', directory, attempt['attempt_id'], operation, '--request-id', 'REQUEST']))
    if value.get('execution_contract') == 'explicit-request-v1':
        actions.append(action('retry', '明确请求一次新attempt，保留原attempt关系',
            prefix + ['retry', directory, attempt['attempt_id'], '--request-id', 'REQUEST'],
            ('原执行确认终态、预算及容量足够；不等待完整归档，不排队',)))
    if not actions:
        actions.append(action('inspect', '查看原执行结果及各项证据覆盖'))
    return actions



def _control_manifest(directory):
    """Authenticate the code/interpreter actually used for control, not job payloads."""
    directory = Path(directory).resolve(strict=True)
    value = read(directory / 'experiment.json')
    if value.get('kind') != 'factory26.exp.experiment' or value.get('schema_version') not in (1, 2, 3):
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
    if artifacts.contents(_control_source(directory, value)) != manifest['contents']:
        raise ValueError('actual frozen controller code closure changed')
    return value


def _control_attempt(directory, manifest, attempt_id):
    path = Path(directory) / 'attempts' / identifier(attempt_id)
    attempt = require(read(path / 'attempt.json'), 'attempt')
    if attempt['attempt_id'] != attempt_id or attempt['experiment_id'] != manifest['experiment_id']:
        raise Blocked('control attempt belongs to another experiment')
    job = next((row for row in manifest['jobs'] if row['id'] == attempt['job_id']), None)
    actual_job = attempt['job']
    if manifest['schema_version'] >= 3:
        accepted = require(read(Path(directory) / 'execution-requests' / (identifier(attempt['dispatch_request_id']) + '.json')), 'execution-request')
        if (accepted.get('attempt_id') != attempt_id or accepted.get('job') != actual_job
                or accepted.get('input_bindings') != attempt.get('input_bindings')
                or accepted['parameters'].get('job_id') != attempt['job_id']
                or accepted['parameters_sha256'] != canonical(accepted['parameters'])):
            raise Blocked('control attempt differs from its exact accepted execution request')
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
        relation = attempt.get('input_bindings', {}).get(name)
        if not isinstance(relation, dict):
            raise Blocked('control input lacks its explicit accepted source relation')
        reference = actual_job['inputs'][name]
        selected = actual_job.get('input_members', {}).get(name, '.')
        if relation.get('reference') != reference or relation.get('member', '.') != selected:
            raise Blocked('control input differs from its accepted artifact/member relation')
        if 'experiment' in relation:
            source_path = Path(relation['experiment']) / 'attempts' / identifier(relation['attempt_id'])
            source = require(read(source_path / 'attempt.json'), 'attempt')
            receipt_path = source_path / 'execution.json'
            receipt = require(read(receipt_path), 'execution')
            if (source['attempt_id'] != relation['attempt_id'] or source['job_id'] != binding['from_job'] or
                    relation['output'] != binding['output'] or receipt.get('outputs') != 'sealed' or
                    receipt.get('artifacts', {}).get(relation['output']) != reference or
                    receipt.get('output_members', {}).get(relation['output'], '.') != selected):
                raise Blocked('control input source no longer matches its exact sealed producer relation')
            # Receipt additions after acceptance are allowed; the immutable output relation is not.
        elif not relation.get('store'):
            raise Blocked('control artifact relation has no explicit source store')
    return path, attempt


def control(directory, attempt_id, action, *, request_id=None, parameters=None):
    directory = Path(directory).resolve(strict=True)
    manifest = _control_manifest(directory)
    frozen_module = _control_source(directory, manifest) / 'lab/exp/controller.py'
    if Path(__file__).resolve() != frozen_module.resolve():
        env = dict(os.environ, PYTHONPATH=str(_control_source(directory, manifest)), PYTHONDONTWRITEBYTECODE='1')
        result = subprocess.run([manifest['controller_runtime']['launcher'], '-B', '-m', 'lab.exp.controller',
            'internal_control', str(directory), attempt_id, action,
            json.dumps({'request_id': request_id, 'parameters': parameters})],
            cwd=_control_source(directory, manifest), env=env, capture_output=True, text=True, check=True)
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
    frozen_module = _control_source(directory, manifest) / 'lab/exp/controller.py'
    if Path(__file__).resolve() != frozen_module.resolve():
        result = subprocess.run([manifest['controller_runtime']['launcher'], '-B', '-m', 'lab.exp.controller',
            'internal_stop_evidence', str(directory), attempt_id, str(Path(output).resolve())],
            cwd=_control_source(directory, manifest), env=dict(os.environ, PYTHONPATH=str(_control_source(directory, manifest)), PYTHONDONTWRITEBYTECODE='1'),
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
    frozen_module = _control_source(directory, manifest) / 'lab/exp/controller.py'
    request_id = identifier(request_id or new_id('checkpoint'))
    if Path(__file__).resolve() != frozen_module.resolve():
        result = subprocess.run([manifest['controller_runtime']['launcher'], '-B', '-m', 'lab.exp.controller',
            'internal_checkpoint', str(directory), identifier(attempt_id), str(Path(output).absolute()), request_id, json.dumps(source_resource)],
            cwd=_control_source(directory, manifest), env=dict(os.environ, PYTHONPATH=str(_control_source(directory, manifest)), PYTHONDONTWRITEBYTECODE='1'),
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
        elif action in ('start', 'attach'):
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
    if action == 'attach':
        return {**saved, 'state_access': 'live', 'snapshot': None, 'managed_state': bool(state_binding)}
    if action == 'query':
        if state_binding and access_resource_id not in state.query(state_binding).get('consumers', {}):
            raise Blocked('Console consumer has not explicitly attached to this holder')
        if access_resource_id not in (saved.get('workspace') or {}).get('writers', []):
            raise Blocked('running accessor has no domain workspace writer coverage')
        return {**saved, 'state_access': 'live', 'snapshot': None, 'managed_state': bool(state_binding)}
    raise ValueError('unsupported accessor action')


def retry(directory, attempt_id, authorization=None, *, request_id, deployment=None):
    """Request a new attempt directly; this never writes a future dispatch queue."""
    directory = Path(directory).resolve(strict=True)
    manifest = require(read(directory / 'experiment.json'), 'experiment')
    attempt_id = identifier(attempt_id)
    attempt = require(read(directory / 'attempts' / attempt_id / 'attempt.json'), 'attempt')
    if attempt['experiment_id'] != manifest['experiment_id']:
        raise ValueError('retry source belongs to another experiment')
    original = require(read(directory / 'execution-requests' / (attempt['dispatch_request_id'] + '.json')),
                       'execution-request')
    if original.get('attempt_id') != attempt_id:
        raise ValueError('original execution request does not bind the retry source')
    return start(directory, job_id=attempt['job_id'], request_id=request_id,
                 deployment=deployment or original['parameters'].get('deployment_file'),
                 input_bindings=original['parameters']['input_bindings'], retry_of=attempt_id)


def render(value, *, details=False):
    return projection.render(value, details=details)


if __name__ == '__main__':
    if sys.argv[1:2] == ['internal_start'] and len(sys.argv) == 4:
        print(json.dumps(public(start(sys.argv[2], **json.loads(sys.argv[3])))))
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
        backend = _backend(attempt)
        print(json.dumps(public((backend.observe_identity if hasattr(backend, 'observe_identity') else backend.observe)(attempt_path, live=True))))
    elif sys.argv[1:2] == ['internal_access'] and len(sys.argv) == 6:
        print(json.dumps(public(access_control(sys.argv[2], sys.argv[3], sys.argv[4], **json.loads(sys.argv[5])))))
    else:
        raise SystemExit('internal controller invocation required')
