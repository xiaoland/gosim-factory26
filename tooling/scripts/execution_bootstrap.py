"""One namespace owns service creation, entry environment and service closure."""
import os
import json
import signal
import subprocess
import tarfile
import platform
import shutil
import sys
import time
from pathlib import Path

try:
    from . import execution_context
except ImportError:
    import execution_context


def resource(directory, *, require_cgroup=False, owner='runner', package=None):
    try:
        from .agent_support import ResourceEvidence, process_identity
    except ImportError:
        from agent_support import ResourceEvidence, process_identity
    evidence = ResourceEvidence(directory, root_pid=os.getpid(), package=package)
    if require_cgroup and evidence.cgroup is None:
        raise ValueError('required execution namespace cgroup resource evidence is unavailable')
    evidence.sample('execution-ready')
    sample = Path(directory) / 'process-evidence/resource-latest.json'
    if not sample.is_file():
        raise ValueError('execution resource sample was not persisted')
    return evidence, {'owner': owner, 'status': 'ready', 'sample_path': str(sample),
                      'archive_path': str(Path(directory) / 'process-evidence/resources.jsonl'),
                      'scope': 'cgroup-v2' if evidence.cgroup else 'host-visible',
                      'cgroup': str(evidence.cgroup) if evidence.cgroup else None, 'gaps': evidence.errors}


def collector(directory, attempt_id, cap_bytes, *, owner='runner'):
    from lab.exp.telemetry import Collector
    value = Collector(directory, attempt_id, cap_bytes=cap_bytes)
    binding = {'endpoint': value.binding['receiver_endpoint'], 'token': value.token,
               **{key: value.binding[key] for key in ('attempt_id', 'stream_id', 'collector_epoch')}}
    return value, {'owner': owner, 'status': 'ready', 'binding': binding}


def context(assembly, services, attempt_id, incarnation_id, path, base_environment, model_policy=None):
    assembly=dict(assembly)
    assembly.setdefault('inputs',json.loads(base_environment.get('FACTORY26_EXP_INPUT_BINDINGS','{}')))
    states = dict(services)
    states['telemetry'] = dict(states.pop('collector', states.get('telemetry', {'owner': 'runner', 'status': 'disabled'})))
    value = execution_context.create(assembly, states, attempt_id, incarnation_id, path, model_policy)
    environment = dict(base_environment)
    # Old values can point into the parent namespace. Only this ready instance speaks.
    for name in tuple(environment):
        if name.startswith('OTEL_EXPORTER_OTLP_') or name in {'FACTORY26_EXP_SERVICES', 'FACTORY26_EXP_RESOURCE_SAMPLE', 'FACTORY26_EXP_TELEMETRY_BINDING', 'FACTORY26_EXP_INPUT_BINDINGS'}:
            environment.pop(name)
    environment.update(execution_context.environment(value))
    environment['FACTORY26_EXECUTION_CONTEXT'] = str(Path(path).resolve())
    support=next((row['local_root'] for row in assembly['definitions'] if row['role']=='support'),None)
    if support:
        environment['PYTHONPATH']=os.pathsep.join([support,str(Path(support)/'otlp-deps'),environment.get('PYTHONPATH','')])
    return environment


def close(evidence, receiver, *, reason='execution-closed', on_error=None):
    errors, seal = [], None
    operations = []
    if evidence is not None:
        operations.extend((('resource-final-sample', lambda: evidence.sample(reason)),
                           ('resource-close', evidence.close)))
    if receiver is not None:
        operations.append(('collector-close', lambda: receiver.close(producer_flush='unknown')))
    for name, operation in operations:
        try:
            value = operation()
            if name == 'collector-close':
                seal = value
        except Exception as error:
            if on_error is not None:
                on_error(name, error)
            else:
                errors.append(error)
    if errors:
        raise errors[0]
    return seal


def delivery_assembly(root, output, attempt_id, namespace=None, definition_bindings=None, input_bindings=None):
    """Translate only the frozen delivery map; no parent paths or name guessing."""
    root, output = Path(root).resolve(strict=True), Path(output).resolve()
    layout = json.loads((root / 'delivery-layout.json').read_text())
    if layout.get('kind') != 'factory26.harness.delivery' or layout.get('schema_version') != 1:
        raise ValueError('unsupported delivery layout')
    if layout['mode'] == 'hosted-prepared':
        return prepared_delivery_assembly(root, output, attempt_id, namespace, layout)
    roles = []
    placements = {row['role']: row for row in definition_bindings or []}
    if layout['mode'] == 'sdk-components' and not placements:
        raise ValueError('SDK thin delivery requires actual authenticated component placements')
    for row in layout['roles']:
        if placements:
            placement=placements.get(row['role'])
            if not placement or placement['reference']!=row['reference'] or placement['member']!=row['member'] or placement['access']!='read-only':
                raise ValueError('SDK role lacks its actual frozen read-only binding: '+row['role'])
            local=Path(placement['local_root'])
            if not local.is_absolute() or not local.exists():
                raise ValueError('SDK role is unavailable in this namespace: '+row['role'])
            roles.append({**placement,'local_root':str(local)})
        else:
            path=root/execution_context.member_join('.',row['path'])
            if not path.exists() or not path.resolve().is_relative_to(root):
                raise ValueError('hosted delivered role is unavailable: '+row['role'])
            roles.append({'role':row['role'],'reference':row['reference'],'member':row['member'],
                'local_root':str(path),'access':'delivered-content-readback'})
    try:
        from .agent_support import process_identity
    except ImportError:
        from agent_support import process_identity
    observed = namespace or {'kind': 'delivery-local-scope', 'process': process_identity(os.getpid()),
                             'platform_binding': 'external-controller-only'}
    actual_inputs=dict(input_bindings or {})
    for name,row in layout.get('inputs',{}).items():
        if name in actual_inputs:
            raise ValueError('delivery and namespace both bind execution input: '+name)
        path=root/execution_context.member_join('.',row['path'])
        if not path.exists() or not path.resolve().is_relative_to(root):
            raise ValueError('delivered execution input escapes delivery: '+name)
        actual_inputs[name]={'reference':row['reference'],'member':row['member'],'root':str(path)}
    state = output / '.factory26' / attempt_id
    return execution_context.validate_assembly({'kind': 'factory26.exp.assembly', 'schema_version': 2, 'status': 'assembled',
            'namespace': observed, 'definitions': roles, 'definition': layout['definition'],
            'state': {'root': str(state), 'mode': 'fresh', 'holder': None, 'generation': 0},
            'inputs':actual_inputs, 'workspace': str(output), 'entry': {'mode': 'fresh', 'path': str(execution_context.role({'assembly':{'definitions':roles}},'agent') / 'main.py')},
            'proof': {'delivery': 'explicit-frozen-role-map', 'state_capture': 'capability-dependent'}})


def prepared_delivery_assembly(root, output, attempt_id, namespace, layout):
    """Install only the already prepared state; preserve its original native paths."""
    from agent_support import verify_package, process_identity
    import exp_checkpoint
    package_readback = verify_package(root)
    execution_context.write(output/'.arc/prepared-definition-readback.json', {
        'variant':package_readback['backend'], 'files':len(package_readback['files']),
        'cache_advice':package_readback['verification_cache_advice']})
    binding = layout['prepared']
    manifest_path = root/execution_context.member_join('.', binding['manifest_path'])
    if exp_checkpoint.digest(manifest_path) != binding['manifest_sha256']:
        raise ValueError('prepared delivery manifest identity differs')
    manifest = json.loads(manifest_path.read_text())
    legacy = (manifest.get('acquisition', {}).get('status') == 'legacy-terminal-export'
              and manifest.get('source_identity', {}).get('backend_identity', {}).get('kind') == 'hosted'
              and not manifest.get('readback', {}).get('gaps', ['missing-readback']))
    if manifest['kind'] != 'factory26.harness.prepared' or (manifest['status'] != 'complete' and not legacy):
        raise ValueError('prepared delivery has unresolved execution gaps')
    target = manifest['target_layout']
    if target['os'] != platform.system() or target['architecture'] != platform.machine():
        raise ValueError('prepared delivery platform differs from worker')
    roles = []
    for row in layout['roles']:
        path = root/execution_context.member_join('.', row['path'])
        if str(path) != row['logical_root'] or not path.exists():
            raise ValueError('prepared definition logical placement differs: '+row['role'])
        roles.append({'role':row['role'], 'reference':row['reference'], 'member':row['member'],
                      'local_root':str(path), 'access':'delivered-content-readback'})
    runtime = next(Path(row['local_root']) for row in roles if row['role'] == 'runtime')
    runtime_files = target['runtime_identity'].get('files')
    if not isinstance(runtime_files, dict) or not runtime_files:
        raise ValueError('prepared Hosted target needs explicit runtime file identities')
    for member, expected_sha in runtime_files.items():
        if exp_checkpoint.digest(exp_checkpoint.path_at(runtime, member)) != expected_sha:
            raise ValueError('prepared runtime differs from frozen target: '+member)
    state = Path(target['run_root'])
    if (not state.is_relative_to(output) or state == output or state.exists() or state.is_symlink()):
        raise ValueError('prepared state placement is occupied or outside output')
    archive_path = root/execution_context.member_join('.', binding['state_archive'])
    if exp_checkpoint.digest(archive_path) != binding['state_archive_sha256']:
        raise ValueError('prepared state archive identity differs')
    expected = {name.removeprefix('run/'):value for name,value in manifest['files'].items()
                if name.startswith('run/')}
    state.mkdir(parents=True)
    links = []
    with tarfile.open(archive_path, 'r') as archive:
        observed = set()
        for item in archive:
            if item.name == 'run' and item.isdir():
                continue
            if not item.name.startswith('run/'):
                raise ValueError('prepared archive member escapes state')
            name = item.name.removeprefix('run/')
            if name not in expected or name in observed:
                raise ValueError('prepared archive has unknown or duplicate member: '+name)
            observed.add(name)
            record = expected[name]
            path = exp_checkpoint.path_at(state, name)
            if item.isdir() and record['type'] == 'directory':
                path.mkdir(parents=True, exist_ok=True)
            elif item.isfile() and record['type'] == 'file':
                path.parent.mkdir(parents=True, exist_ok=True)
                with archive.extractfile(item) as source, path.open('xb') as destination:
                    shutil.copyfileobj(source, destination)
                path.chmod(record['mode'])
            elif item.issym() and record['type'] == 'symlink' and item.linkname == record['target']:
                links.append((path, item.linkname))
            else:
                raise ValueError('prepared archive type differs: '+name)
        if observed != set(expected):
            raise ValueError('prepared state archive is incomplete')
    for path, target_path in links:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.symlink_to(target_path)
    if exp_checkpoint.inventory(state) != expected:
        raise ValueError('prepared state independent readback differs')
    return execution_context.validate_assembly({'kind':'factory26.exp.assembly', 'schema_version':2,
        'status':'assembled', 'namespace':namespace or {'kind':'hosted-delivery', 'process':process_identity(os.getpid())},
        'definitions':roles, 'definition':None, 'state':{'root':str(state), 'mode':'snapshot-copy', 'holder':None, 'generation':0},
        'workspace':str(output), 'inputs':{name:{'reference':row['reference'], 'member':row['member'],
                                              'root':str(root/row['path'])} for name,row in layout.get('inputs', {}).items()},
        'entry':{'mode':'resume', 'path':str(root/'support/recover_completed.py'),
                 'prepared_manifest':str(manifest_path), 'prepared_manifest_sha256':binding['manifest_sha256']},
        'proof':{'delivery':'explicit-prepared-projection', 'state_capture':manifest['acquisition']['status'],
                 'prepared_reference':binding['reference']}})


def launch_delivery(root, argv, *, output, namespace=None, public_environment=None, cap_bytes=64 * 1024 * 1024, state_binding=None, capture_source=None, definition_bindings=None, input_bindings=None):
    """SDK/Hosted delegate their namespace lifecycle to the same bootstrap."""
    root, output = Path(root).resolve(strict=True), Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    attempt_id = (namespace or {}).get('attempt_id') or os.environ.get('FACTORY26_EXP_ATTEMPT_ID') or ('delivery-' + str(os.getpid()))
    incarnation = (namespace or {}).get('incarnation_id') or (namespace or {}).get('container_id') or ('process-' + str(os.getpid()))
    assembly = delivery_assembly(root, output, attempt_id, namespace, definition_bindings, input_bindings)
    if state_binding:
        assembly['state'].update(holder=state_binding,generation=state_binding['generation'])
    if capture_source:
        assembly['proof']['capture_source']=capture_source
    if assembly['entry']['mode'] == 'resume' and '--execute-prepared' not in argv:
        argv = [*argv, '--execute-prepared']
    return _launch_assembly(root,output,attempt_id,incarnation,assembly,public_environment,cap_bytes,argv,capture_source)


def _launch_assembly(root,output,attempt_id,incarnation,assembly,public_environment,cap_bytes,argv,capture_source=None):
    evidence, receiver, process = None, None, None
    states = {}
    control = output / '.arc/execution'
    execution_context.write(control / 'assembly.json', assembly)
    if capture_source:
        logical_workspace=Path(capture_source['workspace']['logical_root'])
        if not output.is_relative_to(logical_workspace) or not Path(assembly['state']['root']).is_relative_to(logical_workspace):
            raise ValueError('bootstrap state escapes actual SDK volume namespace')
        execution_context.write(control/'source-binding.json', {**capture_source,
            'state_member':execution_context.member_join(capture_source['workspace']['subpath'],
                str(Path(assembly['state']['root']).relative_to(logical_workspace))),
            'records':{role:execution_context.member_join(capture_source['workspace']['subpath'],
                str((control/name).relative_to(logical_workspace))) for role,name in (('assembly','assembly.json'),('context','context.json'),('result','entry-result.json'))},
            'attempt_id':attempt_id,'incarnation':incarnation})
    result = control / 'entry-result.json'
    auxiliary_errors = []
    auxiliary_path = control / 'bootstrap-auxiliary-errors.json'

    def report_auxiliary(operation, error):
        row = {'operation': operation, 'type': type(error).__name__, 'message': str(error)}
        auxiliary_errors.append(row)
        try:
            execution_context.write(auxiliary_path, {'errors': auxiliary_errors})
        except Exception as write_error:
            row = {**row, 'diagnostic_write_error': {'type': type(write_error).__name__, 'message': str(write_error)}}
        try:
            sys.stderr.write('Bootstrap auxiliary error: ' + json.dumps(row, ensure_ascii=False) + '\n')
        except (OSError, ValueError):
            pass

    def write_result(receipt):
        for path in (result, output / '.arc/adapter-agent-result.json'):
            try:
                execution_context.write(path, receipt)
            except Exception as error:
                report_auxiliary('result-write:' + str(path), error)

    try:
        defaults={}
        delivery_layout=json.loads((root/'delivery-layout.json').read_text()) if (root/'delivery-layout.json').is_file() else {}
        tool_input=delivery_layout.get('private_inputs',{}).get('tool_env')
        if tool_input:
            private_path=root/execution_context.member_join('.',tool_input['path'])
            defaults=json.loads(private_path.read_text())
            if set(defaults)!={'CONTEXT7_API_KEY','EXA_API_KEY'} or any(not isinstance(value,str) or not value for value in defaults.values()):
                raise ValueError('private tool input must contain the two existing tool credential variables')
        provider_input=delivery_layout.get('private_inputs',{}).get('provider_env')
        if provider_input:
            private_path=root/execution_context.member_join('.',provider_input['path'])
            values=json.loads(private_path.read_text())
            if not isinstance(values,dict) or any(not isinstance(key,str) or not key.isidentifier() or not isinstance(value,str) or not value for key,value in values.items()):
                raise ValueError('invalid private provider input')
            if set(values)&set(defaults):
                raise ValueError('provider input overlaps the tool credential channel')
            defaults.update(values)
            defaults['FACTORY26_PROVIDER_VARIABLES']=json.dumps(sorted(values))
        for key, expected in (public_environment or {}).items():
            if os.environ.get(key) != expected:
                raise ValueError('child environment differs from compiled public policy: ' + key)
        evidence, states['resource_evidence'] = resource(control, require_cgroup=sys.platform.startswith('linux'), owner='runner-payload', package=root)
        receiver, states['collector'] = collector(control, attempt_id, cap_bytes, owner='runner-payload')
        # ``delivery-layout.environment`` is a package/runtime identity in the
        # self-contained projection (for example ``rust-proxy-...``), not an
        # environment mapping.  Public and private environment mappings are
        # already supplied through their explicit channels above.
        layout_environment = delivery_layout.get('environment', {})
        if not isinstance(layout_environment, dict):
            layout_environment = {}
        environment = context(assembly, states, attempt_id, incarnation, control / 'context.json',
            {**defaults,**os.environ,**layout_environment}, public_environment or {})
        if assembly['entry']['mode'] == 'resume':
            environment['FACTORY26_EXP_ASSEMBLY'] = str(control/'assembly.json')
            environment['FACTORY26_EXP_PREPARED_BINDING'] = json.dumps({
                'manifest_path':assembly['entry']['prepared_manifest'],
                'manifest_sha256':assembly['entry']['prepared_manifest_sha256'],
                'run_root':assembly['state']['root'], 'attempt_id':attempt_id, 'assembly_status':'complete'})
        process = subprocess.Popen([sys.executable, assembly['entry']['path'], *argv], env=environment, start_new_session=True)
        sampling = True
        while process.poll() is None:
            if sampling:
                try:
                    evidence.sample('execution-running')
                except Exception as error:
                    report_auxiliary('resource-running-sample', error)
                    sampling = False
            time.sleep(2)
        code = process.wait()
        receipt={'status': 'completed' if code==0 else 'failed', 'exit_code': code, 'definition_root': str(root),
                 'namespace': assembly['namespace'], 'capture_binding':str(control/'source-binding.json') if capture_source else None, 'cleanup':'entry-and-services-owned-by-bootstrap'}
        receipt['auxiliary_errors_path'] = str(auxiliary_path)
        write_result(receipt)
        return code
    except BaseException as error:
        failure={'status':'failed','error':{'type':type(error).__name__,'message':str(error)},
                 'namespace':assembly['namespace'],'definition_root':str(root),
                 'capture_binding':str(control/'source-binding.json') if capture_source else None}
        failure['auxiliary_errors_path'] = str(auxiliary_path)
        write_result(failure)
        raise
    finally:
        if process is not None and process.poll() is None:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
        close(evidence, receiver, on_error=report_auxiliary)


def launch_source(source, runtime, skills, argv, *, output, e2e_runtime=None):
    """Source development uses the same service/entry owner; no hand-written context."""
    from tooling.scripts.runtime import workssd_path
    from tooling.scripts.agent_support import process_identity
    source,runtime,skills=(Path(value).resolve(strict=True) for value in (source,runtime,skills))
    output=workssd_path(output);output.mkdir(parents=True,exist_ok=True)
    support=Path(__file__).resolve().parent
    attempt_id='source-'+str(os.getpid())
    roles=[{'role':name,'local_root':str(root),'member':'.','access':'source-consumer-readback'} for name,root in
        (('agent',source),('runtime',runtime),('skills',skills),('braid',runtime/'bin/braid'),('support',support))]
    declaration=json.loads((source/'materials.json').read_text())
    required=set(declaration.get('definition_roles',[]))
    if required-{'e2e-runtime'}:
        raise ValueError('source entry does not support declared roles: '+','.join(sorted(required-{'e2e-runtime'})))
    if 'e2e-runtime' in required:
        if e2e_runtime is None:
            raise ValueError('source variant requires explicit --e2e-runtime')
        roles.append({'role':'e2e-runtime','local_root':str(Path(e2e_runtime).resolve(strict=True)),'member':'.','access':'source-consumer-readback'})
    assembly={'kind':'factory26.exp.assembly','schema_version':2,'status':'assembled','definition':None,
        'definitions':roles,'namespace':{'kind':'source-local','process':process_identity(os.getpid())},
        'state':{'root':str(output/'.factory26'/attempt_id),'holder':None,'generation':0,'mode':'fresh'},
        'workspace':str(output),'entry':{'mode':'fresh','path':str(source/'main.py')},
        'proof':{'source_selection':'explicit','checkpoint':'unavailable-unpublished-source-definitions'}}
    execution_context.validate_assembly(assembly)
    return _launch_assembly(source,output,attempt_id,'source-process-'+str(os.getpid()),assembly,None,64*1024*1024,argv)
