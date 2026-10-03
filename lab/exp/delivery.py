"""Self-contained delivery is a cached projection of immutable definitions."""
from pathlib import Path
import shutil

from . import artifacts, definitions
from .core import atomic, canonical, locked, read


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
            from scripts.package_agent import write_zip
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
    from scripts.execution_context import member_join
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
