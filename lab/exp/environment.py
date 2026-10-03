"""Resolve maintained physical profiles without changing frozen experiment policy."""
from copy import deepcopy
from pathlib import Path
import time

from .core import atomic, canonical, digest, locked, read, record, require


def load(path):
    path = Path(path).expanduser().resolve()
    value = require(read(path), 'environment')
    allowed = {'kind', 'schema_version', 'id', 'cache_root', 'python', 'harness', 'arc'}
    if set(value) - allowed or not all(value.get(key) for key in ('id', 'cache_root', 'python')):
        raise ValueError('environment needs id, cache_root and python; unsupported fields are not overrides')
    value = deepcopy(value)
    for field in ('cache_root', 'python'):
        value[field] = str((path.parent / value[field]).expanduser().resolve())
    harness = value.setdefault('harness', {})
    if set(harness) - {'runtime', 'skill_source', 'tool_env', 'e2e_runtime', 'otlp_dependencies', 'provider_env', 'application_seed', 'gateway_routes'}:
        raise ValueError('unsupported harness material selection in environment')
    for field, source in harness.items():
        if isinstance(source, dict):
            if set(source)-{'reference','store','member'} or not {'reference','store'} <= set(source):
                raise ValueError('harness frozen asset needs reference/store/member')
            harness[field] = {**source, 'store': str((path.parent/source['store']).resolve())}
        else:
            harness[field] = str((path.parent / source).expanduser().resolve())
    if 'arc' in value:
        arc = value['arc']
        if not isinstance(arc, dict) or set(arc) != {'sdk_source', 'target'}:
            raise ValueError('environment.arc needs host sdk_source and one child target')
        arc['sdk_source'] = str((path.parent / arc['sdk_source']).expanduser().resolve())
        target = arc['target']
        if isinstance(target.get('authority_handoff'), dict) and set(target['authority_handoff']) == {'source'}:
            target['authority_handoff'] = require(read((path.parent / target['authority_handoff']['source']).resolve(strict=True)), 'authority-handoff')
    return {'profile': str(path), 'profile_sha256': digest(path), 'selection': value}


def resolve(value, profile, *, base=None):
    """Fill intent defaults once; a frozen recipe can only bind identical selections."""
    result = deepcopy(value)
    binding = load(profile)
    if result.get('environment_selection'):
        previous = result['environment_selection']
        if previous['selection'] != binding['selection']:
            raise ValueError('environment changes the declared deployment; compile a derived plan')
        return result
    if result['kind'] != 'factory26.exp.intent':
        raise ValueError('a frozen recipe without an environment selection cannot be overridden by a profile')
    selection = binding['selection']
    base = Path(base or Path(profile).resolve().parent)
    productions = result.setdefault('productions', {})
    for name, production in productions.items():
        if production.get('producer') == 'prepare':
            production['source'] = str((base / production['source']).resolve())
            for category in ('materials', 'nodegyp_tools', 'runtime', 'definition_assets'):
                for row in production['repair'].get(category, []):
                    if 'source' in row:
                        row['source'] = str((base / row['source']).resolve())
                    if 'store' in row:
                        row['store'] = str((base / row['store']).resolve())
            continue
        if production.get('producer') != 'harness':
            raise ValueError('unsupported production: ' + name)
        for field, source in selection['harness'].items():
            production.setdefault(field, source)
        for field in ('runtime', 'skill_source', 'tool_env', 'e2e_runtime', 'otlp_dependencies', 'provider_env', 'application_seed', 'gateway_routes'):
            if field in production:
                if not isinstance(production[field], dict):
                    production[field] = str((base / production[field]).resolve())
    result['environment_selection'] = binding
    return result


def plan_prepare(selection):
    from . import artifacts
    from submission import exp_checkpoint
    if set(selection)-{'producer','source','target','repair'} or not {'producer','source','target','repair'}<=set(selection):
        raise ValueError('prepare production needs explicit source, target and repair')
    source = Path(selection['source']).resolve(strict=True)
    if read(source / 'harness-manifest.json').get('schema_version') not in (3,4):
        raise ValueError('new prepare production requires separated v3 checkpoint')
    dependencies = {'manifest_sha256': digest(source / 'harness-manifest.json'),
                    'hook_sha256': digest(Path(exp_checkpoint.__file__)), 'target': selection['target'],
                    'repair': selection['repair'], 'materials': {}}
    for category in ('materials', 'nodegyp_tools', 'runtime', 'definition_assets'):
        for row in selection['repair'].get(category, []):
            if 'source' in row:
                path = Path(row['source']).resolve()
                dependencies['materials'][str(path)] = artifacts.contents(path)
    return dependencies


def produce_runtimes(binding, purposes, resolution=None, *, verification_window=None):
    """Build missing physical runtime once; preserve separate purpose identities."""
    selection = (resolution or binding)['selection']
    from scripts.runtime import ensure_host_runtime
    result = {}
    for purpose in purposes:
        receipt = ensure_host_runtime(Path(selection['cache_root']), Path(selection['python']), purpose,
                                      expected_dependencies=None, verification_window=verification_window)
        if isinstance(receipt, dict):
            receipt = receipt['receipt']
        result[purpose] = str(receipt)
    return result


def produce_materials(spec, directory, store):
    """Run declared producers; index original producer identities across runs."""
    from . import artifacts
    from scripts.package_agent import produce
    directory = Path(directory)
    productions = spec.get('resolved_productions', spec.get('productions', {}))
    required = {value['from_production'] for job in spec['jobs'] for value in [*job.get('inputs',{}).values(), *[job[field] for field in ('prepared','checkpoint','stop_evidence') if field in job]] if isinstance(value,dict) and 'from_production' in value}
    productions = {name:productions[name] for name in sorted(required)}
    binding = spec.get('environment_selection')
    if productions and not binding:
        raise ValueError('material productions need a frozen environment selection')
    cache = Path(spec.get('environment_resolution', binding)['selection']['cache_root']) if binding else None
    result = {}
    for name, selection in productions.items():
        if selection.get('producer') == 'prepare':
            expected = plan_prepare(selection)
            key = canonical(expected)
            output = cache / 'prepared' / key
            index = cache / 'production-index' / ('prepared-' + key + '.json')
            with locked(index.with_suffix('.lock')):
                if index.exists():
                    material = read(index)
                    artifacts.verify(store, material['artifact'])
                else:
                    from submission.exp_checkpoint import prepare
                    if output.exists():
                        output.rename(output.with_name(key + '-' + str(time.time_ns()) + '-partial'))
                    if (Path(selection['source'])/'domain-resolver.json').exists():
                        from .backends import prepare_snapshot_copy
                        prepared=prepare_snapshot_copy(selection,output,store)
                    else:
                        prepared = prepare(Path(selection['source']), output, selection['target'], selection['repair'], artifact_store=store)
                    ref = artifacts.publish(store, output, 'prepared', provenance={
                        'producer': 'harness.prepare', 'dependencies': expected,
                        'prepared_id': prepared['prepared_id']},
                        consumer='prepare-' + key, purpose='derived-prepared', request_id='prepare-' + key)
                    material = {'artifact': ref, 'producer': prepared, 'dependencies': expected}
                    atomic(index, material)
                consumer = 'run-' + canonical(str(directory.resolve()))
                artifacts.retain(store, material['artifact'], consumer=consumer, purpose='input/' + name,
                                 request_id='retain-' + canonical([consumer, name, material['artifact']]))
            result[name] = material
            continue
        if selection.get('producer') != 'harness' or set(selection) - {
                'producer', 'variant', 'runtime', 'skill_source', 'tool_env', 'e2e_runtime', 'otlp_dependencies', 'provider_env', 'application_seed', 'gateway_routes'}:
            raise ValueError('unsupported material production fields: ' + name)
        parameters = {key: value for key, value in selection.items() if key != 'producer'}
        material = produce(output_store=cache / 'harness',
                           expected_dependencies=None, **parameters)
        from . import definitions, delivery
        consumer = 'run-' + canonical(str(directory.resolve()))
        definition_ref, definition = definitions.bind(material, store, cache, consumer)
        agent = next(asset['reference'] for asset in definition['assets'] if asset['name'] == 'agent')
        result[name] = {'artifact': agent, 'definition': definition_ref, 'definition_value': definition,
                        'producer': material, 'observed_at': time.time()}
        private_inputs=definitions.bind_private(material,store,consumer)
        result[name]['private_inputs']=private_inputs
        result[name]['inputs']={key:artifacts.publish(store,row['root'],'harness-input',consumer=consumer,purpose='input/'+key,provenance={'dependencies':row['dependencies']},request_id='harness-input-'+canonical([key,row['dependencies']])) for key,row in material.get('inputs',{}).items()}
        consumers = [job for job in spec['jobs'] if job.get('inputs', {}).get('agent') == {'from_production': name}]
        if any(job['backend'].get('external_docker') for job in consumers):
            result[name]['delivery'] = delivery.project(definition, store, cache, consumer, private_inputs=private_inputs, inputs=result[name]['inputs'])
        if any(job['backend']['kind'] == 'hosted' for job in consumers):
            result[name]['package'] = delivery.project(definition, store, cache, consumer, zipped=True, private_inputs=private_inputs, inputs=result[name]['inputs'])
    atomic(directory / 'productions.json', record('productions', selections=result))
    return result
