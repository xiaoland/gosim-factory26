# 实验定义、编译与构建

本页维护 compiler、environment、readiness 和所选目标的 build 合同。执行请求归[执行说明](execution.md)，材料位置与恢复产物归[制品说明](artifacts.md)。

定义与运行数据分开存放。`experiments/` 保存可维护的 intent、原始 recipe 和冻结 compilation bundle；`runs/` 保存 runtime 资产、每次 build 的执行计划、attempt、制品、遥测和回执。一个定义可以建立多个独立运行目录，不为重试修改原定义。Build 拒绝把运行数据放进其冻结 compilation bundle，或让运行目录包含源定义；compile 同样拒绝覆盖其 intent 所在位置。已有运行目录仍可按原配方重入，不搬迁历史现场。

Experiment 使用 schema 3；intent、compilation、attempt、execution 保持 schema 2；artifact、runtime、request、telemetry 等未变化身份合同保持各自版本 1。新 writer 拒绝旧执行定义。旧运行控制先委派它的冻结 executor，不以新协议重解释旧在途效果；history 仍只读，不补造新保证。

新运行的 `experiment.json.definition` 显式保存源路径、消费字节 SHA 和定义快照的 artifact 引用；`recipe_sha256` 保持同一身份。源路径供人定位，运行中只核验冻结快照，不依赖定义文件持续存在。`status --json` 展示这条关系；旧记录缺少它时返回 unknown，不补造来源。快照是运行证据，后续修改从定义入口开始，不能把快照或运行计划当作可编辑配置。

环境配置使用 `factory26.exp.environment` schema 1，声明 id、cache_root、python 和可选 harness。路径相对配置文件；harness 可声明 runtime、skill_source、tool_env、e2e_runtime、otlp_dependencies、provider_env、application_seed、gateway_routes。Python 是明确的基础解释器；生产者按其字节、平台和锁定依赖建立共享物理环境，controller/runner 保留不同用途回执。编译不安装环境，build 只生产缺失资产。已有明确 runtime 回执仍可直接写入低层 recipe。

Intent 可声明 `productions`：每个命名项使用 `producer: "harness"`、variant 及上述材料选择，job.inputs 用 `{from_production: NAME}` 绑定。Compiler 保存元数据和生产选择；build --job 只解析、生产并冻结所选 job 的实际依赖闭包。Profile 可以给出材料默认值，不能选择模型、费用、需求或恢复损失。冻结 recipe 再使用 profile 时须保持原 selection 一致；不能借 profile 覆盖冻结输入。资产位置与内容身份分别记录，换部署位置沿实际位置回执解析，改变生产选择须新配方。

## 编译明确意图

`compile INTENT --environment PROFILE --directory BUNDLE` 消费 `factory26.exp.intent` schema 2，输出 intent.json、recipe.json 和 compilation.json。低层 recipe 仍可直接 build；复杂实验应把比较和选择政策交给公共 compiler，不再自行写 launch script。Compile 只读取定义元数据及明确选择政策引用的小型原件，不安装 runtime、请求平台、调用模型或启动任务。

Intent 必需字段为 experiment_id、authorization、execution、cases、variants、models、targets、selection_policy、evaluation_policy；labels 可选。execution 声明 max_parallel、budget 和 storage；可通过环境生产 runtime，也可引用明确的 controller_runtime、runner_runtime。cases 是命名对象，每项声明 inputs 和可选 backend 的 competition_id/task；variants 每项的 generate 是现有低层 generate/prepare job 模板，省略 id/target/model_config。models 每项声明 config（model、visual_model、provider、base_url 四项）及可选 native bindings；bindings 使用已有 provider/base_url/credential_env/model_id 合同，只有变量名进入公开配方。

Targets 是显式列表，每项为 `{id, case, variant, model}`。Compiler 不自动展开笛卡尔积，也不从名字推断授权。模板与 case 的重复配置须一致；冲突拒绝编译。选定模型写入 job.model_config，托管同时写入 backend.model_config。模型、费用与 endpoint 不从 ambient environment 补全。

ARC 本地独立生成使用 `variants.<name>.generate` 的 `operation: "arc-local-generate"`、`purpose: "generate"`、inputs 和 limits；inputs 包含 agent，case 提供 requirements 及 backend.competition_id/task。agent 或 requirements 可以引用 `{from_production: NAME}`，无需编译前先生产材料。此操作由公共 ARC job 构造器生成 SDK 参数与 application 输出，不接受手填 command/backend。模型必须声明 native bindings。Environment 的 `arc` 声明 `sdk_source` 和 `target`；sdk_source 指实际宿主 SDK 的目录，包含 local_submit.py，不是镜像内的 local_runner.py。target 使用现有 external_docker 的 endpoint、不可变 image_id、slots、admission_volume 和 authority_handoff。宿主 Python、宿主 SDK 与 Linux Harness 材料各有用途；远端 Docker 的 Linux 材料不由控制宿主的平台推断。

需要接续应用时，case.inputs 可提供 `template`，由官方宿主 SDK 的 `--template` 复制来源应用，再覆盖本阶段公开需求。生成任务不能通过 `from_job` 自动消费前一生成任务；先冻结已发布的 application，再为下一阶段建立引用该确切来源的独立 intent。

旧 Pi 自包含包使用显式 `delivery_mode: "copied-tree"`，编译后冻结到 arc_contract。此模式在真实子域只读保留 agent artifact，并核对 SDK 可写执行副本与来源字节；Pi 原生入口会修改包内权限和创建 home 链接，因此不直接从只读源执行。它保留受管 Docker state、完整 SDK workspace 封存与回收，不声明组件定义、Braid 角色或 bootstrap Harness checkpoint。新组件 Harness 继续使用实际 definition composition。

Compile 核对声明与元数据，保留待生产引用；build 在实际绑定材料后核对 SDK 身份、Linux/amd64 材料与需求目录。Doctor 对未解析计划显示待绑定状态；对已经构建的目标按当前 admission 协议只读查询已有域，不修改域。实际启动时 adapter 向 SDK 提供显式模型环境文件；子容器在启动前读回变量名和公开配置摘要，组合入口在真实子容器内提供 ResourceEvidence 与 telemetry。静态角色核对不能证明容器或模型成功启动，子容器环境读回也不证明供应商已经受理请求。

selection_policy 支持 `{"kind":"explicit"}`，此时 target.model 是 models 中的名字；或 `final-score-margin`，明确 baseline、candidate、minimum_margin（百分点评分差）、scores 和 on_incomplete。scores 以两个模型名和相同非空 case 集合组织，每项 `{source, run_id}` 引用保存的 GET；旧 journal state 另声明 task。必须绑定实际 run ID、终态 PASSED/FAILED、有效百分数及完整测试数量。完整时按声明 case 数量求均值，candidate 达到分差才被选择；缺失原件/未终态时仅按显式 on_incomplete=block 或 baseline 处理。身份冲突和损坏 JSON 是错误，不降为 baseline。采用政策的 target.model 显式写 `{"selection":true}`。

evaluation_policy 为 `{"kind":"none"}`，或 `per-application`，声明 job（purpose=evaluate 的低层模板）、from_generation（评价输入名到生成 output 名的映射）及可选独立 model。每个生成目标获得同 target 的 `.evaluate` job，通过 from_job/output 消费其实际发布制品；Hosted 评价须明确模型及费用，不能继承生成的收费许可。产物发布后，使用者为评价显式选择生成 attempt/output，并创建独立执行请求。设施不会自动选最新产物或启动评价。

Compiler 保存源输入定位、handoff 描述摘要及 runtime 定位、评分原件快照与决定依据；大材料的内容冻结归所选 job 的 build。authority_handoff 可使用现有冻结记录，或 intent 中的 `{source: PATH}`。Build 再核对实际字节，并将小型编译依据发布为独立制品；输入在编译与发布之间改变会被拒绝。相同输入、政策与 compiler 版本可重入同一 bundle；改变任一项须换目录。失败保存具体 compile-error 原件。Compilation receipt 不授予派发许可，旧实验和旧 launcher 的历史产物不被改写。

配方显式冻结 authorization、runtime 生产选择或明确回执、jobs、max_parallel、budget.max_attempts 和 storage.host_reserve_bytes。job 声明 purpose（build/prepare/generate/evaluate）、backend、argv（托管无需 argv）、inputs、outputs 与 wall_seconds/storage_bytes/telemetry_bytes。字符串授权只记录已经取得的许可，不授予执行。`inputs` 接受显式 source，或 artifact_id/manifest_sha256 和可选源 store；独立评价还可消费 `{from_job, output}` 的已发布生成制品。命令中的 `{workspace}`、`{inputs}`、`{attempt_dir}` 和输入名由实际执行环境展开。

job 的公开 environment 冻结模型与供应商政策，environment profile 不持有该政策，私有 deployment 只引用 credential_file/cookie_file。credential_file 为 JSON 环境映射，不能覆盖公开模型、endpoint 或 runtime 政策。`FACTORY26_MODEL_BINDINGS` 以 native provider 或 `native-provider/model-id` 选择通道，分别声明 provider、base_url、credential_env；特定模型可显式声明 model_id 别名。Harness 将按模型覆盖拆为不同原生 provider，并同步 profile 与角色，避免共享 provider 的 key 覆盖其它模型。费用模式由托管 backend 显式声明，不因 endpoint 改变。

## 选定目标的物理构建与只读检查

`doctor INPUT [--job ID] [--environment PROFILE] [--deployment PRIVATE_JSON] [--json]` 聚合本机容量、冻结 controller/runner runtime 身份、输入制品与 producer 原件、模型凭据变量覆盖，以及声明 Docker daemon/image/slots/handoff 的现场读回。查询原配方使用源材料，查询已 build 的目录使用其发布制品。同一查询中已核验的 prepared/stop 制品路径用于来源元数据读取，不在该步骤重复全量哈希；不跨查询缓存内容证明。Prepared 和 stop 原件核对保存的来源绑定，启动仍独立重验当前来源。工具缓存没有独立声明时保持 unknown，不通过扫描任意目录猜可用。

对尚未 build 的 intent 与未解析 recipe，doctor 只读取明确的目标及生产声明，返回 unbound-plan；不读取全部 SDK/runtime/skills 内容，也不初始化 cache 或域。对已构建的执行 recipe，Doctor 只执行 Docker info/image inspect/ps/volume ls/inspect；不调用会修改状态的 authority helper，不创建容器、初始化卷、释放预约、安装工具或请求官网。首次域的卷尚未初始化可显示 not-initialized，需要获授权域 owner 显式初始化；查询或预约不隐式创建缺失权威。Declared slots 与当前可用 slots 分开：只读域查询已有公共合同，未取得相应当前原件时仍显示 unknown；普通 status 不唤起域查询。Runner 镜像内 Python 和供应商实际能力未被执行验证；报告 observed/blocked 不等于可以启动。Start 继续核对物理准入、预算、凭据、来源与授权。

四个新 I14 Harness 使用独立的 `factory26.harness.definition` 组合：variant、runtime、skills 和 support 组件各自发布，角色通过实际 artifact reference/member 关联。Local/Docker 直接消费这些组件；SDK 目录与 Hosted ZIP 是按定义缓存的交付投影。Controller/status 源码属于冻结执行器闭包，不参与 Harness 组件及交付投影的内容身份。运行材料不再以自包含交付目录为唯一内部单位。

`build INPUT --environment PROFILE --directory RUN --job ID` 必须选一个声明的 job。它不构建上游 job、不创建 attempt、不预约执行；下游输入要求保留在冻结定义里，实际消费由 start 明确绑定。生产缓存分别持有 agent、runtime、skills、support 和所选额外组件，组件锁不包住无关生产。Controller 和 runner 各自冻结实际代码闭包到 controller-source/source；私有输入及 store 位置不改变公开内容 key。能力声明描述材料接口，实际 checkpoint 覆盖仍由执行域证明。
