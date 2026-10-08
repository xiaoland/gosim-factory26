# 原生执行登记与物理资源边界

当前源码不再使用内存或 PSI 压力控制启动、claim、输入发送或 run 接续。2026-10-05 用户授权删除共享资源门控；旧冻结包仍保留其原行为，新运行与恢复必须使用记录了新源码和二进制身份的制品。执行环境实际的内存、swap、pids限额和按 Braid session 的模型使用约束继续生效，取值以该run冻结配置及内核观察为准，不从历史run推导。删除软件门控不能保证单个工具命令不会触发 OOM。

`tooling/scripts/runtime_resources.py` 现在登记原生执行所有权、实施明确停止 fence，并提供 run-owner 的只读 cgroup 观察（memory 与 pids 的 current/max/events）及有界 `memory.reclaim` 请求。顶层 Pi、foreground/async 子 Agent 和 Bash 作业经过同一 launcher；它取得自己的进程组，保存 execution/start UUID、PID、boot ID、启动时刻、PGID 和父 start ID，再以同一 PID exec 实际程序。登记失败、身份冲突或已停止的 execution 不启动 payload，并保留具体错误。资源观察不参与启动准入；旧 reservation、recovery budget 和 resource-failed 标记不再参与决定，历史文件不删除。

登记与停止使用同一短期文件锁，锁外执行命令、等待或发送信号。锁文件沿用 `admission.lock` 名称以兼容既有停止入口；该名称不表示仍有资源准入。Node 的 `spawnManaged` 立即返回 ChildProcess，由调用方接 stdout、error、close；`waitManagedStartup` 异步等待 started 回执。等待仍有启动期限，但不再等待压力降低、调用 reclaim 或重放被资源拒绝的启动。

Braid 的 claim 与输入发送只检查真实原生 busy 状态和生命周期身份，不读取资源压力。资源触顶由执行侧保存原始样本，先回收已退出的自有子进程并尝试有界内存reclaim；重新观察仍触顶，或已出现OOM、进程分配失败时，run 保存具体原因并 fail-closed/fail-loudly，不能继续以 waiting/running 假装推进。单纯采集不可得保留具体错误，不构成启动准入或凭空证明资源耗尽。pids.current/max/events 与 memory 同等重要，pids限额包含线程；不能凭 RSS 或 idle 猜测杀掉模型、浏览器或工作树。

公共入口与资源监督器之间的停止契约是显式的：入口在启动 variant child/process-group 后，把实际的 `subprocess.Popen` 对象登记给监督器。监督器以该对象的 PID/PGID 执行一次 TERM，最多等待 3 秒后 KILL；入口对象缺失、已退出或信号失败都写入 `resource-exhausted.json`，不向自身发送 SIGTERM，也不把服务线程记错当作入口已结束。入口负责接收该失败并返回明确的 `resource_exhausted`；gateway/OTLP 是运行所需服务，不是压力处置候选。

孤儿回收与触顶补救是不同责任。Local创建使用Docker `--init`，公共程序入口在安装及启动服务前进入固定Tini subreaper，使Hosted无需依赖平台Docker参数也能回收其后代孤儿。两环境消费同一入口；Linux实际浏览器open/snapshot/close已取得回收证据，Hosted及长时间重复使用仍以独立验收原件为准。Python仍只wait自己持有的Popen，不增加 `waitpid(-1)` 回收线程或忽略SIGCHLD。仍存活的父进程须等待自己的已退出子进程，不能依赖init替代；浏览器工具管理会话复用与close，后台工具管理自有进程结束，variant决定活动会话及测试并行，不由Lab增加全局并发gate。Tini的实现与subreaper语义见[官方说明](https://github.com/krallin/tini#subreaping)。

Local 和 Hosted 的容器内 `ResourceSupervisor` 拥有执行 namespace 的采样。保护线程先读取轻量 cgroup 限额及事件，再提交采样请求；唯一采样 worker 串行执行 `/proc` 扫描、PSS 和证据落盘。最多保留一个待处理请求，合并普通请求，优先保留触顶及终态原因；不会因重采样排队阻塞保护判断。保护观察记录实际间隔和调度延迟，采样记录请求时间、排队延迟、合并数量、采样起止、读取耗时、线程 CPU 和包含落盘的总耗时。关闭只等待有界时间，未能完成 final 会明确记录 incomplete。文件系统写入和内核调度仍可能造成延迟，不能宣称硬实时保护。

共享 `ResourceEvidence` 保存 cgroup 内存分类、peak、PSI、CPU/I/O 和进程身份、RSS及原始CPU/I/O计数。计数仅在读取前后出生身份一致时关联，读取失败保留错误，不填零。PSS通常每10秒补充一次，每次最多12个：按作用域选6个RSS大户，其余按最久未尝试轮转。覆盖摘要区分符合范围、尝试、成功、未尝试及最近成功时间，身份变化和权限错误保留原件。进程明细上限256，覆盖新鲜度条目超过256时明确报告遗漏。PSS、RSS和cgroup记账不能强行配平。

观察到新进程、进程消失、memory.current或peak相邻增长至少64MiB、内核内存/pids事件变化、触顶或终态时补充明细。它们是观测触发条件，不参与启动准入。普通日志保留两个31MiB段；异常及其前3个样本另保留16MiB日志，触顶/内核事件/final使用独立16MiB关键日志，避免普通启动活动耗尽关键日志。每个事件日志到上限后保留capped标记及丢弃计数，不无限增长。普通轮转记录丢弃的时间边界。近期样本和启动登记可以保留消失进程的最后证据，但不能保证捕获两次采样间的短命进程、OOM前PSS或内核受害者。

外部 OTLP receiver 只负责运输，不替代容器采样；Hosted内部receiver关闭重复资源采样，独立receiver保留默认采样。`resource-latest.json`是小型cgroup与采样时间快照，进程原件在归档日志中。在线回收保留采样worker及失败摘要；完整project/workspace归档拥有资源日志和登记。采集失败保存具体错误，不阻止新执行。

[resource_attribution.py](../../tooling/scripts/resource_attribution.py)只读同一执行归档，按boot ID、PID/starttime和可用namespace身份连接原生execution/start/parent_start登记，再以native-state和Braid manifest/status连接会话、Issue/PR及上下文来源。工具作业只输出manifest的身份、toolCallId和生命周期字段，不输出命令或环境。直接出生身份关联与当前样本祖先推断分别标记；旧登记缺namespace时明确降低证据强度。session/工作项来自保存的绑定证据，不能把最终manifest的turn列表当作历史瞬间的活动turn；证据不足保留unknown/ambiguous。跨恢复不相减不同boot或namespace的单调计数；CPU/I/O速率使用同一出生身份的原始计数差和实际采样时间差，缺值与计数重置单列。

## 静止释放、停止与接续

原生 RPC 的 `get_state.data.managed_state` 区分 quiescent、busy 和 unknown，包含 turn、有限作业、待接收结果和服务。OPEN 成员没有待投递输入/reset 且原生确认静止时，Braid 可以释放物理执行；逻辑会话、原生历史、指派和 clone 保留。真实输入或必要恢复才唤醒它。这属于正常生命周期，不是资源压力减载。

父 Pi 的退出和 owned execution 的停止分别保存。非零退出或 SIGKILL 不自动证明子作业已停止。关闭先在登记使用的同一锁下设置 execution fence，阻止新作业，再按 birth identity 和拥有的进程组清理。Pi 已退出时由 `native-managed.mjs cleanup` 离线完成。信号、权限和身份冲突保留原始错误，停止不明时不产生第二个写者。

停止回执覆盖已登记进程组及继承 execution/start marker 的后代。主动清除 marker 并脱组的任意 shell 可能超出范围，本机制没有内核历史追踪能力。归属不明返回 unknown；跨容器恢复仍须证明来源生成容器停止，Docker 暂停或新 volume 的锁不能替代该事实。连续异常恢复仍有生命周期边界；门控删除不改变 stop proof、模型重试、审批、费用或 session 数量约束。

Portless proxy 在成员启动前以前台子进程启动，清除成员 execution/start 标记，由 run 入口保留实际 Popen。有限作业清理不拥有它。入口通过 `X-Portless: 1` 确认就绪，结束时发送信号并等待实际子进程退出；已有监听者或旧 PID 文件不能替代当前 run 的所有权证明。

源码与制品证据归 [timeout-retry packet](../../tasks/iteration14/timeout-retry/packet.md)。部署时恢复 ZIP 的 executable mode 或按安装 manifest 实施等价权限，不能把 ZIP 中已正确记录的 executable 文件用默认 0644 抽取后直接运行。
