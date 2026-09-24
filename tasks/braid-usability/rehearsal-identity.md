# 隐式 CLI 身份的实施预演

状态：只读实施计划；未修改 Braid 源码、未运行测试或模型。以 `/Volumes/WorkSSD/Development/factory26/sources/braid` 当前工作树为准。该工作树已有其它任务的未提交修改：`src/config.rs`、`src/provider/codex.rs`、`docs/20-product-tdd/app-server.md`；身份接线实施时须保留这些改动，尤其 Codex `thread/start`、`thread/resume` 新增的 `modelProvider` 参数。

## 最小落点

只给 `provider_sessions` 增一个可空且唯一的 `cli_binding_id TEXT` 字段（下一条 schema migration）。一个原生执行实例对应一个不透明 binding ID；它经 `BRAID_CLI_BINDING_ID` 进入原生进程环境，并原样存入对应 session 行。`BRAID_STATE` 存当前 state 目录。使用现有的 `Uuid::now_v7()` 生成 ID 即可；不需要新的身份服务、哈希层、按目录查询“最新会话”或按 turn 发令牌。

在 `src/agent_session.rs` 定义内部 `CliContext { state: PathBuf, binding_id: String }`。`src/group/session_manager.rs::SessionManager` 持有现有 state 路径，在真正启动/恢复物理进程前生成 `CliContext`；它的 `resume` 活句柄快返分支不生成新 ID。`SessionFactory::start/resume` 增 `CliContext` 参数，转交 `src/provider/factory.rs` 的 `PiSessions`/`CodexSessions`。`CreatedSession` 仅多返回同一个 `cli_binding_id`，让 manager 的 `start` 向上返回 `(provider_id, binding_id)`、实际执行恢复的 `resume` 返回 `Some(binding_id)`（活句柄快返为 `None`）。Pi 的 `PiProvider::spawn` 和 Codex 的 `CodexProvider::connect` 都必须在原生进程启动命令上设置两个环境变量；不能等 `provider_session_id` 返回再设置，因为那时进程已启动。两种 provider 的 session ID 都在创建协议返回后才可用：Pi 的 `new_session`/`get_state` 在 `src/provider/pi.rs::start_session`，Codex 的 `thread/start` 在 `src/provider/codex.rs::start_session`。binding 因而是预先生成的临时键，创建成功后才同 provider ID 落库。

四个新 session 入口分别是 `src/group/issue_agent.rs::materialize_issue_assignment`、`src/group/pr_agent.rs::materialize_pr_assignment`、`src/group/dispatch.rs::materialize_context_reset` 和 `reactivate_work_item_agent`；均在 `sessions.start` 返回 `(provider_id, binding_id)` 后、下一次模型 dispatch 前调用相应 store 完成函数。让 `complete_agent_assignment`、`complete_context_reset`、`complete_work_item_reactivation` 在现有事务插入 `provider_sessions` 时一并写 binding ID；如果登记失败，移除刚创建的 handle，避免无身份的原生进程继续运行。`src/group/dispatch.rs::start_next_agent_turn` 随后可删去附加在用户文本中的 `--state/--writer-turn` 前缀，内部 `TurnClaim` 和 turns 表继续保留供调度、审计及失效判断。

## 恢复和失效顺序

Issue/PR 恢复分别在 `src/group/issue_agent.rs::resume_issue_provider_sessions` 和 `src/group/pr_agent.rs::resume_pr_provider_sessions`：先核对兼容性并围住遗留活动 turn，再在启动前把旧 session 的 binding ID 清空；由 manager 为真正需要新原生进程的 resume 生成**新** binding 并启动进程。成功后扩展 `src/store/mod.rs::record_provider_resume`，在登记 resume 时间/次数的同次更新中写入新 ID，然后才允许后续 dispatch；失败路径仍由现有 `block_provider_session` 处理。清空和登记各是一行的受生命周期约束更新，不是另一套会话机制。若 `SessionManager::resume` 发现原 handle 仍活着并直接返回，应保持原 binding，不能无端轮换。

Context reset 在 `src/group/dispatch.rs::materialize_next_context_reset` 先 `SessionManager::remove` 旧 handle，`complete_context_reset` 同一事务插新 session、把旧 session 标为 `replaced`。旧 binding 即使仍留在历史行，也不能通过生命周期校验。重指派在 `src/objects.rs::set_assignee` / `edit_with_parent_and_assignees` 先把旧 assignment、agent、session 变为 `stopping`；`src/group/worker.rs::retire_reassigned_sessions` 再证明原生进程 teardown 并退休；新 assignment 走正常 materialization。旧 binding 不得被移给新 assignment。封存 run 也继续由现有 `local_run.lifecycle` 拒绝控制写入。

`src/cli/mod.rs::run` 在 Agent 环境从 `BRAID_STATE` 和 `BRAID_CLI_BINDING_ID` 取值，正常对象命令不要求 agent 传身份参数；宿主诊断可保留显式 `--state`/`--external`，但 Agent 环境不能用这些标志改选身份。`src/objects.rs::LocalObjects::writer` 应在**同一对象写事务**中由 binding ID 找到当前 provider session 及其 `starting/running` turn，投影出原有 `Writer { group, node, turn }`；沿用现有 run、session、assignment、agent、context reset、pending invalidate 检查，不可先在 CLI 查出 turn 再进入另一个事务，以免检查与写入之间失效。`local_comments.writer_turn` 当前直接取入参 `turn`，需要改取已解析的 `writer.turn`，否则隐式调用会丢作者 turn。读命令可凭环境定位 state；写命令没有当前可写 turn 时明确报错，不猜“最近 turn”。

## 环境传递的已知事实与待验证点

- Braid 的 Pi 路径已在 `src/provider/pi.rs::spawn` 将 `braid` 所在目录加入 `PATH`。当前已装 `@earendil-works/pi-coding-agent` 0.85.1 的 `dist/core/tools/bash.js::resolveSpawnContext` 使用 `getShellEnv()`；`dist/utils/shell.js::getShellEnv` 展开 `process.env`，只调整 PATH。内置 bash 的本地代码未过滤 `BRAID_*`，所以主 Pi 工具进程的继承有源码依据；原生 sub-agent 的完整环境链未逐层查实，真实运行仍需观察一次。
- `src/provider/codex.rs::connect` 为每个 session 启动独立 app-server，并设置 `CODEX_HOME`/`BRAID_AGENT_RUNTIME`，目前没有 Pi 那样为 shell 补 `braid` 所在 `PATH`；身份实施须在该 `Command` 上同时补 PATH 和 binding/state 环境。已装 Codex 0.155.0 是本地二进制；这里未取得其工具 shell 如何继承 app-server 环境的源码证据，不能声称已验证。真实 Codex 执行时需观察工具内 `braid issue view` 能找到命令并由环境完成一次带作者的对象写入。
- Pi `start_turn` 有 `state.process.is_none()` 时重新 `spawn` 的分支；正常启动和恢复已先 `spawn`，连接断开会把 handle 标为 unavailable。实施时让该分支沿用同一 handle 的 `CliContext`；若实机发现它可在未经过 SessionFactory 恢复的情况下更换仍可用的物理进程，再收紧该分支的轮换规则。无需让 Braid 接管 Pi sub-agent 生命周期。

## 线性落地顺序与最少观察

1. 增迁移和 `CliContext`，扩展 factory/start/resume 参数及 `CreatedSession.cli_binding_id`；在 Pi、Codex 原生进程启动处接入环境，保留当前未提交的 Codex `modelProvider` 改动。
2. 在四个新 session 完成事务写 binding ID；在两个恢复入口轮换 ID，按现有 reset/重指派生命周期拒绝旧 binding。
3. 让 CLI 默认读取环境，令 `LocalObjects::writer` 在对象写事务内解析 binding/当前 turn，修正评论审计字段；移除 dispatch 文本里的身份前缀及对应 Agent 指引。
4. 获得真实执行授权后，各对 Pi、Codex 观察一次工具命令继承；另观察 resume/reset 后旧 binding 的写入被拒、新 binding 可写，以及同一成员两个工作项的作者归属。预演阶段不运行这些检查。

目前没有证据表明必须重写调度或管理 Pi sub-agent 进程。若 Codex 工具不继承 app-server 环境，这会阻断所选接线；须先在真实执行中确认，再决定是否用 Codex 现有可配置工具环境入口补接，不能在预演中假定它一定继承。
