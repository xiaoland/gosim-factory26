# 本轮只读现场与账户观察

2026-10-02，北京时间。主 Agent 使用 Helium 现有标签页、白名单 Docker inspect 和 df；没有变更账户设置、显示/复制 API key、发起模型生成、恢复或评价。

本记录保存清理前观察，不代表当前现场或允许的新运行位置。用户随后授权删除更早及不完整运行，并规定所有本项目产物必须位于 WorkSSD；原 paused I14 与外置 I14根已退役。当前容量及清理终态见 [清理回执](storage-cleanup.md)，后续路径约束见 [当前方案](../design.md)。

## 现场与空间

北京时间约 23:13，development-2 的两项 fresh baseline 容器仍为 paused，Paused=true、OOMKilled=false，StartedAt 与暂停回执来源一致：GLM 为 `9faab12abf7b2abc8e8880474475803911741c0927815fe6be7db746f727128e`，Flash 为 `d9962d24bf401d262d63e43984f5eb993e573b80e712be82166b15e97162ae2c`。此读回证明容器现场仍在，不证明控制器可恢复派发或供应商当前受理。

df 读回：WorkSSD 剩约 1.2 GiB，Mac Data 剩约 9.7 GiB；development-2 的根文件系统剩约 56 GiB。后续准备须核对实际产物/缓存、运行、归档、应用回传与评分打包的目的地和峰值，消费已有资产并避免重复完整复制；不能仅按远端生成有容量判断全流程有容量。没有删除现场、产物或历史证据，也没有降低现有 reserve。

## 账户页面

千问 Token Plan 的原标签页为 [个人订阅](https://bailian.console.aliyun.com/cn-beijing/subscription/token-plan/personal)。刷新后额度时间为 2026-10-02 23:04:20，Essential 生效中，月已用 57.86%，到期 2026-11-03 00:00；当前列表包含 GLM-5.3、DeepSeek0731、V4 Pro/0813，不列 Flash/K3。页面 Base URL 为 `https://token-plan.cn-beijing.maas.aliyuncs.com/compatible-mode/v1`；私有配置沿此前用户指定的 qianwenaiapi 地址，地址差异不通过假定别名解决。

方舟 [Coding Plan](https://console.volcengine.com/ark/region:cn-beijing/subscription/coding-plan)显示 Pro，近五小时、周、月用量均 0%。实际“使用配置”页的 OpenAI Base URL 为 `https://ark.cn-beijing.volces.com/api/coding/v3`，精确 model name 包含 `glm-5.3-flash`、`glm-5.3`、`kimi-k3`、`kimi-k2.7-code`、`deepseek-v4-flash`、`deepseek-v4-pro`。页面提示 Flash 当前火爆，DS V4 Flash 为高负载；额度未用不等于没有 429。没有触碰 key 的显示、复制、创建或删除。

千问 [普通 API 免费额度](https://bailian.console.aliyun.com/cn-beijing/costing-balance/free-quota)显示 K3 剩 798.3K/1M、DS0731 剩 1M/1M，两者“用完即停”关闭。搜索 GLM 并取消“有额度”筛选后，裸 `glm-5.3` 免费额度和期限为 `-`；`ZHIPU/GLM-5.3-Flash` 为剩 0/共 0，不支持开启“用完即停”。这不能解释为付费账户余额耗尽，也不支持此前 GLM/Flash 各有 1M 免费的判断。

[普通 API 费用概览](https://bailian.console.aliyun.com/cn-beijing/costing-balance/overview)显示本月账单 74.67 元，订阅 79 元，总消费 153.67 元；账户可用余额未取得，不据历史账单推断今晚可持续调用。[模型限额](https://bailian.console.aliyun.com/cn-beijing/costing-balance/quota-managements)尚未取得可用 TPM 数据。公开价格与目录、免费额度与付费余额、页面可见与实际工具/流式响应各自有不同证明范围。

## 供应商目录只读 GET

主线仅使用现有配置查询 `/models`，不发推理 prompt。首次 Python urllib 四个通道均在本机 TLS 信任校验失败，错误包括 `CERTIFICATE_VERIFY_FAILED` / `unable to get local issuer certificate`，DeepSeek 为 `self-signed certificate in certificate chain`；未关闭 TLS 校验。随后改用系统 `/usr/bin/curl` 正常的证书验证重读，四项均 HTTP 200。上述本机错误不能归为模型供应商受理失败。

| 通道 | 当前 GET 观察 | 证明边界 |
| --- | --- | --- |
| 普通 Qwen `/compatible-mode/v1/models` | 261 个 ID，包含 `glm-5.3`、`ZHIPU/GLM-5.3-Flash`、`kimi-k3`、`deepseek-v4-flash-0731`。 | 现有用户指定 qianwenaiapi 地址可鉴权读目录；不证明推理余额、工具或流式。 |
| Token Plan `/compatible-mode/v1/models` | 16 个 ID；相关项为 `glm-5.3`、`deepseek-v4-flash-0731`、`deepseek-v4-pro`、V4.1。 | 与账户可见主要候选吻合；仍不自动把两个域名视为无差异。V4.1 沿此前排除。 |
| ARK `/api/coding/v3/models` | 135 个通用平台 ID；含 `deepseek-v4-flash-ga-260731`、`deepseek-v4-pro-ga-260813`，未列后台 Coding 配置页的 GLM/Flash/K3 alias。 | 此目录不是套餐 alias 受理证据，不能据缺项判定后台 alias 不支持。日期 ID 是否可用套餐调用、是否与稳定 alias 同版本仍待真实请求/官方映射核对。 |
| DeepSeek 原厂 `/v1/models` | 两个 ID：`deepseek-flash`、`deepseek-v4-pro`。 | Flash 沿既有版本排除；Pro 可成为后续显式选型候选，不补成0731同版本备援。 |

没有调用 Chat/Responses、工具或视觉推理，没有消耗生成 tokens，也没有新启动网关。这些目录查询只关闭当前地址/key的鉴权可读性未知；真实生成入口验收仍属于开工后的工作。
