# Factory26 跨组件技术说明

本文解释当前工作树中多个组件共同依赖的职责、交付和证据语义。
产品目标与实验规则归 [PRD](../prd/index.md)，操作命令归 [开发说明](../../CONTRIBUTING.md)和[运行说明](../deployment/index.md)。
实际模型、字段和工具版本以对应源码与原生材料为准；历史 ZIP 具有自己的身份，不会随工作树更新。

## 组件与调用关系

```text
源码开发                         冻结打包
variants/<name>/main.py          variant/build.py + 指定工具与技能材料
          │                                   │
          │                            独立目录 / ZIP
          └──────── 同一 main.py / run.py ─────┘
                                │
               原生材料 → Braid local → Pi 主会话
                                │           └─ Pi 原生 sub-agent
                       accepted commit
                                │
                         frontend/backend 应用
                                │
                    冻结后交由官方 Runner 评测
```

各 [variant](../../variants/) 自己持有生成流程、角色与指令、技能装载和材料选择。
相同代码可以暂时存在于不同 variant，某个实现的演化不要求扩展公共配置生成器。
[scripts/agent_support.py](../../scripts/agent_support.py)提供文件、进程和交付操作，[braid_runtime.py](../../scripts/braid_runtime.py)处理公开的 Braid 交付边界，[core.py](../../scripts/core.py)提供原生接入及会话归档能力。
这些支持模块不决定某个 variant 的协作方式或模型配方。

[runtime.py](../../scripts/runtime.py)准备工具，不读取题目或角色配置。
[package_agent.py](../../scripts/package_agent.py)调用所选 variant 的 build.py 装入显式材料；打包不是应用生成。
raw 基线由 [raw_main.py](../../submission/raw_main.py)独立执行，可直接使用工具资源，不必经过团队 Harness。

[local_experiment.py](../../scripts/local_experiment.py)运行外部 argv 并保存输入、结果和原始观测，不解释 Agent 的内部协作。
[arc_matrix.py](../../scripts/arc_matrix.py)选择实验组合；[arc_bench_adapter.py](../../scripts/arc_bench_adapter.py)调用官方 Runner 并解释其评测结果。
替换 Harness 不应要求实验控制器识别另一种私有会话格式。

## Braid、原生 Agent 与 SVC

SVC 的技能入口、方法正文和模板由 `sources/svc` 一处维护，标准分发结构为 SKILL.md、references/、assets/。
Factory 通过技能来源目录取得完整材料；公共文件操作只负责复制标准资源和许可，各 variant 自行选择装入与启用的技能。
源码运行和打包共用此复制操作，不解析 SVC 内容，不拼装专用 Corpus，也不复制维护者或 CLI 文件。

| 组件 | 拥有的职责 | 不由它决定的内容 |
| --- | --- | --- |
| Factory variant | 将任务转换为根 Issue 的 prompt，选择成员及其原生配置，调用 Braid 并交付应用。 | 不代替 LLM 分解每条 requirement。 |
| Braid | Issue/PR 对象、comment 协作、工作项上下文和所属主会话的执行。 | 不理解 preset，不控制 Pi 内部子代理生命周期，不读取 SVC task packet。 |
| Pi/Codex 原生接入 | 单个工作项内的原生会话、工具与内部子代理。 | 内部 explorer/executor 不是可指派的 Braid 成员。 |
| SVC skill | 按需提供文档、任务包、工作方法与 V&V 指引。 | 不拥有 Braid 对象或实验调度。 |

对运行时 Agent，成员通过 GitHub 式 assignee 显示；内部 profile 是接入配置，不是它需要学习的产品概念。
跨工作项的信息通过 comment/reply 传递；私有会话内容不会因创建子 Issue 自动共享。
代码修改应保持这些边界，Braid 自身的详细行为归其独立仓库，Factory 不复制维护一份内部设计。

## 角色与材料的三个消费者

以 [mixed](../../variants/pi-team-mixed/) 为例，`agents/<id>/profile.json` 和 `instructions.md` 构成本次 Braid 成员及主会话指引。
`run.py:native_files` 生成主会话 launcher 与 binding，替换当前运行的 endpoint 和技能路径；原生 `models.json/settings.json` 由 Pi 消费。
`agents/<id>/agents/*.md` 则由 Pi 子代理扩展消费，声明工作项内部角色的模型、工具和技能。
`build.py` 决定包中实际存在的材料。

因此“包里有某技能”“主会话启用该技能”“某个子代理启用该技能”是三个不同选择。
修改方法见 CONTRIBUTING；这里不复制各角色的模型值或原生字段定义。

## 交付与评测

Braid 进程退出成功还不构成交付。
`braid_runtime.load_delivery` 读取本次结果并核对交付身份，`export_delivery` 从 accepted commit 导出应用，而不是复制仍可能有未提交修改的工作树。
variant 随后按平台布局交付，记录生成与交付结果；失败现场与辅助归档错误分别保留。
具体文件写入和中断恢复仍受当前实现限制，不把这一顺序解释成跨所有文件的事务保证。

本地独立生成应使用 ARC 适配器的两阶段模式：生成时不传公开测试，再对冻结应用评分。
适配器在提交副本外包装标准 main.py，记录其退出状态，不读取 raw 或 Braid 的私有结果来判断任意 Harness。
官方 Runner 在生成之后还会部署应用，因此生成阶段的 Runner 容器退出码不能单独代表 Agent 入口的退出结果。
包装器记录缺失或入口失败时，不把残留文件误认为生成完成。

| 观察 | 能说明什么 | 不能据此说明什么 |
| --- | --- | --- |
| 标准 Agent 入口成功 | Harness 报告其生成流程完成；适配器另外要求交付布局存在。 | 应用满足全部需求。 |
| Braid accepted commit | 本次团队实现选定的交付版本。 | 该版本已经通过外部评分。 |
| 官方完整评测结果 | 此任务、制品和环境下的有效评分，低分也属于结果。 | 另一版本或另一评测环境具有相同效果。 |
| 外层 local experiment completed | 适配器结果报告完成；具体评分在 result 中。 | 所有用例通过，或所有原生会话已完整归档。 |
| OTLP received | 接收器保存了批次。 | 标准消费者已成功解码，或 Agent 过程记录完整。 |
| 原生 manifest partial/unknown | 会话关联或归档的诊断覆盖有限。 | 应用生成必然失败。 |

## 证据归属与已知限制

外层实验保存调用、输入快照和 Runner 结果；团队 Harness 将生成证据放在输出 `.factory26/<id>`；raw 放在 `.arc/raw`；官网记录由对应 journal 保存。
查询时先辨别生产者，保留各自身份，不以相同题名或 variant 名合并不同运行。
原生会话归档尽量保留原始内容，无法核实身份时记录缺口；诊断失败不应被伪装成应用低分。

当前工作树的 Braid OTLP 接线由 Braid 持有 exporter、原生记录语义和离线重建，Factory 只负责归档后的显式证据交接。
`braid local` 采集运行中的根会话，`core.archive_sessions` 写完 `native/manifest.json` 后，通过 `braid_runtime.export_telemetry` 调用本次运行的 Braid 二进制，补采最终原生文件与 Pi 内部子代理。
没有 OTEL endpoint 或 Braid state 时跳过调用；补采限制总等待时间并单独保存退出码、JSON 报告与原始错误，不改变归档返回值或应用终态。

Factory 交接使用归档后的相对路径与经 header 核实的 native identity，保留 provider session 映射及 group、profile、工作项元信息。
Pi 路径型 session_id 不能标为 Braid 数据库 session UUID；无法核实的原生身份保持 null，归档、observer 与父子关联缺口进入 gaps。
Braid run_id 来自其 request/result，不能用外层实验 ID 覆盖。
未解析原文仍可导出，但 missing/partial/unknown 只说明诊断限制；历史文件导出不伪造实时 span 或累加生成计数。
Collector 继续只保存原始 OTLP 批次，重建通过 Braid 公开 CLI 读取导出的 protobuf，并以源文件清单核对完整性；操作入口见[运行说明](../deployment/index.md)。
这些说明描述当前代码接线，不能代替实时模型链路验收，也不赋予历史 ZIP 新能力。

`braid_telemetry_viewer.py` 以实验 run 为入口，通过 OTLP Backend 查询原始批次，再调用 Braid 的官方类型解码与证据重建接口，生成离线静态网站。
页面通过 OTLP resource 选择 Braid 运行，展示消息、对象和三信号；本地会话归档不作为补齐数据源，Backend 缺失保持可见。图表按 runtime resource 和指标属性分组，不能将累计指标跨实例重复求和，历史导出的操作 span 不当作模型执行。

当前查询工具尚未统一覆盖所有新旧布局，Viewer 未发现某条记录不证明它没有执行。
开发依赖恢复也尚未覆盖所有本地未发布修改；这些限制见运行/开发说明，不能用本技术说明宣称已解决。
