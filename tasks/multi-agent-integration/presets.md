# Agent-profile preset：先粗筛，再细化

本页维护 multi-agent 接入任务中的四种装配组合，任务状态与实施责任归 [主入口](packet.md)和各 Cell。用户已选择 ARC-Bench-Lite，并认可下面四种大差异方向，先粗筛再逐步缩小范围。上一版六份 JSON 降为后续细化素材，不能作为当前待执行批次。四种方向尚未接入或运行，技术主体已认可；当前配置归属、浏览器委派和 V&V 范围按用户纠正更新，详见 technical.md。

## 当前首轮方向

共同保留 Braid + SVC、Issue/PR 职责分离、按 profile ID 指派和需求优先。variant/preset 仅归 Factory，Braid 只消费普通 profiles。浏览器首选 agent-browser，也保留 dev-browser/Playwright 的工具替换空间；操作默认由原生 browser-operator 或 executor 承担。区别是可用的配置与工作指导，不是强制 Agent 分解、规定角色调用顺序或由 harness 决定何时验收。profile 数量不等于 Braid Agent 数量，同一通才 profile 可以承接多个 Issue/PR 会话。

| 候选 | 核心与 Braid profiles | 模型和原生子代理 | Skill／方法侧重点 | 与其他方向的实质差异 |
| --- | --- | --- | --- | --- |
| pi-generalist | Pi；一份可承接 Issue/PR 的 generalist profile | 主模型及 explorer/executor/browser-operator 均用 Kimi K3；无 reviewer | 固定 SVC + 浏览器子代理能力；首轮不叠加额外设计/编码方法 skill | 用通用能力承担需求到交付，工作项可以复用同一 profile，少做专长分工。 |
| pi-team | Pi；coordinator、ui-engineer、app-engineer 三份 profile | K3 协调；GLM 5.3 Flash 界面；K2.7 Code 完整功能；explorer/browser-operator K3、executor 用所属实施模型；无 reviewer | UI 提供 Impeccable，app 提供 ponytail；共享 SVC、agent-browser | 同时探索异构模型、专长能力和 Braid 级协作，是完整组合比较，不对单因素归因。 |
| codex-generalist | Codex app-server；与 pi-generalist 相同的 generalist 定义 | 主模型及 explorer/executor/browser-operator 均用 K3；无 reviewer，具体 app-server 配置入口需预演 | 与 pi-generalist 相同的技能集合 | 比较核心的工具执行、上下文和原生子代理行为；Braid + SVC 仍是完整 harness 的共同基础。 |
| pi-verification | Pi；coordinator K3、app-engineer K2.7 Code | 除 explorer/executor、共同 browser-operator 外，独有一个可选 K3/high reviewer；不设 contract-reviewer | 各组共同 V&V 为方法权威；frontend-design、浏览器子代理；顽固故障可按需用适配后的 diagnosing-bugs | 探索额外语义复核能否发现需求理解、Oracle 或证据覆盖盲点；不替代确定性检查，也不要求每次调用或批准。 |

主会话不默认加载浏览器操作 skill，只提供简短委派导航；executor 可直接闭合实现与浏览器反馈，operator 承担有界观察/复现，简单操作不设硬禁令。各角色具体配置以 [technical.md](technical.md) 为权威。除 V&V 外的 SVC Corpus 本批冻结，V&V 完成后四组使用同一版本。

前三组不配置专职 reviewer，仍由主 Agent/executor 完成必要 V&V；不通过改名或强制 explorer 承担审查来补回被删除的角色。pi-verification 的 reviewer 是否增加有用证据仍是待检验假设，本批多因素比较不能单独归因于它。

Reasoning 均以 high 为目标，逐模型实际支持仍需核验；MCP 目前均为空，浏览器通过 CLI 提供。额外技能、核心版本和子代理定义随组合冻结。Impeccable/diagnosing-bugs 的适配尚未完成，不把上表解释为可立即运行，也不照搬其人工等待、固定迭代次数或其他与本项目方法冲突的条款。

首轮比较的是整体效果。除 pi/codex 通才这对刻意保持其他条件相同外，其余方向同时改变多个因素；成绩不能证明单个模型、技能或角色带来了多少提升。保留少数有证据的方向后，才使用下面的细粒度配方定位贡献。若 Agent 没有实际使用某类能力，报告这一事实，不凭 preset 名称推断发生过专长协作或独立验收。

Braid 和 SVC 的语义职责、两个 Lite 任务、需求与测试版本、部署合同和外层资源条件固定；不把大差异误解为改变评分标准或给予某组更多题目信息。详细批次与报告边界见 [experiment-design.md](experiment-design.md)。

历史六配方及原生角色表已移到 [drafts/README.md](drafts/README.md)，仅用于后续细化，不参与本批。

## 浏览器与共同工具

采用用户建议的 [Vercel agent-browser](https://github.com/vercel-labs/agent-browser)，以 CLI 作为浏览器界面。在 browser-operator 和需要它的 executor 配置其[薄导航 skill](https://github.com/vercel-labs/agent-browser/blob/main/skills/agent-browser/SKILL.md)，详细用法由所固定 CLI 版本的 `agent-browser skills get core` 按需提供。Playwright MCP 和仅为它引入的 pi-mcp-adapter 已从所有草案移除。按 Lite/Web 实际需求检查，目前没有必须由 MCP 提供的外部服务，所以 MCP 配置为空。替代浏览器方案见 [skill-candidates.md](skill-candidates.md)，需求对应见 [requirements-fit.md](requirements-fit.md)。

每个 run 的物理会话及子会话使用独立 browser session 标识和状态目录；同工作树内并行会话也要区分，不能只按 worktree 命名。浏览器二进制预装并复用兼容缓存；两者不是一回事。git、svc、braid、项目构建/检查命令与临时 API 验收脚本继续提供。浏览器自检不访问官方评测器，不替代冻结后的 ARC-bench。

agent-browser 的 dogfood 不是默认工作流程：其原文要求行为问题逐步录像，并以 5–10 个问题为目标。这适合面向人的探索性报告，却不是按需求判断本轮交付是否完成的依据。当前只选 core 能力，是否调用专项技能由后续具体问题决定。

## Skill 来源与尚待验证的选择

frontend-design 来自 [Anthropic 官方 skills 仓库](https://github.com/anthropics/skills/tree/main/skills/frontend-design)，原始介绍为[官方技术文章](https://claude.com/blog/improving-frontend-design-through-skills)。它偏向视觉表达、排版、构图及自我审视，不能代替完整产品设计或功能验收。实际文件要求已有 brief 的视觉约束优先；对于复刻类任务必须尊重原要求，不能为了“独特”擅自重新设计。文件有 [2026-06-09 更新](https://github.com/anthropics/skills/commit/2235be7c60b551f5de82ade908fd3816455afcda)与 [2026-09-03 更新](https://github.com/anthropics/skills/commit/41bbe19d1a1a7eaab5e7bb9050a417e5c6cffc8f)，但维护和官方身份不证明对本项目模型有效。

ponytail 使用本机已有版本的固定快照，针对技术实现和复杂度审查。接入前需检查其实际激活、输出约束与 Issue/PR、SVC 方法的优先关系，不能只靠表中的用途标签声称已经隔离其影响。完整候选调查、作者实践和是否接入的判断见 [skill-candidates.md](skill-candidates.md)。当前 Impeccable 归 pi-team，适配后的 diagnosing-bugs 归 pi-verification；它们尚未完成消费侧适配或安装。

## 接入缺口

本地 Braid Request 仍只接收一个 profile，PiConfig 和 Profile 参数分离，Factory wrapper 仍禁用 skills/extensions。需要接通 catalog、直接 assignment、模型参数消费者、隔离的技能/扩展/浏览器装配，并验证切换/恢复、子会话边界与 run 可追溯性。当前实施责任与依赖见 [task-map.md](task-map.md)。本轮没有安装扩展、修改活动配置或启动 bench。
