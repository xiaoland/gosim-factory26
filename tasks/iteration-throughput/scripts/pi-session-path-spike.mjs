#!/usr/bin/env node
// Reproduction probe: RPC state/new_session plus an isolated extension command.
// It never sends a model prompt; the only prompt is the local extension command.
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import assert from "node:assert/strict";
import { pathToFileURL } from "node:url";
const runtime = path.resolve(process.argv[2]);
const lifecycle = process.argv[3] && path.resolve(process.argv[3]);
const { RpcClient } = await import(pathToFileURL(path.join(runtime, "node_modules/@earendil-works/pi-coding-agent/dist/modes/rpc/rpc-client.js")));

const dir = fs.mkdtempSync(path.join(os.tmpdir(), "pi-session-path-spike."));
const extension = path.join(dir, "probe.mjs");
const output = path.join(dir, "probe.json");
fs.writeFileSync(extension, `export default function probe(pi) {
  pi.registerCommand("probe-session-path", { handler: async (_args, ctx) => {
    const sm = ctx.sessionManager;
    const file = sm.getSessionFile();
    const sessionDir = sm.getSessionDir();
    sm.appendMessage({ role: "assistant", content: [{ type: "text", text: "session-path-probe" }], timestamp: Date.now() });
    const fs = await import("node:fs/promises");
    await fs.writeFile(process.env.PI_PROBE_OUT, JSON.stringify({
      observedAt: new Date().toISOString(), getSessionFile: sm.getSessionFile(),
      getSessionDir: sessionDir, beforeAppendFile: file
    }));
  }});
}`);

const cliPath = path.join(runtime, "node_modules/@earendil-works/pi-coding-agent/dist/cli.js");
const client = new RpcClient({
  cliPath, cwd: dir,
  args: ["--no-extensions", ...(lifecycle ? ["--extension", path.join(runtime, "node_modules/pi-subagents/index.ts"), "--extension", lifecycle] : []), "--session-dir", dir, "--extension", extension, "--no-skills", "--no-prompt-templates", "--no-themes", "--no-context-files", "--no-approve"],
  env: { HOME: dir, PI_CODING_AGENT_DIR: dir, PI_OFFLINE: "1", PI_TELEMETRY: "0", PI_PROBE_OUT: output }
});
await client.start();
try {
const before = await client.getState();
const newSession = await client.newSession();
const after = await client.getState();
await client.prompt("/probe-session-path");
for (let n = 0; !fs.existsSync(output) && n < 50; n++) await new Promise(resolve => setTimeout(resolve, 100));
const extensionResult = JSON.parse(fs.readFileSync(output, "utf8"));
const exists = fs.existsSync(after.sessionFile);
const lineCount = exists ? fs.readFileSync(after.sessionFile, "utf8").trim().split("\n").length : null;
assert.equal(newSession.cancelled, false);
assert.equal(after.sessionFile, extensionResult.getSessionFile);
assert.equal(extensionResult.getSessionDir, dir);
assert.equal(exists, true);
console.log(JSON.stringify({
  extensions: lifecycle ? ["pi-subagents", "factory-lifecycle", "probe"] : ["probe"],
  capturedAt: new Date().toISOString(), dir,
  before: { sessionId: before.sessionId, sessionFile: before.sessionFile },
  newSession, after: { sessionId: after.sessionId, sessionFile: after.sessionFile },
  extension: extensionResult, physical: { exists, lineCount }
}, null, 2));
} finally { await client.stop(); }
