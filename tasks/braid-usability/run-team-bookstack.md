# team-bookstack：Braid 对象使用观察

只读范围：`/home/yyh/Development/factory26/runs/batch-multi-agent-20260922-01/pi-team-bookstack/`。以 `braid-state/braid.sqlite3` 的 `mode=ro` 快照为对象依据，并定向核对 `braid-state/turns/` 和 `native/` 会话记录。本文评价协作方式，不评价应用实现质量或验收分数。

## 实际流程

根 Issue `issue:1` 已预填完整任务和授权。Issue Agent 读需求后，直接创建关联 PR `pr:1`，在约 10 KB 的 PR 正文中一次性写下技术选型、数据模型、全部页面/API、初始数据与验收方案；随即在 Issue 评论 #1 宣布已分析并激活实施 Agent。PR Agent 按该方案实现、自检并将 PR 标记 ready。Issue Agent 在独立工作区归档 ready 提交、构建和运行冒烟检查，在 Issue 评论 #2 宣布验收并合并，随后关闭 Issue；评论 #3 只是关闭后的收尾。两个 Agent 有实际的实施与独立复验，但 Braid 对象承担的主要是单向方案交接、状态通知与验收记录。

实施 Agent 在首次 ready 后又继续工作：它把若干可点击 `div` 改为真实链接，重跑自检并再次标记 ready。这是有实质内容的自我修正，但会话记录未显示它是由 Issue Agent 提出的具体反馈触发；Issue 评论 #1 只是此前方案摘要。PR 上没有评论，因此没有在 PR 对象内的问答、审阅建议或修订协商。

## 定位证据（4 项）

1. `local_items` 的 `issue:1` 正文是预填交付指令；`pr:1` 正文约 10,277 字符，标题为“实现 BookStack 知识库系统（frontend+backend 全量交付）”，一次列出技术方案与验收判据。`native/000-…jsonl` 在 03:39:13 记录 `pr create --issue 1 --body-file .braid/pr-body.md`，03:39:54 创建 Issue 评论 #1，内容是“需求已分析完毕，已建立 PR #1 并激活实施 Agent”。
2. `local_comments` 仅有 Issue 评论 #1、#2、#3，均为可见的独立根线程；PR 评论数为 0，`reply_to`、`resolved_through`、`hide_reason` 均为空。#2 是“验收完成…予以接受并合并”的复验记录，#3 是“收尾确认…已完成并关闭”。对应 `native/004-…jsonl` 和 `native/010-…jsonl`。
3. `braid-state/turns/` 与 `native/002-…jsonl`、`native/006-…jsonl` 显示 PR Agent 收到的对象事件分别是关联/创建、Issue 评论 #1；它先在 03:55:10 ready `d74c507`，随后于 03:56–03:59 自行修改链接可访问性并在 04:00:09 再次 ready `7e579034`。没有针对问题的对象内回复或 Issue Agent 修订请求。
4. `native/004-…jsonl` 和 Issue 评论 #2 明确写验收对象为 `d74c507` 的归档副本；`local_merges.head_commit` 则为 `7e579034`，`merge_commit` 为 `e3fa1bd1`。Issue Agent 的复验与 PR Agent 的末次修正并行发生，最终合并提交晚于它所记录的受检提交。这里不能由该记录推断末次修正有错误，只能说验收证据没有绑定最终合并的精确 head。

## 反例与局限

这不是纯粹的空壳流程：Issue Agent 确实独立构建、启动并运行场景检查；PR Agent 也在首次 ready 后修正了可访问性。价值主要来自角色分工和复验，而非 Issue/PR 评论功能带来的协商。当前 SQLite 保留 `local_items.revision`（Issue 为 2、PR 为 4），但没有正文版本历史；原生日志中未见 `issue edit`、`pr edit` 或评论编辑命令，因此只能说**未观察到正文语义演化**，不能断言历史上绝无编辑。同理，当前三条评论均可见、无回复或 resolve；这不是对未保存历史的“从未”判断。

## 产品结论

此 run 支持用户所指的退化形态：根 Issue 接受预填需求，PR #1 承接一次性详案和实现，根 Issue 负责独立复验、合并与重复收尾。若产品目标是让 Braid 承载持续协商，单纯强制创建 Issue/PR 并没有在本例产生这种行为。更直接的改进点是：验收时将受检 commit 与可合并 head 绑定；head 在复验期间变化，就让验收结论失效或要求针对新 head 的明确确认。讨论功能是否需要额外引导，应以跨 run 的实际评论/修订需求判断，不能从本例单独推出强制更多评论会增加收益。
