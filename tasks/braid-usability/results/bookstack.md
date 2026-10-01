# BookStack：旧 Lite 运行的评分与 Braid 工作项取证

本报告只覆盖 `pi-team-mixed-arc-bench-lite-bookstack-8a977ba177`。远端根目录为 `/home/yyh/Development/factory26/runs/braid-usability-lite/20260924/runs/pi-team-mixed-arc-bench-lite-bookstack-8a977ba177`，以下路径均相对该目录。该 run 使用 boundary-fix 前的旧 `pi-team-mixed.zip`，文件原始 SHA-256 为 `8b7c37b7d3097a0d12e14bb4c66170743d7f9d41e3bd443f227b3726073f6b9d`。`run.json` 的 `inputs.agent.sha256=7028ac0aa4b530aac784690ea0fd9c07abebe4b326ec931a00608c927b5b4d2a` 是 `scripts/local_experiment.py:42-52` 对文件名、NUL 分隔符和 ZIP 字节计算的复合输入摘要；两者对应同一文件，不是制品身份差异。本 run 不能作为新边界的验收。

## 官方结果与五项失败

`workspace/experiment-result.json` 记录 generation `completed`、exit code 0；evaluation `completed`，29/34 通过、5 失败、test pass rate 85.3%，`score=null`。冻结与受评源码的 SHA-256 同为 `d301cb6d7d588a6f2ac11fcbc9012f4aaff37886f5cad5b745869e5d3dc004af`。`workspace/official-evaluation/template/.arc/playwright-report.json` 记录五项均在 10 秒测试超时，`execution.debug.log:109-271` 可对应定位；Runner 非零退出来自这些失败，不能记作生成设施故障。

| 官方失败 | 报告直接观测 | 冻结应用中可支持的解释及界限 |
| --- | --- | --- |
| REQ-4.3.1 Create Shelf | 等待访问名匹配 `Shelf 4.3.1` 的 **button** 超时。 | `frontend/src/pages/ShelvesPage.jsx:25-30` 把书架名称渲染为 `Link`，不是 button；`ShelfFormPage.jsx:38-41` 创建后返回书架列表。可确定期望 button 与该列表的控件角色不符，不能仅据此断言 POST 创建失败。 |
| REQ-4.5.1 Save Shelf Edits | `Edit shelf form` 内 placeholder `tag1, tag2` 的输入框数量始终为 0。 | `backend/seed.js:41` 为该书架预置非空标签；`ShelfFormPage.jsx:21-25` 载入标签；`TagField.jsx:8,16,20-28` 在非空时初始展开、点击按钮反而折叠。若官方流程点击 `Shelf Tags` 以展开，这会解释输入框消失；报告未保存此前点击步骤，因此该因果只属强假设。 |
| REQ-5.4.1 Save Book Edits | `Edit book form` 内同一 placeholder 输入框数量始终为 0。 | `backend/seed.js:63` 为该书预置非空标签，`BookFormPage.jsx:99` 复用 `TagField`；同样存在“初始展开、再点则关闭”的机制。报告无法区分 form 未呈现与子输入被关闭。 |
| REQ-6.1.3 Delete Draft | 等待访问名精确 `Edit` 的 button 超时。 | `backend/seed.js:90-97` 的 `Draft 6.1.3` 是草稿；`BookDetailPage.jsx:80-85` 将草稿页直接链接到 `/page/:id/edit`。编辑器 `PageEditorPage.jsx:142-149` 有 `Delete Draft`，但无 `Edit`；阅读页 `PageViewPage.jsx:50-59` 才有 `Edit`。若该路径从图书条目进入草稿，控件路径与期望不符；报告未保留之前导航，不能完全确认。 |
| REQ-9.1 Quick Navigation from Recently Updated | 等待 `Page Updated 9.1` 的 **button** 超时。 | `Home.jsx:78-87` 的最近更新项为 `Link`，后端 `server.js:543-547` 提供非草稿最近更新页。可确定该区域的名称项不是 button；是否同时因数据未更新而缺项，现有报告不能判定。 |

这五项解释来自报告错误与受评源码的对照，未读取外部测试源码，也未重跑应用。根 Issue 自编浏览器走查后来声称 36/36 通过，只证明它的检查路径通过，不能覆盖官方报告中的角色/标签交互差异。

## Braid 工作流与信息作用

生成态数据库 `workspace/official-generation/template/.factory26/20260924-075037-acb81a15/braid-state/braid.sqlite3` 只读查询得到：Issue #1、关联 PR #1、可见评论 #1 各一，PR 已合并，最终合并提交 `5c68ecac2bef05a4429dde18f4a8e6595e439c07`。Issue #1 的正文仍是宿主预填需求入口；Issue Agent 在原生 `native/000-...jsonl` 07:50–07:56 阅读需求与参考图，随后用 `braid pr create --issue 1 ... --assignee glm` 写入详细 PR description，包含技术选型、种子数据、控件可访问名和自检要求。应用代码由 PR 工作树的初版提交 `53370b5` 实施；在创建 PR 前的根 Issue 原生片段未见应用代码写入。设计/实施在工作树和动作上分开，但只有同一 `@glm` 成员承担两项工作；不能推断多模型或多成员协作收益。

PR 首次 ready 于 08:37，根 Issue Agent 09:23 开始构建、启动并以自编浏览器脚本走查；其 `native/000-...jsonl` 09:41 的工具结果声称 35/36 通过，09:47 把章节路由缺失和未登录页重复 `Login` 链接写成 PR 评论 #1，要求修复。PR Agent 的 `native/004-...jsonl` 09:48 实际改 `frontend/src/App.jsx` 与 `frontend/src/pages/Home.jsx`、重新构建，并于 09:49 提交 `5e1cc48`（两文件、1 行新增、6 行删除）。这条评论改变了实现，属于实质反馈而非形式交接。

同一修复会话随后执行 `braid comment resolve 1 && braid pr ready 1`：对象事件确认评论 #1 在 09:49:12 resolved，紧接着 shell 返回“writer turn is stale, fenced, or no longer running”，所以这一次 `ready` 未完成。Braid 用当前 Context 建立后续 PR 会话（`native/006-...jsonl`），该会话读取已解决的评论与提交，完成构建/启动冒烟并在 09:51 再次 `ready`，记录 `ready_commit=5e1cc48`。根 Issue 09:59 的自编回归声称 36/36，10:02 合并 PR 并关闭 Issue。受检的是修复后的 `5e1cc48`，合并提交 `5c68eca` 包含该提交；但官方仍有五项失败，不能把“本地 36/36”写成最终应用通过官方验收。

原生对象命令无需显式 `--state` 或 writer-turn；评论 #1 的 writer 是 Issue group，修复与 resolve 的 writer 是 PR group，合并 writer 是 `issue:1`，与工作项身份对应。评论 resolve 后的新 Context 被实际读取并用于接续 `ready`，说明整理和重建在此处有作用。未见 hide、多 ID 整理、reply 或子 Issue；这些场景标为未观察。现存数据库没有正文历史版本，不能从 PR revision=4 断言 description 曾怎样演化。根 Issue 长时间以 `sleep`/`braid status` 等待 PR ready，信息价值主要发生在一次具体验收反馈及其返工，不应以轮询或单条评论数量衡量。

## 判定边界

该 run 证明了对象身份、Issue/PR 工作树职责、评论反馈导致代码变化，以及 context reset 后接续工作；也证明 Agent 自己的浏览器检查未覆盖官方五处失败。五项失败的直接定位可靠，精确测试交互顺序和评分规则未从允许证据中完整重建，故上述机制解释按证据强度区分。此旧 run 不能证明后续 boundary-fix 的 `quiescent/blocked` 与 ref 冻结行为。
