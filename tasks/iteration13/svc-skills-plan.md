# I13：SVC Agent Skills 优化方案

2026-09-30。用户已复核本方案并授权子Agent开工；本批SVC正文、退出入口和材料核对已完成，见[实施记录](svc-skills-implementation.md)。子 Agent 批次已由独立 GPT-6.1-Sol / extra-high 完成，见[该批实施记录](subagents-implementation.md)。本页保存已批准的 SVC 范围；task-packet 的详细依据沿用[既有复审](task-packet-review.md)，不另建竞争说明。方法在真实工作中的收益仍待获授权证据，documentation/task-packet强制入口与profile整体联查仍属于后续批次。

## 来源与判断修正

用户本轮指出 documentation 是窄化最严重的一项，要求回到原始 Corpus；sub-agents 要以悖论讨论为依据，具体角色内容归角色提示词；documentation、task-packet 必须应用，其接线与后续 profile instruction 优化联查。首版“补入口和少量例子”的范围已撤回，下列方案替代它。

已回读原始完整仓库 `/Users/lanzhijiang/Development/svc`，HEAD 为 `80996c115ba635c6b85db47d0b14663293b95f12`；本次读取的 specs、templates、Corpus 总入口及 task-packet 入口没有工作区改动。Factory `sources/svc` 的历史 `9592494` 也保留这些 specs。

| 来源 | 实际读取及用途 |
| --- | --- |
| [原始 specs 总入口](/Users/lanzhijiang/Development/svc/corpus/specs/index.md) | 知识归属、文档成立条件、可执行约束优先及可选扩展。 |
| [PRD](/Users/lanzhijiang/Development/svc/corpus/specs/prd/index.md)、[Product TDD](/Users/lanzhijiang/Development/svc/corpus/specs/product-tdd/index.md)、[Unit TDD](/Users/lanzhijiang/Development/svc/corpus/specs/unit-tdd/index.md)、[Deployment](/Users/lanzhijiang/Development/svc/corpus/specs/deployment/index.md) | 产品承诺与理由、跨单元契约、内部设计与局部指引、运行及恢复的职责。 |
| [Alignment](/Users/lanzhijiang/Development/svc/corpus/specs/alignment/index.md)、[Multi-repo](/Users/lanzhijiang/Development/svc/corpus/specs/multi-repo/index.md)，五份配套模板及 root/local AGENTS 模板 | 具体协调歧义与跨仓新鲜度问题；区分方法价值、可选形式和旧环境政策。 |
| [Corpus 入口](/Users/lanzhijiang/Development/svc/corpus/index.md)、[task-packet 入口](/Users/lanzhijiang/Development/svc/corpus/task-packet/index.md)；原仓库 design/34、design/19 相关段落 | 非简单任务的持久工作状态；先维护知识归属，再更新受影响任务状态，避免任务视图成为第二份项目定义。 |
| [Factory 原裁剪记录](../svc-corpus-review/agent-first-review.md) | 曾以“一次性生成项目不需要长期归属系统”为由移除整个 specs；SVC `b5a0fb8` 的变更确实删除了这组材料。 |
| [Sub-agent 悖论来源整理](../factory-subagents/cells/subagent-paradox-source.md) | 用户认可的低成本判断方向、生成与判断的不对称、局部反馈、适用条件和开放判断；不把末条 assistant 的框架提案当成用户逐项批准。 |

首版只看现行技能，低估了 documentation 丢失的职责。共享契约维护仍有价值，但它只是项目知识方法的一部分。“一次性生成”不足以排除其它需要：同一次任务中的多个组件、消费者和最终运行也依赖稳定定义。独立 advisor 回读原始材料后也撤回了先前“主体足够、只补入口”的判断。

## Documentation：让项目理解可以持续使用

建议 description：

> Build and maintain durable project understanding: product purpose and behavior, technical responsibilities and contracts, internal design, and operation. Use throughout development to locate the current basis, decide where new knowledge belongs, and keep changed decisions usable by their consumers.

元理论先解释：代码与配置表达和约束实际实现，却未必保存为什么作此选择、承诺的边界、跨组件如何协同以及异常时怎样恢复。只靠对话或当前任务记录，下一位消费者须重新解释，旧结论也容易脱离适用条件继续使用。项目文档保存值得持续复用的含义与理由，连接原要求、当前决定、实现及观察，使后来者能够继续判断和修改。

文档同样会漂移，所以能由代码、配置、类型、schema 或自动化直接维持的事实优先留在那里；文字记录难以廉价恢复的含义。一个事实有当前定义位置，消费者可定位并引用；新信息改变定义时更新相关消费者，而非不断追加另一份说法。是否独立成文取决于内容、读者、变化节奏及重新取得知识的成本。

恢复以下完整内容，每个分支都包含用途、成立条件、实际维护方式及相邻职责的区别：

| 知识职责 | 需要恢复的操作含义与理由 |
| --- | --- |
| 产品目的、承诺与业务语言（PRD） | 保存为谁解决什么问题、为何值得解决、可观察流程、规则、范围及成功判断。技术选择从这些承诺展开，不能由当前实现或绿色检查反推产品要求。初次开发就需要最小可用依据；沿用原需求并标明项目解释，不建立竞争需求。 |
| 跨单元技术设计（Product TDD） | 当多个独立职责单元须共同理解权威状态、拓扑、接口、生命周期、顺序、兼容及失败语义时，保存协同方式与取舍。字段可由 schema 维持，跨边界含义仍可能需要解释；私有细节无需升级为共同契约。 |
| 单元内部设计（Unit TDD） | 保存昂贵、需跨重构存续的内部不变量及选择理由，包括状态、存储、时序或技术约束。逻辑单元不等于目录；是否影响其他单元决定归属，文件大小或是否跨仓不决定它。 |
| 局部指引与开发入口 | root AGENTS/CONTRIBUTING 帮助找到工作入口；local AGENTS 处理物理子树中反复出现、就近提醒能预防的问题。说明范围、原因和有效反馈，先诊断再决定是否需要长期指引，不复制根政策或架构。 |
| 部署与运行知识 | 保存实际需要的打包、配置、数据位置、迁移、可观测性、发布、缓解、回滚及恢复路径。解释何种观察支持何种动作、恢复后怎样判断；故障原件留在任务材料，持续有用的方法归运行文档。 |
| 协作对象与操作含义（Alignment，可选） | 反复误解对象、地址、边界、操作效果或适用状态，且普通标识与说明仍不足时，建立稳定指代及操作含义。用语义标识和当前到目标的变化表达问题，将操作与可观察效果相连；不另立产品或权限来源。 |

用户开工时补充赛题不存在多repo，建议裁剪“跨仓共同依据”。本批采纳：不恢复或分发Multi-repo专门内容、模板及导航；原始完整Corpus保留不动。多组件的共享定义、变更采用和版本对应仍有用途，保留在一般文档方法中，不将它们误作跨仓内容删除。

技能入口承担元理论、归属判断和日常使用；不同场景的细节放入本技能 references，按问题导航。恢复解释与可用操作内容，不只恢复目录名称。PRD/Product TDD 等名称表达职责，已有 README、设计文档或接口定义可以承担它们。原 Corpus 本就明确它们不是必建的文档梯子。

维护覆盖开始工作时寻找依据、决定形成时保留假设和理由、约定形成后更新原定义、变化时处理消费者、收尾时检查仍滞留在临时材料里的长期知识。整理在工作中持续发生，不都推迟到最后写报告。需求、方案、约定、实现及实际观察的性质保持可辨；“权威位置”也不消除与原要求或现实的矛盾。

保留当前共享规则、优先级及消费者采用的有效内容，包括工作树中已有的未提交修订。变更说明差异、对应版本和需调整的工作；发布、通知、实际采用是不同事实。编辑器/导入器例子继续说明这一分支，再以内部状态不变量和运行恢复短情境说明其它知识归属，避免全技能再次只围绕共享合同展开。

模板按真实用途保留为可选起点；不原样恢复其中过时路径、逐次人类批准或固定提交政策。具体项目的授权和实验政策仍由项目约定决定。

## Sub-agents：降低执行和采用成果的总负担

建议 description：

> Decide when and how to delegate work so its result advances the task without requiring the parent to repeat it. Shape useful assignments, match capability and feedback, and judge returns using observations or arguments whose scope and limits are understood.

从原始悖论开始：调用方需要他者完成自己无暇全部处理的工作，却不能仅凭对方自信就采用；完整重做又可能吃掉委派收益；再加一个相似模型复核，仍可能递归转移同一个信任问题。方法解释如何塑造有独立用途、能以较低成本判断和采用的成果，同时保留无法消除的不确定性。

收益包括并行、不同能力与推理路线、隔离大量原始材料，以及 child 利用反馈独立收敛。总成本包含背景传递、等待、纠正、理解、整合、误收后果，也包含过度拒绝与重复检查造成的返工。明确的查询可直接用现成工具；证据路径复杂或需多轮局部收敛时，child 才可能减少调用方负担。这是选择依据，不是量化评分表或仅允许小任务的限制。

先看什么返回能改变调用方的决定或成果、什么观察足以采用，再决定工作边界、能力和交接材料。调用方提供足以明确问题、用途和必要边界的背景、已有材料及在途工作入口，不须先查齐全部局部初态、逐文件划分或设计执行步骤，否则准备成本会吃掉委派价值。child 自主补足局部调查、设计、实现细节与协调，核实结论和操作实际需要的来源身份、初态与消费者；局部可恢复问题留在 child。只有无法在边界内收敛的缺口或会改变整体目标、权限、重大取舍的决定才交回整体负责人。效果和整合边界使独立工作成立，不必固化为输入输出表。此段同步用户本轮对 executor 方案的校正，通用方法仍不预选原生并发政策。

低成本判断有不同成立条件，需要在本技能中讲清，不能用一条外部 V&V 链接代替：

| 结论性质 | 可用机制与限制 |
| --- | --- |
| 可精确查询或受既有约束检查 | 短 SQL、结构查询、schema 或既有检查压缩大量事实。调用方理解命题、查询含义、输入范围和实际结果；空结果可能只是漏查，检查覆盖什么才能支持什么。 |
| 没有完整 oracle，但有可检查关系 | 用不变量、差分、往返或兼容关系缩小未知。关系成立不证明全部需求；比较对象及前提也可能有共同错误。 |
| 全量观察成本过高 | 按问题选择抽样或逐步增加证据，说明覆盖与推断依据。样本成功不自动保证全量，新增投入服务仍会改变决定的未知。 |
| 设计、解释或偏好等开放判断 | 用假设、理由、备选解释、反例及实际反馈帮助决定。无廉价客观判定器仍可委派，保留判断性质，让后续承诺与不确定性相称。 |

child 自报“已经执行”与取得对应实际输入、候选及环境的观察不同；角色身份或另一 Agent 赞同也不是独立证据。调用方理解小检查或论据与当前主张的关系，复用有效结果，对具体矛盾补证，决定采用、返修或保留未知。对象或前提改变时判断哪些结果仍适用，不全部机械重跑，也不拿旧观察证明新候选。

失败给出具体反例与可行动原因，使 child 能在原范围内继续修正，避免调用方中转每次操作。不可恢复的信息、权限或范围缺口才回整体负责人。启动回执不是可用成果；按可变目标协调重叠作用，恢复时先查原工作和产物，防止失联被误判为停止并重复写入。

用两条贯穿情境说明：关系不明的数据问题，经调查形成短查询、实际结果和边界，调用方据此选择修复方向；没有唯一答案的交互方案，经备选解释、反例和使用观察改变选择。各自讲清调用方省去什么工作、实际依据及未支持部分。其它机制用短例辨别，不把来源十二项变成必经流水线。

本技能不含 explorer、advisor、executor 的职责、触发条件、专属步骤或返回格式，不设独立咨询豁免经济判断的角色政策，也不把这些内容换成匿名角色继续保留。具体角色契约收敛到其 description/body，Harness 强制分工归对应入口。通用能力匹配和开放判断仍属于本方法。

保持自包含，不链接其它技能或方法。来源中独立控制面、固定 certificate/coverage/effects schema 和每项效果闸门只是后段 assistant 的更强提案，不恢复为通用架构。原生 cwd 单 writer 问题仍由[executor 讨论](executor-followup.md)决定，本批不预选并发实现。

## Task-packet：让进行中的判断可取用

采用[已有具体草案](task-packet-review.md#具体结构与入口草案待复核)：入口讲清外置工作记忆的目的，用一个任务贯穿“取得材料 → 形成解释 → 取得区分性观察 → 采用结果 → 修订当前判断”。对话按时间追加，当前问题却按仍有效的依据组织；入口保留当前综合，原件与详细材料通过路径按需读取，二者各有用途。

先给短入口加已有材料的最小起点，再按实际检索、所有权与依赖需要介绍 planning/information。结果改变路线时更新当前解释与下一步；无关变化不要求逐值同步。旧解释退出当前行动依据，同时保留能说明为何改变判断的历史来源。

删除 `references/growth.md` 及其入口，不将它改名后整章迁移。保留现有按需组织能力与可选模板，只同步被新正文实际影响的部分。详细拓扑继续留在 planning 深处，不设首次建包必须通过的形状预检。通讯中的问题、决定和材料入口不代替任务工作材料，成熟共享知识仍归项目文档。

## 强制应用与 profile instruction 联查

用户明确 documentation、task-packet 机制需要强制应用。建议后续 profile 批明确：负责人开始承担任务时读取两技能入口，建立或接续项目依据和任务材料；详细 references 根据当前问题展开，已有有效材料及已读知识可接续。关键结果改变理解、决定或路线时维护相关内容。强制应用不要求每轮读全套技能、建立全套文档、为一次短查询另建 packet，也不允许内联正文。

当前 I13 两份父 profile 已要求根负责人建立或接续项目文档、各 Issue 负责人建立或接续 packet、关联 PR 接续同一 packet；又写有“文档组织与任务状态维护分别按需读取”及“技能提供可选方法”。这可能混淆必需机制与可选手段，是直接可见的入口歧义，尚不能证明它导致了某次未采用。

与 M11 去重一起核对三层职责：Braid 提供通用任务与协作协议，Factory profile 表达该运行必须遵循的知识与任务状态约定，技能解释方法、理由和细节。同时检查 Issue/PR 生命周期、child 如何接续相关材料，以及可选措辞是否削弱义务；不把父 profile 重新注入 child，也不让每个 child 默认另建一套项目文档和 packet。当前只记录关联，整体入口待后续提示词批共同设计。

## 退出技能的实际范围

I13 不打包、不启用、不引用 `svc-implementation`、`svc-investigation` 和 `svc-design`，三份技能源码保留。清理不只针对目录清单：现有 I13 的 build/run 选择、父 profile 指引，以及保留四技能的正文和 references 都存在引用；还包括 task-packet information 中没有 Markdown 链接的文字引用。子角色本批已由并行实现移除这三项，不重复改其职责正文。

改动文件面：

- SVC 的 documentation SKILL.md 及按上述职责恢复的内部 references、必要可选模板；sub-agents SKILL.md；task-packet 的 SKILL.md、information/planning、growth 删除及确实受影响的模板入口。
- SVC verification 的 `check-design.md` 与 `feedback-and-evolution.md`：移除外部跳转，保留本段已有的判断含义；不重写已完成的方法。
- Factory I13 的 `build.py`、`run.py`、两份父 `instructions.md`：删除三技能选择和读取要求，保留本轮其余职责；不把退出内容改成内联提示。
- 受影响的材料导航与本批实施记录。SVC 七技能源码布局仍成立，不将 Factory 的四技能选择改成 SVC 全局删除。

documentation/task-packet 强制应用、整体 profile instruction 和 Braid 系统提示的分层去重另批共同处理；本批清理旧技能入口时保留现有文档与任务状态义务。本批只清除与技能选择直接冲突的入口，不顺便改写协作流程、引入新技能、修改 CLI 或启动实验。

## 实施准备与反馈

本轮重新读取原始来源并取得独立 advisor 判断，已撤回首版范围和先前过窄的判断；用户现已明确：“我阅读了方案，没问题，你可以安排subagent开工。btw，可以考虑裁剪掉‘跨仓共同依据’的内容，因为我们的赛题不存在多repo。”本批按该范围实施并裁剪Multi-repo内容，模型沿用用户指定的GPT-6.1-Sol / extra-high。修改前保留 SVC 当前差异和来源身份，特别区分已有 documentation 改动；子角色批次已完成并释放 I13 文件面，本批接续该文件面。

直接复核自然语言、语义依赖和实际分发材料：documentation 能否覆盖各知识职责、解释理由并指导实际维护，sub-agents 能否解释降低消费成本的机制及适用限制、保持自包含且没有具体角色内容，growth 与三项退出入口是否真正消失，保留材料是否仍可达。使用现有材料构建和 prepare-only 取得真实包/会话入口；不添加内容测试、探针、自检或模型调用。所有技能继续以独立文件按需读取，主/子提示词都不内联正文。

材料完整与方法有效分开报告。后续获授权真实工作才观察：是否在决定形成前调用适合的方法，child 是否独立收敛且结果被采用，共享规则是否影响消费者，以及 packet 是否保存并改变当前判断。读过技能、产生文件或增加调用次数均不足以证明这些收益。
