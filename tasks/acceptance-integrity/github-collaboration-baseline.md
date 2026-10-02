# GitHub 软件开发协作行为基准

调查日期：2026-09-27。范围为 GitHub.com 上从任务发现到代码交付、失败处理和继续协作的闭环。依据为 GitHub 官方文档、官方变更日志、公开 schema，以及只读公开 issue API。未读取 Braid 实现，未创建或修改外部资源；本文不判定 Braid 的缺口。

证据标记：**A**＝官方明确说明；**B**＝本次公开实例直接观察，只证明该实例；**I**＝依据已确认事实作出的推断；**U**＝尚未确认。表内“可能通知”指具备接收资格，仍受订阅、权限和渠道设置影响，不能解释为每个收件人一定收到或阅读。

## 先回答关键问题：sub-issue 关闭、重开如何影响父项

**可以确认子项完成会更新父项进度；不能把这个事实写成“父项必定新增关闭事件并通知父项参与者”。本次三个仓库的样本中，建立关系之后关闭子项，没有在父项 REST 时间线新增对应的子项关闭事件。**

| 问题 | 结论和证据 |
| --- | --- |
| 建立、移除父子关系有历史吗？ | **A＋B**。GraphQL 提供 `SubIssueAddedEvent`、`SubIssueRemovedEvent`、`ParentIssueAddedEvent`、`ParentIssueRemovedEvent`；本次 REST 样本也返回这些事件。父项记录子项的加入/移除，子项记录父项关系。[GraphQL Issues](https://docs.github.com/en/graphql/reference/issues#subissueaddedevent) |
| 子项关闭会改变父项进度吗？ | **A**。GitHub 工程文章明确描述子项完成时更新父项进度。父项列表和 Projects 的进度字段提供聚合视图。[官方实现说明](https://github.blog/engineering/architecture-optimization/introducing-sub-issues-enhancing-issue-management-on-github/)、[进度字段](https://docs.github.com/en/issues/planning-and-tracking-with-projects/understanding-fields/about-parent-issue-and-sub-issue-progress-fields) |
| 子项关闭会在父项新增时间线事件吗？ | **B**。下方四个子项的关闭事件均只在自己的完整 REST 时间线中出现。**U**：没有找到官方承诺其在所有版本、所有 UI 中绝不显示。公开 `IssueTimelineItems` union 没有专门的 `SubIssueClosedEvent`，这是辅助证据，单靠类型缺席不能证明所有 UI 行为。[完整 union](https://docs.github.com/en/graphql/reference/issues#issuetimelineitems) |
| 子项重开呢？ | 子项自己的 `ReopenedEvent` 为 **A**；按当前状态计算父项进度应相应回退为 **I**。本次没有取得合适的“先建立关系、后重开”的实例，父项新增历史和父项通知均为 **U**。[重开事件](https://docs.github.com/en/graphql/reference/issues#reopenedevent) |
| 父项 author/assignee/subscriber 会因子项关闭、重开收到通知吗？ | **U**。未找到明确官方收件人规则；公开时间线不能证明私人的通知收件箱。不能从父子关系推导自动订阅继承，也不能因未见父时间线事件就断言一定没有通知。若用户另外订阅子项或 watch 子项所在仓库，其通知资格来自这些关系。[订阅定义](https://docs.github.com/en/subscriptions-and-notifications/concepts/about-notifications) |
| 所有子项关闭会自动关闭父项吗？ | 未找到这种默认规则的官方保证。样本中父项有独立关闭时间和操作记录。以“进度完成”和“父 issue 状态关闭”为两个状态处理，不能把进度当自动关闭承诺。**B＋U**。 |

### 可复查的只读实例

本次对每个 issue 请求 `GET /repos/{owner}/{repo}/issues/{number}/timeline?per_page=100`。下列父项完整结果分别为 33、17、20 项，均无下一页 `Link`。比较的是所有返回事件，再检查关闭时间；不是只看首屏截图。时间均为 UTC。

| 父项 → 子项 | 建立关系 | 子项关闭 | 父项观察 |
| --- | --- | --- | --- |
| [zeph #762](https://github.com/bug-ops/zeph/issues/762) → [#764](https://github.com/bug-ops/zeph/issues/764) | 2026-02-23 20:12:31 | 20:28:41 | 父项有 `sub_issue_added`，没有该关闭时刻的子项关闭事件。 |
| 同父项 → [#770](https://github.com/bug-ops/zeph/issues/770) | 2026-02-23 20:13:25 | 22:07:02 | 同上；父项自己到 23:12:08 才关闭。 |
| [riku #1](https://github.com/fskroes/riku/issues/1) → [#12](https://github.com/fskroes/riku/issues/12) | 2026-07-20 09:49:42 | 13:06:59 | 父项自己 13:07:01 关闭，没有子项关闭事件。 |
| [ag2 #2020](https://github.com/ag2ai/ag2/issues/2020) → [#2036](https://github.com/ag2ai/ag2/issues/2036) | 2025-08-15 18:28:09 | 2025-08-17 14:36:32 | 父项自己 2025-08-18 17:45:40 关闭，没有子项关闭事件。 |

直接核查入口：[zeph 父时间线](https://api.github.com/repos/bug-ops/zeph/issues/762/timeline?per_page=100)、[子 #764](https://api.github.com/repos/bug-ops/zeph/issues/764/timeline?per_page=100)、[子 #770](https://api.github.com/repos/bug-ops/zeph/issues/770/timeline?per_page=100)；[riku 父时间线](https://api.github.com/repos/fskroes/riku/issues/1/timeline?per_page=100)、[子时间线](https://api.github.com/repos/fskroes/riku/issues/12/timeline?per_page=100)；[ag2 父时间线](https://api.github.com/repos/ag2ai/ag2/issues/2020/timeline?per_page=100)、[子时间线](https://api.github.com/repos/ag2ai/ag2/issues/2036/timeline?per_page=100)。这些是可变的在线资源，事件数量可能随未来活动增加。

另一个容易误读的证据是 GitHub Mobile 的 2025-04 公告：“Issue timelines now include events related to sub-issues.” 它没有列出关闭或重开，不能扩大解释为子项所有活动都会复制到父项。[Mobile 公告](https://github.blog/changelog/2025-04-21-mobile-monthly-aprils-general-availability-and-more/)

## 一、任务发现、分工与依赖

通知列的通用收件人基础：当前对象的 author、assignee、已参与者通常已自动订阅；手动 subscriber 和相应 watcher 也可能接收更新。后文单独列出退出和例外。元数据事件是否发通知若无明文，则保留未知。

| 协作动作及作用 | 持久状态／可见历史 | 默认通知及例外 | 如何继续工作；证据 |
| --- | --- | --- | --- |
| 创建 issue：把需求、问题或验收条件变成可引用的工作对象 | 编号、URL、作者、正文、创建时间；可应用模板、标签和 assignee。创建对象不等于必须存在一个名为 `opened` 的 issue timeline 条目。 | 作者默认订阅；已指定 assignee、有效 @ 对象、watch Issues 的用户有相应接收路径。 | 从 issue 正文、评论和侧栏进入上下文。**A**：[创建 issue](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/creating-an-issue)、[默认订阅](https://docs.github.com/en/subscriptions-and-notifications/concepts/about-notifications) |
| 标签分类：区分 bug、功能、求助、团队约定的紧急程度 | 标签是仓库内元数据，可修改；应用/移除有 `labeled`/`unlabeled` 历史。 | 标签存在或变化不能单独推出全部订阅者必收通知。**U**：精确通知矩阵。 | 用标签筛选待办；标签本身不是强制执行顺序。**A**：[管理标签](https://docs.github.com/en/issues/using-labels-and-milestones-to-track-work/managing-labels)、[事件类型](https://docs.github.com/en/rest/using-the-rest-api/issue-event-types) |
| 里程碑、优先级和计划：共同表达“先做什么、何时完成” | Milestone 聚合 issue/PR、截止日期、完成百分比并可排序；Projects 可用自定义 priority、iteration 等字段组织工作。 | **U**：每种计划字段变化的用户通知；不能把排序等同于指派。 | 从 milestone 列表和 project 过滤、分组视图挑选工作。**A**：[Milestones](https://docs.github.com/en/issues/using-labels-and-milestones-to-track-work/about-milestones)、[Projects 实践](https://docs.github.com/en/issues/planning-and-tracking-with-projects/learning-about-projects/best-practices-for-projects) |
| 分配、取消分配：显示谁负责 | assignee 集合改变，timeline 有 `assigned`/`unassigned`；可多人负责。权限决定谁可执行操作。 | 被分配者默认订阅并有 `assign` 通知原因。**U**：取消分配是否一定通知该人、是否自动移除既有订阅，官方资料未充分规定。 | 按 assignee 搜索回到任务，查看正文和交接评论。**A/U**：[分配](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/assigning-issues-and-pull-requests-to-other-github-users)、[事件类型](https://docs.github.com/en/rest/using-the-rest-api/issue-event-types)、[默认订阅](https://docs.github.com/en/subscriptions-and-notifications/concepts/about-notifications) |
| 普通评论、@ 人或团队：澄清需求、汇报进展、请求决定 | 评论进入当前 issue/PR 的 conversation，有独立链接；@ 可以在新评论或编辑评论时加入。 | 当前 conversation 的有效订阅者可能接收；评论者和被 @ 者默认参与并订阅。@ 受访问资格限制；不能通知无权阅读的对象。 | 通知指向当前对象及评论；回复前可读完整 conversation。**A**：[评论 API](https://docs.github.com/en/rest/issues/comments)、[@ 规则](https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax#mentioning-people-and-teams) |
| 引用另一个 issue/PR：把问题、方案、重复项联系起来 | `#number` 或 URL 提供跳转；跨引用可进入被引用对象的 `cross-referenced` 时间线；与父子、依赖、自动关闭关系分别建模。 | **U**：每种跨引用是否通知被引用对象所有订阅者，不能从可见引用推导。 | 沿引用回到原问题及讨论；检查引用是否只是背景，还是明确的 closing link。**A**：[事件类型](https://docs.github.com/en/rest/using-the-rest-api/issue-event-types#cross-referenced)、[PR 关联规则](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/linking-a-pull-request-to-an-issue) |
| 建立／移除 sub-issue：拆分范围，保留上下级导航 | 父子双向关系事件、父项子列表、进度；子项仍有自己的正文、状态和评论。 | **U**：关系操作的确切默认通知；未确认父项订阅自动继承到子项。 | 父页展开子层级，子页标题下返回父项。**A**：[添加子项](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/adding-sub-issues)、[浏览层级](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/browsing-sub-issues) |
| 建立／移除阻塞关系：显示开展工作的前提 | `blocked by`／`blocking` 双向可查询；列表和项目板显示 Blocked 标记；GraphQL 有对应关系事件。 | **U**：上游完成是否自动通知下游所有责任人；官方说明未提供足够保证。 | 沿 Relationships 找到前提事项，判断是否能继续。依赖与范围拆分是不同关系。**A**：[依赖操作](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/creating-issue-dependencies)、[GraphQL Issues](https://docs.github.com/en/graphql/reference/issues) |
| 关闭／重开 issue：记录工作结论或恢复待办 | 状态与关闭原因变化，timeline 记录 `closed`／`reopened`。关闭可以表示完成，也可以表示不计划做。 | 订阅当前 issue 的用户可能接收状态更新；操作状态者默认订阅。**U**：跨父子、依赖的额外通知。 | 阅读关闭原因及评论；重开后继续同一历史，必要时重新分配、@ 交接。**A**：[关闭 issue](https://docs.github.com/en/issues/tracking-your-work-with-issues/administering-issues/closing-an-issue)、[邮件状态通知](https://docs.github.com/en/subscriptions-and-notifications/reference/email-notification-headers)、[事件类型](https://docs.github.com/en/rest/using-the-rest-api/issue-event-types) |

责任、权限和关注度是不同维度。assignee 表达责任，repository role 决定操作权限，subscription 决定接收范围；三者不能互相替代。组织仓库区分 Read、Triage、Write、Maintain、Admin，组织基础权限和自定义角色还可能改变有效权限。**A**：[仓库角色](https://docs.github.com/en/organizations/managing-user-access-to-your-organizations-repositories/managing-repository-roles/repository-roles-for-an-organization)

## 二、从变更提出到 review、验证和集成

| 协作动作及作用 | 持久状态／可见历史 | 默认通知及例外 | 如何继续工作；证据 |
| --- | --- | --- | --- |
| 从 issue 建 branch，并提交代码：把执行产物连接到任务 | Development 可显示关联 branch；从该分支创建 PR 后转为 PR 关联。提交有 SHA，PR 提供 commits 和 diff。 | **U**：建 branch 是否通知所有 issue 订阅者。PR pushes 的邮件接收可配置，不能当作普通 issue 评论通知。 | 从 issue 到 branch/PR，再看具体 commit/diff。建 branch 的 UI 当前官方仍标 preview。**A**：[从 issue 建分支](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/creating-a-branch-for-an-issue)、[通知设置](https://docs.github.com/en/subscriptions-and-notifications/get-started/configuring-notifications) |
| 创建 PR、draft→ready：提出待集成变更并交接评审 | PR 保存 base/head、正文、commits、diff、conversation；draft 不可合并，ready 后可进入正式 review。 | PR 作者默认订阅；配置 CODEOWNERS 时，ready 会请求代码所有者评审。改回 draft 不会退订现有订阅者。 | 通过 Conversation、Commits、Checks、Files changed 理解动机、代码及验证情况。**A**：[PR 视图](https://docs.github.com/en/pull-requests/reference/pull-requests)、[阶段切换](https://docs.github.com/en/pull-requests/how-tos/create-pull-requests/changing-the-stage-of-a-pull-request) |
| 将 PR 关联 issue：让需求与实现双向可发现 | closing link 出现在 Development；普通引用与能关闭 issue 的关联不同。关联/解除可有 `connected`/`disconnected` 历史。 | **U**：只因为 issue 被关联，issue 的全部参与者是否自动订阅该 PR；无此保证。 | 从任一对象进入另一对象检查需求与实现。`Fixes #N` 等正文关键字仅在 PR 目标为默认分支时解释。**A**：[关联 issue](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/linking-a-pull-request-to-an-issue) |
| 请求／再次请求 review：把下一步明确交给评审者 | requested reviewer/team 可见；时间线有 `review_requested`、`review_request_removed` 等记录。 | 被请求的用户或团队收到请求通知；有 `review_requested` 原因。自动 code-owner 请求依赖 CODEOWNERS。**U**：仅移除请求是否退订或向全体通知。 | Reviewer 从请求进入 PR；修订后作者可再次请求同一人复审。**A**：[请求 review](https://docs.github.com/en/pull-requests/how-tos/create-pull-requests/requesting-a-pull-request-review)、[CODEOWNERS](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners) |
| 单条 review 评论／批量 review：对具体文件、行给反馈 | Review comments 附着 diff，形成可回复的 review conversation；pending review 仅作者可见，提交后发布。 | 发布评论会通知 watch 该 PR/仓库的人；批量提交避免逐条发通知。pending 不能当作已交接。 | 从评论跳到代码和所属 review，理解上下文后回复或修改。**A**：[PR 评论](https://docs.github.com/en/pull-requests/how-tos/review-pull-requests/commenting-on-a-pull-request)、[提交 review](https://docs.github.com/en/pull-requests/how-tos/review-pull-requests/reviewing-proposed-changes-in-a-pull-request) |
| Approve／Request changes／Comment：明确评审结果 | 持久 review 状态与汇总评论；review 出现在 PR timeline。 | 已发布 review 触发通知；PR 作者、有效订阅者具备接收路径，渠道受偏好影响。 | 作者处理反馈，评审者复审。Request changes 是否阻止合并取决于保护策略；Approve 本身不执行 merge。**A**：[review 语义](https://docs.github.com/en/pull-requests/how-tos/review-pull-requests/reviewing-proposed-changes-in-a-pull-request)、[reviews API](https://docs.github.com/en/rest/pulls/reviews) |
| 解决 review thread：标识某个局部讨论已处理 | 对话折叠为 resolved；Conversations 菜单可找 unresolved、resolved、outdated。 | **U**：resolve/unresolve 每次的精确收件人和通知条件。 | 保留原评论与代码联系；局部线程 resolved 不等于整个 PR approved。是否要求全部解决后合并可配置。**A**：[解决对话](https://docs.github.com/en/pull-requests/how-tos/review-pull-requests/commenting-on-a-pull-request#resolving-conversations)、[保护规则](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches) |
| Checks／CI：把验证结果反馈给作者与集成人 | Commit statuses 提供简要状态；Checks 可包含日志、注解、结果及详细链接。PR merge box 显示阻碍条件。 | workflow 通知是独立设置；开启后触发 run 的人可收到完成通知，可只收失败。不能认为所有 PR 订阅者默认收到每个 check 的变化。 | 从 PR Checks/注解进入失败日志，修改或重跑。**A**：[Checks](https://docs.github.com/en/pull-requests/reference/status-checks)、[workflow 通知](https://docs.github.com/en/actions/concepts/workflows-and-actions/notifications-for-workflow-runs) |
| 评审、检查成为合并门槛：确保集成前达到团队条件 | 可配置 required reviews/checks、conversation resolution、最新 push 审批、旧批准失效、merge queue 等。是否允许 bypass 也由策略决定。 | 门槛状态可见不等于向所有人广播新通知；具体事件仍走各自通知规则。 | 作者和合并者查看当前 head 对应的缺失条件，补齐后再集成。**A**：[保护分支](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches) |
| 处理冲突：决定并发修改的最终内容 | 冲突阻止 GitHub merge；解决并提交后更新 head。简单行冲突可在线处理，复杂冲突需本地解决。 | **U**：出现／消失冲突是否总通知责任人；不要把 mergeable 状态变化当已完成交接。 | 在 PR merge box 看冲突，查冲突文件；解决后重新验证变更。**A**：[冲突规则](https://docs.github.com/en/pull-requests/reference/merge-conflicts)、[在线解决](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/resolving-a-merge-conflict-on-github) |
| Merge：把审核后的变更集成到 base | PR 变为 merged，记录合并者、时间、commit；仓库可允许 merge commit、squash、rebase。 | PR 当前订阅者可接收状态更新。合并者默认订阅。满足 closing-link 规则时，issue 独立关闭并走 issue 状态通知。 | 从 PR 回到集成 commit 与被解决任务。**A**：[合并](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/merging-a-pull-request)、[合并策略](https://docs.github.com/en/pull-requests/reference/pull-request-merges)、[自动关 issue](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/linking-a-pull-request-to-an-issue) |
| Close PR、重开任务、revert：记录取消与失败恢复 | 未合并 PR 可关闭；issue 可重开。GitHub 的 revert 操作创建一条新的撤销 PR，保留原集成历史。 | 当前对象的状态/评论按其订阅通知；新撤销 PR 是独立协作对象。**U**：revert 是否自动重开原 issue，不能假定。 | 查看原 PR、失败原因、撤销 diff，再明确分配和 review 请求。**A**：[关闭与合并入口](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests)、[Revert](https://docs.github.com/en/enterprise-cloud%40latest/pull-requests/how-tos/merge-and-close-pull-requests/reverting-a-pull-request) |
| CI 失败后诊断／重跑：区分代码问题和执行故障 | Run 与 job 保留结果和日志，日志行可分享链接；重跑仍使用原事件的 SHA/ref。 | 同 workflow 通知设置；可按失败过滤。 | 查失败 step，决定修代码产生新 SHA，或在同 SHA 上重跑。**A**：[日志](https://docs.github.com/en/actions/how-tos/monitor-workflows/use-workflow-run-logs)、[重跑](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/re-run-workflows-and-jobs) |

交付状态还需要保留语义边界：merged 表示进入目标分支，issue closed 可能表示完成或不计划处理，它们本身都不能证明已部署给最终用户。GitHub 可以提供进一步的 release 线索；2026-04 的改进在关联 issue 的 Development 区域显示包含该 PR 的首次 release（可用时）。**A**：[Release 侧栏](https://github.blog/changelog/2026-04-09-release-info-in-issue-sidebar-and-project-defaults/)。本文未扩展到部署执行引擎。

## 三、参与者、订阅者与通知边界

### 谁会继续收到后续更新

| 角色／动作 | 已确认规则 | 不能推导的规则 |
| --- | --- | --- |
| Author | 开 issue/PR 默认订阅该 conversation。 | 作者不是不可退订的永久收件人。 |
| Assignee | 被分配默认订阅；`assign` 是通知原因之一。 | 当前 assignee 列表不是所有订阅者列表；取消分配的自动退订行为未确认。 |
| Commenter／改变状态者 | 评论、关闭 issue、合并 PR 等可使操作者默认订阅。 | 一次历史参与不能覆盖后来主动退订或 ignore。 |
| 被 @ 的人或团队成员 | 有效 @ 触发关注并默认订阅；编辑评论补 @ 也可通知。 | @ 不突破资源访问限制。官方格式文档还列出组织成员条件，跨组织／outside collaborator 的边界应按实际资格核查。 |
| 手动 subscriber | Subscribe 订阅当前 conversation。 | 不能推出其订阅了父项、子项、引用对象或关联 PR。 |
| Repository watcher | 可以 watch 全部，或只选 Issues、PR 等类型；相应对象更新进入接收范围。 | Star、仓库可访问、仅加入组织都不能等同于当前 watch。 |
| Review requested | 请求对象收到专门 review 请求，通知有相应 reason。 | 不代表已经 review、已经接受工作、或会执行修改。 |

上述默认订阅依据：[About notifications](https://docs.github.com/en/subscriptions-and-notifications/concepts/about-notifications)；角色原因依据：[通知 API](https://docs.github.com/en/rest/activity/notifications#about-notification-reasons)；@ 资格依据：[Mentioning people and teams](https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax#mentioning-people-and-teams)；watch 范围依据：[通知设置](https://docs.github.com/en/subscriptions-and-notifications/get-started/configuring-notifications)。均为 **A**，表中保留的未知为 **U**。

**版本冲突要单列。** About notifications 仍提到加入仓库／团队时自动 watch；但官方 2025-04-15 退役公告明确宣布 2025-05-23 起弃用 automatic watching，已有自动产生的订阅保留。本基准按有明确日期的公告，不把新加入仓库自动 watch 当作当前 GitHub.com 必然行为。GHES 要核对具体版本。[退役公告](https://github.blog/changelog/2025-04-14-sunset-notice-for-automatic-watching-of-repositories-and-teams/)

### 退订、偏好、渠道与已读

- **退订可改变后续接收。** 官方说明，退订后再次参与、再次被 @ 或所在团队被 @ 可以重新订阅。单对象还可以 Custom 只接收某些状态更新。**A**：[退订后的恢复](https://docs.github.com/en/subscriptions-and-notifications/tutorials/customizing-a-workflow-for-triaging-your-notifications)、[单对象自定义](https://docs.github.com/en/subscriptions-and-notifications/how-tos/viewing-and-triaging-notifications/triaging-a-single-notification)。
- **接收资格和投递渠道分别配置。** Web/Mobile inbox、Email 和 Mobile push 不是一个保证；邮件还受验证地址和组织域要求影响，自身操作通知也可配置。**A**：[通知设置](https://docs.github.com/en/subscriptions-and-notifications/get-started/configuring-notifications)。官方 inbox 使用说明与配置页对是否必须同时开 Email/On GitHub 的措辞存在差异，本报告不把该细节写成统一硬规则。
- **notification thread 是更新聚合，不是每条 timeline 事件的副本。** REST 提供 `subject`、`unread`、`updated_at`、`last_read_at`；`reason` 会在同一 thread 中变化并保持，例如作者后来被 @ 后 reason 可以保持 mention。它不能用来重建每次事件的真实触发原因。**A**：[Notifications API](https://docs.github.com/en/rest/activity/notifications)。
- **已读不证明已行动。** API 可以直接把通知标为 read；收件箱还区分 Done、Save 和 Unsubscribe。由此只能知道通知整理状态，不能推导代码已修改、review 已完成或任务已接手。前半为 **A**，后一判断为 **I**。[通知 API](https://docs.github.com/en/rest/activity/notifications)、[收件箱处理](https://docs.github.com/en/subscriptions-and-notifications/how-tos/viewing-and-triaging-notifications/managing-notifications-from-your-inbox)。
- **邮箱 reason 和 REST reason 不宜直接混用。** 邮件文档把 `state_change` 描述为已订阅对象被关闭或打开；REST 将其描述为用户改变了 thread 状态。消费方应以各接口自己的契约为准，不能把同名字段当完全相同语义。**A**：[邮件 headers](https://docs.github.com/en/subscriptions-and-notifications/reference/email-notification-headers)、[REST reasons](https://docs.github.com/en/rest/activity/notifications#about-notification-reasons)。

## 四、普通 issue 评论与 PR review thread 的区别

| 对象 | 上下文及状态 | 通知层面的结论 |
| --- | --- | --- |
| Issue 普通评论、PR Conversation 普通评论 | 归属同一个 issue/PR conversation，保存正文和评论链接。PR 的普通评论也使用 issue comments API。 | 当前 conversation 的参与／订阅关系持续有效；没有找到“加一条新的普通评论会创建隔离 thread，屏蔽早前参与者”的 GitHub 规则。 |
| PR review comment/thread | 附着具体 diff 文件／行；可回复、resolved/outdated；所属 review 还有 pending/submitted 和 approval 等状态。 | 官方明确发布评论会通知 watch PR/仓库的人。因此“新 review thread 必定只通知此线程新参与者”也不成立。详细的低噪声优化、单个回复精确收件人未逐项实测，保留 U。 |
| Notifications API thread | 指向 issue、PR 或 commit 的通知聚合。 | 不能因 API 都叫 thread，就把它等同于一条 review conversation，更不能等同于 agent 会话。 |

**A／I** 依据：[Issue comments API](https://docs.github.com/en/rest/issues/comments)、[PR 评论与通知](https://docs.github.com/en/pull-requests/how-tos/review-pull-requests/commenting-on-a-pull-request)、[Notifications API](https://docs.github.com/en/rest/activity/notifications)。特别注意：邮件回复 PR 会成为 Conversation 普通评论，不作为 review 的一部分，不能假定回复落在原代码线程。

因此，对“同一 issue 因出现新 thread，早前参与者不再收到通知”的说法，当前结论是：**缺乏 GitHub 事实支持，且与其 conversation 订阅模型不符。** 如果实际出现未通知，应分别核查是否换成另一个 issue/PR、是否退订、自定义通知、权限、渠道或尚未提交 review；这些是待验证解释，不是对某次故障的诊断。

## 五、历史检索与再次接手

正常协作不是只依赖推送。GitHub 保留几条互补的上下文入口：

1. Issue 的正文、评论与时间线解释需求、决定和责任变化；引用、父子和依赖链接指向相邻工作。
2. PR 的 Conversation、Commits、Checks、Files changed 让接手者从动机走到实现、验证和未解决反馈；review 可从时间线追踪。**A**：[PR 视图](https://docs.github.com/en/pull-requests/reference/pull-requests)、[解决 review](https://docs.github.com/en/pull-requests/concepts/resolving-reviews)。
3. Issues/PR 搜索支持 assignee、author、mentions、involves、label、milestone、state、linked 等条件；项目视图可按 parent 和 close reason 过滤。这使责任人能从当前工作状态重新发现任务。**A**：[搜索筛选](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/filtering-and-searching-issues-and-pull-requests)、[项目过滤](https://docs.github.com/en/issues/planning-and-tracking-with-projects/customizing-views-in-your-project/filtering-projects)。
4. 通知 inbox 可按 reason、仓库和状态整理，也可以跳回原对象；它服务注意力管理。工作结论应落在 issue/PR/review/check 等对象中。前半为 **A**，后半是 **I** 的协作建议。[Inbox filters](https://docs.github.com/en/subscriptions-and-notifications/reference/inbox-filters)。

## 六、供后续对照的原则与明确未知

以下是从事实抽出的比较标准，属于**推断／建议**，并非 Braid 实现结论：

- 保留从需求、责任、实现、评审、验证到集成结果的可导航链路，参与者才能在离开一段时间后继续工作。
- 区分六件事：业务状态改变、历史可见、订阅成立、产生通知、通知被标已读、接收者实际采取行动。任何前一件都不充分证明后一件。
- 将“请求某人处理”做成有对象和上下文的协作动作。assignee、@、review request、changes requested 分别有不同作用，不能只看评论文本是否出现“完成”。
- 分别比较范围关系、阻塞关系和关闭关系：sub-issue、blocked-by、PR closing link 的因果语义不同。
- 审核与验证必须能指向当前变更，并让接手者看到尚未满足的条件；是否强制门槛由团队策略决定。
- GitHub 的普通人类通知语义不保证启动执行者、按时响应或自动恢复父任务。GitHub Copilot 等产品有额外明确的 agent 执行动作，那是专门功能，不能反推普通 issue 通知的调度承诺。[Copilot 分配说明](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/assigning-issues-and-pull-requests-to-other-github-users#assigning-an-issue-to-copilot)

仍然未知且可能影响对照的事项：

| 未知 | 目前不能做的推断 | 最小的后续验证方法（如确有决策需要） |
| --- | --- | --- |
| 子项关闭／重开对仅订阅父项者的通知 | 不能承诺通知，也不能以父 timeline 没事件断言不通知。 | 用两个有明确订阅和渠道设置的测试账号，在专用测试仓库观察双方通知 API／收件箱；另设仅订阅子项的对照。 |
| 子项重开对父项时间线／进度的精确表现 | 不能把关闭样本直接当重开实测。 | 优先找关系建立后重开的公开完整时间线，必要时做隔离实验。 |
| 关系、引用、取消分配、resolve 等元数据操作的精确收件人 | 不能把所有 timeline 事件广播给所有参与者当成 GitHub 原样行为。 | 按动作逐个验证，记录事件、订阅、notification 和渠道四份证据。 |
| 跨对象订阅继承及其特殊情况 | 父 issue、子 issue、关联 PR、撤销 PR 的订阅不能先假定互通。 | 使用仅订阅单个对象的账号验证，避免 watcher 覆盖造成假阳性。 |
| 文档未覆盖的通知优化与版本差异 | 不把文档的概括性“会通知”解释成每条评论一封邮件或所有端一致。 | 核对具体 GitHub.com／GHES 版本、API 版本、账户配置和时间。 |

这些验证需要额外的测试身份和受控写入环境；本轮按只读边界完成调查，没有启动这些实验。
