import { spawn, spawnSync } from "node:child_process";
import { randomUUID } from "node:crypto";
import * as fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { startV8Observation } from "./v8-observation.mjs";

if (process.argv[1] && path.resolve(process.argv[1]) !== fileURLToPath(import.meta.url)) startV8Observation();

const providers = globalThis[Symbol.for("factory26.native-managed-providers.v1")] ??= new Map();
// The upstream user-wide daemon can serve several live native owners. A
// stoppable service must instead belong to this exact execution namespace.
if (process.env.FACTORY_NATIVE_EXECUTION_DIR && process.env.FACTORY_NATIVE_EXECUTION_ID) {
  process.env.MCPORTER_DAEMON_DIR = path.join(process.env.FACTORY_NATIVE_EXECUTION_DIR, "mcporter");
}
const pause = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const diagnostic = (error) => error instanceof Error ? error.message : String(error);
const readJson = (file) => JSON.parse(fs.readFileSync(file, "utf8"));

function writeJson(file, value) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  const temporary = `${file}.${process.pid}.${randomUUID()}.tmp`;
  fs.writeFileSync(temporary, `${JSON.stringify(value)}\n`, { mode: 0o600 });
  fs.renameSync(temporary, file);
}

function helper(args, env = process.env) {
  if (!env.FACTORY_RESOURCE_HELPER || !env.FACTORY_RESOURCE_PYTHON) throw new Error("Managed runtime resource helper is unavailable.");
  const result = spawnSync(env.FACTORY_RESOURCE_PYTHON, [env.FACTORY_RESOURCE_HELPER, ...args], { env, encoding: "utf8", timeout: 10_000, maxBuffer: 64 * 1024 });
  if (result.error || result.status !== 0) throw new Error(result.error ? diagnostic(result.error) : result.stderr.trim() || `Resource helper exited ${result.status}.`);
  return JSON.parse(result.stdout);
}

/** The launcher registers immutable process ownership before exec. */
export function spawnManaged(command, args, options, metadata = {}) {
  const env = options.env ?? process.env;
  if (!env.FACTORY_RESOURCE_HELPER) return spawn(command, args, options);
  const startId = randomUUID();
  const launchArgs = [env.FACTORY_RESOURCE_HELPER, "launch", "--start-id", startId, "--kind", metadata.kind ?? "tool"];
  if (metadata.manifest) launchArgs.push("--manifest", metadata.manifest);
  if (metadata.service) launchArgs.push("--service");
  launchArgs.push("--", command, ...args);
  const child = spawn(env.FACTORY_RESOURCE_PYTHON, launchArgs, { ...options, detached: true, env });
  child.managedStartId = startId;
  child.managedResourceDirectory = env.FACTORY_RESOURCE_DIR;
  child.managedStartReceipt = path.join(env.FACTORY_RESOURCE_DIR, "starts", `${startId}.json`);
  return child;
}

/** Wait without blocking the Pi event loop; callers attach stdout/error/close first. */
export async function waitManagedStartup(child, timeoutMs = 30_000) {
  if (!child?.managedStartReceipt) return { status: "started", unmanaged: true };
  child.managedStartup ??= (async () => {
    const deadline = Date.now() + timeoutMs;
    while (Date.now() < deadline) {
      try {
        const start = readJson(child.managedStartReceipt);
        if (start.status !== "started") throw new Error(`Managed process did not start: ${JSON.stringify(start)}`);
        child.managedProcessRecord = start.process_record;
        return start;
      } catch (error) { if (error.code !== "ENOENT") throw error; }
      if ((child.exitCode !== null && child.exitCode !== undefined) ||
          (child.signalCode !== null && child.signalCode !== undefined)) {
        throw new Error(`Managed launcher exited before publishing a start receipt: ${child.managedStartReceipt}.`);
      }
      await pause(10);
    }
    child.once("error", () => {});
    child.kill("SIGKILL");
    throw new Error(`Managed launcher did not publish a start receipt: ${child.managedStartReceipt}.`);
  })();
  return child.managedStartup;
}

export function registerManagedProvider(name, snapshot, stopServices) {
  const provider = { snapshot, stopServices };
  providers.set(name, provider);
  return () => { if (providers.get(name) === provider) providers.delete(name); };
}

function execution(env = process.env) {
  const directory = env.FACTORY_NATIVE_EXECUTION_DIR;
  const id = env.FACTORY_NATIVE_EXECUTION_ID;
  if (!directory || !id) throw new Error("Native execution identity is unavailable.");
  return { directory, id };
}

function records(directory, id) {
  const entries = fs.readdirSync(path.join(directory, "processes"));
  return entries.filter((name) => name.endsWith(".json")).map((name) => {
    const record = readJson(path.join(directory, "processes", name));
    if (record.schema_version !== 1 || record.execution_id !== id || !Number.isInteger(record.pid) || !Number.isInteger(record.pgid) || !Number.isInteger(record.starttime) || !record.boot_id || !record.start_id) {
      throw new Error(`Invalid native ownership record: ${name}.`);
    }
    return { ...record, ownership_path: path.join(directory, "processes", name) };
  });
}

function processIdentity(pid) {
  try {
    const raw = fs.readFileSync(`/proc/${pid}/stat`, "utf8");
    const fields = raw.slice(raw.lastIndexOf(")") + 2).split(" ");
    return { pid, state: fields[0], pgid: Number(fields[2]), starttime: Number(fields[19]) };
  } catch (error) {
    if (error.code === "ENOENT" || error.code === "ESRCH") return undefined;
    throw error;
  }
}

function ownedProcesses(ownership, id, skipPid, allExecution = false) {
  if (process.platform !== "linux") throw new Error("Native stop verification requires Linux /proc process identities.");
  const bootId = fs.readFileSync("/proc/sys/kernel/random/boot_id", "utf8").trim();
  if (ownership.some((record) => record.boot_id !== bootId)) throw new Error("Native ownership belongs to another boot identity.");
  const all = [];
  for (const name of fs.readdirSync("/proc")) {
    if (!/^\d+$/.test(name)) continue;
    const identity = processIdentity(Number(name));
    if (!identity || identity.state === "Z" || identity.state === "X") continue;
    let owner;
    let startId;
    try {
      // Read only ownership markers; no environment content enters a receipt.
      const entries = fs.readFileSync(`/proc/${name}/environ`).toString().split("\0");
      owner = entries.find((entry) => entry.startsWith("FACTORY_NATIVE_EXECUTION_ID="))?.slice("FACTORY_NATIVE_EXECUTION_ID=".length);
      startId = entries.find((entry) => entry.startsWith("FACTORY_NATIVE_START_ID="))?.slice("FACTORY_NATIVE_START_ID=".length);
    } catch (error) {
      if (error.code !== "ENOENT" && error.code !== "ESRCH" && error.code !== "EACCES") throw error;
    }
    all.push({ ...identity, owner, startId });
  }
  const ownGroups = new Set();
  for (const record of ownership) {
    const leader = all.find((item) => item.pid === record.pid);
    if (leader && leader.starttime !== record.starttime) {
      let previous;
      try { previous = readJson(path.join(path.dirname(path.dirname(record.ownership_path)), "terminals", `${record.start_id}.json`)); }
      catch (error) { if (error.code !== "ENOENT") throw error; }
      if (previous?.start_id === record.start_id && previous.execution_id === id && previous.terminal?.status === "stopped") continue;
      throw new Error(`Native PID identity conflict for ${record.start_id}.`);
    }
    if (leader?.starttime === record.starttime && leader.pgid === record.pgid) ownGroups.add(record.pgid);
    else if (leader && leader.owner === id) throw new Error(`Native PID identity conflict for ${record.start_id}.`);
    else {
      const members = all.filter((item) => item.pgid === record.pgid);
      if (members.length && !members.every((item) => item.owner === id)) throw new Error(`Unverified surviving process group ${record.pgid}.`);
      if (members.length) ownGroups.add(record.pgid);
    }
  }
  const startIds = new Set(ownership.map((record) => record.start_id));
  return all.filter((item) => item.pid !== skipPid && (ownGroups.has(item.pgid) || (item.owner === id && (allExecution || startIds.has(item.startId)))));
}

function ownedDescendants(ownership, startId) {
  const selected = new Set([startId]);
  for (let previous = -1; previous !== selected.size;) {
    previous = selected.size;
    for (const record of ownership) if (selected.has(record.parent_start_id)) selected.add(record.start_id);
  }
  return ownership.filter((record) => selected.has(record.start_id));
}

function signalExact(identity, signal) {
  const current = processIdentity(identity.pid);
  if (!current || current.state === "Z") return;
  if (current.starttime !== identity.starttime) throw new Error(`PID ${identity.pid} changed birth identity before ${signal}.`);
  try { process.kill(identity.pid, signal); }
  catch (error) { if (error.code !== "ESRCH") throw error; }
}

async function stopRecords(ownership, id, skipPid, allExecution = false, directory = execution().directory) {
  const roots = ownership.map((record) => record.start_id);
  const collect = () => {
    const current = records(directory, id);
    const selected = allExecution ? current : [...new Map(roots.flatMap((root) => ownedDescendants(current, root)).map((record) => [record.start_id, record])).values()];
    return ownedProcesses(selected, id, skipPid, allExecution);
  };
  let active = collect();
  for (const item of active) signalExact(item, "SIGTERM");
  const deadline = Date.now() + 3000;
  while (active.length && Date.now() < deadline) { await pause(25); active = collect(); }
  for (const item of active) signalExact(item, "SIGKILL");
  const killDeadline = Date.now() + 1000;
  while (active.length && Date.now() < killDeadline) { await pause(25); active = collect(); }
  if (active.length) throw new Error(`Owned execution remains active: ${active.map((item) => item.pid).join(", ")}.`);
  // Admission has been fenced; repeat the observation after signals settle.
  await pause(25);
  if (collect().length) throw new Error("Owned execution became active during stop verification.");
}

export function managedState(session = {}) {
  try {
    const { directory, id } = execution();
    if (fs.existsSync(path.join(directory, "stopping.json"))) return { status: "unknown", reason: "execution_stopping", execution_id: id };
    const ownership = records(directory, id);
    if (session.isStreaming || session.isCompacting || session.pendingMessageCount > 0) return { status: "busy", reason: "native_turn_or_messages", execution_id: id };
    if (ownedProcesses(ownership, id, process.pid, true).length) return { status: "busy", reason: "owned_process_active", execution_id: id };
    for (const [name, provider] of providers) {
      const state = provider.snapshot();
      if (state.status !== "quiescent") return { status: state.status, reason: `${name}: ${state.reason ?? state.status}`.slice(0, 512), execution_id: id };
    }
    return { status: "quiescent", execution_id: id };
  } catch (error) { return { status: "unknown", reason: diagnostic(error).slice(0, 512), execution_id: process.env.FACTORY_NATIVE_EXECUTION_ID ?? "unavailable" }; }
}

/** Yield only declared services after finite/native obligations are empty. */
export async function yieldStoppableServices(session = {}) {
  try {
    const { directory, id } = execution();
    if (session.isStreaming || session.isCompacting || session.pendingMessageCount > 0) return managedState(session);
    if (fs.existsSync(path.join(directory, "stopping.json"))) return managedState(session);
    const serviceProviders = [];
    for (const [name, provider] of providers) {
      const state = provider.snapshot();
      if (state.status === "quiescent") continue;
      if (!state.services_only || typeof provider.stopServices !== "function") {
        return { status: state.status, reason: `${name}: ${state.reason ?? state.status}`, execution_id: id };
      }
      serviceProviders.push(provider);
    }
    const ownership = records(directory, id);
    const serviceRoots = ownership.filter((record) => record.service === true);
    const serviceRecords = [...new Map(serviceRoots.flatMap((root) => ownedDescendants(ownership, root.start_id)).map((record) => [record.start_id, record])).values()];
    const covered = new Set(ownedProcesses(serviceRecords, id, process.pid).map((item) => item.pid));
    const active = ownedProcesses(ownership, id, process.pid, true);
    if (active.some((item) => !covered.has(item.pid))) return { status: "busy", reason: "finite_or_unclassified_owned_process", execution_id: id };
    for (const provider of serviceProviders) await provider.stopServices();
    await stopRecords(serviceRoots, id, process.pid, false, directory);
    const verifiedAt = Date.now();
    for (const record of serviceRecords) {
      const terminalPath = path.join(directory, "terminals", `${record.start_id}.json`);
      let previous;
      try { previous = readJson(terminalPath); } catch (error) { if (error.code !== "ENOENT") throw error; }
      writeJson(terminalPath, {
        start_id: record.start_id, execution_id: id,
        close: previous?.close ?? { observation: "capacity_service_handoff", observed_at: verifiedAt },
        terminal: { status: "stopped", verified_at: verifiedAt },
      });
    }
    const state = managedState(session);
    writeJson(path.join(directory, "service-handoff.json"), { ...state, service_start_ids: serviceRoots.map((record) => record.start_id), verified_at: verifiedAt });
    return state;
  } catch (error) { return { status: "unknown", reason: diagnostic(error).slice(0, 1024), execution_id: process.env.FACTORY_NATIVE_EXECUTION_ID ?? "unavailable" }; }
}

export async function cleanupOwnedExecution(options = {}) {
  let receiptPath;
  try {
    const { directory, id } = options.directory ? { directory: options.directory, id: options.id } : execution();
    if (!id) throw new Error("Native cleanup requires an execution identity.");
    const self = options.skipSelf ? records(directory, id).find((record) => record.pid === process.pid) : undefined;
    if (self?.parent_start_id) throw new Error("Nested native RPC cleanup requires its own subtree fence; execution cleanup belongs to the root owner.");
    helper(["fence", "--execution-dir", directory, "--execution-id", id]);
    receiptPath = path.join(directory, options.skipSelf ? "children-stop.json" : "execution-stop.json");
    const ownership = records(directory, id);
    await stopRecords(ownership, id, process.pid, true, directory);
    const result = { status: "stopped", execution_id: id, verified_at: Date.now(), coverage: "registered-process-groups-and-inherited-execution-markers", receipt_path: receiptPath };
    writeJson(receiptPath, result);
    return result;
  } catch (error) {
    const result = { status: "unknown", reason: diagnostic(error).slice(0, 1024), ...(receiptPath ? { receipt_path: receiptPath } : {}) };
    if (receiptPath) writeJson(receiptPath, result);
    return result;
  }
}

/** Raw close observations are separate from the proof that the owned group stopped. */
export async function finishManagedProcess(child, close) {
  if (!child.managedProcessRecord) return undefined;
  const record = readJson(child.managedProcessRecord);
  const { directory, id } = execution();
  let terminal;
  try { await stopRecords(ownedDescendants(records(directory, id), record.start_id), id, process.pid); terminal = { status: "stopped", verified_at: Date.now() }; }
  catch (error) { terminal = { status: "unknown", reason: diagnostic(error) }; }
  const terminalPath = path.join(directory, "terminals", `${record.start_id}.json`);
  let previous;
  try { previous = readJson(terminalPath); } catch (error) { if (error.code !== "ENOENT") throw error; }
  writeJson(terminalPath, { start_id: record.start_id, execution_id: id, close: close.observation ? previous?.close ?? close : close, terminal });
  return terminal;
}

export function createManagedProcessTreeController(child) {
  if (!child.managedProcessRecord) return undefined;
  let terminal;
  const terminate = () => terminal ??= (async () => {
    const result = await finishManagedProcess(child, { observation: "cleanup_requested", observed_at: Date.now() });
    return result?.status === "stopped"
      ? { state: "observed", mechanism: "posix-process-group", processGroupId: child.pid, verifiedAt: Date.now() }
      : { state: "unknown", reason: "verification-failed", diagnostic: result?.reason ?? "Managed process record unavailable." };
  })();
  return { terminate, finishAfterWriterClose: terminate };
}

export function publishChildStartup(manifestDirectory, status, reason) {
  if (!process.env.FACTORY_NATIVE_EXECUTION_DIR || !manifestDirectory) return;
  writeJson(path.join(manifestDirectory, "native-child-startup.json"), { status, reason, execution_id: process.env.FACTORY_NATIVE_EXECUTION_ID, observed_at: Date.now() });
}

export async function waitChildStartup(manifestDirectory, timeoutMs) {
  const file = path.join(manifestDirectory, "native-child-startup.json");
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    try { return readJson(file); }
    catch (error) { if (error.code !== "ENOENT") throw error; }
    await pause(10);
  }
  throw new Error(`Async child did not confirm physical startup within ${timeoutMs}ms: ${file}.`);
}

// Process management is installed by this module; it does not alter model prompts.
export default function managedProcessExtension() {}

globalThis[Symbol.for("factory26.native-runtime.v1")] = { spawnManaged, waitManagedStartup, finishManagedProcess, createManagedProcessTreeController, registerManagedProvider, publishChildStartup, waitChildStartup };

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const args = process.argv.slice(2);
  const argument = (name) => args[args.indexOf(name) + 1];
  if (args[0] !== "cleanup" || !args.includes("--execution-dir") || !args.includes("--execution-id")) throw new Error("Usage: native-managed.mjs cleanup --execution-dir DIR --execution-id ID");
  console.log(JSON.stringify(await cleanupOwnedExecution({ directory: argument("--execution-dir"), id: argument("--execution-id") })));
}
