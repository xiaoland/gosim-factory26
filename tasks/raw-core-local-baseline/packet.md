# Raw Pi/Codex × DeepSeek/GLM 本地基线

## 当前决策（取代下方历史状态）

预算控制（2026-09-24）：用户明确要求账户额度切换为500时停止，该500保留未来五天使用。当前Meter浏览器页面与WSL官方登录计量接口均超时，尚不能确认额度值；已要求运行owner保守暂停所有模型调用和补跑，保留现场，不自动恢复。预算停止优先于完成32场，未知余额不能当作未触发。

用户随后明确要求再增加四个并发，总上限改为8。现有 controller 的线程池在启动时固定，不能通过修改清单在线扩容；恢复时排除已有评分、对已完成并冻结的应用只运行评测，并保留中断任务证据，使用单一八并发调度器继续原32场。

2026-09-23 用户要求停止 Kimi/Qwen，在 WSL 恢复原定 DeepSeek/GLM 基线。目标为 raw Pi、raw Codex × `deepseek-v4-flash-vision-exp`、`glm-5.3-flash` × Lite 两题、Web 六题，共 32 场，统一四并发。已有 Kimi/Qwen 分数和中断证据保留为独立历史，不计入这 32 场。运行 owner 正在停止旧 controller 及其所属容器，随后以独立目录启动新矩阵。

WSL 直接 API 复查的三个 DeepSeek 与三个 GLM 均 HTTP 200、返回391、finish=stop，证据位于 WSL 实验根目录 `api-recheck/20260923T135622Z/`。正式运行前另验证基线参数和两轮工具调用：DeepSeek 关闭推理、max_tokens=16384；GLM 开启推理、effort=low、clear_thinking=false、max_tokens=131072。只使用原用户凭据迁移副本，不读取 WSL 自有的不同密钥。沿用冻结官方输入、运行时和 OTLP 薄壳；不运行或新增 Factory/设施测试与包 smoke，接入验收来自真实 API 和获授权 benchmark。

## 历史执行记录

当前执行环境（用户纠正后）：停止所有 macOS 实验进程并删除 `factory26-p0` Colima profile、data/system disks 和 Docker context；保留无关的 `registry-preview`。清除四个 native smoke 的解压 runtime 及此前误建的 `model.env` 密钥副本，原始实验、应用和模型过程证据保留。后续仅在 WSL `wsl.win-ws.localhost` 的 `/home/yyh/Development/factory26-official-local/raw-baseline-20260923-wsl` 执行。本轮 WSL 使用独立 Debian Docker Engine，不重启已有 Docker Desktop 项目。四包、Runner 和冻结输入共 811 文件及 5 个完整应用已校验哈希一致。基础镜像仍为 digest `40e003ed470dbd4c120b9019876ba77303d38dc8b34be7f6e313fe0563dd14de`，WSL wrapper image ID 为 `sha256:840105914e6e166ba1eefa4bd3af1682e795d2e515497198142010c1e79eb19d`；保留 Mac 历史 image ID，不能把平台变更隐藏为同一环境。WSL 原 `~/.config/factory26/llm.env` 与本轮密钥不同，未覆盖；从 Mac 用户原配置安全复制至本轮目录 `.private/llm.env`（600），仍使用 `FACTORY26_API_KEY`。WSL 原生容器出网检查发现宿主 IPv4 本身不可用，仅 IPv6 路由可用；已在 `/etc/docker/daemon.json` 启用 IPv6 bridge（`fd26:fac7:2601::/64`）、ip6tables 和该 Docker 26 版本所需 experimental。容器内两模型真实请求均 HTTP 200、finish=stop、答案391，OTLP HTTP 200，结果保存在 WSL `preflight.json`。已在 WSL 启动一个 29-job、4 并发 controller（PID 720828，manifest `tooling/full-matrix-api-v5-wsl.json`，运行目录 `runs/matrix-api-v5-wsl/`，日志 `logs/matrix-api-v5-wsl-controller.log`），包含两场仅评测及其余 27 场生成，避免分离控制器导致并发降低；已有 3 场分数归档。

最新恢复（2026-09-23 21:12 CST）：Colima VZ 在 21:06:34 进入 `VirtualMachineStateError`，不是模型生成终态；Docker 与 SSH 超时。宿主日志保留于同级运行目录 `vm-error-210634/ha.stderr.log`。强制停止失效 VM 后已重启，Docker、SSH、Node/npm 恢复；确切 VZ 错误原因尚未确定。当前有效评分 3/32（Pi/Kimi Lite/Keep 16/32，Pi/Qwen Lite/BookStack 1/34，Codex/Qwen Web/BookStack 5/34）；新增两场 Kimi Web/12306 已完成生成，仅恢复评测，其余 27 场重新排队。官方冻结 12306 collection 两次均为 135，已修正 `scripts/arc_matrix.py` 原错误常量 138，并扩展已有 CLI 矩阵检查，3 项通过。

状态：2026-09-23 用户明确授权完整运行 Lite 两题、Web 六题，四个 raw 核心/模型组合共 32 场，并以薄壳上报 Agent 过程 OTLP 作为设施验收范例。仅使用本地模拟 Runner；不访问已关闭官网。

当前故障恢复：首轮 Docker 镜像存储发生 I/O 错误，Colima guest ext4 journal aborted；系统盘仅余 1.3 GB，而实验 SSD 尚余约 571 GB。已停止原矩阵，2026-09-23 20:08 CST 完成 system/data 虚拟磁盘迁移到同级 `factory26-official-local/colima-disks/factory26-p0/` 并保留原路径符号链接。系统盘恢复约 16 GB；guest data 盘卸载后 `e2fsck -p` exit 0，重新挂载后 Node/npm 与容器 64 MB 随机写入+sync 通过。镜像 ID 保持 `sha256:e0107fd248d0d810f0deb453787195af417046e16eccb714bcb6723e9a5e0f2c`。两场仅评测恢复先验收，通过后按 `full-matrix-api-v5-recovery-v1.json` 在 `matrix-api-v5-recovery-v1/` 继续 30 场。原 32 个状态中 30 failed、2 interrupted，无有效成绩。Pi/Kimi Lite/Keep 和 Pi/Qwen Lite/BookStack 已完成并冻结生成，可仅恢复评分；其余 30 场将重启生成，旧证据完整保留。

本轮执行：用户授权先用不受阻模型完成原定 32 场矩阵。替换为 `kimi-k2.7-code`（强制开启推理，不发送 effort）和 `qwen3.6-plus`（关闭推理，不发送 effort），分别运行 raw Pi、raw Codex 的全部 Lite 两题与 Web 六题。直接使用原始 `~/.config/factory26/llm.env`；直连工具往返和 max_tokens 上限已核验：两模型各 8 并发及混合 8 并发均成功，32 请求无 429。证据位于同级 `factory26-official-local/runs/raw-baseline-20260923/replacement-api-qualification/`。四组合原生真实工具往返已全部完成（写文件、读取、原生成功终态）。32 场已在 2026-09-23 19:48:08 CST以四并发启动，清单 `full-matrix-api-v5.json`、运行根目录 `matrix-api-v5/`。直接 API 并发探针仅给出已测下界，不将额度拒绝误报为速率限制。

最新逐档结果：16 个模型 × 21 种参数组合的独立直连测试已完成，144 次成功（均完整返回正确答案）、24 次参数拒绝、168 次额度拒绝。8 个模型可用；三个 DeepSeek、三个 GLM、MiniMax M3、Qwen 3.7 Max 全部组合仍返回 insufficient_quota。因此此前把生成不可用归因到整个密钥的判断过宽，当前证据指向模型或上游通道相关的额度门禁。完整结果见 [模型推理参数实测](../../reports/2026-09-23-model-reasoning-probe.md)。原始密钥配置、四并发基线矩阵保持有效，但 DeepSeek/GLM bench 与其并发峰值测试仍受模型通道阻断。

此前控制状态：用户要求暂停后，两场活动 run 已记录为 `interrupted` 且进程/容器退出；随后用户要求先将模型参数按 LLM API 调通，再尽快启动 Lite/Web。参数现在由 `submission/raw_models.json` 维护，不读取 Factory Harness 的模型配置。早期 `api-v1` 包把两模型都设为关闭推理，但 Z.AI 文档明确 GLM-5.3-Flash 只支持开启推理且仅允许 `low`、`high`、`max`；因此改用 `thinking=enabled, reasoning_effort=low` 作为 GLM 基线候选，DeepSeek 候选继续关闭推理。四个最终候选 `api-v4` ZIP 的 Pi/Codex 原生请求已通过假 API 捕获，均从用户原有 `~/.config/factory26/llm.env` 的变量名接入，并对相同模型发送一致的推理字段；假 API 不能证明真实网关接受这些档位。用户要求将矩阵并发上限改为 4，并在可用真实调用后测试各档位及每模型、混合请求的限流峰值；32 场清单为同级 `factory26-official-local/runs/raw-baseline-20260923/full-matrix-api-v4.json`，直接指向该原始密钥文件。此前我为旧入口复制的 `model.env` 与原密钥相同，仍保留为历史 run 证据，但新矩阵不再使用它。当前直接调用 `https://api.arc-bench.com/v1/chat/completions`，两模型均返回 HTTP 429 `Free allocated quota exceeded`，而同一密钥查询 `/v1/models` 返回 200。最近一次 GLM 失败于 2026-09-23 19:16 CST，响应 `type=insufficient_quota`、`code=Free quota exhausted and balance too low, please recharge compute credits.`、`traceId=4a670813a7044711ad21289f143e95b5`。Meter 账户在 19:17 CST 显示已同步可用余额 223.078186 CNY；其 17:57 的 DeepSeek 请求与本地 Pi/BookStack 运行时段吻合，但页面不展示 key ID 或额度组，尚不能证明余额如何适用于该密钥。429 不能解释为并发限流，也不能据此要求用户充值。先导评分只保留历史证据，不计入新参数基线。

2026-09-23 逐档实测：使用原始 `~/.config/factory26/llm.env` 的密钥，直接向 Chat Completions 分别请求 DeepSeek 与 GLM 的 `off`、`low`、`high`、`max`，每档一个最小非流式请求，共八次；八次均返回 HTTP 429 `insufficient_quota`，无任何模型输出或参数校验结果，证据保存在同级 `factory26-official-local/runs/raw-baseline-20260923/api-capability-probe.jsonl`。故目前不能根据这八次请求判断档位实际可用性，也不能测并发峰值；单请求已被额度门禁拒绝。

2026-09-23 先导证据：主办方 Runner 的两阶段无模型预演完成 Lite/Keep 32 项（0/32）。生成容器无测试文件，评分前后应用源码哈希一致。首个 Pi+DeepSeek `high` 先导运行原生终态 `length`，最后一次响应 16,384 output tokens 全为 reasoning，未生成 frontend/backend，因此未计分；原始事件及约 1,207 个 OTLP 批次保留。已将逐 token `message_update` 从后续 OTLP 范例上报中剔除，完整原生事件仍落盘。三个可评分先导均为 Lite/Keep：Codex+GLM `high` 14/32、43.8%、31 个 OTLP 批次；Pi+DeepSeek `off` 27/32、84.4%、180 批；Codex+DeepSeek `none` 22/32、68.8%、166 批。三场评测各自的冻结与评测源码哈希相同；本地 Runner 的 `score` 字段均为 null。Codex+DeepSeek `off` 首次预演被网关以 422 拒绝，明确要求 `reasoning_effort=none`，未计分；`none` 复验成功。Pi+GLM `high` 在持续输出推理约 70 分钟、仍未形成评分时主动中断，`run.json` 为 interrupted 且原始过程保存；这不是模型失败或零分。Pi+GLM `off` 和 Pi+DeepSeek Lite/BookStack 重试在用户暂停时中断；BookStack 首次尝试遭遇模型网关 400 proxy_error/TCP connection reset，生成失败未计分。旧版 Codex+GLM 先导的提示/壳版本不同，不计正式基线。

## 边界

四个组合为 raw Pi、raw Codex 分别使用 `kimi-k2.7-code`、`qwen3.6-plus`。raw 指直接驱动原生核心，不调用 Factory generate、Braid、SVC，也不装配项目技能或外部子代理；核心自身的默认能力保留。全部场景用同一份原生提示，依据冻结需求构建应用，自验结束后再由 Runner 评测；不得将评测失败反馈给同一次生成。每个 run 保留 Agent ZIP、模型名、需求/测试哈希、原生事件与会话、OTLP 批次、产物、终态和评分。

官方 `local_submit.py` 在带 `--tests-dir` 的单阶段调用中，启动 Agent 前便复制测试。基线采用两次官方 Runner 调用：先不传测试，仅生成应用；再以该应用作 `--template`，用无模型 Agent 运行评测，并核对冻结与评测源码哈希。生成容器的 `/workspace/tests` 为空。该隔离模式已通过无模型预演和 Codex+GLM 先导的外部输出核验。

## 待办与完成条件

1. 固定 raw 运行时与打包来源；为 Pi/Codex 编写最薄入口和 OTLP exporter，避免改动评测器或 Factory Harness。
2. 预演单场模型请求、应用交付、原生过程归档与 OTLP 查询，确认容器内链路。
3. 冻结 4×8 矩阵，按主机资源并行；设施故障诊断修复后复验，直到每场完整评分或出现不可恢复外部阻断。
4. 先向用户汇报 32 场成绩、缺项/失败、过程证据与设施验收范围；长期方法入运行文档，脱敏结果入报告，删除本 task packet。

本轮代码验收：`make test` 139 项 Python 检查与 Pi passive observer 检查通过；`.venv/bin/svc status --json` healthy，修改文档的本地链接全部有效。四包冻结为 `fixtures/raw-{pi|codex}-{kimi-k2.7-code|qwen3.6-plus}-api-v5.zip`，初始四场同时覆盖 Lite/Web 和四组合。

WSL 启动独立核验：29 场均已准备，首轮 4 running/25 queued，两个仅评测 job 不调用模型；两个生成 job 各已收到 OTLP logs。macOS 未发现本实验 controller/supervisor 或 Colima hostagent 进程，清理记录在同级 `runs/raw-baseline-20260923/wsl-migration/cleanup.json`；WSL 的 `migration-check.json`、`environment.json` 与 `preflight.json` 记录迁移哈希、环境身份和真实连通性。

Ctrip 集合计数修正：冻结官方 tests 在同一 Runner 镜像执行 `npx playwright test --list` 为125 tests in125 files；Codex/GLM Ctrip 首次报告14通过、111失败、skipped=0、errors=0，与收集一致。`scripts/arc_matrix.py` 预期126为设施常量错误，已改125。原始失败记录保留，冻结应用仅恢复评测，不重跑模型。证据在 WSL recovery8 的 `raw-codex-glm-arc-bench-web-ctrip-9837d043bd/ctrip-count-audit.json` 和 `ctrip-playwright-list.txt`。
