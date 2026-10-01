# 正确使用 Braid：决策摘要

2026-09-30。本研究把 Braid 当作 GitHub 式软件协作控制面，而不是聊天记录、第二份仓库或“给模型塞更多上下文”的容器。

## 日常应该怎么用

1. **Issue 说清当前义务。** description 只维护目标、范围、当前合同入口、完成判据、未决责任和依赖；不持续镜像 WIP commit、长日志、整段讨论史或其它对象的全部状态。
2. **PR 说清当前候选。** description 绑定候选 head、实际变化、解决的行为、证据入口、已知限制和需要审阅的具体问题；不复制需求全文，也不把“ready”当成审阅通过。
3. **comment 只传一个增量。** 写“新事实或决定 → 影响 → 下一行动 → 精确来源”。需要跨任务长期复用的已采纳合同上移稳定文档；改变当前义务的决定同步到 description，但不复制完整讨论。
4. **一个 thread 只有一个可独立结束的问题。** owner、交付物或关闭条件变了就另开 root 并互链。不要把长期合同、短期回执、测试反例和批准混在同一串。
5. **元数据负责路由，不负责证明。** assignee 表示当前推进者；status 表示生命周期；parent/PR link 表示结构或背景；subscribe 表示持续获知。它们都不证明理解、承接、语义覆盖或验收通过。Braid 当前本地实现没有通用 typed dependency、labels 或 milestones；依赖仍须用一句话说明生产者、消费者、产物与满足条件。
6. **先读目标，再按需展开。** 默认读触发 comment、当前对象 description/assignee/status/直接关系，再读本次相关 diff 或合同段落；只有遇到歧义、反例或来源核实时才展开整 thread、linked object、原始证据和历史。不要每轮复读整套文档。
7. **状态动作成功后才宣告。** merged、closed、delivered、consumed、reviewed 是不同事实。先取得真实回执/读回，再写完成结论；终态前先安置仍需他人处理的结果。

## 放在哪里

| 信息 | 权威载体 | 控制面中保留什么 |
| --- | --- | --- |
| 可执行行为、接口 | 源码及其 Git 版本 | Issue/PR 给精确 commit/path/symbol 与为何相关 |
| 跨任务稳定合同 | 版本化设计文档 | 决定、适用版本、受影响对象和入口 |
| 当前工作义务 | Issue description | 目标、完成门、owner、依赖、未决 |
| 当前候选 | PR description | head、变化、证据、限制、审阅请求 |
| 一次提问/反例/裁决/交接 | comment/thread | 增量、影响、下一动作、来源 |
| 调查、授权、计划、恢复点 | task packet | 阶段真相和证据导航，不镜像实时 PR 状态 |
| 完整日志、DB、截图、运行身份 | 原始证据 | 结论、版本、可复核入口 |

目标、范围变化、未决责任、审阅结论、替代关系和关闭理由不能只藏在文件、已隐藏评论或已折叠历史里。相反，大段源码、完整 schema、完整日志和历史讨论不应重复内联；链接时必须同时写明“为什么相关、关键结论、谁下一步做什么”。

## 生命周期底线

- `hide`：只处理明确重复、损坏、整体失效的单条；保留原因和替代 ID。它不能追回已投递通知，也不等于问题解决。
- `resolve`：当前工作树只接受 root ID，并把执行时整条 thread 的最大 comment ID 记作 cutoff；折叠的是整段历史前缀，新回复仍可见。resolve 前必须检查整串，确认长期决定已有当前入口、未决项已拆出。混合 thread 宁可保持可见。
- 关系：建立时写清责任语义；关系失效时移除或更新并给替代入口。不要让两处 description 同时维护同一动态状态。
- 通知：不要求每条 ACK。只有新事实、决定、阻塞或明确行动才回应；“收到”“仍无变化”和重复镜像不应形成循环。

## 为什么不是“统一写短一点”

两个真实任务确有很大的维护面：GitHub 终态有 352 条评论、182 次 context reset；Sheet 有 589 条评论、359 次 reset，最大 PR description 35,643 字符。但这些数字只证明存储、检索和维护负担可观察，不能证明长度导致失分，也不能把 token 当成知识。

真正反复出现的问题是**生命周期不同的事实混在同一载体**：当前合同、历史理由、动态 head、原始证据、外部状态和无动作回执互相镜像。反例同样存在：Sheet 的一次 167,672 字符输入中，Agent 既正确停止了一次重复催问，也仍需重新定位旧 thread。因此规范应控制权威、关闭条件和读取路径，而不是设置全局字数上限。

## 当前 Braid 语义边界

- 当前 dirty 工作树基于 `sources/braid` HEAD `0712a58d…`，整合 binary SHA-256 为 `e2f58d…`；它与 I11 历史运行不同。
- 当前只有有效 description 变化触发本项上下文重建；OPEN 关联 Issue 的 description 变化才跨面触发 PR。comment edit/hide/resolve、title、parent、PR link/unlink 走增量通知，不重建，并排除操作者。
- 当前 PR 默认投影包含自身 description/讨论和 OPEN 关联 Issue 的 description，不包含关联 Issue 评论；Issue 只列直接 parent/sub-issues/PR references，不递归注入祖先正文。
- 投影按 Full → CommentIndex → References 降档；References 截短 description、去掉评论并给读取命令。预算是粗估且严格低于模型窗口 20%，不是语义完整性保证。
- I13 的“旧根提醒先 hide 再建新提醒”仍只是计划，尚未出现在当前源码；不能把它写成已实现能力。

完整协议见 [field-guide.md](field-guide.md)，真实改写见 [cases.md](cases.md)，证据、研究边界和职责分层见 [report.md](report.md)。
