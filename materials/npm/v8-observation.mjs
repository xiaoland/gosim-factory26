import fs from "node:fs";
import path from "node:path";
import { Session } from "node:inspector";
import { PerformanceObserver } from "node:perf_hooks";

const started = Symbol.for("factory26.v8-observation.v1");
const clock = () => ({ realtime_ns: (BigInt(Date.now()) * 1_000_000n).toString(), monotonic_ns: process.hrtime.bigint().toString() });
const errorRecord = (error) => ({ type: error.name, message: error.message, code: error.code });

/** Observe the managed Pi itself; child application Node processes are separate owners. */
export function startV8Observation() {
  const directory = process.env.FACTORY_NATIVE_EXECUTION_DIR;
  const executionId = process.env.FACTORY_NATIVE_EXECUTION_ID;
  if (!directory || !executionId || process.env.FACTORY_NATIVE_START_ID !== executionId || globalThis[started]) return;
  globalThis[started] = true;
  const folder = path.join(directory, "v8");
  const metrics = path.join(folder, "memory.jsonl");
  let descriptor, bytes = 0, capped = false, failed = false;
  const birth = () => {
    try { return fs.readFileSync(`/proc/${process.pid}/stat`, "utf8").split(")").slice(1).join(")").trim().split(/\s+/)[19]; }
    catch { return null; }
  };
  const readIdentity = (name, link = false) => {
    try { return link ? fs.readlinkSync(name) : fs.readFileSync(name, "utf8").trim(); }
    catch { return null; }
  };
  const identity = { pid: process.pid, starttime: birth(), execution_id: executionId, node_version: process.version,
    boot_id: readIdentity("/proc/sys/kernel/random/boot_id"),
    pid_namespace: readIdentity(`/proc/${process.pid}/ns/pid`, true),
    cgroup_namespace: readIdentity(`/proc/${process.pid}/ns/cgroup`, true) };
  const reportError = (error) => { if (!failed) process.stderr.write(`V8 observation failed: ${JSON.stringify(errorRecord(error))}\n`); failed = true; };
  const emit = (kind, data = {}) => {
    if (capped || failed) return;
    try {
      const line = `${JSON.stringify({ schema_version: 1, ...clock(), ...identity, kind, ...data })}\n`;
      if (bytes + Buffer.byteLength(line) > 8 * 1024 * 1024 - 4096) {
        fs.writeSync(descriptor, `${JSON.stringify({ kind: "log_capped", ...identity, ...clock(), cap_bytes: 8 * 1024 * 1024 })}\n`);
        capped = true; return;
      }
      bytes += fs.writeSync(descriptor, line);
    } catch (error) { reportError(error); }
  };
  try {
    fs.mkdirSync(folder, { recursive: true, mode: 0o700 });
    // Each physical execution owns its file; reuse must not overwrite prior evidence.
    descriptor = fs.openSync(metrics, "wx", 0o600);
  } catch (error) { reportError(error); return; }
  const memory = (phase) => emit("v8_memory", { phase, ...process.memoryUsage() });
  memory("startup");
  const interval = setInterval(() => memory("periodic"), 1000);
  interval.unref();
  const gc = new PerformanceObserver((list) => {
    for (const entry of list.getEntries()) emit("v8_gc", { start_time_ms: entry.startTime, duration_ms: entry.duration, detail: entry.detail });
  });
  gc.observe({ entryTypes: ["gc"] });

  let session, active = false, stopped = false;
  const seconds = Number(process.env.FACTORY_V8_PROFILE_SECONDS ?? "0");
  const selection = process.env.FACTORY_V8_PROFILE_EXECUTION;
  const post = (method, params, callback) => session.post(method, params, callback);
  const finish = (reason) => {
    if (!active || stopped) return;
    stopped = true;
    post("HeapProfiler.stopSampling", {}, (error, result) => {
      try {
        if (error) throw error;
        const profile = JSON.stringify(result.profile);
        if (Buffer.byteLength(profile) > 32 * 1024 * 1024) {
          emit("v8_profile_incomplete", { reason: "profile_exceeds_32MiB", stop_reason: reason });
        } else {
          fs.writeFileSync(path.join(folder, "allocation.heapprofile"), profile, { flag: "wx", mode: 0o600 });
          emit("v8_profile_completed", { stop_reason: reason, profile: "allocation.heapprofile", bytes: Buffer.byteLength(profile) });
        }
      } catch (error) { emit("v8_profile_error", { phase: "stop", error: errorRecord(error) }); }
      finally { active = false; session.disconnect(); }
    });
  };
  if (!Number.isFinite(seconds) || seconds < 0 || seconds > 300) {
    emit("v8_profile_error", { phase: "configuration", message: "FACTORY_V8_PROFILE_SECONDS must be between 0 and 300" });
  } else if (seconds > 0 && (!selection || selection === executionId)) {
    session = new Session();
    try {
      session.connect();
      post("HeapProfiler.startSampling", {
        samplingInterval: 512 * 1024,
        includeObjectsCollectedByMajorGC: true,
        includeObjectsCollectedByMinorGC: true,
      }, (error) => {
        if (error) { emit("v8_profile_error", { phase: "start", error: errorRecord(error) }); session.disconnect(); return; }
        active = true;
        emit("v8_profile_started", { duration_seconds: seconds, sampling_interval_bytes: 512 * 1024, include_collected_objects: true });
        const timer = setTimeout(() => finish("window_complete"), seconds * 1000);
        timer.unref();
      });
    } catch (error) { emit("v8_profile_error", { phase: "start", error: errorRecord(error) }); session.disconnect(); }
  }
  process.once("exit", () => {
    finish("process_exit"); memory("exit");
    gc.disconnect(); clearInterval(interval);
    try { fs.fsyncSync(descriptor); fs.closeSync(descriptor); } catch (error) { reportError(error); }
  });
}
