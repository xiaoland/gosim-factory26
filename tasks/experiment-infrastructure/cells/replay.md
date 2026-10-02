# Braid 事件重放与离线准备

用户于 2026-09-28 授权“继续改进基础设施，打通断点恢复”。本工作只改 Braid Store/Actor；宿主入口与 SessionManager 由主 Agent 接线。未运行 Factory 基础设施测试、模型或官网实验，未提交。

来源归档 `runs/e20260928-completed-replay/{github,sheet}/source-workspace.zip` 的 SQLite 页在独立临时目录以只读方式查询，`PRAGMA quick_check` 均为 `ok`。GitHub 有 160 个 pending 事件仍绑定 consumed 批次、237 个有 batch_id 却无事件成员的历史 turn；Sheet 分别为 141、443。后两个总数包含所有 trigger，审查文件中专指 `terminal_contact` 的 236/441 是其子集。原始查询与事件实例见 `tasks/braid-architecture-audit/evidence.md`。

根因是 `wake_batch_events.event_id UNIQUE`：旧 unknown 路径把已消费的原事件改回 pending 后再次 `schedule_event`，新批次成员插入被忽略。现在 unknown 与既有 failed 路径共用复制 replay event 的实现；新事件有独立 ID 和可幂等的 dedupe key，原事件、原批次、原 turn 保留作历史。`advance_scheduler` 和显式离线准备会把已经残留的 pending/consumed 旧绑定转换为 replay event，并封存旧 pending 状态。无实际 pending 成员的开放批次不再转为 runnable，claim 也不会取它；调度器会封存既有空批次。

`StoreActor::prepare_offline_resume() -> Result<Vec<String>, StoreError>` 是宿主停止断言之后、取得 runtime.lock 和核对原 request 之后调用的单个事务：返回旧 provider ID，撤销旧 CLI binding；将 active `interrupting` reset 改为 `materializing` 并移除过时 active_turn_id；旧 active turn 走 unknown fencing/replay。旧通知 turn 也封存为 unknown；这只记录宿主中断，不伪造通知收据。若旧 turn 与待处理 Context 失效同时存在，离线入口保留新 reset 的 materializing 状态并重放原输入。已有 `blocked` 状态不清除。返回的 provider ID 只供这次 SessionManager 的 stopped 证明，调用者不能将其持久化为普遍停止事实。

验证：`cargo check --offline` 通过，只有原有 dead-code 警告。真实未完成快照的 WSL 接续及新 turn 输入追溯由主 Agent 执行；编译和只读源数据统计本身不证明实际恢复成功。
