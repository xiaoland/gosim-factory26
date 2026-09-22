"""Run the pinned official local simulation in an isolated, attributable workspace."""
import argparse
import fcntl
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

from factory import hashes, save

REVISION = 'cfbbc287ee1bbffcf1e936545e4803145693a8d8'


def execute(runner, package, requirements, tests, directory, task, *, image=None,
            env_file=None, prepare_only=False, shared_key=True, expected_tests=None):
    runner, package, requirements, tests, directory = map(
        lambda p: Path(p).resolve(), (runner, package, requirements, tests, directory))
    head = subprocess.check_output(['git', '-C', str(runner), 'rev-parse', 'HEAD'], text=True).strip()
    if head != REVISION or subprocess.check_output(['git', '-C', str(runner), 'status', '--porcelain'], text=True).strip():
        raise ValueError('official local runner must be clean at the frozen revision')
    if env_file and Path(env_file).stat().st_mode & 0o077:
        raise ValueError('model environment file must have mode 600')
    if not prepare_only and not image:
        raise ValueError('execution requires a qualified official image identity')
    identity = dict(venue='local-official-simulation', runner_revision=head, task=task,
                    competition='arc-bench-lite', package_sha256=hashlib.sha256(package.read_bytes()).hexdigest(),
                    requirements=hashes(requirements), tests=hashes(tests), image=image, expected_tests=expected_tests)
    if not prepare_only:
        info = json.loads(subprocess.check_output(['docker', 'image', 'inspect', image], text=True))[0]
        identity['image_id'] = info['Id']
        if info.get('Architecture') != 'amd64':
            raise ValueError('official image must target amd64')
    directory.mkdir(parents=True, exist_ok=True)
    with (directory/'controller.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        state_path = directory/'state.json'
        if state_path.exists():
            state = json.loads(state_path.read_text())
            if state['identity'] != identity:
                raise ValueError('local run inputs changed')
            if state['phase'] == 'collected' or prepare_only and state['phase'] == 'prepared':
                return state
            raise ValueError('existing workspace needs explicit diagnosis; generation is never automatically repeated')
        # Docker bind mounts refer to the daemon host. This command must run on
        # that host; a remote Docker context is sufficient for builds, not runs.
        state = dict(schema_version=1, identity=identity, phase='preparing' if prepare_only else 'running',
                     started_at=time.time(), cost_attribution='unattributed' if shared_key else 'isolated-key')
        save(state_path, state)
        command = [sys.executable, str(runner/'local_submit.py'), 'run', '--competition', 'arc-bench-lite',
                   '--task', task, '--agent', str(package), '--requirements-dir', str(requirements),
                   '--tests-dir', str(tests), '--workspace', str(directory/'workspace')]
        if prepare_only:
            command.append('--prepare-only')
        else:
            command += ['--image', image]
        if env_file:
            command += ['--env-file', str(Path(env_file).resolve())]
        try:
            with (directory/'runner.log').open('w') as log:
                result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
            state.update(exit_code=result.returncode, finished_at=time.time())
            result_path = directory/'workspace/local-result.json'
            if prepare_only:
                state['phase'] = 'prepared' if result.returncode == 0 else 'failed'
            elif result_path.is_file():
                state['result'] = json.loads(result_path.read_text())
                state['phase'] = 'collected' if state['result'].get('evaluation_status') == 'completed' and state['result'].get('total', 0) > 0 else 'failed'
                if expected_tests is not None and state['result'].get('total') != expected_tests:
                    state['phase'] = 'failed'
                    state['error'] = 'official evaluation omitted or added tests'
                if shared_key:
                    for field in ('token_cost', 'token_cost_usd', 'score', 'token_count'):
                        state['result'][field] = None
            else:
                state['phase'] = 'unknown'
                state['error'] = 'official runner produced no result'
            save(state_path, state)
            return state
        except BaseException:
            state.update(phase='unknown', error='controller interrupted; inspect container before any retry')
            save(state_path, state)
            raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('runner', 'package', 'requirements', 'tests', 'directory'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--task', choices=('keep', 'bookstack'), required=True)
    parser.add_argument('--image')
    parser.add_argument('--env-file', type=Path)
    parser.add_argument('--prepare-only', action='store_true')
    args = vars(parser.parse_args())
    result = execute(**args)
    print(json.dumps({'phase':result['phase'], 'evidence':str(args['directory'].resolve()), 'exit_code':result.get('exit_code')}, ensure_ascii=False))
    return 0 if result['phase'] in ('prepared', 'collected') else 1


if __name__ == '__main__':
    sys.exit(main())
