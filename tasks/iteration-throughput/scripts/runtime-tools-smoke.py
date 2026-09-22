#!/usr/bin/env python3
"""Exercise the packaged ps/kill tools inside submission isolation."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--tools-root', type=Path,
                        help='Test collected tools before rebuilding the package')
    args = parser.parse_args()
    root = args.root.resolve()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    sys.path.insert(0, str(root / 'scripts'))
    import submission

    submission.verify_package(root)
    tools_root = (args.tools_root or root / 'runtime').resolve()
    work = Path(tempfile.mkdtemp(prefix='f26-tools-smoke-', dir='/tmp')).resolve()
    inputs = Path(tempfile.mkdtemp(prefix='f26-tools-input-', dir='/tmp')).resolve()
    try:
        env = submission.base_environment()
        env['PATH'] = str(tools_root / 'bin') + ':' + env['PATH']
        prefix = []
        probe = r'''import json, os, shutil, subprocess, sys
ps = shutil.which('ps'); kill = shutil.which('kill')
assert ps and kill
result = subprocess.run([ps, '-axo', 'pid=,ppid='], check=True, capture_output=True, text=True)
rows = [tuple(map(int, line.split())) for line in result.stdout.splitlines()]
assert any(pid == os.getpid() for pid, _ in rows)
child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(120)'], start_new_session=True)
try:
    assert os.getpgid(child.pid) == child.pid
    result = subprocess.run([kill, '-0', '--', '-'+str(child.pid)])
    assert result.returncode == 0
    subprocess.run([kill, '-TERM', '--', '-'+str(child.pid)], check=True)
    assert child.wait(timeout=5) == -15
finally:
    if child.poll() is None:
        child.kill()
print(json.dumps({'ps_listed_self': True, 'process_group_existed': True,
                  'process_group_stopped': True, 'ps': ps, 'kill': kill}))
'''
        result = subprocess.run(prefix + [sys.executable, '-c', probe], cwd=work,
                                env=env, capture_output=True, text=True, timeout=15)
        if result.returncode:
            raise RuntimeError(result.stderr or result.stdout)
        record = json.loads(result.stdout)
        record.update(status='passed',
                      ps_sha256=sha256((tools_root/'libexec/ps').read_bytes()).hexdigest(),
                      kill_sha256=sha256((tools_root/'libexec/kill').read_bytes()).hexdigest())
        (output/'result.json').write_text(json.dumps(record, indent=2) + '\n')
        print(output/'result.json')
    finally:
        shutil.rmtree(work)
        shutil.rmtree(inputs)


if __name__ == '__main__':
    main()
