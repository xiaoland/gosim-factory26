"""A daemon-local volume owns reservations; uncertainty never releases capacity."""
import json
import hashlib
from pathlib import Path
import subprocess
import os
import socket
import sys
import time

from .core import Blocked, atomic, canonical, digest, identifier, read, record, require, process_state, error
from lab.docker_endpoint import confirm, execute

# The helper runs in the selected daemon, with the same volume on every control host.
HELPER = r'''
import fcntl,json,os,sys,time
from pathlib import Path
root=Path('/authority'); payload=json.loads(sys.argv[1]); action=payload['operation']; now=time.time()
def load():
    value=json.loads((root/'registry.json').read_text())
    for name in ('daemon_id','protocol','handoff_sha256','slots'):
        if value[name]!=payload[name]: raise RuntimeError('domain identity mismatch: '+name)
    return value
def save(value):
    temporary=root/'registry.next'
    with temporary.open('w') as out:
        json.dump(value,out);out.flush();os.fsync(out.fileno())
    os.replace(temporary,root/'registry.json');fd=os.open(root,os.O_RDONLY);os.fsync(fd);os.close(fd)
def selection(value):
    rid=payload.get('resource_id'); request=payload.get('request_id')
    return {'domain':{k:value[k] for k in ('daemon_id','protocol','coverage_epoch','maintenance','slots')},
            'resource':value['resources'].get(rid) if rid else None,
            'effect':value['requests'].get(request) if request else None,
            'resources':value['resources'] if not rid else None,
            'workspace':value['workspaces'].get(value['resources'].get(rid,{}).get('workspace')) if rid else None,'observed_at':now}
if action=='query':
    print(json.dumps(selection(load())));sys.exit(0)
with (root/'registry.lock').open('a') as lock:
    fcntl.flock(lock,fcntl.LOCK_EX)
    if action=='initialize':
        if (root/'registry.json').exists():
            value=load()
        else:
            value={'kind':'factory26.exp.managed-domain','schema_version':1,'protocol':2,
                   'daemon_id':payload['daemon_id'],'slots':payload['slots'],'handoff_sha256':payload['handoff_sha256'],
                   'coverage_epoch':1,'maintenance':False,'resources':{},'requests':{},'workspaces':{}}
            save(value)
        print(json.dumps(selection(value)));sys.exit(0)
    value=load()
    if action=='maintenance':
        request=payload['request_id']; mode=payload['mode']; previous=value['requests'].get(request)
        if previous:
            if previous.get('mode')!=mode or previous.get('parameters_sha256')!=payload['parameters_sha256']: raise RuntimeError('maintenance request parameters changed')
            if previous['status']=='applied':
                print(json.dumps(previous));sys.exit(0)
        if mode=='enter':
            value['maintenance']=True
            if any(row['pending'] for row in value['resources'].values()):
                effect={'kind':'factory26.exp.domain-maintenance','schema_version':1,'request_id':request,'mode':mode,'parameters_sha256':payload['parameters_sha256'],'status':'draining','coverage_epoch':value['coverage_epoch']}
                value['requests'][request]=effect;save(value);print(json.dumps(effect));sys.exit(0)
            value['coverage_epoch']+=1
        elif mode=='exit':
            evidence=payload['evidence']
            if not evidence.get('authorization') or evidence.get('daemon_id')!=value['daemon_id'] or evidence.get('writer_scope')!='closed' or evidence.get('launch_windows')!='closed': raise RuntimeError('maintenance exit needs explicit current coverage evidence')
            if any(row['pending'] for row in value['resources'].values()): raise RuntimeError('unresolved domain actions still exist')
            value['maintenance']=False;value['coverage_epoch']+=1
        else: raise RuntimeError('unsupported maintenance transition')
        effect={'kind':'factory26.exp.domain-maintenance','schema_version':1,'request_id':request,'mode':mode,'parameters_sha256':payload['parameters_sha256'],'coverage_epoch':value['coverage_epoch'],'evidence':payload.get('evidence'),'status':'applied','observed_at':now}
        value['requests'][request]=effect;save(value);print(json.dumps(effect));sys.exit(0)
    rid=payload['resource_id']; request=payload['request_id']; parameters=payload.get('parameters',{})
    previous=value['requests'].get(request)
    if previous and (previous['resource_id']!=rid or previous['action']!=payload['action'] or previous['parameters_sha256']!=payload['parameters_sha256']):
        raise RuntimeError('request identity reused with changed action/parameters')
    row=value['resources'].get(rid)
    if action=='begin':
        if previous:
            print(json.dumps(selection(value)));sys.exit(0)
        if value['maintenance'] and payload['action'] not in ('stop','writer-close','capture-end','release'): raise RuntimeError('domain maintenance blocks new creation/start/writers')
        expected=payload.get('expected')
        if expected and (not row or expected['generation']!=row['generation'] or expected['version']!=row['version'] or expected['coverage_epoch']!=value['coverage_epoch']):
            raise RuntimeError('resource observation expired')
        verb=payload['action']
        if verb=='reserve':
            if row: raise RuntimeError('resource already allocated; query original request')
            active=[r for r in value['resources'].values() if r['phase']!='released' and r['role']=='execution']
            role=parameters.get('role','execution')
            if role=='execution' and len(active)>=value['slots']: raise RuntimeError('capacity exhausted, unknown reservations retained')
            if role not in ('execution','copy','query','accessor','build'): raise RuntimeError('unsupported resource role')
            row={'resource_id':rid,'generation':request,'version':0,'phase':'reserved','role':role,'owner':payload['owner'],'pending':None,'identity':None,'workspace':parameters.get('workspace')}
            value['resources'][rid]=row
        elif not row: raise RuntimeError('resource has no reservation')
        if row['phase']=='released': raise RuntimeError('released execution cannot restart; new resource requires new admission')
        if row['pending']: raise RuntimeError('unresolved physical action blocks another transition')
        if verb not in ('reserve','volume-create','create','start','stop','pause','resume','release','writer-open','writer-close','capture-begin','capture-end'):
            raise RuntimeError('unsupported managed action')
        if verb=='create' and row['identity']: raise RuntimeError('resource already materialized')
        if verb=='start' and (not row['identity'] or row['identity'].get('started_at') and not row['identity']['started_at'].startswith('0001-')):
            raise RuntimeError('execution start is single-use; terminal restart forbidden')
        workspace=row.get('workspace')
        if verb=='release' and workspace:
            writers=value['workspaces'].get(workspace,{'writers':[],'capture':None})
            if rid in writers['writers'] or writers['capture']==rid: raise RuntimeError('writer/capture responsibility must close before resource release')
        if verb in ('writer-open','capture-begin','capture-end','writer-close'):
            if not workspace: raise RuntimeError('writer action requires explicit workspace')
            writers=value['workspaces'].setdefault(workspace,{'writers':[],'capture':None})
            if verb=='writer-open' and writers['capture']: raise RuntimeError('workspace capture rejects new writers')
            if verb=='capture-begin' and (writers['capture'] or writers['writers']): raise RuntimeError('workspace still has writers/capture')
            if verb=='writer-open' and rid not in writers['writers']: writers['writers'].append(rid)
            if verb=='capture-begin': writers['capture']=rid
        row['version']+=1
        effect={'kind':'factory26.exp.domain-effect','schema_version':1,'request_id':request,'resource_id':rid,'action':verb,'parameters_sha256':payload['parameters_sha256'],
                'generation':row['generation'],'version':row['version'],'coverage_epoch':value['coverage_epoch'],'status':'pending','intent_at':now,'owner':payload['owner'],'parameters':parameters}
        row['pending']=request;value['requests'][request]=effect
    elif action=='complete':
        if not previous: raise RuntimeError('physical effect has no accepted intent')
        if previous['status']!='pending':
            print(json.dumps(selection(value)));sys.exit(0)
        if row['pending']!=request: raise RuntimeError('pending action identity changed')
        physical=payload.get('physical'); verb=previous['action']
        if verb=='volume-create':
            physical=payload.get('physical')
            if not physical or not physical.get('Name') or not physical.get('Labels'): raise RuntimeError('volume materialization requires asset readback')
            row['volume']=physical
        if verb in ('create','start','stop','pause','resume','release'):
            if not physical: raise RuntimeError('physical action requires exact readback')
            old=row['identity']
            if old and any(old.get(k)!=physical.get(k) for k in ('container_id','created','labels')): raise RuntimeError('physical object birth/ownership changed')
            started=physical['state'].get('StartedAt')
            if old and old.get('started_at') and not old['started_at'].startswith('0001-') and old['started_at']!=started: raise RuntimeError('execution restarted outside domain authority')
            if verb=='start' and (not started or started.startswith('0001-')): raise RuntimeError('start effect unconfirmed')
            if verb in ('stop','release') and physical['state'].get('Status') not in ('exited','dead'): raise RuntimeError('physical terminal effect unconfirmed')
            if verb=='pause' and not physical['state'].get('Paused'): raise RuntimeError('pause effect unconfirmed')
            if verb=='resume' and (physical['state'].get('Paused') or not physical['state'].get('Running')): raise RuntimeError('resume effect unconfirmed')
            row['identity']={**physical,'started_at':started};row['phase']='released' if verb=='release' else 'terminal' if verb=='stop' else 'materialized' if verb=='create' else 'active'
        workspace=row.get('workspace')
        if verb in ('writer-open','writer-close','capture-begin','capture-end'):
            writers=value['workspaces'][workspace]
            if verb=='writer-close': writers['writers']=[r for r in writers['writers'] if r!=rid]
            if verb=='capture-begin': writers['capture']=rid
            if verb=='capture-end': writers['capture']=None
        previous.update(status='applied',physical=physical,result=payload.get('result'),effect_at=now)
        row['pending']=None
    else: raise RuntimeError('unsupported domain operation')
    save(value);response=selection(value);response['accepted_now']=action=='begin';print(json.dumps(response))
'''


def physical(target):
    endpoint = target['endpoint']
    confirm(endpoint)
    ids = execute(endpoint, ['ps', '-a', '--no-trunc', '--filter', 'label=io.factory26.exp.attempt', '--format', '{{.ID}}'],
                  check=True, capture_output=True, text=True, timeout=30).stdout.split()
    if not ids:
        return []
    template = '{"container_id":{{json .Id}},"created":{{json .Created}},"state":{{json .State}},"labels":{{json .Config.Labels}}}'
    for timeout in (30, 60):
        try:
            output = execute(endpoint, ['inspect', '--format', template, *ids],
                             check=True, capture_output=True, text=True, timeout=timeout)
            return [json.loads(line) for line in output.stdout.splitlines()]
        except subprocess.TimeoutExpired as exc:
            if timeout == 60:
                raise
            # This GET precedes the authority mutation; retrying cannot dispatch a container.
            print(json.dumps({'admission_physical_read_retry': error(exc)}), file=sys.stderr, flush=True)


def volume_name(endpoint):
    return 'exp-admission-' + hashlib.sha256(endpoint['daemon_id'].encode()).hexdigest()[:24]


def _first_use(endpoint, scope_path, writers):
    """Consume explicit ownership coverage and original absence observations."""
    scope = require(read(scope_path), 'authority-first-use-scope')
    if (scope.get('daemon_id') != endpoint['daemon_id'] or not scope.get('authorization') or
            scope.get('allow_new_domain') is not True or scope.get('no_other_legacy_domains') is not True or
            scope.get('launch_windows') != 'closed' or not scope.get('writer_scope') or not scope.get('registry_scope')):
        raise Blocked('first-use needs explicit new-domain authorization and closed, declared writer/registry coverage')
    if not isinstance(scope.get('writer_sources'), list) or sorted(str(Path(p).resolve()) for p in scope['writer_sources']) != sorted(str(Path(p).resolve()) for p in writers):
        raise Blocked('first-use writer_sources must explicitly equal the supplied writer scope, including an explicit empty list')
    if not isinstance(scope.get('local_registry_paths'), list):
        raise Blocked('first-use must explicitly declare local registry paths, including an explicit empty list')
    absence = []
    for path in scope['local_registry_paths']:
        location = Path(path).expanduser().absolute()
        try:
            os.lstat(location)
        except FileNotFoundError:
            absence.append({'host': socket.gethostname(), 'path': str(location), 'effect': 'absent',
                            'producer': 'local-lstat', 'observed_at': time.time()})
        else:
            raise Blocked(f'first-use local registry already exists: {location}')
    for row in scope.get('registry_absence', []):
        location = Path(row['source']).expanduser().resolve(strict=True)
        raw = read(location)
        if 'stdout' in raw:
            if raw.get('exit_code') != 0:
                raise Blocked('registry observation command failed')
            raw = json.loads(raw['stdout'])
        info = raw.get('info', {})
        if info.get('exit_code') != 0 or json.loads(info['stdout']).get('ID') != endpoint['daemon_id']:
            raise Blocked('registry absence source does not bind the target daemon')
        matches = [item for item in raw.get('registries', []) if item.get('path') == row['path']]
        if raw.get('hostname') != row['host'] or len(matches) != 1 or matches[0].get('exists') is not False:
            raise Blocked('declared registry path has no original absent observation')
        absence.append({'host': row['host'], 'path': row['path'], 'source': str(location),
                        'sha256': digest(location), 'effect': 'absent'})
    if not absence or not scope.get('evidence'):
        raise Blocked('first-use requires registry absence originals and writer coverage evidence')
    evidence = [{'source': str(Path(p).resolve(strict=True)), 'sha256': digest(p)} for p in scope['evidence']]
    # Scan all objects without reading Env. Label/name coverage is bounded; the
    # explicit owner declaration closes custom domains, not this scan alone.
    containers = execute(endpoint, ['ps', '-a', '--no-trunc', '--format', '{{.ID}}'],
                         check=True, capture_output=True, text=True, timeout=30).stdout.split()
    facts = []
    if containers:
        template = '{"id":{{json .Id}},"name":{{json .Name}},"labels":{{json .Config.Labels}}}'
        facts = [json.loads(line) for line in execute(endpoint, ['inspect', '--format', template, *containers],
                 check=True, capture_output=True, text=True, timeout=30).stdout.splitlines()]
    names = execute(endpoint, ['volume', 'ls', '--format', '{{.Name}}'],
                    check=True, capture_output=True, text=True, timeout=30).stdout.split()
    volumes = json.loads(execute(endpoint, ['volume', 'inspect', *names], check=True,
                         capture_output=True, text=True, timeout=30).stdout) if names else []
    def factory(name, labels):
        return name.lstrip('/').startswith(('factory26', 'exp-admission-')) or any(
            key.startswith('io.factory26.') for key in (labels or {}))
    if any(factory(row['name'], row['labels']) for row in facts) or any(
            factory(row['Name'], row.get('Labels')) for row in volumes):
        raise Blocked('first-use domain contains existing Factory resources; use retirement handoff')
    return {'scope': scope, 'scope_source': str(Path(scope_path).resolve()), 'scope_sha256': digest(scope_path),
            'registry_absence': absence, 'writer_evidence': evidence,
            'physical': {'containers': facts, 'volumes': [{'name': row['Name'], 'labels': row.get('Labels')} for row in volumes]},
            'coverage_limit': 'declared hosts and paths plus Factory label/name scan; custom domains require owner authorization'}


def handoff(endpoint, writers, registry, output, authorization, *, mode='retirement', scope=None):
    """Read an explicitly complete retirement scope; never stop or release anything."""
    confirm(endpoint)
    if not authorization.strip() or Path(output).exists():
        raise ValueError('handoff needs explicit scope and a fresh output')
    observed = []
    for location in writers:
        value = read(location)
        identity = value.get('identity', value)
        state = process_state(identity)
        if state != 'lost':
            raise Blocked(f'legacy writer is {state}, not physically retired: {location}')
        observed.append({'identity': identity, 'effect': 'stopped', 'observation': {'identity_state': state},
                         'source': str(Path(location).resolve()), 'sha256': digest(location)})
    if mode == 'first-use':
        if registry is not None or scope is None:
            raise ValueError('first-use requires --scope and forbids a synthetic --registry')
        basis = _first_use(endpoint, scope, writers)
        value = record('authority-handoff', mode=mode, daemon_id=endpoint['daemon_id'], authorization=authorization,
                       coverage='declared-first-use-scope', writers=observed, reservations='absent', launch_windows='closed',
                       first_use=basis, observed_at=time.time())
        atomic(output, value)
        return value
    if mode != 'retirement' or registry is None or scope is not None:
        raise ValueError('retirement requires an actual --registry; first-use is a separate explicit mode')
    reservations = read(registry)
    if reservations.get('daemon_id') != endpoint['daemon_id'] or reservations.get('reservations') not in ([], {}):
        raise Blocked('legacy registry is not explicitly empty for this daemon; no capacity is released here')
    active = execute(endpoint, ['ps', '--filter', 'label=io.factory26.stage', '--no-trunc', '--format', '{{.ID}}'],
                     check=True, capture_output=True, text=True, timeout=30).stdout.strip()
    if active:
        raise Blocked('legacy physical resources remain: ' + active)
    value = record('authority-handoff', daemon_id=endpoint['daemon_id'], authorization=authorization,
                   coverage='all-legacy-writers-enumerated', writers=observed, reservations='released', launch_windows='closed',
                   registry={'source': str(Path(registry).resolve()), 'sha256': digest(registry)}, observed_at=time.time())
    atomic(output, value)
    return value


def _target(target):
    endpoint = target['endpoint']
    handoff = target.get('authority_handoff')
    if handoff is not None:
        require(handoff, 'authority-handoff')
        covered = (handoff.get('reservations') == 'released' and handoff.get('coverage') == 'all-legacy-writers-enumerated') or (handoff.get('mode') == 'first-use' and handoff.get('reservations') == 'absent' and handoff.get('coverage') == 'declared-first-use-scope')
        if not covered or handoff.get('daemon_id') != endpoint['daemon_id'] or not handoff.get('authorization') or handoff.get('launch_windows') != 'closed':
            raise Blocked('domain requires frozen writer/reservation handoff coverage')
    if target['admission_volume'] != volume_name(endpoint):
        raise Blocked('daemon authority requires its uniquely derived volume')
    if not target['image_id'].startswith('sha256:'):
        raise ValueError('authority helper requires frozen image ID')
    if type(target.get('slots')) is not int or target['slots'] < 1:
        raise ValueError('domain slots must be a frozen positive integer')
    return endpoint, {'daemon_id': endpoint['daemon_id'], 'protocol': 2, 'handoff_sha256': canonical(handoff) if handoff is not None else None, 'slots': target['slots']}


def _helper(target, payload, *, readonly=False):
    endpoint, identity = _target(target)
    confirm(endpoint)
    volume = target['admission_volume']
    raw = execute(endpoint, ['volume', 'inspect', volume], check=True, capture_output=True, text=True, timeout=30)
    asset = json.loads(raw.stdout)[0]
    if asset.get('Driver') != 'local' or asset.get('Options') or not asset.get('Mountpoint'):
        raise Blocked('domain query requires supported Linux local-volume without driver options')
    labels = asset.get('Labels') or {}
    if labels.get('io.factory26.exp.daemon') != endpoint['daemon_id'] or labels.get('io.factory26.exp.protocol') != '2':
        raise Blocked('domain volume identity differs; legacy authority is not silently upgraded')
    handoff_digest = labels.get('io.factory26.exp.handoff')
    if not handoff_digest or identity['handoff_sha256'] and identity['handoff_sha256'] != handoff_digest:
        raise Blocked('domain handoff asset binding differs or is missing')
    identity['handoff_sha256'] = handoff_digest
    owner_id = canonical([payload, time.time_ns()])[:24]
    args = ['create', '--user', '0', '--restart', 'no', '--network', 'none', '--memory', '128m', '--pids-limit', '32',
            '--label', 'io.factory26.exp.role=query', '--label', 'io.factory26.exp.query-owner=' + owner_id, '--mount',
            'type=bind,src=' + asset['Mountpoint'] + ',dst=/authority' + (',readonly' if readonly else ''),
            '--entrypoint', target.get('python', 'python3'), target['image_id'], '-B', '-c', HELPER, json.dumps({**identity, **payload})]
    helper_id = None
    failure = None
    try:
        # Docker object names provide four daemon-wide query-channel slots, without registry mutation.
        for index in range(4):
            name = 'exp-domain-channel-' + hashlib.sha256(endpoint['daemon_id'].encode()).hexdigest()[:16] + '-' + str(index)
            created = execute(endpoint, args[:1] + ['--name', name] + args[1:], capture_output=True, text=True, timeout=30)
            if created.returncode == 0:
                helper_id = created.stdout.strip()
                break
            if 'already in use' not in created.stderr:
                raise subprocess.CalledProcessError(created.returncode, created.args, output=created.stdout, stderr=created.stderr)
        if helper_id is None:
            raise Blocked('all four domain query channels are occupied or uncertain; no load reservation changed')
        output = execute(endpoint, ['start', '--attach', helper_id], check=True, capture_output=True, text=True, timeout=60)
        return json.loads(output.stdout)
    except Exception as exc:
        failure = exc
        raise
    finally:
        if helper_id:
            try:
                inspected = execute(endpoint, ['inspect', '--format', '{{index .Config.Labels "io.factory26.exp.query-owner"}}', helper_id], capture_output=True, text=True, timeout=30)
                if inspected.returncode == 0 and inspected.stdout.strip() == owner_id:
                    cleanup = execute(endpoint, ['rm', '--force', helper_id], capture_output=True, text=True, timeout=30)
                    cleanup_error = cleanup.stderr if cleanup.returncode else None
                else:
                    cleanup_error = 'query helper ownership could not be confirmed'
            except Exception as cleanup_exc:
                cleanup_error = str(cleanup_exc)
            if cleanup_error and failure is not None:
                failure.add_note(cleanup_error)
            elif cleanup_error:
                raise Blocked(cleanup_error)


def initialize(target):
    """Explicit domain owner action; routine query/reserve never initialize a missing asset."""
    endpoint, identity = _target(target)
    confirm(endpoint)
    if not identity['handoff_sha256']:
        raise Blocked('only domain initialization requires explicit complete authority handoff')
    args = ['volume', 'create', '--label', 'io.factory26.exp.handoff=' + identity['handoff_sha256'], '--label', 'io.factory26.exp.daemon=' + endpoint['daemon_id'],
            '--label', 'io.factory26.exp.protocol=2', target['admission_volume']]
    execute(endpoint, args, check=True, capture_output=True, text=True, timeout=30)
    return _helper(target, {'operation': 'initialize', 'slots': target['slots']})


def query(target, resource_id=None, request_id=None):
    return _helper(target, {'operation': 'query', 'resource_id': resource_id, 'request_id': request_id}, readonly=True)


def action(target, resource_id, request_id, action, parameters, owner=None, expected=None):
    identifier(resource_id); identifier(request_id)
    from .core import process_identity
    return _helper(target, {'operation': 'begin', 'resource_id': resource_id, 'request_id': request_id,
                           'action': action, 'parameters': parameters, 'parameters_sha256': canonical(parameters),
                           'owner': owner or process_identity(), 'expected': expected})


def complete(target, resource_id, request_id, action, parameters, *, physical=None, result=None):
    return _helper(target, {'operation': 'complete', 'resource_id': resource_id, 'request_id': request_id,
                           'action': action, 'parameters': parameters, 'parameters_sha256': canonical(parameters),
                           'physical': physical, 'result': result})


def reconcile(target, resource_id, request_id, observed):
    """Apply only an observation whose action version was acquired before physical inspection."""
    row = observed['resource']
    if row['pending']:
        raise Blocked('unresolved action cannot be released from a terminal snapshot')
    parameters = {'observation': observed['physical']}
    value = action(target, resource_id, request_id, 'release', parameters, expected={
        'generation': row['generation'], 'version': row['version'], 'coverage_epoch': observed['domain']['coverage_epoch']})
    if value['effect']['status'] == 'applied':
        return value
    return complete(target, resource_id, request_id, 'release', parameters, physical=observed['physical'])


def maintenance(target, request_id, mode, evidence=None):
    """Explicit owner transition; closing coverage blocks starts but permits draining existing resources."""
    identifier(request_id)
    return _helper(target, {'operation': 'maintenance', 'request_id': request_id, 'mode': mode,
                           'evidence': evidence, 'parameters_sha256': canonical([mode, evidence])})


def authority(target, action='snapshot', **fields):
    """The old reserve/launch/bind writer is unavailable under the new domain protocol."""
    raise Blocked('domain protocol 2 requires query/action/complete; legacy execution uses its frozen executor')
