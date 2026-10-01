# Braid 共同 Git 仓库技术预演

本页是 2026-09-25 的只读设计预演；产品范围与授权以 [packet](packet.md) 为准。本次预演不改源码或运行实验；SVC 方法改稿移出本轮。

## 决定与对象边界

采用 `state/origin.git` 裸仓库作为一次 local run 的共同 origin。它保存已发布的 `delivery_ref` 与 `braid/pr-N` 等分支；每个工作项的 Agent 在 `state/worktrees/...` 持有**独立 clone**。输入 `Profile.workspace` 是初始化用的原始 checkout，不再是运行中的 canonical repository 或 Agent 的 Git common dir。所有 Agent 的本地 HEAD、index、未提交文件和本地 commit 独立；只有显式 `git push` 才发布到 origin。`git fetch` 获取他人的发布成果，不自动 reset、merge 或 rebase 本地工作。

直接用文件路径 remote 的原生 `git push/fetch`，无 HTTP/SSH daemon。Braid 仍负责 Issue/PR 对象事实、分支初始化、ready 所引用的已发布提交，以及 merge 的目标 ref CAS；不接管 Agent 的冲突解决或工作区。公开的 `local/run` 是对象仓库标识，不应混同裸仓库路径。

## 实际调用链与最小修改点

| 路径 | 当前行为 | 应改语义 |
| --- | --- | --- |
| `local::execute` / `config::Profile.workspace` / `LocalObjects::initialize` | 要求所有 profile 指向同一个 checkout；在此建 delivery branch，`local_run.repository`、`request.json.repository`、`result.json.repository` 都指它。 | 首次从输入 checkout 的 HEAD 初始化 `state/origin.git` 和 delivery ref；`local_run.repository` 与 `result.repository` 指向裸 origin，`request.json` 另保留输入 checkout 作为身份和 provenance。恢复时核对两条路径及 origin 的已记录身份，不重建或覆盖 origin；结果的 `delivery_commit` 从 origin 解析。初始创建应可在中断后识别并完成，不能见目录存在就误判已初始化。 |
| `worktree::provision`、`group::issue_agent::provision_issue_agent_worktree`、`group::pr_agent::provision_pr_agent_worktree` | 从 `Profile.workspace` 执行 `git branch`/`git worktree add`；所有目录共享普通 refs，根 Issue 本地 branch 就是 delivery branch。 | 改为从 origin `git clone --no-local --branch <published-branch> <origin> <target>`，每个工作项拥有自己的 `.git` 与 remote；随后在 clone 内建立其私有本地工作分支。根 Issue 也如此。`--no-local` 避免本地路径 clone 默认直接拷贝 refs/objects 时与并发 push 竞争，使用正常本地 Git transport；见 [git-clone 官方说明](https://git-scm.com/docs/git-clone#Documentation/git-clone.txt---local)。clone 的 `user.name`/`user.email` 和 `.git/info/exclude` 中 `.braid/` 需显式配置，输入 checkout 的本地配置不会随 clone 继承。目标已存在时核对 Git 根、origin URL 和所记录分支，不能只凭目录/HEAD 名接受。 |
| `group::issue_agent::resolve_issue_worktree_ref` | 唯一 linked branch 或 delivery ref 被当成共享源 checkout 内的 ref。 | 解析为 origin 上**存在的已发布**启动 ref；无唯一 linked branch 时用 delivery。Issue 本地提交与共同 ref 分离。根 Issue 直接改本地文件或 commit 不改变 delivery；须明确发布或通过 PR 集成。 |
| `objects::create_pr_with_profile` | 在 `local_run.repository` 从当前 delivery commit 建 `braid/pr-N`，同一次调用写关联和指派事件；指派后 PR Agent 才物化工作树。 | 保留此顺序，但在 origin 建源 ref，保证 branch 可读后才提交 PR 对象/关联/指派。新 PR clone 从该 origin ref 启动。现有 `--request-id` 幂等入口及 Git/SQLite 跨事务中断窗口须保留：若 branch 已建而对象未提交，重试验证其原始 base 再接续或明确报错，不静默改写。Issue clone 的本地 commit 不因 create 自动成为 PR head；PR Agent 须自行整合，或先通过明确 push 发布。 |
| `objects::ready` | 查 PR 工作树干净、本地 HEAD 等于共享仓库分支 HEAD，存 `ready_commit`。 | 保留当前 PR 执行身份和 clean 检查；要求当前 clone 的分支/HEAD 与 origin `refs/heads/braid/pr-N` 的已发布 OID 一致。单独本地 commit 不算 ready；引导 Agent 先 push。重复 ready 同 OID 幂等，发布新 OID 后必须再 ready。`PullRequestSnapshot::draft`/context 的 ready 状态仍由 `ready_commit` 决定。 |
| `objects::merge` / `apply_merge` / `recover_merges` | 从同一 source 仓库读 PR/delivery ref，计算 merge commit；先检查 Issue #1 工作树干净，CAS delivery 后再检查并 hard reset 该树，最后写 PR merged。 | 在 bare origin 读取源/目标已发布 OID，用已有 `merge_commits` 构造合并提交、写 prepared intent；随后以一次 `git update-ref --stdin` 事务验证源 ref 仍为 `ready_commit`，并 CAS 更新 delivery ref。删除所有 Issue #1 目录/index 检查与 reset。重启依据 prepared 的 base/head/result 与 origin refs 恢复；若 delivery 为 base 则重试同一 Git ref 事务，若已为 result 则补 SQLite 收据，其它值保留现场并报冲突。merge 不更新任何 Agent 的 HEAD。Git 冲突只写对象反馈，Agent 在自身 clone fetch、解决、push 新源 head、再次 ready。 |
| `store` 的 `worktrees`、重指派、reset 与 resume | `source_path` 是共享 checkout；改派待原生 teardown 后把同一 worktree 转给新 Agent；reset 和 provider resume 复用保存的 `path`、`head_ref`。 | 保留“同一工作成果目录交给继任者”的事务和 fencing，`path` 改为独立 clone 路径，`source_path` 明确记录 origin；保存本地 branch 与启动的发布 ref，不把两者当同一个 HEAD。恢复时验证 clone remote 指向本轮 origin、目录/branch 仍可用，使用原 clone 的脏文件、本地提交和当前 HEAD；绝不重新 clone 覆盖。新物理 session 的 effective profile workspace 继续指此 clone。 |
| `group::provider`、CLI/context、`local::sessions` / `result.json` / `evidence` | PR prompt 称当前分支为 head ref；session manifest 记录 worktree；结果仓库指输入 checkout。 | prompt 和 CLI 反馈区分本地分支、origin 发布 head、ready OID、实际 merge OID；Issue prompt 告知 push/fetch 路径。session manifest 的 `worktree` 保留为 Agent clone 路径；result 的 `repository` 指 origin，`delivery_ref`/`delivery_commit` 只指已发布集成版本。原始输入 checkout 另作 provenance。证据快照里的对象/结果路径随上述事实走，无需另造证据格式。 |

## 发布、合并和恢复的精确语义

1. 首次请求验证输入 checkout 的 HEAD 与 `delivery_ref`，建立裸 origin，把该 HEAD 发布到 delivery，设置 bare `HEAD` 指向 delivery，再持久化 run 身份并激活根 Issue。各 Agent clone 只从 origin 创建。`state` 的运行锁继续保证唯一 Braid runtime；原生 Git ref 的并发由 push 的 fast-forward 规则及 Braid 的 `update-ref <ref> <new> <old>` 约束。
2. 子 Issue 初次物化从其唯一已发布 linked branch 或 delivery 建 clone；无唯一分支时从 delivery 建 clone 的个人分支。PR create 在 origin 从当前 delivery 建 `braid/pr-N`，关联至少一个 Issue，可立即指派新 Agent。此时 PR branch 仅含 base，并不代表提交了实现。
3. Agent 在自身 clone commit 后，明确 push 到目标 origin ref；`ready` 以 origin PR ref 的 OID 为事实，同时核对调用者的 clone HEAD。其他 Agent fetch 后自行决定何时整合。若 PR 源 ref 变了，既有 ready OID 不再允许 merge；再次 ready 覆盖版本。
4. merge 固定 ready OID 和当时 delivery OID，冲突时无目标 ref 更新。无冲突时写 prepared merge commit，再执行同一 origin 上的 ref 事务：`verify refs/heads/braid/pr-N <ready-oid>`、`update <delivery-ref> <merge-oid> <base-oid>`、`prepare`、`commit`（通过 `git -C <origin> update-ref --stdin` 输入，完整事务从 `start` 开始）。若源或目标已变化，整次事务失败，delivery 不推进；成功后把 PR 标为 merged 并通知关联 Issue。中途失败由 `recover_merges` 补齐；它不读取或修改任何 Agent clone。Issue close 是 Agent 的独立对象决定，不由 Braid 根据 merge 自动触发。[git-update-ref 官方说明](https://git-scm.com/docs/git-update-ref#Documentation/git-update-ref.txt---stdin)明确同批 `verify`/`update` 在 refs 可锁定且旧 OID 同时匹配时才执行修改。
5. 改派、context reset 和同请求 resume 均保留原 clone 及 Git 私有状态。若目录遗失或 remote 不符，阻塞并说明原因；不得从当前 origin 重新物化一个空目录冒充原成果。最终 `result.delivery_commit` 必须取 origin delivery 的确切 OID，Factory 以此冻结与导出，不能取任一 Agent clone 的 HEAD。

## 必须在实施计划中定下的边界

- 原生 push 可在 Braid 的 SQLite 事务外更新 origin，但 `update-ref --stdin` 的 `verify` 源 ref + `update` 目标 ref 可在**同一 Git ref 事务**里消除“检查 ready head 后、推进 delivery 前”这段竞态；不用增加 push 控制层。事务成功之后，PR Agent 仍可能推送新的源 head；Braid 的 merged 事实必须指明当次集成的确切 ready/merge OID，不宣称后续提交已集成。Git ref 事务与 SQLite 收据仍不原子，继续由 prepared intent 恢复。官方文档也说明并发读者可能在多 ref 更新中看到部分结果；本事务只修改 delivery，源 ref 仅验证。
- PR create 目前既建 branch 又立即 assign，且 branch 创建与 SQLite commit 不能原子化。必须保持“branch 已可读才发 assign”，并为崩溃后孤立 branch 定义幂等核对/处置；不能仅把 `repo.branch` 改成 `git push` 就忽略这段窗口。裸 origin 首次初始化也有同类中断窗口。
- 现有 `worktrees` 表的名称可以暂存；字段 `source_path` 和 `head_ref` 需要在新代码中明确定义，不应靠重命名迁移制造风险。`Config.repository = local/run` 是逻辑对象名，`Profile.workspace` 是输入材料，`LocalObjects::repository()` 才应是 origin 路径。不能把三者继续当同一个仓库。
- 输入 checkout 的 Git config 不会自动传给 clone；提交身份和 `.braid/` 排除规则需每个 clone 落地。直接 `git push/fetch` 足够，无网络 daemon、共享普通 refs worktree、额外沙箱或 Agent 生命周期机制。
