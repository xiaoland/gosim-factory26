# 实验基础设施入口

新实验使用 schema 3 和 explicit-request-v1。定义不产生执行：build 必须选一个 job，start 必须选 job 和稳定 request-id，每个请求最多绑定一个 attempt。未请求 job、发布的输出、剩余预算和空闲容量不会触发派发、评价或重试。

```sh
python3 -m lab compile INTENT --environment PROFILE --directory BUNDLE
python3 -m lab doctor BUNDLE/recipe.json --job JOB
python3 -m lab build BUNDLE/recipe.json --environment PROFILE --directory EXPERIMENT --job JOB
python3 -m lab start EXPERIMENT --job JOB --request-id REQUEST --deployment PRIVATE_JSON
python3 -m lab status EXPERIMENT
```

默认 status/monitor 是状态文本；`--details` 展开完整诊断，`--json` 用于程序消费，两者互斥，不根据 TTY 自动切换。查询读取保存事实，不启动采集或执行。下一操作是建议及条件，不是授权。详细参数用 `python3 -m lab ACTION --help` 查询。

| 要做什么 | 权威说明 |
| --- | --- |
| 定义目标、模型与明确政策；编译或构建一个目标 | [实验定义与编译](exp/experiments.md) |
| 启动、等待、控制、读取一个或多个实验 | [执行与状态](exp/execution.md) |
| 发布、保留、成员运输、遥测、checkpoint/prepare | [制品与恢复证据](exp/artifacts.md) |
| 按职责找到实现 | [lab.exp 源码导航](exp/README.md) |
| ARC 官方 SDK、平台与应用重放 | [ARC 适配](arc_bench/README.md) |
| 选择恢复来源与当前合法操作 | [恢复入口](../docs/deployment/recovery.md) |

定义位于 experiments/，执行材料和原件位于 WorkSSD 的 runs/。执行终态、服务、输出封口、输运和平台评分分别判断；unknown/pending 不自动 retry。旧 schema1/2 writer 退役，原记录及控制沿冻结 executor，不能翻译为新保证。跨组件约束归[技术说明](../docs/product-tdd/index.md)，当前任务及未验收项归[任务入口](../docs/work-index.md)。
