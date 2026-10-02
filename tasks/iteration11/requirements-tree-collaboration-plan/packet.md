# 需求树与 Braid Issue/PR 协作规划

## 当前问题与授权

2026-09-30。用户原话：“我还想到现在的这些题目的 Requirements 全部都是结构化的，是一个树的形状。那么其实它天然就已经帮我们拆分好了 Issue，只是我们当初没有完全按照它的这个拆分模式去拆分 Issue。如果结合我前面说的，教会 Agent 怎样去使用 Issue 还有 Pull Request 来管理上下文，再结合这个 Requirements 天然的拆分，你觉得怎么样？我希望你能够安排一个规划去深入地研究一下这个问题。”

委派范围明确：“任务是规划与研究，不改runtime/variant/Braid工作项、不运行评测或生成应用。”交付中文完整规划和简短决策摘要。该授权覆盖只读调查、本目录文档及少量有界独立研究；没有源码实现、模型实验、部署或提交授权。

## 当前结论与交付

状态：研究及方案完成，待用户复核方向。建议从完整原树分域，以内聚子树为默认 Issue 责任单元，对跨分支完整操作聚合实现/验收责任；原树身份始终保留。Skill 优先使用现有机制，runtime 强保证另列候选。

- [决策摘要](decision-summary.md)：建议、关键边界及下一步。
- [完整规划](plan.md)：问题证据、方案对比、唯一权威与追溯、具体映射、上下文协议、全流程、可证伪验证计划、实现/实验边界。
- [独立映射研究](mapping-review.md)：36 个 FOLDER 契约、107 个全节点主责任候选及六个具体实例。
- [独立能力复核](context-boundary-review.md)：Braid 历史/当前语义、真实可见性、通知/折叠/终态边界及 Skill/runtime 区别。

本轮静态读取两份 YAML 的结构及父层，主审回读关键叶子并消费已有完整 lineage；未重复全量原生调查。映射研究者对全节点表与原源做了文档覆盖核对，无遗漏/重复/未知 ID/行号偏差；这不证明每项要求的语义或新协议行为已通过验收。

两位独立研究者完成主规划复核。收敛：PR Milestone 权限作用域标为待确认解释；多个 PR 的局部 packet 不共写动态状态；需消费者处理的交接在最终关闭前完成，不能依赖关闭后再唤醒。没有运行测试或新模型实验作为复核。

## 已消费来源及证据边界

- [GitHub 原始树](../run-audit/github/requirements.yaml)：65 节点、18 FOLDER、47 ATOMIC。
- [Sheet 原始树](../run-audit/sheet/evidence/input/requirements.yaml)：42 节点、18 FOLDER、24 ATOMIC。
- [GitHub 需求断点](../github-requirement-breakpoints/report.md)、[框架核对](../github-requirement-breakpoints/framework.md)、[早期机制报告](../../pi-minimal/github-score-analysis/i11-mechanisms-forward.md)。
- [GitHub 完整 lineage](../braid-context-methodology/report.md)、[覆盖账](../braid-context-methodology/coverage.md)、middle-content-evidence/continuation-flow/final-pr23-flow/final-root-flow/runtime-semantics/research 各分项。
- [Sheet 实效](../sheet-effectiveness-analysis/report.md)、[完整 lineage](../sheet-effectiveness-analysis/full-lineage.md)。旧 [comparison](../sheet-effectiveness-analysis/comparison.md) 的切片主要解释已撤回，不沿用。

PR23 原始记录已补齐，旧“来源缺失”说法不再采用。完整 lineage 的结构索引不等于逐字段全读；本研究引用其语义结论和阅读边界，不扩写为本会话全文审阅。官方缺逐例反馈，4/59 分差不解释方法净效应。原需求明确跨业务 Issue/PR 的是 Milestone，历史“标签/里程碑”合称不扩成新要求。

## 下一步与剩余未知

本轮不继续实施。建议先用既有记录做桌面回放/静态语义核对，对比全树镜像与推荐方案，检查父约束、责任承接、语义证据、传播、维护停止及折叠；该只读调查属于既有自主范围，不额外设权限门。

若进入材料修改，按仓库约定先细化具体差分、独立预演和开工复核。任何新生成/官网重放须另定冻结输入、候选材料、预算、受限模型 Braid-session 保护和完成条件，只允许 self_funded。现有方案不授权运行。

未知：模型是否采纳、成本是否降低、是否提高分数、能否泛化，以及若干原需求内部歧义。无资料访问阻塞，不能把未知收益写成已验证结论。

## 改动边界

仅新增本目录文档；没有修改 runtime、variant、应用、Braid 工作项或其他报告，没有运行 Factory/Braid/应用测试、模型生成、评测、部署、提交或推送。仓库已有大量未提交变更，未覆盖或整理他人工作。
