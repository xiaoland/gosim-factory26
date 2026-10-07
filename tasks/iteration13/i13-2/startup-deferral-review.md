# I13-2 启动资源暂缓的独立复核

2026-10-01。结论是需要调整资源暂缓的传播与退出语义，先保留现有 PSI 判据。有效资源样本拒绝启动时，已有义务应留在同一次 Braid 执行内等待下一轮资源观察；等待不代表已经取得进展，也不等于所有工作都无法自动接续。实现继续复用现有两秒循环，不需要新增调度器、持久资源队列或启动等待服务。

## 原始事实与推断

[GitHub 日志](../../../runs/iteration13/i13-2-20261001/first-continuation/github/recovery-braid.log)第3至9行中，`memory.current` 约为 2,460–2,480 MB，限制为 4,294,967,296 bytes，`oom_kill=0`；PSI some/full 的 avg10 从 8.11 降到 5.43，total 始终为 6,834,330 微秒。[Sheet 日志](../../../runs/iteration13/i13-2-20261001/first-continuation/sheet/recovery-braid.log)对应窗口中，charge 约为 2,130–2,140 MB，`oom_kill=0`；avg10 从 30 降到 20.12，full total 始终为 13,055,043 微秒，some total 始终为 13,060,447 微秒。这里 MB 按十进制说明，避免把原始 bytes 误写为 GiB。

两份日志都在数秒后记录 `provider recovery returned an error` 并终态 blocked。[退出读回](../../../runs/iteration13/i13-2-20261001/first-continuation/failure-readback.json)确认两容器 ExitCode=1、OOMKilled=false，且保存的 `template/.arc/stdout.log` 显示材料刷新完成后，Braid 返回1被恢复入口向外传播。上述窗口没有新增 OOM，也没有新的 PSI 停顿累计；它支持“历史停顿的平均值正在衰减”，不能证明高 PSI 从未发生或原阈值错误。安装、解压、材料刷新可能贡献了此前停顿，但现有窗口没有直接证明具体生产者。已查日志没有成功模型启动事实，仍不能单凭缺少该日志断言绝无模型调用。

[worker](../../../sources/braid/src/group/worker.rs)把 resume 的错误转成字符串，随后把 deferred 计入 health.error，并在暂不能执行时报告 `can_progress=false`；[local](../../../sources/braid/src/local.rs)将“全部不能立即推进且存在错误”直接升级为整轮 blocked。这是本次已观察到的失败路径。`SessionError::Deferred` 同时还用于 Unknown 恢复次数已用尽、原生 busy、超时或断连；把全部 Deferred 改成无限等待会扩大本次修复。

## 最小修复边界

在现有 SessionError 到 worker/health 的边界保留一个结构化的“资源暂缓、可随资源变化重试”原因即可。适用的是已确认的资源准入拒绝，不靠错误字符串匹配，不顺便建立通用重试分类框架。资源事实与原错误继续可见；能力缺失、传输失败和恢复次数用尽不能仅因共用 Deferred 就自动获得相同等待语义。

| 入口 | 资源拒绝后必须保留的状态 |
| --- | --- |
| 新 assignment | 复用现有 `defer_agent_assignment`：保留同一 materializing assignment、member、clone 和激活输入，重试不创建新代次。 |
| 已有 provider resume | 保留 provider/native 身份、工作树及原 idle/unknown 义务；旧执行停止证明继续有效。尚未成功恢复时不增加 Unknown 恢复次数，不将 provider 因资源压力永久 block。 |
| sleeping 联系 | 原联系恢复为可投递义务，保留 sleeping 身份，不能把启动拒绝写成已送达。 |
| Context reset | 保留同一个 materializing reset、来源事件和 continuation；资源拒绝时不标 applied/failed，也不重新请求一个 reset。 |
| 已 claim 但输入未接受的 turn | 沿现有 `defer_unstarted_turn` 或 reset notice 的 defer 路径释放执行 claim、保留可重试输入和拒绝事实；没有 provider turn ID 时不能记作已执行，也不能丢失原输入。 |

`last_resume_error`、`last_resume_failed_at` 可以继续保存本次真实拒绝供诊断，不能据字段非空决定整轮失败；成功恢复才沿现有 `record_provider_resume` 清除它们。等待标记须来自当前仍需重试的义务，在准入成功或义务撤销后清除，不能成为永久闩锁。同一 group 里有多个成员时，要保留任何有效的资源等待，不能由最后一个错误覆盖掉另一成员的重试机会。

health 应能表达“现在没有执行，但仍在等资源”；`can_progress` 继续如实为 false。local 聚合只要仍有这种自动重试义务，就保持运行并接受既有取消或外层执行期限，沿现有两秒循环重新观察。资源准入仍立即拒绝原生子调用，避免父进程持有资源等待子进程的死锁。真正的 stop-proof unknown 仍走 fatal stop；所有剩余义务确实需要新外部输入或人工改变条件时，原有可恢复 blocked 语义保留。不要用资源等待放宽这些边界。

## 必要的验收与重接续选择

本次失败日志已证明资源拒绝入口真实可达；需要补上的证据是拒绝后 Braid 保持存活、义务不丢失，以及资源恢复后同一义务获准执行。编译覆盖类型与调用点。既有 Linux 操作容器可在保全的真实准备副本上，用真实 collector、helper 和 Braid CLI 执行无网络操作，核对实际数据库记录与进程生命周期；仅调用 helper 或 Pi get_state 成功不能验收 worker/local 的等待语义。若实际操作没有自然遇到资源暂缓，就明确该分支未被此次操作覆盖，不伪造 PSI 样本、不制造 OOM 负载或另造 mock 场景。最终在一次必要且已授权的接续中观察 deferred → 保持运行 → 准入成功和对应输入/reset 被消费，取得启动闭环反馈即可，不必等评分。

建议本轮采用修正后新冻结的 attempt，继续保留首个失败 attempt 原件。[恢复入口](../../../tooling/linux/recover_completed.py)明确拒绝既有 run 目录，[远端工作区](../../../lab/arc_bench/docker_workspace.py)也明确拒绝复用既有 transport/volume。直接再次启动旧容器会重走恢复入口；绕过入口只调用 Braid 则还需重新承接 collector、共享代理、环境、归档、交付和 controller 身份，已经超出一次传输优化。本轮不值得为它增加第二条接续入口。若现有文件传输能力能复用远端已校验的不可变输入，可以仅传改变的制品后组装并校验一个新包；这不改变新冻结包、新 attempt 和旧现场保全的要求，也不要求开发新的增量传输机制。

本次独立工作仅阅读代码与既有日志并保存本文，未改源码、未运行测试、未启动模型或远端执行。
