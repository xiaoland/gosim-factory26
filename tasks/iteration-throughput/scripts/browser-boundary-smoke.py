#!/usr/bin/env python3
"""Exercise isolated browser sessions without calling a model."""
import argparse
from functools import partial
from hashlib import sha256
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from threading import Thread


def command(prefix, wrapper, cwd, env, *args):
    result = subprocess.run(prefix + [str(wrapper), *args], cwd=cwd, env=env,
                            capture_output=True, text=True, timeout=45)
    if result.returncode:
        raise RuntimeError(f'{args[0]} failed ({result.returncode}): {result.stderr.strip()}')
    return result.stdout.strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True, help='Unpacked submission package')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--library-dir', type=Path,
                        help='Test newly collected runtime libraries before rebuilding the package')
    args = parser.parse_args()
    root = args.root.resolve()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    sys.path.insert(0, str(root / 'scripts'))
    import factory
    import native_profiles
    import submission

    work = Path(tempfile.mkdtemp(prefix='f26-browser-smoke-', dir='/tmp')).resolve()
    inputs = Path(tempfile.mkdtemp(prefix='f26-browser-input-', dir='/tmp')).resolve()
    app = work / 'application'
    app.mkdir()
    (inputs / 'index.html').write_text('''<!doctype html><title>browser boundary</title>
<label>Value<input id="value"></label>
<button onclick="const v=document.querySelector('#value').value;localStorage.setItem('probe',v);document.cookie='probe='+v">Save</button>''')
    server = ThreadingHTTPServer(('127.0.0.1', 0),
        partial(SimpleHTTPRequestHandler, directory=str(inputs)))
    Thread(target=server.serve_forever, daemon=True).start()
    passed = False
    try:
        manifest = submission.verify_package(root)
        config = submission.platform_config(root, manifest)
        _, env = factory.runtime_environment(work, config)
        if args.library_dir:
            env['LD_LIBRARY_PATH'] = str(args.library_dir.resolve())
        native_profiles.materialize(config['effective'], work, config['base_url'],
                                    'browser-boundary-smoke', config.get('visual_base_url'))
        wrapper = work / 'bin/agent-browser'
        env['PATH'] = str(wrapper.parent) + os.pathsep + env['PATH']
        prefix = []
        url = f'http://127.0.0.1:{server.server_port}/'
        observations = {}
        session_envs = {}
        for token in ('alpha', 'beta'):
            session_id = 'qualification-browser-' + token
            session_env = dict(env, PI_SESSION_ID=session_id)
            session_envs[token] = session_env
            command(prefix, wrapper, app, session_env, 'open', url)
            initial = json.loads(command(prefix, wrapper, app, session_env, 'eval',
                                         "localStorage.getItem('probe')"))
            command(prefix, wrapper, app, session_env, 'fill', '#value', token)
            command(prefix, wrapper, app, session_env, 'click', 'button')
            command(prefix, wrapper, app, session_env, 'reload')
            observations[token] = {'initial': initial, 'session_id': session_id}
        for token, session_env in session_envs.items():
            stored = json.loads(command(prefix, wrapper, app, session_env, 'eval',
                                        "localStorage.getItem('probe')"))
            cookie = json.loads(command(prefix, wrapper, app, session_env, 'eval',
                                        'document.cookie'))
            screenshot = app / f'{token}.png'
            command(prefix, wrapper, app, session_env, 'screenshot', str(screenshot))
            identity_files = [path for path in (work / 'browser').glob('*/identity.json')
                              if json.loads(path.read_text())['native_session_id']
                              == observations[token]['session_id']]
            assert len(identity_files) == 1, identity_files
            identity = json.loads(identity_files[0].read_text())
            assert identity == {'run_id': 'browser-boundary-smoke',
                                'native_session_id': observations[token]['session_id']}
            assert observations[token]['initial'] is None and stored == token \
                and cookie == f'probe={token}', (observations[token]['initial'], stored, cookie)
            shutil.copy2(screenshot, output / screenshot.name)
            observations[token].update(
                stored=stored, cookie=cookie, wrapper_identity=identity_files[0].parent.name,
                screenshot_sha256=sha256(screenshot.read_bytes()).hexdigest())
        assert observations['alpha']['wrapper_identity'] != observations['beta']['wrapper_identity']
        for session_env in session_envs.values():
            command(prefix, wrapper, app, session_env, 'close')
        record = {
            'status': 'passed',
            'package_manifest_sha256': sha256((root / 'package-manifest.json').read_bytes()).hexdigest(),
            'isolation': 'direct process launch',
            'environment': 'factory.runtime_environment(submission config)',
            'observations': observations,
        }
        (output / 'result.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
        passed = True
        print(output / 'result.json')
    except BaseException as error:
        for source in [*(work / 'b').glob('*'), *(app / '.brdiag').glob('*.log')]:
            if source.is_file():
                shutil.copy2(source, output / source.name)
        (output / 'failure.json').write_text(json.dumps({
            'status': 'failed', 'error': f'{type(error).__name__}: {error}',
            'workspace': str(work),
        }, indent=2) + '\n')
        raise
    finally:
        server.shutdown()
        server.server_close()
        if passed:
            factory.cleanup_workspace(work)
            shutil.rmtree(work)
            shutil.rmtree(inputs)


if __name__ == '__main__':
    main()
