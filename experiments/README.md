# 实验与配方导航

variant 是独立维护的 Harness；实验是一项问题及其冻结比较条件；run 是一次实际执行。名字供人查找，源码、包、应用摘要与实际 ID 负责身份。维护入口见 [Variant 索引](../variants/README.md)，运行命令见 [Lab](../lab/README.md)与 [ARC 运行说明](../docs/deployment/index.md)。

## 登记下一项实验

在所属 `tasks/<task>/experiments.md` 写清问题、授权、case、冻结输入、计划次数和完成条件，再把记录链接加入此处。编号采用 `eYYYYMMDD-NN`，日期取首次登记的 Asia/Shanghai 日期，同日序号查重后分配，不复用；它不替换 lab 自动生成的 `exp-...` ID。可以在外层目录追加问题简述，编号本身保持稳定。

case 是实验内的配置行，例如 `flash-root`、`coordinator`；它可以使用相同 variant 的不同冻结包。一个 run 的记录至少关联可读名称、venue、实际 run ID/路径、包引用、重放来源与结果入口。编号或目录存在不代表实验已获授权。

| 执行 | 可读名称 | 来源要求 |
| --- | --- | --- |
| 新生成 | `<实验>--<case>--<task>--gNN` | 本次冻结生成包与需求。 |
| 固定应用复评 | `<实验>--<case>--<task>--rNN` | 来源 run、应用摘要及算法；不重新生成应用。 |
| 本地逐场景复评 | `<实验>--<case>--<task>--<scenario>--rNN` | 同上，另保留冻结 suite 与稳定场景 ID。 |

每次新生成或新复评都分配新编号，即使上一次未进入评分；编号在实验/case/task 内跨场所分配，不直接取 lab attempt。恢复同一个 run、重新查询或采集证据沿用原名。名称不供机器解析，关联用明确字段。多个 benchmark 有同名题时，task 简称加比赛前缀。

官网 display name 属于 submission，可能包含多题，不能代替每题运行名。原 journal 与平台 ID 保留；后续重复按受支持且已获授权的入口建立新记录。

## 实际实验记录

已登记：[e20260926-01：官网 GitHub 初步验收](../tasks/acceptance-integrity/experiments.md)，一次自费运行，具体授权与冻结输入见任务记录。

历史记录保持原编号与名字，下面只导航，不重新维护成绩：

| 历史问题/批次 | 原始记录与运行关系 |
| --- | --- |
| codex-base 应用官网回放、mixed 早期与协作改造批次 | [15 条官网运行总览](../tasks/competition-budget/packet.md#官网-hackathon-运行总览2026-09-26-核对)，包含生成失败、重试及取消。 |
| K3 根对照与同应用干净回放 | [K3 实验](../tasks/k3-root-experiment/packet.md)：`7b533d7bd71b` 生成 → `e45e4ae7110d` 原样重放。 |
| 根只协调与预算/流程改造 | [实验 A/B/C](../tasks/competition-budget/experiments.md)：`097402e69a15` 生成 → `8d751d76c2a3` 原样重放；Sheet 是独立生成。 |
| 可信验收与当前 Lite 闭环 | [可信验收任务](../tasks/acceptance-integrity/packet.md)，冻结旧名 ZIP 与现场沿用原身份。 |

无法从历史证据确定的实验边界、case 或来源保持未知；不按目录名或时间相邻补造关系。

当前恢复：[e20260927-01：保存工作区的交接修复与断点恢复](../tasks/acceptance-integrity/experiments.md#e20260927-01保存工作区的交接修复与断点恢复)。
官网原工作区续接：[e20260927-02：Sheet 自费生成恢复](../tasks/acceptance-integrity/experiments.md#e20260927-02官网从-sheet-原工作区继续生成)。同日编号递增，具体运行使用 `g01`、`g02` 区分尝试；平台 ID 与冻结哈希仍是实际身份。

## 可复用配方

| 配方 | 用途 |
| --- | --- |
| [pi-braid-lite](pi-braid-lite/README.md) | 活动基线的 Keep/BookStack 独立生成与评分清单。 |
| [hackathon-local](hackathon-local/README.md) | 已冻结应用的逐场景公开需求代理评测，不是官网分数。 |
| [archive](archive/) | 原定义与历史条件；不作为继续运行的授权。 |

新实验外层目录可用 `runs/<实验编号>-<问题>/`，内部保留 lab 与官网各自记录格式。WSL 的宿主路径照实登记，不复制大型产物来统一绝对路径。旧 `runs/`、冻结输入、ZIP 和官网名称不迁移。

当前新生成：[e20260928-01：Flash Team WSL Hackathon](../tasks/braid-product-hardening/experiments.md)。

同时运行：[e20260928-02：原 DeepSeek 配方供应商直连](../tasks/braid-product-hardening/experiments.md#e20260928-02原-deepseek-配方供应商直连)。

已授权待启动：[e20260928-03：标准协作与检查工具后的全新 Hackathon](../tasks/braid-github-minimal-review/experiments.md)，以前轮 Sheet 完成官网评分为前置。

当前已授权：[e20261001-01：I13 首轮实验](../tasks/iteration13/experiments.md)，Flash/K2.7 Code 与 GLM-5.3/K3 两组各生成 GitHub、Sheet，全部 ARC，本地生成并逐题官网重放。
