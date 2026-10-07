# BigModel 智谱

核对日期：2026-10-02（Asia/Shanghai）。本页记录选型、价格与验证事实；可执行的端点、模型别名、真实请求ID和凭据变量引用归[LiteLLM集中配置](../../../materials/model-gateway.json)。密钥保留在项目私有env中。

## 接入与验证

**BigModel / 智谱原厂**使用凭据前缀`GLM`。相关模型：`glm-5.3-flash`；GLM-5.3 候选。

key 已填；2026-09-24 Flash 短文本 HTTP 200。

## 按量价格

单位为每100万tokens（M），输入为未缓存输入。保留原币种，未知项不视为免费。

| 提供商与模型 | 币种 | 输入 / M | 输出 / M | 缓存读取 / M | 缓存写入或存储 | 适用条件与来源 |
| --- | --- | --- | --- | --- | --- | --- |
| BigModel `glm-5.3` | CNY | 8 | 28 | 2 | 缓存存储限时免费，结束日期未知 | 本次模型行未设长度阶梯。[官方定价](https://docs.bigmodel.cn/cn/guide/start/pricing.md) |
| BigModel `glm-5.3-flash` | CNY | 0.8 | 2.8 | 0.23 | 缓存存储限时免费，结束日期未知 | 本次模型行未设长度阶梯。[官方定价](https://docs.bigmodel.cn/cn/guide/start/pricing.md) |

历史实际调用依据见[接入记录](../../../tasks/external-model-providers/packet.md)。

返回[提供商选型入口](../model-providers.md)。
