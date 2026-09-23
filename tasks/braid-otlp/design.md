# Braid 运行诊断方案（待开工）

## 已核对的现状

Factory `scripts/local_experiment.py` 注入 endpoint、HTTP/protobuf、run token header 和无压缩配置；`arc_bench_adapter.py` 转换容器可访问地址。`scripts/otlp_store.py` 接受三个信号，只持久化原始 protobuf，每批限制 16 MiB。HTTP 200 表示保存批次，不验证 Braid 语义或会话完整性。

Braid 已有 OpenTelemetry 0.32、tracing bridge 和三个 exporter，但 `main.rs` 只安装 stderr subscriber；实际 local 路径没有调用 `TelemetryGuard::install`。现有 `run_probe` 不在 CLI 命令树中。只调用 install 还会与 main 的全局 subscriber 冲突。`emit_payload_event` 又依赖当前 recording span，而 provider 的 stdout/stderr reader 是独立 spawn，当前没有运行 span 的传播。现有唯一业务 metric 是未接线的 probe counter。

SQLite `local_items`、`local_comments`、`associations` 和 `local_merges` 是本地对象权威。普通 Context/CLI 展示会隐藏已折叠正文；诊断导出不能复用这个有损投影。已有 events 记录触发、writer 和引用，不是正文版本日志；编辑覆盖旧正文，删除清除正文。因此现有数据可恢复最终对象，不能保证恢复每次历史编辑的全文。

`local.rs` 保存 physical instructions/context、每轮输入、sessions 和 result。Pi RPC 包含高频增量及活动事件；原生 JSONL 才保留原生 entry、消息父子关系与压缩记录。Factory `core.archive_sessions` 已根据 header 和显式 session-tree 归档 Braid 根会话及 Pi 子代理；Braid 自身只拥有根 provider 的进程生命周期。完整诊断需要复用这条归档链，不能从父会话的 subagent 结果摘要猜孩子全文。

## 语义与所有权

本次“完整”指：源端实际留下的原生消息记录、Braid 实际交给 provider 的指令/上下文/轮次输入，以及最终 Issue、PR、评论、回复、隐藏/解决/删除状态、reaction、关系、指派和合并提交。保留原生结构和顺序，不声称拿到了模型内部隐藏推理、未记录的完整模型请求或删除前全部历史版本。

| 信号 | 内容与用途 |
| --- | --- |
| Traces | run、物理会话、Braid dispatch/turn、物化/替换、合并与结束的耗时和失败；跨异步任务显式关联。正文不堆在 span attribute 中。 |
| Logs | 结构化原生 entry、Braid 输入、对象快照、既有事件、会话关系、终态及诊断错误；承载重建所需数据。证据日志不随 trace 采样被丢弃。 |
| Metrics | 实际 run/turn 结果与耗时、活动会话、已知 token/usage、导出失败等计数。模型、provider、结果作为有限维度；会话/工作项 ID 留在日志和 trace。未报告 usage 的字段保持未知。 |

Braid 的业务状态仍由 SQLite 和原生证据决定，遥测是副本。只有 `braid local` 长生命周期进程持有运行 exporter；Agent 调用的短命对象 CLI 不各自初始化三个后台 exporter。Factory 继续只负责运行归属、归档和调用 Braid 的证据导出入口。Collector 不解释 Braid 数据。

完整证据直接写 SDK LogRecord body，避免 tracing bridge 同时把大正文变成 span event。普通运行诊断仍用 tracing；trace 只保留身份、操作、结果和引用。现有通用 `PayloadEvidence` 的 GitHub/credential 字段不沿用为新日志合同。

每条可重建记录带版本、Braid run_id、记录类型和稳定记录身份。会话另带 provider/native session id、parent id、Braid group/assignment/turn 与工作项身份，尚不确定的关联不猜测。外层实验 run 与内层 Braid run 是两个身份，不能互相覆盖；collector 的 run 归属来自既有凭据，绝不把凭据当关联字段导出。

原生记录按原生 entry id/parentId 与文件顺序恢复；同一文件的序号只描述该源文件，不按 collector 接收时间强排并发会话。工具调用与结果保留 tool call id。会话压缩、分支、模型与 reasoning 变化保持原样，展示消息列表时显式标明这些事件。

恢复重启另建 runtime attempt 身份，trace 描述该次实际执行；原生证据记录身份保持稳定。离线重放不再次累加生成次数、token 或工具执行次数，不为历史产物伪造实时 span。trace 缺少尾部不能反向推断 provider 成功或失败。

对象以一致 SQLite 读事务导出诊断快照，保留隐藏/解决正文和删除墓碑。保留已有事件以解释调度；快照之间的中间修改不承诺完整审计。暂不增加数据库审计表；若用户要求重建每一次编辑/删除前的版本，再把同事务持久化版本列为新增范围。

## 实际接线与失败合同

1. 整理现有 `telemetry.rs` 与 main/local 初始化。配置来自标准 OTEL exporter 环境变量，没有 endpoint 时维持本地诊断；接入现有 HTTP/protobuf，无压缩。三个 exporter 的 endpoint/header 优先级交给 SDK；不另写 HTTP/protobuf 编码器。配置错误与传输失败记录在本地，不能把生成成功改为失败。
2. 在 Braid 既有生命周期边界记录 spans 与计量。`tokio::spawn` 显式携带 context，避免跨 await 持有 entered guard。关闭路径先落业务结果和最终证据，再分别尝试 flush/shutdown 三个信号；一个信号失败不得阻止其余信号收尾。错误退出也先执行收尾，避免 `process::exit` 跳过它。强杀只能保留此前送达和已落盘部分，不能标为完整。
3. 运行期间分批读取已落盘的根会话原生记录及对象快照，复用已有 local 状态推进/会话结束边界，网络发送不放进数据库事务或 provider 读写锁。最终在原生进程收尾后补采尾部。尾部半行暂缓读取；文件被原生核心改写时标明新版本，不能把旧 byte offset 当永久身份。
4. 为 Braid 增加明确的离线证据导出入口，接受 state 和显式原生会话 manifest（准确文件路径、provider、native id、parent id 及归属）。Factory 在现有 `archive_sessions` 完成后将其 manifest 转为该输入，调用同一个 Braid exporter；由此补齐 Pi 内部子代理和原生最终文件，Braid 不内置 Factory 的 `.factory/session-tree.json` 路径或子代理进程管理。四个独立 variant 只显式调用共有证据 helper；不改变它们的原生配置和指令。
5. 重放采用相同记录身份，消费端去重；源端原有 state/native 文件是恢复依据，不增加常驻队列服务。用最终会话文件/对象快照的字节数、记录数与摘要清单判定接收完整性；仅 SDK enqueue/flush 成功不能证明源端所有记录均已到达。证据缺失标 partial/unknown，不升级为交付失败。
6. 以有界记录/批次导出正文。超过单记录预算的内容分片并带顺序与完整摘要，不能截断工具输出或图片内容冒充完整消息；实际 protobuf batch 必须低于 collector 的 16 MiB 限制。SDK 的按条数 batching 本身不提供该字节上限。
7. 增加 Braid 侧离线重建入口，读取 Factory 现有 `telemetry --export` 导出的 `.pb`，输出可读会话 JSONL、对象/关系 JSON、运行时间线及完整性摘要。使用官方 protobuf 类型解码；`prost`/`opentelemetry-proto` 已在现有 Cargo 依赖树，按需声明直接依赖，不自写 wire parser。缺终态清单、缺分片或缺关联明确列出。

保留原始错误、HTTP 状态与响应正文作为本地证据，再产生简报。当前 SDK 的 HTTP 状态正文只在 DEBUG 诊断事件中保留，且网络错误的上层消息会泛化；实施首先核对既有诊断事件能否充分保存底层原因，必要时使用 SDK 公开 HTTP client 包装接口。SDK 自身诊断只送本地 sink，不回送同一个 OTLP exporter，避免失败递归。不得枚举环境变量、导出授权 header 或 credential 字段；完整正文仍视作敏感运行材料。

## API 核对与实施顺序

已查本地 `opentelemetry-otlp-0.32.0` 实现：HTTP builder 已读取通用/信号专用 headers、endpoint、protocol、compression；显式 endpoint 会优先于环境配置。当前 Braid 手工拼 URL 应去除或收敛，避免覆盖标准配置。SDK 成功返回不是独立的完整性证明。协议语义参考 [官方 exporter 规范](https://opentelemetry.io/docs/specs/otel/protocol/exporter/)。

证据 manifest 的最小输入合同为 `schema_version`、`run_id` 和 `sessions[]`；每个 session 包含 `provider`、`native_session_id`、`path`，可选 `parent_native_session_id`、`braid_session_id`、`work_item_kind/id`。路径相对于显式 evidence root，源端核对原生 header；没有 header 的文件仍保留为未解析证据。Factory 只映射既有归档结果，不在归档失败时声明完整。首次实施时固定 CLI 参数和 JSON 类型并更新 Braid 权威文档。

日志 envelope 包含 `schema_version`、`event_kind`、`run_id`、稳定 `record_id`、源文件/entry 身份及序号、必要的会话关联和原始内容。重建输入不信任日志内的绝对路径或 `..`，输出文件名由消费端生成。建议将原始分片限制为 64 KiB，正文使用可逆编码，证据 batch 上限 64 条；按编码后大小核对上限，保留字节和换行以便完整摘要比较。最终清单给出选定源版本及其片段/记录范围，旧版本不能混入最终消息列表。此限额只服务现有 16 MiB 接收边界，不引入通用大文件存储。

开工后首先做实现前提交，边界只含本任务明确批准内容，不顺手提交 Factory 当前其他任务的大量变更。随后依次更新 Braid 运行合同、完成 SDK 接线及生命周期、完成证据导出与重建、接入 Factory 归档、核对实际运行及文档入口。保留原有 Rust SDK，不引入新遥测后端，不修改 collector 的存储职责。

预计源码边界为 Braid `main.rs`、`telemetry.rs`、`local.rs`、`cli/mod.rs`，以及实际生命周期所在的 `group/dispatch.rs`、`group/worker.rs`、provider 读写边界和必要的诊断对象读取；证据编码/重建若不能保持模块内聚，再从 telemetry 拆出专属模块。Factory 边界为 `scripts/braid_runtime.py` 的共有证据调用与四个 variant 的 `run.py` 收尾接线。`core.archive_sessions` 的现有归档结果优先原样复用，不重做子代理发现逻辑。若 API 核对发现需要改变调度、数据库审计模型或原生子代理生命周期，超出本方案，先重新复核。

未知前移：在首次实际历史产物导出时核对标准 SDK 的 HTTP 鉴权、批次尺寸、错误正文和 shutdown；用真实原生文件确认 entry 顺序、改写/压缩行为及子代理 manifest 转换。任何关键来源无法映射时先保留原文和 unknown，不为拼出完整结果编造身份。已有二进制的只读输出只支持现状调查，不当作新实现通过。

## 验收与授权边界

当前独立预演只读历史真实产物，检验信息是否存在、能否关联；没有模拟 runtime、伪造 provider 或发起模型调用。开工后不增加 Factory 自身测试套件或把测试改名为探针。

历史产物与当前数据库 schema 必须先核对。当前 CLI 无法读取的旧对象版本不在原目录迁移，也不为通过验收偷偷补字段；旧原生文件仍可用于会话重建核对，当前对象接口的验收改用版本匹配的真实产物。若缺少这种产物，明确保留该项未验收，待获授权真实运行取得证据，不把历史格式兼容扩展成此次默认范围。

独立预演已核对 15 个会话、106 对工具调用/结果，但有效样本没有子代理、原生 compaction 或分支。开工后的相应验收必须选到包含这些现象的既有真实产物；找不到则保留未验证，并在模型实验授权范围中明确覆盖。另已确认归档 manifest 的相对路径有效而所有 15 个旧绝对路径失效，Pi 路径型 session_id 与数据库 session UUID 也不能直接相等连接；转换必须经 provider_session_id/native_id 显式关联。

| 验收主张 | 判别性实际证据 |
| --- | --- |
| 三类信号进入指定 run | 实际 exporter 对现有 collector 的原始响应及保存批次，以官方 protobuf 类型解码；只看到 batch 数不算完成。 |
| 结束后可独立重建 | 对既有真实产物执行离线导出，再仅从 collector 导出的 protobuf 重建；逐源核对会话条目数/身份/字节摘要，对象正文与关系/墓碑一致。历史导出不得伪造实时 span 或实时耗时。 |
| 子代理未只剩摘要 | 与 Factory 原生 manifest 中 child header、parent id、文件数/摘要核对；原来缺失的 child 仍明确缺失。 |
| 来源边界被保留 | 压缩/分支/工具结果保持原始 entry 语义；隐藏/解决评论采用诊断完整视图，不经 Context 投影过滤。 |
| 传输异常可定位 | 对实际 collector 的失败响应保留状态/正文及本地诊断，运行终态不被遥测覆盖；分片/记录缺失在离线重建中可见。 |
| 实时链路与运行成本 | 需要另行授权一次真实模型运行，再以原生记录和 collector 批次核对异步关联、尾部导出及耗时。当前历史只读预演不能证明实时链路。 |

本次请求不自行启动新 benchmark。若用户同时批准真实实验，先在本 packet 固定选用 variant、题目和完成条件；正式成绩必须完成既定 benchmark，设施故障持续修复到评分后汇报，不自动开启下一轮。
