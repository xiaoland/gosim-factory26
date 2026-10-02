# 09 预演：`subagent_wait` 与 PBB 的调用处反馈

这是只读方案，未改源码或运行。锁定依赖为 `pi-subagents@0.56.0`、`pi-background-bash@1.0.5`、Pi coding agent `0.85.1`（`harness/npm/package-lock.json`）。[08 现场](attempt08-validation.md)已经证明：会话系统指令含名称澄清，但 GitHub 根两次、Sheet 根一次、Sheet #6 三次仍把 PBB `bg*` 作业交给 `subagent_wait`，六次都立即返回无原生任务。因此再加全局提示并不能可靠修复这条调用链。

## 接入点与决定

`pi-subagents/src/runs/background/wait-tool.ts:10-23` 注册 `subagent_wait`；当前 description 用“background work owned by this session”“async run / registered provider item”说明范围，却没有明确排除 Pi Background Bash 的 `bg*`。`subagent-wait.ts:553-555` 的空结果分别是 `No active run matched "<id>". Nothing to wait for.` 与 `No active async runs or registered provider work in this session. Nothing to wait for.`，也未指向 PBB。Pi `docs/extensions.md:842-868` 明确 `tool_result` 事件可读 `event.toolName`、`event.input`、`event.content`，并返回仅含 `content` 的补丁，原始结果的其他字段不变。两个现用 variant 的 `extensions/factory-subagent-observer.ts` 已监听 `tool_result` 观察 `subagent`，可在同一入口追加一个**窄的结果提示**，无需重注册、包装或替换 `subagent_wait`。

拟改文件只有 `variants/pi-braid/extensions/factory-subagent-observer.ts` 与 `variants/pi-braid-flash-team/extensions/factory-subagent-observer.ts`，两份保持同一行为。仅当 `event.toolName === "subagent_wait"` 且原生文本为上述两类空结果时，在原 `event.content` 后追加一条简短 text：

| 原生调用 | 追加反馈要表达的事实 |
| --- | --- |
| `event.input.id` 是 `bg` 加数字，如 `bg001` | “`bg001` 是 Pi Background Bash 作业，`subagent_wait` 不能等待它；有独立工作就继续，需提前查看进度用 `pbb status bg001` / `pbb tail bg001`，仅剩等待时结束本次响应，完成消息会唤醒。”保留原先的 `No active run matched`。 |
| `all:true` 或无 id，原生答当前 session 无 async run/provider item | “`all:true` 只覆盖当前 Pi session 的原生子任务/注册 provider work，不覆盖 bash `bg*`；bash 的完成消息会另行送达，只有需要提前看进度才用 PBB。”保留原始准确的空状态。 |
| 真正原生子任务正在运行、完成、超时、出错，或 `subagent_wait` 以后更改了结果格式 | 不追加，不改变执行、状态、退出码或结果。 |

这个方案在**出错调用的 tool result** 给模型反馈，同时保留 `subagent_wait` 的原生状态语义。不要让 observer 自动代调 `pbb`：它不知道模型是要进度、日志还是等待终态，也不能把 `bg*` 当子代理 UUID。可用 `event.input` 做 `bg\d+` 判定，但最终只在**原生空结果**时添提示，避免将碰巧同名前缀的有效 provider run 错判。结果文本变动会使提示失效而原工具行为仍保持；这是可接受的窄失败模式。

当前 Pi 文档只把 description 定义在 `pi.registerTool(definition)`，没有找到对第三方**已注册工具**的文档化 description override。重新用同名 `registerTool` 需要代理原工具的 schema/execute，形成脆弱包装；直接改 npm 包缓存不能进入冻结产物。若产品要求模型在**首次调用前**看到更明确的工具 description，就须维护锁定 `pi-subagents` 的上游补丁/发布或有版本约束的安装补丁，并在 `wait-tool.ts` 增“not Pi Background Bash bg*”一行；这比当前只修已证误用的最小范围更重。本轮推荐先用现有扩展的 `tool_result` 补丁，不改第三方注册。

## PBB 本身已有完成链，问题在长回合自我等待

`pi-background-bash/extensions/background-bash.ts:749-758` 在后台命令完成时用 `pi.sendMessage({customType:"background_bash_result",...},{deliverAs:"followUp",triggerTurn:true})`，注册的 bash description、promptSnippet 和 promptGuidelines（约 972–979 行）也说完成时自动唤醒、仅需要**提前进度**时用 `pbb`。README 与内置 `skills/pbb/SKILL.md` 同样写了这一点。源码 `sendBackgroundResultFollowUp` 在当前 provider 请求仍忙时先把结果入队，`agent_end` 后才冲刷；这是避免并发请求与悬空 tool-call 竞态的现有设计。08 原生 transcript 中，Sheet #6 06:46:18 启动 `bg001`，随后不断 `subagent_wait`、`sleep` 与 `tail`，而 `background_bash_result` 在 06:55:01–06:55:36 成组进入同一 session（bg001–009）；Sheet 根也在 06:54:39–06:55:00 集中收到 bg001–005。它们证明原生完成通知已实际到达，不宜另造等待工具。不能仅从注入时间推断每个 bash 进程真实完成时间；集中送达与源码的忙时排队机制相符。

调用处提示应明确：**有独立工作先继续；仅剩等待时结束当前响应，完成消息将唤醒；确需提前状态/有界日志才用 `pbb status/tail`。**不要求启动后台后立刻停，也不应让模型再开一条 `sleep; tail` 命令制造第二个 PBB 作业。PBB 当前启动回执已经包含“follow-up result will arrive”“use pbb only if progress before completion”，所以本次不改 PBB 文案或服务逻辑。

真实运行验收：09 自然出现 `bg*` 被误传 `subagent_wait` 时，原始 `No active run matched` 应保留且追加正确的 PBB 入口；`all:true` 无原生任务时仍准确返回空，并说明不覆盖 bash；模型随后应走 PBB 状态/完成通知或结束待唤醒的响应，不再串 `sleep` 轮询。若自然出现真正 Pi 子任务，正常 wait 结果必须原样，不能被 PBB 提示污染。观察到 `background_bash_result` 后，还需看父会话是否实际据退出码/结果继续工作；仅有通知条数不是验收。没有自然触发时只记未触发，不构造 Factory 探针。
