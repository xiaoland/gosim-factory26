# SVC 接线设计草案

状态：Human 已批准。本文尚未修改 Factory 源码或运行时提示词；Canonical Corpus 仍由 `sources/svc/corpus/` 持有，本文件记录接线判断、入口候选文本和实验差异。

## 当前错位与缺口

- `sources/svc/corpus/index.md` 已说明 SVC 面向 Agent、按概念渐进读取，并列出 Task Packet、Working Methods、Sub-agents、Verification 等入口；但当前 `harness/AGENTS.md` 只有两行命令导航。运行时 Agent 看不到“什么时候用什么”，也看不到 Task Packet 与 V&V 是最常用的两条入口。
- `task-packet/index.md` 已定义任务包不拥有长期事实、验收或运行时工作图，也规定 `packet.md` 是短入口、材料按需增长；但入口没有解释它作为外置上下文的意义：短控制面保持当前路线和恢复点，设计、计划、证据等材料承载细节，不能把共享工作项消息或任务包变成第二份权威状态。
- `planning.md`、`growth.md` 已有 Track/Phase/Cell 和形状预检，但没有在入口告诉使用者从小包开始、仅在持久并行或真实共享屏障出现时长大；否则容易把 Cells 当固定流程或要求全量读取。
- `verification/index.md` 与 `methods/design/test.md` 已覆盖 claim、property、oracle、条件选择、验收/诊断证据、反例挑战和残余不确定性；缺口是接线没有给出触发句，也没有提醒 V&V 不等于 Reviewer、批准链或“全绿即证明”。`tasks/verification-system.md` 是本 Factory 的方法输入，不应取代打包 Corpus 的语义归属。
- `harness/instructions/main.md` 的“先形成需求理解、方案和验收依据，再准备……最终验收”容易被读成固定阶段顺序；Corpus 明确按缺失 return 选择方法，设计、实施和验证可交错。无人值守入口还应明说 Agent 从当前需求建立或恢复 packet，在已有授权内自主推进，不等待人类中途宣布状态。

## 可直接复核的入口草案

拟作为 `harness/AGENTS.md` 的用户范围导航；详细运行授权、隔离、交付和协作规则仍由 Factory/运行指令持有，以下文字只路由 SVC：

> SVC（Sustainable Vibe Coding）提供 Agent 与人协作完成软件工作的按需方法：保存可恢复任务状态的 Task Packet，处理探索、设计与实施的 Working Methods，安排有界委派，以及依据需求选择证据并判断剩余不确定性的 Verification。非简单任务开始或需要跨会话恢复时，先读 `svc lookup --path task-packet/`：以短 `packet.md` 维护目标、约束、当前路线和下一步，把设计、计划、证据等较大的外置上下文按需放入材料；从小包开始，只有持久并行或真实共享屏障才增加 Track、Phase、Cell。需求或实现发生变化、准备声称完成、或失败需要解释时，读 `svc lookup --path verification/`，区分验收证据与诊断证据，说明证据支持什么及仍未知什么。探索、设计、实施或有界委派只在对应问题出现时读取 `methods/`、`sub-agents/` 的子条目，不必全量预读。无人中途介入时，在当前需求和授权边界内建立或恢复 packet、作常规决定并推进；缺少不可推断的权威信息时保留清晰阻塞与证据，不自行扩大需求或授权。

这段入口让 Factory 只负责“把可查询的 Corpus 和最短导航送到运行时”；SVC Corpus 负责上述术语、触发条件和证据语义。Factory 仍拥有本次需求、运行权限、隔离、提交/冻结、无人值守和比赛规则；它不在提示词中复制一套 V&V 或任务包方法。共享工作项与消息用于协作、讨论和回报，文件系统中的 Task Packet 用于较大材料、计划、设计、证据和恢复入口；两者互相引用但不互相冒充权威。入口不需要暴露内部调度产品名或agent-profile；Agent只看到GitHub式assignee，Harness负责把它映射到可复用能力配置，任务责任由当前work-item与需求决定。

## Corpus内容边界

当前SVC main `393b935`已经以需求性质和独立证据重写[Test Design](../../sources/svc/corpus/methods/design/test.md)与[Verification](../../sources/svc/corpus/verification/index.md)，覆盖产品意图→性质/约束→观察→Oracle、Oracle与条件选择的区别、验收/诊断证据、语义保真的最低成本边界、fast/broad feedback、独立挑战及residual。它与`tasks/verification-system.md`的核心方法一致，本轮没有证据支持再重写正文。实施只修接线并冻结这两个canonical路径的内容hash；接口spike若发现具体缺口，才在V&V owner中做有界修正。其它Corpus不改。

## pi-team 与 team+V&V 的可解释差异

建议两组使用相同需求、模型、工具、技能、并发和 Task Packet 形状；基础team仍可按需求做自检，不能人为禁用正常质量行为。基础组只获得共同semantic index，按压力查询Corpus。`pi-team-vv`的variant额外引用`methods/design/test.md`和`verification/index.md`；Factory resolver从冻结SVC源读取并把原文装入每个Braid Agent的user instructions，不复制为Factory维护的第二份正文，也不新建verification profile。增强组因此在设计验收与声称完成时明确需求claim、行为property、oracle、输入/状态条件、验收或诊断证据及残余；它不增加reviewer、批准链或新的验收权威。

为使对照可解释，冻结并记录两组实际消费的Corpus内容哈希、effective instructions、运行中`svc lookup`路径和Task Packet版本；同时记录“配置声明、实际加载、可观察行为”三层事实。增强组应以可复核产物体现增量，例如发现了实现改变仍应通过的性质、补充了能区分解释的条件、留下了验收/诊断证据及残余，而不是只报告“做过review”。两组除`svc_preload`路径与由此产生的effective digest外必须相同。

基础组自行按需查询Verification属于其正常能力，不视为“泄漏”；实验比较的是显式预加载/强调的效果，不是人为剥夺方法。最小黑盒资格场景只确认两组装配差异和canonical内容可消费，不用微型任务成绩预判完整benchmark效果。
