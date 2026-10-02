"""A daemon-local volume owns reservations; uncertainty never releases capacity."""
import json
import hashlib
from pathlib import Path
import subprocess
import os
import socket
import time

from .core import Blocked, atomic, canonical, digest, identifier, read, record, require, process_state
from lab.docker_endpoint import confirm, execute

# The helper runs in the selected daemon, with the same volume on every control host.
HELPER = r'''
import fcntl,json,os,sys,time
from pathlib import Path
root=Path('/authority')
root.mkdir(exist_ok=True)
payload=json.loads(sys.argv[1]); action=payload['action']; now=time.time()
def save(value):
    temporary=root/'registry.next'
    with temporary.open('w') as out:
        json.dump(value,out); out.flush(); os.fsync(out.fileno())
    os.replace(temporary,root/'registry.json')
    fd=os.open(root,os.O_RDONLY); os.fsync(fd); os.close(fd)
with (root/'registry.lock').open('a') as lock:
    fcntl.flock(lock,fcntl.LOCK_EX)
    path=root/'registry.json'
    registry=json.loads(path.read_text()) if path.exists() else {'daemon_id':payload['daemon_id'],'slots':payload['slots'],'helper_sha256':payload['helper_sha256'],'handoff_sha256':payload['handoff_sha256'],'reservations':{}}
    for name in ('daemon_id','slots','helper_sha256','handoff_sha256'):
        if registry[name]!=payload[name]: raise RuntimeError('admission authority mismatch: '+name)
    rows=registry['reservations']; physical=payload['physical']
    # Terminal observations only release a previously bound, exact container birth.
    for row in rows.values():
        for resource in physical:
            if row.get('container_id')==resource['container_id'] and row.get('created')==resource['created'] and row.get('started_at') and not row['started_at'].startswith('0001-') and row['started_at']==resource['state'].get('StartedAt') and all(resource['labels'].get(k)==v for k,v in row['labels'].items()) and resource['state'].get('Status') in ('exited','dead') and not any(resource['state'].get(k) for k in ('Running','Paused','Restarting')):
                row.update(phase='released',release_evidence=resource,released_at=now)
    target=payload.get('attempt_id'); previous=rows.get(target)
    if action=='reserve':
        if previous:
            if previous['request_id']!=payload['request_id'] or previous['parameters_sha256']!=payload['parameters_sha256']: raise RuntimeError('attempt already bound to another dispatch')
        else:
            active=[row for row in rows.values() if row['phase']!='released']
            registered={row.get('container_id') for row in active}
            foreign=[resource for resource in physical if resource['container_id'] not in registered and any(resource['state'].get(k) for k in ('Running','Paused','Restarting'))]
            if len(active)+len(foreign)>=registry['slots']: raise RuntimeError('daemon capacity exhausted or unknown reservation retained')
            rows[target]={'attempt_id':target,'request_id':payload['request_id'],'parameters_sha256':payload['parameters_sha256'],'incarnation':payload['incarnation'],'launch_name':payload['launch_name'],'phase':'accepted','accepted_at':now,'owner':payload['owner']}
    elif action=='launch':
        if not previous or previous['incarnation']!=payload['incarnation']: raise RuntimeError('launch binding mismatch')
        if previous['phase']!='accepted': raise RuntimeError('launch already attempted; observe exact resource instead of retrying')
        previous.update(phase='launch_pending',launch_intent_at=now)
    elif action=='bind':
        if not previous or previous['incarnation']!=payload['incarnation']: raise RuntimeError('resource binding mismatch')
        resource=payload['resource']
        if previous.get('container_id') and previous['container_id']!=resource['container_id']: raise RuntimeError('resource identity changed')
        started=resource['state'].get('StartedAt')
        if previous.get('started_at') and not previous['started_at'].startswith('0001-') and previous['started_at']!=started: raise RuntimeError('execution start instance changed')
        previous.update(phase='materialized',container_id=resource['container_id'],created=resource['created'],started_at=started,labels=resource['labels'],materialized_at=now)
    elif action!='snapshot': raise RuntimeError('unsupported admission action')
    save(registry)
    print(json.dumps({'registry':registry,'reservation':rows.get(target),'observed_at':now}))
'''


def physical(target):
    endpoint = target['endpoint']
    confirm(endpoint)
    ids = execute(endpoint, ['ps', '-a', '--no-trunc', '--filter', 'label=io.factory26.exp.attempt', '--format', '{{.ID}}'],
                  check=True, capture_output=True, text=True, timeout=30).stdout.split()
    if not ids:
        return []
    template = '{"container_id":{{json .Id}},"created":{{json .Created}},"state":{{json .State}},"labels":{{json .Config.Labels}}}'
    output = execute(endpoint, ['inspect', '--format', template, *ids], check=True, capture_output=True, text=True, timeout=30)
    return [json.loads(line) for line in output.stdout.splitlines()]


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


def authority(target, action='snapshot', **fields):
    endpoint = target['endpoint']
    confirm(endpoint)
    handoff = target.get('authority_handoff')
    if not isinstance(handoff, dict):
        raise Blocked('daemon takeover requires a frozen retirement handoff; an empty docker ps is insufficient')
    require(handoff, 'authority-handoff')
    first_use = (handoff.get('mode') == 'first-use' and handoff.get('reservations') == 'absent' and
                 handoff.get('coverage') == 'declared-first-use-scope')
    retired = (handoff.get('reservations') == 'released' and handoff.get('coverage') == 'all-legacy-writers-enumerated')
    if (handoff.get('daemon_id') != endpoint['daemon_id'] or not handoff.get('authorization') or
            handoff.get('launch_windows') != 'closed' or not (first_use or retired)):
        raise Blocked('daemon retirement handoff does not close old writers/reservations/inflight launch windows')
    if first_use:
        scope = require(handoff.get('first_use', {}).get('scope'), 'authority-first-use-scope')
        if (scope.get('daemon_id') != endpoint['daemon_id'] or not scope.get('authorization') or
                scope.get('allow_new_domain') is not True or scope.get('no_other_legacy_domains') is not True or
                scope.get('launch_windows') != 'closed' or not scope.get('writer_scope') or not scope.get('registry_scope') or
                not handoff['first_use'].get('registry_absence') or not handoff['first_use'].get('writer_evidence')):
            raise Blocked('first-use authority scope is incomplete')
    for writer in handoff.get('writers', []):
        if writer.get('effect') != 'stopped' or not writer.get('observation'):
            raise Blocked('legacy writer has no physical stop observation')
        if writer.get('identity') and process_state(writer['identity']) == 'alive':
            raise Blocked('legacy writer remains alive; pause is not retirement')
    volume = identifier(target['admission_volume'])
    if volume != volume_name(endpoint):
        raise Blocked(f'daemon admission authority must use its unique frozen volume: {volume_name(endpoint)}')
    image = target['image_id']
    if not image.startswith('sha256:'):
        raise ValueError('Docker execution and admission require an immutable image ID')
    slots = target['slots']
    if type(slots) is not int or slots < 1:
        raise ValueError('Docker slots must be a positive integer')
    helper_sha256 = canonical(HELPER)
    labels = {'io.factory26.exp.authority': '1', 'io.factory26.exp.daemon': endpoint['daemon_id'],
              'io.factory26.exp.helper': helper_sha256, 'io.factory26.exp.slots': str(slots)}
    args = ['volume', 'create']
    for name, value in labels.items():
        args += ['--label', name + '=' + value]
    execute(endpoint, args + [volume], check=True, capture_output=True, text=True, timeout=30)
    observed = json.loads(execute(endpoint, ['volume', 'inspect', volume], check=True, capture_output=True, text=True, timeout=30).stdout)[0]
    if any((observed.get('Labels') or {}).get(name) != value for name, value in labels.items()):
        raise Blocked('admission volume asset identity differs from the frozen daemon/helper/capacity')
    # Old host-owned reservations cannot be safely counted by the new authority.
    legacy = execute(endpoint, ['ps', '--filter', 'label=io.factory26.stage', '--format', '{{.ID}}'],
                     check=True, capture_output=True, text=True, timeout=30).stdout.strip()
    if legacy:
        raise Blocked(f'legacy execution resources still share daemon admission domain: {legacy}')
    payload = dict(action=action, daemon_id=endpoint['daemon_id'], slots=slots, helper_sha256=helper_sha256,
                   handoff_sha256=canonical(handoff),
                   physical=physical(target), **fields)
    result = execute(endpoint, ['run', '--rm', '-i', '--network', 'none', '--mount', f'type=volume,src={volume},dst=/authority',
                                '--entrypoint', target.get('python', 'python3'), image, '-c', HELPER, json.dumps(payload)],
                     check=True, capture_output=True, text=True, timeout=60)
    return json.loads(result.stdout)
