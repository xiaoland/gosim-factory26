# 原生 Hackathon 本地运行

此四配置实验已归档，保留运行和证据恢复说明。当前开发入口见 [Variant 索引](../../variants/README.md)，该对照的来源及后继实验入口见[历史基线任务](../../tasks/hackathon-team-baseline/packet.md)，新运行仍按对应 packet 的当前授权执行。

这次对照有 `codex-base`、`codex-svc`、`pi-base`、`pi-svc` 四个配置。Codex 与 Pi 各自使用原生子代理，不经 Braid；同一核心的两组差异是 SVC skill 及其选定方法章节的装载。主 Agent、explorer、executor 使用 GLM 5.3 Flash，advisor 使用 Kimi K3，browser operator 使用 DeepSeek V4 Flash Vision Exp。四组都有 agent-browser 和独立的 `playwright-core`，后者供 Agent 自行检查生成应用。角色由 [hackathon_main.py](../../variants/native-hackathon/hackathon_main.py) 装配。

角色正文位于 `variants/native-hackathon/agents/`，与供主会话选角的简短 description 分开。
Explorer、executor、advisor 直接取得 exploration-tools 指引；SVC 组还分别取得 Explore、Implementation、Design 原文及其导航来源，browser operator 保持工具专项指引。
子代理使用独立历史，父会话在委派中给出必要事实、材料入口和范围。Pi 使用 fresh、append 与显式技能选择，并关闭内建角色；Codex 按原生 spawn 工具字段明确不继承父历史。
各组运行入口均配置 `MCPORTER_CONFIG`，新运行资源包含 rg、ast-grep 和 MCPorter；详细使用方法随 exploration-tools skill 分发。
角色源码和历史冻结 ZIP 的材料不同；对应改造当时未取得完整实验验收。恢复旧实验必须使用它自己的冻结资源，不能依据当前源码推断旧 ZIP 已具备新能力。


只在 WSL 构建、运行模型和评测。自购供应商凭据在项目内 `.secrets/models.env`，权限为 `600`。[hackathon_gateway.py](../../scripts/hackathon_gateway.py) 在 WSL 宿主读取它，向容器只传 `GATEWAY_URL` 与临时 `GATEWAY_TOKEN`。这组历史实验默认由网关移除客户端自带的推理、温度和采样参数，让供应商使用自己的默认值；新实验若需保留现有配方，可为独立网关实例传 `--preserve-parameters`。`request-metadata.jsonl` 记录模型、客户端原始输出预算与规范化参数，不记录消息正文或密钥。官方 Runner 的宿主 `OPENAI_API_KEY` 由适配器清除，避免把第三方密钥交给 ARC Meter。先用 `docker network inspect bridge` 核实容器能访问的宿主地址；历史环境使用 `172.17.0.1`，新环境须重新核对实际地址。

本实验不另设输出长度预算。网关移除客户端的 `max_tokens`、`max_completion_tokens`、`max_output_tokens`，由供应商决定默认行为。Pi 0.85.1 即使省略 descriptor 的 `maxTokens` 仍会自动发送 16384，因此必须在 API 边界移除，单删配置无效。[hackathon_models.json](../../variants/native-hackathon/hackathon_models.json) 只供 Pi 声明上下文信息，网关不再读取参赛包的模型文件。`request-metadata.jsonl` 分别记录规范化参数和 LiteLLM 转换后的上游参数，可检查兼容层是否重新补入上限。修改运行策略时使用新网关实例和新包，保留既有实验的参数记录。

不传长度不代表供应商无限生成，模型默认值与上下文限制仍生效；当时的参数与别名调查见[本地能力任务](../../tasks/hackathon-capabilities/packet.md)，不能作为此刻供应商接口的承诺。`--thinking off` 只避免 Pi 注入推理档位，供应商仍可按其默认策略思考。

在 WSL 仓库执行，输出目录须是全新路径；网关示例的 4013 端口也须先确认空闲：

```sh
python3 scripts/runtime.py linux --backend pi --output ../factory26-official-local/hackathon-runtime-pi
python3 scripts/runtime.py linux --backend codex --output ../factory26-official-local/hackathon-runtime-codex
python3 scripts/package_hackathon.py --runtime ../factory26-official-local/hackathon-runtime-pi --backend pi --output ../factory26-official-local/pi-base.zip
python3 scripts/package_hackathon.py --runtime ../factory26-official-local/hackathon-runtime-pi --backend pi --svc --output ../factory26-official-local/pi-svc.zip
python3 scripts/package_hackathon.py --runtime ../factory26-official-local/hackathon-runtime-codex --backend codex --output ../factory26-official-local/codex-base.zip
python3 scripts/package_hackathon.py --runtime ../factory26-official-local/hackathon-runtime-codex --backend codex --svc --output ../factory26-official-local/codex-svc.zip
python3 scripts/hackathon_gateway.py --python /home/yyh/.local/bin/python3.12 --runtime ../factory26-official-local/hackathon-runtime-codex --state ../factory26-official-local/hackathon-gateway-example-4013 --port 4013
```

每个包的原生会话和 stderr 留在交付工作区 `.arc/hackathon/`；[raw_otlp.py](../../variants/raw/raw_otlp.py) 将根进程及子代理会话事件作为 OTLP logs 上报。上报错误也保存在该目录，不改变生成终态。
Pi 主会话若以模型输出长度上限 `length` 结束，会在同一 session 中继续，原始事件追加保存并记录续跑次数；不另设次数上限，直到自然结束、报错或运行被停止。其他终态不自动重试。Codex 子代理并发采用原生默认值，不额外写死为 4。

运行入口直接使用运行时提供的 agent-browser，仅设置 Chrome 路径和本 run 的 `AGENT_BROWSER_SOCKET_DIR`。单个浏览任务可用默认会话；同一 run 内并行操作不同页面时，各任务显式使用不同的 `--session <name>`，每条命令沿用该名称。交接浏览任务时传递会话名，即可保留页面与登录状态；浏览器会话不绑定 Pi/Codex 的 Agent 身份。原生 profile、CDP 等参数仍可直接使用，连接外部浏览器时由调用者决定共享范围。

主办方赛事页面提供“Download all requirements” ZIP，同时包含 `hackathon--github`、`hackathon--sheet` 的 `requirements.yaml` 和参考图。2026-09-24 下载快照的 SHA256 为 `9884f23ea10c3dfeee170d1eed57966c8fce9a5ce18a0ac43b3d7942eba8c414`；WSL 的原 ZIP 位于 `factory26-official-local/arcbench-hackathon-requirements.zip`，两题提取到 `platform-inputs/hackathon/{github,sheet}/requirements/`，各自的 `source.json` 记录逐文件哈希。ZIP 不包含 Playwright 评测测试。

用 [arc_matrix.py](../../lab/arc_bench/arc_matrix.py) 指定 `--case hackathon/github --case hackathon/sheet --requirements-only`，并传入冻结 ZIP、官方 Runner、镜像、稳定宿主 `--host-runtime <asset.json>` 与 workspace/telemetry/finalization 容量预算、新网关实例的 `--gateway-state` 与容器可达的 OTLP 宿主地址，即可通过 [Runner 适配器](../../lab/arc_bench/arc_bench_adapter.py) 运行本地生成和部署。每个 run 取得独立临时网关凭据，请求诊断按 run 保存并尝试作为 OTLP logs 上报。无测试时结果的 `mode` 是 `requirements-only`、`score` 是 `null`；`completed` 只表示 Agent 入口成功、生成应用具备标准布局、Runner 完成部署，不代表任何官方得分。官方本地 Runner 明确支持省略 `--tests-dir` 并将评测标记为 `skipped`。需要在本地计分时必须另取同一赛题的官方测试，再用有测试的两阶段模式对冻结应用评分，不能用 Lite/Web 测试代替。

## 将冻结产物交给官网评测

已完成应用与生成中明确 Git 提交的回放是跨 Harness 能力，操作、阶段身份和隐藏反馈隔离已归到[恢复与回放手册](recovery.md#冻结应用与阶段提交回放)。本页保留四配置的历史生成条件；回放评分不能当作原生成耗时或模型性能。
