# I13 子Agent：简化角色并开放原生能力

2026-09-30。用户已审查并修订本页，随后明确授权开工：“你可以按这个方案开工『I13-sub-agent简化与改进』了；注意你一直都可以自由git commit。”本批源码与文档已完成，编译及真实prepare-only材料核对通过，覆盖已复核角色、原生工具/深度、材料加载及视觉模型；真实委派和视觉API行为仍未验。executor原生写入说明已随后按[独立实施记录](executor-followup.md)修正并提交84344b4；SVC批次也已完成。其它组工具接线和实验不在本批。实现与实际反馈归[实施记录](subagents-implementation.md)。

## 本批改变什么

角色描述用于让调用方选择专长，角色正文说明用途；工具能力保持完整。child从独立任务开始，所需事实由本次委派和按需读取取得。角色文件、生成时追加内容和原生扩展注入共同决定实际输入，不能只修改其中一个入口。

| 当前实际入口 | 观察 | 本批方案 |
| --- | --- | --- |
| 两个profile下的五份角色Markdown | 两套正文相同；advisor/explorer只有读取与bash，browser-operator只有read/bash，vision只有read，全部缺少subagent能力。 | 两套角色同步简化，完整开放原生工具与子Agent工具；不新增角色注册或生成框架。 |
| `run.py::native_files` | 给非vision角色追加RUN_CONDITIONS和后台约定；给explorer/executor/advisor内联workflow，给browser-operator内联agent-browser全文。 | 停止这些自动正文追加，保留必要工具扩展和按需技能入口。 |
| 父Braid profile的advisor段 | 强制要求反例、替代方案及缺失事实，并规定结果采用动作，可能抵消child正文简化。 | 本批只精简这段咨询内容要求；保留此前已选定的重要决定前咨询时机，整体Braid方法留下一批。 |
| pi-subagents自动child边界说明 | 扩展会前置角色文件之外的指令，包含只有任务明确要求才能再委派等限制；没有配置覆盖入口。 | 窄改既有fanout边界文案；真实深度限制由原生运行配置承担，完成/结果管线保留。 |
| 视觉模型 | vision和browser-operator在两profile下都使用deepseek-v4-flash-vision-exp。 | 两个角色共同替换为glm-5.3-flash；保留独立visual端点/凭据接线能力。 |

“不可以做什么不超过一句，或者占比不超过5%”用于本批可控的角色及自动追加材料。草案采用正面职责表达，不用改写句式掩盖相同的限制，也不以文案比例证明实际工作收益。

## 角色草案

以下是给模型的实际短文案草案，不是进一步扩写成SOP的提纲。五个角色均保持原生fresh默认、独立任务上下文和完整工具；专长不形成角色级只读或文件访问范围。

| 角色 | 给调用方的description | child正文 |
| --- | --- | --- |
| advisor | 参与问题定义、方案形成和重要取舍，提供独立判断；在反复失败或新证据动摇原方案时帮助重新判断。调用时可附背景、问题和资料列表。 | 就委派给你的问题提供独立判断与建议。 |
| executor | 承担目标和影响范围明确、能够通过反馈独立收敛的工程任务，包括实现、修复和改造；自主完成必要的调查、局部设计、修改与验证，交付可整合的实际成果。关键输入或决定缺失时可请求调用方补充。 | 围绕委派目标独立推进，按需要补足信息与局部设计，利用实际反馈修正实现并交回成果。接续当前工作区并保留其他协作者的修改；影响路线的输入或决定缺失时，可先向调用方请求补充，再继续相关工作。 |
| browser-operator | 操作网页，完成任务、复现问题或取得观察。 | 操作网页以完成委派任务、复现问题或取得观察。使用agent-browser技能中的工具说明，按任务选择页面、可访问性树、截图、console或网络信息。 |
| vision | 解读需求参考图、截图及其它图片。 | 解读与委派问题相关的图片。结合材料语境说明可见内容、结构关系和需要澄清之处，保留来源入口。 |

executor原草案“完成局部实现或修复”只描述动作，没有说明值得委派的工作单元。其边界应是一段目标和效果范围清楚、内部包含必要调查与反馈修正的工程工作，成果可以直接整合。“局部”限定责任和影响，并不限定为小改动、少量文件或一次工具调用。

委派价值在于executor能够独立处理局部问题和可恢复失败，调用方接收实际成果与关键未决事项，而不必持续中转工具、重新实施或重走全部调试。文件多、任务长或动作名本身不足以证明委派有收益。description使调用方看见这种闭环能力，正文不变成固定实施步骤或必填输入输出协议；原始SVC方法仍按需读取，不内联。

这一修订与共享工作区的并发写策略是两项问题。前者改善拟定角色的用途表达，后者已按executor-followup中的用户修正删除原生过宽限制；没有新运行证据证明description偏窄就是I12未使用executor的原因。

explorer的description改为：

> 承担有明确用途、证据路径复杂或噪声较高的调查、根因诊断与探索；独立完成局部证据获取与分析，将结果压缩为调用方可采用的结论、关键来源和重要未知。关键信息不足时可请求调用方补充。

委派价值来自隔离一段有内在关联的调查过程，使调用方能采用结果而不必重复全部检索、诊断和分析。复杂度只是判断线索，还要看任务边界、提供材料和消费结果的成本；不把explorer当作每次单条查询的中转。根因诊断可以包括提出解释、取得区分性观察和修订判断，而不止收集资料。这是给调用方理解职责的理由，不追加为child固定SOP。

child正文保留下列工作入口与必要工具用途：

> 先做元调查，明确要回答的问题、调用方的用途、已有材料和关键信息缺口；据此规划调查，使用task packet保存当前判断、依据及下一步。
>
> 关键信息不足或任务边界不清时，可暂停依赖该信息的调查，向调用方说明缺口及其影响，请求补充后继续。

请求补充发生在采用错误前提开展大量工作之前。复用Pi原生contact_supervisor联络能力，不建立新审批流程或固定提问表；调查结果仍服务调用方的后续决定。

| 工具 | 适用场景 |
| --- | --- |
| ast-grep | 按代码语法结构定位调用、表达式或声明。 |
| Context7 | 查询已知库的API、版本及官方用法。 |
| Exa | 发现跨站来源、检索外部事实或读取网页。 |
| agent-browser | 观察页面、复现交互或读取浏览器反馈，具体接口见其技能。 |

Pi已说明的bash、read、edit/write、ls/find、grep/rg等基础工具不再在角色中重复；原生委派/联络工具也复用其自身说明。Context7和Exa在这里仅说明用途，删除mcporter调用方式；用户已将自有key打包及直接接线归入“其它”组，该组完成后以实际工具接口为准。pi-fff同属“其它”组，不作为本批改稿前提。领域技能按问题读取。

原始SVC参考将Explorer定义为委派工作契约，强调明确消费者、复杂证据路径、来源/时效/未知和紧凑返回。采用其委派与信息补全理由；历史参考的默认只读、固定效果排除和禁止写packet等约束不照搬，保持本轮完整工具及工作材料方向。角色没有新增固定返回模板，也不内联原始方法正文。

用户进一步要求参考当前Codex的advisor角色。采用其在决定形成前参与问题定义和重要取舍、遇到实质新情况时帮助重新判断的定位，将这些使用时机放入给调用方的description；advisor并非只在既定方案完成后审阅。child正文仍为一句用途说明，不移入固定输入输出协议、思考步骤或审查程序。

父profile保留advisor的使用时机，调用内容收敛为一句：“咨询时可附背景、待决问题和资料入口。”去掉规定其反例、替代方案、思考步骤和返回字段的文字。角色用途、父端调用说明与child正文相互一致。

## 配置和输入边界

child保留Pi基础工具说明、简短角色正文、技能发现入口和本次委派；Braid profile instruction及本轮完整环境/工作流程不作为child的自动追加正文。父任务提供与本次工作有关的需求和环境事实，不要求child继承整个Braid会话。

独立advisor已核对父/child参数：Braid只在父进程加入`--append-system-prompt`；原生前台、后台child都从固定参数构造新进程，预算launcher仅加入预算和时序扩展。因此当前没有已证的profile参数自动继承缺陷，不增加拦截器。保留`defaultContext: fresh`、`systemPromptMode: append`、`inheritProjectContext: false`、`inheritSkills: false`；fresh是默认选择，调用方仍可明确传递所需上下文。共享native home的`SYSTEM.md`另有自动发现路径，当前模板没有该文件，材料核对要覆盖该位置。

五个角色均可再次委派。深度按Pi原生计数：Braid成员的主Pi会话为0，子层可为1、2、3；第三层仍可完成自己的工作，不能生成第四层。设置本次run环境`PI_SUBAGENT_MAX_DEPTH=3`，原生代码继承上限、子配置只能收紧；不用错误的`settings.json.subagents.maxDepth`位置，也不新增深度计数器。

删除角色`tools`，在两份native `settings.json`顶层设置：

```json
"defaultTools": ["read", "bash", "edit", "write", "grep", "find", "ls"]
```

这只是Linux内置工具的默认激活集合，不形成角色白名单；扩展工具按原生注册方式启用。Pi还有powershell工具，但本版本在非Windows的execute路径直接报平台不支持，不属于缺少角色权限；本批不添加PowerShell依赖或另造禁用规则。原生没有`tools: "*"`语义，列满角色tools仍会变成硬白名单并可能漏掉联络、等待等扩展工具。

pi-subagents目前只有声明工具包含subagent时才开放fanout。因此在`src/runs/shared/pi-args.ts::resolvePiLaunchToolPlan`中，让未指定tools且既有能力上限允许subagent的路径也取得fanout；其它调用方显式白名单和权限上限语义保留。角色统一装载已有后台bash扩展，包括开放工具后的vision。原生自行加载prompt-runtime/fanout-child，沿用native home中的角色目录，无需重建子角色注册机制。

第二处窄补丁是`subagent-prompt-runtime.ts::CHILD_FANOUT_BOUNDARY_INSTRUCTIONS`。替换为简短的任务归属说明，例如：“You are a subagent working on the assigned task. Use the available tools and subagents to carry it through; the parent session integrates the results.”删除显式请求fanout的前提及重复禁句，保留运行时深度限制、权限边界、结果归属和完成通知。

用户明确：“永远禁止出现内联agent skill的情况，即便是sub-agent也不可以。”该规则适用于全部技能及所有会话。技能始终保存为独立文件，发现入口只提供名称、描述和路径；模型按需读取。SKILL.md及references正文均不拼接到system/profile/role/task prompt，不能通过改换承载层继续预加载。

技能选择不等于工具裁剪。保留角色自己的skills/skillPath，原生buildSkillInjection生成名称、描述和路径，不注入技能正文；不会因inheritSkills:false或父launcher的no-skills丢掉这些显式入口。本批清除三类workflow和agent-browser的现有内联，并从child入口移除svc-implementation/investigation/design引用；整个I13打包清单、父入口和保留技能交叉链接的统一清理仍属于下一批。其余技能保持按需可达，各角色增加svc-sub-agents发现入口。

视觉接线复用现有glm-5.3-flash的text/image配置及兼容字段，更新visual provider目录和VISUAL_MODEL校验，不改advisor、executor、explorer的模型。本批未验证新视觉模型的实际API运行；现有配置可供实现参考，不能代替后续真实使用证据。

## 实施面与反馈

实现落在新`variants/pi-braid-i13/`，由当前I12源码形成明确起点；I12冻结材料和运行保持原身份。保留现有双profile组织，不在本批进行通用配置框架重构。

| 文件面 | 本批职责 |
| --- | --- |
| I13的`agents/*/agents/*.md`、`settings.json`、`models.json` | 角色文案、默认工具、技能/扩展入口及视觉模型。 |
| I13的`run.py` | 移除child追加内容，接线必要扩展、深度上限与视觉模型；父RUN_CONDITIONS整体重写留下一批。 |
| I13的`agents/*/instructions.md` | 仅同步advisor调用内容的简化。 |
| `harness/npm/patches/`中锁定pi-subagents 0.56.0的新窄补丁及`scripts/runtime.py` | 修正未声明tools时的fanout能力与fanout child自动文案，两处原生配置无法表达；通过现有补丁安装/身份记录接线，不修改npm临时缓存代替可冻结实现。 |

原生补丁会进入未来新构建的Factory runtime，未指定tools的原生child将具备再委派入口；已有冻结runtime不会自动改变。显式能力上限继续生效，不顺带修改其它variant的角色文件。I13还未完成下一批材料，不能把本批形成的目录当成最终实验制品。

本页已完成用户方案复核并吸收修订；executor写入说明的后续修正也已独立完成。开工后采用必要编译和实际材料构建，检查生成后的角色、输入来源、工具及扩展接线，特别核对只有技能发现信息而无正文内联。不建立或运行Factory/Braid测试、模拟任务或模型探针。实际三层委派、caller补充信息往返、结果逐层回送、视觉读取和executor采用由后续获授权工作取得反馈，未发生时保留未验。

原有按Braid session的模型预算保护、原生结果归属与完成等待继续有效；开放子层不会增加Braid session名额。后续executor批次已删除通用单writer、强制worktree隔离及父方应用全部修正说明；共享工作区与worktree能力保留，由Agent按任务选择，不设父方独占默认。没有新增并发调度器、自动worktree或调用配额。

## 核对依据

本轮读取两profile全部五角色、父instructions、models/settings、run.py生成路径，以及原生锁定源码。关键边界由独立advisor只读预演，主Agent另核对tool plan、自动fanout文案与PowerShell平台检查；没有执行模型或将源码阅读当作真实调用验收。

- 角色/生成入口：`variants/pi-braid-i12/agents/`、`run.py::native_files`；两个profile的五份角色内容逐一相同。
- 父追加与预算：`sources/braid/src/provider/pi.rs`、`scripts/agent_support.py::budgeted_pi`。
- 原生启动与输入：保留runtime的`pi-subagents/src/runs/foreground/execution.ts`、`background/subagent-runner.ts`、`shared/pi-args.ts`和`subagent-prompt-runtime.ts`。
- 平台工具：Pi 0.85.1的`dist/core/tools/bash.js`和`dist/utils/shell.js::getPowerShellConfig`；只在工具执行时解析shell，注册本身不因此失败。
- Explorer原始参考：已确认`sources/svc`远端为`xiaoland/svc`，读取本地保留提交`393b9352fae1e8b22d86b28a65ff2f7ded267a38`的`corpus/sub-agents/explorer.md`、`index.md`，以及现存`design/74`、`design/77`和`svc-investigation/references/delegating-investigation.md`。这些仅为设计依据，不重新打包被用户排除的skill。
- Executor原始参考：同一提交的`corpus/sub-agents/executor.md`及现存`svc-implementation/references/delegating-implementation.md`，强调明确效果范围、有效局部反馈、实际成果和本地修正能力；采用其职责边界，不复制原文的固定Assignment字段、validator协议或额外SOP。
- caller补充入口：`pi-subagents/src/intercom/native-supervisor-channel.ts`已有contact_supervisor与等待回复路径；本轮只读确认能力，实际请求/恢复仍未验。
