# 实验基础设施

新实验只使用 `factory26.exp.experiment` schema 2。Controller 组织构建、派发、控制、监控和分析；Local/Docker 的独立 runner 持有单个 attempt 的入口、资源限额、原始采集和保全。托管 adapter 持有平台身份与 pending 写入。旧 plan/run/operation writer 已从工作树退役，历史材料通过 `history` 或专用只读 reader 消费；不翻译成新执行。

```sh
python3 -m lab doctor experiments/EXPERIMENT/intent.json --environment /absolute/environment.json
python3 -m lab build experiments/EXPERIMENT/intent.json --environment /absolute/environment.json --directory runs/EXPERIMENT/EXECUTION
python3 -m lab start runs/EXPERIMENT/EXECUTION --deployment /absolute/private-deployment.json
python3 -m lab status runs/EXPERIMENT/EXECUTION --json
python3 -m lab recover /absolute/CHECKPOINT --intent experiments/EXPERIMENT/recovery-intent.json --environment /absolute/environment.json --directory runs/EXPERIMENT/DERIVED
```

环境配置使用 `factory26.exp.environment` schema 1，声明 id、cache_root、python 和可选 harness。路径相对配置文件；harness 可声明 runtime、skill_source、tool_env、e2e_runtime、otlp_dependencies。Python 是明确的基础解释器；生产者按其字节、平台和锁定依赖建立共享物理环境，controller/runner 保留不同用途回执。编译不安装环境，build 只生产缺失资产。已有明确 runtime 回执仍可直接写入低层 recipe。

Intent 可声明 `productions`：每个命名项使用 `producer: "harness"`、variant 及上述材料选择，job.inputs 用 `{from_production: NAME}` 绑定。Compiler 调用生产者的纯依赖计划并冻结其结果；build 重新核对实际依赖后复用或生产。Profile 可以给出材料默认值，不能选择模型、费用、需求或恢复损失。冻结 recipe 使用 profile 时，只允许解析相同依赖的物理位置，改变生产选择须新配方。实际位置与原冻结选择分别记录。

共享 cache 中的 runtime、Harness、executor source 与 runner.pyz 跨 run 复用，run 的 artifacts/source/runner 定位它们并持有独立保留。负载只读消费发布资产，可写 workspace 独立装配；同 UID 的 Local 存储仍在读取或接收边界核验字节，不能拿 receipt 当永久内容证明。首次生产与无变化复用的成本不同。CLI 返回 build 成功表示材料已冻结，不表示模型已启动或入口 ready。

定义与运行数据分开存放。`experiments/` 保存可维护的 intent、原始 recipe 和冻结 compilation bundle；`runs/` 保存 runtime 资产、每次 build 的执行计划、attempt、制品、遥测和回执。一个定义可以建立多个独立运行目录，不为重试修改原定义。Build 拒绝把运行数据放进其冻结 compilation bundle，或让运行目录包含源定义；compile 同样拒绝覆盖其 intent 所在位置。已有运行目录仍可按原配方重入，不搬迁历史现场。

Intent、compilation、experiment、attempt、execution 使用 schema 2；artifact、runtime、request、telemetry 等未变化身份合同保持各自版本 1。新 writer 拒绝旧执行定义。旧运行控制先委派它的冻结 executor，不以新协议重解释旧在途效果；history 仍只读，不补造新保证。

新运行的 `experiment.json.definition` 显式保存源路径、消费字节 SHA 和定义快照的 artifact 引用；`recipe_sha256` 保持同一身份。源路径供人定位，运行中只核验冻结快照，不依赖定义文件持续存在。`status --json` 展示这条关系；旧记录缺少它时返回 unknown，不补造来源。快照是运行证据，后续修改从定义入口开始，不能把快照或运行计划当作可编辑配置。

## 从实验意图到冻结配方

`compile INTENT --environment PROFILE --directory BUNDLE` 消费 `factory26.exp.intent` schema 2，输出 intent.json、recipe.json 和 compilation.json。低层 recipe 仍可直接 build；复杂实验应把比较和选择政策交给公共 compiler，不再自行写 launch script。Compile 只读取显式本地材料，不安装 runtime、请求平台、调用模型或启动任务。

Intent 必需字段为 experiment_id、authorization、execution、cases、variants、models、targets、selection_policy、evaluation_policy；labels 可选。execution 声明 max_parallel、budget 和 storage；可通过环境生产 runtime，也可引用明确的 controller_runtime、runner_runtime。cases 是命名对象，每项声明 inputs 和可选 backend 的 competition_id/task；variants 每项的 generate 是现有低层 generate/prepare job 模板，省略 id/target/model_config。models 每项声明 config（model、visual_model、provider、base_url 四项）及可选 native bindings；bindings 使用已有 provider/base_url/credential_env/model_id 合同，只有变量名进入公开配方。

Targets 是显式列表，每项为 `{id, case, variant, model}`。Compiler 不自动展开笛卡尔积，也不从名字推断授权。模板与 case 的重复配置须一致；冲突拒绝编译。选定模型写入 job.model_config，托管同时写入 backend.model_config。模型、费用与 endpoint 不从 ambient environment 补全。

selection_policy 支持 `{"kind":"explicit"}`，此时 target.model 是 models 中的名字；或 `final-score-margin`，明确 baseline、candidate、minimum_margin（百分点评分差）、scores 和 on_incomplete。scores 以两个模型名和相同非空 case 集合组织，每项 `{source, run_id}` 引用保存的 GET；旧 journal state 另声明 task。必须绑定实际 run ID、终态 PASSED/FAILED、有效百分数及完整测试数量。完整时按声明 case 数量求均值，candidate 达到分差才被选择；缺失原件/未终态时仅按显式 on_incomplete=block 或 baseline 处理。身份冲突和损坏 JSON 是错误，不降为 baseline。采用政策的 target.model 显式写 `{"selection":true}`。

evaluation_policy 为 `{"kind":"none"}`，或 `per-application`，声明 job（purpose=evaluate 的低层模板）、from_generation（评价输入名到生成 output 名的映射）及可选独立 model。每个生成目标获得同 target 的 `.evaluate` job，通过 from_job/output 消费其实际发布制品；Hosted 评价须明确模型及费用，不能继承生成的收费许可。某题产物发布后，controller 按其依赖派发，不等待其它题。

Compiler 冻结源输入内容身份、runtime/handoff 描述摘要、评分原件快照与决定依据。authority_handoff 可使用现有冻结记录，或 intent 中的 `{source: PATH}`。Build 再核对实际字节，并将小型编译依据发布为独立制品；输入在编译与发布之间改变会被拒绝。相同输入、政策与 compiler 版本可重入同一 bundle；改变任一项须换目录。失败保存具体 compile-error 原件。Compilation receipt 不授予派发许可，旧实验和旧 launcher 的历史产物不被改写。

## 只读 readiness

`doctor INPUT [--environment PROFILE] [--deployment PRIVATE_JSON] [--json]` 聚合本机容量、冻结 controller/runner runtime 身份、输入制品与 producer 原件、模型凭据变量覆盖，以及声明 Docker daemon/image/slots/handoff 的现场读回。查询原配方使用源材料，查询已 build 的目录使用其发布制品。同一查询中已核验的 prepared/stop 制品路径用于来源元数据读取，不在该步骤重复全量哈希；不跨查询缓存内容证明。Prepared 和 stop 原件核对保存的来源绑定，启动仍独立重验当前来源。工具缓存没有独立声明时保持 unknown，不通过扫描任意目录猜可用。

对尚未 build 的 intent，doctor 读取明确环境和生产依赖，显示 runtime 缺失及预计生产工作，不初始化 cache 或域。对执行 recipe，Doctor 只执行 Docker info/image inspect/ps/volume ls/inspect；不调用会修改状态的 authority helper，不创建容器、初始化卷、释放预约、安装工具或请求官网。首次域的卷尚未初始化可显示 not-initialized，需要获授权域 owner 显式初始化；查询或预约不隐式创建缺失权威。Declared slots 与当前可用 slots 分开：只读域查询已有公共合同，未取得相应当前原件时仍显示 unknown；普通 status 不唤起域查询。Runner 镜像内 Python 和供应商实际能力未被执行验证；报告 observed/blocked 不等于可以启动。Start 继续核对物理准入、预算、凭据、来源与授权。

配方显式冻结 authorization、runtime 生产选择或明确回执、jobs、max_parallel、budget.max_attempts 和 storage.host_reserve_bytes。job 声明 purpose（build/prepare/generate/evaluate）、backend、argv（托管无需 argv）、inputs、outputs 与 wall_seconds/storage_bytes/telemetry_bytes。字符串授权只记录已经取得的许可，不授予执行。`inputs` 接受显式 source，或 artifact_id/manifest_sha256 和可选源 store；独立评价还可消费 `{from_job, output}` 的已发布生成制品。命令中的 `{workspace}`、`{inputs}`、`{attempt_dir}` 和输入名由实际执行环境展开。

`status EXPERIMENT` 和 `monitor EXPERIMENT` 使用同一 experiment projection。默认按目标与阶段展示当前 attempt、入口结果、执行、归档、输运、产物、阻塞及下一操作；`--json` 保留原有 attempts/execution/model_facts，并增加 targets/stages/facts/inputs/outputs/history/next_actions。job 可显式声明 `target: {"case": "github", "variant": "baseline"}`，两项均须为非空字符串。未声明 target 的评价阶段可沿唯一的 from_job 关系继承生成目标；其它 job 以原 job ID 分组，不解析命名猜比较条件。未派发阶段也会显示，输入等待列出具体 producer job 和 output。已经分配的评价 attempt 显示其实际冻结的输入，后来的生成 retry 不会使它改绑。

每项事实保留 producer 原件和观察时点。Main 的 exit 0、执行终态、archive preserved、export preserved、Harness 声明 complete、collector sealed 和平台 verdict 分别成立；非零入口结果不会因 controller completed 变成成功，unknown 也不会因存在归档变成完整 prepared。发布制品的状态读取本地 manifest 摘要或生产者保存的封口位置事实，不在每次 status 重算全部 payload；消费端仍核验实际字节及语义。平台状态取对应 `/runs/RUN_ID` 的保存 GET 原件，读取 status 或导出 logs 的时间不能代替平台新鲜度。Braid/Console 缺少绑定 attempt 的公开接入观察时明确显示 unknown；不读取其私有 SQL，不从 collector 存活或 Console 配置推断 connected。

Next actions 来自 controller 的公开操作判断，说明可调用命令及需重新满足的条件；保存状态不能授予启动许可。效果 unknown/pending、身份冲突和入口失败先检查原错，不能自动 retry。终态保全或 Docker 输运缺失时可给出同一 attempt 的 `control ... export`，执行时重新核对 incarnation 和物理终态。Prepared 的停止原件必须绑定同一来源；匹配旧原件仍要求 launch 重新观察。启动还须沿用真实授权和 deployment，并核验冻结 runtime、预算及资源。可以将多个现有实验目录列入 `factory26.exp.index`、schema_version=1 的 experiments 路径列表，以 `status INDEX_JSON` 一次读取；相对路径从 index 所在目录解析。这只是查询索引，不改写已有实验或替代运行关系。

公开 environment 冻结模型与供应商政策，私有 deployment 只引用 credential_file/cookie_file。credential_file 为 JSON 环境映射，不能覆盖公开模型、endpoint 或 runtime 政策。`FACTORY26_MODEL_BINDINGS` 以 native provider 或 `native-provider/model-id` 选择通道，分别声明 provider、base_url、credential_env；特定模型可显式声明 model_id 别名。Harness 将按模型覆盖拆为不同原生 provider，并同步 profile 与角色，避免共享 provider 的 key 覆盖其它模型。费用模式由托管 backend 显式声明，不因 endpoint 改变。

Docker endpoint、不可变 image_id、共享 slots 和 daemon 派生 admission_volume 显式冻结。接管还需 authority_handoff：全部旧派发者已停止、旧预留为空、在途窗口关闭的独立原件。`authority-handoff --endpoint JSON --writer OWNER_JSON --registry OLD_REGISTRY --authorization SCOPE --output NEW_JSON` 只读核验已明确列全的退役范围，不停止 owner 或释放槽。paused/alive 不等于退役；现有旧现场不自动迁移。

首次使用实际从未建立 Factory 域的 daemon，使用独立 `authority-handoff --mode first-use --endpoint JSON --scope SCOPE_JSON --authorization NEW_DOMAIN_SCOPE --output NEW_JSON`，不传 `--registry`。scope 的 kind 为 `factory26.exp.authority-first-use-scope`、schema_version=1，必需 daemon_id、authorization、allow_new_domain=true、no_other_legacy_domains=true、launch_windows=closed、writer_scope、registry_scope、writer_sources、local_registry_paths、registry_absence 和 evidence。writer_sources 必须与 `--writer` 原件列表完全一致，没有旧 writer 时显式写空列表；local_registry_paths 同样明确枚举或写空列表，producer 对这些本机路径实际 lstat。registry_absence 的每项为 `{host, path, source}`，source 引用真实宿主 readback：hostname、info 的成功 Docker ID 读回、registries 中该 path 的 exists=false；也支持外层 `{exit_code: 0, stdout: JSON字符串}` 原件。evidence 引用已保存的 writer/记录扫描原件。输出区别保存 reservations=absent 和 declared-first-use-scope，不伪造 released 或空旧 registry。

首次域的覆盖声明由获授权负责人给出；有限扫描、默认路径不存在和空 `docker ps` 都不能自行推出没有未知自定义域。producer 另外实时读取目标 daemon 的全部容器/卷，只扫描 Factory label/name 并保留其它资源；发现旧 Factory 资源则拒绝 first-use。此声明不接管其它 daemon，也不停止或释放任何旧域资源。

旧官网来源使用 `import-source-stop --birth ORIGINAL_GET --status TERMINAL_GET --authorization SCOPE --identity-output NEW_IDENTITY --output NEW_STOP`；可用 `--cancel-evidence ORIGINAL` 保存唯一取消请求来源，但请求受理本身不能满足门控。两个独立 GET 原件的 run/submission/competition/task/created_at/started_at 必须相同，终态 GET 还须有 finished_at。来源记录为 `factory26.exp.legacy-source`，使用 source_id、execution_instance 和 backend_identity，**没有新 attempt_id**。Harness producer 必须明确消费此来源联合类型；不能把它改名成新 attempt。Prepared 继续保留整个 source_identity，停止制品独立发布；新 launch 使用私有 deployment.cookie_file 重新 GET 同一个原 run，核对出生身份和物理终态，缺身份、凭据或当前观察时阻塞。该接口只读、导入及 GET，不进行 cancel/start/resume；跨平台来源尚不支持。

Docker 离线 job 显式设置 backend.network="none"，create 记录在 attempt/docker-create-intent.json 并传入 `--network none`；资源读回核对 HostConfig.NetworkMode 及 NetworkSettings.Networks，不仅根据 prepare-only 名称推断断网。未声明 network 的生成 job 保持 Docker 默认联网。首版不接受其它显式 network 值。

`control ... export` 仅接续终态保全和输运。`retry ... --authorization SCOPE --request-id REQUEST` 在冻结 attempt 预算内登记明确的新 attempt，再用 `start` 接续 controller。未知效果不授权新入口；重复原 dispatch request 不重跑 main。执行退出、归档、遥测封口、producer flush、输运和评分分别报告。Controller completed 只表示声明执行和证据流程结束，outcome 与平台评分仍独立。

制品复制以接收结果为完整性边界：export/transfer 先认证源 manifest 的引用摘要、身份及路径，再对收到的字节完整计算哈希；匹配后才发布目标，不在复制前全量预读源 payload。独立 verify 与 evidence/resolve 仍核对源字节。已完成的 transfer 重入只核验目的 store，不要求源仍可读；export 重入核对已有目标与源 manifest，不重新复制。校验失败的 staging 不发布，源和半成品保留。普通发布、装配和输运在同盘 APFS 上使用隔离写入的 clone；不支持 clone 或跨文件系统时复制字节，不共享可写 hardlink。目标完整性核验仍在传输边界执行，这不等于增量传输。

制品用 `artifact import/verify/export/transfer` 发布、核验及装配，`evidence` 按受限 member/字节游标读取。导入历史字节不会取得新执行证明。`telemetry snapshot/batches/export/ingest` 保留 stream/epoch/源序列、原始 protobuf 与错误；摄取同源批次幂等，冲突原件保留。Analyze 固定原件摘要和采集截止点；没有调用身份时模型用量明确未知，不从原始批次数推导 token 或费用。

四个新 I14 Harness 的布局分为冻结定义、运行派生输入和可写状态。公共材料包含布局支持代码；runner 输入绑定实际 artifact reference/member。Checkpoint/prepared schema 3 只复制状态并独立保留定义依赖，历史 schema 1/2 沿原冻结合同。SDK 自包含交付不变；新终态归档在实际映射和内容证明成立时保存状态与定义关系，不能将它当作完整 checkpoint。

Harness checkpoint/prepare 的公共生产接口、来源停止门控和路径限制见[恢复说明](../docs/deployment/recovery.md)。模型/收费生命周期与跨环境恢复的尚未取得实测见[任务 packet](../tasks/experiment-dx-review/packet.md)。本仓库不运行设施测试或 smoke；真实离线材料取得的反馈不替代模型实验验收。


托管监控只有一个采集 owner：持有该 experiment 控制锁的冻结 controller 调用 hosted adapter。adapter 自己持久保存 next_observation_at，前十分钟每三分钟、此后每八分钟查询并保留平台原件；终态导出也由同一 adapter 完成。不要把新 run 接入旧 hosted_monitor、伪造 legacy journal 或启动第二 collector。Luna 每十分钟使用该实验冻结 runtime/source 的 `lab monitor EXPERIMENT --json` 消费保存记录；这是 status 的只读入口，仅核对本机 controller 出生身份，不请求平台。

监控消费分别看 controller 生命周期、attempt 的 pending/remote_status/具体错误、archive、平台结果和原件时间。provider 新鲜度取该 attempt/platform 中 `/runs/RUN_ID` 成功观察的时间，不能使用本次查询 read_at 或 token 增长代替；controller 失联时报告缺口，不接管采集或重跑入口。重复状态保持安静，终态、具体故障、身份变化或需要用户动作才通知。原 collector 对旧来源的采集权限不会自动转移给新 run；新 run 可以先启动，Luna 订阅接收回执独立成立。真实接续消费合同见 `runs/experiment-dx-review/real-handoff-20261002/monitor-consumer-contract.json`。

## 资产、域动作与失败接续

发布 payload、manifest、域 location 和初始 producer 保留共同可见。Consumer 在装配前取得按用途保留；完成一个用途只释放相应 hold，不以 TTL 或入口退出释放其它消费者。GC 与 retain 共用 store 锁和稳定删除意图，未知位置、旧 store、未满足保全条件的载体继续保护。Artifact identity 与 manifest hash 在跨域输运中保持不变；位置不是新的 artifact identity。

Docker schema 2 使用运行宿主上的 detached runner，负载容器只读挂载域资产，拥有独立的可写执行路径。短时 store owner 执行受限发布/输运，工作负载不能访问 owner 代码、请求和 RW 发布卷。Runner host/process 出生身份与 daemon/container 出生身份分开；controller 退出不撤销 runner，运行宿主失联也不证明 Docker 负载已停止。该隔离依赖 Linux local-volume 及支持 volume-subpath 的 Docker API 1.45 或更高版本，不自动回落到共享 RW。

受管 create/start/stop/pause/resume 先保存版本化意图，再执行和读回物理效果。超时留下 pending；重入原请求查询效果，不重发 create/start。终态实例禁止再次 start，新执行重新准入。只读 query 使用已核验 Mountpoint 的 bind，不按卷名称打开并意外创建缺失卷；正常使用期间不删除或重建域资产根。Query、输运和构建不是另一个生成调度系统，但各自必须有界并发、超时、清理和实际资源约束。

服务 ready、入口确认、named output 封口、telemetry 封口及完整 archive 分别记录。必需 ResourceEvidence 由 runner 持有，Docker 取实际负载的 cgroup 样本，独立于 OTLP 开关。声明产物封口并保留后，同 daemon 的消费者按原位置装配；跨域或 Hosted 才请求输运。完整归档继续保全，其失败不能把已成功的 main 改成失败，也不要求重新运行入口。新 runner 对已封口的 terminal staging 使用显式同盘 handover：先耐久记录请求、来源和内容身份，再 rename 到 artifact publication staging；发布重入复用原 artifact，rename 后失响应从原 handover 接续，不再保留一份相同 terminal staging。原工作区和未确认半成品始终保留。Docker 终态下载的完整目录移入最终 attempt 路径，保存内容核对和耐久安装回执后才释放相同下载 scratch，未归属 metadata 保留。ARC SDK 新产生的输出 tar 标明 transport scratch，只有本地输出完成核对、耐久保存并取得 verified 回执才释放；重入依据保存的本地输出与回执，旧 tar 不按新规则自动删除。

Console accessor 需要域内 `access_resource_id`，创建和启动属于同一权威，其写入许可与 checkpoint 捕获共同排序。新登记不能追认旧未覆盖的活动 accessor；停止后不可重启同一出生实例，新的访问实例需重新创建及登记。当前服务的部署仍由其 owner 安排。
