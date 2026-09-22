# Assignee 投影：Braid 本地 LLD 取证

取证基线：Factory 工作树当前 `sources/braid`，Braid `673c119`（`reuse blocked agent worktrees on recovery`）。本页只描述当前实现和最小接缝方案；不把已有文档中的目标合同当成已实现行为。

## Current evidence

### Profile 注册、持久化和运行时装配

- `local::Request` 接收 `profiles`、`defaults`、`bindings`；`Profile` 当前字段包括 `id`、`display_name`、`tags`、adapter/provider/model/reasoning、`user_instructions` 和上下文限制，但没有 `description`（`sources/braid/src/local.rs:23-37`、`src/config.rs:174-199`）。Factory 的 `scripts/native_profiles.py:95-98` 把 `display_name` 直接写成 profile ID，当前 `harness/profiles/*.json` 也没有 description。
- `local::config` 校验 profile ID 唯一、binding 一一对应、adapter 一致和默认 ID 有效；首次运行把完整请求材料写入 `state/request.json`，恢复时要求 profiles/defaults/bindings 完全相同（`src/local.rs:144-204, 289-315`）。所以内部 profile 材料已经由 Harness 持有并可恢复，但并不等于可投影的公开协作者目录。
- `drive` 为每个 `(issue|pr) × profile` 启动一个 `GroupSpec`。`GroupSpec::new_with_binding` 用 profile 和 binding 计算 `ProfileRecord`，注册到 SQLite；当前 `profiles` 表只存 `profile_id`、revision、effective digest、provider kind、tags（`src/local.rs:350-366`、`src/group/provider.rs:19-57`、`migrations/0001_initial.sql:33-40`）。它没有公开登录名或能力说明。
- 0006 migration 已把 `local_run.default_issue_profile/default_pr_profile`、`local_items.desired_profile_id`、`local_items.assignment_revision` 和 `assignments.assignment_revision` 接上（`migrations/0006_profiles_assignment.sql:1-5`）。`issue/pr create` 默认写入相应 default；显式 profile 先做存在性校验。每个 assignment 记录采用的 profile revision，实际 provider/session 也按 profile 过滤。

### 当前 CLI 和 Context 的可见面

- CLI 已有 `profile list` 和 `profile view ID`，输出 profile ID、adapter、revision、digest、tags；`profile view` 没有脱敏的公开协作者模型（`src/cli/mod.rs:55-66, 482-497`、`src/objects.rs:167-179`）。这是当前最直接的 agent-profile 泄漏入口。
- `issue create`、`issue edit`、`pr create`、`pr edit` 只有单值 `--assignee`，参数实际命名为 profile ID，并直接传到 `create_*_with_profile`/`edit_with_parent_and_profile`（`src/cli/mod.rs:116-140, 173-198, 517-579`）。默认文本和 JSON item 还显示 `desired_profile` 与 `assignment_revision`；`context issue|pr` 额外打印 `Profile: <id>`（`src/cli/mod.rs:285-297, 358-376, 499-505`）。
- 运行时注入的 `issue_system_prompt`/`pr_system_prompt` 当前列出 `issue create` 和 `issue edit`，但没有任何 assignee 用法；正文明确出现 Braid 协议和 `Profile User Instructions`（`src/group/provider.rs:60-88`）。即使不调用 profile 子命令，Agent 也没有被告知如何把 Issue 指给另一协作者。
- Canonical Issue 的 `assignees` 目前永远是单个 `{node_id: "braid", login: "braid"}`，完全不读取 `desired_profile_id`；PR 的 `assignees` 使用默认空向量（`src/objects.rs:796-827, 834-860`）。因此实际注入的 Context 会显示 `@braid`，而不是所选 profile 或目标 Agent。`context::render_complete` 只渲染这个 canonical 字段（`src/context.rs:260-319`）。

### 指派触发、切换和恢复

1. 首次本地运行先建立根 Issue #1，再写入 default profile；初始化和 `issue create` 都发出 `Assign(activate)` 加 `Wake`。Assign 事件给对应 profile 物化 provider session，Wake 随后产生第一轮（`src/objects.rs:106-130, 388-422`；`src/store/mod.rs:2263-2279`）。
2. `issue/pr edit --assignee X` 在一个 SQLite immediate transaction 内先验证 X 存在；同值直接无操作。变更时递增 `assignment_revision`，把旧 assignment/agent/provider session 标为 stopping，并发出一个 Assign 事件（`src/objects.rs:181-241, 448-509`）。
3. 每个 profile worker 都能看到 pending Assign，但 `begin_agent_assignment` 只接受 `desired_profile_id == 当前 profile`，并要求不存在 stopping assignment；因此不会让多个 profile 同时取得同一 Issue。旧 writer 在数据库查询中立即失效，旧 worktree/讨论仍保留（`src/store/mod.rs:3775-3935, 4812-4845`）。
4. worker 每轮先调用 `retire_reassigned_sessions`，adapter 的 `SessionManager::remove` 成功后才把旧 session/assignment retire；之后新 generation 才能物化，并优先复用最近保留的 worktree（`src/group/worker.rs:83-109, 297-366`；`src/store/mod.rs:3211-3281, 3876-3926`）。停止失败会让运行进入 incomplete/blocked，不能以 DB 字段更新冒充原生会话已停止。
5. 当前 Assign 的调度语义是“物化一个 idle session，不自动产生 turn”；store 明确注释 native Issue assignment 不产生 turn，且非 `mention/activate` 的 Issue assignment 使用 `preserve_wake=false`（`src/store/mod.rs:2267-2269`、`src/group/issue_agent.rs:304-325`）。所以重新指派后目标 Agent 会得到当前 Context 的新 session，但通常要等后续 comment/edit/wake 才开始一轮。初始根 Issue 因额外 Wake 而例外。
6. 重启时每个 profile worker 先恢复未完成 Context reset，再按 `profile_id` 和 work-item kind 查找可恢复 provider session。兼容的 session resume 并记录次数；缺 worktree、profile/revision/instruction 不匹配或 provider 失败则 block；活动 turn 丢失会被标成 unknown，不另起并行 writer（`src/group/worker.rs:236-367`、`src/group/issue_agent.rs:72-199`）。可见 Context 发生变化则走 fence→reset→新物理 session→continuation，不改变 assignment 的 profile 归属。

### 与 `gh issue` 指派语义的对照

本机 `gh` help 的当前语法作为对照：`gh issue create` 有 `--assignee login`；`gh issue edit` 有 `--add-assignee login` 和 `--remove-assignee login`，两个参数都可接受逗号分隔的多个 login。当前 Braid 的差异如下：

| 行为 | 当前 Braid | `gh issue` 对照 | 结论 |
| --- | --- | --- | --- |
| create | 单个 `--assignee PROFILE_ID`，省略用 default | 单个 flag，可传多个 login | 名称相似，身份层不兼容，Braid 实际是内部 profile 选择 |
| edit | 单个 `--assignee PROFILE_ID`，语义是替换；无移除 | `--add-assignee`/`--remove-assignee`，可维护集合 | 不对齐 |
| 多 assignee | 无；每个 work-item 只有一个 `desired_profile_id` 和一个 active assignment | GitHub 是 assignee 集合 | 当前没有多 Agent 并行承接同一 Issue 的语义 |
| unassign | local CLI 无操作；数据库字段可为 NULL，但没有清空命令 | `--remove-assignee` | 远端式 `unassign` 只在旧 GitHub ingress 路径存在，不是本地 CLI 合同 |

## Product contract

- 运行时 Agent 只认识 GitHub 式的公开协作者 login/display name。Issue/PR 的公开 assignee 是一个可空、最多一个的值；它代表该 work-item 当前唯一执行 owner。内部 `profile_id`、revision、digest、model、provider、bindings、native home、assignment generation 和 session ID 均属于 Harness/Braid 内部。
- 本轮只承诺 `issue/pr create --assignee LOGIN` 和 `issue/pr edit ID --assignee LOGIN` 的替换语义。暂不添加 `--add-assignee`/`--remove-assignee`：在没有多 assignment 或显式 unassigned desired state 之前，照搬 GitHub flag 会制造错误的集合语义。若需要停止 Agent，应另行定义单值 `--remove-assignee LOGIN` 与恢复/再激活合同，而不是把它伪装成已有能力。
- `issue/pr view/list --json` 和注入 Context 应输出 `assignees`（最多一个公开 login）；不得输出 `desired_profile`、`assignment_revision` 或 profile ID。`context` 不再打印 `Profile:` 行。宿主调试仍可保留 profile 查询，但在 `BRAID_AGENT_RUNTIME=1` 下应拒绝或返回公开 assignee 目录，避免 Agent 通过 `profile list/view` 反查内部配置。
- 每个公开 assignee 需要一条短 description，内容只说明可观察的能力、工具/输入边界和重要限制，不写供应商宣传、内部 profile 名或会话机制。Agent需要知道“可指派谁以及适合什么问题”，但不需要知道其模型和装配细节。
- 重新指派的安全时序保持当前已实现的不变量：写入 desired assignee 后旧 writer 立即 fenced；旧 native session teardown 有收据并 retire 后，才建立新 generation；旧 worktree、评论、未提交文件和 evidence 保留；任何停止未知都返回 blocked/incomplete。Context reset 和普通恢复继续按当前 profile/session 合同执行。
- 是否让“重新指派”立即产生目标 Agent 的第一轮需要单独冻结。当前实现是新 idle session、等待后续 Wake；若产品文案承诺“指派即交接”，则应把本地 reassign 的 Assign batch 保留到新 session 后再 claim 一次 Wake，并增加对应时序验收。不能把当前 idle 物化描述成已完成工作。

## Minimal LLD options with tradeoffs

### Option A — 单值公开 assignee 投影（推荐）

在现有 profile/assignment 结构上加最薄的公开投影：`Profile` 增加 `description`；`ProfileRecord`/migration 持久化公开 `assignee_login` 和 `assignee_description`；内部仍以 `profile_id` 做映射。Factory 用 `display_name` 或新增明确的公开 login 生成材料，校验 login 唯一。

`LocalObjects` 从当前 `desired_profile_id` 查出公开 login，给 Issue/PR canonical snapshot 填 `assignees`；Context renderer 在同一处附加一个短的可用 assignee 目录及 description，CLI 的 `issue/pr view` 复用同一投影。CLI 将 `--assignee` 的输入解释为公开 login，事务开始前完成 login→profile 映射；未知 login 在对象/event 写入前失败。运行时隐藏/拒绝 `profile list/view`，并从普通 item/context/status 输出删除 profile 字段。

优点是复用现有单一 desired owner、assignment revision、worker claim、teardown 和 resume，数据库只增加公开映射字段；Agent可以在 Context 中看到当前 owner和可指派目录。代价是需要一次 schema migration，并要给 Context 增加目录字节预算；reassign 当前仍是 idle session/no-turn，是否保留第一 Wake 需要另一个小决策。

### Option B — 完整 GitHub assignee 集合

增加公开 assignee catalog、work-item assignee 集合和 `--add-assignee`/`--remove-assignee`；每个 login 可对应独立 assignment generation，调度、停止、worktree、Context 和完成条件都要定义一个 Issue 多 Agent 并行时的 owner/写入冲突规则。

这才与 `gh` flag 形状完整对齐，但它把“协作中的另一个 Agent”扩大成“同一 Issue 的多执行 owner”，会引入多个 writer、竞争 turn、完成归属和 unassign 恢复语义。本轮需求没有多 owner 证据，成本远大于投影收益，不应作为最小改动。

### Option C — 独立 assignee projection 表/API

保留 `profiles` 纯内部，只新增 `assignees` 表（公开 login、description、profile 映射、revision），Context/CLI 只读该表。

边界最干净，今后可把公开协作者映射到非 profile 的远端成员；但当前每个 profile 正好一个执行 owner，新增表和同步生命周期没有独立产品需求。除非将来需要多个公开 login 映射同一 profile 或远端 GitHub 身份，否则比 Option A 多一层无必要状态。

## Recommended option

采用 Option A，保留“一个 work-item 一个 active assignee”作为明确合同。最小实施切片应按这个顺序落地：

1. Factory 配置为每个已选 profile 提供唯一公开 login 和短 description；Braid `Profile` 接收并校验它们，`ProfileRecord`/migration 保存 projection，恢复时把 projection 纳入 request identity。
2. canonical Issue/PR、CLI item JSON 和 Context renderer 共用同一个 login 映射；移除 runtime 可见的 profile ID、digest、assignment revision 和 `Profile:` 文本。宿主诊断可继续查内部 profile，但 agent runtime marker 下不提供内部 profile 查询。
3. `--assignee` 改为公开 login 的替换操作；创建/编辑/未知 login 的失败都在写入 event 前发生；同一 login 保持幂等。运行时系统指引明确给出 `issue create/edit --assignee LOGIN`，并让 `issue view/context` 提供可用 assignee 及 description。
4. 先保持当前 assignment 的 fence→teardown→retire→new generation/resume 合同。单独用一个最小 probe 决定 reassign 是否保留一次目标 Wake；在该 probe 通过前，验收只声称“新 session 物化”，不声称“指派自动开始新 turn”。

## Verification cases

1. **输入边界**：两个 profile 有不同内部 ID、公开 login 和 description；重复 login、空 login、过长或含换行 description 在启动前拒绝。
2. **无内部泄漏**：对 Issue/PR 的 `list`、`view`、`context`、初始 system instructions、wake/continuation 输入做字符串扫描；不得出现 `profile`、`desired_profile`、内部 ID、revision、digest、model/provider 或 `Profile:`。仍可出现普通 GitHub 式 `Assignees: @login` 和能力 description。
3. **目录可指派**：运行时只凭初始 Context/`view` 读到两个公开 login 及短 description，能执行 `issue create --assignee other-login` 或 `issue edit ID --assignee other-login`；不需调用 `profile list/view`。
4. **当前 assignee 投影**：默认根 Issue、新建 Issue、显式 reassign 后，canonical snapshot、文本 Context 和 JSON 都只显示对应公开 login；没有 profile 时按明确合同显示空集合，而不是伪造 `@braid`。
5. **原子未知值**：未知 login 的 create/edit 返回错误；work item、desired state、revision、event、assignment 和 wake batch 计数均不变。
6. **单值语义**：同值 `--assignee` 无操作；第二个 `--assignee` 是替换；`--add-assignee`/`--remove-assignee` 在本轮若不实现，应明确报 unsupported，不能悄悄追加或清空。
7. **重指派 fence**：旧 Agent 的 writer turn 在 reassign transaction 后被拒绝；旧 session teardown 完成前没有新 generation/新 writer；停止失败保留 stopping/blocked 和原 worktree。
8. **重指派交接**：停止收据后新 profile 获得同一 Issue Context 和保留 worktree；旧 assignment/session 进入 retired；连续 A→B→C 最终只让 C 成为 desired owner，旧事件不能覆盖最新 desired revision。
9. **turn 语义**：分别验证当前合同（reassign 只物化 idle session，后续 wake 才 turn）和若选择的 handoff 合同（reassign 保留一次 Wake，目标只产生一个第一 turn）；禁止依赖偶然轮询或旧 session 继续写入。
10. **恢复**：运行在 reassign stopping、new generation materializing、Context reset 和 provider session lost 四个位置重启；兼容 session 可 resume，缺收据/工作树/身份不匹配保持 unknown/blocked，不创建竞争 writer。
11. **能力说明**：description 出现在公开 assignee 目录且足够帮助选择；不会出现模型品牌、内部 role/profile/preset、native sub-agent 或 session 生命周期。
12. **PR 对称性**：PR 的 `--assignee`、view/context 和恢复至少满足同一单值映射；如果产品只允许 Issue 指派，应显式排除 PR，而不是保留当前 PR 空 `assignees` 的隐式行为。

## Unknowns

- 公开 login 是否必须与未来 GitHub login 相同、是否大小写不敏感、是否允许 `@` 前缀，尚未由产品合同冻结。
- description 的最大字节数、是否进入每次 Context、以及目录是否应只在 Issue 而非 PR 注入，需用 Context hard limit 的真实预算决定。
- reassign 是否应该立即启动目标第一 turn是当前最大行为未知；现有 store 注释和实现选择 idle session/no-turn，但“把 Issue 指派给另一 Agent”的产品措辞可能要求 handoff wake。
- 本地 `--remove-assignee` 是否需要表达“停止且保持可重开”的 desired-null 状态尚未定义；现有 native unassign debounce/retire 路径不能直接当作本地 CLI 完整合同。
- PR 是否与 Issue 共用 assignee 产品面、以及同一 profile 能否同时支持多个独立 work-item，需要真实协作旅程证明；当前 worker 结构支持并行 work-item，但不支持同一 work-item 多 assignee。
- `profile list/view` 是否完全 host-only，还是保留一个只返回公开 login/description 的别名，需要明确调试与运行时边界；不能继续让 runtime 用内部 profile ID 指派。
- 本地 synthetic assignee 与远端 GitHub Agent App/Bot actor 的身份是否共享字段尚未统一；当前 `@braid` 是硬编码本地占位，不能作为最终公开身份设计。
