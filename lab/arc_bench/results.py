"""Interpret saved ARC Runner results and official workspace evidence."""

import json
from pathlib import Path
import re

ANSI = re.compile(r"\x1b(?:\[[0-?]*[ -/]*[@-~]|\][^\x07]*(?:\x07|\x1b\\))")

def _read(path, warnings):
    try:
        value = json.loads(path.read_text())
        if not isinstance(value, dict):
            raise ValueError("顶层必须是 JSON 对象")
        return value
    except (OSError, ValueError) as exc:
        warnings.append(f"{path}: {exc}")
        return {}


def _error(value):
    clean = ANSI.sub("", str(value or ""))
    clean = re.sub(r"[\x00-\x08\x0b-\x1f\x7f]", "", clean)
    return {"text": clean, "truncated": False}


def experiment_summary(run, metadata):
    """Join saved process boundaries; a Runner exit code is never a score.

    Only known evidence locations are traversed, not frozen dependencies or app trees.
    Deployment status comes from the official Runner's application events.
    """
    warnings, evidence = [], {}

    def link(path):
        if path.exists():
            evidence[str(path.relative_to(run))] = str(path)
        return path

    def read(path):
        return _read(link(path), warnings) if path.is_file() else {}

    link(run/'run.json')
    workspace = run/'workspace'
    result = read(run/metadata['result_path']) or metadata.get('result') or {}
    evaluation = result.get('evaluation') or {}
    generation = dict(result.get('generation') or {})
    directories = [workspace/name for name in ('official-generation', 'official-evaluation', 'official')
                   if (workspace/name).is_dir()]
    generation_dir = next((p for p in directories if p.name != 'official-evaluation'), None)
    evaluation_dir = next((p for p in directories if p.name == 'official-evaluation'), None)
    if evaluation_dir is None and (workspace/'official').is_dir():
        evaluation_dir = workspace/'official'
    if not evaluation and evaluation_dir:
        evaluation = read(evaluation_dir/'local-result.json')
    if not generation and generation_dir:
        generation = read(generation_dir/'template/.arc/adapter-agent-result.json')
        if not generation:
            generation = read(generation_dir/'template/.arc/raw/entry-result.json')
    applications = []
    for folder in directories:
        for pattern in ('*.json', '*.log', 'template/.arc/*.json', 'template/.arc/*.jsonl',
                        'template/.arc/*.log', 'template/.arc/traceability/*.json',
                        'template/.arc/runtime-reporting/*.jsonl'):
            for path in folder.glob(pattern):
                link(path)
        app = folder/'template'
        if (app/'frontend').is_dir() or (app/'backend').is_dir():
            applications.append(str(app))
            link(app)
    for pattern in ('*.log', 'workspace/*.log'):
        for path in run.glob(pattern):
            if path.is_file():
                link(path)
    link(run/'artifacts')
    link(run/'telemetry.sqlite')
    deployment = {'status': 'unknown', 'error': None, 'evidence': None}
    events_dir = evaluation_dir or generation_dir
    events = events_dir/'template/.arc/runner-events.jsonl' if events_dir else None
    # This upstream stream combines install, deployment and scoring under run_tests.
    # Reaching Playwright alone must not turn a later test failure into a deployment failure.
    if events and events.is_file():
        deployment['evidence'] = str(events)
        for number, line in enumerate(events.read_text().splitlines(), 1):
            try:
                event = json.loads(line)
                message = str(event.get('message') or '')
                if message.startswith('Template application is reachable'):
                    deployment.update(status='completed', message=message, line=number)
                elif event.get('step_key') == 'run_tests' and deployment['status'] != 'completed':
                    if event.get('status') in ('error', 'failed'):
                        deployment.update(status='failed', error=message, line=number)
                    elif deployment['status'] == 'unknown':
                        deployment['status'] = 'running'
            except (ValueError, AttributeError) as exc:
                warnings.append(f'{events}:{number}: {exc}')
    if deployment['status'] == 'running' and metadata.get('phase') in ('completed', 'failed', 'interrupted', 'finished', 'cancelled', 'lost'):
        deployment['status'] = 'incomplete'
    passed, failed, total = (evaluation.get(k) for k in ('passed', 'failed', 'total'))
    complete = (evaluation.get('evaluation_status') == 'completed'
                and all(type(v) is int and v >= 0 for v in (passed, failed, total))
                and total > 0 and passed + failed == total)
    if complete and result.get('status') != 'completed':
        warnings.append('Runner 有评分计数，但适配器未确认完整结果或应用身份；不计为完整得分，原始计数见 evaluation.raw')
        complete = False
    score = {'passed': passed, 'failed': failed, 'total': total, 'pass_rate': passed/total} if complete else None
    report = evaluation_dir/'template/.arc/playwright-report.json' if evaluation_dir else None
    evaluation_record = {'id': evaluation_dir.name if evaluation_dir else None,
                         'path': str(evaluation_dir) if evaluation_dir else None,
                         'status': evaluation.get('evaluation_status') or 'unknown', 'phase': None,
                         'score': score, 'error': _error(evaluation['failure_reason']) if evaluation.get('failure_reason') else None,
                         'evidence': {'results.json': str(report) if report and report.is_file() else None},
                         'raw': evaluation}
    error = metadata.get('error') or result.get('error')
    return {'producer': 'local_experiment', 'id': metadata.get('run_id', run.name), 'path': str(run),
            'labels': metadata.get('labels', {}), 'source_application': metadata.get('source_application'),
            'variant': metadata.get('variant'), 'variant_inferred': False, 'backend': None,
            'task': metadata.get('task'), 'competition': metadata.get('competition'), 'model': None,
            'status': metadata.get('phase', 'unknown'), 'stage': result.get('stage') or metadata.get('phase'),
            'observed_at': metadata.get('finished_at') or metadata.get('started_at') or metadata.get('created_at'),
            'error': error, 'runner_exit_code': metadata.get('runner_exit_code'),
            'generation': dict(generation, status=generation.get('status') or 'unknown', phase='generation',
                               updated_at=metadata.get('finished_at'),
                               error=_error(generation['error']) if generation.get('error') else None),
            'deployment': deployment, 'evaluation': evaluation_record, 'remote': None,
            'evidence': evidence, 'factory_runs': [], 'native': [],
            'applications': applications, 'warnings': warnings}
