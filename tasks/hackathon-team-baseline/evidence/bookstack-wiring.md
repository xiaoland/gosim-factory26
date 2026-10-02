# BookStack run 的指令与工具接线原始摘录

仅整理既有 run，不判断原因或效果。`R/` 为 WSL `/home/yyh/Development/factory26/runs/hackathon-team-baseline/20260925/lite-runs/pi-team-mixed-arc-bench-lite-bookstack-ba27587982/`；`G/` 为 `R/workspace/official-generation/template/.factory26/20260924-163415-c848b68c/`。`N0` 为 `G/native/000-2026-09-24T16-34-27-132Z_01a0d444-b2bc-761b-bae8-f2d3bdb3ffab.jsonl`。JSONL 行号指物理行；引文取该行 `message.content` 中的短片段，未复制整行图片、需求或凭据。

## 主 Agent 收到的内容

`G/native/manifest.json:11-15` 将首段原生会话连接到 `G/braid-state/physical/01a0d444-85a1-7a73-956b-b9b8323095c9/instructions.md`，`G/native/manifest.json:34` 另记录容器内指令源路径。归档未单独保存一次完整的模型 system/developer 消息；以下是**该会话关联的实际指令文件**和原生首条 user 消息，不把文件内容冒充逐字网关请求。

| 原始位置 | 小段原文 |
| --- | --- |
| `G/braid-state/physical/01a0d444-85a1-7a73-956b-b9b8323095c9/instructions.md:1-4` | “你负责 Issue #1 的问题、设计与验收依据。需要实施时使用关联 PR 的工作树。”；“当前工作项内的局部委派使用原生 sub-agent。” |
| 同文件 `:9-11` | “本 Factory 使用 Braid 的 Issue/PR 组织工作。像人类一样协作、使用 Issue/PR。”；“按当前问题查阅 SVC 的设计、实现与 V&V 方法，用 task packet 保存持续工作所需的方案、计划、材料和证据。” |
| 同文件 `:13` | “子 Agent 不继承主会话历史，调用时明确设置 context:\"fresh\"”；“连续浏览器操作通常交给 browser-operator 或 executor”；“按当前问题选择直接完成或委派……短小的直接检查无需额外委派。” |
| `G/prompt.txt:1-5` | “本次任务的需求来源是……/input 中的完整需求包”；“阅读 requirements.md、requirements.yaml 和参考图片”；“可以编写运行自己的检查……不得读取、搜索或下载外部验收测试、benchmark 实现、参考应用或先前实验结果。” |
| `N0:4`，首条 `role=user` | “系统已从当前本地对象重建工作记忆。”；“State: open / Assignees: @glm”；末尾：“先通过 `braid` 读取当前工作项，再决定需要的操作。” |
| `N0:5-8` | 首个 assistant 动作为列出输入和 `braid issue view 1`；工具结果给出 Issue #1、`state: OPEN`、`assignee: @glm`；随后 `read` 读取 `requirements.md`、`requirements.yaml`。 |

## 模型对委派与方法的原话

| 原始位置 | 小段原文 |
| --- | --- |
| `N0:39`，`assistant.content[type=thinking]` | “Given scale, I should delegate implementation? The instructions mention sub-agents for bounded delegation. The task is big but well-defined; I can implement directly.”；“I'll write it directly but efficiently.” |
| `N0:39`，同一段 | “Let me also check `braid context issue 1` maybe there's more info, and SVC skill? The svc skill is recommended for nontrivial tasks. It suggests saving task packet etc.” |
| `N0:48`，`assistant.content[type=thinking]` | “Now let me write the application. I'll do it directly — start with backend.”；“Let me create the task design note first (per SVC, save plan in worktree). … I'll keep notes in the issue instead. Actually keep it light — write code now.” |

这三段记录的是模型当时的文字。所检查的三段原生会话没有找到“子代理工具不可用”或“SVC/MCP 工具不可用”的模型陈述。`G/native/001-session-tree.json`、`003-session-tree.json`、`005-session-tree.json` 各自的 `children` 均为空。

## extension、RPC 与日志

| 原始位置 | 记录 |
| --- | --- |
| `G/native-config/pi-glm-fast/native-template/settings.json:1-5` | 配置有 `"subagents": { "disableBuiltins": true }`。`G/native-config/pi-glm-fast/factory-subagent-observer.ts` 文件存在；这是归档配置/文件事实，不是加载成功日志。 |
| `N0:1-5` | 依次为 `session`、`model_change`（`factory26` / `glm-5.3-flash`）、`thinking_level_change`、首条 user 消息、assistant 工具调用。原生 JSONL 的事件类型只有这些初始化记录和后续 `message`；没有独立的 extension-load、RPC 工具清单事件。 |
| `N0` 全文件；`G/native/002-2026-09-24T18-21-10-922Z_01a0d4a6-698a-7470-8670-39bab44a876f.jsonl`；`G/native/004-2026-09-24T18-21-35-832Z_01a0d4a6-cad8-7068-acf5-99e108fcecd5.jsonl` | 三段会话中的实际 toolCall 名称只有 `bash`、`read`、`write`、`edit`（首段分别 85、27、27、15；后两段各只有 `bash` 4、6 次）。未见 sub-agent/RPC/MCP 工具调用或 `tools/list` 返回。 |
| `R/workspace/generation.stderr.log`（0 行）；`R/workspace/generation.stdout.log:1-19`；`R/workspace/official-generation/execution.debug.log:1-58`；`G/telemetry-export.log:1-36`；`G/braid.log:1-7` | 所检查的运行日志没有 extension 加载成功/失败记录或 RPC 工具清单。不能据日志缺项断言扩展未加载。 |
| `G/braid.log:6-7` | 唯一直接相关运行错误：`session terminal with error … provider disconnected`；下一行记录 `Agent Context was replaced … continuation=true`。这两行没有写 extension、RPC 或工具错误。 |

以上仅是本 run 可见材料的摘录；没有进行模型调用、重跑或新测试。
