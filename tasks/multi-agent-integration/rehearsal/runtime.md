# runtime-ready 01：Braid 运行链预演

范围：Factory `e229e6b`、Braid `63459fc`；只读源码预演，未调用模型。Braid clean；Factory 的 `tasks/competition-p0/packet.md` 是既有无关改动。

## 已证实的起点

- `local.rs::Request` 只有一个 `profile` 和全局 `codex`/`pi`；`config()` 把它复制为硬编码 `local-issue`、`local-pr`，`drive()` 仅启动两个 `GroupSpec`。
- `GroupSpec::new` 以 kind 选 profile；`assignment_candidates` 只按 kind 查询。`claim_runnable_turn` 已按 kind + `agent_instances.profile_id` 二次筛选，但没有 desired-profile 来源，不能单独修 claim 解决多 profile。
- `profiles`/`agent_instances` 保存的是实际 profile revision；`local_items`、`assignments` 均没有 desired profile/assignment revision。CLI 无 `--assignee`，`Item` 无该字段，Issue Context 还硬编码 assignee 为 `braid`。
- `PiConfig` 目前持有 provider/model/thinking，`PiProvider::spawn` 从它传 `--provider/--model/--thinking`；Codex 已从 `Profile` 传 model/reasoning。这是双权威。
- Context reset 已先在 store fence writer，但 `SessionManager::remove → close → interrupt` 只向父 Pi 发 `abort`；Pi `kill_on_drop` 也只杀父进程。现有 unassign 甚至先把 DB 标 retired 再 best-effort interrupt。没有 detached child 已停写的证据。
- `sessions.json` 只有 provider/session/worktree/context；缺 profile id/effective digest/native home/parent native session。Factory 现有归档无法可靠关联 child。

## 01 合同（供 Factory/capabilities/feedback 消费）

请求只传普通对象：`profiles: Vec<Profile>`、`defaults: {issue: ProfileId, pr: ProfileId}`、`bindings: BTreeMap<ProfileId, RuntimeBinding>`。三者启动前严格校验 ID、adapter 一致和一一对应；不得有 preset/variant 字段、摘要或文件路径。

`RuntimeBinding` 只含 adapter executable、认证引用、只读 native template、能力摘要与每 physical root 的 native-home materialization 参数。`native_teardown` 为可选受控 hook：`{ command, receipt_relpath }`；不把 Pi 子代理产品名或 RPC 细节做成 Braid 配置。启用外部 Pi subagents 的 binding 必须有该 hook，能力摘要必须覆盖它；Codex 内置子树由其 adapter 的关闭机制负责，不套用 Pi 命令。

`Profile` 是 provider/model/reasoning/instructions/skills 的唯一语义权威；Pi runtime config 收缩为 executable、认证、目录/template。Pi spawn 改传 `profile.provider/model/reasoning`。effective digest 计算 profile + binding 的语义材料/core 版本，排除临时 home/port/key；不能继续只 hash `Profile`。

每个 physical record（并汇入 `sessions.json`）至少写：`profile_id`、`effective_profile_digest`、`work_item_kind/id`、`assignment_generation`、`parent_native_session_id?`、`native_home`、`native_session_path?`。Factory 由真实 header/artifact 扫描 children；Braid 不伪造 child 清单，也不写 preset。

## 最小按序实施切片

1. **注册与启动。** local/config 注册整个 catalog，所有 `(issue|pr) × profile` 启动一个 `GroupSpec`；SessionFactory 按 profile ID 选 binding，并在 physical directory 物化隔离 native home。先替换单 profile request/global ProviderConfig，再改 Factory 装配。
2. **对象与 desired 状态。** 新 migration 在 `local_items` 加 `desired_profile_id`、`assignment_revision`，在实际 `assignments` 记录其采用的 revision。root 用 Factory 显式 default；`issue/pr create --assignee` 与 `issue/pr edit --assignee` 都先查当前 catalog，未知 ID 在任何对象/event 写入前失败；同 ID 无操作。list/view JSON 和 Context 显示当前 desired profile。
3. **切换事务与 claim。** `--assignee` 递增 desired revision，立即把旧 assignment/turn 置为 fenced/stopping，使 `writer()` 失效；旧 worktree、讨论、未提交文件和旧 session evidence 保留。候选与事务 claim 同时要求 kind、desired profile 和最新 assignment revision；stopping 计入唯一 active fence，不能被另一 worker 绕过。停止成功后才 retire old、按最新 desired 创建新 generation；连续重指派只读最新 desired，旧请求不能覆盖它。closed 项只更新 desired，reopen 时不复活 revision 不同的旧 assignment。
4. **reset/取消/恢复。** profile 不变的 Context reset 走同一 fence→teardown→receipt→close→materialize 链；reassign 和 runtime shutdown 亦然。shutdown/失联只能记录 unknown，不能以父 process exit 认定 child stopped。恢复若无与当前 fence/session 匹配的 stopped receipt，assignment/context-reset 保持 blocked/unknown，禁止同 worktree 新 writer；有 receipt 后才恢复或物化。

## 子树 fence 的可验收边界

Braid 写 `.factory/teardown-request.json(fence_id,parent_native_session_id,started_at)` 到独立 native home，调用 binding 的受控 command，读取 `.factory/subagent-stop.json` 的同 fence receipt。receipt 含 schema_version、fence_id、parent_native_session_id、state（stopped/unknown）、children 证据及 completed_at。foreground 证明其 control 已退出；background 证明 terminal、process-terminal observed 与 lease 释放，不能给 foreground 强加不存在的 background 文件。hook 消费这些原生证明，Braid 校验当前请求身份及最终停止结果，不持有插件的内部调度语义。任一缺失、错误或断连均 block/unknown；随后才 abort/kill 父。父 terminal、Pi abort 或 listener abort 均不构成 child termination proof。

## 现有验证入口与缺口

- `cargo test --offline`：20/20 通过（19 bin-unit + 1 CLI integration）；只有既有 dead-code warnings。`cargo test --offline --lib` 不适用，因为 crate 只有 bin target。
- 延伸 `local::same_kind_sessions_overlap_reset_independently_and_do_not_starve_close`：两个 profile、同 kind 的独立 claim，显式/default/unknown assignee，same-profile no-op。
- 延伸 store reset fixture：desired revision 竞争、old writer rejection、重启中 stopping/receipt 缺失、reopen 采用最新 desired。
- 延伸 `provider::factory::pi_sessions_isolate_context_failure_and_release`：真实 detached child heartbeat/lease；仅父 abort 必须失败，matching receipt 后才停止写入并允许新 generation。另为 Codex native child 加同一 observable contract。
- 延伸 `cli_writer_boundary` 和 sessions archive test：assignee JSON/CLI、无 preset 字段、profile/digest/native identity 的归档消费。

## 判定

建议按上述四 slice 实施；当前基础测试通过，但多 profile、direct assignee、子树停止及新 archive identity 都尚未被证明。唯一实质风险是 native teardown receipt 的真实接口；能力主线已给出受控 hook 方向，若实现无法提供匹配 receipt，应保持 blocked/unknown 而非降级为父停止。
