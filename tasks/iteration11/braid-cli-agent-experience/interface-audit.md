# Braid Issue / PR CLI 接口只读审查

日期：2026-09-30。审查对象：`sources/braid` 工作树，HEAD `0712a58d0e5f7af225473d6c48c4aa740c20dfbf`，包含当时未提交修改。不是该 HEAD 的纯提交版本，也未把已有 binary 当成当前源码。

读取了 Factory26 与 Braid 的 AGENTS、Braid `rust-code` skill、当前 PRD/TDD 本地契约；用 ponytail 的最小改动原则评估候选。仅静态阅读，未运行命令作用于真实对象，未编译、测试、安装或试跑模型。本文只新增到获授权的任务目录；resolve/hide/description 的产品语义由主 Agent 另核。

源码身份：

| 文件 | SHA-256 |
| --- | --- |
| `src/cli/mod.rs` | `0c3f1e75cbef4dafdc79c223473830eec42381bdb6c68ee7bc39aa85bc187ac9` |
| `src/objects.rs` | `773bcb68ec5ba2a4e68c63a451f07550cf10508a437cb700299642813cfb676c` |
| `src/main.rs` | `d2ce28e5287fdc86fec877d0680f94ce913dc8a32201e4052bdd653e8293565f` |

## 结论与优先级

CLI 已提供明确工作项、类型化状态、精确成员、正文文件、评论引用、时间线游标、PR 重试键和合并 head 校验；不需要重建命令体系。最值得先改的是参数组合静默降级、字段选择背后的无界读取、以及编辑操作无条件回显完整正文。

本文 P2 表示具体接口缺口或规模增长后的确定成本，P3 表示发现性与一致性改善；没有以静态审查宣称已经发生数据丢失、重复创建或模型误操作。证据 A 为源码直接确定，B 为确定的失败路径但尚无真实触发记录。优先级仍应结合另一审查的真实调用频次与失败日志。

| 级别 | 发现 | 证据 | 最小候选 |
| --- | --- | --- | --- |
| P2 | `view --timeline --json FIELDS` 静默忽略 FIELDS；`--comments` 也可被 timeline 忽略 | A | timeline 拒绝字段选择（或明确支持自己的字段），与 comments 互斥 |
| P2 | `view --json body` 仍加载本项全部评论、完整详情；PR 还加载关联 Issue 的正文与全部评论 | A | 常用标量字段走现有 Item 投影；只有请求 comments/详情时才读取相应数据 |
| P2 | `edit --title` / 改派后无条件回显完整正文，无 JSON/精简回执开关 | A | 默认输出对象编号及变更结果；完整内容由已有 view 按需读取 |
| P2，条件性 | create/comment 提交成功后还有可失败的回执读取，CLI 统一非零错误不能区分“未写入”与“已写入但回执失败” | B | 保留已提交编号，回执扩展失败时输出明确的 committed 状态与读回入口 |
| P3 | list 截断无提示、无游标；裸数组不能证明结果完整 | A | 多取一条判断截断并明确提示；是否新增稳定分页由真实规模决定 |
| P3 | view 字段发现、错误定位和数字引用帮助不充分 | A | 补充字段候选、对象 kind/number、参数值范围和少量关键副作用说明 |

## 1. 参数组合会接受请求却返回另一种内容

Issue/PR `View` 同时声明 `comments`、`timeline` 与 `JsonFields`，只有 `after/limit` 要求 timeline，没有 comments/timeline 互斥：[cli:200](/Volumes/WorkSSD/Development/factory26/sources/braid/src/cli/mod.rs:200)、[cli:290](/Volumes/WorkSSD/Development/factory26/sources/braid/src/cli/mod.rs:290)。执行时 timeline 分支抢先返回，JSON 只取 `json.json.is_some()`，不读选择的字符串：[cli:962](/Volumes/WorkSSD/Development/factory26/sources/braid/src/cli/mod.rs:962)、[cli:1036](/Volumes/WorkSSD/Development/factory26/sources/braid/src/cli/mod.rs:1036)。`print_timeline` 固定输出 `items,after,limit,has_more,next_after`：[cli:665](/Volumes/WorkSSD/Development/factory26/sources/braid/src/cli/mod.rs:665)。

因此 `braid issue view 1 --timeline --json body`，甚至 `--json made_up_field`，都会接受参数并给完整时间线，而普通 view 对未知字段会报错。`--timeline --comments` 则不会显示所请求的评论正文。此处问题是命令成功掩盖了请求被忽略，不是字段名字应当模仿另一 CLI。

小范围候选：先选择一种明确契约。最小版让 timeline 仅接受裸 `--json`/`--json all`，非 all 返回“时间线只支持完整 JSON”；给 `comments` 与 `timeline` 加互斥。暂不为 timeline 新建一套通用查询语言。

## 2. 字段选择节省输出 token，但没有限制读取工作

`view --json <任何字段>` 都令 `include_comments=true`，先调用 `comments_for`，再读 Item，最后才进入投影：[cli:962](/Volumes/WorkSSD/Development/factory26/sources/braid/src/cli/mod.rs:962)、[cli:1036](/Volumes/WorkSSD/Development/factory26/sources/braid/src/cli/mod.rs:1036)。`print_view` 还无条件取得 `view_details`，在合并与序列化所有字段后才做字段筛选：[cli:591](/Volumes/WorkSSD/Development/factory26/sources/braid/src/cli/mod.rs:591)。

详情路径进一步放大读取：

- Issue 详情调用 `issue()`；它读取关联对象、子对象和本项所有评论，即使详情输出根本不含 comments：[objects:1351](/Volumes/WorkSSD/Development/factory26/sources/braid/src/objects.rs:1351)、[objects:1427](/Volumes/WorkSSD/Development/factory26/sources/braid/src/objects.rs:1427)。
- PR 详情调用 `pull_request()`；每个关联 Issue 都进入 `issue_in`，同时读取 PR 全部评论，再查询 Git base/head、投递、订阅和 closing 声明：[objects:1390](/Volumes/WorkSSD/Development/factory26/sources/braid/src/objects.rs:1390)、[objects:1434](/Volumes/WorkSSD/Development/factory26/sources/braid/src/objects.rs:1434)。
- `read_comments` 无 LIMIT，逐评论查询 reactions 并解析作者：[objects:1275](/Volumes/WorkSSD/Development/factory26/sources/braid/src/objects.rs:1275)、[objects:1299](/Volumes/WorkSSD/Development/factory26/sources/braid/src/objects.rs:1299)。指定单条 `comment view ID` 也先读取整条 thread 后 `retain` 到目标评论：[objects:1311](/Volumes/WorkSSD/Development/factory26/sources/braid/src/objects.rs:1311)。

结果是 Agent 被推荐的 `view ID --json body` 虽只输出 body，却仍随全部讨论与关联规模增长；普通文本 view 即使没有 `--comments`，也会因详情构造加载评论。已有输出选择不是“无效”，它确实减少传给模型的 token；这里另一个成本是 DB 查询、内存、Git 子进程及与不相关详情故障耦合。未测量延迟，不能声称已造成超时。

最小候选分两步：先让不含 comments 的显式字段选择不调用 `comments_for`，且只选 `ITEM_FIELDS` 的请求复用已有 `json_item`，不调用 `view_details`；再按真实规模决定是否把详情读取从 canonical Context 构造中拆出。单条 comment 应在 SQL 层按 ID 定位，保留 thread 查询给 `--thread`。不需要缓存或新的服务层。

## 3. 写入回执会放大上下文，格式也没有统一规律

Issue/PR edit 在操作完成后都会调用 `print_item(..., None, None)`：[cli:998](/Volumes/WorkSSD/Development/factory26/sources/braid/src/cli/mod.rs:998)、[cli:1067](/Volumes/WorkSSD/Development/factory26/sources/braid/src/cli/mod.rs:1067)。`print_item` 无条件打印非空完整正文：[cli:582](/Volumes/WorkSSD/Development/factory26/sources/braid/src/cli/mod.rs:582)。因此只改标题、parent 或负责人，也会把长 Description 再送回模型。edit 没有 `--json`，无法使用 list/view 的字段选择机制：[cli:232](/Volumes/WorkSSD/Development/factory26/sources/braid/src/cli/mod.rs:232)、[cli:337](/Volumes/WorkSSD/Development/factory26/sources/braid/src/cli/mod.rs:337)。

其他回执是不同风格：create/comment 可以选择 JSON；close/reopen 只有文本并明确 unchanged；ready/merge 无 `--json` 参数却始终输出 JSON；unlink 直接返回 `Result<()>`，成功 stdout 为空：[cli:1020](/Volumes/WorkSSD/Development/factory26/sources/braid/src/cli/mod.rs:1020)、[cli:1090](/Volumes/WorkSSD/Development/factory26/sources/braid/src/cli/mod.rs:1090)。这些不必一次全改，但 Agent 无法仅凭统一经验预测格式，需要逐命令探查。

最小候选优先处理高成本的 edit：例如 `issue #7 updated; assignee @member`，变更或未变更明确，正文读回沿用 `issue view 7 --json body`。其它命令先补明确帮助与短回执；是否统一 JSON 由调用日志与兼容范围决定，不能把现有 ready/merge JSON 强行改成文本。

## 4. “命令失败”不总能推出“对象未写入”

Issue 创建、评论创建与 PR 创建均先提交再返回编号：[objects:770](/Volumes/WorkSSD/Development/factory26/sources/braid/src/objects.rs:770)、[objects:938](/Volumes/WorkSSD/Development/factory26/sources/braid/src/objects.rs:938)、[objects:1632](/Volumes/WorkSSD/Development/factory26/sources/braid/src/objects.rs:1632)。CLI 随后的 `print_issue_created`、`print_pr_created` 都再次读取对象，`print_comment_result` 再次读取投递记录，而且在首次输出编号之前读取：[cli:722](/Volumes/WorkSSD/Development/factory26/sources/braid/src/cli/mod.rs:722)、[cli:735](/Volumes/WorkSSD/Development/factory26/sources/braid/src/cli/mod.rs:735)、[cli:789](/Volumes/WorkSSD/Development/factory26/sources/braid/src/cli/mod.rs:789)。任一后置读取失败将统一进入 stderr 的 `error: {error:#}`、退出 1：[main:48](/Volumes/WorkSSD/Development/factory26/sources/braid/src/main.rs:48)。

这是可证明的已提交后失败路径；本次没有真实失败样本，不能宣称它已制造重复对象。PR 可用 `--request-id` 重试，Issue/comment 没有同类重试键。Agent 若把任意非零退出都当“未执行”，重发创建/评论可能重复。

最小候选是让已知的 committed 编号不被辅助回执读取吞掉：回执扩展失败时仍报告持久化编号、已写入状态、具体读取错误和 `view` 入口。另一路是在写事务内准备必要回执数据再返回，避免提交后为基础成功回执开启第二轮读取。先处理此边界，不据此泛化为所有写操作新增 request-id。stdout 彻底丢失仍是分布式回执的不确定性，不能通过多打印一行保证精确一次。

## 5. list 有默认边界，但无法证明枚举完整

默认仅 open、按编号倒序、最多 30，Issue/PR 的参数类型已清楚：[cli:189](/Volumes/WorkSSD/Development/factory26/sources/braid/src/cli/mod.rs:189)、[cli:275](/Volumes/WorkSSD/Development/factory26/sources/braid/src/cli/mod.rs:275)。SQL 直接 `LIMIT limit`，没有多取一行，也没有下一页条件：[objects:433](/Volumes/WorkSSD/Development/factory26/sources/braid/src/objects.rs:433)。输出裸列表或裸 JSON 数组：[cli:709](/Volumes/WorkSSD/Development/factory26/sources/braid/src/cli/mod.rs:709)。

运行指引已经说明“最近 30 个 open”“历史用 `--state all --limit N`”，这是有效防护：[provider:62](/Volumes/WorkSSD/Development/factory26/sources/braid/src/group/provider.rs:62)。但 Agent 收到恰好 30 项时仍无法知道有无更多项，只能扩大 N 并重读前面的数据；`--state all` 不等于全部返回。PR closed 包含 merged 是明确本地契约，不能按别的工具直觉视为错误：[objects:445](/Volumes/WorkSSD/Development/factory26/sources/braid/src/objects.rs:445)。

小范围候选：先 `limit + 1` 判断截断，保持现有 stdout JSON 数组兼容，在 stderr 给“还有更多，当前仅前 N 项”的提示。若日志证明大量完整遍历，再设计按当前倒序 number 的 `--before`，并决定是否增加带 `has_more/next_before` 的输出形式；不要无证据先实现通用 offset/search/jq。

## 6. 发现性、引用和错误定位

| 面向 Agent 的边界 | 当前源码事实 | 评价 / 最小候选 |
| --- | --- | --- |
| 默认作用域 | Agent 由环境绑定 run 和 writer；拒绝 Agent 自带 `--state/--writer-turn/--external`。宿主 `--state` 必须在子命令前，列表自己也叫 `--state`：[cli:13](/Volumes/WorkSSD/Development/factory26/sources/braid/src/cli/mod.rs:13)、[cli:837](/Volumes/WorkSSD/Development/factory26/sources/braid/src/cli/mod.rs:837) | Agent 无需携带内部身份，是优点；不建议为 Agent 增加运行目录参数 |
| 对象引用 | 命令位置参数为裸 `i64`，Issue/PR kind 由子命令确定；没有 URL、`#N`、branch 或当前目录推断入口：[cli:200](/Volumes/WorkSSD/Development/factory26/sources/braid/src/cli/mod.rs:200)、[cli:290](/Volumes/WorkSSD/Development/factory26/sources/braid/src/cli/mod.rs:290) | 显式 kind+number 避免误目标；帮助写“正整数本地编号，输入 7 而非 #7”，在 parser 边界拒绝 0。无需为了 gh 兼容增加模糊查找 |
| 成员引用 | 接受可选 `@` 并 lowercase；list 拒绝 @me/多成员；分配时校验最新具体候选：[objects:433](/Volumes/WorkSSD/Development/factory26/sources/braid/src/objects.rs:433)、[objects:501](/Volumes/WorkSSD/Development/factory26/sources/braid/src/objects.rs:501) | 错误会给当前候选和 `assignee list`，是很好的可恢复错误；不用另造 alias 系统 |
| 分支引用 | 接受短 branch 或 `refs/heads/...`，必须是已发布 origin branch；不解析任意 commit：[objects:135](/Volumes/WorkSSD/Development/factory26/sources/braid/src/objects.rs:135)、[objects:1576](/Volumes/WorkSSD/Development/factory26/sources/braid/src/objects.rs:1576) | 创建帮助已有 published/base 默认说明；list 的 base/head 参数尚无相同解释 |
| JSON 字段发现 | list 未知字段列 available；view 只报 `unknown view field`，完整字段还由 kind/details 动态决定：[cli:496](/Volumes/WorkSSD/Development/factory26/sources/braid/src/cli/mod.rs:496)、[cli:591](/Volumes/WorkSSD/Development/factory26/sources/braid/src/cli/mod.rs:591) | view 错误同样返回 available，且先校验再读取；只需复用现有键集合，不需 schema 命令 |
| comment JSON | `--json` 为 bool，无法 `--json body`；单条也返回数组，ID 名为字符串 `database_id`，thread_root/reply_to 是数字：[cli:408](/Volumes/WorkSSD/Development/factory26/sources/braid/src/cli/mod.rs:408)、[cli:1113](/Volumes/WorkSSD/Development/factory26/sources/braid/src/cli/mod.rs:1113)、[context:77](/Volumes/WorkSSD/Development/factory26/sources/braid/src/context.rs:77) | 明确说明数组与稳定评论编号；若日志显示 Agent 常误用字段选择，再补 comment 的轻量字段选择 |
| 找不到对象 | Item 的 query_row 直接 `?`，没有附 kind/number；comment view 同样没有附请求 ID：[objects:372](/Volumes/WorkSSD/Development/factory26/sources/braid/src/objects.rs:372)、[objects:1319](/Volumes/WorkSSD/Development/factory26/sources/braid/src/objects.rs:1319) | 在共享读取边界附对象引用与 list/view 恢复入口，保留底层错误，不需要先引入全局错误码体系 |
| JSON 错误 | 即使使用 --json，应用错误仍是 stderr 文本且应用层退出 1：[main:48](/Volumes/WorkSSD/Development/factory26/sources/braid/src/main.rs:48) | stdout/stderr 分开是优点；Agent 必须检查退出码。是否引入结构化错误需实际机器消费者依据 |
| 帮助副作用 | 多数 list/view/edit/ready/merge/close/reopen 变体没有命令说明；ready.undo 与 match-head-commit 也无说明；未实现 merge 选项有明确说明：[cli:187](/Volumes/WorkSSD/Development/factory26/sources/braid/src/cli/mod.rs:187)、[cli:371](/Volumes/WorkSSD/Development/factory26/sources/braid/src/cli/mod.rs:371) | 补 ready 的已发布 head 观察、merge 更新 base、match-head-commit 的完整 SHA 校验与不改 clone 的短说明；不增加重复教程 |

另一处契约不一致：`--json all` 含 `revision`（`ITEM_FIELDS` 与序列化 Item 都保留），而本地契约说 Agent runtime 隐藏内部 revision 字段：[cli:480](/Volumes/WorkSSD/Development/factory26/sources/braid/src/cli/mod.rs:480)、[objects:57](/Volumes/WorkSSD/Development/factory26/sources/braid/src/objects.rs:57)、[local.md:71](/Volumes/WorkSSD/Development/factory26/sources/braid/docs/20-product-tdd/local.md:71)。这是 P3 契约清晰度问题；需决定该 revision 是公开对象版本还是内部字段，不能简单删除后破坏已有调用。

## 7. 应保留的优点与恢复边界

- `--body` 与 `--body-file` 互斥，文件支持 stdin，并明确完整替换/空文件清空以及先落盘再写入：[cli:116](/Volumes/WorkSSD/Development/factory26/sources/braid/src/cli/mod.rs:116)。这里不需要额外交互编辑器或确认流程。
- list 状态是 ValueEnum；timeline 验证 after 非负、每页 1..100，并用全局 ordinal 续读，输出 has_more 和 next_after：[cli:157](/Volumes/WorkSSD/Development/factory26/sources/braid/src/cli/mod.rs:157)、[objects:300](/Volumes/WorkSSD/Development/factory26/sources/braid/src/objects.rs:300)。时间线文本直接给续读命令与 comment view 入口。
- 改派验证错误 remove、过期候选和组合；相同成员是 no-op。正文、关系、事件在一个 transaction 提交：[objects:819](/Volumes/WorkSSD/Development/factory26/sources/braid/src/objects.rs:819)。未生效操作不会留下半次对象变更。
- close/reopen 与可选评论同事务；已在目标状态返回 unchanged 且不重复发评论：[objects:1769](/Volumes/WorkSSD/Development/factory26/sources/braid/src/objects.rs:1769)、[cli:768](/Volumes/WorkSSD/Development/factory26/sources/braid/src/cli/mod.rs:768)。
- PR request-id 返回既有对象，不重新认领成员；base/head 不同明确拒绝：[objects:1548](/Volumes/WorkSSD/Development/factory26/sources/braid/src/objects.rs:1548)。创建前验证关联 Issue；失败后残留同名分支只在 tip 相同才复用：[objects:1571](/Volumes/WorkSSD/Development/factory26/sources/braid/src/objects.rs:1571)、[objects:1623](/Volumes/WorkSSD/Development/factory26/sources/braid/src/objects.rs:1623)。
- merge 有 expected head 校验、prepared intent 恢复、已 merged 返回原 merge_commit；冲突错误保留 PR/base/head 引用：[objects:1864](/Volumes/WorkSSD/Development/factory26/sources/braid/src/objects.rs:1864)。冲突会写持久冲突记录并通知，非零退出不表示“零副作用”，但它明确表示 Git 合并未发生：[objects:1940](/Volumes/WorkSSD/Development/factory26/sources/braid/src/objects.rs:1940)。
- 失效 writer 给“当前调用已失效，本次修改未写入”，是有力的安全重试边界：[objects:235](/Volumes/WorkSSD/Development/factory26/sources/braid/src/objects.rs:235)。不要把这句话推广到所有 CLI 错误。
- 投递回执明确 queued/delivered/unreachable，保留具体 reason，并说明 delivered 仅代表原生会话接收；未把协作信号冒充任务完成：[cli:774](/Volumes/WorkSSD/Development/factory26/sources/braid/src/cli/mod.rs:774)。

## 小规模 before / after 候选（均未实施）

| 调用场景 | 当前源码推导的行为 | 最小目标行为 |
| --- | --- | --- |
| `issue view 1 --timeline --json body` | 成功返回完整时间线，body 被忽略 | 明确拒绝“不支持 timeline 字段选择”，指向裸 --json |
| `pr view 7 --json body` | 只输出 body，但完整读 PR/关联 Issue 讨论与 Git 详情 | 同样输出 body；只读取该 Item 所需数据 |
| `issue edit 7 --title '新标题'` | 输出整个 Issue，包括长 Description | 输出 `issue #7 updated` 与明确的变更事实，正文读回用现有 view |
| `issue view 999 --json title` | 底层无行错误，无请求对象上下文 | stderr 保留错误并指出 `Issue #999`；给 `issue list --state all` 导航 |
| create 已提交、投递/负责人读取失败 | 退出 1，可能尚未输出新 ID | 明确已创建 ID 与回执读取失败；调用者先 view，不盲目重建 |
| list 实际多于 limit | 返回恰好 limit 条，stdout 无截断标志 | 使用多取一条确认并提示仍有更多；初版保留现有数组格式 |

## 未知与验收约束

没有读取真实运行数据库或 rollout，没有当前源码构建的 --help 输出，也没有性能数字。参数行为来自 clap 声明与分派源码；已读成本来自调用图，尚未量化。后置回执失败、误判完整列表、未知 ID 错误对模型的真实影响，需要与另一子任务的日志交叉印证。

view 的 comments、Item、details 是分开的连接/事务，不能保证一次输出是同一 SQLite 快照；这是可见的结构事实，但本次未证明它产生过相互矛盾的 Agent 输出，未列为优先改动。读取函数共用 `Connection::open`，所以普通对象“读命令”也不应被当作对任意宿主路径完全无文件副作用的探针：[objects:186](/Volumes/WorkSSD/Development/factory26/sources/braid/src/objects.rs:186)。本次没有运行它们。

本报告是设计输入，不是独立产品验收。若批准实现，沿用仓库无测试约束：编译/静态检查与获授权的实际 CLI 操作收集原始 stdout、stderr、退出码和对象状态证据；不创建单元测试、模拟集成测试或更名的探针。
