# 跨 variant 模型配方

供应商模型配方属于 variant：DX variant 通过自身 `model-recipe.json` 声明所需模型及供应商链引用。本目录集中维护可复用的供应商链，catalog 集中维护各供应商模型参数；公共 model-proxy 负责执行配方和归一化运输，不替 variant 选择配方。角色模型与原生请求预算同样归 variant。官网比赛没有 model-proxy，不应用供应商配方，直接消费平台注入的 `OPENAI_BASE_URL` 和 `OPENAI_API_KEY`。选择配方不自动改变任务、执行宿主或评分身份。

| 配方 | 配置归属与消费方式 |
| --- | --- |
| ARC API | 使用 ARC 的模型接口和相应账户额度，沿所属实验的明确端点、凭据引用及冻结 bindings 装配。接入事实见 [ARC 通道](../../docs/deployment/model-providers/arc.md)。2026-10-08 已按用户授权纳入公共自费配方首道；ARC 独立历史配方仍保留原身份。 |
| 自费 | [self-funded.json](self-funded.json)维护已确认模型的有序供应商链。Lab 装配冻结所需路由和 selected catalog，DX 程序启动包内网关，原生客户端只消费 loopback 绑定；最终调用是否成功仍由 run 请求与响应证明。可用 deployment 及端点映射归 [catalog](../model-gateway.json)，私有凭据由执行环境注入。其它角色模型需要已有明确配置，不能由 catalog 默认补成用户决定。 |
| 比赛 | 使用比赛平台向参赛执行注入的模型接口、凭据与模型范围，绑定实际参赛任务及比赛额度；不把自费供应商链打包成比赛配方。参赛与平台绑定边界见[平台与制品](../../docs/deployment/competition.md)。 |

这三种是模型调用配方。官网接口中的 self_funded/competition 是提交或评测身份，不是上述配方的统一选择器；ARC API 配方也不能仅凭“ARC”推断为正式比赛。执行位置、模型通道、评分身份和授权分别明确。

自费 JSON 维护 GLM-5.3、GLM-5.3-Flash、Kimi-K2.7-code，以及当前 I14 使用的 Kimi-K3 和 DeepSeek-V4-Flash-0731 的已选路由，跨 variant 复用；它不要求所有 variant 使用这些模型，也不改写 variant 的参数。角色模型由 variant/本次输入选定，配方解析其所需通道，run 保存实际消费配置和请求记录。既有冻结配置保持原身份，更新公共配方不改变在途运行。

2026-10-08 用户确认“ARC API 额度恢复了，可以加到自费 API 运行的配方中，作为第一道”，随后指定“可以将千帆 Token Plan 从配方下架了”。公共配方已在 GLM-5.3、GLM-5.3-Flash、Kimi-K2.7-code 、Kimi-K3 和 DeepSeek-V4-Flash-0731 前置 ARC，并从所有链移除千帆个人 Token Plan，保留其余供应商顺序。ARC 使用 `ARC_BASE_URL`、`ARC_API_KEY`，独立于 Ark Coding Plan。用户随后明确“ARC的旧模型ID就是0731版本，这是早就确认的事情”，因此 DeepSeek 的稳定 alias `deepseek-v4-flash-0731` 显式映射 ARC wire ID `deepseek-v4-flash`，其链为 ARC → 千问 Token Plan → 千问普通 API。当前 GLM-5.3 链为 ARC → Ark Coding Plan → 千问 Token Plan → 千问普通 API，仍在已有四道上限内。

ARC `/v1/models` 的只读请求已返回 HTTP 200 并列出五个所需 wire ID；这不等于模型生成、工具、流式或当前余额验收。ARC HTTP 402 的完整 JSON（顶层或 `error` 包装）同时精确匹配 `code=insufficient_balance`、`type=billing_error` 时可切下一道；其它认证错误仍终止。该窄例外依据历史原生错误记录，未通过收费请求重现。代理没有在途配置 reload，已运行实例保持旧身份；采用新配方须在原请求安全结束并取得旧执行停止证明后沿同 run 恢复合同冻结新实例。

新 Lab 的自费生成与独立评测通过同一装配函数冻结 variant 声明的路由、catalog 和凭据引用；target 不再选择供应商配方。`--route` 可替代本次配方输入，但必须覆盖 variant 所需模型，缺项不取 catalog 默认。普通 restart 重新消费当前 variant 的配方，显式 route override 保留为输入；在途 run 不热改。2026-10-07 的 Pi/WSL 接续已观察到千帆 GLM-5.3-Flash 返回 HTTP 200，证明当次实际消费了自费配方；随后传输故障仍导致生成失败，不代表完整验收通过。实际记录见[验收记录](../../tasks/finals-experiment-loop/evaluation.md)。

I15 当前自费声明改用 [self-funded-no-arc.json](self-funded-no-arc.json)：仅移除 ARC provider，保留各模型其它既有供应商的顺序，不改变其它variant的默认配方。已有 proxy 不会自动采用；I15 原生接续默认仍保留来源冻结路由。用户明确授权改变已有供应商链时，正常 `lab restart --keep-data --route ... --allow-route-change --route-change-reason ...` 在控制来源前检查 alias 集合及来源冻结 catalog，保存变更收据并复用 I15 的 routing-change 身份校验，不重建业务应用或原生历史。

可将公共自费文件交给已有 `tooling/scripts/package_agent.py --gateway-routes` 材料入口；这仍只证明所选配置进入材料，不证明运行网关成功启动。新 Lab 将路由及 catalog 传给 DX builder，运行入口消费冻结文件；本地从执行环境读取所需凭据，Hosted 包内保留私有输入，均不进入迁移 data。完整参数及实际可用性见 [Lab](../../lab/README.md)和[打包说明](../../tooling/scripts/README.md)。目前并未实现三种配方的统一命名选择器；本文不构成模型执行授权。
