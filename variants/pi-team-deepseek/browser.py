import platform
from pathlib import Path

def browser_wrapper(work, run_id, cache):
    """Native thread identity is per invocation, unlike HOME shared by children."""
    packaged_browser = cache/'bin/chromium'
    if packaged_browser.is_file():
        chrome = packaged_browser
    else:
        browsers = cache/'.agent-browser/browsers'
        pattern = 'chrome-*/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing' if platform.system()=='Darwin' else 'chrome-*/chrome'
        binaries = list(browsers.glob(pattern))
        if len(binaries) != 1:
            raise RuntimeError('locked browser executable is missing or ambiguous; run bootstrap')
        chrome = binaries[0]
    binary = cache/'bin/agent-browser' if (cache/'bin/agent-browser').is_file() else cache/'node_modules/.bin/agent-browser'
    target = work/'bin/agent-browser'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text('''#!/usr/bin/env python3
import hashlib, json, os, sys
from pathlib import Path
identity = os.environ.get('PI_SESSION_ID') or os.environ.get('CODEX_THREAD_ID')
if not identity:
    raise SystemExit('agent-browser requires PI_SESSION_ID or CODEX_THREAD_ID')
args = sys.argv[1:]
if any(a in ('--session', '--session-name', '--profile', '--connect', '--cdp', '--all') or a.startswith(('--session=', '--session-name=', '--profile=', '--cdp=')) for a in args):
    raise SystemExit('Factory owns browser session isolation; use tab commands within this session')
name = hashlib.sha256((RUN_ID+':'+identity).encode()).hexdigest()[:16]
state = Path(STATE)/name
state.mkdir(parents=True, exist_ok=True)
(state/'identity.json').write_text(json.dumps({'run_id':RUN_ID,'native_session_id':identity}))
env = dict(os.environ, AGENT_BROWSER_SESSION=name, HOME=str(state), AGENT_BROWSER_EXECUTABLE_PATH=CHROME, AGENT_BROWSER_SOCKET_DIR=SOCKETS)
os.execve(BINARY, [BINARY, '--session', name, *args], env)
'''.replace('RUN_ID', repr(run_id)).replace('STATE', repr(str(work/'browser'))).replace('BINARY', repr(str(binary))).replace('CHROME', repr(str(chrome))).replace('SOCKETS', repr(str(work/'b'))))
    target.chmod(0o755)
