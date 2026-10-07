"""Incremental native Pi entry using the caller's frozen model connection."""
import argparse
import json
import os
from pathlib import Path
import signal
import shutil
import sys
import uuid
import subprocess

from raw_otlp import LogExporter
from agent_support import cleanup_workspace, stop

ROOT = Path(__file__).resolve().parent
SKILLS = ('svc-task-packet', 'svc-specs', 'svc-verification', 'e2e', 'agent-browser', 'hyperformula', 'handsontable', 'better-auth-best-practices',
          'organization-best-practices', 'fixing-accessibility', 'ponytail')


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def run(requirements, output, model='glm-5.3-flash'):
    if not (requirements/'requirements.yaml').is_file():
        raise ValueError('requirements.yaml is missing')
    if sys.platform != 'linux':
        raise RuntimeError('This frozen Harness requires the official Linux runner')
    runtime = ROOT/'runtime'
    browser = runtime/'bin/browser-exec'
    if not browser.is_file():
        browser = runtime/'bin/chromium'
    for relative in json.loads((ROOT/'runtime-executables.json').read_text()):
        path = ROOT/relative
        mode = path.stat().st_mode
        if mode & 0o111 != 0o111:
            path.chmod(mode | 0o111)
    output.mkdir(parents=True, exist_ok=True)
    # The baseline carries prior native state; every new task owns a fresh run.
    resume_run_id = os.environ.get('FACTORY26_PI_RESUME_RUN_ID')
    run_id = resume_run_id or uuid.uuid4().hex
    if len(run_id) != 32 or any(c not in '0123456789abcdef' for c in run_id):
        raise ValueError('FACTORY26_PI_RESUME_RUN_ID must be a native run UUID')
    evidence = output/'.factory26/pi-minimal-vv/runs'/run_id
    if resume_run_id:
        previous_identity = json.loads((evidence/'identity.json').read_text())
        if previous_identity['variant'] != 'pi-minimal-vv' or previous_identity['main_model'] != model:
            raise ValueError('Native resume identity does not match this variant/model')
        if not (evidence/'session.jsonl').is_file():
            raise ValueError('Native resume session is missing')
        previous_result = evidence/'result.json'
        if previous_result.exists():
            shutil.copy2(previous_result, evidence/('result-before-recovery-'+uuid.uuid4().hex+'.json'))
    else:
        evidence.mkdir(parents=True, exist_ok=False)
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
    save(native/'settings.json', {'packages': [], 'subagents': {'disableBuiltins': True}})
    subagent_config = native/'extensions/subagent'
    subagent_config.mkdir(parents=True, exist_ok=True)
    save(subagent_config/'config.json', {'toolDescriptionMode': 'compact'})
    (home/'.config').mkdir(exist_ok=True)
    env = dict(os.environ)
    for name in list(env):
        if name.startswith('BRAID_') or name == 'FACTORY26_MODEL_BUDGET_PATH':
            env.pop(name)
    if key:
        env['FACTORY26_API_KEY'] = key
    env.update(HOME=str(home), XDG_CONFIG_HOME=str(home/'.config'), PI_CODING_AGENT_DIR=str(native),
               PI_OFFLINE='1',
               PONYTAIL_DEFAULT_MODE='full', PI_CAPABILITY_EVIDENCE_DIR=str(evidence/'capabilities'),
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
    e2e_project = evidence/'e2e-project'
    e2e_project.mkdir(exist_ok=bool(resume_run_id))
    shutil.copy2(ROOT/'tools/e2e.config.ts', e2e_project/'e2e.config.ts')
    if not (e2e_project/'node_modules').is_symlink():
        (e2e_project/'node_modules').symlink_to(runtime/'e2e/node_modules', target_is_directory=True)
    env['E2E_PROJECT_DIR'] = str(e2e_project)
    mcp = json.loads((ROOT/'mcporter.json').read_text())
    (ROOT/'tools/e2e-cli').chmod(0o755)
    mcp['mcpServers']['e2e'] = {'command': str(ROOT/'tools/e2e-cli'),
        'args': ['mcp', '--headless'],
        'cwd': str(e2e_project), 'lifecycle': 'keep-alive'}
    save(evidence/'mcporter.json', mcp)
    env['MCPORTER_CONFIG'] = str(evidence/'mcporter.json')
    instruction = (ROOT/'instructions.md').read_text().replace('@REQUIREMENTS@', str(requirements)).replace('@OUTPUT@', str(output))
    context_file = os.environ.get('TASK_CONTEXT_FILE')
    if context_file:
        context_path = Path(context_file).resolve(strict=True)
        if not context_path.is_file():
            raise ValueError(f'TASK_CONTEXT_FILE is not a readable file: {context_path}')
        context_path.read_text()
        instruction += f'\n\n本次任务提供附加上下文，请先读取 {context_path}，再结合完整公开需求执行。附加材料与官方需求文件分别提供。'
    if resume_run_id:
        instruction = '上一轮模型连接请求失败。保留本会话与应用进展，继续尚未完成的工作。'
        (evidence/('recovery-instructions-'+uuid.uuid4().hex+'.md')).write_text(instruction)
    else:
        (evidence/'user-instructions.md').write_text(instruction)
    command = [str(runtime/'bin/pi'), '--provider', main_provider, '--model', model,
               '--thinking', 'high', '--mode', 'json', '--print', '--no-context-files', '--no-skills',
               '--no-prompt-templates', '--no-themes', '--extension', str(runtime/'node_modules/pi-subagents/index.ts'),
               '--extension', str(runtime/'node_modules/pi-background-bash/index.ts'),
               '--extension', str(ROOT/'vendor/ponytail/pi-extension/index.js'),
               '--extension', str(ROOT/'extensions/capability-evidence.ts'),
               '--extension', str(ROOT/'extensions/factory-pi-timing.ts'),
               '--session', str(evidence/'session.jsonl')]
    for name in SKILLS:
        command += ['--skill', str(ROOT/'skills'/name/'SKILL.md')]
    command += [instruction]
    exporter = LogExporter(evidence, 'pi-session', model)
    save(evidence/('recovery-identity-'+uuid.uuid4().hex+'.json' if resume_run_id else 'identity.json'), {'variant': 'pi-minimal-vv', 'run_id': run_id, 'main_model': model,
                                  'main_provider': main_provider, 'advisor': advisor_model, 'skills': SKILLS})
    continuation = 0
    process = None
    try:
        while True:
            terminal = None
            with (evidence/'events.jsonl').open('a') as events, (evidence/'stderr.log').open('a') as errors:
                process = subprocess.Popen(command, cwd=output, env=env, stdout=subprocess.PIPE,
                                           stderr=errors, text=True, start_new_session=True)
                for line in process.stdout:
                    events.write(line)
                    events.flush()
                    exporter.add(line.rstrip())
                    try:
                        event = json.loads(line)
                    except ValueError:
                        continue
                    message = event.get('message') or {}
                    if event.get('type') == 'message_end' and message.get('role') == 'assistant':
                        terminal = message.get('stopReason')
                code = process.wait()
                stop(process)
                process = None
            if code or terminal != 'length':
                break
            continuation += 1
            command[-1] = '上一轮输出达到长度上限。继续当前会话未完成的工作，保留已有进展。'
        save(evidence/'result.json', {'exit_code': code, 'terminal': terminal, 'continuations': continuation})
        if code or terminal != 'stop':
            raise RuntimeError(f'Pi generation failed: exit={code}, terminal={terminal}')
    finally:
        if process is not None:
            stop(process)
        daemon_closed = False
        try:
            cleanup = subprocess.run([str(runtime/'bin/mcporter'), 'daemon', 'stop'],
                                     cwd=output, env=env, capture_output=True, text=True, timeout=20)
            daemon_closed = cleanup.returncode == 0
            save(evidence/'e2e-daemon-cleanup.json', {'exit_code': cleanup.returncode,
                 'stdout': cleanup.stdout, 'stderr': cleanup.stderr})
        except (OSError, subprocess.TimeoutExpired) as error:
            save(evidence/'e2e-daemon-cleanup.json', {'error': str(error), 'closed': False})
        cleanup_workspace(output, evidence=evidence)
        if daemon_closed:
            alias.unlink()
        exporter.flush()


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
