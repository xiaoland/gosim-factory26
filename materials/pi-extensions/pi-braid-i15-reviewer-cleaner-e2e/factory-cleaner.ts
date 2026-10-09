import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { createHash, randomUUID } from "node:crypto";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { buildSessionContext, convertToLlm, type ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { Type } from "typebox";

const executeFile = promisify(execFile);
const sha256 = (value: string | Buffer) => createHash("sha256").update(value).digest("hex");

type CleanerConfig = {
  provider: string;
  model: string;
  thinking_level: "high";
  shared_requirements: string;
  instructions: string;
  budget_module: string;
};
type CleanerResult = { description?: string; hide: Array<{ id: number; reason: string }>; resolve: number[] };
type Snapshot = {
  operation_id: string;
  writer: { agent_id: string; turn_id: string; session_id: string; assignment_id: string; member_login: string };
  material: { item: { node_id: string }; comments: Array<{ id: number; thread_root: number; lifecycle: string }> };
  [key: string]: unknown;
};

function redact(value: string): string {
  for (const name of ["FACTORY26_API_KEY", "FACTORY26_VISUAL_API_KEY", "OPENAI_API_KEY", "CONTEXT7_API_KEY", "EXA_API_KEY"]) {
    const credential = process.env[name];
    if (credential) value = value.split(credential).join("[credential]");
  }
  return value;
}

function record(directory: string, name: string, value: unknown): void {
  fs.writeFileSync(path.join(directory, name), redact(JSON.stringify(value, null, 2)) + "\n", { flag: "wx", mode: 0o600 });
}

function errorEvidence(error: unknown, depth = 0): unknown {
  if (!(error instanceof Error)) return String(error);
  const command = error as Error & { code?: unknown; signal?: unknown; stdout?: unknown; stderr?: unknown };
  return { name: error.name, message: error.message, stack: error.stack, code: command.code,
    signal: command.signal, stdout: command.stdout, stderr: command.stderr,
    cause: depth < 2 && error.cause !== undefined ? errorEvidence(error.cause, depth + 1) : undefined };
}

function assertObject(value: unknown, allowed: string[]): asserts value is Record<string, unknown> {
  if (!value || typeof value !== "object" || Array.isArray(value)) throw new Error("cleaner result must be a JSON object");
  const unknown = Object.keys(value).filter((key) => !allowed.includes(key));
  if (unknown.length) throw new Error(`unknown cleaner fields: ${unknown.join(", ")}`);
}

function parseResult(text: string, snapshot: Snapshot): CleanerResult {
  const result: unknown = JSON.parse(text);
  assertObject(result, ["description", "hide", "resolve"]);
  if ("description" in result && typeof result.description !== "string") throw new Error("description must be a string or omitted");
  if (!Array.isArray(result.hide) || !Array.isArray(result.resolve)) throw new Error("hide and resolve must be arrays");
  const hidden = new Set<number>();
  for (const hide of result.hide) {
    assertObject(hide, ["id", "reason"]);
    if (!Number.isSafeInteger(hide.id) || (hide.id as number) <= 0 || hidden.has(hide.id as number)) throw new Error("duplicate or invalid hide ID");
    const comment = snapshot.material.comments.find((comment) => comment.id === hide.id);
    if (!comment || comment.lifecycle === "deleted") throw new Error(`hide comment ${hide.id} is unavailable in the current work item`);
    if (typeof hide.reason !== "string" || !hide.reason.trim()) throw new Error("hide reason must be nonempty");
    hidden.add(hide.id as number);
  }
  const resolved = new Set<number>();
  for (const id of result.resolve) {
    if (!Number.isSafeInteger(id) || id <= 0 || resolved.has(id)) throw new Error("duplicate or invalid resolve ID");
    const comment = snapshot.material.comments.find((comment) => comment.id === id);
    if (!comment || comment.thread_root !== id) throw new Error(`resolve ${id} is not a discussion root in the current work item`);
    if (hidden.has(id)) throw new Error("the same discussion root cannot be hidden and resolved");
    resolved.add(id);
  }
  return result as CleanerResult;
}

export default function factoryCleaner(pi: ExtensionAPI): void {
  const configPath = path.join(path.dirname(fileURLToPath(import.meta.url)), "factory-cleaner.json");
  const config: CleanerConfig = JSON.parse(fs.readFileSync(configPath, "utf8"));
  if (config.provider !== "factory26" || config.model !== "glm-5.3-flash" || config.thinking_level !== "high") {
    throw new Error("I14 cleaner requires the frozen factory26/glm-5.3-flash route and high thinking level");
  }
  const systemPrompt = fs.readFileSync(config.shared_requirements, "utf8") + "\n\n" + fs.readFileSync(config.instructions, "utf8");

  pi.registerTool({
    name: "braid_cleaner",
    label: "整理当前 Braid 工作项",
    description: "运行一次独立 cleaner，继承当前有效历史并整理当前 Issue/PR 的正文与讨论。只需触发，不提供操作计划。完整正常结果通过来源校验后原子提交，费用归当前 Braid session。",
    promptSnippet: "按需整理当前 Braid 工作项的正文与讨论",
    parameters: Type.Object({}, { additionalProperties: false }),
    executionMode: "sequential",
    async execute(toolCallId, _params, signal, _onUpdate, ctx) {
      const operationId = randomUUID();
      const nativeHome = process.env.PI_CODING_AGENT_DIR;
      if (!nativeHome) throw new Error("PI_CODING_AGENT_DIR is required for cleaner evidence");
      const directory = path.join(nativeHome, ".factory", "maintenance", operationId);
      fs.mkdirSync(directory, { recursive: true, mode: 0o700 });
      const abort = signal && ctx.signal && signal !== ctx.signal ? AbortSignal.any([signal, ctx.signal]) : signal ?? ctx.signal;
      let response: Awaited<ReturnType<typeof ctx.modelRegistry.complete>> | undefined;
      let reportedUsage: NonNullable<typeof response>["usage"] | undefined;
      let commitStarted = false;
      const braid = async (args: string[], requestSignal?: AbortSignal) => {
        const result = await executeFile("braid", ["maintenance", ...args], {
          cwd: ctx.cwd, env: process.env, signal: requestSignal, maxBuffer: 32 * 1024 * 1024,
        });
        return JSON.parse(result.stdout);
      };
      try {
        abort?.throwIfAborted();
        const branch = ctx.sessionManager.getBranch();
        const caller = branch.findLast((entry) => entry.type === "message" && entry.message.role === "assistant"
          && entry.message.content.some((part) => part.type === "toolCall" && part.id === toolCallId));
        if (!caller || !caller.parentId) throw new Error("cannot locate a complete native history cutoff before the invoking assistant");
        const cutoff = caller.parentId;
        const prefix = branch.slice(0, branch.findIndex((entry) => entry.id === caller.id));
        if (prefix.at(-1)?.id !== cutoff) throw new Error("native branch does not contain the invoking assistant's complete prefix");
        const projected = buildSessionContext(branch, cutoff);
        const messages = convertToLlm(projected.messages);
        const pending = new Set<string>();
        for (const message of messages) {
          if (message.role === "assistant") {
            for (const part of message.content) {
              if (part.type === "toolCall") {
                if (pending.has(part.id)) throw new Error("duplicate tool call in inherited history");
                pending.add(part.id);
              }
            }
          } else if (message.role === "toolResult" && !pending.delete(message.toolCallId)) {
            throw new Error(`unpaired tool result in inherited history: ${message.toolCallId}`);
          }
        }
        if (pending.size) throw new Error("inherited native prefix contains unresolved tool calls");
        const sessionFile = ctx.sessionManager.getSessionFile();
        if (!sessionFile) throw new Error("current native session has no durable source file");
        const sourceBefore = fs.readFileSync(sessionFile);
        const sourceHeader = JSON.parse(sourceBefore.toString("utf8").split(/\r?\n/, 1)[0]);
        const nativeSessionId = ctx.sessionManager.getSessionId();
        if (sourceHeader.type !== "session" || (sourceHeader.id ?? sourceHeader.sessionId ?? sourceHeader.session_id) !== nativeSessionId) {
          throw new Error("reported native source file does not belong to the current parent session");
        }
        const nativeSource = {
          session_id: nativeSessionId, session_file: sessionFile, leaf_id: cutoff,
          invoking_entry_id: caller.id, tool_call_id: toolCallId, branch_digest: sha256(JSON.stringify(prefix)),
          source_file_digest: sha256(sourceBefore),
        };
        record(directory, "native-source.json", nativeSource);
        record(directory, "inherited-context.json", { entries: prefix, messages, thinking_level: projected.thinkingLevel,
          source_file_digest_after_capture: sha256(fs.readFileSync(sessionFile)) });
        const snapshot: Snapshot = await braid(["snapshot", "--operation-id", operationId, "--native-source", path.join(directory, "native-source.json")], abort);
        record(directory, "snapshot.json", snapshot);
        const model = ctx.modelRegistry.find(config.provider, config.model);
        if (!model || !ctx.modelRegistry.hasConfiguredAuth(model)) throw new Error(`configured cleaner model unavailable: ${config.provider}/${config.model}`);
        const budget = await import(pathToFileURL(config.budget_module).href);
        budget.claimModelSession(process.env.FACTORY26_MODEL_BUDGET_PATH, snapshot.writer.agent_id, model.id);
        record(directory, "request.json", { operation_id: operationId, parent: snapshot.writer, native_source: nativeSource,
          model: { provider: model.provider, id: model.id, thinking_level: config.thinking_level },
          shared_requirements_digest: sha256(fs.readFileSync(config.shared_requirements)), instructions_digest: sha256(fs.readFileSync(config.instructions)),
          budget_owner: snapshot.writer.agent_id, started_at: new Date().toISOString() });
        response = await ctx.modelRegistry.complete(model, {
          systemPrompt, messages: [...messages, { role: "user", timestamp: Date.now(),
            content: `执行此次维护。以下快照晚于继承历史，原始正文与需求背景优先。只返回完整维护 JSON。\n${JSON.stringify(snapshot.material)}` }],
        }, { signal: abort, sessionId: snapshot.writer.session_id, maxRetries: 0, maxRetryDelayMs: 0,
          samplingParams: model.samplingParams,
          reasoningEffort: config.thinking_level,
          onResponse: (http) => { record(directory, "http-response.json", { status: http.status }); } });
        record(directory, "response.json", response);
        // A nonempty inherited request cannot have zero input and output; Pi's default zeros are not usage evidence.
        if (response.usage && [response.usage.input, response.usage.output, response.usage.cacheRead, response.usage.cacheWrite].some((tokens) => tokens > 0)) {
          reportedUsage = response.usage;
        }
        if (response.stopReason !== "stop" || response.content.some((part) => part.type === "toolCall")) {
          throw new Error(`cleaner did not complete normally: ${response.stopReason}; ${response.errorMessage ?? ""}`);
        }
        const result = parseResult(response.content.filter((part) => part.type === "text").map((part) => part.text).join(""), snapshot);
        const apply = { snapshot, result, model: { provider: response.provider, model: response.model,
          response_model: response.responseModel ?? null, response_id: response.responseId ?? null,
          stop_reason: response.stopReason, usage: reportedUsage ?? null } };
        record(directory, "apply.json", apply);
        // Operational input remains exact; redaction is confined to diagnostic artifacts.
        const inputFile = path.join(directory, ".private-apply-input.json");
        fs.writeFileSync(inputFile, JSON.stringify(apply), { flag: "wx", mode: 0o600 });
        abort?.throwIfAborted();
        // Once launched, do not abort the short commit process: cancellation cannot undo a committed receipt.
        commitStarted = true;
        const receipt = await braid(["apply", "--input", inputFile]);
        record(directory, "receipt.json", receipt);
        return { content: [{ type: "text", text: JSON.stringify({ status: "committed", receipt }) }],
          details: { operation_id: operationId, status: "committed", receipt, evidence_directory: directory }, usage: reportedUsage };
      } catch (error) {
        const failure = redact(error instanceof Error ? error.message : String(error));
        let receipt: unknown;
        let status = abort?.aborted ? "cancelled_before_commit" : "not_applied";
        let receiptError: string | undefined;
        if (commitStarted) {
          try {
            receipt = await braid(["receipt", operationId]);
            status = receipt ? "committed" : "not_applied";
          } catch (readError) {
            status = "commit_unknown";
            receiptError = redact(String(readError));
          }
        }
        record(directory, "outcome.json", { operation_id: operationId, status, error: failure,
          error_evidence: errorEvidence(error), receipt, receipt_error: receiptError });
        const summary = failure.length > 4000 ? failure.slice(0, 4000) + `\n完整错误：${path.join(directory, "outcome.json")}` : failure;
        return { content: [{ type: "text", text: JSON.stringify({ operation_id: operationId, status, error: summary, receipt }) }],
          details: { operation_id: operationId, status, receipt, error: summary, evidence_directory: directory }, usage: reportedUsage };
      }
    },
  });
}
