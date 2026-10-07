# DeepSeek 原厂

核对日期：2026-10-02（Asia/Shanghai）。本页记录选型、价格与验证事实；可执行的端点、模型别名、真实请求ID和凭据变量引用归[LiteLLM集中配置](../../../materials/model-gateway.json)。密钥保留在项目私有env中。

## 接入与验证

**DeepSeek 原厂**使用凭据前缀`DEEPSEEK`。相关模型：集中网关配置暂不启用DeepSeek原厂路由。当前 Flash 已转接 V4.1，排除该模型；其它模型另行选定。

key 已填；历史 Flash 调用证据保留，不作为当前选型。

当前 Flash 已转接 DeepSeek V4.1，用户明确排除此模型。原厂旧 `deepseek-v4-flash` / Vision Exp ID 也暂时转接到 V4.1，因此不作为当前候选；原厂凭据和历史调用记录保留。其它模型须另行明确选定。依据为[原厂公告](https://api-docs.deepseek.com/news/news260910/)。这一别名关系不推广到千问或 ARC 的0731通道。

历史实际调用依据见[接入记录](../../../tasks/external-model-providers/packet.md)，图片对照与版本限制见[版本调查](../../../tasks/arc-deepseek-version/packet.md)。

返回[提供商选型入口](../model-providers.md)。
