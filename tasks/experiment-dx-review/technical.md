# Exp 基线合同与生命周期

2026-10-02，经独立预演修正并实施的合同。本文只定义新基线；旧格式进入history读取或显式artifact import，不进入以下写入/控制。产品边界见[design](design.md)，迁移和验收见[preparation](preparation.md)。字段名在实现中按此统一，内容缺失不以默认值补成授权或成功。

本文件是已实现基线的技术合同。2026-10-02用户要求回到架构性问题后，最新[架构讨论稿](design.md)尚未形成新的LLD或字段迁移决定；此处保留当前行为，不把讨论中的能力追认为已实现。当前阶段以packet为准。

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
