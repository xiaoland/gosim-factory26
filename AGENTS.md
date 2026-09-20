# Factory26 开发入口

本仓库开发需求到应用生成的 Agent Harness。开发仓库的 Coding Agent 与被评测的运行时 Agent 是不同角色。

## 文档归属

- [文档索引](docs/index.md)：长期文档、历史输入和实验记录的导航。
- [产品说明](docs/prd/index.md)：目的、当前范围、角色和实验规则。
- [运行文档](docs/deployment/index.md)：环境、凭据、执行、恢复和证据查询。
- `variants/`、`scripts/`、`tests/`：可执行参数、行为和边界检查的事实来源。
- `reports/`：单次实验的脱敏结论；`runs/`：被 Git 忽略的原始产物。
- `docs/handoff-original.md`：保留的原始设计输入，不是当前规范。

## 工作约定

先更新发生变化的语义归属文档，再更新入口链接；不要在 README、任务包和长期文档之间复制同一份规范。机械可验证的事实优先由源码、配置和测试维护。项目共享说明不导入个人指南。

非简单任务使用 `tasks/<task>/packet.md` 保存目标、当前状态和验证结果。任务结束时，将长期有效的变化整合进对应文档，再删除任务包；有保留价值的实验结论与原始证据分别留在 `reports/` 和 `runs/`。

修改生成或评测流程前阅读产品说明中的实验规则。外部评测只能在生成结束并冻结应用后运行，不能把失败详情回灌到同一次基线，也不能修改 `third_party/` 的评测器来适配应用。

诊断实验先运行 `python3 scripts/factory.py list` 和 `show <run-id> --case <REQ-ID>`，再按入口查询 SVC evidence；原生 rollout 仅用于有明确目标的恢复或审计。可用 `analyze --svc-source ../svc` 采用相邻 SVC 工作树，操作说明归属运行文档。

项目检查入口为 `make test`；文档变更检查本地链接和 `.venv/bin/svc status --json`。本项目使用 `.venv/bin/svc`，以下 SVC 生成导航中的命令也用该路径执行，避免误用全局旧版本。

<!-- svc:begin -->
## SVC

Use `svc --help` or `svc <command> --help`.

- `svc status`: inspect project state
- `svc lookup`: read SVC guidance
- `svc task init`: create a task packet
- `svc task grow`: inspect packet shape without changing files
- `svc dev`: manage declared development targets

If `AGENTS.local.md` exists, read it after this file. It is ignored local guidance; shared rules belong here.
<!-- svc:end -->
