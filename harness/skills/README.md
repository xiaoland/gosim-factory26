# 固定技能材料

这些文件是实验运行时材料，不是本仓库开发 Agent 的额外工作指令。来源版本归 `../dependencies.lock.json`；上游许可随技能保存。适配内容由 Factory 固定，运行期间不更新。

| 技能 | 取用内容与适配 |
| --- | --- |
| svc | 迁移前的固定单技能快照，仅供归档 variant 和 native-hackathon 的历史包使用。当前 `pi-braid` 从 `sources/svc/skills/` 选用七个独立技能。 |
| svc-documentation / svc-task-packet | 独立技能：前者维护项目知识导航、共享规则和契约；后者维护任务状态、材料、计划与恢复点。两者按需链接。 |
| frontend-design | Anthropic 的视觉选择、层级、文字与自检原则；去除虚构客户背景、等待客户确认、强制新颖性和固定设计轮次，给定需求与参考图优先。 |
| impeccable | pbakaus 的 craft-floor：层级、间距、真实内容、状态、可读性和界面反馈；不接入 launcher、hooks、菜单、强制产物或脱离 brief 的样式禁令。 |
| diagnosing-bugs | Matt Pocock 的症状反馈循环、最小复现、可区分假设与根因修复；移除硬性红测前置、固定假设数量、人工确认和每次永久回归测试要求。 |
| ponytail | 4.10.0 的复用顺序与复杂度判断；仅作用于技术实施，不削减授权要求，不替代 SVC 工作流程，也不强制回答格式。 |
| agent-browser | Factory 的薄操作导航；完整指令由固定版本 CLI 的 `skills get core` 提供。scripts/with-service.py 可包装已有检查入口（check-only）或一项前台服务，保留首轮日志、退出结果和调用者声明的运行前提，收尾自有进程组；不提供业务断言或改写应用。 |
| hyperformula、handsontable | Handsontable 维护者技能的短入口与固定 commit 的按主题参考；两项仅在选用相应库时提供知识，不安装应用库。技能 MIT 许可与运行库许可分开。 |
| better-auth-best-practices、organization-best-practices | 基于 Better Auth 官方文档独立撰写的短入口；组织插件和默认权限只在符合产品要求时选用。 |
| fixing-accessibility | 基于 ibelick/ui-skills 的交互要点，保留 MIT 许可；以需求和实际浏览器行为确定修复。 |

本项目获选的技能资源使用 SKILL.md 与 references/、assets/、scripts/ 标准目录；许可文件随包保留。
Factory 不解析方法正文，也不为 SVC 补装第二份 Corpus。
还原独立 `sources/svc` 工作树后，所选技能的目录链接即可使用；参赛制品里已是普通目录，不依赖外部链接。

浏览器操作默认使用 agent-browser。最终验收按需求选择可重复的应用测试或脚本；已安装的 Playwright Test 与 Chromium 仍可按需使用，不另设独立验收技能。

通用调查工具知识直接归 explorer 角色提示词；MCP 服务配置归各 variant 的 tools/mcporter.json，环境变量 MCPORTER_CONFIG 供工具读取，不再提供 exploration-tools 独立技能。

当前 `pi-braid` 与 `pi-braid-flash-team` 在 build.py 冻结此技能，run.py 将其加入成员主会话的技能目录，executor 和 browser-operator 的原生配置也启用它。
因此两者共享同一工具入口；工具可供检查执行者调用，不将最终验收职责转给 browser-operator。
coordinator/review 与历史团队 variant 的 build.py 也选择此技能，但其原生角色和主会话启用范围不同，且未随本轮构建/验证；native-hackathon/raw 使用独立历史打包路径，不能据此声称全variant或所有旧ZIP已覆盖。
现有冻结包不会因源码变化自动更新。
