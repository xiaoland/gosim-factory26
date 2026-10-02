# 09热修复准备：减少无效协调与环境反馈成本

阶段：用户已批准沿上游问题继续深入并一并在09修复；确定项进入实施，剩余根因继续有界核实，08暂保持运行。
用户已认可“调用处反馈”修复，并要求综合token优化、环境/检查成本与sub-agent方法，准备一次热修复。
本页不将准备授权扩展为未复核的Corpus正文或Braid产品改动。

## 目标与证据

让Agent在正确入口取得可直接用于下一步的反馈，减少重复派工、无信息等待和环境误诊，保留完整需求与验收依据。
不以减少上下文、模型调用或检查次数本身为目标。
依据：[08子代理验收](../../factory-subagents/cells/attempt08-validation.md)、[token分析](../../experiment-infrastructure/cells/token-economics.md)、[GitHub进展](attempt08-progress.md)、[Sheet进展](attempt08-sheet-progress.md)、[委派原始讨论](../../factory-subagents/cells/subagent-paradox-source.md)。

## 候选范围

| 项目 | 根因与拟处理 | 所有权/边界 |
| --- | --- | --- |
| 原生等待工具就地反馈 | 全局澄清已注入仍有6次PBB误用；复用现有observer的tool_result，只在subagent_wait原生无匹配/无活动结果后追加正确入口，bg标识点名PBB，all不代表所有后台工作。保留原始结果，不重注册/自动代执行工具 | Pi接线/扩展，独立预演见factory-subagents的09工具反馈cell |
| 短临时目录 | Chromium明确Socket path too long，短路径后通过；普通TMPDIR改用容器内短临时根，Pi通过已有PI_SUBAGENTS_TEMP_ROOT显式固定到原work/tmp/pi-subagents-uid-0 | fresh与recovery入口同步；保持旧子任务可发现，不迁移/重写原生状态，不建立新沙箱或临时目录框架 |
| SVC委派入口和结果消费 | 通用方法隐藏在task-packet引用，原始讨论强调构造可便宜判断的结果；迁移成svc-delegation，按命题/可检查性选择结果消费方式 | 迁移而非复制，V&V保留验证方法权威；不加入Pi/Braid/比赛术语 |
| 调查与反馈方法最小修正 | 两条全量进程诊断约7.9万字符；tail吞退出码已导致误操作/重跑；多重sleep轮询无信息 | 查现有所有者后只补缺口：查询范围、完整日志与有界摘要、真实退出码、现有完成通知；不禁止必要原文和最终验收 |

临时目录技术事实：锁定pi-subagents在shared/types.ts读取PI_SUBAGENTS_TEMP_ROOT并供results/async/chain/artifacts使用，observer也使用同一环境变量。现有运行采用容器UID0且状态在work/tmp/pi-subagents-uid-0；实施前核对实际恢复制品的路径。短路径具体生命周期以现有容器为边界，无需另加隔离系统。

## 不混入本次的事项

- 不换模型，不估虚构节省比例；缓存token与未缓存token分列。
- 不全局截断/过滤工具错误，原始日志保留。
- 不把跨成员重复读原文一概删除；职责不同可需要独立阅读。
- 本地运行可按用户新增授权直接修补生成工作区；本次候选限已证根因的检查脚本退出码假失败，先核对Agent是否已修。业务判据不变，官网运行不适用此例外。
- PR5手工Git合入后Braid状态CLOSED需另做产品/实现核对；本次不顺带改变merge语义。
- 08旧子任务索引已注入；在途完成唤醒未自然触发，不为验收创造子任务。

## 实施与接续顺序（待具体预演收齐）

1. 收齐工具反馈可用API、SVC正文归属与短临时目录兼容性，形成可复核的文件范围。
2. 经开工确认后实施，直接复核正文引用/打包材料与必要编译；不新增Factory/设施/Corpus测试或改名探针。
3. 若08仍生成，按现有流程热停、保存最新半成品，以新ZIP接续；若已进入交付/评分，保留该流程，不为了热修强停。
4. 新包保持成员、模型、Git及Issue/PR状态，4GiB/2CPU和DeepSeek/BigModel路由不变；Qwen/MiniMax不恢复，不使用参赛额度。
5. 基于真实调用核对bg误用后的纠正、浏览器短路径、旧子任务发现与实际消费；按新窗口计量，未触发明确保留。最终看集成候选与评分，不把更多检查或更少token当成质量证明。

## 技术预演结论与具体影响

工具反馈：Pi 0.85.1已有tool_result返回content补丁，现有factory-subagent-observer.ts即可承接；无需修改pi-subagents依赖或覆盖工具注册。实现位置限两个现用variant的既有扩展，更新原注释明确其已承担连续性/接口反馈。工具description没有可维护覆盖点，本次不为改描述引入上游fork。详见 [工具预演](../../factory-subagents/cells/hotfix09-tool-feedback.md)。
PBB已提供原生完成followUp与triggerTurn，但活动响应期间通知排队；反馈说明有独立工作时继续，只剩等待时结束本次响应让完成消息唤醒，避免sleep循环拖延通知。不创建统一等待工具。

SVC具体删除/迁移/替换及拟正文见 [SVC09设计](../../factory-subagents/cells/svc-method-review.md)。新技能单入口替代旧委派引用；调查/实施保留专项，V&V仍是证据判断权威。两variant的build技能清单增加svc-delegation，受影响角色skills引用和维护导航同时更新；不全量强注入技能正文。

环境：fresh的两variant run.py与现有submission/recover_completed.py同步设置短TMPDIR，显式保留Pi原状态根；不改应用、不改模型。打包和08后续接续继续沿用现有入口。

开工复核对象已收敛为三个部分：调用反馈、短临时目录、SVC委派与反馈方法迁移。手工merge识别等Braid产品行为不进入此包。当前只完成准备，不表示已修改源码或已开始09。

## 本地工作区热修复例外

用户新增授权：“本地运行可以作为特例，替agent改动它的工作区内容来作为我们热修复的一部分”。
因此09可包含生成工作区的有界修复，不仅是Harness源码；不是对官网运行或未来提交的普遍豁免。
候选：Sheet checks/run.sh中set-e/pipefail/lsof无监听返回1导致整个检查假失败。先读取最新候选确认运行Agent未已修；如仍需修，在停机保留半成品后应用最小差异，避免并发修改。保存改动前后提交/补丁、理由与实际复验结果，向相关工作项交接修改事实。
不把运行Agent已修好的内容重复修补，不修改需求、断言预期或隐藏失败；测试框架退出和业务检查结果分别保留。
该本地实验结果标记包含开发侧工作区修补，可用于诊断/恢复，但不能作为未经人工修补的Harness端到端能力证据。若据此转化为未来提交改进，应归入通用工具/方法，而非携带题目实现或检查答案。

## 用户复核修正：先解释成本与工作流，再定09范围

用户指出此前仅处理紧急部分，忽略其它优化和深入排查。主Agent接受：现有token报告是账本加少数例子，尚不是端到端消耗归因；没有新subagent调用也不能只当验收机会未出现，而应核对是否有值得委派的工作及未采用原因。
下一阶段围绕决策调查，不以收集更多计数为目的：
1. 成本结构：模型请求/输出、长上下文来源、工具结果、上下文重建、重复实现/复验之间建立代表性因果链。区分必要并行取证与同一工作重做，不将cache当同价浪费。
2. 环境反馈：从创建工作树→安装/构建→起服务→浏览器检查→退出/清理→结果消费查重复成本；区分可复用环境/现成工具缺口、工具不易发现和模型自造设施，兼顾有限CPU并发。
3. 委派采用：选确有收益的读图/探索/局部实现机会，核对当时入口可见性、任务边界、当前owner、启动成本和消费方式；不以调用数低直接判缺陷。
4. 协作关键路径：前提已满足却未派发、根串行复验/整合、旧分支未消费新基线、冗余/延迟通知与重建，找是否有共同边界缺陷，不只追加SOP。
5. Corpus实际进入工作：技能发现/选读/角色装载→具体决定→反馈解释，区分内容缺失、路由失败、工具反馈误导与执行偏离；据此删除/迁移/补充。
6. 可观测性：08新增collector计时实际读回，确认超时及重复采集放大是否还在；判断现有设施能否廉价回答上述问题。
每条返回：已知证据、竞争解释、最小区分观察、会改变什么决定。之后按收益/质量风险/实施与接续成本收敛09，不把所有候选自动纳入。

最新事实：Sheet检查wrapper假失败已由Agent在1be21ec修复，经PR16合入develop=1d7eca7，原生有修前失败与修后通过；部分旧worktree尚未消费。移出“需要开发侧补丁”范围，转入共享基线消费分析，不重复修复。

系统性诊断与分工入口：[问题与决策索引](hotfix09-synthesis.md)。完整进展树已同步到tasks/iteration-map.md，保留未验证与延期支线。

## 本轮开工授权

用户：“按这个方向和范围，我们继续深入排查，然后一并在09内修复。我同意这几个取舍。”
执行：主Agent负责调用反馈、临时目录、variant接线与集成；browser_guidance_apply负责SVC已复核方法迁移；vision_root_cause负责采集超时/重发语义；live_deep_diagnosis负责外部Git合并状态断点。各自先核实真实边界，根因未明不猜测实施。此次不自动授权提交。

## 新增：Issue/PR共享编号

用户指出两类独立编号不符合预期。已核实objects.rs创建逻辑以WHERE kind过滤MAX(number)，确实分配了两套序列。
09对象层修复由live_deep_diagnosis负责：同一仓库新对象共享递增编号，原有kind+number身份与历史引用保留；旧运行已有碰撞不重编号，新对象从现有两类最大号之后分配。最终实现需保持事务并发分配语义，并覆盖交错创建及旧碰撞后接续。
该问题与此前Issue7/PR7同号混淆相关，但不能把所有依赖误判都归因于编号；历史查看仍需类型。

### 官网协作网页 assignee 复核（2026-09-28）

对照 `runs/official-collaboration-review/data.json`、HTML 的 `desired_member_login` 渲染和两份只读 SQLite：不是导出丢失全部负责人。GitHub 9 个 PR 中 #8（deepseek-12，assignment 已 retired）与 #9（glm-13）有指派，其余 7 个 PR 无 assignment 历史；Sheet 11 个 PR 中仅 #1（glm-7）有指派，其余 10 个无 assignment 历史。网页使用 desired_member_login，未把创建者当负责人。Sheet PR #2 的活动显示 glm-3 创建并合并，关联 Issue #3；这证明未指派 PR 也有成员直接操作，不能把“未指派”解释成无人工作。当前页面未同时突出创建者与执行会话来源，用户容易把责任归属和实际操作者混同；若改进展示，应分别呈现，不能从作者推造 assignee。

## 新增：Issue / PR 实施会话边界

用户确认未指派 PR 所暴露的设计/实现分离不完整属于严重缺陷，要求继续推进手上工作。对象层编号与外部合入修复、Linux 编译和普通 base 准备继续并行，不因新调查停止。live_deep_diagnosis 负责将官网活动与会话对应，主 Agent 负责结合产品边界确定最小修正并集成。
当前已知：创建 PR 不传 assignee 时不会发出 Assign；创建对象不等于创建 PR 会话。Braid 当前 Issue 指引允许关联和合并 PR，这本身符合协作需求，不能把“允许合并”误修为禁止合作。Factory“使用关联 PR 完成实现”尚未明确实际执行者需为另行指派的 PR 负责人。调查区分：通用对象/指派能力的反馈是否完整、Factory 工作方法是否准确表达独立实施。不自动选模型，不改变既有历史身份，不用文件系统沙箱代替协作分工。

已证根因与实现：[独立实施边界](issue-pr-session-boundary.md)。两 variant 五份成员指令已明确实施前创建并指派 PR、由独立 PR 成员承接计划/排障/实现/验收，Issue 负责需求方案与协作判断。Braid provider 只解释创建与指派的通用能力区别；CLI 在文本与 JSON 回执中返回保存的真实 assignee，未指派给出补指派入口，不自动选择模型。无源码访问沙箱、不禁止协作合并、不将工作方法嵌入调度器。旧 PR 历史不改写，恢复后用新真实 PR 的 assignment→独立会话/工作区→实施与交接链条验收，不能以创建数量充当证据。

## 09接续实际进度

2026-09-28 08:12:42 UTC 重查08仍为两题生成，随后以既有 lab stop 停止，operation 5824e51aee46ecdde8c2ab57。08:13:42 控制器与两题均 cancelled，生成PID及容器已退出；正在冻结完整最新半成品，未改应用或清理历史。最终Linux Braid为 final-v2，SHA256 b9be6bc37d16187ef579380075295092cb10bcef2184d8b63bb0f93d6ed62a04，对应source bfcce2840dcf50706b7f0b958ac6c2432d9df58d95a6f1ab531865ae64df2aab；release编译成功。09尚待恢复包装与真实启动，不能将停止成功等同恢复成功。

## 接续监控与恢复点决策

用户要求主线推进时由sub-agent持续监控，判断语义进展/P0阻塞，并考虑更早更干净的恢复点。browser_guidance_apply继续负责09即时诊断与既有180/480监控，不以PID/运行标签/token增长作正常证明。09最新采样1790584009：GitHub items21/active0/pending0，Sheet items26/active3/pending62；待核对根状态、检查评论、最新原生动作及队列消费，不预判死锁。
恢复点按需要修复的状态层选择：只有旧会话内容过时，不足以支持丢弃已验证代码；若任务责任、完成声明或Git整合状态有具体不一致，应识别最早错误与可修复范围。比较保留当前半成品并整理上下文、恢复更早一致状态后携入可信成果、从较早代码重做的损益。先列候选的提交/分支/任务状态及会丢失的成果，不为了“干净”盲目整轮回滚。09实际接续证据尚未收齐；用户询问不等于已选择回滚。

监控纠正（08:27 UTC）：上述1790584009的Braid计数来自展开中的08旧数据库，不是09新调度。08:25:03 recovery main启动，08:26:34/38进入完整workspace展开；两题recovery-braid.log尚不存在，恢复Python进程持续写入。主Agent此前据此向用户声称“已进入Braid执行”不成立，已明确纠正。新监控须区分 inherited snapshot 与 fresh native activity，未启动时显示恢复阶段；不以恢复旧数据库里的active/pending判死锁。

### 已确认外部P0：GLM额度429

09 Braid实际恢复时间：GitHub08:29:16 UTC，Sheet08:29:55 UTC。browser_guidance_apply从原生会话核对：08 GitHub根最后08:09:22.748、Sheet根08:11:50.763连续stopReason=error，429原文含“余额不足或无可用资源包，请充值”、Model Group=glm-5.3-flash、Fallbacks=None。09 Sheet新根会话08:32:18/32/37仍同错误。不是历史DB活动误读，已有恢复后新调用证据。主Agent已立即向用户报告外部P0，具体上游路由核对中；不换模型/凭据、不使用参赛额度。恢复旧快照不能消除额度故障，恢复点讨论必须剥离此外部原因。

已核实429上游为GLM_BASE_URL指向open.bigmodel.cn（BigModel直连），DS指向api.deepseek.com，不是比赛额度。09 Sheet DeepSeek在08:33:15/31仍有成功工具活动，但根GLM关键路径不能最终交付。主Agent已向用户报告并请求选择补充BigModel额度或提供可用GLM路由；已授权browser通过既有lab stop停止09、保留最新工作区，避免根重复429，未换模型/密钥、未退历史快照。停止完成收据待回传。

09已于08:36:14 UTC停止，operation4280dfe493fe70837b31292f，控制器/两题cancelled，生成进程与容器退出，monitor终态退出。08:37:57 UTC同gateway/GLM路径一次最小请求HTTP200（15输入/1输出），用户随后明确已补充BigModel余额。接续保持原路由/模型/资源，从09最新workspace开始，优先复用展开材料，避免重新导入08冻结包覆盖新进展。Pi原生错误信息接线修复并行中；暂无新模型或官网实验。

接续入口：原lab retry会重放08包，新建09/continuation-01的小manifest，独占复用09展开工作区，不重写旧cancelled记录。08:46:48控制器504947启动，使用provider-error-v1增量。接续前宿主事实评论已投递：GitHub Issue9 reply61产生comment67，Sheet Issue7 reply199产生comment211；不改对象状态/指派/应用，作为本地人工诊断介入记录。首次接线遗漏官方runner的uid:gid，Git dubious ownership拒绝启动，未发生模型调用；保留失败record，补齐原runner用户及环境后走continuation-02，不用safe.directory通配绕过。

## 热部署复核门（用户新增明确要求）

用户：“进行热修复部署前，和我确认本次你修复/改动了什么”。当前09及provider-error-v1已通过continuation-02启动，不能倒称尚未部署。自此所有新热部署先交本批清单/影响/恢复点/验证证据，取得用户确认后执行；02已启动运行保留，只读监控继续。已通知恢复负责人及廉价监控Agent不得自行继续替换、部署、投递诊断评论或重启新版本。repo AGENTS.md已补正向部署流程。

## 当前推进授权与新方案边界

用户复核问题树后明确：“基本都没问题，你可以推进；但不少地方只是初步指出修复方向……注意完善方案。”已列09修复、Braid职责归位、svc-sub-agents命名及接续参数候选可继续准备和实际接续；新的工作记忆治理方案另行补齐，不偷偷夹进本次运行材料。当前源码冻结braid-source-roles-v1.tar.gz（70e867ee3c3d1e19645c6907eb35c446e0b62ad11c7a774e1d9aa2088971c82d），Linux离线构建中。接续复用原展开目录；原失败尝试root生成的native归档和.arc结果仅改名保留，由原uid1000创建新文件，不改应用/Git所有权。
