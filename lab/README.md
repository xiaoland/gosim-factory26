# 实验基础设施入口

新实验入口是 lab.exp。它负责编译显式 intent、只读 readiness、冻结 build、派发与控制 attempt、恢复和 status/monitor 投影。ARC 官方 Runner 与官网证据由 lab.arc_bench 适配；资源压力和原生执行约束见 [runtime-resources](../docs/product-tdd/runtime-resources.md)。

常用命令：

    python3 -m lab compile INTENT --environment PROFILE --directory BUNDLE
    python3 -m lab doctor INPUT --environment PROFILE --json
    python3 -m lab build INPUT --environment PROFILE --directory EXPERIMENT
    python3 -m lab start EXPERIMENT --deployment PRIVATE_JSON
    python3 -m lab status EXPERIMENT --json
    python3 -m lab recover CHECKPOINT --intent INTENT --environment PROFILE --directory DERIVED

其它动作及参数用 `python3 -m lab --help`、`python3 -m lab ACTION --help` 查询。控制、接续、来源导入的原件和重入条件归 [执行合同](exp/execution.md)，遥测和输运归 [制品合同](exp/artifacts.md)；`status` 建议不授予执行许可。

路径约定：

- experiments/ 保存 intent、recipe 和冻结 compilation bundle。
- runs/ 保存 runtime 资产、执行计划、attempt、制品、遥测和回执。
- 定义资产、派生输入和可写运行状态分开保存；重试创建新的 attempt。

执行事实按 producer 和观察时间保留。入口结果、执行终态、archive、telemetry、transport 和平台 verdict 分别判断；unknown、身份冲突和 pending 不自动 retry。旧 plan/run/operation writer 已退役，旧记录只读查询，不翻译成新执行。

源码导航：

- [实验定义与编译](exp/experiments.md)：intent、environment、模型绑定和 readiness。
- [执行与状态](exp/execution.md)：controller/runner、单项或多实验查询、控制和来源停止。
- [制品与恢复材料](exp/artifacts.md)：发布、输运、遥测、checkpoint 与 prepared。
- [lab.exp 源码定位](exp/README.md)：按职责找到实际模块。
- [lab.arc_bench ARC 适配](arc_bench/README.md)：官方 Runner、平台状态、模型事实、结果和重放。
- [跨组件技术说明](../docs/product-tdd/index.md)：职责、生命周期和身份约束。
- [恢复手册](../docs/deployment/recovery.md)：操作门控和证据要求。
- [存储生命周期](../tasks/experiment-storage-lifecycle/packet.md)：归档、保留和回收边界。

不把本页当作字段表或运行状态数据库。具体 schema、CLI 参数和失败行为以对应源码及组件说明为准；源码或离线材料反馈也不等于模型、官网或跨环境生命周期验收。
