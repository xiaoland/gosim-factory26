# GitHub 终态 SIGKILL：已知链与缺失证据

2026-09-27。来源是官网原 run `38dc20e99fa5` 的原样终态工作区 `runs/acceptance-integrity/20260927/cooperation-hackathon-self-funded/github-terminal-workspace.zip`；本调查不修改原 run，也不阻止独立自费恢复运行。

11:34:20 UTC，Braid 先记录一个 Pi turn 的 `provider disconnected`，随后在约 0.1 秒内记录两个 DeepSeek Pi 会话退出信号 9。11:34:21 Braid 因 `native teardown could not be proven` 以 `blocked` 结束。官网 generation 失败，evaluation 未开始，0/0 不是应用评分。

两个被杀会话的原生 JSONL 最后仍有实际工作：Issue #7 在写浏览器检查，另一会话在检查前后端服务。扫描 11:25–11:35 的原生 assistant tool calls，没有找到针对 Pi 进程的 `kill`/`pkill` 命令。更早的会话确有针对 Node 服务的终止命令，不能据此归因 11:34 的双 Pi 退出。

现有 ZIP 不含 cgroup `memory.events`、kernel OOM 记录、平台容器退出原因或信号发送者记录。两个会话几乎同时退出与外部资源/进程组处置相容，但也不能排除其它发送者；不能把 OOM 写成结论。要区分原因，需要官网 runner 在 11:34:20 前后的容器内存峰值、OOMKill 状态、cgroup 事件与进程信号来源。当前可确定的运行失败直接原因是 Braid 遇到 SIGKILL 后拒绝无证明地导出半成品；信号来源仍未确定。

新 self_funded 恢复 run `e4e7f35f55eb` 已从保存的原 Braid run 和工作区继续执行。它的完成与否将检验可恢复性，但不会反向证明原 SIGKILL 的来源。
