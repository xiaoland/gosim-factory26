# I13-2：内存压力、协作材料与过程验收

2026-10-01。首次真实部署暴露的资源暂缓终态误判和历史成员材料选择错误均已修复。新的本地 experiment `exp-20261001-223204-4b68eb` 已启动两项，首批原件确认两项原Pi实际resume，Sheet在同一attempt中等待资源后继续，九份已采集原生历史prefix保持；官网Sheet通过真实prepare-only及文件/身份核对后，已创建 `f16834f58674`，self_funded、比赛额度关闭。用户随后追加授权恢复官网Flash/GitHub，现已按同一I13-2配方从保全终态创建 `e1aa595f6995`，self_funded、比赛额度关闭；首批为平台部署阶段，尚未取得新Pi接续证据。原暂停现场、首次失败卷与取消后原件完整保留；同一Console已切换新服务，旧两项归档与新两项live分开登记，实际HTTP/UI读取通过，详见[部署回执](console-deployment.md)。监控已由纯脚本接管，不唤醒审查模型。当前证据与修复归本packet，I13整体实验关系归[实验树](../experiments.md)。

## 授权与目标

用户原话：“我们因为 OOM 要改进 factory harness（你提出的 OOM 防范改进方案，我同意）”；“我们也取得了一些运行的过程，不必等待评分，也可以对 I13 的改进进行验收了，加快我们的反馈循环，节省 API 额度”；“这些改进，作为 I13-2，并且热恢复到 I13 的运行”。

这条指示授权落实[已讨论的 OOM 方案](../../experiment-signal-diagnostics/packet.md)、调查和修正本次协作缺陷、用已有真实过程验收 I13，并将完成的改进应用到可确认的暂停检查点。恢复继续使用对应 I13 模型与费用配方，保留 Git、Braid 与原生会话。它不改变官网新收费尝试的边界，不以自动重试消耗额度换取进展。Console 的独立改进和部署仍由原会话负责。

新增官网Sheet授权原话：“那我们将该运行取消，然后等待 I13-2 一起热修复来恢复吧”。取消已实际执行并确认，后续Sheet接续纳入本次I13-2范围；该范围现已完成改进、冻结、真实prepare-only并启动唯一新执行；不重复重试，不据此恢复已失败的官网GitHub。

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

## 首次实际部署反馈与修正

本地两项于13:56Z完成材料刷新，Braid尝试offline-resume时遭遇资源准入暂缓：GitHub PSI avg10从8.11下降到5.43，Sheet从30下降到24.57；可用charge余量分别约1.82GB和2.16GB，oom_kill均0。worker把资源原因记入恢复错误，local将其聚合成 `provider recovery returned an error` 并blocked退出。Docker实际ExitCode1、Pid0、OOMKilled=false；没有观察到本次Pi启动/握手。原日志与准确限制归[首次接续验收](first-continuation.md)。这不是新OOM或模型生成结果，技能采用、packet发布尚未覆盖。

修正须保留资源暂缓的类型与等待状态，避免将所有Deferred（还用于运输错误、streaming或恢复额度耗尽）一并豁免；原队列、claim、reset及会话身份继续保留，压力恢复后由既有循环接续。PSI累计total在观察窗口未增加而avg10正在衰减，当前不据此放宽阈值。独立判断归[startup-deferral-review.md](startup-deferral-review.md)，源码与实际验证归[startup-deferral-fix.md](startup-deferral-fix.md)。

官网Sheet的首版冻结包 `9e879198…` 仅做prepare-only，没有官网写请求。它因 `native material refresh changes pi-deepseek-fast.model` 停止：原历史identity已迁移为GLM-5.3-Flash/root-only，但Flash base仍包含旧同名DeepSeek模板，刷新逻辑只有在ID缺失时才选择GLM材料。修正限定该已授权迁移且非root的历史identity，无论模板是否同名均选择GLM材料；保留原profile/model、会话与transport，其它模型变化仍拒绝。失败原件归 `recovery-prepare/hosted-sheet/`，来源重建记录归[官网Sheet恢复](hosted-sheet-recovery.md)。

两项修正完成后冻结新的Linux binary与恢复包，旧失败包、未提交官网journal、停止容器及原始错误继续保留。原本地自动评分有成功及发布门槛，本次入口故障不触发重放；主线不会把同一未确认写入重发为第二次官网收费请求。

## 修正后的第二次本地部署

资源类型修复已提交 `468dadd`，材料选择修复为 `111b3a0`。Linux 使用缓存编译镜像、禁用构建网络执行 `cargo build --locked --offline --release --jobs 2` 成功；源码集合 SHA256 为 `89d19889b3e965147b6c00ded21717e32bb42ed05f34ef31ce6a11e7ffa82443`，binary 为 `9d322da9e3dde2d8fb065cff2f5543fdc668dd8dcd2e653a31e87fb1a34874eb`。原生 runtime、技能与模型配方沿用已核对的 I13-2 材料，旧ZIP保持原样。

| 目标 | 第二次物理运行或当前阶段 | 新ZIP SHA256 |
| --- | --- | --- |
| GLM/GitHub | `glm-root--hackathon--github-a94a67b4b3d85b`，原Pi已接续 | `5e80c89aa8a74c48c04b4ca963a1a4d310a50ac26aebeda57a68b58356a5f932` |
| GLM/Sheet | `glm-root--hackathon--sheet-8046cfb0695023`，等待资源后已接续 | `9a48d4604db95be60ba62d456cf1f49a145825820b87e87b3b8c16e9084b044a` |
| 官网 Flash/Sheet | `f16834f58674`，journal `hosted-sheet-r2` | `7de33f7d23a910ec61e4b639275305cdd05222416ff01f2e757d55e58c1ff316` |

新的本地 recipe、冻结实验、当前矩阵、成功后评分跟随及原件归 `runs/iteration13/i13-2-20261001/revision2/`。recipe SHA256 为 `cc5ea8ec405daede3d765b827af52ca7ff1b4b63d8b223a310b45d14d5ce344c`，保持两路并发、每容器4GiB/2CPU与原自有API配方。两项均使用原已保全的停止检查点；首次失败没有观察到Pi启动，不从其中提取新的应用进度。

官网新submission为 `e69e9764310c`，run为 `f16834f58674`。`hosted-sheet-r2/launch-receipt.json` 保存 snapshot/create/start 与独立status/history读回，billing_mode=self_funded、allow_competition_credit=false、pending=null；最初读回QUEUED，脚本随后保存RUNNING及本轮active provider。提交前实际prepare-only和最终readback均exit0，746份保留文件、36份原native、PR5十项未提交文件及pending reset保持，新68份技能与70份home材料匹配冻结包。启动脚本首次仅因本地模块路径缺失而未进入API，错误原件保留；修正后在脚本内部核对最终prepare回执、包SHA和无写身份journal，才执行唯一获授权提交。


首批实际接续已完成一次性取证：两项 root 与原 PR 均在本轮边界后完成 resume/握手，九份已采集 native 保留来源 prefix。Sheet 同一次执行中保留原 reset 等待资源，随后 resume 并应用该 reset，直接覆盖此次资源暂缓修复。两 root 均成功取得维护评论、读取独立技能，并把 AGENTS 与共享 packet 发布到私有 origin/develop（GitHub ccba351、Sheet 3c107ab）。这证明接续和材料补齐已经发生，尚不等于所有协作目标或最终应用通过。原件与覆盖限制归[首次接续验收](first-continuation.md)。

首次 experiment 已自然取得两条 `finished/failed` 终态，原终态跟随按成功门槛跳过官方重放。其最终完整归档另被快照外符号链接阻断，卷与helper保留，详见[回收终态诊断](transport-finalization.md)。这不改变原始恢复入口exit1事实，也不以归档失败冒充应用评分。

## 官网 Flash/GitHub 新增恢复授权

用户在三项接续完成后明确：“flash/github 也请恢复”。本次恢复目标是失败 run `377afa346c92` 的最新可恢复终态工作区，原件 SHA256 `88f2c0c85ffde65ea7fa5db8adb1b96c8692bd2188383f6e85d584177abb486b`。沿用 I13-2 Flash r2 冻结材料、根 GLM-5.3-Flash/advisor Kimi-K2.7-Code、自有 ARC key 与 self_funded，关闭比赛额度。保留原生/Braid/应用进度，平台遗漏的私有 Git 只按实际证据重建并声明限制；先完成隔离 prepare-only，再创建一次新的官网执行。写请求结果不明时只读恢复核查，不重复提交。

恢复输入、工作树和实际准备由 `i13_2_native_runtime` 有界负责，主线负责费用与journal核对、唯一提交和接入既有纯脚本监控。启动前官网题目GET已确认hackathon及GitHub题目可用；旧run的附加GET曾返回HTTP500（该次仅保存错误字符串，响应正文缺失），不以此覆盖已保全的FAILED原件。回执归 github-launch-preparation/。既有两项本地GLM、官网Sheet及Console不受影响。完成条件为恢复包/来源可追溯、实际准备通过、官网新身份与费用模式读回、脚本开始采集该run；长期运行及最终评分另按现有实验流程收集。事实归[GitHub恢复记录](hosted-github-recovery.md)。

本次 GitHub 派生工作区 SHA256 为 `95476f6e56cc15e12a5ca0b7aa4aa44b8c62819ec75154d49fbbd1c6873cb7d6`，最终 ZIP 为 `bd897c86b9dbb56186d3929522e01d2dff19d76fb940f1b613e00ee80751f615`（701169017 bytes）。根私有 Git 依据原生成功提交及八文件tree重建为 `base-scaffolding@828d17e76c962135b1d0827dc62c24ebf76d419e`；PR4/5/6 的在途修改保留。真实 Linux prepare-only 已退出0，stderr为空；786份保留文件、35份原生材料、原identity/工作树状态保持，68份技能与56份home材料匹配。主线另行复算原/派生ZIP及15份原生对话JSONL，均匹配。准确准备回执归 `recovery-prepare/hosted-github-r2/receipt.json`。

唯一提交入口 `launch-hosted-github-r2.py` 已成功完成snapshot/create/start，全流程在同一competition锁内串行执行，没有重发。新submission为 `8fad2a412927`，run为 `e1aa595f6995`，journal `hosted-github-r2` 的pending=null，独立读回billing_mode=self_funded、submission credential_mode=self_funded。比赛额度在冻结输入中为false。23:51:07 CST首批脚本原件为RUNNING、deploy_agent=running、start_agent=pending，当前只能确认平台部署，不能宣称Pi已resume。

既有官网collector按保存的完整进程身份从48187切到245，在同一输出目录追加GitHub journal；Sheet的next/liveness/notifications/done逐项保持，没有新增并行collector或模型审查。回执为 `script-monitor/github-attach-receipt.json`，首批原件为 `hosted-sheet-r2/monitor/20261001T155107.297047Z/`；准确新进程身份归 `hosted-sheet-r2/monitor-launch.json`。

## 监控调整（用户新增授权）

用户明确：“让运行监控用脚本来实现，做到自动化，不继续使用模型，可以通过检查 provider sessions 的状态来判断是否 stale。”据此，`i13-wsl` heartbeat已设PAUSED，监控聊天已idle，不再唤醒Luna或其它审查模型。新官网采集不使用会调用模型的旧 `--review` 路径。由 `local_monitor` 与 `hosted_monitor` 脚本按实际provider identity、生命周期、最后活动和连续观测判断正常等待、不可用、疑似stale及终态，保留阈值/来源与unknown；疑似stale不自动视为有效失败，也不触发收费重跑。实现和实际历史批次反馈归[纯脚本监控](script-monitor.md)。这不取消已经授权的运行本身或成功产物的独立官方评分。

源码已提交 `48bb51b`，官网排队/初始化分支为 `dbcaa2b`，当前会话汇总修正为 `aaf4971`。本地后台PID与源码SHA归 `revision2/background-launch.json`（首个PID17338，当前48111）；官网归 `hosted-sheet-r2/monitor-launch.json`（首个PID27102，经48187后，追加GitHub的当前PID为245）。首批本地原件为 `revision2/observation/monitor/20261001T144445.120401Z`，stderr空；分类仅供定位，实际接续验收仍读取原生记录。默认至少两样本、30分钟无可观测活动才提示suspected_stale；长期不可读原件独立记observation_missing。两处输出目录各自持有文件锁、scheduler与终态记录，旧模型采集不恢复。当前会话优先于导入历史的汇总修正已用真实批次回读确认，两条脚本按精确进程身份重启，scheduler历史和下次采集时间不变，回执为 script-monitor/monitor-restart-current-priority.json。

## 验收决定

首版 I13-2 Braid 从冻结源码构建 Linux binary，源码集合 SHA256 为 `17f93d620849abd0d72efc8770cabfcd39bbc3c610756ff3c4fbb7484b9a4dfb`，binary 为 `bde76a5adcfa581d0d7e24c9bc9cddc32a07bca49888ee0cf8315f00bee03dc5`。实际 Linux 操作确认有限作业减载、服务保留、execution fence 拒绝后续启动和父 Pi 被 SIGKILL 后的离线清理。独立 `/proc` 观察确认父 wait=-9 时子进程仍存活，清理后不再可写；共享 Portless proxy 保持同一 birth 存活并继续响应，最终由 run owner 停止。原件归 `native-runtime/linux-operations/`，适用范围和未触发的模型行为见 [原生实施](native-runtime.md)。这不是强制 OOM 实验，也不能据此保证任意命令不会耗尽内存。

先消费既有生成过程，不等待分数，也不把生成中间态或未评测的零分当作最终应用质量。每项原 I13 目标记录实际触发场景、观察结果、证据入口、未覆盖边界与本轮是否需要修改。重点确认文档各自承担什么、PR 是否复制长期依据、根上下文是否持续保留失效消息，以及遇到资源压力时能否收敛负载和接续原工作。

[过程验收](process-acceptance.md)已区分实际通过、目标未达与尚未覆盖：GitHub 原 native 恢复已有直接证据；Sheet 的技能实际读取未阻止 PR 镜像和事后补 packet；隐藏根的后代仍进入新模型上下文。工具次数仅用作查找入口，不当成方法采用或推进质量。

OOM 的完成证据应覆盖：旧执行及其拥有的子作业确实停止；异常结果与停止证明分开；原 native 历史延续；未盲重放未知外部动作；空闲卸载不会立即被轮询重新拉起；资源拒绝不会使父子委派等待死锁；工具内部并发有真实预算与失败反馈。官网 cgroup 只读，不能把写 memory.high 或子 cgroup 当作必需能力。

协作的完成证据应覆盖：稳定依据留在可定位的文档，PR 保留面向评审与交付的必要事实；根评论隐藏在所有正常读取/模型投影中传递给后代，恢复可见性不会抹去后代自身的隐藏选择；已有原生历史不重写。具体修正依据归 [协作调查](collaboration-findings.md)，OOM 具体实施边界归 [实施准备](oom-implementation.md)。

SVC 强制要求的发布验收按实际协作阶段解释：根共享文档、项目阅读入口和根任务 packet 应在消费者依赖它们之前发布到可取得的共同提交；PR 的当前 packet 随其候选发布，让负责人和接续者可读，合入后在 `origin/develop` 保留。正在进行的局部试验不要求每个文件修改都发布，但仅存在于未提交私有 clone 的 packet 不能声称已完成交接。恢复后必须补齐当前工作中已经欠缺的材料及发布，而非只等待新任务自然采用新文案。

修正完成后先报告实际改动、保全来源与恢复影响，再按本次授权热恢复本地两项及上述已取消的官网Sheet；若来源完整性或必要方案超出本次授权出现实质变化，则把最小决定交回用户。此前已失败官网GitHub不在新增Sheet指示范围内；用户随后明确“flash/github 也请恢复”，现将其单次I13-2官网接续纳入授权。


## 2026-10-02 监控恢复

用户纠正此前完全取消监控会话的安排，明确要求 GPT-5.6-Luna / low 每十分钟监控各run并复用脚本。现有采集器保持唯一，新增模型层仅消费已保存的provider状态、outcome和alerts；普通进展保持安静。原监控聊天已解除归档。旧i13-wsl已被删除，故同会话启用唯一i13-i14 heartbeat。I14新运行索引在 runs/iteration14/i14-0/active-matrix.json；不改变本packet中I13的包、来源、费用或尝试身份。
