# e20260926-01：官网 GitHub 初步验收

首次登记日期2026-09-26（Asia/Shanghai）。用户通过协调对话明确批准既定单题方案：self_funded自带key，不用比赛额度、不参赛，费用控制不用太在意；一次生成，不扩大题目或自动重生成。

case=frozen-baseline；variant=pi-team-mixed（当前pi-braid前身，保留真实包内身份）。
冻结包SHA256=89452d2d9d602ef49fe3170498b5efdf4d07d724fdd09ac68e13619e4390d92f。
题目hackathon--github，运行名e20260926-01--frozen-baseline--github--g01，官网Competition API；状态目录runs/e20260926-01-acceptance-github/official。
模型配置沿冻结配方，根glm-5.3-flash/high；其它成员GLM/DS Flash，原生advisor K3，视觉DS vision。

目的：观察真实官网生成→集成→自动化验收→交付→评分是否完成，结合原生证据判断既有迭代效果；不是单变量模型对照。
完成条件：一条run终态、保留完整可得评分与运行证据；失败保留原因，不自动重生成。15分钟读取状态，明确异常或终态回报。取消由官网POST /runs/<id>/cancel执行，取消不可恢复但保留日志和产物；本轮不设未经用户要求的金额上限。
当前官方前端index-DCT-RiaL.js说明仅official_evaluation扣队伍预算并进入排行榜，self_funded为未勾选分支；只读团队比赛余额285.862202CNY。证据见source/official-billing/verification.json。
创建snapshot是保存运行包，不是勾选正式参赛；请求显式self_funded并验证回执。未发现独立发布动作需调用。
此实验不依赖WSL，也不包含本地BookStack恢复专用补丁；不能假定官网消除其尚未解释的调度风险。


## 最新范围与启动阻碍

用户经协调对话更新为同包四题并行：arc-bench-lite--keep、arc-bench-lite--bookstack、hackathon--github、hackathon--sheet；全部self_funded不参赛，每run内部最多一个会话使用Kimi3，不扩大为四run全局一个。
Hackathon snapshot已上传，submission=fa60d67568df，尚无任何run_id或模型启动。原先单题冻结journal保留，不篡改其输入来假装从开始就是四题。
冻结包model_budget.mjs在PI_SUBAGENT_CHILD=1时直接跳过限制，两个profile的advisor都用K3。因此现包不能保证最新K3会话约束，停止在snapshot-saved，不创建或启动run。
已向协调对话报告精确边界，建议覆盖原生子会话的单run K3名额修正并重新冻结，或由用户明确仍采用原Braid session语义；未修改源代码或启动实验。四题并发平台是否允许仍待接续时核实，不能假称已并行。


用户随后明确撤销新增K3限制，接受当前包可能多个native K3会话，要求不改源码/不改冻结包直接启动四题。
复用Hackathon submission fa60d67568df；新四题journal分为runs/e20260926-01-acceptance-github/hackathon和arc-bench-lite，均同SHA。原单题official目录保留为snapshot来源，不再调度。
首次启动核验后每900秒观察，优先Lite的harness共性故障；不自动重生成，四题终态后结束监控。


## 四题已启动与独立监控

| 题目 | 官网run |
| --- | --- |
| Lite Keep | b3418aa2425d |
| Lite BookStack | 31cf7c5a597c |
| Hackathon GitHub | d593b9eae490 |
| Hackathon Sheet | 03ad599ebd58 |

用户最终指定不用监控subagent或唤醒LLM的自动化；监控子Agent确认未创建任何后台任务并已退出。
Mac独立脚本runs/e20260926-01-acceptance-github/monitor.py持续运行，无WSL依赖。首次真实取证后Lite间隔900秒、Hackathon1800秒，分别停止终态组；每run保存原始status、workspace.zip及摘要，下载最多600秒（连接30秒）。
比较原生JSONL事件数量/尾部角色与工具名、Braid状态、应用/Git等文件内容摘要；不复制模型私有推理到提示消息。两次工作区无变化只能触发needs_review，不据此自动取消；长工具、无原生证据、下载失败均不等同卡死。脚本不能可靠裁决时保存现场并通知用户，确认后可按用户取消授权调用官方cancel，不自动重跑。
持久提醒写monitor/alerts.jsonl，并尝试Mac桌面通知；桌面通知受宿主权限/勿扰状态影响，不声称能自动向聊天发消息。调度记录monitor/scheduler.json、进程记录monitor/pid和process.log。所有run终态后脚本退出。

启动核验：四题均RUNNING，submission与run自费字段一致；独立监控PID79477首次取得四份可读ZIP、各1条原生会话，无下载错误。scheduler实际保存Lite900秒/Hackathon1800秒。主Agent完成一次验证后结束，不维持等待，脚本独立运行。

四题已终态，2026-09-27 08:20完成即时核验，见[四题结果](results/official-four-status.md)。三题未关闭根任务而quiescent，GitHub SIGKILL及清理失败；均无有效评分。脚本于01:30全终态后正常结束，不自动重跑。


# e20260927-01：保存工作区的交接修复与断点恢复

用户经协调对话最终授权四题在本地WSL同时恢复，优先关注Lite快速反馈；GitHub/Sheet用于挽回昨晚已付费成果，完整交付后制作固定应用包官网self_funded重放评分。没有新官网Harness生成，也不是参赛提交。
保留e20260926-01四个原run及ZIP，恢复副本与原件分离。新Braid包含跨thread参与者、同动作去重和直接父项状态通知；离线旧容器不存在的teardown适配仅在恢复build，见runs/e20260927-01-handoff/offline-recovery.patch。完整来源、二进制SHA、工作区路径和四题ID见该目录package.json。
恢复v1/v2的入口失败记录保留；v3补回官网ZIP省略的Git元数据与执行权限，沿同副本继续。所有既有工作文件保留，未发布私人commit历史无法恢复，已向恢复Agent说明。
并发4，Lite默认每900秒采集、Hackathon每1800秒，脚本触发一次性内容审查，配置唯一来源是当时的监控说明（现已删除）。前两批审查分别出现漏读与缺少事件内容，未作为卡死/取消依据；改进后的首个完整闭环仍在实证验收。
完成标准：Lite取得实际交接/集成及必要本地验证证据；GitHub/Sheet完整应用交付并取得真实官网重放结果。若恢复失败需定位并在范围内修复，不从种子自动重生成或无依据反复付费运行。


网络中断续接（2026-09-27）：recovery-v3四题均因原生模型连接错误终止，未交付；原始错误汇总在runs/e20260927-01-handoff/network/native-errors.json。维护侧09:38:19将WSL默认DNS改为Windows sing-box 172.18.0.2，备份旧配置且无服务重启，新容器实证继承；12次v4/v6官方API无凭据请求返回401。真实模型对照：DeepSeek Flash 2.092秒HTTP200完整SSE，GLM Flash首次60.493秒读取超时，进一步仅复核GLM慢首包，不将网络可达等同所有模型可用。
WSL before-dns-resume/{keep,bookstack,github,sheet}.tar.gz保留续接前应用、Git、Braid数据库和会话（排除node_modules/.cache/.npm），大小分别15407086、35006607、25033609、12970092字节。旧recovery-v3目录及原官网ZIP不动。计划用相同冻结恢复脚本/二进制沿当前工作区新增明确网络恢复交接，四题并行续接；新执行记录须关联v3源attempt。若实际恢复暴露Harness缺陷，先保留现场并向用户给修复方案，不擅自修改。

# e20260927-02：官网从 Sheet 原工作区继续生成

首次登记于 2026-09-27（Asia/Shanghai）。本实验回答官网新 run 能否从失败 run `20a1cfd5dec9` 的原始 workspace 继续 Braid 生成，而不是从需求重新创建根 Issue。来源 ZIP SHA256 为 `947085a09e7b3788459ee9c537b40937160461e29fb0fba094bee8800ffad37f`；原冻结 Harness ZIP SHA256 为 `e7c81d0bec85534d0ad0ed51ec44f1fe5369658db84a0bb8eed68ae5c0362f1e`。仅使用官网 `self_funded`，不勾选参赛、不使用比赛额度。失败的原 run 不支持原地 resume；新 run 保留独立身份和费用。

case=`retained-sheet-resume`，variant=`pi-braid`，题目=`hackathon--sheet`。首次恢复执行按来源关系记录为 `e20260927-02--retained-sheet-resume--hackathon-sheet--g01`：submission `0e0c918e76ec`，run `5d3d5da846d9`，上传包 SHA256 `105dbd0b7df69f00777cf227bc30584f029eb78b5fb85b2215d8a0fedb68c9ec`。平台显示 FAILED、0/0，生成入口在恢复原 Git 分支后遇到旧 SIGKILL Pi 会话的停机证明阻断，未开始评分。这个可读运行名是本地来源记录，**不追改已创建的平台名称**。

`g02` 使用隔离的冻结 Braid 源副本，为旧 provider session 建立精确停机名单，仅适用于已结束的旧容器。submission `1cf4716d6055`、run `65f8764677d3`，包 SHA256 `f686a41c5e5aaa6dcad082caaef1df3e64c122173652fc03be0476b37d1d66be`。官网确认它跨过旧会话停机检查，却在 Pi 进程启动时报告 `runtime/bin/pi: Permission denied`，再次于生成阶段 FAILED、0/0。终态工作区中的 `braid-recovery.log` 保存了每个 Pi 的原始错误。相同入口在 WSL 独立副本里成功恢复多个旧 Pi session 并产生新原生活动，证明状态本身可续；差异是官网 Python ZIP 解包没有保留可执行位，而 `g02` 漏掉原入口的 `verify_package()`。

`g03` 修复仅复用原 `package-manifest.json` 与 `verify_package()`，更新 main、恢复二进制和原工作区载荷的哈希；继续忽略 runner 新给的需求 prompt，使用保存的 Braid request/root。Linux 恢复二进制 SHA256 `ba5100c91c135a95031c2739f1de312471413a917fc08d4211a5c2118fb181ca`，上传包 SHA256 `6b42f80d977167bb92477a52dea5294f055c3c5dbf3e3081a4dbf422b1e3fddb`。本地把 `runtime/bin/pi` 刻意改为不可执行后，原 verifier 实际恢复执行权限（before False / after True）。这验证了当前阻断的修法；完整生成和评分仍由新官网 run 验收。每次新的生成执行递增 `gNN`，新 journal 以 `--run-names` 和 `--name` 设置可读名称；旧平台名不追改。

`g03` 官网快照 `9514cbba05f9`、Sheet run `3445926a1142` 已启动，远端确认 `billing_mode=self_funded`。启动日志已进入原工作区 Git refs 恢复；是否成功接回旧 Pi 会话、完成生成及取得评分仍待原始工作区和终态证明。只读采集按 30 分钟间隔运行，不重复创建 run。

11:57 UTC 的官网 workspace ZIP 已下载至 `runs/e20260927-02-sheet-resume/g03/early-workspace.zip`。`recovery-provenance.json` 仍指向原 run `20a1cfd5dec9` 与原 Braid run `20260927-082825-d9c4f6ea`；原 Issue/PR 仍在，根 Issue #1 OPEN，当前 7 个 active turns。原 ZIP 有 94 份原生 JSONL，新快照有 111 份，11:47 后的新 Pi 会话持续写入。这证明保留 Braid 工作/上下文并恢复执行；不表示旧 Pi 进程身份原样延续，也未形成最终交付或评分。

# e20260927-03：官网从 GitHub 原工作区继续生成

用户授权保留失败官网 run `38dc20e99fa5` 的现场，另起官网 `self_funded`、非参赛的新 run，从其终态 workspace 继续生成，不等待 SIGKILL 来源调查，也不从需求重新建立根 Issue。原工作区 ZIP SHA256 `f7db8011d82afa74965e00c52ad1f994e84184d885d517276e57f6019893c0ce`；独立恢复包路径 `runs/acceptance-integrity/20260927/github-official-workspace-resume/pi-braid-github-resume.zip`，SHA256 `4e8468929101c265c121ddbd620dadeb4a8fca8145f62f2a630ac276a5e14067`。

case=`retained-github-resume`，variant=`pi-braid`，题目=`hackathon--github`，运行名 `e20260927-03--retained-github-resume--hackathon-github--g01`，journal `runs/e20260927-03-github-resume/g01/official`。复用 Sheet g03 的精确旧会话停机名单、原 package manifest 和执行位恢复入口，仅替换来源 workspace、原 run `20260927-080209-0b57147a` 与来源 SHA。包内 manifest 校验成功，恢复入口包含 `verify_package(ROOT)` 且原 workspace 的完整哈希与 manifest 一致；跨容器实际恢复及评分仍由官网 run 验收。旧 run 与 Sheet g03 均保持原身份和状态。

官网快照 `9ad3076df84e`、新 GitHub run `e4e7f35f55eb` 已启动。远端 status 确认为 `RUNNING`、`billing_mode=self_funded`、环境准备完成、生成入口运行中，评测未开始。30 分钟只读采集已接线；原 Braid/Pi 会话接续仍待工作区原始证据证明。

11:58 UTC 的官网 workspace ZIP 已下载至 `runs/e20260927-03-github-resume/g01/early-workspace.zip`。`recovery-provenance.json` 指向原 run `38dc20e99fa5`、原 Braid run `20260927-080209-0b57147a`；根 Issue #1 仍 OPEN，当前 7 个 active turns，涉及原 Issue #1/#3/#4/#5/#6/#7 与 PR #8。原 ZIP 有 204 份原生 JSONL，新快照有 211 份，新增 11:58 的 Pi 会话。故已从原工作继续执行，但尚未交付或评分；新 Pi 进程不是旧进程身份原样延续。

## 2026-09-27：从取消前最后工作区再接续

旧 Sheet `3445926a1142` 与 GitHub `e4e7f35f55eb` 均在取消前保存了 `20260927T133809Z` 的原始工作区。新包只替换恢复载荷和来源身份，保留原冻结模型配方；两个新 run 都是官网 `self_funded`、非参赛，不使用比赛额度。旧 run 和包保持原样。

| 题目 | 新包 SHA256 | submission / run | journal |
| --- | --- | --- | --- |
| Sheet g04 | `b7e1366fb119f79cc65992b8c37a67451c23612d0d2fa32fdea5ecf10403a3af` | `dc1aef22a59b` / `bd7ac1b232ba` | `runs/e20260927-02-sheet-resume/g04/official` |
| GitHub g02 | `ed0d4e6fd0fc9b689a8dbe0d468c55dea437447543abe59c8034b867671f8d85` | `79cb6c472852` / `64e0bebcf6f3` | `runs/e20260927-03-github-resume/g02/official` |

14:11 UTC 的首份原始快照表明 Sheet 沿用 Braid run `20260927-082825-d9c4f6ea`，新 Pi JSONL 从 227 增至 236，实际继续执行。GitHub 沿用 Braid run `20260927-080209-0b57147a`，但根 Issue #1 的 Context reset 在 14:09:45–14:10:15 报 `session is unavailable` 并进入 `blocked`；子 Issue #7 仍有活动 turn。14:19 UTC 第二份原始快照确认根 reset 仍 `blocked`，Pi JSONL 456→458，子项仍在继续。错误正好经过 30 秒 RPC 超时窗口，属于线索，尚不能证明超时是唯一根因。两份 ZIP 分别保存在各自 `early-check/` 下；在保留子项正在进行的成果前，不把 GitHub 运行误判为可完成，也不直接取消。

14:35 UTC Sheet 的下一份原始快照显示 Pi JSONL 236→258、3 个活动 turn、0 个 blocked group；Issue #1/#6 与 PR #1/#10 仍开放，尚未进入评分。GitHub 14:30 UTC 快照显示 Issue #7 已关闭，但其收尾 turn 仍运行；根 reset 仍 blocked。隔离恢复包 g03 的 Linux Braid 已编译，准备精确重试根 reset，并将无法送达已 blocked 成员的直接联系明确记为 unreachable；包尚未冻结或上传，待保存 GitHub 子项最终状态。

14:45 UTC GitHub g02 再次只见关闭子项之间的“无行动项”回执，根仍 blocked、没有新整合，活动的 Issue #7 `terminal_contact` 继续重复。已先保存原始工作区，随后核对 submission `79cb6c472852`、`self_funded` 后取消该 run；官网 14:46:53 UTC 确认为 `CANCELLED`，评测未开始。取消后终态 ZIP 保存在 `runs/e20260927-03-github-resume/g02/terminal/20260927T144744Z/64e0bebcf6f3/workspace.zip`，SHA256 `1e8dd37937e26b568307cb10e2d872bb4beff05fece2cd7e74d272e1ca5487f0`。取消前、后原始包均保留。

GitHub g03 沿终态 ZIP 继续，隔离恢复包 `runs/e20260927-03-github-resume/g03/agent.zip` SHA256 `9f13728ee39c980e7b9bc92b3e42fb4f843440cae3f00ddd5f59a7a69ff769a2`。只重试已知的根 Context reset；Pi `new_session` RPC 启动超时由 30 秒延长至 120 秒并记录原始 provider 错误；无法送达已 blocked 成员的直接联系明确记为 `unreachable`，已关闭项目的 blocked group 不再阻止整次交付。源码快照和 Linux 二进制分别在 g03 目录，未改动旧冻结包。官网自费 snapshot `ba4e781e4d25`、GitHub run `6b45225a668c` 在生成入口失败，尚未启动 Braid 或评分：恢复 SQL 将 `agent_instances.context_pressure` 设为 `NULL`，违反数据库的 `NOT NULL` 约束。原始错误保存在 g03 官网日志及快照中；这次运行不能作为根恢复证据。

GitHub g04 仅从 g02 的同一份终态 ZIP 重试，不复用 g03 失败后的运行目录。恢复入口去掉上述无效赋值，其他 Braid 二进制、模型配置和来源工作区均保持一致。新包 `runs/e20260927-03-github-resume/g04/agent.zip` SHA256 `2a4e5e25caad8d138b685d822dac28cd368a05873fafce04112315ffe6a40dc6`；journal 为 `runs/e20260927-03-github-resume/g04/official`，凭据模式仍为 `self_funded`。确认根 Issue 实际恢复须检查新的原生 Pi 会话和工作项进展，不能只凭官网 `RUNNING`。

g04 官网 snapshot `09649b8393ef`、run `8159d597a305` 在生成阶段 FAILED，未评分。终态原始工作区证实根 Context reset `01a0e333-4d88-72a0-a02e-382de4a49c2b` 已从 blocked 变为 applied，新 Pi 会话建立；但恢复候选查询仍包括已经 CLOSED 的 Issue #7 等子项，旧 Pi 会话无法复原，`issue:pi-deepseek-fast` group 报 `session is unavailable` 并使整次 run blocked。根会话刚恢复即被全局错误终止，不能把此 run 视为正常接续。g05 对恢复候选增加工作项 OPEN 条件，继续使用 g02 原始 ZIP；这只过滤不再需要执行的已关闭工作项，不改变开放工作项的恢复。

g05 的独立 Linux Braid 已在 WSL release 编译；来源 SQL 查询核对表明过滤前有开放根 Issue #1 与已关闭子 Issue #4/#5/#6/#7 的五组候选，过滤后只保留根 Issue #1。冻结包 `runs/e20260927-03-github-resume/g05/agent.zip` SHA256 `15ced25f5deb71c810c664576fcb91824e5aac5543ab5cde6ef8b156dcc3bbc4`，journal 为 `runs/e20260927-03-github-resume/g05/official`，官网凭据模式 `self_funded`；等待远端创建与原始工作区证据。

g05 官网 submission `eca758608f83`、run `435b79927a47` 已启动，远端 `RUNNING`、`billing_mode=self_funded`。15:21 UTC 原始 workspace 快照确认根 reset 为 `applied`、新根 Pi session 的 turn 自 15:16 起持续 `running`，其原生 JSONL 已写入模型回复及工具结果（最后记录 15:21:25 UTC）；Braid 有 2 个活动 turn、0 个 blocked group，根 Issue #1 OPEN。因此**GitHub 从保存的工作区恢复了实际生成**，尚未完成集成或评分。原始 ZIP 与数据库在 `runs/e20260927-03-github-resume/g05/official/early-check/20260927T152145Z/435b79927a47/`。本地 controller 已停止，远端 run 未取消；后续读取沿此 run ID，不再上传或启动相同包。
