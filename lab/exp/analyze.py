"""Reproducible experiment summaries bound to saved evidence cutoffs."""
from pathlib import Path
import time

from .core import atomic, digest, new_id, public, read, record, require


def snapshot(experiment, output):
    experiment, output = Path(experiment).resolve(strict=True), Path(output).resolve()
    manifest = require(read(experiment / 'experiment.json'), 'experiment')
    if output.exists():
        raise FileExistsError('analysis snapshots are immutable; choose a new output')
    rows = []
    for path in sorted((experiment / 'attempts').glob('*')):
        if not (path / 'attempt.json').is_file():
            continue
        attempt = require(read(path / 'attempt.json'), 'attempt')
        files = {}
        for name in ('execution.json', 'remote-execution.json', 'observation.json', 'result.json', 'output-artifacts.json',
                     'telemetry/binding.json', 'telemetry/seal.json', 'telemetry-ingestion.json', 'export.json'):
            source = path / name
            if source.is_file():
                files[name] = {'sha256': digest(source), 'value': public(read(source))}
        telemetry = None
        if attempt['job']['backend']['kind'] != 'hosted':
            from .telemetry import snapshot as telemetry_snapshot
            telemetry = telemetry_snapshot(path)
        rows.append({'attempt_id': attempt['attempt_id'], 'job_id': attempt['job_id'],
                     'purpose': attempt['job']['purpose'], 'evidence': files,
                     'telemetry_cutoff': telemetry,
                     'model_usage': {'status': 'unknown', 'reason': 'raw batches are not model-call identities'}})
    value = record('analysis', analysis_id=new_id('analysis'), experiment_id=manifest['experiment_id'],
                   experiment_manifest_sha256=digest(experiment / 'experiment.json'),
                   analyzer={'name': 'exp-evidence-summary', 'version': 1, 'source_sha256': digest(__file__)},
                   captured_at=time.time(), attempts=rows)
    atomic(output, value)
    return value
