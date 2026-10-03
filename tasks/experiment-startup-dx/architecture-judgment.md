# 实际执行装配与生命周期判决

2026-10-03，独立 advisor 复核。结论是调整实施切面：既有 [DX HLD](../experiment-dx-review/design.md) 的职责和生命周期判断成立，但还没有成为 fresh、prepared 和 SDK child 共同消费的实际入口。`c2274d86` 的 ARC operation 有价值，可以保留；它不能作为本轮架构完成或耗时验收依据。继续逐 backend 增加 wrapper 和检查，会保留同一类故障来源。

本判断依据用户的长期正确、定义与运行数据分离、缩短完整打包/启动/热恢复耗时要求，以及 [全生命周期证据](architecture-evidence.md)。我只读了现有设计和关键调用边界，没有运行模型、Docker 或设施测试。exp19–25 的最新运行情况采用实验 owner 经主 Agent 转交的有界记录，不将派发当作成功启动。

## 三个决定实施方向的缺口

**第一，设施尚未拥有 fresh 的完整装配。** `lab/exp/runner.py::_assemble` 在没有 prepared 时直接返回 workspace；variant 自行建立运行根、解析材料和接入服务；SDK wrapper 再建立自己的路径和服务。现有 `harness-layout.json` 是运行后由 Harness 记录的结果，不是入口前设施提供的装配。exp19 的服务 binding、exp20 的旧资源样本、exp21 的宿主 `/Volumes` 路径进入子容器，分别是这个缺口的表现。修正点是让 fresh 与 resume 消费同一个实际执行上下文，不能仅增加一个更早扫描这些变量的 doctor。

**第二，内部材料仍以整包作为生产和复用单位。** `scripts/package_agent.py::selection/assemble/produce` 对 runtime、技能和支持代码形成整树身份并组入每份 variant 材料。既有共享 store 防止了某些物理重复，但小代码修改仍牵动大材料的枚举、复制、校验和交付。应让 producer 直接消费已冻结依赖引用，产出定义组合；自包含包只在 SDK/Hosted 确实要求它时生成。这是生产合同调整，不是给现有整包再增加一个缓存别名。

**第三，运行状态还以单 attempt 的工作目录为主要生命周期。** prepared 路径已经分离定义与状态，但公共 recover 仍要求调用者先交出 checkpoint，再复制 state 制作 prepared 和新 attempt；writer closure 及同域状态交接仍需 Agent 补齐。与此同时，ARC 的 `workspace path='.'` named output 与 terminal archive 会各自发布整树。同域热修复应保留域内 state，只快照必要状态、替换变化定义并启动新执行；终态工作区应只有一次权威封口。否则启动接线即使不再报错，也不能兑现热恢复与空间目标。

## 将已有 HLD 落到公共合同

不建议新增中心服务、全局调度器或通用插件注册框架。需要的是以下合同贯穿现有 producer、controller、backend、runner 和 variant 的实际 caller；字段可在 LLD 收敛，语义不能继续由环境变量猜测。

| 合同 | 必须表达的事实 | 唯一负责的边界 |
| --- | --- | --- |
| 定义组合 | variant 入口、角色到不可变 artifact/ref/member 的关系、依赖 runtime/工具/技能/facility support、每次运行需派生的输入及必要服务。未产出材料保留明确 producer 依赖，最终绑定实际引用。 | producer 决定材料与依赖；compiler 绑定实验政策和选择。 |
| 目标装配 | 本次执行实际所在 namespace；每个声明角色的引用及 member、该 namespace 可用的路径、读写语义；独立 state 根；实际解释器与入口。 | backend 或 SDK bridge 完成物理部署；共同装配模块产出本地有效上下文。 |
| 执行上下文 | 上述装配，加实际资源服务、遥测 binding、模型公开政策和凭据通道、attempt/incarnation 关系，以及负责启动和关闭的 owner。 | 该 namespace 的共同 bootstrap。父 runner 监督子资源，不伪装成子域服务。 |
| state 交接 | state 的域内位置和持有人、当前唯一 writer、停止与关闭覆盖、快照/来源 checkpoint、下一次获准写入的执行，以及定义变更。 | 现有域动作权威管理交接，Harness 提供一致切点和恢复语义；controller 编排，不成为另一写者。 |

资产内容身份、producer 身份、平台 run、attempt 和遥测 epoch 继续各自存在。上表不要求一个新的万能 execution ID；namespace 绑定使用实际 backend 的 host/container/平台身份及必要本地路径作用域。store 位置和 retention 属于控制面的解析/保留信息，不要求工作负载能够访问控制宿主的 store 路径。

输入成员映射必须完整保留。例如 artifact 的 `member=runtime` 被装到子容器 `/workspace/submission/agent/runtime`，其 `node/bin/node` 对应的 member 是 `runtime/node/bin/node`，不是重新以新 root 计算出的 `node/bin/node`。装配应显式记录 `reference + member + local_root`；角色不通过 basename 推断，跨域只使用明确交付布局映射，缺少角色位置则报告该角色未装配。`harness_layout._identity` 不应遍历并 strict-resolve 其他域的路径来寻找身份，更不能忽略原 member。

同一个装配模块应支撑 fresh 和 prepared。Fresh 先分配 state 位置并装配定义，再交给 variant 实例化原生配置；prepared 在原 native 逻辑路径装配已有 state 和选定定义，再进入恢复入口。新材料可以采用不含 artifact hash 的稳定逻辑角色路径，避免定义升级连带路径变化；旧 native JSONL/DB 内绝对路径继续按原合同保留，不自动迁移或修改历史。

variant 仍拥有 Braid/Pi 角色配置、应用/Git、native 会话、一致切点与兼容性。它消费明确的定义角色和服务，生成归本次 state 所有的 request/原生配置，并输出 Harness 状态声明；不再选择另一套资源 sampler、猜父进程服务或从宿主环境反推材料来源。定义/派生输入/状态的分离因而进入实际运行，而不只留在 layout 文件。

## 共同 bootstrap 的准确职责

共同 bootstrap 是冻结、可独立复用的设施代码，直接被 runner payload 或交付包入口调用，不必增加常驻进程。它根据本次执行需求，在实际 namespace 内解析装配，建立必要服务，传递本地有效上下文，启动 Harness，监督并关闭服务、留下入口与终态事实。SDK wrapper 保留 SDK 要求的参数与文件布局转换，移除自己实现的 ResourceEvidence/collector 生命周期和模型政策解释。Hosted 入口也可复用 bootstrap，能力由平台实际条件限定。

资源服务必须指向实际 workload 范围，持续采样；父进程样本或过期样本不是 fallback。遥测的 ready 和 receiver binding 来自同一服务实例，不再由两处可写变量分别声明。兼容旧 Harness 所需环境变量由同一个上下文派生，不再成为独立事实源。模型政策由 compiler 固定，凭据按名字从获准通道绑定；SDK 子容器处仍核对实际传播边界，不能因父环境存在就认为子环境可用。

这里只要求 Harness 声明的必需服务在入口前成立。可选观测缺失应保留具体缺口，不追加“全部观测正常才准启动”的新门控。服务 close、入口退出和 state writer 全关闭各有覆盖，不能相互替代。对未知启动效果仍沿已有请求/资源身份查询，不自动再建一个执行。

这项改动应同时替换 `runner` 的 fresh 旁路、SDK 生成 wrapper 内的服务实现、variant 对父域变量的猜测；只新增上下文 JSON 而不替换这些消费者，不构成完成。它也不应把 ARC SDK 的 `run_container` 私有接口变成所有 backend 的公共接口。

## 设施代码也必须进入实际生产和部署闭包

最新轨迹进一步区分了“修复逻辑有误”和“运行没有消费修复”：实验 owner 报告 exp23 仍出现宿主路径，是因为宿主 adapter 的修改未进入该 recipe 真正冻结的 Lab 执行代码；随后将处理下沉到包内 `harness_layout`，跳过不存在的 producer root 并退回 package-member，exp25 当时仍未确认模型活动。这是执行代码来源和生产依赖不透明，不能靠继续改包内容错关闭。

共同 bootstrap 的源码归属并不足够。LLD 必须列出 controller、adapter、runner payload、交付 bootstrap 各自由哪个冻结代码资产供给，以及解释器依赖与代码身份如何分别绑定。生产计划从实际入口闭包导出：修改 adapter 使消费它的代码资产失效；修改 bootstrap 使相应支持资产和必须展开它的 delivery 失效；不因此重产不变的 Harness runtime。目标解析的是本次冻结组合指定的代码，不从当前 checkout 或 ambient import 偷取新版本。生成 wrapper 的支持代码也按此规则绑定，不能因生成时宿主已安装某模块就省略生产依赖。

公共计划和状态应能直接回答“这次实际运行哪个 adapter/bootstrap”“改动将重产与安装哪些资产”“旧 attempt 为什么仍消费旧版本”。新代码只进入新冻结配方及相应接续，不修改旧执行身份。若本次要求 retained artifact relation，package-member 不能作为缺少原关系的静默降级；交付布局应保留原 ref/member 与实际位置的显式关系。它不要求 Hosted 工作负载能访问宿主 store，关系可以由控制面负责保留和解析。

## 数据与校验怎样随生命周期改变

独立资产不等于把每个小文件变成 artifact。runtime/工具、variant 定义、共享技能和 facility support 按真实生产依赖与变更周期划分；路径绑定后的原生配置和启动 request 仍留在小的运行派生输入中。定义组合引用这些资产，交付投影明确其包内成员。相同组合与 delivery ABI 可以复用包；Hosted 当前仅接受 ZIP 的事实不能变成内部所有场所都必须展开整包的理由。

Local/Docker 在已有目标资产上直接装配；缺资产才由所在域取得和校验。ARC SDK 当前真实接口包含自包含 staging 和完整 workspace 传输/回收；没有证据证明能跳过这些外部步骤。应先删除设施自身的重复 instrument 组装、重复整树封口和无变化扫描，再在明确 SDK 接口的基础上改其输运。不能删除 SDK 已核对 inventory 中的定义副本而让回执失真。Hosted 的 checkpoint/pause/resume 当前不支持，公共投影如实显示，不以重新生成或应用 replay 冒充热恢复。

同域恢复使用已有域权威管理的 state holder：关闭原 entry 与登记 writer，取得一致快照及持续关闭依据，生产变化定义或派生输入，校验恢复兼容性，交接 state 的写入权给新 incarnation。快照用于保全和回退，活动 state 不因新 attempt 自然复制成完整 prepared。旧 attempt 的冻结输入、错误与关闭记录不可改；mutable state 与 immutable checkpoint 不混成一种 artifact。需要跨域迁移时才输运状态快照和目标缺少的定义，保留同一装配消费合同。Local 无法替换被占用的固定根、SDK 无完整 writer 控制等情况，应按真实能力阻塞该恢复动作，不能用外层 Local PID 的停止代替子容器关闭。

此交接不能复用已经 release 的 execution resource。现有 `capture-begin` 只接受无 writer 的 workspace：先由权威记录 transfer-pending 并禁止新 writer，锁外停止并核对旧 writer，随后由独立 capture resource 持有捕获责任；长停止、复制和构建不占文件锁。旧 execution 可以在关闭其 writer 后 release，但 state 的物理保留不能随之释放。最终交接按 state version、快照来源与新 resource 确定唯一写入许可，不能在 `capture-end` 和 `writer-open` 之间留下其他执行可抢占的窗口。Local 可用同语义的本机持久记录和短锁，不因此建设通用调度器；未受管历史 writer 仍需明确覆盖，单 PID 停止观察不足以建立持续关闭。

验证按其保证实际失效的边界执行：可变源码冻结、跨域接收、状态 capture/repair、实际入口装配。已经冻结的 runtime 引用不再由每个 variant producer 重读；同一解析窗口的 asset readback 由共同调用结果复用。Local 同 UID 下未受保护的外部目录仍可能改变，不能靠永久 hash cache 或 receipt 跳过实际风险。Git/SQLite 状态语义、需求身份、唯一 writer 和传输完整性保留；它们不需要在每个内部函数重复全树哈希。校验收敛的交付应包括删除原重复调用，而非再增加一份证明后让下游继续全部重做。

完整 workspace 只封口一次，named output 可引用该封口的成员或同一 artifact；最终 application 因有独立交付合同可以单独发布。归档、导出和 checkpoint 都消费明确 state/capture 布局，不重新从目录名猜定义。保留依赖资产与恢复来源的责任继续归现有 artifact/store retention，不新增全局引用计数服务。

## 对 c2274d86 的处置

| 已有改动 | 判决 |
| --- | --- |
| `arc-local-generate` operation 与 `arc_matrix` 共用领域 job builder | 保留。它消除了开发者编 raw argv 和混淆外层/内层 backend 的责任；是领域 compiler，不是每个 backend 再发明一种运行生命周期。后续输出共同定义组合和执行需求。 |
| controller Python、SDK source、Harness Linux runtime 分开；`from_production` 保留到实际绑定 | 保留并接入组合合同。物理 profile 和尚未生产的输入有各自真实用途，不以打包前必须全就绪代替依赖计划。 |
| SDK 可消费角色、公开模型政策合并、实际子容器环境读回 | 保留对应边界。迁移到装配/启动的同一入口，不另维护独立 ARC 服务事实。 |
| read-only doctor 共用 admission protocol 2 解释 | 保留。它关闭真实不一致；不把 doctor 扩张成新准入权威。 |
| generated child wrapper 的 sampler、collector/bootstrap、手工 input rebinding | 由共同 bootstrap 和显式 delivery placement 替代。保留真实 SDK 参数转换、容器创建/结束及平台错误原件。 |
| 已有离线材料与 compile 反馈 | 保留原证据范围。没有真实服务/模型运行和完整恢复反馈，不足以关闭当前任务。 |

## 实施和真实耗时验收顺序

先细化上述公共合同及各真实 caller 的迁移表，明确谁生产、谁消费、哪个旧分支删除；同时保留现有行为的完整阶段耗时和数据量基线。这一步应产出可执行的 LLD，而不是再写一份 controller/runner 愿景。既有 HLD 作为权威，本文是本次差距判决；收敛后的稳定约定应更新技术说明。

随后做一条贯穿生产、fresh 装配、实际服务、捕获及同域恢复的受控域路径，带上四个 I14 variant 的公共消费接口。该纵向闭环用于判别合同是否真的能减少材料与状态工作；不是只完成 fresh 就宣称恢复自然可用。SDK 与 Hosted 按相同组合/上下文投影接入，但保留真实 capability 边界。ARC 是重要消费者，需要真实 inner namespace 反馈；不应继续以另一个 ARC 专用 operation 代替公共装配。

验收覆盖三条用户路径，并以实际输入、环境和缓存条件明确的完整操作记录为依据：

1. 打包：冷构建、无变化再次交付、只改一个 variant。记录全部构建/发布/封装时间、读取和输运字节，确认共享 runtime 未重产、内部未再组出完整重复材料。Hosted/SDK 必需交付成本单列而不从总数消失。
2. 启动：从用户启动操作到实际 Harness entry，另记首次真实 provider 活动。确认 SDK child 的角色路径、资源范围与服务实例均属于 child，开发者无需拼环境或 raw argv。已有目标资产的 warm 启动不重新扫描/传输整套定义。
3. 热修复：从获准停止到恢复 entry 和首次恢复活动。保留 Git、Braid、native state 的切点及来源关系，证明是接续而非新生成；同域只改小代码时无完整 state/定义往返控制宿主。跨域迁移单独测量。平台不支持的路径明确报告，不用另一行为填充验收。

同时记录峰值与终态实际占用，区分 COW 逻辑大小、真实新增块、活跃 state、快照、delivery 和 scratch。不能把后台未完成的归档或未来必付的输运从成本中移走，也不能用局部压缩加速冒充完整流程提速。先取得可比较的真实反馈再承诺收益倍率。

当前不具备新一轮模型或远端执行授权；具体反馈输入、范围及完成条件须交给有该授权的 owner 或按任务约定复核。源码编译、离线原件读取可以支持接口正确性，但不能替代上述实际行为。达到这些路径的真实证据后即可结束本轮，不再追加全平台能力统一、中心调度或通用迁移项目。

## LLD 独立纸上预演

已按 [实施准备](architecture-plan.md) 的实际 caller 和失败行为推演，而非运行模拟测试。整体方向可以继续；以下三条必须在开工合同中明确。

| 推演 | 应有结果及发现的约束 |
| --- | --- |
| 只修 controller/status、只修宿主 adapter、只修 payload bootstrap | 三种变更进入实际消费它的代码资产。执行配方绑定全部执行角色，但 Harness definition 不应依赖不影响其内容的 controller 代码；否则共享定义身份变化会再次触发大包重产。需要分别列明生产、目标安装和 delivery 失效范围。 |
| 取得 snapshot 后，原位 derived-input repair 写了一半失败 | snapshot 仍是可靠来源，活动 state 已与其不同。修复由 capture owner 许可，按同一请求接续并记录完成和 state generation；失败保持关闭，完成或从保留快照显式恢复后才能 handoff。原 checkpoint 的内容证明不能描述半修 state。 |
| 新 incarnation 获得同域 state 写权，但旧 attempt 的 archive/export 尚未运行 | 旧消费者必须已经耐久绑定不可变 snapshot；否则它们读取的是新运行的状态，身份正确而证据错误。named outputs、terminal archive、后台 export 和 Console 的读取绑定都须在 handoff 前切换。state 之外不变的日志可以后续独立收尾。 |

另核对 Hosted 的可观测差异：平台内部未必能够取得 platform run/container birth。bootstrap 记录它真正知道的本地作用域与 delivery 关联，controller 根据 API 原件补外部关系；不能为了统一字段要求平台注入不存在的事实。上述意见已交实现 owner 纳入准备稿，不需要新增事务框架或中心协调服务。

复核结果：owner 已将三项失败行为及 Hosted 能力差异纳入实施准备正文，我已读取对应改动，未发现需要阻止该方案进入具体开工复核的新问题。此结论仅覆盖职责、调用接缝与纸上失败行为；实现、物理 writer 覆盖、部署闭包及真实耗时仍按既定反馈范围验证。Controller 代码资产重新生产不意味着重新安装未变化的 Python 依赖 runtime。
