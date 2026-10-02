# 最终复审补充：运行时完整性与反向对账

此前runtime-coverage是目录覆盖，不等于所有目录项同等深核，也未覆盖全部打包消费者。本页补齐实际实现→目录的反向核对，并展开R18/R21/R23/R24/R29。仍接续同一最终复审，FR1未修且不重复证明。新增一项需先消费的恢复缺陷FR2，以及L01遗漏的归档消费者C1；没有重做两题全量分析。

本页只读当前源码、原始证据入口和既有实施记录，仅写本文件。没有运行测试、探针、生产函数、构建、模型或实验。下面“实核”指当前机制阅读，不等于行为验收；引用历史执行结果均注明来源和条件。

## 反查范围及可回答的完整性

本轮读取 `iteration10/{closure,implementation,build,evidence-consumption,experiments}.md`、运行时相关cells及当前scope、旧snapshot，沿两活动variant的build/run入口核对实际依赖。检查了Braid独立仓库的dirty文件和diff结构，以迁移、已记录修复与旧部署cell定位归属，没有把全部dirty机械计成迭代10新增修复。

`source-snapshot.json`覆盖Braid源文件/迁移、两variant、npm补丁、runtime.py及submission；它不含 `scripts/{package_agent,agent_support,braid_runtime,core}.py`、`scripts/model_budget.mjs`、`lab/otlp.py` 等实际入包依赖。此前“148文件无漂移”不能证明这些未登记输入不影响修复。当前 `package_agent.py::assemble` 确实复制四个support文件，并为活动variant带入OTLP与依赖；build.py还导出ARC runtime。对此本页明确登记接线和影响，未把其全部历史实现冒称本次逐行重审。

| 实际改动/输入族 | 当前实核入口及目录映射 | 归属与剩余边界 |
| --- | --- | --- |
| 评论回执、指派反馈、正文入口、Agent status裁剪 | Braid CLI；R01/R20/Z03/R29；前轮已实核，快照未变。 | 有目录，复用已有机制结论，不重复CLI操作。 |
| Closes冻结、Git发布恢复、外部整合、共享编号 | objects.rs、0013/0014；R18/R21。 | 本轮展开全局调用链，发现FR2，见下。 |
| 退役收件/范围终态/离线孤儿 | store/mod.rs、local.rs；R23/R24。 | 本轮展开事务、派发和退出接口；历史实证来源见下。 |
| Context一次性、严格sleeping复用、临时resume回退、改派首次Wake | provider/pi/session、dispatch/store/objects；R14/R15/R16/A02。 | 前轮已覆盖关键条件，当前snapshot未变；补读iteration10-lifecycle说明与离线回退，沿用真实Pi尚未验条件。 |
| 旧CLI绑定撤销、已接受/未接受回合区分、物理reset后的assignment修复、允许离线刷新原生材料 | local.rs:303–342/382、store/mod.rs:3070/3181–3224，迁移0008，provider/worker；旧目录只间接涵盖R15/R23/R24。 | 来自较早assignment-resume、termination-contact与experiment-infrastructure/replay修复，是新完整制品携带的恢复前提；不是本轮新发明。应在范围账本列为“继承恢复基线”，不能仅用R15标题声称全部审过。当前离线请求限制和原子修复本轮实核，其它provider完整停止协议复用旧审。 |
| 具体成员身份、PR base/head/draft、direct contact/subscription、根空闲检查 | 迁移0009–0012及objects/store/dispatch，Braid dirty中大量新增函数。 | 是较早协作基线，R17–R23只覆盖其后续修正。存在当前源码和旧产品/实施记录，不因dirty把它们算成迭代10新增；本轮没有重新证明每个原始能力。 |
| observer当前/历史父索引、通知、错误调用提示 | 两活动variant observer；R10/R11/R12/Z01/Z02/L01。 | 运行时已深核；FR1仍未修。反查下游找到C1。 |
| 原生子会话归档与manifest | package_agent.py:96复制core.py；run.py:329调用archive_sessions；core.py:129–230/280–322。 | **目录遗漏的L01消费者C1**；旧snapshot未登记，不能靠observer自身通过推导归档正确。 |
| PBB有限任务登记/agent_end等待/service回执与双平台补丁 | npm patch、runtime.py:24–40、Dockerfile:16–17；A01/A07/L02。 | 已实核；build.md历史c58d66预热不含当前ff7631，仍须新冻结，完成/取消真实时序未证。 |
| Collector发出集合和flush窗口 | evidence.rs/telemetry.rs；R29。 | 本轮展开emit→自动flush→轮末flush→失败重试，见下。 |
| monitor连续错误与来源时间边界、Pi错误原文 | monitor-generation.py、provider/pi；R25/A03。 | 旧snapshot未变，复用已列真实记录核对，非新运行监控通过。 |
| 证据采集包含subscription/activity及新终态标签 | evidence.rs::TABLES与capture终态判断；R29只登记重试、未单列这两处。 | diff显示新增协作表并接受quiescent/blocked终态；属于协作/生命周期基线的证据投影，不把blocked等同应用成功。当前静态已核，精确所属迭代未从dirty推断。 |
| 原文证据ID定位、分页及分析方法 | lab/__main__.py/L03；agents/run-analysis/M05。 | lab读取机制已深核；方法交methods。不能把定位便利当成自动跨链分析。 |
| pnpm/portless、Node/Chromium工具入口、PBB补丁、技能物化及共同环境 | package_agent.py→variant build.py→submission/build.py/Dockerfile，runtime.py；A06/A07/R02/R28/M项。 | 当前传递链已读；Node20/正式npm兼容仍为新应用真实观察。methods负责角色和SVC内容，不以本表代替。 |
| with-service首轮退出/候选回执、process group清理 | agent-browser目录；R26/R27/A10。 | 旧快照一致，复用此前全文审查与历史应用副本实操；不扩大为全机资源隔离。 |
| 按Braid身份的昂贵模型限额 | package_agent复制model_budget.mjs，agent_support.py::budgeted_pi，同一launcher由variant使用。 | 属competition-budget已有约束，现目录没有独立项；当前只读确认SQLite cli_binding→agent_id身份、原生child排除、原子slot和失败退出的接线。不是本轮新修，不声称实际模型请求通过；新制品准入仍必须保留。 |
| ARC/OTLP支持、源包清理、其它实验/老variant dirty | scripts/package_agent.py、lab runtime导出、support/otlp及旧variant目录。 | 旧迭代/基础设施依赖，不应自动记为此次修复。精确dirty起点没有统一提交或逐文件基线，无法给全部hunk确切迭代归属；本页只核影响当前修复的消费者，不声称全仓库审计。 |

反查结果不是“无遗漏”：C1是新增且具体的实现消费者缺口；继承恢复基线、预算保护及support打包输入此前也没有独立覆盖位置。它们应并入同一范围账本说明，不必为了编号再造一套实现。当前没有新的统一Linux制品，不能对尚不存在的制品完成字节级验收；build.md已经承认远端预热和build-source早于后续改动，本轮未操作远端。

## R18/R21深核及FR2：已发布合并的后续快进会被恢复误判为未发布

产品义务是精确发布已批准候选，并在Git/SQLite不能共享事务时恢复那一次已发布的事实，关闭目标使用prepared时冻结的声明；不能因后来正文或源分支改变重解释已发布意图。依据 `sources/braid/docs/20-product-tdd/local.md:88,96–98` 和本次boundaries，不是要求Braid判断应用质量。

本轮直接读 `objects.rs:1321–1425,1499–1538,1612–1894`：创建/ready保存“head当时不在base”的正证；普通merge在Immediate事务中准备合并对象、保存base/head及closing_issues；`update_merge_refs`在Git同一ref事务中verify源head和CAS目标base；正常发布/恢复都调用 `apply_merge`，Issue关闭和PR merged同SQLite事务提交；0014旧行默认空声明避免追溯。这些机制对根因的归属正确，`Closes`解析也没有变成关闭所有关联Issue。非默认分支、纯link、失败及已关闭Issue的边界在代码里明确。

**FR2是本轮新增的确定源码缺口，未用运行复现。** `apply_merge:1786–1811`只接受目标tip等于原base，或恰好等于prepared merge M。具体反例顺序为：Git已发布M，SQLite结算前进程中断；允许的外部Git操作把同一目标快进到D且D包含M；恢复读到D后，代码将intent标conflict并报“prepared merge M was not published”。这是错误的技术事实：M仍在目标历史内。`recover_merges:1843–1849`直接传播该错误，因此恢复无法完成原冻结的Issue关闭和PR结算。

竞争解释和成立条件：若目标仍恰好是M，现有恢复成立；若目标D并不包含M，应继续拒绝，不能把任意移动都当发布成功。没有已知旧运行证据表明该窗口实际出现，也不能将此缺陷归因于两题失分。它之所以需要消费，是本产品已允许外部Git整合，且持久intent明确承担崩溃后收据一致性；不是凭空要求新一种业务流程。

最简根治是沿既有Git祖先关系增加“当前目标含prepared M”的正证，视为原intent已发布，保持现ref不动并使用冻结closing_issues结算。不应放宽到“当前目标含当前head”后重做merge：当前正文可能已改，正是冻结意图要避免的漂移。建议在进入新冻结前处理FR2；本分支未修改源码。后续最小证据是获授权实际操作或真实恢复中的M/D祖先关系、原intent与结算结果；不新增测试/探针。

R21其它部分：`create_item:453–480`从local仓库所有kind最大number之后取号，Issue/PR调用者都在Immediate事务内；数据库保留kind+number约束，不新增会让旧双#1库迁移失败的跨kind唯一索引。外部整合路径要求记录过独有head，且当前head包含该正证，再把观测到的base tip记为receipt并明确未更新Git，不伪称原外部merge提交。旧基线缺字段不凭祖先关系猜测；squash/cherry-pick并不在当前自动识别承诺内。因此共享编号及外部整合主修法成立，不需要新计数器或Git扫描器。

原问题证据复用 `hotfix09-object-identity.md`：08 GitHub PR#5 CLOSED、无local_merges但裸origin存在两父merge；旧无创建正证不能追溯改状态；旧Issue/PR双#1确实存在。该cell历史定向检查不是本轮验收。R18历史检查覆盖普通发布、发布后恢复、正文变化等，但未列出“发布后目标继续快进”窗口，不能用其通过掩盖FR2。

## R23：退役地址和全范围终态是同层技术一致性

本轮实核 `store::settle_unreachable_contacts:2583–2605` 及advance_scheduler、begin_agent_assignment调用；同一事务将仅指向blocked/retired成员的pending direct_contact结清为blocked，queued receipt为unreachable并保留成员状态原因。sleeping不在该集合，既有责任与暂时恢复失败不因该函数变成不可达；新成员不接收旧地址的消息。调度和物化入口共用这个动作，能覆盖无需成功启动特定profile的历史队列，避免只在单一worker补guard。

全范围终态直接核对 `local_delivery_closed:5268–5278`，以及local status、delivery_complete/execution_settled、drive退出和Store claim/reactivation入口：根CLOSED之外要求所有工作项CLOSED/MERGED且无prepared或开放冲突merge；已经接受的turn、reset continuation和materializing仍完成后才退出。根关但其它开放且静止返回blocked，保留现场。范围关闭后的普通通知不为清空队列而新建执行，消息仍留存。状态是调度事实而非应用验收，这与用户边界一致，无需新增“任务已做完”启发式。

原证据为 `termination-contact.md` 及其 `termination-contact-evidence.json`：历史实际DB副本连续推进后，glm-3的27条pending contact结清、25条queued归零且12条assignment身份/状态不变。该实证与“21,206次唯一名错误”的上游机制相配，不是模型质量故障。它不能证明所有未来的暂时性provider故障都被正确归类；该另一边界由R15的Deferred和已有停止/重建协议承担。本轮没有再次操作DB，也没有新增复杂状态，修复方向成立。

## R24：离线物化孤儿不能靠删除终态栅栏解决

本轮完整读取 `prepare_offline_resume:3070–3224`，并核对local调用前置和后续worktree继承：local先持runtime.lock、核同一run/seed/prompt/delivery身份；`--offline-resume`是宿主确认旧执行环境停止的断言，不把锁本身当作已杀掉全部旧原生进程的证明。原函数只处理无provider的materializing责任；OPEN时要求当前desired成员/profile/revision与残留一致，原子退休旧generation、仅释放旧login索引、保留worktree并按原assigned_at重排activation。CLOSED/MERGED只收尾、不建新provider；已有provider不进入孤儿分支。再次调用找不到已退休行，事务失败则回滚。

`begin_agent_assignment:4120–4144`读取旧retired/blocked worktree路径供同责任恢复；源文件并未删除。保留公开成员名而换内部generation是技术重新物化，不是业务改派。仍保留materializing终态栅栏正确：它不能仅凭“无provider行”推断进程已经停止。无需放宽execution_settled或直接清计数。

原始定位 `sheet-closeout.md`给出PR#19在08中assignment/agent materializing、assign已消费、provider/turn均无、close pending，且provider内究竟在哪一步中断缺trace；不推断模型故障或SQLite锁。`sheet-materialization-implementation.md`记录隔离真实DB副本的OPEN/MERGED/已有provider分支，以及实际停止03后冻结8.7GB工作区、仅部署83行补丁、恢复quiescent/exit0、materializing=0、main tree保持577ecba…的收据。未提交文件保留是隔离哨兵结果，不冒称旧08原树有脏文件。既有实际恢复足以支持窄根因修法，本轮不重复恢复或评分；新完整制品仍未验证。

## R29：重试窗口修的是重复放大，底层可靠投递仍有限

本轮实核 `evidence.rs:44–116`、`telemetry.rs:269–320,412–454`：record的内容ID排除capture时间；发出前同时记emitted和since_flush；每64条EvidenceWriter成功force_flush返回true后清since_flush，轮末flush成功同样清；capture或flush失败只从emitted删除since_flush内的ID，保留较早成功窗口。collector位于worker循环外，错误不再重建。发出函数本身失败时当前ID已在since_flush，下轮可重试，并非永久被去重吞掉。

原始观察 `hotfix09-collector-evidence.md`是08两个真实collector session的时间窗、record_id交集和transport/flush错误；它支持重置后重复放大，不证明错误后20.65/50.74MB全是重复。该cell已明确SDK 5秒force_flush回执超时与后台导出仍可能成功、有界队列可能丢记录，当前实现也没有新增逐条确认。故本修法成立于“减少全历史重发”目标，不能写成端到端无损或exactly-once；最终capture失败不会无限重试，原文件仍是恢复权威。

最简方案仍是保留现有collector及短窗口集合，不添持久消息队列、第二套遥测或任意调批阈值。历史定向验证仅复用其明确场景；本轮没有发遥测或解码全库。下次真实运行用原错误窗口及record_id判断重复放大是否消失，不把SDK成功回执当持久化证明。

## C1：L01历史清单没有被归档消费者采用

当前observer支持同home父A有子任务→父B，先把A索引写到 `.factory/session-trees/<编码A>.json`，活动session-tree改成B。运行时previousRuns读取两种索引，这是L01承诺的连续性。

但当前 `scripts/core.py::root_source:129–157` 与 `archive_pi_children:159–230` 只读活动 `session-tree.json`。归档旧父A时，若活动父为B，会复制B清单后因父ID不匹配记partial/error，然后不遍历A的子记录。归档外层捕获该错误，因此不一定让应用交付失败；它会造成旧子原文/关联未进入native manifest，进而L03按native ID无法定位这些未归档子会话。持久work目录里仍有历史索引和原文件，不能说数据已从磁盘删除，但正式归档的完整性确实不成立。

这是当前读写schema消费范围不匹配，尚未观测新run触发；普通Braid启动的startup空父→new父没有旧children，不能用这个常见路径推断现有每次归档都会坏。本轮没有验证常规Braid是否还会自然走到有旧children的同home多父切换；然而L01实现主动支持并保存的路径，归档不能只因主代码没崩溃就当已覆盖。

更简单的补齐是归档每个已登记父时按其native ID选择当前或历史清单，保留现有父ID校验和run内路径限制，再沿原children遍历；不合并父身份、不猜UUID、不建立第二份索引。建议把它登记为L01/L03的下游覆盖，并在主线消费修复范围时决定与当前observer一起完成。无须为追溯旧历史重建所有归档；本分支只有文档权限。

## 可复用项、未证范围及下一决定

此前运行时已充分读过且本轮相关快照未变的R01/R10/R12/R14/R15/R16/R17/R19/R20/R25/R26/R27/A01/A02/A03/A06/A07/Z03按runtime-current/coverage所列具体边界复用；本页对R18/R21/R23/R24/R29已提升到当前完整相关机制核对，仍没有提升为新行为验收。R02/R03/R04–R09/R13/R22及A04/A08–A12的方法正文由methods负责；此处没有越界代其宣布完成。

新增确定高影响FR2已即时通知主线；FR1仍是前轮未消费事项。建议在新冻结前先处理这两个资格/恢复事实缺口，C1应随L01消费其归档义务。其余上述核心修复没有发现要求重做方案的根因错误，可进入原已约定的真实观察，但具体实验授权仍由用户/主线控制。PBB完成/取消/settled、旧结果实际消费、Node20兼容及模型限额实际接线的缺证不以文档覆盖替代。

完整性结论限定为：已将本次可确认的运行时修复与当前关键入包消费者反向对账，并补查此前高影响薄弱项；已明确找到并登记目录遗漏，而非宣称整个dirty仓库或未冻结制品全部验收。跨迭代dirty缺少统一起点、未登记support的历史差异、尚未生成的新包和未自然触发的时序仍分别保留边界。
