# Multi-agent 接入的工作图

本页维护跨 Cell 的责任、依赖和共同门槛；局部线性计划归各 Cell，技术选择归 [technical.md](technical.md)，跨交付的证据与残余归 [verification.md](verification.md)。原根 plan.md 已退役，不与局部计划竞争。Cell 是持续主线在共同阶段中的责任，不是 Agent 名单，也不是生成应用时的运行时工作图。

## 持续主线与共同阶段

| Track | 持续责任与边界 |
| --- | --- |
| runtime：协作运行时 | Braid 按 work-item 管理上下文、按 comment 协作，普通 profiles 的直接指派、重指派和恢复正确；原生 session tree 的生命周期不破坏 writer 边界。源码主要归 sources/braid。 |
| capabilities：能力与方法装配 | Factory 将模型、技能、原生子代理、浏览器与共同 V&V 装成真正可消费的环境；维护四份 preset。Braid 不感知 preset，SVC 非 V&V Corpus 冻结。 |
| feedback：诊断与实验反馈 | 从 work-item/profile 定位实际原生会话、失败与证据；管理固定批次、终态回传、恢复和结果解释，复用 SVC analysis 与 ARC-bench。 |

`ready` 阶段包含三条主线，其共同出口是：同一候选版本能正确运行协作、加载能力，并用可信证据诊断和执行实验。任何一项缺失都不启动八项批次；“配方已写完”不满足出口。

ready 之后的固定批次由 feedback 主线的一条[局部 Plan](experiment-plan.md)承接。此处只有一个执行 owner，没有新的共享屏障，因此不建 experiment Phase 或单格 Cell。发现使 ready 证据失效的设施问题时，暂停扩散并回到相应 owner，不在批次内悄悄更换版本或自动重跑。

## Cell 与当前前沿

| Cell / 局部计划 owner | 状态 | 当前前沿与必须返回的结果 |
| --- | --- | --- |
| [runtime-ready](cells/runtime-ready.md) | active | 将已认可方案收敛成独立预演可执行的运行链；返回指派、协作与原生子树收尾的实现/证据。 |
| [capabilities-ready](cells/capabilities-ready.md) | active | 明确材料消费者与模型/工具兼容性，准备 V&V 实际改动；返回可复现装配及消费证据。 |
| [feedback-ready](cells/feedback-ready.md) | active | 明确身份和终态接缝、查询与批次恢复检查；返回可诊断、可冻结、可运行的实验入口。 |

当前所有局部计划由主 Agent 维护，尚未分派源码实施 writer。独立 Agent 调查任务包拓扑不等于运行时独立预演已经完成。任何执行委派只带该 Cell 的任务增量、必要上下文、权限/文件所有权、反馈和返回合同；子 Agent 的临时状态不取代 Cell 状态。

## 实施前门槛与集成顺序

沿用已约定流程：诊断与方案复核 → 验收方案复核 → 实施计划与独立 Agent 预演 → 实现前提交 → 实现与验收 → 结果汇报。主体方案及用户后续纠正已接受；已有验收原则不重复申请批准，实质语义或验收变化才返回用户复核。

当前下一返回是三个 ready Cell 的首个 Slice：明确源码消费者、接口与检查，分别收敛局部实施路线，再由主 Agent 集成独立预演发现。通过后按既有明确约定提交本任务起点，Factory/Braid/SVC 各自处理且不带入 competition-p0 等无关改动。该门槛未过，不把文档重组记作实施开始。

实施沿以下真实依赖推进，而不是让所有人并行修改同一接口：

1. runtime 的 01 返回普通 profile/运行绑定、指派与原生会话身份边界；capabilities 和 feedback 的 01 可以并行准备材料及检查样例，再对这份接口进行集成预演。三个 01 返回和实施前提交完成后才开始 02，并不等待三个完整 Cell 已满足 ready。
2. runtime 的 02 提供可调用的执行入口；capabilities 的 02 将材料装入其中，返回实际配置供 runtime 的 03 核验真实生命周期。feedback 的 02 同步接入身份、归档与短诊断。先完成一个 work-item 到原生子代理的可观察闭环，再展开四份 preset。
3. 三个 Cell 复用受控场景完成各自证据并回填 verification；feedback 随后冻结八项清单并承接固定批次。诊断是接入交付的一部分，不等 bench 出问题再补。

sources/braid 的 config/local/store/group/provider 由 runtime 协调单一 writer；scripts/factory.py 的装配与证据接缝由主 Agent 集成，capabilities/feedback 未明确分割所有权前不同时写该文件。SVC V&V 正文归 capabilities，其余 Corpus 不改。

## 影响控制的关系

- capabilities 的 01/02 consumes runtime 的 01 返回的 profile/binding 合同；其 02 的真实执行部分再消费 runtime 的 02 入口，不等待整个 runtime Cell 验收完成。
- runtime 的 03 consumes capabilities 的 02 返回的实际配置；feedback 的 01/02 consumes 两者的 01 身份/材料合同，02/03 随联合执行消费实际身份、版本与生命周期证据。双向集成发生在有序返回之间，不形成完整 Cell 互等。
- 三个 ready Cell integrates into 同一版本的 [跨交付核验](verification.md)；预演及受控调用共用证据，不按每个 Cell 重复购买模型调用。
- 固定批次 Plan waits for 三个 ready Cell 满足出口及任务清单冻结；任何缺项不能被另一项“总体通过”抵消。
- provider/角色配置或生命周期改动 invalidates 相应兼容、隔离和证据结论；只重验受影响范围。实验输入变化必须有新的实验身份，不追加未经授权的补跑。
- [上一轮 Braid 包](../multi-agent/packet.md)返回已交付基础和未完成真实验证；[非 V&V 清理](../svc-corpus-review/packet.md)后置，不阻塞本轮；competition-p0 保持独立。
