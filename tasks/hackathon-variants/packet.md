# Hackathon 本地四配置对照

状态：四配置设计已由用户确认，已授权实施、仅提交本任务相关修改，并在完成接线后启动本地正式 benchmark。既有 Lite/Web 运行保持停止。Codex 与 Pi 各自独立运行，完全不使用 Braid。

## 对照与角色

用户提出两条设计：基础组，以及仅增加 SVC 的组。每条分别用 Codex、Pi 实现，因此有四个实际 variant：`codex-base`、`codex-svc`、`pi-base`、`pi-svc`。每个 variant 都跑官方 `hackathon` 的两道任务，预期 8 个独立本地执行；同一 Harness 内固定模型、提示、角色、工具、预算、任务输入与运行环境，比较 SVC 差异。不同 Harness 的得分可并列呈现，但不能当作仅由 SVC 造成的差异。

共同模型分工：主 Agent、explorer 和 executor 使用自购 `glm-5.3-flash`；advisor 使用自购 `kimi-k3`；browser operator 使用自购 `deepseek-v4-flash-vision-exp`。四个子代理分别负责只读调查、有界实现、浏览器旅程、只读判断。browser operator 兼顾需求参考图与运行页面截图，不再加第五个 vision 角色。所有 agent-browser 操作、Playwright 自建功能回归都只接触生成应用与公开需求，不接触官方验收测试。此模型分工已由用户确认。

Pi 使用锁定的 `pi-subagents@0.56.0` 原生扩展，角色 Markdown 明确 model、tools、context、skills；Codex 0.155.0 使用 `CODEX_HOME/agents/*.toml` 原生自定义子代理和 `agents.enabled`，同名角色配置各自模型、指令与权限。各运行独立 home；基础组不装配 SVC，SVC 组在隔离 home 中放入同一冻结 SVC skill，并让主 Agent 与 explorer/executor/advisor 按需使用；browser operator 的任务仍限浏览器和图片。Codex 从隔离 HOME 的 `.agents/skills` 发现技能，Pi 由启动参数与角色声明显式选择。agent-browser 用于交互观察；Playwright 用于 Agent 自己编写的可重复功能自检，需要为四组一致装配独立 Playwright 库和浏览器。现有 `agent-browser@0.38.1` 依赖清单没有 `playwright` 包，不能把它误称为已经可直接运行 Playwright 脚本。原始主/子 Agent 会话与工具事件作为薄封装 OTLP logs 输出，实验设施只接收与保存原始 OTLP。

模型提供商映射归单独本地 LiteLLM 入口：Pi 走 Chat Completions，Codex 走 Responses→Chat，二者用同一模型 alias。provider 密钥只在 WSL 网关进程读取项目 `.secrets/models.env`，Harness 仅获临时网关 token/URL；官方 local_submit 宿主环境清除 `OPENAI_API_KEY`，避免它被发送到 ARC Meter。网关不回退官方模型或其他供应商。初始方案采用各自 API 的默认推理设置，避免 Harness 指定不同档位：Pi 的客户端 descriptor 声明 `reasoning:false` 且 `--thinking off`，实测 GLM 仍返回 reasoning content；Codex 客户端设置 `model_reasoning_effort=none`，已有 Responses 兼容层不把该客户端字段传给上游。两边的真实上游请求参数仍必须采集核对，确认相同后才冻结。此前 Pi 使用推理 descriptor 时，`thinking` 字段在通用 openai provider 上报 400；尝试 `drop_params=true` 后，GLM `off` 仍被上游拒绝，`low` 才能工作。当前无须以全局静默丢弃参数作为正式方案。

## 已有实际证据（2026-09-24，均在 WSL）

- 公开 `GET https://arc-bench.com/api/competitions` 列出 `hackathon`：2 题、200 测试、GitHub 式协作与电子表格方向、无 template。详情 `GET /api/competitions/hackathon` 对当前会话返回 403，要求确认团队。现有同级 `factory26-official-local/platform-inputs` 只有 Lite/Web；hackathon 输入包与精确评测契约尚未取得。
- 自购 Kimi K2.7 Code、GLM 5.3 Flash、DeepSeek Flash 直连 Chat：流式工具调用与带真实 call_id 的工具结果续接均 HTTP 200。自购 Kimi K3 工具调用 HTTP 200。
- 自购 DeepSeek 的 `/models` 没列出 `deepseek-v4-flash-vision-exp`，但该 ID 直连有效 PNG 的图像请求 HTTP 200，64×64 红图识别为 Red；图像加工具调用也 HTTP 200。2×2 图像的一次工具返回误判为 white，故只能证明协议路径可用，不能据此保证视觉正确率。
- 已冻结 LiteLLM 1.102.0 在 WSL 实际启动，三家文字模型经 `/v1/responses` 都返回 200，`tool_choice=auto` 都产生 function_call；`required` 被 Kimi/DeepSeek 的推理模式拒绝。DeepSeek 视觉模型经网关 Chat 和 Responses 发送 64×64 PNG 都返回 200 并识别 Red。
- 冻结 Codex 0.155.0 `multi_agent` 功能开启；以 GLM 主 Agent、Kimi K2.7 Code 自定义 advisor 配置经网关隔离运行，成功调用 advisor 并完成回合。Codex stderr 出现 `OutputTextDelta without active item`，短任务未失败，长任务影响未知。此次未独立记录子代理实际落到的上游模型请求。
- 冻结 Pi 0.85.1 与 `pi-subagents@0.56.0` 经网关隔离运行，GLM 主会话成功调用 `gateway/kimi-k2.7-code` advisor 并结束。随后使用非推理客户端 descriptor 与供应商默认推理，GLM 主会话再次完成；同配置切换 advisor 到 `gateway/kimi-k3` 后，主会话也成功调用 advisor 并结束。网关 Kimi K3 Responses 的 function_call 另有 HTTP 200、completed 证据。此前两次参数错误如上保留。此次未独立记录子代理实际落到的上游模型请求。

参考接口：Codex https://developers.openai.com/codex/multi-agent 、https://developers.openai.com/codex/config-reference ；Pi https://github.com/nicobailon/pi-subagents/tree/v0.56.0/docs ；LiteLLM https://docs.litellm.ai/docs/response_api 、https://docs.litellm.ai/docs/proxy/client_setup/codex_cli 。

## 本轮执行边界

模型分工与 SVC 覆盖范围已确认。实施时冻结四份独立 ZIP，做模型路由及真实请求参数核验、子代理/浏览器/OTLP 小场景验收；取得官方 hackathon 输入包与 runner 对应契约后，在 WSL 启动八个正式本地任务。任何前置验收失败都保留原始错误，不替换模型冒充同一配置。2026-09-24 复查时官网 API 返回 HTTP 500 与“系统维护”，Mac 和 WSL 的本地官方资产都只有 Lite/Web；正式任务输入仍缺失。

2026-09-24 WSL 接线证据：`factory26-official-local/hackathon-runtime-{pi,codex}` 已从冻结 npm lock 构建，四个 ZIP 已冻结在同级目录。`hackathon-gateway/request-metadata.jsonl` 显示三家自购模型的真实 HTTP 200 请求，以及 Pi、Codex 各自 GLM 根会话→Kimi K3 advisor 和 GLM 根会话→DeepSeek browser operator；网关记录均只保留统一后的 16384 输出 token 上限，没有客户端推理参数。Pi 短任务的原生事件在 `hackathon-qualification-pi/{events,browser-events}.jsonl`，Codex 在 `hackathon-qualification-codex/{events,browser-events}.jsonl`；advisor 任务均得到 391，browser operator 路由任务均正常结束。Codex stderr 仍出现 `OutputTextDelta without active item`，短任务正常完成，长任务影响尚无证据。容器到 WSL 网关 bridge 地址实测 HTTP 200。正式 Runner、真实浏览器操作、Playwright、OTLP 全链尚待带真实任务的运行验证，不能将 ZIP 构建或短任务等同 benchmark 完成。

2026-09-24 官网恢复后复查：公开 `/api/competitions` 返回 HTTP 200，`hackathon` 仍列 2 题、200 测试。赛事列表卡片的“Open ARC-Bench on GitHub”指向 `https://github.com/code-philia/arc-bench`；该仓库公开 `main` 和 `polish` 未见 Hackathon 两题的需求或测试。赛事详情起初要求先确认队伍；未认证的 `/api/competitions/hackathon` 返回 HTTP 401，正文为 `Sign in to confirm your team and access this official competition`。

用户随后明确回复“确认”，授权按页面所列单人名单创建正式赛事队伍。2026-09-24 页面确认 `Lan_zhijiang` 队伍已建立，余额 ￥500；没有提交 Agent 包或启动官网运行。赛事详情给出 `hackathon--github`、`hackathon--sheet` 两题。通过 GitHub 题页的“Download all requirements”取得同一个 ZIP，内含两题 `requirements.yaml` 和参考图，SHA256 为 `9884f23ea10c3dfeee170d1eed57966c8fce9a5ce18a0ac43b3d7942eba8c414`，没有公开评测测试。原 ZIP 保存在 WSL `factory26-official-local/arcbench-hackathon-requirements.zip`；提取后的两题需求与逐文件哈希在 `platform-inputs/hackathon/{github,sheet}/`。主办方 Runner 明确支持不传 `--tests-dir`，此时跳过评分。

当前本地矩阵改为四配置 × 两题的生成与部署验收，使用自购模型网关，本地不产生正式得分；用户现已授权下节所述官网非榜单产物回放评测。`hackathon-generation-matrix.json` 固定 8 个 job、4 并发，2026-09-24 已在 WSL 启动 `local_experiment.py`（启动 PID 904226），结果根目录 `runs/hackathon-generation-20260924`，控制器日志 `hackathon-generation-controller.log`。完成后先检查原始 Runner 终态、应用布局、OTLP 批次与预算消耗，再汇报；不把本地无测试运行与官网正式得分混称。

首个 `pi-base × github` 在生成 525.564 秒后失败：官方 Runner 容器退出码 1，Pi session 最后一个 assistant 消息的 `stopReason` 为 `length`，截断发生在规划阶段，尚无 `frontend/` 或 `backend/`。网关此前该任务请求持续 HTTP 200；因此这是输出长度截断后的接线缺口，不是可计分结果或额度拒绝。`submission/hackathon_main.py` 现对 Pi 在同一 session 中最多续跑 8 次，`raw_main.stream` 支持追加原始事件。WSL 已重新冻结 `pi-base-recovery.zip`（SHA256 `8171aa1a8030dd32d9593c5ecb0bd41229650faf8000b57509ac4a420b6402c0`）和 `pi-svc-recovery.zip`（SHA256 `4d100b05120c394b6fb71028d333ba779c9a7720be0543715d675bbc168181b5`）；待原矩阵占用的并发槽释放后，仅补跑受该问题影响的 Pi case。

原先 WSL 的 `recover_pi_length.py`（PID 910296）只准备使用上述续跑包；用户指出第二次出现输出长度问题后，已终止这个尚在等待的补跑控制器，避免继续用 16384 预算补跑。首轮原始矩阵继续保持已冻结参数。

## 输出预算根因与 128K 中间修正（2026-09-24，已被下节取代）

用户要求：“输出长度的问题我们之前也遇到过，这是第二次了，我们应该找到一个根本性的解决方案”。定向读取失败 session 发现最后响应 `output=16384`、`reasoning=16376`、`stopReason=length`。这是一次请求的推理耗尽输出预算，不是网络 JSON 截断。冻结 Pi 0.85.1 的 `docs/models.md` 及 `pi-ai/dist/api/simple-options.js` 证明：自定义模型的 `maxTokens` 可省略，但默认仍是 16384；CLI 路径默认从 descriptor 取值，并按剩余上下文扣除安全余量。此前入口和网关同时硬编码 16384，且网关覆盖所有客户端值，根因在接入配置。只加续跑没有修复它。

官方 GLM 参数页列出 `glm-5.3-flash` 默认 65536、最大 131072，强制启用思考、默认 max；Kimi K3 的默认输出预算为 131072；DeepSeek 当前 Flash 最大支持 384K。本轮将三模型的实验输出预算设为 131072，统一放在 `submission/hackathon_models.json`，由 Pi、打包器和网关共用，网关尊重客户端更小的预算。模型能力与实验预算不混称；没有改动供应商默认推理政策。新实例使用端口 4011、`hackathon-gateway-output128k`，不修改首轮使用的 4010 实例。

WSL `check_output_budget.py` 通过新网关实际调用三模型各自 Chat/Responses 两条路径，共六次均 HTTP 200、回答 391，合计 687 tokens；请求、响应在 `output-budget-evidence/`。这证明接口接受新预算，不证明长任务已经完成或永不截断。新网关 `request-metadata.jsonl` 用于核对客户端与有效输出预算。后续仅对首轮 length 失败的 Pi case 使用新包与新网关补跑，原失败和原参数记录保留。

新 Pi 包已在 WSL 冻结为 `pi-base-output128k.zip`、`pi-svc-output128k.zip`；替换后的等待控制器 PID 922565，日志 `hackathon-pi-output128k-controller.log`。首轮八个 job 结束后，它将使用新网关生成 `hackathon-pi-output128k-matrix.json`，输出到 `runs/hackathon-pi-output128k-20260924`，最多 4 并发，只补跑 length 失败的 Pi case。首轮在跑和排队任务仍属于原始 16K 参数组，不把它们标记为已采用新预算；若后续对照新参数，须显式生成新矩阵。

## 当前决定：由供应商决定输出长度，并清理多余约束

用户明确要求“不设置，允许无限”，并要求检查过度的安全边界、配置、校验与错误耦合。这里可实现的含义是本地不附加输出上限；供应商默认值和模型上下文仍存在。已停止仍在等待的 128K 补跑控制器 922565。Pi descriptor 不再写 `maxTokens`；网关删除三个输出长度参数，连同 Pi 隐式添加的 16K 一起移除，且不再依赖参赛包的模型配置。新网关位于 `hackathon-gateway-defaults`，端口 4012，启动 PID 928330。三模型 × Chat/Responses 六次真实请求均 HTTP 200、回答 391，合计 618 tokens；LiteLLM 发请求前的六条上游参数记录均无输出长度字段。原始证据在 WSL `provider-defaults-evidence/` 与该网关的 `request-metadata.jsonl`，可重现脚本是隔离目录下 `check_provider_defaults.py`。

本次检查覆盖 Hackathon 入口、网关、浏览器包装器，以及 local_experiment→ARC 矩阵→Runner 适配器路径，并非全仓审计。已删除设施的 64 并发上限、Codex 的额外 4 子代理并发限制、Pi 的 8 次 length 续跑上限、ARC 赛题白名单及自动套用的历史测试数量；无测试生成不再要求 `--separate-evaluation`。正常输入符号链接由快照复制目标内容，目录产物归档保留链接。浏览器包装器在本轮先放开原生 session/profile/CDP 参数，随后按下节决定删除；入口不再拒绝 HTTPS 网关。

保留凭据文件权限、网关与 OTLP 身份、run 路径归属、输入身份、冻结应用身份和真实完成状态检查，这些分别防止实际凭据泄露、跨运行写入或把未完成评测当结果。当前 OTLP 接收器的 16MiB 请求大小限制仍保留：它监听容器可达地址并一次性读入内存；放开这个边界需要同步改变存储读取方式。没有改动独立维护的 Braid/SVC 或旧 raw 基线。除上述真实 API 调用外，其余清理以调用路径审查验证，未运行 Factory 测试或包 smoke；完整 benchmark 终态仍待取得。

旧 128K 网关实例已停止。WSL 四份新包 `{pi,codex}-{base,svc}-defaults.zip` 均已完成；当时补跑控制器 PID 933108 改用 `hackathon-gateway-defaults/gateway.env`，不再传多余的 `separate_evaluation=True`。这个尚未开跑的等待控制器现已由下节 952583 替代，网关仍使用供应商默认输出长度。原首轮八个 job 仍保留原参数，新策略的结果单独记录。

## 浏览器隔离简化（2026-09-24）

用户追问各 variant 的 `browser.py` 是否必要。复查时四个 `variants/pi-team-*/browser.py` 内容完全相同，均从 Pi/Codex session ID 派生浏览器身份、重写 HOME，并禁止原生 session/profile/CDP 选项；上一轮仅放开了 Hackathon 的 `submission/native_browser.py`。共享 `harness/skills/agent-browser/SKILL.md` 当时仍保留禁止覆盖 session 的指令，与已放开的 Hackathon 行为不一致。

冻结 agent-browser 0.38.1 自带会话隔离、`--session` 和 `session id --scope worktree`；无需自建浏览器会话管理。Braid 独立的 PI_CODING_AGENT_DIR/CODEX_HOME 只管理 Agent 配置，不自动决定 agent-browser session；同一环境下多个并行浏览任务使用默认 session 仍会相互影响。依据：https://agent-browser.dev/sessions 及运行时包内 `skill-data/core/references/session-management.md`。

用户回复“请处理”，授权实施上述简化。已删除四份 `variants/pi-team-*/browser.py` 和 `submission/native_browser.py`，移除导入、生成包装脚本和打包引用。运行入口直接设置本 run 的 socket 目录与 Chrome 路径；共享 `agent_support.browser_executable` 只解析便携运行时或原生 npm 安装缓存的 Chrome 文件，不管理会话。共享 skill 改为单任务使用默认会话、并行浏览任务显式命名 session、交接时传递名称；删除绑定原生 Agent ID、重写每个浏览会话 HOME、禁止 session/profile/CDP 参数的约束。

WSL 直接操作冻结运行时的 agent-browser：不提供 Pi/Codex ID，两个 session 并行打开 agent-browser 官网首页和 sessions 文档，各自后续 `get url` 保留原页面；改变 `PI_SESSION_ID` 后仍能通过原 session 名继续读取相同页面。两会话已关闭，原始命令输出在 `factory26-official-local/browser-native-evidence/{home,sessions}.jsonl`。这是原生浏览器实际操作证据，没有启动新的模型任务，也没有运行 Factory 测试或包 smoke；完整 benchmark 尚未结束。

WSL 四份 `{pi,codex}-{base,svc}-native-browser.zip` 已重新冻结。包内入口和 skill 的 SHA256 与当前源码一致，均不含 `native_browser.py`；四包 SHA256 记录在 `browser-native-evidence/packages.json`。已停止旧等待控制器 933108，新控制器 PID 952583 使用这些新包和 `hackathon-gateway-defaults/gateway.env`。它等待首轮 PID 904226 结束后，只补跑 length 失败的 Pi case，最多 4 并发；清单为 `hackathon-pi-native-browser-matrix.json`，结果目录为 `runs/hackathon-pi-native-browser-20260924`，日志为 `hackathon-pi-native-browser-controller.log`。首轮及其冻结包保持原样。

## 官方隐藏测试的产物回放评测（2026-09-24）

用户提出将本地生成软件打成 Agent 包，在官网不勾选“使用比赛额度评测”，并明确：“我说的等待一段时间，说的就是‘包内刻意 sleep’，但大概是 3~5s，而且可以尝试一些模型调用；重点是，我们要取得官方的评分结果。”本轮据此授权构建产物回放包并发起非榜单官网评测，先用已完成的 `codex-base` GitHub、Sheet 两题验证链路；不改变生成应用，不使用比赛额度。

实现采用 `scripts/package_arc_replay.py` 和 `submission/arc_replay.py`：从 completed 的本地 ARC run 打包应用源码，保留 run、需求及逐文件哈希；按传入 `requirements.yaml` 的 SHA256 选择对应产物，等待 3 秒再交付。包明确标注 artifact-replay，不冒充再次生成；官网耗时和模型消耗不能替代本地生成记录。复用现有源码归档排除项，不带 node_modules、构建产物、Agent 会话或凭据；平台负责重新安装依赖、构建和部署。暂不添加模型请求，仅在平台确实要求时再处理。

官网当前页面明确关闭比赛额度的运行不进入排行榜，API 密钥字段仍标记必填。已使用明确的无模型占位值上传并启动回放评测。评价结果只用于这批已冻结产物，不回传隐藏测试给生成 Agent。

首个包已在 WSL 构建：`codex-base-artifact-replay.zip`，98,764 bytes，SHA256 `3f78afcaa8e79029bc00734b46044f08d8ea77cdf22ef93d87624e717805e6d6`。源 run 分别是 `codex-base-hackathon-github-97ad8b8eec`、`codex-base-hackathon-sheet-67ac86e938`；归档分别包含 12、21 个应用文件。官网保存名称 `codex-base-artifact-replay-20260924`，比赛额度 checkbox 已确认关闭，API key 填写无模型调用占位值。官网显示“Started 2 runs”；GitHub 的官方 run 为 `a11ce90b4611`（https://arc-bench.com/runs/a11ce90b4611），已通过既有网站登录客户端保存两题 API 状态和日志到 `runs/playground/<官方 run id>/`，两题现已终态，结果见下文。表单保留的 deepseek-v4-flash 只是未使用的模型字段，真实生成模型和成本仍来自本地 run。

官网实际接线已通过：GitHub run `a11ce90b4611` 显示 generation agent 成功退出、应用完成安装与构建、HTTP 3000 可达，并进入 100 场景的官方 Playwright 评测。Sheet run 为 `e263fcdbc5aa`（https://arc-bench.com/runs/e263fcdbc5aa），任务历史标记失败，具体原因见下段；失败不得在没有测试计数的情况下当成有效零分。

Sheet 的应用已成功部署，官方 API 明确返回 `billing_mode=self_funded`、`status=FAILED`、`failure_reason=Failed to enumerate Playwright tests before execution`、`passed_count=0`、`failed_count=0`、`result_path=null`。这是测试枚举阶段故障，页面/API 的 0 分不是有效的 0/100 测试结果；标准输出只含回放与应用部署成功记录，没有更具体的枚举错误。GitHub 同为 self_funded，现已返回官方测试结果；没有修改应用或测试，也没有添加模型调用。

最终结果：GitHub 官方 run `a11ce90b4611` 返回 `score=1.0`、`test_pass_rate=1.0`、1 passed / 99 failed，共 100 项；逐项状态为 1 passed、9 failed、90 timedOut。唯一通过项为 `REQ-3-1: Search for and Locate Repositories - Scenario 2`。官网运行页同时显示 `Playwright results parsed: passed=1, failed=99, score=1.0`。API 整体 status=FAILED 表示存在失败测试，不应与 Sheet 的 0/0 枚举故障混为一类。

两题 `run_duration_seconds` 均为 3，模型 tokens/cost 均为 null；这里只验证冻结应用的官方功能表现，不能用回放耗时或空费用比较生成效率。原始状态、日志、来源映射保存在本机 `runs/playground/{a11ce90b4611,e263fcdbc5aa}/`，并复制到 WSL `factory26-official-local/hosted-artifact-replay-20260924/`。回放工具和说明提交为 `eec8ca8`。本轮两题验证结束：GitHub 得到 1% 官方测试通过率，Sheet 因官方测试枚举故障未取得有效评分；没有启动其他 variant 的官网评测或根据隐藏测试修改生成应用。
