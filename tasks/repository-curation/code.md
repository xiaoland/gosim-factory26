# 代码与工作区归属清单

本清单使用开工时保存的 [status.txt](../../runs/repository-curation-20261002/baseline/status.txt)、[initial.diff](../../runs/repository-curation-20261002/baseline/initial.diff) 和 [head.txt](../../runs/repository-curation-20261002/baseline/head.txt)，起点为 `61e0f5f6c53cca8d81dc629e45a54ae974d6538a`。该状态有 **85 个已跟踪变化（84 修改、1 删除）及 2,458 个未跟踪文件**；初盘的 83 是更早的观察，不覆盖开工基线。未跟踪文件包含此前调查创建的本任务 packet 1 份，以下排除其业务归属。

归属指可以继续采用成果的任务职责，不宣称已经核对各独立会话的实时 owner 或授权。文件可能同时服务多个任务，不能按整文件暂存成一个任务提交。用户随后要求继续完整整理；本负责人补充核对现行入口、构建装配、源码与证据边界，并应用下方明确的源码说明整理。未修改运行逻辑、运行现场或原证据，未执行模型、官网、服务或测试。

## 已跟踪实现及共享入口（37 个文件）

路径中的花括号仅列出实际基线文件，不表示整个目录可清理。

| 职责及材料性质 | 基线文件 | 归属证据与采用边界 |
| --- | --- | --- |
| 仓库入口及跨任务说明（活动文档） | `AGENTS.md`；`docs/{index.md,product-tdd/index.md,deployment/index.md,deployment/console.md,deployment/recovery.md}`；`variants/README.md`（7） | 开工 diff 包含 I11 副本导航、实验恢复与 Console 合同；[长期文档整理](../durable-docs-curation/packet.md)、[Console](../braid-console-control/packet.md)、[DX](../experiment-dx-review/packet.md)联合消费。本轮文档负责人只处理已获批入口整理，不能把原 diff 归入本轮。 |
| 冻结应用本地需求校准和结果呈现（活动 benchmark） | `benchmarks/hackathon/{README.md,github.spec.ts,report.py,support.ts}`（4） | [K3 冻结应用重放](../k3-root-experiment/packet.md)明确记录 github.spec/support 导航与契约校准；README 保存覆盖限制。report 的来源分组、suite 冻结及 retry 选择由[命名整理](../variant-experiment-naming/plan.md)和[实验追溯](../experiment-traceability/packet.md)共同消费；不能将这四项整体视为同一次改动。官方 benchmark 保留。 |
| 原容器只读接入和原生会话展示（活动 Console） | `braid-console/{code_files.py,docker_runtime.py,native_sessions.py,run_records.py,server.py,service.py,web/src/Transcript.tsx,web/src/api.ts}`（8） | [current-runs](../braid-console-control/current-runs.md)明确 runtime-readonly、容器出生身份、原 namespace 路径与禁写职责；diff 对应后端入口与前端只读显示。该任务负责人继续持有 Console，归档原件存在不保证旧路径还能浏览。 |
| 检查原输出与退出值的能力发现（活动技能） | `harness/skills/{agent-browser/SKILL.md,agent-browser/scripts/with-service.py,e2e/SKILL.md}`（3） | [I11 feedback-evidence](../iteration11/cells/feedback-evidence.md)明确 with-service 完成输出及发现入口；[GitHub 最小工具接线](../braid-github-minimal-review/cells/svc-cli-integration.md)保留既有 check-only 实现及真实副本验证。e2e 技能改动的本次细分 owner 尚未确认，不据相邻路径合并授权。 |
| 阶段应用重放与上传适配（活动 ARC 支持） | `lab/arc_bench/{package_arc_replay.py,playground.py}`（2） | diff 增加显式 git-ref 阶段快照以及 curl `--http1.1`；[命名方案](../variant-experiment-naming/plan.md)定义应用来源合同，AGENTS 已保存阶段快照范围。此次具体 curl 修复及阶段快照增量的独立 owner 未确认，保留给原实验负责人核对；不调用上传。 |
| 公共实验恢复、旧来源身份及派发边界（活动实现） | `lab/exp/{__main__.py,admission.py,backends.py,controller.py,hosted.py,runner.py}`（6） | [DX packet](../experiment-dx-review/packet.md)定义 legacy-source 与公共消费者；[I14 startup-blockers](../iteration14/dx-resume/startup-blockers.md)记录 inspect 超时、原容器上传和 start-marker 接缝；hosted 的 latest-submission 修复另有[I13 实证](../iteration13/i13-2/hosted-github-memory-recovery.md)。controller 冻结复制 agent_support，不能去掉恢复共享接线。继续采用须按 hunk 区分 DX owner、I14 恢复 owner 与 I13 hosted owner。 |
| 共享材料与 Braid session 预算（活动实现） | `scripts/{agent_support.py,model_budget.mjs,package_agent.py}`（3） | [I14 provider-recovery](../iteration14/provider-recovery/packet.md)明确 retained-native 路由；[baseline-roots](../iteration14/baseline-roots/packet.md)记录模型 scope；[startup-blockers](../iteration14/dx-resume/startup-blockers.md)记录 child 不能绕过父 Braid owner 及最终 Braid 字节校验；[I11 variant](../iteration11/variant.md)记录 OTLP 名单增量。同一个 agent_support/package_agent 内存在多项职责，不能整文件认作 provider 修复。 |
| 检查点与恢复生产端（活动实现，也读取历史来源） | `scripts/package_completed_recovery.py`；`submission/{exp_checkpoint.py,recover_completed.py}`（3） | [DX packet](../experiment-dx-review/packet.md)明确 producer 独占 worker、source_id/attempt_id 区分；[I14 接续](../iteration14/dx-resume/packet.md)与[provider-recovery](../iteration14/provider-recovery/packet.md)消费通知、传输及材料刷新；[恢复操作调查](../experiment-operations/recovery-findings.md)保留 Git 重建边界。三个文件包含共享历史恢复合同，旧来源支持并非死代码。 |
| 独立 Pi 额度守护（任务专用操作脚本） | `tasks/pi-minimal/budget_guard.py`（1） | [Pi packet](../pi-minimal/packet.md)记录用户低于20不取消、阻止新任务的例外；self_funded 运行不套比赛取消阈值。脚本留在该任务，不能迁入通用预算保护或因当前模式不用而删除。 |

## 独立 variant 的基线改动（6 个文件）

| 职责 | 基线文件 | 证据与保留判断 |
| --- | --- | --- |
| I12 具体成员指派材料（冻结运行的维护源码） | `variants/pi-braid-i12/agents/{pi-deepseek-fast,pi-glm-fast}/instructions.md`（2） | [I12 assignment-members](../iteration12/assignment-members.md)与[assignment-implementation](../iteration12/assignment-implementation.md)记录具体成员身份；修改源码不改旧冻结 ZIP，不能按 I13/I14 活动身份删除。 |
| I14 retained native 模型路由（活动开发源码） | `variants/pi-braid-i14/run.py`；`variants/pi-braid-i14-cleaner/extensions/factory-cleaner.ts`（2） | [baseline-roots](../iteration14/baseline-roots/packet.md)记录 scope 映射；[provider-recovery](../iteration14/provider-recovery/packet.md)记录 cleaner complete 的 samplingParams 接缝。共享 run 的继承关系须保留。 |
| I14 e2e 供应商接线（活动开发源码） | `variants/pi-braid-i14-e2e/{run.py,tools/e2e.config.ts}`（2） | [tester-e2e](../iteration14/tester-e2e.md)记录解除 ARC 耦合；[provider-recovery](../iteration14/provider-recovery/packet.md)及基线 diff 进一步把 wire model、endpoint、key 分别经 E2E_MODEL/BASE_URL/API_KEY 注入。前序说明不代表最终冻结配方，后续改动仍由接续 owner 采用。 |
| Variant 状态导航 | 已计入上表 `variants/README.md` | 不重复计数。I10–I14 的独立副本有隔离职责，不按文件相似度合并。 |

以上6个实现文件与前表37个文件合计43个，剩余42个任务文档如下。

## 已跟踪任务文档（42 个文件）

同目录 packet 是接续入口；配套页的角色由现有正文及开工 diff 确认。这里完整覆盖基线 task 文档，不能据历史状态认定实验已停止或恢复授权仍有效。

| 接续职责 | 基线中的具体文件 | 基线变化及采用入口 |
| --- | --- | --- |
| 旧验收、设施与实验维护记录 | `acceptance-workflow/packet.md`；`competition-p0/packet.md`；`dual-bench-hosted/packet.md`；`hackathon-local-bench/packet.md`；`hackathon-variants/packet.md`；`local-official-bench/packet.md`（6） | 分别保留宿主重启停止、正式验收范围、旧矩阵移交、本地诊断与冻结包结果；不能把历史 run 状态作为当前运行事实。每个现有 packet 自己承担该旧任务接续。 |
| Console 与开发体验接续 | `braid-console-control/packet.md`；`developer-experience/packet.md`（2） | 前者导航 current-runs，后者导航 remaining/monitor；不是本轮源码改动归属证明。 |
| Braid 前序易用性及职责边界 | `braid-usability/{design.md,findings.md,packet.md,plan.md,technical.md,verification.md}`（6） | diff 标注已实施边界与后继 braid-collaboration；保留历史方案及授权纠正。 |
| 子角色及材料实效 | `factory-subagents/{packet.md,roles.md}`（2） | 当前实际使用复审、advisor 决定与 native continuity，原生角色材料仍有后继消费者。 |
| 吞吐旧实验 | `iteration-throughput/{packet.md,cells/environment.md}`（2） | 旧运行环境及结果接续，后继新矩阵须独立授权。 |
| I10 运行与过程证据 | `iteration10/{packet.md,experiments.md,observations/behavior.md}`（3） | 历史运行配方、继续结果和过程观察；不重新生成旧 ZIP。 |
| I11 运行、恢复整理和 stalls | `iteration11/{packet.md,recovery-curation/packet.md,recovery-curation/local-observation.md,runtime-stalls/packet.md}`（4） | 运行入口、恢复原件及本地观察、运行阻塞各有子 packet；保留 lineage，不能把分析截点当恢复检查点。 |
| I12 具体指派与停用现场 | `iteration12/{packet.md,braid.md,deployment.md,restart.md}`（4） | 当前决定及成员身份材料、部署、重启前后原件各自保存，原运行授权不因整理复活。 |
| I13 质量方法 | `iteration13/quality-methods.md`（1） | 方法来源与后继材料整理；I13 packet 本轮新变化不在开工 baseline，不混计。 |
| I14 当前决定与历史执行 | `iteration14/{packet.md,evidence.md,experiments.md,tester-e2e.md,dx-resume/packet.md,dx-resume/host.md}`（6） | 接续 packet 记录全实验暂停；父 packet 保留多个日期的决定，活动投影由本轮文档负责人收束。保存时状态不能替代物理停止证据。 |
| 官网运行观测 | `official-runtime-observability/{packet.md,design.md}`（2） | 保留 Git 发布与平台展示的证据缺口、后续待复核方案；不为填官网接口表增加参赛动作。 |
| Pi Minimal 预算及当前自费实验 | `pi-minimal/{packet.md,meter-budget.md}`（2） | 预算脚本已在实现表计数；两页保留比赛旧模式与当前自费区别。 |
| 已删除的旧 viewer task | `run-process-viewer/packet.md`（删除，1） | 基线已删除；实际 viewer 仍在 `lab/analysis/run_viewer.py`，现操作入口在[证据手册](../../docs/deployment/evidence.md)。未在本轮恢复旧 packet 或删除 viewer 实现。 |
| SVC 正文审查 | `svc-corpus-review/design.md`（1） | diff 明确是2026-09-23设计与结果来源，当前采用看同目录 packet，不把旧外部 Corpus 设计自动应用至当前 skills。 |

## 未跟踪材料族（2,458 个文件）

下表覆盖开工基线所有一级职责族；数量只计 Git 可见文件。目录内的 `.py/.ts` 可能是采集脚本或源码快照，不能全部视为新产品代码。

| 材料族及文件数 | 性质与证据入口 | 处置 |
| --- | --- | --- |
| `docs/deployment` 1 | model-providers 是长期操作说明；[模型供应商](../external-model-providers/packet.md) | 保留权威文档，进入文档负责人核对；已删除的项目级委派指南不再列为现行文档。 |
| `harness/skills/svc` 27 | [hackathon-capabilities packet](../hackathon-capabilities/packet.md)及[implementation](../hackathon-capabilities/implementation.md)明确是迁移前单技能快照，归档 variant 和 native-hackathon 仍消费 | 历史材料支持，不能将未跟踪等同可删除。 |
| `variants/pi-braid-i11` 25 | [I11 variant](../iteration11/variant.md)明确用户要求复制 I10，改身份并保持独立；包含角色、入口、build、扩展、工具 | 独立实现，保留；不和 I10/I12 去重。 |
| `runs/reports/2026-09-23-*` 4 | local-agent-process、local-experiment-infrastructure、model-reasoning-probe、official-results 四份历史结论 | 保留报告身份与条件；是否整合长期知识归文档负责人，原报告不静默覆盖。 |
| `tasks/iteration10` 844、`tasks/iteration11` 1,150 | [I10 instruction-audit](../iteration10/instruction-audit/packet.md)、I10 run-audit、[I11 GitHub audit](../iteration11/run-audit/github/packet.md)、[Sheet audit](../iteration11/run-audit/sheet/packet.md)、[Sheet full-lineage](../iteration11/sheet-effectiveness-analysis/packet.md)是原件、源码快照、派生索引、逐段回读与分析脚本的组合 | `current/`、`current-runtime/`、`work/native-homes/` 是调查快照；分析脚本绑定固定输入。保留完整 lineage 和覆盖账，后续物理整理由数据清单约束；不得直接执行其采集或监控脚本。 |
| `tasks/iteration12` 20、`iteration13` 31、`iteration14` 4 | I12 原生身份/root-cause 证据；I13 材料与恢复调查；I14 baseline-roots、provider-recovery 与 dx-resume 执行页，各子 packet 可定位 | 区分活动方案与历史读取材料，保留 source/run/commit 身份；未调用运行入口。 |
| `tasks/acceptance-integrity` 41、`braid-architecture-audit` 9、`braid-collaboration` 11、`braid-github-minimal-review` 20、`braid-product-hardening` 15、`braid-product-reaudit` 69、`braid-usability` 14 | 各族现有 packet、design/review/disposition 明确职责。reaudit 的 token-{deep-03,final-review}/analyze/extract、freeze_local_workspace，acceptance 的 run-method-check 是分析/操作辅助，`source/official-billing` 是来源证据 | 是调查/设计/实施结果及原件，未整体改造成共享库；是否尚有未交付结论由各 packet 接续。稳定会话 owner 未逐一实时确认。 |
| `tasks/competition-budget` 7、`developer-experience` 2、`development-delegation` 1、`experiment-infrastructure` 24、`experiment-traceability` 6、`external-model-providers` 1、`factory-subagents` 23 | 预算与设施旧证据、开发协作、追溯方案、供应商决定、角色使用分析；token_economics 与 advisor/role audit extract 是固定分析脚本 | 原件与派生材料分别保留，历史 experiment-infrastructure 不作为现行 Lab DX；不把未跟踪角色分析自动接入 runtime。 |
| `tasks/github-score-diagnosis` 13、`sheet-score-diagnosis` 9、`official-collaboration-review` 3、`official-results` 2、`local-run-analysis` 1、`pi-minimal` 19、`research/braid-collaboration-method` 6 | 评分/过程诊断各 packet；Sheet repro.mjs、official review render.py/template.html 是定向复现/离线展示；Pi 的多个 analysis 子 packet 是不同运行身份 | 不自动搬入通用 lab、不用报告替代官网原件；repro 启动与运行操作不在本轮授权。 |
| `tasks/hackathon-capabilities` 9、`hackathon-team-baseline` 16、`issue-decomposition` 5、`iteration-throughput` 3、`k3-root-experiment` 3、`k3-root-only` 1、`raw-core-local-baseline` 1、`arc-deepseek-version` 1 | 已有能力拆分、冻结团队对照及独立模型实验 packet；run-interface-lite/monitor 是当时操作脚本，不能据其存在认定还在运行 | 保留不同实验及授权身份，监控不在整理中启动。 |
| `tasks/svc-cli-simplification` 2、`svc-corpus-review` 6、`variant-experiment-naming` 5、`iteration-map.md` 1 | CLI 审计、正文结果、命名方案及历史导航 | 参赛 Agent skills 与开发 SVC CLI 来源不同；不恢复已退役 CLI。 |
| `tasks/repository-curation` 1 | 此前调查 packet | 属本任务前序材料，不属于其他任务 dirty，不把本次 code/data 文档混入原2458计数。 |

## 已核实的保留依赖与后续决定

定向核对的是实际源码引用、构建装配及少量 task 消费关系，未对所有历史外部快照作全域引用证明。**本轮没有取得足以支持删除产品源码的证据，源码删除候选为空。**

| 对象 | 已观察到的实际消费 | 判断 |
| --- | --- | --- |
| `lab/control.py` | `lab/exp/core.py` 导入 process_identity/process_state；docker_admission、hosted_monitor 仍导入 process_identity；旧 status/wait 也消费 | 含活动共享支持，不能按旧实验名称清理。 |
| `lab/status.py` | `lab/analysis/inspect_runs.py` 与 run_feedback 直接导入；factory 与 viewer 消费 inspect_runs | 当前分析仍读取历史记录，保留。 |
| 历史 GC 及旧 CLI 说明 | 新 Lab 入口不暴露 gc-plan；证据手册明确其来源是历史冻结 CLI | 缺新入口不是应补代码的缺陷；缺少完整动态装载与冻结恢复引用证明，不列删除候选。 |
| 动态构建与恢复 | package_agent 按 variant 选择 build；exp controller/runner 使用冻结源码与 zipapp；docker_workspace 动态加载官方 runner；恢复 producer消费原包材料和来源身份 | 搜索静态 import 不足以认定源码无用，保留构建/冻结目录合同。 |
| I10–I14及历史 `svc` | 技术说明允许独立 variant；I11 复制原文与历史 svc 装配方案明确消费者 | 冗余外观有隔离/历史职责，不去重。 |

后续需要的是原任务 owner 对共享文件 **具体 hunk** 的归属及验收状态核对，尤其 `agent_support.py`、`recover_completed.py`、`package_agent.py`、`report.py`、ARC 上传与阶段快照增量；已确认的联合消费者在上表留入口。整理授权覆盖本地可确认的必要处置，但不代替其它活跃任务的源码验收或运行授权。已有有效实现继续保留；未观察到必须修改的结构缺陷，不为减少文件数增加重构。

验证采用开工状态与 diff 分段比对、目录族计数及上述实际调用检索；没有新增治理脚本、全量 rollout 阅读或可运行测试。最省维护的路径是继续用现有 task packet 追溯和本清单导航，只有出现具体消费断点再调整源码边界。

## 完整整理的实际处置

进一步核对 Git 可见的 `scripts/`、`lab/`、`submission/`、`variants/`、`harness/`：7个符号链接均有效，没有需恢复的断链。I11未跟踪源码已在 variant 索引、独立 build 和公共 packager 装配分支中有明确入口；历史 svc 的三个归档 build 与 native-hackathon 专用 packager 仍消费该快照，不需要再建导航或移动源码。原件/派生数据的 Git 边界由数据负责人集中整理，本负责人不重复更改 gitignore。

已修改三个无其它工作区增量的模块说明，直接让源码读者找到当前职责：`lab/control.py` 区分现行 process identity 和保留的旧控制器 socket/change feed；`lab/status.py` 明确历史 lab.run 的分析消费者和当前 lab.exp status；`lab/gc.py` 明确只读回收规划、历史归档/依赖合同、委派给 lab.exp.artifacts 的 artifact-store 规划，以及现行 CLI 未直接暴露本模块 gc-plan。没有抽取公共模块、改变 import 或增加执行入口；分离现行/历史身份不需要改变仍被消费的实现。

这三处说明通过内置 `compile()` 语法检查及限定 `git diff --check`。其余代码处置已完成核实并按实际消费关系保留，没有发现应删除的废弃源码或必须去重的运行材料。共享恢复实现的功能验收继续归原 owner，不被列作本轮整理欠账。

版本归属也已闭合：I11 的25个未跟踪文件是用户授权交付的独立实现源码；历史 svc 的27个未跟踪文件是能力拆分交付的固定打包材料。两者应受 Factory26 版本管理，不是刻意仅保存在本地的调查材料。已分别在[原I11 packet](../iteration11/packet.md)与[原能力拆分 packet](../hackathon-capabilities/packet.md)补充责任：原任务主线负责采用并纳入版本，本次整理不混合暂存或提交他人实现。实际消费者及版本责任已明确，原任务的提交操作不作为整理欠账。

最终核对时，另一 owner 已扩展 `lab/gc.py` 的 artifact-store 消费；本轮仅据该实际调用修正模块说明，保留并排除其 `store.json`、gc_plan 委派和返回字段等功能变化。三个模块在该核对时点均通过 `compile()`；本轮精确源码增量仅为三个顶部 docstring，不将此语法反馈当作另一 owner 功能验收。
