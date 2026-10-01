# Inquiry: 当前 analysis 为何不能承担 Coding Agent debugger / profiler

## Question / Decision Served

- Question：当前产品在哪一层把机械重建和关键 telemetry 丢给了调用 Agent？现有 bundle、
  provider 与 analysis 边界中，哪些应保留、删除或移动，才能低成本接入 Pi？
- Return needed by：`design.md` 的产品边界、数据 authority 与迁移选择。

## Boundary and Freshness

- In scope：当前仓库 v14 的 Product/Technical/Deployment truth，`svc_cli.analysis`、
  `svc_cli.telemetry`、相关测试；Codex、Claude Code、DeepSeek Harness、DimAgent 与 Pi Agent
  当前公开的 session/event/sub-agent/usage 合同。
- As of：2026-09-19，工作树基于当前 HEAD；Pi 官方仓库已从 `badlogic/pi-mono` 重定向到
  `earendil-works/pi`。
- Freshness condition：Codex rollout 或 Pi session wire format、当前 SVC public contract、
  或目标产品边界变化时重查。

## Evidence Versus Inference

| Evidence / observation | Inference or candidate mechanism | Confidence / missing evidence |
| --- | --- | --- |
| Product Truth 明确把 latency、token、memory、throughput 排除为独立 task-performance outcome，并称 analysis 是 query/read 的组合。 | 当前定位有意优化“终局质量证据导航”，而非 debugger/profiler；用户要求不是小补字段，而是产品重定位。Task-performance 可保留为调用方用例，但不再定义 analysis 产品边界。 | 高；新的 debugger/profiler 定位已被 Human 接受。 |
| `query` 只有 overview/match；descriptor 只暴露类型、角色、工具名、trajectory refs 和 native refs。`read` 只按 native 顺序返回原始帧。 | turn/branch、call/result、重试、状态转换、指标关联都必须由调用 Agent 重放，这是不合理的机械负担。 | 高。 |
| `Relationships` 已投影 turn/actor/lane/concurrency，tool call/result 也有 call id，但 query 不提供 join 或完整记录。 | 现有投影包含部分重建原料，却没有形成用户可消费的执行模型；复杂度已经支付，产品收益没有交付。 | 高。 |
| Codex `token_count` 存在于 `native.bin`，normalizer 的 `_known_ui_record` 明确跳过它；测试要求输入 token_count 后仍不产生记录。 | “不收集 token”更准确地说是“native 已采集，但 telemetry trajectory 主动丢弃”；profiling 缺口应由 Codex normalizer 映射为 usage observation。 | 高。 |
| Codex token_count 同时包含累计与 last usage，rate-limit-only 更新可能重复 last usage；compaction usage 可能另行记录。 | 指标必须保留 provider 语义、样本 identity 和 coverage，不能把每条 event 简单求和。 | 高；具体版本差异需冻结真实 corpus。 |
| schema-v3 authority 只有 `manifest.json`、`native.bin`、`native-index.jsonl`；`trajectory.jsonl` 是可重建缓存。 | Native-first 保真值得保留，但把 trajectory 降为 cache 使 analysis 没有稳定共同输入；trajectory 应升级为 required semantic material，native 改为复核与重新归一化依据。 | 高。 |
| export 当前仍主动构建并可能持久化 trajectory；analysis 在 cache 缺失时只调用默认 Codex provider 重建。 | 现状把 optional cache 与 analysis 侧 provider fallback 混在一起；新边界必须由 telemetry adapter 产出 required trajectory，analysis 不再运行 provider normalizer。 | 高。 |
| trajectory cache 只有 schema 名称，合法旧 cache 会直接复用；trajectory refs 是 ordinal `rNNN`，只绑定不随投影变化的 evidence_id。 | 新增 usage 或改变投影排序会让旧 cache 静默缺字段，并让旧 trajectory refs 指向不同语义。 | 高。 |
| provider registry 已是静态 allowlist，但 CLI/service 默认 Codex，公开参数叫 `--codex-home`，source help 也写死 Codex。 | 不需要动态 plugin system；需要显式 provider 选择和由 manifest 驱动的 decoder 选择。 | 高。 |
| Pi 当前 session 是 JSONL tree：header 后的 entry 以 `id/parentId` 组成分支；assistant、tool result、compaction、branch summary 都可能携带 usage。 | 线性 native 顺序不能代表当前/废弃 branch；usage 也不能假定只属于 assistant turn。通用分析模型必须允许 graph 与多种 usage sample owner。 | 高；实现前仍需真实 Pi fixtures。 |
| Codex session metadata 分开保存 `parent_thread_id` 与 `forked_from_id`；新 `token_usage_record` 带 thread/turn/root-turn/response identity 和单 response usage。 | spawn parent、fork origin 与 usage owner 不能压成一个 `parent_id`；新日志应优先按 response identity 去重，legacy token_count 只能作为较弱口径。 | 高；旧 Codex 版本仍需 fixtures。 |
| Pi core 没有内建 sub-agent；官方 subagent extension 以 `--no-session` 子进程运行，并把 child messages/usage 放入父 tool result details。Pi `parentSession` 用于 fork。 | “一个 agent execution = 一个 session/artifact”不成立；统一 execution 应允许未来映射 embedded child，但首版不解析该 extension。 | 高；第三方 Pi sub-agent extensions 可能采用另一种持久化。 |
| Claude Code 主 transcript 与 sub-agent transcript 分开保存；hook 暴露 main/subagent transcript path 和 agent ID。SDK result 的 `usage` 只含 main loop，而 `modelUsage` / `total_cost_usd` 包含 sub-agents。 | 统一 session ID 或统一 `usage {tokens,cost}` 都会丢失 scope；telemetry 应保留 transcripts 与各层原生 accounting facts。 | 高；本地 transcript 的非公开字段仍需 fixture 锁定。 |
| DeepSeek Harness 的 Session 是 append-only typed event log；LLM message history 从日志派生。事件保留 request header、失败 assistant attempt、exact compact stream、surface replacement 与 usage。其 telemetry 直接一对一镜像 canonical events。 | 若只保留 normalized transcript，会丢失 debugger 最关心的失败尝试、实际 request config 与上下文替换。Evidence core 必须允许 canonical event log 原样成为 material。 | 高；项目仍处 developer preview，source version 必须显式记录。 |
| DimAgent 官方公开合同确认 v2 使用 SQLite 保存 session/history、usage 与 tool logs，并提供 session JSON export、runtime JSONL stream 和 structured trace；稳定内部 schema 未公开。 | 最大公约数不能要求 JSONL、line number 或公开数据库表结构。DimAgent 在真实 fixture 前只能约束容器形状，不能证明 semantic mapping。 | 中高；需取得真实 export/trace 后再承诺 decoder。 |

外部核对：

- Pi [`SessionHeader`、`SessionEntryBase` 与 message/compaction/branch types](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/src/core/session-manager.ts)
- Pi [`Usage` 与 `AssistantMessage`](https://github.com/earendil-works/pi/blob/main/packages/ai/src/types.ts)
- Pi [官方 subagent extension](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/examples/extensions/subagent/index.ts)
- Codex [session parent/fork 与 usage 协议](https://github.com/openai/codex/blob/main/codex-rs/protocol/src/protocol.rs)
- Codex [response-scoped token usage state](https://github.com/openai/codex/blob/main/codex-rs/core/src/state/session.rs)
- Codex [重复 `last_token_usage` 的已知歧义](https://github.com/openai/codex/issues/14489)
- Codex [累计 usage 与 current-context/last usage 的区别](https://github.com/openai/codex/issues/22354)
- Claude Code [sub-agent transcripts 与 nesting](https://code.claude.com/docs/en/sub-agents)
- Claude Code [hook transcript/sub-agent identity](https://code.claude.com/docs/en/hooks)
- Claude Agent SDK [usage 与 sub-agent accounting scope](https://code.claude.com/docs/en/agent-sdk/cost-tracking)
- DeepSeek Harness [canonical Session event model](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/subsystems/session.md)
- DeepSeek Harness [session telemetry mirror contract](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/subsystems/session-telemetry.md)
- DimAgent [CLI export/trace contract](https://dimcode.dev/en/docs/cli/)
- DimAgent [SQLite storage contract](https://dimcode.dev/en/docs/config/)

## Current Synthesis

当前最有价值的资产是现有 typed trajectory 雏形、native-first immutable evidence、精确
framing 和 provider adapter seam。此前 synthesis 错误地从“不能无损统一”推出“不能稳定统一”，
又把 evidence core 收缩成了材料目录，未解决 analysis 的共同输入。

修正后的边界是：telemetry adapter 负责把原生来源机械映射为 required、payload-bearing、
best-effort trajectory，并同时保留 native 依据；analysis 直接消费共同 execution/events，负责
索引、关联、去重与聚合。消息正文、工具参数/结果、delegation/history inheritance、context
change 与 usage 都是 trajectory 的一等材料；缺失与差异用 coverage 和 namespaced extensions
表达。Execution graph 仍只是 analysis 可选的内部索引，不是另一个交换合同。

## Residual and Return

- Residual：首版明确不支持 Pi sub-agent extension；实现首个 slice 仍需用真实 Codex
  parent/sub-agent 与标准 Pi session/branch/fork fixtures 校准 usage、branch、compaction 与 tool
  timing。Claude Code、DeepSeek Harness 与 DimAgent 只保留为 provider-neutral contract pressure，
  不承诺首版 adapters。
- Return：向 `design.md` 提供已证实的问题边界和统一 trajectory 方向；真实 corpus 属于设计
  接受后的第一实现 slice，用于冻结字段细节而不是重新决定是否存在共同模型。
