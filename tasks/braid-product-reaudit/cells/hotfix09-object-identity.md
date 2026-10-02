# 09 对象层：外部 Git 整合与 Issue/PR 共享编号

## 已观察的断点

08 GitHub 的 PR #5 在 Braid 数据库中已是 `CLOSED`，head 为 `refs/heads/braid-agent/issue-6/deepseek-req4`，base 为 `refs/heads/develop`，没有 `local_merges` 记录，`ready_commit` 为空。裸仓库的 `2d29c4de644ac3900edbf10dbcea1010278f396e` 是两父合并提交，第二父为该 PR 的 head `33258736ea85a857ae1f8305f23585348115c0ba`。此前 `merge_with_match` 仅看当前 base 是否已包含 head，一旦包含就拒绝“无新增提交”；它无法记录已在 Git 中整合的事实。08 的旧 PR 没有创建时 base/head 快照，不能凭当前祖先关系反推合并发生在 PR 创建后，故本修复不会自动改写其状态，也不修改运行中的数据库或应用。

另一个已确认断点是 `create_item` 按 kind 各自取最大编号。根 Issue #1 后的首个 PR 也得到 #1。对象身份和 CLI 查找均使用 kind+number，旧双 #1 可继续解析；直接重编号会破坏关联、评论、assignment 与 Git 路径。

## 本次行为

迁移 v13 为新 PR 保存创建时 base commit，并保存 Braid 曾观察到“不在当时 base 中”的 head commit。这个正证可在显式 head 的 PR 创建时取得，也可由 `pr ready` 取得；已非 draft 的 PR 再调用 `ready` 也会更新内部观察证据。`merge --match-head-commit` 的源头匹配检查仍先执行。若当前 base 已包含当前 head，只有当现有 head 仍包含那次正证时才把 PR 记为 `MERGED`；这一状态和 `local_merges` 收据在同一个 SQLite 事务中写入，不更新 Git ref。返回的 `merge_commit` 是本次判定看到的 base tip，可能晚于真正引入 head 的提交，通知也明确说明“当前 head 已包含于目标分支”，不冒称原始外部合并提交。已有 prepared merge 恰好已发布时仍交给原 `apply_merge` 恢复路径。

创建时 base 快照本身不足以证明外部整合：一个本来无差异的 PR 可能只把源分支同步到后来前进的目标分支。没有上述正证的 PR，即使当前 base 含 head，也维持 OPEN 并报告可核查的 base/head SHA 与缺失原因；旧 PR 的创建基线和正证均为空，不会被误标。Braid 不周期扫描 Git，也不推断 squash/cherry-pick 等未保持 commit 身份的整合。

新建 Issue 与 PR 从本地仓库两类对象的共同最大 number 之后取号，分配仍处于 SQLite Immediate transaction 内。旧碰撞保持 kind+number 的旧身份；现有 `(repository_node_id,kind,number)` 唯一约束不改，不能在含旧碰撞的库上追加跨 kind 的唯一索引。新 run 从根 Issue #1 开始，交错新建会依次分配 #2、#3、#4。该修复不改变旧 Git branch、评论或 assignment 键。

## 验证与限制

定向 Braid 测试通过：创建即无差异拒绝、观察到独有 head 后外部 merge 成功、源分支仅同步目标时拒绝、缺少观察证据/旧基线时拒绝、显式 head 创建后外部 fast-forward 成功、`--match-head-commit` 错误时不改状态，以及新编号交错创建与旧双 #1 后继续分配。测试名称为 `externally_integrated_head_requires_a_recorded_positive_pr_delta`、`published_head_ahead_at_creation_can_be_recognized_after_external_fast_forward`、`issue_and_pr_numbers_share_a_sequence_without_renumbering_legacy_collisions`。

曾运行 `cargo test --bin braid objects::tests::`，12 项中上述前两项通过，另有 6 项旧测试失败，涉及既有 profile 成员后缀、旧 published-head API、旧 assign 通知断言、旧冲突错误文字及 Issue close 断言；这些失败不作为本次两个行为的通过证据，未在本有界范围内改写其产品语义。三个定向测试单独均通过。未运行 Factory/设施测试或正式实验。

源码入口：`sources/braid/src/objects.rs` 的 `create_item`、`create_pr_with_options`、`ready_with_undo`、`merge_with_match`；迁移 `0013_pr_created_base.sql` 及 `src/store/mod.rs` 注册；持续语义见 `sources/braid/docs/20-product-tdd/local.md`。
