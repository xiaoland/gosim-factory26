# Codex 原生配置与证据入口

2026-09-21，只读设计调查；没有 LLM 调用、依赖安装或运行源码改动。

本机 `codex-cli 0.155.0`。运行 `codex app-server generate-json-schema --experimental --out runs/agent-profile-presets/codex-schema`，从当前二进制取得协议 schema；该产物位于 Git 忽略目录。它证明接口形状，不证明 K3/比赛网关已支持对应能力。

- `ThreadStartParams` 含 model、modelProvider、config、developerInstructions、baseInstructions、cwd、ephemeral。保留核心默认系统提示，用 developerInstructions 增加 Braid/profile 指引。
- `ThreadStartedNotification.Thread.source.subAgent.thread_spawn` 可表示 parent_thread_id、agent_role、depth；Thread 本身含 agentRole 等身份信息。`ThreadTokenUsageUpdatedNotification` 以 threadId/turnId 关联 usage。归档应从这个关系发现子会话，不能仅遍历 Braid 主会话登记表。
- 固定版本的 [config schema](https://github.com/openai/codex/blob/rust-v0.155.0/codex-rs/core/config.schema.json) 支持 `agents.<name>.config_file/description`、默认子模型/推理和 enabled；role config 使用原生 TOML 配置层。schema 已保存为 `runs/agent-profile-presets/codex-config.schema.json`。不依赖本机个人配置，Factory 生成隔离 CODEX_HOME 下的角色定义和技能配置。
- 固定版本的 [exec_env.rs](https://github.com/openai/codex/blob/rust-v0.155.0/codex-rs/core/src/exec_env.rs) 明确工具 shell 环境注入 CODEX_THREAD_ID；CODEX_SESSION_ID 表示共享 root session，不能单独作为主/子浏览器隔离标识。原文快照在 `runs/agent-profile-presets/codex-exec-env.rs`。

官方[子代理说明](https://developers.openai.com/codex/subagents)和[配置参考](https://developers.openai.com/codex/config-reference)补充配置含义，但网站最新说明与固定二进制可能不同，实施以该版本 schema/源码及实际预演为准。

最小接法：按 Braid profile 生成原生配置模板，每个 Braid 会话树拥有独立 HOME/CODEX_HOME；继续通过 app-server 驱动；原生角色用 TOML 声明，浏览器 wrapper 按 run + CODEX_THREAD_ID 命名；收集原生父子关系并复用现有 rollout/SVC 分析。Braid 不调度 native children。

仍需验明：自定义网关模型是否得到原生 sub-agent 工具并成功执行、角色指令/技能继承、子会话事件可见性与落盘、usage 是否包含子调用、父会话重建/取消时子树如何收尾、K3 的 Responses→Chat 工具/图像/streaming 链路。不能把本次无模型 schema 调查当成这些真实能力已通过。
