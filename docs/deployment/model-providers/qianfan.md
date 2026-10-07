# 百度千帆

核对日期：2026-10-02（Asia/Shanghai）。本页记录选型、价格与验证事实；可执行的端点、模型别名、真实请求ID和凭据变量引用归[LiteLLM集中配置](../../../materials/model-gateway.json)。密钥保留在项目私有env中。

## 接入与验证

**百度千帆普通 API**使用凭据前缀`QIANFAN`。相关模型：优先 GLM-5.3；精确请求 ID 待账户模型列表核实。

key 已填；官方端点已核实，本项目尚无实际调用验证。

重点模型为GLM-5.3，账户精确请求ID尚未核实，因此集中网关配置暂不启用该路由。依据为[模型列表接口](https://cloud.baidu.com/doc/qianfan-api/s/Dmba8k71y)。官网价格原单位是元/千tokens，换算为元/M需乘1000。

## 按量价格

单位为每100万tokens（M），输入为未缓存输入。保留原币种，未知项不视为免费。

| 提供商与模型 | 币种 | 输入 / M | 输出 / M | 缓存读取 / M | 缓存写入或存储 | 适用条件与来源 |
| --- | --- | --- | --- | --- | --- | --- |
| 百度千帆 GLM-5.3 | CNY | 4.8 | 16.8 | 1.2 | 未核实 | 2026-09-24 至 10-07 国庆活动，全天价；原价为8 / 28 / 2。[官方活动](https://cloud.baidu.com/product/qianfan_home/campaign.html) |

本项目接入阶段和证据归[提供商任务记录](../../../tasks/external-model-providers/packet.md)。

返回[提供商选型入口](../model-providers.md)。
