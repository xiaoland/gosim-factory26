# 定义、生产、交付与装配职责复核

本轮仅只读调查与设计，未修改源码，未运行编译、设施操作、测试、网络、Docker 或模型。调查对象分别为主区 `/Volumes/WorkSSD/Development/factory26` 和交付区 `/Volumes/WorkSSD/Development/.worktrees/experiment-startup-dx/factory26`。下文简称 M、D；行号来自本次实际读取。M 有其它负责人在途改动，D 的新模块不代表已经合入 M。本文只覆盖生产与实际装配责任，不替代 state/terminal owner 的生命周期判断。

结论：上一轮把 identity、state、namespace 的重要错误边界补齐了，但“组件独立”还没有贯穿生产与交付计划。当前仍由一个按实验执行的 build 统一选择依赖、生产组件、解释用途、造交付包，再由 SDK adapter 重做域安装。最明显的新问题是 SDK 自包含 delivery 已含 runtime/skills/support，同时新 bridge 再把相同组件装进 daemon 并挂为真正执行源。不能把这一重复称为外部 SDK 不可控成本；不可控的是 SDK 自身的 stage/总 inventory，设施选择先造整包再装第二套资产仍是自己的责任。

## 应有职责及当前越界

| 功能 | 唯一权威和结果 | 当前越界 | 处理方向 |
| --- | --- | --- | --- |
| 实验策略 | 实验领域 compiler；cases、selection/evaluation policy、model policy、依赖关系 | generic compiler 直接解释平台 GET 和 legacy journal 分数格式；同时做大目录内容冻结 | 保留显式实验策略，领域 adapter 产规范 evidence/decision；物理输入发布与内容认证归 producer。compile 消费已冻结 ref 或未生产节点，不启动域、不隐式查询平台 |
| 依赖选择 | variant 声明自己的入口、角色、技能、native 要求；设施声明执行组件依赖 | generic package_agent 知道四 I14 名字、解析 build.py 的 SKILLS AST、检查 Pi 插件源码字串、限制 reviewer seed | 移到 variant/runtime producer 的声明与具体生产证据；设施只检查角色合同与实际来源，不以源码形状充当组件能力 |
| 资产生产 | 组件 producer；每个组件独立 identity、依赖、发布回执 | produce 是全局串行大函数，顺带 pip、生成 SDK archive、私有输入转换；build 先跑所有 productions | 以实际消费为根选择已有生产 DAG 的缺失节点；生产与 resolve/retain 分开；只对真正变化节点生产，不要求一次造齐所有 venue 的物理交付 |
| 定义组合 | 不变 ref/member 与实际角色关系 | agent 成分包含平台 history/export 工具；设施 support 混 checkpoint、telemetry、admission、native policy | definition 只依赖实际 Harness 使用组件；执行 controller/adapter/capture code 在 recipe 执行角色单独绑定，不把控制面修改变成 Harness 重建 |
| 交付投影 | 场所 delivery adapter；从定义和明确交付要求产生传输视图 | environment 推断 hosted/external_docker 来造不同大包；store identity、私有输入混入整包 cache key | 场所提出交付要求，producer 只造需要的视图；同域 SDK 优先薄启动材料+已装组件。Hosted 确需自包含时单列；私有部署输入不使公共定义、公共包重建 |
| 实际域安装 | deployment owner；实际 ref/member→本域 placement、真实 namespace/birth、service ownership | Local/Docker assembly、SDK adapter、delivery bootstrap 各自造 assembly 和检查不同 proof | 一个规范装配结果，一组公共认证/映射规则，venue adapter 仅提供实际 mount/process/API 能力；不要另建中心服务或万能 identity |
| Harness 启动 | 同 namespace bootstrap；就绪服务、真实 entry、关闭责任 | variant main 推断 context/delivery/source/legacy/prepared，并读取固定 `/factory26-namespace.json`；run 仍决定 telemetry fallback | entry dispatch 与受管/独立 bootstrap 归设施；variant 接受已装配 context 和小 derived inputs，负责 native config、生成协作及应用交付 |
| 恢复 | state owner 负责 writer closure/许可；prepare producer 负责明确修复与新 generation；域 installer 安装改变定义 | environment 把 prepare 当普通 production，同时带可变 lease；缓存/生产和控制操作耦合 | 保留 v4 snapshot/ref/member 与 mutable generation 的区别；prepare 请求携独立 state lease，不成为普通可缓存 immutable DAG 节点，不借普通内容副本提升 capture 能力 |

这些是责任边界，不要求为每行建立一套新服务或一组新配置。保留现有 artifact、attempt、execution、producer identity 与显式 relation；应减少用户可填写的重叠权威。

## 已证明的接缝及原因

### 1. compile 不运行模型，但仍承担物理冻结和平台数据解释

D `compiler.py:159–169 → environment.resolve:92–98 → package_agent.selection:269–308` 读取实际解释器、runtime、skills、variant、支持代码闭包；raw path 分支全目录哈希。D `compiler._paths:128–147` 对普通输入和 checkpoint/prepared 再 `artifacts.contents`。D `environment.resolve:44–63` 在重解析已冻结 recipe 时重做 plan_material/plan_prepare。不是 compile 偷跑模型或 pip：pip 实际在生产阶段；问题是“我声明未生产的实验”与“我把当前物理资产冻结”绑成同一个命令，而且同资产可以在 planning/build/安装窗口反复认证。

`from_production` 保留未生产引用是正确改进，但其 harness runtime 仍要在 compile 时物理存在：D `package_agent.selection:282–292` 要读 Braid、Pi 源文件；prepare 的 source manifest 也必须存在（D `environment.plan_prepare:107–117`）。这是已存在组件的 import/freeze 要求，不应变成所有高层计划成立的前置条件。计划可以声明生产来源和目标 ABI，build 才绑定具体发布身份；已有 immutable ref 的认证可以在一次明确消费窗口复用，不能引入跨运行持久免检缓存。

D `compiler.final_score/select:27–95` 解释 GET/legacy tasks 的状态、百分比分数、测试数量、条件 margin，并决定 incomplete 时 baseline/block。这是显式授权的实验策略，不能简单删除为“infra 不应有策略”。应该移出 generic compiler 的平台/legacy 数据解释，保留领域 policy 的声明、来源身份与冻结 decision。D `compiler:229–244` 的 ARC operation→local_job 可以保留为领域 lowering；它不应继续承担 runtime source shape 准入。

M `environment:19–23,73–84` 又加入 provider_env/application_seed/gateway_routes，M `package_agent:339–348` 把 model catalog、provider credentials、reviewer-only seed 计入整个 material identity。路线顺序/模型策略、私有凭据、初始应用是三类不同输入，不应因为同属一次实验而一起进入公共 Harness 材料生产 key。reviewer-only seed 规则应由 reviewer 的输入合同承接，公开模型路由由实验/模型通道组件声明；凭据归本次 private deployment。

### 2. build 仍是跨角色大生产事务，组件拆分没有变成消费驱动

D `controller.build:284–295` 先生产 controller/runner runtime，再 `produce_materials`；D `environment:148–207` 遍历全部 productions，随后看消费者 backend 决定 directory/ZIP。没有从实际可启动 job 依赖闭包选择 production；一个暂不消费的声明也会先生产。controller 在 `319–328` 同时选择 agent/package/delivery、插入 definition、private tool 输入和全部 definition role refs，兼任 venue delivery planner。

D `package_agent.produce:355–450` 虽然组件独立 cache，但一个全局 `.producer.lock` 跨 runtime/skills 复制、OTLP pip（235–251）、support、SDK pyz、variant/e2e、private 输入。由此某个慢组件仍挡全部 variant 生产；不能把缓存命中等同需求驱动。这不是建议删除本地锁：需要把锁和重入回执跟实际组件 production request 对齐，保留失败/未知副作用现场。

还有闭包失效扩大：D `runtime.plan_host_runtime:221–224` 把整个 runtime.py 哈希纳入 Python venv key，修改同文件其它 launcher 代码也会换依赖环境 key；D `controller._source_files:21–30` 用整个 exp/*.py 加 ARC/support/checkpoint 列表产生一个 executor，`_executor:51–79` 将该统一代码与依赖生成 code artifact 和 runner.pyz。只改 status/compiler/controller 也可能更新 SDK 安装的 executor code（docker_workspace:516–533）。必须按实际执行角色切闭包，而不是靠文件名“controller/runner receipt 已独立”宣称代码部署已独立。Python 依赖环境、控制代码、adapter、bootstrap/capture code 各自失效；变更应能从计划直接解释传播范围。

### 3. 新 SDK 路径有两份定义，私有输入扩大重打包

D `delivery.project:9–64` 在 payload 复制 agent、runtime、skills、support、e2e，再普通 publish。runtime 大副本既在 delivery cache，又在 artifact payload（支持 COW 的文件系统可能共享 extents，但不是逻辑消除；Linux fallback 实际复制）。ZIP 从这个目录生成，缓存和 directory/package 各自保留。store_id 纳入 key 与当前 store 下索引/retain 合同相关，不能只删 key 字段而继续使用本地绑定；应把 portable delivery 内容 identity 与实际 store location/retention index 分开。

`private_inputs` 纳入 delivery key（D:10），并把 600 tool JSON复制进去（53–58）。一次凭据轮换可重造整份 runtime delivery。前轮把私有值移出 agent 成分是正确，但仍未移出完整公共交付缓存；SDK 已有 per-attempt env-file + Config.Env 认证通道，应该只传变化的小私有输入。Hosted 如确需嵌入，则使用明确私有 delivery projection，不假装公共可复用包。

D `environment:202–206 → delivery.project` 为 external_docker 先造全自包含目录；SDK 实际 stage 该目录（`arc_bench_adapter.instrument_entry:68–84`），然后 D `docker_workspace._install_child_assets:508–563` 又上传 executor、组件到daemon `/assets` 并 RO bind `/definitions/<role>`（633–636）。bootstrap `delivery_assembly:78–97` 先要求完整 delivered roles 存在，再替换为 mounted roles。因此即使 daemon 已有组件，当前仍不能用薄 delivery；这是新增的设施内部合同限制。应让已认证组件 placements 与自包含 delivery 成为两种明确输入满足方式，而不是必须同时具备。

外部约束要保留：官方 SDK 自身怎么复制 stage、如何计算总 inventory、评价流程由官方接口掌控，不能直接删 SDK 导出定义树破坏它的 inventory。Hosted API 若只接自包含 ZIP，就仍需组合交付。但 SDK 容器已经受控 mount 的新场景，设施额外的完整 runtime 输入不能以 Hosted 的限制为理由保留。

### 4. shared bootstrap 是源码复用，装配权威尚未统一

D `assembly.fresh:63–99` 解析 store、安装稳定 aliases/RO mounts、按 roles 决定 state root；prepared 从旧 target/native 约束归一化。D `execution_bootstrap.delivery_assembly:72–119` 另行解释 delivered paths、可选 definition_bindings/definition_store，自己选择 state root与 proof。D SDK `docker_workspace:661–696` 另造 holder/capture_source/namespace file。物理差异真实必要：controller 有 daemon authority，child 没 Docker socket，也不能读取600控制 store；Hosted 不一定知道 platform run ID。但同一 ref/member 关系、available/unavailable、service requirements 和 entry ownership 不应该三套语义各自增长。

四 main 的 D `variants/pi-braid-i14/main.py:6–35` 同时处理 context、source path fallback、delivery layout、固定namespace文件、旧 package验证、prepared dispatch；四份复制实现。run 的 `134–184` 接线稳定 role，建立 app/native/work/技能链接是 variant 合理职责；`251–259` 又决定 telemetry fallback，且无父绑定时异常可降为 diagnostic。`agent_support.start_local_telemetry:363–384` 与公共 bootstrap/runner继续共有服务准入。应让 runner/standalone/Hosted 选定的 bootstrap先明确服务 ready/disabled/failed，variant只消费；开发源码运行也要走同样入口，不能以“没有 context”就另造一套服务政策。

`harness_layout` 的定义身份与实际路径、derived inputs、state holder 可保留为运行布局记录；不要废掉已修正的 original member+local relative。公共角色需求仍散在 static material_capabilities（D package_agent:223–232）、ARC job.capabilities_required（D local_job:113）、delivery-layout、assembly proof、context.services 和运行期 check。这里有不同维度，不能强塞成一个“capabilities万能字段”。但应收敛为：组件提供的实际能力与 ABI、entry 所需能力、deployment 已验证事实三类；static checkpoint schema4声明不等于 Local fullwriterclosure 或 Hosted SDKresume能力已就绪。

## 删除、迁移与保留的具体对象

删除新路径中“自包含 delivered role 必须存在，同时实际 RO role mount 也必须存在”的双前置条件；不是删 SDK 既有 inventory。删除由通用 package_agent按 variant 名字和私有源码字串猜能力的准入；不是删除 Braid预算/插件继承环境要求。删除四 main 的设施 dispatch 分叉以及 variant 的服务 fallback policy；保留 native profile/skills/application 输出和明确实验输入。

迁移平台 score/legacy证据解释到领域 evidence adapter；迁移 private/model routing/seed 到各自实验输入和部署通道；迁移 delivery决策到消费计划的场所要求；迁移 runtime生产的大锁/索引到组件请求；按 controller/adapter/bootstrap/capture 实际代码闭包部署，不按所有exp源码总hash重发每个场所。

保留 immutable ref/member、源 hash、attempt/producer/platform各自身份与 relation；保留正当跨域传输认证、真实 Mount/Config.Env/birth/service 读回；保留 writer closure、schema4 prior snapshot/newgeneration、Local partial 的诚实限制。ordinary terminal contentcopy 不能事后升级成完整 checkpoint。减少重复认证靠同一消费窗口/不可变发布证据，不靠删除风险边界。

## 可判断的验收

独立验收 report 在 M `runs/developer-experience/post-infrastructure-acceptance-20261003/report.md` 已报告离线 compile 20.328秒、无同条件旧版基线；完整 pack/start/restore/session成本未通过。0.062秒小源码资产反馈不能代替整包或运行反馈。本文没有补运行来改变这些结论。

后续授权真实运行时，不只统计一个总秒数：记录 intent策略求值、输入freeze/import、缺失组件production、delivery、domain安装、namespacebootstrap、service ready、firstentry、firstmodelaccepted、close/capture、repair、handoff/newentry阶段，以及每阶段读取/复制/传输字节、复用实际ref、人工操作和失败重试。平台排队与模型耗时独立标识。

必须覆盖冷启动与同域已有组件两次消费、controller-only/adapter-only/bootstrap-only/variant-only/private-only五类变化的失效传播；同域SDK warmstart不再上传未变化runtime两套材料，private变化不重建公共定义，controller-only不重造Python依赖或Harnessdelivery；Hosted自包含成本单独可解释。compile可在材料未产出时形成完整依赖计划；实际来源变化在生产绑定处具体失败，不靠compile反复全量扫描才安全。

恢复验收必须用实际合法checkpoint，比较同域 definition-only修复与跨域snapshot-copy；同域状态不默认export→prepare整树→upload，旧attempt消费者仍绑定封口来源，新writer许可与generation准确接续。普通Local内容发布可交付，但其partial覆盖不作为完整热恢复通过。

本轮下一步应先在完整责任图上决定上述迁移与删减，而不是再增加operation或隐藏更多argv。通用 public workflow可继续使用compile/build/start/status/recover；这些入口背后必须各有单一决策权威和实际依赖范围。无需要求Agent理解所有内部component、hold、namespace JSON再拼成一次实验。
