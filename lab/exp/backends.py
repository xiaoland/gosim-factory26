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
    if action == 'cancel-reservation':
        return admission.complete(target, resource_id, request_id, action, parameters, result={'no_execution_accepted': True})['effect']
    if action == 'reserve':
        return admission.complete(target, resource_id, request_id, action, parameters, result={'reserved': True})['effect']
    if not value.get('accepted_now'):
        if action in ('writer-open', 'writer-close', 'capture-begin', 'capture-end'):
            return admission.complete(target, resource_id, request_id, action, parameters, result={'effect': action})['effect']
        # Read back the precise promised effect, never reissue its physical call.
        if action == 'discard':
            absence = execute(target['endpoint'], ['inspect', binding['container_id']], check=False, capture_output=True, text=True, timeout=30)
            if absence.returncode != 1 or 'No such object: ' + binding['container_id'] not in absence.stderr:
                raise Blocked('pending discard is not proven removed; do not repeat removal')
            observed = {'removed': True, 'birth': value['resource']['identity'], 'absence': {
                'returncode': absence.returncode, 'stdout': absence.stdout, 'stderr': absence.stderr}}
        elif action == 'create':
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
    if action == 'discard':
        birth = exact_resource(target, binding)
        started = birth['state'].get('StartedAt')
        if birth['state'].get('Status') != 'created' or birth['state'].get('Running') or (started and not started.startswith('0001-')):
            raise Blocked('pre-entry discard source is not an exact never-started object')
        saved_birth = value['resource']['identity']
        execute(endpoint, ['rm', binding['container_id']], check=True, capture_output=True, text=True, timeout=60)
        absence = execute(endpoint, ['inspect', binding['container_id']], check=False, capture_output=True, text=True, timeout=30)
        if absence.returncode != 1 or 'No such object: ' + binding['container_id'] not in absence.stderr:
            raise Blocked('discard response has no exact independent object-absence evidence')
        physical = {'removed': True, 'birth': saved_birth, 'absence': {'returncode': absence.returncode, 'stdout': absence.stdout, 'stderr': absence.stderr}}
        return admission.complete(target, resource_id, request_id, action, parameters, physical=physical)['effect']['physical']
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


def _domain_member_root(target, helper, reference, selected_member, *, missing_ok=False):
    """Resolve a declared immutable member in the actual owner namespace."""
    selected_member = member(selected_member)
    script = ('from lab.exp.artifacts import _manifest,plain_member_contents,member_payload; import json; '
              'ref=json.loads(' + repr(json.dumps(reference)) + '); '
              'plain_member_contents(_manifest("/assets",ref),' + repr(selected_member) + '); '
              'root=member_payload("/assets",ref,' + repr(selected_member) + ',missing_ok=' + repr(missing_ok) + '); '
              'print(json.dumps(str(root) if root is not None else None))')
    return json.loads(_owner_exec(target, helper, [target.get('python','python3'),'-B','-c',script]).stdout)


def prepare_docker(directory, attempt, request, deployment, incarnation):
    """Create a writable execution volume and separately owned published-asset view."""
    directory = Path(directory)
    target, endpoint = attempt['job']['backend'], attempt['job']['backend']['endpoint']
    prefix = 'exp-' + canonical([attempt['experiment_id'], attempt['attempt_id']])[:24]
    volume = prefix + '-execution'
    asset_volume = target.get('artifact_volume', 'exp-assets-' + canonical(endpoint['daemon_id'])[:24])
    rid = attempt['attempt_id']
    inherited_state = deployment.get('state_binding')
    workspace_id = inherited_state['holder_id'] if inherited_state else rid
    labels = {'io.factory26.exp.attempt': rid, 'io.factory26.exp.incarnation': incarnation,
              'io.factory26.exp.experiment': attempt['experiment_id']}
    owner = {'authority_resource_id': rid}
    managed(target, owner, 'reserve', request['request_id'] + '--reserve', {'role': 'execution', 'workspace': workspace_id, 'holder_generation': (inherited_state or {}).get('generation')})
    managed(target, owner, 'volume-create', request['request_id'] + '--workspace-volume',
            {'argv': ['volume', 'create', *[item for k, v in labels.items() for item in ('--label', k + '=' + v)], volume]})
    helper_rid = rid + '--store-owner'
    helper_binding = {'authority_resource_id': helper_rid}
    managed(target, helper_binding, 'reserve', request['request_id'] + '--owner-reserve', {'role': 'copy', 'workspace': None if inherited_state else workspace_id, 'parent_execution_resource': rid, 'preparation_request': request['request_id']})
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
    if not inherited_state:
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
    input_members = dict(attempt['job'].get('input_members', {}))
    prepared_descriptor = attempt['job'].get('prepared_descriptor')
    if prepared_descriptor:
        if prepared_descriptor.get('schema_version') not in (3,4):
            raise Blocked('Docker prepared execution requires separated v3 state and definition relations')
        for definition in prepared_descriptor['definition_assets']:
            input_refs['definition--' + definition['name']] = definition['artifact']
            input_members['definition--' + definition['name']] = definition['member']
    input_retentions = {}
    for name, ref in input_refs.items():
        selected_member = member(input_members.get(name, '.'))
        expected_location = attempt['job'].get('input_locations', {}).get(name)
        if expected_location and (expected_location.get('reference') != ref or expected_location.get('domain_identity', {}).get('daemon_id') != endpoint['daemon_id'] or expected_location.get('volume_id') != asset_volume or expected_location.get('store_root') != '/assets'):
            raise Blocked('input location differs from the exact target daemon/store binding; explicit cross-domain transfer required')
        # Query failure/declared unavailable bytes are not absence and never trigger transport.
        locations = store_action(directory, 'query', {})['locations']
        location = next((row for row in locations if row['reference'] == ref), None)
        if location and location['state'] != 'available':
            raise Blocked('input asset location is unavailable: ' + location['state'])
        selected_root = _domain_member_root(target, helper, ref, selected_member, missing_ok=True) if location else None
        if selected_root is None:
            from . import artifacts as asset_store
            source_store = Path(attempt['artifact_store'])
            staging = '/execution/staging/' + canonical([ref, selected_member])
            _owner_exec(target, helper, [target.get('python','python3'),'-c',
                'from pathlib import Path;Path(' + repr(staging) + ').mkdir(parents=True,exist_ok=True)'])
            if selected_member == '.':
                # A full request requires a real full source position.
                source_payload = asset_store.member_payload(source_store, ref, '.')
                received_root = staging + '/' + ref['artifact_id']
                _owner_exec(target, helper, [target.get('python','python3'),'-c',
                    'from pathlib import Path;Path(' + repr(received_root) + ').mkdir(exist_ok=True)'])
                for source, destination in ((source_store / ref['artifact_id'] / 'manifest.json', 'manifest.json'),
                                             (source_payload, 'payload')):
                    execute(endpoint, ['cp', str(source), helper['container_id'] + ':' + received_root + '/' + destination],
                            check=True, capture_output=True, text=True, timeout=1800)
                store_action(directory, 'transfer', {'source_store': staging, 'reference': ref,
                    'request_id': rid + '--input--' + name, 'consumer': rid})
            else:
                for source, destination in ((source_store / ref['artifact_id'] / 'manifest.json', 'manifest.json'),
                                             (asset_store.member_payload(source_store, ref, selected_member), 'member')):
                    execute(endpoint, ['cp', str(source), helper['container_id'] + ':' + staging + '/' + destination],
                            check=True, capture_output=True, text=True, timeout=1800)
                script = 'from lab.exp.artifacts import receive_member;import json;print(json.dumps(receive_member("/assets",json.loads(' + repr(json.dumps(ref)) + '),' + repr(staging + '/manifest.json') + ',' + repr(staging + '/member') + ',selected_member=' + repr(selected_member) + ',consumer=' + repr(rid) + ',request_id=' + repr(rid + '--input--' + name) + ')))'
                _owner_exec(target, helper, [target.get('python','python3'),'-B','-c',script])
        hold = store_action(directory, 'retain', {'reference': ref, 'consumer': rid, 'purpose': 'execution-input', 'request_id': rid + '--retain--' + name})
        input_retentions[canonical(ref)] = hold
        selected_root = _domain_member_root(target, helper, ref, selected_member)
        _owner_exec(target, helper, [target.get('python', 'python3'), '-c', 'from pathlib import Path; p=Path(' + repr('/execution/payload/inputs/' + name) + '); p.symlink_to(' + repr(selected_root) + ') if not p.exists() else None'])
    _owner_exec(target, helper, [target.get('python', 'python3'), '-c', "from pathlib import Path;[Path('/execution/payload/'+p).mkdir(exist_ok=True) for p in ('workspace','requests','inputs')]"])
    payload = dict(attempt)
    payload['artifact_store'] = '/assets'
    payload['job'] = dict(attempt['job'], inputs=attempt['job']['inputs'])
    atomic(directory / 'payload-attempt.json', payload)
    private = dict(deployment, input_retentions=input_retentions, runtime={'python': target.get('python', 'python3'), 'source': '/assets/' + code['artifact_id'] + '/payload',
                                       'identity': target.get('runtime_identity')})
    if deployment.get('credential_file'):
        execute(endpoint, ['cp', deployment['credential_file'], helper['container_id'] + ':/execution/payload/credentials.json'],
                check=True, capture_output=True, text=True, timeout=60)
        private['credential_file'] = '/execution/credentials.json'
    atomic(directory / 'payload-deployment.json', private)
    placements, definition_placements = [], []
    if attempt['job'].get('prepared') and not (prepared_descriptor or {}).get('state_binding'):
        manifest = prepared_descriptor
        if manifest is None:
            raise Blocked('prepared execution requires the controller resolved definition descriptor')
        from tooling.linux.exp_checkpoint import definition_mount_roots
        prepared_member = member(attempt['job'].get('input_members', {}).get('prepared', '.'))
        selected_state_member = 'content/run' if prepared_member == '.' else prepared_member + '/content/run'
        prepared_state_root = _domain_member_root(target, helper, attempt['job']['inputs']['prepared'], selected_state_member)
        run_root = Path(manifest['target_layout']['run_root'])
        if (not run_root.is_absolute() or run_root == Path('/') or run_root.is_relative_to('/assets')
                or run_root.is_relative_to('/execution') and not run_root.is_relative_to('/execution/workspace')):
            raise Blocked('prepared state root conflicts with isolated executor inputs or evidence namespace')
        mapping = {'logical_root': str(run_root), 'member': 'run', 'subpath': 'state/run', 'access': 'read-write'}
        source, destination = prepared_state_root, '/execution/' + mapping['subpath']
        script = 'import shutil;from pathlib import Path;src=Path(' + repr(source) + ');dst=Path(' + repr(destination) + ');' + 'dst.parent.mkdir(parents=True,exist_ok=True);shutil.copytree(src,dst,symlinks=True)'
        _owner_exec(target, helper, [target.get('python', 'python3'), '-c', script])
        placements.append(mapping)
        if not asset.get('Mountpoint') or not Path(asset['Mountpoint']).is_absolute():
            raise Blocked('definition read-only bindings require the selected daemon volume mountpoint')
        for definition in definition_mount_roots(manifest['definition_assets'], str(run_root)):
            root = Path(definition['logical_root'])
            if root == Path('/') or root.is_relative_to('/execution'):
                raise Blocked('definition root conflicts with writable executor namespace')
            remote = _domain_member_root(target, helper, definition['artifact'], definition['member'])
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
    if attempt['job'].get('definition') and not attempt['job'].get('prepared'):
        definition_ref = attempt['job']['definition']
        script = 'import json;from pathlib import Path;from lab.exp.definitions import resolve;v=json.loads(Path(' + repr('/assets/' + definition_ref['artifact_id'] + '/payload/definition.json') + ').read_text());print(json.dumps(resolve(v,"/assets",' + repr(rid) + ')))'
        roles = json.loads(_owner_exec(target, helper, [target.get('python', 'python3'), '-B', '-c', script]).stdout)
        base = '/execution/definitions/' + workspace_id
        for role in roles:
            definition_placements.append({**role, 'logical_root': base + '/' + role['role'], 'access': 'read-only',
                'daemon_source': str(Path(asset['Mountpoint']) / Path(role['local_root']).relative_to('/assets'))})
        private['definition_layout'] = {'base': base, 'kind': 'daemon-readonly-role-mounts', 'roles': definition_placements}
    elif prepared_descriptor and prepared_descriptor.get('state_binding'):
        from tooling.linux.exp_checkpoint import definition_mount_roots
        for definition in definition_mount_roots(prepared_descriptor['definition_assets'], prepared_descriptor['state_root']):
            remote = _domain_member_root(target, helper, definition['artifact'], definition['member'])
            definition_placements.append({**definition, 'role': definition['name'], 'reference': definition['artifact'],
                'access': 'read-only', 'daemon_source': str(Path(asset['Mountpoint']) / remote.removeprefix('/assets/'))})
        private['definition_layout'] = prepared_descriptor['layout'].get('definition_layout')
    if definition_placements:
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
    if not inherited_state:
        managed(target, helper, 'writer-close', request['request_id'] + '--owner-writer-close')
    if inherited_state:
        locator = inherited_state.get('selected_state', inherited_state['locator'])
        logical = prepared_descriptor['state_root']
        args[args.index('--env'):args.index('--env')] = ['--mount', f"type=volume,src={locator['volume']},dst={logical},volume-subpath={member(locator['subpath'])}"]
        private['layout_bindings'] = [{'logical_root': logical, 'member': 'run', 'subpath': locator['subpath'], 'volume': locator['volume'], 'access': 'read-write'}]
    resource = managed(target, owner, 'create', request['request_id'] + '--create', {'argv': args})
    resource.update(volume=volume, artifact_volume=asset_volume, daemon_id=endpoint['daemon_id'])
    atomic(directory / 'resource.json', record('resource', **resource))
    from . import state
    writer = {'resource_id': rid, 'attempt_id': rid, 'incarnation': incarnation}
    if inherited_state:
        state_binding = {**inherited_state, 'writer': writer}
    else:
        has_definition = bool(attempt['job'].get('definition'))
        state_subpath = 'payload/workspace/.factory26/' + rid if has_definition else 'payload/workspace'
        logical_root = '/execution/workspace/.factory26/' + rid if has_definition else '/execution/workspace'
        state_binding = record('state-binding', holder_id=workspace_id, generation=1, writer=writer,
            authority={'kind': 'docker', 'target': target, 'workspace': workspace_id},
            domain_identity={'kind': 'docker', 'daemon_id': endpoint['daemon_id'], 'volume_id': volume},
            locator={'kind': 'docker-volume', 'volume': volume, 'subpath': state_subpath, 'logical_root': logical_root, 'workspace_subpath': 'payload/workspace', 'workspace_logical_root': '/execution/workspace', 'metadata_subpath': 'payload', 'runtime_subpath': 'owner-runtime'},
            source_attempt_directory=str(directory.resolve()), volume_birth=admission.query(target, rid)['resource']['volume'])
        state.initialize(state_binding, writer, {'protocol': 'managed-writers-v1',
            'entry_contract': 'docker-cgroup-terminal-v1'}, request['request_id'] + '--state-initialize')
    if inherited_state:
        state.handoff_for_execution(state_binding, writer, {'holder_id': workspace_id,
            'generation': state_binding['generation'], 'workspace': prepared_descriptor['state_root']},
            request['request_id'] + '--handoff')
    if inherited_state:
        state_binding = {key: value for key, value in state_binding.items() if key not in ('capture_source', 'outer_relation')}
        state_binding.update(source_attempt_directory=str(directory.resolve()), execution_resource=resource,
            capture_layout={'workspace': {'volume':locator['volume'], 'subpath':locator['subpath'], 'logical_root':logical},
                            'state': {'volume':locator['volume'], 'subpath':locator['subpath'], 'logical_root':logical},
                            'metadata': {'volume':volume,'subpath':'payload'},
                            'code': {'volume':volume,'subpath':'owner-runtime'}})
    state_permit = record('state-permit', holder_id=workspace_id, generation=state_binding['generation'], writer=writer,
        resource={key: resource[key] for key in ('container_id', 'created', 'labels')},
        holder_readback=state.query(state_binding)['holder'], request_id=request['request_id'] + '--state-permit')
    deployment['state_binding'] = state_binding
    deployment['state_permit'] = state_permit
    private['state_binding'] = state_binding
    private['state_permit'] = state_permit
    private['namespace'] = {'kind': 'docker', 'daemon_id': endpoint['daemon_id'], 'container_id': resource['container_id'],
                            'created': resource['created'], 'labels': resource['labels']}
    atomic(directory / 'deployment.json', deployment)
    atomic(directory / 'payload-deployment.json', private)
    execute(endpoint, ['cp', str(directory / 'payload-deployment.json'), helper['container_id'] + ':/execution/payload/deployment.json'],
            check=True, capture_output=True, text=True, timeout=60)
    return resource


def _payload_workspace(directory):
    """Use the same physical run-state mapping for execution, outputs and export."""
    deployment = read(Path(directory) / 'payload-deployment.json')
    mapping = next((row for row in deployment.get('layout_bindings', []) if row['member'] == 'run'), None)
    if mapping and mapping.get('volume') and mapping['volume'] != read(Path(directory) / 'resource.json')['volume']:
        return '/held-state/' + member(mapping['subpath'])
    return '/execution/' + member(mapping['subpath']) if mapping else '/execution/payload/workspace'


def collect_named_outputs(directory, capture_helper):
    """Seal once in the daemon through a closed-state, read-only capture owner."""
    directory = Path(directory)
    attempt, resource = read(directory / 'attempt.json'), read(directory / 'resource.json')
    target = attempt['job']['backend']
    physical = exact_resource(target, resource)
    if physical['state'].get('Status') not in ('exited', 'dead'):
        raise Blocked('output publication requires exact physical terminality')
    receipt = read(directory / 'execution.json')
    from . import state
    helper_record = require(read(directory / 'capture-helper.json'), 'capture-helper')
    holder = state.query(helper_record['holder'])['holder']
    if (helper_record['binding']['container_id'] != capture_helper['container_id']
            or helper_record['capture'] != holder.get('capture')):
        raise Blocked('terminal helper no longer owns the actual capture lease')
    acquisition = state.capture_acquisition(helper_record['holder'], holder)
    script = r'''import json,sys
from pathlib import Path
from lab.exp.core import atomic,read
from lab.exp.artifacts import copy_file,allocate_scratch
from lab.exp.runner import _seal_outputs,_archive
payload=Path(sys.argv[3])
attempt=read(payload/'attempt.json')
receipt=json.loads(sys.argv[1])
if read(payload/'binding.json')['incarnation_id'] != receipt['incarnation_id']:
 raise ValueError('terminal capture incarnation differs from payload')
directory=allocate_scratch('/assets','captures/'+attempt['attempt_id'])
for name in ('attempt.json','binding.json','assembly.json','stdout.log','stderr.log','services.json','ready.json','external-resources.json','resource-evidence-seal.json'):
 source=payload/name
 if source.is_file() and not (directory/name).exists():copy_file(source,directory/name)
for name in ('telemetry','process-evidence','service-errors'):
 source=payload/name
 if source.exists() and not (directory/name).exists():(directory/name).symlink_to(source,target_is_directory=source.is_dir())
atomic(directory/'execution.json',receipt)
refs=_seal_outputs(directory,attempt,receipt,physical_workspace=sys.argv[2],acquisition=json.loads(sys.argv[4]))
refs=_archive(directory,attempt,receipt)
facts=read(directory/'outputs.json')
facts.update(artifacts=refs,result=receipt.get('result'))
atomic(directory/'outputs.json',facts)
print(json.dumps(facts))
'''
    facts = json.loads(_owner_exec(target, capture_helper,
        [target.get('python', 'python3'), '-B', '-c', script, json.dumps(receipt),
         capture_helper['capture_paths']['workspace'], capture_helper['capture_paths']['metadata'], json.dumps(acquisition)]).stdout)
    if facts['attempt_id'] != attempt['attempt_id'] or facts['incarnation_id'] != receipt['incarnation_id']:
        raise Blocked('daemon terminal publication belongs to another execution')
    refs = facts['artifacts']
    facts['locations'] = {name: {'reference': ref,
        'domain_identity': {'kind': 'docker', 'daemon_id': target['endpoint']['daemon_id']},
        'volume_id': resource['artifact_volume'], 'store_root': '/assets'} for name, ref in refs.items()}
    facts['workspace_snapshot']['location'] = {
        'reference': facts['workspace_snapshot']['reference'],
        'domain_identity': {'kind': 'docker', 'daemon_id': target['endpoint']['daemon_id']},
        'volume_id': resource['artifact_volume'], 'store_root': '/assets'}
    atomic(directory / 'outputs.json', facts)
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


def release_execution(directory):
    """Release proven terminal execution capacity without sealing or removing state."""
    directory = Path(directory)
    attempt, resource = read(directory / 'attempt.json'), read(directory / 'resource.json')
    target = attempt['job']['backend']
    observed = admission.query(target, resource['authority_resource_id'])
    if observed['resource']['phase'] != 'released':
        admission.reconcile(target, resource['authority_resource_id'], attempt['attempt_id'] + '--release',
                            domain_observation(target, resource))
        observed = admission.query(target, resource['authority_resource_id'])
    row = observed['resource']
    physical = row.get('identity') or {}
    if (row['phase'] != 'released' or physical.get('container_id') != resource['container_id']
            or physical.get('created') != resource['created']
            or physical.get('labels') != resource['labels']):
        raise Blocked('capacity release acknowledgement does not bind this exact physical resource')
    receipt = record('execution-capacity', attempt_id=attempt['attempt_id'], resource=resource,
                     capacity_released=True, status='released', observed_at=time.time(), authority=observed)
    atomic(directory / 'execution-capacity.json', receipt)
    return receipt


def finish_docker(directory):
    """Close this attempt's store helper independently of publication success."""
    directory = Path(directory)
    attempt = read(directory / 'attempt.json')
    target = attempt['job']['backend']
    release_execution(directory)
    helper_path = directory / 'store-helper.json'
    if not helper_path.exists():
        return
    helper = read(helper_path)
    if admission.query(target, helper['authority_resource_id'])['resource']['phase'] == 'released':
        return
    control_resource(target, helper, 'stop', request_id=attempt['attempt_id'] + '--owner-stop')
    managed(target, helper, 'writer-close', attempt['attempt_id'] + '--owner-writer-close')
    admission.reconcile(target, helper['authority_resource_id'], attempt['attempt_id'] + '--owner-release', domain_observation(target, helper))


def export_terminal_assets(directory, receipt, *, selections, target_store, consumer, request_id):
    """Transport only explicit immutable ref/member selections to their consumer."""
    directory = Path(directory)
    if not selections or not consumer or not target_store:
        raise ValueError('export requires selected assets, target store and consumer')
    offered = [(ref, receipt.get('output_members', {}).get(name, '.'), receipt['output_locations'][name])
               for name, ref in receipt.get('artifacts', {}).items()]
    snapshot = receipt.get('workspace_snapshot')
    if snapshot:
        offered.append((snapshot['reference'], snapshot.get('member', '.'), snapshot['location']))
    received = []
    for selection in selections:
        if set(selection) != {'reference', 'member', 'location'}:
            raise ValueError('export asset needs reference/member/location')
        ref, selected, origin = selection['reference'], member(selection['member']), selection['location']
        if not any(ref == known and origin == location for known, _, location in offered):
            raise Blocked('selected export is not an immutable asset offered by this attempt')
        export_named(directory, ref, origin, target_store, selected_member=selected,
                     consumer=consumer, request_id=identifier(request_id) + '--' + canonical([ref, selected])[:16])
        received.append({'reference': ref, 'member': selected, 'source': origin, 'store': str(target_store)})
    value = record('export', status='preserved', request_id=request_id, consumer=consumer,
                   mode='selected-sealed-assets', assets=received, exported_at=time.time())
    atomic(directory / 'exports' / (identifier(request_id) + '.json'), value)
    return value


def export_named(source_attempt_dir, reference, location, target_store, *, selected_member=".", consumer=None, request_id=None):
    """Explicit cross-domain receive of one retained named artifact, independent of archive."""
    directory, target_store = Path(source_attempt_dir), Path(target_store).resolve()
    attempt = read(directory / 'attempt.json')
    target = attempt['job']['backend']
    if target['kind'] != 'docker':
        target = target.get('external_docker')
    if not target:
        raise Blocked('named artifact source has no frozen Docker transport domain')
    selected_member = member(selected_member)
    if location['domain_identity']['kind'] != 'docker' or location['domain_identity']['daemon_id'] != target['endpoint']['daemon_id']:
        raise Blocked('named artifact location is not bound to its producer daemon')
    identifier(reference['artifact_id'])
    request_id = identifier(request_id or ('named-transfer-' + canonical([reference, location, str(target_store), selected_member, consumer])[:32]))
    transport = directory / 'named-transfers' / request_id
    transport.mkdir(parents=True, exist_ok=True)
    receipt_path = transport / 'effect.json'
    from .artifacts import transfer, verify, receive_member
    if receipt_path.exists() and read(receipt_path)['status'] == 'preserved':
        verify(target_store, reference, path=selected_member)
        helper_path = transport / 'helper.json'
        if helper_path.exists():
            helper = read(helper_path)
            if admission.query(target, helper['authority_resource_id'])['resource']['phase'] != 'released':
                if exact_resource(target, helper)['state'].get('Running'):
                    control_resource(target, helper, 'stop', request_id=request_id + '--stop')
                admission.reconcile(target, request_id, request_id + '--release', domain_observation(target, helper))
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
    atomic(receipt_path, record('named-transfer', request_id=request_id, reference=reference, source=location, selected_member=selected_member, consumer=consumer, status='receiving', stage=str(stage)))
    try:
        remote = helper['container_id'] + ':/assets/' + reference['artifact_id']
        if selected_member == '.':
            execute(target['endpoint'], ['cp', remote, str(stage)],
                    check=True, capture_output=True, text=True, timeout=1800)
            # Raw reception does not clone a managed-store authority.
            (stage / reference['artifact_id'] / 'location.json').unlink(missing_ok=True)
            verify(stage, reference)
            transfer(stage, target_store, reference, request_id=request_id, consumer=consumer or ('receiver:' + request_id))
        else:
            manifest_file = stage / 'manifest.json'
            execute(target['endpoint'], ['cp', remote + '/manifest.json', str(manifest_file)],
                    check=True, capture_output=True, text=True, timeout=60)
            execute(target['endpoint'], ['cp', remote + '/payload/' + selected_member, str(stage / 'member')],
                    check=True, capture_output=True, text=True, timeout=1800)
            receive_member(target_store, reference, manifest_file, stage / 'member',
                           selected_member=selected_member, request_id=request_id,
                           consumer=consumer or ('receiver:' + request_id))
        atomic(receipt_path, record('named-transfer', request_id=request_id, reference=reference, source=location,
              status='preserved', selected_member=selected_member, consumer=consumer, stage=str(stage), completed_at=time.time()))
        return reference
    except Exception as exc:
        atomic(stage / 'transport-error.json', error(exc))
        atomic(receipt_path, record('named-transfer', request_id=request_id, reference=reference, source=location,
              status='unknown', stage=str(stage), error=error(exc)))
        raise

    finally:
        try:
            if exact_resource(target, helper)['state'].get('Running'):
                control_resource(target, helper, 'stop', request_id=request_id + '--stop')
            if admission.query(target, request_id)['resource']['phase'] != 'released':
                admission.reconcile(target, request_id, request_id + '--release', domain_observation(target, helper))
        except Exception as cleanup_error:
            atomic(transport / 'close-error.json', record('error', **error(cleanup_error)))


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


def managed_state(binding, action, request_id, parameters=None):
    """Use the workspace's original domain authority, including during recovery."""
    from . import state
    return state.action(binding, action, request_id, parameters or {})


def close_state(binding, request_id, *, grace=10):
    """Close the accepted writer set by exact births; unknown actions retain the lease.

    This operation covers the holder's maintained launcher contract. It does not
    infer coverage from process groups, cwd scans or disappearance of one parent.
    """
    from . import state
    space = state.query(binding)
    holder = space['holder']
    if holder['phase'] != 'transfer-pending':
        raise Blocked('writer shutdown requires the accepted state transfer intent')
    authority = binding['authority']
    if authority['kind'] == 'docker':
        target = authority['target']
        resources = admission.query(target)['resources']
        for rid in holder['closing_writers']:
            row = resources.get(rid)
            if not row or row.get('pending'):
                raise Blocked('writer birth/action unresolved: ' + rid)
            if row['phase'] == 'released' and (row.get('disposal') or row.get('cancelled_reservation')):
                continue
            if not row.get('identity'):
                raise Blocked('writer birth unresolved: ' + rid)
            physical = {**row['identity'], 'authority_resource_id': rid}
            current = exact_resource(target, physical)
            if current['state'].get('Status') == 'created' and current['state'].get('StartedAt','').startswith('0001-'):
                if rid in state.query(binding).get('writers', []):
                    managed(target, physical, 'writer-close', request_id + '--close--' + rid)
                managed(target, physical, 'discard', request_id + '--discard--' + rid, {'volumes_preserved': True})
                continue
            if current['state'].get('Status') not in ('exited', 'dead'):
                managed(target, physical, 'stop', request_id + '--stop--' + rid, {'grace': grace})
            # Terminal readback is registered even for naturally completed writers.
            if row['phase'] != 'released':
                managed(target, physical, 'writer-close', request_id + '--close--' + rid)
                observation = domain_observation(target, physical)
                admission.reconcile(target, rid, request_id + '--terminal--' + rid, observation)
    elif authority['kind'] == 'local':
        registry = read(Path(authority['root']) / 'state-registry.json')
        for rid in reversed(holder['closing_writers']):
            row = registry['resources'].get(rid)
            if not row or row.get('pending') or not row.get('identity'):
                raise Blocked('registered Local writer birth is unresolved: ' + rid)
            physical = row['identity']
            status = process_state(physical)
            if status == 'unknown':
                raise Blocked('Local writer physical birth cannot be read back: ' + rid)
            if status == 'alive':
                os.kill(physical['pid'], signal.SIGTERM)
                deadline = time.monotonic() + grace
                while process_state(physical) == 'alive' and time.monotonic() < deadline:
                    time.sleep(.1)
                if process_state(physical) == 'alive':
                    os.kill(physical['pid'], signal.SIGKILL)
                deadline = time.monotonic() + grace
                while process_state(physical) == 'alive' and time.monotonic() < deadline:
                    time.sleep(.1)
            if process_state(physical) != 'lost':
                raise Blocked('Local writer exact terminal effect remains unknown: ' + rid)
            state.register_writer(binding, rid, row['incarnation'], physical, closed=True,
                shutdown={'closed': True, 'physical': physical, 'contract': holder['coverage']['entry_contract'],
                          'effect': 'exact-process-terminal', 'request_id': request_id, 'observed_at': time.time()})
    else:
        raise Blocked('backend has no maintained managed writer shutdown contract')
    return state.closure(binding)


def capture_helper(directory, state_binding, request_id, *, repair=False, assets_only=False):
    """Separate capture owner: state RO, published store RW, private scratch RW."""
    from . import state
    directory = Path(directory)
    holder = state.query(state_binding)['holder']
    capture = holder.get('capture')
    if not assets_only and (not capture or holder['phase'] not in ('capturing', 'snapshot-sealed', 'repairing', 'repaired')):
        raise Blocked('capture helper requires the independent holder lease')
    authority = state_binding['authority']
    if authority['kind'] != 'docker':
        raise Blocked('capture helper is a daemon-domain operation')
    target = authority['target']
    resource = read(directory / 'resource.json') if (directory / 'resource.json').exists() else (state_binding.get('execution_resource') or {})
    volume = holder['locator'].get('volume') or resource.get('volume')
    if not volume:
        raise Blocked('source execution volume has no actual managed binding')
    rid = identifier(request_id + '--capture-helper')
    owner = {'authority_resource_id': rid}
    managed(target, owner, 'reserve', request_id + '--reserve', {
        'role': 'copy', 'workspace': None if assets_only else authority['workspace'], 'holder_generation': holder['generation'],
        'state_access': 'repair' if repair else 'readonly', 'capture_owner': capture['owner'] if capture and not assets_only else None, 'capture_token': capture['token'] if capture and not assets_only else None})
    asset_volume = target.get('artifact_volume', 'exp-assets-' + canonical(target['endpoint']['daemon_id'])[:24])
    managed(target, owner, 'volume-create', request_id + '--assets-volume', {'argv': ['volume','create','--label','io.factory26.exp.asset-daemon=' + target['endpoint']['daemon_id'], asset_volume]})
    asset_birth = json.loads(execute(target['endpoint'], ['volume','inspect',asset_volume], check=True,capture_output=True,text=True,timeout=30).stdout)[0]
    if (asset_birth.get('Labels') or {}).get('io.factory26.exp.asset-daemon') != target['endpoint']['daemon_id']:
        raise Blocked('capture asset volume is not bound to the actual daemon')
    expected_volume = state_binding.get('volume_birth')
    if expected_volume:
        current_volume = json.loads(execute(target['endpoint'], ['volume', 'inspect', volume], check=True, capture_output=True, text=True, timeout=30).stdout)[0]
        if any(current_volume.get(key) != expected_volume.get(key) for key in ('Name', 'CreatedAt', 'Labels')):
            raise Blocked('state volume actual birth changed; original holder cannot redirect')
    metadata_volume = resource.get('volume') or state_binding['locator'].get('metadata_volume') or volume
    metadata_path = '/execution/' + member(state_binding['locator'].get('metadata_subpath', 'payload'))
    runtime_path = '/execution/' + member(state_binding['locator'].get('runtime_subpath', 'owner-runtime'))
    state_prefix = '/execution/' if metadata_volume == volume else '/held-state/'
    workspace_path = state_prefix + member(state_binding['locator'].get('workspace_subpath', 'payload/workspace'))
    state_path = state_prefix + member(state_binding['locator']['subpath'])
    layout = state_binding.get('capture_layout')
    if layout:
        if layout['metadata']['volume'] != metadata_volume or layout['workspace']['volume'] != volume or layout['state']['volume'] != volume:
            raise Blocked('current capture layout differs from admitted volume bindings')
        workspace_path = state_prefix + member(layout['workspace']['subpath'])
        state_path = state_prefix + member(layout['state']['subpath'])
        metadata_path = '/execution/' + member(layout['metadata']['subpath'])
        runtime_path = '/execution/' + member(layout['code']['subpath'])
    source_binding = state_binding.get('capture_source')
    records = {}
    if source_binding:
        namespace = source_binding['namespace']
        source_resource = state_binding.get('execution_resource') or admission.query(target, holder.get('prior_writer', holder.get('writer'))['resource_id'])['resource']['identity']
        if namespace['container_id'] != source_resource['container_id'] or namespace['created'] != source_resource['created'] or source_binding['workspace']['volume'] != volume:
            raise Blocked('capture source namespace/volume differs from its admitted birth')
        workspace_path = state_prefix + member(source_binding['workspace']['subpath'])
        state_path = state_prefix + member(source_binding.get('state_member', source_binding['workspace']['subpath']))
        runtime_path = state_prefix + member(source_binding['executor_code']['subpath'])
        records = {name: state_prefix + member(relative) for name, relative in source_binding.get('records', {}).items() if name in ('assembly','context','result','source_binding')}
        metadata_path = None
    name = 'exp-capture-' + canonical([authority['workspace'], request_id])[:24]
    args = ['create', '--name', name, '--restart', 'no', '--network', 'none', '--user', '0',
            '--memory', '512m', '--pids-limit', '64', '--label', 'io.factory26.exp.attempt=' + rid,
            '--label', 'io.factory26.exp.role=copy', '--mount', f'type=volume,src={metadata_volume},dst=/execution' + ('' if repair and metadata_volume == volume else ',readonly'),
            '--mount', f'type=volume,src={asset_volume},dst=/assets', '--tmpfs', '/capture:rw',
            '--env', 'PYTHONPATH=' + runtime_path, '--entrypoint', target.get('python', 'python3'),
            target['image_id'], '-B', '-c', 'import time;time.sleep(2147483647)']
    if metadata_volume != volume:
        args[args.index('--env'):args.index('--env')] = ['--mount', f'type=volume,src={volume},dst=/held-state' + ('' if repair else ',readonly')]
    if not assets_only:
        locator = holder['locator']
        logical = locator.get('logical_root')
        if logical and logical != '/execution/' + member(locator['subpath']):
            args[args.index('--env'):args.index('--env')] = ['--mount',
                f"type=volume,src={volume},dst={logical},volume-subpath={member(locator['subpath'])}" + ('' if repair else ',readonly')]
    physical = managed(target, owner, 'create', request_id + '--create', {'argv': args})
    physical = managed(target, physical, 'start', request_id + '--start')
    physical['started_at'] = physical['state']['StartedAt']
    physical['capture_paths'] = {'workspace': workspace_path, 'state': state_path, 'metadata': metadata_path, 'records': records, 'code': runtime_path, 'store': '/assets'}
    atomic(directory / 'capture-helper.json', record('capture-helper', binding=physical,
        holder=state_binding, capture=capture, request_id=request_id, state_access='repair' if repair else 'readonly',
        store_root='/assets', scratch_root='/capture'))
    return physical


def close_capture_helper(target, physical, request_id):
    stopped = managed(target, physical, 'stop', request_id + '--stop', {'grace': 10})
    return admission.reconcile(target, physical['authority_resource_id'], request_id + '--release',
                               domain_observation(target, stopped))


def install_recovery_assets(binding, rows, request_id):
    """Install explicit immutable dependencies before acquiring mutable capture."""
    from . import artifacts
    if binding['authority']['kind'] == 'local' or not rows:
        return rows
    target = binding['authority']['target']
    directory = Path(binding['source_attempt_directory'])
    receipt_path = directory / 'recovery-assets' / (identifier(request_id) + '.json')
    parameters = canonical(rows)
    if receipt_path.exists():
        saved = read(receipt_path)
        if saved['parameters_sha256'] != parameters:
            raise ValueError('recovery asset request reused with changed dependencies')
        helper = saved['helper']
        if admission.query(target, helper['authority_resource_id'])['resource']['phase'] != 'released':
            close_capture_helper(target, helper, saved['helper_request'] + '--close')
        return saved['installed']
    owner_path = receipt_path.with_name(receipt_path.stem + '.owner.json')
    owner = read(owner_path) if owner_path.exists() else {'generation': 0}
    helper_request = request_id + '--generation-' + str(owner['generation'])
    if owner_path.exists():
        prior = admission.query(target, helper_request + '--capture-helper').get('resource')
        if prior and prior['phase'] == 'released':
            owner['generation'] += 1
            helper_request = request_id + '--generation-' + str(owner['generation'])
    atomic(owner_path, record('recovery-asset-owner', request_id=request_id, helper_request=helper_request,
                            generation=owner['generation'], parameters_sha256=parameters))
    helper = capture_helper(directory, binding, helper_request, assets_only=True)
    installed = []
    script = "from lab.exp.artifacts import transfer,receive_member;import json,sys;r=json.loads(sys.argv[1]);kw=dict(consumer=r['consumer'],request_id=r['request_id']);receive_member('/assets',r['artifact'],r['stage']+'/manifest.json',r['stage']+'/member',selected_member=r['member'],**kw) if r['member']!='.' else transfer(r['stage'],'/assets',r['artifact'],**kw)"
    try:
        for row in rows:
            reference, selected = row['artifact'], member(row.get('member', '.'))
            artifacts.verify(row['store'], reference, path=selected)
            staging = '/capture/receive/' + canonical([reference,selected])
            _owner_exec(target, helper, [target.get('python','python3'),'-c','from pathlib import Path;Path(' + repr(staging) + ').mkdir(parents=True,exist_ok=True)'])
            if selected == '.':
                execute(target['endpoint'], ['cp', str(Path(row['store']) / reference['artifact_id']), helper['container_id'] + ':' + staging + '/' + reference['artifact_id']], check=True, capture_output=True, text=True, timeout=1800)
            else:
                for source, destination in ((Path(row['store']) / reference['artifact_id'] / 'manifest.json','manifest.json'),
                                             (artifacts.member_payload(row['store'], reference, selected),'member')):
                    execute(target['endpoint'], ['cp', str(source), helper['container_id'] + ':' + staging + '/' + destination], check=True, capture_output=True, text=True, timeout=1800)
            _owner_exec(target, helper, [target.get('python','python3'),'-B','-c',script,
                json.dumps({'stage':staging,'artifact':reference,'member':selected,'consumer':request_id,'request_id':request_id+'--'+canonical([reference,selected])[:20]})])
            installed.append({**row, 'store':'/assets'})
        atomic(receipt_path, record('recovery-assets', request_id=request_id, parameters_sha256=parameters, installed=installed, helper=helper, helper_request=helper_request))
        return installed
    finally:
        close_capture_helper(target, helper, helper_request + '--close')


def abort_recovery_assets(binding, request_id):
    """Close only this recovery's immutable installer; pending effects remain blocked."""
    if binding['authority']['kind'] != 'docker':
        return
    target = binding['authority']['target']
    owner_path = Path(binding['source_attempt_directory']) / 'recovery-assets' / (identifier(request_id) + '.owner.json')
    if not owner_path.exists():
        return
    helper_request = read(owner_path)['helper_request']
    rid = identifier(helper_request + '--capture-helper')
    row = admission.query(target, rid).get('resource')
    if not row or row['phase'] == 'released':
        return
    if row.get('pending') or not row.get('identity'):
        raise Blocked('recovery asset helper creation/start effect remains unresolved')
    physical = {**row['identity'], 'authority_resource_id': rid}
    close_capture_helper(target, physical, helper_request + '--close')


def finish_recovery_preparation(binding, request_id):
    """Reenter the original metadata producer's close without repeating repair I/O."""
    if binding['authority']['kind'] != 'docker':
        return
    target = binding['authority']['target']
    producer_request = request_id + '--repair--producer'
    rid = producer_request + '--capture-helper'
    row = admission.query(target, rid).get('resource')
    if not row or row['phase'] == 'released':
        return
    if row.get('pending') or not row.get('identity'):
        raise Blocked('original repair helper physical effect is unresolved')
    close_capture_helper(target, {**row['identity'], 'authority_resource_id':rid}, producer_request + '--close')


def prepare_in_domain(selection, output, store=None):
    """Repair under the retained capture lease; transport only small metadata."""
    from . import state
    from tooling.linux.exp_checkpoint import prepare
    binding = selection['state_binding']
    holder = state.query(binding)['holder']
    if holder['phase'] != 'repairing':
        raise Blocked('domain preparation needs the original repairing capture lease')
    if binding['authority']['kind'] == 'local':
        return prepare(selection['source'], output, selection['target'], selection['repair'],
                       artifact_store=store, state_binding=binding)
    resolver = read(Path(selection['source']) / 'domain-resolver.json')
    directory = Path(binding['source_attempt_directory']).resolve(strict=True)
    request_id = holder['repair']['request_id'] + '--producer'
    helper = capture_helper(directory, binding, request_id, repair=True)
    target = binding['authority']['target']
    script = r'''import json,sys
from pathlib import Path
from tooling.linux.exp_checkpoint import prepare
value=json.loads(sys.argv[1])
source=Path(value['source'])
output=source.parent/'prepared'/value['request_id']
if not (output/'harness-manifest.json').exists():
 prepare(source,output,value['target'],value['repair'],artifact_store='/assets',
         state_binding=value['binding'],state_readback=value['holder'])
from lab.exp.core import atomic,read
bindings=read(output/'provenance/asset-bindings.json')
for row in bindings.values():row.update({key:value['location'][key] for key in ('domain_identity','volume_id','store_root') if key in value['location']})
atomic(output/'provenance/asset-bindings.json',bindings)
print(json.dumps({p.relative_to(output).as_posix():p.read_text() for p in output.rglob('*') if p.is_file()}))
'''
    try:
        files = json.loads(_owner_exec(target, helper, [target.get('python', 'python3'), '-B', '-c', script,
            json.dumps({'source': resolver['metadata_root'], 'request_id': request_id,
                'target': selection['target'], 'repair': selection['repair'], 'binding': binding, 'holder': holder, 'location': resolver['location']})]).stdout)
        output = Path(output)
        if output.exists():
            raise FileExistsError('domain prepared metadata output already exists; retain original')
        output.mkdir(parents=True)
        for relative, contents in files.items():
            path = output / member(relative)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(contents)
        atomic(output / 'domain-resolver.json', record('checkpoint-domain-resolver',
            authority=binding['authority'], location=resolver['location'],
            metadata_root=resolver['metadata_root'].rsplit('/', 1)[0] + '/prepared/' + request_id))
        result = read(output / 'harness-manifest.json')
        import hashlib
        if digest(output / 'harness-manifest.json') != hashlib.sha256(files['harness-manifest.json'].encode()).hexdigest():
            raise Blocked('domain prepared metadata bytes differ from returned producer original')
        close_capture_helper(target, helper, request_id + '--close')
        return result
    except Exception as exc:
        atomic(directory / ('domain-prepare-' + request_id + '-error.json'), record('error', **error(exc)))
        raise


def prepare_snapshot_copy(selection, output, store):
    """Cross-domain projection transports selected state and missing definitions only."""
    from . import artifacts, state
    from tooling.linux.exp_checkpoint import prepare
    source = Path(selection['source'])
    if not (source / 'domain-resolver.json').exists():
        return prepare(source, output, selection['target'], selection['repair'], artifact_store=store)
    managed_source = read(source / 'managed-source.json')
    binding = managed_source['holder']
    holder = state.query(binding)['holder']
    directory = Path(binding['source_attempt_directory'])
    resolver = read(source / 'domain-resolver.json')
    manifest = read(source / 'harness-manifest.json')
    request_id = 'snapshot-copy-' + canonical([manifest['checkpoint_id'], selection['target'], selection['repair'], str(store)])[:32]
    helper = capture_helper(directory, binding, request_id, assets_only=True)
    target = binding['authority']['target']
    script = r'''import json,sys
from lab.exp import artifacts
from lab.exp.core import read
value=json.loads(sys.argv[1])
manifest=read(value['metadata']+'/harness-manifest.json')
binding=manifest['state_snapshot']
source=artifacts.resolve('/assets',binding['reference'],binding['member'],consumer=manifest['checkpoint_id'],retention=binding['retention'])
reference=artifacts.publish('/assets',source,'checkpoint-state-projection',
 provenance={'source_reference':binding['reference'],'source_member':binding['member'],'checkpoint_id':manifest['checkpoint_id']},
 request_id=value['request_id'],consumer=manifest['checkpoint_id'],purpose='cross-domain-state')
print(json.dumps(reference))
'''
    try:
        reference = json.loads(_owner_exec(target, helper, [target.get('python', 'python3'), '-B', '-c', script,
            json.dumps({'metadata': resolver['metadata_root'], 'request_id': request_id})]).stdout)
        location = {**resolver['location'], 'reference': reference}
        export_named(directory, reference, location, store)
        bindings = read(source / 'provenance/asset-bindings.json')
        received = set()
        for asset in manifest['definition_assets']:
            key = canonical(asset['artifact'])
            if key not in received:
                if not (Path(store) / asset['artifact']['artifact_id'] / 'manifest.json').exists():
                    export_named(directory, asset['artifact'], {**resolver['location'], 'reference': asset['artifact']}, store)
                received.add(key)
            bindings[asset['name']]['store'] = str(Path(store).resolve())
        projection = Path(output).parent / ('.' + Path(output).name + '.source-projection')
        if projection.exists():
            raise FileExistsError('snapshot source projection exists; retain partial and choose another output')
        shutil.copytree(source, projection, symlinks=True, copy_function=artifacts.copy_file)
        resolver_copy = projection / 'domain-resolver.json'
        resolver_copy.rename(projection / 'source-domain-resolver.json')
        consumer = manifest['checkpoint_id']
        manifest['source_state_snapshot'] = manifest['state_snapshot']
        manifest['state_snapshot'] = {'reference': reference, 'store': str(Path(store).resolve()), 'member': '.',
            'retention': artifacts.retain(store, reference, consumer, 'checkpoint-state', request_id + '--retain')}
        atomic(projection / 'harness-manifest.json', manifest)
        atomic(projection / 'provenance/asset-bindings.json', bindings)
        close_capture_helper(target, helper, request_id + '--close')
        return prepare(projection, output, selection['target'], selection['repair'], artifact_store=store)
    except Exception as exc:
        atomic(directory / (request_id + '-error.json'), record('error', **error(exc)))
        raise


def initialize_docker_state(target, physical, *, holder_id, attempt_id, incarnation,
                            volume, subpath, logical_root, request_id,
                            source_attempt_directory, volume_birth,
                            metadata_subpath='payload', runtime_subpath='owner-runtime',
                            workspace_subpath=None, workspace_logical_root=None, outer_relation=None):
    """Bind a genuine SDK or runner cgroup to its admitted state volume and namespace."""
    from . import state
    rid = physical['authority_resource_id']
    resource = admission.query(target, rid)['resource']
    if resource.get('workspace') != holder_id or resource.get('identity', {}).get('container_id') != physical['container_id']:
        raise Blocked('actual execution is not reserved in this holder authority')
    if volume_birth.get('Name') != volume:
        raise Blocked('state volume differs from its managed materialization')
    writer = {'resource_id': rid, 'attempt_id': attempt_id, 'incarnation': incarnation}
    binding = record('state-binding', holder_id=holder_id, generation=1, writer=writer,
        authority={'kind': 'docker', 'target': target, 'workspace': holder_id},
        domain_identity={'kind': 'docker', 'daemon_id': target['endpoint']['daemon_id'], 'volume_id': volume},
        locator={'kind': 'docker-volume', 'volume': volume, 'subpath': member(subpath),
                 'logical_root': logical_root, 'metadata_subpath': member(metadata_subpath),
                 'runtime_subpath': member(runtime_subpath), 'workspace_subpath': member(workspace_subpath or subpath),
                 'workspace_logical_root': workspace_logical_root or logical_root},
        source_attempt_directory=str(Path(source_attempt_directory).resolve()), volume_birth=volume_birth,
        execution_resource=physical, outer_relation=outer_relation)
    state.initialize(binding, writer, {'protocol': 'managed-writers-v1',
        'entry_contract': 'docker-cgroup-terminal-v1'}, request_id)
    return binding


def validate_in_domain(root):
    """Validate daemon-owned bytes through their frozen resolver, never host /assets."""
    from . import state
    root = Path(root)
    manifest = read(root / 'harness-manifest.json')
    resolver = read(root / 'domain-resolver.json')
    if manifest.get('state_binding'):
        binding = manifest['state_binding']
        holder = state.query(binding)['holder']
        if holder['phase'] != 'repaired' or holder['generation'] != binding['generation'] or not holder.get('capture'):
            raise Blocked('mutable prepared validation requires the unchanged repaired capture generation')
        immutable = False
    else:
        binding = read(root / 'managed-source.json')['holder']
        holder = state.query(binding)['holder']
        immutable = True
    directory = Path(binding['source_attempt_directory'])
    request_id = 'validate-' + canonical([str(root.resolve()), digest(root / 'harness-manifest.json'), time.time_ns()])[:32]
    helper = capture_helper(directory, binding, request_id, assets_only=immutable)
    target = binding['authority']['target']
    script = 'import json,sys;from tooling.linux.exp_checkpoint import validate;print(json.dumps(validate(sys.argv[1],_in_domain=True,_state_readback=json.loads(sys.argv[2]))))'
    try:
        result = json.loads(_owner_exec(target, helper, [target.get('python', 'python3'), '-B', '-c', script,
            resolver['metadata_root'], json.dumps(holder)]).stdout)
        if result['manifest_sha256'] != digest(root / 'harness-manifest.json'):
            raise Blocked('daemon metadata differs from the exact host checkpoint manifest')
        close_capture_helper(target, helper, request_id + '--close')
        return result
    except Exception as exc:
        atomic(directory / (request_id + '-error.json'), record('error', **error(exc)))
        raise


def abort_preentry(directory, request_id):
    """Release confirmed unstarted capacity, preserving volumes and original errors.

    A pending physical effect is unresolved, regardless of a failed caller receipt.
    This is an authority lifecycle operation, not a scan or a cleanup script.
    """
    directory = Path(directory)
    attempt = read(directory / 'attempt.json')
    target = attempt['job']['backend']
    rid = attempt['attempt_id']
    observation = admission.query(target, rid)
    row = observation.get('resource')
    value = record('preentry-abort', request_id=request_id, attempt_id=rid, source=observation,
                   state='unknown', volumes_preserved=True)
    path = directory / 'preentry-abort.json'
    atomic(path, value)
    if row is None:
        value.update(state='no-reservation', capacity_released=True)
    elif row.get('pending'):
        value.update(reason='pending physical action remains unresolved', capacity_released=False)
    elif row['phase'] == 'released':
        value.update(state='released', capacity_released=True)
    elif row['phase'] == 'reserved' and row['identity'] is None:
        parameters = {'reason': 'confirmed-preentry-failure', 'volumes_preserved': True}
        accepted = admission.action(target, rid, request_id + '--cancel', 'cancel-reservation', parameters,
            expected={'generation': row['generation'], 'version': row['version'], 'coverage_epoch': observation['domain']['coverage_epoch']})
        if accepted['effect']['status'] != 'applied':
            accepted = admission.complete(target, rid, request_id + '--cancel', 'cancel-reservation', parameters,
                                          result={'no_execution_accepted': True})
        value.update(state='reservation-cancelled', capacity_released=True, effect=accepted['effect'])
    elif row['phase'] == 'materialized' and row.get('identity'):
        physical = {**row['identity'], 'authority_resource_id': rid}
        current = exact_resource(target, physical)
        started = current['state'].get('StartedAt')
        if current['state'].get('Status') != 'created' or (started and not started.startswith('0001-')):
            value.update(reason='created object has an execution effect; managed stop/capture required', capacity_released=False)
        else:
            writers = (observation.get('workspace') or {}).get('writers', [])
            if rid in writers:
                managed(target, physical, 'writer-close', request_id + '--writer-close')
            effect = managed(target, physical, 'discard', request_id + '--discard', {'volumes_preserved': True})
            value.update(state='unstarted-object-discarded', capacity_released=True, effect=effect)
    else:
        value.update(reason='resource execution or ownership is not confirmed unstarted', capacity_released=False)
    # The recorded source helper is the only auxiliary owner this abort may drain.
    # A shared holder is not an ownership relation: another capture can use it.
    helpers = []
    helper_path = directory / 'store-helper.json'
    if row is not None and value.get('capacity_released') and helper_path.exists():
        saved = read(helper_path)
        helper_id = saved['authority_resource_id']
        observed = admission.query(target, helper_id)
        helper = observed.get('resource')
        if (helper and helper.get('parent_execution_resource') == rid
                and helper.get('preparation_request')
                and helper['role'] == 'copy' and helper['phase'] != 'released'):
            if helper.get('pending') or not helper.get('identity'):
                helpers.append({'resource_id': helper_id, 'state': 'unknown'})
            else:
                binding = {**helper['identity'], 'authority_resource_id': helper_id}
                if any(saved.get(key) != binding.get(key) for key in ('container_id','created','labels')):
                    raise Blocked('preentry helper differs from the exact recorded source owner')
                current = exact_resource(target, binding)
                writing = helper_id in (observed.get('workspace') or {}).get('writers', [])
                if current['state'].get('Status') == 'created' and current['state'].get('StartedAt','').startswith('0001-'):
                    if writing:
                        managed(target, binding, 'writer-close', request_id + '--helper-close')
                    managed(target, binding, 'discard', request_id + '--helper-discard', {'volumes_preserved': True})
                else:
                    stopped = managed(target, binding, 'stop', request_id + '--helper-stop')
                    if writing:
                        managed(target, stopped, 'writer-close', request_id + '--helper-close')
                    admission.reconcile(target, helper_id, request_id + '--helper-release', domain_observation(target, stopped))
                helpers.append({'resource_id': helper_id, 'state': 'released'})
    value['helpers'] = helpers
    atomic(path, value)
    return value


def seal_sdk_source(directory, binding, request_id):
    """Seal the actual SDK stage before reception; no selected Harness path is guessed.

    The outer attempt remains Local. The admitted child container and stage volume
    supply closure and payload identity. Official SDK resume is not a capability.
    """
    from . import state
    directory = Path(directory)
    source = binding.get('capture_source')
    if not source or binding['authority']['kind'] != 'docker':
        raise Blocked('SDK capture requires the actual child source binding')
    target = binding['authority']['target']
    saved_path = directory / 'sdk-workspace-snapshot.json'
    current = state.query(binding)['holder']
    if saved_path.exists():
        saved = read(saved_path)
        if saved.get('snapshot_request') == request_id and not current.get('capture'):
            return {'snapshot': saved, 'holder': current, 'source': source,
                    'capabilities': {'sdk_resume': False, 'harness_state_from_actual_bootstrap': True}}
    holder = state.begin_capture(directory, binding, request_id)
    acquisition = state.capture_acquisition(binding, holder)
    if holder.get('snapshot'):
        snapshot = holder['snapshot']
        readonly_id = request_id + '--readonly--capture-helper'
        readonly = admission.query(target, readonly_id).get('resource')
        if readonly and readonly['phase'] != 'released':
            if readonly.get('pending') or not readonly.get('identity'):
                raise Blocked('SDK snapshot sealed but readonly helper effect remains unresolved')
            close_capture_helper(target, {**readonly['identity'], 'authority_resource_id': readonly_id}, request_id + '--readonly-close')
    else:
        helper = capture_helper(directory, binding, request_id + '--readonly')
        script = r'''import json,sys
from lab.exp import artifacts
value=json.loads(sys.argv[1])
artifacts.initialize('/assets',value['domain'])
ref=artifacts.publish('/assets',value['workspace'],'sdk-workspace',
 provenance=value['provenance'],request_id=value['request_id'],
 consumer=value['consumer'],purpose='sdk-capture')
hold=artifacts.retain('/assets',ref,value['consumer'],'sdk-capture',value['request_id']+'--hold')
print(json.dumps({'reference':ref,'store':'/assets','member':'.','retention':hold}))
'''
        try:
            asset_volume = target.get('artifact_volume', 'exp-assets-' + canonical(target['endpoint']['daemon_id'])[:24])
            snapshot = json.loads(_owner_exec(target, helper, [target.get('python','python3'), '-B', '-c', script,
                json.dumps({'domain':{'kind':'docker','daemon_id':target['endpoint']['daemon_id'],'volume_id':asset_volume},
                    'workspace':helper['capture_paths']['workspace'], 'request_id':request_id+'--workspace',
                    'consumer':binding['writer']['attempt_id'], 'provenance':{
                        'source_namespace':source['namespace'], 'source_workspace':source['workspace'],
                        'outer':source.get('outer'), 'closure':holder['source_closure'], 'capture_token':holder['capture']['token'], 'acquisition':acquisition, 'sdk_resume':False}})]).stdout)
            snapshot.update(acquisition=acquisition, source_root=source['workspace']['logical_root'], holder=binding,
                generation=holder['generation'], snapshot_request=request_id,
                location={'reference':snapshot['reference'],'domain_identity':{'kind':'docker','daemon_id':target['endpoint']['daemon_id'],'volume_id':asset_volume},
                          'volume_id':asset_volume,'store_root':'/assets'})
            atomic(directory / 'sdk-workspace-snapshot.json', record('workspace-snapshot-binding', **snapshot))
            holder = state.bind_snapshot(binding, snapshot, request_id + '--snapshot')
            close_capture_helper(target, helper, request_id + '--readonly-close')
        except Exception as exc:
            atomic(directory / 'sdk-capture-error.json', record('error', request_id=request_id, **error(exc)))
            raise
    state.consumer_bindings(directory, snapshot, holder['consumers'], binding=binding)
    # Keep the sealed lease for the caller's RO inventory/reception helper. It must
    # close that helper before end_capture; no live writer is reopened.
    return {'snapshot': snapshot, 'holder': holder, 'source': source,
            'capabilities': {'sdk_resume': False, 'harness_state_from_actual_bootstrap': True}}
