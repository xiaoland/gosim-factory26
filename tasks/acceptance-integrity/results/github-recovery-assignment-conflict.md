# GitHub 恢复运行的成员指派冲突（2026-09-27）

官方自费运行 `e4e7f35f55eb` 截至 12:36 UTC 仍为 `RUNNING`，尚未进入评分。12:35:52 UTC 保存的[工作区快照](../../../runs/e20260927-03-github-resume/g01/fresh-20260927T1236-workspace.zip)中，新的 `braid-recovery.log` 从 11:57:44 起累计 8,041 次 `UNIQUE constraint failed: assignments.member_login`。工作区内的 `braid-state/result.json`、`run.json` 和 `braid.log` 来自恢复前的运行；其中的 SIGKILL 与 `generation_failed` 不能归因于本轮。

只读 SQLite 查询显示，Issue #2 的 `glm-3` assignment 已于 11:57:39 被标为 `blocked`，但 `local_items.desired_member_login` 仍是 `glm-3`；26 条先前排队的 `direct_contact` 仍为 `pending`。`sources/braid/src/store/mod.rs::begin_agent_assignment` 见到该工作项不再有 active/stopping assignment，就为同一 `member_login` 创建新 assignment，而 `migrations/0009_member_identity.sql` 的全局唯一索引拒绝复用该名字。候选事件不被消费，调度器因而反复重试。现有 `objects.rs::deliver_comment_to` 已拒绝向 blocked 成员投递新消息，但未收尾此前排队的消息。

最小修复是在 `begin_agent_assignment` 中识别发给已有 blocked/retired 成员的旧 `direct_contact`，将事件标记为 superseded、对应 delivery 标记为 unreachable，然后返回而不创建同名 assignment。若确需继续 Issue #2，应显式重新指派，取得新的成员名。修复应同时覆盖恢复前已排队和恢复后新投递的通知；不能删除唯一约束或重用旧成员身份。

目前不宜只因该错误取消整条官方运行：12:35 快照的 Pi 会话更新到 12:35:51，PR #8、Issue #7 仍有工作；与 12:26 快照相比，PR #8 和 Issue #7 新增了浏览器检查结果。该缺陷确认阻断 Issue #2 的旧通知接续，但尚未证明整体停滞。当前运行中的远端二进制无法原地替换；若后续需要接续，应先保存最新工作区，再用修复后的 Braid 从该快照恢复到新的自费 run，不能重用旧 ZIP 或把历史失败记录当成本轮结果。
