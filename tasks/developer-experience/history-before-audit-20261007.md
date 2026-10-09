# 开发基础设施与 Developer Experience

## 当前结论与接续：剩余噪声分析（2026-10-03）

用户要求在已有 token/耗时改善后，进一步分析噪声和优化空间，并建议交给 advisor。调查和方向判断已完成，采用 [advisor 决策](../../runs/developer-experience/noise-analysis-20261003/advisor-decision.md)。本轮没有修改设施源码或新跑冷任务/模型实验。设施实现继续归[开发-实验基建改进](codex://threads/01a0fa4f-471a-7963-a4e5-bc4a6071113e)，本会话收集与采用证据；long_session_review 持有成本归属，dx_next_decision 持有方案判断，不充当 reviewer。

推荐下一轮窄范围先整合主区既有短导航和组件本地说明，并准确迁移交付 schema3 新职责，再收窄查询、发现和阅读范例。交付 Lab README/recovery 合计73140B，主区对应10517B；reviewer本地入口在主区存在、交付缺失。这是未整合分支的事实，不能描述成上线回归；旧短文也不能直接覆盖新协议。保持原主题文档的权威归属，不新建文档体系或重复摘要。

冷任务11次工具调用中6次回执截断，回执约231626B；一次全树枚举产出927434241B/17.843秒，对应模型回执约40489B，不能把927MB当token输入。12个模型请求 usage 加总与线程总量一致；单请求input从36529增长到107624。固定指令/工具/历史与读入正文的贡献还不可精确分开，不宣称具体节约比例。原件见[成本摘要](../../runs/developer-experience/noise-analysis-20261003/summary.md)、[请求计数](../../runs/developer-experience/noise-analysis-20261003/request-usage.json)、[导航形状](../../runs/developer-experience/noise-analysis-20261003/navigation-shape.json)。

采用的消费方式是单问题先读单实验文本；JSON在现有exec环境中提取相关字段；路径从确切链接或有深度且文件名受限的metadata发现，长文只展开相关节。完整原件、具体错误、观察时间、unknown/partial和恢复身份继续保留。tasks/不是DX优化目标，本packet仅维护当前判断和授权。暂不增加查询参数、向量索引、发现框架或全仓拆分；只有正确单实验文本仍过宽，才扩展现有查询接口。

本轮用户请求范围是分析与方案判断；未进入上述新整合范围的源码实施或分支合入。已完成的冷任务成本参考保留在下文。下一步采用正常已授权工作的反馈，核对是否减少截断、全树扫描和路径猜测返工，继续统计所有实际参与Agent的token与端到端墙钟；不为获得漂亮数字重复完整验收。固定上下文裁剪只在有明确分项证据时另作判断。

## 前轮截面：交付后验收与成本口径（2026-10-03）

当前正在分析剩余噪声与成本机会。用户指示“进一步分析看看有没有优化空间，是否存在噪声过多的问题。（建议交给advisor）”。沿用核心 token/端到端墙钟判据；主会话量化导航与既有取证产出，long_session_review 持有结构化成本归属，dx_next_decision advisor 持有工程方向判断。Advisor不担任reviewer。本次只有只读调查、已有证据分析及packet整理，不改设施源码、不运行新冷任务/模型实验。原件和最终决策归 runs/developer-experience/noise-analysis-20261003/。

已发现：验收worktree未整合主区之前的短导航和reviewer本地README，不能将旧长入口造成的噪声归因给新协议；整合也不能用旧短文档覆盖schema3新语义。一次递归文件枚举产生927434241字节/17.843秒的本机原件，模型实际接收量另行核对，不能把两者混称token。计划先采用advisor决策，给用户具体范围与理由，不预先新增搜索框架或更多重复说明。

当前接续已完成对新交付 15a1a2a2 的单次只读/离线与冷上下文成本验收，完整生命周期仍未验。验收对象为 15a1a2a2（feat/experiment-startup-dx），替代下文 d4ac01dd 的交付截面；主区仍未合入。用户再次要求“实验基础设施有了改进，你验收看看？”，核心判据仍为所有参与 Agent 的 token 与端到端耗时。operation owner 已交付真实多目录监控反馈；独立冷上下文 Agent 使用 gpt-6.1-sol/medium 完成实际定位、离线准备、监控与恢复资格判断，已读取完成后的结构化 usage，避免以命令秒数冒充会话成本。本轮不使用 advisor 作 reviewer。最新 AGENTS 已取代此前版本。

已有首项反馈：同一交付示例 intent 新版离线元数据 compile 一次成功 0.066 秒，旧版本会话参考为 20.328 秒；新版将内容生产/身份冻结移至 build，职责不同，不能据此声称全流程缩短 20 秒。新增原件位于 runs/developer-experience/responsibilities-acceptance-20261003/；独立任务已结束，结果如下。

用户当前核心指标是“token 消耗量和耗时”。新版已有 gpt-6.1-sol/medium 单次冷任务的真实 token/耗时，均低于旧参考；但任务范围、状态和报告不同，仍未形成严格可比、稳定收益的端到端对照。监控呈现、离线编译和静态边界的局部通过只作辅助证据，不能表述成整体提速。当前验收与原始证据见[独立验收报告](../../runs/developer-experience/post-infrastructure-acceptance-20261003/report.md)。

本会话继续负责独立验收和成本证据采用。用户明确要求将设施建议交给[开发-实验基建改进](codex://threads/01a0fa4f-471a-7963-a4e5-bc4a6071113e)，已发送 advisor 结论、外部研究和证据入口；该会话完成独立分支交付 d4ac01ddeefe3864544ca31e523bbba13ffb04e3。验收对象位于 `/Volumes/WorkSSD/Development/.worktrees/experiment-startup-dx/factory26`，尚未合入当前主工作区。设施实现仍由该会话持有，不在这里并行改写。验收中 operation owner 持有真实记录的操作反馈，advisor 持有关键边界判断。

本任务此前的核心文档、本地组件导航及恢复说明已提交为 d6e282d4、fcc87221、3074b476、345c25de、9e5eeeac。持续知识已整合到原有权威文档，完整交付与三轮验收边界见[核心文档报告](../../runs/reports/2026-10-03-core-documentation.md)。用户明确 tasks/ 不是 DX 整理目标；本 packet 只记录本任务状态、判断、授权和证据，不作为另一套产品或运行文档。

### 新交付单次成本结果（15a1a2a2）

独立 gpt-6.1-sol/medium 冷上下文任务完成：216.855 秒、total 920281 token，input 915018、cached input 805504、非缓存 input 109514、output 5263。旧参考为 368.258 秒、total 1626564、非缓存 input 120108。新版有下降迹象，但任务完成范围、readiness覆盖、报告工作及运行状态不同，不能宣称严格 A/B 或全流程提速。仍有全文截断、递归 runs 搜索过宽和路径猜测失败。查询/编译/诊断通过，完整启动与热恢复尚未验。完整证据与各 Agent 审计开销见[本轮报告](../../runs/developer-experience/responsibilities-acceptance-20261003/report.md)、[成本对照](../../runs/developer-experience/responsibilities-acceptance-20261003/cost-comparison.json)。

operation owner 的连续上下文核查为 115.636 秒、974265 total token；它是不同模型/不同任务的验收开销，不用作冷启动对照。主会话成本按截至采样另列，所有实际参与 Agent 都纳入报告，未以参赛 provider 的空 token 字段代替开发 Agent 真实 usage。

### 前轮事实与判断（d4ac01dd）

- 12 个真实 I14 目录的 status 耗时约 0.09–0.16 秒，输出 645–3005 字节；A2 文本直接呈现 provider 生命周期、连续观测、资源等待、semantic unknown 和 partial 覆盖。资源详情仍被截断，证据长路径重复。见[操作报告](../../runs/developer-experience/post-infrastructure-acceptance-20261003/operation/report.md)。这些不是 LLM token 或整体会话耗时。
- 交付自身的真实离线 intent 一次 compile 成功，20.328 秒，无需修复重试；未 build、启动 SDK/Docker/模型或执行完整恢复。见[编译回执](../../runs/developer-experience/post-infrastructure-acceptance-20261003/compile-receipt.json)。没有同条件旧版对照，不能推导提速幅度。
- Advisor 定向审阅未确认阻塞性源码缺陷；普通终态内容与 managed checkpoint 区分保持。Local 缺少完整后代写者合同时仍拒绝完整 capture。完整生命周期、打包/首次启动/热恢复成本尚无实际验收。
- 相对当前主分支，交付分支遗漏了 3074b476 的 recover FileNotFoundError 诊断补充。合入前应保留“显式 Harness checkpoint；平台 ZIP/partial 不能直接恢复”的既有说明；本次未改设施源码或处理分支合入。

最后一轮旧版冷启动仅作参考：368.258 秒；input 1616684、cached input 1496576、非缓存 input 120108、output 9880、total 1626564 token。reasoning output 是 output 子集，不重复相加。见[成本原件](../../runs/developer-experience/core-docs-20261003/next-opportunities/final-cold-costs.json)。该会话完成多种场景和报告，不能直接与新的一次 status 或 compile 比较。三轮会话场景及方法不同，也不是严格 A/B。

### 决策、授权与接续

用户此前授权开展开发体验优化及自主提交，要求独立会话使用 6.1-sol medium 验收，并强调“验收不只是流程能跑完，还要看是否曲折、耗时”。随后要求 advisor 判断、主会话收集整合数据和研究前沿资料，再明确将这些交给设施会话。最新指示“已经完成了改进，你验收一下”授权本次独立验收；“我关注的核心指标是 token 消耗量和耗时”修正了核心判据。本次没有从设施改动授权扩大到新模型实验、远端控制、push 或现场清理。

下一步成本验收必须统计所有实际参与 Agent 的 input/cached input/非缓存 input/output/total，并记录用户请求到取得同等可采用结果的墙钟时间，报告整理时间另列。重试、绕路和等待计入；并发 Agent 时长不相加冒充墙钟。结论正确性、恢复身份和授权边界保持相同，不能靠少完成任务降低成本。输出字节、命令速度及代码结构只是解释性指标。

优先在下一次已有授权的真实任务中采用冻结交付，取得打包、域装配、服务 ready、首次入口和模型受理的分段耗时及修复/重试次数；获得真实新 checkpoint 后再验同域恢复。现在没有可确认的新版端到端成本收益，不宣布任务目标完全达到，也不为补齐数字新增测试、模拟探针或未授权模型运行。

Advisor 采用结论与外部资料分别见[决策](../../runs/developer-experience/core-docs-20261003/next-opportunities/advisor-decision.md)、[研究摘要](../../runs/developer-experience/core-docs-20261003/next-opportunities/external-source-brief.md)。优先改善既有 monitor 保存事实的消费和按未决问题定向阅读；通用历史图、自建向量索引、大规模拆分等仍需实际成本归因后决定。

## 前轮截面：长会话复盘与接续成本（2026-10-03）

用户要求总结会话 `01a0fd22-fe3b-7430-9707-4534e7758565` 及本项目其它较长会话，针对目录、文档、架构和开发基础设施开展开发体验优化。本轮复盘与有证据的入口改进已完成，完整结果见[综合结论](session-recovery/findings.md)。

指定会话的[时间线](session-recovery/target-session.md)覆盖 9 个 turn、485 次命令、7 次压缩；另复盘“开发-实验基建改进”“整理项目数据、代码与文档”，并采用 factory26 main 的既有复盘及末段原始窗口。调查区分历史问题和已交付能力，不把命令数量直接等同于浪费。

本轮已更新 docs/index、Deployment 和 CONTRIBUTING 的接续路径、协议版本、缓存位置及源码定位，并重写实验 DX、存储生命周期两项 packet 的当前答案。两份旧正文逐字节保存在各自 history-20261003.md，原有授权及证据身份保留；没有迁移独立 variant 或建立第二套状态设施。

采用依据是三次实际冻结 Lab status 只读查询、相对链接与历史原件核对，见[回执](../../runs/developer-experience/session-recovery-20261003/verification.json)。已验证入口能够区分取消、在途与未派发，以及技术可用动作和当前授权；没有测量未来会话节省的时间或 token。

本会话 `01a0ff37-7bf2-76c1-8d3a-e04024be2af8` 负责总体复盘与采用，`long_session_review` 交付其它会话及两项 packet 整理，`resume_surface_audit` 交付仓库核对与长期入口修正，advisor 复核实施边界。源码、模型、运行控制、部署与数据清理没有进入本轮范围，未提交或 push；其它任务的并行修改保留。运行验收继续由原实验 owner 按已有授权完成，不从本轮调查新增实验。

## 前轮交付与授权（历史）

2026-09-24 用户授权沉淀可复用监控 Agent，明确模型使用 6-luna medium/high，并消除每分钟返回模型续等。
已新增 [监控角色与程序等待](monitor.md)：当时的监控说明（现已删除）保存提示词和 gpt-6-luna/medium 配置，`scripts/wait_local_runs.py` 持有三分钟状态检查，工具续等留在单次程序编排内。
已替换本轮实验的旧 sol/high 监控 Agent；没有停止、重跑或修改实验。

第一轮的 variant 独立实现、源码开发与冻结制品分离、工具资源独立准备已经完成落地。
用户随后要求删除 Factory/开发设施测试；删除和相关约定已提交为 `99cbe62`。
历史检查结果仅保留为当时的实施证据，不是后续工作要求。

第二轮文档系统与代码注释整理已提交为 `caba9ae`，其后用户明确授权“请做这些”，要求落实此前列出的三项剩余工作。
本次三项已完成：新实验记录查询接入、旧执行路径清退、开发依赖取得与独立源码交接。
具体改动、真实操作结果及限制见 [剩余实施与结果](remaining.md)。
当前改动未提交；未启动新实验、未修改冻结制品、journal 或 SVC Corpus，未新增或运行 Factory/设施/Corpus 测试。
Braid OTLP 等其他任务的并行工作保持原样，未借本次收尾宣布其完成。

### 前轮交付入口

长期入口为 AGENTS、CONTRIBUTING、Product TDD 与 Deployment。
[剩余实施与结果](remaining.md) 记录本次交付和可恢复产物；若要提交，只纳入用户授权范围，不把混合工作区整体提交。
[第二轮文档方案](round-2.md)、[调查](round-2/inquiry.md)、[实施顺序](round-2/plan.md) 是此前文档阶段的记录，其中当时暂缓的三项已由本次落实。

### 相关工作（前轮截面）

[SVC Corpus](../svc-corpus-review/packet.md) 与 [SVC skill 接线](../svc-skill-integration/packet.md)仍有验收事项，保持开放。
[独立 variant](../independent-variants/packet.md) 的调查与预演已由本任务第一轮承接。
官网和本地矩阵的控制状态归各自任务及原始 journal；本轮未查询它们的实时状态，不代其宣布结束或重启。

### 第一轮历史依据

- [调查](inquiry.md)、[边界调查](boundaries.md)：调查时的观察、推导与限制，不代表全部当前实现。
- [第一轮设计](design.md)、[variant 交接](variant-handoff.md)：当时的边界判断。
- [第一轮实施记录](implementation.md)：实际改动、当时的检查及证据限制。

第一轮原始产物位于 `runs/developer-experience/`；长期当前行为以源码及完成整理后的项目说明为准。
