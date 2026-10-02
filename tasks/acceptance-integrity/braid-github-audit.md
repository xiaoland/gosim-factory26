# Braid 与 GitHub 协作体验的断点审查

2026-09-26。
用户已认可本轮内容，并要求进一步审查关键协作差异。
本报告是实施准备材料；没有修改 Braid、Factory 或 SVC 源码，没有新建运行。
对象是 `sources/braid` 当前工作树（HEAD `8921293`，含既有未提交修改），不是把当前代码一概当作 B 冻结包。
B 的事实另以 [097402e69a15 报告](../competition-budget/results/097402e69a15.md) 为准。

## 判断标准

Agent 已有的 GitHub 经验应能用于联系协作者、查看工作、发布代码和合并变更。
同名命令承担不同语义，比缺少一个明确不支持的功能更容易诱发错误。
本轮修正会破坏协作连续性或交付依据的差异，不以完整复制 GitHub 功能表为目标。

GitHub 的通知有 author、comment、mention、push、state_change 等原因；这表明协作不仅依赖父子关系，也依赖明确收件人和参与关系。
参见 [通知原因](https://docs.github.com/en/subscriptions-and-notifications/reference/email-notification-headers)。
这些事实通知不决定谁应实施下一模块，也不替接收者判断工作完成。

## 关键发现与建议

| 项目 | 当前可确认行为 | 对协作的影响 | 建议 |
| --- | --- | --- | --- |
| 显式联系人 | comment 路由只有当前项、关联 Issue/PR 和同一讨论串参与者，不解析 `@成员` | B 中交接评论存在，指定的根成员却没有收到 | 本轮修正：具体成员名可寻址，沿现有消息队列投递评论引用 |
| 联系人的存续 | 关闭后的 Issue 在收尾后 sleeping；合并后的 PR 成员 retired；普通 runnable 选择只处理 active/finalizing assignment | 最终整合可能需要追问已完成任务的作者，当前执行路径没有支持这种继续对话的语义 | 本轮建议补齐：工作项关闭与成员可被联系分开；显式消息可恢复对话，工作项仍维持 CLOSED/MERGED |
| 指派目录 | CLI/context 过滤 root-only，持续指令却遍历全部配置 | Agent 按指令派工被 CLI 拒绝；B 有真实记录 | 已认可修正：统一可指派目录；已有成员作为联系人保留，不等同于可新指派配置 |
| PR 分支 | base 固定为 delivery_ref；`--head` 将提交复制到 `braid/pr-N`，之后原分支更新不会跟随 | `develop → main` 不能按通常 PR 语义表达；已知分支看似被采用，实际只是快照 | 已认可方向继续细化：PR 保存自己的 base/head；显式 head 是已发布分支，merge 与恢复读取该 PR 的分支 |
| ready 与 merge | ready 必须由 PR 自己的 Agent 调用，检查它的 clone 干净、分支和 HEAD，再把 SHA 存为 ready_commit；merge 要求远端 head 仍等于这个 SHA | 发布后的共同代码仍受某个 Agent 的私人工作区限制；其他协作者无法对已发布变更正常推进 ready | 本轮建议修正：ready 表达草稿/可供审阅；合并处理 origin 上的 head/base；版本匹配与 ready 状态分开 |
| 工作关系可见性 | 常用 issue/pr view 基于精简 Item，不显示关联 PR/Issue、子项列表；pr view 也没有 base、当前远端 head SHA 或 merge SHA；完整关系分散在 context 投影中 | Agent 很难从熟悉的入口核对还有哪些工作、当前到底审阅和合并了什么 | 本轮建议补齐现有 view，复用 canonical 关系与 Git 事实，不添加另一份清单 |

“关闭后无法继续对话”依据当前源码路径与本地运行契约，尚无单独真实运行的复现记录；它不是 B 根会话停止的原因，B 根 Issue 当时仍然 OPEN。
该项是对拟议 `@成员` 能力的端到端边界审查，不能只验证名字解析就声称通信闭环成立。

### 1. 让明确的通信意图到达对方

`objects.rs::discussion_changed` 当前按关联和讨论串参与者生成收件对象，没有读取正文中的成员名。
持续指令告诉 Agent “你是 @名字”“成员名用于协作”，却没有实现相应寻址，属于界面对能力的暗示与实际行为不一致。
本轮应补 `@具体成员`，不把 profile 别名解释成任意某个人，不对未知或已改派的成员静默换收件人。
消息保留源 Issue/PR、comment/thread 入口和投递情况；使用者不需要 UUID 或内部 session 参数。

还必须区分：成员是否可联系、是否当前持有该工作项、底层 Pi 进程是否存在、工作项是否已完成。
工作项关闭本身不应抹掉对话地址；恢复对话不等于自动重开工作项或自动返工。
被改派的旧成员与其替代者不是同一个人，具体处理须在 LLD 明确，不能沿“同一个 work-item”将旧名字偷偷映射到新负责人。
只在运行仍可接续的范围内讨论此能力，不为了归档 run 建立常驻通信服务。

GitHub 的创作者和参与者订阅范围更广；当前 Braid 仅同一 thread 的发言者进入相应路由，普通新评论、close 和 merge 也没有完整的创作者订阅。
本轮先确保明确寻址可靠；创作者默认订阅、取消订阅与全仓库 watch 记录为后续差异，不默认引入全套 inbox，也不对所有祖先广播。
普通 push 当前没有通知接线；需要通知他人时可通过明确评论交接，不在本轮默默宣称已有 GitHub 的全部自动通知。

### 2. PR 表达两条已发布分支之间的变更

[gh pr create](https://cli.github.com/manual/gh_pr_create) 用 `--head` 指定源分支，用 `--base` 指定目标分支。
Braid 当前接受 branch/commit 后另建分支，两者名称相同但行为不同。

本轮已有 develop/main 流程，必须一并解决创建、查看、工作目录接线、合并和合并恢复，而不是只增加一个 CLI 参数。
显式 head 分支应被持续引用；从特定 commit 开新分支仍可用普通 Git 完成，无需让 `--head` 兼任“复制快照”。
省略 head 时是否保留自动创建工作分支的便利行为，在 LLD 中给出明确默认，不混入显式 head 的语义。

已有 bare origin + 每工作项独立 clone 是正确边界，merge 也已经在 origin 创建提交并更新 ref，不再依赖根工作区。
尚存的耦合集中在 ready，以及 PR 固定目标和复制 head。
没有证据支持推翻现有 Git 架构。

### 3. 将 ready、发布版本和验收结论分开

[gh pr ready](https://cli.github.com/manual/gh_pr_ready) 改变草稿状态；它不是“这个人的工作区已清空”或“此 SHA 验收通过”。
当前 `pull_request()` 用 `ready_commit.is_none()` 表示 draft，但合并又把 ready_commit 当成必须匹配的发布版本，混合了两种职责。
新提交 push 后，投影仍显示非 draft，merge 却会要求重新 ready，给使用者两个不同答案。

建议对已发布 PR 操作 draft/ready；merge 对当时的 origin base/head 做一致的 Git 合并，不读取其他成员本地 index 或未提交文件。
需要保证“刚刚检查的就是准备合并的版本”时，采用明确的期望 SHA，GitHub CLI 已有 [`--match-head-commit`](https://cli.github.com/manual/gh_pr_merge) 这种表达。
期望 SHA 是调用者指定的版本约束，不代表 Braid 审核过测试或认定产品合格。
现有精确 base/head 合并意图与 ref compare-and-swap 保留其防止错误更新的职责，具体字段随每 PR base/head 一起调整。

### 4. 常用查看入口应足以作出下一步决定

当前 `Item`/`ITEM_FIELDS` 与 canonical 投影各自承载不同信息。
`issue_in()` 已有父项、子项、关联 PR；`pull_request()` 已有关联 Issue 和 base，但 `view` 没有呈现这些。
优先复用已有权威数据，让 issue view 显示直接关系，让 pr view 显示 base/head、当前发布 SHA、草稿状态和已合并结果。
关联只列编号、标题、状态、负责人等足以导航的信息，不递归展开所有任务正文。

GitHub 的 [pr view 字段](https://cli.github.com/manual/gh_pr_view) 也将分支、提交、关联与状态作为直接可查询信息。
无需照搬全部字段；让当前工作真正依赖的信息可见即可。
diff、log、fetch 继续使用普通 Git；不为拥有更多 `braid` 子命令而包装已有工具。

## 保留的有意差异与暂不扩大项

- 指派产生新的具体成员，不建立独立“增加成员”步骤；同一能力配置的不同工作项仍是不同 Agent。这是已确认的会话边界，不按 GitHub 账号复用方式改成共享会话。
- Braid 的 description/comment 是可编辑上下文；hide 带理由、resolve、回复和 reaction 已有支持。这些是产品能力，不因 GitHub 普通 Issue thread 的限制而删除。
- 关闭 Issue 不表示所有相关代码自动验收；merge 不根据评论措辞作产品决定。父子关系只表达组织关系，不自动选择下一批任务。
- 暂不加入 GitHub Actions、review 审批闸门、保护分支、权限角色、项目看板或全站通知设置。
- 当前 Issue/PR 分开编号，裸 `#1` 会有歧义；本轮继续使用 `Issue #1` / `PR #1` 明确地址，不为对齐编号迁移历史状态，也不自动解析模糊引用。
- CLI 还有多个小差异，例如 close 的自定义原因、JSON 字段名和缺少 list 过滤；目前没有证据表明它们是本轮协作中断的关键，不与核心改造混做。

## 与本轮其它工作的边界

Factory 将 quiescent 导出为正常生成是调用方的完成判定缺陷，不是 GitHub 功能缺口。
按已认可方案在 Factory 保留未完成状态和产物，Braid 继续只报告运行与工作项事实。
SVC 内容改进解决如何设计判据、取得证据与判断结果；它不能修复没有收到消息的问题。
variant 指引规定 develop/main、最终自动化验收与角色用法；通用 Braid 不认识这些特定工作政策。

## 实施准备所需的判别依据

LLD 与独立预演应沿一条完整协作路径检查：创建并指派 → 被点名的成员收到原评论 → 关闭后仍能回答明确追问 → 发布分支 → PR 引用当前分支 → 在其他 clone 执行合并 → 调用方区分未完成与正常交付。
同时检查源/目标分支变化、改派后的旧名字、评论编辑/hide、自发消息回声这些真实边界，优先复用现有队列和持久身份。
预演用于检查方案接口与盲区，不让阅读代码的 reviewer 充当行为验收。
真实实验应保留对象、投递、原生输入、Git 和生成应用的证据；不以“命令存在”“评论已写”“退出码零”代替后续效果。

## 源码证据入口

| 事实 | 当前源码 |
| --- | --- |
| 评论收件范围 | `sources/braid/src/objects.rs::discussion_changed`，约 650 行 |
| root-only 列表差异 | `objects.rs::assignee_directory` / `profile_for_login`；`group/provider.rs::local_instructions` |
| 关闭与最终收尾 | `store/mod.rs::prepare_work_item_finalization`、`consume_closed_activation`、`claim_runnable_turn`、约 5153 行的 final_assignment_lifecycle |
| PR 分支复制与目标 | `objects.rs::create_pr_with_profile_and_head`、`pull_request`、`merge`、`apply_merge` |
| ready 依赖本地 clone | `objects.rs::ready`，约 1218 行 |
| 常用查询缺少关系/版本 | `cli/mod.rs::ITEM_FIELDS` / `print_item`；`objects.rs::Item`、`issue_in`、`pull_request` |
| 独立 clone 与 origin | `worktree.rs::provision`；`local.rs::run`；`objects.rs::apply_merge` |
| 调用方导出 | `variants/pi-team-k3-root-only/run.py` 约 283 行；`scripts/braid_runtime.py::load_delivery` |

源码行号仅用于本次调查定位，后续实现会变化；函数和已记录运行证据是稳定入口。
