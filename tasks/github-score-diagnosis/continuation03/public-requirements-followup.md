# continuation-03 GitHub：公开需求追加核对

2026-09-28。对象是已冻结的 `pi-braid--hackathon--github-3d75045c72f1d6`，提交 `c3fb22d`，官网运行 `3583c4dd7e48`。官网报告 16/100 场景通过、5/47 功能完成，但 `tests` 为空，没有逐例断言。本调查只以公开 `evidence/requirements.yaml`、冻结应用、隔离副本的浏览器操作和只读源码为依据；首轮已覆盖的登录、仓库/Issue/PR 正向路径与组织入口角色缺口见 `functional-diagnosis.md`。下表记录新增的有区分力路径，不用本地通过或失败数反推官网逐例结果。

隔离副本位于 `/tmp/with-service-gh-validation-20260928`，调查时 Node 22 服务使用 `127.0.0.1:3189`，数据仅在 `/tmp/gh-public-followup-data-20260928`；取证结束已仅停止该服务 PID 5634。浏览器子代理使用真实浏览器 UI，主任务用 SQLite 只读查询和冻结源码辅助核对；没有修改应用或检查脚本。

## 公开需求与实际行为

| 需求与入口、初始前提 | 浏览器操作、刷新与结果 | 判断 |
| --- | --- | --- |
| **REQ-2-2-1**：Owner 从账户菜单进入组织 `acme` → `Teams` link → `New team` link；预置组织及 Owner `alice-dev`。 | Alice 创建唯一团队 `probe-team-late03`，表单有 `Team name`、可选描述/父团队、`Create team`；跳转到 `/orgs/acme/teams/probe-team-late03`，标题 `acme/probe-team-late03`，刷新保留。Teams 列出预置 `platform-team`、`frontend-team`、`frontend-child` 及父关系。 | 这条正向路径符合。非法/重复名、非 Owner 负例未验。首轮已确认 `Your organizations` 被覆写为 `menuitem` 而需求要求 `link`；该入口缺口仍适用。 |
| **REQ-2-2-2**：团队 `Members` link，Owner 加入当前组织成员 `bob-reviewer`，可立即移除；`Settings` 有原生父团队选择。 | `/orgs/acme/teams/probe-team-late03`：`Add member` 打开 `Username`，提交 Bob 后刷新仍显示 `bob-reviewer` 和 `Remove bob-reviewer`；点击移除、刷新后消失。`Settings` 有原生 `Parent team` select 和 `Save`，显示 `Current parent team: none`；未提交层级更改。 | 成员加入/移除与持久化符合；循环拒绝、层级保存、非 Owner 未验。macOS 浏览器 AX 把原生 select 显示为“pop up button”，不能据此认定其 Web 语义违反 combobox 合同。 |
| **REQ-2-3**：仓库 Admin 从 `Settings` → `Manage access` → `Add people or teams`，选未获授权的组织团队并授予 Write；既有授权改 Read 应替换而非重复。Alice 是组织 Owner。 | `/acme/acme-docs/settings/access` 搜索 `probe-team-late03`，选择结果，`Role` 原生 select 改 Write、点击 `Add`；列表一行显示团队与 Write，刷新保留。随后同一行改 Read、`Save`；刷新仍只有一行且为 Read。 | 授权创建、更改及单行持久化符合。未测成员通过团队访问私有仓库及无权者拒绝。隔离数据中临时团队授权留为 Read，页面没有移除授权按钮。 |
| **REQ-5-4**：只有 Triage/Maintain/Admin 可关闭或重开 Issue，**Write 只能查看状态**；预置 Bob 对 `acme/acme-docs` 为 Write。 | 独立浏览器以 `bob-reviewer` 登录；Alice 的 `Manage access` 显示 Bob 当前角色 Write。Bob 打开 `/acme/acme-docs/issues/8` 的 Open Issue，页面却有 `button "Close issue"`；点击后变 Closed，出现 `Reopen issue`，活动记录 `bob-reviewer Closed issue`。Bob 又重开，刷新后为 Open；只读 SQLite 有 Bob 的 `closed_issue`、`reopened_issue` 两条记录。 | **确认产品与服务端权限违约**，不是仅仅多显示按钮。重开恢复了状态，但隔离副本保留历史审计记录。 |
| **REQ-5-3-1/2/3**：Assignees、Labels、Milestone 的修改同样仅允许 Triage/Maintain/Admin，Write 只能查看。 | 在冻结前端 `IssuePages.tsx` 中，`TRIAGE_ROLES` 明确包含 `write`，四种控件共享 `canTriage`；后端 Assignees、Labels、Milestone、Close/Reopen 路由均用 `requireRepoRole('triage')`，而 `permissions.js` 将 Write 排在 Triage 之上，`guards.js` 用数值等级放行。 | **同一错误权限规则覆盖四个原子功能**。本次只通过浏览器实际写入 REQ-5-4；其余三项是源码推导的高置信风险，尚非独立 UI 复现。 |
| **REQ-6-4**：PR 作者从 `Reviewers` button 打开 `Search`，匹配候选应为 **role option**、精确用户名；选择后请求持久，`Remove <name>` 即时移除。预置 Alice 为 PR #3 `Fix search` 作者、Bob 为独立 Write 候选。 | `/acme/acme-docs/pulls/3`：输入 `bob-reviewer` 后，浏览器 AX 出现的是 **`button "bob-reviewer"`**，没有同名 option。点击该 button 后请求立即保存，刷新保留；`Remove bob-reviewer` 后刷新不再有请求。Conversation 留下请求和移除事件。 | **确认候选可访问性角色违约**；业务写入路径可用。冻结 `PullPages.tsx` 候选直接渲染为 `<button>`，自建 e2e `req6b.spec.mjs` 还显式用 `getByRole('button')` 接受该错误角色。 |
| **REQ-5-3-3 的 PR 分支**：公开要求在 Issue **或 PR** 右侧设置 Milestone。 | Alice 打开公开 PR #3 右侧，仅有 Reviewers、Review summary、Merge、状态控件；浏览器无 `Milestone` 按钮或现有里程碑。冻结 `PullPages.tsx`/`pulls.js` 没有 milestone 路径，`pull_requests` 表也没有 `milestone_id`，而 `issues` 表有。 | **确认 PR 里程碑分支缺失**。Issue 分支此前未在本轮验证；这项缺口不能换算为官网失败数。 |

## 归因与验收启示

最清晰的失效链是公开角色矩阵明确排除 Write → 冻结应用把仓库角色写成线性等级 → 前端显示、服务端同时放行 → Bob 实际关闭 Issue 并持久化。自建 `backend/test/issues.test.mjs` 的权限负例只测 Read/Eve，正例用 Owner/Alice，没有测最接近允许边界的 Write/Bob；这使错误规则通过了自检。对应的最小验收改动方向是从公开需求生成操作级角色矩阵，至少对每个非累积角色边界保留一个“相邻但无权”的实际拒绝场景，检查失败时回到需求而非照现有实现改断言。

第二条链是公开要求 reviewer 候选为 option → 生成 UI 用 button → 自建 e2e 按 button 定位并通过。与首轮 `Your organizations` 的 link/menuitem 缺口同型：功能正向点击成功，无法证明精确可访问性合同成立。应在冻结后的最终产物上，对跨模块入口和 picker 直接按需求角色、名字、作用域核对；业务 API 自检只能补充持久化证据。

组织团队与授权的几条正向路径提供反证：应用不是整体不能工作，也不是所有预置数据缺失。PR 里程碑则是另一类完整性缺口：公开文字覆盖两种工作项，生成实现只覆盖 Issue；需求分解与验收需要枚举这种并列对象。上述证据只能解释具体公开需求违约，无法解释官网 84 个失败场景分别落在哪些功能，也不能从 5/47 推出所有其余功能均坏。其余公开需求未在本次针对性复现中判定。

## 根任务设计与组件选择

原始任务在远端 `ssh wsl.win-ws.localhost` 的 `/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/generation/runs/pi-braid--hackathon--github-88884da4b94a0f/workspace/official-generation/template/.factory26/20260928-030347-78b10c07/`。其中 `braid-state/braid.sqlite3` 的 `local_items`、`local_comments` 及 `work/native-homes/` 原生轨迹保存根 Issue #1、子 Issue #2–#9、PR #1–#13。只读查询并核对提交历史后，有以下分层结论。

1. **根任务做了流程与共享技术设计，不能说完全没有设计。** 根 Issue #1 正文要求先拆分、按共享基础依赖分批、只依据公开需求，规定 Node 20 构建链与临时数据隔离；根评论 #2 在 03:12 UTC 给出子任务树、依赖与整合验收。#2 共享基础正文在 03:08 左右选定 Vite/React/TypeScript + Express/better-sqlite3、数据表、认证/API、权限和共享 UI 骨架；#2 评论 #1 补了端点与错误体契约。最早共享基础提交 `039dbd5` 在 05:05 UTC，REQ-5 提交 `d35b1ec` 在 06:19，PR 评审提交 `752a084` 在 07:48，最终合并提交 `c3fb22d` 在 10:03。早期契约实际传给并约束后续子任务。
2. **设计的粒度不足以守住操作级权限。** 公开 ROOT 特意说明 Read/Triage/Write/Maintain/Admin 不是自动累积等级，REQ-5-3-1/2/3、5-4 均明确排除 Write。#2 共享基础却规定“按 Read/Triage/Write/Maintain/Admin 守卫 API”，最终 `permissions.js` 用 `ROLE_LEVELS` 数值比较。子 Issue #7 把四项权限概括成“`Triage+`”，其关闭/重开验收负例仅要求“Read 不可见”，没有要求 Write 拒绝。PR #7 的实现和自检继承了这个口径，最终根验收复跑同一套检查；浏览器 Bob/Write 关闭 Issue 的结果是可观察后果。这条是**早期契约表达不精确 → 子任务与 oracle 沿袭 → 产品越权**的实证链。
3. **里程碑对象范围在拆分时收窄。** 公开 REQ-5-3-3 第一段写“Issue or pull request”。#2 共享基础数据模型列出 Issue 里程碑关系，却未给 PR 关联；#7 子 Issue 的 REQ-5-3-3 条目只写 Issue 侧的按钮和种子，#8/#9 PR 子任务也未承接 PR Milestone。最终 schema 只有 `issues.milestone_id`，没有 `pull_requests.milestone_id`；浏览器 PR #3 右侧也没有该入口。这条是**并列产品对象未在任务树列清 → 数据与页面都缺失**。根评论 #2 和最终评论 #94 还把同一份 3819 行需求误记为“40 原子需求”；对原始输入和本地证据文件的 SHA-256 均为 `bdc17d…b0b8f`，实际递归计数为 **47**。错误计数不是独立故障，但说明启动时没有可靠的原子需求台账。
4. **可访问性角色在实现和自检之间被同向改写。** #9 子 Issue 对 reviewer 候选只保留“选项”而未保留公开要求的 `role option`；冻结 UI 用 `button`，自建 e2e `req6b.spec.mjs:389` 也用 `getByRole('button')`。根任务最终以这套 e2e 的 103/103 等通过作为全覆盖证据。这个事实支持“断言跟随实现而非合同”的解释，比“没有 icon 包”更贴近已证实的缺口。

组件与图标方面，冻结前端依赖只有 React、React Router、Vite、TypeScript，没有独立组件库或 icon 包；代码有共享 `Form`、`RepoNav`、`StatusBadge` 等组件，并以 CSS、局部 SVG/字符图形实现图标。根 #2 指定“共享 UI 组件”，但在根 #1/#2 的正文与评论中没有记录选用或拒用组件/icon 库的比较、视觉系统或截图验收判据。根负责人最初原生会话列出 27 张参考图，未见在该启动会话打开图像的调用；后续成员目录中存在 vision 子代理轨迹，因此不能推断全团队没看过图。浏览器观察：仓库、Issue、PR 页共用深色顶栏和仓库导航，控件样式大致一致；登录后首页主体稀疏，仅有标题、产品说明和一个公开仓库链接；Issue 有右侧元数据区域而 PR 没有 Milestone。图标较少，但文件、文件夹、状态徽标与 Issue 齿轮有图形表达。**没有组件库是可核实的技术选择，缺少视觉验收是流程空白；目前没有证据证明引入某个库会修复权限、role option 或 PR 里程碑缺口，也不能把视觉取舍换算成官网失分。**

早期设计偏差并非都留在产物里：#2 曾用内部名 `acme/web-app` 作中央种子，与公开需求的 `acme/acme-docs` 不符；PR #13 整合验收发现并以 `bb9bbe6` 修正，根评论 #83/#92 记录了修复和全量复验。因此这条可说明初始需求建模不足和后期返工，**不能列作本次冻结产物的缺陷**。共享基础会话过期错误也在 PR #3 修复，不能拿旧状态解释 16/100。

对 Harness 的最小改进是：根任务启动时为 47 条原子需求生成一份可核对的“对象/角色/可访问名/种子/持久化”台账；子 Issue 和最终验收引用原子 ID，不把“仅 Triage、Maintain、Admin”缩成 `Triage+`，并列对象如 Issue/PR 各有明确归属；共享基础的权限契约按操作表达而非假定单一等级；最终候选除脚本回归外，抽查少量跨角色负例、精确 AX 角色与关键参考页面。若产品下一轮确有更高视觉要求，再依据截图差距决定是否采用组件/icon 库，避免把依赖引入当作已证实的低分修复。

## 证据入口与边界

- 公开要求：`evidence/requirements.yaml`。冻结产物：`runs/e20260928-02-deepseek-direct/attempt-09/continuation-03/github-artifact-replay.zip` 内应用；官网终态：同目录 `github-official/tasks/hackathon--github/status.json`。
- 本地可复现入口：启动隔离副本、以预置 Alice/Bob 登录上述 URL。所有写入只发生在独立 `DATA_DIR`；正式应用未改。此次未运行 Factory 自身或开发基础设施测试，也未执行新官网评分。
- 未解：官网逐例失败、角色/里程碑缺口具体影响的场景数、其余未验公开需求；远端原生轨迹未逐条审阅所有成员的视觉判断，故不对整个生成过程的视觉决策作不存在的断言。
