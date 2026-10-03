"""Read declared assets and current host facts without preparing or reserving."""
import json
import os
from pathlib import Path
import platform
import shutil
import socket
import time

from . import artifacts, controller
from .core import canonical, digest, error, public, read, record, require


def inspect(recipe_path, deployment=None, *, environment=None):
    recipe_path = Path(recipe_path).resolve(strict=True)
    if recipe_path.is_dir():
        recipe_path = recipe_path / 'experiment.json'
    spec = read(recipe_path)
    if environment is not None:
        from .environment import resolve
        spec = resolve(spec, environment, base=recipe_path.parent)
    if spec.get('kind') == 'factory26.exp.intent':
        return _intent_plan(recipe_path, require(spec, 'intent'))
    require(spec, 'experiment')
    controller.validate_recipe(spec)
    base = recipe_path.parent
    result = record('readiness', experiment_id=spec.get('experiment_id'), observed_at=time.time(),
                    source=str(recipe_path), source_sha256=digest(recipe_path),
                    host={'hostname': socket.gethostname(), 'os': platform.system(),
                          'architecture': platform.machine(), 'cpu_count': os.cpu_count(),
                          'free_bytes': shutil.disk_usage(base).free},
                    runtimes={}, jobs=[], blockers=[], dispatch_permission=False,
                    tool_cache={'status': 'unknown', 'reason': '配方没有独立工具缓存合同；工具可能随 Harness 包提供'})
    for name, expected in spec.get('compilation', {}).get('files', {}).items():
        try:
            if name in spec.get('compilation_evidence', {}):
                observed = artifacts.verify(base / 'artifacts', spec['compilation_evidence'][name])['contents']['sha256']
            else:
                observed = digest(name)
            if observed != expected:
                raise ValueError('compiled descriptor or score snapshot changed')
        except (OSError, ValueError) as exc:
            result['blockers'].append({'component': 'compilation', 'source': name, 'error': error(exc)})
    for purpose in ('controller', 'runner'):
        field = purpose + '_runtime'
        value = spec.get(field)
        if value is None and purpose == 'runner' and not any(job['backend']['kind'] != 'hosted' for job in spec['jobs']):
            continue
        try:
            if value is None and spec.get('environment_selection'):
                from scripts.runtime import plan_host_runtime
                binding = spec['environment_selection']
                plan = plan_host_runtime(Path(binding['selection']['python']))
                if plan['dependencies'] != binding['runtime_dependencies']:
                    raise ValueError('runtime dependencies differ from frozen selection')
                value = str(Path(binding['selection']['cache_root']) / plan['key'] / (purpose + '.json'))
            if value is None:
                raise ValueError('local execution needs an explicit runner runtime')
            asset = controller._runtime(value if isinstance(value, dict) else (base / value).resolve(strict=True), purpose)
            result['runtimes'][purpose] = {'status': 'verified', 'root': asset['root'], 'python': asset['launcher'],
                                           'interpreter_sha256': asset['interpreter_sha256'], 'identity_sha256': canonical(asset['identity'])}
        except (OSError, ValueError, KeyError) as exc:
            result['runtimes'][purpose] = {'status': 'unavailable', 'error': error(exc)}
            result['blockers'].append({'component': field, 'error': error(exc)})
    if result['host']['free_bytes'] <= spec['storage']['host_reserve_bytes']:
        result['blockers'].append({'component': 'storage', 'reason': 'host reserve unavailable',
                                   'required_bytes': spec['storage']['host_reserve_bytes']})
    private = {}
    credential_names = set()
    if deployment is None and (base / 'deployment.json').exists():
        deployment = base / 'deployment.json'
    if deployment is not None:
        try:
            private = controller._load_deployment(deployment)
            for name, location in private.items():
                if name == 'credential_file' and Path(location).stat().st_mode & 0o077:
                    raise ValueError('private credential_file must have mode 600')
                if name == 'credential_file':
                    values = read(location)
                    values = values.get('environment', values)
                    if not isinstance(values, dict) or any(not isinstance(key, str) or not isinstance(value, str) for key, value in values.items()):
                        raise ValueError('private credential file needs string environment bindings')
                    credential_names = {key for key, value in values.items() if value}
        except (OSError, ValueError) as exc:
            result['blockers'].append({'component': 'deployment', 'error': error(exc)})
    docker = {}
    for job in spec['jobs']:
        row = {'job_id': job['id'], 'purpose': job['purpose'], 'target': job.get('target'),
               'assets': [], 'blockers': [], 'backend': job['backend']['kind']}
        input_paths = {}
        input_provenance = {}
        bindings = dict(job.get('inputs', {}))
        bindings.update({name: job[name] for name in ('prepared', 'checkpoint', 'stop_evidence') if name in job})
        for name, binding in bindings.items():
            item = {'name': name}
            try:
                if isinstance(binding, dict) and set(binding) == {'from_production'}:
                    item.update(status='waiting', from_production=binding['from_production'])
                    row['blockers'].append({'component': 'input', 'reason': '等待声明producer产物', **item})
                elif isinstance(binding, dict) and 'from_job' in binding:
                    item.update(status='waiting', from_job=binding['from_job'], output=binding['output'])
                    row['blockers'].append({'component': 'input', 'reason': '等待生成制品', **item})
                elif isinstance(binding, str) or 'source' in binding:
                    source = (base / (binding if isinstance(binding, str) else binding['source'])).resolve(strict=True)
                    if isinstance(binding, dict) and 'source_identity' in binding and artifacts.contents(source) != binding['source_identity']:
                        raise ValueError('compiled source bytes changed')
                    input_paths[name] = source
                    item.update(status='present', source=str(source), identity_pinned=isinstance(binding, dict) and 'source_identity' in binding)
                else:
                    store = (base / binding.get('store', 'artifacts')).resolve(strict=True)
                    manifest = artifacts.verify(store, binding)
                    input_paths[name] = store / manifest['artifact_id'] / 'payload'
                    input_provenance[name] = manifest.get('provenance')
                    item.update(status='verified', artifact_id=manifest['artifact_id'], type=manifest['type'])
            except (OSError, ValueError, KeyError) as exc:
                item.update(status='unavailable', error=error(exc))
                row['blockers'].append({'component': 'input', **item})
            row['assets'].append(item)
        if job.get('arc_contract'):
            try:
                from lab.arc_bench.local_job import generation_inputs, sdk_role
                if 'runner' not in input_paths:
                    raise ValueError('ARC host SDK input is not available')
                role = sdk_role(input_paths['runner'])
                if role != job['arc_contract']['sdk']:
                    raise ValueError('ARC host SDK differs from compiled role')
                row['arc_inputs'] = (generation_inputs(input_paths, input_paths['runner'], expected_sdk=role, agent_provenance=input_provenance.get('agent'))
                    if {'agent', 'requirements'} <= input_paths.keys() else {'sdk': role, 'status': 'waiting-for-production'})
            except (OSError, ValueError, KeyError) as exc:
                row['blockers'].append({'component': 'arc-input-role', 'error': error(exc)})
        backend = job['backend']
        if job.get('prepared'):
            try:
                if 'prepared' not in input_paths or job.get('stop_evidence') and 'stop_evidence' not in input_paths:
                    raise controller.Blocked('source gate needs available prepared/stop inputs; see asset errors')
                prepared_path = input_paths['prepared']
                prepared = read(prepared_path / 'harness-manifest.json' if prepared_path.is_dir() else prepared_path)
                stop_path = input_paths.get('stop_evidence')
                stop = read(stop_path / 'manifest.json' if stop_path.is_dir() else stop_path) if stop_path else {}
                controller.source_stop_binding(prepared, stop)
                if prepared.get('status') != 'complete':
                    raise ValueError('Harness producer has not declared complete prepared content')
                row['source_gate'] = 'saved binding matched; current source observation required at launch'
            except (OSError, ValueError, KeyError, controller.Blocked) as exc:
                row['blockers'].append({'component': 'source-gate', 'error': error(exc)})
        if backend['kind'] == 'hosted':
            row['platform'] = {'competition_id': backend.get('competition_id'), 'task': backend.get('task'),
                               'credential_mode': backend.get('credential_mode'),
                               'current_platform_gate': 'unknown; only adapter may observe/reconcile at dispatch'}
            for key in ('cookie_file', *(['credential_file'] if backend.get('credential_mode') == 'self_funded' else [])):
                if key not in private:
                    row['blockers'].append({'component': 'deployment', 'reason': '需要显式私有引用：' + key})
            if backend.get('credential_mode') == 'self_funded' and 'credential_file' in private and not credential_names & {'FACTORY26_API_KEY', 'OPENAI_API_KEY'}:
                row['blockers'].append({'component': 'deployment', 'reason': '选定 credential_file 缺少 hosted adapter 所需模型 key 绑定'})
        bindings = json.loads(job.get('environment', {}).get('FACTORY26_MODEL_BINDINGS', '{}'))
        required = {binding['credential_env'] for binding in bindings.values()}
        row['credential_coverage'] = {'required_variables': sorted(required), 'missing': sorted(required - credential_names)}
        if required - credential_names:
            row['blockers'].append({'component': 'deployment', 'reason': '选定私有引用缺少模型通道凭据变量',
                                     'variables': sorted(required - credential_names)})
        targets = [backend] if backend['kind'] == 'docker' else []
        if backend.get('external_docker'):
            targets.append(backend['external_docker'])
        for target in targets:
            key = canonical(target)
            if key not in docker:
                docker[key] = _docker(target)
            row.setdefault('docker', []).append(docker[key])
            row['blockers'].extend(docker[key]['blockers'])
        row['asset_readiness'] = 'blocked' if row['blockers'] or result['blockers'] else 'observed'
        result['jobs'].append(row)
    return public(result)


def _intent_plan(path, spec):
    """Explain declared production before build; do not initialize caches or domains."""
    from .compiler import select
    binding = spec.get('environment_selection')
    if not binding:
        raise ValueError('doctor on intent requires --environment or a frozen environment selection')
    from scripts.runtime import plan_host_runtime
    selection = binding['selection']
    plan = plan_host_runtime(Path(selection['python']))
    cache = Path(selection['cache_root'])
    result = record('readiness', experiment_id=spec['experiment_id'], source=str(path),
        source_sha256=digest(path), observed_at=time.time(), dispatch_permission=False,
        host={'hostname': socket.gethostname(), 'os': platform.system(), 'architecture': platform.machine(),
              'free_bytes': shutil.disk_usage(path.parent).free}, runtimes={}, jobs=[], blockers=[],
        environment={'id': selection['id'], 'profile_sha256': binding['profile_sha256']}, productions=[])
    result['selection'] = select(spec['selection_policy'], spec['models'], path.parent)
    for purpose in ('controller', 'runner'):
        receipt = cache / plan['key'] / (purpose + '.json')
        result['runtimes'][purpose] = {'status': 'present' if receipt.is_file() else 'build-required',
                                      'python': str(receipt), 'dependencies': plan['dependencies'],
                                      'integrity': 'checked at build/consumption'}
    for name, production in spec.get('productions', {}).items():
        dependencies = binding['material_dependencies'][name]
        if production['producer'] == 'harness':
            from scripts.package_agent import material_identity
            identity = material_identity(dependencies)
            receipt = cache / 'harness/materials' / identity.removeprefix('material-') / 'material.json'
        else:
            identity = canonical(dependencies)
            receipt = cache / 'production-index' / ('prepared-' + identity + '.json')
        result['productions'].append({'name': name, 'producer': production['producer'],
            'dependencies_sha256': canonical(dependencies), 'components': list(dependencies),
            'status': 'present' if receipt.is_file() else 'build-required', 'identity': identity,
            'action': 'verify cached production' if receipt.is_file() else 'produce missing material'})
    for target in spec['targets']:
        template = spec['variants'][target['variant']]['generate']
        arc = None
        if template.get('operation') == 'arc-local-generate':
            try:
                from lab.arc_bench.local_job import sdk_role
                selected_arc = selection['arc']
                arc = {'sdk': sdk_role(selected_arc['sdk_source']), 'target': selected_arc['target'],
                       'inputs': {name: {'status': 'waiting-for-production', **value}
                                  if isinstance(value, dict) and set(value) == {'from_production'} else {'status': 'declared', 'binding': value}
                                  for name, value in {**template.get('inputs', {}), **spec['cases'][target['case']].get('inputs', {})}.items()},
                       'child_services': {'resource_evidence': 'created in actual child namespace',
                                          'telemetry': 'child collector binding required'}}
            except (OSError, ValueError, KeyError) as exc:
                result['blockers'].append({'component': 'arc-input-role', 'error': error(exc)})
        result['jobs'].append({'job_id': target['id'], 'purpose': template['purpose'],
            'asset_readiness': 'planned', 'assets': [], 'blockers': [], 'target': target, **({'arc': arc} if arc else {})})
    return public(result)


def _docker(target):
    from lab.docker_endpoint import execute
    from .admission import volume_name
    result = {'endpoint': target.get('endpoint'), 'image_id': target.get('image_id'),
              'declared_slots': target.get('slots'), 'blockers': [], 'available_slots': 'unknown',
              'reservation_coverage': 'authority not read; no helper created and no reservations reconciled'}
    try:
        endpoint = target['endpoint']
        template = '{"daemon_id":{{json .ID}},"os":{{json .OSType}},"architecture":{{json .Architecture}},"cpu_count":{{json .NCPU}},"memory_bytes":{{json .MemTotal}},"server_version":{{json .ServerVersion}}}'
        info = json.loads(execute(endpoint, ['info', '--format', template], check=True, capture_output=True, text=True, timeout=15).stdout)
        if info['daemon_id'] != endpoint['daemon_id']:
            raise ValueError('Docker daemon differs from the declared endpoint')
        result['host'] = info
        image = target['image_id']
        if not image.startswith('sha256:'):
            raise ValueError('runner image must be an immutable image ID')
        image_info = json.loads(execute(endpoint, ['image', 'inspect', '--format', '{"id":{{json .Id}},"os":{{json .Os}},"architecture":{{json .Architecture}}}', image],
                                        check=True, capture_output=True, text=True, timeout=15).stdout)
        if image_info['id'] != image:
            raise ValueError('runner image identity differs')
        result['image'] = image_info
        result['runner_python'] = {'declared': target.get('python', 'python3'), 'actual_identity': 'unknown; not executed by doctor'}
        template = '{"id":{{json .ID}},"name":{{json .Names}},"state":{{json .State}},"status":{{json .Status}}}'
        output = execute(endpoint, ['ps', '-a', '--no-trunc', '--filter', 'label=io.factory26.exp.attempt', '--format', template],
                         check=True, capture_output=True, text=True, timeout=15)
        result['workloads'] = [json.loads(line) for line in output.stdout.splitlines()]
        if target.get('admission_volume') != volume_name(endpoint):
            raise ValueError('declared admission volume differs from the unique daemon authority')
        handoff = require(target['authority_handoff'], 'authority-handoff')
        if handoff['daemon_id'] != endpoint['daemon_id'] or handoff.get('launch_windows') != 'closed':
            raise ValueError('authority handoff does not bind the declared daemon/closed launch windows')
        names = execute(endpoint, ['volume', 'ls', '--format', '{{.Name}}'],
                        check=True, capture_output=True, text=True, timeout=15).stdout.splitlines()
        if target['admission_volume'] not in names:
            if handoff.get('mode') != 'first-use':
                raise ValueError('declared admission authority volume is missing')
            result['authority_volume'] = {'name': target['admission_volume'], 'status': 'not-initialized',
                                          'reason': 'first-use dispatch creates authority after revalidating handoff'}
        else:
            volume = json.loads(execute(endpoint, ['volume', 'inspect', target['admission_volume']],
                                        check=True, capture_output=True, text=True, timeout=15).stdout)[0]
            from .admission import volume_identity
            result['authority_identity'] = volume_identity(target, volume)
            result['authority_volume'] = volume
        result['handoff'] = {'sha256': canonical(handoff),
                              'mode': handoff['mode'], 'coverage': handoff.get('coverage')}
    except Exception as exc:
        result['blockers'].append({'component': 'docker', 'error': error(exc)})
    result['observed_at'] = time.time()
    return result


def render(value):
    lines = [value['experiment_id'] + ' · readiness（只读，不授予派发许可）',
             f"host: {value['host']['hostname']} / {value['host']['os']} {value['host']['architecture']} / free {value['host']['free_bytes']} bytes"]
    for name, runtime in value['runtimes'].items():
        lines.append(f"{name} runtime: {runtime['status']} / {runtime.get('python', runtime.get('error', {}).get('message', '?'))}")
    for production in value.get('productions', []):
        lines.append(f"material {production['name']} / {production['producer']}: {production['action']}")
    for issue in value['blockers']:
        lines.append('blocked by ' + issue['component'] + ': ' + str(issue.get('reason', issue.get('error', {}).get('message'))))
    for job in value['jobs']:
        lines.append(f"{job['job_id']} / {job['purpose']}: {job['asset_readiness']}")
        for asset in job['assets']:
            lines.append(f"  {asset['name']}: {asset['status']}")
        for target in job.get('docker', []):
            host = target.get('host', {})
            lines.append(f"  docker: {host.get('daemon_id', '?')} / CPU {host.get('cpu_count', '?')} / memory {host.get('memory_bytes', '?')}")
            lines.append(f"  slots: declared {target['declared_slots']} / available unknown（未读取或修改预约权威）")
        for issue in job['blockers']:
            lines.append('  blocked by ' + issue['component'] + ': ' + str(issue.get('reason', issue.get('error', {}).get('message'))))
    lines.append('工具缓存及供应商/平台可执行能力缺少独立声明或现场证明时保持未知；执行仍核对实际准入。')
    return '\n'.join(lines)
