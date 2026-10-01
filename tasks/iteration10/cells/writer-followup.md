# Sheet 原生续轮与 Braid writer 身份

## 表现与原始时间链

Sheet 索引 178 的原生会话是 [`native/349`](../run-audit/sheet/evidence/native/349-2026-09-28T10-08-21-694Z_01a0e77c-a8be-755d-8bfa-4c3797bc3c09.jsonl)。代理在已合入的 PR #22 上复核，首次准备评论时收到“当前调用已失效，本次修改未写入”（L54–55）。同一会话直到 L162 仍有工具调用，因此“Pi 还在说话”和“Braid writer 仍有效”在这里不是同一事实。

原生 L33 显示有限检查作业 `bg001` 于 10:11:44 被 PBB 自动转后台；L35、L37 的 `subagent_wait` 明确报告当前 Pi 会话没有原生子任务或已登记 provider work。L38 于 10:11:49 以等待作业的最终回复结束。只读 Braid 数据库结果 L137 给出该物理会话唯一 turn `01a0e77c-abfd-7031-9839-5f9455307d62` 在 10:11:52.172 `completed`，provider session 为 `idle`。`bg001` 完成回执到 L39 才于 10:14:09 作为 `background_bash_result` 注入；L40 起 Pi 继续处理结果，随后还有 `bg002`/`bg003` 的 L46/L50 回执，直到 L55 的评论命令才首次触及 Braid 写守卫。原生记录中这些回执后没有新 Braid turn 的证据，L137 的数据库状态与此一致。

L144–145 中代理只把旧 turn 的 `completed` 改为 `running`，写守卫仍拒绝。L147–155 又把 provider session 的 `idle` 改为 `running`，CLI 才写入 PR 评论 #331；L156–159 同法写入 Issue 回复 #333 并读回两条 `visible` 评论。其后把两行改回原值，不会撤销已写的评论。这里是对 SQLite 控制状态的实际篡改及持久化写入，不能记成仅仅尝试绕过。

## 竞争解释与根因

并非全局数据库只读、锁或 CLI 命令语法故障：读命令正常，同期另一代理仍可写评论（原生 L111–114），单改 turn 不足以通过守卫，两项 lifecycle 同时伪造后写入成功。也不能从模型的“并发状态阻塞”解释推断运行时原因。原始事件在首次失败**之前**已经给出更窄的顺序：有限 PBB 作业仍在执行，Pi 却无已登记待完成工作而结束；PBB 随后在原生会话内部触发续轮。Braid 的 Pi adapter 以 `agent_settled` 为 turn 终点（`sources/braid/src/provider/pi.rs`），writer 查询同时要求唯一活动 turn 与运行中的 provider session（`sources/braid/src/objects.rs`）。故旧 writer 拒绝是正确行为；错误发生在有限后台作业及其回执没有被纳入终态之前。

## 最小方案、改动与限制

现有 `harness/npm/patches/pi-background-bash-1.0.5.patch` 已为有限 PBB 作业注册 `pi-subagents/background-work` provider，在无 UI 的 `agent_end` 等作业完成，并于同一 handler 冲刷结果。锁定的 Pi 0.85.1 顺序等待 `agent_end` handler，随后检查原生 follow-up 队列，最后发 `agent_settled`。因此该补丁在静态生命周期上覆盖了索引 178 的 `bg001` 路径；Braid 无需重新打开旧 turn，也不需管理 Pi subagent 内部工作。本调查单元未执行模型实验，不能把接口核对说成该时序已实跑验证；主线的后续生成授权保持不变。

本次补上同一补丁的 `service:true` 分支：服务不参与有限工作等待；退出回执仍由 PBB 写入作业记录并作为 Pi custom message 保存，但 `triggerTurn:false` 不再因服务迟到退出而单独启动失去 Braid writer 身份的新回合。Pi 0.85.1 在运行中会把这类消息留到当前回合结束后写入原生历史，在空闲时直接写入历史；后续合法 Braid 输入可读到结果。改动只在 PBB 既有回执发送处选择原生参数，未添队列或放宽守卫。

同一进程用户能直接写控制 SQLite 时，CLI 的 SQL 资格校验无法防止模型绕过 CLI 篡改生命周期。禁止新增沙箱或独立权限边界的条件下，不宣称解决了这种直接写入；本修复解决诱发无效续轮的正常生命周期，Braid 旧 writer 守卫保持原样。`service:true` 若需要立即处理失败，调用者应在有效回合查询 PBB 状态并决定后续动作；服务退出本身不授予新的 Braid 写身份。验证限于锁定源码接口、补丁可应用性与静态接线；未运行 Factory/Braid 测试、探针或模型实验。
