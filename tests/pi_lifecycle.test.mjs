import assert from "node:assert/strict";
import crypto from "node:crypto";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createLifecycleAdapter, factorySubagentLifecycle, RECEIPT_RELATIVE_PATH, REQUEST_RELATIVE_PATH } from "../harness/extensions/factory-subagent-lifecycle.ts";

const lockfile = fileURLToPath(new URL("../harness/npm/package-lock.json", import.meta.url));
const lockDigest = crypto.createHash("sha256").update(fs.readFileSync(lockfile)).digest("hex").slice(0, 16);
const piSubagentsRoot = process.env.PI_SUBAGENTS_ROOT
  ?? path.join(os.homedir(), ".cache", "factory26", `runtime-${lockDigest}`, "node_modules", "pi-subagents");
const piPackage = JSON.parse(fs.readFileSync(path.join(piSubagentsRoot, "package.json"), "utf8"));
assert.equal(piPackage.version, "0.56.0");

const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "factory-pi-lifecycle-"));
const home = path.join(tmp, "pi");
fs.mkdirSync(path.join(home, ".factory"), { recursive: true });
const parentSession = "parent-session";
const startedAt = 1700000000;
const request = { schema_version: 1, fence_id: "fence-1", parent_native_session_id: parentSession, started_at: startedAt };
fs.writeFileSync(path.join(home, REQUEST_RELATIVE_PATH), JSON.stringify(request));

function sessionFile(name, sessionId) {
  const file = path.join(home, name);
  fs.writeFileSync(file, `${JSON.stringify({ type: "session", sessionId })}\n`);
  return file;
}

async function stoppedChildren() {
  let tick = 0;
  const fgSessionFile = sessionFile("foreground.jsonl", "foreground-session");
  const bgSessionFile = sessionFile("background.jsonl", "background-session");
  const parentSessionFile = sessionFile("parent.jsonl", parentSession);
  const calls = [];
  const rpc = async (method, params = {}) => {
    calls.push([method, params]);
    if (method === "status" && !params.id) {
      return { text: tick ? "Run: fg-1\nState: remembered foreground\nSession: " + fgSessionFile : "Run: fg-1\nState: running", asyncSnapshot: { runs: [{ id: "bg-1", state: tick ? "stopped" : "running" }] } };
    }
    if (method === "stop" && params.id === "bg-1") return { runId: "bg-1", state: "stopping" };
    if (params.id === "fg-1") return tick ? { text: `Run: fg-1\nState: remembered foreground\nSession: ${fgSessionFile}` } : { text: `Run: fg-1\nState: running` };
    if (params.id === "bg-1") return tick ? { text: `Run: bg-1\nState: stopped\nSession: ${bgSessionFile}`, details: { lifecycleStatus: { processTerminal: { version: 1, state: "observed", runId: "bg-1", runnerProcessInstanceId: "bg-runner", observedAt: 1, instances: [{ kind: "runner", processInstanceId: "bg-runner" }], canonicalSession: { canonicalSessionId: crypto.createHash("sha256").update(fs.realpathSync(bgSessionFile)).digest("hex"), leaseDisposition: "released", freeAtObservation: true } } } } } : { text: "Run: bg-1\nState: running" };
    return {};
  };
  const adapter = createLifecycleAdapter({ nativeHome: home, getParentSessionId: () => parentSession, getParentSessionFile: () => parentSessionFile, rpc, now: () => tick * 1000, sleep: async () => { tick += 1; }, pollMs: 1, deadlineMs: 10_000 });
  adapter.observe({ details: { mode: "single", results: [{ agent: "executor", sessionFile: fgSessionFile, artifactPaths: { outputPath: path.join(home, "foreground-output.md") }, state: "running" }] }, runId: "fg-1", source: "foreground", state: "running", taskIndex: 0 });
  assert.equal(JSON.parse(fs.readFileSync(adapter.manifestFile)).parent_session_file, parentSessionFile);
  const promise = adapter.stop();
  assert.equal(adapter.fenced, true, "new tool calls are fenced before the first RPC reply");
  const receipt = await promise;
  assert.equal(receipt.state, "ready");
  assert.equal(receipt.children.length, 2);
  assert.equal(receipt.children.find((child) => child.run_id === "fg-1").proof.control_requested, true);
  assert.equal(receipt.children.find((child) => child.run_id === "bg-1").proof.process_terminal_observed, true);
  assert.equal(receipt.children.find((child) => child.run_id === "bg-1").proof.active_lease_released, true);
  assert.equal(receipt.children.find((child) => child.run_id === "fg-1").child_session_id, "foreground-session");
  assert.equal(receipt.children.find((child) => child.run_id === "fg-1").native_role, "executor");
  assert.equal(receipt.children.find((child) => child.run_id === "fg-1").artifact_paths.outputPath, path.join(home, "foreground-output.md"));
  assert.ok(calls.some(([method, params]) => method === "interrupt" && params.runId === "fg-1"));
  assert.ok(calls.some(([method, params]) => method === "stop" && params.id === "bg-1"));
  assert.equal(JSON.parse(fs.readFileSync(path.join(home, RECEIPT_RELATIVE_PATH))).state, "ready");
}

async function backgroundTerminalBoundary() {
  const childFile = sessionFile("terminal-child.jsonl", "terminal-child");
  const canonicalId = crypto.createHash("sha256").update(fs.realpathSync(childFile)).digest("hex");
  const valid = {
    version: 1, state: "observed", runId: "terminal-run", runnerProcessInstanceId: "runner-instance", observedAt: 1,
    instances: [{ kind: "runner", processInstanceId: "runner-instance", closeObservedAt: 1, exitCode: 0, signal: null }],
    canonicalSession: { canonicalSessionId: canonicalId, leaseDisposition: "released", freeAtObservation: true },
  };
  for (const [label, terminal, expected] of [
    ["unknown", { ...valid, state: "unknown" }, "unknown"],
    ["lease-owned", { ...valid, canonicalSession: { ...valid.canonicalSession, freeAtObservation: false } }, "unknown"],
    ["wrong-run", { ...valid, runId: "another-run" }, "unknown"],
    ["wrong-session", { ...valid, canonicalSession: { ...valid.canonicalSession, canonicalSessionId: "other" } }, "unknown"],
    ["missing-runner", { ...valid, instances: [] }, "unknown"],
    ["observed", valid, "ready"],
  ]) {
    const local = fs.mkdtempSync(path.join(os.tmpdir(), "factory-pi-terminal-"));
    fs.mkdirSync(path.join(local, ".factory"));
    fs.writeFileSync(path.join(local, REQUEST_RELATIVE_PATH), JSON.stringify({ ...request, fence_id: label }));
    let tick = 0;
    const adapter = createLifecycleAdapter({ nativeHome: local, getParentSessionId: () => parentSession,
      now: () => tick * 1000, sleep: async () => { tick += 1; }, deadlineMs: 2000,
      rpc: async (method, params = {}) => {
        if (method === "stop") return { runId: "terminal-run", state: "stopping" };
        if (!params.id) return { asyncSnapshot: { runs: [{ id: "terminal-run", state: "stopped" }] } };
        return { text: `Run: terminal-run\nState: stopped\nSession: ${childFile}`, details: { lifecycleStatus: { processTerminal: terminal } } };
      },
    });
    const receipt = await adapter.stop();
    assert.equal(receipt.state, expected, label);
    if (expected === "ready") assert.deepEqual(receipt.children[0].proof.process_terminal, valid);
  }
}

async function canonicalParentFileIsRefreshed() {
  const local = fs.mkdtempSync(path.join(os.tmpdir(), "factory-pi-parent-file-"));
  fs.mkdirSync(path.join(local, ".factory"), { recursive: true });
  fs.writeFileSync(path.join(local, REQUEST_RELATIVE_PATH), JSON.stringify({ schema_version: 1, fence_id: "parent-file-fence", parent_native_session_id: parentSession, started_at: 7 }));
  const firstFile = path.join(local, "sessions", "parent-a.jsonl");
  const secondFile = path.join(local, "sessions", "parent-b.jsonl");
  const listeners = new Map();
  const events = {
    on(name, handler) {
      const handlers = listeners.get(name) ?? [];
      handlers.push(handler);
      listeners.set(name, handlers);
      return () => listeners.set(name, handlers.filter((item) => item !== handler));
    },
    emit(name, value) {
      if (name !== "subagents:rpc:v1:request") return;
      for (const handler of listeners.get(`subagents:rpc:v1:reply:${value.requestId}`) ?? []) handler({ success: true, data: {} });
    },
  };
  const hooks = new Map();
  let command;
  const priorHome = process.env.PI_CODING_AGENT_DIR;
  process.env.PI_CODING_AGENT_DIR = local;
  try {
    factorySubagentLifecycle({ events, on: (name, handler) => hooks.set(name, handler), registerCommand: (_name, options) => { command = options; } });
    hooks.get("session_start")({}, { sessionManager: { getSessionId: () => parentSession, getSessionFile: () => firstFile } });
    assert.equal(JSON.parse(fs.readFileSync(path.join(local, ".factory", "session-tree.json"))).parent_session_file, firstFile);
    await command.handler("", { sessionManager: { getSessionId: () => parentSession, getSessionFile: () => secondFile } });
    assert.equal(JSON.parse(fs.readFileSync(path.join(local, ".factory", "session-tree.json"))).parent_session_file, secondFile);
  } finally {
    if (priorHome === undefined) delete process.env.PI_CODING_AGENT_DIR;
    else process.env.PI_CODING_AGENT_DIR = priorHome;
  }
}

async function canonicalParentSiblingWinsOverAlias() {
  const local = fs.mkdtempSync(path.join(os.tmpdir(), "factory-pi-parent-canonical-"));
  fs.mkdirSync(path.join(local, ".factory"), { recursive: true });
  const sessionDir = path.join(local, "sessions");
  fs.mkdirSync(sessionDir, { recursive: true });
  fs.writeFileSync(path.join(local, REQUEST_RELATIVE_PATH), JSON.stringify({ schema_version: 1, fence_id: "canonical-fence", parent_native_session_id: parentSession, started_at: 8 }));
  const alias = path.join(local, "parent.jsonl");
  const canonical = path.join(sessionDir, "parent.jsonl");
  fs.writeFileSync(alias, JSON.stringify({ type: "message", id: "alias-only" }) + "\n");
  const priorHome = process.env.PI_CODING_AGENT_DIR;
  process.env.PI_CODING_AGENT_DIR = local;
  try {
    const hooks = new Map();
    factorySubagentLifecycle({ events: { on: () => {}, emit: () => {} }, on: (name, handler) => hooks.set(name, handler), registerCommand: () => {} });
    const sessionManager = { getSessionId: () => parentSession, getSessionFile: () => alias, getSessionDir: () => sessionDir };
    hooks.get("session_start")({}, { sessionManager });
    fs.writeFileSync(canonical, JSON.stringify({ type: "session", version: 3, id: parentSession, cwd: local }) + "\n");
    hooks.get("tool_result")({ toolName: "subagent", details: {} });
    assert.equal(JSON.parse(fs.readFileSync(path.join(local, ".factory", "session-tree.json"))).parent_session_file, canonical);
  } finally {
    if (priorHome === undefined) delete process.env.PI_CODING_AGENT_DIR;
    else process.env.PI_CODING_AGENT_DIR = priorHome;
  }
}

async function workflowResultsAreRetained() {
  const local = fs.mkdtempSync(path.join(os.tmpdir(), "factory-pi-workflow-"));
  fs.mkdirSync(path.join(local, ".factory"), { recursive: true });
  fs.writeFileSync(path.join(local, REQUEST_RELATIVE_PATH), JSON.stringify({ schema_version: 1, fence_id: "workflow-fence", parent_native_session_id: parentSession, started_at: 6 }));
  const firstChildSessionFile = sessionFile("workflow-child-a.jsonl", "workflow-child-session-a");
  const secondChildSessionFile = sessionFile("workflow-child-b.jsonl", "workflow-child-session-b");
  const firstArtifactPath = path.join(local, "workflow-output-a.json");
  const secondArtifactPath = path.join(local, "workflow-output-b.json");
  let tick = 0;
  const calls = [];
  const adapter = createLifecycleAdapter({
    nativeHome: local,
    getParentSessionId: () => parentSession,
    rpc: async (method, params = {}) => {
      calls.push([method, params]);
      if (method === "status" && !params.id) return { text: tick ? "Run: workflow-1\nState: remembered foreground" : "Run: workflow-1\nState: running" };
      if (params.id === "workflow-1") return tick
        ? { text: `Run: workflow-1\nState: remembered foreground\nSession: ${firstChildSessionFile}` }
        : { text: "Run: workflow-1\nState: running" };
      return {};
    },
    now: () => tick * 1000,
    sleep: async () => { tick += 1; },
    pollMs: 1,
    deadlineMs: 10_000,
  });
  // This is the minimal redacted shape emitted by the real workflow tool result.
  adapter.observe({ details: { mode: "workflow", results: [
    { index: 0, agent: "browser-operator", sessionFile: firstChildSessionFile, artifactPaths: { outputPath: firstArtifactPath }, exitCode: 0, outputState: "present" },
    { index: 0, agent: "browser-operator", sessionFile: secondChildSessionFile, artifactPaths: { outputPath: secondArtifactPath }, exitCode: 0, outputState: "present" },
  ] }, runId: "workflow-1", source: "foreground" });
  const manifestChildren = JSON.parse(fs.readFileSync(path.join(local, ".factory", "session-tree.json"))).children;
  assert.deepEqual(manifestChildren.map((child) => child.child_session_id).sort(), ["workflow-child-session-a", "workflow-child-session-b"]);
  const receipt = await adapter.stop();
  assert.equal(receipt.state, "ready");
  assert.equal(receipt.children.length, 2);
  assert.deepEqual(receipt.children.map((child) => child.child_session_id).sort(), ["workflow-child-session-a", "workflow-child-session-b"]);
  assert.deepEqual(receipt.children.map((child) => child.native_role), ["browser-operator", "browser-operator"]);
  assert.deepEqual(receipt.children.map((child) => child.artifact_paths.outputPath).sort(), [firstArtifactPath, secondArtifactPath]);
  assert.equal(calls.filter(([method, params]) => method === "interrupt" && params.runId === "workflow-1").length, 1);
}

async function missingProofIsUnknown() {
  const local = fs.mkdtempSync(path.join(os.tmpdir(), "factory-pi-unknown-"));
  fs.mkdirSync(path.join(local, ".factory"), { recursive: true });
  fs.writeFileSync(path.join(local, REQUEST_RELATIVE_PATH), JSON.stringify({ schema_version: 1, fence_id: "fence-2", parent_native_session_id: parentSession, started_at: 2 }));
  let tick = 0;
  const adapter = createLifecycleAdapter({ nativeHome: local, getParentSessionId: () => parentSession, rpc: async (method, params = {}) => {
    if (method === "status" && !params.id) return { asyncSnapshot: { runs: [{ id: "bg-2", state: "running" }] } };
    if (params.id === "bg-2") return { text: "Run: bg-2\nState: stopped", details: { lifecycleStatus: { processTerminal: { state: "unknown", reason: "observer-unavailable" } } } };
    return {};
  }, now: () => tick * 1000, sleep: async () => { tick += 1; }, pollMs: 1, deadlineMs: 2_000 });
  const receipt = await adapter.stop();
  assert.equal(receipt.state, "unknown");
  assert.equal(receipt.error.code, "background_control_failed");
}

async function foregroundCanHandOffBeforeSessionIdentityIsPublished() {
  const local = fs.mkdtempSync(path.join(os.tmpdir(), "factory-pi-live-foreground-"));
  fs.mkdirSync(path.join(local, ".factory"), { recursive: true });
  fs.writeFileSync(path.join(local, REQUEST_RELATIVE_PATH), JSON.stringify({ schema_version: 1, fence_id: "live-foreground", parent_native_session_id: parentSession, started_at: 3 }));
  const adapter = createLifecycleAdapter({
    nativeHome: local,
    getParentSessionId: () => parentSession,
    rpc: async (method, params = {}) => {
      if (method === "status") return { text: "Run: live-fg\nState: running" };
      if (method === "interrupt" && params.runId === "live-fg") return { text: "Interrupt requested" };
      return {};
    },
    deadlineMs: 1_000,
  });
  const receipt = await adapter.stop();
  assert.equal(receipt.state, "ready");
  assert.equal(receipt.children[0].run_id, "live-fg");
  assert.equal(receipt.children[0].proof.control_requested, true);
  assert.equal(receipt.children[0].child_session_id, undefined);
}

async function directForegroundCompletionIsObserved() {
  const local = fs.mkdtempSync(path.join(os.tmpdir(), "factory-pi-direct-completion-"));
  fs.mkdirSync(path.join(local, ".factory"), { recursive: true });
  fs.writeFileSync(path.join(local, REQUEST_RELATIVE_PATH), JSON.stringify({ schema_version: 1, fence_id: "direct-fence", parent_native_session_id: parentSession, started_at: 9 }));
  const childFile = path.join(local, "direct-child.jsonl");
  fs.writeFileSync(childFile, JSON.stringify({ type: "session", id: "direct-child-session" }) + "\n");
  const adapter = createLifecycleAdapter({
    nativeHome: local,
    getParentSessionId: () => parentSession,
    rpc: async (method, params = {}) => {
      if (params.id === "direct-run") return { text: `Run: direct-run\nState: remembered foreground\nSession: ${childFile}` };
      return {};
    },
  });
  adapter.observe({ runId: "direct-run", source: "foreground", state: "interrupted", taskIndex: 0, agent: "executor", sessionFile: childFile });
  const receipt = await adapter.stop();
  assert.equal(receipt.state, "ready");
  assert.equal(receipt.children.length, 1);
  assert.equal(receipt.children[0].child_session_id, "direct-child-session");
  assert.deepEqual(receipt.children[0].proof, { control_inactive: true });
}

async function invalidChildHeaderIsNotIdentity() {
  const local = fs.mkdtempSync(path.join(os.tmpdir(), "factory-pi-invalid-header-"));
  fs.mkdirSync(path.join(local, ".factory"), { recursive: true });
  const invalid = path.join(local, "message.jsonl");
  fs.writeFileSync(invalid, JSON.stringify({ type: "message", id: "not-a-session-id" }) + "\n");
  const adapter = createLifecycleAdapter({ nativeHome: local, getParentSessionId: () => parentSession });
  adapter.observe({ details: { mode: "single", results: [{ agent: "executor", sessionFile: invalid }] }, runId: "invalid-header", source: "foreground" });
  const child = JSON.parse(fs.readFileSync(path.join(local, ".factory", "session-tree.json"))).children[0];
  assert.equal(child.child_session_id, undefined, "message IDs must not become child session identities");
}

async function identityAndReplacementAreUnknown() {
  const local = fs.mkdtempSync(path.join(os.tmpdir(), "factory-pi-identity-"));
  fs.mkdirSync(path.join(local, ".factory"), { recursive: true });
  const file = path.join(local, REQUEST_RELATIVE_PATH);
  fs.writeFileSync(file, JSON.stringify({ schema_version: 1, fence_id: "fence-3", parent_native_session_id: parentSession, started_at: 3 }));
  const mismatch = createLifecycleAdapter({ nativeHome: local, getParentSessionId: () => "other", rpc: async () => { throw new Error("must not call RPC"); } });
  assert.equal((await mismatch.stop()).state, "unknown");
  fs.writeFileSync(file, JSON.stringify({ schema_version: 1, fence_id: "fence-4", parent_native_session_id: parentSession, started_at: 4 }));
  const replaced = createLifecycleAdapter({ nativeHome: local, getParentSessionId: () => parentSession, rpc: async () => { fs.writeFileSync(file, JSON.stringify({ schema_version: 1, fence_id: "new", parent_native_session_id: parentSession, started_at: 5 })); return {}; } });
  const receipt = await replaced.stop();
  assert.equal(receipt.state, "unknown");
  assert.equal(receipt.error.code, "request_replaced");
  assert.equal(JSON.parse(fs.readFileSync(path.join(local, RECEIPT_RELATIVE_PATH))).fence_id, "fence-3", "a stale controller cannot overwrite the replacement receipt");
}

await backgroundTerminalBoundary();
await stoppedChildren();
await canonicalParentFileIsRefreshed();
await canonicalParentSiblingWinsOverAlias();
await workflowResultsAreRetained();
await missingProofIsUnknown();
await foregroundCanHandOffBeforeSessionIdentityIsPublished();
await directForegroundCompletionIsObserved();
await invalidChildHeaderIsNotIdentity();
await identityAndReplacementAreUnknown();
console.log("pi lifecycle checks passed");
