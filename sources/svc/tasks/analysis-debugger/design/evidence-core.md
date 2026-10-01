# Evidence Core：稳定的 best-effort trajectory

## 修正后的结论

Evidence core 是 telemetry 导出、analysis 直接消费的统一语义合同。它的中心不是 manifest，
而是一份**有实际 payload 的、稳定的 best-effort trajectory**。Codex、Claude Code、
DeepSeek Harness、DimAgent 与 Pi 的差异否定的是“无损映射成单一线性 transcript”，不是统一
trajectory 本身。

Evidence bundle 必须同时包含：

```text
最小 header
    + required trajectory（executions + semantic events）
    + referenced native evidence
```

正常 analysis 只读共同 trajectory 就能重建消息、工具链、parent/sub-agent 关系和消耗；只有
来源特有分析、映射歧义、复核或未来重新归一化才读取 extension/native。Execution graph 若
analysis 需要，仍只是它从 trajectory 构造的内存索引，不是另一套交换格式。

## 为什么统一模型成立

五类实现共享的不是文件布局或 session 定义，而是可观察事实：存在可区分的 Agent execution，
execution 产生消息、模型/工具活动、状态与上下文变化，部分事实有父子或历史关系，部分活动附带
资源计量。不同来源可以缺失事实、使用不同计量口径或保留额外事件；这应由 best-effort、coverage
与 extension 表达，而不是以差异为由放弃共同语义。

| Harness | 对 trajectory 的具体压力 |
| --- | --- |
| Codex | parent delegation 与 fork inheritance 必须分开；旧 cumulative token 与新 response usage 必须保留不同 temporality/identity。 |
| Claude Code | 一个 session 可有多个 Agent execution；self token 与 subtree cost 可以来自不同样本，不能合并口径。 |
| DeepSeek Harness | 失败 model attempt、request context、stream 与 context replacement 证明 trajectory 不能退化成最终消息 transcript。 |
| Pi | entry 是树而非单线；fork、branch、compaction 与 usage 需要 history predecessor/context-change 语义。首版不解析 Pi subagent extension。 |
| DimAgent | SQLite/export/trace 证明 source ref 不能依赖 JSONL 行号；在真实 fixture 前不声称其语义映射已验证。 |

## Bundle 的最小组成

### Header

Header 只保留解释 trajectory 所必需的信息：

- evidence/trajectory format version；
- normalizer identity/version；
- provider 与 source format identity；
- 用户选择的根与实际采集边界；
- trajectory/native 内容完整性绑定；
- 按能力列出的具体缺口。

导出时间、泛化的 acquisition method taxonomy、重复的 package/material/capture status 和独立
discovery graph 都不是 core 必需字段。ZIP 成员表已经能充当文件目录，不再发明第二份 inventory。
采集失败只记录具体对象、原因与受影响能力，不建立抽象 receipts 子系统。

### Executions

trajectory 包含零个或多个 execution declaration。`execution` 表示包内可区分的一段 Agent
工作上下文；它不等同于文件、OS 进程，也不强迫所有 provider 使用同一种 session 概念。

每个 execution 必须有：

- 包内唯一、确定性生成的 `execution_id`；
- provider-native identity 的 source ref；
- `root | subagent | unknown` 的已知角色，未知时不得猜测。

可选字段包括显示名称、模型和 provider-native IDs。Parent/sub-agent 不通过一个含混的
`parent_id` 表示，而由 relation events 表达。

### Semantic events

每个 event 的公共 envelope：

| 字段 | 合同 |
| --- | --- |
| `event_id`, `kind`, `payload` | 必需；ID 在当前 trajectory schema 下确定且包内唯一。payload 必须包含已映射的实际内容，不能只给类型或 native 坐标。 |
| `seq` | 必需；仅表示确定性的导出顺序，不冒充跨来源时间或因果顺序。 |
| `execution_id` | 必需但可为 `null`；无法可靠归属时不猜。 |
| `source_refs` | 必需且非空；指向 native material 的记录、组件或字节范围。一份原生记录可产生多个 events。 |
| `timestamp` | 可选；保留来源精度，不用 capture time 补事件时间。 |
| `turn_id`, `predecessor_ids`, call/response identity | 有证据时 best-effort 提供；`predecessor_ids` 用于表达 Pi branch 等非线性历史。 |
| `mapping` | `explicit | derived | tentative`；tentative 默认不参与精确 parent/subtree accounting。 |
| `extensions` | 可选、版本化 namespace；不能重定义公共字段。 |

第一版公共事件族：

| `kind` | trajectory 必须携带的材料 |
| --- | --- |
| `message` | role 与可用的文本/多模态内容；大内容可用包内 blob ref，opaque 必须显式。 |
| `reasoning` | 可用的 full/summary/opaque 内容及其可见性，不要求所有 provider 提供。 |
| `tool_call` | call identity、工具名和实际参数；缺失参数显式为 unknown。 |
| `tool_result` | call identity 或 unresolved 状态、实际结果内容与已知 outcome。 |
| `lifecycle` | agent、turn 或 model attempt 的 start/complete/error/cancel，以及可知的错误。 |
| `context_change` | 模型/配置/提示词变化与 append/replace/compact/reset；可知时引用受影响历史。 |
| `relation` | delegation、history inheritance 等端点、触发事件与依据。 |
| `usage` | 未预聚合的 token/cost observations，带 owner、scope 与 temporality。 |
| `provider_event` | 尚不能共同解释的 namespaced 事件及原生 payload；同时形成相应 coverage issue。 |

`provider_event` 是演进阀，不是逃避公共建模的垃圾桶：已经具有上述公共含义的事实必须映射到
公共事件；只有丢弃 extension 仍不改变公共字段语义的内容才能留在 extension。

下面是供字段复核的最小 wire sketch，不代表已经冻结命名。重点是 trajectory 自身含有正文、
关系与计量，而不是要求消费者再从 native 拼装：

```json
{"type":"execution","execution_id":"exec_root","role":"root","source_refs":[{"material":"native/root.jsonl","record":"session-1"}]}
{"type":"execution","execution_id":"exec_child","role":"subagent","source_refs":[{"material":"native/child.jsonl","record":"agent-a"}]}
{"type":"event","event_id":"evt_prompt","seq":1,"kind":"message","execution_id":"exec_root","payload":{"role":"user","content":[{"type":"text","text":"检查失败测试"}]},"source_refs":[{"material":"native/root.jsonl","line":8}],"mapping":"explicit"}
{"type":"event","event_id":"evt_delegate","seq":2,"kind":"relation","execution_id":"exec_root","payload":{"relation":"delegation","from":"exec_root","to":"exec_child"},"source_refs":[{"material":"native/root.jsonl","line":12}],"mapping":"explicit"}
{"type":"event","event_id":"evt_usage","seq":3,"kind":"usage","execution_id":"exec_child","payload":{"owner":{"type":"execution","id":"exec_child"},"scope":"self","temporality":"delta","measurements":{"input":1200,"output":240}},"source_refs":[{"material":"native/child.jsonl","line":19}],"mapping":"explicit"}
```

若 child transcript 缺失，第二条 execution 仍可存在，但 header 的 execution-relations/usage
coverage 必须是 partial，analysis 只能报告已观察到 delegation 和未知 child consumption。

## Parent/Sub-agent 与分支

relation 至少区分：

- `delegation`：一个 execution 发起另一个 Agent execution；
- `history_inheritance`：fork/branch/continuation 继承已有历史或上下文。

两种关系可以同时存在，不能压成单一 parent。关系端点可以是 execution 或 event，并携带
`explicit | derived | tentative` 映射状态和 source refs。若已观察到 child identity 但 child
transcript 未采集，仍声明 child execution，并在 coverage issue 中记录缺失材料；analysis 因此
可以展示 frontier，而不是把 child 消耗误报为零。

Pi 的 `parentSession` 首版映射为 history inheritance，不解释为 sub-agent delegation。首版不支持
Pi subagent extension 只限制 adapter 覆盖，不限制公共合同的表达能力。

## Usage 是一等事件

每条 usage event 表达一个未折叠 observation：

| 字段 | 含义 |
| --- | --- |
| `owner` | execution、event、model response/operation 的已知归属；未知可显式表示。 |
| `scope` | `self | subtree | unknown`。Claude main-loop token 与 whole-tree cost 因此拆成两条。 |
| `temporality` | `delta | cumulative | gauge | unknown`。analysis 只有在 identity 足够时才求差或去重。 |
| `measurements` | provider 明确报告的 token buckets、total、金额和时长；缺失字段不补零。 |
| `sample_id` / `counter_id` | 原生存在或可确定重建时提供，用于重复 response 与累计序列去重。 |
| `source` | provider-reported 或 client-estimated；金额必须带币种。 |

共同 token 名称首版只覆盖 `input`, `output`, `cache_read`, `cache_write`, `reasoning`, `total`。
adapter 只有在原生含义匹配时才使用共同名称；包含关系或口径不同则保留 provider measurement
并通过 extension 说明，不机械改名。每个 measurement 还要声明它相对其它 measurement 是
`standalone | included_in | additional_to | unknown`；例如 cache read 是否已包含在 input、reasoning
是否已包含在 output，不能靠字段名猜测。`total` 始终是来源报告值，不由 telemetry 自行相加。

聚合规则在 core 中固定如下：

- 同一 observation 内不同 measurement 默认不可相加；只有明确 `additional_to` 才能组合；
- profile 只在同 metric、同单位、同 scope、同口径的独立 delta observations 间求和；
- cumulative counter 按 `counter_id` 排序求差；首个样本只有在捕获边界证明从零开始时才进入
  known subtotal，否则它是 unknown baseline；显式 reset 开新序列，未解释的下降进入 ambiguous；
- `sample_id`/response identity 相同且内容相同的重复样本只计一次；内容冲突则全部进入 ambiguous；
- gauge 不求和，只报告 observation；self 与 subtree 不相加，subtree 也不能反推 child self；
- fork/history inheritance 复制的历史 observation 保留原 owner，不作为 child 的新增消耗；
- cost 按 currency 与 `provider-reported | client-estimated` 分开，不换汇、不混加；
- usage coverage 按 metric 表达；缺失 measurement 只让该 metric unavailable/partial，不补零，也
  不机械降低其它 metric。

Telemetry 负责提取 observation 和标注口径，不生成唯一 totals。Analysis 负责累计样本求差、
response 去重、exclusive/inclusive/subtree 汇总，并把无法归属或可能重叠的样本单列出来。

## Extensions、native 与 coverage

Extensions 使用版本化 namespace，例如 `codex.rollout/v1`、`pi.session/v3`。规则只有三条：

1. 忽略 extension 不能改变任何公共字段已声明的含义；
2. 忽略 extension 会让某项分析不完整时，header 必须有对应 coverage issue；
3. extension 不能冒充原始证据，所有派生事实仍能回到 native source refs。

Native evidence 保留 source-faithful bytes/records/blobs，服务于复核、来源特有分析与将来的
renormalization。它不再是常规 analysis 的必读输入。Source ref 只要求 material identity 加该
material 支持的坐标；JSONL 可以用 line/byte offset，SQLite export 或 API records 使用自身稳定
坐标，不强迫它们伪装成 event index。

Coverage 以少量能力域表达：content、tool linkage、execution relations、history/branch、usage、
timestamps、terminal state。每域为 `complete | partial | unavailable`，并引用具体 issues。未知
事件、缺失 child、截断内容、tentative relation 和 usage scope 冲突都必须降低对应 coverage；
best-effort 不允许“吞掉后仍称 complete”。

## 对当前 `svc.trajectory/v1` 的判断

当前实现是正确起点，不应删除。它已经有 typed events、source refs、relationships、capabilities
和 lossiness；主要问题是：

- `message` 不含正文，`reasoning` 不含可用内容；
- `tool_call` 只保留参数类型，`tool_result` 不含结果；
- Codex `token_count` 被明确丢弃，没有 usage record；
- 一个 trajectory 只围绕单 thread，无法声明多个 execution 及 delegation/inheritance；
- trajectory 被定义为可丢弃 cache，导致 analysis 仍可能依赖 provider decoder；
- ordinal `rNNN` 在 normalizer 演进后不具备稳定语义 identity。

因此首版实现方向应是将它演进为下一版 required trajectory，而非另造 execution graph 或删除
projection。版本升级允许增加实际 payload、execution/relation/usage 事件和内容寻址 ID；旧
`v1` 继续由兼容 reader 读取，但不能宣称具备新增能力。

## Analysis 消费验收

1. 同一套 provider-agnostic analysis 只读共同 trajectory，即可对 Codex 与标准 Pi 返回消息/
   工具链、已知 branch/关系和 usage；无需重放 provider 状态机。
2. Codex parent 与 sub-agent 可遍历，返回 execution exclusive usage、可靠 descendant 的
   inclusive usage，以及未采集/歧义 frontier。
3. 丢弃 extensions 后公共分析结果的既有含义不变；受影响能力诚实降级。
4. 累计样本、重复 response、fork inherited history 不被重复计为新增消耗。
5. 每个共同 event 和派生指标可回查 native refs；未知不是零，partial 不是 complete。

## 已接受的设计决定

1. Required、payload-bearing trajectory 是 telemetry→analysis 的主合同，native 是复核和重新
   归一化依据。
2. Execution + semantic events，而不是 provider session/file，是最大公约数。
3. Delegation 与 history inheritance 分离；tentative relation 默认不进入精确 subtree accounting。
4. Usage 使用 `owner + scope + temporality + measurements`，不制造统一 total。
5. 从现有 `svc.trajectory/v1` 版本升级，不废弃 trajectory，不另建持久 execution graph。

首版 adapter 范围是 Codex rollout 与标准 Pi session。Claude Code、DeepSeek Harness 与 DimAgent
只作为共同模型的设计压力和 provider-neutral contract fixtures；本轮不承诺其采集或 normalizer。
