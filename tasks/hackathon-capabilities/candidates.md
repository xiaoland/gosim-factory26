# 候选能力调查

本轮查阅项目维护者的原始仓库、技能正文及官方工具文档，未安装到活动 Harness。
检索结果仅用于找到来源；下列判断来自原始文件，不以技能市场排名或收藏量作为效果证据。
上游入口正文和 Git tree 身份存于 `runs/hackathon-capabilities/research/upstream/`，正式采用前固定 commit 与实际依赖版本，保留许可。

## 来源、内容与初步取舍

| 候选 | 来源与观测 | 设计判断 |
| --- | --- | --- |
| HyperFormula | [维护者技能](https://github.com/handsontable/handsontable-skills/tree/main/skills/hyperformula)，141 行入口，另有按任务分的 references；描述对象是无 UI 的公式引擎。 | 优先评估 Sheet 的公式求值、引用与重算需求；它不提供表格交互。Agent 选择该库后技能价值最高，不把“有公式需求”变成必须使用它。 |
| Handsontable | [维护者技能](https://github.com/handsontable/handsontable-skills/tree/main/skills/handsontable)，当前入口 834 行、41,465 字节，含配置、示例和多个旧版本迁移内容。 | 选择、编辑、键盘、粘贴等复杂网格交互可能有高收益；主题、UI 结构及版本接线须对照题目。入口过长的代价发生在读取技能时，不能误说全部正文常驻。若采用，优先将导航与详细资料分开。 |
| better-auth-best-practices | [Better Auth 官方技能](https://github.com/better-auth/skills/blob/main/better-auth/best-practices/SKILL.md)，具体库的安装、adapter、session、插件与版本文档。 | 只在需求确实需要认证且选型采用 Better Auth 时引入；不是通用“GitHub 应用开发”知识。 |
| organization-best-practices | [Better Auth organization 技能](https://github.com/better-auth/skills/blob/main/better-auth/organization/SKILL.md)，围绕该插件的组织、成员、邀请、RBAC。 | 组织对象的 UI 不自动等于需要该多租户插件；先确认题目是否要求真实身份与权限语义，再判断其增量。 |
| fixing-accessibility | [ibelick/ui-skills](https://github.com/ibelick/ui-skills/blob/main/skills/fixing-accessibility/SKILL.md)，136 行，覆盖名称、键盘、焦点、原生语义和表单错误。 | 两题都值得采用，作用于实际交互实现及浏览器观察；不将逐行审查命令当作有效验收，也不以隐藏 locator 反向修改语义。 |
| agent-browser | [Vercel 工具](https://github.com/vercel-labs/agent-browser)，本项目已固定 0.38.1，已有简短导航和浏览器子角色。 | 默认延续已有工具；检查关键旅程的实际能力和反馈质量，再决定是否需要替换。 |
| playwright-cli | [Microsoft 工具与技能](https://github.com/microsoft/playwright-cli/tree/main/skills/playwright-cli)，支持 snapshot、键鼠、session、网络等。 | 作为替代候选，不同时让两套等价 CLI 竞争同一浏览器任务。当前尚无证据说明更换工具会解决现有得分问题。 |
| systematic-debugging | [obra/superpowers](https://github.com/obra/superpowers/blob/main/skills/systematic-debugging/SKILL.md)，283 行，包含数据流追踪、假设和原路径复验，也包含固定阶段、红测前置及人类确认。 | 吸收有用诊断手段到 SVC investigation，不整套叠加第二种 SOP。与本地未启用的 diagnosing-bugs 一起消除内容重复。 |
| verification-before-completion | [obra/superpowers](https://github.com/obra/superpowers/blob/main/skills/verification-before-completion/SKILL.md)，120 行，强调声明应有证据，但要求当前消息内完整重新执行。 | 吸收清楚的触发描述与证据表达，保留 SVC 对证据适用范围、制品身份和复用的判断；不照搬全量重跑规则。 |

库技能的许可与库的运行许可分别处理；Handsontable / HyperFormula 选型时须确认适用使用条件，不能因为技能是 MIT 就假定库也相同。
本轮只调查能力，不代用户接受商业许可或新增付费服务。

## MCP 与 CLI

现有 variant 已提供 rg、ast-grep、MCPorter、Context7、Exa 和 agent-browser。
Context7 处理已知库的版本/API问题，Exa 用于未知来源发现；新增专用 MCP 应提供实际不同的知识覆盖，不为数量增加常驻工具定义。

Handsontable 提供[公开 Docs MCP](https://handsontable.com/docs/javascript-data-grid/docs-mcp-server/)，同一个入口覆盖 Handsontable 与 HyperFormula。
官方说明为无需 key 的 Streamable HTTP，工具 `search_docs` 接受 query、limit 与产品版本参数。
可通过现有 MCPorter 按需查询，作为 Sheet 选用这两库时的候选；官网生成容器的出网及服务可用性仍需实际运行确认，宿主能访问不能代替此证据。
版本锁定的本地技能资料仍应能承担常见问题，远端查询帮助处理具体缺口，不成为生成的强制前置。

目前不增加 GitHub MCP：构建 GitHub 风格应用并不需要操作真实 GitHub；Braid 的本地 Issue/PR 已有自己的协作 CLI。
也不增加额外表格计算 MCP：应用需要交付可运行的公式能力，Agent 调用远程计算服务不能替代应用自身实现。

## 优先检验的增量

优先核实两类缺口：Sheet 的领域状态与交互是否需要成熟库知识；两题从需求到可观察交互的反馈是否能被更直接的验证与可访问性技能改善。
区别“材料已提供”“实际选读”“用于一个决定或修复”“改善最终行为”，不能只看 skill 读取次数判断采用有效。
具体需求映射和最后取舍见 `requirements-fit.md`，SVC 拆分见 `svc-routing.md`。
