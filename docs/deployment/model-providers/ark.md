# 方舟 Ark Coding Plan

核对日期：2026-10-02（Asia/Shanghai）。本页记录选型、价格与验证事实；可执行的端点、模型别名、真实请求ID和凭据变量引用归[LiteLLM集中配置](../../../materials/model-gateway.json)。密钥保留在项目私有env中。

## 接入与验证

**方舟 Coding Plan**使用凭据前缀`ARK_CODING_PLAN`。相关模型：优先 `glm-5.3-flash`。

套餐 key 已填；官方端点和模型 ID 已核实，本项目尚无实际调用验证。

方舟 **Ark Coding Plan** 与 **ARC Benchmark** 是独立通道。套餐限定个人开发及支持的 AI 编程工具，接入实验 Harness 时需要核对工具范围，不能当成通用 API 服务额度。[官方概览](https://console.volcengine.com/ark/region:cn-beijing/docs/ark/coding-plan-personal-plan-overview?lang=zh)

额度在支持的工具间共享。每5小时限额从首次请求起按5小时周期刷新，周限额每周一00:00重置，月限额每订阅月第1日00:00重置。耗尽后等待刷新，不扣其它资源包或账户余额。账户具体额度和已用量以开通管理页为准。[官方概览](https://console.volcengine.com/ark/region:cn-beijing/docs/ark/coding-plan-personal-plan-overview?lang=zh)

套餐须使用专用key及Coding端点，普通按量端点不抵扣套餐。模型接入依据为[官方Pi配置](https://docs.volcengine.com/docs/ark/coding-plan-personal-ai-pi?lang=zh)。

## 套餐与账户额度

账户实际购买档位、剩余额度和到期日尚未查询；公开价格不是账户账单。

| 通道 | 公开价格或账户事实 | 额度与条件 | 来源 |
| --- | --- | --- | --- |
| 方舟 Ark Coding Plan 个人版 | Lite 原价40、Pro原价200 CNY/月；活动价9.9、49.9 CNY/月 | 2026-06-08至11-08，最多首两个月优惠，第三个月恢复原价；名额有限，新购/续费/升配共享优惠资格。账户实际档位与剩余资格待核实。 | [用户指定套餐概览](https://console.volcengine.com/ark/region:cn-beijing/docs/ark/coding-plan-personal-plan-overview?lang=zh)、[官方优惠规则](https://docs.volcengine.com/docs/ark/coding-plan-personal-universal-promotion?lang=zh) |

本项目接入阶段和证据归[提供商任务记录](../../../tasks/external-model-providers/packet.md)。

返回[提供商选型入口](../model-providers.md)。
