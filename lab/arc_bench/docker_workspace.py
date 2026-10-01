"""Attempt-owned workspace copies at the ARC Runner's Docker boundary."""

import argparse
import importlib.util
import json
import os
from pathlib import Path
import secrets
import shutil
import signal
import subprocess
import sys
import tarfile
import tempfile
from types import SimpleNamespace

if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from lab.docker_endpoint import confirm, environment, execute, freeze
from lab.records import inventory, read_json, write_json

# Use the same inventory implementation on both hosts, without platform metadata.
REMOTE_INVENTORY = Path(sys.modules[inventory.__module__].__file__).read_text() + '\nprint(json.dumps(inventory(Path(sys.argv[1]))))'
REMOTE_INVENTORY = 'import sys\n' + REMOTE_INVENTORY
LABEL_PREFIX = 'io.factory26.'


def selected_endpoint():
    saved = os.environ.get('EXPERIMENT_DOCKER_ENDPOINT')
    return json.loads(saved) if saved else freeze()


def error_text(error):
    output = getattr(error, 'stdout', None) or getattr(error, 'output', None) or ''
    stderr = getattr(error, 'stderr', None) or ''
    if isinstance(output, bytes):
        output = output.decode(errors='replace')
    if isinstance(stderr, bytes):
        stderr = stderr.decode(errors='replace')
    return f'{type(error).__name__}: {error}\n{output}\n{stderr}'.strip()


def docker(endpoint, args, *, timeout=60, **kwargs):
    confirm(endpoint)
    return execute(endpoint, args, check=True, timeout=timeout, **kwargs)


def inspect(endpoint, kind, identifier):
    try:
        return json.loads(docker(endpoint, [kind, 'inspect', identifier], text=True, capture_output=True, timeout=10).stdout)[0]
    except subprocess.CalledProcessError as error:
        if f'no such {kind}' in (error.stderr or '').lower():
            return None
        raise


def labels_match(value, expected):
    actual = value.get('Labels') or value.get('Config', {}).get('Labels') or {}
    return all(actual.get(key) == content for key, content in expected.items())


def volume_owned(transport):
    volume = inspect(transport['endpoint'], 'volume', transport['volume'])
    if volume is not None and (volume.get('Name') != transport['volume'] or
                               not labels_match(volume, transport['labels'])):
        raise ValueError('workspace volume ownership mismatch')
    return volume


def container_owned(resource):
    endpoint = resource['endpoint']
    identifier = resource.get('container_id') or resource.get('container_name')
    if not identifier:
        return None
    value = inspect(endpoint, 'container', identifier)
    if value is None:
        return None
    if resource.get('container_id') and value['Id'] != resource['container_id']:
        raise ValueError('container ID ownership mismatch')
    if value.get('Image') != resource['image_id']:
        raise ValueError('container image ownership mismatch')
    if resource.get('labels') and not labels_match(value, resource['labels']):
        raise ValueError('container labels ownership mismatch')
    if resource.get('volume'):
        transport = read_json(Path(resource['transport']))
        volume = volume_owned(transport)
        if volume is None or not labels_match(value, resource['labels']):
            raise ValueError('container/volume labels ownership mismatch')
        expected_source = volume['Mountpoint']
        mounted = any(mount.get('Type') == 'volume' and mount.get('Name') == resource['volume'] and
                      mount.get('Source') == expected_source and mount.get('Destination') == '/workspace'
                      for mount in value.get('Mounts', []))
        mounted = mounted and any(mount.get('Type') == 'volume' and mount.get('Source') == resource['volume'] and
                                  mount.get('Target') == '/workspace' and
                                  mount.get('VolumeOptions', {}).get('Subpath') == resource['stage']
                                  for mount in value.get('HostConfig', {}).get('Mounts', []))
    else:
        mounted = any(mount.get('Type') == 'bind' and mount.get('Source') == resource['workspace'] and
                      mount.get('Destination') == '/workspace' for mount in value.get('Mounts', []))
    if not mounted:
        raise ValueError(f"container workspace mount ownership mismatch: {value.get('Mounts')}")
    return value


def observe(path, *, cleanup=False):
    resource = read_json(path)
    record = {'resource': str(path), 'container_name': resource.get('container_name'),
              'container_id': resource.get('container_id'), 'workspace': resource['workspace'],
              'endpoint': resource.get('endpoint')}
    if not resource.get('image_id'):
        return {**record, 'status': 'not-applicable'}
    if not resource.get('endpoint'):
        return {**record, 'status': 'unconfirmed', 'error': 'historical resource has no frozen Docker endpoint'}
    if not resource.get('container_id') and not resource.get('container_name'):
        return {**record, 'status': 'absent' if resource.get('state') == 'not-started' else 'launch-unconfirmed'}
    try:
        value = container_owned(resource)
        if value is None:
            return {**record, 'status': 'absent'}
        resource['container_id'] = value['Id']
        write_json(path, resource)
        record.update(container_id=value['Id'], status='owned', running=value['State']['Running'])
        if cleanup:
            with path.with_suffix('.container.stdout.log').open('wb') as out, path.with_suffix('.container.stderr.log').open('wb') as err:
                logged = execute(resource['endpoint'], ['logs', value['Id']], stdout=out, stderr=err, timeout=10)
                record['logs_exit_code'] = logged.returncode
            docker(resource['endpoint'], ['rm', '--force', value['Id']], capture_output=True, timeout=10)
            record['status'] = 'removed'
        return record
    except Exception as error:
        return {**record, 'status': 'unconfirmed', 'error': error_text(error)}


class Workspace:
    def __init__(self, path):
        self.path = Path(path)
        self.value = read_json(self.path)
        self.endpoint = self.value['endpoint']

    @classmethod
    def create(cls, workspace, endpoint, image_id, *, owner_token=None):
        path = workspace / 'docker-workspace.json'
        if path.exists():
            raise ValueError('this workspace already has a transport receipt; reconcile or clean it instead of rerunning')
        api = endpoint.get('environment', {}).get('DOCKER_API_VERSION') or docker(
            endpoint, ['version', '--format', '{{.Server.APIVersion}}'], text=True, capture_output=True).stdout.strip()
        if tuple(int(part) for part in api.split('.')) < (1, 45):
            raise ValueError(f'remote workspace volume-subpath requires Docker API 1.45 or newer, got {api}')
        labels = {LABEL_PREFIX + 'experiment': os.environ.get('EXPERIMENT_ID', 'standalone'),
                  LABEL_PREFIX + 'run': os.environ.get('EXPERIMENT_RUN_ID', workspace.parent.name),
                  LABEL_PREFIX + 'attempt': os.environ.get('EXPERIMENT_ATTEMPT', '1'),
                  LABEL_PREFIX + 'owner': owner_token or secrets.token_hex(16)}
        name = 'factory26-attempt-' + labels[LABEL_PREFIX + 'owner']
        with path.open('x') as stream:
            json.dump({'schema_version': 1, 'endpoint': endpoint, 'volume': name, 'labels': labels,
                       'image_id': image_id, 'helper_name': name + '-copy', 'stages': {},
                       'state': 'allocating', 'recovery': 'unconfirmed'}, stream)
            stream.write('\n')
        current = cls(path)
        options = [item for key, value in labels.items() for item in ('--label', key + '=' + value)]
        try:
            if volume_owned(current.value) is not None:
                raise ValueError('refusing to reuse an existing workspace volume')
            docker(endpoint, ['volume', 'create', *options, name], capture_output=True)
            volume = volume_owned(current.value)
            current.value.update(mountpoint=volume['Mountpoint'], state='allocated')
            current.save()
            result = docker(endpoint, ['create', '--name', current.value['helper_name'], *options,
                            '--user', '0', '--mount', f'type=volume,source={name},target=/transfer',
                            '--entrypoint', 'python3', image_id, '-u', '-c', 'import time; time.sleep(2147483647)'],
                            text=True, capture_output=True)
            current.value['helper_id'] = result.stdout.strip()
            current.save()
            docker(endpoint, ['start', current.value['helper_id']], capture_output=True)
            current.value.update(state='ready', recovery='pending')
            current.save()
            return current
        except BaseException as error:
            current.value.update(state='unconfirmed', error=error_text(error))
            current.save()
            raise

    def save(self):
        write_json(self.path, self.value)

    def helper(self):
        if volume_owned(self.value) is None:
            raise ValueError('workspace volume is absent before output recovery')
        value = inspect(self.endpoint, 'container', self.value.get('helper_id') or self.value['helper_name'])
        if value is None:
            raise ValueError('workspace copy helper is absent')
        if self.value.get('helper_id') and value['Id'] != self.value['helper_id']:
            raise ValueError('copy helper ID mismatch')
        if value.get('Image') != self.value['image_id'] or not labels_match(value, self.value['labels']) or not any(
            mount.get('Type') == 'volume' and mount.get('Name') == self.value['volume'] and
            mount.get('Destination') == '/transfer' for mount in value.get('Mounts', [])):
            raise ValueError('copy helper ownership mismatch')
        self.value['helper_id'] = value['Id']
        self.save()
        if not value['State']['Running']:
            docker(self.endpoint, ['start', value['Id']], capture_output=True)
        return value['Id']

    def send(self, local, resource_path, user):
        stage = local.name
        if not stage or stage in ('.', '..') or '/' in stage or stage in self.value['stages']:
            raise ValueError('invalid or reused workspace stage')
        manifest = inventory(local)
        write_json(resource_path.with_suffix('.input-manifest.json'), manifest)
        self.value['stages'][stage] = {'workspace': str(local), 'resource': str(resource_path),
                                      'input_sha256': manifest['sha256'], 'recovery': 'pending'}
        self.save()
        helper = self.helper()
        docker(self.endpoint, ['exec', helper, 'mkdir', '-p', '/transfer/' + stage], capture_output=True)
        docker(self.endpoint, ['cp', str(local) + '/.', helper + ':/transfer/' + stage], capture_output=True, timeout=600)
        # Files copied into a container belong to root; the official Runner uses the controller's UID/GID.
        docker(self.endpoint, ['exec', helper, 'chown', '-R', user, '/transfer/' + stage], capture_output=True)
        observed = json.loads(docker(self.endpoint, ['exec', helper, 'python3', '-c', REMOTE_INVENTORY,
                                                    '/transfer/' + stage], text=True, capture_output=True, timeout=600).stdout)
        if observed != manifest:
            raise ValueError('uploaded workspace inventory/hash differs from frozen input')
        return stage

    def recover(self, stage):
        entry = self.value['stages'][stage]
        resource = read_json(Path(entry['resource']))
        try:
            value = container_owned(resource)
            if value is not None and value['State']['Running']:
                raise ValueError('output recovery requires a stopped execution container')
            if resource.get('state') == 'not-started':
                expected = read_json(Path(entry['resource']).with_suffix('.input-manifest.json'))
                if inventory(Path(entry['workspace'])) != expected:
                    raise ValueError('unexecuted local input no longer matches the frozen input manifest')
                write_json(Path(entry['resource']).with_suffix('.output-manifest.json'), expected)
                entry.update(recovery='verified', output_sha256=expected['sha256'], source='unexecuted-local-input')
                self.value['recovery'] = 'verified' if all(item['recovery'] == 'verified' for item in self.value['stages'].values()) else 'pending'
                self.save()
                return {'status': 'verified', 'stage': stage, 'sha256': expected['sha256'], 'source': entry['source']}
            helper = self.helper()
            remote = '/transfer/' + stage
            expected = json.loads(docker(self.endpoint, ['exec', helper, 'python3', '-c', REMOTE_INVENTORY, remote],
                                         text=True, capture_output=True, timeout=600).stdout)
            write_json(Path(entry['resource']).with_suffix('.output-manifest.json'), expected)
            local = Path(entry['workspace'])
            metadata = {}
            for name in ('local-run.json', 'local-result.json'):
                saved = Path(entry['resource']).with_suffix('.' + name)
                if (local / name).is_file():
                    shutil.copy2(local / name, saved)
                if saved.is_file():
                    metadata[name] = saved
            with tempfile.TemporaryDirectory(prefix='.' + stage + '-recovery-', dir=local.parent) as temporary:
                scratch = Path(temporary)
                archive = scratch / 'workspace.tar'
                with archive.open('wb') as stream:
                    docker(self.endpoint, ['cp', helper + ':' + remote + '/.', '-'], stdout=stream,
                           stderr=subprocess.PIPE, timeout=600)
                incoming = scratch / 'workspace'
                incoming.mkdir()
                with tarfile.open(archive) as stream:
                    stream.extractall(incoming, filter='data')
                actual = inventory(incoming)
                if actual != expected:
                    raise ValueError('downloaded workspace inventory/hash differs from remote output')
                # Official Runner writes this locally after docker run, outside the execution copy.
                for name, saved in metadata.items():
                    shutil.copy2(saved, incoming / name)
                previous = scratch / 'previous'
                local.replace(previous)
                try:
                    incoming.replace(local)
                except BaseException:
                    previous.replace(local)
                    raise
            entry.update(recovery='verified', output_sha256=expected['sha256'])
            self.value['recovery'] = 'verified' if all(item['recovery'] == 'verified' for item in self.value['stages'].values()) else 'pending'
            self.save()
            return {'status': 'verified', 'stage': stage, 'sha256': expected['sha256']}
        except BaseException as error:
            entry.update(recovery='failed', error=error_text(error))
            self.value.update(recovery='failed', state='retained')
            self.save()
            raise

    def confirm_local(self, entry):
        expected = read_json(Path(entry['resource']).with_suffix('.output-manifest.json'))
        if expected['sha256'] != entry['output_sha256']:
            raise ValueError('saved output manifest identity differs from recovery receipt')
        actual = {row['path']: row for row in inventory(Path(entry['workspace']))['entries']}
        if any(actual.get(row['path']) != row for row in expected['entries']):
            raise ValueError('verified local output is missing or changed; remote volume retained')

    def finish(self, *, cleanup=False):
        try:
            volume = volume_owned(self.value)
            if volume is None:
                if self.value.get('recovery') != 'verified':
                    raise ValueError('volume absent without verified local output recovery')
                self.value['state'] = 'removed'
                self.save()
                return {'status': 'absent', 'recovery': self.value['recovery']}
            if not cleanup:
                return {'status': 'owned', 'volume': self.value['volume'], 'recovery': self.value['recovery']}
            for stage, entry in self.value['stages'].items():
                observed = observe(Path(entry['resource']), cleanup=True)
                if observed['status'] not in {'absent', 'removed'}:
                    raise ValueError(json.dumps(observed))
                if entry['recovery'] != 'verified':
                    self.recover(stage)
                self.confirm_local(entry)
            if not self.value['stages']:
                # Allocation failed before any input was transferred; there is no execution output to lose.
                self.value['recovery'] = 'verified'
                self.save()
            if self.value['recovery'] != 'verified':
                raise ValueError('workspace outputs have not been verified locally')
            helper = inspect(self.endpoint, 'container', self.value.get('helper_id') or self.value['helper_name'])
            if helper is not None:
                identifier = self.helper()
                docker(self.endpoint, ['rm', '--force', identifier], capture_output=True, timeout=10)
            volume_owned(self.value)
            docker(self.endpoint, ['volume', 'rm', self.value['volume']], capture_output=True, timeout=10)
            self.value['state'] = 'removed'
            self.save()
            return {'status': 'removed', 'volume': self.value['volume'], 'recovery': 'verified'}
        except Exception as error:
            self.value.update(state='unconfirmed', error=error_text(error))
            self.save()
            return {'status': 'unconfirmed', 'volume': self.value['volume'], 'recovery': self.value['recovery'],
                    'error': error_text(error)}


def runner_main(resource_path, runner_path, argv):
    resource = read_json(resource_path)
    workspace = Path(resource['workspace'])
    transport = Workspace(Path(resource['transport'])) if resource.get('transport') else None
    endpoint = resource['endpoint']
    spec = importlib.util.spec_from_file_location('factory26_official_runner', runner_path)
    upstream = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = upstream
    spec.loader.exec_module(upstream)
    original = upstream.run_container
    child = None
    entered = False
    launching = False

    def interrupt(_number, _frame):
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, interrupt)

    def run_docker(command, **kwargs):
        nonlocal child, launching
        if command[:2] != ['docker', 'run'] or command.count('--mount') != 1 or kwargs != {'check': False}:
            raise ValueError('unsupported official Runner Docker command')
        index = command.index('--mount') + 1
        if command[index] != f'type=bind,source={workspace},target=/workspace':
            raise ValueError('official Runner mount differs from registered workspace')
        name = command[command.index('--name') + 1]
        resource.update(container_name=name, state='sending')
        write_json(resource_path, resource)
        command = command[1:]
        command.remove('--rm')
        cidfile = resource_path.with_suffix('.cid')
        options = ['--cidfile', str(cidfile)]
        if transport:
            user = command[command.index('--user') + 1] if '--user' in command else '0:0'
            stage = transport.send(workspace, resource_path, user)
            resource.update(volume=transport.value['volume'], stage=stage)
            write_json(resource_path, resource)
            command[command.index('--mount') + 1] = f"type=volume,source={resource['volume']},target=/workspace,volume-subpath={stage}"
        options += [item for key, value in resource.get('labels', {}).items() for item in ('--label', key + '=' + value)]
        confirm(endpoint)
        resource['state'] = 'launching'
        write_json(resource_path, resource)
        launching = True
        child = subprocess.Popen(endpoint['argv'] + [command[0], *options, *command[1:]], env=environment(endpoint))
        code = child.wait()
        if cidfile.is_file():
            resource['container_id'] = cidfile.read_text().strip()
            write_json(resource_path, resource)
        value = container_owned(resource)
        if value is None or value['State']['Running']:
            raise ValueError('Docker CLI exited without a confirmed stopped execution container')
        resource.update(container_id=value['Id'], state='exited', container_exit_code=value['State']['ExitCode'])
        write_json(resource_path, resource)
        return subprocess.CompletedProcess(command, code)

    def run_container(args, local):
        nonlocal entered
        if local != workspace:
            raise ValueError('official Runner workspace differs from registered workspace')
        entered = True
        try:
            code = original(args, local)
            if transport:
                transport.recover(local.name)
            return code
        finally:
            # A repeated TERM must not interrupt stop and evidence recovery. KILL remains the controller's deadline.
            signal.signal(signal.SIGTERM, signal.SIG_IGN)
            signal.signal(signal.SIGINT, signal.SIG_IGN)
            if not launching:
                resource['state'] = 'not-started'
                write_json(resource_path, resource)
            if child is not None and child.poll() is None:
                child.terminate()
                try:
                    child.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.wait()
            observation = observe(resource_path, cleanup=True)
            write_json(resource_path.with_suffix('.cleanup.json'), observation)
            if transport and local.name in transport.value['stages'] and transport.value['stages'][local.name]['recovery'] != 'verified':
                try:
                    transport.recover(local.name)
                except Exception as error:
                    print('workspace recovery failed: ' + error_text(error), file=sys.stderr)

    upstream.subprocess = SimpleNamespace(run=run_docker)
    upstream.run_container = run_container
    sys.argv = [str(runner_path), *argv]
    try:
        return upstream.main()
    finally:
        if not entered and transport:
            resource['state'] = 'not-started'
            write_json(resource_path, resource)
            transport.value.update(state='retained', error='Runner did not enter container execution')
            transport.save()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--resource', type=Path, required=True)
    parser.add_argument('--runner', type=Path, required=True)
    parser.add_argument('arguments', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    try:
        sys.exit(runner_main(args.resource, args.runner,
                            args.arguments[1:] if args.arguments[:1] == ['--'] else args.arguments))
    except KeyboardInterrupt:
        sys.exit(130)
