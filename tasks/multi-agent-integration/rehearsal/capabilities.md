# capabilities-ready 01：装配预演

边界：2026-09-21 只读核查，基线 `e229e6b`；未启动模型、安装依赖或改动运行源码。本文只回答 Factory→Braid→Pi/Codex 的能力绑定，不定义 preset、V&V 或 Braid 指派语义。

## 结论

批准方案的分层可实现，但当前入口不能装配它：`scripts/factory.py` 将一个 backend/config 投影为一个 `Request.profile`，而 `sources/braid/src/local.rs` 再复制为 `local-issue`、`local-pr`。这不是多个普通 profile 的实现，也没有 profile→native binding。因此能力 Cell 02 不能只改 Factory；必须先由 runtime 接入将 Braid local request 改为 profile catalog 加 profile-id binding。Braid 仍只看普通 profile/binding，不接受 Factory variant/preset。

## 当前实际消费者

| 边界 | 已实际消费 | 缺口 |
| --- | --- | --- |
| Factory | `runtime_environment` 建每次 run 的 `HOME`、`PI_CODING_AGENT_DIR`/`CODEX_HOME`；`braid_request` 传一份 profile、一份 Pi/Codex config；`generate` 写 Pi `models.json` 或 Codex `config.toml`。 | 无 profile catalog、role/skill/extension/browser materialization、effective-config 或 child artifact 归档。 |
| Braid local | `local.rs:20-25,118-135,347-350` 接受单 `profile` + 单 adapter config，并把它克隆成 Issue/PR；`provider/factory.rs` 也只组合一个 native adapter。 | 无按普通 profile ID 选 binding，无法同时承载 Pi 与 Codex 或同核心的异构模型。 |
| Pi | `provider/pi.rs:55-100` 实际传 `--provider/--model/--thinking`、`PI_CODING_AGENT_DIR`、session-dir；模型/推理来自 PiConfig，而 Braid profile 只传给 session/turn。 | PiConfig 是第二模型权威；不传 extension/skill/path；child stop 未接入 Braid reset/cancel。 |
| Codex | `provider/codex.rs:33-49,130-221` 用 app-server、`CODEX_HOME`，在 `thread/start/resume` 传 profile model + developerInstructions，在 `turn/start` 传 reasoning。 | 当前 `scripts/core.py:54-116` 和 Braid 都不物化 role TOML/skill 配置，且未枚举/归档 native child threads。 |

## 最小装配路线

1. Factory 展开 preset 得普通 profile IDs；为每个 profile 生成只读 native template，并为每个 Braid physical session tree 派生独立 `HOME`/native home。运行 binding 只含 executable、该 profile 的 template 路径、材料摘要与必要生命周期入口；provider/model/reasoning 仅由 Profile 持有，不能在 binding 重复维护。API key 继续仅环境注入。
2. Pi template：写该 profile 的网关 `models.json`，显式加载固定 pi-subagents 扩展及选中 agents/skills；以 Markdown frontmatter 固定 native role 的 `model`、`thinking`、`tools`、`skills`、`skillPath`、`inheritProjectContext:false`、`inheritSkills:false`。角色为 explorer/executor/browser-operator；只在 pi-verification 写 reviewer，绝不写 contract-reviewer。`--no-extensions --no-skills` 必须改成明确 allowlist，而不是放开个人发现。
3. Codex template：写隔离 `CODEX_HOME/config.toml` 与原生 agent TOML，采用固定 0.155.0 schema 的 `agents.<name>.config_file`；Braid/profile 指引送 `developerInstructions`，不替换核心 prompt。角色同上，前三 variant 不注册 reviewer。继续走 Responses→Chat adapter。
4. browser launcher 用 `run-id + PI_SESSION_ID` 或 `run-id + CODEX_THREAD_ID` 创建状态目录；绝不能以 role/worktree/CODEX_SESSION_ID 命名。二进制缓存可共享，cookie/localStorage 不可共享。
5. Pi 父调用样例是 `subagent({agent:"executor", task:"…"})`；`status`、`interrupt`、`stop` 是 pi-subagents extension bridge 的 RPC method，不是 Pi 进程 RPC method。Factory 随会话加载一个薄 extension，以 Pi RPC `prompt` 的即时 slash command 进入该 bridge；先封住新的 `subagent` tool call，再控制原生 run。Factory/Braid 记录 provider session → Pi runId/asyncDir → child session/artifact；取消/重置只有在相应 foreground completion 或 background terminal proof 完整时才可收尾，否则 `unknown/blocked`。

## 本机固定边界与证据

* `pi --version` 为 0.85.1；其 `docs/agents.md` 证明 project agent Markdown/frontmatter、显式 skills/skillPath/extensions 与继承开关；其 bash 实现（既有 `research-pi.md` 的 `dist/core/tools/bash.js:119-136`）在每次工具执行注入 `PI_SESSION_ID`。该 ID 是否在 foreground/background child 完整保留，尚需真实场景。
* 实机有 pi-subagents 0.56.0，位于 `~/.pi/agent/npm/npm.disabled/node_modules/pi-subagents`，源码和 docs 表明 `status/interrupt/stop`、async `status.json/events.jsonl/result.json/process-terminal.json` 可用。它在个人 `~/.pi` 下；当前 Factory isolation 明确拒绝该目录（`factory.py:197-207`），所以必须由依赖锁定的受控副本物化到隔离 home，不能引用这个安装路径。
* `codex --version` 为 0.155.0；已保存 schema（`research-codex.md`）支持原生 agent config_file，且固定源码以 `CODEX_THREAD_ID` 标识工具 shell。`Thread.source.subAgent.thread_spawn` 是归档父子边的正确来源；schema/源码不能证明网关 child tool、role/skill 继承或 cancel。
* 本机未发现 `agent-browser` 可执行文件。因此把它写入角色 template 仅是静态配置，02 前需依赖锁定/受控安装；不要把宿主缓存或个人 browser state 暴露进 run。

### Pi native child 收尾的固定接口

Pi RPC 不支持任意 extension RPC。`prompt` 发送 `/factory-subagent-stop ...` 是可用控制入口：Pi 0.85.1 `docs/rpc.md:42-76` 规定 extension command 在 streaming 时立即运行且不需要一次 LLM 采样。Factory 的薄 lifecycle extension 用 `pi.registerCommand`，通过 `pi.events.emit/on` 接入 pi-subagents 0.56.0 已有 `subagents:rpc:v1:request/reply:<requestId>` bridge（`src/extension/rpc.ts:28-33,735-764`），调用 `stop` 或 `interrupt`；不能把该内部 event 名冒充 Pi RPC。

background run 使用 `stop`：pi-subagents `stopAsyncRun` 最终调用导出的 `deliverStopRequest({asyncDir,pid?,kill?,signal?,now?,source?,targetIndex?,childId?})`（`runs/background/control-channel.ts:641-710`），runner 监听 control inbox。停止成功的判据是 terminal status、`process-terminal.json.state == "observed"`、active-run lease 已释放；源码仅在 observed terminal 后释放该 lease（`runs/background/async-status.ts:461-463`）。

foreground run 没有 detached runner、`process-terminal.json` 或 active lease。其已有 `interrupt` 管理分支取 `foregroundControls[runId].interrupt()`，该函数 aborts `interruptController`，并把该 signal 传给 `runSync`（`runs/foreground/subagent-executor.ts:3596-3641,5519-5558`）。Pi RPC `abort` 只承诺当前父操作 idle（`docs/rpc.md:124-135`），不能静态推出所有 foreground child 都已结束。因此 lifecycle command 需先设 closing fence（用 Pi `tool_call` 可阻止 `subagent`，`docs/extensions.md:778-793`）、对每一 foreground run 调 bridge `interrupt`，并等待 bridge `status` 证明对应 foreground control 已移除后写 receipt；实际场景再验明 Pi abort 与此 receipt的先后和 child 不再写入。没有 receipt 时保持 unknown/blocked。

主 Agent 独立核对：foreground 仍有可持久化的 child sessionFile/artifactPaths，见 subagent-executor.ts 的 rememberForegroundRun、updateRememberedForegroundChild；缺少 background process-terminal 不等于没有 child evidence。通过真实 tool result/status/session-tree 关系归档，不能按文件时间猜父子。

### 失败后补齐的协议 spike

第一次 Pi+Braid 联合场景暴露了预演缺口：实现先 abort 父 turn，随后才调用 native teardown，导致 live foreground control 在查询前消失。0.56.0 在 control 仍存活时会由无目标 status 正文给出 run ID；`fleet` 只是有界匿名观测，不应成为生命周期控制依据。修正前先固定以下接口合同，并以 `tests/pi_lifecycle.test.mjs` 的协议级替身逐项执行：

| 场景 | 0.56.0 可见证据 | Factory 行为与出口 |
| --- | --- | --- |
| 无 child | status 无 live run，manifest 没有已观测 child | 不调用 interrupt，允许空树 stopped。 |
| 仅 foreground | live foreground control 由 status 正文给出 run ID | 按 run ID interrupt，等待直接 `subagent:foreground-complete` 的 `runId/taskIndex/sessionFile/agent/state`，缺事件则 unknown。 |
| 仅 background | async snapshot 有活动 run ID | 只按 ID stop；等待 terminal status、process-terminal observed 和 lease released，不调用无目标 interrupt。 |
| foreground + background | status 正文给 foreground run ID，async snapshot 给 background run ID | 两者均定向控制；background 仍需完整 process-terminal/lease proof，互不靠匿名数量推断。 |
| completion payload | event payload 本身含 `source:"foreground"`，不是必然嵌在 `event` 字段内 | 两种形状都解析；session 文件 header 提供 child identity，不能从 message ID 或时间推断。 |

`interrupt` 成功只表示 abort 已发出，不是 child 已停止。若已知 foreground 的完成事件未到达，或 parent session-tree 的 canonical 文件没有可验证 header，联合场景必须失败并保留证据。Braid 必须保持 `native teardown → parent close` 的上层顺序，extension 不用 fleet 猜测被上层提前销毁的控制状态。

## 最小修改面与局部验证

| owner | 最小文件/函数 | 验证 |
| --- | --- | --- |
| runtime | `sources/braid/src/local.rs` Request/config/execute；`provider/factory.rs`；必要时 `config.rs` | 两 profile 的 Issue/PR 只由匹配 binding 启动；未知 ID 在写库前失败；session metadata 记录实际 binding。 |
| capabilities | `scripts/factory.py:runtime_environment,braid_request,generate`；`scripts/core.py:archive_sessions,codex_config` | 无模型 fixture 检查 per-session home/template、Pi argv、Codex `thread/start` 请求、browser state path 与完整归档 manifest。 |
| materials | 新的 Factory-owned harness profiles/roles/skills/dependencies 文件 | resolver 拒绝缺引用/重复 role/reviewer 泄漏；hash 形成 effective-config，且不含 variant/preset 给 Braid。 |

静态检查能证明：选择、隔离路径、allowlist、参数投影、无 reviewer 泄漏与 archive schema。必须真实调用才能证明：K3/K2.7/GLM 兼容、Pi/Codex child 实际使用 role/skill/browser、tool/image/stream、foreground/background ID、child cancel/reset 终态，以及 cookie 隔离。无模型替身只能覆盖调度和参数，不能替代这些证据。

## 对接给 runtime / 联合场景的最小合同

runtime 01 提供 `{profile_id: binding}`，每 binding 有 native-template materializer 与 session-tree root；capabilities 02 提供 role/skill/extension/browser material hashes。联合探针须让父实际调用预定 child，child 写可观察小产物，父读取；再在 child 工作中触发 Braid reset/assignment retirement，收集 Pi `status/process-terminal` 或 Codex native thread stop evidence。无法证实 child 已停时不启动新 writer。
