# 方舟 Ark Coding Plan

核对日期：2026-10-02（Asia/Shanghai）。本页记录选型、价格与验证事实；可执行的端点、模型别名、真实请求ID和凭据变量引用归[LiteLLM集中配置](../../../materials/model-gateway.json)。密钥保留在项目私有env中。

## 接入与验证

**方舟 Coding Plan**使用凭据前缀`ARK_CODING_PLAN`。公共 catalog 维护 `glm-5.3`、`glm-5.3-flash`、`kimi-k2.7-code` 和 `kimi-k3` 通道；本次主路由和 advisor 选路从[跨 variant 模型配方](../../../materials/model-recipes/README.md)取得，不从供应商候选清单推断。

2026-10-07 新增 GLM-5.3 deployment，精确 Coding Plan 请求名为 `glm-5.3`，OpenAI 端点仍为 `https://ark.cn-beijing.volces.com/api/coding/v3`。官方 [OpenCode 配置](https://docs.volcengine.com/docs/ark/coding-plan-personal-ai-opencode?lang=zh)为该模型列出文本输入、1,024,000 上下文和 65,536 输出限制；集中目录仅为此 deployment 保存这些限制，代理逐次请求限制已存在的输出预算，不改变其它供应商或原生模型上限。只读 `/models` 返回 200，但它列出通用版本模型，没有列出该 Coding alias；请求名依据官方工具配置，工具及流式权限仍以真实运行响应核验。

2026-10-02 接入时已填写套餐 key 并核对端点与模型 ID，当时尚无实际调用验证；这是历史接入状态。后续采用配置及调用结果以所属 run 的冻结路由、网关请求和具体响应为准，不将目录中的旧状态当作本轮未接通或已验收的证明。

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
