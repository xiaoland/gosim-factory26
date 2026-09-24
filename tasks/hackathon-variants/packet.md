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
