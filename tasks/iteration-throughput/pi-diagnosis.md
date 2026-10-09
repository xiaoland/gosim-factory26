# Pi teardown、session 与 recovery 边界诊断

本调查只解释已保存故障属于哪一层，并设计下一阶段最小对照；没有启动模型、benchmark、运行中任务或修改源码。结论按现有证据强度排序：目前没有证据说明 Pi 原生 RPC 存在“反复 teardown 失败”的产品缺陷。最强的未闭合问题在 `pi-subagents` 与自有 lifecycle 扩展的终态证明；session 身份问题是消费者把路径当权威；明确 `Failed` 后静默停摆和 blocked worktree 丢失则属于 Braid store 的恢复语义。

## 证据边界

Pi 0.85.1 的 RPC 文档明确区分了几件事。文档来自本机实际安装包 `/Users/lanzhijiang/Library/pnpm/global/v11/1484d-1a0aea79857-e3fc93e34b677276/node_modules/@earendil-works/pi-coding-agent`：`prompt` 成功只表示已接受或排队，后续失败通过事件流报告（`docs/rpc.md:43-76`）；`abort` 只承诺中止当前 operation 并等待 session idle（`docs/rpc.md:124-135`）；独立 shell 命令另有 `abort_bash`（`docs/rpc.md:539-550`）；`get_state` 同时返回稳定的 `sessionId` 与可能变化的 `sessionFile`（`docs/rpc.md:185-214`）。扩展若创建 session-scoped 资源，官方要求扩展自己在幂等的 `session_shutdown` handler 中清理（`docs/extensions.md:220-225,516-525`）。因此，RPC 的 `abort`、extension cleanup 和操作系统进程树终止不是同一个合同，不能相互替代。

原生反证也存在。2026-09-21 的 Pi+Braid 自编辑探针在未启用 native sub-agent 时完成 9 个物理会话、7 次 context replacement 和最终交付，且无残留 PID（`runs/reports/2026-09-21-braid-collaboration-pi-probe.md:3-20`）。Pi 第二次原生能力场景也已完成图像、executor 和双 browser-operator；失败发生在父 session 路径归档，不是 child 执行（`tasks/multi-agent-integration/cells/capabilities-ready.md:38-42`）。更早的 SSE JSON 截断同时出现在 Pi 与 Codex，且三次隔离重放均成功，优先指向共享网关/传输，不能算 Pi lifecycle 证据（`runs/reports/2026-09-21-braid-svc-checkpoint.md:39-47`）。

## 1. 子树终态证明仍混合了“控制请求”和“已经停止”

这是当前证据最充分、仍需设计处理的问题。2026-09-22 08:54–10:48 的资格验证反复暴露同一边界（耗时归因见 `tasks/iteration-throughput/profile-2026-09-22.md:5-10,29-37`）：

- `runs/integration/20260922-000737-pi-braid-5f89e9/check.json` 中 foreground child 已运行且 heartbeat 后来静止，但 Braid 先 abort 父 turn，lifecycle bridge 查询时已看不到 run，receipt 的 `children` 为空。问题是 Braid adapter 的调用顺序使扩展丢失控制面，不是 Pi `abort` 违反合同。
- `runs/integration/20260922-005345-pi-braid-58a8f8/check.json` 与随后 09:11、09:20、09:28 三次 WSL run 中，扩展曾把 `control_inactive` 当终态，但 writer 在 teardown request 后仍持续写约 10 秒；`control_inactive` 被真实文件输出直接反证。
- 顺序改为 lifecycle hook 先 fence/控制，再由 Braid 关闭并检查自己拥有的 Pi 后代树后，`20260922-093409-pi-braid-dc823e` 的 foreground replacement 首次取得 `stopped` receipt、旧 writer 拒绝和新 root；`20260922-095057-pi-braid-643821` 与 `20260922-095417-pi-braid-615aff` 的 foreground/background replacement 及最终 delivery 均完成。后者最初只因归档路径失败而把总体 check 记成 failed，后续在 `runs/_retained-workspaces/f26-braid-_x8vdt25/archive-replay/native/manifest.json` 以 21 个 session、0 个 archive error 离线闭合。

归属如下：

| 层 | 已知 | 未知或不足 | 反证/限制 |
| --- | --- | --- | --- |
| 原生 Pi | `abort` 只保证当前 operation idle；退出时触发 `session_shutdown`，由扩展清理自己的资源。 | Pi 核心不宣称认识 `pi-subagents` 的 detached runner，也没有“所有扩展后代均已退出”的 RPC。 | 无 sub-agent 的 9-session replacement 已通过，不能把接缝故障归为原生 Pi。 |
| `pi-subagents` | 提供 `status`/`interrupt`/`stop`、foreground completion 与 background process-terminal/lease 材料；生命周期调查已记录这些合同（`tasks/multi-agent-integration/research-pi.md:8-17`）。 | 0.56.0 在 observer 不可用、parent 提前 abort、detached runner 已换进程组时，`stop` acknowledgement 到真实 terminal 的保证仍未由同一无模型对照证明。 | `control_inactive` 与 heartbeat 持续并存，状态投影不能单独作为 oracle。 |
| 自有 lifecycle 扩展 | 能在 tool boundary fence 新 subagent，并用 parent/run/child 身份定向发 `interrupt` 或 `stop`（`harness/extensions/factory-subagent-lifecycle.ts:419-515,591-618`）。 | 当前 `proofComplete` 对 foreground 接受 `controlRequested || controlInactive`，对 background 只要求 `childSessionId && controlRequested`（同文件 `:334-337`）；类型中声明的 `status_terminal`、`process_terminal_observed`、`active_lease_released` 没有进入 receipt 或完成判定。 | 单元检查也只断言 background `{control_requested:true}`（`tests/pi_lifecycle.test.mjs:30-61`），所以它证明了控制调用，不证明 detached process terminal。 |
| Braid adapter | 现在先捕获后代、调用 hook，核验 `ready` 身份，再关闭 native tree，最后把 receipt 改为 `stopped` 并在 replacement 前落盘（`sources/braid/src/provider/factory.rs:433-505`）。 | Braid 的 process-tree 证明能覆盖它仍拥有的 parent/foreground 后代；是否覆盖已脱离该树的 background runner 必须由扩展的 process-terminal + lease 证明补齐。 | `tasks/multi-agent-integration/scripts/braid-scene.py:141-162` 的真实 oracle 包含 heartbeat 静止、replacement 顺序和 receipt，但 background receipt 判据目前仍只查 `control_requested` 与 parent tree terminal。 |

设计判断：不要再扩大 Braid 对 `pi-subagents` 内部状态的理解。Braid 只持有两段通用合同：hook 返回精确 fence/parent/children 的 `ready`，以及 Braid 自己拥有的 native tree 终止。对于 detached background，lifecycle hook 必须在 `ready` 前提供 `processTerminal.state=observed` 且 canonical session lease 已释放；缺任一项返回 `unknown`。控制请求本身只能写入诊断字段，不能升级为 terminal proof。

## 2. session UUID 是身份，路径只是可定位材料

原生 RPC 已同时公开 `sessionId` 和 `sessionFile`。历史实现曾在 JSONL header 尚未写出时从路径反推 UUID，后改为直接采用 RPC `sessionId`（`tasks/multi-agent-integration/cells/runtime-ready.md:25-29`）。`20260921-233730-pi-native-f53672` 又显示父路径可能是无 header 的 alias；严格归档因此拒绝，即使三个 child session 与工具产物都存在（`tasks/multi-agent-integration/cells/capabilities-ready.md:38-42`）。`20260922-095417-pi-braid-615aff` 的首次 manifest 也对两个已替换 root 报源路径不存在，但按 Pi UUID 在保留工作区重放可唯一找到规范文件，最终得到 21/21 完整归档。

这属于 adapter/归档消费者和自有 lifecycle 的身份权威问题，不是原生 Pi session 损坏。当前扩展已经用 header UUID 校验 reported file，并尝试 canonical sibling（`harness/extensions/factory-subagent-lifecycle.ts:363-393`）；Braid 也保存 RPC 返回的 native UUID。仍未知的是 cold resume、session replacement 与 archive 延迟同时发生时，0.85.1 是否会继续返回 alias，及 package 升级后目录布局是否变化。判据应保持：关联键只用 UUID；路径必须由“header UUID 唯一匹配”重新定位；找不到或多匹配就是证据 `unknown`，不能按 mtime 或 basename 猜。

## 3. `Failed`、`Unknown` 与 worktree 接管是 Braid 恢复语义

固定批次中 Pi 内部重试耗尽后返回明确 `Failed`。旧 Braid 将 batch 标为已消费，OPEN Issue 随即无后续 runnable work；再启动又从空 physical session 开始。这不是 Pi 应该替 Braid 决定的策略。Braid `690522e` 在 store 边界对同一 OPEN work-item 的同一输入只重放一次，第二次 `Failed` 返回 incomplete；`Unknown` 继续走原有 at-least-once reset/replay（`sources/braid/src/store/mod.rs:5036-5143`，执行记录见 `tasks/multi-agent-integration/cells/runtime-ready.md:37`）。

随后，新 generation 只继承 retired assignment，未继承 blocked assignment，导致重复创建仍被旧 assignment 占用的分支；`673c119` 改为从最新 retired 或 blocked assignment 转移同一 worktree/head/脏内容（`sources/braid/src/store/mod.rs:3871-3925`，执行记录见 `tasks/multi-agent-integration/cells/runtime-ready.md:39`）。因此这两项归 Braid store/lifecycle，不归 Pi adapter、`pi-subagents` 或原生 Pi。

已知修复有单元/集成证据，且 `pi-verification BookStack` 后续正常交付；但本批两项分数依赖确定性人工导出，只证明应用质量，不证明当时 Braid 交付链正常（`runs/reports/2026-09-22-multi-agent-lite.md:12-22`）。仍未知的是 crash 恰好发生在 stopped receipt 已落盘、replacement 尚未物化的窗口时，重启能否只接管一次；以及一次重放前 provider 已完成外部副作用但终态丢失时，CLI 幂等是否覆盖全部操作。下一阶段应只验证这些切点，不再增加重试层或从模型错误文案推断恢复策略。

## 下一阶段最小三层对照 spike

三层都使用同一个 `writer.py`：每 200ms 向 JSONL 追加 `{pid,ppid,pgid,sid,parent_session_id,child_session_id,time}`，收到正常终止信号时追加 terminal 行；宿主另存 `ps -eo pid,ppid,pgid,sid,lstart,args`。每层使用新的 `mktemp -d`、独立 `HOME`/`PI_CODING_AGENT_DIR`/session-dir，不访问网络。需要触发 agent/tool call时使用本地确定性 OpenAI-compatible stub，固定返回同一 subagent/bash tool call；不调用付费模型。controller 全自动触发 edit、kill、restart 和观察，运行时无用户介入；Agent 只看到普通 issue/PR/comment/assignee CLI，不接触 Braid 或agent-profile等内部概念。

| 层 | 确切操作 | 通过判据 | 失败归属 |
| --- | --- | --- | --- |
| A. 原生 Pi RPC | 以 Pi 0.85.1 启动 `pi --mode rpc --session-dir <tmp>/sessions --no-extensions --no-skills`；发送 `get_state` 保存 `sessionId/sessionFile`；发送带 request id 的 `bash` 启动前台 writer，出现两行后发送 `abort_bash`；再关闭 RPC 进程。随后用 `--session <先前文件>` cold resume，再取一次 state 并重复。 | `abort_bash` 返回 `cancelled:true`；writer 1 秒静止且 PID/PGID 消失；RPC 进程退出；resume 后 UUID 与 JSONL header 唯一一致，文件可变化但不能生成第二身份。 | 若只在 A 失败，才形成原生 Pi/RPC 或平台信号处理问题；`abort` 不用于替代 `abort_bash`。 |
| B. Pi + `pi-subagents` + lifecycle | 在同一 core 上显式加载固定 `pi-subagents` 0.56.0 与 `factory-subagent-lifecycle.ts`。本地 stub 让 parent 分别启动 foreground、background child，child 只运行同一 writer。出现两行后写精确 `teardown-request.json`，通过 RPC prompt 调 `/factory-subagent-stop`（extension command 可在 streaming 时立即执行，见 Pi `docs/rpc.md:56-76`），再终止 parent。两种 mode 分开运行。 | receipt 的 fence/parent/run/child UUID 全部匹配；foreground 至少有定向 interrupt，最终由 parent tree terminal 证明；background 必须额外保存 `processTerminal.state=observed`、canonical lease released/free，并确认 detached PID 消失；两者 receipt 后 2 秒无新写入。只有 control acknowledgement、`control_inactive` 或文本 `stopped` 均判失败。 | A 通过而 B 失败，归 `pi-subagents` 控制合同或自有 lifecycle 解析/证明；用原始 RPC reply 和进程 oracle再二分。 |
| C. 经 Braid | 用同一 native template/stub 启动一个最小 root Issue；输入只要求调用 subagent 运行 writer 并等待。controller 在 heartbeat 两行后用宿主 `issue edit` 改 description，触发 context reset。分别在“request 已写但 receipt 未写”和“stopped receipt 已写但 replacement 未创建”两个位置杀 Braid，再以同一 state 重启。另让 stub 对同一 batch 连续返回两次明确 `Failed`。 | 旧 writer 立即被 Braid writer fence；旧 child 先静止并有 matching `stopped` receipt，之后才出现新 root；replacement 复用同一 worktree/脏文件且用新 physical UUID。第一个 crash 点重启必须保持 blocked/unknown、不得创建竞争 writer；第二个 crash 点只创建一个 replacement。明确 `Failed` 只重放同一输入一次，第二次 incomplete；`Unknown` 保持 at-least-once。全程无残留 PID、无第三次模型请求。 | A/B 通过而 C 失败，归 Braid adapter 的顺序/进程所有权，或 store 的 reset/replay/worktree ownership；不得回退为“再跑一次完整生成”。 |

执行顺序必须在每层通过后才加下一层；foreground 与 background 是 B 层的两个必要子例，不扩成模型或 profile 矩阵。A/B/C 共用同一 writer、超时和进程 oracle，任何更高层失败都保留下层已通过证据。B 层若无法从实际 0.56.0 得到 background process-terminal observed + lease released，应停在明确 `unknown`，这已经足以否定进入无人值守正式批次，无需启动 benchmark 证明同一缺口。
