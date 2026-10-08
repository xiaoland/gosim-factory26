# Factory26 跨组件技术说明

本文维护本轮 run 架构的跨组件职责、生命周期和证据边界。命令与执行细节归 [Lab 入口](../../lab/README.md)，旧冻结执行另遵循 [lab.exp 合同](../../lab/exp/README.md)；资源归 [runtime-resources](runtime-resources.md)，恢复操作归 [恢复手册](../deployment/recovery.md)，产品目标归 [PRD](../prd/index.md)。架构已经采用不代表部署和真实验收已完成，当前结果以[任务 packet](../../tasks/finals-experiment-loop/packet.md)为准。

## 组件与调用关系

新入口由 `lab.run` 接受 start、stop、pause、resume、restart 等实际 run 操作，`lab.arc_bench.execution` 持有 ARC Local/Docker 或 Hosted 的真实句柄。每个 run 独立执行、采集和保存结果，CLI/Console 退出不取消运行。普通 Python 组织跨 run 策略与 stages，没有 experiment/job/attempt 控制器、admission、slot、reservation 或未来任务队列。旧 `lab.exp` 仅服务原冻结执行与历史记录，不把它的容量和证明链带入新入口。

公共装配拥有最终程序目录或提交 ZIP，统一加入安装器、gateway、collector、run 输入与数据运输材料；variant 只准备自身程序、角色、技能及原生支持。统一入口先安装公共依赖，再启动公共服务并调用 Harness。本地与 Hosted 使用同一安装输入、依赖版本和入口，不以本地只读宿主 runtime 与官网预打包 runtime 建立两套正常路径；缓存只加速下载。团队编译的 Braid/model-proxy 属程序执行字节，公共 Node/npm 依赖在容器内按 lock 与补丁安装；约2.5 MB的 OTLP Python 依赖闭包直接随包携带，避免额外的 pip 下载与安装步骤。

两个DX采用的应用环境合同是：普通shell、npm生命周期、reviewer和服务子进程默认使用平台Node 20.19.3及其npm，应用依赖不得通过全局NODE_PATH解析到工具安装树。Pi、portless等工具的启动器通过绝对路径使用所需工具Node，不能为启动工具而改变应用子进程的默认PATH。variant指令使用普通npm命令，不要求Agent临时调用app-env。接续保留源码、业务数据和原生历史，但跨ABI的应用依赖须在独立副本按目标环境重装；锁文件迁移不能只替换包管理器名称。此合同正在实现与实际应用验收，状态归[应用环境packet](../../tasks/harness-app-environment/packet.md)，不代表历史variant或在途运行已迁移。

公共服务不解释 variant 的原生模型 selector 或猜测 Pi/Braid 目录。variant 的原生适配拥有会话接续、原生事实采集、完成与应用交付判定；绑定 program 的 observe.py 采集事实，status.py 解释活动，多 variant 共用的机械适配保留明确 Pi/Braid 身份。容器内 workspace 和原生状态的逻辑路径稳定，宿主实际位置归 target。原生 home、Braid DB/worktree 和 retained request 均在 data/harness，凭据在独立私有配置中。旧 lab.exp 的定义资产、authority/capture、compile/readiness 合同只解释原冻结执行，具体见其组件文档。

model-proxy 是公共运输设施，供应商模型配方的选择归 variant 的 `model-recipe.json`，可引用统一维护的供应商链与 catalog，避免复制供应商参数。自费运行由公共装配冻结并消费该配方，向 Harness 提供 `OPENAI_BASE_URL` 和 `OPENAI_API_KEY`；原生客户端模型身份、角色及请求预算归 variant。官网比赛不装配或启动 model-proxy，也不读取供应商配方，直接使用平台注入的同名端点与凭据。

Hosted 上传沿已观察的 model、visual_model、base_url 表单合同。比赛上传所需角色模型由 variant builder 导出 `submission-models.json`，ARC 适配层填官方端点；这些字段不构成供应商配方，也不覆盖 Harness 实际收到的平台注入值。没有证据支持依赖后台省略字段的默认行为。

新运行固定分离 program、inputs、data、records、snapshots 和 evaluations。restart 默认创建新 data 和原生身份；只有显式 keep_data 才迁移全部 data，同 task/需求版本恢复原生身份，下一 task 保留应用及历史并创建新原生任务状态。两种模式都重新组装程序并保留来源，不继承旧控制句柄、费用、遥测库或隐藏评分，也不删除来源现场。私有凭据在可迁移数据之外。新来源记录明确 keep_data；历史 restart 未记录该字段时仍按当时的迁移语义解释。停止来源和保存数据失败不能悄悄退回空会话或旧快照。

Braid 持有 Issue/PR、成员身份、工作项上下文、clone 和共同 origin；Pi/Codex 持有原生会话、工具和内部子代理；SVC 以独立技能文件提供方法和模板。三者的正文不由 Factory 复制成第二份规范。

| 组件 | 拥有 | 不拥有 |
| --- | --- | --- |
| variant/Harness | 生成流程、角色技能、材料选择和应用语义 | 实验调度、Braid 对象或官方评分判断 |
| lab.run / automation | 实际 run 操作、保存记录查询、普通 Python 自动化 | 实验级调度器或 Agent 内部协作语义 |
| lab.arc_bench | ARC 执行、官网响应、完整数据接续、应用冻结和独立测评 | Braid 私有语义或猜测的平台能力 |
| Lab Collector/Backend/Console | 三信号 OTLP、保存状态与结果、通用运行展示 | 运行现场写入、另一个采集循环或实时 Braid CLI 控制 |
| Braid/Pi/SVC | 工作项、原生会话、工具和方法材料 | 对方的私有生命周期或验收结论 |

组件间只沿明确的材料和回执建立关系：

```mermaid
flowchart LR
  CLI[variant / target / task] --> Run[Lab run API]
  Python[普通 Python stages / policy] --> Run
  Run --> Local[ARC Local / Docker]
  Run --> Hosted[Hosted adapter]
  Local --> Harness[Variant Harness]
  Hosted --> Platform[ARC 平台]
  Platform --> Harness
  Harness --> Braid[Braid 工作项]
  Braid --> Native[Pi / Codex 原生会话]
  Native --> App[应用与 Git]
  App --> Frozen[冻结应用制品]
  Frozen --> Eval[独立评价]
```

图中的 Braid 是团队 variant 的路径，不是 Pi-only 的强制依赖。共享 Collector/Backend 在单个 Python 服务中保存与查询原件，SQLite 使用服务宿主本地磁盘；Hosted 只携带轻量接收落盘核心，回收后导入。Braid 自有 reader 解码新增 batch，按固定 cutoff 低频后台重建并发布，页面读取物化结果，正文按需分页，不查询现场私有 DB。

## 生命周期边界

一次 run 的 execution lifecycle 为 starting、running、paused、completed、failed、stopped 或 unknown。activity、brief 和 last_activity_at 来自本次 program 绑定的只读状态脚本；脚本错误只令活动判断 unknown，不改写执行事实或阻塞运行。自动保存所有终态的实际可得材料；archive 只是列表隐藏标记。零分但正常结束的评测是 completed，环境或评测程序中断才是 failed。

experiments/ 保存任务及 evaluations 清单，runs/ 保存实际运行材料与原件。评测建立独立 run，配置中的 simulate、task、official 消费同一不可变应用快照的独立副本，评分、费用和错误不覆盖生成事实。官方 billing_mode 显式指定，不从模型 route 推断；隐藏结果不进入生成 inputs 或阶段控制分支。

自动化程序退出不撤销已经启动的 run，不承诺任意 Python 代码断点重放。已经发出的收费 POST 效果未知时查询原请求，不更换身份盲目重发。恢复只复制确定保存的数据；Hosted 强制取消后只报告平台实际导出的范围与时点，不能补猜测升级成最新完整现场。

## 证据归属与授权

编译、readiness、status 和离线读回只证明它们实际读取的材料。它们不授予模型、官网、Docker、Console、宿主迁移或历史清理许可。保存状态、消息送达和 receipt 存在也不等于现场完成。

制品以 manifest 身份发布，传输在接收边界核验字节；失败 staging、原错和未确认半成品保留。telemetry 保存 stream/epoch/序列和封口事实，分析不能从批次数推导 token、费用或语义进度。回收必须有稳定保留意图和完整证据，目录名、completed、hash 或 Git 提交不能单独授权删除。

模型 route、endpoint、凭据引用与评测政策在实际展开的 task/target/run 记录中保存。native cost=0 不代表平台费用为零；spend 保留 actual/estimate、来源、币种和 as_of，事实缺失保持 unknown。通用层不读取 Braid 私有 SQL，不从 collector 存活或 endpoint 名称推断已调用、已计费。

## 人工查看与物理运行控制

费用估算由执行适配器绑定运输身份及带时间的价格来源，不能因为模型同名而把 ARC 价格套到供应商套餐。`spend.coverage=partial` 的 value 是已知小计，不是完整费用或上界；未知模型、未定价缓存及未记录请求须保留缺项。Console 与 Python 策略消费这份归属好的事实，价格时间与用量截止点分别保留。实际终态账单优先于估算，历史估算保留；策略自行选择如何处置 partial，不增设统一拒绝或停止 gate。

Docker 控制使用该 run 保存的实际 daemon 与容器身份，不以 PID 或名字相近命中其他运行；资源限制和采样是执行配置与事实，不是另一套准入回执。程序、可迁移数据与私有输入分离；跨域迁移遵守实际路径与执行平台能力。

官方 ARC 运行由 lab.arc_bench 保存请求、响应、需求版本和终态 GET。提交受理不能证明模型已开始；HTTP 状态、原响应、需求差异和平台限制必须保留。生成与评价使用独立 run，评分不覆盖生成事实。

新 Console 不进入生成容器，不登记 accessor/writer，也不通过 live Braid CLI 修改工作项。CLI 与 Console 读取同一份保存 status；控制仍使用 run 绑定的实际执行句柄。自管 Docker pause/unpause 不改变 run，Hosted 明确不支持；stop 不级联影响其他 run 或独立自动化程序。旧冻结执行的准入、捕获和访问协调按 [lab.exp](../../lab/exp/README.md) 原合同处理。

## Braid、原生 Agent 与 SVC

Braid 维护工作项、协作和成员；Pi/Codex 维护原生输入、工具调用和会话历史；SVC 提供按需读取的方法。Factory 的装配不能把 Braid 成员、原生主会话和内部角色混成同一配置对象，具体材料消费者见下节。

原生会话恢复先区分继续历史和新建会话；没有适用失效时保留原 context，未知执行状态先确认停止和可恢复性，不能盲目重放。资源压力、进程出生身份、物理停止和逻辑接续的细节见 runtime-resources.md。

## 工作项上下文与原生会话生命周期

工作项的 Braid description、Issue/PR、成员身份和原生 session context 各自维护；只有有效 description 变化才触发上下文重建，普通 comment 不替代工作项合同。恢复前先确认原执行已停止和 context revision，不能把新 profile 文件或一条 handoff 消息当作已有进程即时更新。

## 角色与材料的三个消费者

| 消费者 | 材料与责任 |
| --- | --- |
| Braid 成员 | profile 持有成员能力、主模型和协作身份；run.py 指定根工作项启动成员，之后通过 assignee 指派。 |
| 原生主会话 | native_files 装配 launcher、设置、扩展和技能发现入口；打包存在的材料不自动启用。 |
| Pi 内部角色 | agents 下的角色文件持有自身模型、工具和技能入口；它不是 Braid assignee。 |

I14 的 materials.json 声明材料，公共 producer 决定实际组件内容，三个消费者分别解释所选材料。技能正文保持独立文件，发现入口只携带名称、description 和路径。具体修改位置见 [I13 接线](../../variants/pi-braid-i13/README.md)，其它 variant 按自己的实现读取。

## 交付与评测

variant 的 materials.json 声明材料，build.py 转交显式参数；tooling/scripts/agent_support.py、braid_runtime.py 和 runtime.py 只提供各自公开边界。Braid 的共享 origin、PR 和独立 clone 是交付关系，不能当作官方评测结果。ARC 的 Git history 通道由官方 CLI 写入 Runner 项目，不修改应用或实验索引。

实验定义、runtime、artifact、request、telemetry、attempt、platform run 和评分保持各自身份。一个统一的 trace ID 不能替代这些 producer identity；跨组件只建立显式 relation。材料存在、实际调用、采集成功、归档完成和官方 verdict 必须分开显示。

## 实现、实验与执行身份

Docker/宿主控制、来源停止、完整 checkpoint 恢复、非空遥测封口、官网写入和模型行为需要真实授权实验。源码编译、离线材料读回、保存 receipt 或 status projection 不替代这些验收。旧冻结 ZIP、旧 schema 和历史 variant 保留自身合同，不因当前源码更新而获得新保证。

实现、实验和执行身份必须分别核对：源码提交只证明实现字节，experiment/attempt/remote run 各自证明自己的阶段，Braid/native/Console/ARC 事实只能由对应 producer 原件提供。跨组件只建立显式 relation，不把多个身份压成万能 trace ID。

新执行通过 Lab run 身份关联平台 run、容器、Braid/native 和应用快照，不把它们压成万能 trace ID。旧 experiment/job/attempt、operation、authority 和封口记录保留原生产者，只用于原执行器或历史 reader；新程序不得用旧材料补猜测保证。输出保存保留链接字面值，不跟随外链。回收失败保留远端唯一副本，并与模型执行失败分别报告。

## 关联入口

- [Lab 入口](../../lab/README.md)
- [lab.exp：实验定义与编译](../../lab/exp/experiments.md)
- [lab.exp：执行、恢复与状态投影](../../lab/exp/execution.md)
- [lab.exp：制品、遥测与恢复证据](../../lab/exp/artifacts.md)
- [ARC 适配与评测证据](../../lab/arc_bench/README.md)
- [Variant 索引](../../variants/README.md)
- [恢复手册](../deployment/recovery.md)

源码或本页合同的存在不证明完整模型、官网或跨环境生命周期已经验收；实际验收以对应任务的授权和保存原件为准。
