# Factory 长期文档整理

## 当前范围与授权

用户于 2026-10-01 明确要求：“长期以来，我们迭代太着急太快，没有去整理durable docs，是时候安排一个subagent去进行整理”。本任务整理已经稳定且仍有效的产品意图、跨组件约定和操作知识，完成文档修改；不止交付审计计划。

范围为 `docs/index.md`、`docs/prd/`、`docs/product-tdd/`、`docs/deployment/`、`CONTRIBUTING.md`、`variants/README.md` 及根 README。产品意图归 PRD，跨组件职责、生命周期与失败语义归 TDD，修改和准备方法归 CONTRIBUTING，执行、证据查询和恢复归 Deployment。当前授权、迭代进度、候选设计和实验结果继续留在 task packet、reports 和 runs，不另建迭代状态表。

不改 AGENTS 政策、源码、独立 Braid/SVC 仓库，不运行 Factory/Braid/SVC 测试、模型或实验，不部署或 push，不读取或输出凭据。I12 手动暂停状态保持。存储生命周期分支未合入的实现、I13 未开工的需求树协作和未验收的能力不得写成当前行为。

`docs/prd/index.md` 和 `docs/product-tdd/index.md` 起初由主线持有，等待主线明确交回后才编辑；`harness/skills/README.md` 与 I13 packet/plan/rationale 不在本任务写入范围。其他协作者正在修改仓库，本任务不回退其编辑。

## 整理方法与证据

先保留限定文档起点与历史 dirty，再按当前源码、明确实施回执和任务状态核实。已保存起点、SHA-256、初始限定 diff 和工作区状态：`runs/durable-docs-curation-20261001/baseline/`、`baseline-manifest.json`、`initial-docs.diff`、`initial-status.txt`。文档只提升可跨迭代使用的知识，证据保留可寻址入口；原始报告和任务历史不改写。

主要核实入口：I13 [packet](../iteration13/packet.md) 与工具、提示词、子代理、SVC 接线实施回执；[I10](../iteration10/packet.md)、[I11](../iteration11/packet.md)、[I12](../iteration12/packet.md) 的当前工作与恢复边界；[Console](../braid-console-control/packet.md)；[实验设施](../experiment-infrastructure/packet.md)、[traceability](../experiment-traceability/packet.md)、[预算](../competition-budget/packet.md)、[存储生命周期](../experiment-storage-lifecycle/packet.md)。

当前发现旧入口把 pi-braid 称为唯一活动 Harness，文档索引以 I12 为当前主线，I13 状态落后于实施回执。将修正入口并将动态进度交回对应 packet，不在长期文档维护第二份状态。

## 已完成整理

| 知识职责 | 当前归属与本轮变化 |
| --- | --- |
| 项目与任务入口 | README、docs/index 和 variants 索引改为 I13 开发入口，保留 I10–I12 冻结身份，具体进度与授权仍查 packet。 |
| 产品目标 | PRD 区分独立生成与人工介入研究，说明当前开发入口、ARC 技能边界和新正式参赛授权。 |
| 跨组件约定 | TDD 整合 I13 材料消费者、description-only 与原生连续性、Console 独立职责及交付/评分/证据区别；不把待实施完整协作/需求树技能写成已存在。 |
| 开发操作 | CONTRIBUTING 使用 I13 示例，去掉某次开发 SVC 安装 HEAD 作为长期常量，保留实际安装身份与源码交接方法；修正 factory 查询包含 watch。 |
| 运行操作 | Deployment 分成平台与制品、本地实验、证据查询、恢复与回放四个操作页；索引保留旧任务/报告使用的打包、查询、等待和恢复锚点。通用阶段/应用重放从归档四配置页迁到恢复手册。 |

主线在 `bb148c7` 提交 ARC 文档窄增量后交回 PRD/TDD；本任务另存 `released-baseline/`。ARC 实现 `1c8b9f9` 与[实际回执](../iteration13/arc-boundary-implementation.md)核实了独立 skill/reference、root 入口、非 YAML 图片目录接入及不增加请求语义字段；主线状态随后提交 `4e4b4b7`。本轮不宣称模型采用或完整应用收益。

[工具回执](../iteration13/tools-implementation.md)区分真实 FFF/Context7、Linux装载/构建与 Exa HTTP 401；[提示词回执](../iteration13/prompt-dedup-implementation.md)、[子代理回执](../iteration13/subagents-implementation.md)、[SVC回执](../iteration13/svc-skills-implementation.md)、[上下文实施](../iteration13/context-implementation.md)与[连续性实施](../iteration13/session-continuity-implementation.md)用于核对各消费者及未验边界。Console的关系/正文页依据[真实只读实施](../braid-console-control/session-navigation.md)和现有源码，未改变运行状态。

源码核对发现 Competition 具有显式 `--allow-competition-credit` 门控，而旧 Deployment 声称绝对拒绝额度模式；现文区分默认自费、CLI能力和具体新授权，不恢复 pi-minimal 旧自动接续例外。存储治理主目录 packet 仍是旧设计阶段；实际实现位于独立 worktree 的 `feat/experiment-storage-lifecycle`，当前主线未合入。长期说明标明这一边界，不改旧 task 证据或清理现场。

## 验证、提交与剩余边界

已实际读取 Competition prepare、arc_matrix、恢复打包、hosted_monitor、factory 查询、应用回放和团队打包的 `--help`，退出值均为0；与源码逐项核对所写参数。进行一次性静态链接与锚点核对，结果保存在 `runs/durable-docs-curation-20261001/link-review.json`；没有新增或运行文档内容测试、Factory/Braid/SVC测试、模型或实验。工作区格式检查只覆盖本轮文档。

Git index按起点→终点的本轮增量构造，历史dirty不以整文件暂存。TDD既有assignee改动、Console既有控制说明、Variant未触及的既有入口/独立实现行继续留在工作区；Hackathon的既有阶段回放文字移到新权威操作页，原位置只留转向。起点、三方暂存材料和确切提交身份保存在 `runs/durable-docs-curation-20261001/`。

本轮文档整理完成后没有需要额外开工的整理事项。完整Braid协作/需求树技能、Exa有效key、真实三层委派/连续性与方法采用收益、Console未验UI/Codex及存储分支合入属于原任务；按其已有授权和完成条件接续，不为文档整理自动开启实验或宣称验收通过。

## 参赛须知归档与规则校准（2026-10-01）

用户提供 `参赛须知(1).pdf` 并要求“这应该进入 durable docs”，授权将该规则材料归入长期文档。原件四页、304,937 bytes，SHA256 `5da6b57e40cec8925b536a4535087286839b4e853df54fda37a6f169206b314e`，已原样保存为 [docs/references/competition-notice-20261001.pdf](../../docs/references/competition-notice-20261001.pdf)，文件名日期为接收日。原文件来自用户 Nextcloud 下载目录；后续接续无需依赖该个人路径。

规则操作的唯一正文归 [平台与制品](../../docs/deployment/competition.md#赛事规则与提交模式)，PRD 只纳入泛化 Harness、真实模型生成与需求/参考图边界，文档和运行索引提供入口。正文区分原 PDF、用户对页面“不勾选使用比赛额度评测就不会上榜”的明确补充，以及本项目的实验身份约束；练习也可使用官方 ARC 地址配自有 key，competition 题库不等于正式参赛。已改掉长期文档里过期的“I13全部模型走ARC”描述，具体通道归当前实验 packet。

四页全文已提取并通读，第 2–3 页数学符号的文本提取不完整，因此渲染原页核对公式、参数及排名。原页预览保存在 `runs/durable-docs-curation-20261001/competition-notice/`。日期和券额度明确标记为该版历史安排，不覆盖后续用户更新；未从须知推断当前平台余额、接口是否开放或历史 SIGKILL 根因。文档内容不作为新增提交、收费运行或停止已授权实验的指令。未改 Harness 源码、冻结包或 Agent 提示词。
