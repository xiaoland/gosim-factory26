# 当前两题的行为观察

本观察覆盖整个原运行及 hotfix-01/generation-02 接续，恢复前后按时间区分。
采集器保留路径、行号、对象与调用/结果关联；语义结论必须由实际材料支持，不按关键字或次数判定。

| 观察面 | 需要跟踪的事实 | 需要判断的问题 |
| --- | --- | --- |
| 原生 sub-agents | spawn 角色、任务、模型、独立会话、结果、调用者后续动作；status/wait另计 | 委派是否有边界、是否取得并采用结果、是否有重复等待或主会话重复执行 |
| Issue 工作流程 | description修订、讨论thread、分派、关联PR、实现所在会话和分支、交接及合并 | Issue是否先形成需求/方案，PR负责人是否实际承担实现；上下文整理是否有用 |
| 一般性工作流程 | 产品需求→技术方案与验收方案→计划/预演→实现→验收的材料、动作与时序 | 验收判据是否先于实现、初始条件是否保留、检查是否对应实际交付版本 |
| Agent skills | 可用技能清单、实际读取与返回、后续采用的具体动作 | 哪些技能有采用证据，哪些只读取，哪些当前没有证据；不要求为调用而调用 |

## 首次现场观察

- GitHub develop `c338578` 已合基础 PR #2，含产品/架构/验收文档、基础 PR task packet、后端测试与浏览器检查。Issue #5 已交给关联 PR #11 的独立负责人实施。尚不能据此认定所有子 Issue 都完成了设计与预演。
- Sheet develop `2914d2d` 是空树，基础实现仍在 PR #2；其余子 Issue 尚未指派。根正文已有需求分析、技术与共享契约决定；不要把计划正文视作后续行动已完成。
- 两题都有 advisor 调用证据；采集中还包含 status/wait 和 workflowScript，不能把这些操作总数直接当委派数量。原生记录存在缺头/缺历史情况，需要用子会话及调用结果补链。
- 已见 GitHub 读取 svc-design、svc-implementation、svc-task-packet、agent-browser、认证/组织技能；Sheet 读取 svc-design、svc-task-packet、svc-implementation、agent-browser、hyperformula、handsontable。此处仅声明读取记录，不声明全部成功装载或实际采用；其余技能暂未确认。
- GitHub验收方案包含分层检查、初始状态与持久化、精确角色/名称断言，并明确不以实现反改判据。基础 PR packet 有检查提交与结果记录；尚未独立复验这些应用检查，不能替代最终官方评分。

[develop 完整目录快照](develop-trees-20260929.md)。增量采集脚本与部署记录由对应工作单元维护。

## 2026-09-29 14:34 增量复核

hotfix-02于14:31接续；以下区分旧运行补读与接续后的事实。

- sub-agents：补读确认Sheet Issue #3于13:52明确委派advisor与vision，Issue #4于13:54委派vision。有图片路径、需求背景和具体观察问题，已超出仅根会话使用角色的情况。未完成所有返回结果→采用动作的逐项闭合；本批未确认explorer/executor的实际委派，不等于全程未使用。
- Issue流程：Sheet基础PR已合，子Issue #3/#4形成设计并分别交给PR #8/#9。GitHub身份PR #12已合、Issue #3已关闭；组织模块进入Issue #4/PR #13。GitHub已有1条hidden、5条resolved；Sheet仍0/0，存在多版契约评论叠加。
- 一般流程：Sheet PR #8发布候选d536aa2，报告backend47/frontend43、E2E13通过且记录git_head/dirty/exit；这些是Agent报告，未由主线独立重跑。14:34根comment #64直接核对候选，指出遗漏契约v1.3的min_rows/min_cols，要求PR补齐，说明局部PASS未被自动当整体完成，同时暴露旧判据/新契约不同步。继续跟踪该反馈是否被正确消费。
- skills：已有读取svc-design/implementation/task-packet以及agent-browser与候选库技能的证据；Sheet最终选择未采用Handsontable/HyperFormula，不能算未读取。文档/packet/分层检查有实际产物，但仍不足以将每项产物归因某个技能；svc-documentation、svc-verification的显式使用证据待补齐。

GitHub PR #11对根工作区47c453e/15c79a4的核对跨越本次恢复边界，旧产物已在14:17评论出现。不能据14:33的新回复就判断热修复后再次发生同一越界；需查实际写入时点与当前负责人动作。
