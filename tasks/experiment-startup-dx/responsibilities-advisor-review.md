# 实验设施职责复核：独立架构判断

本文是只读调查后的设计建议，不是源码开工或验收通过记录。事实分别来自主工作区当前源码和独立交付 `d4ac01dd`；不把未合入交付当作主区现状。没有运行测试、Docker、模型、网络采集或控制在途实验。

已结合稳定负责人的 [生产调查](responsibilities-production-review.md) 和 [执行调查](responsibilities-execution-review.md)。两份报告提供精确 caller 与行号；本文负责横贯这些接口的取舍，不重复各 owner 的全文调查。

## 判断与完成标准

应同时修正执行权、事实权威和生产生命周期，不能只拆分 controller 文件。设施可以自动完成使用者已经请求的一次执行或恢复事务，不能因为定义里还有 job、产物已经出现、容量恢复或观察到失败，就自行决定下一次执行。定义是可执行内容的描述；预算是上限；两者都不是待执行队列或持续派发授权。

这里的“显式”是公共调用中有明确的执行对象、输入、目标和请求身份，不是要求增加确认弹窗、授权字符串或让 Agent 手写底层控制原件。一个高层调用应隐藏装配、依赖安装、一次入口启动、监督和收尾的机械步骤。

本轮完成应同时满足三个条件：所有新执行都有直接来源请求；查询与监控没有创建执行的能力；定义、状态、产物、输运和观察各自只有明确的事实权威，使用者不再靠手工读取多份 JSON 拼出操作对象。打包、首次启动和热恢复的真实耗时必须下降或有明确未完成解释，不能只用模块拆分代替反馈。

## 调查中最重要的三个根因

第一，当前 controller 把定义解释为调度策略。主区 `lab/exp/controller.py:701–747` 自动遍历未分配 job，选同 job 最新 attempt 的上游结果并派发下游；`736–739` 还安排 Hosted competition 的等待顺序。交付 `controller.py:735–866` 保留了相同职责。它不仅多了一个两秒循环，还使“重启 controller”可能恢复未来的创建行为。相反，主区 `runner.py:56–105` 对单次 dispatch 的身份与失响应保护、`933–991` 的限额与终态收尾属于一次请求的执行闭环，应保留。

第二，多个状态被压成一个总状态，随后又通过检查去补救。主区 `controller.py:683` 将 archive pending 计入 retry 活跃容量，普通 job 路径却按 execution 终态计算；`control():950` 在控制前调用 live observe，Hosted observe 又可能在 `hosted.py:471` 下载整个 workspace。交付 projection 以多种生产者中时间较新的整条记录代表 attempt，再把 observer/archive 或 controller 的缺口影响到执行阶段。应分开执行、输出、输运和观察事实；观察滞后不改变实际执行退出，归档失败不重新获得执行权，readiness 也不拥有资源排队权。

第三，独立组件身份尚未完全变成按需求生产和装配的生命周期。交付具有 definition、delivery 和域内 assembly，但 builder 仍存在整组生产，SDK 路径还可能同时传自包含 delivery 和安装同样的共享组件。冻结 controller/source 的闭包也会影响实际部署成本。需要明确选择每个场所的物理交付策略和依赖闭包，不能把每种可靠机制全部叠上去，再用缓存和重复验证缓解成本。生产 owner 的报告将给出实际调用和完整证据。

## 推荐的最终职责

| 边界 | 自己拥有的事实与自动工作 | 不应承担的决策 |
| --- | --- | --- |
| Experiment intent / compiler | 解释 cases、variants、模型与显式实验策略；校验可表达性，生成执行定义与生产需求。领域 score policy 可消费已明确选定的冻结证据并记录选择结果。 | 不安装、占槽、启动；不从正在变化的“最新运行”暗中选输入；不把完整原始平台格式解析散入通用编译器。 |
| Build / producers | 从使用者指定目标的依赖闭包生产缺失或变化资产；冻结来源，发布组件和必要的 delivery 投影。目标依赖内部的确定性执行可以自动完成。 | 不构建所有未选任务；不以 run 目录、观察器代码变化、无关 private input 变化触发全部材料重建；不启动实验入口。 |
| Controller 公共命令 | 接受一个明确执行或控制请求，绑定输入与目标，完成请求幂等映射，调用对应 owner 并返回可查询回执。 | 不常驻扫描定义派发 job；不做自动 retry、下游评测、fallback、自动切模型或目标域。 |
| Single-attempt executor / bootstrap | 安装已选择的依赖，建立实际 namespace/context，启动一次入口；完成必要服务、限额、控制、子资源关闭与结果封口。Hosted 则拥有一个已指定 platform run 的提交阶段和终态观察。 | 不选下一个实验；不因 entry 失败自动重开 main；不把父宿主位置或服务事实当子执行域事实。 |
| Monitor / analysis | 按既定目标和频率采集、保存原始状态、形成有时间与覆盖范围的分析；继续观察已授权的运行直到约定终态。 | 不派发、修复、恢复或触发评测；不因监控调用而隐式安装；不在每个 status/control 前运行昂贵采集。 |
| Control / Console | 对明确 attempt/incarnation 执行 stop、pause、resume 或已声明的服务修复；Console 是公共查询与控制的客户端。读活动状态和取得写访问分别表达。 | 不成为第二个派发、writer 或恢复权威；不靠猜 workspace、container、mount 建立事实；不把附加观察缺失当作交付失败。 |
| Admission / state authority | 前者管理实际域的容量与资源效果，后者在同一域权威内管理 state holder、唯一 writer 与 capture/handoff。保留真实出生、失响应与 CAS 约束。 | 不选择待运行 job、等待最合适机会启动或发明跨域中心调度。执行资源释放不等于删除其状态和证据。 |
| Recovery | 对明确来源和已选择的修复完成 capture、prepare、状态修复及一次写权交接；保证原生路径、Git/Braid/native 的来源和切点。 | 不选“最有希望”的检查点、回退有效进度、改变模型/需求，或根据错误自动新建恢复执行。 |
| Artifact / transport | 内容身份、引用与保留属于 artifact；域内位置、缺失内容安装与传输回执属于 transport。成功消费后释放本次拥有的 scratch。 | 不因传输失败重跑模型，不以 archive pending 长占执行槽；不定时清除无关历史材料；不将 artifact identity、member 与物理位置合并。 |
| Projection | 根据各事实生产者投影 execution、outputs、transport、observation 与可用操作；给出原错误及证据入口。 | 不用“最新一条记录”覆盖其它事实，不把展示默认 latest attempt 用作执行绑定，不让读视图制造行为。 |

这些是合同，不要求每行新增模块、进程或服务。controller 可以继续作为公共命令的名称；admission 与 holder 继续共用既有域权威；monitor 可以由一次执行请求建立有界采集责任。没有必要引入通用 workflow engine、全局事件总线或新的任务数据库。

## 公共操作应表达的语义

`compile` 生成计划与所需生产，不运行或安装。可读取必要 schema、声明与选定证据；大资产全量扫描和生产留在真正冻结可变输入的 build 边界。未 build 的计划不伪称已冻结字节。

`build` 明确目标及场所，生产其依赖闭包并返回可启动定义。build 内可以自动安装构建依赖和执行 producer，这是本次请求的工作，不是实验调度。doctor/readiness 只指出缺失与适用能力，不替 build 执行安装，也不占用执行资源。

一次 `start/run` 请求明确一个 job、冻结输入或来源 attempt 的 named output、执行场所和限额。设施完成一次 attempt 的创建及派发。相同请求重入只返回或接续同一已受理操作，不能增加一次执行。未受理且容量不足时立即返回原因；物理效果不明时返回原请求的 unknown，不能换请求偷偷补跑。`from_job` 可以作为编译期尚未绑定的输入需求，但启动必须落实到准确产物及来源，不能选择最新 attempt。

`retry` 是使用者要求新执行的普通请求，记录 retry-of 关系并约束输入/预算；无需依赖常驻 controller 消费信箱。它不是自动错误策略。暂停后的 resume 保留原执行身份；新恢复入口则创建新 attempt，两者不能共享模糊的“继续”语义。

一次显式恢复执行可以作为完整事务：使用者指定来源、目标与已冻结修复，设施完成所需停止/一致 capture、prepare、唯一 writer 交接和启动一个派生 attempt。先将不依赖现场切点的代码生产与安装准备好，再取得 capture，减少停止窗口。另保留明确的 prepare-only 操作供离线审阅；它不启动模型。具体命令命名在 LLD 收敛，必须在调用前清楚表达是否包含停止与新入口，不能复用含糊参数暗中升级副作用。

恢复事务不是通用策略引擎：每一步由已有 owner 执行，只保存请求、真实效果及来源关系。半失败保留原状态和当前责任，允许同请求查询/接续或明确取消/恢复；不得通过超时自动放开未知 writer，也不自动回退。普通 terminal-content-copy 保持不可变内容的合同，完整 checkpoint 仍必须绑定发布时真实的 managed acquisition；不为减少状态数合并这两者。

`status`、`monitor`、`wait` 面向明确的 attempt 或显式选定集合。wait 等待用户指定的阶段或终态，不等待 controller 进程存在与否。运行结束、结果封存、输运完成、平台评分可分别等待。操作命令只核对当次效果所需的轻量身份和真实域权威，不附带整个资产重验证或全 workspace 下载。

## 生产与校验的必要取舍

不需要另建一个会排队的生产调度器。由一次 build 请求对选中目标做依赖闭包求值即可；未变组件以原引用复用，同一操作窗口避免重复校验。可变源码在冻结时检查，跨域安装在接收边界验证，实际装配核对位置和只读能力；查询和控制不重新验证无关 runtime/skills 全树。不能采用永久“已校验”标志掩盖 Local 可变风险。

每个 backend 应选择一种执行装配策略：原生域使用共享不可变定义并独立 RW state；受管 ARC SDK 已有真实组件挂载，推荐薄启动交付加已认证 placements，删除 bootstrap 对完整 delivered roles 的重复前置要求。SDK 接口要求的根入口、依赖文件和工作区 inventory 仍由 adapter 满足，不能擅自删除官方现场。Hosted 等只接受自包含材料的外部平台继续使用 delivery 投影，单独报告组合/压缩成本。这是场所能力决定的两种物理投影，不是让同一新 SDK 路径同时维持两套装配来源。

private 输入属于部署，不应默认成为大型公开定义的重建键。若某平台只能接受包内 private 材料，保留受限交付投影并明确其成本与权限；不是删除凭据权限保护。控制代码、执行代码与 payload support 按实际 import 闭包冻结；只改变 projection 的代码不应使 Harness runtime 重产。

生产 owner 已证实：`environment.produce_materials` 先遍历全部 productions，`package_agent.produce` 的大锁跨多个组件与 pip，SDK bootstrap 同时要求自包含角色和挂载角色，controller 的整个 exp 源码闭包以及 runtime.py 整文件哈希扩大失效范围。这些均应在本轮删除或改归正确 owner，而非留成“未来性能优化”。组件锁保留，但只覆盖该生产请求。variant 声明所需角色/native能力，设施不再按 variant 名字或源码字串猜能力；四 main 的设施分发与服务 fallback 迁到同一 bootstrap，variant 保留自身 native 配置和应用生成。

执行 owner 已证实：Docker 当前可能在终态归档成功后才 release 执行资源；Console query 可能隐式 consumer-register；generic prepare producer 能进入 mutable domain-state repair。应分别改为实际 writer 终态后释放执行责任、显式 attach 后轻量 query、仅显式恢复事务拥有可变状态修复。保持独立 capture 责任与 state retention，不是 finally 无条件释放所有东西。现有四个 admission query channel 是同一 registry 的通道，不应误称四个状态权威或为此新建中心服务。

终态结果的必要封口和 telemetry flush 保留为执行收尾。大型诊断收集按声明政策或显式 collect 进行。执行槽在真实执行资源关闭后释放，状态保留由 holder/artifact retention 承担，后台封存只读不可变 snapshot。若某资源物理上仍在运行，或数据还在被 writer 使用，不能为了显示可用容量提前释放该责任。

## 分批交付而不保留双模式

第一批 hard-cut 执行权：替换旧 `start experiment → work scheduler`；迁移全部公共调用者到一个显式 attempt 请求，移除初始分派、自动下游、latest 绑定和 retry 信箱调度。同步修改 monitor/control/wait/projection，否则删除 scheduler 会丢失 Hosted 的观察责任，或 UI 仍暗示后台会继续。旧冻结记录可读，已运行入口按原记录控制；不为新定义保留 `scheduler=true/false` 两套启动语义。

第二批完成生产与场所装配：基于第一批选定执行对象，build 只生产其依赖闭包；收敛 SDK/shared/delivery 的物理策略、私有输入与代码闭包失效范围。迁移四 I14 和 Hosted/Local/Docker 的实际 caller，删除重复包装与重复装配。不得靠一个新 facade 包住原整组生产而宣布完成。

第三批完成恢复、保留和输运：公共恢复执行封装已有的捕获/修复/交接责任，先准备再停止，旧消费者转向原 snapshot。执行容量、状态保留、终态输运的责任分开。该批完成前不得把“fresh 能启动”称为完整 DX 交付。三批是可审阅的实现提交顺序，不是长期共存的产品模式；最终合入和文档应指向唯一新合同。

每批应删除被取代的入口和调用链，而不是另加同义入口。无需全仓搬文件、重命名全部对象、修改历史 identity、统一所有平台能力，或引入新通用权限/审批框架。保留已经有明确收益的组件定义、实际 namespace、冻结闭包、一次 workspace 封口和 acquisition 区分。

主线已经增加的有效行为需要逐项迁移：Hosted provider 连续观察及原始错误不能因采用较旧交付被覆盖；`3074b476` 的 checkpoint 来源 add_note 应保留。迁移保留行为及历史记录，不保留新的隐式 scheduler 启动模式。投影按各 owner 的事实分别组合，最新 attempt 仅作为展示默认；不能用 controller 故障覆盖各 attempt 的真实终态。

## 本轮阶段与不需要交给用户的选择

用户已经明确所有职责混合均需处理，并要求推进；当前对话同时约定先集中完成整体设计与 advisor 复核，再展示具体实施范围。本轮应交付这个设计及后续 LLD/迁移计划，不边调查边写源码。这里没有影响 HLD 的缺失用户偏好：是否显式执行、是否 hard-cut、是否保留数据、性能目标和禁止设施测试均已明确。命令命名、模块归属、请求字段与提交顺序由实施负责人收敛，不应逐项再问用户。对外报告此次集中复核对象即可，不把常规工程选择包装为新的授权障碍。

后续真正需要独立确认的是未获授权的实际实验及其输入、模型和完成条件，不是上述源代码职责取舍。实施范围仍限这条实验设施公共使用路径及必要 caller，不借“所有职责”扩展为整个仓库的通用控制平台重写。

已复核主负责人 `responsibilities-design.md` 草案，认可其显式执行权、单 attempt 闭环、分 owner 投影和 hard-cut。集中交付前应在该正式方案补齐三组可实施条件：build/resolve 只触达选中闭包且 generic producer 不修改 domain state；受管 SDK 薄入口与 RO 组件替代双重交付前置，private 和各执行角色代码独立失效；恢复执行事务明确止于一个派生 attempt 的启动或明确 prepare-only，先生产再 capture，失败只接续原操作。Console attach 与 query 的分离亦应写为合同。这些已直接交主负责人，不需要新增用户偏好问题。

## 验收必须回应真实成本

主区 `runs/developer-experience/post-infrastructure-acceptance-20261003/report.md` 明确判定 `d4ac01dd` 尚未通过总体成本验收。12 个真实目录 status 约 0.09–0.16 秒、一次离线 compile 20.328 秒，没有同条件旧版基线；不能证明打包、启动或热恢复提速。历史 368.258 秒与 1,626,564 total token 的会话覆盖不同场景，不能拿单条 status/compile 与之直接比较。

后续沿真实用户任务测量：从明确请求到得到相同可采用结论的墙钟时间与全部参与 agent 的 token；另记录打包、域装配、service ready、入口、首个模型受理、停止窗口和恢复入口。区分设施等待、平台排队、模型工作和报告整理；记录失败/重试、读取证据次数、复制/哈希/传输字节、空间峰值。cached input 仍计入总 token，并发 agent 时长不相加冒充墙钟。

这里没有新增测试、模拟探针或未经授权的实验要求。先用源码、编译及真实现存资产操作关闭可关闭的接口不确定性；完整执行反馈在另行具备运行授权的真实场景取得。若某场所仍缺完整 writer 覆盖，具体标明不支持完整恢复；不能把这个限制扩散成普通输出无法交付，也不能伪造恢复成功。
