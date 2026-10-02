"""Read saved producer facts into an experiment view, without observing resources.

The view does not authorize execution. Commands supplied by the controller must
revalidate ownership, inputs and physical state when invoked.
"""
from datetime import datetime, timezone
from pathlib import Path
import shlex

from .core import digest, error, identifier, public, read as read_json, record, require


def read(path):
    value = read_json(path)
    if not isinstance(value, dict):
        raise ValueError(f'saved record must be a JSON object: {path}')
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


def artifact(store, reference):
    """Bind metadata cheaply; consumption still verifies all payload bytes."""
    result = {'reference': reference, 'status': 'unavailable'}
    try:
        root = store / identifier(reference['artifact_id'])
        path = root / 'manifest.json'
        result['evidence'] = evidence(path, {}, 'exp.artifacts')
        if root.is_symlink() or path.is_symlink() or (root / 'payload').is_symlink():
            raise ValueError('artifact metadata redirects through a link')
        if digest(path) != reference['manifest_sha256']:
            raise ValueError('artifact manifest differs from bound reference')
        manifest = require(read(path), 'artifact')
        if manifest['artifact_id'] != reference['artifact_id'] or not (root / 'payload').exists():
            raise ValueError('artifact identity or local payload unavailable')
        result.update(status='published', type=manifest['type'],
                      payload=str(root / 'payload'),
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
    saved = require(read(path / 'attempt.json'), 'attempt')
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
    selected = max(facts or observations, key=lambda row: _time(row[1]), default=(path / 'attempt.json', {'phase': 'unaccepted'}))
    location, observed = selected
    row = {'attempt_id': saved['attempt_id'], 'job_id': saved['job_id'],
           'experiment_id': saved['experiment_id'],
           'purpose': saved['job']['purpose'], 'backend': saved['job']['backend']['kind'],
           'source': str(path), 'created_at': saved['created_at'],
           'retry_of': saved.get('retry_of'), 'execution': observed,
           'retry_request_id': saved.get('retry_request_id'),
           'evidence': evidence(location, observed, 'exp.hosted' if saved['job']['backend']['kind'] == 'hosted' else 'exp.runner'),
           'errors': failures,
           'model_facts': {'desired': saved['job'].get('model_config', saved['job']['backend'].get('model_config')),
                           'bindings': saved['job'].get('environment', {}).get('FACTORY26_MODEL_BINDINGS'),
                           'runtime_selected': observed.get('model_facts', {}).get('runtime_selected', 'unknown'),
                           'observed': observed.get('model_facts', {}).get('observed', 'unknown')}}
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
    row['outputs'] = {name: artifact(store, ref) for name, ref in observed.get('artifacts', {}).items()}
    row['inputs'] = {name: artifact(store, ref) for name, ref in saved['job'].get('inputs', {}).items()
                     if 'from_job' not in ref}
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
        manifest = require(read(directory / 'experiment.json'), 'experiment')
        result.update(experiment_id=manifest['experiment_id'], jobs=manifest['jobs'],
                      labels=manifest.get('labels', {}), frozen=True,
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
    result['inputs'] = {job['id']: {name: artifact(store, ref) for name, ref in job.get('inputs', {}).items()
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
        stage = {'job_id': job['id'], 'purpose': job['purpose'], 'status': phase if row else 'waiting',
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
            producer = current.get(binding['from_job'])
            produced = producer['execution'] if producer else {}
            output = producer.get('outputs', {}).get(binding['output']) if producer else None
            dependency = {'component': 'input', 'input': name, 'from_job': binding['from_job'], 'output': binding['output']}
            if not producer:
                dependency['reason'] = '等待生成 attempt 发布制品'
            elif produced.get('phase', produced.get('execution')) not in ('exited', 'stopped', 'failed'):
                dependency['reason'] = '生成执行终态尚未确认'
            elif produced.get('archive') == 'pending':
                dependency['reason'] = '等待生成证据收尾'
            elif produced.get('exit_code') != 0:
                dependency['reason'] = '生成入口未确认成功，不能派发评价'
            elif not output or output['status'] != 'published':
                dependency['reason'] = '生成制品尚未在本地发布或输运'
            else:
                stage['inputs'][name] = dict(output, from_job=binding['from_job'], output=binding['output'])
                continue
            if producer:
                dependency.update(attempt_id=producer['attempt_id'], evidence=producer['evidence'])
            stage['blockers'].append(dependency)
        for name, item in stage['inputs'].items():
            if item['status'] != 'published':
                stage['blockers'].append({'component': 'input', 'input': name, 'reason': '冻结输入在本地不可读', 'evidence': item.get('evidence'), 'error': item.get('error')})
        owner = value.get('controller', {})
        if (not row or phase not in ('exited', 'stopped', 'failed')) and owner.get('error'):
            stage['blockers'].append({'component': 'controller', 'reason': owner['error'].get('message', 'controller 故障'),
                                       'error': owner['error'], 'evidence': str(Path(value['directory']) / 'controller.json')})
        if (not row or phase not in ('exited', 'stopped', 'failed')) and owner.get('phase') == 'running' and owner.get('physical_state') != 'alive':
            stage['blockers'].append({'component': 'controller', 'reason': '保存的 controller 运行状态没有当前出生身份支持',
                                       'evidence': str(Path(value['directory']) / 'controller.json')})
        if row:
            entry_code = observation.get('entry_exit_code', observation.get('exit_code'))
            if row['backend'] == 'hosted':
                main = 'unknown'
            else:
                main = ('succeeded' if entry_code == 0 else 'failed') if type(entry_code) is int else 'unknown'
            stage['facts']['main'] = _facet(main, row, exit_code=entry_code)
            stage['facts']['execution'] = _facet(phase, row, incarnation_id=observation.get('incarnation_id'),
                                                physical=observation.get('physical'), gap=observation.get('execution_observation_gap'))
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
                    stage['blockers'].append({'component': 'artifact', 'reason': '声明输出尚未在本地发布：' + output['name'],
                                               'evidence': row['evidence'], 'error': published.get('error') if published else None})
            for name, published in stage['outputs'].items():
                if published.get('harness', {}).get('status') == 'partial':
                    stage['blockers'].append({'component': 'harness', 'reason': '生产者声明 partial，不能作为完整 prepared 消费：' + name,
                                               'evidence': published['harness']['evidence'], 'gaps': published['harness']['gaps']})
        if not row and stage['blockers']:
            stage['status'] = 'waiting'
        stage['next_actions'] = action_policy(job, row, stage, value)
        if row and phase in ('exited', 'stopped', 'failed') and stage['blockers'] and stage['status'] != 'failed':
            stage['status'] = 'blocked'
        if not row and not stage['blockers'] and not stage['next_actions']:
            stage['blockers'].append({'component': 'controller', 'reason': '等待 controller 派发；启动时仍需核对预算、资源及输入'})
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


def render(value):
    if value.get('kind') == 'factory26.exp.status-index':
        return '\n\n'.join(render(row) for row in value['experiments'])
    lines = [value.get('experiment_id', value.get('directory', value.get('source', '?')))]
    if not value.get('frozen'):
        failure = value.get('build-error.json', value.get('build_error', value.get('error', {})))
        lines.append('└─ build 未就绪：' + _reason(failure.get('message', str(failure))))
        lines.append('   证据：' + str(Path(value.get('directory', '.')) / 'build-error.json'))
        return '\n'.join(lines)
    owner = value.get('controller', {})
    lines.append(f"controller: {owner.get('phase', '未启动')} / physical: {owner.get('physical_state', 'unknown')}")
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
                if name == 'platform':
                    observed = fact.get('evidence') or {}
                    lines.append(f"│  │    GET 观察：{_stamp(observed.get('observed_at'))} / {observed.get('path', '缺少对应 run 原件')}")
                    result = fact.get('result') or {}
                    if result.get('score') is not None:
                        lines.append('│  │    score: ' + str(result['score']))
            for name, output in stage['outputs'].items():
                declared = output.get('harness', {})
                scope = f" / Harness 声明 {declared['status']}" if declared else ''
                lines.append(f"│  │  artifact {name}: {output['status']} / {output['reference']['artifact_id']}{scope}")
                if output.get('payload'):
                    lines.append('│  │    内容：' + output['payload'])
                if output.get('error'):
                    lines.append('│  │    原错：' + _reason(output['error']['message']))
                if declared.get('gaps'):
                    lines.append('│  │    缺口：' + str(declared['gaps']))
            for blocker in stage['blockers']:
                relation = f" [{blocker['from_job']} → {blocker['output']}]" if blocker.get('from_job') else ''
                lines.append(f"│  │  blocked by {blocker['component']}: {_reason(blocker['reason'])}{relation}")
                source = blocker.get('evidence')
                if source:
                    lines.append('│  │    证据：' + (source['path'] if isinstance(source, dict) else source))
            for action in stage['next_actions']:
                lines.append(f"│  │  next: {action['label']}")
                if action.get('argv'):
                    lines.append('│  │    ' + shlex.join(action['argv']))
                for condition in action.get('requires', []):
                    lines.append('│  │    条件：' + condition)
            if stage.get('attempt_id'):
                row = next(row for row in value['attempts'] if row.get('attempt_id') == stage['attempt_id'])
                lines.append(f"│  │  观察：{_stamp(row['evidence']['observed_at'])} / {row['evidence']['path']}")
            if len(stage['history']) > 1:
                lines.append('│  │  历史：' + ', '.join(item['attempt_id'] +
                             (f" (retry_of {item['retry_of']})" if item['retry_of'] else '') for item in stage['history']))
    for row in value['attempts']:
        if row.get('error'):
            lines.append(f"记录不可读：{row['source']} / {row['error']['message']}")
    lines.append('保存的事实投影；本次读取时间不代表远端新鲜度。操作执行时重新核验。')
    return '\n'.join(lines)
