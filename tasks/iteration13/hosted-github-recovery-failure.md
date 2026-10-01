# 官网 GitHub 接续失败：SIGKILL 与容器 OOM 证据

2026-10-01，对官网 run `377afa346c92` 的既有终态保全做只读诊断。此次新增设施确实取得了历史失败所缺的两类事实：当前 attempt 的 Pi 子进程被 SIGKILL 终止，以及同一容器 cgroup 的 OOM 计数增长。PID 291 在第二次 OOM 计数增长窗口内由存活状态变为僵尸，随后 Braid 的真实 wait 返回 `signal: 9 (SIGKILL)`。这强烈支持 PID 291 是此次 OOM 的受害进程；仍没有内核 victim PID 或信号发送者证据，不能把关联写成已直接证明的因果链。

本次没有启动采集循环、模型、恢复或收费请求，没有修改运行代码，也没有操作仍在运行的 Sheet `691028015e69` 或其 collector。只消费原 hosted_monitor 已保全的终态 workspace，未展开原生 rollout 正文。

## 来源与终态

原始入口是 [终态 collection](../../runs/iteration13/hosted-recovery-20261001/monitor/20261001T101157.239125Z/377afa346c92/collection.json)、[原始 status](../../runs/iteration13/hosted-recovery-20261001/monitor/20261001T101157.239125Z/377afa346c92/status.json) 和同目录 `workspace.zip`。ZIP 为 284,876,119 bytes，SHA256 为 `88f2c0c85ffde65ea7fa5db8adb1b96c8692bd2188383f6e85d584177abb486b`。collection 没有保全错误；本次读取保留了选定条目的 ZIP CRC 与内容 SHA，见 [消费回执](../../runs/iteration13/hosted-recovery-20261001/github-failure-analysis/consumption-receipt.json)。终态保全未同时取得平台终端 stdout/stderr 的原始 HTTP 回执，不能把保存的启动日志当成终态终端日志。

| 字段 | 原始事实 |
| --- | --- |
| 官网 run / submission | `377afa346c92` / `66774c63c885` |
| 名称 / 题目 | `e20261001-01--flash-root--github--hosted-recovery-g03` / `hackathon--github` |
| 当前 attempt | `0fde190635764f079fc17e043328e7cc` |
| 恢复来源 run | `346bc3b51b09` |
| 复用的 Braid run | `20261001-052115-e45f4278`；不以它单独区分新旧执行 |
| 实际执行的 Braid SHA256 | `a8afac46d2a8268dc3e7e163e673220216caaeee892b6d3af01c743b70144414` |
| 平台终态 | `FAILED`；`deploy_agent=completed`、`start_agent=failed`、`run_tests=pending` |
| 评测 | `evaluation_started_at=null`，`tests=[]`，通过和失败数均为 0；平台 score 0 不是有效应用评分 |
| 费用模式 | `self_funded`；本轮是非参赛官网恢复 |
| 费用原字段 | `token_cost_usd=17.136155`，但 `token_cost_currency=CNY`，`settled_at=null`；按原币种暂记 17.136155 CNY，不解释成 USD 或最终结算 |
| 消耗 / 时长原字段 | `token_count=67750296`，`run_duration_seconds=2465` |

API 原时间为 `created_at=2026-10-01T09:24:50.830702`、`started_at=2026-10-01T09:25:00.509841`、`finished_at=2026-10-01T10:07:23.187847`，这些字符串没有时区后缀。下文明确带 `Z` 的事件时间来自容器 realtime 与 Braid 日志，不给 API 原字段补写时区。API 原始失败原因只说 `/workspace/submission/main.py` 返回 exit 1。

当前 attempt 文件中的平台 run ID 是 `null`，原件明确说明平台 ID 未暴露给入口；本次通过该官网 run 的终态 ZIP 和外部 journal 绑定，未把导入历史当作当前执行。新 `process-evidence/attempt.json`、新 Braid spawn/wait、当前二进制回执和当前 result 互相对应。旧 result 已分离到恢复来源路径。[定向提取目录](../../runs/iteration13/hosted-recovery-20261001/github-failure-analysis/current-attempt/) 保存了这些原件。

## 新启动、退出与清理的先后关系

Braid 是 PID 266，PPid/PGID 都为 82，`starttime=88585071`。PR4 的新 Pi 是 PID 291，PPid 266、PGID 82、`starttime=88585077`；它接续 native session `01a0f62d-a0af-73d9-a6c0-23d9855f9a68`。它与采集器均看到 cgroup `0::/`，PID namespace inode 为 `4026533052`、cgroup namespace inode 为 `4026533053`。进程 birth identity 与 namespace 用于排除同 PID 重用。

| UTC 事件时间 | 当前执行的原始记录 |
| --- | --- |
| 09:25:29.949371Z | support 记录 Braid PID 266 spawn；紧接着记录 wait 请求 |
| 09:25:30.008317Z | Braid 记录 PR4 Pi PID 291 启动及 `/proc` identity |
| 10:06:15.005990Z | PR4 worker terminal 报告 provider disconnected |
| 10:06:15.108801Z | Braid 对 PID 291 记录 `stdin-eof-shutdown` wait 请求，原 timeout 180 秒 |
| 10:06:15.108924Z | wait 返回 `signal: 9 (SIGKILL)`；间隔仅 0.123 ms，没有等待到 shutdown timeout |
| 10:06:15.709946Z | Braid 记录 blocked：`native teardown could not be proven: session failed: Pi exited with signal: 9 (SIGKILL)` |
| 10:06:16.416873Z | support wait 收到 Braid exit code 1，signal 为 null |
| 10:06:16.505869Z | 第一个 support workspace cleanup 信号请求，此时 Braid 已退出 |
| 10:06:17.333802Z–10:06:17.853749Z | support 向 collector PID 264 请求 TERM，再 wait 到 exit 0 |

原件见 [operations.jsonl](../../runs/iteration13/hosted-recovery-20261001/github-failure-analysis/current-attempt/process-evidence/operations.jsonl) 和 [recovery-braid.log](../../runs/iteration13/hosted-recovery-20261001/github-failure-analysis/current-attempt/recovery-braid.log)；[生命周期摘要](../../runs/iteration13/hosted-recovery-20261001/github-failure-analysis/braid-lifecycle.json) 保留原行号。去除 ANSI 的派生日志中，PID 291 的启动在第 9–11 行，wait 在第 265–266 行，最终 blocked 在第 276–277 行。

support 共记录 31 次 signal 请求，全部为 SIGTERM，没有 SIGKILL，也没有以 PID 291 为目标的请求。已记录的共享清理晚于该 Pi 的退出，不能解释最先发生的 SIGKILL。Pi owner 的释放日志只表示对象释放事实，不能证明发送过信号；PID 291 的释放记录发生在 wait 之后。其它 Pi 287 和 344 的 wait 返回 success 0；PID 12471 只有释放事实，没有最终 wait，不能据此追加一个已证 SIGKILL。未记录的工具命令或宿主信号路径仍不可排除。

当前 result 保留 root issue 1 为 OPEN、delivery commit `e9e24e029c1603aa9394e3fbad701c5cd9245527`。这次属于生成中断，尚未进入官网评测。

## cgroup OOM 与 PID 291 的关联

可读的 cgroup v2 是 `/sys/fs/cgroup`，从基线到末端均为同一设备/inode `29/1776942`。基线 `09:25:29.571085Z` 中 `memory.max=2147483648`（2 GiB），`memory.current=1248821248`，`memory.events` 和 `.local` 的 `max/oom/oom_kill` 都为 0。末端 `10:06:17.368462Z` 两份 events 都变为 `max=16984, oom=7, oom_kill=2`，`memory.peak=2147528704`，swap current/peak 均为 0，`memory.oom.group=0`。pids limit 没有命中。

因此已证这个容器 cgroup 发生 OOM 事件，并累计计入两个被 OOM killer 杀死的进程。`oom_kill` 的语义本身也包括该 cgroup 进程被其它范围的 OOM killer 杀死；结合 `.local` OOM、limit 命中与 current 逼近 2 GiB，本地内存限额压力是强支持的解释。计数没有 victim PID，不能单靠它指定哪一个进程。[内核 cgroup v2 字段说明](https://docs.kernel.org/admin-guide/cgroup-v2.html)解释这些计数的范围。

两次 `oom_kill` 增量如下。边界使用前一行的采样开始到后一行的写出时间，保守包含读取过程；proc 与 counter 不是原子快照，不把 JSONL 写出时间冒充内核事件时刻。

| 增量窗口（UTC） | 原始变化与观察 |
| --- | --- |
| 09:34:48.305391Z–09:34:50.814511Z | `oom 0→1, oom_kill 0→1`。PID 291 同 birth identity 仍存活，故不能把第一次 OOM 算作它的最终死亡 |
| 10:06:11.616253Z–10:06:14.409900Z | `oom 1→7, oom_kill 1→2`。PID 291 从 S、RSS 75124 pages 变为 Z、RSS 0；随后 wait 确认 signal 9 |

第二个窗口直接来自当前 [resources.jsonl](../../runs/iteration13/hosted-recovery-20261001/github-failure-analysis/current-attempt/process-evidence/resources.jsonl) 第 339/340 行：前一行 current 为 `2147270656` bytes、events `max=15901,oom=1,oom_kill=1`；后一行 current 为 `1928478720` bytes、events `max=16984,oom=7,oom_kill=2`。两行的 PID 291 starttime 都为 `88585077`，后一行 Z 状态再与真实 wait 相接。[OOM 窗口与 PID 明细](../../runs/iteration13/hosted-recovery-20261001/github-failure-analysis/oom-windows-and-pid291.json)保留了两侧样本。

目前可区分“同一容器确实发生 OOM”和“当前 Pi 确实被 SIGKILL 终止”，并得到两者很强的时间与身份关联。尚缺宿主内核 OOM victim 记录或信号 trace，`host_signal_sender=unavailable`；不能确定发送者、直接证明 PID 291 被 OOM killer 选中，或反向解释过去的官网失败。最后一个 sample 也没有被单独用作死因。

## 末端内存组成与设施覆盖

第 339 行可见 135 个 PID，其中 43 个存活且 RSS 非零：4 个 Pi（PID 287/291/344/12471，RSS 合计约 1002 MiB），23 个其它 Node 进程（RSS 合计约 1974 MiB），没有按 exe/comm 识别到存活的 Chrome/Chromium/Firefox。PR4/backend 中同时存在一个 Vitest 主进程和 15 个 worker；PR4/frontend 另有 Node，PR5/backend 和 backend/e2e 也有 Node。仅据这份采样已能观察到多工作树应用验证并行，无需读取 rollout 推测工具命令。明细见 [末端组成](../../runs/iteration13/hosted-recovery-20261001/github-failure-analysis/failure-memory-composition.json)。

这些 RSS 合计重复包含共享页，且各 PID 的读数不是同时取得，不能与 cgroup current 直接相加或据此决定资源扩容值。当前没有采集 `memory.stat`，无法拆开 anonymous、file cache 和 kernel charge。后续若要在降低验证并发与增加官网内存之间选择，现有事实支持先核对多工作树测试的并发数量和 Vitest worker 数；不能把四个 Pi 本身直接认定为全部内存压力来源。本次没有应用这个建议或重启实验。

collector 保存 1181 个样本，跨度 2447.797 秒，末端覆盖到 Braid 退出与 cleanup。实际 resources 流量为 61,482,991 bytes、平均约 24.53 KiB/s；按本次平均速率，两段共 62 MiB 可保留约 43.14 分钟。发生一次轮转，本次之前的段仍在，没有丢弃故障窗口；未来长运行会轮转掉早期历史，不能沿用隔离小进程验证的速率预计 90 分钟完整覆盖。

`resource-status` 的 `write_succeeded=true`、`capability_errors={}`、`capped=false`，最多可见 145 PID，小于 256 上限，详细 PID 没有因数量被省略。采样间隔中位数约 2.027 秒，最大约 2.900 秒。但零 capability errors 不等于所有 `/proc` 字段都无错误：classification 原件保留 26,689 次 `ENOENT=2`，另有 26,681 条分类错误受每样本错误条数上限省略，主要涉及消失或僵尸进程的路径读取；这不等于省略了同数目的 PID。PID 291 的关键 stat 和 cgroup 原始计数可读。见 [采集覆盖摘要](../../runs/iteration13/hosted-recovery-20261001/github-failure-analysis/collection-health-summary.json)。

本次设施达到了“区分当前进程 SIGKILL、容器 OOM、我方实际清理先后”的目标，尚不具备宿主 sender/victim 归因能力。后续恢复或资源调整由主任务决定；这里不把根因关联升级成自动收费重试依据。
