# Braid 运行诊断与排障

本手册用于读取已运行实验的 OTLP 数据、生成静态诊断网站和定位证据缺口。实验启动方式见[运行说明](index.md)，职责边界见[技术说明](../product-tdd/index.md)，实现时的实际验证与限制见[阶段报告](../../reports/2026-09-24-braid-otlp.md)。本页是当前操作入口，历史报告不替代操作步骤。

## 已具备的能力与数据来源

Braid 在配置 OTEL endpoint 时导出 traces、logs、metrics：trace 记录本次运行的生命周期与耗时，logs 承载普通诊断及完整原生文件/对象快照，metrics 记录操作结果和已知 Pi usage。运行期间每五秒采集已落盘根会话及对象，结束时收尾；Factory 完成原生归档后补采最终文件和内部子代理。没有 endpoint 时不启用 exporter 或补采进程。

当前接线使用 OTLP/HTTP protobuf、HTTP 端点及无压缩，读取标准 OTEL 通用配置和信号专用覆盖项。请求超时单位为毫秒，默认 10000；不把 Collector 能力推广为任意 gRPC、HTTPS 或压缩后端支持。

```text
Braid local ──三信号──→ 实验 Collector ──→ OTLP Backend（外层 run/telemetry.sqlite）
Factory 原生归档 ──braid telemetry export──↗                  │
                                                     查询固定批次列表
                                                            ↓
                                     Braid decode / reconstruct / render-markdown
                                                            ↓
                                              静态网站 + 原始批次 + 重建证据
```

网站从 Backend 查询数据，通过 resource 的 `service.name=braid` 和 `braid.run.id` 选择运行，不按 variant 名猜测，也不从本地 `braid-state` 或 `native` 文件补齐内容。外层实验 run ID 与内层 Braid run ID 分开显示。当前 Backend 是 `otlp_store` 管理的 SQLite，Collector 的 OTLP endpoint 是写入接口，不是网站查询 API；远端数据应在能访问该 Backend 的主机上生成网站，再取回整个目录。

页面包括 GitHub 式 Issue/PR 列表和讨论详情、聊天消息、工具调用与结果、trace 时间轴、指标序列、普通日志和完整性缺口。正文按 Markdown 渲染，原始 HTML 转义，图片只显示附件提示，原始 JSON 保留在折叠入口。隐藏/解决评论的现存正文和删除墓碑均保留；数据库没有保存的历史正文版本、完整 commit 历史、文件 diff、CI Checks 和未公开推理不补造。

## 常用操作

在仓库根目录执行。需要 Python 3 和本机可执行的配套 Braid；当前 UI 需要二进制支持 `decode`、`reconstruct`、`render-markdown`。`sources/braid` 是独立仓库，代码取得及跨机器交接见[开发说明](../../CONTRIBUTING.md)。

```sh
cargo build --locked --manifest-path sources/braid/Cargo.toml
make braid-report RUN=/path/to/experiment-run OUTPUT=/path/to/new-site
```

`RUN` 指含 `telemetry.sqlite` 的外层实验目录，不是应用目录或 `.factory26/<id>`。`OUTPUT` 必须尚不存在；打开 `OUTPUT/index.html`，也可将整个目录交给普通静态文件服务器。站点本身不需要 Python 服务、CDN 或联网。`make help` 列出常用入口，脚本 `--help` 列出全部参数。

直接脚本入口与 Make 入口等价：

```sh
python3 scripts/braid_telemetry_viewer.py /path/to/experiment-run \
  --output /path/to/new-site --braid /path/to/host-braid
```

同一实验含多个 Braid run 时，程序列出候选 ID，使用 `BRAID_RUN_ID=<内层ID>` 或脚本 `--braid-run-id` 选择，并换一个新输出目录。生成期间固定 Backend 的批次列表，不等待尚未收到的数据；运行结束后需要完整快照时再次生成新目录。不会启动模型、补发遥测或覆盖旧报告。

只想检查接收情况或导出 protobuf 时：

```sh
python3 scripts/local_experiment.py telemetry /path/to/experiment-run
python3 scripts/local_experiment.py telemetry /path/to/experiment-run --export /path/to/otlp
sources/braid/target/debug/braid telemetry decode --input /path/to/otlp > /path/to/decoded.json
sources/braid/target/debug/braid telemetry reconstruct \
  --input /path/to/otlp --output /path/to/new-evidence
```

`local_experiment telemetry` 可按 `--signal`、`--since`、`--until` 筛选；完整重建应导出全部批次，不能只取 traces，也不能将分片所在时段筛掉。`decode` 依赖文件名的 `-logs.pb`、`-traces.pb`、`-metrics.pb` 后缀区分 wire schema，不要随意改名。多运行重建使用 `reconstruct --run-id <内层ID>`。

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

源端问题需回到 Factory 生成目录：`telemetry-native.json` 是归档交接清单，`telemetry-export-status.json` 保存补采退出码/报告，`telemetry-export.log` 保存输出；`braid-state/telemetry-errors.jsonl` 保存 exporter 的具体网络错误、HTTP 状态与响应正文。这些本地传输错误不保证已进入 Backend，网站中没有错误日志不代表源端没有导出失败。

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
| 实验接收、run 隔离与批次查询 | `scripts/local_experiment.py`、`scripts/otlp_store.py` |
| Backend 查询、运行选择与生成网站 | `scripts/braid_telemetry_viewer.py` |
| GitHub 式讨论、聊天与三信号展示 | `scripts/braid_telemetry_viewer.html` |

当前已经以真实 Backend 数据核对原生字节、对象、重复导出和 HTTP 错误；构建及格式/语法检查也有记录。实时模型链路、子代理全文、原生 compaction/分支仍缺新的真实材料；浏览器视觉与交互验收受工具 URL 策略阻断，未宣称通过。后续实际验证和原始收据入口见[阶段报告](../../reports/2026-09-24-braid-otlp.md)。

修改展示优先用已归档真实 Backend 生成新目录并核对原始数据，不默认启动模型实验，不新增 Factory 测试、mock 或 smoke。改 Braid 需在其独立仓库构建并更新对应合同；旧包不会因宿主代码更新获得新 exporter 能力。

完整会话和工具输出可能含敏感运行内容，分享整个网站前检查原始批次与下载文件。单站数据当前嵌入 HTML，按会话分页仅限制 DOM 数量，整体容量仍受浏览器内存约束。源 manifest 元数据超过预算会报告 partial；诊断工具不能自行恢复已经丢失的源信息。
