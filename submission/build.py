"""Finish the portable runtime inside the Linux build image."""
import json
from pathlib import Path
import re
import subprocess
import sys
import shutil

root = Path('/runtime')
backend = sys.argv[1]
for dependency in ('@earendil-works/pi-coding-agent', '@openai/codex', 'agent-browser', 'pi-subagents'):
    if not (root / 'node_modules' / dependency).is_dir():
        raise RuntimeError(f'frozen npm dependency missing: {dependency}')
if not any((root / '.agent-browser/browsers').glob('chrome-*')):
    raise RuntimeError('frozen agent-browser Chromium is missing')
if backend == 'pi':
    for package in ('@openai/codex', '@openai/codex-linux-x64'):
        target = root/'node_modules'/package
        if not target.is_dir():
            raise RuntimeError(f'frozen npm dependency missing: {package}')
        shutil.rmtree(target)
    (root/'node_modules/.bin/codex').unlink()
agent_browser_bin = root/'node_modules/agent-browser/bin'
for path in agent_browser_bin.iterdir():
    if path.name not in ('agent-browser.js', 'agent-browser-linux-x64'):
        shutil.rmtree(path) if path.is_dir() else path.unlink()
chrome = next((root / '.agent-browser/browsers').glob('chrome-*/chrome'))
dependencies = subprocess.run(['ldd', str(chrome)], check=True, capture_output=True, text=True).stdout
missing = [line.strip() for line in dependencies.splitlines() if 'not found' in line]
if missing:
    raise RuntimeError('Chromium dependency missing in build image: ' + ', '.join(missing))
library = root / 'lib/chromium'
library.mkdir(parents=True)
platform_library = re.compile(r'^(?:libc|libm|libpthread|librt|libdl|libresolv)\.so(?:\.|$)|^ld-linux')
for line in dependencies.splitlines():
    paths = [Path(field) for field in line.split() if field.startswith('/')]
    if not paths:
        continue
    source = paths[0]
    if platform_library.match(source.name):
        continue
    shutil.copy2(source.resolve(), library/source.name)
shutil.copytree('/usr/share/fonts', root/'share/fonts')
shutil.copytree('/usr/share/glib-2.0/schemas', root/'share/glib-2.0/schemas')
fontconfig = root/'etc/fonts'
fontconfig.mkdir(parents=True)
(fontconfig/'fonts.conf').write_text('''<?xml version="1.0"?>
<!DOCTYPE fontconfig SYSTEM "urn:fontconfig:fonts.dtd">
<fontconfig>
  <dir prefix="relative">../../share/fonts</dir>
  <cachedir prefix="xdg">fontconfig</cachedir>
</fontconfig>
''')
(root / 'bin/chromium').write_text(
    '#!/bin/sh\nHERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)\n'
    'LD_LIBRARY_PATH="$HERE/../lib/chromium${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"\n'
    'FONTCONFIG_PATH="$HERE/../etc/fonts"\n'
    'FONTCONFIG_FILE="$FONTCONFIG_PATH/fonts.conf"\n'
    'GSETTINGS_SCHEMA_DIR="$HERE/../share/glib-2.0/schemas"\n'
    'XDG_DATA_DIRS="$HERE/../share${XDG_DATA_DIRS:+:$XDG_DATA_DIRS}"\n'
    'export LD_LIBRARY_PATH FONTCONFIG_PATH FONTCONFIG_FILE GSETTINGS_SCHEMA_DIR XDG_DATA_DIRS\n'
    f'exec "$HERE/../{chrome.relative_to(root)}" "$@"\n'
)
commands = [('pi', '@earendil-works/pi-coding-agent'), ('agent-browser', 'agent-browser')]
if backend == 'codex':
    commands.append(('codex', '@openai/codex'))
for command, package in commands:
    metadata = json.loads((root / 'node_modules' / package / 'package.json').read_text())
    entry = metadata['bin'][command]
    environment = ': "${AGENT_BROWSER_EXECUTABLE_PATH:=$HERE/chromium}"\nexport AGENT_BROWSER_EXECUTABLE_PATH\n' if command == 'agent-browser' else ''
    (root / 'bin' / command).write_text(
        '#!/bin/sh\nHERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)\n'
        + environment +
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
