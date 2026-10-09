"""Shared arc-core browser entry scripts used by direct and derived builds."""


def browser_scripts():
    # Preserve the executor's browser namespace, including Playwright's "0".
    # Resolve through Playwright itself so revision and package-local paths match.
    cache = '''if [ -z "${PLAYWRIGHT_BROWSERS_PATH:-}" ]; then
  PLAYWRIGHT_BROWSERS_PATH="${FACTORY26_BROWSER_CACHE_DIR:-${XDG_CACHE_HOME:-$HERE/../.cache}/factory26-playwright}"
  if [ "$PLAYWRIGHT_BROWSERS_PATH" != "0" ]; then mkdir -p "$PLAYWRIGHT_BROWSERS_PATH"; fi
fi
export PLAYWRIGHT_BROWSERS_PATH
'''
    install = '''#!/bin/sh
set -eu
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
''' + cache + '''if [ -n "${FACTORY26_BROWSER_EXECUTABLE_PATH:-}" ] && command -v "$FACTORY26_BROWSER_EXECUTABLE_PATH" >/dev/null 2>&1; then
  command -v "$FACTORY26_BROWSER_EXECUTABLE_PATH"; exit 0
fi
playwright_browser() { "$HERE/node" -e 'process.stdout.write(require(process.argv[1]).chromium.executablePath())' "$HERE/../node_modules/playwright"; }
BROWSER=$(playwright_browser)
if [ -x "$BROWSER" ]; then printf "%s\\n" "$BROWSER"; exit 0; fi
for candidate in google-chrome chromium chromium-browser; do
  if command -v "$candidate" >/dev/null 2>&1; then command -v "$candidate"; exit 0; fi
done
"$HERE/node" "$HERE/../node_modules/playwright/cli.js" install chromium --no-shell "$@" >&2
BROWSER=$(playwright_browser)
if [ -x "$BROWSER" ]; then printf "%s\\n" "$BROWSER"; exit 0; fi
echo "Playwright Chromium was not installed at $BROWSER (PLAYWRIGHT_BROWSERS_PATH=$PLAYWRIGHT_BROWSERS_PATH)" >&2
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
case "${1:-}" in --help|-h|--version|-V|skills|session) exec "$HERE/node" "$HERE/../node_modules/agent-browser/bin/agent-browser.js" "$@";; esac
''' + cache + '''if [ -z "${AGENT_BROWSER_EXECUTABLE_PATH:-}" ]; then
  AGENT_BROWSER_EXECUTABLE_PATH=$("$HERE/browser-install")
fi
export AGENT_BROWSER_EXECUTABLE_PATH
exec "$HERE/node" "$HERE/../node_modules/agent-browser/bin/agent-browser.js" "$@"
'''
    return {'browser-install': install, 'browser-exec': exec_script, 'agent-browser': agent}
