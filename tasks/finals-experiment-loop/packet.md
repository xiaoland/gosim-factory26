# 决赛实验基础设施改进

## 目标、授权与完成标准

让使用者以 variant、run target、task 开展运行，低负担地观察、控制、接续、保存、评测和分析。simplicity、agent-friendly、traceability/observability 以完整使用链的时间、token、排错及信息搬运成本判断。Exp Console 属于交付范围，WSL、sfp7、官网差异属于设施应处理的集成问题；组件启动、编译通过、模型请求成功均不能代替整体完成。

用户于2026-10-06明确授权：“好的，没问题，你可以开工了；你可以自由提交……按你说的用独立会话验收，你可以使用真实模型，不需要 mock，费用不是问题。”随后批准资源管理、runtime精简/部署优化、公共分层和应用环境统一。可实施、部署及提交本任务改动；不push，不覆盖其它任务修改。Mac产物全部在WorkSSD，不编写或运行Factory/Braid测试、smoke或换名自检。

验收仅自费、非排名，绝不参赛；对象为 `I14-dx-test`、`pi-minimal-vv-dx-test`。完成须取得正常入口的生成—保存—自动评测链、控制及同variant接续/stages、采集驱动策略、Console分析证据，并报告外部覆盖限制和真实使用成本。当前整体未完成。

## 当前设计与资料归属

- 控制单位是run；experiment只是标签。无内部capacity、queue、slot、reservation或准入gate。
- pause/resume操作同一run；restart迁移同variant的data并创建新run，不允许换variant，不设continue/extract。program、inputs、data、records分离。
- 公共设施拥有最终装配、运输层、collector和安装入口；variant拥有角色、供应商模型配方、原生接续及活动解释。Local/Hosted使用同一安装合同，不预装完整开发环境。
- 自费model-proxy抹平运输差异，variant消费base URL/API key；已批准比赛合同直接消费平台注入，不应用供应商配方。用户后来提出透明比赛统计代理的可能性，尚非已批准的新比赛交付；当前代理会改参数/fallback，不能直接当透明代理。
- status分开显示lifecycle与variant activity；Console只读保存事实，本地共享Collector/Backend、Hosted轻量落盘，Braid拥有自身视图。
- memory与pids/线程触顶有界补救，无法恢复明确失败，不持续pause掩盖失败；Tini回收孤儿，工具仍须关闭并等待自己拥有的进程。
- 普通Python策略读取采集变量并调用run API，自定义策略不替代默认自动评测。不引入策略DSL、默认预算门控，不要求用户先提供I15停止线或余额。

合同见 [design](design.md)，批准实施范围见 [implementation](implementation.md)，验收标准见 [evaluation](evaluation.md)，详细证据边界见 [assessment](assessment.md)。[整理前记录](history-before-reorganization-20261007.md)只用于追溯，不从历史“正在”推导当前状态。

## 工作情况：实现与验收分开

| 工作面 | 已交付与可采用事实 | 剩余交付 |
| --- | --- | --- |
| run入口、执行、控制、数据布局 | 两DX已真实运行；Pi pause/resume、WSL→sfp7同任务接续有实际证据；失败及用户指定停止现场已保存 | 两DX完整生成/保存/自动评测；下一task新原生身份与业务数据保留、stages完整链 |
| 公共装配、runtime、构建部署 | 同一安装器及公共最终装配；程序材料约16MB，安装约512MB；普通observer开发来源约246MB→2MB；源对齐release实测2分02秒 | 正常操作冷/热耗时及总成本归纳；不能把材料大小当安装占用、静态体积当普遍提速 |
| model-proxy与供应商用量 | 修复reqwest Linux默认30秒TCP期限，Pi实际大请求跨过期限并按原配方返回；I14新代理实际取得千帆/ARK returned usage；Hosted平台运输已接通ARC单价与native usage的部分费用小计9cf8690c | 现代Hosted实时费用及策略动作未验收；旧Pi冻结代理无新usage捕获，不反推历史；代理源码混合未提交材料需按归属收口 |
| 持续采集、Python策略（当前最高优先级） | watch读saved facts并保留原时间；策略不替代自动评测；Hosted约6/8分钟工作区采集，只读运行事实；GET/ZIP移出控制锁，stop不另起采集 | 现代Hosted导出、采集期间控制及策略实际触发未验收；金额unknown，token不是账单/比赛额度 |
| 资源管理与进程回收 | memory/pids监控、有界补救、明确退出及Tini已实现；真实Linux浏览器一次生命周期无浏览器残留；长run有采样 | 长运行回收与真实触顶补救/退出证据未齐，不制造故障填表，不把采样当峰值 |
| Console、OTLP、Braid视图 | Pi首页/详情及自动刷新实际可用；Braid入口不再猜variant名称；SQLite并发初始化修复后batch增长；轻量Summary生产/消费已提交并Linux编译6分07秒 | Summary新ELF尚未用于在途run；最新reader/静态页最终部署及动态协作视图未通过；最终评分分析待产物 |
| 四测评后端与应用环境 | task/simulate/official/self-test接线及认证存在；Node20应用/Node24工具分离已有真实Linux安装、后端17项应用验收、前端构建及health200 | 本轮新应用未形成，评测结果未齐；旧Hosted生成关闭保留拒绝证据，self-test仍须完成 |
| 独立使用成本 | 历史冷读profiling、实际操作及失败原件保留，验收性质已更正 | 当前是受辅导集成修复验收，不能证明陌生使用者低负担；主侧排错/信息搬运计入成本，不为形式纠偏追加收费运行 |

应用环境专属证据归 [应用环境packet](../harness-app-environment/packet.md)。上述实现交付不自动转为已验收。

## 实际运行与在途状态

19:48按用户要求深入检查工作区：Pi不是完全停滞，但74个请求中53次千帆HTTP500、两次ARK429，失败attempt累计等待约115分钟；首页截图白屏，App.jsx使用UserContext却缺少导入；浏览器长socket路径失败及跨shell未继承session造成双daemon。19:48:54生成Agent自行取得ReferenceError并开始定位。I14原evaluation_closure负责人返回只读证据：PR #2在19:46:50收到changes_requested，随后root/fast仍在执行；325次供应商attempt中311次200、14次429，没有Pi式连续500/130秒失败等待，header平均约3.99秒。两run均无最终评分。详见[晚间运行诊断](runtime-diagnosis-20261007.md)。本次仅诊断，未改变运行/配方或代修业务应用；“active”不能再被解读为运行顺利。

2026-10-07本次整理直接读Mac保存事实：Pi `a3a9a5262b8b40f382883ed636758464`（BookStack）as_of=1791369786、I14 `ed426cf521bd4f46ba58629f4acbd3e3`（github-stage-1）as_of=1791369832，均running/active、自费、不参赛、sfp7执行。未取得本轮终态/最终评分。原件为 `runs/lab/runs/<run>/records/status.json`，这里是带时间读回，不是永久实时状态。

Pi来源d3cc，保留scope f1335fc，冻结代理6f1e07修deadline但无后续usage捕获；I14来源756，保留scope782227，实际消费源对齐Braid fbcd2c及usage代理fd0869。此前“本地修源码、远端仍编旧输入”已定位并修正；哈希一致不证明编译输入正确。

独立会话 `01a114ec-c77a-7531-930b-9321fee3982f`，标题“Lab 新一轮完整独立验收”，本次查询idle、最新turn completed，cursor `495e1ea6-393a-4f0a-9a7a-72c8514cf488:78`。它不是当前正在执行的验收负责人；run observer/自动化与聊天独立。旧会话已停用，610daf已按用户“停止并保存现场”执行并回收。

## 委派情况与责任收敛

上次整理时只有主Agent running，其余可见assignment均completed。用户随后明确“按合理的优先级、责任分配，推进”，主已续派execution_owner完成持续采集/费用事实与Python策略工作面，主继续既有run保存/评测闭环。advisor未唤醒。本轮不新增模型生成或控制其它任务run。

| 负责人/角色 | 已承担与采用结果 | 当前责任、状态 |
| --- | --- | --- |
| 主Agent `/root` | run/自动化/集成，proxy后续修复，编译源对齐，Console/Braid后续修复，采纳返回与提交 | 活跃；拥有总目标、优先级、所有未验收项和运行闭环，不以已委派卸责 |
| execution_owner（执行者） | runtime/安装/部署、公共入口/Tini、应用环境；Hosted采集/控制采用80794c7a；时钟回拨修正daa96533；策略文档616f4290 | 本轮已返回。再次联系受thread limit拒绝、已不在live tree；费用实现由主明确接管，不再声称其在执行 |
| evaluation_closure（执行者） | Pi评测材料冻结b514103f、控制端deferred task/self-test派发700ea0d0；当前远端与Mac包外自动化已实际更新 | 本轮返回completed，无其报告中的SSH/复制在途。Pi生成与评测后台继续；最终评分未形成，残余责任归主，后续同工作面优先续派此owner |
| competition_cost_decision（advisor） | 短控制锁等建议已采用；本轮只基于主提供的价格/用量证据建议partial已知小计及ARC适配归属 | completed；未调用取证或实施，主决定并实现；此前角色越界不沿用 |
| process_reaping_decision（advisor） | 标准Tini/subreaper、保留Popen退出状态所有权、不设全局并发gate建议已采用 | completed，不负责资源实现或验收 |
| acceptance_conversation_decision（误用advisor） | 历史会话取证及评价文档修改已采用b84d6d52 | assignment已结束，不在live tree；保留证据不重做，调查/编辑不再交advisor，该低优先级项不扩展 |
| cold_local_profile、cold_console_profile、cold_hosted_profile、evaluation_implementation等历史执行者 | 历史控制/回收、Console、平台拒绝、自测认证/评测接线，材料已保留 | 不在live tree，不声称持续工作；后续已由主接管，评测残余义务归主，不挂在不可达owner名下 |
| 早期profiling、文档预演及完成标准advisor | 标准、设计取舍及只读反馈已融入design/evaluation/assessment | 已结束，不是实现或最终验收负责人，历史见整理前记录 |

用户2026-10-07明确纠正：“advisor 是给建议的，怎么会变成执行者？而且也不应该让 advisor 去收集证据啊”。当前分工：执行者收集证据，完成调查/修复/操作/验证；主把目标、约束、证据及一个待决问题交advisor，仅请建议，主决定，执行者落实。advisor不当reviewer、调查者、文档作者或监控执行者。已有材料不因纠正分工重复调查。

## 当前推进顺序及剩余责任

用户随后确认“不记住失败是正常的”，要求先修其它问题。当前不改变千帆等待期限、fallback跨请求记忆或在途配方。主修submission/runtime_install.py的公共短socket目录（按原目录hash隔离，Linux临时socket与Mac WorkSSD分别落位），修浏览器技能示例为每条命令显式session；未来程序消费，未热改在途冻结材料。用现有Pi容器、独立诊断session实际打开现有首页、读取交互元素并close，原超长名称task-8945cd75636e在短目录下正常，无需代修应用；原生Agent已自行修好白屏。第一次诊断命令的shell引用错误未启动浏览器，保留工具回执，不记作产品失败。

Console原owner续派被thread limit拒绝，主明确接管。查明reader文件18:06更新，而服务PID1318330从18:02运行；静态页hash也落后。主更新Braid静态页并只重载Console至PID3951941（20:19:46），静态页hash已与源码dca6014b一致，reader文件hashc13cfae8一致。生成容器与observer未重启。API旧投影仍为空/partial，需要新worker回执进一步判别；不能把部署完成当动态视图通过。evaluation_closure已续派负责两run实际保存/自动评测，尚待返回，不暂存/提交；主统一处理Git index。

1. 持续采集、费用事实及普通Python策略最高优先级。Hosted实现已返回，后续实际qualification优先续派execution_owner；主拥有消费/自动化接线。金额、策略动作和控制边界须分别有证据，不用预算问题阻塞设施交付。
2. 主完成现有两条自费run的生成—保存—自动评测闭环，已有observer是唯一采集者，不频繁读心跳或派同条件run；明确设施缺陷按原授权修复，保留实际消费版本。
3. 产物形成后，主收口同variant/new task/stages、各评测后端、Console结果分析与总成本。非阻塞Braid视图明确留缺项，不为视图重启模型。
4. 主按归属整合本任务未提交源码/文档并逐项提交；不整目录提交model-proxy或Braid dirty tree。整体报告再次核对目标，不以最近局部修复代替完成。

当前不需要用户给停止线、余额或新许可。此整理不改变原目标、费用模式和比赛禁令。

本轮实际核对发现I14 ed426的冻结task_config没有evaluations，现有默认自动化会直接返回而不评分。主已给维护的github-stage-1/2任务配置默认self-test，后续正常启动消费；不改写ed426冻结manifest。为当前ed426补普通后台脚本 `records/finish-evaluation.py`，等待正常completed及Mac result-save成功后独立self-test，失败/停止则不评分。进程PID66676已实际启动，回执phase=waiting-for-generation；来源、PID出生身份、日志及结果均在该run的records。它不是新的采集者，不创建模型生成，self-test不参赛；此时尚无评分证明。Pi a3已有随题评测配置，保持现有自动链不重复派发。

随后实际ssh读回确认Pi远端task_config.evaluations中的requirements/tests均为null，Mac路径在manifest relocate时被清空；不能继续声称其现有自动链已经具备完整输入。已委派evaluation_closure处理共享材料边界和当前冻结run包外补救。远端四个observe/default进程均实际存活：Pi233116/245040，I14 968810/984993；不以进程存活宣称生成或评测完成。主侧I14补充评分进程已再次读回alive，尚在等待生成。

execution_owner本轮文档返回d8d4f8d4已读取，但“没有run账单就必须unknown”及idle额外资格要求不采用为合同：actual须账单，estimate可来自已核实ARC单价及本run usage并保留coverage；脚本自行解释原生时间/工具等待，不由设施增加idle gate。主已合并反馈给原owner继续具体计价取证和必要reader修复，不把文档补充当费用工作面完成。

费用owner后续返回616f4290及价格适用性证据，仍未实现estimate；再次联系受agent thread limit拒绝且owner已不在live tree，费用实现明确由主接管。competition_cost_decision仅基于主提供的证据建议partial已知小计、显式missing和ARC适配归属，主采用。主复用已有Pi费用算式与今天18:27的ARC价格原件，新增公共arc_spend及价格表，Hosted仅在model_transport=platform且无终态账单时投影estimate；首次价格快照保存在records/platform，源价格/usage时间分开，自费供应商不套价。多个native scope用量合并，不由最后scope覆盖前者。对历史已归属ARC的真实完成响应数据只读重算¥15.550208680000003，与原小计¥15.55020868仅浮点尾差；这不是新参赛或新运行验收，现代Hosted实时消费/策略动作仍未通过。旧self-funded ZIP用于解析/算式读取，不将其ARC套价结果认定真实金额。

本次真实docker top只读快照（as_of=1791370827）：Pi8个进程、I14 13个进程，均无僵尸；同时保存资源样本pids.current为34/62（含线程），两者pids.events.max=0，memory.oom/oom_kill=0。I14 memory.events.max=206是累计边界，不冒充OOM或当前持续触顶。此证明长运行当前无僵尸积累样本，不证明所有工具生命周期或触顶补救已通过；没有为资源验收制造故障。

evaluation_closure已交付b514103f：冻结requirements及约24KB tests到run inputs、传输后remote manifest指向真实远端路径，现场仍由原observer233116/default245040与Mac relay50624执行，没有重启生成。主采用其原件与实际路径读回，不重复调查；后续仍由同owner核对sfp7 default→wsl评测宿主的必要执行接线并收取评分结果。当前不是已完成评测。本轮最高优先级费用实现提交9cf8690c，跨组件partial语义提交d4e7e474；两run最新保存facts仍running/active，尚无最终应用与评分。

后续该owner实际确认sfp7→WSL DNS/host-key不可达，Mac→WSL及SDK/image/run root可用；评测改用已有Mac relay在保存后派发，不要求用户补SSH接线。当前源run的default245040已替换为2525159，Mac relay50624替换为97137，部署使用700ea0d0；原observer233116和生成容器未停止/重启。实际回执为 `records/evaluation-automation-repair.json`、`evaluation-relay-repair.json`，材料/旧manifest亦保留。共享index在主提交assessment时纳入该owner已暂存的两个本任务源码hunks，700ea0d0说明未准确覆盖代码；已告知owner勿重复提交，本轮后续统一由主暂存/提交。没有他人任务source纳入。这是包外自动化热部署证据，不是已取得评分。

主只读刷新完整ARC价格尝试：已有meter.cookies请求/api/user/models返回401 user authentication required，现存Helium支持模型panel也显示同一错误；未查询余额、未要求用户重新登录来阻断交付。维护价格表继续明确采用今天10:27 UTC的已保存原件，两已核实模型之外保留missing，不声称完整当日模型价格覆盖。后续新鲜价格可更新公共表，新run观察会记录自己的版本；已有run沿用已保存价格。

## 关键交付和证据

- Python策略：a439ae26、f3c41f36；Hosted事实消费：d92b074c；周期采集/控制：80794c7a。
- Console/Braid：17d6da0b、dbcae9e2、f80f3546；新Summary编译材料：`runs/finals-experiment-loop/validation/cooperation-summary-*`，未动态资格化。
- 源对齐：b19dc7b0；`runs/finals-experiment-loop/validation/i14-source-aligned-build-*20261007*`。
- Hosted真实旧self-funded ZIP：`runs/finals-experiment-loop/validation/hosted-workspace-observation-20261007.json`，423条assistant usage、2session，重复读changed=false；旧包无现代gateway/resource，不宣称现代导出/并发取消通过。
- 受辅导验收纠偏：b84d6d52；所有原失败和旧现场保留，不覆盖为成功。
