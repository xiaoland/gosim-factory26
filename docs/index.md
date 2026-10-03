# Factory26 文档入口

本页按读者要做的事选择权威说明。组件细节靠近源码，历史资料单独导航；当前问题、授权和进度仍由所属 packet 持有。

| 要做什么 | 先读哪里 | 需要细节时 |
| --- | --- | --- |
| 理解产品目标与协作模型 | [PRD](prd/index.md) | [Variant 实现索引](../variants/README.md)。 |
| 理解跨组件责任与生命周期 | [技术说明](product-tdd/index.md) | [资源与原生执行约定](product-tdd/runtime-resources.md)。 |
| 改代码、角色、技能或打包 | [开发入口](../CONTRIBUTING.md) | [Variant 本地说明](../variants/README.md)、[scripts](../scripts/README.md)、[harness](../harness/README.md)、[submission](../submission/README.md)。 |
| 定义、准备、运行或查询实验 | [Lab 入口](../lab/README.md) | [定义与编译](../lab/exp/experiments.md)、[执行与状态](../lab/exp/execution.md)、[制品与遥测](../lab/exp/artifacts.md)。 |
| 选择运行路径、恢复或定位失败 | [运行手册](deployment/index.md) | [本地 Runner](deployment/local-experiments.md)、[恢复](deployment/recovery.md)、[证据](deployment/evidence.md)。 |
| 读取 Braid 对象、原生会话或遥测 | [Console 接入](deployment/console.md) | [Console 组件](../braid-console/README.md)、[Braid 诊断](deployment/braid-diagnostics.md)。 |
| 确认平台规则、费用模式或通道 | [平台与制品](deployment/competition.md) | [提供商目录](deployment/model-providers.md)，留意具体来源与核对日期。 |
| 找实验定义、运行名或旧配方 | [实验入口](../experiments/README.md) | [历史实验登记](../experiments/archive/README.md)。 |
| 接续一个具体工作主题 | [工作主题索引](work-index.md) | packet 顶部的决定与证据入口，再查保存的 Lab status/monitor。 |
| 查前序结论与原始输入 | [报告索引](../reports/README.md) | [最初输入](archive/initial-handoff.md)、[历史运行协议](deployment/history/README.md)。 |

参数、模型和现场状态从实际源码、冻结制品或 producer 原件取得，导航不维护第二份配置。暂停、停止和选择检查点前读 [恢复门控](deployment/recovery.md#当前-checkpointprepare-与停止门控)，不从目录名、报告或旧计划推断当前授权。

文档归属按问题选择：产品意图归 PRD；跨组件约束归技术说明；接口和局部实现方法归组件 README；操作者的路径选择归运行手册；时点事实与旧协议归报告或历史目录。修改现有权威正文，已迁移的内容只保留直接链接；新增页面必须接住独立的读者任务，不建立空模板。

## 开发侧 SVC

[svc.json](../svc.json)声明开发 Corpus baseline，`.venv/bin/svc status --json`显示本地安装与集成状态，不证明工作流程有效或参赛方法已通过实验。
文档归属按需查询 `.venv/bin/svc lookup --path specs/`；任务包信息组织查询 `task-packet/`；局部设计与注释原则查询 `taste/implementation/`。
这些是开发侧方法，参赛侧裁减 Corpus 与 skill 接线另由对应任务和实际 variant 维护。
生成块由开发 SVC 管理，其中 `svc` 指项目 `.venv/bin/svc`。

<!-- svc:begin navigation sha256=7f7f63d0b8989624f57bd21b82b2ac2d05e4445edfd5af4bc3742996f0754bda -->
## SVC Corpus

Use `svc lookup` when packaged Sustainable Vibe Coding Corpus guidance is relevant, and discover its browse/search/read grammar through `svc lookup --help`. Project documentation outside this marked block remains Consumer-owned.
<!-- svc:end navigation -->
