# 原生 Hackathon 本地运行

这次对照有 `codex-base`、`codex-svc`、`pi-base`、`pi-svc` 四个配置。Codex 与 Pi 各自使用原生子代理，不经 Braid；同一核心的两组只差 SVC skill。主 Agent、explorer、executor 使用 GLM 5.3 Flash，advisor 使用 Kimi K3，browser operator 使用 DeepSeek V4 Flash Vision Exp。四组都有 agent-browser 和独立的 `playwright-core`，后者供 Agent 自行检查生成应用。角色由 [hackathon_main.py](../../submission/hackathon_main.py) 装配。

只在 WSL 构建、运行模型和评测。自购供应商凭据在项目内 `.secrets/models.env`，权限为 `600`。[hackathon_gateway.py](../../scripts/hackathon_gateway.py) 在 WSL 宿主读取它，向容器只传 `GATEWAY_URL` 与临时 `GATEWAY_TOKEN`。网关移除各客户端自带的推理、温度和采样参数，让供应商使用自己的默认值；`request-metadata.jsonl` 记录模型、客户端原始输出预算与规范化参数，不记录消息正文或密钥。官方 Runner 的宿主 `OPENAI_API_KEY` 由适配器清除，避免把第三方密钥交给 ARC Meter。先用 `docker network inspect bridge` 核实容器能访问的宿主地址；本机是 `172.17.0.1`。

输出预算由 [hackathon_models.json](../../submission/hackathon_models.json) 集中声明，Pi 主会话、原生子代理和网关共用。当前三模型单次输出预算均为 131072，包含推理和正文；这是本实验预算，不表示三个模型的最大能力相同。GLM 5.3 Flash 的官方默认值为 65536、最大值为 131072；Kimi K3 默认 131072、最大可设 1048576；DeepSeek 当前 Flash 最大支持 384K。后二者无需为解决本轮 16K 截断而直接配置到最大值。依据：[GLM 参数](https://docs.bigmodel.cn/cn/guide/start/concept-param)、[Kimi Chat API](https://platform.kimi.com/docs/api/chat)、[DeepSeek 参数](https://api-docs.deepseek.com/quick_start/pricing/)。DeepSeek 官方已将本实验保留的 `deepseek-v4-flash-vision-exp` 别名路由到 V4.1 Flash；其与 Kimi K3 的上下文声明均更新为 1M。

Pi 0.85.1 的自定义模型省略 `maxTokens` 会采用 16384，并不会省略 API 输出预算。Pi 发送前还会按剩余上下文缩小预算，网关必须保留这个较小值；客户端没有指定时使用集中配置，超过配置时取配置上限。网关启动时保存 `model-limits.json` 快照，打包器将同一文件冻结进 ZIP。修改后须使用新网关实例和新包，不在既有实验中途替换参数。`--thinking off` 仅避免 Pi 注入推理档位；GLM 5.3 Flash 仍按供应商默认进行思考，不能把它当成关闭上游推理。

在 WSL 仓库执行，输出目录须是全新路径：

```sh
python3 scripts/runtime.py linux --backend pi --output ../factory26-official-local/hackathon-runtime-pi
python3 scripts/runtime.py linux --backend codex --output ../factory26-official-local/hackathon-runtime-codex
python3 scripts/package_hackathon.py --runtime ../factory26-official-local/hackathon-runtime-pi --backend pi --output ../factory26-official-local/pi-base.zip
python3 scripts/package_hackathon.py --runtime ../factory26-official-local/hackathon-runtime-pi --backend pi --svc --output ../factory26-official-local/pi-svc.zip
python3 scripts/package_hackathon.py --runtime ../factory26-official-local/hackathon-runtime-codex --backend codex --output ../factory26-official-local/codex-base.zip
python3 scripts/package_hackathon.py --runtime ../factory26-official-local/hackathon-runtime-codex --backend codex --svc --output ../factory26-official-local/codex-svc.zip
python3 scripts/hackathon_gateway.py --python /home/yyh/.local/bin/python3.12 --runtime ../factory26-official-local/hackathon-runtime-codex --state ../factory26-official-local/hackathon-gateway
```

每个包的原生会话和 stderr 留在交付工作区 `.arc/hackathon/`；[raw_otlp.py](../../submission/raw_otlp.py) 将根进程及子代理会话事件作为 OTLP logs 上报。上报错误也保存在该目录，不改变生成终态。
Pi 主会话若以模型输出长度上限 `length` 结束，会在同一 session 上最多续跑 8 次，原始事件继续追加；达到上限仍未自然结束时保留失败状态。其他终态不自动重试。

主办方赛事页面提供“Download all requirements” ZIP，同时包含 `hackathon--github`、`hackathon--sheet` 的 `requirements.yaml` 和参考图。2026-09-24 下载快照的 SHA256 为 `9884f23ea10c3dfeee170d1eed57966c8fce9a5ce18a0ac43b3d7942eba8c414`；WSL 的原 ZIP 位于 `factory26-official-local/arcbench-hackathon-requirements.zip`，两题提取到 `platform-inputs/hackathon/{github,sheet}/requirements/`，各自的 `source.json` 记录逐文件哈希。ZIP 不包含 Playwright 评测测试。

用 [arc_matrix.py](../../scripts/arc_matrix.py) 指定 `--case hackathon/github --case hackathon/sheet --requirements-only --separate-evaluation`，并传入四个冻结 ZIP、官方 Runner、镜像、自购网关的 `gateway.env` 与容器可达的 OTLP 宿主地址，即可通过 [Runner 适配器](../../scripts/arc_bench_adapter.py) 运行本地生成和部署。无测试时结果的 `mode` 是 `requirements-only`、`score` 是 `null`；`completed` 只表示 Agent 入口成功、生成应用具备标准布局、Runner 完成部署，不代表任何官方得分。官方本地 Runner 明确支持省略 `--tests-dir` 并将评测标记为 `skipped`。需要计分时必须另取同一赛题的官方测试，再用有测试的两阶段模式对冻结应用评分，不能用 Lite/Web 测试代替。
