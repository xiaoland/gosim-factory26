import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { createSubagentObserver, factorySubagentObserver } from "../harness/extensions/factory-subagent-observer.ts";

function session(file, id) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, `${JSON.stringify({ type: "session", id })}\n`);
}

const root = fs.mkdtempSync(path.join(os.tmpdir(), "factory-pi-observer-"));
const home = path.join(root, "home");
const sessions = path.join(home, "sessions");
const parentAlias = path.join(home, "parent.jsonl");
const parentFile = path.join(sessions, "parent.jsonl");
const childA = path.join(home, "child-a.jsonl");
const childB = path.join(home, "child-b.jsonl");
session(parentAlias, "alias");
session(parentFile, "parent");
session(childA, "child-a");
session(childB, "child-b");

const observer = createSubagentObserver({
  nativeHome: home,
  getParentSessionId: () => "parent",
  getParentSessionFile: () => parentAlias,
  getParentSessionDir: () => sessions,
  now: () => 7,
});
assert.equal("stop" in observer, false);
assert.equal("fenced" in observer, false);
observer.observe({ details: { mode: "workflow", results: [
  { runId: "run", index: 0, agent: "executor", sessionFile: childA, artifactPaths: { outputPath: path.join(root, "a.md") }, state: "completed" },
  { runId: "run", index: 0, agent: "explorer", sessionFile: childB, state: "completed" },
] } });
let manifest = JSON.parse(fs.readFileSync(observer.manifestFile, "utf8"));
assert.equal(manifest.parent_session_file, parentFile);
assert.equal(manifest.diagnostic_status, "complete");
assert.deepEqual(manifest.children.map((child) => child.child_session_id).sort(), ["child-a", "child-b"]);
assert.ok(manifest.children.every((child) => child.evidence_source === "pi-subagents:passive-observer"));
assert.equal(manifest.children[0].artifact_paths.outputPath, path.join(root, "a.md"));

observer.observe({ asyncSnapshot: { runs: [{ id: "background", state: "running" }] } });
manifest = JSON.parse(fs.readFileSync(observer.manifestFile, "utf8"));
assert.equal(manifest.diagnostic_status, "partial");
assert.equal(manifest.children.find((child) => child.run_id === "background").association_status, "partial");

const hooks = new Map();
const nativeEvents = new Map();
const priorHome = process.env.PI_CODING_AGENT_DIR;
process.env.PI_CODING_AGENT_DIR = home;
try {
  factorySubagentObserver({
    on: (name, handler) => hooks.set(name, handler),
    events: { on: (name, handler) => nativeEvents.set(name, handler) },
  });
  assert.deepEqual([...hooks.keys()].sort(), ["session_start", "tool_result"]);
  hooks.get("session_start")({}, { sessionManager: {
    getSessionId: () => "parent",
    getSessionFile: () => parentAlias,
    getSessionDir: () => sessions,
  } });
  assert.ok(nativeEvents.has("subagent:process-terminal"));
} finally {
  if (priorHome === undefined) delete process.env.PI_CODING_AGENT_DIR;
  else process.env.PI_CODING_AGENT_DIR = priorHome;
}

console.log("pi passive observer checks passed");
