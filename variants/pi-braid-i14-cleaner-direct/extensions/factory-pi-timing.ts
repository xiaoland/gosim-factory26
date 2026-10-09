import fs from "node:fs";
import { randomUUID } from "node:crypto";

// Passive timing only: no prompt, response body, tool argument, or credential leaves Pi.
export default function factoryPiTiming(pi: { on: (name: string, handler: (event: any, context?: any) => void) => void }): void {
	const file = process.env.FACTORY26_PI_TIMING_FILE;
	if (!file) return;
	const instance = randomUUID();
	let sequence = 0;
	let request: string | undefined;
	let firstSeen = false;
	const tools = new Map<string, { name: string; start: number }>();
	const identity = (context?: any) => ({
		instance_id: instance,
		pid: process.pid,
		session_id: context?.sessionManager?.getSessionId?.(),
		session_file: context?.sessionManager?.getSessionFile?.(),
	});
	const write = (kind: string, data: Record<string, unknown>, context?: any) => {
		try {
			fs.appendFileSync(file, JSON.stringify({ kind, at_ms: Date.now(), ...identity(context), ...data }) + "\n");
		} catch (error) {
			process.stderr.write(`Pi timing write failed: ${String(error)}\n`);
		}
	};
	pi.on("before_provider_request", (_event, context) => {
		request = `${instance}:${++sequence}`;
		firstSeen = false;
		write("request_start", { request_id: request, model: context?.model?.id,
			provider: context?.model?.provider }, context);
	});
	pi.on("after_provider_response", (event, context) => {
		write("response_headers", { request_id: request, status: event.status }, context);
	});
	pi.on("message_update", (event, context) => {
		const update = event?.assistantMessageEvent;
		if (request && !firstSeen && ["text_delta", "thinking_delta", "toolcall_delta"].includes(update?.type)
			&& update?.delta) {
			write("first_update", { request_id: request,
				update_type: update.type }, context);
			firstSeen = true;
		}
	});
	pi.on("message_end", (event, context) => {
		const message = event?.message;
		if (message?.role !== "assistant") return;
		write("message_end", { request_id: request, response_id: message.responseId,
			model: message.model, provider: message.provider, usage: message.usage,
			stop_reason: message.stopReason }, context);
		request = undefined;
	});
	pi.on("tool_execution_start", (event, context) => {
		tools.set(event.toolCallId, { name: event.toolName, start: Date.now() });
		write("tool_start", { tool_call_id: event.toolCallId, tool_name: event.toolName }, context);
	});
	pi.on("tool_execution_end", (event, context) => {
		const started = tools.get(event.toolCallId);
		tools.delete(event.toolCallId);
		write("tool_end", { tool_call_id: event.toolCallId, tool_name: event.toolName ?? started?.name,
			is_error: event.isError }, context);
	});
}
