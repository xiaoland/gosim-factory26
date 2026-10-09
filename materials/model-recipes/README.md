# 模型配方

DX variant 通过自己的 `model-recipe.json` 选择模型与供应商链。本目录维护可复用的链，[catalog](../model-gateway.json)维护 deployment、端点和参数；model-proxy 执行运输和兼容处理。角色模型及原生请求预算归 variant。

| 输入 | 使用方式 |
| --- | --- |
| [self-funded.json](self-funded.json) | 公共自费供应商链，支持当前配置中的 GLM、Kimi 和 DeepSeek alias。ARC 是已配置链的首道，其余顺序以 JSON 为准。 |
| [self-funded-no-arc.json](self-funded-no-arc.json) | I15 当前选择的自费链；移除 ARC，其它供应商顺序保留。 |
| ARC 平台注入 | 比赛程序直接消费平台 `OPENAI_BASE_URL/API_KEY`，不装配 model-proxy 或自费供应商链。 |

模型调用通道与官网 `self_funded/competition` 评分身份分别配置。连接 ARC API 不代表正式参赛；私有凭据由执行环境注入，不进入公开配方或可迁移 data。

Lab 冻结 variant 所需路由和 selected catalog。`--route FILE` 覆盖本次输入，必须覆盖所需 alias，缺项不取 catalog 默认。打包入口使用 `package_agent.py --gateway-routes FILE`；完整操作见 [Lab](../../lab/README.md)和[公共工具](../../tooling/scripts/README.md)。实际消费与请求是否成功从对应 run 的配置、请求和响应取证。

已运行 proxy 不会自动采用新 JSON。普通 restart 重新消费当前配方；I15 的同任务原生接续默认保留来源冻结路由，显式变更走 `restart --keep-data --route ... --allow-route-change --route-change-reason ...`，核对 alias 和来源 catalog 并保存变更回执。

DeepSeek alias `deepseek-v4-flash-0731` 在 ARC 上使用 wire ID `deepseek-v4-flash`，映射归 catalog。ARC HTTP 402 仅在 JSON 精确匹配 `code=insufficient_balance`、`type=billing_error` 时可切下一道，其它认证错误保留失败；兼容行为由代理实现维护。模型列表查询成功不能证明生成、工具调用、流式响应或账户余额。调用与费用限制见[模型配置说明](../../docs/deployment/model-providers.md)。
