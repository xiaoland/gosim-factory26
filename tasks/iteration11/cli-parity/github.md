# GitHub CLI 行为基线

## 范围与证据

本报告独立整理 GitHub CLI，不涉及其他 CLI 的实现或差异。覆盖 `issue` 与 `pr` 的 create、view、list、edit、comment、close、reopen，以及仅属于 `pr` 的 merge、ready。

本机实际执行的版本查询结果是 **`gh version 2.89.0 (2026-03-26)`**。实际执行范围仅为版本与 help：16 个子命令的 `--help`，父命令帮助，以及 formatting、exit-codes、environment 帮助。没有执行真实 issue/PR 查询或修改，没有创建远端对象、运行测试或探针。下文的运行行为来自该版本源码阅读，不冒充服务端实测。

证据分三层：

- **本机 help**：[`github-evidence/`](github-evidence/) 保存原始输出；用于确认本机暴露的参数、字段和文档默认值。
- **同版本源码**：从 GitHub CLI 官方仓库 `v2.89.0` tag 下载，保存于 [`github-evidence/source/`](github-evidence/source/)；用于核实分支、输出通道、参数冲突和调用顺序。[版本发布页](https://github.com/cli/cli/releases/tag/v2.89.0)。
- **在线官方手册**：已联网核对 [issue](https://cli.github.com/manual/gh_issue)、[pr](https://cli.github.com/manual/gh_pr)、[issue edit](https://cli.github.com/manual/gh_issue_edit)、[pr merge](https://cli.github.com/manual/gh_pr_merge)、[exit codes](https://cli.github.com/manual/gh_help_exit-codes)。在线手册滚动更新，不作为固定版本实现的替代证据。

[`collection.json`](github-evidence/collection.json) 记录采集入口和下载清单。报告中的源码链接均固定到 `v2.89.0`。本次没有验证具体仓库权限、GitHub.com/GHES 版本差异及服务端策略；涉及这些前提的结论明确保留边界。

## 命令形状与默认输出

以下“终端”指 stdout 被识别为 TTY；重定向、管道及 `GH_FORCE_TTY` 会改变分支。所有命令都有 `--help` 与继承的 `-R/--repo [HOST/]OWNER/REPO`。编号属于仓库，不能脱离仓库上下文当作全局 ID。省略仓库通常使用本地仓库上下文，也可由 `GH_REPO` 指定。

| 命令 | 位置参数与默认选择 | 默认行为、成功输出及主要副作用 |
| --- | --- | --- |
| `issue create` | 不接受位置参数；别名 `new` | 创建 issue；缺标题/正文时交互询问；成功 URL 到 stdout。可同时设置 assignee、label、project、milestone。 |
| `issue view` | 必须一个编号或 URL | stdout 显示详情；终端渲染 Markdown，管道输出元数据行与原始正文。支持 `--comments`、`--web`、JSON。 |
| `issue list` | 不接受位置参数；别名 `ls` | 默认 open、最多 30 条；stdout 列表。支持筛选、搜索、web、JSON。 |
| `issue edit` | 一个或多个编号/URL，必须同仓库 | 修改选定字段；成功对象的 URL 到 stdout。多个 issue 并行更新，可能部分成功。 |
| `issue comment` | 必须一个编号或 URL | 默认新增普通评论；成功评论 URL 到 stdout。可编辑/删除当前用户最后一条评论。 |
| `issue close` | 必须一个编号或 URL | 关闭；可先发评论；状态摘要到 stderr。支持 reason 和 duplicate-of。 |
| `issue reopen` | 必须一个编号或 URL | 重新打开；可先发评论；状态摘要到 stderr。 |
| `pr create` | 不接受位置参数；别名 `new` | 创建 PR，成功 URL 到 stdout；流程可能 fork、push Git 分支。 |
| `pr view` | 最多一个编号/URL/分支；省略时当前分支关联 PR | stdout 详情；支持 comments、web、JSON。 |
| `pr list` | 不接受位置参数；别名 `ls` | 默认 open、最多 30 条；stdout 列表。 |
| `pr edit` | 最多一个编号/URL/分支；省略时当前分支关联 PR | 修改选定字段，成功 PR URL 到 stdout；可改 base、reviewer 等元数据。 |
| `pr comment` | 最多一个编号/URL/分支；省略时当前分支关联 PR | 普通会话评论；成功评论 URL 到 stdout。 |
| `pr close` | **必须**一个编号/URL/分支 | 关闭 PR；可先发评论，并可删除本地/远端分支；摘要到 stderr。 |
| `pr reopen` | **必须**一个编号/URL/分支 | 重新打开已关闭 PR；merged PR 不能通过此命令重新打开。 |
| `pr merge` | 最多一个编号/URL/分支；省略时当前分支关联 PR | 立即合并、启用自动合并、加入队列或关闭自动合并，取决于参数和服务端状态。普通成功摘要仅终端输出到 stderr。 |
| `pr ready` | 最多一个编号/URL/分支；省略时当前分支关联 PR | 默认把草稿改为待评审；`--undo` 转回草稿；状态摘要到 stderr。 |

`issue` 没有 `merge` 或 `ready` 子命令。PR 参数中的分支选择可包含 `OWNER:branch`，但不能推广到所有同名 flag：`pr list --head` 明确不支持该形式。`pr view/comment/merge/ready` 在指定 `--repo` 且未给位置参数时，构造阶段明确报 `argument required when using the --repo flag`；`pr edit` 没有这条同样的构造检查，不能把上述规则概括为所有 PR 命令统一行为。

以上入口可从本机逐命令 help 核对；实现见文末命令源码索引。

## 正文、文件、stdin 与交互

### 正文输入不是一套统一规则

`-b/--body` 接收文本，`-F/--body-file` 接收文件路径；`-F -` 才读取 stdin。文件读取是完整读取，读失败向上传播；没有不带 flag 自动消费 stdin 的共同约定。`--body` 的内容不会被 CLI 当作文件名读取；shell 自身的替换与转义属于调用方行为。[文件读取实现](https://github.com/cli/cli/blob/v2.89.0/pkg/cmdutil/file_input.go)

| 命令族 | 正文含义 | 同时给 body 与 body-file | 省略正文 / 清空规则 |
| --- | --- | --- | --- |
| issue/pr create | 新对象描述 | 该版本构造器没有将两者设为互斥；非空 body-file 路径读取结果覆盖 body | 普通非交互创建要求标题和正文参数已提供；PR 的 fill 系列可替代。`--body ""` 算提供了参数，不等于“参数缺失”。 |
| issue/pr edit | **替换**对象描述 | 非空 body-file 与显式 body 互斥 | 未选择正文就不修改；显式 `--body ""` 将空正文作为更新值，不是 append。 |
| issue/pr comment | 新评论或最后一条评论的正文 | body、body-file、启用的 editor、web 最多选择一种 | 无输入且能交互时询问；不能交互则报错。删除模式禁止正文输入。 |
| pr merge | **合并提交消息**的正文 | body 与 body-file 互斥 | 不修改 PR 描述；另有 subject 与 author-email。 |

创建时 `--template` 与已经提供的正文冲突。`create --editor` 使用编辑器第一行作为标题，其余为正文；`create --web` 打开浏览器创建流程，不能把打开浏览器等同于 API 对象已创建。issue create 对空白标题有后续校验；是否接受其他空内容还受具体 API 约束，不能仅由 flag 的“已提供”状态推导。

普通非交互 `issue create` 要求 title/body；`pr create` 可用 title/body 或 `--fill`、`--fill-first`、`--fill-verbose`。三个 fill flag 互斥；显式标题、正文优先于自动填充。PR 的 draft、reviewer、no-maintainer-edit 等与 web 存在具体冲突检查，完整组合以该版本构造器为准，不假设浏览器模式支持所有创建参数。[issue create](https://github.com/cli/cli/blob/v2.89.0/pkg/cmd/issue/create/create.go)、[PR create](https://github.com/cli/cli/blob/v2.89.0/pkg/cmd/pr/create/create.go)、[issue edit](https://github.com/cli/cli/blob/v2.89.0/pkg/cmd/issue/edit/edit.go)、[PR edit](https://github.com/cli/cli/blob/v2.89.0/pkg/cmd/pr/edit/edit.go)、[评论共同输入校验](https://github.com/cli/cli/blob/v2.89.0/pkg/cmd/pr/shared/commentable.go#L59)

编辑不带修改 flag 时走交互选择；非交互需要明确修改字段。issue 批量编辑不支持交互编辑多个对象。标签、项目、assignee 是 add/remove 形式；title、body、base 等标量是设置值；milestone 与 remove-milestone 互斥，不能把所有参数理解为增量追加。

### 评论定位与删除

`comment` 的位置参数定位 issue/PR，不是评论 ID。默认新增普通讨论评论；`pr comment` 不是逐行 review comment 接口。

- `--edit-last` 编辑当前用户最后一条评论。没有当前用户评论时，`--create-if-none` 才明确允许创建；交互流程也可以询问是否创建。
- `--create-if-none` 只能与 `--edit-last` 使用。
- `--delete-last` 删除当前用户最后一条评论；非交互必须 `--yes`。`--yes` 只能搭配删除模式。
- 删除成功输出 `Comment deleted` 到 stderr，新增/编辑成功输出评论 URL 到 stdout。
- `--web` 打开评论位置；浏览器打开成功不证明评论已经提交。
- 此版本没有显式拒绝同时设置 edit-last 与 delete-last，运行分支优先处理删除；不要替源码虚构这组参数互斥。

证据：[共享评论实现](https://github.com/cli/cli/blob/v2.89.0/pkg/cmd/pr/shared/commentable.go)。

## Assignee 的含义和更新规则

| 场景 | 参数与规则 |
| --- | --- |
| 创建 | `-a/--assignee` 是可重复、可逗号分隔的 login 列表。指定的是被分配用户，并非自动选择当前用户。 |
| 编辑 | `--add-assignee` 与 `--remove-assignee` 在已有集合上计算。现有其他 assignee 保留；同一 login 同时 add/remove 时，先加后删，最终移除。 |
| 列表 | `-a/--assignee` 是单个筛选字符串，不产生 assignment 写操作。 |
| 特殊名称 | `@me` 解析为当前认证用户。issue create/edit 的本机 help 还明确支持 `@copilot`，并说明 GHES 不支持 Copilot assignment。PR create 的本机 help 只明确写 `@me`，本报告不扩大其文字保证。 |
| Reviewer | PR 的 reviewer 独立于 assignee；create 用 `--reviewer`，edit 用 `--add-reviewer/--remove-reviewer`。不能将分配与请求评审视为同一字段。 |

编辑实现先保留默认集合，再展开特殊名称并添加，最后移除；还按 host feature 区分 node ID 与 actor login 的 API 路径。名称解析失败可以阻止修改。使用同一参数名不保证所有主机支持同一 actor 集合。[assignee 更新实现](https://github.com/cli/cli/blob/v2.89.0/pkg/cmd/pr/shared/editable.go#L95)

## 查询、列表与 JSON

### 默认值与查询边界

issue list 状态枚举是 `open|closed|all`；PR list 是 `open|closed|merged|all`。默认均为 `open`，`--limit` 默认 30 且必须至少 1。PR 的普通列表实现将 `closed` 映射到 CLOSED 与 MERGED，因此 closed 不是“只关闭未合并”。[PR 列表实现](https://github.com/cli/cli/blob/v2.89.0/pkg/cmd/pr/shared/lister.go)

普通仓库列表按创建时间倒序，内部按页获取到 limit；没有在这些子命令上暴露可接续的 cursor 参数。带搜索条件可能走 Search API，不能将普通列表排序/无限数量推广到搜索路径。搜索最多 1000 条；实现对受此限制的文本结果发 stderr 警告，但 JSON 分支在警告前返回。[issue 列表请求](https://github.com/cli/cli/blob/v2.89.0/pkg/cmd/issue/list/http.go)、[issue list](https://github.com/cli/cli/blob/v2.89.0/pkg/cmd/issue/list/list.go)、[PR list](https://github.com/cli/cli/blob/v2.89.0/pkg/cmd/pr/list/list.go)

`--search` 已含状态条件时，CLI 移除默认 open 条件。PR `--draft` 是可区分未提供/true/false 的筛选，未提供不会只列非草稿。PR `--head`、`--base` 分别筛选头/基分支；`--label` 的多个标签要求同时匹配。

### 人类输出与管道输出

终端 list 有数量标题、颜色和表格；管道不输出同样的标题，字段布局也可能增加 state。终端 view 显示渲染后的详情；**普通管道 view 仍有元数据行、`--` 分隔符与原始正文，并非只输出 body**。issue 原始详情含 title/state/author/labels/comments/assignees/projects/milestone/number；PR 还包含 reviewer、URL、增删行、auto-merge 等信息。

`view --comments` 的非终端分支输出评论列表，不再输出上述详情块；PR 还包含可展示的 review。不要把普通文本输出当成跨 TTY 一致的数据协议。[issue view](https://github.com/cli/cli/blob/v2.89.0/pkg/cmd/issue/view/view.go#L175)、[PR view](https://github.com/cli/cli/blob/v2.89.0/pkg/cmd/pr/view/view.go#L130)

### JSON 的边界

本报告范围内，只有 issue/pr 的 **view 与 list** 提供 `--json`。create、edit、comment、close、reopen、merge、ready 没有通用 `--json` 成功响应协议。

`--json field1,field2` 必须选择允许的字段。view 导出单个对象，list 导出数组；无结果的 JSON list 是空数组。`--jq` 和 `--template` 必须配合 JSON；JSON 与 web 冲突。未知字段报错并显示允许字段；裸 `--json` 用于显示字段提示时也是参数错误分支，不能当成成功的数据请求。错误不会统一包装成 JSON 对象。[JSON flag 与导出实现](https://github.com/cli/cli/blob/v2.89.0/pkg/cmdutil/json_flags.go)

本机 help 的 issue 字段集：

```text
assignees, author, body, closed, closedAt, closedByPullRequestsReferences,
comments, createdAt, id, isPinned, labels, milestone, number, projectCards,
projectItems, reactionGroups, state, stateReason, title, updatedAt, url
```

本机 help 的 PR 字段集：

```text
additions, assignees, author, autoMergeRequest, baseRefName, baseRefOid, body,
changedFiles, closed, closedAt, closingIssuesReferences, comments, commits,
createdAt, deletions, files, fullDatabaseId, headRefName, headRefOid,
headRepository, headRepositoryOwner, id, isCrossRepository, isDraft, labels,
latestReviews, maintainerCanModify, mergeCommit, mergeStateStatus, mergeable,
mergedAt, mergedBy, milestone, number, potentialMergeCommit, projectCards,
projectItems, reactionGroups, reviewDecision, reviewRequests, reviews, state,
statusCheckRollup, title, updatedAt, url
```

字段名是稳定选择入口，不代表嵌套集合全部无限展开。issue view 对 comments 有额外分页加载路径；本次不对所有 JSON 嵌套连接作“保证完整”的推断。[issue view 分页入口](https://github.com/cli/cli/blob/v2.89.0/pkg/cmd/issue/view/view.go#L145)

## 生命周期和 Git 副作用

### Close / reopen / ready

已处于目标状态的 issue close/reopen、PR close/reopen 会先警告并成功返回，不再追加 `--comment`。需要转换状态时，评论先创建，状态 mutation 后执行；如果后一步失败，前面的评论可能已经保留。它们不是跨评论和状态的事务。

issue close 的 reason 支持 `completed`、`not planned`、`duplicate`。省略 reason 时 CLI 留空并不发送 stateReason，不能把服务端默认原因写成 CLI 明确指定的 completed。`--duplicate-of` 可自动补 reason=duplicate，冲突原因、自引用及目标是 PR 等有专门校验。issue close/reopen 的实现通过共享查询也能识别 PR 并转用 PR mutation；这是源码兼容行为，父命令 help 仍以 issue 命名。[issue close](https://github.com/cli/cli/blob/v2.89.0/pkg/cmd/issue/close/close.go)、[issue reopen](https://github.com/cli/cli/blob/v2.89.0/pkg/cmd/issue/reopen/reopen.go)

merged PR 的 close/reopen 会说明不能操作并失败。`pr ready` 仅允许 OPEN PR，默认取消草稿；`--undo` 设为草稿。已经满足目标时警告且成功返回。ready 不表示批准评审、检查通过或已合并。[PR close](https://github.com/cli/cli/blob/v2.89.0/pkg/cmd/pr/close/close.go)、[PR reopen](https://github.com/cli/cli/blob/v2.89.0/pkg/cmd/pr/reopen/reopen.go)、[PR ready](https://github.com/cli/cli/blob/v2.89.0/pkg/cmd/pr/ready/ready.go)

PR close 的 `--delete-branch` 默认 false。启用后先关闭再清理分支；在对应本地分支上时可能切换到默认分支，`--repo` 模式跳过本地删除，跨仓库 PR 跳过远端删除。后续 Git 操作失败不回滚已完成的关闭。

### PR create

head 默认当前分支；base 依次取显式 `--base`、当前分支 `gh-merge-base` Git 配置、仓库默认分支。当前分支未完全推送时，创建流程可能询问推送位置并 fork/push；显式 `--head` 跳过这类自动 fork/push 行为。help 说明 head 的 `<user>:<branch>` 不支持 organization owner。

默认非草稿，默认允许维护者修改，`--no-maintainer-edit` 才关闭该能力。`--dry-run` 打印拟创建内容，**仍可能推送 Git 改动**，不能作为纯只读探查。即使最终 API 创建失败，此前 Git 推送也可能已经完成。[PR create 源码](https://github.com/cli/cli/blob/v2.89.0/pkg/cmd/pr/create/create.go)

### PR merge

`--merge`、`--rebase`、`--squash` 互斥。普通非交互合并没有指定策略会报错，不存在可一概依赖的隐含 squash 默认；交互模式询问允许的策略。`--auto`、`--disable-auto`、`--admin` 互斥。

要求 merge queue 的目标分支不要求客户端选择策略：检查未满足时可启用自动合并，满足后加入队列。已经在队列中有专门处理；队列要求与删除分支请求存在限制。`--admin` 使用管理员权限绕过相应约束，不会授予调用者权限。`--auto` 也可能在已经可立即合并时直接合并，所以输出成功既不能统一解释为“已合并”，也不能统一解释为“只登记等待”。[官方 merge 手册](https://cli.github.com/manual/gh_pr_merge)、[固定版本流程](https://github.com/cli/cli/blob/v2.89.0/pkg/cmd/pr/merge/merge.go)

`--match-head-commit` 将用户输入直接放入 GraphQL `expectedHeadOid`；该调用路径没有用本地 Git 展开缩写，也没有本地前缀匹配。服务端是否接受某种缩写不在本次实测范围，应按需要精确匹配的提交 OID 理解，不能虚构 CLI 会自动解析短 SHA 的保证。[merge 请求](https://github.com/cli/cli/blob/v2.89.0/pkg/cmd/pr/merge/http.go)

`--delete-branch` 的 flag 默认 false；交互合并在未明确指定时仍可询问是否删除。正常立即合并后可清理本地/远端分支；当前分支需要切换时会 checkout 到 PR base 并尝试 pull。跨仓库 PR 不走同样的远端删除，等待自动合并时跳过清理。已经合并的 PR 仍可能处理本地清理。合并、切换、pull、删除之间没有整体回滚。[merge 与清理顺序](https://github.com/cli/cli/blob/v2.89.0/pkg/cmd/pr/merge/merge.go#L534)

普通 merge 成功提示经 `infof` 输出：仅 stdout 为 TTY 时写 stderr，非终端可成功但没有这一摘要。警告不受相同抑制。不能凭 stdout 是否有 URL 判断 merge 是否成功。[输出实现](https://github.com/cli/cli/blob/v2.89.0/pkg/cmd/pr/merge/merge.go#L491)

## 错误、退出码与部分成功

本机 exit-codes help 约定：0 成功、1 失败、2 用户取消、4 需要认证；同时提醒个别命令可能有其他退出码。不能把所有 HTTP 401/403 或任意权限错误直接映射成 4：顶层专门识别 AuthError，其余请求失败走各自错误处理。[官方退出码说明](https://cli.github.com/manual/gh_help_exit-codes)、[顶层错误处理](https://github.com/cli/cli/blob/v2.89.0/internal/ghcmd/cmd.go#L112)

| 情况 | 已核实的行为 |
| --- | --- |
| 参数数量、枚举或组合无效 | 返回参数错误；不是默默忽略。具体报错文字保存在版本源码。 |
| body-file 无法读取 | 返回读取错误，不回退为 body 或空正文。 |
| 列表没有匹配结果 | **退出 0**；终端可在 stderr 提示无结果；非终端文本无对应提示；JSON 输出空数组。 |
| close/reopen/ready 已是目标状态 | 对相应允许状态警告并成功返回；不等于所有生命周期命令都幂等。 |
| merged PR 要求 close/reopen，或非 OPEN PR 要求 ready | 输出具体说明并失败。 |
| 批量 issue edit 有部分失败 | 成功 URL 排序后到 stdout；每项失败原因排序后到 stderr；最后返回失败汇总，已成功项不会回滚。 |
| 评论后关闭失败、创建前推送成功后创建失败、合并后删分支失败 | 命令失败并不能证明没有发生任何写入。 |

批量编辑是并发的，stdout 排序不是更新发生顺序。[issue edit 执行与汇总](https://github.com/cli/cli/blob/v2.89.0/pkg/cmd/issue/edit/edit.go#L265)

错误是命令自身输出、HTTP/GraphQL 客户端错误以及顶层格式化的组合；本报告没有承诺统一错误码字段、统一 JSON envelope 或固定所有错误句式。API 权限、功能开关、仓库状态与网络会影响具体失败内容，保留原始 stderr 比归并成泛化类别更有助于诊断。

## 环境与可重现前提

本机 environment help 明确：`GH_TOKEN` 优先于 `GITHUB_TOKEN` 及已保存凭据；GHES 有独立 enterprise token 变量。`GH_REPO`、`GH_HOST` 改变默认定位；`GH_PROMPT_DISABLED` 禁用交互；`GH_FORCE_TTY` 可强制终端式输出；`GH_EDITOR`、`GH_BROWSER`、`GH_PAGER` 可指定编辑器、浏览器、分页器。颜色、Markdown 宽度、配置和更新提示也会影响呈现。这里只记录变量约定，没有读取或输出实际凭据。[本机环境帮助](github-evidence/environment-help.txt)

因此可复现调用至少应记录 gh 版本、命令与 flag、仓库/主机、是否可交互及 stdout 是否 TTY。服务端状态、权限和 Git 工作区状态属于运行前提，不能由 help 单独证明。

## 命令源码索引

| 命令 | 官方 v2.89.0 源码 |
| --- | --- |
| issue create / view | [create](https://github.com/cli/cli/blob/v2.89.0/pkg/cmd/issue/create/create.go)、[view](https://github.com/cli/cli/blob/v2.89.0/pkg/cmd/issue/view/view.go) |
| issue list / edit | [list](https://github.com/cli/cli/blob/v2.89.0/pkg/cmd/issue/list/list.go)、[edit](https://github.com/cli/cli/blob/v2.89.0/pkg/cmd/issue/edit/edit.go) |
| issue comment / close / reopen | [comment](https://github.com/cli/cli/blob/v2.89.0/pkg/cmd/issue/comment/comment.go)、[close](https://github.com/cli/cli/blob/v2.89.0/pkg/cmd/issue/close/close.go)、[reopen](https://github.com/cli/cli/blob/v2.89.0/pkg/cmd/issue/reopen/reopen.go) |
| pr create / view | [create](https://github.com/cli/cli/blob/v2.89.0/pkg/cmd/pr/create/create.go)、[view](https://github.com/cli/cli/blob/v2.89.0/pkg/cmd/pr/view/view.go) |
| pr list / edit | [list](https://github.com/cli/cli/blob/v2.89.0/pkg/cmd/pr/list/list.go)、[edit](https://github.com/cli/cli/blob/v2.89.0/pkg/cmd/pr/edit/edit.go) |
| pr comment / close / reopen | [comment](https://github.com/cli/cli/blob/v2.89.0/pkg/cmd/pr/comment/comment.go)、[close](https://github.com/cli/cli/blob/v2.89.0/pkg/cmd/pr/close/close.go)、[reopen](https://github.com/cli/cli/blob/v2.89.0/pkg/cmd/pr/reopen/reopen.go) |
| pr merge / ready | [merge](https://github.com/cli/cli/blob/v2.89.0/pkg/cmd/pr/merge/merge.go)、[ready](https://github.com/cli/cli/blob/v2.89.0/pkg/cmd/pr/ready/ready.go) |

每个子命令的本机 help 分别保存在 `github-evidence/<issue|pr>-<command>-help.txt`。上述结论是本机 help 与对应官方实现的静态核实；没有用实际外部写操作验证服务端效果。
