# Factory26

GOSIM Agentic Factory 2026 的 Agent Harness 实验仓库。当前开发 Braid + SVC + Codex app-server/Pi 的 multi-agent harness，保留独立生成、冻结、官方 ARC-Bench-Lite 评测和 SVC analysis 证据。

```sh
cd ~/Development/factory26
python3 scripts/factory.py bootstrap --backend pi
make test
python3 scripts/factory.py run --backend pi --eval-host wsl.win-ws.localhost
```

参赛 ZIP 的构建、平台模型注入与运行限制见[参赛包说明](docs/deployment/index.md#参赛包与平台边界)。

运行前按[本地运行文档](docs/deployment/index.md)准备环境和仓库外的比赛密钥。当前范围和实验规则见[产品说明](docs/prd/index.md)，完整文档导航见[文档索引](docs/index.md)。

新运行用 `--variant pi-generalist|codex-generalist|pi-team|pi-verification` 选择组合，默认 pi-generalist；`--task keep|bookstack` 选择 Lite 任务。每份 `variants/<variant>/preset.json` 只选择普通 profiles，模型、技能和原生子角色分别归 `harness/` 中对应文件；Braid 不感知 preset。固定八项批次由 [实验清单](experiments/multi-agent-lite.json)管理，联合验收状态见 [task packet](tasks/multi-agent-integration/packet.md)。显式 `--config` 保留自定义单核心及参赛包入口；历史 run 和报告不改写。

`list --backend pi`、`show <run-id> --case <REQ-ID>` 导航结果；`show --run <目录> --profile <ID>` 或 `--session <原生ID>` 定向查询主子会话证据。

`sources/svc`、`sources/braid` 是独立的共同开发 Git 仓库。SVC 通过简短导航提供 Corpus 方法；Braid 围绕本地 Issue/PR 管理会话上下文、围绕 comment 进行异步协作，二者没有直接依赖。Codex 使用固定 LiteLLM 协议适配。Braid 工作项 Agent 与 Codex/Pi 原生子代理是不同层级；能力声明与真实验证结果分开记录。

首轮四组 Keep 结果：Pi + SVC **7/32**、Codex + SVC **9/32**、Pi + SVC + braid **14/32**、Codex + SVC + braid **8/32**。其中 braid 两组使用旧适配器，不能代表当前本地模式。条件、耗时、清理故障恢复和限制见[四组实验报告](reports/2026-09-20-harness-matrix.md)。

首次原始 Pi 基线为 **Keep 6/32，通过率 18.75%**；条件、耗时、usage、失败原因和原始产物入口见[实验报告](reports/2026-09-20-pi-keep-baseline.md)。这是本地单任务结果，尚未验证线上提交。

本项目通过 `.venv/bin/svc` 使用项目本地 SVC；`svc.json` 记录采用的 Corpus baseline。开发与文档维护约定见 [AGENTS.md](AGENTS.md)。

资料：[比赛官网](https://create.gosim.org/factory26/)、[ARC-bench 平台](https://www.arc-bench.com/competition)、[评测器](https://github.com/code-philia/arc-bench)、[教学 Labs](https://github.com/code-philia/agentic-software-engineering-hackathon)、[svc](https://github.com/xiaoland/svc)、[braid](https://github.com/xiaoland/braid)。
