# Factory26 跨组件技术说明

本文解释当前主线中多个组件共同依赖的职责、生命周期、交付和证据语义。当前开发入口是 `pi-braid-i13`；旧 variant 与冻结包按自身材料解释。已完成源码和材料核对的能力不等于取得完整生成与模型行为验收。
产品目标与实验规则归 [PRD](../prd/index.md)，操作命令归 [开发说明](../../CONTRIBUTING.md)和[运行说明](../deployment/index.md)。
实际模型、字段和工具版本以对应源码与原生材料为准；历史 ZIP 具有自己的身份，不会随工作树更新。

## 组件与调用关系

开发侧新实验由 `lab.exp.controller` 组织 build、派发、控制、监控和分析。Local/Docker 的每个 attempt 由独立冻结 runner 持有实际执行、资源限额、collector 与归档；Docker runner 位于固定运行宿主，负载只读消费域资产，短时 store owner 持有发布写入；托管平台由独立 adapter 持有远端身份和 pending 请求。Controller 退出不撤销已受理执行，重入同一请求不能重跑入口。工作树旧 plan/run/operation writer 已退役，历史输入只能只读查询或显式导入，新执行不翻译旧 schema。

`lab.exp.compiler` 将显式 intent 的目标、模型选择和逐应用评价政策编译为严格冻结 recipe；选择原件、输入内容身份与 compiler 摘要保留在 compilation 及发布制品中。同一编译 bundle 只接受相同输入/政策/版本，变化须新 bundle。Compiler 不请求平台、执行模型或隐式准备环境；I14 的逐实验策略 launcher 已退役。`lab.exp.readiness` 只读聚合声明 runtime/材料、模型凭据变量覆盖与 Docker 宿主事实，不安装或预约；域权威提供只读 query；未取得当前容量原件时明确 unknown，查询不能替代 start 的当前门控。

`lab.exp.projection` 从保存的公开生产者事实构建统一实验视图，status 与 monitor 共用目标、阶段、输入依赖、当前 attempt、历史关系、产物覆盖、阻塞及操作建议。比较目标通过配方的 case/variant 显式声明；已经分配的评价不因后来生成重试而改绑。投影保留生产者身份、证据时点和原错，不保存另一份可手改的成功状态或启动采集器。Controller 提供操作建议，实际执行仍核对原冻结执行器及当前物理门控；旧停止证据、完整归档和入口成功不能互相替代。操作方法与覆盖限制见 [Lab 入口](../../lab/README.md)。

执行终态、归档、遥测封口、传输和评分分别成立。Docker named output 封口并取得保留后，同域消费者直接装配，跨域或平台消费才取得独立输运；完整归档由原 owner 独立收尾；设施失败保留原错及未完成阶段，不解释为有效零分。费用模式、模型、供应商与凭据来源冻结在配方，运行凭据通过私有部署引用提供。通用层不读 Braid 私有 SQL，Harness 的公开 checkpoint producer 持有恢复语义核验。

Prepared 内容与来源停止证明分别发布；启动核对同一执行 instance 的当前物理停止观察和实际目标 OS、架构、runtime、logical root。当前 producer 只支持保持这些原生路径约束的装配，跨 OS/根路径迁移没有隐式文本替换。Docker 准入权威属于实际 daemon，共同卷冻结实现和容量；旧 dispatcher、预留和在途启动未明确交接时禁止新域接管。Console 工作项操作继续使用 Braid 公共 CLI，物理控制使用该 experiment 的冻结执行协议；尚无公开静止协调能力时拒绝 Console 暂停。

本轮实际离线材料反馈与尚未取得的模型/跨环境生命周期验收见[实验设施 packet](../../tasks/experiment-dx-review/packet.md)。源码及合同的存在不证明那些现场效果。

```text
源码开发                         冻结打包
variants/<name>/main.py          variant/build.py + 指定工具与技能材料
          │                                   │
          │                            独立目录 / ZIP
          └──────── 同一 main.py / run.py ─────┘
                                │
               原生材料 → Braid local → Pi 主会话
                                │           └─ Pi 原生 sub-agent
                    共同 origin 的交付 ref → commit
                                │
                         frontend/backend 应用
                                │
                    冻结后交由官方 Runner 评测
```

各 [variant](../../variants/) 自己持有生成流程、角色与指令、技能装载和材料选择。
相同代码可以暂时存在于不同 variant，某个实现的演化不要求扩展公共配置生成器。
[scripts/agent_support.py](../../scripts/agent_support.py)提供文件、进程和交付操作，[braid_runtime.py](../../scripts/braid_runtime.py)处理公开的 Braid 交付边界，[core.py](../../scripts/core.py)提供原生接入及会话归档能力。
这些支持模块不决定某个 variant 的协作方式或模型配方。

[runtime.py](../../scripts/runtime.py)准备工具，不读取题目或角色配置。
锁定的`pi-subagents 0.56.0`通过原生依赖补丁关闭自动验收：扩展提供执行、结果、错误与用量，不推断验收等级、不要求验收报告，也不代替委派者执行验证命令或判定任务达标。
旧验收记录保留可读，接续执行不重新启用其策略；这项行为由原生扩展负责，不进入Braid或SVC配置。
同一补丁去掉工具说明及包内帮助中的cwd级单writer、普通写入强制worktree隔离和父方应用全部修正的通用要求。共享cwd与独立worktree仍由Agent按任务选择，原生session lease继续防止同一会话被同时续写。
补丁同时接入本地依赖缓存与Linux预打包环境，既有冻结包不会自动更新。
[package_agent.py](../../scripts/package_agent.py)调用所选 variant 的 build.py 装入显式材料；打包不是应用生成。
raw 基线由 [raw_main.py](../../variants/raw/raw_main.py)独立执行，可直接使用工具资源，不必经过团队 Harness。

[lab](../../lab/README.md)将外部 argv 与共享输入冻结为实验，controller 分配 attempt，独立 runner 保存执行、操作和原始 OTLP 事实；`lab.exp.projection` 统一呈现保存的阶段与依赖，不解释 Agent 内部协作。不同 Harness 可直接作为外部命令运行，不需要实现设施内部接口；历史 Lab 状态读取与新实验投影分开。
Docker 是容器执行边界，Mac 控制器和 run 记录仍持有源码及实验事实。声明 Docker 的 attempt 冻结标准 CLI 选中的 endpoint 和 daemon ID，资源操作复用该身份。本地 bind 路径保留；ARC 远程接入使用带所有权标签的 named volume、阶段子目录及 helper 传输，官方 Runner 在本地装配和解释结果。输出清单核验并发布到原 run 后才允许释放远端副本；不可达或回收失败保持 unconfirmed 并支持显式 cleanup 补采。Console 访问容器仍只支持本宿主 Unix socket context。远程 OTLP 默认在执行容器 loopback 收集并随文件回收，网络 collector 入口必须显式选择和验证。操作与限制见[本地实验](../deployment/local-experiments.md)。

新 schema v3 冻结 storage policy 和稳定宿主 controller Python 依赖；attempt 分配及增加并发前核对目标文件系统 available bytes/inodes、host reserve、workspace/telemetry/finalization 及构建峰值。运行中异步观测占块，软阈值暂停派发，硬阈值受控停止进程组；外部资源仍须独立核实。历史 v1/v2 保持 legacy-unbudgeted。
[arc_matrix.py](../../lab/arc_bench/arc_matrix.py)选择实验组合；[arc_bench_adapter.py](../../lab/arc_bench/arc_bench_adapter.py)调用官方 Runner；[ARC 结果解释](../../lab/arc_bench/results.py)与[原生过程证据](../../lab/analysis/native_evidence.py)只用于可选分析。
替换 Harness 不应要求实验控制器识别另一种私有会话格式。

ARC 官网运行追溯由独立分发的官方 SDK 命令入口写入 Runner 的 `.arc` 文件。跨 Harness 的稳定接口是版本化 CLI 及其 JSON 结果，SDK 内部 Python 模块不作为消费者接口。Harness 选择是否把该入口交给 Agent，并负责所上报关系的真实性；ARC 适配层保存本地文件和官网 API 响应、提供查询。通用 lab 只连接运行与制品，不从 OTLP 或代码推断官方关系。材料存在、实际调用、采集成功和官方评测结果在查询中保持不同证据来源。

Git 历史是独立的 ARC 展示通道。公共 `arc-runtime.pyz notify-history` 对 Runner 目录中既有仓库发送刷新信号；`publish-history` 则接收内部源仓库与提交引用，把真实祖先导入 Runner 项目目录的受管仓库后发送信号。公共工具不解释 Braid 状态，不修改交付应用或索引，分别报告历史更新和信号写入情况。variant 负责仓库和提交选择、同步时机、重试及工作区保留。官网适配器在现有轮询中采集提交列表及不可用响应，查询分别呈现最近观察和最近可用值，不能将终态工作区不可用推断为 Agent 没有提交。

## Braid、原生 Agent 与 SVC

SVC 的技能入口、方法正文和模板由 `sources/svc/skills/` 一处维护，每个技能使用 SKILL.md、references/、assets/ 标准分发结构。
Factory 通过技能来源目录取得完整材料；公共文件操作只负责复制标准资源和许可，各 variant 自行选择装入与启用的技能。I13 选择 documentation、task-packet、sub-agents、verification，退出 investigation、design、implementation 的分发与引用；旧 variant 不自动同步这一选择。
源码运行和打包共用此复制操作，不解析 SVC 内容，不拼装专用 Corpus，也不复制维护者或 CLI 文件。


| 组件 | 拥有的职责 | 不由它决定的内容 |
| --- | --- | --- |
| 参赛 Harness 的 adapter/wrapper | 将任务转换为根 Issue 的 prompt，提供成员及其原生配置，选择根启动成员，调用 Braid 并交付应用。 | 不代替 LLM 分解任务或指派后续 Issue/PR。 |
| Braid | Issue 设计与独立 PR 实施的分工、Issue/PR 对象、具体成员身份、comment 协作、工作项上下文、独立 Git clone 与共同 origin 的已发布分支。 | 不提供 V&V 方法，不理解 preset，不控制 Pi 内部子代理生命周期，不读取 SVC task packet。 |
| Pi/Codex 原生接入 | 单个工作项内的原生会话、工具与内部子代理。 | 内部 explorer/executor 不是可指派的 Braid 成员。 |
| SVC skill | 按需提供文档、任务包、工作方法与 V&V 指引。 | 不拥有 Braid 对象或实验调度。 |

对运行时 Agent，成员通过 GitHub 式 assignee 显示；指派时选择的是能力配置别名，操作会返回新 Agent 的具体成员名。内部 profile ID、原生会话 ID 只用于宿主调度和证据关联。
variant 通过 `root_profile_id` 明确指派根 Issue，后续对象未指定 assignee 时保持未指派，不自动挑选成员。
创建 PR 本身不会启动 PR 成员。Braid 的成员指引要求在实施前创建并指派关联 PR，由独立 PR 负责人承接计划、排障、实现与验收；Issue 负责人维护需求、方案、验收依据及协作决定。此分工不限制成员讨论或合并其他人的成果，也不由 Braid 自动挑选模型。

I13 的根 Issue 直接负责共享架构与开发反馈设施，通过关联的独立基础 PR 落地，再指派可消费该基础的业务子项；最终通过 develop → main 整合 PR 验收。工作项保留原需求和场景入口，不能把父项摘要或需求编号清单当作子项已经取得完整合同。根 Issue 发布跨任务的产品、技术与验收约定；各 Issue 及关联 PR 接续同一任务的 packet。项目文档拥有稳定定义，packet 拥有当前判断、计划、证据与下一步，两者通过链接关联。

I13-2 的 profile 明确强制采用文档与 packet，并提供独立技能入口；通用启用时机与工作记忆方法归 SVC。当前 clone 根、共享提交、候选发布及 description/comment 的具体职责归 braid-collaboration。材料留在适用 Git 工作树，发布后由 AGENTS 阅读入口发现；运行私有目录不替代共同交付。Braid 不解析 packet 内容来替代 Agent 的采用判断。

I13 的配方政策保留在 profile：根基础 PR、develop → main 路线、advisor/vision 分工及应用反馈工具。独立 [braid-collaboration](../../harness/skills/braid-collaboration/SKILL.md) 持有工作边界、交接采用、变化和关闭方法，[arc-bench](../../harness/skills/arc-bench/SKILL.md) 持有需求层级、跨枝承诺、来源追溯与平台前提；后者单向引用通用协作方法。项目知识、task packet、原生委派与 V&V 的完整方法继续归 SVC，不在新技能复制。原生 executor 协助当前工作项，不承接已经指派给另一 Braid 成员的同一责任。
CLI 的运行位置和调用身份由原生执行环境提供；Agent 使用普通对象命令，不传 state 或 writer-turn。
跨工作项的信息通过 comment/reply 传递；代码通过各自 clone 对共同 origin 的 push/fetch 共享，私有会话内容不会因创建子 Issue 自动共享。
代码修改应保持这些边界，Braid 自身的详细行为归 `sources/braid/docs/`，Factory 不复制维护一份内部设计。Braid 与 SVC 源码由本仓库 Git 统一跟踪；源码归属统一不改变组件的运行时职责。

Agent 的协作入口借助已有的 GitHub 使用经验，介绍 Issue/PR 的查看、评论与指派，并提示“像人类一样协作”。
设计与实现分离的角色责任由 Braid 的 Issue/PR 指引和独立会话、工作区支持；具体怎样调查、设计、计划、验证由 SVC 提供通用方法。Braid 不据此自动选择实现者，也不以创建对象代替实际交接。
Factory 是参赛 Agent 的称呼，variant 实现负责装配组件，不另设能力指引层。
原生子代理的发现与调用由 Codex/Pi 及其扩展介绍，角色配置承载用途、模型与按需技能入口。
Braid 不授予任务权限，不固定根成员独占合并，也不判断比赛产物是否完成。

## 工作项上下文与原生会话生命周期

Braid 当前主线只有有效 description 变化触发上下文重建，传播到其它工作项须存在真实 description 依赖。title、comment、relationship 等变化作为增量通知，当前操作者不接收自己的动作；实际参与者与关注者仍保留相应消息。失效事件属于确切指派成员及 revision，休眠时保存描述变化，但不单独唤醒会话。详细对象和生命周期契约由 Braid 自身技术文档维护，Factory 不解析其私有表来补调度。

恢复先区分继续原生历史与真正建立新会话。没有适用的描述失效时保留原 session 和实际 context revision，不因 profile 或指令摘要改变抹去历史；模板只在创建 native home 时复制，已有进程不声称即时采用所有新文件。执行终态 unknown 先确认旧执行已停止和原生可恢复性，再提供一次明确的继续输入；不能盲重放旧输入或追认成功。只有确切历史丢失才进入相应新建路径，权限、歧义、暂时不可用和不兼容配置保留具体错误。

I13-2 将物理执行停止、OPEN idle 卸载和共享内存准入接入原生生命周期；跨组件职责、覆盖条件与压力策略归[运行资源约定](runtime-resources.md)。热更新独立技能和角色时显式刷新保留 home 中的 Harness 材料，并核对原生历史与模型配方未改变；只替换 native template 不足以更新已有 home。

这些源码已整合编译并核对既有材料，活动重建、休眠 resume、unknown 接续与并发改派的完整模型行为仍未实测，也未应用到冻结 I12。依据与当前验收范围见[上下文实施](../../tasks/iteration13/context-implementation.md)和[连续性实施](../../tasks/iteration13/session-continuity-implementation.md)；旧 ZIP 不因宿主源码更新而改变。

## 角色与材料的三个消费者

以 [I13](../../variants/pi-braid-i13/) 为例，`agents/<id>/profile.json` 和 `instructions.md` 构成本次 Braid 成员及主会话指引。
`run.py:native_files` 生成主会话 launcher 与 binding，替换当前运行的 endpoint 和技能路径；原生 `models.json/settings.json` 由 Pi 消费。
`agents/<id>/agents/*.md` 则由 Pi 子代理扩展消费，声明工作项内部角色的用途、模型与技能入口。
`build.py` 决定包中实际存在的材料。

I13原生子代理保留独立上下文，角色不设置工具白名单，父profile和运行条件不自动追加给child。技能保持独立文件，system/profile/role/task prompt只允许技能名称、描述和路径，不内联SKILL.md或references正文。所有角色可使用后台Bash与原生委派工具；run环境设置最大子层为3，深度、能力上限和结果回送仍由原生扩展执行。锁定版本的窄补丁让未声明工具且能力上限允许的child取得fanout入口，并简化其自动边界文案；显式工具声明仍遵守原有上限。这些改变进入新runtime构建，不追溯修改冻结运行。

I13按实际消费者分配稳定指令：Braid提供工作项身份、职责和通用对象协议，profile持有develop→main路线及advisor/vision等配方政策，运行条件持有通用工具环境与工作范围，原生工具description持有调用契约。角色目录description供父会话选择，角色正文与声明的技能发现信息进入child，二者不互相拼接。主成员开始或接续Braid工作时从profile取得协作技能读取入口，非简单工作的项目知识与task packet连接由技能指向SVC；适用的原生explorer/executor继续沿其自身技能声明读取材料。一次会话不因接续而反复注入方法。配置输出文件的child只在system取得输出义务，task不追加同一副本；恢复消息只补实际身份、状态与材料入口。

I13 的两份主技能各自给出完整核心判断，references 按当前决定展开；共同设置案例只在 Braid 技能保存一份，ARC references 按需单向引用。build 选择包内材料，run 使用既有 copy_skill 与 Pi --skill 机制复制和发现两项技能，不解析正文或增加自动内容装配。

I13的ARC特定输入与交付知识集中在独立 `arc-bench` 技能及其reference，根Issue description只提供本次任务、输入位置、技能读取入口及输出语言等任务参数。技能按普通材料选择、复制和发现，正文不进入profile；后续工作项由Agent给出适用合同的入口，不靠复制整份根正文传播。生成入口接收并复制输入目录，不以 `requirements.yaml` 是否存在判断任务能否开始；读取失败保留实际文件错误，材料解释和缺口由Agent处理。Braid/Pi请求不增加需求节点、依赖或覆盖字段。现有赛事启动参数、归档元信息和应用导出仍由外围协议持有，ARC知识迁移不改变它们。

I13 将固定版本的 `pi-background-bash` 显式加载到 Braid 成员 Pi 会话和有 Bash 权限的内部角色；插件覆盖原生 Bash，普通命令超过 30 秒会交还带任务 ID 的运行状态，命令继续执行，终态由插件回传。插件自身提供工具用法提示。Braid 以 Pi 的 `agent_settled` 记录一次调用的执行终态，不追踪原生子任务或插件内部作业。
原生接入的完成契约是：当前有限工作结束，其必要结果被父会话接收并完成后续处理后，才能正常结束调用；排空异常必须保留原始错误并投影为失败，不能以最后一条正常回应替代。
service 和历史任务结果可以在调用之间积累事实，但不能在调用结束后自行启动模型；后续被 Braid 接受的输入可以消费这些记录。执行终态不等于产品验收完成，业务判断仍由 Agent 根据证据作出。

因此“包里有某技能”“主会话启用该技能”“某个子代理启用该技能”是三个不同选择。
修改方法见 CONTRIBUTING；这里不复制各角色的模型值或原生字段定义。

## 人工查看与物理运行控制

Factory26 Exp Console是开发侧实验设施，不进入生成制品。通用Home与运行选择只拥有接入和显示状态，零登记可用；运行事实来自lab/冻结生产者记录，缺失保持未知，协作事实归Braid。App/Home、通用Run/HTTP与BraidRun/Sessions及对象类型分开，不引入未有第二消费者的adapter框架。服务使用新稳定根、固定app和单一manifest格式，hard cutoff旧服务接口，不保留升级/回退平台；旧配置和journal作为退役历史证据保存，新manifest是唯一权威配置。现场通过配套 Braid CLI 读取对象、实施人工编辑和取得会话目录；归档以只读 SQLite 投影读取保存对象，用保存的会话目录及 native manifest 定位原文，不依赖旧 Git、workspace 或访问容器，不重建工作项或 provider 生命周期。稳定服务制品冻结程序、前端、Python身份和受管理binary；接入明确 live/archive、运行身份、读写权限及独立的Docker物理控制。服务 manifest 直接表达可恢复配置的GC引用，HTTP停止不解除依赖；显式release保留身份墓碑与journal回执。HTTP、转发、访问容器及实验生成容器分别拥有生命周期，只有标记为Console自有的访问容器可由其管理命令启停；访问日志轮转，人工journal保留。Braid 不依赖 Console、ARC 或 Docker。

Docker 适配层暂停整个生成容器，Console 使用同一数据库/Git 的独立无网络访问容器继续人工访问。新暂停先在同一 Linux WAL 锁域取得写者门闩，确认容器已暂停后释放；锁只是暂停事务边界，不能代替完整恢复检查点。错误保留现场，不自动恢复、重建或解锁。实际部署及读取、写入、resume 和浏览器交互的不同验收范围见[Console packet](../../tasks/braid-console-control/packet.md)，操作归[接入说明](../deployment/console.md)。

## 交付与评测

Braid 返回 quiescent、blocked 或 failed 等操作状态，variant 分别保存进程退出码及运行结果。
`braid_runtime.load_delivery` 只解析请求指定的 ref 与确切 commit，`export_delivery` 只导出该提交；工作流程的完成判断由 variant 持有。
I13 要求 Braid 正常退出、status 为 quiescent 且 result.root_issue.state 为 CLOSED 后才交付 origin/main。根仍 OPEN、blocked/failed 或状态不可取得时保留未完成与现场，不将已有部分应用当正常交付。
该 variant 的持续成员指引安排子 PR 合 develop、根整合 PR 在候选上完成完整自动化验收后合 main；Braid 提供普通 base/head 与工作项事实，不判断验收质量或替 Agent 选择子项模型。根 CLOSED 是团队的完成报告，并非产品正确性的机器证明。
variant 随后按平台布局交付，记录生成与交付结果；真实运行故障仍保留原始结果和可恢复工作区，即使当前提交已经可以独立评测。
缺少 ref、无法导出或布局不满足平台要求仍是应用交付故障；不从任意 PR 或未提交工作树猜测替代产物。
具体文件写入和中断恢复仍受当前实现限制，不把这一顺序解释成跨所有文件的事务保证。

本地独立生成应使用 ARC 适配器的两阶段模式：生成时不传公开测试，再对冻结应用评分。
当官方只公开需求而不公开测试时，适配器在同一生成阶段结束后核对 Agent 入口、标准交付布局和 Runner 部署终态，记录为 `requirements-only`，其评分字段保持 `null`；这不是两阶段评分结果。
适配器在提交副本外包装标准 main.py，记录其退出状态，不读取 raw 或 Braid 的私有结果来判断任意 Harness。
官方 Runner 在生成之后还会部署应用，因此生成阶段的 Runner 容器退出码不能单独代表 Agent 入口的退出结果。
包装器记录缺失或入口失败时，不把残留文件误认为生成完成。

| 观察 | 能说明什么 | 不能据此说明什么 |
| --- | --- | --- |
| 标准 Agent 入口成功 | Harness 报告其生成流程完成；适配器另外要求交付布局存在。 | 应用满足全部需求。 |
| Factory 冻结的集成 commit | 此次提供给 Runner 的确切应用版本。 | 工作项全部关闭、Braid 无执行错误，或应用满足全部需求。 |
| 官方完整评测结果 | 此任务、制品和环境下的有效评分，低分也属于结果。 | 另一版本或另一评测环境具有相同效果。 |
| 外层 local experiment completed | 适配器结果报告完成；具体评分在 result 中。 | 所有用例通过，或所有原生会话已完整归档。 |
| OTLP received | 接收器保存了批次。 | 标准消费者已成功解码，或 Agent 过程记录完整。 |
| 原生 manifest partial/unknown | 会话关联或归档的诊断覆盖有限。 | 应用生成必然失败。 |

## 证据归属与已知限制

外层实验保存调用、输入快照和 Runner 结果；团队 Harness 将生成证据放在输出 `.factory26/<id>`；raw 放在 `.arc/raw`；官网记录由对应 journal 保存。
查询时先辨别生产者，保留各自身份，不以相同题名或 variant 名合并不同运行。
原生会话归档尽量保留原始内容，无法核实身份时记录缺口；诊断失败不应被伪装成应用低分。

当前工作树的 Braid OTLP 接线由 Braid 持有 exporter、原生记录语义和离线重建，Factory 负责归档后的显式交接。Braid state 与 native 原文是普通 decision 归档的内容权威；OTLP 默认发送操作信号及内容身份、字节数、覆盖状态和 usage 摘要。
`braid local` 周期性发送有界摘要；`core.archive_sessions` 完成 `native/manifest.json` 后，通过本次 Braid 二进制补发最终摘要和内部子代理覆盖。仅显式 `telemetry export --portable` 发送完整原文分片，保留跨边界离线重建格式。
没有 OTEL endpoint 或 Braid state 时跳过调用；补采限制总等待时间并单独保存退出码、JSON 报告与原始错误，不改变归档返回值或应用终态。

Factory 交接使用归档后的相对路径与经 header 核实的 native identity，保留 provider session 映射及 group、profile、工作项元信息。
Pi 路径型 session_id 不能标为 Braid 数据库 session UUID；无法核实的原生身份保持 null，归档、observer 与父子关联缺口进入 gaps。
Braid run_id 来自其 request/result，不能用外层实验 ID 覆盖。
未解析原文仍可导出，但 missing/partial/unknown 只说明诊断限制；历史文件导出不伪造实时 span 或累加生成计数。
Collector 继续只保存原始 OTLP 批次。默认摘要不能重建原文；portable export 才能通过 Braid CLI 读取 protobuf 并按源清单核对完整性。操作入口见[Braid 诊断手册](../deployment/braid-diagnostics.md)。
I13 finalizer 写 archive.json，分别记录执行、交付、评测、诊断覆盖、原文保存、恢复承诺及回收状态。归档复制/读取失败或声明原文未保存会阻止删除 work，应用结果独立保留；关联覆盖不全本身不等于原文丢失。只有 eligible 回执且无恢复承诺才释放 work；冻结 I12 材料不变。
当前可执行归档级仅为 decision，其它级别尚未实现且在配方边界拒绝。schema v3 用稳定宿主 asset.json 同时绑定 controller、job 与 inspect/cleanup Python launcher，计划和启动核对环境树身份。只读 GC 按冻结实验、run、recovery 和归档回执建立引用视图，仅精确 work 可成为候选；资产未见引用不等于删除授权，当前没有 apply。
这些说明描述当前代码接线，不能代替实时模型链路验收，也不赋予历史 ZIP 新能力。

`braid_telemetry_viewer.py` 以实验 run 为入口，通过 OTLP Backend 查询原始批次，再调用 Braid 的官方类型解码与证据重建接口，生成离线静态网站。
页面通过 OTLP resource 选择 Braid 运行，展示消息、对象和三信号；本地会话归档不作为补齐数据源，Backend 缺失保持可见。图表按 runtime resource 和指标属性分组，不能将累计指标跨实例重复求和，历史导出的操作 span 不当作模型执行。

查询层读取 Factory 与 lab 外层 run 的实际记录，分别呈现生成、部署和评分；完整评分不能由容器退出码推导，缺少原始证据仍显示未知。
Viewer 从外层实验链接原生会话和原始错误，不读取生成器配置来启动或重建实验。
独立源码以 Git bundle、工作区 patch 和未跟踪文件交接，依赖由目标平台原生工具重建；范围与命令见开发说明。

## 实现、实验与执行身份

ARC 的 operation 是一次已批准范围的持久接续入口，不拥有另一套生成状态。prepare 冻结实际 experiment 或 Competition inputs 以及操作源码；run 消费该冻结结果，status 从原 run、journal 和 scheduler 读回。启动、终态重放、观察与完成判断使用同一份实验/job 作用域，不能从共享目录里发现的其它 run 扩大执行范围。恢复准备显式绑定实际输入，准备成功与来源停止各自成立后才允许恢复启动。组件原始记录继续是事实来源，跨组件回执只证明交接效果。

controller、collector 和 Docker 准入共享完整进程身份语义：同机且确认为不存在是 lost，存在但缺少出生依据是 unknown，只有非空出生依据匹配才是 alive。旧记录不回填猜测身份；unknown 阻断接管、重试和破坏性清理。collector 的确定失败终止当前自动接续，显式重入才接管原 scheduler；正常终态后的新订阅可重新启动观察。输出归档保留链接字面值且不跟随外链；严格输入冻结与执行输出保全是不同契约，归档失败保留远端唯一副本，不改判为模型生成失败。

跨本地 controller 的执行容量由冻结 Docker daemon 上的共享准入控制，矩阵 workers 仍只控制本矩阵。准入同时计真实活动执行容器与尚未物化的 reservation，完整身份未知的 reservation 保留容量；物理退出与进程失联确认共同决定释放。当前 registry 只保证同宿主、同用户的参与者，不提供跨宿主分布式锁，所有共享消费者须选择相同容量和 registry。

variant 标识独立维护的 Harness，实验 case 标识该问题中的配置行，run ID 标识一次实际执行。人类实验编号与运行名都不能替代包、应用和机器身份。命名登记见 [实验导航](../../experiments/README.md)。

通用 lab 的 `labels` 是字符串元信息。稳定值随 job 冻结，本次执行标签随 operation request 和 run 保存；执行标签不能覆盖冻结值，retry 不继承上次执行标签。通用调度不理解 g/r、ARC task 或 Harness。状态查询和可选分析展示 run 中的保存值。

ARC 团队包身份以 `package-manifest.json` 的 `capabilities.variant` 为准，旧顶层 variant 兼容读取，两者冲突时报错。`arc_matrix --candidate CASE=ZIP` 将配置行与真实包身份分开；旧 `--variant NAME=ZIP` 是身份声明，不能用于覆盖一个已知的包身份。缺失身份保持未知，声明和已验证来源分别保存。Competition 保留顶层 variant 的原调用声明以兼容续接，真实包身份在 `package_identity`，新逐题 labels 只标注已有来源证明的 variant。

重放包可以携带多题和不同生成来源。按需求匹配 replay case 后，把来源 run、原实验/包引用与带算法的应用摘要传给 `source_application`；不以 submission 名或第一个 case 推断整个包的来源。旧 replay 的文件哈希映射摘要与新应用树摘要是不同算法，不能直接互换。原始来源缺失时不从名称或原生 Agent 会话猜测。

本地 Hackathon 报告先明确选择冻结实验/job 集或显式 run 集，再按 case、赛题、应用、suite、镜像及其他冻结执行输入隔离。替代关系只来自同一实验/job 的显式 retry 链；独立重复分别呈现。缺来源的记录保留可观察结果与缺失原因，不拼接总分。分组键只在本报告内使用，真实关联字段独立保存。

存储生命周期成果已按来源提交增量整合至当前开发主线和 I13；来源、合入身份、实际反馈及未验边界见[存储任务](../../tasks/experiment-storage-lifecycle/packet.md)与[I13 合入回执](../../tasks/iteration13/storage-lifecycle-integration.md)。源码接线不代表宿主资产已建立、预算停止/归档删除已实测或历史材料已迁移。
