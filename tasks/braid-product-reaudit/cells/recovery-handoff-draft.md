# 09 接续的三条事实交接草稿（未投递）

本页供主线审阅是否需要在恢复后用宿主诊断评论提醒现有成员。原草稿以 08 停止归档为截面；**2026-09-28 08:44 UTC 已只读重看 09 停止工作区**，最新结论和可直接使用的正文文件列在下一节。这里只整理事实和重新判断的范围，不改对象状态、指派、数据库或生成应用，也不代表宿主判定实现完成。来源见[恢复点复核](recovery-point-review.md)。

## 09 停止截面与待审阅正文

- GitHub Issue #9 仍 `OPEN`，评论 #61 仍是 PR #12/head `752a084` 的交付入口；PR #12 仍 `OPEN` 且现任 assignee 为空，`develop=afee849`。短正文：[handoff-09-github-pr12.txt](handoff-09-github-pr12.txt)，目标是 Issue #9 回复 #61。
- Sheet Issue #7 仍 `CLOSED`，评论 #199 的通过口径未改；PR #19 仍 `OPEN`，已有负责人 @glm-16，head 更新为 `753f334`，`develop=7f4216e`。PR #19 评论 #207 已由 #7 成员独立复现旧实现 `200 !== 400`、新候选 10/10 与 84 checks 通过，并认为可合并；**但 PR 仍未进入 develop**。短正文：[handoff-09-sheet-pr19.txt](handoff-09-sheet-pr19.txt)，目标是 Issue #7 回复 #199，提醒最终候选/关闭口径，不重复要求重跑全部检查。
- GitHub PR #5 的外部合入事实已经在 Issue #6 #46 与 PR close reason 说明，本轮**不准备投递**。

两份 bodyfile 已逐字节复制到 WSL `attempt-09/host-diagnostic-comments/`（不在生成工作区内），SHA256 分别为 `eae1abd822ea419d7b1aa93678b0d8f45ad16910ac2fae7b54f0be172c087321`、`ed5271a1a205e2a9e0344f1369a49c07c412e8890c5ff55eb19b01d5888e96b8`。GitHub 正文只写历史成员名 `glm-11`，不使用 @ 触发额外定向通知。本文其余表格保留 08 原始草稿的证据来源，不应用其中旧 head 覆盖 09 核对。

| 事实 | 已有最合适的讨论位置 | 可供审阅的短正文 |
| --- | --- | --- |
| GitHub PR #5 的 Braid 状态 `CLOSED`，代码实际已入 `develop` | Issue #6 顶层评论 **#46**，根负责人已在此记录 PR #5 独立复验、Git 合入与关闭；PR #5 本身无评论。该事实已有 close reason 与 #46，若恢复后的成员没有误读，**无需再发一条重复通知**。若需纠偏，回复 #46；不要新建平行顶层讨论。 | `宿主只读核对：PR #5 的 Braid 对象仍是 CLOSED；其 head 3325873 已由双亲 merge 2d29c4d 纳入 develop，08 冻结 develop afee849 仍包含该 head。请区分“代码已整合”与“Braid 未记录为 MERGED”，以当前 Git 树和 Issue #6 的验收证据判断 REQ-4；不要仅凭 CLOSED 重新实现或把对象状态当作新的合并证据。` |
| Sheet Issue #7 的完成口径与新 PR #19 冲突 | Issue #7 顶层评论 **#199** 是 `REQ5_ALL_PASS` 后关闭本项的原声明。回复这条比在根 Issue 重复完整验收日志更直接；#7 已 CLOSED，若希望当前根也收到，发布前核实 @根成员的现任身份。PR #19 尚无评论。 | `宿主只读核对：Issue #7 comment #199 在 develop 6bb8192 报告 REQ5_ALL_PASS 并关闭；其后 08:12 创建的 PR #19（head b89df03）专门补 REQ-5-2-1 的范围移动写校验，08 冻结时仍 OPEN，且未在 develop 7f4216e。请按需求与当前代码重新判断四种写路径的覆盖和 #7 的完成口径，在最终候选上核对 #19；此前 #199 不能单独证明 range move API 已完整拒绝非法整单。` |
| GitHub PR #12 已交付 head，但独立 PR 责任未形成 | Issue #9 顶层评论 **#61** 是作者的交付、自检与 head 说明；PR #12 本身无评论。回复 #61，把复核要求贴在交接处。根 Issue #1 的进展串 #58/#62 已收到摘要，通常无须再贴一份。 | `宿主只读核对：Issue #9 comment #61 交付 PR #12/head 752a084（基于 afee849）及作者自检。08 冻结 PR #12 为 OPEN、无现任 assignee；07:49:20 的 @glm-11 指派四秒后被移除，不能视为独立复核已完成。请先查当前指派与已有结果，再决定由谁复核既有 head、Issue #9 的设计和最终候选；不要因这条自检直接合并，也无需重做已交付实现。` |

三个句子的 commit/状态锚点来自 08 `braid-state/braid.sqlite3`、`origin.git`：GitHub `pi-braid--hackathon--github-97914b9e3158cf`（Braid run `20260928-030347-78b10c07`）、Sheet `pi-braid--hackathon--sheet-d478f7dc8ff84f`（Braid run `20260928-025746-66feadac`）；09 `restore-point-facts.json` 与 `recovery-package-verification.json` 确认其源。Sheet PR #19 的冻结 branch `b89df03` 在 `backend/src/middleware/validationGuard.ts` 增加 `/move` 入口及 `checks/req3-move-api.mjs` 检查，说明新缺口不只是空标题；仍须由执行成员在当前 develop 和需求下验证正确性。GitHub PR #12 无现任 assignee 只对 08 冻结成立，不推断 09 现在仍无负责人。

## 已核实的宿主 CLI 入口

当前 `sources/braid/src/cli/mod.rs` 与 09 构建快照 `attempt-09/braid-build-final-v2/src/cli/mod.rs` 均登记全局参数 `--state <braid-state目录> --external`；写操作在非 Agent 环境必须有 `--external` 或有效 `--writer-turn`，本草稿只讨论宿主 `--external`。评论子命令接受 `issue comment <issue号> --reply-to <全局comment_id> --body-file <UTF-8文件>`；`BodyArgs` 还支持 `--body`，但长中文正文用文件可保留换行。示意语法（**未执行**）：

```text
braid --state <GitHub 09 的 braid-state 目录> --external issue comment 6 --reply-to 46 --body-file <审阅后的正文文件>
braid --state <Sheet 09 的 braid-state 目录> --external issue comment 7 --reply-to 199 --body-file <审阅后的正文文件>
braid --state <GitHub 09 的 braid-state 目录> --external issue comment 9 --reply-to 61 --body-file <审阅后的正文文件>
```

`comment_reply` 会校验 reply 属于同一工作项；评论写入还要求 Braid `local_run` 未 sealed。关闭的 Issue 仍可评论，但“成功写入”不等于现任根一定会被唤醒；按当前订阅/线程参与者与 @ 投递规则重新确认收件。若主线选择只发一条 GitHub 根诊断，可回复根 Issue #1 的进展串 #58/#59，合并 PR #5 与 #12 两个短事实；这样减少通知但远离各自原交接处。若主线选择零评论，09 新成员仍可从现有 Issue #6 #46、Issue #9 #61、Sheet #7 #199 及 PR/提交自行复核，本草稿不构成必须投递的决定。
