# Verification：Coding Agent debugger / profiler 验收证据方案

Human 拥有最终 acceptance；本文件只拥有实现应返回哪些可复核证据，以及什么观察足以支持接受。

## Qualification record（2026-09-19）

- `pdm run test`：275 passed。
- `pdm build -p svc_cli`：sdist 与 wheel 构建成功。
- clean temporary venv 仅安装 wheel 后，标准 Pi fixture 完成
  `export v4 → analysis --schema → overview → profile → trace → read`；overview 的手算 usage 是
  input=114、output=25、cache_read=15。
- Targeted contracts cover Codex root/child delegation 与 child usage、Pi active-path/all-work usage、
  evidence v4 integrity、trajectory v2 strict payloads、版本矩阵、cursor scope，以及 binary/Unicode
  byte-for-byte read pagination。

## 验收目标

验收证明的不是“新增字段存在”，而是调用 Agent 不再机械重放 provider 日志，即可：

1. 看见 root/sub-agent execution、branch/fork、model/tool/context/lifecycle 结构；
2. 得到口径明确、不会重复计数的 self/inclusive usage，并辨认未知和歧义；
3. 用一次 overview 加至多一次 trace/profile 回答预设诊断问题；
4. 从任何公开 ref 继续读取共同语义或精确 native 依据；
5. 在 Codex 与标准 Pi 上使用同一套 analysis 协议。

首版 adapter 只验收 Codex rollout 与标准 Pi session。Pi subagent extensions 明确延期；Claude
Code、DeepSeek Harness、DimAgent 只提供 provider-neutral contract pressure，不要求采集器或
normalizer。

## 设计关闭前的冻结项

以下均已有推荐答案，不再需要新架构讨论；实现开始时把字段名和 fixtures 固化为 executable
contract：

- **版本轴**：evidence bundle v4、trajectory v2、analysis API v3 独立演进；支持矩阵见下文。
- **Usage ledger**：同 metric/scope/口径的独立 delta 才求和；cumulative 需要已知 baseline 或
  相邻求差；reset、duplicate、gauge、self/subtree、fork inheritance、currency/basis 按
  [`design/evidence-core.md`](design/evidence-core.md) 的规则处理。
- **History selector**：默认 `all_work`；路径由显式 leaf event ref 选择，不猜 active branch。
- **Provider surface**：保留 `telemetry agent-thread` 以减少迁移；新增 `--provider codex|pi`，新
  调用显式传入。通用 `--home` / `--id` 承载 provider-native home/entrypoint，现有
  `--codex-home` / `--thread-id` 作为 legacy Codex 兼容别名；analysis 不接受 provider 参数。
- **首版范围**：Codex 必须支持 delegated child/grandchild 与其消耗；Pi 支持标准 session tree、
  branch、compaction、fork/`parentSession`，不支持 subagent extension。

`agent-thread` 只是现有采集资源名，不等于 evidence core 的 execution 定义；一个 export 可以
包含 root 和已确认的 delegated descendants。

## Fixture 与 Oracle 原则

- 使用冻结、脱敏、保留真实 wire shape 的 Codex/Pi 原生 fixtures；不以测试专用虚构格式替代。
- 每个 fixture 记录 provider/source-format version 与它关闭的风险。
- Export 从原生 fixtures 产生 bundle；Analysis 测试优先消费导出结果，不只手工拼 bundle。
- 期望结果使用小型 semantic oracle/手算 ledger，不对整份巨大 JSON 做无意义 snapshot。
- 至少一个测试在 export 后移走 provider home，再执行 query/read，证明 bundle 自包含且 analysis
  不调用 provider normalizer。
- 同一 evidence、semantic version 和 request 重复执行，IDs、排序、聚合及 continuation 一致。

推荐最小 corpus：

| Fixture | 必含事实 |
| --- | --- |
| Codex single | user/assistant/reasoning、tool call/result、context/lifecycle、response usage、Unicode/大内容。 |
| Codex execution tree | root、两个 children、一个 grandchild、delegation trigger、每个 execution 的 usage。 |
| Codex degraded tree | 已见 child identity 但 transcript 缺失、tentative relation、悬空 tool result。 |
| Codex accounting | delta、cumulative snapshots、duplicate response、counter reset、cache/reasoning inclusion、零值与缺失值。 |
| Pi history tree | entry branch、明确 leaf、废弃路径、compaction、tool result usage。 |
| Pi fork | `parentSession`/history inheritance、复制历史、fork 后新增 usage。 |
| Provider-neutral pressure | Claude mixed self/subtree accounting、DeepSeek failed attempt/context replacement、非行号 source ref；只验证 core 可表达。 |

## 黑盒验收矩阵

### 1. Telemetry 与 trajectory

- Codex/Pi `list` 与 `export` 接受显式 provider，bundle 记录 provider/source format/normalizer。
- Bundle v4 必含 trajectory/v2 与 referenced native materials；trajectory/native 都参与完整性绑定。
- Message/reasoning、tool 参数与结果、context change、lifecycle、relation、usage 都携带实际 payload
  或可读取 content/blob ref，不只留下类型和坐标。
- 未识别来源事件成为 namespaced `provider_event` 并降低对应 coverage，不被静默丢弃。
- 每个 semantic event 能解析到有效 native source refs；丢弃 extensions 不改变公共字段含义。

### 2. Parent/Sub-agent 与缺失边界

- Codex root/child/grandchild 被声明为不同 executions，delegation 与 history inheritance 不混淆。
- Overview 给出每个 execution 的 self usage；inclusive 只包含 distinct、可靠 descendants。
- 缺失 child transcript 产生 frontier/issue；child usage 为 unavailable，不是零。
- 已观察 delegation 可保持 `relation_mapping=complete`，同时
  `descendant_closure=partial`；coverage 只降低受影响能力。
- 重复 relation 或同一 child 从多个材料被发现时，不重复 execution 或重复计费。

### 3. Pi branch、fork 与 history

- `all_work` 包含所有已发生路径；显式 leaf path 只包含 predecessor 链和有证据的 inherited
  context，两者事件集合由 oracle 预先列明。
- Overview 若知道 active leaf，返回其 event ref；query 不接受含混的“猜 active”选择。
- `parentSession` 映射为 history inheritance，不映射为 delegation。
- Fork 复制的历史可出现在 trace context，但 usage 保留原 owner，不成为 fork child 新消耗。
- Compaction/branch summary 作为 context change/usage observation 保留，不被当成普通 assistant
  message 重复计数。

### 4. Usage 手算 ledger

对每个 fixture 建立独立 ledger，逐项断言：

- 同 sample/response identity 的重复记录只计一次；冲突 duplicate 进入 ambiguous。
- Cumulative 已知 baseline 正确求差；未知首样本不进入 known subtotal；reset 开新序列；未解释
  下降进入 ambiguous。
- Gauge 不求和；self/subtree 不相加；tentative owner 不进入精确 inclusive。
- Input/output/cache/reasoning 的 inclusion relationship 可见；只有 `additional_to` 可以组合。
- Provider total 不由组件重算；缺失 metric 不补零，真实零保持零。
- Cost 按 currency 与 provider-reported/client-estimated 分栏，无换汇或混加。
- Profile 分页只分页 rows，scope aggregate 与页面大小无关。

### 5. Query 四个 intents

- **overview**：一次返回 roots、execution topology、relations、lifecycle、per-execution self/
  inclusive usage、coverage/issues 和下钻 refs；无需先 match/read。
- **trace**：execution/turn/event selectors 均返回关联后的 actual payload；tool call/result、所属
  turn/execution、context/lifecycle 可机械关联；大内容有 recoverable ref。
- **profile**：execution/model/tool 三种固定 breakdown 与 oracle 一致；不接受任意 group-by。
- **match**：closed predicates 的命中/不命中可预测；complete empty 与 coverage-limited empty 可
  机器区分；返回的每个 ref 都能被 trace/profile/read 消费。

预设两个端到端问题作为产品验收：

1. “哪个 Codex sub-agent 消耗最多，它执行了哪些工具，哪些消耗仍未知？”
2. “Pi fork 后新增了哪些工作和 token，哪些只是继承历史？”

每题最多使用一次 overview 加一次 trace 或 profile；不得读取 provider home 或自行重放 native
状态机。

### 6. Read、Refs、Cursor 与预算

- Exact content/blob/native read 保真；native forward read 的小页拼接与大页结果逐字节相同。
- 超大 Unicode/binary payload 可通过 cursor 完整恢复；截断有显式 content status/ref。
- 每个 ref 绑定 evidence/kind/id；跨 evidence、错误 kind、missing ref 返回稳定 conflict。
- Cursor 绑定 evidence、API/semantic version、intent、selector/order/scope；改 selector、换 evidence
  或不兼容升级明确失败。调用方不构造或修改 cursor。
- `max_bytes` 约束完整编码响应；pagination 不改变 evidence coverage。

### 7. Schema、错误与通道

- `analysis --schema` 能发现 query/read、版本、ref consumer 与最短示例；叶子 schema 是从运行时
  models 生成的 JSON Schema 2020-12。
- 发布 schema 可验证每个示例、实际成功响应和结构化 error；不存在“实现比 schema 更严格”的
  隐藏前提。
- 非法字段/枚举返回 JSON Pointer 与 allowed/expected；未知响应字段不影响兼容 consumer。
- Success/partial/unavailable：exit 0、stdout 一个 JSON、stderr 空；request error：exit 2；
  ref/cursor conflict：exit 3；bundle/runtime failure：exit 4；错误时 stdout 空、stderr 一个 JSON。
- 所有失败路径保持 provider source、bundle 和请求文件不变。

### 8. 版本支持矩阵

| Request/API | Evidence v3 + trajectory/v1 | Evidence v4 + trajectory/v2 |
| --- | --- | --- |
| 无 version（API v2） | 保持现有 query/read v2 输出。 | 明确拒绝，不让旧 reader 误解多-material bundle。 |
| `version: 3` query | 返回 `re-export-required` capability limit；不运行 provider normalizer。 | 完整 overview/trace/profile/match。 |
| `version: 3` read | 保留 v3 native exact/forward read。 | content/blob/native exact 与 native forward read。 |

Evidence v1/v2 继续拒绝并指向 recollection/re-export。Ref/cursor 不跨 evidence 或 semantic version
延续。迁移测试必须逐格执行，不能只测 happy path。

### 9. Fresh-wheel 与仓库资格

- 更新 Product Truth、Product TDD、Deployment、CLI help、migration note 和 release-change material
  的 canonical owners，不留下 task packet 作为唯一说明。
- `pdm run test` 通过；targeted contract/provider tests 能单独运行并清楚定位失败。
- `pdm build -p svc_cli` 后，在干净临时环境只安装 wheel，使用隔离 Codex/Pi fixture homes 完成：
  `list → export → analysis --schema → overview → trace/profile → read`。
- Fresh-wheel 流程不读取仓库源码或未打包 fixture/schema；构建产物包含需要的 schemas/resources。
- 不把五种 provider 全接入、无限日志规模、长期 dogfood 或性能优化升级为首版完成条件；响应
  边界与 256 MiB source 上限需保持，但没有证据时不发明 wall-clock SLA。

## 验收通过条件

以下条件必须同时成立：

1. 上述矩阵无未解释失败，完整 `pdm run test` 与 fresh-wheel smoke 通过；
2. 两个预设诊断问题满足两次 query 内完成，且结果与 semantic oracle/usage ledger 一致；
3. Codex child 消耗、Pi fork 新增消耗、unknown/ambiguous/partial 均未被误报；
4. 所有公开 refs、schemas、errors 和 migration cells 都由自动化检查覆盖；
5. durable docs 与实现一致，没有仍要求调用 Agent 机械重建 native 日志的旧合同。

验收失败应返回对应设计 owner：trajectory 映射问题回 evidence core，调用往返/可恢复性问题回
analysis interface，单 provider 解析问题回 adapter；不要用额外 fallback 或特殊输出掩盖。
