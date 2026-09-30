# Executor：实际入口与委派成本来源

2026-09-30。按用户“应该自动继续排查”推进；用户最新清单明确executor还需进一步讨论分析解决方案。用户现选择本问题作为主线讨论。本页已补核原生入口、执行路径和说明差分；用户现已授权“好的，开工，应用该修正”；已完成原生说明与帮助文档的最小删除，实际补丁组装、语法编译和工具说明生成通过；未启动模型或创建强制调用规则。
已消费[独立R07调查](upstream-root-cause-investigation/r07.md)，本页记录进一步的入口核对与方案增量。

## 当前裁决

PR15实际列出了executable executor，知道backend/frontend或spec可分，却明确引用“同cwd/worktree一个writer”而预期必须创建隔离工作树、再cherry-pick/合并，选择自己实现。
PR19/20/22还有类似选择，不能继续只写“看不到没用的原因”；但没有executor实际成果，不能把预计成本高等同测得的收益损失。
同一PR能够使用advisor/explorer，排除“所有原生委派均不可用”作为这个样本的解释。

## 新核对的上游来源

版本为pi-subagents 0.56.0，本地保留副本在 `runs/iteration11/20260929-feasibility/runtime/node_modules/pi-subagents/`。
`src/extension/tool-description.ts` L18、L29、L67反复按cwd/worktree规定单writer，L29同时把readonly reviewer、父Agent应用修改作为推荐路径。
`src/extension/public-execution.ts` L41–51实际支持 `isolation:none/worktree`，只检查与显式worktree参数矛盾，不在这个入口强制所有写入隔离；公开字段说明也支持共享cwd。
因此“共享cwd必须有第二个worktree”首先是过宽的指引约束，不能等同于Pi工具不提供共享目录执行。
这不是完整端到端能力证明；历史完整provider工具schema未留存，本地版本身份及主会话直接引用共同支持该指引被采用。

SVC `svc-sub-agents` 则按 **mutable target** 说明写入所有权，允许清晰的整合边界；两者约束单位不同。
I12当前executor角色本身已具备read/bash/edit/write/grep/find/ls，允许授权范围内实现，没有同cwd禁写条款。
接下来应讨论原生扩展对主Agent表达的规则及共享写入边界，不把全部问题归咎于SVC的收益计算或再堆一条“多使用executor”。“Pi禁止多个写入者”不够准确：已证的是工具说明要求同cwd单writer，以及模型采用该指引后的成本预期；未证运行时硬性拒绝多个写入者。

## 写入路径比较（保留能力，不预设协作政策）

| 路径 | 适用情况与成本 | 当前判断 |
| --- | --- | --- |
| 同工作区按实际可变对象分工 | child可接续当前未提交工作，自主调查并组织局部修改，成果直接可用；实际共享效果由执行过程中识别和协调，不要求父方预先列全文件、Git或安装步骤。 | 工具已有该能力；由Agent按任务选择。 |
| 独立worktree | 分支必须独立演进、变更相互影响或任务需隔离时，接受建树、提交与整合成本；外部服务和数据库不会因此自动隔离。 | 保留为有实际理由时的选择。 |
| child只分析，父Agent应用修改 | 父Agent必须独占同一可变对象、且委派分析仍有价值时合适；不能验证executor独立交付价值。 | 保留能力，不作为所有代码委派的默认形式。 |

用户最新反馈将改动收敛为删除原生工具里多余的cwd级单writer指引，保留三种路径由Agent选择。不另设强制共享目录、父方独占Git或固定写入协调制度；现有executor角色和SVC委派方法继续承担任务范围与协作判断。

写入路径及其真实成本由Agent按工作决定。创建更多worktree从未被本项目禁止，公共接口亦提供worktree:true；无须用新的默认禁止或强制规则替换旧规则。

验收时分别判断：工具是否实际启动并交回；效果边界是否被遵守；相比自做是否取得独立价值。
前两项不能证明第三项。先在获授权的真实任务中取得采用证据，不为本次调查自行发起成本对照实验。
Sheet采集未见executor的事实仍有效，但未用的每个决定不能直接套用GitHub理由。

## 角色用途表达的补充修订

用户指出拟定executor description可能与explorer一样偏窄。对照原始SVC Executor契约后，已将[subagents-plan](subagents-plan.md)中的“完成局部实现或修复”改为可独立收敛的工程任务：具备明确目标与影响范围，自主处理必要调查、局部设计、实现和反馈修正，交回可整合的实际成果；关键信息或决定缺失时可先请求caller补充。

“局部”是责任与效果边界，不是任务大小。说明这项闭环能力有助于调用方选择有委派价值的工作，而不将executor当作单次编辑助手。它与单writer指引问题分别处理；此次文案复核没有新增行为证据，不能据此认定I12未采用的根因或净收益已经闭合。

## 本轮讨论：按效果分工，工作区不自动排他

用户在SVC批次交子Agent实施后选择查看executor并发写入问题。首轮提出按可变目标分工及父方统筹Git等细则；用户进一步指出运行时并不阻止共享cwd、worktree一直允许，删除多余说明即可。当前方案据此进一步简化，不把首轮讨论中的风险分析全部转成新提示词制度。本项已获准按这一收敛范围实施。

### 执行路径与适用限制

本轮读取 `runs/iteration13/subagents-20260930/runtime/node_modules/pi-subagents/` 的 0.56.0 源码；这份独立 runtime 仅带前批已记录补丁，不冒充已部署 I12 的完整工具输入。

| 来源 | 新核对的事实及含义 |
| --- | --- |
| `src/extension/tool-description.ts:13–20,184` 与 I13 settings | 当前未设置 toolDescriptionMode，工具采用短 DEFAULT description 加 promptGuidelines；cwd 单 writer 位于该 guidelines。full/compact/custom 也各有重复政策，但不能宣称它们此刻全被装载。 |
| 同文件 safety/full/compact | safety 要求同 cwd 单 writer 并让父方应用修正，custom 会强制追加它；compact 重复该要求。full/compact 另把 repository mutation 直接导向 worktree。只改一个句子或提供 custom 文案仍可能留下冲突。 |
| `src/extension/public-execution.ts:41–51`、`schemas.ts:280–281` | isolation:none 转换为 worktree:false，接口明确允许共享 cwd；这不是写入权限是否到位的端到端证明。 |
| `src/runs/foreground/subagent-executor.ts:3220–3246,3535–3546`、`execution.ts:544–546` | 未启用 worktree 就不创建工作树，child 使用源 cwd 启动。async-execution.ts:1438–1442 也在未启用时使用 runnerCwd。所核路径没有按 cwd 排斥另一 writer。 |
| `src/runs/shared/session-lease.ts:112–126` | lease 以原生 session 文件为键，避免同一会话被同时续写；它不是代码工作区的 writer 锁，不应移除。 |
| `src/runs/shared/worktree.ts:150–158,243–252` | managed worktree 要求源工作区干净，可能链接顶层 node_modules。它有真实准备成本，也不自动隔离依赖安装、端口或外部数据。 |
| `src/runs/shared/mutation-evidence.ts` | tracked mutation 依据整个 cwd 的前后 Git diff 变化；共享并写时不能将其 changedFiles 自动归为某个 child 独占成果。消费仍要结合实际委派范围和产物，不因此新增归属追踪框架。 |
| `src/extension/subagent-guide.ts` | guide 会读取包内 README/docs；docs/workflows.md 的通用写入规则实际可达。包内 pi-subagents skill 及 references 另有同类规则，当前 Factory 不显式启用该 skill；它们不是本次观察到的自动内联输入。 |

### 为什么当时放弃 executor

本轮定向回读 PR15 原件 L52/L54（消息 771f60d1、295759f1），确认调用方知道 worktree:true 可用，也认为提交后 cherry-pick 可行；没有尝试创建失败或因权限被拒的记录。它在“可分前后端”“同cwd不宜并写”“隔离后担心共享文件冲突和整合复杂度”“自己已有上下文，预计能顺序做完”之间反复取舍，最后选择全部自做，仅把executor保留到上下文压力上升时使用。它后来还识别了不重叠文件分工，但没有因此改变选择。

因此，创建worktree被允许与Agent认为不值得采用并不矛盾。已证的是成本与一致性风险的主观预期；过宽单writer指引给普通实现委派额外加了一道隔离前提，但不能把它当成唯一原因，也没有实际冲突/合并耗时支持这种预期。上文clean tree和node_modules事实仅说明工具特性，不是当时放弃的已证根因。

### 当前取舍

采纳用户的简化方向：已有executor描述和通用委派方法要求处理任务范围、保留他人修改并独立收敛，当前无须再增加一套父方独占Git、文件级锁或固定并发协议。共享cwd和独立worktree均保留，Agent可以自主选择。

用户进一步明确不能采纳要求父方知晓过多执行细节的方案：否则委派价值不划算，应回到svc-sub-agents的原理。这修正的不只是规则长度，而是工作归属。调用方明确想解决的问题、成果用途、必要背景和真正影响目标/权限的边界；executor自主取得材料、形成局部设计、选择工作区和写入方式、协调局部效果并利用反馈修正。父方无需预先设计完整文件划分、Git操作、依赖安装、资源清单或每项检查，child也不因碰到普通实现问题就反复交回。

成果采用只取得足以支持当前决定的结果与依据；需要改变整体目标、权限或重要取舍的事项才升级。具体执行细节可保存在工作材料中按需取得，不默认回灌父会话。该原则已同步给SVC实施子Agent，核对其输入说明是否不慎要求调用方先完成整个任务的元调查和设计。运行是否从中获益仍由实际工作证据判断，不先假设必须用制度阻止尚未观察到的冲突。

### 已实施范围

优先在既有Pi扩展补丁中直接删掉过宽指引，避免在system/profile再叠“忽略另一条规则”。同步删除promptGuidelines、safety和compact里的cwd级单writer、默认只读child及父方应用全部修正要求；full/compact的worktree说明只解释参数效果，不把普通repository mutation一概导向worktree。

既有参数、执行能力、原生session lease与深度限制保持其原职责；本项不需要改派生逻辑，也不增加writer调度器、权限名单或固定协调协议。工具原生custom模式还会追加safetyGuidance，因此仅在配置里写一个自定义description未必去掉旧条款，直接修包内来源更明确。

包内可读取说明一起消除通用矛盾：docs/workflows.md，skills/pi-subagents/SKILL.md、references/constraints-and-recipes.md、execution-controls.md、multi-lane-orchestration.md，及 prompting-and-roles 中把 one writer 泛称为硬约束的例子。只改普遍规则与例子的适用条件，不重写无关高级编排教程、模型角色或全部单 writer 示例。原生包文件经既有补丁机制接线到本地/Linux runtime 及来源身份；SVC 当前按可变目标协调的通用原则与此相容，不往技能追加 executor 专项政策。

反馈先核对实际补丁适用、编译、最终工具说明及 guide/skill 的一致含义，不添加测试、探针或模拟任务。模型并发启动、成果交回、是否遵守范围与实际净收益分别在后续获授权真实任务观察；本轮说明修正方案不依赖另开成本对照实验，也不声称已经证明收益。


## 实施与反馈（2026-09-30）

按用户“好的，开工，应用该修正”实施。原生工具guidelines、safety、compact中的cwd级单writer、默认只读child及父方应用修正要求已删除；full/compact的worktree说明只解释参数效果。包内工作流和技能帮助共六份文档同步去掉通用禁并写及强制隔离说明，保留注明适用条件的单writer示例。executor可以自行选择共享目录或worktree，并完成其任务内的调查、设计、实现和协调；本批没有新加父方逐文件规划或Git操作制度。

改动并入已有 `pi-subagents-0.56.0-acceptance-off.patch`，保留此前关闭自动验收的全部差分。该补丁已经修改同一tool-description.ts；另加重叠补丁会使本地runtime前一补丁的目标hash戳在每次prepare时失效。复用现有补丁并补齐runtime的六个文档目标即可，Linux既有Docker应用路径和来源hash记录自然消费更新，无须改缓存机制或新增接线。

证据目录为 `runs/iteration13/executor-guidance-20260930/`。`start.json`和before保留起点；`guidance-only.patch`仅展示本批原生说明差分；最终补丁SHA-256为 `3c233e953cf16dd0c6fd9cf006aaa4e11b991daa9c145ab8f838b049853e5a1f`。

| 实际反馈 | 结果及边界 |
| --- | --- |
| 从原始0.56.0 npm归档按生产顺序应用四份补丁，fuzz=0 | 全部成功；最终18个acceptance-off目标与预期材料一致。相对上一条补丁链仅七份文件变化，执行逻辑没有额外差分。原始输出见after-apply.json和source-review.json。 |
| Python编译及TypeScript 5.7.2语法/emit编译 | 通过，TypeScript零诊断；不宣称完整类型检查。见assembly-result.json、native-compile.json。 |
| 直接导入组装后的原生模块，按两个真实I13 settings生成description/metadata | 两份当前默认输入均已去掉单writer条款；full/compact常量及custom必加safety也已导出核对。材料在rendered/。 |
| 帮助入口及源材料核对 | workflows、SKILL和四份references的重复通用规则已同步；剩余单writer内容属于条件示例或未启用builtin角色的原有说明。没有内联技能正文。 |
| I12文件身份比对 | 本批前后25份文件hash一致；未替换冻结runtime或控制现存运行。 |

这批验证的是补丁和可消费材料，未运行模型、并发child、测试或包smoke。共享写入、三层委派、成果整合与实际委派收益仍待获授权真实任务取得证据；现有session lease、worktree准备要求及cwd级mutation-evidence归属限制保留。
