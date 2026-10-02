"""Immutable artifact publication and verified, environment-local resolution."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import socket
import sys
import time

from lab.arc_bench.workspace_archive import output_inventory
from .core import Blocked, atomic, canonical, digest, error, identifier, locked, member, new_id, read, record, require


def contents(path):
    if path.is_file() and not path.is_symlink():
        return {'kind': 'file', 'sha256': digest(path), 'executable': bool(path.stat().st_mode & 0o111)}
    return {'kind': 'directory', **output_inventory(path)}


def copy_file(source, destination):
    """Isolate file writers with APFS clones; other filesystems copy the bytes."""
    if sys.platform == 'darwin':
        import ctypes
        import errno
        library = ctypes.CDLL(None, use_errno=True)
        if library.clonefile(os.fsencode(source), os.fsencode(destination), 0) == 0:
            return str(destination)
        code = ctypes.get_errno()
        if code not in {errno.EXDEV, errno.ENOTSUP, errno.EINVAL}:
            raise OSError(code, os.strerror(code), str(source))
    return shutil.copy2(source, destination)


def initialize(store, domain_identity=None):
    """Create a persistent store identity; existing domain bindings cannot change."""
    store = Path(store).resolve()
    store.mkdir(parents=True, exist_ok=True, mode=0o700)
    with locked(store / '.store.lock'):
        path = store / 'store.json'
        if path.exists():
            value = require(read(path), 'artifact-store')
            if domain_identity is not None and value['domain_identity'] != domain_identity:
                raise Blocked('artifact store belongs to a different storage domain')
            return value
        domain = domain_identity or {'kind': 'local', 'host': socket.gethostname(),
                                     'storage_root': str(store), 'device': store.stat().st_dev}
        value = record('artifact-store', store_id=new_id('store'), domain_identity=domain,
                       isolation='consumer-readback' if domain['kind'] == 'local' else 'owner-controlled',
                       created_at=time.time())
        atomic(path, value)
        return value


def _sync(path):
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)



def _durable_tree(root):
    files = [root] if root.is_file() else (p for p in root.rglob('*') if p.is_file() and not p.is_symlink())
    for path in files:
        with path.open('rb') as stream:
            os.fsync(stream.fileno())
    if root.is_dir():
        for directory, names, _ in os.walk(root, topdown=False, followlinks=False):
            _sync(directory)

def _hold(consumer, purpose, request_id):
    if not isinstance(consumer, str) or not consumer or not isinstance(purpose, str) or not purpose:
        raise ValueError('retention requires a stable consumer and explicit purpose')
    request_id = identifier(request_id)
    return record('artifact-retention', retention_id='retain-' + canonical([consumer, purpose, request_id])[:32],
                  consumer=consumer, purpose=purpose, request_id=request_id, state='held', retained_at=time.time())


def _location(binding, ref, hold):
    return record('artifact-location', reference=ref, store_id=binding['store_id'],
                  domain_identity=binding['domain_identity'], relative_path=ref['artifact_id'],
                  state='available', verified_at=time.time(), verification='received-content-inventory',
                  retentions={hold['retention_id']: hold}, sequence=1)


def _object_location(store, ref):
    path = Path(store) / identifier(ref['artifact_id']) / 'location.json'
    if not path.exists():
        raise Blocked('legacy artifact location has no managed retention; keep its source protected and explicitly transfer/import')
    value = require(read(path), 'artifact-location')
    binding = require(read(Path(store) / 'store.json'), 'artifact-store')
    if value['reference'] != ref or value['store_id'] != binding['store_id'] or value['domain_identity'] != binding['domain_identity']:
        raise Blocked('artifact location reference or storage domain changed')
    return path, value


def _available(location):
    if location['state'] != 'available':
        raise Blocked('artifact location is ' + location['state'] + '; retain/consume refused')


def query(store, ref=None, request_id=None):
    """Read saved facts only; missing/unreachable bytes never prove safe deletion."""
    store = Path(store).resolve(strict=True)
    binding = require(read(store / 'store.json'), 'artifact-store')
    if request_id is not None:
        request_id = identifier(request_id)
        for folder in ('requests', 'retention-requests'):
            path = store / folder / (request_id + '.json')
            if path.exists():
                return read(path)
        raise Blocked('no saved effect for this store request')
    if ref is not None:
        return _object_location(store, ref)[1]
    locations = [require(read(path), 'artifact-location') for path in sorted(store.glob('artifact-*/location.json'))]
    return record('artifact-store-view', store=binding, locations=locations, observed_at=time.time())


def retain(store, ref, consumer, purpose, request_id):
    store = Path(store).resolve(strict=True)
    hold = _hold(consumer, purpose, request_id)
    with locked(store / '.store.lock'):
        action = store / 'retention-requests' / (identifier(request_id) + '.json')
        parameters = canonical([ref, consumer, purpose])
        if action.exists():
            previous_action = read(action)
            if previous_action['parameters_sha256'] != parameters:
                raise ValueError('retain request reused with different consumer/reference/purpose')
            path, current = _object_location(store, ref)
            _available(current)
            effect = current['retentions'][previous_action['effect']['retention_id']]
            if effect['state'] != 'held':
                raise Blocked('retain was released; use a new acquisition request')
            return effect
        path, location = _object_location(store, ref)
        _available(location)
        previous = next((row for row in location['retentions'].values()
                         if row['consumer'] == consumer and row['purpose'] == purpose and row['state'] == 'held'), None)
        if previous:
            atomic(action, record('artifact-retain-effect', request_id=request_id, parameters_sha256=parameters, effect=previous))
            return previous
        location['retentions'][hold['retention_id']] = hold
        location['sequence'] += 1
        atomic(path, location)
        atomic(action, record('artifact-retain-effect', request_id=request_id, parameters_sha256=parameters, effect=hold))
        return hold


def release(store, ref, retention_id, request_id):
    """Release one purpose only; missing response is queried with the same request."""
    store = Path(store).resolve(strict=True)
    identifier(retention_id); identifier(request_id)
    with locked(store / '.store.lock'):
        path, location = _object_location(store, ref)
        hold = location['retentions'][retention_id]
        if hold['state'] == 'released':
            if hold['release_request_id'] != request_id:
                raise Blocked('retention already released by another request')
            return hold
        hold.update(state='released', release_request_id=request_id, released_at=time.time())
        location['sequence'] += 1
        atomic(path, location)
        return hold


def deletion_intent(store, ref, request_id, *, writer_closed, preservation_satisfied):
    """GC preparation only. Applying deletion is a separate authorized operation."""
    if writer_closed is not True or preservation_satisfied is not True:
        raise Blocked('GC requires explicit writer closure and satisfied preservation policy')
    store = Path(store).resolve(strict=True)
    identifier(request_id)
    with locked(store / '.store.lock'):
        path, location = _object_location(store, ref)
        if location['state'] == 'deleting' and location['deletion']['request_id'] == request_id:
            return location['deletion']
        _available(location)
        if any(hold['state'] == 'held' for hold in location['retentions'].values()):
            raise Blocked('artifact or its carrier remains retained')
        deletion = record('artifact-deletion', request_id=request_id, reference=ref,
                          location_sequence=location['sequence'], state='intent', requested_at=time.time(),
                          writer_closed=True, preservation_satisfied=True)
        location.update(state='deleting', deletion=deletion, sequence=location['sequence'] + 1)
        atomic(path, location)
        return deletion


def publish(store, source, artifact_type, provenance=None, capabilities=None, *,
            request_id=None, consumer=None, purpose='producer', domain_identity=None, move_source=False):
    """Publish immutable content. Explicit handover consumes a sealed same-device source.

    A saved handover identity permits retry after its rename, without recopying or
    deleting an unconfirmed payload. Ordinary publication preserves its source.
    """
    if move_source and Path(source).is_symlink():
        raise ValueError('handover source cannot redirect through a link')
    source, store = Path(source).resolve(), Path(store).resolve()
    if move_source and (source.is_relative_to(store) or store.is_relative_to(source)):
        raise ValueError('handover source and artifact store must not overlap')
    binding = initialize(store, domain_identity)
    request_id = identifier(request_id or new_id('publish'))
    parameters = {'source': str(source), 'type': artifact_type, 'provenance': provenance or {},
                  'capabilities': capabilities or {}, 'consumer': consumer, 'purpose': purpose}
    if move_source:
        parameters['move_source'] = True
    action_path = store / 'requests' / (request_id + '.json')
    with locked(store / '.store.lock'):
        if action_path.exists():
            action = read(action_path)
            if action['parameters_sha256'] != canonical(parameters):
                raise ValueError('publication request reused with different parameters')
        else:
            action = record('artifact-publication', request_id=request_id, artifact_id=new_id('artifact'),
                            parameters_sha256=canonical(parameters), state='staging', created_at=time.time())
            atomic(action_path, action)
    artifact_id = action['artifact_id']
    with locked(store / 'requests' / (request_id + '.lock')):
        target = store / artifact_id
        if target.exists():
            ref = {'artifact_id': artifact_id, 'manifest_sha256': digest(target / 'manifest.json')}
            verify(store, ref)
            _available(_object_location(store, ref)[1])
            action.update(state='published', reference=ref)
            atomic(action_path, action)
            return ref
        staging = store / '.staging' / request_id
        staging.mkdir(parents=True, exist_ok=True, mode=0o700)
        atomic(staging / 'production.json', record('production', artifact_id=artifact_id,
               type=identifier(artifact_type), started_at=time.time(), provenance=provenance or {}))
        try:
            payload = staging / 'payload'
            if move_source:
                handover = staging / 'handover.json'
                expected = read(handover) if handover.exists() else None
                ownership = {'request_id': request_id, 'artifact_id': artifact_id,
                             'source': str(source), 'type': artifact_type,
                             'parameters_sha256': canonical(parameters)}
                source_present = source.exists() or source.is_symlink()
                payload_present = payload.exists() or payload.is_symlink()
                if source_present == payload_present:
                    raise Blocked('handover requires exactly one of sealed source or transferred payload; retain both locations')
                if expected is None:
                    if payload_present:
                        raise Blocked('handover payload lacks its original source identity; retain partial publication')
                    if source.is_symlink() or not (source.is_file() or source.is_dir()):
                        raise ValueError('handover source must be a sealed regular file or directory')
                    if source.stat().st_dev != staging.stat().st_dev:
                        raise Blocked('handover requires source and artifact store on the same filesystem')
                    expected = {**ownership, 'contents': contents(source)}
                    atomic(handover, expected)
                    identity = expected['contents']
                else:
                    if any(expected.get(key) != value for key, value in ownership.items()):
                        raise ValueError('handover identity differs from publication request')
                    identity = contents(source if source_present else payload)
                    if identity != expected['contents']:
                        raise ValueError('handover payload differs from sealed source identity')
                if source_present:
                    source.rename(payload)
                    _sync(source.parent)
                    _sync(staging)
            else:
                if payload.exists() or payload.is_symlink():
                    raise Blocked('partial publication retained; use its error and a new explicit production request')
                if source.is_file():
                    copy_file(source, payload)
                elif source.is_dir():
                    shutil.copytree(source, payload, symlinks=True, copy_function=copy_file)
                else:
                    raise ValueError('artifact source must be a regular file or directory')
                identity = contents(payload)
            _durable_tree(payload)
            value = record('artifact', artifact_id=artifact_id, type=artifact_type,
                           contents=identity, provenance=provenance or {}, capabilities=capabilities or {},
                           created_at=time.time(), producer={'component': 'exp.artifacts', 'version': 1})
            atomic(staging / 'manifest.json', value)
            ref = {'artifact_id': artifact_id, 'manifest_sha256': digest(staging / 'manifest.json')}
            hold = _hold(consumer or ('production:' + artifact_id), purpose, request_id)
            atomic(staging / 'location.json', _location(binding, ref, hold))
            _sync(staging)
            with locked(store / '.store.lock'):
                staging.rename(target)
                _sync(store)
                action.update(state='published', reference=ref, published_at=time.time())
                atomic(action_path, action)
            return ref
        except BaseException as exc:
            atomic(staging / 'failure.json', error(exc))
            raise


def _manifest(store, ref):
    """Authenticate the declared identity without claiming payload verification."""
    artifact_id = identifier(ref['artifact_id'])
    root = Path(store).resolve(strict=True) / artifact_id
    if root.is_symlink() or (root / 'payload').is_symlink() or (root / 'manifest.json').is_symlink():
        raise ValueError('artifact identity cannot redirect through links')
    source = (root / 'manifest.json').read_bytes()
    if hashlib.sha256(source).hexdigest() != ref['manifest_sha256']:
        raise ValueError('artifact manifest content changed')
    manifest = require(json.loads(source), 'artifact')
    if manifest['artifact_id'] != artifact_id or manifest['contents']['kind'] not in {'file', 'directory'}:
        raise ValueError('artifact identity or content kind differs from published manifest')
    return manifest


def member_contents(store, ref, path='.'):
    """Project a member's frozen identity from its authenticated immutable manifest.

    This does not read current source bytes. Transfer and consumer readback still
    verify their received bytes against this identity at the respective boundary.
    """
    manifest = _manifest(store, ref)
    return contents_member(manifest['contents'], path)


def contents_member(expected, path='.'):
    """Select a bounded member from an already authenticated inventory."""
    relative = member(path)
    if relative == '.':
        return expected
    if expected['kind'] != 'directory':
        raise ValueError('file artifact has no nested member')
    entries = expected['entries']
    for ancestor in Path(relative).parents:
        if str(ancestor) != '.' and any(row['path'] == ancestor.as_posix() and row['type'] == 'link' for row in entries):
            raise ValueError('artifact member redirects through an ancestor link')
    root = next((row for row in entries if row['path'] == relative), None)
    if root is None or root['type'] == 'link':
        raise ValueError('artifact member is missing or redirects through a link')
    if root['type'] == 'file':
        return {'kind': 'file', 'sha256': root['sha256'], 'executable': root['executable']}
    prefix = relative + '/'
    selected = [{**row, 'path': row['path'][len(prefix):]} for row in entries if row['path'].startswith(prefix)]
    encoded = json.dumps(selected, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()
    return {'kind': 'directory', 'algorithm': expected['algorithm'], 'entries': selected,
            'sha256': hashlib.sha256(encoded).hexdigest()}


def verify(store, ref):
    manifest = _manifest(store, ref)
    root = Path(store).resolve(strict=True) / manifest['artifact_id']
    if contents(root / 'payload') != manifest['contents']:
        raise ValueError('artifact contents or identity differs from published manifest')
    return manifest


def resolve(store, ref, path='.', *, consumer=None, request_id=None, retention=None):
    if (Path(store) / ref['artifact_id'] / 'location.json').exists():
        consumer = consumer or ('reader:' + str(Path(store).resolve()))
        if retention is None:
            retain(store, ref, consumer, 'reader', request_id or ('read-' + canonical([consumer, ref, path])[:32]))
        else:
            location = _object_location(store, ref)[1]
            _available(location)
            held = location['retentions'].get(retention['retention_id'])
            if not held or held['state'] != 'held' or held['consumer'] != consumer:
                raise Blocked('read-only resolution requires an existing consumer retention')
    # Legacy evidence can still be inspected; no managed consumer or execution guarantee is invented.
    verify(store, ref)
    relative = member(path)
    root = Path(store).resolve() / ref['artifact_id'] / 'payload'
    candidate = root / relative if relative != '.' else root
    current = root
    if current.is_symlink():
        raise ValueError('artifact root is a link')
    for part in Path(relative).parts:
        if part == '.':
            continue
        current = current / part
        if current.is_symlink():
            raise ValueError(f'ordinary artifact resolution cannot follow link: {relative}')
    if not candidate.exists() or not candidate.resolve().is_relative_to(root.resolve()):
        raise ValueError('artifact member is missing or escapes content boundary')
    if ref.get('member_sha256') and digest(candidate) != ref['member_sha256']:
        raise ValueError('artifact member digest differs')
    return candidate


def materialize(store, ref, destination, *, consumer=None, request_id=None, retention=None):
    """Verify received bytes before publication, without pre-reading the source."""
    destination = Path(destination).resolve() if not Path(destination).is_symlink() else Path(destination)
    consumer = consumer or ('assembly:' + str(destination))
    request_id = request_id or ('assemble-' + canonical([consumer, ref])[:32])
    if retention is None:
        retain(store, ref, consumer, 'assembly', request_id)
    else:
        location = _object_location(store, ref)[1]
        _available(location)
        held = location['retentions'].get(retention['retention_id'])
        if not held or held['state'] != 'held' or held['consumer'] != consumer:
            raise Blocked('read-only assembly requires the consumer existing held retention')
    manifest = _manifest(store, ref)
    source = Path(store).resolve() / ref['artifact_id'] / 'payload'
    if destination.is_symlink():
        raise ValueError('artifact destination cannot redirect through a link')
    if destination.exists():
        if contents(destination) != manifest['contents']:
            raise ValueError('existing input materialization differs from artifact')
        return destination
    if manifest['contents']['kind'] == 'directory':
        for row in manifest['contents']['entries']:
            if row['type'] == 'link':
                target = (source / row['path']).parent / row['target']
                if not target.resolve().is_relative_to(source.resolve()):
                    raise ValueError(f"external artifact dependency must be explicitly prepared: {row['path']}")
    destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    staging = destination.with_name('.' + destination.name + '.' + new_id('materialize'))
    if source.is_file():
        copy_file(source, staging)
    else:
        shutil.copytree(source, staging, symlinks=True, copy_function=copy_file)
    if contents(staging) != manifest['contents']:
        raise ValueError('artifact materialization content differs')
    staging.rename(destination)
    _sync(destination.parent)
    return destination


def import_evidence(store, source, *, evidence_type='evidence', provenance=None, capabilities=None):
    """Import bytes and explicit coverage, never upgrade a legacy execution guarantee."""
    return publish(store, source, evidence_type,
                   {'operation': 'explicit-import', **(provenance or {})},
                   {**(capabilities or {}), 'execution_proof': False})


def transfer(source_store, destination_store, ref, *, request_id=None, consumer=None, domain_identity=None):
    """Receive the same identity; retain both sides until target publication is confirmed."""
    source_store, destination_store = Path(source_store).resolve(), Path(destination_store).resolve()
    binding = initialize(destination_store, domain_identity)
    request_id = identifier(request_id or ('transfer-' + canonical([str(source_store), binding['store_id'], ref])[:32]))
    consumer = consumer or ('transfer:' + request_id)
    action_path = destination_store / 'requests' / (request_id + '.json')
    parameters = canonical({'source': str(source_store), 'reference': ref, 'consumer': consumer})
    with locked(destination_store / 'requests' / (request_id + '.lock')):
        if action_path.exists():
            action = read(action_path)
            if action['parameters_sha256'] != parameters:
                raise ValueError('transfer request reused with different parameters')
        else:
            action = record('artifact-transfer', request_id=request_id, reference=ref,
                            parameters_sha256=parameters, state='receiving', created_at=time.time())
            atomic(action_path, action)
        target = destination_store / identifier(ref['artifact_id'])
        if target.exists():
            verify(destination_store, ref)
            retain(destination_store, ref, consumer, 'transfer-target', request_id)
            action.update(state='published', confirmed_at=time.time())
            atomic(action_path, action)
            return ref
        managed_source = (source_store / ref['artifact_id'] / 'location.json').exists()
        source_hold = retain(source_store, ref, 'transfer:' + request_id, 'transfer-source', request_id) if managed_source else None
        # Legacy sources are read-only, remain protected by their original owner, and gain no invented hold.
        manifest = _manifest(source_store, ref)
        staging = destination_store / '.incoming' / request_id
        staging.mkdir(parents=True, exist_ok=True, mode=0o700)
        incoming = staging / ref['artifact_id']
        try:
            if incoming.exists():
                try:
                    verify(staging, ref)
                except (OSError, ValueError):
                    incoming.rename(staging / ('partial-' + new_id('copy')))
            if not incoming.exists():
                incoming.mkdir()
                shutil.copy2(source_store / ref['artifact_id'] / 'manifest.json', incoming / 'manifest.json')
                source_payload = source_store / ref['artifact_id'] / 'payload'
                if manifest['contents']['kind'] == 'file':
                    copy_file(source_payload, incoming / 'payload')
                else:
                    shutil.copytree(source_payload, incoming / 'payload', symlinks=True, copy_function=copy_file)
            verify(staging, ref)
            hold = _hold(consumer, 'transfer-target', request_id)
            atomic(incoming / 'location.json', _location(binding, ref, hold))
            _durable_tree(incoming)
            with locked(destination_store / '.store.lock'):
                incoming.rename(target)
                _sync(destination_store)
                action.update(state='published', published_at=time.time(), legacy_source=not managed_source)
                atomic(action_path, action)
            if source_hold:
                release(source_store, ref, source_hold['retention_id'], request_id + '-release')
            return ref
        except BaseException as exc:
            atomic(staging / 'transport-error.json', error(exc))
            action.update(state='partial', error=error(exc))
            atomic(action_path, action)
            raise


def gc_plan(store):
    """Saved domain references, including carrier protection; never authorize removal from a scan."""
    store = Path(store).resolve(strict=True)
    with locked(store / '.store.lock'):
        view = query(store)
        rows = []
        legacy = []
        for path in store.glob('artifact-*/manifest.json'):
            if not (path.parent / 'location.json').exists():
                legacy.append(str(path.parent))
        for location in view['locations']:
            holds = [hold for hold in location['retentions'].values() if hold['state'] == 'held']
            rows.append({'reference': location['reference'], 'state': location['state'],
                         'retentions': holds, 'carrier': str(store),
                         'candidate': location['state'] == 'available' and not holds,
                         'reclaim_authorized': False})
        return record('artifact-gc-plan', store=view['store'], objects=rows, legacy_protected=legacy,
                      carrier_retained=bool(legacy or any(row['retentions'] or row['state'] != 'deleted' for row in rows)),
                      read_only=True, created_at=time.time())


def apply_deletion(store, ref, request_id):
    """Apply the previously accepted GC request; reentry keeps the original deletion effect."""
    store = Path(store).resolve(strict=True)
    with locked(store / 'requests' / (identifier(request_id) + '.lock')):
        with locked(store / '.store.lock'):
            path, location = _object_location(store, ref)
            deletion = location.get('deletion')
            if not deletion or deletion['request_id'] != request_id:
                raise Blocked('GC apply requires the exact accepted deletion intent')
            if location['state'] == 'deleted':
                return deletion
            if location['state'] not in {'deleting', 'deletion-failed'} or any(
                    hold['state'] == 'held' for hold in location['retentions'].values()):
                raise Blocked('GC deletion no longer owns an unretained location')
        # Deleting state rejects new retains. Never hold the domain lock for large removal.
        payload = store / ref['artifact_id'] / 'payload'
        try:
            if payload.is_symlink():
                raise ValueError('GC payload cannot redirect through a link')
            if payload.is_dir():
                shutil.rmtree(payload)
            elif payload.exists():
                payload.unlink()
            _sync(path.parent)
            with locked(store / '.store.lock'):
                _, current = _object_location(store, ref)
                current.update(state='deleted', sequence=current['sequence'] + 1)
                current['deletion'].update(state='deleted', deleted_at=time.time())
                atomic(path, current)
                return current['deletion']
        except BaseException as exc:
            with locked(store / '.store.lock'):
                _, current = _object_location(store, ref)
                current.update(state='deletion-failed', sequence=current['sequence'] + 1)
                current['deletion'].update(state='unknown', error=error(exc))
                atomic(path, current)
            raise



def invalidate(store, ref, request_id, failure):
    """Storage owner records a diagnosed local-copy failure, preserving original production identity."""
    identifier(request_id)
    store = Path(store).resolve(strict=True)
    with locked(store / '.store.lock'):
        path, location = _object_location(store, ref)
        if location['state'] in {'deleting', 'deleted', 'deletion-failed'}:
            raise Blocked('deletion owns this location; record the failure on its action instead')
        location.update(state='damaged', failure=failure, failure_request_id=request_id,
                        sequence=location['sequence'] + 1)
        atomic(path, location)
        return location

def main():
    """Fixed store actions for short-lived domain owner helpers; no arbitrary shell."""
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('query', 'initialize', 'publish', 'retain', 'release', 'materialize', 'transfer'))
    parser.add_argument('--store', type=Path, required=True)
    parser.add_argument('--request', type=Path, help='versioned artifact-store-action JSON')
    args = parser.parse_args()
    request = require(read(args.request), 'artifact-store-action') if args.request else {}
    if args.action == 'query':
        value = query(args.store, request.get('reference'), request.get('request_id'))
    elif args.action == 'initialize':
        value = initialize(args.store, request['domain_identity'])
    elif args.action == 'publish':
        value = publish(args.store, request['source'], request['type'], request.get('provenance'),
                        request.get('capabilities'), request_id=request['request_id'],
                        consumer=request['consumer'], purpose=request['purpose'])
    elif args.action == 'retain':
        value = retain(args.store, request['reference'], request['consumer'], request['purpose'], request['request_id'])
    elif args.action == 'release':
        value = release(args.store, request['reference'], request['retention_id'], request['request_id'])
    elif args.action == 'materialize':
        value = str(materialize(args.store, request['reference'], request['destination'],
                                consumer=request['consumer'], request_id=request['request_id'], retention=request.get('retention')))
    else:
        value = transfer(request['source_store'], args.store, request['reference'],
                         request_id=request['request_id'], consumer=request['consumer'])
    print(json.dumps(value, ensure_ascii=False))


if __name__ == '__main__':
    main()
