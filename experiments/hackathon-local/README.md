# Hackathon 本地公开需求回放

本配方将 [benchmarks/hackathon](../../benchmarks/hackathon/README.md) 的每个公开需求场景展开为独立的官方 Runner job。它只消费已生成、冻结的应用，不调用模型、不修改软件、不访问官网。每题来源 variant 和应用关系取自 ZIP 内 `replay-manifest.json`，测试脚本与 coverage 共享冻结，逐场景选择另存。

新配方使用 `factory26.exp.experiment`，由 matrix.py 显式接收 controller/runner runtime、资源预算、Docker endpoint 和 authority-handoff；具体必需项使用 `python3 experiments/hackathon-local/matrix.py --help`。生成后用 `python3 -m lab build RECIPE --directory EXPERIMENT --job JOB`、`start EXPERIMENT --job JOB --request-id REQUEST`，状态与原始结果使用 `status EXPERIMENT` 和 `analyze EXPERIMENT --output NEW`。旧 benchmark report 的 cohort 查询继续用于历史 run，尚未接入新 attempt 合同。

从仓库根执行后续步骤：

```sh
python3 -m lab doctor RECIPE --json
python3 -m lab build RECIPE --directory EXPERIMENT --job JOB
python3 -m lab start EXPERIMENT --job JOB --request-id REQUEST
python3 -m lab status EXPERIMENT
python3 -m lab analyze EXPERIMENT --output NEW_ANALYSIS
```

当前状态和分析消费新的 attempt 合同，命令与控制规则见 [Lab](../../lab/README.md)。每个 job 使用独立应用副本；失败保留场景、冻结测试身份、Runner 输出及设施错误，缺失结果不当作有效零分。公开需求覆盖的限制归 benchmark 自身说明。

旧 `benchmarks/hackathon/report.py` cohort 报告尚未接入新 attempt 合同。读取旧 run、coverage 缺口、重试链和报告选择见 [历史记录查询](../archive/hackathon-local.md)，不要用旧 `lab run/retry` 创建新执行。运行名称按 [实验命名](../README.md#登记下一项实验)登记，不从文件名猜来源。
