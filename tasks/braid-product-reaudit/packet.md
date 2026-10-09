# Braid 第二轮产品复审

公开树保留本任务的复审结论和实现说明；cells 中的生成统计、原始回包和分析脚本已移除，可从 Git 历史按提交恢复。

最新追加调查分工见 [分析派单](cells/analysis-dispatch.md)：Astra 负责 token 与 GitHub 最小协作体验复审，6-Sol 负责未闭合证据追查；平台线程上限下复用现有成员。

当前状态（2026-09-28 10:43 UTC）：continuation-03从09:20接续约83分钟。GitHub在10:10完成生成并交付c3fb22d，评分被“两题全部生成完”的控制器屏障延迟；Sheet10:38合并PR20，仍在REQ-3跟进与最终整合。暂无新证据表明P0阻塞。详见[进展与耗时](cells/continuation03-progress.md)、[增量token](cells/continuation03-token-profile.md)。控制器509773、监控510138保持运行；本次只读取证，未部署新修复。
新补充的[工作记忆整理方案](cells/context-curation-design.md)已给出具体操作/落点/验收，尚未部署。原01/02失败、余额429及下文历史过程保留事实，不代表03仍失败。


状态：2026-09-28 用户已授权应用修复，进入实施与真实运行验收。前一阶段仅调查；以下原始审查记录保留其时点边界。

当前运行入口：[08热修复清单](cells/hotfix08.md)。[09热修复方案](cells/hotfix09.md) 已获开工授权，源码与Linux Braid已完成，08通过既有入口停止并保存完整半成品；09两题恢复包已准备，控制器PID490689已启动并出现新原生活动，但BigModel根GLM持续额度429。已决定用既有stop停止09保留最新成果，等待用户解决路由额度；09停止收据待补。
当前分工：主 Agent 负责边界判断、Factory 指引与接续集成；live_deep_diagnosis 完成对象层修复后调查 Issue/PR 独立实施缺口；vision_root_cause 完成 telemetry 修复后构建 Linux Braid；browser_guidance_apply 完成 SVC 迁移和普通包，继续准备09恢复控制器。用户要求已明确根因的各支线一并解决，根因不明项保留证据继续调查；历史分工不代表当前待办。

本轮的结论是维持已经收敛的产品模型，不再建立新的阶段、消息分类器或执行模式。四项已批准修正方向自洽；优先处理当前产品承诺与入口行为之间的矛盾，以及尚未闭环的成员身份错误。追加真实协作证据表明，普通消息等待长执行结束才送达仍是产品缺口，应复核工作期间按批次进入原生输入的承诺。其它新建议只涉及说明收件与结束边界，不自动把根关闭升级为新结束模式。

新增上游审查：[Braid 产品价值审查](cells/context-capability-coverage.md)。用户指出我们不应只沿功能采用率检查：顶层是工作记忆、多Agent协作、设计实施分离是否提供实际收益或增加代价。官网/本地并行复用已有证据，机制调用仅为解释结果的一层。09接续照常推进。

恢复点决策：[恢复点复核](cells/recovery-point-review.md)。暂不退到06/07；07→08保留了GitHub22、Sheet39个develop提交。三条具体状态的[宿主事实交接草稿](cells/recovery-handoff-draft.md)仅供接续前审阅，尚未投递。当前先解决BigModel额度429，再纠正具体责任/验收状态。用户已明确补充BigModel余额；08:37:57 UTC同路由一次最小请求HTTP200。保持原配方，修正错误漏报后从09最新停止工作区接续，优先复用已展开材料。

当前复核入口：[09问题→职责→修复→状态树](cells/hotfix09-problem-tree.md)。角色职责已归位Braid源码，技能名按用户决定改为svc-sub-agents；不因内容获认可自动部署新版本。

新增协作缺口：[PR closing keywords](cells/closing-keywords.md)。已确认当前无正文关键字解析、合并仅记关联活动而不关闭 Issue；需按 GitHub 的默认分支合并语义修正，不能把普通关闭或任意分支合并等同关闭 Issue。尚未改实现。

2026-09-28 用户明确授权：GitHub立即单独应用重放上传官网，以self_funded评分；后续每题独立采用同样流程，不等Sheet。来源03交付c3fb22d；重放ZIP SHA256 3b4acdcaee785ef13ab135441ea65404884b697684af06026281c2a7324e706b，journal：runs/e20260928-02-deepseek-direct/attempt-09/continuation-03/github-official。官网run已启动：https://arc-bench.com/runs/3583c4dd7e48 ，submission 818851321657。Sheet继续生成，隐藏评测反馈不回灌生成会话。

本轮新增[分析分工与待追查清单](cells/analysis-dispatch.md)：用户指定Astra分析token和GitHub体验缺口、6-Sol追查环境与协作耗时。模型和实际派发状态分别记录，不能将排队任务称为已运行。

用户已通过协调任务授权[token根因修复实施](cells/token-fix-implementation.md)。主处理Pi一次性Context注入，6-Sol处理终态通知批量/可行复用，Astra继续GitHub体验审查；运行材料未替换。

GitHub03官网已终态：3583c4dd7e48，16/100，功能5/47，self_funded，三阶段completed。用户授权独立按原始需求实际使用冻结应用诊断；Astra接续至tasks/github-score-diagnosis/continuation03/，不修改应用或重生成。token修复继续。

## 范围、权限与基线

用户要求先复审产品需求和行为，再审技术实现。Braid 负责 GitHub 式 Issue/PR/comment、可编辑 Context、明确身份及异步投递；LLM 负责语义、工作方法和应用完成决定。成员不是 Profile，责任不是执行容量。根五分钟检查保留；Pi 原生子代理由 Pi 管理。

原始审计阶段仅授权调查与 task packet 整理；后续用户已授权实现及 DeepSeek 半成品恢复，范围和分工以下方“本轮开工与分工”为准。

Braid HEAD 为 `89212933c976b889f27de1b8cfe863baf8f6042e`，工作树含既有未提交改动。具体读取基线见 [baseline.json](baseline.json)，不能用 HEAD 单独代表本次实现。输入材料为上一轮 [产品审查](../braid-architecture-audit/product-review.md)、[产品模型](../braid-architecture-audit/product-model.md)、[技术发现](../braid-architecture-audit/findings.md)，以及 [hardening packet](../braid-product-hardening/packet.md)、[iteration](../braid-product-hardening/iteration.md)、[Context/通知单元](../braid-product-hardening/cells/context-notifications.md)、[生命周期单元](../braid-product-hardening/cells/lifecycle.md)。

## 交付与恢复入口

- [产品复审](review.md)：用户工作流、已经修正的旧发现、最小产品建议与待复核范围。
- [技术核对](technical-followup.md)：产品结论之后的确定性矛盾及后续判据，不声称已经实施或验收。
- [成员冲突证据](member-conflict-evidence.json)：独立只读打开历史 ZIP，保存日志计数、具体事件和 SQLite 查询；原归档未改写。

产品建议已经用户复核并授权实施。全对象终态仍是当前已选范围，根单独关闭结束的新模式没有被采用。历史 21,206 条唯一键错误单列未闭环；新版本的通知量、费用、墙钟或应用质量收益也没有本轮实测。

追加输入：主线提供 [新 run 证据](../braid-product-hardening/cells/live-run-evidence.md) 和 [共享契约投递链](../experiment-infrastructure/cells/shared-contract-braid-causality.md)。已纳入产品复审第 3 项及技术 T4；新原生错误尚未闭环归因，不扩大缓冲区或修改冻结输入。


## 用户追加事项总览（2026-09-28）

此表是本轮接续入口；详细材料仍分布在各 cell，不复制成一份大报告。
“实现完成”与“运行验证完成”分开记录。

| 用户要求 | 责任人与当前状态 | 材料／剩余工作 |
| --- | --- | --- |
| 发现运行缺陷后及时修复，保留半成品接续 | 主 Agent；attempt-08 已保留07半成品真实续进，4GiB/2CPU不变 | 07应用视觉分工、技能辅助工具、恢复用量与采集减负；尚无新评分 |
| 再做 Braid 产品复审及技术审查，应用简化 | 主 Agent + braid_apply_review；审查及修复已做，实际恢复暴露的新缺陷继续闭环 | review.md、technical-followup.md、cells/termination-contact.md |
| description/comment/thread 指引；各 Issue 工作方法是否落实 | 指引已修改；browser_guidance_apply 已收集逐项证据 | live-workflow-evidence.md；有局部设计产物，但没有证明全链路普遍遵循 |
| 环境排障进一步细分；核对 agent-browser 技能与易用性 | 独立取证已做，浏览器指引已修正 | browser-guidance-implementation.md、../github-score-diagnosis/environment-cost.md、../sheet-score-diagnosis/environment-cost.md；旧运行零调用不能证明工具不好用，新文案未进入本次保留的旧原生材料 |
| 共享契约冲突中 Braid 混乱／冗余的影响 | contract_causality_followup（gpt-6-sol/high）已完成补充分析 | ../experiment-infrastructure/cells/shared-contract-braid-causality.md；已证明初始决议读后偏离、后续两条纠偏排队；确认有冗余回执增大输入，但未证实挤掉关键裁决；reset后裁决可见且被复述，不给百分比归因 |
| 实验设施更好用，独立 OTLP、token/耗时与原始错误入口 | 主 Agent + browser_guidance_apply；已实现实时页面与恢复接线，独立跟进07 Collector超时 | ../experiment-infrastructure/cells/live-diagnostics.md；不能用旧快照页面证明新采集正常 |
| Harness 预制应用检查脚本可放在 Agent Skill，不写入生成应用源码 | agent-browser/scripts/with-service.py 已实现，在Sheet后端副本实际取得HTTP200与check exit0 | ../experiment-infrastructure/cells/live-observability-followup.md；可选工具，无业务判据，不重建browser-checks |
| 上次官网 Issue/PR 重建为 GitHub-like 页面 | 已完成 | ../../runs/official-collaboration-review/index.html |
| Qwen/MiniMax 各模型 session、输入/输出/cache token | 独立分析完成，使用停止前时点 | ../experiment-infrastructure/cells/flash-deepseek-process-comparison.md；cache=0 仅代表原生报告值，非实际账单 |
| 停止 Qwen/MiniMax，比较 DeepSeek 进展和用量 | Qwen/MiniMax 两题已取消；对比完成 | 同上；DeepSeek GitHub 尚无 DeepSeek 成员参与时，不能冒称模型效果对照 |
| 视觉解读应由合适sub-agent承担；全面核查子角色 | live_deep_diagnosis 完成全景账本；主 Agent 已写入口修正，vision_root_cause 打包08 | ../factory-subagents/cells/usage-map.md、native-discovery.md；3完成vision、1未完成executor、4启动前失败；修正尚待08真实使用 |
| 官网及当前本地两题token消耗与优化空间 | live_deep_diagnosis独立分析；主线继续热恢复 | ../experiment-infrastructure/cells/token-economics.md；best-effort，未知不计零，悲观情景与事实分开 |
| 后续补充交给 sub-agent，主 Agent 保持主线 | 正在执行 | 主 Agent 负责 Braid 修复、集成和恢复；补充诊断单独委派，不把调查完成误作修复验收 |

## 本轮开工与分工
用户：“这个指引冲突应该去修复；应当在合适的提示词中提示使用 agent-browser；找到的 Braid 简化重点也应当应用。”随后明确要求委派实验设施改进。
授权包括发现故障后定位修复、重新打包并基于已有半成品接续运行；保持已有四题矩阵和模型路由，不消耗参赛额度。
主 Agent 负责普通消息接收、Pi busy/lag 因果核对与修复、description/comment/thread 指引、实际工作流程审计及最终接续。
独立 Agent braid_apply_review 负责统一退出、历史不可达输入收尾及针对性 Braid 验证。
独立 Agent browser_guidance_apply 负责浏览器指引及工作方法入口核对。
独立 Agent live_runs_evidence 转负责实验设施：实时 token/耗时入口、故障证据定位、现有监控接续；主 Agent 接手实际运行分析。
实施复用现有队列、原生 steer、诊断页面和监控脚本；不增加消息语义分类、Pi 子代理生命周期管理或生成应用源码。
验收用 Braid 针对性验证和当前真实运行，Factory/设施/Corpus 不添加测试。先保留现场，冷恢复时替换宿主运行材料且保持原 Git/对象/原生会话证据；新产物及来源另记，不覆盖原冻结输入。

用户后续明确停止 Qwen/MiniMax 配方：WSL e20260928-01/attempt-02 两题已通过 lab stop 取消，工作区保留；不自动重启该配方。
DeepSeek e20260928-02/attempt-02 两题继续，修复后的半成品接续仅对仍获授权的 DeepSeek 矩阵进行。
停止前用量与进展对比由设施子 Agent 完成，见 ../experiment-infrastructure/cells/flash-deepseek-process-comparison.md。

## 实施进展与本轮证据入口

- 浏览器指引已应用；见 browser-guidance-implementation.md。仅修改共用技能及活动配方材料，冻结旧输入未改。
- Braid description/comment/thread入口说明已修正；工作方法仍归variant/SVC。
- T1/T2与明确拒收重放已实施，定向验证及真实旧DB副本结果见 cells/termination-contact.md。
- 普通运行中输入沿现有批次steer，收据只表示原生接收；见 input-delivery-implementation.md。Store定向检查通过。
- Pi收据/状态锁/通知广播修复及8项定向验证见 pi-delivery-lld.md；原生迟到steer窄竞态边界明确保留，不使用退出兜底补丁。
- 各Issue实际方法产物见 live-workflow-evidence.md，完整原始对象切片为 live-workflow-snapshot.json；没有将方案标题当成已经完成全部流程。
- ds vision调用与需求整理时序见 vision-requirements-evidence.md。
- Linux编译和DeepSeek半成品恢复打包已完成，attempt-03已启动；沿用原模型/需求/责任记录，使用新Braid。浏览器技能改动不冒充旧原生材料已生效。
- 冷恢复Collector/timing接线与实时剖面已实现并冻结在attempt-03；实际恢复后的新遥测仍需运行证据。

DeepSeek切换：旧attempt-02两题已通过lab stop确认cancelled，仅为授权修复接续；原工作区完整ZIP保存到attempt-03/{github,sheet}-workspace.zip，保留本地.git和Unix链接。
新Linux Braid在WSL使用缓存rust:1.93-bookworm中已有1.93.1工具链编译通过（仓库rust-toolchain指定1.93.0会触发下载，已显式使用已安装的同系列补丁版本），产物attempt-03/braid-linux。

恢复attempt-03已启动：controller PID188716；GitHub pi-braid--hackathon--github-48681390d16c89，Sheet pi-braid--hackathon--sheet-8b17a98231417f。
GitHub恢复ZIP 70d9715533a35c97fc2c421789ff0e6e9b80c26f3b563fab7bc64b9864e8db17；Sheet ff3efe48dde242b9bbb2e688ee350d285ddbafead1451e0c95a05d45ab30601c。
Braid Linux a171d5cb67ed694bb45872fe05de393e6c71c15ffe13bb7b8eec8543b3c0a77d，源码ad688ae4c8c12959b9e1465e8f018047f22df4186eb8226b2c71b4235ea0e647。
原生模型/指令材料保持原请求，因此本次续接验收Braid和恢复采集，不把新的agent-browser技能文案视作已进入旧会话。
冷恢复完整接续与评分尚待实际证据。监控已委派deepseek_recovery_watch，gpt-5.6-luna/low，程序采样180/480秒，新故障回报。

03:57 UTC：两个恢复入口Python仍在运行，尚无新Braid/Pi活动证据；GitHub进程等待磁盘读取runtime依赖文件。已委派设施Agent诊断启动IO，监控Agent继续核查新会话活动；不以旧快照或容器存活判定恢复成功。

## 热修复 attempt-04（用户明确授权）

用户：“同意，应当移除 browser-checks 独立技能及其强制注入（使用热修复）”。
两条 attempt-03 均因 instruction revision 改变后错误阻断 assignment、再以同 member_login 物化导致唯一键冲突而失败；不是模型完成或评分结果。新 OTLP 确有 logs/traces/metrics 入库，单条 capture timeout 的丢失范围未知。
本次从已停止 attempt-03 最新完整工作区接续：保留应用、Git、Issue/PR/comment、成员身份和模型路由；修复 Braid 的原生会话重建边界，刷新宿主提供的技能、成员/子角色指令与启动材料，移除 browser-checks。旧材料与快照保留，重新冻结到 attempt-04。
assignment_fix 负责恢复边界及针对性 Braid 回归；browser_guidance_apply 删除技能和消费者；live_runs_evidence 复用已有 runtime 制作新普通 base package；主 Agent 负责恢复入口材料刷新、打包、运行和实际新活动确认。
“热修复”在本项目指新 Harness + 保留半成品的停止后接续，不是替换正在执行的进程内代码。不重新从需求生成，不自动启动已取消 Qwen/MiniMax 配方，不提交源码。

热修复接续入口现在支持显式刷新原生材料；重复workspace哈希改为复用已校验manifest，恢复阶段输出具体进度。来源.arc保存到recovery-source-arc，保留新runner自己的事件文件；已确认旧恢复会混入590/654行前次运行事件。原始ZIP不改。

2026-09-28 04:20 UTC 左右，attempt-04控制器PID194714已启动，来源为attempt-03两题最新完整工作区。新Braid SHA256 5fa3631bdcd6aecc1674a1bb67e3dfc7095cbd0f66bc81ad804ec994e3d2eba8；源码70e7fa8eaec6cdd101906ddaabc76f0b8e68c9466d5026968e0b060582e1c0fe。
GitHub热修复ZIP e13d8c702338b7064684638a2db2306b8cea660b4c5945bdcee461d766b4f80f；Sheet 22ffdb80a16e0f1d093c80b33f976656f4f2ee6632b37494681da7f8a06a4e22。两包显式refresh_native_materials=true，来源记录保存于runs/e20260928-04-hotfix/{github,sheet}-package.json。
两个原member身份恢复的Braid针对性回归已过；真实模型续进仍待确认。低成本deepseek_recovery_watch接管新attempt监控，只认新时点证据，不启动旧或已取消配方。

2026-09-28 04:20 UTC：确认 attempt-04 两条 run.json 已生成：GitHub `pi-braid--hackathon--github-cd96acb2188357`、Sheet `pi-braid--hackathon--sheet-bb12af664cce56`。未发现重复监控；已启动既有 `monitor-generation.py`，Python PID 194802（父 shell 194801），采样证据为 `runs/e20260928-02-deepseek-direct/attempt-04/generation-monitor.jsonl`，日志为同目录 `monitor-generation.log`。首条采样两题均为 running，尚无 agent 状态、runner 退出码或收据；继续只读等待新 Braid/Pi/OTLP 或明确终态。

2026-09-28 04:24 UTC：attempt-04 在生成阶段出现明确恢复故障，尚未产生可验收的新模型消息或工具调用。两题各自新的 `execution.debug.log` 均显示恢复已完成“restoring retained workspace”并在 native 刷新阶段因 `/workspace/submission/agent/agents/._pi-deepseek-fast/profile.json` 为非目录而 `NotADirectoryError`，generation-agent exit 1。此前 `recovery-braid.log` 中的 `assignments.member_login` 记录属于恢复 ZIP 保留的 03:58 旧日志，不能归因于 attempt-04 新阶段；本次诊断已修正为按错误时间与阶段核对新日志。

2026-09-28 04:33 UTC：attempt-05 两题均完成 runtime/native 刷新并进入 `resuming Braid`，随后生成阶段 exit 1。GitHub 新 `recovery-braid.log` 在 04:33:24 记录 `result="blocked"`；Sheet 新日志在 04:33:36 记录同样的 `local run blocked`。监控采样显示 GitHub native sessions=2、Sheet=9，但当前证据未确认本轮新的实际模型消息/工具结果；不能把 session 数或旧 JSONL mtime 当作新活动。

2026-09-28 04:50 UTC：attempt-06 首次有效恢复活动已确认。既有监控 PID `199628`，证据 `runs/e20260928-02-deepseek-direct/attempt-06/generation-monitor.jsonl`；采样显示 GitHub Braid `active_turns=2`, `pending_events=7`, native sessions=4 且 newest_age=5s，Sheet `active_turns=7`, `pending_events=0`, native sessions=16 且 newest_age=2s。两题新的 `execution.debug.log` 均记录本轮 `Recovery: resuming Braid`（GitHub 04:49:39、Sheet 04:49:53 UTC），状态仍 running；这确认 native 恢复后有实际新时点活动，尚未终态。

补充核实：GitHub 恢复后 native session `2026-09-28T04:49:47.690Z...jsonl` 在 `04:50:04.164Z` 写入 assistant 消息，包含两个 `bash` 工具调用（查看工作树与 Braid comment）；Sheet 恢复后 native session `2026-09-28T04:49:57.782Z...jsonl` 之后已有 assistant/tool 活动，采样中的 active turns=7。只记录时间、角色与行为，不抄录长内容。两题只读 SQLite assignments 均保留原 member_login：GitHub `glm-1`/`glm-2`，Sheet 包含既有 `glm-1`、`glm-2`、`deepseek-*` 等成员，未见本轮唯一键冲突。

2026-09-28 05:30 UTC：attempt-07 两条新 run 已确认：GitHub `pi-braid--hackathon--github-116b6cbc63dc5c`、Sheet `pi-braid--hackathon--sheet-28ca9afab308e8`。既有监控 PID `231787`（父 shell `231786`）已启动，首采样两题均 running。execution.debug.log 显示 GitHub 05:30:27、Sheet 05:30:27 仍在 `Recovery: verifying packaged runtime and workspace` 阶段，尚未确认本轮新 Braid/native assistant/tool 活动；继续按 180/480 秒采样。

2026-09-28 05:36 UTC：attempt-07 已完成恢复并确认真实新模型活动。监控采样显示 GitHub `active_turns=7`, native sessions=13, newest_age=0s；Sheet `active_turns=7`, native sessions=24, newest_age=0s。新 native JSONL 中 GitHub assistant/tool 活动从 05:33:56 UTC 开始，Sheet 从 05:33:35 UTC 开始，均晚于本次启动。`docker inspect` 核对两 ARCBench 容器均为 memory `4294967296`（4 GiB）、NanoCPUs `2000000000`（2 CPU）。当前两题仍 running；未见本轮错误。

## attempt-04 包污染与 attempt-05 接续

attempt-04 两题分别04:24:11/04:24:32 UTC在native_files报NotADirectoryError：传输混入的agents/._pi-deepseek-fast被当作成员目录；未进入新Braid、没有模型或应用进展。Sheet旧recovery-braid.log中的03:58唯一键错误属于恢复来源，不能归于新执行。
共享打包入口现在过滤AppleDouble/macOS元数据并同步manifest，stage同样清理；传输使用COPYFILE_DISABLE=1 tar --no-xattrs。旧包保留；attempt-05重新包装，继续使用attempt-03的最新有效半成品、新Braid与同一模型路由。恢复来源的旧Braid/Collector日志另行归档，当前路径只表示本次恢复阶段。

attempt-05已启动（controller PID196466）。实际ZIP目录检查两包均metadata_entries=0、browser_checks_entries=0、refresh_native_materials=true；GitHub SHA27bdd6376d7cd419b8cc236bd82b6cba1ca0a7db6874af74c8f681df02385c69，Sheet SHA8c652339d0e403ea694e2bb81799d4a268fbbba7271c64df1688f90a476f0298。Braid及模型配方不变。等待新会话实际续进证据，不以容器或Python启动判热修复完成。

attempt-05两题进入新Braid后仍blocked（04:33:24/04:33:36 UTC）；这次没有重复member_login错误。真实DB显示已applied reset的新PS/agent idle，但旧assignment仍blocked，另有materializing reset尚未完成。新的生命周期修正将在offline入口和reset完成事务维护同一成员状态，并等待driver初始化及pending reset完成后再判断blocked；正在以05真实DB副本验证。
attempt-06已冻结05完整工作区作为最新半成品，保留新指令材料及旧协作记录；等待最终Braid补丁通过上述验证再编译和接续。用户授权不变，Qwen/MiniMax保持取消。

用户追加要求：“在你完成恢复之后，请使用树状视图进行阶段性汇报与整理（仍然从上一次官网运行结束开始算起）”。材料由iteration_report_materials（gpt-5.6-luna/high）整理，主线恢复后综合；不把这次browser-checks移除当成全部迭代范围。
06候选Braid已在05 GitHub/Sheet真实SQLite副本验证offline入口与reset完成事务的状态闭合，另cargo check与定向Braid回归通过；副本虚拟native session仅验证存储事务，不宣称真实模型验收。最终源码已冻结并开始Linux编译。

attempt-06已启动（controller PID199559）。Linux二进制9b489308beda28950403b27dc09b6aae0911f6368738316785810104f018de0a，源码052b2b7233f921d2a0265b81dde18ee06af721aa8228166c313cb0b248244828。两个新包再次核实无macOS metadata/browser-checks，refresh_native_materials=true；source_run_id分别指向05的github-470b59e7eebba8、sheet-d40c0b57bb4a78。包来源记录保存在runs/e20260928-04-hotfix/*-package-attempt06.json。低成本监控等待实际新Pi响应或本次故障；尚未报告成功。

阶段汇报已同步到 [iteration-report.md](iteration-report.md) 与 [总图入口](../iteration-map.md)。attempt-06 已由恢复后真实 assistant/tool 消息确认续进；报告保留未完成评分与观测收益边界。

## 热观察与快速修复（2026-09-28，用户授权）

用户明确要求：现在深入分析运行和可观测性缺陷，继续改善设施，落地 Skill 中的预制检查工具，深查 DS vision 使用；基本定位根因、提出合理方案并简单核实后可应用并尽快保留半成品热修复，不等待完整评分。
主 Agent负责整合、可观测性修正、现有 agent-browser skill 内可选通用服务/检查辅助脚本与热修复；live_deep_diagnosis（6-sol/high）负责运行语义与设施使用反馈；vision_root_cause（6-sol/high）负责图片需求→模型能力→发现/委派/消费的根因链。
检查脚本不写生成应用，不含题目选择器或断言，不改变初始数据，不恢复 browser-checks 独立技能或强制 Playwright 注入。
Qwen/MiniMax 保持取消，仅分析存量证据。禁止 Factory/devinfra/Corpus 测试，真实运行材料与实际应用操作用于核实。当前变更不自动提交。

用户进一步修正：读图应由合适 sub-agent 承担，不能用主模型可收图作为直接承担专业任务的充分理由。
已撤去刚提出的“能直接读图无需委派”文案，改为需求参考图由 vision 解析，主会话给出问题/路径并消费来源明确的观察，可批量与复用。
补充调查：所有原生 sub-agent 的实际使用与结果消费（live_deep_diagnosis）；自编技能清点（主 Agent），见 cells/skill-inventory.md。
本轮设施/工具具体改动及真实应用操作证据见 ../experiment-infrastructure/cells/live-observability-followup.md。

用户授权每题资源扩大为4GiB + 2 CPUs；attempt-07 通过ARC官方local runner现有参数设置，旧06仍为2GiB/1CPU，不直接比较耗时为纯Harness收益。
用户要求深入审计 exploration-tools 的拆分/迁移/删除；live_deep_diagnosis独立审计，主线暂不凭技能名称删除。来源清单见 cells/skill-inventory.md。

07接续输入已保留06停止后的完整工作区：GitHub 211121785 bytes、Sheet 572864078 bytes，保留Git、未提交工作、协作和原生记录。
07普通base SHA256 898faffcff715af23bf5f71154edf136c48e075b0d509ab4434d15d81adcd64b，含可选with-service与vision职责修正；尚未声明运行恢复。
探索工具专项审计见 cells/exploration-tools-review.md：建议保留通用入口、仅explorer强制正文、将Handsontable专门说明归还领域技能；07保持原exploration-tools，不将只读审计冒充已应用。
原生subagent专项见 ../experiment-infrastructure/cells/subagent-usage.md；06恢复窗零真实spawn，Flash曾把成员名当原生角色并产生重复工作归属。当前仅视觉分工已改，不能宣称其它角色使用已改善。

attempt-07 controller PID231677 已启动，沿用两题06半成品与模型路由，生成资源显式4g/2CPU。
GitHub包f62e1ff600abf6c88c0c5dfb0a4932c149076b883a1fcda23d1d72ce47850145；Sheet包268f90b91ea6240afd4af37d8678bddaf1294f5ae24cba1200fbb5da4b2c9b59；Braid二进制4074f51ec262294f8acf21f6f9ae31b6457884e8ba1593b16e06a647449c2a00。
用户认为 exploration-tools 应直接成为 explorer 角色提示词，主 Agent 赞同并更新审计方案；07不含此迁移，不冒称已应用。

exploration-tools归属调整已按快速修复授权完成源码：工具知识进入explorer，独立技能与其注册/重复正文注入删除，MCP配置归各variant/tools，领域命令归现有技能。07输入未改，等待下一次材料刷新。
依据Flash实证，同时补Pi工具的角色目录与braid指派名不可互换、避免重复实现已有同事工作的简短说明；不规定固定委派流程。

2026-09-28 05:44 UTC：07 当前监控 PID243060，原231787已替换；运行控制器231677未动。监控终态集合补入cancelled，并停止遗漏退出的06旧监控199628。Sheet在05:37:33新增证据flush超时（13条pending，5000ms），表明30秒采样/扩容尚未完全消除采集故障；应用生成仍继续，不能称为生成失败。原生子代理完整复审入口转至 [factory-subagents packet](../factory-subagents/packet.md)。

当前事实纠正：continuation-02已失败，两题在模型调用前报Git dubious ownership。拟修的Docker --user并未实际进入02冻结launcher；不能把之前“参数已补齐”的报告作为证据。停止新部署，准备独立未执行候选供用户确认；保留01/02失败与原09工作区。
