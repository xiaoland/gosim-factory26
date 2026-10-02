"""Physical execution adapters; neither owns an experiment controller."""
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import time

from . import admission
from .core import atomic, read, record, error, identifier, Blocked, canonical, process_identity, process_state
from lab.docker_endpoint import confirm, execute


def capabilities(target):
    kind = target['kind']
    if kind == 'local':
        return {'backend': kind, 'platform': sys.platform, 'control': ['stop', 'pause', 'resume'],
                'checkpoint': 'harness_declared_only', 'telemetry': 'otlp_http', 'independent_runner': True}
    if kind == 'docker':
        confirm(target['endpoint'])
        return {'backend': kind, 'daemon_id': target['endpoint']['daemon_id'], 'image_id': target['image_id'],
                'control': ['stop', 'pause', 'resume'], 'checkpoint': 'harness_declared_only',
                'admission_volume': target['admission_volume'], 'telemetry': 'otlp_http', 'independent_runner': True}
    raise Blocked(f'unsupported self-owned backend: {kind}')


def inspect(target, container_id):
    confirm(target['endpoint'])
    template = '{"container_id":{{json .Id}},"image_id":{{json .Image}},"created":{{json .Created}},"state":{{json .State}},"labels":{{json .Config.Labels}}}'
    result = execute(target['endpoint'], ['inspect', '--format', template, container_id],
                     check=True, capture_output=True, text=True, timeout=30)
    return json.loads(result.stdout)


def exact_resource(target, binding):
    current = inspect(target, binding['container_id'])
    if target.get('image_id') and current['image_id'] != target['image_id']:
        raise Blocked('Docker actual image differs from the frozen execution image')
    if binding.get('started_at') and current['state'].get('StartedAt') != binding['started_at']:
        raise Blocked('Docker resource restarted after the bound execution instance')
    if current['created'] != binding['created'] or any(current['labels'].get(k) != v for k, v in binding['labels'].items()):
        raise Blocked('Docker execution resource birth or ownership changed')
    return current


def control_resource(target, binding, action, grace=10):
    current = exact_resource(target, binding)
    if action == 'stop':
        if current['state'].get('Running') or current['state'].get('Paused') or current['state'].get('Restarting'):
            if current['state'].get('Paused'):
                execute(target['endpoint'], ['unpause', binding['container_id']], check=True, capture_output=True, text=True, timeout=30)
            execute(target['endpoint'], ['stop', '--time', str(int(grace)), binding['container_id']],
                    check=True, capture_output=True, text=True, timeout=grace + 30)
    elif action == 'pause':
        if not current['state'].get('Paused'):
            execute(target['endpoint'], ['pause', binding['container_id']], check=True, capture_output=True, text=True, timeout=30)
    elif action == 'resume':
        if current['state'].get('Paused'):
            execute(target['endpoint'], ['unpause', binding['container_id']], check=True, capture_output=True, text=True, timeout=30)
    else:
        raise ValueError(f'unsupported resource control: {action}')
    observed = exact_resource(target, binding)
    if action == 'stop' and observed['state'].get('Status') not in ('exited', 'dead'):
        raise Blocked('Docker stop returned without terminal physical observation')
    return observed


def external(directory, action=None, grace=10, *, include_helpers=True):
    path = Path(directory) / 'external-resources.json'
    if not path.exists():
        return []
    from .core import require
    manifest = require(read(path), 'external_resources')
    facts = []
    for resource in manifest['resources']:
        if action and not include_helpers and resource.get('role') == 'transport-helper':
            continue
        target = resource['backend']
        if target['kind'] != 'docker':
            raise Blocked('external resource has no physical control capability')
        observation = control_resource(target, resource, action, grace) if action else exact_resource(target, resource)
        facts.append({'resource': resource, 'observation': observation})
    return facts


def launcher(deployment):
    runtime = deployment.get('runtime', {})
    if runtime.get('launcher'):
        return list(runtime['launcher'])
    return [runtime.get('python', deployment.get('python', sys.executable)), '-B', '-m', 'lab.exp.runner']


def local_launch(directory, deployment):
    from lab.assets import asset_inventory
    from .core import digest
    runtime = deployment['runtime']['asset']
    if (asset_inventory(Path(runtime['root'])) != runtime['identity'] or
            digest(Path(runtime['launcher']).resolve(strict=True)) != runtime['interpreter_sha256']):
        raise Blocked('local runner runtime no longer matches its frozen asset')
    environment = dict(os.environ)
    environment['PYTHONDONTWRITEBYTECODE'] = '1'
    source = deployment.get('runtime', {}).get('source')
    if source:
        environment['PYTHONPATH'] = str(source)
    with (Path(directory) / 'runner.log').open('ab', buffering=0) as log:
        process = subprocess.Popen(launcher(deployment) + ['internal_worker', str(directory)],
                                   stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                                   start_new_session=True, close_fds=True, env=environment)
    return {'runner_process': process_identity(process.pid), 'runner_pid': process.pid}


def docker_launch(directory, attempt, request, deployment, incarnation):
    target = attempt['job']['backend']
    endpoint = target['endpoint']
    identifier(attempt['attempt_id'])
    name = 'exp-' + canonical([attempt['experiment_id'], attempt['attempt_id']])[:32]
    volume = name + '-data'
    labels = {'io.factory26.exp.attempt': attempt['attempt_id'], 'io.factory26.exp.incarnation': incarnation,
              'io.factory26.exp.experiment': attempt['experiment_id']}
    reservation = admission.authority(target, 'reserve', attempt_id=attempt['attempt_id'], request_id=request['request_id'],
                                     parameters_sha256=request['parameters_sha256'], incarnation=incarnation,
                                     launch_name=name, owner=process_identity())['reservation']
    if reservation['incarnation'] != incarnation or reservation['phase'] != 'accepted':
        raise Blocked('dispatch already accepted in daemon authority; reconcile saved launch binding')
    admission.authority(target, 'launch', attempt_id=attempt['attempt_id'], incarnation=incarnation)
    # A crash from this point cannot be retried as another create/start.
    args = ['volume', 'create']
    for key, value in labels.items():
        args += ['--label', key + '=' + value]
    execute(endpoint, args + [volume], check=True, capture_output=True, text=True, timeout=30)
    existing = json.loads(execute(endpoint, ['volume', 'inspect', volume], check=True, capture_output=True, text=True, timeout=30).stdout)[0]
    if any((existing.get('Labels') or {}).get(k) != v for k, v in labels.items()):
        raise Blocked('attempt volume identity already exists with another incarnation')
    args = ['create', '--name', name, '--restart', 'no', '--mount', f'type=volume,src={volume},dst=/attempt',
            '--workdir', '/attempt', '--env', 'PYTHONPATH=/attempt/runtime']
    for key, value in labels.items():
        args += ['--label', key + '=' + value]
    args += ['--init']
    limits = attempt['job']['limits']
    for key, flag in (('memory_bytes', '--memory'), ('cpus', '--cpus'), ('pids', '--pids-limit')):
        if limits.get(key):
            args += [flag, str(limits[key])]
    args += ['--entrypoint', target.get('python', 'python3'), target['image_id'], '-m', 'lab.exp.runner', 'internal_worker', '/attempt']
    result = execute(endpoint, args, check=True, capture_output=True, text=True, timeout=60)
    container_id = result.stdout.strip()
    resource = inspect(target, container_id)
    binding = {**resource, 'volume': volume, 'daemon_id': endpoint['daemon_id']}
    atomic(Path(directory) / 'resource.json', record('resource', **binding))
    admission.authority(target, 'bind', attempt_id=attempt['attempt_id'], incarnation=incarnation, resource=resource)
    with tempfile.TemporaryDirectory(prefix='exp-upload-') as temporary:
        staged = Path(temporary)
        for filename in ('attempt.json', 'request.json', 'execution.json', 'binding.json', 'resource.json'):
            value = read(Path(directory) / filename)
            if filename == 'attempt.json':
                value['artifact_store'] = '/attempt/artifact-store'
            atomic(staged / filename, value)
        private = dict(deployment)
        private['runtime'] = {'python': target.get('python', 'python3'), 'source': '/attempt/runtime'}
        if deployment.get('credential_file'):
            shutil.copy2(deployment['credential_file'], staged / 'credentials.json')
            private['credential_file'] = '/attempt/credentials.json'
        atomic(staged / 'deployment.json', private)
        if (Path(directory) / 'inputs').exists():
            shutil.copytree(Path(directory) / 'inputs', staged / 'inputs', symlinks=True)
        else:
            (staged / 'inputs').mkdir()
        (staged / 'workspace').mkdir()
        (staged / 'artifact-store').mkdir()
        source = Path(deployment['runtime']['source']).resolve(strict=True)
        shutil.copytree(source, staged / 'runtime', symlinks=True)
        execute(endpoint, ['cp', str(staged) + '/.', container_id + ':/attempt'],
                check=True, capture_output=True, text=True, timeout=300)
    execute(endpoint, ['start', container_id], check=True, capture_output=True, text=True, timeout=60)
    started = inspect(target, container_id)
    binding = {**binding, 'started_at': started['state']['StartedAt'], 'state': started['state']}
    atomic(Path(directory) / 'resource.json', record('resource', **binding))
    admission.authority(target, 'bind', attempt_id=attempt['attempt_id'], incarnation=incarnation, resource=binding)
    marker = Path(directory) / 'resource-start.json'
    atomic(marker, record('resource', **binding))
    execute(endpoint, ['cp', str(marker), container_id + ':/attempt/.resource-start.json'],
            check=True, capture_output=True, text=True, timeout=60)
    execute(endpoint, ['exec', container_id, target.get('python', 'python3'), '-c',
                       "import os;os.replace('/attempt/.resource-start.json','/attempt/resource-start.json')"],
            check=True, capture_output=True, text=True, timeout=30)
    return binding


def docker_read(directory, filename='execution.json'):
    attempt = read(Path(directory) / 'attempt.json')
    target = attempt['job']['backend']
    resource = read(Path(directory) / 'resource.json')
    exact_resource(target, resource)
    with tempfile.TemporaryDirectory(prefix='exp-read-') as temporary:
        path = Path(temporary) / filename
        execute(target['endpoint'], ['cp', resource['container_id'] + ':/attempt/' + filename, str(path)],
                check=True, capture_output=True, text=True, timeout=60)
        return read(path)


def docker_request(directory, request):
    target = read(Path(directory) / 'attempt.json')['job']['backend']
    resource = read(Path(directory) / 'resource.json')
    exact_resource(target, resource)
    path = Path(directory) / 'requests' / (request['request_id'] + '.json')
    atomic(path, request)
    # Complete private temp -> rename in target, avoiding partially observed control JSON.
    remote = '/attempt/requests/.' + request['request_id'] + '.json'
    execute(target['endpoint'], ['exec', resource['container_id'], target.get('python', 'python3'), '-c',
                                 "from pathlib import Path;Path('/attempt/requests').mkdir(exist_ok=True)"],
            check=True, capture_output=True, text=True, timeout=30)
    execute(target['endpoint'], ['cp', str(path), resource['container_id'] + ':' + remote],
            check=True, capture_output=True, text=True, timeout=60)
    execute(target['endpoint'], ['exec', resource['container_id'], target.get('python', 'python3'), '-c',
                                 'import os;os.replace(' + repr(remote) + ',' + repr(remote.replace('/.', '/')) + ')'],
            check=True, capture_output=True, text=True, timeout=30)


def docker_export(directory):
    directory = Path(directory)
    attempt = read(directory / 'attempt.json')
    target = attempt['job']['backend']
    resource = read(directory / 'resource.json')
    physical = exact_resource(target, resource)
    if any(physical['state'].get(k) for k in ('Running', 'Paused', 'Restarting')) or physical['state'].get('Status') not in ('exited', 'dead'):
        raise Blocked('consistent Docker terminal export requires physical terminal observation')
    stage = directory / ('export-' + str(time.time_ns()))
    stage.mkdir()
    try:
        execute(target['endpoint'], ['cp', resource['container_id'] + ':/attempt/.', str(stage)],
                check=True, capture_output=True, text=True, timeout=300)
        from .artifacts import verify
        receipt = read(stage / 'execution.json')
        refs = list(receipt.get('artifacts', {}).values())
        store = Path(attempt['artifact_store'])
        store.mkdir(parents=True, exist_ok=True)
        for ref in refs:
            verify(stage / 'artifact-store', ref)
            destination = store / ref['artifact_id']
            if not destination.exists():
                staging = store / ('.transport-' + ref['artifact_id'])
                shutil.copytree(stage / 'artifact-store' / ref['artifact_id'], staging, symlinks=True)
                staging.rename(destination)
            verify(store, ref)
        for name in ('telemetry', 'telemetry-transports'):
            if (stage / name).is_dir():
                destination = directory / name
                if destination.exists():
                    from .artifacts import contents
                    if contents(destination) != contents(stage / name):
                        raise Blocked('existing telemetry export differs from terminal source: ' + name)
                else:
                    shutil.copytree(stage / name, destination, symlinks=True)
        atomic(directory / 'remote-execution.json', receipt)
        atomic(directory / 'export.json', record('export', status='preserved', source=resource,
                                               stage=str(stage), artifacts=receipt.get('artifacts', {}), exported_at=time.time()))
        admission.authority(target, 'snapshot')
        return read(directory / 'export.json')
    except Exception as exc:
        atomic(stage / 'transport-error.json', error(exc))
        raise
