# 现有设施的证据与因果判断

## 2026-10-07 原定目标达成核对

整体尚未达成。完成标准是使用者从正常入口低负担地开展、控制、接续、评测并解释实验，不是组件启动、包变小或某个模型请求成功。以下核对区分实现、实际观察与缺口；下文的2026-10-06调查和较早边界诊断保留历史身份，不代表当前源码。

独立性范围已更正：新验收会话后续得到主会话持续的根因、操作路径和预期观察辅导，其实际运行证据仍可采用，但整体属于受辅导的集成修复验收，不能证明无背景使用成本低。依据真实人类对话及具体委托的复核见 [evaluation 的独立 Agent 代表旅程](evaluation.md#独立-agent-的代表旅程)。现有两条运行继续完成，不为沟通纠偏新增收费运行；设计者的额外介入计入使用成本。

| 原定目标 | 当前可采用事实 | 尚未达成的部分与下一步 |
| --- | --- | --- |
| run 控制、三参数入口，无容量队列 | lab.run/CLI已接入真实执行；新版失败run保留身份、原错并自动保存；新Pi正常双spawn观察已工作；a3接续已连续完成真实模型响应 | 两个DX完整生成链均未完成；I14的756仍blocked且完整保存，已定位到本地修正未进入远端编译输入，主负责重新构建并正常接续 |
| 公共装配与统一环境，variant保留原生语义 | public_package拥有最终装配，同一安装器及lock；Linux代理两别名真实HTTP200，装配字节一致 | 不能以装配成功代替真实Harness使用；原设计中完整runtime挂载路线已被替代，适配对象仅本轮两个DX派生variant |
| 启停、pause/resume、同variant数据接续、原生stages | Pi由WSL跨宿主restart到sfp7已实际保留同task/native scope并取得模型响应；题目stages由三参数入口接入，无新增控制对象 | 当前交付的pause/resume、I14同task接续及下一task新原生身份/业务数据保留、自动stage推进尚未完整验收 |
| 自动保存成功、失败、停止现场 | 旧610daf停止回收完成；新0aeae2、782227失败均自动saved；本机与远端回执已分开 | 完成生成的应用、自动评测原件与阶段关联尚未形成；强制取消后的平台范围仍按实际能力报告 |
| 采集驱动的spend/idle自动操作 | 新Pi的status/CLI已实际显示本run已记录原生token；按时间排除迁移旧消息，覆盖明确partial，不采用cost零占位 | 供应商账单/已核实请求价格尚未接通，金额仍未知；用量不代替费用，idle动作实际覆盖仍未闭环 |
| Exp Console/OTLP与Braid自有视图 | 独立验收已从首页查看d3cc真实终态、原生502、资源、用量/费用未知、来源及参赛false；通用详情轮询/刷新、Pi查看入口与最新native选择已修复部署；主实际观察a3页面在无操作时更新活动、日志与资源 | 早先active详情缺事实的报告不能仅凭前端修复推导API根因；最终评分分析和Braid完整协作分析尚未验收 |
| 四个测评后端与自动评测 | 接口、task配置和self-test认证接线已存在 | 新版应用未生成完成，随题、模拟、self-test尚无本轮评分；已确定关闭的Hosted入口保留拒绝证据，不重复上传或参赛来填矩阵 |
| 资源管理：观察、补救后明确失败，不持续pause | Tini入口、memory/pids观察及有界补救已落地，真实浏览器一次生命周期无浏览器残留；Pi实际有内存/pids/限额采样 | 长运行孤儿回收、资源触顶后的真实有界补救与退出仍缺本轮证据；采样值不是峰值或补救成功证明，不制造资源故障填表 |
| runtime精简、构建部署及使用成本 | 程序材料约16MB；普通observer源码从约246MB收窄到约2MB，820e0a2e已提交；新Braid修复仍需约12分钟Linux release编译 | 约512MB安装占用不能说成16MB运行占用；源码范围缩小尚无正常启动提速实测，主动操作/token/排错成本未证明整体降低 |
| 应用开发与评测环境一致，默认无需补救 | 真实Linux公开GitHub基线副本已完成公共ensure、npm安装、后端17项测试、前端构建、正式服务和portless health200；应用及后台子进程Node20.19.3/npm10.8.2，工具Node24.10.0 | DX完整原生生成/接续与自动评测仍待主线；基线前端自身测试失败保留，不改应用来使设施验收通过；不扩历史variant/I15、不宣称已解决Vitest慢点 |

采用completion_criteria_decision advisor的优先级：先完成已有Pi/WSL闭环并定位I14启动阻断，同时用已有run验Console；费用采集缺口由主处理，不无限优化应用分数、不继续以runtime优化替代产品验收。独立验收仍绝不参赛，模型只用variant声明的当前自费配方。真实模型/平台等待与设施主动操作分开计时；尚无依据声称普遍节省比例。

Pi d3cc已failed、Mac完整saved，记录1,444,211 native tokens、coverage=partial，金额不是tokens换算值；新a3已连续取得完整响应，独立会话最新观察122 provider turns及约1.24M token，仍在应用实现/验证、尚无终态或评分。应用环境统一细节及Linux验证归[应用环境packet](../harness-app-environment/packet.md)。Hosted生成关闭是外部覆盖限制，不能用self-test替代Hosted生成/取消/轻量采集验收；比赛分支在本轮绝不实际运行。未知费用不能当零，费用采集仍须反馈，不因平台限制免除。

本页区分已观察事实、能力边界和设计推论，配合 [评价标准](evaluation.md) 与 [HLD 草案](design.md) 使用。调查对象是 2026-10-06 读取的工作区和历史运行材料；仓库仍有其它任务在修改，历史快照不代表现在的运行状态。

## 分层调整前的调查与设计判断

2026-10-07 分层调整前对新 DX 实现的边界核对：公共 gateway/OTLP/seed-data/运输装配当时仍重复在两份 variant build.py 内，且 OTLP 和 proxy 依赖默认引用历史 runs 路径；公共 harness_services 又包含 I14 的 DeepSeek selector、visual identity 推断和 Pi/Braid 原生目录权限修复。execution 的原生事实采集也直接解释 Pi JSONL 和 Braid 状态。因而“服务实现共用”并不等于职责已分开：公共升级仍需逐 variant 接线，原生布局修改又传播进通用服务。两个 DX README 当时还保留旧 ready-context 或 private-models 接线，不能作为当前边界依据。本段保留问题识别的历史因果，当前达成判断以上表和对应新run为准。

采用 advisor 的设计判断作为待落实建议：公共装配拥有最终产物及公共服务启动、data 运输和执行生命周期；variant 拥有角色/技能选择、原生模型映射、会话接续、完成与交付判定、状态解释；多个 variant 实际共用的 Pi/Braid 机械适配保留明确原生身份的 helper。公共装配在 variant 材料准备后统一加入基础设施，不只抽取重复函数再要求每个 variant 选择调用。Portless 是应用开发服务代理，不与 LLM gateway 混同；ARC history 发布机制可共享，发布来源与时机仍属 variant。本次为只读诊断及建议，未更改源码或在途运行。判断效果以一次公共 gateway/OTLP 变更自然被两个 variant 新装配采用、原生布局修改不再要求公共服务猜路径为准，不增加插件注册或通用 hook 框架。

现有设施已经能保存输入、请求与外部身份、原始错误、工作区和部分原生过程；runner/observer 不依赖聊天存活，Hosted 评分事故也能事后取证。这些是可复用的能力，不等于必须保留提供它们的全部 compiler、receipt、authority 或 reservation 结构。

新需求改变了职责：实验入口专用于 ARC；Console 改为只读 OTLP 查询，Braid 拥有自身视图；运行 owner 执行 Python 条件策略与自动回收；本地共享观测、Hosted 自包含。现有实现中与这些职责相反的机制已有源码证据，可据此提出删除或替换，不需要先制造更多事故。但现有材料不能给出新架构提速比例，也不能证明“全栈必须重写”。

此前“优先保留 lab.exp 内核、只做纵向接缝、先收敛单一环境”的结论过早，已撤回。当前以用户需求和总使用/维护成本比较复用、重构与重写，不将任何候选预先排除。

## 只读冷启动 profiling 的有效范围

三个 Agent 从目标身份与文档入口开始，只读取材料，不启动服务或运行：

| 任务 | 调查墙钟 | 命令批次 | 有效观察及限制 |
| --- | ---: | ---: | --- |
| 本地 Stage2 状态与失败原因 | 95 秒 | 9 | 找到 admission 原错；默认 status 未直接给出该错误。没有测量启动、模型活动或实际重试成本。 |
| Console/Braid 阅读 | 164 秒 | 18 | 暴露现 Console 仅接 Braid 和人工登记的产品范围。样本是纯 Pi，要求寻找其 Braid run 不成立，不能据此判定 Braid 接入损坏。 |
| Hosted 0/29 的过程和原因 | 214 秒 | 17 | 能区分生成、评分、旧状态与独立 self-test。包含阅读既有分析报告，并非从原件独立重做全部诊断。 |

Hosted 起止 epoch 为 1791284729 与 1791284943，差 214 秒；原返回的 114 秒是算术错误。上述墙钟包含阅读、推理、工具等待和结果整理，没有分段计时，不能标成“主动耗时”。命令批次和约略跳转数是定位线索，不是稳定性能指标。

Console Agent 还误把 generation.resource.json 的 creation 状态当作运行从未开始；对应任务后来保存的实际读回证明 Pi 已发请求并修改应用。该推论撤回。另一条“Kimi 只属于候选路由”的推论也不采用：Flash 是主模型，Kimi 是原生 advisor，应查角色配置与实际请求。

## 代表性因果链

### 本地停止后的容量接续

stage2-experiment-kimi-max32768 的 attempt-ca3155869da3166b303fadac 在 admission helper 报 `capacity exhausted, unknown reservations retained` 后退出。外层 exit 1、归档保存和 generation 未进入执行是不同事实；仅看默认状态需要额外下钻才能发现首错。

[对应运行 packet](../pi-minimal/sequential-stage2-stage3-20261006/packet.md) 后续记录，两条占用 execution slot 的记录均已 terminal/pending=null，分别属于历史 I14 和本轮已停止的 262e；本轮 writer-close/release 成功后，新 e3107 获得 reserve 并进入材料输运。原件入口为旧 attempt 的 workspace/user-stopped-capacity-release.json 和新 attempt 的 workspace/all-runs-status-snapshot.json。

这条证据支持的链条是：用户停止生成 → 运行终态但容量责任尚未关闭 → 下一次启动被阻止 → owner 调查并关闭本轮责任 → 下一次 reserve 成功。它说明“停止完成、保存产物、释放可用容量”的跨组件交接对用户有真实成本；不能只归因为机器容量不足，也不能据此认定所有 unknown reservation 都是泄漏。该后续事实来自另一任务的记录，本任务未控制这些资源。

本轮设计已经决定由实际 ARC/Docker 生命周期承担执行责任，删除内部 capacity、slot、admission、reservation 和运行队列；资源限额与采样仍由实际执行器提供。上述历史证据保留为旧机制使用成本，不再把“是否保留配额框架”列为待决问题。当前无需修复或清理这些历史运行才能继续设计。

### Hosted 0/29 与应用自身缺陷

Hosted run 32db20c04573 的历史证据显示生成已交付应用，但正式 29 个场景均在浏览器启动前失败：`/ms-playwright/chromium-1200/chrome-linux64/chrome` 不存在。独立 self-test 的 3/29 另外暴露应用缺陷，不能混为正式 0/29 的原因。

因此重写本地 runner 不会修复该 Hosted 浏览器缺失。设施应自动保存平台错误与评分原件，让使用者能直接区分环境失败和有效业务评分；为什么平台目录缺失仍需平台证据。原件/报告入口：runs/deadline-20261003/final-score-check-20261006/pi-stage2.json、runs/deadline-20261003/pi-zero-analysis-20261006/stage2/report.md。本任务没有重新评分。

### Console 的旧职责带来的成本

当前 Console 文档和实现要求显式登记 live/archive 来源，并依赖 Braid binary、state、workspace 或 accessor。登记与公共服务锁耦合，浏览、现场读取和实时写入的生命周期绑在一起。这些是源码/操作合同事实，不由此次无效的纯 Pi/Braid 样本推导。

用户已不需要实时介入，因而 Braid 写桥、writer/accessor、停写与 capture 协调不再服务当前 Console 产品要求。删除这些职责，改由 OTLP Backend 保存数据并由 Braid 解释自己的对象，才可能真正消除现场耦合；只是新增自动 registry 或隐藏写按钮会保留多数成本。Pi-only 仍应作为正常实验展示通用过程、资源、费用与结果。

证据入口：braid-console/README.md、braid-console/docs/contracts.md、docs/deployment/console.md、braid-console/service.py。

### 采集变成启动前提

scripts/execution_bootstrap.py:19 的 resource() 在要求 cgroup 却未找到，或首次 sample 未持久化时抛错；Linux payload 入口以 require_cgroup=True 调用。由此，辅助观测缺口可直接阻止生成。这是设施耦合，不是资源曲线缺失本身导致 ARC 无法执行。

同文件 collector() 创建每次运行的 lab.exp.telemetry.Collector。当前 receiver 已支持 OTLP traces/logs/metrics 和原件存储，但不能据“支持 OTLP”就认定本地共享部署或 Hosted 低内存目标已经满足。应分别复用协议处理能力、改变生命周期，并测量实际采集开销。

### 已有 Braid 导出与未知覆盖

Braid 有 OTLP 三信号，默认周期 EvidenceWorker 使用 Summary；Portable 导出还能产生 evidence_chunk 与 evidence_artifact。因此“OTLP 无法承载原生过程”不是正确结论。真正待核的是默认生产者输出是否足以支持所需视图、native turn 与费用字段是否准确、断连后如何补齐。整个应用工作区仍按文件归档，不为统一协议而全部塞入 OTLP。

纯 Pi 有自己的 raw_otlp.py 生产链，不套 Braid 对象合同。证据入口：sources/braid/src/telemetry.rs、sources/braid/src/evidence.rs、variants/pi-minimal-vv/main.py、variants/raw/raw_otlp.py。

后续定向原件核对进一步确认：Pi 的 session usage 原生 cost 全零，不等于平台实际无费用；raw OTLP 不发送 message_update，timing 只记首次更新，因此现成 OTLP/timing 不能直接给出准确 idle。需要把持续活动和生命周期从生产者接到执行侧策略，再输出观测。字段与规模见[观测专项](cells/observability.md#2026-10-06-定向原件核对)。这不是运行测试或新实验。

## 设计判断与剩余不确定性

可以据现有证据提出：三参数入口和 ARC 装配、统一 target 配置与路径、取消 Console 的现场写入依赖、资源采集不门控、单 owner 的 Python 策略、终态自动回收、顺序应用 stages。它们分别对应重复装配、职责改变、故障传播和真实阶段需求，不是为了减少文件数量。

仍需收敛的关键事实是：共享服务实际部署与可达性；现有 OTLP 查询/存储能力是否适合新 Console；native session turn 的生产语义；Hosted 可导出目录、强制取消后的回收时点及采集内存；具体哪些现有执行/资源机制可整段移除。Mac、WSL、sfp7、Hosted 需要明确 target 边界，不必假装能力相同，也尚未决定只支持其中一个自管宿主。

更新的只读部署调查已确定首选 sfp7 作为共享 Backend 宿主，依据是约 110.8 GiB 可用空间相对 WSL 的约 25.1 GiB；两者仍保留执行 target。WSL 实际已有 loopback Console，修正“Mac 没看到服务等于没有 Console”的潜在误推。跨执行容器 HTTP/OTLP 可达性仍未验证。当前推荐复用 lab/otlp 协议接收、增加专用查询，且以真实峰值决定是否替换存储；不把这些选择当已完成部署。

下一轮 profiling 用同一任务输入和明确环境比较完整用户旅程，分开记录机械操作、寻找信息、执行等待和返工。现有故障原件可以先用于数据/视图设计；服务启动、费用/turn 策略、挂起和跨阶段运行必须在明确授权的真实运行上取得证据，不通过编写替身测试来宣称完成。
