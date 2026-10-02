# 命名整理交付与证据

本轮按用户两次明确开工指示完成源码与文档修改，未提交。没有启动生成、评分、模型调用或官网写操作，也没有运行 Factory 测试、模拟任务、smoke 或探针。验证使用文件保全、源码静态核对和 WSL 上已有真实运行的只读查询与报告。

## 已完成

三个源码目录现为 `pi-braid`、`pi-braid-coordinator`、`pi-braid-review`；Lite 配方为 `experiments/pi-braid-lite`。移动的是实际工作树，包含未跟踪材料。迁移清单比对确认：三个 variant 的文件集合、权限、链接与角色内容完整保留，各自只有 `run.py` 的 VARIANT 常量改变。Lite 仅改命令中的名称及说明。

通用 lab 接通稳定 labels 与本次执行的 job→labels 映射；后者进入 operation request 和 run，retry 不继承上次执行标签。实际运行名和机器 ID 在 CLI、JSON 及现有分析展示中分别保存。重试路径在转交冻结控制器前解析为绝对路径，避免切换工作目录后误读相对路径。

ARC 矩阵区分 candidate/case 与包内 variant；共同制品读取识别 `capabilities.variant`、旧顶层 variant 和每题 replay 来源。Competition 保存新元信息并用于续接比较，Playground 保留实际上传名称与复用 submission 的来源。evaluate 和本地 Hackathon 配方沿 `source_application` 传递已取得的来源，未知身份不补造。

Hackathon 报告 schema v3 先选择实际批次，再按 case、赛题、应用与评测条件分组。替代只沿同实验/job 的 retry 链；独立重复不按时间配对。每个组保留 coverage、应用摘要算法、选中与排除记录。官网查看器按 journal 类型发现记录，不再把 `competition/**/hosted/*` 当成唯一目录布局。

当前 README、Variant 索引、开发与运行说明、Lab 契约、跨组件说明及实验导航均已同步。新增的 `experiments/README.md` 区分配方、实验登记和历史证据；旧任务补后继入口，冻结包和运行原名保留。

## 实际核对

| 核对 | 观察与证据 |
| --- | --- |
| 源码目录保全 | [迁移前清单](../../runs/variant-experiment-naming/implementation/migration-before.json)和[迁移差异](../../runs/variant-experiment-naming/implementation/migration-verification.json)；三个 run.py 反向替换名称后的摘要等于迁移前摘要。 |
| 当前路径与语法 | 逐项检查当前执行消费者，旧名称只保留在历史包引用、归档与迁移对应表；31 份相关 Python 源码通过 AST 解析，未执行其运行流程。`git diff --check` 无输出，检查范围内文档链接均可定位。 |
| 旧 lab 记录正常查询 | 在 WSL 使用本轮代码读取真实 run `codex-base-artifact-replay-hackathon-local-github-req-1-1-1-ac1a3d9d01`；[查询结果](../../runs/variant-experiment-naming/implementation/legacy-show.json)保留原 ID、状态和证据入口，新标签缺失仍为空。 |
| 真实报告的条件隔离 | 在 WSL 对同一旧 variant 的三条真实记录运行新版报告，得到两个 suite 组，Runner、适配器等冻结执行输入摘要也参与分组；同一场景在不同 suite 的记录分别保留，未以“最新”覆盖。结果分别为选择 1 项及选择 2 项，不伪装为完整 47 项；因为旧记录未冻结 coverage，conditions_complete 为 false。见[报告](../../runs/variant-experiment-naming/implementation/history-selection-final/report.md)和[结构化结果](../../runs/variant-experiment-naming/implementation/history-selection-final/result.json)。 |
| 旧 replay 来源兼容 | 在 WSL 用共同制品读取读取两份真实回放 ZIP，取得旧 variant、每题来源和 `arc-application-tree-sha256-v1` 摘要；不根据包文件名补 variant。见[来源读取](../../runs/variant-experiment-naming/implementation/replay-sources.json)。 |
| 官网记录与包对应 | 两份 ZIP 的完整 SHA256 与原 journal 中的值一致，journal 分别关联 `e45e4ae7110d`、`8d751d76c2a3`。见[对应证据](../../runs/variant-experiment-naming/implementation/history-links.json)。这是保存记录的身份核对，不是官网状态刷新。 |

WSL 首次 SSH 超时，后续重连成功。只读执行使用 `/tmp/factory26-naming-20260926` 中的隔离代码与 `/home/yyh/Development/factory26/.venv/bin/python`，未覆盖远端工作仓库或控制器。历史报告输入来自 `/home/yyh/Development/factory26-official-local/experiments/hackathon-local-eval-20260925/full/runs`，coverage 显式引用该批次 source 中的冻结文件；选择清单完整保存在 report/analysis JSON。输出已取回上表的本地证据目录。

## 证据限制

旧 K3 回放包保存的直接来源是本地导入身份 `4c17843-clean-replay`，不是官网生成 ID。`7b533d7bd71b` → `e45e4ae7110d` 的关系仍由原任务的明确导出记录解释，新读取没有制造一个包内不存在的原生成引用。另一包直接保存 `097402e69a15`。原 journal 可能停在旧采集状态；本次不将其阶段字段当作最新平台事实。

本轮没有新执行或上传，因此新标签在真实 attempt 分配、官网 prepare/续接中的行为仍待下一次已获授权实验观察。当前证据确认静态接线、旧记录兼容和真实报告隔离，不宣称新模型行为或官网写入已验证。目录迁移只改三个身份常量，不改变材料装配和依赖，本轮没有为名称整理重复构建大型 runtime 或冻结新 ZIP。

工作树原有大量其他任务的修改；未回滚、提交或覆盖它们。主要执行文件的本轮源码增量对照保存在 `runs/variant-experiment-naming/implementation/task-source.diff`，完整实现仍以工作树为准。
