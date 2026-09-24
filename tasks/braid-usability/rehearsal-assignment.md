# 指派路径独立预演（只读）

范围：`sources/braid` 的本地 Issue/PR 指派与结束路径，以及四个 `variants/pi-team-{glm,mixed,vv,deepseek}/run.py` 的请求接线。未修改源码，未运行测试、实验或模型。

## 当前路径与必须切断的隐式选择

| 路径 | 当前事实 | 目标与最小落点 |
| --- | --- | --- |
| 请求与根初始化 | 四个 variant 用 `DEFAULTS.issue/pr`；`local.rs::Request/config` 强制两个默认 Profile；`execute` 先 `objects.initialize`，再 `set_profile_defaults` 将根 Issue 指派并把两个默认值写入 `local_run`。`Config.profile_selection` 无运行消费者。 | 请求只给 `root_profile_id`（Profile ID，不是 login）；校验它在成员目录中；`initialize` 同一事务把根 Issue 的 `desired_profile_id` 设为该 ID，再发根 `Assign`。删除 `set_profile_defaults` 调用、`ProfileDefaults/ProfileSelection` 和四个 `DEFAULTS`，保留现有 metadata 用根 Profile 取模型。历史 SQLite 的 `default_*` 列可留作旧 schema，不再读取。定位：`variants/*/run.py:20,102,125`，`src/local.rs:23-31,183-211,300-324`，`src/objects.rs:109-145`，`src/config.rs:20-24,56-59,119-123`。 |
| 后续创建与 edit | `objects.rs::create_item` 在未给 assignee 时从 `local_run.default_issue_profile/default_pr_profile` 补值；`create_issue_with_parent_and_profile`、`create_pr_with_profile` 无条件发 `Assign(activate)`，Issue 另发 Wake。现有 `replace_assignee_in` 和 edit `--add-assignee` 已能明确指派及改派。 | `create_item` 只保存显式 login 解析出的 Profile，缺省为 NULL；Issue/PR 创建仅在显式指派时发 `Assign`。Issue 的需求 Wake 及 PR 关联通知可以保留，等待将来指派；不新增分派机制。普通 view/list 的空 assignee 当前省略文字，按设计在 CLI/context 显示“未指派”。定位：`src/objects.rs:254-284,398-432,930-1005,219-251,459-562`，`src/cli/mod.rs:388-409`，`src/context.rs:518-523`。 |
| 事件选择与 materialize | `store.rs::assignment_candidates` 对所有 profile 返回同一 pending assign/unassign/mention；Issue 执行者对非 mention 先用 canonical assignees 判断，PR 则直接到 `begin_agent_assignment`。后者在 `desired_profile_id IS NULL` 时把当前抢到事件的 profile 写进去，形成第二层自动认领；其不匹配的显式指派则原样等待正确 profile。 | 候选带上“本地对象未指派”标志，两个 group driver 对这类旧的 assign/mention 事件直接消费为 no-op；`begin_agent_assignment` 再以事务守卫要求 `desired_profile_id == profile.profile_id`，NULL 只消费该旧激活事件，不更新 assignee、不物化。显式指派的事件仍由匹配 profile 消费，其他 profile 不抢。这样兼顾新建时不发 assign 与旧状态残留 pending assign 不永久卡住 `status.pending_events`。定位：`src/store/mod.rs:3300-3325,3790-3951`，`src/group/issue_agent.rs:278-337`，`src/group/pr_agent.rs:234-273`。 |
| 执行 claim/resume | `claim_runnable_turn` 的 `(l.node_id IS NULL OR l.desired_profile_id IS NULL OR l.desired_profile_id=?2)` 允许本地 NULL 配已有 session；`provider_resume_candidates` 只看 active/finalizing 与旧 profile，未复核当前明确指派。 | 本地 claim 改为必须匹配 `desired_profile_id=ai.profile_id`（保留已有 assignment_revision 匹配）；resume 同样以当前 `desired_profile_id`、`assignment_revision` 限制旧执行实例。`objects::prepare_dispatch` 也只应准备当前指派的 session。正常显式指派不变，NULL 不能因旧 session 或批次继续运行。定位：`src/store/mod.rs:3115-3156,4827-4860`，`src/objects.rs:1414-1421`。 |
| unassign、close、reopen | `edit` 取消/替换只停止 materializing/active/finalizing，遗漏已关闭后的 sleeping 组；`retire_unassigned_work_item` 也只找前三类。`begin_work_item_reactivation` 按最新 sleeping generation 复活，未比对当前 `desired_profile_id/assignment_revision`。因此关闭后取消或改派，再 reopen，可能复活旧成员；关闭状态新增 assignee 的 assign 事件会被消费，reopen 也没有对应新激活。 | 取消/改派时将 sleeping 组纳入现有 stopping→原生 teardown→retired 路径，保留 worktree 供后续接手；`begin_work_item_reactivation` 仅恢复与当前明确指派及 assignment_revision 相同的 sleeping 组。reopen 时若有明确指派但没有可恢复的当前组，再发一次明确 `Assign`，走现有物化链；NULL 时 reopen 只消费 lifecycle，不复活旧组。定位：`src/objects.rs:219-251,539-563,1115-1170`，`src/store/mod.rs:3468-3595,3957-4100,3220-3290`，`src/group/worker.rs:79-101`。 |
| 终态 | `local::status.pending_batches` 只计有 active/materializing/finalizing assignment 的批次；`pending_events` 计 pending assign/lifecycle/invalidate。`drive` 非 quiescent 会继续等；静止时只有根 completed、无 OPEN 工作项等条件才 sealed，否则 `incomplete`。`seal_delivery` 再拒绝 OPEN 或 pending 控制事件。 | 未指派对象的普通 Wake 可暂存而不让运行循环；旧 NULL assign 必须按上行消费，closed/reopened lifecycle 由现有 no-group 分支消费。OPEN 未指派子项会导致明确 `incomplete`，不会被默认为完成；已关闭未指派对象不阻止合法收尾。无需改完成规则。定位：`src/local.rs:249-260,442-492`，`src/objects.rs:1120-1148,1354-1390`，`src/store/mod.rs:3365-3445,3490-3579`。 |

## 建议实施顺序

1. 四个 variant 改成单一 `ROOT_PROFILE_ID`；`local.rs::Request`、`config.rs` 改为只验证根 Profile。根初始化与请求持久化在 `local.rs`/`objects.rs` 一起改，保持新 run 的根 Issue 原子明确指派；删除后续创建读取旧默认列的分支。旧库中的已记录 `desired_profile_id` 保持原值，不尝试从现有值猜测它当初是显式还是默认产生。
2. Issue/PR 创建只在显式 assignee 存在时发 activate；补上 CLI/context 对空指派的文字呈现。确认 edit 增加 assignee 仍复用原 `replace_assignee_in`，无须新命令。
3. 在 store 的候选/事务入口清掉旧 NULL 激活并禁止 NULL 认领；随后收紧 claim、resume、prepare_dispatch，确保没有绕过当前指派的执行入口。此顺序先去掉新事件来源，再处理旧事件，避免 pending 循环。
4. 统一关闭状态下的取消/改派与 sleeping 组清退；在 reopen 事务中校验当前指派与 generation revision，并为“明确指派但无匹配 sleeping 组”补发 assign。沿现有 `stopping_provider_sessions` 和 teardown 路径，不直接删除工作树或复活旧默认。
5. 最后按已批准验收计划检查：新建 NULL Issue/PR 不产生执行、后来 edit 指派可启动、同成员跨工作项隔离、关闭后取消/改派再重开、旧 NULL pending 激活收敛、OPEN 未指派项返回 incomplete，以及已有明确指派的恢复行为。此次预演没有运行这些检查。

## 边界与风险

`migrations/0006_profiles_assignment.sql` 的旧默认列可保留，不必破坏旧库 schema；但新 `Request` 去掉 `defaults` 后，旧格式 `request.json` 的继续运行兼容性需明确。建议新运行严格使用新字段，已有 sealed run 保持只读；若要求旧未结束 run 用新二进制恢复，需要单独设计只读请求转换，绝不能从旧 `default_pr_profile` 给尚未指派的新对象补人。这是请求兼容范围，不是 assignment 数据迁移。

现有 NULL 与非 NULL `desired_profile_id` 没有“由人明确指派还是旧默认生成”的来源字段，历史非 NULL 值不能可靠追溯；本轮只能保证不再读取旧默认、不覆盖已有值，并使之后的 NULL 保持未指派。
