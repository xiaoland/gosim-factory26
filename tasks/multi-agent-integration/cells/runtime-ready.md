# 协作运行时 × 接入就绪

Track：runtime。Phase：ready。状态：active。01 独立预演完成，见 [runtime.md](../rehearsal/runtime.md)；实现由 braid_profiles_impl 持有 Braid 源码，主 Agent 集成。实施起点提交后进入 02。

本 Cell 使 Braid Agent 能按问题使用多个 work-item 和异步讨论，并在明确 profile 下启动、重建、重新指派和恢复。profiles 是能力选择，不是 multi-agent 协作本身；不增加 preset 概念、强制拆 Issue、角色链或父 Agent 让位规则。

## 出口与依据

必须交付普通 profile registry/CLI 指派到实际 provider 的完整消费链，且错误 ID、并发 claim、重指派与恢复不串配置。旧 writer 及其原生子树停止后才能启动新写者，保留 work-item、讨论、工作树和未提交内容。返回实际身份、版本和相应行为证据，不以字段存在或原先单 profile 的探针代替新能力。

设计归 [直接指派与恢复](../technical.md#braid-的直接指派与恢复)及 [原生装配](../technical.md#原生装配与子代理)，判据归 [verification.md](../verification.md)。已有 comment/thread、自编辑与同类并发基础见 [上一轮执行记录](../../multi-agent/execution.md)；其中真实 Codex 和多个同类 Agent 协作的证据仍不充分，不能在迁移任务包时被标成完成。

## 局部计划

1. **01：返回可实施的运行链与预演结论。** 沿 config/local/objects/store/group/provider 的真实消费者核对 profile、assignment generation、binding 与 native session 身份；用独立 Agent 预演重指派、reset、失联和 native children 收尾。明确修改 owner、原有检查入口和实际未知，不重复抄写设计。
2. **02：返回可运行的指派与生命周期。** 在实施前共同门槛通过后，接 registry/CLI/claim/默认值和 provider 唯一参数源，解除现有 PiConfig/模型双重权威；再沿已有 fencing/reset 恢复边界处理子树。扩展现有真实行为检查，保持一条可运行的集成路径。
3. **03：返回与装配、诊断的联合证据。** 消费 capabilities 的 02 返回的真实配置，不等待其完整 Cell 满足 ready；向 feedback 返回 Braid work-item/profile 与原生父子关系、重建/终态证据。与已计划的 Pi/Codex 场景合并核验，真实协作残余按证据回填，不自行扩大模型探针范围。

01 后若原生接口不能满足既定语义，计划停在该未知处并返回方案影响；普通实现分支本地修复。当前调查不算正式预演，也不授予跳过实现前提交的权限。

返回给 capabilities：普通 profiles/运行绑定合同与隔离会话入口。返回给 feedback：可关联的实际身份和生命周期证据。源码所有权主要为 sources/braid；共享 store 由一个 writer 整合，Factory 消费接缝由主 Agent 协调。
