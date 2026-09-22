# 从任务责任推导 Agent 边界

本页持有本轮团队结构的产品设计建议，不是已批准的活动配置。证据入口为 Braid `docs/20-product-tdd/local.md`、Factory `harness/instructions/main.md`、`harness/profiles/`、`scripts/native_profiles.py`，以及上一轮按需求整理的 `tasks/multi-agent-integration/requirements-fit.md`。

## 从不可回避的问题出发

最终要交付的是满足需求的应用。LLM 从当前消息推理并通过工具改变环境；一次采样不拥有跨会话的隐含记忆，持续状态由 harness 和外部材料保存。增加一个 Agent 的价值只能来自更合适的能力、更少的无关上下文或可并行工作，代价则是材料交接、重复理解、冲突与整合。不同岗位名称不会自动产生这些价值。

因此首先要确定的是：哪一部分结果需要自己持续维护的设计、验收、讨论和进度？哪些决策需要共享同一份上下文才能正确作出？这决定 work-item 边界。运行时Agent据此创建或指派Issue；Harness再把assignee映射到具备适当模型、技能、工具、权限与方法的内部配置。一个配置可以支持多个Issue/PR会话，不意味着一个全局单例Agent；反之，换模型也不必凭空创建新的产品工作项。

| 对象 | 所持有的责任 | 不从它推导什么 |
| --- | --- | --- |
| Factory task | 一次应用生成目标及完整requirement bundle | 每条requirement各建一个Issue，或预先固定组织架构 |
| Braid work-item | 一次工作的目标、讨论、阶段上下文与交付关系 | 一个固定领域岗位 |
| Assignee | Agent可见的GitHub式协作者身份 | agent-profile、模型路由或内部会话机制 |
| 内部agent-profile | 可重用的模型、方法、工具与能力配置；映射为assignee | 运行时Agent需要理解的协作对象或任务分解规则 |
| Braid Agent | 在该 work-item 上持续组织工作、通过评论与其它工作项协作 | 必须独占一种内部能力配置 |
| 原生 sub-agent | 当前工作项内部的一次有界委派及其局部反馈 | 独立 Issue 或运行时协作图 |
| Task packet | 可恢复、可共享的任务材料与工作控制信息 | Braid 对象状态的第二个权威数据库 |

## 推荐的团队形态

推荐先采用按 work-item 形成的团队，不预设 coordinator/UI/app 等互斥岗位。一个Factory task先建立一个根Issue；description保存任务prompt与冻结bundle入口，单条requirement不自动成为Issue。运行时Agent只把Issue指派给可见的协作者；Issue 会话承担需求、方案和验收设计，PR 会话承担实施计划/预演、执行和验收。其差异来自工作对象与上下文，不需要靠复制两份几乎相同的内部配置维持。根Issue的整体责任来自它所承接的task，不是某个只有它能执行的模型标签。

当任务值得拆分时，Agent 可以为完整的子目标创建 sub-issue，并指派给可见的协作者独立推进；可以不拆，也不需要父 Agent 退出当前执行来释放某种语义容量。讨论、追问、整合通过 comment/thread 进行，Braid 不从评论内容推断批准或完成。原生 explorer/executor/browser-operator/vision 提供当前工作项的有界委派。Kimi 专项咨询可以是原生能力，不能为调用昂贵模型而伪造子 Issue 或由 harness 自动升级。

这不是删除 multi-agent：在当前 Braid 中，一个 Issue 与关联 PR 已对应不同工作项会话；同类多个 Issue/PR 也支持同时执行。内部增加agent-profile应有实际的模型选择、技能/工具权限、专门职责或独立上下文需要；运行时只把这些差异投影成可指派成员的能力说明。若配置只有成本/模型差异，就直说这些差异，不包装成互不重叠的岗位。

一个可复核的对照例子：笔记的创建、编辑、保存、删除及撤销紧密共享状态约束，把 UI 与存储分别指派给两个长期岗位会增加协调。可在同一工作项内由 executor 完成局部改动，由 browser-operator 检查用户旅程。若某应用的两个完整用户能力具有足够稳定的共享接口和独立验收，它们可以成为两个 sub-issue。上述例子解释判断方法，不能固化成赛题专用分解模板或强制阈值。

## Assignee说明与内部配置

内部description记录擅长解决什么问题、相关工具/输入能力、重要限制，以及昂贵能力的代价。Harness把必要信息投影成指派者可读的assignee说明；Agent不读取profile对象，也不知道profile概念。现有Braid只有Profile对象且没有description字段，需在技术设计中贯通内部注册、持久化、assignee投影和GitHub式指派CLI，不能要求运行时调用`profile list/view`。

后续配置表必须分别列 Braid profiles 与 Pi 原生角色：model、真正支持的 reasoning 参数、context、skills、MCP、工具、描述与实际消费者。不能用统一的 high 代替核实不同模型的协议，也不能用模型宣称的1M token窗口替代Braid的字节限制与实际上下文策略。

browser-operator 和独立 vision 均使用 deepseek-v4-flash-vision-exp。前者直接观察DOM和截图完成页面旅程；后者处理给定图片的局部分析。两者可以共享模型但有不同工具和效果边界，避免每次截图都经另一个Agent转发。图片读取、消息传输和工具返回形态仍需真实接口spike证明。

## Braid 与 task packet 的接缝

Issue/PR description 和 comment 维护工作项共享语义及可编辑上下文；task packet 保存不适合反复装入消息的设计材料、局部计划、脚本、证据和当前恢复入口。讨论结论可以指向材料中的具体版本，不要求逐条复制所有评论。反过来，修改一个本地文件不能假装已向其它工作项发送消息。

工作树的隔离意味着文件路径不天然跨 Agent 可见。本轮LLD需要明确材料共享路径或Git版本的读取方式、写入owner和新鲜度；不能因每个会话都存在tasks目录就认定已经形成共享packet。当前阶段先明确此合同，不引入第二个任务调度器或自动同步所有Markdown。

## 下一阶段应证明什么

用同一种profile创建两个需要持续协作的工作项，检查各自上下文、工作树和评论可达性；分别委派原生局部执行，证明它不创建额外Braid工作项。用一个有歧义的局部需求检验Agent是否能保持整体约束和选择不拆分，不以角色调用数作为验收。模型配方与SVC V&V的实验差异另行冻结，不把这份组织设计与换模型的效果混为一项结论。
