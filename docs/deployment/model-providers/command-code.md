# Command Code GOAT

核对日期：2026-10-02（Asia/Shanghai）。本页记录选型、价格与验证事实；可执行的端点、模型别名、真实请求ID和凭据变量引用归[LiteLLM集中配置](../../../harness/model-gateway.json)。密钥保留在项目私有env中。

## 接入与验证

**Command Code GOAT**使用凭据前缀`COMMAND_CODE`。相关模型：优先 `z-ai/glm-5.3-flash`。

key 尚未填写；官方端点和模型 ID 已核实，本项目尚无实际调用验证。

重点模型为GLM-5.3 Flash，公开token价格用于套餐计量，不能直接当成购买套餐后的实际单位成本。[Provider API](https://commandcode.ai/docs/provider)、[Flash发布](https://commandcode.ai/blog/glm-5-3-flash-aka-ox-alpha-is-live-with)

## 按量价格

单位为每100万tokens（M），输入为未缓存输入。保留原币种，未知项不视为免费。

| 提供商与模型 | 币种 | 输入 / M | 输出 / M | 缓存读取 / M | 缓存写入或存储 | 适用条件与来源 |
| --- | --- | --- | --- | --- | --- | --- |
| Command Code GLM-5.3 Flash | USD | 0.15 | 0.50 | 0.03 | 官方表列“—” | GOAT 文档公布的 token 计量价；实际消耗订阅额度，不能直接当作订阅购买成本。[官方 GOAT](https://commandcode.ai/docs/plans/goat) |

## 套餐与账户额度

账户实际购买档位、剩余额度和到期日尚未查询；公开价格不是账户账单。

| 通道 | 公开价格或账户事实 | 额度与条件 | 来源 |
| --- | --- | --- | --- |
| Command Code GOAT | 10 USD/月 | 通用说明为每5小时14、每周35、每月70 USD usage；Flash 模型行列月额度60 USD。两者是不同层次的限额，不把 Flash 写成70 USD专属额度；实际共享和扣减以账户用量页为准。 | [官方 GOAT](https://commandcode.ai/docs/plans/goat) |

本项目接入阶段和证据归[提供商任务记录](../../../tasks/external-model-providers/packet.md)。

返回[提供商选型入口](../model-providers.md)。
