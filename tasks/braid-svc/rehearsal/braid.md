# braid 本地产品链路静态预演

结论：已确认的 Issue/PR/comment 方案可以沿现有 queue/group/session 链实现，但必须先打通本地启动、CLI 写入与交付终态三个接点。最容易留下的假成功是数据库已经更新、模型仍读旧上下文，或 PR 已完成、Factory 却冻结了另一个目录。

本报告是实施前的静态预演，不是实际验收。读取了 packet、design、verification、plan、inquiry，以及 `sources/braid` 原始 HEAD `08c1c10d3b61b24119580ba8af14e2a393f7ea33`。下文 braid 源码行号均指该 HEAD，可用 `git show HEAD:<path>` 复核。`src/local.rs` 的 Stage/Handoff/Refresh 循环只作为未批准草稿识别，没有当作现有产品保证。Factory 行号指本次读取的未提交工作树。未构建、运行模型、修改实现或提交；只新增本报告。

## 无人值守收敛的推荐决定

建议让根 Issue 的现有 Issue Agent 负责本次 requirement 是否完成及交付内容的判断。这里是根工作项的责任，不新增 supervisor、强制 reviewer 或固定角色往返。PR Agent 负责实现和自检，根 Issue Agent 可以在已有 turn 中直接检查并接受多个 PR；需要修正时通过对象和 comment 产生工作，不要求每个 PR 都经过固定轮数。

| 决定 | 负责者与操作 | 运行时必须验证的事实 |
| --- | --- | --- |
| PR 可以被接受 | PR Agent 通过本地 CLI 将 PR 标为 ready，说明实现与自检结果。 | ready 对应明确的 head commit；不能把未提交文件当作该 PR 的交付内容。 |
| 接受并合入 PR | 根 Issue Agent 检查当前 PR 和交付树后调用 `pr merge`；冲突或验证失败回到该 PR。 | 合入的是指定 head，目标是本次 run 的 delivery branch；不把 ready 自动解释为 merge。 |
| 根需求完成 | 根 Issue Agent 在必要实现已合入、当前交付树自检结束、未完成事项已明确处置后调用 Issue close，reason 为 completed。 | 根 Issue 的完成声明、相关工作项和 PR 状态、交付提交必须一致；关闭为 not-planned 或遇到 blocker 不等于生成成功。 |
| 可以交给 Factory 冻结 | Braid 根据对象终态和现有执行状态作机械判断。 | close/merge 的 finalization 已结束，没有在执行、待执行、待 reset 或未决的执行；固定交付 commit，停止会话并拒绝之后的控制写入。 |

`pr ready`、`pr merge`、Issue close/reopen 是本地生命周期 CLI 的具体化，不能继续依赖远端 GitHub 或人类。它们补全 design 已留给预演处理的收敛空白，尚不是已经实现或已经逐项批准的命令接口。

PR ready、merge 完成、实现失败和明确请求设计判断，应通过已有事件队列通知相关 Issue group。根 Issue 可能正在执行，因此普通通知可以进入 pending batch，等当前 turn 结束后处理；不需要强行打断或建立新的通知后台进程。自己的 description/comment 回声抑制仍保留，但自己发出的 close、merge 等生命周期命令必须生效，不能一并过滤为 OriginEcho。

根 Issue 建立时记录本次 run 唯一的 delivery branch；可使用根 Issue 已有专属 worktree 的分支，不必再建独立集成服务或多余 worktree。PR 默认从该分支的当前提交创建实现分支，根 Issue 合并到该分支并检查其结果。一个 run 的对象存储只服务这次 requirement，避免从任意图遍历猜测哪些外部工作项属于本次交付。

保留 1:N / N:1：同一个 Issue 可以通过不同请求 comment 创建多个 PR；一个 PR 可以关联多个 Issue，PR Context 读取所有直接关联 Issue。相同请求 comment 的 ensure 仍返回同一个 PR，不能把目标 Issue 身份用作 PR 唯一键。多个 Issue 关联同一个 PR 时只合并一次；合并事件通知各相关组。根 Issue 对需求满足作最终判断，不由“所有边都关闭了”推导业务正确。

建议根 Issue close completed 在仍有未处置的必要子项、open PR 或未决实现时返回具体阻塞引用，让当前 Agent 继续处理。明确放弃的探索 PR 可以关闭并记录原因，不应被迫合并；关闭探索分支不能自动关闭关联需求。根 Issue 已关但 finalization 未完成时，运行仍未成功。若根 Issue 仍开着，而队列、debounce、执行和恢复都已耗尽，返回可诊断的 incomplete/stalled，而不是无限等人、循环自唤醒或伪造 completed。

冻结应使用返回的不可变交付 commit 导出应用，不复制最后一个 Agent 的 cwd，也不选择编号最大或修改时间最新的 PR。成功结果至少关联 root Issue、delivery branch、delivery commit、对象数据库和 provider session 映射。历史 Unknown 已有可验证恢复结果时不永久阻塞；当前未决执行不能被忽略。应用测试失败可以是有效生成结果，但 provider 正常退出本身不是完整生成结果。

有一处必须带入方案/验收复核的授权细化：Factory 当前 `scripts/factory.py:293–296` 明确禁止创建 Git 提交，而已确认方案要求本地 branch/worktree 和 PR 合并。建议将运行授权改为“允许本次临时生成仓库内的本地 commit/merge，禁止 push 和修改开发源码仓库”。初始空应用也需要一个本地基线提交才能创建 worktree。这不是恢复远端 PR 的 bootstrap 补偿，而是本地 Git 的前置条件。不能由 CLI 偷做提交绕过原禁令；本报告不代替用户批准这一文字调整。

## 从需求到交付的实际路径

1. Factory 创建隔离的 run 目录、需求输入、空应用 Git 仓库及本地基线；传入明确的 repo、root requirement、provider 和 Braid state 位置。Braid 建根 Issue，并分别记录 activation 与首个需求 Wake。只写 assign 会按上游契约保持 idle，不会自动开始任务。
2. Braid 通过本地存储物化 Issue Context，建立其专属 group/worktree/session。运行指令说明对象 CLI、无人值守授权和交付责任；SVC 仍仅通过原生核心的独立 user-scope 导航出现。
3. Agent 使用 CLI 改 description、创建或 hide/delete comment。正文变更、writer group/turn 和事件在同一事务内落库。Group 依据依赖关系执行已有 reset；相同逻辑 group/worktree 保留，实际新 session 接收当前完整正文。
4. Issue Agent 用稳定请求 comment 调用 PR ensure，得到本地 PR、关联、branch/worktree 与 activation。PR Agent 可读取所有关联 Issue、修改设计及实现，不经过 Stage 枚举。自写产生的正文变化不自打断；下一次正当执行前自动物化最新 Context。
5. PR ready 驱动根 Issue 的接受/修改判断，CLI merge 维护交付 branch 与 PR 生命周期；根 Issue 在交付检查之后完成。Braid 等待终态处理结束并输出交付 commit，Factory 才冻结、评测和归档。

## 五个容易卡住的切面

### 1. 配置和激活看似本地，实际仍等待 GitHub 或第一个人类事件

`src/config.rs:38、594–603` 要求 GitHub 配置和 App/secret。`src/runtime/mod.rs:77–91` 启动时立即连接 GitHub 并读取 webhook secret，129–145 还启动 mention、outbox、reconciliation 网络 worker。`src/group/issue_agent.rs:280–303` 只接受 assign/mention，并检查 GitHub App assignee；`src/store/mod.rs:2333–2344` 区分 activation 和普通 Wake。单纯换 CLI 子命令或把 GitHubClient 留作空壳都不能启动本地任务。

最小修正方向：让本地组成入口只装配本地对象存储、既有 queue/group、provider factory；移除本分支不用的 GitHub 配置要求。根 requirement 的 activation 和首条输入是显式的领域事实，不假扮可信人类 mention。无需保留一个永远未使用的 GitHub backend 插件。

最小检查：在没有 GitHub token、App key、secret、remote，且网络不可用的临时环境，用确定性 provider 启动一条本地 requirement，观察恰好一个根 Issue group 和首个 turn；只执行独立 assign 的控制样本应保持 idle。该检查在实施后运行，本次未运行。

### 2. CLI 写入绕过失效屏障，或错误使用进程环境识别 writer

`src/cli/gh_cmd.rs:4–68` 只有 comment create 和 PR ensure；`src/writer/mod.rs:38–86` 以 profile 标记 comment 写入，没有当前 group/turn 的强制前置条件。`src/store/mod.rs:4182–4247` 已有旧 session/turn 的 reset 屏障，但新本地 CLI 若直接写正文就会绕过它。`src/provider/factory.rs:16–21` 的 Codex factory 共享连接，因此不能把每个 turn 的身份仅放到共享 app-server 进程的一个可变环境变量里。

最小修正方向：在发给该物理 turn 的运行上下文中提供其调用身份，由 CLI 将 writer group/turn 传入存储操作；存储在同一个写事务里校验当前身份是否仍允许控制操作。origin 区分发起组和接收组，不能只记录一个所有 Agent 共用的布尔值。没有必要增设账户体系；这里是现有运行的控制前置条件。

最小检查：两个逻辑 group 的 CLI 写入能区分作者；触发 A reset 后，用 A 的旧 turn 身份执行 description edit、comment hide、PR merge，全部拒绝且不产生正文/事件半写入；B 的合法写入仍可完成。自己 close Issue 的生命周期不能被 self-echo 过滤掉。

### 3. 更新 revision 后仍向旧物理会话派发

`src/group/dispatch.rs:422–454` 领取 turn 后向现有 session 发送 references；`src/store/mod.rs:4646–4659` 选取 `COALESCE(w.context_revision,ps.context_revision)`，没有证明该 session 已收到新版本。`src/producer/reconcile.rs:197–202` 重渲染并记录 revision，也不会自动替换这个旧输入。另一方面，`src/store/mod.rs:2352、4278、4302` 广泛排除 agent-origin，不能满足精确自身回声规则。

最小修正方向：完整正文和 comment 生命周期以本地事务存储为权威，既有 projector 负责 materialize；在 group 允许开始下一次正当 turn 的边界确认物理会话与当前 Context 相容。需要替换时沿现有 reset/session 创建路径完成，不把 revision 改成新值来跳过输入更新。非 Agent 的跨面 description 失效保留 debounce；自身修改不打断当前 turn、不额外自唤醒。

最小检查：先把包含 OLD 正文及两个可见 comment 的 Context 送入 session；通过真实 CLI 改为 NEW、hide 一个、delete 一个。捕获下一 session 的实际输入，证明只有 NEW、hide/delete 元数据且没有旧正文。另测 self-write 不启动多余 turn，但随后另一条合法事件唤醒时自动获得 NEW。断言 group/worktree 身份不变，不能只断言数据库 revision 改变。

### 4. PR 对象已本地化，worktree 仍要求远端分支且 N:M 被 ensure 压成 1:1

`src/worktree.rs:48–59` 验证 GitHub remote URL，89–108 执行远端 fetch 后才创建 worktree。`src/group/issue_agent.rs:189–206` 从 GitHub 查询 default branch；`src/group/pr_agent.rs:25–53、57–81` 在 Context 准备和 worktree 创建中仍依赖 GitHub。`src/writer/prepare.rs:11–24、54–83` 从远端 comment/Issue 得到实现请求；`src/store/gh_writes.rs:129–180` 则已经具备请求键和 branch 元数据，可以保留幂等语义而替换平台读取。

最小修正方向：本地 ref 决定分支起点，source repo 只作为干净对象源；group 的有效 cwd 是各自 worktree。保留已有 worktree 重用校验，删除 remote 验证/fetch。PR ensure 用本地请求 comment 的身份幂等建立 PR，关联表保留独立 N:M 关系；不要改成每个 Issue 只有一个 implementation 对象。

最小检查：无 remote 的本地 repo 中创建两个 Issue、三个请求 comment，证明同 comment 重试仍一个 PR，同 Issue 不同 comment 可以产生两个 PR，第三个 PR 可关联两个 Issue；所有实现 worktree 可用且相互不写错目录。Context reset 后已有未提交应用改动仍在原 worktree。

### 5. merge、finalization 和冻结之间留下提交丢失或假终态

`src/group/dispatch.rs:54–87` 在 close 后安排 finalization；这不是收到 close 就能退出。`src/group/worker.rs:158–191` 记录 provider terminal，不代表业务完成。Factory 当前 `scripts/factory.py:315–348` 在 braid 进程成功后设置 generated，356 复制原 `app` 目录；多 worktree 后该目录可能没有最终实现。现有 CLI 没有本地 ready/merge/完成链，草稿 `src/local.rs` 的 Action::Complete 不能填补它。

最小修正方向：按本报告的根 Issue 责任与明确 delivery branch 收敛。merge 需要验证被接受的 head 与当前目标 base；冲突应留下可处理的 PR 状态和事件，不能宣告 merged。Git ref 更新与 SQLite 状态不属于同一事务，不能声称原子：复用现有 write-intent/receipt 思路记录该次 merge 的精确输入与结果，恢复时依据实际 Git ancestry/ref 收敛，不重放一遍未知 merge。所有 lifecycle finalization 完成后再冻结固定 commit；finalization 新发现需要修改实现时，应产生后续工作或重新打开相关对象，不能在已合入 PR 后偷偷追加未交付代码。

最小检查：两条 PR 分别添加不同可见产物并合入同一 delivery branch，冻结树必须同时包含二者，且来源与返回 commit 一致。再注入 merge 冲突及“Git 已更新、DB 尚未标 merged”中断，确认不成功冻结、不重复合并，修复/恢复后能收敛。根 Issue 提前 close、仍在 finalization、当前执行 Unknown 时均不能得到成功交付；历史 Unknown 已妥善恢复不永久卡死。

## 建议实施顺序

1. 先确定本地启动与交付契约：根 Issue activation/首个 Wake、临时 Git 提交授权、delivery branch、close/ready/merge 的责任和最终结果字段。删除旧 Stage/Handoff/Refresh 草稿的运行入口应在有可替换链路的实施提交中完成，本轮不动。
2. 实现单一存储的 Issue/comment/PR 正文、稳定身份、关联和带 writer 前置条件的 CLI 事务，先走通一次 create/read/edit/event；保留原 EventKind 的领域意图，不制造 GitHub webhook payload。
3. 将 context materialize、Issue/PR activation、worktree 与 runtime composition 改接本地 source；随后接入现有 queue/group 的自动 reset、下一 turn 的 Context 相容检查和恢复。不能只在 initial materialize 改一次来源，遗漏 reopen/reset 路径。
4. 在同一对象链上实现 ready/merge/root completed/finalization 收敛，解决 Git 与数据库的恢复边界；再让 Factory 从交付 commit 导出应用并归档准确的对象、worktree、session 映射。不能先宣布应用 generated，再补填终态。
5. 运行上述五个切面检查及已复核的局部故障样本，再执行真实四组 bench。静态报告和确定性 provider 都不能代替真实核心、实际输入与冻结应用的验收。

## 需要主 Agent 带回复核的内容

本报告没有批准新的产品边界。根 Issue 接受 PR、明确 delivery branch 和自动终态判断，是对 design 已明确留白的无人值守收敛细化，建议纳入验收矩阵一起复核。必须显式处理 Factory 原有“禁止 Git 提交”与本地合并的矛盾；如果仍要求运行时一律不能创建提交，则无法按这里的真实 branch/worktree/merge 路径实施，需要回到产品方案决策。

未发现需要新增通用插件框架或固定多 Agent 阶段的理由。现阶段也不应增加无限重试、自发审查轮数或启发式成功判定。实际测试结果、合并恢复和退出行为均尚未验证。
