"""One experiment owner; execution effects belong to independent executors."""
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


def _source(destination):
    """Freeze explicit modules, not a mutable directory-wide controller snapshot."""
    destination.mkdir(parents=True)
    files = [ROOT / 'exp' / '__init__.py', ROOT / '__init__.py', ROOT / '__main__.py', ROOT / 'control.py',
             ROOT / 'records.py', ROOT / 'assets.py', ROOT / 'otlp.py', ROOT / 'docker_endpoint.py']
    files += list((ROOT / 'exp').glob('*.py'))
    # ARC SDK child resources use the same execution identity and daemon authority.
    files += [ROOT / 'arc_bench' / name for name in (
        '__init__.py', 'playground.py', 'arc_bench_adapter.py', 'arc_bench_noop.py',
        'workspace_archive.py', 'docker_workspace.py', 'docker_admission.py', 'arc_artifacts.py', 'traceability.py')]
    for source in dict.fromkeys(files):
        target = destination / 'lab' / source.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    submission = destination / 'submission'
    submission.mkdir()
    (submission / '__init__.py').write_text('')
    shutil.copy2(ROOT.parent / 'submission/exp_checkpoint.py', submission / 'exp_checkpoint.py')
    return files


def _runtime(path, purpose='controller'):
    value = require(read(path), 'runtime')
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


def build(spec_path, directory):
    spec_path, directory = Path(spec_path).resolve(strict=True), Path(directory).resolve()
    spec = require(read(spec_path), 'experiment')
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
    if (directory / 'experiment.json').exists():
        manifest = require(read(directory / 'experiment.json'), 'experiment')
        if manifest['recipe_sha256'] != digest(spec_path):
            raise ValueError('experiment specification changed; build a new experiment')
        verify(directory)
        return manifest
    directory.mkdir(parents=True, mode=0o700, exist_ok=True)
    os.chmod(directory, 0o700)
    if (directory / 'build-intent.json').exists() and read(directory / 'build-intent.json')['recipe_sha256'] != digest(spec_path):
        raise ValueError('incomplete build belongs to a different recipe')
    if (directory / 'build-error.json').exists():
        (directory / 'build-error.json').rename(directory / ('build-error-' + new_id('receipt') + '.json'))
    atomic(directory / 'build-intent.json', record('build', recipe_sha256=digest(spec_path),
                                                  started_at=time.time(), phase='building'))
    store = directory / 'artifacts'
    bindings_path = directory / 'build-bindings.json'
    bindings = read(bindings_path) if bindings_path.exists() else {}
    def publish_input(key, origin, kind, provenance):
        if key in bindings:
            ref = bindings[key]
            if artifacts.contents(origin) != artifacts.verify(store, ref)['contents']:
                raise ValueError('build source changed after publication: ' + key)
            return ref
        ref = artifacts.publish(store, origin, kind, provenance=provenance)
        bindings[key] = ref
        atomic(bindings_path, bindings)
        return ref
    try:
        runtime_path = (spec_path.parent / spec['controller_runtime']).resolve(strict=True)
        runtime = _runtime(runtime_path)
        runner_runtime = None
        if any(job.get('backend', {}).get('kind') == 'local' for job in spec['jobs']):
            runner_runtime = _runtime((spec_path.parent / spec['runner_runtime']).resolve(strict=True), 'runner')
        jobs, ids = [], set()
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
            inputs = {}
            for name, value in job.get('inputs', {}).items():
                identifier(name)
                if isinstance(value, str) or isinstance(value, dict) and 'source' in value:
                    origin = value if isinstance(value, str) else value['source']
                    origin = (spec_path.parent / origin).resolve(strict=True)
                    inputs[name] = publish_input(job_id + '/input/' + name, origin, 'input',
                        {'recipe_sha256': digest(spec_path), 'job_id': job_id, 'name': name})
                elif isinstance(value, dict) and 'artifact_id' in value:
                    ref = {key: value[key] for key in ('artifact_id', 'manifest_sha256')}
                    if value.get('store'):
                        artifacts.transfer((spec_path.parent / value['store']).resolve(strict=True), store, ref)
                    else:
                        artifacts.verify(store, ref)
                    inputs[name] = ref
                elif isinstance(value, dict) and set(value) == {'from_job', 'output'}:
                    identifier(value['from_job']); identifier(value['output'])
                    if job['purpose'] != 'evaluate':
                        raise ValueError('published job outputs are only consumed by independent evaluation')
                    inputs[name] = value
                else:
                    raise ValueError('input must explicitly reference a source or artifact')
            for output in job.get('outputs', []):
                from .core import member
                identifier(output['name']); identifier(output['type']); member(output['path'])
            for field in ('checkpoint', 'prepared', 'stop_evidence'):
                if field in job:
                    binding = job[field]
                    if not isinstance(binding, dict) or 'source' not in binding:
                        raise ValueError(f'{field} must reference explicit producer evidence source')
                    inputs[field] = publish_input(job_id + '/' + field, (spec_path.parent / binding['source']).resolve(strict=True),
                                                     field.replace('_', '-'), binding.get('provenance', {}))
                    job[field] = inputs[field]
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
        if 'executor-code' in bindings:
            artifacts.materialize(store, bindings['executor-code'], source)
            code = bindings['executor-code']
        else:
            if source.exists():
                source.rename(directory / new_id('incomplete-source'))
            _source(source)
            _dependency_tree(source, runtime)
            code = publish_input('executor-code', source, 'executor-code', {'source': 'explicit exp module set'})
        zipapp.create_archive(source, directory / 'runner.pyz', main='lab.exp.runner:main',
                              interpreter='/usr/bin/env python3', compressed=True)
        experiment_id = identifier(spec.get('experiment_id') or new_id('experiment'))
        value = record('experiment', experiment_id=experiment_id, authorization=spec['authorization'],
                       jobs=jobs, budget=budget, storage=storage, max_parallel=spec['max_parallel'],
                       recipe_sha256=digest(spec_path), controller_runtime=runtime,
                       runner_runtime=runner_runtime,
                       code=code, runner_sha256=digest(directory / 'runner.pyz'), created_at=time.time(),
                       labels=spec.get('labels', {}))
        atomic(directory / 'experiment.json', value)
        atomic(directory / 'build-intent.json', record('build', phase='published',
              experiment_id=experiment_id, recipe_sha256=digest(spec_path), finished_at=time.time()))
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
    artifacts.verify(store, value['code'])
    if artifacts.contents(directory / 'source') != artifacts.verify(store, value['code'])['contents']:
        raise ValueError('installed executor code differs from frozen artifact')
    if digest(directory / 'runner.pyz') != value['runner_sha256']:
        raise ValueError('frozen runner code changed')
    for job in value['jobs']:
        for ref in job.get('inputs', {}).values():
            if 'from_job' not in ref:
                artifacts.verify(store, ref)
    return value


def _backend(attempt):
    if attempt['job']['backend']['kind'] == 'hosted':
        from . import hosted
        return hosted
    from . import runner
    return runner


def source_stop_binding(prepared, stop):
    """Check the saved binding; a matching record is not a current stop proof."""
    if prepared.get('kind') != 'factory26.harness.prepared' or prepared.get('schema_version') != 1:
        raise Blocked('prepared artifact needs the public Harness prepared contract')
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
    if 'prepared' not in job:
        return
    prepared_path = artifacts.resolve(store, job['prepared'])
    manifest_path = prepared_path / 'harness-manifest.json' if prepared_path.is_dir() else prepared_path
    prepared = read(manifest_path)
    if prepared.get('kind') != 'factory26.harness.prepared' or prepared.get('schema_version') != 1:
        raise Blocked('prepared artifact needs the public Harness prepared contract')
    from submission.exp_checkpoint import validate
    validate(prepared_path)
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
           **(deployment or {})})
    try:
        for name, ref in job['inputs'].items():
            artifacts.materialize(directory / 'artifacts', ref, path / 'inputs' / name)
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
                        if attempt['job']['backend']['kind'] == 'docker' and observation.get('phase') in FINISHED and observation.get('archive') == 'preserved':
                            if not (path / 'export.json').exists():
                                export_request = request(attempt['attempt_id'], 'export', {},
                                    request_id='terminal-export-' + attempt['attempt_id'], incarnation=observation['incarnation_id'])
                                exported = executor.control(path, export_request)
                                if exported.get('status') != 'applied':
                                    raise Blocked('terminal artifact transport unconfirmed: ' + json.dumps(exported))
                            observation = executor.observe(path, live=True)
                        if observation.get('phase') in FINISHED:
                            if attempt['job']['backend']['kind'] == 'hosted' and observation.get('archive', {}).get('status') == 'not-exported':
                                observation = executor.export(path)
                            elif attempt['job']['backend']['kind'] != 'hosted' and observation.get('archive') == 'preserved':
                                _ingest_telemetry(path)
                        if observation.get('phase') in {'unaccepted', 'not-dispatched', 'accepted', 'snapshot-saved', 'run-created'} or observation.get('execution') == 'unaccepted':
                            if (path / 'allocation-error.json').exists():
                                for name, ref in attempt['job']['inputs'].items():
                                    artifacts.materialize(directory / 'artifacts', ref, path / 'inputs' / name)
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
                active = [row for row in attempts if row[2].get('phase') not in FINISHED or
                          (row[1]['job']['backend']['kind'] != 'hosted' and row[2].get('archive') == 'pending')]
                if any(row[2].get('phase') == 'unknown' or row[2].get('pending') or
                       row[2].get('archive') == 'failed' or (row[0] / 'allocation-error.json').exists() for row in attempts):
                    raise Blocked('an attempt has unknown effects or preparation failure; retain its identity and inspect')
                for job in manifest['jobs']:
                    if job['id'] in assigned or len(active) >= manifest['max_parallel']:
                        continue
                    resolved = dict(job, inputs=dict(job['inputs']))
                    unavailable = False
                    for name, binding in job['inputs'].items():
                        if 'from_job' not in binding:
                            continue
                        producers = [row for row in attempts if row[1]['job_id'] == binding['from_job']]
                        if not producers or producers[-1][2].get('phase') not in FINISHED or producers[-1][2].get('archive') == 'pending':
                            unavailable = True
                            break
                        production = producers[-1][2]
                        ref = production.get('artifacts', {}).get(binding['output'])
                        if production.get('exit_code') != 0 or not ref:
                            raise Blocked('generation has no successful frozen output for evaluation: ' + binding['from_job'])
                        artifacts.verify(directory / 'artifacts', ref)
                        resolved['inputs'][name] = ref
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
        active = [row for row in value['attempts'] if row['execution'].get('phase', row['execution'].get('execution')) not in FINISHED or
                  row['backend'] != 'hosted' and row['execution'].get('archive') == 'pending']
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
    if phase not in FINISHED:
        if alive:
            return [action('wait', '等待当前 attempt；不新增入口', prefix + ['wait', directory, '--timeout', '60'])]
        if stage['blockers']:
            return [action('inspect', '先核对观察故障及当前资源身份')]
        return [action('start', '重连接续原 attempt 的 controller', prefix + ['start', directory],
                       ('原 runner/平台身份保持；启动操作重新核对并按原请求接续',))]
    archive = observed.get('archive')
    needs_export = (archive == 'failed' or attempt['backend'] == 'docker' and
                    attempt.get('export.json', {}).get('status') != 'preserved' or
                    isinstance(archive, dict) and archive.get('status') == 'not-exported')
    if needs_export:
        if alive:
            return [action('wait', '等待当前 controller 收尾；不重跑入口', prefix + ['wait', directory, '--timeout', '60'])]
        if not observed.get('incarnation_id'):
            return [action('inspect', '执行 incarnation 缺失，不能发出 export 控制')]
        return [action('export', '接续保全或输运同一 attempt，保留原入口结果',
                       prefix + ['control', directory, attempt['attempt_id'], 'export'],
                       ('执行时核对同一 incarnation 和物理终态；不会重新运行 main',
                        '修复已报告的存储/输运条件；导出成功不代表 Harness prepared 完整'))]
    if archive == 'pending':
        return [action('wait' if alive else 'inspect', '等待或核对 runner 收尾；不能按入口退出推断保全完成')]
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


def control(directory, attempt_id, action, *, request_id=None, parameters=None):
    directory = Path(directory).resolve(strict=True)
    manifest = verify(directory)
    frozen_module = directory / 'source/lab/exp/controller.py'
    if Path(__file__).resolve() != frozen_module.resolve():
        env = dict(os.environ, PYTHONPATH=str(directory / 'source'), PYTHONDONTWRITEBYTECODE='1')
        result = subprocess.run([manifest['controller_runtime']['launcher'], '-B', '-m', 'lab.exp.controller',
            'internal_control', str(directory), attempt_id, action,
            json.dumps({'request_id': request_id, 'parameters': parameters})],
            cwd=directory / 'source', env=env, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    path = directory / 'attempts' / identifier(attempt_id)
    attempt = require(read(path / 'attempt.json'), 'attempt')
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
    manifest = verify(directory)
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
    elif sys.argv[1:2] == ['internal_observe'] and len(sys.argv) == 4:
        directory = Path(sys.argv[2]).resolve(strict=True)
        verify(directory)
        attempt_path = directory / 'attempts' / identifier(sys.argv[3])
        attempt = require(read(attempt_path / 'attempt.json'), 'attempt')
        print(json.dumps(public(_backend(attempt).observe(attempt_path, live=True))))
    else:
        raise SystemExit('internal controller invocation required')
