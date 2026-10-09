# 实验基础设施入口

Lab 的核心控制单位是 run：一次可以独立启动、停止和保存结果的实际执行。新入口直接组装 variant、ARC 任务与 target，不使用 experiment/job/attempt 控制器、capacity、slot、reservation 或未来任务队列。当前重构与验收状态以 [决赛设施 packet](../tasks/finals-experiment-loop/packet.md) 为准；源码存在或命令帮助可读不表示远端路径已完成验收。

```sh
python3 -m lab start I14-dx-test sfp7 TASK
python3 -m lab status
python3 -m lab status RUN --json
python3 -m lab pause RUN
python3 -m lab resume RUN
python3 -m lab stop RUN
python3 -m lab restart RUN
python3 -m lab restart RUN --keep-data --task NEXT_TASK
python3 -m lab wait RUN --json
python3 -m lab logs RUN --follow
python3 -m lab save RUN
python3 -m lab save RUN --json
python3 -m lab evaluate RUN --kind official
python3 -m lab evaluate RUN --kind self-test
python3 -m lab archive RUN
python3 -m lab serve --config SERVICE_JSON
```

`start` 只要求 variant、target、task，可追加 `--route FILE`、`--competition` 和 `--script FILE`。task 可以是需求目录或维护的任务配置；自动评测由任务配置的 evaluations 清单明确启用，官网重放费用模式不从模型 route 推断。自费装配冻结 variant 声明的[供应商模型配方](../materials/model-recipes/README.md)、所需路由与 provider 配置；`--route` 覆盖本次路由，不修改公共供应商链。官网比赛不加载供应商配方、不带 model-proxy，直接使用平台同名注入的 OPENAI_BASE_URL/API_KEY；角色模型仍归 variant。改设施与跑模型是不同授权范围；本文命令示例本身不启动或授权收费实验。

普通命令默认输出简短状态和本次操作的必要回执；`start/restart` 显示实际配方、参赛身份、来源及记录位置，`evaluate` 显示独立评测子 run 和冻结应用引用。控制回执不代表结果已保存，评测派发也不代表已有评分。`save` 取得一个可搬运现场包，默认写入该 run 的 `snapshots/portable-*.zip`；它不停止运行、不改 lifecycle，也不把运行中的不一致现场当作终态检查点。需要完整结构化信息时，对这些命令追加 `--json`；Python API 始终返回完整对象。错误独立显示，不被正常 brief 遮住。`logs` 保持日志流，不默认展开原生会话历史。

终态自动保存与人工 `save` 共用同一个 `execution.save` 源保存器。远端 Local run 先由执行宿主保存并由 Mac relay 回收，portable 包只在拥有本地副本的控制宿主生成；Hosted 和本地控制侧则在终态源保存成功后直接生成。结果回执中的 `portable_package` 是控制侧路径，不能用远端 `save.json` 路径代替。

自费代理运行的 `spend.usage` 汇总本 run 创建之后、已保存原生消息中的 token 用量，并保留 session、模型和原件路径。接续继承的旧消息不重复计入新 run；未保存或正在执行的请求仍是缺口，因此覆盖状态为 partial。CLI 和 Console 同时显示这份事实。原生 token 用量不是供应商账单；未取得供应商计费或已核实的请求价格时，金额明确未知，不采用原生配置中的零费用占位值。

普通 Python 策略应把 `spend.kind`/`spend.status` 当作金额资格：`actual` 需要有已确认的结算依据，不能仅由平台金额字段存在推出；`estimate` 可以由同一 run 的 usage、明确的价格表来源/币种/生效时间和覆盖范围计算，不能把套餐 credits 或原厂价冒充 ARC 费用。self-funded provider 即使金额未知，仍提供 `spend.usage` 和 `spend.provider_usage.attempts` 的 session、model、deployment、token 与 `as_of`。ARC 的计量服务另有模型价格、账户用量和计费请求接口，但共享 access key 的用量差值不能归属单个并发 run；缺少同源价格或模型身份映射时保持 unknown。idle 则读取 `last_activity_at` 与状态脚本的 `evidence`/新鲜度；策略可自行决定阈值和工具等待含义，设施只保留原始时间与缺项，动作仍直接调用 `run.stop(path)` 或 `run.restart(path)`。

公共资源管理器的最新 cgroup 采样保存在当前 run 的 `data/harness/<native_scope_id>/producers/<run_id>/resource-observation.json`；观察程序复用这份数据写入 `status.resource` 与 `status.resources.supervisor`，供 Python 策略和 Console 消费。采样含内存/PID用量、上限、触顶事件及读取错误，保留来源与时点；它是最新采样，不是历史峰值，也不把容器退出后的 Docker 零值当作运行消耗。

Console 状态发布使用 gzip 传输完整快照，不裁剪供应商尝试来掩盖采集缺口。注册入口与 OTLP 共用服务配置的 `max_batch_bytes`（默认64 MiB），约束传输及解压后的正文，同时兼容旧客户端的未压缩 JSON；不另设512 KiB状态限制。发布失败保留具体HTTP错误，不改执行状态或伪造新采集时间。页面的任务/目标用于定位run，供应商尝试默认显示总数和最近记录，完整原件按展开读取。

Hosted 的 `model_transport=platform` 运行从周期工作区采集本轮原生用量，按 ARC 价格得到 `spend.kind=estimate`；运行中及终态均以该估算为主口径，不依赖平台费用字段。ARC 适配器在首次观察时将维护的 `lab/arc_bench/arc-prices.json` 保存到该 run 的 `records/platform/arc-prices.json`，后续沿用此价格版本。金额是已定价用量的小计；`coverage`、`missing`、`price_as_of` 和 `usage_as_of` 明确未定价模型/缓存项与采集截止点，未完成请求不按零计算。Pi 的 input 已排除缓存，output 已含 reasoning，不重复计费。平台费用字段单独保留在 `platform-meter.json`；最新工作区缺少 native usage 时报告 unknown，不由平台金额替代或填零，也不为费用重复下载。完整 project 已保存后可用[归档费用脚本](../tooling/scripts/README.md#braid-project-归档费用)核算所有本轮会话。此表不用于 Qianfan/ARK 等自费供应商配方，即使模型同名也不套价；策略自行决定如何处置 partial，不将小计低于阈值解释为总费用低于阈值。

Hosted 运行中的观察仍按现有 observer 周期执行状态和日志查询；workspace 快照在最近一次请求后 300 秒内直接复用，避免重复下载。超过该间隔才读取 `workspace/template-bundle`，只解析当前 scope/run 的 native、gateway 和 resource 成员。现代资源返回为 `resources.supervisor`，保留 producer 路径和原始 `observed_at`/`observed_at_ns`；旧布局保留在 `resources.platform`。状态与 spend 的 `as_of` 仍取各自的状态响应时间，不被 workspace 快照时间覆盖。

独立 self-test 仍通过同一个 `evaluate` API，以 `--kind self-test` 区分，不增加 backend 命令。它从冻结运行的 `github-stage-N` 任务自动映射到对应的 `github-stage-N-req-test`；显式 `--task github-stage-N-req-test` 只用于覆盖任务。self-test 是私有、非排名结果，提交 ZIP、状态和回执保存在评测 run 的 `records/self-test`；如果站点没有导出 workspace，保存记录会明确列出缺口。认证由实际执行宿主的 Helium 私有会话材料提供，自测站 cookie 不复用 ARC 官网 cookie。

远端 local run 的 default worker 不直接在执行宿主派发评测；保存成功后，`task`、`simulate`、`official` 和 `self-test` 四种配置都由 Mac relay/controller 消费同一份已保存应用与 inputs，再按各自 target 启动独立评测 run。requirements/tests 由启动装配自动复制并按 run-relative 路径传输，不要求使用者手写 records 脚本、复制材料或为 sfp7→WSL/Hosted 评测手工接线。

`status` 无参数只列未归档且 lifecycle 不是 completed 的运行；failed、stopped 和 unknown 不会被默默隐藏。`--all` 查看全部，指定 RUN 始终可以查回。执行 lifecycle 来自实际执行器，activity/brief 来自该次 program 固定的 variant 状态脚本，查询只读保存事实，不进入远端重新采集。`archive --undo` 撤销隐藏；归档标记不停止、搬移或删除数据。正常完成的零分评测仍是 completed。

观察刷新暂时失败时，自动观察器保留上一份 status 中的 spend、native、resources、last_activity_at 和原 `as_of`，只将 activity 标为 unknown，并在 `observation_failed_at`、`error` 和 `records/observation-error.json` 中记录本次错误。这样 Python 策略不会把一次读取故障误判为事实归零；下一次成功观察才会替换这些事实。

Hosted 工作区下载失败也保留上次成功读取的 native、provider usage 和资源原件及其时间，另在 `workspace_observation.observation_failed_at` 与 `workspace_error` 暴露最新失败。平台状态查询和工作区采集各有时点，前者成功不表示后者新鲜。现代 gateway 和资源记录仅消费当前 native scope、当前 producer run，迁移来的旧 producer 不计入本 run 的供应商尝试。

启动准备失败会保存具体错误并显示 failed；越过远端创建或启动边界后失去回执则显示 unknown，不能仅凭没有句柄判成失败或重新派发。Local 后台 worker 派发成功仍为 starting，只有实际执行观察才能确认 running。异常不会因已有 starting 文件而被遮住；本次错误位于 records/start-error.json，远端派发意图位于 records/dispatch.json。

`pause/resume` 保持同一次实际执行；自管 Docker 使用 pause/unpause，Hosted 不支持。`restart RUN` 先停止并保存来源，再重新装配同名 variant，从题目基线开始创建新工作区和新原生会话，不继承来源进度，也不删除旧现场。target、task 和模型配置默认沿用来源，可以显式覆盖 target、task 或 route。

`restart RUN --keep-data` 才是接续：迁移完整 data，相同 task 和需求版本恢复原生会话；新 task 保留应用及历史，建立新原生任务状态。`--snapshot` 只在此模式下选择来源保存快照。不支持切换 variant、任意路径提取或失败时悄悄启动空会话。Python 对应 `run.restart(path, keep_data=True)`；已有接续脚本必须显式传入该参数，默认值已改为从零重跑。

I15 同任务原生接续默认保留来源冻结路由。明确授权改变配方时，使用 `--route FILE --allow-route-change --route-change-reason REASON`；此入口只允许同 scope 的 I15 接续，保留模型 alias 集合，并按来源供应商目录验证新链。装配和 Harness 分别保存、核对变更回执，不能只改输入文件便宣称在途 proxy 已采用。

`restart` 的新 run 按 target 名称重新解析当前维护配置，包含 runtime；来源停止与保存仍使用来源的冻结配置。需要指定旧 runtime 时，通过已有 `LAB_CONFIG` 选择固定该版本的配置，再执行 restart，不改来源记录。这只固定所选环境，不是完整检查点恢复，因为 variant 程序仍重新装配。

`stop` 只操作指定 run，不停止独立 Python 自动化程序或其他 run；回收迟到结果仍继续。Python 使用 `lab.run` 的同一组函数组织策略和 stages，不增加调度 DSL。默认 stages 只在 completed 后接续；费用和 idle 使用采集的来源、截止点与缺项，不把未知数当作零。

多阶段题目在任务配置中声明 `stages`，其值为按顺序排列的单阶段 task 名称或需求目录。例如维护入口中的 `github-stages` 声明 `{"stages": ["github-stage-1", "github-stage-2"]}`，可以直接使用 `python3 -m lab start I14-dx-test sfp7 github-stages`。目录题目的 `task.json` 使用同样格式，其中相对目录以该题目目录为基准；每个单阶段继续使用自己的需求和 evaluations 配置，不支持嵌套 stages。

`start` 实际派发第一阶段 run，并在启动命令所在的控制宿主后台运行普通阶段推进程序。前一 run 正常完成后，程序通过同 variant 的 `restart(..., keep_data=True)` 保存并迁移完整 data，重新装配程序，派发下一阶段；failed 或 stopped 不自动接续。每个阶段仍有自己的 run ID、状态、费用和评测，没有实验级控制对象或预先派发的队列。第一阶段 manifest 的 `stage_plan` 保存本次题目声明，`records/stages-progress.json` 保存已实际派发的 run 路径、当前步骤和具体错误；`records/stages.json` 与 `stages.log` 保存推进程序的进程身份与日志。普通 `status` 仍按 run 显示，不将阶段推进记录伪装成运行状态。跨阶段程序不能依靠已结束的执行容器继续运行，因此必须保留控制宿主；本地和 Hosted 使用同一入口。

`--script` 是普通 Python 程序，与观察、保存和任务自动评测并行运行，不替代它们。`lab.automation.watch()` 默认读取 `LAB_RUN` 的已保存事实，持续提供 `spend`、`native`、`resources`、执行状态及其来源时间；它不再采集、不访问平台，也不把旧数据刷新成新事实。重复读取允许脚本按当前时间判断 idle，具体判断与操作由脚本自己表达。例如：

```python
import time
from lab import run
from lab.automation import watch

for facts in watch():
    spend = facts['spend']
    native = facts['native']
    resources = facts['resources']
    # 在这里用普通 Python 判断，并调用 run.stop(facts['path'])
    # 或 run.restart(facts['path'], keep_data=True) 接续；省略 keep_data 则从零重跑。
    # 阈值、未知数据处理及动作后退出均由脚本决定。
    print(time.time(), spend, native, resources, flush=True)
```

默认 `watch()` 在指定 run 进入 `completed`、`failed` 或 `stopped` 后返回；只有显式使用 `watch(..., follow=True)` 或 `lab status RUN --follow` 才会观察接续。跟随只消费 manifest 中 `source.kind=restart` 的直接后继：停止早于 restart 派发时会保留在原 run 上等待并显示 `old→waiting`，出现唯一后继才显示 `old→new` 并继续；出现多个后继则显示分支并要求用户明确指定 run。普通 `status`、`stop`、`pause`、`resume` 和 `restart` 始终针对用户给出的具体 run，不会因跟随关系重定向控制。

状态中的 `restart_summary` 汇总接续材料是否保存、是否复用 native 状态、目标 run 的冻结/装配材料、派发回执和执行端实际消费证据；没有执行端版本回执时明确保持 `consumed.adopted=null`，不把 manifest 的版本字段当作已生效证明。公共包入口在安装后写入小型 `material-consumption.json`，由已有 records/workspace 回收链读取；回执缺失只暴露 unknown，不阻止 Harness 启动。它分别给出当前 run 的 provider 请求、响应和成功响应，以及 variant status 脚本提供的 `effective_action`（`at`、`source`、`run_id`/`producer_run_id`）和来源时间；请求本身不能代替 variant 动作。正在运行但没有有效动作证据时会明确标记 `running-but-no-valid-action-observed`，旧 native scope 的 last_activity 不会算作当前动作。费用和 provider usage 默认只统计当前 producer run；完整保留的 native session 另以 `native_session_scope` 标示，不能把两者相加。
历史 `source.kind=restart` 未记录 `keep_data` 时仍表示当时的保留进度接续，新记录显式区分两种模式。`status --follow` 跟随明确的 restart 后继，但不把从零重跑误认成原生会话接续。

| 要做什么 | 权威说明 |
| --- | --- |
| 启动、控制、查询一个 run；组织 Python 策略 | [公共运行 API](run.py)、[自动化](automation.py) |
| 程序与数据目录、ARC 执行和同 variant restart | [ARC 适配](arc_bench/README.md) |
| 当前 run 的 Console、共享 Collector 与 Backend | [Lab Console](../consoles/lab/README.md)；Braid 协作与旧冻结服务见 [Braid Console](../consoles/braid/README.md) |
| 读取或操作旧冻结执行 | [历史 lab.exp 源码导航](exp/README.md)；使用其原执行器，不接入新的 run 控制。 |
| ARC 官方 SDK、平台与应用重放 | [ARC 适配](arc_bench/README.md) |
| 选择恢复来源与当前合法操作 | [恢复入口](../docs/deployment/recovery.md) |

新 run 固定包含 manifest.json、program、inputs、data/workspace、data/harness、records、snapshots 和 evaluations。program 保存实际程序，data 保存应用与可迁移原生状态，records 保存本次日志、状态、资源、费用与平台原件。`lab save RUN` 的规范包只包含 `manifest.json`、`data/workspace`、`data/harness` 和 `records`；它明确排除 `program`、`inputs`（包括预装 SDK/runtime 和开发缓存）、`snapshots`（包括官网原始 project.zip）及 `evaluations`。harness 内只额外排除明确的公共安装缓存 `browser-cache`、`home/.npm`、`home/.cache` 和 `home/.local`；workspace 内只有带 `runtime-source.json` 安装标记的公共 runtime 才会排除，不会按名称删除应用自己的 `runtime`、`node_modules`、better-sqlite3 或业务数据。records 中的原始归档文件也留在 run 内证据，不再嵌套进规范包。包外仍保留来源 run、原始官网 ZIP 路径及 `records/portable-save.json`。restart 不迁移旧记录或旧费用。凭据不进入可迁移 data 或公开归档。

Mac 控制及回收记录默认位于 WorkSSD 的 runs/lab，`LAB_RUN_ROOT` 可选择其他 WorkSSD 路径。远端执行目录按 target 配置确定；共享服务 SQLite 位于服务宿主本地磁盘，不跨宿主挂载 WAL。历史 schema1/2/3 记录保持原身份，兼容入口为 `python3 -m lab.exp`，不自动接管当前活动执行。跨组件约束归[技术说明](../docs/product-tdd/index.md)。

本地自费 I15 原生接续可在用户明确临时替换模型时，用 `restart --keep-data --allow-route-change --route-change-reason ... --route ... --model-catalog ...` 提供本轮独立 catalog。该入口只限同 scope、本地非参赛执行，catalog 明确 text alias → GLM-5.3 actual model 和独立 Flash vision alias；供应商连接必须已存在于来源冻结输入。来源 inputs 不修改，新 catalog 和授权变化另存新 run。正式 profile 和共享默认配方不受影响。原生会话逻辑 alias 可以保留以延续历史，实际模型以新 run 的 model_routes 与 native-model-substitution 回执为准；费用按生效执行切片区分，不能把旧 Flash 历史全部改按 GLM 计价。视觉 provider、原生视觉角色与 E2E 的模型引用在启动时读回该独立视觉 alias，避免图片发给文本模型。
