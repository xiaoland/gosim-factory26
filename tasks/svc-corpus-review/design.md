# SVC Corpus 候选改稿与验收

这是 2026-09-23 对 `~/Development/svc` 当前 `80996c1` 的设计提案，不是已经生效的 Corpus 文本。目标是在不增加读者查阅负担的前提下，让抽象方法能指导实际判断。独立只读审计指出两处正文问题；Factory 的应用缺陷只能说明这些方法值得验证，不能证明 Corpus 导致了它们。

## 1. Design：把“考虑什么”接到“如何收敛方案”

当前 `~/Development/svc/corpus/methods/design/index.md` 先定义 forces、commitments 和三种 projection，随后列要关联的因素；同目录的 `technical.md` 又列技术关注点。两处都没有把代表性旅程、既有实现和边界反例串成一条可复核的判断路径。建议替换总入口中重复的职责枚举，保留 Product/Technical/Test 三个投影及其独立性；候选核心段落是：

> Start with a representative journey or state transition where a decision matters. Trace the current claim through its entry point, owner of data and state, dependencies, and failure or recovery path. Propose one arrangement and challenge it with a plausible counterexample or change. If the arrangement fails, revisit the product claim or technical boundary; carry cross-owner consequences into Test Design. Stop when the consumer can implement the current horizon without silently deciding a material requirement.

这是一种可选择的工作路径，不要求每个简单任务画调用链或生成设计文档。BookStack 的创建/编辑路由和登录前置是用来检验路径是否有辨别力的实例，不写入通用 Corpus 作为固定检查项。

## 2. Implementation：在线性计划之前关闭高代价未知

当前 `~/Development/svc/corpus/methods/implementation/index.md` 提醒部分线性计划、最小改动与快速反馈，但缺说明什么时候先预演。建议替换紧邻 “Plan a linear partial route” 的抽象重复，候选核心段落是：

> Before committing to a route, identify unknowns that could change it: external protocol, permission, runtime, migration, or another hard boundary. Test the consequential unknown with the smallest real probe and record what would stop or redirect the change. Plan only the path supported by that evidence, then implement in bounded slices with local feedback. For a simple local change with no route-changing unknown, act directly.

真实浏览器、Pi/Braid 接缝和外部平台协议曾在 Factory 的正式执行时才暴露条件错误；这里提炼的是预演选择标准，不把某个工具或平台写成普遍义务。

## 3. V&V 的关联建议，不在本包实施

`~/Development/svc/corpus/methods/design/test.md` 已要求判别性 oracle。可由 V&V owner 评估是否加一条双向校准：故意违背明确合同的实现应被拒绝，符合合同但结构不同的实现应被接受。mixed/Keep 的 `button` 被改为 `menuitem` 后自验仍 76/76；另一些测试却把 `title` 当后代节点查询而与题目合同可能冲突。这说明误通过与误拒绝都需区分，但不能由单例推定 SVC 文本是根因。实施前先核对冻结 runtime 所用的 Corpus 版本，避免重复覆盖已有 V&V 改写。

## 验收与实施顺序

用同一个通用内容应用任务对原文与候选文进行盲读比较。两名独立读者应能指出创建/编辑路由、认证前置、状态归属，以及仍须澄清的需求；候选文不能诱发额外加载无关 Corpus。再给一个依赖真实鉴权与外部 API 的实施任务，观察 Agent 是否在改源码前提出最小真实探针、停止条件和首个可执行 slice；简单本地改动仍应直接执行。V&V 另用明确 button 合同与等价 DOM 结构检验双向 oracle。

若复核通过，先确认 SVC 目标 checkout、做候选段落的独立消费预演和最小文本 diff；向用户呈现精确影响并取得开工确认，然后做实现前提交、改 Corpus、跑 SVC 自身的文档/链接检查及上述消费场景。官网当前冻结 ZIP 和本轮评分不受改稿影响。Task Packet 与 Sub-agent Corpus 保持现状，除非消费测试给出相反证据。
