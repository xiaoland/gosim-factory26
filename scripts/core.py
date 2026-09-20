"""Native agent transports; provider homes are supplied by the isolated run."""
import json
import subprocess
from pathlib import Path


def codex_turn(command, app, env, prompt, output, model, thinking):
    """Drive app-server v2; only turn/completed establishes completion."""
    with (output / 'codex-events.jsonl').open('w') as events, (output / 'codex.stderr.log').open('w') as err:
        proc = subprocess.Popen(command + ['app-server', '--stdio'], cwd=app, env=env,
                                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=err,
                                text=True, start_new_session=True)
        next_id = 0
        deferred = []
        def send(method, params, request=True):
            nonlocal next_id
            frame = {'method': method, 'params': params}
            if request:
                next_id += 1
                frame['id'] = next_id
            proc.stdin.write(json.dumps(frame) + '\n'); proc.stdin.flush()
            return next_id
        def receive():
            line = proc.stdout.readline()
            if not line:
                raise RuntimeError('Codex app-server disconnected before terminal')
            events.write(line); events.flush()
            frame = json.loads(line)
            if 'method' in frame and 'id' in frame:
                # No operator exists. Reject unsupported interactive requests explicitly.
                proc.stdin.write(json.dumps({'id':frame['id'], 'error':{'code':-32601,'message':'Unattended harness has no interactive handler'}})+'\n')
                proc.stdin.flush()
            return frame
        def request(method, params):
            request_id = send(method, params)
            while True:
                frame = receive()
                if frame.get('id') == request_id and 'method' not in frame:
                    if 'error' in frame: raise RuntimeError(str(frame['error']))
                    return frame['result']
                deferred.append(frame)
        try:
            request('initialize', {'clientInfo': {'name':'factory26','version':'1'}, 'capabilities':{'experimentalApi':True}})
            send('initialized', {}, False)
            result = request('thread/start', {'cwd':str(app), 'model':model,
                             'approvalPolicy':'never', 'sandbox':'danger-full-access', 'ephemeral':False})
            thread = result['thread']['id']
            started = request('turn/start', {'threadId':thread, 'input':[{'type':'text','text':prompt}], 'effort':thinking})
            usage = None
            while True:
                frame = deferred.pop(0) if deferred else receive()
                if frame.get('params',{}).get('threadId') != thread: continue
                if frame.get('method') == 'thread/tokenUsage/updated': usage = frame['params'].get('tokenUsage')
                if frame.get('method') == 'turn/completed':
                    turn = frame['params']['turn']
                    if turn['id'] != started['turn']['id']: continue
                    if turn['status'] != 'completed': raise RuntimeError(str(turn))
                    return {'thread_id':thread, 'native_usage':usage, 'estimated_cost':None}
        finally:
            # Imported lazily so this transport can also be used in standalone probes.
            import os, signal
            try: os.killpg(proc.pid, signal.SIGTERM)
            except ProcessLookupError: pass
            try: proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL); proc.wait()
            proc.stdin.close()
            proc.stdout.close()


def codex_config(home, base_url, model):
    (home / 'config.toml').write_text(f'''model_supports_reasoning_summaries = true
model_reasoning_summary = "none"
model = {json.dumps(model)}
model_provider = "factory26"
approval_policy = "never"
sandbox_mode = "danger-full-access"
web_search = "disabled"
[model_providers.factory26]
name = "Factory26 competition"
base_url = {json.dumps(base_url)}
env_key = "FACTORY26_API_KEY"
wire_api = "responses"
''')
