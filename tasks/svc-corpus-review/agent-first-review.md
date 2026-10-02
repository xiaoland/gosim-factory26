# Factory 使用的 SVC Corpus：目录与行文审查

状态：2026-09-23 方案已在 Factory 专用 `sources/svc` 实施；非 bench 验收见 [实施状态](implementation.md)，评分验收按用户安排暂缓。
范围是 Factory26 无人值守的 Web 应用生成任务，不是宣布通用 SVC 的所有 Consumer 都不需要项目文档。
Factory 的 requirement 已提供本次产品需求，生成的软件项目不进入持续迭代周期。

## 先确认实际消费边界

Factory 的 `scripts/package_agent.py` 从 `sources/svc` 快照复制 `corpus/` 和 CLI 源码。
`submission/Dockerfile` 把该源码构建成参赛包内的 SVC wheel。
当前 variant 固定 `sources/svc` 的 `393b935`，而此前改稿在独立的 `~/Development/svc` 工作树 `80996c1` 上。
因此，上一轮改稿已通过自身检查，但尚不能视为 Factory 下一份参赛包的 Corpus 改进。
本轮的目标源是 Factory 的 `sources/svc`，不回写已经冻结的 ZIP。

## 开发 SVC 与 Factory SVC 的边界

两者服务不同的 Agent，应分开维护和装载。
本项目的开发 Agent 使用完整的通用 SVC Corpus 和 analysis 等开发工具；参赛 Agent 只使用从 `sources/svc` 构建的 Factory Corpus 与运行所需 CLI。
`~/Development/svc` 中已做的通用改稿不能自动改变参赛 Agent；有共同价值的改稿须明确挑选进入 `sources/svc`，并通过参赛包验收。

源码目前已部分分开，运行产物还没有分开。
官方 ZIP 从 `sources/svc` 构建 wheel 到 `/runtime/python`。
旧本地生成路径 `scripts/factory.py::runtime_environment` 却把 Factory 项目的 `.venv` 复制给参赛 Agent；`scripts/sources.py::build('svc')` 把 `sources/svc` 安装进同一个 `.venv`，`factory.py::analyze` 又默认用其中的 `svc`。
因此，若把开发用的完整 SVC 安装进 `.venv`，本地生成就可能读到与官方包不同的 Corpus。
调整时将开发侧 `.venv/bin/svc` 与参赛 Agent 的 SVC 安装分开；参赛 Agent 的本地安装只从 `sources/svc` 构建，按源码快照复用，不在每个 run 重装，也不再复制开发 `.venv`。
本地和官方使用相同的 Factory Corpus 输入与 CLI 源码；平台不同导致的安装文件差异不要求 wheel 字节相同。
保留开发侧通过完整 SVC 或 `analyze --svc-source` 诊断 run 的能力。
不为此新增通用的 Corpus 选择器或双模式配置。

## 目录逐项审查

| 当前入口 | 当前规模 | 本场景的消费判断 | 建议的目录动作 |
| --- | ---: | --- | --- |
| `index.md` | 1 文件 | 必须给 Agent 一个小而明确的路由入口；目前却混入长期文档归属、人类审批与偏好。 | 重写为 requirement → task state → work method → delegation → verification 的问题路由。 |
| `task-packet/` | 14 文件、542 行 | 必须支持跨会话恢复和多 Agent 共享任务信息；现有短入口主要面向 Human，模板和入口重复。 | 保留目录与真正可用的 Track/Phase/Cell 深度；把 `packet.md` 定义为 Agent 可恢复的短入口，按需保留模板，删除重复说明和关闭时迁入长期文档的默认流程。 |
| `methods/` | 7 文件、251 行 | Explore、Design、Implementation 仍是生成任务的工作方法；Product/Technical/Test Design 有不同判断责任。 | 保留此树；按具体问题清理人类偏好与无效边界声明；检查图与邻近正文是否重复。 |
| `verification/` | 1 文件、68 行 | requirement 到可观察证据的闭环必需。 | 保留为独立顶层能力，不合并进 Test Design。 |
| `sub-agents/` | 3 文件、42 行 | 物理 Pi/Codex 内部的有界委派有用；不得混成 Braid issue 级 Agent 协作。 | 保留，并在入口明确此语义边界。 |
| `taste/` | 2 文件、127 行 | `index.md` 的个人偏好与人类裁决不属于本 Corpus；`implementation/index.md` 有可迁移的技术判断。 | 删除个人偏好入口；把经压缩的技术判断移入 `methods/design/` 的技术深度，然后移除 `taste/` 目录。 |
| `specs/` | 12 文件、353 行 | 产品需求来自 requirement；一次性生成项目不需要 PRD、TDD、Deployment、Alignment 或 Multi-repo 的长期归属系统。 | 从 Factory 使用的 Corpus 中移除整个目录及其模板，不再做先前提出的路径统一。 |
| `templates/` | 2 文件、51 行 | Agent 的 user-scope 指引由 Factory 打包；运行中的 Agent 不应再建立一套项目 AGENTS 模板。 | 从 Factory 使用的 Corpus 中移除。 |
| `migrations/` | 2 文件、54 行 | 一个生成 run 不升级 SVC baseline；升级指南和发布维护说明都不帮助完成 requirement。 | 从 Factory 使用的 Corpus 中移除。版本与发布机制由 SVC 仓库的工具和维护文档处理。 |

`task-packet/templates/` 内九个可选模板也逐项检查了用途。
`packet.template.md` 是 `svc task init` 的实际输入，必须保留。
`plan`、`task-map` 和 `cell` 对应线性计划与真实共享屏障，保留为按需深度。
`inquiry`、`diagnostic-matrix`、`design`、`decisions` 和 `verification` 对应不同的信息状态，诊断和多 Agent 协作时可能需要，也暂时保留。
当前问题是入口、模板索引与模板注释重复讲准入规则，不是这九个文件已经有证据可以全部删除。
先压缩重复说明；若消费预演中某个模板仍只制造文件而无独立返回，再单独删除它。

目标目录不是给现有所有 SVC Consumer 的兼容布局，而是 Factory 参赛 Agent 真正需要的入口：

```text
corpus/
  index.md
  task-packet/
    index.md
    planning.md
    information.md
    growth.md
    templates/                 # 仅保留有实际恢复或协作价值的模板
  methods/
    index.md
    explore/
    design/                    # product, technical, test, engineering-judgment
    implementation/
  verification/
  sub-agents/
  version.json
```

`corpus/AGENTS.md` 是维护者规则，不进入 wheel，物理源码目录中仍保留它。
把原 `taste/implementation/index.md` 的有效技术判断压缩到 `methods/design/engineering-judgment.md`，并从 Technical Design 和 Implementation 按需路由过去。

对通用 SVC 的持续迭代消费者，`specs/` 和迁移能力可能仍有价值。
我建议只在 Factory 的 `sources/svc` 参赛快照中做此次裁减，保留独立的 `~/Development/svc` 工作树；通用价值明确的行文和方法改进再单独向上游整理。
直接在 SVC 通用产品中删掉这些目录会破坏它的其它 Consumer，新增一个可配置打包过滤器则会扩大本次实现面。

## 内容与行文规则

SVC Corpus 不决定 Agent 的操作权限，也不决定人的偏好。
运行时授权由 Factory/Braid 的任务与工具边界给出，产品行为由 requirement 给出。
这不排除 requirement 本身包含应用登录、角色权限或用户偏好；Agent 仍须实现这些产品需求。
删除的是 Corpus 对人类批准、个人口味和协作礼节作出的通用指令，而不是应用领域的认证或权限逻辑。

用户提到的标准应为 [ASD-STE100](https://www.asd-ste100.org/STE_faq.html) Simplified Technical English。
本项目参考其清楚、直接、稳定用词的原则，不声称完全符合其专用词典。
写作时用主动语态、明确主语、一个句子只说一个主要判断或动作；先写必须知道的条件，再写动作；同一概念使用同一术语。
一行写一个完整句子，不因超过 80 字符而在句中硬换行。
标题、列表、表格和代码块按其结构换行；需要缩短时拆分句义，不删掉主语或条件。
将这条规则写入 SVC 的 Corpus 作者指引，并把本轮改动的正文按它重写。

删图是独立的内容去重工作，不归入行文风格。
`methods/explore/index.md`、`methods/design/index.md` 和 `methods/implementation/index.md` 的图先逐条对照正文；只删没有独有关系的图及相邻重复句，不因“Agent 不喜欢图”而一律删除。

## 验收与实施边界

先用一项简单 Web requirement 和一项含多角色协作、视觉资源的 requirement 预演新的目录路由。
Agent 应在需要时找到 Task Packet、Design、Test Design、Verification 和物理 sub-agent 指引，不读取已移除的项目文档或迁移内容，也不把 Braid Agent 当成 Pi sub-agent。
分别检查开发与参赛 Agent 的 `svc lookup --list/--path`、`svc task init/grow`、相对链接、Catalog 和 wheel 内文件树；开发侧仍有完整指南和 analysis，参赛侧没有已移除的目录，所有入口必须能落到存在的文档。
从本地生成路径启动参赛 Agent，核对其实际 `svc` 可执行文件、包路径与 Corpus 摘要都来自 `sources/svc`，开发 `.venv` 的 Corpus 改动不会影响它；同一源码快照的后续本地 run 复用安装。
核对官方 ZIP 的 Corpus 摘要与本地参赛安装一致；若两侧 Python/平台产生不同安装元数据，只比较实际 CLI 源码和 Corpus 内容。
实验基础设施准备好后，用真实构建包执行一个完整 ARC-Bench-Lite run，得到评分后先报告，不自动开启下一轮。
比较基础 Corpus 的文件数与检索路径，只把减少无关阅读且不丢失关键判断视为内容层验收；分数波动不能单独证明行文改善。

从 Catalog 删除公开路径属于 SVC 的不兼容变更；Factory 快照已采用 Corpus `16.0.0`，并让旧 baseline 停在升级边界，没有伪称无需迁移。
冻结 variant 的 SVC revision、官方构建与本地参赛安装必须指向同一份 `sources/svc` 内容；不要再用开发 SVC 的自测代替参赛包验收。
