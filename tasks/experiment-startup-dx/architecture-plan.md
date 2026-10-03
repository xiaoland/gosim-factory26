# 实际执行装配与状态接续实施准备

本文落实 `architecture-judgment.md` 的四项合同，供具体开工复核；尚未修改源码或执行新实验。字段名称是拟定 LLD，现有 artifact reference、producer identity、attempt/incarnation、平台 run 与 telemetry identity 原样保留。实施允许增加表达真实关系的版本化记录，不引入中心服务或万能 ID。

## 生产组合与交付

拟新增 `lab/exp/definitions.py`，管理定义组合的严格解析、依赖保留、成员边界和单窗口验证；不承担启动或域调度。`scripts/package_agent.py` 改为生产可复用资产并组合，`environment.produce_materials` 接实际引用。冻结输出为 `factory26.harness.definition` schema1，包含：

- variant 及其 entry（角色名、成员路径、解释器角色），fresh/resume 两种 Harness entry 与兼容性声明。
- `assets`：按实际变更周期分 variant、runtime/tools、skills、facility support；每项 name、artifact reference、member、producer identity 与受支持平台。producer identity 来自真实生产回执，不能手填替代内容证明。
- `roles`：role → asset name + 相对该 asset member 的 relative member，含 agent/runtime/skills/braid/可选e2e；允许同 asset 的嵌套角色，不重复发布整包。
- `derived_inputs`：request、capabilities、native templates、技能链接等由 Harness 创建的 state 内相对路径；必需/可选服务需求与状态兼容协议。

编译前的 intent 保留既有 `from_production` 依赖；build 绑定后 definition 只含实际不可变引用。缓存键是生产输入 identity/ABI，不含实验目录或宿主路径。源码冻结捕获前后仍检查真正可变 source；已发布 runtime 引用不再每个 variant 读一遍整树。store 位置、持有 consumer、生产暂存位置均不进入跨域身份。

delivery 独立模块 `lab/exp/delivery.py` 消费上述组合，生成 self-contained SDK tree 或 Hosted ZIP，并输出冻结 `delivery-layout.json`：每个角色的原 ref/member 与包内明确路径。缓存键为完整 definition 内容身份、delivery 格式/ABI/平台，不因 run 变化。现 `package-manifest.json` 继续是 ZIP 自包含内容证明，增加原组件关系；directory production 不伪造 ZIP manifest。归档/发布已有完整资产直接移交封口目录，保留失败原件，不靠复制到另一生产目录补合同。

## placement 与实际 context

拟新增 `lab/exp/assembly.py` 与可独立冻结的 `scripts/execution_bootstrap.py`（其可部署依赖闭包明确纳入 executor 与 delivery）。前者处理纯解析/装配证明，backend/SDK bridge 处理物理布局；后者持有本域服务、启动、关闭和结果。两者不是常驻服务。

`assembly.json` schema2 的身份/路径分离为：

| 部分 | 拟定字段与语义 |
| --- | --- |
| 来源 | definition artifact/ref、prepared 或 checkpoint ref（若有）、编译公开政策身份；它们是冻结输入。 |
| namespace | Local host 身份/执行实例；Docker daemon/container birth；SDK真实child container birth；Hosted仅包含入口内实际可取得的作用域与delivery/attempt关系及能力，平台run由controller从API原件外部关联。取实际资源回执，不要求平台注入不可取得的run/container birth，不手工填container。 |
| definitions | 每项 role、reference、member、local_root、access；reference/member是身份，local_root只在当前namespace有效。不可用角色显式unavailable与原因，不传父路径。 |
| state | 域内 locator、持有人、实际RWroot、application root、state generation；这个记录是位置/lease而非artifact。 |
| entry | actual executable、成员入口、fresh/resume模式、兼容协议；引用上方实际role。 |
| proof | 域内安装/挂载/成员边界读回回执与verification window。RO能力按真实场所说明。 |

成员运算唯一为 `artifact member / role-relative member / child-relative member`。`harness_layout._identity` 消费 role binding，不 strict-resolve 其他域 root，不丢原 member。SDK rebinding 从 delivery-layout 明确包内路径映射，不使用 basename/role猜目录。

`execution-context.json` schema1 在本域落盘，只允许 bootstrap 创建。包含 assembly摘要、当前 attempt/incarnation、公开模型政策、获准凭据通道的变量名、service instances、owner与本次启动请求。telemetry instance 同时含状态与receiver binding（attempt/stream/epoch/endpoint），resource instance含实际scope/cgroup、sample path及持续采样owner。token与必要私密通道放同域权限受限绑定，不复制到公开记录；不记录凭据值。仅必需服务失败阻止entry；可选服务缺口保留具体原因。

bootstrap 在实际namespace建立资源采样与collector，准备一次context，调用 Harness，持有子进程/必需服务完整try/finally；关闭结果分别记entry exit、service close、writer close。兼容环境变量只从context派生，不再接受并行事实源。旧没有新capability的历史材料沿冻结旧入口，不能无条件要求含Factory support。

四I14 `main.py/run.py` 消费context中的定义与state。Harness仍创建其角色/native request、应用/Git与Braid state，并声明一致切点；不再选采样器/receiver、猜HERE或父域变量。恢复入口 `recover_completed.execute_prepared` 也消费同context，保留Braid/Pi恢复语义，删除其重复资源/路径装配及入口第二次全state inventory。context的组装证明必须针对同次实际安装有效，不能用永久hash缓存跳过Local可写风险。

## 设施代码的冻结与实际部署闭包

新增轨迹 exp23 的 host adapter 修复没有进入本次已冻结 Lab runtime，故运行继续使用旧逻辑；随后实验 owner 在包内跳过 foreign root/fallback package-member 只是旧材料的止血，会损失 retained definition relation，不能作为新contract成功。实际运行轨迹由root保存，本文不将exp25派发当作首模型成功。

执行配方绑定设施代码依赖图：controller/adapter实际executor-code、payload bootstrap/support、SDK bridge、生成delivery入口分别有真实producer source identity及部署角色。definition仅引用实际影响Harness或交付内容的组件；controller/status代码不进入definition/delivery key。Python runtime身份、executor源码身份、Harness runtime与SDK来源仍分开；任何generated wrapper的import只可指向已冻结部署闭包，不依赖ambient PYTHONPATH或host checkout。`controller._source_files/_executor`、host runtime producer sourcefreeze与package support选择必须消费同一源依赖声明，不能只在某一closure补文件。

源码变更使对应设施code资产及依赖它的executor/delivery projection失效，定义runtime/tool资产不随之重产。build读回最终引用与entry import resolution，deployment回执列实际消费ref/sourcehash；public plan/status展示请求版本、当前冻结版本、待生产/待部署资产及为何旧attempt仍沿旧freeze。设施修复必须构建并部署到实际caller，热修复选择新executor/bootstrap通过上述state交接进入新incarnation；直接编辑host文件不会被当已部署，也不改历史runtime。新ABI缺retained关系则具体blocked；只有历史或平台明确partial能力可使用package identity，不自动降级新合同。

| 仅变化的设施代码 | 重产与实际安装 | 不应失效的资产 |
| --- | --- | --- |
| controller/status | 重产controller执行代码与对应controller runtime/source deployment；已有attempt保持旧controller消费合同，公共入口明确新版适用边界。 | Harness definition、共享runtime/tools/skills、SDK/Hosted delivery。 |
| host adapter/SDK bridge | 重产host executor/adapter资产并绑定新配方，安装到实际host执行runtime；只有确实改变generated delivery内容的依赖才重产delivery。 | 未变Harness definition与runtime；不能因host adapter源码变动无条件重打整包。 |
| payload bootstrap/support | 重产bootstrap组件；Local/Docker只取得新组件，SDK/Hosted因包内组件变化重新生成对应delivery投影。 | variant与runtime/tools/skills；平台要求自包含ZIP时仍有真实delivery压缩成本，单列测量。 |


## state holder、公共 capture 与同域恢复

state holder 是现域权威的一条workspace生命周期记录，不是可发布的内容artifact。拟含既有 domain identity、workspace locator、generation、当前writer resource/incarnation、pending transition/capture request与实际能力。Local将持有WorkSSD本机状态目录中的锁/耐久动作记录；Docker沿现admission workspace registry；ARC bridge登记真实child及SDK派生writers，不能用外层Local停止代替child。未知或域外writer明确阻塞完整capture。

新增公共 `lab checkpoint EXP ATTEMPT --directory ... --request-id ...`：controller只编排backend受管动作，不要求调用者提供closure JSON。动作序列是：

1. 校验期望incarnation，在原权威短事务中登记 `transfer-pending` 与state generation，阻止新增writer；不持长文件锁跨停止、构建或输运。锁外请求Harness一致切点、物理关闭entry及已登记access/service写者，逐项确认出生/终态并writer-close。服务close不替代状态writer close。
2. 域权威取得capture lease，阻止新增writer；保存closure所覆盖的writer集合、workspace generation、实际domain证据、capture token。沿现 `capture-begin/end` 请求重入规则，失响应只query原请求，不重复启动资源。
3. 在lease内捕获Git/SQLite/native与应用的同一切点，生成不可变checkpoint；定义仅保留refs。文件复制/快照与语义检查在此边界执行。checkpoint发布成功前不释放依赖或原state；失败保留snapshot半成品与lease，重入明确继续或abort。
4. checkpoint回执保存原execution/platform、closure与冻结内容，才结束单独capture或进入恢复计划。新模型运行不是checkpoint动作的隐含行为。

现schema3 checkpoint可以表达state-only+refs，优先复用；若新增holder relation需要schema升级，只升级该字段合同并保留旧schema读取，不重新定义identity。历史checkpoint缺公共closure或旧混装不自动变完整。新prepared采用两种明确绑定：`snapshot-copy`（现跨域/离线prepared合同）和 `domain-state`（同域计划引用closure+不可变checkpoint+可变holder）。后者不是把active state宣称为immutable artifact，不能复用旧prepared字段伪装自包含。

同域 `recover` 规划definition/derived修复、验证原native逻辑根和兼容性，再准备新attempt的新resource。旧Docker resource不能restart（admission现single-use），新resource挂同holder state；Local新进程也有新出生与incarnation。写权交接以holder generation+来源checkpoint+预期旧incarnation+新resource为CAS；在同一个权威事务中清除capture并将唯一writer许可交给新resource，不能分成capture-end后任意writer-open而留下抢占窗口。实际创建/启动继续按原pending/readback机制确认。跨域恢复仍从snapshot-copy输运state及目标缺失定义，不把源holder路径当目标路径。

domain-state 的 derived repair 是真实可写变更，必须在capture owner持有独占许可期间执行。每次修复以既有request identity记录预期holder generation、来源snapshot、变更清单和每项完成事实，完成后冻结repair readback/兼容检查，推进到新state generation。修到一半失败仍保持blocked与capture，不套用来源checkpoint的content proof；重入只完成原请求的未完成项，或经显式abort/restore动作从保留snapshot复原，不能自动回滚可能的新有效内容。handoff只接受完整repair和目标assembly回执绑定的新generation，未改state的definition-only修复也须记录这一事实。

在handoff之前，旧attempt所有state消费者必须转到来源snapshot：named outputs、terminal archive、后台export与Console状态读写入口的定位关系先封口并耐久保存。workspace整树不再独立复制两次，输出引用snapshot的明确成员/关系；旧Console writer先关闭，新Console需向新holder登记。后台归档若未完成，仍仅消费保留snapshot，不得在新writer开放后读活动workspace。state外不再写状态的旧日志可以单独收尾。此迁移是写权转移的前置条件，而不是事后显示修正。

旧attempt的输入、错误、entry退出、closure和checkpoint ref永久保持冻结。新运行修改同state后，旧attempt的workspace locator只能解释为“原域位置”，其结果展示/回放读封口snapshot；不会继续把可变目录的当前内容当旧attempt证据。回退也基于不可变snapshot恢复，不把新代码退出等同可以覆盖进度。公共status给出holder当前writer、新旧attempt关系、snapshot来源与合法操作。

capture owner与old writer必须分离：现admission以resource_id持有capture且release要求capture关闭，需为snapshot/handoff保留独立未release的受管capture责任，不能复用已release资源。原execution关闭writer后可release，但state卷/目录的物理保留归holder，不能随原execution cleanup删除；capture在独立资源持有期间持续禁止新writer。Local不能只加一把进程锁就声称覆盖全部writers；所有平台允许的access入口必须加入相同registry，不受管外部编辑是能力限制。具体registry迁移按advisor复核结论实施。

## 实际 caller 替换表

| caller | 实施后行为与删除项 |
| --- | --- |
| package_agent selection/assemble/produce；四variant build.py | 冻结组件引用，独立variant输出；删每variant复制/重hash完整runtime。交付投影统一生产缓存。 |
| environment resolve/produce_materials；controller build/verify | 保留未生产依赖，绑定definition refs；同窗口同ref一次解析；生产发布移交，不再要求directory package manifest。删相邻重复full verify，保留跨域首次安装和可变source检查。 |
| compiler + arc_matrix/local_job | 继续领域operation，共享job构造，输出definition/execution需求；恢复模式也通过相同assembly，不让用户填私有SDKargv。 |
| runner _input_bindings/_assemble/_ready_services/worker/docker_worker | fresh不再旁路；fresh/prepared调用共同assembly/bootstrap。父runner只监督实际子域，删父sample/receiver直传及重复bootstrap。 |
| backends prepare_docker/collect/export/managed | 按assembly显式ROdefs/RWstate；stateholder贯穿启动/收集/导出/capture。停止/快照/交接用域权威，保留containerbirth/失响应重入。 |
| ARC instrument_entry + docker_workspace runner_main | 保留SDK参数/容器/输运桥，delivery布局接入共同bootstrap；删生成wrapper内独立sampler/collector/rebinding/政策解释。总SDKinventory不删材料；新layout成员显式证明后组合归档。 |
| 四I14 run.py/main.py + recover_completed | 统一context消费者；Harness保留原生恢复/一致切点；删双重服务选择、位置猜测与恢复入口重复inventory。 |
| exp_checkpoint capture/prepare | 公共managed closure供给；快照与可变holder分流；同域计划不复制完整state，跨域仍snapshot-copy。 |
| runner _seal_outputs/_archive；Docker named outputs | 整workspace单次封口；workspace named output与archive引用同封口，capture关系一致。应用artifact独立冻结；不延后成本冒充减少。 |
| hosted dispatch/export；replay | 复用definition→delivery，bootstrap使用真实平台条件；capability明确不支持pause/resume/checkpoint。平台partialexport保留原身份，应用replay不冒充state恢复。 |
| package/runtime sourcefreeze与文档 | 新assembly/bootstrap/dependency闭包固定；旧runtime不改。更新既有技术/运行说明与projection，不把task文档升成第二套权威。 |

## 能力与失败行为

Local默认只承诺verified read与写隔离，定义目标占用冲突则ready blocked；新ABI稳定role路径与old native绝对路径明确分流。自有Docker能RO挂定义并RW挂holder，新域缺原逻辑挂载/平台不匹配则blocked，不覆盖。ARC child需实际SDKcontainer身份、模型传播和其本地服务；完整capture仅在所有SDKwriters可受管且state locator有真实mapping时支持，否则说明具体missing capability，不自动改成fresh生成。Hosted上传/启动/停止/导出按API支持，平台拒绝和409原件照存，不因为无法热恢复绕过正确门控。

发布/安装失响应先查原request/ref/proof；不明效果显示unknown及下一合法query，不能启动第二entry。必需role未装配、member越界、actualref不同或服务binding跨域属于启动前失败；启动以后provider错误与Harness失败保留其原错误，不混成设施准备失败。

## 实施顺序与有界反馈

1. 固定字段与所有caller迁移，尤其capture责任、Local登记覆盖、context私密绑定和旧prepared兼容；先给具体实施说明复核，不在本准备阶段编辑源码。
2. 生产组合与delivery、单窗口资产解析，取得真实现存材料的directory/ZIP读回和sharedref复用反馈；不重建大runtime，只读真实producer原件。编译新模块/生成entry。
3. 同一纵向实现Local/Docker fresh+prepared assembly/bootstrap与四I14消费；同时迁ARC/Hosteddelivery消费者，不保留第二套新服务入口。历史冻结入口明确旧合同。
4. 公共checkpoint受管closure与stateholder交接、同域/跨域recover分流；终态单封口与旧attemptsnapshot来源同步完成。不能以fresh成功宣布本轮收束。
5. 无模型离线反馈仅操作真实已发布小资产、真实checkpoint（若可取得），记录ref/member/retain/实际目录装配/编译，保存操作原件。缺新完整runtime或writerclosure时明确未验，不造fixture/mock/probe，不运行设施测试。

最小后续真实实验需单独授权：在自有受控Docker域，一case、一模型、一I14variant、既定单session预算，fresh启动到明确有效进展后受管capture；仅小代码/定义修复，保留同state接续，记录Git/Braid/native来源；完成应用冻结与已有授权评价边界。验证四variant通过各真实生产/装配材料操作，若其专属服务不能离线证明则另列必要小运行。ARC需一次真实innernamespace启动/服务采样/退出输运，恢复能力仅在已获SDK完整writer覆盖时追加；Hosted仅一次真实delivery消费/平台能力原件，不能为了矩阵覆盖虚构其resume。

冷cache/warmcache、改一个variant、多variant共享runtime的打包成本分段；启动从用户操作记至实际entry，另记provider首次活动；热修复从stop到恢复entry，跨域单列。每段记录monotonic耗时、hash读取字节/遍数、复制/传输量、实际占用峰值与终态。所有本地输出必须WorkSSD，远端执行环境须先满足该任务已约定的实际存储边界。没有可比较基线与完整恢复证据前，不承诺提速比例。
