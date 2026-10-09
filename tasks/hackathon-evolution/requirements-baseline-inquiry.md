# Hackathon Evolution 需求与基线调查

调查日期：2026-10-06（北京时间）
材料：`runs/hackathon-evolution/inquiry-20261006/requirements/`、`requirements.zip`、`initial-projects.zip`。
方法：仅用 `ZipFile` 将官方包完整提取到 `runs/hackathon-evolution/inquiry-20261006/baseline/`，并另提取 `frontend/src`、`backend/src` 到同目录 `readonly-source/` 做静态阅读；没有启动服务、模型、测试、评测，也没有读取隐藏评测器或原生 rollout。WorkSSD 复核为 931 GiB 总量、269 GiB 可用；ZIP 约 188 MiB，解压内容约 567 MiB。

完整材料的逐成员哈希、应用目录和提取安全检查见 [`material-manifest.json`](../../runs/hackathon-evolution/inquiry-20261006/material-manifest.json)。原始 ZIP SHA-256 为 `38c0457d9df1...fad8ba0`；提取记录 3413 个成员（3411 文件、2 目录），拒绝绝对路径、`..` 路径和符号链接，原 ZIP 未修改。`.factory26`/`.factory-e2e` 等运行材料仅为归档忠实性保留，未作为产品源码或评测依据。

## 公开需求范围

`requirements.yaml` 显示 GitHub 有 52 个 atomic、Sheet 有 10 个 atomic。每题都有 5 个修改项和 5 个新增项，因此本轮公开行为增量是每题 10 项、共 20 项，对应每题 30 个公开评测场景（不是说旧 atomic 已通过；旧功能仍需在演化产物中保留并由平台验收）。

## GitHub：5 项既有行为修改

|需求|公开增量|基线源码边界与判断|
|---|---|---|
|REQ-1-1-1 注册|用户名允许小写字母、数字、单个 `-`/`_`，1–39 字符，首尾不能是分隔符；重复用户名保留输入并报原错误。|基线 `backend/src/routes/auth.js:14-28` 只有登录，没有注册路由；数据库 `schema.js:10-16` 仅有 `users.username/email UNIQUE`。注册校验、错误保留和演化规则的实现位置需要先在初赛产物中确认，不能仅依赖唯一约束。|
|REQ-1-1-2 登录|邮箱匹配大小写不敏感；用户名仍大小写敏感；错误登录不得建 session。|`routes/auth.js:17-26` 使用 `username = ? OR email = ?` 的精确 SQLite 比较，未体现邮箱规范化；成功插入 `sessions`，所以只需把邮箱分支改为大小写不敏感并保留用户名精确语义。需注意数据库现有邮箱数据和唯一约束是否已按大小写处理。|
|REQ-2-1-2 建组织|提交的 identifier 可含大写，先转小写再做唯一性检查和持久化；display name 仅 trim 后保留原大小写。|静态基线未找到 `organization`/`teams` 表或对应 route（schema 现有表从 users、repositories、collaborators 到 issues/PR 等）。这表明组织功能至少存在明显边界缺口；若初赛运行时由其它被排除的材料提供，首轮必须以实际目录和数据库迁移核对，不能假设静态包已有组织数据。|
|REQ-3-1 搜索仓库|查询大小写不敏感，同时匹配 repository name 和持久化 description，并服从可见权限。|`routes/repos.js:18-27` 仅提供公开仓库列表；源码中未见全局搜索 route/page。仓库实体已有 `description`（`schema.js` 与 `repos.js:21-23`），因此数据字段存在，但搜索入口、权限过滤和 description substring 行为需新增或确认。|
|REQ-4-3-1 分支选择|分支选项有 `option` role/准确名称；选择后写入地址并在 reload 恢复；无匹配查询不改变地址和活动分支。|`frontend/src/pages/RepoPage.tsx:16-32,43-53` 仅以 React state 保存默认/当前 branch，并用原生 `<select>` 加载文件；没有 URL 读写、查询过滤或自定义 option 语义。该增量集中在 RepoPage 与路由状态，后端已有 branches/files API。|

5 个新增 GitHub atomic 的边界：

|需求|新增公开行为|基线源码边界与判断|
|---|---|---|
|REQ-1-4 Active sessions|Settings → Active sessions 列出当前及其它会话（设备/last-active，不泄露 secret）；只能撤销其它会话，撤销后受保护页面回登录，当前会话继续有效。|已有 `sessions(token,user_id)` 与登录/注销的写入删除（`backend/src/routes/auth.js:25-43`）以及 `auth.js` 按 token 查会话，但没有 session 元数据、列表/撤销 route 或 Settings 页面；需要扩展 schema/API/UI，并保留当前 token。|
|REQ-2-4 Audit log|Owner 可看语义表格 Actor/Action/Target/Timestamp，可按 action 过滤并 reload 保持；普通 Member 不可进入。|已有 issue/PR `events` 记录基础设施，但未找到 organization、owner/member、组织事件或 Audit log route/page；schema 未见组织审计表。需要先确认现场是否含额外组织实现，不能从静态包假定可复用。|
|REQ-3-5 Archive/restore repository|Admin 确认归档/恢复；Archived 标记持久化，仍可读但所有写操作禁用；恢复保留文件、issue、branch、权限。|`repositories` 有 visibility 等字段但 schema/route/frontend 未见 archived 状态、设置按钮或统一写操作门禁；现有 issue/pull/repo 写 route 各自检查权限。需要持久字段、读模型、设置 UI，并在每个写入口统一拒绝 archived。|
|REQ-4-5 Releases|有 Releases/New release 表单，发布到已有 branch/tag，tag 同 repo 唯一；访客可读、无发布权限；刷新保留。|未见 releases 表、route、页面或 RepoShell 导航；branches 已存在，故目标 branch 可复用，但 release 关联和唯一约束需新增。|
|REQ-5-5 Reactions|已认证可在 issue 上加/移自己的 reaction，菜单和精确按钮语义，计数 reload 保留；匿名只能看计数。|未见 reactions 表、route、IssueDetail reaction UI；issues/comments/labels/assignees/milestones 已有独立表和 API，反应应新增关联表并避免修改 issue 主体。|

## Sheet：5 项既有行为修改

|需求|公开增量|基线源码边界与判断|
|---|---|---|
|REQ-1-2-2 重命名 workbook|trim 后最长 80；跨 workbook 大小写不敏感唯一；精确错误文案；失败保留标题、home link 和对话框值。|对话框已存在（`EditorDialogs.tsx:18-55`），但 `Editor.tsx:422-428` 只检查空值并直接 commit；backend `server.js:134-145` 的 PUT 只做非空结构校验，未做名称长度/跨文件唯一性。需要同时保证前端提交失败不关闭且后端原子写保持旧文档。|
|REQ-2-1-3 重命名 worksheet|trim 后最长 50；同 workbook 内大小写不敏感唯一；精确错误文案；失败保留 tab/dialog 值。|对话框已存在（`EditorDialogs.tsx:58-95`），`Editor.tsx:384-393` 只做空值和大小写敏感的 `===` 重复判断。文档整体 PUT 已能持久化，但大小写唯一和长度检查目前没有。|
|REQ-3-1-1 Delete 清除|Delete 清除当前矩形；清公式移除原公式并重算依赖；保留选择、空 formula bar，刷新后仍为空。|网格已监听 Delete/Backspace 并调用 `onClearRange`（`Grid.tsx:175-179`），说明部分增量可能已在初赛基线中；需要确认 `onClearRange` 是否覆盖矩形、公式依赖和持久化，静态代码存在不能视为 UI 验收。|
|REQ-5-1-2 保存 filter view|当前过滤器可命名保存；名称 trim/非空/同 workbook 唯一；可管理、替换、删除并持久化 criteria。|`model.ts:64` 的 Sheet 只有单个 `filter`；`Editor.tsx:436-460` 只有 create/apply/clear filter，`EditorDialogs.tsx` 仅有过滤条件对话框，未见 saved views 数据结构、菜单或管理 UI。需要扩展文档 schema 与前后端整文档保存，同时不能破坏已有 filter。|
|REQ-5-2-1 数据验证错误文案|对话框增加可选 Error message；trim 后替换所有非法输入路径；重开预填，更新/清除立即生效且刷新保留。|`ValidationRule` 当前只保存 type/range/values/min/max（`model.ts:127-155`），对话框保存同样字段（`EditorDialogs.tsx:295-318`），`validationMessage` 固定生成标准文案；因此需增加字段并让所有 `checkValue` 调用统一使用它。|

5 个新增 Sheet atomic 的边界：

|需求|新增公开行为|基线源码边界与判断|
|---|---|---|
|REQ-6-1 Freeze rows/columns|View 菜单冻结行、列或 panes；按钮显示 `Frozen rows: <count>; columns: <count>`，刷新保留。|`Sheet` 模型当前含 cells/validations/filter/selection/pivot，但未见 freeze 字段、View 菜单或 frozen button。需要在 JSON 文档中增加兼容字段，并让 Grid 渲染冻结状态。|
|REQ-6-2 Find/replace|按显示值整格匹配，大小写可选；Find next 显示计数并选中；Replace all 只改当前 sheet，显示替换数且持久化。|未见 Edit 菜单、Find dialog、匹配/替换状态或批量更新入口；现有 `model.ts` 有单元格/范围操作基础，但需避免把公式显示值和原公式语义混淆。|
|REQ-7-1 Named ranges|Data → Named ranges；名称必须字母开头，保存范围可用于公式；编辑范围立即重算，刷新保留。|`Sheet` 模型未见 named ranges 字段；公式引擎注释称同 sheet 引用且现有解析未显示命名解析。需要文档字段、公式解析环境和管理 UI/API；错误文案必须在边界统一。|
|REQ-7-2 Conditional formatting|按 Greater than/Text contains 与三种 fill style 保存、编辑、删除；只对匹配 cell 显示，刷新保留。|未见 conditional rules 字段、Format 菜单或 Grid 条件样式；`Grid.tsx` 目前只根据 selection/filter 组织 class。需把规则存储与显示样式分开，不能改变 cell value。|
|REQ-8-1 Cell notes|Insert → Add note；单元格有 Open note，支持查看/编辑/删除；不改 value，刷新保留。|未见 notes 字段、Insert 菜单、note dialog 或 cell note button。应新增按 cell coordinate 的持久字段，并兼容已有 JSON，避免把 note 写入 `cells` 破坏公式/CSV。|

## 数据、迁移与种子注意事项

GitHub 基线是 SQLite（包内 `backend/database.db`）且 schema 使用 `CREATE TABLE IF NOT EXISTS`；本轮新增/确认组织、会话、审计、归档、release、reaction 时，不能只改 UI，需考虑已有 seed 用户、repositories、branches、issues 和唯一约束。没有组织相关表/路由的静态证据时，首轮 Harness 应先读取实际基线目录和数据库 schema，再决定是增量迁移还是沿用已有表，禁止清空数据库重建。

Sheet 基线是每 workbook 一个 JSON 文件（`backend/src/server.js:20-40`），启动只在 data 目录为空时写入 `Q3 Sales` seed；PUT 是整本 JSON 原子替换（`server.js:134-145`）。公开规则只明确平台自动注入应用，需求文本要求 application provision 对应 EVO seed；谁负责 fixture 注入未由本调查实证。因此 Harness 不能假设平台已经提供 EVO workbook：应在现场确认入口与数据职责，并确保应用按公开需求提供/识别 EVO 数据，同时保留基线数据。新增 `filterViews`、validation error message、freeze、named ranges、conditional rules、notes 等字段应向后兼容旧文档。

## 首轮 Harness 运行原则与未知

后续首轮运行应把平台注入的实际应用现场与本地归档基线分别核对：先列出输出目录、读取启动入口、确认数据目录和 DB/JSON 实际位置，再按每题 30 个公开演化场景覆盖 10 项增量。这里不预设采用哪个 variant，也不把本地静态基线差异解释为方案优劣；Harness 输入输出契约仍与初赛相同，且不得复制下载包、清空输出目录、覆盖整个项目或探测测试文件。

静态调查不能证明旧 52/10 atomic 已通过，也不能证明 UI 可达性、ARIA、reload、并发保存和跨浏览器行为。尤其需要首轮实际运行确认：GitHub 的注册/组织/搜索入口是否在未提取的产物部分；新增 session/audit/archive/release/reaction 的实际数据入口；Sheet `onClearRange` 的完整实现、预置 JSON 的字段版本，以及 EVO fixtures 是由应用还是平台提供。若运行结果显示基线与静态包不一致，应以平台注入后的现场为准并把差异写回 packet。

证据入口：

- 需求：`runs/hackathon-evolution/inquiry-20261006/requirements/hackathon-evolution--github/requirements.yaml`、`...--sheet/requirements.yaml`
- 基线源码只读提取：`runs/hackathon-evolution/inquiry-20261006/readonly-source/`
- 原始包校验：`requirements-inventory.json`、`initial-projects-inventory.json`
