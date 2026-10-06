"""Submission-side snapshot transport and OTLP setup for the DX variants."""
from contextlib import contextmanager
import json
import os
from pathlib import Path
import select
import shutil
import subprocess
import sys
import tarfile


def install_inputs(package, output):
    package, output = Path(package), Path(output)
    output.mkdir(parents=True, exist_ok=True)
    inputs = package / 'inputs'
    seed = inputs / 'seed-data'
    archive = inputs / 'seed-data.tar'
    if archive.is_file() and not seed.exists():
        seed.mkdir()
        with tarfile.open(archive) as source:
            # The builder creates this trusted archive from our own frozen data.
            # Native absolute symlinks retain stable /workspace/template targets.
            source.extractall(seed, filter='fully_trusted')
    workspace = seed / 'workspace'
    if workspace.is_dir():
        for item in workspace.iterdir():
            # ARC owns the current allowed input and private evaluation context.
            # Previous versions remain in the original snapshot archive.
            if item.name in {'requirements', '.arc'}:
                continue
            target = output / item.name
            if item.is_symlink():
                if target.is_symlink() or target.exists():
                    target.unlink()
                target.symlink_to(os.readlink(item))
            elif item.is_dir():
                shutil.copytree(item, target, dirs_exist_ok=True, symlinks=True)
            else:
                shutil.copy2(item, target)
    harness = seed / 'harness'
    if harness.is_dir():
        shutil.copytree(harness, output / '.factory26/data/harness',
                        dirs_exist_ok=True, symlinks=True)
    contract = output / '.factory26/lab-run.json'
    contract.parent.mkdir(parents=True, exist_ok=True)
    if (inputs / 'lab-run.json').is_file():
        shutil.copy2(inputs / 'lab-run.json', contract)
    return json.loads(contract.read_text())


@contextmanager
def services(package, output):
    """Use injected local OTLP, or a lightweight raw receiver on Hosted."""
    package, output = Path(package), Path(output)
    contract = install_inputs(package, output)
    evidence = (output / '.factory26/data/harness' / contract['native_scope_id'] /
                'producers' / contract['run_id'])
    evidence.mkdir(parents=True, exist_ok=True)
    process = None
    previous = {}
    error_log = None
    try:
        if contract.get('target_kind') == 'hosted':
            error_log = (evidence / 'collector.stderr.log').open('a')
            process = subprocess.Popen(
                [sys.executable, str(package / 'lab_otlp.py'), '--serve-run', str(evidence)],
                stdout=subprocess.PIPE, stderr=error_log, text=True)
            try:
                if not select.select([process.stdout], [], [], 15)[0]:
                    raise RuntimeError('Hosted OTLP receiver did not provide its startup handshake')
                line = process.stdout.readline()
                if not line:
                    raise RuntimeError(f'Hosted OTLP receiver exited before startup: {process.poll()}')
                binding = json.loads(line)
                values = {
                    'OTEL_EXPORTER_OTLP_ENDPOINT': binding['endpoint'],
                    'OTEL_EXPORTER_OTLP_PROTOCOL': 'http/protobuf',
                    'OTEL_EXPORTER_OTLP_HEADERS': 'x-experiment-token=' + binding['token'],
                    'OTEL_SDK_DISABLED': 'false',
                }
                for name, value in values.items():
                    previous[name] = os.environ.get(name)
                    os.environ[name] = value
            except Exception as error:
                # Evidence failure is visible, but does not gate generation.
                (evidence/'collector-start.json').write_text(json.dumps({
                    'status': 'failed', 'error': f'{type(error).__name__}: {error}'})+'\n')
        yield contract
    finally:
        if process is not None:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        if error_log is not None:
            error_log.close()
        for name, value in previous.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value
