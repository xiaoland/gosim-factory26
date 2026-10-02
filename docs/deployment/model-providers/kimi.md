# Moonshot Kimi

核对日期：2026-10-02（Asia/Shanghai）。本页记录选型、价格与验证事实；可执行的端点、模型别名、真实请求ID和凭据变量引用归[LiteLLM集中配置](../../../harness/model-gateway.json)。密钥保留在项目私有env中。

## 接入与验证

**Moonshot / Kimi 原厂**使用凭据前缀`KIMI`。相关模型：`kimi-k2.7-code`；`kimi-k3`。

key 已填；2026-09-24 K2.7 Code 短文本 HTTP 200；2026-10-02 目录列出 K3、K2.7 Code。

Kimi K3 的缓存写入收费与缓存读取分别记录，不能只用输入、输出单价估算费用。普通 K2.7 Code 保留在选型范围，HighSpeed 排除。

## 按量价格

单位为每100万tokens（M），输入为未缓存输入。保留原币种，未知项不视为免费。

| 提供商与模型 | 币种 | 输入 / M | 输出 / M | 缓存读取 / M | 缓存写入或存储 | 适用条件与来源 |
| --- | --- | --- | --- | --- | --- | --- |
| Moonshot `kimi-k3` | CNY | 20 | 100 | 2 | 写入：5min TTL 为20元/M；1h TTL 为40元/M | 默认 TTL 为5min，命中续期不重复收费；未标价格结束日期。[官方定价](https://platform.kimi.com/docs/pricing/chat) |
| Moonshot `kimi-k2.7-code` | CNY | 6.5 | 27 | 1.3 | 本次表未列单独写入价 | 未列长度阶梯或结束日期。[官方定价](https://platform.kimi.com/docs/pricing/chat) |

历史实际调用依据见[接入记录](../../../tasks/external-model-providers/packet.md)，模型目录核对见[I14记录](../../../tasks/iteration14/dx-resume/packet.md)。

返回[提供商选型入口](../model-providers.md)。
