# Session 恢复路径调查
调查日期：2026-10-03。先只读审计，随后修正有证据的文档漂移；没有启动 Factory/Braid、模型、实验控制或测试。指定 session 的完整整理见 [target-session.md](target-session.md)；本文件只记录入口、目录边界和文档核对。

## 当前入口是否经过退役 dx-resume

不需要。`docs/index.md:23`、`:36` 直接把 I14 packet 作为入口；`tasks/iteration14/packet.md:3` 又明确“当前范围与执行身份以夜间 packet 为准”，链接 `overnight-plan/packet.md`。当前 canonical 路径是：

`docs/index.md → tasks/iteration14/packet.md → tasks/iteration14/overnight-plan/packet.md → execution.md / design.md / cells`

`tasks/iteration14/dx-resume/packet.md:3` 明确写着“本 packet 已退役为历史记录”，并把当前决定指向 `../overnight-plan/packet.md`。它只在追溯旧恢复决定和错误时有用，不需要再次迁移或删除。

## 已核实的目录和长 session 摩擦

计数需要区分来源：`find` 得到 24 个 docs Markdown 和 16,458 个 tasks 文件，但这包括未跟踪运行验证、第三方/构建目录等资产。逐项 `git ls-files` 统计为 24 个 tracked docs Markdown（其中 `docs/` 顶层 2 个、递归子目录 22 个），1,209 个 tracked tasks Markdown，2,746 个 tracked tasks 文件总数。历史 task Markdown 主要集中在 iteration10/11（分别 465/139 个顶层目录归属），不能把未跟踪验证资产和 tracked 文档混为一个信息量指标。历史材料合理保留，因为它承载授权、费用、失败和身份；问题是当前入口对历史与当前边界的标注，而不是按总文件数建立新架构。

现有机制值得继续复用：`docs/index.md` 的主题导航、I14 顶部 current block、Lab `compile → doctor → build → start → status/control`、artifact manifest、source-stop、authority-handoff，以及 `runs/iteration14/overnight-20261003/monitor-contract.json`。不应再建第二套 launcher、监控器或状态表。

## 真实可证明的差异

| 观察 | 证据 | 影响 |
| --- | --- | --- |
| 修订前 Deployment 首页写 experiment schema 1，而实际合同按 kind 使用当前版本；experiment 为 2。 | `docs/deployment/index.md:3`（修订前）；`lab/exp/core.py:15-16` | 已纠正文案，避免错误选择协议。 |
| 修订前实验 DX packet 顶部待开工、文末已实施并合入。 | [原文](../../experiment-dx-review/history-20261003.md) | 已将当前交付与未验边界写回短入口，旧过程保留。 |
| `CONTRIBUTING.md` 曾把开发 SVC 示例写到 `~/Development/svc`，并把默认 cache 写成 `~/.cache/factory26/`；实际 runtime 使用仓库内 `runs/runtime-cache` 和 `runs/build-cache`，且项目规则要求新产物在 WorkSSD。 | `CONTRIBUTING.md:76,96,118-125`（修订前）；`scripts/runtime.py:22-25,150-154` | 冷启动者会按文档把源码/缓存放到错误位置；这是已直接修正文档的入口漂移。 |

`make braid-report` 仍服务当前 OTLP 诊断，不作为旧入口退役。I14 夜间 packet 已标注旧队列退役，本轮只链接原 owner 的当前答案，没有复制或改写其运行状态。

## 建议（仅限当前调查，不新增设施设计）

可直接修正文档的最小范围（本轮已落实）：

- 把 `docs/deployment/index.md` 的 schema 1 改为当前 schema 2，并保留旧 writer/history 的说明（已完成）。
- 在 runtime 文档中明确 `runtime path` 指向安装结果，build-cache 保存 npm 下载、工具缓存和临时文件；两者同 lock hash 是设计关系（已完成）。
- 在 Deployment 首页补充开发控制、官方 ARC 本地 Runner 与 Hosted 的位置边界；Braid report/telemetry 继续作为当前 OTLP 诊断链（已完成）。

本调查没有修改源码或实验状态；调查期间的文档改动均记录在后续收口段落。
