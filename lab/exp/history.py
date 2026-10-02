"""Bounded read-only access to legacy producer facts."""
from pathlib import Path
import time
from .core import error, public, read, record


def inspect(path):
    path = Path(path).resolve(strict=True)
    names = ('manifest.json', 'spec.json', 'inputs.json', 'prepare-receipt.json', 'receipt.json',
             'run.json', 'state.json', 'worker.json', 'handoff.json', 'completion.json')
    paths = [path] if path.is_file() else [path / name for name in names if (path / name).is_file()]
    facts = []
    for source in paths:
        try:
            value = read(source)
            facts.append({'source': str(source), 'value': public(value)})
        except (OSError, ValueError) as exc:
            facts.append({'source': str(source), 'error': error(exc)})
    return record('history', source=str(path), read_at=time.time(), facts=facts,
                  guarantees='original producer facts only; not new execution or authorization')


# Frozen legacy scope selection stays read-only after the writer cutoff.
def experiment_runs(inputs):
    """Read actual runs belonging to the frozen experiment and jobs."""
    experiment = Path(inputs['experiment'])
    manifest = read(experiment / 'manifest.json')
    root = (experiment / manifest['runs_root']).resolve()
    runs = []
    for path in sorted(root.iterdir()):
        if not (path / 'run.json').is_file():
            continue
        row = read(path / 'run.json')
        if row.get('experiment_id') != inputs['experiment_id'] or row.get('job_id') not in inputs['job_ids']:
            continue
        if row.get('run_id') != path.name:
            raise ValueError(f'run directory identity differs from record: {path}')
        runs.append(path)
    return runs


def selected_runs(inputs):
    """Later external retry attempts do not enlarge this operation's authorization."""
    selected = []
    first = {}
    for path in experiment_runs(inputs):
        row = read(path / 'run.json')
        if path.name in inputs['run_ids']:
            selected.append(path)
        elif (row['job_id'] in inputs['first_attempt_jobs'] and row.get('attempt') == 1
              and not row.get('retry_of')):
            if row['job_id'] in first:
                raise ValueError(f'multiple first attempts for frozen job: {row["job_id"]}')
            first[row['job_id']] = path
            selected.append(path)
    missing = set(inputs['run_ids']) - {path.name for path in selected}
    if missing:
        raise ValueError(f'frozen run records disappeared: {sorted(missing)}')
    return selected
