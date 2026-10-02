"""A frozen, detached supervisor owns exactly one attempt and its collector."""
import argparse
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import time

# Frozen code carries the Python protobuf tree, including ZIP execution.
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'

from . import backends, telemetry
from .core import (atomic, canonical, error, identifier, locked, new_id, process_identity,
                   process_state, read, record, require, Blocked, member)


def _attempt(directory):
    return require(read(Path(directory) / 'attempt.json'), 'attempt')


def _request(directory, request):
    directory = Path(directory)
    require(request, 'request')
    identifier(request['request_id'])
    if request['attempt_id'] != _attempt(directory)['attempt_id']:
        raise ValueError('request targets another attempt')
    if canonical(request['parameters']) != request['parameters_sha256']:
        raise ValueError('request parameter digest differs')
    path = directory / 'requests' / (request['request_id'] + '.json')
    if path.exists():
        if canonical(read(path)) != canonical(request):
            raise ValueError('request identity reused with changed original')
    else:
        atomic(path, request)
    return path.with_suffix('.effect.json')


def _save(directory, receipt, **updates):
    receipt.update(updates, observed_at=time.time(), sequence=receipt.get('sequence', 0) + 1)
    receipt['phase'] = receipt['execution']
    atomic(Path(directory) / 'execution.json', receipt)
    return receipt


def _effect(path, request, status, **facts):
    value = record('effect', request_id=request['request_id'], attempt_id=request['attempt_id'],
                   action=request['action'], status=status, observed_at=time.time(), **facts)
    atomic(path, value)
    return value


def dispatch(attempt_dir):
    directory = Path(attempt_dir).resolve(strict=True)
    attempt = _attempt(directory)
    request = require(read(directory / 'request.json'), 'request')
    if request['action'] != 'dispatch':
        raise ValueError('attempt initial request must dispatch')
    with locked(directory / 'dispatch.lock'):
        effect = _request(directory, request)
        if (directory / 'execution.json').exists():
            saved = read(directory / 'execution.json')
            if saved['dispatch_request_id'] != request['request_id']:
                raise Blocked('attempt already bound to another dispatch; a new request cannot rerun main')
            return observe(directory)
        deployment = read(directory / 'deployment.json')
        job = attempt['job']
        limits = job['limits']
        for key in ('wall_seconds', 'storage_bytes', 'telemetry_bytes'):
            if isinstance(limits.get(key), bool) or not isinstance(limits.get(key), (float, int)) or limits[key] <= 0:
                raise ValueError(f'explicit positive attempt limit required: {key}')
        if not isinstance(job.get('command'), list) or not job['command'] or not all(isinstance(x, str) for x in job['command']):
            raise ValueError('job command must be nonempty argv of strings')
        free = __import__('shutil').disk_usage(directory).free
        if free < limits.get('storage_reserve_bytes', limits['storage_bytes']):
            raise Blocked('attempt storage reserve is unavailable; no active cache/evidence will be deleted')
        backends.capabilities(job['backend'])
        incarnation = new_id('runner')
        binding = record('binding', attempt_id=attempt['attempt_id'], incarnation_id=incarnation,
                         dispatch_request_id=request['request_id'], backend=job['backend']['kind'], accepted_at=time.time())
        atomic(directory / 'binding.json', binding)
        receipt = record('execution', attempt_id=attempt['attempt_id'], experiment_id=attempt['experiment_id'],
                         job_id=attempt['job_id'], incarnation_id=incarnation, dispatch_request_id=request['request_id'],
                         backend=job['backend']['kind'], accepted_at=time.time(), execution='accepted',
                         archive='pending', telemetry='pending', artifacts={}, sequence=0,
                         capabilities=backends.capabilities(job['backend']))
        _save(directory, receipt)
        _effect(effect, request, 'accepted', incarnation_id=incarnation)
        # Mark the unresolved launch window before Popen/create. Reentry never launches.
        _save(directory, receipt, execution='launch_pending', launch_intent_at=time.time())
        try:
            if job['backend']['kind'] == 'local':
                launch = backends.local_launch(directory, deployment)
            else:
                launch = backends.docker_launch(directory, attempt, request, deployment, incarnation)
            atomic(directory / 'launch.json', record('launch', attempt_id=attempt['attempt_id'], incarnation_id=incarnation,
                                                    dispatched_at=time.time(), **launch))
        except Exception as exc:
            # Side effects may have occurred. This is never a failed/no-execution proof.
            atomic(directory / 'launch-error.json', record('error', **error(exc)))
            _effect(effect, request, 'unknown', incarnation_id=incarnation, error=error(exc))
            return observe(directory)
    return observe(directory)


def observe(attempt_dir, live=False):
    directory = Path(attempt_dir)
    attempt = _attempt(directory)
    if not (directory / 'execution.json').exists():
        return record('execution', attempt_id=attempt['attempt_id'], execution='unaccepted', phase='unaccepted')
    receipt = read(directory / 'execution.json')
    if (directory / 'remote-execution.json').exists():
        receipt = read(directory / 'remote-execution.json')
    result = dict(receipt)
    result['phase'] = result['execution']
    if (directory / 'launch-error.json').exists():
        result['dispatch_error'] = read(directory / 'launch-error.json')
    if live:
        try:
            if attempt['job']['backend']['kind'] == 'docker':
                resource = read(directory / 'resource.json')
                physical = backends.exact_resource(attempt['job']['backend'], resource)
                result = backends.docker_read(directory)
                result['physical'] = physical
                result['phase'] = result['execution']
                if physical['state'].get('Status') in ('exited', 'dead') and result['execution'] not in ('exited', 'stopped', 'failed'):
                    result['phase'] = 'unknown'
                    result['execution_observation_gap'] = 'container terminal but entry exit/finalization receipt unavailable'
                result['backend_identity'] = {**read(directory / 'resource.json'), 'kind': 'docker', 'endpoint': attempt['job']['backend']['endpoint']}
                atomic(directory / 'remote-execution.json', result)
            else:
                binding = read(directory / 'binding.json')
                result['runner_identity_state'] = process_state(binding.get('runner_process'))
                if result['execution'] not in ('exited', 'stopped', 'failed') and result['runner_identity_state'] != 'alive':
                    launch_path = directory / 'launch.json'
                    launch_identity = read(launch_path).get('runner_process') if launch_path.exists() else None
                    if process_state(launch_identity) != 'alive':
                        result['phase'] = 'unknown'
                        result['execution_observation_gap'] = 'supervisor ownership unavailable; entry is not replayed'
                result['entry_identity_state'] = process_state(result.get('entry_process')) if result.get('entry_process') else 'unknown'
                result['external_resources'] = backends.external(directory)
                if result.get('backend_identity'):
                    result['backend_identity']['external_resources'] = [item['resource'] for item in result['external_resources']]
            result['live_observed_at'] = time.time()
        except Exception as exc:
            result['observation_error'] = error(exc)
    if (directory / 'export.json').exists():
        result['transport'] = read(directory / 'export.json')
    return result


def control(attempt_dir, request):
    directory = Path(attempt_dir)
    with locked(directory / 'control.lock'):
        effect = _request(directory, request)
        if effect.exists():
            return read(effect)
        binding = read(directory / 'binding.json')
        if request.get('expected_incarnation') != binding['incarnation_id']:
            return _effect(effect, request, 'rejected', error={'message': 'expected execution incarnation differs or is absent'}, actual_incarnation_id=binding['incarnation_id'])
        if request['action'] == 'export':
            _effect(effect, request, 'accepted', incarnation_id=binding['incarnation_id'])
            try:
                if _attempt(directory)['job']['backend']['kind'] == 'docker':
                    result = backends.docker_export(directory)
                else:
                    receipt = observe(directory, live=True)
                    if receipt['execution'] not in ('exited', 'stopped', 'failed') or receipt.get('entry_identity_state') == 'alive':
                        raise Blocked('terminal export requires execution/physical terminal evidence')
                    with locked(directory / 'worker.lock', blocking=False):
                        if receipt.get('archive') != 'preserved':
                            artifacts = _archive(directory, _attempt(directory), receipt)
                            _save(directory, receipt, archive='preserved', artifacts=artifacts, finalized_at=time.time())
                    result = {'artifacts': receipt.get('artifacts', {}), 'archive': receipt.get('archive')}
                return _effect(effect, request, 'applied', result=result)
            except Exception as exc:
                return _effect(effect, request, 'unknown', error=error(exc))
        if request['action'] not in ('stop', 'pause', 'resume'):
            return _effect(effect, request, 'rejected', error={'message': 'unsupported fixed control action'})
        target = _attempt(directory)['job']['backend']
        if target['kind'] == 'docker':
            try:
                resource = read(directory / 'resource.json')
                backends.exact_resource(target, resource)
                if request['action'] == 'stop':
                    # Ask runner to finalize first, then independently enforce physical stop.
                    try:
                        backends.docker_request(directory, request)
                    except Exception as exc:
                        atomic(directory / 'control-delivery-error.json', error(exc))
                    grace = _attempt(directory)['job']['limits'].get('stop_grace_seconds', 10)
                    deadline = time.monotonic() + grace + 5
                    while time.monotonic() < deadline:
                        current = backends.exact_resource(target, resource)
                        if not current['state'].get('Running'):
                            break
                        time.sleep(.25)
                    fact = backends.control_resource(target, resource, 'stop', grace)
                else:
                    fact = backends.control_resource(target, resource, request['action'])
                return _effect(effect, request, 'applied', physical=fact, incarnation_id=binding['incarnation_id'])
            except Exception as exc:
                return _effect(effect, request, 'unknown', error=error(exc))
        # Local IPC is a protected, durable inbox consumed by the exact frozen worker.
        if process_state(binding.get('runner_process')) != 'alive':
            if request['action'] != 'stop':
                return _effect(effect, request, 'unknown', error={'message': 'runner process ownership unavailable'})
            try:
                facts = backends.external(directory, 'stop')
                receipt = read(directory / 'execution.json')
                identity = receipt.get('entry_process')
                descendants = _group_members(identity['pid']) if identity and process_state(identity) == 'alive' else []
                if process_state(identity) == 'alive':
                    os.killpg(identity['pid'], signal.SIGTERM)
                    grace = _attempt(directory)['job']['limits'].get('stop_grace_seconds', 10)
                    deadline = time.monotonic() + grace
                    while process_state(identity) == 'alive' and time.monotonic() < deadline:
                        time.sleep(.25)
                    if process_state(identity) == 'alive':
                        os.killpg(identity['pid'], signal.SIGKILL)
                if identity:
                    _finish_group(identity['pid'], descendants, grace if descendants else 0)
                if process_state(identity) != 'lost':
                    raise Blocked('entry stop cannot be confirmed from exact birth identity')
                return _effect(effect, request, 'applied', physical={'entry_identity_state': 'lost'}, external_resources=facts,
                               execution_exit_code='unknown', archive='unknown')
            except Exception as exc:
                return _effect(effect, request, 'unknown', error=error(exc))
        return record('effect', request_id=request['request_id'], attempt_id=request['attempt_id'], action=request['action'],
                      status='queued', incarnation_id=binding['incarnation_id'])


def observe_source(source_identity):
    """A fresh observation binds the exact source instance, never a nearby process."""
    identifier(source_identity['attempt_id'])
    identifier(source_identity['execution_instance'])
    backend = source_identity['backend_identity']
    kind = backend['kind']
    if kind == 'local':
        state = process_state(backend['process'])
        result = {'status': 'stopped' if state == 'lost' else 'active' if state == 'alive' else 'unknown',
                  'identity_state': state}
        # Source carries child identities when its SDK owns external workload resources.
        group_members = _group_members(backend['process']['pid'])
        known = {canonical(identity) for identity in backend.get('group_members', [])}
        if group_members:
            result['status'] = 'active' if all(canonical(identity) in known for identity in group_members) else 'unknown'
        result['group_members'] = group_members
        children = []
        for child in backend.get('external_resources', []):
            if not child.get('started_at') or child['started_at'].startswith('0001-'):
                raise Blocked('external Docker source start instance was not bound')
            physical = backends.exact_resource(child['backend'], child)
            children.append(physical)
            if physical['state'].get('Status') not in ('exited', 'dead'):
                result['status'] = 'active' if physical['state'].get('Running') else 'unknown'
        result['external_resources'] = children
    elif kind == 'docker':
        if not backend.get('started_at') or backend['started_at'].startswith('0001-'):
            raise Blocked('Docker source execution start instance was not bound')
        physical = backends.exact_resource({'kind': 'docker', 'endpoint': backend['endpoint']}, backend)
        status = physical['state'].get('Status')
        result = {'status': 'stopped' if status in ('exited', 'dead') else 'active' if status in ('running', 'paused', 'restarting') else 'unknown',
                  'physical': physical}
    else:
        raise Blocked(f'unsupported source observation backend: {kind}')
    return record('source_observation', source_identity=source_identity, effect=result['status'], observed_at=time.time(), **result)


def _environment(job, deployment):
    # Ambient provider bindings cannot silently override the frozen recipe.
    names = ('PATH', 'HOME', 'USER', 'LOGNAME', 'SHELL', 'LANG', 'LC_ALL', 'TMPDIR', 'SYSTEMROOT')
    environment = {name: os.environ[name] for name in names if name in os.environ}
    environment.update(job.get('environment', {}))
    environment['PYTHONDONTWRITEBYTECODE'] = '1'
    if deployment.get('runtime', {}).get('source'):
        environment['PYTHONPATH'] = deployment['runtime']['source']
    if deployment.get('credential_file'):
        private = read(deployment['credential_file'])
        credentials = private.get('environment', private)
        import re
        declared = set()
        for binding in json.loads(job.get('environment', {}).get('FACTORY26_MODEL_BINDINGS', '{}')).values():
            declared.add(binding['credential_env'])
        if any(name in job.get('environment', {}) or name in {'MODEL', 'VISUAL_MODEL', 'FACTORY26_MODEL_BINDINGS'}
               or name.endswith('BASE_URL') or (name not in declared and not re.search(r'(?:API_KEY|TOKEN|PASSWORD|SECRET|CREDENTIAL)$', name))
               for name in credentials):
            raise ValueError('private credential file cannot override frozen provider/model/runtime policy')
        environment.update(credentials)
    if not all(isinstance(k, str) and isinstance(v, str) for k, v in environment.items()):
        raise ValueError('execution environment must contain only string keys/values')
    return environment


def _expand(value, directory, job):
    assembled = read(directory / 'assembly.json')['workspace'] if (directory / 'assembly.json').exists() else str(directory / 'workspace')
    names = {'attempt_dir': str(directory), 'workspace': assembled, 'inputs': str(directory / 'inputs')}
    names.update({name: str(directory / 'inputs' / name) for name in job.get('inputs', {})})
    for name, replacement in names.items():
        value = value.replace('{' + name + '}', replacement)
    return value


def _assemble(directory, attempt, deployment):
    """Place verified prepared content at its declared logical roots, without migration."""
    import platform
    import shutil
    job = attempt['job']
    if not job.get('prepared'):
        return directory / 'workspace'
    prepared = directory / 'inputs' / 'prepared'
    from submission.exp_checkpoint import validate, inventory
    validation = validate(prepared)
    manifest = read(prepared / 'harness-manifest.json')
    if manifest['kind'] != 'factory26.harness.prepared' or validation['status'] != 'complete':
        raise Blocked('execution requires complete prepared content')
    target = manifest['target_layout']
    if target['os'] != platform.system() or target['architecture'] != platform.machine():
        raise Blocked('prepared target OS/architecture differs from actual worker')
    runtime_identity = job['backend'].get('runtime_identity') if job['backend']['kind'] == 'docker' else deployment['runtime'].get('identity')
    if not runtime_identity or target['runtime_identity'] != runtime_identity:
        raise Blocked('prepared runtime identity differs from explicitly frozen target')
    if job['backend']['kind'] == 'docker':
        from .core import digest
        if (runtime_identity.get('image_id') != job['backend']['image_id'] or
                runtime_identity.get('python_sha256') != digest(Path(sys.executable).resolve(strict=True))):
            raise Blocked('prepared Docker runtime is not the actual image/interpreter asset')
    if target['run_root'] != manifest['layout']['run_root']:
        raise Blocked('prepared producer does not support native logical-root migration')
    mappings = [{'logical_root': target['run_root'], 'member': 'run'}] + manifest['materials']
    roots = []
    for mapping in mappings:
        root = Path(mapping['logical_root'])
        if not root.is_absolute() or root == Path('/') or '..' in root.parts:
            raise ValueError('prepared logical root must be a bounded absolute directory')
        if root.exists() or root.is_symlink():
            raise Blocked(f'prepared target placement is occupied; original source/materials are not overwritten: {root}')
        if root.is_relative_to(directory) or directory.is_relative_to(root):
            raise Blocked('prepared logical placement overlaps supervisor inputs/runtime/evidence')
        for parent in root.parents:
            if parent.is_symlink():
                raise Blocked('prepared logical placement traverses an unbound external link')
        if any(root.is_relative_to(previous) or previous.is_relative_to(root) for previous in roots):
            raise Blocked('prepared logical roots overlap; producer must provide an unambiguous assembly')
        roots.append(root)
    intent = record('assembly', status='staging', prepared=job['prepared'], target_layout=target,
                    mappings=mappings, workspace=target['run_root'], started_at=time.time())
    atomic(directory / 'assembly.json', intent)
    try:
        for mapping, target_root in zip(mappings, roots):
            source = prepared / 'content' / member(mapping['member'])
            if source.is_symlink() or not source.resolve().is_relative_to((prepared / 'content').resolve()):
                raise ValueError('prepared composition member escapes content')
            expected = inventory(source)
            target_root.parent.mkdir(parents=True, exist_ok=True)
            staging = target_root.with_name('.' + target_root.name + '.' + new_id('assembly'))
            shutil.copytree(source, staging, symlinks=True)
            if inventory(staging) != expected:
                raise ValueError('prepared assembly independent content readback differs')
            staging.rename(target_root)
        intent.update(status='assembled', completed_at=time.time(), actual_os=platform.system(), actual_architecture=platform.machine(), runtime_identity=runtime_identity)
        atomic(directory / 'assembly.json', intent)
        return Path(target['run_root'])
    except Exception as exc:
        intent.update(status='failed', error=error(exc))
        atomic(directory / 'assembly.json', intent)
        raise


def _size(root):
    total = 0
    for directory, _, files in os.walk(root, followlinks=False):
        for name in files:
            path = Path(directory) / name
            if not path.is_symlink():
                try:
                    total += path.stat().st_size
                except FileNotFoundError:
                    pass
    return total


def _telemetry_size(directory):
    roots = [directory]
    manifest = directory / 'telemetry-sources.json'
    if manifest.exists():
        value = require(read(manifest), 'telemetry_sources')
        for source in value['sources']:
            path = directory / member(source['relative_path'])
            if not path.resolve().is_relative_to(directory.resolve()):
                raise ValueError('telemetry source escapes attempt domain')
            roots.append(path)
    return sum(_size(root / 'telemetry') for root in roots)


def _group_members(group_id):
    result = subprocess.run(['ps', '-eo', 'pid=,pgid=,stat='], capture_output=True, text=True, check=True)
    members = []
    for line in result.stdout.splitlines():
        fields = line.split()
        if len(fields) >= 3 and fields[1] == str(group_id) and not fields[2].startswith('Z'):
            pid = int(fields[0])
            identity = process_identity(pid)
            if not identity.get('boot_id') or not identity.get('process_start'):
                # ps is a snapshot: a short-lived child can exit before birth is
                # read. Only a fresh absent/nonmember observation can skip it.
                current = subprocess.run(['ps', '-p', str(pid), '-o', 'pgid=,stat='], capture_output=True, text=True)
                if current.returncode == 1 and not current.stdout.strip() and process_state(identity) == 'lost':
                    continue
                current.check_returncode()
                current_fields = current.stdout.split()
                if len(current_fields) >= 2 and (current_fields[0] != str(group_id) or current_fields[1].startswith('Z')):
                    continue
                identity = process_identity(pid)
            if identity.get('boot_id') and identity.get('process_start'):
                members.append(identity)
            else:
                failure = Blocked(f'process group member birth identity is unavailable: pid={pid}, group={group_id}')
                failure.detail = {'identity': identity, 'current_ps': current.stdout, 'current_ps_stderr': current.stderr}
                raise failure
    return members


def _finish_group(group_id, observed, grace):
    """Clean known descendants; unobserved members remain a physical ownership gap."""
    known = {canonical(identity): identity for identity in observed}
    current = _group_members(group_id)
    if any(canonical(identity) not in known for identity in current):
        raise Blocked('unobserved descendants remain after entry exit; no stopped proof is claimed')
    for identity in current:
        if process_state(identity) == 'alive':
            os.kill(identity['pid'], signal.SIGCONT)
            os.kill(identity['pid'], signal.SIGTERM)
    deadline = time.monotonic() + grace
    while _group_members(group_id) and time.monotonic() < deadline:
        time.sleep(.1)
    for identity in _group_members(group_id):
        if canonical(identity) not in known or process_state(identity) != 'alive':
            raise Blocked('descendant ownership changed during stop escalation')
        os.kill(identity['pid'], signal.SIGKILL)
    deadline = time.monotonic() + 5
    while _group_members(group_id) and time.monotonic() < deadline:
        time.sleep(.1)
    if _group_members(group_id):
        raise Blocked('process group stop could not be physically confirmed')


def _terminate(process, identity, grace):
    if process.poll() is not None:
        return
    if process_state(identity) != 'alive':
        raise Blocked('cannot signal a process without the original birth identity')
    os.killpg(process.pid, signal.SIGCONT)
    os.killpg(process.pid, signal.SIGTERM)
    try:
        process.wait(timeout=grace)
    except subprocess.TimeoutExpired:
        if process_state(identity) != 'alive':
            raise Blocked('process birth changed during stop escalation')
        os.killpg(process.pid, signal.SIGKILL)
        process.wait()


def _archive(directory, attempt, receipt):
    from .artifacts import publish
    import shutil
    job = attempt['job']
    workspace = Path(read(directory / 'assembly.json')['workspace']) if (directory / 'assembly.json').exists() else directory / 'workspace'
    evidence_size = _size(workspace) + _size(directory / 'telemetry')
    output_size = sum(_size(workspace / member(row['path'])) if (workspace / member(row['path'])).is_dir()
                      else (workspace / member(row['path'])).stat().st_size
                      for row in job.get('outputs', []) if (workspace / member(row['path'])).exists())
    reserve = job['limits'].get('storage_reserve_bytes', job['limits']['storage_bytes'])
    if shutil.disk_usage(directory).free < reserve + 2 * evidence_size + output_size:
        raise Blocked('terminal preservation scratch/reserve unavailable; source evidence remains and main is not repeated')
    artifacts = dict(receipt.get('artifacts', {}))
    for output in job.get('outputs', []):
        name = identifier(output['name'])
        if name in artifacts:
            continue
        relative = member(output['path'])
        source = workspace / relative
        if not source.exists():
            receipt.setdefault('missing_outputs', []).append(name)
            continue
        if source.is_symlink() or not source.resolve().is_relative_to(workspace.resolve()):
            raise ValueError(f'output escapes attempt workspace: {relative}')
        artifacts[name] = publish(attempt['artifact_store'], source, output['type'],
                                  {'attempt_id': attempt['attempt_id'], 'incarnation_id': receipt['incarnation_id'], 'output': name})
        _save(directory, receipt, artifacts=artifacts)
    result_path = job.get('result_path')
    if result_path:
        result = workspace / member(result_path)
        if result.exists():
            if result.is_symlink() or not result.resolve().is_relative_to(workspace.resolve()):
                raise ValueError('result file escapes workspace')
            receipt['result'] = read(result)
    # Archive evidence has a distinct role; it makes no checkpoint completeness claim.
    archive = directory / 'terminal-evidence'
    archive.mkdir(exist_ok=True)
    for name in ('stdout.log', 'stderr.log', 'binding.json', 'execution.json', 'external-resources.json'):
        if (directory / name).exists():
            shutil.copy2(directory / name, archive / name)
    shutil.copytree(workspace, archive / 'workspace', symlinks=True, dirs_exist_ok=True)
    if (directory / 'telemetry').exists():
        shutil.copytree(directory / 'telemetry', archive / 'telemetry', ignore=shutil.ignore_patterns('credential.json'), dirs_exist_ok=True)
    atomic(archive / 'telemetry-cutoff.json', telemetry.snapshot(directory))
    artifacts['terminal_archive'] = publish(attempt['artifact_store'], archive, 'terminal-archive',
                                          {'attempt_id': attempt['attempt_id'], 'incarnation_id': receipt['incarnation_id']},
                                          {'checkpoint': False, 'workspace_preserved_in_execution_domain': True})
    return artifacts


def worker(attempt_dir):
    directory = Path(attempt_dir).resolve(strict=True)
    with locked(directory / 'worker.lock', blocking=False):
        attempt, deployment = _attempt(directory), read(directory / 'deployment.json')
        binding = read(directory / 'binding.json')
        receipt = require(read(directory / 'execution.json'), 'execution')
        if receipt['execution'] != 'launch_pending' or receipt['incarnation_id'] != binding['incarnation_id']:
            raise Blocked('runner entry cannot be replayed from existing execution facts')
        binding['runner_process'] = process_identity()
        binding['control_inbox'] = str(directory / 'requests')
        atomic(directory / 'binding.json', binding)
        job, limits = attempt['job'], attempt['job']['limits']
        if job['backend']['kind'] == 'docker':
            deadline = time.monotonic() + limits['wall_seconds']
            while not (directory / 'resource-start.json').exists():
                if time.monotonic() >= deadline:
                    _save(directory, receipt, execution='unknown', error={'message': 'container started but exact StartedAt binding was not delivered'})
                    return
                time.sleep(.1)
            atomic(directory / 'resource.json', read(directory / 'resource-start.json'))
        (directory / 'workspace').mkdir(exist_ok=True)
        (directory / 'requests').mkdir(exist_ok=True)
        collector, process, identity = None, None, None
        stopped, stop_reason = False, None
        stop_signal = []
        signal.signal(signal.SIGTERM, lambda *_: stop_signal.append('supervisor_sigterm'))
        signal.signal(signal.SIGINT, lambda *_: stop_signal.append('supervisor_sigint'))
        try:
            workspace = _assemble(directory, attempt, deployment)
            enabled = job.get('telemetry', {}).get('enabled', True)
            if enabled:
                collector = telemetry.Collector(directory, attempt['attempt_id'], cap_bytes=limits['telemetry_bytes'])
            environment = _environment(job, deployment)
            environment.update({'FACTORY26_EXP_ATTEMPT_DIR': str(directory), 'FACTORY26_EXP_ATTEMPT_ID': attempt['attempt_id'],
                                'FACTORY26_EXP_INCARNATION': binding['incarnation_id'],
                                'FACTORY26_EXP_TELEMETRY_CAP_BYTES': str(limits['telemetry_bytes'])})
            if job['backend'].get('external_docker'):
                external_target = job['backend']['external_docker']
                environment['EXPERIMENT_DOCKER_ENDPOINT'] = json.dumps(external_target['endpoint'])
                environment['EXP_ADMISSION_VOLUME'] = external_target['admission_volume']
                environment['EXP_ADMISSION_SLOTS'] = str(external_target['slots'])
            if collector:
                environment.update(collector.environment())
                environment['FACTORY26_EXP_TELEMETRY_BINDING'] = json.dumps({'endpoint': collector.binding['receiver_endpoint'], 'token': collector.token, **{k: collector.binding[k] for k in ('attempt_id', 'stream_id', 'collector_epoch')}})
            command = [_expand(value, directory, job) for value in job['command']]
            _save(directory, receipt, execution='entry_launch_pending', entry_launch_intent_at=time.time(), command=command,
                  runner_process=binding['runner_process'], telemetry='active' if collector else 'disabled')
            with (directory / 'stdout.log').open('ab', buffering=0) as stdout, (directory / 'stderr.log').open('ab', buffering=0) as stderr:
                entry_environment = dict(environment)
                entry_environment['PYTHONPATH'] = deployment['runtime']['source']
                process = subprocess.Popen([deployment['runtime']['python'], '-B', '-m', 'lab.exp.runner', 'internal_entry', str(directory)],
                                           cwd=workspace, env=entry_environment, stdin=subprocess.DEVNULL,
                                           stdout=stdout, stderr=stderr, start_new_session=True, close_fds=True)
                identity = process_identity(process.pid)
                backend_identity = {'kind': 'local', 'process': identity}
                if job['backend']['kind'] == 'docker':
                    backend_identity = {**read(directory / 'resource.json'), 'kind': 'docker', 'endpoint': job['backend']['endpoint']}
                _save(directory, receipt, execution='running', entry_process=identity, backend_identity=backend_identity, started_at=time.time())
                _effect(directory / 'requests' / (receipt['dispatch_request_id'] + '.effect.json'), read(directory / 'request.json'),
                        'applied', incarnation_id=binding['incarnation_id'], entry_process=identity)
                deadline = time.monotonic() + limits['wall_seconds']
                known_descendants = {}
                while True:
                    if process.poll() is not None:
                        break
                    if process_state(identity) == 'alive':
                        for descendant in _group_members(process.pid):
                            known_descendants[canonical(descendant)] = descendant
                    if process.poll() is not None:
                        break
                    for path in sorted((directory / 'requests').glob('*.json')):
                        if path.name.endswith('.effect.json'):
                            continue
                        request = read(path)
                        effect = path.with_suffix('.effect.json')
                        if effect.exists() or request['action'] == 'dispatch':
                            continue
                        if request.get('expected_incarnation') != binding['incarnation_id']:
                            _effect(effect, request, 'rejected', error={'message': 'execution incarnation differs'})
                            continue
                        _effect(effect, request, 'accepted', incarnation_id=binding['incarnation_id'])
                        try:
                            action = request['action']
                            if action not in ('stop', 'pause', 'resume'):
                                raise ValueError('unsupported runner action')
                            facts = backends.external(directory, action, limits.get('stop_grace_seconds', 10), include_helpers=False)
                            if action == 'stop':
                                _terminate(process, identity, limits.get('stop_grace_seconds', 10))
                                _finish_group(process.pid, list(known_descendants.values()), limits.get('stop_grace_seconds', 10))
                                stopped, stop_reason = True, 'control_request'
                            else:
                                if process_state(identity) != 'alive':
                                    raise Blocked('entry identity is unavailable')
                                os.killpg(process.pid, signal.SIGSTOP if action == 'pause' else signal.SIGCONT)
                                _save(directory, receipt, execution='paused' if action == 'pause' else 'running')
                            _effect(effect, request, 'applied', incarnation_id=binding['incarnation_id'], entry_process=identity,
                                    external_resources=facts, exit_code=process.poll())
                        except Exception as exc:
                            _effect(effect, request, 'unknown', error=error(exc))
                    reason = stop_signal[0] if stop_signal else ('wall_limit' if time.monotonic() >= deadline else None)
                    if reason is None and _size(workspace) + sum((directory / name).stat().st_size for name in ('stdout.log', 'stderr.log')) > limits['storage_bytes']:
                        reason = 'workspace_storage_limit'
                    if reason is None and _telemetry_size(directory) > limits['telemetry_bytes']:
                        reason = 'aggregate_telemetry_storage_limit'
                    if reason:
                        backends.external(directory, 'stop', limits.get('stop_grace_seconds', 10), include_helpers=False)
                        _terminate(process, identity, limits.get('stop_grace_seconds', 10))
                        stopped, stop_reason = True, reason
                    time.sleep(.25)
                exit_code = process.wait()
                _save(directory, receipt, entry_exit_code=exit_code, entry_finished_at=time.time())
                _finish_group(process.pid, list(known_descendants.values()), limits.get('stop_grace_seconds', 10))
                receipt['process_group'] = {'group_id': process.pid, 'members': list(known_descendants.values()), 'effect': 'stopped'}
                receipt['backend_identity']['group_members'] = list(known_descendants.values())
            # SDK child containers may outlive its parent; terminality must inspect them.
            facts = backends.external(directory)
            if any(any(item['observation']['state'].get(k) for k in ('Running', 'Paused', 'Restarting')) for item in facts):
                facts = backends.external(directory, 'stop', limits.get('stop_grace_seconds', 10))
            if receipt.get('backend_identity'):
                receipt['backend_identity']['external_resources'] = [item['resource'] for item in facts]
            _save(directory, receipt, execution='stopped' if stopped else 'exited', exit_code=exit_code,
                  finished_at=time.time(), stop_reason=stop_reason, external_resources=facts)
        except Exception as exc:
            if process is not None and process.poll() is None:
                try:
                    backends.external(directory, 'stop', limits.get('stop_grace_seconds', 10))
                    _terminate(process, identity, limits.get('stop_grace_seconds', 10))
                except Exception as stop_exc:
                    receipt['stop_error'] = error(stop_exc)
            if process is not None and process.poll() is not None:
                _save(directory, receipt, entry_exit_code=process.returncode,
                      entry_finished_at=receipt.get('entry_finished_at', time.time()))
            _save(directory, receipt, execution='unknown' if process else 'failed', error=error(exc), finished_at=time.time())
        finally:
            if collector:
                try:
                    seal = collector.close(producer_flush='unknown')
                    _save(directory, receipt, telemetry='sealed', collector_seal=seal)
                except Exception as exc:
                    _save(directory, receipt, telemetry='unknown', collector_error=error(exc))
            try:
                telemetry_sources = telemetry.finalize_sources(directory)
                _save(directory, receipt, telemetry_sources=telemetry_sources)
                artifacts = _archive(directory, attempt, receipt)
                _save(directory, receipt, archive='preserved', artifacts=artifacts, finalized_at=time.time())
            except Exception as exc:
                _save(directory, receipt, archive='failed', archive_error=error(exc))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['internal_worker', 'internal_entry'])
    parser.add_argument('attempt_dir', type=Path)
    args = parser.parse_args()
    if args.action == 'internal_entry':
        attempt = _attempt(args.attempt_dir)
        limits = attempt['job']['limits']
        resource.setrlimit(resource.RLIMIT_FSIZE, (int(limits['storage_bytes']), int(limits['storage_bytes'])))
        if limits.get('cpu_seconds'):
            resource.setrlimit(resource.RLIMIT_CPU, (int(limits['cpu_seconds']), int(limits['cpu_seconds'])))
        if limits.get('memory_bytes') and sys.platform.startswith('linux'):
            resource.setrlimit(resource.RLIMIT_AS, (int(limits['memory_bytes']), int(limits['memory_bytes'])))
        environment = _environment(attempt['job'], read(args.attempt_dir / 'deployment.json'))
        for name in ('FACTORY26_EXP_ATTEMPT_DIR','FACTORY26_EXP_ATTEMPT_ID','FACTORY26_EXP_INCARNATION','FACTORY26_EXP_TELEMETRY_BINDING','FACTORY26_EXP_TELEMETRY_CAP_BYTES','OTEL_EXPORTER_OTLP_ENDPOINT','OTEL_EXPORTER_OTLP_PROTOCOL','OTEL_EXPORTER_OTLP_HEADERS','EXPERIMENT_DOCKER_ENDPOINT','EXP_ADMISSION_VOLUME','EXP_ADMISSION_SLOTS'):
            if name in os.environ:
                environment[name] = os.environ[name]
        command = read(args.attempt_dir / 'execution.json')['command']
        os.execvpe(command[0], command, environment)
    else:
        worker(args.attempt_dir)


if __name__ == '__main__':
    main()
