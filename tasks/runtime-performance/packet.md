# 运行时资源采样与性能剖析

## 当前状态与授权

2026-10-08，用户明确授权：“好的，我同意这个方案；你现在可以开始修复这6个P0～P1的问题了”。实施范围为PSS覆盖、保护与重采样分离（含耗时/延迟）、事件现场、异常留存、CPU/I/O投影和出生身份/业务归属六项。P2深层profiling不在此次实施范围。不操作主线程运行、不启动模型或官网实验，不push。用户后续明确“可以提交”，授权本任务本地commit。

当前六项源码修复已提交为2cca0d0f；独立Linux正常服务运行已量化短时采样开销。用户随后授权将新材料正常原生接续到既有本地I15，目前接续派发在途。超过12进程的覆盖、长时轮转和真实负载验收仍待实际证据；官网生效尚未验收。

任务目标是让运行证据支持回答：何时发生资源压力、哪些进程或工作阶段贡献占用、为何出现性能退化，以及证据有何缺口。资源文件存在、采集器启动成功或曲线有值均不足以证明达成目标。

本任务负责共享采样、剖析和分析能力；I15 的参赛、恢复、费用与运行控制继续归 [I15 packet](../iteration15/packet.md)。已有 [official-runtime-observability](../official-runtime-observability/packet.md) 主要负责 ARC 追溯与 Git 历史，不与本任务合并。本侧负责用户新增授权的这一次本地I15材料生产、正常接续和初始采用验收，不调用主线程子Agent。后续既定终态及评分义务继续由I15原监控承接。

## 已有基础与事实边界

主线程已经修复 Hosted collector 的 agent_support 导入路径，以及 Local 外部 OTLP 接收器无法采执行容器的问题。当前公共 ResourceSupervisor 在容器内复用既有循环调用 ResourceEvidence，Hosted OTLP 接收器关闭重复资源采样。重新生产官网包会复制当前 Python 源；再次上传旧 ZIP 不会获得修复。

已有本地真实采样能记录 cgroup memory.stat/peak、进程身份与树、选中进程 smaps_rollup/PSS。公开 receiver 和短时容器服务操作已有实际反馈；这不是高并发负载验收，也不能补回此前官网 Sheet 缺失的历史峰值。运行身份与是否实际部署必须从 I15 当前 packet 核实，不在这里复制易失状态。

2026-10-08 本侧只读审查确认当前限制：普通采样周期是在前轮工作结束后再等待约2秒，PSS 明细通常每10秒最多12个进程；触顶与final额外采样。它不是所有进程的同期PSS，也不是瞬时OOM受害者追踪。PSS总和不能直接等同cgroup内存总量，memory.stat子项也不能不加区分地全部求和。

## 已确认缺口与实施优先级

| 优先级 | 事实或风险 | 建议及判别依据 |
| --- | --- | --- |
| P0 | PSS固定选最多12个进程，长期大户可能反复入选，其余长期未覆盖；当前缺明确的PSS覆盖与新鲜度摘要 | 大户优先并轮转其余目标；记录符合范围的数量、实际采样数量、遗漏原因及每进程最后采样时间。不能将部分覆盖称为全部进程。 |
| P0 | ResourceSupervisor先做完整sample再读触顶状态；扫描、smaps和同步落盘都在保护线程，存在推迟判断的风险，但尚未测出开销 | 先量化采样耗时与监督延迟，再确定轻量判断和重采样的边界。保留唯一采样责任，不让无界重采样阻塞资源保护。 |
| P0 | resource_limit明细在触发后等待1秒再采，进程可能已被OOM杀死；普通2秒/明细10秒会漏短时突增 | 保留近期样本；结合已有物理启动/退出事件、峰值增加和资源压力触发有界明细。事件触发不保证赶在内核OOM前完成，须明确能力限制。 |
| P0 | resources.jsonl只保留当前和上一段，下一次轮转会丢弃更早段 | 普通样本维持有界存储；异常及启动突增的相关证据独立保全，记录缺失时间范围。不得为保全无限扩张日志。 |
| P1 | inventory读取了逐进程cpu_ticks和io_bytes，构造最终processes列表时未携带，真实短时样本也没有这两字段 | 保存原始计数；使用同一出生身份的计数差与单调时间差计算速率。不能以累计量当本轮消耗；读取失败不写零。 |
| P1 | 资源样本没有直接连接Braid session、Issue/PR、turn和工具作业，进程树在父进程退出后也不足以解释归属 | 复用已登记execution/start/parent_start记录及PID出生身份离线关联，不读取完整环境/命令行，不另建Agent维护的资源关系表。 |
| P1 | 有sample_started，却没有明确sample_finished/耗时/调度延迟；数据内各读取并非原子同期快照 | 记录采样起止、实际间隔、跳过/过期/身份变化，展示观测窗口。按实际开销决定频率，不先宣称2秒精确周期。 |
| P2 | 资源观测尚不能说明调用栈、分配来源或事件循环卡顿 | 热点确认后才开展短时CPU调用栈或V8采样分配剖析，保留触发原因、目标和能力边界；不默认全进程永久profiling。 |

实施入口：

- [agent_support.py](../../tooling/scripts/agent_support.py)：ResourceEvidence、process_identity、process_memory_evidence、process_evidence。审查时PSS选择在289–299行，CPU/I/O读取在233–243行、最终投影在283行，轮转在311–325行；接续时重新定位，不能假定行号不变。
- [harness_services.py](../../lab/arc_bench/harness_services.py)：ResourceSupervisor的采样/触顶/终态顺序。
- [runtime_resources.py](../../tooling/scripts/runtime_resources.py)：原生进程execution/start与出生身份登记。
- [lab/otlp.py](../../lab/otlp.py)、[public_package.py](../../tooling/linux/public_package.py)：采样职责、包装路径及生产消费。
- [资源职责说明](../../docs/product-tdd/runtime-resources.md)：持久合同归属。仅在实际实施改变职责时更新，不将本任务建议复制为现行合同。

## 建议组织方式

持续观测保留cgroup分类、CPU/I/O、PSI、进程身份和RSS；PSS采用有覆盖说明的周期明细及事件补充。资源事件与已有native生命周期记录用单调时间、boot/namespace/cgroup身份、PID/starttime关联，跨恢复不把不同执行的原始单调时钟直接相减。

Node热点进一步区分heapUsed/heapTotal、external/arrayBuffers与RSS。arrayBuffers已包含在external中，不能重复求和；V8堆分配也不代表全部原生内存。CPU忙、等待模型网络、事件循环堵塞和内存回收停顿需要不同证据，不能仅从耗时或低CPU推断。

官网权限不足时，perf/eBPF、内核OOM受害者和部分/proc字段可能不可用。记录具体能力/错误，使用允许的用户态证据；不要升级权限或假称受害者已知。接近OOM时不自动生成完整heap snapshot，其额外内存和停顿会影响被观察运行。是否开展profiling及其额外负载需要具体范围。

## 下一步与完成标准

1. 接续时读取当前源码及主线程已经完成的变化，避免覆盖同时进行的修复。先核对P0/P1缺口是否仍存在，再形成最小实施范围。
2. 优先完成PSS覆盖说明、采样自身开销/监督延迟、事件现场保存、CPU/I/O投影和执行身份关联。先证据闭环，后深层profiler，不以增加字段数作为完成标准。
3. 实际反馈采用已授权的正常服务操作与运行；不编写或运行Factory/Braid测试、模拟探针或额外压力实验。新模型/官网运行须有对应授权。
4. 从已保存证据还原至少一次真实资源增长事件：关联启动/turn/工具、cgroup分类及进程明细；明确无法归属部分、采样窗口、遗漏与权限错误。不得把进程PSS与cgroup记账强行配平。
5. 量化采样耗时、实际周期、采集器CPU/RSS及证据增长量，在真实同类阶段判断开销；目前没有已批准的数值预算，不自行宣布达标。
6. 验证长时轮转后关键异常仍可读取；被杀进程无法补采时保留最后已知身份、邻近样本和内核事件，未知受害者继续标记未知。
7. 分别确认Local与新生产Hosted材料的消费及正常产出，源修改不等于官网生效。收尾更新已有职责文档，交付事实、限制及未完成事项。

P0/P1证据与误导性缺口解决、实际开销已量化、可从归档独立还原事件且部署边界明确，才可称采样能力完成；深层profiling按真实热点范围另行确定。当前六项源码已改，编译及旧归档关联已取得反馈；下述部署后验证仍未完成。

## 本次实现与反馈

- `agent_support.py`保留6个按作用域排序的大户，另外最多6个按最久未尝试轮转；记录PSS尝试/成功/未覆盖和最近成功时间。保存逐进程CPU/I/O计数、读取窗口、错误和出生身份复核，不重复读取stat取得CPU。
- `ResourceSupervisor`保护循环先读轻量cgroup，再向唯一worker提交合并请求。保留触顶原因，final合并未处理原因；记录调度/排队延迟及合并数，关闭等待超时明确incomplete。没有新增实验或独立collector。
- 启动/消失、至少64MiB相邻内存或peak增长、内核memory/pids事件触发明细；前3个样本进入独立事件日志。普通两段各31MiB，事件和关键日志各16MiB；关键日志不被普通启动事件填满。capped及丢弃数量可见，总声明容量更新为96MiB（不含小型状态文件）。
- 新进程登记增加namespace证据，读取不可得不改变launch行为；`resource_attribution.py`只读出生身份登记、native-state、manifest/status和白名单工具作业字段。直接关联与祖先推断区别标记；旧登记缺namespace、历史活动turn和无法关联者保持明确限制。原始计数按相同boot/namespace/出生身份及单调时间差计算速率。
- Hosted两条既有轻量回收路径已加入worker和失败摘要；完整归档仍拥有日志及登记。跨组件现行说明更新于runtime-resources.md，命令入口归tooling/scripts/README.md。

2026-10-08对六个Python源执行内存内编译，无cache产物；不运行Factory/Braid测试。对已有44c16936归档运行实际只读关联命令，426个样本、2557个登记身份无解析错误；19497条进程观测中15782条找到归属（5946条直接出生身份、9836条样本祖先推断），3715条unknown。结果连接到根Issue、业务Issue、PR/review及5401条工具作业证据。它们是逐样本观测次数，不是独立进程或作业数，旧namespace证据缺失。旧日志缺逐进程CPU/I/O，18944条可比较观测明确报计数不可得，没有生成虚构速率。

原件与摘要见[runs/runtime-performance](../../runs/runtime-performance/)，其中`archived-attribution.jsonl`、`archived-attribution-summary.json`来自同一冻结归档的离线读取，不向生成回送内容。

后续必要反馈：在用户另行安排的实际Linux执行消费新Python材料及runtime登记材料，核对超过12个进程时的轮转/失败覆盖、普通日志轮转后事件留存、final完成或incomplete回执，并量化collection/total/thread CPU、实际间隔和证据增长量。当前没有新执行，所以这些反馈、官网生效及实际OOM前细节均未知。持续主线程运行与模型配方完全未改；本侧不自行部署或重新提交。

## 调研来源与证据

机制结论优先使用官方资料，论坛只作为实践问题线索，不当作本运行根因证据。

- [Linux cgroup v2](https://docs.kernel.org/admin-guide/cgroup-v2.html)：memory.stat/peak/events/local、CPU/I/O记账及OOM语义；peak没有同步进程归因。
- [Linux /proc](https://docs.kernel.org/filesystems/proc.html)：smaps_rollup/PSS、RSS精度、读取竞态及进程身份边界。
- [Linux PSI](https://docs.kernel.org/accounting/psi.html)：资源停顿、累计时间与事件通知；只读官网环境不保证可注册需写入的触发器。
- [Brendan Gregg USE方法](https://www.brendangregg.com/usemethod.html)、[Flame Graphs](https://www.brendangregg.com/flamegraphs.html)：利用率/饱和/错误与热点剖析，长期平均会隐藏短时饱和。
- [Node内存统计](https://nodejs.org/api/process.html#processmemoryusage)、[事件循环观测](https://nodejs.org/api/perf_hooks.html)：RSS、堆、external、Buffer及事件循环利用/延迟。
- [Node采样堆剖析](https://nodejs.org/en/learn/diagnostics/memory/using-heap-profiler)、[heap snapshot风险](https://nodejs.org/en/learn/diagnostics/memory/using-heap-snapshot)：区分周期分配样本和高开销完整快照。
- [BCC oomkill](https://github.com/iovisor/bcc/blob/master/tools/oomkill.py)：有宿主权限时取得OOM受害者；不是官网默认可用能力。
- [论坛实践讨论](https://www.reddit.com/r/rust/comments/1ekklj0/phantom_menance_memory_leak_that_wasnt_there/)：文件缓存与泄漏混淆等调查线索，不据此判断本项目泄漏。
- 已有真实短时服务证据：[memory-container-operation](../../runs/iteration15/official-sheet-20261008/memory-container-operation/)。本侧只读其中原始resources.jsonl，确认process投影缺CPU/I/O、没有采样完成时间，不能把这次短操作当高进程数量验收。
- 主线程内存因果与修复：[memory-diagnosis-notes.md](../../runs/iteration15/official-sheet-20261008/memory-diagnosis-notes.md)。它保留历史资源缺失与真实启动链证据，本packet不改其结论或运行控制状态。

Mac产物仅WorkSSD，不commit/push、不操作主线程运行。当前单一packet足以承接调查与线性实施；有真实并行负责人或文档压力时再拆分，暂不建立额外空模板。

2026-10-08本地提交授权：用户“可以提交”。仅提交本任务及其必要采样接线，按改动块排除agent_support网关/catalog/browser、Hosted用量与归档保留、其它README改动。原始分析产物不入Git；没有部署、push或控制运行。

2026-10-08用户授权“在本地启动下，试试看效果”：在现有WSL Docker独立容器运行正常receiver和受登记文件服务约65秒，模型0；不控制其它容器、不造压力或改日志容量，不运行Factory/Braid测试。此短服务运行不声称覆盖>12进程、长时轮转或OOM。操作材料保存于/Volumes/WorkSSD/Development/factory26/runs/runtime-performance/local-20261008-153249。

用户新增授权：“好像I15在本地有个运行哦，你可以将新的I15改动接续上去来验收”。当前来源ea119b6b8a50435cbb68ae9fcda93d4d、scope e4bdfc124b444524b4b13e4533a22740、SFP7、4GiB、去ARC自费路由，现有runtime未含新容量池与serviceyield。先正常生产独立新Linux runtime，材料完成后沿Lab正常stop/save/native resume接续，不直接覆盖正在执行的材料或改应用/DB。控制可能中断在途模型/工具、丢弃未落盘进度或重复耗用；来源完整保存及停止证明不足则不派发新写者。还未控制I15。

独立服务最终实际反馈：attempt3 exit0，33次正常HTTP读取；35采样，collection中位2.436ms/最大5.387ms，采样线程CPU中位2.323ms/最大5.308ms，普通间隔中位2.063s/最大2.137s，最大4进程；PSS成功35条，CPU/I/O速率126条，真实新namespace登记32条进程观测直接关联。final保存完成，无采样错误、遗漏、OOM或capped；最终全采样含落盘81.910ms。资源证据428404字节。attempt1依赖opentelemetry缺失、attempt2操作脚本kind错误均完整保留；attempt3补已有公共依赖、修正实际launcher参数。原件local-20261008-153249/final-evidence，摘要summary.json。短服务数据不能证明>12轮转、长时轮转或高负载开销。

新Linux runtime公共生产exit0，E2E由copy_e2e_addon正常复用锁定旧addon；独立LAB_CONFIG冻结目标runtime/max_active_agents=4，未修改共享target。原ea119已正常stopped、saved=true/errors=[]。Lab新切片22a576d946f0460cb235908a74366cce已正常启动，restart命令exit0。来源data和約5.1GiB原生状态经正常执行器复制/同步；manifest和lab-run输入确认同scope/native_resume=true、Local容量4、competition=false；共享target未改。

2026-10-08 08:02Z初始真实采用验收：新容器16e148eb161a运行，observer583161/default595003/Macrelay81898由正常restart自动启动，未增加collector。Braid status实际execution_pool=max_active_agents4/reserved_slots4，active_turns4；PR8、PR9、review5/7沿原native_session_id产生新assistant与成功bash/edit结果。新producer gateway原件有12个terminal complete，deployment均ark-coding-plan-glm-5.3-flash，无ARC路径。

采样独立worker及新字段已实际采用。初始41条资源样本、最多20进程，collection中位12.787ms/最大188.500ms；最大值对应memory_growth/memory_peak_growth事件。>12进程明细9条，每条最多12PSS；窗口累计24个出生身份取得明细，末样本20个可见出生身份全部具有最近成功记录，不表示同期全覆盖。无采样错误/进程遗漏/capped/日志轮转/OOM。最新memory.current约1.466GiB、peak约2.171GiB，不能用此初始窗口推断长期稳定。

正常只读离线关联对当前生产证据exit0、2816登记身份无解析错误；1004逐样本进程观测中537匹配（299出生身份直接、238样本祖先），467unknown；匹配均有新namespace证据；954条同出生身份CPU/I/O速率观测。关联到PR8/9及review5/7。约2.154GiB样本中review5 Pi PSS515099KiB、PR8 Pi512631KiB、review7 Pi183164KiB、PR9 Pi181827KiB，均直接出生身份关联，不能与cgroup记账配平。原件、summary、native-continuation、memory-attribution-example位于runs/runtime-performance/i15-adoption；本次只读分析不向生成注入内容。

此次接续及初始采用已完成；运行继续由既有observer/default/Macrelay承接终态保存和独立评分义务。尚未验证长时轮转保全、真实OOM边界、高负载长期开销或Hosted采用；不把初始反馈称六项全部验收完成。不push、不追加提交、不运行Factory/Braid测试。
