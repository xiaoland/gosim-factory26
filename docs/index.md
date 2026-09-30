# Factory26 文档与任务入口

当前说明回答项目如何工作；task packet 保存进行中的问题与决定；报告保留特定条件下观察到的结果。
历史报告和原始 handoff 不作为当前操作规范。

## 当前说明

| 要了解什么 | 入口 |
| --- | --- |
| 仓库地图与协作约定 | [AGENTS.md](../AGENTS.md) |
| 产品目标、协作模型与实验规则 | [PRD](prd/index.md) |
| 组件责任、调用关系、交付与终态语义 | [Product TDD](product-tdd/index.md) |
| 修改角色/技能、开发依赖与源码运行 | [CONTRIBUTING](../CONTRIBUTING.md) |
| 打包、执行、证据查询与恢复 | [Deployment](deployment/index.md) |
| 外部命令实验、OTLP 与控制 CLI 契约 | [Lab](../lab/README.md) |
| 实验登记、运行命名与配方 | [实验导航](../experiments/README.md) |
| Braid OTLP、会话网站与故障定位 | [Braid 诊断运行手册](deployment/braid-diagnostics.md) |
| 当前 Lite 两阶段本地矩阵配方 | [pi-braid Lite](../experiments/pi-braid-lite/README.md) |

参数与模型值从各 [variant](../variants/) 和实际制品读取，文档解释意义与修改关系，不维护第二份配置表。
当前活动实现与归档状态见 [Variant 索引](../variants/README.md)；本会话的已落地、待验证和暂停事项见 [迭代总览树](../tasks/iteration-map.md)。
当前自费回放与修复版完整实验见 [预算与交付](../tasks/competition-budget/packet.md)；旧正式运行记录保留历史身份，不构成新参赛授权。
当前支持与设计意图分开写；更新时改写受影响正文，不靠新增声明覆盖过期推荐。
局部实现理由归代码旁，跨组件约定归技术说明，操作命令归开发/运行说明。
不创建空模板或针对文档内容的测试。

## 接续任务

下表按主题导航，不复制各 packet 的授权、进度、PID 或评分。
打开对应 packet 确认当前事项；远端状态仍以本次观测和原始 journal 为准。

| 主题 | 入口 |
| --- | --- |
| 当前主线、授权与工作单元 | [迭代12 packet](../tasks/iteration12/packet.md)：从零运行已暂停，保留工作连续性修复及人工介入console；[I11恢复与最终评分](../tasks/iteration11/runtime-stalls/packet.md)，前序[迭代11](../tasks/iteration11/packet.md)及[迭代10](../tasks/iteration10/packet.md)保留原始设计和运行证据 |
| 当前V&V改写与后续协作改进 | [迭代13 packet](../tasks/iteration13/packet.md)：V&V元理论、内容与导航改写已开工；G01及角色接线、Console整体暂停/恢复分别保留待办状态 |
| 实时查看与介入I12 Issue/PR | [协作console](deployment/console.md)，写入复用Braid CLI；人工介入是本轮研究条件 |
| 开发体验、文档系统与独立 variant 演化 | [DX](../tasks/developer-experience/packet.md)；[独立 variant 前序材料](../tasks/independent-variants/packet.md) |
| Variant、实验与运行的命名整理 | [命名方案任务](../tasks/variant-experiment-naming/packet.md)（实现与文档已完成，证据及验证边界见 packet） |
| 参赛 SVC 方法与 skill 接线 | [Corpus](../tasks/svc-corpus-review/packet.md)、[skill](../tasks/svc-skill-integration/packet.md) |
| Hackathon 能力选型与 SVC 技能路由 | [技能与工具设计](../tasks/hackathon-capabilities/packet.md)；[既有 Lite 基线](../tasks/hackathon-team-baseline/packet.md) |
| Braid 工作项上下文、CLI 易用性与 Agent 指派 | [Braid 改进](../tasks/braid-usability/packet.md) |
| 官方与本地实验的组织及恢复 | [双比赛官网记录](../tasks/dual-bench-hosted/packet.md)、[raw 本地基线](../tasks/raw-core-local-baseline/packet.md) |
| 官网中断恢复、低频监控与耗时改进 | [实验设施](../tasks/experiment-infrastructure/packet.md) |
| Braid 独立架构与功能审查 | [架构审查](../tasks/braid-architecture-audit/packet.md) |
| 本轮 GitHub / Sheet 得分根因 | [GitHub](../tasks/github-score-diagnosis/packet.md)、[Sheet](../tasks/sheet-score-diagnosis/packet.md) |
| 得分与 Agent 过程分析 | [官网结果](../tasks/official-results/packet.md)、[本地过程](../tasks/local-run-analysis/packet.md) |
| 协作方法的前序调查 | [会话分析](../tasks/development-loop-review/packet.md) |

[早期 multi-agent 接入](../tasks/multi-agent-integration/packet.md)、[迭代吞吐](../tasks/iteration-throughput/packet.md)保存其阶段的方案与证据，不自动授权新运行。
[agent-profile-presets](../tasks/agent-profile-presets/packet.md)已指向接入任务，[SVC CLI 裁减](../tasks/svc-cli-simplification/packet.md)已指向 skill 接线；沿后继入口接续，不启动旧计划。
其余历史任务材料保留在 [tasks](../tasks/)，未核实完成条件时不仅依据文件日期关闭任务。

## 实验报告与历史材料

| 主题 | 报告 |
| --- | --- |
| Braid OTLP 与会话重建 | [2026-09-24 接入及真实归档验收](../reports/2026-09-24-braid-otlp.md) |
| 官网完整结果与限制 | [2026-09-23 官网总览](../reports/2026-09-23-official-results.md) |
| 本地应用得分的过程原因 | [2026-09-23 Agent 过程分析](../reports/2026-09-23-local-agent-process.md) |
| 发布版本地运行设施的阶段记录 | [2026-09-23 本地实验设施](../reports/2026-09-23-local-experiment-infrastructure.md) |
| 首轮组合比较 | [2026-09-20 四组结果](../reports/2026-09-20-harness-matrix.md)、[原始 Pi 基线](../reports/2026-09-20-pi-keep-baseline.md) |
| 早期接入与平台适配 | [Braid/SVC 检查点](../reports/2026-09-21-braid-svc-checkpoint.md)、[P0 阶段报告](../reports/2026-09-21-competition-p0.md)、[Pi/SVC Keep](../reports/2026-09-21-pi-svc-keep.md) |
| 诊断与接口的前序调查 | [开发闭环](../reports/2026-09-20-development-loop.md)、[并发与 API](../reports/2026-09-20-playground-concurrency.md)、[旧反馈设施](../reports/2026-09-21-experiment-feedback.md) |
| 最初输入 | [原始 handoff](handoff-original.md) |

这些报告中的测试、沙箱、模型或平台可用性描述是当时事实，不是当前方法要求。
原始证据位于各报告明确指向的运行目录，通常被 Git 忽略，不随源码自动分发。

## 开发侧 SVC

[svc.json](../svc.json)声明开发 Corpus baseline，`.venv/bin/svc status --json`显示本地安装与集成状态，不证明工作流程有效或参赛方法已通过实验。
文档归属按需查询 `.venv/bin/svc lookup --path specs/`；任务包信息组织查询 `task-packet/`；局部设计与注释原则查询 `taste/implementation/`。
这些是开发侧方法，参赛侧裁减 Corpus 与 skill 接线另由对应任务和实际 variant 维护。
生成块由开发 SVC 管理，其中 `svc` 指项目 `.venv/bin/svc`。

<!-- svc:begin navigation sha256=7f7f63d0b8989624f57bd21b82b2ac2d05e4445edfd5af4bc3742996f0754bda -->
## SVC Corpus

Use `svc lookup` when packaged Sustainable Vibe Coding Corpus guidance is relevant, and discover its browse/search/read grammar through `svc lookup --help`. Project documentation outside this marked block remains Consumer-owned.
<!-- svc:end navigation -->

- [Braid 产品加固与 Flash Team](../tasks/braid-product-hardening/packet.md)：授权修复、产品审查、WSL 两题实验。
