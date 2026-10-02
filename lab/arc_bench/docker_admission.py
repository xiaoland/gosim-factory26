"""ARC SDK child admission through the daemon-owned exp authority."""
from contextlib import contextmanager
from pathlib import Path

from lab.control import process_identity
from lab.exp.admission import authority
from lab.exp.core import atomic, canonical, read, record


def target(resource):
    return {'endpoint': resource['endpoint'], 'image_id': resource['image_id'],
            'slots': resource['shared_docker_slots'], 'admission_volume': resource['admission_volume'],
            'authority_handoff': resource['authority_handoff']}


@contextmanager
def admit(endpoint, resource):
    """Reserve before launch; only exact physical terminal evidence releases capacity."""
    if endpoint != resource['endpoint']:
        raise ValueError('SDK admission endpoint differs from child binding')
    attempt_id = resource['exp_attempt_id']
    value = authority(target(resource), 'reserve', attempt_id=attempt_id,
                      request_id=resource['exp_request_id'], parameters_sha256=canonical(resource),
                      incarnation=resource['exp_incarnation'], launch_name=resource['container_name'],
                      owner=process_identity())
    atomic(Path(resource['resource_path']).with_suffix('.admission.json'), value)
    yield value
    # Unknown launch windows and absent containers keep their reservation.
    value = authority(target(resource))
    atomic(Path(resource['resource_path']).with_suffix('.admission.json'), value)


def launch(resource):
    return authority(target(resource), 'launch', attempt_id=resource['exp_attempt_id'], incarnation=resource['exp_incarnation'])


def bind(resource, container):
    evidence = {'container_id': container['Id'], 'created': container['Created'],
                'state': container['State'], 'started_at': container['State'].get('StartedAt'), 'labels': container['Config']['Labels']}
    value = authority(target(resource), 'bind', attempt_id=resource['exp_attempt_id'],
                      incarnation=resource['exp_incarnation'], resource=evidence)
    register(resource, evidence)
    return value


def register(resource, evidence):
    root = Path(resource['exp_attempt_dir'])
    path = root / 'external-resources.json'
    existing = read(path) if path.exists() else record('external_resources', resources=[])
    entry = {'backend': {'kind': 'docker', **target(resource)}, 'attempt_id': resource['exp_attempt_id'],
             'incarnation': resource['exp_incarnation'], 'role': resource.get('role', 'execution'), **evidence, 'resource_file': resource['resource_path']}
    prior = [row for row in existing['resources'] if row['attempt_id'] == entry['attempt_id']]
    if prior and any(row['container_id'] != entry['container_id'] or row['created'] != entry['created'] or
                     (row.get('started_at') and not row['started_at'].startswith('0001-') and
                      row['started_at'] != entry.get('started_at')) for row in prior):
        raise ValueError('SDK child execution identity changed')
    existing['resources'] = [row for row in existing['resources'] if row['attempt_id'] != entry['attempt_id']] + [entry]
    atomic(path, existing)
