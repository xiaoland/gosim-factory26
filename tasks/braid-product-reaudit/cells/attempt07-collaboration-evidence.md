# attempt-07 协作交接与验收状态复核

只读截面至 2026-09-28 05:53 UTC。对象是 WSL `runs/e20260928-02-deepseek-direct/attempt-07/generation/runs/` 的 GitHub `20260928-030347-78b10c07`、Sheet `20260928-025746-66feadac`。07 控制器约 05:27:49 启动，新 Pi 主会话约 05:32–05:33 开始；旧 `recovery-source-native` 和 06 复制材料不当作新行为。以 Braid `braid.sqlite3` 的事件/收件/重建/PR 状态、`work/native-homes` 的实际 user/tool/decision、生成 Git 提交和已有检查结果构成链条；未新跑应用或测试。历史对照是[共享契约因果](../../experiment-infrastructure/cells/shared-contract-braid-causality.md)与[06 运行诊断](../../experiment-infrastructure/cells/live-deep-diagnosis.md)，不是同条件 A/B 实验。

## GitHub：共享会话缺陷得到纠偏，重复补丁最终从 PR 移除

07 #6 处理 REQ-4 时用临时 DATA_DIR 实测 `POST /api/auth/login` 200 且返回 `sid`，紧接着 `GET /api/auth/me` 401；原生记录 05:39:29 定位 `backend/src/sessions.js` 的查询只选 `s.id AS session_id, u.*`，过期判断却读取未选的 `expires_at`，会把已建会话立即删除。#6 在父 Issue #1 comment #20（05:39:58）说明复现、共享影响及自己的修复 commit `8d09c3b`。Braid `local_comment_delivery` 对 #20 给 `deepseek-3` 和 `glm-1` 都记 `delivered`；这只是收件状态，额外有 #3 原生 user 输入于 05:40:04 引用 comment #20、05:40:06 `braid comment view 20 --thread`、05:40:15 准确说明两份修法差异；根成员也于 05:40:37 收到、05:40:43 读、05:40:58 识别重复补丁。

#3 当时的 REQ-1 PR #2 已有同义修复。它先在 comment #21（05:41:40）裁定采用 #6 形态，原生记录 05:40:33–05:40:45 显示它把 `sessions.js` 对齐、跑 backend/E2E 并 push。随后共享基础负责人经 PR #3 把修复与种子 diff 统计修正先合入 `develop`（`038e059`，Issue #2 comment #22）；#3 不再坚持自己分支的重复修复，而在 05:41:59 rebase 到该 head、从 PR #2 移掉 `sessions.js`，新 head `a8e2dd4`，05:42:48 报告 E2E 72/72、backend 18/18，comment #23/#24 交接。#6 收到 #24，05:43:21 读取，05:43:25–05:43:45 fetch/rebase 并消除自己分支的 `sessions.js` 差异。只读 Git 校验：`038e059:backend/src/sessions.js` 实有 `s.expires_at AS session_expires_at`，`git diff --name-only 038e059 a8e2dd4` 不含 `sessions.js`。后续根成员在 `6419fb8` 独立复跑、以 `--match-head-commit` 合并 PR #2 至 `354b198`（Issue #3 comment #29）；其检查结果属根成员报告，本次未重跑。

这是一条**已送达→确实读取→改变代码归属/重基→以具体 head 复验**的正例，比“评论变多”更能说明协作起作用。也暴露实际成本：#3/#6/#5 对同一个 shared `sessions.js` 有过平行局部修补，靠后续 PR #3 与两次 rebase 才收敛。不能因最终没有重复 diff 就说初期没有重复工作。旧 Sheet 2026-09-27 案例中裁决虽已读却采用旧形状、后续运行中纠偏未及时进入；这次 GitHub 条件不同，但至少证实 07 的普通更新能在仍工作的父会话中形成新 user 输入和代码动作。

## Sheet：CSV 冲突裁决被执行，随后出现 PR/Issue 编号混淆

旧窗 05:10:43 Issue #3 comment #55 已给 CSV 负责人一个清楚的合并门槛：PR #3 共享基础跟进先入 `develop` (`61b51ee`)，CSV PR #4 与其在 `checks/run.sh`、`checks/playwright.config.ts`、`frontend/src/api.ts` 冲突；须 rebase、保留两方意图、在同一新 head 重跑完整 checks。#55 对 `deepseek-3` 收件为 `delivered`。07 新主会话 05:33:24 收到 Issue #3 内容，05:33:28 主动 `braid comment view 55 --thread`，05:33:33–05:33:39 确认工作树和远端已有 `a012447`、核对三处冲突合成。这里 rebase 提交本身可能在 07 接续前已完成，**不能把 `a012447` 的所有编辑归功于 07**；07 可归因的是重新核对和验证新 head、更新 PR/交接。

#3 于 05:40:16 原生记录得到 `checks/run.sh` **14 passed、exit 0**，05:41:08 在 Issue #3 comment #62 写明 head `a012447`、三文件处理、frontend 6/6、backend 8/8、tsc 和 CSV 3/3，PR #4 comment #63 也标明按该 head 复核。只读 Git 校验显示 `a012447` 的 `checks/run.sh` 有 CSV suite，`playwright.config.ts` 有 csv project，`frontend/src/api.ts` 有 importCsv；PR #4 对 `develop` 的 merge commit 为 `757e557`。PR 负责人 `glm-9` 在 07 新主会话 05:33:32 读取 PR #4，05:33:41–05:33:56 核对 rebase head 和 diff，之后独立运行检查；05:48:30 记录重跑 14/14/exit 0，05:49:12 comment #71 发表复核，05:49:15 准备用 `--match-head-commit a012447` 合并时发现 PR 已由另一执行合入，随后核查 `a012447` 已在 `origin/develop`。这证明裁决/证据被阅读、代码交叠被保留、对应 head 经过两位成员检查并合并；不把 PR 审阅者的晚到合并尝试另算交付。

验收边界仍有一处新的错误。CSV 负责人 comment #66 明确写“待 **Issue #7 的 Create filter** 发布到 develop 后再补浏览器级‘筛选隐藏行仍导出’回归”，Issue #7 实际仍是排序/筛选/校验/透视工作。可是 PR 审阅者在 05:50:10 的原生思考把“#7 落地后”解释成 **PR #7 已合并**，进而 Issue #3 comment #72（05:50:20）称“PR #7 已合入 develop——现在可以补”该回归。Braid SQLite 证实 PR #7 的标题是“检查套件可靠性：超时上限、run 私有运行目录、服务器端口归属校验”，merge `0539c62`，不是筛选功能；同一时段根 Issue #1 comment #70 仍列 Issue #7 为进行中。#72 对 `deepseek-3` 收件为 `queued`，截面内未见它因此写出错误浏览器检查，也未见最终验收声称该场景通过。因此这是**依赖门槛解释错误**，尚不能说造成产品失败；最小纠偏是把遗留检查绑到筛选实现的实际 PR/merge commit 和可运行候选，而非只写“#7”。

PR #4 复核首次 14 项中有 5 项失败、第二次 14/14 通过。审阅者把第一次归因于共享机器上种子 JSON/日志消失，并指出 `run.sh` watchdog 与 cleanup 竞态，有服务逃逸清理；Issue #2 comment #73 已转给检查套件负责人。此次只读证据能证明两次实际结果和后续交接，不能凭复核者的解释或目录 mtime 独立证明“外部删除”唯一原因；最终验收仍须以隔离数据目录及真实默认入口结果为准。

## 通知和重建：能区分输入类型，尚不能宣称总体开销下降

07 启动时 GitHub 5、Sheet 6 个已有 Braid 成员在约 05:32–05:33 各有一次 `context_resets`，属于跨冻结运行接续；不是普通评论导致的重复重建。之后至本截面 GitHub 未见新的 `context_resets`，虽有 #20/#21/#24 等普通评论送达并在同一主会话形成新 user 输入，说明该链不必因普通通知重建才能被读到。Sheet 另有 3 次中途 reset：PR #4 负责人的一次聚合了 `pr #4 title/body 已修改` 和跨 surface 的 Issue #3 body 编辑；Issue #3 成员两次因自己的 Issue #3 title/body 修改 reset。`context_reset_events` 均为 `kind:invalidate`，非普通 comment。#3 05:47 新会话实际识别一次是自己改正文触发，继续检查状态，存在自我通知/重建成本；不能把它称为纯评论噪声已消除。

`wake_batches` 在 07 窗口两题都有非空批次（本截面 GitHub 27、Sheet 22），但批次数/事件数既不等于模型请求，也不等于信息价值。旧 Sheet 的 63 条引用与晚到 #109/#118 是另一冻结条件，07 未做等负载/等任务对照；本报告只下“本次选定交接链送达且被行动消费”“普通评论未触发上述重建”“正文编辑仍会重建”的结论，不宣称通知量、token 或总耗时已下降。后续判断应用是否满足初始种子和最终验收，仍须以原始 requirements 的给定初始状态、合并候选的实际启动与行为检查核对；Issue/PR 评论里的 PASS 不能代替这一步。
