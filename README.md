# Factory26

GOSIM Agentic Factory 2026 的 Agent Harness 实验仓库。比较 Codex app-server / Pi 与 SVC Corpus、braid 的四种组合，保留独立生成、冻结、官方 ARC-bench Keep 评测和 svc analysis 证据。

```sh
cd ~/Development/factory26
python3 scripts/factory.py bootstrap --variant pi-svc
make test
python3 scripts/factory.py run --variant pi-svc --eval-host wsl.win-ws.localhost
```

运行前按[本地运行文档](docs/deployment/index.md)准备环境和仓库外的比赛密钥。当前范围和实验规则见[产品说明](docs/prd/index.md)，完整文档导航见[文档索引](docs/index.md)。

组合配置位于 `variants/<id>/config.json`；使用 `python3 scripts/factory.py list` 或 `show <run-id> --case <REQ-ID>` 导航实验。详细诊断和远程评测方式见运行文档。Codex 使用固定 LiteLLM 协议适配；`sources/svc`、`sources/braid` 是独立的共同开发 Git 仓库。SVC 通过简短导航提供 Corpus 方法；braid 通过本地 Issue/PR/comment、CLI 与事件驱动上下文管理协作，二者可独立启用。本地对象接入正在执行新的验收，旧成绩不代表新实现。

首轮四组 Keep 结果：Pi + SVC **7/32**、Codex + SVC **9/32**、Pi + SVC + braid **14/32**、Codex + SVC + braid **8/32**。其中 braid 两组使用旧适配器，不能代表当前本地模式。条件、耗时、清理故障恢复和限制见[四组实验报告](reports/2026-09-20-harness-matrix.md)。

首次原始 Pi 基线为 **Keep 6/32，通过率 18.75%**；条件、耗时、usage、失败原因和原始产物入口见[实验报告](reports/2026-09-20-pi-keep-baseline.md)。这是本地单任务结果，尚未验证线上提交。

本项目通过 `.venv/bin/svc` 使用项目本地 SVC；`svc.json` 记录采用的 Corpus baseline。开发与文档维护约定见 [AGENTS.md](AGENTS.md)。

资料：[比赛官网](https://create.gosim.org/factory26/)、[ARC-bench 平台](https://www.arc-bench.com/competition)、[评测器](https://github.com/code-philia/arc-bench)、[教学 Labs](https://github.com/code-philia/agentic-software-engineering-hackathon)、[svc](https://github.com/xiaoland/svc)、[braid](https://github.com/xiaoland/braid)。
