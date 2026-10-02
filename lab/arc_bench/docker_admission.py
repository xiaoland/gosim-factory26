"""ARC SDK child admission through the daemon-owned exp authority."""
from contextlib import contextmanager
from pathlib import Path

from lab.exp import admission, backends
from lab.exp.core import atomic, locked, read, record


def target(resource):
    return {'endpoint': resource['endpoint'], 'image_id': resource['image_id'],
            'slots': resource['shared_docker_slots'], 'admission_volume': resource['admission_volume']}


def binding(resource, physical=None):
    return {'authority_resource_id': resource['exp_attempt_id'], **(physical or {})}


@contextmanager
def admit(endpoint, resource):
    """Use the shared action authority; unknown effects never release a child slot."""
    if endpoint != resource['endpoint']:
        raise ValueError('SDK admission endpoint differs from child binding')
    value = backends.managed(target(resource), binding(resource), 'reserve', resource['exp_request_id'],
                             {'role': resource.get('role', 'execution'), 'workspace': resource.get('authority_workspace', resource['workspace'])})
    atomic(Path(resource['resource_path']).with_suffix('.admission.json'), value)
    yield value


def create(resource, argv):
    return backends.managed(target(resource), binding(resource), 'create',
                            resource['exp_request_id'] + '-create', {'argv': argv, 'timeout': 600})


def create_volume(resource, argv):
    return backends.managed(target(resource), binding(resource), 'volume-create',
                            resource['exp_request_id'] + '-volume-create', {'argv': argv, 'timeout': 600})


def control(resource, physical, action):
    return backends.managed(target(resource), binding(resource, physical), action,
                            resource['exp_request_id'] + '-' + action,
                            {'grace': 10} if action == 'stop' else {})


def release(resource, physical):
    """Release capacity only after fresh exact terminal evidence and closed writers."""
    selected = target(resource)
    owned = binding(resource, physical)
    observed = backends.domain_observation(selected, owned)
    value = admission.reconcile(selected, resource['exp_attempt_id'],
                                resource['exp_request_id'] + '-release', observed)
    atomic(Path(resource['resource_path']).with_suffix('.release.json'), value)
    return value


def writer(resource, physical, action, request_id):
    return backends.managed(target(resource), binding(resource, physical), action, request_id,
                            {'workspace': resource.get('authority_workspace', resource['workspace'])})


def bind(resource, container):
    evidence = {'container_id': container['Id'], 'created': container['Created'],
                'state': container['State'], 'started_at': container['State'].get('StartedAt'), 'labels': container['Config']['Labels']}
    register(resource, evidence)
    return admission.query(target(resource), resource['exp_attempt_id'])


def register(resource, evidence):
    root = Path(resource['exp_attempt_dir'])
    path = root / 'external-resources.json'
    with locked(root / '.external-resources.lock'):
        existing = read(path) if path.exists() else record('external_resources', resources=[])
        entry = {'authority_resource_id': resource['exp_attempt_id'], 'backend': {'kind': 'docker', **target(resource)}, 'attempt_id': resource['exp_attempt_id'],
                 'incarnation': resource['exp_incarnation'], 'role': resource.get('role', 'execution'), **evidence, 'resource_file': resource['resource_path']}
        prior = [row for row in existing['resources'] if row['attempt_id'] == entry['attempt_id']]
        if prior and any(row['container_id'] != entry['container_id'] or row['created'] != entry['created'] or
                         (row.get('started_at') and not row['started_at'].startswith('0001-') and
                          row['started_at'] != entry.get('started_at')) for row in prior):
            raise ValueError('SDK child execution identity changed')
        existing['resources'] = [row for row in existing['resources'] if row['attempt_id'] != entry['attempt_id']] + [entry]
        atomic(path, existing)
