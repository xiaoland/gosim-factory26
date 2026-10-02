# 08:24 后 ABC/base/根增量索引与语义抽查账

## 精确选择与结果

为避免把关键词导航当全文，我按 `full-lineage/inventory/records.jsonl` 的 `source_file + line + msg_id + exact_fingerprint` 生成机器索引，并以选定原始 JSONL 做定向语义抽查。筛选条件是 `timestamp >= 2026-09-29T08:24:23`、work item 为 `pr:2 / issue:1 / issue:3 / pr:8 / issue:4 / pr:9 / issue:5 / pr:10`、inventory `read_status=needs_new_read`。当前 inventory revision 的筛选结果为 **298 个原始 JSONL 文件、20,433 条 inventory 记录**。这是索引/筛选规模，**不表示每条都进入本模型语义上下文**。实际语义抽查的文件、行号、msgID 和结论见 [semantic-excerpts.md](semantic-excerpts.md)。

| 阶段 / work item | 原始文件 | 索引记录 | `needs_new_read` 记录 | 关键范围 |
| --- | ---: | ---: | ---: | --- |
| base / PR2 | 34 | 1,487 | 1,487 | 08:24 后至 11:53；原始行边界见 inventory |
| coordination / Issue1 | 19 | 1,083 | 1,083 | 08:24 后至 02:11；含根迁移、契约、最终关闭 |
| A / Issue3 + PR8 | 34 + 32 | 2,212 + 1,903 | 2,212 + 1,903 | 08:24 后至 11:58 |
| B / Issue4 + PR9 | 13 + 57 | 936 + 4,484 | 972 + 4,484 | Issue4 的时间阈值子集为 936；当前 inventory needs_new_read 全集为 972 |
| C / Issue5 + PR10 | 43 + 58 | 4,209 + 4,119 | 4,217 + 4,124 | inventory needs_new_read 全集；时间阈值子集为 4,209 + 4,119 |

文件级范围由 inventory 的原始路径和每条原始行号定义；没有按 basename 合并。前述范围包含 direct native 与同一响应的 session 镜像，镜像只有在不同身份时保留，纯重复只作为 fingerprint 对照。大型工具代码、重复正文和完整需求原文没有逐字进入本模型上下文；未列入 semantic-excerpts.md 的后段记录仍是**未做语义判读**，只能称索引覆盖。报告引用采用已抽查的原始 path:line、msgID，以及 DB 的 comment/event ID 和版本。

## 语义分块

1. **抽查批次 A（C / PR10）**：读取 Issue5 的刷新正文、PR10 状态和交付证据片段，确认 `a592c3e` 后仍等待 D 依赖；完整 path/line/msgID 见 semantic-excerpts.md #C1–#C3。
2. **抽查批次 B（B / PR9）**：读取 PR9 状态、依赖边界、通知后的“无动作”判断和根 Issue 当前契约片段；见 semantic-excerpts.md #B1–#B3。
3. **抽查批次 C（base / PR2）**：读取根契约、`paste` 新端点事实与事务边界片段；见 semantic-excerpts.md #base1–#base3。
4. **抽查批次 D（A / PR8 与根刷新）**：读取 A-3 已转交 C、C 合入后接缝消失的刷新片段；见 semantic-excerpts.md #A1–#root1。
5. **未抽查的记录**：本轮筛选范围中除上述语义片段外的记录，包括重复正文、完整 tool 代码、其余 assistant/user 决策，保留在原始 JSONL 与 records.jsonl 中，没有在本轮模型上下文逐条判读。D/E/PR13/14 的新增原生材料仍由主线/另一 cell 负责。

## 可恢复但不可补造的缺口

- inventory 明确记录旧审查引用但 final-source 路径缺失两份 08:12 canonical 文件：
  `work/native-homes/pi-deepseek-fast-01a0ec38-35dd-7292-b895-d0e44b9d34d8/2026-09-29T08-12-00-593Z_01a0ec38-7ed1-7254-82dc-68808058883f.jsonl` 与
  `work/native-homes/pi-deepseek-fast-01a0ec38-8bcb-74d0-be82-614b9908cfc5/2026-09-29T08-12-04-675Z_01a0ec38-8ec3-772c-ad3c-be78bb664933.jsonl`（以 inventory.md 的完整路径为准）。对应 early increment 原件仍在 `tasks/iteration11/run-audit/sheet/increment/` 并已由旧账全读，可复用其原生内容；但 final-source canonical 身份/追加边界无法宣称完整。DB blocked reset/event 是该 DB 内的结构证据，不是所有原生证据的唯一来源。
- native 载荷可证明 owner 说“我已核对/无需动作”以及其随后写入的 comment，但不能单独证明所有 recipient 已阅读；需要同时满足 delivery=delivered、对应 turn/response、且后续动作消费同一 revision，才可称为已消费。pending/unreachable 仍按缺口报告。
- 旧正文和评论的覆盖用 final DB 当前 body + native 工具写入对照；任何只在被覆盖前正文、缺失 native 文件或未持久化临时结果中的内容均不补写成事实。
