# 离线恢复

用户授权：2026-09-28“继续改进基础设施，打通断点恢复”。
范围：Braid 的旧输入重放与冷恢复、Factory 保留工作区接线；不扩展到 Codex 消息收据或无关精简。

宿主显式 `braid local REQUEST --offline-resume` 表示来源执行环境已停止，旧执行不再访问该状态或工作文件。
Braid 获取原 runtime.lock，核对原请求身份与材料后，由 Store 撤销旧 CLI 身份并准备遗留执行；既有 provider IDs 成为本次进程内的停止事实。
普通启动不隐式作这个断言，新启动的 provider 也不继承此停止事实。
通知未完成但来源执行已被终止的 reset 保留恢复记录，不能伪造已经完成通知。

实现分工：主 Agent 负责 CLI/local/config/SessionManager 和恢复载荷；replay_queue_fix 负责 Store/Actor 内离线准备、unknown 重放与既有损坏队列修复。
不在 Factory 中改 SQLite，不清除与失联无关的真实 blocked 错误。

用户随后明确要求启动官网运行以完成验收。使用已取消 Sheet 3445926a1142 的真实未完成快照，在官网新 self_funded run 中接续；保留原需求、模型材料和工作项，只替换修复后的 Braid 与恢复入口。
WSL 只编译 Linux 二进制，不启动重复本地生成；不勾选参赛，不用 official_evaluation，不改原始快照。完成条件是恢复后有真实输入与模型行为、无空批次循环，交付并进入完整官方评分。


## 冻结与启动

Linux release 编译成功。制品 `runs/e20260928-offline-resume/agent.zip`，SHA256 `fe0215add47fb35f71513fc5bd447ad6d5220fb8dc6a65735fbcbe19c3fa7ba3`。
Braid 二进制 SHA256 `53a2d58213b053d8cc3acb97c388c8db6e10e483c1ac2639c92eda1a9fad6a1a`，来源源码 tar、快照与模型配置均保存在该目录。
官方已只读确认来源 run 为 CANCELLED。新 journal 位于 `runs/e20260928-offline-resume/official`；控制器使用原 journal、启动后前 10 分钟 180 秒、随后 480 秒的周期。不得重复上传或创建，不确定写入按 pending 核对。

官网身份：submission `6a2d7c30464c`，run `dd3bda66bcb3`，billing_mode=self_funded。
监控首轮已确认 deploy_agent=completed、start_agent=running、run_tests=pending；完整验收尚未结束。
`offline_resume_monitor`（gpt-5.6-luna / low）通过现有脚本按启动后前 10 分钟每 3 分钟、随后每 8 分钟的间隔采集，终态后核对工作区；源控制器继续使用同一 journal，不另起 run。

监控进程的持续运行需脱离工具会话进程组。此前纯工具会话/后台 shell 的监控曾消失且无终态记录；当前使用 subprocess.Popen(start_new_session=True) 启动独立只读监控，PID 65250，stdout/stderr 保存在 runs/e20260928-offline-resume/monitor-process.log，scheduler 已更新且独立 ps 确认存活。原 run-all 控制器 PID 59034 未中断。

## 2026-09-28 实际冷恢复中间证据

快照：runs/e20260928-offline-resume/acceptance-check/20260928T011601Z/dd3bda66bcb3。
恢复启动后，原 Issue #6 已关闭，新 PR #12 已合并；根 Issue #1 与集成 PR #1 仍开放。
数据库 active_turns=4、blocked_groups=0；四个原 provider 记录了恢复。
以 2026-09-28T00:39:04 为界，新 turn 的非空 batch_id 对应零 wake_batch_events 的数量为 0。
新 turn 按用途/状态：context_reset_notice completed=10/running=1，terminal_contact completed=55/running=1，wake_batch completed=26/running=2。
这支持冷恢复后真实工作继续、未复现空批次循环；55 次有输入的 contact 不据此全部判为无效。
离线恢复记录与新的原生工具调用均在快照中。最终交付和官方完整评分仍待完成，不能宣告全部验收通过。

用户已调整完成条件为冷恢复平稳运行，不需完整交付；上述真实续进满足该范围。按用户授权取消 dd3bda66bcb3，远端确认 CANCELLED，controller/monitor 已停止；原始回执 runs/e20260928-offline-resume/user-stop.json。原完整评分要求由此取代，本项不再等待评分。
