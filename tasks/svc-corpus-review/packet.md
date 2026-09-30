# SVC Corpus 审查

目标：让 Factory 的无人值守 Agent 只加载完成 Web 应用 requirement 所需的 SVC 指引，同时让本项目开发与诊断继续使用完整 SVC。

当前入口：SVC已是 `sources/svc/skills/` 下七个独立技能。当前V&V元理论、内容与导航的进一步改写由 [I13](../iteration13/packet.md) 承接，并已获开工授权；本包保存早期精简和增强的决定与证据。
历史上参赛侧单技能用于早期实验，之后五技能拆分与接线由 [Hackathon 能力任务](../hackathon-capabilities/packet.md) 完成材料层面验收；这些形态不覆盖当前技能目录。
开发和 analysis 继续使用独立完整 SVC；两边的内容不会自动同步。

2026-09-24 的 [Corpus 增强](enhancement.md) 已完成正文改稿和编辑复核，原先的 corpus/ 路径由后续 [完整 skill 迁移](../svc-skill-integration/native-skill.md) 替换。
迁移同时清退 Factory 包装文件和 SVC 专用装配参数，并使常用方法从 SKILL.md 直接可达。
历史精简、增强记录保留当时路径和材料，不覆盖当前入口。

本包的早期实施已有正文和材料层面的结果，不把后续运行自动计作这些旧版本的独立效果验收。单技能时期的方法正文由历史 `harness/skills/svc` 快照保留，当前实施状态以I13及对应冻结材料为准。
评分实验沿用既有安排；独立 variant 与 DX 的完成也不替代 Corpus 和 skill 接线的行为验收。

- [Factory Corpus 的目录、行文和验收方案](agent-first-review.md)
- [本轮实施与非 bench 验收证据](implementation.md)
- [场景耦合审查](overfit-audit.md)
- [前一阶段通用 SVC 的 Design/Implementation 改稿](design.md)
