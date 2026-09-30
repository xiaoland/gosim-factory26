# I13：保全需求责任与验收判断

2026-09-30。状态：G04/G05的V&V方法正文已随元理论改写提交到SVC `31906a5`；G01、task-packet依据说明及I13角色接线尚未实施。
用户随后要求重新审查V&V技能；[技能复审](vv-skill-review.md) 确认内容与路由的更大缺口。
本文保留三项因果证据及采用判据，G04/G05原局部措辞已经融入整体方法，不再作为待重复追加的补丁；实际源码及内容复核见技能复审页。
用户明确要求“那么将G01/G04/G05纳入I13的范围内”。本cell从I12转交，保留已有诊断、方案与独立材料调查；历史编号I12-G01/G04/G05不变，修复归属I13。
当时确认的是迭代范围；随后V&V技能取得单独开工授权并完成。I12两题按用户要求暂停，见 [原重启与暂停记录](../iteration12/restart.md)，不改变冻结输入；I13的实现载体及实验输入另行确定。

## 顶层目标与因果链

在分工、整合和结果交接中保持原产品承诺，让最终完成判断由足够、可追溯的证据支持，同时复用仍有效的工作。
这不是要求多写文档、多开审查、多跑一遍测试；要改变的是三次具体决定。

```text
原始产品承诺
├─ 分工：本项不做的已知需求 → 整体责任保留 → 实际接手与成果返回［G01］
├─ 整合：原始场景 → 现有判据能否证明 → 已有证据或明确缺口［G04］
└─ 交接：一次真实执行 → 独立原件 → 同次结果的摘要与完成结论［G05］
```

G01和G04与已登记G02共享PR里程碑遗漏这条证据链，但分别解释责任转移与最终审查的决定，不按三个功能缺陷计数。
G05是独立的记录错配，不否认最终194/152通过，也不据此解释全部官方失分。
两题共有的效率修复E01/E02继续在I12按既有 [问题账](../iteration12/i11-github-score/findings.md) 观察，不恢复专门SHA规则或叠加无动作提醒。

## 为什么现有方法没有闭合这些问题

| 问题 | 当时已经具备什么 | 可观察的断点 | 修正决定 |
| --- | --- | --- | --- |
| G01 | 原需求可读，局部范围不能缩小产品承诺的原则及owner/evidence方法已存在。 | 两位负责人已经看见并列对象的缺口，仍猜由另一模块负责；根读到排除声明，却没有形成实际承接。 | 排除已知需求不是完成或转交的证明。局部负责人报告具体义务和来源，整体负责人保留它，直到被实际接手并返回成果。 |
| G04 | 检查设计已经要求对照原场景及并列对象；原文、排除声明和mapping都被整合者读到。 | 整合者认为语义转换上游已经完成，选择只检查ID引用并执行现有suite；packet把工作项正文与原需求排成统一权威顺序。 | 按要回答的问题区分依据；接受已有判据时同样核对它能证明哪些原始行为，mapping只定位证据，不证明覆盖。 |
| G05 | 角色已有保存原始输出、实际退出码和失败的要求；现有with-service工具每次使用独立临时结果目录。 | 原生执行手动重复写同名日志，后续摘要把前一轮成功与后一轮失败文件混配，根抽查最终通过日志未纠正。 | 重复执行的原件保持可分别引用；摘要从引用的那一次原件生成，交回前核对候选、条件、退出码与输出属于同次。 |

原始决策与工具返回见 [PR23过程](../iteration11/braid-context-methodology/final-pr23-flow.md) §2–5、[根最终审阅](../iteration11/braid-context-methodology/final-root-flow.md)及 [跨模块承接](../pi-minimal/github-score-analysis/i11-mechanisms-forward.md) §6。
这些消息确实到达且被理解，不能把质量链归为Braid丢信，也不能以更长上下文或再加“完整覆盖”口号替代决定修正。

## 具体方案与归属

以下四个位置是三项问题的原局部落点；V&V整体修订以新的技能复审方案为准。I13角色保留按需入口，不复制这些方法全文。
Braid继续提供Issue/PR、成员、讨论、Git和上下文能力，不解析业务需求，不决定哪些业务场景通过。
Variant仍负责角色与技能接线；不生成或修改本题应用的检查与数据。

### G01：任务范围变化产生实际交接

在 `sources/svc/skills/svc-task-packet/references/planning.md` 现有依赖与协作段补一段，保留局部边界和不受影响工作并行的原则：

> When required behavior falls outside a contributor's assigned scope, identify the obligation and its source for the coordinator. The coordinator retains it as unfinished in the overall task until an owner actually accepts it and the result is returned. Naming another module or sending a notification does not establish that handoff. The contributor can continue unaffected work without implementing beyond their scope.

不新增固定表格、ack状态或强制为每次普通交接再建任务。
已经有明确负责人及实际工作、成果的，不因缺一句格式化确认重复协商；尚未分派的义务可以按真实依赖等待，但不能进入完整交付声明。
`product.md`已有“局部责任缩小不缩小产品承诺”，保留，不在这里再复制一轮通用完整性指引。

### G04：接受已有检查也要判断语义覆盖

在 `sources/svc/skills/svc-verification/references/interpreting-results.md` 的“Establish Confidence Through Evidence”段衔接已有共同错误假设原则：

> A requirement-to-check mapping locates work; a reference or a passing check does not establish that its judgment covers the original scenario. When accepting existing checks for an integrated coverage claim, compare their judgments with the original objects, roles, initial conditions, actions and promised results, especially at excluded boundaries or revised interpretations. Ask whether the evidence could still pass if a promised behavior were absent. Retain valid results and name the unsupported behavior; this comparison does not itself require rerunning them.

检查设计中的反例、例外和真实跨组件路径不再复制到新章节。
对原场景的核对是独立于引用数量、PASS数量的语义判断，不要求另派reviewer，不强制重写所有检查或重读所有历史讨论。
例如产品承诺“编辑器和导入器都能更新同一设置并在重开后保存”，只有编辑器路径的全绿不能证明导入器；保留编辑器证据，补清导入器义务和观察，不能把缺口扩大为全量复跑。

同时替换 `sources/svc/skills/svc-task-packet/SKILL.md` 的单句依据说明：

> Take intended product behavior from requirements, assignment and coordination authority from current work items, and current truth from observations. These sources answer different questions; a narrower assignment does not redefine the product promise.

这处理的是“所有依据按一个顺序排名”的错误，而不是禁止工作项澄清需求；有效的需求更正仍须具有对应决定权限和来源。

### G05：每次执行与摘要一一对应

在 `sources/svc/skills/svc-verification/references/repeatable-checks.md` 现有原始保存/摘要链中补足：

> Retain each execution under a distinct, directly referenceable result entry. Use the execution tool's durable record or a separate output file, and do not overwrite an earlier failure or interruption on a repeat. Produce the summary from that retained result. Before handing it off, confirm that the candidate, relevant conditions, actual exit status and cited output belong to the same execution. Keep earlier and later results separately attributable; a later pass does not relabel an earlier attempt.

复用已有执行记录即可，缺少完整输出与退出码时才使用agent-browser技能中的包装工具；该工具本来就会创建独立目录，此项不改工具、不加执行框架。
需要持续保全时把独立结果入口保留到任务证据中，不要求生成应用增加固定scripts或目录，也不为制造记录重复运行已完成检查。
“某次失败的原因尚未确定”和“后一次检查通过”可以同时成立，摘要不通过更名或换标签消除前者。

### 方法进入工作的入口

作为设计基线的两份 `variants/pi-braid-i12/agents/*/instructions.md`，其最终整合与交接段已经要求按需读取svc-verification。
I13采用对应角色入口，具体实现目录须在开工说明中确定；本次不创建variant，也不修改I12文件。
将该入口收敛为“作出最终覆盖结论时，按svc-verification核对原始承诺、现有判据及对应结果；交接具体依据与剩余义务”，替换现有含糊的“按需解释结果”，不叠加第二套SOP。
这段只定位何时采用方法，不在Braid共用指令、root description或其它技能复制完整清单。
本次技能复审已确认description和首段的使用入口偏窄，应按新方案调整；这仍不意味着所有会话预读完整Corpus，也不表示已经测得运行中的路由收益。

## 原局部实施准备与后续归属

以下保留三项问题的原准备过程。V&V内容已经按新复审方案完成；剩余task-packet和角色落点不得因这一记录被当作已应用。

1. 主线按以上四个方法位置窄改，保持已有正确信息及相对链接；同步两份独立角色的同一采用入口。
2. 以历史#235/#308排除、PR23接受mapping和isolated日志错配三条真实输入离线预演：新方法是否能识别未接手义务、语义缺口和同次结果错配，同时保留边界纪律及已证通过。
3. 独立材料调查已由 `i12_method_gaps`（GPT-6.1 Sol / medium，fresh上下文）返回，支持三项问题的局部落点；它没有完成本次使用时机及知识深度的全面复审，不能以“已有原则”推定内容充分。工具独立目录由主线直接核实。调查没有修改源码或运行模型，也未把阅读方法视为实际验收。
4. 开工前呈现I13实现载体、角色入口、SVC材料的选择与加载边界及实验安排，取得针对该实施范围的开工依据；然后应用源码并冻结新材料身份，保留I12身份。共享SVC源码改动不等于已投递给活动会话，也不能自动授权改变I12运行输入。

这份实施准备没有承诺热部署或启动I13实验。I12已有模型进度保留；I13的实验起点、矩阵与完成条件尚未确定，不由本次范围登记推出。

## 验收与边界

不编写或运行SVC内容、Factory或Braid测试，不新增模拟执行或模型探针。
编辑后人工核对链接、实际材料选择和指令接收位置，离线预演只使用已经保存的原始事实，不复跑生成应用或猜隐藏评测器。
下面是I13的采用判据；具体实验须另行确定并获得授权。I12运行是已有基线，不能代替尚未投递的I13方法修正取得采用证据：

- G01：跨范围排除有实际承接或仍明确保留为未完成，最终候选包含对应行为；不能以“已通知根”结案。
- G04：整合判断回到原场景，并能说明既有判据的覆盖和缺口；有效结果被复用，不因形式上的独立复核全量重跑。
- G05：多次执行可分别追溯，交回摘要与引用原件属于同一次；失败与后来的成功各保留实际归属。

触发这些决定后才能评价采用；若未触发，标为未验证，不制造缺陷或提前宣称长期有效。
官方不提供逐例错误，不能把得分变化直接分配给某段提示词；过程采用与末端得分分别记录。
