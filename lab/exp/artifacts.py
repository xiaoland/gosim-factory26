"""Immutable artifact publication and verified, environment-local resolution."""
import os
from pathlib import Path
import shutil
import stat
import time

from lab.arc_bench.workspace_archive import output_inventory
from .core import atomic, canonical, digest, identifier, locked, member, new_id, read, record, require


def contents(path):
    if path.is_file() and not path.is_symlink():
        return {'kind': 'file', 'sha256': digest(path), 'executable': bool(path.stat().st_mode & 0o111)}
    return {'kind': 'directory', **output_inventory(path)}


def publish(store, source, artifact_type, provenance=None, capabilities=None):
    """Publish new production identity; a failed stage and its error remain private."""
    source, store = Path(source).resolve(strict=True), Path(store).resolve()
    artifact_id = new_id('artifact')
    staging = store / '.staging' / artifact_id
    staging.mkdir(parents=True, mode=0o700)
    atomic(staging / 'production.json', record('production', artifact_id=artifact_id,
           type=identifier(artifact_type), started_at=time.time(), provenance=provenance or {}))
    try:
        payload = staging / 'payload'
        if source.is_file():
            shutil.copy2(source, payload)
        elif source.is_dir():
            shutil.copytree(source, payload, symlinks=True)
        else:
            raise ValueError('artifact source must be a regular file or directory')
        identity = contents(payload)
        files = [payload] if payload.is_file() else (p for p in payload.rglob('*') if p.is_file() and not p.is_symlink())
        for path in files:
            with path.open('rb') as stream:
                os.fsync(stream.fileno())
        value = record('artifact', artifact_id=artifact_id, type=artifact_type,
                       contents=identity, provenance=provenance or {}, capabilities=capabilities or {},
                       created_at=time.time(), producer={'component': 'exp.artifacts', 'version': 1})
        atomic(staging / 'manifest.json', value)
        target = store / artifact_id
        staging.rename(target)
        descriptor = os.open(store, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        return {'artifact_id': artifact_id, 'manifest_sha256': digest(target / 'manifest.json')}
    except BaseException as exc:
        from .core import error
        atomic(staging / 'failure.json', error(exc))
        raise


def verify(store, ref):
    artifact_id = identifier(ref['artifact_id'])
    root = Path(store).resolve(strict=True) / artifact_id
    if root.is_symlink() or (root / 'payload').is_symlink() or (root / 'manifest.json').is_symlink():
        raise ValueError('artifact identity cannot redirect through links')
    if digest(root / 'manifest.json') != ref['manifest_sha256']:
        raise ValueError('artifact manifest content changed')
    manifest = require(read(root / 'manifest.json'), 'artifact')
    if manifest['artifact_id'] != artifact_id or contents(root / 'payload') != manifest['contents']:
        raise ValueError('artifact contents or identity differs from published manifest')
    return manifest


def resolve(store, ref, path='.'):
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


def materialize(store, ref, destination):
    """Copy verified content without silently binding external link targets."""
    manifest = verify(store, ref)
    source = Path(store).resolve() / ref['artifact_id'] / 'payload'
    destination = Path(destination)
    if destination.exists() or destination.is_symlink():
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
        shutil.copy2(source, staging)
    else:
        shutil.copytree(source, staging, symlinks=True)
    if contents(staging) != manifest['contents']:
        raise ValueError('artifact materialization content differs')
    staging.rename(destination)
    return destination


def import_evidence(store, source, *, evidence_type='evidence', provenance=None, capabilities=None):
    """Import bytes and explicit coverage, never upgrade a legacy execution guarantee."""
    return publish(store, source, evidence_type,
                   {'operation': 'explicit-import', **(provenance or {})},
                   {**(capabilities or {}), 'execution_proof': False})


def transfer(source_store, destination_store, ref):
    """Move a verified published identity between stores without republishing it."""
    verify(source_store, ref)
    destination_store = Path(destination_store).resolve()
    target = destination_store / identifier(ref['artifact_id'])
    with locked(destination_store / '.transfer.lock'):
        if target.exists():
            verify(destination_store, ref)
            return ref
        staging = destination_store / '.incoming' / new_id('transfer')
        staging.mkdir(parents=True, mode=0o700)
        shutil.copytree(Path(source_store).resolve() / ref['artifact_id'], staging / ref['artifact_id'], symlinks=True)
        verify(staging, ref)
        (staging / ref['artifact_id']).rename(target)
        atomic(destination_store / 'transfers' / (ref['artifact_id'] + '.json'),
               record('artifact-transfer', reference=ref, source_store=str(Path(source_store).resolve()), verified_at=time.time()))
        return ref
