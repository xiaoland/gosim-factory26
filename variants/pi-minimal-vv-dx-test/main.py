"""Direct native Pi entry for the official ARC runner."""
import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys

from raw_otlp import LogExporter
from agent_support import (browser_executable, stop, bind_native_models,
                           bind_retained_native_models)
from pi_transport import model_bindings
from pi_state import repair_state_files

ROOT = Path(__file__).resolve().parent
SKILLS = ('svc-verification', 'agent-browser', 'hyperformula', 'handsontable', 'better-auth-best-practices',
          'organization-best-practices', 'fixing-accessibility', 'ponytail')


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def run(requirements, output):
    if not (requirements/'requirements.yaml').is_file():
        raise ValueError('requirements.yaml is missing')
    runtime = ROOT/'runtime'
    for relative in json.loads((ROOT/'runtime-executables.json').read_text()):
        path = ROOT/relative
        if not path.stat().st_mode & 0o111:
            path.chmod(path.stat().st_mode | 0o111)
    output.mkdir(parents=True, exist_ok=True)
    contract_path = output/'.factory26/lab-run.json'
    if not contract_path.is_file():
        raise ValueError('ARC run contract .factory26/lab-run.json is missing')
    contract = json.loads(contract_path.read_text())
    native_scope = contract.get('native_scope_id')
    if not native_scope or not contract.get('run_id'):
        raise ValueError('lab-run.json needs run_id and native_scope_id')
    # Native state is independent of this program checkout and survives a
    # program rebuild.  Same-task restart points at the same session file.
    evidence = output/'.factory26/data/harness'/native_scope
    evidence.mkdir(parents=True, exist_ok=True)
    saved_home = evidence/'home'
    saved_home.mkdir(exist_ok=True)
    # Pi sees a script-relative home; its physical contents remain downloadable.
    home = evidence/'pi-home'
    if not home.is_symlink() and not home.exists():
        home.symlink_to(saved_home, target_is_directory=True)
    if not home.is_symlink() or home.resolve() != saved_home.resolve():
        raise ValueError(f'Pi home is already bound to a different workspace: {home}')
    native = (home/'.pi/agent').resolve()
    native.mkdir(parents=True, exist_ok=True)
    native_resume = bool(contract.get('native_resume'))
    session_path = evidence/'session.jsonl'
    if native_resume and not session_path.is_file():
        raise ValueError(f'Pi native resume requested but session is missing: {session_path}')
    main_provider, advisor_model = 'factory26', 'factory26/kimi-k2.7-code'
    if native_resume:
        models = json.loads((native/'models.json').read_text())
        identity = json.loads((evidence/'identity.json').read_text())
        main_provider, advisor_model = identity['main_provider'], identity['advisor']
    else:
        models = json.loads((ROOT/'models.json').read_text())
    bindings, model_environment = model_bindings(providers=models['providers'])
    if native_resume:
        bind_retained_native_models(models, bindings)
    else:
        bind_native_models(models, bindings)
    save(native/'models.json', models)
    if not native_resume:
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
    env = dict(model_environment)
    for name in list(env):
        if name.startswith('BRAID_') or name == 'FACTORY26_MODEL_BUDGET_PATH':
            env.pop(name)
    env.update(HOME=str(home), XDG_CONFIG_HOME=str(home/'.config'), PI_CODING_AGENT_DIR=str(native),
               PI_OFFLINE='1',
               PONYTAIL_DEFAULT_MODE='full', PI_CAPABILITY_EVIDENCE_DIR=str(evidence/'capabilities'),
               FACTORY26_PI_TIMING_FILE=str(evidence/'pi-timing.jsonl'),
               PATH=str(runtime/'bin')+':/usr/local/bin:/usr/bin:/bin',
               NODE_PATH=str(runtime/'node_modules'), PI_SUBAGENT_PI_BINARY=str(runtime/'bin/pi'),
               MCPORTER_CONFIG=str(ROOT/'mcporter.json'),
               AGENT_BROWSER_SOCKET_DIR=str(evidence/'browser'),
               BROWSER_CHECK_NODE_MODULES=str(runtime/'node_modules'))
    browser_cache = evidence/'browser-cache'
    browser_cache.mkdir(parents=True, exist_ok=True)
    env['FACTORY26_BROWSER_CACHE_DIR'] = str(browser_cache)
    browser = browser_executable(runtime)
    if browser is not None:
        env.update(AGENT_BROWSER_EXECUTABLE_PATH=str(browser), BROWSER_EXECUTABLE_PATH=str(browser))
    instruction_path = evidence/'user-instructions.md'
    if native_resume:
        instruction = instruction_path.read_text() if instruction_path.is_file() else None
        if not instruction:
            raise ValueError(f'Pi native resume requested but original instructions are missing: {instruction_path}')
    else:
        instruction = (ROOT/'instructions.md').read_text().replace('@REQUIREMENTS@', str(requirements)).replace('@OUTPUT@', str(output))
        instruction_path.write_text(instruction)
    command = [str(runtime/'bin/pi'), '--provider', main_provider, '--model', 'glm-5.3-flash',
               '--thinking', 'high', '--mode', 'json', '--print', '--no-context-files', '--no-skills',
               '--no-prompt-templates', '--no-themes', '--extension', str(runtime/'node_modules/pi-subagents/index.ts'),
               '--extension', str(runtime/'node_modules/pi-background-bash/index.ts'),
               '--extension', str(ROOT/'vendor/ponytail/pi-extension/index.js'),
               '--extension', str(ROOT/'extensions/capability-evidence.ts'),
               '--extension', str(ROOT/'extensions/factory-pi-timing.ts'),
               '--session', str(session_path)]
    for name in SKILLS:
        command += ['--skill', str(ROOT/'skills'/name/'SKILL.md')]
    command += [instruction]
    exporter = LogExporter(evidence, 'pi-session', 'glm-5.3-flash')
    save(evidence/'identity.json', {'variant': 'pi-minimal-vv-dx-test', 'main_model': 'glm-5.3-flash',
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
                    if event.get('type') in {'tool_execution_start', 'tool_execution_end'}:
                        print(json.dumps({key: event[key] for key in
                              ('type', 'toolName', 'toolCallId', 'isError') if key in event}), flush=True)
                    message = event.get('message') or {}
                    if event.get('type') == 'message_end' and message.get('role') == 'assistant':
                        terminal = message.get('stopReason')
                        usage = message.get('usage') or {}
                        print(json.dumps({'event': 'model_response', 'model': message.get('model'),
                              'stop_reason': terminal, 'tokens': {key: usage[key] for key in
                              ('input', 'output', 'cacheRead', 'cacheWrite', 'totalTokens') if key in usage}}), flush=True)
                        if terminal == 'error':
                            print(message.get('errorMessage', 'Pi assistant returned an error'),
                                  file=sys.stderr, flush=True)
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
        exporter.flush()
        ownership_errors = repair_state_files(output, [native])
        if ownership_errors:
            save(evidence/'state-ownership-errors.json', ownership_errors)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('requirements', type=Path)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--type', choices=['web'], default='web')
    args = parser.parse_args()
    signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt('terminated')))
    run(args.requirements.resolve(), args.output_dir.resolve())


if __name__ == '__main__':
    main()
