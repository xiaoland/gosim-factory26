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

## 自动恢复建议（未实现）

推荐复用 `lab/arc_bench/hosted_monitor.py` 的终态采集及既有监控锁，增加一个由冻结实验策略显式启用的恢复分支，不另建服务。策略只允许名单中的非参赛 `self_funded` / ARC API 生成，按原始来源 family 累计至多一次生成接续；恢复 run 再失败就停止，不把新 run 重新当成拥有一次额度的来源。初始 Flash/GitHub、Flash/Sheet 的已授权启动不等这个分支，分析本身不授权额外收费请求。上线付费分支前要冻结允许的来源、一次接续额度及费用/时间边界。

恢复候选必须同时满足：重新 GET 并核对当前平台官网 run、submission、task 身份，明确 `FAILED` 且执行环境已停止；当前 generation 阶段失败，`evaluation_started_at` 明确为空、测试仍未开始，不能把字段缺失当作未开始；当前 attempt 有真实的新 Braid 启动和 PID/starttime 身份，以及其运行期间新 Pi 启动与对应 wait 的 signal 9（或主 Braid 自身 wait=-9）事实。仅字符串 SIGKILL、旧 Braid run ID、旧 result 或 native 会话内容不足。信号来源仍可未知；这是获准后进行一次接续的故障判据，不是将其归因为平台或 OOM。

恢复入口应在任何准备操作前持久化新 attempt UUID，绑定父来源、当前包/需求 SHA 和可取得的当前平台 run；保全导入的 `process-evidence/`、旧 recovery 日志、旧 result，当前日志和采样用新的目录。主 Braid 请求、实际 spawn 的 PID/starttime/namespace、二进制 SHA、wait 分别记录，保留原错误和原生命周期。Pi 的当前启动 identity 与 wait 从独立的新 Braid 日志关联；同一 PID 必须在同一个新进程生命周期内解释。g02 这种新 Pi 尚未启动就 EACCES 的情况应分类为当前启动权限错误，旧来源的 SIGKILL 被排除。现有 `result.json` 没有 attempt 或时间身份，不能靠其原路径仍存在或 mtime 判断本次执行。准备模式也不能当模型已启动。缺少新身份、日志写失败、wait 不可得或归属不唯一时，停止自动决策并留下缺口，不补猜事实。

首先保全当前 raw API 状态/日志、工作区 ZIP、下载 HTTP 收据、CRC/SHA、包与请求身份；确认 Braid DB/WAL、origin/ref、worktree 文件、原生 session/header 可相互对应，缺失私有 Git 与非原子快照的限制保留。然后复用 `scripts/package_completed_recovery.py --journal ... --continue-generation` 从原件副本建立独立恢复包，保持模型配方、材料和预算保护，使用已验证的 runtime；在新目录执行既有无模型准备反馈。该入口当前只相信已保存 journal 终态，自动分支须在打包前和写请求前重新核对远端停止事实。完整可恢复检查点无法确认、材料/模型不同或需要新修复时退出自动路径，交回决定。

远端写入统一复用 `competition.Controller.prepare`、`_post`、`recover` 的持久化 pending 和锁边界。`recover` 在这里核查未确认的 HTTP 写入，不恢复容器或生成进程。上传、create、start 任一响应未知都保留 pending，只读核查同一 submission/task/run，不重发 POST，也不重新生成 ZIP 绕过 pending；找不到唯一 identity 时停止。新恢复 journal 关联原来源与 attempt、保持非参赛费用模式，执行后仍由现有 monitor 采集；重复失败、用户停止/取消、budget-stop、exit 78、认证/额度拒绝、确认资源边界不足、源码/材料变化、评测已经开始都不触发第二次生成。部署或应用评测失败走已冻结应用的独立重放范围，不能通过重新生成自动争取分数。token 增长和 reviewer 分类不参与这些门控。

现有已核实客户端仅提供创建新 run、start、cancel 和状态/产物读取；未发现可复用的失败容器重启接口。`PAUSED` 或恢复请求状态也不证明终态容器可原地重建。因此本方案使用新容器、新 run、新包身份，保留旧 Braid run 的工作记忆并由 Braid `--offline-resume` 处理，不向旧 `/start` 请求赌博。新生成会继续消耗 ARC API 额度；有限次不代表有限美元。现有成本观察可能延迟，按 Braid session 的模型限制也不是金额上限；若没有已冻结的新增费用/时间额度及可用的停止条件，只自动保全和准备包，停止在创建/启动之前。

最少实施面为 `lab/arc_bench/hosted_monitor.py` 的终态恢复分支与 family 回执，以及由现有负责人接线的 `submission/recover_completed.py` attempt/启动证据；`competition.py` 和打包器继续复用，只有身份校验或入口不够用的具体缺口才扩展。验收保留当前真实 Linux EACCES/SIGKILL/wait 回执、新旧 attempt 隔离与实际恢复包的 `--prepare-only` 反馈；HTTP 不确定写入和真实收费接续必须在之后明确获授权的官网操作中取得原件，不引入模拟测试、探针套件或为验收制造收费重试。
