# GLM BookStack run：Braid 对象的实际用途

范围仅为 `pi-team-glm-bookstack` 的 `20260923-075835-137d82cf`。证据根目录：`/home/yyh/Development/factory26/runs/local/iteration-throughput-boundary/pi-team-glm-bookstack/work/output/.factory26/20260923-075835-137d82cf/`。以下仅分析对象正文、评论与其对应流程，不判断应用实现或验收声称的正确性。

1. **Issue #1 是预填的完整交付指令；PR #1 是实现完成后创建的单个交付对象。** 根 Issue 正文直接给出需求包、技术约束、授权和交付方式；Issue 执行者先在自己的 worktree 完成并提交 `b21564f`，随后创建关联 PR #1，其正文列需求覆盖、种子、验证与假设。这里没有从需求讨论形成设计、拆分子工作项再实现的对象演化。证据：`braid-state/braid.sqlite3` 的 `local_items(issue:1, pr:1)` 与 `associations`；`native/000-2026-09-22T23-58-43-666Z_01a0cb8e-b9d2-76ba-a5c3-eacd8890ad90.jsonl` 中 00:25:08 的 `git commit`、00:25:38 的 PR 创建调用；`events` 中 00:25:38 的关联和分配事件。

2. **PR 执行者提供了额外检查，但评论没有推动修订。** PR 执行者检查文字、运行前后端、执行 API 冒烟并于 00:28:39 标记 ready；Issue #1 评论 1 在 00:28:44 才提出“请自行复核后调用 pr ready”，晚于 ready；PR #1 评论 2 在 00:28:49 报告检查结果。下一轮 PR 执行者读取评论后没有提交修订；对象记录中仍是同一实现 commit `b21564f`。因此这里有独立检查的实际收益，却没有观察到围绕发现的问题协商、反馈、修改、再验收。证据：`braid-state/braid.sqlite3` 的 `local_comments(comment_id=1,2)`、`events` 的 ready / comment 通知顺序；`native/002-2026-09-23T00-25-38-916Z_01a0cba7-5f64-727d-8855-095da2836afa.jsonl` 中 00:26:30–00:28:39 的检查和 `pr ready`；`native/004-2026-09-23T00-29-10-902Z_01a0cbaa-9b76-71e7-a401-609445a31f25.jsonl` 的评论读取。

3. **合并与结案仍是线性阶段交接。** Issue 执行者曾在 00:27:59 试图直接 `pr ready`，被角色权限拒绝；PR 执行者 ready 后，Issue 执行者于 00:29:27 合并，再于 00:30:22 在交付树做最后冒烟、00:30:49 关闭 Issue。PR 执行者的 Issue #1 评论 3 于 00:30:23 发布，复述合并与验证结果；它没有提出新的决策。根 Issue 的末段验证发生在合并后，不构成合并前的讨论回路。证据：`native/000-2026-09-22T23-58-43-666Z_01a0cb8e-b9d2-76ba-a5c3-eacd8890ad90.jsonl` 的上述调用与 `only this PR group can mark ready` 结果；`braid-state/braid.sqlite3` 的 `local_merges(pr:1)`、`local_comments(comment_id=3)`、`events` 的 merge/close；`native/006-2026-09-23T00-29-49-416Z_01a0cbab-31e8-760e-b0a1-6cf4da923c6f.jsonl` 的收尾评论调用。

4. **讨论功能被使用得很浅。** 三条评论均是独立顶层串，没有 `reply_to`；当前库中没有 hidden/deleted 评论。Issue 评论 1 的串在 Issue 关闭后的 finalization 中被 resolve，属于清理已完成交接；对评论 3 的下一次 resolve 因 writer turn 失效而未成功。Issue/PR 正文当前修订号分别为 2/3，但数据库不保留正文版本历史，不能断言它们从未编辑；现有初始/后续 context 与事件未呈现围绕正文变更的协商。证据：`braid-state/braid.sqlite3` 的 `local_comments`、`local_items.revision`、`events` 中 00:31:56 的 resolve 通知；`native/008-2026-09-23T00-31-23-623Z_01a0cbac-a1e7-76d4-bddf-7559673cb035.jsonl` 的 resolve 调用及 stale writer 结果；`braid-state/physical/*/context.md` 的对象快照。

**产品结论：** 在这个单次 run，Braid 的角色门槛促成 PR 侧复验，Issue/PR/评论则主要充当工作移交和结果公告。若要评估“协作讨论”的收益，应看评论是否在 ready/merge 前触发可追踪的澄清、修订或取舍；本 run 没有这样的可见实例。该结论仅适用于此 run，且正文历史不可复原。
