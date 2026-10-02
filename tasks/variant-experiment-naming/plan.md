# 命名整理实施计划

本计划落实已接受的 [设计](design.md)。2026-09-26 恢复后完成准备，用户随后两次明确开工；本轮已实施，结果见 [交付核对](verification.md)。独立只读预演见 [preplay](preplay.md)。

## 完成后用户怎样使用

维护者从 Variant 索引选择真实实现，在所属任务的 `experiments.md` 登记问题、case 与允许的执行次数。准备配方时明确真实 variant 和实验 case；每次新执行分配新的 g/r 名称，恢复或查阅已有 run 沿用其身份。查询同时显示可读名称、机器 ID、提交包和来源应用；报告先选定评测批次，再比较条件一致的结果。

实验编号由任务登记维护，`experiments/README.md` 提供导航与同日查重入口，不建设编号服务或通用配置生成器。旧记录可以没有新标签，其原始名称和身份继续有效。

## 1. 先固定当前工作树，再移动目录

迁移对象是开工时的当前工作树，包括未跟踪文件和已删除文件的状态。准备时 HEAD 为 `ad0a627`，但该提交不能代表三个 variant 的全部内容：root-only 整个目录未跟踪，mixed 的 advisor 等材料也有未跟踪内容。不能通过从 HEAD 检出、解压旧包或套用旧 diff 来重建目标目录。

| 源目录 | 目标目录 | 保留的实际职责 |
| --- | --- | --- |
| `variants/pi-team-mixed` | `variants/pi-braid` | 当前基线，包含 develop/main、自动化整体验收、advisor、browser-checks 和交付条件改造。 |
| `variants/pi-team-k3-root-only` | `variants/pi-braid-coordinator` | 根只协调的独立实现，保留其现有材料、分支和生命周期。 |
| `variants/pi-team-reviewer` | `variants/pi-braid-review` | 独立最终验收工作流，保留其现有实现。 |
| `experiments/pi-team-mixed-lite` | `experiments/pi-braid-lite` | 当前 Lite 配方，不改写它此前生成的冻结实验。 |

开工时先核对其他任务是否仍向上述目录写入，并确认目标不存在。记录文件的相对路径、类型、权限、符号链接目标及内容摘要，然后移动目录。逐文件比较移动前后清单，仅允许三个 `run.py` 的 `VARIANT` 和明确列出的当前调用方发生命名变更；角色指令、原生模型配置、依赖、技能与执行流程不借此调整。

执行调用方只有 `Makefile` 的默认值和 Lite `matrix.sh` 的固定 variant 参数需要随迁移更新。`scripts/package_agent.py` 动态定位单层 `variants/<name>/build.py`；入口、构建和原生材料均按相对路径查找，保留单层布局即可。旧名不增加隐式执行别名或源码符号链接。

冻结 ZIP、lab inputs/controller-source、官网 journal 与实际 run 目录不移动。已在 WSL 执行的 Lite 使用冻结 ZIP 和实验输入；本轮只依据既有 packet 说明这个隔离关系，不接管、重启或查询其运行进度。

## 2. 分开稳定标签与本次执行名称

复用 `labels` 和已有 run/operation 记录，不建立第二套身份对象。字段约定如下；通用 lab 只保存标签，不解释 ARC 编号或调用 Harness。

| 位置 | 内容与语义 |
| --- | --- |
| 配方 job 的 `labels` | `experiment_key`、`case`、`operation` 等稳定元信息；`operation` 为 `generate` 或 `replay`，不替代进程终态。 |
| 现有四个身份标签 | `competition`、`variant`、`task`、`venue` 保持现有读取兼容。旧顶层值和显式 labels 同时存在而冲突时拒绝冻结，不静默选择一个。 |
| 本次执行的可选标签映射 | `job_id -> labels`，用于本次分配的 `run_name`；不会写回冻结 job，也不从被重试 run 继承。 |
| `run.json.labels` | 保存稳定标签与本次执行标签的合并结果；执行标签只能补充或重复相同值，不能改写冻结标签。 |
| 既有 operation request | 保存本次实际消费的标签映射，保留新 run 的 `trigger_operation` 和原 `retry_of`。 |

`lab plan` 继续只冻结配方。`lab run`、`lab retry` 增加可选 `--run-labels <JSON文件>`，沿 `start → _frozen_command → _controller → controller → _allocate` 传递，在产生 run 前读取并验证全部映射。拒绝不认识的 job ID、非字符串标签和冲突值，避免部分分配之后才发现输入错误。映射内容进入 operation request；后续展示消费 run 中已保存的值，不再读取外部文件。

初次执行和 retry 都由外层任务登记分配完整名称；不能以 job 的 attempt 生成跨场所编号，也不解析名称取得机器身份。未提供执行标签时保持无可读名，不猜测或沿用上一轮名称。已有记录缺少新标签仍可查询。旧冻结 controller 不增加新参数或回写源码；需要补充说明时只在任务对应表中记录。

修改 `lab/plan.py`、`lab/run.py`、`lab/__main__.py`、`lab/status.py`，让冻结、分配、逐次尝试查询和人类视图保存或展示同一份标签。`show` 的 job 汇总不能把冻结 job 名当作所有 attempts 的名字；名称与机器 ID 一起呈现。

## 3. 在 ARC 边界核实包身份与应用来源

团队包继续由 `scripts/package_agent.py` 写 `capabilities.variant`。读取方先读取这一生产者字段，兼容旧顶层 `variant`，两者有值且不同则报告冲突。缺失身份如实保留为未知，不根据 ZIP 文件名、目录名或用户的 case 名填成已验证的 variant。共同读取规则放在现有 ARC 制品模块，避免 Competition、matrix 与 Playground 分别实现。

重放包按 `replay-manifest.json` 中与需求匹配的 case 读取来源 variant 与应用；一个多题包可能携带不同来源，不能取第一项作为整个包的单一 variant。容器的声明名称、来源实现和实验 case 各自保留其语义。

`arc_matrix` 增加 `--candidate CASE=ZIP` 表示实验配置行；同一真实 variant 的不同 ZIP 可以具有不同 case。现有 `--case COMPETITION/TASK` 仍是选题参数，不能重新解释为实验 case。旧 `--variant NAME=ZIP` 保留为兼容输入，NAME 是用户声明的 variant；包提供身份时必须一致，缺失时保留声明与未验证状态。新记录不把任意对照别名写成真实 variant。

| 接入点 | 具体改动 |
| --- | --- |
| `lab/arc_bench/arc_matrix.py` | 分离 candidate/case 与包内 variant；接受实验编号等稳定标签，输出可供执行映射引用的稳定 job ID。 |
| `experiments/hackathon-local/matrix.py` | 沿 replay case 读取原 variant；增加实验 case 和稳定 scenario 标签，填已有 `source_application`。 |
| `lab/arc_bench/package_arc_replay.py`、`evaluate.py` | 沿用 `replay-manifest.json` 与 `source_application`，传递实际可得的原生成记录、原包身份、带算法的应用摘要；缺失信息不伪造。 |
| `lab/arc_bench/competition.py` | 准备时保存实验/case/operation、逐题运行名及包来源；新元信息参与新记录的续接一致性比较。恢复读取冻结值，保持原 submission display name 与单 snapshot/task run 约束。 |
| `lab/arc_bench/playground.py` | 在既有上传与运行记录保存实际提交名称及上述可选元信息；复用 submission 时继承稳定包来源，显式提供本次 run_name。查询读取已保存数据，不改远端名称。 |

Competition 的 `self_funded` 限制和授权边界保留。submission 名仍表示多题容器，逐题名称对应真实平台 run；重复调用 prepare/resume 不重新分配名称。旧官网 journal 不补写这些字段。

应用来源复用已有字段，摘要同时保留算法。replay 的文件哈希映射摘要和 `arc-application-tree-sha256-v1` 不互相改名，也不直接视为同一种身份。协议只传递事实与引用，不为补齐表格读取模型私有会话。

## 4. 让报告按真实批次选择结果

`benchmarks/hackathon/report.py` 目前按 variant/scenario 取最新结果，会把同名 variant 的不同应用或不同评测轮次拼接。先收窄输入选择，再做现有需求统计：

1. 支持明确选择冻结实验及其 job 集，或显式 run 集。兼容旧 `--runs-root`，但只在能唯一确定批次时直接汇总；混合输入应列出候选和缺失关联，要求选择，不能继续取全局最新。
2. 在选定集合内，依据 `experiment_id/job_id/retry_of` 识别同一 job 的实际 retry 链。仅沿明确关系选取替代尝试，并保留 excluded 原因；没有关系的两次执行各自呈现。
3. 按实验 case、来源应用、suite、运行条件隔离结果。`r01` 与 `r02` 不因为应用和 suite 相同而合并；名称只供展示，组关系取自明确字段和选定 job/run 集。
4. 从选定记录取得各自冻结 coverage，保留 missing、unexecuted、incomplete 等状态。应用缺少来源时可以展示已有执行事实，不能把缺失身份当成相同应用或有效零分。

报告不改测试文件、判据或原始结果。输出兼容应以实际消费者为准：保留可兼容的现有汇总字段，分组信息不能继续用单独 variant 当唯一键。命名展示涉及的现有分析入口只接通标签，不扩展成新的聚合平台。

## 5. 更新权威说明与历史导航

当前说明更新 `README.md`、`AGENTS.md`、`CONTRIBUTING.md`、`variants/README.md`、PRD、Product TDD、Deployment、`lab/README.md`、`docs/index.md` 和 `harness/skills/README.md` 中的有效入口。Variant 索引只列职责、状态和源码，不混入某次成绩或构建进度。已归档 variant README 中指向基线的链接更新为后继路径，原目录名不改。

新建 `experiments/README.md`，将可复用配方与实际实验登记分开。新实验编号只在有真实问题和矩阵时登记；本任务的命名验收不是新模型实验，不占用一个实验编号。按 `tasks/competition-budget/packet.md` 的 15 条历史记录建立导航和生成/回放对应关系，缺少确证的实验边界不补造编号。原记录仍是历史事实的来源，不复制一张独立维护的成绩表。

受影响的其他任务只更新当前源码链接或增加后继说明。acceptance-integrity、acceptance-workflow 等材料中的冻结 ZIP、源码快照、journal 和 run 路径保留原文。Deployment 中旧 ZIP 的具体例子不能批量替换成一个尚不存在的新 ZIP。

## 顺序、验收与停止条件

实施按“固定内容并迁移入口 → 标签与来源链 → 报告选择 → 文档与实际证据复核”推进，每步检查当前工作树，适应其他任务已经完成的改动。跨任务源码仍在写入时先协商路径切换，独立的标签和报告工作可以继续；不要求清空或提交整个脏工作树。

| 要证明的事情 | 验收依据 |
| --- | --- |
| 迁移只改名称，原生行为材料完整保留 | 移动前后的文件清单、权限、链接与摘要差异，加命名消费者 diff。 |
| 当前操作入口不再指向被移走的路径 | `rg` 逐条分类剩余旧名称：当前消费者必须更新；历史引用须仍有真实证据入口或后继说明。 |
| 新字段沿真实记录链保存 | 检查配方、冻结 manifest、执行 request、run 和查询消费者；不运行自编模拟任务或设施测试。 |
| 历史兼容且不混计 | 用已有真实记录执行只读查询与派生报告，覆盖两条生成→回放链和同 variant 的不同批次；输出到新的 analysis 目录，不修改原记录。 |
| 新包使用新入口及相同原生材料 | 若需实际打包，仅在 WSL 使用正常打包入口并保留完整 manifest；不运行 Agent、模型、包 smoke 或评测。 |

目录、标签和报告结果分别报告证据及限制。静态审阅与打包不证明模型行为；新标签的实际分配若尚无获授权真实运行，则明确标注“记录链已实现，实际执行待下一次授权实验观察”，不创建假 benchmark 验收。

只有以下情况需要重新决策：当前 variant 的维护者要求保留旧活动入口；观察到不可按既有标签/来源接口表达的身份冲突；计划必须改变运行、评分或预算语义。普通路径遗漏、文档链接失效和范围内的读取缺陷在授权实施中直接修复。
