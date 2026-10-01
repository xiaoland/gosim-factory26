# 协作体验实施预演

2026-09-27。这里只做静态接口与数据流预演，不把源码阅读当作行为验收；尚未取得实现开工确认。对照材料为 [技术与验收方案](cooperation-design.md)、[协作体验 cell](cells/cooperation-experience.md) 和当前 `sources/braid`。

## 已收敛的最小方向

关注键使用不可复用的具体 `member_login`，而不是尚未物化的 `assignment_id`。当前对象写入已经具备所需的先后关系：`create_item` 预留 `desired_member_login`，`replace_assignee_in` 在写入 Assign 事件前更新目标成员，`begin_agent_assignment` 再把该值写入 assignment。因此关注关系可以在没有 assignment 实体时成立，也不会因 provider session 重建换联系人。

改派仍保留旧 `member_login` 的关注记录，但所有可达性判断都必须以当前 `local_items.desired_member_login` 与事件收件地址复核；旧身份不可静默转投新身份。

## 需要在实施前锁定的接缝

### 1. 指派事件是否携带身份快照

证据：[`objects.rs:238-323`](../../../sources/braid/src/objects.rs) 中 `set_assignee`/`replace_assignee_in` 先分配成员并更新 `desired_member_login`，随后发出 Assign；[`store/mod.rs:3907-4036`](../../../sources/braid/src/store/mod.rs) 的 `begin_agent_assignment` 从当前 `desired_member_login` 物化 assignment，但普通 Assign 事件本身没有收件成员快照。`assignment_candidates` 也会以当前 desired 值或旧 assignment 值做 `COALESCE`（[`store/mod.rs:3361-3410`](../../../sources/braid/src/store/mod.rs)）。

会走岔的情况：改派与旧 Assign/普通输入交错时，旧事件可能被新 desired 成员消费；关注键虽然稳定，事件却没有证明“这次动作属于哪一具体成员”。

最小修正建议：关注事件和成员定向事件统一写 `recipient_login`，并把 `assignment_revision` 或 `desired_member_login` 快照作为消费前条件；在同一 Store 事务中核对当前 desired 值，不匹配则 supersede/记录不可达，不能仅按 profile 匹配。`begin_agent_assignment` 已对 direct contact 做 `recipient_login == desired_member_login` 检查（[`store/mod.rs:3957-3968`](../../../sources/braid/src/store/mod.rs)），应把同一身份不变量扩展到实现所新增的关注投递路径。

未解决决策：Assign/activate 是否也要携带身份快照，还是只对“关注产生的投递事件”携带。前者能消除旧指派竞态，后者改动较小但必须证明旧 Assign 不会触发错误物化。

### 2. 关闭成员的普通回复必须复用 direct contact

证据：新评论从 [`objects.rs:675-706`](../../../sources/braid/src/objects.rs) 进入 `discussion_changed`；当前相关工作项都发普通 Wake（[`objects.rs:749-784`](../../../sources/braid/src/objects.rs)），只有显式 @ 才在目标 CLOSED 时发 `mention + direct_contact` 并写 `recipient_login`（[`objects.rs:708-738`](../../../sources/braid/src/objects.rs)）。Store 的关闭恢复入口要求 sleeping assignment 且按事件 `recipient_login` 选中原成员（[`store/mod.rs:3560-3699`](../../../sources/braid/src/store/mod.rs)）。

会走岔的情况：普通回复把“源 Issue 的状态”当成收件人的状态，或沿普通 Wake 入队；这样 CLOSED 成员既不能恢复，或错误地改变源 Issue 状态。finalizing/stopping 与普通回复交错时也不能丢事件。

最小修正建议：在 `discussion_changed` 为每个收件目标单独读取目标 `work_items.state`；目标 CLOSED 时生成带 `detail='direct_contact'`、`recipient_login` 的事件，目标 OPEN 才走 Wake。复用现有 lifecycle candidate/reactivation 路径，等待 finalizing 收尾后再按同一具体成员恢复；不可恢复时写明确 delivery unreachable，不 reopen 对象、不新建负责人。

未解决决策：普通回复是否也要给已 `retired/blocked` 且没有 sleeping assignment 的旧成员留下“不可达”回执。建议保留回执并消费事件，避免 pending 事件永久阻塞根空闲判断。

### 3. 移除关联普通广播时保留 Context 投影失效

证据：`discussion_changed` 当前把 active association 加入相关收件集并发 Wake（[`objects.rs:763-782`](../../../sources/braid/src/objects.rs)）；`changed` 负责 Issue→PR 的跨表 Context 失效，外部 Issue description 变更会发 `Invalidate` + `cross_surface`（[`objects.rs:430-467`](../../../sources/braid/src/objects.rs)）。PR Context 会嵌入完整 `IssueSnapshot`，包含正文、评论与状态（[`objects.rs:1070-1107`](../../../sources/braid/src/objects.rs)）。关联本身的写入还会给 PR 发 Invalidate（[`objects.rs:1300-1348`](../../../sources/braid/src/objects.rs)）。

会走岔的情况：为取消“只因关联就广播”而删除所有 association 事件，PR 会继续持有旧 Issue 投影；反过来保留所有 Wake，又会把导航关系误当成普通参与关系。

最小修正建议：分开“收件人资格”和“Context 依赖”：去掉关联只带来的普通讨论 Wake，保留关联增删的 PR Context Invalidate，以及 `changed` 中已经存在的 `cross_surface` 失效/调度。每个变更点只产生一次 projection event；不要用关注表替代投影依赖。

未解决决策：Issue 评论/隐藏/解决是否会改变 PR 的嵌入式 `IssueSnapshot`，从而需要关联 PR Invalidate；当前 `discussion_changed` 对关联项只发 Wake，实施者需按最终 Context 契约明确“正文/评论/关系”各自的失效范围，不能用删除广播顺带决定。

### 4. 根五分钟计时不能从 `status`/`agent_instances.idle` 推断

证据：当前 [`local.rs:242-254`](../../../sources/braid/src/local.rs) 的 `status` 只统计全局 `active_turns`、部分 pending batch/event、reset 和 materializing；`quiescent` 这些计数全为零就返回 true。主循环在 [`local.rs:370-421`](../../../sources/braid/src/local.rs) 以此结束运行，即使 `issue:1` 仍 OPEN。Store 中可证明执行事实还包括 `turns` starting/running、`wake_batches` pending/runnable、`events` pending/resetting/materializing、`context_resets` interrupting/materializing、assignment/provider/session 的 materializing/finalizing/reset_pending/unknown 等状态。

会走岔的情况：root Agent 只是暂时没有 runnable turn 时被当成 quiescent；或 `agent_instances.lifecycle='idle'` 掩盖 provider turn、恢复、重置或 materialization 尚未完成。重启后若 idle 起点未持久化，五分钟会重复或漏发。

最小修正建议：在 Store/对象层提供一个 root-specific snapshot，事务内同时核对：root OPEN、当前 desired member 与 assignment revision 一致、assignment/agent/provider 可执行、无 starting/running turn、无 root 待处理输入、无 lifecycle/reset/materialization/recovery 工作。`idle_since` 与最近一次系统检查评论关联字段落在 `local_run`；到期时再次在同一写事务中核对、写系统普通评论并清除起点，保证并发到期只发一次。root OPEN 且条件成立时，local loop 等待下一检查点，不返回 quiescent；root CLOSED/运行停止仍沿既有收尾路径。

未解决决策：root 的“无待处理输入”是否统计全局队列，还是只统计 root 及其当前 assignment。方案写的是 root 资格，建议至少覆盖 root 的全部 event/wake/reset/recovery 事实；全局其它子项不应取消 root 空闲，但其跨表 Context 失效若会进入 root 队列必须纳入。

### 5. 系统评论作者需要一个稳定的对象表示

证据：`comment_reply` 以 `writer=None` 创建系统/外部评论时，`local_comments.writer_group` 为 NULL（[`objects.rs:678-704`](../../../sources/braid/src/objects.rs)）；`read_comments` 的 `display_member` 将 NULL 显示为 `external`（[`objects.rs:960-984`](../../../sources/braid/src/objects.rs)）。现有 `writer` 校验只接受有效原生 Agent turn（[`objects.rs:181-195`](../../../sources/braid/src/objects.rs)）。

会走岔的情况：根提醒正文虽然写入，但历史、Context、timeline 将作者显示为 external；若借用 root Agent turn，又会把系统动作错误归因给 root 成员并产生自回声排除。

最小修正建议：使用保留的系统作者标识（例如 `braid`，不进入可指派成员目录）贯穿 local comment、事件 actor/display、Context/timeline；系统评论仍走普通关注收件，但作者排除逻辑按系统作者处理，不借用 root assignment。该表示应在 migration 中有明确约束并与 `external` 保持区分。

## 预演边界

本预演没有启动运行、执行行为验收、修改源码或新增测试；没有展开 Pi 原生恢复和 Git 算法。以上位置只证明当前数据流和接口接缝，真正的自然回复、关闭后联系、关联 Context、五分钟时序及一次性去重仍须在用户确认开工后按已批准验收矩阵验证。
