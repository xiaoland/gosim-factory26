# Hackathon 本地公开需求回放

本目录保存旧 `factory26.exp.experiment` 配方和[公开需求验收集](suite/README.md)。它按公开场景评测已经生成并冻结的应用，不调用模型、不修改应用、不访问官网；覆盖范围及限制由验收集维护。

`matrix.py` 接收 replay 包、输入目录、controller/runner runtime、资源预算、Docker endpoint 和 authority-handoff，输出旧执行合同。参数见 `python3 experiments/hackathon-local/matrix.py --help`。生成的定义、测试选择与编译材料写入 `runs/<实验>/`，例如 `--output runs/<实验>/definition/experiment.json`；本目录只维护可复用配方和验收源码。

此配方尚未适配当前 run 级 Lab。读取或接续既有 job/attempt 使用其冻结的 [lab.exp 执行器](../../lab/exp/README.md)及原 runtime/source，并从该执行的帮助与回执核对参数；不能使用当前 `python3 -m lab build/start` 执行旧 recipe。源码存在和 CLI 帮助可读不等于取得运行授权或执行就绪。当前 run 的入口见 [Lab](../../lab/README.md)。

每个 job 使用独立应用副本；失败保留场景、冻结测试身份、Runner 输出及具体设施错误，缺失结果不当作有效零分。`suite/report.py` 的 cohort 查询只消费旧 run；历史 coverage、重试链与报告选择见[历史查询](../archive/hackathon-local.md)，不将它宣称为新 run 的分析入口。
