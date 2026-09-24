# Variant 独立实现

当前已由 [developer-experience](../developer-experience/packet.md) 承接实施与验收。
用户已批准三项优先修正并授权直接推进；本 packet 的调查和独立预演作为迁移依据，最新结果归 DX 的 implementation.md。

目标：每个活动 variant 自己拥有完整的 Harness 实现，能够改变指令、能力装配和执行方式，不必先扩展共同配置模型或修改其他 variant。
这不是把同一生成器的配置分散到四个目录。

本任务不关闭 [SVC Corpus 审查](../svc-corpus-review/packet.md)，也不替代 [SVC skill 接线](../svc-skill-integration/packet.md)的剩余验收。
迁移以当前已完成的 skill 接线为起点，不重新引入 SVC CLI、AGENTS 注入或正文预载。
已有模型读取验收的额度阻断继续由 skill 任务记录；新任务不把它误算成已经通过。
历史 ZIP、run、journal 与评分保持原身份。

四个活动 variant 已迁移为独立实现；模型配方与 Corpus 方法未调整。
原生输入与原基线核对一致，真实模型效果仍需另行验收。
设计材料：[设计](design.md)、[技术方案](technical.md)、[验收](verification.md)、[实施计划](plan.md)。
前序独立事实核实见 [证据接口](evidence-contract.md)，四组真实物化接口预演见 [预演结果](rehearsal.md)。
这些材料描述迁移时的决定与证据，不再作为当前源码入口导航；实际操作见 [CONTRIBUTING](../../CONTRIBUTING.md)。
