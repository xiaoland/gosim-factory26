# Braid 本地产品实施

本地 Issue/PR/comment 产品链已实现，保留原 Context renderer、StoreActor/projector、queue、Agent Group、SessionManager 与 Git worktree 执行链。`local.rs` 的固定阶段草稿已替换；GitHub App/HTTP、producer/writer、远端 CLI 和启动配置已裁剪。历史迁移不重写，其中旧远端表不再是本地正文权威。

接口为 `braid local request.json`，请求沿用 profile/codex/pi/prompt/state，增加 run_id 和 delivery_ref。Profile 使用 context_soft_ratio/context_hard_bytes，不再接收 github_actor_node_id/status_surfaces。Factory 提供有初始 HEAD 的隔离仓库；Braid 为根 Issue 分配 delivery worktree，PR 使用各自分支/worktree。写 CLI 必须显式带本轮 `--writer-turn` 或宿主 `--external`。当前权威使用说明位于 sources/braid/docs/20-product-tdd/local.md。

本地 SQLite 原子保存完整正文、稳定 comment 身份/墓碑、N:M 关联、实际 writer group/turn 和事件。自写只产生 OriginEcho；其它受影响组仍按 direct invalidation 或相关 Wake 更新。合法下一轮在派发前校验实际 Context，必要时沿原 reset 替换物理会话，保留 group/worktree。finalizing 状态也保持该约束，旧 turn 的控制操作在事务内拒绝。

PR ready 保存已提交候选，根 Issue 接受并合入交付分支。合并先写 durable intent，再 CAS 更新 Git ref，支持 Git 已完成而 SQLite 未收据的幂等恢复，并拒绝覆盖未知未提交内容。根 Issue completed、各工作项处置、finalization 成功、队列/reset/merge 收敛后才能封存交付 commit；provider turn completed 本身不是整体成功。

state/result.json 返回整体终态与固定 delivery_commit；state/sessions.json 持续列出所有真实建立的物理会话及实际 instructions/context/turn 输入路径。失败也保留证据。未建立的启动尝试不冒充物理会话；已建立但物化失败或身份响应丢失的会话保留 unknown，不能静默略过。Factory 负责按精确 Codex thread ID 或 Pi 原生路径验证会话和冻结 commit。

2026-09-20 局部验证：`cargo test --quiet` 实际 10 项通过（0 failed，4.48 秒）。其中原 provider/store 边界与新增完整产品场景共同覆盖两 PR 产物合入、恰一次 finalization、实际新 Context/旧正文消失、comment hide/unhide/delete、N:M/ensure 幂等、跨组 writer 与原子 fencing、冲突放弃、Git/数据库中断恢复，以及启动尝试与已建立 unknown 会话的归档区别。`cargo fmt --check`、`cargo check`、`git diff --check` 在提交前完成；check 仍有裁剪后保留的历史 store/telemetry dead_code 警告。

当前状态：稳定本地提交为 `5957d2f9404cda84d781ded51d681ae7b1b1f91d`，子仓库 clean，已通知主流程刷新构建 stamp 后运行关闭 SVC 的真实 Pi/Codex 受控探针。真实探针期间不继续修改该源码快照。局部检查不是比赛模型、真实接入或 Keep bench 通过的证据；本轮未读取凭据、调用比赛模型或运行 bench。真实探针和四组新 bench 的结论由 Factory26 主任务后续记录。

真实 Codex 探针 `runs/integration/20260920-222837-codex-plain-5ea7e9` 的通用产品断言通过（5 个物理会话），但原生证据额外揭示了宿主入口误用：PR finalization session `01a0bf46-343c-7ba1-97e0-bcdf615c9f48`、Braid turn `01a0bf46-352c-7071-bc4e-bf71b23cc7eb` 先用 `--external` 建立 comment #6，数据库 writer 为空并产生 Wake；随后同 turn 用正确 writer 建立 comment #7 并删除 #6。可从该 run 的 native/manifest.json 按 session 精确定位。原探针未覆盖这个边界，不能用其 passed 证明防误用有效。

本轮窄修正只在 Codex app-server 与 Pi RPC 子进程启动时设置 `BRAID_AGENT_RUNTIME=1`，包括 resume 的新进程。CLI 在标记环境中访问对象前拒绝 external；默认 help 隐藏宿主参数，缺 writer 时只提示本轮 writer。宿主无该标记时仍保留显式 external。没有新增 broker、凭据或权限体系，也不声称防止清除环境变量或直接修改数据库；Context、queue、merge 语义保持不变。

窄修正局部验证：11 项单元测试与 1 项真实 CLI 二进制集成测试全部通过（分别 4.51 秒、0.38 秒）。新 CLI 测试实际以标记/无标记环境启动 Braid，证明 Agent external 的正文与 comment 写入均被拒绝且正文、revision、comment/event 数量不变；宿主 external 写入成功，当前 writer 成功，旧 writer 拒绝且状态不变，help 不显示 external。假 Codex app-server 与 Pi RPC 的真实子进程均验证 start/resume 继承标记，且不改测试宿主环境。首次自查只发现测试 fixture 仓库 node id 与产品约定不一致，修正 fixture 后全套通过，未扩大产品实现。`cargo fmt --check`、`cargo check` 和 `git diff --check` 通过；新增 guard 的真实 native shell 检查由主流程在新构建上重新运行两个探针，旧 probe 证据保留。

防误用修正稳定提交为 `bd0cfcce01dead92e19fc58f34805aa231624927`，Braid 子仓库 clean，已冻结并通知主流程刷新构建及重跑两个真实探针。该提交只包含 CLI/provider 启动边界、相应回归测试和 local.md 合同；没有运行模型或 bench。
