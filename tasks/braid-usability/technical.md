# 技术方案：隐藏运行身份，保留工作项语义

状态：技术方案及独立预演已完成；当前推进状态与授权纠正见 [packet](packet.md)。
最终接口决定及顺序见 [实施计划](plan.md)，实际结果以 packet 和运行证据为准。

## 职责与数据流

```text
Factory variant
  └─ 成员目录 + 根 Issue 启动成员 + 任务输入
Braid
  ├─ Issue/PR/讨论对象：共享工作内容与明确的 assignee
  ├─ 现有上下文投影：当前正文、可见讨论、关联工作项
  ├─ 调度与会话：运行已指派工作项，处理既有上下文替换
  └─ 启动环境：自动绑定当前执行实例的 CLI 身份
Pi / Codex app-server
  └─ 主 Agent 与原生 sub-agents；继承工作项调用身份
```

Braid 只实现对象、消息送达、上下文投影和执行机制。
不从评论语义推断方案已批准、需求已完成或应该拆分；这些判断属于 LLM。

## 1. 自动取得 CLI 调用身份

当前 `dispatch.rs` 在每轮文本输入中附上 state/writer-turn，`cli/mod.rs` 要求再次传入，`objects.rs::writer` 从 turn 查作者和有效性。
直接把 turn 写入进程启动环境不成立：Pi RPC 和 Codex app-server 会跨多个 dispatch 持续运行。
按工作目录查最新身份也不成立：上下文重建沿用 worktree，旧进程可能误取到新身份。

建议使用与一次原生执行实例绑定的不透明 CLI 身份，经子进程环境传递。
启动或恢复原生进程时产生新 binding；同一进程内的后续 dispatch 沿用 binding，重建或重启恢复时换新 binding，旧 binding 不再有效。
binding 只定位 Braid 记录的 provider session，不是 Agent 可选的角色，也不需要 Agent 读取或复制。

具体接线：

- SessionFactory 的启动/恢复契约传递内部 `CliContext`，其中包含 state 路径和 binding；不把它放入可选 profile 或用户指令。
- Pi 子进程与 Codex app-server 子进程设置该环境，保证其 shell 能解析本次运行的 `braid`；沿用现有 PATH 接线方式。
- binding 与 provider session 的关联在现有状态库持久化，原生创建返回 session ID 后绑定，完成绑定前不派发模型工作；恢复同一原生历史也撤销旧 binding。
- CLI 在写入事务中由 binding 找到其所属且有效的 session、当前执行记录和 assignment，复用现有作者归属与失效检查。没有当前可写执行则返回明确错误，不挑选另一 session 或猜测最近的 turn。
- 读操作同样能识别运行位置和当前工作项，但不要求正在采样；宿主诊断保留显式 state，Agent 路径不使用 external。
- dispatch 输入与 Agent 提示删除 state/writer-turn 前缀及手工身份更新说明；内部 turn 记录可继续用于诊断，无需一并重构 provider 协议。

原生 sub-agent 继承同一工作项的身份，不据此新增 Braid assignment；Braid 不替 Pi 管理其后台进程。
这里将调用授权绑定到执行实例而非启动时的某个 turn；不宣称能仅凭继承环境辨别每个后台工具最初由哪次模型采样发起。
旧执行实例失效、重指派和已封存 run 仍拒绝写入。

预演收敛为 provider_sessions 上新增可空唯一的 cli_binding_id，SessionManager 在真正 start/resume 前生成 CliContext，CreatedSession 返回 binding ID。
各 complete 注册事务把后得的 provider session ID 与 binding 一并持久化；resume 先清旧 binding，再启动并登记新 binding。
详细调用点见 [身份预演](rehearsal-identity.md)，不另建命令服务或身份守护进程。

## 2. 明确指派，移除两层自动选择

已核实的修改面：

| 位置 | 当前行为 | 目标 |
| --- | --- | --- |
| 四个 `variants/*/run.py` | `DEFAULTS={issue,pr}` | 仅声明根成员，成员原生配置继续各自维护 |
| `config.rs`、`local.rs` | 必须验证 Issue/PR 两个默认 profile | 请求只声明根启动成员，初始化根 Issue 时明确指派 |
| `objects.rs::create_item` | assignee 缺失时读全局默认 | 缺失保持 NULL；仅显式指派才激活 |
| `store.rs::begin_agent_assignment` | desired_profile 缺失时写入抢到事件的 profile | NULL 不创建执行，必须与明确 assignee 匹配 |
| 事件选择、claim、unassign/reopen 路径 | 部分 SQL 将 NULL 视作任意 profile 可用 | NULL 只能表示未指派，不能经后续路径被自动认领 |

创建未指派对象不发启动它的 assign 事件；正常对象变化和已有讨论保留。
之后 edit 指派复用现有 assignment 路径；取消指派停止既有执行，但保留对象和已有工作。
旧数据库迁移沿用现有机制，保留已经明确记录的 assignee，不批量重写历史结果；新请求不继续提供自动分工默认值。

## 3. 上下文整理与 Agent 指引

复用 `context.rs` 对 Issue/PR/关联对象及评论的现有投影，不另造共享记忆文件或第二份上下文 schema。
`group/provider.rs` 的角色说明围绕当前工作项与产品动作编写；删除内部 writer、finalization 等操作要求和整页 CLI 参数清单。
四个 variant 的 instructions 删除重复协作协议，保留成员能力、原生委派和无人值守边界；SVC skill 不改。

评论同类整理使用多 ID CLI 参数；先在同一 SQLite 事务中读取并验证全部对象，再执行 resolve 或 hide，整组提交后才让既有 invalidation 机制处理结果。
错误时保持整组未应用；只触及原操作会影响的工作项，不建立新的语义事件类型。
批量整理复用对象更新语义，不能逐个调用会自行提交的现有 public 方法。
帮助说明批量整理是一次操作，正文更新会使后续会话基于当前工作项继续，不要求 Agent 拷贝 turn 或执行 refresh。

## 预演结论与实际运行边界

1. [身份预演](rehearsal-identity.md)已定位 start/resume/reset/reassign 注册点、后得 provider ID 与原评论审计字段的改动。
2. [指派预演](rehearsal-assignment.md)已定位 NULL pending 事件、closed sleeping 组与 reopen 复活旧执行者的路径，计划纳入清退与当前指派匹配。
3. [上下文预演](rehearsal-context.md)已定位批量事务、既有 invalidation 和六份 variant 指令归属。
4. Pi 内置工具的环境继承有当前本地源码依据；Codex 原生工具继承未实际运行验证，官方环境配置能力及本轮验收边界记录在实施计划。

上述检查采用调用链、接口资料与后续授权的真实操作，不为 Factory/基础设施新增测试或探针。
若预演发现必须扩大到调度重写或 Pi 内部生命周期管理，应回到产品边界复核，不带着更大隐含范围开工。
