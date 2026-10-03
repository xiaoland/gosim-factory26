"""Fresh and restored entries consume the same namespace-local assembly."""
from pathlib import Path
import os
import socket

from . import definitions
from .core import atomic, digest, identifier, process_identity, read, record


def install_aliases(roles, base, *, state_binding=None, expected=None):
    """Replace only this holder's recorded aliases under its actual capture lease."""
    base = Path(base).absolute()
    base.mkdir(parents=True, exist_ok=True)
    receipt = base / 'placements.json'
    previous = read(receipt) if receipt.exists() else {'kind': 'factory26.definition.placements', 'roles': []}
    prior = {row['role']: row for row in previous['roles']}
    if state_binding:
        from . import state
        holder = state.query(state_binding)['holder']
        if holder['phase'] != 'repairing' or not holder.get('capture'):
            raise ValueError('definition alias replacement requires this holder capture repair lease')
    result = []
    for row in roles:
        role = identifier(row['role'])
        physical = Path(row.get('physical_root', row['local_root'])).resolve(strict=True)
        target = base / role
        if target.exists() or target.is_symlink():
            old = prior.get(role)
            if not old or old['local_root'] != str(target) or not target.is_symlink():
                raise ValueError('definition role path is not this holder recorded alias: ' + role)
            if not target.samefile(physical):
                source = (expected or {}).get(role)
                if not state_binding or not source or old['reference'] != source['reference'] or old['member'] != source['member']:
                    raise ValueError('definition replacement lacks exact original ref/member and capture lease: ' + role)
                temporary = base / ('.' + role + '.next')
                if temporary.is_symlink():
                    if temporary.resolve() != physical:
                        raise ValueError('unfinished alias replacement points at another asset')
                else:
                    temporary.symlink_to(physical, target_is_directory=physical.is_dir())
                temporary.replace(target)
        else:
            target.symlink_to(physical, target_is_directory=physical.is_dir())
        result.append({**row, 'physical_root': str(physical), 'local_root': str(target)})
    atomic(receipt, {'kind': 'factory26.definition.placements', 'schema_version': 1, 'roles': result})
    descriptor = os.open(base, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    return result, {'base': str(base), 'receipt_sha256': digest(receipt)}


def namespace(directory, attempt, deployment):
    if deployment.get('namespace'):
        return deployment['namespace']
    if attempt['job']['backend']['kind'] == 'docker':
        raise ValueError('Docker payload needs its actual container namespace binding')
    return {'kind': 'local', 'host': socket.gethostname(), 'process': process_identity(),
            'device': Path(directory).stat().st_dev}


def fresh(directory, attempt, deployment):
    directory = Path(directory)
    workspace = directory / 'workspace'
    workspace.mkdir(exist_ok=True)
    roles, definition = [], None
    if attempt['job'].get('definition') and not attempt['job']['backend'].get('external_docker'):
        definition = attempt['job']['definition']
        value = read(directory / 'inputs/definition/definition.json')
        roles = definitions.resolve(value, attempt['artifact_store'], attempt['attempt_id'],
            retentions=deployment.get('input_retentions') if attempt['job']['backend']['kind']=='docker' else None)
    layout = None
    holder_id = (deployment.get('state_binding') or {}).get('holder_id', attempt['attempt_id'])
    if roles:
        if attempt['job']['backend']['kind'] == 'docker':
            installed = {row['role']: row for row in deployment.get('definition_bindings', [])}
            mapped = []
            for row in roles:
                placement = installed.get(row['role'])
                if not placement or placement['reference'] != row['reference'] or placement['member'] != row['member'] or placement['access'] != 'read-only':
                    raise ValueError('fresh Docker definition lacks actual read-only placement: ' + row['role'])
                root = Path(placement['logical_root'])
                if not root.samefile(row['local_root']):
                    raise ValueError('Docker mounted definition differs from retained source')
                mapped.append({**row, 'physical_root': row['local_root'], 'local_root': str(root), 'access': 'read-only'})
            roles = mapped
            layout = deployment.get('definition_layout')
        else:
            roles, layout = install_aliases(roles, directory.parent.parent / 'definition-layouts' / holder_id)
    state_root = workspace / '.factory26' / attempt['attempt_id'] if roles else workspace
    value = record('assembly', schema_version=2, status='assembled', definition=definition,
        definitions=roles, namespace=namespace(directory, attempt, deployment),
        state={'root': str(state_root), 'holder': deployment.get('state_binding'),
               'generation': (deployment.get('state_binding') or {}).get('generation', 0), 'mode': 'fresh'},
        entry={'mode': 'fresh', 'command': attempt['job']['command']}, workspace=str(workspace),
        proof={'inputs': 'retained-artifact-consumer-readback', 'definition_layout': layout})
    from scripts.execution_context import validate_assembly
    validate_assembly(value)
    atomic(directory / 'assembly.json', value)
    return workspace


def initialize_state(directory, attempt, deployment, value, binding):
    from . import state
    holder = deployment.get('state_binding')
    if holder is None and attempt['job']['backend']['kind']=='local':
        writer={'resource_id':attempt['attempt_id'],'attempt_id':attempt['attempt_id'],'incarnation':binding['incarnation_id']}
        namespace=value['namespace']
        domain={'kind':'local','host':namespace['host'],'device':namespace['device']}
        holder={'authority':{'kind':'local','root':str(Path(directory).parents[1]/'state-authority'),'workspace':attempt['attempt_id']},
                'holder_id':attempt['attempt_id'],'domain_identity':domain,'source_attempt_directory':str(Path(directory).resolve()),
                'locator':{'kind':'local','path':value['state']['root']}, 'writer':writer,'generation':1}
        state.initialize(holder,writer,{'protocol':'managed-writers-v1','entry_contract':'local-registered-native-and-owner-shutdown-v1',
            'external_children':'explicit-domain-relations-required' if attempt['job']['backend'].get('external_docker') else 'none'},attempt['attempt_id']+'--initialize-state')
        deployment['state_binding']=holder
        atomic(Path(directory)/'deployment.json',deployment)
    if holder and holder['authority']['kind']=='local' and holder['writer']['incarnation']!=binding['incarnation_id']:
        writer={'resource_id':attempt['attempt_id'],'attempt_id':attempt['attempt_id'],'incarnation':binding['incarnation_id']}
        holder={**holder,'writer':writer}
        state.handoff_for_execution(holder,writer,value,attempt['attempt_id']+'--handoff')
        deployment['state_binding']=holder
        atomic(Path(directory)/'deployment.json',deployment)
    if holder:
        if holder['authority']['kind']=='docker':
            permit=deployment.get('state_permit')
            if not permit or permit['holder_id']!=holder['holder_id'] or permit['generation']!=holder['generation'] or permit['writer']!=holder['writer']:
                raise ValueError('Docker payload lacks its authority-accepted current entry permit')
            actual=value['namespace']
            physical=permit['resource']
            if physical['container_id']!=actual['container_id'] or physical['created']!=actual['created']:
                raise ValueError('Docker entry permit belongs to another physical namespace')
        else:
            state.permit(holder,holder['writer']['resource_id'],binding['incarnation_id'],holder['generation'])
        value['state'].update(holder=holder,generation=holder['generation'])
        atomic(Path(directory)/'assembly.json',value)
    return value


def prepared(directory, attempt, deployment, value):
    """Preserve old logical-root checks; normalize their actual installation proof."""
    roles = []
    for row in value['definitions']:
        roles.append({**row, 'role': row['name'], 'reference': row['artifact'],
                      'member': row.get('member', '.'), 'local_root': row['logical_root']})
    value.update(schema_version=2, definitions=roles,
        namespace=namespace(directory, attempt, deployment),
        state={'root': value['workspace'], 'holder': deployment.get('state_binding'),
               'generation': (deployment.get('state_binding') or {}).get('generation', 0), 'mode': value.get('state_mode', 'snapshot-copy')},
        entry={'mode': 'resume', 'command': attempt['job']['command']},
        proof={'prepared': attempt['job']['prepared'], 'installation': 'content-and-native-readback'})
    from scripts.execution_context import validate_assembly
    validate_assembly(value)
    atomic(Path(directory) / 'assembly.json', value)
    return value
