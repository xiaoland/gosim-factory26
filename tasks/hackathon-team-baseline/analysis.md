# Lite 改进采用情况：主 Agent 综合分析

本页承接两份逐题评分报告，回答本轮为什么没有体现子 Agent、SVC 方法和 Braid 协作改进。
根因判断由主 Agent 完成；子 Agent 只补取原始材料，入口为 [Keep 接线证据](evidence/keep-wiring.md) 与 [BookStack 接线证据](evidence/bookstack-wiring.md)。
没有修改 Harness、冻结包或评测器，没有新增运行、模型调用或设施测试。

## 能确认的因果链

BookStack 不是完全没有注意到协作与方法指引。
该段原文讨论的是当前会话的原生 sub-agent，不是拆分子 Issue；此前用笼统的“委派”描述它不够准确。
其首段原生会话第 39 行考虑了委派，随后以任务虽大但定义明确为由选择直接实现；第 48 行又考虑保存 SVC 设计笔记，继而选择立即写代码。
这直接支持“主 Agent 选择自己的执行路线”，不支持“它不知道有子 Agent 或 SVC”。
两段记录均在主要实现前；收尾时的 provider disconnected 无法解释之前的这项选择。

实际路径为：

```text
根 Issue 获得整个应用的交付目标
└─ 主 Agent 选择自己实现和浏览器自检
   ├─ 没有委派 → 子角色的独立上下文、SOP、模型、工具均未进入执行
   ├─ 没有继续读取 SVC 方法 → 不能验证正文增强的运行收益
   └─ 工作项没有承接实施协作
      ├─ Keep：主要代码已完成后才建 PR；PR 主要复核构建与启动
      └─ BookStack：无 PR，完成后写交付评论并 close/resolve
```

Keep 没有找到同样明确讨论委派取舍的原文，不能把 BookStack 的理由移植给它。
但它的提交与 PR 创建顺序、评论内容和实际角色调用也符合这条执行路径。

这里必须区分能力选择与职责偏离。
原生子 Agent 是按问题使用的能力，不调用本身不构成缺陷；不能为覆盖角色强制委派。
但“规模大、需求定义明确，所以直接独做”不是充分的取舍：规模本身带来耗时与注意力成本，定义明确通常反而降低分工和集成成本。
应倾向为大任务寻找有用的并行切分；拆成独立工作项还是当前工作项内的子代理，依据工作所有权与协作需要决定，不能混为一类。
Issue 负责问题、设计及验收依据，PR 负责实施，是已确定的工作方式。
先在 Issue 写完应用、再补 PR 或完全不建 PR，才是本轮明确没有维持的职责边界。
Braid 的上下文整理动作确实发生，但尚无讨论被另一成员采用并改变实施的完整链条。

## 子 Agent 是否根本没有接上

对照的是本轮冻结 ZIP 中 Pi 0.85.1、pi-subagents 0.56.0，而不是网络最新版本。
以 ZIP 条目逐字比较了实际读取的 Pi main.js、agent-session.js、两个 package.json 和 pi-subagents/index.ts，均与本轮 runtime-pi-braid 中的对应文件相同。
源码消费者与原始归档支持以下事实：

| 环节 | 本轮证据与含义 |
| --- | --- |
| Factory → Braid | run 保存的 binding 指向成员 launcher；归档 launcher 显式传入 pi-subagents/index.ts 和 observer 两个 --extension。不是只把包放进 ZIP。 |
| Braid → Pi | 本轮 build-input/sources/braid 的 provider/factory.rs:config_for 采用 binding.executable；provider/pi.rs:spawn 增加 RPC、模型、home、指令与会话参数，不设置工具白名单或禁用扩展。 |
| Pi 加载规则 | dist/core/resource-loader.js:316-319 在 noExtensions 时仍选择 cliEnabledExtensions；两个显式扩展可以同时加载。 |
| 扩展注册与默认工具 | pi-subagents/src/extension/index.ts:716 注册 subagent；Pi agent-session.js:157-161 开启 includeAllExtensionTools，工具注册表将扩展工具加入活动工具。disableBuiltins 关闭内建角色发现，不关闭 subagent 工具。 |
| 失败行为 | Pi main.js:725-730 在扩展加载错误时退出 1。两题已经完成实际采样与工具执行，日志没有此类启动错误；因此不支持“扩展正常报加载错误后静默退化运行”的解释。 |
| 仍缺的历史记录 | 原始 argv 的完整展开、当次有效工具 schema/模型请求未留存。入口还有 PI_SUBAGENT_CHILD=1 时不注册父扩展的分支；本轮保存材料没有这个环境标记的完整快照。因此不能宣称已经逐字证明历史网关请求包含 subagent。 |

综合判断是：接线消费者链成立，现有事实更支持正常注册后未使用，尚未定位到应修复的 Pi/Braid 接线缺陷。
这不是“已经验证子代理执行正常”：没有子调用，无法验证角色发现、参数、模型请求及成果采用。
不能为了填补历史缺失字段而把新启动的一次结果冒充旧 run 的实际请求。

## 哪一层没有兑现改进

主指令已经提及 fresh 委派、浏览器角色、SVC 与 task packet，Issue/PR 职责也确实进入该会话关联的指令文件。
其 provider 接线为 Pi 的 --append-system-prompt / Codex 的 developerInstructions；不能与对象快照所在的 user message 混称。
Braid 固定指令不应把实现者的阶段映射当作使用者的操作指南；改进应从 GitHub 式对象操作和 Agent 间协作出发，方法归 SVC，原生子代理能力介绍归 Codex/Pi 及其扩展。
BookStack 对其中内容的主动讨论进一步佐证其可感知性。
因此再添加一句“有 SVC/子 Agent，可以使用”没有对症。
观察到的结果是主 Agent 选择直接实现整个交付，未体现预期的协作收益；BookStack 以“需求足够明确”解释其独做选择，但这不足以抵消规模带来的时间与注意力成本。
这些证据没有唯一定位原因，不能直接推导“应加强阶段指令”，也不能归因于 GLM 的固定能力上限、某句提示词或工具 schema 长度。

现有指令还同时出现“使用当前工作项的 Git worktree”和“Issue 需要实施时使用关联 PR 的工作树”。
它们可以被正确理解为各阶段使用自己的工作树，但初始任务覆盖整个交付、根成员又具备完整实施能力，容易让当前 Issue 被当成整个任务的执行主体。
这是有证据支撑的接线歧义候选，不是已通过消融确认的唯一原因。
两位 Braid 成员也都被描述为可承担完整工作项，没有必须换人的产品要求；只用 GLM 不能单独认定指派器或 DeepSeek 接入失败。

SVC 在 Keep 被读到入口和 packet 导航，BookStack 明确考虑方法后跳过记录，均说明“技能可发现”与“关键方法被采用”是两回事。
直接装入子角色的 SOP 只有在子角色被调用后才可能发挥作用，因此本轮不能评价正文质量、fresh 收益或工具知识是否合适。
同样，没有 Context7/Exa 请求是未观察，不是网络不可达的证据；两题沿用熟悉的技术栈，未发现必须外部查证却因无工具而卡住的记录。

## 对下一轮的具体意义

本轮已经证明普通应用生成、部署、完整评分，以及部分 Issue/PR/评论操作可运行；尚未证明团队型 Harness 的预期工作方式。
优先改进对象是任务入口与组件职责：需求保存在工作项中，用简短请求唤起 Agent；协作说明借助其熟悉的 Issue/PR 操作经验，SVC 入口从实际问题介绍方法价值。
保留按需委派，不增加强制 sub-issue、角色调用数量、讨论轮数或 Braid 的语义调度规则。
不因本轮没有子调用而修改 Pi Adapter、重写 pi-subagents 或重写所有子角色 SOP。

如果要比较主模型能力，应该在职责表达一致后单独改变主模型；当前证据不支持直接把问题全部归给 GLM，或同时调整全部模型与 Corpus。
后续真实运行应留存一次有效工具/角色发现结果以明确工具暴露；这是当前已指出的有限证据缺口，不需要新的观测平台。
以上是分析形成的改进方向，本次未进行实现，也未启动官网或额外 bench。

评分判断继续以 [Keep](results/keep.md)、[BookStack](results/bookstack.md) 为准。
两题已有生成期真实浏览器反馈与局部修复，隐藏评分发生在冻结后，不能用其未回流指控 Factory 反馈闭环失败。
Keep 的 DOM 定位分歧及 BookStack 的 helper 时序/入口分歧，也不能自动归为未使用 SVC 或子 Agent 所造成的产品缺陷。
