# I13-2 的内存压力与原生执行

I13-2 在同一 run 内共享内存压力和进程启动准入。Braid 继续拥有工作项、输入队列和逻辑会话；Pi 原生接入拥有工具、内部子 Agent、后台作业及其结果。资源控制不读取任务内容，不选择模型，也不解释 PBB 的业务结果。实际部署与运行验收以 [I13-2 packet](../../tasks/iteration13/i13-2/packet.md) 为准，旧冻结包不随源码变化。

既有 OTLP collector 每两秒保存 cgroup v2 的内存、压力和进程证据，并原子发布 `process-evidence/resource-latest.json`。`scripts/runtime_resources.py` 在 run 的 `process-control/` 使用短期文件锁串行决定启动；锁外才执行命令、等待结束或发送信号。它拥有启动登记和预算，不建立第二份工具作业表。

## 启动与压力反馈

所有启用此机制的顶层 Pi、foreground/async 子 Agent 和 Bash 作业都经过同一 Python launcher。launcher 先取得自己的进程组，登记 execution/start UUID、PID、启动时刻、boot ID、PGID 和父 start ID，再以同一 PID `exec` 实际程序。准入失败立即返回 `resource_deferred` 及原始资源事实；原生子调用不排队等待父进程释放内存。Braid 的输入和未物化指派仍保留为可重试义务。

准入要求有限的 `memory.max`、同一 cgroup 的新鲜样本和可读的登记记录。决定时重新读取实际内存与 PSI，避免并发启动共同使用旧余量。每个存活的已登记 leader 提供 128 MiB 启动预算下限，保留 256 MiB 余量；预算下限与 cgroup 用量取较大值，不把各进程 RSS 相加作为容器占用。只有低 PSI 时才折减部分 inactive file cache，折减不超过上限的四分之一，仍只是可回收量的估计。

调整后用量达到 80% 或 PSI 升高时延后新增执行，达到 90%、出现新的 OOM kill 或严重 PSI 时视为严重压力；恢复要求低于 70% 且两个不同采样点持续低压。样本超过十秒、身份变化、读取失败均返回具体不可用原因，不当作空闲。普通 turn 只检查当前压力，不在模型思考和父等子期间长期占据另一个 turn 配额。

原生扩展在每次模型 turn 的当前 system prompt 中提供有界资源事实和工具原生 worker 建议，建议先用一个 worker。它不复制技能正文，不追加重复用户历史，也不改写 shell 命令。Braid 的既有循环串行请求一次有限作业减载，然后重新观察压力；一次减载只停止一个归属可确认的有限作业树，保留原输出、退出与可能的部分副作用。常驻服务不被自动当作有限作业中止。

Portless proxy 由 run 入口在任何成员启动之前以前台子进程启动，清除成员 execution/start 标记。同一 run 的成员共享这一代理，有限作业清理不拥有它。入口保留实际 Popen，通过 HTTP 的 `X-Portless: 1` 确认就绪，结束时向这个子进程发送信号并等待退出；已有监听者或旧 PID 文件不能替代当前 run 的所有权证明。普通应用服务仍由原生作业管理。

## 物理停止与逻辑接续

原生 RPC 的 `get_state.data.managed_state` 区分 `quiescent`、`busy` 和 `unknown`。除了正在进行的 turn，还检查有限作业、待接收结果和服务。OPEN 成员没有待投递输入/reset 且原生确认静止时，Braid 可以释放物理执行；逻辑会话、native 历史、指派和 clone 保留。之后只由真实输入或必要恢复唤醒，不在轮询中重新拉起全部 OPEN 成员。

父 Pi 的 wait 结果与 owned execution 的停止结果分别保存。非零退出或 SIGKILL 不自动等于子作业仍活；反之，父退出也不证明子作业已停。关闭先在准入使用的同一锁下设置 execution fence，阻止新作业，再按登记的 birth identity 和拥有的进程组清理；Pi 已退出时由 `native-managed.mjs cleanup` 离线完成。信号、权限和身份冲突保留原始错误，停止不明时不产生第二个写者。

停止回执的覆盖范围是已登记进程组及继承 execution/start marker 的后代。任意 shell 主动清除 marker 后再脱组、双重派生，可能超出这一范围；本机制不具备内核历史追踪能力，不能据回执声称对任意脱组进程的无条件证明。检测到归属不明则返回 `unknown`。历史运行跨容器恢复还须取得整个来源生成容器已停止的事实，不能把 Docker 暂停或新 volume 中可取得的锁当作旧执行已停。

Unknown 接续在停止可确认后沿原 native 身份恢复，以一次明确恢复输入要求核对已完成动作，避免盲重放。连续异常恢复有界；自身重试、例行根提醒和系统生成通知不重置次数。资源延后或恢复次数用尽时，其它健康成员仍可推进；所有成员确实没有可执行推进时，run 返回可恢复的 blocked。真正无法证明旧 execution 已停仍沿既有 fatal stop 路径阻塞整轮并保留 ownership；本轮不声称已经建立任意未知 writer 的跨成员隔离。

这些机制可以降低同时驻留和工具过量派生导致的 OOM，但不能保证任意单个命令都能在给定内存内完成。一次 shell 内部的 worker 数仍由所用工具控制；最低并行仍不足时保留事实，由运行负责人决定资源或执行方式。
