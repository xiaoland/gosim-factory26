# 当前技能来源与注入方式

2026-09-28，用户要求检查额外自编技能，SVC 也列出。
依据：harness/skills/README.md、dependencies.lock.json、pi-braid/build.py、run.py 与原生角色配置。
以下是当前源码；attempt-06 不含本轮新增 with-service.py/视觉分工指引，下一次热修复才应用。

## 当前源码 pi-braid：13 项技能（已启动的 attempt-07 仍为14项）

| 技能 | 材料归属与自编范围 | 当前接入 |
| --- | --- | --- |
| agent-browser | 自编薄导航；完整浏览器操作手册由固定 CLI 0.38.1 的 `skills get core` 提供。本轮新增自编可选 scripts/with-service.py。不是直接原样采用上游同名 skill。 | 主会话/执行者可选技能；browser-operator 还直接注入导航正文。 |
| better-auth-best-practices | 根据 Better Auth 官方文档自编的短指南，虽同名但没有复制上游 skill 正文。 | 主会话以及 advisor/explorer/executor 可选。 |
| organization-best-practices | 根据 Better Auth organization 文档自编，亦非上游同名技能原文。 | 主会话以及 advisor/explorer/executor 可选。 |
| hyperformula | 自编短入口，附固定上游版本的按主题参考和许可；混合材料。 | 主会话以及 advisor/explorer/executor 可选。 |
| handsontable | 自编短入口，附固定上游版本参考和许可；混合材料。 | 同上。 |
| fixing-accessibility | 精简改写 ibelick/ui-skills，不是原样上游。 | 主会话、executor、browser-operator 可选。 |
| impeccable | 从 pbakaus/impeccable 选取并改写视觉/交互原则。 | 主会话、executor 可选。 |
| ponytail | 从 DietrichGebert/ponytail 4.10.0 适配，去掉本场景不适合的回答/强制测试规则。 | 主会话、executor 可选。 |
| svc-task-packet | 本地 SVC：外置工作记忆、恢复点与协作材料。 | 主会话、explorer、executor 可选。 |
| svc-investigation | 本地 SVC：按信息缺口组织调查。 | 主会话、advisor/explorer/executor 可选；explorer 直接注入 workflow。 |
| svc-design | 本地 SVC：需求、技术与验收方案。 | 主会话、advisor 可选；advisor 直接注入 workflow。 |
| svc-implementation | 本地 SVC：计划、实施与反馈。 | 主会话、executor 可选；executor 直接注入 workflow。 |
| svc-verification | 本地 SVC：判据、证据、归因与完成判断。 | 主会话和除 vision 外角色可选。 |

原生 vision：skills 为空、inheritSkills=false、仅 read 工具；它接收委派给定的图片与问题。
五个 SVC 入口由 harness/skills 下链接指向 sources/svc/skills，制品中是普通目录。

## 存在于仓库但未选入活动 pi-braid

- frontend-design：基于 Anthropic 上游适配；仅存量/归档消费者，不在当前 build.py 与 MAIN_SKILLS。
- diagnosing-bugs：基于 Matt Pocock 上游适配；同样未选入当前 variant。
- svc：历史单技能快照；当前五技能来自独立 SVC 源码，不能把旧快照当活动内容。
- browser-checks：已经删除，包含旧强制 executor 注入；旧冻结输入作为历史证据保留。

## 明确发现与处理

存在额外自编技能，尤其两个 Better Auth 名称容易被误认成上游原文，应按来源表理解。
exploration-tools 已按用户方向从当前源码删除：专业工具知识移入 explorer，MCP 配置移至 variant/tools，领域用法回到领域技能。attempt-07 的旧冻结材料仍保留该技能。
当前没有重新引入独立验收技能；with-service.py 放在既有 agent-browser 技能中，且不含需求断言或应用源代码。
可选 skill 与角色正文注入是两件事：三个 SVC workflow 会进入相应角色正文；browser-operator 也直接收到 agent-browser 导航。它们不是“只有模型选读才出现”。
本次清点不代表已逐篇确认内容有效；角色使用与方法耦合的判断结合 subagent-usage.md 的真实轨迹继续进行，不仅凭技能名称或篇数决定删除。
