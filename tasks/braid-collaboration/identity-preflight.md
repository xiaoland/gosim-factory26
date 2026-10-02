# Braid 身份 LLD 与执行预演

2026-09-25，只读调查。本文只覆盖 Braid 具体成员身份、指派生命周期、Agent 可见投影和 Factory archive 接线；SVC 通用反馈改稿、共同仓库实现和新实验不在本页调查范围。未修改 Braid 源码，未运行测试、模拟器、探针或模型实验。

## 结论先行

当前真正的匹配键是 `local_items.desired_profile_id`，不是公开 assignee。应保留这个内部键，让现有每个 `kind × profile` 的 worker、`assignment_revision` 和 `profile_revision` 继续工作；新增一条与 Profile 分离的、在 assign 事务中预留的公开成员身份：

```text
Profile（配置）       profile_id=pi-glm-fast, base_login=glm
当前工作项投影        desired_profile_id=pi-glm-fast, desired_member_login=glm-2
逻辑 Agent            assignments.member_login=glm-2
物理执行              agent_instances.agent_id=<内部 ID>
Provider 会话         provider_sessions.provider_session_id=<provider ID>
```

`desired_member_login` 必须在 `issue/pr create --assignee`、`issue/pr edit --add-assignee`、根 Issue 初始化的同一 SQLite immediate transaction 中生成、落库并随 assign 结果返回。名字来自 `local_run` 的单调递增运行序号，按 `alias-N` 生成；不能扫描现有 assignment/desired 值取最小空号，因为 worker 启动前撤销的预留也不能被复用。这样 assign 已成功而 worker 尚未物化时，`view/list/context/status` 已能显示 `@glm-2`，而 worker 仍用 `desired_profile_id` 匹配 `pi-glm-fast`。

`assign` 仍是唯一的成员生命周期动作；不加入 create-member、member pool、调度池或全局安全机制。现有 create 的 `--assignee` 和 edit 的 `--add-assignee/--remove-assignee` 是进入这个共享 assign/unassign 事务的语法，不是新的成员管理对象。

## 已核实事实

### 现有状态链和调用点

| 位置 | 事实 | 身份含义 |
| --- | --- | --- |
| `migrations/0001_initial.sql:29-73` | `profiles` 是 `(profile_id, revision)`；`assignments` 按工作项 generation；`agent_instances.agent_id` 属于 assignment；`provider_sessions` 属于 agent instance。 | Profile、逻辑 assignment、Agent instance、物理 session 已有分层，但没有公开成员字段。 |
| `migrations/0006_profiles_assignment.sql:1-4` | `local_items.desired_profile_id`、`local_items.assignment_revision` 和 `assignments.assignment_revision` 已存在。 | 当前工作项选择 Profile，并以 revision fence 旧执行。 |
| `migrations/0007_assignee_projection.sql:1-2` | Profile 只有静态 `assignee_login`/description 投影。 | 同一 Profile 的所有工作项现在会显示同一 login。 |
| `src/objects.rs:114-141` | `initialize` 先建立根 Issue，再直接写 `desired_profile_id` 和 Assign 事件；调用时 Profile 记录尚未由 `GroupSpec` 注册。 | 根 Issue 是 assign 预留必须覆盖的异步前间隙。 |
| `src/objects.rs:154-182` | `item`/`assignee_directory` 从当前 Profile 的静态 login 派生公开 assignee。 | 这里只改投影会破坏 worker 的 Profile 匹配。 |
| `src/objects.rs:192-250` | `set_assignee`/`replace_assignee_in` 修改 Profile、递增 assignment revision、停止旧组并发 Assign；同 Profile 当前是 no-op。 | 这是所有改派入口应共用的事务边界。 |
| `src/objects.rs:252-275,391-427,964-1045` | Issue/PR create 可接受 `--assignee`，将 Profile 解析和对象/Assign 事件写在同一事务。 | 创建时即可预留公开成员名。 |
| `src/objects.rs:453-559` | edit 先校验 add/remove，再原子改对象、改派或清除 Profile；add 当前只能从 unassigned 开始，remove 必须命中静态 login。 | 需要把校验改为“配置输入 + 当前具体成员输出”的语义。 |
| `src/objects.rs:575-650,788-845` | 评论作者存 `writer_group`；reaction 的 actor 目前直接存 writer group；读取时作者和 reaction 都直接把该值作为 login。 | 这是 Agent-facing UUID 的确定泄漏点。 |
| `src/store/mod.rs:3339-3370` | `assignment_candidates` 按 pending Assign/Unassign/Mention 返回事件，不带目标 Profile/公开成员。 | 改派后各 Profile worker 只能靠后续检查猜测归属。 |
| `src/store/mod.rs:3840-4002` | `begin_agent_assignment` 以 `desired_profile_id`、`assignment_revision`、停止状态作原子检查，然后才创建 UUID assignment/agent。 | 这是逻辑身份复制到物化 assignment 的唯一正确落点。 |
| `src/store/mod.rs:4004-4169` | Unassign 先 debounce、fence turn/provider、等待 teardown，再 retire assignment/worktree/wake。 | remove 不能立刻删除公开历史或抢建新 assignment。 |
| `src/store/mod.rs:3520-3738,4370-4835` | reopen/context reset 保留 assignment/agent，替换 provider session；`agent_id` 不因 provider 重启或 Context rebuild 改变。 | 公开成员应挂 assignment，而不是 provider session。 |
| `src/store/mod.rs:3147-3190,4903-5010` | resume/turn claim 主要按 Profile 和 provider session 工作。 | 增加可读名字字段即可，不改变调度模型。 |
| `src/group/worker.rs:41-80,124-166` | 每个 `kind × profile` 一个 `GroupDriver`，`group_id` 为 `kind:profile`。 | 这是调度 worker，不是具体 Braid Agent 名，不能替换成公开成员。 |
| `src/group/issue_agent.rs:231-281` | Issue unassign 重新物化 canonical assignees 并与 `profile.assignee_login` 比较。 | 具体成员投影后该比较必错；应改为事件/assignment 的内部 Profile 目标。 |
| `src/group/issue_agent.rs:312-349` | Issue assign 再把 canonical assignee login 与静态 Profile login 比较，随后 `begin_agent_assignment` 才做 durable check。 | 删除公开 login 匹配，保留 `begin_agent_assignment` 的 Profile/revision 原子匹配。 |
| `src/group/pr_agent.rs:233-317` | PR assign 同样由 profile worker 取事件，再由 store 原子创建 assignment。 | PR 路径可复用相同成员预留和复制。 |
| `src/group/provider.rs:60-93` | 指引把静态 `@profile.assignee_login` 列成“可指派成员”，并没有当前 Agent 的具体身份。 | 必须拆分配置目录和当前成员身份。 |
| `src/context.rs:425-500` | Context 把 `Actor.login` 用于作者、assignee、reaction 和通知文本。 | 只要对象层提供公开 login，渲染层无需 UUID 脱敏。 |
| `src/cli/mod.rs:320-465,535-745` | runtime 已隐藏 Profile 命令；Item/JSON/Context/评论是 Agent 可见边界；create 只返回 id，edit 打印 Item。 | assign 结果应在现有输出中明确返回具体成员名。 |
| `src/local.rs:89-125,206-240` | sessions manifest 现在记录 raw `group_id`、Profile、generation 和 provider 资料；status 的 Agent runtime 分支只输出 items。 | archive 可以保留 raw 证据，同时增加可读成员字段。 |
| `src/worktree.rs:24-92,135-161` | 当前代码仍是 worktree 接线；本轮目标运行改用 `origin.git` + 工作项独立 clone，clone 当前没有成员 Git author 配置。 | 改派复用工作项 clone 时必须更新其 local identity。 |

### Agent-facing UUID 泄漏面

需要处理的不是所有字符串，而是 Braid 交给 Agent 的身份边界：

1. `objects.rs:825-843` 将 `writer_group` 和 reaction actor 原值放进 `CommentSnapshot`；Context、CLI JSON 和 `comment view` 随后暴露它们。
2. `context.rs:425-490` 会把上述 `Actor.login`/reaction actor 写入模型文本。
3. `group/provider.rs:60-70` 目前把 Profile 的静态 login 当作 `@成员`，既不区分配置与成员，也无法表达当前身份。
4. `objects.rs:241-247` 的 Assign reference 目前写静态 login；它会进入 wake batch、通知和 provider event references。
5. `src/cli/mod.rs:603-617` 的 Context 目录当前显示 `@` 加静态 login；create/edit 的结果没有明确给出具体派生名。

内部 `events.writer_group`、`local_comments.writer_group/writer_turn`、`agent_instances.agent_id`、`provider_sessions.*`、provider raw logs、Factory archive 和宿主诊断可以继续保留真实 ID。它们不能通过 Braid 的 Context、文本/JSON、评论作者/reaction、通知、CLI Agent 错误或指引边界泄漏。

## 建议 LLD

### 1. 数据字段与约束

下一次源码授权时增加一条最小迁移，字段名可按项目命名习惯调整，但语义应固定：

```sql
ALTER TABLE local_run ADD COLUMN next_member_sequence INTEGER NOT NULL DEFAULT 0;
ALTER TABLE local_items ADD COLUMN desired_member_login TEXT;
ALTER TABLE assignments ADD COLUMN member_login TEXT;
CREATE UNIQUE INDEX assignments_member_login
  ON assignments(member_login) WHERE member_login IS NOT NULL;
```

`desired_member_login` 是当前工作项的公开 owner projection；`assignments.member_login` 是该 assignment generation 的逻辑 Agent 身份。新 assignment 必须非空；旧 assignment 允许暂时 NULL 以保持 forward-only migration 和历史 raw 数据不变。不要把成员名挂在 `agent_instances` 或 `provider_sessions`：前者会让 assignment 重建丢身份，后者会让 provider restart/context reset 变成新的人。

`Item.assignees` 只从 `desired_member_login` 生成 `Actor { node_id: "member:<login>", login }`；`desired_profile_id` 继续保留在内部结构并参与所有 worker/store 查询，不能改成按 login 匹配。

### 2. 名字预留算法

Profile 的 `assignee_login` 是配置 alias，不是 Agent 名。`local_run` 增加一个递增成员序号；在 `BEGIN IMMEDIATE` 中先递增并持久化该序号，再生成 `alias-N`。序号属于整个 run，不按配置分别计数；已撤销或已退休的预留也消耗序号，不能复用。分配器不扫描现有 `desired_member_login` 或 `assignments`，也不引入全局池或调度器。

事务内的共享 helper（建议在 `src/objects.rs` 附近，Store 不复制一套分配器）应有以下行为。公开输入只接受现有配置 alias（例如 `glm`）；内部 Profile id 不成为 CLI 或 Agent-facing 输入。

| 情形 | durable 写入 | 返回 |
| --- | --- | --- |
| 未指派 → 配置 `glm` | 写 `desired_profile_id=...`、`desired_member_login=glm-N`、`assignment_revision+1`、Assign 事件 | `已指派 @glm-N（配置 glm）`，不表示已启动 |
| 当前就是同一配置 | 不写对象、revision、event、wake 或序号 | 原 `@glm-N`，幂等成功 |
| 当前是别的配置，只有 add | 拒绝，零写入 | 当前具体成员和配置名的可读错误 |
| `remove` | 要求输入精确匹配当前具体 login；清空两个 desired 字段，revision+1，旧 assignment 进入 stopping，发 Unassign | `已移除 @glm-N`，等待 debounce/teardown |
| `remove old + add deepseek` | 一个 immediate transaction 校验两边后写一次新 revision、旧 assignment stopping、新 `deepseek-M` 预留和 Assign/替换事件 | `已改派为 @deepseek-M（配置 deepseek）` |
| remove 后再次 add 同配置 | 旧名字不复用，产生新序号 | 新的具体成员名 |
| assign 事件重复投递 | 由 `event_id`/现有事件生命周期幂等消费，不能生成第二个 assignment | 已预留的同一名字 |

输入值是现有配置 alias；输出和 remove 输入是具体成员 login。不要让 Agent 用 `@glm-2` 反推出配置再重复 assign；当前成员名不是配置目录。

根 Issue 必须走同一 helper。最小接线是把当前 `local.rs:293-301` 的顺序改为：先按本次运行配置注册/ upsert 根请求所需的 `ProfileRecord`，再调用 `objects.initialize`；initialize 在创建根 Issue 的同一事务中调用该 helper，原子写入 `desired_profile_id`、`desired_member_login`、序号和 Assign 事件。不能先只写 `desired_profile_id` 再异步补名字，否则根 Issue 会有可见 UUID/静态 login 窗口。

create 的事务仍然同时建立对象、公开名字和 Assign 事件；CLI 结果需在已有 id 结果旁带 `assignee`/`profile`（无 assignee 时维持未指派）。edit 的文本已有 assignee 行，JSON 结果应能直接取得 concrete `assignees`。不等待 Context、worktree、provider 或模型启动。

### 3. 异步物化与 worker 匹配

最短状态流如下：

```text
assign transaction
  ├─ local_items(desired_profile_id, desired_member_login, assignment_revision)
  └─ events(assign, reference=@member)
        ↓ pending candidate（带 target_profile_id/member_login）
profile worker 只领取自己的 target_profile_id
        ↓ begin_agent_assignment 原子检查 desired_profile_id + revision
assignments(member_login=desired_member_login, generation)
        ↓
agent_instances(agent_id=UUID) → provider_sessions(provider ID)
```

`AssignmentCandidate` 应增加 `target_profile_id`（或等价内部字段）和公开 `member_login`。`assignment_candidates` 应接受当前 worker 的 profile id，查询 assign 时使用 `local_items.desired_profile_id`，查询 unassign 时使用仍处于 stopping/active 的最新 assignment 的 agent instance Profile。这样错误 Profile worker不会消费别人的 event，也不需要用公开 login 反查配置。

`AgentMaterialization` 增加 `member_login`，由 `begin_agent_assignment` 从 `desired_member_login` 复制；`ProviderResumeCandidate`、`ContextResetClaim`、必要时 `TurnClaim` 同样带这个只读可读字段。所有 Profile/revision/assignment_revision 查询保持原样。

必须删除或改写以下公开 login 匹配：

- `src/group/issue_agent.rs:331-334`：不再将 canonical assignee 与 `profile.assignee_login` 比较；`begin_agent_assignment` 的 `desired_profile_id` 原子检查是权威。
- `src/group/issue_agent.rs:246-251`：unassign 不再以静态 login 判断是否仍指派；由 candidate 的 target Profile 和 durable assignment 状态决定。若未来保留 canonical 复核，也只能比较当前公开 `member_login`，不能比较配置 alias。
- 所有 `provider_resume_candidates`/`claim_runnable_turn` 的 Profile 条件继续使用 `profile_id`，不能改成 member login。

Provider restart、Context reset、reopen 的 assignment generation 不变时复用原 `member_login`。真正改派先 fence/teardown 旧 assignment，再创建新 generation 和新 member login；worktree 可复用，逻辑人不能复用。

原生 explorer、executor、browser operator 等继续是所属 Braid Agent 的 provider 内部子代理；它们不写 Braid `assignments`、不获得新成员名、不出现在成员目录，也不改变 `agent_instances → provider_sessions` 链路。

### 4. Agent-facing 身份边界

| 表面 | 目标行为 | 内部保留 |
| --- | --- | --- |
| Issue/PR assignee、list/view/status JSON | `@glm-2` 等 concrete login | `desired_profile_id`、assignment/agent UUID 只留内部 |
| 评论作者 | 用 `assignments.member_login` 解析 writer group | `writer_group`、writer_turn 原值保留 |
| 评论 reaction | 新写入仍保留既有 raw actor key 做幂等；展示经 writer group → assignment 映射得到 `member_login` | raw actor、旧事件和 archive 不改写；不新增 reaction display 字段 |
| Context 文本/JSON | Actor 的 `node_id` 只能是 `member:<login>` 等可读稳定键 | raw UUID 不穿过 Context struct |
| Assign/Unassign/wake 通知 | 使用 concrete member 和 Issue/PR 编号；配置可另以“配置 glm”出现 | event writer/assignment UUID 留 DB/host |
| provider 指引 | `你是 @glm-2，当前处理 Issue #2`；目录显示 `配置 glm：...`，不能写 `@glm` 代表配置 | Profile id、digest、provider/session diagnostics 仍 host-only |
| Agent CLI 错误 | 只说成员名、配置名、Issue/PR 编号和可执行动作；不把 assignment/agent/provider/session UUID 拼进错误 | Store/raw error 可在宿主日志保留 |
| sessions manifest | 增加 `member_login`，并保留 `profile_id`、generation、provider、raw `group_id`/session paths 供 Factory archive | archive 是 host-facing，不是 Agent Context |

`src/objects.rs:819-844` 建议集中做 display resolver：writer group → `agent_instances` → `assignments.member_login`。`CommentSnapshot.author.node_id` 使用 member login；reaction 展示也走同一 resolver，不新增 reaction display 字段。旧 raw assignment 没有 `member_login` 时不能把 UUID fallback 给 Agent；旧运行的内部 UUID 映射继续保留。

`src/group/provider.rs:60-93` 建议把 `local_instructions` 增加当前 `member_login` 参数，且所有入口传入同一个字段：初次 materialize、resume、reopen、context reset。静态目录改为“配置目录”，当前身份单独写入指引。`src/cli/mod.rs:603-617` 同样把配置与当前成员分两段；不把配置 alias 加 `@`。

### 5. sessions manifest 与 Git 身份

`src/local.rs:89-110` 的 `RecordingFactory::start` 已能按 worktree 查 assignment。查询结果增加 `assignment_id`（raw archive）、`member_login`（可读）和现有 `group_id`；`local.rs:226-234` 回填现有物理 session 时同样 join assignment。建议 manifest 记录：

```json
{
  "member_login": "glm-2",
  "profile_id": "pi-glm-fast",
  "assignment_generation": 1,
  "group_id": "<raw internal id>",
  "provider_session_id": "<raw provider id>"
}
```

这里不删除 raw 字段：Factory archive 需要完整身份映射和恢复证据；只是不把 manifest 内容拼入 Agent Context。上下文/通知使用 `member_login`。

本轮采用 `origin.git` 加每个工作项独立 clone。具体成员的 Git author 在该 clone 的普通 local config 中设置，例如 `user.name=@glm-2`、`user.email=glm-2@braid.local`；不修改 origin、其它 clone 或全局 Git config。共同仓库的其它实现不在本页调查范围。应在以下两个时机写入：

1. 新 assignment 首次 provision clone 后；
2. 改派复用既有工作项 clone、provider 启动前。

这样 clone 属于工作项，改派后的新提交使用新成员身份，既有 commit 的作者不变，origin 和其它工作项不串扰。merge commit 仍由 Braid 的既有签名策略决定。

## 历史、兼容与未知

### 保持不变的部分

- 不改历史 comment/body、event reference、provider raw log、Git commit 或 Factory archive 文件；本轮只为新运行生成公开成员名，不迁移旧运行的作者展示或回填历史 alias。
- 不重用 retired assignment 的 concrete member name。
- 不把 provider session 重启、上下文替换、reopen 的同一 assignment 误判为新成员。
- 不增加调度池、全局成员表、全局锁或 Braid 原生子代理管理。

本轮没有仍影响主方案的实质产品不确定性：名字格式固定为 `alias-N`，序号由 `local_run` 单调递增；public 输入固定为现有配置 alias；旧运行不做作者展示迁移或历史 alias backfill；Git 使用工作项独立 clone 的 local config（`@member` / `member@braid.local`）。旧运行的内部 UUID 映射和 Factory archive 仍保留。

## 最短线性修改顺序（未来取得源码授权后）

1. 写 forward-only migration：`local_run.next_member_sequence`、`desired_member_login`、`assignments.member_login`；只对新运行生成成员名，不为旧 assignment 建公开 alias，保留旧运行的 raw 映射。
2. 在 `objects.rs` 集中实现 Profile 输入解析、名字预留、当前 Item 投影和 assign result；接通 initialize/create/edit/remove/reassign，保持 `desired_profile_id`、assignment revision 和停止 fence。
3. 在 `store/mod.rs` 扩展 candidate/materialization/resume/reset 结构，按 target Profile 过滤 worker，复制 `member_login`；保持 `profile_id`/revision 匹配逻辑。
4. 在 `objects.rs/context.rs/cli/mod.rs` 接通 assignee、author、reaction、JSON、Context 和 CLI 输出；错误/通知只经 public identity 边界。
5. 在 `group/provider.rs` 和 issue/pr/dispatch 的所有 prompt 构造入口传入当前 member；配置目录与当前 Agent 指引分开。
6. 在 `local.rs` 增加 manifest 的 `member_login`，在工作项 clone 接线处写入普通 local Git identity；确认 reassign 复用 clone 会更新身份且不改 origin/global config。
7. 只在用户明确开工后通过真实运行观察边界行为；当前阶段不新增或运行 Factory、基础设施、Corpus 测试、探针或模拟器。

## 预演验收观察点

实现复核时按状态事实观察，而不是以事件数量代替身份正确性：

1. assign transaction 提交后、任何 worker 运行前，`issue/pr view --json` 已有唯一 concrete member，且结果明确是“已指派/已预留”，没有“已开始”。
2. 两个工作项选择同一 Profile 时得到不同 member login；同一工作项重复同一配置得到相同 login 且没有新 assignment/event。
3. 改派期间旧 provider 被 fence/teardown；新 assignment 使用新 member login，旧评论/旧提交仍署旧成员，worktree 文件继续保留。
4. provider restart/context reset/reopen 在同一 assignment 上恢复同一 member login；物理 session ID 变化不影响公开身份。
5. workers 按 Profile id/revision 接单，即使公开 assignee 已是 `glm-2`，不会出现“Profile 不匹配”或错误 worker 消费事件。
6. Context、`view/list/status --json`、comment 作者、reaction、通知、provider 指引和 CLI 错误都不含 UUID；宿主日志、raw provider evidence、sessions manifest 仍能用 raw ID 追溯。
7. 同一工作项 clone 的新 commit 使用接手成员的普通 local author；其它 clone、origin、source checkout、全局 Git config 不变。
