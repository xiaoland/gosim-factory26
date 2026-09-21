# 能力与方法装配 × 接入就绪

Track：capabilities。Phase：ready。状态：active。01 独立预演及 V&V 方案复核完成，见 [capabilities.md](../rehearsal/capabilities.md)；主 Agent 持有装配/V&V，pi_lifecycle_impl 持有薄生命周期扩展。实施起点提交后进入 02，真实兼容性仍待验明。

本 Cell 让 Braid 的每个 Agent 实际获得所选 Codex/Pi 核心、原生子代理、技能、浏览器和 SVC 指引。四份 preset 是这一责任的装配产物，不能替代整体 multi-agent 能力交付。普通 profile、原生子角色和 Factory preset 分层，LLM 保留工作组织与决策。

## 出口与依据

实际核心消费的模型/reasoning、能力材料与声明一致，个人配置隔离，原生子代理可完成有界工作并返回；浏览器按物理会话隔离，executor 保有局部实现与反馈循环。四组共享固定 V&V，其余 SVC Corpus 不变；只有 pi-verification 提供可选 reviewer，无 contract-reviewer。技能或模型不兼容须显式报告，不能静默降级后保留原名称。

选择归 [技术方案](../technical.md)、[四份 preset](../presets.md)，材料依据归 [需求映射](../requirements-fit.md)、[技能调查](../skill-candidates.md)、[Pi](../research-pi.md)和[Codex](../research-codex.md)。V&V 的方法输入是[用户原文](../../verification-system.md)，不改原文，不借适配重写其余 Corpus。

## 局部计划

1. **01：返回装配路线及风险收敛。** 独立预演实际 Pi 扩展/角色和 Codex app-server 配置入口、隔离 HOME、session ID 与模型协议；明确哪些事实已有证据、哪些必须在联合场景验明。准备 V&V 的具体删改与消费样例、外部 skill 的必要适配，避免新增强制流程。
2. **02：返回可消费的能力环境。** 共同实施前门槛通过后，按 runtime 的绑定接通配置、材料、原生子角色和浏览器；先闭合一个 work-item 到 child 的加载、工作、返回路径，再展开四份组合。dependencies/models、profiles、roles、preset、batch 各有责任，不重建 God config。
3. **03：返回固定装配与兼容证据。** 在既定 Pi/Codex 联合场景中验明 K3/K2.7 Code/GLM Flash 必需参数、工具/图像与流式终态、技能实际消费和浏览器隔离；核验 V&V 判据辨别能力及非 V&V 文件不变，交付四份可复现组合和来源摘要。

模型、核心或工具能力不足会改变配置意义时，返回具体证据和建议，不自行换模型、取消能力或扩成浏览器交叉矩阵。模板或静态配置检查只证明配置边界，不能冒充真实消费。

本 Cell 的 01/02 consumes runtime 的 01 profile/binding 合同，02 的真实执行消费 runtime 的 02 入口；自身 02 的实际配置供 runtime 的 03 联合核验，不等待完整 runtime Cell。向 feedback 随各返回提供配置/身份合同、实际配置、材料版本与能力证据。主要写入面为 Factory 装配、variants/harness 和 SVC 的 V&V owner；scripts/factory.py 的共享接缝由主 Agent 统一集成，不与 feedback 同时编辑。
