# Braid 核心实施交接

范围：`sources/braid` 的 `src/**` 和 `migrations/**`，其中 `src/group/provider.rs` 由并行任务负责，本轮没有修改；`src/config.rs` 和 `src/provider/codex.rs` 原有的 modelProvider 变更已保留。未提交、未推送、未改测试或运行实验。

## 已落地

1. **隐式 CLI 身份。** 新增 `0008_cli_binding.sql` 的 nullable、唯一 `provider_sessions.cli_binding_id`。`SessionManager` 在原生 start/resume 前生成绑定，`CliContext` 将状态目录和绑定传至 Pi/Codex 进程环境。恢复旧会话时先清除旧绑定，成功后记录新绑定。`LocalObjects::writer` 在同一对象事务中按当前 binding 查找唯一活跃 turn，并沿用生命周期、reset 和 invalidation 栅栏。Agent CLI 从环境读取身份，不再需要 dispatch 附加 `--state --writer-turn`；普通 help 隐藏 `--writer-turn`。Pi 的 `start_turn` 不再用旧 binding 自行重启断开的原生进程。
2. **明确指派。** 本地请求用 `root_profile_id`，初始化根 Issue 时在一笔事务内记录 Profile 并发 `Assign`。新建 Issue/PR 缺省为 NULL，只有显式给 assignee 才发激活事件；移除默认补人和 NULL 自动认领。候选激活、claim、resume、dispatch 都要求当前明确 Profile 与 assignment revision 匹配；未指派的历史 pending 激活收敛为 no-op，列表和上下文显示“未指派”。关闭后的 sleeping 组也纳入取消/改派清退；reopen 只复活当前匹配组，若有明确指派却无可复活组则补发 `Assign`。Issue/PR unassign 均走物理会话清退再退休，并在取消指派时退休工作树。
3. **多评论整理。** `comment hide` 和 `comment resolve` 接受多个 ID，原单 ID 语法仍可用。对象层一次 Immediate 事务先读取校验整组，再更新、发既有 discussion invalidation，最后统一提交；重复 ID 与同一 resolve thread 去重。`unhide/delete/unresolve` 保持原单 ID 语义。

## 构建与验收边界

在上述修改后，`cargo build --locked` 成功，18 个 dead_code 等非阻断警告；`git diff --check` 无输出。没有运行测试、探针、模型或真实任务，因而原生 CLI 的环境继承、SQLite 迁移和端到端语义仍需下一阶段真实验收。Codex app-server 启动时已设置绑定环境，但其工具 shell 是否继承要在实机观察。旧 `cfg(test)` fixture 仍引用过去的接口；本轮按约定未写改运行测试，也未为它们增加生产兼容层。

涉及文件：`src/agent_session.rs`、`src/cli/mod.rs`、`src/config.rs`、`src/context.rs`、`src/group/{dispatch,issue_agent,pr_agent,session_manager,worker}.rs`、`src/local.rs`、`src/objects.rs`、`src/provider/{factory,pi,codex}.rs`、`src/store/mod.rs`、`migrations/0008_cli_binding.sql`。
