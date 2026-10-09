# 百度千帆

核对日期：2026-10-03（Asia/Shanghai）。本页记录选型、价格与验证事实；可执行的端点、模型别名、真实请求ID和凭据变量引用归[LiteLLM集中配置](../../../materials/model-gateway.json)。密钥保留在项目私有env中。

## 接入与验证

千帆普通按量API与个人Token Plan使用独立端点和凭据，不合并为一个通道。用户已分别填写两套key；本项目尚无这两条通道的实际调用验证，凭据有效性与账户模型权限未验收。

| 通道 | 私有env前缀 | OpenAI兼容Base URL | 验证边界 |
| --- | --- | --- | --- |
| 普通按量API | `QIANFAN` | `https://qianfan.baidubce.com/v2` | 官方列出GLM-5.3请求ID为`glm-5.3`；已加入网关候选路由。 |
| 个人Token Plan（用户称Coding Plan） | `QIANFAN_TOKEN_PLAN` | `https://qianfan.baidubce.com/v2/tokenplan/personal` | 官方列出GLM-5.3请求ID为`glm-5.3`；已加入网关候选路由。 |

个人套餐的Chat请求路径为Base URL后追加`/chat/completions`，使用专属API key，与普通后付费及企业版隔离。依据为[个人版快速开始](https://cloud.baidu.com/doc/qianfan/s/kmracfgi2)、[个人版模型与接入说明](https://cloud.baidu.com/doc/qianfan/s/Dmrabu8b6)及[官方产品页](https://cloud.baidu.com/product/codingplan.html)。不将旧Coding Plan的`/v2/coding`入口与本次用户指定的个人Token Plan入口混用。

普通API的GLM-5.3请求ID同为`glm-5.3`，依据为[官方模型列表](https://cloud.baidu.com/doc/qianfan/s/rmh4stp0j)。选择普通按量通道时传入`--route glm-5.3=qianfan-glm-5.3`；选择个人套餐GLM-5.3时，给新网关实例传入`--route glm-5.3=qianfan-token-plan-glm-5.3`；默认路由保持原选择。可执行映射以集中配置为准，账户权限仍需实际调用核验。

## 个人套餐价格

用户已购买个人套餐，具体档位、成交价和额度尚未记录。按套餐权益及模型抵扣规则消费，下面普通API的元/M活动价不代表套餐价格或其实际抵扣成本。

## 普通API按量价格

单位为每100万tokens（M），输入为未缓存输入。保留原币种，未知项不视为免费。

| 提供商与模型 | 币种 | 输入 / M | 输出 / M | 缓存读取 / M | 缓存写入或存储 | 适用条件与来源 |
| --- | --- | --- | --- | --- | --- | --- |
| 百度千帆 GLM-5.3 | CNY | 4.8 | 16.8 | 1.2 | 未核实 | 2026-09-24 至 10-07 国庆活动，全天价；原价为8 / 28 / 2。[官方活动](https://cloud.baidu.com/product/qianfan_home/campaign.html) |

本项目接入阶段和证据归[提供商任务记录](../../../tasks/external-model-providers/packet.md)。

返回[提供商选型入口](../model-providers.md)。
