"""Prepare a frozen recovery package in an exclusive, offline Linux container."""

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import secrets
import shutil
import sqlite3
import stat
import subprocess
import sys
import time
from zipfile import ZipFile


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    path.chmod(0o600)


def database_facts(path):
    with sqlite3.connect(f'file:{path}?mode=ro', uri=True) as db:
        tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        names = ('provider_sessions', 'agent_instances', 'assignments', 'context_resets',
                 'context_reset_events', 'work_items', 'worktrees')
        facts = {}
        for name in names:
            if name not in tables:
                continue
            rows = db.execute(f'SELECT * FROM {name} ORDER BY 1').fetchall()
            facts[name] = {'columns': [row[1] for row in db.execute(f'PRAGMA table_info({name})')],
                           'rows': len(rows), 'sha256': hashlib.sha256(json.dumps(
                               rows, ensure_ascii=False, default=lambda value: value.hex()).encode()).hexdigest()}
        trees = [row[0] for row in db.execute('SELECT path FROM worktrees ORDER BY path')]
    return facts, trees


def container_prepare(package, evidence):
    """Execute the package's existing prepare boundary and independently read back its effects."""
    workspace = Path('/workspace')
    agent, requirements, output = workspace / 'submission/agent', workspace / 'requirements', workspace / 'template'
    agent.mkdir(parents=True)
    requirements.mkdir()
    evidence.mkdir(parents=True, exist_ok=True)
    receipt = {'package_sha256': digest(package), 'models_started': False, 'provider_resume': 'not attempted',
               'directory_ownership': {name: {'uid': Path(name).stat().st_uid, 'gid': Path(name).stat().st_gid,
                                              'mode': oct(stat.S_IMODE(Path(name).stat().st_mode))}
                                       for name in ('/workspace', '/packages', '/evidence')}}
    with ZipFile(package) as archive:
        for item in archive.infolist():
            path = PurePosixPath(item.filename)
            if path.is_absolute() or '..' in path.parts or '\\' in item.filename or stat.S_ISLNK(item.external_attr >> 16):
                raise ValueError(f'unsafe recovery package member: {item.filename}')
        archive.extractall(agent)
    source = json.loads((agent / 'recovery-source.json').read_text())
    manifest = json.loads((agent / 'package-manifest.json').read_text())
    for name, row in manifest['files'].items():
        if digest(agent / name) != row['sha256']:
            raise ValueError(f'package manifest hash mismatch: {name}')
    run = output / '.factory26' / source['braid_run_id']
    run_prefix = 'template/.factory26/' + source['braid_run_id'] + '/'
    before = evidence / 'before-state'
    before.mkdir()
    expected = {}
    with ZipFile(agent / 'recovery-workspace.zip') as archive:
        for name in ('braid.sqlite3', 'braid.sqlite3-wal', 'braid.sqlite3-shm'):
            member = run_prefix + 'braid-state/' + name
            if member in archive.namelist():
                (before / name).write_bytes(archive.read(member))
        identity_before, trees = database_facts(before / 'braid.sqlite3')
        request_before = json.loads(archive.read(run_prefix + 'braid-request.json'))
        roots = [run_prefix + 'work/application/', run_prefix + 'braid-state/origin.git/']
        roots += [str(PurePosixPath(tree).relative_to('/workspace')) + '/' for tree in trees]
        native_roots = [str(PurePosixPath(binding['native_home']['root']).relative_to('/workspace')) + '/'
                        for binding in request_before.get('bindings', {}).values()]
        if request_before.get('pi', {}).get('home'):
            native_roots.append(str(PurePosixPath(request_before['pi']['home']).relative_to('/workspace')) + '/')
        templates = [str(PurePosixPath(binding['native_template']).relative_to('/workspace')) + '/models.json'
                     for binding in request_before.get('bindings', {}).values()]
        for item in archive.infolist():
            if item.is_dir():
                continue
            name = item.filename
            path = PurePosixPath(name)
            if path.is_absolute() or '..' in path.parts or '\\' in name or not path.parts or path.parts[0] != 'template':
                raise ValueError(f'unsafe workspace member: {name}')
            if name.startswith('template/requirements/') and stat.S_ISLNK(item.external_attr >> 16):
                raise ValueError(f'requirements symlink is not allowed: {name}')
            if name.startswith('template/requirements/'):
                path = requirements / PurePosixPath(name).relative_to('template/requirements')
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(archive.read(item))
            preserve = any(name.startswith(root) for root in roots)
            preserve |= not name.startswith(('template/.factory26/', 'template/.arc/', 'template/requirements/'))
            preserve |= any(name.startswith(root) for root in native_roots) and (
                '/sessions/' in name or PurePosixPath(name).name in {'models.json', 'auth.json'})
            preserve |= name in templates
            preserve |= name.startswith(run_prefix + 'work/tmp/') and '/pi-subagents' in name
            if preserve:
                expected[name] = {'sha256': hashlib.sha256(archive.read(item)).hexdigest(),
                                  'symlink': stat.S_ISLNK(item.external_attr >> 16)}
        # Missing clone metadata requires a caller-selected commit, never DB branch inference.
        members = set(archive.namelist())
        for tree in [str(run / 'work/application'), *trees]:
            relative = str(PurePosixPath(tree).relative_to('/workspace'))
            if not any(name == relative + '/.git' or name.startswith(relative + '/.git/') for name in members):
                key = str(PurePosixPath(tree).relative_to(str(run)))
                if not source.get('git_reconstruction', {}).get(key):
                    raise ValueError(f'clone .git missing without explicit reconstruction: {key}')
    save(evidence / 'preserved-files.json', expected)
    save(evidence / 'database-before.json', identity_before)
    env = dict(os.environ, OPENAI_BASE_URL='http://offline.invalid/v1', OPENAI_API_KEY='', FACTORY26_API_KEY='',
               PYTHONDONTWRITEBYTECODE='1', GIT_OPTIONAL_LOCKS='0')
    for name in ('VISUAL_BASE_URL', 'VISUAL_API_KEY', 'FACTORY26_VISUAL_API_KEY'):
        env.pop(name, None)
    command = [sys.executable, str(agent / 'main.py'), str(requirements), '--output-dir', str(output), '--prepare-only']
    with (evidence / 'stdout.log').open('w') as stdout, (evidence / 'stderr.log').open('w') as stderr:
        result = subprocess.run(command, cwd=agent, env=env, stdout=stdout, stderr=stderr)
    receipt.update(exit_code=result.returncode, command=command, source_binding=source)
    save(evidence / 'execution.json', receipt)
    if result.returncode:
        raise RuntimeError(f'recovery main exited {result.returncode}; stdout/stderr retained')
    allowed_changes = {}
    for flag, filename in (('replace_braid_deepseek_with_glm', 'recovery-model-migration.json'),
                           ('override_native_transport', 'recovery-native-transport.json')):
        if source.get(flag):
            changes = json.loads((run / filename).read_text())
            for row in changes['files']:
                allowed_changes[str(Path(row['path']).relative_to(workspace))] = row
            shutil.copy2(run / filename, evidence / ('package-' + filename))
    mismatches = []
    for name, fact in expected.items():
        path = workspace / name
        try:
            actual = hashlib.sha256(os.readlink(path).encode()).hexdigest() if fact['symlink'] else digest(path)
        except OSError as error:
            actual = f'{type(error).__name__}: {error}'
        change = allowed_changes.get(name)
        expected_hash = fact['sha256']
        if change and change['before_sha256'] == expected_hash:
            expected_hash = change['after_sha256']
        if actual != expected_hash:
            mismatches.append({'path': name, 'expected': fact['sha256'], 'actual': actual})
    identity_after, trees_after = database_facts(run / 'braid-state/braid.sqlite3')
    save(evidence / 'database-after.json', identity_after)
    request_after = json.loads((run / 'braid-request.json').read_text())
    ignored_profile_fields = {'user_instructions'} if source.get('refresh_native_materials') else set()
    recipe = lambda request: {profile['id']: {key: value for key, value in profile.items()
                                             if key not in ignored_profile_fields}
                              for profile in request['profiles']}
    expected_recipe = recipe(request_before)
    if source.get('replace_braid_deepseek_with_glm'):
        migration = json.loads((run / 'recovery-model-migration.json').read_text())['profile_change']
        before_profile = expected_recipe[migration['profile_id']]
        if any(before_profile.get(key) != value for key, value in migration['before'].items()):
            raise ValueError('model migration receipt does not match original profile')
        before_profile.update(migration['after'])
    git = []
    for tree in dict.fromkeys([str(run / 'work/application'), str(run / 'braid-state/origin.git'), *trees_after]):
        facts = {'path': tree}
        for key, arguments in (('head', ['rev-parse', 'HEAD']), ('refs', ['show-ref']),
                               ('dirty', ['status', '--porcelain=v1', '--untracked-files=all'])):
            result = subprocess.run(['git', '-C', tree, *arguments], capture_output=True, text=True, env=env)
            facts[key] = {'exit_code': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}
        git.append(facts)
    save(evidence / 'git.json', git)
    git_errors = [row for row in git if row['head']['exit_code'] or
                  (row['path'] != str(run / 'braid-state/origin.git') and row['dirty']['exit_code'])]
    materials = []
    if source.get('refresh_native_materials'):
        for file in sorted((agent / 'skills').rglob('*')):
            if file.is_file():
                target = run / 'work/skills' / file.relative_to(agent / 'skills')
                materials.append({'path': str(target), 'expected': digest(file), 'actual': digest(target)})
        for profile, binding in request_after.get('bindings', {}).items():
            template = Path(binding['native_template'])
            for home in sorted(Path(binding['native_home']['root']).glob(profile + '-*')):
                for name in ('agents', 'settings.json', 'pi-fff.json'):
                    path = template / name
                    files = [path] if path.is_file() else sorted(file for file in path.rglob('*') if file.is_file())
                    for file in files:
                        target = home / file.relative_to(template)
                        materials.append({'path': str(target), 'expected': digest(file), 'actual': digest(target)})
    save(evidence / 'materials.json', materials)
    for name in ('recovery-preparation.json', 'recovery-attempt.json', 'recovery-git.json',
                 'recovery-native-materials.json', 'materials.json', 'recovery-braid-binary.json',
                 'recovery-resource-environment.json'):
        if (run / name).is_file():
            shutil.copy2(run / name, evidence / ('package-' + name))
    binary = digest(run / 'work/bin/braid')
    receipt.update(verified_files=len(expected), preserved_file_mismatches=mismatches,
                   database_unchanged=identity_before == identity_after, worktree_paths_unchanged=trees == trees_after,
                   profiles_recipe_unchanged=expected_recipe == recipe(request_after),
                   root_profile_unchanged=request_before['root_profile_id'] == request_after['root_profile_id'],
                   material_mismatches=[row for row in materials if row['expected'] != row['actual']],
                   actual_braid_sha256=binary, expected_braid_sha256=source['braid_sha256'], git_errors=git_errors,
                   attempt=json.loads((run / 'recovery-attempt.json').read_text()))
    save(evidence / 'readback.json', receipt)
    if (mismatches or not receipt['database_unchanged'] or not receipt['worktree_paths_unchanged']
            or not receipt['profiles_recipe_unchanged'] or not receipt['root_profile_unchanged'] or git_errors or receipt['material_mismatches'] or binary != source['braid_sha256']):
        raise ValueError('prepared workspace differs from source or authorized materials; readback retained')
    return receipt


def container_stop_basis(source):
    """Read and join preserved source identity and stopping observations without inventing identities."""
    stop = source['stop_binding']
    stop_path = Path(stop['path'])
    if digest(stop_path) != stop['sha256']:
        raise ValueError('恢复执行被阻止：来源停止原件 SHA 不一致')
    raw = json.loads(stop_path.read_text())
    selected = [row for row in raw.get('runs', [raw])
                if (row.get('container_id') or row.get('container')) == stop.get('container_id')]
    if len(selected) != 1 or selected[0] != stop.get('observation'):
        raise ValueError('恢复执行被阻止：来源容器观察与停止原件不一致')
    observed = selected[0]
    state = observed.get('after', observed.get('state', {}))
    source_run_id, container = source['source_run_id'], stop.get('container_id')
    started = state.get('StartedAt')
    daemon = observed.get('daemon_id') or raw.get('daemon_id')
    if (not container or state.get('Running') is not False or state.get('Pid') != 0
            or not started or not stop.get('observed_at')):
        raise ValueError('恢复执行被阻止：缺少确切容器、启动身份、停止状态或观察时间')
    identity_binding = source.get('source_identity_binding')
    identity_sha = None
    context_sha = None
    if identity_binding:
        identity_path = Path(identity_binding['path'])
        if digest(identity_path) != identity_binding['sha256']:
            raise ValueError('恢复执行被阻止：来源 identity 原件 SHA 不一致')
        identity = json.loads(identity_path.read_text())
        source_container = identity.get('source_container', {})
        source_daemon = identity.get('daemon_id')
        if (identity.get('source_run_id') != source_run_id or identity.get('braid_run_id') != source.get('braid_run_id')
                or source_container.get('id') != container or source_container.get('state', {}).get('StartedAt') != started
                or source_container.get('labels', {}).get('io.factory26.run') != source_run_id
                or not source_daemon or identity.get('endpoint', {}).get('daemon_id') != source_daemon):
            raise ValueError('恢复执行被阻止：来源 run/container/StartedAt/daemon identity 不一致')
        context_binding = identity_binding.get('stop_identity')
        if context_binding:
            context_path = Path(context_binding['path'])
            if digest(context_path) != context_binding['sha256']:
                raise ValueError('恢复执行被阻止：停止上下文原件 SHA 不一致')
            context = json.loads(context_path.read_text())
            rows = [row for row in context.get('cases', context.get('runs', []))
                    if (row.get('container') or row.get('container_id')) == container]
            if (len(rows) != 1 or context.get('daemon_id') != source_daemon
                    or rows[0].get('source_run_id') != source_run_id
                    or rows[0].get('state') != observed.get('before')
                    or rows[0].get('state', {}).get('StartedAt') != started):
                raise ValueError('恢复执行被阻止：停止上下文不能精确连接 source identity 与 stop.before')
            if daemon and daemon != context['daemon_id']:
                raise ValueError('恢复执行被阻止：停止原件与上下文 daemon 不一致')
            daemon = context['daemon_id']
            context_sha = context_binding['sha256']
        if daemon != source_daemon:
            raise ValueError('恢复执行被阻止：停止观察缺少与来源相同的 daemon 证据')
        if observed.get('source_run_id') and observed['source_run_id'] != source_run_id:
            raise ValueError('恢复执行被阻止：停止观察的 source run 与来源 identity 不一致')
        identity_sha = identity_binding['sha256']
    elif observed.get('source_run_id') != source_run_id or not daemon:
        raise ValueError('恢复执行被阻止：停止观察未绑定来源 run/container/daemon；caller-confirmed 不能作为独立停止证明')
    return {'kind': 'saved-container-stop-observation', 'source_run_id': source_run_id,
            'container_id': container, 'started_at': started, 'daemon_id': daemon,
            'receipt_sha256': stop['sha256'], 'source_identity_sha256': identity_sha,
            'stop_identity_sha256': context_sha, 'observation_time': stop['observed_at'], 'fresh_observation': False}


def verify_launch(package, preparation_receipt=None):
    """Require observed preparation and source stopping before executing any recovery ZIP.

    Historical caller-confirmed packages remain usable for offline preparation only.
    Ordinary generation packages have no recovery gate.
    """
    package = Path(package).resolve(strict=True)
    with ZipFile(package) as archive:
        members = set(archive.namelist())
        main = archive.read('main.py') if 'main.py' in members else b''
        recovery = bool({'recovery-source.json', 'recovery-workspace.zip'} & members) or b'recovery-source.json' in main
        if not recovery:
            return {'status': 'not-required'}
        if not {'recovery-source.json', 'recovery-workspace.zip', 'package-manifest.json'} <= members:
            raise ValueError('恢复执行被阻止：恢复 ZIP 的来源或 manifest 缺失')
        raw_source = archive.read('recovery-source.json')
        source = json.loads(raw_source)
        manifest = json.loads(archive.read('package-manifest.json'))
        if manifest.get('schema_version') != 1 or manifest.get('files', {}).get('recovery-source.json', {}).get('sha256') != hashlib.sha256(raw_source).hexdigest():
            raise ValueError('恢复执行被阻止：恢复来源与 manifest 不一致')
        frozen_journal = None
        if source.get('journal_binding'):
            binding = source['journal_binding']
            observation = binding.get('frozen_observation')
            if not observation:
                raise ValueError('恢复执行被阻止：legacy 包缺少冻结 journal 观察；原活动 state 不能作为不可变门控')
            payload = {}
            for name in ('inputs', 'state'):
                member = observation.get(name + '_member')
                if not member or member not in members:
                    raise ValueError('恢复执行被阻止：冻结 journal 观察成员缺失')
                raw = archive.read(member)
                sha = hashlib.sha256(raw).hexdigest()
                if sha != binding.get(name + '_sha256') or sha != manifest['files'].get(member, {}).get('sha256'):
                    raise ValueError('恢复执行被阻止：冻结 journal 观察 SHA/manifest 不一致')
                payload[name] = json.loads(raw)
            frozen_journal = payload
    if preparation_receipt is None:
        raise ValueError('恢复执行被阻止：需要绑定最终 ZIP 的实际 prepare receipt')
    receipt_path = Path(preparation_receipt).resolve(strict=True)
    receipt = json.loads(receipt_path.read_text())
    sha = digest(package)
    if receipt.get('status') != 'prepared' or receipt.get('package_sha256') != sha or receipt.get('source_binding') != source:
        raise ValueError('恢复执行被阻止：成功 prepare 回执与实际 ZIP/来源不一致')
    attempt = Path(receipt['attempt_directory'])
    readback_path = Path(receipt['readback'])
    if not readback_path.resolve().is_relative_to(attempt.resolve()) or digest(readback_path) != receipt['readback_sha256']:
        raise ValueError('恢复执行被阻止：独立读回原件身份改变')
    readback = json.loads(readback_path.read_text())
    execution = json.loads((readback_path.parent / 'execution.json').read_text())
    prepared = json.loads((readback_path.parent / 'package-recovery-preparation.json').read_text())
    prepared_attempt = json.loads((readback_path.parent / 'package-recovery-attempt.json').read_text())
    isolation = json.loads((attempt / 'container-isolation.json').read_text())
    if (execution.get('exit_code') != 0 or execution.get('package_sha256') != sha
            or '--prepare-only' not in execution.get('command', [])
            or readback.get('package_sha256') != sha or readback.get('source_binding') != source
            or prepared.get('mode') != 'prepare-only' or prepared.get('models_started') is not False
            or prepared_attempt.get('mode') != 'prepare-only' or prepared_attempt.get('phase') != 'prepared'
            or prepared_attempt.get('source_run_id') != source.get('source_run_id')
            or prepared_attempt.get('braid_run_id') != source.get('braid_run_id')
            or isolation.get('Id') != receipt.get('container_id') or isolation.get('Image') != receipt.get('image_id')
            or isolation.get('HostConfig', {}).get('NetworkMode') != 'none' or isolation.get('Mounts')
            or readback.get('actual_braid_sha256') != source.get('braid_sha256')):
        raise ValueError('恢复执行被阻止：实际 prepare 命令、隔离环境或二进制读回不匹配')
    before = json.loads((readback_path.parent / 'database-before.json').read_text())
    after = json.loads((readback_path.parent / 'database-after.json').read_text())
    if before != after or readback.get('preserved_file_mismatches') or readback.get('material_mismatches'):
        raise ValueError('恢复执行被阻止：来源身份、保留文件或材料读回有差异')
    source_run_id = source.get('source_run_id')
    if not source_run_id:
        raise ValueError('恢复执行被阻止：来源 run identity 缺失')
    journal = source.get('journal_binding')
    stop = source.get('stop_binding')
    if journal:
        inputs, state = frozen_journal['inputs'], frozen_journal['state']
        task = journal['task']
        observed = state['tasks'][task]
        original = journal.get('source_package_verification', {})
        manifest_sha = hashlib.sha256(json.dumps(inputs.get('package_manifest'), sort_keys=True).encode()).hexdigest()
        if (inputs.get('venue') != 'hosted' or state.get('venue') != 'hosted'
                or task not in inputs.get('tasks', []) or journal.get('run_id') != source_run_id
                or state.get('pending') or observed.get('run_id') != source_run_id
                or observed.get('remote_status') not in {'PASSED', 'FAILED', 'CANCELLED'}
                or observed.get('remote_status') != journal.get('terminal_status')
                or not state.get('submission_id') or state['submission_id'] != journal.get('submission_id')
                or inputs.get('package_sha256') != journal.get('package_sha256')
                or state.get('package_sha256') != journal.get('package_sha256')
                or original.get('sha256') != journal.get('package_sha256')
                or original.get('manifest_sha256') != manifest_sha):
            raise ValueError('恢复执行被阻止：冻结来源 run/终态/原包的 journal 绑定未确认')
        basis = {'kind': 'saved-hosted-terminal-journal', 'source_run_id': source_run_id,
                 'submission_id': state['submission_id'], 'state_sha256': journal['state_sha256'],
                 'observation_time': observed.get('observed_at'), 'fresh_observation': False}
    elif stop:
        basis = container_stop_basis(source)
    else:
        raise ValueError('恢复执行被阻止：来源只有 caller-confirmed，缺少可核对的停止原件')
    return {'status': 'verified', 'package_sha256': sha, 'source_run_id': source_run_id,
            'preparation_receipt': str(receipt_path), 'stop_basis': basis}


def prepare(spec, directory):
    """Return a private prepared receipt; failed attempts retain their exclusive container and files.

    spec selects package OR recovery (the existing packager's option names), docker_image,
    optional frozen docker_endpoint or docker_context, and uid/gid. No model key is injected.
    """
    from lab.arc_bench.docker_workspace import docker, inspect, error_text
    from lab.docker_endpoint import freeze
    import fcntl

    directory = Path(directory).resolve()
    root = Path(__file__).resolve().parents[2]
    if directory.is_relative_to(root) and subprocess.run(
            ['git', 'check-ignore', '-q', '--', str(directory)], cwd=root).returncode:
        raise ValueError('private recovery artifacts must be Git ignored or outside the repository')
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    directory.chmod(0o700)
    with (directory / '.prepare.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        return _prepare(spec, directory, docker, inspect, error_text, freeze)


def complete_prepared_transport(directory, export_receipt, validation_receipt):
    """Complete only a failed workspace transfer from a saved, stopped prepare container.

    The export and its existing extraction must belong to the same attempt. This
    boundary makes no Docker calls and never executes the package's main again.
    """
    import fcntl
    import tarfile
    from .workspace_archive import output_inventory

    directory = Path(directory).resolve(strict=True)
    export_path = Path(export_receipt).resolve(strict=True)
    validation_path = Path(validation_receipt).resolve(strict=True)
    with (directory / '.prepare.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        final = directory / 'receipt.json'
        original = json.loads(final.read_text())
        if original.get('status') == 'prepared':
            binding = original.get('transport_reentry', {})
            if (binding.get('export_receipt_sha256') != digest(export_path)
                    or binding.get('validation_receipt_sha256') != digest(validation_path)):
                raise ValueError('prepared transport is already bound to different export evidence')
            verify_launch(original['package'], final)
            return original
        attempt = Path(original['attempt_directory']).resolve(strict=True)
        spec = json.loads((directory / 'spec.json').read_text())
        spec_hash = hashlib.sha256(json.dumps(spec, sort_keys=True).encode()).hexdigest()
        if (original.get('status') != 'failed' or original.get('spec_sha256') != spec_hash
                or attempt.parent != directory or json.loads((attempt / 'receipt.json').read_text()) != original):
            raise ValueError('transport reentry requires the unchanged failed attempt and specification')
        for name, expected in json.loads((directory / 'input-hashes.json').read_text()).items():
            if digest(name) != expected:
                raise ValueError(f'recovery input content changed: {name}')
        package = Path(original['package']).resolve(strict=True)
        if (package != attempt / 'agent.zip' or digest(package) != original['package_sha256']
                or digest(attempt / 'recovery-runner.py') != original['runner_sha256']):
            raise ValueError('failed attempt package or runner identity changed')
        isolation = json.loads((attempt / 'container-isolation.json').read_text())
        stopped = json.loads((attempt / 'container-final.json').read_text())
        environment = json.loads((directory / 'environment.json').read_text())
        state = stopped.get('State', {})
        if (any(row.get('Id') != original['container_id'] or row.get('Image') != original['image_id']
                or row.get('HostConfig', {}).get('NetworkMode') != 'none' or row.get('Mounts')
                for row in (isolation, stopped))
                or environment.get('endpoint') != original['docker_endpoint']
                or environment.get('image_id') != original['image_id']
                or state != original.get('container_final_state')
                or state.get('Running') is not False or state.get('Paused') is not False
                or state.get('Restarting') is not False or state.get('Pid') != 0
                or not state.get('FinishedAt') or state.get('StartedAt') != isolation['State'].get('StartedAt')):
            raise ValueError('saved prepare isolation or stopped container identity differs')
        export = json.loads(export_path.read_text())
        validation = json.loads(validation_path.read_text())
        export_attempt = Path(export['source_attempt'])
        if not export_attempt.is_absolute():
            export_attempt = export_path.parent.parent / export_attempt
        archive = Path(validation['archive']).resolve(strict=True)
        workspace = Path(validation['destination']).resolve(strict=True)
        if (export_attempt.resolve() != attempt or export.get('container_id') != original['container_id']
                or export.get('image_id') != original['image_id'] or export.get('package_sha256') != original['package_sha256']
                or export.get('exit_code') != 0 or export.get('container_restarted') is not False
                or export.get('models_started') is not False or validation.get('models_started') is not False
                or validation.get('container_restarted') is not False or validation.get('mismatches') != []
                or export.get('started_at', 0) < original.get('finished_at', 0)
                or export.get('finished_at', 0) < export.get('started_at', 0)
                or digest(archive) != export.get('sha256') or export.get('sha256') != validation.get('archive_sha256')
                or archive.stat().st_size != export.get('bytes')):
            raise ValueError('completed workspace export does not match the stopped failed attempt')
        readback_path = attempt / 'readback/readback.json'
        observed = json.loads(readback_path.read_text())
        execution = json.loads((readback_path.parent / 'execution.json').read_text())
        if (execution.get('exit_code') != 0 or execution.get('models_started') is not False
                or observed.get('verified_files') != validation.get('preserved_files')
                or any(observed.get(name) is not True for name in (
                    'database_unchanged', 'worktree_paths_unchanged', 'profiles_recipe_unchanged', 'root_profile_unchanged'))
                or any(observed.get(name) for name in ('preserved_file_mismatches', 'material_mismatches', 'git_errors'))):
            raise ValueError('the original offline prepare or independent readback did not succeed')
        # Bind every extracted file, including generated preparation metadata, to
        # the complete archive; the preserved-file subset alone cannot do this.
        inventory = output_inventory(workspace)
        actual = {row['path']: row for row in inventory['entries']}
        names = set()
        with tarfile.open(archive) as stream:
            for member in stream:
                path = PurePosixPath(member.name)
                if path.is_absolute() or '..' in path.parts or '\\' in member.name:
                    raise ValueError(f'unsafe exported workspace path: {member.name}')
                name = str(path)
                if name == '.' and member.isdir():
                    continue
                if name in names:
                    raise ValueError(f'duplicate exported workspace path: {name}')
                names.add(name)
                expected = {'path': name}
                if member.isdir():
                    expected['type'] = 'directory'
                elif member.issym():
                    expected.update(type='link', target=member.linkname)
                elif member.isfile() or member.islnk():
                    with stream.extractfile(member) as data:
                        expected.update(type='file', sha256=hashlib.file_digest(data, 'sha256').hexdigest(),
                                        executable=bool(member.mode & 0o111))
                else:
                    raise ValueError(f'unsupported exported workspace member: {name}')
                if actual.get(name) != expected:
                    raise ValueError(f'extracted workspace differs from completed export: {name}')
        if names != actual.keys():
            raise ValueError('extracted workspace contains files outside the completed export')
        run = workspace / '.factory26' / original['source_binding']['braid_run_id']
        if digest(run / 'work/bin/braid') != original['source_binding']['braid_sha256']:
            raise ValueError('exported prepared workspace binary differs from frozen source')
        reentry = attempt / ('transport-reentry-' + secrets.token_hex(8))
        reentry.mkdir(mode=0o700)
        failed_copy = reentry / 'failed-receipt.json'
        shutil.copy2(final, failed_copy)
        candidate = {**original, 'status': 'prepared', 'receipt': str(final), 'readback': str(readback_path),
                     'readback_sha256': digest(readback_path), 'prepared_workspace': str(workspace),
                     'docker_exec_exit_code': execution['exit_code'], 'finished_at': time.time(),
                     'prepared_identity': {'container_id': original['container_id'], 'image_id': original['image_id'],
                                           'endpoint': original['docker_endpoint'], 'attempt': observed['attempt']},
                     'transport_reentry': {'failed_receipt': str(failed_copy), 'failed_receipt_sha256': digest(failed_copy),
                         'export_receipt': str(export_path), 'export_receipt_sha256': digest(export_path),
                         'validation_receipt': str(validation_path), 'validation_receipt_sha256': digest(validation_path),
                         'archive': str(archive), 'archive_sha256': digest(archive),
                         'workspace_inventory_sha256': inventory['sha256'], 'workspace_entries': len(actual),
                         'models_started': False, 'container_restarted': False, 'main_reexecuted': False}}
        candidate.pop('error', None)
        candidate_path = reentry / 'receipt.json'
        save(candidate_path, candidate)
        candidate['launch_verification'] = verify_launch(package, candidate_path)
        save(candidate_path, candidate)
        # The original attempt receipt and incomplete workspace remain untouched.
        # Publish only after the existing launch gate accepts the derived receipt.
        pending = directory / 'receipt.transport-completed.json'
        save(pending, candidate)
        pending.replace(final)
        return candidate


def _prepare(spec, directory, docker, inspect, error_text, freeze):
    spec = json.loads(json.dumps(spec))
    final = directory / 'receipt.json'
    spec_hash = hashlib.sha256(json.dumps(spec, sort_keys=True).encode()).hexdigest()
    frozen = directory / 'spec.json'
    if frozen.exists() and json.loads(frozen.read_text()) != spec:
        raise ValueError('recovery prepare directory is already bound to a different specification')
    save(frozen, spec)
    if final.exists():
        receipt = json.loads(final.read_text())
        if receipt.get('spec_sha256') != spec_hash:
            raise ValueError('saved preparation receipt specification differs')
        if receipt['status'] == 'prepared':
            if digest(receipt['package']) != receipt['package_sha256'] or digest(receipt['readback']) != receipt['readback_sha256']:
                raise ValueError('completed preparation package/readback changed')
            return receipt
    file_fields = {'workspace', 'base_package', 'source_package', 'stop_receipt', 'source_identity', 'stop_identity', 'git_reconstruction',
                   'braid', 'braid_source', 'braid_source_identity'}
    references = [spec['package']] if spec.get('package') else [value for key, value in spec.get('recovery', {}).items()
                                                              if key in file_fields and value]
    for name in ('inputs.json', 'state.json'):
        if spec.get('recovery', {}).get('journal'):
            references.append(str(Path(spec['recovery']['journal']) / name))
    inputs = {str(Path(path).resolve(strict=True)): digest(path) for path in references}
    input_path = directory / 'input-hashes.json'
    if input_path.exists() and json.loads(input_path.read_text()) != inputs:
        raise ValueError('recovery input content changed; create a new operation directory')
    save(input_path, inputs)
    attempt = directory / ('attempt-' + secrets.token_hex(8))
    attempt.mkdir(mode=0o700)
    receipt = {'status': 'preparing', 'spec_sha256': spec_hash, 'started_at': time.time(), 'attempt_directory': str(attempt),
               'receipt': str(final), 'provider_resume': 'not attempted'}
    identifier = None
    endpoint = None
    try:
        if bool(spec.get('package')) == bool(spec.get('recovery')):
            raise ValueError('provide exactly one package or recovery specification')
        package = attempt / 'agent.zip'
        if spec.get('package'):
            shutil.copy2(Path(spec['package']).resolve(strict=True), package)
        else:
            args = [sys.executable, str(Path(__file__).resolve().parents[2] / 'scripts/package_completed_recovery.py'),
                    '--output', str(package), '--evidence-dir', str(attempt / 'packaging')]
            allowed = {'journal', 'task', 'source_run_id', 'workspace', 'workspace_sha256', 'base_package', 'source_package',
                       'stop_receipt', 'stop_container', 'source_identity', 'stop_identity', 'git_reconstruction', 'braid', 'braid_source', 'braid_source_identity',
                       'continue_generation', 'replace_braid_deepseek_with_glm', 'with_official_signal_evidence',
                       'override_native_transport', 'refresh_native_materials'}
            for key, value in spec['recovery'].items():
                if key not in allowed:
                    raise ValueError(f'unknown recovery option: {key}')
                if value is not None and value is not False:
                    args.append('--' + key.replace('_', '-'))
                    if value is not True:
                        args.append(str(value))
            with (attempt / 'packager.stdout.log').open('w') as stdout, (attempt / 'packager.stderr.log').open('w') as stderr:
                result = subprocess.run(args, stdout=stdout, stderr=stderr)
            if result.returncode:
                raise RuntimeError(f'recovery packager exited {result.returncode}; raw logs retained')
        package.chmod(0o600)
        runner = attempt / 'recovery-runner.py'
        shutil.copy2(Path(__file__).resolve(), runner)
        runner.chmod(0o600)
        receipt['runner_sha256'] = digest(runner)
        with ZipFile(package) as archive:
            source = json.loads(archive.read('recovery-source.json'))
        receipt.update(package=str(package), package_sha256=digest(package), source_binding=source,
                       source_binding_sha256=hashlib.sha256(json.dumps(source, sort_keys=True).encode()).hexdigest())
        environment_path = directory / 'environment.json'
        if environment_path.exists():
            frozen_environment = json.loads(environment_path.read_text())
            endpoint = frozen_environment['endpoint']
            image_selector = frozen_environment['image_id']
            uid, gid = frozen_environment['uid'], frozen_environment['gid']
        else:
            endpoint = spec.get('docker_endpoint') or freeze(spec.get('docker_context'))
            image_selector = spec['docker_image']
            uid, gid = int(spec.get('uid', os.getuid())), int(spec.get('gid', os.getgid()))
        receipt['docker_endpoint'] = endpoint
        image = json.loads(docker(endpoint, ['image', 'inspect', image_selector], capture_output=True, text=True).stdout)[0]
        if image.get('Os') != 'linux':
            raise ValueError('recovery preparation requires a Linux image')
        if uid < 0 or gid < 0:
            raise ValueError('execution UID/GID must be nonnegative')
        save(environment_path, {'endpoint': endpoint, 'image_id': image['Id'], 'uid': uid, 'gid': gid})
        name = 'factory26-recovery-' + secrets.token_hex(12)
        receipt.update(container_name=name, image_id=image['Id'], uid=uid, gid=gid)
        save(attempt / 'receipt.json', receipt)
        identifier = docker(endpoint, ['create', '--name', name, '--network', 'none', '--user', '0',
                                      '--label', 'io.factory26.recovery=' + name, '--entrypoint', 'python3', image['Id'],
                                      '-c', 'import time; time.sleep(2147483647)'], capture_output=True, text=True).stdout.strip()
        receipt['container_id'] = identifier
        save(attempt / 'receipt.json', receipt)
        docker(endpoint, ['start', identifier], capture_output=True)
        isolation = inspect(endpoint, 'container', identifier)
        save(attempt / 'container-isolation.json', isolation)
        if isolation['HostConfig']['NetworkMode'] != 'none' or isolation.get('Mounts'):
            raise ValueError('prepare container isolation differs from exclusive offline contract')
        docker(endpoint, ['exec', identifier, 'mkdir', '-p', '/workspace', '/packages', '/evidence'], capture_output=True)
        docker(endpoint, ['cp', str(package), identifier + ':/packages/agent.zip'], capture_output=True, timeout=600)
        docker(endpoint, ['cp', str(runner), identifier + ':/packages/recovery.py'], capture_output=True)
        docker(endpoint, ['exec', identifier, 'chown', '-R', f'{uid}:{gid}', '/workspace', '/packages', '/evidence'], capture_output=True)
        with (attempt / 'docker.stdout.log').open('wb') as stdout, (attempt / 'docker.stderr.log').open('wb') as stderr:
            result = docker(endpoint, ['exec', '--user', f'{uid}:{gid}', identifier, 'python3', '/packages/recovery.py',
                                      '--container-prepare', '/packages/agent.zip', '/evidence'], stdout=stdout, stderr=stderr, timeout=1800)
        receipt['docker_exec_exit_code'] = result.returncode
        docker(endpoint, ['cp', identifier + ':/evidence/.', str(attempt / 'readback')], capture_output=True, timeout=600)
        readback = attempt / 'readback/readback.json'
        observed = json.loads(readback.read_text())
        prepared_workspace = attempt / 'prepared-workspace'
        archive = attempt / 'prepared-workspace.tar.gz'
        export_stderr = attempt / 'prepared-workspace-export.stderr.log'
        export_command = ['exec', identifier, 'tar', '--numeric-owner', '-czf', '-',
                          '-C', '/workspace/template', '.']
        export = {'archive': str(archive), 'stderr': str(export_stderr),
                  'command': export_command, 'started_at': time.time()}
        receipt['prepared_workspace_export'] = export
        try:
            with archive.open('xb') as stdout, export_stderr.open('xb') as stderr:
                result = docker(endpoint, export_command, stdout=stdout, stderr=stderr, timeout=600)
            export['exit_code'] = result.returncode
        except BaseException as error:
            export.update(exit_code=getattr(error, 'returncode', None),
                          timed_out=isinstance(error, subprocess.TimeoutExpired), error=error_text(error))
            raise
        finally:
            export['finished_at'] = time.time()
            if archive.exists():
                export.update(bytes=archive.stat().st_size, sha256=digest(archive))
        from .workspace_archive import extract_output
        extract_output(archive, prepared_workspace)
        receipt['prepared_workspace'] = str(prepared_workspace)
        if observed['package_sha256'] != receipt['package_sha256']:
            raise ValueError('container package differs from frozen host package')
        receipt.update(status='prepared', readback=str(readback), readback_sha256=digest(readback),
                       prepared_identity={'container_id': identifier, 'image_id': image['Id'],
                                          'endpoint': endpoint, 'attempt': observed['attempt']})
    except BaseException as error:
        receipt.update(status='failed', error=error_text(error), docker_exec_exit_code=getattr(error, 'returncode', None))
        if identifier and endpoint:
            try:
                docker(endpoint, ['cp', identifier + ':/evidence/.', str(attempt / 'readback')], capture_output=True, timeout=600)
            except Exception as copy_error:
                receipt['evidence_copy_error'] = error_text(copy_error)
        raise
    finally:
        if identifier and endpoint:
            try:
                docker(endpoint, ['stop', '--time', '1', identifier], capture_output=True, timeout=20)
                observed = inspect(endpoint, 'container', identifier)
                save(attempt / 'container-final.json', observed)
                receipt['container_final_state'] = observed['State']
            except Exception as stop_error:
                receipt['container_stop_error'] = error_text(stop_error)
        receipt['finished_at'] = time.time()
        save(attempt / 'receipt.json', receipt)
        save(final, receipt)
    return receipt


if __name__ == '__main__':
    if len(sys.argv) == 5 and sys.argv[1] == '--complete-prepared-transport':
        receipt = complete_prepared_transport(*sys.argv[2:])
        print(json.dumps({key: receipt[key] for key in ('status', 'receipt', 'package_sha256', 'container_id')}, ensure_ascii=False))
    elif len(sys.argv) == 4 and sys.argv[1] == '--container-prepare':
        try:
            container_prepare(Path(sys.argv[2]), Path(sys.argv[3]))
        except BaseException as error:
            import traceback
            Path(sys.argv[3]).mkdir(parents=True, exist_ok=True)
            Path(sys.argv[3], 'operation-error.txt').write_text(traceback.format_exc())
            raise
    else:
        raise SystemExit('Use lab.arc_bench.recovery.prepare(spec, directory) from the operation entrypoint')
