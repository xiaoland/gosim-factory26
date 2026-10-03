"""Read saved producer facts into an experiment view, without observing resources.

The view does not authorize execution. Commands supplied by the controller must
revalidate ownership, inputs and physical state when invoked.
"""
from datetime import datetime, timezone
from pathlib import Path
import shlex
import json

from .core import digest, error, identifier, public, read as read_json, record, require


def read(path):
    value = read_json(path)
    if not isinstance(value, dict):
        raise ValueError(f'saved record must be a JSON object: {path}')
    return value


def _saved_record(value, kind):
    """Accept historical read contracts without granting their old execution semantics."""
    allowed = {1, 2, 3} if kind == 'experiment' else {1, 2}
    if not isinstance(value, dict) or value.get('kind') != 'factory26.exp.' + kind or value.get('schema_version') not in allowed:
        raise ValueError('unsupported saved ' + kind + ' record')
    return value


def validate_target(value):
    if not isinstance(value, dict) or set(value) != {'case', 'variant'} or any(
            not isinstance(item, str) or not item.strip() for item in value.values()):
        raise ValueError('job target must explicitly declare nonempty case and variant strings')
    return value


def target(job, jobs):
    """Use declared comparison conditions, or an explicit generation relation."""
    if job.get('target'):
        return validate_target(job['target'])
    sources = {binding['from_job'] for binding in job.get('inputs', {}).values()
               if 'from_job' in binding}
    if len(sources) == 1:
        source = jobs.get(next(iter(sources)), {})
        return validate_target(source['target']) if source.get('target') else {'job_id': source.get('id', job['id'])}
    return {'job_id': job['id']}


def evidence(path, value, producer):
    return {'path': str(path), 'producer': producer,
            'observed_at': value.get('live_observed_at', value.get('observed_at',
                           value.get('exported_at', value.get('created_at'))))}


def _time(value):
    return max((value.get(name) or 0 for name in
                ('live_observed_at', 'observed_at', 'exported_at', 'created_at')), default=0)


def _producer_record(root, manifest, name=None):
    contents = manifest['contents']
    path = root / 'payload' if name is None else root / 'payload' / name
    expected = contents.get('sha256') if name is None else next(
        (row.get('sha256') for row in contents.get('entries', [])
         if row['path'] == name and row['type'] == 'file'), None)
    if path.is_symlink() or not expected or digest(path) != expected:
        raise ValueError('producer record differs from published artifact contents: ' + str(path))
    return read(path)


def provider_facts(directory, attempt, observed):
    """Decode one referenced saved observation; never collect or classify again."""
    pointer = observed.get('workspace_observation')
    if not pointer:
        return {'status': 'unknown', 'reason': '缺少当前 attempt 的已保存 provider 观察'}
    result = {'status': 'unknown', 'producer': 'exp.hosted.workspace_observation'}
    try:
        source = Path(pointer['source'])
        result['source'] = str(source)
        if source.is_symlink() or not source.resolve(strict=True).is_relative_to(Path(directory).resolve(strict=True)):
            raise ValueError('provider observation is outside its attempt evidence')
        saved = read(source)
        expected = {'attempt_id': attempt['attempt_id'], 'incarnation_id': observed.get('incarnation_id'),
                    'run_id': observed.get('run_id'), 'submission_id': observed.get('submission_id')}
        if not expected['incarnation_id'] or any(saved.get(key) != value for key, value in expected.items() if value is not None):
            raise ValueError('provider observation attempt/incarnation/platform identity differs')
        provider = saved['provider']
        sessions = []
        for row in provider.get('sessions', []):
            native = row.get('native') or {}
            retained = native.get('retained_evidence') or {}
            sessions.append({**{key: row.get(key) for key in ('session_id', 'provider_session_id', 'lifecycle',
                'classification', 'current_attempt', 'last_activity_at', 'unchanged_since', 'unchanged_samples',
                'unchanged_seconds', 'reason', 'tool_liveness')},
                'error': (row.get('turn') or {}).get('error'),
                'native': {'path': native.get('path'), 'available': native.get('available'),
                           'coverage': retained.get('coverage'), 'complete_native': retained.get('complete_native'),
                           'parse_errors': native.get('parse_errors', [])}})
        result.update(status=provider.get('classification', 'unknown'), identity=expected,
            observed_at=saved.get('observed_at'), provider_observed_at=provider.get('observed_at'),
            platform_status=saved.get('platform_status'), semantic_progress=provider.get('semantic_progress', 'unknown'),
            stale_after_seconds=provider.get('stale_after_seconds'), minimum_samples=provider.get('minimum_samples'),
            sessions=sessions, resource_wait_groups=provider.get('resource_wait_groups', []),
            provider_health=provider.get('provider_health', {}), group_errors=provider.get('group_errors', {}),
            errors=provider.get('errors', []), run_error=provider.get('run_error'),
            workspace_error=saved.get('workspace_error'), evidence_root=saved.get('evidence'))
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        result.update(reason='已保存 provider 观察不可采用', error=error(exc))
    return result


def artifact(store, reference, location=None, path='.'):
    """Bind metadata cheaply; consumption still verifies all payload bytes."""
    selected_member = path
    result = {'reference': reference, 'status': 'unavailable', 'member': selected_member}
    if location is not None:
        if location.get('reference') != reference or location.get('domain_identity', {}).get('kind') != 'docker':
            return {**result, 'error': {'message': 'saved asset location differs from producer reference'}}
        return {**result, 'status': 'published', 'location': location,
                'integrity': 'producer sealed location; domain revalidates retention and bytes on consumption'}
    try:
        root = store / identifier(reference['artifact_id'])
        path = root / 'manifest.json'
        result['evidence'] = evidence(path, {}, 'exp.artifacts')
        if root.is_symlink() or path.is_symlink() or (root / 'payload').is_symlink():
            raise ValueError('artifact metadata redirects through a link')
        if digest(path) != reference['manifest_sha256']:
            raise ValueError('artifact manifest differs from bound reference')
        manifest = require(read(path), 'artifact')
        if manifest['artifact_id'] != reference['artifact_id']:
            raise ValueError('artifact identity or local payload unavailable')
        from .artifacts import member_payload
        selected_payload = member_payload(store, reference, selected_member)
        result.update(status='published', type=manifest['type'],
                      payload=str(selected_payload), member=selected_member,
                      evidence=evidence(path, manifest, 'exp.artifacts'),
                      provenance=manifest.get('provenance', {}),
                      capabilities=manifest.get('capabilities', {}),
                      integrity='manifest-bound; payload verified again on consumption')
        # Only a public producer manifest can describe checkpoint completeness.
        harness = root / 'payload/harness-manifest.json'
        if harness.is_file() and not harness.is_symlink():
            declared = _producer_record(root, manifest, 'harness-manifest.json')
            if declared.get('kind') in ('factory26.harness.checkpoint', 'factory26.harness.prepared'):
                result['harness'] = {key: declared.get(key) for key in
                                     ('kind', 'schema_version', 'status', 'checkpoint_id', 'prepared_id', 'source_identity')}
                result['harness']['evidence'] = str(harness)
                result['harness']['gaps'] = declared.get('readback', {}).get('gaps', [])
        if manifest['type'] == 'stop-evidence':
            stop = require(_producer_record(root, manifest, 'manifest.json' if (root / 'payload').is_dir() else None), 'stop-evidence')
            result['stop'] = {key: stop.get(key) for key in
                              ('kind', 'schema_version', 'effect', 'source_identity', 'captured_at')}
    except (OSError, ValueError, KeyError, TypeError) as exc:
        result.update(status='unavailable', error=error(exc))
    return result


def attempt(path, store):
    saved = _saved_record(read(path / 'attempt.json'), 'attempt')
    if path.name != saved['attempt_id'] or saved['job_id'] != saved['job']['id']:
        raise ValueError('attempt directory or job differs from its saved identity')
    binding_path = path / 'binding.json'
    binding = require(read(binding_path), 'binding') if binding_path.exists() else {}
    if binding and binding.get('attempt_id') != saved['attempt_id']:
        raise ValueError('runner binding belongs to a different attempt')
    observations, failures = [], []
    for name in ('execution.json', 'remote-execution.json', 'observation.json', 'dispatch-observation.json'):
        location = path / name
        if not location.exists():
            continue
        try:
            value = read(location)
            if value.get('attempt_id') not in (None, saved['attempt_id']):
                raise ValueError('saved observation belongs to a different attempt')
            if binding and value.get('incarnation_id') not in (None, binding['incarnation_id']):
                raise ValueError('saved observation belongs to a different incarnation')
            observations.append((location, value))
        except (OSError, ValueError, TypeError) as exc:
            failures.append({'component': 'identity', 'evidence': str(location), 'error': error(exc)})
    # A controller observation error is not a replacement for runner facts.
    facts = [(p, v) for p, v in observations if 'execution' in v or 'backend' in v]
    selected = next(((p, v) for p, v in facts if p.name == 'execution.json'),
                    (path / 'attempt.json', {'phase': 'unaccepted'}))
    location, observed = selected
    row = {'attempt_id': saved['attempt_id'], 'job_id': saved['job_id'],
           'experiment_id': saved['experiment_id'],
           'purpose': saved['job']['purpose'], 'backend': saved['job']['backend']['kind'],
           'external_docker': bool(saved['job']['backend'].get('external_docker')),
           'source': str(path), 'created_at': saved['created_at'],
           'retry_of': saved.get('retry_of'), 'execution': observed,
           'retry_request_id': saved.get('retry_request_id'),
           'evidence': evidence(location, observed, 'exp.hosted' if saved['job']['backend']['kind'] == 'hosted' else 'exp.runner'),
           'errors': failures,
           'observations': [{'source': str(p), 'observed_at': _time(v),
                             'physical': v.get('physical'), 'runner_identity_state': v.get('runner_identity_state'),
                             'error': v.get('observation_error') or v.get('error')}
                            for p, v in observations if p.name != 'execution.json'],
           'input_bindings': saved.get('input_bindings', {}),
           'model_facts': {'desired': saved['job'].get('model_config', saved['job']['backend'].get('model_config')),
                           'bindings': saved['job'].get('environment', {}).get('FACTORY26_MODEL_BINDINGS'),
                           'runtime_selected': observed.get('model_facts', {}).get('runtime_selected', 'unknown'),
                           'observed': observed.get('model_facts', {}).get('observed', 'unknown')}}
    capacity_path = path / 'execution-capacity.json'
    if capacity_path.exists():
        try:
            capacity = require(read(capacity_path), 'execution-capacity')
            resource = read(path / 'resource.json')
            if capacity.get('attempt_id') != saved['attempt_id'] or capacity.get('resource') != resource:
                raise ValueError('capacity receipt belongs to another execution resource')
            row['capacity'] = {'status': 'released' if capacity.get('capacity_released') is True and capacity.get('status') == 'released' else 'unknown',
                               'evidence': evidence(capacity_path, capacity, 'exp.admission'),
                               'resource': resource}
        except (OSError, ValueError, KeyError) as exc:
            row['errors'].append({'component': 'identity', 'evidence': str(capacity_path), 'error': error(exc)})
    if row['backend'] == 'hosted':
        row['provider'] = provider_facts(path, saved, observed)
    for p, value in observations:
        if (value.get('error') and max(_time(value), value['error'].get('observed_at', 0)) >= _time(observed)) or value.get('observation_error'):
            row['errors'].append({'evidence': str(p), 'error': value.get('error') or value['observation_error']})
    for name in ('allocation-error.json', 'launch-gate.json', 'export.json', 'launch-error.json'):
        location = path / name
        if location.exists():
            try:
                row[name] = read(location)
                if name == 'export.json' and (row[name].get('source', {}).get('labels', {}).get('io.factory26.exp.attempt') != saved['attempt_id'] or
                        binding and row[name].get('source', {}).get('labels', {}).get('io.factory26.exp.incarnation') != binding['incarnation_id']):
                    del row[name]
                    raise ValueError('export source does not bind the attempt/incarnation')
            except (OSError, ValueError) as exc:
                row['errors'].append({'component': 'identity', 'evidence': str(location), 'error': error(exc)})
    # Failed transport stages remain diagnostic even when no export receipt exists.
    exported_at = row.get('export.json', {}).get('exported_at', 0)
    for location in sorted(path.glob('export-*/transport-error.json')):
        try:
            value = read(location)
            if value.get('observed_at', 0) > exported_at:
                row['errors'].append({'component': 'transport', 'evidence': str(location), 'error': value})
        except (OSError, ValueError) as exc:
            row['errors'].append({'component': 'transport', 'evidence': str(location), 'error': error(exc)})
    row['outputs'] = {name: artifact(store, ref, observed.get('output_locations', {}).get(name),
                                   path=observed.get('output_members', {}).get(name, '.'))
                      for name, ref in observed.get('artifacts', {}).items()}
    for name, output in row['outputs'].items():
        output['member'] = observed.get('output_members', {}).get(name, '.')
    row['workspace_snapshot'] = observed.get('workspace_snapshot')
    row['state_observations'] = []
    for state_path in sorted((path / 'state-observations').glob('*.json')):
        try:
            value = require(read(state_path), 'state-observation')
            state_binding, holder = value['binding'], value['holder']
            if (Path(state_binding['source_attempt_directory']).resolve() != path.resolve()
                    or state_binding['holder_id'] != holder['holder_id']
                    or state_binding['domain_identity'] != holder['domain_identity']):
                raise ValueError('state observation belongs to another attempt or holder')
            snapshot = holder.get('snapshot') or {}
            row['state_observations'].append({
                'holder_id': holder['holder_id'], 'domain_identity': holder['domain_identity'],
                'generation': holder['generation'], 'version': holder['version'], 'phase': holder['phase'],
                'writer': holder.get('writer'), 'capture': holder.get('capture'),
                'snapshot': {key: snapshot.get(key) for key in ('reference', 'member', 'generation')},
                'history': holder.get('history', []), 'coverage': holder.get('coverage', {}),
                'action': value['action'], 'observed_at': value['observed_at'],
                'observation_source': value['observation_source'], 'source': str(state_path)})
        except (OSError, ValueError, KeyError, TypeError) as exc:
            row['errors'].append({'component': 'state', 'evidence': str(state_path), 'error': error(exc)})
    row['inputs'] = {name: artifact(store, ref, saved['job'].get('input_locations', {}).get(name),
                                  path=saved['job'].get('input_members', {}).get(name, '.'))
                     for name, ref in saved['job'].get('inputs', {}).items()
                     if 'from_job' not in ref}
    for name, item in row['inputs'].items():
        item['member'] = saved['job'].get('input_members', {}).get(name, '.')
    archived = observed.get('archive')
    if isinstance(archived, dict) and archived.get('artifact'):
        row['outputs']['terminal_archive'] = artifact(store, archived['artifact'])
    # Read only public collector receipts; no private SQL or receiver polling.
    row['telemetry_sources'] = observed.get('telemetry_sources', [])
    for source in row['telemetry_sources']:
        if source.get('snapshot', {}).get('attempt_id') not in (None, saved['attempt_id']):
            row['errors'].append({'component': 'identity', 'evidence': row['evidence']['path'],
                                  'error': {'message': 'telemetry snapshot belongs to a different attempt'}})
    if row['backend'] == 'hosted' and observed.get('run_id'):
        platform = []
        for location in (path / 'platform').glob('observation-*.json'):
            try:
                value = require(read(location), 'platform-observation')
                if value.get('endpoint') != '/runs/' + observed['run_id']:
                    continue
                if value['value'].get('id') != observed['run_id']:
                    raise ValueError('platform GET record does not bind the saved run')
                platform.append((location, value))
            except (OSError, ValueError, KeyError, TypeError) as exc:
                row['errors'].append({'component': 'platform', 'evidence': str(location), 'error': error(exc)})
        if platform:
            location, value = max(platform, key=lambda item: _time(item[1]))
            row['platform_observation'] = {'value': value['value'], 'evidence': evidence(location, value, 'ARC GET')}
    return row


def facts(directory, read_at):
    """Keep old status fields available while adding independently bound facts."""
    result = record('status', directory=str(directory), read_at=read_at,
                    experiments=[], attempts=[], blockers=[])
    try:
        manifest = _saved_record(read(directory / 'experiment.json'), 'experiment')
        result.update(experiment_id=manifest['experiment_id'], jobs=manifest['jobs'],
                      recipe_schema_version=manifest['schema_version'],
                      execution_contract=manifest.get('execution_contract', 'legacy-scheduler'),
                      labels=manifest.get('labels', {}), frozen=True,
                      recipe_sha256=manifest['recipe_sha256'], definition=manifest.get('definition'),
                      budget=manifest['budget'], max_parallel=manifest['max_parallel'])
    except (OSError, ValueError, KeyError) as exc:
        result.update(frozen=False, build_error=error(exc))
        for name in ('build-intent.json', 'build-error.json'):
            path = directory / name
            if path.exists():
                try:
                    result[name] = read(path)
                except (OSError, ValueError) as failure:
                    result[name] = {'error': error(failure)}
        return result
    owner = directory / 'controller.json'
    if owner.exists():
        try:
            result['controller'] = require(read(owner), 'controller')
        except (OSError, ValueError) as exc:
            result['controller'] = {'phase': 'unknown', 'error': error(exc)}
    store = directory / 'artifacts'
    for path in (directory / 'attempts').glob('*'):
        try:
            row = attempt(path, store)
            job = next((job for job in manifest['jobs'] if job['id'] == row['job_id']), None)
            if not job or row['experiment_id'] != manifest['experiment_id'] or row['purpose'] != job['purpose'] or row['backend'] != job['backend']['kind']:
                raise ValueError('attempt identity is outside the frozen experiment')
            result['attempts'].append(row)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            result['attempts'].append({'source': str(path), 'error': error(exc)})
    result['attempts'].sort(key=lambda row: (row.get('created_at', 0), row.get('attempt_id', '')))
    result['inputs'] = {job['id']: {name: artifact(store, ref, job.get('input_locations', {}).get(name),
                                                   path=job.get('input_members', {}).get(name, '.'))
                                  for name, ref in job.get('inputs', {}).items()
                                  if 'from_job' not in ref} for job in manifest['jobs']}
    consumed = {row.get('retry_request_id') for row in result['attempts'] if 'attempt_id' in row}
    result['pending_retries'] = []
    for path in (directory / 'retries').glob('*.json'):
        try:
            value = require(read(path), 'retry')
            if value['request_id'] not in consumed:
                result['pending_retries'].append({'request_id': value['request_id'],
                                                   'source_attempt': value['source_attempt'], 'evidence': str(path)})
        except (OSError, ValueError, KeyError) as exc:
            result['blockers'].append({'component': 'retry', 'reason': '重试预约记录不可读',
                                       'evidence': str(path), 'error': error(exc)})
    return result


def _facet(status, row, **details):
    return {'status': status, 'evidence': row.get('evidence'), **details}


def stages(value, action_policy):
    """Pure stage projection over saved facts and controller-owned action policy."""
    jobs = {job['id']: job for job in value.get('jobs', [])}
    current = {row['job_id']: row for row in value['attempts'] if 'job_id' in row}
    groups = {}
    for job in jobs.values():
        row = current.get(job['id'])
        observation = row['execution'] if row else {}
        phase = observation.get('phase', observation.get('execution', 'unaccepted'))
        stage = {'job_id': job['id'], 'purpose': job['purpose'], 'status': phase if row else 'not-requested',
                 'attempt_id': row['attempt_id'] if row else None, 'blockers': [], 'facts': {},
                 'inputs': dict(row['inputs'] if row else value.get('inputs', {}).get(job['id'], {})),
                 'outputs': row.get('outputs', {}) if row else {},
                 'history': [{'attempt_id': previous['attempt_id'], 'retry_of': previous.get('retry_of'),
                              'source': previous['source'], 'phase': previous['execution'].get('phase', previous['execution'].get('execution'))}
                             for previous in value['attempts'] if previous.get('job_id') == job['id']]}
        for name, binding in job.get('inputs', {}).items():
            if 'from_job' not in binding:
                continue
            if row and name in row['inputs']:
                # An allocated evaluation already froze its input. A later
                # generation retry must not retroactively rebind that attempt.
                stage['inputs'][name] = dict(row['inputs'][name], from_job=binding['from_job'],
                                             output=binding['output'], bound_to_attempt=row['attempt_id'])
                continue
            stage['blockers'].append({'component': 'input', 'input': name,
                'from_job': binding['from_job'], 'output': binding['output'],
                'operation': 'start', 'reason': '尚未显式选择来源attempt/output或不可变artifact成员'})
        for name, item in stage['inputs'].items():
            if item['status'] != 'published':
                stage['blockers'].append({'component': 'input', 'input': name, 'reason': '冻结输入缺少可消费位置', 'evidence': item.get('evidence'), 'error': item.get('error')})
        if row:
            entry_code = observation.get('entry_exit_code', observation.get('exit_code'))
            if row['backend'] == 'hosted':
                main = 'unknown'
            else:
                main = ('succeeded' if entry_code == 0 else 'failed') if type(entry_code) is int else 'unknown'
            stage['facts']['main'] = _facet(main, row, exit_code=entry_code)
            stage['facts']['execution'] = _facet(phase, row, incarnation_id=observation.get('incarnation_id'),
                                                physical=observation.get('physical'), gap=observation.get('execution_observation_gap'))
            if row.get('capacity'):
                stage['facts']['capacity'] = row['capacity']
            if row.get('external_docker'):
                children = [fact for fact in observation.get('external_resources', [])
                            if fact.get('resource', {}).get('role') == 'execution']
                states = [fact.get('observation', {}).get('state', {}).get('Status', 'unknown') for fact in children]
                stage['facts']['child_execution'] = _facet(', '.join(states) if states else 'unknown', row,
                    resources=children, reason=None if children else
                    '当前只有外层 supervisor 事实；缺少实际子容器出生/状态，不证明模型已启动')
            stage['facts']['services'] = _facet('failed' if phase == 'readiness_failed' else
                'ready' if observation.get('ready') else 'unknown', row,
                entry_status=observation.get('entry_status', 'unknown'), services=observation.get('services', {}))
            if row.get('state_observations'):
                stage['facts']['state'] = _facet('saved', row, holders=row['state_observations'])
            if row.get('provider'):
                stage['facts']['provider'] = row['provider']
            archive = observation.get('archive', 'unknown')
            stage['facts']['archive'] = _facet(archive.get('status', 'unknown') if isinstance(archive, dict) else archive, row)
            if row['backend'] == 'docker':
                exported = row.get('export.json', {})
                stage['facts']['export'] = {'status': exported.get('status', 'failed' if any(e.get('component') == 'transport' for e in row['errors']) else 'unknown'),
                                            'evidence': evidence(Path(row['source']) / 'export.json', exported, 'exp.docker-transport') if exported else None}
            seal = observation.get('collector_seal')
            stage['facts']['telemetry'] = _facet('sealed' if seal else observation.get('telemetry', 'unknown'), row,
                                                producer_flush=seal.get('producer_flush', 'unknown') if seal else 'unknown',
                                                sources=row.get('telemetry_sources', []))
            if job['purpose'] == 'generate':
                for component in ('braid', 'console'):
                    stage['facts'][component] = {'status': 'unknown', 'reason': '没有绑定此 attempt 的公开接入观察回执'}
            if row['backend'] == 'hosted':
                remote = row.get('platform_observation', {})
                stage['facts']['platform'] = {'status': remote.get('value', {}).get('status', 'unknown'),
                    'evidence': remote.get('evidence'), 'run_id': observation.get('run_id'),
                    'submission_id': observation.get('submission_id'), 'result': remote.get('value'),
                    'observation_error': observation.get('observation_error')}
            for failure in row['errors']:
                stage['blockers'].append({'component': failure.get('component', 'observation'),
                                           'reason': failure['error'].get('message', '保存的观察错误'), **failure})
            for name in ('allocation-error.json', 'launch-error.json'):
                if row.get(name):
                    stage['blockers'].append({'component': 'allocation' if name.startswith('allocation') else 'dispatch',
                                               'reason': row[name].get('message', '入口前置条件未满足'),
                                               'error': row[name], 'evidence': str(Path(row['source']) / name)})
            for field in ('archive_error', 'collector_error', 'observation_error', 'stop_error'):
                if observation.get(field):
                    stage['blockers'].append({'component': field.removesuffix('_error'), 'reason': observation[field].get('message', field),
                                               'error': observation[field], 'evidence': row['evidence']})
            if main == 'failed':
                stage['status'] = 'failed'
                stage['blockers'].append({'component': 'main', 'reason': f'入口退出码 {entry_code}', 'evidence': row['evidence']})
            for name in ('error', 'execution_observation_gap'):
                if observation.get(name) and not stage['blockers']:
                    issue = observation[name]
                    stage['blockers'].append({'component': 'execution', 'reason': issue.get('message', str(issue)) if isinstance(issue, dict) else issue, 'evidence': row['evidence']})
            for output in job.get('outputs', []):
                published = stage['outputs'].get(output['name'])
                if phase in ('exited', 'stopped', 'failed', 'unknown') and (not published or published['status'] != 'published'):
                    stage['blockers'].append({'component': 'artifact', 'reason': '声明输出尚未封口发布：' + output['name'],
                                               'evidence': row['evidence'], 'error': published.get('error') if published else None})
            for name, published in stage['outputs'].items():
                if published.get('harness', {}).get('status') == 'partial':
                    stage['blockers'].append({'component': 'harness', 'reason': '生产者声明 partial，不能作为完整 prepared 消费：' + name,
                                               'evidence': published['harness']['evidence'], 'gaps': published['harness']['gaps']})
        if not row and stage['blockers']:
            stage['status'] = 'not-requested'
        stage['next_actions'] = action_policy(job, row, stage, value)
        if not row and not stage['blockers'] and not stage['next_actions']:
            stage['blockers'].append({'component': 'input', 'reason': '尚未明确请求运行；没有后台派发'})
        grouping = target(job, jobs)
        key = tuple(sorted(grouping.items()))
        groups.setdefault(key, {'target': grouping, 'stages': []})['stages'].append(stage)
        value['blockers'].extend(dict(issue, job_id=job['id']) for issue in stage['blockers'])
    value['targets'] = list(groups.values())
    return public(value)


def _stamp(value):
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, timezone.utc).isoformat(timespec='seconds')
    return '未知时点'


def _reason(value):
    """Keep the concrete beginning and failure tail; JSON retains the full error."""
    text = ' '.join(str(value).split())
    return text if len(text) <= 300 else text[:120] + ' … ' + text[-160:]


def _resource_details(value):
    """Render saved resource measurements without truncating their numeric fields."""
    if isinstance(value, dict):
        candidate = value
        if not any(key in candidate for key in ('memory_current', 'memory_max', 'accounted_for_admission')):
            value = candidate.get('message') or candidate.get('error') or candidate.get('detail')
            return _resource_details(value) if value is not None else []
    elif isinstance(value, str):
        offset = value.find('{')
        if offset < 0:
            return []
        try:
            candidate, _ = json.JSONDecoder().raw_decode(value[offset:])
        except ValueError:
            return []
        if not isinstance(candidate, dict) or not any(key in candidate for key in ('memory_current', 'memory_max', 'accounted_for_admission')):
            return []
    else:
        return []
    return [key + '=' + json.dumps(item, ensure_ascii=False, sort_keys=True)
            for key, item in candidate.items()]


def render(value):
    if value.get('kind') == 'factory26.exp.status-index':
        return '\n\n'.join(render(row) for row in value['experiments'])
    lines = [value.get('experiment_id', value.get('directory', value.get('source', '?')))]
    root = Path(value['directory']) if value.get('directory') else None
    def short_path(path, base=None):
        if not path:
            return '缺少入口'
        try:
            return str(Path(path).relative_to(Path(base) if base else root))
        except (ValueError, TypeError):
            return str(path)
    if root:
        lines.append('记录目录：' + str(root))
    if not value.get('frozen'):
        failure = value.get('build-error.json', value.get('build_error', value.get('error', {})))
        lines.append('└─ build 未就绪：' + _reason(failure.get('message', str(failure))))
        lines.append('   证据：' + str(Path(value.get('directory', '.')) / 'build-error.json'))
        return '\n'.join(lines)
    owner = value.get('controller', {})
    if owner:
        lines.append(f"历史controller: {owner.get('phase', 'unknown')} / physical: {owner.get('physical_state', 'unknown')}")
    elif value.get('execution_contract') == 'explicit-request-v1':
        lines.append('执行：显式请求；无后台调度')
    if owner.get('error'):
        lines.append('controller 错误：' + _reason(owner['error'].get('message', str(owner['error']))))
    for group in value.get('targets', []):
        label = group['target']
        lines.append('├─ ' + (' / '.join(label[k] for k in ('case', 'variant')) if 'case' in label else label['job_id']))
        for stage in group['stages']:
            lines.append(f"│  ├─ {stage['purpose']}  {stage['status']}  {stage.get('attempt_id') or '尚未派发'}")
            for name, fact in stage['facts'].items():
                extra = ''
                if name == 'main' and fact.get('exit_code') is not None:
                    extra = f" (exit {fact['exit_code']})"
                if name == 'platform':
                    extra = f" (run {fact.get('run_id') or '?'})"
                if name == 'telemetry':
                    extra = f" (producer flush: {fact['producer_flush']})"
                lines.append(f"│  │  {name}: {fact['status']}{extra}")
                if fact.get('reason'):
                    lines.append('│  │    缺口：' + fact['reason'])
                if name == 'state':
                    for holder in fact['holders']:
                        writer = holder.get('writer') or {}
                        capture = holder.get('capture') or {}
                        lines.append(f"│  │    holder {holder['holder_id']}: {holder['phase']} / generation={holder['generation']} / version={holder['version']}")
                        lines.append(f"│  │      writer: {writer.get('resource_id', 'none')} / incarnation: {writer.get('incarnation', 'none')} / capture: {capture.get('owner', 'none')}")
                        snapshot = holder['snapshot']
                        if snapshot.get('reference'):
                            lines.append(f"│  │      snapshot: {snapshot['reference']['artifact_id']} / member: {snapshot.get('member', '.')}")
                        lines.append(f"│  │      保存的 {holder['action']} 回执：{_stamp(holder['observed_at'])} / {holder['source']}")
                if name == 'provider':
                    lines.append(f"│  │    semantic_progress: {fact.get('semantic_progress', 'unknown')} / 平台: {fact.get('platform_status', 'unknown')}")
                    lines.append(f"│  │    producer: {fact.get('producer', 'unknown')} / 观察: {_stamp(fact.get('observed_at'))}")
                    if fact.get('source'):
                        lines.append('│  │    状态摘要原件：' + short_path(fact['source']))
                    if fact.get('evidence_root'):
                        lines.append('│  │    定向取证目录：' + short_path(fact['evidence_root']))
                    lines.append(f"│  │    stale 阈值: {fact.get('stale_after_seconds', '?')}s / 最少样本: {fact.get('minimum_samples', '?')}")
                    for session in fact.get('sessions', []):
                        lines.append(f"│  │    session {session['session_id']}: {session['classification']} / lifecycle={session['lifecycle']} / current_attempt={session['current_attempt']} / 连续{session['unchanged_samples']}次、{session['unchanged_seconds']}s")
                        for detail in (session.get('reason'), session.get('error')):
                            if detail:
                                lines.append('│  │      原因：' + _reason(str(detail)))
                        native = session['native']
                        lines.append(f"│  │      native: {native['coverage']} / complete={native['complete_native']} / {short_path(native['path'], fact.get('evidence_root'))}")
                    for group in fact.get('resource_wait_groups', []):
                        health = fact.get('provider_health', {}).get(group, {})
                        detail = health.get('error') or fact.get('group_errors', {}).get(group) or '原因 unknown'
                        lines.append('│  │    resource_wait ' + group + ':')
                        structured = _resource_details(detail)
                        for item in structured or [_reason(str(detail))]:
                            lines.append('│  │      ' + item)
                    for detail in (fact.get('error'), fact.get('run_error'), fact.get('workspace_error'), *fact.get('errors', []), *fact.get('group_errors', {}).values()):
                        if detail:
                            lines.append('│  │    原始错误：' + _reason(str(detail)))
                if name == 'platform':
                    observed = fact.get('evidence') or {}
                    lines.append(f"│  │    GET 观察：{_stamp(observed.get('observed_at'))} / {short_path(observed.get('path'))}")
                    result = fact.get('result') or {}
                    if result.get('score') is not None:
                        lines.append('│  │    score: ' + str(result['score']))
            for name, output in stage['outputs'].items():
                declared = output.get('harness', {})
                scope = f" / Harness 声明 {declared['status']}" if declared else ''
                lines.append(f"│  │  artifact {name}: {output['status']} / {output['reference']['artifact_id']}{scope}")
                if output.get('payload'):
                    lines.append('│  │    内容成员：' + short_path(output['payload']))
                if output.get('error'):
                    lines.append('│  │    原错：' + _reason(output['error']['message']))
                if declared.get('gaps'):
                    lines.append('│  │    缺口：' + str(declared['gaps']))
            for blocker in stage['blockers']:
                relation = f" [{blocker['from_job']} → {blocker['output']}]" if blocker.get('from_job') else ''
                lines.append(f"│  │  blocked by {blocker['component']}: {_reason(blocker['reason'])}{relation}")
                source = blocker.get('evidence')
                if source:
                    lines.append('│  │    问题原件：' + short_path(source['path'] if isinstance(source, dict) else source))
            for action in stage['next_actions']:
                lines.append(f"│  │  next: {action['label']}")
                if action.get('argv'):
                    lines.append('│  │    ' + shlex.join(action['argv']))
                for condition in action.get('requires', []):
                    lines.append('│  │    条件：' + condition)
            if stage.get('attempt_id'):
                row = next(row for row in value['attempts'] if row.get('attempt_id') == stage['attempt_id'])
                lines.append(f"│  │  观察：{_stamp(row['evidence']['observed_at'])} / {short_path(row['evidence']['path'])}")
            if len(stage['history']) > 1:
                lines.append('│  │  历史：' + ', '.join(item['attempt_id'] +
                             (f" (retry_of {item['retry_of']})" if item['retry_of'] else '') for item in stage['history']))
    for row in value['attempts']:
        if row.get('error'):
            lines.append(f"记录不可读：{row['source']} / {row['error']['message']}")
    lines.append('保存的事实投影；本次读取时间不代表远端新鲜度。操作执行时重新核验。')
    return '\n'.join(lines)
