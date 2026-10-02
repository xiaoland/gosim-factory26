# 工作项入口、协作层次与 SVC 导航

状态：产品方案、实施准备均已复核，用户已明确开工并授权自购 API 的完整 Lite 验收。
本次由主 Agent 分析；运行证据见 evidence/keep-wiring.md、evidence/bookstack-wiring.md，消息路径见 evidence/braid-message-paths.md。

## 从使用者的视角组织入口

Agent 是工具与协作环境的使用者。
入口应借助它已有的 GitHub 使用经验，说明有哪些对象、可以怎样操作和联系其他 Agent；工作组织与决策由 LLM 根据问题完成。
将 Issue/PR 映射为设计/实现阶段、解释会话隔离和上下文投影，是实现者理解系统的方式，不应直接转写成 Agent 的入门指令。
上下文隔离与可编辑对象仍是产品行为，使用者通过 Issue/PR、评论等操作获得这些能力。

Factory 是本项目参赛 Agent 的称呼，不是 Braid、SVC、Pi/Codex 之外的运行时组件或指令权威。
具体 variant 负责将这些组件及其配置装配成参赛 Agent；不能据此发明“Factory 能力指引”来接管各组件的职责。
原生 sub-agent 的能力、调用方式与角色发现由 Codex/Pi 及其实际提供该能力的扩展介绍，角色配置与 SOP 也通过对应原生入口提供。

## 两种分工分别解决什么

Braid Agent 是某个 Issue/PR 的负责人；工作项 description、comments 和 metadata 组织其可编辑上下文，成员通过评论异步协作。
原生 sub-agent 是这个负责人会话内的有界执行者，由 Pi/Codex 提供，不成为另一个 Braid assignee。
大任务应优先寻找能缩短关键路径并减少单会话注意力负担的切分；定义明确往往降低分工成本，不能作为独做的充分理由。
需要独立目标和持续协调时组织 Issue/PR；当前工作项内的探索、实施或浏览器操作适合原生子代理。
选择仍由 LLM 作出，不规定子 Issue 数量、必须经过的角色或调度流水线。

## 当前输入的事实

Factory 按 bench 的任务输入构造 request.prompt，包含需求文件入口、应用交付要求和本次运行约束。
Braid Local 将其写入根 Issue description 并指派 root_profile_id；不是把一个 requirement 条目映射为一个 Issue。
现在的初始化还固定标题为“根需求”并产生“根需求已建立，请读取当前需求并处理工作项”的唤醒内容。
初始会话另收到两类材料：Braid 固定指令与 variant 配置的 instructions，以及包含对象快照、重建说明和事件引用的 user message。
这两者不能统称“Braid 发送的消息”：Pi 通过 --append-system-prompt 接收 instructions，Codex 通过 developerInstructions 接收；对象快照与唤起才进入 user message。
所以当前启动消息不是只有“请处理 Issue #1”。

Issue 的角色指令已经明确写“你负责 Issue #1 的问题、设计与验收依据。需要实施时使用关联 PR 的工作树。”
variant 当前的成员指令也明确了 Issue 负责设计、PR 负责实施。
它们存在于实际会话关联的指令归档，因此不能把本轮结果写成完全未告知职责；行为没有落实这一点。
该句位于长期指令通道，不是 user message；但通道正确不能证明其内容合适。
修正目标是从使用者熟悉的对象操作与协作出发介绍环境，而非将阶段映射从 user message 搬到更高优先级的指令中。

## 修正后的输入职责

| 内容 | 负责者与表达 |
| --- | --- |
| 任务目标与需求 | 调用方提供给 Issue description；Braid 保持其内容，不另写一份整个应用的执行命令。 |
| 启动请求 | user message 中只用“请处理 Issue #1。”或“请处理 PR #2。”唤起当前工作项，不在此注入工作方法。 |
| 会话工作上下文 | Braid 投影当前工作项的 description、可见 comments/replies、metadata 和必要关联对象；编辑后按产品行为重建。它是任务材料，不是另一套阶段命令。 |
| 协作环境的使用说明 | 在稳定指令中介绍 braid CLI 的 GitHub CLI 式用法、Issue/PR 指派与评论操作，告知像人类一样在 Issue/PR 中协作。入口使用可见对象与动作，不要求 Agent 学习内部阶段映射或会话模型。 |
| 原生 sub-agent 能力 | Codex/Pi 及其提供子代理能力的扩展负责工具说明、角色发现和调用方式；通过其原生配置承载角色模型与 SOP。Braid 不负责介绍或规定这种委派。 |
| SVC 入口 | SVC skill description 说明它能帮助解决的问题；成员 user instruction 可放简短技能导航，正文与术语留在 skill 内。 |
| 工作方法正文 | SVC 负责 task packet、设计、实施、V&V 和原生委派方法；保持比赛无关。 |

“请处理 Issue #1”是启动指令的收敛，不删除 description/comments 的自动上下文投影，否则会削弱用户明确要求的 Braid 上下文管理。
实际 provider 消息格式在技术方案中落实，不先为这种语义区分发明新的状态机或协议层。
原生会话启动、恢复与上下文重建使用同一职责划分；变更通知报告工作项/讨论发生了什么，由 Agent 决定下一步。

协作入口候选：

> 使用 `braid` CLI 操作 Issue / PR，用法与 GitHub CLI 一致。Issue 和 PR 可以 assign 给其他 Agent。像人类一样在 Issue / PR 中开展协作。

操作示例与评论回复、hide/resolve 等可发现性在技术准备时按实际 CLI 核对，避免声称尚未支持的兼容性；不借示例展开固定协作流程。

## 同类边界审查范围

覆盖根 Issue 初始化、Issue/PR 启动、上下文重建、存量会话的新消息、面向 Agent 的 CLI 返回与固定工作指令。
已发现共用 provider.rs 的 Braid 指令直接提及原生 sub-agent，应删除这项跨界职责，并核对 Codex/Pi 及扩展已有的工具说明是否足够；不另造一层介绍。
初始化“根需求”及其唤醒文本把通用 task 预先解释成 requirement，应使用工作项身份表述。
启动和重建中的“系统已重建工作记忆”、内部事件叙述等不承担产品决策；将事实材料与简短唤起分开，去掉重复指挥。
已核对的 Issue/PR 启动、上下文重建和新通知路径没有根据评论内容自动推导具体处理计划；额外文字大部分是对象快照、内部说明与通用读对象提示。
不能从“启动消息不止一句”直接认定这些路径全都越过语义边界；对象上下文投影是 Braid 的正当职责。
PR 创建通知以及合并冲突反馈也要区分对象事实/操作约束与 Harness 替 Agent 编写的下一步计划。
合并冲突、未指派和会话故障仍需报告具体事实，Agent 据此决定处理方式；不是隐藏错误或删除可诊断信息。
本轮审查入口与职责归属，保留 Issue/PR 对象和上下文管理的实际能力，不由此扩展到调度重写、Pi 子代理生命周期管理或 bench 完成门槛。

## SVC 导航候选

采用 user instruction 的短索引作为主要改进；它在不打开 skill 前就给出高频行为的用途和入口。
建议正文：

> `svc` 是软件开发的工作方法指南。需要理清需求和方案、把复杂任务的进展保存在文件中以便接续或协作，或判断软件是否满足需求、怎样验证修复时，查阅对应内容。反复尝试没有进展时，也可用它重新检查问题和处理方式。只读当前需要的部分。

这替换现有笼统的一句 SVC 指引，不复制方法正文或恢复 SVC CLI。
入口面向尚未读过 SVC 的 Agent：从它已经遇到的问题解释收益与使用时机，指向技能；具体文档名和方法术语在进入技能后再引入。
导航依赖方向是“当前问题 → 可获得的帮助 → 技能入口 → 具体方法”，不要求先理解技能内部章节才能决定是否读取。
具体安装路径由现有技能发现材料提供。
skill description 同步突出触发时机与作用，减少泛泛列举内容；英文候选为：

> Guidance for planning software work, preserving decisions and progress in files across sessions or collaborators, and checking whether results meet requirements. Consult for multi-step work, unclear requirements or technical choices, repeated unsuccessful attempts, or deciding what remains before completion.

description 保持通用，不写 bench、Factory 或 Issue/PR 专属策略。
此次不以低采用率证明 Corpus 正文错误，也不扩大到全部方法重写。

## 后续复核对象

用户已认可从使用者已有经验介绍能力的原则，并要求同类审查与修正。
具体落点、接线核实、实施顺序及检查范围见 [入口审查与实施准备](interface-audit.md)；完成适用的独立预演后呈现具体影响，取得开工确认。
角色是否调用仍按真实工作需要；验收重点是职责和上下文是否清晰、协作是否有实际消费者，以及关键方法是否影响判断，不能以调用数量代替收益。
不新增 Factory、基础设施或 Corpus 测试；后续模型/bench 运行另列具体授权范围。
