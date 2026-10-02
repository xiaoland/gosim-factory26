# Exp 技术合同与实现边界

2026-10-02，经独立预演修正并实施的合同。本文只定义新基线；旧格式进入history读取或显式artifact import，不进入以下写入/控制。产品边界见[design](design.md)，迁移和验收见[preparation](preparation.md)。字段名在实现中按此统一，内容缺失不以默认值补成授权或成功。

前轮基线已实施，但合同描述不等于每项能力都已完成运行验收。下文先保留该基线合同；文末“下一版方案”列出本轮源码核对出的缺口和拟议接口，尚未实施或冻结字段迁移。最新职责与生命周期归[design](design.md)，当前阶段以packet为准。

## 记录与存储

各公开记录有kind、schema_version、领域ID、producer身份/版本、写入序列或不可变内容摘要。动作参数与原始错误由所属组件保留；公开投影按字段白名单输出，实际key/token/cookie不写入制品或摘要。私有凭据通过目标环境显式credential_ref装配，不参与内容身份也不因导入继承授权。

| 记录 | 必需内容及owner |
| --- | --- |
| Experiment | controller产生：experiment_id、jobs、授权作用域引用、输入artifact引用、目的/比较条件、controller与runner制品、budget/storage、执行能力要求。 |
| Job | controller冻结：job_id、purpose、argv/命名输入、结果/输出合同、backend目标及能力、依赖的明确制品引用。purpose区分build/prepare/generate/evaluate；不建立任意步骤DAG语言。 |
| Attempt | controller分配：attempt_id、experiment/job、输入摘要、来源attempt/checkpoint、允许变更、分配预算、目标后端、dispatch_request_id。分配不等于受理/启动。 |
| Request | controller或明确控制调用者产生：request_id、attempt_id、action、参数摘要/原件、授权作用域、创建时间。按身份去重，不用命令文本或时间推断重复。 |
| Execution receipt | runner/平台适配生产：attempt、executor incarnation、实际后端身份、请求受理与动作效果、原始命令/退出/错误、资源与制品/telemetry引用。 |
| Artifact manifest | producer产生：artifact_id、type、内容清单/摘要、来源及组成、语义能力/缺损、producer与runtime版本。manifest原子发布后不可改写。 |
| Stream/batch | runner collector产生：attempt、stream_id、collector_epoch、batch_seq、signal、原始payload摘要、时间、receive_errors；序列在指定stream/epoch内解释。 |
| Analysis | analyzer产生：analysis_id、artifact与batch cutoff、程序版本、规则、统计/平台结果、缺口与原件入口。 |

控制域保存实验、请求和所消费证据引用；执行域保存实际效果、工作目录与原始采集；制品域保存不可变组成。逻辑域不要求单机三个数据库。当前实现可用已有JSON原子发布、SQLite原始批次与文件索引，避免新增数据库产品。Controller状态是只读投影，不能复制execution receipt后由自己改变终态。

Artifact URI解析为artifact_id/member/digest，member为受限相对路径。Resolver只有在内容与组成核验后才提供本机位置。归档保留链接字面值，不沿外链读文件；外部恢复依赖必须显式登记。Stage目录包含原始命令、阶段时间、具体HTTP/传输/退出错误；不完整stage不是published artifact。没有完整源原件时import只能生成partial/unknown观察，不能生成新执行证明。

## 最小执行接口

| 调用 | 语义 |
| --- | --- |
| capabilities(target) | 后端返回平台、runtime、存储/控制/遥测/检查点能力及观察时点；只读snapshot不预约容量。 |
| dispatch(attempt, request) | 受理固定单次输入并建立独立执行；返回executor身份、效果可查询入口或unknown。新执行失败不隐式改backend/模型。 |
| control(attempt, request) | 固定动作stop或已支持的pause/resume；pause不是checkpoint，resume暂停不是从历史重新生成。Unsupported显式拒绝。 |
| observe(attempt, cursor) | 返回该执行者自己的事实、源序列及原错；失联返回读取缺口，不修改历史执行状态。 |
| export(attempt, request) | 保全制品及批次，不再执行main；缺原件/传输失败保留资源和原错，完整核验后发布。 |

Controller先持久登记dispatch/control意图；executor先持久受理再产生副作用，阶段效果在下一阶段之前落盘。受理至实际启动之间仍可能崩溃，未消除的窗口保留unknown，不声称exactly-once。调用重入复用同request；参数摘要改变必须新request。同attempt重新执行入口永远不由重复请求触发。

接收侧在实际执行资源域持久绑定attempt_id、dispatch_request_id与incarnation；同attempt的不同dispatch请求拒绝第二次执行，不允许跨控制宿主各建监督者。响应丢失后可凭attempt/request查询这一绑定和效果，不依赖调用者曾收到socket地址。控制请求同时绑定预期incarnation及资源身份，变化时拒绝旧请求并返回实际原件，避免旧stop/pause操作新资源。

新runner制品显式冻结代码和依赖，而非从工作树广复制.py。每attempt有一个独立监督者，collector与其生命周期归属一致，执行资源/日志不依赖controller线程或管道。启动时runner创建私有持久runtime binding，包含attempt、incarnation、stream、控制入口、receiver入口和凭据引用；不以stdout握手作为唯一恢复来源。

Local控制由同机受权限保护的IPC接入；Docker通过后端的固定执行/读回方法访问runner控制入口；托管使用平台API。传输只承载版本化数据与固定动作，不执行接收到的任意shell字符串。第一版不暴露网络总控服务或自动跨宿主接管。

Runner恢复先核对host/boot/process birth、容器/daemon/labels/volume及自己的incarnation。只能接续可证明归属的观察、停止、输运和收尾；已执行或效果unknown时不重发入口。监督者死亡而子进程仍存活时，可查询/控制哪些资源由实际后端能力决定；原退出码无法取得就保持unknown，不能通过新进程观察追认exit0。没有可靠接管能力时保留现场并阻塞，不增加通用租约系统。

执行、交付、archive、telemetry和evaluation分别报告。顶层summary可有blocked/active/terminal等投影，但不作为任何物理效果或完成合同的权威。Terminal执行仍可有archive/telemetry未完成，允许在无模型动作的范围重入收尾。

## 资源与后端

Local资源域由固定host identity、受管理资源目录及同机锁共同界定；Docker资源域由daemon ID及该daemon可共同访问的受管准入资产界定。不同控制宿主必须走同一准入权威。Docker后端可使用同daemon受管volume和固定helper完成锁/受理/效果核对，不依赖Mac工作树本地registry；具体锁与identity实现须在预演确认。

第一版Docker准入采用daemon内一个明确资产身份的受管volume及固定helper，冻结volume/daemon/实现身份。Helper在共同锁内完成attempt受理绑定和reservation原子登记；负载资源按稳定attempt/launch身份及labels物化，观察同身份资源后才发布物化效果。占位后owner死亡且尚无容器时，reconcile同时核对持久launch记录、owner和该daemon资源；任一在途launch不能排除即保持unknown，不按TTL释放。容量释放由同权威保存实际退出/无在途launch依据和效果。缺证据时返回具体缺项与影响；人为放弃/释放必须是独立授权动作，保留unknown原件，不作为常规重试分支。外部无法排除的物化窗口是显式阻塞，不承诺自动清除。

Reservation核对owner及待物化执行，活动容量核对真实负载资源。释放以物理退出及完整身份观察为依据，未知owner保留容量。Runner受理前核验分配预算与本地storage reserve，执行期负责workspace/telemetry caps和固定停止升级；controller负责总实验派发预算。系统不删除活动cache或原证据维持运行。

托管adapter冻结包、题目、model_config、credential_mode和提交门控，platform request写pending后才发出。响应先保存原件再应用远端身份；重复消费同响应不重复建立attempt。pending无唯一远端身份时禁止再次POST。平台无可靠能力的字段为unsupported/unknown，不能用本地wrapper受理冒充平台已运行。平台费用模式和模型网关供应商分别呈现。

## Checkpoint与恢复

Harness提供版本化checkpoint组成及验证合同，至少包括可恢复文件、Git/未提交内容、DB/WAL、native会话、binary/材料和路径布局要求。取得checkpoint有明确来源attempt、执行资源身份、时间/切点、一致性方法和覆盖范围。活动源不提供一致性协议时，仅支持已确认停止后取得；导出若本身缺文件，发布partial并说明不能保证什么。

Checkpoint必须引用取得切点时的执行instance与资源出生身份；停止后取得的checkpoint还引用取得前停止依据。Prepared沿组成引用传递该来源instance。Launch核对stop evidence与同一instance，并核对资源未以新出生身份重启；当前观察或后端可验证的终态约束不足时保持unknown，不能拿一次旧stopped状态给外部Docker restart后的源发许可。

Prepared producer消费checkpoint、原Harness制品、允许材料变更和目标layout/runtime，实际执行无网络/无模型凭据prepare，保存命令与独立readback，完成内容和语义核验后发布prepared artifact。通用层核对生产合同，Braid/native专有检查由Harness生产者承担，不能以通用SQL静默修改或重建历史。

Prepared manifest只引用来源checkpoint和允许变更，不内联来源停止证明。Stop evidence为单独不可变原件，绑定source attempt/实际执行身份和相应后端观察；launch同时核验prepared、stop evidence、目标能力及授权。源被再次执行须有新execution身份，不拿旧停止观察给新源发许可。

跨环境恢复采用受管理logical layout和artifact resolver装配。容器跨daemon可维持相同逻辑root；跨OS/native路径改变须有Harness声明的语义迁移hook及独立readback。内容内部存在绝对路径不自动代表损坏，但需要明确layout约束，禁止文本全局替换。未支持的迁移组合在build或prepare边界拒绝。

Resolver区分内容读取与可执行装配：普通文件member的中间目录与最终对象不能沿symlink逃出制品，链接字面值单独返回，外部目标只有显式依赖绑定后才能装配。Prepared manifest冻结实际核验的layout/OS/runtime约束及迁移hook版本；新目标不满足约束时重新prepare，不因digest相同跳过语义核验。

应用artifact和checkpoint使用不同清单：应用可按交付合同排除.git/native等恢复材料；checkpoint不能复用应用排除规则。阶段应用以明确commit冻结，记录阶段身份，未提交内容不偷偷算入该commit。每题最终应用取得后独立分配evaluate attempt，不等其它题；费用/耗时/用量与生成分开。

## Telemetry与分析

Collector原始接收不按payload hash判业务重复。新receive保留原始重传及接收事实；controller从执行侧传输时以stream/epoch/batch_seq去重摄取同一源批次。HTTP确认在持久化之后，受理批次携带session/meta和receive errors，不再只导出protobuf裸文件。

同stream/epoch/batch_seq出现不同digest时拒绝应用并保留冲突原件。每个collector epoch发布最终持久序列和receive-error截止的封口回执；producer结束/flush另有结果。Controller排空须逐epoch确认指定范围已摄取并记录缺口，snapshot截止只表示分析范围。强杀producer或collector没有最终回执时，排空保持unknown，不以短期无新批次宣布完整。

源序列/时间、接收时间与controller摄取时间分别保存，跨机时间戳不用于推断严格因果。Call/span identity控制模型调用统计，metrics按delta/cumulative定义分析。没有必要身份时明确无法精确去重或归因，不用account余额差估计单run费用。

模型事实的desired来自冻结实验，frozen来自Harness/build制品，runtime-selected来自启动生产者的公开回执，observed来自实际请求/用量原件。Runner可以收集版本化Harness公开输出，不能为补这几个字段解析Braid/Pi私有数据库或输出完整进程Env；不支持的生产者明确保持unknown。材料通知的送达、实际采用与行为效果分别成立。

模型、provider endpoint、credential来源与官网credential_mode分别属于实验配方；通用Harness/runner/recovery不固化ARC-only或自动回落。角色的连接绑定显式冻结，实际采用另留事实。已冻结包和已发生请求保留原provider身份，配方修正只进入明确的新冻结。

分析snapshot固定每个stream/epoch截止序列、artifact列表、analyzer版本和规则；新增批次产生新snapshot，旧结果不改写。生成、重放、评分与设施耗时分开，隐藏评分结果不反馈给仍在生成的Agent。Monitor可报告疑似stale及连续观察依据，不能自动把token增长视为语义进展或擅自重启。

## 消费者与切换

统一 experiment projection 的读取层只消费已保存 producer 原件，保留原始身份及错误；阶段层从冻结 jobs、显式 target 和输入关系生成尚未派发及已经发生的阶段。最新 attempt 按实际 created_at 选择，历史 retry_of 保留；已分配评价的输入来自其自身冻结 attempt，而不是最新生成的输出。Manifest 摘要核对与实际内容/语义消费核验分开，缺字节或 partial 不提升保证。人类树和 JSON 共享此模型，CLI 不请求平台、运行 Docker inspect、读取原生私有 SQL 或产生另一份成功记录。

Controller 提供 next_actions，包括操作对象、命令和需重验的前提。保存事实不足以确认动作时返回原错与证据入口，不制造可执行 retry；export 接续原 attempt 的保全/输运，source-stop binding 在状态解释与 launch 中复用同一核对。Source 当前观察、私有 deployment、runtime 和准入仍属于执行门控。平台新鲜度只采用绑定 run 的成功 GET 原件；telemetry sealed 不声明 producer flush，Braid/Console 没有公开绑定观察时保持 unknown。

Console登记从实际executor接入manifest取得state/binary/access能力引用，重复接收不新增另一服务或容器。物理pause/resume/stop通过runner/backend固定控制接口；Braid工作项内部操作仍由Braid公共接口负责。GC消费manifest引用、活动/unknown资源与恢复承诺，缺完整扫描不回收。历史reader独立于新writer，不对旧数据默认补费用/出生身份/恢复保证。

新CLI拒绝旧格式写入并指向history或明确import；没有执行参数自动翻译。旧冻结执行器/runtime只在登记的退役通道保留，不修改source/ZIP/journal。活动旧dispatcher如依赖工作树，需要切换清单明确保全或停派交接；不能删除import后让它随机失败，也不能授权它继续无边界创建旧格式新实验。

本合同已完成独立预演和源码实施；当前具体 CLI/schema 以 lab/README.md 与公开 producer 为准。Console 自动发现/登记和跨 OS/native 根迁移仍不受支持。实际反馈及尚未验证的生命周期范围见 packet，不能凭字段定义声称现场能力已完成。


## Intent compilation 与 readiness

公共 compiler 消费 schema 1 intent，生成当前严格 experiment recipe；操作及字段合同归 [Lab](../../lab/README.md)。显式目标和命名政策承担高层选择，低层模板继续承担执行细节。模型与评价费用独立，from_generation 编译为 from_job/output，不建立任意 DAG。输入字节身份在 compile 冻结，在 build 前与实际发布后均核对；评分快照、runtime/handoff 描述发布成 compilation_evidence 制品。Compiler 源码摘要参与 bundle 重入身份，变化须新 bundle，不改已有实验。

Readiness 查询原 recipe 或已 build manifest，复用冻结 runtime、artifact 和来源停止绑定验证，读取声明 Docker endpoint 的白名单字段。它不调用 admission.authority：该函数会建立 helper 并调和预约，不能包装成只读查询。当前可用 slots 无只读合同，保持 unknown；声明容量和观察到的 workload 分别保存。首次域缺失卷显示尚未初始化，创建只能由实际 dispatch 重验后进行。Doctor 的资产事实不替代 start 的当前来源、预算、平台、凭据及物理准入门控。


制品复制分开 manifest 认证与 payload 核验。认证只证明引用摘要、record/ID 和根路径，不能据此声称源 payload 已核验。Materialize/transfer 在 staging 目标上完整核验声明内容后才发布；源变化造成收到的字节不匹配时仍拒绝。独立 verify/resolve 保留源全量核验，复制路径不预读源 payload。Transfer 目的 store 已存在时先核验目的结果并返回同一引用，不因来源移除而要求重新传输；没有引入以 stat/mtime 为依据的缓存。Doctor 的 asset 核验结果仅在当前查询中供来源元数据读取复用。

## 定义、运行数据与耗时验收

运行定义归 `experiments/`，运行数据归 `runs/`；Lab 作为通用执行器使用显式路径，并拒绝新运行目录与冻结 compilation bundle 重叠。新 build 将实际消费的原始 recipe 字节发布为小型定义快照，记录源路径、SHA 和 artifact relation；运行计划与快照属于执行证据，不能成为另一份可编辑定义。读取与哈希使用同一次字节读取，避免解析版本与记录身份不同。既有记录保留历史行为，缺来源关系就显示 unknown。

用户指定主验收为缩短打包、启动运行、热修复恢复运行的耗时。分别以完整打包命令至制品完成、启动请求至入口确认、取得明确热修复输入至恢复入口确认为端到端区间。记录输入规模、代码/runtime身份、宿主、缓存条件和阶段耗时；同类真实输入才可比较。减少哈希次数、doctor耗时或单次复制都只能解释变化，不能代替上述验收。平台排队、上传、来源停止等待和模型首请求各自记录，不从本地确认推断实际模型成功。

通用打包器将哈希与 ZIP 写入合成一次文件读取，manifest 描述实际写入的字节；保留原压缩策略。直接存储内嵌 ZIP 在真实包上节省压缩时间但增大上传体积，因目标包含上传总耗时而未采用。文件权限和内容清单合同保持不变，ZIP 容器哈希因编码变化会改变。首次运行与热恢复尚需代表性端到端反馈，不能由打包局部改进宣布完成。

## 下一版方案：当前缺口与接口责任

本节为技术方案，不是当前CLI或schema说明。调查对象为独立DX分支；I14启动复盘中的ResourceEvidence、`--execute-prepared`等修复属于原owner的对应版本，不能追认为本分支能力。正式迁移前核对已提交版本与真实材料，不合入其他owner的在途文件。

| 本分支当前行为 | 下一版合同要求 |
| --- | --- |
| build把输入收进run专属store，为每个run重新制作执行代码；Docker launch经控制宿主copy/cp。 | 材料跨run存在，运行绑定引用；缺失才构建或输运，执行域直接装配已有材料。 |
| publish核验并原子rename，payload仍是普通可写目录。 | 明确写入覆盖；受控published只读消费，弱Local继续核验收到的字节。 |
| from_job只支持generate→evaluate，等producer终态及archive非pending。 | 消费特定输出合同及必要成功事实；named产物发布和保留可独立于整域archive。 |
| checkpoint检查停止identity后copy；结构读回不能证明获取期间没有writer。 | Harness证明获取切点与writer关闭覆盖；通用hash、Git fsck或DB完整性不能补出该事实。 |
| prepare仅复制checkpoint，allowed_changes为空；runtime identity非空不等于语义兼容。 | Harness声明允许变更和兼容条件，实际产出派生语义；不静默把任意热补丁记为已支持。 |
| declared output存在就发布，不解释最终/阶段application合同。 | 生产者分别声明prepared可执行、最终交付或阶段快照；artifact存在不等于交付成功。 |
| launch_pending先于只读physical查询；snapshot会写registry、释放预约。 | 按具体动作登记意图和效果，query只读，reconcile显式；查询超时不扩大成entry未知。 |
| physical在helper锁外取得，随后用于释放；GC仅保守pin新exp目录。 | 动作版本参与释放判定；域内保留与GC排序，多位置关系不能由本机路径扫描猜测。 |

### 资产发布、位置与保留

继续使用artifact_id与manifest SHA及producer relation。构建复用指向既有发布产物和其依赖依据，不再次publish同一副本制造新生产身份；真实重新构建或修改材料则产生新artifact。内容寻址去重不是本轮合同的前提。可变源码/配置冻结一次取得实际内容身份；builder公开实际源码、lock、参数、目标及外部依赖身份到产物的选择依据，依赖尚未冻结则说明缺口，controller不由每个实验维护手写失效列表。ZIP封装单独绑定输入引用及编码参数，不将重新封装算作runtime重新生产。

域存储owner维护位置可用性与消费者保留，controller只保存其引用及回执。位置绑定完整artifact引用、domain与store/volume资产身份、受限相对位置、核验方法和观察；绝对路径由部署resolver解析。资产位置不依赖attempt出生身份，host重启也不自动使持久内容失效。可用、损坏、失联分别解释，不能改原manifest或用另一副本的成功填补失联位置。

发布与producer初始保留共同可见，不能先暴露published位置再补保留。消费者以稳定consumer、用途和请求，在域锁内确认位置未进入删除并登记保留，取得回执后才绑定/装配。保留同时保护承载它的volume/store或父目录，各用途独立release；producer退出或archive收尾不能绕过保留直接删除载体。跨域目标发布并承担保留后，源才按既定政策释放。崩溃留下的多余保留可查询、补完，不能按时间超期自动丢弃；controller不可达不解除consumer责任。元数据沿用文件原子发布与现有锁。

GC同锁登记稳定删除意图，无有效保留且满足writer关闭及既定保存承诺后才删除。Consumer先retain则删除被拒绝，删除意图先成立则新retain被拒绝；先前扫描结果不授权稍后删除。删除效果响应丢失查询原请求，失败保留具体对象与缺口，不恢复为可用或改称不存在；确认尚未发生删除才可取消意图。Retain只防回收，内容和装配仍由其相应事实证明。

Docker域用持久assets volume保留published，工作负载只获得只读访问；producer向staging写入，由存储owner核验并发布。可写恢复材料进入独立workspace，原artifact不随Git/SQLite写入改变。Local无法排除同UID写入口时，在装配复制/读取边界核验字节并复用本次结果，普通目录不消费永久可信receipt。具体copy/COW能力是后端选择；不为此引入通用overlay或扩大权限隔离体系。

同daemon消费先取得小型manifest和域位置事实，直接装配named output；完整archive由原owner继续保全。跨daemon缺内容时transfer保持原identity、保留partial并核验接收内容后发布。当前托管仅支持整包ZIP提交；submission是消费关系，除非平台具备完整读回及核验能力，不能登记成该artifact的可物化副本，也不自动继承费用授权。

### 证明覆盖与失效

内容事实归store，恢复/交付语义归Harness，目标能力和装配归backend/runner，当前来源关闭归实际控制权威。沿已有readback正向保存检查范围、实际依赖、目标条件和缺口，消费者按用途选择所需事实；“validator相同”只能维持已覆盖的保证，不能把存在性或结构解析升级为恢复成功。Compiler从producer能力与维护的目标配置解析这些绑定，不要求开发者拼接新的proof identity。

| 变化或动作 | 延续的事实 | 需重新取得的事实 |
| --- | --- | --- |
| 同目标新run、已有受控发布材料 | 内容与有相同依赖的生产语义。 | consumer保留、新attempt及其装配/ready/entry；当前容量与授权门控。 |
| 配方或模型政策改变 | 未依赖该配置的runtime/Harness材料、原checkpoint来源。 | 实际受影响的构建/恢复语义与新配方绑定；模型嵌入材料时不得忽略。 |
| Harness热修复 | 原checkpoint内容、来源和历史证据。 | 允许变更、validator/依赖和目标兼容判定、派生prepared及新run关系。 |
| OS/runtime/native布局改变 | 内容身份及原语义的历史覆盖。 | Harness目标兼容或迁移hook读回、新目标装配。 |
| 跨域接收或弱Local读取 | producer来源、匹配内容所覆盖的语义。 | 实际接收字节、目标位置/保留与装配。 |
| workspace已被入口/accessor写入 | 原发布artifact的事实。 | 当前workspace状态；不能复用其初始装配核验来证明运行后内容。 |
| 来源重启或writer覆盖变化 | 取得时的历史原件。 | 当前控制覆盖、停止与一致切点依据；旧stopped不发新启动许可。 |

Checkpoint获取至少关闭全部相关writer，或消费Harness明确的一致快照协议。域受管动作排序及关闭覆盖保护整个获取窗口，捕获前后两次stopped观察不能排除中间写入；覆盖失效即partial/unknown。DB/WAL、Git对象/未提交工作和native尾部属于同一获取窗口，分别解析成功只证明结构可读。从origin补HEAD/index产生带缺口的派生事实，不能改写为原历史完整。

热修复派生合同绑定原checkpoint、修复材料、允许与实际变更、validator及其相关解释器依赖、目标条件和恢复损失。只重取变化触及的语义，不将所有Harness源码变化视为整个checkpoint失效。目标身份变化先由Harness判断兼容；无需迁移内容时增加目标兼容事实，保留原prepared引用，不复制相同内容制造新prepared。

Application合同至少固定允许需求、内容、来源attempt、最终或阶段身份、选定commit与未提交内容处理、交付生产事实。评价消费这一冻结及其授权，不要求恢复complete，也不从目录存在或producer退出0推断交付完成。Prepared同样须有自己合同的成功发布事实；该事实成立后，后续archive/telemetry错误不撤销其语义或触发再次prepare。

### 域权威与动作效果

域配置先界定受管容量池和谁能创建/启动/重启。受管动作共同排序，未明确释放的请求继续占位；终止并释放的执行不得重启，新执行重新准入。暂停/恢复沿同身份且不释放容量。外部调度者共享权威或划分独立池；管理员绕过控制路径作为维护/接管处理。名额预约与宿主物理资源保证分开，不能通过每次全量inspect补出不存在的排他调度约定。

在此覆盖内，终态及writer关闭可以成为单调事实，启动消费域权威及覆盖状态，不每次重扫同一停止来源。旧来源可被外部重启、accessor未纳入覆盖或发生维护接管时，这个依据不成立，须重新取得对应观察。减少检查来自责任和失效合同，不来自把陈旧事实改标为新鲜。

覆盖包含SDK child、runner、Console等受管控制入口。维护先关闭新动作并推进覆盖版本，再进行外部操作及重新对账；reserve/reconcile提交核对此版本。无法关闭或观察外部控制入口的域保持保守边界，不能把手工约定追认为终态保证。覆盖版本是现有域事实的修订，预约周期可由既有request/incarnation绑定表示，不要求开发者掌握另一组身份。

以下为能力划分，函数名仅用于讨论，不是新增CLI命令或第二套状态机：

| 能力 | 唯一效果owner与接续合同 |
| --- | --- |
| preflight | Backend只读环境与能力观察，不初始化helper/volume或隐式安装依赖；失败保留原错与覆盖，沿原attempt重查。 |
| domain query | 读取既有权威事实，可经短时helper只读挂载已存在资产；不得新建缺失volume、写registry、释放预约或启动负载。查询通道自身的对象/错误由backend负责，不扩大为entry未知。 |
| initialize/handoff | 域owner建立或接管维护的权威资产及覆盖，独立于每次run；缺失时报告未建立，不夹在只读查询里。 |
| reserve/reconcile | 域权威登记稳定请求、参数与占位，或应用明确核对结果；响应丢失查询同请求，不重新分配。 |
| materialize | Backend分别持久登记资源create、输入装配、runner启动意图；查询精确对象身份、内容读回及出生身份后接续。 |
| runner ready | Runner发布固定runtime、装配、控制入口、限额和必需服务事实；OTLP与ResourceEvidence分别声明，容器started不代替ready。 |
| start entry | Runner先登记固定入口请求与启动窗口，再绑定进程出生及效果；未知窗口只查询，不重发main。 |
| publish/export | 原producer与backend分别拥有内容发布和输运；接续同发布意图及artifact身份，partial输运不改变entry事实。 |

Controller只发意图并消费上述owner事实；公开状态不产生另一份可修改的执行终态。一次dispatch可组织这些动作，但不能仅留下一个覆盖所有阶段的launch_pending。各作用域已确认的事实按原owner序列保留，后续失败不回滚为“所有步骤未知”。

受管动作在共同锁内先登记意图并推进版本，再调用物理动作、保存效果。超时不清除pending，动作版本相同也不能排除迟到副作用。物理观察前取得对象动作版本，观察可在锁外进行；释放时核对精确终态、对象出生、预约周期、此前动作及覆盖版本、无未决物化/启动/重启，并保证该终态不可受管重启。不能观察后才补入最新版本。

未知受管对象保留其已有占位，不强迫其他仍有容量的请求等待该对象成功inspect；无法界定外部占用的覆盖缺口仍阻塞相关容量许可。Not-started只能由效果owner证明未进入副作用调用且无旧调用在途，不能由调用者依据缺文件产生。释放不能只靠未发现容器、旧terminal快照或TTL。原实现的snapshot必须拆成只读query与明确reconcile，而不是只改函数名称。

只读helper的生命周期归backend查询通道，具有稳定query请求和自己的错误范围。挂载须保护既有权威资产身份及生命周期；仅先inspect再挂载不能排除删除/重建交错。Docker会在挂载缺失named volume时创建它，`--mount`也不例外，不能把只读选项当成“仅打开既有卷”。[Docker官方说明](https://docs.docker.com/engine/storage/volumes/#start-a-container-with-a-volume)。域维护/删除门控须覆盖查询期间，或实际查询机制拒绝隐式初始化；缺失权威报告未建立，失败报告原错，不能返回空registry。

I14两份原错分别限定边界：reserve前inspect超时尚未调用reserve helper/负载create，但此前authority volume已可能建立，不能称完全无副作用；export docker cp超时可能留下partial或仍在进行的复制，只影响输运，不能重跑prepare/收费入口。保留具体对象、HTTP/退出/超时原件，效果未知不被宽泛的retry掩盖。

Ready逐项服务失败时，先对账原collector/控制入口等动作；只有入口尚未受理且对应旧动作已结束或隔离，才修复缺项并继续原请求，不重启整个runner补偿。Export固定源封口、发布身份与各stage写入范围；先确认旧复制结束或隔离它的目标写入，再接续同产物，不把超时等同复制已停。

### 架构检验与实施前核实

三类流程并列验收，不指定首条实施路径。真实输入下同时记录用户发起到可交付制品/入口确认的端到端时间、主动操作次数，以及构建、扫描、装配、传输、等待和收尾的实际工作。首次缺资产、无变化复用、相关局部变更分别说明输入与缓存条件。移出关键路径的archive工作及保留仍计入总成本和完成责任；没有实测前不承诺倍率。

最有判别力的实施前核实是：现存终态控制路径能否绕过准入重新启动；负载/accessor是否仍持有发布存储可写入口；consumer保留与GC是否存在无保护窗口。答案分别决定是否能减少全域inspect、跨阶段重复哈希和archive等待。接口预演还须覆盖响应丢失后查询、controller重连、目标位置失联、同产物不同用途和有修复材料的恢复；使用现存错误/材料推演，并将无法取得的实际效果标为待验收，不造fixture或运行设施测试。

具体改动面、公开入口和按kind版本切换已进入[开工说明](preparation.md)，当前待开工复核。各owner依本文的责任与失败合同实现局部字段，不能更改不可变manifest或静默扩大保证。真实模型、平台写入、旧来源停止、Console部署与数据清理仍按各任务范围，不由本节扩大授权。

开工准备补充两项新材料的必需条件：预算包装器取消child豁免、继承父Braid binding；runner复用现有ResourceEvidence并发布实际样本绑定/ready。未满足这些能力的旧包保留历史，不能因hash未变而进入新生成。辅助query采用有界通道，不登记生成预约；copy只保留输运效果，可写accessor进入writer覆盖，构建按实际资源竞争核算。
