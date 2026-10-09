# 完整需求的自主交付与可信验收

2026-09-28 两条官网 run 已按用户指示取消；根 Issue 与交付代码完成后，关闭项的联系回环阻止评分，证据、修复边界和重评验收见[交付终止 cell](cells/terminal-contact-loop.md)。用户已授权“修复之后，重新运行”；只用 `self_funded` 从保留工作区继续，不重新生成需求或动用参赛额度。

2026-09-27 GitHub 官网恢复运行的旧通知与成员身份冲突：见[只读诊断](results/github-recovery-assignment-conflict.md)。当前其他会话仍有工作，不以该局部错误判整次运行停滞。

2026-09-27 新一轮官网原工作区续跑的身份与证据在[实验登记](experiments.md#2026-09-27从取消前最后工作区再接续)。Sheet `bd7ac1b232ba` 已确认真实接续；GitHub g02 的根 Issue reset 被标为 blocked，保留终态后经 g03/g04 两次明确失败修复，g05 `435b79927a47` 已在新原生会话中继续根 Issue 的模型/工具活动，尚未完整交付或评分。当前不从需求重新生成，也不把 RUNNING 本身当作完成证据。通用官网断点恢复路径另见[实验基础设施任务](../experiment-infrastructure/packet.md)。

当前协作体验改进独立维护于 [协作体验 cell](cells/cooperation-experience.md)，包括自然回复交接与根 Issue 连续空闲五分钟的检查评论；当前源码已实施，真实运行证据与限制见该 cell。Context 重建时的[原会话自然收尾实施与验证边界](cells/context-reset-handoff.md)已有 Braid 源码接线，尚未用真实 Pi reset 验收。

2026-09-27 协作体验复核恢复：两份独立调查已取得并归档，见 [调查综合](cooperation-synthesis.md)。当前讨论全面协作改进的产品范围；已有通知局部修复与 Pi 恢复修复分别记录，不将其当作全面方案已实现。
用户补充确认交接通过协作提示完成：子任务完成后由 Agent 在父 Issue 评论，父 Agent 拆分时可明确该约定；Braid 负责普通评论的可靠投递。已有父项自动状态通知列入后续移除范围，尚未改动源码或冻结运行。

最新协作产品审计及架构/流程图：[协作体验再审计](cooperation-audit.md)。普通回复不要求补 @；关注关系和关闭后普通联系是本轮重点。当前仅审计及方案材料更新。

## 当前状态与下一步

2026-09-26，原迭代已获“可以开工”授权，Braid/SVC/浏览器工具及 pi-team-mixed 的主体修改已完成，尚未通过完整运行验收，未提交。
B Sheet 新证据暴露取消指派阻塞，用户已确认“让责任关系与执行资源彻底解耦”并允许进一步推进；补充具体方案与独立预演已完成，用户明确“确认，开工”，进入实现。
本次开工范围为指派生命周期 cell 的收尾/候选派发修复与 Factory 根提示删除，连同重新构建及已允许的本地验收；不包含提交和官网实验。
官网实验按用户要求暂停；B 的运行、现场和分析由用户负责，不监控、不恢复、不修改。

下一步按依赖顺序：

1. [指派生命周期 cell](cells/assignment-lifecycle.md) 已收敛收尾事务、每工作项候选、改派竞态及原生停止确认；Factory 根提示的删除范围已同步。
2. 已取得“确认，开工”；assignment_fix（gpt-6-sol/high）负责 Braid 和相应文档，主 Agent 负责 variant 提示、整合与实验。
3. 既有应用检查已接续完成并取回报告；主Agent独立检查发现oracle漂移及复跑范围过度声明，见results/method-check.md。
4. Braid 修复已实现并通过 cargo check；首轮启动的 schema 版本漂移修复后，冻结到 schema-fix/。用户改为先 Lite、通过后再 Hackathon；当前 GitHub/Sheet 已主动取消并保留现场，以同一ZIP启动Keep/BookStack，完整评分后先汇报。
5. 报告本轮完整结果及证据限制，由用户决定后续实验。官网恢复运行及源码提交均等待用户明确指令。

## 顶层目标与取舍依据

目标是在预算内提高无人值守完成完整 Hackathon 需求的成功率，缩短获得有效反馈和修复的周期。

| 要取得的结果 | 用来判断的证据 | 对应改动 |
| --- | --- | --- |
| 把整个任务做完 | 完整范围的推进、交接、集成与最终应用；中断有具体原因 | Braid 通信/Git/指派生命周期、variant 协作和交付 |
| 让完成判断可信 | 判据忠实于需求，能识别违约，证据对应最终版本和运行条件 | SVC V&V、整合 PR、自动化完整验收 |
| 让有效反馈足够便宜 | 检查编写/调试负担、有效失败、复跑与修复成本 | 现成浏览器检查工具、按需方法导航、模型分工 |

Issue/PR 数量、技能读取次数和脚本 PASS 数都不能代替以上结果。
语义和工作决策归 LLM；Braid 提供可靠的对象、上下文、通信和 Git 操作；SVC 提供可选用的方法。
多项改动的单轮实验只能观察整体效果，不能分离每项改动的净贡献。

## 已确认的决定

- 根 Issue 使用 GLM-5.3-Flash；原生 advisor 使用 Kimi-K3。子 Issue 和全部 PR 的负责人由 LLM 从允许成员配置中选择，Braid 不按阶段指定模型。
- 流程是需求分析 → 相互校正的技术与验收方案 → 实现计划与排障 → 实现和快速反馈 → 自动化 V&V → 合并和关闭。
- 工作流程放在 variant 成员的持续 instructions，通过 user_instructions → Pi append-system-prompt 接线；初始消息仅指向工作项。
- 子 PR 合入 develop；根关联整合 PR 将经过完整自动化验收的 develop 合入 main。Factory 只在 Braid 报告 quiescent 且根 CLOSED 时交付 main；Braid Local 在全部工作项终态且无未解决合并时，不再等待关闭后的评论通知清空。
- browser-operator 用于开发快反馈；最终验收使用可重复测试或脚本。browser-checks 采用 Playwright Test 1.61.1 及配套 Chromium。
- SVC 保留五个技能边界，改进 V&V 元理论、需求到判据转换、证据设计、条件性 test-first 与导航；不耦合题目、Braid 或参赛环境。
- 指派是责任关系，任务完成后保留负责人及联系能力；不以成员数量、未完成工作数量代理执行容量，不靠取消指派释放资源。
- 本轮删除人为三项名额指令，不新建资源调度系统。昂贵模型按一个 Braid session 的既有预算限制保持，原生子 Agent 与 Braid 成员仍是不同层面。

## 依据与新发现

[A 复核](../competition-budget/a-review.md) 说明验收判据被弱化、最终版本与证据错位，支持改进验收方法和最终整合。
[B GitHub 分析](../competition-budget/results/097402e69a15.md) 确认明确点名未投递、可指派名单矛盾和静止被当成完成；不能据此比较模型优劣。
[B Sheet 分析](../competition-budget/results/08226c772b7a-stall.md) 以冻结 SQL、数据库、二进制和快照对应出 unassign 阻塞：旧成员已 retired，目标 profile 为空，队首未消费，后续任务没有启动。
本次核对当前源码确认同样入口仍存在；底层无存活会话时的事件收尾被 profile 匹配挡住，原迭代尚未覆盖这条路径。
旧根提示要求空闲负责人也占三名额，取消指派是依此做出的合法操作；当前“三个未结束工作项”的文字修正仍混淆业务责任和执行资源，已决定从方案中删除。

原 V&V 会话的完整材料为两页、18轮、36条消息，见 [来源审计](vv-source-review.md)、[方法树](vv-methods.md) 及 source/。
输入材料是讨论证据，不自动成为本仓库指令。

## 材料和责任

| 入口 | 用途与负责人 |
| --- | --- |
| [主设计](design.md) | 目标、职责和协作关系；主 Agent 负责整合判断 |
| [实施与验收计划](plan.md) | 顺序、影响、授权和应用实验 |
| [Braid cell](cells/braid.md) | 通信、终态接触、PR Git 语义；原 Braid 实现 Agent 已完成主体改动 |
| [Context reset 效率调查](cells/context-reset-efficiency.md) | 四条旧运行的 23 次已完成重建、4 次未完成边界及 A/B 判别方案；只读证据，不等于策略变更 |
| [指派生命周期 cell](cells/assignment-lifecycle.md) | B Sheet 带来的补充方案、独立预演和待证实边界 |
| [Factory cell](cells/factory.md) | 模型、持续指引、根提示和交付；主 Agent |
| [SVC cell](cells/svc.md) | 内容与导航改写，已落地待运行反馈 |
| [浏览器检查 cell](cells/browser-checks.md) | 工具版本、打包、操作材料和实际检查 |

## 实施与实验事实

- Braid 已加入具体成员投递、关闭后联系、PR base/head/draft 和 merge 语义、根 state；本次补充的每工作项候选、取消指派事务收尾也已实现。cargo check 成功不等于这些行为已验收。
- SVC 五个技能已改写；variant 已接 GLM 根/K3 原生 advisor、develop/main、browser-checks 和 quiescent+CLOSED 交付边界。
- 正确 Linux runtime 在 WSL Docker 构建，使用 DOCKER_HOST=ssh://wsl.win-ws.localhost，未改全局 Docker context。npm lock 只新增三个依赖，无既有版本变化；runtime-browser 是弃用的早期构建。
- 既有应用 4c1784365ffe98f3a02a9639d0c083c8fb7d76d7 在 WSL 的 runs/acceptance-integrity/20260926/method-check/application 运行于4317，独立检查使用新 SVC/browser-checks 和 DeepSeek-v4-Flash/high，自带 key。
- 2026-09-26 check-writer.json 为 finished、exit_code=0，但原生末尾是 provider error：400 proxy_error / connection reset by peer（request id 2026092619191643468810135734），并非完整检查报告。产出 checks/issues.spec.ts、pulls.spec.ts、auth.spec.ts；Agent 最后公开摘要称16通过、8失败，尚未独立归因，不作验收通过。脚本和原始会话已取回 runs/acceptance-integrity/20260926/method-result，原WSL现场保留。
- 现有冻结 ZIP SHA256 为 423888113c6c43f7f75be51d9b6d9125075fee4184c45ae0350dc1e37bbd9b2b，路径 runs/acceptance-integrity/20260926/pi-team-mixed.zip；source-snapshots 保存对应 Braid/SVC 源码。此包没有取消指派修复，保留历史身份，不覆盖。
- 应用检查接续已结束，作者报告24/25并非可信需求通过率，证据与主Agent判断已归档。4317/4318两个本实验服务已停止；数据库与日志取回application-evidence.tar。为WSL腾出空间，已清理可从Mac恢复的本实验runtime副本及失败run的解包依赖；冻结ZIP、Braid二进制、数据库、原始错误均保留。
- 第一阶段已确认工具真实可运行，但发现textbox→searchbox的oracle漂移；两项独立产品检查都失败，详见[阶段记录](results/method-check.md)。方法收益未确立，完整配方沿已批准计划实测。
- 新包位于 assignment-fix/pi-team-mixed.zip，SHA256 bf55645e2c4ecfa414f963c6a92d0e12587d03b7e9cad97754b4bf9b9fe79a08；Braid/SVC源码记录在同目录source-snapshots。WSL首轮本地两题在启动前均失败：schema11迁移已应用，但DATABASE_SCHEMA_VERSION仍为9。实验目录assignment-fix/local-generation，github=job-0001-94253c478eba23，sheet=job-0002-5c625d1436fead，原始错误在各自template/.factory26/*/braid.log。没有模型生成或评分。已将版本常量改为最后一项migration的version，单一来源避免再次漂移；已以新包启动新本地实验，不覆写失败制品。生成应用冻结后才接公开需求代理评测，结果不能冒充官网分数。

## 授权与保持的边界

用户“可以开工”授权原 plan 的实现、既有应用检查与实验，未授权提交。
随后用户“先不要运行官网实验，可以运行本地实验”撤销本轮官网执行；目前没有上传、提交或启动新的官网 run。
用户在补充方案、独立预演与本地验收安排呈现后明确“确认，开工”，对应指派生命周期修复和根提示删除的实现与验收。
沿用约定：设计与验收方案复核 → 具体计划和独立预演 → 开工复核 → 实现与已授权验收。
不新增、维护或运行 Factory/基础设施/Braid 模拟测试、probe 或 SVC 内容测试；保留真实生成应用的检查与 benchmark。
不修改旧 A/B 的输入、现场或运行，不读取隐藏验收信息，不用代码阅读代替运行证据，不启动 scheduled task。
原生会话证据定向读取；长期运行用脚本等待和终态回传，不频繁模型轮询。

## 已取消的 Hackathon 验收

新包 schema-fix/pi-team-mixed.zip，SHA256 89452d2d9d602ef49fe3170498b5efdf4d07d724fdd09ac68e13619e4390d92f。
WSL实验为 /home/yyh/Development/factory26/runs/acceptance-integrity/20260926/schema-fix/local-generation；GitHub=job-0001-cc9e367fdb4fbf，Sheet=job-0002-9de9a1ed0fc1b6，max_parallel=2。
用户调整为先Lite后Hackathon，已通过lab stop取消两题（operation 8d77e1034a4b772cdede3d40），phase均为cancelled；没有本轮Hackathon评分。终态是用户主动停止，不能计为生成失败或零分。
已核对 WSL 中 lab.wait 进程实际存在（PID 242896），监听两条当前 run。
本地运行启动时遗漏 --listen-host 0.0.0.0，容器遥测不能到达回环接收器；已在 Docker 网关172.17.0.1:46431临时转发到原接收器127.0.0.1:46431（PID245842），两题的 traces/logs/metrics 均已实际入库。生成未中断；结束后停止该转发，下次启动直接传 --listen-host 0.0.0.0。
WSL磁盘曾只余140 MB。清理先删除本轮失败run的可恢复依赖副本，再将完整失败实验归档到Mac assignment-fix/failed-local-generation.tar.gz，通过gzip校验后移除两个失败run的workspace副本。WSL的journal、冻结输入仍在，源码、数据库、二进制及原始日志可从Mac归档恢复。
随后清理Docker未使用构建缓存，保留6GB缓存，释放4.159GB；未删除镜像、运行容器或其它实验现场。
一次性实验脚本 schema-fix/score-after-generation.sh 随取消退出（scoring.exit=1），没有启动71项代理评分。临时遥测转发已停止。清理取消run的可重建runtime依赖副本，原生会话、Braid数据库和日志保留。
停止前原生会话出现Request timed out及400 proxy_error/connection reset by peer；这是真实外部模型代理错误，不能归因于用户取消，也不能据此给应用评分。

## 当前验收：Lite 因宿主重启停止，待恢复

用户已确认宿主重启、网络恢复。WSL与原工作区可达，两题Braid local_run仍为running，支持以原request/profile/workspace恢复。外层Runner没有同等resume入口，lab retry会重新生成，因此本次使用runs中的一次性resume.py在相同镜像和/workspace路径运行冻结Braid二进制，保持原生会话、指派、Git分支及未提交文件；原cancelled记录不覆写，另建lite/resume-experiment记录恢复过程。达到原配方quiescent+根CLOSED条件后导出main，复用既有Lab应用评分命令，无需重新安装Runner或浏览器。
开发工作区期间已改名pi-braid；本实验仍使用原pi-team-mixed冻结材料，不重新打包，不混入之后源码改动。旧reviewer对照仍停止，不恢复。
恢复遇到两项事实：第一次容器用户不匹配，Git拒绝root访问UID1000仓库，已恢复原UID/GID；第二次Braid的materialize_next_context_reset无条件停止已丢失的旧内存句柄，导致两题blocked。assignment_fix完成有界独立预演，确认该处可沿其它恢复路径的is_managed条件继续既有reset事务，但仅靠无句柄不能普遍证明旧进程已退出。
本次宿主重启和旧容器销毁已经提供退出事实，因此仅在lite/recovery-braid冻结源码副本增加guard，编译恢复专用二进制；不修改原ZIP或直接推广到当前sources/braid。后续结果须标明恢复运行时修正。一般崩溃恢复的停止确认仍是待解决产品边界，不用此实验假装已修复。

用户指示：“可以先运行 lite bench，而不是Hackthon bench；lite bench 通过之后，再运行 Hackthon bench。”
使用同一schema-fix冻结ZIP（89452d2d9d602ef49fe3170498b5efdf4d07d724fdd09ac68e13619e4390d92f），WSL现有官方本地Runner、镜像和官方API自带key接线。
配方位于WSL runs/acceptance-integrity/20260926/lite/manifest.json，Keep/BookStack并行2，separate-evaluation；生成只读取需求，随后自动用既有Lite测试评分。监听绑定0.0.0.0，容器接172.17.0.1。
Lite先检查生成、交付、部署及完整评分是否跑通，再结合得分与行为证据判断是否适合进入Hackathon；不凭进程退出零认定通过，不臆造分数阈值。完整Lite结果先报告，Hackathon不自动恢复。
两题已实际启动：实验根lite/experiment，Keep=job-0001-6e16af60ec3591，BookStack=job-0002-b9fe4e2691470b，控制器通过lab --background启动；clean_replay_monitor已改为等待这两条run。实验身份同时保存在Mac runs/acceptance-integrity/20260926/lite/experiment.json。
用户要求WSL宿主重启前收尾。已通过lab stop停止两题（operation 5cd10e487cd7a245d305ad84），均cancelled、runner exit -2，controller-55b98ff32c95为finished，本轮容器已退出，监控已结束。这是维护停止，不计为失败评分；尚未取得完整结果。
WSL已sync，原文件保留；Mac备份lite/pre-reboot.tar.gz含控制器记录、两题原生会话、Braid数据库、Git仓库及未提交工作区、telemetry，排除可恢复依赖缓存。重启后先核对现场和恢复入口，再决定如何接续；不要把lab retry当作原生会话无损恢复，也不要无核对重复生成。
重启前发现容器1d8be64c895e，原误判属于其它会话；经tasks/acceptance-workflow/packet.md核实，其实是本会话早前独立reviewer对照实验。原生会话最后活动为11:25（UTC+8），22:00时active_turns=0、pending_events=3，运行标签不能证明仍在推进。已向用户纠正归属，并接管本次维护停止与现场保存，详见该旧packet的维护记录。
20:45（UTC+8）状态复核：已运行约30分钟，均仍生成、未评分。Keep有4个子Issue，基础Issue已关闭、PR#1合入develop，后续3项已在推进，4个活动执行；这是跨过首批交接的实际证据，尚不能证明最终闭环。BookStack有5个子Issue和2个OPEN PR（含develop→main整合PR），5个活动执行；原生记录出现两套基础提交6854da9/71e6a1c及接口差异，作为重复实现/衔接风险保留，未定根因。20:35前后多会话有官方代理timeout/400连接重置，之后仍有代码编辑、提交等操作，不能说整体停滞，也不能忽略API错误。WSL余4.7GB。


### 宿主重启后的恢复记录（2026-09-26 22:35 UTC+8）

WSL、Docker 与原工作区已恢复；旧 reviewer 和已取消的 Hackathon 保持停止。
原 Lite 取消记录、冻结 ZIP 与 Mac pre-reboot.tar.gz 保留。
Keep 重启前根 Issue 已 CLOSED、main 为 3c009124a279dcd322c979bd3eac5479bc9b8514，因此直接导出该候选，没有再启动模型。
导出记录 lite/keep-export/runs/job-0001-e5a3dddbb1c8d5 已完成；官方本地评分 lite/keep-recovered-evaluation/runs/evaluation-fa57360e5194c8 已启动。
这属于中断后候选评分，不追改原生成记录为成功。

BookStack 根 Issue 尚 OPEN，原状态恢复曾先遇到容器 UID 与 Git 所有者不一致，改为原 UID 1000 后，又遇到 context reset 无条件删除已丢失的内存会话句柄。
独立预演确认本次重启已消灭原容器进程；恢复专用冻结源码副本只在存在 managed handle 时执行 remove，保留原 store fencing 和 reset transaction。
此条件仅在本次确认旧进程已退出的恢复场景成立，不直接推广到 canonical Braid。
恢复二进制 SHA256 ac93e0855ed4bfc1f168c213b47a05cfa9e22d477f7ab4b7f44f5f86b10a8f71，仅替换 BookStack 留存工作区的工具；原 ZIP、canonical sources/braid 未改动。
源码与额外修改保存在 lite/recovery-braid；WSL lite/recovery-binary.json 保存前后哈希。
新恢复记录 lite/bookstack-resume-v3/runs/job-0001-a07b49c1485b8c 已启动。
自动评分脚本 lite/score-recovery-v3.py（PID 5655）等待恢复完成后评分，结果写入 lite/recovery-v3-scoring.json。
评分入口误把不存在的可选 selection.json 当成必需文件，已在本次隔离 code 副本修正为存在才使用；完整 Lite 用例保持不变。
clean_replay_monitor 已接管两题终态监听；收到完整评分后先报告，不自动启动 Hackathon。
恢复后的结果带有中断、恢复补丁条件，不能作为未中断的原冻结包基线。


### 命名规范接续

已查阅 [Variant 索引](../../variants/README.md)、[实验导航](../../experiments/README.md) 和 [命名迁移任务](../variant-experiment-naming/packet.md)。
当前源码入口为 pi-braid；pi-braid-coordinator、pi-braid-review 是独立实验实现，不自动视为同版本基线的单变量对照。
本轮已冻结的 pi-team-mixed ZIP、原始 run 和恢复记录沿用历史身份，不改名为 pi-braid，也不重新分配实验编号。
后续新实验先在本任务 experiments.md 登记 eYYYYMMDD-NN、问题、case、冻结输入、授权和完成条件；执行名使用实验--case--task--gNN（生成）或 rNN（固定应用复评），来源关联保留实际 ID 与摘要。
恢复同一执行沿用原名；新复评分配新执行名。当前历史批次的恢复/候选评分关系以上述实际路径为准，不追造新命名体系下的历史实验身份。


### Windows/WSL 维护协调（2026-09-26 23:10 UTC+8）

协调对话 01a0de34-4eaa-7072-8cc1-f4c3932929ea 授权只读盘点与 homelab 01a0ddee-95e4-7883-af43-d985fdf3dbb4 交换事实；未授权停止、清理或更改调度。
Keep 已完成官方本地评分 27/32（84.4%）；外层 failed/exit1 与内层 evaluation_status=completed 并存，不能当作设施失败重跑。
BookStack 容器41e563fa1668运行，控制器PID5326、自动评分脚本PID5655及等待PID5658继续工作。
维护窗口须等生成及评分终态、自动评分脚本退出、确认无待续任务，再把重启后新增证据备份到Mac；pre-reboot.tar.gz只覆盖重启前。
保留原始runs、冻结输入、ZIP、源码、原生会话、数据库与Git工作区，Runner镜像840105914e6e及恢复构建c2675bc945bc；Docker无volume。
两个退出容器analysis-e45与compassionate_bassi没有确认可删除；6.081GB build cache仅是待确认候选，不按Docker reclaimable标签直接清理。
homelab确认Debian根251GiB、使用235GiB、用户可用约4GiB，VHD位于D:\WSLDebian\ext4.vhdx，D盘机械盘仍余761GiB，优先评估虚拟盘/文件系统扩容条件。
Docker Desktop为另一引擎且承载其它项目；Factory实验空闲不等于整个WSL/Windows可重启。容量与停机方案由协调对话收敛并取得用户授权。

维护条件补充：homelab核实Debian根块设备为274877906944字节（256GiB），WSL2.7.14支持manage/resize。其依据的官方扩容流程要求先shutdown全部WSL，因此不采用仅停Debian的设想；需协调Docker Desktop及远程网络入口。建议容量512GiB尚待用户决定。停机后先冷备约240GiB原VHD，再扩容、验证；机械盘冷备耗时未知，不承诺短维护窗口。本轮仍仅调查协调。

网络盘点补充（homelab只读取证）：Windows host独占代理；Debian及生成容器无HTTP_PROXY类变量，容器禁用Python代理handler仍访问GitHub200。GitHub解析为fake-IP（198.18.0.54/fc00::36），WSL仅有fc00::/18路由、无公网IPv6默认路由，因此不能据此声称原生公网IPv6可用。未修改网络配置；维护后验证实际容器经既有路径访问所需服务。


### 用户调整目标并停止本轮（经协调对话转达）

用户要求以初步验收收益判断是否继续，明确授权核实恢复边界后暂停或终止，不再默认完整跑完。
Keep已取得27/32；BookStack根OPEN，五个子Issue三闭两开，最终develop→main PR未完成。最新status active_turns=0、materializing_groups=1、pending_events=868，无可靠剩余时长；事件积累原因尚未诊断，不能当作仍在有效推进。
BookStack develop=a22a1aa5de3d2956fe3b78b78089024e3637d7db，main仍51daa89d5c58b4af0d78b312a78b8e7d081415ca（种子）。不满足“应用全部生成”，保留部分实现而不生成伪完整评分。
已SIGTERM本任务自动评分PID5655及等待5658，lab stop operation f4c31614cdb4980924ad2037，bookstack-resume-v3为cancelled/exit-15。随后docker ps为空，未见本轮controller/wait；不自动恢复或排队新实验。
Mac备份lite/post-reboot-stop.tar.gz进行中，包含重启后Lite工作区、Git、Braid数据库、原生会话及评分证据，排除可恢复依赖缓存；WSL原文件不删除，必要镜像保留。
初步验收只支持Keep完成交付与评分、BookStack出现子任务集成；完整两题及BookStack最终交付未通过验收。Keep可用已冻结候选复评；BookStack只能显式选择develop的部分成果作诊断评测，恢复生成仍有会话物化问题，不承诺无损自动接续。
下一阶段官网实验仅讨论：先确认待验证问题、当前pi-braid具体冻结输入与本地恢复补丁的处理、题目/费用预算/自带key self_funded，再核对打包与比赛参与开关，用户批准具体方案后才能上传运行。禁止沿用official_evaluation或消耗参赛额度；本次没有官网写入。

网络覆盖修正：homelab后续强制地址族检查发现容器到198.18.0.54:443连续两次TCP超时，fc00::36则TLS/HTTP200；当前仅确认fake-IP IPv6路径可达，容器IPv4透明出网存在缺口，未确认丢包层。后续官网/本地可达性判断不得把默认HTTP成功解释为完整双栈正常。

收尾备份已完成：Mac runs/acceptance-integrity/20260926/lite/post-reboot-stop.tar.gz，822354167字节、11567条目，tar完整遍历与gzip -t通过；确认数据库、原生JSONL、Git objects、Keep评分报告及BookStack取消记录均在。已通知协调/homelab：Factory执行阻碍解除，未授权整个WSL停机；无自动实验排队，原现场及必要镜像保留。

官网下一步已具体化为[单题运行提案](official-next.md)：复用已冻结包，Hackathon GitHub一次，self_funded不参赛，沿既有模型；平台只读核查成功。新的付费执行授权、实际参赛语义/费用边界确认前不提交。

### WSL 扩容恢复完成（2026-09-27，homelab回报）

Debian VHD原地扩大至512GiB，ext4总503GiB/已用235GiB/可用244GiB，UUID未变；源VHD冷备SHA已核对一致。原生Docker26.1.5、SSH122及route unit恢复，Desktop原10容器恢复。Factory本地实验未重启，保护镜像840105914e6e/c2675bc945bc及工作区/bind源保留。原容器41e563fa1668使用docker run --rm，lab stop后自动删除符合预期，不是维护清理造成。容器IPv4透明出网缺口未修复；主机v4/v6 GitHub200不代表容器双栈正常。以上容量与服务事实来自homelab恢复验收，本会话未重复启动容器验证。

2026-09-27官网四题调查完成，见[因果诊断](results/official-four-diagnosis.md)。实际运行约51–99分钟，平台报告合计121.902018CNY；凌晨全终态而上午才获知，不是八小时持续执行。三题交接在独立线程缺收件人，根无wake；Keep唯一活动为PR复验，断连晚于根停止。GitHub强杀来源缺平台进程证据。未修源码/重跑/使用WSL，下一步先复核通用订阅与交接产品边界，SIGKILL单独取证。


2026-09-27 协调对话更新：先系统梳理 GitHub 协作体验，暂不实施或重跑。用户已接受同工作项跨 thread 通知原则；GitHub 官方行为由独立研究负责，本侧已整理 [Braid 当前行为基准](braid-cooperation-current.md)，涵盖动作、持久状态、收件人、投递、可见上下文及冻结版本边界。GitHub SIGKILL 原因调查已停止；既有 build 属于生成自验收，不满足完整交付应用直接复评的前提。


### 2026-09-27 当前执行阶段（覆盖此前官网重跑安排）

用户经协调会话授权已知通知缺口修复、针对性操作核查与本地恢复评分。当前不新建官网实验。
先从昨晚已保存的官网工作区只读原件建立恢复副本，Keep优先，随后BookStack/Sheet；GitHub单独核实恢复条件，不继续调查SIGKILL来源。
恢复保留原任务、原生会话和Git成果；历史漏发通知通过明确标记的新恢复动作补交接，不伪造旧事件。
并行消化两个独立GitHub/Braid调查，提出完整协作差异与需讨论取舍。全面协作改进经确认、实施完成后，才重新官网同包四题self_funded运行；不能把本次通知小修等同全面改进。
监控改为脚本计时/采集后一次性Agent内容审查，当时固定说明（现已删除），禁止Agent长驻轮询。官网版本脚本已编写但未端到端验证，暂不部署；本地恢复沿相同原则接线。
通知操作核查已通过：跨thread无@、重叠@去重、直接父项关闭/重开历史、重复close幂等、busy队列保留。实际provider消费仍待本地恢复观测；没有将检查等同完整bench。


2026-09-27 最新完整调度：四题同时在WSL恢复，优先关注Lite反馈，不是大题先跑。GitHub/Sheet为利用昨晚已付费成果，完成必要工作后直接官网应用重放取得官方评分；不从头生成、不为分数扩范围。全面协作改进之后才新开官网四题完整生成。复用策略已写入 [运行说明](../../docs/deployment/recovery.md)，固定一次性审查说明后来已删除。
首次本地启动恢复适配发现官网ZIP遗漏所有私人.git目录与执行权限；原始bare origin和工作文件、native会话完整。恢复v2只重建Git元数据，不覆盖文件，将未发布历史无法还原明确告知Agent；v2又因wrapper无执行位在模型启动前blocked，v3补回有shebang/ELF的执行位后接续，不重新提取或重生成。原始失败及每次恢复日志均保留。

两份独立调查已完整对照，形成 [完整协作改进讨论稿](braid-collaboration-next.md)。按实际工作链区分必须补齐、可裁减、Agent适配和未知；只是方案，不把review/checks/依赖等候选全部视为已授权实现。


### 2026-09-27 09:30 实时故障与证据摘要修正

09:27:32只读现场：Keep、BookStack、GitHub的recovery-v3已finished/failed，根Issue均OPEN、无交付receipt；Sheet仍有2个执行会话和2个pending batch。前三题不是完整评分结果，不制作半成品重放包。
停止前Pi原始JSONL反复记录stopReason=error/errorMessage=Connection error；Braid对应Pi settled with Some("error")。09:30左右WSL宿主与Sheet运行容器对https://api.arc-bench.com/v1/models的无凭据curl均在10秒DNS解析超时、HTTP000。已交homelab只读关联历史网络日志；当前DNS故障不直接证明所有先前连接错误同源。没有重启设施或再次恢复失败任务。
一次性审查第三批（monitor/20260927T011940.861473Z）确实读到原生工具输出、评论及具体事件，但采集器丢了空content的errorMessage，使其无法正确解释静止原因。现已保留错误字段，修正lab phase读取；另去掉JSON原文转义匹配的误拒绝，保留实际审查工具证据供人工复核；桌面通知改用真实Unicode。监控PID35448重新采集四题做一次审查，之后仍15/30分钟节奏。此次仅重启证据监控脚本，不影响模型运行或Docker。

监控新批20260927T012947.258396Z已完整结束并经主Agent对照：5次实际证据读取，三题Connection error及未完成对象、Sheet具体Toolbar写入均与独立WSL检查一致。primary-review.json记录内容核验与限制；outcome.json与alerts.jsonl已落盘，桌面通知提交exit0。监控将前三题记为本attempt终态，Sheet按30分钟继续采集；这不表示实验目标完成。新的恢复attempt须在网络确认后重新登记与接线，避免done集合误用。

网络分层（homelab只读回报）：默认网关DNS172.29.144.1对api.arc-bench.com/github的UDP/TCP查询超时，223.5.5.5/1.1.1.1查询可用但可能仍经TUN。保留TLS域名、固定已验证fakeIP后，WSL与Sheet容器v4/v6均收到官方API401，TLS约0.4秒；当前指向DNS网关路径，不是全面API传输中断，真实模型请求仍待验证。维护线程核实规则作用域，尚未改resolver或防火墙。
用户经协调对话更新：模型网络恢复后优先完成四题，不重复确认既有实验授权；发现新的Harness缺陷先保留现场并讨论方案，再实施。前三题已失败停下，Sheet继续；未自动修复顶层quiescent诊断表达，也未盲目重跑。

09:43维护窗口更新：第二次GLM真实请求在01:41:53Z开始，10.034秒报errno -3解析失败；随后新容器实查resolv.conf已经回退172.29.144.1。维护侧确认运行WSL尚未加载generateResolvConf=false，自动恢复旧symlink。已撤回网络恢复判定。四题finished且docker ps为空，全部探针结束，Mac采集器35448已停止；四份before-dns-resume归档完整读取确认DB/origin.git/native记录。已向homelab释放仅Debian terminate/start窗口，不shutdown全WSL、不动Desktop/sing-box。待跨重启和采集入口验证配置不回退后，重新真实模型验证再接续。

09:52恢复启动：维护侧实际09:50定时采集和09:51二次入口确认resolver未回退；真实GLM Flash 78.461秒HTTP200完整SSE、DS Flash2.337秒HTTP200完整SSE，见network/post-reboot-model-request-result.jsonl。通过既有CLI给四题根Issue新增网络恢复交接并@开放工作项负责人，原评论/事件不改。使用同一脚本、恢复二进制、镜像和保留工作区启动recovery-v4四题并行；recipe-dns-resume.json逐题关联v3源路径。未改Harness源码。监控已改读v4、旧scheduler保留为local-scheduler-v3.json，新一轮15/30分钟节奏；稍后验证实际会话动作，不将controller启动等同恢复成功。

09:56启动核查：v4四容器running，但尚无braid-resume.log或新native动作，不能称模型已恢复。四个恢复Python进程D态(folio_wait_bit_common/wait_on_buffer)，具体Keep fd3停在work/skills/ponytail/LICENSE读取；vmstat I/O wait约41%，磁盘239GB可用、内存7.8GB空闲。已交homelab只读查存储层，暂未确认Harness缺陷，不改源码/不重启。完整四题新run ID见runs/e20260927-01-handoff/package.json的dns_recovery。

09:58实证：Keep/BookStack各2个active Pi，Keep对develop 9b883a4发起构建和最终自动化验收，BookStack接续Page/Chapter保留代码与检查脚本。GitHub/Sheet尚在准备，09:59 Sheet已有4个pending batch，未据此声称生成完成。已复用原score-recovery-v2.py建立v4 Lite终态后评分，WSL PID5625，只在恢复结果completed时运行官方Lite本地evaluate；源run失败则记录错误不送评。新监控PID41923，旧证据保留，未修改运行中Harness。

10:01四题均有Braid日志，Keep2active、BookStack1active+1pending、Sheet4active且有真实工具动作；GitHub进入3pending，尚无新native回应。homelab只读采样：Debian VHD位于D盘机械HDD，根盘sdf读均约82.7ms/写均885.6ms、busy约100%，I/O pressure下降且四恢复Python均已S/do_wait。只确认高存储等待，不断言冷缓存或硬件故障；未改存储配置。

GitHub恢复缺陷进入待讨论：根#1/#4的已知会话get_state超时被CreatedWithoutIdentity包装，继而物化失败、provider/agent/assignment三层blocked，assignment写retired_at且被恢复候选排除。GitHub容器已docker pause保留#5成果，其余三题继续；暂停归档25,112,317字节完成。已整理[证据与最小修复/接续方案](results/github-resume-timeout-plan.md)，包括冻结源码行、实际状态、避免2秒无限重试、旧两条投影的有审计修复及真实Pi验证。未修改Harness/DB或解冻，待用户讨论。

2026-09-27 用户明确“同意这个修正，修正之后恢复 GitHub 运行”。本阶段获准修复 Pi 已知会话恢复超时分类、同进程重试边界，对 #1/#4 的误阻断投影做有审计记录的定向修复，并沿原工作区恢复 GitHub；验收仍是完整交付及获授权的 self_funded 应用重放。无需重新授权本范围，不提交源码或新开完整生成。

实施中发现独立的原会话路径缺陷：DB 记录的路径无文件，`resume_home` 找到 `sessions/` 子目录中的真实文件，但 Pi 仍收到旧路径。隔离副本中，旧路径 `get_state` 的 session ID 与原文件不符；改用真实路径后根与 #4 均一致。已完成超时分类与同进程单次尝试源码改动、Linux 构建及无模型受控超时检查；旧 GitHub 容器在原件归档后结束，recovery-v4 因主动 SIGTERM 失败收尾。真实 DB 仍保留 blocked，未应用修复事务，也未启动 recovery-v5。按用户此前“新 Harness 缺陷先保留现场并讨论方案”的约定，待复核[路径修复方案](results/github-resume-timeout-plan.md#实施中发现传给-pi-的路径并非原生文件)后继续。

用户随后明确“好的，追加这个局部修复”。现获准修正真实文件定位与 Pi `--session` 实参、保持 Braid 稳定会话 ID/通知键，并在隔离副本验收后执行已批准的状态修复与 GitHub 接续。没有授权提交源码或新建完整官网生成。
