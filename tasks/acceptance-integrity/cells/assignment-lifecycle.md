# 指派、会话与执行资源

源码入口后继：本文件中的 `variants/pi-team-mixed` 现为 `variants/pi-braid`；历史冻结包与运行身份不变。

状态：2026-09-26，补充方案及独立预演已呈现；用户明确“确认，开工”，按本页范围进入实现与本地验收。
本 cell 接续原迭代，不替代 [Braid 通信与 Git cell](braid.md)。
证据是 [B Sheet 现场分析](../../competition-budget/results/08226c772b7a-stall.md)，旧现场不修改、不恢复。

## 产品结果与边界

指派保存谁负责这项工作，任务完成后保留负责人和可联系上下文。
原生执行可停止、会话可休眠，这不要求修改 Issue/PR 的责任关系。
取消指派表示撤销责任，改派表示换负责人；二者不能被当作资源回收接口。

根 description 删除成员/未完成项三名额规则和无依据的整批屏障。
按共享基础等真实依赖组织工作；独立部分何时并行由 LLM 判断。
本轮不新增资源调度器、计数器或“禁止取消指派”指令，不管理 Pi 内部子 Agent。
昂贵模型的 Braid session 总量约束保持，这是独立的预算决定。

## 当前失败路径

`objects.rs` 登记责任撤销并 fence 旧执行，worker 确认停止后将 assignment 标为 retired。
`assignment_candidates` 从 desired profile 或 stopping assignment 取得目标，已 retired 的 unassign 因而得到 None。
Issue/PR worker 都只取整个类型的首个事件，settlement 又要求匹配 profile；事件未被消费，后面的独立指派无法进入。
`retire_unassigned_work_item` 已有无成员、已重新指派、已退休等路径，`finish_unassigned_work_item` 也会检查存活 provider 再消费事件，但入口无法到达。

因此要恢复的是持久控制操作的闭合，而不是给消失的成员补一个模型配置或重新启动会话。
同一工作项的先后关系有意义，无关工作项共用一个不可越过的队首则没有必要。

## 实施约束

1. 将没有执行资源需要回收的 unassign 完成为幂等控制操作；只能依据事务内当前状态，不能把 target_profile=None 单独当作“可以丢弃事件”的证据。
2. 有存活会话时，继续由其实际拥有者确认停止。改派中的新成员不受旧事件收尾影响，不为消费旧事件停止新会话。
3. 候选选择按工作项保留先后次序，并使不相关的可执行候选能够到达对应 worker。复用现有事件与事务，不引入新的调度服务、全局锁或自制重试框架。
4. 指派回执表达已登记和具体成员名；现有查询展示实际执行状态，不增加要求 LLM 轮询或操作内部生命周期的步骤。

## 最小技术落点

| 修改位置 | 具体处理 |
| --- | --- |
| variants/pi-team-mixed/run.py 根 description | 删除三项名额及整批屏障句子，保留共享基础等真实依赖；不额外告诉 LLM 管理执行资源 |
| src/store/mod.rs::assignment_candidates 及其 StoreActor/Command 接口 | 候选先沿现有 direct_contact 分流规则形成同一来源集合，再按工作项取最老事件；按实际处理者过滤，允许没有目标的 unassign 进入收尾。返回每项一个候选，不再只返回全类型/全profile首项 |
| src/group/issue_agent.rs、pr_agent.rs | 一轮逐项处理候选；本项暂未settled或失败不提前返回整个列表。非空owner仍严格匹配，空owner只进入事务确认后的收尾，不物化会话 |
| src/store/mod.rs::retire_unassigned_work_item / finish_unassigned_work_item | 复用两段现有控制流程；把无存活会话的收尾闭合。每个有副作用的事务再次检查当前desired assignee及待收尾旧assignment；已改派只结算过期事件，不影响新成员和新消息 |
| Braid lifecycle 文档 | 说明完成保留责任、取消/改派停止旧执行、无关工作可继续推进；不引入业务阶段或模型分配策略 |

不把 target_profile=None 视为执行资源已全部释放的证明；最终消费仍需真实 provider 状态支持。
保留 SessionManager::remove 的停止确认、现有 stopping ownership 检查，以及 begin_agent_assignment 的成员/revision/stopping事务闸门。
不新增 migration、持久状态或恢复控制器。
当前 finish 的整工作项 wake_batches 清空也要受事务内当前指派校验约束：若两段之间已改派，旧收尾只消费自身过期事件，不能清掉新成员的待收消息。
按profile过滤后仍 LIMIT 1 不足以解决同profile工作项之间的阻塞，因此一次取得每项一个候选并逐项尝试；不额外发明游标或资源额度。

指派CLI已有成员名和执行查询，本轮只纠正确有“已启动”误导的回执或说明，不新增等待/轮询协议或改变assign为同步等待。
主 Agent 保留集成判断，不把阅读代码当作运行验证。

## 独立预演

委派 `unassign_rehearsal`，gpt-5.6-luna/high，fresh context。
权限仅为只读跟踪现有代码和失败材料；不修改源码、不运行测试/probe、不启动新实验。
预演已完成源码路径追踪，确认 worker 先完成 native teardown 并置 retired，随后 profile 查询丢失owner，收尾入口返回，形成失败链。
确认现有 retire/finish 两段和 begin_agent_assignment 的 stopping barrier 可复用；没有理由改 Pi adapter 或添加资源计数。
主 Agent 修订了两项建议：profile过滤不能仍只取全局第一项；LocalObjects 的当前指派以同一SQLite事务为权威，不恢复旧GitHub canonical读回作为额外权威。
证据边界：这是实施前路径推演，未执行真实取消/改派；冻包原始证据证明旧缺陷，源码分析不证明修复有效。

需要覆盖的分支：

- 已退休且没有存活 provider：消费旧 unassign，不创建新会话。
- 正在执行时取消：先 fence 与确认停止，之后完成事件；停止失败保留具体错误。
- 取消紧接同项改派：旧取消不能取消新负责人，旧明确地址不转投新成员。
- 一个工作项待收尾，另一个已指派：后者仍能推进；同项事件按必要顺序处理。
- 关闭/合并后仍保留指派：现任成员继续可联系，不把完成自动变成 unassign。

## 实施与本地验收顺序

原迭代中已运行的冻结应用检查不依赖 Braid，可独立分析结果。
本补充已完成具体计划、独立预演和开工复核；现修改 Factory 根提示和 Braid 生命周期。
构建新二进制，沿已有打包方式生成新的 ZIP 与源码记录，不覆写当前冻结包或旧 A/B。
然后使用新包完成已允许的本地 GitHub/Sheet 生成及冻结应用的独立公开需求检查。

真实运行应保留工作项、指派身份、原生会话、消息及 Git 证据，证明完成后的负责人仍可联系且后续工作能推进。
如果本地任务自然出现取消/改派，观察事件收尾与后续执行；没有发生的分支明确记为未观测，不能靠最终得分或源码阅读声称已验证。
不为强迫覆盖而给生成 Agent 加额外业务动作，不建立 Factory/Braid 模拟测试、probe 或 SVC 内容测试。
官网实验仍暂停；源码提交需用户明确指令。

## 实施记录

用户“确认，开工”后，assignment_fix（gpt-6-sol/high）完成 Braid 增量，主 Agent 删除 variant 的名额段落与整批屏障。
候选按工作项取最早可处理事件，分别交给相应profile；Issue/PR逐项尝试，单项等待不退出整轮。候选保留stopping/retired的旧owner，以便真实停止操作仍由对应worker执行；无owner进入幂等事务收尾。
retire/finish均复查当前指派，finish检查该工作项全部非终态provider；改派后仅消费旧事件，不清新成员wake batch。保留既有停止确认和物化事务闸门。
源码与lifecycle/local文档已完成，cargo check --locked通过；没有运行测试/probe、没有提交。Linux构建与新包位于runs/acceptance-integrity/20260926/assignment-fix，后续真实运行仍待验收。

首次本地运行在模型启动前暴露旧迁移接线错误：支持版本常量仍为9，而嵌入迁移已到11。已改为从MIGRATIONS末项推导，cargo check通过；schema-fix/记录修正后的新源码和包。该失败不是评分结果，取消指派运行行为仍未获得证据。
