# 实验与开发基础设施 DX 开工说明

2026-10-02，用户认可继续架构方案，并问“好的，可以准备开工了吗”。本轮已完成实施面核对与独立advisor复核，当前为待开工复核。本文取代前轮基线的旧实施准备；历史切换依据保留在packet及Git历史。尚未修改设施源码、部署服务或启动实验。

工作分支为 `feat/infrastructure-dx`，唯一实施worktree为 `/Users/lanzhijiang/Development/.worktrees/infrastructure-dx/factory26`，准备基于 `9f9eab9c`。职责归[design](design.md)，接口与失败合同归[technical](technical.md)，原件及授权归[packet](packet.md)。自由提交授权继续用于当前任务；原工作区其他owner的未提交代码与运行仍由原owner持有。

## 本轮结果与范围

本轮完整交付是让开发者从实验定义、Harness修改或明确恢复来源出发，经公共入口得到材料选择、构建、目标装配、运行与结果。打包、启动、热修复恢复三类流程共同约束架构，内部依赖顺序不构成只交付某一条路径的计划。

| 用户流程 | 完成时应有的行为 | 主要消除的工作 |
| --- | --- | --- |
| 打包 | Producer从实际材料选择声明依赖；已有runtime、依赖、Harness材料与代码资产可复用，按后端需要封装ZIP。 | 每次run重装Python/OTLP依赖、重建runtime、重冻相同执行代码及无变化全量材料生产。 |
| 启动 | 维护的环境配置解析目标；已有域资产直接装配，逐服务ready后确认入口，公共状态解释阻塞与接续。 | 调用者手填runtime/物理字段、同域payload绕控制宿主、全域重复inspect及查询失败后的人工运行树重建。 |
| 热修复恢复 | 原checkpoint、修复材料和新配方分别引用；有限Hook生成派生prepared；封口产物先保留再消费，来源关闭和恢复损失明确。 | 重建整个恢复包、重复无关prepare/语义扫描、整域archive等待及输运失败后重跑入口。 |

Hosted仍按真实平台协议提交完整ZIP；平台费用、排队与完整上传分别计时。平台不提供的增量能力不纳入提速承诺。资源采样与预算保护是新材料可消费的前提，不为了复用而延续旧缺陷。

## 默认工作流与支持边界

公共CLI继续使用 `python -m lab`。以下是拟实施合同；代码开工后更新Lab操作文档，不把它当作当前已可调用命令。

- `build INPUT --environment PROFILE --directory RUN` 接受新intent或新冻结recipe。Intent由同一compiler编译，controller只生产缺失材料并冻结实际选择；run主要保存配方、引用、动作及证据索引。维护的profile给出Python/平台、存储、backend与工具来源，不要求每次填写hash或制作两套物理runtime。对冻结recipe，profile只解析已经声明的目标约束、资产位置与部署条件，不能覆盖冻结选择；目标、runtime或生产条件改变须新recipe及派生关系。未来产物按原producer/output合同绑定。
- `compile INTENT --environment PROFILE --directory BUNDLE` 保留仅编译入口。输出冻结政策、目标约束和生产计划；尚未产生的输入引用明确producer/output合同，不构建材料或执行运行。
- `doctor INPUT --environment PROFILE` 可在build前解释复用、缺失及预计工作。默认status/monitor消费保存事实；需要当前权威查询时明确观察范围和成本。
- `start RUN --deployment PRIVATE` 沿已授权配方派发。每次执行消费冻结代码资产；代码资产在缺失或实际依赖变化时构建，不能继续依赖可变工作树。
- `recover SOURCE --intent INTENT --environment PROFILE --directory NEW_RUN` 组织明确的恢复派生与材料准备，建立来源关系；不隐式停止旧来源或启动模型。准备后仍由start进入运行，pause/resume继续属于原执行控制。

Profile与producer能力共同解析最终物理绑定；实验定义仍显式拥有目标、需求、模型/费用、预算及允许恢复变更。高层定义不编写私有driver；通用外部argv能力保留，不新增任意工作流DSL。

首版支持Local及现有Linux Docker目标、明确停写的完整来源、相同OS/架构/logical layout、同内容跨daemon输运、独立可写workspace和四个I14 variant。修复Hook仅覆盖已有问题需要的材料类别：指令/技能/扩展/launcher刷新、已声明provider transport、路径别名及外部工具物化、明确兼容的runtime替换；每类有前置条件和实际变更记录。模型/需求改变消费对应授权，原Git/native历史与应用工作不得被材料刷新覆盖。活动源一致快照、跨OS/native根迁移、自动Git重建及任意补丁不进入完整恢复能力。

## 已核实的边界与实现取舍

| 边界 | 当前源码观察 | 本轮确定的处理 |
| --- | --- | --- |
| 唯一动作权威 | Backend直接create/start/control；SDK执行容器、copy helper和Console accessor仍有自己的物理调用；禁止restart命令不能阻止start旧容器。 | 受管工作负载的创建/启动/控制统一排序；released实例拒绝再次start。Accessor可写许可纳入workspace writer覆盖，捕获窗口拒绝冲突的access-start。 |
| 辅助操作 | query、copy、构建与生成资源性质不同。 | Query有界并发/超时/清理，不先写预约才能读权威；copy只保留实际输运请求/partial。可写helper纳入writer覆盖。构建限制并发与资源，实际竞争同池才共同核算，不为每种helper建立另一套调度状态机。 |
| 发布资产 | publish原子rename但payload仍可写；producer不能拿整资产卷RW后声称published只读。 | Producer写隔离staging，存储owner核验发布；负载仅只读消费published，并使用独立workspace。弱Local在实际读取/复制边界核验字节，复用本次结果。 |
| 保留与清理 | named output在archive阶段发布；GC仅pin整个新exp目录。 | 发布与初始保留共同可见；consumer先retain后装配，保留覆盖载体；GC与保留同锁并查询稳定删除意图。旧store继续保守保护。 |
| 运行服务 | 外部collector使Harness返回而未建立ResourceEvidence；runner缺必需样本接线。 | 复用现有ResourceEvidence，由runner持有、入口前ready，Docker样本来自实际cgroup，独立于OTLP开关。 |
| Braid预算 | model_budget在PI_SUBAGENT_CHILD=1时跳过保护，四I14都经过此包装器。 | 取消child豁免，继承父Braid binding，多个child仍属于同一Braid session；缺身份拒绝昂贵调用。复用选择核对新保护能力及相关依赖。 |

只读权威查询首版选择明确支持的Linux local-volume：已核验Mountpoint的只读bind，域资产根正常运行期间不删除/重建，GC只处理内部对象，维护退役排空访问；读取还核对域身份。非local driver或不能证明这些条件时返回unsupported/具体缺口，不同时实现keeper container及自动降级。该选择不新增常驻服务，其实际挂载/缺失行为仍需获授权Docker操作确认。

源码核对未找到原启动owner所述execute-prepared、精确node-gyp和child预算修复的可见提交。开工时只按确切已提交版本比较依赖并采用必要变更；没有可用提交就按本合同实现等价修复，不能复制原工作区未提交文件或追认原版本已经生效。

## 文件责任与集成次序

以下为必要改动面，不要求每个逻辑责任新增一个模块。各owner可在其边界内组织实现，交叉改动由主Agent整合，所有参与者保留他人修改。

| Owner | 独占主要代码面 | 交付责任 |
| --- | --- | --- |
| 主Agent | lab/exp/core.py、compiler.py、controller.py、projection.py、readiness.py、__main__.py；公开文档与实验入口 | 按kind版本、环境解析/生产计划、引用绑定、合法接续、状态/诊断；整体切换与验收。 |
| exp_harness_materials | scripts/runtime.py、package_agent.py、package_completed_recovery.py、braid_runtime.py、agent_support.py、runtime_resources.py、model_budget.mjs；submission/exp_checkpoint.py、recover_completed.py；四I14的build.py/run.py及必要launcher/冻结child接线 | 实际依赖与复用、封装、正向语义覆盖、有限修复Hook、独立application合同；必需资源/预算能力。 |
| exp_platform | lab/exp/artifacts.py、hosted.py、lab/gc.py、lab/arc_bench/docker_workspace.py | 域store、位置/保留、稳定输运与接收校验；SDK消费权威动作ABI；Hosted引用/pending；GC保护。 |
| exp_execution | lab/exp/admission.py、backends.py、runner.py | 权威动作/版本/未决效果、域装配、独立监督与逐服务ready、ResourceEvidence生命周期、封口产物与归档分离。 |
| 主Agent整合Console | braid-console/service.py、docker_runtime.py及受影响登记合同 | 仅收敛绕过权威及workspace写入口，消费公开绑定；不重构Console内部调度、UI或部署。 |

存储owner给runner提供发布/保留接口，执行owner给SDK/Console提供固定动作ABI；各自只写自己的事实。runner named输出与服务接线由execution owner修改，材料owner消费其合同，平台owner不并行编辑runner/backends。

内部先冻结按kind版本、生产选择、store和动作ABI，再并行实施对应owner；随后接入SDK/Console writer、controller/public producer与投影，最后完成整体验证和文档。发布时整体启用新writer，不长期提供旧recipe自动翻译或两套运行生命周期。源码编译通过不代替各用户流程闭环。

## 切换与现场隔离

新执行合同按kind单独版本化，不能将core.SCHEMA全局改成2连带重写artifact/runtime/telemetry身份。Intent/compilation/experiment/attempt/execution的生产选择、引用或接续语义改变，使用新版本；request的身份与参数绑定合同及artifact/runtime/telemetry/analysis未改变部分保留原版本。Harness checkpoint/prepared新增保证使用明确的新producer合同，历史元数据缺覆盖不补造complete。新增域位置/保留记录从首版开始，具体字段归technical及实现接口。

新writer拒绝旧执行recipe；旧事实走history/显式import。既有运行继续使用其冻结executor，不迁移或热替换；控制旧运行也必须委派该版本，不从旧launch_pending推导新协议安全重启。旧运行store和未决平台写入持续保护，新增managed位置不能改原artifact manifest/hash。

本轮源码实施不依赖完成原主线运行或接受其未提交修复。实际使用共享daemon前要确认资源域覆盖、旧writer/预约及能力；未知时阻塞对应真实操作，不能通过创建新的名字声称宿主已隔离。Console本轮改接缝代码，现有服务仍由原owner部署维护。

## 真实反馈、验收与授权

开工范围包括源码、编译、受影响文档、已有真实材料在本worktree新输出目录的离线生产/封装/输运/读回。原件只读；新的store/output在报告完成前保留。使用已存在的生产入口，不添加设施测试、fixture、probe、smoke或伪造错误/状态。

| 反馈与材料 | 实际操作与完成依据 | 保留的限制 |
| --- | --- | --- |
| packaging/receipt.json对应真实包及stage | 无变化复用、实际相关材料修改后的生产/封装；记录实际依赖、字节/权限、缺失构建和未发生的重复安装。 | 已有62.45→57.49秒只覆盖ZIP编码，不能当本轮完整打包基线或保证倍率。 |
| transport/receipt.json对应artifact-d86677e75e19ba22505792b5 | 新store真实接收及同请求重入，保留身份；记录本次发生的扫描/复制，沿旧原件解释失败范围。 | 旧接收重入27.03秒仍全量核验；没有实际故障不能宣称丢响应已验收。 |
| separation的真实发布配方与startup-review索引 | 新版定义/计划及引用构建，来源/代码身份读回；对可确认的完整来源进行明确离线派生和结构读回。 | 历史停止原件不授权今天启动；缺获取窗口证明则只反馈其结构与缺口。 |
| 已有application与明确交付原件 | 独立冻结最终/阶段应用，核对commit、需求与未提交内容政策。 | 缺恢复材料保持partial，外部评分需对应费用授权。 |

主验收仍是三类端到端区间：完整打包请求到可交付资产/包，启动请求到入口确认，明确热修复输入到恢复入口确认。同时记录人为接线次数、材料规模、代码/runtime/平台、物理环境、缓存及构建/扫描/复制/传输/等待；从关键路径移出的archive继续记录总成本及owner完成。首次缺材料、无变化复用和相关局部变化分别比较，不用单次顺序计时当稳定benchmark。

真实Docker装配/ready/入口、controller断开接续、child预算归属、完整恢复及模型首成功，还需冻结实际输入、daemon/profile、预算与控制动作。当前不会启动模型/平台、停止旧来源、创建或接管共享域、部署Console、迁移旧运行或应用GC；这些动作在具体实验范围内另行安排。可以先完成代码及离线闭环，但最终报告不能将其写成三类端到端验收已通过。

本轮独立advisor支持进入开工复核，建议限制辅助状态和采用单一查询挂载策略；对本说明再次复核后，补清冻结recipe的环境解析边界及编译写BUNDLE的措辞。三个实施owner已经返回可执行的文件/责任/验收范围；实际操作前核对材料可用性和环境属于正常执行门控，不再扩大架构调查。

当前开工复核对象就是本文的源码、文档、编译与真实离线生产范围。待用户针对该范围明确同意开工后实施；继续保留自由提交和本任务worktree隔离。未知效果不重发入口，具体风险/错误留原件；运行中证据明确的范围内设施缺陷由owner完成修复闭环。
