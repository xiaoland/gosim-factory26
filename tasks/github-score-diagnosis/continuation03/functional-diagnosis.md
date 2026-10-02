# continuation-03 GitHub 冻结应用实用复现

2026-09-28，目标是已发布应用 `pi-braid--hackathon--github-3d75045c72f1d6` 的冻结重放，不修改应用、不重生成或重评。官网重放 `3583c4dd7e48` 的 `status.json` 为 16/100、16/100 场景通过、5/47 功能完成，`tests` 为空，无法从官网材料定位其余逐例失败。`github-official/inputs.json` 指向该 published application；`github-artifact-replay.zip` 中 `replay-manifest.json` 的要求摘要为 `bdc17d23265a6b1948aec150e69d0b2accfa37db4c569305c97be7ff7f3b0b8f`，与输入一致。原始路径：`runs/e20260928-02-deepseek-direct/attempt-09/continuation-03/{github-official,github-artifact-replay.zip}`。

将 ZIP 解压到独立的 `/tmp/factory26-github-3583/`，在 macOS Node 22.22.3 下分别对 backend/frontend 执行 `npm ci`，frontend `npm run build`，以 `HOST=127.0.0.1 PORT=3181 DATA_DIR=/tmp/factory26-github-3583/data npm start` 启动。`/api/health` 返回 200 `{"ok":true}`。本机默认 Node 26.3.0 编译冻结依赖 `better-sqlite3@11.10.0` 失败（V8 API 已变），换用满足应用声明 `>=20.19.0` 的 Node 22 后安装与运行成功；这是本机诊断环境兼容问题，**不能推定为官网低分原因**。端口 3181 与 Sheet/3000 分离，未触碰其他服务。

| 正常用户路径 | 浏览器观察与持久化核对 |
| --- | --- |
| 账户、仓库与 Issue | 从首页 `Sign in` 用冻结要求的预置 `alice-dev` 登录；新建 `alice-dev/replay-probe` 私有仓库并初始化 README，仓库页显示 Private、README 和初始提交。新建 Issue `Replay diagnostic issue`、发表评论 `Persistent discussion probe.`，刷新后仍显示。只读 SQLite 记录为 `repo|replay-probe|private`、`issue|1|Replay diagnostic issue|open`、该评论正文。 |
| 组织 | 从账户菜单进入组织列表，新建 `replay-guild`，页面显示新组织，People 显示 `alice-dev` 为 Owner；SQLite 有 `org|replay-guild|Replay Guild`。 |
| PR 审阅与合并 | 在预置 `acme/acme-docs` PR #7 的 Files changed 中，以 Alice 提交 Approve 审阅，刷新后仍显示；确认合并后 PR 变 Merged，main 代码树出现 `docs/` 和合并提交 `7f8fb58`。SQLite 有 `review|approve|Independent review probe.` 与 `pr|7|merged|7f8fb58`。 |
| 访问边界与搜索 | Alice 退出后，访客及预置 `eve-reader` 都在直达 Alice 私有仓库时看到 `Access denied`；Eve 查看公开 PR #6 时没有审阅/合并控件。访客全局搜索 `acme-docs` 返回公开仓库，搜索 `replay-probe` 返回 `No results`。 |
| 注册负例 | 从首页 Sign in → Create an account，填入无效用户名 `-bad`、邮箱 `not-an-email`、短密码、不同确认并保持条款未勾选；一次提交后同时显示 Username、Email、Password、terms 四项错误。此次未创建账户或接受条款。冻结源码 `frontend/src/pages/AuthPages.tsx:113` 已有 `noValidate`，旧来源 run 的 HTML 原生邮箱校验截断缺陷在本产物中未复现。 |

**已复现的产品合同缺口**：冻结要求 `requirements.yaml:588` 明写账户菜单的 **link** `Your organizations` 打开组织页；冻结应用 `frontend/src/components/AccountMenu.tsx:67-69` 在 React Router `Link` 上显式加 `role="menuitem"`。实际浏览器无障碍树为 `menuitem "Your organizations"`，没有同名 link。人手点击 menuitem 能打开组织列表，但按需求角色操作的用户/自动化入口无法找到它。这说明该入口的可访问性合同违约，影响依赖组织导航的场景；没有逐例官网数据，无法据此推算它贡献了多少分。与旧来源产物相比，`New repository` 此次真实呈现为 link，注册多字段反馈也正常，不能把旧缺陷直接沿用为本次结论。

**结论边界**：上述实测证明部署和多条关键业务路径可用且持久化，反证“整个应用无法启动/全部写入无效”。确认的组织入口角色缺口是具体产品违约，但单独不能解释 84 个官网场景失败或 5/47 功能数；官网没有逐例断言，未检查所有 47 个原子需求。Chrome 扩展 UI 曾短暂阻断本地自动化；之后复现继续成功，故不列为应用问题。没有修改冻结应用、源码、官方评分或运行中的 Sheet 服务。
