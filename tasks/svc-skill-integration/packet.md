# SVC 作为 Agent Skill 接入

## 当前状态

2026-09-24，用户明确批准 SVC 自身实现为完整 Agent Skill，并要求优化导航。
本轮已将入口及正文归到 `sources/svc/SKILL.md`、`references/`、`assets/`，Factory 只保留源码目录链接。
四个 variant 和打包入口移除了 `--svc-corpus` 及二次装配，使用通用 skill 文件复制。
具体边界、导航选择和操作结果见 [完整 skill 迁移](native-skill.md)。

SVC 源仓库已按用户授权提交为 `b5a0fb8`；用户随后确认允许拆分提交必要前序实现。
Factory 前序独立 variant/DX 实现已提交为 `7bb2c60`，完整 skill 接线与本记录单独提交；其他实验、诊断和旧路径清理不纳入。
未启动模型/bench，也未运行 Factory 或 Corpus 测试。
开发侧完整 SVC、模型配方、Agent 角色和冻结制品保持原有状态。
Corpus 增强与此前 skill 接线的真实运行验收仍开放，不能用目录迁移或材料分发代替行为证据。

## 历史实施与验收

[初次接线设计](design.md)、[当时实施记录](implementation.md) 描述旧包装式 skill、Pi/Codex 读取调查和当时 ZIP。
其中的共同 profile resolver、旧测试入口及安装说明已由 DX 和本轮迁移替代，不是当前运行方法。
当时真实模型读取遇到 429，未取得完整技能使用证据；该状态只是历史观察，不代表当前服务可用性。
当前生成、打包和依赖恢复方式见根 CONTRIBUTING 与运行文档。
