# ARC DeepSeek Flash 版本调查

当前采用（2026-10-08）：用户明确“ARC的旧模型ID就是0731版本，这是早就确认的事情”。公共自费配方据此采用稳定 alias `deepseek-v4-flash-0731` → ARC wire ID `deepseek-v4-flash`，以 ARC 为第一道；本次没有重新发生成请求。以下调查结论和证据保留其 2026-10-01 历史身份。

历史状态：本次调查完成。当前证据明显支持 ARC 的 `deepseek-v4-flash` 是 2026-07-31 的 V4 Flash；这属于较强推断，尚无 ARC 实际路由及后端快照的直接确认。仅作公开资料核实与少量真实 API 取证，未修改 Harness、模型配置，未启动或恢复 benchmark。

追加状态：别名可用性调查完成，当前团队凭据不能调用 `deepseek-flash`。用户随后问“那也许Arc可以用deepseek-flash模型吗（应该就是 ds-v4.1-flash）？”，据此执行最小别名可用性取证。先向 ARC 请求一次 `deepseek-flash` 短文本（关闭思考、输出上限128、不重试）；原计划成功时用此前同一张图片追加一次请求。该授权只覆盖此次取证，不修改 Harness 或启动 benchmark。

直接别名请求返回 HTTP 400 / `provider_not_selected`，提示选择 `x-onr-provider` 或配置服务端 `models.yaml`。公开 ONR 文档确认该头是显式选择 provider 的接口。依据此前响应里的 TaoToken 标记，仅追加一次 `x-onr-provider: taotoken` 的短文本请求，检验这一有证据来源的路由假设；不枚举其它 provider。不把该名称已获 ARC 配置当作事实。

## `deepseek-flash` 别名实测结果

2026-10-01 17:58–18:00（Asia/Shanghai），继续使用同一 ARC key 与 `https://api.arc-bench.com/v1/chat/completions`，两次短文本均关闭思考、temperature=0、max_tokens=128。原始证据：[flash-alias-20261001T095855Z](../../runs/arc-deepseek-version/flash-alias-20261001T095855Z/)。

| 请求 | 实际响应 | 含义 |
| --- | --- | --- |
| `model=deepseek-flash`，默认路由 | HTTP 400，`provider_not_selected`；`no provider selected: set x-onr-provider or configure models.yaml`。Request ID `2026100117585605579630386038`。 | 默认路由未能选择 provider；不能解释成上游模型不存在。 |
| 相同请求，增加 `x-onr-provider: taotoken` | HTTP 403，`team_model_not_allowed`；`Model is not in the team allowed list.`。traceId `ca5bd8280ab34bd8bf30ca25d0658a01`，Request ID `2026100118003661492023731966`。 | 请求得到明确的团队模型权限拒绝，当前凭据不能调用该 ID。 |

公开接口依据：[ONR 主仓库的 Provider Selection 与 Model Routing](https://github.com/r9s-ai/open-next-router#provider-selection)。该文档只用于理解错误提示，不证明 ARC 的完整部署配置。

两次请求都未取得模型答案或 usage。未重试、未发图片请求，不通过其它名称或 provider 绕过团队权限。当前结论针对这份团队凭据及当前服务状态，不推断所有 ARC 团队均不可用。需要 ARC 为本团队开放 `deepseek-flash`；若要沿用不传额外头的普通调用，还需服务端提供默认模型路由。仍未修改 Harness、模型配置或启动 benchmark。

用户原话：“你有没有办法探测看看Arc这边提供的DeepSeek V4 Flash模型是DeepSeek V4.1 Flash还是今年7月30左右的那个V4 Flash。”本次按该请求执行最小版本调查；不沿用其它任务的停止状态去阻止本次定向取证，也不恢复那些任务。

## 问题与判据

需要判断当前 `https://api.arc-bench.com/v1` 的 `deepseek-v4-flash` 实际模型。模型清单名称、创建时间和模型自报身份不能单独证明后端版本。优先寻找实际响应的上游版本名、明确的快照或路由元数据；网关若改写或屏蔽，结合公开映射与可区分能力形成有边界的推断。

2026-10-01 已查 DeepSeek 官方更新日志：七月底版本发布于 2026-07-31；2026-09-10 发布 V4.1 Flash，官方接口把 `deepseek-v4-flash` 与 `deepseek-v4-flash-vision-exp` 临时转接到 V4.1 Flash。该公告只证明 DeepSeek 官方端点，不能直接推广到 ARC。

## 调查安排

先只读获取 ARC `/models` 与必要的公开或计量模型元数据。随后最多三次短文本请求到 ARC Flash，单次输出上限 256 tokens，关闭思考，不重试；仅在元数据未能定版时增加一次合成图片请求（输出上限 128 tokens）检验原生视觉行为。必要时对用户已有 DeepSeek 官方端点做同输入对照，不调用其它模型。所有请求串行，保留 HTTP 状态、响应体、脱敏响应头及版本字段，不保存或打印凭据。不做广泛能力 benchmark，也不通过质量、速度或自报身份直接定版。

完成条件：给出观测、版本结论及置信边界；若无法定版，明确缺少的 ARC 路由或快照信息。原始证据保存到 `runs/arc-deepseek-version/`，不向生成 Agent 注入信息。

公开来源：https://api-docs.deepseek.com/updates/ 。

## 当前结论与证据

2026-10-01 16:04–16:07（Asia/Shanghai）完成一次 ARC 模型清单读取、一次 ARC 短文本请求、一次 ARC 图片请求和一次官方图片对照。三个生成请求均 HTTP 200，无服务端重试；ARC 合计 199 tokens，官方对照 246 tokens。首次 Python 默认 CA 存储缺少信任链，握手失败、未取得 HTTP 响应；改用已有 certifi 信任库后继续，证书校验始终开启。

原始证据目录：[20261001T080329Z](../../runs/arc-deepseek-version/20261001T080329Z/)。请求载荷、响应体、脱敏响应头、HTTP/耗时收据、挑战图片与预期答案都保留。TaoToken 用户标识已从证据头脱敏，API key 未写入证据。

| 观察 | 事实 | 判断边界 |
| --- | --- | --- |
| ARC `/v1/models` | Flash、Vision Exp、Pro 均为 `owned_by=custom`，Flash ID 为 `deepseek-v4-flash`；本次清单未列 `deepseek-flash`。 | 名称与目录创建时间不能证明权重版本。 |
| ARC 文本请求 | 返回 `model=deepseek-v4-flash`，无 `system_fingerprint`；响应头包含 `X-Taotoken-Request-Id` 等标记。 | 标记支持链路中有 TaoToken，尚未直接取得其后端路由。 |
| TaoToken 当前公开目录 | `deepseek-v4-flash` 明确描述为“Deepseek-V4-Flash 0731”、284B/激活13B，publishTime 为 2026-07-31，supportedModalities 仅 `text`。 | 当前供应商声明比旧模型别名更具体，仍不等于某次 ARC 调用的部署身份。 |
| 同目录的新 Flash | `deepseek-flash` 明确描述 V4.1、552B 与 Causal-Encoder-Decoder，publishTime 为 2026-09-14，supportedModalities 为 `text,image_url`。 | TaoToken 在目录中把两者作为不同 ID 提供，不能套用 DeepSeek 官方端点的别名升级关系。 |
| 同图片对照 | ARC 把随机字符串 `2EBGVQMZ` 答成 `A3B7C2D9`，三个图形也全部错；官方 `deepseek-flash` 正确读取字符串及红色长方形、蓝色圆形、绿色三角形。两份请求的图片载荷相同，其它参数除模型名外相同，关闭思考，temperature=0。 | 图片请求被接受不等于图片有效进入模型；结果不能排除网关丢失图片，也不能单独定版。 |

TaoToken 来源：[当前模型广场](https://taotoken.net/models?modelId=deepseek-v4-flash)。Web 工具不能读取该页面，Python 的经过证书校验的 GET 成功获得当前 SSR HTML；完整内容保存在 `taotoken-model.html`。从 `window.__pinia_state__` 按精确 ID 抽出的完整模型对象分别保存在 `deepseek-v4-flash.public-model.json` 与 `deepseek-flash.public-model.json`，不把搜索摘要当作当前目录证据。

主 Agent 据当前目录、ARC 响应标记与真实图片对照形成上述判断。独立 advisor `/root/flash_version_judgment` 读取请求、图片及目录原件后，确认这些证据支持较强推断，但不支持宣称已严格确认；不再追加无法区分网关丢图与旧模型的能力请求。

若需要严格定版，最小缺失事实是 ARC/TaoToken 对本次请求 `X-Taotoken-Request-Id=dfe4753b917acc32924a0e78d1b0f4e8` 实际使用的上游模型及版本快照。当前不将 ARC 这条旧 ID 认定为已验证的 V4.1，不据此修改配置或继续模型实验；本次结果交给用户判断后续范围。
