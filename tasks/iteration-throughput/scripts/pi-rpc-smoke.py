"""No-model qualification of actual Pi RPC and the installed lifecycle command."""
import json
import os
from pathlib import Path
import selectors
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'scripts'))
import native_profiles

cache = native_profiles.runtime_cache()
out = ROOT/'runs/qualification/pi-rpc-smoke'
out.mkdir(parents=True, exist_ok=True)
with tempfile.TemporaryDirectory(prefix='factory26-pi-rpc-') as temp:
    home = Path(temp)
    command = [str(cache/'node_modules/.bin/pi'), '--mode', 'rpc', '--no-extensions', '--no-skills',
               '--no-prompt-templates', '--no-themes', '--extension', str(cache/'node_modules/pi-subagents/index.ts'),
               '--extension', str(ROOT/'harness/extensions/factory-subagent-lifecycle.ts')]
    env = {'PATH':os.environ['PATH'], 'HOME':str(home), 'PI_CODING_AGENT_DIR':str(home), 'PI_OFFLINE':'1', 'PI_TELEMETRY':'0'}
    with (out/'stderr.log').open('w') as errors, (out/'rpc.jsonl').open('w') as evidence:
        process = subprocess.Popen(command, cwd=home, env=env, stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE, stderr=errors)
        selector = selectors.DefaultSelector(); selector.register(process.stdout, selectors.EVENT_READ)
        pending = b''
        def rpc(kind, **extra):
            global pending
            identity = kind+'-'+str(time.time_ns())
            process.stdin.write((json.dumps({'id':identity,'type':kind,**extra})+'\n').encode()); process.stdin.flush()
            deadline = time.monotonic()+30
            while time.monotonic()<deadline:
                if not selector.select(max(0, deadline-time.monotonic())): break
                chunk = os.read(process.stdout.fileno(), 65536)
                if not chunk: raise RuntimeError('Pi exited before RPC reply')
                pending += chunk
                while b'\n' in pending:
                    line,pending=pending.split(b'\n',1)
                    if not line.strip(): continue
                    frame=json.loads(line); evidence.write(json.dumps(frame)+'\n'); evidence.flush()
                    if frame.get('id')==identity:
                        assert frame.get('success') is True, frame
                        return frame.get('data')
            raise TimeoutError('Pi RPC did not reply within 30 seconds: '+kind)
        try:
            state=rpc('get_state'); parent=state['sessionId']
            rpc('abort')
            directory=home/'.factory'; directory.mkdir(exist_ok=True)
            request={'schema_version':1,'fence_id':'no-model','parent_native_session_id':parent,'started_at':int(time.time())}
            (directory/'teardown-request.json').write_text(json.dumps(request))
            rpc('prompt',message='/factory-subagent-stop')
            receipt=json.loads((directory/'subagent-stop.json').read_text())
            assert receipt['state']=='ready' and receipt['children']==[], receipt
            assert receipt['parent_native_session_id']==parent
            (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
            print(json.dumps({'status':'passed','scope':'actual Pi RPC + lifecycle command, no children/model calls','evidence':str(out)}))
        finally:
            selector.close(); process.terminate()
            try: process.wait(timeout=5)
            except subprocess.TimeoutExpired: process.kill(); process.wait()
