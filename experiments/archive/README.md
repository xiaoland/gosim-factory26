# 历史实验定义与登记

本目录保留旧定义和登记来源，不维护当前运行状态。日期说明登记时点，启动、恢复和费用仍以所属 packet 及其冻结执行器为准；历史表中的授权不授予新的运行许可。

`multi-agent-lite.json` 属于已退役执行器的固定格式。旧本地公开需求回放的生产和报告语义见 [Hackathon 本地历史记录](hackathon-local.md)。当前流程回到 [实验入口](../README.md)。

## 前序实验登记（截至 2026-10-01）

已登记：[e20260926-01：官网 GitHub 初步验收](../../tasks/acceptance-integrity/experiments.md)，一次自费运行，具体授权与冻结输入见任务记录。

历史记录保持原编号与名字，下面只导航，不重新维护成绩：

| 历史问题/批次 | 原始记录与运行关系 |
| --- | --- |
| codex-base 应用官网回放、mixed 早期与协作改造批次 | [15 条官网运行总览](../../tasks/competition-budget/packet.md#官网-hackathon-运行总览2026-09-26-核对)，包含生成失败、重试及取消。 |
| K3 根对照与同应用干净回放 | [K3 实验](../../tasks/k3-root-experiment/packet.md)：`7b533d7bd71b` 生成 → `e45e4ae7110d` 原样重放。 |
| 根只协调与预算/流程改造 | [实验 A/B/C](../../tasks/competition-budget/experiments.md)：`097402e69a15` 生成 → `8d751d76c2a3` 原样重放；Sheet 是独立生成。 |
| 可信验收与前序 Lite 闭环 | [可信验收任务](../../tasks/acceptance-integrity/packet.md)，冻结旧名 ZIP 与现场沿用原身份。 |

无法从历史证据确定的实验边界、case 或来源保持未知；不按目录名或时间相邻补造关系。

9 月 27 日登记的恢复：[e20260927-01：保存工作区的交接修复与断点恢复](../../tasks/acceptance-integrity/experiments.md#e20260927-01保存工作区的交接修复与断点恢复)。
9 月 27 日登记的官网工作区续接：[e20260927-02：Sheet 自费生成恢复](../../tasks/acceptance-integrity/experiments.md#e20260927-02官网从-sheet-原工作区继续生成)。同日编号递增，具体运行使用 `g01`、`g02` 区分尝试；平台 ID 与冻结哈希仍是实际身份。

9 月 28 日登记的新生成：[e20260928-01：Flash Team WSL Hackathon](../../tasks/braid-product-hardening/experiments.md)。

9 月 28 日登记的直连对照：[e20260928-02：原 DeepSeek 配方供应商直连](../../tasks/braid-product-hardening/experiments.md#e20260928-02原-deepseek-配方供应商直连)。

9 月 28 日登记的待启动计划：[e20260928-03：标准协作与检查工具后的全新 Hackathon](../../tasks/braid-github-minimal-review/experiments.md)，以前轮 Sheet 完成官网评分为前置。

10 月 1 日登记的 I13 实验：[e20261001-01：I13 首轮实验](../../tasks/iteration13/experiments.md)，官网 GitHub 生成异常结束并已保全。WSL 恢复后启动四项本地运行：Flash/GitHub 从终态副本重建接续，其余三项干净生成；沿用两路并发及逐题官网应用重放，另行针对官网运行补齐 SIGKILL/OOM 取证，WSL 启动不依赖此调查。
