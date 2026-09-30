# Factory26

GOSIM Agentic Factory 2026 / ARC-Bench 的 Agent Harness 开发与实验仓库。Coding Agent 在这里开发 Harness，运行时 Agent 使用冻结材料接收需求并生成应用；生成与外部评测分别保存输入、执行身份和原始证据。

当前开发入口是 [pi-braid-i13](variants/pi-braid-i13/)，采用 Pi、Braid 和按需读取的 SVC 技能。I10、I11、I12 的独立实现、冻结包与运行证据保留原身份；具体用途见 [Variant 索引](variants/README.md)，当前问题、授权和未完成验收见 [I13 packet](tasks/iteration13/packet.md)。

| 要做什么 | 入口 |
| --- | --- |
| 理解产品目标与组件边界 | [PRD](docs/prd/index.md)、[技术说明](docs/product-tdd/index.md) |
| 准备工具、修改角色或技能 | [CONTRIBUTING](CONTRIBUTING.md) |
| 打包、运行、查询证据或恢复 | [运行说明](docs/deployment/index.md) |
| 接续任务与找历史结论 | [文档与任务索引](docs/index.md) |
| 确认协作、修改及实验授权 | [AGENTS.md](AGENTS.md) |

各 variant 自己维护生成流程与原生材料，公共支持模块不决定协作方法或模型配方。Braid 管理 Issue/PR、成员与讨论，SVC 提供独立方法材料，原生 Pi 内部子代理承担工作项内委派。当前实验使用自带 key 的 `self_funded`；冻结制品和旧实验记录不会因工作树更新而改变。

资料：[比赛官网](https://create.gosim.org/factory26/)、[ARC-Bench](https://www.arc-bench.com/competition)、[评测器](https://github.com/code-philia/arc-bench)、[SVC](https://github.com/xiaoland/svc)、[Braid](https://github.com/xiaoland/braid)。
