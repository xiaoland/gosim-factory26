# 两轮 ARC-Bench-Lite 得分诊断

本文记录逐个 task run 的评分现场；不是开发耗时复盘。上一轮是在 WSL 用当时固定的公开 ARC 测试评估生成应用，本轮是官网 Competition 练习。公开 benchmark 已有新版，且两轮的包、需求文本与部分 Braid revision 不同；这些分数不能当作同口径单变量 A/B 实验。

| 轮次与 variant | Keep | BookStack | 证据 |
| --- | ---: | ---: | --- |
| 上轮 pi-generalist | 3/32 | 18/34 | WSL `runs/batch-multi-agent-20260922-01/pi-generalist-{keep,bookstack}/evaluation/` |
| 上轮 pi-team | 16/32 | 15/34 | WSL `runs/batch-multi-agent-20260922-01/pi-team-{keep,bookstack}/evaluation/` |
| 上轮 codex-generalist | 5/32 | 8/34 | WSL 批次 Keep；BookStack `runs/20260922-144234-2b52c95d/evaluation/20260922-170531-cd743f12/` |
| 上轮 pi-verification | 8/32 | 9/34 | WSL `runs/20260922-144234-cd7850f8/evaluation/20260922-153455-63155f43/` 与 `runs/20260922-154050-5ee2ae35/evaluation/20260922-165811-3a5efd02/` |
| 本轮 pi-team-mixed | 23/32 | 13/34 | 本机 `runs/competition/iteration-throughput-boundary-20260923/hosted/pi-team-mixed/tasks/` |
| 本轮 pi-team-deepseek | 32/32 | 27/34 | 本机 `runs/competition/iteration-throughput-boundary-20260923/hosted/pi-team-deepseek/tasks/` |
| 本轮 pi-team-glm（官网，进行中） | 23/32 | 待完成 | 本机 `runs/competition/iteration-throughput-boundary-20260923/hosted/pi-team-glm/tasks/` |
| 本轮 pi-team-glm（本地旧版测试） | 未评分 | 8/34 | WSL `runs/local/iteration-throughput-boundary/pi-team-glm-bookstack/evidence/evaluation-input/evaluation/20260923-083210-cdf1ebe3/` |
| 本轮 pi-team-glm DNS 修复重跑（本地旧版测试） | 6/32 | 未运行 | WSL `runs/local/iteration-throughput-boundary/pi-team-glm-keep-dns-retry-1/evidence/evaluation-input/evaluation/20260923-120054-ccaf365c/` |
| 本轮 pi-team-vv（本地旧版测试） | 未评分 | 15/34 | WSL `runs/local/iteration-throughput-boundary/pi-team-vv-bookstack-dns-retry-2/evidence/evaluation-input/evaluation/20260923-114739-e36da31b/` |

上轮每项都有 `results.json` 和失败用例的 `test-results/*/error-context.md`；这些现场快照比汇总页的 `timedOut` 更能说明失败停在哪里。本轮官网状态只有泛化的 10 秒超时，需读取对应 `logs/*.json` 中的 Playwright stdout；Keep 的实际应用 bundle 可下载，BookStack 的应用源码已保存至对应 task 目录的 `analysis/application/`。本轮官网没有取得失败时的 DOM 快照，因此对 BookStack 的底层原因须保留不确定性。

## Keep

- **上轮 pi-generalist，3/32**：29 个失败中，12 个被 `div.note` 与测试的 `article` 卡片范围假设挡住，7 个被 `nav` 与测试的 `complementary` 侧栏假设挡住，4 个在 `Take a note…` 与精确名称 `Take a note` 的入口差异处停止；其余 6 个涉及编辑器、搜索建议、设置菜单和视图控件语义。侧栏 helper 甚至将原本展开的导航误判为关闭并主动折叠。可见控件存在不等于其下游操作被测试过。
- **上轮 pi-team，16/32**：5 项停在测试要求的 `dialog "Note editor"` 与实际内联编辑器／`Edit note` 对话框差异；2 项标签操作停在 `Label note` 对话框与测试限定的 `Note editor`；2 项测试寻找 `Archive`，而应用和输入要求均写 `Archived`。其余失败分布在标签编辑结构、置顶属性、设置菜单角色、视图控件状态及侧栏属性。REQ-2.8.1 的失败快照里笔记已在 PINNED 区，故不能说置顶动作没有发生。
- **上轮 codex-generalist，5/32**：27 个失败的首个阻断点分为卡片范围 12、创建入口名称 4、侧栏范围／误折叠 6、编辑器角色 1、搜索建议角色 1、设置菜单内容 1、视图状态属性 2。卡片标题与操作按钮是兄弟节点，测试回退到标题节点后查不到按钮；这不是这些按钮不存在的证据。
- **上轮 pi-verification，8/32**：24 个评分失败集中在创建入口不是 button、编辑器缺 dialog、搜索建议缺 listbox、设置菜单缺 menu/menuitem、视图／侧栏缺状态属性，以及测试从标题节点查找兄弟操作按钮。该 run 是恢复后评分，但 `summary.errors=[]` 且 32 项均验证，不能把其低分归因于交付链失败。
- **本轮 pi-team-mixed，23/32**：9 项中 6 项是应用把规范明确要求为 button 的 `Delete Note`／`Change labels` 覆盖成 `role="menuitem"`；2 项是规范要求 article 自身 `title="Pinned"`，应用照做，测试却用 `card.getByTitle('Pinned')` 查子节点，不能据此判置顶状态错误；REQ-4.2 找不到 Save，但无失败 DOM，原因未定。生成侧宣称自验 76/76、复核 79/79，仍遗漏了 6 项明确角色合同，说明自验 oracle 没覆盖真实验收的这个边界。
- **本轮 pi-team-deepseek，32/32**：官网 32 项全通过，生成和评分均完成。它是本轮第一个 Keep 满分的正式参赛 run；不能仅凭总分断言其内部协作方式导致提升。
- **本轮 pi-team-glm，23/32**：独立逐例诊断将 9 项失败分为 `Notes workspace` region 缺失 1 项、两条 `Travel plans` 卡片内按钮未出现 2 项、`Note editor` 内 `Work`/`Reminders` checkbox 未出现 3 项、置顶标题被测试作为卡片后代查询但未找到 2 项、卡片内 `Pin note` 按钮未找到 1 项。全部是 10 秒定位超时；官网未提供 DOM snapshot/traceability 内容，不能据此证实具体应用缺陷或测试合同冲突。证据在 `hosted/pi-team-glm/tasks/arc-bench-lite--keep/logs/4d876c42c913d94a.json` 的 Playwright stdout 106–350 行。
- **本轮 pi-team-glm，本地 DNS 修复重跑 6/32**：26 个失败均有 DOM 快照。5 项点击创建／编辑入口后仍留在主页，没有出现 `Note editor` 对话框；21 项首先卡在可访问结构或文案：卡片标题与操作按钮为同级而测试从标题下查按钮 12 项、侧栏 `navigation` 与要求的 `complementary` 不符 3 项、视图／侧栏状态属性缺失 3 项，以及标签输入、搜索建议角色、菜单文案各 1 项。应用已启动，32 项全执行，低分不是 DNS 或评测设施中断。此 run 是旧公开测试重新生成的应用，不能与官网 GLM/Keep 23/32 当作同一应用环境差。证据在 WSL `runs/local/iteration-throughput-boundary/pi-team-glm-keep-dns-retry-1/evidence/evaluation-input/evaluation/20260923-120054-ccaf365c/`。

## BookStack

- **上轮 pi-generalist，18/34**：16 个失败中，13 个有 DOM 证据指向 logo、删除确认、Tags、New Book、Page title 等可见控件的角色／名称／placeholder 与测试不一致；2 个创建 Shelf 用例的 fixture 在页面及 seed 中均不存在；另 1 个 Draft 在页面不可见，虽有 seed，底层原因未定。
- **上轮 pi-team，15/34**：19 个失败中，8 个是 logo、Confirm Delete、Tags、New Book 等入口语义或名称差异，2 个是 Shelf fixture 缺失，6 个在无名 Login form 处受阻，2 个是 New Book 文案差异。REQ-6.2.1 是明确的应用路由错误：创建路由带 `id`，表单却把 `Boolean(id)` 视为编辑模式，现场显示 `Edit Chapter`／`Not found`。
- **上轮 codex-generalist，8/34；pi-verification，9/34**：大量失败在无名 Login form、把导航操作渲染为 link 而测试查 button、logo 为 link 而测试查 `BookStack logo` button 等公共入口处停止。前者 26 项失败，后者 25 项失败；下游创建、删除、收藏结果多数未被运行到。pi-verification 的 Draft 用例还受到未登录前置失败影响，不能归为删除逻辑错误。
- **本轮 pi-team-mixed，13/34**：21 项均记录为超时，但按首个失败阶段分为 17 项入口／导航、4 项页面或提交后断言（REQ-2.2、4.1、4.5.1、6.2.1）。官网 helper 的 `firstVisible()` 对候选定位器各试 500ms，全部未及时可见便回退第一个 button；因此日志显示“等待 button”本身不能证明 link 不存在。生成源码确实有 seed、列表 fetch、表单和保存路径；缺失败时 DOM，不能把 17 项一概判成数据缺失，也不能判成测试竞态。REQ-4.5.1 已点击 Save 才等更新名称；REQ-6.2.1 已点击 Save Chapter 才等新章节名称，这两项尤其不能归为入口缺失。
- **本轮 pi-team-deepseek，27/34**：7 项均在 `locator.click` 等按钮 10 秒时停止，尚未执行后续保存、删除或跳转断言。其中五项共享 Tags 入口：创建／编辑书架要求表单内 `Shelf Tags` 按钮（REQ-4.3.1、4.5.1），创建／编辑书籍及从书架创建书籍要求表单内 `Book Tags` 按钮（REQ-5.3.1、5.4.1、5.6.1）。REQ-6.1.3 等全页 `Edit` 按钮以进入草稿编辑器；REQ-8.2 等全页 `Favorite` 按钮以开始收藏。证据为 `hosted/pi-team-deepseek/tasks/arc-bench-lite--bookstack/logs/301dcbc530871c4e.json` 的解码 stdout 99–290 行。官网未提供这些失败时的 DOM，定位阻断点可信，具体控件为何缺失仍待验证。
- **本轮 pi-team-glm，本地 8/34**：26 项失败有逐例 DOM 快照。11 项首先受未登录写入限制阻断：9 项操作按钮由 `user` 条件隐藏，另 2 项提交后显示 `You need to be logged in.`，而这些官方用例没有登录前置。6 项先在未命名的 Login form 处停止，不能据此判断认证逻辑本身。其余首个停点为 Logo 定位 2、缺少 `Shelf 4.3.1` 种子 1、`ShelfForm.jsx` 使用未定义 `id` 导致 `ReferenceError` 1、应用文案符合输入规范但与官方测试相反 3、草稿操作菜单未展开 1、章节内页面导航预期不明 1。这里同时存在可证实的生成缺陷、测试与规范冲突及未定责的导航差异；不能把本地 8/34 与官网 mixed 的 13/34 差额归因于单一模型或 profile。
- **本轮 pi-team-vv，本地旧版测试 15/34**：独立逐例诊断将 19 项失败按首阻断分为登录表单 `Login` 按钮 6 项、书架／图书创建编辑控件 6 项、删除／编辑器／收藏动作 6 项，以及 Logo 角色／名称 1 项。REQ-1.2 的失败 DOM 明确显示 `link "BookStack home"` 包含 `img "BookStack logo"`，测试却找 `button "BookStack logo"`；其余多数只能确认控件在当时状态不可定位。生成轨迹记录构建、API 冒烟和自报的 76 项检查，但这不是本次 UI benchmark 的通过证据。34 项全执行、无设施错误；证据位于 `runs/local/iteration-throughput-boundary/pi-team-vv-bookstack-dns-retry-2/evidence/evaluation-input/evaluation/20260923-114739-e36da31b/`。

跨 run 比较只能确认**阻断位置**：上轮有不少用例被可访问性角色、名称及 fixture 的公共差异放大；本轮 Keep 消除了部分旧入口阻断，却出现新的 button/menuitem 违反；BookStack 本轮即使生成了更多页面，仍有大量用例未到业务断言。下一轮应把真实失败现场和题目文字、官方 selector 一起作为诊断依据；不能由 10 秒超时推断模型慢，也不能把当前 23/32 与上轮 16/32 的差额归因于单一 profile 改动。
