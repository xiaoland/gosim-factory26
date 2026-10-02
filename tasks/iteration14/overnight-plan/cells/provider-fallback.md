# Provider fallback 调查与当前建议（2026-10-02）

## 当前账户事实

今晚只考虑四个渠道：ARK Coding Plan、千问普通 API、千问 Token Plan Essential、DeepSeek 原厂。历史 BigModel/Kimi 默认不进入推荐链，也不能从 BigModel 推导 K3 可用性。

用户从 Helium 后台读回的事实：

- Token Plan 是 Essential，2026-10-02 23:04:20 月已用 57.86%；可见 `glm-5.3`、`deepseek-v4-flash-0731`、`deepseek-v4-pro`、`deepseek-v4-pro-0813`，不列 Flash/K3。页面 endpoint 为 `token-plan.cn-beijing.maas.aliyuncs.com/compatible-mode/v1`，私有 env 历史 endpoint 是用户指定的 `token-plan.maas.qianwenaiapi.com`，两者差异须在真实请求前核对。
- ARK Pro 页面显示 5 小时、周、月额度均 0% 已用，当前实际配置模型 ID 为 `glm-5.3-flash`、`glm-5.3`、`kimi-k3`、`kimi-k2.7-code`、`deepseek-v4-flash`、`deepseek-v4-pro`。页面可见不等于工具、流式或 Responses 已验收。
- 普通 API 免费额度页：`kimi-k3` 剩 798.3K/1M，`deepseek-v4-flash-0731` 剩 1M/1M，均未开启“用完即停”；裸 `glm-5.3` 免费额度/期限显示 `-`（未知，不能当零），`ZHIPU/GLM-5.3-Flash` 显示 0/0（未获免费配额，不能解读为普通 API 余额耗尽）。普通账单本月 74.67 元，总含订阅 153.67 元；余额未知，普通 API 不是零成本。
- 旧阿里 Coding Plan 与当前 Token Plan Essential 是不同服务；旧 Coding Plan 条款不套用 Token Plan，也不靠用户确认豁免。当前方案不把旧 Coding Plan 纳入候选。

## 当前采用的候选链

稳定客户端 alias 继续使用精确模型名；`chat`、`responses`、视觉等是能力字段，不新增 `chat-code`/`responses-code` 等模型别名，以免破坏现有预算护栏。

| 精确 alias | 候选顺序 | 采用理由与缺口 |
| --- | --- | --- |
| `glm-5.3-flash` | ARK `glm-5.3-flash` → 普通 Qwen `ZHIPU/GLM-5.3-Flash` | ARK 为当前主路由；普通 Qwen 作为 fallback，但免费额度为 0/0，按量费用和余额必须显式记录。Token Plan 不列 Flash，不能加入。 |
| `glm-5.3` | ARK `glm-5.3` → Token Plan `glm-5.3` → 普通 Qwen `glm-5.3` | 三者页面/目录有不同程度证据；Token Plan 已用 57.86%，普通 Qwen 裸 GLM 免费额度未知。需逐项确认精确 wire ID、工具和 API 形态。 |
| `kimi-k3` | ARK `kimi-k3` → 普通 Qwen `kimi-k3` | Token Plan 不列 K3；普通 Qwen 尚有 798.3K 免费额度，但仍需记录“用完即停”未开启和账户费用边界。 |
| `kimi-k2.7-code` | ARK `kimi-k2.7-code` | 当前没有四渠道中已确认的等价备用；用户只排除 highspeed 变体，不能扩大为其它未确认模型。无 candidate 才停止该 alias。 |
| `deepseek-v4-flash-0731` | Token Plan `deepseek-v4-flash-0731` → 普通 Qwen `deepseek-v4-flash-0731` | 普通 Qwen 剩 1M/1M；这是同 ID fallback。ARK 的 `deepseek-v4-flash` 没有版本等价证据，移出候选；DeepSeek 原厂不强填。 |
| `deepseek-v4-pro` | Token Plan `deepseek-v4-pro` → ARK `deepseek-v4-pro` | 两个账户页面均可见；需验收实际 wire ID、工具/Responses 兼容和额度。 |

视觉请求只能使用已做视觉真实验收的同模型 deployment；不能用文字模型 fallback 代替。Flash 的视觉链仍需单独验收，文本 HTTP 200 不证明视觉能力。

候选链是实验方案提议，不代表已受理或已启动。每个候选应在冻结配置中保留 provider、plan、wire model、endpoint 非敏感部分和账户身份。

## LiteLLM 1.102.0 实际能力

已定位本机 uv 缓存：`/Users/lanzhijiang/.cache/uv/archive-v0/zil2Bd8JCYkrBEUd/litellm-1.102.0.dist-info/METADATA`，版本为 1.102.0；只读源码，未安装或修改依赖。

冻结 `litellm/router.py` 确认原生 Router 有：

- `fallbacks`、`max_fallbacks`、`num_retries`、`RetryPolicy`、`allowed_fails`、`cooldown_time`；同 model group 多 deployment 也可失败重选。
- `enable_weighted_failover=True` 只在 async 路径启用，并受 `max_fallbacks` 限制。
- Chat 流在尚无生成内容时可 fallback；已生成内容后抛原始异常。Responses 流在已有内容时会构造 continuation input 再 fallback，属于语义重写，不能当无损重放。
- Proxy 会读取顶层 `router_settings` 并传给 Router，但当前 `scripts/hackathon_gateway.py` 只调用 `bin/litellm --config`，现有 `harness/model-gateway.json` 没有 router settings。

当前 launcher 的根边界仍是问题：`prepare_catalog()` 每个 alias 只保留一个 deployment；所以原生 fallback 能力尚未被实例配置使用。最小接入应让冻结配置同时包含链上候选、把 API 形态作为请求能力字段，并在现有 callback 中记录每个尝试的 `alias / deployment_id / provider / plan / wire_model / config_sha256 / run_id / attempt_id / incarnation / attempt_index / status`。不应另造代理。

## 失败处理建议

- 对 429、连接失败、503：按冻结策略做一次短退避，再尝试同链下一个候选；不在同一通道重复打爆额度。403/402/401/400、模型不存在、权限或工具 schema 不兼容：终止当前 deployment，并可继续到已冻结且获许可的下一个候选；只有没有 candidate 才停止整个 alias/实验。
- 套餐耗尽类 429 进入 cooldown，不把 retry 当作额度恢复。每次失败保留具体 HTTP 状态、错误类型和响应诊断，不能只写“rate limited”。
- 流式首 token 前失败可以切换；已发出内容后，Chat 按冻结 1.102.0 行为终止，Responses 的 continuation fallback 只有在单独验收通过后才能启用。
- 记录 LiteLLM 实际选择的 deployment；仅记录客户端 alias、或仅看到 HTTP 200，都不足以证明 route identity。

## 未验边界

- 当前 Proxy 启动参数与 `router_settings`、fallback 链和自定义 callback 的组合尚未实际启动验证。
- 各账户精确 wire ID、工具调用、流式、视觉、Responses 语义和剩余额度尚未逐项真实验收。
- Token Plan 页面 endpoint 与私有 env 历史 endpoint 的差异尚未通过安全的目录/最小请求核对；不读取或输出凭据。
- ARK `deepseek-v4-flash` 与 Token Plan/普通 Qwen `deepseek-v4-flash-0731` 没有版本等价证据，因此不纳入链。

官方依据：[百炼 Token Plan 个人版](https://help.aliyun.com/zh/model-studio/token-plan-personal-overview)、[Token Plan 快速开始](https://help.aliyun.com/zh/model-studio/token-plan-team-quickstart)、[百炼限流](https://help.aliyun.com/zh/model-studio/rate-limit)、[方舟 Coding Plan Codex 配置](https://docs.volcengine.com/docs/ark/coding-plan-personal-ai-codex?lang=en)、[DeepSeek 限流](https://api-docs.deepseek.com/quick_start/rate_limit/)、[DeepSeek 错误码](https://api-docs.deepseek.com/quick_start/error_codes/)、[DeepSeek 工具调用](https://api-docs.deepseek.com/guides/tool_calls/)、[LiteLLM Router fallback/retry 源码对应文档](https://docs.litellm.ai/docs/completion/reliable_completions)。

本调查未读取凭据值、未启动网关、未请求模型、未使用 Helium 自动化、未安装依赖、未部署或恢复实验，未运行 Factory/Braid 测试。
