# I10 pi-braid Lite 配方

`matrix.sh` 固定 `pi-braid` 的 Keep/BookStack 两题以及独立评价关系，输入 ZIP 的包内身份必须为 `pi-braid`。这是保留的 I10 配方，不为 I13/I14 自动选择材料或模型；改名前的冻结 ZIP 保留旧身份，不能直接用于这个固定身份入口。

脚本从仓库根调用 `lab.arc_bench.arc_matrix` 生产当前 recipe，不启动模型。除首个 ZIP 参数外，调用方必须提供 ARC matrix 的显式输入：Runner/需求、controller/runner runtime、Docker endpoint/准入、资源与存储预算、模型、评价政策、authority-handoff 和授权。具体参数用下列帮助查询：

```sh
python3 -m lab.arc_bench.arc_matrix --help
experiments/pi-braid-lite/matrix.sh AGENT_ZIP <本次明确参数> --output RECIPE
```

`--separate-evaluation` 已由脚本固定，必须同时提供明确的 `--replay-policy`；旧 `--env-file` 网关接线已退役，凭据通过当前私有 deployment 提供。生成 recipe 后沿 [Lab](../../lab/README.md) 的 doctor/build/start/status 执行，不使用旧 `python3 -m lab.run run`。

比较同一 variant 的多个冻结包时，直接使用通用 ARC matrix 的 `--candidate CASE=ZIP` 和 `--experiment-key`；`--case COMPETITION/TASK` 选择题目。计划和实际许可归所属任务，名称与旧记录查询见 [实验导航](../README.md)。
