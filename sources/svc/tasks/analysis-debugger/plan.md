# Plan：线性实现 Coding Agent debugger / profiler

## Owner and Expected Return

- Owner：Primary；不建立并行 Tracks。Advisor 已完成设计与 sequencing challenge，不拥有实现。
- Expected return：按已接受的 design/verification 从真实 fixtures 逐步交付 bundle v4、trajectory
  v2、Codex/Pi telemetry、analysis API v3、兼容迁移、durable docs 与 fresh-wheel 资格。
- Authority：[`design.md`](design.md)、[`design/evidence-core.md`](design/evidence-core.md)、
  [`design/analysis-interface.md`](design/analysis-interface.md) 与
  [`verification.md`](verification.md) 已被 Human 接受。实现不得借机重开其产品决定。

## Linear Execution Rules

1. 严格按下面顺序推进；前一 slice 的 executable contract 和最小验证通过后才进入下一 slice。
2. 两种 provider fixtures 从第一步同时在场，但 adapters 顺序实现；不用并行 Track 换取表面速度。
3. 每步保持现有 v2 tests 通过。版本分流在早期建立，不能等最后才补 compatibility。
4. 每步只增加下一步立即消费的模型、helper 或模块；不预建 plugin system、query DSL 或通用图框架。
5. 第 11 步是组合资格，不是首次测试；语义错误必须在所属 slice 当场关闭。
6. 无新 Human barrier；只有实现证据迫使改变已接受合同、扩大 provider 范围或修改授权时才返回。

## Ordered Slices

### 01. 冻结 corpus、oracle 与 baseline

**进入**：Design 与 Verification 已接受；尚未改 runtime。

**产出**：

- 脱敏、保留真实 wire shape 的 Codex single/tree/degraded/accounting fixtures；
- 标准 Pi branch/fork fixtures；
- provider/source-format version 与脱敏说明；
- 独立手算 usage ledger、leaf-path 事件集合、两个产品验收问题的预期答案；
- 旧 evidence v3 / API v2 compatibility samples；
- 当前 targeted/full test baseline。

**退出验证**：Fixtures 可由独立的小型 probe 按原生格式解析；oracle 明确来自手算事实而非待实现
算法；现有测试 baseline 通过。

### 02. 固化 wire models、schemas 与版本分流

**进入**：Codex/Pi 代表性反例与 oracle 已在场。

**产出**：

- trajectory v2 execution/event/measurement/coverage/extension models；
- evidence bundle v4 manifest/material/source-ref/content-ref models；
- analysis API v3 request/response/error/ref/cursor models；
- generated JSON Schema 2020-12 与最短 examples；
- API v2/v3、evidence v3/v4 的早期 dispatcher/rejection seam。

**退出验证**：正反 contract examples 同时通过 runtime model 与发布 schema 检查；usage inclusion、
history selector、coverage scope、ref consumer 和版本矩阵都有可失败断言；v2 请求仍走旧路径。

### 03. 完成 bundle v4 与 read 基础

**进入**：IDs、refs、材料坐标和完整性合同已由 models 固定。

**产出**：

- v4 deterministic write/load/validate；required trajectory 与 native materials 共同绑定 identity；
- content/blob/native material 定位与 exact read；native forward read；
- 完整响应 byte budget、fragment continuation 和 scope-bound cursor；
- 保留 evidence v3 native read 路径，不引入 provider fallback。

**退出验证**：小型 bundle 往返相同；trajectory/native 任一篡改被拒绝；Unicode/binary 用不同页
大小可逐字节恢复；跨 evidence/kind/version ref/cursor 明确失败。

### 04. 完成 Codex telemetry v4 导出

**进入**：Bundle v4 能承载并读取全部公共事件。

**产出**：

- provider-neutral CLI/service 参数：`--provider`、`--home`、`--id`，保留 legacy Codex aliases；
- Codex root/child/grandchild bounded collection closure；
- message/reasoning/tool/context/lifecycle actual payload normalization；
- delegation/history relations、usage observations、missing-child frontier 与 source refs；
- v4 export receipt，不再产生 optional-cache 语义。

**退出验证**：全部 Codex fixtures 由公开 export 产生 v4 bundle 并与 oracle 对照；source 不被修改；
所有 refs 可解析；重复发现不重复 execution/relation/usage；旧 Codex CLI aliases 仍按合同工作。

### 05. 完成标准 Pi telemetry v4 导出

**进入**：Codex 已证明共同 bundle/export 路径可用。

**产出**：

- Pi inventory/source resolution 与 v4 export；
- entry tree、predecessor、active leaf、branch、compaction、usage normalization；
- `parentSession` → history inheritance 与 fork 后新增工作归属；
- 明确不解析 Pi subagent extension。

**退出验证**：Pi fixtures 与原生 oracle 一致；all-work/path 所需 refs 完整；复制历史不新增 usage；
`parentSession` 不成为 delegation；公共 models 不出现 Pi-only 特判字段。

### 06. 完成 provider-agnostic 范围与关联分析

**进入**：Codex/Pi 的真实 v4 exports 均可用。

**产出**：

- execution/turn/event/tool call-result 关联与 deterministic ordering；
- delegation frontier、relation mapping 与 descendant closure；
- `all_work` 和 explicit leaf-path scope；
- capability coverage 与具体 issues；
- 仅为上述查询建立必要的内存索引，不持久化 execution graph。

**退出验证**：同一分析入口消费两种 provider bundle；事件路径与 oracle 一致；移走 provider home
后结果不变；analysis 不导入或调用 provider normalizer。

### 07. 完成 usage accounting

**进入**：Owner、relations 与 history scope 已可靠确定。

**产出**：

- sample/response dedupe；delta/cumulative baseline/diff/reset；gauge separation；
- per-metric coverage 与 inclusion relationships；
- self、distinct-descendant inclusive、subtree observation、frontier 与 ambiguous buckets；
- inherited-history exclusion；currency 与 reported/estimated cost separation；
- provider-neutral aggregation API，尚不绑定 query presentation。

**退出验证**：手算 ledger 全部一致；duplicate/cumulative/fork 不重复计费；未知、零、歧义分开；
tentative owner 不进入精确 subtotal；聚合结果不依赖 response page size。

### 08. 完成 query v3 四个 intents

**进入**：Association 与 accounting 已有独立、已验证 owner。

**顺序产出**：

1. `overview`：topology、lifecycle、per-execution usage、coverage/issues、下钻 refs；
2. `trace`：execution/turn/event selectors、actual payload、关联上下文与 recoverable content refs；
3. `profile`：execution/model/tool fixed breakdown、完整 scope aggregates 与 ambiguous observations；
4. `match`：closed predicates、可靠 empty semantics 与可消费 refs。

所有 intents 共用 response envelope、完整 byte budget、opaque continuation 与 deterministic order。

**退出验证**：两个产品问题各在 overview + 至多一次 trace/profile 中回答；所有公开 refs 可下钻；
小页/大页逻辑等价；profile 使用完整 scope 而非当前页；正常分析无需 native replay。

### 09. 收紧 CLI、schema、errors 与完整兼容矩阵

**进入**：Query/read v3 已能完成新路径。

**产出**：

- `analysis --schema` catalog 和 leaf schemas；
- 字段级 JSON Pointer/allowed/expected errors；
- stdout/stderr 与 exit 0/2/3/4 合同；
- continuation mismatch/restart guidance；
- 逐格实现 API v2/v3 × evidence v3/v4，并保持 historical cutoffs；
- 确认不存在 hidden provider-normalizer fallback。

**退出验证**：黑盒执行版本矩阵每一格和错误路径；schema 验证全部 examples、success 与 error
outputs；API v2 + evidence v3 行为不变；API v2 + evidence v4 明确拒绝。

### 10. 同步 durable truth、迁移与 release material

**进入**：外部行为、字段和兼容矩阵已稳定。

**产出**：

- 更新现有 Product Truth、Product TDD、Deployment canonical owners；
- 更新 CLI help、migration guide、release-change material；
- 删除“trajectory 是 optional cache”“调用 Agent 必须重建 native”“token 不是独立分析能力”等
  已失效 durable claims；
- 确保 task packet 不是唯一解释。

**退出验证**：所有文档命令/examples 可由实际 schema/CLI 执行；provider scope、版本、迁移和恢复
路径一致；Corpus/build checks 通过。

### 11. 最终资格与 fresh-wheel

**进入**：代码、tests、docs 与 packaged resources 已落定。

**产出与验证**：

- 运行 targeted provider/contract/analysis tests；
- 运行完整 `pdm run test`；
- `pdm build -p svc_cli`；
- 在干净临时环境只安装 wheel，使用隔离 Codex/Pi fixture homes 完成
  `list → export → analysis --schema → overview → trace/profile → read`；
- 再次执行两个产品验收问题与版本矩阵关键格；
- 记录验证证据、剩余限制和未实现的明确延期项。

**退出**：[`verification.md`](verification.md) 的全部接受证据成立，没有未解释失败、源码树依赖、
无法消费的 ref、误报 usage 或仍要求调用 Agent 机械重建 native 的路径。

## Known Deferrals

- Pi subagent extensions；
- Claude Code、DeepSeek Harness、DimAgent adapters；
- query DSL、在线分析/控制、断点/单步、模型评分与自动因果结论；
- v2 query/match 的最终移除；
- 无实测压力前的持久 analysis cache、性能框架或 wall-clock SLA。

## Current Gate

- Complete：01→11 已实现并通过完整测试、构建与 fresh-wheel smoke。已接受产品合同和 provider
  范围未改变。
