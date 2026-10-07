"""Retained definition composition, independent of delivery and writable state."""
from pathlib import Path

from . import artifacts
from .core import atomic, canonical, member, read


def validate(value):
    if value.get('kind') != 'factory26.harness.definition' or value.get('schema_version') != 1:
        raise ValueError('unsupported definition composition')
    names = set()
    for asset in value['assets']:
        if asset['name'] in names or set(asset['reference']) != {'artifact_id', 'manifest_sha256'}:
            raise ValueError('definition needs unique assets and actual artifact references')
        names.add(asset['name'])
        member(asset.get('member', '.'))
    roles = set()
    for row in value['roles']:
        if row['role'] in roles or row['asset'] not in names:
            raise ValueError('definition role is duplicated or has no asset')
        roles.add(row['role'])
        member(row.get('member', '.'))
    if not {'agent', 'runtime', 'skills', 'braid', 'support'} <= roles:
        raise ValueError('definition is missing a required Harness role')
    return value


def bind(producer, store, cache, consumer):
    """Publish components once; immutable references are the composition's inputs."""
    cache = Path(cache)
    assets = []
    for name, component in producer['components'].items():
        key = canonical([name, component['dependencies'], artifacts.initialize(store)['store_id']])
        index = cache / 'component-index' / (key + '.json')
        if component.get('reference'):
            reference = component['reference']
            source_store = Path(component['store']).resolve(strict=True)
            if source_store != Path(store).resolve(strict=True):
                artifacts.transfer(source_store, store, reference, consumer=consumer,
                                   request_id='component-transfer-' + canonical([consumer, reference,component.get('member','.')]),selected_member=component.get('member','.'))
        elif index.exists():
            row = read(index)
            if row['dependencies'] != component['dependencies']:
                raise ValueError('component production identity was rebound')
            reference = row['reference']
            production_receipt=Path(component['root']).parent/'component.json'
            if production_receipt.exists() and not Path(component['root']).exists():
                published={**component,'reference':reference,'store':str(Path(store).resolve()),'member':'.',
                           'root':str(Path(store).resolve()/reference['artifact_id']/'payload')}
                atomic(production_receipt,published)
                component.update(published)
        else:
            reference = artifacts.publish(store, Path(component['root']), 'harness-' + name,
                provenance={'producer': 'harness.component', 'role': name,
                            'dependencies': component['dependencies'], 'material_id': component['component_id']},
                consumer='component-' + key, purpose='definition-component', request_id='component-' + key, move_source=True)
            atomic(index, {'reference': reference, 'dependencies': component['dependencies']})
            production_receipt=Path(component['root']).parent/'component.json'
            if production_receipt.exists():
                published={**component,'reference':reference,'store':str(Path(store).resolve()),'member':'.',
                           'root':str(Path(store).resolve()/reference['artifact_id']/'payload')}
                atomic(production_receipt,published)
                component.update(published)
        artifacts.retain(store, reference, consumer, 'definition/' + name, 'definition-' + canonical([consumer, name, reference]))
        asset={'name': name, 'reference': reference, 'member': component.get('member', '.')}
        if component['component_id'].startswith('component-'):
            asset['producer_identity']={'kind':'harness.component','id':component['component_id']}
        # A reused runtime keeps its actual producer provenance in the source artifact.
        # Its artifact ID is not recast as a newly invented Harness producer identity.
        assets.append(asset)
    roles = [{'role': name, 'asset': name, 'member': '.'} for name in producer['components']]
    roles.append({'role': 'braid', 'asset': 'runtime', 'member': 'bin/braid'})
    value = validate({'kind': 'factory26.harness.definition', 'schema_version': 1,
        'variant': producer['variant'], 'assets': assets, 'roles': roles,
        'entry': {'fresh': {'role': 'agent', 'member': 'main.py'},
                  'resume': {'role': 'support', 'member': 'recover_completed.py'}},
        'capabilities': producer['capabilities']})
    directory = cache / 'definitions' / canonical(value)
    directory.mkdir(parents=True, exist_ok=True)
    atomic(directory / 'definition.json', value)
    reference = artifacts.publish(store, directory, 'harness-definition',
        provenance={'producer': 'harness.definition', 'material_id': producer['material_id']},
        consumer=consumer, purpose='definition', request_id='definition-' + canonical(value))
    return reference, value


def resolve(value, store, consumer, *, retentions=None, roles=None):
    """One readback per physical artifact in this operation window."""
    validate(value)
    selected=[row for row in value['roles'] if roles is None or row['role'] in roles]
    required={row['asset'] for row in selected}
    roots = {}
    assets = {}
    for asset in value['assets']:
        if asset['name'] not in required:
            continue
        reference = asset['reference']
        key = canonical([reference,asset.get('member','.')])
        if key not in roots:
            retention = (retentions.get(canonical(reference)) if retentions is not None else
                         artifacts.retain(store, reference, consumer, 'definition-assets', 'resolve-' + canonical([consumer, reference])))
            if retention is None:
                raise ValueError('read-only definition input lacks its existing consumer retention')
            roots[key] = artifacts.resolve(store, reference, asset.get('member','.'),consumer=consumer, retention=retention)
        assets[asset['name']] = asset
    result = []
    for role in selected:
        asset = assets[role['asset']]
        from tooling.scripts.execution_context import member_join
        relative = member_join(asset.get('member', '.'), role.get('member', '.'))
        artifacts.member_contents(store, asset['reference'], relative)
        result.append({'role': role['role'], 'reference': asset['reference'], 'member': relative,
            'store': str(store), 'local_root': str(roots[canonical([asset['reference'],asset.get('member','.')])] / role.get('member','.')),
            'access': 'consumer-readback'})
    return result


def bind_private(producer, store, consumer):
    """Retain the existing two-tool defaults as a private execution input."""
    return {name:artifacts.publish(store,row['root'],'private-execution-input',
        provenance={'producer':'harness.private-input','dependencies':row['dependencies']},
        consumer=consumer,purpose='per-attempt-private-input',request_id='tool-input-'+canonical(row['dependencies']))
        for name,row in producer.get('private_inputs',{}).items()}
