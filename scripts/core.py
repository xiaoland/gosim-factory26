"""Native agent transports; provider homes are supplied by the isolated run."""
import json
import hashlib
import re
import shutil
import subprocess
from pathlib import Path


def archive_sessions(output, home, work, entries):
    """Archive every declared physical session, including invalidated sessions.

    Missing evidence remains an explicit entry so failure diagnostics retain the
    producer's identity instead of guessing from file order or modification time.
    """
    native = output/'native'
    native.mkdir(exist_ok=True)
    archived = []
    for index, entry in enumerate(entries):
        row = dict(entry, native=None, sha256=None)
        try:
            provider, session_id = row['provider'], row['session_id']
            source = row.get('native_session_path')
            if not source and provider == 'codex' and re.fullmatch(r'[a-fA-F0-9-]+', session_id):
                matches = list(home.glob(f'sessions/**/rollout-*-{session_id}.jsonl'))
                if len(matches) != 1:
                    raise ValueError('Codex thread 没有唯一的原生 rollout')
                source = matches[0]
            if not source:
                raise ValueError('会话没有明确的原生文件路径')
            source = Path(source).resolve(strict=True)
            if not source.is_relative_to(work.resolve()):
                raise ValueError('原生会话路径不属于本次隔离目录')
            with source.open() as stream:
                header = json.loads(stream.readline())
            actual_id = header.get('payload', {}).get('id') if provider == 'codex' else header.get('id')
            # Pi's provider session ID is its native path; the header carries a UUID.
            if provider == 'codex' and actual_id != session_id:
                raise ValueError('原生会话身份与 Braid 清单不同')
            if provider == 'pi' and session_id not in (actual_id, str(source)):
                raise ValueError('Pi 原生会话身份与清单不同')
            target = native/f'{index:03}-{source.name}'
            shutil.copy2(source, target)
            row.update(source_path=str(source), native=str(target.relative_to(output)),
                       sha256=hashlib.sha256(target.read_bytes()).hexdigest(), native_id=actual_id)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            row['archive_error'] = str(exc)
        archived.append(row)
    manifest = {'schema_version': 1, 'sessions': archived}
    (native/'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n')
    return archived


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
