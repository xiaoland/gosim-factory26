# 外部 agent skill 候选（2026-09-21 核验）

本页逐项评估技能及其实际依赖，不推荐因作者或仓库名气而整包安装。判断标准是 Factory 的实际边界：Braid 工作项与 Pi 原生 subagent 分层，模型保留语义判断；ARC-bench 可无人值守。因此，要求人类审批、强制 TDD、固定角色/阶段流水线的内容，即使方法本身合理，也不能直接成为全局硬规则。

主 Agent 核验 frontend-design、agent-browser 与 Impeccable；explorer 有界筛选下面三项，主 Agent 复读实际技能中影响取舍的条款后整合。以[社区使用讨论](https://www.reddit.com/r/ClaudeCode/comments/1w47y8j/which_skills_are_you_using_frequently/)发现线索，再看作者文章、GitHub 履历、技能原文和修改；不把 star 或口碑当效果证据。X 检索未获得比这些原始材料更有用的实践证据，因此不补充未经核验的转述。

## 1. obra / Jesse Vincent：`verification-before-completion`

- **用途：**在声称“已修复、测试通过、构建通过或任务完成”前，先确定能证明该断言的命令，实际运行并检查完整输出、退出码和失败数。它还明确要求不要信任 subagent 的“成功”报告，要看 diff 和独立验证。
- **原始技能：**[SKILL.md](https://github.com/obra/superpowers/blob/main/skills/verification-before-completion/SKILL.md)；[raw 版](https://raw.githubusercontent.com/obra/superpowers/main/skills/verification-before-completion/SKILL.md)。
- **作者工程经历：**Jesse Vincent 的[本人简介](https://blog.fsck.com/about/)称其长期构建 Request Tracker、K-9 Mail，并任过 Perl 5 Project Lead；这比“技能作者”身份更能说明其有真实维护经验。
- **持续实践/优化证据：中等偏强。**作者在[本人使用报告](https://blog.fsck.com/2025/10/09/superpowers/)中详细说明工作流演变、如何用真实场景而非问答测验检查 skill；这构成自用的一手证据。技能在 2026-07-05 仍有[针对 eval 的内容精简提交](https://github.com/obra/superpowers/commit/3be5aad)，仓库随后仍在更新（[仓库元数据](https://api.github.com/repos/obra/superpowers)）。这证明该技能被维护、且维护者用评测检验过表达改动；不能单凭此推出 Jesse 在所有日常项目中逐条执行它。
- **内容成本与 SVC 冲突：有明显重叠。**核心是“声明与新鲜证据匹配”，不要求设计审批、TDD 或特定角色序列。它的“每次消息都必须重新跑完整命令”若照字面全局化，会对长任务和不适合全量运行的检查造成浪费；应把 `full` 解释为“与所作断言相称的完整验证”，并保留 SVC 的证据入口和任务状态为准。
- **主 Agent 结论：作为 SVC V&V 的对照材料，本轮不再叠加为独立 skill。**explorer 最初建议轻量适配接入；复核后，已有 V&V 原文和项目工作约定已覆盖其核心证据纪律，再引入一套权威收益不足。原文还把新鲜度绑定到“这条消息内重新运行”，容易导致重复验证；证据是否过期应按被验证状态与影响范围判断。

## 2. Matt Pocock：`diagnosing-bugs`

- **用途：**为难复现 bug 或性能回退先构造紧凑、可无人执行、能对用户原始症状变红的反馈环；随后最小化复现、提出可证伪假设、做定向探针、修复并回归验证。对 Web 应用可选用 HTTP、headless browser、trace replay 和 `git bisect`。
- **原始技能：**[SKILL.md](https://github.com/mattpocock/skills/blob/main/skills/engineering/diagnosing-bugs/SKILL.md)；[raw 版](https://raw.githubusercontent.com/mattpocock/skills/main/skills/engineering/diagnosing-bugs/SKILL.md)。
- **作者工程经历：**Pocock 的[GitHub 主页](https://github.com/mattpocock)自述为前 Vercel、Stately 工程师，且维护 TypeScript 工程项目；这是与 Web/TypeScript 实现直接相关的公开一手简介。
- **持续实践/优化证据：强。**[作者的技术说明](https://www.aihero.dev/skills-diagnosing-bugs)解释了反馈环、假设和定向探针的关系。该仓库把技能称为“Straight from my `.agents` directory”（[仓库主页](https://github.com/mattpocock/skills)）；该文件在 2026-08 有多次[历史提交](https://github.com/mattpocock/skills/commits/main/skills/engineering/diagnosing-bugs/SKILL.md)，其中一项明确移除了无法实际触发的跨技能交接。这可证明作者持续在真实 agent 配置中修订；“所有步骤均被长期 dogfood”的力度仍无法从公开材料独立证实。
- **内容成本与 SVC 冲突：需要适配。**它把“先有可变红的紧凑命令”设为后续诊断的前置条件，并要求向用户展示 3–5 个假设。前者可能卡住缺少可复现环境的故障。后者明确允许用户不在线时继续，不能误报成强制审批；但固定 3–5 个假设与“没有红反馈就不能推理”仍过强。其 Phase 5 只在有合适 seam 时要求先写回归测试，不能把这一条件省略。SVC 已有面向运行产物的诊断入口，不能被这一流程替代。
- **结论：不建议直接接入。**建议只摘取“反馈环要针对原始症状、最小化复现、探针须区分假设”三条，按现有 Braid/SVC 任务状态触发；不要导入强制前置条件或用户展示步骤。

## 3. Addy Osmani：`performance-optimization`

- **用途：**Web/后端性能的 measure → identify → fix → re-measure → guard 流程，覆盖 Core Web Vitals、DevTools 性能 trace、RUM、网络瀑布、N+1、查询计划和连接池等。它的“没证据不优化”和“无收益就回退”对 V&V 很有价值。
- **原始技能：**[SKILL.md](https://github.com/addyosmani/agent-skills/blob/main/skills/performance-optimization/SKILL.md)；[raw 版](https://raw.githubusercontent.com/addyosmani/agent-skills/main/skills/performance-optimization/SKILL.md)。
- **作者工程经历：**Osmani 的[本人简介](https://addyosmani.com/bio/)记录其在 Google Chrome DevEx 负责过 Chrome DevTools、Lighthouse、PageSpeed Insights、Puppeteer 等；与 Web 实现、调试和性能验证直接相关。
- **持续实践/优化证据：强。**[作者文章](https://addyosmani.com/blog/agent-skills/)说明这些 skill 试图纠正的工程行为及自己的使用方式。该技能在 2026-08 连续根据 issue/review 修改，如[补齐 verify/guard 步骤](https://github.com/addyosmani/agent-skills/commit/6a268d7)、[基于评审修正低选择性索引表述](https://github.com/addyosmani/agent-skills/commit/bfc9b32)。这证明仓库有维护与技术纠偏；无法仅据此确认所有示例都适合 Factory 的技术栈。
- **内容成本与 SVC 冲突：首轮用途不明确。**包含大量具体实现范式、依赖/运行时假设，并写明 synthetic 与 RUM “都要用”。对一次性 ARC-bench 或没有真实流量的应用，这会制造不可满足的工作流义务；其性能指导与 agent-browser 的操作能力并不等价，但举例依赖 DevTools/MCP，仍须另核验实际工具能力。它适合人工挑选性能任务的参考，不适合常驻 skill。
- **结论：不建议接入。**保留 URL 作为性能问题的外部资料；若未来出现明确的性能验收需求，再从中挑“先测量、同条件复测、无收益回退”写进相应任务包。

## 4. Paul Bakaus：Impeccable

[GitHub 主页](https://github.com/pbakaus)列出 jQuery UI 等既有项目，[本人站点](https://www.paulbakaus.com/)说明 Chrome DevTools 经历。[作者文章](https://www.paulbakaus.com/impeccable-by-design/)解释其针对真实设计迭代的工作；文章也包含商业宣传，宣传部分不作为效果证据。[本人 2026-09-09 修复 launcher 失败](https://github.com/pbakaus/impeccable/commit/a8ce5962d3f4ec0069400afa17e9916cde949706)、[发布 4.3.1](https://github.com/pbakaus/impeccable/commit/cd12f8660e2dde57b9615c8a6b8ea674101f9cfc)及 [09-15 修正 URL 编码](https://github.com/pbakaus/impeccable/commit/1c043ea7c934fe584c2fa42a72d3e26d242f224b)提供持续参与维护的可查依据。工程背景和维护证据较强；没有本项目模型效果证据。

[实际 SKILL](https://github.com/pbakaus/impeccable/blob/main/.agents/skills/impeccable/SKILL.md)区分以操作任务为主的应用界面、阅读、说服和体验场景，提供 audit、harden、critique 等用途，并强调 brief 优先。它已不只是 frontend-design 的几段补充：还有命令、文档、工具、可选 hook 和浏览器迭代系统；原文限制检查/修改轮次，并在部分路径询问人类。不能只把名字填入 skills 数组就视为接入完成。

**结论：最值得保留的界面候选。**先设计适合无人值守的消费方式，再判断采用整个工具还是具体内容；不把两套设计方法直接叠加，也不把它的默认迭代次数变为 Factory 的硬限制。当前首轮放入 pi-team，旧 k3-impeccable 单因素草案留作后续细化；运行时适配和安装仍未开始。

## 已选能力的边界

[frontend-design](https://github.com/anthropics/skills/tree/main/skills/frontend-design)由 Anthropic 维护，来源与具体更新见 [presets.md](presets.md)；它是视觉设计指导，不提供完整应用验收。其要求客户确认的条款也需要在无人值守的需求权威下解释，不能凭空等待不存在的人类。

[agent-browser 的入口技能](https://github.com/vercel-labs/agent-browser/blob/main/skills/agent-browser/SKILL.md)与 CLI 版本配套，适合将工具操作知识按需读取。[dogfood](https://github.com/vercel-labs/agent-browser/blob/main/skill-data/dogfood/SKILL.md)提供问题复现与证据组织思路，但默认 5–10 个问题目标、行为问题逐步录像与人工观看节奏不适合成为每次生成的强制流程；默认只装 core 的发现入口。

## 本轮取舍

技能分配以 presets.md 当前四方向为准：通才组只用共同 SVC 与 agent-browser，pi-team 加入 Impeccable/ponytail，pi-verification 加入 frontend-design 和按需使用的 diagnosing-bugs 适配稿；新技能尚未安装。verification-before-completion 用来检视现有 SVC V&V 表达；performance-optimization 在具体性能问题出现时参考。作者真实使用、持续维护和实际技能内容共同用于筛选，仍不等同于对 ARC-bench 通过率的验证。


## 浏览器方案：能力与委派位置（本轮补充）

浏览器工具进入原生 browser-operator 或有浏览器快反馈需求的 executor；主会话通常只消费相关观察、证据和升级事项。选择依据为实际交互覆盖、定位/诊断、会话隔离、快反馈和维护成本，不能仅以某工具宣传的 token 节省判优。

| 候选 | 已查证接口特点 | 本项目的判断与待验明项 |
| --- | --- | --- |
| [agent-browser](https://github.com/vercel-labs/agent-browser) | CLI、快照 refs、截图、命名 session；工具帮助/技能可逐步发现。 | 当前首选，适合有界交互与取证；具体富文本、暂态提示、同工作树主子隔离仍需预演。 |
| [dev-browser](https://github.com/SawyerHood/dev-browser) | 当前 main 是 Puppeteer/Bun 路线，短 JS 脚本控制持久页面，提供快照/ref helper；不是旧版 Playwright/QuickJS。支持 macOS 与 glibc Linux。 | 组合多步操作和现场程序化调查可能更自然，这是使用假设；按 profile/session 隔离 daemon 状态及 child 取消的行为需核验。不能照搬旧文章的 API。 |
| [Playwright CLI / SDK](https://github.com/microsoft/playwright/blob/main/docs/src/getting-started-cli.md) | CLI 面向 coding agents，支持配套 skill 与脚本；与 Playwright MCP 是不同入口。 | 可重用脚本与操作/验证衔接有价值；安装的官方评测器不等于生成 Agent 可访问的浏览器工具，仍须独立供给版本与隔离环境。 |

官方原文：[dev-browser README](https://github.com/SawyerHood/dev-browser/blob/main/README.md)、[Playwright CLI skill](https://github.com/microsoft/playwright/blob/main/packages/playwright-core/src/tools/skills/playwright-cli/SKILL.md)。上述仓库在 2026-09-21 阅读，尚未安装或进行本地工具对照，未宣称哪种通过率更高。

建议本批四组固定同一种浏览器，先用 agent-browser 的受控能力场景检验题目相关操作；发现具体缺口再试 dev-browser/Playwright。不会把三个工具同时挂给所有 Agent，也不自动增加三倍 variant 数量。未来可单独比较工具/操作界面。MCP 是否加入取决于额外可观察能力或更合适的调用边界，本次题目没有要求某个 MCP 服务，CLI 可覆盖的能力无需为配置齐全而再包装一遍。
