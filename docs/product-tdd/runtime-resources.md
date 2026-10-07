# 原生执行登记与物理资源边界

当前源码不再使用内存或 PSI 压力控制启动、claim、输入发送或 run 接续。2026-10-05 用户授权删除共享资源门控；旧冻结包仍保留其原行为，新运行与恢复必须使用记录了新源码和二进制身份的制品。执行环境实际的内存、swap、pids限额和按 Braid session 的模型使用约束继续生效，取值以该run冻结配置及内核观察为准，不从历史run推导。删除软件门控不能保证单个工具命令不会触发 OOM。

`scripts/runtime_resources.py` 现在登记原生执行所有权、实施明确停止 fence，并提供 run-owner 的只读 cgroup 观察（memory 与 pids 的 current/max/events）及有界 `memory.reclaim` 请求。顶层 Pi、foreground/async 子 Agent 和 Bash 作业经过同一 launcher；它取得自己的进程组，保存 execution/start UUID、PID、boot ID、启动时刻、PGID 和父 start ID，再以同一 PID exec 实际程序。登记失败、身份冲突或已停止的 execution 不启动 payload，并保留具体错误。资源观察不参与启动准入；旧 reservation、recovery budget 和 resource-failed 标记不再参与决定，历史文件不删除。

登记与停止使用同一短期文件锁，锁外执行命令、等待或发送信号。锁文件沿用 `admission.lock` 名称以兼容既有停止入口；该名称不表示仍有资源准入。Node 的 `spawnManaged` 立即返回 ChildProcess，由调用方接 stdout、error、close；`waitManagedStartup` 异步等待 started 回执。等待仍有启动期限，但不再等待压力降低、调用 reclaim 或重放被资源拒绝的启动。

Braid 的 claim 与输入发送只检查真实原生 busy 状态和生命周期身份，不读取资源压力。资源触顶由执行侧保存原始样本，先回收已退出的自有子进程并尝试有界内存reclaim；重新观察仍触顶，或已出现OOM、进程分配失败时，run 保存具体原因并 fail-closed/fail-loudly，不能继续以 waiting/running 假装推进。单纯采集不可得保留具体错误，不构成启动准入或凭空证明资源耗尽。pids.current/max/events 与 memory 同等重要，pids限额包含线程；不能凭 RSS 或 idle 猜测杀掉模型、浏览器或工作树。

公共入口与资源监督器之间的停止契约是显式的：入口在启动 variant child/process-group 后，把实际的 `subprocess.Popen` 对象登记给监督器。监督器以该对象的 PID/PGID 执行一次 TERM，最多等待 3 秒后 KILL；入口对象缺失、已退出或信号失败都写入 `resource-exhausted.json`，不向自身发送 SIGTERM，也不把服务线程记错当作入口已结束。入口负责接收该失败并返回明确的 `resource_exhausted`；gateway/OTLP 是运行所需服务，不是压力处置候选。

孤儿回收与触顶补救是不同责任。Local创建使用Docker `--init`，公共程序入口在安装及启动服务前进入固定Tini subreaper，使Hosted无需依赖平台Docker参数也能回收其后代孤儿。两环境消费同一入口；Linux实际浏览器open/snapshot/close已取得回收证据，Hosted及长时间重复使用仍以独立验收原件为准。Python仍只wait自己持有的Popen，不增加 `waitpid(-1)` 回收线程或忽略SIGCHLD。仍存活的父进程须等待自己的已退出子进程，不能依赖init替代；浏览器工具管理会话复用与close，后台工具管理自有进程结束，variant决定活动会话及测试并行，不由Lab增加全局并发gate。Tini的实现与subreaper语义见[官方说明](https://github.com/krallin/tini#subreaping)。

既有 collector 继续保存 cgroup、内存、PSI 和进程证据，`resource-latest.json` 只是观测快照。采集缺失不阻止新执行。既有 native-state 与 evidence-capture 回执继续用于判断运行和快照行为；没有增加采集循环。

## 静止释放、停止与接续

原生 RPC 的 `get_state.data.managed_state` 区分 quiescent、busy 和 unknown，包含 turn、有限作业、待接收结果和服务。OPEN 成员没有待投递输入/reset 且原生确认静止时，Braid 可以释放物理执行；逻辑会话、原生历史、指派和 clone 保留。真实输入或必要恢复才唤醒它。这属于正常生命周期，不是资源压力减载。

父 Pi 的退出和 owned execution 的停止分别保存。非零退出或 SIGKILL 不自动证明子作业已停止。关闭先在登记使用的同一锁下设置 execution fence，阻止新作业，再按 birth identity 和拥有的进程组清理。Pi 已退出时由 `native-managed.mjs cleanup` 离线完成。信号、权限和身份冲突保留原始错误，停止不明时不产生第二个写者。

停止回执覆盖已登记进程组及继承 execution/start marker 的后代。主动清除 marker 并脱组的任意 shell 可能超出范围，本机制没有内核历史追踪能力。归属不明返回 unknown；跨容器恢复仍须证明来源生成容器停止，Docker 暂停或新 volume 的锁不能替代该事实。连续异常恢复仍有生命周期边界；门控删除不改变 stop proof、模型重试、审批、费用或 session 数量约束。

Portless proxy 在成员启动前以前台子进程启动，清除成员 execution/start 标记，由 run 入口保留实际 Popen。有限作业清理不拥有它。入口通过 `X-Portless: 1` 确认就绪，结束时发送信号并等待实际子进程退出；已有监听者或旧 PID 文件不能替代当前 run 的所有权证明。

源码与制品证据归 [timeout-retry packet](../../tasks/iteration14/timeout-retry/packet.md)。部署时恢复 ZIP 的 executable mode 或按安装 manifest 实施等价权限，不能把 ZIP 中已正确记录的 executable 文件用默认 0644 抽取后直接运行。
