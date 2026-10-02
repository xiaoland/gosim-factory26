# Sheet 完整 lineage 覆盖账

## 来源与只读边界

本账使用唯一来源 `tasks/iteration11/sheet-effectiveness-analysis/evidence/final-source/workspace/official-generation/template/.factory26/20260929-042409-811f18d4`（原始 B），SQLite 通过 `file:<完整路径>?mode=ro` 只读打开；采集时 `braid.sqlite3-wal` 为 0 字节，未写入或 checkpoint 原件。当前材料包哈希见 `evidence/identity.json`（DB 对应 binary `3056feb7…`）。

旧全读审计已覆盖 04:24–08:24：176 个源/11203 行及 7 个增量文件段，10 个对象与 179 条评论的对象核对见 `tasks/iteration11/run-audit/sheet/coverage-validation.json`。本账不把该账重标为本轮逐字重读，但复用其结果并以关键原文抽查核因果。

## 本轮新增阅读范围

后 08:24 的 final-source 原始 JSONL 按原始文件身份计数，边界为文件名时间戳 `>=2026-09-29T08-24-23`；以下是机器索引/筛选范围，不等同于模型逐行语义阅读。巨大 tool 代码、同响应镜像和已核对正文没有逐字复制到上下文；语义抽查清单见 [semantic-excerpts.md](semantic-excerpts.md)。每个选定文件的 `[1,last_line]`、原始 path/line/msgID/fingerprint 仍由 inventory 记录保留；语义去重只合并重复 payload：

| 工作项 | 文件数 | 行数 | reset 数（post-cut） | blocked reset | continuation |
| --- | ---: | ---: | ---: | ---: | ---: |
| PR 2（基础） | 34 | 1,487 | 17 | 0 | 17 |
| Issue 1（根） | 17 | 922 | 17 | 0 | 17 |
| Issue 3 / PR 8（A） | 29 / 30 | 1,932 / 1,850 | 28 / 25 | 1 / 0 | 28 / 25 |
| Issue 4 / PR 9（B） | 11 / 50 | 821 / 4,050 | 13 / 44 | 0 / 0 | 11 / 42 |
| Issue 5 / PR 10（C） | 36 / 51 | 3,726 / 3,756 | 35 / 44 | 1 / 0 | 35 / 43 |

选择表达式是 `B/work/native-homes/*/2026-09-(29|30)T[时间]-[时间]-[时间]_*.jsonl`，按 worktree 中的 `issue-1/3/4/5`、`pr-2/8/9/10` 归类；session 镜像只在存在不同响应身份时保留，其他以 canonical direct 文件去重。D/E、PR13/14 的后 08:24 材料由主线/另一 cell 负责，本报告只引用其已登记的跨链评论和状态行，不重复全读。

与当前 inventory revision 的筛选账对齐后，时间阈值范围为 298 个原始 JSONL、20,433 条记录；其中 ABC/base 的 `needs_new_read` 全集为 19,399 条，coordination Issue1 另有 1,083 条，不能把时间阈值结果替代 inventory 全集。索引读取量不是模型语义上下文量，也不称“全读”。inventory 在本轮复核期间增加了 Issue4 的追加记录，旧快照数字不再采用。实际语义抽查和未读边界见 [post-0824-reading.md](post-0824-reading.md) 与 [semantic-excerpts.md](semantic-excerpts.md)。

## SQLite 对象覆盖

| 表 | 行数 | 覆盖用途 |
| --- | ---: | --- |
| `local_items` / `work_items` | 14 / 14 | 14 个当前对象的标题、正文、revision、state、父关系与候选指针 |
| `local_activity` | 1,102 | 创建、编辑、评论、回复、关联、合并、指派、resolve/hide/close 的追加动作流；最终 ordinal 1102 |
| `local_comments` | 589 | 全部当前评论；含 reply/thread、revision、lifecycle、resolve/hide 元数据 |
| `local_comment_delivery` | 2,227 | 2,041 delivered、12 queued、174 unreachable；recipient/reason/event 关联 |
| `events` | 3,494 | 1,573 wake、1,170 mention、672 invalidate、56 noop、18 assign、5 lifecycle；含 event_id、reference、writer/recipient/context revision |
| `context_resets` / `context_reset_events` | 359 / 672 | 356 applied、3 blocked；338 continuation、21 fresh；reset 到 session/turn/event 的绑定 |
| `associations` | 8 | 8 条 issue→PR 关系，当前均 active |
| `local_subscriptions` | 23 | 21 active、2 inactive，含 source 与 changed_at |
| `assignments` / `agent_instances` / `provider_sessions` / `turns` | 15 / 15 / 444 / 682 | 指派代际、角色实例、原生 session、turn 生命周期 |

所有表均用最终 DB 读取；历史版本没有被伪造：`local_activity.detail` 的编辑事件只说 title/body changed，`local_items` 只有最终正文，`local_comments` 只有最终 body（虽有 27 个 revision>1 的评论，但没有旧 body 快照）。因此历史正文仅在对应 native/tool 回包仍保存时可重建。

## 已知缺口

1. 这份 DB 是终态数据库而不是跨文件原子检查点；WAL 为零只说明本份原件没有待回放 WAL，不能证明采集前的中间版本、已被覆盖正文或未写入的远端动作存在/不存在。
2. `local_items` 与 `local_comments` 不保留每次正文/评论编辑前的 body。`revision` 能证明发生更新，不能单独回答旧版本具体写了什么；正文历史要以 native JSONL 的工具请求/回包为准，已超出保存处的旧内容不可恢复。
3. `events` 的 pending mention（18）和 blocked invalidate（3）仍在 DB 中；它们证明事件存在及当前未消费/不可投递，不证明负责人看见了对应正文。14 个对象已关闭/合并，而 `local_run.lifecycle` 仍为 `running`、`root_check_comment=581`，说明终态快照与历史工作流状态不能互换。
4. `local_comment_delivery` 的 `unreachable` 174 条主要因旧负责人被重新指派（reason `@glm-1 was reassigned; current assignee: @glm-9` 169 条），其余为非具体成员目标；回包和评论正文仍可能在 Braid/native 记录中存在，不能把 unreachable 解释成正文丢失。
5. 08:12 的系统 reset/invalidate blocked 状态保留在 DB（event `01a0ec37-7b44…`、reset `01a0ec37-80e9…`）；对应 early increment 原件仍在旧 audit 目录且已全读，但 final-source canonical 两路径缺失/追加边界仍不可补造。后续恢复链可证明之后动作，但不能补回该窗口中未执行的模型判断。
