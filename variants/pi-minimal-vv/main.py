"""Incremental native Pi entry using the caller's frozen model connection."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import shutil
import sys
import uuid
import subprocess
import traceback

try:
    from raw_otlp import LogExporter
    telemetry_import_error = None
except Exception as error:
    LogExporter = None
    telemetry_import_error = error
from agent_support import cleanup_workspace, stop
from e2e_runtime import require_e2e_addon

ROOT = Path(__file__).resolve().parent
SKILLS = ('svc-task-packet', 'svc-specs', 'svc-verification', 'e2e', 'agent-browser', 'hyperformula', 'handsontable', 'better-auth-best-practices',
          'organization-best-practices', 'fixing-accessibility', 'context7-docs')


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def tool_environment():
    """Use the existing private tool input; explicit execution values take precedence."""
    names = ('CONTEXT7_API_KEY', 'EXA_API_KEY')
    private = ROOT/'.private/tool-env.json'
    values = json.loads(private.read_text()) if private.is_file() else {}
    if not isinstance(values, dict) or (private.is_file() and set(values) != set(names)) or any(
            not isinstance(value, str) or not value for value in values.values()):
        raise ValueError('Private tool input needs the two known non-empty credential variables')
    result = {name: os.environ.get(name, values.get(name)) for name in names}
    if any(not isinstance(value, str) or not value for value in result.values()):
        raise ValueError('CONTEXT7_API_KEY and EXA_API_KEY must be supplied through the private tool input')
    return result


def run(requirements, output, model='glm-5.3-flash'):
    os.environ['FACTORY26_ENTRY_PHASE'] = 'setup'
    if not (requirements/'requirements.yaml').is_file():
        raise ValueError('requirements.yaml is missing')
    if sys.platform != 'linux':
        raise RuntimeError('This frozen Harness requires the official Linux runner')
    runtime = ROOT/'runtime'
    search_extensions = (runtime/'node_modules/@ff-labs/pi-fff/src/index.ts',
                         runtime/'node_modules/@upstash/context7-pi/extensions/context7.ts',
                         ROOT/'extensions/exa.ts')
    for extension in search_extensions:
        if not extension.is_file():
            raise FileNotFoundError(f'Native search extension is missing: {extension}')
    tool_keys = tool_environment()
    browser = runtime/'bin/browser-exec'
    if not browser.is_file():
        browser = runtime/'bin/chromium'
    for relative in json.loads((ROOT/'runtime-executables.json').read_text()):
        path = ROOT/relative
        mode = path.stat().st_mode
        if mode & 0o111 != 0o111:
            path.chmod(mode | 0o111)
    # Official ZIP extraction may drop executable bits; restore them before addon validation.
    require_e2e_addon(runtime/'e2e')
    output.mkdir(parents=True, exist_ok=True)
    # The baseline carries prior native state; every new task owns a fresh run.
    resume_run_id = os.environ.get('FACTORY26_PI_RESUME_RUN_ID')
    run_id = resume_run_id or uuid.uuid4().hex
    if len(run_id) != 32 or any(c not in '0123456789abcdef' for c in run_id):
        raise ValueError('FACTORY26_PI_RESUME_RUN_ID must be a native run UUID')
    evidence = output/'.factory26/pi-minimal-vv/runs'/run_id
    if resume_run_id and (evidence/'stages.json').exists():
        raise ValueError('This retained run uses the removed two-session coordinator; resume requires its frozen Harness, not this single-session entry')
    if resume_run_id:
        previous_identity = json.loads((evidence/'identity.json').read_text())
        if previous_identity['variant'] != 'pi-minimal-vv' or previous_identity['main_model'] != model:
            raise ValueError('Native resume identity does not match this variant/model')
        if previous_identity.get('phase') is not None:
            raise ValueError('A staged native identity cannot resume as a single-session run')
        if not (evidence/'session.jsonl').is_file():
            raise ValueError('Native resume session is missing')
        previous_result = evidence/'result.json'
        if previous_result.exists():
            result = json.loads(previous_result.read_text())
            if result.get('exit_code') == 0 and result.get('terminal') == 'stop':
                raise ValueError('This native run already completed; resume does not start another generation')
            shutil.copy2(previous_result, evidence/('result-before-recovery-'+uuid.uuid4().hex+'.json'))
    else:
        evidence.mkdir(parents=True, exist_ok=False)
    os.environ['FACTORY26_ENTRY_EVIDENCE'] = str(evidence)
    saved_home = evidence/'home'
    saved_home.mkdir(exist_ok=True)
    home = saved_home
    native = (home/'.pi/agent').resolve()
    native.mkdir(parents=True, exist_ok=True)
    main_provider, advisor_model = 'factory26', 'factory26/kimi-k2.7-code'
    key = os.environ.get('OPENAI_API_KEY') or os.environ.get('FACTORY26_API_KEY')
    base = os.environ.get('OPENAI_BASE_URL') or os.environ.get('FACTORY26_BASE_URL')
    if not key or not base:
        raise ValueError('Caller must inject the frozen model API key and endpoint')
    models = json.loads((ROOT/'models.json').read_text())
    models['providers']['factory26']['baseUrl'] = base
    save(native/'models.json', models)
    roles = native/'agents'
    roles.mkdir(exist_ok=True)
    for source in (ROOT/'agents').glob('*.md'):
        text = source.read_text().replace('@RUNTIME@', str(runtime)).replace('@SKILLS@', str(ROOT/'skills')).replace('@PACKAGE@', str(ROOT))
        text = text.replace('factory26/kimi-k2.7-code', advisor_model)
        (roles/source.name).write_text(text)
    save(native/'pi-fff.json', {'mode': 'tools-only'})
    save(native/'settings.json', {'packages': [], 'subagents': {'disableBuiltins': True},
                                 'compaction': {'enabled': True, 'thresholdTokens': 245000}})
    subagent_config = native/'extensions/subagent'
    subagent_config.mkdir(parents=True, exist_ok=True)
    save(subagent_config/'config.json', {'toolDescriptionMode': 'compact'})
    (home/'.config').mkdir(exist_ok=True)
    env = {**os.environ, **tool_keys}
    for name in list(env):
        if name.startswith('BRAID_') or name == 'FACTORY26_MODEL_BUDGET_PATH':
            env.pop(name)
    if key:
        env['FACTORY26_API_KEY'] = key
    env.update(HOME=str(home), XDG_CONFIG_HOME=str(home/'.config'), PI_CODING_AGENT_DIR=str(native),
               PI_OFFLINE='1', PI_FFF_MODE='tools-only', FACTORY26_SUBAGENT_CATALOG='1',
               PI_CAPABILITY_EVIDENCE_DIR=str(evidence/'capabilities'),
               FACTORY26_PI_TIMING_FILE=str(evidence/'pi-timing.jsonl'),
               PATH=str(runtime/'bin')+':/usr/local/bin:/usr/bin:/bin',
               NODE_PATH=str(runtime/'node_modules'), PI_SUBAGENT_PI_BINARY=str(runtime/'bin/pi'),
               MCPORTER_CONFIG=str(ROOT/'mcporter.json'),
               AGENT_BROWSER_EXECUTABLE_PATH=str(browser),
               AGENT_BROWSER_SOCKET_DIR=str(evidence/'browser'),
               BROWSER_EXECUTABLE_PATH=str(browser),
               BROWSER_CHECK_NODE_MODULES=str(runtime/'node_modules'))
    temporary = evidence/'tmp'
    temporary.mkdir(exist_ok=True)
    alias = Path('/tmp')/('f26-pivv-'+uuid.uuid4().hex[:12])
    alias.symlink_to(temporary, target_is_directory=True)
    env.update(TMPDIR=str(alias), MCPORTER_DAEMON_DIR=str(alias/'mcporter'),
               FACTORY26_TOOL_NODE=str(runtime/'bin/node'), E2E_RUNTIME=str(runtime/'e2e'),
               E2E_NODE_MODULES=str(runtime/'e2e/node_modules'),
               E2E_CONFIG_TEMPLATE=str(ROOT/'tools/e2e.config.ts'), E2E_MODEL='glm-5.3-flash',
               E2E_OUTPUT_DIR=str(evidence/'e2e'),
               E2E_BASE_URL=base, E2E_API_KEY=key, E2E_TELEMETRY_DISABLED='1')
    env['FACTORY26_BROWSER_CACHE_DIR'] = str(evidence/'browser-cache')
    if not env.get('PLAYWRIGHT_BROWSERS_PATH'):
        env['PLAYWRIGHT_BROWSERS_PATH'] = env['FACTORY26_BROWSER_CACHE_DIR']
    e2e_project = evidence/'e2e-project'
    e2e_project.mkdir(exist_ok=bool(resume_run_id))
    shutil.copy2(ROOT/'tools/e2e.config.ts', e2e_project/'e2e.config.ts')
    if not (e2e_project/'node_modules').is_symlink():
        (e2e_project/'node_modules').symlink_to(runtime/'e2e/node_modules', target_is_directory=True)
    env['E2E_PROJECT_DIR'] = str(e2e_project)
    mcp = json.loads((ROOT/'mcporter.json').read_text())
    (ROOT/'tools/e2e-cli').chmod(0o755)
    mcp['mcpServers'].pop('e2e', None)
    save(evidence/'mcporter.json', mcp)
    env['MCPORTER_CONFIG'] = str(evidence/'mcporter.json')
    owned = evidence/'owned-e2e'
    owned.mkdir(exist_ok=True, mode=0o700)
    owned.chmod(0o700)
    recipe_file = evidence/'owned-e2e-recipe.json'
    # Only actual E2E child inputs belong to its identity; shell exports are not inputs.
    names = ('HOME', 'XDG_CONFIG_HOME', 'PATH', 'NODE_PATH', 'TMPDIR', 'MCPORTER_DAEMON_DIR',
             'FACTORY26_TOOL_NODE', 'E2E_RUNTIME', 'E2E_NODE_MODULES', 'FACTORY26_BROWSER_CACHE_DIR',
             'PLAYWRIGHT_BROWSERS_PATH',
             'BROWSER_EXECUTABLE_PATH', 'BROWSER_CHECK_NODE_MODULES', 'E2E_BASE_URL',
             'E2E_MODEL', 'E2E_TELEMETRY_DISABLED')
    recipe = {'stateDirectory': str(owned), 'environment': {name: env[name] for name in names},
              'credentialVariable': 'FACTORY26_API_KEY',
              'credentialFingerprint': hashlib.sha256(key.encode()).hexdigest(),
              'configTemplate': str(ROOT/'tools/e2e.config.ts'),
              'nodeModules': str(runtime/'e2e/node_modules'),
              'serverCommand': str(ROOT/'tools/e2e-cli'),
              'serverFingerprint': hashlib.sha256((ROOT/'tools/e2e-cli').read_bytes()).hexdigest(),
              'runtimeSource': str(runtime/'runtime-source.json'),
              'runtimeFingerprint': hashlib.sha256((runtime/'runtime-source.json').read_bytes()).hexdigest(),
              'mcporterCommand': str(runtime/'bin/mcporter')}
    if recipe_file.exists():
        previous = json.loads(recipe_file.read_text())
        if previous != recipe:
            # Recovery already cleaned live services; retained handles are not browser checkpoints.
            save(evidence/('owned-e2e-recipe-before-recovery-'+uuid.uuid4().hex+'.json'), previous)
    save(recipe_file, recipe)
    recipe_file.chmod(0o600)
    env['FACTORY26_E2E_RECIPE'] = str(recipe_file)
    instruction = (ROOT/'instructions.md').read_text().replace('@REQUIREMENTS@', str(requirements)).replace('@OUTPUT@', str(output))
    context_file = os.environ.get('TASK_CONTEXT_FILE')
    if context_file:
        context_path = Path(context_file).resolve(strict=True)
        if not context_path.is_file():
            raise ValueError(f'TASK_CONTEXT_FILE is not a readable file: {context_path}')
        context_path.read_text()
        instruction += f'\n\n本次任务提供附加上下文，请先读取 {context_path}，再结合完整公开需求执行。附加材料与官方需求文件分别提供。'
    if resume_run_id:
        instruction = '保留本会话与应用进展，继续尚未完成的工作。'
        (evidence/('recovery-instructions-'+uuid.uuid4().hex+'.md')).write_text(instruction)
    else:
        (evidence/'user-instructions.md').write_text(instruction)
    command = [str(runtime/'bin/pi'), '--provider', main_provider, '--model', model,
               '--thinking', 'high', '--mode', 'json', '--print', '--no-context-files', '--no-extensions', '--no-skills',
               '--no-prompt-templates', '--no-themes', '--extension', str(runtime/'node_modules/pi-subagents/index.ts'),
               '--extension', str(runtime/'node_modules/pi-background-bash/index.ts'),
               '--extension', str(ROOT/'extensions/capability-evidence.ts'),
               '--extension', str(ROOT/'extensions/factory-pi-timing.ts'),
               '--extension', str(ROOT/'extensions/owned-e2e.ts'),
               '--extension', str(search_extensions[0]), '--fff-mode', 'tools-only',
               '--extension', str(search_extensions[1]),
               '--extension', str(search_extensions[2]),
               '--session', str(evidence/'session.jsonl')]
    for name in SKILLS:
        command += ['--skill', str(ROOT/'skills'/name/'SKILL.md')]
    command += [instruction]
    def execution_error(stage, error):
        record = {'stage': stage, 'error_type': type(error).__name__,
                  'error': str(error), 'traceback': ''.join(traceback.format_exception(error))}
        sys.stderr.write(record['traceback'])
        try:
            with (evidence/'execution-errors.jsonl').open('a') as errors:
                errors.write(json.dumps(record, ensure_ascii=False)+'\n')
        except BaseException:
            traceback.print_exc()
    exporter = None
    if telemetry_import_error is not None:
        execution_error('telemetry-import', telemetry_import_error)
    elif LogExporter is not None:
        try:
            exporter = LogExporter(evidence, 'pi-session', model)
        except BaseException as error:
            execution_error('telemetry-prepare', error)
    save(evidence/('recovery-identity-'+uuid.uuid4().hex+'.json' if resume_run_id else 'identity.json'), {'variant': 'pi-minimal-vv', 'run_id': run_id, 'main_model': model,
                                  'main_provider': main_provider, 'advisor': advisor_model, 'skills': SKILLS, 'execution': 'single-session'})
    os.environ['FACTORY26_ENTRY_EVIDENCE'] = str(evidence)
    os.environ['FACTORY26_ENTRY_PHASE'] = 'generation'
    continuation = 0
    process = None
    try:
        while True:
            terminal = None
            streams = {}
            for name in ('events.jsonl', 'stderr.log'):
                try:
                    streams[name] = (evidence/name).open('a')
                except BaseException as error:
                    execution_error('open-'+name, error)
                    streams[name] = None
            try:
                process = subprocess.Popen(command, cwd=output, env=env, stdout=subprocess.PIPE,
                                           stderr=streams['stderr.log'], text=True, start_new_session=True)
                for line in process.stdout:
                    events = streams['events.jsonl']
                    if events is not None:
                        try:
                            events.write(line)
                            events.flush()
                        except BaseException as error:
                            execution_error('event-log', error)
                            streams['events.jsonl'] = None
                            try:
                                events.close()
                            except BaseException as close_error:
                                execution_error('event-log-close', close_error)
                    if exporter is not None:
                        try:
                            exporter.add(line.rstrip())
                        except BaseException as error:
                            execution_error('telemetry-add', error)
                            exporter = None
                    try:
                        event = json.loads(line)
                    except ValueError:
                        continue
                    message = event.get('message') or {}
                    if event.get('type') == 'message_end' and message.get('role') == 'assistant':
                        terminal = message.get('stopReason')
                code = process.wait()
                try:
                    stop(process)
                except BaseException as error:
                    execution_error('completed-pi-process-stop', error)
                process = None
            finally:
                for name, stream in streams.items():
                    if stream is not None:
                        try:
                            stream.close()
                        except BaseException as error:
                            execution_error('close-'+name, error)
            if code or terminal != 'length':
                break
            continuation += 1
            command[-1] = '上一轮输出达到长度上限。继续当前会话未完成的工作，保留已有进展。'
        native_result = {'exit_code': code, 'terminal': terminal, 'continuations': continuation}
        os.environ['FACTORY26_NATIVE_RESULT'] = json.dumps(native_result)
        try:
            save(evidence/'result.json', native_result)
        except BaseException as error:
            execution_error('native-result-save', error)
        if code or terminal != 'stop':
            raise RuntimeError(f'Pi generation failed: exit={code}, terminal={terminal}')
    except BaseException as error:
        execution_error('generation', error)
        raise
    finally:
        os.environ['FACTORY26_ENTRY_PHASE'] = 'cleanup'
        if process is not None:
            try:
                stop(process)
            except BaseException as error:
                execution_error('pi-process-stop', error)
        # Close only sessions from this run before stopping its owned daemon.
        for state_file in owned.glob('*/session.json'):
            try:
                state = json.loads(state_file.read_text())
                if state.get('session') and state.get('status') in ('open', 'open_failed', 'close_failed'):
                    close = subprocess.run([str(runtime/'bin/node'), str(ROOT/'tools/owned-e2e.mjs'),
                        json.dumps({'operation': 'close', 'handle': state['handle']})],
                        cwd=output, env=env, capture_output=True, text=True, timeout=60)
                    save(state_file.parent/'executor-close.json', {'exit_code': close.returncode,
                        'stdout': close.stdout, 'stderr': close.stderr})
                    if close.returncode:
                        execution_error('owned-e2e-close', RuntimeError(
                            f'exit={close.returncode}; stdout={close.stdout}; stderr={close.stderr}'))
            except BaseException as error:
                execution_error('owned-e2e-close', error)
        daemon_closed = False
        try:
            cleanup = subprocess.run([str(runtime/'bin/mcporter'), 'daemon', 'stop'],
                                     cwd=output, env=env, capture_output=True, text=True, timeout=20)
            daemon_closed = cleanup.returncode == 0
            save(evidence/'e2e-daemon-cleanup.json', {'exit_code': cleanup.returncode,
                 'stdout': cleanup.stdout, 'stderr': cleanup.stderr})
            if cleanup.returncode:
                execution_error('e2e-daemon-stop', RuntimeError(
                    f'exit={cleanup.returncode}; stdout={cleanup.stdout}; stderr={cleanup.stderr}'))
        except BaseException as error:
            execution_error('e2e-daemon-stop', error)
        try:
            cleanup_workspace(output, evidence=evidence)
        except BaseException as error:
            execution_error('workspace-cleanup', error)
        if daemon_closed:
            try:
                alias.unlink()
            except BaseException as error:
                execution_error('daemon-alias-removal', error)
        if exporter is not None:
            try:
                exporter.flush()
            except BaseException as error:
                execution_error('log-export', error)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('requirements', type=Path)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--type', choices=['web'], default='web')
    parser.add_argument('--model', choices=['glm-5.3', 'glm-5.3-flash'], default='glm-5.3-flash')
    args = parser.parse_args()
    signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt('terminated')))
    run(args.requirements.resolve(), args.output_dir.resolve(), args.model)


if __name__ == '__main__':
    main()
