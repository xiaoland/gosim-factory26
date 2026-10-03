# ARC 本地实验

## 当前新实验入口

新实验使用 `factory26.exp.experiment` schema 3。复杂矩阵先以 `python3 -m lab compile INTENT --environment PROFILE --directory BUNDLE` 冻结目标、模型选择和逐应用评价政策，再用 `doctor` 查询声明材料与宿主事实、`build INPUT --environment PROFILE --directory EXPERIMENT --job JOB` 发布冻结执行器；已授权的执行使用 `start EXPERIMENT --job JOB --request-id REQUEST --deployment PRIVATE_JSON`。维护的profile与实际生产依赖共同解析runtime及材料；参数和完整命令归 [Lab](../../lab/README.md)，当前实施及未验边界归[实验 DX](../../tasks/experiment-dx-review/packet.md)。

ARC matrix 也可直接生产新 recipe，显式提供 controller/runner runtime、预算、Docker endpoint/image、共享权威、模型与评价政策；可用 `python3 -m lab.arc_bench.arc_matrix --help` 查询参数。旧 `--env-file` 与 gateway-state 接线已经退役，私有凭据由 deployment 提供。SDK 子容器归同一 attempt 资源合同，旧派发者、预约和在途窗口尚未完成交接时不能接管该资源域；首次使用新域须有独立的 first-use 证据，不从容器数量推导授权。

生成阶段只读取允许的需求，应用发布后由依赖该制品的独立评价 job 消费，生成和评价的输入、费用及耗时分别保存。已冻结应用的本地复评使用 `python3 -m lab.arc_bench evaluate --spec RECIPE --output EXPERIMENT --build-only` 发布显式评价配方；它不再按来源 run 路径猜输入或继承模型/费用许可。`--build-only` 不启动执行，实际评价另按本轮授权接续。应用是否可消费由其制品和 producer 回执证明，不由外层 completed 推导。

## 历史运行合同与取证参考

以下保留旧冻结 run 的生产过程及操作，解释原记录的目录、字段和恢复依赖。命令仅适用于保存该协议的原冻结程序；工作树的 plan/run/operation、host-lab、按来源 run 复评等旧接口已退役，不能按这些示例新建执行。新旧 schema 的版本号属于不同协议，旧 schema v3 不会因数字较大而成为新 experiment schema 3 的替代品。

本文说明冻结 Harness 的本地生成与评分，适用于 Lite/Web 及需求公开的 Hackathon。它不调用官网；官网评分和应用重放见[平台操作](competition.md)与[恢复手册](recovery.md)。题目、制品、并发和完成条件先在所属 packet 登记，命名规则见[实验导航](../../experiments/README.md)。

### 准备 Runner 与运行条件

[arc_matrix.py](../../lab/arc_bench/arc_matrix.py) 将冻结 Agent ZIP 与 Lite/Web 任务展开为可并行的 job；[lab](../../lab/README.md) 在实验内共享冻结输入、保存实际控制器源码，为每个 job 建立独立尝试并运行指定命令。
它只要求外部 Runner 写入 `workspace/experiment-result.json`，不导入 Factory、Braid 或 Agent 会话格式。
[arc_bench_adapter.py](../../lab/arc_bench/arc_bench_adapter.py) 是单独的 ARC-Bench 适配器：调用主办方 `local_submit.py`，保存其原始 workspace 和 `local-result.json`，核对评测完成及用例计数，再写通用结果。
评测完成后的低分仍是有效结果；Runner 没有产出完整评测时是执行失败。

Mac 保存源码、Git、实验控制器及最终 run 目录，Docker daemon 只运行容器。通过标准 `docker context use <context>` 或 `DOCKER_CONTEXT=<context>` 选择 daemon；项目不维护设备、地址或 SSH 清单。每个声明使用 Docker 的 attempt 在启动时冻结实际 endpoint、TLS 参数和 daemon ID，build、run、inspect、stop 与 cleanup 使用该连接。运行中切换当前 context 不改变已开始的 attempt。

Unix socket daemon 保留本地 bind mount 路径。远程 endpoint 使用带 experiment/run/attempt/owner 标签的 attempt named volume 和 helper container；官方 Runner 仍在 Mac 装配阶段 workspace，适配器将冻结输入和 SHA-256 清单送入 volume，再以 `volume-subpath` 挂载阶段目录。需要 Docker Engine 26/API 1.45 或更新版本。挂载的实际类型、volume 名称/标签、子目录、完整容器 ID 及镜像 ID共同确认资源归属。Mountpoint 只保存为该 daemon 的执行证据，不用作项目配置或源码路径。

执行退出后先保存官方本地结算回执，再回收 workspace、容器日志和原始证据到 Mac。下载先进入临时目录，对照远端输出清单核验 SHA-256，再发布到原阶段目录；各阶段输出已核验且执行容器已清理后，才删除 helper 与 volume。`docker-workspace.json` 保存执行副本、回收与清理状态，`*.input-manifest.json` 和 `*.output-manifest.json` 保存完整文件清单。Mac 的 `run.json`、stdout/stderr、`experiment-result.json` 与归档始终为权威记录。

取消时仍沿用控制器的 TERM/KILL 语义，适配器只停止经精确归属核验的本 attempt 容器，再尝试回收。daemon 不可达、复制或哈希校验失败均保留具体错误和 `unconfirmed`/回收失败状态；volume 保留供恢复，不能据本地进程退出声称远端已清理。`lab reconcile <run>` 只核对，恢复连接后 `lab cleanup <run>` 停止所属容器、重试未完成的回收，并在核验成功后释放 volume，不重新装配或启动 Agent。历史资源没有冻结 endpoint 时保持 unconfirmed，不能拿当前 context 猜测清理位置。Console 的本宿主 Unix socket 限制不受此接线影响。

控制器与当时的新 worker 登记本机 host、boot ID、PID 和原生出生身份；Linux 使用 `/proc`，Mac 使用 boot UUID 与 libproc 的微秒出生时间。旧记录不回填，也不把两个空出生字段当作匹配。确认同机 PID 已消失，或同一 boot 的出生身份不再匹配时，才判 lost；进程存在但历史身份不足、宿主不同或查询不可读均保持 unknown。仍标 running 的未知控制器阻断接管，未知控制器阻断 cleanup，未知已启动 worker 阻断 retry 与 cleanup；reconcile 保存这项事实，不自行修复历史身份。旧 worker 缺 host 时不能仅凭本机 PID 不存在放行。

长矩阵启动前检查 Mac 回收空间、远端磁盘和容器内模型 API。Mac 容量预算只覆盖本地权威目录，不等于远端 volume 的存储配额；远端临时空间须另外确认。远程回收会同时保留下载 tar、解压目录与原阶段目录，workspace cap 和 finalization scratch 必须按这个峰值声明，不能只按最终应用大小估算。出现共享环境故障时停止派发，保留完整生成的应用，环境恢复后仅补评测，不把设施失败计作模型零分。以下命令在 Mac 仓库执行，Runner 与输入都使用 Mac 上的冻结目录；镜像在所选 daemon 构建。基础 Python 使用本机明确的可执行路径。
基础镜像 digest 是 2026-09-23 核验的 `linux/amd64` 发布物；若换镜像，保留新 digest 和每个 run 的 `image_id`，不要将两者的分数视作同一环境。

```sh
LOCAL_ASSETS=../factory26-official-local
RUNNER="$LOCAL_ASSETS/runners/<revision>"
python3 scripts/runtime.py host-lab --python /path/to/host/python3.12 \
  --output "$LOCAL_ASSETS/runtimes/lab-<build-id>"
HOST_RUNTIME="$LOCAL_ASSETS/runtimes/lab-<build-id>/asset.json"
ARCBENCH_LOCAL_BASE_IMAGE=gyataro/arcbench-runner@sha256:40e003ed470dbd4c120b9019876ba77303d38dc8b34be7f6e313fe0563dd14de \
ARCBENCH_LOCAL_PLATFORM=linux/amd64 "$RUNNER/build-image.sh"

python3 -m lab.arc_bench.arc_matrix \
  --candidate candidate=/path/to/frozen-agent.zip \
  --case arc-bench-lite/keep --case arc-bench-web/keep \
  --inputs-root "$LOCAL_ASSETS/platform-inputs" --runner "$RUNNER" \
  --host-runtime "$HOST_RUNTIME" \
  --image arcbench-local-submit:latest --workers 4 --separate-evaluation \
  --shared-docker-slots 5 --memory 2g --cpus 2 \
  --workspace-cap-gib 24 --telemetry-cap-gib 4 --finalization-scratch-gib 8 \
  --host-reserve-gib 50 --build-cap-gib 20 --archive-level decision \
  --output "$LOCAL_ASSETS/experiments/example/manifest.json"

python3 -m lab run "$LOCAL_ASSETS/experiments/example/manifest.json" \
  --runs-root "$LOCAL_ASSETS/experiments/example/runs"
```

真实模型可在 `arc_matrix.py` 指定直连模型的 `--env-file .secrets/arc-bench.env`，或指定新网关实例的 `--gateway-state <状态目录>` 并按需提供 `--env-file` 中的额外客户端变量。Mac 网关的客户端地址必须有经远端容器验证可达的显式入口，不能沿用 loopback 或把远端 host.docker.internal 当作 Mac；适配器不自动开放网关端口。网关模式由每个 run 的临时凭据绑定请求，`--env-file` 不再同时直接传给 Runner；官方 Meter 凭据仍独立。模型 env 文件权限为 `600`，适配器临时合入 OTLP 参数后传给 Docker，运行结束删除临时副本。
`host-lab` 在明确的稳定宿主目录建立不可覆盖的 Python 环境并写 `asset.json`；失败目录没有有效回执，不能消费。schema v3 配方显式选择该回执，controller、adapter、gateway wrapper 与 inspect/cleanup 共用其 launcher，计划和每次启动核对环境树身份。基础 Python 和独立 gateway service 仍是分别记录的宿主前提，不能从本次命令推断它们已建立。

容量值只是命令形状示例；每轮须依据冻结包、Runner workspace、telemetry 和归档峰值在 packet 声明预算。该旧协议的可执行归档级仅为 `decision`，其它级别尚未实现，CLI 和 schema v3 配方会拒绝。当时的新 ARC 配方写 schema v3，attempt 分配和增加并发前保存空间/inode 预检；历史 v1/v2 保持 `legacy-unbudgeted`，不能据此声称通过容量保护。

运行中异步容量观察写入 `storage-observations.jsonl`；达到 80% 或扫描不完整时暂停新派发，单 run 达到 cap 时停止对应进程组，host reserve/inode 触底时停止全部受控进程组。预算停止保留 workspace、OTLP、原错和阈值，不触发 GC，也不能计作模型零分。进程组退出不能证明容器等外部资源已停；`run.json` 保存 `unconfirmed`，须用 `reconcile` 核实并按需显式 `cleanup`。

`--prepare-only` 只准备两类输入与制品装配，不产生评分。
独立生成使用 `--separate-evaluation`，生成阶段不传公开测试；省略该选项的单阶段路径不作为独立生成基线。
以下 workers 派发及五秒容量等待属于旧冻结执行器。新 schema 3 使用显式 job/request，容量不足直接返回，资源释放与归档分开；新操作以 Lab 入口为准。

旧矩阵中的每个执行都有独立 run ID；同一赛题、不同 variant 可以同时运行，`--workers` 只限制该实验控制器的派发并发，不按赛题或 variant 加锁。`arc_matrix --memory 2g --cpus 2` 将每个新 run 的 Docker 内存和 CPU 参数冻结到 adapter argv；Python 调用对应 `build(..., memory="2g", cpus="2")`。不指定时沿用官方 Runner 默认值，不改写旧配方。容器内存与 CPU 限制不等于 schema v3 的 workspace、telemetry 和归档存储预算。

需要多个控制器共享执行容量时，同一旧协议的矩阵显式设置 `--shared-docker-slots 5`，Python 调用对应 `build(..., shared_docker_slots=5)`。准入按冻结 daemon ID，在同一控制器宿主的 `~/.config/factory26/docker-admission/<daemon-id哈希>/` 使用持久 registry 和文件锁；XDG_CONFIG_HOME 可改变配置根目录，FACTORY26_DOCKER_ADMISSION_ROOT 可指定统一准入根目录。所有参与控制器须使用同一稳定目录，不为每个 run 单设目录；已有 registry 与请求的槽数不一致时拒绝执行。五槽是同宿主、同用户或共享锁目录、同 daemon 的共同上限，各控制器的 workers 不会各得到五槽。不同宿主、独立锁目录或未接入准入的外部执行者不受同一锁协调，不能据此声称跨宿主全局限流。

准入计入 daemon 上带 `io.factory26.stage` 标签的 running、paused 和 restarting 执行容器；helper 不带此标签，不占执行槽。新启动前的 reservation 另占槽，匹配同 run/attempt/stage/owner 的实际活动容器后只计一次；未知进程身份不会自动释放 reservation，确认 lost 后仍须独立 Docker 读回证明没有对应活动执行。容量不足时程序每五秒等待并保存状态变化，不调用模型。准入覆盖输入传输、执行及 finally 的停止和回收，退出时释放本次 reservation；仍在运行的物理容器继续计入。最新事实与变化保存在 registry 的 `receipts/<lease-id>.json`、同名 `.jsonl` 和阶段旁的 `*.resource.admission.json`。观察时间表示该次读回，不等于持续健康保证。

例如同一 daemon 已有两条旧 I13 执行时，五槽中只余三槽；新矩阵使用 `--memory 2g --cpus 2` 不改变原两条的 4GiB 配额，旧执行结束后，显式请求的新增执行可使用释放的槽；容量不足时不排队。不替换旧冻结 controller-source 来接入新政策。共享锁机制的存在与容量读回不能替代多控制器并发、满槽等待或失联回收的实际运行验收。
`run.json` 保存输入快照哈希、适配器退出码、原始 Runner 结果和遥测取得情况；原始 Runner 退出码在 `result.runner_exit_code`。
旧流程将 Runner workspace、stdout/stderr 和声明归档的产物留在外层 run 目录中。I13 内层归档只有回执授权才删除其精确 `work`；这不授权清理外层 Runner 现场。只读候选查询与保护边界见[证据说明](evidence.md#存储回收候选)。

运行期间，基础设施提供带 run 凭据的 OTLP/HTTP protobuf 接收端，支持 traces、logs 和 metrics。
本地 daemon 默认将通用 OTEL exporter 端点改为 `host.docker.internal`；本地 Linux 可用 `--container-otlp-host <宿主网关>` 显式选择入口，并自行验证容器可达性及 collector 监听地址。
远程 daemon 默认通过包装入口复用现有 OTLP receiver，在执行容器 loopback 收集 traces/logs/metrics 到 `template/.arc/adapter-telemetry/telemetry.sqlite`，随 workspace 核验回收。I13 自身的 `.factory26/<run>/telemetry.sqlite` 仍优先作为其过程查询来源。Mac collector 默认仅监听 loopback；远端 `host.docker.internal` 不代表 Mac。只有调用方明确配置并验证了网络入口时，才使用 `--container-otlp-host <可达的collector主机>`，不会自动开放 Mac 端口。
接收端只保存原始 OTLP 批次，不规定 Agent 上报语义；未上报保持 absent，不影响评分。
Runner 若将原始会话或失败 DOM 写到自身不可访问的临时目录，外层设施无法在销毁后补采，应让 Runner 或 Harness 在运行时写入持久 workspace。

### 冻结应用的本地复评

已生成的 ARC 应用可用 `python3 -m lab.arc_bench evaluate <来源run> --output <新实验目录> --host-runtime <稳定asset.json> --workspace-cap-gib <容量> --telemetry-cap-gib <容量> --finalization-scratch-gib <容量>` 单独复评。该旧复评流程冻结 schema v3、稳定 Python 与本次预算；预算须按复评峰值声明，不自动继承来源生成的现场解释器或预算。命令优先核验入口前发布的应用，沿用来源的冻结需求、测试、Runner 与镜像 ID；旧 run 缺测试快照时显式补 `--tests <已冻结测试目录>`。加 `--plan-only` 只准备新实验。复评通过 `--template` 和核验型 noop 消费应用，不运行生成 Agent，也不传模型凭据。改变测试范围或镜像会产生新的评测条件。

```sh
python3 -m lab show "$LOCAL_ASSETS/experiments/example/runs/<run-id>"
python3 -m lab telemetry "$LOCAL_ASSETS/experiments/example/runs/<run-id>" \
  --export "$LOCAL_ASSETS/experiments/example/analysis/exported-otlp"
```

`telemetry` 也接受 `--signal`、`--since`、`--until`、`--after-id`、`--until-id` 与 `--limit`；导出的 `.pb` 保持接收时的原始 OTLP protobuf 内容。`evidence <run> <相对路径> --offset N --bytes N` 按范围读取原始文件。`events`/`wait` 使用持久游标；`parallel` 可在执行中调整总槽位，`stop` 请求停止，`reconcile` 只核对已登记资源，`cleanup` 才显式清理。失联后不自动重跑已有尝试。
`--max-parallel` 接受任意正整数，调整的是单控制器派发槽位；已冻结的共享 Docker 准入上限独立生效，不能通过增加 max-parallel 绕过。冻结目录保留内部符号链接，但拒绝指向快照外部的链接；ARC 矩阵接受输入目录提供的 `COMPETITION/TASK`，不维护赛题白名单或历史测试数量；是否完整评分依据本次 Runner 的终态与计数，适配器的 `--expected-tests` 仅在调用者明确指定时约束数量。
Braid 的会话重建、静态网站、补采和逐项排障统一见 [Braid 诊断运行手册](braid-diagnostics.md)。
常用入口为 `make braid-report RUN=<外层实验run目录> OUTPUT=<新网站目录>`，详情见 `make help` 或 `python3 -m lab.analysis.braid_telemetry_viewer --help`。
外层实验 run 与 Braid run_id 分别保留，不互相替代；接收批次或生成网站成功都不等于诊断证据完整。

### Raw Pi/Codex 基线

[package_raw_core.py](../../scripts/package_raw_core.py) 可直接消费 `runtime.py linux` 导出的原生工具目录，也保留从历史 ZIP 提取 runtime 的方式，再加入独立的 [raw_main.py](../../variants/raw/raw_main.py) 入口。
模型请求参数由 [raw_models.json](../../variants/raw/raw_models.json) 按模型 API 定义，两个核心的 ZIP 固定同一组 `thinking`、`reasoning_effort` 和 `max_tokens` 参数、模型 descriptor 和来源摘要；不读取 Factory harness 的模型配置，也不加载 Factory、Braid、SVC、项目技能或外部子代理。
具体运行模型与资格状态由实验记录维护；通道曾返回额度拒绝，不代表模型持续不可用，恢复后应以真实 API 请求确认所选参数和工具调用。
Pi 直接使用 JSON 输出和原生 session；Codex 使用 JSON 输出的原生 CLI，Chat 网关接入沿用 LiteLLM Responses 兼容层，并由 raw 专用适配器移除 Codex 自带的 reasoning 字段。
入口将完整原生事件、stderr、会话与终态写在应用工作区 `.arc/raw/`；[raw_otlp.py](../../variants/raw/raw_otlp.py) 将过程事件作为 OTLP logs 发送，跳过高频的逐 token `message_update`。
上报失败记在同一目录，不覆盖生成终态。
这些事件的分析语义由实验使用者决定。

```sh
python3 scripts/package_raw_core.py --runtime runs/runtime-pi \
  --backend pi --model glm-5.3-flash \
  --output ../factory26-official-local/fixtures/raw-pi-glm.zip
```

对 raw 独立生成基线，矩阵加入 `--separate-evaluation`：适配器先调用主办方 Runner **不传测试目录**生成应用，再以不调用模型的空入口及 `--template` 对冻结应用评分。
它比较生成后的应用源码哈希与评测容器启动时的源码哈希，并分别保留 `official-generation` 与 `official-evaluation` 工作区。
主办方单次本地运行会先把公开测试放入容器，所以此两阶段模式是避免 Agent 在生成期间读到测试的必要边界；生成容器虽仍有空的 `/workspace/tests` 目录，但没有测试文件。
`run.json.result` 分开记录生成终态、两阶段退出码、源码身份与完整评分。

raw 入口可读取 `FACTORY26_API_KEY` 并采用冻结包指定的模型；历史默认地址不代表当前授权的凭据来源。新实验按任务选择自带 key 和对应 endpoint，不能沿用旧参赛额度凭据。

需要连接别的兼容网关时可提供 `OPENAI_BASE_URL`。
不要提交或分享凭据。
评测阶段不向空入口注入模型凭据。
生成目录中的原生事件和 OTLP 批次可能包含需求、工具输出或模型文本，分享前检查内容。

raw 的 API 参数以 [raw_models.json](../../variants/raw/raw_models.json) 和包内 raw-config.json 为准。
原生客户端档位及协议转换不能代替实际 API 能力事实；历史参数调查见[模型推理记录](../../reports/2026-09-23-model-reasoning-probe.md)。
具体运行组合、资格状态和未完成事项归 [raw 任务](../../tasks/raw-core-local-baseline/packet.md)，不在操作说明中同步另一份矩阵。

本节本地运行不调用官网；既有 Competition 控制器与归档仍可追溯历史结果。
官网可用性以实际观测为准，不能用这里的历史描述判断是否恢复。
共享模型 key 并发使用时，账户级费用差值仍不能可靠归因到单个 run，应以 Runner 原始结果中的实际可用值及其限制为准。

历史接口、环境与资格证据见 [迭代 task packet](../../tasks/iteration-throughput/packet.md)。
本地模拟结果不能宣称官网评分通过。

本地生成的内存与 CPU 参数经 `arc_matrix --memory <Docker内存值> --cpus <CPU数>` 冻结，再由 adapter 原样传给官方 local runner；未指定时沿用 runner 默认值。
记录资源配额与 cgroup 压力后再比较耗时，不把不同资源条件下的变化单独归功于模型或 Harness。

### 工具、浏览器与应用验收

runtime 随包提供 pnpm、portless、agent-browser、Playwright 及其命令入口，依赖版本以包内 npm lock 为准。活动 variant 为同次运行的成员和接续设置共同的 npm cache 与 pnpm store，位于 `work/cache/`；它们按需积累下载，不预装应用框架或业务依赖，也不要求离线安装。
浏览器操作默认使用 agent-browser。runtime 保留已安装的 Playwright Test 与配套 Chromium，按需用于可重复检查；两者使用同一浏览器二进制，各自管理会话。
`BROWSER_CHECK_NODE_MODULES` 指向已安装的 Node 依赖，`BROWSER_EXECUTABLE_PATH` 指向可移植浏览器入口；按应用检查方式使用，不强制配置模板或独立验收技能。
检查目录的 node_modules 链接由应用自己的 .gitignore 排除，不成为交付依赖。最终验收使用可重复的应用测试或脚本，原始错误、trace、候选提交和运行条件保留在该次工作证据中。
原有冻结 runtime 和 ZIP 不随此修改更新。

### 冻结输入与新一次执行

`arc_matrix --candidate CASE=ZIP` 将本轮配置行与包内真实 variant 区分；同一 variant 的不同冻结 ZIP 可作为不同 candidate。兼容参数 `--variant NAME=ZIP` 是身份声明，包内已知名称不一致时拒绝运行，不能用于伪造历史身份。`--experiment-key` 标记已登记实验；题目继续用 `--case COMPETITION/TASK` 选择。

配方 job ID 包含 candidate、competition 和 task。初次执行及 `lab retry` 均显式传本次 `--run-labels <JSON文件>`，不继承上次运行名；稳定标签随配方冻结。完整参数和例子见 [历史标签合同](../product-tdd/index.md#实现实验与执行身份)。原样复评的 job ID 为 `evaluation`，同样保存实验、case 和本次执行标签。

旧 `local_runner.py`、`platform_public_run.py` 及共同配置的 factory.py generate/run/bootstrap/eval/batch 已退役；旧 manifest 和 run 保持原样，不能因改名成为新实验。raw 的具体配置与资格记录见[原始基线任务](../../tasks/raw-core-local-baseline/packet.md)，归档原生四配置的来源与运行方式见 [Hackathon](hackathon.md)。
