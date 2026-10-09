"""Lifecycle connection to the Rust sampler; offline analysis stays in Python."""
import json
import os
from pathlib import Path
import select
import shutil
import subprocess


def monitor_binary(package=None):
    configured = os.environ.get('FACTORY_RESOURCE_MONITOR')
    if configured:
        candidates = [Path(configured)]
    else:
        root = Path(package) if package else Path(__file__).resolve().parent
        candidates = [root/'runtime/bin/factory26-resource-monitor',
                      root/'native/bin/factory26-resource-monitor',
                      root.parent/'runtime/bin/factory26-resource-monitor']
        installed = shutil.which('factory26-resource-monitor')
        if installed:
            candidates.append(Path(installed))
        runtime = os.environ.get('FACTORY_NATIVE_RUNTIME_MODULE')
        if runtime:
            candidates.append(Path(runtime).parent/'bin/factory26-resource-monitor')
    for candidate in candidates:
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate.resolve()
    raise FileNotFoundError(f'Rust resource monitor is not installed: {candidates}; produce a current runtime')


class ResourceMonitor:
    def __init__(self, run, *, root_pid=None, package=None, sampler_only=False):
        self.run = Path(run)
        self.root_pid = root_pid or os.getpid()
        self.process = None
        self.log = None
        self.closed = False
        binary = monitor_binary(package)
        self.run.mkdir(parents=True, exist_ok=True)
        self.log = (self.run/'resource-monitor.stderr.log').open('a')
        args = [str(binary), '--run', str(self.run), '--root-pid', str(self.root_pid)]
        if sampler_only:
            args.append('--stdin-only')
        try:
            self.process = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                            stderr=self.log, text=True, start_new_session=True)
            if not select.select([self.process.stdout], [], [], 15)[0]:
                raise RuntimeError('Rust resource monitor startup timed out')
            line = self.process.stdout.readline()
            if not line:
                raise RuntimeError(f'Rust resource monitor exited before readiness: {self.process.poll()}')
            self.binding = json.loads(line)
            self.cgroup = Path(self.binding['cgroup_path']) if self.binding.get('cgroup_path') else None
            self.errors = {}
            if self.binding.get('status') != 'ready':
                raise RuntimeError(f'Rust resource monitor startup failed: {self.binding}')
        except BaseException:
            try:
                self._terminate()
            except Exception as cleanup_error:
                import sys
                print(f'Resource monitor startup cleanup failed: {cleanup_error}', file=sys.stderr)
            raise

    def send(self, value):
        if self.closed or self.process.poll() is not None:
            raise RuntimeError(f'Rust resource monitor is no longer active: {self.process.poll()}')
        self.process.stdin.write(json.dumps(value)+'\n')
        self.process.stdin.flush()

    def register_entry(self, process):
        # Registration is diagnostic only; the monitor never signals this entry.
        from agent_support import process_identity
        birth = process_identity(process.pid).get('starttime')
        if birth is None:
            raise RuntimeError(f'Cannot register entry birth identity: {process.pid}')
        self.send({'kind': 'register_entry', 'pid': process.pid, 'starttime': birth})

    def sample(self, kind='sample'):
        if kind == 'final':
            self.close()
        else:
            self.send({'kind': 'sample', 'sample_kind': kind})

    def _terminate(self):
        if self.process is not None:
            if self.process.poll() is None:
                self.process.terminate()
                try:
                    self.process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait(timeout=3)
            for stream in (self.process.stdin, self.process.stdout):
                if stream:
                    stream.close()
        if self.log is not None:
            self.log.close()

    def close(self):
        if self.closed:
            return
        failure = None
        try:
            if self.process.poll() is None:
                self.send({'kind': 'final'})
                self.process.stdin.close()
                self.process.wait(timeout=5)
            if self.process.returncode != 0:
                failure = {'phase': 'close', 'returncode': self.process.returncode,
                           'error': 'Rust resource monitor did not finish successfully',
                           'stderr': str(self.run / 'resource-monitor.stderr.log')}
        except Exception as error:
            failure = {'phase': 'close', 'error': f'{type(error).__name__}: {error}'}
        finally:
            self.closed = True
            try:
                self._terminate()
            except Exception as error:
                failure = {'phase': 'cleanup', 'previous': failure,
                           'error': f'{type(error).__name__}: {error}'}
        if failure is not None:
            # An evidence collector's failure must not bypass application eval.
            try:
                (self.run / 'resource-monitor-close-error.json').write_text(json.dumps(failure)+'\n')
            except OSError as error:
                import sys
                print(f'Resource monitor close diagnostic: {failure}; write failed: {error}', file=sys.stderr)


class ResourceEvidence(ResourceMonitor):
    """OTLP compatibility: the receiver schedules samples; Rust alone collects them."""
    def __init__(self, run, *, root_pid=None, package=None):
        super().__init__(run, root_pid=root_pid or os.getppid(), package=package, sampler_only=True)

    def sample(self, kind='sample'):
        if kind == 'final':
            return self.close()
        self.request_id = getattr(self, 'request_id', 0) + 1
        self.send({'kind': 'sample', 'sample_kind': kind, 'request_id': self.request_id})
        if not select.select([self.process.stdout], [], [], 15)[0]:
            raise RuntimeError('Rust resource sample did not return within 15 seconds')
        line = self.process.stdout.readline()
        result = json.loads(line) if line else {}
        if result.get('request_id') != self.request_id or result.get('status') != 'sampled':
            raise RuntimeError(f'Rust resource sample failed: {result}; exit={self.process.poll()}')
