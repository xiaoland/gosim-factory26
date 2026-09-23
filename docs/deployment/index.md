# 本地运行与证据

本文维护运行、证据查询和恢复操作。
产品规则见 [PRD](../prd/index.md)，组件责任与终态含义见[技术说明](../product-tdd/index.md)，开发准备见 [CONTRIBUTING](../../CONTRIBUTING.md)。
实验选择以当次任务与冻结清单为准；文中的历史观测不代表平台或机器此刻的状态。

## 参赛包与平台边界

参赛包复用本项目的 Braid + SVC 生成、Git 交付冻结和原生证据归档。
每个 ZIP 固定一个 variant 及其全部能力材料；根目录 `main.py` 接受平台传入的需求，不读取本地 benchmark，也不执行评测：

```sh
python3 scripts/package_agent.py --variant pi-team-mixed --output runs/packages/pi-team-mixed.zip --docker-context arcbox-win
# 以下命令在解压后的 ZIP 根目录执行，并由调用环境提供模型变量。
python3 main.py /path/to/requirements --output-dir /path/to/output
```

构建需要可用的 Linux x86_64 Docker daemon；`--docker-context` 可省略以使用当前 context。
脚本只发送指定构建输入，不上传整个开发目录。
Braid 从当前 `sources/braid` 构建；SVC 从当前 `sources/svc/corpus` 作为技能材料冻结，不构建或安装 CLI；raw Codex 的 LiteLLM Python 依赖用 Linux CPython 3.12 安装到包内目录。
Node、所选核心、Chrome及其NSS动态模块、常用进程工具与非系统动态库均在构建时安装并随包提供；Pi 需要 Node >=22.19，不能直接使用平台原有 Node 20。
精确工具版本由 [Dockerfile](../../submission/Dockerfile) 固定，实际文件哈希、源码身份和执行权限写入 `package-manifest.json`。
npm lock 和 Python 依赖清单随 runtime 保留。
重复构建不覆盖已有 ZIP；构建时无需模型 key，比赛运行时无需 clone 源码、Cargo 或开发者 venv。

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

官方 Competition 的自动化入口为 [competition.py](../../scripts/competition.py)，统一记录 ZIP identity、submission snapshot、task run、日志游标与终态收集。
`prepare` 不写平台；其余写入按批准的实验范围执行，任何 POST 结果不确定都先保留 journal，再只读核查，不盲重试。
Playground 仍只用于显式 practice，不混入 Competition 结果。

同一比赛只允许最新 snapshot 承接新任务。
历史混合矩阵由 [official_matrix.py](../../scripts/official_matrix.py) 运行：四个冻结 variant 依次推进；每个 variant 的 Lite 两题与 Web 六题由两个 Competition controller 并行执行，各比赛内部逐题运行。
两侧全部取得终态、完整评分及 manifest 声明的测试数，才上传下一 variant。
已完成一侧在重启后复用原 journal，不重复 POST；历史 Lite 单比赛 manifest 仍可恢复。
客户端并行请求不能证明官网同时分配执行槽，报告应保存各 run 的实际状态和时间。
两场比赛读取相同 ZIP bytes，manifest 绑定 SHA256；完整低分计入结果，设施失败不计为评分。
远端没有可用推送接口时，后台脚本从 180 秒间隔采集。

Lite/Web 的隔离输入位于仓库同级 `factory26-official-local/platform-inputs/<competition>/<task>/`，逐题保存公开需求、测试、素材与来源哈希。
主办方现已发布 [本地模拟 Runner](https://github.com/code-philia/hackathon-local-simulation/tree/4e62690ef0af48601150f248e1f993a300533357) 所需的生产基础镜像；原先只支持 Lite 的 `local_runner.py` 和官网矩阵内的本地队列已移除。
同级 `platform_public_run.py` 是早期的公开测试诊断入口，依赖 Factory 实现，也不作为新实验设施的执行底座。

## Lite/Web 本地实验

[arc_matrix.py](../../scripts/arc_matrix.py) 将冻结 Agent ZIP 与 Lite/Web 任务展开为可并行的 job；[local_experiment.py](../../scripts/local_experiment.py) 为每个 job 冻结输入、建立独立 run 目录并运行指定命令。
它只要求外部 Runner 写入 `workspace/experiment-result.json`，不导入 Factory、Braid 或 Agent 会话格式。
[arc_bench_adapter.py](../../scripts/arc_bench_adapter.py) 是单独的 ARC-Bench 适配器：调用主办方 `local_submit.py`，保存其原始 workspace 和 `local-result.json`，核对评测完成及用例计数，再写通用结果。
评测完成后的低分仍是有效结果；Runner 没有产出完整评测时是执行失败。

本项目的本地容器构建、Agent 生成和 benchmark 评测统一在 WSL（`wsl.win-ws.localhost`）执行。
macOS 仅用于编辑、传输制品和查看结果，不为这些实验创建或启动 Colima。
控制器、Docker daemon 和 workspace 必须使用经过实际 bind mount 验证的路径；能连接 Windows Docker Desktop socket 并不证明它能挂载 WSL 目录。
WSL 本轮使用独立 Docker Engine，不重启其他项目所在的 Docker Desktop。

长矩阵启动前检查 WSL 磁盘、容器内模型 API 和容器至 OTLP collector 的连接。
2026-09-23 的 WSL 观测为 IPv6 可用、IPv4 不通，当时独立 Docker Engine 的默认 bridge 已按 [Docker IPv6 文档](https://docs.docker.com/engine/daemon/ipv6/)启用 IPv6；只验证 WSL 宿主网络不足以证明容器能访问模型。
出现共享运行环境故障时停止派发，保留完整生成的应用；环境恢复后仅补评测，不把设施失败计作模型零分。
以下命令在 WSL 仓库中执行，先固定镜像与输入。
以下路径按仓库与 `factory26-official-local` 同级布置；Docker daemon 必须能访问 bind mount 的实际路径。
基础镜像 digest 是 2026-09-23 核验的 `linux/amd64` 发布物；若换镜像，保留新 digest 和每个 run 的 `image_id`，不要将两者的分数视作同一环境。

```sh
LOCAL_ASSETS=../factory26-official-local
ARCBENCH_LOCAL_BASE_IMAGE=gyataro/arcbench-runner@sha256:40e003ed470dbd4c120b9019876ba77303d38dc8b34be7f6e313fe0563dd14de \
ARCBENCH_LOCAL_PLATFORM=linux/amd64 "$LOCAL_ASSETS/runner/build-image.sh"

python3 scripts/arc_matrix.py \
  --variant deepseek=runs/packages/iteration-throughput-boundary/pi-team-deepseek.zip \
  --variant mixed=runs/packages/iteration-throughput-boundary/pi-team-mixed.zip \
  --case arc-bench-lite/keep --case arc-bench-web/keep \
  --inputs-root "$LOCAL_ASSETS/platform-inputs" --runner "$LOCAL_ASSETS/runner" \
  --image arcbench-local-submit:latest --workers 4 --separate-evaluation \
  --output "$LOCAL_ASSETS/runs/example-matrix.json"

python3 scripts/local_experiment.py run "$LOCAL_ASSETS/runs/example-matrix.json" \
  --runs-root "$LOCAL_ASSETS/runs/example-results" --listen-host 0.0.0.0
```

真实模型需在 `arc_matrix.py` 加 `--env-file ~/.config/factory26/llm.env`；该文件权限为 `600`，适配器临时合入 OTLP 参数后传给 Docker，运行结束删除临时副本。
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

```sh
python3 scripts/local_experiment.py status "$LOCAL_ASSETS/runs/example-results/<run-id>"
python3 scripts/local_experiment.py telemetry "$LOCAL_ASSETS/runs/example-results/<run-id>" \
  --signal traces --export "$LOCAL_ASSETS/runs/exported-otlp"
```

`telemetry` 也接受 `--since` 与 `--until` 的 Unix 秒时间戳，导出的 `.pb` 保持接收时的原始 OTLP protobuf 内容。

### Raw Pi/Codex 基线

[package_raw_core.py](../../scripts/package_raw_core.py) 可直接消费 `runtime.py linux` 导出的原生工具目录，也保留从历史 ZIP 提取 runtime 的方式，再加入独立的 [raw_main.py](../../submission/raw_main.py) 入口。
模型请求参数由 [raw_models.json](../../submission/raw_models.json) 按模型 API 定义，两个核心的 ZIP 固定同一组 `thinking`、`reasoning_effort` 和 `max_tokens` 参数、模型 descriptor 和来源摘要；不读取 Factory harness 的模型配置，也不加载 Factory、Braid、SVC、项目技能或外部子代理。
具体运行模型与资格状态由实验记录维护；通道曾返回额度拒绝，不代表模型持续不可用，恢复后应以真实 API 请求确认所选参数和工具调用。
Pi 直接使用 JSON 输出和原生 session；Codex 使用 JSON 输出的原生 CLI，Chat 网关接入沿用 LiteLLM Responses 兼容层，并由 raw 专用适配器移除 Codex 自带的 reasoning 字段。
入口将完整原生事件、stderr、会话与终态写在应用工作区 `.arc/raw/`；[raw_otlp.py](../../submission/raw_otlp.py) 将过程事件作为 OTLP logs 发送，跳过高频的逐 token `message_update`。
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

raw 实验可使用 `~/.config/factory26/llm.env` 的 `FACTORY26_API_KEY`；raw 入口把它提供给原生客户端，默认连接 `https://api.arc-bench.com/v1`，模型由各 ZIP 固定。
需要连接别的兼容网关时可提供 `OPENAI_BASE_URL`。
不要提交或分享凭据。
评测阶段不向空入口注入模型凭据。
生成目录中的原生事件和 OTLP 批次可能包含需求、工具输出或模型文本，分享前检查内容。

raw 的 API 参数以 [raw_models.json](../../submission/raw_models.json) 和包内 raw-config.json 为准。
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

旧 run 的 eval/analyze/show 继续读取其归档配置；不要以新 variant 重写旧结果。
新实验状态使用 local_experiment 的 status，完整评分失败用例是有效结果，生成/评测设施中断不是零分。

## 按记录生产者查询

先确认拿到的是外层实验目录、Harness 内层目录还是平台 journal；它们的状态描述不同过程。
当前没有覆盖这些格式的统一 brief 入口。

| 记录类型 | 从哪里开始 | 下一层证据与限制 |
| --- | --- | --- |
| local_experiment 外层 run | `python3 scripts/local_experiment.py status <run目录>` | run.json 的 phase/result、stdout/stderr、workspace 内官方结果；不把旧 run_feedback 的 unknown 当作该实验没有终态。 |
| Factory 团队生成 | `python3 scripts/factory.py show --run <输出/.factory26/id>` | braid.log、delivery.json、braid-state、native/manifest.json；使用显式路径，不依赖根 runs 的自动发现。 |
| raw 生成 | 官方 workspace 的 `template/.arc/raw/` | 原生事件、stderr、身份与入口结果；外部评分在外层 Runner 结果中。 |
| 历史 Factory run | `python3 scripts/run_feedback.py brief <旧run目录>` 或 factory show | 旧 status/outcome 格式与归档评测；这是旧流程摘要，不是任意目录的通用解释器。 |
| Competition / Playground | 对应 journal、已保存 status 和平台原始结果 | 记录观察时间、远端 ID、完整评分与采集缺口；历史文件不证明远端当前状态。 |

Factory show 可以按原归档支持的评测和用例继续定位：

```sh
python3 scripts/factory.py show --run /path/to/factory-run --case REQ-2.2
python3 scripts/factory.py show --run /path/to/factory-run --eval <evaluation-id> --json
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
python3 scripts/run_viewer.py
open runs/viewer/index.html
```

当前页面按生产者发现根目录的 Factory run、Competition hosted 控制器声明的平台 run 和已保存的 Playground run；不会完整发现外层 local_experiment 或新嵌套 .factory26 记录，缺少展示不表示未执行。
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
local_experiment 应等待执行进程完成并读取持久结果；下面的只读等待命令只适用于旧 Factory 状态格式：

```sh
python3 scripts/run_feedback.py watch runs/<run-id>
python3 scripts/run_feedback.py watch runs/<run-id> --after-event <已处理的event_id>
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

`python3 scripts/factory.py analyze --run <Factory生成目录>` 为每个原生会话分别导出 `analysis/<序号>-<来源指纹>/evidence-v4.zip`，保存 overview、模型 usage 和 provenance。
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

旧 run 的 `factory.py eval --run <目录> --eval-host wsl.win-ws.localhost`、list、show 和 analyze 保留；生成时的配置和制品身份不改写。
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

[sources.py](../../scripts/sources.py) 记录 HEAD 及未提交、未跟踪文件的源码哈希；Braid 另记录二进制哈希并在生成前验证构建仍匹配。
SVC 直接归档源码，不需要构建记录。
历史 run 的 `sources/` 保存其实际源码归档；新 variant 记录实际代码/材料哈希、原生配置与包载荷，旧 runs 不补写新版本。
[SVC 技能入口](../../harness/skills/svc/SKILL.md) 提供按需导航，方法正文只来自 Corpus；接线不进入 Braid 控制协议。

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

[playground.py](../../scripts/playground.py) 使用网站 HTTP 接口完成登录、上传、运行和证据收集，日常实验不需要浏览器。
首次运行 `python3 scripts/playground.py login`，交互输入网站邮箱和密码；也可以通过 `--credentials ~/.config/factory26/playground-login.json` 读取权限为 600 的 JSON 文件（email、password）。
登录验证后保存权限为 600 的 `~/.config/factory26/playground.cookies.txt`。
网站会话与比赛模型密钥分开保管，登录信息不进入仓库或命令参数。

```sh
python3 scripts/playground.py whoami
python3 scripts/playground.py requirements --catalog benchmark
python3 scripts/playground.py submit --practice --package /path/to/agent.zip --config /path/to/model-config.json --requirement keep --name factory-keep
python3 scripts/playground.py watch <run-id>
python3 scripts/playground.py collect <run-id>
```

上传前必须准备符合平台契约的 Python Agent ZIP，根目录包含 main.py 与 requirements.txt。
`submit` 要求通过 `--config` 显式提供网关和模型，并使用仓库外比赛密钥；配置不会改变 ZIP 已打包的核心或工作流。
清单明确标记 configuration_scope=model-settings-only，包身份以 SHA256 为准。
只有无模型探针使用 `--offline`，该选项传非凭据占位符。
包哈希、已确认的 submission/run ID 与执行阶段记录在 `runs/playground/upload-*/submission.json`，便于写请求失败后查明已经完成哪一步；传输结果不明时不自动重复 POST。

续跑、启动和取消只接受本工具清单中明确记录为 practice/probe 的 ID；未知、正式和缺少分类的历史 ID 请通过平台管理。

同一包重跑使用 `python3 scripts/playground.py run --submission <submission-id> --requirement <requirement-id>`，避免重复上传。
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

共同配置的 `factory.py batch` 已退役，不再用旧 multi-agent-lite 清单启动新矩阵。
新矩阵使用前述 arc_matrix/local_experiment 路径；旧 batch.json、inputs.json 及各 run 保留为历史证据，不迁移成新的运行身份。

concurrency.py 是旧评测并发与模型探测工具，不承担当前矩阵调度。
其历史记录位于 `runs/concurrency/`，曾有的并发观测只支持相应应用、接口和当时环境，不能推导当前吞吐或模型额度。
该旧探针会把 429 归类为限流且未保留完整响应正文，不能用其摘要区分额度耗尽和并发限制；当前方案不推荐以它作为资格依据。
旧平台与工具调查见 [2026-09-20 记录](../../reports/2026-09-20-playground-concurrency.md)，不是当前机器环境承诺。
