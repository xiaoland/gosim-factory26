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
from .core import atomic, read, record, error, identifier, Blocked, canonical, digest, process_identity, process_state, require, member
from lab.docker_endpoint import confirm, execute


def _legacy_birth(value):
    fields = ('id', 'submission_id', 'competition_id', 'requirement_id', 'created_at', 'started_at')
    if not isinstance(value, dict) or any(not isinstance(value.get(key), str) or not value[key] for key in fields):
        raise Blocked('legacy platform source requires run/submission/task/competition and actual creation/start birth')
    for key in fields[:4]:
        identifier(value[key])
    return {key: value[key] for key in fields}


def import_source_stop(birth, status, output, identity_output, authorization, cancel_evidence=None,
                       *, experiment=None, attempt_id=None):
    """Read saved ARC GET originals; cancellation intent alone grants no effect."""
    from lab.arc_bench.playground import API
    if (experiment is None) != (attempt_id is None):
        raise ValueError('hosted stop import requires experiment and attempt together')
    if not authorization.strip() or Path(output).exists() or Path(identity_output).exists() or Path(output).resolve() == Path(identity_output).resolve():
        raise ValueError('stop import needs explicit scope and two fresh output files')
    initial, terminal = read(birth), read(status)
    identity = _legacy_birth(initial)
    if _legacy_birth(terminal) != identity:
        raise Blocked('terminal observation differs from original source birth')
    if terminal.get('status') not in {'PASSED', 'FAILED', 'CANCELLED'} or not terminal.get('finished_at'):
        raise Blocked('source needs an independent terminal GET with finished_at; cancel acceptance is insufficient')
    originals = {name: {'source': str(Path(path).resolve(strict=True)), 'sha256': digest(path)}
                 for name, path in [('birth', birth), ('terminal_get', status)]}
    if experiment is None:
        source = record('legacy-source', source_id='arc-run-' + identity['id'],
                        execution_instance=canonical(identity),
                        backend_identity={'kind': 'legacy-hosted', 'platform': 'arc', 'api': API, **identity})
    else:
        from .controller import verify
        directory = Path(experiment).resolve(strict=True)
        manifest = verify(directory)
        attempt_path = directory / 'attempts' / identifier(attempt_id)
        attempt = require(read(attempt_path / 'attempt.json'), 'attempt')
        execution = require(read(attempt_path / 'execution.json'), 'execution')
        request = require(read(attempt_path / 'request.json'), 'request')
        job = next((item for item in manifest['jobs'] if item['id'] == attempt.get('job_id')), None)
        backend = attempt['job']['backend']
        if (attempt.get('attempt_id') != attempt_id or attempt.get('experiment_id') != manifest['experiment_id'] or
                job != attempt['job'] or backend.get('kind') != 'hosted' or
                execution.get('attempt_id') != attempt_id or execution.get('backend') != 'hosted' or
                not execution.get('incarnation_id') or request.get('attempt_id') != attempt_id or
                request.get('action') != 'dispatch' or request.get('parameters_sha256') != canonical(request['parameters']) or
                attempt.get('dispatch_request_id') != request.get('request_id') or
                execution.get('dispatch_request_id') != request.get('request_id')):
            raise Blocked('hosted source experiment/attempt/job/dispatch binding differs')
        identifier(execution['incarnation_id'])
        package = attempt_path / 'inputs' / 'agent'
        frozen_agent = read(directory / 'artifacts' / identifier(job['inputs']['agent']['artifact_id']) / 'manifest.json')
        package_sha256 = digest(package) if package.is_file() else None
        if (not package_sha256 or frozen_agent['contents'].get('kind') != 'file' or
                frozen_agent['contents'].get('sha256') != package_sha256 or execution.get('dispatch_sha256') !=
                canonical({'backend': backend, 'package_sha256': package_sha256, 'request': request})):
            raise Blocked('hosted source dispatch differs from its frozen package and request')
        if (_legacy_birth(execution.get('platform_result')) != identity or
                execution.get('run_id') != identity['id'] or execution.get('submission_id') != identity['submission_id'] or
                backend.get('competition_id') != identity['competition_id'] or backend.get('task') != identity['requirement_id']):
            raise Blocked('hosted source saved execution birth differs from independent GET originals')
        source = {'attempt_id': attempt_id, 'execution_instance': execution['incarnation_id'],
                  'backend_identity': {'kind': 'hosted', 'platform': 'arc', 'api': API, **identity}}
        for name, path in [('experiment', directory / 'experiment.json'), ('attempt', attempt_path / 'attempt.json'),
                           ('execution', attempt_path / 'execution.json'), ('dispatch_request', attempt_path / 'request.json')]:
            originals[name] = {'source': str(path), 'sha256': digest(path)}
    if cancel_evidence is not None:
        originals['cancel'] = {'source': str(Path(cancel_evidence).resolve(strict=True)), 'sha256': digest(cancel_evidence)}
    value = record('stop-evidence', source_identity=source, **{key: value for key, value in source.items()
                                                           if key not in {'kind', 'schema_version'}},
                   effect='stopped', observation={'status': terminal['status'], 'finished_at': terminal['finished_at'],
                                                'basis': 'saved-independent-platform-get', 'value': _legacy_birth(terminal)},
                   authorization=authorization, originals=originals, captured_at=time.time(),
                   launch_permission=False)
    atomic(identity_output, source)
    atomic(output, value)
    return value


def observe_source(source, deployment=None):
    backend = source.get('backend_identity', {})
    if backend.get('kind') == 'legacy-docker':
        require(source, 'legacy-source')
        identity = {key: backend[key] for key in ('source_run_id', 'daemon_id', 'container_id', 'created', 'started_at', 'image_id', 'labels')}
        if source.get('source_id') != identity['source_run_id'] or source.get('execution_instance') != canonical(identity):
            raise Blocked('legacy Docker source birth differs from its frozen identity')
        if backend['endpoint'].get('daemon_id') != identity['daemon_id']:
            raise Blocked('legacy Docker source endpoint differs from its daemon')
        _closed_legacy_writers(backend['writers'])
        users = execute(backend['endpoint'], ['ps', '-aq', '--no-trunc', '--filter', 'volume=' + backend['volume']],
                        check=True, capture_output=True, text=True, timeout=30).stdout.split()
        if set(users) != {item['container_id'] for item in backend['volume_users']}:
            raise Blocked('legacy Docker source volume users changed after writer closure')
        for item in backend['volume_users']:
            user = exact_resource({'kind': 'docker', 'endpoint': backend['endpoint'], 'image_id': item['image_id']}, item)
            if not _docker_stopped(user['state']):
                raise Blocked('legacy Docker source volume still has an active writer/accessor')
        physical = exact_resource({'kind': 'docker', 'endpoint': backend['endpoint'], 'image_id': identity['image_id']}, backend)
        state = physical['state']
        stopped = _docker_stopped(state)
        return record('source_observation', source_identity=source, effect='stopped' if stopped else 'unknown',
                      physical=physical, observed_at=time.time())
    hosted = backend.get('kind') == 'hosted'
    if source.get('kind') != 'factory26.exp.legacy-source' and not hosted:
        from .runner import observe_source as observe_runner_source
        return observe_runner_source(source)
    if not hosted:
        require(source, 'legacy-source')
    else:
        if 'kind' in source or 'schema_version' in source:
            raise Blocked('hosted source must retain the actual attempt execution identity without a legacy producer kind')
        identifier(source['attempt_id'])
        identifier(source['execution_instance'])
    from lab.arc_bench.playground import API, Client, run_path
    identity = _legacy_birth(backend)
    if (backend.get('platform') != 'arc' or backend.get('api') != API or
            (not hosted and (backend.get('kind') != 'legacy-hosted' or
             source.get('source_id') != 'arc-run-' + identity['id'] or source.get('execution_instance') != canonical(identity)))):
        raise Blocked('unsupported or inconsistent platform source producer identity')
    cookie = (deployment or {}).get('cookie_file')
    if not cookie:
        raise Blocked('platform source current observation requires explicit private cookie_file; no ambient credential fallback')
    # This adapter only GETs the original run; it never cancels or resumes it.
    value = Client(cookie).request(run_path(identity['id']))
    if _legacy_birth(value) != identity:
        raise Blocked('platform source actual execution birth changed')
    status = value.get('status')
    stopped = status in {'PASSED', 'FAILED', 'CANCELLED'} and bool(value.get('finished_at'))
    return record('source_observation', source_identity=source, effect='stopped' if stopped else 'unknown',
                  status=status, finished_at=value.get('finished_at'), observed_at=time.time(),
                  platform_identity=identity)


def capabilities(target):
    kind = target['kind']
    if kind == 'local':
        return {'backend': kind, 'platform': sys.platform, 'control': ['stop', 'pause', 'resume'],
                'checkpoint': 'harness_declared_only', 'telemetry': 'otlp_http', 'independent_runner': True}
    if kind == 'docker':
        confirm(target['endpoint'])
        version = execute(target['endpoint'], ['version', '--format', '{{.Server.APIVersion}}'], check=True, capture_output=True, text=True, timeout=30).stdout.strip()
        if tuple(int(part) for part in version.split('.')) < (1, 45):
            raise Blocked('isolated Docker asset/workspace mounts require API 1.45 volume-subpath')
        return {'backend': kind, 'daemon_id': target['endpoint']['daemon_id'], 'image_id': target['image_id'],
                'control': ['stop', 'pause', 'resume'], 'checkpoint': 'harness_declared_only',
                'admission_volume': target['admission_volume'], 'telemetry': 'otlp_http', 'independent_runner': True}
    raise Blocked(f'unsupported self-owned backend: {kind}')


def inspect(target, container_id):
    confirm(target['endpoint'])
    template = '{"container_id":{{json .Id}},"image_id":{{json .Image}},"created":{{json .Created}},"state":{{json .State}},"labels":{{json .Config.Labels}},"network_mode":{{json .HostConfig.NetworkMode}},"networks":{{json .NetworkSettings.Networks}}}'
    result = execute(target['endpoint'], ['inspect', '--format', template, container_id],
                     check=True, capture_output=True, text=True, timeout=30)
    value = json.loads(result.stdout)
    if target.get('network') == 'none' and (value['network_mode'] != 'none' or set(value['networks'] or {}) - {'none'}):
        raise Blocked('Docker physical network does not match frozen network:none')
    return value


def exact_resource(target, binding):
    current = inspect(target, binding['container_id'])
    if target.get('image_id') and current['image_id'] != target['image_id']:
        raise Blocked('Docker actual image differs from the frozen execution image')
    if binding.get('started_at') and current['state'].get('StartedAt') != binding['started_at']:
        raise Blocked('Docker resource restarted after the bound execution instance')
    if current['created'] != binding['created'] or any(current['labels'].get(k) != v for k, v in binding['labels'].items()):
        raise Blocked('Docker execution resource birth or ownership changed')
    return current


def control_resource(target, binding, action, grace=10, request_id=None):
    request_id = request_id or binding['authority_resource_id'] + '--' + action
    return managed(target, binding, action, request_id, {'grace': grace} if action == 'stop' else {})


def external(directory, action=None, grace=10, *, include_helpers=True, request_id=None):
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
        observation = control_resource(target, resource, action, grace, request_id=(request_id + '--' + resource['attempt_id']) if request_id else None) if action else exact_resource(target, resource)
        facts.append({'resource': resource, 'observation': observation})
    return facts


def launcher(deployment):
    runtime = deployment.get('runtime', {})
    if runtime.get('launcher'):
        return list(runtime['launcher'])
    return [runtime.get('python', deployment.get('python', sys.executable)), '-B', '-m', 'lab.exp.runner']


def preflight(attempt, deployment):
    """Read-only requirements; failure precedes any runner or workload acceptance."""
    from lab.assets import asset_inventory
    runtime = deployment['runtime']['asset']
    if asset_inventory(Path(runtime['root'])) != runtime['identity'] or digest(Path(runtime['launcher']).resolve(strict=True)) != runtime['interpreter_sha256']:
        raise Blocked('runner runtime does not match the explicit frozen host asset')
    capability = capabilities(attempt['job']['backend'])
    if attempt['job']['backend']['kind'] == 'docker':
        capability['domain'] = admission.query(attempt['job']['backend'])['domain']
    return capability


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


def managed(target, binding, action, request_id, parameters=None):
    """Perform one fixed Docker action after authority acceptance; reentry only observes."""
    parameters = dict(parameters or {})
    resource_id = binding['authority_resource_id']
    value = admission.action(target, resource_id, request_id, action, parameters)
    effect = value['effect']
    if effect['status'] == 'applied':
        return {**effect['physical'], 'authority_resource_id': resource_id} if effect.get('physical') else effect.get('result')
    if action == 'reserve':
        return admission.complete(target, resource_id, request_id, action, parameters, result={'reserved': True})['effect']
    if not value.get('accepted_now'):
        if action in ('writer-open', 'writer-close', 'capture-begin', 'capture-end'):
            return admission.complete(target, resource_id, request_id, action, parameters, result={'effect': action})['effect']
        # Read back the precise promised effect, never reissue its physical call.
        if action == 'create':
            argv = parameters['argv']
            if '--name' not in argv:
                raise Blocked('pending create lacks a stable physical query name')
            observed = inspect(target, argv[argv.index('--name') + 1])
            required_labels = dict(item.split('=', 1) for index, item in enumerate(argv) if index and argv[index - 1] == '--label')
            if observed['image_id'] != target['image_id'] or any(observed['labels'].get(k) != v for k, v in required_labels.items()):
                raise Blocked('pending create name belongs to another physical owner')
        elif action == 'volume-create':
            observed = json.loads(execute(target['endpoint'], ['volume', 'inspect', parameters['argv'][-1]], check=True, capture_output=True, text=True, timeout=30).stdout)[0]
            required_labels = dict(item.split('=', 1) for index, item in enumerate(parameters['argv']) if index and parameters['argv'][index - 1] == '--label')
            if any((observed.get('Labels') or {}).get(k) != v for k, v in required_labels.items()):
                raise Blocked('pending volume belongs to another asset owner')
        else:
            observed = exact_resource(target, binding)
        completed = admission.complete(target, resource_id, request_id, action, parameters, physical=observed)
        return {**completed['effect']['physical'], 'authority_resource_id': resource_id}

    endpoint = target['endpoint']
    if action in ('writer-open', 'writer-close', 'capture-begin', 'capture-end'):
        return admission.complete(target, resource_id, request_id, action, parameters, result={'effect': action})['effect']
    if action in ('create', 'volume-create'):
        argv = parameters['argv']
        if not argv or (argv[0] != 'create' if action == 'create' else argv[:2] != ['volume', 'create']):
            raise ValueError('managed create accepts only a frozen Docker create argv')
        result = execute(endpoint, argv, check=True, capture_output=True, text=True, timeout=parameters.get('timeout', 60))
        physical = inspect(target, result.stdout.strip()) if action == 'create' else json.loads(execute(endpoint, ['volume', 'inspect', result.stdout.strip()], check=True, capture_output=True, text=True, timeout=30).stdout)[0]
    else:
        physical = exact_resource(target, binding)
        if action == 'start':
            execute(endpoint, ['start', binding['container_id']], check=True, capture_output=True, text=True, timeout=60)
        elif action == 'stop':
            if physical['state'].get('Paused'):
                execute(endpoint, ['unpause', binding['container_id']], check=True, capture_output=True, text=True, timeout=30)
            if physical['state'].get('Running') or physical['state'].get('Restarting'):
                execute(endpoint, ['stop', '--time', str(parameters.get('grace', 10)), binding['container_id']],
                        check=True, capture_output=True, text=True, timeout=parameters.get('grace', 10) + 30)
        elif action == 'pause':
            execute(endpoint, ['pause', binding['container_id']], check=True, capture_output=True, text=True, timeout=30)
        elif action == 'resume':
            execute(endpoint, ['unpause', binding['container_id']], check=True, capture_output=True, text=True, timeout=30)
        elif action not in ('writer-open', 'writer-close', 'capture-begin', 'capture-end'):
            raise ValueError('unsupported managed physical action')
        physical = exact_resource(target, binding)
    completed = admission.complete(target, resource_id, request_id, action, parameters, physical=physical)
    return {**completed['effect']['physical'], 'authority_resource_id': resource_id}


def domain_observation(target, binding):
    value = admission.query(target, binding['authority_resource_id'])
    value['physical'] = exact_resource(target, binding)
    return value


def _owner_exec(target, helper, argv, *, timeout=1800):
    exact_resource(target, helper)
    return execute(target['endpoint'], ['exec', helper['container_id'], *argv],
                   check=True, capture_output=True, text=True, timeout=timeout)


def store_action(directory, action, request):
    """Only the separately supervised storage owner has the published volume writable."""
    directory = Path(directory)
    target = read(directory / 'attempt.json')['job']['backend']
    helper = read(directory / 'store-helper.json')
    path = directory / ('store-request-' + canonical(request) + '.json')
    atomic(path, record('artifact-store-action', **request))
    remote = '/execution/' + path.name
    execute(target['endpoint'], ['cp', str(path), helper['container_id'] + ':' + remote],
            check=True, capture_output=True, text=True, timeout=60)
    output = _owner_exec(target, helper, [target.get('python', 'python3'), '-B', '-m', 'lab.exp.artifacts', action,
                                        '--store', '/assets', '--request', remote])
    return json.loads(output.stdout)


def prepare_docker(directory, attempt, request, deployment, incarnation):
    """Create a writable execution volume and separately owned published-asset view."""
    directory = Path(directory)
    target, endpoint = attempt['job']['backend'], attempt['job']['backend']['endpoint']
    prefix = 'exp-' + canonical([attempt['experiment_id'], attempt['attempt_id']])[:24]
    volume = prefix + '-execution'
    asset_volume = target.get('artifact_volume', 'exp-assets-' + canonical(endpoint['daemon_id'])[:24])
    rid = attempt['attempt_id']
    labels = {'io.factory26.exp.attempt': rid, 'io.factory26.exp.incarnation': incarnation,
              'io.factory26.exp.experiment': attempt['experiment_id']}
    owner = {'authority_resource_id': rid}
    managed(target, owner, 'reserve', request['request_id'] + '--reserve', {'role': 'execution', 'workspace': rid})
    managed(target, owner, 'volume-create', request['request_id'] + '--workspace-volume',
            {'argv': ['volume', 'create', *[item for k, v in labels.items() for item in ('--label', k + '=' + v)], volume]})
    helper_rid = rid + '--store-owner'
    helper_binding = {'authority_resource_id': helper_rid}
    managed(target, helper_binding, 'reserve', request['request_id'] + '--owner-reserve', {'role': 'copy', 'workspace': rid})
    managed(target, helper_binding, 'volume-create', request['request_id'] + '--assets-volume',
            {'argv': ['volume', 'create', '--label', 'io.factory26.exp.asset-daemon=' + endpoint['daemon_id'], asset_volume]})
    asset = json.loads(execute(endpoint, ['volume', 'inspect', asset_volume], check=True, capture_output=True, text=True, timeout=30).stdout)[0]
    if (asset.get('Labels') or {}).get('io.factory26.exp.asset-daemon') != endpoint['daemon_id']:
        raise Blocked('published asset volume identity differs from selected daemon')
    helper_args = ['create', '--user', '0', '--name', prefix + '-store-owner', '--restart', 'no', '--network', 'none',
                   '--memory', '256m', '--pids-limit', '64', '--label', 'io.factory26.exp.attempt=' + helper_rid,
                   '--label', 'io.factory26.exp.role=copy', '--mount', f'type=volume,src={asset_volume},dst=/assets',
                   '--mount', f'type=volume,src={volume},dst=/execution', '--env', 'PYTHONPATH=/execution/owner-runtime',
                   '--entrypoint', target.get('python', 'python3'), target['image_id'], '-B', '-c', 'import time;time.sleep(2147483647)']
    helper = managed(target, helper_binding, 'create', request['request_id'] + '--owner-create', {'argv': helper_args})
    helper = managed(target, helper, 'start', request['request_id'] + '--owner-start')
    helper['started_at'] = helper['state']['StartedAt']
    atomic(directory / 'store-helper.json', helper)
    managed(target, helper, 'writer-open', request['request_id'] + '--owner-writer-open')
    execute(endpoint, ['cp', deployment['runtime']['source'], helper['container_id'] + ':/execution/owner-runtime'],
            check=True, capture_output=True, text=True, timeout=1800)
    _owner_exec(target, helper, [target.get('python', 'python3'), '-c',
                               "from pathlib import Path;[Path('/execution/'+p).mkdir(exist_ok=True) for p in ('payload','staging')]"])
    store_action(directory, 'initialize', {'domain_identity': {'kind': 'docker', 'daemon_id': endpoint['daemon_id'], 'volume_id': asset_volume}})
    from .artifacts import publish, contents
    code = deployment.get('executor_code') or publish(attempt['artifact_store'], deployment['runtime']['source'], 'executor-code',
                   request_id='executor-' + canonical(contents(Path(deployment['runtime']['source']))),
                   consumer=rid, purpose='runner-code')
    _owner_exec(target, helper, [target.get('python', 'python3'), '-c', "from pathlib import Path;[Path('/execution/payload/'+p).mkdir(parents=True,exist_ok=True) for p in ('workspace','requests','inputs')]"])
    input_refs = {'executor': code, **attempt['job']['inputs']}
    prepared_descriptor = attempt['job'].get('prepared_descriptor')
    if prepared_descriptor:
        if prepared_descriptor.get('schema_version') != 3:
            raise Blocked('Docker prepared execution requires separated v3 state and definition relations')
        for definition in prepared_descriptor['definition_assets']:
            input_refs['definition--' + definition['name']] = definition['artifact']
    for name, ref in input_refs.items():
        expected_location = attempt['job'].get('input_locations', {}).get(name)
        if expected_location and (expected_location.get('reference') != ref or expected_location.get('domain_identity', {}).get('daemon_id') != endpoint['daemon_id'] or expected_location.get('volume_id') != asset_volume or expected_location.get('store_root') != '/assets'):
            raise Blocked('input location differs from the exact target daemon/store binding; explicit cross-domain transfer required')
        # Query existing managed position first; only missing assets cross the control-host boundary.
        try:
            locations = store_action(directory, 'query', {})['locations']
            present = any(row['reference'] == ref and row['state'] == 'available' for row in locations)
        except Exception:
            # A failed query is not an absent asset and must not trigger another transport.
            raise
        if not present:
            source = Path(attempt['artifact_store']) / ref['artifact_id']
            execute(endpoint, ['cp', str(source), helper['container_id'] + ':/execution/staging/' + ref['artifact_id']],
                    check=True, capture_output=True, text=True, timeout=1800)
            _owner_exec(target, helper, [target.get('python', 'python3'), '-c', 'from pathlib import Path;Path(' + repr('/execution/staging/' + ref['artifact_id'] + '/location.json') + ').unlink(missing_ok=True)'])
            store_action(directory, 'transfer', {'source_store': '/execution/staging', 'reference': ref,
                         'request_id': rid + '--input--' + name, 'consumer': rid})
        hold = store_action(directory, 'retain', {'reference': ref, 'consumer': rid, 'purpose': 'execution-input', 'request_id': rid + '--retain--' + name})
        _owner_exec(target, helper, [target.get('python', 'python3'), '-c', 'from pathlib import Path; p=Path(' + repr('/execution/payload/inputs/' + name) + '); p.symlink_to(' + repr('/assets/' + ref['artifact_id'] + '/payload') + ') if not p.exists() else None'])
    _owner_exec(target, helper, [target.get('python', 'python3'), '-c', "from pathlib import Path;[Path('/execution/payload/'+p).mkdir(exist_ok=True) for p in ('workspace','requests','inputs')]"])
    payload = dict(attempt)
    payload['artifact_store'] = '/assets'
    payload['job'] = dict(attempt['job'], inputs=attempt['job']['inputs'])
    atomic(directory / 'payload-attempt.json', payload)
    private = dict(deployment, runtime={'python': target.get('python', 'python3'), 'source': '/assets/' + code['artifact_id'] + '/payload',
                                       'identity': target.get('runtime_identity')})
    if deployment.get('credential_file'):
        execute(endpoint, ['cp', deployment['credential_file'], helper['container_id'] + ':/execution/payload/credentials.json'],
                check=True, capture_output=True, text=True, timeout=60)
        private['credential_file'] = '/execution/credentials.json'
    atomic(directory / 'payload-deployment.json', private)
    placements, definition_placements = [], []
    if attempt['job'].get('prepared'):
        manifest = prepared_descriptor
        if manifest is None:
            raise Blocked('prepared execution requires the controller resolved definition descriptor')
        from submission.exp_checkpoint import definition_mount_roots
        content_root = '/assets/' + attempt['job']['inputs']['prepared']['artifact_id'] + '/payload/content'
        run_root = Path(manifest['target_layout']['run_root'])
        if (not run_root.is_absolute() or run_root == Path('/') or run_root.is_relative_to('/assets')
                or run_root.is_relative_to('/execution') and not run_root.is_relative_to('/execution/workspace')):
            raise Blocked('prepared state root conflicts with isolated executor inputs or evidence namespace')
        mapping = {'logical_root': str(run_root), 'member': 'run', 'subpath': 'state/run', 'access': 'read-write'}
        source, destination = content_root + '/run', '/execution/' + mapping['subpath']
        script = 'import shutil;from pathlib import Path;src=Path(' + repr(source) + ');dst=Path(' + repr(destination) + ');' + 'dst.parent.mkdir(parents=True,exist_ok=True);shutil.copytree(src,dst,symlinks=True)'
        _owner_exec(target, helper, [target.get('python', 'python3'), '-c', script])
        placements.append(mapping)
        if not asset.get('Mountpoint') or not Path(asset['Mountpoint']).is_absolute():
            raise Blocked('definition read-only bindings require the selected daemon volume mountpoint')
        for definition in definition_mount_roots(manifest['definition_assets'], str(run_root)):
            root = Path(definition['logical_root'])
            if root == Path('/') or root.is_relative_to('/execution'):
                raise Blocked('definition root conflicts with writable executor namespace')
            remote = '/assets/' + definition['artifact']['artifact_id'] + '/payload'
            if definition['member'] != '.':
                remote += '/' + member(definition['member'])
            # Check the daemon namespace through its owner, never with a control-host Path.exists().
            if root.is_relative_to('/assets'):
                script = 'from pathlib import Path;print("true" if Path(' + repr(str(root)) + ').exists() else "false")'
                present = json.loads(_owner_exec(target, helper, [target.get('python', 'python3'), '-c', script]).stdout)
                if not present:
                    raise Blocked('definition logical mount target absent from retained daemon namespace: ' + str(root))
            daemon_source = str(Path(asset['Mountpoint']) / remote.removeprefix('/assets/'))
            definition_placements.append({**definition, 'access': 'read-only', 'daemon_source': daemon_source})
        private['layout_bindings'] = placements
        private['definition_bindings'] = definition_placements
        atomic(directory / 'payload-deployment.json', private)
    for source_name, target_name in (('payload-attempt.json', 'attempt.json'), ('payload-deployment.json', 'deployment.json'), ('binding.json', 'binding.json')):
        execute(endpoint, ['cp', str(directory / source_name), helper['container_id'] + ':/execution/payload/' + target_name],
                check=True, capture_output=True, text=True, timeout=60)
    args = ['create', '--name', prefix + '-entry', '--restart', 'no', '--init',
            '--mount', f'type=volume,src={asset_volume},dst=/assets,readonly', '--mount', f'type=volume,src={volume},dst=/execution,volume-subpath=payload',
            '--env', 'PYTHONPATH=' + private['runtime']['source'], '--workdir', '/execution/workspace']
    if target.get('network') == 'none':
        args += ['--network', 'none']
    for placement in placements:
        args += ['--mount', f"type=volume,src={volume},dst={placement['logical_root']},volume-subpath={placement['subpath']}"]
    for definition in definition_placements:
        args += ['--mount', f"type=bind,src={definition['daemon_source']},dst={definition['logical_root']},readonly"]
    for key, value in labels.items():
        args += ['--label', key + '=' + value]
    for field, flag in (('memory_bytes', '--memory'), ('cpus', '--cpus'), ('pids', '--pids-limit')):
        if attempt['job']['limits'].get(field):
            args += [flag, str(attempt['job']['limits'][field])]
    args += ['--entrypoint', target.get('python', 'python3'), target['image_id'], '-B', '-m', 'lab.exp.runner', 'internal_payload', '/execution']
    managed(target, helper, 'writer-close', request['request_id'] + '--owner-writer-close')
    resource = managed(target, owner, 'create', request['request_id'] + '--create', {'argv': args})
    resource.update(volume=volume, artifact_volume=asset_volume, daemon_id=endpoint['daemon_id'])
    atomic(directory / 'resource.json', record('resource', **resource))
    return resource


def _payload_workspace(directory):
    """Use the same physical run-state mapping for execution, outputs and export."""
    deployment = read(Path(directory) / 'payload-deployment.json')
    mapping = next((row for row in deployment.get('layout_bindings', []) if row['member'] == 'run'), None)
    return '/execution/' + member(mapping['subpath']) if mapping else '/execution/payload/workspace'


def collect_named_outputs(directory):
    """Publish named content in the daemon store, without exporting the entire execution domain."""
    directory = Path(directory)
    attempt, resource = read(directory / 'attempt.json'), read(directory / 'resource.json')
    target = attempt['job']['backend']
    physical = exact_resource(target, resource)
    if physical['state'].get('Status') not in ('exited', 'dead'):
        raise Blocked('output publication requires exact physical terminality')
    workspace = _payload_workspace(directory)
    refs, missing = {}, []
    for output in attempt['job'].get('outputs', []):
        output_path = workspace + '/' + member(output['path'])
        script = 'from pathlib import Path;root=Path(' + repr(workspace) + ');p=Path(' + repr(output_path) + ');\nif p.is_symlink() or not p.resolve().is_relative_to(root.resolve()):\n raise ValueError("output escapes workload workspace")\nprint("true" if p.exists() else "false")'
        exists = json.loads(_owner_exec(target, read(directory / 'store-helper.json'), [target.get('python', 'python3'), '-B', '-c', script]).stdout)
        if not exists:
            missing.append(output['name'])
            continue
        ref = store_action(directory, 'publish', {'source': workspace + '/' + member(output['path']),
                           'type': output['type'], 'provenance': {'attempt_id': attempt['attempt_id'], 'output': output['name']},
                           'request_id': attempt['attempt_id'] + '--output--' + canonical(output['name'])[:24], 'consumer': attempt['attempt_id'], 'purpose': 'producer-output'})
        refs[output['name']] = ref
    result = None
    if attempt['job'].get('result_path'):
        result_path = workspace + '/' + member(attempt['job']['result_path'])
        script = 'from pathlib import Path;root=Path(' + repr(workspace) + ');p=Path(' + repr(result_path) + ');\nif p.is_symlink() or not p.resolve().is_relative_to(root.resolve()):\n raise ValueError("result escapes workload workspace")\nprint(p.read_text() if p.is_file() else "null")'
        result = json.loads(_owner_exec(target, read(directory / 'store-helper.json'), [target.get('python', 'python3'), '-B', '-c', script]).stdout)
    atomic(directory / 'outputs.json', record('named-outputs', attempt_id=attempt['attempt_id'], artifacts=refs, result=result, missing_outputs=missing,
          locations={name: {'reference': ref, 'domain_identity': {'kind': 'docker', 'daemon_id': target['endpoint']['daemon_id']},
                     'volume_id': resource['artifact_volume'], 'store_root': '/assets'} for name, ref in refs.items()}, sealed_at=time.time()))
    return refs


def payload_record(directory, filename, optional=False):
    directory = Path(directory)
    target = read(directory / 'attempt.json')['job']['backend']
    helper = read(directory / 'store-helper.json')
    remote = '/execution/payload/' + member(filename)
    output = _owner_exec(target, helper, [target.get('python', 'python3'), '-c',
                         'from pathlib import Path; p=Path(' + repr(remote) + ');print(p.read_text() if p.is_file() else "null")'])
    value = json.loads(output.stdout)
    if value is None and not optional:
        raise Blocked('required payload fact is absent: ' + filename)
    return value


def payload_send(directory, filename, value):
    directory = Path(directory)
    target = read(directory / 'attempt.json')['job']['backend']
    helper = read(directory / 'store-helper.json')
    transport_id = read(directory / 'attempt.json')['attempt_id'] + '--payload-' + canonical([filename, value])[:24]
    managed(target, helper, 'writer-open', transport_id + '--writer-open')
    path = directory / ('payload-send-' + member(filename))
    atomic(path, value)
    filename = member(filename)
    remote = '/execution/payload/' + str(Path(filename).parent / ('.' + Path(filename).name))
    execute(target['endpoint'], ['cp', str(path), helper['container_id'] + ':' + remote], check=True, capture_output=True, text=True, timeout=60)
    _owner_exec(target, helper, [target.get('python', 'python3'), '-c',
                              'import os;os.replace(' + repr(remote) + ',' + repr('/execution/payload/' + filename) + ')'])

    managed(target, helper, 'writer-close', transport_id + '--writer-close')


def docker_export_preflight(directory, attempt, resource):
    """Account for terminal reception and host evidence assembly before copying."""
    target = attempt['job']['backend']
    helper = read(Path(directory) / 'store-helper.json')
    script = '''import json,os,stat,sys
from pathlib import Path
root=Path('/execution/payload')
def failure(exc):raise exc
def size(path):
 if not path.is_dir() or path.is_symlink():raise ValueError('missing or redirected export source: '+str(path))
 total=4096
 for current,dirs,files in os.walk(path,followlinks=False,onerror=failure):
  for name in dirs+files:
   value=(Path(current)/name).lstat()
   # Include archive headers and extraction allocation, including empty directories.
   total+=((value.st_size+4095)//4096)*4096+512 if stat.S_ISREG(value.st_mode) else 4096
 return total
extra=Path(sys.argv[1])
print(json.dumps({'T_bytes':size(root)+(size(extra) if extra != root/'workspace' else 0)}))
'''
    measured = json.loads(_owner_exec(target, helper, [target.get('python', 'python3'), '-B', '-c', script, _payload_workspace(directory)], timeout=180).stdout)
    margin = attempt['job']['limits'].get('storage_reserve_bytes', attempt['job']['limits']['storage_bytes'])
    free = shutil.disk_usage(directory).free
    required = 2 * measured['T_bytes'] + margin
    value = record('export-preflight', source=resource, **measured,
                   margin_bytes=margin, required_bytes=required, host_free_bytes=free,
                   missing_bytes=max(0, required-free), observed_at=time.time())
    atomic(Path(directory) / 'export-preflight.json', value)
    if free < required:
        raise Blocked('terminal export storage unavailable: required=' + str(required) + ', free=' + str(free) + ', missing=' + str(required-free))
    return value



def _release_export_scratch(directory, receipt):
    """Release matching downloaded duplicates only after final paths have durable receipts."""
    from .artifacts import contents, _sync
    stage = Path(receipt['stage'])
    if stage.parent.resolve() != directory.resolve() or not stage.name.startswith('payload-export-'):
        raise Blocked('export scratch path is outside the owning attempt')
    released = set(receipt.get('scratch_released_members', []))
    errors = {}
    for name, expected in receipt['installed'].items():
        source = stage / name
        if source.is_dir() and not source.is_symlink():
            try:
                if contents(source) != expected:
                    errors[name] = {'message': 'downloaded scratch changed; retained'}
                    continue
                shutil.rmtree(source)
                _sync(stage)
            except OSError as exc:
                errors[name] = error(exc)
                continue
        elif source.exists() or source.is_symlink():
            errors[name] = {'message': 'downloaded scratch object changed type; retained'}
            continue
        released.add(name)
    receipt.update(scratch_released_members=sorted(released), scratch_release_errors=errors)
    atomic(directory / 'export.json', receipt)
    return receipt


def export_payload(directory):
    directory = Path(directory)
    attempt, resource = read(directory / 'attempt.json'), read(directory / 'resource.json')
    target = attempt['job']['backend']
    from .artifacts import contents, _sync, _durable_tree
    progress_path = directory / 'payload-export-intent.json'
    saved = read(directory / 'export.json') if (directory / 'export.json').exists() else None
    if saved and saved.get('installed'):
        if saved['source'] != resource:
            raise Blocked('saved export belongs to another execution resource')
        for name, expected in saved['installed'].items():
            if contents(directory / name) != expected:
                raise Blocked('preserved terminal payload changed: ' + name)
        return _release_export_scratch(directory, saved)
    physical = exact_resource(target, resource)
    if physical['state'].get('Status') not in ('exited', 'dead'):
        raise Blocked('execution evidence export requires physical terminality')
    progress = read(progress_path) if progress_path.exists() else None
    if progress and progress['source'] != resource:
        raise Blocked('pending export belongs to another execution resource')
    stage = Path(progress['stage']) if progress else directory / ('payload-export-' + str(time.time_ns()))
    if not progress:
        stage.mkdir()
        progress = record('export', status='downloading', source=resource, stage=str(stage))
        atomic(progress_path, progress)
    try:
        if progress['status'] == 'downloading':
            if any(stage.iterdir()):
                previous = str(stage)
                stage = directory / ('payload-export-' + str(time.time_ns()))
                stage.mkdir()
                progress.update(stage=str(stage), retained_partials=[*progress.get('retained_partials', []), previous])
                atomic(progress_path, progress)
            docker_export_preflight(directory, attempt, resource)
            helper = read(directory / 'store-helper.json')
            execute(target['endpoint'], ['cp', helper['container_id'] + ':/execution/payload/.', str(stage)],
                    check=True, capture_output=True, text=True, timeout=1800)
            workspace_source = _payload_workspace(directory)
            if workspace_source != '/execution/payload/workspace':
                if (stage / 'workspace').exists():
                    (stage / 'workspace').rename(stage / 'entry-workspace-parent')
                (stage / 'workspace').mkdir()
                execute(target['endpoint'], ['cp', helper['container_id'] + ':' + workspace_source + '/.', str(stage / 'workspace')],
                        check=True, capture_output=True, text=True, timeout=1800)
            progress['workspace_source'] = workspace_source
            names = ('workspace', 'telemetry', 'telemetry-transports', 'process-evidence', 'service-errors')
            progress.update(status='downloaded', contents={name: contents(stage / name)
                            for name in names if (stage / name).is_dir() and not (stage / name).is_symlink()})
            atomic(progress_path, progress)
        for name, expected in progress['contents'].items():
            source, destination = stage / name, directory / name
            if source.exists():
                if destination.exists() and any(destination.iterdir()):
                    if contents(destination) != expected:
                        raise Blocked('existing export differs from terminal payload: ' + name)
                    # Matching download scratch is released only after the final preservation receipt.
                else:
                    if destination.exists():
                        destination.rmdir()
                    source.rename(destination)
                    _sync(directory)
                    _sync(stage)
            if contents(destination) != expected:
                raise Blocked('installed terminal payload differs from completed download: ' + name)
            _durable_tree(destination)
        for name in ('stdout.log', 'stderr.log', 'payload-terminal.json', 'services.json', 'ready.json'):
            if (stage / name).exists():
                shutil.copy2(stage / name, directory / name)
                _sync(directory / name)
        if (stage / 'assembly.json').exists():
            shutil.copy2(stage / 'assembly.json', directory / 'payload-assembly.json')
            _sync(directory / 'payload-assembly.json')
        # Unclaimed metadata and any conflicting original remain at stage; live input links are not followed.
        _durable_tree(stage)
        ready = read(directory / 'ready.json')
        execution = read(directory / 'execution.json')
        deployment = read(directory / 'payload-deployment.json')
        assembly_path = directory / 'payload-assembly.json'
        assembly = read(assembly_path) if assembly_path.is_file() else None
        mapping = next((row for row in deployment.get('layout_bindings', []) if row['member'] == 'run'), None)
        if mapping and (not assembly or assembly.get('status') != 'assembled'
                        or assembly['workspace'] != mapping['logical_root'] or mapping.get('access') != 'read-write'):
            raise Blocked('exported state lacks its exact completed assembly mapping')
        state_binding = {'logical_root': mapping['logical_root'] if mapping else '/execution/workspace',
                         'installed_root': str((directory / 'workspace').resolve()), 'installed_member': 'workspace',
                         'contents': progress['contents']['workspace'], 'platform': ready['execution_platform'],
                         'runtime_identity': ready['runtime'], 'mapping': mapping,
                         'definitions': assembly['definitions'] if assembly else [],
                         'readonly_inputs': [{'root': '/assets/' + ref['artifact_id'] + '/payload', 'artifact': ref}
                                             for ref in attempt['job']['inputs'].values()],
                         'source_identity': {'attempt_id': attempt['attempt_id'], 'execution_instance': execution['incarnation_id'],
                                             'backend_identity': execution['backend_identity']}}
        atomic(directory / 'export.json', record('export', status='preserved', source=resource,
               stage=str(stage), installed=progress['contents'], state_binding=state_binding, exported_at=time.time()))
        return _release_export_scratch(directory, read(directory / 'export.json'))
    except Exception as exc:
        atomic(stage / 'transport-error.json', error(exc))
        raise


def finish_docker(directory):
    directory = Path(directory)
    attempt, resource = read(directory / 'attempt.json'), read(directory / 'resource.json')
    target = attempt['job']['backend']
    admission.reconcile(target, resource['authority_resource_id'], attempt['attempt_id'] + '--release', domain_observation(target, resource))
    helper = read(directory / 'store-helper.json')
    control_resource(target, helper, 'stop', request_id=attempt['attempt_id'] + '--owner-stop')
    admission.reconcile(target, helper['authority_resource_id'], attempt['attempt_id'] + '--owner-release', domain_observation(target, helper))


def export_named(source_attempt_dir, reference, location, target_store):
    """Explicit cross-domain receive of one retained named artifact, independent of archive."""
    directory, target_store = Path(source_attempt_dir), Path(target_store).resolve()
    attempt = read(directory / 'attempt.json')
    target = attempt['job']['backend']
    if location['domain_identity']['kind'] != 'docker' or location['domain_identity']['daemon_id'] != target['endpoint']['daemon_id']:
        raise Blocked('named artifact location is not bound to its producer daemon')
    identifier(reference['artifact_id'])
    request_id = 'named-transfer-' + canonical([reference, location, str(target_store)])[:32]
    transport = directory / 'named-transfers' / request_id
    transport.mkdir(parents=True, exist_ok=True)
    receipt_path = transport / 'effect.json'
    from .artifacts import transfer, verify
    if receipt_path.exists() and read(receipt_path)['status'] == 'preserved':
        verify(target_store, reference)
        return reference
    helper_path = transport / 'helper.json'
    if helper_path.exists():
        helper = read(helper_path)
        current = exact_resource(target, helper)
        # A retained terminal helper can still expose its mounted files through Docker cp.
        if current['state'].get('Status') not in ('running', 'exited', 'created'):
            raise Blocked('named transport helper physical status unavailable')
    else:
        owner = {'authority_resource_id': request_id}
        managed(target, owner, 'reserve', request_id + '--reserve', {'role': 'copy'})
        argv = ['create', '--name', request_id, '--restart', 'no', '--network', 'none', '--memory', '128m', '--pids-limit', '32',
                '--label', 'io.factory26.exp.attempt=' + request_id, '--label', 'io.factory26.exp.role=copy',
                '--mount', 'type=volume,src=' + location['volume_id'] + ',dst=/assets,readonly',
                '--entrypoint', target.get('python', 'python3'), target['image_id'], '-B', '-c', 'import time;time.sleep(2147483647)']
        helper = managed(target, owner, 'create', request_id + '--create', {'argv': argv})
        atomic(helper_path, helper)
        started = managed(target, helper, 'start', request_id + '--start')
        helper.update(started_at=started['state']['StartedAt'], state=started['state'])
        atomic(helper_path, helper)
    if not helper.get('started_at') or helper['started_at'].startswith('0001-'):
        started = managed(target, helper, 'start', request_id + '--start')
        helper.update(started_at=started['state']['StartedAt'], state=started['state'])
        atomic(helper_path, helper)
    stage = transport / ('receive-' + str(time.time_ns()))
    stage.mkdir()
    atomic(receipt_path, record('named-transfer', request_id=request_id, reference=reference, source=location, status='receiving', stage=str(stage)))
    try:
        execute(target['endpoint'], ['cp', helper['container_id'] + ':/assets/' + reference['artifact_id'], str(stage)],
                check=True, capture_output=True, text=True, timeout=1800)
        # The transport staging is raw reception, not a cloned managed-store authority.
        (stage / reference['artifact_id'] / 'location.json').unlink(missing_ok=True)
        verify(stage, reference)
        transfer(stage, target_store, reference, request_id=request_id, consumer='receiver:' + request_id)
        atomic(receipt_path, record('named-transfer', request_id=request_id, reference=reference, source=location,
              status='preserved', stage=str(stage), completed_at=time.time()))
        if exact_resource(target, helper)['state'].get('Running'):
            control_resource(target, helper, 'stop', request_id=request_id + '--stop')
        admission.reconcile(target, request_id, request_id + '--release', domain_observation(target, helper))
        return reference
    except Exception as exc:
        atomic(stage / 'transport-error.json', error(exc))
        atomic(receipt_path, record('named-transfer', request_id=request_id, reference=reference, source=location,
              status='unknown', stage=str(stage), error=error(exc)))
        raise


def _docker_stopped(state):
    return (state.get('Status') in {'exited', 'dead'} and state.get('Running') is False and
            state.get('Paused') is False and state.get('Restarting') is False and state.get('Pid') == 0)



def _closed_legacy_writers(writers):
    if not isinstance(writers, list) or not writers:
        raise Blocked('legacy Docker source requires its closed restart/writer identities')
    current = process_identity()
    for writer in writers:
        state = process_state(writer)
        if state == 'lost':
            continue
        # Darwin withholds proc_pidinfo birth for zombies. A current zombie cannot
        # execute; the shared dispatcher need not be resumed merely to reap it.
        if state == 'unknown' and writer.get('host') == current['host'] and writer.get('boot_id') == current['boot_id']:
            if type(writer.get('pid')) is not int or writer['pid'] <= 0:
                raise Blocked('legacy Docker writer PID is invalid')
            result = subprocess.run(['ps', '-o', 'stat=', '-p', str(writer['pid'])], capture_output=True, text=True, timeout=10)
            if result.returncode == 0 and result.stdout.strip().startswith('Z'):
                continue
        raise Blocked(f'legacy Docker source writer is not closed: pid={writer.get("pid")}, state={state}')



def import_docker_source_stop(birth, status, writers, output, identity_output, authorization):
    """Bind retained legacy Docker originals to a fresh exact physical observation."""
    if not authorization.strip() or Path(output).exists() or Path(identity_output).exists() or Path(output).resolve() == Path(identity_output).resolve():
        raise ValueError('legacy Docker import needs explicit scope and two fresh output files')
    initial, terminal, retirement = read(birth), read(status), read(writers)
    original, endpoint = initial['source_container'], initial['endpoint']
    if (initial['source_run_id'] != terminal.get('source_run_id') or initial['daemon_id'] != terminal.get('daemon_id') or
            original['id'] != terminal.get('container_id') or original['state']['StartedAt'] != terminal['after'].get('StartedAt')):
        raise Blocked('legacy Docker stop original differs from its source birth')
    identities = [row['identity'] for row in retirement['writers']]
    _closed_legacy_writers(identities)
    physical = inspect({'kind': 'docker', 'endpoint': endpoint}, original['id'])
    if (physical['image_id'] != original['image'] or physical['state']['StartedAt'] != original['state']['StartedAt'] or
            any(physical['labels'].get(k) != v for k, v in original['labels'].items())):
        raise Blocked('legacy Docker current container differs from original source execution')
    identity = dict(source_run_id=initial['source_run_id'], daemon_id=initial['daemon_id'],
                    container_id=physical['container_id'], created=physical['created'],
                    started_at=physical['state']['StartedAt'], image_id=physical['image_id'], labels=physical['labels'])
    if not identity['started_at'] or identity['started_at'].startswith('0001-'):
        raise Blocked('legacy Docker source lacks actual execution start')
    volume = initial['volume']
    users = execute(endpoint, ['ps', '-aq', '--no-trunc', '--filter', 'volume=' + volume], check=True, capture_output=True, text=True, timeout=30).stdout.split()
    volume_users = []
    for container_id in users:
        value = inspect({'kind': 'docker', 'endpoint': endpoint}, container_id)
        if not _docker_stopped(value['state']):
            raise Blocked('legacy Docker volume writer/accessor closure is incomplete')
        volume_users.append({**{key: value[key] for key in ('container_id', 'created', 'image_id', 'labels')},
                             'started_at': value['state']['StartedAt']})
    source = record('legacy-source', source_id=identifier(identity['source_run_id']), execution_instance=canonical(identity),
                    backend_identity={'kind': 'legacy-docker', 'endpoint': endpoint, **identity, 'writers': identities,
                                      'volume': volume, 'volume_users': volume_users})
    observation = observe_source(source)
    if observation['effect'] != 'stopped':
        raise Blocked('legacy Docker current source is not physically stopped')
    originals = {name: {'source': str(Path(path).resolve(strict=True)), 'sha256': digest(path)}
                 for name, path in [('birth', birth), ('stop', status), ('writer_retirement', writers)]}
    value = record('stop-evidence', source_identity=source, source_id=source['source_id'],
                   execution_instance=source['execution_instance'], backend_identity=source['backend_identity'],
                   effect='stopped', observation=observation, authorization=authorization, originals=originals,
                   captured_at=time.time(), launch_permission=False)
    atomic(identity_output, source)
    atomic(output, value)
    return value
