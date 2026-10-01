"""Freeze, launch and continue one authorized ARC experiment operation."""
import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import traceback

from lab.control import process_identity, process_state
from lab.records import file_hash, inventory, read_json
from .competition import Controller, Blocked, atomic_json, prepare as prepare_hosted
from .playground import redact

TERMINAL = {'completed', 'finished', 'failed', 'interrupted', 'cancelled', 'lost'}
SOURCE = Path(__file__).resolve().parents[2]


@contextmanager
def lock(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


def error_record(error):
    return redact({'type': type(error).__name__, 'message': str(error),
                   'http_status': getattr(error, 'status', None), 'detail': getattr(error, 'detail', None)})


def resolve(value, base):
    return str((base / Path(value).expanduser()).resolve(strict=True))


def freeze_source(directory):
    target = directory / 'source/lab'
    for folder in (Path(''), Path('arc_bench')):
        (target / folder).mkdir(parents=True, exist_ok=True)
        for file in (SOURCE / 'lab' / folder).glob('*.py'):
            shutil.copy2(file, target / folder / file.name)
    return {str(p.relative_to(directory)): file_hash(p) for p in target.rglob('*.py')}


def controller_identity(experiment):
    result = inventory(experiment / 'controller-source')
    # Historical controllers generate bytecode caches; they are not frozen source.
    entries = [row for row in result['entries'] if '__pycache__' not in Path(row['path']).parts]
    encoded = json.dumps(entries, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()
    return {**result, 'entries': entries, 'sha256': hashlib.sha256(encoded).hexdigest()}


def prepare(spec_path, directory):
    os.umask(0o077)
    spec_path = Path(spec_path).resolve(strict=True)
    directory = Path(directory).resolve()
    directory.mkdir(parents=True, exist_ok=True)
    spec = read_json(spec_path)
    if not isinstance(spec.get('authorization'), str) or not spec['authorization'].strip():
        raise ValueError('operation requires the authorized scope in authorization')
    if spec.get('venue') not in {'local', 'hosted'}:
        raise ValueError('venue must be local or hosted')
    spec_hash = file_hash(spec_path)
    with lock(directory / 'prepare.lock'):
        input_path = directory / 'inputs.json'
        if input_path.exists():
            inputs = read_json(input_path)
            if inputs['spec_sha256'] != spec_hash:
                raise ValueError('operation inputs changed; use a new operation')
            verify_inputs(directory, inputs)
            return inputs
        original = directory / 'spec.json'
        if original.exists() and file_hash(original) != spec_hash:
            raise ValueError('unfinished operation belongs to different inputs; retain it')
        if not original.exists():
            shutil.copy2(spec_path, original)
        try:
            preparations = {}
            declared = spec.get('preparations', {})
            if not isinstance(declared, dict):
                raise ValueError('preparations must be an object')
            if spec['venue'] == 'local':
                mapping = spec.get('preparation_jobs', {})
                if not isinstance(mapping, dict) or set(mapping.values()) != set(declared):
                    raise ValueError('every preparation must be explicitly bound through preparation_jobs')
                if bool(spec.get('recipe')) == bool(spec.get('experiment')):
                    raise ValueError('local operation requires exactly one of recipe or existing experiment')
                if spec.get('recipe'):
                    from lab.plan import normalize
                    recipe_origin = Path(resolve(spec['recipe'], spec_path.parent))
                    jobs, *_ = normalize(read_json(recipe_origin), recipe_origin.parent)
                else:
                    frozen = Path(resolve(spec['experiment'], spec_path.parent)) / 'manifest.json'
                    jobs = read_json(frozen)['jobs']
                if set(mapping) - {job['id'] for job in jobs}:
                    raise ValueError('preparation_jobs contains an unknown job')
            elif {row['preparation'] for row in spec['hosted'] if 'preparation' in row} != set(declared):
                raise ValueError('every preparation must be explicitly bound to a hosted input')
            from .recovery import prepare as prepare_recovery
            for name, request in spec.get('preparations', {}).items():
                if Path(name).name != name or name in {'', '.', '..'}:
                    raise ValueError('preparation id must be a directory name')
                request = {**request}
                if request.get('package'):
                    request['package'] = resolve(request['package'], spec_path.parent)
                if request.get('recovery'):
                    request['recovery'] = dict(request['recovery'])
                    for field in ('journal', 'workspace', 'base_package', 'source_package', 'stop_receipt',
                                  'source_identity', 'stop_identity', 'git_reconstruction', 'braid',
                                  'braid_source', 'braid_source_identity'):
                        if request['recovery'].get(field):
                            request['recovery'][field] = resolve(request['recovery'][field], spec_path.parent)
                preparations[name] = prepare_recovery(request, directory / 'preparations' / name)
            inputs = {'schema_version': 1, 'spec_sha256': spec_hash, 'authorization': spec['authorization'],
                      'venue': spec['venue'], 'prepared_at': time.time(), 'preparations': preparations,
                      'credential_file': resolve(spec['credential_file'], spec_path.parent) if spec.get('credential_file') else None,
                      'monitor_output': str((spec_path.parent / Path(spec.get('monitor_output', directory / 'observation')).expanduser()).resolve()),
                      'bindings': {}}
            if spec['venue'] == 'local':
                from lab.plan import create, normalize
                if bool(spec.get('recipe')) == bool(spec.get('experiment')):
                    raise ValueError('local operation requires exactly one of recipe or existing experiment')
                if spec.get('recipe'):
                    recipe_origin = Path(resolve(spec['recipe'], spec_path.parent))
                    recipe = read_json(recipe_origin)
                    normalized, *_ = normalize(recipe, recipe_origin.parent)
                    mapping = spec.get('preparation_jobs', {})
                    jobs = {job['id']: job for job in normalized}
                    if not isinstance(mapping, dict) or set(mapping) - jobs.keys() or set(mapping.values()) - preparations.keys():
                        raise ValueError('preparation_jobs must map known job IDs to preparation IDs')
                    for raw, job in zip(recipe['jobs'], normalized):
                        raw.update(id=job['id'], inputs=job['inputs'])
                        if job['id'] in mapping:
                            raw['inputs']['agent'] = preparations[mapping[job['id']]]['package']
                    recipe_path = directory / 'recipe.json'
                    if recipe_path.exists() and read_json(recipe_path) != recipe:
                        raise ValueError('recipe changed during preparation; retain operation and use a new directory')
                    atomic_json(recipe_path, recipe)
                    experiment = directory / 'experiment'
                    if not (experiment / 'manifest.json').exists():
                        create(recipe_path, experiment_root=experiment)
                else:
                    experiment = Path(resolve(spec['experiment'], spec_path.parent))
                manifest = read_json(experiment / 'manifest.json')
                mapping = spec.get('preparation_jobs', {})
                jobs = {job['id']: job for job in manifest['jobs']}
                if not isinstance(mapping, dict) or set(mapping) - jobs.keys() or set(mapping.values()) - preparations.keys():
                    raise ValueError('preparation_jobs contains an unknown job or preparation')
                if set(mapping.values()) != set(preparations):
                    raise ValueError('every preparation must be explicitly bound to a local job')
                for job_id, name in mapping.items():
                    agent = jobs[job_id]['inputs'].get('agent')
                    if not agent or agent['sha256'] != preparations[name]['package_sha256']:
                        raise ValueError('existing experiment input differs from preparation; create a new experiment')
                controller_source = controller_identity(experiment)
                if controller_source != manifest.get('controller_source'):
                    raise ValueError('actual controller-source differs from frozen manifest')
                inputs.update(experiment_id=manifest['experiment_id'], job_ids=list(jobs),
                              preparation_jobs=mapping, controller_source=controller_source)
                scope = {'experiment': str(experiment), 'experiment_id': manifest['experiment_id'], 'job_ids': list(jobs)}
                existing = experiment_runs(scope)
                by_job = {job_id: [p.name for p in existing if read_json(p / 'run.json')['job_id'] == job_id] for job_id in jobs}
                requested = spec.get('run_ids')
                if requested is None:
                    if any(len(values) > 1 for values in by_job.values()):
                        raise ValueError('existing experiment has multiple attempts; explicitly freeze run_ids')
                    requested = [p.name for p in existing]
                if not isinstance(requested, list) or len(set(requested)) != len(requested) or set(requested) - {p.name for p in existing}:
                    raise ValueError('run_ids must uniquely identify existing runs in the frozen experiment')
                if any(values and not set(values) & set(requested) for values in by_job.values()):
                    raise ValueError('run_ids must select an existing attempt for every already assigned job')
                inputs.update(run_ids=requested, first_attempt_jobs=[job_id for job_id, values in by_job.items() if not values])
                if any(job['preparation']['status'] != 'ready' for job in manifest['jobs']):
                    raise ValueError('local experiment has unprepared inputs; inspect preparation.jsonl')
                labels = spec.get('run_labels')
                if isinstance(labels, str):
                    labels = read_json(resolve(labels, spec_path.parent))
                if labels is not None:
                    from lab.run import execution_labels
                    execution_labels(manifest, labels)
                inputs.update(experiment=str(experiment), run_labels=labels, replay=spec.get('replay'))
                inputs['bindings'][str(experiment / 'manifest.json')] = file_hash(experiment / 'manifest.json')
            else:
                journals = []
                used_preparations = set()
                for row in spec['hosted']:
                    name = row['id']
                    if Path(name).name != name or name in {'', '.', '..'}:
                        raise ValueError('hosted id must be a directory name')
                    if any(Path(p).name == name for p in journals):
                        raise ValueError('duplicate hosted id')
                    options = {k: v for k, v in row.items() if k not in {'id', 'package', 'preparation'}}
                    if 'preparation' in row:
                        used_preparations.add(row['preparation'])
                    package = (preparations[row['preparation']]['package'] if 'preparation' in row
                               else resolve(row['package'], spec_path.parent))
                    journal = directory / 'hosted' / name
                    prepare_hosted(journal, package, **options)
                    journals.append(str(journal))
                    inputs['bindings'][str(journal / 'inputs.json')] = file_hash(journal / 'inputs.json')
                if used_preparations != set(preparations):
                    raise ValueError('every preparation must be explicitly bound to a hosted input')
                if not journals:
                    raise ValueError('hosted operation requires at least one input')
                inputs['journals'] = journals
            if inputs.get('replay'):
                replay = inputs['replay']
                if set(replay.get('jobs', {})) - set(inputs.get('job_ids', [])):
                    raise ValueError('replay contains an unauthorized job ID')
                if 'defaults' not in replay and 'jobs' not in replay:
                    raise ValueError('replay requires explicit defaults or per-job hosted options')
            inputs['source'] = freeze_source(directory)
            atomic_json(input_path, inputs)
            atomic_json(directory / 'prepare-receipt.json', {'status': 'prepared', 'inputs': str(input_path),
                                                          'prepared_at': time.time()})
            return inputs
        except BaseException as error:
            atomic_json(directory / 'prepare-receipt.json', {'status': 'failed', 'error': error_record(error),
                                                          'observed_at': time.time()})
            raise


def verify_inputs(directory, inputs):
    if inputs['venue'] == 'local':
        if 'run_ids' not in inputs or 'first_attempt_jobs' not in inputs:
            raise ValueError('operation lacks a frozen attempt scope; retain old inputs and use its frozen source or prepare a new operation')
        experiment = Path(inputs['experiment'])
        manifest = read_json(experiment / 'manifest.json')
        if (manifest['experiment_id'] != inputs['experiment_id'] or
                [job['id'] for job in manifest['jobs']] != inputs['job_ids'] or
                controller_identity(experiment) != inputs['controller_source']):
            raise ValueError('frozen experiment scope or controller-source changed')
    for name, expected in inputs.get('bindings', {}).items():
        if file_hash(name) != expected:
            raise ValueError(f'frozen operation binding changed: {name}')
    for name, expected in inputs.get('source', {}).items():
        if file_hash(directory / name) != expected:
            raise ValueError(f'frozen operation source changed: {name}')
    for result in inputs.get('preparations', {}).values():
        if file_hash(result['package']) != result['package_sha256']:
            raise ValueError('prepared package changed')


def worker_owner(directory):
    """Use the current worker, preserving a confirmed birth across partial launch receipts."""
    actual = read_json(directory / 'worker.json') if (directory / 'worker.json').exists() else {}
    launched = read_json(directory / 'worker-launch.json') if (directory / 'worker-launch.json').exists() else {}
    if actual and launched and all(actual.get(k) == launched.get(k) for k in ('pid', 'boot_id', 'process_start')):
        return actual
    return max((actual, launched), key=lambda row: row.get('started_at', 0))


def spawn(directory, name, command, python, *, cwd=None):
    receipt = directory / (name + '-launch.json')
    owner = worker_owner(directory) if name == 'worker' else read_json(receipt) if receipt.exists() else {}
    state = ('finished' if owner.get('phase') in {'completed', 'failed', 'interrupted'} else
             process_state(owner) if owner else 'absent')
    if state == 'alive':
        return owner
    if state == 'unknown':
        raise Blocked(f'{name} process ownership is unknown; retain existing process')
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=str(directory / 'source'))
    argv = [python, '-B', *command]
    with (directory / (name + '.stdout.log')).open('ab') as out, (directory / (name + '.stderr.log')).open('ab') as err:
        process = subprocess.Popen(argv, cwd=cwd or directory, env=env, stdout=out, stderr=err, start_new_session=True)
    result = {**process_identity(process.pid), 'command': argv, 'phase': 'launching', 'started_at': time.time(),
              'stdout': str(directory / (name + '.stdout.log')), 'stderr': str(directory / (name + '.stderr.log'))}
    atomic_json(receipt, result)
    return result


def run(directory):
    directory = Path(directory).resolve(strict=True)
    inputs = read_json(directory / 'inputs.json')
    verify_inputs(directory, inputs)
    launch_gate(directory, inputs)
    with lock(directory / 'dispatch.lock'):
        completed = directory / 'worker.json'
        if completed.exists() and read_json(completed).get('phase') == 'completed':
            return {'status': 'completed', 'operation': str(directory), 'worker': read_json(completed)}
        python = sys.executable
        if inputs['venue'] == 'local':
            manifest = read_json(Path(inputs['experiment']) / 'manifest.json')
            if manifest.get('schema_version') == 3:
                from lab.assets import frozen_host_runtime
                python = frozen_host_runtime(manifest['controller_runtime'])['launcher']
        result = spawn(directory, 'worker', ['-m', 'lab.arc_bench', 'operation', '_work', str(directory)], python)
    return {'status': 'accepted', 'operation': str(directory), 'worker': result}


def register_targets(output, targets):
    output.mkdir(parents=True, exist_ok=True)
    path = output / 'targets.json'
    with lock(output / 'targets.lock'):
        rows = read_json(path)['targets'] if path.exists() else []
        by_run = {row['run_id']: row for row in rows}
        for row in targets:
            prior = by_run.get(row['run_id'])
            if prior is not None and prior != row:
                raise ValueError('monitor run binding changed')
            by_run[row['run_id']] = row
        atomic_json(path, {'targets': list(by_run.values())})
    return path


def experiment_runs(inputs):
    """Read actual runs belonging to the frozen experiment and jobs."""
    experiment = Path(inputs['experiment'])
    manifest = read_json(experiment / 'manifest.json')
    root = (experiment / manifest['runs_root']).resolve()
    runs = []
    for path in sorted(root.iterdir()):
        if not (path / 'run.json').is_file():
            continue
        row = read_json(path / 'run.json')
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
        row = read_json(path / 'run.json')
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


def monitor_complete(output, targets):
    path = output / 'monitor/accepted.json'
    if not path.exists():
        return False
    result = read_json(path)
    accepted = result.get('accepted', {})
    return all(
        accepted.get(rid, {}).get('identity') == identity and
        accepted[rid].get('first_batch') and rid in result.get('done', [])
        for rid, identity in targets.items())


def ensure_monitor(directory, inputs, runs, journals, sessions):
    output = Path(inputs['monitor_output'])
    observers = []
    if inputs['venue'] == 'local' and runs:
        matrix = directory / 'active-matrix.json'
        atomic_json(matrix, {'experiment': inputs['experiment'], 'runs': [str(p) for p in runs]})
        targets = {run.name: {'matrix': str(matrix), 'record': str(run / 'run.json'),
                    'run_id': run.name, 'created_at': read_json(run / 'run.json').get('created_at')} for run in runs}
        observers.append((output, targets, ['-m', 'lab.arc_bench.local_monitor', '--matrix', str(matrix), '--output', str(output)]))
    hosted_targets = []
    identities = {}
    for journal in journals:
        path = Path(journal).resolve()
        state = read_json(path / 'state.json')
        for task, row in state['tasks'].items():
            if not row.get('run_id'):
                continue
            rid = row['run_id']
            target = {'journal': str(path), 'submission_id': state['submission_id'], 'run_id': rid}
            hosted_targets.append(target)
            identity = {**target, 'competition_id': state['competition_id'], 'task_id': task}
            if rid in identities and identities[rid] != identity:
                raise ValueError(f'hosted run identity collision: {rid}')
            identities[rid] = identity
    if hosted_targets:
        hosted_output = output if inputs['venue'] == 'hosted' else output / 'hosted'
        targets_path = register_targets(hosted_output, hosted_targets)
        observers.append((hosted_output, identities, ['-m', 'lab.arc_bench.hosted_monitor', str(hosted_output), '--targets', str(targets_path)]))
    for base, targets, command in observers:
        base.mkdir(parents=True, exist_ok=True)
        with lock(base / 'dispatch.lock'):
            if monitor_complete(base, targets):
                continue
            receipt = base / 'collector-launch.json'
            acceptance = base / 'monitor/accepted.json'
            row = read_json(acceptance) if acceptance.exists() else {}
            launched = read_json(receipt) if receipt.exists() else {}
            # During startup the public receipt may still describe the preceding collector.
            owner = (launched if launched.get('started_at', 0) > row.get('started_at', 0)
                     else row.get('collector') or launched)
            physical = process_state(owner) if owner else 'absent'
            if physical == 'unknown':
                raise Blocked(f'collector ownership unknown: {base}')
            if physical != 'alive':
                previous = row
                added_targets = set(targets) - previous.get('accepted', {}).keys()
                normal_extension = previous.get('collector_status') == 'completed' and bool(added_targets)
                if str(base) in sessions and not normal_extension:
                    raise Blocked(f'collector stopped before handoff completed: {base}; inspect accepted.json and explicitly run operation again')
                env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=str(directory / 'source'))
                argv = [sys.executable, '-B', *command]
                with (base / 'stdout.log').open('ab') as out, (base / 'stderr.log').open('ab') as err:
                    process = subprocess.Popen(argv, cwd=directory, env=env, stdout=out, stderr=err, start_new_session=True)
                atomic_json(receipt, {**process_identity(process.pid), 'phase': 'launching', 'command': argv,
                                     'started_at': time.time(), 'source': str(directory / 'source')})
            elif owner == row.get('collector') and row.get('collector_status') in {'failed', 'interrupted'}:
                raise Blocked(f'collector reported {row["collector_status"]}: {base}')
            sessions.add(str(base))
    return observers

def secret(inputs):
    path = inputs.get('credential_file')
    if not path:
        raise ValueError('hosted launch/replay requires a private credential_file')
    # Plain key files and dotenv assignments are data; never source them as shell code.
    for line in Path(path).read_text().splitlines():
        line = line.strip()
        if line.startswith(('FACTORY26_API_KEY=', 'OPENAI_API_KEY=')):
            return line.split('=', 1)[1].strip().strip('"\'')
    value = Path(path).read_text().strip()
    if value and '\n' not in value and '=' not in value:
        return value
    raise ValueError('private credential file contains no selected API key')


def replay_run(directory, inputs, run):
    state = read_json(run / 'run.json')
    target = directory / 'replays' / run.name
    target.mkdir(parents=True, exist_ok=True)
    receipt = target / 'result.json'
    if receipt.exists():
        previous = read_json(receipt)
        if previous['status'] in {'skipped', 'launched'} or previous.get('worker_id') == read_json(directory / 'worker.json')['worker_id']:
            return previous.get('journal')
    try:
        result_path = run / state.get('result_path', 'workspace/experiment-result.json')
        result = read_json(result_path) if result_path.exists() else {}
        published = run / 'workspace/official-generation/.lab-artifacts/receipt.json'
        if state.get('runner_exit_code') != 0 or result.get('status') != 'completed' or not published.is_file():
            atomic_json(receipt, {'status': 'skipped', 'source': str(run), 'phase': state['phase'], 'result': result})
            return None
        options = {**inputs['replay'].get('defaults', {}), **inputs['replay'].get('jobs', {}).get(state['job_id'], {})}
        expected_task = state['competition'] + '--' + state['task']
        if options.get('competition_id') != state['competition'] or options.get('tasks') != [expected_task]:
            raise ValueError('replay options must target exactly the source competition/task')
        from .package_arc_replay import package
        archive = target / 'application.zip'
        if not archive.exists():
            package([run], archive)
        package_binding = target / 'package.json'
        if package_binding.exists() and read_json(package_binding)['sha256'] != file_hash(archive):
            raise ValueError('replay package changed')
        atomic_json(package_binding, {'source_run': str(run), 'sha256': file_hash(archive)})
        journal = target / 'official'
        prepare_hosted(journal, archive, **options)
        with Controller(journal, secret=secret(inputs)) as controller:
            controller.launch()
        atomic_json(receipt, {'status': 'launched', 'source': str(run), 'journal': str(journal), 'observed_at': time.time()})
        return str(journal)
    except Exception as error:
        journal = target / 'official'
        atomic_json(receipt, {'status': 'needs-review', 'source': str(run), 'journal': str(journal) if journal.exists() else None,
                             'error': error_record(error), 'observed_at': time.time(), 'worker_id': read_json(directory / 'worker.json')['worker_id']})
        return str(journal) if journal.exists() else None


def launch_gate(directory, inputs):
    from .recovery import verify_launch
    prepared = {row['package_sha256']: row.get('receipt') for row in inputs.get('preparations', {}).values()}
    results = []
    if inputs['venue'] == 'local':
        experiment = Path(inputs['experiment'])
        manifest = read_json(experiment / 'manifest.json')
        assigned = {read_json(run / 'run.json')['job_id'] for run in selected_runs(inputs)}
        for job in manifest['jobs']:
            if job['id'] in assigned:
                continue
            agent = job['inputs'].get('agent')
            if agent:
                package = experiment / 'inputs' / agent['id'] / agent['content']
                results.append({'job_id': job['id'], 'result': verify_launch(package, prepared.get(agent['sha256']))})
    else:
        for journal in inputs['journals']:
            frozen = read_json(Path(journal) / 'inputs.json')
            state = read_json(Path(journal) / 'state.json')
            if all(state['tasks'].get(task, {}).get('run_id') and
                   state['tasks'][task].get('phase') in {'started', 'terminal', 'collected'}
                   for task in frozen['tasks']):
                continue
            results.append({'journal': journal, 'result': verify_launch(Path(journal) / frozen['package'],
                            prepared.get(frozen['package_sha256']))})
    atomic_json(directory / 'launch-gates.json', {'observed_at': time.time(), 'results': results})


def handoff(directory, inputs, runs, journals):
    atomic_json(directory / 'handoff.json', {'runs': [str(p) for p in runs], 'journals': journals,
                'monitor_output': inputs['monitor_output'], 'observed_at': time.time()})


def work(directory):
    directory = Path(directory).resolve(strict=True)
    os.umask(0o077)
    with lock(directory / 'worker.lock'):
        inputs = read_json(directory / 'inputs.json')
        verify_inputs(directory, inputs)
        worker = {**process_identity(), 'worker_id': str(time.time_ns()), 'phase': 'running', 'started_at': time.time()}
        atomic_json(directory / 'worker.json', worker)
        sessions = set()
        runs, journals = [], inputs.get('journals', [])[:]
        try:
            launch_gate(directory, inputs)
            launch = None
            if inputs['venue'] == 'local':
                experiment = Path(inputs['experiment'])
                runs = selected_runs(inputs)
                assigned = {read_json(p / 'run.json')['job_id'] for p in runs}
                active_path = experiment / 'active.json'
                active = read_json(active_path) if active_path.exists() else None
                unfinished = assigned != set(inputs['job_ids']) or any(read_json(p / 'run.json')['phase'] not in TERMINAL for p in runs)
                if unfinished and active and active.get('phase') == 'running' and process_state(active) != 'alive':
                    raise Blocked('existing controller ownership unconfirmed; use lab reconcile')
                if assigned != set(inputs['job_ids']) and (not active or active.get('phase') != 'running'):
                    from lab.run import start
                    launch = start(experiment, background=True, run_labels=inputs.get('run_labels'))
                    launch.update(process=process_identity(launch['controller_pid']), observed_at=time.time())
                    atomic_json(directory / 'controller-launch.json', launch)
                atomic_json(directory / 'follower-accepted.json', {'status': 'accepted', 'experiment': str(experiment),
                            'experiment_id': inputs['experiment_id'], 'job_ids': inputs['job_ids'],
                            'replay_authorization': inputs.get('replay'), 'accepted_at': time.time(), 'process': process_identity()})
            else:
                # Preserve and hand over every actual run even if a later launch fails.
                try:
                    for journal in journals:
                        with Controller(journal, secret=secret(inputs)) as controller:
                            controller.launch()
                except BaseException:
                    handoff(directory, inputs, runs, journals)
                    try:
                        ensure_monitor(directory, inputs, runs, journals, sessions)
                    except Exception as monitor_error:
                        worker['handoff_error'] = error_record(monitor_error)
                    raise
            while True:
                if inputs['venue'] == 'local':
                    runs = selected_runs(inputs)
                    if inputs.get('replay'):
                        for run in runs:
                            if read_json(run / 'run.json')['phase'] in TERMINAL:
                                journal = replay_run(directory, inputs, run)
                                if journal and journal not in journals:
                                    journals.append(journal)
                    assigned = {read_json(p / 'run.json')['job_id'] for p in runs}
                    all_terminal = assigned == set(inputs['job_ids']) and all(read_json(p / 'run.json')['phase'] in TERMINAL for p in runs)
                    active = read_json(active_path) if active_path.exists() else None
                    confirmed = active and active.get('phase') == 'running' and process_state(active) == 'alive'
                    if not all_terminal and not confirmed:
                        if not launch or time.time() - launch['observed_at'] > 30:
                            raise Blocked('controller no longer has confirmed ownership while generation is unfinished; inspect controller receipt')
                else:
                    all_terminal = True
                handoff(directory, inputs, runs, journals)
                observers = ensure_monitor(directory, inputs, runs, journals, sessions)
                if all_terminal and observers and all(monitor_complete(base, targets) for base, targets, _ in observers):
                    failures = [read_json(p) for p in (directory / 'replays').glob('*/result.json') if read_json(p)['status'] == 'needs-review']
                    worker.update(phase='failed' if failures else 'completed', finished_at=time.time(), replay_errors=failures)
                    break
                if all_terminal and not observers:
                    raise Blocked('no actual run identity is available for collector handoff')
                time.sleep(5)
        except BaseException as error:
            worker.update(phase='interrupted' if isinstance(error, (KeyboardInterrupt, SystemExit)) else 'failed',
                          finished_at=time.time(), error=error_record(error))
            (directory / 'worker.traceback.log').write_text(traceback.format_exc())
            raise
        finally:
            atomic_json(directory / 'worker.json', worker)
            atomic_json(directory / 'completion.json', worker)
    return worker

def status(directory):
    directory = Path(directory).resolve(strict=True)
    inputs = read_json(directory / 'inputs.json')
    result = {'operation': str(directory), 'venue': inputs['venue'], 'authorization': inputs['authorization'],
              'observed_at': time.time(), 'worker': worker_owner(directory) or None}
    if result['worker']:
        result['worker']['physical_state'] = process_state(result['worker'])
    handoff = read_json(directory / 'handoff.json') if (directory / 'handoff.json').exists() else {'journals': inputs.get('journals', []), 'runs': []}
    result['runs'] = [read_json(Path(p) / 'run.json') for p in handoff.get('runs', [])]
    result['journals'] = [{'directory': p, 'state': read_json(Path(p) / 'state.json')} for p in handoff.get('journals', [])]
    result['observers'] = []
    for path in (Path(inputs['monitor_output']), Path(inputs['monitor_output']) / 'hosted'):
        monitor = path / 'monitor'
        if (monitor / 'accepted.json').exists():
            result['observers'].append({'directory': str(path), 'accepted': read_json(monitor / 'accepted.json'),
                                       'completion': read_json(monitor / 'completion.json') if (monitor / 'completion.json').exists() else None})
    result['follower'] = read_json(directory / 'follower-accepted.json') if (directory / 'follower-accepted.json').exists() else None
    return redact(result)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='action', required=True)
    prepared = commands.add_parser('prepare')
    prepared.add_argument('spec', type=Path)
    prepared.add_argument('--directory', type=Path, required=True)
    for name in ('run', 'status', '_work'):
        commands.add_parser(name).add_argument('directory', type=Path)
    args = parser.parse_args(argv)
    if args.action == 'prepare':
        value = prepare(args.spec, args.directory)
    elif args.action == 'run':
        value = run(args.directory)
    elif args.action == '_work':
        value = work(args.directory)
    else:
        value = status(args.directory)
    print(json.dumps(value, ensure_ascii=False))
    return 0
