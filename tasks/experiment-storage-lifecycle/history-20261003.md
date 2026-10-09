# experiment-storage-lifecycle

- **Objective**: 为 Factory26 的运行时、缓存、workspace、Braid/native/OTLP、应用和评分证据建立可验证的归档、预算、引用与安全回收边界。
- **Guardrails**: 不触碰 I12 暂停现场及其 restart、shared submission、Braid/Console、容器和 watcher 依赖；不运行模型实验；不新增或运行 Factory/Braid 测试。实现使用编译、静态核对、实际制品操作及后续单独获授权实验验收。
- **Authorization**: 用户于 2026-09-30 确认普通实验默认采用 `decision` 归档级，并授权“直接改进 braid 的 OTLP 导出内容、内部采集/埋点等”，要求创建独立分支和 worktree 开始；随后明确“可以自由提交”。授权范围包括本方案需要的 Factory、Braid、文档和任务包改动及当前任务提交，不包括模型实验、历史清理、I12 现场迁移或 VHDX 停机操作。
- **Workspace**: 当前在 `/Volumes/WorkSSD/Development/factory26` 的 `main`，原独立分支/worktree 已按用户授权合入及清理。下文 2026-10-01 及以前提交是历史阶段；本轮只提交空间与定义/状态分离改动，保留其它任务的未提交内容。
- **Current Truth**: 历史快照中 `telemetry.sqlite*` 约 18.7 GiB，Braid SQLite 约 0.12 GiB；大 telemetry 样本超过 99.8% payload 是 logs。源码确认完整 native/对象 evidence 被周期性分片写入 OTLP。隐藏的 attempt-local interpreter/runtime 和完成后缺少独立 reclaim 判据，使目录名或 `completed` 都不能安全授权删除。
- **Decision**: 普通 Factory 实验使用 `decision`：长期保留应用/replay、必要 Braid state、关联 native 原文、评分和错误；完整 OTLP、整棵 workspace 仅在逐轮明确的 `resumable`/`forensic` 级保留。执行/cleanup/recovery 引用可以 pin 物理对象，provenance 只保留身份和位置事实。
- **Implementation Status**: Braid 提交 `e87b82b` 将运行期和默认手工 export 改为有界摘要；只有 `--portable` 发送完整原文，增加源材料 bytes/artifacts 指标，并保留既有离线重建格式。Factory 提交 `57cd761` 已接入默认摘要、`archive.json` 回执及“回执授权后才删除 work”的门禁，提交 `e222296` 已增加 lab schema v3、冻结的 storage policy/解释器依赖及启动 preflight，提交 `cfc7aa2` 已增加异步实际占块观测、80% 派发门禁、100%/host reserve/inode 的受控进程组 TERM/KILL，以及外部资源 `unconfirmed` 边界，提交 `956de0b` 已将 controller、job、inspect/cleanup 绑定到同一份稳定宿主 Python 资产回执，提交 `e6e1a5c` 已增加失败关闭的只读 GC plan；只有完整 v1 archive 回执的精确 `work` 能成为非授权候选。
- **Integration Authorization**: 用户于 2026-10-01 明确：“好的，也可以委派开工 合入 experiment-storage-lifecycle”。授权 Factory/Braid 源码与文档合入及必要 I13 适配、非模型编译/CLI/prepare-only 和当前任务限定提交；不含资产建立、历史/I12 GC plan、apply、真实清理、迁移或物理运行控制。
- **Current Integration**: 六个 Factory 来源提交已按 delta 合入开发主线，I12 收尾改动仅映射到 I13；Braid e87b82b 已整合为目标 8325ed6。集成收紧真实原文保存门禁、decision-only 支持边界，加入 I13 GC 保护，并将新应用复评配方适配至稳定 Python/预算 schema v3。Python/Rust 编译、CLI 帮助及真实 prepare-only 通过，运行期归档/预算/GC/传输行为未实测。
- **Next Step**: 完成本轮四 I14 定义/状态分离、checkpoint/prepared v3、监控与载体生命周期接线，以及编译和现存材料离线反馈。完整 prepare、Docker 启动和热恢复仍需要真实冻结 I14 runtime/material，并在其实际执行授权内验收；本轮不创建运行现场或清理旧数据。

## 空间增长调查（2026-10-03）

用户要求排查每次实验至少消耗 10 GiB 的原因，本轮授权为只读调查及任务记录，不是新一轮源码修改或清理。当前目录在 main，先前 worktree/分支说明属于历史阶段。现存 I13-2 累计目录计量 167.49 GiB，其中 Sheet collector 的 monitor 约 52.13 GiB，三个平台 run 共 105 个完整 workspace ZIP 合计 26.73 GiB。当前源码还存在输入、终态、输运与恢复阶段的全量复制；正式新 DX 的共享 artifact store 和 runtime 已经复用，不能将其错误算成每 run 独立副本。

当前结果、证据口径、源码归因和下一轮方向见 [空间调查](investigation-20261003/findings.md)。未修改源码、未删除数据、未运行模型或设施测试。进一步实施需就监控证据、恢复内容与载体生命周期的具体范围复核；本次没有宣称三类端到端耗时或增量空间验收通过。

## 空间优化开工及边界修正（2026-10-03）

用户针对调查结果明确授权：“是的，这些属于实验基础设施，请进行优化”。进入监控证据保留与终态、回传载体生命周期的源码实施；本轮不执行模型、平台请求、Docker 控制或历史清理，沿用编译及真实已保存材料的离线反馈。storage_producers 持有制品、终态和输运改动，exp_platform 持有监控证据实现；主 Agent 持有整体合同与整合。其它任务未提交修改保持原样。

用户随后指出：“定义数据和运行数据分离，其实不仅仅是实验基础设施而言，还是 variant 内部实现而言，但这也同时是实验基础设施的责任”。独立复核确认此约束必须覆盖实际入口：variant 将 binary、技能及动态配置拷入 run，SDK instrument_entry 又把整个材料放入 workspace；终态完整捕获会重新携带 runtime。现有共享 store、COW 及 scratch 释放只能解决部分成本，不能作为定义与状态已经分离的完成依据。

已将资产、派生输入、可写状态的职责以及旧冻结兼容约束同步到 [DX 设计](../experiment-dx-review/design.md)。Variant 声明语义，设施承担真实装配、引用保留与状态捕获；新合同需在入口、捕获和恢复端贯通，不能仅增加 manifest 或按目录名排除。当前监控与载体优化继续在其已明确的边界实施，variant/SDK/checkpoint 新分离合同正在收敛，尚未宣称实现完成。

## 定义与运行状态分离开工（2026-10-03）

用户认可分层后明确：“这个分层没错；我们开始应用吧/开工吧？”本条授权覆盖四个新 I14 variant、公共材料生产接线、SDK 交付装配和 checkpoint/prepared 的实际消费边界，继续完成已开始的监控与载体生命周期优化；不扩大到模型、平台、Docker 运行控制或历史清理。主 Agent 持有公共布局、SDK 与整合；exp_platform 接续监控后持有四 I14 入口；storage_producers 持有 v3 捕获/准备与 controller、runner/backend 消费。Advisor 已独立收敛 ABI 和旧合同约束。

新运行的 harness-layout 声明定义资产、派生输入与可写 state。派生的小型配置、request 和 launcher 留在本次 state 内，不为了语义分层再制造多套 artifact。定义在 runner 实际输入中绑定 reference/member；Hosted 只有 package identity 时不伪造可恢复 artifact relation。Checkpoint/prepared v3 保存状态及冻结定义依赖，目标 store 只作实际解析位置；v2 仍按原自包含合同解释。同一资产内的嵌套定义角色折叠装配，状态与定义重叠拒绝。Docker 保持真实只读挂载，Local 沿现有 verified-read 和写隔离合同，不宣称新内核权限隔离。

验收使用现存真实材料的离线生产、装配、读回和编译。另一任务清理后当前无可用新 I14 冻结 runtime/material，不能伪造 runtime 或改写旧 run phase 来取得反馈；完整四 variant prepare 和真实 Docker 生命周期按实际材料前提报告，不能用局部副本操作替代端到端验收。

## 本轮实现结果（2026-10-03）

四个新 I14 材料及入口已接入三层布局，Braid 与静态技能直接引用冻结定义，派生配置和 native 可写状态留在 run。打包选择冻结布局支持及公共 prepared executor，四入口实际支持 `--execute-prepared`。Checkpoint/prepared v3 保留状态与独立定义依赖，消费端解析及装配这些引用；旧冻结记录仍按原版本合同解释。一次消费窗口按真实 store/reference 复用已验证资产，不为语义角色重复读取完整 payload；prepare 的同引用输运也去重。

Docker 恢复使用独立 `state/run`，保持原逻辑路径并贯穿启动、named outputs/result、导出预估与实际导出；定义只读。首次运行与 prepared 的 `export.json.state_binding` 绑定原执行 namespace、环境身份和本机安装内容，checkpoint 显式消费真实回执，不能把导出主机当作原环境。定义修复保留前后关系，不改旧资产；Local 逻辑位置被占用仍明确阻塞。

SDK 交付副本移到外层状态目录之外，保留其原导出树和 inventory。终态归档仅在实际路径映射、保留关系及内容证明成立后省略定义子树；缺口保留原材料。终态 sealed evidence 使用移交发布，Docker 下载后安装使用 rename，新 SDK transport tar 在已持久验证后释放，避免完整载体长期并存。以上 Docker/SDK 和完整恢复接线已实现并编译，实际生命周期反馈范围见下节。

监控优化已独立提交 `302878bc`。其它本轮源码、文档及反馈限定提交；AGENTS、Braid 与 iteration14 其它任务修改不纳入。当前 20 个 Python 源码及 2 个生成入口编译通过，有限 diff 检查通过，未增加或执行设施测试。实际依赖保留及成员身份反馈见 [成员消费回执](investigation-20261003/retained-member-operation.json)，编译入口见 [编译记录](investigation-20261003/compilation.json)。

## 本轮反馈与验收口径（2026-10-03）

监控使用既有真实终态 ZIP 离线取得反馈，原 ZIP 为 164,995,785 字节，前后 SHA 一致且继续保留。永久判定证据为 6,508,663 字节，15,236,514 字节的提取 scratch 在持久化后释放；六个 provider 的活动及 fingerprint 与完整读取一致，required_reads 均指向仍存在的永久文件。一个原生来源在原 ZIP 中已经缺失，仍保留 absent。见 [监控操作回执](investigation-20261003/monitor-operation.json)。普通轮次 ZIP 物理释放与同故障连续去重缺少现存样本，尚未实测；全量 ZIP 网络下载没有减少。

现存仓库文档及制品模块共 65,050 字节通过实际 COW 复制、sealed handover 发布、同请求重入及 materialize 读回；移交后 staging 已消费，同请求身份一致，消费者内容一致。公共布局随后读取该真实已发布资产，三个语义角色均绑定同一 reference/member，状态另存。见 [资产操作回执](investigation-20261003/asset-operation.json)。这是资产机制反馈，不是可运行 Harness 或完整 prepare 反馈。

本轮不宣称已验收“每次至少节省 10 GiB”，也不以局部毫秒级副本操作代表打包、启动、热恢复端到端耗时。缺少新 I14 冻结 runtime/material 及新 wrapper 的真实终态 namespace 原件，完整四入口 prepare、Docker 生命周期、SDK 正向组合捕获和热恢复的实际运行反馈仍待这些前提。

## Supporting Material

- [治理设计](design.md)
- [I13 合入回执](../iteration13/storage-lifecycle-integration.md)
- [合入前历史](history/)
- [WSL 应急治理记录](../../runs/wsl-retained-20260930/README.md)
- [运行说明](../../docs/deployment/index.md)
- [产品技术说明](../../docs/product-tdd/index.md)
