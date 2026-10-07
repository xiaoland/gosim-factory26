# Variant、实验与运行的命名方案

本文方案已于 2026-09-26 获用户接受。用户随后恢复挂起任务，经 [实施计划](plan.md)、[独立预演](preplay.md) 和明确开工指示完成本轮落地；证据及限制见 [交付核对](verification.md)。授权和接续状态见 [packet](packet.md)。

## 目标与取舍

看到一个名称，应能知道它是哪个 Harness、在验证什么问题，还是哪一次具体执行；查看一条成绩，应能找到生成它的代码、配置、应用及评测来源。名称负责导航，冻结清单、哈希和平台 ID 负责身份。

推荐保留 variant、实验、运行三层。模型组合是实验的一个配置项，应用和提交包是有明确身份的产物，submission 是平台容器；这些都不再发展成第四套命名体系。沿用现有独立 variant、lab 和官网 journal，不建设统一配置生成器或新的实验数据库。

## 已核实的现状

| 事实 | 对方案的约束 |
| --- | --- |
| 7 个 `pi-team-*` 的主入口和 observer 扩展相同，但运行、技能与导出流程已经分化。 | 可以统一架构分类，不能仅凭相似名字合并源码。 |
| `k3-root` 缺当前 mixed 的后台 Bash 接线和交付前清理；`reviewer` 的清理也仍旧。 | 改名不能同时宣称消除了这些行为差异。 |
| 恢复时的 mixed 已采用 develop/main、自动化整体验收、原生 advisor 和 browser-checks，并以 quiescent、根 CLOSED 作为交付条件；coordinator/reviewer 仍有不同流程。 | 沿用已接受的三个名称，但迁移各自当前内容；三个新名字不代表同版本基线上的单变量对照。 |
| `k3-root-only` 不仅换模型，还限制后续可指派成员、要求根只协调，并增加外部工具前置调用。 | 其中协调者职责可以成为工作流区别；模型和前置调用不应写进永久名称。 |
| raw 与 native-hackathon 没有 Braid 工作项；后者有原生角色编排，前者刻意关闭部分扩展/技能。 | “无 Braid”不等于“没有子 Agent”；归档入口不能硬塞进团队打包协议。 |
| [独立实现约定](../independent-variants/design.md)明确允许 variant 自持流程与材料，反对共同 DSL 生成所有 Harness。 | 本轮命名整理保留该决定。 |
| lab 已有冻结 experiment ID、job ID、实际 run ID 和 retry 关系；官网有独立 submission/run ID 与 journal。 | 增加人类可读编号，不重写这些机器身份。 |
| Competition 恢复会用 submission 的 display name 辅助找回上传结果。 | 已冻结或在途的官网名称不能随整理改写。 |
| 原样重放已有应用来源与文件摘要，但不同生产者的摘要算法并不相同。 | 对照应用必须记录算法与来源，不能仅对比两个同名 hash 字段。 |

直接证据入口：[mixed 运行](../../variants/pi-braid/run.py)、[root-only 运行](../../variants/pi-braid-coordinator/run.py)、[根职责](../../variants/pi-braid-coordinator/agents/pi-kimi-k3/instructions.md)、[reviewer 契约](../../variants/pi-braid-review/agents/pi-glm-fast/agents/reviewer.md)、[打包](../../tooling/scripts/package_agent.py)、[lab 冻结](../../lab/plan.py)、[官网准备与恢复](../../lab/arc_bench/competition.py)、[应用重评来源](../../lab/arc_bench/evaluate.py)、[重放包](../../lab/arc_bench/package_arc_replay.py)。

## 一、Variant 的命名与生命周期

统一使用 `<engine>-<coordination>[-<workflow>]`，小写英文、数字与单连字符，建议不超过四个词。名称一经用于冻结产物便作为历史事实保留；更名通过显式对应表建立关系，不覆盖旧清单。

| 部分 | 含义 | 当前需要的词 |
| --- | --- | --- |
| engine | 实际驱动会话的 Agent 客户端，不是模型厂商 | `pi`、`codex` |
| coordination | 主要协作机制 | `braid`：Braid 工作项；`native`：客户端原生会话及其委派能力 |
| workflow，可省略 | 确有独立维护需要的职责或工作流程差异 | `coordinator`：根只协调且不被指派到后续工作项；`review`：独立最终验收职责 |

`pi-braid` 表示 Pi 会话由 Braid 工作项组织。默认接入的 SVC、浏览器工具、后台 Bash 等写入材料和说明，不把每项依赖串进名称。`native` 不承诺单 Agent；是否允许原生子代理由实现和冻结配置说明。

名称中不使用模型名、供应商组合、预算、日期、成绩、`v2`、`new`、`final`、`mixed`、`base` 或未经解释的缩写。版本由源码和制品身份表达；活动、实验、归档是状态字段，不是名字后缀。方法扩展只有在值得独立维护时才进入 workflow，不为“多装一个技能”创建长期 variant。

创建新 variant 前需要回答：是否改变入口/协作机制，或者改变值得并行维护的职责和生命周期？若只是更换模型、推理档位、提示词版本、技能选择、工具开关或额度，且不改变上述职责/生命周期，不新建永久目录。职责也可以由指令而非代码表达，不能以“只改 Markdown”自动归为无行为差异。使用现有独立实现的实验源码快照，保留本次实际原生配置和包；不要求先写一个万能配置接口。

新增一个独立 reviewer 的角色文件本身不足以证明需要新 variant；当前 reviewer 同时规定独立上下文、验收职责和完成前委派，因此暂保留为实验工作流。若该方法成为共同基线，再通过明确的行为迁移合入主线，原实验身份照旧保留。普通修复和基线演进不改 variant 名字。

### 现有实现的具体处置

| 现有名称/入口 | 推荐名称或归属 | 迁移建议 |
| --- | --- | --- |
| `pi-team-mixed` | `pi-braid` | 活动基线，仅改身份与消费者；首次改名不改变行为。 |
| `pi-team-k3-root-only` | `pi-braid-coordinator` | 保留为实验实现。名称表达根不写应用代码，且该根成员不用于后续 Issue/PR 指派；K3 和昂贵会话约束仍独立记录。 |
| `pi-team-reviewer` | `pi-braid-review` | 保留为实验实现，不借改名补齐与 mixed 的流程差异。 |
| `pi-team-k3-root` | `pi-braid` 家族的历史 K3 配置与历史实现 | 原目录及 ZIP 保留归档；它与当前 `pi-braid` 不是等价别名。 |
| `pi-team-deepseek`、`pi-team-glm` | `pi-braid` 家族的历史单成员配置与历史实现 | 保留原路径和证据；旧技能/导出流程不是当前基线的等价别名，不重新启用或构建。 |
| `pi-team-vv` | `pi-braid` 家族的历史 V&V 实现与实验 | 保留原名；旧技能/导出流程不是当前基线的等价别名，不自动升级为活动 `pi-braid-vv`。 |
| `raw/` 的 Pi/Codex | `pi-native`、`codex-native` 家族下的 raw 历史配置 | 仅分类；共享归档入口、专用打包器与原路径保留。 |
| `native-hackathon/` 的 codex-base、codex-svc、pi-base、pi-svc | 对应 native 家族下的 base/SVC 历史配置 | 仅分类，不把这四个历史配置变成四个新源码目录。 |

分类名称不等于当前可执行入口；索引必须同时写清状态和真实源码路径。归档查询仍返回原名称及原身份。旧名用于查询时可以展示后继关系，但执行 CLI 不将旧名悄悄跳转到新实现。

目标活动目录仍保持单层，因为团队打包器目前要求 `variants/<name>/build.py`：

```text
variants/
├─ pi-braid/                 活动基线
├─ pi-braid-coordinator/     实验：根只协调
├─ pi-braid-review/          实验：独立最终验收
├─ pi-team-k3-root/          原路径归档
├─ pi-team-deepseek/         原路径归档
├─ pi-team-glm/              原路径归档
├─ pi-team-vv/               原路径归档
├─ native-hackathon/         原生对照归档
└─ raw/                     原始基线归档
```

[acceptance-integrity](../acceptance-integrity/packet.md) 的可信验收改造当前落在 mixed，迁移时由 `pi-braid` 承接这份实际内容；coordinator 与 reviewer 的既有行为分别保留。实施前核对这三个目录是否仍有源码写入，再统一移动当前工作树；已经冻结的 ZIP、实验副本与在途运行继续使用原路径和身份。

## 二、实验命名：稳定编号，加一个问题

采用 `eYYYYMMDD-NN` 作为人类可读实验编号，日期取首次登记的 Asia/Shanghai 日期，序号在仓库同日内唯一、分配后不复用。中文标题表达要回答的问题，例如“限制昂贵模型会话后，能否完成完整交付”；可选英文目录后缀为 `root-session-budget`。

示例 `e20260926-01-root-session-budget` 中，稳定键是 `e20260926-01`，后缀只是说明。这里的编号仅是示例，尚未给既有实验重新编号。前一轮提议的 `E026` 不采用：跨日期和多任务协作时需要额外维护一个全局递增号，日期加当日序号更容易查重。

实验通常绑定一个问题、冻结矩阵和一组允许的重复次数。一个实验可比较多个 variant 或配置；配置行用有意义的 case 名，如 `flash-root`、`k3-root`、`independent-review`，只在该实验内唯一。不要再把 A/B/C 当长期唯一身份。

问题、比较条件或实际执行输入发生实质变化时登记新实验，并引用前序；同样冻结输入的已授权重复仍属于原实验。追加一次原样评分若用于回答新的部署假设，可以是新实验，但必须关联原生成应用。仅追加诊断报告不会制造新实验。任何编号或目录存在都不代表运行授权。

实验记录直接沿用 `tasks/<task>/experiments.md`：写问题、授权、矩阵、冻结来源、计划次数、完成条件及运行对应表。一个任务可承载多项实验；不为每个编号创建空 task packet。`experiments/README.md` 只做实验编号到任务记录的导航，并将“可复用配方”和“实际实验登记”分开呈现。

已有 `lab` 自动产生的 `exp-时间-随机值` 是执行器 ID，继续保留。新的人类编号写在任务记录与明确的外层路径中，映射到它；不复用或覆盖 `manifest.experiment_id`。官网 journal 不搬进 lab，只在同一实验记录里链接。

## 三、运行命名：生成与重放必须一眼可辨

运行的可读名称采用：

```text
<experiment>--<case>--<task>--gNN     本次调用生成 Harness
<experiment>--<case>--<task>--rNN     回放已冻结应用，仅重新评测
```

例如 `e20260926-01--k3-root--github--g01`。`case` 始终保留；单配置可用 `main`，因此以后增加对照不会要求改旧名。双连字符只划分字段，字段内部可用单连字符。task 简称在实验内跨 benchmark 唯一；若两个比赛都有同名题，用 `hackathon-github` 一类带比赛前缀的简称，真实 competition/task 字段仍分别保存。

每次新的生成执行使用新 g 编号，即使是点击“重试”、相同 submission 或上一轮中断，也不沿用 g01。每次新的固定应用评测使用新 r 编号，即使上次未进入测试。编号在实验、case、task 范围内分别递增，跨 local/hosted 不重复分配。恢复同一个平台 run、重新查询状态或再次收集日志不产生新编号。lab 的 attempt/retry_of 与平台 run ID 继续记录真实执行身份；不额外发明 a01 嵌套层。

逐场景本地验收的每个 job 仍是独立执行，名称在 task 后附已有稳定 scenario ID，例如 `...--github--req-1-1-1--r01`；上层可按同一应用及 suite 展示为一组。名称不承担通用解析协议，机器关联始终消费明确字段与原始 ID。

rNN 必须显式指向来源 g 的实际 run ID、来源实验记录及冻结应用摘要；不能只靠名字中的 g01 猜来源。因此跨实验、跨机器或从本地生成到官网回放也能表达。树状展示从这些来源事实产生，而不是按目录名或时间邻近拼接。

| 情况 | 归类 |
| --- | --- |
| 同一 Harness 再跑一遍需求 | 新 g；会重新调用生成模型，应用身份可能不同。 |
| 同一冻结应用再次部署/评分 | 新 r；来源应用身份应相同。 |
| 官网任务暂停后恢复同一 run | 保留同一可读名称和平台 ID。 |
| 看过评测反馈后修改应用再评估 | 新实验，明确 `oracle/dev-only`；不能称原样重放。 |
| 本地验收已有应用 | r 的一种评测场所；必须标明 local 和具体 suite，与官网成绩分开。 |
| 整个生成命令内部的重试 | 仍归外层 g；保留原生过程，不伪装成多个独立实验样本。 |

运行对应表的必要列为：可读名称、venue、实际 run ID/记录路径、提交包引用、来源应用（重放时）、结果证据入口。成绩引用原始结果，附观测时间；没有测试、执行失败、有效 0/100、暂停和取消分别展示。variant 索引不再写某次成绩或“构建中”这样的瞬时 run 状态。

### 官网名称的实际边界

官网 display name 属于 submission，当前 Competition 一次 submission 可创建 GitHub、Sheet 等多个 run。因此新上传的名称建议为 `<experiment>--<case>--<competition>--g01` 或 `...--r01`，完整到题目的运行名仍保存在本地对应表。名称末尾表示这次提交的生成/回放批次，不能替代各题的实际执行序号。

复用 submission 重跑属于执行入口能力，而不是改名能力：当前 Competition 对同 snapshot/task 保持单 run，不支持把同 journal 再派发为第二次；Playground 虽有复用 submission 的命令，写入口又有自身 practice/probe 范围限制。新规范不扩大这些权限或自动绕过入口限制。需要重复运行时，仍按获授权的受支持流程记录新 journal/平台 ID；不单为展示名额外上传，也不假称 Competition 已支持原地重试。

已上传名称、submission ID 和 run ID 全部保留。Competition 的恢复逻辑仍依据冻结名称工作；展示层可以附加可读别名，不能修改旧 journal 或远端名称来替代来源映射。

## 四、把规则接到现有目录与证据

不搬历史 `runs/`，不移动正在使用的服务、journal 或冻结源码。新实验的外层目录按编号归拢，例如：

```text
tasks/<task>/
  packet.md                         决策与授权
  experiments.md                    实验矩阵及运行对应表

experiments/
  README.md                         编号导航与配方导航
  pi-braid-lite/                    原 mixed Lite 配方随基线改名
  hackathon-local/                  保留当前通用回放验收配方
  archive/                          保留

runs/e20260926-01-root-session-budget/
  k3-root/
    hosted/hackathon/g01/           一次 submission 的 inputs/state/tasks 布局
    local/hackathon/g02/            另一执行批次的 lab manifest/runs 布局
  analysis/                         派生报告，不改原始结果
```

这些路径是外层组织建议，不要求本地与官网内部使用同一协议。官网 journal 是一次 submission 的多题容器，不是某道题的单 run 目录；跨比赛必须分 journal。WSL 数据根可继续使用仓库同级 `factory26-official-local/experiments/<编号>/`，记录完整 host/path 即可，不复制大型产物来追求相同绝对路径。仅在实际需要时创建目录。

新 ZIP 文件名可采用 `<variant>--<ZIP摘要前12位>.zip`；完整 SHA256 仍写入既有清单。重放包命名表达 replay 与来源应用，不当作新 variant。只是外层文件名改变不修改 ZIP 字节；旧 ZIP 不重新封装。

### 复用与补齐现有记录

第一阶段使用现有任务表、manifest 和 journal，即可建立可读的实验树，不新增数据库或跨格式控制器。实施时对新产物补齐既有记录链：

1. 将 `variant` 与实验 `case` 分开。当前 `arc_matrix --variant NAME=ZIP` 中的 NAME 可被当作任意对照别名；以后 variant 表达真实实现，case 表达该实验的配置行。新记录最少透传 `experiment_key`、`case`、`operation`（generate/replay）及可读运行名 `run_name`。稳定元信息由配方 job 的 labels 进入冻结 manifest；run_name 经本次执行的可选标签映射进入 run.json，不能放在冻结 job 中让 retry 继承。查询/report 消费各 run 保存的值；官网在现有 inputs/submission 记录保存实验与 case 元信息，各平台 run 的对应名称沿已有逐题记录保存。`plan.normalize` 当前只保留固定字段，因此不能只在 recipe 中写新字段而不更新整条链。旧数据保持旧语义，缺 case 不猜配方。`arc_matrix` 原有 `--case` 是选题参数，实施采用独立的 candidate 输入表达实验配置行，保留其原义。
2. 新团队包统一 variant 字段的生产与读取。当前 `package_agent.py` 写在 `capabilities.variant`，Competition 却仅核对顶层 `variant`；应读取生产者实际字段，对显式冲突拒绝接续。旧包保留原字段，身份缺失则如实显示；禁止根据目录名补成已验证。
3. 新重放来源继续使用现有 `source_application` 和 `replay-manifest.json`，补齐可取得的原生成记录引用、原提交包身份；官网准备把该来源摘要保存在既有输入记录或链接到包内 manifest。Hackathon 本地 matrix 也须填已有 source_application。Playground 的上传记录当前未保存传给官网的 name，若用于后续实验应在原 submission 记录里保留名称和上述引用。不解析模型私有会话来推断来源，缺失就写未知。

应用摘要必须带算法。已有 replay case 的 `application_sha256` 是文件哈希映射摘要，而 `application_manifest.sha256` 使用 `arc-application-tree-sha256-v1`；不能在迁移中改名冒充相同摘要。底层旧字段保持可读取，新的展示引用带算法的应用 manifest。哈希确认内容身份，不证明完成需求；相同 variant 名也不证明两次输入完全相同。

当前 `benchmarks/hackathon/report.py` 按 variant/场景组织结果。今后必须先明确本次评测批次，再按实验 case、应用来源及评测输入隔离；批次复用真实冻结 lab manifest 的 experiment_id/job 集，或显式保存的 run 集，不再引入另一种全局批次 ID。r01/r02 即使应用和 suite 完全相同，也作为独立重复呈现。只有同一 job 的显式 retry 链可以按既定策略选替代结果，并列出被替代记录；不跨两轮部分结果拼成一轮完整成绩。历史缺少这些关联时保留证据不足，不按名称猜合并。这属于显示和分组消费者的必要修正，不修改测试判据或评分结果。

## 五、最近运行如何呈现

下面只展示来源关系，原始 ID 与历史名字不变。括号内为来源配置说明，不伪称新规范已在当时生效。

```text
pi-braid 家族
├─ 历史 K3 根配置：7b533d7bd71b → 11/100
│  └─ 同应用重放：e45e4ae7110d → 14/100
└─ 根只协调配置：097402e69a15 → 0/100
   └─ 同应用重放：8d751d76c2a3 → 0/100
```

这四条是两次生成、两次回放；不构成从 11 到 14 到 0 的单变量迭代曲线。Sheet 是独立需求下的另一次生成，单独列于对应实验矩阵。更早的 codex-base 本地应用也允许作为官网 r 的来源，不虚构一条官网 g。

已经核对的 15 条官网记录保留在 [现有总览](../competition-budget/packet.md#官网-hackathon-运行总览2026-09-26-核对)。后续只给它们增加实验归属、来源关系与原路径导航，不改原结果或为凑齐命名而重新运行。

## 六、实施顺序与验收

规则与处置表已经接受，恢复后的实施计划和只读预演已经完成。开工依据按本仓既定复核流程记录，不把方案认可或恢复任务自动当作全部源码修改授权。下表是设计范围，具体接口、顺序和文件按 [实施计划](plan.md) 执行。

| 步骤 | 改动范围 | 完成依据 |
| --- | --- | --- |
| 1. 建立导航 | Variant 索引按活动/实验/归档分类；登记实验编号；给 15 条官网记录建立来源对应。 | 从任一记录可找到原 journal、生成/回放属性与来源；无重复统计。 |
| 2. 改三个活动/实验入口名 | 移动 mixed、root-only、reviewer 目录；更新各自 VARIANT、当前打包/配方/文档调用方。 | 名称变更与行为差异分开列；旧冻结输入不被改写，当前消费者不再引用失效入口。 |
| 3. 接通新记录与分组 | 沿用既有字段补齐包身份核对、重放来源传递、case/应用维度的展示与报告。 | 同名 variant 的两份应用不会混计；不同场所/评测输入明确区分；旧记录仍可读取。 |
| 4. 收尾操作说明 | 更新 CONTRIBUTING、技术/运行说明和实验导航；旧任务只加后继入口。 | 一个维护者无需阅读对话，就能命名下一轮并定位历史证据。 |

执行消费者包括三个 variant 的 `run.py`、`Makefile`、`lab/arc_bench/{arc_matrix,competition,playground,package_arc_replay,evaluate,arc_artifacts}.py`、`lab/{plan,run,status,__main__}.py`、`experiments/pi-team-mixed-lite/`、`experiments/hackathon-local/matrix.py` 及 `benchmarks/hackathon/report.py`。`scripts/package_agent.py` 的动态路径和 `capabilities.variant` 生产规则可以沿用。只沿现有标签/来源链处理，不改变通用调度、重试或终态语义。旧 `official_matrix` 及已冻结清单不自动重新启用；开工时仍需适应其他任务的最新改动。

验收使用真实历史记录的正常查询、报告输出与必要的实际打包结果，不新增或运行 Factory 单元测试、模拟集成测试、包 smoke 或探针。重点核对：两个原样重放链仍能解释；生成前失败不展示为有效零分；同一 variant 下不同 case/应用的本地结果不被覆盖；旧官网 ID、原文件和哈希保持不变；新包原生角色与行为材料除名称外未因迁移改变。构建或静态核对不能声称已验证模型行为，新生成/评分仍需独立实验授权。

不在本轮迁移里合并不同流程、补齐历史 variant 的功能、重跑 benchmark、改远端 display name、恢复或停止控制器、提交代码。后续若要把 coordinator/review 合入基线，需要明确选择保留行为、完成差异审阅，并作为行为变更单独验收。
