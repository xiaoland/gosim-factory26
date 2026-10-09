# Factory 内部子 Agent 的工作方法

公开树保留本任务的设计、判断和验证摘要；cells 中的生成 JSON、宿主回放和分析脚本已移除，可从 Git 历史按提交恢复。

当前阶段：实际运行使用复审与已授权热修复。

## 2026-09-28：实际运行使用复审
用户要求完整观察先前官网运行，以及本地 DeepSeek 两题的历史及当前恢复窗、已取消 Qwen/MiniMax 两题中的原生子代理使用，区分 Braid 成员、主会话重建与原生子会话。
官网 GitHub 由 live_deep_diagnosis 取证，官网 Sheet 由 browser_guidance_apply 取证，分别写 cells/hosted-github-usage.md 与 cells/hosted-sheet-usage.md；主 Agent 整合覆盖清单及跨环境比较。
usage-map 已纳入上一批官网生成来源链和本地对照；更早独立官网运行仍列为未逐一核对，不称全历史穷尽。缺快照或原生记录标作未知，不算未使用。
用户已授权：“没问题，都可以推进、落地（相当于复核方案并且开工）；特别是 sub-agent 几乎不可用、混淆的问题，要重视”。
当前调查由 live_deep_diagnosis 负责证据整合，主 Agent 负责根因判断与修正集成。
完整视图按委派输入、实际角色/模型、独立上下文、返回、父会话消费与结果组织；不以次数或 token 增长代替收益。
完成的材料见[跨窗口使用视图](cells/usage-map.md)与[原生入口调查](cells/native-discovery.md)；此前截面见 [初步使用分析](../experiment-infrastructure/cells/subagent-usage.md)。
已确认 vision 只读任务被上游语义写入分类误拒、PBB 后台任务被误交给 Pi 子代理等待工具；最小修正边界见上述材料。

## 新增审查：SVC 的委派与角色方法

用户已认可四项改进方向；在细化或修改 Corpus 前，先独立完整整理原始讨论 [Sub-agent 悖论解析](https://chatgpt.com/share/6aba0cb0-28e4-83e8-ae51-54d3cc2a521f)，再复核方法。该来源整理由 browser_guidance_apply 完成，见 [原始讨论整理与复核](cells/subagent-paradox-source.md)：可见五条消息已完整分段阅读，分享前史及末条提案的后续用户确认不可见。报告区分用户聚焦、双方收敛与 assistant 未决提案，并指出结果消费需兼顾命题可检性，不能只按信息/产物二分；不以来源替既有方案背书。整理只改本任务包，不授权 Corpus、实现或运行变更。

用户要求进一步审查SVC的sub-agent方法。当前仅调查与方案，不修改Corpus；与08热修及token分析分开。
主审查见 [SVC方法复审](cells/svc-method-review.md)，独立运行接缝复核见 cells/svc-runtime-seam-review.md。
目标是让委派形成有用工作边界并减少主会话负担；不以角色/调用数为目标，不把原生接口故障变成Corpus禁令。

## 前轮实施记录

以下为前轮实施及其当时的验收边界。
用户授权原话：“不进行验收，我们进行几轮迭代之后，再进行一次实验；你可以开工。”
本轮完成既定源码与文档修改；构建、打包和实验验收留待后续统一安排。
用户要求检查 advisor、executor、explorer、browser-operator 的 SOP、专业知识、模型及上下文继承配置。
已按用户复核修正方案，并处理固定角色流水线及审查发现的同类耦合。
用户回复“很好，这个方案没问题。”批准了上一轮呈现的设计、技术与验收方案。
实施顺序、文件责任及后续候选实验见 [实施计划](plan.md)。设计基线提交为 a6d5276；用户于本轮授权提交实现，验收转入新基线任务。
既有 Braid 两题验收已完成，分别由独立 Agent 分析；原冻结制品不变。

## 问题与方向

明确输入、权限与输出只建立了委派接口；子 Agent 还需要能在局部完成判断、行动、反馈和修正的方法。
改进目标是提高一次委派可直接采用的产出，降低父 Agent 补发上下文、转述工具输出及重新做一遍工作的成本。
角色方法应帮助 LLM 作判断，不将所有任务编排成固定的 explorer → advisor → executor → browser 流水线。

[配置调查](findings.md)区分 Hackathon 四角色与 Braid 五角色的实际配置，记录参数语义及尚未核实的行为。
[修正后的设计与耦合审查](design.md)落实用户两项决定：这些角色明确不继承主会话历史；专业性指角色工作 SOP 和按场景选择工具的知识，不扩大为领域工程职责。
用户还要求处理固定角色流水线，并审查同类耦合；审查已定位七项问题，包含未关闭 Pi 内建角色、基础提示装配差异与技能二选一。
具体复核材料为 [角色正文与来源](roles.md)、[技术接线](technical.md)、[验收方案](verification.md)。
已更新 rg、ast-grep 与通过 MCPorter 调用 Context7/Exa 的构建及运行接线；独立工具预演已完成 scratch 安装、实际源码结构搜索，以及 Context7/Exa 文档查询。
两项独立预演已完成，结果见 [原生上下文接线](rehearsal-context.md) 和 [工具执行](rehearsal-tools.md)。
已收敛 Pi 默认值与父调用的区别、Codex 原生角色发现、SVC 章节直接装载，以及 ast-grep 原生 ELF 与 MCPorter Node 入口的区别。
目标 Docker 构建和真实模型生效情况留待后续统一验收；当前没有相应结论。
保持现有 base/SVC 对照含义：通用 SVC 方法归 SVC，角色专项知识与工具操作方法独立；不能将 SVC 正文复制进 base 组使对照失效。

本任务不新增 Factory、基础设施或 Corpus 测试，不自动授权新模型运行。
实施前后验收应基于实际生成应用与子会话记录，分别检查配置是否生效、局部工作是否完成以及父会话是否能采用结果；角色被调用或输出更长不能单独证明收益。

## 本轮实现与恢复点

Hackathon 四角色分开 description/正文，SVC 章节从冻结 skill 直接装入角色指令；Base 不装入 SVC。
Pi 明确 fresh、append、技能选择和关闭内建角色，父委派指引明确无历史；Codex 保持原生角色目录与 spawn 参数语义。
四个 Braid variant 的六套成员同步装入方法和工具指引，移除 specialist 的失败前置条件；vision、模型配方、Braid 核心及 SVC 正文不变。
工具 worker 完成依赖锁、Linux 构建接线和探索 skill；主 Agent 完成角色、各 variant、打包选择及文档整合。原计划的第二实现委派遇到 Agent 数量上限，由主 Agent 直接完成。
MCP 配置放在技能标准资源目录 `assets/mcporter.json`，沿用既有 copy_skill 复制规则。
本轮未运行构建、打包、模型、benchmark 或验收，未新增测试；新工具尚未进入旧 runtime/ZIP。
下次统一实验前从当前源码构建资源并冻结新包，再检查上下文、工具使用和应用评分；本页不自动授权此前建议的八 run 矩阵。


## 当前复审：advisor 与 left-shift

用户认为主要问题仍是 left-shift 不足，要求检查过去运行的 advisor 使用，并重新考虑 K2.7 根 variant 的必要性。
Astra worker `token_final_astra` 承接 [advisor 审计](cells/advisor-left-shift-audit.md)：按配置/发现/调用尝试/真实子会话/返回/父消费分层，覆盖可取得的官网与本地来源链，逐项标注缺失窗口。
主 Astra 复核角色、SVC 设计方法与实际高影响决策的接线；重点判断在根种子折衷、跨模块契约、验收判据形成之前是否使用了独立判断，而不是提高调用次数。
本次仅调查与方案，不修改角色/技能/源码，不调用模型实验。
K2.7 根 variant 保留已准备源码，但暂不推进打包/实验；“可能没必要”不是删除指令，待本轮证据复核决定其取舍。

## Advisor 前置判断：本次开工

用户授权：“可以，而且 advisor 不遵循 SVC sub-agents 的那套收益计算方法”。
实施范围：SVC 将独立咨询从普通委派收益计算中分开，设计入口提供导航；活动 pi-braid 及现有 Flash 对照的原生主指令与 advisor 角色同步说明时机、输入和消费。
不修改 Braid 调度、模型、已有运行；K2.7 候选继续暂存。直接复核内容和实际技能分发链接，不编写/运行 Corpus 或 Factory 测试；实际采用与决策收益等待下一次获授权运行。无提交授权。

本次指引已应用；范围和验证边界见 [已批准取舍](cells/advisor-decision.md#应用与验证范围)。实际采用尚未实验验证。

迭代 10 的 explorer/executor/advisor 原始使用链与最小落点见 [三角色使用审计](cells/iteration10-role-audit.md)，包含 Braid 已指派工作被再次用 Pi 启动的公开动作证据，以及当前已落地但尚缺真实采用的修正。
