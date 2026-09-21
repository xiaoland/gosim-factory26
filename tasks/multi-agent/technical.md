# Braid 协作能力的技术方案

本方案仅对应用户要求落地的第 1 项。新增或选择更多 agent-profile 属于后续 Factory 装配项目，本轮保持请求中的单一 profile 及现有 Issue/PR 派生配置。SVC Corpus 清理和全面诊断设施改造也不在本轮；已有输入、会话和交付证据随行为改动保持可用。

产品依据见 [design.md](design.md)，验收依据见 [verification.md](verification.md)。用户于 2026-09-21 明确同意技术、验收和实施方案；实施前进行了独立预演并提交基线。下文诊断事实对应源码起点 `e0c3ca2`，方案实施与验证结果单独见 [execution.md](execution.md)；当前操作契约归 Braid 本地协议。

## 对象、CLI 和上下文

复用 SQLite 本地对象权威及现有 renderer。新增不可变迁移，旧 comment ID 和正文不变，旧扁平 comment 作为独立讨论起点；不修改已发布迁移。拟增加以下机械事实：

| 数据 | 用途与边界 |
| --- | --- |
| comment 的回复对象及讨论根 | 保留针对谁回复的关系，所有回复属于同一 work-item。新回复引用已经存在的 comment；不复制原文。删除保留墓碑与回复关系，不级联删除讨论。 |
| thread 的 resolved 状态与折叠范围 | resolve 折叠当前已有讨论，后来的回复仍可呈现和投递；unresolve 恢复讨论，但不恢复另行隐藏或删除的正文。折叠范围需要稳定顺序标识，不依赖墙钟先后。 |
| comment 的可选 hide 理由 | 正文移出默认上下文时，身份、隐藏状态和理由仍可读；显式回看可以读取仍保留的内容。 |
| reaction 的目标、作者和表达 | 同一作者对同一 comment 的同种表达去重，可以撤回。作者来自当前 writer 身份，不接受模型自行冒充另一个作者。 |
| Issue 的父关系 | 可选的单父关系，拒绝自引用、环和不存在的对象；通过已有 parent/sub_issues 投影呈现引用，不递归展开全文，不附加审批或自动关闭行为。 |

拟议 CLI 沿现有模式扩展：`issue/pr comment ... --reply-to COMMENT_ID`；`comment view ID --thread`，显式选项查看折叠内容；`comment resolve/unresolve ID` 操作其所在讨论；`comment hide ID --reason TEXT`；reaction 的添加/撤回。Issue create 可指定 parent，edit 可关联或解除 parent。现有正文/stdin、JSON 输出和 writer 身份行为继续保持；具体参数表在实施预演中一次性核对所有消费者，不增设同义接口。

默认 Context 呈现开放讨论及可见正文、折叠讨论的定位信息、隐藏理由和 reaction 作者。已 resolved 讨论的新回复进入 Context，而旧正文继续折叠；harness 不自动替 LLM 作出 unresolve 决定。编辑已折叠历史的正文仍保持其折叠状态，变化引用允许主动回看。resolve/hide/reaction 均不直接改变 Issue/PR 完成状态。

## 异步消息的投递

复用当前对象写入与 events/wake_batches 同事务的机制，不建立任务结果事件或新的消息平台。现有 `objects.rs::changed` 只覆盖目标和直接关联 Issue/PR，单靠它不能保证无关联的 Issue A 在 B 留言后收到 B 的回复。

建议接收范围为讨论所在 work-item、现有直接关联消费者，以及该 thread 中发言的 Braid Agent 所属 work-item；同一变更的接收对象去重，发起者不因普通自身消息反复唤醒。父子关系本身不广播消息，不遍历祖先或后代。作者持久身份映射回逻辑工作项，不以可被替换的 provider session 为收信地址。

跨工作项消息仍归原 thread 保存；接收方获得带来源及稳定 comment ID 的简短引用，通过 CLI 读取讨论，不把外部完整讨论复制进本工作项。变更和接收引用原子提交，沿既有队列合并、重启恢复和输入重放执行。物理会话重建不改变消息归属；这一跨工作项路由需要在实施预演中用真实事务与输入档案核对，不只测试 renderer 字符串。

## 自编辑真正作用于会话

当前 `objects.rs::emit` 把自身 Wake 和 Invalidate 都变成 OriginEcho；`prepare_dispatch` 只在已有下一次合法输入时补做重建。这意味着自身改 description 或 hide 后，若没有后续外部输入，不保证发生上下文替换。

拟保留普通自身 comment/reaction 的回声抑制，但对改变已物化正文或可见性的操作保留失效事实，包括自身修改。对象写入先原子完成；现有 reset 链随后 fence 旧 writer、interrupt 对应物理执行、从 canonical state 创建替代会话并继续。无效旧 writer 不能借重试绕过屏障。无需 Agent 手工 refresh，也不要求它为其它会话让位而结束执行。

这里有一项已发现的竞态：当前 reset continuation 取决于是否还能选到活动执行。如果 provider 恰好先结束，idle reset 不会产生 continuation。因此自身语义内容修改后的继续处理必须由持久的失效来源和会话事实决定，不能依赖通知到达顺序。只针对需要重新处理的自编辑保留一次延续，不能把每次普通自发 comment 变成自激循环。该变更和 finalizing 状态的关系必须在正式实施预演中一起检查。

具体还需修正 terminal 结算：已有待处理失效时，finalization 不能抢先把会话置为 sleeping/retired，令 reset 再也无法选中它。是否需要失效取决于默认投影是否改变；同值写入、不可见的 HTML 注释或已隐藏正文修改不因此增加无效重建。

这一方案的可见行为需要复核：自编辑成功提交后，旧物理会话可能立即被替换，不能假定仍能用旧 writer 连续执行下一条命令，也不能依赖一定收到原工具的成功输出。继续工作所需信息应已存在于当前对象或工作树。协议会清楚说明这个边界；不会宣称中断能撤销已经发生的 shell/Git 操作。

## 不同工作项的独立执行

保留现有两个 role driver、StoreActor 和 SessionManager；不新增每工作项进程或第二个调度器。`worker.rs` 的单个活动执行改为按物理会话索引的集合，分别接收终态、失联、reset 和 steering；同时继续物化、恢复并 claim 其它 idle 会话。现有 `store::claim_runnable_turn` 已通过持久事务保证每个会话只有一个当前执行，不需要重建身份体系。profile 配置保持原样。

独立源码调查发现，不能只把 Option 改成集合：

- `prepare_work_item_finalization` 当前可能把仍在运行的对象的 close 当作无事可做并消费；需要保留尚不可执行的关闭处理，同时让候选查询跳过它，避免阻塞其它对象。
- resume 路径会按候选集 retain session，而候选不含 reset_pending；必须保留当前活动集合仍持有的会话，直到对应 reset/终态路径释放，不能误关另一会话。
- 终态匹配、失联处理和 shutdown 逐会话处理，不能因一个失败清空其它执行；旧 close/reset 的顺序不能改变恰一次收尾和已封存交付的条件。

先修正按 session 的独立性，不把活动逻辑会话数量直接当成 LLM 请求并发数，也不新增“等待时必须结束执行”的约定。比赛 API 的请求并发控制仍属于具体实验条件；若需要限流，应在请求执行边界核实，不能以此重建父子等待协议。本轮保持 Git merge intent/CAS 和最终 delivery commit 权威不变。

## Provider 子代理与角色指导

本轮核查 provider sub-agent，不配置新 profile 或装配新扩展。Pi 当前 Factory wrapper 使用 `--no-extensions`，所以宿主虽装有 pi-subagents，也不代表隔离运行中可用。Codex 二进制有 `multi_agent` 特性；app-server schema 没有 spawn RPC 不能证明模型侧工具不存在。当前证据尚不能确认隔离运行的实际工具暴露以及父会话替换时子会话的存活、写入和结果回注边界，后续需针对实际配置验证。

这项未知不应伪装成已接通，也不应把 provider sub-agent 变成 Braid 工作项。Braid 本轮可先验证其自身各 Agent 会话的独立性；provider 子代理的启用与不同 profile 的装配另行处理。

`group/provider.rs` 的产品指导需要同步：Issue 负责需求、技术方案、最终验收方案；PR 负责实施预演与计划、执行、最终验收及证据。去除“结束当前 turn 等待后续事件”等组织工作要求，保留底层调用所需的 writer 标识。comment 是交流与工作记忆，不是控制阶段的指令。根 Issue 仍根据实际交付判断总体完成，不把讨论状态当作验收。
