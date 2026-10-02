# DeepSeek 文本模型的成本对照候选

阶段：后续实验规划，未改变当前官网运行或冻结包。2026-09-27 只读核对 `pi-braid` 与两份历史终态工作区；价格以同日登录 ARC Meter `/api/user/models` 返回的公开价目为准。厂商直连价、比赛网关价和官网 run 的 `token_cost_usd` 不能混用。

## 当前用途和真实消耗

两份当前恢复 ZIP 的 `pi-deepseek-fast` 主模型均为 `deepseek-v4-flash`、reasoning=`high`，不是视觉 SKU。原生 `explorer`、`executor` 也使用此文本模型；`browser-operator`、`vision` 使用独立的 `deepseek-v4-flash-vision-exp`，`advisor` 使用 Kimi K3，根 Issue 为 GLM-5.3-Flash。旧 Sheet 数据库有 2 个 DeepSeek Issue assignment；旧 GitHub 有 6 个 DeepSeek Issue assignment 和 1 个 PR assignment。根 Agent 自行指派，配置不把 DeepSeek 限定于某种工作项。

历史终态 Pi JSONL 的 assistant usage 按实际 `model` 汇总如下。`input` 与 `cacheRead` 分开；`totalTokens` 是两者加 `output`，不能按它套同一单价。Sheet 的 28 个 DeepSeek 会话文件、582 次带 usage 的响应全部来自 DeepSeek 成员；GitHub 的 80 个会话文件、2,067 次响应中，76 个来自 DeepSeek 成员，4 个在 GLM 成员的原生子代理目录。旧官方 run 的 token_count 与 Meter 费用按共享 access key 的时间窗计量，期间运行可能重叠，不可当作这两个模型的逐请求账单。

| 旧运行 | 非缓存 input | output | cacheRead | 最大单次 input+cacheRead |
| --- | ---: | ---: | ---: | ---: |
| Sheet | 1,052,415 | 450,128 | 49,290,752 | 220,370 |
| GitHub | 3,905,464 | 1,349,087 | 189,279,488 | 305,603 |

ARC Meter 当前目录中的确切可用 ID 是 `deepseek-v4-flash`、`qwen3.6-flash` 和 `minimax-m3`。每百万 token 的网关标价（人民币）分别为 DeepSeek `3/9/0.1`、Qwen `1.2/7.2/缓存栏空白`、MiniMax `2.1/8.4/0.42`，顺序为非缓存 input/output/cache hit。空白表示**未知**，不能按免费缓存计算。网关 `/v1/models` 只给出 ID 与 owned_by，不披露上下文、工具协议或实际路由版本。

按旧 DeepSeek usage 原样乘以网关价，仅作模型单价反事实，不代表替换后会产生相同 token，也不是实际账单：

| 模型价目 | Sheet 估算 | GitHub 估算 | 解释 |
| --- | ---: | ---: | --- |
| DeepSeek V4 Flash | ¥12.137 | ¥42.786 | 历史 usage 的参考价 |
| MiniMax M3 | ¥26.693 | ¥99.031 | 缓存读取价是 DeepSeek 的 4.2 倍；保持非缓存量时，须减少约 70% 缓存读取才打平 |
| Qwen 3.6 Flash | ¥4.504 + 49.291 × 缓存价 | ¥14.400 + 189.279 × 缓存价 | 缓存价单位为元/百万；打平阈值约 ¥0.155 / ¥0.150 每百万 |

Qwen 如果缓存按完整 input 价 ¥1.2/百万计费，反事实为 Sheet ¥63.653、GitHub ¥241.535；如果按 ¥0.1/百万则是 ¥9.433、¥33.328。只有拿到 ARC Meter 的实际 Qwen 缓存账单或明确计费说明，才能判断哪种情形接近现实。历史 GitHub 有 70/2,067 次 DeepSeek 响应的单次 input+cacheRead 超过 256K；Qwen 厂商直连价对超过 256K 的请求分档，ARC Meter 目录暂未显示此分档，也不能直接套到网关。

厂商资料只用于能力上限与直连价参考：阿里云给 `qwen3.6-flash` 标 1M context、function calling、视觉和缓存能力；MiniMax 给 M3 标 1M context、多步工具调用和多模态，直连标价按 512K 分档。DeepSeek 官方已把旧 `deepseek-v4-flash` 名称映射到 V4.1 Flash，但 ARC 网关是否采用同一映射尚无证据。以上都不能证明 Pi 经 ARC 网关的长任务、工具调用和缓存计量可靠。

## 后续最小 A/B

先做网关协议资格检查：对 Qwen/M3 分别核实实际可用额度、Pi 两轮工具往返、reasoning 参数、长上下文边界、原生 usage 的 cacheRead 与 Meter 逐请求计费。旧 Qwen 短请求已通过参数测试，但 M3 当时受 `insufficient_quota` 阻断，均不能代替这次资格检查。

资格通过后，用同一 Hackathon 题目和同一干净起点做三臂对照：现有 DeepSeek 文本模型、Qwen、M3。只替换 `pi-deepseek-fast` 主模型和两个文本原生子代理的模型及必要协议适配；根 GLM、视觉、advisor、技能、Braid、需求、启动环境、并发上限与验收方式保持一致。三臂使用相同可指派成员说明，记录实际指派差异。为取得每臂可归属的官网费用，先串行运行，避免共享密钥并行使官方 token/费用时间窗互相污染；如改用独立密钥或可验证的逐请求计费关联，再考虑并行。

比较顺序是完整交付/评分、生成成功率和耗时，其次才是实际账单与分项 token。若候选需要更多重试、丢失工具调用或使最终验收倒退，较低名义单价没有意义。第一题可选历史 DeepSeek 用量较大的 GitHub；只有候选显示可靠收益，再用 Sheet 复核跨题可迁移性。此规划不授权现在启动实验。

能力与厂商价来源：[ARC Meter 账号模型目录](https://meter.arc-bench.com/user)、[阿里云 Qwen3.6 Flash 型号页](https://docs.modelstudio.console.alibabacloud.com/en/model-studio/qwen3-6-flash)、[阿里云分档价格](https://www.alibabacloud.com/help/en/model-studio/model-pricing)、[MiniMax M3 型号页](https://www.minimax.io/models/text/m3)、[MiniMax API 价格](https://platform.minimax.io/subscribe/token-plan?tab=api-enterprise)、[DeepSeek 型号与价格](https://api-docs.deepseek.com/quick_start/pricing/)；上述外部报价不代替 ARC Meter 当前实际计费。
