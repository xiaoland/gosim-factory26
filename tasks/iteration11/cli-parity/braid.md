# Braid CLI 独立行为清单

本清单只描述当前 `sources/braid` 的 CLI；不对照其他工具，也不把帮助文字当成行为证明。取证方式是读取 `src/cli/mod.rs`、`src/objects.rs`、`src/main.rs` 的当前实现，并读取已编译二进制的相关 `--help`。本轮未创建或修改工作项、未运行测试或模拟探针。源码同时有其他 I11 工作在编辑，因此下述行号对应本次取证时点；实际运行仍受所在 Braid run 的状态与身份约束。

## 先找到工作项与正文

`braid issue list` 和 `braid pr list` 分别列出本地 Issue、PR，按编号升序；文本行是编号、状态、当前具体负责人和标题，没有状态筛选、搜索或分页参数。`--json` 产出数组；`--json id,title,state` 等选择字段，允许的列表字段固定为 `id,kind,title,body,state,reason,head_ref,base_ref,draft,ready_commit,revision,parent,assignees,execution`。缺失值按对象序列化为 `null` 等原值。列表没有评论字段。依据：[命令定义](../../../sources/braid/src/cli/mod.rs#L139-L145)、[PR 定义](../../../sources/braid/src/cli/mod.rs#L213-L220)、[字段与列表输出](../../../sources/braid/src/cli/mod.rs#L375-L450)、[文本列表](../../../sources/braid/src/cli/mod.rs#L608-L619)、[数据库排序](../../../sources/braid/src/objects.rs#L409-L419)。

`braid issue view ID` / `braid pr view ID` 读取单项，文本默认显示正文及关系/活动摘要，评论需 `--comments`。`--json` 不带字段名时输出完整 item、详情及评论；指定字段可读取 `body`、`comments` 及详情字段，例如 Issue 的 `parent_issue,sub_issues,associated_prs,subscriptions,execution_error`，PR 的 `associated_issues,closing_issues,base_commit,head_commit,merge_commit,assignee_activity,assignee_deliveries`。这与列表的固定字段集不同：详情字段由对象和详情映射实际包含的键决定，未知键报错。`--comments` 与 `--json` 在读取时均会获取评论，但 `--json body` 只返回所选 `body`。依据：[读取分支](../../../sources/braid/src/cli/mod.rs#L824-L834)、[PR 读取分支](../../../sources/braid/src/cli/mod.rs#L889-L897)、[详情输出](../../../sources/braid/src/cli/mod.rs#L490-L557)、[详情来源](../../../sources/braid/src/objects.rs#L1340-L1399)。

`view ID --timeline` 改为读取工作项活动流，不返回一般详情；`--after N` 是排除该全局活动序号的游标，默认 0；`--limit N` 默认 30、有效范围 1–100。文本输出页尾与下一页命令，JSON 是 `{items,after,limit,has_more,next_after}`；只有还有下一页时 `next_after` 有值。`--after`、`--limit` 必须与 `--timeline` 同用。活动项带序号、时间、作者、动作、来源评论 ID 和详情，不等同完整评论正文。依据：[参数](../../../sources/braid/src/cli/mod.rs#L145-L159)、[渲染](../../../sources/braid/src/cli/mod.rs#L559-L571)、[查询和边界](../../../sources/braid/src/objects.rs#L287-L297)。

## 创建 Issue 或 PR

`issue create -t TITLE (-b BODY | -F FILE)` 可加 `--parent ISSUE_ID`、`--assignee AGENT`、布尔 `--json`。`pr create --issue ISSUE_ID[,ISSUE_ID...] -t TITLE (-b BODY | -F FILE)` 还可加 `--request-id`、`--base`、`--head`、`--draft`、`--assignee`、布尔 `--json`。两者都要求显式提供正文来源，标题不能只含空白；Issue/PR 正文本身允许空字符串。Issue 父项必须存在且不能成环。编号在本地 Issue 与 PR 之间共用序列。依据：[参数](../../../sources/braid/src/cli/mod.rs#L164-L175)、[PR 参数](../../../sources/braid/src/cli/mod.rs#L238-L265)、[必需正文](../../../sources/braid/src/cli/mod.rs#L845-L853)、[PR 调用](../../../sources/braid/src/cli/mod.rs#L908-L920)、[编号/标题](../../../sources/braid/src/objects.rs#L538-L565)、[父项检查](../../../sources/braid/src/objects.rs#L865-L877)。

PR 必须关联至少一个已存在 Issue；关联仅提供背景，不能据此推断会自动关闭。`--base` 默认本次 run 的 delivery ref；显式 `--head` 必须是本次 origin 已发布的分支，且不能与 base 相同。省略 head 时会从 base 新建 `refs/heads/braid/pr-ID`。`--request-id` 是可选重试键：命中已有 PR 时返回原创建结果；若又传 base/head，会检查它们与原 PR 一致。创建成功的 Issue JSON 是 `{id,assignees,assignment_note}`；PR JSON 包含 id、head/base ref 与 commit、assignees、assignment_note。依据：[PR 创建实现](../../../sources/braid/src/objects.rs#L1442-L1553)、[创建输出](../../../sources/braid/src/cli/mod.rs#L621-L632)、[PR 输出](../../../sources/braid/src/cli/mod.rs#L660-L676)。

## 修改正文、标题、父项与负责人

`issue edit ID` 可改 `-t/--title`、正文、`--parent`/`--remove-parent`、`--add-assignee AGENT`/`--remove-assignee MEMBER`；`pr edit ID` 可改标题、正文、负责人，没有父项参数。至少要提供一项修改；正文参数一旦提供便替换**完整**正文，空内容会清空，而不提供正文则保留原文。成功后打印更新后的文本 item，没有 `--json` 开关。依据：[参数](../../../sources/braid/src/cli/mod.rs#L177-L193)、[PR 参数](../../../sources/braid/src/cli/mod.rs#L266-L278)、[调用及输出](../../../sources/braid/src/cli/mod.rs#L855-L879)、[PR 调用](../../../sources/braid/src/cli/mod.rs#L922-L938)、[编辑约束与写入](../../../sources/braid/src/objects.rs#L748-L860)。

所有这些正文输入共用 `-b/--body` 或互斥的 `-F/--body-file`：`-b` 的值按字面使用，`-F PATH` 读取 UTF-8 文件全文，`-F -` 读标准输入至 EOF。创建 Issue/PR、发布评论、编辑评论要求其中之一；编辑 Issue/PR 可省略。CLI 不负责执行或确认生成正文的上游 shell 命令是否成功，长正文宜先保存文件并检查，再传入 `-F`。依据：[BodyArgs](../../../sources/braid/src/cli/mod.rs#L98-L130)、[命令调用](../../../sources/braid/src/cli/mod.rs#L845-L881)、[PR 调用](../../../sources/braid/src/cli/mod.rs#L908-L940)、[评论编辑](../../../sources/braid/src/cli/mod.rs#L975-L978)。

`--assignee`/`--add-assignee` 接受可指派 Profile 的名称，可省略前导 `@`，匹配时转小写；它并非把旧成员登录名再次分配。每次新指派会生成独立的 `名称-序号` 具体成员，后续联系与 `--remove-assignee` 使用该具体名字。已有负责人时，单独 `--add-assignee` 报错；改派需在同一 `edit` 命令中同时指定 `--remove-assignee 当前具体成员 --add-assignee 新名称`。单独移除也要求准确匹配当前成员。创建及改派的用户输出会说明新负责人。依据：[名称与新成员](../../../sources/braid/src/objects.rs#L453-L482)、[编辑校验](../../../sources/braid/src/objects.rs#L774-L791)、[替换行为](../../../sources/braid/src/objects.rs#L492-L536)、[输出](../../../sources/braid/src/cli/mod.rs#L621-L632)。

## 评论、线程和可见性

`issue comment ID` / `pr comment ID` 用正文参数发评论，可用 `--reply-to COMMENT_ID` 回复同一工作项里的评论；空白评论被拒绝。布尔 `--json` 返回 `{id,deliveries}`；文本输出评论 ID 与投递回执。回执的 `delivered` 只表示会话接受输入，不证明对方已处理。`comment edit COMMENT_ID` 用同一正文参数整体替换评论，成功后只输出文本回执。可见内容的编辑会更新活动/通知；仅 HTML 注释变化不会当作可见内容变化。依据：[命令定义](../../../sources/braid/src/cli/mod.rs#L194-L202)、[PR 定义](../../../sources/braid/src/cli/mod.rs#L279-L287)、[写入](../../../sources/braid/src/objects.rs#L882-L919)、[输出及回执语义](../../../sources/braid/src/cli/mod.rs#L634-L658)、[编辑语义](../../../sources/braid/src/objects.rs#L1008-L1043)。

`comment view COMMENT_ID` 直接按全局评论 ID 读取，`--thread` 扩展为同一根线程，`--json` 返回**数组**（即使只读一条），每项还带 deliveries。直接读指定评论会展开 resolved 历史中仍可见的正文；读整条线程时，resolved 的旧内容默认折叠。`--include-hidden` 会展开 hidden 与 resolved 历史；deleted 评论的正文已经为 `NULL`，不能恢复。折叠或隐藏时输出的 `read_body_with` 指向直接读取命令。依据：[命令定义](../../../sources/braid/src/cli/mod.rs#L320-L356)、[读取分支](../../../sources/braid/src/cli/mod.rs#L956-L974)、[快照与展开逻辑](../../../sources/braid/src/objects.rs#L1188-L1242)、[JSON 提示](../../../sources/braid/src/cli/mod.rs#L417-L430)。

`comment hide ID... [--reason TEXT]`、`comment resolve ID...` 支持一次多个 ID；`unhide ID`、`unresolve ID` 与 `delete ID` 单条执行。hide 是评论可见性，resolve 是线程的已处理/折叠状态，二者独立；对线程中任一评论 resolve 会把该线程截至当时的评论设为已处理历史，后续新回复仍可见。delete 清空正文且不可恢复。另有 `comment reaction add/remove ID EXPRESSION`。这些是 Braid 的本地讨论操作，不能把 hide/resolve 解释为关闭 Issue/PR。依据：[命令](../../../sources/braid/src/cli/mod.rs#L337-L368)、[分发](../../../sources/braid/src/cli/mod.rs#L979-L993)、[可见性实现](../../../sources/braid/src/objects.rs#L1044-L1111)、[线程解决范围](../../../sources/braid/src/objects.rs#L1112-L1150)、[快照过滤](../../../sources/braid/src/objects.rs#L1188-L1210)。

## 关闭、重开、PR 关联、就绪与合并

`issue close ID --reason TEXT` / `pr close ID --reason TEXT` 必须传理由参数；从 open 真正转为 closed 时，理由不能只含空白。`reopen ID` 重新打开。已处于目标状态时实现直接返回成功，无输出；已合并 PR 不能重开。关闭与重开命令成功时也无 JSON 输出。依据：[命令](../../../sources/braid/src/cli/mod.rs#L203-L210)、[PR 命令](../../../sources/braid/src/cli/mod.rs#L310-L317)、[分发](../../../sources/braid/src/cli/mod.rs#L884-L887)、[PR 分发](../../../sources/braid/src/cli/mod.rs#L951-L954)、[生命周期实现](../../../sources/braid/src/objects.rs#L1663-L1683)。

`pr link ID --issue ISSUE_ID` / `pr unlink ID --issue ISSUE_ID` 修改背景关联，不是关闭声明；创建 PR 时的 `--issue` 也是同一类关联。只有 PR 正文里的本仓库 `Closes #N` / `Fixes #N` / `Resolves #N` 等关闭引用，在合入 origin 默认分支且引用指向存在的 Issue 时才形成关闭目标。解析器只检查 Markdown 段落与标题中的正文词对，跳过代码节点；不读取 commit message 或跨仓库引用。依据：[命令与帮助](../../../sources/braid/src/cli/mod.rs#L238-L243)、[关联命令](../../../sources/braid/src/cli/mod.rs#L288-L299)、[关联实现](../../../sources/braid/src/objects.rs#L1572-L1614)、[关闭目标](../../../sources/braid/src/objects.rs#L1733-L1755)、[正文解析器](../../../sources/braid/src/objects.rs#L1969-L1995)。

`pr ready ID` 将 open PR 标为非 draft，并记录当前已发布 head commit；`pr ready ID --undo` 将其改回 draft。若已处于目标 draft 状态，仍返回当前 head，但不再改状态。输出始终是 JSON `{head_commit,draft}`，无需 `--json`。`pr merge ID [--match-head-commit SHA]` 只接受 open、非 draft PR；可用参数要求当前 head 与所给 SHA 完全相同。成功始终输出 JSON `{merge_commit}`。已合并时返回既有 merge commit。若目标分支已含 head，只有已记录创建时 base 与曾观测到独有 head 的情况下才记录整合，且不更新 Git 引用；否则会准备/应用合并提交。冲突时报错，合并不发生。依据：[命令与分发](../../../sources/braid/src/cli/mod.rs#L300-L317)、[JSON 输出](../../../sources/braid/src/cli/mod.rs#L948-L950)、[ready](../../../sources/braid/src/objects.rs#L1622-L1662)、[merge 检查与路径](../../../sources/braid/src/objects.rs#L1761-L1875)。

## 调用上下文、帮助与错误

`braid --help` 和 `braid issue|pr|comment --help` 展示命令树；各子命令 `--help` 展示参数。当前帮助文案明确 `-F -`、正文替换以及 assignee 名称/具体成员的区别，但行为以上述实现为准。普通宿主调用非 `local`/telemetry 命令需要 `--state`；Agent runtime 从环境绑定 state 和身份，并拒绝显式 `--state`、`--writer-turn`、`--external`。列表、查看等读取可无 writer；创建、编辑、评论、关闭、合并等写入需要有效当前 Agent 身份或宿主 `--external`。这不是普通无状态远程 API。依据：[全局参数](../../../sources/braid/src/cli/mod.rs#L10-L22)、[绑定及写入门禁](../../../sources/braid/src/cli/mod.rs#L679-L734)。

Clap 处理未知选项、缺少必填参数和参数互斥；业务校验还会拒绝无修改的 edit、错误负责人、无效父项/回复对象、空白评论、未发布 PR 分支、draft/closed PR 合并及 head 不匹配等。应用错误由入口打印为 `error: ...` 到 stderr 并以退出码 1 结束；具体消息受失败分支影响，不应依赖其完整文本作程序接口。依据：[输入定义](../../../sources/braid/src/cli/mod.rs#L98-L137)、[入口](../../../sources/braid/src/main.rs#L47-L52)、[编辑](../../../sources/braid/src/objects.rs#L759-L791)、[PR 创建](../../../sources/braid/src/objects.rs#L1484-L1503)、[合并](../../../sources/braid/src/objects.rs#L1761-L1855)。

**已核与缺证。** 上述参数、输出形状、校验和状态变化已由当前实现核对；相关 `--help` 已在当前二进制只读核对，构建成功。本轮没有在实际 run 中执行写命令，也没有逐个触发错误分支，因此不声称跨所有真实运行状态的端到端效果、help 与并行编辑完成后的最终一致性，或外部接收方实际处理了投递的评论。
