"""Freeze explicitly selected bench-owned context without changing official inputs."""
import hashlib
import json
from pathlib import Path


PACKAGED_ENTRYPOINT = '''"""Bind the separately frozen bench context before entering the Harness."""
import os
from pathlib import Path
import runpy

root = Path(__file__).resolve().parent
os.environ['TASK_CONTEXT_FILE'] = str(root / 'bench/task-context.md')
runpy.run_path(str(root / 'agent-main.py'), run_name='__main__')
'''


def freeze_task_context(config_path, task, extra_dir):
    config_path = Path(config_path).resolve(strict=True)
    config = json.loads(config_path.read_text())
    if task not in config['tasks']:
        raise ValueError(f'Task {task} is not selected by {config_path}')
    source = (config_path.parent / config['task_context']).resolve(strict=True)
    if not source.is_file():
        raise ValueError(f'Task context is not a readable file: {source}')
    content = source.read_bytes()
    extra_dir = Path(extra_dir)
    extra_dir.mkdir(parents=True, exist_ok=True)
    destination = extra_dir / 'task-context.md'
    if destination.exists():
        raise FileExistsError(f'Frozen task context already exists: {destination}')
    with destination.open('xb') as output:
        output.write(content)
    receipt = {'task': task, 'source_config': str(config_path), 'source': str(source),
               'source_config_sha256': hashlib.sha256(config_path.read_bytes()).hexdigest(),
               'sha256': hashlib.sha256(content).hexdigest(), 'bytes': len(content),
               'frozen_file': str(destination.resolve()),
               'owner': 'Factory26 additional bench context; not official requirements'}
    (extra_dir / 'task-context-source.json').write_text(json.dumps(receipt, indent=2) + '\n')
    return receipt


def bind_packaged_task_context(stage, config_path, task):
    """Keep the Harness entry unchanged behind a package-owned context binding."""
    stage = Path(stage)
    receipt = freeze_task_context(config_path, task, stage / 'bench')
    entry = stage / 'main.py'
    original = stage / 'agent-main.py'
    if original.exists():
        raise FileExistsError(f'Packaged Harness entry already exists: {original}')
    entry.rename(original)
    entry.write_text(PACKAGED_ENTRYPOINT)
    return receipt
