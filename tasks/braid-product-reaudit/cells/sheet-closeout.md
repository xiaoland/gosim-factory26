# Sheet continuation-03 收尾根因与恢复边界

只读运行状态截面截至 2026-09-28 12:34 UTC，来源证据核对截至 12:43 UTC。目标是 `pi-braid--hackathon--sheet-22730f82778f3a`，沿用 [后段进展](sheet-progress-late03.md) 与 [未闭合证据](open-evidence-followup.md)。没有改应用、脚本、运行数据库、进程或官网任务，也没有启动第十次迭代。

## 因果链

| UTC | 持久证据 | 含义 |
| --- | --- | --- |
| 08:12:42.047 | `attempt-09/pre-stop-state.json` 保存 08 的 Sheet run 仍 `running`；随后 `stop08-operation.json` 记录 `lab stop` 请求 | 停止与后续 PR #19 创建并发；不能假定停止截面之后无新写入。 |
| 08:12:44.579—08:12:45.739 | 08 Braid `local_activity` 创建 PR #19 并指派 glm-16；`events` 的 assign 被消费；`assignments/agent_instances` 创建 `materializing` 记录 | 原生责任已持久化，但 provider session 尚未成立。assignment `01a0e712-d32c-7280-ad28-56af2cc2bb70`，agent `01a0e712-d32c-7280-ad28-56b1dd938bf8`。 |
| 08:12:49.367—08:12:50.845 | PR #19 worktree 记为 active；`physical/01a0e712-e265-7c52-9edf-c53926f12176/session.json` 仍 `starting`、`native_session_id=null`；对应 native home 出现配置文件，但无 Pi JSONL | 物化已过 worktree 建立，停在原生 session 建立/登记边界。`provider_sessions` 和该 agent 的 `turns` 均为空。 |
| 08:12:50.859 | 08 Sheet `run.json` 为 `cancelled`，`runner_exit_code=-15` | 停止操作结束了来源执行；当前证据支持物化被停机中断。不能从缺少末段日志判定 `sessions.start` 内部的精确指令位置。 |
| 08:19 冻结→09 接续 | 08 冻结 DB 与 09 当前 DB 中同一 assignment 仍 `materializing`；09 新恢复进程已执行并继续其它成员工作 | 09 没有对这条不完整责任做恢复或退休。 |
| 09:21:42→12:01:33 | PR #19 合并为 `a3ff57a`，其 `lifecycle/closed` 事件仍 pending；根 Issue #1 关闭、PR #26 合入，`main=3fb842a46362c6c676bb2e99f92453d46f8394d9` | 产品工作全关，但 PR #19 的物化状态及收件未结算。 |

这不是由 `blocked_groups=10` 推出的诊断。09 `status.json` 的 `delivery_closed=true`、`active_turns=0`、`pending_resets=0`、`pending_continuations=0`、`materializing_groups=1`，唯一 materializing assignment 正是已合并的 PR #19。continuation-03 实际使用 Docker bind mount 的 Braid binary SHA-256 `74739b9d…`，对应冻结源码 `attempt-09/continuation-03/generation/inputs/input-0008/braid-source-roles-v1.tar.gz`；宿主 worktree 下 `work/bin/braid` 的 `b9be6bc3…` 是被 mount 覆盖的文件，不能据它解释当前运行。08 源 binary 为 `4074f51e…`，其 PR 物化调用顺序与 09 冻结源码相同。

冻结源码的 PR 物化流程是 `begin_agent_assignment` 先消费 assign 并持久化 materializing，接着建立 worktree，再 `sessions.start(...).await`；只有返回后才 `complete_agent_assignment` 把 assignment 变 active，或在显式错误分支 `fail_agent_assignment` 变 blocked。08 的 SIGTERM 落在这几个边界之间，没有错误返回分支可执行。`session.json=starting` 是文件投影，不等于已登记 provider session；缺少 Pi JSONL 和 DB provider 行表示没有可由恢复器枚举的原生会话。08 `recovery-braid.log` 最后记录在 08:12:08，OTLP traces 最晚约 08:12:09、logs 收到 08:12:43；08:12:45—50 没有涵盖物化末段的 trace，故不能把 `sessions.start` 内哪一步被取消写成已证事实，也不能额外归咎 SQLite 锁或模型错误。

## 为什么 09 未自行收敛

09 冻结源码 `prepare_offline_resume` 处理已登记的 `provider_sessions`、中断的 turns 和 context reset，没有扫描无 provider session 的 materializing assignment。`provider_resume_candidates` 只取 `active/finalizing/blocked` 且 INNER JOIN `provider_sessions`；PR #19 两项条件都不满足。原 assign 已 consumed，普通 activation 不会重新创建它；后续直达收件受现存 materializing 责任挡住。PR #19 合并事件虽仍 pending，`prepare_work_item_closure` 对 materializing owner 直接返回 false，不变更它。当前 DB 的只读核对给出：该 PR 的 provider/turn 行数均为 0，原 assign consumed，合并 close pending，assignment 与 agent 均 materializing。

`execution_settled()` 保留 `materializing_groups=0` 的要求是正确的安全边界：一个正在启动的成员不能被当作已终止。这里缺的是**在已证明旧执行停止后，结算被中断的物化**。当前 `local_run.lifecycle=running`、外层 `run.json.phase=running`、`finished_at/result` 为空；生成进程 PID 509790、Braid PID 510021 仍存活。普通 pending events、wake batches 和 blocked groups 不是这次 `execution_settled` 的直接阻塞项。

## 最小修复与当前运行的影响

建议在 Braid 的离线恢复入口、取得 `runtime.lock` 且宿主明确证明旧执行环境已停止后，对 `materializing` 且无 provider session 的 assignment 做一次事务性结算，留下可审计的原因；不要改 `execution_settled()`，也不要直接清零计数。若工作项仍 OPEN，保留原成员身份与 worktree，结束不完整物化并重排 activation，使正常物化路径重试；若工作项已 CLOSED/MERGED，退休无原生会话的残留责任并结算关联关闭事件。重入需幂等，且不能把未确认停止的原生进程当作不存在。隔离 DB 副本应至少验证：08 冻结的 PR #19 恰好匹配一次，恢复后无孤儿 materializing；OPEN 分支仍会重试同一工作，不丢原始收件；MERGED 分支不创建新模型会话；其它 assignment 和 Git 状态不变。此处是修复判据，尚未实现或运行实验。

当前 03 已在执行，不能对它调用要求“旧执行已停止”的恢复入口，也不能热替换其已运行的 Rust 二进制。若要让原接续生成得到完成 receipt，需另行批准具体处置：先保留当前状态、受控停止并冻结工作区/DB，确认旧容器和 provider 写入者退出；用经隔离副本验证的修复版 Braid 做新的接续，并确认 `main` 树与原 `3fb842a4` 相同后才接受生成结果。现有上传监听 PID 82066 绑定 03 的 run.json，480 秒读取一次，只有 `result.status=completed` 才打包；停止 03 会令它看到非完成终态并退出，因此新接续还须明确接管单题打包和 `self_funded` journal 防重复。当前无 Sheet ZIP、`sheet-official` journal 或官网 run ID。此恢复不是获准自动开启第十次迭代，且不能在未给出处置清单前操作运行。

证据入口：08/09 Sheet 工作区各自 `.factory26/20260928-025746-66feadac/braid-state/{braid.sqlite3,status.json,origin.git}`，08 同目录 `physical/01a0e712-e265-7c52-9edf-c53926f12176/session.json`、`work/native-homes/pi-glm-fast-01a0e712-e268-71f1-a96c-b75185fd1201/`、`recovery-braid.log`、`telemetry.sqlite`；08 run `run.json`；09 `pre-stop-state.json`、`stop08-operation.json`；03 `generation/runs/pi-braid--hackathon--sheet-22730f82778f3a/run.json` 与本地 `sheet-hosted-on-completion.{py,log,pid}`。冻结源码关键位置：`src/group/pr_agent.rs` 物化；`src/store/mod.rs` 的 `prepare_offline_resume`、`provider_resume_candidates`、`assignment_candidates`、`prepare_work_item_closure`；`src/local.rs` 的 `execution_settled`。

## 修复与恢复已获授权

用户明确批准上述离线恢复修复及Sheet恢复/评分：先真实08数据库副本验证，再受控停止冻结03、确认写入停止、修复版接续并确认main树不变，接管单题self_funded评分。sheet_closeout_sol负责最小Braid修改及隔离验证；主Agent负责实际roles-v1候选构建与恢复集成。保留完成检查，不改应用/检查产物，不以手工SQL修活动数据库。第十次迭代完整新实验仍未获启动许可。
