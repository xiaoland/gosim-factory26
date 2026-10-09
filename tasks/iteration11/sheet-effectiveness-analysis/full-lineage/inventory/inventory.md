# I10→I11 sheet full lineage inventory

本账只覆盖指定 final-source run `20260929-042409-811f18d4`；没有混入 `tasks/iteration10/run-audit/sheet/`。它是索引与覆盖账，不把索引、关键词或截断摘要标作全文阅读。

## 规模与安全边界

- 原始 JSONL：565 个文件、38,414 行、188,251,949 bytes；解析错误 0。
- 早期读取账引用但 final-source 缺失 2 个原始路径（只列路径，不把其内容假定存在）：`work/native-homes/pi-deepseek-fast-01a0ec38-35dd-7292-b895-d0e44b9d34d8/2026-09-29T08-12-00-593Z_01a0ec38-7ed1-7254-82dc-68808058883f.jsonl`, `work/native-homes/pi-deepseek-fast-01a0ec38-8bcb-74d0-be82-614b9908cfc5/2026-09-29T08-12-04-675Z_01a0ec38-8ec3-772c-ad3c-be78bb664933.jsonl`。
- 记录索引：38,414 条；`message` 35,451、session header 509、custom_message 699、无类型运行记录 5。
- 以两个正式 coverage ledger 独立计算：已读完整 175，仅部分范围 1，需要新读 389；cells 自报范围另存 `reader_report_ranges`，不提升 ledger 覆盖状态。
- 机器索引保留原文件相对路径、原行号、msgID、timestamp、cwd、work item、阶段和完整行/载荷指纹；正文未复制，避免把凭据或大工具回包带入报告。
- 早期读取账与 final-source 反向对比：唯一账路径 179；same 175，只追加 1，内容前缀不一致 1，早期独有 2。改写/追加项保留早期与 final SHA-256、行数和路径，不能把 canonical 文件冒充完整历史。
- 反向差异明细（早期源本身是否已全读，及 final 是否仍缺）：
  - `work/native-homes/pi-deepseek-fast-01a0ec10-47cb-7063-b87c-3091a9ce6d5d/2026-09-29T07-28-06-207Z_01a0ec10-4c3f-7130-bbce-c852c0d29a59.jsonl`：coverage.json old=34行 ranges=[[1, 34]] old_full=True (appended)；final 追加行需新读（旧 ranges 只覆盖前缀）。
  - `work/native-homes/pi-deepseek-fast-01a0ec38-35dd-7292-b895-d0e44b9d34d8/2026-09-29T08-12-00-593Z_01a0ec38-7ed1-7254-82dc-68808058883f.jsonl`：increment/coverage.json old=8行 ranges=[[1, 8]] old_full=True (early_only)；final-source 缺失。
  - `work/native-homes/pi-deepseek-fast-01a0ec38-8bcb-74d0-be82-614b9908cfc5/2026-09-29T08-12-04-675Z_01a0ec38-8ec3-772c-ad3c-be78bb664933.jsonl`：increment/coverage.json old=5行 ranges=[[1, 5]] old_full=True (early_only)；final-source 缺失。
  - `work/native-homes/pi-glm-fast-01a0ec18-dd01-7710-8628-056a21a12e7a/2026-09-29T07-37-31-051Z_01a0ec18-eaab-742f-beef-c670a8c6bc1c.jsonl`：coverage.json old=36行 ranges=[[1, 36]] old_full=True (content_diff)；final canonical 内容不一致，整份按需新读；sibling 不能替代此路径。
- session/canonical 关系：55 个 native lineage key 关联多个物理文件；`session-links.json` 保留 top-level、sessions、subagent run/artifact 的每个路径，不能按 session basename 去重；重建 top-level 可能有不同 header session id，故另用 timestamp+UUID lineage key。
- 缺读交接账：`read-gaps.json` 按 coordination_history / de_lineage / mainline 列出每个原文件的未覆盖行段；这里的“缺读”来自既有 ranges，不把 sibling 副本或摘要折算为已读。
- 08:24 切割核对：有 1 个原文件的时间范围跨越 cutoff；`cutoff-crossings.json` 同时给出原始行号的 pre/post ranges，因此分区不能只按文件名或首 timestamp 推断。

## 可委派分区与去重增量导航

| 阶段 | 文件数 | 记录行数 | 当前需要新读的记录 | 适合交接 |
|---|---:|---:|---:|---|
| coordination | 53 | 2,411 | 1,083 | 按 work item/session 分区，保留原行号与 payload fingerprint |
| base | 67 | 3,631 | 1,487 | 按 work item/session 分区，保留原行号与 payload fingerprint |
| A | 115 | 7,187 | 4,115 | 按 work item/session 分区，保留原行号与 payload fingerprint |
| B | 110 | 7,696 | 5,456 | 按 work item/session 分区，保留原行号与 payload fingerprint |
| C | 131 | 10,918 | 8,341 | 按 work item/session 分区，保留原行号与 payload fingerprint |
| D | 29 | 2,394 | 2,394 | 按 work item/session 分区，保留原行号与 payload fingerprint |
| D-stability | 3 | 52 | 52 | 按 work item/session 分区，保留原行号与 payload fingerprint |
| E | 53 | 3,710 | 3,710 | 按 work item/session 分区，保留原行号与 payload fingerprint |
| integration | 4 | 415 | 415 | 按 work item/session 分区，保留原行号与 payload fingerprint |

建议分区：coordination_history 负责 Issue 1 与全 DB 协作演变及 08:24 后 ABC/base 增量；de_lineage 负责 Issue 6/7、PR 11/12 及其子角色后段；主线负责 Issue 1、PR 13/14 在 08:24 后的原生新增。相同 payload 只可作为候选重复，必须同时核对原 path、msgID、timestamp，不能按 basename 合并。

## 读取状态的含义

- `already_read_full`：现有 `coverage.json`、`increment/coverage.json` 或 cells read-ranges 对该原文件覆盖 1..N；可复用早期全文阅读账。
- `already_read_partial`：现有账只覆盖明确行段；其余行仍需新读。
- `needs_new_read`：final-source 原文件未在现有读取账中出现；不能因同 session 的副本或摘要而标已读。
- 逐记录状态按行段计算，适用于无头 continuation；未标正文已读的 payload 仍需回原 JSONL。
- `read-gaps.json` 是正式 `coverage.json` + `increment/coverage.json` 的 ledger 缺口分配索引，不是本轮各 cell 已完成语义阅读后的终态；`reader_report_ranges` / `reader_report_status` 只反映 cells 自报范围，未用于提升 `read_status`，脚本与关键词索引也不计全文阅读。

## SQLite 留存能力（只读、保留 WAL）

- 表计数：`work_items` 14、`provider_sessions` 444、`turns` 682、`context_resets` 359、`local_items` 14、`local_comments` 589、`local_activity` 1102、`events` 3494、`associations` 8、`local_merges` 8。
- description：只能看到当前 `local_items` title/body 与 revision（revision>1 的 item 14）；没有 description history 表，events 只有 invalidation 元数据，deliveries 的 raw_payload 空行 3102/3102。
- relation：`associations` 与 `local_merges` 只有当前/最终行（当前 associations active=0 为 0，merge error 为 0）；没有关系变更历史，需回 native JSONL。
- hide/resolve：当前 comments lifecycle hidden 3、resolved_through 非空 28，activity 中有 resolved 30、unresolved 2、hide 4；没有 comment state history 表，完整状态演变仍需 native JSONL。

## 机器文件

- [inventory.json](../../report.md)：summary、work item/assignment 映射、565 文件覆盖索引与字段契约。
- [records.jsonl](records.jsonl)：38,414 条逐行原始位置索引；无正文复制。
- [lineage-comparison.json](../../report.md)：早期 `evidence/`、`increment/` 已读源与 final-source 的逐路径存在性、行数、SHA-256、前缀/内容差异账。
- [session-links.json](../../report.md)：同一 native/session identity 的多物理载体关系与各自覆盖状态。
- [read-gaps.json](../../report.md)：按三个可委派分区列出需要新读的原文件和精确行段。
- [cutoff-crossings.json](../../report.md)：列出跨 2026-09-29T08:24:25.679855Z 的文件及其原始行号区间。
- `build_inventory.py`：可复核的只读生成脚本；SQLite 使用 `file:...?mode=ro`，没有修改 DB/WAL。
