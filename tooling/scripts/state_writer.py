"""Join the existing state authority at actual process launch boundaries."""
import os
import subprocess
import sys
import uuid
from pathlib import Path

try:
    from . import execution_context
except ImportError:
    import execution_context


def binding(environment=None):
    environment = environment or os.environ
    path = environment.get('FACTORY26_EXECUTION_CONTEXT')
    if not path:
        return None
    context = execution_context.read(path)
    holder = context['assembly']['state'].get('holder')
    return holder if holder and holder['authority']['kind'] == 'local' else None


def gate(environment=None):
    holder = binding(environment)
    if holder:
        from lab.exp.state import permit
        writer = holder['writer']
        permit(holder, writer['resource_id'], writer['incarnation'], holder['generation'])
    return holder


def started(pid, *, role, environment=None):
    holder = gate(environment)
    if holder is None:
        return None
    from lab.exp.core import process_identity, canonical
    from lab.exp.state import register_writer
    physical = process_identity(pid)
    resource_id = 'writer-' + canonical(physical)[:40]
    writer = holder['writer']
    register_writer(holder, resource_id, writer['incarnation'], physical, role=role, parent=writer['resource_id'])
    return {'binding': holder, 'resource_id': resource_id, 'physical': physical, 'role': role}


def closed(receipt):
    if receipt is None:
        return
    from lab.exp.state import register_writer
    holder = receipt['binding']
    physical = receipt.get('physical')
    if physical is None:
        from lab.exp.core import locked, read
        root = Path(holder['authority']['root'])
        with locked(root / '.state.lock'):
            row = read(root / 'state-registry.json')['resources'][receipt['resource_id']]
            physical = row['identity']
    register_writer(holder, receipt['resource_id'], holder['writer']['incarnation'], physical,
                    role=receipt['role'], closed=True,
                    shutdown={'closed': True, 'physical': physical, 'contract': 'owner-waited-same-birth-v1'})


def spawn(command, *, environment, role, **options):
    """Reserve before Popen; the child binds its birth before payload execution."""
    holder = gate(environment)
    if holder is None:
        process = subprocess.Popen(command, env=environment, **options)
        process._state_writer = None
        return process
    from lab.exp.state import reserve_writer, bind_writer
    resource_id = 'writer-' + uuid.uuid4().hex
    request_id = resource_id + '--launch'
    writer = holder['writer']
    reserve_writer(holder, resource_id, writer['incarnation'], request_id,
                   parent=writer['resource_id'], role=role)
    launcher = [sys.executable, '-B', str(Path(__file__).resolve()), '--context', environment['FACTORY26_EXECUTION_CONTEXT'],
                '--resource', resource_id, '--request', request_id, '--', *command]
    try:
        process = subprocess.Popen(launcher, env=environment, **options)
    except OSError as error:
        bind_writer(holder, resource_id, request_id, failed_spawn={'spawn_effect': 'not-created', 'errno': error.errno, 'message': str(error)})
        raise
    process._state_writer = {'binding': holder, 'resource_id': resource_id, 'role': role}
    return process


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--context', required=True)
    parser.add_argument('--resource', required=True)
    parser.add_argument('--request', required=True)
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    os.environ['FACTORY26_EXECUTION_CONTEXT'] = args.context
    holder = binding()
    from lab.exp.core import process_identity
    from lab.exp.state import bind_writer
    bind_writer(holder, args.resource, args.request, physical=process_identity())
    gate()
    command = args.command[1:] if args.command[:1] == ['--'] else args.command
    if not command:
        raise ValueError('state writer launch needs a payload command')
    os.execvpe(command[0], command, os.environ)
