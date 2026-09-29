#!/usr/bin/env python3
"""Run a check with an owned temporary service, or wrap a self-managed check."""
import argparse
import json
import os
from pathlib import Path
import re
import signal
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request


def save(evidence, result):
    receipt = evidence / 'result.json'
    temporary = evidence / 'result.json.tmp'
    temporary.write_text(json.dumps(result, indent=2) + '\n')
    temporary.replace(receipt)


def candidate(cwd):
    def git(*arguments):
        try:
            completed = subprocess.run(['git', '-C', str(cwd), *arguments],
                capture_output=True, text=True, check=False)
        except OSError:
            return None
        return completed.stdout.strip() if completed.returncode == 0 else None

    head = git('rev-parse', '--verify', 'HEAD')
    if head is None:
        return None
    status = git('status', '--porcelain=v1', '--untracked-files=all')
    return {'git_head': head, 'dirty': bool(status) if status is not None else None,
            'untracked': any(line.startswith('??') for line in status.splitlines())
            if status is not None else None}


def terminate(process):
    if process is None:
        return []
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return []
    except OSError as exc:
        return [f'TERM process group {process.pid}: {exc}']
    return []


def stop(process, grace=5, already_terminated=False):
    if process is None:
        return []
    errors = [] if already_terminated else terminate(process)
    pgid = process.pid  # Popen(start_new_session=True): only this invocation owns it.
    try:
        process.wait(timeout=grace)
    except subprocess.TimeoutExpired:
        pass
    except OSError as exc:
        errors.append(f'wait for process {process.pid}: {exc}')
    deadline = time.monotonic() + grace
    while time.monotonic() < deadline:
        try:
            os.killpg(pgid, 0)
        except ProcessLookupError:
            break
        except OSError as exc:
            errors.append(f'check process group {pgid}: {exc}')
            break
        time.sleep(0.05)
    try:
        os.killpg(pgid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    except OSError as exc:
        errors.append(f'KILL process group {pgid}: {exc}')
    try:
        process.wait(timeout=5 if grace >= 1 else 0.1)
    except subprocess.TimeoutExpired:
        errors.append(f'process {process.pid} did not exit after KILL')
    except OSError as exc:
        errors.append(f'wait for process {process.pid}: {exc}')
    return errors


def stop_safely(process, grace=5, already_terminated=False):
    try:
        return stop(process, grace=grace, already_terminated=already_terminated)
    except Exception as exc:
        return [f'cleanup of process {process.pid}: {exc}']


def interrupted(signum, frame):
    raise KeyboardInterrupt(f'signal {signum}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cwd', type=Path, required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--start', help='foreground service command; bash with pipefail')
    mode.add_argument('--check-only', action='store_true', help='wrap a check that manages its own services')
    parser.add_argument('--port', type=int)
    parser.add_argument('--ready-path', default='/')
    parser.add_argument('--ready-timeout', type=float, default=90)
    parser.add_argument('--context', action='append', default=[], metavar='KEY=VALUE',
                        help='record an explicit candidate or runtime precondition')
    parser.add_argument('check', nargs=argparse.REMAINDER, help='-- command [arguments]')
    args = parser.parse_args()
    command = args.check[1:] if args.check[:1] == ['--'] else args.check
    if not command:
        parser.error('supply a check command after --')
    if args.check_only and args.port is not None:
        parser.error('--check-only does not accept --port')
    if args.start is not None and (args.port is None or not 1 <= args.port <= 65535):
        parser.error('--start requires --port in 1..65535')
    if args.ready_timeout <= 0:
        parser.error('ready-timeout must be positive')
    if not args.ready_path.startswith('/') or args.ready_path.startswith('//'):
        parser.error('ready-path must be a local path')
    context = {}
    for item in args.context:
        key, separator, value = item.partition('=')
        if not separator or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_.-]*', key) or key in context:
            parser.error('--context requires a unique KEY=VALUE')
        context[key] = value
    cwd = args.cwd.resolve(strict=True)
    if not cwd.is_dir():
        parser.error('cwd must be a directory')

    evidence = Path(tempfile.mkdtemp(prefix='service-check-'))
    base_url = f'http://127.0.0.1:{args.port}' if args.start is not None else None
    env = dict(os.environ)
    if base_url:
        env.update(PORT=str(args.port), BASE_URL=base_url)
    result = {'mode': 'service' if args.start is not None else 'check-only', 'cwd': str(cwd),
              'candidate': candidate(cwd), 'context': context, 'base_url': base_url,
              'service_command': args.start, 'check_command': command,
              'service_pid': None, 'check_pid': None, 'check_exit': None,
              'status': 'starting', 'cleanup_status': 'pending', 'started_at': time.time()}
    service = check = None
    code = 1
    phase = 'service' if args.start is not None else 'check'
    receipt_errors = []

    def record():
        try:
            save(evidence, result)
        except OSError as exc:
            receipt_errors.append(str(exc))
            print(f'evidence_error: {exc}', file=sys.stderr)

    signal.signal(signal.SIGTERM, interrupted)
    print(f'Evidence: {evidence}' + (f'\nBASE_URL={base_url}' if base_url else ''), flush=True)
    record()
    try:
        with (evidence/'service.log').open('wb') as service_log, (evidence/'check.log').open('wb') as check_log:
            if args.start is not None:
                # Fail before launching when the requested listener is already occupied.
                with socket.socket() as probe:
                    probe.bind(('0.0.0.0', args.port))
                service = subprocess.Popen(['bash', '-o', 'pipefail', '-c', args.start],
                    cwd=cwd, env=env, stdout=service_log, stderr=subprocess.STDOUT, start_new_session=True)
                result['service_pid'] = service.pid
                deadline = time.monotonic() + args.ready_timeout
                opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
                last_error = 'no response'
                while True:
                    if service.poll() is not None:
                        raise RuntimeError(f'service exited before readiness: {service.returncode}')
                    try:
                        with opener.open(base_url + args.ready_path, timeout=1) as response:
                            if response.geturl().split('/')[2] != base_url.split('/')[2]:
                                raise RuntimeError('readiness redirected to another origin')
                            result['ready_http_status'] = response.status
                        break
                    except (urllib.error.URLError, TimeoutError) as exc:
                        last_error = str(exc)
                    if time.monotonic() >= deadline:
                        raise RuntimeError(f'service readiness timed out: {last_error}')
                    time.sleep(0.2)
            phase = 'check'
            result['status'] = 'checking'
            record()
            check = subprocess.Popen(command, cwd=cwd, env=env, stdout=check_log,
                stderr=subprocess.STDOUT, start_new_session=True)
            result['check_pid'] = check.pid
            while check.poll() is None:
                if service is not None and service.poll() is not None:
                    raise RuntimeError(f'service exited during check: {service.returncode}')
                time.sleep(0.2)
            result['check_exit'] = check.returncode
            code = check.returncode if check.returncode >= 0 else 128 - check.returncode
            result['status'] = 'check_signaled' if check.returncode < 0 else (
                'passed' if code == 0 else 'check_failed')
            if check.returncode < 0:
                result['check_signal'] = -check.returncode
            record()  # Preserve the first real check exit before cleanup.
    except KeyboardInterrupt as exc:
        result.update(status='interrupted', error=str(exc))
        print(f'interrupted: {exc}', file=sys.stderr)
        code = 130
        record()  # A supervisor may escalate before full cleanup finishes.
    except (OSError, RuntimeError) as exc:
        result.update(status='service_error' if phase == 'service' or isinstance(exc, RuntimeError)
                      else 'check_start_error', error=str(exc))
        print(f'{result["status"]}: {exc}', file=sys.stderr)
    finally:
        # A second TERM/INT must not skip cleanup or its receipt.
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        fast = result['status'] == 'interrupted'
        cleanup_errors = []
        if fast:
            # PBB may escalate after 500 ms: signal both owned groups first.
            cleanup_errors.extend(terminate(check))
            cleanup_errors.extend(terminate(service))
        cleanup_errors.extend(stop_safely(check, grace=0.05 if fast else 5,
                                          already_terminated=fast) if check is not None else [])
        if check is not None and result['check_exit'] is None:
            result['check_exit'] = check.returncode
            result['check_completion'] = 'stopped_during_cleanup'
            if check.returncode is not None and check.returncode < 0:
                result['check_signal'] = -check.returncode
        record()
        cleanup_errors.extend(stop_safely(service, grace=0.05 if fast else 5,
                                          already_terminated=fast) if service is not None else [])
        result['cleanup_status'] = 'failed' if cleanup_errors else 'passed'
        if cleanup_errors:
            result['cleanup_errors'] = cleanup_errors
            if code == 0:
                code = 1
        result['finished_at'] = time.time()
        if receipt_errors:
            result['evidence_errors'] = receipt_errors.copy()
            if code == 0:
                code = 1
        record()
        print(f'{result["status"]}; logs and exit receipt: {evidence}', flush=True)
    return code


if __name__ == '__main__':
    sys.exit(main())
