# 现有设施的证据与因果判断

本页区分已观察事实、能力边界和设计推论，配合 [评价标准](evaluation.md) 与 [HLD 草案](design.md) 使用。调查对象是 2026-10-06 读取的工作区和历史运行材料；仓库仍有其它任务在修改，历史快照不代表现在的运行状态。

## 当前能作出的判断

2026-10-07 对新 DX 实现的边界核对：公共 gateway/OTLP/seed-data/运输装配仍重复在两份 variant build.py 内，且 OTLP 和 proxy 依赖默认引用历史 runs 路径；公共 harness_services 又包含 I14 的 DeepSeek selector、visual identity 推断和 Pi/Braid 原生目录权限修复。execution 的原生事实采集也直接解释 Pi JSONL 和 Braid 状态。因而“服务实现共用”并不等于职责已分开：公共升级仍需逐 variant 接线，原生布局修改又传播进通用服务。两个 DX README 还保留旧 ready-context 或 private-models 接线，不能作为当前边界依据。

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
