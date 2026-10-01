# 正确使用 Braid：Issue/PR 协作方法研究

2026-09-30。独立研究，不是前一轮失分根因报告的续篇；不改实现、真实 Issue/PR、Skill 或配置。先给日常方法，证据和研究放在后半。简版见 [decision-summary.md](decision-summary.md)，可直接执行的写法见 [field-guide.md](field-guide.md)，完整改写见 [cases.md](cases.md)。

## 1. 结论：把 Braid 当协作控制面

正确用法不是“把所有可能有用的信息写进 Issue/PR”，也不是“越短越好”。Issue/PR 的任务是让接手者在默认工作集中看到：

- 当前目标和完成门；
- 这次发生的变化；
- 未决问题、责任和依赖；
- 当前候选与审阅边界；
- 稳定合同、代码和证据的精确入口。

代码、稳定设计、task packet 和原始证据继续各自做权威。description 是**当前协作接口**；comment/thread 是**带作者和时间的一次增量及决策过程**；metadata/relationship 是**机器路由状态**。三者不应复制同一全文，也不能互相冒充。

最重要的操作规则只有五条：

1. Issue description 维护当前义务；PR description 维护当前候选。
2. comment 只写新事实/决定、影响、下一行动和来源。
3. 一个 thread 对应一个可独立结束的问题。
4. 先读目标和本次变化，再按需取代码、合同、证据和历史。
5. 状态动作真实成功后才宣告；送达、理解、承接、审阅和验收分开证明。

这不是全局字符上限、统一大模板、所有信息复制到 description、每次唤醒全量摘要，也不是每条通知强制 ACK。

## 2. 信息模型：一项事实只保留一个当前权威

### 2.1 载体职责

| 载体 | 权威事实 | 控制面必须可见 | 不应承担 |
| --- | --- | --- | --- |
| Issue description | 本工作项当前义务 | 目标、范围、合同入口、完成门、开放责任/依赖 | 逐次进度、WIP hash、完整讨论史 |
| PR description | 当前候选的审阅合同 | 解决的行为、实际变化、head、证据、限制、审阅请求 | 需求全文、完整日志、未裁定历史 |
| comment | 一次有作者/时间的增量 | 新事实、问题、反例、提案、裁决、交接、影响和下一动作 | 当前正文副本、整份文件、无新事实回声 |
| thread | 一个问题的往返 | owner、判断对象、结束条件 | 多个独立问题或长期/短期混合 |
| metadata / relationship | 机器可路由状态 | 责任、生命周期、结构、持续关注 | 理解、采纳、语义覆盖、验收证明 |
| 源码 | 可执行行为 | commit/path/symbol | 决策理由和未决责任 |
| task packet | 开发任务的调查、授权、计划、恢复点 | 当前阶段、决定来源、下一步、证据导航 | 实时 PR/Issue 状态副本 |
| 稳定设计文档 | 跨任务复用的已采纳合同 | 定义、约束、理由、适用版本 | 未决争议和逐次进度 |
| 原始证据 | 可复核事实 | run/artifact/DB/日志身份 | 当前结论和下一动作 |

### 2.2 何时链接，何时必须内联

大块源码、完整 schema、稳定合同、日志、DB 和图片用版本化入口链接；控制面内联“为何相关、关键结论/例外、下一 owner”。

以下不能只留文件或折叠评论：目标/范围变化、当前阻塞、未决责任、契约变化结论、审阅结论、旧结论的替代关系、关闭理由。否则通知到达时，接收者无法判断是否要行动。

路径必须可追溯：共享 Git 内容用 commit/ref + path + section/symbol；运行证据用 run/artifact/DB 身份和必要校验值；仅当所有人明确共享同一工作树时，绝对/相对路径才足够。链接失效风险并不要求把文件全文复制进 comment，而是要求保留决定所需的最小事实。

### 2.3 防止平行状态

动态 head 由 Git/PR 负责，冻结候选时才在 PR description 固定；负责人和状态由对象元数据负责；共享合同由拥有它的稳定文档负责。其它对象只写消费版本和本项影响，不持续镜像。

更新流程是：先更新事实权威，再留一次传播 comment；若当前义务或候选改变，更新对应 description。旧 comment 保留决定出处，新入口保留当前结论。不是把同一全文写三遍。

## 3. 元数据和关系：路由，而不是理解证明

成熟 GitHub 把 assignee、label/type、milestone/status、blocked-by、linked PR、review request 和 subscription 分开建模。这样做的价值是可过滤、可查询、可通知，而不是让 prose 重复机器状态。

当前 Braid 本地实现的能力更窄：一位当前负责人、Issue parent/child、PR–Issue association、显式 subscription 和对象生命周期；当前 renderer/CLI 不提供通用 labels、milestones、typed dependency 或原生 review decision。方法必须以实际能力为界：

- assignee 是当前执行责任和会话生命周期，不只是标签；
- parent 是分解/导航，不递归注入父或祖先正文；
- PR–Issue link 是背景/导航及 PR 对 OPEN Issue description 的依赖，不表示订阅、承接或关闭意图；
- subscribe 是持续关注，`@` 是一次定向联系；
- OPEN/CLOSED/MERGED 只表示对象生命周期，不表示产品验收成立。

任何跨对象依赖仍需一句责任语义：生产者、消费者、产物版本、满足条件和证据入口。排除范围必须有承接项/owner/关闭条件；“不属于我”不是交接。

## 4. 阅读与上下文：当前工作集 + 按需慢层

### 4.1 默认读取顺序

1. 精确读取触发事件指向的 comment/变化；
2. 读当前对象 description、assignee、status 和直接关系；
3. 读相关 diff、源码 symbol 或合同精确段落；
4. 有歧义、反例、争议或来源核验时，再展开 thread、linked object、证据和历史；
5. 行动前确认候选/版本身份，行动后只更新发生语义变化的入口。

Agent 不应每轮复读整套 docs、全部 comments 或所有 linked objects。也不能只看自动投影就声称没有父层约束：关系不会自动把祖先合同送进来，References 降档甚至会截短 description。

### 4.2 当前 Braid 实际投影

- Issue：标题、状态、当前负责人、关闭理由、直接 parent/sub-Issue/PR 引用、自身 description 和自身当前可见讨论；不递归展开祖先/子项/PR 正文。
- PR：自身标题、状态、负责人、head→base、description、讨论；列出全部直接关联 Issue，只展开 OPEN 关联 Issue description；不展开关联 Issue 评论或 CLOSED Issue 正文。
- hidden comment 不进入默认讨论；resolved cutoff 内只保留 root 标记；deleted 正文不可恢复。

预算固定按 Full → CommentIndex → References → 最小 locator 下降。CommentIndex 去掉评论正文但保留结构和单条读取入口；References 清空评论，从每项 1200 字符开始逐次减半截 description，并给完整读取命令。判定同时受 byte hard limit 与粗估 token 严格低于模型窗口 20% 约束；估算并非模型 tokenizer。

这说明两件事：

- “已存在 DB/关系里”不等于“默认注入”；
- “已注入 token”也不等于“Agent 已理解或可靠使用”。

分档只在初次物化、真实 description reset 或必须新建原生会话时选择；普通 comment wake、metadata 更新和正常 resume 不会每轮重发完整投影。没有证据证明 I11 实际触发过当前降档算法，不能把静态代码写成历史成本测量。

### 4.3 为什么 LLM 比人更需要选择协议

GitHub UI 允许人扫侧栏、折叠、搜索和随时跳转；Braid 的模型输入由 runtime 投影和事件构造，不能假设“UI 上看得到”就是“这轮收到”。持续 Agent 还会被异步唤醒、恢复旧原生会话或因 description 变化重建。

`Lost in the Middle` 只改变相关信息在长上下文中的位置，模型表现就可能显著变化；SWE-agent 显示专为 Agent 设计的导航/查看接口会改变行为和表现。它们支持把当前目标、关键约束、未决行动放在显著工作集，并提供按需读取；不支持统一字符上限、永远只看首尾或“长上下文必然无用”。

## 5. comment 与 thread 生命周期

### 5.1 创建与继续

一个 root 只有一个主要问题、owner/判断和结束条件。补证据、回答、裁决和确认落点继续 reply；新 owner、新交付物、新结束条件或旁支风险另开 root 并互链。

真实 #308 thread 把三个合同裁决、文档义务、清单外失败和折叠回执混在一起。历史 `resolve 318` 折叠整个 root，恢复后只能全部保持可见。这不是“少写几句”能修复，而是 thread 边界错误。完整拆分见 [cases.md](cases.md)。

### 5.2 决定何时上移

- 跨任务复用且已采纳 → 稳定设计文档；
- 改变本项当前目标、范围、完成门或开放责任 → Issue description；
- 改变当前候选、证据或审阅边界 → PR description；
- 只解释历史选择 → comment/thread。

上移前保留决定身份、替代对象、影响范围和适用版本；上移后 comment 只需指向当前入口。重要结论不能仅留在准备 hide/resolve 的历史里。

### 5.3 hide、resolve、delete

当前 `hide` 只作用一条，保留正文/身份/reason，不隐藏回复；unhide 可恢复。它只降低后续默认可见性，无法从已运行原生历史删除文字，也无法撤回已 queued/delivered 通知。

当前 `resolve` 只接受 root ID；执行时以 thread 最大 comment ID 作为 `resolved_through`，折叠整串时间前缀；新回复在 cutoff 后仍可见；再次 resolve 才吸收新回复；unresolve 清空整串 cutoff。resolve 前必须读取整串、上移长期决定、拆出未决责任并核对 root/cutoff。混合 thread 宁可开放。

`delete` 清空正文且不可恢复，不是整理手段。敏感信息原则上不应先写入；真正需要删除须服从额外授权与证据规则。

### 5.4 无新事实的停止条件

当前 comment 创建/编辑/hide/resolve 会联系当前负责人、显式订阅者和同 thread 历史参与者，并处理当次 `@`；操作者本人跳过。由此，一个“收到”“仍无变化”或整理动作也可能变成别人的新输入。

不要求每条通知 ACK。范围、责任、未决、冻结候选或证据适用性没有变化时，不镜像 WIP head，不发状态回声，不通过 hide/resolve 制造一次新的维护回合。真正的契约变化、反例、阻塞和交接必须通知，不能为了少打扰而沉默。

## 6. 状态、终态和恢复

### 6.1 状态动作不是文字

历史 PR #23 #347 先写“Issue #1 已关闭”，#348 实际读到仍 OPEN，#349 执行 close 并取得回执后才成立。协议因此要求：先做 mutation，核对 changed/state/head/merge，再写“已完成”。写操作结果未知时先读状态，不重放 mutation 取 ID；#256/#257 已证明重放会产生重复正文和两组通知，随后 hide 也无法撤回。

### 6.2 close/merge 的边界

当前 close 可与解释 comment 同事务保存；若对象已经是目标状态，则 no-op 且不再发表评论。close 不检查其它工作项、PR 或业务验收，不打断当前执行。负责人自己 close 只记录状态，外部 close 才作为普通输入联系负责人。

ready/draft 是状态增量，不是 review approval。merge 使用 origin 的精确 base/head，可用 `--match-head-commit` 防错；普通关联 Issue 只得到 merged activity，只有 PR description 的关闭关键词且目标为默认分支才关闭 Issue。终态前必须把需要别人继续处理的结果放到正确对象；不能假设全部对象关闭后还有一次 finalization turn。

### 6.3 当前与历史重建语义必须分开

I11 历史中可见 comment edit/hide/resolve 和 link/unlink 会产生 Invalidate；维护动作曾推动 reset。当前 I13 dirty 工作树已经改为：

- 只有有效 description 变化重建本项；
- OPEN Issue description 变化才跨面重建关联 PR；
- comment/title/parent/link 变化走增量通知，不重建；
- 操作者不收到自己的操作；
- 正常 resume 保留旧 native history，不因全投影 hash 变化自动 start。

当前只经过编译和只读 CLI 核对，真实写操作、并发送达、休眠 resume、模型采用仍未验收。报告中的历史成本不能倒推成当前实测收益；当前静态修复也不能声称已消除同类行为。

另一个必要边界：I13 `materials-plan.md` 提议“先 hide 旧根提醒再建新提醒”，但当前 `root_idle_tick` 仍每次新增可见提醒，只向根负责人投递；计划尚未实现。

## 7. 真实案例支持什么，不支持什么

### 7.1 可观察负载

| 指标 | GitHub | Sheet |
| --- | ---: | ---: |
| Issue/PR 数 | 23 | 14 |
| description 当前字符 | 69,748 | 191,426 |
| description edits | 186 | 374 |
| comments | 352 | 589 |
| comments 当前字符 | 388,017 | 904,879 |
| 最大 description | Issue #6，9,293 | PR #9，35,643 |
| context resets | 182 | 359 |

GitHub thread #308 有 11 条、17,499 字符；Sheet thread #1 有 138 条、222,576 字符。Sheet 根的一次实际输入达到 167,672 字符。

这些数字支持“维护和定位面较大”，不支持“字符越多必然越错”“reset 全由内容墙造成”或“删字会线性节省 token/时间/得分”。Sheet 同一次大输入里，Agent 正确识别已有 #265/#267 并停止催问，也仍重新定位旧 thread、纠正状态。

### 7.2 真正稳定的结构发现

- 大 description 的共同问题是混合当前合同、历史理由、动态 head、原始证据、外部状态和无动作回执。
- 大 thread 的共同问题是多个关闭条件共用 root；resolve 粒度无法与语义粒度一致。
- 重复写入不是普遍“大段复制”：GitHub 唯一的大块 Agent 精确重复是 #256/#257；其它多是短系统提醒。应区分 method 问题和 runtime 生产者。
- 表格、REQ ID、全部 CLOSED 都是代理指标；证据必须绑定真实 head/artifact，审阅必须说明已核和未核的语义范围。
- merged、closed、delivered、consumed、reviewed 不是同一个状态。

完整 before/after 与下一行动见 [cases.md](cases.md)。

## 8. 人类工程标杆与研究启发

### 8.1 官方实践：能力事实

GitHub 官方把 Issue 用于计划、讨论和跟踪，把 sub-issue、dependency、assignee、label/type、milestone、subscription 和 linked PR 分开；PR review 又把 Comment、Approve、Request changes 分开。多条 review comment 可一次提交，官方明确提到这样能减少多次通知；超出 PR 范围的建议应开新 Issue。hidden comment 只是 minimized but expandable，适合 off-topic/outdated/resolved，不是删除。

Google Engineering Practices 要求首行可独立扫描，正文解释问题、why、局限并链接设计/基准；也提醒外链可能失效，需保留足够上下文。review comment 应说明理由、区分必改/建议/FYI；长期解释应写回代码或设计，而不是只留 review 工具。

这些是成熟标杆，不是 Braid 当前能力。特别不能据此在 Braid 要求不存在的 label、blocked-by 或 approve 命令。

### 8.2 实证研究：适度推论

- Google 约 900 万 reviewed changes 的研究描述了轻量、异步、小变更、快速迭代和少数 reviewer；review 也承担理解和知识传播。单公司案例不能规定 Braid 制度。
- Microsoft 约 150 万评论研究发现，变更文件越多，有用评论比例越低；熟悉文件的 reviewer 更可能给有用意见。usefulness 含作者感知，不等于 token 或产品质量。
- pull-based development 研究显示贡献者需要状态 awareness 又不会充分传播，integrator 面临质量和优先级负担。这支持结构化状态与明确 handoff，不支持让所有人订阅所有项。
- RE–VV 对齐研究支持需求变化、验证证据和共同理解需要传播；traceability mapping 同时报告变更管理收益和维护 link 的成本。由此应保持少量高质量可追关系，而不是追求关系数量。

### 8.3 对 Agent 的设计提案

综合而不是照搬：description 首屏服务 triage/下一行动；review 意见有界批量提交；长期结论进入稳定载体；可表达的状态使用现有 metadata，缺失的 typed metadata 只作为未来候选；Agent 用窄化接口按需读取源代码和证据。外部研究不能证明这些规则会提高本项目官方分数，需先做历史桌面回放，再由另获授权的运行检验模型采用。

## 9. 职责图景

```text
方法 / Skill
  决定写哪里、先读什么、何时拆 thread/上移/交接/停止
        │
        ▼
CLI
  精确读字段和版本；写回 changed/unchanged、ID、root/cutoff、影响与具体错误
        │
        ▼
Runtime
  投影、预算降档、关系展开、通知、invalidate/reset、历史恢复
```

方法不能承诺系统不存在的继承、通知或 review；CLI 不判断理解/验收；runtime 不把 link/close/delivered 自动提升为承接/通过。三层共同的底线是保留精确来源和版本，不把维护动作伪装成业务义务。

## 10. 不跑模型的验证方案

本轮不运行测试、生成、评测或模型。用已有资料做静态审阅和桌面演练：

1. **新接手演练：** 只按默认读取协议，能否指出当前目标、变化、未决 owner、合同/证据入口？
2. **放置演练：** 把 Issue #6、comment #89、Sheet PR #9 按决策流重排，检查是否产生第二份当前事实、孤儿义务、隐藏例外或不可追版本。
3. **thread 演练：** 对 #308 列 root、cutoff、长期决定与拆出的未决，确认何时安全 resolve。
4. **通知演练：** 对 WIP hash 维护链和 #256/#257 逐事件判断是否有新事实、是否触发读/写/通知；不估算反事实 token。
5. **追溯演练：** 对 PR #23 从原需求→Issue→PR→review→证据追一条义务，区分 ID 出现、语义覆盖、真实执行和最终对象状态。
6. **正例回归：** 对 Issue #8→PR #17 验证新规范不会强迫多余 ACK、全文复制或过早 close。

记录的结果类型只有：缺失当前事实、冲突副本、孤儿责任、不可追版本、混合关闭条件、无新事实回合、规则误报。字符数、评论数、全部 closed 或 REQ 引用率不能单独判通过。

## 11. 最终判断与后续边界

可教给 Agent 的核心不是“写短”，而是**控制权威、增量、关闭条件和读取路径**：

- 当前义务有一个默认入口；
- 新消息只增加一个可行动差异；
- 每个 thread 有可独立结束的语义边界；
- 大事实留权威载体，控制面保留结论和路由；
- 关系与状态负责机器路由，人类/Agent 仍需证明承接和验收；
- 历史完整可追，但不常驻每轮工作集。

这套方法与现有 requirements-tree 规划兼容：原需求身份和上层责任仍由其方案维护，本研究只规定 Issue/PR 如何承载、传播、读取和收束，不重做节点映射。

后续若写 Skill，应从 [field-guide.md](field-guide.md) 提取最小操作协议，并把“当前 Braid 能力/未来 typed metadata 候选”严格分开。此次不修改 Skill。若要验证行为收益，必须另定当前源码冻结身份、历史回放判据或获授权模型实验；本研究没有取得运行效果证据。

全部来源及精确版本见 [evidence-index.md](evidence-index.md)。
