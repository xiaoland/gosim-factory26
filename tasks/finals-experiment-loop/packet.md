# 决赛实验基础设施重设计

2026-10-07 用户调整当前优先级：为今晚 I15 参赛准备持续监控、自动策略和运行中费用采集，避免结束后才看到比赛额度扣减。现有两条自费验收继续自然完成，不增加比赛验收或模型矩阵。非阻塞 Braid 视图改进收住，只保留已定位合同修复及编译输入；当前先将已有 Hosted 工作区快照采集接入新 run observer，按5–10分钟读取原生用量，排除运行环境，向 Python 策略提供带来源与时间的事实。平台终态账单和运行中估算分开，未核实 ARC 计价前不套原厂价、不把未知当零。

Python策略接线已提交 a439ae26、f3c41f36：watch直接读取保存事实，重复快照保留as_of；自定义策略不替代自动评测，远端策略复用stages的源码交付范围以支持start/restart。实际读取ed426的running/active及spend/native/resources成功，读取756失败终态后watch正常退出；没有操作在途run。Hosted采集owner正在用真实历史ZIP验证累计用量及现有reader复用，尚无金额/自动取消实际证明。Braid轻量Summary生产补丁Linux release完成6分07秒，ELF e332a98805121799f780cfc3fc652519e77f448a3b9238dcdfc451c76dc0113f，材料与日志在validation/cooperation-summary-*；当前在途run未更换程序，新生产版本尚未部署或取得动态视图证明，不让这一缺项堵主线。用户另要求复核验收会话的真实对话方式，并明确低优先级交sub-agent；acceptance_conversation_decision读取真实Factory26会话并持有evaluation/assessment的证据归类，不派新运行。

execution_owner 持有 hosted_run 及必要解析模块的采集/修复/实际反馈，主 Agent 持有策略与执行生命周期接线，competition_cost_decision advisor 判断比赛统计代理和计价前提。当前 Rust proxy 会改写模型预算与 fallback，不直接放进比赛包；透明统计层是否加入由该判断收敛。本任务仍不创建、启动或停止正式比赛运行。主曾误问用户剩余额度/停止线，用户明确纠正：本任务交付采集变量及普通 Python 自由判断/操作能力，不是替 I15 制定预算策略；撤回该前置，不建立默认阈值或预算门控。另已修复 start --script 覆盖默认自动评测的问题：自定义策略与任务自动评测分别启动，不再二选一；该修正尚待真实消费，不宣称完整自动策略通过。

最新目标核对归[assessment达成表](assessment.md#2026-10-07-原定目标达成核对)：整体未达成，已完成的架构与局部运行能力不能代替完整使用链。采用advisor的收敛顺序：收取Node/npm实际应用验证并继续当前Pi/I14；并行修Console已发现的active事实缺失；产物形成后完成原定自动评测、同variant接续/stages及采集策略证据；最后汇总正常操作的时间/token/排错成本。不扩variants/模型矩阵，不制造资源触顶或idle条件，不因分数低追加优化。Hosted关闭与绝不参赛是外部未覆盖边界，self-test评分和内部费用/Console缺口仍须完成。

I14恢复责任已由execution_owner明确交回主Agent，无在途构建或收费操作。主直接读取实际Linux编译输入，发现 `braid-rebuild-unknown-timeout-20261007/src/src/store/mod.rs` 仍只JOIN `wt.lifecycle='active'`，而746/756保存的worktree为blocked；本地已提交的修正接受active/blocked，却未同步进远端编译输入。远端还保留宽泛error.contains("timed out")，与本地精确get_state条件不同。因此撤回“实际SQL条件满足但helper原因未知”的诊断：交付ELF哈希一致只证明交付了那个二进制，不证明它包含当前源码修正。主已同步当前Braid src，并复用原Cargo volume执行release编译，日志为远端 `source-aligned-build.log`；不增加恢复条件、诊断框架或设施测试。编译与正常接续的实际结果仍待取得。

该release实际完成用时2分02秒，ELF SHA `fbcd2c03148c6f96bfa4d3eaf777c74450592cf66393e2fe19e75ee4e7eee88e`；编译输入store哈希与Mac一致，Cargo.toml/Cargo.lock亦一致。新不可变材料为 `runs/runtime-i14-offline-materialization-source-aligned-20261007`，两个DX维护入口已切换，旧在途Pi不动；正常启动拥有新远端发布及回执。编译日志与实际源码归档保存在 `runs/finals-experiment-loop/validation/i14-source-aligned-build-*20261007*`。独立会话已收到自然请求，从756保存现场正常接续并观察真实活动，不把编译完成等同恢复成功。

独立正常接续产生 `ed426cf521bd4f46ba58629f4acbd3e3`，来源756、同native scope782227、self-funded/competition=false，实际program包含上述fbcd Braid及fd0869 proxy。已running/active，恢复后新Pi原生session为01a115c7-c485-7652-b14a-26b941be3559，blocked_groups=0。当前provider usage已真实采到千帆及ARK完整返回的token/cache/reasoning等字段，13条recorded时reader_errors=[]；按真实attempt归属，未返回usage的429不当零，金额仍未知。主在实际Console页面看到了这些事实。Braid入口原按variant名称猜测而漏I14，已改读native.braid.available；随后发现共享服务未装protobuf依赖，原HTTP400保存具体No module named opentelemetry。主复用已有纯Python otlp-deps部署后已开始接收batch；一次初建并发PRAGMA WAL报database is locked，及完整Braid投影尚未取证，继续闭环，不以空iframe算通过。

采用advisor的SQLite修复：初始化锁与成功路径集合，每个稳定run数据库成功初始化一次，仅非WAL时切换；不串行所有读写、不建连接池或重试队列。SQLite持久化错误返回具体503而非断开连接。语法检查与共享服务重部署完成，实际后续batch由4推进到6，旧失败批次是否重送仍未知，不宣称零丢失。进一步发现语义合同缺口：Braid周期Summary只发库存，不发object/session，而viewer强制Portable reconstruct，继续等待不会产生动态协作视图。采用advisor决定：Braid周期Summary只发送当前对象/会话的必要关系、状态与时间，避免反复读native全文；Braid viewer直接解释Summary，正文/完整历史留到终态保存后Portable导入。主负责该生产/消费修复，当前生成不为此重启，后续正常stage消费新生产版本；当前空视图明确未通过。

费用专项采用advisor判断：spend为run新增货币支出，预付购买成本不均摊、原生token不冒充套餐credits或账单。主负责公共proxy返回usage采集、当前producer按request/attempt/deployment投影以及CLI/Console/Python事实；不建账户系统、不强制切按量供应商取得样本。新proxy支持SSE跨chunk/多行data和非流式JSON的usage观察，1MiB软捕获边界只报告缺项、不改变转发或阻止运行；Linux release编译完成，新ELF SHA `fd08694b8f9ce7de568bdb94dccfbdd9d7ca4626f65924e579a16abb142a9244`，默认装配已切换，旧a3冻结版本不热改。公共reader实际读取已保存d3日志得到50次attempt、三条实际deployment、0条returned_usage（旧代理未采集），无读取错误；不得反推历史provider usage。新增代理capture仍待下一次正常真实请求验证，不新增模拟设施测试或收费矩阵。来源源码仍有其它未提交材料，不整目录提交。

I14第二次修复根因是旧物理Pi尝试为unknown/get_state180s超时，而重试条件仅接failed。execution_owner已修改该条件、cargo check及Linux release完成，Braid SHA `c4662bb9d883505eceb8fe9ef44a7b1619c03c003ead7462608a4c14bc2ad609`，源码hash `1632d5a38e59100133fd5101ccd8bb75981a89463b5f6c11729887e65668b635`，目标使用 `runs/runtime-i14-offline-materialization-retry-20261007b` 及新远端发布目录。独立会话获准从746835正常接续一次，尚待真实部署/模型活动；owner继续局部修复并仅提交所属hunk，不带格式化或其它dirty。

该正常接续实际为 `7561359db2a943979d22153f1633da04`，17:30:11仍failed/blocked，无provider turn、无模型请求，Mac完整saved=true/errors=[]。第二次条件修复不足以解除blocked，不能将正确失败投影视为恢复成功；execution_owner继续核对实际发布字节及agent/physical关联，不原样重试、不自行派收费run。Pi a3截至17:31:14仍running/active、本run partial native tokens491,138，已连续完成多个真实模型请求；尚无完整应用或评分。独立会话继续正常wait与自动评测闭环。

756的实际argv包含offline-resume、receipt存在，消费Braid c4662bb9，约0.33秒blocked；这些事实排除未调用或未消费版本。owner称“SQL条件满足却无replay”的判断仍须区分源冻结状态与756失败后状态。advisor确定恢复入口位置合理：Lab只迁data，I14调用唯一offline入口，Braid在provider/scheduler前prepare；不把SQL搬Lab、不继续放宽unknown。下一步由原owner对齐argv→request.state的DB/native identity→来源746冻结状态→prepare receipt→本次blocked写入；若缺调用前原件，在现有回执补处理前状态与结果，不建框架。只对已证明停get_state、尚未交付输入恢复原input/dedupe；no native identity本身不证明输入未交付。修复hunk与两DX target已由owner提交f22bf6c0，其他格式化/dirty保留，未push。

2026-10-07 proxy专项纠偏：completion_criteria_decision advisor定位Cargo.lock锁定reqwest0.13.5，其Linux异步Client默认tcp_user_timeout为30秒；主已读官方版本源码确认。公共Client现在显式tcp_user_timeout(None)，请求总期限仍有效，不改配方、重试或fallback。此前“源码无30秒配置”不能推导实际socket无30秒期限。相近9.28MB请求33已HTTP200完成，35按既有链在千帆500后由ARK成功，不能用固定体积上限解释。Linux复用编译缓存22.33秒完成，新ELF SHA256 `6f1e07fc10a50149e2be513450177b88d53f5c9d4323d0dcaaefea48f0c7979d`，交付为 `runs/provider-model-config-20261007/delivery/model-proxy-linux-x86_64-tcp-deadline-20261007/factory26-model-proxy-linux-x86_64`，公共默认装配已切换。独立会话获准从d3cc现场正常接续一次；尚未证明实际上传恢复。若仍30秒失败先核对交付字节/socket，若到总期限仍无ACK则保留这一次证据再定位出口/对端，不继续延长期限或同条件重跑。proxy源码目录已有其它未提交来源，未整目录纳入本任务commit。

独立验收已实际从Console首页进入Pi详情，确认failed/inactive、来源/配方/competition=false、最新502、资源终态与非峰值采样、partial用量及费用未知均可见。其两项新增负担已修：未提供experiment标签时不展示“实验名未知·未保存”，归档统计改为“已归档”，生命周期不再称作保存回执。Console TypeScript/Vite构建及Linux部署完成，后续新run负责动态刷新反馈。

新Pi正常接续为 `a3a9a5262b8b40f382883ed636758464`，来源d3cc、native_resume=true、self-funded、competition=false；装配proxy SHA与上述6f1e07一致。启动安装期间CLI将迁移历史的502误当当前activity=error，根因是Pi status.py未区分新run时间边界。已复用native usage.since过滤当前活动消息，历史原件仍供Console查看；在该真实run保存facts上执行新版解释器返回unknown/session message unavailable，符合尚无当前消息，不新增设施测试。当前冻结program不热改；源码修复由后续正常启动消费，当前请求产生新消息后原解释器也会更新。这不是新proxy已失败的证据。

a3 request1实际请求体9,299,978字节，31.7秒时连接仍ESTAB，bytes_acked6,955,255、notsent2,361,921、rwnd_limited99.9%；只读原件为该run records/upload-socket-observation-20261007.txt。随后按既有配方fallback到ARK，第2attempt 11,459ms取得HTTP200及first_body_bytes；不改供应商配方。这证明该请求不再30秒被切断且已恢复模型响应，不证明千帆接收端背压根因解决、stream完整结束或应用完成。主在同一打开的Console详情无任何刷新动作，实际看到as_of从17:14:31变到17:17:28、activity从继承error变为active、新session activity及当前producer日志/资源出现；独立会话继续终态及自动评测。整体仍未完成。

2026-10-07 用户明确“你可以开始，这也是基础设施改进的一部分”，批准将[应用开发与评测环境统一](../harness-app-environment/packet.md)纳入本任务。公共默认应用Node/npm与工具解释器分离，范围为两个DX及实际评测入口；不扩展历史variant/I15，不热改在途。execution_owner持有公共安装与Linux应用操作，主持有DX入口/指令与技术说明。该packet拥有具体环境证据和完成标准，本入口不复制；费用仍自费、绝不参赛。

最新验收：Pi正常同任务接续 `d3cc30d25f8e4da5be4b467f709f2250` 已于16:55:32自然失败，退出1。已消费响应头/总期限600秒，在sfp7取得真实模型回合，最后三次9,291,245字节请求仍在约30–32秒报 `SendRequest: connection error: Connection timed out (os error 110)`，没有响应头；不能再归为WSL独有或旧90秒期限。Mac结果回收已明确saved=true、errors=[]，partial原生用量1,444,211 tokens，实际spend未采集，不能当零。来源为1c1e1b，native scope仍为f1335fc，同variant/data/原生状态。I14普通接续 `746835582f574a7fa7b25856b8e24b5b` 也failed且完整保存，仍报告必要group物化/恢复blocked；execution_owner继续核实发布版本和恢复条件，独立会话不再重复同条件派发。完整生成和应用评分均未完成。

用户认可推进重心纠偏并明确“请继续推进吧”。应用环境已经取得真实Linux资格化结果，详见所属packet；这不解除上述生成阻塞。Console实际页面能显示Pi终态、资源、原生错误、日志与partial用量，费用未知明确保留；主发现通用详情未轮询、刷新按钮只刷新旧Braid查询、Pi首页入口被禁用以及Native面板选到较旧subagent，已修复并部署。真实首页已可打开Pi详情。这属于主的实际操作反馈，不冒充独立验收；早先独立会话报告API事实缺失的根因尚未由这项前端修复证明。继续完成生成、控制/接续/stages、自动保存/评测和分析链，不扩大模型矩阵或性能项目，全部自费、绝不参赛。

公共源传输已定位到观察程序每次spawn无条件复制完整variants/harness/arc-bench（约246MB，其中arc-bench约236.7MB）。修正为普通观察/评测只复制lab/scripts，原生stages再携带构建来源；仅开发源码排除.git、node_modules和测试报告，program/inputs/data默认完整复制不变。这是待正常启动验证的源码改动，约2MB静态来源体积不能直接当成实际启动提速证据；不为profiling重启活跃Pi。

当前推进：用户确认WSL腾出空间并授权继续完整验收；只读df确认 `/home/yyh/factory26-lab-runs` 所在盘约13GB可用、inode使用34%。主按原定design/evaluation重新核对，结论与缺口表归assessment首节，整体尚未达成。新Pi运行 `ad9a7d1acefa49e5bf8326b18beecf6b` 已实际生成部分应用，但代理前8次HTTP200后连续4次传输超时，容器自行退出1，不能记为有效零分或完整验收；现场自动回收 saved=true、synced=true。同一独立会话已获续行指示，继续同任务接续和Console真实使用。全部验收仍自费、不参赛，不清理WSL数据。

本轮修复：远端观察程序在第二次spawn重写manifest时读到空文件并退出，导致CLI/Console停留在starting/unknown；`_push_remote_manifest` 已改为同目录临时文件写完后rename。原观察日志保留，主仅重启所属观察程序，没有停止模型或创建重复relay；恢复后具体502错误、失败终态和自动保存均可见。下一次正常start/restart负责验证双spawn路径。新错误原件在该run的gateway.log：请求体由约69KB增长至3,699,935字节，后4次均约30秒出现 `SendRequest: connection error: Connection timed out (os error 110)`；尚不能仅凭这些事实判定供应商、网络或代理责任，主继续定向诊断，不增加无依据重试或隐式换模型。

自费用量已复用native采集接入status、CLI和Console：只汇总本run创建后已保存的assistant usage，按session/provider/model保留tokens和来源，coverage明确partial，不采用native占位cost=0。对已保存ad9现场的定向读取取得158,167 totalTokens，但这不是账单或新run已消费改动的证明；实际金额仍未知。Console前端编译并部署成功，实际HTTP首页引用新资源。execution_owner继续I14新782227的完整wrapper冷启动/get_state超时；resource-deferred是最新批准的Braid资源修复，不能凭目录名降级回p。advisor完成标准已采用；新增/续派费用owner受agent thread limit拒绝，该责任暂由主承担。

后续新Pi run `f1335fc0c4d9446e90a6f6a99faaf687` 是全新start，source_run=null，不冒充restart。正常双spawn后状态进入running，原生消息与spend.usage均实际可读，CLI已显示partial token汇总，证明原子manifest与用量接入被正常消费。随后3,709,375字节 request 9 失败；该请求没有收到HTTP响应头，主附着其真实socket读取元数据，bytes_acked在2,486,323停住，Send-Q为1,230,511、notsent718879、unacked374并持续重传。这将问题收敛到上传未完成，不是上传完成后等待模型回复；此前较小请求的HTTP 200与sfp7对照请求的HTTP 200/complete不能归给request 9，还不能据此归责供应商。原件片段在 `runs/finals-experiment-loop/validation/pi-f1335fc-upload-stall-20261007.txt`。同一独立会话在其自然终态保存后，使用正常restart把同task/data迁移到sfp7、保持配方，以取得跨宿主接续与实际网络消费对照；不额外重放未知受理请求、不循环同条件启动。Console还修正Docker stats已保存但UI字段不匹配导致未知的展示，编译部署已完成，真实查询仍归独立会话。

2026-10-07 WSL 上传停顿的只读归因：失败连接位于容器 `172.30.0.3` → `14.215.183.202:443`，request 9 没有收到HTTP响应头，发送约3,006,162 bytes后长期停在 `bytes_acked=2,486,323`，`Send-Q=1,230,511`、`notsent=718,879`、`unacked=374`，TCP进入拥塞窗口1并持续重传，最终30秒 `SendRequest ETIMEDOUT`。WSL 宿主当前 `eth0 mtu=1408`、Docker bridge `mtu=1500`，Docker bridge为普通MASQUERADE（172.30.0.0/24→WSL eth0）；这解释了环境差异的候选路径，但不能单凭MTU判错。对照是同一 peer、同variant/task/data 在 sfp7 的3,717,996及4,218,601字节请求均HTTP 200且complete，因此请求体大小、供应商端点和应用配方不是充分解释。当前最可能归因仍是WSL2/Windows NAT出口在该连接上的路径级丢包/黑洞这一待证假设，不是已确定根因；尚未有Windows NAT内部状态或宿主抓包证据，不能进一步归责Windows主机或供应商，也不支持修改MTU。新增只读宿主观测：WSL `eth0` 累计 RX/TX errors/drops 均为0，Docker bridge errors为0、TX drops为246；当前路由为 `172.29.144.0/20 → eth0` 默认网关 `172.29.144.1`，Docker为 `172.30.0.0/24`。这些读数没有证明宿主接口物理丢包。没有新增收费对照、没有打断sfp7运行；后续仅消费现有运行/正常restart路径已产生的socket、路由、接口和容器网络证据，任何全局Windows/WSL网络变更先单独报主具体范围。

当前修复提交 `1c55aadc`，仅纳入原子manifest、本run原生用量与CLI/Console展示及对应操作说明；core ulimit及其它工作区改动未纳入。I14 owner在同镜像、当前resource-deferred完整wrapper下取得无模型RPC get_state成功：首次组合managed/timing约91秒，后续约3.5秒。采用advisor判断，暂不新增部署专属预热、预编译系统或加握手超时；先由独立会话正常restart完成真实生成，若准备过程再次可重复导致失败再修同一安装/原生启动生命周期。原件归782227的diagnostic-full-wrapper-20261007.tar，原失败现场不改写。一次成功启动不证明冷启动缺陷根治或完整I14通过。

Pi正常restart的新run为 `1c1e1b407fb3498b83260e4c58c4c149`，source_run=f1335fc、native_resume=true、native_scope_id保持f1335fc、target=sfp7、competition=false。同一peer的大请求已成功，随后出现一次独立的504 upstream_headers_timeout，原生重试后又有4.56MB请求HTTP200/complete；不把旧502、这次504和后续成功混成同一个结果。仍待应用终态与独立评测。Linux代理默认路径修复提交 `3478bae6`；未确认归属的未跟踪proxy源码不整目录纳入。

资源采样消费修复提交 `584179c7`：复用公共ResourceSupervisor的 `resource-observation.json`，按当前scope/run producer读取，接入status.resource/resources.supervisor和Console；写入改为相邻临时文件fsync后rename，避免新读者读到截断采样。对f133已保存现场取得内存945,020,928 bytes、pids22及2GiB上限，状态与Console发布成功；这是该采样时点，不是历史峰值。前端已编译部署；在途Pi不为展示更新重启，后续正常run消费新观察接线。独立会话负责实际可理解性验收，不用源码或HTTP首页代替UI结果。

后续采用advisor的明确决策修公共proxy默认响应头期限：sfp7请求完整上传后被90秒内部期限主动截断，原生重试又可成功；execution_owner将prepare.py默认headers_ms改为600000，与既有单请求total同值。Rust仍从已有deadline起算，不重置请求时钟；connect/body/stream_idle不变，没有新供应商配置、重放或换模型。源码语法检查完成，binary不重编；adapter处于未跟踪共享源码，不整目录提交。独立会话在当前provider回执后正常stop/save/restart，以冻结程序和实际config核对新默认、取得90–600秒迟到响应是否带来收益的证据；源码修改本身不是收益证明。

Console配方/来源/保存位置修复提交 `ffddd4ab`：publish原先遗漏model_recipe/model_routes，这两个已有事实现已供概览消费，原生/费用事实不重新采集；前端直接显示目标、任务、参赛身份与来源run，保存回执可展开。实际f133 API返回配方、5条路由和saved=true，前端编译部署成功；UI可理解性仍由独立会话自然操作核对。当前验收顺序允许Pi交付后并行重试I14，分别记录共享负载，不将并行样本称孤立冷启动基准。

2026-10-07 侧会话用户询问原生 stages 题目支持，在获知仅有 Python helper 后明确“好，请你推进”。已补充 task 配置的扁平 `stages` 列表，以及 `lab start` 自动选择第一阶段、在控制宿主启动普通阶段推进程序的接线；维护任务 `github-stages` 指向既有 Stage1/2。程序复用 run.wait/restart，只在 completed 后迁移同 variant 数据；初始 manifest 保存声明，stages-progress 原件记录实际派发与具体失败。各阶段的采集、保存和默认评测保持原职责，没有新增控制对象、队列或阶段 gate。修改范围为 lab/run.py、lab/automation.py、targets 中新增任务，以及既有 Lab/design 说明；Python 语法解析、targets JSON 解析与实际 automation 命令帮助成功。侧会话没有启动收费运行、修改主会话在途验收或提交 Git；完整真实 Stage1→Stage2 验收仍未通过，不能把源码接线视为完成证明。主会话后续验收可以改为直接选择 github-stages，而非手写 stages 脚本。

2026-10-07 model-proxy 启动缺陷已修复并取得实际 Linux 请求证据。loader 改为 alias 内 deployment 唯一；不同 alias 可以复用真实供应商身份。sfp7 release 编译45.74秒，新 ELF 的SHA256为 `9b19fc6ea9396799ae998b1539d9780f872cba4746c590625a088eb502b14776`；公共装配默认引用已切换，装配出的代理与该字节一致。`deepseek-v4-flash-0731` 和 `deepseek-v4-flash` 均由同一千帆 Token Plan deployment 返回HTTP200，并记录body_end及terminal complete，代理随后受控停止。证据为 `runs/model-proxy-alias-fix-20261007-build.txt`、`runs/model-proxy-alias-fix-20261007-linux-request.txt`。中途生成的Mac ARM构建未用于Linux操作，旧失败消费字节未覆盖。主已核对ELF、hash及原始请求事件，通知同一独立验收会话重试I14；这证明代理缺陷修复，不代表完整生成/接续/测评通过。WSL空间仍归用户处理。

本次失败沿革：新独立验收的 I14 run `0aeae2e5b3e74f60b7331edaf6a15ccd` 启动后退出，gateway.log 原错为 `invalid or duplicate deployment`，现场已自动保存；Pi run `e05ca1f9b7974c308420d49ea283e9d1` 在 WSL mkdir 时遇到 `No space left on device`，尚未派发。2026-10-07 用户明确“我会处理 WSL 空间问题，请你修复 model-proxy 问题”。WSL 空间由用户处理，本任务不清理其远端数据。execution_owner 持续负责公共交付，已完成 proxy 修复、Linux 编译交付与实际自费请求证据；主已采用证据并通知同一独立验收会话。主读回失败 run 的 inputs/model-gateway.json，确认千帆 Token Plan、千问 Token Plan、普通千问的三个 DeepSeek0731 deployment 分别复用在 native/canonical 两个 alias；Rust loader 的全局唯一约束与该正常映射冲突。修复允许跨 alias 复用、保留 alias 内重复拒绝，不伪造供应商身份。验收仍绝不参赛；完整生成、接续与评测尚未通过。

当前收尾包括公共交付与进程回收边界。用户提供的旧Pi运行进程快照实际有321个僵尸，其中320归PID1 Python；3个存活浏览器daemon，存活Chrome相关进程合计489线程。新版Local创建已带 `--init`，历史执行路径和Hosted入口不能因此视为已修复。公共ResourceSupervisor已有内存/pids采集、有界补救和明确失败，但只回收自身直接子进程，不能替代PID1的孤儿回收责任。process_reaping_decision advisor负责最小跨环境处置判断；execution_owner继续公共交付闭环，主负责保存来源及进程边界整合。此事实不授权增加全局并发gate，也不授权参赛。

advisor已建议统一公共入口在安装/服务/Harness前使用标准静态Tini subreaper，Python Popen仍独占直接子进程退出状态；Local保留Docker init覆盖SDK自身。execution_owner在公共入口与安装器实现并用真实Linux浏览器open/snapshot/close取得PPID、线程、僵尸及退出码证据。活动浏览器与测试并发归工具生命周期和variant策略，不因快照有三个daemon就判定全泄漏；监控不能把提高pids限额当作孤儿回收修复。

资源实现与文档已提交 `dc417302`；Braid三个文件仅提交本任务资源hunks，其它dirty改动保留。保存来源修复提交 `96dc22d0`。统一轻量交付、Tini入口及模型接入提交 `2a4dfe58`。新独立验收I14初始观察约251 MiB/18个PID，首次依赖安装约34秒，但随后代理启动失败；未取得模型成功证据。完整使用和评分仍未完成，这些提交不是全任务完成声明。

2026-10-07 保存回执来源修复已落地：远端原件镜像为remote-save/remote-result-save，不能覆盖本机save/result-save；本机完成回收才写自己的storage_root。relay先回收再供自动评测使用，已回收的终态材料不重复传输。对610daf实际执行记录同步成功，原本机保存时间1791353029.8941178未被远端1791352588.2794924覆盖。没有重新启动或评测该run。最新安装器的实际Linux浏览器open/snapshot已成功，mcporter/portless目前只有help证据；OTLP Python闭包约2.5 MB继续随包携带，文档已与实现一致。新独立完整模型验收仍待可消费的新交付。

2026-10-07 用户对610daf处置明确选择“停止并保存现场”。已按该run冻结target通过Lab stop停止，观察回执为 stopped/inactive、exit_code=143；随后本机回收完成，save 返回 saved=true、errors=[]、as_of=1791353029.8941178。工作区、原生状态与日志位于 `runs/lab/runs/610daf8655bc4f178cf6b0b35e94cfc7/data/`，停止与保存原件归该run的records。没有派发新run、接续或评测，没有覆盖原执行版本。正在执行的turn/未落盘写入可能中断，现场保存不等于完整可恢复检查点。此次发现远端保存回执可能先于Mac回收完成，需要由保存实现明确来源，不能提前把远端 saved=true 当作本机回收完成；execution_owner继续修复该公共边界。

## 2026-10-07 全新新版 Lab 验收会话（当前）

用户要求从正常使用者视角重新完整验收 `I14-dx-test` 与 `pi-minimal-vv-dx-test`，使用真实自费模型，绝不参赛；官网评测只能使用自费、非排名的独立评分。该验收不接续旧 run 或原生会话，重点同时观察可用性、绕路/排错负担、墙钟耗时和 token 负担。主已确认新交付可实际消费并通知启动，新I14运行已受理；已有实验授权，不等待用户重复开工批准。

已核对：正常入口为 `python3 -m lab start VARIANT TARGET TASK`；当前目标配置的两 variant 均指向 `arc-core-direct-20261007p`，自费配方由 `harness/model-recipes/self-funded.json` 冻结；独立评分使用 `python3 -m lab evaluate RUN --kind self-test`，不等同比赛提交。只读 `lab status --all --json` 发现旧 `610daf8655bc4f178cf6b0b35e94cfc7` 仍为 running，属于历史现场，不能控制、接续或作为新版验收证据。启动前读回原件保存在 `runs/finals-experiment-loop/validation/preflight-status-20261007.json`。

当前下一步：同一新会话从正常入口重试I14自费验收，新装配消费修复后的Linux代理；WSL恢复空间等待用户处理。按 `evaluation.md` 的矩阵串行覆盖两个 variant，将真实使用成本与功能结果分开记录。Tini 下已有一次真实浏览器生命周期证据，但长运行进程累积仍待生成应用验收，不能用入口成功代替模型活动或评分。

2026-10-07 用户明确：“本任务的验收绝对不可以参赛”，并建议抛弃原验收会话、新开会话完整验收。该限制覆盖所有验收生成与评测，禁止 competition/official_evaluation、正式提交或上榜身份；官网独立评分只能自费且非排名，不从平台或比赛题目推断参赛许可。原独立会话停止后续派发、评测与接续，已有610daf现场保留，尚未取消该run。新的独立会话从正常Lab入口完整验收，不继承旧会话的绕路经验；消息尽量自然，具体标准和原件归本packet及evaluation。实现官网比赛接入分支不授予验收参赛权限。

新会话为 `01a114ec-c77a-7531-930b-9321fee3982f`，标题“Lab 新一轮完整独立验收”。已要求它只准备正常入口，等待新交付确认后启动真实自费运行，不接续旧run、不修改设施源码；发现问题交回本任务修复。原会话 `01a1118d-d790-7df1-93b5-df1801813158` 已收到停止后续操作的消息。610daf是否停止并保存现场已向用户提出非阻塞选择，未自行取消。旧评分与运行原件可作历史反馈，但不充当新一轮完整验收通过证据。

本轮最新交付事实：公共入口已登记真实 variant Popen，资源监督器不再依赖 PID 环境字段或杀自身；补救不杀活动 gateway/collector。memory.events.max 只是可能需要 reclaim 的边界事件，不当成不可逆失败；OOM、进程分配失败或补救后仍触顶才有界关闭实际 child 并保存原错，依据 [Linux cgroup 定义](https://docs.kernel.org/admin-guide/cgroup-v2.html)。新版轻量包保留其它 variants 的原全局 npm 输入，公共安装闭包独立锁定；实际 ARC Linux 安装约512 MB、192个依赖，原件 runs/public-minimal-final-CimnND/linux-install-evidence.txt。

原生旧格式 reader 已从 execution 移到 scripts/legacy_native_observation.py，调用既有 Pi/Braid reader；610daf/de22 的 messages=113、turns=193、provider sessions=2，以及原始断连事实保留。默认自费包的 proxy 字节缺漏已修复。供应商配方选择移出 target 后发现 Local 仍按旧 recipe 名选择 ARC Meter/凭据处理，已改用冻结派生的 model_transport；旧 target 仅兼容原标记，不能重新选择 ARC。剩余正在由 execution_owner 闭环的事项是新 Braid 资源修复的实际 Linux 执行字节、公共 Python 依赖安装与去除两个DX builder遗留重复最终装配分支。原610daf不动；Stage2 等实际执行材料确认，尚无新生成/接续/评分通过声明。

2026-10-07 用户明确模型配方指供应商模型配方，归 variant；官网比赛运行没有 model-proxy，所以不加载或应用供应商配方。公共设施归一化自费运行的模型运输，variant 统一消费 OPENAI_BASE_URL / OPENAI_API_KEY；比赛直接消费平台同名注入。角色模型、原生会话模型身份和预算仍由 variant 管理，不由运输层选择。当前已切断 competition 装配的供应商读取并移除公共 native descriptor，尚待官网上传字段合同与新交付真实运行资格闭环，不宣称验收通过。

轻量安装包已在 sfp7 的实际 ARC Linux image 安装固定 Node 24、npm lock 和 native patches，约两分钟、安装后 runtime 约937 MB，证据为 runs/public-package-linux-AodKRb/linux-installer-evidence.txt。公共最终装配职责及资源失败的受控子进程接线仍在补齐；Mac 组装与 Linux 安装成功不等于生成 Agent、接续及评分均通过。原610daf不动。

advisor 核对已有官网前端和成功上传原件后建议保留 model/visual_model/base_url 的已观察上传字段形状，不假定后台支持省略。比赛字段中的模型意图由 variant builder 导出角色模型，ARC 接入层填写已确认的官方端点，不从供应商配方推导。SDK 的环境透传只证明原生注入接口，不能证明上传字段默认。没有为本次核对发起比赛运行。独立验收继续原 Stage1 与冻结评分，Stage2 启动前等待新交付确认。

本轮已将最终装配调用移到公共 execution/public_package，variant-only builder 导出自身材料及 submission-models.json。根入口对比赛跳过供应商冻结，自费统一注入 OPENAI 两个变量；同任务原生 credential name 的兼容留在 Pi 适配，不由公共运输解释。源语法检查通过，未启动比赛运行。新 Linux 精简安装为约506 MB，原件 runs/public-pruned2-Q4LdpS/linux-install-evidence.txt；仍在核对必要依赖闭包不会删除其它 variant 的工具输入。资源补救的累计事件与处置后触顶已分开，采用 supervisor 持有真实 Popen 句柄；入口登记、最终新交付真实生成和接续仍待闭环。

2026-10-07 用户新增资源机制要求：不再充当 gate，监控并在触顶时尝试释放与補救，最终接受 fail-closed/fail-loudly，不持续 suspend 掩盖失败；覆盖内存和近期遇到的进程数上限。environment_causality 负责 scripts/runtime_resources.py 与实际 Braid pressure/native 执行模块的调查、实现及编译/真实原件反馈，advisor 协助作用层级与有界补救判断。当前610daf不动，不新增capacity或通用恢复框架；实际政策与已验证边界由该owner返回后整合。

2026-10-07 用户明确授权“这个分层没错，请应用”，并要求公共 native runtime 不进入提交包，改安装脚本在 Harness 启动前运行；随后要求避免本地只读宿主 runtime 与官网完整包的环境差异。当前实施采用同一轻量程序材料、统一启动入口和容器内固定依赖安装，两边不依赖不同的预装 runtime 路径。团队编译的 Braid/model-proxy 属程序执行字节，仍随程序交付，公共 Node/npm/Python 依赖由安装器准备；不能假定官网可下载团队自建 release。

execution_owner 持有公共最终装配、两DX builder/main wrapper、安装器和local挂载调整；主处理原生模型映射、Pi文件权限适配及跨组件文档；cold_local_profile 持有绑定variant的原生事实采集及已有事实合同的保留。advisor 已给出同入口/同固定版本安装路线，实际受限容器下载闭包和后续真实运行仍待资格化。610daf及原独立验收身份保持，不为本轮设施变更中断。

2026-10-07 用户提出公共运行设施与 variant 边界疑问。只读核对与 advisor 判断确认，新实现仍有双向耦合：公共装配复制在各 builder，公共服务反向知道原生别名和布局。当前建议及源码依据归 assessment：公共设施拥有最终装配、服务、运输与执行生命周期；variant 拥有原生行为和语义，共享原生机械适配明确标识而不混入通用 Lab。本次先报告判断，不因用户提出疑问自动扩大源码改动，当前独立 run 不动。

2026-10-07 用户告知验收会话刚被中断并要求继续。只读确认原独立会话 turn 为 interrupted；实际 run `610daf8655bc4f178cf6b0b35e94cfc7` 的保存状态截至北京时间 12:53:52 仍为 running/active。已给原会话发送自然接续消息，保持原 run 和负责人，不重新启动实验；继续原 Stage1 冻结、独立评分及 Stage2 接续验收。

2026-10-07 已修复 restart 隐式继承旧依赖：原实现复制整份 source.target_config，即使显式同名 target 或新 stage 也跳过维护配置。采用 advisor 建议，新 run 重新解析 target、装配当前程序/runtime，来源 stop/save 继续用来源冻结配置；需要固定旧 runtime 使用已有 LAB_CONFIG，不新增模式。源码语法检查已通过，下一次原 Stage2 接续负责取得真实装配证据。当前 610daf 不动；它携带的远端 source/config 也不热改，由独立负责人在正常结束后从维护入口接续。

2026-10-07 self-test 认证已通过实际只读请求：维护客户端 GET `/api/auth/session` 返回 HTTP 200、authenticated=true，原件为 `runs/self-test-auth-20261007/authentication.json`。已修复本机 Python 默认 CA 路径失效导致的 `CERTIFICATE_VERIFY_FAILED`，JSON 请求和 ZIP 上传共用标准库 SSL context，使用已有有效 CA，不关闭 TLS 校验、不新增依赖。已通知原独立验收会话复用现有私有登录材料；没有上传或评分，仍待 Stage1 冻结应用。旧 pending_auth 段落保留为历史故障事实，不再是当前阻塞。

2026-10-07 用户告知“钥匙串我刚刚授权好了”。此前等待系统授权的前提解除，evaluation_implementation 恢复原 self-test 认证与实际评分闭环，优先复用已有登录材料；已通知原独立验收会话在 Stage1 完成冻结后按原计划独立评分、接续 Stage2。授权完成不等于认证或评分已取得，下面的 pending_auth 记录是当时事实。默认维护基座同步为已正式发布的 p，不再指向旧 o。

2026-10-07 用户明确“是，你不必停下，继续”，继续原优化和验收闭环。runtime 集成已提交 `e7a3cb7d`，公共回执及 self-test 接入提交 `d7c4605b`。正式默认已切到直出 p：约 495 MiB，经维护入口首次发布 42.84 秒、再次调用复用；真实 ARC 容器在只读 runtime 下通过 `agent-browser open https://example.com` 与 snapshot，缓存后操作 2.78 秒，`--help` 不下载浏览器。构建与基座精简共用一个浏览器入口实现，不新增工具分层。原件见 evaluation；这些不是空缓存完整构建或生成 Agent 使用通过的证明。

独立 Stage1 run `610daf8655bc4f178cf6b0b35e94cfc7` 仍消费完整 c，已实际写入认证、数据库及前端文件，保持同一执行继续生成；不为默认材料更新打断它。完成后由原独立负责人冻结应用、执行模拟与 self-test 评测，再接续 Stage2。尚无阶段完成或评分。历史 j/m/o 的体积、发布及失败事实保留在下文，当前默认以 p 为准。

2026-10-07 用户再次提醒“避免过度的校验、安全、隐私设计”。后续修复必须对应已发生错误或具体的凭据泄露、误操作、产物损失风险，不扩展通用校验层、隐私框架或启动门禁；不把辅助证据缺失判成运行失败，不为填齐验收字段追加无关实验。继续优先原运行接续、构建部署耗时及正常使用负担。

2026-10-07 用户回复“那么继续推进优化”，继续授权既有优化闭环。当前优先解决原 Stage1 的原生接续故障，再以真实源码修改取得精简 runtime 的构建/部署/消费证据。execution_owner 持续持有构建部署，与独立验收的原恢复负责人协调在途版本，不重复构建或接管运行；主修正公共 dispatch 异常的状态与原错投影。self-test 钥匙串授权仍等待用户，不触发新查询。

当前 runtime 原始 `du -sk` 为 1,106,552 KiB，正式默认 j 为 551,760 KiB，最新直出 m 为 507,260 KiB（约 495 MiB）。m 的 37.07 秒是缓存命中的构建/导出，不是空缓存或 Braid 源码改动耗时；j 默认发布及同版本复用有正式部署回执。Stage1 最新 de22 已实际恢复同一 root native identity 后断连，原实施输入在旧 reset 中丢失可执行唤醒的问题正由原负责人修复；没有新的生成完成、冻结应用或评分证据。

随后恢复负责人已产出新 Braid c，execution_owner 复用其字节组装 o（518,416 KiB，约 506 MiB，实际组装 5.18 秒），通过维护入口正式发布并切换默认 target；原件为 `runs/arc-default-deploy-20261007/runs/default-runtime-recovery-c/records/runtime-deployment.json`。该发布仍为 full-rsync，同版本复用已有证据，新版本自动兼容基座选择/增量仍由同一 owner 完成。主已采用 advisor 的副作用边界判断修复公共 start 异常投影，并保留 subprocess stdout/stderr 到 start-error 原件；Local 派发受理显示 starting，而非尚无实际观察就报 running。以上只做编译和实际旧记录查询，后续资格由原独立接续取得。

最新维护 target 已内置正式 o 基座，普通用户不提供额外基座参数；维护增量路径实际取得 `reflink-base-plus-braid`、3.29 秒（`runs/arc-default-deploy-20261007/runtime-delta-staging2.{json,time}`）。发布已改为同父目录 staging 内完成复制/delta/新回执后 rename，避免 clone 携带旧回执被中断后误认。该样本 Braid hash 与 o 相同，只证明路径；c 原编译耗时日志缺失，不补造。原独立 run `610daf8655bc4f178cf6b0b35e94cfc7` 已实际消费完整 c，root 原身份 wake turn completed、fast 实施 wake turn running，应用完成仍未证明；不能称本次运行消费精简 o。I14 具体错误 brief 修复提交为 `fcc1a6bc`，其它当前任务集成仍待完成。

2026-10-07 用户补充官网费用回执的已知平台缺陷：创建为 `official_evaluation`、启动显示 `self_funded` 时，实际已经使用比赛费用。已核对新 run 的 Hosted start：当前没有比较这两个费用字段的拒绝校验，冻结模式不被启动响应覆盖，原始 upload/create/start 回执分别保存。因此不新增兼容层或平台写请求，只在启动边界及运行说明记录该例外；后续验收不能把这一差异判成自费或启动失败。此次为代码路径核对，未新发官网请求或消费比赛费用。

2026-10-07 11:00 当前恢复事实：第二版 Linux runtime 已部署，新 run `d38fa85756f24f13bb5fbb262b3fdf80` 在约 10:58 启动，保留原 native scope。恢复负责人读回两个中断 reset 均 `applied`、旧 provider session 均 `replaced`，并取得新的 completed `reset_continuation`；应用第一阶段完成及后续评分仍未取得证据。主此前只读上层验收会话，漏掉其子负责人已执行的进展，两次“还在准备 Linux”报告过时，不代表实际执行一直等待。

本次恢复发布从约 10:26 到 10:58：首次完整 Linux runtime 构建 705.7 秒，首次 restart（含约 1.1 GiB runtime 同步）156.0 秒；首版因 assignment 已恢复 active 而恢复 SQL 只接受 blocked，实际未触发 reset，修正一条条件后再次构建。第二版构建/导出存在失败重试，其中 Docker identity GET 10 秒超时使 runtime-source.json 未生成，包构建原错为该文件缺失；最终 restart 161.2 秒返回。这是完整 release 重建/输运、实现返工及导出边界错误的叠加，不是单纯交叉编译耗时。

用户指出 Helium 已登录 self-test，并明确允许逆向其登录接入。主实地确认已有 xiaoland 登录会话；撤回将“cookie 未部署”当作需要用户解决的外部前提。evaluation_implementation 持续完成现有登录态到维护客户端的安全接线及真实认证核验，凭据不进入公开记录或迁移 data，未取得该接线成功证据前不宣称 self-test 完整可用。

实际接入现已自动发现 Helium 目标域 cookie 并走 macOS Keychain 的既有 ACL；系统需要用户允许一次读取，不能由开发 Agent 绕过。用户对该系统授权回复“稍后再确认”，因此不再触发查询/弹窗，认证成功及新评分仍未取得。私密材料准备、复用、评测映射和 child 回收由设施负责，不把接线交给使用者；runtime 与其它独立工作继续。

认证模块已去除派生密钥出现在 openssl argv 的边界，使用系统 CommonCrypto 的内存接口；主实地确认当前 Python 可加载 CCCrypt 符号，仅核对原生接口可用，没有解密或外部请求。后续 HTTP 认证成功仍待用户授权，不以静态编译或符号发现代替。已准备的私有 cookie 材料会复用，避免每次查询重复钥匙串读取；必要准备发生在耗时打包前。

2026-10-07 用户新增明确授权：“runtime 的大小也是个值得关注的问题……尽可能精简，避免预打包开发环境比如 chromium、better-sqlite……完整构建、部署等的耗时也需要优化，请你推进。验收不要只是能用，而是用得好（使用者不绕弯子、消耗 token 少、消耗时间少）”。execution_owner 已接续 runtime、依赖材料、DX builders 与增量部署，evaluation_implementation 持续负责 self-test/auth/映射/回收；共享 local_run 按函数边界直接协调。advisor 建议冻结基座派生新 Braid 字节、远端宿主内独立复制后只传变化，并修复导出完成被清理网络错误否定的边界。体积、冷/热构建、实际传输与独立使用成本纳入 [evaluation](evaluation.md)，具体实施归 [implementation](implementation.md)。这些是正在实施的目标，尚无精简或提速通过声明。

## 当前纠正：模型配方实际消费

主采用 advisor 对普通 CLI 输出的判断：默认 brief 加必要回执，完整 JSON 显式 `--json`，Python API 与保存原件不变；控制受理、实际终态及保存完成分别表达。初版实际只读查询 d38 显示 running/active，表格输出 258 字节、同次完整 JSON 146,510 字节；这是输出规模事实，不是 token 节省测量。随后根据独立会话反馈，为单 run 补配方、来源、记录路径和保存回执，无参数列表仍是 brief；P2 读回 saved=true、d38 明示 unknown。start/restart/control/evaluate 的新默认输出仍待独立真实操作验收。

2026-10-07 用户指出，验收错误使用已明确耗尽的 ARC API，而非当前自费配方。主 Agent 承担这次冻结配置错误；历史 ARC 授权不代表本轮应选 ARC。P1 `e1ce4d6f6a174bb995c74f22e3db3a0d` 实际首次请求为 HTTP 402 `insufficient_balance`，没有应用生成进展，不能算有效零分或验收通过。原始 run、请求错误与保存材料保留；不要求用户补充 ARC 额度。

后续本轮验收改用集中维护的当前自费配方 `harness/model-recipes/self-funded.json`。生成装配与 Hosted 评测共用 `freeze_model_channel`，本地无模型评测不读取供应商凭据；运行入口已实际消费冻结路由和 selected catalog，不再只复制 `--route` 文件。per-provider 模型描述与私有凭据一并装配，不把官网 `billing_mode=self_funded` 当作模型配方切换。验收会话不负责寻找凭据或拼供应商配置。此节覆盖下文和 evaluation 中旧 ARC 冻结及“尚未收费运行”的过时状态；旧段落保留为实施沿革。

advisor `recipe_source_decision` 核对了文档审计中用户指定的 GLM/Flash/K2.7-code 链，以及 10 月 6 日 I14 实际冻结路由与千帆成功、Flash 千帆限额后 Ark 接管的记录。公共配方补齐同一来源的 K3 与 DeepSeek0731；两 variant 按实际角色闭包筛选，不从 catalog 的默认项选供应商。主已修改 execution/targets 的公共配方选择、所需 alias 冻结、selected catalog 与私有凭据材料；self-funded 路径移除 ARC Meter。provider_model_config 完成 builder/shared services 的网关消费链及 per-provider 参数，Linux binary 为 `runs/provider-model-config-20261007/delivery/model-proxy-linux-x86_64`，SHA256 `388b29d3002dbbf6add9051ad986cb6de46021736eace1d02b3ee4bf0a98d38f`。主接通原生模型描述，保留会话身份与兼容配置，并通过 Python 编译。已向原独立会话发送短消息继续 BookStack；尚无修复后实际调用或控制验收结果，不把源码编译当作通过。

修复后实际接续 run 为 `bf51263913f7414d9d50207deaa417c8`，保留 P1 native scope。保存的 `data/harness/e1ce4d6f6a174bb995c74f22e3db3a0d/producers/bf51263913f7414d9d50207deaa417c8/gateway.log` 中六次 `upstream_headers` 均为 `qianfan-token-plan-glm-5.3-flash`、HTTP 200，证明本次确实消费自费配方而非 ARC。独立会话确认真实工具活动及 pause/resume，实际暂停约 50 秒（等待 30 秒另加操作往返）。之后出现代理 413 `body_limit_or_read_error`，终态 failed；费用未采集不记零。SDK 回收又遇到程序 `.private/model-proxy` 的权限边界，现场通过保留私有原件及移出 SDK 回收范围恢复 saved=true，不代表自动保存已通过。provider_model_config 继续负责 413 根因/修复与新 binary；cold_local_profile 继续负责 saved-facts 同步、私有状态/SDK 回收边界。详见 evaluation 的实际记录，应用完成与后续矩阵仍未通过。

- **Objective**: 面向 2026-10-08 18:00 决赛截止，重设计开展、观察、控制、接续和分析 ARC 实验的完整设施。让 Agent 主要处理实验问题，不再负担环境接线、身份拼接和机械排错；simplicity、agent-friendly、traceability/observability 都以真实使用成本判断。
- **Guardrails**: 2026-10-06 用户已明确批准实施计划开工、自由提交及真实模型独立会话验收，费用不是问题；原话见下文。不控制其它任务运行、不清理历史数据、不 push。Mac 产物只在 WorkSSD。保留他人工作区改动；不编写或运行 Factory/Braid 的测试、smoke 或换名自检。用户新增的自实现模拟测试指生成应用的评测，不扩大为设施测试。
- **Verification**: 先定义代表需求与可观察结果，再以独立 Agent 的实际使用 profiling 取得反馈。覆盖三参数启动、status、pause/resume、同 variant restart、本地与 Hosted、Pi-only 与 Braid、OTLP/Console、资源、费用/turn 策略、顺序 stages、失败/取消及完整结果保存。查阅历史材料的耗时只作为诊断基线，不能充当真实启动或改造收益证明，方法见 [evaluation](evaluation.md)；不把这些活动塞进实现计划的调查阶段。
- **Current Truth**: 用户已批准 [design](design.md) 与六段 [implementation](implementation.md) 开工。自费配方已由真实请求 HTTP 200 证明实际消费，pause/resume 保持同一容器；最新 BookStack 接续 `a0d8fdab6eea4fe295c1bbcff65bca41` 约一分钟返回，status 正确显示 running/failed、资源与原生错误，失败现场自动保存成功。该次后续连接超时，没有完成应用或取得随题评分；费用未采集，完整验收仍未通过。
- **Next Step**: evaluation_implementation 接通 self-test 及四个测评后端的公共接口、配置、原件保存和实际操作；独立会话继续本地 GitHub Stage1/2 的生成与控制，冻结后独立评分。官网生成明确拒绝的路径不再重复上传；BookStack 保存现场及网络故障证据保留，按可消费的修复条件接续。主更新设计、矩阵及 packet 并集成返回，不重复启动 observer、不接管其它任务。

2026-10-07 最新 Linux proxy 去除任意请求体字节上限，仍保留读取超时、JSON 边界和具体 `body_read_error`；交付 binary SHA256 为 `eeacf0fb751b53499941e01ac49b061e497eac3212b0debd8c1a521087e77388`。旧 `388b29…` 是上一接续的冻结身份，不覆盖旧 run 材料。P2 接续已不再返回 413，但发生 `502 upstream_transport_error`，原始诊断为 `Connection timed out (os error 110)`，处于 SendRequest，不能证明供应商未收到请求，因此不扩大模糊错误自动 fallback。普通 `lab logs` 仍缺 SDK 捕获的过程内容，该问题由本地负责人持续处理。

主已修复生成装配未回写 Hosted frozen target_config 的共享边界，以及 Mac relay 在自动评测子 run 派发回执到达前退出的问题。原执行宿主仍是唯一 observer；Mac 仅登记已经派发的同身份 task-evaluation child 并启动 saved-facts relay。freeze application 失败保存具体派发错误，不留下无回执等待。上述最新接线仅完成静态编译，实际评测与 Hosted 仍待独立操作反馈。

最新 proxy 为请求保留实际序列化 `request_bytes` 和 attempt 的 `elapsed_ms`，不复制或记录 prompt；交付 SHA256 `19562690787bf2e0a51aefb71e1d99e35e6f70054fe6f57e050344ac8de83fd8`。P2 网络事后核对只证明宿主当时可达，不能替代容器失败时证据，故不擅自改供应商或 timeout。SDK 确认普通过程与 stderr 合并到 `.arc/stdout.log`，新增 observer 回收为 records/agent.stdout.log；新运行以启动前字节 offset 分隔，旧无 baseline 的记录明确包含迁移历史，不默认展开完整 rollout。

实际浏览器 Console 初次连接拒绝，原因是 Mac→sfp7 隧道退出；共享服务仍 HTTP 200，恢复 ssh -fNT 转发后页面因列表 manifest 字段缺失崩溃。cold_console_profile 持续负责 API/UI 契约、重新编译部署及实际页面反馈。Pi/Hosted Stage1 `7868abfa67fa4ce096126ccc768e4bde` 已由独立会话启动，当前在上传自包含包，没有平台 run ID，不重复提交不明写请求；BookStack 完成及评测仍待恢复。

当前提交 `a0305e4b` 保存公共自费配方、冻结入口、DX 消费链、观测回收与日志边界；已有网关/catalog 的其它工作区变化按归属保留，不宣称整个工作区已清洁交付。Console 当前已实际浏览器验证 Pi 详情的 lifecycle/activity、资源/native 与费用 unknown 可见；完整 JSON 不作为默认界面，进一步可读性部署由同一 owner 持续完成。

Hosted 的独立操作取得明确 HTTP 400，而非模型失败。cold_hosted_profile 当前 GET 核实 `hackathon` 已 ended，Stage1/2 需求仍可读但无新建生成提交入口。2026-10-07 用户纠正：self-test 是原先明确要求的测评后端，官网生成入口关闭不能扩大为测评不可用。撤回以 Evolution 替换本轮题目的提议及待确认事项，不启动新题或复用其它任务提交。原 Hosted 生成两阶段覆盖仍有缺口；本地 Stage1/2 生成、独立 self-test 评分继续沿用原授权。

独立会话继续持有已授权本地 I14/sfp7 Stage1→Stage2 验收，已收到短自然请求；BookStack 原网络故障现场保留。明确上传拒绝后的保存边界已由独立会话修复并用本次真实原件得到 saved=true（scope program/inputs/records，无远端执行 workspace），不是生成成功或完整远端回收。

后续提交为 `bd1e2cfe`（所需 catalog deployment、provider 描述消费、Console 与明确官网拒绝的保存）和 `27bd09e7`（费用缺口具体来源与原因）。catalog 只采用当前自费链依赖的新增项，其它已有工作区配置保持原样。当前 Pi 详情已实际浏览器核对：最新 502 原错、retained session、终态资源与费用 not_collected 原因可以直接查看；旧 P2 过程 stdout 已通过已有读取路径补入 records，并明确其启动边界未知，不改原始 workspace。

本地 Braid 首次 `26cd033f71ef4ee6bc5c3cd599b8e73d` 约四秒退出，原错为旧代码读取 `routes['factory26']` 的 KeyError，无模型调用；独立会话修复为按实际模型解析集中绑定，继续持有实际运行和 native idle 证据。该次失败未计为生成或接续通过。共用 Braid 状态读取与当前 scope/native 路径映射还在同一会话的修复闭环中，主不抢占控制或另建 observer。

原 Stage1 官方 self-test 页面当前可读，任务为 `github-stage-1-req-test`（另有 Stage2/3），上传应用 ZIP 最大 50 MB、根含 Dockerfile，页面说明结果仅本人可见、不计正式成绩。该入口与已关闭 Hosted submissions 不是同一路径；没有公开的精确需求/评测器版本时保留该限制，不将其变成新增许可门禁。evaluation_implementation 持续负责官网、self-test、本地随题、本地模拟四个测评后端的实现与真实反馈；主负责公共接口和文档集成。独立验收会话继续持有本地生成与控制，应用冻结后独立测评，隐藏反馈不进入生成。当前 self-test 仅取得只读入口证据，尚未上传评分，不能宣称接入或验收完成。

## 开工授权与责任

2026-10-06 用户原话：“好的，没问题，你可以开工了；你可以自由提交；基于 I14, pi-minimal 派生出 I14-dx-test, pi-minimal-vv-dx-test 两个 variants （派生新的 variant 是因为本次实验基础设施改进必定会涉及到 variant 的改进），按你说的用独立会话验收，你可以使用真实模型，不需要 mock，费用不是问题。”这条指示批准当前 design/implementation 的源码实施、必要部署、当前任务提交和真实模型验收。比赛提交与既有运行仍不在接管范围。

主 Agent 负责公共 run API、CLI、自动化、ARC 执行、restart、target 配置、整体集成和提交；cold_console_profile 持续负责 OTLP/Backend/Console/Braid view。前两位执行负责人的交付尚未接通真实控制、数据回收和原生接续，主没有采用其完成声明。evaluation_implementation 已确认没有构建、SDK 或收费运行在途，并转交执行责任；它继续持有 evaluate/package_arc_replay 的独立评测结果。2026-10-07 execution_owner 明确没有在途运行后，主接管两个 variant 的 main.py、I14 run.py 与共用 harness_services；execution_owner 仅维护两个 build.py 并从最新源码重建材料。原草稿和构建原件保留，不回退其他工作区。

2026-10-07 已移除 I14 dispatcher 对旧 execution context 的启动门禁，入口直接运行 variant。接续应用迁移到真实 template 根，native 数据独立迁移；当前平台输入与私有评测上下文不被旧输入覆盖。Hosted 共用轻量 raw receiver，按当前 Lab run ID 单独保存 producer 数据；本地使用共享 Collector。执行端 supervisor/Python 自动化通过 remote spawn 接入，Mac relay 只消费保存的记录并回收数据，不成为第二套运行观察器。以上是源码接线状态，尚未进行本轮真实模型验收。

已经向独立验收会话 `01a1118d-d790-7df1-93b5-df1801813158` 发送首个自然请求：“现在帮我用 pi-minimal-vv-dx-test 在 WSL 跑一次 BookStack。跑起来后暂停半分钟再恢复；看一下状态、日志和费用，确认有真实进展后停止并保存现场。顺便记录一下使用中哪里费劲。”不提供 CLI 操作清单或内部技术导航。请求开始实际 P1 使用，但发送成功不证明已经运行。费用目前可采集共享 account-key-window delta，不能冒称 per-run，因此 P1 的精确费用自动停止仍未覆盖；这次手动停止属于原验收矩阵明确允许的接续准备。WSL 固定实际 loaded image ID cfb919…，源/目标 17 层一致与默认配置差异的证据保存在 `runs/arc-bench-image-comparison-20261007.json`。

首个实际 P1 run 为 `e1ce4d6f6a174bb995c74f22e3db3a0d`。独立会话已观察到完整 ZIP 构建及输入重复传输，`starting` 未区分阶段会增加查日志成本；尚未收到其模型活动、pause/resume 或保存验收结果。advisor 因官方 SDK agent 目录会解引用 symlink，建议本地小程序目录＋固定只读 runtime、Hosted 完整 ZIP；已采用，P1 保持原冻结材料不打断，后续 P2 记录各段耗时与传输事实，不凭源码宣称收益。当前任务源码提交 `f01e5fa1`，后续 runtime/运输及 provider 配置修正仍进行中。

2026-10-07 用户追加：“llm gateway / model proxy 注意引入 per provider 的模型配置，比如 ARK 的 kimi-k2.7 的 max_tokens 和其它提供商的配置就不太一样。”已交 advisor 决定 catalog deployment 归属及 cap/default 语义，再交 provider_model_config 负责 catalog、Rust proxy、LiteLLM 发送边界及说明；主接 native 模型描述和统一装配。该责任不控制当前实验，也不擅自增加其它供应商的付费调用。具体数值必须核对对应 provider/套餐的来源，不能以一个模型名推导共同上限。

已安排 local_execution_decision advisor 判断官方 SDK prepare 后直接 Docker create/start 与继续捕获 SDK stdout 容器身份的取舍。判断依据是实际 SDK `docker run --rm`、随机容器名和只在结束后保存的 local-run.json；尚无本轮收费运行，不能把 SDK prepare 成功当作运行控制通过。

已采用 advisor 的直接 create→保存 CID→start 建议；cold_local_profile 接续其边界调查，持有新增 local_run.py 的真实执行、远端部署与控制回收结果，主负责把它接入公共 API。SDK Meter 是共享 access-key 累计差值，不保证单 run 归属，不因此增加串行 gate。默认 target registry 已改用实际 Mac 材料构建路径与远端执行路径，不再返回缺 SDK/runtime 的假 profile；任务 registry 提供 BookStack 和已冻结 GitHub Stage1/2 的需求入口。主只读 GET 确认 `/competitions/hackathon` 的实际 id 为 hackathon；官网凭据使用现存 ARC dotenv，而非不含 ARC key 的 models.env。以上仍是接线与事实核对，不是付费验收结果。

实际材料检查尚未通过：第一份 I14 ZIP 根 main.py 仍是旧 facility dispatcher；第一份 Pi ZIP 仅 28 项，缺 node/pi runtime。原包保留在 runs/finals-experiment-loop/materials，不发给独立验收者，variant owner 正修复直接 builder 与入口。新版执行装配已改为调用这两个 builder，不再进入 package_agent 的定义/制品门控包装。原生状态观察只采用真实 header/session_id；没有 provider turn ID 时保留缺失，不用行号补造。状态脚本错误保留 stdout/stderr，查询本身不制造活动时间。

历史 Hosted 原始 template-bundle ZIP 的实际根为 template/，已按这条证据修正下载映射到 data/workspace 与 data/harness。完整 native 历史仍迁移；新 raw collector 使用 native_scope/producers/当前 Lab run ID 独立目录，不把旧 batch 重新计作新 run 的消费。以上代码尚待真实包和平台运行验证。WSL SDK 已部署，镜像仍需执行 owner 完成传输；共享 Console 的 sfp7 宿主/容器 bridge 和 WSL 宿主反向隧道已有 HTTP 200，WSL 容器入口、实际原生生产、费用以及 Hosted raw 回收尚不能算验收通过。

独立验收会话 `01a1118d-d790-7df1-93b5-df1801813158` 负责真实首次使用与 profiling，不以阅读实现代替实际反馈。evaluation 已冻结最多八次生成与三项独立评测，覆盖 BookStack、GitHub Stage1/2 及策略/平台停止；费用来源未知不当作零，非正式参赛 self_funded。当前尚未开始收费验收，等待真实可消费执行与服务版本。旧段落中的“待开工”描述是历史授权沿革，不代表当前阶段。

用户随后要求验收派单尽量接近平日的自然消息，不发长串明确边界或操作导航。已告知独立会话：前述长说明属于准备，不作为冷启动顺畅证据；真正交付后的派单只描述实验目标与关心的结果，入口查找与排错都计入真实使用负担。

Console owner 已报告 sfp7 的实际部署：独立目录 `/home/yyh/factory26-exp-console-20261006`，loopback `127.0.0.1:18765`，服务 PID `3337058`，`/api/runs` 返回 200；Linux Braid binary 已编译并具备 `telemetry reconstruct --decoded`。这证明服务可启动，不证明真实 run 的生产、传输和投影已通过验收。执行 owner 的最新交付仍缺真实 ARC target/Hosted 接线，restart 仍有创建目录与旧 handle 继承问题，主未采用其“闭环完成”声明，已要求同一 owner 持续修复到实际可启动。当前仍没有本任务收费运行。

公共 observer 已接入 Console saved-facts 发布，终态只有 `save` 明确返回 `saved: true` 才结束；发布失败独立记录，不改变运行生命周期。共享字段为 `observability.service_url`、`registration_token_file` 和 `collector_token_file`，秘密不进入迁移 data。此接线仍需真实生产者验证。

主已实地只读确认 sfp7 HTTP 200；服务部署期间重启，PID 不作为永久身份。初次列表包含本任务构造的登记，不能证明真实生产链路，已要求 owner 删除；owner 已报告清除并明确旧 facility4 缺少 status/native turn/cost。约 27 MiB 的单次 RSS 只属于空载服务，不作为低内存验收结论。当前源码中的旧 `lab.control.Control`、exclusive/send 写入链没有调用方，已删除，保留进程出生身份与历史只读等待；这不等于整套 lab.exp 已退役。

主分担 `lab/arc_bench/hosted_run.py` 的真实官网 API 适配，执行 owner 继续负责打包、数据映射与实际 dispatch 接线。新模块保存 upload/create/start/cancel 请求及响应、真实 submission/run ID、日志 cursor、平台费用和全 workspace ZIP；未知写请求不自动重发，5xx/传输不明不冒充确定失败。当前只通过编译，未调用收费 API；规范 data 在平台导出中的映射和原生接续尚须与实际包完成闭环。

旧入口退役的调用核对确认：新评测仍可经 ARC adapter 导入旧 artifacts/core/telemetry，I14 的 experiment_entry/bootstrap 仍带 state_writer，package_agent/runtime 也被其他当前材料构建调用。整目录删除 lab.exp 会破坏这些维护调用方；已经冻结的 runner.pyz 不读当前源码，但重新构建仍受影响。新 run 必须提取实际 ARC/材料功能并切断门控，而非依赖 gate 在某些环境 no-op；旧源码中他人的未提交变化不得覆盖。该核对由 cold_local_profile 完成，只读，没有控制旧运行。新增 advisor 委派被平台 thread limit 拒绝，当前没有取得新的重大退役取舍意见，不把只读依赖核对冒充 advisor 建议。

## 历史需求与决定沿革

用户要求先定义“怎样算好的实验设施”，依据实验需求、工程知识、Agent 使用 profiling 建立完整因果链，不为找问题而找问题。Mac、WSL、sfp7 和官网差异属于设计对象，环境触发、集成耦合与设施内部缺陷分别归因。Exp Console 属于实验基础设施，不留作无期限的外围改进。

用户随后明确要求：Exp Console 不再承担实时介入；数据走 OTLP，Braid 自己实现 Braid 视图；本地共享包含 Collector/Backend 的观测服务，官网执行仍轻量自包含。还需资源采集，耦合 ARC-Bench 并统一 variant/gateway/collector 装配与路径，Python 条件自动取消/接续，自动保存完整工作区、日志、评测和费用，移除所有 gate/校验，三参数启动与停止/挂起，以及 stages。最后提醒“这个任务不小哦”。以上全部属于本轮设计范围，不按截止日期偷换成少数入口修补。

2026-10-06 用户补充了自动且强耦合的自实现模拟测试、官网重放、试题自带三类评测，统一各 variant 共用的 gateway/collector 装配，以及来自采集的 spend、native session turn idle 等 Python 变量。同期提出的跨 variant、多路径接续后来被用户撤回，当前同 variant 整体 data 迁移的决定见下文。

早期方案阶段的授权原话：“我同意你定下的这个推进方案，在开始实现之前和我确认方案，你可以自由继续推进。”当时只认可设计推进方法，尚未批准开工。该阶段已被顶部记录的明确开工授权替代；本段保留沿革，不要求当前执行重新申请许可。

用户随后明确：“核心调度对象/控制单位是run，而不是实验。（我后续还会不断补充，你不必停下）；你总是可以有不同的看法”。已撤掉把 run 定义为整条实验链再用 attempt 控制的候选；每次实际可独立派发/停止执行是 run，内部阶段服从平台真实粒度。来源、接续、重试和独立评测通过 run 关系连接，experiment 仅标签。stop 只操作指定 run，跨 run 操作与费用范围由普通 Python 程序明确表达。

用户质疑“撤销尚未派发的自动后续”是否仍保留 capacity/queue。复核确认这是设计越界：把尚未执行的 Python 代码想象成了设施待办任务，执行调查稿也残留 reservation/slot 的目标措辞。主 Agent 与 advisor 已撤回建议，目标设计删除内部 capacity、admission、slot、reservation、运行队列及未来任务撤销机制；历史故障证据保留。启动直接尝试执行，资源不足返回实际错误。Python 直接调用运行 API，不增加 action 解释层或任意脚本断点恢复；默认 stages 只在 completed 后继续，显式 restart 仍可处理 failed/stopped。stop RUN 不停止独立自动化程序，两者不混称。

用户最新修正要求：suspend 改 pause；接续不能用 continue；程序与数据路径规范后，只迁移数据且不允许切换 variant，extract 无意义；新增 status，无参数列未归档、非正常结束的 run brief，由绑定 variant 的脚本解释活动；继续收敛到可列实现计划，计划不含信息收集、调查或实验。当前采用 restart 表达同 variant 新执行，覆盖 stop→保存确定数据→迁移→启动的顺序；status 默认条件为未归档 AND lifecycle != completed。状态脚本固定在本次 program 版本，只读采集事实，脚本错误显示 unknown；正常执行得到零分仍为 completed。archive 仅列表标记，自动保存结果另行完成。此段覆盖前述历史 cross-variant、多路径接口及命名建议，设计正文以最新决定为准。

第二轮独立文档预演已经能推导启动/status、pause/resume、restart、归档后查回与独立评测；唯一操作缺口是自动三类评测的实际启用和官网费用来源。已补 task.json 的 evaluations 清单、同一应用快照绑定及 official billing_mode，不加许可字符串/审批门禁。另经 advisor 核对 Braid retained request 的实际约束，明确同 task 用原 native 状态、下一 task 建新状态，避免旧 root 已结束就跳过新需求。预演仍是文档反馈，不是运行验收。

主 Agent 与 advisor 的建议是删除重复证明、准入和人工写入协调，但保留路径边界、秘密处理、准确控制目标、未知收费写入防重复这四类直接风险约束。这是明确提出的保留建议，不声称已获用户认可，也不改名藏回“全部移除”之后。具体理由见 design。

Collector/Backend 推荐来自现有接收能力、所需领域查询和部署总成本，而不是只因赶期限或最小代码行数。没有“新架构已经验证”结论。最小可用交付必须纵向包含执行、观测、控制和归档；分批决定交付顺序，不取消完整目标。

## 负责人及可采用结果

| 负责人 | 范围 | 当前交付 |
| --- | --- | --- |
| 主 Agent | 产品要求、评价标准、跨组件 HLD、方案复核及 packet | 本 packet、design、evaluation、assessment |
| execution_owner | 两个派生 variant 的程序/数据分离及原生接续 | 材料构建不能替代实际同 task/new task 验收 |
| evaluation_implementation | evaluate/package_arc_replay 独立评测 | 尚待真实应用快照 |
| cold_console_profile（承接原 observability_owner） | OTLP、资源/费用/turn、Collector/Backend、Console 与 Braid 边界 | [观测专项](cells/observability.md)，原 owner 已不在活跃树，主 Agent 在本轮明确转交收敛责任 |
| finals_infra_advisor | 重大工程判断，不担任实现 reviewer | 明确 restart/native task 分支、status/archive、Python 自动化及 Braid 自有低频物化视图，已整合到 design |
| continuation_journey_rehearsal | 首次使用者的独立文档预演 | 两轮桌面使用反馈；最新补齐评测清单与费用模式入口，旧多路径意见已随用户修正失效；不是运行验收 |

只读实施准备得到两项具体采用结果：sfp7/WSL 可用空间约 110.8/25.1 GiB，WSL 已有本地 Console，跨域 HTTP 未验证；Pi 历史主会话 274 条 usage 的原生 cost 全零而平台有实际费用，raw OTLP 省略 message_update、timing 仅 first_update，不能直接作为精确 idle。原件与限制分别记录在执行、观测 cell，主线未控制这些运行。

第一轮 facility_journey_profile、environment_causality 和三个 cold-profile Agent 的结论保留在 assessment。后续相关工作保持原 owner；profile Agent 的原始意见不自动等于已采纳事实。

## 证据与更正

2026-10-06 的三次只读冷启动调查墙钟分别为本地 95 秒、Console 164 秒、Hosted **214 秒**。这是 Agent 执行整个调查的墙钟，不是独立测得的主动劳动。Hosted 原返回写成 114 秒，已按 epoch 差更正。Console 样本为纯 Pi variant，不产生 Braid 是预期行为；其 creation 快照也不能证明从未运行，历史读回实际已有 Pi 请求和工具活动。不能用这个样本证明 Braid 接入失败。

历史 capacity 拒绝原件有价值，但不能仅凭报错断言 admission 正确或存在泄漏。另一任务后续保存了 terminal 仍占槽、writer-close/release 及下一次 reserve 的证据，应据其解释生命周期接缝，不能把旧失败快照当当前运行状态。

- [当前设施证据与因果判断](assessment.md)
- [质量标准及 profiling 方法](evaluation.md)
- [完整需求与 HLD 草案](design.md)
- 历史基线：[实验 DX 复核](../experiment-dx-review/packet.md)、[实验操作](../experiment-operations/packet.md)、[实验追溯](../experiment-traceability/packet.md)
- 顺序阶段历史：[Pi Stage2/3 packet](../pi-minimal/sequential-stage2-stage3-20261006/packet.md)
- 本任务只读分析快照：runs/finals-experiment-loop/readback-20261006-analysis.json
