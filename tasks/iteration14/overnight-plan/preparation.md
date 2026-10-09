# I14 实施准备：从材料到两轮有效反馈

2026-10-03。此页把[实验设计](design.md)落实为实施顺序、责任及停止条件。用户已授权必要源码、材料生产及基建就绪后自动开工，不再等待审核；实际选择和反馈归[执行](execution.md)。清理与简短通知已经独立完成，不再成为前置任务。

## 当前接续顺序

用户早晨明确要求e2e、cleaner、reviewer全部启动，后明确本地runner为现有WSL/sfp7，撤回macOS/Darwin方向。现有e2e A2保持，新cleaner/reviewer从同一公开GitHub需求远端本地独立完整生成、逐应用官网评分，非seed audit；具体范围见[设计](design.md)。

1. root已按出生身份停止旧serial及新Hosted等待编排，核对无audit-B派发及queue start-intent，保留A2 controller；两个新增槽位仍在原台账，总历史limit=4。
2. provider_fallback作为两项新远端本地生成唯一执行owner，核实WSL/sfp7既有runner/profile、物理存储、准入、材料及实际共享设施；不建立Mac生成环境或迁移共享VM。现有Linux包保留，实际接线需要变化时派生新身份，不改冻结原件。
3. 沿现行Lab schema2冻结两项本地生成及独立逐应用官网评价依赖；具体存储合同成立后启动，保存真实controller/runner/daemon/容器出生身份及首个有效模型turn。根因明确的设施缺陷由owner闭环，不运行设施测试。
4. 生成仅消费公开需求，每条完成即冻结application manifest，由独立self_funded评价job消费；官网同题槽未释放时只等待评价，不暂停本地生成、不重复start。旧409派发保留为未开始生成，不算模型轮次或零分。
5. 现有15分钟5.6-Luna medium监控消费A2及两项真实本地job的保存记录，只报告；root负责总体修复决定与结果采用。生成、应用发布、评价、机制采用及资源证据分别记账，全部终态后汇报，不自动新增候选。

用户已明确允许远端执行数据，Mac侧全部材料、cache、日志、控制及回传仍位于WorkSSD。远端身份、backing和实际容量已读回，按冻结合同使用。新实验复用已生产Linux runtime和原同模型fallback链；两条新增包不得内置seed。provider_fallback持有两项新本地派发责任，root持有A2控制、台账、监控合同及结果采用。

## 三个必要源码接缝

**材料与写入。** 保留runtime的npm锁、11份补丁摘要和managed模块均与当前一致；当前Linux材料已生产并冻结。新生成消费现有WSL/sfp7 Linux runner，不能由Mac默认安装结果冒充。实际读回确认development-2已有精确ARC runner镜像与共享准入，development-1当前仅有Python基础镜像；因此采用development-2现成执行链，不建设Mac环境。两端Docker实际backing均在远端磁盘，用户已允许远端执行数据；Mac侧写入仍严格核对WorkSSD。

实际生产链显式选择WorkSSD的runtime、material-cache、artifact-store、staging、日志及temp。uv/npm/Cargo/Zig新cache分别绑定；短socket目录可使用WorkSSD上的短根。处理本夜会调用的home/default-temp及硬编码/tmp入口，写入前解析真实路径并核对挂载身份，不仅检查前缀。表中未调用的历史Console/Docker/旧driver不是本夜重构清单；外部工具、库及凭据只读消费无需整体迁移。[边界调查](cells/recovery-boundary.md)列出当前事实。

**模型链。** 在现有`hackathon_gateway.py::prepare_catalog()`显式消费本次激活alias集合及每条同alias候选链，不能遍历全部目录后隐式选历史默认。首轮仅Flash、K3、DS0731；GLM root未选，不为它验收或装配凭据。原生Router用`order=0/1/2`表达确定优先级，`num_retries=0`、`max_fallbacks=n-1`，timeout/cooldown与Pi/e2e原生重试一起冻结。

真实账户与请求已闭合，冻结Flash：千帆Token Plan→ARK Coding Plan→普通Qwen；DS0731：千帆Token Plan→千问Token Plan→普通Qwen；K3：ARK Coding Plan→普通Qwen。智谱原厂无余额、ARC额度耗尽，均不装配。已购Coding Plan优先；普通Qwen仅为当前激活模型的按量末位备用，其单价未知不冒称更便宜。精确deployment及请求回执归provider-fallback cell与stage-a包内routes。文字、工具、视觉经同host gateway真实HTTP200；Linux实际加载由官网首轮验证。

K3为ARK→普通Qwen，DS0731为Qwen Token Plan→普通Qwen同ID；前者缺ARK K3 catalog row，后者缺普通Qwen0731 row，只补本轮实际使用项。内部原生selector `factory26/deepseek-v4-flash`须通过既有`FACTORY26_MODEL_BINDINGS`明确映射到gateway的`deepseek-v4-flash-0731`，不靠默认provider掩盖版本差异。DS两路同供应商，只能覆盖部分套餐/账户额度限流，不能宣称容量故障独立；失败按具体原因有界切换，不引入未证同版本的ARK或原厂别名。

千帆GLM-5.3活动价为4.8/16.8/1.2元/M，至10月7日，比BigModel GLM原价各低40%；套餐Credits不能据此折算。GLM后置且不进入首轮依赖。未来实际选GLM时，千帆已购Plan权益/能力确认可用则拟选千帆Plan→ARK；权益未知则拟选ARK→千帆普通。两者各须实际核对账户、精确wire ID和启用能力。ARK不成立时，千帆Plan→普通仅是额度备用，不能承诺独立容量。价格和配置事实归[供应商调查](cells/provider-fallback.md)，不再维护另一份全目录路由表。

现有Portless shared proxy继续承担应用URL，它不能兼作模型Router。在Braid首请求前启动独立run-owned LiteLLM进程，复用已有进程证据与finally清理；绑定后的native model、profile、role及e2e均访问沙箱loopback。Hosted提交的HTTPS ARK字段仍是平台metadata，不用开发机localhost替代。首次请求前失败可切换，已交付内容/工具片段后保留部分输出并失败；不启用Responses continuation或盲目工具重放。记录实际provider/deployment、HTTP响应、流状态和同一会话身份。[模型接缝](cells/provider-fallback.md)是细节入口。

Hosted只提交一个API key，不会自动注入多供应商变量。拟复用`.private`/0600私有ZIP合同，新增选定provider凭据文件，由Harness仅交给gateway，Pi/e2e取得临时本地访问token。公开catalog保留env引用，公开manifest仅保留hash；ZIP解包后须实际恢复private目录0700/文件0600，不能只信ZIP条目权限。原始私有包与普通证据分开存放，原错按实际秘密值精确脱敏。此项已获本夜必要交付授权，host已验证选定凭据过滤、权限与gateway接线；Linux/官方解包反馈仍须实际运行。

**seed与报告。** `pi-braid-i14-reviewer/main.py/run.py/build.py`显式消费application-seed；生产依赖及包身份绑定A manifest，而非仅复制一个目录。A只进入独立work/application；现有初始化只提交空仓库，seed模式必须提交准确应用文件并回读初始tree。正常空应用模式不变。有原commit保留原commit；无commit的合法final snapshot绑定files inventory即可。

seed模式使用明确审阅职责材料，避免默认root继续搭脚手架或从零分派完整应用。查验者保持独立，修改由本次副本的实现职责承担；每项修复必须有公开依据、实际失败或闭合数据流、清楚范围及修复后验证。语义与不足证据项保留。audit gate位于`load_delivery/publish_application/deliver`及preview前；无B不把A复制到交付根。审阅报告引用A/需求、分类、证据、修改及保留项，终态写有界日志摘要，原件沿workspace回收。具体插入点归[实验入口](cells/experiment-entry.md)。

## 证据回收与有限分支

复用基建owner正在优化的hosted monitor，只保留必要采集和终态，不另造collector。首轮开始前必须从进程起点生产并保存资源/native/应用事实，指定现有workspace-bundle回收入口与唯一保全责任人，使提前退出也能立即保全；终态下载适配及定向解析可在首轮期间完成。将现有下载及native/Braid/process-evidence读取接到当前Hosted attempt，取得ZIP hash、平台run、cgroup身份和oom计数变化。平台JSON/logs可以独立保存；缺资源原件只记OOM unknown，不能否认已经交付的应用或分数。

生成状态、应用发布、评分完成、e2e实际采用、OOM证据覆盖、audit完成分别记录。官网test FAILED可以包含有效完整分数；audit无应用的FAILED不是应用零分。缺报告不能称已审阅，无机制证据不能自动改产品。应用artifact不等待全部遥测封口，但报告中结论必须引用其确有的证据。

原Hosted有限队列已退役。原A/A2与新reviewer/cleaner占四个模型机会；同请求fallback及明确发生在生成前的409拒绝不算额外模型验证。拒绝原件和实际派发身份保留，不以更名隐藏执行历史。无自动seed-B或重跑。当前两项本地生成及官网评价沿现有Lab依赖，不另建通用调度或恢复服务。

第三候选只有公开过程指出一个明确未解机制、剩余余额及同条件候选可消费时才派发：工具方案疑问可选现有普通baseline；明确上下文窄修可复验同根e2e；保留e2e的reviewer/cleaner组合若没有预定可用材料则不临时造新variant。分数低、token增长或空闲槽本身都不触发。原因未知、证据不齐或同错重复时保全并报告。

## 实际命令与完成边界

材料交付仍走现有`scripts/package_agent.py --runtime ... --cache-root ... --output ...`，Hosted消费真正冻结的ZIP文件，不把from_production目录当官网输入。seed/gateway额外参数已实现并用于本轮真实材料生产，当前队列不包含seed。实验编译、建立、启动和查询沿`python -m lab.exp compile/build/start/status/wait/control`；recipe与本次run分开，recipe改动须派生新运行。真实路径、命令、冻结身份及派发回执归execution与对应run；已建立的有限等待程序归queued-generations，不把准备或受理称为模型已运行。

验收使用编译、真实制品生产/装配/读回、实际路由操作和获授权官网实验；不新增或运行Factory/Braid测试、模拟供应商、探针或smoke。真实429不存在时只能报告已观察错误类型及未验429，不能声称全部fallback通过。约30分钟未取得入口或有效turn时诊断具体阻塞；连续无语义进展亦定向调查，不以token增长判进展或按时间盲重启。沿已有采集及十分钟摘要消费者，普通状态不反复通知。

实施时先关闭首轮材料、私有Router、预算/存储、起始取证与保全接缝并保存真实读回，然后自动开始首轮；用户已撤销等待审核的要求。seed出口及终态消费可在首轮期间继续完成，第二轮派发前才要求其全部冻结。已经取得的清理、通知、I13分析和基建交付不重做。
