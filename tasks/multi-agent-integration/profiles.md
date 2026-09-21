# Agent Profile 的配置边界与当前实现

调查日期：2026-09-21。本页的实现表保存实施前观察，不能用于判断接入完成；最新实现与真实证据见 [runtime](cells/runtime-ready.md) 和 [capabilities](cells/capabilities-ready.md)。本页保留概念边界与调查依据，不替代技术与验收方案。

## Profile、preset 和 variant

Braid 的 [术语表](../../sources/braid/docs/10-prd/glossary.md) 将 Agent Profile 定义为不可变 Agent 配置，包含 provider、model、reasoning、user instructions、tools、skills、MCP 等。因此不能把 profile 收窄成模型名或一段角色提示，也不能因为当前 Rust struct 较薄就据此删掉产品能力。

Profile 描述一种可运行 Agent 的配置：使用哪种核心、模型与参数，获得什么指令和工具能力，可以使用怎样的原生 sub-agent。Factory 负责把这些声明装配为实际运行环境；密钥值、临时 HOME、端口、工作树路径与宿主位置由运行时绑定，不写进可复用 preset。声明使用某个 MCP/CLI 属于能力选择，安装并启动它属于装配，二者需要形成可验证的对应关系。

Preset 是 Factory 拥有的命名、可版本化组合；Braid 不认识 preset 或 variant，只接收普通 profiles 和工作项指派。可以只包含一种 profile，也可以包含多种 profile 的组合、默认使用方式和 provider 内部 sub-agent 配置；本任务当前认可四种首轮方向，六份旧草案仅作后续细化素材，见 presets.md。每个 preset 对应一个 variant，variant 保留明确身份并引用共同的 Braid/SVC 基础。需求、评测版本、执行机器与评测 worker 数是实验条件；不通过复制所有基础配置来制造多个 variant。

用户最新确认：本项目 preset 配置 Braid 可直接 assign 的 profile 集合，work-item 以明确 profile ID 选择；GitHub label 已无必要。Pi 的 explorer/executor/reviewer 是单个 profile 内部的物理 sub-agent 配置，不属于上述同一层的 profile 集合。具体新配方以 [presets.md](presets.md) 为准；目标优先提高通过率，成本留待后续消融。

Issue 的需求/方案/验收设计职责、PR 的实施预演/执行/最终验收职责属于共同 Braid 协议。Profile 可以配置专长与工作方式，但不重复维护这些职责，也不规定必须拆 Issue、必须派满团队或必须遵守某条任务阶段链。Braid-level multi-agent 与 Codex/Pi-native sub-agent 始终分别表示。

## 可配置内容与实效

| 范围 | 应理解的配置内容 | 当前 Factory/Braid 实际情况 |
| --- | --- | --- |
| 核心 | Codex app-server 或 Pi、实现版本与适配 | 每次运行仅一个 backend；Braid `session_factory` 要求 Codex/Pi 恰选一个。 |
| 模型 | 模型 ID、网关/provider、推理参数，以及原生调用所需的模型能力描述 | Factory 填同一 model/thinking；Codex 取 Profile.model/reasoning，Pi 取独立 PiConfig.model/thinking。修改 Profile 不保证 Pi 调用发生变化。 |
| 指令 | 行为、专长、工作方式及所需方法导航 | Profile.user_instructions 会进入有效指令；Factory 当前写空字符串，Braid 追加角色协议，SVC 由 user-scope AGENTS.md 两行导航提供。 |
| 工具与服务 | 核心工具、额外 CLI、MCP server、相关访问配置 | 保留原生工具与 Braid/SVC CLI；没有额外技能或 MCP 装配入口，不能靠提示宣称工具已可用。 |
| Skills/扩展 | 可加载的技能、Pi extension、辅助提示材料及精确来源 | Pi wrapper 明确禁用 extensions、skills、prompt templates、themes；当前不可从 profile 启用。 |
| 原生 sub-agent | 可用子代理定义、各自模型/指令/工具及生命周期 | Factory 隔离运行未完成此类装配与验收；宿主有扩展或特性不等于实验 Agent 可用。 |
| 上下文 | Braid 投影大小与压力；原生核心的上下文/压缩设置 | 现有 `context_soft_ratio=0.8`、`context_hard_bytes=1000000` 针对 Braid canonical projection 的字节数；不是模型 token window，也不控制整个原生对话的压缩。 |
| 适用范围与身份 | profile ID、显示名、适用 Issue/PR 的 tags、有效配置版本 | 本地 Request 只接收一个 profile，再硬编码克隆成 local-issue/local-pr。没有工作项选择任意 profile 的入口。 |

关键消费者为 [Profile schema](../../sources/braid/src/config.rs)、[本地装配](../../sources/braid/src/local.rs)、[Codex adapter](../../sources/braid/src/provider/codex.rs)、[Pi adapter](../../sources/braid/src/provider/pi.rs)、[Factory 请求生成](../../scripts/factory.py) 和 [核心配置](../../scripts/core.py)。`adapter_version`、`provider` 等字段是否承担声明中的检查或查表职责，要以这些消费者为准；存在字段不等于契约已落实。

Factory 当前所有显式自定义配置都标记为 `custom`；多个 preset variant 需要保留各自可追溯身份。模型与推理参数也必须只有一份可编辑权威，再生成 backend 各自的实际参数，避免同名不同实效或异名同实效。

已安装 Pi 的 `docs/models.md` 和 `docs/settings.md` 还提供模型能力描述（输入模态、contextWindow、maxTokens）、逐模型 thinking 映射、samplingParams、OpenAI-compatible 参数兼容开关、原生 compaction、工具选择及扩展/技能加载。这些是原生可配置能力，不代表 Factory 已开放相同入口。尤其 `reasoning_effort`、developer role 与 thinking 的 wire format 要匹配实际网关；不能仅凭模型名字套用某家 provider 的默认兼容设置。模型能力描述中的缺省值也不能当作真实服务规格。

现有本地 Pi 运行只在 models.json 覆盖 deepseek provider 的连接信息；平台打包路径另外写入模型 descriptor。两条路径的能力元数据尚未统一。先前原生会话记录证实实际使用了 deepseek-v4-flash-vision-exp，但这不能证明其余候选模型的能力描述和参数映射均正确。

## 账户模型目录

通过用户指定的 [meter 页面](https://meter.arc-bench.com/user) 的“支持模型”和“API 文档”读取。下面是当时页面显示的价格，单位为 CNY / 1M token，分别为输入、输出与缓存命中；不是实际账单估算。目录确认可调用，不证明具体 reasoning、视觉、上下文或并发能力，也不证明模型质量排名。

| 用户指定模型 | 输入 | 输出 | 缓存命中 |
| --- | ---: | ---: | ---: |
| deepseek-v4-flash | 3 | 9 | 0.1 |
| deepseek-v4-pro | 9 | 27 | 0.3 |
| glm-5.3 | 8 | 28 | 2 |
| glm-5.3-flash | 0.8 | 2.8 | 0.23 |
| kimi-k2.7-code | 6.5 | 27 | 1.3 |
| kimi-k3 | 20 | 100 | 2 |
| qwen3.7-plus | 2 | 8 | 0.4 |
| qwen3.8-max | 12 | 36 | 1.5 |

目录另外列出 deepseek-v4-flash-vision-exp（1/4/0.02）、glm-5.2（8/28/2）、kimi-k2.6（6.5/27/1.1）、kimi-k2.7-code-highspeed（13/54/2.6）、minimax-m3（2.1/8.4/0.42）、qwen3.6-flash（1.2/7.2，缓存未标）、qwen3.6-plus（2/12，缓存未标）及 qwen3.7-max（12/36/2.4）。当前活动配置仍使用 deepseek-v4-flash-vision-exp。

网页 API 文档说明 OpenAI Chat Completions 和 SSE streaming；没有给出 Responses 原生支持、模型逐项参数映射、上下文窗口、输入模态或明确并发额度。不能把示例里的占位域名当 API base URL，也不能把全部模型统一套用 high 就称为等价推理条件。当前实际网关由 Factory 配置中的 `https://api.arc-bench.com/v1` 提供。

## 接下来设计需要回答的问题

用户已提出 Kimi K3 协调、GLM 5.3 Flash / Kimi K2.7 Code 专项实现的方向。先把这些 Braid profile 的完整能力和工作分工配置正确；不再把探索成本作为首轮目标。价格和型号名字不能代替效果证据。

为草案核对工具调用、图像读取、reasoning 传参、隔离加载和有效配置记录，避免把装配失败记成模型能力差。完整实验延续既有独立生成、冻结、官方评测和终态报告约定。本轮尚未批准或启动任一配方实验。
