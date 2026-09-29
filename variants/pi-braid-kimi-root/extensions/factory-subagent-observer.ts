import fs from "node:fs";
import os from "node:os";
import path from "node:path";

export const MANIFEST_RELATIVE_PATH = path.join(".factory", "session-tree.json");

type JsonObject = Record<string, unknown>;

type Child = {
	mode: "foreground" | "background";
	runId: string;
	childId?: string;
	parentSessionId?: string;
	childSessionId?: string;
	sessionFile?: string;
	artifactPaths?: Record<string, string>;
	nativeRole?: string;
	status?: string;
};

type ObserverOptions = {
	nativeHome?: string;
	getParentSessionId?: () => string | undefined;
	getParentSessionFile?: () => string | undefined;
	getParentSessionDir?: () => string | undefined;
	getParentCwd?: () => string | undefined;
	now?: () => number;
};

function object(value: unknown): JsonObject | undefined {
	return value && typeof value === "object" && !Array.isArray(value) ? value as JsonObject : undefined;
}

function items(value: unknown): unknown[] {
	return Array.isArray(value) ? value : [];
}

function string(value: unknown): string | undefined {
	return typeof value === "string" && value ? value : undefined;
}

function stringMap(value: unknown): Record<string, string> | undefined {
	const source = object(value);
	if (!source) return undefined;
	const result = Object.fromEntries(Object.entries(source).filter((entry): entry is [string, string] => typeof entry[1] === "string"));
	return Object.keys(result).length ? result : undefined;
}

function sessionId(file: string | undefined): string | undefined {
	if (!file) return undefined;
	try {
		const header = object(JSON.parse(fs.readFileSync(file, "utf8").split(/\r?\n/, 1)[0]));
		if (header?.type !== "session") return undefined;
		return string(header.sessionId ?? header.session_id ?? header.id);
	} catch {
		return undefined;
	}
}

function writeJson(file: string, value: unknown): void {
	fs.mkdirSync(path.dirname(file), { recursive: true });
	const temporary = `${file}.${process.pid}.tmp`;
	fs.writeFileSync(temporary, `${JSON.stringify(value, null, 2)}\n`);
	fs.renameSync(temporary, file);
}

export function createSubagentObserver(options: ObserverOptions = {}) {
	const nativeHome = options.nativeHome ?? process.env.PI_CODING_AGENT_DIR;
	if (!nativeHome) throw new Error("PI_CODING_AGENT_DIR is required for Factory subagent observation.");
	const manifestFile = path.join(nativeHome, MANIFEST_RELATIVE_PATH);
	const children: Child[] = [];
	const parentSession = options.getParentSessionId ?? (() => undefined);
	const parentSessionFile = options.getParentSessionFile ?? (() => undefined);
	const parentSessionDir = options.getParentSessionDir ?? (() => undefined);
	const parentCwd = options.getParentCwd ?? (() => undefined);
	const now = options.now ?? (() => Date.now());

	const canonicalParentFile = (): string | undefined => {
		const reported = string(parentSessionFile());
		const parent = string(parentSession());
		if (!reported || !parent || sessionId(reported) === parent) return reported;
		const directory = string(parentSessionDir());
		if (!directory) return reported;
		const canonical = path.join(directory, path.basename(reported));
		return sessionId(canonical) === parent ? canonical : reported;
	};

	const merge = (next: Child): void => {
		let current = next.sessionFile
			? children.find((child) => child.runId === next.runId && child.sessionFile === next.sessionFile)
			: undefined;
		current ??= children.find((child) => child.runId === next.runId
			&& (!next.sessionFile || !child.sessionFile)
			&& ((next.childId && child.childId === next.childId) || (!child.sessionFile && !child.childId)));
		if (!current) {
			current = { mode: next.mode, runId: next.runId };
			children.push(current);
		}
		Object.assign(current, Object.fromEntries(Object.entries(next).filter(([, value]) => value !== undefined)));
		current.childSessionId ??= sessionId(current.sessionFile);
	};

	const collect = (value: unknown, inheritedMode?: Child["mode"]): void => {
		const root = object(value);
		if (!root) return;
		const mode = (string(root.mode ?? root.source) === "background" ? "background" : inheritedMode ?? "foreground");
		const runId = string(root.runId ?? root.id);
		if (runId) merge({
			mode,
			runId,
			childId: root.index === undefined && root.taskIndex === undefined ? undefined : String(root.index ?? root.taskIndex),
			parentSessionId: string(root.parentSessionId ?? root.parent_session_id) ?? parentSession(),
			sessionFile: string(root.sessionFile),
			artifactPaths: stringMap(root.artifactPaths),
			nativeRole: string(root.agent),
			status: string(root.state ?? root.status),
		});
		for (const result of items(root.results)) collect(result, "foreground");
		const snapshot = object(root.asyncSnapshot);
		for (const run of items(snapshot?.runs ?? root.runs)) collect(run, "background");
		for (const child of items(root.children)) collect(child, mode);
		if (root.details) collect(root.details, mode);
	};

	const writeManifest = (): void => {
		const parent = parentSession();
		const projected = children.map((child) => ({
			mode: child.mode,
			run_id: child.runId,
			...(child.childId ? { child_id: child.childId } : {}),
			...(child.parentSessionId ? { parent_session_id: child.parentSessionId } : {}),
			...(child.childSessionId ? { child_session_id: child.childSessionId } : {}),
			...(child.sessionFile ? { session_file: child.sessionFile } : {}),
			...(child.artifactPaths ? { artifact_paths: child.artifactPaths } : {}),
			...(child.nativeRole ? { native_role: child.nativeRole } : {}),
			status: child.status ?? "unknown",
			association_status: child.parentSessionId && child.childSessionId && child.sessionFile ? "complete" : "partial",
			evidence_source: "pi-subagents:passive-observer",
		}));
		const diagnosticStatus = !parent ? "unknown" : projected.some((child) => child.association_status !== "complete") ? "partial" : "complete";
		const file = canonicalParentFile();
		writeJson(manifestFile, {
			schema_version: 1,
			diagnostic_status: diagnosticStatus,
			...(parent ? { parent_native_session_id: parent } : {}),
			...(parentCwd() ? { parent_cwd: parentCwd() } : {}),
			...(file ? { parent_session_file: file } : {}),
			updated_at: now(),
			children: projected,
		});
	};

	return {
		manifestFile,
		observe(value: unknown): void {
			collect(value);
			writeManifest();
		},
	};
}

type PreviousRun = {
	id: string; role: string; parent: string; home: string; updatedAt: number;
	artifacts: Array<{ role: string; childId?: string; paths: Record<string, string> }>;
};

function readObject(file: string): JsonObject | undefined {
	try { return object(JSON.parse(fs.readFileSync(file, "utf8"))); } catch { return undefined; }
}

function previousCwd(home: string, manifest: JsonObject): string | undefined {
	const stored = string(manifest.parent_cwd);
	if (stored) return stored;
	const file = string(manifest.parent_session_file);
	if (!file || path.dirname(file) !== home) return undefined;
	const sessions = path.join(home, "sessions");
	try {
		for (const entry of fs.readdirSync(sessions, { withFileTypes: true })) {
			if (!entry.isDirectory()) continue;
			const canonical = path.join(sessions, entry.name, path.basename(file));
			try {
				const fd = fs.openSync(canonical, "r");
				const buffer = Buffer.alloc(4096);
				let length: number;
				try { length = fs.readSync(fd, buffer, 0, buffer.length, 0); } finally { fs.closeSync(fd); }
				const header = JSON.parse(buffer.toString("utf8", 0, length).split(/\r?\n/, 1)[0]);
				if (header.type === "session" && (header.id === manifest.parent_native_session_id || header.sessionId === manifest.parent_native_session_id)) return string(header.cwd);
			} catch { /* Continue to other session directories. */ }
		}
	} catch { /* An old native home may have been only partially archived. */ }
	return undefined;
}

function previousRuns(nativeHome: string, cwd: string, currentSession: string | undefined): PreviousRun[] {
	const root = path.dirname(nativeHome);
	const found = new Map<string, PreviousRun>();
	let homes: string[];
	try { homes = fs.readdirSync(root); } catch { return []; }
	for (const name of homes) {
		const home = path.join(root, name);
		if (home === nativeHome) continue;
		const manifest = readObject(path.join(home, MANIFEST_RELATIVE_PATH));
		if (!manifest || !items(manifest.children).length || previousCwd(home, manifest) !== cwd) continue;
		const parent = string(manifest.parent_native_session_id);
		if (!parent || parent === currentSession) continue;
		for (const value of items(manifest.children)) {
			const child = object(value);
			const id = string(child?.run_id);
			if (!id || !/^[0-9a-f]{8}-[0-9a-f-]{27}$/i.test(id)) continue;
			const role = string(child?.native_role) ?? "unknown";
			const updatedAt = Number(manifest.updated_at) || 0;
			let run = found.get(id);
			if (!run || updatedAt > run.updatedAt) {
				run = { id, role, parent, home, updatedAt, artifacts: [] };
				found.set(id, run);
			}
			if (run.home === home) {
				if (run.role === "unknown" && role !== "unknown") run.role = role;
				run.artifacts.push({ role, childId: string(child?.child_id), paths: stringMap(child?.artifact_paths) ?? {} });
			}
		}
	}
	return [...found.values()].sort((a, b) => b.updatedAt - a.updatedAt);
}

function savedOutcome(run: PreviousRun): string | undefined {
	const outcomes: string[] = [];
	for (const artifact of run.artifacts) {
		const base = `${run.id}_${artifact.role}${artifact.childId === undefined ? "" : `_${artifact.childId}`}`;
		const file = artifact.paths.metadataPath ?? path.join(run.home, "subagent-artifacts", `${base}_meta.json`);
		const meta = readObject(file);
		if (!meta) continue;
		const exit = meta.exitCode;
		outcomes.push(`${artifact.role}${artifact.childId === undefined ? "" : `#${artifact.childId}`} ${exit === 0 ? "completed" : typeof exit === "number" ? `exit ${exit}` : "metadata present"}${string(meta.error) ? ` (${string(meta.error)!.slice(0, 160)})` : ""}: ${file}`);
	}
	return outcomes.length ? outcomes.join("; ") : undefined;
}

function tempRoot(): string {
	return process.env.PI_SUBAGENTS_TEMP_ROOT
		? path.resolve(process.env.PI_SUBAGENTS_TEMP_ROOT)
		: path.join(os.tmpdir(), `pi-subagents-uid-${process.getuid?.() ?? 0}`);
}

function nativeStatus(runId: string): { state: string; dir: string; updated?: string } | undefined {
	const dir = path.join(tempRoot(), "async-subagent-runs", runId);
	const status = readObject(path.join(dir, "status.json"));
	if (!status || status.runId !== runId) return undefined;
	return { state: string(status.state) ?? "unknown", dir, ...(typeof status.lastUpdate === "number" ? { updated: new Date(status.lastUpdate).toISOString() } : {}) };
}

function nativeResult(runId: string): { state: string; file: string } | undefined {
	const file = path.join(tempRoot(), "async-subagent-results", `${runId}.json`);
	const result = readObject(file);
	if (!result || (result.runId !== runId && result.id !== runId)) return undefined;
	const state = string(result.state) ?? (result.success === true ? "complete" : result.success === false ? "failed" : "unknown");
	return { state, file };
}

function handoffLine(run: PreviousRun): string {
	const status = nativeStatus(run.id);
	const result = nativeResult(run.id);
	const artifact = savedOutcome(run);
	const state = result && ["complete", "failed", "paused", "stopped", "rejected"].includes(result.state)
		? `native result ${result.state}`
		: status ? `native status ${status.state}${status.updated ? ` at ${status.updated}` : ""}` : "native status unavailable (unknown after cold restore)";
	return `- ${run.role} ${run.id} (parent ${run.parent}): ${state}${artifact ? `; ${artifact}` : ""}; artifacts ${path.join(run.home, "subagent-artifacts")}; inspect subagent({action:"status",id:"${run.id}"}).`;
}

export function factorySubagentObserver(pi: {
	on: (event: string, handler: (value: any, context?: any) => void) => void;
	events: { on: (event: string, handler: (value: unknown) => void) => unknown };
	sendMessage: (message: { customType: string; content: string; display: boolean }, options: { triggerTurn: boolean }) => void;
}): void {
	type SessionManager = { getSessionId?: () => string | undefined; getSessionFile?: () => string | undefined; getSessionDir?: () => string | undefined };
	let manager: SessionManager | undefined;
	let cwd: string | undefined;
	let observer: ReturnType<typeof createSubagentObserver> | undefined;
	let handoff: PreviousRun[] = [];
	let introduced = false;
	let activeSession: string | undefined;
	const watchers: fs.FSWatcher[] = [];
	const delivered = new Set<string>();
	const checks = new Map<string, () => void>();
	const closeWatchers = () => { for (const watcher of watchers.splice(0)) watcher.close(); };
	const current = () => observer ??= createSubagentObserver({
		getParentSessionId: () => manager?.getSessionId?.(),
		getParentSessionFile: () => manager?.getSessionFile?.(),
		getParentSessionDir: () => manager?.getSessionDir?.(),
		getParentCwd: () => cwd,
	});
	pi.on("session_start", (_event, context) => {
		closeWatchers();
		delivered.clear();
		checks.clear();
		introduced = false;
		manager = context?.sessionManager;
		activeSession = manager?.getSessionId?.();
		cwd = string(context?.cwd);
		observer = undefined;
		current().observe({});
		const nativeHome = process.env.PI_CODING_AGENT_DIR;
		handoff = nativeHome && cwd ? previousRuns(nativeHome, cwd, manager?.getSessionId?.()) : [];
		if (nativeHome && handoff.length) {
			const index = path.join(nativeHome, ".factory", "previous-subagents.json");
			writeJson(index, { cwd, runs: handoff.map(({ id, role, parent, home, artifacts }) => ({ run_id: id, role, parent_session_id: parent, native_home: home, artifacts })) });
		}
		for (const run of handoff) {
			const initial = nativeStatus(run.id);
			const priorResult = nativeResult(run.id);
			if (!initial || !["queued", "running"].includes(initial.state)
				|| (priorResult && ["complete", "failed", "paused", "stopped", "rejected"].includes(priorResult.state))) continue;
			try {
				const ownerSession = activeSession;
				const check = () => {
					if (activeSession !== ownerSession || delivered.has(run.id)) return;
					const status = nativeStatus(run.id);
					const result = nativeResult(run.id);
					const terminal = result && ["complete", "failed", "paused", "stopped", "rejected"].includes(result.state) ? result.state : status?.state;
					if (!terminal || !["complete", "failed", "paused", "stopped", "rejected"].includes(terminal)) return;
					try {
						pi.sendMessage({ customType: "factory-subagent-handoff", content: `Earlier subagent reached ${terminal}: ${handoffLine(run)}${result ? `; native result ${result.file}` : ""}`, display: true }, { triggerTurn: true });
						delivered.add(run.id);
					} catch (error) { console.error(`Failed to deliver previous subagent ${run.id}:`, error); }
				};
				checks.set(run.id, check);
				const watcher = fs.watch(initial.dir, { persistent: false }, (_event, name) => {
					if (!name || name === "status.json" || name === "process-terminal.json") check();
				});
				watcher.on("error", (error) => console.error(`Previous subagent watch failed for ${run.id}:`, error));
				watchers.push(watcher);
				check();
			} catch (error) { console.error(`Failed to watch previous subagent ${run.id}:`, error); }
		}
		if (checks.size) {
			try {
				const watcher = fs.watch(path.join(tempRoot(), "async-subagent-results"), { persistent: false }, (_event, name) => {
					if (!name) { for (const check of checks.values()) check(); return; }
					checks.get(String(name).replace(/\.json$/, ""))?.();
				});
				watcher.on("error", (error) => console.error("Previous subagent result watch failed:", error));
				watchers.push(watcher);
			} catch { /* Status-directory watches remain authoritative. */ }
		}
	});
	pi.on("before_agent_start", () => {
		if (introduced || !handoff.length) return;
		introduced = true;
		const currentHome = process.env.PI_CODING_AGENT_DIR;
		const index = currentHome ? path.join(currentHome, ".factory", "previous-subagents.json") : "(unavailable)";
		return { message: { customType: "factory-subagent-handoff", content: `Previous native subagent runs for this same worktree (verify before re-delegating a write task). Showing ${Math.min(handoff.length, 8)}/${handoff.length}; full UUID index: ${index}\n${handoff.slice(0, 8).map(handoffLine).join("\n")}`, display: true } };
	});
	pi.on("session_shutdown", () => { activeSession = undefined; closeWatchers(); checks.clear(); handoff = []; });
	pi.on("tool_result", (event, context) => {
		manager = context?.sessionManager ?? manager;
		if (event?.toolName === "subagent") current().observe(event);
		// Keep the native result; explain the separate bash job namespace at the failed call.
		if (event?.toolName !== "subagent_wait") return;
		const content = event.content ?? [];
		const text = content.filter((part: any) => part.type === "text").map((part: any) => part.text).join("\n");
		const id = event.input?.id;
		const bashJob = typeof id === "string" && /^bg\d+$/.test(id);
		const missingJob = bashJob && text.includes(`No active run matched "${id}". Nothing to wait for.`);
		const empty = !id && text.includes("No active async runs or registered provider work in this session. Nothing to wait for.");
		if (!missingJob && !empty) return;
		const hint = missingJob
			? `${id} is a Pi Background Bash job, not a native subagent run. For early progress use pbb status ${id} or pbb tail ${id}.`
			: "subagent_wait only waits for native subagent or registered provider work; it does not cover bash bg* jobs. Use pbb status/tail if you need their early progress.";
		return { content: [...content, { type: "text", text: `${hint} Bash completion messages arrive automatically. Continue independent work; if only waiting remains, end this response so completion can wake you. Do not create another sleep-and-poll bash job.` }] };
	});
	for (const event of ["subagent:async-started", "subagent:control-event", "subagent:foreground-complete", "subagent:process-terminal"])
		pi.events.on(event, (value) => current().observe(value));
}

export default factorySubagentObserver;
