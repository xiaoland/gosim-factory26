# 执行、状态与输运职责调查

本次是用户扩大设施职责梳理后的只读调查和设计，不是实现或运行验收。主区为 `/Volumes/WorkSSD/Development/factory26`，多人正在修改；交付基线为本 worktree HEAD `d4ac01ddeefe3864544ca31e523bbba13ffb04e3`。以下主区结论针对本次读到的工作区文件，不能当作不可变提交。没有编译、测试、模型、Docker、网络、资源控制或清理操作。

已读取主区 `runs/developer-experience/post-infrastructure-acceptance-20261003/report.md`。其未关闭项包括完整 runtime/Harness 打包、首次入口与模型受理、合法 checkpoint 的同域恢复实操，以及整体 session 成本对照；源码边界和已保存原件的局部操作通过，不能替代这些验收。同任务、同模型、同等完成质量与所有参与 agent 的 token 汇总，是本轮建议沿用的成本验收口径，不是本调查已取得的对照结果。职责拆分的设计也不自动证明总成本下降。

## 核心判断

执行终态、工作进度的内容保全、具备关闭写者证明的 checkpoint、资产输运、完整证据归档是五种不同事实。它们可以在同一有限 attempt 闭环内自动接续，但失败、容量和重入身份必须分别记账。当前问题并非所有事情共用一个 controller 文件，而是下游保全/输运失败能延长执行容量、改变执行观察，或挡住本应优先生效的 stop。建议保持现有固定请求和域 authority，不引入新的中心服务或万能任务系统。

## 已核实调用链与迁移建议

| 位置与调用链 | 实际耦合与影响 | 应删、移或保留 |
| --- | --- | --- |
| 主区 `lab/exp/controller.py:933` control → `:947` executor.observe(live=True) → 主区 `lab/exp/hosted.py:528` observe → `:546` `_workspace_observation` → `:471` 完整 workspace ZIP download/collect。之后才进入 hosted.control `:564` 并 POST cancel `:589`。 | stop 的前置身份观察包含工作进度取证、大包下载和解析，且 held hosted.lock 覆盖整个采集。下载失败在观察中被保存，耗时仍先于控制；已有身份也不能避开该重工作。 | 控制仅消费已有 incarnation 与固定远端 identity，必要时做有界身份/状态 GET 或 pending reconcile；工作区采集移到原监控/保全 owner。保留 run identity 核对、原 HTTP 响应、pending 不重 POST、原采样频率和平台只能整包取得的真实限制。不能用少读 workspace 牺牲 provider liveness。 |
| 交付 `lab/exp/controller.py:1081` control → `:1094` live observe；交付 hosted.observe `:356` 目前仅 reconcile + run GET。主区 hosted 已新增 workspace 监控，交付没有该功能。 | 相同 ABI `observe(live=True)` 在两份实现的成本和副作用不同，交付直接覆盖主区会丢掉新监控；主区直接合入又会把重采集重新带进 stop。 | 保留主区已实现的监控证据能力，拆成身份观察与进度采集两个有界动作。不要全选旧实现或删除监控来取得快 stop。 |
| 交付 `lab/exp/controller.py:735` work，`:754` live observe，`:757` 托管终态自动 export；同一 try 内异常变 `phase='unknown'`。`:782–784` retry 要等 archive，并把 archive pending 纳入 max_parallel；常规 active 集合 `:798` 仅按 phase 计算，与 retry 口径不同；`:856` 实验完成条件另等 archive pending。主区同类代码在 `:635` 起。 | 证据归档异常可能使调度看到执行 unknown；retry 并发的定义与归档等待混在一起；常规新 job 并非统一被 archive pending 计入，因此需修的是两种派发口径和独立收尾预算，而不能概称所有终态 attempt 都占 max_parallel。 | 调度分别消费 execution、publication/evidence 和 transport 回执。执行额度依实际执行/未知创建释放，发布所需输入可单独等 named output finalized；归档按自身有界预算接续，不替代运行是否 active。完整归档要求仍可作为实验交付完成条件，但不得借此占执行槽。 |
| 交付 `lab/exp/runner.py:1089` docker_worker → `:1146` physical terminal → writer-close → payload-terminal → `:1157` `_seal_docker_terminal` → `:1158` finish_docker。`:1066` terminal capture → RO helper → collect_named_outputs。交付 `backends.py:581` collect 在域内 `_seal_outputs` 与 `_archive`；`:832` finish_docker 才释放执行和 store helper。 | 真实容器已退出，归档/collector/发布失败仍可能跳过 finish；异常分支保存 archive failed，但仍需人工 export 才推进。执行额度和 RW store owner 的释放被绑在保全成功之后。 | 物理 writer 停止/关闭后独立持久 execution terminal 与 admission release；保留 holder、state volume、artifact holds，不随 slot release 删除。捕获通过独立 RO helper继续，保全失败保存 partial 和请求原件。收尾 owner 对已取得资源在成功/失败路径都完成其有限关闭；unknown 资源保持占位，不能 finally 无条件释放。 |
| 交付 `runner.py:185` control 分派 `repair-ready`、export、stop/pause/resume；`:225` export 调 `_seal_docker_terminal` 后 `backends.export_terminal_assets`，Local 调 `_seal_local_terminal` 后 `_archive`。主区 export `:222` 路径还包含 capture、export_payload、_archive、finish_docker。 | 名为 export 的动作同时补封口、归档、跨域输运和资源生命周期。同一 error/unknown 难以说明哪个副作用已完成。 | 保留兼容 CLI 的一个有限编排入口，但内部每步用现有独立请求/回执：确认终态、发布内容、归档证据、按 consumer 请求运输。重入不得因输运丢响应再次封口/重跑入口。普通本域消费无需 export 到控制宿主。 |
| 交付 `backends.py:845` export_terminal_assets 汇集 named outputs、archive、workspace 和定义引用，`:883` export_named 用 RO helper输运。 | 交付已有资产级位置/retain合同，优于旧 export_payload 全量安装到宿主；但 export 默认集合仍可能运输消费者不用的全部定义和证据。 | 保留该正确边界，把输运请求明确到 reference/member、目标域和 consumer hold；发布位置与消费保留独立记账。不恢复“导出全部现场后才能消费”的旧路径。完整证据导出可以作为显式选择，不能暗中附加每次 named output 消费。 |
| 交付 `controller.py:471` recover，`:490` 起 domain-state 模式读取 managed-source、reopen capture、repair-begin、`:526` prepare_in_domain、repair-item/complete，之后 compile/build 新 run；`environment.py:138–179` generic prepare producer也能按 state_binding 执行域内修复。`submission/exp_checkpoint.py:733` prepare 实际改派生状态和 native 输入。 | recover 不启动模型，但不是纯离线转换；它保持可写 repair helper/CAS capture，generic material production也可能跨入旧现场副作用。失败或新 run build 未完成会留 repairing/repaired capture。 | 把 recovery 决策/配方验证与显式 domain repair operation 分开，操作回执保留 generation、request、类别、实际结果；compile 只能声明/核对，不借 generic producer 名字隐式修旧状态。不可用 TTL自动撤销 unknown writer。公开 query/resume/abort 的边界由原 operation owner承担；跨域 snapshot-copy 不需长占 mutable repair lease。 |
| 交付 `controller.py:1290` checkpoint，以及 `:1145` SDK dispatcher，调用 state → close writers → snapshot → schema4 small metadata；`state.py:14` reducer在原 registry 锁内执行业务状态，`admission.py:397` 固定物理 action，`backends.py:247` 接受后执行/查询。 | controller承担跨组件编排合理，但 acquisition 证明不能由编排者补写文本代替发布时事实。当前已有真正的普通内容/恢复捕获区分。 | 保留主线：ordinary terminal-content-copy不可升为 checkpoint；schema4核 publication 原 token/request/closure；已有同代 managed snapshot 可复用，不重封；未知 Local detached覆盖具体 blocked。迁移不把“易用”解释为弱化证明或把 archive 当 checkpoint。 |
| 交付 `backends.py:1090` capture_helper、`:1178` prepare_in_domain、`:1235` snapshot-copy、`:1357` abort_preentry；SDK `docker_workspace.py:508` 起组件输运及 `:669` child holder。 | helper是执行/copy/accessor角色的资源，不是各起一套 authority。需要不同 RO/RW/namespace 的资源不应机械合并。问题在 owner、预期生命周期、scope、关闭失响应和多次输运是否明确。 | 保留同 daemon registry、精确 birth、pending、writer/capture职责和真实 role。copy helper不占 execution slots，但仍受自身资源预算/动作回执监管；不按失联或名称前缀“收垃圾”。取消纯预约与 exact never-started discard 已有正确机制，复用，不另写 cleanup脚本。 |
| 交付 Console `docker_runtime.py:229` access_control、`:239` 每 CLI live_access → controller `:1455` access_control → authority和 holder query；service `:259`、server `:114` 接该判断。 | 每次 query 保证 handoff 后不能读旧 live state，是必要责任；query 当前亦可能执行 consumer-register，是接入与读取的语义混合。 | 首次显式登记 consumer，之后 query只取当前许可/绑定；每次写入 CLI仍需实际 holder gate，不能永久缓存“已登记/已验证”。旧 reader必须转 immutable snapshot，Local缺适配器保持明示限制。轻量 control_manifest边界保留，不能重新扫描大 runtime/所有 inputs 后才允许 stop/query。 |

交付 `admission.py:333–358` 的权威读写自身用短生命周期 query container，四个稳定 daemon channel 名称限制同时占用；真正权威仍是同一个 volume registry。这个实现不能被误报为“四套独立authority”。它会产生每次动作的容器启动/关闭成本及 uncertain channel 阻塞，应记录实际渠道和耗时后判断是否需要已有通道的生命周期复用；不能为了少 helper 绕过锁、pending与精确域身份，也不据此建立常驻中心服务。

## 同一次执行内的失败闭环

设施就绪服务失败、确定未创建、已创建但未启动、模型/应用失败、物理停止未知、发布失败和输运失败必须分开。就绪服务可在原 live supervisor、entry尚未请求和原剩余预算内有限 repair-ready；这不是为新模型尝试追加预算。新的执行仍须显式 retry 配方/预算，pending start 不允许第二入口。

交付 `runner.py:1162–1170` preentry异常已有 abort_preentry，只在 entry-intent不存在时进入，保留主要错误与 abort错误。`backends.py:1357` 区分纯预约取消、exact created-neverstarted discard、pending unknown。该分界应保留并采用到其它同类公共 owner。不能以“failed”文本或 helper关闭作为 execution已释放的证明。运行后失败则独立完成实际 writer关闭和已取得资源生命周期，再做证据保全；保全失败不重运行模型，也不篡改原 exit code。

## 3074b476 add_note 回归

已只读核对提交 `3074b476` 的 controller.diff：主区 recover 在 `harness-manifest.json` 的 FileNotFoundError 上保留原异常并加 note，明确 SOURCE 必须为显式 Harness checkpoint，平台 ZIP/partial不能直接恢复。主区现 `controller.py:462–468` 仍有该行为。交付 `d4ac01dd` 的 `controller.py:484` 又变成裸 `read`，确有回归。

它不是 stop下载 ZIP 的同一执行根因。直接原因是隔离分支扩展整个 recover流程时未保留主线已经加上的输入边界诊断。它暴露同一职责弱点：恢复 source识别与模式编排黏在大函数中，公共入口的最小合同容易随另一生命周期扩展消失。最小设计是保留原 FileNotFoundError及 note，把共同的 checkpoint source识别作为恢复操作前的明确有界步骤；不需要额外状态服务，也不需要重新运行已知无意义输入证明这项确定差异。

## 正确边界的保留与验收

以下是设计后的实际操作验收安排，不是已完成验收，也不新增设施测试或fixture。

1. 在下一次已经获得实验许可的真实 run中，记录 stop请求、身份校验、控制受理和物理关闭的分段时间。监控采集原频率继续；同一时刻下载/解析失败不得挡控制。不能为调查自行取消在跑实验。
2. 使用真实终态及既有失败原件，分别读 execution终态、admission release、named output位置、保全/输运请求。内容保全失败不应占 execution slot；资源unknown仍占位。原 state、volume和retention在执行release后继续存在。
3. 以真实发布内容分别验证普通terminal输出消费和managed checkpoint恢复。普通封口的未知detached gap不得等同应用交付失败，也不能被后贴closure升级。完整checkpoint须核其发布时原 proof与真实停止实例。
4. 同域 consumer只取得位置/member+retain并装配；跨域只复制请求的资产/定义闭包；平台仍完整ZIP，无平台能力依据不得宣称网络减少。记录真实请求数、传输字节、耗时、helper role/数量/关闭结果，判断保全之外是否出现重复全量输运。
5. 使用实际已失败且有mapping的SDK child生成metadata checkpoint，检查child physical identity、outer relation、source-member、回执及失败原件独立保留；不把公共Harness prepared称为原SDK resume。
6. 总成本验收沿主报告口径：同任务/模型/完成质量，所有agent的total/cached/非缓存input/output，用户请求到同等可行动结论墙钟，包含重试和无效读取。模块数、静态编译、命令输出字节或并行agent时长之和不能代替它。
