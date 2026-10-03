# Hackathon 本地回放的历史记录

本页保留旧 run/retry writer 的生产过程及旧 cohort 报告语义。它不能用于启动当前 experiment；当前入口见 [公开需求回放](../hackathon-local/README.md)。

## 历史记录查询

以下保留旧运行生产过程供定位已有证据。工作树旧 run/retry 写入入口已退役，不能照此新增运行。在历史 WSL 仓库根生成清单的步骤为：

```sh
python3 experiments/hackathon-local/matrix.py \
  --replay ../factory26-official-local/codex-base-artifact-replay.zip \
  --inputs-root ../factory26-official-local/platform-inputs \
  --runner ../factory26-official-local/raw-baseline-20260923-wsl/runner \
  --image arcbench-local-submit:latest --workers 4 \
  --output ../factory26-official-local/experiments/<id>/manifest.json
```

运行和汇总：

```sh
python3 -m lab run ../factory26-official-local/experiments/<id>/manifest.json \
  --runs-root ../factory26-official-local/experiments/<id>/runs
python3 benchmarks/hackathon/report.py \
  --runs-root ../factory26-official-local/experiments/<id>/runs \
  --output ../factory26-official-local/experiments/<id>/analysis/<report-id>
```

可重复传入 `--task github|sheet` 或 `--scenario <稳定场景 ID>` 生成局部诊断清单。报告同时列本次选择数与全套分母，未运行项目显示为 `unexecuted`。重试使用 `python3 -m lab retry <run目录>`，形成新的尝试；报告先选择明确批次，再按 case、赛题、应用、suite 与镜像隔离，只沿显式 retry 链替代旧尝试，并列出排除原因。独立重复不按时间或名称拼接；如同一批次含多个无法对齐的重复，分别展示，可用显式 run 集选定一轮。缺失来源不等于相同应用，也不等于有效零分。

2026-09-25 早期 runs 的 `inputs/tests` 没有复制 `coverage.json`。报告这批记录时须显式传 `--coverage <该次实验冻结源码中的 coverage.json>`；报告会标明它来自实验外的明确冻结来源，且不宣称 run 自身完整冻结了覆盖映射。新配方的 coverage 已纳入共享输入，无需此参数。

## 记录命名与报告选择

配方接受 `--experiment-key <编号> --case <配置行>`；job ID 为稳定 scenario ID。实际执行时用 `lab run/retry --run-labels <JSON>` 分配本次运行名，格式和登记方法见 [实验导航](../README.md)。每个 job 的 `source_application` 来自需求匹配的 replay case，包含已有来源 run 与带算法的应用摘要；旧来源 variant 不因当前目录更名而改写。

推荐以冻结实验选择报告：

```sh
python3 benchmarks/hackathon/report.py \
  --experiment <冻结实验目录或manifest.json> \
  --output <新的分析目录>
```

`--experiment` 可重复以并列多个批次；`--run <run目录>` 可重复以声明本次要查看的明确集合。旧 `--runs-root` 只在目录中全部记录属于同一个已知实验时接受，混合或缺失批次身份时会要求显式选择。报告只读原数据，输出新的 `result.json`、`analysis.json` 和 `report.md`。

报告 schema v3 的 cohorts 按条件分组，以报告内编号作键，真实 case/variant、实验 ID、每题应用摘要与算法、suite/image、Runner/适配器等冻结执行输入摘要、来源 coverage、选中和被替代记录均显式保存。每个 cohort 只统计其赛题；不同应用、批次或独立重复不会被填成一轮完整成绩。
