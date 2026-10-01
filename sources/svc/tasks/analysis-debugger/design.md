# Design: Coding Agent debugger / profiler 的产品与边界

## Forces and Constraints

- 用户需要诊断 agent 行为与资源消耗，而不是只定位日志片段。
- SVC 应承担可确定、可重复的机械工作；调用 Agent 应承担任务语义、因果与价值判断。
- Codex、Claude Code、DeepSeek Harness、DimAgent 与 Pi 的 authority 分别呈现 rollout、
  多 transcript、typed event log、SQLite/export/trace 与 entry tree；共同 trajectory 必须允许
  best-effort、非线性历史和 provider extensions，不能假装无损 transcript。
- required trajectory 必须携带可分析的实际 payload；source-faithful native evidence 用于复核、
  来源特有能力与重新归一化。二者都必须暴露 provenance、coverage 与 normalizer version。
- 不引入动态插件系统、查询 DSL、自然语言分析器、质量分数或第二套持久 authority。
- 现有 query/read 是 public contract，迁移成本必须显式处理。

## Proposed Coherent Solution

### 1. 产品承诺

`svc analysis` 是离线、确定性的 Coding Agent debugger/profiler。它回答：

- 这次执行实际形成了什么 session/branch/turn/model-call/tool-call 结构？
- 每个动作与结果怎样关联，哪些调用失败、重试、悬空或终止？
- 明确记录的 token、cost、cache、time、tool outcome 等指标是多少，覆盖范围是什么？
- 哪些原生证据支持这些事实，哪些信息缺失、含混或 provider 不提供？

它不回答“Agent 为什么这样做”“任务是否做得好”“应如何改进”，也不把 chronology 提升为
causality。调用 Agent 使用结构化事实与 native refs 完成这些语义判断。

### 2. Authority 与数据流

```text
provider-local sources
        |
        v
telemetry rooted collection + provider normalization
        |
        v
evidence core = minimal header + required payload-bearing trajectory
                + referenced native evidence
        |
        v
provider-agnostic analysis indexes + coverage + native refs
        |
        +--> overview: topology / terminal state / availability
        +--> trace: reconstructed branch/turn/model/tool chains
        +--> profile: token/cost/cache/time/outcome metrics
        `--> native read: exact fallback and semantic investigation
```

- **Telemetry owns**：entrypoint selection、bounded discovery、source-faithful capture，以及把来源
  事实 best-effort 映射为 required trajectory；它保存 observation，不预聚合唯一 totals。
- **Analysis owns**：直接消费共同 trajectory，建立查询索引、关联工具/历史/parent-subagent、
  去重和聚合 usage，并输出 coverage-qualified views；常规路径不重放 provider 状态机。
- **Provider adapter owns**：provider discovery/capture 与 source→trajectory normalizer；仍是内置
  静态 allowlist，不做第三方 plugin lifecycle。
- **Calling Agent owns**：任务目标关联、异常解释、竞争原因、质量/成本判断、改进建议。

### 3. 共同 trajectory 与 Analysis 内部索引

Evidence core 公开 execution declarations 和 semantic events，包含实际 message/reasoning/tool
payload、delegation/history-inheritance relations、context changes 与 usage observations。详细合同
由 [`design/evidence-core.md`](design/evidence-core.md) 拥有。

Analysis 可以从它构建 execution graph/spans 或其它内存索引，但这些不是第二套持久 schema。
不要加入“verification step”“good/bad retry”“case/episode”这类依赖任务语义或启发式分类。

### 4. 用户表面

保留 `svc analysis query/read`，不新增 `inspect`。Query vNext 是封闭 intent union：

- `overview`：首次调用直接返回 execution topology、每个 execution 的 usage 摘要、生命周期、
  coverage、issues 和下钻 refs；
- `trace`：按 execution/turn/event ref 返回实际 payload 与已关联的 model/tool/context activity；
- `profile`：按 execution/model/tool 固定维度聚合 usage/cost/cache/time/outcome；
- `match`：保留为低层 typed locator，不作为新流程必经步骤。

精确 `read` 保留为 content/blob/native ref 的 escape hatch。常见交互预算是一次 overview 加一次
定向 trace/profile；正常分析不需要回到 native 重建。完整合同由
[`design/analysis-interface.md`](design/analysis-interface.md) 拥有。

### 5. Trajectory 与 ref 规则

`trajectory.jsonl` 从可删除 cache 升级为 bundle 的 required semantic material。Analysis 的常规
路径只消费它；native 只用于复核、extension 与 renormalization。Event/execution identity 由
规范化语义与 source refs 确定生成，不能继续让会随插入记录漂移的 `rNNN` 冒充稳定 identity。

### 6. 首版 execution 范围

第一版从用户选择的 entrypoint(s) 出发，捕获 adapter 能以原生证据确认、且受边界约束的
delegated descendant materials。ancestors 与 fork/inherited sources 只在 normalizer 解释所需
或显式请求时采集。Analysis 结果同时返回：

- 每个 execution 的 exclusive usage；
- 按 distinct descendant execution 汇总的 inclusive usage；
- active branch 与 all-work usage；
- 无法捕获或无法可靠归属的 frontier/ambiguous usage。

详细 authority 和 wire shape 由 [`design/evidence-core.md`](design/evidence-core.md) 拥有。

### 7. Pi 首版边界

- CLI 用显式 `--provider codex|pi` 选择 inventory/export；通用 home 参数替代新增第二个
  provider 专名参数。source 模式也记录明确 provider，不靠不可靠的自动猜测。
- Analysis 不接受 provider 参数；trajectory schema 是共同 reader 的选择 authority。
- Pi normalizer 保留标准 session 的完整 entry tree，将当前 branch、废弃 branch 与 fork 继承
  区分；首版不支持 Pi sub-agent extension 或其内嵌 child results。
- usage 可挂在 assistant、tool result、compaction、branch summary 上；profiler 聚合
  identity-bearing samples，而不是写死某一种消息。
- Analysis 内部模型不排除 embedded child execution，但首版不为假设中的 Pi extension 编写
  parser、fixture 或 core 字段；以后由真实 adapter 压力启用。

## Live Alternatives

| Alternative | Why still live | Cost or risk |
| --- | --- | --- |
| 在现有 `query` 新增 `case/episode` intent | 已有旧任务提案，增量改动看似较小 | `case/episode` 边界依赖启发式；继续把 debugger 伪装成 locator，且 Pi branch 与 profiling 会迫使 intent 膨胀。 |
| trajectory 仍只是可删除 cache | 可以始终从 native 重建 | 把 provider decode 放回 analysis，不能形成稳定 telemetry→analysis 合同；不推荐。 |
| provider adapter 直接产出最终 report，不设共同 trajectory | 初次接 Pi 文件更少 | 每个 provider 重复 join/aggregation/coverage 逻辑，跨 provider 结果不可比较；不推荐。 |
| 新增 `inspect` 再保留 query/read | 名字更像 debugger | 形成重叠入口和第四套发现路径；现有 query 足以承载 closed intents，不推荐。 |
| major release 直接替换 query/read | public surface 最干净 | 未经真实 dogfood 就删除逃生口，迁移风险高；当前不推荐。 |

## Representative Consequences

- Enables：调用 Agent 一次请求即可获得已重建链路和成本画像；Codex/Pi 只各自解析原生
  差异；新增 provider 不复制 debugger 的 joins、aggregations 与 coverage 语义。
- Costs / risks：trajectory 若追求无损会变成巨型 normalized schema；必须用 best-effort、少量
  公共事件和 namespaced extensions 控制，并由真实 corpus 的共同诊断需求约束。
- Verification pressure：同一组 debugger questions 在 Codex/Pi fixtures 上产生同形结果；
  token/cost 不重复计数；branch 不串线；cache/compaction 口径透明；每个 derived item 可追到
  native refs；缺失字段返回 unavailable/ambiguous 而非 0。

## Residual / Return

- Closed：Evidence core 与 agent-friendly query/read 交互均已被 Human 接受。Usage ledger、显式
  leaf-path selector、coverage scope 和三条版本轴已在专项设计中冻结。
- First release：Codex rollout + 标准 Pi session adapters；Codex parent/sub-agent consumption 是
  必需能力，Pi subagent extension 明确延期。
- Residual：v2 query/match 在后续 major 的长期去留不阻塞本轮；ID/hash 算法、模块拆分、合理
  budget 常量和错误 code 最终拼写属于保持合同的实施细节。
- Return：设计阶段关闭；[`verification.md`](verification.md) 接管实施资格与最终 return。Claude
  Code、DeepSeek Harness、DimAgent 只作为 provider-neutral contract pressure，不承诺首版 adapter。
