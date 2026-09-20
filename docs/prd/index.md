# Factory26 产品说明

Factory26 用于开发和比较参加 GOSIM Agentic Factory / ARC-bench 的 Agent Harness。使用者是开发 Harness 的工程师；运行时 Agent 接收需求包并生成应用。开发仓库的 Coding Agent 与被评测的运行时 Agent 是不同角色。

项目要让每次实验能够回答：输入了什么需求、使用了什么模型与 Harness、产生了什么应用、评测如何结束，以及证据在哪里。具体运行方式由[运行文档](../deployment/index.md)维护，单次结果由[四组实验报告](../../reports/2026-09-20-harness-matrix.md)维护。

## 当前能力与范围

目前比较四种组合：Codex app-server + SVC、Pi + SVC，以及各自增加 braid。两种核心使用独立临时 HOME 和原生配置目录；原始 Pi、Codex 配置也可单独运行。backend、workflow 与 svc 是三个独立选择，启用 braid 不要求启用 SVC。比赛模型、需求和外部评测版本由配置声明，实际使用的组件源码随每次运行归档。

Codex 通过 app-server v2 接口驱动，使用固定版本 LiteLLM 将 Responses 请求转换为比赛网关的 Chat Completions 请求。适配器是实验条件的一部分。Pi 直接使用比赛网关。运行时保留核心默认系统提示和原生工具；尚未添加额外技能或 MCP server。

SVC 是可选的 Corpus 工作方法，通过核心的 user-scope AGENTS.md 注入。文档归属、任务包组织、verification 和工作姿势由 Agent 按实际需要采用；运行器不把 SVC 任务包作为调度协议，也不复制开发者个人指南。已有设计或实施事实的权威正文应被引用，避免任务包产生第二份权威副本。

braid 的本地模式由 `sources/braid` 维护。它拥有 `.braid/design.md`、`.braid/implementation.md` 两个工作项的当前记忆，以及独立的 handoff、refresh、complete 控制动作；Factory26 只提供需求、workspace 和核心配置。设计与实现 Agent 可以修改当前正文、修正彼此发现的问题，并通过交接继续协作。每次明确交接或刷新都使用已有 SessionFactory / AgentSession 边界创建新物理会话，重新加载当前正文，不继承旧聊天。工作区保留，逻辑工作项不随物理会话更换而改变。

本地模式串行交接，不实现并发委派、GitHub 事件监听或中途人类交互。它复用 braid 的会话边界，但没有运行 GitHub GroupDriver / store 生命周期；不能把本地模式的验证解释成完整 GitHub 产品验收。braid 对 SVC 没有运行时依赖；SVC 也不调用 braid。

每组先做接入检查，再根据需求生成应用，冻结后运行官方 Keep 全部 32 项测试。所有设计、实现、上下文重建会话都属于同一次生成，usage 共同计入。SVC 与 braid 在项目内独立 Git 仓库共同开发；变更后重建，以源码哈希和运行归档区分实验变量。首轮四组分数属于旧的 tasks/generation 补丁，不能用来证明当前 braid 本地模式正确。

当前四组验证范围为本地单任务流程；另有无模型的 Playground 探针验证上传和 Agent 执行，但尚未验证四组 harness 的平台兼容性与完整评分。Keep 单任务分数不能表述为完整 ARC-bench 或线上 Lite 总分。各次结论记录在 reports/，未完成的实验不能计为零分或成功结果。

## 实验规则

独立生成基线只根据允许的需求与资源实现应用，不能读取外部验收测试、参考应用或先前失败报告。Agent 可以编写自己的检查并据此修改应用；外部评测必须在生成结束、应用冻结后执行。

如果后续实验主动使用公开评测反馈修复应用，必须创建新的 run 并标明 `oracle/dev-only`，不能与独立生成基线混淆。线上提交资格需要单独验证，不能由本地流程跑通推导。

固定并记录 benchmark 版本，不修改评测器来适配生成应用。完整评测中的失败用例是有效实验结果；安装、构建、启动或评测中断不能当作有效零分。上游需求或评测缺陷需要记录证据及影响。

每次实验保留输入和应用哈希、模型参数、原始 rollout、usage、退出状态及评测结果。缺失指标按未知处理，客户端费用估算不等于比赛账单。原始产物保存在被 Git 忽略的 `runs/`，可长期分享的脱敏结论保存在 `reports/`。
