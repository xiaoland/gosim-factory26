# Braid 协作与需求树方案：观察、研究和推导

2026-10-01。用户认可[方案](collaboration-requirements-plan.md)，并要求进一步审查已观察的协作缺陷、人类协作与GitHub Issue/PR研究、LLM上下文和方案之间的推导。本页用这些依据检验并改进方案；已有认可不使方案成为必须维持的结论。用户另提供 `code-philia/agentic-requirement-compiler`，已完成固定版本的独立只读调查，并据其机制及边界修订方案。两处ARC耦合修正已单独获准并完成源码及材料核对，完整协作与需求树方法随后获明确开工授权并已完成提交2d2fb87，模型采用仍待验；当前范围与文件组织归[实施方案](collaboration-requirements-plan.md)。

用户进一步明确，推导可以改变方案。调查应同样重视支持、反例与更好的解释，直接修正受影响的设计及计划，并说明改变的依据；剩余不确定性用于决定下一项有辨别力的观察。源码实施的授权边界与设计判断分别处理，不能用“尚未开工”或“原方案已认可”过滤改进。技能数量、材料分工及当前未选机制均是现有证据下的取舍；新依据可以改变它们，同时遵守用户明确的泛化与技能独立边界。

本轮回读I12人工原稿（含此前登记未覆盖的I12-2）、I11 GitHub/Sheet完整过程报告、上游根因分线和消息定位，并重新打开下列外部一手资料。没有重新逐条回放全部原生会话，没有运行模型或实验。下文区分历史报告核实的事实、用户人工观察及工程推论；外部文献不替本地证据证明因果。

## 已经观察到什么

### I12：协作资料的读者和用途没有分清

你的[I12原稿](/Users/lanzhijiang/Documents/factory26/manual-review-I12.md)所指出的不只是篇幅：原始需求、环境、技术栈、已有文档约定、子Issue结构和关联关系不断进入description/title；已消费的advisor结论和图片观察仍常驻；长comment混合多个可独立结束的问题。它们把原始资料、稳定定义、当前待办和已结束过程放在一起，接收者还要判断哪些仍有效、哪里是当前依据。

I12-2进一步指出重复@、指派后再通知、重复Closes政策、已有packet又抄要点，以及merge后展开核验记录。这里的评价标准是消息是否帮助协作者继续工作。原始证据应保存，但这不要求把每次完整核验表再发进协作上下文。你肯定的“packet入口、只更新状态、历史证据见链接”则是有用正例。

另外，root可能掌握过多局部图片细节、advisor偏向对既定方案挑错，提示我们检查分工是否真正减少父方工作、咨询是否仍有开放决定可以改变。这两项目前主要是人工观察；不能仅凭逐图读取或调用次数判定浪费。

全部登记见[M01—M17](i12-manual-review.md)。第二组尚未逐条重放当时通知路由。建议也需经过产品语义校准：同根的平级回复并不是可独立resolve的单元；重复@是否冗余取决于实际路由；有用短摘要可以省去读整份文件，不能机械删除所有复述；merge事件也不会表达全部剩余义务。

### I11：不同环节发生了不同的失真

| 具体过程 | 已支持的机制 | 导出的方案选择 |
| --- | --- | --- |
| GitHub里程碑原要求同时涉及业务Issue和PR。M5沿Issue收窄；M6a猜别组负责；M6b已知M5仅做Issue且已关闭，仍按REQ章节归属排除PR面。咨询摘要又省去这项矛盾。 | 原文已经看见，已知缺口没有成为需处理的范围决定；局部不实施被提升为整体责任结束。 | 排除本项实施时仍保留原义务，由整体负责人处理未承接部分。独立咨询要看得到挑战当前边界的事实。 |
| 最终PR23接过全套spec、平台启动和结果保存任务，随后把已有mapping视为充分，以47个叶子ID有引用停止语义回核。 | 执行责任承接了，判据能证明哪些原始要求的判断没有同样具体地承接。194/152通过与交付身份是真实的。 | 交接分别说明证明范围、实际候选结果和剩余缺口；复用有效证据，不能拿ID齐全替代语义覆盖。 |
| 根早期只展开ATOMIC，漏掉FOLDER的首页唯一入口要求；后来PR20读取父文并修了局部导航，共享入口仍未回核。 | 早期漏投影与晚期可见但未采用是两段；后段原因尚未完全确定。 | 阅读完整层级、保留适用父约束，并在整合时回到完整用户路径。改善可见性只能解释前半段。 |
| Sheet v1.3合同已发布给Issue owner等，活动PR8实现者仍交旧候选，后来读取并修订。另有Checks新增merge派生状态，旧更新路径未相应扩大。 | 发布、取得、采用不自动相等；新消费者也可能改变旧状态传播的责任。 | 联系实际消费者并说明所需采用；设计变化需考虑消费关系及证据适用范围。 |
| GitHub #308混合多个裁决、文档义务和失败处理；Sheet对回复resolve时把仍有效的设计及新待办一起折叠，随后恢复。 | 作者要结束的义务与工具讨论单元不一致。误操作和纠正已证，未证明短暂折叠造成应用损失。 | 方法按独立结束条件组织thread，CLI明确操作范围。root-only接口修复仍不能替代内容组织。 |
| 已完成模块不断镜像全局head，编辑/hide在历史runtime中触发重建和新的处理请求；另有同会话认可旧证据适用后仍因交接争议预期而重跑。 | 前者有事件反馈机制，后者不依赖reset。 | 资料归属与停止条件归方法；错误重建归runtime；已有证据采用归V&V，不能用一种修复包办。 |
| PR23将新失败文件仍标成前次成功，另有输出覆盖；也曾先宣称根Issue关闭，读回却发现OPEN。 | 执行原件、摘要、对象状态被混用。 | 摘要与同次结果对应，状态结论消费真实回执。证据保全不等于要求持续公开审计回报。 |

前三条的详细输入与选择见[上游根因深化](../iteration11/braid-context-methodology/root-causes-deepening.md)、[PR23过程](../iteration11/braid-context-methodology/final-pr23-flow.md)和[需求断点](../iteration11/github-requirement-breakpoints/causal-chains.md)；Sheet及讨论粒度见[完整lineage](../iteration11/sheet-effectiveness-analysis/full-lineage.md)；同会话复跑另见[R06](upstream-root-cause-investigation/r06.md)。本表没有把同一里程碑遗漏在多个环节出现算作多个功能缺陷。

初态还有不同偏离：同一团队同时有parent和descendant的要求被较弱示例替代；应用供应的Issue初态被猜测由外部fixture提供；逐场景恢复被每次本地run新建DB替代。它们支持区分产品供应、检查准备和外部前提，不能推出“每次启动清空数据”，也不能猜测官方初始化方式。[初态分线](../iteration11/github-requirement-breakpoints/causal-chains.md)

### 正例限制了我们应当增加多少流程

GitHub Issue8在列出剩余前提后，即使根说可以关闭，仍等PR17实际承接、合入并核实后才关。Sheet C→E区分共享实现发布、消费者接入及剩余实施义务。这说明现有机制能够闭合责任，不需要默认新增一轮ACK；要改变的是分配和返回中哪些事实被保留、怎样被采用。[GitHub正例](../iteration11/braid-context-methodology/root-causes-deepening.md)、[Sheet正例](../iteration11/sheet-effectiveness-analysis/full-lineage.md)

Sheet的透视反例改变了候选方案，advisor比较选项、指出边界，负责人采用有用部分并拒绝不符合原要求的新错误文案。PR20也有核对变更后接受已有证据、结束工作的正例。因此保留独立判断与必要反馈，不用“已经咨询”证明正确，也不强制所有事情重审、重跑。[独立判断](../iteration11/sheet-effectiveness-analysis/full-lineage.md)、[证据复用对照](upstream-root-cause-investigation/r06.md)

## 人类协作研究提供了什么

**共同理解是协作需要达到的条件。** Clark与Brennan区分呈现信息和建立足够理解，关注双方完成沟通的总工作。合适的后续行动也可提供理解证据，不必无穷确认。因此我们沿“发出什么—对方看到什么—怎样回应或行动—上游如何判断”检查交接。将此应用于责任承接是工程推论；文中的acceptance不等于批准方案或承担实施。[原文](https://web.stanford.edu/~clark/1990s/Clark%2C%20H.H.%20_%20Brennan%2C%20S.E.%20_Grounding%20in%20communication_%201991.pdf)

**协调处理的是活动间的依赖。** Malone与Crowston区分任务分解、共享资源和生产者/消费者关系；后者包括先后、传递和产物是否适合下游使用。这让我们追到关联后的实际消费，而不是将parent/link当成承接。已有稳定接口允许独立推进时，也无须等待所有上游工作结束。[原文](https://crowston.syr.edu/sites/default/files/acmcs94.pdf)

**树形与良好分解是两件事。** Parnas说明设计决定与接口如何影响独立开发，并区分层级和模块分解质量。我们借此反问：一组需求能否形成可独立推进、可采用的结果，还是分开后仍需逐步共同决定？这是从代码模块到Agent工作的类比，不是某一种Issue粒度已被论文证明最优。[原文](https://wstomv.win.tue.nl/edu/2ip30/references/criteria_for_modularization.pdf)

**追溯还要检查父要求被完整承担。** NASA的要求管理指导将来源、分配和覆盖联系起来，要求核对分解能否满足父层，变更影响上下层及接口。我们采用这种区别，在已有材料中保留必要映射，不照搬其审批组织或文档规模。[官方手册](https://www.nasa.gov/reference/6-2-requirements-management/)

这些研究帮助我们区分事实和提出解释，不是要求“多写文档”。同样，Google现代代码审阅研究是特定组织的探索性案例，不是LLM团队的控制实验；人类实践的规模不能证明Braid的净收益。[研究](https://research.google/pubs/modern-code-review-a-case-study-at-google/)

## GitHub Issue/PR模型怎样进入方案

GitHub用Issue计划、讨论和跟踪工作，以PR提出具体改动；责任、层级、依赖和订阅有不同表达，review又区分一般评论、批准及请求修改。它提供了将“问题/义务”和“候选/评价”分开的产品参照。[Issue](https://docs.github.com/en/issues/tracking-your-work-with-issues/learning-about-issues/about-issues)、[PR review](https://docs.github.com/en/pull-requests/reference/pull-request-reviews)

Google的CL指南强调问题、原因、限制与必要背景，短标题供扫描，正文服务当前及未来读者；review指南强调说明理由、让作者处理局部方案，把长期解释留到代码或设计。这支持“能直接理解的结论和必要理由，加可深入读取的入口”，而不是无解释链接或全文复制。[CL说明](https://google.github.io/eng-practices/review/developer/cl-descriptions.html)、[评论指南](https://google.github.io/eng-practices/review/reviewer/comments.html)

GitHub还明确说明批量提交review可以减少通知，已结束讨论可折叠，超出PR范围的意见可以转入关联Issue。这支持按问题和下一行动组织讨论；并不要求每个疑问都另开任务，也不把resolved视为验收通过。[评论与讨论](https://docs.github.com/en/pull-requests/how-tos/review-pull-requests/commenting-on-a-pull-request)

这里有两项适配。GitHub没有要求Issue负责人只能设计、必须另指派独立PR成员实施；这是Braid/Factory已选政策，我们在其上改进，不能伪称人类工程通则。Braid的对象能力也比GitHub窄，指派还会启动独立成员工作区；不能假设它拥有全部label、typed dependency或review状态。

由此形成当前载体职责：Issue说明还欠什么，PR说明候选怎样兑现和如何判断，讨论说明本次增量，metadata表达系统真实支持的关系和状态；项目文档、packet、原始证据分别承载稳定知识、当前推理及观察。这个安排综合了本地问题和外部实践，不是任一来源给出的唯一标准。

## LLM上下文带来哪些额外条件

人类可以扫侧栏、展开和跳转；Braid必须构造本轮输入。当前Issue不自动展开祖先正文，PR只自动展开直接关联且OPEN的Issue正文；存在关系不等于全部相关讨论被输入。原生历史中的旧文字也不会因后来hide而被追溯清除。重建、普通通知和恢复是不同路径。[能力核对](../research/braid-collaboration-method/report.md)、[当前更新规则](context-update-policy.md)

因而要分别看：**资料存在、能按入口取得、本轮实际输入、Agent正确采用**。里程碑链主要落在最后一步；atomic-only漏父文发生在输入选择；开发侧AGENTS被自动追加到参赛clone则是生产者边界。这些问题需要不同修正，不能统称“没上下文”。

Lost in the Middle在其研究模型和任务中发现信息位置影响使用；SWE-agent显示面向Agent的导航、编辑等接口会影响行为和表现。它们支持认真设计工作集和读取接口，不能证明当前模型容量上限，也不能据此判定I11某次错误由长上下文造成。[长上下文研究](https://arxiv.org/abs/2307.03172)、[Agent接口研究](https://arxiv.org/abs/2405.15793)

本地反例是Sheet约167,672字符的一次输入：Agent既正确识别已有评论、停止多余催问，也重新定位旧thread、纠正状态。长度可测，语义采用仍要逐项核对。过度缩短可能删除决定性的例外，所有原件常驻则增加寻找当前依据的工作。[Sheet记录](../iteration11/sheet-effectiveness-analysis/full-lineage.md)

方案因此采用当前决定所需的工作集与可按需读取的完整材料。默认入口呈现目标、变化、未决及必要依据，深层文档、历史和原件可寻址。packet是推理与恢复材料，description是协作中的当前承诺，二者不镜像；技能以独立文件提供方法和理由，不反复内联到system/profile。

## Agentic Requirement Compiler 带来的补充

2026-10-01核对官方仓库main的提交[`a119f22`](https://github.com/code-philia/agentic-requirement-compiler/commit/a119f22fc09391ec5924b44217c0373a02724cca)。本轮只读源码，没有运行其脚本、测试或模型。[调查记录](../../runs/iteration13/requirement-compiler-research-20261001/research.md)保留定位与边界。以下所称ARC compiler是该生成系统，ARC-Bench是评测与需求来源，两者职责不同。

它将已经结构化的requirements.yaml作为输入，保留节点正文、场景、父子和dependencies，并围绕接口、测试、执行和Git checkpoint形成可恢复过程。这个参考的价值是把原要求与后续工程产物实际接起来；README所述愿景也需要逐项核对实现。[输入与追溯模型](https://github.com/code-philia/agentic-requirement-compiler/blob/a119f22fc09391ec5924b44217c0373a02724cca/src/arcbench_agent_runtime/traceability.py#L159)

| 已实现机制 | 对当前方案的启发与边界 |
| --- | --- |
| 编排顺序是父DESIGN、子节点、父IMPLEMENT；显式dependencies不决定拓扑调度。 | 需求层级提供来源和组织关系，工作依赖仍须解释。父方可以先给出足够稳定的共同决定，再让局部独立推进；无需把全部局部实现细节提前设计完。[编排](https://github.com/code-philia/agentic-requirement-compiler/blob/a119f22fc09391ec5924b44217c0373a02724cca/src/core/workflow.py#L864) |
| 一个接口可关联多个req_id，specification可进入下阶段，父/依赖接口记录可读取。 | 将真正共享的约束放进可消费合同，能支持多个需求共同兑现。当前叶子默认上下文没有祖先正文；非叶无视觉参考可跳过DESIGN、IMPLEMENT也直接结束，因而父层业务义务不能依赖流程自动保全。[接口登记](https://github.com/code-philia/agentic-requirement-compiler/blob/a119f22fc09391ec5924b44217c0373a02724cca/src/core/phases.py#L694)、[上下文](https://github.com/code-philia/agentic-requirement-compiler/blob/a119f22fc09391ec5924b44217c0373a02724cca/src/agents/context/pipeline.py#L388) |
| 系统执行已登记测试、记录原始输出，并根据退出码推进TDD；接口、文件、测试和Git checkpoint有追溯入口。 | 可执行判据与真实结果比口头完成声明更有约束力；来源映射、判据充分性和实际执行仍是分别需要判断的事情。普通生成链未保存scenario_id，也没有逐项义务的负责人账。[执行](https://github.com/code-philia/agentic-requirement-compiler/blob/a119f22fc09391ec5924b44217c0373a02724cca/src/core/phases.py#L420)、[测试登记](https://github.com/code-philia/agentic-requirement-compiler/blob/a119f22fc09391ec5924b44217c0373a02724cca/src/core/phases.py#L791) |
| 新增/修改节点使本节点、祖先及直接反向显式依赖进入有限重编排。 | 变更要追到消费者。当前计算不把父正文变化传播给子孙，也不递归扩展反向依赖；实际共享状态、接口及旧证据的影响需要补充语义判断。[影响计算](https://github.com/code-philia/agentic-requirement-compiler/blob/a119f22fc09391ec5924b44217c0373a02724cca/src/core/workflow.py#L579) |

其终态门槛给出了一个有辨别力的静态反例：零测试manifest可以接受，IMPLEMENT跳过后仍可进入PASSED；有测试时允许只执行当前层的文件子集，却依据该层最后一次输出给全部test_id写入同一个passed值。源码支持这些路径，不等于已证明某次应用因此错误。它们说明自动化执行与结构化追溯仍不能自然保证父义务完整或每条证据精确，正好对应PR23中“判据范围”与“执行事实”需要分开的判断。[跳过路径](https://github.com/code-philia/agentic-requirement-compiler/blob/a119f22fc09391ec5924b44217c0373a02724cca/src/core/phases.py#L396)、[状态回写](https://github.com/code-philia/agentic-requirement-compiler/blob/a119f22fc09391ec5924b44217c0373a02724cca/src/core/phases.py#L629)

因此本轮补强的是四种关系的区别：**需求树说明承诺及来源，工作依赖说明谁消费什么，责任关系说明谁处理剩余义务，证据关系说明哪些观察支持哪些承诺**。在现有项目文档、Issue/PR及packet中表达必要关系即可。共享接口用于跨需求约束，普通局部要求直接落实到实现与判据；父层或合同变化时回查适用子路径和真实消费者。当前落点仍是两项独立技能和既有材料入口，尚无依据引入compiler runtime、逐节点调度或全量状态表。

### 用户补充分析与主线判断

用户随后提供ARC的五方向分析，并明确“分析不是我的态度和建议”。这里将其作为研究材料；以下取舍是主线判断，不登记成用户偏好或开工授权。补充核对沿用同一固定提交和只读边界，事实与精确定位归同一[调查记录](../../runs/iteration13/requirement-compiler-research-20261001/research.md)。

| 补充分析中的事实 | 静态核对结果 |
| --- | --- |
| 已有数据初始化与UI/API/FUNC/DB合同 | 类型有代码校验；确定性、幂等初始化并经正常应用路径访问属于默认验收文字，未证明Agent实际遵守。[上下文政策](https://github.com/code-philia/agentic-requirement-compiler/blob/a119f22fc09391ec5924b44217c0373a02724cca/src/agents/context/pipeline.py#L155) |
| 接口卡片可能挤掉必要依赖 | 表按interface_id字典序保存，卡片未按相关性优先排序，达到默认30张即停止；按req_id或interface_id补取完整记录的工具仍可使用。这是初始可见性缺口，不能直接推成材料彻底不可得。[卡片选择](https://github.com/code-philia/agentic-requirement-compiler/blob/a119f22fc09391ec5924b44217c0373a02724cca/src/agents/context/pipeline.py#L388)、[完整读取](https://github.com/code-philia/agentic-requirement-compiler/blob/a119f22fc09391ec5924b44217c0373a02724cca/src/agents/tools/traceability.py#L20) |
| 后层修改后仍汇总前层旧PASS | 属实；不会自动重跑先前层。这与上文“执行文件子集却给整层登记PASS”是不同边界，前者涉及候选变化，后者涉及同次执行范围。[循环与汇总](https://github.com/code-philia/agentic-requirement-compiler/blob/a119f22fc09391ec5924b44217c0373a02724cca/src/core/phases.py#L562) |
| 独立视觉分析及缓存 | 机制已实现；保留结构性文字、排除实例数据是提示词政策。缓存身份含路径、mtime_ns、size和prompt版本，未含视觉模型或请求参数；没有实际错误复用事故的证据。[视觉与缓存](https://github.com/code-philia/agentic-requirement-compiler/blob/a119f22fc09391ec5924b44217c0373a02724cca/src/core/visual_analysis.py#L197) |
| 按阶段选技能、失败后选repair | 阶段和auth关键词选择属实；repair只判断失败摘要非空，不能称已认证“真实失败”。其文案写每层10次，运行常量为5次；文件开放也不证明读取和采用。[选择](https://github.com/code-philia/agentic-requirement-compiler/blob/a119f22fc09391ec5924b44217c0373a02724cca/src/agents/skills/selection.py#L28)、[技能文案](https://github.com/code-philia/agentic-requirement-compiler/blob/a119f22fc09391ec5924b44217c0373a02724cca/src/skills/tdd-test-failure-repair/SKILL.md#L21) |
| 阶段工具限制确实执行 | middleware在构造时注册，限制重复读写、测试生成的验证及非测试资产写入；允许分页和失败后解锁。设计阶段是首次写入路径数量与单次行数限制，不能保证只生成骨架。未运行调用复现。[注册](https://github.com/code-philia/agentic-requirement-compiler/blob/a119f22fc09391ec5924b44217c0373a02724cca/src/agents/runtime/factory.py#L117)、[执行边界](https://github.com/code-philia/agentic-requirement-compiler/blob/a119f22fc09391ec5924b44217c0373a02724cca/src/agents/runtime/stage_discipline.py#L55) |

**跨层行为契约值得补强，但先判断初态是谁的义务。** 初始化、跨页面状态和可见交互是理解完整用户操作的三个有用视角，可帮助发现共享假设。产品承诺正常启动即存在的数据必须由应用提供；用户先前创建的账户或购物车，可以由正常产品流程建立；只为检查后续行为准备的数据也可能合法。仅凭GIVEN写着“已存在”，无法将这三者合成统一的自动seed要求。当前SVC已保留这个区别；采用ARC例子时继续保留它。[判据设计](../../sources/svc/skills/svc-verification/references/check-design.md)、[可重复条件](../../sources/svc/skills/svc-verification/references/repeatable-checks.md)

共同合同只需解释跨成员决定：哪个状态是权威来源、消费者何时读取或失效、初态由谁提供、操作怎样产生可观察结果。具体存储、客户端库和局部实现可由接收者选择。认证一致性可以作为贯穿UI/API/持久化的实例；“三类合同”不必成为每项工作都填写的JSON或三份前置文档。现有Better Auth技能提供库选型与版本入口，不等于已经自动解决了通用跨页面状态问题。[现有认证入口](../../materials/skills/better-auth-best-practices/SKILL.md)

**依赖决定什么可以开始，比依赖排序本身更关键。** 需求字段可能表达语义关联、输入或实施前提；稳定合同可支持消费者先行实现，真实数据及服务则可能是整合验证的前提。先辨别关系的含义，再决定并行、等待或合并工作。当前Braid由负责人分批指派，已有机制可表达这些选择；现有证据尚未要求增加拓扑调度器。读取材料时优先保留本次决定必需的约束与入口，按需取得完整原件；不会因某项被标记为dependency就将所有依赖全文永久装入上下文。

**最终候选需要适用证据，回归范围由变化决定。** 后续实现可能使早期结果失效，应检查共享代码、数据、环境及判据变化，复查受影响路径，并观察尚未覆盖的完整用户结果。当前I13整合PR及SVC已有这条方法；增加固定的全量重跑或把所有需求强制走Unit/Integration/E2E会重复现有工作，并不自动填补语义缺口。没有测试和没有验收证据也需区分：其他可靠观察可能足以支持某项判断，而零观察不能被计为已验证。[证据适用性](../../sources/svc/skills/svc-verification/references/interpreting-results.md)、[快反馈与完整结果](../../sources/svc/skills/svc-verification/references/feedback-and-evolution.md)

分析中按“能否看到公开测试”分支讨论的是一般策略。本项目既定规则是生成阶段仅用允许需求设计自身检查，冻结后独立使用官方评测；外部验收材料不进入仍在生成的Agent。自生成检查如有错误，可据需求修正其观察或判据，并保留理由；外部判据的权威与修改权限单独判断。

**视觉产物应可复用也可复查。** I13已独立委派vision，保留图片来源、可见结构与未知；ARC对结构性文字和展示样例数据的区别可补充需求阅读方法。参考图中的具体数据是否有约束力仍由题目语义决定，不能统一忽略。视觉摘要不能取代原图；将来做模型对照时需要记录图像、模型、提示词和参数的身份。当前I13未使用ARC的视觉缓存，不由其缓存缺口新增自己的缓存系统。

**新增技能和硬限制都要看独有作用。** `tdd-test-failure-repair`中所述的证据驱动诊断、回看需求、区分产品/检查/环境及改变假设，内容已大部分由本轮SVC V&V承担；实际采用仍待观察。认证一致性更适合作为相关需求下的领域材料候选，先检查其相对现有方法的独有内容。技能发现保持名称、description和独立路径；外部方案中的阶段工具拒绝和固定重试预算不自动成为I13政策，既有全角色工具开放及禁止内联技能的决定保持有效。

## 当前方案的取舍及修订

| 选择 | 依据与取舍 |
| --- | --- |
| `braid-collaboration`与`arc-bench`分开 | 通用协作与ARC输入/交付的职责和读取时机不同，又在分工/交回处相接。ARC技能原拟名为arc-requirements；用户明确泛化边界后改名并承接交付契约，仍为两份独立材料。 |
| 完整阅读、按成果与依赖分工、保留父层与跨枝义务 | 回应漏父文、跨对象排除与共享状态链。进一步撤回“默认沿内聚子树分域”的优先顺序：需求树提供来源和候选切分，语义耦合与可消费结果决定工作边界；跨枝工作不需要作为例外论证，根也不需预做所有局部调查。 |
| 未承接义务和实际消费进入交接 | 由失败链及同环境正例支持。接手可由正确行动证明，caller无需先列尽局部执行细节。 |
| 各载体分工，评论面向下一行动 | 回应I12两组观察与多处状态镜像；兼顾当前可理解性和历史可追溯，保存证据不转化为持续审计汇报。 |
| thread与结束条件一致，维护可停止 | 由误折叠、事件反馈和停止正例支持；产品接口修复与内容组织各自承担责任。 |
| 交回区分证明范围、执行事实和剩余要求 | 回应PR23与记录错配。详细方法继续归SVC V&V，不再增加一套重复验收流程。 |

新技能的正文应给出判断方法及理由，而不是只有触发词或禁止清单。Braid保留通用身份与操作契约，Factory保留配方政策，SVC保留通用方法；迁入新技能的现有方法同步从profile/根任务退出。通用案例解释决策关系，历史题目答案留在开发侧研究。

用户随后明确，目标是泛化coding agent harness，ARC特定适配只能进入Agent Skill与root Issue description。该要求将上面的“不引入compiler运行时”进一步变成稳定职责边界：从ARC学到的一般协作与证据判断，须能在普通需求下解释；ARC的字段、输入文件约定及平台交付契约集中在ARC技能，root只给本次目标、参数和读取入口。当前profile内已有的固定ARC安装/启动条件也须迁出，而不是只限制今后新增内容。既有外围调用与交付协议保持原职责。具体迁移和真实材料核对归[方案](collaboration-requirements-plan.md#泛化边界及现有内容的迁移)。

目前可以支持的是有针对性的材料与接口修正，尚不能证明持续采用、总成本下降或评分提高。后续应看责任是否保全、真实消费者是否采用、有效证据是否复用、当前入口能否支持继续工作；字符数、评论数、ID数量与全部closed只提供辅助事实。
