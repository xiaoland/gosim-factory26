# 本地构建与运行

使用 Rust 1.93+、Cargo 和系统 Git。`cargo build --release` 生成 target/release/braid；`cargo fmt --check` 和 `cargo check --bin braid` 检查源码。本地入口只需要显式 Codex/Pi/Bub adapter 配置和已有初始 HEAD 的隔离 Git 仓库，不需要 GitHub App、remote、secret、webhook、tunnel 或公网服务。

运行 `braid local request.json`。请求和输出字段见 [本地运行契约](../20-product-tdd/local.md)。调用者把同一 braid 二进制放入两个核心的 PATH；每次 dispatch 也提供当前可执行文件、state 和 writer turn 的命令前缀。SVC 通过调用者的原生 user scope 独立配置，Braid 不调用 SVC。

state/braid.sqlite3 是唯一对象权威，迁移保持不可变；同一 state 只有一个持有独占锁的 runtime。恢复必须使用相同请求身份。result.json 的 completed 加固定 delivery commit 才允许 Factory 导出应用；incomplete/failed 的对象、worktree、物理输入和原生会话都应归档。

sessions.json 持续列出所有实际建立的物理 session。Pi 的原生文件分布于各自 worktree 下，不能只搜索初始 source；Codex 使用准确 thread ID 寻找并核验 rollout。历史被替换/Unknown 的会话参与计量，但不单独决定整体生成是否成功。

日志写 stderr。真实 native 核心与官方 bench 由 Factory26 运行及保存证据；源码或文档变更后应刷新实际构建来源，不能把旧二进制当本次实现。

## OTLP 与离线重建

`braid local` 在配置 OTEL endpoint 时启用 traces、logs、metrics；未配置时仅写 stderr。
当前构建使用与 Factory collector 相同的 OTLP/HTTP protobuf、无压缩、HTTP 端点，读取标准
`OTEL_EXPORTER_OTLP_ENDPOINT`、`OTEL_EXPORTER_OTLP_HEADERS` 及各信号专用覆盖项。
当前 SDK 不接受显式 compression=none，入口在创建线程前以相同 argv 重新执行自身并移除该值，保持无压缩语义；不在运行中修改进程全局环境。
请求超时读取对应 `OTEL_EXPORTER_OTLP_*_TIMEOUT`，单位毫秒，默认 10000。
凭据仅作 HTTP header，不进入证据清单。正文是敏感运行材料，分享前需检查。

运行期间每三十秒采集已落盘材料的内容身份、字节数、覆盖状态和 usage 摘要，结束信号立即触发补采。
摘要按内容身份去重，不把对象快照、Braid 输入或增长中的原生文件正文写入 OTLP。
证据 flush 失败保留待提交记录数、耗时及 capture 阶段，超时仍表示完整性未知。
trace 记录 run、session、turn、创建/恢复、合并恢复与交付封存，metrics 记录操作结果、耗时、源材料规模和原生文件中已知的 Pi usage。
usage 是已观测累计值的 gauge，按 provider/model/token 类型区分，未报告的字段保持未知，不代表账单。
运行强杀、缺少源文件或子代理清单时，只能恢复部分现场。

Factory 在原生归档结束后通过显式 manifest 补采内部子代理；其他宿主也可调用同一命令：

```sh
braid --state /absolute/state telemetry export --native-manifest /absolute/evidence/native-manifest.json
braid --state /absolute/state telemetry export --native-manifest /absolute/evidence/native-manifest.json --portable
braid telemetry reconstruct --input /absolute/exported-otlp --output /absolute/new-diagnostic-directory
braid telemetry decode --input /absolute/exported-otlp > decoded.json
```

export 只读取已有对象和原生材料，不运行 Agent；其 trace/metrics 描述本次导出操作，不伪造历史执行或重复累加生成用量。默认只导出有界摘要，供已在本地归档原件的普通运行使用。只有 `--portable` 才把完整对象、输入与原生会话分片写入 logs，供没有其它原件的跨边界离线重建；portable OTLP 本身应作为原件保存，不再重复长期保留同一 native 副本。
manifest 包含 `schema_version: 1`、`run_id`、`sessions` 和 `gaps`；每条 session 含 `provider`、`native_session_id`、相对于 manifest 目录的 `path`，可带 `parent_native_session_id`、`provider_session_id`、group/profile 和工作项身份。
无法确认的 native identity 可为 null，但会保留原文并标记缺口。文件必须在 manifest 所属目录内。
省略 manifest 只能采集 Braid 拥有的根会话，不能证明原生子代理清单完整。

reconstruct 读取 portable export 的 collector `.pb`；仅有默认摘要时不能重建原文。输入含多个 Braid run 时要求 `--run-id`。
输出目录必须尚不存在。`manifest.json` 保存源文件映射、摘要和缺口；`messages.jsonl` 保留每个原生 entry 及会话关系，`native-*.jsonl` 保持原始字节，`objects.json` 保存完整对象表，`timeline-*.jsonl` 保存既有事件。
源路径只用于描述，不决定输出文件位置。未知/缺失片段、没有终态清单及源端 gaps 均使重建结果为 partial；命令正常退出只证明操作完成，须查看摘要的 status。

导出故障写入 state/telemetry-errors.jsonl，保留具体网络错误、HTTP 状态及响应正文。
传输失败不更改业务结果；三个信号分别收尾，单个失败不阻止其余信号。
保留的 state 与原生归档可以再次 export，摘要和 portable 重建均按稳定记录身份去重。
Collector 保存批次、SDK flush 成功均不能单独证明完整，重建以最终源清单逐项核对字节与摘要。

`decode` 用官方 protobuf 类型输出三信号 JSON，保留 resource、scope、原始属性及纳秒时间字符串，供宿主静态诊断页面使用。
输入文件名必须分别以 `-traces.pb`、`-logs.pb`、`-metrics.pb` 结尾；三种 protobuf 不能仅凭 wire 内容可靠区分。
结果中的 `batches` 为成功解码批次，`errors` 保留逐文件失败原因；退出成功不等于所有批次解码成功。
Factory 的 `braid_telemetry_viewer.py` 从实验 OTLP Backend 查询批次，再调用 decode/reconstruct；页面不从本地 state 或原生归档补造 Backend 缺失内容。

`braid telemetry render-markdown` 从 stdin 接收 Markdown 字符串数组，向 stdout 返回等长 HTML 数组，供宿主诊断页面批量渲染正文。
它复用 Comrak 的表格、任务列表、删除线和自动链接支持，转义原生 HTML，使用默认的安全链接处理；调用方仍应限制远端资源加载。

## Bub 原生环境

安装 Python 3.12+，并在同一个隔离原生环境安装 Bub、bub-acp-server、bub-session-prompt 和 bub-mcp。核对来源与协议边界见 [Bub adapter](../20-product-tdd/app-server.md#bub-原生-acp-adapter)；本次读取和编译依据固定的 Bub/contrib commits，不以浮动 `@main` 声称可恢复兼容。官方安装入口是 `bub install bub-acp-server@main`，实际部署应锁定安装来源并保留依赖清单。Braid 不替用户修改全局安装或登录。

用该环境中的 `bub --help`、`bub acp --help` 和 `bub hooks` 确认 CLI 与插件，命令不调用模型。hooks 必须含 `system_prompt: ... session-prompt`，且 `provide_tape_store: builtin`；额外 tape store 插件本次不支持。Braid 会在同一环境重复核对该边界，失败保留具体输出。

local 请求为所有 Bub Profiles 设置 `adapter_type: "bub"`，并只提供 `bub` 配置。其字段为绝对 executable、native home 根 `home`、可选 `startup_timeout_seconds`（默认180）、api_key_environment 或 api_key_file。凭据文件沿既有 `provider_api_key` TOML 格式；不配置凭据字段时使用 Bub 自身原生配置与环境。bindings 仍以 Profile ID 提供 executable、native_template 和 native_home.root；每个物理会话从模板派生不同 home。native_template 可提供必要的 Bub 配置与认证，必须保留新 home 和默认 tapes 直到归档完成；不要在模板复制其它会话的 acp-sessions.json 或 braid-session.json。

Profile.model 可以使用完整 Bub model 名；provider 非空时须同时给 model，二者组成 `provider:model`。reasoning 采用 Bub 的 reasoning_effort 选项，真实模型是否支持该值另行验证。`braid local` 会启动模型工作；本次仅做了 no-model 协议材料反馈，并未授权借运行说明启动实验。

恢复必须使用相同 owned home、确切 ACP ID 和成员 clone cwd。完整归档包含 `acp-sessions.json`、`braid-session.json`、`sessions/acp-server:<ACP_ID>/AGENTS.md` 及准确 tape；只有 native tape 不能重建首次 prompt 前尚未执行的 Context。未完成的 prompt、活动断连与进程强停保留 Unknown，原始文件及具体错误交给宿主恢复。没有模型调用的 initialize/new/load 成功只证明这些接口与身份材料可读取。
