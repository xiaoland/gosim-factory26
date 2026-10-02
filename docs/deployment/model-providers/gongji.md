# 共绩算力 MaaS

核对日期：2026-10-02（Asia/Shanghai）。本页记录选型、价格与验证事实；可执行的端点、模型别名、真实请求ID和凭据变量引用归[LiteLLM集中配置](../../../harness/model-gateway.json)。密钥保留在项目私有env中。

## 接入与验证

**共绩算力 MaaS**使用凭据前缀`GONGJI`。相关模型：普通备选，尚未指定重点模型；官方 Flash 示例为 `z-ai/glm-5.3-flash`。

key 已填；官方端点已核实，本项目尚无实际调用验证。

当前作为普通备选，尚未指定重点模型。官方示例Flash ID为 `z-ai/glm-5.3-flash`，账户权限与调用能力待验证。[快速上手](https://docs.suanli.cn/llm/quickstart)

## 按量价格

单位为每100万tokens（M），输入为未缓存输入。保留原币种，未知项不视为免费。

| 提供商与模型 | 币种 | 输入 / M | 输出 / M | 缓存读取 / M | 缓存写入或存储 | 适用条件与来源 |
| --- | --- | --- | --- | --- | --- | --- |
| 共绩算力 | CNY | 待核实 | 待核实 | 待核实 | 待核实 | 先选定精确模型，再查[官方价格入口](https://suanli.cn/price/)或模型广场。 |

本项目接入阶段和证据归[提供商任务记录](../../../tasks/external-model-providers/packet.md)。

返回[提供商选型入口](../model-providers.md)。
