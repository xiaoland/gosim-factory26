# Braid 上下文重建触发清单

2026-09-30，基于开工前 `sources/braid` 工作树定向核对。用户已认可本页判断并授权应用；下表保留问题基线，实际落地状态归 [实施记录](context-implementation.md)，不把基线误读成修正后的行为。I12保持暂停、冻结材料不变。
CLI C01—C04已单独授权实施，不能将接口回执修正视为下面的事件语义已经修正。

这里的“重建”指Braid用最新对象投影启动新的原生会话、替换旧会话历史；同一原生会话收到新消息不算重建。
还单列没有生成Invalidate事件、却仍会更换原生会话的路径，避免遗漏恢复时的上下文丢失。

## 对象操作

| 编号 | 当前触发条件及范围 | 本轮取舍 |
| --- | --- | --- |
| CR01 | Issue/PR description可见正文改变：本项重建。自己编辑也触发；HTML注释之外的正文变化参与比较。 | 已决定保留。相同正文或仅HTML注释变化不造重建。 |
| CR02 | Issue正文改变传播给其关联PR；当前本地路径没有按关联Issue是否开放收紧。 | 拟只保留PR实际展开的开放关联Issue description依赖；关闭Issue描述不在其展开上下文中。可单独筛选这条传播。 |
| CR03 | 只改title也被归入title/body失效；Issue title还传播到关联PR。 | 已决定删除重建，改增量更新。 |
| CR04 | 编辑可见且未折叠comment正文：本项及关联PR重建；包括操作者编辑自己的评论。隐藏/已折叠评论编辑走Wake，非同一路径。 | 已决定全部不重建；操作者不自回送，其它必要收件人获增量。 |
| CR05 | hide、unhide、delete、修改hide reason：状态/理由实际变化时，本项及关联PR重建。仅改隐藏理由也会进入。 | 已决定不重建。CLI、Console及以后投影立即反映对象状态，已进入当前原生历史的文本不被追溯删除。 |
| CR06 | resolve、unresolve：折叠截止发生变化时，本项及关联PR重建。 | 已决定不重建。根ID校验、批量对称及回执属于独立CLI任务；停止Invalidate属于核心任务。 |
| CR07 | PR link/unlink关联Issue：已有PR重建；PR创建接入关联也走共享入口，但首次会话组装不等于重建已有会话。 | 已决定关系变化不重建，按实际关系更新增量通知。父子Issue关系当前已是Wake，不需要新增重建。 |

主要入口：`objects.rs::edit_with_parent_and_assignees`、`changed`、`discussion_changed`、`comment_visibility`、`hide_comments`、`resolve_comments`、`link_in`。
既有无效事件一般要求存在活动/物化/收尾中的指派；无人或休眠时并非立即重建。休眠恢复另有下述CR08，不能因此声称这些更新不影响其原生连续性。
旧Ingress接口另有 `store::schedule_cross_surface_invalidations`，只在提供可见description、相关标记及符合条件时传播；本地CLI没有启用这条Ingress分支。它重复CR02的来源，不是另一种用户操作。

## 其它更换原生会话的路径

| 编号 | 当前实际行为 | 建议及未决边界 |
| --- | --- | --- |
| CR08 | 关闭/休眠后的成员因真实联系或重开而恢复时，以完整对象投影hash相同作为resume条件。title/comment/关系变过也可能start新会话。 | 已决定去除全投影hash门槛。复用按指派归属的未应用description失效事实，描述未变则resume旧原生会话。详细预演见context-update-policy。 |
| CR09 | 恢复检查发现profile revision或system instruction revision变化，创建替换会话；不只是用户显式选择新模型才会触发。 | 需单独筛选“什么变化真的要求换会话”。当前profile revision来自配置/运行binding摘要，覆盖面比模型选择宽；不建议把所有配置变化自动等同旧历史不能继续使用。原生是否支持同会话更新各类配置仍须定向核实。 |
| CR10 | 执行结果标为unknown后，`fence_session_and_request_reset`直接请求新会话。来源包括活动连接/事件流关闭、事件消费者漏消息、发送返回Unavailable、恢复发现活动执行丢失handle，以及仍有活动执行时的运行关闭/离线收尾。 | 重点待收窄。“不知道上一次执行结果”与“原生历史不可恢复”是不同事实。先确认旧执行停止、读取原生状态和历史再决定是否resume；具体恢复协议尚未设计，不能直接删除停止确认或盲重放输入。普通failed/Deferred不是一律走此路径。 |
| CR11 | 休眠Pi会话的确切原生session文件已经不存在，直接以当前对象start；其它resume错误有重试/阻断分支，并不全部start。 | 保留“已证实无法恢复历史”作为必要的新建条件，保留具体原因；超时/断线本身不作为历史消失的证据。 |
| CR12 | 真正的新指派/更换负责人，新成员建立新会话；取消指派停用旧执行。 | 这是新负责人生命周期，不是旧负责人因材料维护被reset。同一负责人重复assign无变化；不通过取消/重指派整理上下文。 |

主要入口：`group/dispatch.rs::reactivate_work_item_agent`、`group/worker.rs`的provider恢复与事件终态处理、`store::begin_provider_replacement`、`fence_session_and_request_reset`、`prepare_offline_resume`。
故障后接续已经登记的context reset属于原重建的恢复，不另列为新的业务触发原因。

## 本身不触发重建的输入

新评论/回复、@、reaction、subscribe/unsubscribe、父子关系变化、ready/draft、正常通知与5分钟根提醒，本身走增量或状态路径。
close/merge关闭和reopen属于生命周期；关闭后再唤醒是否重建取决于CR08—CR11，不应把普通关闭/合并列为无条件reset。
Git提交或SHA变化本身没有找到独立的Braid重建触发；20%投影分档在物化时选内容，超过硬上限可报错，不是周期性自动重建。
Pi自身的compaction属于原生Harness维护历史的机制，与Braid用Issue/PR投影替换会话是两层；本轮清单不修改Pi compaction。
Console当前Docker pause/unpause只冻结/继续原进程，不能与进程退出后的冷恢复混为一谈。

## 当前推荐的筛选边界

日常对象操作只保留CR01及经选择的CR02；CR03—CR07与CR08中的非description哈希变化移除重建。
CR09配置变化和CR10未知结果应分别形成窄设计，不因为它们叫“恢复”而自动免责，也不在CLI实施中顺手处理。
CR11真正丢失原生历史与CR12真正的新负责人保留必要的新建路径。
