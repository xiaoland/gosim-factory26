"""Single-attempt ARC platform adapter; durable uncertain writes are query-only."""
from pathlib import Path
import time
import hashlib
import json
import os
from zipfile import ZipFile, ZIP_DEFLATED
from urllib.parse import urlencode, urlsplit

from .core import Blocked, atomic, canonical, digest, error, identifier, locked, read, record, require
from lab.arc_bench.playground import Client, CONFIG, redact, run_path
from lab.arc_bench.traceability import collect_hosted
from lab.arc_bench.arc_artifacts import package_metadata

TERMINAL = {'PASSED', 'FAILED', 'CANCELLED'}


def capabilities(target=None):
    return {'backend': 'hosted', 'dispatch': True, 'observe': True, 'stop': True,
            'pause': False, 'resume': False, 'checkpoint': False,
            'telemetry': 'platform-export-only', 'export': 'partial-platform-evidence'}


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
        return path
    job = attempt['job']
    if job['purpose'] != 'evaluate' or 'application' not in job['inputs']:
        raise Blocked('hosted dispatch needs frozen agent ZIP or explicit application evaluation input')
    from lab.arc_bench.arc_artifacts import verify as verify_application
    from .artifacts import publish
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
                       capabilities={'model_generation': False, 'source_application_sha256': identity['sha256']})
    atomic(package_receipt, record('production', source_sha256=frozen, source=source,
                                 package_sha256=digest(package), artifact=artifact, completed_at=time.time()))
    return package


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
        with locked(CONFIG / 'exp-hosted-locks' / (backend['competition_id'] + '.lock')):
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
                for row in history:
                    if row.get('is_latest'):
                        for score in row.get('task_scores', []):
                            if score.get('run_id'):
                                value = _get(directory, client, run_path(score['run_id']))
                                if value.get('status') not in TERMINAL:
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
                latest = [row for row in history if row.get('is_latest') is True]
                if len(latest) != 1 or latest[0]['id'] != state['submission_id']:
                    raise Blocked('snapshot is no longer uniquely latest; do not create')
                if any(score.get('task_id') == backend['task'] and score.get('run_id') for score in latest[0].get('task_scores', [])):
                    raise Blocked('snapshot already has a task run; reconcile identity instead of creating')
                _post(directory, client, state, 'create', '/runs', request['request_id'],
                      fields={'submission_id': state['submission_id'], 'requirement_id': backend['task']})
            if state['phase'] == 'run-created':
                _post(directory, client, state, 'start', run_path(state['run_id']) + '/start', request['request_id'])
        return state


def observe(attempt_dir, live=False):
    directory, attempt, backend, deployment, client = _context(attempt_dir)
    with locked(directory / 'hosted.lock'):
        if not (directory / 'execution.json').exists():
            return record('execution', attempt_id=attempt['attempt_id'], backend='hosted', phase='not-dispatched', capabilities=capabilities())
        state = require(read(directory / 'execution.json'), 'execution')
        if live and time.time() >= state.get('next_observation_at', 0):
            interval = 180 if time.time() - state['accepted_at'] < 600 else 480
            state['next_observation_at'] = time.time() + interval
            try:
                _reconcile(directory, client, state, backend)
                if state.get('run_id'):
                    value = _get(directory, client, run_path(state['run_id']))
                    _validate_run(state, backend, value)
                    state['remote_status'] = value.get('status')
                    state['platform_result'] = _safe(value)
                    if value.get('status') in TERMINAL:
                        state['phase'] = 'exited'
                    elif state.get('start_acknowledged'):
                        state['phase'] = 'active'
                    state['observation'] = 'known' if value.get('status') else 'unknown'
                state.pop('observation_error', None)
            except Exception as exc:
                state['observation_error'] = _safe(error(exc))
                state['observation'] = 'unknown'
            _save(directory, state)
        return state


def control(attempt_dir, request):
    directory, attempt, backend, deployment, client = _context(attempt_dir)
    require(request, 'request')
    if request['attempt_id'] != attempt['attempt_id']:
        raise ValueError('control request does not bind attempt')
    if request['action'] == 'export':
        return export(directory)
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


def export(attempt_dir):
    directory, attempt, backend, deployment, client = _context(attempt_dir)
    state = observe(directory, live=True)
    if not state.get('run_id'):
        raise Blocked('remote run identity unknown; cannot export evidence')
    with locked(directory / 'hosted.lock'):
        state = require(read(directory / 'execution.json'), 'execution')
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
        reference = publish(attempt['artifact_store'], folder, artifact_type='terminal-archive',
                            provenance={'component': 'exp-hosted', 'attempt_id': attempt['attempt_id'],
                                        'submission_id': state['submission_id'], 'run_id': state['run_id'],
                                        'gaps': ['platform JSON export does not prove complete application, Git/native history or telemetry drain']},
                            capabilities={'checkpoint': False, 'coverage': 'platform-json-only'})
        state['archive'] = {'status': 'partial', 'artifact': reference}
        _save(directory, state)
        return state
