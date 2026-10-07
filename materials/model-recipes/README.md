# 跨 variant 模型配方

模型配方选择调用通道、费用来源和模型到通道的绑定，独立于 variant。当前有 ARC API、自费、比赛三种；variant 负责 Agent 行为与角色模型，装配者按本次输入应用所选配方。选择配方不自动改变任务、执行宿主或评分身份。

| 配方 | 配置归属与消费方式 |
| --- | --- |
| ARC API | 使用 ARC 的模型接口和相应账户额度，沿所属实验的明确端点、凭据引用及冻结 bindings 装配。接入事实见 [ARC 通道](../../docs/deployment/model-providers/arc.md)。当前公共 deployment catalog 未纳入 ARC，已有配置按其原装配入口消费，不根据自费链生成 ARC 路由。 |
| 自费 | [self-funded.json](self-funded.json)维护已确认模型的有序供应商链。Lab 装配冻结所需路由和 selected catalog，DX 程序启动包内网关，原生客户端只消费 loopback 绑定；最终调用是否成功仍由 run 请求与响应证明。可用 deployment 及端点映射归 [catalog](../model-gateway.json)，私有凭据由执行环境注入。其它角色模型需要已有明确配置，不能由 catalog 默认补成用户决定。 |
| 比赛 | 使用比赛平台向参赛执行注入的模型接口、凭据与模型范围，绑定实际参赛任务及比赛额度；不把自费供应商链打包成比赛配方。参赛与平台绑定边界见[平台与制品](../../docs/deployment/competition.md)。 |

这三种是模型调用配方。官网接口中的 self_funded/competition 是提交或评测身份，不是上述配方的统一选择器；ARC API 配方也不能仅凭“ARC”推断为正式比赛。执行位置、模型通道、评分身份和授权分别明确。

自费 JSON 维护 GLM-5.3、GLM-5.3-Flash、Kimi-K2.7-code，以及当前 I14 使用的 Kimi-K3 和 DeepSeek-V4-Flash-0731 的已选路由，跨 variant 复用；它不要求所有 variant 使用这些模型，也不改写 variant 的参数。角色模型由 variant/本次输入选定，配方解析其所需通道，run 保存实际消费配置和请求记录。既有冻结配置保持原身份，更新公共配方不改变在途运行。

新 Lab 默认 target 已选择 `model_recipe: self-funded`，生成与独立评测通过同一装配函数冻结所选路由、catalog 和凭据引用。生成按 variant 的 `model_aliases` 筛选有序链；`--route` 可替代本次配方输入，但必须覆盖所需模型，缺项不取 catalog 默认。2026-10-07 的 Pi/WSL 接续已观察到千帆 GLM-5.3-Flash 返回 HTTP 200，证明实际消费了该配方；随后传输故障仍导致生成失败，不代表完整验收通过。实际记录见[验收记录](../../tasks/finals-experiment-loop/evaluation.md)。

可将公共自费文件交给已有 `tooling/scripts/package_agent.py --gateway-routes` 材料入口；这仍只证明所选配置进入材料，不证明运行网关成功启动。新 Lab 将路由及 catalog 传给 DX builder，运行入口消费冻结文件；本地从执行环境读取所需凭据，Hosted 包内保留私有输入，均不进入迁移 data。完整参数及实际可用性见 [Lab](../../lab/README.md)和[打包说明](../../tooling/scripts/README.md)。目前并未实现三种配方的统一命名选择器；本文不构成模型执行授权。
