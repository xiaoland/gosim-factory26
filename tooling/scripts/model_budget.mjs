import fs from "node:fs";
import path from "node:path";
import { DatabaseSync } from "node:sqlite";

// One Braid owner for this entire set; native context replacements do not change ownership.
const restricted = new Set([
  "glm-5.2", "glm-5.3", "qwen-3.8-max", "qwen3.7-max", "kimi-k3",
  "kimi-k2.7-code-highspeed", "deepseek-v4-pro",
].map(normalize));

function normalize(model) {
  return model.toLowerCase().split("/").at(-1).replace(/[-_.]/g, "");
}

export function claimModelSession(slot, session, model) {
  if (!restricted.has(normalize(model))) return;
  if (!slot || !session) throw new Error("昂贵模型请求缺少运行或会话身份，已拒绝调用");
  try {
    // A symlink publishes the owner atomically; it is never followed or released.
    fs.symlinkSync(session, slot);
  } catch (error) {
    if (error.code !== "EEXIST") throw error;
    if (fs.readlinkSync(slot) !== session) {
      throw new Error(`昂贵模型名额已由本次运行的另一会话使用；拒绝 ${model}，请选择 Flash 模型`);
    }
  }
}

export default function modelBudget(pi) {
  let owner;
  pi.on("before_provider_request", (event, context) => {
    // Native children inherit their parent's Braid binding and claim that same owner.
    // Skipping children would let different Flash members each spend on K3.
    try {
      const model = event.payload?.model ?? context.model?.id;
      if (typeof model !== "string") throw new Error("无法辨认请求模型，已拒绝调用");
      if (!restricted.has(normalize(model))) return;
      if (!owner) {
        if (!process.env.BRAID_STATE || !process.env.BRAID_CLI_BINDING_ID)
          throw new Error("昂贵模型请求缺少 Braid 会话身份，已拒绝调用");
        const database = new DatabaseSync(path.join(process.env.BRAID_STATE, "braid.sqlite3"), { readOnly: true });
        try {
          // The CLI binding changes on resume; the logical Braid agent survives context replacement.
          owner = database.prepare("SELECT agent_id FROM provider_sessions WHERE cli_binding_id = ?")
            .get(process.env.BRAID_CLI_BINDING_ID)?.agent_id;
        } finally {
          database.close();
        }
      }
      claimModelSession(process.env.FACTORY26_MODEL_BUDGET_PATH, owner, model);
    } catch (error) {
      // Pi catches ordinary extension exceptions and would still send the request.
      // Exit before transport instead of turning this spending limit into a warning.
      try {
        fs.writeSync(2, `Factory model budget: ${error.message}\n`);
      } finally {
        process.exit(78);
      }
    }
  });
}
