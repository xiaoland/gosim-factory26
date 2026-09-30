"""Interpret saved ARC Runner results and official workspace evidence."""

import json
from contextlib import closing
from pathlib import Path
import re
import sqlite3

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


def _evidence_key(run, path):
    try:
        return str(path.relative_to(run))
    except ValueError:
        return str(path)


def _retained_generation(run, metadata, evidence, warnings):
    resource = run/'workspace/generation.resource.json'
    if not resource.is_file():
        return None
    evidence[str(resource.relative_to(run))] = str(resource)
    facts = _read(resource, warnings)
    labels = metadata.get('labels') or {}
    raw = facts.get('workspace')
    source_id = facts.get('source_run_id')
    if (not isinstance(raw, str) or not Path(raw).is_absolute() or
            not source_id or source_id != labels.get('source_run_id') or
            raw != labels.get('retained_generation')):
        warnings.append(f'{resource}: 保留工作区来源与当前 run 标签不一致')
        return None
    source = Path(raw)
    previous = source.parent.parent/'run.json'
    prior = _read(previous, warnings) if previous.is_file() else {}
    if prior.get('run_id') != source_id or not source.is_dir():
        warnings.append(f'{resource}: 来源 run 身份或工作区不可确认')
        return None
    return source


def _runtime_blocker(run, generation_dir, metadata, evidence, warnings):
    if metadata.get('phase') != 'running' or generation_dir is None:
        return None
    states = list((generation_dir/'template/.factory26').glob('*/braid-state/braid.sqlite3'))
    if len(states) != 1:
        return None
    path = states[0]
    started = metadata.get('started_at') or 0
    if generation_dir != run/'workspace/official-generation':
        writes = [candidate.stat().st_mtime for candidate in (path, Path(str(path) + '-wal')) if candidate.is_file()]
        if not writes or max(writes) < started:
            return None
    try:
        with closing(sqlite3.connect(f'{path.as_uri()}?mode=ro', uri=True, timeout=5)) as db:
            db.execute('PRAGMA query_only=ON')
            db.execute('BEGIN')
            lifecycle = db.execute('SELECT lifecycle FROM local_run').fetchone()
            active = db.execute("SELECT count(*) FROM turns WHERE lifecycle IN ('starting','running')").fetchone()[0]
            pending = db.execute("SELECT count(*) FROM events WHERE lifecycle='pending'").fetchone()[0]
            owners = db.execute("""SELECT w.node_id,w.kind,w.number,a.lifecycle,ai.lifecycle,ai.context_error,
                                  (SELECT cr.error FROM context_resets cr WHERE cr.agent_id=ai.agent_id
                                   ORDER BY cr.updated_at DESC LIMIT 1)
                                  FROM work_items w
                                  LEFT JOIN assignments a ON a.work_item_node_id=w.node_id
                                      AND a.lifecycle IN ('active','finalizing')
                                  LEFT JOIN agent_instances ai ON ai.assignment_id=a.assignment_id
                                  WHERE w.state='OPEN'""").fetchall()
    except (OSError, sqlite3.Error) as exc:
        warnings.append(f'Braid 实时状态 {path}: {exc}')
        return None
    if not lifecycle or lifecycle[0] != 'running' or not owners:
        return None
    evidence[_evidence_key(run, path)] = str(path)
    blocked = [owner for owner in owners if owner[3] is not None and owner[4] == 'blocked' and owner[5]]
    if not blocked:
        return {'status': 'clear', 'source': str(path), 'active_turns': active,
                'pending_events': pending, 'blocked_owners': []}
    root_blocked = any(owner[0] == 'issue:1' for owner in blocked)
    status = 'blocked' if not active and (root_blocked or len(blocked) == len(owners)) else 'partial'
    logs = []
    for candidate in path.parent.parent.glob('*braid.log'):
        if candidate.name.startswith('continuation-'):
            try:
                if int(candidate.name.split('-', 2)[1])/1e9 < started:
                    continue
            except ValueError:
                continue
        elif candidate.name not in ('recovery-braid.log', 'braid.log'):
            continue
        if candidate.stat().st_mtime >= started:
            logs.append(candidate)
    log = max(logs, key=lambda item: item.stat().st_mtime) if logs else None
    log_error = None
    if log:
        evidence[_evidence_key(run, log)] = str(log)
        try:
            with log.open('rb') as source:
                end = source.seek(0, 2)
                source.seek(max(0, end - 65536))
                for line in source.read().decode('utf-8', 'replace').splitlines():
                    clean = _error(line)['text']
                    if re.search(r'\bPi\b.*\b(?:failed|error)\b|\bERROR\b.*braid::provider::pi', clean):
                        log_error = clean
        except OSError as exc:
            warnings.append(f'Braid 日志 {log}: {exc}')
    return {'status': status, 'source': str(path), 'active_turns': active,
            'pending_events': pending,
            'blocked_owners': [{'work_item': f'{kind} #{number}', 'context_error': error,
                                'reset_error': reset_error}
                               for _, kind, number, _, _, error, reset_error in blocked],
            'provider_log': str(log) if log else None, 'provider_log_error': log_error}


def experiment_summary(run, metadata):
    """Join saved process boundaries; a Runner exit code is never a score.

    Only known evidence locations are traversed, not frozen dependencies or app trees.
    Deployment status comes from the official Runner's application events.
    """
    warnings, evidence = [], {}

    def link(path):
        if path.exists():
            evidence[_evidence_key(run, path)] = str(path)
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
    runtime_generation_dir = generation_dir or _retained_generation(run, metadata, evidence, warnings)
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
            'evidence': evidence, 'runtime_blocker': _runtime_blocker(run, runtime_generation_dir, metadata, evidence, warnings),
            'factory_runs': [], 'native': [],
            'applications': applications, 'warnings': warnings}
