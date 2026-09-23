# 评测口径与并行批次设计

2026-09-21 核对 GOSIM 官网规则、已登录 ARC-bench 比赛列表与详情，以及本地活动配置和历史报告。本页记录实验设计；尚未开始本批模型调用，也不是正式初赛成绩报告。用户最新选择：先用 ARC-Bench-Lite，并先比较差异较大的组合，再逐步缩小范围。此前六任务、36 次生成的提议撤回。

## 口径纠正

| 范围 | 已核实的内容 | 本项目现状 |
| --- | --- | --- |
| 历史 Keep | 本地固定开源 revision 1eb018367bedd618d3b9ced406ce07fb423d4956，Keep 全部 32 项 | 已有多次完整单任务结果，不能叫完整 benchmark。 |
| 公开 Lite | 平台详情明确 Keep 32 项、BookStack 34 项，共 66 项；GOSIM 首页明确公开赛榜单不是正式初赛排名 | 本轮选定范围；尚未完成同一 harness 的完整 Lite。 |
| 公开 Web | 平台当前为 6 个任务、484 项，须同一 submission 覆盖所有任务才能得聚合成绩 | 本地未完成全六任务；本轮仅作测试发现，固定本地版实际为 478 项，与线上 484 项不同，不能混用。 |
| GOSIM 正式初赛 | 官网/规则写 9 月 24–30 日，GitHub + Spreadsheets 功能复刻，涉及 Actions、组织权限、审计、Rulesets；指标为 GUI 通过率、网关 Token、墙钟时间，权重待公布 | 当前可见比赛列表未找到对应正式题包；未核实正式需求、测试总数、评分权重与题包版本。不能以 Web/Lite 名字推断其等于初赛。 |

官方来源：[GOSIM 首页](https://create.gosim.org/factory26/)、[规则](https://create.gosim.org/factory26/rules)、[平台列表](https://arc-bench.com/competition)、[Lite 详情](https://arc-bench.com/competitions/arc-bench-lite)、[Web 详情](https://arc-bench.com/competitions/arc-bench-web)。这些页面通过浏览器读取；网页抓取器未能解析比赛页面。Web 详情的任务链接和测试数是明确内容；其中通用 How to compete 文案仍提到 GitHub-style/spreadsheet-style，不能用这段通用文案覆盖实际列出的六个任务。

平台详情当时显示 12306=138、BookStack=34、Ctrip=126、Keep=32、PrestaShop=87、Stack Overflow=67，共 484。固定本地 revision 的 README 列出 117、34、125、32、86、66，共 460；本轮进一步运行已安装 Playwright 的 `test --list --reporter=json`，实际发现 12306=135、BookStack=34、Ctrip=125、Keep=32、PrestaShop=86、Stack Overflow=66，共 478 项；没有执行测试、生成应用或调用模型。原始清单见 [benchmark-discovery.json](../../runs/agent-profile-presets/benchmark-discovery.json)，评测器工作树仍干净。README 的 12306 声明数与实际发现数不一致；本地发现与平台当前数也不同，不能仅用 README 作分母。正式比较必须固定 requirement 及测试版本、task ID 和实际用例身份，不能只记录总数。

历史依据：[首次基线](../../reports/2026-09-20-pi-keep-baseline.md)、[四组结果](../../reports/2026-09-20-harness-matrix.md)、[恢复后单任务](../../reports/2026-09-21-pi-svc-keep.md)。旧 shared-config 的额外 Keep 运行不属于本批 preset 矩阵，已从本地证据中移除，不能自动计作新 preset 的成绩。

## Preset 应服务的能力

此前两份配方主要是通用 Web 角色加视觉技能，没有从初赛目标推导足够完整的能力设计。现在以需求理解与长上下文、一致的领域实体/权限/状态、可靠持久化、复杂操作与错误状态、按规格实现 GUI、可重复自检为共同重点。Spreadsheets 的具体数据/计算/操作合同必须等题目确认，不能自行发明必须实现的公式、协作或导入能力。

首轮四个相距更远的方向见 [presets.md](presets.md)：Pi 通才、Pi 异构团队、Codex 通才、Pi 验证强化，产品方向已获用户认可。原六份草案成为后续细化素材。所有组合保留 Braid + SVC，单个工作项自行决定是否调用子代理或分解需求。优先通过率，同时记录 Token 和时长。

## 批次范围与可比性

用户已明确希望扩展 preset 并并行比较，原先只建议单个 preset 后停止的节奏据此改为预先约定的一批实验。实施前仍按既有约定复核具体技术与验收方案并完成预演，不把方向授权等同于尚不存在的装配已经可运行。

本轮范围已由用户选为 ARC-Bench-Lite：Keep 与 BookStack，两项合计 66。首轮建议四种组合各生成两项，共 4 × 2 = 8 个独立任务，平行执行一个固定批次。正式题包即使随后开放，也不自动替换本批题目；用户决定下一轮是否转向正式题包。Lite 用于快速筛选候选，不能把其结果外推为 GitHub/Spreadsheets 成绩。

本地固定版本测试发现的两项数量也为 32/34；数量相同不证明与线上要求、素材、用例身份和部署环境完全一致。执行前固定来源及版本，并明确是平台 Lite 还是同任务本地练习，不能只合计 66 就宣称线上分数。优先复用已有 runner、浏览器和 API 脚本；不为本轮另建评测框架。

方法上是由粗到细的离散搜索，不是用分数估算连续梯度。首轮比较完整组合，允许同时改变模型、专长配置和方法技能以获得有意义的差异；因此不能把成绩差异归因于其中一个因素。根据两项结果、实际用到的能力、失败模式和基础设施异常，推荐保留一至两个有希望的方向交用户复核，再围绕它们做小范围模型/技能/角色对照。若差距很小或明显受偶发失败影响，先建议重复验证而非立刻淘汰。成本消融仍留在质量收敛之后。

所有 variant 使用同一批需求素材、同一部署合同、依赖版本、评测器和资源条件；从干净工作区独立生成。跨 variant 不共享产出、任务答案或该批失败详情，避免后跑组合得到额外信息。完成生成并冻结后才运行官方评测。一个 task 一次生成；失败保留阶段和原因，不自动加修复重跑。每个组合使用同一配置完成整个 suite，中途修改代码、技能或模型须产生新实验身份。

报告先给逐任务结果与生成失败、基础设施失败、评测完成的区别，再给完整覆盖后的公开 suite 汇总。宏平均和总 passed/total 分开；不冒充尚未公布的正式计分权重。缺失任务不能记为已获得完整分数。单次每题仍只能作初步比较，不据细小差距声称稳定优胜。

## 并行和反馈

已实测 WSL 四个独立 Keep 评测任务，全部与参考逐项一致，吞吐约 3.91 倍；不能外推为四个复杂应用同时生成或 K3/GLM 长会话配额已验证。[并发报告](../../reports/2026-09-20-playground-concurrency.md)中的模型四路成功仅是 DeepSeek 短请求。

建议外层先同时生成两个 variant/task，冻结评测最多四个独立任务；每个评测仍保持官方单 worker。如果实际 CPU/内存和模型服务表现支持，再把生成提高到四个，而不是修改官方 Playwright workers。Braid agents 与原生子代理还会产生内部模型请求，所以外层两个生成不等于只有两个 API 请求；预演要验证总请求并发可观测、限流/排队可诊断，不能通过缩短正常 Agent 的时间/token 上限解决。

每个任务独立 workspace、HOME、服务端口、Braid 数据、浏览器 session 和报告目录；共享内容只包括只读工具/依赖缓存。批次开始前冻结配置和任务清单，新增批次记录只聚合现有 run/evaluation 证据，不造第二套日志数据库。终态由进程/事件唤醒观察者；仅无事件接口的远端后台采集从 180 秒间隔起，主 Agent 不反复轮询。

单项终态形成简报，批次结束统一比较后停止；本批预先排定的任务可以继续，但不自动开始下一轮或新增重跑。若出现配置串用、跨任务污染、系统性协议错误或资源不足，暂停尚未开始的任务并报告原因，不把同一基础设施错误复制到整个批次。

## 启动前需要补齐

具体技术和验收见 [technical.md](technical.md)、[verification.md](verification.md)，实施责任归 [task-map.md](task-map.md)及各 Cell，批次步骤归 [experiment-plan.md](experiment-plan.md)。多 profile/直接指派、Pi 参数唯一权威、原生能力隔离、manifest 和证据追溯仍需实际接通；模型接口、图像输入、任务资产、依赖缓存与失败回传由独立预演和受控场景验明。既有 Keep 验收仍用于相应基础设施回归，不能替代本批 suite 的完成条件。

本轮追加的控制条件：preset/variant 仅归 Factory；浏览器操作默认委派原生 operator/executor。四组使用同一浏览器实现作为初始条件，替代工具先做有界预演。SVC 仅 V&V 调整在本批前完成并固定，其余 Corpus 冻结；不在批次中修改。具体需求到能力映射见 [requirements-fit.md](requirements-fit.md)，不据 Lite 或 Web 抽查声称正式初赛完整适配。
