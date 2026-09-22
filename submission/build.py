"""Finish the portable runtime inside the Linux build image."""
import json
from pathlib import Path
import sys
import shutil

root = Path('/runtime')
backend = sys.argv[1]
for dependency in ('@earendil-works/pi-coding-agent', '@openai/codex', 'agent-browser', 'pi-subagents'):
    if not (root / 'node_modules' / dependency).is_dir():
        raise RuntimeError(f'frozen npm dependency missing: {dependency}')
if not any((root / '.agent-browser/browsers').glob('chrome-*')):
    raise RuntimeError('frozen agent-browser Chromium is missing')
for command, package in (('pi', '@earendil-works/pi-coding-agent'),
                         ('codex', '@openai/codex'), ('agent-browser', 'agent-browser')):
    metadata = json.loads((root / 'node_modules' / package / 'package.json').read_text())
    entry = metadata['bin'][command]
    (root / 'bin' / command).write_text(
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
