# Assignee Cell：实施前独立预演

状态：预演完成；没有修改 `sources/braid`、Factory、SVC 或活动配置。唯一写入本文件。

## Observed

证据基线是 `sources/braid` 当前提交 `673c119`，与 packet/plan/design/verification/assignee-projection 一致的现状如下。

- 配置入口 `sources/braid/src/local.rs:23-37,144-204,289-315` 接收 `profiles/defaults/bindings`，恢复时要求三者完全相同；`Profile` 在 `src/config.rs:176-224` 没有公开 login/description。`scripts/native_profiles.py:95-98` 把 `display_name` 直接写成内部 profile id。因而恢复材料可持久化，公开身份尚未存在。
- `GroupSpec::new_with_binding` (`src/group/worker.rs:60-66`) 生成 `ProfileRecord`；`src/group/provider.rs:19-57` 只写 profile id、revision、effective digest、provider kind、tags；`migrations/0001_initial.sql` 的 `profiles` 表也只有这五类内部字段。`0006_profiles_assignment.sql` 已有 `desired_profile_id`、`assignment_revision`，不是公开 assignee 映射。
- 对象写入的共同路径是 `LocalObjects::create_item` → `create_issue_with_parent_and_profile` / `create_pr_with_profile`，以及 `edit_with_parent_and_profile` → `set_assignee_in` (`src/braid/src/objects.rs:181-271,376-507,882-1000`)。当前 `--assignee` 的值直接按 profile id 校验；同值幂等，未知值在 INSERT/UPDATE/event 前失败。
- `Item`、CLI JSON/text 和 `context` 仍暴露 `desired_profile`、`assignment_revision` 与 `Profile:` (`src/braid/src/objects.rs:44-71,147-168`; `src/braid/src/cli/mod.rs:238-319,480-536`)。`profile list/view` 返回 id、adapter、revision、digest、tags；`BRAID_AGENT_RUNTIME=1` 目前没有隐藏入口。
- canonical Issue 固定产生 `assignees=[{node_id:"braid",login:"braid"}]`，不查 `desired_profile_id`；canonical PR 维持默认空 `assignees` (`src/braid/src/objects.rs:796-860`)。Context 只渲染 canonical 字段 (`src/braid/src/context.rs:260-319`)。因此当前 Agent 看到的 owner 不是实际 selected profile，PR 也不对称。
- 初始化 `LocalObjects::initialize` 只创建一个 `issue:1`，随后写 `Assign(activate)` 和 `Wake` (`src/braid/src/objects.rs:106-130`)；`local_run(singleton=1)` 与 `fresh` 路径保证一轮 run 只有一个根 Issue。现有 `local_issue_two_prs_merge_finalize_and_archive_every_session` 通过了根 Issue→多个 PR→合入→finalization 的完整旅程，且恢复 request identity 变化会被拒绝。
- 重指派当前路径是 immediate transaction：先 `ensure_profile`，再更新 `desired_profile_id/assignment_revision`，把旧 assignment/agent/provider session 标为 `stopping`，最后发一个 `Assign` (`src/braid/src/objects.rs:208-241`)。`begin_agent_assignment` (`src/braid/src/store/mod.rs:3775-3950`) 只接受当前 desired profile，并在 stopping 存在时返回 `None`；worker 的 `retire_reassigned_sessions` (`src/braid/src/group/worker.rs:84-109,297-366`) 取得 native teardown 后才允许新 generation。
- 当前 Assign 对普通 reassign 只物化 idle session；`preserve_wake=false` 会消费旧 wake，后续 wake 才会产生 turn (`src/braid/src/store/mod.rs:2263-2269,3849-3853`; `src/braid/src/group/issue_agent.rs:302-328`)。只有初始 `activate` 或 mention 保留 wake。故“成功新 session”目前不等于“恰一次目标第一轮”。
- 已运行 `cargo test --all-targets`：28 个 Rust 单元测试和 1 个 `tests/cli_writer_boundary.rs` 集成测试全部通过。覆盖的可用证据包括：未知 profile create/edit 不落库、旧 writer 被 fence、停止前替换 assignment 不产生新 generation、停止后代际递增且保留脏 worktree、blocked session 可接管原 worktree、CLI `--external`/旧 turn 被拒绝、根 Issue 与 PR finalization 可收敛。没有测试公开 login、description、运行时 profile 隐藏、canonical assignee 投影或 reassign 唤醒。

## 关键合同判定

单 active assignee 可复用现有 `desired_profile_id`、`assignment_revision`、worker claim、teardown、worktree reuse 和 resume；不需要另造多 owner assignment 表。公开投影应是 profile record 的字段，而不是额外 `assignees` 状态表。

`create --assignee LOGIN` 可以保持 GitHub 形状，事务内先做 LOGIN→内部 profile 映射，再创建对象及 activation/wake；未知 LOGIN 必须在任何对象、event、assignment、wake 写入前失败。

`edit --add-assignee/--remove-assignee` 与当前产品合同存在未解决冲突：`design.md` 的 HLD要求两旗标支持同命令原子替换，并在单 owner 下拒绝第二 owner/不匹配 remove；`assignee-projection.md` 的 Product contract 又明确本轮暂不添加两旗标，只承诺 `edit --assignee LOGIN`。当前实现两者都不存在，只实现单值 `--assignee PROFILE_ID`。因此不能把“源码已有 GitHub 语义”作为通过证据。

建议实施 handshake 冻结为：保留 `--assignee LOGIN` 替换语义，同时实现 `--add-assignee LOGIN` 与 `--remove-assignee LOGIN` 作为单 owner 的严格别名/组合合同：单独 add 在已有 owner 时报“已有 active assignee”，单独 remove 仅接受当前 LOGIN 并进入明确的 desired-null/retire 状态，同一 edit 中 remove 旧 + add 新必须在一个 SQLite transaction 内完成；未知、不匹配、两个 add 或两个 remove 均在写前失败。若 Human 要坚持 Product contract 的“暂不添加”，则这些旗标必须明确返回 unsupported，并把验证项降级为负例；不能静默把 add 当 replace、把 remove 当空 profile。

## 精确拟改文件与 owner

按最小 Option A，owner 只触及这些文件族：

1. Factory 配置 owner：`scripts/native_profiles.py` 生成唯一公开 `assignee_login`/短 `assignee_description`；`scripts/profiles.py` 校验字段、唯一性、字符/长度边界；必要时只更新选中 `harness/profiles/*.json` 的公开能力来源。这里不暴露 model/provider/profile 名。
2. 配置与请求 owner：`sources/braid/src/config.rs` 扩展 `Profile` 的公开字段并做登录名/description 验证；`sources/braid/src/local.rs` 把字段纳入 request identity、初始化注册和 legacy 恢复分支。`src/group/provider.rs` 生成含公开投影的 `ProfileRecord`，system prompt 增加 assignee 操作和目录但不写内部字段。
3. 持久化 owner：新增 `sources/braid/migrations/0007_assignee_projection.sql`，在 `profiles` 增加可兼容的 `assignee_login`、`assignee_description`（迁移本身不猜模型身份）；`sources/braid/src/store/mod.rs` 扩展 `ProfileRecord`、register/upsert、login 映射查询和 assignment snapshot。不要新建独立 projection 表。
4. 对象/投影 owner：`sources/braid/src/objects.rs` 统一 profile→公开 login 的查询，Issue/PR canonical 都填最多一个公开 Actor，保留一个 task 一个 root Issue；去掉 `Item` 的内部字段。`sources/braid/src/context.rs` 复用同一 canonical 投影并追加短成员目录。
5. CLI/runtime owner：`sources/braid/src/cli/mod.rs` 让 create/edit 接收公开 login；`view/list/context/status --json` 只输出 `assignees`/公开目录；runtime marker 下 profile list/view 拒绝或只返回同一公开目录；按最终合同实现 add/remove 或显式 unsupported。`src/group/issue_agent.rs` 的 `assigned_to_braid` 检查必须改为当前公开 owner/内部映射的统一判定，`src/group/dispatch.rs` 的 Issue/PR reset/resume 只消费公开 context。
6. 验证 owner：优先扩展已有 `sources/braid/src/objects.rs`、`src/store/mod.rs` 测试；CLI 边界扩展 `sources/braid/tests/cli_writer_boundary.rs`。若需要真实配置恢复，再扩展 `src/local.rs` 现有 product fixture；不新增测试框架或并行抽象。

## 迁移与兼容决定

- `0007` 必须 forward-only、checksum-verified；新列先允许 NULL，使旧 DB 能打开。运行启动时按当前 request 的公开字段注册/回填，回填后新 assignment 只能引用已经验证的公开投影。
- 旧 `request.json` 若缺公开字段，兼容读取时只允许一次确定性回填：`assignee_login` 从既有 profile 的稳定 `display_name`/id 生成，description 使用明确的 legacy “capability description unavailable” 标记；随后写回新 request identity。禁止从 model/provider/digest 推断能力。若产品拒绝 legacy 公开身份，应把旧 run 标为 blocked 并要求重新初始化，不能伪造 `@braid`。
- 旧 `profiles` 行无公开字段时，迁移后仍可用于宿主诊断，但 runtime context 不得输出 profile id；只有成功得到 login+description 的 request 才能启动 Agent。新 request 的公开字段改变必须触发 resume identity mismatch，避免旧会话误绑新身份。
- `desired_profile_id`、`assignment_revision`、assignment generation、session id 和 provider digest 继续留在内部 SQLite/diagnostic 中，绝不作为公开 Item/Context/JSON 合同；旧对象无 assignee 应渲染为空集合，不再伪造 `@braid`。

## 严格实施顺序与每步可运行检查

1. 先冻结 login 命名、大小写、`@` 前缀、description 上限和 add/remove 合同；运行 `scripts/profiles.py` 现有静态解析及一条重复/空/换行/超长负例。失败归属 Factory 配置，不进入 Braid。
2. 添加 `0007`、Profile/Record 字段和 register/upsert；运行 migration-forward/旧 DB fixture，确认旧历史可读、新字段唯一且 checksum 生效。失败归属 schema/Store，立即回滚 migration 与字段，不改对象层。
3. 接上线性 profile→login 映射和 request identity；运行 fresh→resume、改 login resume mismatch、legacy request 兼容三例。失败归属 Config/Local。
4. 让 canonical Issue/PR、Item JSON/text、Context、system prompt 共用一个公开 projection；运行字符串扫描，`list/view/context/status` 与 wake/continuation 输入不得出现 profile、desired_profile、revision、digest、model/provider、`Profile:` 或内部 id；同时断言两个公开 login 和 description 可见。失败归属 Objects/Context/CLI/Provider。
5. 先实现 `create --assignee LOGIN` 和单值 replace；运行 unknown create/edit 前后 work_items、local_items、events、assignments、wake batch 计数完全相同；同值无-op，第二次 replace 只有一个 active owner。再按第“关键合同判定”选择实现 add/remove 或 unsupported 负例，所有组合必须证明同一 transaction 原子性。失败归属 CLI/Objects/Store。
6. 接通 assignment fence→native teardown receipt→retire→new generation/resume；用 A→B→C、stopping、teardown unknown、provider lost、重启四个切点检查旧 turn 写入全拒绝、停止前无新 writer、worktree/comment/evidence 保留、最终仅 C active。失败归属 worker/adapter/store；停止未知必须 blocked/incomplete，不能降级成 DB 成功。
7. 冻结 reassign wake 选择后跑 turn 旅程：当前合同应证明 reassign 只建 idle session；若要求 handoff，则同一 assignment 只产生恰一次目标第一 turn，重复 poll/restart 不增 turn。失败归属 dispatch/scheduler 合同，阻止宣称“指派即开始”。
8. 最后跑一个 Factory task 的 root Issue #1、一个 child Issue、一个 PR 的真实 CLI 旅程；确认 root 唯一、PR/Issue assignee 对称、comment/ready/merge/finalization 与旧工作树恢复仍通过。此步才允许进入实现 handshake，不启动 benchmark/hosted run。

## 可能导致设计回退的证据

- 同一个公开 login 无法稳定映射到一个 profile，或一个 profile 必须暴露多个公开 login：Option A 失效，才考虑独立 projection 表。
- 旧 request/DB 无法确定性回填公开身份，且产品不接受 legacy blocked/re-init：必须回退兼容方案，不能隐式把 profile id 当 login。
- add/remove 的单 owner 原子替换无法在同一 SQLite transaction 中同时保持 fence、desired-null、wake 计数和旧 writer 拒绝：回退到仅 `--assignee`，不要做伪 GitHub 集合。
- 目标 Agent 仍只得到 idle session，或一次 reassign 出现 0/2 个首轮 turn：不能宣称“交接唤醒恰一次”；保留 idle 合同或退回设计。
- native teardown 只有 ack 没有 process terminal + lease receipt，或 crash 切点会产生竞争 writer：回退到 blocked/unknown，不进入局部补丁。
- PR canonical/context 无法与 Issue 共享公开 projection，或一个 Factory task 仍能创建多个根 Issue：设计边界不成立，返回设计而不是补丁。

## 残余

仍未由本次只读检查冻结：公开 login 大小写/`@` 规则、description 字节预算与是否每次 Context 注入、PR 是否必须显示完整成员目录、reassign 是否保留一次 Wake、`--remove-assignee` 的 desired-null/重新激活合同、legacy 迁移接受 blocked 还是稳定回填，以及远端 GitHub actor 与本地 synthetic actor 的字段共用。现有测试未覆盖这些项；因此本 Cell 只能作为实施前影响握手，不能以源码审阅或全量旧测试宣称 assignee projection 已通过。

验证命令：`cargo test --all-targets`（`sources/braid`，28+1 全部通过）。
