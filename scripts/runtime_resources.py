"""Share Linux process-start admission without owning native job results."""

import argparse
from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path
import sys
import time
import uuid


MIB = 1024 * 1024


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary = path.with_name(f'.{path.name}.{uuid.uuid4().hex}.tmp')
    try:
        with temporary.open('x') as stream:
            os.chmod(temporary, 0o600)
            json.dump(value, stream, ensure_ascii=False)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def read_json(path):
    return json.loads(path.read_text())


def process_identity(pid):
    fields = Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()
    return {'pid': pid, 'pgid': int(fields[2]), 'starttime': int(fields[19]),
            'state': fields[0],
            'boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip()}


def still_running(record):
    try:
        current = process_identity(record['pid'])
    except FileNotFoundError:
        return False
    return (current['boot_id'] == record['boot_id'] and
            current['starttime'] == record['starttime'] and
            current['state'] not in {'Z', 'X'})


@contextmanager
def locked(directory):
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (directory / 'admission.lock').open('a') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        yield


def key_values(raw):
    return {key: int(value) for key, value in
            (line.split() for line in raw.splitlines() if line.strip())}


def pressure_values(raw):
    return {parts[0]: {key: float(value) for key, value in
                      (field.split('=', 1) for field in parts[1:])}
            for parts in (line.split() for line in raw.splitlines()) if parts}


def current_pressure(directory):
    """Use charged memory and stalls; cache credit is a bounded estimate."""
    policy = read_json(directory / 'policy.json')
    sample = read_json(Path(policy['sample_path']))
    age = time.monotonic_ns() - sample['sample_started']['monotonic_ns']
    if age < 0 or age > 10_000_000_000:
        raise ValueError(f'resource sample is stale or from another boot: age_ns={age}')
    cgroup = Path(sample['cgroup_path'])
    identity = cgroup.stat()
    if sample['cgroup_identity'] != {'device': identity.st_dev, 'inode': identity.st_ino}:
        raise ValueError('resource sample cgroup identity changed')
    # Read the charge again while holding admission's lock. The two-second process
    # inventory remains evidence, but is too old to serialize simultaneous starts.
    current = int((cgroup / 'memory.current').read_text())
    maximum = (cgroup / 'memory.max').read_text().strip()
    if maximum == 'max':
        raise ValueError('a finite cgroup memory.max is required by this resource policy')
    maximum = int(maximum)
    if maximum <= 0 or current < 0:
        raise ValueError('invalid cgroup memory charge or limit')
    stat = key_values((cgroup / 'memory.stat').read_text())
    events = key_values((cgroup / 'memory.events').read_text())
    psi_error = None
    try:
        psi = pressure_values((cgroup / 'memory.pressure').read_text())
    except OSError as error:
        psi, psi_error = {}, {'type': type(error).__name__, 'errno': error.errno,
                              'message': str(error)}
    some = psi.get('some', {}).get('avg10')
    full = psi.get('full', {}).get('avg10')
    inactive = max(0, stat.get('inactive_file', 0))
    # ponytail: a conservative cache estimate; tune from real reclaim evidence,
    # rather than treating every cached byte as either pinned or free memory.
    credit = min(inactive, maximum // 4) if (some is not None and some < 5 and
                                                   full is not None and full < 0.5) else 0
    adjusted = max(0, current - credit)
    sample_id = str(sample['sample_started']['monotonic_ns'])
    previous_path = directory / 'pressure.json'
    previous = read_json(previous_path) if previous_path.exists() else {}
    previous_events = previous.get('oom_kill')
    oom_increased = previous_events is not None and events.get('oom_kill', 0) > previous_events
    if oom_increased or adjusted >= maximum * 0.90 or (full is not None and full >= 10):
        status, reason = 'critical', 'oom_or_sustained_memory_pressure'
    elif adjusted >= maximum * 0.80 or (full is not None and full >= 2) or (
            some is not None and some >= 20):
        status, reason = 'pressured', 'memory_headroom_or_reclaim_pressure'
    else:
        status, reason = 'normal', 'memory_headroom_available'
    recovered = (adjusted < maximum * 0.70 and
                 (some is None or some < 5) and (full is None or full < 0.5))
    good_samples = 0
    if previous.get('status') in {'pressured', 'critical'} and status == 'normal':
        if recovered:
            good_samples = previous.get('good_samples', 0) + int(sample_id != previous.get('sample_id'))
        if good_samples < 2:
            status, reason = 'pressured', 'waiting_for_two_recovered_samples'
    result = {'schema_version': 1, 'status': status, 'reason': reason, 'sample_id': sample_id,
              'observed_at_ns': time.time_ns(), 'memory_current': current, 'memory_max': maximum,
              'inactive_file': inactive, 'cache_credit_estimate': credit,
              'accounted_for_admission': adjusted, 'charged_headroom': max(0, maximum-current),
              'psi': psi, 'psi_error': psi_error, 'oom_kill': events.get('oom_kill', 0),
              'good_samples': good_samples,
              'startup_reserve_bytes': policy['startup_reserve_bytes'],
              'headroom_reserve_bytes': policy['headroom_reserve_bytes']}
    write_json(previous_path, result)
    return result


def status(directory):
    try:
        return current_pressure(directory)
    except (OSError, ValueError, KeyError, TypeError) as error:
        return {'schema_version': 1, 'status': 'unavailable',
                'reason': f'{type(error).__name__}: {error}',
                'errno': getattr(error, 'errno', None), 'observed_at_ns': time.time_ns()}


def live_reservations(directory):
    path = directory / 'admission.json'
    saved = read_json(path) if path.exists() else {}
    active = {}
    for start_id, reservation in saved.items():
        record = read_json(Path(reservation['process_record']))
        if still_running(record):
            active[start_id] = reservation
    return active


def launch(args, directory):
    uuid.UUID(args.start_id)
    command = args.command[1:] if args.command[:1] == ['--'] else args.command
    if not command:
        raise ValueError('launch requires a payload command')
    execution_id = os.environ['FACTORY_NATIVE_EXECUTION_ID']
    execution_dir = Path(os.environ['FACTORY_NATIVE_EXECUTION_DIR'])
    uuid.UUID(execution_id)
    # The launcher becomes the payload: there is no spawn-to-registration gap.
    if os.getpgrp() != os.getpid():
        os.setsid()
    identity = process_identity(os.getpid())
    if identity['pgid'] != identity['pid']:
        raise ValueError('launch does not own its process group')
    receipt = directory / 'starts' / f'{args.start_id}.json'
    record_path = execution_dir / 'processes' / f'{args.start_id}.json'
    with locked(directory):
        if record_path.exists() or receipt.exists():
            raise ValueError('a process start identity cannot be reused')
        resource = status(directory)
        reason = None
        admission_error = None
        try:
            active = live_reservations(directory)
        except (OSError, ValueError, KeyError, TypeError) as error:
            active = None
            reason = f'admission_unavailable: {type(error).__name__}: {error}'
            admission_error = {'type': type(error).__name__, 'errno': getattr(error, 'errno', None),
                               'message': str(error)}
        if reason is not None:
            pass
        elif (execution_dir / 'stopping.json').exists():
            reason = 'execution_stopping'
        elif resource['status'] != 'normal':
            reason = resource['reason']
        else:
            reserved = sum(item['reserved_bytes'] for item in active.values())
            requested = resource['startup_reserve_bytes']
            # Reservations are a startup floor, not a second sum of process RSS.
            projected = max(resource['accounted_for_admission'], reserved) + requested
            if projected > resource['memory_max'] - resource['headroom_reserve_bytes']:
                reason = 'startup_headroom_reserved'
        if reason:
            denied = {'schema_version': 1, 'status': 'resource_deferred', 'reason': reason,
                      'start_id': args.start_id, 'execution_id': execution_id,
                      'pressure': resource, 'admission_error': admission_error,
                      'observed_at_ns': time.time_ns()}
            write_json(receipt, denied)
            if active is not None:
                write_json(directory / 'admission.json', active)
            print(json.dumps(denied, ensure_ascii=False), file=sys.stderr, flush=True)
            return 75
        record = {'schema_version': 1, 'start_id': args.start_id, 'execution_id': execution_id,
                  'parent_start_id': os.environ.get('FACTORY_NATIVE_START_ID'),
                  'kind': args.kind, 'service': args.service, **identity,
                  'created_at_ns': time.time_ns()}
        if args.manifest:
            record['manifest_path'] = args.manifest
        write_json(record_path, record)
        active[args.start_id] = {'process_record': str(record_path),
                                 'reserved_bytes': resource['startup_reserve_bytes']}
        write_json(directory / 'admission.json', active)
        write_json(receipt, {'schema_version': 1, 'status': 'started',
                             'start_id': args.start_id, 'execution_id': execution_id,
                             'process_record': str(record_path), 'pid': identity['pid'],
                             'pressure': resource, 'observed_at_ns': time.time_ns()})
    environment = dict(os.environ, FACTORY_NATIVE_START_ID=args.start_id)
    try:
        os.execvpe(command[0], command, environment)
    except OSError as error:
        failure = {'schema_version': 1, 'status': 'exec_failed', 'start_id': args.start_id,
                   'execution_id': execution_id, 'errno': error.errno,
                   'reason': f'{type(error).__name__}: {error.strerror}',
                   'observed_at_ns': time.time_ns()}
        write_json(receipt, failure)
        print(json.dumps(failure, ensure_ascii=False), file=sys.stderr, flush=True)
        return 126


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path)
    commands = parser.add_subparsers(dest='operation', required=True)
    check = commands.add_parser('status')
    check.add_argument('--directory', type=Path, dest='operation_directory')
    configure = commands.add_parser('configure')
    configure.add_argument('--directory', type=Path, dest='operation_directory', required=True)
    configure.add_argument('--sample-path', type=Path, required=True)
    configure.add_argument('--startup-reserve-mib', type=int, default=128)
    configure.add_argument('--headroom-reserve-mib', type=int, default=256)
    fence = commands.add_parser('fence')
    fence.add_argument('--execution-dir', type=Path, required=True)
    fence.add_argument('--execution-id', required=True)
    run = commands.add_parser('launch')
    run.add_argument('--start-id', required=True)
    run.add_argument('--kind', choices=['native', 'tool'], required=True)
    run.add_argument('--manifest')
    run.add_argument('--service', action='store_true')
    run.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    directory = (getattr(args, 'operation_directory', None) or args.directory or
                 Path(os.environ['FACTORY_RESOURCE_DIR'])).resolve()
    if args.operation == 'configure':
        if args.startup_reserve_mib <= 0 or args.headroom_reserve_mib <= 0:
            raise ValueError('resource reserves must be positive')
        policy = {'schema_version': 1, 'sample_path': str(args.sample_path.resolve()),
                  'startup_reserve_bytes': args.startup_reserve_mib * MIB,
                  'headroom_reserve_bytes': args.headroom_reserve_mib * MIB}
        with locked(directory):
            write_json(directory / 'policy.json', policy)
        print(json.dumps(policy))
    elif args.operation == 'status':
        with locked(directory):
            print(json.dumps(status(directory), ensure_ascii=False))
    elif args.operation == 'fence':
        uuid.UUID(args.execution_id)
        with locked(directory):
            write_json(args.execution_dir / 'stopping.json',
                       {'execution_id': args.execution_id, 'requested_at_ns': time.time_ns()})
        print(json.dumps({'status': 'fenced', 'execution_id': args.execution_id}))
    else:
        return launch(args, directory)
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({'status': 'error', 'reason': f'{type(error).__name__}: {error}',
                          'errno': getattr(error, 'errno', None)}, ensure_ascii=False),
              file=sys.stderr)
        sys.exit(1)
