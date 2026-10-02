# 审查路径与证据

本次不写或运行模拟测试，不把代码中的分支存在等同于产品行为已经发生。证据来自已有真实运行归档、当前源码调用链与契约；对源码才支持的结论明确标注为边界推断。所有时间按原始材料记录为 UTC。

## 决策路径

1. 从对象事务追到收件人、事件、batch、group、physical session 和真实输入，辨别通知为什么成为执行。
2. 从终态对象与 `delivery_ref` 追到 local 退出，核实交付完成和可继续协作是否共享了不必要的生命周期。
3. 从 Invalidate 追到原会话通知、自然收尾、身份 fencing、teardown 和新 Context，核实每个持久状态对应的恢复事实。
4. 从 PR head/base、merge intent 和裸 origin 追到成员 clone，检查 Git/SQLite 边界，以及 LLM 能否看到并处理冲突。
5. 对重复机制和历史遗留逐项问：删除后会丢失哪个当前产品承诺；没有具体承诺才列入过度实现。

## 已读取的权威与边界

- `/Volumes/WorkSSD/Development/factory26/AGENTS.md`：允许只读调查与任务包整理；不新增基础设施测试；本轮不启动新模型实验。
- `sources/braid/AGENTS.md`：Local 契约为权威；对象与事件同事务；每工作项 clone；provider 原生树与 Braid assignment 分离。
- `sources/braid/docs/10-prd/README.md`、`docs/20-product-tdd/README.md` 和 `local.md`：当前产品与架构。
- `tasks/acceptance-integrity/cells/terminal-contact-loop.md`：两份来源快照的终态通知回环及恢复后无新增 Pi 会话的已有报告；本次重新核对了来源 ZIP，不把这份文字当成运行 oracle。

源码基线为审查时的工作区，`sources/braid` 含未提交实现与 migration 改动。该审查不对代码归属或提交完成度作推断。

## 原始材料定位

| 材料 | 来源 ZIP 内路径前缀 | 读取内容 |
| --- | --- | --- |
| `runs/e20260928-completed-replay/github/source-workspace.zip` | `template/.factory26/20260927-080209-0b57147a/` | `braid-state/braid.sqlite3`、turn 输入、对应 Pi JSONL |
| `runs/e20260928-completed-replay/sheet/source-workspace.zip` | `template/.factory26/20260927-082825-d9c4f6ea/` | 同上 |

ZIP 的 SHA256 分别为 `d4ca397ed629598ebe2801f75cfaf6f51d74454ae4bd831c21ccd82153af5200` 与 `9b981b0ee88b5b10563f4bab17d6e8ecb34a77fa803597a0cc9dfe8d21468b5c`。数据库页载入内存读取，没有改动来源归档或运行 state；两份 `PRAGMA quick_check` 均为 `ok`。源 ZIP 没有 `braid.sqlite3-wal`，因此本报告针对归档实际保存的数据库页，不声称覆盖取消时最后一瞬间的未归档写入。

[runtime-summary.json](runtime-summary.json) 保存查询结果、选择的事件/turn/batch ID、实际输入和原生消息摘录，以及源数据库与当前源码 SHA256。`provider_sessions` 数量是数据库记录数，不等同于 ZIP 内可找到的全部原生文件数；部分最近会话文件缺失，证实原生行为时只使用实际存在的 JSONL。

## 空批次回环的核对链

以下查询直接对来源数据库执行，未注入对象、事件或模拟 provider。

```sql
-- 没有事件成员的 turn，不凭“很多 session”推断回环。
SELECT t.trigger_kind, count(*) AS n
FROM turns t
WHERE NOT EXISTS (
  SELECT 1 FROM wake_batch_events be WHERE be.batch_id=t.batch_id
)
GROUP BY t.trigger_kind;

-- 证明 pending 事件仍唯一绑定于 consumed 批次，且原 turn 为 unknown。
SELECT e.event_id,e.work_item_node_id,e.reference,e.lifecycle,
       b.batch_id,b.lifecycle AS batch_lifecycle,
       t.turn_id,t.lifecycle AS turn_lifecycle
FROM events e
JOIN wake_batch_events be ON be.event_id=e.event_id
JOIN wake_batches b ON b.batch_id=be.batch_id
JOIN turns t ON t.batch_id=b.batch_id
WHERE e.lifecycle='pending' AND b.lifecycle='consumed';

-- 没有新评论时是否仍启动 terminal_contact。
SELECT count(*) AS n,min(started_at),max(started_at)
FROM turns
WHERE trigger_kind='terminal_contact'
  AND started_at>(SELECT max(created_at) FROM local_comments);
```

一个明确的 GitHub 残留输入是事件 `01a0e286-c7dd-7d22-9499-2f23da73c97c`：目标 issue:5，引用 issue:1 comment 79，当前 pending，却仍属于 consumed 批次 `01a0e2a4-cba4-7731-8ccf-dc86fba68357`；原 turn `01a0e2a4-d365-7b12-8c37-1bc0fbca4ae4` 在 `11:57:08Z` 变 unknown。紧接着 issue:5 从 `11:57:50Z` 起出现 39 个无成员输入的 turn。

Sheet 对应残留输入之一为事件 `01a0e2de-e48a-7b40-9de8-c0c39fbea09c`：目标 issue:4，引用 pr:1 comment 112，原批次 `01a0e314-f281-7453-a407-f687fef5e854` 已 consumed，原 turn `01a0e314-f910-7dd2-8711-2237d802be71` 在 `14:00:41Z` 变 unknown。issue:4 从 `14:01:03Z` 起出现 81 个空 turn。

Sheet 已完成的空 turn `01a0e3cd-9f3b-7620-b7e5-e0822c1c6c7f` 的双重证据：

- `braid-state/turns/01a0e3cd-9f3b-7620-b7e5-e0822c1c6c7f.md`：没有事件引用的“请处理 Issue #5”。
- `work/native-homes/pi-glm-fast-01a0e3cd-97b8-7052-8d86-40e65c41eb5f/2026-09-27T16-58-17-526Z_01a0e3cd-9a36-71f5-b5dd-40f7ba8d12e1.jsonl`：确有原生用户输入；assistant 消息 `81f5417c` 在 `16:58:25.301Z` 表示 Issue 已关闭、没有遗留工作。

评论互发也有原始记录：Sheet comments #209–216 多次陈述 main 未变、无待办，并明确要求停止重复确认。这支持“通知产生噪音”，但本报告的主要缺陷不依赖对这些中文内容作语义分类，而由空事件批次和原生输入证明。

## 当前源码与恢复限制

| 决策问题 | 核对路径 | 证据级别 |
| --- | --- | --- |
| 为什么没有新评论仍执行？ | `mark_turn_terminal(unknown)` → `schedule_event` → UNIQUE(event_id) → `advance_scheduler` → reactivation → claim | 来源运行与当前源码互证 |
| 原 request 是否能恢复旧 running？ | `local::execute` 身份校验 → `resume_*` 标 unknown → materializing reset → 空 `SessionManager.remove` | 源码确定路径，未运行当前二进制 |
| 锁能否证明旧进程停止？ | `local.rs` 的文件锁只作用于当前 state 路径；provider 句柄不持久化 | 进程与资源边界推断，不能当作停止证明 |
| Codex 能否证明 reset 通知已处理？ | `finish_running` → `ProviderAgentSession` → `AgentProvider` 默认错误；Codex 无 override | 源码确定路径，缺当前真实 Codex取证 |
| Git 合并是否应移除 intent？ | 真实 Git object/ref 与 SQLite 独立提交；`apply_merge` 可恢复一次发布 | 保留机制；未发现来源快照的 prepared merge 遗留 |

`rg` 全树核对了 `BRAID_COLD_STOPPED_SESSIONS` 和消息收据实现/调用方。没有运行 Braid local、cargo test、provider 命令、官网提交或模型调用。本轮也没有把历史失败快照归因于当前尚未执行的 reset 改动。

## 审查范围的停止点

三项核心问题已足以决定后续工作，因此不继续扩展为全文件逐行 review。完成出口与 merge 后续 ref 前进只列为待验证边界。复杂度候选通过调用方搜索与现有 outbox/lease 行数核对，不把文件长、trait 多或依赖多单独当成缺陷。

## 第二轮产品证据方法

第二轮仍只读取同两份归档，不运行新模型、官网实验或模拟测试。独立输出为 [产品审查](product-review.md)、[产品图](product-model.md)、[产品统计](product-evidence.json) 与 [源码基线](product-baseline.json)。源码读取期间有其它工作者实施已授权修复，起始与结束的文件哈希分别保存；技术旧报告不代表结束时未修复状态。

reset 比较只选来源 SQLite 中 lifecycle 为 applied 的记录，将 old/new provider session 映射到实际 `braid-state/physical/*/session.json`，再读取同目录 `context.md`。匹配后分别保存归档完整路径、provider ID、字节大小、reset ID、时间、触发事件与差异。比较仅去除已知历史传输包装和尾部空白；没有重写正文，也没有让模型概括后再比较。

分类为：新旧正文相等的 identical；新正文以旧正文为前缀且更长的 strict_append；其它 changed_existing。GitHub 配对 60 条（40/7/13），Sheet 配对 84 条（39/8/37）。`nonshrinking_prefix_count` 包含相同正文，不能当作严格追加数量；报告只用 `reset_change_kinds.strict_append` 表示纯追加。相同正文可能承担恢复，不能据此认定无用。归档 Context 字节计数不是 tokenizer 结果，更不代表已支付 token；未据此估算账单。

通知从真实 comment 的 reply_to、thread_root 和 `local_comment_delivery` 逐条追踪，记录收件身份、status、reason 与 event_id。报告将目标数、queued、delivered、unreachable 分开；delivered 是 Braid 投递回执，仍不等于一个独立的正常完成 turn。两个 GitHub 样本的 9 个目标包括 5 个不可达目标，不应表述为 9 轮已执行。实际内容包含“无行动项”的例子只用于说明存在真实讨论回执，主缺陷仍由投递控制流和持久事实支持。

finalization 数量按真实 turns.trigger_kind 与 lifecycle 汇总，输入读取归档的 `turns/<id>.md`。部分 finalization 携带其它待处理评论，故仅据触发名不能判断整轮冗余。关闭关联 Issue 正文消失、开放 backlog 阻止完成分支等仍为源码边界风险，没有在本轮实际复现业务失败。

对根五分钟检查的需求归属及当前已批准改动进度，以主线转达的用户明确要求为准：检查保留，前三技术修复与清理已经主线报告编译完成，WSL 尚未启动。本轮只把新 Operational Status system comment 列入后续 Context 验收来源，没有继续扩大取证。下一轮所需真实验收在产品报告末表中逐项给出。
