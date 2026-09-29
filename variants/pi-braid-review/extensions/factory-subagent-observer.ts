import fs from "node:fs";
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

export function factorySubagentObserver(pi: {
	on: (event: string, handler: (value: any, context?: any) => void) => void;
	events: { on: (event: string, handler: (value: unknown) => void) => unknown };
}): void {
	type SessionManager = { getSessionId?: () => string | undefined; getSessionFile?: () => string | undefined; getSessionDir?: () => string | undefined };
	let manager: SessionManager | undefined;
	let observer: ReturnType<typeof createSubagentObserver> | undefined;
	const current = () => observer ??= createSubagentObserver({
		getParentSessionId: () => manager?.getSessionId?.(),
		getParentSessionFile: () => manager?.getSessionFile?.(),
		getParentSessionDir: () => manager?.getSessionDir?.(),
	});
	pi.on("session_start", (_event, context) => {
		manager = context?.sessionManager;
		current().observe({});
	});
	pi.on("tool_result", (event, context) => {
		manager = context?.sessionManager ?? manager;
		if (event?.toolName === "subagent") current().observe(event);
	});
	for (const event of ["subagent:async-started", "subagent:control-event", "subagent:foreground-complete", "subagent:process-terminal"])
		pi.events.on(event, (value) => current().observe(value));
}

export default factorySubagentObserver;
