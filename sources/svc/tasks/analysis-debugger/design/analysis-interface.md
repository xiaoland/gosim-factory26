# Analysis 交互设计：Agent-friendly query/read

## 结论

保留两个现有入口，不新增 `inspect`：

```bash
svc analysis --schema
svc analysis query --input evidence.zip --request <file|->
svc analysis read  --input evidence.zip --request <file|->
```

`query` 是对共同 trajectory 的 typed debugger/profiler；`read` 是按 ref 读取精确内容和 native
依据的逃生口。新版 query 使用封闭 intent union：`overview | trace | profile | match`。

目标交互预算是：

1. 一次 `overview` 后，调用 Agent 已知道 root/sub-agent 拓扑、各 execution 已知消耗、生命周期
   摘要、coverage 与具体缺口；
2. 再用至多一次 `trace` 或 `profile` 回答一个明确诊断问题；
3. 只有复核、超大内容或 provider 特有事实才需要 `read`。

## 对现有交互的复审结论

| 现状 | Agent-facing 问题 | 修正 |
| --- | --- | --- |
| `overview` 主要给 record counts、ranges 和 projection capability。 | 调用 Agent 仍需 match/read/join 才知道执行结构与消耗。 | 首次响应直接给 topology、per-execution usage、lifecycle、coverage 和 issues。 |
| Query 同时返回 trajectory/native refs，但 read 只消费 native refs。 | 部分公开引用没有可调用的后续动作。 | 建立 ref consumer 表；无消费者的 ref 不公开。 |
| `query_schema()` / `read_schema()` 是手写摘要，代码明确说实际校验更严格。 | Agent 无法可靠预构造请求，只能执行后试错。 | 从实际 request/response models 生成标准 JSON Schema。 |
| Validation errors 被折叠成“request 不符合 shape”。 | Agent 不知道错误字段、允许值或最小修复。 | 返回稳定 code、JSON Pointer 和 bounded expected/allowed 信息。 |
| Help 要求从 match 再读 contiguous native context。 | 在 accepted evidence core 下，这会重新把机械重建交给调用方。 | Trace 直接返回关联后的 normalized payload；native read 只作复核。 |
| Cursor scope binding、stdout/stderr 分离和 pagination≠partial 已存在。 | 这些是可靠的 agent-facing 资产。 | 保留，并补上 analysis semantic version 与完整响应字节预算。 |

## Agent-friendly 判据

| 判据 | 本设计要求 |
| --- | --- |
| 最少往返 | overview 不是目录；它直接返回可行动的 execution/usage/coverage 摘要。 |
| 可发现 | `analysis --schema` 一次发现 query/read；叶子 `--schema` 返回各自子集、示例、默认值和限制。 |
| 可构造 | 请求由严格模型生成标准 JSON Schema，不再以“实现比 schema 更严格”的手写摘要代替合同。 |
| 可判定 | `0`、unknown、partial、unavailable、空结果和分页具有不同机器语义。 |
| 可继续 | ref/cursor 可原样复制；每种 ref 都有唯一、明确的消费入口。 |
| 可恢复 | 字段级错误给 JSON Pointer、允许值和针对该错误的下一步，不要求盲目试错。 |
| 可控 | 固定 intent 与 selector union，不接受 SQL、JSONPath、regex program、任意聚合或自然语言 prompt。 |
| 可演进 | 请求显式携带合同版本；响应允许增加字段，调用方必须忽略未知响应字段。 |

“Agent-friendly”不等于所有输出都做成人类短文本，也不等于只提供 JSON。这里的核心是减少
调用 Agent 必须记忆、猜测、join 和重试的协议工作。

## Discovery 与 CLI 通道

```bash
svc analysis --schema
svc analysis query --schema
svc analysis read --schema
```

- 顶层 schema 是一个小型协议目录，包含 query/read request/response schema refs、支持版本、
  ref consumer 表和每个 intent 的最短示例。
- 叶子 schema 从实际 request/response models 生成 JSON Schema 2020-12，不手写一份较弱合同。
- `--help` 解释产品用途和解释边界；构造合法请求不应依赖阅读 help 或 Corpus 文档。
- 成功时 stdout 恰好一个 JSON value，stderr 为空；错误时 stdout 为空，stderr 恰好一个结构化
  JSON error。Analysis 无需额外 `--json` 开关。
- exit `0` 包括合法的 partial/unavailable；`2` 是请求错误，`3` 是 ref/cursor scope conflict，
  `4` 是 bundle/input/analysis failure。缺失 usage 不是 shell failure。

## Query vNext

初始请求显式声明 `version` 和 `intent`。Continuation 只重复 `version`、`intent`、opaque cursor
和页面预算；selector 已绑定到 cursor，不得重述或修改。

### `overview`：默认诊断入口

```json
{"version":3,"intent":"overview"}
```

默认 scope 固定为 bundle 声明的 roots、已采集 delegated descendants 和 `all_work` history。
它不能猜“最新 session”。若 provider 明确记录 active leaf，overview 可以返回该 event ref；路径
查询仍必须复制这个 leaf ref，不能提交含混的 `active` 开关。

响应至少包含：

- scope：roots、descendant policy、history policy；
- executions：ref、root/subagent/unknown、lifecycle state、model（若已知）；
- relations：delegation 与 history inheritance；
- 每个 execution 的 self usage，以及可靠 descendants 的 inclusive usage；
- tool/model/turn/lifecycle 的有界 counts 与失败/悬空状态摘要；
- 按能力域的 coverage 和指向具体对象的 issues；
- 可直接用于 trace/profile 的 refs。

Overview 返回 usage 摘要，但不倾倒完整事件正文或所有 usage samples。大量 executions/relations
可以分页；usage 摘要必须按完整声明 scope 计算，不能只统计当前页面。

示意响应：

```json
{
  "format":"svc.analysis.query/v3",
  "version":3,
  "intent":"overview",
  "evidence_id":"E",
  "status":"partial",
  "scope":{"roots":["exec_root"],"descendants":true,"history":"all_work"},
  "data":{
    "executions":[
      {"ref":{"evidence_id":"E","kind":"execution","id":"exec_root"},"role":"root","usage":{"self":{"status":"partial","known":{"input":1200,"output":240},"metric_coverage":{"input":"complete","output":"complete","cache_read":"unavailable"}},"inclusive":{"status":"partial","known":{"input":1200,"output":240}}}},
      {"ref":{"evidence_id":"E","kind":"execution","id":"exec_child"},"role":"subagent","usage":{"self":{"status":"unavailable","known":{},"metric_coverage":{"input":"unavailable","output":"unavailable"}},"inclusive":{"status":"unavailable","known":{}}}}
    ],
    "relations":[{"kind":"delegation","from":"exec_root","to":"exec_child","mapping":"explicit"}]
  },
  "coverage":{"relation_mapping":"complete","descendant_closure":"partial","usage":"partial"},
  "issues":[{"code":"child-evidence-missing","execution_id":"exec_child","affects":["usage","trace"]}],
  "page":{"next_cursor":null,"returned_items":2}
}
```

`known` 是已知 subtotal，绝不能命名成 total。真实测得的零是 `known` 中的 `0`；unknown 使用
per-metric coverage 和 issue 表示，不能用 `null` 或缺省值让调用方猜。某一 metric 缺失不应
让已完整采集的其它 metric 也变成 unavailable。

Coverage 绑定请求 scope。缺失 child transcript 不否定已经 explicit 映射的 delegation，所以
`relation_mapping` 可以 complete；但它使 `descendant_closure` 与 child usage partial。不能用一个
笼统的 relations 状态同时表达“已见边是否可靠”和“整棵后代树是否完整”。

### `trace`：关联后的执行轨迹

```json
{
  "version":3,
  "intent":"trace",
  "select":{"execution":{"evidence_id":"E","kind":"execution","id":"exec_child"}},
  "history":"all_work",
  "max_items":50,
  "max_bytes":65536
}
```

`select` 是封闭 union，只允许 execution、turn 或 event ref：

- execution：返回该 execution 的关联事件；可显式选择是否包含 delegated descendants；
- turn：返回完整 turn 内的 model/tool/message/context activity；
- event：返回该事件的操作上下文，例如 tool call/result、所属 turn/execution 和相关 lifecycle。

Trace 返回 normalized actual payload，不能要求调用 Agent 再从 native 拼工具参数、结果或正文。
它按 trajectory `seq` 稳定排序，同时返回 predecessor/relation refs；不得把 seq 或前后 N 条伪装
成 causality/branch context。大内容显式改为 content ref，并说明 inline/referenced/truncated；不能
静默裁剪。

`history` 也是封闭 union：`"all_work"` 或
`{"path":{"leaf":<event-ref>}}`。Path 由 predecessor/history-inheritance refs 确定，不以文件
相邻或 wall-clock 猜测。Inherited events 可以作为路径上下文显示，但 usage 仍归原 execution，
不能计为 fork child 的新增工作。若 active leaf 已知，调用方从 overview 复制它形成 path selector。

### `profile`：固定维度的完整范围聚合

```json
{
  "version":3,
  "intent":"profile",
  "select":{"execution":{"evidence_id":"E","kind":"execution","id":"exec_root"},"descendants":true},
  "history":"all_work",
  "breakdown":"model"
}
```

`breakdown` 只有 `execution | model | tool`。不提供 group-by 表达式：

- execution：self、可靠 descendant inclusive、frontier 和 ambiguous usage；
- model：token/cost/cache/time 的已知 samples 与口径；
- tool：call/result/outcome/time，不把工具统计冒充模型 usage。

Profile 对完整 select scope 计算，分页只分页 breakdown rows。Self 与 inclusive 数值不放在可直接
求和的同一序列；cumulative、重复 response、subtree samples 和 fork inherited history 必须先按
evidence core 规则处理。无法去重、无法归属或可能重叠的 observations 单列，不静默丢弃。

### `match`：低层定位，不是必经流程

保留 closed typed match，支持事件类型、role、tool name、literal text 和明确 ref/range 等有限
predicates。它返回可消费的 event/content/native refs 和小型 descriptor，不再返回只能展示、
没有后续入口的 trajectory ref。空结果只有在对应能力和范围 complete 时才是可靠否定。

## Ref、Read 与 Cursor

所有公开 ref 绑定 `evidence_id + kind + id`，调用方复制即可，不计算 hash、不理解 ID 格式。

| Ref kind | 消费入口 |
| --- | --- |
| `execution`, `turn`, `event` | `query` 的 trace/profile selector（profile 只接受适用 kind）。 |
| `content`, `blob` | `read` exact-ref。 |
| `native` | `read` exact-ref 或 forward range。 |

若某个 ref 没有上述消费方式，就不应公开。Trace event 同时带 source refs，因此调用方可以选择
继续使用共同语义，或下钻到精确 native 依据。

Read v3 继续使用两个严格形状，不增加查询能力：

```json
{"version":3,"ref":{"evidence_id":"E","kind":"content","id":"content_1"},"max_bytes":65536}
```

或从一个 native ref 开始 forward read。`ref` exact-read 与 `start` forward-read 互斥；后续只提交
cursor 和页面预算。

Ref 只承诺在其 immutable evidence snapshot 内稳定；trajectory 和 native 完整性共同绑定
evidence identity，因此重新归一化产生新 snapshot/ref，而不是让旧 ref 静默改义。

每个响应最多一个 `next_cursor`。Cursor 绑定 evidence、合同版本、intent、selector、ordering、
normalizer/analysis semantic version 和已解析 scope；不签名、不建立 server session。升级后无法
安全继续时，返回明确的 `cursor-version-mismatch`，要求用原始请求重新开始。

页面预算约束整个编码响应，而不只计算 payload。Pagination 不降低 evidence coverage；content
truncation 或 material omission 才降低，并必须提供恢复 ref。

## Coverage、Issues 与 Errors

顶层 `status` 只总结“当前 intent 对声明 scope 的回答能力”：`complete | partial | unavailable`。
具体能力同时保留独立 coverage，因此可以表达 relations complete、usage partial。

Issue 是稳定 code 加对象 scope 和受影响能力。至少区分：source 不提供、采集缺失、内容截断、
未知 provider event、tentative relation、usage scope unknown、usage overlap 和 child evidence missing。
不要引入模糊置信度分数。

字段错误必须让 Agent 一次修正：

```json
{
  "format":"svc.analysis.error/v3",
  "code":"invalid-request",
  "message":"Unsupported profile breakdown.",
  "details":{"path":"/breakdown","allowed":["execution","model","tool"]}
}
```

只对可恢复错误给具体 action，例如 cursor mismatch 重新执行原请求、missing source 重新采集、旧
bundle 使用兼容 reader 或重新 export；不统一标记 `retryable: true`。

## 版本与迁移

- 现有无 `version` 的 query/read request 继续按 v2 解释，输出保持 v2；不能在旧命令名下静默
  改义。
- 三条版本轴独立：新 evidence bundle 是 v4、required trajectory 是 `svc.trajectory/v2`、新
  analysis API 是 v3；版本号相同或不同都不互相推导。
- API v3 初始请求要求 `version: 3`。Bundle v3 缺少 trajectory/v2 时，query v3 只返回明确的
  `re-export-required` capability limit，不运行 provider normalizer 偷偷补建；read v3 仍可读取其
  exact native refs。Bundle v4 才能宣称完整的新能力。
- API v2 + bundle v3 保持当前行为；API v2 + bundle v4 明确拒绝，避免旧 reader 误解多 material
  evidence；API v3 + bundle v4 是完整支持路径。Bundle v1/v2 继续是历史 cutoff。
- `query --schema` 同时发布受支持版本的 discriminated schemas；顶层 `analysis --schema` 指向它们。
- `read` 的 exact native fidelity 保持；新增 content/blob ref 是加法，不让 read 变成搜索工具。
- `match` v2 在过渡期保留；v3 agent workflow 以 overview→trace/profile 为主。真实 dogfood 证明
  新路径覆盖后，再在后续 major 决定是否移除 v2，而不是本次先删。

## 明确不做

- 不新增 `inspect`，也不把 overview/trace/profile 做成三个 CLI 子命令；
- 不提供可组合 `views[]`、任意 selector tree、查询语言或自然语言分析 prompt；
- overview 不只返回目录，也不默认倾倒全部正文；
- 不返回无消费者的 ref，不要求调用方拼 cursor 或关系 ID；
- 不把 active branch、all work、self 和 subtree 消耗混为同一 total；
- 不要求 Agent 在得出每个事实前都读取 native；共同 trajectory 是正常分析输入。

## 已接受的设计决定

1. 复用 `query/read`，不新增 `inspect`；query 拥有四个 closed intents。
2. Overview 首次调用包含 execution topology、usage 摘要和 coverage，而不是正文。
3. Profile 只提供固定 execution/model/tool breakdown，不提供 group-by DSL。
4. v3 请求显式 `version: 3`；无版本请求在过渡期保持 v2 行为。
5. 每个公开 ref 必须有 query 或 read 的明确消费入口。
