"""One retained workspace snapshot, shared by outputs, capture and terminal evidence."""
from pathlib import Path
import shutil
import time

from . import artifacts
from .core import Blocked, atomic, canonical, locked, member, new_id, read, record, require


def workspace_root(directory):
    directory = Path(directory)
    assembly = directory / 'assembly.json'
    return Path(read(assembly)['workspace']) if assembly.exists() else directory / 'workspace'


def _retain_binding(binding, attempt, purpose):
    store, ref = binding['store'], binding['reference']
    artifacts._manifest(store, ref)
    binding['retention'] = artifacts.retain(store, ref, attempt['attempt_id'], purpose,
        'snapshot-retain-' + canonical([attempt['attempt_id'], ref, purpose])[:40])
    return binding


def seal_workspace(directory, attempt, receipt, *, capture=None, physical_root=None, window=None, acquisition=None, request_scope=None):
    """Freeze once, or consume the snapshot installed before a state handoff.

    A content snapshot makes no writer-closure or checkpoint-completeness claim.
    Managed capture supplies those facts separately. A later caller never reads
    the active state after the attempt has a durable snapshot binding.
    """
    directory = Path(directory)
    workspace = workspace_root(directory)
    source = Path(physical_root) if physical_root is not None else workspace
    acquisition = dict(acquisition or {'kind': 'terminal-content-copy',
        'checkpoint': False, 'gaps': ['cross-file cut and unregistered descendant writer closure are not proven']})
    if acquisition['kind'] not in ('terminal-content-copy', 'managed-writer-capture'):
        raise ValueError('unsupported workspace acquisition')
    if request_scope and acquisition['kind'] != 'managed-writer-capture':
        raise ValueError('request-scoped recovery snapshot requires managed capture')
    prefix = ('capture-' + canonical(request_scope)[:24]) if request_scope else 'terminal'
    binding_path = directory / (prefix + '-snapshot.json')
    with locked(directory / '.workspace-seal.lock'):
        if binding_path.exists():
            binding = require(read(binding_path), 'workspace-snapshot-binding')
            if (binding['attempt_id'] != attempt['attempt_id'] or
                    binding['incarnation_id'] != receipt['incarnation_id'] or
                    binding['source_root'] != str(workspace.absolute())):
                raise Blocked('workspace snapshot belongs to another attempt, incarnation or layout')
            if acquisition['kind'] == 'managed-writer-capture' and binding.get('acquisition') != acquisition:
                raise Blocked('workspace snapshot was sealed under another acquisition; use the capture request scope')
            member(binding.get('member', '.'))
            return _retain_binding(binding, attempt, 'terminal-workspace')
        stage = directory / (prefix + '-snapshot-staging')
        staged = directory / (prefix + '-snapshot-staging.json')
        if not staged.exists():
            if source.is_symlink() or not source.is_dir():
                raise Blocked('workspace snapshot requires an actual state directory')
            if capture is None:
                from .runner import _capture_definitions
                capture = _capture_definitions(source, attempt['artifact_store'], attempt['attempt_id'] + '--snapshot')
            excluded = {row['path'] for row in capture['definitions']}
            if stage.exists():
                stage.rename(directory / new_id('workspace-snapshot-partial'))
            reserve = attempt['job']['limits'].get('storage_reserve_bytes', attempt['job']['limits']['storage_bytes'])
            if shutil.disk_usage(directory).free <= reserve:
                raise Blocked('workspace snapshot storage reserve unavailable; state remains intact')
            def omit(parent, names):
                relative = Path(parent).relative_to(source)
                return [name for name in names if (relative / name).as_posix() in excluded]
            observed_start = time.time()
            shutil.copytree(source, stage, symlinks=True, copy_function=artifacts.copy_file, ignore=omit)
            definitions = list(capture['definitions'])
            assembly_path = directory / 'assembly.json'
            if assembly_path.exists():
                for row in read(assembly_path).get('definitions', []):
                    if row.get('reference'):
                        selected = member(row.get('member', '.'))
                        hold = artifacts.retain(attempt['artifact_store'], row['reference'], attempt['attempt_id'],
                            'snapshot-definition/' + row['role'],
                            'snapshot-def-' + canonical([attempt['attempt_id'], row['reference'], selected, row['role']])[:40])
                        definitions.append({'role': row['role'], 'artifact': row['reference'], 'member': selected,
                                            'store': attempt['artifact_store'], 'retention': hold})
            capabilities = {'checkpoint': False, 'workspace_composition': 'state-and-definition-relations',
                            'definitions': definitions,
                            'excluded_definitions': [{'path': row['path'], 'reference': row['artifact'],
                                'member': row.get('member', '.')} for row in capture['definitions']],
                            'capture_gaps': capture['gaps'], 'acquisition': acquisition}
            atomic(staged, record('workspace-snapshot-staging', status='sealed',
                attempt_id=attempt['attempt_id'], incarnation_id=receipt['incarnation_id'],
                source_root=str(workspace.absolute()), readback_root=str(source.absolute()),
                capabilities=capabilities, acquisition=acquisition,
                observation_started_at=observed_start, sealed_at=time.time()))
        descriptor = require(read(staged), 'workspace-snapshot-staging')
        if descriptor['attempt_id'] != attempt['attempt_id'] or descriptor['incarnation_id'] != receipt['incarnation_id']:
            raise Blocked('workspace snapshot staging belongs to another execution')
        if descriptor.get('acquisition') != acquisition:
            raise Blocked('workspace snapshot staging was sealed under another acquisition')
        ref = artifacts.publish(attempt['artifact_store'], stage, 'workspace-snapshot',
            {'attempt_id': attempt['attempt_id'], 'incarnation_id': receipt['incarnation_id'],
             'source_root': descriptor['source_root'], 'acquisition': acquisition}, descriptor['capabilities'],
            request_id=attempt['attempt_id'] + '--' + prefix + '--workspace-snapshot', consumer=attempt['attempt_id'],
            purpose='terminal-workspace', move_source=True, _readback=window)
        binding = record('workspace-snapshot-binding', attempt_id=attempt['attempt_id'],
            incarnation_id=receipt['incarnation_id'], reference=ref, store=str(attempt['artifact_store']),
            member='.', source_root=descriptor['source_root'], capabilities=descriptor['capabilities'],
            sealed_at=descriptor['sealed_at'], acquisition=acquisition,
            observation_started_at=descriptor['observation_started_at'])
        _retain_binding(binding, attempt, 'terminal-workspace')
        atomic(binding_path, binding)
        return binding


def resolve_workspace(binding, attempt, *, window=None):
    """Verify one snapshot consumption window; it cannot redirect to active state."""
    resolver = window.resolve if window is not None else artifacts.resolve
    return resolver(binding['store'], binding['reference'], member(binding.get('member', '.')),
        consumer=attempt['attempt_id'], retention=binding['retention'])
