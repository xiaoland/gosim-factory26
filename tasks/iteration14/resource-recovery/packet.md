# I14 资源释放与明确失败

当前状态（2026-10-03 20:34 CST）：用户最新要求“先在本地修正好，确保能跑起来，再上传官网运行”。四个已取得run身份的新接续均在有效Braid生成前退出：14afd为规范化request无pi，f809为误用--resume，cd42/dd3为冻结fallback所需千问变量未装配。三项明确机械缺陷已窄修，v7定义保留原checkpoint/角色/模型/历史。root正式将主线实际官方runner接续及必要入口修复交稳定runtime owner resource_gate_implementation，先在sfp7现有development-2域、官方镜像3d51899c…、2GiB取得新的native/gateway/资源证据；通过后再同来源官网接续。direct owner先准备9b/8ca并等待主线实际启动成功。9b4 v6另有snapshot POST curl56、效果unknown、无run/submission，负责人只读核对，不继续create/start。当前没有新主线Hosted派发；未达到完整OOM验收，监控仅报警，root持总体及结果采用。

用户原话：“改进资源gate，避免让它阻塞工具启动，而是让它先尝试释放资源，如果多次失败/反复触发资源限制，则fail-closed，而不是让运行继续看似 running 实则阻塞。”此指示授权必要源码、编译、材料生产及实际操作核实。用户随后纠正“五次上限是本地，不适用于官网”，并批准停止旧run和第六次官网验证，要求以OOM为关键并接续旧进度。此次覆盖此前将本地台账误用于官网、把无原位resume推导为不能外部接续的判断；[授权原话](../../../runs/iteration14/resource-recovery-20261003/resume-official/authorization-accepted.json)已保存。

run `94b8e2b76455` 已保全并于14:31:43 CST通过冻结执行器取消。完整现场显示资源拒绝持续约一小时，Issue idle但有待投递输入、PR turn仍running；两Pi Node约307/272MB RSS，file cache约1.2GB。没有证据将其归为某一进程堆泄漏；`oom_kill=0` 不证明有效推进。原件、数值与分析归[报告](../../../runs/iteration14/oom94-release-20261003/analysis/report.md)。

## 已实施行为

Braid run 共享唯一恢复协调和预算：先关闭新增准入，给既有静止Pi卸载路径一个scheduler间隔，再停止精确ownership确认的有限作业；没有适用有限作业时，对当前run cgroup有界请求最多256MiB的memory.reclaim。service及其祖先/后代、共享Portless不被自动选择；active turn不按quiescent卸载。动作回执不等于资源已经释放，内核错误和部分副作用保留。

每个episode最多三轮、总计30秒；十分钟内第四次独立压力事件fail-closed。动作/RPC/采样使用同一剩余deadline；模型重试、turn结束或Pi重启不重置run预算。这些阈值是工程起点，尚未由真实运行标定。两个不同、足够新的低压样本及可用启动余量才允许重试；idle路径先留两秒scheduler grace，再判断后续样本，不把时间经过当作物理停止证明。实际卸载/回收效果仍须运行证据确认。

Python launcher只在短admission lock内核对和登记，恢复等待位于锁外。Node异步等待启动回执，保留Pi RPC响应；每个start独立登记请求，同一deferred receipt revision只消费一次，授权后等待新的launcher决定。仅明确未执行payload可以重试，started/unknown不自动重放。五类工具/子Agent启动已接线，Bash终态promise在startup await前建立，避免短命payload丢失退出事件。

恢复耗尽、重复压力、无效采样或恢复阶段启动确认超时写run共享失败事实，沿Braid统一shutdown和原生停止证明退出；非quiescent result与入口非零形成generation_failed，不把仍存活或平台RUNNING冒称生成有效。原始失败原因与停止是否可证分开记录。技术约定归[资源说明](../../../docs/product-tdd/runtime-resources.md)。

Chrome原生曾明确报告SingletonSocket路径过长。e2e入口在Linux生成生命周期建立私有短alias指向run/work实体临时目录，TMPDIR及mcporter使用alias；Mac不建/tmp alias，全部实体仍在WorkSSD。确认daemon、workspace及collector收尾后仅删alias，停止不明则保留并记录；不搬走实体证据。其[源码编译回执](../../../runs/iteration14/resource-recovery-20261003/run5182-stall/chrome-temp-alias-fix.json)不替代真实Chromium操作验收。

## 交付和验证

Mac cargo check、Linux cargo zigbuild、Python/Node静态编译均返回0，五类patched caller完成TypeScript emit；完整类型检查未通过验收，保留包存在既有peer/declaration drift，emit使用noCheck。未运行Factory/Braid/SVC测试、探针、smoke或新模型；没有commit/push。Linux Braid SHA256为`3345d50d1959a2aa5f16f8177e4c1c15a97df94779e53184c54039517c1a73cd`。

[完整runtime差异](../../../runs/iteration14/resource-recovery-20261003/implementation/runtime-tree-diff.json)确认父44,607文件零遗漏，仅八个授权文件变化；Python/npm锁和其它父负载保留。首次子集runtime所冻包缺Python/Chromium实体，已[明确拒绝采用](../../../runs/iteration14/resource-recovery-20261003/candidate/adoption-blocked.json)，不覆盖其冻结身份。派生完整性要求已归[制品合同](../../../lab/exp/artifacts.md)。

完整候选已由标准package producer与Lab build冻结于`runs/iteration14/resource-recovery-20261003/candidate-complete/`，883,444,695bytes、私有0600；ZIP SHA256为`169d32f6a3101c9659a6c3ea6b722f07221ee57cb7be22c5097ed793f136aaa2`。Braid来源/包字节、受管模块和实际caller、必要Python/Chromium、依赖锁均已核对。[冻结回执](../../../runs/iteration14/resource-recovery-20261003/candidate-complete/preparation-completion.json)和[root采用回执](../../../runs/iteration14/resource-recovery-20261003/adoption-receipt.json)保留身份；源码细节和编译归[实现回执](../../../runs/iteration14/resource-recovery-20261003/implementation/resource-gate-source-receipt.json)。

已授权下一步：保全最近可确认完整Git/Braid/native恢复点，沿冻结执行器停止run5182，取得配对终态和槽释放，生成公共checkpoint与显式机械补丁兼容prepared，再只启动一次同Flash/GitHub/self_funded、官网2GiB接续。无官网原位resume不等于不能external export/checkpoint/prepare接续；不静默fresh start。验收以实际释放/回落、新采样和工具恢复，或有界失败、停止回执及非零终态为首要；完整官网结果沿原生成目标取得。数据不足保持partial并明确缺口，不伪造完整检查点。

旧run `5182d1d25e9d`已独立GET确认16:54:38 CST取消，无评分、未进入评测。旧manifest绑定被新producer拒绝是当前具体恢复接入缺陷，不据此认定旧数据不可恢复；同一点Git/Braid/native的完整性尚待公共producer读回。停止及原始错误归[处置记录](../../../runs/iteration14/resource-recovery-20261003/resume-official/recovery-disposition.json)。

用户新增要求对`9b4cc578b462`、`8ca071551fd4`取消并用新版接续。最近完整workspace源分别约81.8MB、182.6MB，最后原生活动为14:00:43、14:24:58；17:07–17:08保存观察仍RUNNING且无resource_wait_groups，不能直接归因gate。每个同题各授权一次接续，原模型、角色及self_funded配方保持；用户随后授权应用Rust Gateway，接续仅更换传输设施；不控制stage3 `db6d8361841b`。授权、处置与后续完整性证据归[直连接续](../../../runs/iteration14/resource-recovery-20261003/direct-continuations/authorization-accepted.json)。

监控只报警，执行负责人修复；当前身份、预期取消、root处置及新接续绑定以monitor-contract为准。15分钟heartbeat已删除旧run活动身份的硬编码，仅消费契约与既有有界摘要。创建受理与实际原生生成分开记录，不冒称OOM修复已通过实际验收。

Mac项目产物、cache/temp/控制证据全部在WorkSSD；WSL/sfp7及官网可保留远端执行数据。其余owner修改保留。

用户最新要求删除better-sqlite3等应用预装/预编译材料，参赛Agent自行安装配置；原运行中已经生成的应用依赖与数据库保留。瘦runtime已移除预编译包和环境注入，原父材料不变。用户随后要求应用已完成的sources/model-proxy；[I14接入低内存模型代理](codex://threads/01a1012f-81f9-7150-927c-3de9259ada24)独立持有gateway接线和打包闭包，原模型/角色保持，接续transport明确记录为Rustproxy。因sub-agent工具已返回thread limit，按用户先前允许容量不足时创建会话的授权建立该会话；主线通过保存回执与wait_threads采用，不重复实现。429进一步追查已按用户指示停止。

5182三个Git缺口已由advisor核实为导出后的clone元数据缺失：空application精确对应空seed5cae616，Issue6文件对应d3ea8ff，PR53跟踪文件对应cb5dd68，全部对象和已发布祖先在origin。可仅重建副本.git执行结构，不checkout、不创建新commit，不改业务文件、DB或native；保留原index/reflog未恢复的限制。prepared核验恢复后的真实HEAD/index与保全文件，将当前执行缺口与历史元数据限制分开，原checkpoint不追认完整。

基础设施合并已完成，main为`5e96bdd6`，主区在途修改恢复，独立worktree已清理。兼容判断按旧5182实际冻结包716e与新3345的确切差异，不将cache父c88的八文件差异当作5182升级证明；advisor已交明确runtime兼容和prepared入口接入缺口。新public assembly实际通过support/runtime_resources.py接入gate，并包含state_writer/execution_context及Lab依赖闭包；旧candidate-complete保持原身份，恢复owner消费[合并后assembly回执](../../../runs/iteration14/resource-recovery-20261003/implementation/post-merge-public-assembly-receipt.json)重新生产support，不把新helper盲拷到缺依赖的runtime根目录。

2026-10-03 当前接续入口：resource gate owner持有三份新版定义材料、主线实际官方runner验证和必要公共入口修复；direct owner独占9b4/8ca；root持总体、授权、monitor绑定与结果采用。旧Git clone缺口按真实origin提交重建元数据，原件仍partial；8ca遗失未发布1e0ee09对象，采用已保留ff4基底+全部未提交现场，并经既有comment明确通知，不伪造HEAD。三份新运行均显式消费Rustproxy、原模型角色、无业务native预打包材料。Rust接入会话01a1012f-81f9-7150-927c-3de9259ada24已完成Linux Chat/SSE/tool实际200和最大采样RSS5.75MiB；root采用其binary/闭包，不将此当作完整OOM验收。新版投影沿公共delivery/bootstrap形成snapshot-copy assembly，原logical state/native路径保持，执行--execute-prepared。最新实际派发身份与证据位于本文当前状态和monitor-contract，旧来源仍保留原身份。

实际准备与派发反馈：精确兼容合同为schema2，producer现沿相同SHA/源/协议/成员约束消费；package backend为pi、variant由capabilities.variants声明；host_lab的uv freeze环境名错误已修；Hosted控制证据不在Mac装配Linux逻辑链接。未派发的失败原件保留在resume-official/prepared-final-v1、experiment与experiment-v2；没有据此新增官网生成。5182正式包[回执](../../../runs/iteration14/resource-recovery-20261003/resume-official/projected-agent-receipt.json)为985df8…、1055578833bytes，gateway仍70c51…、Braid3345…；终态消费者复用direct owner程序，只读冻结projection，不新采集。

官网14afd实际入口反馈与修复归[错误保全](../../../runs/iteration14/resource-recovery-20261003/resume-official/known-entry-failure-repair.json)。该失败发生于网关启动后、execute_braid前；真实最后样本memory.max=2GiB、current约1.47GiB，file约1.32GiB、anon约95MiB，不能用此启动阶段样本证明gate恢复或完整OOM验收。v5 helper为40d545…，三份immutable定义[索引](../../../runs/iteration14/resource-recovery-20261003/implementation/legacy-staging-index-v5.json)保留原角色、模型、runtime及direct声明。新配方删除900s collector override，采用已有adapter采集间隔，Luna消费仍15分钟；没有新增采集循环或今晚自动迭代授权。

2026-10-07 资源边界接线收尾：本轮任务文件为`scripts/runtime_resources.py`、`lab/arc_bench/harness_services.py`与`docs/product-tdd/runtime-resources.md`；Braid仅涉及`src/local.rs`去除永久`waiting_for_resources`分支、`src/group/worker.rs`不再以资源等待遮蔽终态错误、`src/provider/session.rs`将资源拒绝映射为保留原消息的`resource_exhausted`失败。其余Braid格式化、生命周期及store改动均为既有dirty worktree，不纳入本轮边界，不stage、不提交。资源监督器已改为直接登记公共入口的`subprocess.Popen`，补救后以current/max与补救窗口新增event区分recovered和不可逆失败；入口已补early-failure登记，避免监督线程先失败后新child继续运行。实际编译反馈：在`/Volumes/WorkSSD/Development/factory26`执行`cargo check --manifest-path sources/braid/Cargo.toml`返回0，仅有既有dead-code/unused警告；未运行Factory/Braid测试、探针、smoke或新模型实验，未控制610daf。
