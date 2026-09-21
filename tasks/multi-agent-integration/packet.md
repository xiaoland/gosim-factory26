# Multi-agent 接入与完整实验

本轮目标是让 Braid 级 Agent 协作、Codex/Pi 内部子代理、SVC 方法和开发反馈在同一 harness 中实际接通，再以四种组合完成 ARC-Bench-Lite 实验。agent-profile presets 是能力装配的一项交付，不是任务中心；配置数量和子代理数量不能证明 multi-agent 已成立。

当前已完成方案调查，技术主体及用户后续纠正已记录；尚未完成正式实施预演、实现前提交、本轮源码接入或八项 bench。下一步由三个接入 Cell 收敛局部实施计划及独立预演，再依约提交起点并实施。任务包拓扑调查不算实现预演。当前没有新的用户决策项。

## 本轮怎样组织

[task-map.md](task-map.md) 维护跨 Cell 依赖与共同门槛；每个 Cell 自持局部线性计划、出口和返回。当前状态如下，不另设一份包办全部步骤的根 Plan。

| 工作主线 × 接入就绪阶段 | 当前状态 | 必须交付 |
| --- | --- | --- |
| [协作运行时](cells/runtime-ready.md) | active，预演待执行 | 普通 profile 直接指派、异步协作、上下文/原生子树生命周期，以及真实证据边界。 |
| [能力与方法装配](cells/capabilities-ready.md) | active，装配待实施 | 真正消费的模型、原生子代理、浏览器、技能与共同 V&V；四份可复现 preset。 |
| [诊断与实验反馈](cells/feedback-ready.md) | active，接缝待接通 | 低噪诊断、身份与证据关联、可恢复批次和终态回传。 |

三个出口在同一候选版本共同成立，才能进入 [固定批次的局部计划](experiment-plan.md)。后者由 feedback 主线承接，目前 TBC；它不需要独立共享阶段，因此不伪造第四个 Cell。

## 保持不变的边界

- LLM 拥有任务语义和工作组织；Braid 围绕 comment 协作、围绕 work-item 管理上下文。multi-agent 是 Braid 层，sub-agent 是原生核心层，不强制拆 Issue、派满角色或父 Agent 让位。
- 一个 variant 对应一个 preset，仅 Factory 选择、展开、冻结整组 profiles；Braid 不感知 preset/variant。指派到普通 profile，配置按语义责任显式引用。
- 浏览器通常由原生 operator/executor 操作，executor 保有局部反馈；agent-browser 为首选，MCP 当前为空。仅 pi-verification 配置可选 reviewer，无 contract-reviewer。
- V&V 纳入本轮，四组固定同一版本；其余 SVC Corpus 冻结，后续清理由[独立任务](../svc-corpus-review/packet.md)维护。user-scope 保留薄导航。
- pi-generalist、pi-team、codex-generalist、pi-verification 各跑 Keep/BookStack，共八项。WSL 固定 runner，先两路生成、最多四路独立单-worker评测，不称线上排名或正式初赛成绩。
- 生成冻结后才外部评测，失败详情不回灌同次生成，终态失败不自动重跑。结果按项短报，批次汇总后停止；系统性错误暂停扩散。主会话不频繁 polling。

## 从哪里恢复理解

| 问题 | 当前权威入口 |
| --- | --- |
| 协作运行时、配置、材料如何接通？ | [技术方案](technical.md)；局部实施路线见各 Cell。 |
| 哪些已经证明，怎样验收？ | [跨交付核验与验收方案](verification.md)，包含上一轮残余。 |
| 四种组合是什么，为什么这样选？ | [presets](presets.md)、[题目能力映射](requirements-fit.md)、[技能与工具调查](skill-candidates.md)。 |
| 核心接口与模型兼容有哪些未知？ | [profile 消费链](profiles.md)、[Pi](research-pi.md)、[Codex](research-codex.md)。 |
| 实验身份与资源条件是什么？ | [experiment-design](experiment-design.md)，执行步骤归 experiment-plan。 |
| 工作方法和既有基础是什么？ | [协作模式提炼](../development-loop-review/analysis.md)、[共同方法输入](../multi-agent/working-methods.md)、[V&V 原文](../verification-system.md)、[上一轮 Braid 记录](../multi-agent/packet.md)。 |

已有 evidence 证明 Braid 对象能力和 Pi 自编辑路径的一部分，不证明本轮多 profile/原生子代理接入。当前重要未知是三个比赛模型的实际参数/工具/图像兼容、原生子树在 reset/取消时收尾，以及多 Braid Agent 的真实协作；静态 schema 和配置声明不能替代这些证据。已有调查产物保留在 `runs/agent-profile-presets/`，历史路径不改写。

推进次序沿用根 AGENTS.md：方案复核、验收复核、实施计划与独立预演、实现前提交、实现验收、结果汇报。按已有授权继续，不因 Cell 重组重复请求批准；改变实质产品语义或验收范围才返回用户。主 Agent 持有整体判断、共享源码集成与门槛，低成本子 Agent 承担有界调查/预演，不使用 Advisor。competition-p0 等独立任务不混入本次变更或提交。
