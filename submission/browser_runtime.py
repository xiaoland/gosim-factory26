"""Shared arc-core browser entry scripts used by direct and derived builds."""

def browser_scripts():
    install = '''#!/bin/sh
set -eu
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
for candidate in "${FACTORY26_BROWSER_EXECUTABLE_PATH:-}" google-chrome chromium chromium-browser; do
  if [ -n "$candidate" ] && command -v "$candidate" >/dev/null 2>&1; then command -v "$candidate"; exit 0; fi
done
CACHE="${FACTORY26_BROWSER_CACHE_DIR:-${XDG_CACHE_HOME:-$HERE/../.cache}/factory26-playwright}"
mkdir -p "$CACHE"
export PLAYWRIGHT_BROWSERS_PATH="$CACHE"
"$HERE/node" "$HERE/../node_modules/playwright/cli.js" install chromium --no-shell "$@" >&2
for BROWSER in "$CACHE"/chromium-*/chrome-linux*/chrome; do
  if [ -x "$BROWSER" ]; then printf "%s\\n" "$BROWSER"; exit 0; fi
done
echo "Playwright Chromium was not installed" >&2
exit 1
'''
    exec_script = '''#!/bin/sh
set -eu
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
BROWSER=$("$HERE/browser-install")
exec "$BROWSER" "$@"
'''
    agent = '''#!/bin/sh
set -eu
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
case "${1:-}" in --help|-h|--version|-V) exec "$HERE/node" "$HERE/../node_modules/agent-browser/bin/agent-browser.js" "$@";; esac
CACHE="${FACTORY26_BROWSER_CACHE_DIR:-${XDG_CACHE_HOME:-$HERE/../.cache}/factory26-playwright}"
export PLAYWRIGHT_BROWSERS_PATH="$CACHE"
find_browser() { for candidate in "${FACTORY26_BROWSER_EXECUTABLE_PATH:-}" google-chrome chromium chromium-browser; do if [ -n "$candidate" ] && command -v "$candidate" >/dev/null 2>&1; then command -v "$candidate"; return; fi; done; find "$CACHE" -type f -path "*/chromium-*/chrome-linux*/chrome" -perm -u+x -print -quit; }
BROWSER="$(find_browser || true)"
if [ -z "$BROWSER" ]; then BROWSER=$("$HERE/browser-install"); fi
export AGENT_BROWSER_EXECUTABLE_PATH="${AGENT_BROWSER_EXECUTABLE_PATH:-$BROWSER}"
exec "$HERE/node" "$HERE/../node_modules/agent-browser/bin/agent-browser.js" "$@"
'''
    return {'browser-install': install, 'browser-exec': exec_script, 'agent-browser': agent}
