# 原生 Pi 子代理在父会话重建后的连续性

调查范围：官网 GitHub 来源链中根成员 `@glm-1` 的三个 `executor`，见 [hosted-github-usage.md](hosted-github-usage.md)。只读核对锁定的 `pi-subagents@0.56.0`、当前 variant observer 与官网 ZIP。没有操作运行或构造 Factory 探针。结论把**原生接口能做什么**与**官网现场实际证明了什么**分开。

## 已证根因

初始官网 run `38dc20e99fa5` 中，父 Pi session `01a0e299-90fd-7652-8f9c-ac54e0f5e402` 11:24:54 启动异步 `executor` UUID `7befc0b1-...`，11:26:02 为它 arm 非阻塞等待。重建后的父 session `01a0e29d-9511-719a-9662-a40b1351d755` 11:27:55 又把同一 rebase 交给新 UUID `76d53282-...`；11:28:16 只查询新 UUID 的 status，未查询旧 UUID。旧子 transcript 记录直到 11:34:18，新子直到 11:33:59。二者在重叠期都调用 bash/read、共用根 Issue worktree，但未证实同一工作树文件并发写入。g01 11:56:47 才启动；12:05 的第三次 UUID `56af2cee-...` 属于 g01，并以 SIGKILL 结束，不能把三次都归 g01 或 g05。

`pi-subagents` 的状态与投递按**物理 Pi session/process**划界：

| 接口 | 源码事实 | 重建含义 |
|---|---|---|
| `subagent({action:"status"})` 无 id | `src/runs/background/run-status.ts::inspectSubagentStatus` 调用 `listAsyncRuns(..., sessionId: state.currentSessionId)`，只列当前 session 的 active async runs。 | 新父即使与旧父同 Braid 成员，也不会在默认列表发现旧 UUID。`action:list` 列的是可用角色，不是运行列表。 |
| `subagent({action:"status",id:<完整 UUID>})` | `run-id-resolver.ts::exactAsyncLocation` 先按共享 `asyncDirRoot/<id>` 或结果文件解析；`run-status.ts` 的普通状态展示不拒绝异 session（`view:"transcript"` 明确拒绝）。根目录默认是 `TMPDIR/pi-subagents-uid-0/async-subagent-runs`；本 variant 的 `TMPDIR=work/tmp`。 | **若**新父拿到 UUID、共享临时目录仍在且 status/result 未清理，可定向读旧状态；这不是自动发现，也不保证冷恢复有效。官网 status 返回曾显示 `/workspace/template/.factory26/.../work/tmp/pi-subagents-uid-0/async-subagent-runs/76d...`。 |
| `subagent_wait({id,nonBlocking:true})` | `wait-subscriptions.ts` 记录原 `sessionId`，只 `restore`／`reconcile` 当前 session 的记录；`subagent-wait.ts` 的运行列表亦以 `currentSessionId` 过滤。 | 新父不会继承旧父订阅；把旧 UUID 再传给新父 wait 也不是受支持的跨 session 等待。 |
| 完成通知 | `notify.ts::deliver` 要求 result `sessionId===state.currentSessionId`，异步还要求 `completionOwnerId===state.completionOwnerId`；`result-watcher.ts::ownsCompletion` 同样双重过滤。`shared/completion-owner.ts` 的 owner 是一个 Pi 进程内稳定 UUID。 | 旧子完成不会自动投递给重建的新父进程／session。原生 owner 约束防串线，应保留。 |
| 原生恢复/控制 | `async-resume.ts` 可读已保存的子 session，但调用方提供当前 `sessionId` 时拒绝异 session；steer/stop 也校验当前 session。未发现 adopt/rebind 旧运行到新 session 的 API。 | 不应以新父 `resume`、`wait` 或偷偷改 status.owner 冒充连续性。 |

修复前的 variant `factory-subagent-observer.ts` 是**被动证据层**。它在各自 `PI_CODING_AGENT_DIR/.factory/session-tree.json` 写父 session ID、子 UUID、role、artifact 路径/状态；新父获全新 native home，自己的 manifest 不读旧 home。官网终态 ZIP 中旧/新两个 home 各保留一个 `executor` UUID，`association_status:partial`、`status:unknown`。这能找回 UUID，却不足以判定旧子仍运行。官网 ZIP 不含 `work/tmp` 里的原生 `status.json`/result，所以不能从归档实证旧 UUID 跨重建时在 status API 中可见，也不能断言前两次终态；其 transcript 和旧 home artifacts 仍有独立证据价值。

## 已实施的被动交接

只改两个现用 variant 的 `extensions/factory-subagent-observer.ts`；未改 Braid、pi-subagents 上游或生成应用。observer 在 `session_start` 从当前 `PI_CODING_AGENT_DIR` 上一级 `work/native-homes/` 读取 sibling `.factory/session-tree.json`，以**旧父原生 session 的 cwd 与当前 `ctx.cwd` 完全一致**作为成员归属条件，再排除当前 session。官网旧 manifest 未存 cwd；同 home 的 `sessions/**/<父 session 文件名>` 首条 `type:"session"` 记录可回填 `cwd`。新 manifest 直接增 `parent_cwd`。同 UUID 合并，完整清单写入新 home 的 `.factory/previous-subagents.json`；首次摘要最多显示最近八个并明确完整索引路径，未决项不因摘要上限从索引消失。

对每个旧 UUID 只投影原生 `async-subagent-runs/<UUID>/status.json` 与 `async-subagent-results/<UUID>.json`；目录来自 `PI_SUBAGENTS_TEMP_ROOT` 或 `os.tmpdir()/pi-subagents-uid-<uid>`，本 variant 的 `TMPDIR=work/tmp`。若两者缺失，明确写 `unknown`，并给出旧 home artifact 入口。产物优先用 manifest 的 `artifact_paths.metadataPath`，缺时按 `child_id` 组合路径（包括 workflow 的 `_0`）；meta 的 exitCode/SIGKILL 是独立结果证据，仅 transcript 或 manifest `status:unknown` **不能**写成 running/completed。冷恢复若 `work/tmp` 未保留，仍可报告已保存的 UUID/artifact，不能承诺进程存活或自动恢复。

新父首个 `before_agent_start` 收到一条简短、持久的上下文消息，列旧 UUID、旧父 session、role、已知状态/不确定性和 `subagent({action:"status",id:"<完整 UUID>"})`。Pi 官方 `docs/extensions.md::before_agent_start` 支持向本次模型输入注入 persistent message。只在新 session 注入一次。对于启动时原生 status 尚为 queued/running 的旧 UUID，observer 以 `fs.watch` 被动观察该 run 的 status 目录和原生结果目录；文件进入原生终态时以 `pi.sendMessage(...,{triggerTurn:true})` 唤起新父，按 UUID 去重，`session_shutdown` 关闭监听。它不启动、停止、重派或改写任何子进程/原生 owner。父仍需核对产物，再决定是否重派同一写任务。

**验证与边界**：上游 `status.json` 经原子写入（rename），结果文件在 `async-subagent-results` 下以 `<UUID>.json` 发布，目录监听与路径来自真实 0.56.0 源码。两个 observer 已通过 `node --check`；未做 Factory 测试或运行探针，仍需在下一次真实父重建中验证消息可见和 `triggerTurn` 唤起。文件事件只能交接原生已落盘的终态：旧子若 SIGKILL 且上游没有写终态 status/result，observer 不推断失败，也不会自行调度恢复。`fs.watch` 自身若失效会记录错误而不会增加轮询状态机；冷恢复丢失临时目录时状态保持 unknown。

证据定位：`runs/e20260928-completed-replay/github/source-workspace.zip` 中三个父 home 的 `sessions/` JSONL 与 `.factory/session-tree.json`、`subagent-artifacts/`；当前源码 `variants/pi-braid-flash-team/extensions/factory-subagent-observer.ts`、`variants/pi-braid/extensions/factory-subagent-observer.ts`；锁定 npm 包 `~/.cache/factory26/runtime-faf60473273ddeed/node_modules/pi-subagents/src/{runs/background,shared}/`。
