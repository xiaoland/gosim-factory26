"""Same-host admission for attempt-owned execution containers on one Docker daemon."""

from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import secrets
import time

from lab.control import process_identity, process_state
from lab.docker_endpoint import confirm, execute
from lab.records import read_json, write_json

LABELS = tuple('io.factory26.' + name for name in ('run', 'attempt', 'stage', 'owner'))


def _key(labels):
    return tuple(labels.get(name) for name in LABELS)


def _directory(endpoint):
    daemon = endpoint.get('daemon_id')
    if not daemon:
        raise ValueError('shared Docker admission requires a frozen daemon ID')
    config = Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config'))
    root = Path(os.environ.get('FACTORY26_DOCKER_ADMISSION_ROOT', config / 'factory26/docker-admission'))
    directory = root.expanduser() / hashlib.sha256(daemon.encode()).hexdigest()
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    return directory


@contextmanager
def _locked(directory):
    with (directory / 'registry.lock').open('a+') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        yield


def _registry(directory, endpoint, slots):
    if type(slots) is not int or slots <= 0:
        raise ValueError('shared Docker slots must be a positive integer')
    path = directory / 'registry.json'
    record = read_json(path) if path.is_file() else {
        'daemon_id': endpoint['daemon_id'], 'slots': slots, 'reservations': []}
    if record['daemon_id'] != endpoint['daemon_id'] or record['slots'] != slots:
        raise ValueError('shared Docker admission daemon or capacity differs from existing registry')
    return record


def _physical(endpoint):
    confirm(endpoint)
    listed = execute(endpoint, ['ps', '--all', '--no-trunc', '--filter',
                               'label=io.factory26.stage', '--format', '{{.ID}}'],
                     text=True, capture_output=True, check=True, timeout=15)
    ids = listed.stdout.split()
    if not ids:
        return []
    # Select ownership/state fields so diagnostic stdout cannot expose container Env.
    fields = ('{"container_id":{{json .Id}},"state":{{json .State}},'
              '"labels":{{json .Config.Labels}},"memory":{{json .HostConfig.Memory}},'
              '"nano_cpus":{{json .HostConfig.NanoCpus}}}')
    inspected = execute(endpoint, ['container', 'inspect', '--format', fields, *ids],
                        text=True, capture_output=True, check=True, timeout=15)
    result = []
    for line in inspected.stdout.splitlines():
        container = json.loads(line)
        state = container['state']
        if state.get('Running') or state.get('Paused') or state.get('Restarting'):
            container['labels'] = container['labels'] or {}
            result.append(container)
    return result


def _capacity(endpoint, record):
    physical = _physical(endpoint)
    occupied = {_key(container['labels']) for container in physical}
    retained = []
    reservations = []
    released = []
    for reservation in record['reservations']:
        state = process_state(reservation['identity'])
        bound = _key(reservation['labels']) in occupied
        if state == 'lost' and not bound:
            released.append(reservation['id'])
            continue
        retained.append(reservation)
        reservations.append({'id': reservation['id'], 'identity_state': state,
                             'bound_to_active_container': bound,
                             'labels': reservation['labels']})
    record['reservations'] = retained
    used = len(physical) + sum(not item['bound_to_active_container'] for item in reservations)
    return {'observed_at': time.time(), 'daemon_id': endpoint['daemon_id'],
            'slots': record['slots'], 'used': used, 'available': max(0, record['slots'] - used),
            'physical': physical, 'reservations': reservations, 'reclaimable_lost': released}


def snapshot(endpoint, slots):
    """Read real capacity without acquiring a lease or changing saved reservations."""
    directory = _directory(endpoint)
    with _locked(directory):
        record = _registry(directory, endpoint, slots)
        return {**_capacity(endpoint, record), 'registry': str(directory / 'registry.json')}


@contextmanager
def admit(endpoint, resource):
    """Hold one launch reservation through execution/finalization; physical runs stay counted."""
    slots = resource.get('shared_docker_slots')
    if slots is None:
        yield None
        return
    directory = _directory(endpoint)
    labels = resource.get('labels', {})
    if any(not isinstance(labels.get(name), str) or not labels[name] for name in LABELS):
        raise ValueError('shared Docker admission requires run/attempt/stage/owner labels')
    identity = process_identity()
    if not identity.get('boot_id') or not identity.get('process_start'):
        raise ValueError(f'cannot reserve Docker capacity without process birth identity: {identity}')
    identifier = secrets.token_hex(16)
    receipt_path = directory / 'receipts' / (identifier + '.json')
    lease = {'id': identifier, 'identity': identity, 'labels': labels,
             'resource': resource.get('resource_path'), 'workspace': resource.get('workspace'),
             'source': resource.get('source'), 'created_at': time.time(),
             'receipt': str(receipt_path)}
    admitted = False
    last = None

    def receipt(status, **facts):
        previous = read_json(receipt_path) if receipt_path.is_file() else {}
        value = {**previous, **lease, 'status': status, 'updated_at': time.time(), **facts}
        write_json(receipt_path, value)
        with receipt_path.with_suffix('.jsonl').open('a') as stream:
            stream.write(json.dumps(value, ensure_ascii=False) + '\n')
            stream.flush()
            os.fsync(stream.fileno())
        if lease['resource']:
            write_json(Path(lease['resource']).with_suffix('.admission.json'), value)

    try:
        while not admitted:
            with _locked(directory):
                record = _registry(directory, endpoint, slots)
                capacity = _capacity(endpoint, record)
                if any(_key(item['labels']) == _key(labels) for item in record['reservations']) or any(
                        _key(item['labels']) == _key(labels) for item in capacity['physical']):
                    raise ValueError('this run/attempt/stage/owner already holds Docker execution capacity')
                if capacity['available']:
                    record['reservations'].append(lease)
                    admitted = True
                write_json(directory / 'registry.json', record)
                signature = (capacity['used'], tuple(item['container_id'] for item in capacity['physical']),
                             tuple((item['id'], item['identity_state']) for item in capacity['reservations']))
                if admitted or signature != last:
                    receipt('admitted' if admitted else 'waiting', capacity=capacity)
                    last = signature
            if not admitted:
                time.sleep(5)
        yield lease
    finally:
        if admitted:
            with _locked(directory):
                record = _registry(directory, endpoint, slots)
                record['reservations'] = [item for item in record['reservations'] if item['id'] != identifier]
                write_json(directory / 'registry.json', record)
            receipt('released')
        elif receipt_path.is_file():
            receipt('not-admitted')
