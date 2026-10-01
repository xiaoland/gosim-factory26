# 官网容器进程终止证据

2026-10-01 用户要求“改进实验基础设施”，以调查反复发生在官网运行中的原生 SIGKILL。用户随后澄清 WSL 从未出现此问题；WSL 宿主 tracefs 方案已停止，唯一未提交新增文件及精确 patch 保全到 `runs/experiment-signal-diagnostics-abandoned-20261001/` 后撤回，没有部署或发送信号。本任务不改四项已经冻结的 WSL 实验包。

本次源码授权覆盖官网容器内可取得的通用证据。新的官网生成、收费实验与冻结包部署仍按对应实验授权执行；当前失败 run 不能补采历史宿主事件。原失败身份与链路见 [I13 官网失败保全](../iteration13/hosted-github-failure.md)。

独立 advisor 已复核：复用 `lab.otlp.serve_run` 现有进程与停止循环，每两秒保存只读资源样本，不增加服务或修改 Braid 协议。`scripts/agent_support.py` 保存 namespace、proc/cgroup 原件、读取 errno、日志上限及自身信号请求、返回和 wait。`sources/braid/src/provider/pi.rs` 保存已有 wait/shutdown 事实；私有 Child owner 只记录释放，保持 Tokio 原有 `kill_on_drop(true)`，不为日志增加信号、wait 或重试。`scripts/core.py` 将证据加入既有归档对象，不增加生成或回收门禁。

主线复核要求持续保留长运行的末端证据，并避免按 PID 数字优先造成模型进程遗漏。资源数据因此采用两个各 31 MiB 的段轮转，启动基线独立保留、上限 2 MiB；每次轮转记录被替换的旧段字节数、上一段身份与覆盖开始时点。操作 JSONL 仍为低频 8 MiB cap，达到上限保存明确 marker。每个样本最多记录 256 个进程，优先 collector 父进程的后代树且按层级保留上层进程，其次为 run cwd、当前 cgroup和其它可见进程，各范围计数及遗漏数保存。不可读字段保留错误，不填零。证据目录位于生成 run 的 `process-evidence/`，不放进可回收的 `work/`。实际可读性由每次容器启动发现，不能把 WSL 验证结果当成官网权限保证。

SIGKILL 无法在被杀进程内捕捉。cgroup `oom_kill` 增量只能证明其范围内发生 OOM 杀进程，不能单独指认某个 Pi；namespace 可能隐藏宿主和祖先资源边界。成功的信号 API 返回不证明信号导致死亡；Child owner 释放也不证明 Tokio 发出了信号。整个容器被杀时 collector 可能一同停止，最终可下载覆盖取决于平台保存的工作区。预算保护器只退出 78，不发送 SIGKILL，本次不修改它。

源码与隔离 Linux 实际操作反馈已经完成。`python3 -m py_compile` 与 Braid `cargo check` 成功，没有运行 Factory/Braid 测试套件。无模型、无网络、有限额的隔离容器确认 cgroup v2 原始计数和 256 MiB 限制可读；UID 1000 读取 root PID 的部分 proc 字段返回 EACCES 13，保存了原错误。自建子进程实际 TERM/KILL 的 wait 分别为 -15/-9；共享 workspace 清理实际为 -15。日志目录只读时保留 EROFS 30，实际清理仍完成。现有 OTLP 接收返回 HTTP 200，collector 正常停止并保存最终样本。辅助证据归档实际权限拒绝返回 errno 13，保留错误且没有增加原有回收阻塞理由，恢复权限后对象重新纳入归档。

最终验证将资源段临时缩至 64 KiB，在 122 次真实 proc/cgroup 采样中发生四次轮转，上一段 60,841 字节、当前段 51,144 字节，末端仍有 final 样本；此修改只存在于 ignored runs 的一次性操作材料。默认两个 31 MiB 段未改。默认 collector 在三个可见进程时每个常规样本 3,509 字节，约 1,754.5 字节/秒；90 分钟约 9 MiB，62 MiB 名义覆盖约 10.29 小时。此速率不代表官网或模型运行；高进程数会缩短保留窗口，轮转会继续保留末端。每次采样保存实际范围与遗漏，达到详细记录上限时优先本运行进程树。

操作回执、源码 SHA、归档以及原始 JSONL 保存在 `runs/experiment-signal-diagnostics-validation-20261001/`，摘要为 `verification-summary.json`，Linux 原件在其 `remote-evidence/official-signal-evidence-validation-20261001-attempt5/`。远端隔离目录为 `/home/yyh/factory26/{assets,runs}/official-signal-evidence-validation-20261001` 及带 attempt 后缀的 runs 目录。早期操作材料命名冲突、runner 缺少 OTLP 依赖、stdin 未接入的失败回执均保留；后来从既有冻结目录只读复制既有 OTLP 依赖后正常验证。所有本任务隔离容器已在记录退出状态后删除，证据仍可读。正式模型容器与服务没有修改。

2026-10-01 主线转达新优先级：Flash/GitHub 与 Flash/Sheet 迁回官网非参赛生成，使用 ARC API；本版本成为这两条新启动的前置。恢复包需要冻结 `support/agent_support.py`、`support/core.py`、`support/otlp.py`，保留原 `support/otlp-deps`，并将本次 `pi.rs` 与 catalog 修复编入同一 Linux Braid。恢复入口 copy 后必须取得实际 `work/bin/braid` SHA，而非只更改 manifest。包和 Linux 编译由对应负责人实施。本任务只提交当前文件，不 push，不改四项 WSL 冻结包。官网 proc/cgroup 真实权限和首次采集完整性仍由下一次已授权新 run 的 capability/error 原件确认；WSL 回执不作官网保证。

自动恢复机制另作有界设计，不启动收费重试。恢复决策必须绑定当前官网 attempt 和本次新启动/退出身份，排除导入的旧 result、native 与 SIGKILL 日志。仅 generation 阶段、评测未开始、平台已终态且来源停止后考虑；当前版本不增加自动重试。
