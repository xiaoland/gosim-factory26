# ARC 网关全部模型推理参数实测（2026-09-23）

使用独立 Python 脚本直接请求 `https://api.arc-bench.com/v1/chat/completions`，未调用 Pi、Codex、Runner 或实验控制器。密钥仅从 `~/.config/factory26/llm.env` 的 `FACTORY26_API_KEY` 读取，不写入证据。模型清单来自同一网关的 `/v1/models`。

每个模型测试 21 个组合：默认参数、`thinking.type=enabled/disabled`、九个 `reasoning_effort` 值单独传入，以及这九个值与 `thinking.type=enabled` 同时传入。九个值为 `off`、`none`、`minimal`、`low`、`medium`、`high`、`xhigh`、`max`、`ultra`；其中包含客户端常见别名和可能无效的值，用于观测网关的接受或拒绝行为。每次请求询问 17×23，输出上限为 256 tokens，非流式，四并发，无重试。

336 次请求中，144 次 HTTP 200，均以 `finish_reason=stop` 完整返回 `391`；24 次 HTTP 400，168 次 HTTP 429。八个模型可生成，另外八个模型的所有组合均返回 `insufficient_quota / Free allocated quota exceeded.`。这推翻了“整个密钥都无法生成”的判断；错误与模型或其上游通道相关，具体计费原因尚未确定。

以下“接受”仅表示参数请求成功，不证明每个字符串都对应不同的推理强度；网关可能映射或忽略参数。额度错误不能用于判断参数是否受支持。

| 模型 | 单独传入时被接受的 reasoning_effort | thinking=disabled | HTTP 200 / 400 / 429 |
| --- | --- | --- | --- |
| deepseek-v4-flash | 未验证：额度拦截 | 额度拦截 | 0 / 0 / 21 |
| deepseek-v4-flash-vision-exp | 未验证：额度拦截 | 额度拦截 | 0 / 0 / 21 |
| deepseek-v4-pro | 未验证：额度拦截 | 额度拦截 | 0 / 0 / 21 |
| glm-5.2 | 未验证：额度拦截 | 额度拦截 | 0 / 0 / 21 |
| glm-5.3 | 未验证：额度拦截 | 额度拦截 | 0 / 0 / 21 |
| glm-5.3-flash | 未验证：额度拦截 | 额度拦截 | 0 / 0 / 21 |
| kimi-k2.6 | off, none, minimal, low, medium, high, xhigh, max, ultra | 接受，未返回 reasoning_content | 21 / 0 / 0 |
| kimi-k2.7-code | off, minimal, low, medium, high, xhigh, max, ultra | 拒绝 | 19 / 2 / 0 |
| kimi-k2.7-code-highspeed | off, minimal, low, medium, high, xhigh, max, ultra | 拒绝 | 19 / 2 / 0 |
| kimi-k3 | off, none, minimal, low, medium, high, xhigh, max, ultra | 接受，未返回 reasoning_content | 21 / 0 / 0 |
| minimax-m3 | 未验证：额度拦截 | 额度拦截 | 0 / 0 / 21 |
| qwen3.6-flash | none, minimal, low, medium, high, xhigh | 接受，未返回 reasoning_content | 15 / 6 / 0 |
| qwen3.6-plus | none, minimal, low, medium, high, xhigh | 接受，未返回 reasoning_content | 15 / 6 / 0 |
| qwen3.7-max | 未验证：额度拦截 | 额度拦截 | 0 / 0 / 21 |
| qwen3.7-plus | none, minimal, low, medium, high, xhigh, max | 接受，未返回 reasoning_content | 17 / 4 / 0 |
| qwen3.8-max | none, minimal, low, medium, high, xhigh, max | 接受，未返回 reasoning_content | 17 / 4 / 0 |

Kimi K2.7 Code 与 Highspeed 的 `thinking=disabled` 和单独 `reasoning_effort=none` 均明确报错：只允许开启推理。其余被接受的字符串均有 reasoning_content；尤其 `off` 字符串并未关闭推理。Kimi K2.6 和 K3 单独传 `none` 或显式 disabled 时无 reasoning_content，其余本次成功组合都有。不能据此把 Kimi 接受的九个字符串当成九个独立档位。

Qwen 3.6 Flash/Plus 接受 none、minimal、low、medium、high、xhigh；拒绝 off、max、ultra。单独 none/minimal 本次不返回 reasoning_content。Qwen 3.7 Plus 和 3.8 Max 还接受 max，拒绝 off、ultra；3.8 Max 的 minimal 本次仍返回 reasoning_content。3.7 Plus 的某个拒绝消息枚举未列出 max，但实际 max 请求成功，应保留该网关行为差异。

对于全部八个可用模型，显式 enabled 搭配 none 的请求均成功且返回 reasoning_content。开关与强度存在优先级，不能以 none 字符串单独判断最终是否开启推理。

当前基线要求的 DeepSeek Vision Exp 与 GLM 5.3 Flash 仍全部被额度检查拦截，因此本次未启动这两个模型的 bench，也未测得其生成并发峰值。四并发探测成功不构成并发上限证据。

独立脚本和完整证据位于仓库同级 `factory26-official-local/runs/raw-baseline-20260923/all-model-reasoning-probe/`：`probe.py`、`manifest.json`、`models.json`、`results.jsonl`、`summary.json`，以及按模型与组合保存的 `request.json`、`response.body`、响应头和 `result.json`。traceId 来自原始响应 JSON，不由本地设施生成。

## 替代基线的接入与并发核验

随后针对 `kimi-k2.7-code`（enabled，无 effort）和 `qwen3.6-plus`（disabled，无 effort）分别完成真实两轮工具调用：模型先请求工具，再正确读取工具返回值。请求上限 `262144` 与 `65536` 分别被网关接受。这只验证上限参数被接受，不表示实际生成了该数量的 tokens。

两模型各测试 4、8 并发，另测试混合 8 并发；32 个并发探针全部 HTTP 200，无 Retry-After。批次耗时分别为 Kimi 1.77/2.00 秒、Qwen 4.38/4.99 秒、混合 4.47 秒。8 是已验证的请求并发下界，尚未触及上限；短请求结果不能证明长上下文生成的吞吐或持续限流规则。直连证据位于同级 `factory26-official-local/runs/raw-baseline-20260923/replacement-api-qualification/`。原定 32 场基线将采用这两个可用模型替换被阻断的 DeepSeek/GLM，并保留原生核心接入核验。


## 通道恢复复查

2026-09-23 21:56 CST 起，在 WSL 使用同一用户凭据直接请求六个先前被阻断的 DeepSeek/GLM 模型，均返回 HTTP 200、答案391、finish_reason=stop。此次使用默认推理参数，确认基础调用恢复，不追认先前被额度门禁拦截的档位为已验证。原始请求和响应保存在 WSL 实验根目录 `api-recheck/20260923T135622Z/`。用户随后要求停止 Kimi/Qwen 并恢复原定 DeepSeek Vision Exp、GLM 5.3 Flash 的 32 场基线；所选基线参数和工具调用另行验证。

恢复后的基线资格已确认：DeepSeek Vision Exp 关闭推理并携带 `reasoning_effort=none` 的请求返回200；DeepSeek 与 GLM 5.3 Flash 均完成两轮真实工具调用，正确返回工具内容 `ARC-LOOKUP-OK`。GLM 使用 enabled、clear_thinking=false、low、max_tokens=131072，第一轮 reasoning_content 保留回传；DeepSeek disabled 模式没有 reasoning_content。全部无重试、配额或传输错误。证据位于同一 WSL 根目录 `replacement-api-qualification/`。这证明所选基线参数和工具往返可用，不表示其他推理档位已重新实测。
