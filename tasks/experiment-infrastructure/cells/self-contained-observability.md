# 自包含遥测实施记录

状态：代码与归档查询已接通；新 Pi 回调事件和官网数据仍待获授权的真实运行验证。

2026-09-28。实施授权来自本轮用户指示：复用现有 OTLP/SQLite/viewer，给官网与 WSL 包内本地持久化，并补 Pi 原生 token 与耗时诊断；不新增 Factory 测试或模型实验。以下以当前源码和 Pi 0.85.1 类型定义为准。

## 已核实接口和数据路径

- `lab.otlp.receiver()` 已接受 OTLP/HTTP protobuf 三信号，按注册 token 把原始批次写入 SQLite；`list_batches/read_batch` 和既有 viewer 可以读同一格式。`receiver` 当前在退出时关闭 HTTP 服务；SQLite 使用 WAL，需要停机后 checkpoint 再归档单个数据库文件。
- `lab.run._environment()` 将 endpoint、protocol、token header 注入本地 Runner；官网 ZIP 没有独立接收器。`scripts/package_agent.assemble()` 复制 variant 和 support，构建在开发宿主执行，生成在 Linux 容器执行。
- 两个 Braid variant 的 `run.py` 在 `logged(braid local)` 后 `archive_sessions()`；后者调用 `scripts/braid_runtime.export_telemetry()`，此函数从 `os.environ` 读 OTEL 配置。包内接收器必须活到补采结束，且补采必须取得与 Braid 相同的 OTEL 环境。
- Pi 0.85.1 类型定义确认 `before_provider_request` 仅有 payload，`after_provider_response` 仅有 status/headers、在流消费前触发；`message_update` 带 assistantMessageEvent，`message_end.message` 是最终消息及 usage；`tool_execution_start/end` 带 toolCallId/toolName。原生 assistant JSONL 的 message ID 与 usage 是去重权威来源。请求到首增量仅是客户端可见延迟，不能当服务端推理时间；不完整回调保持开放状态。
- `factory-subagent-observer.ts` 已被根 Pi launcher 加载，记录 `.factory/session-tree.json`；内部 Pi 通过 `budgeted_pi` 产生的 `PI_SUBAGENT_PI_BINARY` 启动。新扩展应通过这一共同启动入口加载，避免根/子会话漏数或重复加载。

## 实施顺序与口径

1. 给现有 `lab/otlp.py` 增加单 run 进程入口，启动时写 `run/telemetry.sqlite` 并输出仅供父进程读取的 endpoint/token；退出时停接收并 checkpoint。打包现有 protobuf 依赖和同一接收器，不另写协议栈。只监听容器 loopback，不使用应用端口 3000。
2. 两个 variant 在生成阶段启动该进程并把 OTEL 配置传给 Braid、最终补采；退出时收束进程，记录接收状态及错误，保留 SQLite 于 `.factory26/<run>/`。准备模式不启动。包内接收器优先于外层 WSL Runner endpoint；宿主 `lab telemetry`、run 状态与 viewer 查找包内数据库，外层空数据库不冒充无数据。该路径在生成结束后读取同一个归档，不提供外层实时副本。
3. Pi 扩展只写无 prompt/response 内容的事件 JSONL：会话身份、请求/响应头/首增量/最终消息时间、模型与原生 usage、工具起止；原生 JSONL 仍作为 usage 核验来源。将事件文件随 `.factory26` 归档，缺失和未闭合区间明确标出。
4. 分析入口从归档原生消息按消息 ID 去重聚合模型/会话 token，再按事件关联工具和请求时间。展示独立时间与已知覆盖率，不相加重叠时长，不把平台官网账单估算成原生费用；在既有诊断页增加剖面，并保留机器可读 JSON。
5. 验证只用已有归档操作、CLI、编译/类型检查，不运行 Factory 测试、smoke/probe 或付费新实验。官网公网端点未知，实时链路状态保持未验证。

## 实际操作证据与边界

- 从历史生成归档 `runs/competition-budget/20260926/root-only/analysis/final/template/.factory26/20260926-070555-c315f6e9` 运行 `python3 -m lab.analysis.native_profile`，得到 6 个 Pi 会话、2 个模型，保留真实 `profile_id=pi-kimi-k3` 与 `work_item_id=1`。`run.json.generation_seconds` 给出约 2527853 ms 墙钟；该旧归档无回调事件，请求、工具、活动并集与费用均为 `null`，没有补造时间。机器可读结果见 `runs/e20260928-product-hardening/observability/native-profile.json`。
- 从已有 `runs/braid-otlp/archive-roundtrip-final` Backend 再生 viewer 成功：8 批、9 会话，证据状态 `partial`。网站及 CLI 输出见 `runs/e20260928-product-hardening/observability/site/`、`viewer-cli.json`、`telemetry-cli.json`。该历史数据没有对应新生成归档，Token 与耗时页明确标记缺失；不能把此结果当作新版本实时模型链路验证。
- 两个 variant 分别完成实际 Linux ZIP 构建，ZIP 均含 `support/otlp.py`、纯 Python protobuf 依赖、`extensions/factory-pi-timing.ts` 与 manifest。实际 staged 接收器模块可导入 traces/logs/metrics 三类 protobuf 请求类型。最终包核对见 `runs/e20260928-product-hardening/observability/package-receipt.json`；未复制两个各约 435 MB 的 ZIP。Python 编译、Node TS/页面脚本语法检查与 `git diff --check` 记录见 `checks.log`。
- 用已有 Backend 第 1 批 263774 字节真实 logs protobuf 通过独立接收器入口完成 HTTP 200 写入，正常 SIGTERM 停机后 WAL 为 0 字节；仅复制 `telemetry.sqlite` 到稳定归档，仍能读出相同字节与摘要。回执和可单文件读取数据库见 `runs/e20260928-product-hardening/observability/collector-receipt.json`、`standalone-telemetry.sqlite`。
- WSL 外层 Runner 的 Collector 在这两个包的新运行中可能为空；宿主 CLI、run 终态统计与 viewer 从归档选择内层 SQLite。尚无新真实 WSL 运行核对这个自动选择和 Pi 回调的端到端数据。官网旧运行已有工作区取回证据，但新自包含包的 SQLite 随官网工作区取回以及公网实时通路未由真实新运行证实；因此只承诺包内本地归档能力，不承诺实时远程可见。
