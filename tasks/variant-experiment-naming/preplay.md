# 命名整理实施预演

2026-09-26 恢复任务后进行了两项独立只读预演：`naming_paths_preplay` 核对目录消费者、工作树与历史边界；`naming_identity_preplay` 核对冻结、分配、重试、包身份、来源和报告链。主 Agent 对关键分配与报告入口作了交叉读取，并将处理决定纳入 [实施计划](plan.md)。这次没有修改源码、打包、启动模型、执行设施测试或调用官网。

## 目录与当前内容

| 检查结果 | 实施决定 |
| --- | --- |
| 团队打包器动态读取 `variants/<name>/build.py`；三个 main/build/run 使用同层相对路径，目标目录均不存在。 | 保持单层布局，移动当前目录；不增加名称注册表或执行别名。 |
| 执行中的固定旧名位于 `Makefile:2`、三个 `run.py:23` 和 Lite `matrix.sh:8`。 | 更新这些消费者；其余命中逐项分为当前入口与历史事实。 |
| root-only 整个目录未跟踪，当前有 32 个普通文件；mixed 包含未跟踪的 advisor 材料。 | 迁移整个当前目录，以文件清单和摘要核对；不以 Git tracked 文件列表作为完整内容。 |
| mixed 已演进到 develop/main、自动化验收、advisor 和新的交付条件；另外两个实现保留旧流程。 | 名称沿用已接受决定，各自行为完整保留；不能宣称它们是同基线的单变量对照。 |
| 当前说明、已归档 variant 的基线链接和部分进行中任务仍引用旧源码路径。 | 更新当前源码链接，历史任务只加后继入口；不批量改写 frozen ZIP/run 路径。 |
| acceptance-integrity 记录中的 Lite 使用独立冻结 ZIP 与 WSL 实验目录。 | 命名迁移保留这些对象；开工时核对源码写入协调即可，不为迁移重启实验。 |

证据入口：[打包器](../../scripts/package_agent.py)、[Makefile](../../Makefile)、[Lite 配方](../../experiments/pi-braid-lite/matrix.sh)、[mixed](../../variants/pi-braid/run.py)、[coordinator 前身](../../variants/pi-braid-coordinator/run.py)、[review 前身](../../variants/pi-braid-review/run.py)、[可信验收任务](../acceptance-integrity/packet.md)。这些源码链接在目录迁移时应更新；本文列出的旧名称保留为预演时的观察。

当前文档消费者为 README、AGENTS、CONTRIBUTING、Variant 索引、PRD、Product TDD、Deployment、文档索引、harness/skills README、归档 deepseek/glm/vv README 和 Lite README。另有 acceptance-integrity 的 plan/design/cells 及 official-runtime-observability packet 中的当前源码引用。旧矩阵、历史报告、冻结包与原始运行内容不属于替换范围。

## 身份与来源链

| 观察到的断点 | 收敛后的处理 |
| --- | --- |
| `lab/plan.py:34` 只保留四个顶层标签。配方添加 case 后会在冻结时丢失。 | 接受通用 labels，保留兼容字段；同时存在而冲突则拒绝冻结。 |
| `lab/run.py:125` 原样继承 job labels。若 run_name 冻结在 job 中，每次 retry 会重用名称。 | 稳定标签随 job；run_name 随本次执行映射进入 run 和现有 operation request。 |
| `attempt` 只在同机器 experiment/job 内递增，无法保证跨 venue 的 g/r 编号。 | 外层任务登记分配名称；lab 不解析或分配 ARC 名称。 |
| `start` 实际通过冻结的 `controller-source` 启动；只改当前 CLI 无法改变旧实验控制器。 | 新参数覆盖完整调用链；旧冻结实验按旧入口运行，仅在外层记录补充导航。 |
| status 的 job attempts 和单 run show 未完整返回标签。 | 查询展示每次 run 保存的 labels，同时保留机器 ID，不仅展示 job 稳定标签。 |
| 团队包写 `capabilities.variant`，Competition 仅读顶层 variant。 | 在 ARC 包读取边界统一兼容与冲突规则；不改变包内字段生产位置。 |
| arc_matrix 的 `--variant NAME=ZIP` 可被用作任意别名，且 `--case` 已表示选题。 | 新增 candidate 表达实验配置行；现有 case 参数不改义，variant 声明与包内身份分开核对。 |
| evaluate/replay manifest 已有来源信息，但缺部分原实验、原包、摘要算法引用；Hackathon matrix 只取来源 variant。 | 沿已有 source_application 和 replay case 传递可取得的事实；缺失仍未知。 |
| Playground 上传记录不保留传入名称，复用 submission 时也会丢稳定包来源。 | 在现有记录保存实际名称与来源，复用容器时显式记录本次 run_name。 |

主要证据：[plan](../../lab/plan.py)、[CLI](../../lab/__main__.py)、[run 分配与启动](../../lab/run.py)、[status](../../lab/status.py)、[Competition](../../lab/arc_bench/competition.py)、[Playground](../../lab/arc_bench/playground.py)、[evaluate](../../lab/arc_bench/evaluate.py)、[replay 打包](../../lab/arc_bench/package_arc_replay.py)、[Hackathon matrix](../../experiments/hackathon-local/matrix.py)。

执行映射只补充标签或重复相同值，不能覆盖冻结 variant/case 等事实。未提供映射的 retry 保持无可读名，而不是继承旧名。映射应在开始分配前整体验证，并保存实际内容；不能仅保存一个之后可能被编辑的 JSON 文件路径。新字段只服务命名和来源，不参与预算模式或执行许可判断。

## 报告批次隔离

`benchmarks/hackathon/report.py:149-175` 当前按 `(variant, scenario_id)` 选择最大 attempt/时间，未先限定 `experiment_id/job_id/retry_of`。这会出现三个具体错误：两个不完整批次被拼成完整成绩；旧批次 attempt=2 压过新批次 attempt=1；同 variant 的不同应用互相覆盖。`conditions_complete` 只检查 suite/image，不能排除这些混计。

实施先增加冻结实验或显式 run 集选择，再按 case、每题来源应用及评测输入隔离；仅在明确的同 job retry 链中替代旧尝试。独立重复分别呈现，excluded 保存具体原因。coverage 也必须从选定记录取得，不能先取整个目录里碰到的第一份。对无法确定批次的旧记录展示不确定性和候选，不用名字补推身份。

证据入口：[报告](../../benchmarks/hackathon/report.py)。这次是控制流预演，并未用真实历史数据执行新版报告；该步骤属于后续实现验收。

## 预演结论与剩余边界

没有发现需要改变已接受三层命名设计的事实。需要补入实施范围的文件是 `lab/__main__.py`；需要明确的接口是本次执行标签映射、candidate 与选题参数分离、报告批次选择。均可沿现有记录实现，无需新编号服务、数据库或统一 Harness 配置。

迁移前仍须重新核对其他任务是否正在写三个 variant 目录，这是时点检查，不是要求所有任务停工。工作树中的变更会继续演进，本文路径与行号只代表本次读取；实现不能复制预演时的完整文件覆盖后续修改。

新记录的真实执行尚未发生。之后验收分开报告静态链路、原有记录的实际查询/报告和必要的 WSL 打包；不把这些证据宣称为新模型运行或新评分验证。预演结束时已具备呈现具体开工范围的条件；之后的授权和落地结果见 [packet](packet.md)，本文件只记录当时的只读结论。
