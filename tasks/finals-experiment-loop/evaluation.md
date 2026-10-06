# 好的实验设施：标准与验证方法

2026-10-07 配方更正：首次 P1 因设施默认错误使用耗尽 ARC，返回 HTTP 402 `insufficient_balance`，没有真实生成进展。下文原 ARC 路由冻结已撤销，后续验收使用集中维护的当前自费配方；不等待 ARC 充值，不由验收会话自行改供应商。先接通配方冻结与运行网关的实际消费，再由同一独立会话继续已授权使用目标。原失败记录保留，不计为通过；暂停/恢复、生成与接续仍待实际验收。

本页先定义用户要完成的工作，再说明如何观察收益和归因。它不是新增运行门禁。现有代码是否保留，由其对这些结果的贡献决定；组件数量、代码行、命令数和故障数都不能单独决定重写。

## 使用结果

| 需求 | 好设施应达到的可观察结果 | 需测量或核实的内容 |
| --- | --- | --- |
| 开展实验 | 给出 variant、run target、task 就能启动；路由和比赛参数可选；不手工组装 SDK、gateway、collector 或身份文件 | 从输入齐备到实际执行的时间、人工步骤、环境修正与返工 |
| 不必守着运行 | 普通 Python 脚本根据指定来源的费用、native session turn 等事实执行预设操作；聊天和 Console 退出不影响运行 | 策略依据、触发时点、实际操作结果；事实未知时的行为；不重复收费启动 |
| 本地共享、官网自包含 | 自管 target 使用共享 Collector/Backend；Hosted 无需本地服务在线即可执行并保存可导出数据 | 各部署的 CPU/RSS/磁盘和采集开销、断连后的可见延迟/缺口、终态导入 |
| 看懂实验 | Console 展示运行、阶段、资源、费用、日志、应用和评分；Braid 自有视图；Pi-only 正常可见 | 从指定 run 到解释问题所需的原始事件/文件的步骤与时间，身份及新鲜度歧义 |
| 停止、pause 和 resume | 操作作用于正确 run，保存实际效果；pause/resume 保持同一 run，不支持的操作直接说明 | 停止到结果可得/实际进程与容器退出的区间；保留/丢失的进度；Hosted 能力限制 |
| 同 variant restart | 程序和 data 分开，restart 整体迁移 data 并重新装配同名 variant 的程序，创建来源明确的新 run | 应用与原生状态没有遗漏；旧记录不变，旧费用/句柄不重复计入；失败不偷偷换旧快照或新会话 |
| status | 无参数列出未归档且未正常完成的 run，brief 来自绑定的 variant/评测器脚本 | running/stalled 等执行事实和活动判断同时可见；依据时间、缺项和脚本原错可解释 |
| 顺序 stages | 独立 stage 作为 run 依次启动，平台内部阶段保持真实粒度；无需逐次人工派发 | 每个 run 的输入、控制、耗时和消耗独立；没有实验级控制器或重复 attempt 层 |
| 自动三类测评 | 模拟测试、官网重放、题目自带入口直接消费应用快照；评分独立取得 | 应用身份、评测来源和独立错误；公开报告显式选择，隐藏反馈不影响生成或控制分支 |
| 自动保存、事后分析 | 成功、失败和取消都自动回收平台可得的完整工作区、原始日志、评测、消耗与执行配置 | 实际取得范围/时点和缺项；只拿保存材料能否解释、比较与重新使用应用 |
| 环境复杂但使用简单 | Mac/WSL/sfp7/Hosted 的路径、网络、凭据和能力由 target 装配，不由实验使用者临时修正 | 切换 target 是否只改变物理配置；故障是否能定位到正确执行侧与外部响应 |

这里的“自动保存”不虚构强制终止后不存在的材料。显示“取得到某时点的 workspace”和明确缺失，优于把部分数据标为完整，或把辅助证据缺失当整个实验无结果。观测数据、控制结果和文件归档各有真实来源，不互相冒充。

核心控制单位是 run。stop 只停止指定 run，不操作其它 run，也不管理 Python 程序的后续代码。默认顺序脚本在 completed 后接续，stopped 不当作 completed；脚本也可明确调用 restart。停止独立自动化程序与停止 run 是两件操作，文档不能承诺只做后者就阻止前者继续执行。比较标签不能改变控制范围，跨 run 的累计费用必须写清选择范围。

自动结果保存与 archive 标记分开：所有终态都保存结果，archive 仅从默认 status 列表隐藏，不改变终态、停止运行或删除材料。正常完成且评分为零的评测仍是 completed；评测环境/程序未完成才是 failed。

## Simplicity 的具体含义

默认路径不要求使用者填写 request/attempt/container 身份、选择 observer 生产者、停 Console 登记、补写 receipt、运行多层 doctor 或维持前台会话。每次执行自动保存采用的实际配置和原始错误，让机械事实可追溯，而不要求先证明整个环境完美才启动。

维护成本同样重要：新增一个真实 variant、target 或 stage，应修改它所属的配置/接入，不反复贯穿多个控制器、资源账本和 Console 现场协议。必要差异可以有明确边界；不以少写几行代码为由把所有职责塞进一个巨型脚本。也不为一个已知顺序流程引入通用 DAG、策略 DSL、插件总线或多层恢复引擎。

新入口不设内部 capacity、slot、reservation 或待运行队列；调用启动直接尝试执行，失败显示实际环境错误。资源采样与 Docker limits 不成为另一套准入系统。动作记录解释已经发生的调用，不承担未来任务、取消清单或任意 Python 程序断点恢复。

“移除所有 gate/校验”是本轮明确要求。方案逐项说明删除机制，另行明示对路径、秘密、控制对象、收费请求防重复的保留建议，不借“完整性”重新建立证明链。这些建议的理由是具体不可逆损失，而非抽象最佳实践。

## Profiling：必须区分什么

| 时间或负担 | 记录方式 |
| --- | --- |
| 整体墙钟 | 同一任务开始/结束的真实时间，包含工具调用、推理和等待；不命名为纯主动劳动 |
| 主动操作段 | 按步骤记录准备输入、执行命令、浏览 UI、解释结果；不能从总墙钟直接扣猜测值 |
| 执行等待 | 构建、输运、平台排队、模型生成、评测、归档分别记录实际起止 |
| 寻找与排错 | 为定位入口、路径、记录生产者、身份、错误和恢复方式花费的步骤/时间 |
| 判断与交接 | 区分用户真正的实验选择和可由程序处理的机械选择；记录跨文档/主机/UI 的信息搬运 |
| 返工与损失 | 重复打包/输运/启动、丢失生成进度、重复收费风险；说明触发原因 |

不靠访谈声称“节省 80%”，不以模型自然等待掩盖操作负担，也不把一次快查询当成完整实验能力。首次与熟练使用分别观察；测量起点、输入规模、缓存、网络和执行环境随结果保存。当前三个只读样本只能作为信息查阅基线，限制见 [assessment](assessment.md)。

关键时间区间是：输入齐备→实际执行，实际执行→首个原生活动，阶段结束→应用可用，停止/终态→实际进程与容器退出，事件产生→Console 可查询，规则条件成立→控制生效，终态→完整可得归档，应用发布→评分及比较结果。只记录会影响决策的区间，不建立新的追踪官僚流程。

## 独立 Agent 的代表旅程

预演者收到尽量接近用户平日表达的自然实验请求，只说明实验目标、variant 与关心的结果，不附长串接口边界、技术导航或逐步操作清单。它从维护入口自行寻找运行方式，保存步骤、耗时、困惑点和实际结果；遇到能力不足保留原始失败，不让设计者在旁边持续口头导航。运行授权与保护要求仍由现有 packet 和维护设施承担，不用冗长派单掩盖使用成本。

2026-10-06 用户明确提醒，给独立会话的验收消息应尽量接近日常消息，不是长串边界明确的说明。此前独立会话读过设计并收到详细矩阵/约束，属于准备与已知条件使用，不能称为完全无背景的冷启动。可运行交付后的实际任务采用自然派单；需要主会话额外解释的成本单列。

1. 用三个必要参数在已配置的自管 target 开展真实 ARC 任务，观察资源、请求消耗和过程，离开会话后回来读取状态与结果。
2. 用 Hosted 路径完成同类实际目标，区分执行、平台评分和回收，确认自包含记录可导入共享 Backend。低内存结论来自真实 RSS/缓冲/数据规模测量，不从实现语言推断。
3. 分别读取一个 Pi-only 与 Braid 运行，在 Console 找到阶段、费用、原始错误和结果；Braid 页面由其自身实现提供。成功样本与真实历史失败样本都保留。
4. 在已明确授权的真实运行中使用 spend 或 native session/turn idle 条件触发动作，确认采集来源、范围和时点；执行侧读不到事实与 Backend 断流要能区分。观察 stop 与同 variant restart 的实际结果，而非仅有 stop requested；status 的活动判断来自所用 variant 的脚本。
5. 完成同 variant 的 stage1→stage2 restart，确认整个 data 中的应用、原生状态均被迁移，程序使用新 run 固定版本，旧费用和隐藏报告不变成新生成输入。自动执行配置的三类应用测评，验证公开报告选择与隐藏反馈隔离。另验证实际支持目标的 pause/resume，Hosted 不支持时如实显示。
6. 从成功、失败、用户取消的保存材料做一次比较，判断分数、成本、耗时、资源和配置差异；不去现场读取活数据库才能解释历史结果。

这些是验收覆盖，不是要求六次独立收费运行。能在同一真实实验中观察的行为合并；已有原件用于历史读取，缺少的动态能力才安排新操作。新的付费输入、矩阵、策略和停止损失先明确记录并取得相应授权。不得新建假 Harness、模拟 turn、设施测试、smoke 或改名探针来代替真实使用。

2026-10-06 已完成一次独立 Agent 的文档桌面预演，不算运行验收或启动 profiling。原预演关于跨 variant 多路径接口的意见，因用户随后将接续收敛为同 variant 全部 data 迁移而失效；停止/保存顺序、公开反馈选择和执行侧采集与 Backend 断流的区别仍适用。实际行为尚待实现后观察。

第二轮文档预演能够推导 start/status、pause/resume、restart、归档后查回和独立评测；发现三类自动测评启用清单及官网费用模式没有操作入口，现已在 task 配置中明确。同 task restart 保留原 native 执行，需求版本变化由 variant 创建新原生任务状态并继续应用；实际反馈须区分这两种已定行为，不能把下一阶段快速返回旧 completed 当作成功。

本页是独立的实际使用反馈安排，不是实现计划中的信息收集、调查或探索性实验阶段。方案依据当前接口决定形成，实施项直接交付确定功能；真实性能、平台强制取消后的可得数据范围和新实现缺陷按实际反馈报告，不预称已经验证。

## 因果链与架构决定

每个高成本或失败都沿同一条链解释：实验需求 → 实际环境与材料 → 设施的装配/执行/采集行为 → 原始异常或额外步骤 → 对用户结果的影响 → 修正所需操作。随后问两个反事实：环境正常时是否仍存在；保留当前环境但正确划分责任时是否仍存在。

环境容量、网络和平台限制不自动等于设施缺陷；设施错误也不能被“环境复杂”掩盖。一次问题可以同时有环境触发、集成耦合、错误投影与恢复成本。例如旧运行 terminal 仍占槽，需分别核实资源实际存在、配额规则和释放责任，不能仅凭 unknown 字符串宣判。

由此形成工程选择：

- 已有能力满足目标且代价低，复用；不连带保留其无关包装和协议。
- 同一环境事实或生命周期责任在多层重复，重划边界；证明如何消除重复工作。
- 旧职责已经取消，或拆补成本高于清晰的新实现，允许有界重写；不以“必须先发生更多失败”作为重写准入。
- 比较整套重写时，计入迁移、现存运行、历史读取、新集成未知和截止时间；不能只比较新代码行数。

方案必须说明什么新观察会改变选择，同时记录现有设施顺利完成的部分。决赛截止约束交付次序与可承受风险，不替代需求，也不自动授权扩大实验或修改现存运行。

## 独立实际验收：2026-10-06 冻结安排

### 2026-10-07 自然请求：Hosted GitHub Stage1 → Stage2

主会话将 BookStack 发送连接故障交由网关负责人继续修复，要求保留现场，改为使用 `pi-minimal-vv-dx-test` 在官网完成 GitHub 第一阶段后接第二阶段，当前自费配方，不参加比赛，并观察状态、日志及自动保存。北京时间 01:25:51 执行维护三参数入口 `lab start pi-minimal-vv-dx-test hosted github-stage-1`，run `7868abfa67fa4ce096126ccc768e4bde`。不停止或接管同账户其它运行；本次流程仅在第一阶段 completed 后 restart 到 github-stage-2，失败不冒充阶段交付。原件入口 `runs/finals-experiment-loop/validation/github-hosted-*`。当前装配中，尚未取得平台执行或评分结果。

### 2026-10-07 自然请求：WSL BookStack

#### 完成生成与随题评测的接续

主会话修复代理大小限制、身份传递与私有文件回收后，再次授权从保存现场完成 BookStack 并跑题目自带测试。北京时间 01:13:31 调用 `lab restart bf51263913f7414d9d50207deaa417c8`，新 run `a0d8fdab6eea4fe295c1bbcff65bca41`，program version `bab048249d8b542419ad227f3fa72d613e2f867871bba98da4ef9f67dbf90b56`，继续原 native session。此次约一分钟返回；公共 status 直接显示 running 与 Docker resources，实测瞬时内存 438.8 MiB/2 GiB，修正前 unknown 问题已在真实使用中消失。普通 logs 仍只有 runtime 构建信息，费用继续 self-funded-provider/not_collected、金额与币种为空。已通过维护 `lab wait` 等待终态；随题评测采用继承 task 配置中的 BookStack evaluations，确认未自动派发前不重复派发。原件为 `validation/bookstack-wsl-completion-*`；当前尚未完成生成或取得评分。

本次随后失败：网关 request 1 与 3 到 QIANFAN_TOKEN_PLAN 取得 HTTP 200 并 complete；request 2/4/5/6/7 每次约 30 秒出现 `error sending request: client error (SendRequest): connection error: Connection timed out (os error 110)`，日志 connect false。原生多次重试后退出，公共状态明确 failed/exit 1；不是先前 413，也不是有效业务零分。完整网关原错已保留 `validation/bookstack-wsl-completion-gateway-error.txt`。终态约 01:17:44，自动保存约 01:17:56 返回 saved true/errors 空，显式排除 inputs/sdk-workspace/submission/.private/**；本轮无须手工同步容器身份或修权限，保存修复取得实际证据。没有完成应用，默认程序未继续随题评测。

有界只读网络核对显示 WSL 宿主此时对 Qianfan 两个 DNS IPv4 地址分别 HEAD 返回 404、Ark 返回 401，均很快；这不能证明失败请求在容器中从未发送，也不能拿后来可达否定原始超时。日志需要手工找到 producers/当前 run/gateway.log 才能从 502 追到具体发送连接错误，普通 logs 仍不够。已咨询 transport_decision advisor 判断同一已授权配方下的安全接续办法；不扩大不明发送错误的自动 fallback、不切供应商、不盲目重复付费启动。生成与随题评测的目标仍由本会话持有。

advisor 返回的可采用判断是：锁定依赖中 SendRequest 与连接建立的 Connect 不同，connect false 不能直接改判，committed false 仅指代理未向下游提交响应，不能证明上游未受理。约 30 秒与 reqwest 默认 TCP user timeout 一致，但这只是解释候选，未证实具体网络根因。宿主 HEAD 的能力范围已明确，不再重复同一核对；供应商受理与费用目前未知。下一步需执行 owner 修复真实发送路径或由主会话明确更新已冻结的自费接续安排，再由本验收者继续，不能把原样反复启动当作已修复。该 advisor 未启动模型、未改源码；本次无生成/评测在途。

#### 自费配方修正后的实际接续

主会话通知维护入口已接回当前自费配方后，于北京时间 00:53:53 执行 `lab restart e1ce4d6f6a174bb995c74f22e3db3a0d`。新 run 为 `bf51263913f7414d9d50207deaa417c8`，program version 为 `d43168ea42c3435cb51ec0f99ad7015f68ac8e23da23a9b33913270f15d2f4c5`，native_resume true，沿用 session `01a11204-0bfb-74ee-9dc0-8ed3ea67cb60`。冻结配方实际为 self-funded，Flash 路由顺序为 QIANFAN_TOKEN_PLAN、ARK_CODING_PLAN、QWEN，advisor 为 ARK_CODING_PLAN 的 kimi-k2.7-code；路由声明本身不作为全部上游均被调用的证据。共享 runtime 首次部署约四分钟，状态已有 assembly/dispatch 阶段，首次 CLI 返回约 00:58。

容器 00:57:49.221 启动，原生 session 随后保存真实 assistant 响应、read/bash 等工具结果。00:59:07.106 的 pause 回执 exit 0，Docker 实际 Paused true；明确等待 30 秒，00:59:57.657 resume/unpause 回执 exit 0，实际 Running true/Paused false，同一容器 ID 未变。由于独立记录与工具往返，实际暂停区间为约 50.55 秒，不声称严格半分钟。恢复后 01:00:00 至 01:00:27 有新增 read 与模型响应，证明原生执行继续；应用尚在需求/技能阅读阶段，不能宣称应用功能已实现。

01:00:27.885 的原生 assistant 返回 `413 {"code":"body_limit_or_read_error","type":"model_proxy"}`，随后 01:00:33.294 的 stop 回执 exit 0。Docker 实际 01:00:31.211 以 exit 1 退出，停止命令成功但终态属于原生错误导致 failed，不能改写成正常完成或由用户停止导致的退出。本次不因该错误另起付费运行，用户要求停止保存已执行。

公共 status 在容器 running/paused/resumed 时仍为 unknown，原因是远端 worker 的 records 缺少本次实际 docker.json；验收者必须直接只读 Docker inspect 才能确认控制效果。为完成终态保存，将 Mac 已冻结的本次真实 docker.json 原件同步到同一远端 run 的 records，未制造容器身份或更改控制目标。公共 logs 仍只显示 runtime 构建信息，真实活动与 413 要到原生 session 定向查找。自费 spend 为 not_collected、value/currency null，来源说明明确不用 ARC shared-key meter；未虚构套餐单价或把未知记为零。公共过程资源采集也未提供可用分项，本次不能给 collector/gateway 峰值结论。

保存首次失败原因是 inputs/sdk-workspace/submission/.private/model-proxy 下的 root 私有目录不可读。已保留失败回执；停止后将该私有目录整体移至同一远端 run 的 .private/submission-services，原位置保留绝对路径引用，Mac 已取得的同名目录移至本 run 的 .private/recovered-submission-services，未放宽凭据权限、删除私有原件或把秘密带入 data。第一次重新保存因原目录非空发生 rsync exit 23，原错同样保留。最后维护执行保存入口于 01:02:16.222 返回 saved true/errors 空，scope 为 data/workspace、data/harness、records；Mac data 约 37 MiB，容器实际 exited，远端原件仍保留。本次仅修复现场接线与私有存储位置，没有覆盖并行 owner 的共享源码。

本次接续至保存约八分半墙钟。使用负担主要是首次 runtime 部署等待、公共 lifecycle 无法解释真实容器、普通日志不展示原生错误、自费费用未采集，以及终态保存需要两次现场修复。暂停/恢复与恢复后的真实原生活动已有证据；应用质量、严格 30 秒暂停、自费真实账单与完整自动回收无需修复均未证明。原件统一为 `runs/finals-experiment-loop/validation/bookstack-wsl-*`，完整现场为 `runs/lab/runs/bf51263913f7414d9d50207deaa417c8`。

本次派单只要求使用 `pi-minimal-vv-dx-test` 在 WSL 跑 BookStack，运行后暂停半分钟再恢复，查看状态、日志与费用，确认真实进展后停止保存。未附操作导航。验收者从 `lab/README.md` 找到维护入口，于北京时间 00:14:40 调用 `python3 -m lab start pi-minimal-vv-dx-test wsl bookstack`，生成 run `e1ce4d6f6a174bb995c74f22e3db3a0d`。本行实际操作取代此前准备矩阵中 A 的金额策略停止；后续结论只覆盖本次实际动作。

启动阶段已观察到：构建约 839 MiB 的包，组装 SDK 工作区约 2.4 GiB，先传至 WSL 的 `data/sdk-workspace`，然后再传整个 `inputs`。北京时间 00:23:25 仍未返回启动结果，状态统一显示 starting/activity unknown，日志仅 runtime 导出，尚未观察到模型活动。WSL 00:22:29 可用空间约 7.3 GiB。需要另查构建文件及进程才能分清等待阶段，属于本次真实寻找/诊断成本，不是生成耗时。原件位于 `runs/finals-experiment-loop/validation/bookstack-wsl-*`，完整 run 记录位于 `runs/lab/runs/e1ce4d6f6a174bb995c74f22e3db3a0d`；任务仍在进行，尚未证明 pause/resume、真实进展或保存完成。

北京时间 00:25:31 首次返回后读取状态为 failed。Docker 实际 StartedAt 为 00:20:00.357，FinishedAt 为 00:20:28.328，退出码 1；启动返回之前模型已失败约五分钟。原生 Pi session `01a11204-0bfb-74ee-9dc0-8ed3ea67cb60` 首次请求返回 HTTP 402，code 为 insufficient_balance，原错为 `access key balance is exhausted`，request id `2026100700202935341752974272`。没有模型输出或应用实现进展，暂停半分钟/恢复/进展后停止均未完成，不能以建好容器或有 message_end 算通过。首次诊断曾推断需要 ARC 余额或凭据；主会话已更正为默认模型配方接错，后续等待维护入口接回当前自费配方。本次没有切供应商或重复付费启动。

费用采集为 baseline→terminal 的 account-key-window 差值 0 CNY、0 tokens，来自 meter-baseline.json 和 meter-terminal.json，明确 note 为 shared access-key window delta，不是精确单 run 费用。原生 usage 同样为零，但不凭它证明所有费用来源可靠。状态在 lifecycle failed 时仍显示 activity active、brief latest Pi session message，错误响应被当作最近活动；普通 `lab logs RUN` 只显示 package-build 的 runtime 导出，HTTP 402 必须进入 session.jsonl 定向取证才能找到。以上两点属于错误可见性负担。

首次保存为 saved false，rsync exit 23，原因是 root:root/0600 的 auth.json 和 models-store.json 对宿主执行用户不可读。已保留原错到 `validation/bookstack-wsl-save-original.json`，只读取两个文件是否为空及顶层键名，确认均为空对象后，仅将这两个现场文件所属用户修正为原 run 目录的 1000:1000，权限保持 0600，未删除文件或扩大读取权限。随后调用维护执行保存入口，00:27:27 返回 saved true、errors 空，scope 为 data/workspace、data/harness、records；原件为 `validation/bookstack-wsl-save-recovered.json`。Mac 回收 data 约 11 MiB，完整远端现场保留。此操作恢复了本次保存，不代表新运行已修复根因；源码正由原 owner 修改，验收者未覆盖共享源码或提交。

本次从三参数启动到阻塞诊断与保存约十三分钟墙钟，包含构建、重复传输、实际 28 秒失败执行、查询与定向排错，不能称为主动劳动或模型生成耗时。已完成入口实际尝试、状态/日志/费用读取和失败现场回收；未完成的 pause/resume 与真实生成进展仍由同一验收会话持有，待统一装配实际消费当前自费配方后继续本次使用目标，不等待 ARC 可用性。

独立会话持续负责真实首次使用、必要设施修复、实际部署与验证，共享修改与对应 owner 协调，暂不自行提交共享源码。当前等待主会话提供可消费版本与维护入口，尚未启动付费运行。准备时阅读过本任务设计，实际操作若获得设计者口头导航，单列协助成本，不声称完全冷启动独立成功。

本节修订此前将三类评测强套同一 GitHub 应用、将所有模型映射 Flash 的安排。GitHub Stage1 没有真实随题 tests；`benchmarks/hackathon` 自述为公开需求代理，属于 simulate。真实随题测试采用 `third_party/arc-bench/arc-bench-lite/bookstack/tests`，其需求来自同级 requirements。BookStack 的 task eval 与 GitHub 的 simulate/official 结果属于不同来源应用，不能声称三者绑定一个快照。每项实际评测仍绑定自己的不可变应用快照。这里只核对目录来源与维护说明，不阅读隐藏测试内容，也不修改外部评测器。

GitHub 输入固定为 `hackathon--github-stage-1`、`hackathon--github-stage-2`，公开需求来源分别为 `runs/iteration14/timeout-retry-20261004/execution/inputs/github-stage-1/requirements` 和同级 `github-stage-2/requirements`；BookStack 输入来自 `third_party/arc-bench/arc-bench-lite/bookstack/requirements`。交付后保存实际 task 配置与公开需求版本，初始运行不带历史应用、原生状态、费用或隐藏报告。

variant 来源固定：`I14-dx-test` 从 `pi-braid-i14` 派生；名称为 `pi-minimal-vv-dx-test` 的新 variant 从 `pi-minimal` 派生，不引入旧 vv tester/e2e 行为。当前模型通道由公共 `harness/model-recipes/self-funded.json` 选择供应商链，不使用已耗尽 ARC API；旧 P1 的错误冻结与响应原样保留。I14 保持 root `glm-5.3`、fast/visual `glm-5.3-flash`、角色可用 `kimi-k3`/`deepseek-v4-flash-0731` 的实际模型闭包；Pi 保持主角色 `glm-5.3-flash`、advisor `kimi-k2.7-code`。每个 run 冻结实际选中的 deployment 顺序、wire model 与 per-provider 描述，不把不同模型偷偷映射成 Flash，不由验收者临时换供应商。受限模型合计只允许一个 Braid session 使用，保护须按 Braid session 生效；运行矩阵串行，不以子 Agent 数量替代该限制。

不参与比赛，官方生成/重放显式 `self_funded`，不继承历史 `official_evaluation` 或比赛提交身份。费用不限不等于无限运行：下表最多八次生成执行，每个生成 run 以四小时为观察和停止边界，评测由实际平台终态完成。设施失败保留原件，由同一 owner 修复后明确接续，不盲目重发未知收费写入。已冻结应用的独立评测可与下一 stage 并行，不接管其它任务。

| 行 | variant / target / task | 合并动作 | 生成执行数与证据 |
| --- | --- | --- | --- |
| A | Pi / WSL / BookStack | 三参数 start；真实活动后 pause 约 30 秒再 resume；采集已知且大于零的本 run spend 触发一次 stop；同 task restart 完成，应用自动 task eval | 2；原 run pause/resume 身份不变；restart 新 Lab run 沿用原 native session，整个 data 保留、旧费用/records 不迁移；真实随题报告绑定冻结 BookStack 应用 |
| B | Braid / sfp7 / GitHub Stage1 → Stage2 | 三参数 start；由可信 native idle 条件触发一次 stop；同 task restart 完成；completed 后默认 Python 程序 restart 到 Stage2；Stage1 应用自动 simulate+official | 3；同 task 保留 Braid/native identity，Stage2 新建 native task/root、继承完整 data 与应用；公开代理与官网重放共用 Stage1 应用快照，隐藏报告不进 Stage2 |
| C | Pi / Hosted / GitHub Stage1 → Stage2 | 三参数 start，自包含执行；pause/resume 保存不支持原错；两个阶段由默认程序顺序完成、终态导入共享 Backend | 2；平台实际身份、self_funded、Hosted 轻量采集资源、Stage2 原生新任务与应用接续、完整可得回收及导入 cutoff |
| D | Braid / Hosted / GitHub Stage1 | 三参数 start，真实原生活动且出现可确认应用写入后 platform cancel，仅回收不恢复 | 1；取消前最近 workspace 时点、预计损失、实际 cancel 回执、进程/平台终态、可得原生状态/应用/日志/遥测与缺项 |
| 共用 | 本轮生成和评测 run | status 默认/RUN/--all、logs、wait、archive/undo；Console Pi/Braid/评测的状态、资源、费用、日志、快照和评分；Braid 自有对象/session/正文/cutoff 页面 | 默认列表只列未归档且非 completed；archive 不停止/删数据；activity 与 lifecycle 分开；仅靠保存材料可解释成功、策略取消、平台取消及实际失败 |

A 的金额停止采用采集层已归属本 run 的 spend，要求 value/currency/source/actual-or-estimate/as_of 已知且新鲜，第一次大于零触发；unknown 不当作零，停止后不重复启动。estimate 仅在明确价格来源、币种与请求 usage 都可得时采用；不以 route/model 别名证明计价，不为订阅套餐套虚构单价。若 ARC 路径仅终态返回账单且维护采集没有可信实时 estimate，则记录 spend 触发未覆盖；仍可手动停止取得同 task restart 的实际反馈，但不能记为预算策略生效。四小时边界属于另一种停止原因。

主会话已采用本矩阵为实际验收范围：最多八次生成与三次独立评测，不因低分追加。执行与评测交付及必要修复的稳定 owner 为 `/root/evaluation_implementation`，观测 owner 为 `/root/cold_console_profile`；主会话负责公共 API、CLI、automation 与总文档。验收者不提前 review 未交付实现，收到可消费入口后以真实操作反馈，后续文件编辑使用 apply_patch。

B 的 idle 条件固定为本 run 中非 terminal native session 连续两个观察达到 30 秒没有可信原生活动、采集仍新鲜，且不处于 waiting_tool/retrying。保留真实 session/turn 生命周期、最后活动与采用来源；有原生 turn 则用 turn_idle_for，没有可验证原生 turn 则使用 session_idle_for 并注明覆盖限制。读者缺失或未知时不触发，不模拟时间、turn 或停滞。若运行持续活跃直到自然完成而未达到条件，记录“idle 动作未覆盖”，不硬停后冒称触发；可沿该行已授权同 task 接续观察，不增加虚假场景。采集只使用维护程序与其保存摘要，不另起爬官网/日志采集循环。

A/B 控制允许损失仅限本会话自己的在途请求、连接与尚未落盘写入。动作前记录真实 native identity、最近可信活动、应用 Git 状态与停止目的，动作后分别记录终止、应用可得、完整回收和实际清理时点。D 已授权有损平台 cancel，必须先记录最近平台可读 workspace 时点及预计损失；取消可能绕过包内 finalizer，不能将部分回收称为完整最新现场，也不把另起空会话称无损恢复。

评测配置采用维护入口的实际格式后保存原件。A 的 task 使用真实 BookStack 随题 tests，执行在冻结应用独立副本中，默认 hidden；B 的 simulate 复用已有 `benchmarks/hackathon` 公开代理与正式维护运行方法，不另造应用 smoke，保留实际测试源码版本和来源限制。B 的 official 只上传同一 Stage1 冻结应用，self_funded、hidden。公开代理报告只由显式配置选为 Stage2 inputs，隐藏结果不得决定生成提示、重试或下一 stage。各评测失败不取消其它种类、不改写生成结果；业务零分而程序完成仍是 completed。

本轮不单独制造假任务/假模型来取得 failed。真实故障保留原错并修复；若均成功，使用已有真实历史失败读取材料时明确标为历史覆盖，不冒充新版本动态失败。三类评测分别来自正确题目，Console 与比较必须展示来源区别。

原件入口为 `runs/finals-experiment-loop/validation/`，Mac 所有 cache/tmp/控制/回收均在 WorkSSD。逐行保存 task/route/target/program 版本、原始命令和 stdout/stderr/HTTP 响应、控制回执、run/平台/native 身份、快照、回收范围、策略事实、UI 观察。分别记录输入齐备→实际执行、首个活动、规则→动作、阶段→应用、应用→评分、终态→退出/回收、事件→Console 可查的时点；墙钟、主动操作段、模型/平台等待、寻找/排错与返工分开，不猜测纯主动劳动。资源来自真实执行域 CPU/RSS/I/O/磁盘以及 collector/gateway/采样分项，无法分项则明示缺口。

交付通知须提供实际可消费版本、准确 variant 名称、维护 CLI/target/task/route 配置入口、共享服务地址和已知限制。先按维护文档执行，再保留不足及修复反馈；不通过旧 compile/doctor/build/exp 入口绕过交付，不要求逐条口头导航。当前待运行，以上没有验收通过含义。
