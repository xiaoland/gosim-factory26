"""Run the approved frozen-application check-writing experiment on WSL."""
import json
import os
from pathlib import Path
import subprocess
import time

root = Path('/home/yyh/Development/factory26/runs/acceptance-integrity/20260926/method-check')
runtime = root.parent / 'runtime'
materials = root / 'materials'
workspace = root / 'checks-workspace'
workspace.mkdir(exist_ok=True)
credentials = {}
for line in (Path.home() / '.config/factory26/llm.env').read_text().splitlines():
    if '=' in line and not line.lstrip().startswith('#'):
        name, value = line.split('=', 1)
        credentials[name.strip()] = value.strip().strip('"').strip("'")
env = dict(os.environ, FACTORY26_API_KEY=credentials['FACTORY26_API_KEY'],
           PI_CODING_AGENT_DIR=str(materials / 'config'), PI_OFFLINE='1', PI_TELEMETRY='0',
           BROWSER_CHECK_NODE_MODULES=str(runtime / 'node_modules'),
           BROWSER_EXECUTABLE_PATH=str(runtime / 'bin/chromium'),
           AGENT_BROWSER_EXECUTABLE_PATH=str(runtime / 'bin/chromium'),
           BASE_URL='http://127.0.0.1:4317',
           PATH=str(runtime / 'bin') + os.pathsep + os.environ['PATH'])
command = [str(runtime / 'bin/pi'), '--mode', 'json', '--print', '--no-context-files',
           '--no-extensions', '--no-skills', '--no-prompt-templates', '--no-themes',
           '--provider', 'factory26', '--model', 'deepseek-v4-flash', '--thinking', 'high',
           '--tools', 'read,bash,edit,write,grep,find,ls',
           '--session', str(root / 'session.jsonl'),
           '--append-system-prompt', str(materials / 'instructions.md')]
for name in ('svc-verification', 'svc-implementation', 'svc-design', 'svc-task-packet',
             'svc-investigation', 'browser-checks'):
    command += ['--skill', str(materials / 'skills' / name / 'SKILL.md')]
command.append('@' + str(materials / 'prompt.md'))
record = dict(started_at=time.time(), model='deepseek-v4-flash', reasoning='high',
              source_commit='4c1784365ffe98f3a02a9639d0c083c8fb7d76d7',
              command=command, status='running')
record_path = root / 'check-writer.json'
if record_path.exists():
    raise FileExistsError('This experiment already has a check-writer record; inspect it before resuming.')
record_path.write_text(json.dumps(record, ensure_ascii=False, indent=2))
with (root / 'pi-output.jsonl').open('w') as output, (root / 'pi-stderr.log').open('w') as error:
    result = subprocess.run(command, cwd=workspace, env=env, stdout=output, stderr=error)
record.update(finished_at=time.time(), exit_code=result.returncode,
              status='finished' if result.returncode == 0 else 'failed')
record_path.write_text(json.dumps(record, ensure_ascii=False, indent=2))
print(json.dumps({key:record[key] for key in ('status', 'exit_code', 'started_at', 'finished_at')}))
