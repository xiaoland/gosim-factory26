# Hackathon 本地公开需求代理评测

这个配方把 `benchmarks/hackathon` 的每个场景展开成独立的官方 Runner job。它只回放已经生成并冻结的软件；不会调用模型、修改软件或访问官网。

在 WSL 仓库根生成清单：

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
python3 -m lab.run run ../factory26-official-local/experiments/<id>/manifest.json \
  --runs-root ../factory26-official-local/experiments/<id>/runs
python3 benchmarks/hackathon/report.py \
  --runs-root ../factory26-official-local/experiments/<id>/runs \
  --output ../factory26-official-local/experiments/<id>/analysis
```

可重复传入 `--task github|sheet` 或 `--scenario <稳定场景 ID>` 生成局部诊断清单。报告仍以 GitHub 47、Sheet 24 条公开原子需求为固定分母，未运行项目显示为 `unexecuted`。
