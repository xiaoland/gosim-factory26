# 好的实验设施：标准与验证方法

2026-10-07 配方更正：首次 P1 因设施默认错误使用耗尽 ARC，返回 HTTP 402 `insufficient_balance`，没有真实生成进展。下文原 ARC 路由冻结已撤销，后续验收使用集中维护的当前自费配方；不等待 ARC 充值，不由验收会话自行改供应商。先接通配方冻结与运行网关的实际消费，再由同一独立会话继续已授权使用目标。原失败记录保留，不计为通过；暂停/恢复、生成与接续仍待实际验收。

本页先定义用户要完成的工作，再说明如何观察收益和归因。它不是新增运行门禁。现有代码是否保留，由其对这些结果的贡献决定；组件数量、代码行、命令数和故障数都不能单独决定重写。

## 使用结果

2026-10-07 用户明确要求“用得好”，不是只验证能用。本轮判断同时覆盖行为正确与使用成本：独立会话只收到自然目标，不需要设计者补充 cookie、远端环境变量、题目 ID 或构建接线；能从维护命令的简短输出找到状态、原错及结果，而非默认展开完整原生 rollout。记录实际操作/排错次数、来回消息、输入上下文及 token usage（生产者有记录时）、构建/输运/首次活动/结果回收的分段墙钟。没有 usage 时报告缺项，不把字节数或工具次数伪称 token，也不把模型自然等待算成设施主动劳动。

runtime 反馈记录目录逻辑字节与实际占用、组成、构建环境和 cache 条件、冷/热构建、派生组装及跨网实际传输字节。已有基座的小 Braid 修复不应重新安装和输运无关开发环境；已冻结现场、程序来源及实际启动能力必须保持。新包不预装仅为应用开发使用的 Chromium 等材料，其真实工具入口也不能要求实验使用者自己接线。体积下降或命令成功单独不构成通过：必须由真实运行确认能力仍可用，且使用成本获得有条件的实际改善，不凭一次样本声称普遍节省比例。

本次基线为 `runtime-i14-reset-recovery-20261007b`：`du` 实测约 1.1 GiB，其中 `.playwright` 385 MiB、`node_modules` 402 MiB、`bin` 140 MiB、字体 68 MiB。首次完整构建 705.7 秒；两次成功 restart 墙钟分别约 156 和 161 秒，包含组装与输运，不能直接命名为纯传输耗时。更详细的跨网字节及 token 数据尚缺；负责人后续交付须补实际来源，不靠估算填满表格。

普通命令现复用 brief 输出，完整回执显式 `--json`，Python API 与落盘原件不变。补充前真实 d38 status 的表格输出为 258 字节，完整 JSON 为 146,510 字节；status 本来已有 brief，这组数只说明避免默认展开冻结配置的规模，不代表本次 token 节省。独立会话指出单 run 的配方和保存位置仍需翻完整记录，主随后在单 run 输出中补配方、来源、记录路径与保存回执，无参数列表不扩展。实际 P2 输出 saved=true、scope 为 workspace/harness/records、errors 空；d38 没有保存回执，明确显示 unknown。主核对失败 P2 的原生事实时又发现相同时间戳的 timing `message_end` 抢先于 session outcome，使 brief 只剩 failed；Pi DX 状态脚本已改为同时间优先 outcome，消费该保存事实实际返回具体 `502 upstream_transport_error`。没有改写旧 program 或旧 saved status，新默认 start/control/evaluate 仍需独立实际操作验证。

runtime owner 已产生约 640 MB 的 arc-core 原件，移出预装 Chromium、字体和 GLib 浏览器资源；`runtime-i14-arc-core-20261007g` 的来源记录包括 profile、删除项及浏览器 wrapper digest。已有完整基座复制/精简约 5.4 秒，不是从空缓存构建。f 版本全量部署原件 `runs/runtime-i14-arc-core-20261007f-rsync.txt` 记录约 601.4 MB、135.10 秒；此前 d 版本首次同步约 53.96 秒，保留网络/版本条件差异，不把一个耗时推广为固定收益。手工相同基座复制及 Braid/metadata delta 为约 12.7 MB、1.29 秒，但维护入口对 g 缺失 derivation identity 的兼容条件尚未成立，因此不能宣称普通 dispatch 已取得该收益。`runtime-i14-arc-core-20261007f-browser-startup.txt` 只证明 sfp7 宿主 Chrome 可渲染，不证明 ARC 容器内工具可用；无系统浏览器的 CDN/TLS 失败、实际容器安装/缓存及普通默认接线仍由 execution_owner 持续修复，真实模型使用验收尚未取得。

后续已发布默认 j：实占 551,760 KiB（约 539 MiB），维护 `_ensure_remote_runtime` 实际部署到 `/home/yyh/factory26-lab-runtime/arc-core-20261007j-deployed`，同版本再次调用回执 `reused=true`；证据为 `runs/arc-default-deploy-20261007/runs/default-runtime-deploy/records/runtime-deployment.json`。j 的 ARC 容器内在只读 runtime、外部可写浏览器缓存条件下实际打开 example.com，证据为 `runs/runtime-i14-arc-core-20261007j-container-browser.txt`；这是浏览器运行能力，不是生成 Agent 普通工具使用通过。最新 m 从 Docker arc-core 直接产出，不先安装再删除 Chromium，实占 507,260 KiB（约 495 MiB），缓存构建/导出 37.07 秒；原件为 `runs/runtime-i14-arc-core-direct-20261007m-build.txt`。该日志 Braid cargo 层为 CACHED，不能据此宣称源码修改或空缓存构建达到同一耗时。m 尚非默认发布材料；普通接续自动增量、真实源码改动耗时及整体使用 token 收益仍待取得。

无参数 status 实际仍列出装配失败的 `70cab...` 为 starting。已有 CLI 原件明确是缺 runtime-source.json、尚未派发；根因是 assembly 已写进度状态，异常后调用方只在状态文件不存在时写失败。主将确知未派发的装配异常归到公共 assemble 边界，保留具体错误并写 failed，覆盖 start 与 restart 两个正常调用方；平台写结果不明的边界不改。本次仅编译及调用链核实，不制造故障探针，也不改写历史记录来伪造新路径实测通过。

19b 的后续证据又暴露 dispatch 准备异常同样留下 starting；它没有执行句柄或实际远端目录，但这两项缺失本身不能普遍证明未派发。采用 advisor 的实际副作用边界判断：Local helper 部署完成后、create/simulate 调用前保存最小派发意图；公共 start 异常写 status 与 manifest，准备失败为 failed，越过边界后未知为 unknown，保留 start-error 原件。self-test 最终 submit 前保存独立意图，尚未提交的认证/打包失败不冒充已执行。Local worker 派发受理不再直接标 running，等待已有 observer 取得实际运行事实。这些是新源码的边界修复，未制造故障或改写 19b 历史；仍需后续实际接续资格化。

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
| 四个测评后端 | 官网重放、self-test、本地随题、本地模拟直接消费应用快照；评分独立取得 | 应用身份、评测来源和独立错误；公开报告显式选择，隐藏反馈不影响生成或控制分支 |
| 自动保存、事后分析 | 成功、失败和取消都自动回收平台可得的完整工作区、原始日志、评测、消耗与执行配置 | 实际取得范围/时点和缺项；只拿保存材料能否解释、比较与重新使用应用 |
| 环境复杂但使用简单 | Mac/WSL/sfp7/Hosted 的路径、网络、凭据和能力由 target 装配，不由实验使用者临时修正 | 切换 target 是否只改变物理配置；故障是否能定位到正确执行侧与外部响应 |

这里的“自动保存”不虚构强制终止后不存在的材料。显示“取得到某时点的 workspace”和明确缺失，优于把部分数据标为完整，或把辅助证据缺失当整个实验无结果。观测数据、控制结果和文件归档各有真实来源，不互相冒充。

核心控制单位是 run。stop 只停止指定 run，不操作其它 run，也不管理 Python 程序的后续代码。默认顺序脚本在 completed 后接续，stopped 不当作 completed；脚本也可明确调用 restart。停止独立自动化程序与停止 run 是两件操作，文档不能承诺只做后者就阻止前者继续执行。比较标签不能改变控制范围，跨 run 的累计费用必须写清选择范围。

自动结果保存与 archive 标记分开：所有终态都保存结果，archive 仅从默认 status 列表隐藏，不改变终态、停止运行或删除材料。正常完成且评分为零的评测仍是 completed；评测环境/程序未完成才是 failed。

I14 的失败 brief 此前仅显示 failed，即使同一保存 status 的当前 scope provider evidence 已有 `provider session disconnected before terminal receipt`。绑定的 status.py 已在 failed 时采用这些已采集具体错误并保留 agent/source 证据；消费真实 de22 原件得到该明确 brief，没有重新采集、读取 rollout 或改写旧冻结程序。后续正常运行由新 builder 冻结脚本，不为显示修复额外重启 610daf。

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
5. 完成同 variant 的 stage1→stage2 restart，确认整个 data 中的应用、原生状态均被迁移，程序使用新 run 固定版本，旧费用和隐藏报告不变成新生成输入。自动执行配置的应用测评，覆盖官网、self-test、本地随题、本地模拟四个后端，验证公开报告选择与隐藏反馈隔离。另验证实际支持目标的 pause/resume，Hosted 不支持时如实显示。
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

### 2026-10-07 自然请求：sfp7 I14 GitHub Stage1 → Stage2

主会话要求官网入口先等核对、不重复上传，继续在 sfp7 用 I14-dx-test 跑 GitHub 第一阶段，原生会话空闲半分钟时自动停止保存，再同 task 接续完成后进入第二阶段，保持集中自费配方。验收者持续持有此流程，不接管其它容器。启动前只读确认 sfp7 `/home` 为本地 `/dev/nvme0n1p3`、可用约 103 GiB；Mac 控制与证据位于 WorkSSD、可用约 241 GiB。当前公共 native facts 仅有 Pi sessions 的 active/waiting_tool/observed 与时间点，没有明确 idle 或 retry 生命周期；已咨询 advisor，不能把超过 30 秒没有 message_end 直接当作空闲。先取得真实执行事实，再按可信状态判据决定是否触发；缺项保持 unknown，不能伪造自动停止覆盖。

首个 run `26cd033f71ef4ee6bc5c3cd599b8e73d`，program `36a693c9b0dc31db618e2ffc3e21021e3d92c2c2a6617837009910e09020906c`，首次共享 runtime 约 1.9 GiB、装配到启动约三分钟。容器启动后约四秒 failed/exit 1，普通 `lab logs` 直接保留 `run.py:139 KeyError: 'factory26'`。集中配方提供 per-model native routes，I14 仍按旧 provider 级 key 取 endpoint。已改为复用 native_model_route 按实际 MODEL 取 endpoint，原 run 自动 saved true/errors 空，只有 gateway producer 文件，无 Braid request/SQLite/native session，不能声称恢复了原生进度。

明确另起同需求 fresh `004e8a6d54f94c478bf9ce383d2c7afc` 后，生成越过模型接线，在 start_shared_proxy 导入 state_writer 时又失败 `ModuleNotFoundError: No module named 'execution_context'`。共享 helper 的 portless/Popen/等待仍依赖已退役门控，已改为直接 Popen，保留 process_identity 与退出/停止 evidence；本次也自动 saved true。下一 fresh `c3ba31ebccf141f38548eac7dbcde021` 进入 Braid，native launch 的 runtime_resources.py 还有同一残余 state_writer 依赖，导致 provider disconnected、未创建 managed execution processes、teardown unknown。原始 Braid diagnostic 明确包含 missing execution_context，原始 stop unknown 不改写。已移除新包此唯一残余调用，并从 I14 SUPPORT 移除不再使用的 state_writer.py；未将旧门控重新打包。以上均无 provider session 或模型进展。

第三次自动回收因 root 的 process-control/临时目录及 stop/telemetry 文件仍为私有模式、宿主用户无权读取而 rsync 23。原始错误保留 `github-sfp7-stage1-save-permission-original.json`；维护 save 在确认 Docker terminal 后将本 run data 所属用户恢复为 run 根目录的宿主 owner，保留权限位，SDK .private 仍排除。sfp7 sudo 非交互权限已实地确认，修复后对同一真实现场 save 返回 saved true/errors 空；未控制其它运行或迁出远端原件。

独立 owner braid_idle_evidence 复用 provider_liveness 的 SQLite/WAL 快照与 Braid status，接到已有 observer 的 native.braid，限定 manifest.native_scope_id，仅映射该 scope 的容器路径，保留源身份/缺项。真实 Braid 初始状态 pending_events=1、provider_sessions 空，因此当时 idle unknown，控制没有触发。advisor 初步全局静止判据经冻结请求复核后修正为任一当前非终态 provider idle/sleeping，turn 已终止且无工具、重试或未解除恢复错误，连续新鲜观察与 turn/活动/恢复指纹保持 30 秒后，经已有 stop/save API 控制；其它会话在途计数只用于明确预期损失。failed turn 也可进入真实 idle，不能把它当业务完成。普通 Python 控制程序为 `validation/github-sfp7-stages.py`，只读已有 status，不建第二采集循环，Stage1 failed 不派发 Stage2，所有源改动仅编译与实际操作验证，未运行设施测试或提交共享源码。

真实模型 run `3a9346912db449ffa0f8ccbe5fe2ba8e` 越过初始化后产生 39 次成功上游响应，包括 Qianfan GLM-5.3 24 次、Qwen GLM-5.3 10 次、Ark Kimi-K3 4 次及 Qwen Kimi-K3 1 次。末段 Qianfan 返回 HTTP 429 `token_plan_person_rate_limit_exceeded`，冻结 fallback Qwen 返回 HTTP 403 `AccessDenied.Unpurchased`；此前 Qwen 成功记录仍保留，不能概括为始终不可用。会话 `01a11255-8f35-7c80-a58d-eac7c7c3bbc0` 在 failed turn 后进入明确 idle，保存事实连续约 33.9 秒空闲后触发，从程序首次可信 idle 观测到实际停止约 45.7 秒；这不代表原生会话最早进入 idle 的时点。自动保存 saved true/errors 空。原件为 `3a9346912db449ffa0f8ccbe5fe2ba8e-control.json`、`github-sfp7-stage1-gateway-original-all.txt`。异步 SSH 启动原先持有 stdio 导致 CLI 等待执行终态，已在维护 start/spawn/simulate 的 nohup 分支修正重定向和分组；该 run 采用原始 Docker 身份接回已有 observer，没有重复启动容器。

同题接续 `ffb8014cc06c43c480c2583ef9f3335c` 保留 native_scope `3a9346912db449ffa0f8ccbe5fe2ba8e`，但 Braid 启动被 Git `detected dubious ownership` 拦住：保存阶段已交还宿主 owner 的应用仓库再次由 SDK root 使用。原错为 `github-sfp7-stage1-restart-braid-error.txt`，外层缺失 result.json 不是根因。根据 advisor 判断，维护执行在新 run 独占 data 恢复到 root owner，确认 terminal 后保存交回实际宿主 owner，保留权限位、不跟随符号链接，不扩大全局 safe.directory。从该已保存现场再接续产生 `ec254b7b29b8421b9a4f14fdc98abdce`，CLI 成功返回，原 session `01a11255-8f35-7c80-a58d-eac7c7c3bbc0` 创建 UTC 18:18:14 的新 running turn `01a11270-079f-7033-8422-fc3192b15450`，证明越过 Git 错误并恢复原生执行。控制程序此次禁用重复 idle-stop，以第一阶段 completed 作为第二阶段派发前提；随后因供应商阻塞按下述处置停止，第二阶段始终未启动。

随后对 Stage1 run `ec254b7b29b8421b9a4f14fdc98abdce` 做了三次保存事实核对（原始快照见 `validation/github-sfp7-stage1-owner-restart-blocked.json`）。两个当前 provider session 均为 `blocked`，最新 turn 均 `failed`，native `pending_tools=[]`、`active_turns=0`、`pending_events=0`、`pending_continuations=0`、`pending_resets=0`、`materializing_groups=0`；但 Braid 仍有 `pending_batches=1`。定向读取当前 observer-owned SQLite 后确认该计数对应 `wake_batches.lifecycle='runnable'`、目标 `issue:1` 的唯一 batch，关联 pending wake event；两个 assignment/provider session 都是 `blocked`，而 `claim_runnable_turn` 要求 active/finalizing assignment 与 idle provider session，因此该 batch 当前不可执行，只保留未来恢复机会。证据见 `validation/github-sfp7-stage1-ec254-pending-batch-evidence.json`，调度条件来源为 `sources/braid/src/store/mod.rs` 的 `claim_runnable_turn`。当前 403 是本 run gateway 的新记录：Qwen fallback 返回 `AccessDenied.Unpurchased`，Qianfan 也有 429 `token_plan_person_rate_limit_exceeded`；原始定向日志保留于 `validation/github-sfp7-stage1-ec254-gateway.log`。已核对并结束唯一 controller PID 66956，随后通过既有 `run.stop`、`run.wait` 与 `execution.save` 完成停止和保存：最终 lifecycle `stopped`、container exit code `143`、save `saved=true`、errors 空。处置回执为 `validation/github-sfp7-stage1-owner-restart-disposition.json`；未派发 Stage2，停止放弃的是该不可执行 batch 的后续自动恢复机会，未观察到在途模型/tool turn。

接续前又核对了同 task `native_resume` 的实际合同：`lab/arc_bench/restart.py` 会复制 `data`、保留 `native_scope_id=3a934...` 并设置 `native_resume=true`；I14 入口随后使用 retained request 调用 `braid local --offline-resume`。现有 Braid 的 `prepare_offline_resume` 只清理旧 CLI binding；`provider_resume_candidates` 对 `blocked` session 只接受特定 resume error，而本 run 两个 blocked session 的 `last_resume_error` 均为空，故 native resume 会保留它们和 runnable batch，却不会产生可恢复 candidate，`claim_runnable_turn` 也没有 idle session 可领取 batch。该设施边界已记录在上述 pending-batch evidence；没有启动新的 restart、没有改 DB。继续同 task 前需修复并部署该 resume 接线，不能把复制 data 或设置 `native_resume=true` 当作恢复成功。

随后按 advisor 采用的边界，在 `sources/braid/src/store/mod.rs` 的 `prepare_offline_resume` 接入同一 reset 生命周期：只匹配精确的 reset notice 失败、仍保留原生 session identity、无在途 turn/后继 reset/session、事件与 worktree 身份一致的当前 reset；不调用 `record_provider_resume`，assignment 在 reset notice 验证前不释放给普通 dispatch，失败继续 blocked。`claim_context_reset_notice` 仅为 interrupting reset 接受 blocked assignment。Mac release binary 不能部署，实际构建使用远端 `development-2` Docker、Linux x86-64，独立 runtime 目录为 `runs/runtime-i14-reset-recovery-20261007b`，Braid SHA256 为 `d93c345362c27000d09be151bf752ee113b08e795087fd7e59db0ce9b49aac03`；旧 `/home/yyh/factory26-lab-runtime/i14-sequential-20261006` 未覆盖。

首个部署验证 run `63d294eb60094cf6b6100b5ae681cba1` 暴露了条件过严：同 task restart 的 assignment 已被既有恢复路径置为 `active`，因此 reset 没有重试。该 run 已精确停止并保留。放宽条件到 `active/finalizing/blocked` 后，第二个同 task run `d38fa85756f24f13bb5fbb262b3fdf80` 实际消费上述独立 Linux runtime，仍保留 `native_scope_id=3a9346912db449ffa0f8ccbe5fe2ba8e` 与集中 self-funded 配方。远端 SQLite 已读到两个原 blocked reset 均 `applied`，旧 native provider sessions 均 `replaced`，新 root session `01a1144c-5502...` 与 fast session `01a1144c-48d8...` 已物化，其中 `reset_continuation` 已 `completed`；当前 Braid `blocked_groups=0`、`pending_batches=0`、`pending_resets=0`。d38 当前仍在 Stage1 生成，尚未宣称 Stage1 完成或派发 Stage2。

后续定向观察进一步确认：Braid assignments 仍为 `active`；root 最近一次 `wake_batch` 已 `completed`，其原生会话记录 PR #2 为 OPEN/draft、head `84af540`，等待 `glm-1` 承接。对应 fast 新 session 为 `idle` 且没有 JSONL turn。Issue/PR 两个 worktree 当前只有初始化提交 `6c53cd8`、设计文档提交 `84af540` 及未跟踪 `tasks/`，没有业务实现提交。因此当前可确认的是 reset 恢复成功，Stage1 尚未完成，尚无应用冻结提交，也不具备派发 Stage2 的条件。

此前将现象解释为“恢复后缺少面向当前 glm-1 的新输入，需要协作者发出明确实施输入”只是中间推断，已被下面的 lost-wake 证据替代：root 确实将 PR #2 解释为等待调度，但决定性原因是 provider 在普通 turn 创建前失败，旧 wake 被消费且 reset 未重放。

随后确认原始 fast session 的首条实施输入确已到达，provider 在普通 turn 创建前返回 403 `AccessDenied.Unpurchased`；reset notice 自身也以同一 403 失败。由于旧 session 没有可查询的普通 `failed` turn，原 `complete_context_reset` 将 `continuation=0` 并消费旧 wake batch，造成原实施输入丢失。修复 `sources/braid/src/store/mod.rs`：对同一 reset 仅在失败 notice、无普通 turn、且 reset event 可定位到旧 wake batch 时重放原 `wake` 事件，保留原事件身份、失败记录和 reset_continuation；不重放 assign/invalidate，不改变普通 idle 语义。`cargo check --locked --bin braid` 通过。Linux x86-64 独立 runtime 已构建于 `runs/runtime-i14-offline-input-recovery-20261007`，Braid SHA256 `aa307dc50424a538dc7218d3d0d302e12085a13e654e6dc4b9c461b696cd81f2`；部署到远端新 runtime 目录的接续仍在进行，未覆盖旧冻结 runtime。

同 task restart 的实际尝试产生 run `f5cbf353e67742468cb9d1bafd569d24`，使用上述 runtime 但在 Braid 入口失败：原始结果为 `root Issue #1 member glm-root-1 has no resumable session`，同时 `scope_closed=false`、`queued_comment_deliveries=0`，容器 exit 1，未进入模型生成。f5 的远端 `sessions.json` 显示 root 最新物理会话为 `unknown`，而非可恢复句柄；该记录保留于 `runs/lab/runs/f5cbf353e67742468cb9d1bafd569d24/records/agent.stdout.log` 与 `records/status.json`。另有 `19b53703de774619b877bf16c9535c00` 的本地 starting manifest，但 `remote_run` 为空、无 execution handle，不能称为已启动或可消费的接续；其后续选择仍需遵守 root 身份与历史完整性边界。

对 f5 的 root locator 定向核对：root 最新 JSONL 文件实际存在于远端 run 的 native-home，旧 writer 有 `execution-stop.json`、`stopping.json` 与 `children-stop.json`，无 root/`braid local` 进程；Store 中 root assignment/agent 仍为 `active`/`idle`，最新 provider session 为 `unknown`，`provider_session_id` 与 sessions manifest 中的同一 native locator 一致，两个 reset 均 `applied`。因此历史文件与 Store 身份没有丢失，当前失败来自恢复候选未将 unknown root 变为可执行 idle session，随后 `root_idle_tick` 按合同报告“no resumable session”；尚未有证据支持 fresh root 或丢失历史。19b 仍无远端目录/handle，不能作为恢复验证。

### 2026-10-07 自然请求：Hosted GitHub Stage1 → Stage2

主会话将 BookStack 发送连接故障交由网关负责人继续修复，要求保留现场，改为使用 `pi-minimal-vv-dx-test` 在官网完成 GitHub 第一阶段后接第二阶段，当前自费配方，不参加比赛，并观察状态、日志及自动保存。北京时间 01:25:51 执行维护三参数入口 `lab start pi-minimal-vv-dx-test hosted github-stage-1`，run `7868abfa67fa4ce096126ccc768e4bde`，program version `3074e30597a0465fcba24ae4e49232a0cf6650f20c48ff4be048742b2d07b316`。不停止或接管同账户其它运行；本次流程仅在第一阶段 completed 后 restart 到 github-stage-2，失败不冒充阶段交付。原件入口 `runs/finals-experiment-loop/validation/github-hosted-*`。

上传请求明确 `credential_mode=self_funded`，但 Hosted 维护入口仍选择 `catalog=competition`、`competition_id=hackathon`。官网 `/submissions` 返回 HTTP 400，原始 detail 为 `This competition is no longer accepting submissions`，request id 为 `upload-1791307640070984000`；未创建 submission 或平台 run，模型未执行，不能取得应用或评分。只读查询 benchmark（16 题）与 playground（2 题）的公开目录均没有 GitHub Stage1/Stage2。没有改题、切参赛入口或重复上传；第二阶段缺少第一阶段交付与可用官网任务入口，因此未启动。本次约四分钟墙钟主要消耗于 841 MiB 包构建及被拒绝的上传。

公共 status 正确 failed，嵌套 platform.rejected 保存 HTTP 400、请求身份和原始响应，可解释拒绝原因；普通 logs 仍只有 runtime 构建信息，单独使用不足。原自动保存返回 `RuntimeError: Hosted identity unknown; no downloadable result yet`，错误地要求明确未建执行的运行拥有远端 workspace。已在 hosted_run.save 的确定拒绝分支保存 program/inputs/records，并以显式 pre-execution-rejection 标记让 execution.save 接受该范围；未决请求及真正缺失 workspace 的执行仍报错。原失败回执保留为 `github-hosted-stage1-save-original.json`。两个源码文件 py_compile 通过，随后对本次真实 run 调用维护 save 返回 saved true，platform_run_id null，明确 gap 为无平台执行及远端 workspace；保存回执已发布。此次证明修复后的手工保存分支，尚未证明新启动的自动保存闭环；没有编写或运行设施测试，没有提交共享源码。

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

不参与比赛，官方生成/重放显式 `self_funded`，self-test 为私有非排名评测，不继承历史 `official_evaluation` 或比赛提交身份。下表最多八次有效生成执行；按当前 AGENTS 约定，本地自费不默认附加四小时或金额停止线，原表 A 的金额控制只在采集可靠且实验明确采用时成立，不把账单未知变成默认 gate。评测由实际平台终态完成。设施失败保留原件，由同一 owner 修复后明确接续，不盲目重发未知收费写入。已冻结应用的独立评测可与下一 stage 并行，不接管其它任务。

2026-10-07 用户补充官网已知缺陷：创建身份为 `official_evaluation` 时，启动回执即使显示 `self_funded`，实际仍可能使用比赛费用。此为用户提供的平台事实，尚无本次请求可独立复核；保留创建与启动两份原始回执，不仅凭显示字段判定 start 失败或实际自费。本轮非参赛、自费授权不变，不能借该字段误用比赛费用。self-test 当前仍等待用户完成钥匙串授权，未触发认证或提交；本地生成、应用冻结和 Stage2 接续可继续。

| 行 | variant / target / task | 合并动作 | 生成执行数与证据 |
| --- | --- | --- | --- |
| A | Pi / WSL / BookStack | 三参数 start；真实活动后 pause 约 30 秒再 resume；采集已知且大于零的本 run spend 触发一次 stop；同 task restart 完成，应用自动 task eval | 2；原 run pause/resume 身份不变；restart 新 Lab run 沿用原 native session，整个 data 保留、旧费用/records 不迁移；真实随题报告绑定冻结 BookStack 应用 |
| B | Braid / sfp7 / GitHub Stage1 → Stage2 | 三参数 start；由可信 native idle 条件触发一次 stop；同 task restart 完成；completed 后默认 Python 程序 restart 到 Stage2；Stage1 应用独立 simulate+self-test，官网重放保留明确拒绝证据 | 3；同 task 保留 Braid/native identity，Stage2 新建 native task/root、继承完整 data 与应用；公开代理与 self-test 共用 Stage1 应用快照，隐藏报告不进 Stage2；self-test 不冒充 Hosted 生成覆盖 |
| C | Pi / Hosted / GitHub Stage1 → Stage2 | 三参数 start，自包含执行；pause/resume 保存不支持原错；两个阶段由默认程序顺序完成、终态导入共享 Backend | 2；平台实际身份、self_funded、Hosted 轻量采集资源、Stage2 原生新任务与应用接续、完整可得回收及导入 cutoff |
| D | Braid / Hosted / GitHub Stage1 | 三参数 start，真实原生活动且出现可确认应用写入后 platform cancel，仅回收不恢复 | 1；取消前最近 workspace 时点、预计损失、实际 cancel 回执、进程/平台终态、可得原生状态/应用/日志/遥测与缺项 |
| 共用 | 本轮生成和评测 run | status 默认/RUN/--all、logs、wait、archive/undo；Console Pi/Braid/评测的状态、资源、费用、日志、快照和评分；Braid 自有对象/session/正文/cutoff 页面 | 默认列表只列未归档且非 completed；archive 不停止/删数据；activity 与 lifecycle 分开；仅靠保存材料可解释成功、策略取消、平台取消及实际失败 |

A 的金额控制仅作为明确采用时的验收条件：采集层须已归属本 run 的 spend，value/currency/source/actual-or-estimate/as_of 已知且新鲜，第一次大于零触发；unknown 不当作零，停止后不重复启动。estimate 仅在明确价格来源、币种与请求 usage 都可得时采用；不以 route/model 别名证明计价，不为订阅套餐套虚构单价。没有可信实时费用时记录该项未覆盖；仍可手动停止取得同 task restart 的实际反馈，但不能记为预算策略生效。本地自费默认运行不采用此金额条件或四小时停止边界。

主会话已采用本矩阵为实际验收范围：最多八次有效生成，不因低分追加。原三次独立评测的安排补正为包含 self-test：A 的 BookStack 随题评测及 B 同一冻结 Stage1 的模拟和 self-test；官网重放及 Hosted 生成无法执行的覆盖保留实际拒绝与缺口，不换题伪称完成。用户要求四个后端都由设施支持，不代表必须对不可用入口重复提交。评测交付及必要修复的稳定 owner 为 `/root/evaluation_implementation`，观测 owner 为 `/root/cold_console_profile`；独立验收会话持有实际生成与控制，主会话负责公共 API、CLI、automation 与总文档。

B 的 idle 条件固定为本 run 中非 terminal native session 连续两个观察达到 30 秒没有可信原生活动、采集仍新鲜，且不处于 waiting_tool/retrying。保留真实 session/turn 生命周期、最后活动与采用来源；有原生 turn 则用 turn_idle_for，没有可验证原生 turn 则使用 session_idle_for 并注明覆盖限制。读者缺失或未知时不触发，不模拟时间、turn 或停滞。若运行持续活跃直到自然完成而未达到条件，记录“idle 动作未覆盖”，不硬停后冒称触发；可沿该行已授权同 task 接续观察，不增加虚假场景。采集只使用维护程序与其保存摘要，不另起爬官网/日志采集循环。

A/B 控制允许损失仅限本会话自己的在途请求、连接与尚未落盘写入。动作前记录真实 native identity、最近可信活动、应用 Git 状态与停止目的，动作后分别记录终止、应用可得、完整回收和实际清理时点。D 已授权有损平台 cancel，必须先记录最近平台可读 workspace 时点及预计损失；取消可能绕过包内 finalizer，不能将部分回收称为完整最新现场，也不把另起空会话称无损恢复。

评测配置采用维护入口的实际格式后保存原件。A 的 task 使用真实 BookStack 随题 tests，执行在冻结应用独立副本中，默认 hidden；B 的 simulate 复用已有 `benchmarks/hackathon` 公开代理与正式维护运行方法，不另造应用 smoke，保留实际测试源码版本和来源限制。B 的 self-test 上传同一 Stage1 冻结应用，任务 `github-stage-1-req-test`，私有非排名、hidden；精确评测器版本未公开时明示未知。官网重放不因生成提交入口关闭而与 self-test 混同，不重复已确定被拒绝的请求。公开代理报告只由显式配置选为 Stage2 inputs，隐藏结果不得决定生成提示、重试或下一 stage。各评测失败不取消其它种类、不改写生成结果；业务零分而程序完成仍是 completed。

本轮不单独制造假任务/假模型来取得 failed。真实故障保留原错并修复；若均成功，使用已有真实历史失败读取材料时明确标为历史覆盖，不冒充新版本动态失败。四个测评后端分别来自正确题目，Console 与比较必须展示来源区别。

原件入口为 `runs/finals-experiment-loop/validation/`，Mac 所有 cache/tmp/控制/回收均在 WorkSSD。逐行保存 task/route/target/program 版本、原始命令和 stdout/stderr/HTTP 响应、控制回执、run/平台/native 身份、快照、回收范围、策略事实、UI 观察。分别记录输入齐备→实际执行、首个活动、规则→动作、阶段→应用、应用→评分、终态→退出/回收、事件→Console 可查的时点；墙钟、主动操作段、模型/平台等待、寻找/排错与返工分开，不猜测纯主动劳动。资源来自真实执行域 CPU/RSS/I/O/磁盘以及 collector/gateway/采样分项，无法分项则明示缺口。

交付通知须提供实际可消费版本、准确 variant 名称、维护 CLI/target/task/route 配置入口、共享服务地址和已知限制。先按维护文档执行，再保留不足及修复反馈；不通过旧 compile/doctor/build/exp 入口绕过交付，不要求逐条口头导航。当前待运行，以上没有验收通过含义。
2026-10-07 新接续 `de22a0c3d9464c509ac8194bb0f516c8` 实际消费 Linux runtime `/home/yyh/factory26-lab-runtime/i14-offline-input-recovery-20261007b`（Braid SHA `aa307dc50424a538dc7218d3d0d302e12085a13e654e6dc4b9c461b696cd81f2`），`native_resume=true`、source `d38fa85756f24f13bb5fbb262b3fdf80`、native scope `3a9346912db449ffa0f8ccbe5fe2ba8e`。该次重启仍在同一 root native identity 上完成 `resume_count=1`（`last_resumed_at=2026-10-07T03:51:22.965Z`），随后 wake turn 以 `provider session disconnected before terminal receipt` 结束，最终 Braid 仍报 `root Issue #1 member glm-root-1 has no resumable session`；3/3 provider health 均 `error=null, can_progress=false`。因此已排除候选查询过滤和 worker 首次 health 未汇报造成的过早 root idle 判定；当前剩余阻塞是恢复后的 provider turn 断连，不能安全重放该 unknown 输入。原始证据：`runs/lab/runs/de22a0c3d9464c509ac8194bb0f516c8/records/status.json`、`records/agent.stdout.log`、`records/runtime-deployment.json`。
同日随后构建并部署 `runs/runtime-i14-offline-input-recovery-20261007c`（Linux x86-64，Braid SHA `f1b292c48956475b358df30a58b06ebb17a3a88dcd86f11a6a3ac8ff57f8f88f`）启动真实接续 `610daf8655bc4f178cf6b0b35e94cfc7`。该 run 的 `native_resume=true`、source 仍为 d38、scope 仍为 `3a9346912db449ffa0f8ccbe5fe2ba8e`，容器 handle `19574b172848bc27cc0ffdf27443b65ddf912c714e5c51587ed9f2e174cff65f`。保存摘要已观察 root 原 native identity `...pi-glm-root-01a1144c...` `resume_count=1` 且 wake completed；fast 产生新 native binding `...pi-glm-fast-01a11486...` 并进入 `wake_batch` running，原生 JSONL 已实际写入 `backend/src/auth/password.ts`、`backend/src/db/schema.ts`、`backend/src/db/client.ts`、`frontend/index.html`、`frontend/src/main.tsx`、`frontend/src/App.tsx`。这证明旧 applied reset 的去重 wake replay 已被真实执行消费；Stage1 当前仍在生成中，self-test 仍 pending_auth。
