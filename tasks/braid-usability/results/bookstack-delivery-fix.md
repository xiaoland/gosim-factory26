# 临时修复版 BookStack：交付成功，独立评测 23/34

本报告只分析 `pi-team-mixed-arc-bench-lite-bookstack-58b12caa6b`。生成 `completed`、Braid 交付提交 `9beb0fbe38a953d374357d890e198c42f228ad73`；冻结与评测应用源码 SHA-256 均为 `cabf34ad94469c597193e3262c32d1112f0ebe431f8bd9cb772a7627a8686df8`。官方本地 Runner 的 noop 评测完成，Playwright **23 passed / 11 failed / 34 total，67.6%**。`score=null` 是 noop 阶段没有 Meter；Runner exit 1 对应失败断言，并非生成或设施失败。未重跑、修改应用或读取评测测试源码。`run.json` 的 `inputs.agent.sha256` 是文件名、NUL 与文件字节的复合摘要，不应当作 ZIP 文件本身的 SHA-256。

## 十一项失败的因果定位

| 项目 | 可观察的失败点与冻结应用原因 |
| --- | --- |
| REQ-4.2.1、REQ-5.6.1、REQ-6.1.2、REQ-7.1、REQ-7.2、REQ-8.2、REQ-9.1：7 项 | 交互在进入目标书架或书籍时停止：报告中的定位器等待相应名称的 `button`，失败快照中目标却是可见的 `link`，例如 `Shelf 4.2.1`、`Book 6.1.2`。冻结应用的列表页把对象名称渲染为 React Router `Link`，故这七项未触达各自后续的详情、草稿、最近浏览、收藏或最近更新断言。可判定为实际入口控件角色与本轮定位方式不合，不能据此推断后续功能均坏。 |
| REQ-4.3.1：1 项 | 创建后等待 `Shelf Created 4.3.1` 的 heading 超时；失败快照中同名书架已经是列表里的 `link`。`ShelfForm.jsx` 创建成功后跳转 `/shelves`，而非新书架详情。因此写入有可见证据，失败来自保存后的页面落点与断言不同。PR 正文也明确写了“保存→`/shelves`”，根验收未纠正该决策。 |
| REQ-4.5.1、REQ-5.4.1：2 项 | 编辑表单中点击 `Shelf Tags` / `Book Tags` 后，定位器找不到 placeholder 为 `tag1, tag2` 的输入框。`ShelfForm.jsx` 和 `BookForm.jsx` 传 `initiallyOpen={isEdit}`；`TagsField.jsx` 点击切换开合，故编辑页初始展开，评测点击后反而关闭并移除输入框。失败止于填写标签前。 |
| REQ-6.1.3：1 项 | 评测到达 `Book 6.1.3` 详情时等不到 `Draft 6.1.3` 按钮；快照显示未登录的 `Login` 链接及“无章节或页面”。`seed.js` 确实创建同名草稿，但 owner 是种子用户；`server.js` 的 `pageVisibleTo` 仅让草稿 owner 看见，匿名身份在书籍 API 中被过滤。此处的种子身份与匿名评测场景冲突，不能据此断言草稿删除确认流程本身失效。 |

失败集中在交互契约与种子可见性。PR 的 61 项 API 自检和根成员的 49 项 API 冒烟、JSX 静态核查没有覆盖上述浏览器实际路径；它们是运行者的自检声明，不能替代本轮 Playwright 结果。现有证据不支持把 11 项失败归因于模型连接、Runner 启动或 Braid 交付门槛。

## Braid 在本 run 的实际作用

根 Issue #1 由 `@glm` 负责。根成员先形成详细 PR #1 正文，列出架构、页面可访问性、种子数据和验收要求，并在 09:23:10 UTC **显式指派**给 `@glm`；这里是同一 profile 的不同工作项、会话与工作树，不是不同模型成员的协商。根初始会话未写应用文件；PR 会话实现并提交代码，在 PR 正文追加构建、API 与渲染自检，正文最终 revision 4。根成员随后在独立工作树做构建、API 冒烟与静态核查，于 10:43:46 在 PR 留下一条“独立复验、接受合并”的评论，10:43:55 合并；之后在根 Issue 留交付说明，以自然语言验收理由关闭根 Issue。Braid 状态最终为根 Issue `CLOSED`、PR #1 `MERGED`、交付 `completed`。

这说明工作项确实承载了实施计划、显式指派、独立验收和最终交付决定，比仅将根 Issue 当作流水线入口更有结构。但评论是验收通知，未见作者回复或据评论修改实现；没有持续的方案协商。PR 验收评论 #1 后来被 `resolve`，随后原生会话以 `--thread --include-hidden` 查看时标为 resolved history；没有观察到 hide 或 reply。此处 resolve 整理了已结束的验收记录，未观察到其改变实现决策。根成员接受的 PR 正文明确指定创建书架后回列表、将种子草稿归属种子用户；这两处决定直接对应评测失败，说明信息被记录和接受，不等于浏览器交互已验证。

## 证据定位与界限

只读证据副本位于 `/Volumes/WorkSSD/Development/factory26/runs/braid-usability-implementation/evidence/bookstack-delivery-fix/`，对应 WSL 原 run 为 `/home/yyh/Development/factory26/runs/braid-usability-lite/20260924/delivery-fix/runs/pi-team-mixed-arc-bench-lite-bookstack-58b12caa6b/`。状态与来源见副本 `run.json`、`workspace/experiment-result.json`、生成目录 `.factory26/20260924-090427-f0d5e71e/braid-state/{result,status}.json`；11 项直接失败和页面快照见 `workspace/official-evaluation/template/.arc/playwright-report.json` 与 `workspace/official-evaluation/tests/test-results/*/error-context.md`。相应应用原因见冻结 `frontend/src/pages/{Shelves,Books,ShelfForm,BookForm,BookDetail}.jsx`、`frontend/src/components/TagsField.jsx`、`backend/src/{seed,server}.js`。Braid 对象及评论见 `braid-state/braid.sqlite3` 的 `local_items`、`local_comments`、`assignments`，操作顺序见同级 `native/{000,002,004,006,008,010,012}*.jsonl` 与 `manifest.json`。副本不含评测测试源码。

本报告只给已触达断言的失败链；七项入口失败之后的功能与草稿删除流程未被这些测试实际验证。它是重新生成的应用，不能将这里的 23/34 与旧 BookStack run 当作同一应用仅修改交付语义后的受控对照。
