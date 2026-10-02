# Braid Local 精简

用户已授权应用架构审查中的三类精简候选。本单元只改 Braid；不启动模型实验，不提交。

远端 mention 验权、数据库 runtime owner lease、GitHub outbox 的 recover/claim/finish API 均无 Local 调用方，已移除 StoreActor 包装、命令和实现。Local 的 `runtime.lock` 仍承担同路径主进程互斥；迁移时的独立文件 lease 保留。已发布 migration 与历史表不改，旧数据库的事件、owner lease、outbox 和 status comment 行仍可读取；`runtime_status` 保留历史 pending/uncertain write 计数。 `objects.rs` 的本地 @mention 投递、订阅与 direct contact 不属于远端验权，未清退。

运行错误原先写进无人消费的 GitHub outbox。宿主 status/result 能显示 turn 与全局运行状态，但不能呈现每条 Operational Status 的工作项消息，因此 Store 将消息写为对应本地 Issue/PR 的 Braid 系统评论，并加入 timeline；同一工作项连续相同状态只写一次。这条路径不创建 Event、wake batch 或 outbox intent，也不调用评论通知，因此不额外唤醒 Agent。错误仍可在对象评论与宿主状态/结果证据中诊断；旧 outbox 积压不自动重放或抹除。

Issue/PR 的 provider 恢复过程已收敛到现有 GroupDriver，按工作项类型选择原指令与 PR head ref 检查；失联 turn 仍先标记 unknown，再决定是否可恢复，保留离线恢复与旧输入重放语义。删除未被 `src` 使用的直接 `url` 依赖；它仍是其它依赖的间接依赖。

验证：`cargo check` 通过；`git diff --check` 通过。新增 `operational_status_is_visible_without_queueing_work`，覆盖 Issue/PR 系统评论可见、重复去重及不产生队列/写出意图。当前 `cargo test operational_status_is_visible_without_queueing_work` 尚未执行到测试：仓库现有测试目标编译有 33 个旧 API 签名错误，包括 `local.rs` 的 `ProfileDefaults` / `CliContext` 和 `provider/factory.rs` 的 `CliContext`，以及 Store 既有 reset fixture 少传参数；本单元不越界修这些 fixture。

残余边界：历史 outbox pending 行仍作为证据保留，不会通过已删除的 API 自动送往 GitHub。若未来恢复远端 GitHub 运行模式，需要重新定义验权、owner 和写出执行契约；不可把这些 Local 清理后的空接口当成可用远端消费者。
