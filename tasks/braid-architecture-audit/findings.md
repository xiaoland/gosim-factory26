# 审查结论

最重要的结论是：已观测到的数百个 `terminal_contact` 主要包含一个持久队列重放错误，不能只解释为 LLM 互发回执。优先修复事件重放，再恢复明确的冷恢复边界；当前 Context reset 改动还使 Codex 路径确定性阻塞。本次不修改实现、不运行模型、不提交。

审查基线为 `sources/braid` HEAD `89212933c976b889f27de1b8cfe863baf8f6042e` 加当前未提交改动，关键文件 SHA256 见 [原始统计](runtime-summary.json)。[证据说明](evidence.md) 区分归档观察与源码推断；[拓扑与时序](architecture.md) 展示成因。

后续落实（2026-09-28）：第 1、2 项已实现，官网 Sheet run `dd3bda66bcb3` 已证明未完成快照平稳续进，并按用户缩小后的验收范围取消。第 3 项和三类精简均已实现；Codex 普通/steer 收据已核对，完整工作项 reset 尚未端到端验收。另见产品修正状态 [packet](../braid-product-hardening/packet.md)；历史 member_login 唯一键忙重试仍缺专项闭环，不与空批次修复混为一谈。以下源码状态均指上述审查基线，修复接续见 [离线恢复单元](../experiment-infrastructure/cells/offline-resume.md)。

## 1. P0：unknown 重放违反事件所属批次约束，持续生成无输入会话

**状态：真实运行已证实；当前源码仍存在相同因果链。**

| 来源 | provider_sessions 记录 | terminal_contact turns | 没有任何事件成员的 terminal_contact |
| --- | ---: | ---: | ---: |
| GitHub | 465 | 396 | 236（59.6%） |
| Sheet | 686 | 609 | 441（72.4%） |

Sheet 最后一条评论是 #216，时间为 `2026-09-27T16:44:31.225680656Z`；此后仍启动了 96 个 `terminal_contact`，最后一个为 `16:58:27.349049672Z`。这批新会话不能归因于随后新建评论。GitHub 的 236 个空联系 turn 发生在根 Issue 于 `16:01:21Z` 关闭之前，因而全局终态早退出不会覆盖它们。

Sheet turn `01a0e3cd-9f3b-7620-b7e5-e0822c1c6c7f` 的 batch `01a0e3cd-9a45-7cf3-b9a3-6a4e65e88bab` 的 `event_count=0`，没有 `wake_batch_events` 行。实际投递的 `turns/<turn>.md` 只有“请处理 Issue #5”“使用 braid issue view 5 --comments 查看当前内容”，没有发生更新的引用。对应原生 Pi JSONL 最后答复为“Issue #5 已经处于 CLOSED 状态，无需进一步处理”，随后仍创建下一会话。

原因有四个相连环节：

1. `migrations/0001_initial.sql:231` 规定 `wake_batch_events.event_id UNIQUE`，一个事件只能属于一个历史批次。
2. `store/mod.rs:5455` 的 unknown 分支把已经消费的同一个事件改回 pending，再调用 `schedule_event`；旧批次成员记录仍在。
3. `store/mod.rs:2555` 先创建新批次，再 `INSERT OR IGNORE` 成员。唯一约束使插入数为零，但空批次仍保留；`advance_scheduler`（2666）只检查 deadline，使其变为 runnable。
4. 关闭工作项的旧 `direct_contact` 仍 pending。`complete_work_item_reactivation`（3760）会再次调度它；空批次的 turn 无法消费该事件，终结后又进入 sleeping，触发下轮物理会话创建。

这是投递与重放的机械约束错误，应由 Braid 修复；不需要判断评论有没有意义，也不应要求 LLM 用沉默或额外协议绕过。

**最小修正方向：** 保留原批次的历史证据，复用当前 failed 路径已有的“建立新重放事件”方式处理 unknown，不把旧事件重新绑定到新批次。另一种 coherent 方案是允许同一事件属于多个尝试批次、只在单批次内去重；两者选一，不同时建设两套机制。`schedule_event` 与 claim 的共同不变量应是“存在实际待投递输入才有可执行批次”。仅加 `event_count>0` 检查可以止空转，却会继续丢失原请求，不能单独作为修复。已经残留的 pending 事件/consumed 成员关系由 Braid 的恢复路径处理，Factory 不改数据库状态。

**可验证标准：** 从已有真实未完成快照恢复后，每个 ordinary/terminal-contact turn 都能追到实际输入；unknown 的原输入只进入一个当前待处理尝试，原 turn 的事件历史仍可查询；同一个关闭工作项在没有新输入时不增加 session 或 turn。根仍 OPEN 时也必须成立，不能只验证全对象终态快照零调用退出。

## 2. P1：冷恢复要求新进程持有旧句柄，持久状态无法兑现恢复承诺

**状态：当前控制流确定；本轮没有以当前二进制执行未完成快照。**

当前公开入口是 `braid local <原 request.json>`。`local.rs:305` 起核对 run_id、repository 绝对路径、seed HEAD、prompt、delivery_ref、profiles、bindings；不匹配就拒绝恢复。PiFactory 能在 `native_home.root` 下按原 session 文件名寻找 JSONL，但这个回退不消除前面的请求身份校验。`BRAID_COLD_STOPPED_SESSIONS` 在当前源码没有消费者。

`resume_issue_provider_sessions`（`group/issue_agent.rs:76`）与 PR 对应函数（`group/pr_agent.rs:105`）先把没有本进程句柄的 starting/running turn 标记 unknown 并 continue。`fence_session_and_request_reset`（`store/mod.rs:5330`）立即建立 materializing reset。同一个 worker 周期随后执行 `materialize_next_context_reset`（`group/dispatch.rs:277`），无条件 `SessionManager.remove(old_id)`。新进程的句柄表与 stopped 集合为空，`session_manager.rs:133` 明确报“cannot prove native teardown”。旧会话甚至还没进入下次 resume 周期。

已存在的 materializing reset 要区分旧 provider 状态：`reset_pending` 不在 resume 候选中，同样在空句柄 remove 处阻塞；`unknown` 可以先被重新启动再关闭，这只能证明新启动进程关闭，不能证明来源旧进程已停。已有 interrupting reset 则在 `recover_context_resets`（`store/mod.rs:4835`）直接 blocked。这些分支不能合并宣传为已支持安全冷恢复。

`runtime.lock` 只排除同一路径的另一个 Braid 主进程。Braid 崩溃后仍可能有旧 Pi 根进程；跨主机复制还会得到独立的文件锁。因此把“拿到锁”解释为“旧执行已死”不成立。也不能让 Braid 因此接管 Pi 原生子代理树。

**最小修正方向：** 区分已有持久 teardown 事实与没有停止证明的冷恢复。当前正常通知路径先关闭旧 provider，再把 reset/旧 session 持久化为 `materializing/reset_pending`，这类恢复可使用已建立的事实；unknown 创建 materializing 发生在实际 teardown 之前，不能作同样推断。没有证明时保留 blocked，并提供一个明确的宿主离线恢复入口：宿主保证来源运行环境已终止，旧执行不会再访问保留 state/clone；Braid 取得锁后撤销旧 CLI 身份，按该断言确认已知旧 provider ID 的 teardown，继续原有 reset/输入重放。记录一次宿主断言即可，不需要增加另一套 lifecycle，也不需要管理 Pi 内部代理。

此入口只解决停机证明；同路径身份与材料要求仍然成立。若要支持任意路径迁移，应另行定义路径重定位契约，不能由 Factory 随意改 profiles 或 SQLite 来绕过。

**可验证标准：** 已确认旧环境终止的真实未完成快照，分别覆盖旧 running、unknown、materializing、interrupting 状态；旧身份不可写，没有两个执行同时使用同一 clone，工作项和未提交文件保留，重放输入可追溯。未给停止证明时明确 blocked。全终态快照早退出不算验证了这些恢复路径。

## 3. P1：Pi 专属消息收据成了共享 reset 门槛，Codex 不能重建 Context

**状态：当前源码确定；没有当前 Codex 真实运行证据。**

`group/worker.rs:169` 的 `finish_running` 对所有 adapter 调用 `message_was_processed`。`provider/session.rs:302` 将它转发给 `AgentProvider`。只有 `provider/pi.rs:414` 实现原生 JSONL 检查；`provider/mod.rs:106` 的默认行为返回 `native message receipt is unavailable for this adapter`，`CodexProvider` 没有覆盖该方法。

因此 Codex 的普通 turn 终结后先进入补发通知路径；`context_reset_notice` turn 再正常终结，仍无法取得收据，随后 reset blocked。触发条件只是工作项 Context 需要重建，不是异常断线。

“旧模型有机会处理通知”是有效要求。缺陷在于把 Pi 的证据取得方式加入共享必选契约，却保留 Codex 能力声明而不实现对应证据。

**最小修正方向：** 由 provider adapter 完整兑现同一个可观察契约，Codex 使用其原生消息/turn 事实返回收据。不要让 GroupDriver 解析 provider 私有记录，也不要把 RPC ACK 当成处理证明。若当前范围只允许支持 Pi，则应在启动前明确拒绝不具备能力的 adapter，并修改公开能力声明；运行到第一次编辑才永久阻塞不可接受。

**可验证标准：** 分别用真实 Pi 和 Codex 执行一次工作项自编辑及一次外部编辑；旧会话出现通知及后续 assistant 活动，正常终结后才启动包含最新完整 Context 的替代会话。必须验证真实 provider 的消息收据；模拟返回 true 不能证明这一边界。

## 复杂度专项

以下是静态调用关系明确的删减候选，优先级低于上述三项，不据此发起仓促重构。

- `delete:` Local 无调用方的远端 mention 验权、数据库 owner lease 和 GitHub 写出队列消费 API。三个函数段分别为 `store/mod.rs:2610–2665`、`2861–2945`、`2946–3080`，合计 276 行，另有对应 Actor 包装。Local 已用文件锁，输入来自本地对象事务，未启动 GitHub outbox 消费器；来源数据库仍各积压 11/7 条 pending comment_create，说明错误报告正进入无人消费的旧通道。将仍需呈现的运行错误留在当前 status/result 或明确的本地对象通道；保留已发布 migration 历史，不倒改旧 schema。
- `delete:` Cargo.toml 的直接 `url` 依赖在 `src` 没有使用。删除直接声明即可；不承诺减少它作为其它库间接依赖的实际构建量。
- `shrink:` Issue/PR 的恢复函数各约 130 行，真正差异是 Context/指令和 PR 分支检查；冷恢复缺陷也在两份函数重复。修恢复时可合为现有 GroupDriver 的一个过程，以工作项类型选择必要材料，不新增策略类或插件层。

`net: -276 行函数体、-1 项直接依赖是已定位候选；实际改动还需保留本地错误可见性，未实施，未把预估当作已实现收益。`

## 尚未独立验证的边界

- 当前 `delivery_complete` 在观察到全部对象终态后立即通知 worker shutdown。`worker.rs:320` 把仍活跃的 turn 记为 unknown，再关闭 provider，而 `local.md` 同时承诺 close/merge 不打断当前收尾。来源完成快照零模型退出证明了交付出口，但没有证明运行中的最后一个 close 与收尾顺序。建议明确停止新调度与等待已经接受的 turn 收尾的关系，再用真实原生执行验证；不以增加轮数或时间阈值解决。
- `apply_merge` 只把目标 ref 精确等于 prepared merge commit 认作已发布；若 Git ref 更新后、SQLite 收据前中断，而目标随后又前进到该 merge 的后代，当前恢复会报告未发布。源码支持这个边界推断，但两份快照没有 unresolved prepared merge，未证实发生。可用实际 Git/进程中断验证后决定是否增加祖先关系判断。

审查不建议削弱对象/事件原子事务、clone 隔离、merge intent 或独立 provider 适配器；这些机制都有已存在的边界要保护。也不建议让 Braid 判断评论语义、接管 Pi 子代理，或把 benchmark 验收固化进运行时。
