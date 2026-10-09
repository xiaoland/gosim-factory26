# ARC 实验通道

核对日期：2026-10-08（Asia/Shanghai）。本页记录选型、价格与验证事实；可执行的端点、模型别名、真实请求ID和凭据变量引用归[集中模型目录](../../../materials/model-gateway.json)。密钥保留在项目私有env中。

## 接入与验证

ARC 账户额度通道的端点为 `https://api.arc-bench.com/v1`，公共 catalog 使用 `ARC_BASE_URL`、`ARC_API_KEY` 环境引用；私有凭据保留在 `.secrets/models.env`，沿用项目已有 ARC 账户 key。ARC 与方舟 Ark 是不同通道。

2026-10-08 用户报告额度恢复并授权作为自费配方第一道。只读 `GET /v1/models` 返回 HTTP 200，列出 `glm-5.3`、`glm-5.3-flash`、`kimi-k2.7-code`、`kimi-k3` 和 `deepseek-v4-flash`；这些模型已加入[公共自费配方](../../../materials/model-recipes/self-funded.json)首道。没有发生成请求，没有查询账户余额，不宣称完整兼容验收。原始清单与请求收据归 `runs/arc-self-funded-20261008/`。

用户随后明确“ARC的旧模型ID就是0731版本，这是早就确认的事情”。当前配置据此采用显式映射：稳定 alias `deepseek-v4-flash-0731` → ARC wire ID `deepseek-v4-flash`，同样放入自费首道。此前调查的较强推断及直接证据限制保留为历史，不覆盖本次用户确认。历史 `deepseek-flash` 请求曾被团队权限拒绝，本次清单仍未列出该 ID；不将它混入 0731 配方。版本历史见[调查记录](../../../tasks/arc-deepseek-version/packet.md)。

历史原生错误记录保存 HTTP 402 / `code=insufficient_balance`、`type=billing_error` 和 `access key balance is exhausted`，不是独立原始 HTTP 响应体。代理只对 ARC 的完整、可解析 JSON（顶层或 `error` 包装）精确匹配这两个字段后转后备，继续保留真实诊断；其它 401/402/403 不放开。没有通过收费调用重新制造余额耗尽。
## 按量价格

单位为每100万tokens（M），输入为未缓存输入。保留原币种，未知项不视为免费。

| 提供商与模型 | 币种 | 输入 / M | 输出 / M | 缓存读取 / M | 缓存写入或存储 | 适用条件与来源 |
| --- | --- | --- | --- | --- | --- | --- |
| ARC 冻结模型 | 未核实 | 待核实 | 待核实 | 待核实 | 待核实 | 应取该通道实际计价与账单，不套用原厂价；旧余额和免费额度拒绝记录不能作为当前额度。 |

## 套餐与账户额度

账户实际购买档位、剩余额度和到期日尚未查询；公开价格不是账户账单。

| 通道 | 公开价格或账户事实 | 额度与条件 | 来源 |
| --- | --- | --- | --- |
| ARC | 用户2026-10-08报告额度恢复；当前余额未查询 | 生成通道、官方提交凭据和评分费用模式分别冻结；历史授权不自动恢复暂停实验。 | [实验边界](../../../AGENTS.md#实验边界)、[平台与制品](../competition.md) |

本项目接入阶段和证据归[提供商任务记录](../../../tasks/external-model-providers/packet.md)。

返回[提供商选型入口](../model-providers.md)。
