# SVC 委派与反馈方法：09 设计稿

阶段：四项方向已获认可，用户进一步授权后已按本稿实施 SVC 源码迁移；实施记录与复核边界见文末。没有新增 Corpus 或基础设施测试，没有打包、运行或提交。09 接线、冻结材料及运行安排由主线统一管理。

## 目标、证据与已认可方向

目标是让委派减少主会话必须承载的局部上下文与串行工作，同时保留正确的采用依据。收益包括更小的调查回显、可并行工作、局部自主闭环和较便宜的结果判断；不是调用更多角色、压低输出字数或省略必要验收。

原始讨论已完整整理于 [来源复核](subagent-paradox-source.md)：五条可见消息中，用户明确聚焦低成本验证和不必重读全部证据；末条 assistant 的控制面/效果闸门/固定返回结构没有可见用户确认，不作为本设计要求。当前 [运行接缝](svc-runtime-seam-review.md)区分技能目录与实际正文注入；[使用账本](usage-map.md)证明重复写任务、未取得返回以及成功消费视觉报告的不同情况。

[token 截面](../../experiment-infrastructure/cells/token-economics.md)的具体可行动证据是两次宽范围进程回显合计 78,806 字符，以及跨成员重复全文读取；这不等于全部可删，更不能按字符或 cacheRead 推算固定节省比例。[Sheet 08](../../braid-product-reaudit/cells/attempt08-sheet-progress.md)表明检查退出码、环境失败、产品缺陷和共享基线变化必须分开：Playwright passed 仍可能有 cleanup 退出1，长临时路径导致浏览器未启动，候选合并后旧 PASS 未必覆盖新行为。检查多并不自动等于浪费。

保留用户已认可的四项方向：

1. 新增独立 `svc-delegation`，迁移通用方法而非复制；其他技能明确路由。
2. 形成独立有用的结果、局部反馈和集成边界；开放问题也可以委派，不要求父先想完全部方案。
3. 角色由反复出现的问题、专业方法/工具与可消费返回形成；一次性任务不要求新建角色。
4. 输入包含现有负责人、在途工作、共享前提；消费实际结果，避免重做和盲收。

**对第 4 项的修订：不再以信息/产物二分决定验证方式。** 信息结论可能由一个 SQL 或结构查询廉价检查；代码/设计产物也可能包含没有客观 oracle 的判断。应先看采用哪项命题、什么观察能支持它、父理解与核验的成本、错误后果，再选择依据。

## 方法树与责任边界

```text
委派（svc-delegation）
├─ 是否值得：直接工作/现成工具，与交接、执行、消费、返工比较
├─ 形成边界：独立用途、必要输入、局部反馈、允许效果、集成面
├─ 选择能力：反复问题 + 方法/工具 + 可消费返回；不按阶段强制分人
├─ 派前核对：当前负责人、在途工作、共享前提，避免重复写同一目标
└─ 采用结果：明确命题和当前用途，选择足够且便宜的依据
   ├─ 可检查事实/约束：审查小查询或判定逻辑及范围，取得实际结果
   ├─ 关系或变化：依据相关不变量、差分或行为观察
   └─ 开放判断：理由、替代方案、反例、未知与真实反馈
调查：按问题收窄读取/回显，保留来源与失败含义，停止无信息增益重复
实施：局部反馈指导修改，实际候选与共享契约一致
V&V：检查设计、实际完成、结果含义、证据适用范围与复验
Task Packet：保存当前所有权、在途成果入口与下一条件，不接管执行生命周期
```

这些分支是选择依据，不是固定角色或阶段。新技能讲委派和结果消费的因果机制，V&V 保持证据判断权威；不复制完整验证目录，不创建成本打分表、证书 schema、固定 reviewer 或状态机。真实运行句柄、通知、权限限制和恢复归 harness；Corpus 不写模型、比赛或具体运行字段。

## 当前已有方法与拟变更清单

| 所有者/路径（均相对 `sources/svc/`） | 已有内容 | 拟动作与具体增量 |
| --- | --- | --- |
| 新 `skills/svc-delegation/SKILL.md` | 原通用正文目前在 task-packet reference | **迁移并替换展开**原成本比较、能力匹配、可用返回、单写者及父子责任；补工作边界形成、角色内聚、现有 owner/in-flight 核对、按命题选择可消费依据。核心保持在一个短 skill，不新增多层 reference |
| `skills/svc-task-packet/references/delegation.md` | 唯一通用委派正文 | **删除旧正文文件**，不留同义副本或另一份方法权威；下面入口同时迁移 |
| `skills/svc-task-packet/SKILL.md` | 表格路由至旧 delegation.md；Core method 已记录 owner/dependencies/evidence | **替换**委派行目标为 `../svc-delegation/SKILL.md`。在既有 Core method 的 owner/next return 句中合入“进行中工作与结果入口”，不新增任务账本/表格 |
| `skills/svc-investigation/references/delegating-investigation.md` | “Apply the delegation criteria”无链接；已要求 scope/freshness/只读/足够答案 | **替换**为明确链接 `../../svc-delegation/SKILL.md`；保留专项调查方法，不重复通用原则 |
| `skills/svc-implementation/references/delegating-implementation.md` | 同样无入口的 criteria；已有effect surface、feedback、局部修复与升级 | **替换**为同一新技能链接；保留专项实施，不新增固定先调查后实施顺序 |
| `skills/svc-investigation/SKILL.md`、`skills/svc-implementation/SKILL.md` | 各指向自己的专项 delegation | **小幅替换入口句**：何时/如何委派指新技能，角色专项说明指既有 reference；两者职责显式，不要求重复阅读所有材料 |
| `skills/svc-investigation/references/workflow.md` | 已有按决定查询、足够即停、保留出处；停滞段已有wait/notification | **在既有段内补足**：先选能改变判断的范围/字段/行段，优先短查询/摘要而非全目录/全进程命令；需要细节时保留原始结果入口。等待句具体化为已有完成信号优先，不能叠 sleep+重复状态查询；无信号且当前确需进展信息时才有界查询 |
| `skills/svc-verification/references/repeatable-checks.md` | 已要求条件等待、失败原文、跳过不算通过、实际断言发生 | **补实际完成与输出边界**：获取承担判断的命令退出状态；截断/过滤展示不改变其失败含义，原始错误可找回；任务完成反馈与产品异步条件等待分开。前者复用已有通知，后者仍需条件等待，不以“少轮询”为由省略 |
| `skills/svc-verification/references/interpreting-results.md` | 已区分应用/检查/环境/缺观察；已要求对应实际候选，足够即停 | **替换末段收敛句**：指出候选或有关前提改变时选择受影响行为复验，未受影响有效证据可复用；全产品结果未观察时仍需整体验收。不另造验证强度阶梯 |
| `skills/svc-verification/references/evidence-design.md` | 已有最低成本且保持语义的边界、成本/错误信号考虑 | **保留不改**；委派消费路由此处。便宜但丢失用户旅程不是省钱，已有充分表达 |
| `skills/svc-implementation/references/workflow.md` | 已按改变的行为与边界选反馈，并明确局部PASS不是最终验收 | **保留不改**，不重复追加“少跑测试”或套件配额 |
| `README.md` | 把delegation列入task-packet职责 | **替换目录职责**，列新技能，task-packet只保留任务状态/规划/模板，不扩正文 |

当前源码文本检索只发现 task-packet 入口直接引用旧 reference，调查/实施是无链接文字；实施时须再看同批改动后的实际消费者，迁移必须同时替换。不要因怕断链长期保留双正文。

Factory 消费接线是独立实施面：冻结技能选择与活跃启动器须包含新技能；需要决定委派的父会话能发现它。子角色只在其任务可能再委派时才需要可发现入口，不把新正文一律强追加五角色。当前三角色直接追加的 investigation/implementation/design workflow 保留其职责，不因新增技能复制通用委派全文。具体打包、锁、清单与角色 consumers 由09总计划统一核实，此设计不授权修改历史包或旧运行。

## 少量拟正文

下面保留实施前的英文正文草案作为设计依据，当前权威正文已迁入对应技能，实际实施范围见文末。

### 新技能核心（迁移后的结构与拟文）

Frontmatter：`name: svc-delegation`；description 拟为 `Decide whether and how to delegate useful work, then consume the returned result without repeating it or accepting unsupported claims.` 版本按仓库现行发布规则处理，不在本设计预定发行号。

> Use delegation when a child's independent work can repay context transfer, waiting, correction, and integration. Compare it with direct work and an available deterministic tool. The gain may come from parallel work, a different method, or reducing the raw material the Primary must process. A role name or another Agent's agreement does not establish correctness.
>
> Shape an assignment around a result with an independent use, enough source context, local feedback, permitted effects, and a clear integration boundary. An open question can be delegated without prescribing its answer. Let the child resolve bounded information and design gaps; keep decisions beyond that boundary with the consumer.
>
> Before assigning work, check the current owner, work already in progress, and relevant shared conditions. Coordinate overlapping effects before adding another writer. On interruption or recovery, inspect the original work and existing artifacts before reassigning the same change; missing status does not establish that it stopped.
>
> Match capability to the judgment and tools the work needs. A reusable role earns its place through a recurring class of problems, methods suited to them, and returns that a consumer can use. A one-time assignment need not become a role, and a stage name does not require a separate Agent.
>
> Name the intended result and its consumer, relevant sources, effect limits, required initial state, available feedback, and the condition for returning unresolved work. Pass the context needed for that return rather than the full parent history. The child handles local reasoning and recoverable failures; the Primary owns the overall decision and integration.
>
> Decide what claim the return must support and how it can be judged at lower cost than repeating the work. For a checkable claim, a small query or constraint with its actual result and input scope may be more useful than a large evidence dump. For an open judgment, use the reasons, alternatives, counterexamples, and remaining uncertainty to inform the next decision. Neither form makes unsupported conclusions acceptable. Use the verification skill to judge the evidence and its limits.
>
> Consume the actual return against the current decision and artifact. A launch receipt is not a result. Reuse applicable observations, investigate material contradictions, and retain uncertainty where evidence is missing. Do not require the Primary to repeat the whole task merely to use it.

末尾路由：调查专项 `../svc-investigation/references/delegating-investigation.md`；实施专项 `../svc-implementation/references/delegating-implementation.md`；证据判断 `../svc-verification/SKILL.md`；恢复/协作状态 `../svc-task-packet/SKILL.md`。这些是按需入口，不是必读链。

保留两个简短对照例，不增加字段模板：

- 大量记录是否存在孤儿引用，可返回范围明确的关系查询和实际结果；父检查查询是否覆盖要判断的关系及空值等前提，而不重读所有记录。它不证明所有数据业务规则成立。
- 选择交互方案未必有布尔判定器；子可返回备选、约束、反例与有用观察，父决定下一步原型或行为反馈，不用多数赞同冒充验证。

### 现有所有者的窄修订

调查 workflow 在获得足够问题上下文后加入：

> Choose the smallest query scope and output that can distinguish the live explanations. Request relevant fields or sections before dumping complete files, directories, or process lists. Keep a source handle for details that the consumer may need; a short display must not turn a failed query or incomplete search into a negative finding.

调查停滞段**替换现有等待句**：

> Use an available completion notification or wait mechanism for work already in progress. Do not add repeated sleep-and-status calls that provide no new decision-relevant information. If no completion signal is available and progress must be checked, make the query bounded and preserve the condition that will justify the next action.

repeatable-checks 合入实际执行/失败含义段：

> Obtain the completion result and exit status of the command that carries the check. A successful display filter or final shell command does not replace that status. Keep output concise while preserving the concrete failure and a path to the original result. Reuse the execution system's completion signal; separately wait for any product consequence the requirement promises.

interpreting-results **替换末尾扩验/停止句**：

> When the candidate or a relevant precondition changes, identify which previous conclusions may no longer hold and recheck the affected behavior. Reuse evidence whose artifact, conditions, and claim remain applicable. Use broader acceptance when interactions or the complete promised outcome remain unexamined; reducing feedback cost is not a reason to omit it. Stop expanding checks once the current decision is adequately supported unless a change, failure, or unresolved concern justifies more.

Task Packet 的原 owner/next return 句补 `work already in progress and its result entry point` 即可，不另建存储格式。通用正文不出现具体命令状态工具、重启通知实现或浏览器socket修复。

## 删除、保留与避免的重复

删除旧 task-packet delegation 正文后，新增技能是唯一通用委派权威。替换原本信息/产物两分消费树，不在旧树后叠一个“更多注意事项”段。调查/实施专项只管其工作类型，V&V只管观察与判断，任务包只保留当前事实。

保留原先按能力与反馈匹配、单写者/合并边界、场景前提、局部自主修复、父整合责任等有效原则。既有 evidence-design、implementation workflow 不因本轮又加同义句。不会添加固定 verifier、强制多角色流程、每次必须运行完整套件、每次必须缩短输出、固定预算/评分表或 schema。

## 实施后真实验收方案

这里是09真实运行验收设计；本次源码编辑只完成文末所列文本和引用复核。没有新增 Corpus测试、合成委派任务、额外模型调用或 benchmark。

首先基于冻结产物与真实启动材料静态核对迁移事实：旧正文不再被消费，新技能能由相关父会话发现，专项链接实际指向随包交付的位置，既有角色workflow只装载一次。技能可发现不等于模型实际采用，报告分开记录。

之后在主线已授权的真实任务中，选择自然出现的对应机会观察，不要求为了验收制造每种场景：

| 自然机会 | 支持改进的证据 | 不足以通过/需要修正的现象 |
| --- | --- | --- |
| 同一目标已有负责人或未终结任务 | 新委派输入明确不同返回/影响边界，或先消费原任务结果 | 同一可变目标重复委派、只改文字宣称唯一写者；若旧状态不可见，先记工具缺口 |
| 大量材料/进程/记录调查 | 范围与字段围绕问题；短输出仍有原始结果入口和必要失败信息，父可据此推进 | 仅少字符却缺决定所需上下文；过滤吞退出状态；无法还原失败 |
| 已启动异步工作 | 实际完成信号进入父决策，期间能做独立工作；没有无信息增益的sleep查询链 | 定时反复读同一状态、回执当完成；通知未投递则归设施而非提示失效 |
| 分支整合或共享前提改变 | 明确哪些旧结论失效，针对受影响行为复验并完成尚未覆盖的整体验收 | 每次全量重跑却不说明新增信息，或为省成本沿用失效PASS/跳过必须旅程 |
| 子结果回传 | 父对具体命题选择合适依据并使用，既非全文重做也非盲信 | 只有“子说已完成”，另一Agent赞同替代真实依据，或开放判断被伪造为确定PASS |

观察成本按实际回显、重复操作、等待查询和返工链描述，并保留任务规模、候选/条件变化与缺失记录。token只作为辅助量，不预设可省百分比，不以更少调用认定质量提高。新一轮没有自然出现某场景时标作未观察，不为凑覆盖新造实验；必要的产品验收仍照需求完成。

上述为实施依据；当前源码实施状态见下节，打包和真实运行验收仍由09主线推进。


## 2026-09-28 实施记录

用户经主线明确授权：“沿已同意方向深入并一并在09修复”；本有界实施覆盖 `sources/svc/skills` 及维护导航，不覆盖variant/build/agents接线、打包、运行或提交。先读取 `sources/svc/AGENTS.md`，保留工作树已有改动，没有回滚历史迁移。

已新增 `skills/svc-delegation/SKILL.md` 为唯一通用委派正文，并删除 `skills/svc-task-packet/references/delegation.md`。迁移成本/能力/输入/单写者/父子责任，补实际owner与在途工作、角色内聚、按命题可判断性消费、避免启动回执当结果。保留仓库当前16.0.0版本基线，不自行发布新版本。

直接消费者已改：task-packet SKILL委派表及当前工作记录句；investigation/implementation两个SKILL入口、各自专项delegation链接；investigation workflow查询范围与完成通知段；verification repeatable-checks实际退出码/过滤/完成信号段；interpreting-results受影响行为复验末段。evidence-design、implementation workflow、五角色配置和其他既有方法未改。

维护导航同步为六技能：README、AGENTS、USER_MANUAL列出delegation独立职责，CONTRIBUTING允许短方法直接在SKILL正文。跨技能路由仍是可选引用；单独安装者需要相关方法时应将目标技能放在同一级目录，不能再宣称每项跨技能内容已包含于一个独立目录。

文本与引用复核：直接读取新增与改动段落，并使用 `rg` 核对新入口、专项链接与旧路径。当前 `skills/`及四份维护导航中，旧 `references/delegation.md`、无链接 `Apply the delegation criteria`、五技能旧表述均无匹配。相对路径从SKILL使用 `../svc-delegation/SKILL.md`，从专项reference使用 `../../svc-delegation/SKILL.md`，对应新文件；新skill的四条路由对应既有verification/task-packet入口及调查/实施专项文件。`git -C sources/svc diff --check` 无输出；由于skills目录仍是既有未跟踪迁移，diff检查不覆盖这些新增文件，正文以直接阅读复核为准。没有创建或执行内容测试、探针、模型或打包。

主线消费者迁移要求：冻结选择和运行安装加入名称 `svc-delegation`；需要委派的父会话技能目录可发现它；检查固定技能清单/锁/文档导航是否仍列五技能；旧task-packet delegation路径不再复制或强装。当前角色按需发现相关技能，**不把新正文强追加全部角色**；现有三角色workflow装配保持一份。冻结包与既有native材料不会随源码自动更新，须由09接线与恢复过程显式刷新。

剩余风险：本轮只证明文本与引用接线源的正确性，不证明父实际读取和采用，更不证明token净节省。Corpus不能修复缺失完成通知/状态归属或浏览器环境；执行层修复须保留各自验收。行为效果按本页真实任务观察表判定，不因更短输出或更少测试宣称成功。

主线补充planning既有依赖段：前提满足后重新查看可推进工作，依赖只阻塞其消费者；分支隔离不等于服务/可变数据/算力独立。依据GitHub根串行集成延后REQ6a、Sheet多lane服务事实；不增加调度器、强制并行或资源限额规则。
