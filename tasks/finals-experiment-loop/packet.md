# 决赛实验基础设施重设计

- **Objective**: 面向 2026-10-08 18:00 决赛截止，重设计开展、观察、控制、接续和分析 ARC 实验的完整设施。让 Agent 主要处理实验问题，不再负担环境接线、身份拼接和机械排错；simplicity、agent-friendly、traceability/observability 都以真实使用成本判断。
- **Guardrails**: 2026-10-06 用户已明确批准实施计划开工、自由提交及真实模型独立会话验收，费用不是问题；原话见下文。不控制其它任务运行、不清理历史数据、不 push。Mac 产物只在 WorkSSD。保留他人工作区改动；不编写或运行 Factory/Braid 的测试、smoke 或换名自检。用户新增的自实现模拟测试指生成应用的评测，不扩大为设施测试。
- **Verification**: 先定义代表需求与可观察结果，再以独立 Agent 的实际使用 profiling 取得反馈。覆盖三参数启动、status、pause/resume、同 variant restart、本地与 Hosted、Pi-only 与 Braid、OTLP/Console、资源、费用/turn 策略、顺序 stages、失败/取消及完整结果保存。查阅历史材料的耗时只作为诊断基线，不能充当真实启动或改造收益证明，方法见 [evaluation](evaluation.md)；不把这些活动塞进实现计划的调查阶段。
- **Current Truth**: 用户已批准 [design](design.md) 与六段 [implementation](implementation.md) 开工；公共 run CLI/API、自动化与文档已进入源码，两个专用 variant 材料已派生，执行与观测草稿仍在修正实际接线，尚不可当作可运行交付或验收通过。没有启动本轮收费模型。已定合同：pause/resume 保持原 run；restart 同 variant 整体迁移 data 并创建新 run，同 task 恢复原生执行、新 task 建新原生状态；status 执行事实与脚本 activity 分别展示；共享服务在 sfp7，Hosted 轻量自包含；Braid 自有累计证据后台投影。
- **Next Step**: 依六段确定改动完成实现与部署，派生 I14-dx-test、pi-minimal-vv-dx-test，安排独立会话实际验收。真实验收题目、route、控制损失及运行身份在 evaluation 中冻结并记录；费用不限不是无限运行，也不授权接管其他任务。

## 开工授权与责任

2026-10-06 用户原话：“好的，没问题，你可以开工了；你可以自由提交；基于 I14, pi-minimal 派生出 I14-dx-test, pi-minimal-vv-dx-test 两个 variants （派生新的 variant 是因为本次实验基础设施改进必定会涉及到 variant 的改进），按你说的用独立会话验收，你可以使用真实模型，不需要 mock，费用不是问题。”这条指示批准当前 design/implementation 的源码实施、必要部署、当前任务提交和真实模型验收。比赛提交与既有运行仍不在接管范围。

主 Agent 负责公共 run API、CLI、自动化、ARC 执行、restart、target 配置、整体集成和提交；cold_console_profile 持续负责 OTLP/Backend/Console/Braid view。前两位执行负责人的交付尚未接通真实控制、数据回收和原生接续，主没有采用其完成声明。evaluation_implementation 已确认没有构建、SDK 或收费运行在途，并转交执行责任；它继续持有 evaluate/package_arc_replay 的独立评测结果。2026-10-07 execution_owner 明确没有在途运行后，主接管两个 variant 的 main.py、I14 run.py 与共用 harness_services；execution_owner 仅维护两个 build.py 并从最新源码重建材料。原草稿和构建原件保留，不回退其他工作区。

2026-10-07 已移除 I14 dispatcher 对旧 execution context 的启动门禁，入口直接运行 variant。接续应用迁移到真实 template 根，native 数据独立迁移；当前平台输入与私有评测上下文不被旧输入覆盖。Hosted 共用轻量 raw receiver，按当前 Lab run ID 单独保存 producer 数据；本地使用共享 Collector。执行端 supervisor/Python 自动化通过 remote spawn 接入，Mac relay 只消费保存的记录并回收数据，不成为第二套运行观察器。以上是源码接线状态，尚未进行本轮真实模型验收。

已经向独立验收会话 `01a1118d-d790-7df1-93b5-df1801813158` 发送首个自然请求：“现在帮我用 pi-minimal-vv-dx-test 在 WSL 跑一次 BookStack。跑起来后暂停半分钟再恢复；看一下状态、日志和费用，确认有真实进展后停止并保存现场。顺便记录一下使用中哪里费劲。”不提供 CLI 操作清单或内部技术导航。请求开始实际 P1 使用，但发送成功不证明已经运行。费用目前可采集共享 account-key-window delta，不能冒称 per-run，因此 P1 的精确费用自动停止仍未覆盖；这次手动停止属于原验收矩阵明确允许的接续准备。WSL 固定实际 loaded image ID cfb919…，源/目标 17 层一致与默认配置差异的证据保存在 `runs/arc-bench-image-comparison-20261007.json`。

已安排 local_execution_decision advisor 判断官方 SDK prepare 后直接 Docker create/start 与继续捕获 SDK stdout 容器身份的取舍。判断依据是实际 SDK `docker run --rm`、随机容器名和只在结束后保存的 local-run.json；尚无本轮收费运行，不能把 SDK prepare 成功当作运行控制通过。

已采用 advisor 的直接 create→保存 CID→start 建议；cold_local_profile 接续其边界调查，持有新增 local_run.py 的真实执行、远端部署与控制回收结果，主负责把它接入公共 API。SDK Meter 是共享 access-key 累计差值，不保证单 run 归属，不因此增加串行 gate。默认 target registry 已改用实际 Mac 材料构建路径与远端执行路径，不再返回缺 SDK/runtime 的假 profile；任务 registry 提供 BookStack 和已冻结 GitHub Stage1/2 的需求入口。主只读 GET 确认 `/competitions/hackathon` 的实际 id 为 hackathon；官网凭据使用现存 ARC dotenv，而非不含 ARC key 的 models.env。以上仍是接线与事实核对，不是付费验收结果。

实际材料检查尚未通过：第一份 I14 ZIP 根 main.py 仍是旧 facility dispatcher；第一份 Pi ZIP 仅 28 项，缺 node/pi runtime。原包保留在 runs/finals-experiment-loop/materials，不发给独立验收者，variant owner 正修复直接 builder 与入口。新版执行装配已改为调用这两个 builder，不再进入 package_agent 的定义/制品门控包装。原生状态观察只采用真实 header/session_id；没有 provider turn ID 时保留缺失，不用行号补造。状态脚本错误保留 stdout/stderr，查询本身不制造活动时间。

历史 Hosted 原始 template-bundle ZIP 的实际根为 template/，已按这条证据修正下载映射到 data/workspace 与 data/harness。完整 native 历史仍迁移；新 raw collector 使用 native_scope/producers/当前 Lab run ID 独立目录，不把旧 batch 重新计作新 run 的消费。以上代码尚待真实包和平台运行验证。WSL SDK 已部署，镜像仍需执行 owner 完成传输；共享 Console 的 sfp7 宿主/容器 bridge 和 WSL 宿主反向隧道已有 HTTP 200，WSL 容器入口、实际原生生产、费用以及 Hosted raw 回收尚不能算验收通过。

独立验收会话 `01a1118d-d790-7df1-93b5-df1801813158` 负责真实首次使用与 profiling，不以阅读实现代替实际反馈。evaluation 已冻结最多八次生成与三项独立评测，覆盖 BookStack、GitHub Stage1/2 及策略/平台停止；费用来源未知不当作零，非正式参赛 self_funded。当前尚未开始收费验收，等待真实可消费执行与服务版本。旧段落中的“待开工”描述是历史授权沿革，不代表当前阶段。

用户随后要求验收派单尽量接近平日的自然消息，不发长串明确边界或操作导航。已告知独立会话：前述长说明属于准备，不作为冷启动顺畅证据；真正交付后的派单只描述实验目标与关心的结果，入口查找与排错都计入真实使用负担。

Console owner 已报告 sfp7 的实际部署：独立目录 `/home/yyh/factory26-exp-console-20261006`，loopback `127.0.0.1:18765`，服务 PID `3337058`，`/api/runs` 返回 200；Linux Braid binary 已编译并具备 `telemetry reconstruct --decoded`。这证明服务可启动，不证明真实 run 的生产、传输和投影已通过验收。执行 owner 的最新交付仍缺真实 ARC target/Hosted 接线，restart 仍有创建目录与旧 handle 继承问题，主未采用其“闭环完成”声明，已要求同一 owner 持续修复到实际可启动。当前仍没有本任务收费运行。

公共 observer 已接入 Console saved-facts 发布，终态只有 `save` 明确返回 `saved: true` 才结束；发布失败独立记录，不改变运行生命周期。共享字段为 `observability.service_url`、`registration_token_file` 和 `collector_token_file`，秘密不进入迁移 data。此接线仍需真实生产者验证。

主已实地只读确认 sfp7 HTTP 200；服务部署期间重启，PID 不作为永久身份。初次列表包含本任务构造的登记，不能证明真实生产链路，已要求 owner 删除；owner 已报告清除并明确旧 facility4 缺少 status/native turn/cost。约 27 MiB 的单次 RSS 只属于空载服务，不作为低内存验收结论。当前源码中的旧 `lab.control.Control`、exclusive/send 写入链没有调用方，已删除，保留进程出生身份与历史只读等待；这不等于整套 lab.exp 已退役。

主分担 `lab/arc_bench/hosted_run.py` 的真实官网 API 适配，执行 owner 继续负责打包、数据映射与实际 dispatch 接线。新模块保存 upload/create/start/cancel 请求及响应、真实 submission/run ID、日志 cursor、平台费用和全 workspace ZIP；未知写请求不自动重发，5xx/传输不明不冒充确定失败。当前只通过编译，未调用收费 API；规范 data 在平台导出中的映射和原生接续尚须与实际包完成闭环。

旧入口退役的调用核对确认：新评测仍可经 ARC adapter 导入旧 artifacts/core/telemetry，I14 的 experiment_entry/bootstrap 仍带 state_writer，package_agent/runtime 也被其他当前材料构建调用。整目录删除 lab.exp 会破坏这些维护调用方；已经冻结的 runner.pyz 不读当前源码，但重新构建仍受影响。新 run 必须提取实际 ARC/材料功能并切断门控，而非依赖 gate 在某些环境 no-op；旧源码中他人的未提交变化不得覆盖。该核对由 cold_local_profile 完成，只读，没有控制旧运行。新增 advisor 委派被平台 thread limit 拒绝，当前没有取得新的重大退役取舍意见，不把只读依赖核对冒充 advisor 建议。

## 当前需求与决定

用户要求先定义“怎样算好的实验设施”，依据实验需求、工程知识、Agent 使用 profiling 建立完整因果链，不为找问题而找问题。Mac、WSL、sfp7 和官网差异属于设计对象，环境触发、集成耦合与设施内部缺陷分别归因。Exp Console 属于实验基础设施，不留作无期限的外围改进。

用户随后明确要求：Exp Console 不再承担实时介入；数据走 OTLP，Braid 自己实现 Braid 视图；本地共享包含 Collector/Backend 的观测服务，官网执行仍轻量自包含。还需资源采集，耦合 ARC-Bench 并统一 variant/gateway/collector 装配与路径，Python 条件自动取消/接续，自动保存完整工作区、日志、评测和费用，移除所有 gate/校验，三参数启动与停止/挂起，以及 stages。最后提醒“这个任务不小哦”。以上全部属于本轮设计范围，不按截止日期偷换成少数入口修补。

2026-10-06 用户补充了自动且强耦合的自实现模拟测试、官网重放、试题自带三类评测，统一各 variant 共用的 gateway/collector 装配，以及来自采集的 spend、native session turn idle 等 Python 变量。同期提出的跨 variant、多路径接续后来被用户撤回，当前同 variant 整体 data 迁移的决定见下文。

本次授权原话：“我同意你定下的这个推进方案，在开始实现之前和我确认方案，你可以自由继续推进。”这是推进方法及设计工作的认可，不是当前 HLD 所有取舍已获认可，也不是开工许可。下一次集中复核应给出可决定的架构、具体改动范围、独立预演结论及真实验收安排。

用户随后明确：“核心调度对象/控制单位是run，而不是实验。（我后续还会不断补充，你不必停下）；你总是可以有不同的看法”。已撤掉把 run 定义为整条实验链再用 attempt 控制的候选；每次实际可独立派发/停止执行是 run，内部阶段服从平台真实粒度。来源、接续、重试和独立评测通过 run 关系连接，experiment 仅标签。stop 只操作指定 run，跨 run 操作与费用范围由普通 Python 程序明确表达。

用户质疑“撤销尚未派发的自动后续”是否仍保留 capacity/queue。复核确认这是设计越界：把尚未执行的 Python 代码想象成了设施待办任务，执行调查稿也残留 reservation/slot 的目标措辞。主 Agent 与 advisor 已撤回建议，目标设计删除内部 capacity、admission、slot、reservation、运行队列及未来任务撤销机制；历史故障证据保留。启动直接尝试执行，资源不足返回实际错误。Python 直接调用运行 API，不增加 action 解释层或任意脚本断点恢复；默认 stages 只在 completed 后继续，显式 restart 仍可处理 failed/stopped。stop RUN 不停止独立自动化程序，两者不混称。

用户最新修正要求：suspend 改 pause；接续不能用 continue；程序与数据路径规范后，只迁移数据且不允许切换 variant，extract 无意义；新增 status，无参数列未归档、非正常结束的 run brief，由绑定 variant 的脚本解释活动；继续收敛到可列实现计划，计划不含信息收集、调查或实验。当前采用 restart 表达同 variant 新执行，覆盖 stop→保存确定数据→迁移→启动的顺序；status 默认条件为未归档 AND lifecycle != completed。状态脚本固定在本次 program 版本，只读采集事实，脚本错误显示 unknown；正常执行得到零分仍为 completed。archive 仅列表标记，自动保存结果另行完成。此段覆盖前述历史 cross-variant、多路径接口及命名建议，设计正文以最新决定为准。

第二轮独立文档预演已经能推导启动/status、pause/resume、restart、归档后查回与独立评测；唯一操作缺口是自动三类评测的实际启用和官网费用来源。已补 task.json 的 evaluations 清单、同一应用快照绑定及 official billing_mode，不加许可字符串/审批门禁。另经 advisor 核对 Braid retained request 的实际约束，明确同 task 用原 native 状态、下一 task 建新状态，避免旧 root 已结束就跳过新需求。预演仍是文档反馈，不是运行验收。

主 Agent 与 advisor 的建议是删除重复证明、准入和人工写入协调，但保留路径边界、秘密处理、准确控制目标、未知收费写入防重复这四类直接风险约束。这是明确提出的保留建议，不声称已获用户认可，也不改名藏回“全部移除”之后。具体理由见 design。

Collector/Backend 推荐来自现有接收能力、所需领域查询和部署总成本，而不是只因赶期限或最小代码行数。没有“新架构已经验证”结论。最小可用交付必须纵向包含执行、观测、控制和归档；分批决定交付顺序，不取消完整目标。

## 负责人及可采用结果

| 负责人 | 范围 | 当前交付 |
| --- | --- | --- |
| 主 Agent | 产品要求、评价标准、跨组件 HLD、方案复核及 packet | 本 packet、design、evaluation、assessment |
| execution_owner | 两个派生 variant 的程序/数据分离及原生接续 | 材料构建不能替代实际同 task/new task 验收 |
| evaluation_implementation | evaluate/package_arc_replay 独立评测 | 尚待真实应用快照 |
| cold_console_profile（承接原 observability_owner） | OTLP、资源/费用/turn、Collector/Backend、Console 与 Braid 边界 | [观测专项](cells/observability.md)，原 owner 已不在活跃树，主 Agent 在本轮明确转交收敛责任 |
| finals_infra_advisor | 重大工程判断，不担任实现 reviewer | 明确 restart/native task 分支、status/archive、Python 自动化及 Braid 自有低频物化视图，已整合到 design |
| continuation_journey_rehearsal | 首次使用者的独立文档预演 | 两轮桌面使用反馈；最新补齐评测清单与费用模式入口，旧多路径意见已随用户修正失效；不是运行验收 |

只读实施准备得到两项具体采用结果：sfp7/WSL 可用空间约 110.8/25.1 GiB，WSL 已有本地 Console，跨域 HTTP 未验证；Pi 历史主会话 274 条 usage 的原生 cost 全零而平台有实际费用，raw OTLP 省略 message_update、timing 仅 first_update，不能直接作为精确 idle。原件与限制分别记录在执行、观测 cell，主线未控制这些运行。

第一轮 facility_journey_profile、environment_causality 和三个 cold-profile Agent 的结论保留在 assessment。后续相关工作保持原 owner；profile Agent 的原始意见不自动等于已采纳事实。

## 证据与更正

2026-10-06 的三次只读冷启动调查墙钟分别为本地 95 秒、Console 164 秒、Hosted **214 秒**。这是 Agent 执行整个调查的墙钟，不是独立测得的主动劳动。Hosted 原返回写成 114 秒，已按 epoch 差更正。Console 样本为纯 Pi variant，不产生 Braid 是预期行为；其 creation 快照也不能证明从未运行，历史读回实际已有 Pi 请求和工具活动。不能用这个样本证明 Braid 接入失败。

历史 capacity 拒绝原件有价值，但不能仅凭报错断言 admission 正确或存在泄漏。另一任务后续保存了 terminal 仍占槽、writer-close/release 及下一次 reserve 的证据，应据其解释生命周期接缝，不能把旧失败快照当当前运行状态。

- [当前设施证据与因果判断](assessment.md)
- [质量标准及 profiling 方法](evaluation.md)
- [完整需求与 HLD 草案](design.md)
- 历史基线：[实验 DX 复核](../experiment-dx-review/packet.md)、[实验操作](../experiment-operations/packet.md)、[实验追溯](../experiment-traceability/packet.md)
- 顺序阶段历史：[Pi Stage2/3 packet](../pi-minimal/sequential-stage2-stage3-20261006/packet.md)
- 本任务只读分析快照：runs/finals-experiment-loop/readback-20261006-analysis.json
