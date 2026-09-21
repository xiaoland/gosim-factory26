# Pi 与 pi-subagents 装配合同调查

调查边界：Factory26 四个已认可 variant 的 Pi 路径；只核对 profile 参数、skills/原生子会话、浏览器隔离和证据。未启动模型或安装扩展。版本基线为本机 `@earendil-works/pi-coding-agent` 0.85.1；pi-subagents 上游 `1ac7b5e2652e9571164847ac2905ab4aded92791`（2026-09-21 读取）。

## 可支持的最小接法

1. Factory 为每个 Braid profile 生成隔离 Pi home 与只含该 profile 的 `models.json`/skills/agent 定义；Braid 以 profile ID 选中该环境，并从 `Profile.model`、`Profile.reasoning` 生成 Pi `--provider --model --thinking`。当前 Pi adapter 已只消费独立 `PiConfig`（`sources/braid/src/provider/pi.rs:62-101`），而 Factory wrapper 又固定 `--no-extensions --no-skills`（`scripts/factory.py:297-305`），故两处都必须改为同一冻结 profile 投影；不能让 PiConfig 再成为第二模型权威。
2. 用 `--no-extensions --no-skills` 加显式 `--extension <pi-subagents>`、能力目录内的 profile agent/skill 路径，或等价隔离 settings。Pi 的显式 `--skill` 在 `--no-skills` 下仍加载；pi-subagents agent frontmatter 可逐角色固定 `model`、`thinking`、`skills`、`skillPath`、`inheritProjectContext`、`inheritSkills`、tools 与 extensions。`inheritSkills:false + skills + skillPath` 才是仅选定技能；缺 skill 仅 warning，必须由 Factory 启动检查拦截。
3. explorer/executor/reviewer 等是 pi-subagents 自定义 agent（Markdown frontmatter），不是 Braid profile；实际选择以 technical.md 为准，reviewer 仅属 pi-verification。foreground child 在父 Pi 进程内；background child 在 detached runner 内，均为 Pi session。背景 child 默认加载 ambient extensions；foreground 不重载 ambient extension，但继承其注册 provider。为可重复隔离，应给实际选用的角色显式 `extensions` allowlist/`subagentOnlyExtensions`，并保留 pi-subagents 必需 runtime；不要依赖宿主发现。
4. Pi 原生 session 可由 Braid 的 `workspace/.braid/pi-sessions` 获取（现有 adapter）；pi-subagents background artifacts 给 `runId`、`sessionId`、`sessionFile`、`outputFile`、`children`，并有 `events.jsonl`、`status.json`、`result.json`、`process-terminal.json`。Factory 应归档这些原件，以 `Braid provider session → pi-subagents runId → childId/sessionFile` 建父子边，不靠文件名/时间推断。`/subagent-cost` 汇总 parent+child；Pi 原有 session totals 不自动包含 async child，缺 artifact 只能标 unavailable/lower bound。
5. agent-browser session 由 run + 当前物理 session ID 派生。主 Agent 独立核验纠正了最初报告：Pi 0.85.1 的 docs/extensions.md:2160 和 dist/core/tools/bash.js:119–136 证实原生模型 bash 默认在每次 execute 从 ctx.sessionManager.getSessionId() 注入 PI_SESSION_ID、PI_SESSION_FILE、PI_PROVIDER、PI_MODEL、PI_REASONING_LEVEL；ReadonlySessionManager 也提供 getSessionId。session_start 的事件 payload 无 ID 并不表示整个 API 无此能力。wrapper 可直接消费 PI_SESSION_ID，无需新增 child 环境扩展或修改共享 process.env。仍须在 pi-subagents 的 foreground/background 实际执行中验明此环境保留，以及各子会话 ID 不相同。

本机包完整路径：/Users/lanzhijiang/Library/pnpm/global/v11/1484d-1a0aea79857-e3fc93e34b677276/node_modules/@earendil-works/pi-coding-agent。上述纠正由主 Agent 阅读实际 bash 消费者和 ReadonlySessionManager 类型完成。

## 异步与未验明项

pi-subagents 有 `status`/`interrupt`/`stop`，background stop 及 runner close 有 `process-terminal.json`；只有 live parent 观察 exact detached runner close 且 session lease 释放才是 `observed`，否则为 `unknown`。Braid reset/取消尚未调用这些控制，故不能承诺重建/取消会收尾所有 child：接入时必须以父 session shutdown/reset 映射 stop/interrupt、等待终态 proof 并归档；失败保留 unknown，不能取消 async 功能来绕开。

候选 K3/K2.7/GLM 的 reasoning、image、context/maxTokens 仍未验明。Pi descriptor 必须逐模型声明 `input`（图像）、`reasoning`/`thinkingLevelMap`、窗口/输出上限和 OpenAI-compatible compat；网关只文档化 Chat Completions/SSE，现有资料不足以确认上述三个模型的映射。

## 来源

- 本机 Pi 0.85.1：`.../pi-coding-agent/docs/{skills,extensions,custom-provider,sessions}.md`；类型：`dist/core/extensions/types.d.ts`、`dist/core/tools/bash.d.ts`。
- 本机 Factory：`sources/braid/src/provider/pi.rs`、`sources/braid/src/config.rs:77-115`、`scripts/factory.py:163-181,297-305,449-513`。
- pi-subagents 上游：<https://github.com/nicobailon/pi-subagents/tree/1ac7b5e2652e9571164847ac2905ab4aded92791/docs>，尤其 `agents.md`、`models.md`、`observability.md`、`tool-reference.md`、`configuration.md`。
