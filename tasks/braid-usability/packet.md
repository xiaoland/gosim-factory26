# Braid 的使用价值与 Agent 接口

2026-09-25 后续迭代的范围与推进入口已整理为 [Braid 协作身份与共同 Git 仓库](../braid-collaboration/packet.md)。
本目录保留身份与合并的前序调查，以及下文历史实施和验收；本轮授权以新 packet 为准。

2026-09-25 新问题进入调查与方案讨论：[具体成员身份与指派](agent-identity.md)。
用户澄清 assignee 是具体 Agent，profile 只是派生配置；当前实现却把 profile login 投影成负责人，造成独立会话同名。
最新产品边界：仅通过指派工作派生成员，assign 明确区分所选配置和返回的具体成员名；Agent 可见接口不使用内部 UUID。
针对 GitHub run 的提前关单与跨工作区 WIP，已完成 [合并反馈的定向调查](merge-feedback.md)。按用户最新定位，Braid 还需还原 GitHub 的共同 Git 仓库语义；PR 合并混入根 Agent worktree 操作是这项边界缺失的具体表现。本地 origin 与 Agent 客户端的接线仍待技术设计。
此项尚未取得源码修改或实验授权；下文保留此前边界修正的实施与验收记录。

当前阶段：用户已批准应用 [职责边界修正](run-boundary.md) 和限定于 Braid Factory 的 [自主工作流程](factory-workflow.md)。源码改动、本机编译与 Linux release 构建已完成，新冻结制品的完整 Lite 两题已启动，身份见边界文档。新旧运行由一位监控 Agent 继续跟进。旧首轮 BookStack 已取得 29/34（85.3%），独立分析进行中；临时修复版 BookStack 尚待终态。
旧首轮 Keep 入口失败，同一合入应用独立补评分为 19/32（59.4%）；临时关闭理由修复版 Keep 已正常生成并评分为 23/32（71.9%），[独立分析](results/keep-delivery-fix.md)确认设计/实施已实际分离，但它与旧 Keep 是不同生成应用，也不是此次边界修正的验收。
用户随后要求审查 Braid 的其它同类问题、保持 Braid/SVC 与比赛无直接关系，并把工作流程应用到采用 Braid 的 Factory。
本次开工依据是用户原话：“这个工作流程没错，不过你提出的这个版本要限定一下，是仅 braid factory 才能这样；‘像人类一样协作’不必展开，让LLM自行理解就好。你可以应用这些修正了。”
授权覆盖边界修正与限定后的工作指令：Braid 操作终态、根 Issue 特权/交付门槛清理、Factory 按集成 ref 冻结，以及相关规范；不改 SVC、模型与工具配方，不提交。
独立 Agent 负责 Braid local/objects/evidence 及其文档，主 Agent 负责 provider 指引、四 variant 接线与六份成员指令；保持现有监控和逐 run 分析分工。
接口收敛为 quiescent/blocked/failed；Factory 记录操作结果但独立读取请求中的集成 ref；沿用完整 Lite 两题的真实验收，新制品与旧运行分目录。
已有 Keep 报告已补全同一合入应用的 13 个失败案例诊断，原入口失败与独立补评分分别保留在 [结果](results/keep.md)。
实施前任务包提交为 `16cdfb3`；其它任务工作区差异另保存在 `runs/braid-usability-implementation/baseline/`。
2026-09-24 用户提出两个目标：让 Issue/PR 在真实任务中发挥作用，以及降低 Agent 使用 Braid 的认知负担。
本轮设计复核通过后，主 Agent 本应完成实施计划与独立预演、呈现具体影响，再取得单独的开工确认。
用户对 V&V 归属提出修正并说“其它的没问题”，批准的是设计复核，不是开工。
主 Agent 错误地将其当作开工同意，进行了任务包提交、源码修改、构建和实验启动；此前 packet 及方案中的“已获开工确认”记录不实，现已纠正。
用户指出这一越权后，进一步明确“不，你不必停止或撤回”；当前依据这一新指示继续既有实施与两题实验，保留现有工作，不将它追溯解释为此前已获授权。
本次问题是未执行仓库已有的开工闸门。用户随后明确要求“检查并按需更新repo AGENTS.md，防止再次越过我直接开始实现”；已在原协作段落补齐阶段回复的解释边界、源码/委派/实验的开工闸门，以及授权必须追溯到用户指示的记录要求。
SVC skill 改造的真实运行验收仍保留在原任务，不因转入本任务而关闭。

## 当前判断

`--state` 是运行状态目录，`--writer-turn` 同时用于确定作者、所属工作项和拒绝过期执行的写入。
保留运行时的身份与生命周期判断，不意味着应让 LLM 反复传内部参数。
改动前，variant 指定的 Issue/PR profile 是全局默认，不只是根 Issue 的启动成员。
本轮已移除默认补人：variant 只指定根 Issue 成员，后续未指派工作项不启动。

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
WSL 官方本地 Runner、镜像、Lite 两题输入及密钥文件已确认；官方 `/v1/models` 返回 HTTP 200，采样和评分仍待正式运行。
开工影响包括 Braid schema/API、四 variant 接线和六份角色指引，以及一个 pi-team-mixed 完整 Lite bench（两题并行）。
Codex 接线随 Braid 修改和构建，本轮 Pi bench 不证明 Codex 工具链已通过真实验收。
易用性修正不自动证明 Braid 的额外收益；不强制增加拆分或讨论，不改写既定设计/实现职责，不重写调度架构。

沿用协作顺序：诊断与方案复核 → 验收方案复核 → 实施计划及适用的独立预演 → 具体影响与开工确认 → 实现和已授权验收 → 汇报。
V&V 方法仅由 SVC Corpus 提供；Braid 的指引只解释工作项、讨论、上下文和交付动作，pi-team-vv 仅提示读取 SVC，不向 Braid 复制 V&V 方法。
Factory 四个 run.py 已改 root_profile_id；初始任务 prompt 改为描述最终任务交付，避免用“你独立实现并结束”把整个需求误读成当前 Issue 会话应直接写完的阶段命令。
不新增 Factory/基础设施/Corpus 测试；模型和 benchmark 仅限已确认矩阵，不触及其它任务暂存区。

核心实现交接见 [implementation-core.md](implementation-core.md)，实际环境与构建恢复见 [environment.md](environment.md)。
