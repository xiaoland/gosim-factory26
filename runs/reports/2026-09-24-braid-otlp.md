# Braid OTLP 接入与真实归档验收

2026-09-24 完成 Braid 三信号接线、Factory 归档补采和离线重建。用户已明确批准开工及本任务提交；没有启动新的模型或 benchmark。Braid 独立仓库实现提交为 `061f7f6`，Factory 前置方案与授权记录为 `b54258e`。源码接线需要重新构建、打包才进入新的运行，历史 ZIP 不变。

长期合同见 [Factory 运行说明](../../docs/deployment/index.md)、[技术说明](../../docs/product-tdd/index.md)及 Braid 的 `docs/20-product-tdd/local.md`、`docs/40-deployment/README.md`。临时任务包已收尾，前置设计和独立预演可从 `b54258e` 查看。

## 实现边界

Braid 使用已有 OpenTelemetry SDK，启用当前 collector 支持的 OTLP/HTTP protobuf、无压缩。运行期间每五秒采集已落盘根会话与对象，结束时收尾；普通运行诊断与完整证据分别使用有界日志队列。trace 描述本次 run、session、turn、创建/恢复、合并恢复与交付封存；metrics 记录操作结果、耗时和原生文件中已知的 Pi usage。

Factory 的四个独立 variant 已共用 `core.archive_sessions`，因此只在这一归档边界调用共有 `braid_runtime.export_telemetry`，没有为每个 variant 重复接线。补采使用准确的归档路径和 native identity，覆盖原生内部子代理；失败及超时单独记录，不更改应用终态。

重建从 collector 原始 protobuf 中取出证据，按稳定身份去重，并校验所选快照的片段、字节数和 SHA-256。输出完整原生文件、逐条原生 entry、最终对象与既有事件；缺失记录或来源缺口明确为 partial。原生压缩、分支、工具调用关系保留原始结构，不推测并发顺序。现有数据库没有保存的历史正文版本、模型内部推理和未记录请求不在恢复承诺内。

实际操作发现 SDK 0.32 拒绝显式 `OTEL_EXPORTER_OTLP_COMPRESSION=none`。入口在创建线程前重新执行自身，移除该值，维持无压缩语义；没有在 Tokio 中不安全地修改进程环境。传输错误保存 HTTP 状态、响应正文及网络原因，避免 SDK 上层摘要丢失诊断信息。

## 实际证据

原始样本为 `runs/integration/20260921-185322-pi-plain-2887cf`。仅复制已有 state/native，使用新二进制、现有真实 collector 和实际 Factory 归档补采函数执行；没有生成模型响应、改写源数据库或构造替代 runtime。原始操作与收据保存在 [archive-roundtrip-final](../braid-otlp/archive-roundtrip-final)。

| 核对项 | 实际结果与证据 |
| --- | --- |
| 三信号接收 | 首次导出 logs 2 批、traces 1 批、metrics 1 批；最大 protobuf 批次 724462 字节，低于 16 MiB。见 `receipt.json`、`otlp/`。 |
| 原生会话 | 9 个源会话全部重建，逐文件 SHA-256 相等；样本包含 141 条消息、68 对工具调用/结果。见 `receipt.json`、`reconstructed/`。 |
| 最终对象 | 2 个 Issue/PR 对象、6 条评论、1 条 reaction、1 条关联、1 条合并及 10 个 turn 与源 SQLite 逐行一致；源数据库摘要未变。见 `source-comparison.json`。 |
| 重放去重 | 同一归档再次导出，合并两次批次后仍为 9 个会话。见 `failure-and-replay.json`、`reconstructed-repeat/`。 |
| trace/metric 语义 | 用官方 protobuf 类型解码，两次导出各有一个成功结束的 export span、操作计数 1、活动值归零和实际耗时；没有伪造历史模型运行 span/token。见 `signals.json`。 |
| 真实错误响应 | 对实际 collector 使用未注册 token，导出非零退出，分别保存 logs/traces/metrics 的 403 和 `unknown run token`；未将有效鉴权 token 写入本地错误。见 `failure-and-replay.json`、`braid-state/telemetry-errors.jsonl`。 |
| 编译与局部校验 | `cargo build --locked`、`cargo fmt --all -- --check` 通过；Braid 分片缺失/损坏边界检查通过。未增加或运行 Factory 自身测试。 |
| Clippy | 当前与原始 HEAD 均有 43 个既存错误，按文件和诊断内容比对一致；不宣称全库 lint 通过。见 [verification](../braid-otlp/verification)。 |

旧 manifest 未提供完整性状态，因此本样本重建为 partial，缺口为 `Factory native diagnostic_status=unknown`。成功传输和字节一致证明已知材料的往返，不证明历史子代理清单完整。

## 尚未取得的运行证据

实时模型链路的异步关联、五秒采集成本及 provider 尾部收集没有新的真实模型运行证据。历史有效样本没有原生 compaction 或分支；另找到的两份父子清单共引用 8 个原生文件，但文件已不存在，无法进行子代理全文往返验收。这些边界保留未验证，后续若开展模型实验，应在该实验授权与矩阵中明确覆盖；本次不自动启动实验。

实现仍采用每轮读取源文件和单条有界 manifest。极大源清单或单文件片段引用超过 192 KiB 元数据预算时，会保留缺口并报告 partial；需要由真实大运行证明必要性后再分页元数据。Codex 未知 token 字段保持未知，不从工具事件推算。原始产物目录被 Git 忽略，证据不会随源码提交自动分发。

## 后续静态网站生成

用户随后要求制作静态可视化，并明确入口是包含 Braid 的实验 run，数据从 OTLP Backend 获取。已新增 `scripts/braid_telemetry_viewer.py` 与原生 HTML/JS 模板，通过 `otlp_store.list_batches/read_batch` 查询当前 run 的 Backend，再调用 Braid decode/reconstruct。Braid 解码接口提交为 `d5c963f`，使用官方 protobuf 的 serde 支持，保留三信号全部字段。运行方法见[运行说明](../../docs/deployment/index.md)。

静态页面通过 resource 识别 Braid 身份，展示全文会话、工具调用定位、Issue/PR/评论/关系、trace 时间轴、按资源与属性区分的指标以及普通日志和证据缺口。不把本地 state/native 当作替代数据源，不跨 runtime 累加累计指标，不把离线 export span 展示成模型执行。源文字按文本渲染；嵌入 JSON 转义 HTML 结束标签，超出 JavaScript 安全整数范围的值以精确字符串呈现，原始文件另供下载。

真实操作产物位于 [braid-otlp-viewer](../braid-otlp-viewer)，网站入口为 [site/index.html](../braid-otlp-viewer/site/index.html)。8 个 Backend 批次全部字节一致，重建材料摘要与此前往返结果一致；站点包含 9 个会话、168 条原生 entry、2 个 Issue/PR、6 条评论、2 个 span、6 条 metric 记录，证据状态仍为 partial。另读取一个真实 raw Codex 实验的 Backend，正确报告没有 Braid resource，退出码为 1，没有生成空站点。

`cargo build --locked`、格式检查、Braid 的纳秒精度/trace 身份/损坏批次边界检查和既有分片检查通过；Python 与 JavaScript 语法检查通过。Clippy 仍为前述 43 项既存问题。没有新增或运行 Factory 自身测试，也没有启动模型实验。

浏览器交互与视觉验收未完成：浏览器工具的自动安全审查以 URL 策略拒绝打开本地 file:// 页面，禁止通过其他浏览器通道或服务绕过；因此没有以改地址、HTTP 服务或替代浏览器继续打开。交互仍需在允许访问该产物的环境核实，不能将语法和数据核对当成浏览器验收通过。站点与原始收据均已保留。

## 讨论与聊天呈现改版

用户进一步要求接近 GitHub 的 Issue/PR UI 和 chatbot 消息列表。讨论页已改为列表进入详情，提供状态胶囊、Markdown 描述/评论、回复定位、reaction、成员与关联侧栏，以及已记录的合并提交。PR 分页布局参考 [GitHub 官方说明](https://docs.github.com/en/pull-requests/reference/pull-requests)；未采集的完整 commit 历史、Checks 和 Files changed 显式说明缺口，不伪造检查结果或 diff。

会话按用户与助手区分头像和正文区域，思考折叠，工具参数/输出独立呈现，原生会话、模型与压缩记录作为事件分隔；原始 JSON 退到折叠诊断入口。Markdown 复用已有 Comrak，通过 Braid `render-markdown` 批量渲染，原始 HTML 转义，危险链接拒绝，图片替换为附件提示。Braid 支持提交为 `8921293`，没有引入新 Markdown 库。

新版产物为 [github-chat/index.html](../braid-otlp-viewer/github-chat/index.html)，收据为 `runs/braid-otlp-viewer/github-chat-receipt.json`。重新从真实 Backend 生成的 9 个会话、168 条原生 entry、2 个对象和 6 条评论与上一版完全一致，146 段正文完成 Markdown 转换。构建、语法检查及 Braid Markdown 格式/HTML/危险链接边界检查通过；Clippy 仍为 43 项既存问题，没有新增或运行 Factory 测试。前述浏览器 URL 策略限制仍然存在，本轮未声称已通过视觉或交互验收，也未运行新模型实验。
