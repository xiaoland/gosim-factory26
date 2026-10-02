# Corpus 增强实施记录

2026-09-24，用户已复核设计并明确授权修改。
本轮完成实际供 Factory 使用的 `sources/svc/corpus` 及 `harness/skills/svc/SKILL.md` 导航改稿。
原有未提交改动保留，开发侧 `~/Development/svc` 未同步，已有冻结制品未修改。

## 具体改动

| 正文归属 | 实际改动 |
| --- | --- |
| methods/design/test.md | 从当前待决问题设计证据；区分满足要求与满足原始目标；保留双向 oracle、条件选择、真实依赖与总成本；容纳有理由的质性判断。 |
| verification/index.md | 分开观察、解释和结论；区分产品、检查、环境与证据缺口；明确独立机制及其适用范围；结果指向修复、回到设计、补观察或停止扩大检查。 |
| methods/index.md、explore/index.md | 以知识或产物是否改善判断重复工作；围绕可区分的解释取证；说明足够、外部等待与证据不可得；删除 Frame/keyness 等入口术语负担。 |
| methods/implementation/index.md | 把可能推翻路线的未知放到实现前核实；先用现有接口资料，再选择最小真实 spike；按证据规划并用局部反馈继续。 |
| methods/design/index.md、product.md、technical.md | 以代表性行为、实际系统和有理由的提案组织设计；开放问题主动推进并保留可修订假设；明确真实版本接口与早期核实的连接。 |
| methods/design/engineering-judgment.md | 复杂性增长先检查必要需求，再检查状态归属、生命周期和责任；用单一资源双重控制的例子说明边界改正如何消除时序补丁。 |
| sub-agents/ 三篇 | 比较完整委派成本；区分任务边界与认知难度；按任务证据选择执行者；角色页返回可直接使用的结论/产物，验证原则引用唯一正文。 |
| task-packet/information.md、verification 模板 | 让当前解释、被排除方向及下一项观察可恢复；删除 terminal Verification 和固定 qualification 枚举，保持验证可在工作途中改变路线。 |
| corpus/index.md、corpus/AGENTS.md、skill 入口 | 按当前问题路由；移除维护者的 Catalog/wheel 旧约定；继续要求按句换行和通用例子，不引入特定赛事或运行时。 |

本轮改动 16 篇 Corpus 文件（含维护者 AGENTS）及一个 skill 入口；可装载的 Markdown 文件仍为 27 篇，没有新增方法文档、角色或模板。
没有改变 task packet 的 Track/Phase/Cell 拓扑，也没有引入循环计数器、固定角色链、审批等待或模型排名。
个人 AGENTS 中的判断原则已分别进入对应方法，没有复制语言偏好、提交/权限规则或 Advisor 约定。

## 编辑复核与边界

直接对照设计、修改前正文和改稿，复核了 V&V 与 Test Design 的职责、Product Design 假设与验收依据的区别、委派入口与角色页的引用，以及模板和正文的一致性。
新增链接仍指向既有方法文件；四个新增片段链接分别对应 Inquiry、Resolve Unknowns That Could Change the Route、Reconsider Growing Complexity，以及委派所引用的 Establish Confidence Through Evidence 小节。
没有建立或运行 Corpus 内容测试、盲读实验、提示词评分器、设施测试或改名自检，也没有运行新模型/benchmark。
未提交；不改运行源码、模型配方、CLI、开发侧安装或冻结包。

实施前副本位于 `runs/svc-corpus-review/enhancement-before/`。
相对于该副本的本轮 Corpus 改动保存为 `runs/svc-corpus-review/enhancement.patch`，避免把前轮精简与本轮增强混成一次变更。

本轮只完成正文落地和编辑复核，不宣称已改善模型行为或成绩。
后续沿用已约定的完整 bench 与原生 trace 验收，等待实验安排；先确认实际消费候选材料，再判断提前消除未知、无效重复、证据选择和完整得分。
此前精简与 skill 接线的运行验收仍开放，不因本轮完成而关闭。
