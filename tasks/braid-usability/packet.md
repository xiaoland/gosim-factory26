# Braid 的使用价值与 Agent 接口

当前阶段：已获开工同意，实施中。
2026-09-24 用户提出两个目标：让 Issue/PR 在真实任务中发挥作用，以及降低 Agent 使用 Braid 的认知负担。
本轮设计、计划和独立预演均已完成；用户在具体开工询问后回复“其它的没问题”，并明确 V&V 方法属于 SVC Corpus。
按这一归属修正后开始已确认的实施与一个 pi-team-mixed 完整 Lite 实验；实施前先仅提交本任务包。
用户已确认“阶段交接工具”的产品诊断，以及去除使用负担、交还分工决定两条方向；随后明确回复“复核通过”，批准本任务的具体设计与验收方案。
设计批准后已单独呈现具体开工影响；当前授权来自后续开工回复，不把前次设计批准当作实现授权。
SVC skill 改造的真实运行验收仍保留在原任务，不因转入本任务而关闭。

## 当前判断

`--state` 是运行状态目录，`--writer-turn` 同时用于确定作者、所属工作项和拒绝过期执行的写入。
保留运行时的身份与生命周期判断，不意味着应让 LLM 反复传内部参数。
variant 当前指定的 Issue/PR profile 是全局默认，不只是根 Issue 的启动成员。
虽然 create/edit 已支持 assignee，省略 create 的 assignee 仍会替 Agent 作选择。

用户进一步澄清：问题不是没有调用 Issue/PR，而是实际使用退化成根 Issue → 单个实施 PR → 根 Issue 复验合并，或按阶段交付 design.md/implementation.md。
这种固定交接不足以体现 Braid 的上下文管理和协作价值；上一答将重点放在是否使用过流程，偏离了问题。
已按此前一 run 一分析者的约定，由三个独立分析者并行完成旧 pi-team/BookStack、本轮 pi-team-glm/BookStack 和 pi-team-vv/BookStack 的对象与讨论审查。
主 Agent 负责产品判断与跨 run 综合，不重复逐 run 分析，不将当前源码行为直接归因到历史冻结包。
具体证据、局限和方案见 [调查与产品方向](findings.md)。

三个 run 均只有一个 Issue、一个 PR 和三条顶层评论，主要用于派发、完成公告和收尾，未观察到评论推动的澄清或修订。
旧 team 是一次性约 10 KB 方案交接；V&V 是约 4 KB 方案交接；GLM 更是根 Issue 已实现后才创建 PR，PR Agent 主要复验。
GLM 在收尾实际执行过 resolve，因此不能笼统说上下文编辑功能没有调用；第一次 resolve 后下一次被 stale writer 拒绝，是易用性问题的具体运行证据。
旧 team 复验的提交早于最终合并提交，是协作记录没接住实际变化的具体例子，不单独扩展成本轮修复项目。
结论支持用户的产品诊断：当前主要收益来自交接和复验，尚未体现 Braid 作为持续工作上下文与协作载体的额外收益。

## 下一步与边界

已形成 [产品设计](design.md)、[技术方案](technical.md) 与 [验收方案](verification.md)。
本次新查明：`begin_agent_assignment` 还会把未指派对象交给抢到事件的 profile，只移除 variant 默认值不能实现显式指派。
三个独立 Agent 已完成身份绑定、指派/恢复路径、评论事务与指引归属的预演；主 Agent 已整合 [实施计划与开工影响](plan.md)。
预演结果见 [身份](rehearsal-identity.md)、[指派](rehearsal-assignment.md)、[上下文](rehearsal-context.md)，它们是实施前排障，不是运行验收。
身份采用现有 provider_sessions 的一个 binding 字段；清除默认分派也覆盖 sleeping/reopen；评论多 ID 一次事务，不重写调度。
WSL 官方本地 Runner、镜像、Lite 两题输入及密钥文件存在已只读确认；当前模型/API可用性未运行验证。
开工影响包括 Braid schema/API、四 variant 接线和六份角色指引，以及一个 pi-team-mixed 完整 Lite bench（两题并行）。
Codex 接线随 Braid 修改和构建，本轮 Pi bench 不证明 Codex 工具链已通过真实验收。
易用性修正不自动证明 Braid 的额外收益；不强制增加拆分或讨论，不改写既定设计/实现职责，不重写调度架构。

沿用协作顺序：诊断与方案复核 → 验收方案复核 → 实施计划及适用的独立预演 → 具体影响与开工确认 → 实现和已授权验收 → 汇报。
V&V 方法仅由 SVC Corpus 提供；Braid 的指引只解释工作项、讨论、上下文和交付动作，pi-team-vv 仅提示读取 SVC，不向 Braid 复制 V&V 方法。
不新增 Factory/基础设施/Corpus 测试；模型和 benchmark 仅限已确认矩阵，不触及其它任务暂存区。
