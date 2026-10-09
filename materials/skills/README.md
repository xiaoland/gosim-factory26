# 固定技能材料

技能正文是实验运行时材料，不是本仓库开发 Agent 的额外工作指令。来源版本归 `../dependencies.lock.json`；上游许可随技能保存。适配内容由 Factory 固定，运行期间不更新。

开发侧编写与维护方法见 [AGENTS.md](AGENTS.md)，涵盖标准格式、触发指针、信息分层和原则的判断依据；它不作为运行时技能分发。

| 技能 | 取用内容与适配 |
| --- | --- |
| svc | 迁移前的固定单技能快照，仅供归档 variant 和 native-hackathon 的历史包使用。其它 variant 从 `sources/svc/skills/` 显式选择独立技能，选择表以自己的 build.py 为准。 |
| svc-documentation / svc-specs / svc-task-packet | 独立选择：documentation 提供项目理解与共享规则维护方法，specs 定位长期知识的权威归属，task-packet 保存当前任务状态。跨技能入口是可选路线，以包内发现面为准；缺失时按 task-packet 的独立继续方式工作，不默认补装全部技能。 |
| frontend-design | Anthropic 的视觉选择、层级、文字与自检原则；去除虚构客户背景、等待客户确认、强制新颖性和固定设计轮次，给定需求与参考图优先。 |
| impeccable | pbakaus 的 craft-floor：层级、间距、真实内容、状态、可读性和界面反馈；不接入 launcher、hooks、菜单、强制产物或脱离 brief 的样式禁令。 |
| diagnosing-bugs | Matt Pocock 的症状反馈循环、最小复现、可区分假设与根因修复；移除硬性红测前置、固定假设数量、人工确认和每次永久回归测试要求。 |
| ponytail | 4.10.0 的复用顺序与复杂度判断；仅作用于技术实施，不削减授权要求，不替代 SVC 工作流程，也不强制回答格式。 |
| braid-collaboration | 按成果组织责任，分别判断任务边界与执行并发，消费交接与变化、核对执行、接受结果和结束义务；完整案例只保存一份，文档、委派与 V&V 深层方法引用 SVC。 |
| arc-bench | 从原需求树形成能力候选，结合父层约束、跨枝旅程、真实依赖和反馈调整工作边界，回查责任与覆盖，按需读取平台交付合同；单向引用通用 Braid 方法。 |
| agent-browser | Factory 的薄操作导航；原生接口由固定版本 CLI 的 `skills get core` 提供。运行检查、服务和日志包装按需读取 references/application-checks.md；scripts/with-service.py 保留执行事实并收尾自有进程组，不决定业务验收。 |
| e2e | 正文保存观察、隔离和验收判断，具备原生 owned 入口时使用 references/owned-session-entry.md，直接MCP连接与同attempt示例归 references/mcp-session-lifecycle.md；环境接线归 references/runtime-setup.md，冻结版本的退出与报告排障归 references/runner-results.md。pi-minimal-vv 的 builder 仅替换 runtime-setup，业务状态转移方法也归共享 reference；I15 不再维护整份 e2e 正文副本。 |
| hyperformula、handsontable | Handsontable 维护者技能的短入口与固定 commit 的按主题参考；两项仅在选用相应库时提供知识，不安装应用库。技能 MIT 许可与运行库许可分开。 |
| better-auth-best-practices、organization-best-practices | 基于 Better Auth 官方文档独立撰写的短入口；组织插件和默认权限只在符合产品要求时选用。 |
| fixing-accessibility | 基于 ibelick/ui-skills 的交互要点，保留 MIT 许可；以需求和实际浏览器行为确定修复。 |

技能复制、发现和实际启用的边界见 [共用材料](../README.md)。I13 的具体选择与工具接线归 [I13 本地说明](../../variants/pi-braid-i13/README.md#工具与技能接线)，本页只维护技能的来源与适配。

本项目获选的技能资源使用 SKILL.md 与 references/、assets/、scripts/ 标准目录；许可文件随包保留。
Factory 不解析方法正文，也不为 SVC 补装第二份 Corpus。
`sources/svc` 随 Factory26 源码取得；技能链接依赖本仓源码，参赛制品里已是普通目录，不依赖外部开发 SVC checkout。

浏览器操作默认使用 agent-browser。最终验收按需求选择可重复的应用测试或脚本；已安装的 Playwright Test 与 Chromium 仍可按需使用，不另设独立验收技能。

各 variant 的原生工具、MCP 服务与会话启用范围由自身接线维护，不从本页推断全 variant 覆盖。Context7 的独立 `context7-docs` 技能从锁定并补丁后的 npm 包收录，来源版本归 npm lock，不在此复制其正文。已有冻结包不会因源码变化自动更新。

`pi-minimal-vv` 使用自身的 `skills/e2e/references/runtime-setup.md` 作为独立项目接线来源；装包时复制为普通文件，不对技能正文做全文替换。I15 默认消费当前共享技能库，再应用 variant 中明确保留的差异文件，不再维护部分技能刷新名单。主会话、reviewer 和子角色仍按各自声明决定发现入口；这些变化只对后续新装配生效。
