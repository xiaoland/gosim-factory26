# Factory26 文档索引

本页是项目知识入口。产品承诺、运行方式和实验结果分别维护在各自的归属文档中；SVC 方法通过项目本地 CLI 查询，不复制 Corpus 到仓库。

| 内容 | 入口 | 维护范围 |
| --- | --- | --- |
| 产品说明 | [PRD](prd/index.md) | 目的、角色、能力范围和实验规则 |
| 本地运行 | [Deployment](deployment/index.md) | 环境、密钥、执行、恢复和证据查询 |
| 开发流程 | [AGENTS.md](../AGENTS.md) | 开发入口、更新约定和任务包保留规则 |
| 可执行事实 | [Factory 共同配置](../variants/factory/config.json)、[运行器](../scripts/factory.py)、[检查](../tests/test_factory.py) | Braid + SVC、可选 Pi/Codex backend，以及可机械验证的边界 |
| 四组实验 | [SVC / braid 比较](../reports/2026-09-20-harness-matrix.md) | 首轮四组的状态、条件、结果和限制 |
| 本地对象接入实验 | [Braid / SVC 检查点](../reports/2026-09-21-braid-svc-checkpoint.md) | 真实接入验证、Keep 失败与主动中断；没有新四组分数 |
| 实验反馈设施 | [无模型验收](../reports/2026-09-21-experiment-feedback.md) | 全流程终态、低噪诊断与分层协作的验证范围 |
| 恢复后真实实验 | [Pi + SVC / Keep](../reports/2026-09-21-pi-svc-keep.md) | 当前接入首次完整 32 项成绩与失败分布 |
| 参赛 P0 验收 | [制品与无模型验收](../reports/2026-09-21-competition-p0.md) | 两种 backend 的 ZIP、隔离与交付检查，以及尚未验证的生产边界 |
| 实验结论 | [首次 Pi / Keep 基线](../reports/2026-09-20-pi-keep-baseline.md) | 固定运行条件下的结果，不是当前产品承诺 |
| 开发闭环调查 | [诊断、协议桥与 Playground](../reports/2026-09-20-development-loop.md) | 改进证据、候选源码检查与云端探针范围 |
| API 与并发实测 | [Playground / WSL](../reports/2026-09-20-playground-concurrency.md) | API 实际执行、云端环境与独立任务并发结果 |
| 历史输入 | [原始 handoff](handoff-original.md) | 未改写的设计输入，含尚未采用的建议 |

## 更新方式

先修改内容的归属文档，再调整导航。PRD 维护做什么和为什么，Deployment 维护如何运行；实际参数和版本优先引用源码与配置，实验数据引用对应报告，避免并行维护副本。

生成运行器、braid 本地入口和远程评测的使用与约束集中在 Deployment；精确协议字段及终态检查由源码和回归检查维护。不建立空的 Product TDD、Unit TDD 模板；当新的设计约定需要独立维护时，再按 SVC 的准入规则增加文档。

任务进行中的假设、计划和状态放在任务包中，不写成长期事实。历史 handoff、实验报告和原始日志不因文档整理而被改写。

## SVC 入口

项目配置为 [svc.json](../svc.json)。使用 `.venv/bin/svc status --json` 查看配置、Corpus baseline 和集成状态，使用 `.venv/bin/svc lookup --path specs/` 查询文档归属规则。下面生成块内的 `svc` 同样指项目本地 CLI；生成块由 `svc init` 维护，其外内容由项目维护。

<!-- svc:begin navigation sha256=7f7f63d0b8989624f57bd21b82b2ac2d05e4445edfd5af4bc3742996f0754bda -->
## SVC Corpus

Use `svc lookup` when packaged Sustainable Vibe Coding Corpus guidance is relevant, and discover its browse/search/read grammar through `svc lookup --help`. Project documentation outside this marked block remains Consumer-owned.
<!-- svc:end navigation -->
