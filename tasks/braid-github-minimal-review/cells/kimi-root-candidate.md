# 第十次迭代：仅根 Issue 更换 Kimi 的候选

用户已最终选择 kimi-k2.7-code（非K3、非highspeed），授权准备独立实现与最小配置/连通性核实；不启动实验。待独立 GitHub 调查与用户复核后决定启动。

## 模型与渠道核对

2026-09-28 使用 WSL 既有 `.secrets/models.env` 的 KIMI_BASE_URL/KIMI_API_KEY，只读 GET /models 返回 HTTP200。当前配置的供应商是 api.moonshot.cn，目录中包括 `kimi-k3`、`kimi-k2.7-code`、`kimi-k2.7-code-highspeed`、`kimi-k2.6`。未发生成请求，目录可见不证明推理/工具协议完整兼容或额度足够。
Kimi 官方 [模型目录](https://platform.kimi.ai/docs/models) 同样列出 K3 与 K2.7 Code：K3上下文1M、K2.7 Code 256K。用户所称K2.7对应候选精确ID是kimi-k2.7-code，不默认选highspeed。
现有 experiment gateway.json 只配置kimi-k3路由，引用KIMI环境变量；pi-braid的models.json和advisor已包含K3，没有K2.7 Code。既有网关启动时的真实环境尚未重读，不能用当前models.env冒充该进程的实际渠道。

## 最小对照

从当前pi-braid基线冻结后派生独立完整实现，不复用已漂移的pi-braid-coordinator或历史pi-team-k3-root。保留GLM/DeepSeek可指派profiles、原生角色模型/SOP/技能/MCP/工具/预算/资源/工作流。仅新增根专用profile（相同主指令、原生角色与材料，模型为所选Kimi）并令ROOT_PROFILE_ID指向它；root-only仅阻止该配方用于新子Issue/PR，不增加只协调、不写代码等其它工作方法。根具体成员仍可收到讨论。
当前root-only已由Braid成员目录与assign解析过滤；沿用该限定，不由Braid指定子项模型。子Issue与PR仍由root从原GLM/DeepSeek成员配方选择。昂贵模型名额仍按Braid session限制；原生advisor当前本就使用K3，本对照不额外更改它。

|候选|必要配套|推荐理由/限制|
|---|---|---|
|kimi-k3|复用现有provider模型定义、既有KIMI路由，新增root专用profile|推荐作为“更强根模型能否改善设计”的对照；已有协议接线、无需新增模型路由。耗时/成本须报告。|
|kimi-k2.7-code|增加模型定义及新实验网关路由，按256K正确配置上下文|同渠道可见但未接线，不能把K3的1M元数据照搬。需单独核实推理/工具参数。|

最终选择已确认：kimi-k2.7-code。此前推荐K3仅为历史评审选项，不再待决策。保持当前渠道，不调用昂贵生成、不启动实验。工作流程缺口审计在workflow-entry-audit.md，先报告现状，不借模型对照叠加新的通用prompt。

## 已授权实现（2026-09-28）

用户明确选择 `kimi-k2.7-code` 根 variant，授权完成独立实现和最低配置核实，不启动实验、不提交、不替换冻结运行。已从当时最新 `variants/pi-braid/` 复制完整独立目录 `variants/pi-braid-kimi-root/`，复制时排除源码目录的 `__pycache__`。仅在新目录令 `VARIANT=pi-braid-kimi-root`、`ROOT_PROFILE_ID=pi-kimi-k27-code`；新增的根 profile 复制 GLM 根的 instruction、settings、原生角色和模型目录，以 `kimi-k2.7-code` 为主模型，标记 `root-only`，保留 `reasoning=high` 的 Pi 调用档位。此标签由 Braid 成员目录与 assign 解析排除，根本人仍按基线工作，可写代码；既有 GLM/DeepSeek 成员 profile、指令和原生角色文件没有改动。新根成员的原生 advisor 仍指向 K3。

K2.7 模型描述从已有 `variants/raw/raw_models.json` 取与 Pi 相同的兼容字段：`contextWindow=262144`、`supportsReasoningEffort=false`、`thinkingFormat=deepseek`、`maxTokensField=max_tokens`；`maxTokens=131072` 与基线 GLM/K3 描述一致，避免仅因换主模型就改变根成员请求输出上限。原始基线曾观察 K2.7 在 `thinking=enabled` 且无 effort 时完成两轮真实工具调用，并接受请求上限 262144（[历史记录](../../../reports/2026-09-23-model-reasoning-probe.md)）；这不证明当前 variant 已通过同样调用或曾实际生成那么多 tokens。官方 [模型目录](https://platform.kimi.ai/docs/models) 给 K2.7 Code 256K 上下文，区别于 K3 的 1M；[K2.7 使用说明](https://platform.kimi.ai/docs/guide/kimi-k2-7-code-quickstart) 说明 thinking 必须启用、默认 `max_tokens=32768`、工具选择限 auto/none，并要求多轮工具调用保留 `reasoning_content`。官方默认 32768、配方请求上限 131072、模型实际最大支持输出是三个不同概念；现有资料未证明第三者的准确值。新目录不套用 K3 的 `reasoning_effort`。

`scripts/hackathon_gateway.py` 的新模型路由仅把 `kimi-k2.7-code` 指向既有 `KIMI_BASE_URL/KIMI_API_KEY`；未读取或更改活动网关状态。`scripts/package_agent.py` 的 OTLP 打包名单加入新 variant，保证沿用基线的 `lab/otlp.py` 和依赖包。`variants/README.md` 加入独立实现导航。未改 `scripts/package_completed_recovery.py`：这是完成后恢复旧包的受限入口，此候选尚未产生可恢复运行。未改预算/技能/MCP/Pi 内部角色/任务提示。
后续实验入口若设置 `MODEL`，其值必须是 `kimi-k2.7-code`：`run.py` 明确校验平台 `MODEL` 与根 profile 模型一致。此次只准备源码，未调整尚未授权的新实验矩阵、未产生新包。

网关现有 `--preserve-parameters` 开关决定是否保留客户端的 thinking 与输出参数；默认路径会移除这些参数，保留模式则把 Kimi 所需的 `thinking` 移入请求 `extra_body`。新路由本身不改变这项运行选择。实际参数是否由 Pi 按预期发送、LiteLLM 是否原样转发，需要由未来隔离运行的网关原始请求记录证明；目录查询和静态配置不足以保证。
只读检查 WSL 当前 `runs/e20260928-02-deepseek-direct/gateway/service.json` 的 `preserve_parameters` 为 `true`；未打印其它字段、改写状态或重启服务。该服务的 gateway.json 创建于本次源码修改前，仍不能把新增路由当作已进入活动网关。

源码核对只比较复制目录和基线文件、解析 5 个 Python 文件及 10 个 JSON 文件（另解析改动的网关和打包脚本），核对三个 profile 的 id/model/tags 和根模型目录。目录比较只显示新增根 profile、`run.py` 两个标识差异及源目录旧 `__pycache__`；新根模型目录对 GLM 的差异仅一条 K2.7 模型，原生角色文件逐字相同。根据 AGENTS.md 不运行 Factory 设施测试或包 smoke。此处未构建制品、未请求 K2.7 生成或工具往返，也未运行新的 Braid session；真实 Pi→网关→Kimi 的参数保真、推理内容续传、预算表现与应用评分仍须在单独获授权的实验中观察。当前 WSL `GET /models` 200 仅是现有渠道的模型目录证据，不能当作新路由实测成功。


## 当前优先级调整

用户在 Sheet 同分诊断后提出 left-shift 不足，并认为本 K2.7 variant 可能没有必要。
先审查既有 K3 advisor 的真实使用与决策收益；本候选源码保留，暂不推进打包、连通性生成或实验。
不把“尚未利用更强的独立判断”直接推成“需要更换全程根模型”；也不在缺证时宣称 advisor 能替代更强根模型。
