# Factory26

GOSIM Agentic Factory 2026 的 Agent Harness 实验仓库。当前开发 Braid + SVC + Codex app-server/Pi 的 multi-agent harness，保留独立生成、冻结、官方 ARC-Bench 评测和 SVC analysis 证据。

当前唯一活动 Harness 为 `variants/pi-braid`：Pi + Braid + SVC，持有完整代码、原生角色与指令。另有 coordinator 与 review 两个独立实验实现，其余历史实现和结果保留；详见 [Variant 状态](variants/README.md)。

构建一个参赛包：

```sh
python3 scripts/package_agent.py --variant pi-braid \
  --output runs/packages/pi-braid.zip --docker-context arcbox-win
```

运行与官方 Runner 接入见 [运行文档](docs/deployment/index.md)；当前 Lite 两阶段矩阵配方位于 [experiments](experiments/pi-braid-lite/README.md)。开发准备、角色修改与源码运行见 [CONTRIBUTING](CONTRIBUTING.md)，组件与交付关系见[技术说明](docs/product-tdd/index.md)，协作约定见 [AGENTS.md](AGENTS.md)。

包内 `main.py` 接受需求目录和 `--output-dir`；生成与外部评测分开。Braid 管理 Issue/PR 上下文与 comment 协作，SVC 提供按需读取的方法，二者没有直接依赖。新运行使用明确制品，历史结果保持原始条件。

以下是历史实验，不代表当前独立实现的成绩。更多结果见[报告索引](docs/index.md)。

首轮四组 Keep 结果：Pi + SVC **7/32**、Codex + SVC **9/32**、Pi + SVC + braid **14/32**、Codex + SVC + braid **8/32**。其中 braid 两组使用旧适配器，不能代表当前本地模式。条件、耗时、清理故障恢复和限制见[四组实验报告](reports/2026-09-20-harness-matrix.md)。

首次原始 Pi 基线为 **Keep 6/32，通过率 18.75%**；条件、耗时、usage、失败原因和原始产物入口见[实验报告](reports/2026-09-20-pi-keep-baseline.md)。这是本地单任务结果，尚未验证线上提交。

本项目通过 `.venv/bin/svc` 使用项目本地 SVC；`svc.json` 记录采用的 Corpus baseline。开发与文档维护约定见 [AGENTS.md](AGENTS.md)。

资料：[比赛官网](https://create.gosim.org/factory26/)、[ARC-bench 平台](https://www.arc-bench.com/competition)、[评测器](https://github.com/code-philia/arc-bench)、[教学 Labs](https://github.com/code-philia/agentic-software-engineering-hackathon)、[svc](https://github.com/xiaoland/svc)、[braid](https://github.com/xiaoland/braid)。
