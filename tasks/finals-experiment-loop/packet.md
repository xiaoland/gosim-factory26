# 决赛实验基础设施改进

## 目标、授权与完成标准

让使用者以 variant、run target、task 开展运行，低负担地观察、控制、接续、保存、评测和分析。simplicity、agent-friendly、traceability/observability 以完整使用链的时间、token、排错及信息搬运成本判断。Exp Console 属于交付范围，WSL、sfp7、官网差异属于设施应处理的集成问题；组件启动、编译通过、模型请求成功均不能代替整体完成。

用户于2026-10-06明确授权：“好的，没问题，你可以开工了；你可以自由提交……按你说的用独立会话验收，你可以使用真实模型，不需要 mock，费用不是问题。”随后批准资源管理、runtime精简/部署优化、公共分层和应用环境统一。可实施、部署及提交本任务改动；不push，不覆盖其它任务修改。Mac产物全部在WorkSSD，不编写或运行Factory/Braid测试、smoke或换名自检。

验收仅自费、非排名，绝不参赛；对象为 `I14-dx-test`、`pi-minimal-vv-dx-test`。完成须取得正常入口的生成—保存—自动评测链、控制及同variant接续/stages、采集驱动策略、Console分析证据，并报告外部覆盖限制和真实使用成本。当前整体未完成。

用户最新决定：“不必这样继续真的运行下去，太浪费时间了，提前终止或者虚假完成”。本轮采用提前终止而非修改完成事实：停止Pi a3a9a526与I14 ed426并保存现场，撤销尚未派发的stage2和评分等待，不继续付费生成或填验收矩阵。停止前最近保存事实两run为running/active，没有最终保存、评分或stage2；在途模型与工具可能被中断，已有持久化进度需保留，不承诺完整检查点。执行负责人evaluation_closure负责正常控制入口与远端/Mac回收，主负责结果采用与未验收边界。App续办automation已实际PAUSED。设施改进没有因此被标记完成。

本次终止已实际完成：两run均stopped，远端和Mac result-save均saved:true/errors:[]，范围为data/workspace、data/harness及records，原件在各run records。I14 stages-progress为cancelled-before-dispatch，只有原stage1 run；finish-evaluation-result为cancelled-before-evaluation，未取得评分。Mac relay、stages与评分等待进程的已记录出生身份均lost，后台收尾已退出。回收途中Pi遭遇rsync mkstempsock Invalid argument，修复公共save运输为不复制Unix socket及device等非持久化特殊文件；新relay实际消费后两run成功回收，不把先前失败改写为成功。没有修改应用、伪造completed或新增运行；剩余正常完成评分/stages及其它未验收项如实保留，不再自动开展长时间真实验收。

## 2026-10-08 整理后接续

用户确认命名方案：“同意”。当前 restart 默认同 variant 从零重跑，restart --keep-data 显式接续；两者都停止并保存来源、创建新 run，不删除旧现场。pause/resume 仍为同 run。evaluation_closure 负责执行入口、CLI、Python/stages 及历史模式展示，主负责现有操作与技术文档、采用和只提交本次增量。没有授予新生成、收费验收、评测或参赛操作。历史 source.kind=restart 不重新解释；本次新记录明确是否继承 data，所有依赖接续的维护调用改为显式 keep_data=True。Console 当前只读且没有 restart 入口，不额外添加界面。验证以编译、帮助入口与既有保存事实为限，新模式的真实重启尚未资格化。

本次实现已采用：新来源只持久 source.keep_data，模式标签由该字段派生；历史缺字段按原保留数据解释，原生身份是否继承另看 native_resume，不从应用接续推断。默认 fresh 不复制来源 data，仍复用同题冻结需求、初始基线、题目测试和模型输入，路径重绑定到新 run；keep-data 走原迁移流程，snapshot 不允许在 fresh 模式偷偷生效。CLI、公共 Python 和 stages 已同步；旧 Pi/I14 状态只读显示 keep-data，帮助入口列出 --keep-data，Python 编译通过，没有启动、停止、评测或更改任何运行。提交只纳入本任务增量，保留其它在途 source、阶段自动启动和文档修改；新 fresh 的生成、保存及评分闭环仍未真实运行验收。

用户批准接续体验三项修复：“名称后面再修吧，我同意这三个修复，请落地”。继续沿用restart命名；监控跟随与恢复摘要由evaluation_closure负责lab公共接口，native_recovery_activation负责variant/Braid职责恢复的调查、窄修复与编译/已有事实验证。主负责边界取舍、合并及仅本任务提交。允许必要源码、材料与文档修复，不据此启动或控制其它任务运行，也不恢复已停止收费验收。原有source_run关系继续为来源，不增加实验或chain控制对象；只读跟随不改变具体run控制，分支不猜选。职责激活使用领域正常事件，不硬编码设施评论或普遍清空重试。变更前保留相关混合dirty的精确边界，源码/材料交付和真实运行资格分别报告。

上述三项源码已落地。`lab status RUN --follow` 和 Python `watch(..., follow=True)` 跟随明确的restart直接后继，终态尚无后继时等待，有分支则交回明确选择；控制不重定向。接续摘要分别展示保存、派发、执行入口实际消费的程序/runtime身份、当前producer请求及原生工具动作，缺回执保持unknown。公共包安装后写小型消费回执，既有本地和Hosted采集回收，无第二采集者。共享native reader把同日志匹配的toolCall/toolResult及当前run时间边界输出为effective_action；HTTP、active及泛化活动证据不代替动作，工具错误保留outcome。Braid显式offline-resume仅对当前OPEN责任、idle原生会话、最新ordinary整轮failed、无待处理事件/wake的工作发正常wake，按failed turn去重，不清重试或重开closed。I14-dx-test和I15已有共享reader/offline-resume接线，因此后续装配消费修复。

反馈采用编译及既有现场只读操作，不再收费生成：Python编译与Braid cargo check通过；既有d3cc→a3a9接续链的watch实测先handoff再等待，a3a9保存状态仍无新字段，不能声称旧运行已消费新代码。新native reader只读a3a9原件耗时0.029秒，返回本run已完成bash工具及无reader error，没有写回旧status。原生修改前dirty边界保存在 `runs/lab/recovery-activation-verification/`。本轮未给既有运行热部署，未动态验证新版入口消费回执或Braid异常责任唤醒；这三项为源码交付、部分真实保存事实验证，不代表整项实验设施资格化完成。后续若获运行许可，只需在正常接续中检查这些新事实，不扩收费矩阵。

用户补充真实接续反馈：两次正常stop/save/restart保留应用、Braid和原生会话，修复版材料使负责人恢复有效工具动作；仍须人工切换监控/token口径，耗尽重试的Issue要由正常事件唤醒，实际生效事实分散。此反馈不是本任务停止验收的恢复许可，不操作其它任务run。主只读确认restart已有source_run、同task复用native_scope，而watch固定run并在终态退出。advisor只依据上述事实给建议，未调查或实施。当前采用推进方向：先利用既有来源关系减少只读监控接续负担，具体控制仍绑定明确run；本run producer切片与原生会话全量分开，不能相加复计。其次将材料采用、接续后请求和variant有效动作汇成已有采集事实的摘要，不加gate/第二采集者。Issue唤醒归variant/Braid正常事件机制，不能在公共restart里硬编码评论、批量重开职责或清空重试计数。自动跟随、职责唤醒及反馈摘要均尚未实现/验收；主保留此后续责任，下一步核对监控消费者与variant恢复入口后在已授权设施范围内收口，不追加收费矩阵。

用户进一步明确CLI优先，并批准统一现场保存方案：“是的，而且‘不混入安装 runtime’很重要，官网下载下来的 project.zip 需要我们额外剔除掉安装的开发环境。开始。”本次由原保存负责人evaluation_closure接续实现 `lab save RUN`，统一人工与终态保存链，交付含data/workspace、data/harness、records与来源身份的可搬运包；主负责采用及仅提交本任务修改。只排除实际设施安装目录，不按node_modules名称误删应用依赖，官网原始导出保留证据。运行中取包属于非一致现场快照，不停止或伪造终态；终态复用已保存现场。验收采用既有停止现场，不恢复生成、新增评测或参赛。Console下载不在本轮实现范围。

本次CLI实现已采用：save正常输出package、source_as_of、packaged_at、排除数量及gaps/errors，--json提供完整回执；包内携带规范数据与最终采集/排除说明。运行中使用独立源快照回执，不写终态result-save；Hosted人工live每次重新取包，不永久复用第一次快照。远端Local终态由既有relay回收后在控制侧打包，Hosted/控制侧本地由已有observer保存后打包，源保存与包生成错误分别保留。这些自动化及Hosted实时路径为代码接线结论，未新增真实运行证明。

采用实际I14归档时发现初版漏掉scope/work中的浏览器、npm/pnpm环境，1.3GB包仍含Chromium；原owner修复实际目录后一次最终重打为884846301bytes、82.943秒，公共缓存成员为零，大头仍是Braid工作树中的应用依赖，未按依赖名盲删。旧错误包保留证据。随后修复包内最终回执、终态同来源复用以及Pi容器pi-home链接相对化；最终schema2在真实Pi入口通过，约98MB、8529成员（含目录）、gaps/errors均为空，第二次正常获取约0.05秒返回同一包。最终Pi路径为runs/lab/runs/a3a9a5262b8b40f382883ed636758464/snapshots/portable-1791393951451055000.zip。I14缓存剔除包路径为对应run snapshots/portable-1791393628510537000.zip，其回执仍为早期版本，最后两项元数据修复后未重压大包，不宣称已是最终schema2产物。两run仍stopped，consistent=false，不冒充完成或检查点。所有操作未启动模型、评测或参赛，原owner已返回，主承担剩余资格边界与提交。

用户确认“整理完成”，继续既有实现授权内的设施收口，不恢复两条已停止验收运行，不新增收费生成或评测，App续办保持暂停。整理后的入口为 materials、tooling/scripts、tooling/linux、consoles/lab 与 consoles/braid；其它未提交改动保留，不整目录暂存。

主负责采集事实与策略消费边界；evaluation_closure已续派，负责默认保存、评测及stages接线的必要修复，拥有automation.py、local_run.py与评测相关实现。该负责人不暂存或提交，由主采用具体改动后统一提交。advisor上轮只给下一步建议，本轮未派执行。Console后续沿用原负责人，当前未唤醒。

正常CLI只读确认Pi a3a9a526和I14 ed426均stopped/inactive，远端与Mac现场回收事实仍saved:true/errors:[]。冻结manifest中的历史harness路径保留，不能因整理而改写历史程序身份。

本次定位到采集故障的明确源码缺陷：公共observe异常时覆盖status，丢掉旧spend/native/resources；Hosted工作区下载失败时覆盖workspace-latest，丢掉旧用量与资源。修复保留旧事实及原时间，另记录本次采集失败时间与具体错误，不刷新旧数据、不中断策略或新增采集者。Hosted修复已完成源码解析，未在现代Hosted真实故障中验证；公共观察修复由上述原owner落实。后续仍优先采集—策略—控制，再默认保存/评测/stages及保存后分析，不能把源码修复当整体验收完成。

采集修复已采用并提交44297d55。正常watch只读消费两条终态现场，能取得旧usage、resources和last_activity_at并退出，未刷新as_of；这不证明故障分支真实触发。Hosted gateway和资源同样限定当前scope/producer，错误历史只写失败元数据，不反复复制旧native事实。

evaluation_closure完成新正常入口代码路径核对，并将远端来源的simulate/official同task/self-test统一延后至Mac controller派发，复用EVALUATION_KINDS。requirements/tests在装配时冻结、同一relay回收后派发，stages从当前维护task计划自动启动；旧run的finish-evaluation.py和补充阶段脚本不再作为新run必要步骤。以上是接线结论，未进行新的四后端或stages真实执行，不恢复旧run。

console_acceptance完成只读实际使用：CLI brief每条约0.05秒，首页约4.5秒；两run stopped、saved且无评分可见。发现日志只展示末尾65KB却未注明范围、原生state active易被当执行状态、没有workspace浏览入口。主已修截尾提示、原生state说明、直接展示保存宿主的workspace与完整日志原件路径；正常Lab前端构建成功，静态文件已部署到既有sfp7服务，未重载后台、运行或collector。原生Braid仍缺协作快照，文件浏览/下载仍缺项，页面明确说明；原owner正做上述窄UI读回，不将路径提示冒充文件浏览功能。

上述三项窄UI实际读回通过，改动提交afc01a6b。随后采用advisor仅基于给定事实的建议，补成功保存后的有界workspace文件清单，沿已有record_summaries发布，不运输内容或增加Backend跨宿主文件服务。真实Pi现场78个文件、I14现场16个文件，无截断/读取错误；经正常run.publish写入既有服务，HTTP详情实际取得同样数量，原保存时间保留。新静态页已再次构建部署，未重载服务；内容预览/下载仍未提供，清单和真实保存位置只证明定位能力。原owner继续窄UI读回。

文件清单实际UI读回已采用：Pi78/I14 16项，路径/bytes/symlink、排除目录和原保存时点可见。首次复查指出未截断时没有上限说明，已补并构建部署index-DyIYCLnf.js，末次I14读回明确“最多列出500个文件；本次未截断”。文件定位交付795c973d，内容读取下载和Braid完整视图仍未实现或资格化。evaluation_closure及console_acceptance本轮均已返回，不声称仍在运行；主保留全部残余义务。没有重启生成、派发评测或恢复App续办；源与静态部署、已有事实读回、故障分支及四后端真实闭环的未验收边界分别保留。

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
| evaluation_closure（执行者） | Pi评测材料冻结b514103f、控制端deferred task/self-test派发700ea0d0；两DX窄路径observer已实际部署 | 已续派并执行；核对实际自动收尾进程、保存重试及生成为何未终态，负责明确设施故障的修复和实际消费。最终评分未形成，主仍持有整体义务 |
| competition_cost_decision（advisor） | 短控制锁等建议已采用；本轮只基于主提供的价格/用量证据建议partial已知小计及ARC适配归属 | completed；未调用取证或实施，主决定并实现；此前角色越界不沿用 |
| process_reaping_decision（advisor） | 标准Tini/subreaper、保留Popen退出状态所有权、不设全局并发gate建议已采用 | completed，不负责资源实现或验收 |
| acceptance_conversation_decision（误用advisor） | 历史会话取证及评价文档修改已采用b84d6d52 | assignment已结束，不在live tree；保留证据不重做，调查/编辑不再交advisor，该低优先级项不扩展 |
| cold_local_profile、cold_console_profile、cold_hosted_profile、evaluation_implementation等历史执行者 | 历史控制/回收、Console、平台拒绝、自测认证/评测接线，材料已保留 | 不在live tree，不声称持续工作；后续已由主接管，评测残余义务归主，不挂在不可达owner名下 |
| 早期profiling、文档预演及完成标准advisor | 标准、设计取舍及只读反馈已融入design/evaluation/assessment | 已结束，不是实现或最终验收负责人，历史见整理前记录 |

用户2026-10-07明确纠正：“advisor 是给建议的，怎么会变成执行者？而且也不应该让 advisor 去收集证据啊”。当前分工：执行者收集证据，完成调查/修复/操作/验证；主把目标、约束、证据及一个待决问题交advisor，仅请建议，主决定，执行者落实。advisor不当reviewer、调查者、文档作者或监控执行者。已有材料不因纠正分工重复调查。

## 当前推进顺序及剩余责任

用户在I15两项改进交付后要求“那继续验收吧？”：继续现有两DX自费、非参赛闭环，不据此新开I15比赛运行。evaluation_closure已续派负责两run自动保存/评分、必要修复与实际部署，主不重复其调查；新browser_operator console_acceptance负责真实Console只读使用、寻找负担和界面反馈，不控制运行/不读实现代替使用。主负责采集/策略剩余资格边界与采用结果。普通CLI最新读回21:18：两run仍running/active，没有result-save回执；I14811attempts/745returned usage，Pi约17.19M原生token，不是供应商账单。任务包、协作、verification技能用于恢复责任及区分部署/实际效果；等待使用既有后台机制，不频繁读GPT心跳，不为填矩阵重复收费生成。

该UI验收发现并闭合Console发布HTTP413：正常快照超过注册独立512KiB限制，导致I14停21:07旧状态。主采用advisor仅给定证据的gzip/既有消息配置建议，部署至Console1285376；对真实快照777370字节→77612字节，正常发布0.073秒，独立UI确认21:26新状态与821attempts，不裁剪原件。另改task/target定位、attempt计数、按展开生成raw DOM及时间时区说明，已构建部署，待末次UI读回。过程与旧错误归runtime-diagnosis及validation/console-live-observation-20261007-2121.md。两run仍未终态/评分；I14原生观察间歇30秒超时并遇实际内存边界，已续派原owner处理，不用提高timeout或停止生成来补验收。

最终UI读回已采用：21:32选择器task/target/短ID明确，I14显示847attempts/781returned usage，原件展开/收起正常、GMT+8明确；Pi仍active/130原生消息。Console修复提交2965ccc3；console_acceptance assignment completed。原生超时与两run完整闭环仍归evaluation_closure，尚待其具体修复/当前自动化进程证据，不将本轮界面通过转为整个设施通过。

用户最新要求继续追查本地正式Pi-vv的project.zip，并把自验用例相互影响纳入打包设施改进。主负责用例数据边界，evaluation_closure负责冻结服务能力取证及pbb停止入口必要修复，process_reaping_decision仅依据提供证据给取舍建议。证据和决定归runtime-diagnosis-20261007.md；只读采用已有正式run材料，不控制它、不注入反馈、不改其应用。主已补公共e2e技能的case与journey隔离说明，复用现有fixture，不新增通用数据库reset。源码打包只影响未来程序，不宣称在途已修。两条DX生成—保存—评分闭环及持续采集/策略qualification仍未完成，不因该局部修复收尾总任务。

自验技能提交97b86d10。服务负责人已交回冻结包能力证据和pbb kill全局job ID修复；主修正patch编辑意外、确认可解析并只采用当前hunks。语法检查不等于实际停止资格化，无正式run或进程受到控制。该局部assignment已结束，整个实验闭环未完成，后续两run保存/评分仍沿用现有自动化，不用这一归因调查替代主要目标。

用户随后明确“要至少让I15收到”，并补充“e2e skill的改进也是”。主补I15 builder的PBB CLI成员，保留其专属业务状态转换reference并加入同一用例隔离说明。新交付为`runs/iteration15/materials/pbb-e2e-isolation-20261007/overlay.tar`，22,159,360字节，SHA452e3b77772a4b0453b8d494a43d2c6cd9a25e17066906ffd1a4d52385b34e1c；package-identity.json实际绑定PBB SHA30b4bc886fa8853435924d9f4f377723f807a0545e2071ecf4d081cdb6bd0585、e2e SHAca917d57f0a76c3b744cb418cd49919b685c097645039ea0fdb7f9b620ae0890。复制原同版protocol的明确成员到独立protocol-inputs，仅修改PBB并注明不是完整runtime；旧输入、底包、Braid和旧overlay保留。node语法检查通过，真实归档读回和launcher消费路径已核对，不是包smoke/停止实际验收。没有模型、评测、参赛或在途控制。I15当前运行未收到热更新；新交付已具备两改进。I15已有未提交的技能/reference及builder接线属于原owner工作，保留不整目录提交。

用户随后确认“不记住失败是正常的”，要求先修其它问题。当前不改变千帆等待期限、fallback跨请求记忆或在途配方。主修submission/runtime_install.py的公共短socket目录（按原目录hash隔离，Linux临时socket与Mac WorkSSD分别落位），修浏览器技能示例为每条命令显式session；未来程序消费，未热改在途冻结材料。用现有Pi容器、独立诊断session实际打开现有首页、读取交互元素并close，原超长名称task-8945cd75636e在短目录下正常，无需代修应用；原生Agent已自行修好白屏。第一次诊断命令的shell引用错误未启动浏览器，保留工具回执，不记作产品失败。

Console原owner续派被thread limit拒绝，主明确接管。查明reader文件18:06更新，而服务PID1318330从18:02运行；静态页hash也落后。主更新Braid静态页并只重载Console至PID3951941（20:19:46），静态页hash已与源码dca6014b一致，reader文件hashc13cfae8一致。生成容器与observer未重启。API旧投影仍为空/partial，需要新worker回执进一步判别；不能把部署完成当动态视图通过。evaluation_closure已续派负责两run实际保存/自动评测，尚待返回，不暂存/提交；主统一处理Git index。

重载后Console worker推进至batch2790、as_of1791375647.318，回执status=unavailable，明确旧Summary没有collaboration snapshot，以及native inventory/path缺项；新reader真实消费已生效，动态协作内容仍未资格化。主另修公共browser wrapper，使skills/session元数据命令直接调用上游，不先下载安装Chromium；该修复针对19:32读取core文档触发177MiB下载的真实损耗，后续包装消费，不改在途冻结文件。evaluation_closure已返回I14包外automation/local_run部署，旧default984993→3949199，observer968810与生成不动；回执records/evaluation-automation-repair.json，旧源亦保留。当前I14冻结task_config无evaluations，故这里是派发版本统一，不声称task分支已造成本次失败；最终评分仍由Mac finish-evaluation脚本等待。当前两run尚无最终评分。

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

本轮继续验收采用 evaluation_closure 的原生观察修复：限定约定日志路径，避免扫描整个生成工作区。I14 在原进程不重启的情况下已实际消费，三次真实采集 211/213/208 ms，reader_errors 为空；部署与原文件保留见该 run 的 records/native-observer-repair.json。该 owner 继续负责两条既有自费运行的终态保存和自动评测，先核对 default、Mac relay 与 finish-evaluation 的实际执行者，不能用旧 PID 或 waiting 文件代替健康证据。当前没有结果保存或评分，整体验收仍未完成；不新开生成、不参赛、不代改应用。

后续真实执行者核对：Pi default2525159、I14 default3949199、Mac Pi relay97137、I14 relay74665均在执行。Pi也热部署窄扫描，三次真实入口2706–2867 ms，不套用I14耗时。I14评分等待脚本首次修补saved:false立即退出，主因现有保存者仍会重试而未采用此语义，已要求原owner保留重试、暴露具体失败，并在保存执行者确实lost时明确报错；不能为了消除等待而永久跳过评分。修补进程身份也需同步正常记录，不只另留新PID。两run仍无终态/评分，owner正在有界诊断原生语义进展，而非继续读心跳。

最终评分等待修复已采用：先读取明确saved:true，仅仍需等待时检查Mac relay出生身份，不拿远端supervisor在Mac判断lost；失败回执保留具体内容并继续等待所属保存者重试，明确lost则非零错误退出。当前PID22765，主通过正常process_state读回alive；代码与旧版本、回执均在ed426的records。没有通过制造保存失败验收该分支。原生末尾的有界取证表明Pi request139进行中、前请求千帆500空体约130秒后ARK成功，I14有工具活动及request876成功并保存usage；不将这些事实扩大为应用质量或完成证明。

主发现原定stage1→stage2推进未接到当前ed426（无stage_plan，旧脚本已随历史失败退出），已使用现有lab.automation.stages显式传入github-stage-2接回；Mac PID22971、出生身份见records/stages.json，stages-progress.json为waiting，主读回alive。仅ed426正常completed后同variant restart，保留data、自费/competition=false，下一任务独立native身份；不启动额外fresh矩阵、不重复评分发起者。原生生成、保存和评测仍由既有后台执行者持有，终态未形成。

用户再次要求继续，主已为当前任务设置App线程续办“实验设施验收闭环”（automationId=automation，每10分钟）。它只消费既有事实、采用结果及修复明确设施故障，不是第二采集者，也不替代运行内Python策略；状态不变保持安静，实质进展/完成/失败/用户决策才通知。不新开矩阵、不参赛、不代改应用、不重复派发，闭环完成后暂停续办。这样无需用户反复催办即可收取既有后台执行结果。

- Python策略：a439ae26、f3c41f36；Hosted事实消费：d92b074c；周期采集/控制：80794c7a。
- Console/Braid：17d6da0b、dbcae9e2、f80f3546；新Summary编译材料：`runs/finals-experiment-loop/validation/cooperation-summary-*`，未动态资格化。
- 源对齐：b19dc7b0；`runs/finals-experiment-loop/validation/i14-source-aligned-build-*20261007*`。
- Hosted真实旧self-funded ZIP：`runs/finals-experiment-loop/validation/hosted-workspace-observation-20261007.json`，423条assistant usage、2session，重复读changed=false；旧包无现代gateway/resource，不宣称现代导出/并发取消通过。
- 受辅导验收纠偏：b84d6d52；所有原失败和旧现场保留，不覆盖为成功。
