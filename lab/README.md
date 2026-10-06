# 实验基础设施入口

Lab 的核心控制单位是 run：一次可以独立启动、停止和保存结果的实际执行。新入口直接组装 variant、ARC 任务与 target，不使用 experiment/job/attempt 控制器、capacity、slot、reservation 或未来任务队列。当前重构与验收状态以 [决赛设施 packet](../tasks/finals-experiment-loop/packet.md) 为准；源码存在或命令帮助可读不表示远端路径已完成验收。

```sh
python3 -m lab start I14-dx-test sfp7 TASK
python3 -m lab status
python3 -m lab status RUN --json
python3 -m lab pause RUN
python3 -m lab resume RUN
python3 -m lab stop RUN
python3 -m lab restart RUN --task NEXT_TASK
python3 -m lab wait RUN --json
python3 -m lab logs RUN --follow
python3 -m lab evaluate RUN --kind official
python3 -m lab archive RUN
python3 -m lab serve --config SERVICE_JSON
```

`start` 只要求 variant、target、task，可追加 `--route FILE`、`--competition` 和 `--script FILE`。task 可以是需求目录或维护的任务配置；三类自动评测由任务配置的 evaluations 清单明确启用，官网重放费用模式不从模型 route 推断。改设施与跑模型是不同授权范围；本文命令示例本身不启动或授权收费实验。

`status` 无参数只列未归档且 lifecycle 不是 completed 的运行；failed、stopped 和 unknown 不会被默默隐藏。`--all` 查看全部，指定 RUN 始终可以查回。执行 lifecycle 来自实际执行器，activity/brief 来自该次 program 固定的 variant 状态脚本，查询只读保存事实，不进入远端重新采集。`archive --undo` 撤销隐藏；归档标记不停止、搬移或删除数据。正常完成的零分评测仍是 completed。

`pause/resume` 保持同一次实际执行；自管 Docker 使用 pause/unpause，Hosted 不支持。`restart` 先停止实际执行并保存确定数据，再重新装配同名 variant 程序，整体迁移 data，创建来源明确的新 run。相同 task 和需求版本恢复原生会话；新 task 保留应用及历史，建立新原生任务状态。不支持切换 variant、任意路径提取或失败时悄悄启动空会话。

`stop` 只操作指定 run，不停止独立 Python 自动化程序或其他 run；回收迟到结果仍继续。Python 使用 `lab.run` 的同一组函数组织策略和 stages，不增加调度 DSL。默认 stages 只在 completed 后接续；费用和 idle 使用采集的来源、截止点与缺项，不把未知数当作零。

| 要做什么 | 权威说明 |
| --- | --- |
| 启动、控制、查询一个 run；组织 Python 策略 | [公共运行 API](run.py)、[自动化](automation.py) |
| 程序与数据目录、ARC 执行和同 variant restart | [ARC 适配](arc_bench/README.md) |
| 通用 Console、共享 Collector 与 Backend | [Console](../braid-console/README.md) |
| 读取或操作旧冻结执行 | [历史 lab.exp 源码导航](exp/README.md)；使用其原执行器，不接入新的 run 控制。 |
| ARC 官方 SDK、平台与应用重放 | [ARC 适配](arc_bench/README.md) |
| 选择恢复来源与当前合法操作 | [恢复入口](../docs/deployment/recovery.md) |

新 run 固定包含 manifest.json、program、inputs、data/workspace、data/harness、records、snapshots 和 evaluations。program 保存实际程序，data 保存应用与可迁移原生状态，records 保存本次日志、状态、资源、费用与平台原件。restart 不迁移旧记录或旧费用。凭据不进入可迁移 data 或公开归档。

Mac 控制及回收记录默认位于 WorkSSD 的 runs/lab，`LAB_RUN_ROOT` 可选择其他 WorkSSD 路径。远端执行目录按 target 配置确定；共享服务 SQLite 位于服务宿主本地磁盘，不跨宿主挂载 WAL。历史 schema1/2/3 记录保持原身份，兼容入口为 `python3 -m lab.exp`，不自动接管当前活动执行。跨组件约束归[技术说明](../docs/product-tdd/index.md)。
