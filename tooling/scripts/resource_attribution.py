"""Join saved resource samples to native ownership; never inspect live credentials."""
import argparse
import json
from pathlib import Path


def archived_member(harness, source):
    """Resolve only members of this harness; archived absolute paths are not live paths."""
    if not source:
        return None
    harness = Path(harness).resolve()
    parts = Path(source).parts
    anchor = ('data', 'harness', harness.name)
    indexes = [i for i in range(len(parts)-2) if tuple(parts[i:i+3]) == anchor]
    if len(indexes) != 1:
        return None
    relative = Path(*parts[indexes[0]+3:])
    target = (harness/relative).resolve()
    return target if target.is_relative_to(harness) else None


def ownership_index(harness):
    records, errors = {}, []
    homes = Path(harness)/'work/native-homes'
    for path in homes.glob('*/managed-executions/*/processes/*.json'):
        try:
            row = json.loads(path.read_text())
            key = (row['boot_id'], row['pid'], row['starttime'])
            if not key[0] or not isinstance(key[1], int) or not isinstance(key[2], int):
                raise ValueError('invalid process birth identity')
            owner = {key: row.get(key) for key in ('execution_id', 'start_id', 'parent_start_id', 'kind', 'service', 'manifest_path', 'ns/pid', 'ns/cgroup')}
            owner['record_path'] = str(path)
            job_path = archived_member(harness, row.get('manifest_path'))
            if job_path is not None and job_path.is_file():
                try:
                    job = json.loads(job_path.read_text())
                    owner['job_evidence'] = {key: job[key] for key in (
                        'jobId', 'globalJobId', 'toolCallId', 'sessionId', 'instanceId',
                        'startedAt', 'completedAt', 'status', 'run_id', 'role',
                        'parent_session_id', 'child_session_id') if key in job}
                    owner['job_evidence']['source'] = str(job_path)
                except (OSError, ValueError) as error:
                    owner['job_evidence_error'] = {'path': str(job_path), 'error': str(error)}
            state = path.parent.parent/'native-state-latest.json'
            if state.is_file():
                native = json.loads(state.read_text())
                if native.get('expected_execution_id') == row['execution_id']:
                    owner['native_session_id'] = native.get('native_session_id')
                    owner['native_state_path'] = str(state)
                    owner['session_binding_observed_at_unix_nanos'] = native.get('observed_at_unix_nanos')
            records.setdefault(key, []).append(owner)
        except (OSError, ValueError, KeyError) as error:
            errors.append({'path': str(path), 'error': str(error)})
    sessions = {}
    for relative, field in (('native/manifest.json', 'sessions'), ('braid-state/status.json', 'physical_sessions')):
        manifest = Path(harness)/relative
        if not manifest.is_file():
            continue
        try:
            for session in json.loads(manifest.read_text()).get(field, []):
                if session.get('native_session_id'):
                    evidence = {key: session.get(key) for key in (
                        'group_id', 'profile_id', 'context_path', 'assignment_generation',
                        'work_item_id', 'work_item_kind', 'turns')}
                    evidence['source'] = str(manifest)
                    sessions.setdefault(session['native_session_id'], []).append(evidence)
        except (OSError, ValueError) as error:
            errors.append({'path': str(manifest), 'error': str(error)})
    return records, sessions, errors


def attribute(sample, records, sessions, boot_id=None):
    boot = sample.get('boot_id') or boot_id
    processes = {row['pid']: row for row in sample.get('processes', [])}
    results = []
    for process in processes.values():
        current, seen, via = process, set(), 'registered-birth-identity'
        owners = []
        while current and current['pid'] not in seen:
            seen.add(current['pid'])
            owners = records.get((boot, current['pid'], current.get('starttime')), []) if boot else []
            owners = [owner for owner in owners if not owner.get('ns/pid') or
                      (owner.get('ns/pid') == current.get('ns/pid') and
                       owner.get('ns/cgroup') == current.get('ns/cgroup'))]
            if owners:
                break
            current = processes.get(current.get('ppid'))
            via = 'observed-ancestor'
        result = {'pid': process['pid'], 'starttime': process.get('starttime'),
                  'status': 'matched' if len(owners) == 1 else 'ambiguous' if owners else 'unknown',
                  'method': via if owners else None, 'owners': owners}
        if len(owners) == 1:
            result['namespace_evidence'] = ('matched' if owners[0].get('ns/pid') else 'legacy-registration-missing')
            result['session_evidence'] = sessions.get(owners[0].get('native_session_id'), [])
            # A current manifest lists candidates, not the turn active at this historical instant.
            result['active_turn_status'] = 'unknown'
        results.append(result)
    return {'sample_started': sample.get('sample_started'), 'boot_id': boot,
            'attribution': results, 'scope': 'same-execution-archive-visible-process-tree'}


def counter_rates(sample, previous):
    """Only compare counters from the same boot, namespace and process birth."""
    current, rates = {}, []
    for process in sample.get('processes', []):
        key = (sample.get('boot_id'), process.get('ns/pid'), process['pid'], process.get('starttime'))
        stamp = process.get('counter_read_started', sample.get('sample_started', {})).get('monotonic_ns')
        if not key[0] or key[3] is None or stamp is None or process.get('counter_identity_matches') is False:
            continue
        current[key] = (stamp, process)
        old = previous.get(key)
        rate = {'pid': process['pid'], 'starttime': process.get('starttime'), 'status': 'no_previous_sample'}
        if old is not None and stamp > old[0]:
            elapsed = (stamp-old[0])/1e9
            rate.update(status='observed', interval_seconds=elapsed, counters_per_second={})
            for name in ('cpu_ticks', 'io_bytes'):
                left, right = old[1].get(name), process.get(name)
                if name == 'cpu_ticks':
                    left, right = {'cpu_ticks': left}, {'cpu_ticks': right}
                if not isinstance(left, dict) or not isinstance(right, dict):
                    continue
                for field, value in right.items():
                    before = left.get(field)
                    if not isinstance(value, int) or not isinstance(before, int):
                        continue
                    if value >= before:
                        rate['counters_per_second'][field] = (value-before)/elapsed
                    else:
                        rate.setdefault('counter_resets', []).append(field)
            if not rate['counters_per_second']:
                rate['status'] = 'counters_unavailable_or_reset'
        elif old is not None:
            rate['status'] = 'non_increasing_sample_time'
        rates.append(rate)
    return current, rates


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--harness', required=True, type=Path)
    parser.add_argument('--samples', required=True, type=Path)
    args = parser.parse_args()
    records, sessions, errors = ownership_index(args.harness)
    boot = None
    baseline = args.samples.parent/'resources-baseline.jsonl'
    if baseline.is_file():
        for line in baseline.open():
            row = json.loads(line)
            boot = row.get('raw', {}).get('/proc/sys/kernel/random/boot_id', '').strip() or boot
    print(json.dumps({'kind': 'attribution_capabilities', 'registration_identities': len(records),
                      'errors': errors, 'historical_turn_inference': 'unavailable'}))
    previous = {}
    with args.samples.open() as stream:
        for line in stream:
            row = json.loads(line)
            samples = [row] if 'processes' in row else ([*row.get('preceding_samples', []), row['sample']]
                                                       if row.get('kind') == 'resource_incident' else [])
            for sample in samples:
                sample = {**sample, 'boot_id': sample.get('boot_id') or boot}
                previous, rates = counter_rates(sample, previous)
                result = attribute(sample, records, sessions, boot)
                result['process_rates'] = rates
                print(json.dumps(result))


if __name__ == '__main__':
    main()
