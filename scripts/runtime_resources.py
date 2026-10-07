"""Register Linux process ownership and honor explicit execution-stop fences."""

import argparse
from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path
import sys
import time
import uuid


def _cgroup_v2_path():
    """Resolve this process' cgroup without guessing a host path."""
    try:
        membership = next(line[3:] for line in Path('/proc/self/cgroup').read_text().splitlines()
                          if line.startswith('0::'))
        for line in Path('/proc/self/mountinfo').read_text().splitlines():
            before, separator, after = line.partition(' - ')
            if not separator or not after.split() or after.split()[0] != 'cgroup2':
                continue
            fields = before.split()
            root, mount = Path(fields[3]), Path(fields[4])
            if membership == '/':
                return mount
            if Path(membership).is_relative_to(root):
                candidate = mount / Path(membership).relative_to(root)
                return candidate if '..' not in candidate.parts else None
    except (OSError, StopIteration, IndexError, ValueError):
        return None
    return None


def _resource_snapshot():
    """Read kernel resource facts; this never decides whether to start work."""
    cgroup = _cgroup_v2_path()
    result = {'schema_version': 1, 'observed_at_ns': time.time_ns(),
              'cgroup_path': str(cgroup) if cgroup else None, 'values': {}, 'errors': {}}
    if cgroup is None:
        result['errors']['cgroup'] = {'type': 'Unavailable', 'message': 'cgroup v2 is not visible'}
        return result
    for name in ('memory.current', 'memory.max', 'memory.events', 'pids.current',
                 'pids.max', 'pids.events'):
        try:
            result['values'][name] = (cgroup / name).read_text().strip()
        except OSError as error:
            result['errors'][name] = {'type': type(error).__name__, 'errno': error.errno,
                                      'message': str(error)}
    return result


def observe(directory):
    """Persist one bounded resource observation for the run owner."""
    value = _resource_snapshot()
    path = Path(directory) / 'resource-observations'
    write_json(path / f"{value['observed_at_ns']}.json", value)
    return value


def reclaim(directory):
    """Attempt only kernel cache reclaim; never kill an unclassified process."""
    cgroup = _cgroup_v2_path()
    if cgroup is None:
        return {'status': 'unknown', 'reason': 'cgroup v2 is not visible', 'observed_at_ns': time.time_ns()}
    target = cgroup / 'memory.reclaim'
    if not target.exists():
        return {'status': 'unsupported', 'reason': 'memory.reclaim is unavailable',
                'cgroup_path': str(cgroup), 'observed_at_ns': time.time_ns()}
    try:
        current = int((cgroup / 'memory.current').read_text().strip())
        amount = max(0, min(current, 256 * 1024 * 1024))
        if amount == 0:
            return {'status': 'no-op', 'reason': 'memory.current is zero',
                    'cgroup_path': str(cgroup), 'observed_at_ns': time.time_ns()}
        target.write_text(str(amount))
        return {'status': 'requested', 'requested_bytes': amount,
                'cgroup_path': str(cgroup), 'observed_at_ns': time.time_ns()}
    except OSError as error:
        return {'status': 'failed', 'reason': f'{type(error).__name__}: {error}',
                'errno': error.errno, 'cgroup_path': str(cgroup),
                'observed_at_ns': time.time_ns()}


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


def launch(args, directory):
    uuid.UUID(args.start_id)
    command = args.command[1:] if args.command[:1] == ['--'] else args.command
    if not command:
        raise ValueError('launch requires a payload command')
    execution_id = os.environ['FACTORY_NATIVE_EXECUTION_ID']
    execution_dir = Path(os.environ['FACTORY_NATIVE_EXECUTION_DIR'])
    uuid.UUID(execution_id)
    if os.getpgrp() != os.getpid():
        os.setsid()
    identity = process_identity(os.getpid())
    if identity['pgid'] != identity['pid']:
        raise ValueError('launch does not own its process group')
    receipt = directory / 'starts' / f'{args.start_id}.json'
    record_path = execution_dir / 'processes' / f'{args.start_id}.json'
    # Registration and the shutdown fence share one lock; pressure never denies a start.
    with locked(directory):
        if record_path.exists() or receipt.exists():
            raise ValueError('a process start identity cannot be reused')
        if (execution_dir / 'stopping.json').exists():
            denied = {'schema_version': 1, 'status': 'start_rejected',
                      'reason': 'execution_stopping', 'start_id': args.start_id,
                      'execution_id': execution_id, 'observed_at_ns': time.time_ns()}
            write_json(receipt, denied)
            print(json.dumps(denied), file=sys.stderr, flush=True)
            return 75
        record = {'schema_version': 1, 'start_id': args.start_id, 'execution_id': execution_id,
                  'parent_start_id': os.environ.get('FACTORY_NATIVE_START_ID'),
                  'kind': args.kind, 'service': args.service, **identity,
                  'created_at_ns': time.time_ns()}
        if args.manifest:
            record['manifest_path'] = args.manifest
        write_json(record_path, record)
        write_json(receipt, {'schema_version': 1, 'status': 'started',
                             'start_id': args.start_id, 'execution_id': execution_id,
                             'process_record': str(record_path), 'pid': identity['pid'],
                             'observed_at_ns': time.time_ns()})
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
    configure = commands.add_parser('configure')
    configure.add_argument('--directory', type=Path, dest='operation_directory', required=True)
    # Accept an old caller's sample argument without requiring it or consulting pressure.
    configure.add_argument('--sample-path', type=Path)
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
        policy = {'schema_version': 3, 'pressure_gate': False,
                  'resource_observation': 'memory-and-pids-cgroup-v2',
                  'lifecycle': 'process-identity-and-explicit-stop-fence'}
        with locked(directory):
            write_json(directory / 'ownership-policy.json', policy)
        print(json.dumps(policy))
    elif args.operation == 'observe':
        print(json.dumps(observe(directory), ensure_ascii=False))
    elif args.operation == 'reclaim':
        print(json.dumps(reclaim(directory), ensure_ascii=False))
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
