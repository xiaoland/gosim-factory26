# MiniMax 官方

核对日期：2026-10-03（Asia/Shanghai）。本页记录中国区普通按量API，使用私有env前缀`MINIMAX`。重点模型为M3，客户端别名`minimax-m3`映射到官方请求ID`MiniMax-M3`，大小写按官方保留。可执行映射与凭据引用归[LiteLLM集中配置](../../../materials/model-gateway.json)。

## 接入与验证

[官方OpenAI SDK说明](https://platform.minimax.cn/docs/api-reference/text-openai-api)列出中国区Base URL为`https://api.minimax.cn/v1`，Chat路径追加`/chat/completions`；旧`platform.minimaxi.com`文档入口当前重定向至`platform.minimax.cn`。本项目新增`MINIMAX_API_KEY`空值供填写，使用普通开放平台API key；Token Plan订阅key及套餐权益另属通道，不在本次配置内。账户权限、连通性和实际工具调用均未验收。

选择M3时为新实例传入`--alias minimax-m3 --route minimax-m3=minimax-official-m3`。`--alias`限定本实例启用的模型；省略时启动器会装配整个目录，所选通道的key必须已填。只运行其它模型时继续显式列出所需alias，避免要求未启用的MiniMax凭据。

官方声明M3上下文为1M，并支持文本、图片、视频和工具；这些是供应商能力说明，不能作为本项目LiteLLM及原生客户端的完整验收。多轮工具调用需保留完整assistant返回与思考内容；本次不改变已有兼容层。

## 普通API按量价格

单位为人民币元/100万tokens，标准服务层级。按输入长度区分价格，缓存写入或存储费用未在M3表中明确列出。

| 输入长度 | 未缓存输入 / M | 输出 / M | 缓存读取 / M |
| --- | --- | --- | --- |
| ≤512K tokens | 2.10 | 8.40 | 0.42 |
| >512K tokens | 4.20 | 16.80 | 0.84 |

[官方按量定价](https://platform.minimax.cn/docs/guides/pricing-paygo)标注上述价格为永久五折；`service_tier=priority`按标准价的1.5倍计费。本路由不主动启用priority，实际收费以账户账单为准。

本项目接入证据归[提供商任务记录](../../../tasks/external-model-providers/packet.md)。返回[提供商选型入口](../model-providers.md)。
