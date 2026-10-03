"""Self-contained delivery is a cached projection of immutable definitions."""
from pathlib import Path
import shutil

from . import artifacts, definitions
from .core import atomic, canonical, locked, read


def project(definition, store, cache, consumer, *, zipped=False, private_inputs=None):
    key = canonical({'definition': definition, 'format': 'zip' if zipped else 'sdk-directory', 'private_inputs':private_inputs or {}, 'abi': 2, 'store_id': artifacts.initialize(store)['store_id']})
    cache = Path(cache)
    index = cache / 'delivery-index' / (key + '.json')
    with locked(index.with_suffix('.lock')):
        if index.exists():
            reference = read(index)['reference']
            artifacts.retain(store, reference, consumer, 'delivery', 'delivery-retain-' + canonical([consumer, reference]))
            return reference
        if zipped:
            directory_ref = project(definition, store, cache, consumer, zipped=False, private_inputs=private_inputs)
            payload = artifacts.resolve(store, directory_ref, consumer=consumer)
            output = cache / 'deliveries' / key
            output.mkdir(parents=True, exist_ok=True)
            from scripts.package_agent import write_zip
            source = output / 'agent.zip'
            if source.exists():
                raise ValueError('unfinished ZIP delivery is retained; publication requires explicit recovery')
            write_zip(payload, source, definition['variant'], {}, capabilities={**definition['capabilities'],'variant':definition['variant']}, persist_manifest=False)
        else:
            roles = {row['role']: row for row in definitions.resolve(definition, store, 'delivery-' + key)}
            output = cache / 'deliveries' / key
            if output.exists():
                raise ValueError('unfinished delivery must be preserved before reentry')
            payload = output / 'payload'
            payload.parent.mkdir(parents=True)
            payload.mkdir()
            shutil.copytree(roles['agent']['local_root'], payload/'agent', symlinks=True, copy_function=artifacts.copy_file)
            shutil.copy2(payload/'agent/main.py',payload/'main.py')
            shutil.copy2(payload/'agent/requirements.txt',payload/'requirements.txt')
            mapping = {'agent': 'agent'}
            for name in ('runtime', 'skills', 'support', 'e2e-runtime'):
                if name not in roles:
                    continue
                shutil.copytree(roles[name]['local_root'], payload / name, symlinks=True, copy_function=artifacts.copy_file)
                mapping[name] = name
            mapping['braid'] = 'runtime/bin/braid'
            layout = {'kind': 'factory26.harness.delivery', 'schema_version': 1,
                      'definition': definition, 'roles': [{**row, 'path': mapping[row['role']]} for row in roles.values()]}
            # Store/root are installation hints, not part of the frozen delivered identity.
            for row in layout['roles']:
                row.pop('store', None)
                row.pop('local_root', None)
                row.pop('access', None)
            if (private_inputs or {}).get('tool_env'):
                private_source=artifacts.resolve(store,private_inputs['tool_env'],consumer=consumer)
                (payload/'.private').mkdir(mode=0o700)
                artifacts.copy_file(private_source,payload/'.private/tool-env.json')
                (payload/'.private/tool-env.json').chmod(0o600)
                layout['private_inputs']={'tool_env':{'reference':private_inputs['tool_env'],'path':'.private/tool-env.json'}}
            atomic(payload / 'delivery-layout.json', layout)
            source = payload
        reference = artifacts.publish(store, source, 'agent-package' if zipped else 'harness-delivery',
            provenance={'producer': 'harness.delivery', 'definition': definition, 'capabilities': definition['capabilities']},
            consumer=consumer, purpose='delivery', request_id='delivery-' + key)
        atomic(index, {'reference': reference, 'definition': definition, 'format': 'zip' if zipped else 'sdk-directory'})
        return reference
