# 协作体验对齐

## 目标与阶段

让 Agent 凭 GitHub 使用经验可靠地参与、交接和再次接手工作，同时保留 Braid 的可编辑上下文能力。
用户已回复“同意（braid发送的根检查评论其实就接近人类的协作角色），继续推进”，通过 [技术与验收方案](../cooperation-design.md)。实施计划与独立预演已完成；2026-09-27 用户经协调对话明确授权“现在开工”，范围为关注、收件、活动历史、根空闲检查、CLI/view 和文档整合，并授权本地 Lite 验收。随后用户更新实验顺序：这轮 Lite 只需完整生成和交付，无需等待本地评分；通过后用同一冻结包和官网 API 的 `self_funded` 模式运行 Hackathon GitHub、Sheet，不勾选参赛或使用比赛额度。实现进行中；不改冻结实验制品，不提交 Git。
根检查评论视为 Braid 以协作者身份发出的普通提醒，不代表业务裁决或验收结论。
本 cell 不接管既有 Pi 恢复修复或实验监控。
两次旧官网工作区的只读逐条分析见[重复协作与状态读取](../results/collaboration-loop-analysis.md)：Sheet 的无行动回执链与 GitHub 的根五分钟重复检查是当前最清楚的低 ROI 模式；此调查尚未修改正在运行的恢复包。
针对时间与 token 的[最小优化方案及验收口径](collaboration-efficiency.md)已获授权并实施于当前源码；正在运行的官网包仍使用旧冻结内容，真实节省待后续对照测量。
[旧冻结运行中 Context reset 的逐次成本与触发边界](context-reset-efficiency.md)是独立只读调查；保留必要重建，是否减少普通追加引起的重建仍待同状态 A/B 判断。
[已决定重建时原 Pi 会话如何自然收尾](context-reset-handoff.md)是独立技术与实施 cell；它不讨论减少重建次数。用户已授权，Braid 源码已接线，真实 Pi reset 时序尚未验收。

## 已确认的产品行为

- 普通回复通过工作项关注关系送达相关参与者；@ 用于邀请或特别点名，不是交接成功的前提。
- 父 Agent 拆分时约定交接位置；子 Agent 完成后回到相应讨论中回复结果及材料。后续移除子项关闭/重开自动通知父项的旧适配，不伪造 Agent 的交接正文。
- 责任、关注关系、工作项状态和执行资源分别表达。关闭后仍应能够通过正常讨论继续联系相关成员。
- 根 Issue 保持开放且其 Agent 连续空闲五分钟时，Braid 添加普通评论：“请检查当前工作进展。”
- 已有待处理输入或会话正在恢复时，不追加该评论；根 Agent 开始执行后重新计时。根 Issue 关闭或运行停止后不发送。
- 根 Issue 开放但暂时无活动时，运行等待下一次检查周期，不立即以 quiescent 退出。明确执行故障仍需报告，周期评论不掩盖故障，也不决定下一步业务行动。

## 设计材料

- [实施计划与开工影响](../cooperation-plan.md)：顺序、责任、接缝和验收安排；[独立预演](../cooperation-preflight.md)已完成，接缝已收敛；当前实施已获授权。
- [当前源码审计与四张图](../cooperation-audit.md)：区分当前行为、断点和目标流程。
- [调查综合](../cooperation-synthesis.md)：范围与取舍。
- [GitHub 行为基准](../github-collaboration-baseline.md)：官方事实、公开样本和未知。

## 下一步与验收依据

当前 Braid 源码已加入 migration 12、订阅及活动历史、具体成员收件与 revision 身份检查、关闭后联系、根五分钟检查、CLI 和持续指引；2026-09-27 Mac `cargo check --offline -q` 与 `git diff --check` 通过。已在旧真实数据库的独立副本上应用迁移：7 个工作项得到 9 条可证实的初始关注；CLI 的 `issue view --json subscriptions` 可读。对副本根 Issue 写入一条无 @ 的真实 CLI 评论，回执显示 @glm-1 与 @deepseek-2 各 queued 一次，后者的收件工作项为已关闭的 Issue #2，事件为 `direct_contact`。这是对象与队列证据，不证明原生输入、Agent 行动或最终评分。

Linux 新构建已完成；独立 ZIP 冻结于 `runs/acceptance-integrity/20260927/cooperation-package/pi-braid-cooperation.zip`，SHA256 为 `e7c81d0bec85534d0ad0ed51ec44f1fe5369658db84a0bb8eed68ae5c0362f1e`。WSL 使用同一 ZIP 启动本地 Lite 两题并行实验 `runs/acceptance-integrity/20260927/cooperation-build/experiment`：Keep=`pi-braid--arc-bench-lite--keep-10fc2c7504fd89`，BookStack=`pi-braid--arc-bench-lite--bookstack-a1b5092108c040`。此处是官方发布 Runner 的本地模拟，并非官网提交。

两条 Lite run 的真实 Braid SQLite 已创建，均已由 runtime 应用 schema 12，根 Issue 均已有首位关注成员。接下来确认真实原生输入、五分钟根检查及两题完整生成/交付；评分可作为后续额外证据，但不再作为本次进入 Hackathon 的门槛。不得把编译或副本操作当作整体验收。

早期真实运行观察：Keep 已生成 5 个 Issue、5 条运行中的物理 turn，BookStack 已生成 6 个 Issue、2 条运行中的物理 turn；两题原生 Pi 会话文件仍持续更新。Keep 根 Agent 最初在评论中误用 `@glm`/`@deepseek`（配置别名）而收到 `unreachable` 回执，随后自行以具体成员名发出更正评论；这是产品指引仍可改进的证据，不等于投递中断。当前评论的具体成员事件已入队，尚待对应 turn 结束后核实消费和 Agent 后续行动。

15 分钟实跑检查发现 Pi/Braid 输入接缝风险：Keep 的 `braid.log` 在 07:12:27 连续两次记录 `Agent is already processing. Specify streamingBehavior ('steer' or 'followUp')`，同一原生 session 的两条 Braid turn 因而在取得 provider turn ID 前标记 failed；07:13:56 又启动一条 running turn。07:12:23 另有改派后旧 session terminal 的 `turn ... is not active`，需独立判断。Pi RPC 的 `get_state` 明确暴露 `isStreaming/isCompacting`，`prompt` 在仍 streaming 且未指定 streamingBehavior 时拒绝；直接使用 followUp 会把等待语义交给 Pi 内部队列，可能破坏 Braid turn 与实际原生执行的对应。已向协调会话报告，官网 Hackathon 上传暂缓；Lite 保留继续运行以收集是否恢复、是否重复的证据。

进一步对应到原生轨迹：Issue #4 的 Pi session 在 07:12:24 收到 `pi-background-bash` 的 `background_bash_result`，Braid 于 07:12:26 记该 turn completed，但原生会话 07:12:35 仍执行后台 Bash、07:12:41 执行 `subagent_wait`，所以 `agent_settled` 不能简单视为此原生会话不再采样。两次 busy 投递失败触发 Store 的失败重放，07:13:56 新 turn 启动，尚无消息丢失证据。另一个改派迟到终态已由数据库确认：旧 turn=interrupted，provider、agent、assignment 均为 retired；terminal 拒绝是已收尾状态的幂等缺口，不是同一个 Pi busy 故障。

讨论中的最小修复方向：Pi 接口以 `get_state.isStreaming/isCompacting/pendingMessageCount` 判定可投递时机，busy 不应先把 Braid claim 标为失败再重放，而应保留原输入等原生可接收后再发送；不能简单改为 Pi `followUp`。改派迟到 terminal 只在同一 turn 已 interrupted 且所属会话/assignment 已 retired 时按已结算处理，仍对其它状态冲突报错。真实验收应再现背景结果与新评论并发，核对没有 busy 失败、同一评论被原生会话接收一次，以及改派旧成员仍被 fence。该方案尚未修正源码，官网大题保持暂停。

暂停能力核查：现有 `lab stop` 对活动进程组发 SIGTERM，宽限后 SIGKILL 并标记 cancelled；Braid 无 pause 命令。暂停整个 Docker 容器虽可冻结文件状态，但进行中的模型 HTTP 请求可能超时，不能保证无损恢复。因此不对这两条未交付的 Lite 生成执行 stop/pause；只读监测继续，官网上传暂停。已用 SQLite 在线 backup 和原生会话文件复制保护两个时间点现场，位于 WSL `runs/acceptance-integrity/20260927/cooperation-build/pre-pause-evidence/{keep,bookstack}/`；完整工作区原件仍在对应 run 目录。用户若决定放弃进行中生成，需接受中断及后续不确定恢复的代价。

用户随后纠正：两次可恢复的 Pi busy 不能直接视作足以阻断官网大题的 Harness 缺陷；应先验证普通协作评论的真实路径及是否出现用户可见漏消息。2026-09-27 在 Lite Keep 的开放 Issue #4 留下一条不含 @ 的外部普通评论 #8：「请检查此 Issue 当前进度和依赖；如有阻塞，请在本讨论说明。」Braid 给两位实际关注者 `glm-4`、`glm-1` 各排队一次；当时 `glm-1` 的 turn 仍活动，事件保持 pending。`glm-4` 的 event 已 consumed、delivery 已 delivered，07:33:19 原生 Pi JSONL 收到含 comment #8 引用的 user 输入，07:34:08 Agent 实际执行 `braid issue view 4 --comments`，随后继续操作。此时日志 busy 错误仍只有先前两次，没有新失败。该例证明评论→关注→queue→原生输入→Agent 行动路径可工作，但仍需关注根成员后续接收与整体验收；Lite 不暂停，官网依更新门槛待两题完整交付且没有实质阻断后启动自费运行。

本轮新门槛以 Lite 两题完整生成/交付为准。当前冻结的本地 `--separate-evaluation` job 会在生成后由同一进程立即发起评分，故不把评分结果设为继续 Hackathon 的前置条件；应保留已有生成证据，不为了跳过评分而中断仍在执行的生成。官网自费 journal 已在 `runs/acceptance-integrity/20260927/cooperation-hackathon-self-funded/official` 本地准备，包 SHA 与 Lite 一致；competition=`hackathon`，tasks=`hackathon--github`、`hackathon--sheet`，model=`glm-5.3-flash`，visual=`deepseek-v4-flash-vision-exp`，credential_mode=`self_funded`。官网公开 API 已只读确认比赛与两题存在；尚未上传或创建远端 run。

验证限制：Braid 普通 `cargo check --offline -q`、release 构建与 `git diff --check` 已通过；完整 `cargo test --offline -q` 未能编译现有测试代码，报错集中在旧测试仍使用已删除的 `ProfileDefaults` 和旧 `SessionFactory` 参数等接口（共 33 处）。这与新增协作行为的运行验证是两件事；本 cell 不顺手重写整套旧测试。

## 2026-09-27 官网执行与 Sheet 回放

后续用户调整了上述 Lite 门槛：两条 Lite 在保存 SQLite、原生会话和工作区副本后已由 `lab stop` 取消，未形成完整评分；WSL 计费容器与进程已退出。当前冻结 ZIP 不变。官网 self_funded 快照 `b235fb4d2565` 的 GitHub run `38dc20e99fa5` 继续运行，远端 `billing_mode=self_funded`；Sheet 生成 run `979a3b837210` 在 `RUNNING` 时依用户新策略受控取消，远端确认 `CANCELLED`，取消证据见 `runs/acceptance-integrity/20260927/cooperation-hackathon-self-funded/official/sheet-cancel.json`。监控只按 30 分钟采集与审查，不重新启动取消的 run。

昨晚 WSL Sheet `recovery-v4/runs/sheet-6cab5e8fa56937` 只完成了生成：根 Issue CLOSED、交付 commit `e1cf426cec8c`，导出前后端应用；该恢复没有评分。其 `requirements.yaml` SHA256 `9cddf67be50748106289ed158648629a6c50c30a490d0eda5bd570c557440b96` 与官方公开 Sheet 需求相同。现成应用被封装为独立 `artifact-replay`，本地回放入口验证可交付前后端且不调用模型。冻结 replay ZIP SHA256 `9a098830cb5005a801ba13e9fa1426f77a4d622b88106922212da93b9e062734`；官网自费、非参赛快照 `dc87fa7a7a8c` 的 Sheet 评分 run `1397a33b9504` 已启动，远端 `billing_mode=self_funded`。这次结果衡量旧应用的部署和评分，不等同于新一轮端到端生成。

该 replay 的官网评分现已终态：`1397a33b9504` 为 `FAILED`，但官方计数为 58/100 通过、42/100 未通过，功能项 8/24，得分 58.0。准备环境、运行入口、评分三个阶段均完成；日志显示回放入口交付既有应用、前端构建成功、后端监听 3000。官网 `tests=[]`，失败原因为泛化的 “Runner exited with test failures or runtime errors”，因此不能归因到具体 42 个场景。远端 `billing_mode=self_funded`、`token_cost_usd=0.123566`；回放入口没有模型调用，但平台费用字段来源尚不明确，不声称零费用。原始状态和日志在 replay 的 `official/tasks/hackathon--sheet/` 下。

用户随后授权重新运行一次新 Sheet 生成。旧生成 run `979a3b837210` 远端仍为 `CANCELLED` 且 `can_resume=false`；现用完全相同的冻结 `pi-braid` ZIP 建立单题自费快照 `a23fff519c26`，新 Sheet run `20a1cfd5dec9` 已启动，首次远端状态 `STARTING`、`billing_mode=self_funded`。其 journal 为 `runs/acceptance-integrity/20260927/cooperation-hackathon-sheet-restart-self-funded/official`，独立 30 分钟监控复用现有固定审查指令；原 GitHub run `38dc20e99fa5` 的监控仍继续。三条 Sheet 身份分别是取消的生成、旧应用的 replay 评分、此次新生成，分析时不能合并。

09:12 监控核查：GitHub 08:03/08:33/09:03 三次、Sheet 08:28/08:58 两次均按 30 分钟下载官网 workspace ZIP，并运行一次性 `gpt-5.6-luna/low` 内容审查。GitHub 08:33→09:03 的 develop 从 `d31aebf` 到 `7497a388`，Issue #2 CLOSED、PR #1 MERGED，原生会话从 3 增至 6；审查读到自检 42/42 与 Issue 代码写入。Sheet 08:28 的 ZIP 尚无 Braid，08:58 已有 6 份原生 JSONL、PR #2 MERGED 到 develop `44f245f`、3 个活动 turn。Sheet 的 08:58 审查却误称 ZIP 没有原生会话，是实际漏读。监控已改为在每批 `required_reads` 明列 Braid status 和最新两份 Pi JSONL，审查必须精确列出已读路径；进程重启时立即持久化真实 PID，便于确认守护存活。

即时 09:12 补采双题 ZIP 与固定审查已完成。两题官网仍 RUNNING/生成阶段；GitHub 相对 09:03 的 develop/对象状态暂未变化，两个最新 Pi 会话出现 JSON 解析错误、请求超时和终止；Sheet 相对 08:58 的 develop/PR 状态暂未变化，但原生会话在 09:00–09:03 写入首页、工作簿新建页、编辑页和样式，随后 09:08 一次请求超时。补审查实际读取 Braid 状态及四份 Pi JSONL，均判 `needs_review`：当前有实质工作和可恢复性未知的 provider 错误，尚无持续无进展或整体阻塞证据，不据一次错误取消付费运行。下一轮 30 分钟快照将核对错误后的接续与交付。

### 新 Sheet 生成终态与本地接续

新 Sheet 官网 run `20a1cfd5dec9` 于 10:35:43 UTC 以 `FAILED` 结束，生成入口退出 1，评测未开始，官方计数 0/0；这不是旧应用 replay 的 58/100。终态 Braid 记录为 `blocked`、根 Issue #1 OPEN，main=`decb1c97`、develop=`56a93241`、PR #2–#6 MERGED，另有 7 个活动 turn。直接失败链为 10:35:28 Pi 进程收到 SIGKILL，Braid 无法证明该原生会话安全收尾；最后原生工具动作是在 Issue #6 工作树运行后台浏览器检查并读取其输出。浏览器脚本只终止自己启动的 Node 服务、Playwright 配置为 1 worker；平台 ZIP 与日志未提供杀进程者或 cgroup/OOM 证据，SIGKILL 来源仍未知。官网该 run `can_resume=false`，不尝试原地续。

终态 workspace ZIP SHA256 `947085a09e7b3788459ee9c537b40937160461e29fb0fba094bee8800ffad37f` 已原样保存并复制到 WSL `runs/acceptance-integrity/20260927/sheet-recovery-20a1cfd5dec9/`。本地恢复曾误启动：首个 Lab attempt `sheet-08e91c042c787b` 因缺 `submission/support` 失败；第二次 `sheet-4acb7ba2af3e94` 已停止，停止前的模板另存为 `paused-template`，没有本地续跑计划。用户明确改为上传原始官网工作区，让官网自费、非参赛的新 run 接续生成并评分；不能将本地恢复副本混入上传，也不能把新 run 说成原 run 原地 resume。原 GitHub 官网 run 继续独立监控。

此后 GitHub 官网 run `38dc20e99fa5` 也以 `FAILED` 结束，官方未进入评分，计数 0/0。终态工作区原样保存于 `runs/acceptance-integrity/20260927/cooperation-hackathon-self-funded/github-terminal-workspace.zip`，SHA256 `f7db8011d82afa74965e00c52ad1f994e84184d885d517276e57f6019893c0ce`。Braid 日志在 11:34:20 UTC 记录两个 DeepSeek Pi 会话的 SIGKILL，随后因无法证明原生收尾而 `blocked`；对应原生会话末尾仍在执行 Issue #7 的浏览器检查相关工作，未见自行终止命令。信号发送者与是否发生 OOM 未由现有 ZIP 证明。此时根 Issue #1 仍 OPEN，`main` 仍是种子提交，`develop` 已有部分合并成果，不能把未交付的应用当作完成版评分。Sheet 的官网工作区恢复另记于 [实验 e20260927-02](../experiments.md#e20260927-02官网从-sheet-原工作区继续生成)。
