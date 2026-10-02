# I11 final GitHub：REQ-5 Issues / REQ-6 Pulls 旅程断点

2026-09-30，只读有界调查。对象为官网最终重放 `e68661975b53`；身份、184/184 冻结文件一致性与无逐例评分信息复用 `tasks/pi-minimal/github-score-analysis/i11-e68661975b53.md`。本 cell 只写本文件；没有启动应用、运行测试、读取私有评测器、修改应用或 variant，也未另委派。代码审查应用 ponytail 技能，按真实组件组合追调用，而非以函数存在代替用户可达。阶段：先完整需求层级 description → 路由/组合控件 → API/权限/存储/seed → 重要缺口的定向过程与历史自验反证；精确审查耗时未单独计量。

记号：**F** = `runs/analysis/i11-github-e68661975b53/20260930T033923Z/extracted/template/`，以下应用路径均相对 F；**N6** = `runs/analysis/i11-github-e68661975b53/20260930T033923Z/native-preserved/065faa32-2026-09-29T16-09-22-776Z_01a0eded-8a58-762d-bc11-f3200d8a7401.jsonl`。JSONL 行是物理行。原始 tar 成员身份见同目录 `selected-native-index-v2.json`，不使用 v1。

## 原需求前提与入口

不是把 atomic 名称当全集。REQ-5 父层 `requirements/requirements.yaml:2130–2164` 规定持久对象、统一编号、按权限展示控件、跨账户/刷新一致性、append-only 活动、独立 mutation seed。REQ-6 父层 `:2807–2847` 规定四状态、Draft 可关闭、Merged 终态、当前 compare commit/stale/Outdated、导航链接与准确名称，以及每场景独立 provision/restore（含重复/并行）。文件/分支来自 REQ-3-3 与 REQ-4-3 的既有仓库上下文，不能凭新造孤立 PR 替换。

| 原层级 | 用户旅程与状态前提 | 最终组合入口及静态核对 |
| --- | --- | --- |
| REQ-5-1（:2171–2180）、5-1-1（:2188）、5-1-2（:2247–2259） | Public Issues；Open/Closed 精确标题；Search issues 输入即过滤，URL/刷新保留；详情独立可开、精确 heading、description/metadata/timeline | `routes.tsx:113–123`；RepoNav 的 Issues link；IssueListPage 链接/搜索 input(type=search)/URL query；IssueDetailPage 独立 detail GET，标题 h1 与编号分开。SegmentedNav 的徽标 aria-hidden，标题 Link 无编号混入名称。 |
| REQ-5-2 父层（:2340–2353）、5-2-1（:2362）、5-2-2（:2426–2445）、5-2-3（:2500–2519） | Write/Maintain/Admin 创建、两次独立内容保存、评论；空白标题/评论零残留；Read/Triage 控件缺席；任何已登录可读者可 toggle 自己 reaction | NewIssuePage 的 Title/Description/Submit new issue；IssueDetailPage 的两个 InlineEditor、CommentEditor、ReactionBar，TextField/textarea 的 label→id；API 信封真正解包；issues router 的 write guard、service transaction/validation、comments+activities、reaction 唯一键。 |
| REQ-5-3 父层（:2572–2587）、5-3-1（:2594–2617）、5-3-2（:2653–2667）、5-3-3（:2702）、5-4（:2741–2755） | Triage/Maintain/Admin 管理 metadata/状态（Write 被明确排除）；assignable 是另一个 ≥Triage 集合；本仓库 label/milestone；点击 option 即保存关闭；milestone 同时适用于 Issue/PR | IssueDetailPage 右侧三个 MetadataPicker，Menu→listbox→option 精确用户名/标签/里程碑；选项回调连到 put/delete 与返回完整 detail；issues router/service 限当前 repo、写活动。Issue close/reopen 立即调用，Read/Write 无控件。PR milestone 见候选 1。 |
| REQ-6-1（:2855） | Settings→Branches；Admin 两独立规则；exact branch；非Admin无 Add；当前 compare commit 的 test 初始pending，Admin Save持久，保护参与merge/direct-write约束 | `routes.tsx:127`；BranchSettingsPage:148 实际组合 BranchProtectionSection，后者 Admin-only 表单；pulls router 的规则/checks route；service per-PR/per-commit check key；Checks 在 Conversation arrival 与 Checks tab 两处互斥显示。与 merge 的更新接线见候选 2。直接文件写入的保护 enforcement 由其它 cell 覆盖。 |
| REQ-6-2 父层（:2941–2954）、6-2-1（:2962）、6-2-2（:3050）、6-2-3（:3112–3132）、6-2-4（:3197–3217） | Public PR list，state/author/review组合；Write+ New link→base/compare native selects→read-only diff；同branch/no diff不可创建；Open/Draft同pair拒绝；Create按钮唯一；Draft不可review/merge，author/Maintain/Admin可Ready | routes:148–150；PullListPage URL filters、准确标题link；ComparePullsPage native labels/select、自动比较、formMode 隐藏外部Create按钮；API create→service validation+transaction、pair查重；detail Ready→重新detail GET。 |
| REQ-6-3 父层（:3273–3287）、6-3-1（:3294–3310）、6-3-2（:3395–3409）、6-3-3（:3444–3467）、6-3-4（:3523–3544） | Public detail；Conversation/Commits/Files changed/Checks 为link；diff已保存分支当前head；非作者Write+在Open可single/pending/review，added/deleted首行可直接点；pending仅本人，旧commit Outdated，最新decision生效 | PullDetailPage 的 SegmentedNav→tab；repoApi.compare→DiffView，lineExtra 的每added/deleted Add comment 真正挂在DiffLines后；single editor与review Dialog互斥，Comment label不重复；API响应更新完整detail；service保存side/line/compare commit，pending过滤、review发表与latestDecisions；当前review stale从branch head推导。 |
| REQ-6-4（:3598–3623）、6-5（:3658–3689）、6-6（:3753–3771） | author(Open/Draft)/Maintain/Admin 管reviewer请求；目标非作者Write+；Maintain/Admin仅合并eligible Open，blocked显禁用+原因，确认原子重读；author/Maintain/Admin关闭Open/Draft，Closed→Open，Merged terminal | ReviewersPanel→MetadataPicker Search option→POST/DELETE；eligible MergeArea→Dialog→merge API→transaction双parent+base更新；close/reopen API与activity完整。Draft关闭遗漏见候选3。 |

以上是静态链覆盖，**不是这些旅程已经运行通过**。原始全层级 description 已读；场景按发现定向回读（5-3-3、6-1、6-4、6-5、6-6），未宣称本 cell 逐字重读全部 scenario steps。

## 少量按影响面排序的候选

### 1. PR milestone 全链缺失（复用已证结论）

**入口→前提→动作→结果：** Triage/Maintain/Admin 打开 PR detail → 当前仓库有 milestone → 点击右侧 Milestone/option 保存或None → 页面根本无此按钮/区域，无法完成旅程。

- 原需求 `requirements.yaml:2702`，场景`:2714–2734`明确 issue **or pull request**。
- 交付：PullDetailPage:742–752 的 aside 仅 ReviewersPanel/ReviewsSummary；`frontend/src/features/pulls/` 与 `backend/src/modules/pulls/` 无 milestone 路径。Issue 的 `IssueDetailPage:328–366`/issues router milestone/`issue_milestones` 不为PR提供可达能力。
- 过程直接证据：N6:65 知道 M5未实现PR UI；:67 实际读原需求；:68 仍按M5/REQ-5编号排除。根#231→M6a#235、根#305→M6b#308→根#313 的全文/来源和同期裁决复用 `i11-e68661975b53.md`；本 cell 回读 N6上述行，未补造 PR23 native。
- 反证：Issue milestone 有完整button→option→API→repo约束→持久化，故不是全局 milestone 不会做。历史 `e2e/issues.spec.ts:465–495` 仅走Issue，与两个对象的需求不等价。
- **静态确证**；无新行为复现；**未知评分贡献**。

### 2. Checks Save 不更新当前页 merge gate，单功能成功与连续旅程断开

**入口→前提→动作→结果：** Admin 打开受保护Open PR，非作者approval满足、无冲突，唯一阻塞为test pending → Checks选择success并Save → check文本与存储变success，但Merge仍disabled并显示旧check原因，不能在当前页继续合并。反向success→failure时按钮仍可保持enabled/旧confirmation条件，最终服务端拒绝。

- 要求：REQ-6父层`:2830–2835` 页面随上下文一致；6-1`:2855` check参与后续资格；6-5`:3658–3689` eligible按钮/blocked原因与实际条件一致。这里是跨组件状态一致性缺口；并不声称任一独立指定场景必然先做此组合。
- 初始 snapshot：PullDetailPage:276–294 `pullApi.detail`取得`detail.merge`，effect只依赖 owner/name/number/repositoryState.status/user.id。服务 `pulls/service.js:863–872`每次detail GET重算mergeGate。
- 保存链：PullChecks:40–49 → `pulls/api.ts:350–353` PUT `/checks/test`，只返回`check`；pulls router 的checks PUT只`res.json({check:setCheckStatus(...)})`。service:140–156将当前compare commit键持久写入。
- 消费断点：PullDetailPage:**497** `onCheckChanged`只构造`{...current, checks:check}`，`merge`保留。`tab`变化也不在上述detail effect依赖中；Checks tab与Conversation各自同回调（:738、:810）。MergeArea:202–214读取`gate.eligible`/旧reasons；母页:650–659传`detail.merge`。diff effect因detail变化重跑不刷新merge。
- **反证/限损：** page reload重新GET detail即可恢复；其它完整detail mutation（review/close/ready）也可能间接刷新。service:737–778每次重算gate，mergePull:797–809事务前后独立重读；故旧enabled不证明越权或错误合并。前端snapshot错误仍影响按钮与解释。
- 自验边界：`e2e/pulls.spec.ts:129–150`保存后只断言test success/setter，:142立即reload，再以API查commit一致性；不检查Save后Merge按钮。`e2e/reviews.spec.ts:244–261`直接goto **已预置approval+success** 的eligible PR才检查enabled/conditions。不是观察到某个失败被删除，而是两条分离旅程及reload没有覆盖连续状态更新。未执行它们。
- 过程归属：M6a packet `docs/task-packets/m6a-issue-9.md:88–90`拥有Checks，M6b packet `m6b-issue-10.md:90–105`增加merge snapshot。当前材料未显示两者讨论Save后刷新契约；**未证当时为何遗漏**，不以静态成品推测模型内部原因。
- **静态确证更新链；浏览器实际呈现待授权运行验证；未知评分影响。** 最小后续行为判别为同一页面pending→success→Merge（不先reload），以及success→failure后的disabled/reasons一致性。

### 3. Draft close 后端可执行，前端无入口

**入口→前提→动作→结果：** 作者或Maintain/Admin直接打开Draft PR（现有`Draft onboarding update`或新建Draft）→放弃提案，查找Close pull request→按钮缺席。先Ready变Open可绕到关闭，但改变了状态/活动，不能替代关闭Draft本身。

- 原需求父REQ-6`:2820–2825`，6-6`:3761–3765`明确Open **or Draft**。
- PullDetailPage:380–381 的 `canClose`已经包含draft；但:638–647 Draft JSX只渲染disabled Merge和Ready，Close仅在:648–665的`state==='open'`块。`routes.tsx:150`直接访问同页，不存在另一Draft控制组件。
- `pulls/api.ts`有close调用；router独立`requireCloseActor`；service:879–895允许open/draft并transaction写状态/活动，不更新branch。权限与存储不是断点。
- 过程：N6:15的真实工具回包含“close an unmerged Open or Draft”；N6:**71**却设计“Close pull request (when Open) / Reopen (when Closed)”。最终`m6b-issue-10.md:51`写仅`{open,closed}`，与UI形状一致。可证需求在当时可见且设计缩窄；不能证明是哪段原文注意力不足导致。
- 反证：Open close/reopen是完整可达旅程，`e2e/reviews.spec.ts:317–336`只覆盖Open；Draft Ready已有独立验收，不能推出Draft关闭已验。
- **静态确证；Draft seeded可达前提确证；没有运行复现；未知官方是否覆盖此扩展状态。**

### 4. 场景初态隔离义务被解释为单份seed + 自验排序/构造；评分方隔离能力未知

**入口→前提→动作→结果候选：** 以同一seed页面完成合法mutation，后续或重复场景再打开同页 → 是否仍满足原始title/metadata/review/branch pair/eligible状态，依赖外部是否重新提供DB或另造对象。当前seed不会将该页自动恢复初态。

- 原要求：REQ-5`:2154–2159`各mutation独立Issue，6父层`:2843–2847`每scenario独立provision/restore，6-5`:3666`每seed state reuse前独立恢复。
- 确证单份：`seed/issues.js:175–220`只有#1 Improve onboarding、#2closed、#3 Original issue title；`docs/seed-data.md:105`把#3同时用于invalid edit与metadata。`seed/pulls.js:302–345` acme-docs仅4PR，`merge-lab`仅eligible/blocked/review3PR、共享main。
- 官网工作区 `backend/data/app.db`以SQLite **mode=ro**读取（未输出凭据）：issues恰好上述3行；pull_requests恰好acme-docs4 + protection-lab1 + merge-lab3。查询只证明下载时对象库存，不推断官方执行顺序。没有发现scenario/reset表也不证明必须存在这类表。
- `ensureIssue`/`ensurePull`（issues:60、pulls:159）既有行直接返回；seed注释明确保留编辑/关闭/合并。这是正确的重启持久化行为，不能简单修为启动时覆写用户数据；需要先确认场景隔离归谁负责。
- **直接过程解释**：N6:**68**读到“restored independently ... repeated and parallel”，却以“e2e fresh DB per run”及“within run once/separate PRs”解释可满足，再复用Improve onboarding作inline/approve/close，merge-lab review PR作pending/Request changes；N6:71与最终packet:123–134持续这一分配。M5 packet的“spec自建fixture”给自验构造唯一Issue，保护seed，但不自动向仅靠seed页面的外部操作方提供这些对象。
- 竞争解释/反证：外部评分器可能按场景新DB或主动构造、恢复对象；原要求没有明示必须实现scenario生命周期API。当前单份seed并不独自证明运行污染；两次成功mutation的元数据也可能互不影响，不能机械计为全部功能失败。merge成功/拒绝已分别提供PR、ready seed也独立于draft创建，有真实局部隔离改进。
- **确证的是交付seed库存及复用解释；重复/并行初态是否失败待外部生命周期证据；评分影响未知。** 此项应作为下一步核实前提，优先于添加reset API或指责所有seed不合法。

## 反证、覆盖与停止点

- Issue非累积权限已修：permissions中的ISSUE_MANAGER_ROLES是triage/maintain/admin，issues router的metadata/status真正使用；前端api:117–123镜像。Write可编辑评论但不能管理metadata，不能套用其它variant的旧越权结论。
- PR reviewer候选复用assignable-users不漏Write：issues service:468–473的 ≥Triage包含Write，ReviewersPanel再筛Write/Maintain/Admin；后端拒绝作者。前端候选未排除作者会导致可见无效选项，但已有eligible reviewer可选，未升级为高影响断点。
- 比较/创建、Draft Ready、review single/pending/latest/stale、Open close/reopen、transaction merge都追到具体UI组合、API信封、权限与持久逻辑；未发现足以声称这些全链普遍断开的证据。API存在不是运行通过。
- 已读本cell各页面、shared Menu/Button/TextField/SegmentedNav/DiffView、对应API、issues service/router、pulls service/router、seed文件与相关packet；定向读现有e2e Checks/Merge/Close与已知milestone断言，不运行。未全读历史native或PR23；N6仅按明确新缺口取证。早期大输出曾截断，关键需求description/新候选代码和引用均改为分段/定向补读；截断部分不计全量过程阅读。
- 剩余限制：官方只有汇总4/100、无逐例错误；没有授权行为复现；尚不知评分方state isolation；PR23终态native已取回，见[主报告的证据状态更正](../report.md)及其新目录；机制会话正在补审，本cell未重复读取或补造过程。此cell不能将四个候选映射到96失败，不能保证修复提分。高影响发现已即时回传主审；完成后由主审整合跨cell共因，应用/设施修复另需其授权范围。
