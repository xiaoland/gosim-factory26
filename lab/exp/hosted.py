"""Single-attempt ARC platform adapter; durable uncertain writes are query-only."""
from pathlib import Path, PurePosixPath
from datetime import datetime, timezone
import time
import hashlib
import subprocess
import sys
import json
import os
from zipfile import ZipFile, ZIP_DEFLATED
from urllib.parse import urlencode, urlsplit

from .core import Blocked, atomic, canonical, digest, error, identifier, locked, read, record, require, process_identity, process_state
from lab.arc_bench.playground import Client, CONFIG, redact, run_path, private_storage
from lab.arc_bench.traceability import collect_hosted
from lab.arc_bench.arc_artifacts import package_metadata

TERMINAL = {'PASSED', 'FAILED', 'CANCELLED'}


def capabilities(target=None):
    return {'backend': 'hosted', 'dispatch': True, 'observe': True, 'stop': True,
            'pause': False, 'resume': False, 'checkpoint': False,
            'telemetry': 'platform-export-only', 'seal': 'partial-platform-evidence', 'export': 'selected-sealed-assets'}


def _context(directory):
    directory = Path(directory).resolve()
    attempt = require(read(directory / 'attempt.json'), 'attempt')
    job = attempt['job']
    backend = job['backend']
    if backend['kind'] != 'hosted':
        raise ValueError('hosted backend required')
    for key in ('competition_id', 'variant', 'task'):
        identifier(backend[key])
    mode = backend['credential_mode']
    if mode not in {'self_funded', 'official_evaluation'}:
        raise ValueError('explicit credential_mode required')
    if mode == 'official_evaluation' and backend.get('allow_competition_credit') is not True:
        raise Blocked('official evaluation requires frozen competition-credit authorization')
    config = backend['model_config']
    if any(not config.get(key) for key in ('model', 'visual_model', 'base_url', 'provider')):
        raise ValueError('model_config must freeze model, visual_model, base_url and provider')
    url = urlsplit(config['base_url'])
    if url.scheme != 'https' or not url.hostname or url.username or url.password or url.query or url.fragment:
        raise ValueError('model endpoint must be HTTPS without credentials')
    deployment = read(directory / 'deployment.json') if (directory / 'deployment.json').exists() else {}
    client = Client(deployment['cookie_file']) if deployment.get('cookie_file') else None
    return directory, attempt, backend, deployment, client


def _safe(value, secret=None):
    value = redact(value)
    if isinstance(value, dict):
        return {key: _safe(item, secret) for key, item in value.items()}
    if isinstance(value, list):
        return [_safe(item, secret) for item in value]
    return value.replace(secret, '[redacted]') if secret and isinstance(value, str) else value


def export_application(workspace_zip, destination, provenance):
    """Export one published application manifest from a hosted workspace ZIP.

    This is deliberately independent of platform scores and tests.  Only the
    application artifact's own v2 manifest and inventory may enter the seed.
    """
    workspace_zip = Path(workspace_zip).resolve(strict=True)
    destination = Path(destination).resolve()
    with ZipFile(workspace_zip) as archive:
        candidates = []
        for name in archive.namelist():
            if name.endswith('/application-manifest.json'):
                root = name[:-len('/application-manifest.json')]
                if root.endswith('/application-artifact') or root == 'application-artifact':
                    candidates.append((root, name))
        if len(candidates) != 1:
            raise ValueError(f'workspace ZIP 中没有唯一 application-artifact manifest：{len(candidates)}')
        root, manifest_name = candidates[0]
        manifest_bytes = archive.read(manifest_name)
        manifest = json.loads(manifest_bytes)
        if (manifest.get('kind') != 'factory26.harness.application' or
                manifest.get('schema_version') != 2 or
                manifest.get('status') != 'published' or
                manifest.get('delivery_kind') not in {'final', 'stage'}):
            raise ValueError('application-artifact 不是合法 published application manifest v2')
        if not manifest.get('application_id') or not isinstance(manifest.get('source_identity'), dict):
            raise ValueError('published application manifest 缺少来源身份')
        entries = manifest.get('files')
        if not isinstance(entries, dict):
            raise ValueError('published application manifest 缺少 files inventory')
        expected = {name for name, item in entries.items()
                    if isinstance(item, dict) and item.get('type') == 'file'}
        if len(expected) != sum(isinstance(item, dict) and item.get('type') == 'file'
                                for item in entries.values()):
            raise ValueError('application inventory 含无效文件条目')
        prefix = root + '/application/'
        members = {name[len(prefix):]: info for name, info in
                   ((item.filename, item) for item in archive.infolist()
                    if item.filename.startswith(prefix) and not item.is_dir())}
        if set(members) != expected:
            raise ValueError('application ZIP members 与 manifest files 不一致')
        staging = destination.with_name(destination.name + '.partial')
        if staging.exists() or destination.exists():
            raise ValueError(f'seed 输出已存在：{destination}')
        (staging / 'application').mkdir(parents=True)
        for name in sorted(expected):
            relative = PurePosixPath(name)
            if relative.is_absolute() or '..' in relative.parts or '\\' in name:
                raise ValueError(f'application inventory 路径越界：{name}')
            item = entries[name]
            info = members[name]
            target = staging / 'application' / Path(*relative.parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            hasher = hashlib.sha256()
            with archive.open(info) as source, target.open('wb') as output:
                while chunk := source.read(1024 * 1024):
                    hasher.update(chunk)
                    output.write(chunk)
            if hasher.hexdigest() != item.get('sha256'):
                raise ValueError(f'application 文件哈希不匹配：{name}')
            mode = item.get('mode')
            if isinstance(mode, int):
                target.chmod(mode & 0o777)
        (staging / 'application-manifest.json').write_bytes(manifest_bytes)
        with workspace_zip.open('rb') as source:
            source_workspace_sha256 = hashlib.file_digest(source, 'sha256').hexdigest()
        receipt = dict(provenance, source_workspace_sha256=source_workspace_sha256,
                       source_member=root, manifest_sha256=hashlib.sha256(
                           manifest_bytes).hexdigest(), application_id=manifest['application_id'])
        (staging / 'seed-provenance.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
        staging.rename(destination)
    return {'status': 'published', 'path': str(destination), 'manifest_sha256': receipt['manifest_sha256'],
            'application_id': receipt['application_id'], 'source_member': receipt['source_member']}


def _export_terminal_seed(directory, attempt, state):
    """Materialize a seed beside the attempt after a terminal observation."""
    status_path = directory / 'application-seed-status.json'
    target = directory / 'application-seed'
    if target.exists():
        return read(status_path) if status_path.exists() else {'status': 'published', 'path': str(target)}
    if state.get('remote_status') not in TERMINAL:
        return {'status': 'not_terminal', 'platform_status': state.get('remote_status')}
    observation = state.get('workspace_observation') or {}
    workspace = Path(observation.get('evidence', '')) / 'workspace.zip'
    provenance = {'attempt_id': attempt['attempt_id'], 'run_id': state.get('run_id'),
                  'submission_id': state.get('submission_id'), 'source': 'hosted-workspace-artifact'}
    try:
        result = export_application(workspace, target, provenance)
    except Exception as exc:
        result = {'status': 'evidence_incomplete', 'error': _safe(error(exc)),
                  'workspace': str(workspace), 'reason': 'no legal published application seed'}
    atomic(status_path, result)
    return result


def _workspace_observation(directory, attempt, state, client, value):
    """Let the existing attempt owner consume bounded native and resource evidence."""
    from lab.arc_bench.hosted_monitor import collect_workspace, evidence_retention, release_round, durable_evidence
    from lab.arc_bench.provider_liveness import assess, epoch, transition
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    dest = directory / 'monitor' / stamp / state['run_id']
    private_storage(dest)
    row = {'run_id': state['run_id'], 'evidence': str(dest), 'status': value.get('status'),
           'failure_reason': value.get('failure_reason'), 'boundary': epoch(value.get('started_at') or value.get('created_at')),
           'evaluation_started_at': value.get('evaluation_started_at')}
    atomic(dest / 'status.json', _safe(value))
    stages = {step['key']: step.get('status') for step in value.get('steps', []) if 'key' in step}
    preparing = value.get('status') == 'QUEUED' or stages.get('start_agent') == 'pending'
    if not preparing:
        try:
            client.download(run_path(state['run_id']) + '/workspace/template-bundle', dest / 'workspace.zip')
            collect_workspace(dest, row)
            # Resource baselines and latest counters remain separately inspectable;
            # ordinary observations do not retain another whole native archive.
            with ZipFile(dest / 'workspace.zip') as archive:
                for item in archive.infolist():
                    path = Path(item.filename)
                    if (item.is_dir() or path.is_absolute() or '..' in path.parts or '.factory26' not in path.parts or
                            any(part in path.parts for part in ('node_modules', 'runtime', '.private'))):
                        continue
                    selected = (path.name in {'run.json', 'delivery.json', 'audit-status.json', 'audit-report.json',
                                             'model-gateway.json', 'resource-latest.json', 'resource-status.json',
                                             'resources-baseline.jsonl'} or path.name == 'request-metadata.jsonl')
                    if not selected:
                        continue
                    target = dest / 'runtime-evidence' / path
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with archive.open(item) as source:
                        if item.file_size > 2 * 1024 * 1024:
                            source.seek(item.file_size - 2 * 1024 * 1024)
                        target.write_bytes(source.read(2 * 1024 * 1024))
                    if path.name == 'request-metadata.jsonl' and item.file_size > 2 * 1024 * 1024:
                        atomic(target.with_suffix('.window.json'), {'source_bytes': item.file_size,
                               'offset': item.file_size - 2 * 1024 * 1024, 'complete': False})
        except Exception as exc:
            row['workspace_error'] = error(exc)
    observed = time.time()
    observation = row.get('provider_observation') or {'observed_at': observed, 'phase': value.get('status'),
        'run_error': value.get('failure_reason'), 'sessions': [], 'errors': [],
        'observation_error': row.get('workspace_error')}
    state_file = directory / 'provider-monitor-state.json'
    monitor = read(state_file) if state_file.exists() else {'liveness': {}, 'notifications': {}, 'full_evidence': {}}
    verdict = assess(observation, monitor['liveness'].get(state['run_id']), stale_after=1800, min_samples=2)
    if preparing and value.get('status') not in TERMINAL:
        verdict['classification'] = 'preparing' if observed - state['accepted_at'] < 1800 else 'provider_unavailable'
        if verdict['classification'] == 'provider_unavailable':
            verdict['group_errors']['entry'] = 'No start_agent transition within 30 minutes of accepted dispatch'
    monitor['liveness'][state['run_id']] = verdict
    notice = transition(state['run_id'], verdict, monitor['notifications'])
    evidence_retention(row, verdict, notice, monitor)
    summary = {'attempt_id': attempt['attempt_id'], 'incarnation_id': state['incarnation_id'],
               'run_id': state['run_id'], 'submission_id': state['submission_id'], 'observed_at': observed,
               'platform_status': value.get('status'), 'provider': verdict, 'notice': notice,
               'evidence': str(dest), 'retention': row['retention'], 'workspace_error': row.get('workspace_error')}
    atomic(dest / 'collection.json', row)
    atomic(dest / 'liveness.json', verdict)
    atomic(state_file, monitor)
    atomic(directory / 'monitor-latest.json', summary)
    if notice:
        with (directory / 'monitor-events.jsonl').open('a') as stream:
            stream.write(json.dumps(summary, ensure_ascii=False) + '\n')
    durable_evidence(dest, omit=(dest / 'workspace.zip', dest / 'scratch'))
    release_round(row)
    state['workspace_observation'] = {'source': str(directory / 'monitor-latest.json'),
        'observed_at': observed, 'classification': verdict['classification'], 'evidence': str(dest)}


def _save(directory, state):
    state['observed_at'] = time.time()
    atomic(directory / 'execution.json', state)


def _get(directory, client, endpoint):
    if client is None:
        raise Blocked('explicit private cookie_file deployment binding required for platform access')
    value = client.request(endpoint)
    atomic(directory / 'platform' / ('observation-' + str(time.time_ns()) + '.json'),
           record('platform-observation', endpoint=endpoint, observed_at=time.time(), value=_safe(value)))
    return value


def _apply(state):
    pending = state.get('pending')
    if not pending or 'response' not in pending:
        return
    response = pending['response']
    try:
        if pending['action'] == 'snapshot':
            state['submission_id'] = identifier(response['submission']['id'])
            state['phase'] = 'snapshot-saved'
        elif pending['action'] == 'create':
            state['run_id'] = identifier(response['run']['id'])
            state['phase'] = 'run-created'
        else:
            state['phase'] = 'stop-requested' if pending['action'] == 'stop' else 'started'
        if pending['action'] == 'start':
            state['start_acknowledged'] = True
    except (KeyError, TypeError, ValueError):
        pending['error'] = {'type': 'InvalidResponse', 'message': 'platform response lacks exact identity'}
        return
    state.setdefault('request_effects', {})[pending['request_id']] = {'action': pending['action'], 'effect': 'acknowledged'}
    state['pending'] = None


def _post(directory, client, state, action, endpoint, request_id, *, secret=None, prior_ids=None, **kwargs):
    if client is None:
        raise Blocked('explicit private cookie_file deployment binding required for platform writes')
    if state.get('pending'):
        raise Blocked('previous platform write is unknown; query only, never resend')
    pending = {'action': action, 'endpoint': endpoint, 'request_id': request_id,
               'requested_at': time.time(), 'prior_ids': prior_ids}
    state['pending'] = pending
    _save(directory, state)
    try:
        response = client.request(endpoint, 'POST', secret=secret, **kwargs)
    except Exception as exc:
        pending['error'] = _safe(error(exc), secret)
        _save(directory, state)
        atomic(directory / 'platform' / (request_id + '-' + action + '.json'), record('platform-write', **pending))
        raise Blocked(f'platform {action} outcome unknown: {pending["error"]}') from exc
    pending['response'] = _safe(response, secret)
    # Save the response before interpreting identity or permitting the next write.
    _save(directory, state)
    atomic(directory / 'platform' / (request_id + '-' + action + '.json'), record('platform-write', **pending))
    _apply(state)
    _save(directory, state)
    if state.get('pending'):
        raise Blocked('platform response identity unknown; query only')


def _validate_run(state, backend, value):
    if (not isinstance(value, dict) or value.get('id') != state['run_id'] or
            value.get('submission_id') != state['submission_id'] or value.get('requirement_id') != backend['task']):
        raise Blocked('platform run identity does not bind this submission and task')


def _reconcile(directory, client, state, backend):
    _apply(state)
    pending = state.get('pending')
    if not pending:
        return
    action = pending['action']
    if action in {'snapshot', 'create'}:
        history = _get(directory, client, '/competitions/' + backend['competition_id'] + '/submissions')
        if not isinstance(history, list):
            raise Blocked('unrecognized platform history')
        if action == 'snapshot':
            candidates = [row for row in history if row.get('display_name') == state['display_name']
                          and row.get('id') not in (pending.get('prior_ids') or [])]
            if len(candidates) != 1:
                raise Blocked('unknown snapshot has no unique matching remote identity')
            pending['response'] = {'submission': {'id': identifier(candidates[0]['id'])}}
        else:
            candidates = {score.get('run_id') for row in history if row.get('id') == state['submission_id']
                          for score in row.get('task_scores', []) if score.get('task_id') == backend['task'] and score.get('run_id')}
            if len(candidates) != 1:
                raise Blocked('unknown create has no unique matching remote run')
            candidate = identifier(candidates.pop())
            validation = dict(state, run_id=candidate)
            _validate_run(validation, backend, _get(directory, client, run_path(candidate)))
            pending['response'] = {'run': {'id': candidate}}
    else:
        value = _get(directory, client, run_path(state['run_id']))
        _validate_run(state, backend, value)
        confirmed = value.get('status') in TERMINAL if action == 'stop' else (
            value.get('started_at') or value.get('status') in TERMINAL | {'QUEUED', 'STARTING', 'RUNNING', 'PAUSED'})
        if not confirmed:
            raise Blocked('platform action has no physical observation; preserve pending')
        pending['response'] = {}
    _save(directory, state)
    _apply(state)
    _save(directory, state)


def _package(directory, attempt):
    path = directory / 'inputs' / 'agent'
    if path.is_file():
        from .artifacts import contents, retain, verify
        reference = attempt['job']['inputs']['agent']
        retain(attempt['artifact_store'], reference, attempt['attempt_id'],
               'platform-submission', attempt['attempt_id'] + '--retain--agent')
        if contents(path) != verify(attempt['artifact_store'], reference)['contents']:
            raise Blocked('hosted submission ZIP differs from frozen artifact')
        return path
    job = attempt['job']
    if job['purpose'] != 'evaluate' or 'application' not in job['inputs']:
        raise Blocked('hosted dispatch needs frozen agent ZIP or explicit application evaluation input')
    from lab.arc_bench.arc_artifacts import verify as verify_application
    from .artifacts import publish, retain, verify
    for name in ('application', 'application_receipt', 'requirements'):
        retain(attempt['artifact_store'], job['inputs'][name], attempt['attempt_id'],
               'hosted-replay-' + name, attempt['attempt_id'] + '--retain--' + name)
    application = directory / 'inputs' / 'application'
    receipt = directory / 'inputs' / 'application_receipt'
    requirements = directory / 'inputs' / 'requirements' / 'requirements.yaml'
    identity = verify_application(application, receipt)
    hashes = {row['path']: row['sha256'] for row in identity['entries'] if row['type'] == 'file'}
    if len(hashes) != len(identity['entries']):
        raise Blocked('hosted replay ZIP cannot transport application links')
    for component in ('frontend', 'backend'):
        if not (application / component / 'package.json').is_file():
            raise Blocked('frozen application lacks ' + component + '/package.json')
    source = {'application': job['inputs']['application'], 'application_receipt': job['inputs']['application_receipt'],
              'requirements': job['inputs']['requirements'], 'source_job': job.get('source_job')}
    requirement_sha256 = digest(requirements)
    case = {'run_id': attempt['attempt_id'], 'variant': job['backend']['variant'],
            'competition': job['backend']['competition_id'], 'task': job['backend']['task'],
            'requirements_sha256': requirement_sha256, 'files': hashes,
            'application_sha256': hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest(),
            'application_manifest': identity, 'source_application': source, 'provenance': 'exp-application-artifact'}
    manifest = {'mode': 'artifact-replay', 'delay_seconds': 3, 'cases': [case]}
    production = directory / 'replay-production'
    production.mkdir(exist_ok=True)
    frozen = canonical(source)
    intent = production / 'intent.json'
    if intent.exists() and read(intent)['source_sha256'] != frozen:
        raise Blocked('hosted replay source differs from durable production intent')
    if not intent.exists():
        atomic(intent, record('production', attempt_id=attempt['attempt_id'], source_sha256=frozen, source=source))
    package = production / 'agent.zip'
    package_receipt = production / 'receipt.json'
    if package_receipt.exists():
        previous = read(package_receipt)
        if previous['source_sha256'] != frozen or digest(package) != previous['package_sha256']:
            raise Blocked('hosted replay production identity changed')
        verify(attempt['artifact_store'], previous['artifact'])
        retain(attempt['artifact_store'], previous['artifact'], attempt['attempt_id'], 'platform-submission',
               attempt['attempt_id'] + '--retain--replay-package')
        return package
    scripts = Path(__file__).resolve().parents[1] / 'arc_bench'
    if not package.exists():
        with package.open('xb') as stream:
            with ZipFile(stream, 'w', compression=ZIP_DEFLATED) as archive:
                archive.write(scripts / 'arc_replay.py', 'main.py')
                archive.write(scripts / 'arc_artifacts.py', 'arc_artifacts.py')
                archive.writestr('requirements.txt', '')
                archive.writestr('replay-manifest.json', json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
                for name in hashes:
                    archive.write(application / name, 'applications/' + attempt['attempt_id'] + '/' + name)
            stream.flush()
            os.fsync(stream.fileno())
    # Independent readback also reconciles a completed ZIP whose publication receipt was interrupted.
    with ZipFile(package) as archive:
        expected_names = {'main.py', 'arc_artifacts.py', 'requirements.txt', 'replay-manifest.json'} | {
            'applications/' + attempt['attempt_id'] + '/' + name for name in hashes}
        if set(archive.namelist()) != expected_names or len(archive.namelist()) != len(expected_names):
            raise Blocked('hosted replay ZIP readback inventory differs')
        if json.loads(archive.read('replay-manifest.json')) != manifest:
            raise Blocked('hosted replay ZIP source manifest differs')
        for name, expected in hashes.items():
            if hashlib.sha256(archive.read('applications/' + attempt['attempt_id'] + '/' + name)).hexdigest() != expected:
                raise Blocked('hosted replay ZIP readback content differs: ' + name)
        for name, source_path in (('main.py', scripts / 'arc_replay.py'), ('arc_artifacts.py', scripts / 'arc_artifacts.py')):
            if hashlib.sha256(archive.read(name)).hexdigest() != digest(source_path):
                raise Blocked('hosted replay producer runtime differs')
    artifact = publish(attempt['artifact_store'], package, 'evaluation-input', provenance=source,
                       capabilities={'model_generation': False, 'source_application_sha256': identity['sha256']},
                       request_id=attempt['attempt_id'] + '--replay-package', consumer=attempt['attempt_id'],
                       purpose='platform-submission')
    atomic(package_receipt, record('production', source_sha256=frozen, source=source,
                                 package_sha256=digest(package), artifact=artifact, completed_at=time.time()))
    return package


def _latest_submission(history):
    if not isinstance(history, list) or not history:
        raise Blocked('platform submission history is empty or unrecognized')
    if any('is_latest' in row for row in history):
        latest = [row for row in history if row.get('is_latest') is True]
    else:
        # The live competition API exposes created_at, not is_latest. Deletion
        # eligibility also depends on active runs and cannot establish recency.
        try:
            dated = [(datetime.fromisoformat(row['created_at']).replace(tzinfo=timezone.utc), row) for row in history]
        except (KeyError, TypeError, ValueError) as exc:
            raise Blocked('submission history lacks valid creation identities') from exc
        newest = max(date for date, _ in dated)
        latest = [row for date, row in dated if date == newest]
    if len(latest) != 1:
        raise Blocked('platform submission history has no unique latest identity')
    return latest[0]



def freeze_replay(attempt_dir):
    """Offline package production from explicitly bound inputs; no platform access."""
    directory = Path(attempt_dir).resolve(strict=True)
    attempt = require(read(directory / 'attempt.json'), 'attempt')
    with locked(directory / 'hosted.lock'):
        return _package(directory, attempt)


def dispatch(attempt_dir):
    directory, attempt, backend, deployment, client = _context(attempt_dir)
    if client is None:
        raise Blocked('hosted dispatch requires explicit private cookie_file deployment binding')
    request = require(read(directory / 'request.json'), 'request')
    if request['attempt_id'] != attempt['attempt_id'] or request['action'] != 'dispatch':
        raise ValueError('dispatch request does not bind attempt')
    with locked(directory / 'hosted.lock'):
        package = _package(directory, attempt)
        metadata = package_metadata(package)
        if metadata.get('variant') and metadata['variant'] != backend['variant']:
            raise ValueError('frozen package variant differs from backend')
        frozen = canonical({'backend': backend, 'package_sha256': digest(package), 'request': request})
        if (directory / 'execution.json').exists():
            state = require(read(directory / 'execution.json'), 'execution')
            if state['dispatch_sha256'] != frozen:
                raise Blocked('attempt already bound to different dispatch input')
        else:
            state = record('execution', attempt_id=attempt['attempt_id'], backend='hosted',
                           incarnation_id=attempt['attempt_id'], dispatch_request_id=request['request_id'],
                           dispatch_sha256=frozen, accepted_at=time.time(), phase='accepted', pending=None, submission_id=None, run_id=None,
                           display_name=attempt['attempt_id'], capabilities=capabilities(), model_facts={'desired': backend['model_config']},
                           credential_mode=backend['credential_mode'], archive={'status': 'not-exported'})
            _save(directory, state)
        with locked(private_storage(client.cookie.parent / 'exp-hosted-locks') / (backend['competition_id'] + '.lock')):
            _reconcile(directory, client, state, backend)
            if not state['submission_id']:
                detail = _get(directory, client, '/competitions/' + backend['competition_id'])
                if detail.get('id') != backend['competition_id'] or detail.get('template_required'):
                    raise Blocked('competition identity or template requirement unsupported')
                if backend['task'] not in {row['id'] for row in detail.get('tasks', [])}:
                    raise ValueError('task does not belong to frozen competition')
                history = _get(directory, client, '/competitions/' + backend['competition_id'] + '/submissions')
                if not isinstance(history, list):
                    raise Blocked('unrecognized platform history')
                # A new latest snapshot can invalidate another attempt's creation rights.
                for row in ([_latest_submission(history)] if history else []):
                    if row:
                        for score in row.get('task_scores', []):
                            if score.get('run_id'):
                                value = _get(directory, client, run_path(score['run_id']))
                                if value.get('status') not in TERMINAL and not (
                                        backend.get('parallel_distinct_tasks') is True and
                                        backend['credential_mode'] == 'self_funded' and
                                        value.get('requirement_id') and value['requirement_id'] != backend['task']):
                                    raise Blocked('competition latest snapshot still has active or unknown execution')
                secret = None
                if backend['credential_mode'] == 'self_funded':
                    credential = Path(deployment['credential_file'])
                    if credential.stat().st_mode & 0o077:
                        raise ValueError('private credential_file must be mode 600')
                    private = read(credential)
                    values = private.get('environment', private)
                    secret = values.get('FACTORY26_API_KEY') or values.get('OPENAI_API_KEY')
                    if not secret:
                        raise ValueError('selected credential_file lacks model key')
                _post(directory, client, state, 'snapshot', '/submissions', request['request_id'], secret=secret,
                      fields={'competition_id': backend['competition_id'], 'runtime': 'python', 'catalog': 'competition',
                              'agent_source': 'upload', 'credential_mode': backend['credential_mode'],
                              'display_name': state['display_name'], **{key: backend['model_config'][key] for key in ('model', 'visual_model', 'base_url')}},
                      package=package, prior_ids=[row['id'] for row in history])
            if not state['run_id']:
                history = _get(directory, client, '/competitions/' + backend['competition_id'] + '/submissions')
                latest = _latest_submission(history)
                if latest['id'] != state['submission_id']:
                    raise Blocked('snapshot is no longer uniquely latest; do not create')
                if any(score.get('task_id') == backend['task'] and score.get('run_id') for score in latest.get('task_scores', [])):
                    raise Blocked('snapshot already has a task run; reconcile identity instead of creating')
                _post(directory, client, state, 'create', '/runs', request['request_id'],
                      fields={'submission_id': state['submission_id'], 'requirement_id': backend['task']})
            if state['phase'] == 'run-created':
                _post(directory, client, state, 'start', run_path(state['run_id']) + '/start', request['request_id'])
        if state.get('start_acknowledged'):
            try:
                start_observer(directory)
            except Exception as exc:
                atomic(directory / 'observer-launch-error.json', record('error', **error(exc)))
        return state


def observe_identity(attempt_dir, live=False):
    """Only current remote identity/status; no workspace download or diagnostics."""
    directory, attempt, backend, deployment, client = _context(attempt_dir)
    with locked(directory / 'hosted.lock'):
        if not (directory / 'execution.json').exists():
            return record('execution', attempt_id=attempt['attempt_id'], backend='hosted', phase='not-dispatched', capabilities=capabilities())
        state = require(read(directory / 'execution.json'), 'execution')
        if live and client and state.get('run_id'):
            try:
                value = _get(directory, client, run_path(state['run_id']))
                _validate_run(state, backend, value)
                state.update(remote_status=value.get('status'), platform_result=_safe(value))
                if value.get('status') in TERMINAL:
                    state['phase'] = 'exited'
                elif state.get('start_acknowledged'):
                    state['phase'] = 'active'
                state['observation'] = 'known' if value.get('status') else 'unknown'
                state.pop('observation_error', None)
            except Exception as exc:
                state['observation_error'] = _safe(error(exc))
            _save(directory, state)
        return state


def observe(attempt_dir, live=False):
    return observe_identity(attempt_dir, live=live)


def collect_progress(attempt_dir):
    """One attempt's existing provider evidence policy; never writes platform state."""
    directory, attempt, backend, deployment, client = _context(attempt_dir)
    with locked(directory / 'progress.lock'):
        state = observe_identity(directory, live=True)
        if state.get('observation_error'):
            raise Blocked('platform identity observation failed; original error is preserved in execution.json')
        if not state.get('run_id') or not state.get('platform_result'):
            return state
        _workspace_observation(directory, attempt, state, client, state['platform_result'])
        with locked(directory / 'hosted.lock'):
            current = read(directory / 'execution.json')
            current['workspace_observation'] = state['workspace_observation']
            _save(directory, current)
        return current


def start_observer(attempt_dir):
    """Attach a GET-only observer to this durable accepted execution, never dispatch."""
    directory, attempt, backend, deployment, client = _context(attempt_dir)
    state = require(read(directory / 'execution.json'), 'execution')
    path = directory / 'observer.json'
    with locked(directory / 'observer-launch.lock'):
        if path.exists():
            previous = read(path)
            if previous['attempt_id'] != attempt['attempt_id'] or previous['incarnation_id'] != state['incarnation_id']:
                raise Blocked('observer belongs to another execution')
            if process_state(previous.get('process')) == 'alive' or previous.get('phase') == 'completed':
                return previous
        root = directory.parents[1]
        manifest = read(root / 'experiment.json')
        runtime = manifest['controller_runtime']
        from .controller import _control_source
        source = _control_source(root, manifest)
        env = dict(os.environ, PYTHONPATH=str(source), PYTHONDONTWRITEBYTECODE='1')
        launch_path = directory / 'observer-launch.json'
        if launch_path.exists() and read(launch_path).get('status') == 'pending':
            raise Blocked('observer spawn acknowledgement unknown; preserve original launch instead of duplicating collection')
        atomic(launch_path, record('observer-launch', attempt_id=attempt['attempt_id'],
            incarnation_id=state['incarnation_id'], status='pending', requested_at=time.time()))
        try:
            with (directory / 'observer.log').open('ab', buffering=0) as log:
                process = subprocess.Popen([runtime['launcher'],'-B','-m','lab.exp.hosted','observer',str(directory)],
                    cwd=source,env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=log,start_new_session=True)
        except Exception as exc:
            atomic(launch_path, record('observer-launch', status='not-created', error=error(exc)))
            raise
        atomic(launch_path, record('observer-launch', attempt_id=attempt['attempt_id'],
            incarnation_id=state['incarnation_id'], status='spawned', process=process_identity(process.pid)))
        value = record('attempt-observer',attempt_id=attempt['attempt_id'],incarnation_id=state['incarnation_id'],
            process=process_identity(process.pid),phase='accepted',capabilities={'platform_writes':False,'dispatch':False})
        atomic(path,value)
        return value


def observer(attempt_dir):
    directory = Path(attempt_dir).resolve(strict=True)
    with locked(directory / 'observer-worker.lock', blocking=False):
        state = require(read(directory/'execution.json'),'execution')
        identity = state['incarnation_id']
        backend = require(read(directory / 'attempt.json'), 'attempt')['job']['backend']
        attempts = 0
        while True:
            state = observe_identity(directory, live=False)
            if state['incarnation_id'] != identity:
                raise Blocked('observer execution identity changed')
            terminal = state.get('remote_status') in TERMINAL
            due = state.get('next_observation_at', 0)
            if time.time() < due:
                time.sleep(min(60,max(.1,due-time.time())))
                continue
            interval = backend.get('observation_interval_seconds',
                180 if time.time()-state['accepted_at']<600 else 480)
            with locked(directory/'hosted.lock'):
                current=read(directory/'execution.json')
                current['next_observation_at']=time.time()+interval
                _save(directory,current)
            try:
                state = collect_progress(directory)
                if state.get('remote_status') in TERMINAL:
                    seal(directory)
                    result=record('attempt-observer',attempt_id=state['attempt_id'],incarnation_id=identity,
                        phase='completed',process=process_identity(),finished_at=time.time())
                    atomic(directory/'observer.json',result)
                    return result
            except Exception as exc:
                attempts += 1
                atomic(directory/'observer-error.json',record('error',**error(exc),incarnation_id=identity))
                if state.get('remote_status') in TERMINAL and attempts>=3:
                    result=record('attempt-observer',attempt_id=state['attempt_id'],incarnation_id=identity,
                        phase='completed',process=process_identity(),finished_at=time.time(),evidence='incomplete',error=error(exc))
                    atomic(directory/'observer.json',result)
                    return result
                time.sleep(min(60,interval))



def control(attempt_dir, request):
    directory, attempt, backend, deployment, client = _context(attempt_dir)
    require(request, 'request')
    if request['attempt_id'] != attempt['attempt_id']:
        raise ValueError('control request does not bind attempt')
    if request['action'] == 'export':
        return export(directory, request)
    if request['action'] == 'seal':
        current = require(read(directory / 'execution.json'), 'execution')
        if request.get('expected_incarnation') != current['incarnation_id']:
            raise Blocked('seal must bind the accepted hosted incarnation')
        return seal(directory, request_id=request['request_id'])
    if request['action'] != 'stop':
        raise Blocked('hosted supports stop; pause, resume and checkpoint are unsupported')
    with locked(directory / 'hosted.lock'):
        state = require(read(directory / 'execution.json'), 'execution')
        if request.get('expected_incarnation') != state['incarnation_id']:
            raise Blocked('control must bind exact hosted execution incarnation')
        path = directory / 'controls' / (identifier(request['request_id']) + '.json')
        if path.exists() and read(path) != request:
            raise ValueError('control request identity reused with different parameters')
        atomic(path, request)
        if request['request_id'] in state.get('request_effects', {}):
            return state
        if state.get('pending'):
            _reconcile(directory, client, state, backend)
            if request['request_id'] in state.get('request_effects', {}):
                return state
        if not state.get('run_id'):
            raise Blocked('remote run identity unknown; stop cannot target it')
        _post(directory, client, state, 'stop', run_path(state['run_id']) + '/cancel', request['request_id'])
        return state


def seal(attempt_dir, request_id=None):
    directory, attempt, backend, deployment, client = _context(attempt_dir)
    request_id = identifier(request_id or (attempt['attempt_id'] + '--platform-export'))
    receipt_path = directory / 'exports' / (request_id + '.json')
    if receipt_path.exists():
        from .artifacts import verify
        previous = read(receipt_path)
        verify(attempt['artifact_store'], previous['archive']['artifact'])
        if (directory / 'execution.json').exists():
            with locked(directory / 'export.lock'):
                state = require(read(directory / 'execution.json'), 'execution')
                seed_status = _export_terminal_seed(directory, attempt, state)
                with locked(directory / 'hosted.lock'):
                    current = require(read(directory / 'execution.json'), 'execution')
                    current['application_seed'] = seed_status
                    _save(directory, current)
        return previous
    state = observe(directory, live=True)
    if not state.get('run_id'):
        raise Blocked('remote run identity unknown; cannot export evidence')
    if state.get('remote_status') not in TERMINAL:
        raise Blocked('terminal evidence publication requires a terminal remote run; ongoing collection belongs to its observer')
    with locked(directory / 'export.lock'):
        state = require(read(directory / 'execution.json'), 'execution')
        state['application_seed'] = _export_terminal_seed(directory, attempt, state)
        folder = directory / 'platform'
        for name, endpoint in (('traceability', 'traceability?node_id=__all__'), ('commit-history', 'commit-history')):
            collect_hosted(client, run_path(state['run_id']) + '/' + endpoint, folder, name,
                           save=atomic, redact=_safe)
        cursor_file = folder / 'log-cursor.json'
        cursor = read(cursor_file) if cursor_file.exists() else {'log_offset': 0}
        chunk = _get(directory, client, run_path(state['run_id']) + '/logs?' + urlencode(cursor))
        if not isinstance(chunk, dict) or type(chunk.get('log_offset')) is not int or chunk['log_offset'] < cursor['log_offset']:
            raise Blocked('invalid log cursor; source observation preserved')
        atomic(cursor_file, {'log_offset': chunk['log_offset']})
        from .artifacts import publish
        snapshot = directory / 'export-snapshots' / request_id
        if not snapshot.exists():
            import shutil
            snapshot.parent.mkdir(exist_ok=True)
            staging = snapshot.with_name(snapshot.name + '.partial')
            if staging.exists():
                raise Blocked('platform export snapshot copy incomplete; preserve partial and use a new export request')
            shutil.copytree(folder, staging)
            staging.replace(snapshot)
        reference = publish(attempt['artifact_store'], snapshot, artifact_type='terminal-archive',
                            provenance={'component': 'exp-hosted', 'attempt_id': attempt['attempt_id'],
                                        'submission_id': state['submission_id'], 'run_id': state['run_id'],
                                        'gaps': ['platform JSON export does not prove complete application, Git/native history or telemetry drain']},
                            capabilities={'checkpoint': False, 'coverage': 'platform-json-only'},
                            request_id=request_id, consumer=attempt['attempt_id'], purpose='platform-evidence')
        state['archive'] = {'status': 'partial', 'artifact': reference}
        with locked(directory / 'hosted.lock'):
            current = read(directory / 'execution.json')
            current.update(archive=state['archive'], application_seed=state['application_seed'])
            atomic(receipt_path, current)
            _save(directory, current)
        return current


def export(attempt_dir, request):
    """Transport explicitly selected already published evidence; no platform collection."""
    from . import artifacts
    directory = Path(attempt_dir)
    attempt = require(read(directory / 'attempt.json'), 'attempt')
    state = require(read(directory / 'execution.json'), 'execution')
    if request.get('expected_incarnation') != state['incarnation_id']:
        raise Blocked('export must bind the accepted platform incarnation')
    parameters = request['parameters']
    selections = parameters.get('assets')
    if not selections or not parameters.get('consumer') or not parameters.get('target_store'):
        raise ValueError('export needs selected assets, consumer and target_store')
    offered = [state['archive']['artifact']] if state.get('archive', {}).get('artifact') else []
    for row in selections:
        if row.get('reference') not in offered or set(row) - {'reference','member','location'}:
            raise Blocked('selected platform evidence has not been published by this attempt')
        artifacts.transfer(attempt['artifact_store'], parameters['target_store'], row['reference'],
            selected_member=row.get('member','.'), consumer=parameters['consumer'],
            request_id=request['request_id'] + '--' + canonical([row['reference'],row.get('member','.')])[:16])
    effect = record('export', request_id=request['request_id'], status='preserved', assets=selections,
        target_store=parameters['target_store'], consumer=parameters['consumer'])
    atomic(directory / 'exports' / (identifier(request['request_id']) + '.json'), effect)
    return effect


if __name__ == '__main__':
    if sys.argv[1:2] == ['observer'] and len(sys.argv)==3:
        observer(sys.argv[2])
    else:
        raise SystemExit('only single-attempt observer entry is supported')
