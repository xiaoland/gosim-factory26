# Braid Local 产品边界

Braid 将 Issue 和 PR 作为 Coding Agent 的持久工作记忆，而非固定执行阶段。Issue Agent 维护需求、设计与验收判断；PR Agent 在自己的 Git worktree 实施、自检和提交。根 Issue 可以接受多个 PR，最后在明确交付分支判断需求是否完成。

本地版本保留 Issue/PR 的 N:M 关联、评论稳定身份与可见性、逻辑 group、完整 Context 替换、精确 writer 回声抑制、失效 turn fencing、队列及 finalization。它以本地 SQLite 和 CLI 代替 GitHub 平台，不建设 GitHub HTTP 模拟服务或通用 backend 插件层。

可观察承诺与接口集中在 [本地运行契约](../20-product-tdd/local.md)。真实 Codex/Pi/Bub 输入替换、Factory26 导出交付树与官方 bench 结果必须由独立接入验收证明，provider 一轮 completed 不能替代这些证据。

本目录其它历史产品页描述原上游 GitHub 版的原始设计。此分支的裁剪差异以本页与本地运行契约为准；原上游实现保留在 Git 历史与相邻工作树。
