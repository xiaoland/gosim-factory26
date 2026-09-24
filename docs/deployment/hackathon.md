# 原生 Hackathon 本地运行

这次对照有 `codex-base`、`codex-svc`、`pi-base`、`pi-svc` 四个配置。Codex 与 Pi 各自使用原生子代理，不经 Braid；同一核心的两组只差 SVC skill。主 Agent、explorer、executor 使用 GLM 5.3 Flash，advisor 使用 Kimi K3，browser operator 使用 DeepSeek V4 Flash Vision Exp。四组都有 agent-browser 和独立的 `playwright-core`，后者供 Agent 自行检查生成应用。角色由 [hackathon_main.py](../../submission/hackathon_main.py) 装配。

只在 WSL 构建、运行模型和评测。自购供应商凭据在项目内 `.secrets/models.env`，权限为 `600`。[hackathon_gateway.py](../../scripts/hackathon_gateway.py) 在 WSL 宿主读取它，向容器只传 `GATEWAY_URL` 与临时 `GATEWAY_TOKEN`。网关统一每次请求的 16384 输出 token 上限，移除各客户端自带的推理、温度和采样参数，让供应商使用自己的默认值；`request-metadata.jsonl` 记录模型与规范化参数，不记录消息正文或密钥。官方 Runner 的宿主 `OPENAI_API_KEY` 由适配器清除，避免把第三方密钥交给 ARC Meter。先用 `docker network inspect bridge` 核实容器能访问的宿主地址；本机是 `172.17.0.1`。

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

正式矩阵需在 `platform-inputs/hackathon/<task>/` 放入官方公开需求、测试与来源哈希，再通过 [arc_matrix.py](../../scripts/arc_matrix.py) 的 `--case hackathon/<task>` 建立作业，传入网关生成的 `gateway.env`，使用 `--separate-evaluation`。本地 [Runner 适配器](../../scripts/arc_bench_adapter.py) 先生成应用，再对冻结源码评分。2026-09-24 的本地官方资产只有 Lite/Web，官网 API 返回“系统维护”；缺少 Hackathon 两题输入时无法启动有效本地评分。不要用 Lite/Web 或自拟题替代正式结果。
