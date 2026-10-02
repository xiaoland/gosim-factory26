# 实验基础设施干净基线方案

2026-10-02，当前为已授权并实施的新基线设计。用户明确支持“hard-cutoff，建立干净基线，可以一步到位，以长期正确为第一优先级”。这一取向取代此前兼容现有operation/recovery、只实施P0的分批方案。本次重新定义完整交付与切换边界，不把改命令名称或增加wrapper当作新架构。调查与决定见[packet](packet.md)，具体实施准备见[preparation](preparation.md)。源码已实施，真实离线反馈与未验证能力见 packet；未控制既有实验。

## 开发工作流修正

用户指出“你没有从正确的层次去改进开发体验”。此前减少重复哈希、复制前源预读和打包双读，是局部成本优化；不能解决开发者仍要准备runtime、制作包、找checkpoint与stop原件、组装prepare、上传及启动的问题。后续主线改为开发工作流、资产生命周期与变更传播，由现有controller/compiler承接，不另建通用工作流服务。下述为修正方案，尚未实现；已有局部改动保留其实际反馈，不视为本方案验收。

负责人维护实验定义，指定Harness源码/材料、cases、模型与评价政策，以及明确目标环境；已知环境与依赖配置有维护入口，不要求每次实验手制controller和runner runtime描述。Compiler/controller解析这些声明及本次变更，确定哪些产物可复用、哪些需构建或传输、哪些需重新prepare。调用者不再把已经准备好的每个物理输入和每条中间命令拼进高层定义。底层recipe仍严格冻结，执行输入不能从后续工作树变化中隐式刷新。

运行定义与运行数据分离首先是生命周期分离，而非目录限制。Runtime、Harness代码/材料、checkpoint和prepared各有来源与失效条件，多个运行引用同一已发布资产。每次运行保存实际消费身份、绑定、attempt和证据，不因为新建运行就全量复制所有资产；执行工作区仍独立可写。共享store必须提供受管理发布、修改边界及失效规则，不能用mtime、普通路径或上次校验回执假定内容未变。现有artifact身份与producer relation继续使用，不引入万能trace ID。

| 开发者的任务 | 设施应承接的结果 | 需消除的重复工作 |
| --- | --- | --- |
| 修改Harness后启动一个实验 | 从定义与显式环境选择形成固定执行输入，准备缺少的依赖，启动并返回运行入口。 | 手工准备两套runtime、选择包路径、编写build/prepare胶水；未变runtime与材料反复构建。 |
| 用同一版本再运行或更换模型/case | 复用同一材料产物，冻结新的政策和attempt身份；按目标环境复用已有资产位置。 | 因新运行目录复制、打包和传输全部材料。 |
| 从一个明确checkpoint热修复后接续 | 显式关联checkpoint与修复材料，按变更影响完成必要prepare/迁移，重新核对来源停止与需求身份后分配新attempt。 | 把恢复数据再次塞进完整运行包，手工比对并串联所有阶段；无变化步骤也重做。 |

ZIP是托管平台等后端要求的交付形式，不是所有开发运行必须经过的中间模型。Local/Docker路径应直接消费冻结材料；平台仅支持完整上传时仍输出并上传完整包，不承诺不存在的增量API。源码和恢复状态独立建模，后端按需组装交付格式。恢复数据已在目标且可确认身份时不绕回控制宿主再上传；跨环境布局或语义迁移确实改变时，必要prepare与读回仍由Harness生产者负责。

公开工作流接受实验定义与目标环境，返回一次具体运行；恢复接受来源运行/checkpoint和明确修复输入。Controller拥有构建、物化、输运和prepare的阶段接续，保存真实效果与原错，显示复用或重做的原因、当前阻塞及下一操作。重复请求接续同一效果，显式retry建立新attempt；一个简写命令若仍执行原来的全量工作，不算此改进。来源停止、需求变更、费用与效果unknown的门控继续针对实际风险，不缓存启动许可。

主验收仍是打包、启动和热修复恢复的端到端耗时，同时核对变化传播：复用同一源码与环境时未变资产是否再次构建/输运；只改变模型政策时是否仍重做材料；真实热修复只改Harness代码时是否重做无关runtime或恢复状态。记录各阶段的实际工作量和失败接续位置，避免把5秒局部节省当成整个工作流完成。下一步先完成一条真实开发路径的变更/依赖/生命周期设计与接口收敛，再实施；不继续以更多局部校验补丁代替该边界。

## I14 启动证据与实施顺序

用户提供的 [I14 启动卡点](/Volumes/WorkSSD/Development/factory26/tasks/iteration14/dx-resume/startup-blockers.md)进一步修正上面的方案：资产复用只覆盖一部分成本，阶段合同、数据所在资源域和启动效果边界同样需要改变。本次另读保存的cleaner named prepared输运回执（660.924秒、两端退出0）、reviewer全 `/attempt/.` 导出300秒超时、reviewer reserve前17容器inspect60秒超时。原件快照归 `runs/infrastructure-dx/startup-review/`；其它表项作为来源会话记录使用，不追认为本分支实测或当前健康。

| 实际接缝 | 要明确的合同和责任 | 对开发闭环的影响 |
| --- | --- | --- |
| prepared complete且独立published，但terminal大archive仍pending；调用者自行提取/verify/compile/build/start。 | 准备产物的封口、来源及可消费能力独立于终态整域归档。Controller直接消费满足该阶段要求的named output，归档有自己的持久收尾责任。 | 成功prepare不因无关大归档阻塞，失败输运接续同一产物；原错和未完成保全继续可见。 |
| 同daemon准备产物先回控制宿主，后续Docker启动再次装配/复制；单次named输运超过11分钟。 | Artifact引用可绑定其实际daemon/store/volume位置；同域消费通过核验来源、不可变发布边界和新attempt独立工作区在目标装配，跨域才输运。 | 消除控制宿主往返；不通过共用可写卷、跳过内容边界或伪造源停止换速度。 |
| reserve前只读查询超时，runner已写launch_pending，后续只observe；全域batch inspect受复制中的单个容器影响。 | 启动阶段分别保存只读准入、reservation、物化和entry的效果边界；只读失败可有界重试，可能已有写入时按共同权威对账。全域容量仍核对真实held/physical，状态查询与大数据输运分开组织。 | 无需Agent逐文件证明是否可以接续；同域复制压力由设施安排，不靠会话临时协调顺序，也不跳过未知持有者。 |
| 原始ZIP、checkpoint、prepared、assembled被同一校验/解压路径反复处理；私有driver另猜runtime字段、产物路径与逻辑根。 | Harness producer提供各阶段公开输入/输出，compiler/controller/runner各消费自己阶段的合同。打包/验证共用载荷选择，已装配入口不重新解压或套原始无链接合同；合法链接依赖在生产阶段处理并保存依据。 | 开发者声明恢复来源与修复材料即可；减少因字段、路径和重复阶段解释导致的返工。 |
| 迁移OTLP接收后漏掉ResourceEvidence；Docker cgroup内存又被当RLIMIT_AS；工具wire模型与逻辑预算模型混用。 | Runner承担完整运行服务与后端资源语义，Harness声明消费能力；模型绑定明确区分逻辑身份与供应商wire ID。入口前完成必要服务准备。 | 修复完整运行组合，不用容器RUNNING或局部prepare成功代替实际可工作；不为每项失败新增私有driver。 |
| 选Python不兼容、编译失败后继续build、12GiB预留晚于大量材料准备、迁移路径经链接仍在WorkSSD。 | 工作流先解析阶段与环境约束、实际filesystem和预计峰值存储，再安排昂贵材料工作；后续阶段仅消费前段成功输出。 | 提前给出可处理阻塞，避免先复制数GB再发现不能启动；物理准入仍在实际启动时重核。 |

第一条实施路径据此缩小为“已有明确checkpoint及修复材料 → prepare产物封口 → 同域装配 → 确认生成入口”。先明确prepare到generate的类型化产物依赖、资源域位置和阶段接续，再整合上层定义入口；不先建全局缓存或通用DAG。当前源码的from_job仅允许generate→evaluate，且等待producer终态并排除archive pending，不能把它当作已经支持上述路径。扩展须按产物合同声明所需的producer成功/封口事实；不能从任意artifact存在推断可启动，也不提前评价仍未冻结的应用。

端到端验收应回答：同域消费是否仍下载再上传整个prepared；整域archive pending是否阻断已满足合同的下游；只读准入失败是否需要新attempt或人工猜效果；产物输运失败是否重跑prepare；runner服务是否在入口前齐备。记录实际入口确认和模型成功分别成立。来源停止、需求身份与未知副作用门控保留，改变的是它们的责任和适用阶段。资料中的现有修复由原启动owner持有，本分支不覆盖其在途代码或控制正在运行的矩阵。

## 产品目标与硬切含义

一次实验具有明确目标、允许输入、材料、模型/费用、资源预算、矩阵和完成条件。负责人决定这些条件与恢复取舍；设施组织build/control/monitor/analyze，可靠保存已发生的效果与原件。失败后只接续已经授权且缺失的动作，不让会话重新拼状态或用重跑消除unknown。

硬切针对新写入、新控制协议、公开入口和当前维护的执行实现。切换后新实验只接受新基线schema和CLI，删除执行侧兼容v1/v2/v3、旧operation与旧journal的默认推断及参数翻译。不建立新入口到旧多层编排的桥。历史事实保留只读，显式导入产生新制品并保留来源与缺口，不修改原件或继承收费授权。

活动旧执行仍由它实际消费的冻结程序负责，直到自然终态或取得明确退役/迁移授权。切换前核对所有在途批次的派发器、运行中attempt、待派项、collector、资源、源码/runtime来源及Console引用；不能假设派发器也已冻结。未启动且尚未冻结的新项不能因属于旧批次而继续在旧协议下新增。新旧混跑的资源域必须能由同一权威核对准入，否则该域等待旧执行退出；不得把unknown reservation当成空槽。硬切不自动停止模型、删除历史、释放保护或替换活动ZIP。

## 两个事实所有者

| 层 | 拥有的职责 | 提供的事实 |
| --- | --- | --- |
| Exp controller | 实验规格与授权范围、build组织、材料冻结、矩阵与attempt分配、预算/准入安排、控制意图、恢复选择、monitor和analyze。 | 实验意图、固定输入、动作请求、已消费的执行证据、阻塞及下一动作。 |
| Exp runner | 单attempt受理和物理执行、Harness入口生命周期、冻结限额执行、本地原始遥测、工作区/输出保全与执行效果。 | 真实执行身份、动作效果、资源与原始错误、制品、遥测范围和各项收尾事实。 |

Controller不能成为runner状态的第二写者。一次请求受理不等于执行发生；入口退出、外部容器停止、应用交付、输出回收、遥测排空和评分分别记录。Controller聚合投影由原生产者事实重建，没有另一份可手改的步骤成功数据库。

Build调用明确的材料生产者，不导入variant实现。需要实际执行的构建或prepare工作也纳入有明确身份和预算的执行，不能成为不受控的临时脚本。Analyze消费固定证据范围和版本化分析器；确定性统计与平台成绩归设施，语义解释和下一轮策略归负责人。它们是controller侧能力，不要求全部运行在一个常驻进程内。

Runner主要控制外部argv入口、资源和进程生命周期，不控制Braid成员或Pi子代理，不读取私有SQL补调度。Harness提供自身恢复与检查点语义。公共Agent SDK runtime、ARC官方Runner、Factory exp runner是三个不同制品。

## 执行、控制与环境

自有runner是每attempt独立监督者，有自己的冻结runtime、执行目录、控制入口、实际资源身份、持久遥测和收尾责任。Controller断开不终止已受理执行或关闭其collector；runner在冻结限额内继续，并完成保全。Controller重连读取原身份和证据，不重复启动。Runner自身死亡也不能证明Harness子进程或容器已停止；后端核对物理资源，效果不确定则保留unknown。

稳定的执行合同包括能力声明、prepare/start/control/observe/export效果、身份及原始错误。Local process、Docker和ARC托管分别实现实际能力，不用一个状态机伪装成相同运行环境。Local/Docker采用自有runner；托管平台由平台适配器返回远端submission/run、pending写入和平台可取得证据，不声称存在可部署的本地runner或不存在的暂停/检查点能力。

模型、provider与credential来源、官网费用模式由实验配方拥有，通用Harness/runner/recovery不固化ARC-only。已核对主会话最新人类指示：GLM-5.3使用Qwen AI，应作为其新配方修正；其它模型渠道另行明确冻结，不自动把整矩阵改Qwen。现有四个I14 run.py及recover_completed.py存在ARC-only拒绝或强制写入，本次完整基线包含这些生产端的边界修正，不能仅改文档。既有冻结与已发生请求保持历史，当前Flash/GitHub不改provider或费用。

环境无关指控制面消费稳定合同和制品引用。适配层仍识别真实平台、架构、daemon、镜像、卷、进程出生身份、连接与存储。准备环境和执行环境分别冻结，缺runtime/image/资产有明确blocker，不自动换host或回落到其它供应商。

每个动作有稳定request_id、目标attempt、参数摘要及请求原件。执行者持久保存受理与效果；同请求重入返回同一效果或unknown，不分配新attempt。不宣称通用exactly-once；不可消除的启动/写入窗口明确保留，禁止以重复启动或POST解决。Retry与从检查点继续生成都是明确的新attempt，绑定来源、允许变更和新授权范围。旧执行未知时阻断，除非负责人明确允许并存。

Runner在controller失联时仍执行已分配的单次资源限额。总预算由controller派发及分配约束，不能把在线token统计当成失联后的硬限额。Harness内部Braid session预算由冻结Harness材料实施并提供能力事实，通用runner不解析其私有会话数量。Docker容量准入位于实际daemon资源域的共同权威，包含reservation和物理活动；不继续依赖多个控制宿主恰好共享本地目录，也不扩展为通用分布式调度平台。

## 身份、制品与恢复

新领域区分experiment、job、attempt、request、runner incarnation、artifact、telemetry stream/collector epoch、evaluation attempt和analysis snapshot。后台服务进程身份属于生命周期证据，不能替代业务执行身份。平台与本机身份在对应后端命名空间保存，不靠名称或时间邻近猜关联。领域artifact身份与内容digest分别存在，相同字节不表示相同生产行为。

公开引用为artifact_id、member相对路径和digest；位置由环境resolver装配。原始绝对路径保留于私有证据，但不能作为跨环境合同的身份。制品包含schema、producer/源码/runtime版本、输入及组成清单、来源关系、能力和缺损。生产先登记意图、写staging并保存阶段原件，核验后原子发布不可变manifest；失败留下半成品及原错，接续产生派生产物，不补写历史成功。

| 产物 | 合同 |
| --- | --- |
| Checkpoint | 来源执行及恢复切点、Git/未提交内容、DB/WAL、native历史、材料/binary、外部依赖和路径约束；Harness声明语义完整性及缺损。 |
| Prepared input | Checkpoint/原包及允许材料变更、实际prepare命令、独立读回与完整输运绑定；适合指定Harness/runtime消费，不携带启动许可。 |
| Terminal archive | 执行终态的具体观察、文件保全与输运、遥测截止点、未完成收尾和恢复承诺；不是自动可继续的checkpoint。 |
| Application/evaluation input | 应用内容、需求、来源attempt/commit、最终或阶段快照身份；评分执行的费用、耗时和用量独立。 |

停止证明独立绑定确切来源执行与资源身份，在启动时与prepared input共同核验。补停止证明不需要改prepared包；它不是永久允许任意来源重启的凭证。材料可以先准备，但不能把内容hash一致解释为来源已停。

一致checkpoint由Harness提供取得/核验合同，执行侧取得材料并绑定切点。至少支持已确认停止源的完整checkpoint；活动源只有提供明确一致切点能力时才能声明完整。平台导出遗漏Git/native等内容时报告partial和具体恢复限制，不凭bare origin猜未发布历史。Braid专有恢复检查从通用实验层移到Harness恢复生产者/公共接口，不继续以Factory私有SQL形成隐含合同。

跨环境恢复显式声明native配置绝对路径、外链、外部依赖和语义迁移能力。普通相对文件可装配；需要Harness迁移的内容通过其明确接口处理，拒绝全目录文本替换。可迁移能力不足就报告限制，不退回一份依赖原机器绝对路径的prepared receipt并称为环境无关。

## 遥测、监控与分析

执行侧collector将原始protobuf、接收错误和绑定持久保存；endpoint/凭据以私有引用记录，stream identity不等于token。接收先持久化再确认，收尾区分producer结束/flush、collector保存、controller摄取。Controller的monitor消费这些事实与平台专有观察，不再自行exec容器读取私有进程/模型配置。

传输封装包含attempt、stream、collector epoch、源批次序列、signal、内容digest、生产/接收时间及截止点。Controller对同源批次重复摄取幂等；原始OTLP重传事实保留，不按payload SHA推断调用身份。模型用量依赖call/span identity，metrics依其delta/cumulative语义解释，不统一累加或去重。平台只能提供导出摘要时明确覆盖能力。

Monitor统一呈现实验/attempt、执行/归档/采集/评分、模型desired/frozen/runtime-selected/observed、版本、时间、具体原错及缺口。Console消费真实接入身份并通过runner/后端执行物理控制；自己的服务、访问容器和binary生命周期仍归Console。通知送达不等于采用或效果。

Analyze固定artifact与批次截止点、分析器版本、规则与缺口，结果可复算。生成与重放的耗时/消耗分别记录；缺辅助遥测不自动判交付失败，token增长不证明语义进展。隐藏评分反馈不注入仍在独立生成的Agent。

## 实现与一次切换

建议在lab中建立独立exp实现，controller、runner、后端、制品与telemetry合同按责任承载。顶层CLI只路由一个新执行领域；新controller不得调用旧operation worker/lab.run/Competition Controller串联生命周期。可复用内容清单、安全解压、HTTP原错、出生身份、OTLP编码和官方SDK等成熟实现，迁移其归属并删除重复owner及旧执行兼容。

整个交付包括新schema/CLI、独立runner、local/Docker/ARC托管接入、build与资产、物理控制/准入、检查点与prepared/application制品、遥测/monitor/analyze、Console接入及历史只读/切换规则。全部范围内部可分工和按依赖实施，验收与公开切换以完整基线为单位，不发布一个仍依赖旧controller存活的半成品基线。

首次实现范围与接口收敛见preparation。共享源有其它任务修改，开工前核对owner与真实依赖；全体当前使用的配方/包生产者、runtime、analysis和Console调用者同步切换，不能只修改Python imports而漏掉复制源码或动态launcher。新controller/runner分别显式冻结制品，不再广复制目录冒充稳定发布。

新合同的LLD见[technical](technical.md)，有界独立预演已完成并整合request/attempt绑定、准入物化窗口、切换前门槛、来源instance链、链接resolver边界及telemetry封口。当前主线HOLD和活动执行责任见preparation，不把本方案当作恢复旧模型运行许可。

当前方案授权仍不包括付费运行、停止现有模型、在途迁移和删除证据。无费的源码、编译与真实离线制品反馈已获开工授权并完成；独立runner中断/恢复、跨环境恢复、平台写入唯一性与实时遥测效果须有具体真实实验输入和授权，不能用fixtures、probe、smoke或源码阅读代替。本仓库不建立设施测试。

## 验收与判定

完成必须具备：controller断开后已受理执行/采集/收尾独立成立；重连不重复main/收费；动作受理与物理效果有独立原件；同source batch重摄取不重复统计；本地与Docker环境使用同合同并保留真实能力；prepared与来源停止分离；恢复保留Harness声明的历史和路径语义；平台pending未知不重发；每题完成后冻结应用独立评分；分析有固定截止；新入口拒绝旧格式执行而旧事实仍可读。

既有真实失败/导出/读回支持离线制品和历史分析，但不能证明独立runner、活源checkpoint、跨环境native迁移、collector中断及平台恢复。第一轮真实验收需使用当前获批准Harness与冻结材料，由用户确认模型/费用/题目/完成条件和允许的中断/控制动作；已有实验授权不自动扩充到新基线。验收失败修复设施后继续同范围，设施故障不当作有效零分。

独立advisor支持完整新领域和真正独立runner，并要求停止证明外置、unknown窗口、平台能力缺口与旧执行退役边界。独立迁移调查与制品预演已整合；它们提供设计反馈，不作为实际效果验收。


## 统一投影实施与后续意图编译

用户进一步指出底层生产者 identity 与显式 relation 是正确基础，但开发者仍需在 task、业务实验编号、目录、job/attempt、Harness 会话、平台 submission/run 和重放之间切换。新 status/index 已能聚合保存的实验与 attempt，但不等于贯通恢复、材料、评分及 Console 的统一投影。下一轮不能继续让“先判断生产者”成为人的常规操作前提。

当前定义采用两层：Experiment intent 经 compile 产生 Frozen execution recipe，后者执行产生 attempts/artifacts/evidence。Intent 声明问题、比较维度、目标、允许材料/模型/费用、资源与次数、评分及恢复政策；compiler 消费显式冻结的输入和命名政策，输出严格 recipe、选择依据、输入来源及未满足条件。Compiler 不执行模型、控制源、安装 runtime 或在线查询来隐藏缺项，不引入任意表达式/通用 DAG。I14 的逐实验 launch.py 已退役，策略选择迁入公共 compiler；同一 frozen recipe 的运行接续仍属于 controller。

人的默认入口以实验为中心，呈现目标行和阶段、产物及观察事实，保留 case/variant 比较条件和各生产者标识。2026-10-02 用户明确“你可以开工”后，本轮实施统一 projection：status/monitor 共用读模型，未派发的阶段也可见；明确展示入口、执行、归档、输运、遥测、平台观察、产物覆盖与阻塞，controller 给出操作建议及重新核验条件。原件时点不被本次查询时间替代，已有评价保持原冻结输入，unknown 不因归档存在而变成成功。Braid/Console 尚无绑定 attempt 的公开接入观察时保持 unknown，本轮不实施这些消费者的自动登记。查询可聚合显式 index 中多个实际实验，但不从目录或 job 命名猜跨实验逻辑关系。

统一工作流先复用现有 Lab CLI；Makefile 可做发现入口，但新增别名本身不能解决状态和策略碎片。Controller/runner runtime 继续独立冻结；日常准备可按明确指纹复用资产，缺资产时报告并进入显式准备动作，不退回随手选当前 Python。Console 首次服务、权限与访问环境的安装仍属于 operator，之后订阅实验公开接入 manifest 并保存接收回执；state/binary/container/mount mapping 由生产者提供和消费者核验，开发者不逐项手工交接。部署、支持宿主和读取权限仍须具体定义。

用户随后明确“继续推进，你可以自由提交”，实施接续公共 compiler 与只读 doctor。Compiler 使用显式 targets、命名模型选择和逐应用评价政策，冻结源输入身份和决定依据；doctor 聚合已声明资产与宿主读回，不安装、预约或授予派发许可。可用 slots、工具缓存及镜像内 interpreter 缺少独立只读合同或现场证明时保持 unknown；自动 Console 接入仍是后续方案。真实恢复路径用于核对“已发生事实、未取得证明、合法操作条件”能否由同一查询解释；没有通过写入旧冻结记录、新建采集器或启动模型取得验收。下一轮从新增 I14 到可比较结果的路径再收敛 intent 字段与命名策略，不把本轮 projection 交付宣称为整个 experiment UX 已完成。


用户随后基于真实热恢复指出，统一入口之外，重复全量校验和复制是当前最主要的体验成本。后续优先级调整为证明复用及减少物理搬运，再考虑 Console 自动接入。校验必须说明新增风险：来源停止与需求授权属于当前现场，内容及语义属于指定不可变版本，传输属于新的目标字节。相同内容、validator 版本和政策的语义回执可复用；同一操作内已取得的 inventory/manifest 不应层叠重算。链接判断独立于文件 SHA，运输目标仍核验实际字节，运行 workspace 与保存原件保持独立写入。发布 store 的不可变保障未建立前，不以 mtime 或旧回执代替字节证明。具体静态调用链、证据缺口和原 owner 边界归 packet，同一操作的部分重复哈希和制品复制前的源预读已消除；跨阶段语义回执复用及减少物理复制仍待实施。
