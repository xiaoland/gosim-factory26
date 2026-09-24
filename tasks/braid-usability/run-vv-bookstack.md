# vv BookStack run：Braid Issue / PR 使用观察

范围仅限 `20260923-101118-26a0f6bf`。依据该 run 的 `braid-state/braid.sqlite3`（只读打开）的对象正文、评论、关联及事件，以及 `native/000…jsonl`、`002…jsonl`、`004…jsonl`、`006…jsonl` 中对应的 Braid 命令记录。这里评价协作载体的实际用途，不评价实现质量或验收分数。

1. **对象结构只有一层需求和一层实现。** `work_items` / `local_items` 仅有根 `issue:1`（「根需求」）与 `pr:1`（「实现 BookStack 知识库系统」）；`associations` 只有 `issue:1 → pr:1`。Issue 正文是平台交付要求及完整需求包路径；根 Issue Agent 在 `native/000…jsonl:34` 直接用一份约 4 KB 的 PR 正文创建 PR（见 `local_items.body`），一次写入架构、API、路由、种子数据、假设和验收方案，再交给实现 Agent。未见拆分后的子 Issue 或多个独立 PR。PR 正文确实让实现 Agent 拿到具体规格与验收计划，但其主要作用是从根 Issue 到单个实现任务的交接。

2. **可见对话是完成通知和验收回执，没有设计往返。** `local_comments` 只有三条顶层评论：`comment:1`（Issue，03:33:27）由 PR Agent 报告提交 `78bdaa0`、自检结果并写「下一步：等待根 Issue 验收」；`comment:2`（PR，03:44:23）由 PR Agent 在合并后收尾；`comment:3`（Issue，03:44:44）由根 Issue Agent 报告独立验收并关闭。三条 `reply_to` 均为 NULL、`thread_root` 各指自身，且没有针对需求假设的提问、答复或修订要求。具体定位：`local_comments.comment_id=1,2,3` 的正文和字段；`events` 中 `comment:1` 唤醒 Issue、`comment:2` / `comment:3` 唤醒对方，但通知没有形成可见的回复链。

3. **有独立复验这一实质贡献，但通过 Braid 传递的内容仍主要是流水线状态。** `comment:1` 给出构建、启动、API 冒烟和种子数据自检信息；随后根 Issue Agent 在 `native/004…jsonl:20-36` 读实现、重建并运行自己的验收脚本，在 `:42` 合并 PR，`comment:3` 写独立验收结果，最后在 `:48` 关闭 Issue。`local_merges.pr_node_id=pr:1` 记录实现提交 `78bdaa0` 合入 `e7f98a4`。这说明 Issue/PR 边界支撑了独立审查与合并；可见记录里没有审查提出修改、实现 Agent 回应或第二轮提交，因此评论本身更像「完成 → 复验 → merge」的交接凭据。

4. **高级讨论动作在最终状态未使用，正文历史不可完整还原。** 三条评论均 `lifecycle=visible`、`revision=1`，`hide_reason`、`resolved_through`、`reply_to` 均为 NULL；当前没有隐藏、解决或回复链。`local_items` 中 Issue `revision=2`、PR `revision=3`，但数据库只保留当前正文，不能凭 revision 推断正文文字曾如何演化，也不能断言历史上从未编辑。所见 native 命令显示 PR 在 `native/000…jsonl:34` 创建，之后 `native/002…jsonl:133,135` 发完成评论并置 ready；未在所检原生记录中看到正文编辑命令。这一局限不改变对最终评论结构和可见工作流的判断。

**产品结论：** 该 run 的 Braid 有明确的任务分配、实现说明和独立验收价值；Issue/PR 的讨论能力几乎没有转化为需求澄清或迭代协作。若目标是证明 Braid 能促成多方协商，单根 Issue → 单 PR → 验收合并的产物不足以支持；若目标只是留下任务与验收痕迹，这个实例已做到，但对象层级和评论线程带来的额外收益有限。
