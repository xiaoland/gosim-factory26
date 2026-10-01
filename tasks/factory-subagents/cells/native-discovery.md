# Pi 原生子代理入口与完成回执：07 冻结运行核查

只读截面 2026-09-28 05:45 UTC；实际使用 ledger 见[完整视图](usage-map.md)。核对对象是 WSL DeepSeek attempt-07 两题的冻结 `workspace/observed-agent/agent/runtime/node_modules/pi-subagents@0.56.0`、角色文件、`work/native-homes` JSONL 与 `subagent-artifacts`，并与仓库同版本包源码对照。07 后续热修复不追溯改变该冻结制品。常规 Pi JSONL 隐去完整系统提示（子 transcript 首条为 `[prompt redacted]; live Prompt Audit only.`），所以以下把**实际模型可见的工具结果/调用**与**注册源码能推知的说明**分开。

## 实际入口与身份边界

冻结 `pi-subagents/src/extension/index.ts` 注册 `subagent`，参数来自 `schemas.ts::createSubagentParamsSchema()`；默认工具描述来自 `tool-description.ts::DEFAULT_SUBAGENT_TOOL_DESCRIPTION`，并加 `promptSnippet`/`promptGuidelines`，明确先 `{action:"list"}`、执行时省略 action，单个子角色用 `{agent,task}`，只有显式多步骤/并行才用 `workflowScript`。schema 的 `agent` 是**Pi 角色名**；Braid `assignee` 是协作成员身份，二者不互换。默认描述没有内嵌当时五个角色的逐项名字，需调用 `list` 才可得可执行名单。

GitHub 07 #5 在 05:34:16、#6 在 05:35:33 实际调用 `{action:"list"}`。返回五个 executable `advisor/browser-operator/executor/explorer/vision`，均标 `context:fresh` 并附中文 description。随后父会话以 `agent:"vision"` 成功启动，说明角色发现与选择路径在新窗**可用**；Flash 02 的 `agent:"qwen"`、`agent:"minimax"` 报 `Unknown agent` 是模型把 Braid 成员名用在 Pi 角色参数，不能归咎于角色目录未装入。可见性缺口是主会话必须主动 `list`；角色正文/完整 frontmatter 不会逐项出现在该返回中，若需要核实工具/模型/技能还得 `{action:"get"}` 或读角色文件。07 #6 为诊断误拒实际自行读了 `/workspace/submission/agent/agents/pi-deepseek-fast/agents/vision.md`。

冻结角色声明 `defaultContext:fresh`、`inheritProjectContext:false`、`inheritSkills:false`、`systemPromptMode:append`；`settings.json` 只设置 `subagents.disableBuiltins:true`，对应 home 无 `extensions/subagent/config.json` 来覆盖默认 context。07 父调用未指定 `context`，子 transcript 以独立 task 开始、没有父聊天正文；实际 `list` 报 `fresh`。这组成强证据支持 fresh 配方被选中，但完整系统提示已脱敏，不能声称仅凭 transcript 逐字核验了所有继承项。`tool-description.ts` 还明确：若以后全局 `defaultSubagentContext` 被设置，它会在省略 `context` 时覆盖角色 `defaultContext`；若要强制角色声明，调用方应传 `context:"profile"`，或保持当前无全局覆盖。

## 两个独立接口问题

**只读视觉任务被语义鉴权误拒。** GitHub #6 05:35:39 与 05:35:43 的请求明确求“视觉解读”“只读视觉解读”，要求抄录图片上 `Create new file`、`Commit changes` 等英文控件名。两次启动结果均是 `Agent 'vision' was given an implementation task, but its tool allowlist has no mutation-capable tools`，无子会话。05:36:30 父改成较短的“只读图片解读”后成功，05:37:46 收到完整报告并在 05:38:05 总结图片差异。这不是视觉模型不会读图。上游 `pi-subagents/src/runs/shared/task-intent.ts::classifyTaskMutationIntent` 对任务全文做英文动词正则，未识别被引用的界面文案；`completion-guard.ts::validateImplementationToolContract` 据此在只含 `read` 的 vision 启动前拒绝。foreground、async 单子与 background workflow runner 均调用该校验。函数首行 `completionGuard === false` 直接返回，且完成期 mutation guard 同受此开关控制。因此四个非实施角色声明 `completionGuard:false` 可去掉这类不可靠的自然语言“应编辑”判断，executor 保留实施证据 guard。限制是 advisor/explorer/browser-operator 含 `bash`，上游把 `bash` 当可变更能力，本来就不会在启动期同样拦截；其只读边界由角色指令约束，非硬权限。不要为 `Create new file` 等控件名不断添加关键词特例。

**后台作业等待语义易混。** `pi-subagents/src/runs/background/wait-tool.ts` 注册 `subagent_wait`，只等当前会话的原生 async run；冻结 `pi-background-bash/extensions/background-bash.ts` 只注册 `bash`，PBB `bg*` 作业靠完成 `custom_message source=pi-background-bash` 或 `pbb status/tail` 取得结果，不注册同名 wait 工具。GitHub 07 成功 launch 的工具结果给出 UUID run ID，并明确由 Pi completion wake 与 `subagent_wait({id:"..."})` 等待；这套回执本身正常，两个父会话均收到 `subagent-notify` 并消费。Sheet 07 某父会话却在 05:38:56 用 `subagent_wait({id:"bg001"})`，立即返回 `No active run matched "bg001"`；其他无 ID wait 也返回本会话无原生 run。它等待的是 PBB 作业，不是另一个同名工具覆盖。最小澄清可放现有 `subagent` 工具用法段：`bg*` 用 PBB 完成消息/`pbb status|tail`，`subagent_wait` 只用原生子代理 UUID run ID；不需要新包装或固定角色流水线。

## 判断

07 的主要发现不是“子代理 API 不可用”：`list`、角色装入、async 启动、通知与父消费均有正例。真实阻断是上游通用 task 文本分类拿参考截图的 UI 英文当写代码命令，另有 PBB 与 Pi 两种后台概念被模型混淆。修复优先级应是删除非实施角色的语义交付 guard、保持角色工具边界、清楚标出两套作业 ID；是否委派仍由父任务是否有可分离的输入/返回决定。对子代理的使用效果与未委派机会见[usage-map](usage-map.md)，不以工具调用数判断进展。
