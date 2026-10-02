# Hackathon requirements fit

本调查只读取官方公开 requirements、当前 `pi-team-mixed` 接线和 `harness` 材料；没有读取测试、coverage、评分器或旧应用，也没有查候选项目的外部实现。

官方输入：

- GitHub：`wsl.win-ws.localhost:/home/yyh/Development/factory26-official-local/platform-inputs/hackathon/github/requirements/requirements.yaml`（47 个 ATOMIC）；本地副本为 [github/requirements.yaml](/Volumes/WorkSSD/Development/factory26/runs/hackathon-capabilities/research/requirements/github/requirements.yaml)。
- Sheet：`wsl.win-ws.localhost:/home/yyh/Development/factory26-official-local/platform-inputs/hackathon/sheet/requirements/requirements.yaml`（24 个 ATOMIC）；本地副本为 [sheet/requirements.yaml](/Volumes/WorkSSD/Development/factory26/runs/hackathon-capabilities/research/requirements/sheet/requirements.yaml)。

## 先给结论

GitHub 需求确实需要登录、持久 session、组织/团队/仓库授权和按操作检查的权限；它不是只做公开仓库浏览，也不是要求接入生产 IdP、邮件或 OAuth。注册后邮箱直接 verified，找回密码使用页面上固定的 `123456`，系统不发邮件、不生成 reset link、不调用外部验证码服务。需要实现的是本地应用的账户、密码、session、组织成员关系、团队层级、仓库可见性和权限矩阵，并在刷新、返回、重新打开后保持结果。

Sheet 需求确实需要公式、矩形选区、键盘/剪贴板、结构变更后的引用调整、持久化和精确可访问性状态。公式引擎与表格网格是两个问题：HyperFormula 只能覆盖计算/依赖的一部分，Handsontable 只能覆盖网格交互的一部分；两者都不能代替服务端持久化、业务弹窗、CSV、验证、pivot 或本题规定的 ARIA 契约。

“多租户”在这里是产品领域行为而非生产 SaaS 交付：组织、个人 namespace、私有仓库、成员/团队 grants 和权限隔离都要有；没有计费、跨租户运营后台或外部身份提供商的要求。

## 按需求组映射

“已有覆盖”指当前 Harness 能提供的 Agent 工作方法或验证工具，不表示生成应用已经实现该产品功能。

| 需求 ID | 关键产品行为 | 候选能力 | 已有覆盖 | 增量价值与风险 |
| --- | --- | --- | --- | --- |
| GitHub `REQ-1-1-1`, `REQ-1-1-2`, `REQ-1-1-3`, `REQ-1-2`, `REQ-1-3` | 注册字段和密码规则、精确字段错误、通用 `Invalid credentials`、账号和 session 持久化；登出只使当前浏览器 session 失效；改密；固定可见验证码 `123456` 的本地找回流程。 | `better-auth-best-practices` 可提供密码/session 的通用安全检查；`fixing-accessibility` 可复核 label、密码字段和状态反馈。 | `agent-browser` 可操作并观察页面；SVC、`impeccable` 提供通用实现/界面方法。没有 Better Auth 或认证专用 skill 接线。 | 需要应用内账号/session 和安全存储；生产邮件、OAuth、MFA、验证码服务不在需求内。Better Auth 指南若假定其默认邮件/插件流程，可能与固定码和精确 UI 冲突；它不能替代后端持久化或权限检查。 |
| GitHub `REQ-2-1-1`, `REQ-2-1-2`, `REQ-2-2-1`…`REQ-2-2-4`, `REQ-2-3` | 组织仓库浏览和私有过滤；创建组织；Owner 维护团队、父子层级和成员；直接添加/移除成员；仓库给人或团队授予 `Read/Triage/Write/Maintain/Admin`，修改 grant 不重复；私有仓库按当前有效 grants 决定可见。移除成员还要清理其组织团队成员关系和直接 grants。 | `organization-best-practices` 是 Better Auth organization 插件的具体 API 指南，可帮助核对组织、成员、团队和邀请/权限接口边界；`better-auth-best-practices` 只能补充 session 边界。 | 当前没有 Better Auth 或组织插件接线；通用 SVC 方法和 explorer 可帮助拆模型；`agent-browser` 可检查 Owner/non-Owner 控件是否存在或缺失。 | 只有在实际选用 Better Auth organization 插件时，指南才有直接 API 增量；否则需求仍需自有持久模型。即使采用也不能照搬默认 RBAC：官方需求明确角色不是自动累加梯度，团队层级不传播成员资格/授权，不能用“组织成员=私有仓库可见”的简化。 |
| GitHub `REQ-3-1`, `REQ-3-2-1`…`REQ-3-2-3`, `REQ-3-3`, `REQ-3-4` | 全局仓库搜索和私有结果隔离；创建个人/组织仓库、visibility、README；fork 复制可访问历史并保留来源关系；复制 HTTPS/SSH clone value；公开 overview；Admin 才可改 visibility，变更后公开/私有规则立即生效。 | `organization-best-practices`（Better Auth organization 插件 API）只对组织 namespace/成员边界有条件参考价值；`agent-browser` 可验证搜索、clipboard 和 reload。 | agent-browser 已接线；没有 Git/仓库领域能力专用 skill。 | 只有实际采用该插件时才有 API 增量；插件不能实现仓库对象、历史、fork 或 visibility 规则。主要产品增量仍是明确 namespace、visibility、fork lineage 和原子写入；风险是把 clone value 当成真实远端协议或把 fork 当成页面复制。 |
| GitHub `REQ-4-1`, `REQ-4-2-1`…`REQ-4-2-3`, `REQ-4-3-1`…`REQ-4-3-3`, `REQ-4-4` | 按分支浏览目录/文件；提交历史、commit/revision diff、仓库内 code search；分支列表/切换、从 revision 建分支、Admin 改默认分支；Web 文件创建/编辑/删除/历史写入，权限与 reload 保持。 | `agent-browser` 只适合验证真实页面旅程；`fixing-accessibility` 可复核树、链接和控件语义。 | `agent-browser`、SVC exploration/implementation 方法已进入相应内部角色；无 Git 对象或 diff 实现能力。 | 需要后端持久提交图、分支 head、路径内容和操作权限。候选技能不会减少这部分产品实现；风险是只做静态文件列表而不维护 commit/branch 关系。 |
| GitHub `REQ-5-1-1`, `REQ-5-1-2`, `REQ-5-2-1`…`REQ-5-2-3`, `REQ-5-3-1`…`REQ-5-3-3`, `REQ-5-4` | issue 列表/过滤/详情和讨论；创建、编辑、评论/反应；按权限管理 assignees、labels、milestones；Triage/Maintain/Admin 才可关闭/重开；状态、操作者、时间、关联关系持久化。 | `organization-best-practices`（Better Auth organization 插件 API）只能条件性帮助核对成员/组织 API 边界；`fixing-accessibility` 适合复核菜单、dialog、combobox。 | agent-browser 可观察 UI；SVC 方法已覆盖协作流程，不含 issue 领域模型。 | 插件指南不能覆盖 issue 权限或状态机；只有实际采用该插件时才有 API 增量。仍需清晰权限矩阵和原子关联更新，避免让 Write/Read 获得 Triage 操作，或只隐藏按钮而后端仍接受未授权写入。 |
| GitHub `REQ-6-1`, `REQ-6-2-1`…`REQ-6-2-4`, `REQ-6-3-1`…`REQ-6-3-4`, `REQ-6-4`, `REQ-6-5`, `REQ-6-6` | 分支保护只支持 exact branch、1 个非作者有效 Approve 和 `test` success 两个独立条件；PR 列表、比较、普通/草稿创建；overview、commit、changed files/diff、行内评论、review、reviewer request；合并前重读 head/compare/protection/review/check，成功才原子生成 merge commit；关闭/重开不合并。 | `organization-best-practices`（Better Auth organization 插件 API）不能覆盖 review/merge 状态机；`fixing-accessibility` 可覆盖 review controls 的键盘和状态复核；`agent-browser` 可做端到端观察。 | agent-browser 和 SVC 协作方法已有；无 Git merge/review 专用能力。 | 这是持久状态机和权限/一致性问题；插件指南只有在实际采用时才提供成员 API 参考，不能覆盖 review/merge。风险是把 Merge 当成标记 PR 状态，或把旧 review/check 继续算入新 compare commit；需求要求失败时 branch 与 PR 均不变。 |
| Sheet `REQ-1-1-1`, `REQ-1-2-1`, `REQ-1-2-2`, `REQ-1-3-1`, `REQ-1-3-2` | workbook 列表/打开/创建/重命名；直接 URL/刷新/重开恢复同一 workbook 和 active worksheet；CSV 导入保留行列、空字段、UTF-8、引号/换行；CSV 导出按实际 used range、转义内容，公式导出当前结果；成功修改持久化，失败不留下半条记录。 | `agent-browser` 可验证 URL、文件上传/下载；`fixing-accessibility` 可复核对话框和文件控件。 | agent-browser 已接线；无 CSV 或 workbook 专用 skill。 | 候选网格库不能自动提供服务端持久化、原子导入/导出和恢复 URL。风险是只处理简单逗号分隔文本，遗漏 quoted comma、escaped quotes、嵌入换行和空字段。 |
| Sheet `REQ-2-1-1`…`REQ-2-1-4`, `REQ-2-2-1`, `REQ-2-2-2` | worksheet 增删、切换、重命名、最后 active tab/selection 恢复；行列插入/删除要移动数据、validation 和 formula references，pivot source 变更有明确刷新/删除约束。 | `handsontable` 可覆盖部分 tab/grid/row-column 交互；`fixing-accessibility` 可检查 ARIA tabs/menus/dialogs；`hyperformula` 可帮助结构变更后的公式引用调整（若真实接入且 API 能覆盖）。 | 只有通用 UI 设计、SVC 和 agent-browser；`harness/npm/package.json` 未声明两库。 | Handsontable 对网格编辑/结构操作有高增量，但自定义持久化、pivot 依赖约束、错误文案和 ARIA 状态仍需实现。HyperFormula 对引用迁移有价值但不懂 worksheet 生命周期或 UI。两者同时引入会增加适配边界，先证明需求覆盖再选。 |
| Sheet `REQ-3-1-1`, `REQ-3-1-2`, `REQ-3-1-3` | 单元格/公式栏编辑；Enter 提交、Escape 取消；TSV/换行二维 paste 要全量原子应用；矩形拖选必须精确，grid 为 `aria-multiselectable=true`，内外 cell 的 `aria-selected` 准确且选区跨刷新/worksheet 保持。 | `handsontable` 适合 editing/selection/clipboard/keyboard 的基础交互；`fixing-accessibility` 直接适合 ARIA 契约审查；`agent-browser` 可读取 accessibility tree。 | agent-browser 已接线，但它是观察/操作工具；没有网格或 accessibility 专用 skill。 | Handsontable 的增量大于单纯写 DOM，但精确 accessible names/states、选区持久化和全量失败回滚仍须自建/核验。键盘和浏览器 clipboard 是产品行为，不是 agent-browser 自动带来的能力。 |
| Sheet `REQ-3-2-1`, `REQ-3-2-2` | 同 worksheet 的 copy/cut/paste 保留二维布局；相对/绝对引用正确调整；source/target 要原子；Undo/Redo 覆盖编辑、paste、移动、行列结构，按钮和 Ctrl-Z/Ctrl-Y 一致，刷新后状态持久，undo 后新修改清空 redo 分支。 | `handsontable` 可减少基础 clipboard/keyboard/grid 代码；`hyperformula` 可支持复制公式后的计算；`agent-browser` 适合验证快捷键结果。 | 只有 agent-browser 与通用方法；无 history/grid/formula skill。 | 这组需求仍需要应用自己的操作记录、原子事务和持久化；库的默认 undo 语义、跨 workbook 隔离和规则/pivot 恢复必须逐项核对。风险是只 undo 可见值，没有恢复公式、规则、结构和计算结果。 |
| Sheet `REQ-4-1-1`, `REQ-4-1-2`, `REQ-4-2-1`, `REQ-4-2-2` | 支持常量/括号/四则/A1 引用、SUM/AVERAGE/COUNT/MIN/MAX；公式栏保留原表达式，grid 显示结果；复制时相对引用偏移、绝对引用不变；编辑/paste/移动/插删行列后依赖按序重算；稳定显示 `#DIV/0!`, `#REF!`, `#NAME?`, `#ERROR!` 和循环错误，错误可修复且持久。 | `hyperformula` 是最直接的候选计算引擎；`handsontable` 只有在配合公式插件/外部引擎时才有价值；`fixing-accessibility` 对公式栏/错误提示有辅助价值。 | 没有公式引擎或表格库接线；SVC/agent-browser 只能帮助实现/验证。 | HyperFormula 的增量价值高，尤其是 dependency graph、函数解析、错误和引用调整；但它不负责公式栏与 grid、持久化、undo、row/column/pivot 业务。需求不要求 cross-worksheet refs，避免为更大公式语言建模。风险是把库结果直接当作规定的原始 formula/error 文案而不加适配层。 |
| Sheet `REQ-5-1-1`, `REQ-5-1-2`, `REQ-5-2-1`, `REQ-5-3-1` | 选区内稳定排序（header、类型比较、稳定顺序）；多列 AND filter 只隐藏不删除；Dropdown/Number range validation 作用于输入、paste、range move，批量失败全量回滚；pivot 只支持一 row、可选 column、一 value 和 SUM/COUNT/AVERAGE，结果/字段/refresh 错误持久。 | `handsontable` 可参考/覆盖基础 sort/filter/grid UI；`hyperformula` 可提供 pivot 聚合所需的计算，但不能替代 pivot editor/result worksheet；`fixing-accessibility` 可检查 dialogs/options/combobox/grid。 | agent-browser、通用 UI 方法已有；没有 sort/filter/validation/pivot 专用能力。 | 这是最可能需要应用层实现的区域：候选库不能保证 exact dialog text、first-appearance order、Grand Total、source field 删除保护、validation 全量回滚。风险是采用库默认排序/过滤/validation 语义而违反持久化和 pivot refresh 规则。 |

## 候选能力逐项判断

| 候选 | 类型和实际适配 | 当前状态 | 建议与边界 |
| --- | --- | --- | --- |
| `hyperformula` | 库专属指南/计算引擎，不是通用产品方法。直接对应 Sheet `REQ-4-1-*`, `REQ-4-2-*`，并可辅助 `REQ-2-2-*` 的引用迁移与 `REQ-3-2-1` 的公式复制。 | 未出现在 `harness/npm/package.json`，也未在 `harness/skills` 或 `pi-team-mixed` 接线。 | 这是候选中对实际产品缺口最明确的一项，但只有在确定采用该引擎后才值得分发指南。保留自有适配层：原始公式、规定错误字符串、依赖刷新、持久化和 transaction 仍由应用负责。不要把它当成完整 spreadsheet 能力。 |
| `handsontable` | 库专属网格指南。直接对应 Sheet `REQ-2-*`, `REQ-3-*` 的编辑、选区、剪贴板、键盘和部分 sort/filter；对 ARIA grid 可能有基础支持但不能假定满足精确契约。 | 未出现在 `harness/npm/package.json` 或现有 skills。 | 可显著减少交互代码，但引入前要对 exact `aria-selected`, `aria-multiselectable`, accessible names、持久化 selection、原子失败和自定义 dialogs 做最小垂直验证。不要为了 24 条需求默认引入，同时使用它和另一套 grid 实现会造成重复。 |
| `better-auth-best-practices` | 具体认证库/插件指南，不是生产认证的需求说明。对 GitHub `REQ-1-*` 的 session、密码、恢复安全有参考，但默认流程可能含 email/plugin 语义。 | 当前没有 Better Auth 依赖或接线。 | 不应以“生产认证”名义加入默认包。若后续应用明确选 Better Auth，再只采用与本地固定码、已验证邮箱、精确错误和 session 持久化兼容的部分；否则通用 auth 边界写入实现/评审即可。 |
| `organization-best-practices` | Better Auth organization 插件的具体 API 指南，不是通用组织方法。对 GitHub `REQ-2-*`, `REQ-3-4` 的组织、成员、团队和 namespace 边界有条件适配；不能覆盖 `REQ-5/6` 的 issue/review 状态机。 | 当前没有 Better Auth 或 organization 插件依赖/接线；指南来源为 `better-auth/skills/better-auth/organization/SKILL.md`。 | 只有在后续明确采用该插件时，才有直接 API 增量；否则它只是候选参考。必须以官方 ROOT/atomic 规则为准，避免插件默认 RBAC 的累加角色、团队层级传播或默认私有仓库可见。 |
| `fixing-accessibility` | 通用方法/审查技能，不是 UI 组件库。直接适配两套需求中的 exact accessible names、ARIA roles/states、keyboard behavior、dialog/menu/combobox 和“未授权控件必须缺席”。 | 当前没有该 skill；agent-browser 能读 accessibility tree，但不自动审查或修复。 | 这是低依赖、高回报的补充，尤其是 Sheet `REQ-1-1-1`, `REQ-2-1-*`, `REQ-3-1-*`, `REQ-5-*` 和 GitHub 的菜单/权限控件。仍必须逐条回到 requirements YAML，不能让通用建议覆盖需求规定的精确文字。 |
| `agent-browser` | 浏览器操作/证据工具，不增加生成应用功能。适用于所有需要真实页面、刷新、回退、上传下载、clipboard、ARIA tree、键盘结果的验证。 | 已在 `harness/skills/agent-browser/SKILL.md`；`harness/npm/package.json` 声明 `agent-browser: 0.38.1`。`pi-team-mixed/run.py` 将其放入 executor/browser-operator；`build.py` 也打包它。 | 已覆盖，不需重复加入另一份操作指南。它不能替代应用持久化、服务端授权，也不能把一次点击当成保存成功；现有 skill 已要求操作后观察结果。 |
| `playwright-cli` | 通用浏览器 CLI/验证工具，不是应用能力。可用于脚本化重复旅程、下载/上传、键盘和 accessibility 检查。 | 候选 CLI 未安装；仅有 `playwright-core: 1.61.1`，它是库依赖，不等于 Playwright CLI。 | 当前已由 agent-browser 覆盖相同验证面；除非出现 agent-browser 无法稳定复现的具体缺口，否则新增 CLI 是重复运行时和维护成本。不要因为 package 中有 `playwright-core` 就宣称已有 `playwright-cli`。 |

## 当前接线证据

- `variants/pi-team-mixed/run.py` 的 `native_files()` 将 SVC 的 explore/implementation/design 方法和 `exploration-tools` 注入对应角色；`executor` 与 `browser-operator` 另取 `agent-browser`。
- `variants/pi-team-mixed/run.py` 的主 Pi launcher 显式启用 `svc`, `ponytail`, `impeccable`, `exploration-tools`；`build.py` 打包 `svc`, `ponytail`, `impeccable`, `agent-browser`, `exploration-tools`。
- `harness/skills/README.md` 列出 `frontend-design` 等历史固定材料，但当前 `pi-team-mixed/run.py` 的 launcher 未启用 `frontend-design`；当前活动接线使用 `svc`, `ponytail`, `impeccable`, `exploration-tools`，browser-operator/executor 另取 `agent-browser`。当前没有 HyperFormula、Handsontable、Better Auth、组织权限或 accessibility 专用材料。
- `harness/npm/package.json` 只声明 `@ast-grep/cli`, Pi/Codex、`agent-browser`, `mcporter`, `pi-subagents`, `playwright-core`；没有 `hyperformula`, `handsontable`, Better Auth 或 `playwright-cli`。

因此，候选优先级应按真实缺口排序：公式需求优先评估 HyperFormula；网格交互优先评估 Handsontable 但先做 ARIA/持久化垂直切片；accessibility 方法可作为轻量补充；认证和组织候选只能作为受边界约束的指南；agent-browser 已经足够，playwright-cli 暂无增量理由。
