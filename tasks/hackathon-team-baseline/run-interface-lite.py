"""WSL: build the approved interface revision and run the two Lite tasks."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tarfile

root = Path(sys.argv[1]).resolve()
source = root / 'build-input'
state = {'phase': 'restoring'}

def step(name, command):
    state['phase'] = name
    (root / 'execution.json').write_text(json.dumps(state, indent=2) + '\n')
    subprocess.run(command, cwd=source, check=True)

if '--from-running' not in sys.argv[2:]:
    with tarfile.open(root / 'build-input.tar.gz') as archive:
        archive.extractall(root, filter='data')
(root / 'docker-config').mkdir(exist_ok=True)
(root / 'docker-config/config.json').write_text('{"auths":{}}\n')
os.environ['DOCKER_CONFIG'] = str(root / 'docker-config')
for name in ('OPENAI_API_KEY', 'OPENAI_BASE_URL', 'FACTORY26_API_KEY'):
    os.environ.pop(name, None)
gateway = None
try:
    if not {'--from-packaging', '--from-running'}.intersection(sys.argv[2:]):
        step('restoring', [sys.executable, 'scripts/sources.py', 'restore',
                          str(source / 'braid-handoff'), str(source / 'sources/braid')])
        step('building', [sys.executable, 'scripts/runtime.py', 'linux', '--backend', 'pi',
                         '--output', str(root / 'runtime-pi-braid'),
                         '--braid-source', str(source / 'sources/braid')])
    if '--from-running' not in sys.argv[2:]:
        step('packaging', [sys.executable, 'scripts/package_agent.py', '--variant', 'pi-team-mixed',
                          '--runtime', str(root / 'runtime-pi-braid'),
                          '--output', str(root / 'pi-team-mixed.zip')])
    with (root / 'gateway-launch.log').open('a') as log:
        gateway = subprocess.Popen([
            '/home/yyh/.local/bin/python3.12', 'scripts/hackathon_gateway.py',
            '--runtime', '/home/yyh/Development/factory26-official-local/hackathon-runtime-codex',
            '--python', '/home/yyh/.local/bin/python3.12', '--secrets', str(root / 'models.env'),
            '--state', str(root / 'gateway'), '--port', '4014', '--preserve-parameters',
        ], cwd=source, stdout=log, stderr=log, start_new_session=True)
    (root / 'gateway.pid').write_text(str(gateway.pid))
    # The gateway's native startup produces this file before serving requests.
    gateway.wait(timeout=1) if gateway.poll() is not None else None
    import time
    time.sleep(5)
    if gateway.poll() is not None:
        raise RuntimeError('Gateway exited; see gateway-launch.log and gateway/gateway.log')
    values = dict(line.split('=', 1) for line in (root / 'gateway/gateway.env').read_text().splitlines())
    envfile = root / 'self-funded.env'
    envfile.write_text('FACTORY26_BASE_URL=' + values['GATEWAY_URL'] + '\nFACTORY26_API_KEY=' + values['GATEWAY_TOKEN'] + '\n')
    envfile.chmod(0o600)
    step('matrix', [sys.executable, '-m', 'lab.arc_bench.arc_matrix',
                   '--variant', 'pi-team-mixed=' + str(root / 'pi-team-mixed.zip'),
                   '--case', 'arc-bench-lite/keep', '--case', 'arc-bench-lite/bookstack',
                   '--inputs-root', '/home/yyh/Development/factory26-official-local/platform-inputs',
                   '--runner', '/home/yyh/Development/factory26-official-local/raw-baseline-20260923-wsl/runner',
                   '--image', 'arcbench-local-submit:latest', '--env-file', str(envfile),
                   '--workers', '2', '--container-otlp-host', '172.17.0.1',
                   '--separate-evaluation', '--output', str(root / 'lite-matrix.json')])
    step('running', [sys.executable, '-m', 'lab.run', 'run', str(root / 'lite-matrix.json'),
                    '--runs-root', str(root / 'lite-runs'), '--listen-host', '0.0.0.0'])
    state['phase'] = 'completed'
except BaseException as error:
    state.update(phase='failed', failed_phase=state['phase'], error=str(error))
    raise
finally:
    (root / 'execution.json').write_text(json.dumps(state, indent=2) + '\n')
    if gateway is not None:
        try:
            os.killpg(gateway.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
