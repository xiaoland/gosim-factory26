# 指派身份与离线会话恢复

2026-09-28 DeepSeek attempt03 恢复时，更新后的内建指令使旧 provider session 的 `instruction_revision` 不匹配。`GroupDriver::resume` 把该差异作为不可恢复故障，`block_provider_session` 将 assignment 标为 blocked。之后待处理的激活事件又尝试为当前 `desired_member_login` 插入新 assignment，触发 `assignments_member_login` 唯一索引。这个唯一约束正确保护了公开成员身份；不应删约束或另造 login。

热修复使指令或 Profile revision 变化进入既有 Context reset：确认旧物理会话已停后，在同一 assignment、agent 和 worktree 上建立 `materializing` reset，更新绑定的 Profile revision，并由原流程新建 provider session。已因同类不兼容而 blocked、仍与当前工作项指派一致的记录也可进入这条路径。旧激活事件在 blocked 同成员 assignment 存在时保持待处理，不再试图插入相同 login。仓库、工作项、工作树等其它不兼容情况仍保持原错误处理。

离线恢复请求允许在原 run 身份、根 Profile、Profile 身份和模型配方、adapter 类型不变时更新 `user_instructions` 与原生 binding 材料。更新前将旧 `request.json` 归档到 `request-history/`；普通恢复仍要求材料完全一致。原生会话停止由 `--offline-resume` 的宿主断言或当前 SessionManager teardown 证明，不能仅凭数据库状态推断。

验证边界：`sources/braid` 的 `cargo check --locked` 通过；定向 Braid 回归 `blocked_instruction_change_replaces_session_without_reassigning_member` 通过，覆盖 blocked 旧会话、unknown turn、同成员待激活事件、新指令 revision 写入与原 assignment 上的后续 turn。未运行 Factory 测试、探针、模型或付费实验；attempt03 真实状态接续由主线负责，运行库未修改。

## attempt05 遗留 reset 接续

attempt05 两份真实数据库的只读副本显示，新热修复已成功建立物理会话，但从 attempt03 继承的 `materializing` reset 完成后，旧 assignment 仍是 blocked：GitHub Issue #1/#2 均为 `assignment=blocked, agent=idle, new provider=idle, reset=applied`；Sheet Issue #1/#2/#3/#4 同类，#5/#7 仍有 `materializing` reset 且旧 assignment blocked，#6 为 `materializing`/`reset_pending`。新 provider 已带当前指令，所以再比较 revision 无法触发另一轮 reset。

修复在既有事务中闭合两条边界：离线入口只把“当前成员、已 applied reset、新 provider idle、agent idle”的旧 blocked assignment 恢复为 active/finalizing；`complete_context_reset` 复查当前成员和 assignment revision，并在遗留 materializing reset 完成时归正旧 blocked assignment。`local::drive` 的 blocked 判定等待所有 Issue/PR driver 首次 health 报告及 `pending_resets=0`，避免中途截断恢复。`block_provider_session` 仍为真正无法恢复的原生故障保留 blocked assignment，现有不可达消息结算与显式改派的工作树继承依赖该状态；指令/Profile 变化已改走 reset，不再调用这个故障入口。

验证：从 WSL attempt05 两个运行库各复制一份到本机临时目录，运行临时 Braid 定向检查，仅在副本上调用 `prepare_offline_resume` 与遗留 reset 的 `complete_context_reset`。两份副本均达到“当前成员的 blocked assignment 为零”，且已 applied 的新 idle session 获得可恢复 assignment。临时检查源码已移除；没有改动运行库，也没有启动模型。此验证证明 store 状态可闭合，不等于真实原生会话已成功启动或任务已完成。
