# Braid 运行诊断与排障

本手册用于读取已运行实验的 OTLP 数据、生成静态诊断网站和定位证据缺口。实验启动方式见[运行说明](index.md)，职责边界见[技术说明](../product-tdd/index.md)，实现时的实际验证与限制见[阶段报告](../../reports/2026-09-24-braid-otlp.md)。本页是当前操作入口，历史报告不替代操作步骤。

## 已具备的能力与数据来源

Braid 在配置 OTEL endpoint 时导出 traces、logs、metrics：trace 记录本次运行的生命周期与耗时，logs 承载普通诊断及完整原生文件/对象快照，metrics 记录操作结果和已知 Pi usage。运行期间每五秒采集已落盘根会话及对象，结束时收尾；Factory 完成原生归档后补采最终文件和内部子代理。`pi-braid` 与 `pi-braid-flash-team` 的新包会在生成容器内启动独立接收器，把三信号写入生成目录 `.factory26/<run>/telemetry.sqlite`；接收器持续到最终补采结束后关闭。其端口由系统分配在容器 loopback，不占用应用评测的 3000 端口。若接收器启动失败，`run.json` 的 `telemetry_diagnostic_error` 和 `telemetry-collector.log` 保留原因，生成仍继续。

含请求计时修正的 Collector 每处理一个 POST，会向同目录 `telemetry-collector.log` 写一条 `event=otlp_request_timing` JSON。`started_at`/`finished_at` 是 Unix 时间戳（秒）；`read_ms`、`decode_ms`、`persist_ms`、`response_write_ms`、`total_ms` 是本机 monotonic 耗时（毫秒）。未进入的阶段为 `null`，失败请求保留已走阶段、`failure_stage` 和 HTTP 状态；成功提交的批次带 `batch_id`。`persist_ms` 包含 SHA-256、入库与 commit，`response_write_ms` 只代表本地写出，不证明客户端已收到回执。记录仅包含 signal、collector session、字节数和上述时间/状态，不包含 token、headers 或 payload；历史包及实施前运行没有这些记录。

当前接线使用 OTLP/HTTP protobuf、HTTP 端点及无压缩，读取标准 OTEL 通用配置和信号专用覆盖项。请求超时单位为毫秒，默认 10000；不把 Collector 能力推广为任意 gRPC、HTTPS 或压缩后端支持。

```text
新包：Braid local / 最终补采 ──三信号──→ 包内 Collector ──→ .factory26/<run>/telemetry.sqlite
旧版及其他 Harness ──三信号──→ 实验 Collector ──→ 外层 run/telemetry.sqlite
                                                       ↓ 固定批次列表
                                    Braid decode / reconstruct / render-markdown
                                                       ↓
                                           静态网站 + 原始批次 + 重建证据
新包：Pi JSONL + pi-timing.jsonl ──→ Token 与耗时剖面 ──↗
```

网站从 Backend 查询 Braid 数据，通过 resource 的 `service.name=braid` 和 `braid.run.id` 选择运行，不按 variant 名猜测。Token 与耗时视图另读同一生成目录的原生 Pi JSONL 与 `pi-timing.jsonl`：运行中用 `braid-state/sessions.json` 定位根会话和 Pi 回调中声明的子会话，收尾后优先用 `native/manifest.json`。`profile.json` 标明 `live-unarchived` 或归档状态、未结束请求、已知 usage 字段数和缺口；它不依赖 ARC traceability。外层实验 run ID 与内层 Braid run ID 分开显示。Collector 的 OTLP endpoint 是写入接口，不是网站查询 API；远端数据应在能访问生成目录的主机上生成网站，再取回整个目录。

页面包括 GitHub 式 Issue/PR 列表和讨论详情、聊天消息、工具调用与结果、trace 时间轴、指标序列、普通日志和完整性缺口。正文按 Markdown 渲染，原始 HTML 转义，图片只显示附件提示，原始 JSON 保留在折叠入口。隐藏/解决评论的现存正文和删除墓碑均保留；数据库没有保存的历史正文版本、完整 commit 历史、文件 diff、CI Checks 和未公开推理不补造。

## 常用操作

在仓库根目录执行。需要 Python 3 和本机可执行的配套 Braid；当前 UI 需要二进制支持 `decode`、`reconstruct`、`render-markdown`。`sources/braid` 是独立仓库，代码取得及跨机器交接见[开发说明](../../CONTRIBUTING.md)。

```sh
cargo build --locked --manifest-path sources/braid/Cargo.toml
make braid-report RUN=/path/to/experiment-run OUTPUT=/path/to/new-site
```

`RUN` 指含 `telemetry.sqlite` 的目录，可以是外层实验 run，也可以是新包生成的 `.factory26/<id>`。`OUTPUT` 必须尚不存在；打开 `OUTPUT/index.html`，也可将整个目录交给普通静态文件服务器。`OUTPUT/analysis.json` 保存源 run、批次截止点及解释器身份；把输出放在对应实验的 `analysis/<新名称>/` 下，`lab show <run>` 可列出它。站点本身不需要 Python 服务、CDN 或联网。`make help` 列出常用入口，脚本 `--help` 列出全部参数。

直接脚本入口与 Make 入口等价：

```sh
python3 -m lab.analysis.braid_telemetry_viewer /path/to/experiment-run \
  --output /path/to/new-site --braid /path/to/host-braid
```

同一实验含多个 Braid run 时，程序列出候选 ID，使用 `BRAID_RUN_ID=<内层ID>` 或脚本 `--braid-run-id` 选择，并换一个新输出目录。生成期间固定 Backend 的批次列表，不等待尚未收到的数据；运行结束后需要完整快照时再次生成新目录。不会启动模型、补发遥测或覆盖旧报告。

只想检查接收情况或导出 protobuf 时：

```sh
python3 -m lab telemetry /path/to/experiment-run
python3 -m lab telemetry /path/to/experiment-run --export /path/to/otlp
python3 -m lab.analysis.native_profile /path/to/generation/.factory26/<run> \
  --output /path/to/new-profile.json
sources/braid/target/debug/braid telemetry decode --input /path/to/otlp > /path/to/decoded.json
sources/braid/target/debug/braid telemetry reconstruct \
  --input /path/to/otlp --output /path/to/new-evidence
```

`lab telemetry` 可按 `--signal`、`--since`、`--until`、批次 ID 范围筛选；完整重建应导出全部批次，不能只取 traces，也不能将分片所在时段筛掉。`decode` 依赖文件名的 `-logs.pb`、`-traces.pb`、`-metrics.pb` 后缀区分 wire schema，不要随意改名。多运行重建使用 `reconstruct --run-id <内层ID>`。

`native_profile` 的 token 数来自 Pi assistant 消息的 `usage`，按原生消息 ID 去重；按实际 model/provider、根成员与 Pi 子会话、成功与错误消息分组。每个字段同时显示已知消息数，缺失字段保持未知。Pi 回调只记录请求、响应头、首个实际流增量、最终消息和工具起止的时间及身份，不保存 prompt、响应正文或工具参数。请求到首增量是客户端可见延迟，不能称为服务端推理时间；未结束请求的用量与耗时未知，未结束工具耗时未知。模型调用、工具和并行任务的累计时长不能相加当总墙钟。旧归档没有这些新回调时间，剖面会明确标记 `timing_events=absent`。Pi 的 input 与 cacheRead 是分别报告的字段；cacheRead 为 0 不能证明供应商没有缓存命中，Pi 的 cost=0 也不是账单，当前剖面不估算费用或性价比。

WSL Runner 的外层 Collector 仍为其他 Harness 提供接收。上述两个 variant 使用包内 Collector，因而外层 `telemetry.sqlite` 可以为空；`lab telemetry`、外层 run 终态统计与 viewer 会优先定位工作区归档中的包内数据库，并显示所用路径。官网旧运行的工作区已有取回记录；**新自包含包**的 `telemetry.sqlite` 随官网工作区取回尚未由真实新运行核对。当前没有验证官网公网实时接收，也没有为它配置外部端点。

## 从哪些文件开始排障

网站生成目录保留读取截止点和中间结果。生成失败也可能留下该目录，不自动删除现场；修复后另选新目录。

| 位置 | 回答的问题 |
| --- | --- |
| `batches.json`、`otlp/` | Backend 实际返回哪些批次，信号、接收时间、字节数和摘要是什么？原始批次保留本实验全部服务。 |
| `decoded.json`、`decoded.stderr.log` | 官方类型解码是否成功？查看 `errors`，以及 resource 中的服务和 Braid 身份。 |
| `reconstruction.json`、`reconstruction.stderr.log` | 选中了哪个快照？有没有缺分片、源文件、会话关联或终态清单？ |
| `evidence/manifest.json` | 哪些 artifact 已通过字节/摘要校验，来源与输出文件如何对应？ |
| `evidence/messages.jsonl`、`native-*.jsonl`、`objects.json` | 逐条原生记录、完整原生文件和最终对象内容是什么？其他输入文件通过 manifest 映射定位。 |
| `markdown.stderr.log` | 二进制是否支持渲染接口，Markdown 批量渲染是否失败？ |
| `index.html` | 可读快照；不是实时监控，也不代替上述原始证据。 |
| `profile.json` | 运行中或归档 Pi usage、实际模型/会话时间、运行墙钟与活动区间并集；字段缺失和未闭合区间可查。 |
| `source-errors/` | 从本次生成目录复制的原始 `braid-state/telemetry-errors.jsonl`、`braid.log` 和 runner stderr；页面错误摘要链接到原文件并标明行号。 |

源端问题需回到 Factory 生成目录：`telemetry-native.json` 是归档交接清单，`telemetry-export-status.json` 保存补采退出码/报告，`telemetry-export.log` 保存输出；`braid-state/telemetry-errors.jsonl` 保存 exporter 的具体网络错误、HTTP 状态与响应正文。网站只展示当前已识别生成目录里的源端错误，原始文件也保留在生成目录。OTLP capture 超时是否丢失某些批次无法仅凭已收到的批次或 `receive_errors=0` 判断；网站仍可生成，但这不证明源端完整。

| 症状 | 定位与下一步 |
| --- | --- |
| Backend 不存在 | 检查是否误选 `.factory26` 内层目录，以及是否在 Backend 所在主机；不要新建空 SQLite 代替遗失数据。 |
| 没有 Braid resource | 查看批次数与 `decoded.json`：可能是 raw run、旧版 Braid 没有上报、解码失败或源端传输失败。variant 名不能证明包含 Braid。 |
| 二进制不存在、无法执行或不认识子命令 | 构建当前宿主的 Braid，或用 `BRAID` / `--braid` 指定；Linux 打包二进制不能直接作为 macOS 诊断工具。 |
| 多个 Braid run | 根据候选 resource ID 明确选择；不要把外层实验 ID 当作内层 ID。 |
| 网站生成成功但显示 partial | 逐项读 manifest 的 `gaps`；旧归档缺少完整性声明也会 partial。成功传输、退出码 0 和页面可打开均不等于源材料完整。 |
| 缺分片或摘要不一致 | 先确认没有按信号/时间丢掉 logs，再检查传输失败。若源文件仍在，可在有效接收上下文中补采；不要删除缺口强制 complete。 |
| 只有 export span / metric | 这是离线导出的实际操作，不是历史模型运行。实时 span、耗时和 token 不能通过补采历史文件补造。 |
| 没有某类 token、diff、Checks | 当前来源没有报告，保持未知；不能把缺失当作 0 或通过。累计指标按 resource/实例区分，不能跨实例简单求和。 |
| HTTP 403 / 超时 | 查看源端 `telemetry-errors.jsonl` 的原始状态/正文；403 可表示 run token 未注册，超时需核对 collector 生命周期和容器到宿主地址。不要将凭据写入命令或页面。 |
| 输出目录已存在 | 保留原始失败现场或旧网站，换一个新目录；脚本不会覆盖它。 |
| 浏览器禁止本地页面或页面资源不全 | 确认交接了完整网站目录并使用环境允许的静态访问方式；遇到安全策略拒绝不能通过替代通道绕过，数据/语法核对也不能代替浏览器验收。 |

## 补采与失败语义

只有保留了原始 state/native，且拥有正确 run 的有效 Collector endpoint/鉴权环境时，才可重新导出：

```sh
braid telemetry export --state /absolute/generation/braid-state \
  --native-manifest /absolute/generation/telemetry-native.json
```

命令继承标准 `OTEL_EXPORTER_OTLP_*` 环境变量，不在参数中传凭据。实验结束后的旧临时 endpoint 或 token 可能已经无效；此命令不会重启 Collector、注册 token 或自动绑定另一个实验。必须先通过实验设施取得合法接收上下文。省略 manifest 只能采集 Braid 拥有的根会话，无法证明内部子代理完整。

Factory 自动补采最多等待 120 秒，错误单独记录，不覆盖应用交付终态。Braid 导出错误也不改变业务结果；重建按稳定记录身份去重，补采不重复累加历史生成用量。业务 `completed/incomplete/failed`、证据 `complete/partial`、实验评分属于不同维度。

## 后续修改与验证边界

| 要修改的行为 | 代码入口 |
| --- | --- |
| 三信号配置、HTTP 原始错误、flush/shutdown 与计量 | `sources/braid/src/telemetry.rs` |
| 原生/对象快照、分片、摘要、重建、protobuf 解码与 Markdown | `sources/braid/src/evidence.rs`、`src/cli/mod.rs` |
| run/session/turn 生命周期埋点 | `sources/braid/src/local.rs`、`src/group/`、`src/provider/` |
| Factory 归档结束后的补采和错误留存 | `scripts/core.py`、`scripts/braid_runtime.py` |
| 实验接收、run 隔离与批次查询 | `lab/run.py`、`lab/otlp.py` |
| Backend 查询、运行选择与生成网站 | `lab/analysis/braid_telemetry_viewer.py` |
| GitHub 式讨论、聊天与三信号展示 | `lab/analysis/braid_telemetry_viewer.html` |

当前已经以真实 Backend 数据核对原生字节、对象、重复导出和 HTTP 错误；构建及格式/语法检查也有记录。实时模型链路、子代理全文、原生 compaction/分支仍缺新的真实材料；浏览器视觉与交互验收受工具 URL 策略阻断，未宣称通过。后续实际验证和原始收据入口见[阶段报告](../../reports/2026-09-24-braid-otlp.md)。

修改展示优先用已归档真实 Backend 生成新目录并核对原始数据，不默认启动模型实验，不新增 Factory 测试、mock 或 smoke。改 Braid 需在其独立仓库构建并更新对应合同；旧包不会因宿主代码更新获得新 exporter 能力。

完整会话和工具输出可能含敏感运行内容，分享整个网站前检查原始批次与下载文件。单站数据当前嵌入 HTML，按会话分页仅限制 DOM 数量，整体容量仍受浏览器内存约束。源 manifest 元数据超过预算会报告 partial；诊断工具不能自行恢复已经丢失的源信息。

## 热恢复后的原生用量

恢复期间 `native/manifest.json` 可能是来源运行的 partial 归档。
查询会将它与当前 Braid 会话和原生 JSONL 合并；只有 complete 终态归档独占来源。
新恢复入口在开始执行前移走旧归档，避免旧材料遮住新活动。

`python3 -m lab.analysis.native_profile <.factory26/run目录> --since 2026-09-28T04:49:39Z --output /tmp/profile-window.json` 只观察指定时间之后。
用量按响应时间，耗时按操作开始时间；跨边界操作排除数另列，不把旧运行耗时算入新窗口。
模型汇总的 Braid 成员数、原生主会话数、Pi 子会话数分别列出；Context reset 后同一成员会有多个原生主会话。
供应商 usage 与账单不同，错误请求的零用量不证明免费。

本地生成的 `arc_bench_adapter.py --memory 4g --cpus 2` 将资源参数原样传给官方 local runner；未指定时沿用 runner 默认值。
记录资源配额与 cgroup 压力后再比较耗时，不把不同资源条件下的变化单独归功于模型或 Harness。

## 原生子任务与浏览器临时目录

Pi/Braid variant为浏览器和一般临时文件使用容器内短路径`/tmp/f26-*`，避免Chromium的Unix socket路径超限。
`PI_SUBAGENTS_TEMP_ROOT`单独指向保留工作区的`work/tmp/pi-subagents-uid-<uid>`；新运行和半成品恢复采用相同映射，因此缩短TMPDIR不迁移旧子任务的状态/产物索引。
该临时根随容器结束清理，子任务目录继续作为恢复材料保留。

`subagent_wait`不能等待PBB的`bg*`命令；原生空结果仍保留，现有扩展在误用处追加正确入口。
后台完成通知可能排在当前响应之后；有独立工作可继续，仅剩等待时结束当前响应，由完成消息唤醒，不再创建sleep轮询命令。

### 原生子任务观察索引与恢复

同一原生父会话恢复时，observer先加载其已有session-tree清单，再合并后续事件。同一native-home可以创建不同的父会话；切换时有子任务的旧清单按父身份保留在`.factory/session-trees/`，新父按同工作区查找旧任务及持久产物入口，旧任务不改挂到新父。旧任务完成消息在当前原生父进程存活期间记录到Pi上下文，但不独立启动模型回应；后续合法输入可以消费该结果，父再次恢复时也会重新读取状态和结果。这个观察功能不自动接管旧任务、不保证关闭进程后仍能唤醒，也不使历史任务阻止当前工作结束；执行责任和等待由原生工具及Agent决定，Braid不管理内部子任务。

归档每个已登记的父会话时，原文定位和子任务遍历使用同一父身份选择规则：优先匹配活动清单，否则读取对应历史清单。清单与原生 header 的父子身份仍须一致；没有匹配材料时保留诊断缺口，不把当前父的记录归到旧父，也不以归档不完整判定应用交付失败。
