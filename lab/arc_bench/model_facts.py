"""Project model evidence without credentials, prompts, or model requests."""
import hashlib
import json
from pathlib import Path
import re
import time
from urllib.parse import urlsplit, urlunsplit
import zipfile


def identity(path):
    path = Path(path)
    return {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def endpoint(value):
    if not value or value.startswith(('@', '$')):
        return None
    parsed = urlsplit(value)
    if parsed.scheme not in {'https', 'http'} or not parsed.hostname:
        return None
    host = parsed.hostname
    if ':' in host:
        host = '[' + host + ']'
    if parsed.port:
        host += ':' + str(parsed.port)
    # Query/userinfo can carry credentials. Only standard API paths are public.
    path = parsed.path if re.fullmatch(r'/(?:v\d+(?:/(?:openai|chat/completions|messages))?|compatible-mode/v\d+|api/(?:coding/)?paas/v\d+)/?', parsed.path) else ''
    return urlunsplit((parsed.scheme, host, path, '', ''))


def channel(url):
    return 'arc' if url and urlsplit(url).hostname == 'api.arc-bench.com' else 'unknown'


def auth_selector(value):
    match = re.fullmatch(r'\$([A-Z][A-Z0-9_]*)', value or '')
    return {'method': 'environment', 'environment': match[1]} if match else {
        'method': 'configured_literal' if value else 'unknown'}


def connection(provider):
    url = endpoint(provider.get('baseUrl'))
    return {'endpoint': url, 'channel': channel(url), 'api': provider.get('api'),
            'authentication': auth_selector(provider.get('apiKey')), 'credential_mode': 'unknown'}


def frontmatter(text):
    if not text.startswith('---\n'):
        return {}
    result = {}
    for line in text.split('---', 2)[1].splitlines():
        key, sep, value = line.partition(':')
        if sep and key in {'name', 'model', 'thinking'}:
            result[key] = value.strip().strip('\"\'')
    return result


def material_rows(profile, models, roles, root_id=None):
    providers = models.get('providers', {})
    name = profile['id']
    provider = profile.get('provider')
    rows = [{'scope': 'braid-root' if name == root_id else 'braid-member', 'profile_id': name,
             'model': profile.get('model'), 'provider_alias': provider, 'reasoning': profile.get('reasoning'),
             'adapter_version': profile.get('adapter_version'),
             **connection(providers.get(provider, {}))}]
    for role, text in roles.items():
        values = frontmatter(text)
        alias, sep, model = values.get('model', '').partition('/')
        rows.append({'scope': 'pi-subagent', 'profile_id': name, 'role': values.get('name', role),
                     'model': model if sep else alias or None, 'provider_alias': alias if sep else provider,
                     'reasoning': values.get('thinking'), **connection(providers.get(alias if sep else provider, {}))})
    for alias, definition in providers.items():
        if 'visual' in alias:
            for model in definition.get('models', []):
                rows.append({'scope': 'visual', 'profile_id': name, 'model': model['id'],
                             'provider_alias': alias, **connection(definition)})
    return rows


def e2e_row(text):
    model = re.search(r"\.chatModel\(['\"]([^'\"]+)['\"]\)", text)
    url = re.search(r"(?:baseURL|arcBaseURL)\s*[:=]\s*['\"]([^'\"]+)['\"]", text)
    return {'scope': 'e2e', 'model': model[1] if model else None, 'endpoint': endpoint(url[1]) if url else None,
            'credential_mode': 'unknown', 'evidence_level': 'static_config'}


def _runtime_snapshot(run):
    """Read only public fields at their producer, before crossing Docker/monitor boundaries."""
    run = Path(run)
    request_path = run / 'braid-state/request.json'
    if not request_path.exists():
        request_path = run / 'braid-request.json'
    if not request_path.exists():
        return {'status': 'unknown', 'reason': 'braid request unavailable', 'source': str(run)}
    request = json.loads(request_path.read_text())
    profiles = request.get('profiles', [])
    rows, sources, errors = [], [identity(request_path)], []
    for profile in profiles:
        binding = request.get('bindings', {}).get(profile['id'], {})
        template = Path(binding.get('native_template', run / 'missing-native-template'))
        try:
            path = template / 'models.json'
            models = json.loads(path.read_text())
            model_source = identity(path)
            sources.append(model_source)
            roles = {}
            for path in sorted((template / 'agents').glob('*.md')):
                roles[path.stem] = path.read_text()
                sources.append(identity(path))
            projected = material_rows(profile, models, roles, request.get('root_profile_id'))
            for row in projected:
                row.update(material='native-template', evidence_level='runtime_selected', source=model_source)
            rows.extend(projected)
            settings = template / 'settings.json'
            if settings.is_file():
                sources.append(identity(settings))
            homes = binding.get('native_home', {}).get('root')
            for path in sorted(Path(homes).glob(profile['id'] + '-*/models.json')) if homes else []:
                # A materialized Pi home can differ from its launch template.
                native = json.loads(path.read_text())
                sources.append(identity(path))
                for alias, definition in native.get('providers', {}).items():
                    rows.append({'scope': 'pi-native-provider', 'profile_id': profile['id'],
                                 'native_home': str(path.parent), 'provider_alias': alias,
                                 'models': [m['id'] for m in definition.get('models', [])],
                                 'material': 'native-home', 'evidence_level': 'runtime_selected', 'source': identity(path),
                                 **connection(definition)})
        except (OSError, ValueError, KeyError) as error:
            errors.append({'profile_id': profile['id'], 'type': type(error).__name__, 'reason': 'native material unreadable', 'errno': getattr(error, 'errno', None), 'source': str(template)})
    connection_path = run / 'model-connection.json'
    receipt = None
    if connection_path.is_file():
        raw = json.loads(connection_path.read_text())
        receipt = {'endpoint': endpoint(raw.get('base_url')), 'authentication': {
            'method': 'environment', 'environment': raw.get('api_key_environment'),
            'configured': raw.get('api_key_configured')},
            'remaining_supplier_auth_environment': raw.get('remaining_supplier_auth_environment'),
            'credential_mode': raw.get('credential_mode', 'unknown')}
        sources.append(identity(connection_path))
    recovery = []
    for name in ('recovery-attempt.json', 'recovery-native-transport.json', 'recovery-model-migration.json', 'recovery-provenance.json'):
        path = run / name
        if path.is_file():
            sources.append(identity(path))
            raw = json.loads(path.read_text())
            recovery.append({'source': identity(path), **{k: raw[k] for k in ('operation', 'applied_at', 'started_at') if k in raw}})
    impl = run / 'implementation-hashes.json'
    if impl.is_file():
        sources.append(identity(impl))
    observed = {}
    timing_parse_errors = []
    timing = run / 'pi-timing.jsonl'
    if timing.is_file():
        with timing.open() as stream:
            for line_number, line in enumerate(stream, 1):
                try:
                    value = json.loads(line)
                except json.JSONDecodeError as error:
                    if len(timing_parse_errors) < 5:
                        timing_parse_errors.append({'line': line_number, 'message': error.msg, 'column': error.colno, 'partial_append': not line.endswith('\n')})
                    continue
                if value.get('model') and value.get('provider'):
                    key = (value['provider'], value['model'], value.get('session_id'))
                    observed[key] = {k: value.get(k) for k in ('provider', 'model', 'session_id', 'session_file', 'at_ms', 'kind')}
        sources.append({'path': str(timing), 'bytes': timing.stat().st_size})
    # Tools are outside the Braid profiles; inspect their actual shipped config.
    for path in (Path('/workspace/submission/agent/tools/e2e.config.ts'), run / 'tools/e2e.config.ts'):
        if path.is_file():
            rows.append(e2e_row(path.read_text()))
            sources.append(identity(path))
    process_connections = []
    for proc in Path('/proc').glob('[0-9]*'):
        try:
            raw = dict(part.split(b'=', 1) for part in (proc / 'environ').read_bytes().split(b'\0') if b'=' in part)
            if raw.get(b'FACTORY26_PI_TIMING_FILE') != str(run / 'pi-timing.jsonl').encode():
                continue
            urls = {name: endpoint(raw[name.encode()].decode()) for name in ('FACTORY26_BASE_URL', 'OPENAI_BASE_URL', 'VISUAL_BASE_URL') if name.encode() in raw}
            process_connections.append({'pid': int(proc.name), 'process_start': (proc/'stat').read_text().rpartition(')')[2].split()[19],
                'endpoints': urls, 'authentication': {'method': 'environment', 'configured_variables': [name for name in ('FACTORY26_API_KEY', 'FACTORY26_VISUAL_API_KEY', 'OPENAI_API_KEY') if raw.get(name.encode())]},
                'credential_mode': 'unknown', 'evidence_level': 'process_environment'})
        except (OSError, ValueError, IndexError):
            continue  # Processes can exit between /proc reads; this is supplementary evidence.
    return {'status': 'observed', 'source': str(run), 'observed_at': time.time(), 'root_profile_id': request.get('root_profile_id'),
            'rows': rows, 'connection_receipt': receipt, 'observed_usage': list(observed.values()), 'timing_parse_errors': timing_parse_errors,
            'sources': sources, 'errors': errors, 'recovery': recovery, 'process_connections': process_connections,
            'limits': ['配置不证明模型已调用；timing 未覆盖的工具调用和账单费用模式未知。']}


def runtime_snapshot(run):
    try:
        return _runtime_snapshot(run)
    except (OSError, ValueError, KeyError, TypeError) as error:
        details = {'type': type(error).__name__, 'errno': getattr(error, 'errno', None)}
        if isinstance(error, json.JSONDecodeError):
            details.update(message=error.msg, line=error.lineno, column=error.colno)
        return {'status': 'unknown', 'source': str(run), 'rows': [], 'errors': [details]}


def environment_facts(path):
    values = {}
    for line in Path(path).read_text().splitlines():
        name, sep, value = line.strip().removeprefix('export ').partition('=')
        if sep and name in {'MODEL', 'VISUAL_MODEL', 'OPENAI_BASE_URL', 'FACTORY26_BASE_URL', 'VISUAL_BASE_URL'}:
            values[name] = value.strip().strip('\"\'')
    return {name: endpoint(value) if name.endswith('BASE_URL') else value for name, value in values.items()}


def _frozen_job(experiment, job):
    inputs = job['inputs']
    result = {'job_id': job['id'], 'rows': [], 'sources': [], 'environment': None, 'errors': []}
    paths = {name: experiment / 'inputs' / row['id'] / row['content'] if 'id' in row else experiment / row['path'] for name, row in inputs.items() if 'id' in row or 'path' in row}
    for name in ('agent', 'model_env'):
        if name in paths:
            result['sources'].append({**identity(paths[name]), 'expected_sha256': inputs[name]['sha256'], 'input': name})
    if 'model_env' in paths:
        result['environment'] = environment_facts(paths['model_env'])
    if 'agent' not in paths:
        result['errors'].append('frozen agent input unavailable')
        return result
    with zipfile.ZipFile(paths['agent']) as archive:
        names = set(archive.namelist())
        for name in sorted(names):
            if not re.fullmatch(r'(?:.*/)?agents/[^/]+/profile.json', name):
                continue
            folder = name.rsplit('/', 1)[0]
            profile = json.loads(archive.read(name))
            models = json.loads(archive.read(folder + '/models.json'))
            roles = {Path(p).stem: archive.read(p).decode() for p in sorted(names)
                     if p.startswith(folder + '/agents/') and p.endswith('.md')}
            result['rows'].extend(material_rows(profile, models, roles))
        for name in sorted(names):
            if name.endswith('/e2e.config.ts'):
                result['rows'].append(e2e_row(archive.read(name).decode()))
    return result


def frozen_job(experiment, job):
    try:
        return _frozen_job(experiment, job)
    except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile) as error:
        details = {'type': type(error).__name__, 'errno': getattr(error, 'errno', None),
                   'source': str(experiment), 'reason': '冻结模型材料不可读取'}
        if isinstance(error, json.JSONDecodeError):
            details.update(message=error.msg, line=error.lineno, column=error.colno)
        return {'job_id': job['id'], 'rows': [], 'sources': [], 'environment': None, 'errors': [details]}


def compare(frozen, actual, desired):
    drift = []
    for source in frozen.get('sources', []):
        if source.get('expected_sha256') != source['sha256']:
            drift.append({'kind': 'frozen_input_changed', 'source': source['path']})
    roots = [row for snapshot in actual for row in snapshot.get('rows', []) if row['scope'] == 'braid-root']
    expected = (frozen.get('environment') or {}).get('MODEL') or desired.get('root_model')
    for root in roots:
        if expected and expected != root['model']:
            drift.append({'kind': 'root_model', 'expected': expected, 'actual': root['model']})
    by_key = {(row.get('profile_id'), row['scope'], row.get('role'), row.get('provider_alias')): row
              for row in frozen.get('rows', [])}
    for snapshot in actual:
        for process in snapshot.get('process_connections', []):
            env = frozen.get('environment') or {}
            for name, url in process['endpoints'].items():
                expected_url = env.get(name)
                if expected_url and url and expected_url.rstrip('/') != url.rstrip('/'):
                    drift.append({'kind': 'process_endpoint', 'pid': process['pid'], 'expected': expected_url, 'actual': url})
        for row in snapshot.get('rows', []):
            key = (row.get('profile_id'), 'braid-member' if row['scope'] == 'braid-root' else row['scope'], row.get('role'), row.get('provider_alias'))
            original = by_key.get(key)
            if original and original.get('model') != row.get('model'):
                drift.append({'kind': 'model', 'scope': row['scope'], 'profile_id': row.get('profile_id'),
                              'role': row.get('role'), 'frozen': original.get('model'), 'actual': row.get('model')})
            env = frozen.get('environment') or {}
            expected_url = env.get('VISUAL_BASE_URL') if row['scope'] == 'visual' else None
            expected_url = expected_url or env.get('FACTORY26_BASE_URL') or env.get('OPENAI_BASE_URL') or (original or {}).get('endpoint')
            if expected_url and row.get('endpoint') and expected_url.rstrip('/') != row['endpoint'].rstrip('/'):
                drift.append({'kind': 'endpoint', 'scope': row['scope'], 'expected': expected_url, 'actual': row['endpoint']})
    covered = bool(actual) and bool(frozen.get('rows')) and not frozen.get('errors') and all(snapshot.get('rows') and not snapshot.get('errors') for snapshot in actual)
    return {'status': 'detected' if drift else 'no_observed_drift' if covered else 'unknown', 'differences': drift,
            'coverage': '比较模型、endpoint及冻结输入字节；费用模式及未观察的调用不在一致性结论内。'}


def operation_snapshot(directory, *, live=False):
    from lab.exp.history import selected_runs
    directory = Path(directory).resolve()
    inputs = json.loads((directory / 'inputs.json').read_text())
    result = {'operation': str(directory), 'venue': inputs['venue'], 'observed_at': time.time(), 'jobs': []}
    if inputs['venue'] != 'local':
        result['journals'] = [journal_snapshot(Path(p)) for p in inputs.get('journals', [])]
        return result
    experiment = Path(inputs['experiment'])
    manifest = json.loads((experiment / 'manifest.json').read_text())
    selection = directory / 'selection.json'
    desired = json.loads(selection.read_text()) if selection.is_file() else {}
    desired = {k: desired[k] for k in ('root_model', 'criterion', 'config_sha256') if k in desired}
    if selection.is_file():
        desired['source'] = identity(selection)
    runs = selected_runs(inputs)
    for job in manifest['jobs']:
        if job['id'] not in inputs['job_ids']:
            continue
        frozen = frozen_job(experiment, job)
        actual, observations = [], []
        for run in runs:
            record = json.loads((run / 'run.json').read_text())
            if record['job_id'] != job['id']:
                continue
            batches = sorted((Path(inputs['monitor_output']) / 'monitor').glob('*/' + run.name + '/model-facts.json'))
            if live and record['phase'] not in {'completed', 'finished', 'failed', 'interrupted', 'cancelled', 'lost'}:
                from .local_monitor import collect
                import tempfile
                module_source = Path(__file__).with_name('provider_liveness.py').read_text()
                with tempfile.TemporaryDirectory(prefix='factory26-model-facts-') as temporary:
                    observation = collect(run, Path(temporary), module_source, model_facts_only=True)
                facts = observation.get('model_facts', [])
                observations.append({'run_id': run.name, 'read_at': observation['observed_at'],
                                     'observation_error': observation.get('observation_error'), 'status': observation.get('status'),
                                     'preparation': observation.get('preparation'), 'physical': observation.get('physical'), 'source': 'existing local_monitor.collect'})
            elif batches:
                saved = json.loads(batches[-1].read_text())
                facts = saved['snapshots']
                observations.append({'run_id': run.name, 'source': identity(batches[-1]), 'read_at': saved['observed_at']})
            else:
                roots = run / 'workspace/official-generation/template/.factory26'
                facts = [runtime_snapshot(p) for p in sorted(roots.iterdir()) if (p / 'braid-request.json').is_file()] if roots.is_dir() else []
                observations.append({'run_id': run.name, 'phase': record['phase'], 'reason': '没有保存模型采集；可显式 --live 单次读回' if not facts else 'archived workspace'})
            actual.extend(facts)
        result['jobs'].append({'job_id': job['id'], 'desired': desired, 'frozen': frozen,
                               'actual': actual, 'observations': observations, 'drift': compare(frozen, actual, desired),
                               'replay_policy': {k: v for k, v in ((inputs.get('replay') or {}).get('jobs', {}).get(job['id'], (inputs.get('replay') or {}).get('defaults', {}))).items() if k in {'credential_mode', 'allow_competition_credit'}}})
    return result


def journal_snapshot(directory):
    raw = json.loads((directory / 'inputs.json').read_text())
    models = raw.get('model_config') or {}
    state = json.loads((directory / 'state.json').read_text()) if (directory / 'state.json').exists() else {}
    observed_modes = [{ 'run_id': task.get('run_id'), 'credential_mode': task['platform_result']['credential_mode']}
                      for task in state.get('tasks', {}).values() if (task.get('platform_result') or {}).get('credential_mode')]
    return {'directory': str(directory), 'platform_observed_modes': observed_modes, 'frozen': {'models': {k: endpoint(v) if k.endswith('url') else v
             for k, v in models.items() if k in {'model', 'visual_model', 'base_url'}},
             'credential_mode': raw.get('credential_mode', 'unknown'), 'source': identity(directory / 'inputs.json')},
            'actual': {'status': 'unknown', 'reason': '平台启动模式不证明生成工作区的原生模型；需运行材料'},
            'run_ids': [v.get('run_id') for v in state.get('tasks', {}).values()]}


def run_snapshot(run, *, live=False):
    run = Path(run)
    record = json.loads((run / 'run.json').read_text())
    frozen = frozen_job(run, {'id': record['job_id'], 'inputs': record['inputs']})
    actual = []
    observation = {'run_id': record['run_id'], 'phase': record['phase']}
    if live and record['phase'] not in {'completed', 'finished', 'failed', 'interrupted', 'cancelled', 'lost'}:
        from .local_monitor import collect
        import tempfile
        with tempfile.TemporaryDirectory(prefix='factory26-model-facts-') as temporary:
            saved = collect(run, Path(temporary), Path(__file__).with_name('provider_liveness.py').read_text(), model_facts_only=True)
        actual = saved.get('model_facts', [])
        observation.update(read_at=saved['observed_at'], observation_error=saved.get('observation_error'), status=saved.get('status'), preparation=saved.get('preparation'), physical=saved.get('physical'))
    else:
        root = run / 'workspace/official-generation/template/.factory26'
        if root.is_dir():
            actual = [runtime_snapshot(p) for p in sorted(root.iterdir()) if (p/'braid-request.json').is_file() or (p/'braid-state/request.json').is_file()]
        observation['reason'] = 'archived workspace' if actual else '没有本地运行材料；活动运行可用 --live'
    return {'run_id': record['run_id'], 'desired': {'status': 'unknown', 'reason': 'run原件不含独立desired声明'},
            'frozen': frozen, 'actual': actual, 'observation': observation, 'drift': compare(frozen, actual, {})}


def query(path, *, live=False):
    path = Path(path).resolve()
    if path.is_file():
        index = json.loads(path.read_text())
        if 'operations' in index:
            return {'source': identity(path), 'operations': [operation_snapshot(row['operation'], live=live) for row in index['operations']],
                    'queued': [{'target': value, 'actual': 'not_dispatched', 'frozen': 'operation_not_frozen'} for value in index.get('queued', [])]}
        if 'runs' in index:
            return {'source': identity(path), 'runs': [run_snapshot(p, live=live) for p in index['runs']]}
        raise ValueError('需要 operation-index 或含 runs 的既有matrix索引')
    if (path/'run.json').exists():
        return run_snapshot(path, live=live)
    if (path/'inputs.json').is_file() and 'competition_id' in json.loads((path/'inputs.json').read_text()):
        return journal_snapshot(path)
    return operation_snapshot(path, live=live)


def render(value):
    """Human view; the JSON projection remains the machine interface."""
    if 'platform_observed_modes' in value:
        return json.dumps(value, ensure_ascii=False, indent=2)
    operations = value.get('operations', [value])
    jobs = [job for operation in operations for job in operation.get('jobs', [])]
    jobs.extend(value.get('runs', []))
    if 'frozen' in value:
        jobs.append(value)
    lines = []
    for job in jobs:
        lines.append('\n运行：' + job.get('run_id', job.get('job_id', 'unknown')))
        lines.append('desired root：' + job.get('desired', {}).get('root_model', 'unknown') + '；drift：' + job['drift']['status'])
        lines.append('层级\t职责/成员/角色\t模型\tAPI endpoint\t费用模式')
        for layer, rows in [('frozen', job['frozen']['rows']), *[('actual', a.get('rows', [])) for a in job['actual']]]:
            for row in rows:
                if row['scope'] == 'pi-native-provider':
                    continue
                label = '/'.join(str(row[k]) for k in ('scope', 'profile_id', 'role') if row.get(k))
                lines.append('\t'.join([layer, label, str(row.get('model') or 'unknown'), row.get('endpoint') or 'unknown', row.get('credential_mode', 'unknown')]))
        if job['frozen'].get('environment'):
            lines.append('冻结模型连接输入：' + json.dumps(job['frozen']['environment'], ensure_ascii=False))
        for actual in job['actual']:
            seen = sorted({(row['provider'], row['model']) for row in actual.get('observed_usage', [])})
            lines.append('已观察调用：' + ', '.join(provider + '/' + model for provider, model in seen))
            urls = sorted({url for p in actual.get('process_connections', []) for url in p['endpoints'].values() if url})
            lines.append('活动进程连接：' + ', '.join(urls))
        lines.append('冻结来源：' + ', '.join(p['path'] + ' sha256=' + p['sha256'] for p in job['frozen']['sources']))
        for difference in job['drift']['differences']:
            lines.append('漂移：' + json.dumps(difference, ensure_ascii=False))
        for observation in job.get('observations', [job.get('observation', {})]):
            lines.append('观察：' + json.dumps(observation, ensure_ascii=False))
        if job.get('replay_policy'):
            lines.append('独立评分费用政策：' + json.dumps(job['replay_policy'], ensure_ascii=False))
    for operation in operations:
        for journal in operation.get('journals', []):
            lines.append(json.dumps(journal, ensure_ascii=False))
    if value.get('queued'):
        lines.append('\n未派发：' + ', '.join(row['target'] for row in value['queued']))
    lines.append('\n配置不证明已调用，API认证不证明账单模式；unknown与no_observed_drift均不代表完整一致。详细来源、版本、native home与session身份使用 --json。')
    return '\n'.join(lines)
