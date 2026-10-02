# PR 关闭关键字的 GitHub 对齐缺口

2026-09-28：用户指出 Closes 关联 Issue 未随 PR 关闭，要求还原 GitHub 协作体验。本轮只读核实，未改实现或运行。

## 已确认

Braid objects.rs 的 create_pr_with_options 只按显式 issues 参数调用 link_in；没有解析 PR description 的 closing keywords。apply_merge 在成功发布 Git ref 后将 PR 设为 MERGED，对关联 Issue 仅写 associated_pr_merged 活动，不修改 Issue 状态。普通关联和关闭意图没有区分。因此即使 PR 正文含 Closes #N、合入默认分支，目前也不会按该声明自动关闭 Issue。

GitHub 的规则是：PR description 中 close/closes/closed、fix/fixes/fixed、resolve/resolves/resolved 加 Issue 引用，在 PR 合入默认分支时自动关闭目标 Issue；仅关闭未合并 PR 不会关闭 Issue。普通评论不是这一声明入口。提交消息也支持 closing keywords，但属于另一触发入口，不能将仅支持 PR 正文宣称为完整覆盖。
来源：https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/linking-a-pull-request-to-an-issue

## 修正方向（待实施设计）

区分上下文关联与关闭声明；创建和编辑 PR 正文时让声明可见，合并实际成功后在现有事务/恢复路径完成 Issue 状态、活动和生命周期通知，失败或单纯 close 不触发。复用现有 Issue 关闭语义，不让 Agent 额外记忆补偿步骤。

需要先明确本地仓库默认分支的权威来源：local_run.delivery_ref 是交付目标，不能不经核实就等同 Git 默认分支。当前 develop→main 工作流中，如果默认分支是 main，子 PR 合入 develop 不自动关闭才是 GitHub 行为；不能为了修复而改成任意目标分支合并均关闭，也不能自动将父 Issue 的全部子项关闭。

验收边界：正文 create/edit/remove、多目标声明、默认/非默认分支、普通关闭/合并失败、成功合并与崩溃恢复不重复通知。Braid 有界行为测试允许；本项未部署，既有运行保持不变。
