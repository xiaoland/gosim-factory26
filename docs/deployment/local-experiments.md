# ARC 本地实验

本文说明冻结 Harness 的本地生成与评分，适用于 Lite/Web 及需求公开的 Hackathon。它不调用官网；官网评分和应用重放见[平台操作](competition.md)与[恢复手册](recovery.md)。题目、制品、并发和完成条件先在所属 packet 登记，命名规则见[实验导航](../../experiments/README.md)。

## 准备 Runner 与运行条件

[arc_matrix.py](../../lab/arc_bench/arc_matrix.py) 将冻结 Agent ZIP 与 Lite/Web 任务展开为可并行的 job；[lab](../../lab/README.md) 在实验内共享冻结输入、保存实际控制器源码，为每个 job 建立独立尝试并运行指定命令。
它只要求外部 Runner 写入 `workspace/experiment-result.json`，不导入 Factory、Braid 或 Agent 会话格式。
[arc_bench_adapter.py](../../lab/arc_bench/arc_bench_adapter.py) 是单独的 ARC-Bench 适配器：调用主办方 `local_submit.py`，保存其原始 workspace 和 `local-result.json`，核对评测完成及用例计数，再写通用结果。
评测完成后的低分仍是有效结果；Runner 没有产出完整评测时是执行失败。

本项目的本地容器构建、Agent 生成和 benchmark 评测统一在 WSL（`wsl.win-ws.localhost`）执行。
macOS 仅用于编辑、传输制品和查看结果，不为这些实验创建或启动 Colima。
从 macOS 用 `tar` 向 WSL 传源码时，设置 `COPYFILE_DISABLE=1` 并使用 `tar --no-xattrs`，避免将 `._*`、`.DS_Store` 或 `__MACOSX` 元数据送入独立源码快照和 Agent ZIP。打包入口也会过滤这些路径；已生成的旧 ZIP 保留原样，恢复包装时过滤其载荷与 manifest。
控制器、Docker daemon 和 workspace 必须使用经过实际 bind mount 验证的路径；能连接 Windows Docker Desktop socket 并不证明它能挂载 WSL 目录。
既有实验使用 WSL 独立 Docker Engine；操作前核对本轮实际 daemon，不重启其他项目的 Docker Desktop。

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
  --candidate candidate=/path/to/frozen-agent.zip \
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
当前主线将 Runner workspace、stdout/stderr 和声明归档的产物留在 run 目录中。存储生命周期分支的归档回执和 GC 尚未合入，不能依据 completed 或目录名自行删除恢复依赖。

运行期间，基础设施提供带 run 凭据的 OTLP/HTTP protobuf 接收端，支持 traces、logs 和 metrics。
通用 OTEL exporter 环境变量注入外部 Runner；适配器把端点改成容器可访问的 `host.docker.internal`，Linux 上若该名字不可用可通过 `arc_matrix.py --container-otlp-host <宿主机网关地址>` 指定。
Docker 容器要连到 Collector 时使用 `--listen-host 0.0.0.0`。
接收端只保存原始 OTLP 批次并按 run、时间和信号类型查询，不规定 Agent 上报语义；Harness 未上报时 `telemetry.status=absent`，不影响评分。

Runner 若将原始会话或失败 DOM 写到自身不可访问的临时目录，外层设施无法在销毁后补采，应让 Runner 或 Harness 在运行时写入持久 workspace。

## 冻结应用的本地复评

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

## Raw Pi/Codex 基线

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

本地生成的 `arc_bench_adapter.py --memory 4g --cpus 2` 将资源参数原样传给官方 local runner；未指定时沿用 runner 默认值。
记录资源配额与 cgroup 压力后再比较耗时，不把不同资源条件下的变化单独归功于模型或 Harness。

## 工具、浏览器与应用验收

runtime 随包提供 pnpm、portless、agent-browser、Playwright 及其命令入口，依赖版本以包内 npm lock 为准。活动 variant 为同次运行的成员和接续设置共同的 npm cache 与 pnpm store，位于 `work/cache/`；它们按需积累下载，不预装应用框架或业务依赖，也不要求离线安装。
浏览器操作默认使用 agent-browser。runtime 保留已安装的 Playwright Test 与配套 Chromium，按需用于可重复检查；两者使用同一浏览器二进制，各自管理会话。
`BROWSER_CHECK_NODE_MODULES` 指向已安装的 Node 依赖，`BROWSER_EXECUTABLE_PATH` 指向可移植浏览器入口；按应用检查方式使用，不强制配置模板或独立验收技能。
检查目录的 node_modules 链接由应用自己的 .gitignore 排除，不成为交付依赖。最终验收使用可重复的应用测试或脚本，原始错误、trace、候选提交和运行条件保留在该次工作证据中。
原有冻结 runtime 和 ZIP 不随此修改更新。

## 冻结输入与新一次执行

`arc_matrix --candidate CASE=ZIP` 将本轮配置行与包内真实 variant 区分；同一 variant 的不同冻结 ZIP 可作为不同 candidate。兼容参数 `--variant NAME=ZIP` 是身份声明，包内已知名称不一致时拒绝运行，不能用于伪造历史身份。`--experiment-key` 标记已登记实验；题目继续用 `--case COMPETITION/TASK` 选择。

配方 job ID 包含 candidate、competition 和 task。初次执行及 `lab retry` 均显式传本次 `--run-labels <JSON文件>`，不继承上次运行名；稳定标签随配方冻结。完整参数和例子见 [Lab](../../lab/README.md#实验标签与每次执行的名称)。原样复评的 job ID 为 `evaluation`，同样保存实验、case 和本次执行标签。

旧 `local_runner.py`、`platform_public_run.py` 及共同配置的 factory.py generate/run/bootstrap/eval/batch 已退役；旧 manifest 和 run 保持原样，不能因改名成为新实验。raw 的具体配置与资格记录见[原始基线任务](../../tasks/raw-core-local-baseline/packet.md)，归档原生四配置的来源与运行方式见 [Hackathon](hackathon.md)。
