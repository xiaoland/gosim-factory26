"""Self-contained delivery is a cached projection of immutable definitions."""
from pathlib import Path
import shutil
import tarfile

from . import artifacts, definitions
from .core import atomic, canonical, digest, locked, read


def project_prepared(prepared, store, cache, consumer, *, environment):
    """Project a verified legacy Hosted prepared state without running repairs again."""
    from tooling.linux.exp_checkpoint import validate, resolve_definition_assets, definition_mount_roots
    prepared = Path(prepared).resolve(strict=True)
    validation = validate(prepared)
    manifest = read(prepared/'harness-manifest.json')
    legacy = (manifest.get('acquisition', {}).get('status') == 'legacy-terminal-export'
              and manifest.get('source_identity', {}).get('backend_identity', {}).get('kind') == 'hosted'
              and not validation['readback']['gaps'])
    if manifest['kind'] != 'factory26.harness.prepared' or (validation['status'] != 'complete' and not legacy):
        raise ValueError('Hosted projection requires executable prepared state')
    if manifest['target_layout']['os'] != 'Linux' or manifest['target_layout']['architecture'] != 'x86_64':
        raise ValueError('Hosted prepared projection requires Linux x86_64')
    mounts, _ = resolve_definition_assets(prepared, manifest)
    roots = definition_mount_roots(manifest['definition_assets'], manifest['target_layout']['run_root'])
    # The historical Hosted package has one flat root; overlapping roles must
    # already refer to the same immutable artifact, as checked by the producer.
    if len(roots) != 1 or roots[0]['logical_root'] != '/workspace/submission':
        raise ValueError('Hosted legacy projection requires its original flat submission root')
    variant = read(prepared/'content/run/harness-layout.json')['variant']
    definition_root = dict(mounts)[roots[0]['logical_root']]
    package_manifest = read(definition_root/'package-manifest.json')
    if variant not in package_manifest['capabilities']['variants']:
        raise ValueError('prepared state and replacement definition variants differ')
    reference = artifacts.publish(store, prepared, 'prepared-state', consumer=consumer,
        purpose='hosted-recovery', request_id='prepared-'+canonical([consumer, manifest['prepared_id']]))
    output = Path(cache)/'prepared-deliveries'/canonical([reference, environment])
    if output.exists():
        raise FileExistsError('unfinished prepared delivery retained: '+str(output))
    shutil.copytree(definition_root, output,
                    symlinks=True, copy_function=artifacts.copy_file)
    metadata = output/'.prepared'
    metadata.mkdir()
    for item in prepared.iterdir():
        if item.name == 'content':
            continue
        if item.is_dir():
            shutil.copytree(item, metadata/item.name, symlinks=True, copy_function=artifacts.copy_file)
        else:
            artifacts.copy_file(item, metadata/item.name)
    with tarfile.open(metadata/'state.tar', 'w') as archive:
        archive.add(prepared/'content/run', arcname='run', recursive=True)
    roles = [{'role':row['name'], 'reference':row['artifact'], 'member':row['member'],
              'logical_root':row['logical_root'],
              'path':str(Path(row['logical_root']).relative_to('/workspace/submission')) or '.'}
             for row in manifest['definition_assets']]
    roles.append({'role':'support', 'reference':roots[0]['artifact'], 'member':'support',
                  'logical_root':'/workspace/submission/support', 'path':'support'})
    atomic(output/'delivery-layout.json', {'kind':'factory26.harness.delivery', 'schema_version':1,
        'mode':'hosted-prepared', 'roles':roles, 'definition':None, 'environment':environment,
        'prepared':{'reference':reference, 'manifest_path':'.prepared/harness-manifest.json',
                    'manifest_sha256':validation['manifest_sha256'], 'state_archive':'.prepared/state.tar',
                    'state_archive_sha256':digest(metadata/'state.tar')},
        'inputs':{'gateway_routes':{'reference':roots[0]['artifact'], 'member':'support/gateway-routes.json',
                                   'path':'support/gateway-routes.json'}},
        'private_inputs':{'provider_env':{'path':'.private/provider-env.json'},
                          'tool_env':{'path':'.private/tool-env.json'}}})
    # This is facility entry selection, not a second restoration implementation.
    shutil.copy2(output/'support/experiment_entry.py', output/'main.py')
    from tooling.scripts.package_agent import write_zip
    package = output.parent/(output.name+'.zip')
    write_zip(output, package, package_manifest['backend'], package_manifest['sources'],
              capabilities={**package_manifest['capabilities'], 'variant':variant})
    return package


def project(definition, store, cache, consumer, *, zipped=False, private_inputs=None, inputs=None):
    key = canonical({'definition': definition, 'format': 'hosted-zip' if zipped else 'sdk-thin', 'private_inputs':private_inputs or {} if zipped else {}, 'inputs':(inputs or {}) if zipped else {}, 'abi': 4})
    domain = artifacts.initialize(store)['store_id']
    cache = Path(cache)
    index = cache / 'delivery-index' / domain / (key + '.json')
    with locked(index.with_suffix('.lock')):
        if index.exists():
            reference = read(index)['reference']
            artifacts.retain(store, reference, consumer, 'delivery', 'delivery-retain-' + canonical([consumer, reference]))
            return reference
        if zipped:
            directory_ref = _self_contained(definition, store, cache, consumer, private_inputs, inputs)
            payload = artifacts.resolve(store, directory_ref, consumer=consumer)
            output = cache / 'deliveries' / domain / key
            output.mkdir(parents=True, exist_ok=True)
            from tooling.scripts.package_agent import write_zip
            source = output / 'agent.zip'
            if source.exists():
                raise ValueError('unfinished ZIP delivery is retained; publication requires explicit recovery')
            write_zip(payload, source, definition['variant'], {}, capabilities={**definition['capabilities'],'variant':definition['variant']}, persist_manifest=False)
        else:
            roles = {row['role']: row for row in definitions.resolve(definition, store, 'delivery-' + key,roles={'agent','support'})}
            output = cache / 'deliveries' / domain / key
            if output.exists():
                raise ValueError('unfinished delivery must be preserved before reentry')
            payload = output / 'payload'
            payload.parent.mkdir(parents=True)
            payload.mkdir()
            shutil.copy2(Path(roles['support']['local_root'])/'experiment_entry.py',payload/'main.py')
            shutil.copy2(Path(roles['agent']['local_root'])/'requirements.txt',payload/'requirements.txt')
            layout = {'kind': 'factory26.harness.delivery', 'schema_version': 1,
                'mode': 'sdk-components', 'definition': definition,
                'roles': _declared_roles(definition)}
            atomic(payload / 'delivery-layout.json', layout)
            source = payload
        reference = artifacts.publish(store, source, 'agent-package' if zipped else 'harness-delivery',
            provenance={'producer': 'harness.delivery', 'definition': definition, 'capabilities': definition['capabilities']},
            consumer=consumer, purpose='delivery', request_id='delivery-' + key, move_source=True)
        atomic(index, {'reference': reference, 'definition': definition, 'format': 'zip' if zipped else 'sdk-directory'})
        return reference


def _declared_roles(definition):
    from tooling.scripts.execution_context import member_join
    assets={row['name']:row for row in definitions.validate(definition)['assets']}
    return [{'role':row['role'],'reference':assets[row['asset']]['reference'],
             'member':member_join(assets[row['asset']].get('member','.'),row.get('member','.'))}
            for row in definition['roles']]


def _self_contained(definition, store, cache, consumer, private_inputs, inputs):
    """Hosted requires a full delivery; SDK never calls this producer."""
    key=canonical({'definition':definition,'private_inputs':private_inputs or {},'inputs':inputs or {},'format':'hosted-directory','abi':4})
    domain=artifacts.initialize(store)['store_id']
    index=Path(cache)/'delivery-index'/domain/(key+'.json')
    with locked(index.with_suffix('.lock')):
        if index.exists():
            ref=read(index)['reference']
            artifacts.retain(store,ref,consumer,'hosted-delivery','retain-'+canonical([consumer,ref]))
            return ref
        roles=definitions.resolve(definition,store,consumer)
        output=Path(cache)/'deliveries'/domain/key
        if output.exists():
            raise ValueError('unfinished hosted delivery retained; resume its publication explicitly')
        output.mkdir(parents=True)
        layout={'kind':'factory26.harness.delivery','schema_version':1,'mode':'hosted-self-contained',
            'definition':definition,'roles':[]}
        for row in roles:
            if row['role']=='braid':
                member='runtime/bin/braid'
            else:
                member=row['role']
                shutil.copytree(row['local_root'],output/member,symlinks=True,copy_function=artifacts.copy_file)
            layout['roles'].append({**{key:row[key] for key in ('role','reference','member')},'path':member})
        shutil.copy2(output/'support/experiment_entry.py',output/'main.py')
        shutil.copy2(output/'agent/requirements.txt',output/'requirements.txt')
        for name,ref in (private_inputs or {}).items():
            source=artifacts.resolve(store,ref,consumer=consumer)
            path=output/'.private'/(name+'.json')
            path.parent.mkdir(mode=0o700,exist_ok=True)
            artifacts.copy_file(source,path);path.chmod(0o600)
            layout.setdefault('private_inputs',{})[name]={'reference':ref,'path':str(path.relative_to(output))}
        for name,ref in (inputs or {}).items():
            if name not in {'application_seed','gateway_routes'}:
                raise ValueError('undeclared Hosted execution input: '+name)
            source=artifacts.resolve(store,ref,consumer=consumer)
            path=output/'inputs'/name
            path.parent.mkdir(exist_ok=True)
            if source.is_dir():
                shutil.copytree(source,path,symlinks=True,copy_function=artifacts.copy_file)
            else:
                artifacts.copy_file(source,path)
            layout.setdefault('inputs',{})[name]={'reference':ref,'member':'.','path':str(path.relative_to(output))}
        atomic(output/'delivery-layout.json',layout)
        ref=artifacts.publish(store,output,'hosted-delivery',consumer=consumer,purpose='hosted-projection',
            provenance={'producer':'harness.delivery','definition':definition,'capabilities':definition['capabilities']},
            request_id='hosted-delivery-'+key,move_source=True)
        atomic(index,{'reference':ref})
        return ref
