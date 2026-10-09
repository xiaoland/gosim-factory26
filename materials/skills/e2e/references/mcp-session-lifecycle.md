# Keep one MCP attempt on one connection

Manual MCP is interactive exploration; repeatable application acceptance belongs in TypeScript checks run by the frozen runner. MCP does not invoke the inner model, and the runner owns its own attempts and engines rather than adopting a manual MCP session.

Before open, read Runtime setup and choose the actual isolated service, absolute config, output destination and supplied tool command. Preserve the whole environment, not just three E2E variables. Keep endpoint/model/credential values private and unchanged. For mcporter keep-alive, child environment, resolved command/arguments and configured cwd participate in connection identity; different identities can coexist in the same daemon with separate E2E session maps. The server's config cwd, rather than an incidental shell cwd, is its working directory; do not change server configuration during a live attempt.

Open once and retain the id in local program state. The frozen E2E 0.15.1 MCP surface is:

| Tool | Payload | Result |
| --- | --- | --- |
| open_session | optional config and target | content text with Session <id>, tool catalog and initial observation |
| tools | session, optional tool | catalog or that tool's argument schema |
| call | session, tool, optional args object | content with action/observation; failure can include isError and an observation |
| close_session | session | cleanup text; closes that engine and app processes it started |

These tools do not use a session_id payload. The SDK allows omitted session only when exactly one session is open; always pass it explicitly. Open is not a reconnect operation. Never add E2E_SESSION to the child environment after open to carry the id: put session in the MCP payload. Each session exists only in its owning E2E server process; disconnect closes it, and another process cannot accept its id. Do not retry an unknown id against a different connection or keep opening sessions until a call happens to work.

Use locate to try semantic locators and read the exact match count, verdict, current nodes and generated test expression. Inspect tools {tool: "locate"} for the installed arguments. Use roles and accessible names where the contract requires them; choose one of role/text/label/placeholder/testId, with name narrowing role. Match exactly unless the requirement justifies substring matching. A locate result is exploration feedback, not a durable handle or completed acceptance assertion. Do not regex-search observation lines to infer a control, or reuse a node id after the screen changes.

Handle CLI transport failures and MCP isError as failures, retaining actual content and exit status. The frozen mcporter CLI maps the original MCP isError to exit 1 before formatting; the example uses text output plus that real exit. Its --output json can unwrap structured content or JSON-valued text and does not guarantee a content/isError envelope; --output raw is Node inspection text rather than guaranteed JSON. Do not JSON.parse either mode assuming the raw MCP envelope. An action failure can still return a new observation. Close your own returned id in finally using the same connection environment, and retain both the primary failure and cleanup result. If open fails before returning an id, report it rather than inventing an id or stopping the shared daemon. Only after old sessions close may a new attempt choose a new output directory; do not adopt reports left by earlier attempts.

The complete interaction example below uses only Node standard-library process calls. Run it with the supplied tool Node after exporting the owned attempt environment; its sole positional argument is a JSON locate query from the actual catalog. It performs read-only exploration after opening, not an acceptance verdict. Extend the action block when implementing a real journey, preserve this open/finally-close lifecycle, and use TypeScript tests for repeatable requirement assertions. Consult e2e guide mcp for the locked SDK's broader interface.

## One complete exploration attempt

```js
// Run with the supplied tool Node and the owned attempt's environment.
const { spawnSync } = require('node:child_process');

const env = Object.freeze({ ...process.env });
for (const name of ['E2E_CONFIG', 'E2E_APP_URL', 'E2E_OUTPUT_DIR']) {
  if (!env[name]) throw new Error(`${name} must be fixed before opening this attempt`);
}
const cwd = process.cwd();
const locateQuery = JSON.parse(process.argv[2]); // e.g. {"role":"button","name":"Sign in"}
let session;
let primaryFailure;

function invoke(tool, args) {
  const result = spawnSync('mcporter', ['call', `e2e.${tool}`, '--args',
    JSON.stringify(args), '--output', 'text'], { env, cwd, encoding: 'utf8' });
  // Retain the actual response and exit before interpretation; do not log env/credentials.
  if (result.stdout) process.stdout.write(result.stdout);
  if (result.stderr) process.stderr.write(result.stderr);
  console.error(`e2e.${tool} exit=${result.status}`);
  if (result.error) throw result.error;
  // The locked CLI maps the original MCP isError to exit 1 before formatting.
  if (result.status !== 0) {
    throw new Error(`e2e.${tool} failed: exit=${result.status}; ${result.stdout}${result.stderr}`);
  }
  return result.stdout;
}

try {
  const opening = invoke('open_session', { config: env.E2E_CONFIG });
  const text = opening;
  // Only parse the SDK's opening id, never controls from observation text.
  session = /^Session ([0-9a-f-]+)\b/m.exec(text)?.[1];
  if (!session) throw new Error('open_session did not return the frozen Session <id> text');
  invoke('tools', { session });
  invoke('call', { session, tool: 'observe', args: {} });
  invoke('call', { session, tool: 'locate', args: locateQuery });
  // Add journey actions here using the actual catalog and latest observation.
} catch (error) {
  primaryFailure = error;
  throw error;
} finally {
  if (session) {
    try {
      invoke('close_session', { session });
    } catch (cleanupError) {
      if (!primaryFailure) throw cleanupError;
      console.error('Session cleanup also failed:', cleanupError);
    }
  }
}
```

The managed runtime fixes `MCPORTER_DAEMON_DIR` to this physical native execution at startup. Keep it unchanged for the whole attempt; subjobs inherit it. Connection environment/config identity distinguishes server connections, while this namespace distinguishes the owning daemon. The executor may stop explicitly owned service trees during an idle capacity handoff. A new physical execution or native recovery preserves application/history, not an existing browser handle or MCP process; open a new owned attempt rather than reusing its old handle. Never stop another execution's daemon.
