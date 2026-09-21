"""Finish the portable runtime inside the Linux build image."""
import json
from pathlib import Path
import sys
import shutil

root = Path('/runtime')
backend = sys.argv[1]
package = '@earendil-works/pi-coding-agent' if backend == 'pi' else '@openai/codex'
metadata = json.loads((root / 'node_modules' / package / 'package.json').read_text())
entry = metadata['bin'][backend]
(root / 'bin' / backend).write_text(
    '#!/bin/sh\nHERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)\n'
    f'exec "$HERE/node" "$HERE/../node_modules/{package}/{entry}" "$@"\n'
)
for name, module, function in [('svc', 'svc_cli.cli', 'main')] + (
        [('litellm', 'litellm', 'run_server')] if backend == 'codex' else []):
    (root / 'bin' / name).write_text(
        '#!/usr/bin/env python3\nimport sys\nfrom pathlib import Path\n'
        "sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'python'))\n"
        f'from {module} import {function}\nsys.exit({function}())\n'
    )
for path in (root / 'bin').iterdir():
    path.chmod(0o755)

for path in root.rglob('__pycache__'):
    if path.is_dir():
        shutil.rmtree(path)
