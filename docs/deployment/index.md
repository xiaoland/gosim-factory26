# 本地运行与证据

本文维护运行、证据查询和恢复操作。
产品规则见 [PRD](../prd/index.md)，组件责任与终态含义见[技术说明](../product-tdd/index.md)，开发准备见 [CONTRIBUTING](../../CONTRIBUTING.md)。
实验选择以当次任务与冻结清单为准；文中的历史观测不代表平台或机器此刻的状态。
分析运行的 token、耗时与完成度，使用开发侧 [运行分析 SOP](../../agents/run-analysis.md)。
Hackathon 四配置的 WSL 构建与运行见 [原生 Hackathon 运行说明](hackathon.md)。

## 参赛包与平台边界

参赛包复用本项目的 Braid + SVC 生成、Git 交付冻结和原生证据归档。
每个 ZIP 固定一个 variant 及其全部能力材料；根目录 `main.py` 接受平台传入的需求，不读取本地 benchmark，也不执行评测：

```sh
python3 scripts/package_agent.py --variant pi-braid --output runs/packages/pi-braid.zip --docker-context arcbox-win
# 以下命令在解压后的 ZIP 根目录执行，并由调用环境提供模型变量。
python3 main.py /path/to/requirements --output-dir /path/to/output
```

构建需要可用的 Linux x86_64 Docker daemon；`--docker-context` 可省略以使用当前 context。
脚本只发送指定构建输入，不上传整个开发目录。
Braid 从当前 `sources/braid` 构建；当前团队 variant 从 `sources/svc/skills/` 冻结所选七个 SVC 技能，不构建或安装 CLI；raw Codex 的 LiteLLM Python 依赖用 Linux CPython 3.12 安装到包内目录。
Node、所选核心、Chrome及其NSS动态模块、常用进程工具与非系统动态库均在构建时安装并随包提供；Pi 需要 Node >=22.19，不能直接使用平台原有 Node 20。
精确工具版本由 [Dockerfile](../../submission/Dockerfile) 固定，实际文件哈希、源码身份和执行权限写入 `package-manifest.json`。
npm lock 和 Python 依赖清单随 runtime 保留。
重复构建不覆盖已有 ZIP；构建时无需模型 key，比赛运行时无需 clone 源码、Cargo 或开发者 venv。

活动 `pi-braid` 的新包包含受管后台 Bash：普通命令运行超过 30 秒时返回任务 ID，进程保持运行；预期长任务也可由插件原生 `background: true` 参数直接后台启动。当前 Pi 会话中可用 `pbb list`、`pbb status <ID>`、`pbb tail <ID>` 查看状态与日志，`pbb kill <ID>` 明确停止；记录保存在该次工作区 `work/home/.pi/pbb/`。命令显式传入的 `timeout` 仍是会终止进程的硬期限，不能与自动转后台阈值混淆。会话关闭会清理其后台进程；原已冻结 ZIP 和暂停的 run 不获得此能力。

入口要求 Linux x86_64 和 CPython 3.12。
它先校验所有载荷并恢复 ZIP 解压丢失的执行权限，再在临时工作区直接启动原生程序。
包、需求、会话配置和交付身份仍由入口分别校验并记录；文件访问限制与网络白名单由运行平台负责，入口不再装配 Landlock 或其它自建沙箱。

平台通过 `OPENAI_API_KEY`、`OPENAI_BASE_URL` 注入文本连接；`MODEL` 若提供须与根角色一致。
可选完整 `VISUAL_API_KEY`、`VISUAL_BASE_URL`、`VISUAL_MODEL` 只供视觉角色使用，不覆盖主模型；仅有默认 VISUAL_MODEL 不视为提供了视觉凭据。
视觉地址启用时须同时提供对应 key 与模型；这只是 endpoint/key 路由分离，不代表账户 quota 已隔离或由 Harness 分配，未设置视觉地址时视觉 provider 回退到文本 endpoint/key。
冻结 variant 的主模型和视觉角色与平台模型不一致时拒绝运行，避免改变实验条件。
配置与清单保存环境变量名，不保存 key；运行时只传递实际需要的凭据。

应用交付遵循官方标准布局：`frontend/package.json` 提供 build，`backend/package.json` 提供 start；后端在 `HOST=0.0.0.0 PORT=3000` 下提供前端产物与 API，目标应用兼容 Node 20.19.3。
包内 Node 24 用于 Harness，不能推定部署环境也有 Node 22。
禁止依赖本地模拟器专用的 `deploy.sh`。
入口只在生成成功并冻结后复制应用，保留平台预置的 `.arc`、`.git` 和 `requirements`，拒绝覆盖同名应用文件。
输入可为独立需求快照，或输出目录原有的 `requirements/`。
证据保存在输出的 `.factory26/<run-id>/`；`run.json` 描述生成，`delivery.json` 单独描述交付成功或失败。

官方 Competition 的自动化入口为 [competition.py](../../lab/arc_bench/competition.py)，统一记录 ZIP identity、submission snapshot、task run、日志游标与终态收集。
通用参赛包只需满足平台的根入口 `main.py` 与 `requirements.txt`；Factory 包另有 `package-manifest.json` 时，Competition 会核对其中每个文件的哈希。所有包的冻结身份仍是 ZIP SHA256。
`prepare` 不写平台；其余写入按批准的实验范围执行，任何 POST 结果不确定都先保留 journal，再只读核查，不盲重试。
`prepare --credential-mode self_funded` 使用自带模型 key，也是旧 journal 缺失该字段时的历史语义。
2026-09-26 起停止使用参赛额度：`prepare` 拒绝 `official_evaluation`，提交入口也拒绝旧额度 journal 的上传、创建和启动；状态读取和证据收集保留。
凭据模式与 ZIP、模型配置一起冻结在 inputs.json 中，重用目录时必须相同；改变模式使用新的状态目录。后续 snapshot/run-all 从该记录取值，不另传开关。
摘要的 credential_mode 是请求模式；实际运行返回的 billing_mode 另保留在 platform_result 和原始 status.json，不能混为一谈。
后续官网实验使用 `self_funded`，冻结模型配置与自带 key 对应的服务地址一致；明确参加比赛须另获授权。
预算决定以 Braid session 为边界，七类昂贵模型合计只允许一个 Braid session 使用；Pi 原生会话和 sub-agent 不单独占用 Braid 名额。
当前源码以 CLI binding 对应的 Braid 逻辑成员领取名额；上下文重建沿用同一成员，原生子会话不另占名额。旧冻结包不包含这项修正。
限制是模型使用权限，不是金额上限；一个长会话仍可能很昂贵。
实现与下一轮修复范围见 [预算与交付任务](../../tasks/competition-budget/packet.md)。

Playground 仍只用于显式 practice，不混入 Competition 结果。

ARC 的官网 Run detail 使用官方 SDK 写入 Runner 的 `.arc/traceability/*.json` 与 `.arc/runner-events.jsonl`。需要此能力的 Harness 可在 WSL 导出公共工具，并在自身包构建、清单冻结之前放入 ZIP，通过自己的原生指令或工具机制将绝对路径交给 Agent：

```sh
python3 -m lab.arc_bench runtime export --output /path/to/arc-runtime.pyz
python3 /path/to/arc-runtime.pyz guide
python3 /path/to/arc-runtime.pyz version --json
python3 /path/to/arc-runtime.pyz methods --json
```

该文件包含 2026-09-25 官方 starter 的 `arcbench-agent-runtime` 0.1.0 和调用入口，运行时使用 Runner 的 `ARCBENCH_*` 路径，无需现场安装 SDK。公共 CLI 的 `traceability <方法>` 和 `events <方法>` 接受官方 SDK 的 JSON 关键字参数；`methods --json` 列出本包装器 v1 固定支持的方法与签名。操作加 `--json` 后，stdout 返回单个包含 `api_version`、`operation`、`status`、`paths`、`result` 及适用时 `error` 的结果；退出码 0 表示操作完成，1 表示失败或部分完成。旧命令默认输出仍兼容。多代理写同一个 run 时统一通过此入口调用官方高层方法；锁只保护通过该入口进行的操作。实验追溯由 Harness 从原有工作过程采集，不为填写官网页面要求参赛 Agent 额外上报；需求、接口和测试关系缺少明确事实来源时保持空白。自报的测试状态也不等于官方评分。

需要在官网展示真实 Git 提交的 Harness 可选两种命令：直接在 Runner 项目目录维护 Git 仓库时使用 `notify-history [--output-dir <Runner项目目录>] --json`；内部仓库开发时使用 `publish-history --source-repo <仓库> --ref <引用或OID> [--output-dir <Runner项目目录>] --json`。后者将选定提交及其祖先导入 Runner 项目目录的受管 Git 仓库，不改动应用文件或索引；`--preview` 在应用已就位后请求预览刷新。两种命令每次调用都尝试写入刷新信号，结果分别报告 `history_changed`、`history_updated` 和 `signal_written`；写入信号不证明官网已显示。仓库选择、轮询、重试和清理由 variant 决定。活动 `pi-braid` 从本轮运行的 `state/origin.git` 在生成中每五秒读取已发布的交付分支，交付后用冻结的交付 OID 再发布；结果写入本次 `.factory26/<run>/history-publication.json`。历史发布失败不改变应用生成结果，origin 与各 Agent 的独立 clone 留在 run state 供恢复；未合并分支和未提交文件不在发布范围内。

本地 run 与官网 task 的已保存证据可用 `python3 -m lab.arc_bench traceability <目录> [--node <需求ID>] [--json]` 查询；默认不发网络请求。它区分包内工具、实际记录与采集状态。本地保留原始表和事件，官网在既有监控轮询与显式 `collect` 时保存每次追溯及 commit history 响应或具体失败；查询分别显示提交历史的最近观察与最近可用列表的时间、来源和数量。终态若返回 `workspace_unavailable`，原始观察保留，但不会覆盖运行中已保存的提交列表。官网没有已确认的自定义文件下载能力，因此查询不会把托管工具调用日志标为已取得。通用 OTLP 仍保存 Harness 自选的 Agent 过程信号。

同一比赛只允许最新 snapshot 承接新任务。
新建 snapshot 不要求旧 snapshot 的任务全部终结；旧 run 的状态与原 journal 保持独立，本轮已观察到官网在旧 Sheet run 暂停时接受新 submission。
历史混合矩阵由 [official_matrix.py](../../lab/arc_bench/official_matrix.py) 运行：四个冻结 variant 依次推进；每个 variant 的 Lite 两题与 Web 六题由两个 Competition controller 并行执行，各比赛内部逐题运行。
两侧全部取得终态、完整评分及 manifest 声明的测试数，才上传下一 variant。
已完成一侧在重启后复用原 journal，不重复 POST；历史 Lite 单比赛 manifest 仍可恢复。
客户端并行请求不能证明官网同时分配执行槽，报告应保存各 run 的实际状态和时间。
两场比赛读取相同 ZIP bytes，manifest 绑定 SHA256；完整低分计入结果，设施失败不计为评分。
远端没有可用推送接口时，后台脚本从 180 秒间隔采集。

Lite/Web 的隔离输入位于仓库同级 `factory26-official-local/platform-inputs/<competition>/<task>/`，逐题保存公开需求、测试、素材与来源哈希。
主办方现已发布 [本地模拟 Runner](https://github.com/code-philia/hackathon-local-simulation/tree/4e62690ef0af48601150f248e1f993a300533357) 所需的生产基础镜像；原先只支持 Lite 的 `local_runner.py` 和官网矩阵内的本地队列已移除。
同级 `platform_public_run.py` 是早期的公开测试诊断入口，依赖 Factory 实现，也不作为新实验设施的执行底座。

## Lite/Web 本地实验

[arc_matrix.py](../../lab/arc_bench/arc_matrix.py) 将冻结 Agent ZIP 与 Lite/Web 任务展开为可并行的 job；[lab](../../lab/README.md) 在实验内共享冻结输入、保存实际控制器源码，为每个 job 建立独立尝试并运行指定命令。
它只要求外部 Runner 写入 `workspace/experiment-result.json`，不导入 Factory、Braid 或 Agent 会话格式。
[arc_bench_adapter.py](../../lab/arc_bench/arc_bench_adapter.py) 是单独的 ARC-Bench 适配器：调用主办方 `local_submit.py`，保存其原始 workspace 和 `local-result.json`，核对评测完成及用例计数，再写通用结果。
评测完成后的低分仍是有效结果；Runner 没有产出完整评测时是执行失败。

当前 WSL 长生成若在 attempt 内保存了 `monitor-generation.py`，用该 attempt 的 `generation-monitor.jsonl` 查看最后采样时间，再用 `pgrep -af '[m]onitor-generation.py'` 核对**同一路径**的监控进程仍在；旧采样行不能证明程序仍活着。只在确认该 attempt 没有现存监控进程且两题仍运行时，使用 attempt 的 Python 重新启动其原脚本并保留 stdout/stderr 到 `monitor.log`。脚本从各题 `run.json.started_at` 计算前十分钟每 180 秒、之后每 480 秒的间隔，接续不会重置观察窗；这只恢复采样，不重启生成或模型，也不代替原生 Pi/数据库核对。

两题运行由一次性 `run-experiment.py` 包装时，用户取消会使 `lab run` 返回非零；包装脚本不能仅凭子进程退出码把取消记作实验失败。新 attempt 的包装脚本应在非零返回后读取两题 `run.json.phase`：均为 `cancelled` 时记录外层 `cancelled` 并跳过评分，其余故障保留原错误。旧 attempt 的 `execution.json` 和脚本保持原样，报告同时展示外层错误与逐题取消事实。

本项目的本地容器构建、Agent 生成和 benchmark 评测统一在 WSL（`wsl.win-ws.localhost`）执行。
macOS 仅用于编辑、传输制品和查看结果，不为这些实验创建或启动 Colima。
从 macOS 用 `tar` 向 WSL 传源码时，设置 `COPYFILE_DISABLE=1` 并使用 `tar --no-xattrs`，避免将 `._*`、`.DS_Store` 或 `__MACOSX` 元数据送入独立源码快照和 Agent ZIP。打包入口也会过滤这些路径；已生成的旧 ZIP 保留原样，恢复包装时过滤其载荷与 manifest。
控制器、Docker daemon 和 workspace 必须使用经过实际 bind mount 验证的路径；能连接 Windows Docker Desktop socket 并不证明它能挂载 WSL 目录。
WSL 本轮使用独立 Docker Engine，不重启其他项目所在的 Docker Desktop。

长矩阵启动前检查 WSL 磁盘、容器内模型 API 和容器至 OTLP collector 的连接。
2026-09-23 的 WSL 观测为 IPv6 可用、IPv4 不通，当时独立 Docker Engine 的默认 bridge 已按 [Docker IPv6 文档](https://docs.docker.com/engine/daemon/ipv6/)启用 IPv6；只验证 WSL 宿主网络不足以证明容器能访问模型。
出现共享运行环境故障时停止派发，保留完整生成的应用；环境恢复后仅补评测，不把设施失败计作模型零分。
以下命令在 WSL 仓库中执行，先固定镜像与输入。
以下路径按仓库与 `factory26-official-local` 同级布置；Docker daemon 必须能访问 bind mount 的实际路径。现存 Runner 固定副本位于旧实验目录 `raw-baseline-20260923-wsl/runner`，新实验可显式引用，后续归档进 `runners/<revision>/` 时须记录实际来源身份。
基础镜像 digest 是 2026-09-23 核验的 `linux/amd64` 发布物；若换镜像，保留新 digest 和每个 run 的 `image_id`，不要将两者的分数视作同一环境。

```sh
LOCAL_ASSETS=../factory26-official-local
RUNNER="$LOCAL_ASSETS/raw-baseline-20260923-wsl/runner"
ARCBENCH_LOCAL_BASE_IMAGE=gyataro/arcbench-runner@sha256:40e003ed470dbd4c120b9019876ba77303d38dc8b34be7f6e313fe0563dd14de \
ARCBENCH_LOCAL_PLATFORM=linux/amd64 "$RUNNER/build-image.sh"

python3 -m lab.arc_bench.arc_matrix \
  --candidate historical-deepseek=runs/packages/iteration-throughput-boundary/pi-team-deepseek.zip \
  --candidate historical-mixed=runs/packages/iteration-throughput-boundary/pi-team-mixed.zip \
  --case arc-bench-lite/keep --case arc-bench-web/keep \
  --inputs-root "$LOCAL_ASSETS/platform-inputs" --runner "$RUNNER" \
  --image arcbench-local-submit:latest --workers 4 --separate-evaluation \
  --output "$LOCAL_ASSETS/experiments/example/manifest.json"

python3 -m lab run "$LOCAL_ASSETS/experiments/example/manifest.json" \
  --runs-root "$LOCAL_ASSETS/experiments/example/runs" --listen-host 0.0.0.0
```

真实模型可在 `arc_matrix.py` 指定直连模型的 `--env-file .secrets/arc-bench.env`，或指定新网关实例的 `--gateway-state <状态目录>` 并按需提供 `--env-file` 中的额外客户端变量。网关模式由每个 run 的临时凭据绑定请求，`--env-file` 不再同时直接传给 Runner；官方 Meter 凭据仍独立。模型 env 文件权限为 `600`，适配器临时合入 OTLP 参数后传给 Docker，运行结束删除临时副本。
`--prepare-only` 只准备两类输入与制品装配，不产生评分。
独立生成使用 `--separate-evaluation`，生成阶段不传公开测试；省略该选项的单阶段路径不作为独立生成基线。
矩阵中的每个执行都有独立 run ID；同一赛题、不同 variant 可以同时运行，`--workers` 只限制总并发，不按赛题或 variant 加锁。
`run.json` 保存输入快照哈希、适配器退出码、原始 Runner 结果和遥测取得情况；原始 Runner 退出码在 `result.runner_exit_code`。
整个 Runner workspace、stdout/stderr 和声明归档的产物留在 run 目录中，不自动清理。

运行期间，基础设施提供带 run 凭据的 OTLP/HTTP protobuf 接收端，支持 traces、logs 和 metrics。
通用 OTEL exporter 环境变量注入外部 Runner；适配器把端点改成容器可访问的 `host.docker.internal`，Linux 上若该名字不可用可通过 `arc_matrix.py --container-otlp-host <宿主机网关地址>` 指定。
Docker 容器要连到 Collector 时使用 `--listen-host 0.0.0.0`。
接收端只保存原始 OTLP 批次并按 run、时间和信号类型查询，不规定 Agent 上报语义；Harness 未上报时 `telemetry.status=absent`，不影响评分。

Runner 若将原始会话或失败 DOM 写到自身不可访问的临时目录，外层设施无法在销毁后补采，应让 Runner 或 Harness 在运行时写入持久 workspace。

已生成的 ARC 应用可用 `python3 -m lab.arc_bench evaluate <来源run> --output <新实验目录>` 单独复评。命令优先核验入口前发布的应用，沿用来源的冻结需求、测试、Runner 与镜像 ID；旧 run 缺测试快照时显式补 `--tests <已冻结测试目录>`。加 `--plan-only` 只准备新实验。复评通过 `--template` 和核验型 noop 消费应用，不运行生成 Agent，也不传模型凭据。改变测试范围或镜像会产生新的评测条件。

```sh
python3 -m lab show "$LOCAL_ASSETS/experiments/example/runs/<run-id>"
python3 -m lab telemetry "$LOCAL_ASSETS/experiments/example/runs/<run-id>" \
  --export "$LOCAL_ASSETS/experiments/example/analysis/exported-otlp"
```

`telemetry` 也接受 `--signal`、`--since`、`--until`、`--after-id`、`--until-id` 与 `--limit`；导出的 `.pb` 保持接收时的原始 OTLP protobuf 内容。`evidence <run> <相对路径> --offset N --bytes N` 按范围读取原始文件。`events`/`wait` 使用持久游标；`parallel` 可在执行中调整总槽位，`stop` 请求停止，`reconcile` 只核对已登记资源，`cleanup` 才显式清理。失联后不自动重跑已有尝试。
`--max-parallel` 接受任意正整数，设施不另设并发封顶。冻结目录保留内部符号链接，但拒绝指向快照外部的链接；ARC 矩阵接受输入目录提供的 `COMPETITION/TASK`，不维护赛题白名单或历史测试数量；是否完整评分依据本次 Runner 的终态与计数，适配器的 `--expected-tests` 仅在调用者明确指定时约束数量。
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

raw 实验可使用项目内 `.secrets/arc-bench.env` 的 `FACTORY26_API_KEY`；raw 入口把它提供给原生客户端，默认连接 `https://api.arc-bench.com/v1`，模型由各 ZIP 固定。

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

## 环境、源码运行与生成

开发环境、工具准备、各 variant 的源码入口和按改动选择检查统一见 [CONTRIBUTING](../../CONTRIBUTING.md)。
工具准备不安装 benchmark；目录运行不必先压 ZIP。
新活动路径不再使用 `factory.py bootstrap/run` 的共同配方。

每个 variant 的 main.py/run.py 自己拥有执行流程，agents/ 保存原生模型、角色与主指令。
SVC skill 的入口及相邻正文按需加载，不预载到 AGENTS.md，也不安装运行时 SVC CLI。
VV 组在 mixed 的基础上增加验收方法短指引；这些新源码不等同于旧冻结 ZIP。

调用者通过环境提供模型连接与凭据，或在源码开发时传入 base URL。
角色模型来自本 variant 原生材料，平台 MODEL 若提供必须匹配根角色。
生成证据位于输出 `.factory26/<run-id>`，包括 prompt、Braid request/state、原生配置和会话清单；成功从 delivery commit 导出应用，失败保留工作现场。

正式实验使用明确冻结的制品及官方 Runner。
两阶段 ARC 适配器在提交副本外包裹标准 Agent 入口，记录进程退出状态，随后冻结应用再评测；它不读取 raw 或 Braid 的私有终态文件。
原始包不改写。
Harness 应将自身未完成/失败表达为非零退出。

旧 run 的 analyze/show 继续读取其归档配置；不要以新 variant 重写旧结果。
新实验状态先用 `lab show` 查看任务、尝试、结果与证据入口；`lab.analysis.factory show` 才解释 ARC 生成、部署和评分。完整评分失败用例是有效结果，生成/评测设施中断不是零分。

## 按记录生产者查询

先确认拿到的是外层实验目录、Harness 内层目录还是平台 journal；它们的状态描述不同过程。
`lab.analysis.factory show`、`lab.analysis.run_feedback brief` 接受 Factory 生成目录或 lab 外层目录；平台 journal 继续由官网工具解释。

| 记录类型 | 从哪里开始 | 下一层证据与限制 |
| --- | --- | --- |
| 实验外层 run | `python3 -m lab show <run目录>` | 连接实际尝试、适配器结果与证据；`lab status` 读取原始记录，不推断评分。 |
| ARC/Factory 分析 | `python3 -m lab.analysis.factory show --run <run目录>` | 分别解释生成、部署、评分及已归档过程证据。 |
| Factory 团队生成 | `python3 -m lab.analysis.factory show --run <输出/.factory26/id>` | braid.log、delivery.json、braid-state、native/manifest.json；使用显式路径，不依赖根 runs 的自动发现。 |
| raw 生成 | 官方 workspace 的 `template/.arc/raw/` | 原生事件、stderr、身份与入口结果；外部评分在外层 Runner 结果中。 |
| 历史 Factory run | `python3 -m lab.analysis.run_feedback brief <旧run目录>` 或 factory show | 旧 status/outcome 格式与归档评测仍可读取，原始记录不迁移、不改写。 |
| Competition / Playground | 对应 journal、已保存 status 和平台原始结果 | 记录观察时间、远端 ID、完整评分与采集缺口；历史文件不证明远端当前状态。 |

Factory show 可以按原归档支持的评测和用例继续定位：

```sh
python3 -m lab.analysis.factory show --run /path/to/factory-run --case REQ-2.2
python3 -m lab.analysis.factory show --run /path/to/factory-run --eval <evaluation-id> --json
```

`list/show` 只读已有运行。
生成失败时，show 从哈希核实的 Pi 归档提取末条 assistant 的终止原因与记录位置；不展示完整正文，不回溯已恢复或已替代会话的旧错误，损坏或关联不唯一时明确未知。
默认 show 先呈现状态、失败和相关入口；指定 --case 时优先展示该用例。
全部元数据、路径、会话和 SVC evidence 映射保留在 --json，避免默认输出铺满文件列表。
生成状态、所选评测和 SVC coverage 分别展示；最新本地评测失败时不回退到旧分数。
用例入口展开有长度标记的错误、从官方 error-context 定向提取的页面片段及行号，以及重定位后的本地截图、视频和 trace。
页面事实不自动等于因果结论。
历史数据缺少阶段或退出码时显示未知；旧 variant 根据配置推导并显式标记。

浏览多个归档时，可以生成本机静态诊断页：

```sh
python3 -m lab.analysis.run_viewer
open runs/viewer/index.html
```

页面发现 runs 下嵌套的 Factory/lab 外层记录，以及 Competition hosted 控制器和 Playground 的归档。
进入实验目录后不扫描其 inputs、工具资源和应用依赖；外层详情直接链接嵌套 .factory26、raw 会话、生成应用与评分报告。
例如 `python3 -m lab.analysis.run_viewer --root ../factory26-official-local --output ../factory26-official-local/experiments/<id>/analysis/viewer` 可将相邻实验的页面放在本次分析目录。默认输出仍为输入根的 `runs/viewer`。
矩阵、批次、派生 `analysis/run.json` 不算独立 run。
列表可搜索 run ID、组合和状态；详情分开展示生成/平台状态、完整评分、逐用例错误、执行过程和可打开的归档证据。
Competition 的 `FAILED` 可以带有效低分，运行中、生成失败和评测中断则显示评分未知。

Factory 过程按物理会话展示 Agent 的可见说明、工具调用与返回状态，标出 Issue/PR、turn、原生文件及行号；只有 manifest 哈希核实后才将工作项归属标为可信。
旧 run 没有 manifest 时可查看未核实的原生过程，缺少会话或格式不可读时显示证据缺口。
多个工作项可能并发，页面顺序不代表单一因果链。
Competition 和 Playground 展示已归档的 `runner_events`，按事件 ID 去重并把心跳单独计数；平台未归档 Agent 内部工具调用时，不能从阶段事件推断其操作。
两类平台事件时间保留原值，不能据页面推断跨来源的精确时差。

网页是生成时的快照，不轮询平台；run 更新后重跑上述命令。
页面只展示有界摘要，不内嵌原始提示词、推理和完整工具输出；摘要与原始日志仍可能包含敏感内容，分享前应检查。
生成文件位于被 Git 忽略的 `runs/viewer/`，源归档保持不变。

各生产者的阶段字段以其实际记录为准。
团队入口记录 prepared、braid 及结束阶段，旧生成和评测入口还有 setup、cleanup、install、build、health、tests 等记录，不能用一套阶段列表套用所有 run。
失败保留 `failed_phase`，中断明确标记。
Braid 生成失败时另存 `recovery-workspace.json` 并保留原始工作目录及 Git common repo，以免销毁恢复依据；成功后清理。
应用终态先持久化；原生会话缺少规范 header 时另存 `unparsed_native` 原始文件，标记归档错误，不伪造会话身份或覆盖应用结果。
阶段更新时间表示最后一次阶段变化，不代表进程仍存活；服务不健康时可由阶段日志定位。

历史远程评测以 `remote-evaluations/<evaluation-id>.json` 保存每次请求的完整观测，`remote-evaluation.json` 仅作为最近观测的兼容入口。
请求在启动前分配明确 ID，区分连接、传输、远端运行和下载，每 180 秒获取该 ID 的 summary；SSH 进程退出立即返回，不额外等一个观察周期。
下载后核对 run、benchmark 和冻结应用哈希，不按目录差集猜测执行。
观测时间与观测失败单独保存，下载后用终态 summary 收口；断线不能被当成远程零分或停止成功。
`show` 同时保留最新本地评测与远端状态，不把暂存远端状态当作已下载成绩。

## 等待、反馈与交接

一次已获授权的长实验交给较低成本子 Agent 持有运行命令和等待，主 Agent 处理其他工作或等待完成消息。
交接只需本次目标、配置与证据路径、完成条件、允许操作和停止条件。
子 Agent 根据程序摘要判断哪些证据值得展开，返回结果、依据、未知和需要决策的事项；不转发整段日志。
每次实验结束先向用户汇报，由用户决定下一轮，不自动重跑。

旧 Factory `run` 的后台观察器每 180 秒读取已有事件并保存 `feedback.json`，相同类别错误不重复输出，执行退出时立即刷新终态。
错误类别与重试是观测事实，可能已经恢复；不输出不能指导判断的工具完成计数。
整体状态以 `outcome.json` 为准，错误片段只用于定向取证。
没有完整结果的旧 run 明确标记 `scope=generation`，不能据此声称 bench 已完成。

主会话不定时读取原始流，也不通过每三分钟唤醒一次模型来模拟事件通知。
当前使用子 Agent 的原生完成消息回传，验收范围限于主会话仍活跃的情况；尚未验证主会话结束或 App 关闭后的唤醒。
lab.run 应等待执行进程完成并读取持久结果；下面的只读等待命令只适用于旧 Factory 状态格式：

```sh
python3 -m lab.analysis.run_feedback watch runs/<run-id>
python3 -m lab.analysis.run_feedback watch runs/<run-id> --after-event <已处理的event_id>
```

独立 `watch` 没有被观测进程的句柄，因此以至少 180 秒的间隔检查文件；发现终态后立即返回。
已处理的终态身份保持静默，这用于去重，不保证跨进程消息恰好投递一次。
停止等待不等于停止远端实验。

## 证据与分析

证据按上表的生产者保存。
旧 Factory `runs/<run-id>/` 与新团队输出 `.factory26/<id>` 均可包含配置、提示、哈希、原生 session 和生成日志；外部评测的 JSON、HTML、截图、视频与 trace 位于对应评测目录，不保证与生成记录同层。
新入口的材料哈希也不等于旧入口保存的完整源码快照。
`native/manifest.json` 将每个物理 session 与 provider、逻辑 group、工作项、turn、归档输入及内容哈希对应；被替换会话的用量仍计入。
缺失证据保留身份及错误，不能用最新文件代替。
退出时清理 Agent 与应用进程组；报告中的相对产物链接依赖本机保留的 run，不会随源码自动分发。

`python3 -m lab.analysis.factory analyze --run <Factory生成目录>` 为每个原生会话分别导出 `analysis/<序号>-<来源指纹>/evidence-v4.zip`，保存 overview、模型 usage 和 provenance。
来源指纹包含原生内容、实际 provider 和 exporter；缓存使用前核对原生清单与产物哈希。
相同来源复用已完成分析；来源变化重新导出，全部查询成功后才发布目录，失败不覆盖已有分析。
历史目录保持原样。
用量是否汇总及覆盖哪些会话应以该生产者的实际记录为准，缺项不能当作零；不要从入口名称推断统计完整。
进一步检查可使用 `query`、`read`；请求格式通过命令帮助与 `--schema` 查询：

```sh
.venv/bin/svc analysis query --help
.venv/bin/svc analysis read --help
.venv/bin/svc status --json
.venv/bin/svc lookup --path specs/
```

svc 负责证据导航，不自动判定应用质量。
标准 Pi session 缺少执行终态，可能使 overview 显示 `partial`；应结合覆盖声明、运行器退出码与最终模型停止原因判断，不能把 `partial` 一概解释成内容丢失。
实际费用未知时保持 null，不用客户端估算替代比赛账单。

## 历史单核心与远程评测入口

活动团队 Harness 只从 `variants/<name>/main.py` 进入；已退役的 shared-config 入口不再提供默认配置。
新活动 variant 不经共同 resolver，也不使用旧 batch。

旧 run 的 list、show 和 analyze 保留；旧 eval 和 SSH 评测路径已删除，新的复评显式向官方 Runner 提供既有应用。
生成时的配置和制品身份不改写。
新本地实验按照前面的官方 Runner 路径执行，不复制跨平台 node_modules 或 venv。

## SVC 与 braid 的共同开发

`sources/svc`、`sources/braid` 是各自有 origin 和 main 分支的独立 Git 仓库，由父仓库忽略。
`sources/svc` 是参赛 Agent 的 SVC 源码；相邻 `~/Development/svc` 保留完整通用 Corpus，供本项目开发和独立 analysis 使用，两棵工作树的改动不会自动同步。
`sources/braid` 是当前参赛 Braid 的源码修改位置。
`third_party/arc-bench` 只保存固定评测器。
旧 `third_party/svc`、`third_party/braid` 副本为历史运行与构建缓存保留，当前生成不再读取其源码。

```sh
git -C sources/svc status --short
git -C sources/braid status --short
cargo build --locked --manifest-path sources/braid/Cargo.toml
```

参赛 SVC 或 Braid 的改动直接修改 `sources/` 中对应源码；Braid 改动构建后观察实际调用结果，SVC 内容改动由显式源码运行或下一次制品装配取用。
Corpus 不设内容测试；新 run 仍需独立实验授权。
通用 SVC 的改动保留在 `~/Development/svc`；只有明确适用于参赛 Agent 的内容才移入 `sources/svc`。
更新上游时在各自仓库显式 fetch/merge，处理本地改动后重建。
父仓库 status 不会列出这些独立仓库的改动，提交也应在各自仓库明确执行。

[sources.py](../../scripts/sources.py) 只负责独立仓库的 export/restore，不再维护 Braid 构建戳或强制全树哈希匹配。
Cargo 直接负责增量构建；完整的开发 SVC 安装与跨机器交接命令见 [CONTRIBUTING](../../CONTRIBUTING.md)。
历史 run 的 sources/ 源码归档原样保留；新 variant 记录实际代码/材料哈希、原生配置与包载荷，不给旧 runs 补写新版身份。
[SVC 技能集合](../../sources/svc/README.md) 由 SVC 自身维护；每个技能有自己的入口、references 和按需模板。
Factory 的当前技能目录链接到该集合，运行与打包使用通用 skill 复制操作，制品不依赖此链接；历史 `harness/skills/svc` 保留给归档消费者。接线不进入 Braid 控制协议。

默认 analyze 使用开发 `.venv/bin/svc`；已有 `--svc-source <path>` 可使用具备 PDM 环境的源码工作树作独立诊断，它记录实际 HEAD 和 CLI 源码哈希，不替换运行时 Corpus，也不改写旧分析。
SVC analysis 是开发工具，分析没有 SVC 注入的原始 core run 也完全有效。

若要追踪生成期间已经出现的工具错误，先用稳定短语 match，再用返回的 ref 做 trace：

```sh
printf '%s\n' '{"version":3,"intent":"match","predicates":{"kinds":["tool_result"],"text_terms":["稳定错误短语"]}}' |
  .venv/bin/svc analysis query --input <evidence-v4.zip> --request -
printf '%s\n' '{"version":3,"intent":"trace","event":<match返回的ref对象>}' |
  .venv/bin/svc analysis query --input <evidence-v4.zip> --request -
```

trace 提供关联的标准化调用上下文；只有需要精确内容恢复或原生审计时才用 read。
外部评测在生成之后发生，其错误未必存在于生成 transcript 中，不能把用例 ID 强行关联到某次工具调用。
应先从用例证据判断应用缺口，再回看当时相关实现或自检行为。

## 历史 Playground 操作

[playground.py](../../lab/arc_bench/playground.py) 使用网站 HTTP 接口完成登录、上传、运行和证据收集，日常实验不需要浏览器。
首次运行 `python3 -m lab.arc_bench.playground login`，交互输入网站邮箱和密码；也可以通过 `--credentials ~/.config/factory26/playground-login.json` 读取权限为 600 的 JSON 文件（email、password）。
登录验证后保存权限为 600 的 `~/.config/factory26/playground.cookies.txt`。
网站会话与比赛模型密钥分开保管，登录信息不进入仓库或命令参数。

```sh
python3 -m lab.arc_bench.playground whoami
python3 -m lab.arc_bench.playground requirements --catalog benchmark
python3 -m lab.arc_bench.playground submit --practice --package /path/to/agent.zip --config /path/to/model-config.json --requirement keep --name factory-keep
python3 -m lab.arc_bench.playground watch <run-id>
python3 -m lab.arc_bench.playground collect <run-id>
```

上传前必须准备符合平台契约的 Python Agent ZIP，根目录包含 main.py 与 requirements.txt。
`submit` 要求通过 `--config` 显式提供网关和模型，并使用仓库外比赛密钥；配置不会改变 ZIP 已打包的核心或工作流。
清单明确标记 configuration_scope=model-settings-only，包身份以 SHA256 为准。
只有无模型探针使用 `--offline`，该选项传非凭据占位符。
包哈希、已确认的 submission/run ID 与执行阶段记录在 `runs/playground/upload-*/submission.json`，便于写请求失败后查明已经完成哪一步；传输结果不明时不自动重复 POST。

续跑、启动和取消只接受本工具清单中明确记录为 practice/probe 的 ID；未知、正式和缺少分类的历史 ID 请通过平台管理。

同一包重跑使用 `python3 -m lab.arc_bench.playground run --submission <submission-id> --requirement <requirement-id>`，避免重复上传。
已创建但尚未启动的 run 使用 `start <run-id>`；明确结束云端执行使用 `cancel <run-id>`。
中断本地 `watch` 只停止等待，不改变云端 run。
401 表示需要重新登录。

`status <run-id> --saved` 可只读重放已归档状态，不联网、不改旧产物。
摘要分开列出最近有效事件、心跳和采集时刻，缺少观测时间时明确未知；不使用文件 mtime 猜测。
traceability 没有显式记录时显示未建立关联，不能由 SDK 自报 passed 推导外部评测成功。
`status` 输出阶段摘要，`watch` 默认每 180 秒读取状态和增量日志，只在 PASSED、FAILED、CANCELLED 或 PAUSED 时收集证据、输出摘要并退出；可用 `--after-event` 跳过已处理的同一结果。
运行中无变化保持静默，PAUSED 表示需介入而非完成；运行中的计数不作为完整成绩。
观测超过 360 秒标为 stale，不据此推断远端已经停止。
平台曾将实际耗时返回为 0，因此终态摘要用 started_at/finished_at 计算 elapsed_seconds，并汇总测试状态；原始时长字段保留在 status.json。
`collect` 将状态、日志游标与分块、traceability 和 commit history 保存到 `runs/playground/<run-id>/`。
JSON 的凭据字段会脱敏，但原始日志仍可能包含 Agent 工具输出，继续由 Git 忽略。

这些接口来自当时的网站公开前端，可能随平台更新；此前实际完成网站登录、上传、启动、Demo 单项评测和证据下载。
云端环境与脚本实测见[并发与 API 报告](../../reports/2026-09-20-playground-concurrency.md)，早期协议调查见[开发闭环调查](../../reports/2026-09-20-development-loop.md)。
Playground 与 Competition、本地评测具有不同身份，具体参赛包的成绩以其冻结身份和正式结果为准。

## 旧执行入口与历史记录

共同配置的 factory.py generate/run/bootstrap/eval/batch 及旧 shared submission 入口已删除，不再用旧 multi-agent-lite 清单启动新矩阵。
新矩阵使用 `lab.arc_bench.arc_matrix` 和 `lab.run`；当前 Lite 配方见 [pi-braid 矩阵](../../experiments/pi-braid-lite/README.md)。[旧 multi-agent-lite 定义](../../experiments/archive/multi-agent-lite.json)、batch.json、inputs.json 及各 run 保留为历史证据，不迁移成新的运行身份。

旧评测并发与模型探测工具 concurrency.py 已删除。
其历史记录位于 `runs/concurrency/`，曾有的并发观测只支持相应应用、接口和当时环境，不能推导当前吞吐或模型额度。
该旧探针曾把 429 归类为限流且未保留完整响应正文，不能用其历史摘要区分额度耗尽和并发限制。
旧平台与工具调查见 [2026-09-20 记录](../../reports/2026-09-20-playground-concurrency.md)，不是当前机器环境承诺。


### 项目内私密凭据

自购模型凭据放在项目根目录 `.secrets/models.env`，目录权限700、文件权限600，整个目录由Git忽略。该私有文件预留Kimi、GLM、DeepSeek各自的API_KEY与BASE_URL；这些名称是待接入的配置约定，当前入口不会自动加载它。不要将该目录加入Agent制品、输入快照或交接源码归档。正式官方凭据使用独立的 `.secrets/arc-bench.env`，不混入自购配置；已有历史密钥不自动迁移。

macOS工作树中的文件供用户填写；实验仍只在WSL运行。未来运行时需显式将所需配置安全放入WSL项目的同名私有目录，未配置前不得回退官方密钥。不要将自购密钥作为官方Runner的OPENAI_API_KEY传入：该Runner会用它登录官方Meter。此处记录凭据存放约定，不代表多供应商运行接线已经完成。

## 活动 variant 的预打包环境

runtime 随包提供 pnpm、portless、agent-browser、Playwright 及其命令入口，依赖版本以包内 npm lock 为准。活动 variant 为同次运行的成员和接续设置共同的 npm cache 与 pnpm store，位于 `work/cache/`；它们按需积累下载，不预装应用框架或业务依赖，也不要求离线安装。
浏览器操作默认使用 agent-browser。runtime 保留已安装的 Playwright Test 与配套 Chromium，按需用于可重复检查；两者使用同一浏览器二进制，各自管理会话。
`BROWSER_CHECK_NODE_MODULES` 指向已安装的 Node 依赖，`BROWSER_EXECUTABLE_PATH` 指向可移植浏览器入口；按应用检查方式使用，不强制配置模板或独立验收技能。
检查目录的 node_modules 链接由应用自己的 .gitignore 排除，不成为交付依赖。最终验收使用可重复的应用测试或脚本，原始错误、trace、候选提交和运行条件保留在该次工作证据中。
原有冻结 runtime 和 ZIP 不随此修改更新。

## 为新实验命名与关联来源

先在所属任务登记问题、矩阵与执行次数，规则和已有记录入口见 [实验导航](../../experiments/README.md)。不要更名旧 ZIP、journal、官网 submission 或 run 来套用新规则。

本地矩阵用 `--candidate CASE=ZIP` 表示实验配置行，真实 variant 从包内读取；可多次传入同一个 variant 的不同 ZIP。原 `--case COMPETITION/TASK` 继续选题，`--experiment-key` 写入稳定标签。`--variant NAME=ZIP` 是兼容的身份声明，若包内名称不同会拒绝，不能用于给旧包伪造新 variant。

```sh
python3 -m lab.arc_bench.arc_matrix \
  --candidate coordinator=/path/to/frozen-agent.zip \
  --experiment-key <已登记实验编号> \
  --case arc-bench-lite/keep --case arc-bench-lite/bookstack \
  --inputs-root /path/to/platform-inputs --runner /path/to/runner \
  --image <镜像> --separate-evaluation --output /path/to/recipe.json
```

配方 job ID 包含 candidate、competition 和 task。执行前按这些 ID 准备 `--run-labels <JSON文件>`；初次执行和 `lab retry` 都显式给本次名称，见 [Lab 示例](../../lab/README.md#实验标签与每次执行的名称)。原样复评入口 `lab.arc_bench evaluate` 同样接受 `--experiment-key`、`--case` 和 `--run-labels`，其 job ID 为 `evaluation`。只准备时用 `--plan-only`，随后由 lab 运行新实验。

Competition 的 `prepare` 接受 `--experiment-key`、`--case` 和 `--run-names <JSON文件>`；后者形如 `{"github":"<实验>--<case>--github--g01","sheet":"<实验>--<case>--sheet--g01"}`。`--name` 仍是多题 submission 的实际 display name。新元信息冻结在 inputs 与逐题状态，再次 prepare 必须一致；resume/read 不产生新名称。旧记录缺字段保持缺失，不回填冻结事实，单 snapshot/task 的运行限制也不改变。

Playground 的练习 submit/run 接受 `--experiment-key`、`--case`、`--run-name`。上传记录保存实际 display name；复用 submission 时继承包和应用来源，run_name 只取本次显式参数，省略则无名称。以上参数不改变自费模式、练习入口限制或实验授权。

查询使用 `lab show ... --json`、Competition 的 `--json` 或 Playground `status <run-id> --saved`，名称与实际 ID 同时展示。新来源字段沿既有 replay manifest/source_application 保存；一个多题重放包可能有多个 variant。应用摘要须连同算法解释，缺少算法的历史值不能直接与新版摘要比较。

## 实验恢复与反馈循环

选择执行方式时，先区分三类运行：

| 方式 | 输入与产出 | 结果归属 |
| --- | --- | --- |
| 新 Harness 实验 | 冻结 Harness、需求和模型条件，重新生成应用，再评分 | 本次冻结 Harness 的完整执行结果。 |
| 工作区断点恢复 | 保留原始 ZIP，在副本中恢复代码、会话和协作状态，完成必要的剩余工作 | 原始运行加明确恢复改动后的结果，不是原版本独立完成。 |
| 完成应用重放 | 冻结已完成的应用，用既有 replay 打包入口部署评分，不再调用生成 Harness | 指定应用版本的评分；不能冒称一次新的端到端生成成绩。 |

已完成的 Braid 工作区用 `python3 scripts/package_completed_recovery.py --source-run-id <旧run> --workspace <官网工作区ZIP> --base-package <旧冻结包> --braid <修复版Linux二进制> --braid-source <对应源码快照> --output <新包>` 准备。新包携带原工作区与哈希；入口恢复原 Braid run、确认所有工作项终态，再导出旧 `main`。每个新包使用独立的 Competition journal 和 `self_funded`，旧 run 不会原地恢复；具体来源及身份见当轮 packet。默认模式发现开放工作项会拒绝生成，防止一次重评意外调用模型。

自费迭代遇到未完成的生成中断时，保留原始 ZIP 和完整 Braid 工作区。打包命令添加 `--continue-generation` 可准备未完成工作区的接续包；它恢复原模型与工具环境、Git 索引及保留文件，调用原 `braid local` 请求，不改数据库生命周期。此模式只用于来源执行环境已经停止的快照；恢复入口显式调用 `braid local REQUEST --offline-resume`，由 Braid 撤销旧执行身份、修复输入重放并准备会话，Factory 不修改数据库。当前代码已编译，完整官网验收状态以实验设施 packet 为准；已有 g03–g05 的手写包不是该入口的验收。原始证据保持只读，接续时新增的通知要标明来源，不能改写成历史上已经送达。

热恢复先确定错误首次出现及开始大规模扩散的时间，优先选择扩散前最近的可恢复检查点，避免把已受影响的上下文和协作状态原样带入修复后的运行。核对检查点内应用与 Git、Braid 数据库和原生会话的时间及相互引用；单独回退应用提交不能代表整个运行已回退。保留当前现场，记录选择依据、会丢弃的有效进度以及缺失材料。没有可确认的较早检查点时，明确记录限制，再按已授权范围接续。

需要把新的技能和原生指令应用于半成品时，使用包含新 variant 材料的 `--base-package`，并同时指定 `--continue-generation --refresh-native-materials`。恢复入口重建宿主拥有的 skills、capabilities 和成员指令，保留旧材料副本、应用工作区、协作记录和原模型路由；Braid 在离线恢复边界重建受影响的原生会话。仅替换二进制而不刷新材料，不代表新技能或提示词已生效。原执行须先停止，每次接续使用新的包和运行目录。


接续入口从工作区 ZIP 还原 Unix 文件权限和符号链接，使用包内 Pi 时间回调与 OTLP 接收器追加本次采集。Braid 结束后重新归档原生会话，原 ZIP 自带的 `native/` 先保存在 `recovery-source-native-<时间戳>/`；`recovery-diagnostics.json` 分别记录采集、归档和清理错误。清理失败仍阻断交付。旧来源和新接续的采集时间段应分开解读，不能把恢复后新增记录当作旧运行的当时状态。

应用生成完成后冻结交付版本，通过官网自费应用重放取得官方评分；本地模拟分数和启动检查不替代官网评分。工作区接续与应用重放分别记录来源，不能把重放分数冒称为一次新的端到端生成成绩。正式参赛提交从冻结 Harness 和需求重新生成，以测量完整执行；自费迭代不因此丢弃可续接的工作区。

监控由程序与一次性审查者分工。程序run 启动后前 10 分钟每 3 分钟、随后每 8 分钟读取状态和阶段；运行中默认不下载整个工作区，也不调用模型。终态时下载原始工作区，保存总分、阶段及身份，然后退出；终态下载失败另记 `evidence_errors` 并随终态告警退出，不把缺证据当已收齐，也不因不存在的失败工作区无限等待。官网工作区打包下载允许 10 分钟，覆盖通常的 2–3 分钟。需要语义监督时明确添加 `--review`，每批下载后启动读取 [固定审查指令](../../agents/run-monitor.md) 的一次性审查者。审查者不计时或轮询。

下载、审查进程启动、审查结果保存、告警提交与取消确认分别留收据。文件哈希变化、token 增长不等于进展；下载失败不等于实验失败；通知系统接受提醒不代表人已看到。审查失败必须成为明确告警，不能把 needs_review 文件视作已经有人处理。每批保存提示词版本、模型、输入证据路径与结论，避免并发重复审查同一批。

短题暴露通用缺陷时，先保留全部现场并确定原因，再做有针对性的修复验证。在已授权的官网并行实验中，可按当轮规则取消同轮未终态的 Hackathon 运行；取消需要实际请求及远端状态确认。本地断点恢复应保留进度、受控暂停后续接，不机械沿用官网取消策略，也不在活动进程中无记录更换二进制。合理等待、外部故障与 Harness 缺陷分别处理，禁止无依据反复重生成。

每轮在 task packet 登记题目、模型、来源、费用模式、调度、告警消费者和完成条件。官网默认使用 API、`self_funded` 自带 key、非参赛，不占比赛额度；策略可复用不等于无限付费授权。

执行入口：`python3 -m lab.arc_bench.hosted_monitor <证据目录> --journal <Competition状态目录> [--journal <另一个状态目录>]`。省略 `--journal` 时沿用 `<目录>/hackathon` 或 `arc-bench-lite` 布局。默认只观察；已有明确取消授权且使用旧目录布局时，才可添加 `--cancel-on-lite-failure`。`FAILED` 但评分完成不触发联动取消；明确的生成/部署失败或审查者有证据的阻塞结论才进入取消路径。当前本地恢复使用任务内的 `runs/e20260927-01-handoff/local-monitor.py`，不把一次恢复适配升级为全局框架。
