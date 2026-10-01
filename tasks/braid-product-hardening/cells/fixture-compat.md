# Braid 测试 fixture 编译兼容

状态：`cargo test --bin braid --no-run` 已可编译；运行期旧测试仍有语义失败，按本轮授权边界停止修改。

初次编译退出 101、共 33 个错误，完整输出在 [fixture-compat-build.log](fixture-compat-build.log)。只在 `cfg(test)` 区域把 `Request.defaults` 改为 `root_profile_id`，为测试 `SessionFactory` 和 provider 调用传入 `CliContext`，为 `LocalObjects::initialize` 传入根 profile，为 context reset 传入 binding id。`objects.rs` fixture 在初始化前登记测试 profile，且每个 writer 的 `assignments.member_login` 与 `local_items.desired_member_login` 使用同一个唯一成员名。

复编译退出 0，完整输出在 [fixture-compat-build-after.log](fixture-compat-build-after.log)。额外运行 `cargo test --bin braid objects::tests:: -- --test-threads=1`：10 项中 3 项通过、7 项失败，见 [fixture-compat-objects.log](fixture-compat-objects.log)。失败涉及旧别名断言与新具体成员身份、发布 head、合并冲突和讨论终态。它们已超出过期字段/函数签名的机械接线范围；没有改生产逻辑、测试断言或冻结运行。未提交。
