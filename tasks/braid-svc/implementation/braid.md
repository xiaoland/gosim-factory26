# Braid 本地产品实施

本地 Issue/PR/comment 产品链已实现，保留原 Context renderer、StoreActor/projector、queue、Agent Group、SessionManager 与 Git worktree 执行链。`local.rs` 的固定阶段草稿已替换；GitHub App/HTTP、producer/writer、远端 CLI 和启动配置已裁剪。历史迁移不重写，其中旧远端表不再是本地正文权威。

接口为 `braid local request.json`，请求沿用 profile/codex/pi/prompt/state，增加 run_id 和 delivery_ref。Profile 使用 context_soft_ratio/context_hard_bytes，不再接收 github_actor_node_id/status_surfaces。Factory 提供有初始 HEAD 的隔离仓库；Braid 为根 Issue 分配 delivery worktree，PR 使用各自分支/worktree。写 CLI 必须显式带本轮 `--writer-turn` 或宿主 `--external`。当前权威使用说明位于 sources/braid/docs/20-product-tdd/local.md。

本地 SQLite 原子保存完整正文、稳定 comment 身份/墓碑、N:M 关联、实际 writer group/turn 和事件。自写只产生 OriginEcho；其它受影响组仍按 direct invalidation 或相关 Wake 更新。合法下一轮在派发前校验实际 Context，必要时沿原 reset 替换物理会话，保留 group/worktree。finalizing 状态也保持该约束，旧 turn 的控制操作在事务内拒绝。

PR ready 保存已提交候选，根 Issue 接受并合入交付分支。合并先写 durable intent，再 CAS 更新 Git ref，支持 Git 已完成而 SQLite 未收据的幂等恢复，并拒绝覆盖未知未提交内容。根 Issue completed、各工作项处置、finalization 成功、队列/reset/merge 收敛后才能封存交付 commit；provider turn completed 本身不是整体成功。

state/result.json 返回整体终态与固定 delivery_commit；state/sessions.json 持续列出所有真实建立的物理会话及实际 instructions/context/turn 输入路径。失败也保留证据。未建立的启动尝试不冒充物理会话；已建立但物化失败或身份响应丢失的会话保留 unknown，不能静默略过。Factory 负责按精确 Codex thread ID 或 Pi 原生路径验证会话和冻结 commit。

2026-09-20 局部验证：`cargo test --quiet` 实际 10 项通过（0 failed，4.48 秒）。其中原 provider/store 边界与新增完整产品场景共同覆盖两 PR 产物合入、恰一次 finalization、实际新 Context/旧正文消失、comment hide/unhide/delete、N:M/ensure 幂等、跨组 writer 与原子 fencing、冲突放弃、Git/数据库中断恢复，以及启动尝试与已建立 unknown 会话的归档区别。`cargo fmt --check`、`cargo check`、`git diff --check` 在提交前完成；check 仍有裁剪后保留的历史 store/telemetry dead_code 警告。

当前状态：稳定本地提交为 `5957d2f9404cda84d781ded51d681ae7b1b1f91d`，子仓库 clean，已通知主流程刷新构建 stamp 后运行关闭 SVC 的真实 Pi/Codex 受控探针。真实探针期间不继续修改该源码快照。局部检查不是比赛模型、真实接入或 Keep bench 通过的证据；本轮未读取凭据、调用比赛模型或运行 bench。真实探针和四组新 bench 的结论由 Factory26 主任务后续记录。
