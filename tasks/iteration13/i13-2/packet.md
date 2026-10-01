# I13-2：内存压力、协作材料与过程验收

2026-10-01。I13-2 源码与材料已完成，Linux 编译、原生执行实际操作和两份本地恢复包的真实 prepare-only 操作通过。21:43 CST 已停止两个旧生成容器，从保全副本启动新 experiment `exp-20261001-212808-5a935b`；当前正在读取新执行回执、接入单一 Console 与独立监控。用户取消的官网 Flash/Sheet `691028015e69` 正从取消后原件准备接续材料。本文件记录本轮增量；I13 模型、费用和实验关系归[实验树](../experiments.md)。

## 授权与目标

用户原话：“我们因为 OOM 要改进 factory harness（你提出的 OOM 防范改进方案，我同意）”；“我们也取得了一些运行的过程，不必等待评分，也可以对 I13 的改进进行验收了，加快我们的反馈循环，节省 API 额度”；“这些改进，作为 I13-2，并且热恢复到 I13 的运行”。

这条指示授权落实[已讨论的 OOM 方案](../../experiment-signal-diagnostics/packet.md)、调查和修正本次协作缺陷、用已有真实过程验收 I13，并将完成的改进应用到可确认的暂停检查点。恢复继续使用对应 I13 模型与费用配方，保留 Git、Braid 与原生会话。它不改变官网新收费尝试的边界，不以自动重试消耗额度换取进展。Console 的独立改进和部署仍由原会话负责。

新增官网Sheet授权原话：“那我们将该运行取消，然后等待 I13-2 一起热修复来恢复吧”。取消已实际执行并确认，后续Sheet接续纳入本次I13-2范围；当前等待改进完成和新恢复输入冻结，由主线核对来源、费用模式与实际新身份后执行，不立即启动或重复重试，不据此恢复已失败的官网GitHub。

用户给出的协作事实入口是 GLM/Sheet `glm-root--hackathon--sheet-a45a22ec644204` 的 PR 2 与 Issue 1。PR description 中疑似重复了应由 task packet、durable docs、AGENTS.md 承接的内容；根讨论中存在过时评论。用户明确预期：隐藏根评论时，它下面所有子评论也隐藏。调查需要区分实际材料重复、技能未被采用、提示冲突、对象语义与展示差异，不能仅凭篇幅判断协作失败。

用户随后补充：“浏览 origin/develop，我发现 Agent 实际上没有建立符合 SVC 要求的知识文档系统，也没有看到 `tasks/` ……我要求必须使用 SVC 文档系统和 task packet”。据此，SVC 文档与 packet 是本轮强制行为要求，验收必须覆盖当前发布分支及接续者的发现/取得路径。原生会话中出现 write 或 read 只证明局部动作；仍须核对文件是否留在私有 clone、是否提交/发布、共同入口是否能指向适用材料，以及后续成员是否实际采用。不得以 PR description 代替缺失的工作记忆，也不以创建空目录或固定模板集合冒充文档系统。

用户进一步提出两个待核对解释：遗留 `harness/skills/svc` 总入口是否仍分发 growth，以及 task-packet 的启用时机和载体边界是否不够明确。前者已核对本轮旧 ZIP、暂停现场与新 staging：实际均为四项独立 SVC 技能，遗留总入口未进入 I13。后者纳入当前协作修正，通用技能明确工作前启用和各类材料职责，Braid 特有 description/comment 边界留在 Braid 技能；profile 只持有强制采用和触发要求。文本位置是候选解释，不能替代实际因果证据。

## 工作树与责任

```text
I13-2
├─ 暂停现场与接续来源：核对真实 writer/暂停状态，保全完整检查点
├─ OOM 防范：执行所有权与异常接续、空闲释放、资源准入、工具压力反馈
├─ 协作修正：PR/文档职责、技能采用、根评论隐藏与后代可见性
├─ I13 过程验收：已有行为证据、未覆盖行为、修正前后差异
└─ 热恢复：冻结新制品，核对旧执行停止，保持原身份与工作记忆接续
```

主线持有集成与恢复决定。`i13_local_console_attach` 仅负责两项暂停现场保全及恢复可行性；`oom_recovery_code_review` 沿既有调查细化 OOM 接口和实施边界；`i13_collaboration_forensics` 定向调查 PR 2、Issue 1 与当前材料。实施交接在各自结果中记录明确文件所有权，避免并行覆盖。源码改动、编译和实际操作按范围推进，不新增或运行 Factory、Braid、SVC 测试或改名探针。

## 当前来源与接续约束

本地 experiment 为 `exp-20261001-184401-7c84dd`，入口 `runs/iteration13/local-rebuild-20261001/launch-summary.json`。GitHub run 为 `glm-root--hackathon--github-f9e238c1b698a5`，Braid run 为 `20261001-074336-af6f78cd`；Sheet run 为 `glm-root--hackathon--sheet-a45a22ec644204`，Braid run 为 `20261001-104900-3b994a70`。容器运行在 Debian-Rebuild 的远端 Docker，控制器和证据保留在 Mac。用户声明暂停后的实际进程状态仍需只读核对，旧 launch-summary 的 RUNNING 不能代表当前状态。

本轮原件写入 `runs/iteration13/i13-2-20261001/`，现场保全归 `preservation/`。不把单独 Git 提交、数据库拷贝或非原子运行中 ZIP 当成完整检查点；完整性取决于应用文件/私有 Git、Braid DB/WAL 和 native session 是否属于同一静止执行状态。变更冻结材料前保留旧制品与源快照；新制品身份、材料更新方式和任何会话变化都须有回执。

两份完整归档的源前后清单与本地清单一致，导出后仍为暂停。Sheet archive SHA256 为 `a0e26c43e68cfb3bbffd6642cb68c495ea1e76d5a4e809a49fcfe115f34f8f72`，GitHub 为 `11f93424e118d0de8f0b180b706097404c0aee1b1dd87363b1c2c9a40e508f72`；主线重新计算 SHA 并保存 `preservation/primary-verification.json`。来源包括完整私有 Git、未提交工作树、Braid DB/WAL 与 native 历史，不包括进程内存。实际停止证明仍须在 offline-resume 前取得。

实际只读检查已确认两个原生成容器均为 Docker `Paused=true`，Mac lab 状态仍是 running。暂停本身不会使 `lab.wait` 返回终态。主线核对旧 `follow-batch.py` 的 PID 4719 和精确入口后已发送 TERM，随后确认进程不再存在，回执为 `preservation/old-follow-stop.json`；这是为本轮维护撤下旧自动评分跟随，不改变容器暂停状态。Luna 独立监控及既有 heartbeat 已同步用户暂停，官网采集继续原范围。

官网Sheet的新来源为 `runs/iteration13/hosted-recovery-20261001/sheet-user-cancel/workspace.zip`，SHA256 `0e9c2798c80ab56641f7937aed861416d164dd495a716378e702975a795fa13b`。取消前核对submission `5ada036f2340`与run `691028015e69`，单次POST后独立GET确认CANCELLED；回执pending=false。取消后导出HTTP200、155468835字节，原件包含Braid `20261001-074506-6e7af22b`、origin.git、工作树、DB/WAL和native；平台仍遗漏clone私有 `.git`，需要重建接续，不能宣称完整私有Git检查点。保存取消/下载/内容回执，不改变旧ZIP或native历史。Braid导出status中的running不证明取消后仍有进程。既有hosted_monitor取得终态后正常退出；`i13-wsl` heartbeat保持原PAUSED状态，等待主线交接新身份。

最新原件已推翻此前从17:35快照推断持续卡死的结论：PR2/3/4已MERGED，PR5会话在21:10:13成功修改undo.ts、21:13:05成功修改types.ts，根会话至21:14:39仍在定位任务packet。这些是实际内容证据，不依赖新增对象数或token增长；仍未证明应用完成或通过评测。恢复前应进一步核对PR5未提交工作与发布commit `743c543e5e048aa3172639436b4c252cf93b742b`、DB及native的关系，保留取消时的在途工作，避免将旧测试失败作为当前阻塞原因。

## 本地热恢复实施

本次源码提交为 `d3f1a3e`（原生执行所有权、资源准入与生命周期）、`dbf2795`（协作材料采用及可见性）、`842e9ee`（恢复入口选择及持续文档）。冻结制品没有带入共享工作区的其它改动。I13 实际仍分发四项独立 SVC 技能；遗留 `harness/skills/svc` 总入口和 growth 不进入本轮。

| 恢复目标 | 新 lab run | 恢复制品 SHA256 |
| --- | --- | --- |
| GLM/GitHub | `glm-root--hackathon--github-346a6ae5a0e3a0` | `eaaaa9af3bc2556248e48657ef2bb081cdc7e2d210c07735b77911fffc2d76a5` |
| GLM/Sheet | `glm-root--hackathon--sheet-efba85c7cfa0f9` | `421314b614bf13e1a33c95fc244ed6813de2f07a5c6972915e94ecbabd14e9a5` |

真实 Linux prepare-only 操作在无网络、无外部挂载的隔离容器完成。GitHub 的27,100份来源文件、Sheet的21,740份来源文件均逐项一致；原生身份、Braid配方、root选择不变，GitHub根9项和PR2的55项未提交工作、Sheet PR3的12项未提交工作仍在。68份独立技能文件及保留home中的原生材料与新包一致，profile指令已更新。原始权限前置错误和bare origin不适用 `git status` 的回执保留，不能删除后宣称从无错误。证据为 `runs/iteration13/i13-2-20261001/recovery-prepare/observations.json` 及分题原件。

`preservation/pre-stop-readback.json` 证明原生成仍暂停、容器birth/daemon身份一致，当前Braid各表内容与保全数据库完全相同、quick_check均ok。随后按本次维护执行stop，两容器均为 `Running=false, Paused=false, Pid=0, ExitCode=143, OOMKilled=false`；这是主动切换，不是新增OOM或不明SIGKILL。旧3+8采集及自动评分跟随已撤下，原卷和归档保留。实际停止证明在 `preservation/old-execution-stop.json`。

新执行延续相同Braid/native身份，使用新的lab run和volume区分这次物理执行。两份派生检查点各有一条维护comment，交代新的独立技能与补齐现有未发布材料的义务；原description、会话历史和未提交代码没有被改写。`recipe.json` 冻结2路并发、每容器4GiB/2CPU及原自有API配方。新终态跟随只有在runner成功、结果completed且应用已发布时才独立self_funded重放，维护退出不触发评分。

官网Sheet须另记取消后来源的Git重建限制：平台遗漏clone私有 `.git`；根checkout有原生操作与89个已发布文件共同支持，可仅重建为 `verify-pr4@bc9c94a`，保留PR5未提交改动和已在途的context reset。它不等于原暂存区、reflog或未发布提交历史已经恢复。待派生ZIP、冻结包和实际prepare-only回执收齐后再执行本次获授权的Sheet接续。

## 验收决定

新 Braid 已从冻结源码构建 Linux binary，源码集合 SHA256 为 `17f93d620849abd0d72efc8770cabfcd39bbc3c610756ff3c4fbb7484b9a4dfb`，binary 为 `bde76a5adcfa581d0d7e24c9bc9cddc32a07bca49888ee0cf8315f00bee03dc5`。实际 Linux 操作确认有限作业减载、服务保留、execution fence 拒绝后续启动和父 Pi 被 SIGKILL 后的离线清理。独立 `/proc` 观察确认父 wait=-9 时子进程仍存活，清理后不再可写；共享 Portless proxy 保持同一 birth 存活并继续响应，最终由 run owner 停止。原件归 `native-runtime/linux-operations/`，适用范围和未触发的模型行为见 [原生实施](native-runtime.md)。这不是强制 OOM 实验，也不能据此保证任意命令不会耗尽内存。

先消费既有生成过程，不等待分数，也不把生成中间态或未评测的零分当作最终应用质量。每项原 I13 目标记录实际触发场景、观察结果、证据入口、未覆盖边界与本轮是否需要修改。重点确认文档各自承担什么、PR 是否复制长期依据、根上下文是否持续保留失效消息，以及遇到资源压力时能否收敛负载和接续原工作。

[过程验收](process-acceptance.md)已区分实际通过、目标未达与尚未覆盖：GitHub 原 native 恢复已有直接证据；Sheet 的技能实际读取未阻止 PR 镜像和事后补 packet；隐藏根的后代仍进入新模型上下文。工具次数仅用作查找入口，不当成方法采用或推进质量。

OOM 的完成证据应覆盖：旧执行及其拥有的子作业确实停止；异常结果与停止证明分开；原 native 历史延续；未盲重放未知外部动作；空闲卸载不会立即被轮询重新拉起；资源拒绝不会使父子委派等待死锁；工具内部并发有真实预算与失败反馈。官网 cgroup 只读，不能把写 memory.high 或子 cgroup 当作必需能力。

协作的完成证据应覆盖：稳定依据留在可定位的文档，PR 保留面向评审与交付的必要事实；根评论隐藏在所有正常读取/模型投影中传递给后代，恢复可见性不会抹去后代自身的隐藏选择；已有原生历史不重写。具体修正依据归 [协作调查](collaboration-findings.md)，OOM 具体实施边界归 [实施准备](oom-implementation.md)。

SVC 强制要求的发布验收按实际协作阶段解释：根共享文档、项目阅读入口和根任务 packet 应在消费者依赖它们之前发布到可取得的共同提交；PR 的当前 packet 随其候选发布，让负责人和接续者可读，合入后在 `origin/develop` 保留。正在进行的局部试验不要求每个文件修改都发布，但仅存在于未提交私有 clone 的 packet 不能声称已完成交接。恢复后必须补齐当前工作中已经欠缺的材料及发布，而非只等待新任务自然采用新文案。

修正完成后先报告实际改动、保全来源与恢复影响，再按本次授权热恢复本地两项及上述已取消的官网Sheet；若来源完整性或必要方案超出本次授权出现实质变化，则把最小决定交回用户。已失败官网GitHub的收费恢复不在新增Sheet指示范围内。
