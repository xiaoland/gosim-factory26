# 实验基础设施干净基线方案

2026-10-02，当前为已授权并实施的新基线设计。用户明确支持“hard-cutoff，建立干净基线，可以一步到位，以长期正确为第一优先级”。这一取向取代此前兼容现有operation/recovery、只实施P0的分批方案。本次重新定义完整交付与切换边界，不把改命令名称或增加wrapper当作新架构。调查与决定见[packet](packet.md)，具体实施准备见[preparation](preparation.md)。源码已实施，真实离线反馈与未验证能力见 packet；未控制既有实验。

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
