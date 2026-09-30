"""Direct native Pi entry for the official ARC runner."""
import argparse
import json
import os
from pathlib import Path
import signal
import subprocess

from raw_otlp import LogExporter
from agent_support import cleanup_workspace, stop

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
        path.chmod(path.stat().st_mode | 0o111)
    output.mkdir(parents=True, exist_ok=True)
    # ARC does not expose .arc in downloaded workspaces; use the existing
    # experiment evidence directory, independently of the generated app.
    evidence = output/'.factory26/pi-minimal'
    evidence.mkdir(parents=True, exist_ok=True)
    saved_home = evidence/'home'
    saved_home.mkdir(exist_ok=True)
    # Pi sees a script-relative home; its physical contents remain downloadable.
    home = ROOT/'pi-home'
    if not home.is_symlink() and not home.exists():
        home.symlink_to(saved_home, target_is_directory=True)
    if not home.is_symlink() or home.resolve() != saved_home.resolve():
        raise ValueError(f'Pi home is already bound to a different workspace: {home}')
    native = (home/'.pi/agent').resolve()
    native.mkdir(parents=True, exist_ok=True)
    private_models = ROOT/'private-models.json'
    main_provider, advisor_model = 'factory26', 'factory26/kimi-k2.7-code'
    key = None
    if private_models.is_file():
        models = json.loads(private_models.read_text())
        main_provider, advisor_model = 'bigmodel', 'arc/kimi-k2.7-code'
    else:
        key = os.environ.get('OPENAI_API_KEY') or os.environ.get('FACTORY26_API_KEY')
        base = os.environ.get('OPENAI_BASE_URL') or os.environ.get('FACTORY26_BASE_URL')
        if not key or not base:
            raise ValueError('Runner must provide OPENAI_API_KEY and OPENAI_BASE_URL')
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
        if name.startswith('BRAID_') or name == 'FACTORY26_MODEL_BUDGET_PATH' or (
                private_models.is_file() and name in ('OPENAI_API_KEY', 'OPENAI_BASE_URL', 'FACTORY26_API_KEY', 'FACTORY26_BASE_URL')):
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
               AGENT_BROWSER_EXECUTABLE_PATH=str(runtime/'bin/chromium'),
               AGENT_BROWSER_SOCKET_DIR=str(evidence/'browser'),
               BROWSER_EXECUTABLE_PATH=str(runtime/'bin/chromium'),
               BROWSER_CHECK_NODE_MODULES=str(runtime/'node_modules'))
    instruction = (ROOT/'instructions.md').read_text().replace('@REQUIREMENTS@', str(requirements)).replace('@OUTPUT@', str(output))
    (evidence/'user-instructions.md').write_text(instruction)
    command = [str(runtime/'bin/pi'), '--provider', main_provider, '--model', 'glm-5.3-flash',
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
    exporter = LogExporter(evidence, 'pi-session', 'glm-5.3-flash')
    save(evidence/'identity.json', {'variant': 'pi-minimal', 'main_model': 'glm-5.3-flash',
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
        cleanup_workspace(output)
        exporter.flush()


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
