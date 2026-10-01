# Hackathon 能力选择与 SVC 技能路由

状态：设计、实施计划与独立预演已复核；源码和打包材料已实施并完成材料层面验收。真实模型行为与评分验收待当前冻结官网实验结束后另行决定。
2026-09-25 用户先确认“复核没问题，同意你的 agent skill 取舍方案还有 SVC 拆分方案”，随后以“可以开工。”授权五技能拆分、候选技能选材、`pi-team-mixed` 接线和新包构建。
本任务不改变正在运行的冻结制品，也不启动新的模型实验。

## 当前结果

- `sources/svc/skills/` 是五个独立 Agent Skills 的当前来源；`harness/skills/svc` 保存迁移前单技能快照，只供归档消费者。
- 活动 `pi-team-mixed` 的主会话和两个成员的原生子角色已显式选择技能；investigation、implementation、design 的方法正文各从对应 `references/workflow.md` 预装一次。角色仍用 fresh 上下文。
- HyperFormula、Handsontable、Better Auth 两项及 fixing-accessibility 是可选知识；固定上游资料与许可。Handsontable Docs MCP 经既有 MCPorter 按需查询。未预装应用库，未改 npm runtime 依赖。
- 新包为 `runs/hackathon-capabilities/20260925-pi-team-mixed-skills.zip`，SHA256 `ad47f4ff0f3066e1830a775393dac7053aec6fb653703f14208142b884d57f33`，434031362 bytes。实包清单显示 14 个技能入口、五个 SVC 入口、两个成员各自的角色配置和三份 workflow；活动包不含历史单技能 `svc`。复用 runtime 的 Braid revision 为 `89212933c976b889f27de1b8cfe863baf8f6042e`。
- 以上只证明材料实际装配；模型选读、MCP 在官网容器的可达性及成绩仍未知。未运行 Factory/Corpus 内容测试，未开启新模型实验，也未提交源码。

## 下一步与证据入口

当前官网实验由 `/root/hackathon_monitor` 用脚本每 900 秒监听，见 [Issue 拆分任务](../issue-decomposition/packet.md)。旧矩阵 journal 与用户手动重试保持各自身份；监听不修改源码、冻结输入或重复创建 run。`factory26-hackathon` scheduled heartbeat 已暂停。
实验结果出来后，向用户报告基线；下一轮的正式输入、提交方式与对照范围须由用户决定。新包的过程证据应区分技能已提供、实际选读、用于具体决定或修复，以及最终评分。SVC Corpus 的行为验收仍保留在 [SVC Corpus 任务](../svc-corpus-review/packet.md)。

GitHub 手动重试已报告 1/100，见 [原始分析与补充复核](../issue-decomposition/results/7207a7fe0845.md)。新的关键证据是相同 assignee 的独立工作项被根 Agent 当成自己继续承担，导致基础框架重复实现，以及错误投递模块指令、合并结果和完成声明不符。当前技能包未针对这些协作断点修正；下一轮方向先交用户复核，包保持未提交状态。

后续协作修正的范围、设计阶段与验收衔接见 [Braid 协作迭代](../braid-collaboration/packet.md)；本任务已完成的技能材料继续复用，真实行为验收保持开放。

- [设计与验收](design.md)、[实施范围](implementation.md)、[原生接口证据](rehearsal-native.md)、[独立预演](rehearsal-plan.md)。
- [需求映射](requirements-fit.md)、[候选来源](candidates.md)、[SVC 路由](svc-routing.md)、[工作区接续](workspace.md)。
