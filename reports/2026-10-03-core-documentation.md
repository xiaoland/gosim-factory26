# 2026-10-03 核心文档与导航整理

本轮接续开发体验调查，按用户要求把范围转向核心文档、组件本地说明和目录导航，没有整理任务 packet，也没有启动实验或改动运行控制。整理基于当时工作树及实际 CLI/源码；它不证明运行耗时或模型 token 已经下降。

原先的主要成本不是缺少总索引，而是同一长页同时承担当前协议、历史操作、组件接口和瞬态状态。典型问题包括实验首页把九月底登记标成“当前”、Console 手册与 README 循环指路、旧暂停门闩与新控制门控混用、系统盘部署路径、失效启动方式，以及监控消费者说明沿用过期的模型禁令。

| 内容 | 整理后的归属 |
| --- | --- |
| 读者按主题找方法 | [文档入口](../docs/index.md)，工作与报告目录独立导航。 |
| 定义、执行、制品合同 | [Lab](../lab/README.md)及 `lab/exp/` 本地主题文档；技术说明维护跨组件责任。 |
| 工具准备、材料、Linux 装配、I13 接线 | `scripts/`、`harness/`、`submission/`、`variants/pi-braid-i13/` 的本地 README。 |
| Console 服务操作与界面读取 | [运行手册](../docs/deployment/console.md)和[组件合同](../braid-console/docs/contracts.md)，旧部署与暂停规则单独归档。 |
| 旧运行协议、实验登记、初始输入 | [历史协议](../docs/deployment/history/README.md)、[历史实验](../experiments/archive/README.md)、`docs/archive/initial-handoff.md`。 |
| 本机路径与发现方法 | 根 `AGENTS.local.md`，Git 忽略，不保存运行状态或授权。 |

还清理了根目录只剩空目录的 `skills/`、`patches/` 树；有效技能仍在 `harness/skills/`，npm 补丁仍在 `harness/npm/patches/`。独立 variant 与冻结执行器的代码路径和身份没有为文档整理而迁移。

九个主要入口的正文合计从约 222 KB 降至 56 KB，减少约 75%；这是阅读载荷的度量，迁出的必要内容仍在对应权威页或历史协议中。原始 handoff 按字节保留。检查覆盖 59 份核心文档、517 个相对链接及 67 个外部指入链接，文件和锚点均可达；实际 CLI 帮助、schema 与来源导入分支已定向核对，diff 格式检查通过。

基线、迁移回执和检查明细位于 `runs/developer-experience/core-docs-20261003/`，由 Git 忽略。验证没有运行 Factory/Braid 测试、包 smoke、模型或 benchmark；现行能力中尚缺受管理 Console accessor 创建 CLI，手册明确使用已有合法 accessor、原容器只读或归档接入，没有杜撰创建步骤。
