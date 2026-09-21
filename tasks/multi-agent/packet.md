# 单一 Harness 的多 Agent 协作

目标：把后续开发收敛为一个 Braid + SVC harness，Codex app-server / Pi 是可选 backend；围绕上下文管理、多 Agent 协作、设计与实现分离，提供 Agent 可按问题自主组合的能力。

用户已确定上述方向，并接受根 Issue description 保存 Factory prompt、引用完整 requirements 包，子 Issue 按需要内联局部需求。Braid 与 SVC 继续独立：前者管理对象、关系、执行和上下文，后者提供协作方法，Factory harness 负责装配。CLI/config 收敛已完成。用户于 2026-09-21 同意第 1 项 Braid 能力的具体技术、验收及实施方案；完成独立预演及基线提交后实施。新增 agent-profile 是另一个项目，归第 3 项 Factory 装配，本轮不做。

当前实现：CLI/config 收敛已经完成；Braid 有多个逻辑 group 和独立 worktree，但每种角色仍只有一个活动执行，多个 PR 串行，也没有父子 Issue 关系。SVC user scope 保持两行查询导航，导航存在不能证明方法有效或多 Agent 协作已接通。

本页保留控制状态和授权；[产品方案](design.md)承接协作与上下文行为，[技术方案](technical.md)和[验收方案](verification.md)是本轮已批准的具体方案；[共同工作方法](working-methods.md)承接设计、实施和 V&V；[实施计划](plan.md)维护步骤与复核门槛；[历史实施核验](implementation.md)保留已完成 CLI/config 的证据。各文档拥有不同问题，不以一份长文代替 packet。

已完成实现和本地核验见实施记录；后续讨论尚未转为源码修改或 multi-agent 实验。历史 `pi-svc` 的 [9/32 实验](../../reports/2026-09-21-pi-svc-keep.md)不代表当前新协作方案的效果；[旧接入 packet](../braid-svc/packet.md)不因方向收敛而虚报完成。

当前讨论依据用户纠正收敛为：LLM 拥有任务语义与决策，harness 连接环境并提供能力。Braid 的协作机制围绕 comment 组织异步消息、围绕 work-item 组织 session context；multi-agent 专指 Braid 级别 Agent，sub-agent 专指 Codex/Pi 内部子会话。Turn 留作现有 provider 的执行协议事实，不作为产品上的协作单位。不强制拆 Issue，也不要求结束主会话执行后才允许协作；当前同类 worker 串行化属于待解决的实现限制。

最新输入明确：Issue 负责需求、技术方案和最终验收方案，PR 负责实施预演与计划、执行和最终验收；完整方法输入保留在用户的 [verification-system.md](../verification-system.md)。Issue/PR 普通 comment 需要回复、resolve/hide，hide 可附理由；reaction 是轻消息的候选能力。本地 Braid 只有扁平 comment 的 hide/unhide/delete，hide 理由硬编码，旧 thread/reaction 代码不等于这些能力已接通。

撤回“SVC 方法骨架已成立、只需补强”的过强结论：当前仅确认相关概念存在，未证明组织与写法能支持实际工作。接下来优先按具体消费问题审查删除、合并和重写，不预先保住目录或增补条款；证据与最小验证思路归 [共同工作方法](working-methods.md)。本轮抽查未形成全 Corpus 审计结论，也未执行候选文档的对照验证。

当前进入实施预演。独立只读调查发现并发会暴露 close 消费及 reset 中会话回收问题，自编辑还存在 terminal/continuation 顺序竞态，已进入技术与验收方案；正式预演继续核对真实接口、恢复及检查入口。用户方法原文保持不动。既有 bench 标准沿用，每次实验结束即汇报；其它任务的进展与授权归各自 packet，不重复启动其正在运行的实验。
