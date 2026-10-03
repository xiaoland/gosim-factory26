"""Workspace authority: registered writers, independent capture and CAS handoff.

This authority covers declared managed writers only. A caller must supply the
actual launcher/service closure contract; a process-group exit is not coverage.
"""
import inspect
import json
from pathlib import Path
import time

from .core import Blocked, atomic, canonical, identifier, locked, read, record, require


def transition(registry, workspace, action, request_id, parameters, now):
    """One short registry transaction. No physical action or payload I/O occurs here."""
    spaces = registry.setdefault('workspaces', {})
    space = spaces.setdefault(workspace, {'writers': [], 'capture': None})
    requests = registry.setdefault('requests', {})
    old = requests.get(request_id)
    signature = {'workspace': workspace, 'action': action, 'parameters': parameters}
    if old:
        if old.get('state_parameters') != signature:
            raise RuntimeError('state request reused with changed parameters')
        return old
    holder = space.get('holder')
    if action == 'initialize':
        if holder:
            raise RuntimeError('state holder already exists; query its original generation')
        coverage = parameters['coverage']
        if coverage.get('protocol') != 'managed-writers-v1' or not coverage.get('entry_contract'):
            raise RuntimeError('state holder requires the actual managed writer contract')
        holder = {'kind': 'factory26.exp.state-holder', 'schema_version': 1,
                  'holder_id': workspace, 'domain_identity': parameters['domain_identity'],
                  'locator': parameters['locator'], 'coverage': coverage, 'generation': 1,
                  'version': 1, 'phase': 'writable', 'writer': parameters['writer'],
                  'pending': None, 'capture': None, 'snapshot': None, 'repair': None}
        space['holder'] = holder
    else:
        if not holder:
            raise RuntimeError('workspace has no state holder; historical writers require explicit coverage')
        if parameters.get('expected_generation') != holder['generation']:
            raise RuntimeError('state generation changed')
        if action == 'consumer-register':
            if holder['phase'] != 'writable':
                raise RuntimeError('state transfer rejects new live consumers')
            consumer = parameters['consumer']
            resource = registry['resources'].get(consumer['resource_id'])
            if not resource or resource.get('workspace') != workspace:
                raise RuntimeError('consumer has no resource in this holder authority')
            existing = space.setdefault('consumers', {}).get(consumer['id'])
            if existing and existing != consumer:
                raise RuntimeError('state consumer identity changed')
            space['consumers'][consumer['id']] = consumer
        elif action == 'transfer-begin':
            if holder['phase'] != 'writable' or holder['pending']:
                raise RuntimeError('state already has a transfer/capture owner')
            if parameters['old_incarnation'] != holder['writer']['incarnation']:
                raise RuntimeError('old state writer incarnation changed')
            if holder.get('snapshot'):
                holder.setdefault('history', []).append({'generation': holder['generation'], 'snapshot': holder['snapshot'], 'repair': holder.get('repair')})
            holder.update(snapshot=None, repair=None)
            holder['closing_writers'] = list(dict.fromkeys(space['writers'] + [holder['writer']['resource_id']] + [rid for rid, row in registry['resources'].items() if row.get('workspace') == workspace and row.get('role') != 'capture' and row.get('state_access') != 'readonly' and row.get('phase') != 'released']))
            holder.update(phase='transfer-pending', pending=request_id,
                          prior_writer=holder['writer'], consumers=list(dict.fromkeys(parameters['consumers'] + list(space.get('consumers', {})))))
        elif action == 'capture-acquire':
            if holder['phase'] != 'transfer-pending' or holder['pending'] != parameters['transfer_request']:
                raise RuntimeError('capture requires the original transfer intent')
            if space['writers'] or any(row.get('pending') for row in registry['resources'].values()
                                       if row.get('workspace') == workspace):
                raise RuntimeError('state writers or unresolved physical actions remain')
            closure = parameters['closure']
            if (closure.get('status') != 'closed' or closure.get('coverage') != holder['coverage']
                    or closure.get('unmanaged_writers') or not closure.get('writers')):
                raise RuntimeError('actual registered writer closure is incomplete')
            observed = {row['resource_id']: row for row in closure['writers']}
            if set(observed) != set(holder['closing_writers']):
                raise RuntimeError('closure differs from the accepted writer set')
            for writer_id in holder['closing_writers']:
                writer = registry['resources'].get(writer_id)
                proof = observed[writer_id]
                if not writer or writer.get('pending') or proof.get('closed') is not True:
                    raise RuntimeError('registered writer closure is unresolved')
                if proof.get('physical') != writer.get('identity'):
                    raise RuntimeError('writer closure does not match authority birth/effect')
                if writer['phase'] not in ('terminal', 'released'):
                    raise RuntimeError('writer has no confirmed terminal effect')
            owner = parameters['capture_owner']
            if owner in registry['resources']:
                raise RuntimeError('capture owner identity already allocated')
            registry['resources'][owner] = {'resource_id': owner, 'role': 'capture',
                'workspace': workspace, 'generation': request_id, 'version': 1,
                'phase': 'capturing', 'pending': None, 'identity': None,
                'owner': parameters['owner']}
            capture = {'owner': owner, 'request_id': request_id, 'token': parameters['capture_token'],
                       'generation': holder['generation'], 'closure': closure}
            holder.update(phase='capturing', capture=capture, writer=None, source_closure=closure)
            space['capture'] = owner
        elif action == 'writer-reserve':
            if holder['phase'] != 'repaired' or not holder['capture']:
                raise RuntimeError('new writer reservation requires repaired capture')
            writer = parameters['writer']
            rid = writer['resource_id']
            if rid in registry['resources']:
                raise RuntimeError('writer resource already allocated')
            registry['resources'][rid] = {'resource_id': rid, 'workspace': workspace, 'role': 'entry',
                'identity': None, 'incarnation': writer['incarnation'], 'phase': 'reserved', 'pending': None}
        elif action == 'capture-reopen':
            if holder['phase'] != 'closed' or space['writers'] or space['capture'] or holder['snapshot'] != parameters['snapshot']:
                raise RuntimeError('only the closed original snapshot can reopen a recovery lease')
            if any(row.get('pending') for row in registry['resources'].values() if row.get('workspace') == workspace):
                raise RuntimeError('unresolved physical action blocks recovery capture')
            owner = parameters['capture_owner']
            if owner in registry['resources']:
                raise RuntimeError('capture owner identity already allocated')
            registry['resources'][owner] = {'resource_id': owner, 'role': 'capture', 'workspace': workspace,
                'generation': request_id, 'version': 1, 'phase': 'capturing', 'pending': None,
                'identity': None, 'owner': parameters['owner']}
            holder['capture'] = {'owner': owner, 'request_id': request_id, 'token': parameters['capture_token'],
                'generation': holder['generation'], 'closure': holder['source_closure']}
            holder.update(phase='snapshot-sealed', pending=request_id)
            space['capture'] = owner
        elif action in ('snapshot-bind' , 'repair-begin', 'repair-item', 'repair-complete', 'handoff', 'capture-close', 'repair-abort'):
            capture = holder['capture']
            if (not capture or parameters['capture_token'] != capture['token']
                    or parameters['capture_owner'] != capture['owner'] or space['capture'] != capture['owner']):
                raise RuntimeError('capture owner/token changed; late requests cannot clear a new lease')
            if action == 'snapshot-bind':
                if holder['snapshot']:
                    raise RuntimeError('capture snapshot already sealed')
                holder['snapshot'] = parameters['snapshot']
                holder['phase'] = 'snapshot-sealed'
            elif action == 'repair-begin':
                if holder['phase'] != 'snapshot-sealed' or holder['snapshot'] != parameters['snapshot']:
                    raise RuntimeError('repair requires the retained source snapshot')
                holder['repair'] = {'request_id': request_id, 'snapshot': parameters['snapshot'],
                                    'changes': parameters['changes'], 'completed': {}, 'status': 'pending'}
                holder['phase'] = 'repairing'
            elif action == 'repair-item':
                repair = holder['repair']
                if not repair or repair['request_id'] != parameters['repair_request']:
                    raise RuntimeError('repair request changed')
                item = parameters['item']
                if item not in repair['changes'] or item in repair['completed']:
                    raise RuntimeError('repair item is not an incomplete declared change')
                repair['completed'][item] = parameters['readback']
            elif action == 'repair-complete':
                repair = holder['repair']
                if (not repair or repair['request_id'] != parameters['repair_request']
                        or set(repair['completed']) != set(repair['changes'])
                        or parameters['readback'].get('compatible') is not True):
                    raise RuntimeError('repair is incomplete or incompatible')
                repair.update(status='complete', readback=parameters['readback'])
                holder['generation'] += 1
                holder['phase'] = 'repaired'
            elif action == 'repair-abort':
                if holder['phase'] not in ('snapshot-sealed', 'repairing', 'repaired'):
                    raise RuntimeError('recovery abort requires this original capture or repair')
                repair = holder.get('repair')
                if repair and repair['request_id'] != parameters['repair_request']:
                    raise RuntimeError('recovery abort belongs to a different repair request')
                if space['writers']:
                    raise RuntimeError('recovery abort has registered writers still open')
                for row in registry['resources'].values():
                    if row.get('workspace') != workspace or row['resource_id'] == capture['owner'] or row['phase'] == 'released':
                        continue
                    if row.get('pending'):
                        raise RuntimeError('recovery abort has an unresolved physical action')
                    if (row.get('role') in ('entry', 'execution') and row['phase'] == 'reserved'
                            and row.get('identity') is None and not row.get('volume')):
                        row.update(phase='released', cancellation={'request_id': request_id, 'effect': 'confirmed-uncreated'})
                        continue
                    raise RuntimeError('recovery abort requires exact resource closure/release: ' + row['resource_id'])
                holder.update(phase='repair-aborted', capture=None, pending=None, writer=None,
                              abort={'request_id': request_id, 'generation': holder['generation'],
                                     'state_preserved': True, 'rollback': False, 'observed_at': now})
                if repair:
                    repair.update(status='aborted', aborted_at=now)
                space['capture'] = None
                registry['resources'][capture['owner']]['phase'] = 'released'
            elif action == 'handoff':
                if holder['phase'] != 'repaired' or holder['snapshot'] != parameters['snapshot']:
                    raise RuntimeError('handoff requires completed repair and unchanged snapshot')
                if holder['prior_writer']['incarnation'] != parameters['old_incarnation']:
                    raise RuntimeError('handoff prior incarnation changed')
                if parameters['consumers'] != holder['consumers'] or not all(
                        row.get('snapshot') == holder['snapshot'] and row.get('closed') is True
                        for row in parameters['consumer_bindings']):
                    raise RuntimeError('old consumers have not all closed/rebound to snapshot')
                if {row['id'] for row in parameters['consumer_bindings']} != set(holder['consumers']):
                    raise RuntimeError('old consumer coverage differs from transfer intent')
                writer = parameters['writer']
                row = registry['resources'].get(writer['resource_id'])
                if row and (row.get('role') not in ('entry', 'execution') or (row.get('incarnation') and row['incarnation'] != writer['incarnation']) or (row.get('identity') and row['identity'].get('labels', {}).get('io.factory26.exp.incarnation') != writer['incarnation'])):
                    raise RuntimeError('new writer incarnation differs from its reserved actual birth')
                if (not row or row['workspace'] != workspace or row['phase'] == 'released'
                        or row['pending'] or (row.get('identity') or {}).get('state', {}).get('Running')
                        or space['writers'] or any(resource.get('workspace') == workspace and resource.get('state_access') == 'repair' and resource.get('phase') != 'released' for resource in registry['resources'].values()) or parameters['assembly'].get('generation') != holder['generation']
                        or parameters['assembly'].get('holder_id') != workspace):
                    raise RuntimeError('new resource/assembly is not ready for this exclusive generation')
                holder.update(writer=writer, phase='writable', capture=None, pending=None,
                              assembly=parameters['assembly'])
                space['writers'] = [writer['resource_id']]
                space['capture'] = None
                space.setdefault('consumer_history', []).append({'snapshot': holder['snapshot'], 'bindings': parameters['consumer_bindings']})
                space['consumers'] = {}
                registry['resources'][capture['owner']]['phase'] = 'released'
            else:
                if holder['phase'] != 'snapshot-sealed':
                    raise RuntimeError('repair/handoff capture cannot be silently abandoned')
                if any(row.get('workspace') == workspace and row.get('capture_owner') == capture['owner'] and (row.get('pending') or row.get('phase') != 'released') for row in registry['resources'].values()):
                    raise RuntimeError('capture helper responsibility is still active or unresolved')
                holder.update(phase='closed', capture=None, pending=None)
                space['capture'] = None
                registry['resources'][capture['owner']]['phase'] = 'released'
        else:
            raise RuntimeError('unsupported state action')
        holder['version'] += 1
    effect = {'kind': 'factory26.exp.state-effect', 'schema_version': 1,
              'request_id': request_id, 'status': 'applied', 'state_parameters': signature,
              'holder': json.loads(json.dumps(holder)), 'observed_at': now}
    requests[request_id] = effect
    return effect


# The same reducer runs under the existing daemon registry lock, not another authority.
TRANSITIONS = inspect.getsource(transition)


def query(binding):
    authority = binding['authority']
    if authority['kind'] == 'docker':
        from . import admission
        return admission.state_query(authority['target'], authority['workspace'])
    if authority['kind'] != 'local':
        raise Blocked('backend has no managed state authority')
    root = Path(authority['root']).resolve(strict=True)
    with locked(root / '.state.lock'):
        registry = require(read(root / 'state-registry.json'), 'state-registry')
        return registry['workspaces'].get(authority['workspace'])


def action(binding, verb, request_id, parameters):
    identifier(request_id)
    authority = binding['authority']
    if authority['kind'] == 'docker':
        from . import admission
        result = admission.state_action(authority['target'], authority['workspace'], verb, request_id, parameters)
    elif authority['kind'] == 'local':
        root = Path(authority['root']).resolve(strict=True)
        with locked(root / '.state.lock'):
            registry = require(read(root / 'state-registry.json'), 'state-registry')
            result = transition(registry, authority['workspace'], verb, request_id, parameters, time.time())
            atomic(root / 'state-registry.json', registry)
    else:
        raise Blocked('backend has no managed state authority')
    # This is the accepted action's original readback, not a background observation.
    directory = Path(binding['source_attempt_directory'])
    if directory.is_dir():
        observations = directory / 'state-observations'
        observations.mkdir(exist_ok=True)
        path = observations / (identifier(binding['holder_id']) + '.json')
        with locked(observations / '.lock'):
            previous = read(path) if path.exists() else None
            holder = result['holder']
            version = (holder['generation'], holder['version'])
            if not previous or version >= (previous['holder']['generation'], previous['holder']['version']):
                atomic(path, record('state-observation', binding=binding, holder=holder,
                    action=verb, request_id=request_id, observed_at=result['observed_at'],
                    observation_source='accepted-authority-action', effect=result['status']))
    return result


def abort_recovery(binding, request_id):
    """Release an idle recovery lease without pretending repaired bytes equal its snapshot."""
    holder = query(binding)['holder']
    if holder['phase'] == 'repair-aborted':
        if holder['abort']['request_id'] != request_id + '--abort':
            raise Blocked('holder was aborted by another recovery request')
        return holder
    if holder['phase'] == 'closed' and not holder.get('repair'):
        return holder
    capture = holder.get('capture')
    if not capture:
        raise Blocked('no original recovery lease can be aborted')
    return action(binding, 'repair-abort', request_id + '--abort', {
        'expected_generation': holder['generation'], 'capture_owner': capture['owner'],
        'capture_token': capture['token'], 'repair_request': request_id + '--repair'})['holder']


def initialize(binding, writer, coverage, request_id):
    authority = binding['authority']
    if authority['kind'] == 'local':
        root = Path(authority['root']).resolve()
        root.mkdir(parents=True, exist_ok=True)
        with locked(root / '.state.lock'):
            path = root / 'state-registry.json'
            if not path.exists():
                atomic(path, record('state-registry', domain_identity=binding['domain_identity'],
                                   resources={}, workspaces={}, requests={}))
    return action(binding, 'initialize', request_id, {'domain_identity': binding['domain_identity'],
                  'locator': binding['locator'], 'writer': writer, 'coverage': coverage})


def permit(binding, resource_id, incarnation, generation):
    space = query(binding)
    if not space or not space.get('holder'):
        raise Blocked('state holder is absent')
    holder = space['holder']
    if (holder['phase'] != 'writable' or holder['generation'] != generation
            or holder['writer'] != {'resource_id': resource_id, 'incarnation': incarnation,
                                    'attempt_id': binding['writer']['attempt_id']}):
        raise Blocked('resource has no exclusive state writer permit')
    return holder


def register_writer(binding, resource_id, incarnation, physical, *, role='entry', parent=None, closed=False, shutdown=None):
    """Local launcher/child-owner registration, with its real birth and shutdown receipt.

Every allowed native/access/service launcher calls this before writer entry and
again with its retained shutdown proof. Unregistered shutdown is never inferred.
"""
    authority = binding['authority']
    if authority['kind'] != 'local':
        raise Blocked('Docker writer registration is owned by managed resource actions')
    root = Path(authority['root']).resolve(strict=True)
    with locked(root / '.state.lock'):
        path = root / 'state-registry.json'
        registry = require(read(path), 'state-registry')
        workspace = registry['workspaces'][authority['workspace']]
        holder = workspace['holder']
        current = registry['resources'].get(resource_id)
        if current and current.get('identity') is not None and current['identity'] != physical:
            raise Blocked('local writer physical birth changed')
        if closed:
            from .core import process_state
            if process_state(physical) != 'lost':
                raise Blocked('Local writer terminal birth must be independently read back')
            if not shutdown or not shutdown.get('contract'):
                raise Blocked('Local writer closure requires its maintained launcher contract')
            if not current or not shutdown or shutdown.get('closed') is not True or shutdown.get('physical') != physical:
                raise Blocked('local writer requires its actual child-owner shutdown proof')
            current.update(phase='terminal', shutdown=shutdown)
            workspace['writers'] = [item for item in workspace['writers'] if item != resource_id]
        else:
            if holder['phase'] != 'writable' or not holder['writer'] or incarnation != holder['writer']['incarnation']:
                raise Blocked('state transfer forbids another writer')
            if resource_id != holder['writer']['resource_id'] and parent not in workspace['writers']:
                raise Blocked('native/service writer needs its admitted parent owner')
            registry['resources'][resource_id] = {'resource_id': resource_id, 'identity': physical,
                'incarnation': incarnation, 'role': role, 'workspace': authority['workspace'],
                'parent': parent, 'phase': 'active', 'pending': None}
            if resource_id not in workspace['writers']:
                workspace['writers'].append(resource_id)
        atomic(path, registry)
        return registry['resources'][resource_id]


def closure(binding):
    """Read the frozen transfer set. A caller must have performed each managed shutdown."""
    authority = binding['authority']
    space = query(binding)
    holder = space['holder']
    if holder['phase'] != 'transfer-pending':
        raise Blocked('state closure requires accepted transfer-pending')
    if authority['kind'] == 'docker':
        from . import admission
        registry = admission.query(authority['target'])
        resources = registry['resources']
    else:
        root = Path(authority['root']).resolve(strict=True)
        with locked(root / '.state.lock'):
            resources = read(root / 'state-registry.json')['resources']
    rows = []
    for rid in holder['closing_writers']:
        row = resources.get(rid)
        if not row or row.get('pending') or row['phase'] not in ('terminal', 'released'):
            raise Blocked('writer terminal effect is not closed: ' + rid)
        if authority['kind'] == 'local' and not row.get('shutdown', {}).get('closed'):
            raise Blocked('local entry/native shutdown coverage is missing: ' + rid)
        rows.append({'resource_id': rid, 'closed': True, 'physical': row['identity'],
                     'shutdown': row.get('shutdown')})
    return {'status': 'closed', 'coverage': holder['coverage'], 'writers': rows,
            'unmanaged_writers': [], 'generation': holder['generation']}


def capture(binding, request_id, owner):
    space = query(binding)
    holder = space['holder']
    if holder.get('capture') and holder['capture']['request_id'] == request_id:
        return holder
    token = 'capture-' + canonical([binding['holder_id'], holder['generation'], request_id])[:32]
    proof = closure(binding)
    result = action(binding, 'capture-acquire', request_id, {
        'expected_generation': holder['generation'], 'transfer_request': holder['pending'],
        'capture_owner': 'capture-' + request_id, 'capture_token': token,
        'owner': owner, 'closure': proof})
    return result['holder']


def consumer_bindings(attempt, snapshot, consumers, *, binding=None):
    """Seal registered old readers/writers before handoff; no mutable locator is retained."""
    attempt = Path(attempt).resolve(strict=True)
    saved = read(attempt / 'state-consumers.json') if (attempt / 'state-consumers.json').exists() else record('state-consumers', consumers=[])
    registered = {row['id']: row for row in saved['consumers']}
    if binding:
        for name, row in query(binding).get('consumers', {}).items():
            registered[name] = {**row, 'closed': True, 'closure': query(binding)['holder'].get('source_closure')}
    if set(registered) != set(consumers):
        raise Blocked('old state consumer set changed or is not registered')
    bindings = []
    for name, row in registered.items():
        if row.get('writer') and not row.get('closed'):
            raise Blocked('old Console/access writer remains open: ' + name)
        bindings.append({'id': name, 'snapshot': snapshot, 'closed': True,
                         'previous_locator': row.get('locator')})
    atomic(attempt / 'consumer-snapshot-bindings.json', record('consumer-snapshot-bindings', bindings=bindings))
    return bindings


def begin_capture(directory, binding, request_id, *, consumers=None, grace=10):
    """Public managed lifecycle: freeze entry, close exact writers, acquire lease."""
    from . import backends
    directory = Path(directory)
    holder = query(binding)['holder']
    if holder.get('capture'):
        if holder['capture']['request_id'] != request_id + '--capture':
            raise Blocked('state is held by another capture request')
        return holder
    if binding['authority']['kind'] == 'local' and holder['coverage'].get('descendant_writer_contract') != 'registered-or-no-detach-v1':
        raise Blocked('Local capture coverage is partial: native tool descendants may detach; no maintained registration/shutdown contract')
    if holder['phase'] == 'closed':
        token = 'capture-' + canonical([binding['holder_id'], holder['generation'], request_id])[:32]
        return action(binding, 'capture-reopen', request_id + '--capture', {
            'expected_generation': holder['generation'], 'snapshot': holder['snapshot'],
            'capture_owner': 'capture-' + request_id, 'capture_token': token,
            'owner': {'kind': 'controller', 'request_id': request_id}})['holder']
    if holder['phase'] == 'writable':
        if consumers is None:
            saved = read(directory / 'state-consumers.json') if (directory / 'state-consumers.json').exists() else {'consumers': []}
            consumers = [row['id'] for row in saved['consumers']]
        action(binding, 'transfer-begin', request_id + '--transfer', {
            'expected_generation': holder['generation'], 'old_incarnation': holder['writer']['incarnation'],
            'consumers': consumers})
    else:
        if holder.get('pending') != request_id + '--transfer':
            raise Blocked('state has another unresolved transfer request')
    backends.close_state(binding, request_id + '--closure', grace=grace)
    return capture(binding, request_id + '--capture', {'kind': 'controller', 'request_id': request_id})


def bind_snapshot(binding, snapshot, request_id):
    holder = query(binding)['holder']
    capture = holder['capture']
    return action(binding, 'snapshot-bind', request_id, {'expected_generation': holder['generation'],
        'capture_owner': capture['owner'], 'capture_token': capture['token'], 'snapshot': snapshot})['holder']


def end_capture(binding, request_id):
    holder = query(binding)['holder']
    capture = holder['capture']
    if not capture:
        if holder['phase'] == 'closed':
            return holder
        raise Blocked('capture owner absent; cannot release another lifecycle')
    return action(binding, 'capture-close', request_id, {'expected_generation': holder['generation'],
        'capture_owner': capture['owner'], 'capture_token': capture['token']})['holder']


def handoff_for_execution(binding, writer, assembly, request_id):
    """Install one new permit after actual reservation; physical start follows outside lock."""
    holder = query(binding)['holder']
    if holder['phase'] == 'writable':
        return permit({**binding, 'writer': writer}, writer['resource_id'], writer['incarnation'], binding['generation'])
    if holder['phase'] != 'repaired' or holder['generation'] != binding['generation']:
        raise Blocked('state is not the expected repaired generation')
    if binding['authority']['kind'] == 'local':
        action(binding, 'writer-reserve', request_id + '--reserve', {
            'expected_generation': holder['generation'], 'writer': writer})
    source_attempt = Path(binding['source_attempt_directory'])
    consumers = consumer_bindings(source_attempt, holder['snapshot'], holder['consumers'], binding=binding)
    capture = holder['capture']
    installed = {**assembly, 'holder_id': binding['holder_id'], 'generation': holder['generation']}
    result = action(binding, 'handoff', request_id, {'expected_generation': holder['generation'],
        'capture_owner': capture['owner'], 'capture_token': capture['token'],
        'snapshot': holder['snapshot'], 'old_incarnation': holder['prior_writer']['incarnation'],
        'consumers': holder['consumers'], 'consumer_bindings': consumers,
        'writer': writer, 'assembly': installed})
    return result['holder']


def reserve_writer(binding, resource_id, incarnation, request_id, *, parent, role):
    """Accept a Local spawn intent before process creation, under the holder lock."""
    authority = binding['authority']
    if authority['kind'] != 'local':
        raise Blocked('Docker launch reservations use managed resource actions')
    root = Path(authority['root'])
    with locked(root / '.state.lock'):
        registry = require(read(root / 'state-registry.json'), 'state-registry')
        workspace = registry['workspaces'][authority['workspace']]
        holder = workspace['holder']
        parameters = {'resource_id': resource_id, 'incarnation': incarnation, 'parent': parent, 'role': role}
        old = registry['requests'].get(request_id)
        if old:
            if old.get('parameters') != parameters:
                raise Blocked('Local writer spawn request changed')
            return old
        root_entry = resource_id == holder['writer']['resource_id'] and parent is None
        if holder['phase'] != 'writable' or holder['writer']['incarnation'] != incarnation or (not root_entry and parent not in workspace['writers']):
            raise Blocked('state transfer rejects a new Local writer launch')
        current = registry['resources'].get(resource_id)
        if current and not (root_entry and current['phase'] == 'reserved' and not current.get('identity') and not current.get('pending') and current['incarnation'] == incarnation):
            raise Blocked('Local writer resource already allocated')
        registry['resources'][resource_id] = {'resource_id': resource_id, 'workspace': authority['workspace'],
            'identity': None, 'incarnation': incarnation, 'role': role, 'parent': parent,
            'phase': 'launch-pending', 'pending': request_id}
        workspace['writers'].append(resource_id)
        effect = record('state-writer-launch', request_id=request_id, parameters=parameters, status='pending')
        registry['requests'][request_id] = effect
        atomic(root / 'state-registry.json', registry)
        return effect


def bind_writer(binding, resource_id, request_id, physical=None, *, failed_spawn=None):
    """Resolve only the original accepted spawn; an unknown response remains pending."""
    authority = binding['authority']
    root = Path(authority['root'])
    with locked(root / '.state.lock'):
        registry = require(read(root / 'state-registry.json'), 'state-registry')
        row = registry['resources'][resource_id]
        effect = registry['requests'][request_id]
        if row['pending'] != request_id:
            if effect['status'] == 'applied' and effect.get('physical') == physical:
                return effect
            raise Blocked('Local writer launch identity changed')
        if physical:
            from .core import process_state
            if process_state(physical) != 'alive':
                raise Blocked('Local writer created birth is not currently observable')
            row.update(identity=physical, phase='active', pending=None)
        elif failed_spawn and failed_spawn.get('spawn_effect') == 'not-created':
            row.update(phase='released', pending=None, shutdown={'closed': True, 'physical': None,
                'contract': 'python-subprocess-failed-before-return-v1', 'error': failed_spawn})
            workspace = registry['workspaces'][authority['workspace']]
            workspace['writers'].remove(resource_id)
        else:
            raise Blocked('Local spawn unknown; retain pending rather than infer absence')
        effect.update(status='applied', physical=physical, failed_spawn=failed_spawn)
        atomic(root / 'state-registry.json', registry)
        return effect


def capture_acquisition(binding, holder):
    """Describe the original admitted capture; this function performs no I/O."""
    capture = holder.get('capture')
    if (holder['holder_id'] != binding['holder_id'] or not capture
            or capture['generation'] != holder['generation']
            or not holder.get('source_closure')):
        raise Blocked('managed capture acquisition lacks the original holder/lease proof')
    return {'kind':'managed-writer-capture','holder_id':holder['holder_id'],
            'generation':holder['generation'],'capture_request_id':capture['request_id'],
            'capture_token':capture['token'],'closure':holder['source_closure']}


def terminal_content_permission(binding):
    """Read back known Local writers, allowing content copy without full closure.

    Lost exact registered births may close their own responsibility. Unknown or
    live births and pending launches block. This proves no coverage of detached
    descendants and never creates an authority recovery snapshot.
    """
    from .core import process_state
    authority = binding['authority']
    if authority['kind'] != 'local':
        raise Blocked('ordinary partial writer permission is Local only')
    root = Path(authority['root']).resolve(strict=True)
    with locked(root/'.state.lock'):
        registry = require(read(root/'state-registry.json'),'state-registry')
        workspace = registry['workspaces'][authority['workspace']]
        holder = workspace['holder']
        if holder['generation'] != binding['generation'] or holder['phase'] != 'writable':
            raise Blocked('ordinary content copy cannot bypass an active state transfer')
        if holder['coverage'].get('descendant_writer_contract') == 'registered-or-no-detach-v1':
            raise Blocked('complete writer coverage must use managed capture')
        observed = []
        for rid,row in registry['resources'].items():
            if row.get('workspace') != authority['workspace']:
                continue
            if row.get('pending'):
                raise Blocked('registered Local writer launch remains unresolved: '+rid)
            physical = row.get('identity')
            if not physical:
                if row['phase'] == 'released' and row.get('shutdown',{}).get('closed'):
                    observed.append({'resource_id':rid,'effect':'not-created','proof':row['shutdown']})
                    continue
                raise Blocked('registered Local writer birth remains unresolved: '+rid)
            current = process_state(physical)
            if current != 'lost':
                raise Blocked('registered Local writer is '+current+': '+rid)
            row.update(phase='terminal',shutdown={'closed':True,'physical':physical,
                'contract':'registered-exact-process-terminal-v1','observed_at':time.time()})
            if rid in workspace['writers']:
                workspace['writers'].remove(rid)
            observed.append({'resource_id':rid,'physical':physical,'effect':'exact-process-terminal'})
        atomic(root/'state-registry.json',registry)
    return {'kind':'terminal-content-copy','holder_id':binding['holder_id'],
            'generation':binding['generation'],'registered_writers':observed,
            'checkpoint_eligible':False,'writer_coverage':'partial',
            'coverage_gap':'native tool descendants may detach without registered shutdown',
            'cross_file_consistency':'not-proven'}
