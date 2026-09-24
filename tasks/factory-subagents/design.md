# 角色 SOP、工具选择与解耦

本稿已完成用户要求的方案修正与审查，并通过设计复核；本轮实现已完成，实际生效待统一验收。
角色内聚性来自它能独立运用一套工作方法与工具完成局部任务，而不是给角色追加更多领域职责或限制。

本轮重点是 Hackathon 四角色；Braid Factory 同步纠正上下文政策、固定前置阶段及方法可达性，不重排其成员和原生角色集合。
具体角色正文与方法来源见 [角色方案](roles.md)，原生接线和工具取得见 [技术方案](technical.md)，实际运行判据见 [验收方案](verification.md)。
模型配方保持当前值；实施计划与独立预演已完成，已按 plan.md 获准实施；用户将验收推迟至后续统一实验。

## 上下文与角色内容

这些原生子 Agent 明确不继承主会话历史。
父 Agent 提供任务增量、必要事实和材料路径，子 Agent 从自己的角色指令、选定技能与这份委派开始。
需要补充的信息由定向读取或后续消息传递，不以完整 fork 补足。
这不等于清空模型配置、工具定义或显式装载的技能。

Pi 角色显式 defaultContext:fresh，父调用明确 context:fresh；项目指令与技能目录继承分别配置，不能冒充历史开关。
Codex 0.155.0 的工具有两套协议：V1 调用 fork_context:false，V2 调用 fork_turns:"none"。
父调用指引按实际工具协议表达；单在子角色正文写“不继承”无法撤销启动时已经复制的历史。
此方案使用原生接口和明确调用指引，不新造过滤代理；实际执行是否遵从须从子会话记录确认。

主 Agent 看到的 description 只需帮助选角。
子 Agent 的正文提供工作方法、工具选择依据与局部完成标准。
具体委派补充当次问题；角色正文不预定后续由哪个角色接手。

explorer 的 SVC 组在角色上下文中直接取得 SVC Explore SOP：识别缺失答案及其用途、选择合适证据、区分观察与解释、在足以支持决定时停止。
实现时从已分发 skill 的相应文件取得正文及来源路径，避免手工维护第二份 SOP；详细延伸材料仍按需读取。
executor 同样取得 SVC Implementation 中与局部执行有关的方法，而不是额外承担 API/持久化领域角色。
base 组保持无 SVC；工具使用知识可以与 SVC 组保持一致。

## Explorer 的工具判断

下表是选择依据，不是全部执行一次的顺序。
已知入口直接读取；问题变化时可切换工具。

| 探索问题 | 适用工具与判断 |
| --- | --- |
| 已知字面量、错误文本、文件名或符号拼写 | rg/文件查找快速定位，再读取必要上下文。 |
| 调用、表达式、语法节点及其结构关系，文本匹配噪声大 | ast-grep；按项目语言选择结构模式，不为简单字面量查询创建 AST 规则。 |
| 某个库或框架的 API、版本用法与代码示例 | Context7；确认库身份和目标版本，结果与实际安装版本相符。 |
| 不知道资料位于哪里，需跨站发现技术材料或方案 | Exa 搜索/取页；找到相关原始来源后定向核实，不把摘要直接当实现事实。 |
| 代码或文档无法回答的实际行为 | 在委派允许的范围内做最小真实观察；若需其他能力，由父 Agent 根据问题决定如何补足。 |

当前 Factory 原生 Pi 有 grep/find/ls/read/bash；仓库自己的 CLI/MCP 装配中没有发现 ast-grep、Context7、Exa 接入。
开发机存在 ast-grep skill 不证明参赛包具备工具；rg 是否作为独立命令在最终镜像可用也不能只凭本机推断。
建议把 rg、ast-grep 装入运行资源，以 MCPorter CLI 调用 Context7、Exa 的公共 MCP 服务。
两种 Factory 使用同一套工具指引，SVC/base 组工具相同；不为同一能力分别维护 Codex MCP 和 Pi 扩展接线。
MCPorter 已提供所需发现、调用与错误输出，Factory 只提供配置和角色知识，不实现 MCP 客户端。
2026-09-24 已取得当前工具定义，独立预演也完成了实际结构搜索及 Context7/Exa 文档查询；这不保证持续额度或目标制品中的执行，详见 rehearsal-tools.md。
不将缺少工具的现状处理成每个角色都运行安装/自举流程。

工具能力参考：<https://ast-grep.github.io/guide/introduction.html>、<https://context7.com/docs/overview>、<https://exa.ai/docs/get-started/exa-mcp>。

## 同类耦合审查

| 当前位置与行为 | 问题 | 拟处理 |
| --- | --- | --- |
| Hackathon 主指令“先让 explorer…让 advisor…让 executor…” | 把角色集合变成固定流程，简单任务也被诱导派活。 | 给出角色选择依据，由当前问题决定直接完成还是委派，不规定必经角色。 |
| Braid 六份主指令与 specialist 正文要求普通路径未收敛 | 把独立判断绑定到失败之后，不能在高返工风险的决定前使用。 | 用决策难度、不确定性和独立判断价值描述适用场景，去除固定前置阶段。 |
| Hackathon write_roles 复用 instruction 作为 description 与正文 | 选角信息与执行方法共用一段文本；补强 SOP 会让主上下文也接收冗长工作细节。 | 保持简短 description，将 SOP 与工具知识放入子角色正文/专用材料。 |
| 仅说“SVC 可用于 planning/verification” | explorer 的 Explore、executor 的 Implementation 依赖主会话重复补充或子代理自行猜入口。 | 让所选角色实际接到对应方法；保持 SVC 为方法来源，Factory 为装配者。 |
| 新 Pi 配置未关闭 pi-subagents 内建角色 | 四个自定义角色之外还会发现其他角色，带入未设计的模型、历史继承和工作方法。 | 与 Braid 的现有做法一致，设置 disableBuiltins:true，保留四个明确配置的角色。 |
| Pi 四角色依赖默认 replace，而 Codex 使用 developer_instructions | 相同的短角色正文在两端对应不同基础工具指引，不能据文本相同推断角色能力相同。 | Pi 显式 append，保留原生工具方法，角色正文增加本次职责、SOP 与工具知识；历史仍为 fresh。 |
| Pi 把 svc 与 browser skill 作二选一，Codex 从 home 发现所有已装配 skill | 功能差异由实现分支偶然决定，executor 的浏览器反馈知识不一致。 | 明确每个角色的技能选择与装载方式，方法内容按角色提供；不把所有技能全文塞给所有角色。 |

已审查四角色生成器、raw 任务指令、四个 Braid variant 的六套角色/主指令、SVC sub-agents 与 Explore/Implementation。
SVC 中“先理解问题”“先检查委派收益”等是有因果依据的方法，不等同于固定角色交接；本轮未据此扩大修改。
现有 Braid Issue/PR 的设计与实现职责是已确认产品行为，也不作为这次子 Agent 解耦的删除对象。
browser-operator 与 vision 的分工在既有 Braid Factory 有独立工具边界，不因本次审查擅自合并角色。
本轮没有发现 SVC Explore/Implementation 强制按角色名交接的流程；不修改这些方法来消除并不存在的耦合。
也不把现有 agent-browser 的版本匹配使用指引视作错误耦合：这是选定工具的必要知识，允许角色按观察目的选择其操作。

验收需区分：实际角色与工具装载是否正确、不继承历史是否发生、角色是否用合适方法形成可采用的结果。
不要求每个角色或工具都被调用；不以委派数量、提示词字数证明内聚性。
不修改既有冻结包或新增实验矩阵；具体实验安排待后续实施说明复核。
