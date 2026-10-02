# Braid 协作行为：当前实现基准

2026-09-27。调查与设计材料，尚未授权实现或重新运行。
目标是让熟悉 GitHub 的 Agent 可以可靠地协作；四题运行只提供缺口证据，不构成完整产品需求。
GitHub 行为基准由协调会话的独立调查提供，本文不推定 GitHub 的父项时间线必然产生通知。

## 身份与证据边界

当前 Factory 入口为 `pi-braid`，e20260926-01 实际运行的是旧名 `pi-team-mixed` 冻结包，SHA256 为 `89452d2d9d602ef49fe3170498b5efdf4d07d724fdd09ac68e13619e4390d92f`。
Braid 源码 HEAD 为 `89212933c976b889f27de1b8cfe863baf8f6042e`，包含未提交修改，不能单凭 HEAD 认定运行版本一致。
本次逐字比较当前源码与此前从冻结材料恢复的 `runs/acceptance-integrity/20260926/lite/recovery-braid`，`objects.rs`、`store/mod.rs`、`cli/mod.rs`、`context.rs` 和 `local.md` 相同；`group/dispatch.rs` 不同，该恢复树有本地恢复补丁。
本表以当前源码为实现依据；运行事实另见 [四题诊断](results/official-four-diagnosis.md)。没有新运行测试，也不把已有源码中的测试当作当前验收通过证据。

## 一致的分析链

协作动作 → 持久对象及历史变化 → 默认收件人 → 通知入队与合并 → 空闲/运行中会话投递 → 可读上下文 → Agent 自己决定行动。
状态可查、事件存在、通知排队、输入已发送、Agent 已理解或采取行动是不同事实。

| 协作动作 | 持久变化与现有收件范围 | 可见性及待对照问题 |
| --- | --- | --- |
| 创建 Issue | 保存对象，可保存 parent；指定 assignee 时发 Assign，并向新工作项发 Wake | 创建者未通过独立订阅关系持久登记；父关系本身不通知父项。不能把“创建过”当作“已订阅”。 |
| 指派、取消或改派 | 保存具体成员、assignment revision；撤销旧执行写权限，排队 Assign/Unassign；新成员由所选配置派生 | 指派与执行容量已分离；历史发言人通过旧 assignment 映射工作项，改派后究竟通知谁需要明确规则，不能直接沿用 SQL 当产品定义。 |
| 新评论及回复 | 保存 comment/thread/作者；通知当前项、直接关联 Issue/PR、同 thread 发言者对应工作项 | 新 thread 不继承同工作项其他 thread 的参与者，这是已确认的缺口。 |
| 明确 @成员 | 解析具体成员名，保存逐地址回执，目标 OPEN 用 Wake，关闭目标用 direct_contact Mention | 已改派成员报告不可达；不将旧名字静默改投新人。显式联系关闭工作项不重开对象。 |
| 子 Issue 挂接、移除 | 更新 parent_issue；edit 对子项及其关联 PR 发变更，创建时只发新项事件 | 不给旧/新父项记录专门关系事件或通知；父项 view 能查询当前关系，但不是历史时间线。 |
| Issue 关闭/重开 | 保存状态和原因，对本项发 Lifecycle，对直接关联 PR 发 Wake；重开按需恢复 assignee | 不向 parent 路由。local.md 明确“不自动唤醒父项”，新增父项状态事件及通知是契约变更。 |
| PR 关联/解除 Issue | associations 保存活动关系；PR 收 Invalidate（关联新增还 Wake），Issue 收 Wake | 有持久事件及关联查询；不能据此断言 Agent 有可浏览的统一 timeline。 |
| PR ready、合并、关闭 | ready 改草稿状态；merge 在 origin 更新所选 base 并保存合并状态，通知关联 Issue；close/reopen 发本项及关联项事件 | merge 不自动关闭 Issue、不判定产品完成。需与 GitHub 的普通关联和 closing reference 分别对照。 |
| 评审、请求修改 | CLI 未发现独立 review/request-changes 操作；当前可用评论表达意见 | 是能力差异，不先假定必须新增审批状态机；等待真实协作需求与 GitHub 基准决定。 |
| 编辑/隐藏/解决讨论 | 修改持久讨论与上下文投影；源项可能需要上下文重建，跨项收到引用 | 保留 Braid 可编辑上下文产品能力；这些操作的收件规则也要与新增评论一起复核，不能遗漏。 |

上述入口主要在 `sources/braid/src/objects.rs`：create_issue、edit_with_parent_and_assignees、set_parent_in、discussion_changed、direct_mentions、link_in、lifecycle、apply_merge。

## 入队、投递与可读性

对象写入和事件产生共用 SQLite 事务，events 是持久记录，wake_batches 是可执行输入的批次。
`schedule_event` 合并目标工作项的 pending/runnable batch，并以 event_id 去重；批次已 runnable 时不被新输入推迟。
`claim_runnable_turn` 只领取 idle 的 Agent/provider session，并在事务中消费 batch、将 session 标为 running。
因此普通 Wake 可以等待正在运行的执行结束，不需要引入新的中断或并发会话；故障恢复仍须沿现有 unknown/reset 路径核对，不能据此承诺端到端恰好一次处理。
`mark_turn_started` 在 provider 已启动对应输入时把定向评论标为 delivered；它不证明模型已读懂、更不证明已经执行交接。
当前 `comment view` 可查明确 @ 的投递回执，普通讨论广播没有等价的逐收件人回执。
跨工作项输入主要是源对象/评论引用，接收者用 `comment view --thread` 等读取内容，不复制正文作为新的权威。

去重还有一个具体边界：discussion_changed 与 direct_mentions 分别发事件，emit 每次生成新的 object_version；同一接收者同时满足参与关系及 @ 时，batch 的 event_id 去重不能消除两个不同事件。
后续设计应先合并一次动作的收件人及原因，再进入既有事件路径，不能宣称现有 batch 已完成语义去重。
发件人自己写普通评论会转 OriginEcho，避免自我唤醒；该规则应在新增订阅路由中保留。

现有 events 包含运行/调度事件，并非天然等同用户协作时间线；CLI 当前没有已核实的统一 timeline 接口。
父项变更必须既可在父项历史中重新读取，又进入可靠通知路径。下一步应检查能否从现有持久事件投影所需协作历史，避免另造 inbox 或把内部调度细节暴露给 Agent。

## 运行证据如何映射

Keep 与 BookStack：根曾参与子项其他 thread，最终交接开新 thread，根没有新 Wake；显式 @ 根的历史评论则确实到达。
Sheet：只派第一批，子项独立新 thread 的交接未通知根；其关闭也未产生父项通知，后续任务未派发。
三个案例分别证明参与范围与父子状态通知缺口，不证明应对所有祖先广播普通评论。
GitHub 的 SIGKILL 原因调查已按用户指示停止，不混入通知改动。它没有进入官方 evaluation，main 是种子，develop 只有部分合并成果；不能视为完整应用原样复评的合适输入。

## 已接受原则与待决定范围

用户已接受同一工作项参与者跨 thread 接收通知；同时要求尽可能还原 GitHub 协作体验。
用户希望子项状态变化在父项历史可见且通知相关协作者；GitHub 对 close/reopen 的精确时间线和订阅规则由独立调查确认。
尚需决定创建者、当前/历史负责人、发言者、显式订阅者之间的默认关系，以及取消指派、关闭工作项和隐藏/删除评论后的通知规则。
职责边界保持：Braid 负责协作对象、持久事实与可达消息；谁做下一步、是否拆分或验收由 Agent 决定；Factory 的交付判定属于调用方。
下一步以独立 GitHub 基准逐项对照，标注已确认缺口、正常适配差异及未知，再确定最小完整实施范围和可观察验收。不实施、不重跑。
