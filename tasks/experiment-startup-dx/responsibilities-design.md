# 实验设施的职责与显式操作方案

本方案接续 scheduling-review.md，覆盖用户要求的全部实验设施职责混合，以及独立验收报告的反馈。整体职责方案已由稳定advisor复核，具体CLI参数与caller迁移将在实施准备中收敛；源码仍是主区并行状态与交付 d4ac01dd。这里的组件名称表示现有代码的责任，不要求建设对应服务、数据库或框架。

## 目标与原则

使用者决定执行哪个实验工作、输入哪份材料、在哪运行、是否重试/恢复/评测。设施负责把这个决定变成可靠的单次操作。定义、预算、空闲容量、观察状态或文件存在都不能自行成为下一次执行请求。

降低完整打包、启动和热恢复的耗时，并降低达到可行动判断所需的阅读和手工接线。改进不是让使用者驱动更多低层步骤，也不是用新模式长期兼容隐式调度。必要自动化封装在一次明确请求内，其范围及停止条件可由回执解释。

## 责任与权力

| 责任 | 拥有的决定与数据 | 不承担 |
| --- | --- | --- |
| 实验定义与编译 | cases/models/variants/明确政策；冻结job与输入契约 | 创建待运行队列、预约执行槽、启动运行、自动挑选下一轮产物 |
| 材料生产与交付 | 指定目标的依赖闭包、不可变资产身份、公开交付格式 | 运行state、目标机器绝对路径、私有凭据、运行优先级 |
| Controller公共操作 | 显式请求、目标与输入绑定、操作回执、一次执行的协调 | 扫描未执行job、隐式DAG调度、自动新增attempt、据monitor判定自动恢复 |
| Runner与backend adapter | 已受理attempt的一次入口、实际namespace、服务、限额、所属资源关闭、输出封口 | 选择实验策略、选择评测对象、改写其它运行的决策 |
| 域准入与state所有权 | 具体共享资源的排他/容量；writer出生身份与交接顺序 | 决定下一项工作、替用户排队、用材料hash推导真实停止 |
| 观察、分析与projection | 既定范围的采集、原始回执、观察时间、连续样本、解释与展示 | 平台写入、自动创建或恢复执行、用缺辅助证据改写入口结果 |
| 制品保留与运输 | 资产位置、引用保留、接收字节及耐久回执、显式导出 | 把archive pending当模型仍运行、把普通内容封口当完整checkpoint |
| Harness/native与Console | Harness提供应用/native恢复语义；Console消费明确live/archive接入 | variant重新实现设施服务；Console另建实验控制权或选择运行来源 |

请求者/实验负责人持有策略权；controller处理请求而不持有独立的策略权。runner负责履行已经接受的执行请求。远端平台仍持有真实platform run生命周期，adapter只是按显式请求调用它并记录回执。

## 完整使用路径

1. 维护实验intent并显式编译。编译确定性处理定义与明确政策，材料尚未生产时只形成未解析的依赖计划，不声称这是可复现的最终执行recipe。依赖关系可以描述需要哪种输入，不能描述未来自动触发；模型选择政策若由使用者明确声明，编译可以确定性计算结果并冻结依据，仍不产生运行。
2. 按明确job/交付目标构建其实际依赖；resolve/readiness也只读取这一闭包，包括该目标确实依赖的显式政策证据，不能先碰所有未选production。没有必要提前打包整张矩阵。构建绑定实际生产身份和变化闭包，输出最终严格、不可变的execution recipe；冻结后的身份不能随路径当前内容变化。编译、构建和材料验证的回执不创建attempt，不预约运行容量。
3. 显式请求运行一个job，指定deployment与确切输入。一次请求绑定一次attempt/后端执行；缺材料/容量/可证明来源时返回准确阻塞。若已经产生外部作用，保存原请求并只核对/接续它，不把失败当作一个可随意替换的新请求。
4. 该attempt的runner完成本域装配、所需服务和一次入口。命令返回之后运行继续，限额与终态不依赖主Agent在场。Hosted单run的既定观察可持续，但仅持有观察权。
5. 查看该attempt/run的保存事实。执行结束、输出就绪、导出未完和证据缺口分别展示。真正的执行资源终止后释放执行额度；保留和I/O工作仍归其各自owner，不自动删除历史材料。
6. 使用者显式选择冻结应用发起独立评测。失败重试或恢复也由明确请求触发；不能因为上游就绪、controller重新连接或monitor告警而启动。

以上是操作语义，不是强制使用者手动执行六个命令。一次start可以完成所需装配和标准收尾，一次recover可以完成明确的capture/repair/交接事务。实现可保留现有CLI名称，关键是每个命令的作用范围、身份及结果可直接解释。

## 状态与失败

请求accepted不等于模型started；入口结束不等于全部输出完成；观察失败不等于执行失败；普通workspace快照不等于恢复checkpoint。控制命令只读取它需要的当前身份与物理事实，stop不等待workspace下载、全包核验或native诊断。

状态投影按owner分别呈现execution、outputs、transport、observations、recovery能力，不选一条“最新记录”覆盖所有facet。展示最新attempt可以作为默认视图，但具体操作必须指向选定身份。阻塞说明要表达阻塞哪项操作：不能恢复不等于不能停止；native证据partial不等于应用不能评测。原错误、HTTP状态与具体detail保留。

准入失败不留未来执行队列。外部作用未知时也不自动释放或重发；以原请求作用核对为必要例外，不能把“没有排队”误实现为丢弃部分作用。并行预算是上限，未耗尽不是工作指令。跨域身份、存储保留、完整恢复的writer证明仍保留，删掉它们不能合理降低耗时。

## Agent 与 Human 的 CLI 阅读合同（后续优化设计）

2026-10-03 用户明确要求将 Agent 作为需要理解现场的使用者对待，JSON 经常不是 agent-friendly 的默认交付。本段为 `15a1a2a2` 之后的优化设计，不宣称以下呈现已实现；前轮源码及未关闭的完整打包、首次启动、热恢复验收仍以实施记录为准。

默认输出面向 Human/Agent，按命令的领域语义组织。stdout 是否为 TTY 不决定格式；Agent 通过工具或管道捕获文本仍然是阅读。`--json` 是显式、稳定且完整的程序消费合同。可读输出不等于所有对象翻译成散文：原文本直接交付，适合阅读的结构保持结构，多项结果保留各自身份。目标是减少理解和正确行动的工作，而非只减少字节或反对 JSON。

Status/monitor 使用同一 projection，默认回答当前执行事实、影响所选动作的阻塞和证据缺口、下一合法操作及其条件；`--details` 展开完整诊断，JSON 保持完整字段。必须在首层保留明确 job/attempt 和平台身份、具体错误、影响决策的 unknown/partial、各事实的来源与观察时间。旧 resource_wait 或 native 活动不得作为当前终态运行的阻塞展示；若存在身份冲突或当前 writer 风险，则冲突自身仍在首层。详情入口是精确命令或已保存原件路径，不让调用者再次猜目录、重建运行树或选择 JSON 字段。

Build/start/control/recover 的结果说明此次实际完成或受理的作用及对应身份，区分材料冻结、执行受理、入口确认、终态、封口和运输。发现预期输入缺失时指出对象、缺口、合法下一步及参数条件；没有授权、身份或事实支持时不生成可直接重发的写命令。不加统一的 success/data/metadata/next_actions 包装来替代各动作合同。Help 按本动作说明参数、重入与副作用，采用现有 argparse，不建立第二套发现协议。

查询成功读取失败、取消或仍在运行的 attempt，与查询命令本身失败是两个事实。限时观察结束不取消执行，不授予 retry；CLI 退出码与领域终态分别表达。状态结果走 stdout，过程与命令错误走 stderr；实际执行的原生 stdout/stderr 按既有合同保留，不能机械分流而改变入口行为。有界等待中的只读轮询不同于已删除的配置驱动调度，不能仅凭轮询外形判断越权。

有限呈现明确哪些信息没有展开，提供续查路径；不通过静默字符串裁剪消除具体错误、HTTP 状态、partial/unknown 或分页边界。完整原件已经保存时直接引用，不为摘要再复制或重新采集；如命令确需交付尚未保存的大内容，完整结果仅写到明确的项目外置磁盘目录，同一次操作交付路径，不使用系统临时目录。内容是否收起不改变原事实、身份或执行许可。

参考相邻 SVC 的 `docs/prd/corpus.md:23`、`docs/prd/development.md:26` 及 `cli/src/svc_cli/cli.py:_render_status/_render_lookup/_render_error`：默认文本按命令语义呈现，下一步含原因和必要命令，发现从单层浏览逐步到精确正文。参考 InKCre/core-py 的 `tasks/knowledge-lifecycle-capabilities/units/cli-sink/output-presentation.md`、`list-error-contract.md`、`tasks/knowledge-lifecycle-capabilities/common-patterns/agent-tools.md`。其设计支持上述原则，但当前 `cli/src/inkcre_cli/output.py` 对对象默认仍主要 pretty JSON，长内容为字符预算落盘；部分默认 HTTP 错误文字未显示结构化状态。因此采用职责与交互原则，不把参考实现当作完整达标模板，不复制其临时盘策略或固定截断方式。

## 改动形式与边界

采用一套新写入合同，不增加auto_start开关或scheduler mode。移除常驻controller的job/retry扫描，入口转为一个选定job的显式执行请求；旧冻结executor继续只读/原控制合同，新写入不通过旧调度模式。已有producer/attempt/platform/stream身份分别保留，relation不重写。

采用现有模块完成责任调整，不先按表拆出八个服务。沿公共调用路径删除职责旁路，使stop/query不途经诊断采集，使普通结果不途经完整恢复证明，使消费已有资产不途经无关工作生产。公共操作可以协调多组件，但被调用组件不能再自己决定实验策略。

新的批处理调度器、事件总线、中心状态数据库、万能trace ID及通用workflow engine均不在本轮范围。未来明确批处理需求另行决定，不为删除scheduler提前造一个外部scheduler。

## 已核实的全路径调整

| 调整 | 主因与落点 | 保留边界 |
| --- | --- | --- |
| 删除隐式初次派发、DAG启动和retry mailbox调度 | controller的常驻循环把recipe当工作队列；详见scheduling-review | 单次请求幂等、真正容量约束、已受理runner继续履行 |
| 计划与物理冻结分开 | compiler/environment做整树内容认证和平台legacy格式解释；production review第1节 | 显式policy仍可计算；ARC领域lowering保留；已有producer原身份和来源hash不改 |
| 生产范围按请求消费闭包确定 | build先生产全部productions，global producer lock包含慢节点和跨角色交付；production第2节 | 组件生产仍有锁与失败回执；无需新DAG调度框架 |
| 公共定义、私有输入、部署位置分别失效 | private输入和store进入delivery缓存；runtime.py全文件进入Python依赖key；production第2/3节 | 位置/retain索引可有store身份，不能伪装成可移植内容身份；Python依赖与实际ABI冻结 |
| SDK每次只采用一种满足方式 | 全delivery树和同组件daemon RO placements成为双前置；production第3节 | 受管SDK新写入唯一采用薄启动材料+已认证placements，删除双前置；Hosted仍明确自包含；官方SDK inventory不改造 |
| 装配、入口和服务有一个权威 | Local/SDK/delivery各造语义，四main复制分派，run有服务fallback；production第4节 | 场所的真实mount/process/API差异由adapter提供；variant持有native配置和应用语义 |
| 控制与进度采集分开 | main control→live observe→ZIP下载，交付与main同ABI成本不同；execution表第1/2行 | 身份GET/原pending核对保留；现有provider/liveness采集继续由原owner完成 |
| 执行终态/容量独立于发布与归档 | Docker真正退出后，release仍在seal/archive后；execution表第3/4行 | unknown创建/停止不释放；state卷、holds、原进度不因release删除 |
| 发布与运输按消费者请求分开 | export同时补seal、archive、transport、resource finish；export资产集合仍可过大 | 一次公共动作可协调有限步骤，各步独立回执；只运输选定reference/member的必要闭包 |
| recovery作为有副作用事务 | domain-state持capture、执行repair；generic prepare也有该作用；execution恢复行 | snapshot-copy可以纯派生；同域修改显式request/generation/类别与中断接续，不走缓存生产 |
| Console登记与query分开 | query路径可能执行consumer-register | 初次登记明确；后续query无登记副作用；旧live不自动读新writer，archive来源固定 |
| projection不承担状态仲裁及调度 | 选整条latest记录、controller错误灌入stage、归档缺口改顶层blocked | latest仅展示默认；各facet来源/时间保留；候选动作不是授权 |

上表覆盖本轮发现的职责混合，不把普通文件复用、跨组件协调或真实多场所差异都列为错误。具体源码链由两个稳定owner报告及主Agent projection报告提供；未复查的其它仓库组件不宣称已完成全面审计。

## 恢复操作的可理解边界

同域恢复不是将capture藏进build。先验证明确checkpoint与目标兼容性，再对明确state generation执行有限repair事务，保存已修类别与实际输出，然后绑定新装配/运行请求。源码build和定义验证应尽量先完成，缩短保持可变state租约的区间；仍有未能前置的真实条件时在请求回执中明确。

同一request的query/continue只解释或完成该事务；中断时不会创建第二writer，不通过TTL或自动rollback丢掉已经修好的进度。abort只在能确认writer/helper停止且记录明确保全状态后结束事务；不默认复原或删除新旧state。是否接续模型执行必须是原请求明确包含或使用者随后发出的start，不能从prepared ready推导。

恢复的公共语义明确分为prepare-only和恢复执行请求：前者不启动入口，同域repair依然是有副作用操作；后者明确授权完成准备/capture/repair/交接并启动一个派生attempt。不会默认改变现有纯派生recover的运行权限，也不会在prepare ready后自动推导start。具体命令名由实施准备确定，但请求必须显式携带这一差别。

snapshot-copy是另一种明确输入获取方式，保留源不可变快照和自己的作用回执；不能为了看起来统一让它也长时间占原域repair lease。普通内容副本与managed acquisition保持原区别。SDK不支持官方resume不等于通用Harness prepare受支持，也不能反过来混称。

## 实施依赖与删除点

第一批贯通显式执行请求、单run observer与轻量控制：删除work/retry扫描、未分配DAG启动、controller级wait/排队提示及跨不相关job的全局阻塞。同步CLI/request mapping/backend受理/projection，确保删除scheduler后终态采集仍有唯一owner；不能只删除循环导致无人收尾。

第二批贯通消费驱动build与场所装配：缩小生产节点和锁/代码闭包，拆private/store/public身份，SDK薄交付替代双全量前置；删除四main的设施分叉、variant服务fallback和generic package按名字/源码猜能力。所有新消费入口采用同一认证/映射语义；不先新增schema再留下旧旁路。

第三批贯通资源收尾、capture/repair/transport和事实投影：执行容量关闭不等待归档；recovery副作用从immutable production路径移出；运输只随consumer请求；Console登记/query分开；状态facet及验收报告的具体呈现问题一起修。普通交付不受完整恢复覆盖缺口阻断，完整恢复仍不弱化证明。

三批属于一个整体设计，按依赖交付，不是三个可长期并存的模式。每批公共路径闭环后才能冻结给实验owner采用；整轮完成仍要同时满足全部职责和既定实际验收。合入保留main并行修复，包括3074b476的缺manifest说明以及现有provider监控；不以整文件替换省略三方采用。

## 验收与反馈

独立验收对d4ac01dd仅部分通过：保存事实的status/monitor与真实离线compile可用；完整打包、启动、恢复及整体会话成本没有通过。主区缺manifest错误说明必须保留，资源详情、证据路径及多实验比较在现有projection/index边界处理。

行为验收覆盖：build/status/monitor不创建执行；显式start只对应一个选定job；同请求不会新增attempt；容量或输入后续变化不触发运行；生成结束不启动评测；control不先下载workspace；执行结果与归档各自独立；单次执行仍能在请求者离开后监督并记录终态；capture/repair失败保留原进度、来源与writer约束。

性能反馈必须来自同条件实际材料及已授权实验。分别记录材料生产/封装/传输，域装配/service ready/首次入口/首次模型受理，capture/repair/缺资产补齐/交接/恢复入口耗时。模型耗时、平台排队与设施耗时分开；同时记录读取字节、重复哈希/复制/上传、峰值空间、必要修复次数与用户首次可行动判断时间。禁止把compile的20.328s或小源码资产0.062s外推成全流程提速。

不新增Factory/Braid测试、模拟fixture、smoke、自检或另起探针。没有合法新checkpoint或具体模型/Docker运行授权时，完成可独立实施与编译的部分，并明确哪条实际验收仍缺输入，不用静态审阅填补。

## 设计采用与剩余阶段

主Agent采用两位稳定owner的生产/执行调查及 storage_judgment 独立HLD复核。Reviewer要求的三条硬边界已经补入：resolve/build只触达选中闭包、SDK单一薄交付合同和各角色独立失效、恢复请求的prepare-only/单派生执行差异与中断处理。未新建框架、注册中心、测试或隐藏调度模式。

整体设计完成，后续实施准备围绕上述三批落点细化实际字段、公共caller迁移和删除清单。此文是任务方案，尚未修改或替代已发布的运行文档；不能让读者误以为新源码已经采用。三类真实性能与生命周期验收仍未完成。
