# 重置通知 Deferred 热修复实施

本 cell 已获用户授权直接修复和热部署清晰设施缺陷。源码改动位于独立 Braid 仓库；远端运行和部署由主 Agent 执行。

## 修改

- `AgentSession::can_accept_input` 经 Provider 查询原生接收状态；Pi 使用 `get_state` 的 streaming/compacting 事实。调度将可接收的 session ID 同时传给普通 wake 和 reset notice 的 claim，因此一个忙会话不挡其它会话。发送时的竞争仍由 Deferred 分支处理。
- reset notice 首次 claim 建立一个未开始 turn。Deferred 将其置为 `deferred`，保持 `active_turn_id`，恢复时重新领取同一 turn；不写 `failed` 和 `ended_at`。重启恢复保留这项待投递义务。
- schema 16 为 `turns` 增加 `deferred_reason`、`first_deferred_at`、`last_deferred_at`、`deferred_count`。普通输入发送后 Deferred 仍走原有 batch 重放，记录其具体原因和时间；不会把发送前筛选到的忙碌视作一次投递尝试。

## 验证与交接

本地仅运行 `cargo check` 和静态 diff 核对；按仓库约定不新增或运行测试、模拟探针。主 Agent 负责 Linux 构建、schema 迁移备份与运行热部署，依据原生记录验证同一 reset 的待投递、成功送达及无 failed turn 风暴。
