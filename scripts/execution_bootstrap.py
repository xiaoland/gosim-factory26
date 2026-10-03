"""One namespace owns service creation, entry environment and service closure."""
import os
import json
import signal
import subprocess
import sys
import time
from pathlib import Path

try:
    from . import execution_context
except ImportError:
    import execution_context


def resource(directory, *, require_cgroup=False, owner='runner'):
    try:
        from .agent_support import ResourceEvidence, process_identity
    except ImportError:
        from agent_support import ResourceEvidence, process_identity
    evidence = ResourceEvidence(directory)
    evidence.root_pid = os.getpid()
    evidence.root_starttime = process_identity(os.getpid()).get('starttime')
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


def close(evidence, receiver, *, reason='execution-closed'):
    try:
        if evidence is not None:
            evidence.sample(reason)
    finally:
        if receiver is not None:
            return receiver.close(producer_flush='unknown')


def delivery_assembly(root, output, attempt_id, namespace=None, definition_store=None, definition_bindings=None):
    """Translate only the frozen delivery map; no parent paths or name guessing."""
    root, output = Path(root).resolve(strict=True), Path(output).resolve()
    layout = json.loads((root / 'delivery-layout.json').read_text())
    if layout.get('kind') != 'factory26.harness.delivery' or layout.get('schema_version') != 1:
        raise ValueError('unsupported delivery layout')
    roles = []
    for row in layout['roles']:
        relative = execution_context.member_join('.', row['path'])
        path = root / relative
        if not path.exists() or not path.resolve().is_relative_to(root):
            raise ValueError('delivered definition role is unavailable: ' + row['role'])
        roles.append({'role': row['role'], 'reference': row['reference'], 'member': row['member'],
                      'local_root': str(path), 'access': 'delivered-content-readback'})
    if definition_bindings:
        placements={row['role']:row for row in definition_bindings}
        mapped=[]
        for row in roles:
            placement=placements.get(row['role'])
            if not placement or placement['reference']!=row['reference'] or placement['member']!=row['member'] or placement['access']!='read-only':
                raise ValueError('SDK role lacks its actual frozen read-only binding: '+row['role'])
            local=Path(placement['local_root'])
            if not local.is_absolute() or not local.exists():
                raise ValueError('SDK read-only role is unavailable in this namespace: '+row['role'])
            mapped.append({**row,'store':placement['store'],'local_root':str(local),'access':'read-only'})
        roles=mapped
    if definition_store:
        from lab.exp import artifacts
        roots={}
        installed=[]
        for row in roles:
            reference=row['reference']
            key=json.dumps(reference,sort_keys=True)
            if key not in roots:
                roots[key]=artifacts.resolve(definition_store,reference)
            relative=execution_context.member_join(row['member'],'.')
            artifacts.member_contents(definition_store,reference,relative)
            installed.append({**row,'store':definition_store,'local_root':str(roots[key]/relative),'access':'read-only'})
        roles=installed
    from agent_support import process_identity
    observed = namespace or {'kind': 'delivery-local-scope', 'process': process_identity(os.getpid()),
                             'platform_binding': 'external-controller-only'}
    state = output / '.factory26' / attempt_id
    return {'kind': 'factory26.exp.assembly', 'schema_version': 2, 'status': 'assembled',
            'namespace': observed, 'definitions': roles, 'definition': layout['definition'],
            'state': {'root': str(state), 'mode': 'fresh', 'holder': None, 'generation': 0},
            'workspace': str(output), 'entry': {'mode': 'fresh', 'path': str(execution_context.role({'assembly':{'definitions':roles}},'agent') / 'main.py')},
            'proof': {'delivery': 'explicit-frozen-role-map', 'state_capture': 'capability-dependent'}}


def launch_delivery(root, argv, *, output, namespace=None, public_environment=None, cap_bytes=64 * 1024 * 1024, state_binding=None, capture_source=None, definition_store=None, definition_bindings=None):
    """SDK/Hosted delegate their namespace lifecycle to the same bootstrap."""
    root, output = Path(root).resolve(strict=True), Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    attempt_id = (namespace or {}).get('attempt_id') or os.environ.get('FACTORY26_EXP_ATTEMPT_ID') or ('delivery-' + str(os.getpid()))
    incarnation = (namespace or {}).get('incarnation_id') or (namespace or {}).get('container_id') or ('process-' + str(os.getpid()))
    assembly = delivery_assembly(root, output, attempt_id, namespace, definition_store, definition_bindings)
    if state_binding:
        assembly['state'].update(holder=state_binding,generation=state_binding['generation'])
    if capture_source:
        assembly['proof']['capture_source']=capture_source
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
    try:
        defaults={}
        delivery_layout=json.loads((root/'delivery-layout.json').read_text())
        tool_input=delivery_layout.get('private_inputs',{}).get('tool_env')
        if tool_input:
            private_path=root/execution_context.member_join('.',tool_input['path'])
            defaults=json.loads(private_path.read_text())
            if set(defaults)!={'CONTEXT7_API_KEY','EXA_API_KEY'} or any(not isinstance(value,str) or not value for value in defaults.values()):
                raise ValueError('private tool input must contain the two existing tool credential variables')
        for key, expected in (public_environment or {}).items():
            if os.environ.get(key) != expected:
                raise ValueError('child environment differs from compiled public policy: ' + key)
        evidence, states['resource_evidence'] = resource(control, require_cgroup=sys.platform.startswith('linux'), owner='runner-payload')
        receiver, states['collector'] = collector(control, attempt_id, cap_bytes, owner='runner-payload')
        environment = context(assembly, states, attempt_id, incarnation, control / 'context.json', {**defaults,**os.environ}, public_environment or {key:os.environ[key] for key in ('MODEL','VISUAL_MODEL','OPENAI_BASE_URL','FACTORY26_MODEL_PROVIDER','FACTORY26_MODEL_BINDINGS') if key in os.environ})
        process = subprocess.Popen([sys.executable, assembly['entry']['path'], *argv], env=environment, start_new_session=True)
        while process.poll() is None:
            evidence.sample('execution-running')
            time.sleep(2)
        code = process.wait()
        receipt={'status': 'completed' if code==0 else 'failed', 'exit_code': code, 'definition_root': str(root),
                 'namespace': assembly['namespace'], 'capture_binding':str(control/'source-binding.json') if capture_source else None, 'cleanup':'entry-and-services-owned-by-bootstrap'}
        execution_context.write(result,receipt)
        execution_context.write(output/'.arc/adapter-agent-result.json',receipt)
        return code
    except BaseException as error:
        failure={'status':'failed','error':{'type':type(error).__name__,'message':str(error)},
                 'namespace':assembly['namespace'],'definition_root':str(root),
                 'capture_binding':str(control/'source-binding.json') if capture_source else None}
        execution_context.write(result,failure)
        execution_context.write(output/'.arc/adapter-agent-result.json',failure)
        raise
    finally:
        if process is not None and process.poll() is None:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
        close(evidence, receiver)
