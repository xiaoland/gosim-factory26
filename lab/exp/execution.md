# 执行、恢复与状态

本文只描述旧 lab.exp 的 experiment/attempt 合同。执行命令使用所属运行冻结的 source 与 runtime；当前 run 级操作见 [Lab](../README.md)。

新实验只使用 `factory26.exp.experiment` schema 3，执行合同为 `explicit-request-v1`。Controller 接受显式的构建、执行和控制请求；每个执行请求选择一个 job，最多绑定一个 attempt。定义中的 job 列表是可选执行计划，不会触发自动派发、下游启动或自动重试。Local/Docker 的独立 runner 持有单个 attempt 的入口、资源限额、原始采集和保全。托管 adapter 持有平台身份与 pending 写入。旧 plan/run/operation writer 已从工作树退役，历史材料通过 `history` 或专用只读 reader 消费；不翻译成新执行。

`start EXP --job JOB --request-id REQUEST` 在冻结预算和当前容量内受理一个 attempt。相同请求与参数重入读取或接续原效果；改变参数必须使用新请求。容量不足返回阻塞，不排队。`retry EXP ATTEMPT --request-id REQUEST` 明确创建并派发一个新 attempt，原执行须已确认终态。未知效果不能按失败重跑。`wait EXP ATTEMPT --timeout 60` 只等待选定 attempt。

下游输入通过 `start --inputs FILE` 明确选择，例如 `{ "application": { "experiment": "/absolute/source-run", "attempt_id": "attempt-ID", "output": "application" } }`。也可给出 `{reference, store, member, location?}`。选择冻结为输入关系，不随后来重试改绑。

`control EXP ATTEMPT seal --request-id REQUEST` 接续原 attempt 的封口/标准归档；`export` 单独运输，由 `--parameters FILE` 明确指定 `assets`（每项 reference、member、location）、target_store 与 consumer。执行退出、封口、遥测、输运和评分分别报告。恢复默认只准备，`recover --execute` 才显式启动一个派生 attempt；continue/query/abort 使用相同 request-id，未知物理效果保留原回执。

## 查询保存事实

`status EXPERIMENT [EXPERIMENT ...]` 和 `monitor EXPERIMENT [EXPERIMENT ...]` 使用同一 experiment projection。默认输出供人和 Agent 阅读的文本，展示当前 job/attempt/平台身份、入口与执行事实、影响下一动作的具体错误或 unknown/partial、来源时间及下一合法操作；`--details` 展开完整结构化资源诊断，与 `--json` 互斥。输出模式由参数决定，不根据 TTY 改变；`--json` 保留原有 attempts/execution/model_facts，并增加 targets/stages/facts/inputs/outputs/history/next_actions。job 可显式声明 `target: {"case": "github", "variant": "baseline"}`，两项均须为非空字符串。未声明 target 的评价阶段可沿唯一的 from_job 关系继承生成目标；其它 job 以原 job ID 分组，不解析命名猜比较条件。未派发阶段也会显示，未请求阶段列出所需的 producer job/output；保存的产物不会自动绑定新执行。已经分配的评价 attempt 显示其实际冻结的输入，后来的生成 retry 不会使它改绑。

每项事实保留 producer 原件和观察时点。Main 的 exit 0、执行终态、archive preserved、export preserved、Harness 声明 complete、collector sealed 和平台 verdict 分别成立；非零入口结果不会因 controller completed 变成成功，unknown 也不会因存在归档变成完整 prepared。发布制品的状态读取本地 manifest 摘要或生产者保存的封口位置事实，不在每次 status 重算全部 payload；消费端仍核验实际字节及语义。平台状态取对应 `/runs/RUN_ID` 的保存 GET 原件，读取 status 或导出 logs 的时间不能代替平台新鲜度。Braid/Console 缺少绑定 attempt 的公开接入观察时明确显示 unknown；不读取其私有 SQL，不从 collector 存活或 Console 配置推断 connected。

Next actions 来自 controller 的公开操作判断，说明可调用命令及需重新满足的条件；保存状态不能授予启动许可。效果 unknown/pending、身份冲突和入口失败先检查原错，不能自动 retry。终态保全或 Docker 输运缺失时可给出同一 attempt 的 `control ... seal`，执行时重新核对 incarnation 和物理终态。Prepared 的停止原件必须绑定同一来源；匹配旧原件仍要求 launch 重新观察。启动还须沿用真实授权和 deployment，并核验冻结 runtime、预算及资源。可以将多个现有实验目录列入 `factory26.exp.index`、schema_version=1 的 experiments 路径列表，以 `status INDEX_JSON` 一次读取；相对路径从 index 所在目录解析。这只是查询索引，不改写已有实验或替代运行关系。

Provider 已保存的会话生命周期、连续观察、资源等待及 native 证据覆盖范围也进入 status/monitor 投影。只消费当前 attempt 引用且身份一致的原件，不重新采集或分类；外层 Local supervisor 与实际 Docker child 的状态分别显示，外层 running 不证明子容器或模型已经开始。

受管 state 的已接受动作原回执也进入统一视图，保留 holder、generation、writer、capture 和 snapshot 的分别身份。多域 holder 分别显示；保存的动作回执不等于当前远端观察，status 不为此启动新的查询或采集。

托管监控只有一个采集 owner：受理的单个 attempt 启动独立冻结 observer 调用 hosted adapter。adapter 自己持久保存 next_observation_at，前十分钟每三分钟、此后每八分钟查询并保留平台原件；终态导出也由同一 adapter 完成。不要把新 run 接入旧 hosted_monitor、伪造 legacy journal 或启动第二 collector。Luna 每十分钟使用该实验的 controller_runtime 与 controller-source 读取 `python3 -m lab.exp monitor EXPERIMENT --json`（历史实验仍使用原 source） 消费保存记录；这是 status 的只读入口，读取本地保存的身份与观察，不请求平台。

监控消费分别看 observer 生命周期、attempt 的 pending/remote_status/具体错误、archive、平台结果和原件时间。provider 新鲜度取该 attempt/platform 中 `/runs/RUN_ID` 成功观察的时间，不能使用本次查询 read_at 或 token 增长代替；observer 失联时报告缺口，不接管采集或重跑入口。重复状态保持安静，终态、具体故障、身份变化或需要用户动作才通知。原 collector 对旧来源的采集权限不会自动转移给新 run；新 run 可以先启动，Luna 订阅接收回执独立成立。真实接续消费合同见 `runs/experiment-dx-review/real-handoff-20261002/monitor-consumer-contract.json`。

## 装配与域控制

Fresh、prepared 和 SDK child 使用共同 assembly，显式绑定本域定义根、可写 state、实际 namespace 和入口。公共 bootstrap 在实际运行域提供持续资源采样与 telemetry，并从同一执行上下文派生入口变量；父域的服务路径和凭据值不成为公开子域事实。旧冻结执行器仍沿自己的合同。

新 Docker 执行使用运行宿主上的 detached runner，负载容器只读挂载域资产，拥有独立的可写执行路径。短时 store owner 执行受限发布/输运，工作负载不能访问 owner 代码、请求和 RW 发布卷。Runner host/process 出生身份与 daemon/container 出生身份分开；controller 退出不撤销 runner，运行宿主失联也不证明 Docker 负载已停止。该隔离依赖 Linux local-volume 及支持 volume-subpath 的 Docker API 1.45 或更高版本，不自动回落到共享 RW。

受管 create/start/stop/pause/resume 先保存版本化意图，再执行和读回物理效果。超时留下 pending；重入原请求查询效果，不重发 create/start。终态实例禁止再次 start，新执行重新准入。只读 query 使用已核验 Mountpoint 的 bind，不按卷名称打开并意外创建缺失卷；正常使用期间不删除或重建域资产根。Query、输运和构建不是另一个生成调度系统，但各自必须有界并发、超时、清理和实际资源约束。

Docker 离线 job 显式设置 backend.network="none"，create 记录在 attempt/docker-create-intent.json 并传入 `--network none`；资源读回核对 HostConfig.NetworkMode 及 NetworkSettings.Networks，不仅根据 prepare-only 名称推断断网。未声明 network 的生成 job 保持 Docker 默认联网。首版不接受其它显式 network 值。

独立题目的自费练习可在 backend 冻结 `parallel_distinct_tasks=true`。此时新 snapshot 不因最新 snapshot 中其它已确认 task 的活动运行而阻塞；相同 task、未知 task 身份和正式比赛模式仍沿用门控。snapshot/create/start 继续在现有 competition 锁内依次执行，创建时仍核实 snapshot 是最新身份，不扩大既有冻结实验的并行权限。


Console accessor 需要域内 `access_resource_id`，创建和启动属于同一权威，其写入许可与 checkpoint 捕获共同排序。新登记不能追认旧未覆盖的活动 accessor；停止后不可重启同一出生实例，新的访问实例需重新创建及登记。当前服务的部署仍由其 owner 安排。

## 准入与来源停止

Docker endpoint、不可变 image_id、共享 slots 和 daemon 派生 admission_volume 显式冻结。接管还需 authority_handoff：全部旧派发者已停止、旧预留为空、在途窗口关闭的独立原件。`authority-handoff --endpoint JSON --writer OWNER_JSON --registry OLD_REGISTRY --authorization SCOPE --output NEW_JSON` 只读核验已明确列全的退役范围，不停止 owner 或释放槽。paused/alive 不等于退役；现有旧现场不自动迁移。

首次使用实际从未建立 Factory 域的 daemon，使用独立 `authority-handoff --mode first-use --endpoint JSON --scope SCOPE_JSON --authorization NEW_DOMAIN_SCOPE --output NEW_JSON`，不传 `--registry`。scope 的 kind 为 `factory26.exp.authority-first-use-scope`、schema_version=1，必需 daemon_id、authorization、allow_new_domain=true、no_other_legacy_domains=true、launch_windows=closed、writer_scope、registry_scope、writer_sources、local_registry_paths、registry_absence 和 evidence。writer_sources 必须与 `--writer` 原件列表完全一致，没有旧 writer 时显式写空列表；local_registry_paths 同样明确枚举或写空列表，producer 对这些本机路径实际 lstat。registry_absence 的每项为 `{host, path, source}`，source 引用真实宿主 readback：hostname、info 的成功 Docker ID 读回、registries 中该 path 的 exists=false；也支持外层 `{exit_code: 0, stdout: JSON字符串}` 原件。evidence 引用已保存的 writer/记录扫描原件。输出区别保存 reservations=absent 和 declared-first-use-scope，不伪造 released 或空旧 registry。

首次域的覆盖声明由获授权负责人给出；有限扫描、默认路径不存在和空 `docker ps` 都不能自行推出没有未知自定义域。producer 另外实时读取目标 daemon 的全部容器/卷，只扫描 Factory label/name 并保留其它资源；发现旧 Factory 资源则拒绝 first-use。此声明不接管其它 daemon，也不停止或释放任何旧域资源。

旧官网来源使用 `import-source-stop --birth ORIGINAL_GET --status TERMINAL_GET --authorization SCOPE --identity-output NEW_IDENTITY --output NEW_STOP`；可用 `--cancel-evidence ORIGINAL` 保存唯一取消请求来源，但请求受理本身不能满足门控。两个独立 GET 原件的 run/submission/competition/task/created_at/started_at 必须相同，终态 GET 还须有 finished_at。来源记录为 `factory26.exp.legacy-source`，使用 source_id、execution_instance 和 backend_identity，**没有新 attempt_id**。Harness producer 必须明确消费此来源联合类型；不能把它改名成新 attempt。Prepared 继续保留整个 source_identity，停止制品独立发布；新 launch 使用私有 deployment.cookie_file 重新 GET 同一个原 run，核对出生身份和物理终态，缺身份、凭据或当前观察时阻塞。该接口只读、导入及 GET，不进行 cancel/start/resume；跨平台来源尚不支持。

真实 hosted 来源使用 `python3 -m lab.exp import-source-stop --experiment EXPERIMENT --attempt ATTEMPT --birth BIRTH_GET_JSON --status TERMINAL_GET_JSON --cancel-evidence CANCEL_JSON --authorization "已获授权的恢复范围" --identity-output NEW_IDENTITY_JSON --output NEW_STOP_JSON`。`--experiment` 与 `--attempt` 必须成对提供；导入核对冻结合同、实际 attempt、execution 和派发绑定，以及来源与独立终态 GET 的 run、submission、competition、task、创建及启动时间。取消响应只作为原件保留，独立 GET 必须确认终态和结束时间。输出保留真实 attempt 和 execution incarnation，不伪装成 legacy 来源；两个输出均须为新文件。导入不执行停止，也不授予启动许可。恢复启动仍须显式提供 deployment 的私有 `cookie_file`，通过独立 GET 确认同一来源确已停止。

旧 Docker 来源使用 `python3 -m lab.exp import-docker-source-stop --birth SOURCE_IDENTITY_JSON --status SOURCE_STOP_JSON --writers WRITER_RETIREMENT_JSON --authorization "已获授权的恢复范围" --identity-output NEW_IDENTITY_JSON --output NEW_STOP_JSON`。来源保留真实旧 run ID，以 daemon、完整 container ID、创建/启动时间、image 和 owner labels 绑定 `legacy-docker` execution，不补造新 attempt ID。导入会实时读回原 daemon 的同一容器及全部来源卷使用者，要求它们已退出、Pid 为零且没有 paused/restarting 状态；旧写入与重启进程也须关闭。Darwin 的僵尸进程保留原 unknown 与新 `ps` Z 观察，不为回收僵尸解除共享 dispatcher 的暂停。启动同样重验出生身份、卷使用者和 writer；消失、连接失败、重启或新增写入入口均阻塞，不清退其它来源或整个 daemon。

## 检查点与显式恢复操作

公共受管入口为 `python3 -m lab.exp checkpoint RUN ATTEMPT --directory CHECKPOINT --request-id REQUEST`。它在原域权威上阻止新增写者、关闭已登记的实际执行及访问写者，并取得独立 capture 许可；不要求使用者制作 closure JSON。没有受管覆盖的历史运行仍需沿其冻结合同取证，不能从父进程退出推断完整关闭。外层 Local 包含 SDK child 时，公共入口选择已登记、终态接收已验证且具有真实 state mapping 的 child；唯一来源可直接采用，多个来源须用 `--source-resource AUTHORITY_RESOURCE_ID` 明确选择。来源保留 child 的实际出生身份与外层关联，不用外层 Local 身份代替。入口非零退出不自动否定检查点，完整性仍由 Harness producer 判定；该路径不提供官方 SDK resume。

默认恢复入口为 `python3 -m lab.exp recover CHECKPOINT --intent RECOVERY_INTENT --environment PROFILE --directory NEW_RUN --job JOB --request-id REQUEST`。Intent 在普通实验字段之外声明 `recovery: {production: NAME, target: TARGET_LAYOUT, repair: REPAIR}`，相关 variant 的 prepared 使用 `{from_production: NAME}`。缺省 `mode` 为 `snapshot-copy`；显式 `mode: "domain-state"` 和稳定 `request_id` 选择同域受管恢复。入口冻结原 checkpoint 身份、修复输入、生产依赖及派生关系，准备新 run，不启动模型。SOURCE 必须是明确 checkpoint，不从含混 run/archive 自动猜。

恢复是一次显式操作，缺省只准备选定 job。`--execute` 才请求派生 attempt 的一次入口；`--action query` 只读原操作回执，`--action continue` 以原 request 接续，`--action abort` 在确认本请求的 helper、新执行预约和 writer 责任已关闭后结束准备。取消保留原快照、当前状态字节、修复 ledger 和 generation，不回滚也不把写权交还旧入口。已启动的派生执行须针对其 exact attempt 停止，不能用取消准备代替。部分修复取消后的 holder 是 `repair-aborted`，不能当作可重开原快照的 `closed`；通常从保留的 immutable snapshot 新建恢复。

快照、定义换版、repair lease 和 writer 交接的完整合同见[制品与恢复证据](artifacts.md#检查点与准备)。操作者先按[冻结恢复门控](../../docs/deployment/history/recovery.md#当前-checkpointprepare-与停止门控)确认来源与授权；旧协议见[冻结恢复记录](../../docs/deployment/history/recovery.md)。

`status`、`monitor`、`wait` 默认文本；`--json` 是显式程序合同，不是默认诊断入口。查询命令成功读到 failed/cancelled/running attempt，与查询失败分别表达；wait 的超时不停止执行或授予 retry。状态结果写 stdout，命令错误写 stderr。诊断沿返回的精确原件路径展开，不递归扫描运行目录，也不默认读取 native rollout。
