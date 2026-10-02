# Context 与讨论通知实施单元

状态：实现与定向验证完成。范围为产品审查 finding 1、2、5；未修改 finalization、local 退出条件或根五分钟检查。

## 落点与判据

- `src/objects.rs`：移除 `prepare_dispatch` 中“完整投影哈希不同即 Invalidate”的兜底；已有标题/正文、可见评论、hide/delete、resolve/unresolve 修改继续在对象事务内发 Invalidate，并传播给直接关联 PR。普通新增评论与系统提醒通过 Wake/引用读取；unknown 恢复仍走原 store/provider 证明链，不改 revision 假称旧会话收到新快照。
- `src/group/dispatch.rs`：删去唯一的哈希兜底调用。初次物化或真正 reset 仍渲染完整 Context。
- `src/objects.rs` 讨论收件：当前 assignee、同 thread 历史评论作者、当前有效 @、显式 active watch 的并集；跳过作者与重复地址。创建、评论和 @ 不建立全项 watch；显式退订后 @ 只投递本条。旧具体成员不重定向，关闭成员仍按原 direct contact 送达。
- `src/context.rs`：PR 对直接关联的 CLOSED Issue 使用完整的当前 description 与受 hide/resolve 控制的讨论投影；不递归展开关系。
- `docs/20-product-tdd/context.md` 与 `local.md`：更新上述当前契约。定向测试覆盖追加不 reset、编辑/reset 及相关 PR、同讨论/显式 watch/退订、关闭关联 Issue 投影。

## 验证

`cargo check` 与 `git diff --check` 通过。先前 33 个旧 fixture 编译错误由相邻单元机械修复后，以下真实 SQLite/对象边界测试逐个通过：`appended_comments_wake_while_existing_content_invalidates_related_pr`、`discussion_delivery_is_thread_scoped_and_explicit_watch_survives_mention`、`closed_linked_issue_keeps_current_visible_context`。相关旧测试 `thread_participant_receives_durable_reference_after_session_replacement` 的断言已校准为实际来源及 comment ID 引用，重跑通过。其余旧 `objects::tests` 有 6 项失败，涉及旧 member alias/profile、PR head、merge 及 seal 行为，未在本单元扩修。未运行 benchmark，未提交。

追加恢复验证：`ResetFixture` 补齐当前具体成员和 profile 关系，并按“旧会话通知与自然收尾后才 fence”驱动两种 terminal 顺序及重启路径。测试暴露的 continuation 批次无可领取输入由主实现单元修正后，`cargo test --bin braid store::session_recovery_tests::self_edit -- --nocapture` 为 2 passed、0 failed。OPEN continuation 领取 `wake_batch`，旧 finalizing 领取 `terminal_contact`；旧写者在已验证 teardown 后拒绝写入。
