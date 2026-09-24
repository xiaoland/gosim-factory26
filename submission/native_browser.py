"""Give each native agent session its own agent-browser process state."""

from pathlib import Path


def install(work, runtime):
    command = work / "bin/agent-browser"
    command.parent.mkdir(parents=True, exist_ok=True)
    command.write_text('''#!/usr/bin/env python3
import hashlib, os, sys
from pathlib import Path
identity = os.environ.get("PI_SESSION_ID") or os.environ.get("CODEX_THREAD_ID") or "default"
args = sys.argv[1:]
name = hashlib.sha256(identity.encode()).hexdigest()[:16]
state = Path(WORK) / "browser" / name
state.mkdir(parents=True, exist_ok=True)
env = dict(os.environ, HOME=str(state))
env.setdefault("AGENT_BROWSER_SESSION", name)
env.setdefault("AGENT_BROWSER_EXECUTABLE_PATH", CHROME)
env.setdefault("AGENT_BROWSER_SOCKET_DIR", str(Path(WORK) / "b"))
os.execve(BINARY, [BINARY, *args], env)
'''.replace("WORK", repr(str(work))).replace("CHROME", repr(str(runtime / "bin/chromium")))
   .replace("BINARY", repr(str(runtime / "bin/agent-browser"))))
    command.chmod(0o755)
    return command.parent
