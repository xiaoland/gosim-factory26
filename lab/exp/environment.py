"""Resolve maintained physical profiles without changing frozen experiment policy."""
from copy import deepcopy
from pathlib import Path
import time

from .core import atomic, canonical, digest, locked, read, record, require


def load(path):
    path = Path(path).expanduser().resolve(strict=True)
    value = require(read(path), 'environment')
    allowed = {'kind', 'schema_version', 'id', 'cache_root', 'python', 'harness', 'arc'}
    if set(value) - allowed or not all(value.get(key) for key in ('id', 'cache_root', 'python')):
        raise ValueError('environment needs id, cache_root and python; unsupported fields are not overrides')
    value = deepcopy(value)
    for field in ('cache_root', 'python'):
        value[field] = str((path.parent / value[field]).expanduser().resolve())
    harness = value.setdefault('harness', {})
    if set(harness) - {'runtime', 'skill_source', 'tool_env', 'e2e_runtime', 'otlp_dependencies'}:
        raise ValueError('unsupported harness material selection in environment')
    for field, source in harness.items():
        harness[field] = str((path.parent / source).expanduser().resolve(strict=True))
    if 'arc' in value:
        arc = value['arc']
        if not isinstance(arc, dict) or set(arc) != {'sdk_source', 'target'}:
            raise ValueError('environment.arc needs host sdk_source and one child target')
        arc['sdk_source'] = str((path.parent / arc['sdk_source']).expanduser().resolve(strict=True))
        target = arc['target']
        if isinstance(target.get('authority_handoff'), dict) and set(target['authority_handoff']) == {'source'}:
            target['authority_handoff'] = require(read((path.parent / target['authority_handoff']['source']).resolve(strict=True)), 'authority-handoff')
    return {'profile': str(path), 'profile_sha256': digest(path), 'selection': value,
            'python_sha256': digest(Path(value['python']).resolve(strict=True))}


def resolve(value, profile, *, base=None):
    """Fill intent defaults once; a frozen recipe can only bind identical selections."""
    result = deepcopy(value)
    binding = load(profile)
    if result.get('environment_selection'):
        previous = result['environment_selection']
        from scripts.runtime import plan_host_runtime
        from scripts.package_agent import plan_material
        if (binding['python_sha256'] != previous['python_sha256'] or
                plan_host_runtime(Path(binding['selection']['python']))['dependencies'] != previous['runtime_dependencies']):
            raise ValueError('environment changes frozen runtime dependencies; compile a derived recipe')
        if binding['selection'].get('arc') != previous['selection'].get('arc'):
            raise ValueError('environment changes frozen ARC SDK/target; compile a derived recipe')
        resolved = deepcopy(result.get('productions', {}))
        for name, production in resolved.items():
            if production['producer'] == 'harness':
                for field, origin in previous['selection']['harness'].items():
                    if production.get(field) == origin and field in binding['selection']['harness']:
                        production[field] = binding['selection']['harness'][field]
                observed = plan_material(**{key: item for key, item in production.items() if key != 'producer'})
            else:
                observed = plan_prepare(production)
            if observed != previous['material_dependencies'][name]:
                raise ValueError('environment changes frozen material dependencies: ' + name)
        if any(previous.get(key) != item for key, item in binding.items()):
            result['environment_resolution'] = binding
            result['resolved_productions'] = resolved
        return result
    if result['kind'] != 'factory26.exp.intent':
        raise ValueError('a frozen recipe without an environment selection cannot be overridden by a profile')
    selection = binding['selection']
    base = Path(base or Path(profile).resolve().parent)
    productions = result.setdefault('productions', {})
    for name, production in productions.items():
        if production.get('producer') == 'prepare':
            production['source'] = str((base / production['source']).resolve(strict=True))
            for category in ('materials', 'nodegyp_tools', 'runtime', 'definition_assets'):
                for row in production['repair'].get(category, []):
                    if 'source' in row:
                        row['source'] = str((base / row['source']).resolve(strict=True))
                    if 'store' in row:
                        row['store'] = str((base / row['store']).resolve(strict=True))
            continue
        if production.get('producer') != 'harness':
            raise ValueError('unsupported production: ' + name)
        for field, source in selection['harness'].items():
            production.setdefault(field, source)
        for field in ('runtime', 'skill_source', 'tool_env', 'e2e_runtime', 'otlp_dependencies'):
            if field in production:
                production[field] = str((base / production[field]).resolve(strict=True))
    result['environment_selection'] = binding
    from scripts.runtime import plan_host_runtime
    from scripts.package_agent import plan_material
    binding['runtime_dependencies'] = plan_host_runtime(Path(selection['python']))['dependencies']
    for name, production in productions.items():
        binding.setdefault('material_dependencies', {})[name] = (
            plan_prepare(production) if production['producer'] == 'prepare' else plan_material(
                **{key: value for key, value in production.items() if key != 'producer'}))
    return result


def plan_prepare(selection):
    from . import artifacts
    from submission import exp_checkpoint
    if set(selection) != {'producer', 'source', 'target', 'repair'}:
        raise ValueError('prepare production needs explicit source, target and repair')
    source = Path(selection['source']).resolve(strict=True)
    if read(source / 'harness-manifest.json').get('schema_version') != 3:
        raise ValueError('new prepare production requires separated v3 checkpoint')
    dependencies = {'manifest_sha256': digest(source / 'harness-manifest.json'),
                    'hook_sha256': digest(Path(exp_checkpoint.__file__)), 'target': selection['target'],
                    'repair': selection['repair'], 'materials': {}}
    for category in ('materials', 'nodegyp_tools', 'runtime', 'definition_assets'):
        for row in selection['repair'].get(category, []):
            if 'source' in row:
                path = Path(row['source']).resolve(strict=True)
                dependencies['materials'][str(path)] = artifacts.contents(path)
    return dependencies


def produce_runtimes(binding, purposes, resolution=None):
    """Build missing physical runtime once; preserve separate purpose identities."""
    selection = (resolution or binding)['selection']
    if digest(Path(selection['python']).resolve(strict=True)) != binding['python_sha256']:
        raise ValueError('selected Python interpreter changed since compilation')
    from scripts.runtime import ensure_host_runtime
    result = {}
    for purpose in purposes:
        receipt = ensure_host_runtime(Path(selection['cache_root']), Path(selection['python']), purpose,
                                      expected_dependencies=binding['runtime_dependencies'])
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
    binding = spec.get('environment_selection')
    if productions and not binding:
        raise ValueError('material productions need a frozen environment selection')
    cache = Path(spec.get('environment_resolution', binding)['selection']['cache_root']) if binding else None
    result = {}
    for name, selection in productions.items():
        if selection.get('producer') == 'prepare':
            expected = binding['material_dependencies'][name]
            if plan_prepare(selection) != expected:
                raise ValueError('recovery dependencies changed since compilation')
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
                'producer', 'variant', 'runtime', 'skill_source', 'tool_env', 'e2e_runtime', 'otlp_dependencies'}:
            raise ValueError('unsupported material production fields: ' + name)
        parameters = {key: value for key, value in selection.items() if key != 'producer'}
        material = produce(output_store=cache / 'harness',
                           expected_dependencies=binding['material_dependencies'][name], **parameters)
        identity = material['material_id']
        index = cache / 'production-index' / (canonical(identity) + '.json')
        with locked(index.with_suffix('.lock')):
            consumer = 'run-' + canonical(str(directory.resolve()))
            if index.exists():
                previous = read(index)
                if previous['material_id'] != identity or previous['dependencies'] != material['dependencies']:
                    raise ValueError('production identity rebound to different dependencies')
                ref = previous['artifact']
                artifacts.verify(store, ref)
                artifacts.retain(store, ref, consumer=consumer, purpose='input/' + name,
                                 request_id='retain-' + canonical([consumer, name, ref]))
            else:
                ref = artifacts.publish(store, Path(material['root']), 'harness-material',
                    provenance={'producer': 'harness', 'material_id': identity,
                                'dependencies': material['dependencies'], 'capabilities': material['capabilities']},
                    consumer=consumer, purpose='input/' + name,
                    request_id='publish-' + canonical([identity, str(Path(store).resolve())]))
                atomic(index, {'material_id': identity, 'dependencies': material['dependencies'], 'artifact': ref})
        result[name] = {'artifact': ref, 'producer': material, 'observed_at': time.time()}
        package_needed = any(job['backend']['kind'] == 'hosted' and
            job.get('inputs', {}).get('agent') == {'from_production': name} for job in spec['jobs'])
        if package_needed:
            from scripts.package_agent import write_zip
            package_index = cache / 'production-index' / ('package-' + canonical(identity) + '.json')
            with locked(package_index.with_suffix('.lock')):
                if package_index.exists():
                    packaged = read(package_index)
                    artifacts.verify(store, packaged['artifact'])
                else:
                    output = cache / 'packages' / canonical(identity)
                    output.mkdir(parents=True, exist_ok=True)
                    archive = output / 'agent.zip'
                    if archive.exists():
                        archive.rename(output / ('partial-' + str(time.time_ns()) + '.zip'))
                    source_record = Path(material['root']) / 'runtime/runtime-source.json'
                    records = read(source_record).get('sources', {}) if source_record.exists() else {}
                    write_zip(Path(material['root']), archive, 'pi', records,
                              capabilities=material['capabilities'], persist_manifest=False)
                    package_ref = artifacts.publish(store, archive, 'agent-package',
                        provenance={'producer': 'harness.package', 'material_id': identity,
                                    'material': ref, 'capabilities': material['capabilities']},
                        consumer='package-' + canonical(identity), purpose='delivery',
                        request_id='package-' + canonical(identity))
                    packaged = {'artifact': package_ref, 'material_id': identity}
                    atomic(package_index, packaged)
                artifacts.retain(store, packaged['artifact'], consumer=consumer, purpose='input/' + name,
                                 request_id='retain-' + canonical([consumer, name, packaged['artifact']]))
                result[name]['package'] = packaged['artifact']
    atomic(directory / 'productions.json', record('productions', selections=result))
    return result
