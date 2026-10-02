# 本地 attempt-08 的 Context 编辑采用与投影

本页只读核对 2026-09-28 本地 attempt-08 GitHub、Sheet 停止后的 `braid-state/braid.sqlite3`、根 Issue 的原生 Pi JSONL 首条输入，以及该轮 Linux Braid 所用 attempt-07 `braid-source.tar.gz` 中的 `objects.rs`/`context.rs`。没有修改 run、数据库或生成应用，也没有执行测试。活动表保留历史动作；`local_items` 与 `local_comments` 只表示停止时快照，不能互相替代。路径和查询口径见末尾。

## 采用事实：根 Issue 与其它工作项不同

| attempt-08 | 两题全局历史动作 | 根 Issue #1 的停止时状态 | 根讨论历史 |
| --- | --- | --- | --- |
| GitHub | `local_activity` 有正文 `edited` 6 次（均在 PR）、`comment_edited` 2 次（Issue #4/#7）；无 hide/resolve/unhide/delete | 正文 revision 1、1,217 字符；30 条评论均 visible，`resolved_through`、`hide_reason` 均空 | 18 条顶层评论、12 条 reply；无根正文 edit、comment edit、hide 或 resolve |
| Sheet | `edited` 25 次（Issue #3 有 15 次），hide 3 次；无 comment edit/resolve/unhide/delete | 正文 revision 1、1,217 字符；25 条评论均 visible，`resolved_through`、`hide_reason` 均空 | 13 条顶层评论、12 条 reply；无根正文 edit、comment edit、hide 或 resolve |

Sheet 的三次 hide 是已发生的真实操作，分别为 Issue #3 comment #86（06:03）、PR #11 comment #91（06:07）、Issue #5 comment #103（06:16）；原因都明确写了 shell 剥蚀反引号片段，随后重发完整版。当前三条仍是 `hidden`，有 `hide_reason` 和 `updated_at`；这是修正坏消息，不是收起过期的已完成讨论。GitHub 无 hide。两题有大量 reply，说明讨论串入口被采用；“没有 resolve”只表示该能力在本地这两题未用，不能由数量断言模型审查品质。

## 真实重建输入中的历史负担

两题根 Issue 都在恢复时重建过 Context；下面只计对应原生 JSONL **第一条 user 消息的 Context 文本**（非整次会话 token/全部后续工具读取）：

| 根新会话时间 UTC | Context 字符 | 内含本根 `issuecomment-*` 数 | 可区分的旧进展与后续结论 |
| --- | ---: | ---: | --- |
| GitHub 04:49:43 | 2,938 | 1 | 初期拆分记录 |
| GitHub 05:32:51 | 4,255 | 6 | 进度催办及回应开始累积 |
| GitHub 06:43:44 | 15,705 | 20 | #5 于 04:57 称共享基础未发布、催促 commit/push；同一新 Context 仍含 #7 于 05:06 说明 PR #1 已合入 develop。#17/#32 等早期“已合并/进行中”清单也继续在正文中。 |
| Sheet 04:50:03 | 4,335 | 3 | 拆分、种子契约与改派进展 |
| Sheet 05:33:32 | 5,768 | 7 | #24 于 03:31 记录 #2 改派；同一新 Context 已含 #50 于 05:04 说明共享基础 PR #2 已合入。 |
| Sheet 06:44:34 | 11,139 | 16 | #24 仍与 #50、#58 等之后的合并状态一起被送入。 |

旧进展不等于无用：#17/#32、Sheet #13 的契约裁决等包含来源、检查或依赖，根可能需要审计来龙去脉。上面两组“未发布→已合入”“改派→已合入”则是较明确的状态更新候选，可在明确结论保留后隐藏旧催办或折叠解决的线程。Braid 不理解这些句子的时效性，保持可见是当前默认；此处没有测量模型实际注意力、错误归因或可节省 token，不能把输入增长全判为浪费。根会话后续也可能主动 `view --comments`，本表不覆盖那些读取。

## 08 投影语义：有能力，使用时会影响 Context

实际 08 Braid 对应的 attempt-07 源码快照中，`objects.rs::hide_comments` 把选中评论设为 `lifecycle='hidden'`、保留 `hide_reason` 并发 `Invalidate`；`resolve_comments` 在根评论上写 `resolved_through` 为当前线程最大评论 ID，同样发 `Invalidate`。`read_comments(..., include_hidden=false)` 对 hidden 或位于 `resolved_through` 截止点内的评论不给 `body`；`context.rs::render_comment` 仍输出评论引用、作者、时间和状态，然后在 `minimized`/`folded` 分支返回，不渲染正文。截止点后的新回复不折叠。delete 则将正文置空、不能恢复。由此，“hide/resolve 实际用了也毫无效果”与实现不符；它们收起的是 Context 中的正文，不擦除对象历史。`comment view --include-hidden` 可按需读取折叠内容。

源代码语义不等于本地根已产生收益：两题根从未 hide/resolve，故上述旧评论在实际重建输入中照常出现。Sheet 三条 hide 验证该能力被代理用于坏消息修正，但本次没有对它们对应成员的重建前后做逐字节输出对照，不能借它们量化节省。对正文编辑，`local_activity.edited` 与 `context_resets` 应分开看：Sheet Issue #3 的短期进度写入正文会触发自身 Context 重建，[高用量因果报告](../../experiment-infrastructure/cells/hotfix09-cost-causes.md)已定位 06:47、07:02、07:12 三次；这证明可编辑能力被用，但用在短期进度时会带来重读成本，不能直接取消正文更新能力。

当前最有区分力的判断是：**根工作记忆能力存在，讨论/回复和 Context 重建确实承载了交接；根的历史整理机制未被采用，而子项的 hide 被用于修正传输损坏。** 候选原因包括没有明确“进展事实何时转为过期”的人工收束动作、根持续串行集成时缺少整理时点、以及从创建起保留完整审计历史本身合理；现有记录不能在三者间定量分摊。改进应从一次真实根线程开始：保留决策和验收结论，用 hide/resolve 收起已被后续结论取代的旧催办，再核对下一次 Context 的正文与引用是否符合预期；这属于审查/工作方法，不是让 Harness 自动按词句或时间判定过期，也不是硬设 hide 数量。若要论证价值，需要比较同等任务下决策准确性、漏读、恢复成本和审计可追溯性，当前单轨迹不提供该反事实。

原始 DB 分别位于 WSL `/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-08/generation/runs/pi-braid--hackathon--github-97914b9e3158cf/workspace/official-generation/template/.factory26/20260928-030347-78b10c07/braid-state/braid.sqlite3` 与 `/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-08/generation/runs/pi-braid--hackathon--sheet-d478f7dc8ff84f/workspace/official-generation/template/.factory26/20260928-025746-66feadac/braid-state/braid.sqlite3`；原生会话路径从各 DB `provider_sessions` 中按根 Issue assignment 取回，在同一内层根 `work/native-homes` 下读取。08 使用的 Linux binary hash `4074f51e…` 与 attempt-07 `braid-linux` 相同；投影源码取 attempt-07 `braid-source.tar.gz`（SHA256 `03eca1db…`）。
