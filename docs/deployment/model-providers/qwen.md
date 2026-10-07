# 千问普通 API 与 Token Plan

核对日期：2026-10-02（Asia/Shanghai）。本页记录选型、价格与验证事实；可执行的端点、模型别名、真实请求ID和凭据变量引用归[LiteLLM集中配置](../../../materials/model-gateway.json)。密钥保留在项目私有env中。

## 接入与验证

**千问普通 API**使用凭据前缀`QWEN`。相关模型：Flash 精确 ID 为 `ZHIPU/GLM-5.3-Flash`；`glm-5.3`、`kimi-k3`。

key 已填；2026-10-02 模型目录 HTTP 200，Flash 单次直接请求 HTTP 200；不等于 Pi 完整接入验收。

**千问 Token Plan**使用凭据前缀`QWEN_TOKEN_PLAN`。相关模型：内部 DeepSeek 使用 `deepseek-v4-flash-0731`；目录亦列 `glm-5.3`。

套餐 key 已填；2026-10-02 模型目录 HTTP 200；当次目录未列 Flash 或 K3。

普通 API 与 Token Plan 分别使用独立凭据。账户模型目录证明模型可见，不证明余额、套餐抵扣或完整工具调用已经验收。各模型1M免费额度是用户提供的账户事实，剩余量和期限尚未独立查询。

## 按量价格

单位为每100万tokens（M），输入为未缓存输入。保留原币种，未知项不视为免费。

| 提供商与模型 | 币种 | 输入 / M | 输出 / M | 缓存读取 / M | 缓存写入或存储 | 适用条件与来源 |
| --- | --- | --- | --- | --- | --- | --- |
| 千问普通 API：Flash、GLM-5.3、K3 | CNY | 待核实 | 待核实 | 待核实 | 待核实 | [官方价格页](https://platform.qianwenai.com/pricing/api)动态加载具体模型单价，本次未取得可采用数值。 |

## 套餐与账户额度

账户实际购买档位、剩余额度和到期日尚未查询；公开价格不是账户账单。

| 通道 | 公开价格或账户事实 | 额度与条件 | 来源 |
| --- | --- | --- | --- |
| 千问 Token Plan 个人版 | 限时 Lite 39、Essential 79、Standard 139、Pro 499 CNY/月；原价60、120、180、600 | 月限额分别11,500、25,500、45,000、180,000 Credits；加油包100 CNY/20,000 Credits。优惠截止日期未标明。 | [官方概述](https://platform.qianwenai.com/docs/token-plan/overview) |
| 千问普通 API | 用户2026-10-02报告 GLM-5.3、K3 各有1M免费额度 | 尚未独立查余额、有效期、输入/输出抵扣口径；不能据此声明当前调用免费。 | [用户决定及记录](../../../tasks/iteration14/dx-resume/packet.md) |

目录及Flash实际调用依据见[I14接续记录](../../../tasks/iteration14/dx-resume/packet.md)。

返回[提供商选型入口](../model-providers.md)。
