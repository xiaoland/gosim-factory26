import * as fs from "node:fs";
import * as path from "node:path";
import { randomUUID } from "node:crypto";

export const COMMAND_NAME = "factory-subagent-stop";
export const REQUEST_RELATIVE_PATH = path.join(".factory", "teardown-request.json");
export const RECEIPT_RELATIVE_PATH = path.join(".factory", "subagent-stop.json");
export const MANIFEST_RELATIVE_PATH = path.join(".factory", "session-tree.json");
export const CONTROL_DEADLINE_MS = 180_000;

type Json = null | boolean | number | string | Json[] | { [key: string]: Json };
type RpcMethod = "status" | "interrupt" | "stop";

export interface TeardownRequest {
	version?: number;
	schema_version?: number;
	fence_id: string;
	parent_native_session_id: string;
	started_at: Json;
}

export interface ChildProof {
	control_inactive?: boolean;
	status_terminal?: boolean;
	process_terminal_observed?: boolean;
	active_lease_released?: boolean;
}

export interface ChildEvidence {
	mode: "foreground" | "background";
	run_id: string;
	child_id?: string;
	parent_session_id: string;
	child_session_id?: string;
	session_file?: string;
	artifact_paths?: Record<string, string>;
	native_role?: string;
	status: string;
	proof: ChildProof;
	evidence_source: string;
}

export interface StopReceipt {
	schema_version: 1;
	state: "stopped" | "unknown";
	fence_id: string;
	parent_native_session_id: string;
	started_at: Json;
	completed_at: number;
	children: ChildEvidence[];
	error?: { code: string; message: string };
}

interface KnownChild {
	mode: "foreground" | "background";
	runId: string;
	childId?: string;
	parentSessionId: string;
	childSessionId?: string;
	sessionFile?: string;
	artifactPaths?: Record<string, string>;
	nativeRole?: string;
	status?: string;
	asyncDir?: string;
	processTerminal?: Record<string, unknown>;
	controlInactive?: boolean;
}

interface LifecycleOptions {
	nativeHome?: string;
	deadlineMs?: number;
	pollMs?: number;
	now?: () => number;
	sleep?: (ms: number) => Promise<void>;
	getParentSessionId?: () => string | undefined;
	getParentSessionFile?: () => string | undefined;
	getParentSessionDir?: () => string | undefined;
	rpc?: (method: RpcMethod, params?: Record<string, unknown>) => Promise<unknown>;
	rpcWithDeadline?: (method: RpcMethod, params: Record<string, unknown> | undefined, remainingMs: number) => Promise<unknown>;
	readJson?: (file: string) => unknown;
	writeJson?: (file: string, value: unknown) => void;
}

interface EventBus {
	on(event: string, handler: (value: unknown) => void): (() => void) | void;
	emit(event: string, value: unknown): void;
}

function record(value: unknown): Record<string, unknown> | undefined {
	return value && typeof value === "object" && !Array.isArray(value) ? value as Record<string, unknown> : undefined;
}

function string(value: unknown): string | undefined {
	return typeof value === "string" && value.trim() ? value.trim() : undefined;
}

function array(value: unknown): unknown[] {
	return Array.isArray(value) ? value : [];
}

function stringMap(value: unknown): Record<string, string> | undefined {
	const input = record(value);
	if (!input) return undefined;
	const output = Object.fromEntries(Object.entries(input).filter(([, item]) => typeof item === "string")) as Record<string, string>;
	return Object.keys(output).length ? output : undefined;
}

function jsonEqual(left: unknown, right: unknown): boolean {
	return JSON.stringify(left) === JSON.stringify(right);
}

function readJsonFile(file: string): unknown {
	return JSON.parse(fs.readFileSync(file, "utf8"));
}

function writeJsonFile(file: string, value: unknown): void {
	fs.mkdirSync(path.dirname(file), { recursive: true });
	const tmp = `${file}.${process.pid}.${randomUUID()}.tmp`;
	fs.writeFileSync(tmp, `${JSON.stringify(value, null, 2)}\n`, "utf8");
	fs.renameSync(tmp, file);
}

function requestIdentity(value: unknown): Pick<TeardownRequest, "fence_id" | "parent_native_session_id" | "started_at"> | undefined {
	const input = record(value);
	const fenceId = string(input?.fence_id);
	const parent = string(input?.parent_native_session_id);
	if (!fenceId || !parent || input?.started_at === undefined) return undefined;
	return { fence_id: fenceId, parent_native_session_id: parent, started_at: input.started_at as Json };
}

function statusPayload(value: unknown): Record<string, unknown> {
	const root = record(value) ?? {};
	const details = record(root.details);
	return { ...root, ...(details ?? {}) };
}

function parseStatusText(value: unknown): { runId?: string; state?: string; sessionFile?: string; processTerminal?: string; asyncDir?: string } {
	const root = record(value) ?? {};
	const text = string(root.text) ?? string(root.message) ?? "";
	const line = (name: string): string | undefined => string(text.match(new RegExp(`^${name}:\\s*(.+)$`, "m"))?.[1]);
	return {
		runId: line("Run"),
		state: line("State"),
		sessionFile: line("Session"),
		processTerminal: line("Process terminal"),
		asyncDir: line("Dir"),
	};
}

function sessionIdFromFile(file: string | undefined): string | undefined {
	if (!file) return undefined;
	try {
		const first = fs.readFileSync(file, "utf8").split(/\r?\n/, 1)[0];
		const header = record(JSON.parse(first));
		if (header?.type !== "session") return undefined;
		return string(header?.sessionId ?? header?.session_id ?? header?.id);
	} catch {
		return undefined;
	}
}

function processProof(value: unknown): ChildProof {
	const terminal = record(value);
	const canonical = record(terminal?.canonicalSession);
	const lease = canonical?.leaseDisposition === "released" || canonical?.leaseDisposition === "not-held" || canonical?.canonicalSessionLeaseReleased === true;
	return {
		status_terminal: terminal?.state === "observed" ? true : undefined,
		process_terminal_observed: terminal?.state === "observed",
		active_lease_released: lease || undefined,
	};
}

function isActive(state: unknown): boolean {
	return state === "running" || state === "queued" || state === "pending";
}

function isTerminal(state: unknown): boolean {
	return state === "complete" || state === "completed" || state === "failed" || state === "paused" || state === "stopped" || state === "rejected" || state === "remembered foreground";
}

function addChild(target: Map<string, KnownChild>, input: Partial<KnownChild> & { runId?: string; parentSessionId?: string }): void {
	const runId = string(input.runId);
	const parentSessionId = string(input.parentSessionId);
	if (!runId || !parentSessionId) return;
	let key = `${input.mode ?? "background"}:${runId}:${input.childId ?? ""}`;
	let prior = target.get(key);
	if (prior && input.sessionFile && prior.sessionFile && prior.sessionFile !== input.sessionFile) {
		// Workflow results may reuse a local index for separate runs. Their
		// explicit session files are the durable identity available at this point.
		key = `${key}:${input.sessionFile}`;
		prior = target.get(key);
	}
	if (!prior && input.childId === undefined) {
		const sameRun = [...target.entries()].filter(([candidateKey, candidate]) =>
			candidate.mode === (input.mode ?? "background") && candidate.runId === runId && candidate.childId !== undefined && candidateKey.startsWith(`${input.mode ?? "background"}:${runId}:`));
		if (sameRun.length === 1) {
			[key, prior] = sameRun[0];
		} else if (sameRun.length > 1) {
			// A run-level status line cannot identify one child in a parallel
			// foreground run; do not invent an extra child record.
			return;
		}
	}
	if (!prior && input.childId !== undefined) {
		const unscopedKey = `${input.mode ?? "background"}:${runId}:`;
		prior = target.get(unscopedKey);
		if (prior) {
			target.delete(unscopedKey);
			key = `${input.mode ?? "background"}:${runId}:${input.childId}`;
		}
	}
	const child = prior ?? { mode: input.mode ?? "background", runId, parentSessionId };
	child.mode = input.mode ?? child.mode;
	child.runId = runId;
	child.parentSessionId = parentSessionId;
	if (input.childId !== undefined) child.childId = input.childId;
	if (input.childSessionId !== undefined) child.childSessionId = input.childSessionId;
	if (input.sessionFile !== undefined) child.sessionFile = input.sessionFile;
	if (!child.childSessionId && child.sessionFile) child.childSessionId = sessionIdFromFile(child.sessionFile);
	if (input.artifactPaths !== undefined) child.artifactPaths = input.artifactPaths;
	if (input.nativeRole !== undefined) child.nativeRole = input.nativeRole;
	if (input.status !== undefined) child.status = input.status;
	if (input.asyncDir !== undefined) child.asyncDir = input.asyncDir;
	if (input.processTerminal !== undefined) child.processTerminal = input.processTerminal;
	if (input.controlInactive !== undefined) child.controlInactive = input.controlInactive;
	target.set(key, child);
}

function collectChildren(statusValue: unknown, parentSessionId: string, known: Map<string, KnownChild>): void {
	const root = statusPayload(statusValue);
	const event = record(root.event);
	const eventRunId = string(event?.runId);
	const directRunId = string(root.runId ?? root.id) ?? eventRunId;
	const eventSource = string(event?.source ?? root.source);
	if (directRunId && root.asyncDir) addChild(known, { mode: "background", runId: directRunId, parentSessionId, status: string(root.state) ?? "running", asyncDir: string(root.asyncDir), nativeRole: string(root.agent) });
	const processTerminal = record(root.processTerminal) ?? (root.state === "observed" && string(root.runnerProcessInstanceId) ? root : undefined);
	if (directRunId && processTerminal) addChild(known, { mode: "background", runId: directRunId, parentSessionId, status: "complete", processTerminal, nativeRole: string(root.agent) });
	if (directRunId && eventSource === "foreground") {
		const foreground = event ?? root;
		const state = string(foreground.state) ?? "running";
		addChild(known, { mode: "foreground", runId: directRunId, parentSessionId, childId: foreground.taskIndex === undefined ? undefined : String(foreground.taskIndex), status: state, sessionFile: string(foreground.sessionFile ?? root.sessionFile), nativeRole: string(foreground.agent ?? root.agent), controlInactive: !isActive(state) });
	}
	const textStatus = parseStatusText(root);
	if (textStatus.runId && textStatus.state === "running") {
		const mode = textStatus.asyncDir || textStatus.processTerminal ? "background" : "foreground";
		addChild(known, { mode, runId: textStatus.runId, parentSessionId, status: "running", asyncDir: textStatus.asyncDir, nativeRole: string(root.agent), controlInactive: mode === "foreground" ? false : undefined });
	}
	const foreground = array(root.foregroundRuns);
	for (const runValue of foreground) {
		const run = record(runValue);
		if (!run) continue;
		const runId = string(run.runId ?? run.id);
		if (!runId) continue;
		const state = string(run.state ?? run.status) ?? "unknown";
		const children = array(run.children);
		if (children.length === 0) addChild(known, { mode: "foreground", runId, parentSessionId, status: state, nativeRole: string(run.agent), controlInactive: !isActive(state) });
		for (const childValue of children) {
			const child = record(childValue);
			if (!child) continue;
			addChild(known, {
				mode: "foreground", runId, parentSessionId,
				childId: child.index === undefined ? undefined : String(child.index),
				childSessionId: string(child.sessionId), sessionFile: string(child.sessionFile),
				artifactPaths: stringMap(child.artifactPaths),
				nativeRole: string(child.agent),
				status: string(child.status) ?? state, controlInactive: !isActive(state),
			});
		}
	}
	// Foreground tool results carry the durable child evidence in
	// details.results. The completion event carries sessionFile but does not
	// repeat artifactPaths, so merge both projections by run/index.
	for (const [resultIndex, resultValue] of array(root.results).entries()) {
		const result = record(resultValue);
		if (!result) continue;
		const runId = string(result.runId ?? root.runId ?? root.id);
		if (!runId) continue;
		const childState = string(result.state ?? result.status) ?? string(root.state) ?? "unknown";
		addChild(known, {
			mode: "foreground",
			runId,
			parentSessionId,
			childId: String(result.index ?? result.taskIndex ?? resultIndex),
			status: childState,
			sessionFile: string(result.sessionFile),
			artifactPaths: stringMap(result.artifactPaths),
			nativeRole: string(result.agent),
			controlInactive: !isActive(childState),
		});
	}
	const snapshot = record(root.asyncSnapshot);
	for (const runValue of array(snapshot?.runs ?? root.runs)) {
		const run = record(runValue);
		if (!run) continue;
		const runId = string(run.id ?? run.runId);
		if (!runId) continue;
		const state = string(run.state ?? run.status) ?? "unknown";
		addChild(known, { mode: "background", runId, parentSessionId, status: state, asyncDir: string(run.asyncDir), nativeRole: string(run.agent) });
		for (const nested of array(run.children)) {
			const child = record(nested);
			if (!child) continue;
			const nestedId = string(child.id ?? child.runId);
			if (!nestedId) continue;
			addChild(known, { mode: "background", runId, childId: nestedId, parentSessionId, status: string(child.state ?? child.status) ?? "unknown", sessionFile: string(child.sessionFile), nativeRole: string(child.agent) });
		}
	}
}

function childReceipt(child: KnownChild): ChildEvidence {
	const proof = child.mode === "foreground"
		? { control_inactive: child.controlInactive === true }
		: processProof(child.processTerminal);
	return {
		mode: child.mode,
		run_id: child.runId,
		...(child.childId ? { child_id: child.childId } : {}),
		parent_session_id: child.parentSessionId,
		...(child.childSessionId ? { child_session_id: child.childSessionId } : {}),
		...(child.sessionFile ? { session_file: child.sessionFile } : {}),
		...(child.artifactPaths && Object.keys(child.artifactPaths).length ? { artifact_paths: child.artifactPaths } : {}),
		...(child.nativeRole ? { native_role: child.nativeRole } : {}),
		status: child.status ?? "unknown",
		proof,
		evidence_source: child.mode === "foreground" ? "pi-subagents:status/foregroundRuns" : "pi-subagents:status/processTerminal",
	};
}

function proofComplete(child: KnownChild): boolean {
	if (!child.childSessionId) return false;
	if (child.mode === "foreground") return child.controlInactive === true;
	const proof = processProof(child.processTerminal);
	return isTerminal(child.status) && proof.process_terminal_observed === true && proof.active_lease_released === true;
}

export function createLifecycleAdapter(options: LifecycleOptions = {}) {
	const nativeHome = options.nativeHome ?? process.env.PI_CODING_AGENT_DIR;
	if (!nativeHome) throw new Error("PI_CODING_AGENT_DIR is required for Factory subagent lifecycle control.");
	const requestFile = path.join(nativeHome, REQUEST_RELATIVE_PATH);
	const receiptFile = path.join(nativeHome, RECEIPT_RELATIVE_PATH);
	const manifestFile = path.join(nativeHome, MANIFEST_RELATIVE_PATH);
	const now = options.now ?? (() => Date.now());
	const sleep = options.sleep ?? ((ms: number) => new Promise<void>((resolve) => setTimeout(resolve, ms)));
	const readJson = options.readJson ?? readJsonFile;
	const writeJson = options.writeJson ?? writeJsonFile;
	const deadlineMs = options.deadlineMs ?? CONTROL_DEADLINE_MS;
	const pollMs = options.pollMs ?? 100;
	const parentSession = options.getParentSessionId ?? (() => undefined);
	const parentSessionFile = options.getParentSessionFile ?? (() => undefined);
	const parentSessionDir = options.getParentSessionDir ?? (() => undefined);
	const known = new Map<string, KnownChild>();
	let fenced = false;

	const readRequest = (): TeardownRequest => {
		const value = readJson(requestFile);
		const identity = requestIdentity(value);
		if (!identity) throw new Error("invalid teardown request identity");
		return { ...identity, schema_version: record(value)?.schema_version as number | undefined, version: record(value)?.version as number | undefined };
	};
	const sessionHeaderMatches = (file: string, sessionId: string | undefined): boolean => {
		if (!sessionId) return false;
		try {
			const first = fs.readFileSync(file, "utf8").split(/\r?\n/, 1)[0];
			const header = record(JSON.parse(first));
			return header?.type === "session" && header.id === sessionId;
		} catch {
			return false;
		}
	};
	const resolveParentSessionFile = (): string | undefined => {
		const reported = string(parentSessionFile());
		const sessionId = string(parentSession());
		if (!reported || !sessionId) return reported;
		if (sessionHeaderMatches(reported, sessionId)) return reported;
		const dir = string(parentSessionDir());
		if (dir) {
			const canonical = path.join(dir, path.basename(reported));
			if (canonical !== reported && sessionHeaderMatches(canonical, sessionId)) return canonical;
		}
		return reported;
	};
	const writeManifest = (): void => {
		const sessionFile = resolveParentSessionFile();
		writeJson(manifestFile, {
			schema_version: 1,
			parent_native_session_id: parentSession(),
			...(sessionFile ? { parent_session_file: sessionFile } : {}),
			updated_at: now(),
			children: [...known.values()].map(childReceipt),
		});
	};
	const sameRequest = (request: TeardownRequest): boolean => {
		const current = requestIdentity(readJson(requestFile));
		return Boolean(current && current.fence_id === request.fence_id && current.parent_native_session_id === request.parent_native_session_id && jsonEqual(current.started_at, request.started_at));
	};

	const observe = (value: unknown): void => {
		collectChildren(value, parentSession() ?? "", known);
		writeManifest();
	};
	const updateChild = (child: KnownChild, value: unknown): void => {
		const root = statusPayload(value);
		const textStatus = parseStatusText(root);
		if (textStatus.state) child.status = textStatus.state;
		if (textStatus.sessionFile && !child.sessionFile) child.sessionFile = textStatus.sessionFile;
		if (textStatus.asyncDir) child.asyncDir = textStatus.asyncDir;
		if (!child.nativeRole) child.nativeRole = string(root.agent);
		const lifecycle = record(record(root.lifecycleStatus)?.processTerminal) ?? record(root.processTerminal);
		if (lifecycle) child.processTerminal = lifecycle;
		if (child.sessionFile) child.childSessionId = child.childSessionId ?? sessionIdFromFile(child.sessionFile);
		if (child.mode === "foreground") child.controlInactive = child.status !== "running";
	};
	const statusParams = (child: KnownChild): Record<string, unknown> => ({ id: child.runId });

	const stop = async (): Promise<StopReceipt> => {
		const started = now();
		const deadlineAt = started + deadlineMs;
		const existing = (() => {
			try { return readJson(receiptFile) as StopReceipt; } catch { return undefined; }
		})();
		const request = readRequest();
		const currentParent = parentSession();
		if (!currentParent || currentParent !== request.parent_native_session_id) return finish(request, "unknown", [], { code: "parent_identity_mismatch", message: "Teardown request parent does not match the active Pi session." });
		if (existing && existing.schema_version === 1 && existing.fence_id === request.fence_id && existing.parent_native_session_id === currentParent && jsonEqual(existing.started_at, request.started_at)) return existing;
		fenced = true;
		if (!sameRequest(request)) return finish(request, "unknown", [], { code: "request_replaced", message: "Teardown request changed before lifecycle control began." });
		const rpc = options.rpc;
		if (!rpc && !options.rpcWithDeadline) return finish(request, "unknown", [], { code: "rpc_unavailable", message: "Pi subagent RPC bridge is unavailable." });
		const callRpc = async (method: RpcMethod, params?: Record<string, unknown>): Promise<unknown> => {
			const remainingMs = deadlineAt - now();
			if (remainingMs <= 0) throw new Error("control_deadline");
			return options.rpcWithDeadline
				? options.rpcWithDeadline(method, params, remainingMs)
				: rpc!(method, params);
		};
		try { observe(await callRpc("status")); } catch (error) {
			if (now() >= deadlineAt) return finish(request, "unknown", [...known.values()].map(childReceipt), { code: "control_deadline", message: `Lifecycle control exceeded ${deadlineMs}ms.` });
			return finish(request, "unknown", [...known.values()].map(childReceipt), { code: "status_failed", message: error instanceof Error ? error.message : String(error) });
		}
		const targets: KnownChild[] = [];
		const controlled = new WeakSet<KnownChild>();
		const controlledRuns = new Set<string>();
		const controlKey = (child: KnownChild): string => `${child.mode}:${child.runId}`;
		const refreshTargets = (): void => {
			for (const child of known.values()) if (!targets.includes(child)) targets.push(child);
		};
		refreshTargets();
		for (const child of targets) {
			try { updateChild(child, await callRpc("status", statusParams(child))); } catch (error) {
				if (now() >= deadlineAt) return finish(request, "unknown", targets.map(childReceipt), { code: "control_deadline", message: `Lifecycle control exceeded ${deadlineMs}ms.` });
			}
			if (!isActive(child.status) && proofComplete(child)) continue;
			try {
				if (controlledRuns.has(controlKey(child))) {
					controlled.add(child);
					continue;
				}
				controlled.add(child);
				controlledRuns.add(controlKey(child));
				if (child.mode === "foreground") await callRpc("interrupt", { runId: child.runId });
				else await callRpc("stop", { id: child.runId, ...(child.childId ? { childId: child.childId } : {}) });
			} catch (error) {
				if (now() >= deadlineAt) return finish(request, "unknown", targets.map(childReceipt), { code: "control_deadline", message: `Lifecycle control exceeded ${deadlineMs}ms.` });
				child.status = "unknown";
				return finish(request, "unknown", targets.map(childReceipt), { code: `${child.mode}_control_failed`, message: error instanceof Error ? error.message : String(error) });
			}
		}
		while (now() < deadlineAt) {
			if (!sameRequest(request)) return finish(request, "unknown", targets.map(childReceipt), { code: "request_replaced", message: "Teardown request changed while lifecycle control was in progress." });
			try { observe(await callRpc("status")); } catch {
				if (now() >= deadlineAt) break;
			}
			refreshTargets();
			for (const child of targets) {
				try { updateChild(child, await callRpc("status", statusParams(child))); } catch {
					if (now() >= deadlineAt) break;
				}
				if (controlled.has(child) || (!isActive(child.status) && proofComplete(child))) continue;
				try {
					if (controlledRuns.has(controlKey(child))) {
						controlled.add(child);
						continue;
					}
					controlled.add(child);
					controlledRuns.add(controlKey(child));
					if (child.mode === "foreground") await callRpc("interrupt", { runId: child.runId });
					else await callRpc("stop", { id: child.runId, ...(child.childId ? { childId: child.childId } : {}) });
				} catch (error) {
					if (now() >= deadlineAt) break;
					child.status = "unknown";
				}
			}
			if (now() >= deadlineAt) break;
			if (targets.every(proofComplete)) return finish(request, "stopped", targets.map(childReceipt));
			await sleep(Math.min(pollMs, Math.max(1, deadlineAt - now())));
		}
		return finish(request, "unknown", targets.map(childReceipt), { code: "control_deadline", message: `Lifecycle control exceeded ${deadlineMs}ms.` });
	};

	const finish = (request: TeardownRequest, state: StopReceipt["state"], children: ChildEvidence[], error?: StopReceipt["error"]): StopReceipt => {
		let current = false;
		try {
			current = sameRequest(request);
		} catch {
			// A replaced or removed request owns the receipt path now.
		}
		const finalError = current ? error : { code: "request_replaced", message: "Teardown request changed before the lifecycle receipt could be committed." };
		const receipt: StopReceipt = { schema_version: 1, state: current ? state : "unknown", fence_id: request.fence_id, parent_native_session_id: request.parent_native_session_id, started_at: request.started_at, completed_at: Math.floor(now() / 1000), children, ...(finalError ? { error: finalError } : {}) };
		if (current) writeJson(receiptFile, receipt);
		return receipt;
	};

	return {
		get fenced() { return fenced; },
		observe,
		stop,
		requestFile,
		receiptFile,
		manifestFile,
	};
}

function rpcViaPi(pi: { events: EventBus }, method: RpcMethod, params: Record<string, unknown> | undefined, deadlineMs: number): Promise<unknown> {
	const requestId = randomUUID();
	return new Promise((resolve, reject) => {
		let done = false;
		const replyEvent = `subagents:rpc:v1:reply:${requestId}`;
		let unsubscribe: (() => void) | void;
		let timer: ReturnType<typeof setTimeout> | undefined;
		const cleanup = () => { if (unsubscribe) unsubscribe(); if (timer) clearTimeout(timer); };
		const finish = (callback: () => void) => { if (done) return; done = true; cleanup(); callback(); };
		unsubscribe = pi.events.on(replyEvent, (reply) => {
			const value = record(reply);
			if (value?.success === false) finish(() => reject(new Error(string(record(value.error)?.message) ?? "Pi subagent RPC failed.")));
			else finish(() => resolve(value?.data));
		});
		timer = setTimeout(() => finish(() => reject(new Error(`Pi subagent RPC ${method} timed out.`))), deadlineMs);
		pi.events.emit("subagents:rpc:v1:request", { version: 1, requestId, method, ...(params ? { params } : {}), source: { extension: "factory-subagent-lifecycle" } });
	});
}

export function factorySubagentLifecycle(pi: { events: EventBus; registerCommand: (name: string, options: { description: string; handler: (args: string, ctx: { sessionManager: { getSessionId: () => string | undefined; getSessionFile?: () => string | undefined; getSessionDir?: () => string | undefined } }) => Promise<void> }) => void; on: (event: string, handler: (value: any, ctx?: any) => any) => void; }): void {
	type SessionManagerRef = { getSessionId?: () => string | undefined; getSessionFile?: () => string | undefined; getSessionDir?: () => string | undefined };
	let adapter: ReturnType<typeof createLifecycleAdapter> | undefined;
	let activeSessionManager: SessionManagerRef | undefined;
	let parentSessionId: string | undefined;
	let parentSessionFile: string | undefined;
	let parentSessionDir: string | undefined;
	const current = () => {
		adapter ??= createLifecycleAdapter({
			getParentSessionId: () => activeSessionManager?.getSessionId?.() ?? parentSessionId,
			getParentSessionFile: () => activeSessionManager?.getSessionFile?.() ?? parentSessionFile,
			getParentSessionDir: () => activeSessionManager?.getSessionDir?.() ?? parentSessionDir,
			rpcWithDeadline: (method, params, remainingMs) => rpcViaPi(pi, method, params, remainingMs),
		});
		return adapter;
	};
	pi.on("session_start", (_event: any, ctx: any) => {
		activeSessionManager = ctx?.sessionManager;
		const sessionId = ctx?.sessionManager?.getSessionId?.();
		if (typeof sessionId === "string" && sessionId) {
			parentSessionId = sessionId;
			const sessionFile = ctx?.sessionManager?.getSessionFile?.();
			parentSessionFile = typeof sessionFile === "string" && sessionFile ? sessionFile : undefined;
			const sessionDir = ctx?.sessionManager?.getSessionDir?.();
			parentSessionDir = typeof sessionDir === "string" && sessionDir ? sessionDir : undefined;
			// Persist an honest empty tree immediately. This gives every physical
			// native home a current-session manifest even when no tool has run;
			// teardown still obtains live proof through the RPC status pass.
			current().observe({});
		}
	});
	pi.on("tool_call", (event: any, ctx: any) => {
		const sessionManager = ctx?.sessionManager ?? event?.ctx?.sessionManager;
		if (sessionManager) {
			activeSessionManager = sessionManager;
			const sessionId = sessionManager?.getSessionId?.();
			if (typeof sessionId === "string" && sessionId) parentSessionId = sessionId;
			const sessionFile = sessionManager?.getSessionFile?.();
			if (typeof sessionFile === "string" && sessionFile) parentSessionFile = sessionFile;
			const sessionDir = sessionManager?.getSessionDir?.();
			if (typeof sessionDir === "string" && sessionDir) parentSessionDir = sessionDir;
		}
		if (!current().fenced || event?.toolName !== "subagent") return;
		return { block: true, reason: "Factory subagent teardown fence is closing the native session tree." };
	});
	pi.on("tool_result", (event: any) => {
		if (event?.toolName === "subagent") current().observe({ details: event.details, text: event.content?.filter((item: any) => item.type === "text").map((item: any) => item.text).join("\n") });
	});
	for (const event of ["subagent:async-started", "subagent:control-event", "subagent:foreground-complete", "subagent:process-terminal"]) {
		pi.events.on(event, (value) => current().observe(value));
	}
	pi.registerCommand(COMMAND_NAME, {
		description: "Stop Factory-owned native subagents and write the lifecycle receipt.",
		handler: async (_args, ctx) => {
			activeSessionManager = ctx.sessionManager;
			parentSessionId = ctx.sessionManager.getSessionId();
			parentSessionFile = ctx.sessionManager.getSessionFile?.();
			parentSessionDir = ctx.sessionManager.getSessionDir?.();
			await current().stop();
		},
	});
}

export const registerFactorySubagentLifecycle = factorySubagentLifecycle;
export default factorySubagentLifecycle;
