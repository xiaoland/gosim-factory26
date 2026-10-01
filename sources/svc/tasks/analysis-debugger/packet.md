# 将 `svc analysis` 重定位为 Coding Agent 调试与剖析工具

- **目标**：让 `svc analysis` 从“原始证据导航器”变成 Coding Agent / agent
  harness 的诊断工具：telemetry 导出自包含、payload-bearing 的 best-effort trajectory 与
  source-faithful native evidence，analysis 负责机械关联行为与消耗；调用 Agent 负责结合任务
  语义解释事实、提出原因和结论。共同模型应以 extensions 和 coverage 接纳 Codex、Pi 与后续
  Agent 的差异，而不是放弃统一 trajectory。
- **边界**：产品与技术设计已先行接受，现已获准实现；不加入断点、单步、在线控制或模型判分；
  不把因果判断、任务质量结论交给 SVC；不执行 release。任务包基线已按 Human 要求单独提交，
  实现变更仍保持未提交，等待最终复核。
- **完成验证**：以 Codex 与 Pi 的代表性日志证明同一分析表面可以返回执行拓扑、已关联的
  turn/model/tool 链、带覆盖说明的 token/cost/time/tool 指标和 native evidence refs；调用方
  无须重放 provider 状态机，未知与缺失不会伪装成零或完整；相关 CLI、bundle、迁移和
  fresh-wheel 合同通过。
- **当前事实**：用户指出的两个核心缺口成立。现有 `query` 只匹配扁平结构并返回 native
  refs，`read` 只读原生帧；关系 join、branch/turn 重建与指标聚合仍落在调用 Agent。
  Codex `token_count` 保留在 native capture，却被 normalizer 明确丢弃且由测试固化。
  现有 `svc.trajectory/v1` 是可演进的共同模型雏形，但缺少实际内容、usage 和多 execution；
  当前把它降为 optional cache 也使 analysis 缺少稳定输入。详见
  [`inquiry.md`](inquiry.md) 与 [`design/evidence-core.md`](design/evidence-core.md)。
- **当前决定**：Human 已接受 [`design/evidence-core.md`](design/evidence-core.md) 的 unified
  trajectory 合同与 [`design/analysis-interface.md`](design/analysis-interface.md) 的 agent-friendly
  query/read 交互。Closure review 已补齐 usage ledger、显式 leaf-path、coverage scope 与版本矩阵；
  设计阶段关闭。Human 已接受 [`verification.md`](verification.md) 的验收证据方案。
- **当前实现**：[`plan.md`](plan.md) 的 11 个 slices 已完成。Codex parent/sub-agent consumption、
  标准 Pi branch/fork/compaction、trajectory v2、evidence v4 与 analysis API v3 已通过源码树和
  fresh-wheel 验证。Pi subagent extension 延期；Claude Code、DeepSeek Harness、DimAgent 仍只
  作为设计压力。

## 支撑材料

- 现状与外部格式证据：[`inquiry.md`](inquiry.md)
- 待讨论设计：[`design.md`](design.md)
- Evidence core 专项：[`design/evidence-core.md`](design/evidence-core.md)
- Agent-friendly 交互专项：[`design/analysis-interface.md`](design/analysis-interface.md)
- 已接受的验收证据方案：[`verification.md`](verification.md)
- 已接受的线性实现路线：[`plan.md`](plan.md)
