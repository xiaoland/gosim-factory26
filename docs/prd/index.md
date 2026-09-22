# Factory26 产品说明

Factory26 用于开发和比较参加 GOSIM Agentic Factory / ARC-bench 的 Agent Harness。使用者是开发 Harness 的工程师；运行时 Agent 接收需求包并生成应用。开发仓库的 Coding Agent 与被评测的运行时 Agent 是不同角色。

项目要让每次实验能够回答：输入了什么需求、使用了什么模型与 Harness、产生了什么应用、评测如何结束，以及证据在哪里。具体运行方式由[运行文档](../deployment/index.md)维护，单次结果由[四组实验报告](../../reports/2026-09-20-harness-matrix.md)维护。

## 当前能力与范围

活动实验统一使用 Pi + Braid + SVC。四个 variant 分别比较 DeepSeek 同构团队、GLM 同构团队、两者混合团队，以及混合团队加 canonical SVC V&V。Variant 直接引用内部 profiles、默认 assignee 和方法装配；具体模型、技能、工具及原生角色由对应配置持有，Braid 不接收 variant 或 preset。Codex app-server 适配与历史 generalist 结果保留为基线和排障材料，不进入当前活动矩阵。

一个 Factory task invocation 建立一个根 Issue，description 保存任务 prompt 与冻结 requirement bundle 的读取入口。单条 requirement 不自动成为 Issue；Agent 根据目标与协作需要决定是否拆分子 Issue。同一内部 profile 可承载多个独立工作项，现有 Braid driver 可以让它们重叠运行。

运行时 Agent 使用 GitHub 式 Issue、PR、comment、reply、hide/resolve、reaction 和 assignee。成员目录说明协作者能力；Harness 将公开 assignee 映射到内部 profile，运行时无需理解 Braid、模型路由或会话调度。每个工作项同时最多一个活动 owner。重指派复用既有 writer fence、native teardown 和工作树恢复；取得旧 writer 的停止证明后才允许目标 Agent 开始。

Issue 对应需求理解、技术方案与最终验收设计，PR 对应实施计划、执行与最终验收。它们是 Agent 可组合使用的能力，不强制固定轮次或自动拆分。跨工作项通过 comment/reply 传递需要的事实、问题和交付证据；PR ready 后由消费者决定接受与合入。根 Issue 完成及生命周期收敛共同确定最终交付 commit。

原生 sub-agent 服务所属工作项内的局部委派。explorer/executor 使用快速文本模型，vision/browser-operator 使用视觉模型，specialist 为按需的昂贵能力；模型、reasoning、skills 与 tools 都显式装配。原生角色不出现在可指派成员目录。浏览器按 run 和 native session 隔离，任务分解与工具选择由 LLM 决定。

SVC 提供 Task Packet、探索与实施方法、有界委派和 V&V。user-scope AGENTS.md 是简短语义索引，说明何时读取、如何保存可恢复状态；正文保持在冻结的 SVC Corpus。基础团队按需读取，V&V variant 额外装配 canonical test design 与 verification 两条入口。Braid 不读取 SVC packet，也不拥有其文件组织。

参赛 ZIP 固定运行依赖、有效能力配置和源码哈希。文本与视觉凭据分别由平台注入，视觉配置不能覆盖主模型或冻结角色。生成产物遵循官方 frontend/backend 布局；冻结应用后才进入官方评测。Competition 与官方 local simulation 使用相同 ZIP bytes，报告明确区分 venue。具体运行和恢复方法见[运行文档](../deployment/index.md)；当前真实资格与实验结果见[迭代 packet](../../tasks/iteration-throughput/packet.md)，上述配置与本地检查不能替代正式成绩。

## 实验规则

每次实验无论成功或失败，都先汇报已观察结果、原因判断与限制，由用户确定下一轮方向。持续沿用的验收方案不等于自动补跑或连续迭代授权；用户要求停止时，应中断活动实验并保留证据。

独立生成基线只根据允许的需求与资源实现应用，不能读取外部验收测试、参考应用或先前失败报告。Agent 可以编写自己的检查并据此修改应用；外部评测必须在生成结束、应用冻结后执行。

如果后续实验主动使用公开评测反馈修复应用，必须创建新的 run 并标明 `oracle/dev-only`，不能与独立生成基线混淆。线上提交资格需要单独验证，不能由本地流程跑通推导。

固定并记录 benchmark 版本，不修改评测器来适配生成应用。完整评测中的失败用例是有效实验结果；安装、构建、启动或评测中断不能当作有效零分。上游需求或评测缺陷需要记录证据及影响。

每次实验保留输入和应用哈希、模型参数、原始 rollout、usage、退出状态及评测结果。缺失指标按未知处理，客户端费用估算不等于比赛账单。原始产物保存在被 Git 忽略的 `runs/`，可长期分享的脱敏结论保存在 `reports/`。

## 持续采用的验收基线

本轮采用已批准的[验收方案](../../tasks/iteration-throughput/verification.md)：先验证实际改动涉及的模型接口、Pi 生命周期、assignee 协作和官方包入口，随后冻结四 variants × Keep/BookStack。生成或评测设施中断不得计为低分；完整评分的低分是有效结果，完成矩阵后先报告，再由用户决定下一轮。

历史 Keep 单任务和 Playground 探针只支持其记录的主张，不等于完整 ARC-Bench-Lite、Web 或正式初赛成绩。多个并发 run 共享 Meter key 时，不能把账户费用差值伪装为逐项准确成本；保留不可归因标记。只有具备明确输入、版本、冻结应用与评分身份的结果才能横向比较。
