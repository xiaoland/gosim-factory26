# 官网 PR 指派发生在实现前还是实现后

只读核对官网 GitHub `435b79927a47` 的 PR #8 与 Sheet `bd7ac1b232ba` 的 PR #1。对象与成员时序取 [`github.sqlite3`](../../../runs/official-collaboration-review/github.sqlite3)、[`sheet.sqlite3`](../../../runs/official-collaboration-review/sheet.sqlite3)；原生动作与 Git 来自两题 [`source-workspace.zip`](../../../runs/e20260928-completed-replay/github/source-workspace.zip)、[`source-workspace.zip`](../../../runs/e20260928-completed-replay/sheet/source-workspace.zip)。GitHub ZIP 的 `template/.factory26/20260927-080209-0b57147a/native/088-...jsonl` 为 Issue #7 首会话，`native/260-...jsonl` 为 PR #8 首会话；Git 对象在同包 `braid-state/origin.git`。本页不追踪全量代码行作者，也不把 PR 指派等同于独立实施。

## GitHub PR #8：Issue 会话先实现，PR 会话随后整合、修改并自检

| UTC 时点 | 可复核动作 | 意义 |
| --- | --- | --- |
| 10:51:02–05 | Issue #7 指派 @deepseek-10；Issue 原生首会话开始 | 其任务即 REQ-6-1、6-3-3/4、6-4/5/6 的评审与合并控制。 |
| 10:57:56–11:13:46 | Issue 首会话在 `issue-7/...` 工作树调用 `write`/`edit`：10:57 `backend/pulls.js`，10:58 `server.js`/`seed.js`，11:01 `PullDetail.tsx`，11:02 `SettingsBranches.tsx`，11:05 `check7.js`，11:12 `checks/issue7.spec.ts` 等；期间还启动服务、运行 `check7` 并修检查。 | **功能实现和检查编写在 PR 指派前已经实质发生。** 这是原生文件写入动作，不依赖作者署名或评论自述。 |
| 11:14:53 | 根在 Issue #7 评论 #123 看到在途代码，要求立即 push WIP/建 PR，指出其旧基线与刚合入的 PR 基础 `f52ade5` 冲突；应以 develop 详情页宿主为基准集成。 | PR 是已有实现与新基线的交接/集成入口，非实施的起点。 |
| 11:16:06 | `d00c0ba` WIP 快照相对 `7f22406` 已有 13 文件、约 2471 行新增；Git 提交署名 @deepseek-10，subject 写“published by root per hard checkpoint”。 | Git 提交与原生写入相互印证此前已有大量代码；**不能只凭署名推定谁执行了提交命令**。 |
| 11:16:20–28 | 根创建 PR #8 并指派 @deepseek-12；`pr:8` 的 Pi 首会话 11:16:27 开始，11:16:47 首先用 `git diff 7f22406 d00c0ba` 看先前快照。 | PR 成员拿到的是既有 WIP head。 |
| 11:22–12:56 | PR 原生会话随后修改 `backend/server.js`/`pulls.js`、`seed.js`、`PullDetail`/`pullShell`/`PullFiles`、检查和文档；11:27 有后端提交调用，12:56 形成最终 `3e61a4a`（以 `f52ade5` 为父，13 文件、约 2111 行新增/141 行删除）。根的 Issue #7 评论 #154 逐项指出读 API、路由、详情页宿主与文档冲突；#166 又说明根已接管集成并要求 Issue 原负责人暂停向旧分支推送。 | PR 阶段有**实质代码整合与修复**，不是仅挂名验收；但原 Issue 实现、根的集成干预和 PR 会话动作交织，不能称这次按“先 Issue 设计、后 PR 独立实施”完成。最终提交用泛化作者名，不能逐行归属。 |
| 13:04–13:16 | PR #8 评论 #240 由 @deepseek-12 报告在 `3e61a4a` 上 `check7.js 84/84`、Playwright 15/15、三套回归与 build；13:06:38 由 `writer_node=pr:8` 合并为 `2accac1`，#248 核对 merge 双亲与树一致。 | **独立 PR 成员参与最终候选检查和合并**有证据；因其也修改最终代码，#240 是该成员的自检，不宜称与最终实现完全独立的第三方验收。根在 Issue #7 #243 采用其证据并关闭。 |

该链更准确的名称是“Issue 已实现的 WIP 在依赖变化后被 PR/根接手整合和复验”。它仍有价值：根的 #154 指出 `reviews` 字段、重复 handler、路由冲突，PR 阶段实际将功能嫁接到 PR 基础宿主并取得对应 head 的检查。但它不证明 Factory 期望的设计/实施分工已经采用；若把 PR #8 当完整正例，会遗漏前 19 分钟的 Issue 源码写入和根的接管。

## Sheet PR #1：独立整合者的正例，职责不是功能实现

Sheet PR #1 在 08:35:04 创建，`head_ref=develop`、`base_ref=main`，正文写明“各子任务成果合入 develop 后在本 PR 执行覆盖全部需求的自动化验收”。它于 10:15:58 指派 @glm-7；根评论 #48 明确等待 #4/#5/#6 入 develop、在最终候选上检查。@glm-7 从 #56 的基线验收起，随 develop 前进在 #97/#105/#137/#170 留下多个候选的回归与最终证据，和根及功能负责人在 #62/#108/#119/#124 等处往返讨论；15:02:55 以 `writer_node=pr:1` 合并 `develop@8152b05` 到 `main@4023362`。

这足以证明 Braid 能把**集成与最终验收**交给独立负责人并由根消费，对并行成果收束有实际作用。它不是 Sheet 各功能由独立 PR 成员从设计实施的证据：PR #1 本来就是跨功能的 develop→main 整合对象，不能拿它补多数 feature PR 未指派的缺口。[Issue/PR 边界](issue-pr-session-boundary.md)已列 Sheet PR #2 等功能由 Issue 会话直接创建/合并的反例。

## 对 09 判据的影响

09 的新 Factory 指引已明确“进入实施前创建并指派 PR，PR 独立成员承接实现”，所以**文字覆盖这个时间断点**；官网旧行为以及目前继承旧半成品的事后 PR 不能验收新指引已生效。今后验证应看同一功能的首个源码写入/提交是否晚于 PR 独立成员建立及设计交接，并看其对原 Issue 的方案/验收依据有实际引用；对接已有 WIP 的 PR，应如实标为整合/修复/复核，不能因存在 assignee 自动改称“PR 承担了实现”。不要求撤销根整合能力，也不要求所有 PR 都有相同职责。
