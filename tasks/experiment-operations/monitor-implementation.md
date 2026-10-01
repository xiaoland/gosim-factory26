# 启动与监控实施回执

2026-10-02。用户授权“同意，开工，可以自有提交”。本分工修改 `competition.py`、`hosted_monitor.py`、`local_monitor.py`、`provider_liveness.py`，保留 Competition 原有未提交锁改动。没有提交，由主 Agent 集成。本次使用 ponytail lite，复用现有 scheduler、采集与通知，不建立监控服务或另一套状态库。

`Controller.launch(task_id=None)` 必须在 Controller 上下文内调用。未指定 task 时处理冻结 journal 内全部 task；snapshot/create/start 及必要只读 recover 位于同一比赛锁，status 独立读回位于锁外。已有 identity 和已启动 phase 复用原方法，不重新 snapshot 或创建替代 run。pending 无唯一恢复 identity 时保留现场并抛出诊断，包含已存 HTTP/detail。`launch-receipt.json` 保存开始、结束、请求 tasks、pending_before、最终 summary/pending；异常保存类型与原文，ApiError 另存 HTTP/detail。启动已成功而独立读回失败可从 summary 和 pending 区分，重入不会再启动该 run。返回值为既有 summary。新写请求的响应与错误另存 `write-receipts/`，避免 pending 清除后丢失原始 response 或 HTTP/detail。

官网新增 `--targets <JSON文件>`，接受数组或 `{ "targets": [...] }`，每项包含 `journal`（绝对目录）、`run_id`、`submission_id`。接收时从 journal 得到并核对 competition/task，远端 status 也核对 run/submission/task/competition。原 `--journal` 和自动发现入口保留。每轮重读 targets，空闲等待最多十秒；串行批次下载期间不能保证十秒墙钟接收。新 target 单独立即到期，不使旧 run 提前采样。旧 scheduler 的 `next`、liveness、notifications、done 保留；迁移存在 liveness 的 run 沿用原 next。新增 `run_next` 支持逐 run 到期。删去活动订阅不会静默抛弃它，已接受身份保留至终态；已接受 journal 替换 identity 会失败。

本地继续消费原 `--matrix` 的动态 runs，不再等待最多八分钟才重读。run.json 的 run_id、路径和 created_at 形成接收身份，matrix 路径也是身份的一部分。新增 run 首批单独采集，不提前重采原 run，活动目标移出 matrix 后仍保留至终态。

scheduler 的 `accepted[run_id]` 是权威接收记录。每项含 identity、accepted_at、first_batch（首批目录，尚未采集为 null）、last_batch、last_observed_at、last_successful_at、last_error；官网另记 last_status_successful_at，区分有效平台读回与附加工作区缺口。`monitor/accepted.json` 只发布可查询副本，含当前 collector 完整 host/boot/PID/birth identity。首批存在不代表采集成功；最近成功时间与错误独立呈现。`monitor/completion.json` 保存 completed/once/failed/interrupted、错误、collector、done、accepted 与 scheduler 路径。SIGTERM 转为可记录的中断；SIGKILL、断电和无法写盘不能保证退出回执。

provider terminal 加入真实官网 PASSED。通知签名仅规范化 monitor 批次导出前缀，原错误保留在 evidence；同相对路径、同故障内容可去重，原因内容或相对文件改变仍产生新签名。OS 通知仍是 best-effort，不保证 exactly-once 或人已读。

## 实际反馈

编译四个修改模块成功。按主 Agent 批准范围，用正式 `local_monitor --once` 消费 `runs/iteration13/local-rebuild-20261001/active-matrix.json` 的两条真实 finished run。新独占输出为 `runs/experiment-operations/monitor-readback/20261002-local-terminal/`：completion.status 为 completed，两条接收均有身份、首批与最近成功时间，collector 有完整 Darwin 进程身份，两个桌面通知退出码均为 0，human_seen 保持 unknown。未访问 Docker、凭据或远端 API。

`runs/experiment-operations/monitor-readback/20261002-terminal-records/terminal-readback.json` 记录真实 PASSED `23a11724c9f4`、CANCELLED `691028015e69` 原件经生产 assess/transition 后均为 terminal；没有构造或修改观察样本，没有发出这些分类回放通知。该目录的 targets/receiver/accepted 记录真实 PASSED journal `bd3c2e50b511` 的身份接收；此为本地解析反馈，不是官网 collector 首批成功。

未应用或替换现行 collector，未观察现行四项活跃 run，未进行收费运行。Controller 新 POST/恢复崩溃窗口、活跃采集中动态追加、跨批次同因通知去重及异常退出仍没有本次真实操作反馈；源码实现与编译不等于这些性质已验收。通知持久化窗口、导出文件集合原子性与 provider 活动是否代表语义进展仍未得到保证。
