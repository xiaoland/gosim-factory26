# Braid Local Product TDD

当前权威契约是 [local.md](local.md)。LocalObjects 持有当前完整 Issue/PR/comment 与关联数据，context 模块负责投影；StoreActor 与 queue 决定批次和失效，GroupDriver 执行物化、恢复、finalization 与 dispatch，SessionManager 管理可替换的中立句柄，provider adapter 管理 Codex/Pi 物理资源。

同一逻辑 group 和 Git worktree 可以绑定多个先后替换的物理 session。模型收到的是完整当前 Context；事件引用与本轮 writer 身份由 dispatch 独立提供。当前正文与语义事件在同一 SQLite 事务写入；Git 合并由持久 intent 和实际 ref 恢复，不假设 Git 与 SQLite 是一个事务。

[Context](context.md)、[生命周期](lifecycle.md) 和 [provider](app-server.md) 分别解释投影、调度与 adapter 边界。历史 GitHub 文档属于上游原始版本，不是此本地入口的配置或操作指南。
