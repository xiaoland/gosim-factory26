# WSL 四条新 run 的过程证据（2026-09-28 03:10:54 UTC 截面）

本记录只读观察 `attempt-02`，不代表终态或评分。四个生成会话均已越过 runner 启动并有 Braid turn、原生 Pi assistant/tool 消息、模型响应和包内采集；`generation/active.json` 的 `running` 本身不是模型执行证据。证据根为 WSL `/home/yyh/Development/factory26/runs/e20260928-{01-flash-team,02-deepseek-direct}/attempt-02/generation/runs/`，每例详情在 `workspace/official-generation/template/.factory26/<id>/`。

| case | Braid turns（完成/失败/运行）| Pi 请求开始/assistant 响应结束 | 包内 OTLP logs/metrics/traces 批次 | Applied reset |
| --- | ---: | ---: | ---: | ---: |
| Flash Team GitHub `20260928-025803-8d9418d2` | 2/1/6 | 184/179 | 61/12/12 | 0 |
| Flash Team Sheet `20260928-025750-fb85c109` | 0/1/5 | 228/225 | 88/12/7 | 0 |
| DeepSeek Direct GitHub `20260928-030347-78b10c07` | 0/0/2 | 24/23 | 30/6/3 | 0 |
| DeepSeek Direct Sheet `20260928-025746-66feadac` | 5/2/6 | 253/248 | 95/12/15 | 0 |

计数来自各例 `braid-state/braid.sqlite3` 的 `turns`/`context_resets`、`pi-timing.jsonl` 的 `request_start`/`message_end` 和包内 `telemetry.sqlite` 的 `batches`；它们不是 token 数或工作完成量。请求开始与响应结束在运行中可能不相等，也可能包含失败/重试。四例 `receive_errors=0`，三类 OTLP 信号均持续入库；原生计时也含 response headers、first update、tool start/end 和 usage。外层实验 run 的空白 `telemetry.sqlite` 不应误作包内数据库。最初检查了 WSL 旧仓库路径，不能据此判断本实验缺 viewer。主 Agent 随后使用实验 code 快照实际生成 DeepSeek Sheet 新运行诊断页：`attempt-02/analysis/first-live-view/index.html`，144 批、6 会话、evidence_status=partial；本机副本 `runs/e20260928-02-live-observability/`。这验证了包内采集到宿主查询/页面的实际通路，不代表所有批次完整或终态归档已验收。

**需要接手的真实故障。** Flash GitHub、Flash Sheet 各有一个 `pi-minimax` 失败 turn。原生 Pi assistant error 明确是 HTTP 429 `rate limit exceeded(RPM) (1002)`，Braid 记 `Pi settled with Some("error")`；其余 turn 仍运行，不等于整 run 失败。DeepSeek Sheet 在 03:10:17–23 UTC 两次报 `cannot send user message through AgentSession`，具体为 `Agent is already processing. Specify streamingBehavior ('steer' or 'followUp') to queue the message.`；随后报 `session notification stream lost; handle is unavailable: channel lagged by 115`。该例此时已有两个 failed turns、40 条 wake 事件，应追踪对应消息是否重试、丢失或重复消费，不能把 wake 数直接算成模型调用或无效回环。

DeepSeek 两例 runner 的计量基线请求报 HTTP 401，但随后正常启动 Braid，并观察到模型 200 响应；这是计量覆盖缺口，不是已证实的模型拒绝。包内 `braid-state/telemetry-errors.jsonl` 中，四例分别有 2、2、1、6 次 OTLP capture `Timeout(5s)`（按上表顺序）；`receive_errors=0` 只说明 Collector 未记录接收拒绝，无法证明超时批次均已送达。缺失批次范围及其对最终重建的影响目前未知。DeepSeek Sheet 的 Pi subagents 还警告 vision 子代理 `extensions: []` 会禁用 ambient provider 扩展；原生计时已见 2 次 `factory26-visual` vision 响应，故这条警告当前不能直接判为全部 vision 调用失败。

**历史问题在新任务拆解中的早期对照。** 历史 [Sheet 因果记录](sheet-context-causality.md) 指向初始 `A1:C6` GIVEN 未传给共享基础及下游验收。新 Flash Sheet 的 `local_items issue:2` 已写 `Q3 Sales`、A1=`Region`、East/1200、North/800 和 Sheet2 类似数据，整合 `issue:6` 复述这个较窄的 seed；两者都未包含 `A1:C6`。新 DeepSeek Sheet 的共享基础 `issue:2` 只明确 Sheet1 A1=`Region`，其他子 Issue 同样没有 `A1:C6`。因此关键初始条件在两个 variant 的任务分解中仍未完整保留；尚不能判断实施、检查或最终结果。历史 [GitHub 因果记录](github-context-causality.md) 的错误发生于把明确的 `link` 判据改为 `menuitem`。新两例 GitHub REQ-2 Issue 都写了 `Your organizations` 入口，但未明确 `link` role；当前没有相应浏览器判据变更可供比较。

四例目前均无 `context_resets`，所以不能评价 reset 降幅；DeepSeek Sheet 的 40 条 wake 含实际任务消息和收件，应按事件→batch→turn→原生 user 输入链判别，不能按总数认定噪声。方法材料是否改善判据选择和覆盖声明，需等真实检查/整合决策出现后，将权威需求、检查依据、失败修正与最终声明逐项相连。本截面不能代替观察窗结束、完整设施验收或最终评分。

03:13:42 UTC 最新截面：四条 run 仍 running；Flash GitHub完成/失败/运行5/2/4，Flash Sheet1/1/4，DeepSeek GitHub0/0/2，DeepSeek Sheet6/2/5。全部工作项仍OPEN，没有最终验收或评分；失败turn数不等于整run失败。

诊断页的实际局限：本次first-live-view没有profile.json。viewer只在native/manifest.json已归档时接入token/耗时剖面，运行中已有pi-timing.jsonl也不会启用该页。因此当前能查看OTLP会话，但实时token/耗时尚未形成好用的入口；不能称新设施全链路通过。源码依据 lab/analysis/braid_telemetry_viewer.py 的 generation 候选选择。
监控接续：检查发现原委派没有留下持久在线脚本；主Agent已启动两个attempt-02/monitor-generation.py，PID143827/143831，采样遵守180/480秒，日志记录本目录。此处仅程序采集，不冒称存在后台语义审查。
